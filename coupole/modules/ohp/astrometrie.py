"""Contrôle de la solution astrométrique (repris de ohp_xisf.py).

Contrôles de cohérence, toujours faits (sans ASTAP) :
  * solution présente et lisible ;
  * échelle à moins de 2 % de la nominale (XPIXSZ/FOCALLEN) ou de la médiane
    de la nuit (même instrument, même taille d'image) ;
  * angle à moins de 5° de la médiane de la nuit (modulo 180°) ;
  * centre à moins de 1,5° du médoïde de l'objet (fixe) ou 2° du médoïde
    objet+nuit (mobile).
Les médianes et médoïdes viennent de l'inventaire ENTIER (colonnes ObsCore,
calculées par la base depuis la même solution WCS que l'en-tête).
"""
from __future__ import annotations

import collections as C
import math
import warnings

import numpy as np

from ...core.astro import cap, ecart_angle, mediane_angle, sep_deg
from .cibles import FIXES

TOL_ECHELLE = 0.02
TOL_ANGLE = 5.0
DIST_FIXE = 1.5
DIST_MOBILE = 2.0
ACCORD_ASTAP = 10.0        # secondes d'arc : ASTAP « confirme »
DESACCORD_ASTAP = 60.0


def wcs_de(ent, nx, ny):
    """Solution de l'en-tête → {'ra','dec','echelle','angle','parite'} ou None."""
    ct1 = ent.gets('CTYPE1') or ''
    if not ct1.startswith('RA--') or ent.getf('CRVAL1') is None:
        return None
    from astropy.wcs import WCS, FITSFixedWarning
    h = ent.header_astropy()
    h['NAXIS'] = 2
    h['NAXIS1'] = nx
    h['NAXIS2'] = ny
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', FITSFixedWarning)
            warnings.simplefilter('ignore', UserWarning)
            w = WCS(h, relax=True)
            ra, de = (float(v) for v in w.all_pix2world([[(nx + 1) / 2, (ny + 1) / 2]], 1)[0])
            cd = w.pixel_scale_matrix
    except Exception:
        return None
    det = cd[0, 0] * cd[1, 1] - cd[0, 1] * cd[1, 0]
    if not np.isfinite(det) or det == 0 or not np.isfinite(ra) or not np.isfinite(de):
        return None
    return {'ra': ra % 360, 'dec': de, 'echelle': math.sqrt(abs(det)) * 3600,
            'angle': math.degrees(math.atan2(cd[0, 1], cd[1, 1])) % 360, 'parite': 1 if det < 0 else -1}


def cle_classe(x):
    """(télescope, nuit, taille, classe d'échelle) ; 4096 px : colonne d'échelle fausse dans la base."""
    nx = int(x['s_xel1'])
    return (x['tel'], str(x['nuit']), nx, 0 if nx == 4096 else round(x['s_pixel_scale'] / 0.02))


def cle_groupe(x):
    return x['objet'] if x['cat'] in FIXES else (x['objet'], str(x['nuit']))


def attentes(d):
    """Médianes par classe et médoïdes de position, sur tout l'inventaire (hors doublons)."""
    angles = {}
    for x in d:
        if not x['doublon']:
            pts = [float(v) for v in x['s_region'].split()[2:]]
            angles[x['access_url']] = cap(pts[0], pts[1], pts[2], pts[3]) if len(pts) >= 4 else None
    grp = C.defaultdict(list)
    for x in d:
        if not x['doublon']:
            grp[cle_classe(x)].append(x)
    med = {}
    for k, xs in grp.items():
        if len(xs) < 3:
            continue
        ech = [x['s_pixel_scale'] for x in xs if x['s_pixel_scale'] > 0.1]
        med[k] = {'echelle': float(np.median(ech)) if ech and k[3] else None, 'n': len(xs),
                  'angle': mediane_angle([angles[x['access_url']] for x in xs
                                          if angles[x['access_url']] is not None])}
    pos = C.defaultdict(list)
    for x in d:
        if not x['doublon']:
            pos[cle_groupe(x)].append((x['s_ra'], x['s_dec'], x['s_fov']))
    medo = {}
    for k, v in pos.items():
        v2 = v[::len(v) // 400 + 1] if len(v) > 400 else v
        best, bn = v2[0], -1
        for a in v2:
            n = sum(1 for b in v2 if sep_deg(a[0], a[1], b[0], b[1]) < max(a[2], 0.2))
            if n > bn:
                best, bn = a, n
        medo[k] = (best[0], best[1], len(v))
    return med, medo


def attentes_pour(x, med, medo):
    """Sous-ensemble utile à une image (léger à transmettre à un processus de conversion)."""
    nx = int(x['s_xel1'])
    m = {k: v for k, v in med.items() if k[:3] == (x['tel'], str(x['nuit']), nx)}
    k = cle_groupe(x)
    return m, ({k: medo[k]} if k in medo else {})


def controles(x, sol, nx, ech_nominale, med, medo):
    """Liste des raisons de douter de la solution (vide = cohérente).  Textes techniques (journal)."""
    pb = []
    refs = [ech_nominale] if ech_nominale else []
    refs += [m['echelle'] for k, m in med.items() if k[:3] == (x['tel'], str(x['nuit']), nx) and m['echelle']
             and m['n'] >= 5]
    if refs and min(abs(sol['echelle'] / r - 1) for r in refs) > TOL_ECHELLE:
        pb.append('echelle %.3f"/px au lieu de %s' % (sol['echelle'], '/'.join('%.3f' % r for r in refs)))
    m = med.get(cle_classe(x), {})
    if m.get('angle') is not None and ecart_angle(sol['angle'], m['angle']) > TOL_ANGLE:
        pb.append('angle %.1f deg au lieu de %.1f' % (sol['angle'], m['angle']))
    kk = cle_groupe(x)
    if kk in medo and medo[kk][2] > 1:
        dist = sep_deg(sol['ra'], sol['dec'], medo[kk][0], medo[kk][1])
        if dist > (DIST_FIXE if x['cat'] in FIXES else DIST_MOBILE):
            pb.append('centre a %.2f deg du groupe' % dist)
    return pb
