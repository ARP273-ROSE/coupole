"""Formats de sortie : XISF (défaut), FITS compressé .fits.fz, FITS float32.

* XISF : Float32 en ADU avec bounds="-1000:65535" (UInt16 pour les FITS IRIS
  entiers), compression zstd+sh niveau 9 — choix mesuré et argumenté dans
  _outils/TEST.md.  Pour PixInsight : rien à régler à l'ouverture.
* FITS compressé (.fits.fz, compression par tuiles du standard FITS) : sans
  perte.  Mesuré avec astropy 8.0 : pour des flottants, RICE_1 et HCOMPRESS_1
  QUANTIFIENT les valeurs (perte, même avec quantize_level=0 : écart d'un ADU) ;
  seuls GZIP_1 et GZIP_2 avec quantize_level=0 restituent les flottants bit à
  bit.  Coupole écrit donc GZIP_2 (octets réordonnés, le meilleur des deux) pour
  les flottants et RICE_1 (sans perte pour les entiers) pour les UInt16.  Lu par
  Siril, astropy, DS9, fpack/funpack (CFITSIO).
* FITS non compressé float32 : le plus universel, deux fois plus petit que le
  float64 d'origine du T120, sans compression.
* XISF compatible (« xisf16 », 0.1.9) : UInt16, compression zlib+sh — ce qu'écrit
  N.I.N.A. lui-même.  Vérifié : N.I.N.A. 3.2 ne lit pas zstd (ajouté en janvier 2026
  dans sa branche de développement) et ramène tout flottant à [0, 1] sans lire
  `bounds` (image blanche en ADU) ; Siril (≥ 1.4.0, lu sans perte par ses versions
  officielles 1.4.0 et 1.4.4) garde les flottants XISF tels quels hors de sa plage
  [0, 1] (statistiques × 65 535).  Les entiers 16 bits sont lus juste par les deux.
  Prix : arrondi à l'ADU entier (≤ 0,5 ADU) et écrêtage à [0, 65 535] (valeurs
  négatives des poses courtes calibrées) — compté et écrit dans l'en-tête.
Chaque fichier écrit est relu et comparé pixel à pixel aux valeurs écrites.
"""
from __future__ import annotations

import os
import warnings

import numpy as np

from ...core import xisf

BORNES = (-1000.0, 65535.0)
CODEC, NIVEAU = 'zstd+sh', 9
CODEC_COMPATIBLE, NIVEAU_COMPATIBLE = 'zlib+sh', 6
EXTENSIONS = {'xisf': '.xisf', 'xisf16': '.xisf', 'fz': '.fits.fz', 'fits': '.fits'}
FORMATS = ('xisf', 'xisf16', 'fz', 'fits')
# Rapport taille de sortie / taille FITS, pour l'estimation avant téléchargement.
# xisf : mesuré sur la banque entière (6.2 de l'Inventaire) ; fz et fits : voir PROGRESSION.md.
RATIOS = {'xisf': {'T120': 0.363, 'IRIS': 0.622}, 'xisf16': {'T120': 0.14, 'IRIS': 0.40},
          'fz': {'T120': 0.39, 'IRIS': 0.66},
          'fits': {'T120': 0.50, 'IRIS': 1.0}}
STRUCTURELS = {'SIMPLE', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2', 'NAXIS3', 'EXTEND', 'BZERO', 'BSCALE',
               'PCOUNT', 'GCOUNT', 'XTENSION', 'ZIMAGE', 'ZBITPIX', 'ZNAXIS', 'ZNAXIS1', 'ZNAXIS2',
               'ZCMPTYPE', 'ZTILE1', 'ZTILE2', 'ZQUANTIZ', 'ZDITHER0', 'ZNAME1', 'ZVAL1', 'ZNAME2', 'ZVAL2',
               'ZSIMPLE', 'ZEXTEND', 'CHECKSUM', 'DATASUM', 'END'}


PIEDESTAL_U16 = 1000          # ADU ajoutés avant l'arrondi (mot-clé PEDESTAL) : garde les fonds négatifs


def vers_uint16(ref, piedestal: float = PIEDESTAL_U16):
    """(UInt16 = arrondi de ref + piédestal, écrêté à [0, 65 535] ; mesure de la perte) pour le XISF compatible.

    Le piédestal (1 000 ADU, la même borne basse que le XISF Float32 : bounds -1000:65535) garde les valeurs
    négatives des poses courtes calibrées : mesuré sur la banque, sans piédestal une pose T120 de 10 s au fond
    sur-soustrait (−220 ADU) perdait 99,75 % de ses pixels à 0.  Il est écrit dans l'en-tête (PEDESTAL, convention
    de PixInsight) ; les autres logiciels voient un fond relevé de 1 000 ADU, le même pour toutes les poses.
    Perte : pixels écrêtés en bas (< −piédestal) et en haut (> 65 535 − piédestal), écart maximal hors écrêtage
    (≤ 0,5 ADU d'arrondi), écart de la médiane (« fond ») une fois le piédestal retiré."""
    fini = np.isfinite(ref)
    r = np.where(fini, ref, 0.0) + piedestal
    u = np.clip(np.rint(r), 0, 65535)
    dans = fini & (r >= -0.5) & (r < 65535.5)                     # ce qui s'arrondit dans [0, 65 535]
    ecart = float(np.abs(u[dans] - r[dans]).max()) if dans.any() else 0.0
    fond_ref = float(np.median(r[fini])) if fini.any() else 0.0
    fond_u = float(np.median(u[fini])) if fini.any() else 0.0
    return u.astype('<u2'), {'u16_negatifs': int((fini & (r < -0.5)).sum()), 'u16_hauts': int((r >= 65535.5).sum()),
                             'u16_non_finis': int((~fini).sum()), 'u16_ecart_max': ecart,
                             'u16_ecart_fond': round(fond_u - fond_ref, 4), 'u16_piedestal': piedestal}


def description_conversion(fmt: str, bitpix: int, entier16: bool) -> str:
    """Texte technique (ASCII, ≤ 68 car.) de la conversion, pour XISFCONV et HISTORY."""
    if fmt == 'xisf16':
        if entier16:
            return 'FITS BITPIX=16 (BZERO=32768) -> XISF UInt16 zlib+sh, sans perte'
        return 'FITS BITPIX=%d -> XISF UInt16 zlib+sh, +%d ADU, arrondi' % (bitpix, PIEDESTAL_U16)
    if fmt == 'xisf':
        if entier16:
            return 'FITS BITPIX=16 (BZERO=32768) -> XISF UInt16, sans perte'
        return 'FITS BITPIX=%d -> XISF Float32 en ADU, bounds -1000:65535' % bitpix
    if fmt == 'fz':
        if entier16:
            return 'FITS BITPIX=16 (BZERO=32768) -> FITS.fz RICE_1, sans perte'
        return 'FITS BITPIX=%d -> FITS.fz Float32 GZIP_2 sans quantification' % bitpix
    if entier16:
        return 'FITS BITPIX=16 (BZERO=32768) -> FITS UInt16, sans perte'
    return 'FITS BITPIX=%d -> FITS Float32 en ADU' % bitpix


def _header_fits(mots):
    from astropy.io import fits
    h = fits.Header()
    for nom, val, com in mots:
        if nom in STRUCTURELS:
            continue
        if nom == 'HISTORY':
            h.add_history(com)
        elif nom == 'COMMENT':
            h.add_comment(com)
        else:
            try:
                h.append(fits.Card.fromstring(('%-8s= %s / %s' % (nom, val, com))[:80]))
            except Exception:
                try:
                    h.append(fits.Card.fromstring(('%-8s= %s' % (nom, val))[:80]))
                except Exception:
                    pass
    return h


def identiques(a, b) -> bool:
    """Égalité pixel à pixel, NaN compris, sans les copies de 64 Mo que fait `np.array_equal(equal_nan=True)`
    (indexation booléenne) : seulement des tableaux de booléens (1 octet par pixel)."""
    if a.shape != b.shape:
        return False
    if a.dtype.kind != 'f' or b.dtype.kind != 'f':
        return bool(np.array_equal(a, b))
    egaux = a == b
    if egaux.all():
        return True
    return bool((egaux | (np.isnan(a) & np.isnan(b))).all())


def ecrire(fmt, chemin, donnees, mots, proprietes, createur):
    """Écrit `donnees` (float32 ou uint16) au format voulu et vérifie la relecture.  Renvoie la taille."""
    if fmt in ('xisf', 'xisf16'):
        bounds = BORNES if donnees.dtype.kind == 'f' else None
        if fmt == 'xisf16':
            if donnees.dtype.str != '<u2':
                raise ValueError('compatible XISF expects UInt16 samples')
            octets, _ = xisf.ecrire(chemin, donnees, mots, proprietes, bounds=None, codec=CODEC_COMPATIBLE,
                                    niveau=NIVEAU_COMPATIBLE, createur=createur)
        else:
            octets, _ = xisf.ecrire(chemin, donnees, mots, proprietes, bounds=bounds, codec=CODEC, niveau=NIVEAU,
                                    createur=createur, niveau_abstrait=round(1 + (NIVEAU - 1) * 99 / 21))
        relu, inf = xisf.lire(chemin, strict=True)        # notre fichier : contrôle complet
        if relu.dtype.str != donnees.dtype.str:
            raise ValueError('read back format %s instead of %s' % (relu.dtype.str, donnees.dtype.str))
        if not identiques(relu, donnees):
            raise ValueError('pixels read back differ from pixels written')
        t_ = xisf.xml_texte
        if [tuple(m) for m in inf['mots_cles']] != [(t_(a), t_(b), t_(c)) for a, b, c in mots]:
            raise ValueError('keywords read back differ')
        return octets
    from astropy.io import fits
    h = _header_fits(mots)
    tmp = str(chemin) + '.tmp'
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        if fmt == 'fz':
            if donnees.dtype.kind == 'f':
                hdu = fits.CompImageHDU(donnees.astype('>f4'), header=h, compression_type='GZIP_2',
                                        quantize_level=0.0)
            else:
                hdu = fits.CompImageHDU(donnees, header=h, compression_type='RICE_1')
            fits.HDUList([fits.PrimaryHDU(), hdu]).writeto(tmp, overwrite=True, checksum=True)
            ext = 1
        else:
            fits.PrimaryHDU(donnees, header=h).writeto(tmp, overwrite=True, checksum=True)
            ext = 0
        with fits.open(tmp, memmap=False) as hd:
            relu = hd[ext].data
            if relu is None or relu.shape != donnees.shape or not identiques(relu.astype(donnees.dtype), donnees):
                raise ValueError('pixels read back differ from pixels written')
    os.replace(tmp, chemin)
    return os.path.getsize(chemin)
