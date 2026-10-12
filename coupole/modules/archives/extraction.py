"""Préparation d'un fichier téléchargé : extension scientifique, WCS, unités, NaN, crédits ; sortie FITS ou XISF.

Les produits des grands observatoires sont des FITS à plusieurs extensions : JWST ``_i2d`` (SCI, ERR, CON, WHT,
VAR_*, puis une extension ASDF), HST ``_drz``/``_drc`` (SCI, WHT, CTX), ESO (image principale ou extensions),
NOIRLab (``.fits.fz`` : extensions compressées par tuiles).  PixInsight et Siril n'ouvrent par défaut que la
première image, souvent vide (en-tête seul) : on extrait donc l'image scientifique.

* Choix de l'extension : la première nommée ``SCI`` ; à défaut, la première image à deux dimensions (ou à trois
  dont la première vaut 1) ; une image à plusieurs plans (cube) est refusée avec un message.  Une pose à plusieurs
  détecteurs (« pawprint » de l'ESO : 4 détecteurs pour HAWK-I, 16 pour VISTA, 32 pour OmegaCAM), sans extension
  SCI et dont chaque extension a sa WCS, donne un fichier par détecteur.
* En-tête : mots-clés de la WCS de l'extension (dont les distorsions SIP et TPV), puis les métadonnées utiles de
  l'en-tête principal et de l'extension (télescope, instrument, filtre, dates, temps de pose, programme, PI,
  unités ``BUNIT`` et constantes photométriques ``PHOTFLAM``/``PHOTMJSR``/``PIXAR_SR``…), puis l'origine
  (archive, identifiant, fichier), le crédit et les conditions d'usage (``CREDIT``, ``COMMENT``).
* **Recadrage sur la zone utile** (0.2.2) : une mosaïque peut n'avoir de données que dans un coin (cellule du ciel
  « skycell » des mosaïques multi-visites de Hubble, rognée au rectangle de *toutes* les poses de la cellule, tous
  filtres confondus) ; on garde le plus petit rectangle qui contient tous les pixels valides (finis et non nuls),
  lu par blocs de lignes sans charger l'image entière, et l'on décale ``CRPIX1``/``CRPIX2`` d'autant (la WCS, SIP
  compris, reste exacte).  ``CROPX0``/``CROPY0``/``ORIGNAX1``/``ORIGNAX2`` gardent la trace du recadrage.
* NaN (pixels sans donnée restants, à l'intérieur du rectangle) : comptés ; remplacés par 0 (PixInsight traite mal
  les NaN) ; ``NANCOUNT``/``NANFILL`` le disent.  **Pas de masque séparé par défaut** : l'alignement considère
  alors les 0 exacts comme « sans donnée ».  Sur option, masque ``<nom>_masque.fits`` en entiers 8 bits
  compressés (1 = donnée), écrit après recadrage.
* XISF : Float32, ``bounds`` = minimum et maximum des données (0 compris) : les valeurs physiques (MJy/sr,
  électrons/s…) sont gardées telles quelles, PixInsight les ramène à [0, 1] pour l'affichage.
"""
from __future__ import annotations

import datetime as D
import os
import re
import warnings

import numpy as np

from ... import __version__
from ...core import xisf

CLES_WCS = re.compile(r'^(WCSAXES|CTYPE[12]|CRVAL[12]|CRPIX[12]|CDELT[12]|CUNIT[12]|CD[12]_[12]|PC[12]_[12]|'
                      r'PV[12]_\d+|PS[12]_\d+|LONPOLE|LATPOLE|RADESYSA?|RADECSYS|EQUINOX|EPOCH|MJDREF|DATEREF|WCSNAME|'
                      r'A_ORDER|B_ORDER|AP_ORDER|BP_ORDER|A_\d+_\d+|B_\d+_\d+|AP_\d+_\d+|BP_\d+_\d+|A_DMAX|B_DMAX)$')
CLES_META = ('TELESCOP', 'INSTRUME', 'DETECTOR', 'CHANNEL', 'MODULE', 'FILTER', 'FILTER1', 'FILTER2', 'PUPIL',
             'OBSERVAT', 'DATE-OBS', 'TIME-OBS', 'DATE-BEG', 'DATE-END', 'MJD-OBS', 'MJD-AVG', 'EXPTIME', 'XPOSURE',
             'EFFEXPTM', 'TEXPTIME', 'EXPSTART', 'EXPEND', 'TARGNAME', 'TARGPROP', 'OBJECT', 'PROPOSID', 'PROGRAM',
             'PROG_ID', 'PI_NAME', 'PI_COI', 'PROPTTL1', 'TITLE', 'BUNIT', 'PHOTFLAM', 'PHOTPLAM', 'PHOTBW', 'PHOTFNU',
             'PHOTZPT', 'PHOTMODE', 'PHOTMJSR', 'PHOTUJA2', 'PIXAR_SR', 'PIXAR_A2', 'MAGZP', 'MAGZPT', 'ZEROPT',
             'PHOTZP', 'FLUXCONV', 'GAIN', 'WAVELENG', 'WAVELNTH', 'BANDPASS', 'ORIGIN', 'PROCVER', 'CAL_VER',
             'DRZSCALE', 'D001SCAL', 'NUMEXP', 'NCOMBINE', 'NDRIZIM', 'NEXPOSUR', 'SKYCELL', 'ASN_ID')
MAX_PIXELS = 2**31


class Inexploitable(ValueError):
    """Le fichier n'a pas d'image à deux dimensions exploitable (spectre, cube, table)."""


def _ouvrir(chemin, memmap: bool = True):
    from astropy.io import fits
    return fits.open(str(chemin), memmap=memmap, lazy_load_hdus=False)


def choisir_extension(hdul) -> int:
    """Indice de l'extension scientifique."""
    for i, h in enumerate(hdul):
        if (h.header.get('EXTNAME') or '').strip().upper() == 'SCI' and h.header.get('NAXIS', 0) >= 2:
            return i
    for i, h in enumerate(hdul):
        n = h.header.get('NAXIS', 0)
        if h.is_image and n >= 2:
            dims = [h.header.get('NAXIS%d' % k, 0) for k in range(1, n + 1)]
            if all(d > 1 for d in dims[:2]) and all(d == 1 for d in dims[2:]):
                return i
            if n == 3 and dims[2] > 1:
                raise Inexploitable('cube with %d planes' % dims[2])
    raise Inexploitable('no 2-D image')


def wcs_celeste(entete) -> bool:
    """La WCS de cet en-tête est-elle céleste et utilisable ?"""
    try:
        from astropy.wcs import WCS, FITSFixedWarning
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', FITSFixedWarning)
            w = WCS(entete, naxis=2)
        return bool(w.has_celestial) and w.celestial.naxis == 2
    except Exception:
        return False


def _texte_fits(s) -> str:
    return ''.join(c if 32 <= ord(c) < 127 else '?' for c in str(s))


def entete_prepare(primaire, sci, o: dict | None, nom_source: str, ext: int, nan: int, masque: str):
    """En-tête de l'image préparée (astropy.io.fits.Header)."""
    from astropy.io import fits
    h = fits.Header()
    for k in sci:
        if k and CLES_WCS.match(k):
            h[k] = sci[k]
    for k in CLES_META:
        for source in (sci, primaire):
            if source is not None and k in source and k not in h:
                v = source[k]
                if isinstance(v, str):
                    v = _texte_fits(v)[:68]
                try:
                    h[k] = (v, _texte_fits(source.comments[k])[:46])
                except (ValueError, KeyError):
                    pass
                break
    o = o or {}
    if o.get('cible') and 'OBJECT' not in h:
        h['OBJECT'] = _texte_fits(o['cible'])[:68]
    for k, v, c in (('ARCHIVE', o.get('archive', ''), 'archive of origin'),
                    ('ARCHMISS', o.get('mission', ''), 'mission or collection'),
                    ('ARCHID', o.get('id', ''), 'identifier in the archive'),
                    ('ORIGFILE', nom_source, 'downloaded file'),
                    ('SCIEXT', ext, 'science extension of the original file'),
                    ('LAMBDA', o.get('lambda_nm'), '[nm] central wavelength of the band'),
                    ('NANCOUNT', nan, 'pixels without data (NaN in the original)'),
                    ('NANFILL', 0.0 if nan else None, 'value written in place of NaN'),
                    ('MASKFILE', masque or None, 'mask: 1 = data, 0 = no data')):
        if v not in (None, ''):
            h[k] = (_texte_fits(v)[:68] if isinstance(v, str) else v, c)
    if o.get('credit'):
        h['CREDIT'] = (_texte_fits(o['credit'])[:68], 'credit to display with any image')
        h.add_comment(_texte_fits('Credit: %s' % o['credit']))
    if o.get('page'):
        h.add_comment(_texte_fits('Archive page: %s' % o['page'])[:72])
    h.add_comment('Public archival data; follow the usage terms of the archive.')
    h.add_history('Science extension %d of %s extracted by Coupole %s' % (ext, _texte_fits(nom_source)[:40], __version__))
    h['DATE'] = (D.datetime.now(D.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'), 'file creation (UTC)')
    return h


def mots_cles_xisf(h) -> list[tuple[str, str, str]]:
    """Cartes d'un en-tête astropy → mots-clés XISF (nom, valeur au format FITS, commentaire)."""
    out = []
    for c in h.cards:
        k = c.keyword
        if k in ('SIMPLE', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2', 'EXTEND', 'BZERO', 'BSCALE', ''):
            continue
        if k in ('HISTORY', 'COMMENT'):
            out.append((k, '', str(c.value)))
            continue
        v = c.value
        if isinstance(v, bool):
            s = 'T' if v else 'F'
        elif isinstance(v, (int, np.integer)):
            s = str(int(v))
        elif isinstance(v, (float, np.floating)):
            s = repr(float(v))
        else:
            s = "'%s'" % str(v).replace("'", "''")
        out.append((k, s, str(c.comment or '')))
    return out


def bornes(donnees) -> tuple[float, float]:
    """(minimum, maximum) des données finies, 0 compris (valeur des NaN remplacés) ; intervalle jamais nul."""
    lo, hi = np.inf, -np.inf
    for i in range(0, donnees.shape[0], 1024):
        bloc = donnees[i:i + 1024]
        fin = bloc[np.isfinite(bloc)]
        if fin.size:
            lo, hi = min(lo, float(fin.min())), max(hi, float(fin.max()))
    if not np.isfinite(lo):
        lo, hi = 0.0, 1.0
    lo, hi = min(lo, 0.0), max(hi, 0.0)
    if hi <= lo:
        hi = lo + 1.0
    return lo, hi


def ecrire_image(chemin, donnees, entete, fmt: str = 'xisf') -> int:
    """Écrit (atomiquement) l'image Float32 ; rend la taille du fichier."""
    chemin = str(chemin)
    tmp = chemin + '.tmp'
    if fmt == 'xisf':
        lo, hi = bornes(donnees)
        props = [('Observation:Object:Name', 'String', str(entete.get('OBJECT', '')))] if entete.get('OBJECT') else []
        xisf.ecrire(tmp, np.ascontiguousarray(donnees, dtype='<f4'), mots_cles_xisf(entete), props, bounds=(lo, hi),
                    createur='Coupole %s' % __version__)
    else:
        from astropy.io import fits
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            fits.PrimaryHDU(np.asarray(donnees, dtype='>f4'), header=entete).writeto(tmp, overwrite=True, checksum=True)
    os.replace(tmp, chemin)
    return os.path.getsize(chemin)


def ecrire_masque(chemin, masque, entete) -> None:
    """Masque 1 = donnée, 0 = sans donnée : entiers 8 bits, compressé par tuiles (GZIP) — quelques centaines de ko au
    lieu d'un octet par pixel (un masque pleine taille de 0.2.1 pesait 312 Mo pour 19 806 × 15 741 px)."""
    from astropy.io import fits
    h = fits.Header()
    for k in entete:
        if k and CLES_WCS.match(k):
            h[k] = entete[k]
    h['COMMENT'] = 'Coupole mask: 1 = data, 0 = no data (NaN in the original)'
    tmp = str(chemin) + '.tmp'
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(np.ascontiguousarray(masque, dtype=np.uint8), header=h,
                                                           compression_type='GZIP_1')]).writeto(tmp, overwrite=True)
    os.replace(tmp, str(chemin))


def lire_masque(chemin) -> np.ndarray | None:
    """Masque booléen (compressé 0.2.2 ou plein 0.2.0/0.2.1) ; None si illisible."""
    from astropy.io import fits
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with fits.open(str(chemin), memmap=False) as hm:
                for h in hm:
                    if h.data is not None:
                        return np.asarray(h.data) > 0
    except (OSError, ValueError):
        return None
    return None


def zone_utile(donnees, bloc: int = 512) -> tuple[int, int, int, int] | None:
    """(y0, y1, x0, x1) inclus du plus petit rectangle qui contient tous les pixels valides (finis et non nuls),
    calculé par blocs de lignes (une image projetée en mémoire n'est jamais chargée entière).  None : aucun pixel
    valide."""
    ny = donnees.shape[0]
    lignes = []
    colonnes = None
    for i in range(0, ny, bloc):
        b = np.asarray(donnees[i:i + bloc])
        while b.ndim > 2:
            b = b[0]
        v = np.isfinite(b) & (b != 0)
        l = v.any(axis=1)
        if l.any():
            idx = np.nonzero(l)[0] + i
            lignes += [int(idx[0]), int(idx[-1])]
            c = v.any(axis=0)
            colonnes = c if colonnes is None else (colonnes | c)
    if not lignes or colonnes is None or not colonnes.any():
        return None
    xs = np.nonzero(colonnes)[0]
    return min(lignes), max(lignes), int(xs[0]), int(xs[-1])


def nombre_poses(h) -> int | None:
    """Nombre de poses combinées d'après l'en-tête : NUMEXP (produits HAP), NCOMBINE de l'extension SCI (poses
    réunies au rejet des rayons cosmiques), NEXPOSUR (JWST), sinon les fichiers distincts des D###DATA (drizzle)."""
    for k in ('NUMEXP', 'NCOMBINE', 'NEXPOSUR'):
        v = h.get(k)
        if isinstance(v, (int, np.integer)) and v > 0:
            return int(v)
    fichiers = {str(h[k]).split('[')[0] for k in h if re.match(r'^D\d{3}DATA$', k or '')}
    return len(fichiers) or None


def exposition_totale(h) -> float | None:
    for k in ('TEXPTIME', 'XPOSURE', 'EFFEXPTM', 'EXPTIME'):
        v = h.get(k)
        if isinstance(v, (int, float, np.integer, np.floating)) and v > 0:
            return float(v)
    return None


def extensions_detecteurs(hdul) -> list[int]:
    """Images d'une pose à plusieurs détecteurs (« pawprint » de VISTA, HAWK-I, OmegaCAM…) : plusieurs extensions
    images avec chacune une WCS céleste et aucune extension nommée SCI.  [] sinon."""
    if any((h.header.get('EXTNAME') or '').strip().upper() == 'SCI' for h in hdul):
        return []
    out = []
    for i, h in enumerate(hdul):
        if i and h.is_image and h.header.get('NAXIS', 0) == 2 and wcs_celeste(h.header):
            out.append(i)
    return out if len(out) > 1 else []


def preparer(source, dest_sans_ext, o: dict | None = None, fmt: str = 'xisf', etiquette: str | None = None,
             masque: bool = False, recadrer: bool = True, nommer=None) -> dict:
    """Prépare `source` (FITS, FITS compressé, PDS3/VICAR/PDS4) en `dest_sans_ext` + extension du format.

    Une pose à plusieurs détecteurs donne un fichier par détecteur (``<nom>_d1``, ``_d2``…).  `recadrer` : garder
    seulement la zone utile ; `masque` : écrire aussi le masque des pixels sans donnée (compressé).
    Rend {'chemin', 'chemins', 'masque', 'forme', 'forme_origine', 'recadrage', 'nan', 'wcs', 'bunit',
    'extension', 'octets', 'poses', 'exposition', 'entete'} ; lève Inexploitable.  `nommer(entete)` : chemin sans
    extension choisi d'après l'en-tête préparé (nom lisible), à la place de `dest_sans_ext`."""
    o = o or {}
    nom = os.path.basename(str(source))
    if o.get('format') in ('pds3', 'vicar', 'pds4') or nom.lower().endswith(('.img', '.xml')):
        return _preparer_planetaire(source, dest_sans_ext, o, fmt, etiquette, nommer)
    for memmap in (True, False):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            hdul = _ouvrir(source, memmap)
            try:
                exts = extensions_detecteurs(hdul) or [choisir_extension(hdul)]
                resultats = []
                for k, ext in enumerate(exts):
                    suffixe = '_d%d' % (k + 1) if len(exts) > 1 else ''
                    resultats.append(_preparer_hdu(hdul, ext, str(dest_sans_ext) + suffixe, o, nom, fmt, masque,
                                                   recadrer, nommer, suffixe))
                break
            except ValueError as e:              # entiers avec BZERO/BSCALE (poses brutes) : pas de projection mémoire
                if not memmap or 'memory-mapped' not in str(e):
                    raise
            finally:
                hdul.close()
    r = dict(resultats[0])
    r['chemins'] = [x['chemin'] for x in resultats]
    r['masques'] = [x['masque'] for x in resultats if x['masque']]
    r['nan'] = sum(x['nan'] for x in resultats)
    r['octets'] = sum(x['octets'] for x in resultats)
    return r


def _preparer_hdu(hdul, ext, dest_sans_ext, o, nom, fmt, masque=False, recadrer=True, nommer=None,
                  suffixe='') -> dict:
    sci = hdul[ext]
    nx0, ny0 = sci.header.get('NAXIS1', 0), sci.header.get('NAXIS2', 0)
    if nx0 * ny0 > MAX_PIXELS:
        raise Inexploitable('image too large')
    brut = sci.data
    while brut is not None and brut.ndim > 2:
        brut = brut[0]
    if brut is None:
        raise Inexploitable('no data')
    zone = zone_utile(brut) if recadrer else None
    if zone is not None and (zone[0], zone[1], zone[2], zone[3]) == (0, brut.shape[0] - 1, 0, brut.shape[1] - 1):
        zone = None
    if zone is not None:
        y0, y1, x0, x1 = zone
        donnees = np.array(brut[y0:y1 + 1, x0:x1 + 1], dtype=np.float32)
    else:
        donnees = np.array(brut, dtype=np.float32)
    primaire = hdul[0].header if ext != 0 else None
    sci_h = sci.header
    fini = np.isfinite(donnees)
    nan = int(donnees.size - np.count_nonzero(fini))
    masque_chemin = ''
    poses = nombre_poses(sci_h) or (nombre_poses(primaire) if primaire is not None else None)
    if nommer is not None:
        provisoire = entete_prepare(primaire, sci_h, o, nom, ext, nan, '')
        if poses:
            provisoire['NPOSES'] = poses
        dest_sans_ext = str(nommer(provisoire)) + suffixe
    if nan:
        donnees = np.where(fini, donnees, np.float32(0))
        if masque:
            masque_chemin = str(dest_sans_ext) + '_masque.fits'
    h = entete_prepare(primaire, sci_h, o, nom, ext, nan, os.path.basename(masque_chemin))
    if zone is not None:
        y0, y1, x0, x1 = zone
        for k, d in (('CRPIX1', x0), ('CRPIX2', y0)):
            if k in h:
                h[k] = float(h[k]) - d
        h['ORIGNAX1'] = (int(brut.shape[1]), 'width of the original image (pixels)')
        h['ORIGNAX2'] = (int(brut.shape[0]), 'height of the original image (pixels)')
        h['CROPX0'] = (x0 + 1, 'first original column kept (1-based)')
        h['CROPY0'] = (y0 + 1, 'first original row kept (1-based)')
        h.add_history('Cropped to the useful area: columns %d-%d, rows %d-%d of %d x %d (CRPIX shifted).' % (
            x0 + 1, x1 + 1, y0 + 1, y1 + 1, brut.shape[1], brut.shape[0]))
    if poses:
        h['NPOSES'] = (poses, 'exposures combined in this product')
    chemin = str(dest_sans_ext) + ('.xisf' if fmt == 'xisf' else '.fits')
    os.makedirs(os.path.dirname(chemin) or '.', exist_ok=True)
    octets = ecrire_image(chemin, donnees, h, fmt)
    if masque_chemin:
        ecrire_masque(masque_chemin, fini, h)
    return {'chemin': chemin, 'masque': masque_chemin, 'forme': tuple(donnees.shape), 'forme_origine': (int(ny0), int(nx0)),
            'recadrage': list(zone) if zone is not None else None, 'nan': nan, 'wcs': wcs_celeste(h),
            'bunit': str(h.get('BUNIT', '')), 'extension': ext, 'octets': octets, 'poses': poses,
            'exposition': exposition_totale(h), 'entete': h}


def _preparer_planetaire(source, dest_sans_ext, o, fmt, etiquette, nommer=None):
    from astropy.io import fits
    from . import pds
    donnees, meta = pds.lire(source, etiquette)
    if donnees.ndim == 3:
        if donnees.shape[0] != 1:
            raise Inexploitable('%d bands' % donnees.shape[0])
        donnees = donnees[0]
    # PDS et VICAR : ligne 1 = HAUT de l'image ; FITS (et XISF dans Coupole, même ordre) : ligne 1 = BAS.  On
    # retourne les lignes pour que l'image s'affiche comme dans l'archive.
    donnees = np.ascontiguousarray(np.asarray(donnees, dtype=np.float32)[::-1])
    fini = np.isfinite(donnees)
    nan = int(donnees.size - np.count_nonzero(fini))
    if nan:
        donnees = np.where(fini, donnees, np.float32(0))
    h = fits.Header()
    correspondances = (('TELESCOP', ('SPACECRAFT_NAME', 'INSTRUMENT_HOST_NAME')), ('INSTRUME', ('INSTRUMENT_NAME', 'INSTRUMENT_ID')),
                       ('FILTER', ('FILTER_NAME',)), ('OBJECT', ('TARGET_NAME',)),
                       ('DATE-OBS', ('START_TIME', 'IMAGE_TIME')), ('EXPTIME', ('EXPOSURE_DURATION',)),
                       ('PRODUCT', ('PRODUCT_ID',)), ('DATASET', ('DATA_SET_ID',)))
    for k, cles in correspondances:
        for c in cles:
            v = meta.get(c)
            if v not in (None, '', 'N/A'):
                if isinstance(v, tuple):              # valeur avec unité : 1.92 <SECOND>
                    v = v[0]
                if k == 'EXPTIME' and isinstance(v, (int, float)) and str(meta.get(c, '')).upper().find('MS') >= 0:
                    v = v / 1000
                h[k] = _texte_fits(v)[:68] if isinstance(v, str) else v
                break
    if meta.get('_unite'):
        h['BUNIT'] = _texte_fits(meta['_unite'])[:68]
    if (o or {}).get('exposition'):
        # durée annoncée par l'archive, en secondes (le label Cassini donne EXPOSURE_DURATION en millisecondes
        # sans unité : 10000 pour une pose de 10 s)
        h['EXPTIME'] = (float(o['exposition']), '[s] exposure time (from the archive)')
    h2 = entete_prepare(None, h, o, os.path.basename(str(source)), 0, nan, '')
    for k in h:
        if k not in h2:
            h2[k] = h[k]
    h2['PLANFMT'] = (meta.get('_format', ''), 'planetary format of the original')
    h2.add_comment('No celestial WCS: planetary image (spacecraft geometry not applied).')
    h2.add_history('Rows flipped: line 1 of the PDS/VICAR image (top) is the last row here.')
    h2['NPOSES'] = (1, 'exposures combined in this product')
    if nommer is not None:
        dest_sans_ext = nommer(h2)
    chemin = str(dest_sans_ext) + ('.xisf' if fmt == 'xisf' else '.fits')
    os.makedirs(os.path.dirname(chemin) or '.', exist_ok=True)
    octets = ecrire_image(chemin, donnees, h2, fmt)
    return {'chemin': chemin, 'chemins': [chemin], 'masque': '', 'masques': [], 'forme': tuple(donnees.shape),
            'forme_origine': tuple(donnees.shape), 'recadrage': None, 'nan': nan, 'wcs': False,
            'bunit': str(h2.get('BUNIT', '')), 'extension': 0, 'octets': octets, 'poses': 1,
            'exposition': exposition_totale(h2), 'entete': h2}


def recadrer_prepare(chemin, masque: str = '', garder_masque: bool = False) -> dict:
    """Recadre sur sa zone utile une image déjà préparée (0.2.0/0.2.1 : pleine taille + masque non compressé).
    Les NaN sont relus d'après le masque s'il existe ; la WCS est décalée ; le fichier est récrit à sa place
    (atomiquement).  Avec `garder_masque`, un masque compressé ``<nom>_masque.fits`` est écrit (s'il reste des
    pixels sans donnée).  Rend {'recadre', 'avant', 'apres', 'masque'}."""
    from astropy.io import fits
    chemin = str(chemin)
    donnees, h = lire_prepare(chemin)
    if masque:
        m = lire_masque(masque)
        if m is not None and m.shape == donnees.shape:
            donnees = np.where(m, donnees, np.float32(np.nan))
    avant = tuple(donnees.shape)
    zone = zone_utile(donnees)
    recadre = zone is not None and (zone[1] - zone[0] + 1, zone[3] - zone[2] + 1) != avant
    if recadre:
        y0, y1, x0, x1 = zone
        donnees = donnees[y0:y1 + 1, x0:x1 + 1]
        for k, d in (('CRPIX1', x0), ('CRPIX2', y0)):
            if k in h:
                h[k] = float(h[k]) - d
        if 'ORIGNAX1' not in h:
            h['ORIGNAX1'] = (avant[1], 'width of the original image (pixels)')
            h['ORIGNAX2'] = (avant[0], 'height of the original image (pixels)')
        h['CROPX0'] = (int(h.get('CROPX0', 1)) + x0, 'first original column kept (1-based)')
        h['CROPY0'] = (int(h.get('CROPY0', 1)) + y0, 'first original row kept (1-based)')
        h.add_history('Cropped to the useful area by Coupole %s: %d x %d -> %d x %d.' % (
            __version__, avant[1], avant[0], donnees.shape[1], donnees.shape[0]))
    fini = np.isfinite(donnees)
    nan = int(donnees.size - np.count_nonzero(fini))
    donnees = np.where(fini, donnees, np.float32(0)).astype(np.float32)
    nouveau = ''
    if 'MASKFILE' in h:
        del h['MASKFILE']
    h['NANCOUNT'] = (nan, 'pixels without data (NaN in the original)')
    if nan:
        h['NANFILL'] = (0.0, 'value written in place of NaN')
    elif 'NANFILL' in h:
        del h['NANFILL']
    if garder_masque and nan:
        base = chemin[:-5] if chemin.lower().endswith(('.xisf', '.fits')) else chemin
        nouveau = base + '_masque.fits'
        h['MASKFILE'] = (os.path.basename(nouveau), 'mask: 1 = data, 0 = no data')
    if 'DATE' in h:
        del h['DATE']
    for k in ('SIMPLE', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2', 'EXTEND'):
        if k in h:
            del h[k]
    ecrire_image(chemin, donnees, h, 'xisf' if chemin.lower().endswith('.xisf') else 'fits')
    if nouveau:
        ecrire_masque(nouveau, fini, h)
    del fits
    return {'recadre': recadre, 'avant': avant, 'apres': tuple(donnees.shape), 'masque': nouveau}


def valeur_fits(s: str):
    """Valeur d'un mot-clé XISF écrite au format FITS (« 'texte' », T/F, entier, réel) → valeur Python."""
    s = (s or '').strip()
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'").rstrip()
    if s in ('T', 'F'):
        return s == 'T'
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def lire_prepare(chemin) -> tuple[np.ndarray, object]:
    """Relit une image préparée (FITS ou XISF) : (données float32, en-tête astropy) ; NaN rétablis d'après le
    masque s'il existe."""
    from astropy.io import fits
    chemin = str(chemin)
    if chemin.lower().endswith('.xisf'):
        donnees, info = xisf.lire(chemin)
        h = fits.Header()
        for nom, val, com in info.get('mots_cles', []):
            if nom == 'HISTORY':
                h.add_history(com)
            elif nom == 'COMMENT':
                h.add_comment(com)
            elif nom:
                try:
                    h.append((nom, valeur_fits(val), com[:60]), end=True)
                except (ValueError, KeyError):
                    pass
        donnees = np.asarray(donnees, dtype=np.float32)
    else:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with fits.open(chemin, memmap=False) as hd:
                donnees = np.asarray(hd[0].data, dtype=np.float32)
                h = hd[0].header.copy()
    m = h.get('MASKFILE')
    masque = None
    if m:
        cm = os.path.join(os.path.dirname(chemin), str(m))
        if os.path.exists(cm):
            masque = lire_masque(cm)
    if masque is not None and masque.shape == donnees.shape:
        donnees = np.where(masque, donnees, np.float32(np.nan))
    elif (h.get('NANCOUNT') or 0) > 0 and h.get('NANFILL') == 0:
        # pas de masque (réglage par défaut depuis 0.2.2) : les 0 exacts écrits à la place des NaN redeviennent
        # « sans donnée » (une vraie mesure vaut rarement 0 à la précision d'un réel 32 bits)
        donnees = np.where(donnees == 0, np.float32(np.nan), donnees)
    return donnees, h
