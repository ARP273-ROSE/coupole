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
Chaque fichier écrit est relu et comparé pixel à pixel aux valeurs écrites.
"""
from __future__ import annotations

import os
import warnings

import numpy as np

from ...core import xisf

BORNES = (-1000.0, 65535.0)
CODEC, NIVEAU = 'zstd+sh', 9
EXTENSIONS = {'xisf': '.xisf', 'fz': '.fits.fz', 'fits': '.fits'}
# Rapport taille de sortie / taille FITS, pour l'estimation avant téléchargement.
# xisf : mesuré sur la banque entière (6.2 de l'Inventaire) ; fz et fits : voir PROGRESSION.md.
RATIOS = {'xisf': {'T120': 0.363, 'IRIS': 0.622}, 'fz': {'T120': 0.39, 'IRIS': 0.66},
          'fits': {'T120': 0.50, 'IRIS': 1.0}}
STRUCTURELS = {'SIMPLE', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2', 'NAXIS3', 'EXTEND', 'BZERO', 'BSCALE',
               'PCOUNT', 'GCOUNT', 'XTENSION', 'ZIMAGE', 'ZBITPIX', 'ZNAXIS', 'ZNAXIS1', 'ZNAXIS2',
               'ZCMPTYPE', 'ZTILE1', 'ZTILE2', 'ZQUANTIZ', 'ZDITHER0', 'ZNAME1', 'ZVAL1', 'ZNAME2', 'ZVAL2',
               'ZSIMPLE', 'ZEXTEND', 'CHECKSUM', 'DATASUM', 'END'}


def description_conversion(fmt: str, bitpix: int, entier16: bool) -> str:
    """Texte technique (ASCII, ≤ 68 car.) de la conversion, pour XISFCONV et HISTORY."""
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


def ecrire(fmt, chemin, donnees, mots, proprietes, createur):
    """Écrit `donnees` (float32 ou uint16) au format voulu et vérifie la relecture.  Renvoie la taille."""
    if fmt == 'xisf':
        bounds = BORNES if donnees.dtype.kind == 'f' else None
        octets, _ = xisf.ecrire(chemin, donnees, mots, proprietes, bounds=bounds, codec=CODEC, niveau=NIVEAU,
                                createur=createur, niveau_abstrait=round(1 + (NIVEAU - 1) * 99 / 21))
        relu, inf = xisf.lire(chemin)
        if relu.dtype.str != donnees.dtype.str:
            raise ValueError('read back format %s instead of %s' % (relu.dtype.str, donnees.dtype.str))
        if not np.array_equal(relu, donnees, equal_nan=(donnees.dtype.kind == 'f')):
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
            if relu is None or relu.shape != donnees.shape or \
                    not np.array_equal(relu.astype(donnees.dtype), donnees,
                                       equal_nan=(donnees.dtype.kind == 'f')):
                raise ValueError('pixels read back differ from pixels written')
    os.replace(tmp, chemin)
    return os.path.getsize(chemin)
