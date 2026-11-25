"""Les points de Lagrange : problème restreint des trois corps, circulaire et plan (sans Qt, jumeau de
``src/calc/lagrange.ts`` de Coupole Web).

Deux corps de masses 1 − μ et μ tournent sur des cercles autour de leur centre de masse ; dans le repère qui tourne
avec eux (unités : distance a, période 2π), le grand est en (−μ, 0), le petit en (1 − μ, 0).  Un troisième corps,
de masse négligeable, y ressent le potentiel effectif −Ω, avec
    Ω(x, y) = (x² + y²)/2 + (1 − μ)/r₁ + μ/r₂,
et la force de Coriolis : ẍ − 2ẏ = ∂Ω/∂x, ÿ + 2ẋ = ∂Ω/∂y.  La constante de Jacobi C = 2Ω − v² est conservée ; là
où 2Ω < C, le corps ne peut pas aller (courbes de vitesse nulle).  Les cinq points de Lagrange sont les points
d'équilibre : L1, L2, L3 sur l'axe (instables), L4 et L5 au sommet des triangles équilatéraux (stables si
μ < μ_Routh = (1 − √(23/27))/2 = 0,038 52).  Rayon de Hill : r_H ≈ a (μ/3)^(1/3)."""
from __future__ import annotations

import functools
import math

MU_ROUTH = (1.0 - math.sqrt(23.0 / 27.0)) / 2.0
UA = 149_597_870.7                       # km

# systèmes : clé → (μ, a en km)
SYSTEMES = (
    ('soleil_terre', 1.0 / (1.0 + 328_900.56), UA),               # Soleil et Terre + Lune
    ('terre_lune', 1.0 / (1.0 + 81.300_568), 384_400.0),
    ('soleil_jupiter', 1.0 / (1.0 + 1047.348_644), 5.2026 * UA),
    ('pluton_charon', 0.1218 / 1.1218, 19_596.0),
)


def omega(mu: float, x: float, y: float) -> float:
    r1 = math.sqrt((x + mu) ** 2 + y * y)
    r2 = math.sqrt((x - 1.0 + mu) ** 2 + y * y)
    return 0.5 * (x * x + y * y) + (1.0 - mu) / r1 + mu / r2


def gradient(mu: float, x: float, y: float) -> tuple[float, float]:
    dx1, dx2 = x + mu, x - 1.0 + mu
    r1 = math.sqrt(dx1 * dx1 + y * y)
    r2 = math.sqrt(dx2 * dx2 + y * y)
    k1, k2 = (1.0 - mu) / (r1 * r1 * r1), mu / (r2 * r2 * r2)
    return x - k1 * dx1 - k2 * dx2, y - k1 * y - k2 * y


def _bissection(f, a: float, b: float, n: int = 200) -> float:
    fa = f(a)
    for _ in range(n):
        m = 0.5 * (a + b)
        fm = f(m)
        if (fm > 0.0) == (fa > 0.0):
            a, fa = m, fm
        else:
            b = m
    return 0.5 * (a + b)


@functools.lru_cache(maxsize=16)
def points_lagrange(mu: float) -> dict:
    """Positions (x, y) des cinq points de Lagrange."""
    def f(x):
        return gradient(mu, x, 0.0)[0]
    eps = 1e-12
    x1 = _bissection(f, -mu + eps, 1.0 - mu - eps)           # entre les deux corps
    x2 = _bissection(f, 1.0 - mu + eps, 2.0)                  # au-delà du petit
    x3 = _bissection(f, -2.0, -mu - eps)                      # au-delà du grand
    h = math.sqrt(3.0) / 2.0
    return {'L1': (x1, 0.0), 'L2': (x2, 0.0), 'L3': (x3, 0.0), 'L4': (0.5 - mu, h), 'L5': (0.5 - mu, -h)}


def jacobi(mu: float, x: float, y: float, vx: float, vy: float) -> float:
    return 2.0 * omega(mu, x, y) - vx * vx - vy * vy


def rayon_hill(mu: float) -> float:
    return (mu / 3.0) ** (1.0 / 3.0)


def derivees(mu: float, s):
    x, y, vx, vy = s
    gx, gy = gradient(mu, x, y)
    return (vx, vy, gx + 2.0 * vy, gy - 2.0 * vx)


def pas_rk4(mu: float, s, h: float):
    k1 = derivees(mu, s)
    k2 = derivees(mu, tuple(s[i] + h / 2.0 * k1[i] for i in range(4)))
    k3 = derivees(mu, tuple(s[i] + h / 2.0 * k2[i] for i in range(4)))
    k4 = derivees(mu, tuple(s[i] + h * k3[i] for i in range(4)))
    return tuple(s[i] + h / 6.0 * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) for i in range(4))


H_MAX = 0.002
R_CONTACT = 1e-3                     # distance (en a) sous laquelle on arrête : collision avec un des deux corps


def contact(mu: float, s) -> bool:
    x, y = s[0], s[1]
    return math.hypot(x + mu, y) < R_CONTACT or math.hypot(x - 1.0 + mu, y) < R_CONTACT


def integrer(mu: float, s, duree: float):
    """Avance de `duree` par pas égaux d'au plus H_MAX ; s'arrête au contact d'un corps (rend aussi un drapeau)."""
    n = max(1, math.ceil(duree / H_MAX))
    h = duree / n
    for _ in range(n):
        s = pas_rk4(mu, s, h)
        if contact(mu, s):
            return s, True
    return s, False


# cas types : clé → écart δ par défaut
CAS = (('tetard', 0.005), ('fer_a_cheval', 0.01), ('l1', 0.01), ('l2', 0.01), ('l3', 0.01))


def regions(mu: float, c: float) -> str:
    """Où le corps peut aller, d'après sa constante de Jacobi comparée à celles des points de Lagrange."""
    L = points_lagrange(mu)
    cl = {k: jacobi(mu, x, y, 0.0, 0.0) for k, (x, y) in L.items()}
    if c > cl['L1']:
        return 'r_ferme'
    if c > max(cl['L2'], cl['L3']):
        return 'r_l1'
    if c > min(cl['L2'], cl['L3']):
        return 'r_l2'
    if c > cl['L4']:
        return 'r_l3'
    return 'r_partout'


def depart(mu: float, cas: str, delta: float):
    """Conditions initiales (x, y, vx, vy) dans le repère tournant pour un cas type, δ réglant l'écart."""
    L = points_lagrange(mu)
    if cas == 'tetard':                    # un peu à côté de L4, au repos dans le repère tournant
        x, y = L['L4']
        return (x + delta * 0.5, y + delta * math.sqrt(3.0) / 2.0, 0.0, 0.0)
    if cas == 'fer_a_cheval':              # en face du petit corps, sur une orbite circulaire un peu plus large
        r = 1.0 + delta
        return (-r, 0.0, 0.0, -(r ** -0.5 - r))
    if cas in ('l1', 'l2', 'l3'):          # au point d'équilibre, poussé de δ/100 vers l'extérieur
        x, y = L[cas.upper()]
        return (x + delta * 0.01, y, 0.0, 0.0)
    x, y = L['L4']
    return (x, y, 0.0, 0.0)
