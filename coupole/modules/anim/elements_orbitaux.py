"""Éléments d'une orbite képlérienne autour de la Terre (sans Qt, jumeau de ``src/calc/elements_orbitaux.ts`` de
Coupole Web).

Six nombres fixent une orbite et la position sur elle : demi-grand axe a (taille), excentricité e (forme),
inclinaison i (angle du plan de l'orbite avec l'équateur), longitude du nœud ascendant Ω (comptée depuis le point
vernal ♈ dans le plan de l'équateur), argument du périgée ω (compté depuis le nœud ascendant dans le plan de
l'orbite) et anomalie moyenne M (où est le satellite, proportionnelle au temps).  Position : équation de Kepler
M = E − e sin E, anomalie vraie ν, rayon r = a(1 − e cos E), puis rotation Rz(Ω) Rx(i) Rz(ω) du plan de l'orbite
vers le repère équatorial (x vers ♈, z vers le pôle Nord).  Vitesse : vis-viva v² = μ(2/r − 1/a).  Trace au sol :
la Terre tourne en un jour sidéral (à t = 0, le méridien de Greenwich regarde le point vernal)."""
from __future__ import annotations

import math

from . import astro

MU_KM3_S2 = astro.GM_TERRE / 1e9          # 398 600,4418 km³ s⁻²
R_TERRE_KM = astro.R_TERRE_KM               # 6 378,137 km (rayon équatorial)
JOUR_SIDERAL_S = 86_164.0905                # rotation de la Terre par rapport aux étoiles
OMEGA_TERRE = 2.0 * math.pi / JOUR_SIDERAL_S

# Orbites types : clé → (a en km, e, i, Ω, ω en degrés)
ORBITES = {
    'iss': (6_795.0, 0.0005, 51.64, 45.0, 60.0),            # station spatiale, ≈ 417 km d'altitude
    'polaire': (7_178.0, 0.001, 98.6, 45.0, 90.0),          # héliosynchrone, ≈ 800 km
    'gps': (26_560.0, 0.01, 55.0, 45.0, 60.0),              # GPS : demi-jour sidéral, 6 plans à 55°
    'molniya': (26_562.0, 0.74, 63.4, 45.0, 270.0),         # apogée au-dessus de l'hémisphère Nord
    'geo': (42_164.0, 0.0, 0.0, 0.0, 0.0),                  # géostationnaire : un jour sidéral à l'équateur
}


def periode_s(a_km: float) -> float:
    """Période de révolution (s) : T = 2π √(a³ / μ)."""
    return 2.0 * math.pi * math.sqrt(a_km ** 3 / MU_KM3_S2)


def demi_grand_axe_de_periode(t_s: float) -> float:
    """Demi-grand axe (km) d'une orbite de période t_s (troisième loi de Kepler)."""
    return (MU_KM3_S2 * (t_s / (2.0 * math.pi)) ** 2) ** (1.0 / 3.0)


def vitesse(r_km: float, a_km: float) -> float:
    """Vitesse (km/s) à la distance r : vis-viva."""
    return math.sqrt(MU_KM3_S2 * (2.0 / r_km - 1.0 / a_km))


def rotation(i: float, om: float, w: float):
    """Matrice (3 lignes) du plan de l'orbite (x vers le périgée, y à 90° dans le sens du mouvement) vers le repère
    équatorial : Rz(Ω) Rx(i) Rz(ω).  Angles en degrés."""
    ci, si = math.cos(math.radians(i)), math.sin(math.radians(i))
    co, so = math.cos(math.radians(om)), math.sin(math.radians(om))
    cw, sw = math.cos(math.radians(w)), math.sin(math.radians(w))
    return ((co * cw - so * sw * ci, -co * sw - so * cw * ci, so * si),
            (so * cw + co * sw * ci, -so * sw + co * cw * ci, -co * si),
            (sw * si, cw * si, ci))


def appliquer(m, v):
    return tuple(m[k][0] * v[0] + m[k][1] * v[1] + m[k][2] * v[2] for k in range(3))


def etat(a: float, e: float, i: float, om: float, w: float, m_deg: float) -> dict:
    """Position (km, repère équatorial), vitesse (km/s), anomalies (degrés) et distance pour l'anomalie moyenne M."""
    m = math.radians(m_deg % 360.0)
    ee = astro.resoudre_kepler(m, e)
    nu = 2.0 * math.atan2(math.sqrt(1.0 + e) * math.sin(ee / 2.0), math.sqrt(1.0 - e) * math.cos(ee / 2.0))
    r = a * (1.0 - e * math.cos(ee))
    p = a * (1.0 - e * e)
    h = math.sqrt(MU_KM3_S2 * p)
    plan_pos = (r * math.cos(nu), r * math.sin(nu), 0.0)
    plan_vit = (-MU_KM3_S2 / h * math.sin(nu), MU_KM3_S2 / h * (e + math.cos(nu)), 0.0)
    rot = rotation(i, om, w)
    return {'E': math.degrees(ee) % 360.0, 'nu': math.degrees(nu) % 360.0, 'r': r, 'v': vitesse(r, a),
            'pos': appliquer(rot, plan_pos), 'vit': appliquer(rot, plan_vit)}


def point_orbite(a: float, e: float, rot, nu_deg: float):
    """Point de l'orbite (km, repère équatorial) d'anomalie vraie ν."""
    nu = math.radians(nu_deg)
    r = a * (1.0 - e * e) / (1.0 + e * math.cos(nu))
    return appliquer(rot, (r * math.cos(nu), r * math.sin(nu), 0.0))


def sous_satellite(pos, t_s: float) -> tuple[float, float]:
    """Latitude et longitude (degrés, −180…180) du point sous le satellite à l'instant t (s)."""
    x, y, z = pos
    lat = math.degrees(math.atan2(z, math.hypot(x, y)))
    lon = math.degrees(math.atan2(y, x) - OMEGA_TERRE * t_s)
    return lat, (lon + 180.0) % 360.0 - 180.0


def trace_au_sol(a: float, e: float, i: float, om: float, w: float, m0_deg: float, t0_s: float, t1_s: float,
                 n: int = 400) -> list:
    """Trace au sol entre t0 et t1 (s) ; l'anomalie moyenne vaut m0 à t = 0.  Liste de (lat, lon)."""
    nmoy = 360.0 / periode_s(a)
    out = []
    for k in range(n + 1):
        t = t0_s + (t1_s - t0_s) * k / n
        s = etat(a, e, i, om, w, m0_deg + nmoy * t)
        out.append(sous_satellite(s['pos'], t))
    return out


def genre_orbite(a: float, e: float, i: float) -> str:
    """Nature de l'orbite pour l'affichage : 'heurte' (le périgée est sous la surface), 'geostationnaire',
    'geosynchrone', 'polaire', 'retrograde' ou 'prograde'."""
    if a * (1.0 - e) < R_TERRE_KM:
        return 'heurte'
    synchrone = abs(periode_s(a) - JOUR_SIDERAL_S) < 0.005 * JOUR_SIDERAL_S
    if synchrone and e < 0.01 and i < 1.0:
        return 'geostationnaire'
    if synchrone:
        return 'geosynchrone'
    if abs(i - 90.0) <= 10.0:
        return 'polaire'
    return 'retrograde' if i > 90.0 else 'prograde'
