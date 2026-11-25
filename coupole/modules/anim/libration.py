"""Rotation synchrone et libration de la Lune (sans Qt, jumeau de ``src/calc/libration.ts`` de Coupole Web).

La Lune tourne sur elle-même d'un mouvement uniforme, en un mois sidéral, mais parcourt son orbite elliptique à
vitesse variable (loi des aires) : vue de la Terre, elle oscille d'est en ouest, de l = ν − M (anomalie vraie moins
anomalie moyenne, ≈ 2e sin M : 6,3° pour e = 0,0549 ; la Lune réelle va jusqu'à 7,9° car le Soleil déforme son
orbite).  Son équateur est incliné de I = 6,68° sur le plan de l'orbite : on voit tour à tour au-delà de chaque pôle,
b = arcsin(sin I sin(ν + ϖ)), ϖ étant l'angle du nœud de l'équateur au périgée (il tourne en quelques années).
Un observateur à la surface de la Terre voit en plus jusqu'à ρ = arcsin(R⊕/d) ≈ 0,95° de côté (libration diurne).

Part de la surface vue au moins une fois : un point P de la Lune n'est jamais vu si P·S < −sin ρ pour toutes les
directions S de la Terre vues de la Lune.  Sur le grand cercle d'azimut ψ autour du point opposé à la Terre, la limite
de la zone jamais vue est à la distance angulaire α(ψ) = minₜ [atan2(Sₓ, D) − arcsin(sin ρ / √(Sₓ² + D²))],
D = S_y cos ψ + S_z sin ψ ; aire jamais vue = ∫ (1 − cos α) dψ."""
from __future__ import annotations

import math

E_LUNE = 0.0549
I_LUNE = 6.68                    # inclinaison de l'équateur lunaire sur le plan de l'orbite (°)
MOIS_SIDERAL_J = 27.321_661_55
A_LUNE_KM = 384_400.0
R_TERRE_KM = 6378.137
N_PSI = 120
N_T = 48
N_OMEGA = 6

# formations lunaires repères : clé, latitude (°), longitude (° est)
FORMATIONS = (('crisium', 17.0, 59.1), ('tycho', -43.3, -11.4), ('copernic', 9.6, -20.1),
              ('grimaldi', -5.2, -68.6), ('orientale', -19.4, -92.8))


def kepler(m: float, e: float) -> float:
    E = m if e < 0.8 else math.pi
    for _ in range(50):
        d = (E - e * math.sin(E) - m) / (1.0 - e * math.cos(E))
        E -= d
        if abs(d) < 1e-14:
            break
    return E


def anomalie_vraie(m: float, e: float) -> float:
    E = kepler(m, e)
    return 2.0 * math.atan2(math.sqrt(1.0 + e) * math.sin(E / 2.0), math.sqrt(1.0 - e) * math.cos(E / 2.0))


def distance(m: float, e: float, a: float = A_LUNE_KM) -> float:
    return a * (1.0 - e * math.cos(kepler(m, e)))


def libration(m: float, e: float, i_deg: float, varpi_deg: float, synchrone: bool = True) -> tuple[float, float]:
    """(l, b) en degrés : longitude et latitude du point sous la Terre, vu de la Lune, à l'anomalie moyenne m (rad).
    l > 0 : on voit davantage le bord est (mer des Crises)."""
    nu = anomalie_vraie(m, e)
    rot = m if synchrone else 0.0
    l = math.atan2(math.sin(nu - rot), math.cos(nu - rot))
    b = math.asin(math.sin(math.radians(i_deg)) * math.sin(nu + math.radians(varpi_deg)))
    return math.degrees(l), math.degrees(b)


def direction(l_deg: float, b_deg: float) -> tuple[float, float, float]:
    l, b = math.radians(l_deg), math.radians(b_deg)
    return math.cos(b) * math.cos(l), math.cos(b) * math.sin(l), math.sin(b)


def fraction_vue(directions: list, rho_deg: float = 0.0, n_psi: int = N_PSI) -> float:
    """Part de la sphère vue au moins une fois depuis les directions S (vecteurs unitaires, repère de la Lune, x vers le
    point moyen sous la Terre), avec une marge de vue ρ."""
    s = math.sin(math.radians(rho_deg))
    jamais = 0.0
    for k in range(n_psi):
        psi = 2.0 * math.pi * (k + 0.5) / n_psi
        c, sn = math.cos(psi), math.sin(psi)
        amin = math.pi
        for sx, sy, sz in directions:
            d = sy * c + sz * sn
            r = math.sqrt(sx * sx + d * d)
            a = math.atan2(sx, d) - (math.asin(min(1.0, s / r)) if r > 0.0 else 0.0)
            if a < amin:
                amin = a
        if amin > 0.0:
            jamais += 1.0 - math.cos(amin)
    return 1.0 - jamais * (2.0 * math.pi / n_psi) / (4.0 * math.pi)


def directions_cycle(e: float, i_deg: float, varpi_deg: float, synchrone: bool = True, n: int = N_T) -> list:
    out = []
    for j in range(n):
        out.append(direction(*libration(2.0 * math.pi * j / n, e, i_deg, varpi_deg, synchrone)))
    return out


def fraction_mois(e: float, i_deg: float, varpi_deg: float, synchrone: bool = True, rho_deg: float = 0.0) -> float:
    return fraction_vue(directions_cycle(e, i_deg, varpi_deg, synchrone), rho_deg)


def fraction_annees(e: float, i_deg: float, synchrone: bool = True, rho_deg: float = 0.0) -> float:
    """Sur de nombreuses années : ϖ prend toutes les valeurs (N_OMEGA valeurs régulières)."""
    d = []
    for k in range(N_OMEGA):
        d += directions_cycle(e, i_deg, 360.0 * k / N_OMEGA, synchrone)
    return fraction_vue(d, rho_deg)


def rho_diurne(e: float, m: float = 0.0) -> float:
    """Demi-angle sous lequel la Lune voit la Terre (°) : arcsin(R⊕ / d), à la distance moyenne si m n'est pas donné."""
    return math.degrees(math.asin(R_TERRE_KM / A_LUNE_KM))


def projection(lat_deg: float, lon_deg: float, l_deg: float, b_deg: float) -> tuple[float, float, float]:
    """Projection orthographique d'un point de la Lune vu de la Terre (point sous la Terre (l, b)) : x vers l'est
    lunaire (à droite, nord en haut), y vers le nord, z > 0 si le point est tourné vers nous."""
    la, lo, b = math.radians(lat_deg), math.radians(lon_deg - l_deg), math.radians(b_deg)
    x = math.cos(la) * math.sin(lo)
    y = math.cos(b) * math.sin(la) - math.sin(b) * math.cos(la) * math.cos(lo)
    z = math.sin(b) * math.sin(la) + math.cos(b) * math.cos(la) * math.cos(lo)
    return x, y, z
