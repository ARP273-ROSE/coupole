"""Deux corps en orbite autour de leur centre de masse : exoplanètes et étoiles doubles (sans Qt).

Lois de Kepler et de Newton exactes : période P = 2π √(a³ / G(M₁ + M₂)), positions par l'équation de Kepler,
vitesse radiale de l'étoile v_r = K [cos(ν + ω) + e cos ω] avec K = (2πG / P)^⅓ M₂ sin i / (M₁ + M₂)^⅔ / √(1 − e²),
transits et éclipses par l'aire exacte de recouvrement de deux disques uniformes.

Repère : X, Y dans le plan du ciel, Z vers l'observateur ; le compagnon est devant l'étoile principale quand
ν + ω = 90° (transit).  Constantes nominales de l'UAI (résolution 2015 B3) : R☉, R♃ (équatorial), GM♃."""
from __future__ import annotations

import math

from . import astro

G = astro.G_SI
GM_SOLEIL = astro.GM_SOLEIL
GM_JUPITER = 1.266_865_3e17          # m³ s⁻² (UAI 2015 B3, nominal)
M_SOLEIL_KG = GM_SOLEIL / G
M_JUPITER_KG = GM_JUPITER / G
R_SOLEIL_M = 6.957e8                 # UAI 2015 B3
R_JUPITER_M = 7.1492e7               # UAI 2015 B3 (équatorial)
UA_M = astro.UA_KM * 1000.0
JOUR_S = 86_400.0


def periode_s(a_m: float, m1_kg: float, m2_kg: float) -> float:
    """3e loi de Kepler (forme de Newton) : P = 2π √(a³ / G(M₁ + M₂))."""
    return 2 * math.pi * math.sqrt(a_m ** 3 / (G * (m1_kg + m2_kg)))


def demi_grand_axe_m(p_s: float, m1_kg: float, m2_kg: float) -> float:
    return (G * (m1_kg + m2_kg) * (p_s / (2 * math.pi)) ** 2) ** (1 / 3)


def amplitude_k(m1_kg: float, m2_kg: float, a_m: float, e: float, i_deg: float) -> float:
    """Demi-amplitude de la vitesse radiale de l'étoile (m/s)."""
    p = periode_s(a_m, m1_kg, m2_kg)
    return ((2 * math.pi * G / p) ** (1 / 3) * m2_kg * math.sin(math.radians(i_deg))
            / (m1_kg + m2_kg) ** (2 / 3) / math.sqrt(1 - e * e))


def anomalie_vraie(phase: float, e: float) -> float:
    """Anomalie vraie (radians) à la fraction `phase` de période après le périastre."""
    ee = astro.resoudre_kepler(2 * math.pi * (phase % 1.0), e)
    return 2 * math.atan2(math.sqrt(1 + e) * math.sin(ee / 2), math.sqrt(1 - e) * math.cos(ee / 2))


def relative(phase: float, a: float, e: float, i_deg: float, omega_deg: float) -> tuple[float, float, float]:
    """Position (X, Y, Z) du compagnon par rapport à l'étoile principale (mêmes unités que a)."""
    nu = anomalie_vraie(phase, e)
    r = a * (1 - e * e) / (1 + e * math.cos(nu))
    u = nu + math.radians(omega_deg)
    i = math.radians(i_deg)
    return r * math.cos(u), r * math.sin(u) * math.cos(i), r * math.sin(u) * math.sin(i)


def vitesse_radiale(phase: float, k: float, e: float, omega_deg: float) -> float:
    """Vitesse radiale de l'étoile principale (> 0 : elle s'éloigne)."""
    nu = anomalie_vraie(phase, e)
    w = math.radians(omega_deg)
    return k * (math.cos(nu + w) + e * math.cos(w))


def phase_conjonction(e: float, omega_deg: float) -> float:
    """Phase (depuis le périastre) où le compagnon passe devant : ν = 90° − ω."""
    nu = math.radians(90.0 - omega_deg)
    ee = 2 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2), math.sqrt(1 + e) * math.cos(nu / 2))
    return ((ee - e * math.sin(ee)) / (2 * math.pi)) % 1.0


def aire_recouvrement(r1: float, r2: float, d: float) -> float:
    """Aire commune à deux disques de rayons r1, r2 dont les centres sont à la distance d (lentille exacte)."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return math.pi * min(r1, r2) ** 2
    a1 = math.acos(max(-1.0, min(1.0, (d * d + r1 * r1 - r2 * r2) / (2 * d * r1))))
    a2 = math.acos(max(-1.0, min(1.0, (d * d + r2 * r2 - r1 * r1) / (2 * d * r2))))
    return (r1 * r1 * (a1 - math.sin(2 * a1) / 2) + r2 * r2 * (a2 - math.sin(2 * a2) / 2))


def flux_deux_disques(phase: float, r1: float, r2: float, s1: float, s2: float, e: float, i_deg: float,
                      omega_deg: float) -> float:
    """Flux total de deux disques uniformes (rayons en unités du demi-grand axe, brillances de surface s1, s2) :
    π r₁² s₁ + π r₂² s₂ moins la partie cachée du disque de derrière."""
    x, y, z = relative(phase, 1.0, e, i_deg, omega_deg)
    d = math.hypot(x, y)
    cache = aire_recouvrement(r1, r2, d)
    total = math.pi * (r1 * r1 * s1 + r2 * r2 * s2)
    return total - cache * (s1 if z > 0 else s2)        # z > 0 : le compagnon (2) est devant, il cache 1


def duree_transit(phase0: float, r1: float, r2: float, e: float, i_deg: float, omega_deg: float,
                  n: int = 4000) -> float:
    """Fraction de période pendant laquelle le compagnon (devant) recouvre l'étoile principale (0 sans transit)."""
    pas = 1.0 / n
    dedans = 0
    for k in range(-n // 4, n // 4):
        ph = phase0 + k * pas
        x, y, z = relative(ph, 1.0, e, i_deg, omega_deg)
        if z > 0 and math.hypot(x, y) < r1 + r2:
            dedans += 1
    return dedans * pas


# ---------------------------------------------------------------- étoile de la séquence principale (original)
def luminosite_de_masse(m: float) -> float:
    """L / L☉ d'une étoile de la séquence principale (relation masse-luminosité de l'original)."""
    return 0.232_220_431_737_728 * m ** 2.26 if m < 0.43 else m ** 3.99


_POLY_T = ((-1.61, (3.76424847491303, 0.140316436337353, 0.0139709648834783, 0.00146257952166353,
                    0.000114203991057792, 0.00000534009520193973, 1.00897501873505e-7)),
           (0.22, (3.76404749064937, 0.139720836051662, 0.0131949471107482, 0.000878016217920958,
                   -0.00016087678534046, -0.0000718923778642037, -0.0000098430921759891)),
           (1.48, (3.76404935999916, 0.139700505514371, 0.0132834512392025, 0.000681148684168764,
                   0.0000515647954029831, -0.000230931527900807, 0.0000134429776870977)),
           (2.61, (3.76208682178285, 0.14541668375348, 0.00684584757963743, 0.00396076543835346,
                   -0.000464655201610208, -0.000381007438333072, 0.0000623586254118745)),
           (3.62, (3.7785507438146, 0.129897095940252, 0.00142810707728862, 0.0167045399494531,
                   -0.00693250229182094, 0.00103845665508301, -0.000055992055857869)),
           (5.43, (3.94943146036608, -0.154281251321452, 0.1979230342627, -0.055596100619304,
                   0.00799539610207913, -0.000600846748510063, 0.0000187770530697032)),
           (math.inf, (4.36797099518548, -0.314871178456464, 0.143399968097621, -0.0130740129137381,
                       -0.00159255369850374, 0.000357973227398207, -0.000017804556980593)))


def temperature_de_luminosite(l: float) -> float:
    """Température effective de la séquence principale selon log L (polynômes de l'original)."""
    x = math.log10(l)
    for borne, c in _POLY_T:
        if x < borne:
            v = 0.0
            for coef in reversed(c):
                v = v * x + coef
            return 10 ** v
    raise ValueError(l)


def etoile_sequence_principale(m: float) -> dict:
    """Luminosité, température, rayon (R☉ par Stefan-Boltzmann avec T☉ = 5 772 K) d'une étoile de masse m (M☉)."""
    from . import hr
    lum = luminosite_de_masse(m)
    t = temperature_de_luminosite(lum)
    return {'L': lum, 'T': t, 'R': hr.rayon_solaire(lum, t)}


# ---------------------------------------------------------------- planètes du Système solaire (Standish, JPL)
def heliocentrique(nom: str, siecles: float) -> tuple[float, float, float]:
    """Position héliocentrique (ua, écliptique et équinoxe J2000) d'une planète par les éléments moyens de
    Standish (table 1, 1800–2050) : siecles = siècles juliens depuis J2000 (TDB)."""
    from .donnees_lot3 import ELEMENTS_STANDISH
    e0, de = ELEMENTS_STANDISH[nom]
    a, e, i, l, varpi, om = (x + d * siecles for x, d in zip(e0, de))
    w = varpi - om
    m = math.radians(((l - varpi + 180.0) % 360.0) - 180.0)
    ee = astro.resoudre_kepler(m, e)
    xp, yp = a * (math.cos(ee) - e), a * math.sqrt(1 - e * e) * math.sin(ee)
    cw, sw = math.cos(math.radians(w)), math.sin(math.radians(w))
    co, so = math.cos(math.radians(om)), math.sin(math.radians(om))
    ci, si = math.cos(math.radians(i)), math.sin(math.radians(i))
    return ((cw * co - sw * so * ci) * xp + (-sw * co - cw * so * ci) * yp,
            (cw * so + sw * co * ci) * xp + (-sw * so + cw * co * ci) * yp,
            (sw * si) * xp + (cw * si) * yp)


def soleil_barycentrique(siecles: float, planetes) -> tuple[float, float, float]:
    """Position du centre du Soleil par rapport au centre de masse du Soleil et des planètes choisies (ua) :
    −Σ mᵢ rᵢ / (M☉ + Σ mᵢ), rᵢ héliocentriques ; masses = GM de l'éphéméride DE440."""
    from .donnees_lot3 import GM_DE440_KM3_S2 as GM
    tot = GM['soleil']
    sx = sy = sz = 0.0
    for nom in planetes:
        x, y, z = heliocentrique(nom, siecles)
        g = GM[nom]
        sx, sy, sz, tot = sx + g * x, sy + g * y, sz + g * z, tot + g
    return -sx / tot, -sy / tot, -sz / tot
