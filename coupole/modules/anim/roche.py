"""La limite de Roche (sans Qt, jumeau de ``src/calc/roche.ts`` de Coupole Web).

Un satellite tenu par sa seule gravité (sans cohésion) est disloqué par la marée de sa planète s'il s'en approche à
moins de d = K R (ρ_M/ρ_m)^(1/3), R rayon et ρ_M densité de la planète, ρ_m densité du satellite :
  - K = 2,44 pour un satellite fluide, que la marée allonge (É. Roche, 1849) ;
  - K = ∛3 = 1,44 pour une sphère rigide en rotation synchrone : au point le plus proche de la planète, marée et force
    centrifuge (3GM r/d³) égalent la gravité propre (Gm/r²).
Étirement de marée rapporté à la gravité propre : 3 (ρ_M/ρ_m)(R/d)³ (1 à la limite rigide).  Allongement d'équilibre
d'un satellite fluide homogène (petites déformations) : (a − b)/r = 15/4 (ρ_M/ρ_m)(R/d)³.

Unités de la simulation : R = 1, GM = 1 (période 2π d^(3/2)).  Le satellite est un amas de grains en rotation
synchrone ; sous la limite, chaque grain suit sa propre orbite de Kepler autour de la planète, et la rotation
différentielle (les grains intérieurs vont plus vite) les étale en anneau."""
from __future__ import annotations

import math

K_FLUIDE = 2.44
K_RIGIDE = 3.0 ** (1.0 / 3.0)

# systèmes : clé, ρ planète, ρ satellite (kg·m⁻³), rayon de la planète (km), distance de départ (R)
SYSTEMES = (('terre_lune', 5514.0, 3344.0, 6378.1, 10.0), ('mars_phobos', 3933.0, 1876.0, 3389.5, 2.76),
            ('saturne_glace', 687.0, 920.0, 60268.0, 3.08), ('jupiter_comete', 1326.0, 500.0, 71492.0, 4.0))
R_SATELLITE = 0.16               # rayon dessiné de l'amas (en R), sans effet sur la limite


def limite(rapport: float, modele: str) -> float:
    return (K_FLUIDE if modele == 'fluide' else K_RIGIDE) * rapport ** (1.0 / 3.0)


def etirement(rapport: float, d: float) -> float:
    return 3.0 * rapport / d ** 3


def allongement(rapport: float, d: float) -> float:
    return 15.0 / 4.0 * rapport / d ** 3


def periode(d: float) -> float:
    return 2.0 * math.pi * d ** 1.5


def grains(n_couronnes: int = 5) -> list:
    """Positions des grains dans un disque de rayon 1 (réseau hexagonal) ; x vers l'extérieur, y le long de l'orbite."""
    out = []
    pas = 1.0 / n_couronnes
    for j in range(-n_couronnes, n_couronnes + 1):
        y = j * pas * math.sqrt(3.0) / 2.0
        decal = 0.5 * pas if j % 2 else 0.0
        for i in range(-n_couronnes - 1, n_couronnes + 2):
            x = i * pas + decal
            if x * x + y * y <= 1.0 + 1e-9:
                out.append((x, y))
    return out


def position_intact(d: float, theta: float, g, etire: float) -> tuple[float, float]:
    """Position (repère de la planète) du grain g de l'amas intact, allongé de « etire » le long de l'axe."""
    x, y = g[0] * R_SATELLITE * (1.0 + etire), g[1] * R_SATELLITE / math.sqrt(1.0 + etire)
    c, s = math.cos(theta), math.sin(theta)
    return d * c + x * c - y * s, d * s + x * s + y * c


def elements(x: float, y: float, vx: float, vy: float) -> tuple:
    """Orbite képlérienne plane (GM = 1) : (a, e, ω, M₀, n) ; None si elle n'est pas fermée."""
    r = math.hypot(x, y)
    v2 = vx * vx + vy * vy
    en = v2 / 2.0 - 1.0 / r
    if en >= 0.0:
        return None
    a = -1.0 / (2.0 * en)
    rv = x * vx + y * vy
    ex = (v2 - 1.0 / r) * x - rv * vx
    ey = (v2 - 1.0 / r) * y - rv * vy
    e = math.hypot(ex, ey)
    w = math.atan2(ey, ex) if e > 1e-12 else 0.0
    h = x * vy - y * vx
    nu = math.atan2(y, x) - w
    E = 2.0 * math.atan2(math.sqrt(1.0 - e) * math.sin(nu / 2.0), math.sqrt(1.0 + e) * math.cos(nu / 2.0))
    m0 = E - e * math.sin(E)
    n = a ** -1.5
    return a, e, w, m0, n if h > 0.0 else -n


def position_kepler(el: tuple, t: float) -> tuple[float, float]:
    a, e, w, m0, n = el
    m = m0 + n * t
    E = m
    for _ in range(30):
        d = (E - e * math.sin(E) - m) / (1.0 - e * math.cos(E))
        E -= d
        if abs(d) < 1e-13:
            break
    xo, yo = a * (math.cos(E) - e), a * math.sqrt(1.0 - e * e) * math.sin(E)
    if n < 0.0:
        yo = -yo
    c, s = math.cos(w), math.sin(w)
    return c * xo - s * yo, s * xo + c * yo


def liberer(d: float, theta: float, gs, etire: float) -> list:
    """Éléments de chaque grain au moment de la dislocation : position de l'amas, vitesse de la rotation d'ensemble
    (vitesse angulaire de l'orbite circulaire du centre, d^(−3/2))."""
    om = d ** -1.5
    out = []
    for g in gs:
        x, y = position_intact(d, theta, g, etire)
        out.append(elements(x, y, -om * y, om * x))
    return out
