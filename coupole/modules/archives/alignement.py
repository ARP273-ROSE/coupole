"""Alignement de plusieurs images d'archive sur une même grille, et aide à la composition couleur.

Méthode (voir ``docs/archives_methode.md``) : les images des archives ont une astrométrie (WCS) exacte ; on ne
cherche donc pas d'étoiles, on **rééchantillonne** chaque image sur une grille commune décrite par une WCS :

* grille de référence : la WCS d'une des images (« le filtre de référence », souvent celui de meilleure
  résolution), ou une grille **optimale** qui couvre toutes les images (``find_optimal_celestial_wcs`` de la
  bibliothèque ``reproject`` si elle est installée ; sinon calcul maison : plan tangent au centre moyen, pas du
  pixel le plus fin, rectangle qui contient toutes les empreintes) ; option : pixels agrandis (`echelle` > 1) pour
  des jeux trop lourds ;
* rééchantillonnage : ``reproject_interp`` (bilinéaire, défaut, le plus rapide), ``reproject_adaptive``
  (anti-crénelage, meilleur quand les pas diffèrent beaucoup) ou ``reproject_exact`` (recouvrement exact des
  pixels, « drizzle » exact, lent ; sa documentation signale une perte de précision sous 0,05″ par pixel : on passe
  alors à l'adaptative) si ``reproject`` est installé ; sinon ``scipy.ndimage.map_coordinates`` (bilinéaire) sur
  les coordonnées calculées par astropy, par blocs de lignes ;
* unités : une brillance de surface (MJy/sr de JWST, …/arcsec²) ne change pas quand le pixel change ; une
  quantité **par pixel** (électrons/s de HST, nanomaggies de SDSS, ADU…) est multipliée par le rapport des
  surfaces de pixel (sortie/entrée), sinon la photométrie serait faussée d'autant ;
* les NaN (masques) sont rétablis avant, et le masque commun (intersection) est écrit à côté ;
* recadrage facultatif sur la zone commune à toutes les images (pas de bords vides en couleur).

Composition : les filtres sont rangés par longueur d'onde ; trois filtres → bleu, vert, rouge ; plus de trois →
**palette chromatique** (teintes réparties du violet au rouge dans l'ordre des longueurs d'onde, comme les images
de presse de Hubble et de JWST : Rector et al. 2007, AJ 133, 598).  On écrit un aperçu PNG (étirement asinh),
le tableau des couleurs et une expression PixelMath prête à coller dans PixInsight.
"""
from __future__ import annotations

import colorsys
import json
import math
import os
import re
import struct
import warnings
import zlib

import numpy as np

from .extraction import ecrire_image, ecrire_masque, lire_prepare

MAX_PIXELS_SORTIE = 400_000_000        # au-delà : demander des pixels plus grands (`echelle`)
LIGNES_PAR_BLOC = 256


def reproject_disponible() -> bool:
    try:
        import reproject  # noqa: F401
        return True
    except Exception:
        return False


def _wcs(h):
    from astropy.wcs import WCS, FITSFixedWarning
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', FITSFixedWarning)
        return WCS(h, naxis=2).celestial


PAS_MIN_EXACTE = 0.05                   # ″ : en dessous, « exacte » devient « adaptative »


def pas_arcsec(w) -> float:
    return math.sqrt(surface_pixel_arcsec2(w))


def surface_pixel_arcsec2(w) -> float:
    from astropy.wcs.utils import proj_plane_pixel_area
    return float(proj_plane_pixel_area(w)) * 3600.0 ** 2


def par_pixel(bunit: str) -> bool:
    """True si l'unité est une quantité par pixel (à corriger du rapport des surfaces), False pour une brillance
    de surface (…/sr, …/arcsec²)."""
    u = (bunit or '').lower().replace(' ', '')
    if not u:
        return True
    return not re.search(r'/sr|sr-1|sr\^-1|/arcsec|arcsec-2|arcsec\*\*-2|arcsec\^-2|/as2|steradian', u)


class Image:
    def __init__(self, chemin):
        self.chemin = str(chemin)
        self.donnees, self.entete = lire_prepare(chemin)
        self.wcs = _wcs(self.entete)
        if not self.wcs.has_celestial:
            raise ValueError('no celestial WCS: %s' % os.path.basename(self.chemin))
        self.lambda_nm = self.entete.get('LAMBDA')
        self.filtre = str(self.entete.get('FILTER') or self.entete.get('FILTER2') or self.entete.get('FILTER1') or '')
        self.bunit = str(self.entete.get('BUNIT') or '')
        self.instrument = str(self.entete.get('INSTRUME') or '')
        self.nom = os.path.splitext(os.path.basename(self.chemin))[0]

    @property
    def forme(self):
        return self.donnees.shape


def grille_optimale(images, echelle: float = 1.0):
    """(WCS, (ny, nx)) qui couvre toutes les images, au pas de la plus fine (× `echelle`)."""
    if reproject_disponible():
        from reproject.mosaicking import find_optimal_celestial_wcs
        pas = min(math.sqrt(surface_pixel_arcsec2(i.wcs)) for i in images) * echelle
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            w, forme = find_optimal_celestial_wcs([(i.forme, i.wcs) for i in images], resolution=pas / 3600.0 * _u_deg())
        return w, tuple(int(x) for x in forme)
    return _grille_maison(images, echelle)


def _u_deg():
    import astropy.units as u
    return u.deg


def _grille_maison(images, echelle: float):
    from astropy.wcs import WCS
    coins = []
    for im in images:
        ny, nx = im.forme
        x = np.array([0, nx - 1, nx - 1, 0, (nx - 1) / 2])
        y = np.array([0, 0, ny - 1, ny - 1, (ny - 1) / 2])
        ra, dec = im.wcs.all_pix2world(x, y, 0)
        coins += list(zip(ra, dec))
    ra = np.array([c[0] for c in coins])
    dec = np.array([c[1] for c in coins])
    vec = np.array([np.cos(np.radians(dec)) * np.cos(np.radians(ra)), np.cos(np.radians(dec)) * np.sin(np.radians(ra)),
                    np.sin(np.radians(dec))]).mean(axis=1)
    ra0 = math.degrees(math.atan2(vec[1], vec[0])) % 360
    dec0 = math.degrees(math.atan2(vec[2], math.hypot(vec[0], vec[1])))
    pas = min(math.sqrt(surface_pixel_arcsec2(i.wcs)) for i in images) * echelle / 3600.0
    w = WCS(naxis=2)
    w.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    w.wcs.crval = [ra0, dec0]
    w.wcs.cdelt = [-pas, pas]
    w.wcs.crpix = [1, 1]
    x, y = w.all_world2pix(ra, dec, 0)
    x0, y0 = math.floor(x.min()), math.floor(y.min())
    w.wcs.crpix = [1 - x0, 1 - y0]
    nx, ny = int(math.ceil(x.max() - x0)) + 1, int(math.ceil(y.max() - y0)) + 1
    return w, (ny, nx)


def grille_reference(im: Image, echelle: float = 1.0):
    if echelle == 1.0:
        return im.wcs.deepcopy(), im.forme
    w = im.wcs.deepcopy()
    ny, nx = im.forme
    if w.wcs.has_cd():
        w.wcs.cd = w.wcs.cd * echelle
    else:
        w.wcs.cdelt = np.array(w.wcs.cdelt) * echelle
    w.wcs.crpix = [(w.wcs.crpix[0] - 0.5) / echelle + 0.5, (w.wcs.crpix[1] - 0.5) / echelle + 0.5]
    return w, (int(math.ceil(ny / echelle)), int(math.ceil(nx / echelle)))


def reechantillonner(im: Image, w_dst, forme, methode: str = 'bilineaire', arret=None) -> np.ndarray:
    """Image `im` sur la grille (w_dst, forme) ; NaN hors de l'image source."""
    if reproject_disponible() and methode in ('bilineaire', 'adaptative', 'exacte', 'proche'):
        from reproject import reproject_adaptive, reproject_exact, reproject_interp
        if methode == 'exacte' and min(pas_arcsec(im.wcs), pas_arcsec(w_dst)) < PAS_MIN_EXACTE:
            methode = 'adaptative'          # reproject_exact perd en précision sous 0,05″ (documentation de reproject)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            if methode == 'exacte':
                sortie, _ = reproject_exact((im.donnees, im.wcs), w_dst, shape_out=forme)
            elif methode == 'adaptative':
                sortie, _ = reproject_adaptive((im.donnees, im.wcs), w_dst, shape_out=forme, conserve_flux=False,
                                               boundary_mode='ignore')
            else:
                sortie, _ = reproject_interp((im.donnees, im.wcs), w_dst, shape_out=forme,
                                             order='bilinear' if methode == 'bilineaire' else 'nearest-neighbor')
        return np.asarray(sortie, dtype=np.float32)
    from scipy.ndimage import map_coordinates
    ny, nx = forme
    sortie = np.full(forme, np.nan, dtype=np.float32)
    xs = np.arange(nx, dtype=np.float64)
    ordre = 0 if methode == 'proche' else 1
    for y0 in range(0, ny, LIGNES_PAR_BLOC):
        if arret is not None and arret.is_set():
            raise InterruptedError()
        y1 = min(ny, y0 + LIGNES_PAR_BLOC)
        X, Y = np.meshgrid(xs, np.arange(y0, y1, dtype=np.float64))
        ra, dec = w_dst.all_pix2world(X, Y, 0)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            px, py = im.wcs.all_world2pix(ra, dec, 0, quiet=True)
        sortie[y0:y1] = map_coordinates(im.donnees, [py, px], order=ordre, mode='constant', cval=np.nan,
                                        prefilter=False).astype(np.float32)
    return sortie


def plus_grand_rectangle(masque: np.ndarray) -> tuple[int, int, int, int] | None:
    """(y0, y1, x0, x1) du plus grand rectangle aligné sur les axes entièrement à True (méthode de l'histogramme
    par ligne, pile monotone : O(lignes × colonnes)).  None si aucun pixel."""
    ny, nx = masque.shape
    hauteurs = np.zeros(nx, dtype=np.int64)
    meilleur, res = 0, None
    for y in range(ny):
        hauteurs = np.where(masque[y], hauteurs + 1, 0)
        pile = []
        for x in range(nx + 1):
            h = int(hauteurs[x]) if x < nx else 0
            debut = x
            while pile and pile[-1][1] >= h:
                xd, hd = pile.pop()
                aire = hd * (x - xd)
                if aire > meilleur:
                    meilleur, res = aire, (y - hd + 1, y + 1, xd, x)
                debut = xd
            pile.append((debut, h))
    return res


def zone_commune(masques, cote: int = 240, part: float = 0.9) -> tuple[slice, slice] | None:
    """Plus grand rectangle couvert par TOUTES les images, calculé sur le masque commun réduit à au plus `cote`
    blocs de côté : un bloc compte comme couvert si au moins `part` de ses pixels le sont.  Ainsi une colonne
    morte ou un petit trou au milieu d'une mosaïque (fréquents sur JWST et HST) ne réduit pas le recadrage à une
    bande étroite ; ces quelques pixels restent sans donnée (0 et masque).  None si les images ne se recouvrent pas."""
    commun = np.logical_and.reduce(masques)
    if not commun.any():
        return None
    k = max(1, int(math.ceil(max(commun.shape) / cote)))
    ny, nx = int(math.ceil(commun.shape[0] / k)), int(math.ceil(commun.shape[1] / k))
    plein = np.zeros((ny * k, nx * k), dtype=np.float32)
    plein[:commun.shape[0], :commun.shape[1]] = commun
    reduit = plein.reshape(ny, k, nx, k).mean(axis=(1, 3)) >= (part if k > 1 else 1.0)
    r = plus_grand_rectangle(reduit)
    if r is None:
        return None
    y0, y1, x0, x1 = r
    return slice(y0 * k, min(commun.shape[0], y1 * k)), slice(x0 * k, min(commun.shape[1], x1 * k))


def entete_grille(base, w, forme):
    from astropy.io import fits
    h = fits.Header()
    for k in base:
        if k in ('HISTORY', 'COMMENT', '') or re.match(r'^(WCSAXES|CTYPE|CRVAL|CRPIX|CDELT|CUNIT|CD\d|PC\d|PV\d|PS\d|'
                                                        r'LONPOLE|LATPOLE|RADESYS|EQUINOX|A_|B_|AP_|BP_|NAXIS|MASKFILE|'
                                                        r'NANCOUNT|NANFILL)', k):
            continue
        try:
            h[k] = (base[k], base.comments[k])
        except Exception:
            pass
    h.update(w.to_header(relax=False))
    for k in ('COMMENT', 'HISTORY'):
        for v in base.get(k, []) or []:
            (h.add_comment if k == 'COMMENT' else h.add_history)(str(v))
    return h


def aligner(chemins, dossier, reference: int | None = 0, methode: str = 'bilineaire', echelle: float = 1.0,
            recadrer: bool = True, fmt: str = 'xisf', arret=None, progression=None) -> dict:
    """Aligne les images préparées `chemins` dans `dossier`.  `reference` : indice de l'image dont la grille sert
    (None : grille optimale).  Rend {'fichiers', 'masque', 'forme', 'grille', 'composition', 'apercu'}."""
    progression = progression or (lambda *a: None)
    images = [Image(c) for c in chemins]
    if len(images) < 1:
        raise ValueError('no image')
    if reference is None:
        w, forme = grille_optimale(images, echelle)
        grille = 'optimale'
    else:
        w, forme = grille_reference(images[reference], echelle)
        grille = images[reference].nom
    if forme[0] * forme[1] > MAX_PIXELS_SORTIE:
        raise MemoryError('output grid %d x %d too large: increase the pixel scale' % (forme[1], forme[0]))
    os.makedirs(dossier, exist_ok=True)
    surf_dst = surface_pixel_arcsec2(w)
    sorties = []
    for k, im in enumerate(images):
        progression(k, len(images), im.nom)
        a = reechantillonner(im, w, forme, methode, arret)
        if par_pixel(im.bunit):
            a *= np.float32(surf_dst / surface_pixel_arcsec2(im.wcs))
        sorties.append(a)
        im.donnees = None                                  # libère l'original
    masques = [np.isfinite(a) for a in sorties]
    coupe = zone_commune(masques) if recadrer else None
    if coupe is not None and recadrer:
        sorties = [a[coupe] for a in sorties]
        masques = [m[coupe] for m in masques]
        w = w.slice(coupe)
        forme = sorties[0].shape
    commun = np.logical_and.reduce(masques)
    fichiers = []
    for im, a, m in zip(images, sorties, masques):
        h = entete_grille(im.entete, w, forme)
        h.add_history('Reprojected by Coupole onto grid %s (%s%s)' % (grille, methode,
                                                                       ', reproject' if reproject_disponible() else ''))
        nan = int(m.size - np.count_nonzero(m))
        if nan:
            h['NANCOUNT'] = (nan, 'pixels without data after reprojection')
            h['MASKFILE'] = ('masque_commun.fits', 'common mask: 1 = data in every image')
        chemin = os.path.join(dossier, im.nom + '_aligne' + ('.xisf' if fmt == 'xisf' else '.fits'))
        ecrire_image(chemin, np.where(m, a, np.float32(0)), h, fmt)
        fichiers.append(chemin)
    ecrire_masque(os.path.join(dossier, 'masque_commun.fits'), commun, entete_grille(images[0].entete, w, forme))
    compo = composition([(im.nom, im.filtre, im.lambda_nm, im.instrument) for im in images])
    apercu = os.path.join(dossier, 'apercu_couleur.png')
    ecrire_apercu_couleur(apercu, sorties, compo)
    ecrire_composition(os.path.join(dossier, 'composition.txt'), compo, fichiers)
    resume = {'fichiers': fichiers, 'masque': os.path.join(dossier, 'masque_commun.fits'), 'forme': list(forme),
              'grille': grille, 'methode': methode, 'reproject': reproject_disponible(), 'composition': compo,
              'apercu': apercu}
    with open(os.path.join(dossier, 'alignement.json'), 'w', encoding='utf-8') as f:
        json.dump(resume, f, ensure_ascii=False, indent=1)
    return resume


# ============================================================================================ composition
def couleur_chromatique(rang: int, n: int) -> tuple[float, float, float]:
    """Couleur du `rang`-ième filtre (0 = plus courte longueur d'onde) parmi `n` : teinte de 270° (violet-bleu)
    à 0° (rouge).  n = 3 : bleu, vert, rouge purs."""
    if n == 1:
        return (1.0, 1.0, 1.0)
    if n == 3:
        return [(0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)][rang]
    if n == 2:
        return [(0.0, 0.5, 1.0), (1.0, 0.5, 0.0)][rang]
    teinte = (240.0 - 240.0 * rang / (n - 1)) / 360.0
    return colorsys.hsv_to_rgb(teinte, 1.0, 1.0)


def composition(images: list[tuple]) -> list[dict]:
    """[(nom, filtre, lambda_nm[, instrument])] → [{'nom', 'filtre', 'lambda_nm', 'rang', 'couleur': (r, g, b)}] dans l'ordre
    d'entrée ; les longueurs d'onde inconnues sont déduites du nom du filtre (F444W → 4 440 nm, F656N → 656 nm)."""
    rows = []
    for ligne in images:
        nom, filtre, lam = ligne[:3]
        instrument = ligne[3] if len(ligne) > 3 else ''
        rows.append({'nom': nom, 'filtre': filtre, 'lambda_nm': lam if lam else lambda_filtre(filtre, instrument)})
    ordre = sorted(range(len(rows)), key=lambda i: (rows[i]['lambda_nm'] is None, rows[i]['lambda_nm'] or 0, i))
    for rang, i in enumerate(ordre):
        rows[i]['rang'] = rang
        rows[i]['couleur'] = tuple(round(c, 3) for c in couleur_chromatique(rang, len(rows)))
    return rows


def lambda_filtre(filtre: str, instrument: str = ''):
    """Longueur d'onde (nm) d'après un nom de filtre de type Hubble/JWST (F + 3 ou 4 chiffres + lettres).
    JWST (NIRCam, NIRISS, MIRI) et l'infrarouge de Hubble (WFC3/IR, NICMOS) : centièmes de µm (F444W → 4 440 nm,
    F1000W → 10 000 nm, F160W → 1 600 nm) ; visible de Hubble (ACS, WFC3/UVIS, WFPC2) : nm (F435W → 435 nm)."""
    m = re.search(r'F(\d{3,4})(W2|W|M|N|LP|X)?\b', (filtre or '').upper())
    if not m:
        return None
    v = int(m.group(1))
    ins = (instrument or '').upper()
    if len(m.group(1)) == 4 or any(x in ins for x in ('NIRCAM', 'NIRISS', 'MIRI', 'NIRSPEC', '/IR', 'NICMOS')):
        return v * 10.0
    if ins:
        return float(v)
    return v * 10.0 if v < 200 else float(v)


def etirer(a: np.ndarray, bas: float = 0.5, haut: float = 99.7, beta: float = 8.0) -> np.ndarray:
    """Étirement asinh entre deux centiles des pixels finis, rendu entre 0 et 1."""
    fin = a[np.isfinite(a)]
    if fin.size == 0:
        return np.zeros_like(a, dtype=np.float32)
    echant = fin[:: max(1, fin.size // 2_000_000)]
    lo, hi = np.percentile(echant, [bas, haut])
    if hi <= lo:
        hi = lo + 1.0
    x = np.clip((np.nan_to_num(a, nan=lo) - lo) / (hi - lo), 0, None)
    return (np.arcsinh(beta * x) / np.arcsinh(beta)).clip(0, 1).astype(np.float32)


def reduire(a: np.ndarray, cote: int = 1600) -> np.ndarray:
    k = max(1, int(math.ceil(max(a.shape[:2]) / cote)))
    return a[::k, ::k]


def ecrire_apercu_couleur(chemin, sorties, compo, cote: int = 1600):
    canaux = np.zeros(reduire(sorties[0], cote).shape + (3,), dtype=np.float32)
    poids = np.zeros(3, dtype=np.float32)
    for a, c in zip(sorties, compo):
        e = etirer(reduire(a, cote))
        for k in range(3):
            canaux[..., k] += e * c['couleur'][k]
        poids += np.array(c['couleur'], dtype=np.float32)
    canaux /= np.maximum(poids, 1e-6)
    ecrire_png(chemin, (canaux * 255 + 0.5).clip(0, 255).astype(np.uint8))


def ecrire_png(chemin, img: np.ndarray):
    """PNG 8 bits (niveaux de gris ou RVB), ligne 0 = haut de l'image : on retourne l'image (en astronomie la ligne
    0 du FITS est en bas)."""
    img = np.ascontiguousarray(img[::-1])
    h, w = img.shape[:2]
    genre = 2 if img.ndim == 3 else 0
    brut = b''.join(b'\x00' + img[y].tobytes() for y in range(h))

    def bloc(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    donnees = b'\x89PNG\r\n\x1a\n' + bloc(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, genre, 0, 0, 0)) + \
        bloc(b'IDAT', zlib.compress(brut, 6)) + bloc(b'IEND', b'')
    tmp = str(chemin) + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(donnees)
    os.replace(tmp, str(chemin))


def ecrire_apercu_gris(chemin, a: np.ndarray, cote: int = 800):
    ecrire_png(chemin, (etirer(reduire(a, cote)) * 255 + 0.5).astype(np.uint8))


def identifiant_pixinsight(nom: str) -> str:
    """Identifiant que PixInsight donne à une image ouverte : lettres, chiffres et « _ » seulement, jamais un chiffre
    en tête (« jw02739-o002_…_aligne » → « jw02739_o002_…_aligne »)."""
    s = re.sub(r'[^A-Za-z0-9_]', '_', nom)
    return '_' + s if not s or s[0].isdigit() else s


def ecrire_composition(chemin, compo, fichiers):
    lignes = ['# Coupole: chromatic ordering (shortest wavelength = bluest)', '#',
              '# image\tfilter\tlambda_nm\tR\tG\tB']
    for c in sorted(compo, key=lambda c: c['rang']):
        lignes.append('%s\t%s\t%s\t%.3f\t%.3f\t%.3f' % (c['nom'], c['filtre'], '%.0f' % c['lambda_nm'] if c['lambda_nm'] else '?',
                                                       *c['couleur']))
    noms = [identifiant_pixinsight(os.path.splitext(os.path.basename(f))[0]) for f in fichiers]
    expr = []
    for k in range(3):
        termes = ['%.3f*%s' % (c['couleur'][k], n) for c, n in zip(compo, noms) if c['couleur'][k] > 0]
        poids = sum(c['couleur'][k] for c in compo) or 1
        expr.append('(%s)/%.3f' % (' + '.join(termes) or '0', poids))
    lignes += ['', '# PixelMath (PixInsight): open the aligned files (identifiers below), stretch them, then',
               '# "Use a single RGB/K expression" unchecked, "Create new image" (RGB):',
               'R: ' + expr[0], 'G: ' + expr[1], 'B: ' + expr[2]]
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes) + '\n')
