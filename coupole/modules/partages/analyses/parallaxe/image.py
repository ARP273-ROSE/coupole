"""Mesures sur les images : centre de la Lune, position de l'ISS, passage pixel → (α, δ) par la solution astrométrique.

* Lecture : FITS (2-D, ou cube couleur 3 × H × W ramené à la luminance) par astropy ; JPEG/PNG/TIFF par Qt
  (QImage, utilisable hors du fil graphique).  Les lignes d'un FITS sont rangées du bas vers le haut ; celles d'un
  JPEG du haut vers le bas : la WCS d'un FITS se lit donc sur le tableau du FITS lui-même.
* Solution astrométrique : WCS de l'en-tête (TAN, TAN-SIP… : astropy.wcs), ou fichier « .wcs » d'astrometry.net /
  ASTAP posé à côté de l'image.
* **Centre de la Lune** : la Lune est le plus grand objet brillant ; son bord est ajusté par un cercle (moindres
  carrés algébriques de Kåsa), en écartant à chaque tour les points du bord situés à l'intérieur du cercle : le
  terminateur d'une Lune gibbeuse ou d'un croissant est une demi-ellipse INTÉRIEURE au disque, il ne tire donc pas
  le centre.  Incertitude : dispersion des points du limbe divisée par la racine de leur nombre.
* **ISS** : dans une série de poses courtes, l'objet qui bouge d'une image à l'autre (image moins la médiane de ses
  voisines) ; dans une pose seule, le trait le plus allongé (extrémités = début et fin de la pose).
"""
from __future__ import annotations

import math
import os
import warnings
from dataclasses import dataclass

import numpy as np


class ImageIllisible(ValueError):
    pass


@dataclass
class Image:
    donnees: np.ndarray            # 2-D float32, ligne 0 = première ligne du fichier (bas de l'image pour un FITS)
    entete: dict                   # mots-clés FITS utiles (ou EXIF), valeurs Python
    wcs: object = None             # astropy.wcs.WCS (2-D) ou None
    chemin: str = ''


def entete_propre(h):
    """Copie d'un en-tête sans les cartes illisibles (logiciels qui écrivent « TRUE » ou de l'hexadécimal)."""
    from astropy.io import fits
    propre = fits.Header()
    for carte in h.cards:
        try:
            if carte.keyword in ('COMMENT', 'HISTORY', ''):
                continue
            _ = carte.value
            propre.append(carte, end=True)
        except Exception:
            continue
    return propre


CLES_WCS = ('CTYPE1', 'CTYPE2', 'CUNIT1', 'CUNIT2', 'CRPIX1', 'CRPIX2', 'CRVAL1', 'CRVAL2', 'CD1_1', 'CD1_2',
            'CD2_1', 'CD2_2', 'PC1_1', 'PC1_2', 'PC2_1', 'PC2_2', 'CDELT1', 'CDELT2', 'CROTA2', 'LONPOLE', 'LATPOLE',
            'RADESYS', 'RADECSYS', 'EQUINOX', 'A_ORDER', 'B_ORDER', 'AP_ORDER', 'BP_ORDER', 'PV2_1', 'PV2_2')


def _wcs_de_entete(h):
    """WCS céleste 2-D d'après les seuls mots-clés WCS standard (les en-têtes de certains logiciels contiennent des
    mots-clés qui font échouer la lecture complète)."""
    try:
        import re as _re
        from astropy.io import fits
        from astropy.wcs import WCS
        m = fits.Header()
        m['NAXIS'] = 2
        for k in ('NAXIS1', 'NAXIS2'):
            if k in h:
                m[k] = h[k]
        for k in h.keys():
            if k in CLES_WCS or _re.match(r'^(A|B|AP|BP)_\d+_\d+$', k):
                v = h[k]
                if isinstance(v, str):
                    v = v.strip()
                    if k.startswith('CUNIT'):
                        v = v.lower()
                m[k] = v
        if 'CTYPE1' not in m or 'CRVAL1' not in m:
            return None
        if any(k in m for k in ('CD1_1', 'CD2_2')):
            for k in ('CDELT1', 'CDELT2', 'CROTA2'):
                m.remove(k, ignore_missing=True)
        if 'A_ORDER' in m and not str(m['CTYPE1']).endswith('-SIP'):
            m['CTYPE1'], m['CTYPE2'] = str(m['CTYPE1']) + '-SIP', str(m['CTYPE2']) + '-SIP'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            w = WCS(m)
        return w if w.has_celestial else None
    except Exception:
        return None


def wcs_annexe(chemin: str):
    """Fichier .wcs (astrometry.net, ASTAP) posé à côté de l'image : « image.wcs » ou « image.fits.wcs »."""
    base = os.path.splitext(chemin)[0]
    for c in (base + '.wcs', chemin + '.wcs'):
        if os.path.isfile(c):
            try:
                from astropy.io import fits
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    with fits.open(c) as h:
                        return _wcs_de_entete(h[0].header)
            except Exception:
                continue
    return None


def lire(chemin: str, garder_couleur: bool = False) -> Image:
    n = chemin.lower()
    if n.endswith(('.fits', '.fit', '.fts', '.fz')):
        from astropy.io import fits
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with fits.open(chemin, memmap=False) as hdul:
                hdu = next((h for h in hdul if getattr(h, 'data', None) is not None and h.data.ndim >= 2), None)
                if hdu is None:
                    raise ImageIllisible('no image')
                a = np.asarray(hdu.data, dtype=np.float32)
                if a.ndim == 3:
                    a = a.mean(axis=0) if a.shape[0] <= 4 else a[0]
                elif a.ndim > 3:
                    raise ImageIllisible('cube')
                h = entete_propre(hdu.header)
                ent = {k: h[k] for k in h.keys() if k and k not in ('COMMENT', 'HISTORY', '')}
                w = _wcs_de_entete(h) or wcs_annexe(chemin)
        return Image(a, ent, w, chemin)
    from PyQt6.QtGui import QImage
    q = QImage(chemin)
    if q.isNull():
        raise ImageIllisible('unreadable')
    q = q.convertToFormat(QImage.Format.Format_Grayscale16)
    w_, h_ = q.width(), q.height()
    ptr = q.constBits()
    ptr.setsize(q.sizeInBytes())
    a = np.frombuffer(ptr, dtype=np.uint16).reshape(h_, q.bytesPerLine() // 2)[:, :w_].astype(np.float32)
    return Image(a, {}, wcs_annexe(chemin), chemin)


def pixel_vers_radec(img: Image, x: float, y: float) -> tuple[float, float]:
    """(x, y) en pixels du tableau (origine 0) → (α, δ) en degrés, ICRS (distorsions SIP comprises)."""
    if img.wcs is None:
        raise ImageIllisible('no WCS')
    ra, dec = img.wcs.all_pix2world([[x, y]], 0)[0]
    return float(ra) % 360.0, float(dec)


def echelle_arcsec(img: Image) -> float:
    if img.wcs is None:
        return float('nan')
    from astropy.wcs.utils import proj_plane_pixel_scales
    return float(np.mean(proj_plane_pixel_scales(img.wcs.celestial))) * 3600.0


# ============================================================================================== Lune
def _reduire(a: np.ndarray, maxi: int = 1500) -> tuple[np.ndarray, int]:
    f = max(1, int(math.ceil(max(a.shape) / maxi)))
    if f == 1:
        return a, 1
    h, w = (a.shape[0] // f) * f, (a.shape[1] // f) * f
    return a[:h, :w].reshape(h // f, f, w // f, f).mean(axis=(1, 3)), f


def ajuster_cercle(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Cercle de Kåsa (moindres carrés algébriques) : (xc, yc, r)."""
    A = np.column_stack([x, y, np.ones_like(x)])
    b = x * x + y * y
    c = np.linalg.lstsq(A, b, rcond=None)[0]
    xc, yc = c[0] / 2, c[1] / 2
    return float(xc), float(yc), float(math.sqrt(max(0.0, c[2] + xc * xc + yc * yc)))


def _cercle_seuil(a, lisse_plein, fond, pic, f, centre_pic):
    """Cercle du limbe pour un seuil fond + f (pic − fond) : composante qui contient le pic, bord ajusté en écartant
    les points intérieurs (terminateur)."""
    from scipy import ndimage
    seuil = fond + f * (pic - fond)
    m = lisse_plein > seuil
    etiq, n = ndimage.label(m)
    if n == 0:
        return None
    k = etiq[centre_pic]
    if k == 0:
        return None
    objet = ndimage.binary_fill_holes(etiq == k)
    bord = objet & ~ndimage.binary_erosion(objet)
    by, bx = np.nonzero(bord)
    if len(bx) < 20:
        return None
    bx = bx.astype(float)
    by = by.astype(float)
    xc, yc, r = ajuster_cercle(bx, by)
    garde = np.ones(len(bx), bool)
    for _ in range(8):
        d = np.hypot(bx - xc, by - yc) - r
        nouv = d > -max(1.5, 0.01 * r)           # le limbe est SUR le cercle ; le terminateur à l'intérieur
        if nouv.sum() < 20 or (nouv == garde).all():
            break
        garde = nouv
        xc, yc, r = ajuster_cercle(bx[garde], by[garde])
    res = np.hypot(bx[garde] - xc, by[garde] - yc) - r
    return {'x': xc, 'y': yc, 'r': r, 'sigma_px': max(float(np.std(res)) / math.sqrt(max(1, garde.sum())) * 2.0,
                                                      0.05),
            'rms_px': float(np.std(res)), 'points': int(garde.sum()), 'phase_part': float(garde.sum() / len(bx)),
            'seuil': f}


SEUILS = (0.95, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3)


def centre_lune(a: np.ndarray, rayon_attendu_px: float | None = None) -> dict:
    """Centre et rayon du disque lunaire (pixels du tableau, origine 0).  Rend {'x', 'y', 'r', 'sigma_px', 'rms_px',
    'points', 'phase_part', 'seuil', 'rapport_rayon'} ; lève ImageIllisible si aucun disque n'est trouvé.

    Plusieurs seuils sont essayés (une Lune surexposée est entourée d'un halo qui grossit le disque à seuil bas) :
    avec le rayon attendu (distance approchée et échelle de l'image), on garde le seuil dont le cercle a le rayon le
    plus proche ; sans lui, le seuil à mi-hauteur."""
    from scipy import ndimage
    a = np.nan_to_num(a.astype(np.float32))
    petit, f = _reduire(a)
    lisse = ndimage.gaussian_filter(petit, 1.0)
    fond = float(np.median(lisse))
    iy, ix = np.unravel_index(int(np.argmax(lisse)), lisse.shape)
    pic = float(lisse[iy, ix])
    if pic <= fond:
        raise ImageIllisible('flat image')
    # zone de travail en pleine résolution : l'objet au seuil le plus bas
    m = lisse > fond + min(SEUILS) * (pic - fond)
    etiq, _ = ndimage.label(m)
    k = etiq[iy, ix]
    ys, xs = np.nonzero(etiq == k)
    marge = 6 * f
    y0, y1 = max(0, ys.min() * f - marge), min(a.shape[0], (ys.max() + 1) * f + marge)
    x0, x1 = max(0, xs.min() * f - marge), min(a.shape[1], (xs.max() + 1) * f + marge)
    zone = ndimage.gaussian_filter(a[y0:y1, x0:x1], 0.7)
    zy, zx = np.unravel_index(int(np.argmax(zone)), zone.shape)
    zpic = float(zone[zy, zx])
    essais = []
    for s in SEUILS:
        c = _cercle_seuil(zone, zone, fond, zpic, s, (zy, zx))
        if c is not None:
            c['x'] += x0
            c['y'] += y0
            essais.append(c)
    if not essais:
        raise ImageIllisible('no Moon')
    if rayon_attendu_px:
        choix = min(essais, key=lambda c: abs(math.log(max(c['r'], 1e-3) / rayon_attendu_px)))
        choix['rapport_rayon'] = choix['r'] / rayon_attendu_px
    else:
        choix = min(essais, key=lambda c: abs(c['seuil'] - 0.5))
        choix['rapport_rayon'] = None
    choix['essais'] = [(c['seuil'], c['x'], c['y'], c['r']) for c in essais]
    # saturation : part du disque ajusté au niveau maximal de l'image (Lune « brûlée » : bord et centre douteux)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    dans = (xx - choix['x']) ** 2 + (yy - choix['y']) ** 2 <= choix['r'] ** 2
    choix['saturation'] = float(np.mean(a[dans] >= 0.995 * float(a.max()))) if dans.any() else 0.0
    choix['douteux'] = bool(choix['saturation'] > 0.5 or (choix['rapport_rayon'] is not None and
                                                           not 0.8 < choix['rapport_rayon'] < 1.25))
    return choix


# ============================================================================================== ISS
def objet_mobile(courante: np.ndarray, voisines: list) -> dict:
    """Position de l'objet qui bouge : courante − médiane des voisines ; barycentre de la tache la plus brillante.
    Rend {'x', 'y', 'flux', 'longueur', 'x1', 'y1', 'x2', 'y2'} (extrémités si la tache est un trait)."""
    from scipy import ndimage
    ref = np.median(np.stack([np.asarray(v, np.float32) for v in voisines]), axis=0) if len(voisines) > 1 \
        else np.asarray(voisines[0], np.float32)
    diff = np.asarray(courante, np.float32) - ref
    return _tache(ndimage.gaussian_filter(diff, 1.0))


def trait_principal(a: np.ndarray) -> dict:
    """Pose seule : le trait le plus long (ISS en pose longue)."""
    from scipy import ndimage
    lisse = ndimage.gaussian_filter(np.nan_to_num(a.astype(np.float32)), 1.0)
    fond = ndimage.median_filter(lisse[::8, ::8], 9)
    fond = np.kron(fond, np.ones((8, 8), np.float32))[:lisse.shape[0], :lisse.shape[1]]
    return _tache(lisse - fond, allonge=True)


def _tache(d: np.ndarray, allonge: bool = False) -> dict:
    from scipy import ndimage
    med = float(np.median(d))
    mad = float(np.median(np.abs(d - med))) * 1.4826 or 1.0
    m = d > med + 6 * mad
    etiq, n = ndimage.label(m)
    if n == 0:
        raise ImageIllisible('no moving object')
    meilleur, score = None, -1.0
    for k, sl in enumerate(ndimage.find_objects(etiq), 1):
        ys, xs = np.nonzero(etiq[sl] == k)
        if len(xs) < 3:
            continue
        ys = ys + sl[0].start
        xs = xs + sl[1].start
        w = d[ys, xs] - med
        if allonge:
            c = np.cov(np.vstack([xs, ys]))
            ev = np.linalg.eigvalsh(c)
            s = math.sqrt(max(ev[-1], 0)) * (1 - math.sqrt(max(ev[0], 0) / max(ev[-1], 1e-9)))
        else:
            s = float(w.sum())
        if s > score:
            meilleur, score = (xs, ys, w), s
    if meilleur is None:
        raise ImageIllisible('no moving object')
    xs, ys, w = meilleur
    x, y = float(np.average(xs, weights=w)), float(np.average(ys, weights=w))
    c = np.cov(np.vstack([xs, ys]), aweights=w) if len(xs) > 2 else np.eye(2)
    ev, vec = np.linalg.eigh(c)
    axe = vec[:, -1]
    proj = (xs - x) * axe[0] + (ys - y) * axe[1]
    return {'x': x, 'y': y, 'flux': float(w.sum()), 'longueur': float(proj.max() - proj.min()),
            'x1': float(x + proj.min() * axe[0]), 'y1': float(y + proj.min() * axe[1]),
            'x2': float(x + proj.max() * axe[0]), 'y2': float(y + proj.max() * axe[1])}


# ============================================================================================== en-têtes
def lieu_et_heure(entete: dict) -> dict:
    """Lieu et heure d'un en-tête FITS : SITELAT/SITELONG (« +44:13:51 » ou décimal), OBSGEO-*, DATE-OBS (début)
    + EXPTIME/2 (milieu de pose).  Valeurs absentes : None."""
    import datetime as D
    from ...mesures import angle
    out = {'lat': None, 'lon': None, 'alt_m': None, 'instant': None, 'milieu': None, 'pose_s': None}
    for cles, champ in ((('SITELAT', 'OBSLAT', 'LAT-OBS', 'OBSGEO-B', 'LATITUDE'), 'lat'),
                        (('SITELONG', 'OBSLONG', 'LONG-OBS', 'OBSGEO-L', 'LONGITUD'), 'lon')):
        for c in cles:
            if c in entete and entete[c] not in (None, ''):
                v = angle(entete[c]).valeur
                if v is not None:
                    out[champ] = v
                    break
    for c in ('SITEELEV', 'OBSGEO-H', 'ALT-OBS', 'ELEVATIO'):
        if c in entete:
            try:
                out['alt_m'] = float(entete[c])
                break
            except (TypeError, ValueError):
                pass
    texte = str(entete.get('DATE-OBS') or '')
    if texte and 'T' not in texte and entete.get('TIME-OBS'):
        texte = texte + 'T' + str(entete['TIME-OBS'])
    try:
        t = D.datetime.fromisoformat(texte.strip().replace('Z', ''))
        out['instant'] = t.replace(tzinfo=D.timezone.utc)
    except ValueError:
        pass
    for c in ('EXPTIME', 'EXPOSURE'):
        try:
            out['pose_s'] = float(entete[c])
            break
        except (KeyError, TypeError, ValueError):
            pass
    if out['instant'] is not None:
        out['milieu'] = out['instant'] + D.timedelta(seconds=(out['pose_s'] or 0.0) / 2)
    return out
