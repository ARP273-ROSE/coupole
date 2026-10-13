"""Éléments de scène partagés : sphère locale (horizon, points cardinaux, zénith), personnage, grilles."""
from __future__ import annotations

import math

import numpy as np

from ...core.i18n import tr
from . import astro, dessin


def points_cardinaux(pe: dessin.Peintre3D, r: float = 1.1, nord_sud_seulement: bool = False):
    """Étiquettes N, E, S, O sur l'horizon (repère local x = nord, y = ouest, z = zénith)."""
    pts = (('anim_pc_n', 0.0), ('anim_pc_e', 90.0), ('anim_pc_s', 180.0), ('anim_pc_o', 270.0))
    for cle, az in pts:
        if nord_sud_seulement and az in (90.0, 270.0):
            continue
        pe.etiquette(np.array(astro.vecteur_horizon(az, 0.0)) * r, tr(cle), 'horizon')


def personnage(pe: dessin.Peintre3D, taille: float = 0.13, cle: str = 'texte'):
    """Petit observateur debout au centre de la sphère locale."""
    pe.segment((0, 0, 0), (0, 0, taille * 0.62), cle, 2.0, repere_monde=True)
    pe.segment((0, 0, taille * 0.45), (0, taille * 0.2, taille * 0.3), cle, 1.6, repere_monde=True)
    pe.segment((0, 0, taille * 0.45), (0, -taille * 0.2, taille * 0.3), cle, 1.6, repere_monde=True)
    xs, ys, _, _ = pe.ecran((0, 0, taille * 0.78), repere_monde=True)
    dessin.disque(pe.p, xs[0], ys[0], max(2.5, pe.r * taille * 0.12), cle)


def sphere_locale(p, vue, cx, cy, r, dessiner_dessus_dessous, couleur_ciel=None, alpha_sol: float = 0.55,
                  cardinaux: bool = True, observateur: bool = True):
    """Sphère locale complète : ciel, éléments sous l'horizon, plan de l'horizon, éléments au-dessus,
    points cardinaux et observateur.  `dessiner_dessus_dessous(pe)` est appelée deux fois (passes)."""
    pe = dessin.Peintre3D(p, vue, cx, cy, r)
    pe.contour('grille', couleur_ciel or 'ciel', 0.30)
    dessin.scene_en_deux_passes(pe, dessiner_dessus_dessous, lambda: pe.plan('sol', alpha_sol))
    if cardinaux:
        points_cardinaux(pe)
    if observateur:
        personnage(pe)
    return pe


def cercle_declinaison(dec: float, n: int = 181) -> np.ndarray:
    """Parallèle de déclinaison δ dans le repère équatorial."""
    return dessin.cercle((0, 0, 1), 90.0 - dec, n)


def cercle_horaire(ra_deg: float, dec0: float = -90.0, dec1: float = 90.0, n: int = 91) -> np.ndarray:
    d = np.linspace(dec0, dec1, n)
    a = math.radians(ra_deg)
    dr = np.radians(d)
    return np.stack([np.cos(dr) * math.cos(a), np.cos(dr) * math.sin(a), np.sin(dr)], axis=1)


def arc_equateur(ra0_deg: float, ra1_deg: float, dec: float = 0.0, n: int = 60) -> np.ndarray:
    a = np.radians(np.linspace(ra0_deg, ra1_deg, n))
    d = math.radians(dec)
    return np.stack([math.cos(d) * np.cos(a), math.cos(d) * np.sin(a), np.full(n, math.sin(d))], axis=1)


def ecliptique(eps: float, n: int = 181) -> np.ndarray:
    """Écliptique dans le repère équatorial (pôle de l'écliptique en α = 18 h, δ = 90° − ε)."""
    return dessin.cercle((0.0, -math.sin(math.radians(eps)), math.cos(math.radians(eps))), 90.0, n,
                         origine=(1.0, 0.0, 0.0))


def eq_vers_local(tsl_deg: float, lat: float):
    """Transformateur (N, 3) équatorial → repère local, pour Peintre3D(transformer=…)."""
    m = np.array(astro.matrice_equatorial_vers_horizon(tsl_deg, lat))
    return lambda pts: np.asarray(pts, dtype=float).reshape(-1, 3) @ m.T


def local_de_eq(tsl_deg: float, lat: float, ra_deg: float, dec: float) -> np.ndarray:
    m = np.array(astro.matrice_equatorial_vers_horizon(tsl_deg, lat))
    return m @ np.array(astro.vecteur_equatorial(ra_deg, dec))


def az_alt_de_vecteur(v) -> tuple[float, float]:
    """Vecteur du repère local → (azimut depuis le nord vers l'est, hauteur)."""
    return (math.degrees(math.atan2(-v[1], v[0])) % 360.0, math.degrees(math.asin(max(-1.0, min(1.0, v[2])))))
