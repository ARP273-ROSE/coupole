"""Volumes légers de la nébuleuse d'Orion (M42) et d'IC 434 / Tête de Cheval pour « Orion en 3D » : nuages de particules
pré-calculés (même suite pseudo-aléatoire, mêmes formules et mêmes arrondis que src/calc/nebuleuses_orion.ts de Coupole
Web ; test croisé sur tests/nebuleuses_orion_reference.json), posés à leur position exacte et agrandis ×AGRANDI autour
de leur centre (avec leurs étoiles excitatrices) pour être visibles à l'échelle de la constellation.

Géométrie publiée (données « Orion 3D », structures_orion.json) :
 - M42 : modèle en « cloque » (blister) : θ¹ Ori C à 0,2 pc devant le front d'ionisation (Wen & O'Dell 1995 ; O'Dell et
   al. 2009), couche émissive de 0,13 pc (Wen & O'Dell 1995), front en bol z(r) = −0,2 (1 − (r/R)²) pc, R = 3,725 pc
   (66′ à 388 pc, SIMBAD), paroi du nuage moléculaire OMC-1 derrière le front, Voile 1 à 3 pc devant (O'Dell et al.
   2009, fig. 5), Barre d'Orion à sa position SIMBAD ; forme au-delà de ≈ 0,5 pc schématique.
 - IC 434 et la Tête de Cheval : σ Ori « à la même distance » (387,5 pc, Schaefer et al. 2016 ; Gerin et al. 2009),
   bord d'Orion B vu par la tranche, pilier de 0,68 × 0,45 pc (6′ × 4′, SIMBAD) et 0,1 pc d'épaisseur (Gerin et al.
   2009), NGC 2023 à sa position SIMBAD ; profondeur et étendue d'IC 434 non publiées : schématiques.
Repère local (pc) : x vers l'est, y vers le nord (dans le plan du ciel), z vers l'observateur."""
from __future__ import annotations

import math

from . import orion3d_geo as O

AGRANDI = 12
VERSION = 1
BARRE_RADEC = (83.84291666666667, -5.409166666666667)
NGC2023_RADEC = (85.4078844555898, -2.2645107495667616)


class Alea:
    """mulberry32 (entiers non signés sur 32 bits ; identique en TypeScript)."""

    def __init__(self, graine: int):
        self.e = graine & 0xFFFFFFFF

    def u(self) -> float:
        self.e = (self.e + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((self.e ^ (self.e >> 15)) * (self.e | 1)) & 0xFFFFFFFF
        t = (t ^ ((t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0


def _r4(x: float) -> float:
    # même arrondi que Math.round(x * 1e4) / 1e4 (demi vers +∞)
    return math.floor(x * 1e4 + 0.5) / 1e4


def base_locale(P):
    """Base locale (est, nord, vers l'observateur) au point P (ICRS)."""
    vers_obs = O.unitaire((-P[0], -P[1], -P[2]))
    los = O.unitaire(P)
    est = O.unitaire(O.cross((0.0, 0.0, 1.0), los))
    nord = O.cross(los, est)
    return est, nord, vers_obs


def decalage_ciel(ra0, dec0, ra, dec, d):
    """Décalage dans le plan du ciel (pc, est et nord) entre deux directions vues à la distance d."""
    return (ra - ra0) * math.cos(dec0 * O.DEG) * O.DEG * d, (dec - dec0) * O.DEG * d


def _placer(C, b, x, y, z, k=AGRANDI):
    return tuple(_r4(C[i] + k * (x * b[0][i] + y * b[1][i] + z * b[2][i])) for i in range(3))


def _etoile(i: str) -> dict:
    return next(e for e in O.DONNEES['etoiles'] if e['id'] == i)


def radec(P):
    n = O.norme(P)
    ra = math.atan2(P[1], P[0]) / O.DEG
    if ra < 0:
        ra += 360
    return ra, math.asin(P[2] / n) / O.DEG


def m42() -> dict:
    a = Alea(42)
    C = tuple(_etoile('tet01_ori_c')['xyz'])
    b = base_locale(C)
    R = O.DONNEES['primitives']['m42_bol']['rayon_pc']

    def prof(r):
        return -0.2 * (1 - (r / R) ** 2)

    L = []

    def ajouter(x, y, z, r, rvb, alpha, genre):
        L.append({'p': _placer(C, b, x, y, z), 'r': _r4(r * AGRANDI), 'rvb': rvb, 'alpha': _r4(alpha), 'genre': genre})

    # paroi du nuage moléculaire OMC-1, derrière le front
    for _ in range(150):
        r = 1.15 * R * math.sqrt(a.u())
        f = 2 * math.pi * a.u()
        z = prof(min(r, R)) - 0.25 - 0.35 * a.u()
        ajouter(r * math.cos(f), r * math.sin(f), z, 0.55 + 0.45 * a.u(), (86, 60, 46), 0.38, 'poussiere')
    # couche émissive (0,13 pc) devant le front en bol : [O III] au centre, Hα au bord
    for _ in range(320):
        r = R * a.u() ** 1.4
        f = 2 * math.pi * a.u()
        z = prof(r) + 0.13 * a.u()
        centre = r < 0.3 * R
        ajouter(r * math.cos(f), r * math.sin(f), z, 0.3 + 0.45 * a.u(), (120, 225, 215) if centre else (255, 84, 112),
                (0.3 if centre else 0.26) * (1 - 0.5 * (r / R)), 'gaz')
    # Barre d'Orion : front vu par la tranche, à sa position SIMBAD
    d = O.norme(C)
    cra, cdec = radec(C)
    bx, by = decalage_ciel(cra, cdec, BARRE_RADEC[0], BARRE_RADEC[1], d)
    for _ in range(18):
        ajouter(bx + 0.08 * (a.u() - 0.5), by + 0.08 * (a.u() - 0.5), prof(math.hypot(bx, by)) + 0.05, 0.12,
                (255, 150, 120), 0.35, 'gaz')
    # Voile d'Orion, 1 à 3 pc devant le Trapèze (gaz neutre, absorbant)
    for _ in range(90):
        r = R * math.sqrt(a.u())
        f = 2 * math.pi * a.u()
        ajouter(r * math.cos(f), r * math.sin(f), 1 + 2 * a.u(), 0.8 + 0.4 * a.u(), (170, 132, 96), 0.07, 'poussiere')
    # le Trapèze : θ¹ Ori A, B, D autour de C (même distance que C, décalages du ciel agrandis)
    etoiles = []
    for i in ('tet01_ori_a', 'tet01_ori_b', 'tet01_ori_d'):
        e = _etoile(i)
        x, y = decalage_ciel(cra, cdec, e['ra'], e['dec'], d)
        etoiles.append({'id': i, 'p': _placer(C, b, x, y, 0)})
    return {'id': 'm42', 'centre': C, 'particules': L, 'etoiles': etoiles,
            'reperes': [{'fiche': 'orion:m42', 'p': _placer(C, b, 0, 0, prof(0))}]}


def ic434() -> dict:
    a = Alea(434)
    C = tuple(O.DONNEES['primitives']['tete_de_cheval']['centre'])
    b = base_locale(C)
    d = O.norme(C)
    hra, hdec = radec(C)
    L = []

    def ajouter(x, y, z, r, rvb, alpha, genre):
        L.append({'p': _placer(C, b, x, y, z), 'r': _r4(r * AGRANDI), 'rvb': rvb, 'alpha': _r4(alpha), 'genre': genre})

    # bord d'Orion B (L1630), à l'est du front : poussière
    for _ in range(160):
        x = 2.6 * a.u() ** 1.6
        ajouter(x, 3.6 * (2 * a.u() - 1), 1.2 * (2 * a.u() - 1), 0.35 + 0.35 * a.u(), (62, 42, 36), 0.55, 'poussiere')
    # IC 434 : gaz ionisé par σ Ori, à l'ouest du front (plus dense contre le front)
    for _ in range(200):
        x = -1.3 * a.u() ** 2
        ajouter(x, 3.4 * (2 * a.u() - 1), 1.0 * (2 * a.u() - 1), 0.25 + 0.3 * a.u(), (240, 70, 96), 0.24, 'gaz')
    # le pilier de la Tête de Cheval : 0,68 × 0,45 pc, 0,1 pc d'épaisseur, avancé vers σ Ori
    for i in range(70):
        if i < 18:
            x = -0.3 * a.u()
            y = 0.18 * (a.u() - 0.5)
        else:
            f = 2 * math.pi * a.u()
            s = math.sqrt(a.u())
            x = -0.62 + 0.34 * s * math.cos(f)
            y = 0.1 + 0.225 * s * math.sin(f)
        ajouter(x, y, 0.1 * (a.u() - 0.5), 0.07 + 0.05 * a.u(), (22, 12, 12), 0.85, 'poussiere')
    # NGC 2023 : nébuleuse par réflexion (lumière bleutée diffusée), à sa position SIMBAD
    nx, ny = decalage_ciel(hra, hdec, NGC2023_RADEC[0], NGC2023_RADEC[1], d)
    for _ in range(30):
        ajouter(nx + 0.35 * (a.u() - 0.5), ny + 0.35 * (a.u() - 0.5), 0.2 * (a.u() - 0.5), 0.18 + 0.12 * a.u(),
                (170, 195, 255), 0.16, 'gaz')
    sig = _etoile('sig_ori')
    sx, sy = decalage_ciel(hra, hdec, sig['ra'], sig['dec'], d)
    return {'id': 'ic434', 'centre': C, 'particules': L, 'etoiles': [{'id': 'sig_ori', 'p': _placer(C, b, sx, sy, 0)}],
            'reperes': [{'fiche': 'orion:tete_de_cheval', 'p': _placer(C, b, -0.62, 0.1, 0)},
                        {'fiche': 'orion:ic434', 'p': _placer(C, b, -0.6, 2.2, 0)},
                        {'fiche': 'orion:ngc2023', 'p': _placer(C, b, nx, ny, 0)}]}


_CACHE = None


def nebuleuses() -> list:
    global _CACHE
    if _CACHE is None:
        _CACHE = [m42(), ic434()]
    return _CACHE
