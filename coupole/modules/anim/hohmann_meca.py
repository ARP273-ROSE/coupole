"""Transfert de Hohmann entre deux orbites circulaires coplanaires (sans Qt, jumeau de ``src/calc/hohmann.ts`` de
Coupole Web).

Deux poussées : au départ (rayon r₁), on passe de la vitesse circulaire v₁ = √(μ/r₁) à la vitesse du périgée de
l'ellipse de transfert (demi-grand axe a = (r₁ + r₂)/2), v_p = √(μ (2/r₁ − 1/a)) ; une demi-ellipse plus tard
(t = π √(a³/μ)), à r₂, on passe de v_a = √(μ (2/r₂ − 1/a)) à v₂ = √(μ/r₂).  Pour retrouver une cible sur l'orbite
d'arrivée, il faut partir quand elle a une avance angulaire φ = π − n₂ t (fenêtre de tir), ce qui revient tous les
2π / |n₁ − n₂| (période synodique).  Vers une orbite plus basse, les deux poussées freinent."""
from __future__ import annotations

import math

from . import astro

MU_TERRE = astro.GM_TERRE / 1e9                  # km³ s⁻²
MU_SOLEIL = astro.GM_SOLEIL / 1e9
R_T = astro.R_TERRE_KM
UA = astro.UA_KM

# scénarios : clé → (μ, r₁ km, r₂ km, nom du départ, nom de l'arrivée, cible : None ou clé de texte, avance de la
# cible au départ de l'animation en degrés)
SCENARIOS = {
    'leo_geo': (MU_TERRE, R_T + 200.0, 42_164.0, 'leo', 'geo', 'geo_sat', 150.0),
    'leo_iss': (MU_TERRE, R_T + 200.0, R_T + 417.0, 'leo', 'iss', 'iss', 40.0),
    'terre_lune': (MU_TERRE, R_T + 200.0, astro.D_LUNE_KM, 'leo', 'lune', 'lune', 160.0),
    'terre_mars': (MU_SOLEIL, UA, 1.523_679 * UA, 'terre', 'mars', 'mars', 150.0),
    'terre_venus': (MU_SOLEIL, UA, 0.723_332 * UA, 'terre', 'venus', 'venus', 150.0),
    'terre_jupiter': (MU_SOLEIL, UA, 5.202_6 * UA, 'terre', 'jupiter', 'jupiter', 40.0),
}


def mod2pi(x: float) -> float:
    return x - 2.0 * math.pi * math.floor(x / (2.0 * math.pi))


def bilan(mu: float, r1: float, r2: float) -> dict:
    """Vitesses (km/s), poussées, durée (s), angle de phase au départ (degrés) et période synodique (s)."""
    a = 0.5 * (r1 + r2)
    v1, v2 = math.sqrt(mu / r1), math.sqrt(mu / r2)
    vd = math.sqrt(mu * (2.0 / r1 - 1.0 / a))           # vitesse sur l'ellipse au départ (périgée ou apogée)
    va = math.sqrt(mu * (2.0 / r2 - 1.0 / a))           # à l'arrivée
    t = math.pi * math.sqrt(a ** 3 / mu)
    n1, n2 = math.sqrt(mu / r1 ** 3), math.sqrt(mu / r2 ** 3)
    phase = math.degrees(math.pi - n2 * t)
    phase = (phase + 180.0) % 360.0 - 180.0
    return {'mu': mu, 'a': a, 'e': abs(r2 - r1) / (r2 + r1), 'v1': v1, 'v2': v2, 'vd': vd, 'va': va,
            'dv1': vd - v1, 'dv2': v2 - va, 'dv': abs(vd - v1) + abs(v2 - va), 't': t, 'n1': n1, 'n2': n2,
            'phase': phase, 'synodique': 2.0 * math.pi / abs(n1 - n2)}


def attente_fenetre(b: dict, avance_deg: float) -> float:
    """Temps (s) jusqu'à la prochaine fenêtre, la cible ayant `avance_deg` d'avance sur le départ maintenant."""
    d0, phi = math.radians(avance_deg), math.radians(b['phase'])
    if b['n2'] > b['n1']:
        return mod2pi(phi - d0) / (b['n2'] - b['n1'])
    return mod2pi(d0 - phi) / (b['n1'] - b['n2'])


def position_transfert(b: dict, r1: float, r2: float, theta_depart: float, dt: float) -> tuple[float, float]:
    """Rayon (km) et angle (radians) du vaisseau sur l'ellipse de transfert, dt secondes après le départ."""
    a, e = b['a'], b['e']
    n = math.sqrt(b['mu'] / a ** 3)                     # mouvement moyen sur l'ellipse
    vers_le_haut = r2 >= r1
    m = n * dt + (0.0 if vers_le_haut else math.pi)
    ee = astro.resoudre_kepler(m, e)
    nu = 2.0 * math.atan2(math.sqrt(1.0 + e) * math.sin(ee / 2.0), math.sqrt(1.0 - e) * math.cos(ee / 2.0))
    r = a * (1.0 - e * math.cos(ee))
    perigee = theta_depart if vers_le_haut else theta_depart + math.pi
    return r, perigee + nu


def ecart_rendez_vous(b: dict, avance_au_depart_deg: float) -> float:
    """Avance de la cible sur le vaisseau à l'arrivée (degrés, −180…180) quand on part avec cette avance."""
    x = avance_au_depart_deg + math.degrees(b['n2'] * b['t']) - 180.0
    return (x + 180.0) % 360.0 - 180.0
