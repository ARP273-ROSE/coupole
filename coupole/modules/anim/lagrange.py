"""Les points de Lagrange : problème restreint des trois corps, circulaire et plan (sans Qt, jumeau de
``src/calc/lagrange.ts`` de Coupole Web).

Deux corps de masses 1 − μ et μ tournent sur des cercles autour de leur centre de masse ; dans le repère qui tourne
avec eux (unités : distance a, période 2π), le grand est en (−μ, 0), le petit en (1 − μ, 0).  Un troisième corps,
de masse négligeable, y ressent le potentiel effectif −Ω, avec
    Ω(x, y) = (x² + y²)/2 + (1 − μ)/r₁ + μ/r₂,
et la force de Coriolis : ẍ − 2ẏ = ∂Ω/∂x, ÿ + 2ẋ = ∂Ω/∂y.  La constante de Jacobi C = 2Ω − v² est conservée ; là
où 2Ω < C, le corps ne peut pas aller (courbes de vitesse nulle).  Les cinq points de Lagrange sont les points
d'équilibre : L1, L2, L3 sur l'axe (instables), L4 et L5 au sommet des triangles équilatéraux (stables si
μ < μ_Routh = (1 − √(23/27))/2 = 0,038 52).  Rayon de Hill : r_H ≈ a (μ/3)^(1/3).

Orbites de halo autour de L1 et L2 (en trois dimensions) : développement analytique du troisième ordre de
D. L. Richardson (« Analytic construction of periodic orbits about the collinear points », Celestial Mechanics 22,
241, 1980).  Coordonnées centrées sur le point de Lagrange, en unités de γ (distance du point au petit corps),
X = x_L + γx, Y = γy, Z = γz ; amplitudes Ax (dans le plan) et Az (hors du plan) liées par l₁Ax² + l₂Az² + Δ = 0,
fréquence λν.  L'état initial de Richardson, intégré tel quel (problème restreint en 3D), suit l'orbite environ un tour
puis s'en écarte : ces orbites sont instables (les sondes corrigent leur trajectoire)."""
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


def omega3(mu: float, x: float, y: float, z: float) -> float:
    r1 = math.sqrt((x + mu) ** 2 + y * y + z * z)
    r2 = math.sqrt((x - 1.0 + mu) ** 2 + y * y + z * z)
    return 0.5 * (x * x + y * y) + (1.0 - mu) / r1 + mu / r2


def jacobi3(mu: float, x, y, z, vx, vy, vz) -> float:
    return 2.0 * omega3(mu, x, y, z) - vx * vx - vy * vy - vz * vz


def jacobi_etat(mu: float, s) -> float:
    return jacobi3(mu, *s) if len(s) == 6 else jacobi(mu, *s)


def derivees3(mu: float, s):
    x, y, z, vx, vy, vz = s
    dx1, dx2 = x + mu, x - 1.0 + mu
    r1 = math.sqrt(dx1 * dx1 + y * y + z * z)
    r2 = math.sqrt(dx2 * dx2 + y * y + z * z)
    k1, k2 = (1.0 - mu) / (r1 * r1 * r1), mu / (r2 * r2 * r2)
    return (vx, vy, vz, x - k1 * dx1 - k2 * dx2 + 2.0 * vy, y - k1 * y - k2 * y - 2.0 * vx, -k1 * z - k2 * z)


def pas_rk4_3(mu: float, s, h: float):
    k1 = derivees3(mu, s)
    k2 = derivees3(mu, tuple(s[i] + h / 2.0 * k1[i] for i in range(6)))
    k3 = derivees3(mu, tuple(s[i] + h / 2.0 * k2[i] for i in range(6)))
    k4 = derivees3(mu, tuple(s[i] + h * k3[i] for i in range(6)))
    return tuple(s[i] + h / 6.0 * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) for i in range(6))


H_MAX = 0.002
R_CONTACT = 1e-3                     # distance (en a) sous laquelle on arrête : collision avec un des deux corps


def contact(mu: float, s) -> bool:
    x, y = s[0], s[1]
    if len(s) == 6:
        z = s[2]
        return math.sqrt((x + mu) ** 2 + y * y + z * z) < R_CONTACT or \
            math.sqrt((x - 1.0 + mu) ** 2 + y * y + z * z) < R_CONTACT
    return math.hypot(x + mu, y) < R_CONTACT or math.hypot(x - 1.0 + mu, y) < R_CONTACT


def integrer(mu: float, s, duree: float):
    """Avance de `duree` par pas égaux d'au plus H_MAX ; s'arrête au contact d'un corps (rend aussi un drapeau).
    État plan (x, y, vx, vy) ou en trois dimensions (x, y, z, vx, vy, vz)."""
    n = max(1, math.ceil(duree / H_MAX))
    h = duree / n
    pas = pas_rk4_3 if len(s) == 6 else pas_rk4
    for _ in range(n):
        s = pas(mu, s, h)
        if contact(mu, s):
            return s, True
    return s, False


# cas types : clé → écart δ par défaut (orbites de halo : δ = Az en unités de a, signe = famille nord ou sud)
CAS = (('tetard', 0.005), ('fer_a_cheval', 0.01), ('l1', 0.01), ('l2', 0.01), ('l3', 0.01), ('halo_l1', 0.01),
       ('halo_l2', 0.01))


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
    """Conditions initiales (x, y, vx, vy) dans le repère tournant pour un cas type, δ réglant l'écart ; orbites de
    halo : état (x, y, z, vx, vy, vz) de Richardson au passage dans le plan x–z."""
    if cas in ('halo_l1', 'halo_l2'):
        return halo(mu, cas[-2:].upper(), delta).etat(0.0)
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


# ------------------------------------------------------------------ orbites de halo (Richardson 1980, 3ᵉ ordre)
AZ_MAX = 0.4                          # Az ≤ 0,4 γ : au-delà, le développement du 3ᵉ ordre n'est plus fiable
# périodes sidérales des systèmes (jours) : Terre (année sidérale), Lune (mois sidéral), Jupiter, Charon
PERIODES_J = {'soleil_terre': 365.256_363, 'terre_lune': 27.321_662, 'soleil_jupiter': 4332.589,
              'pluton_charon': 6.387_2}


class Halo:
    """Orbite de halo de Richardson autour de L1 ou L2 ; δ = Az en unités de a (signe : famille nord ou sud)."""

    def __init__(self, mu: float, point: str, delta: float):
        xl = points_lagrange(mu)[point][0]
        self.xl = xl
        g = (1.0 - mu - xl) if point == 'L1' else (xl - (1.0 - mu))
        self.gamma = g

        def c(n):
            if point == 'L1':
                return (mu + (-1) ** n * (1.0 - mu) * g ** (n + 1) / (1.0 - g) ** (n + 1)) / g ** 3
            return ((-1) ** n * mu + (-1) ** n * (1.0 - mu) * g ** (n + 1) / (1.0 + g) ** (n + 1)) / g ** 3
        c2, c3, c4 = c(2), c(3), c(4)
        lam = math.sqrt((-(c2 - 2.0) + math.sqrt((c2 - 2.0) ** 2 + 4.0 * (c2 - 1.0) * (1.0 + 2.0 * c2))) / 2.0)
        k = 2.0 * lam / (lam * lam + 1.0 - c2)
        D = lam * lam - c2
        d1 = 3.0 * lam * lam / k * (k * (6.0 * lam * lam - 1.0) - 2.0 * lam)
        d2 = 8.0 * lam * lam / k * (k * (11.0 * lam * lam - 1.0) - 2.0 * lam)
        a21 = 3.0 * c3 * (k * k - 2.0) / (4.0 * (1.0 + 2.0 * c2))
        a22 = 3.0 * c3 / (4.0 * (1.0 + 2.0 * c2))
        a23 = -3.0 * c3 * lam / (4.0 * k * d1) * (3.0 * k ** 3 * lam - 6.0 * k * (k - lam) + 4.0)
        a24 = -3.0 * c3 * lam / (4.0 * k * d1) * (2.0 + 3.0 * k * lam)
        b21 = -3.0 * c3 * lam / (2.0 * d1) * (3.0 * k * lam - 4.0)
        b22 = 3.0 * c3 * lam / d1
        d21 = -c3 / (2.0 * lam * lam)
        a31 = (-9.0 * lam / (4.0 * d2) * (4.0 * c3 * (k * a23 - b21) + k * c4 * (4.0 + k * k))
               + (9.0 * lam * lam + 1.0 - c2) / (2.0 * d2) * (3.0 * c3 * (2.0 * a23 - k * b21) + c4 * (2.0 + 3.0 * k * k)))
        a32 = -1.0 / d2 * (9.0 * lam / 4.0 * (4.0 * c3 * (k * a24 - b22) + k * c4)
                           + 1.5 * (9.0 * lam * lam + 1.0 - c2) * (c3 * (k * b22 + d21 - 2.0 * a24) - c4))
        b31 = 3.0 / (8.0 * d2) * (8.0 * lam * (3.0 * c3 * (k * b21 - 2.0 * a23) - c4 * (2.0 + 3.0 * k * k))
                                  + (9.0 * lam * lam + 1.0 + 2.0 * c2) * (4.0 * c3 * (k * a23 - b21)
                                                                          + k * c4 * (4.0 + k * k)))
        b32 = 1.0 / d2 * (9.0 * lam * (c3 * (k * b22 + d21 - 2.0 * a24) - c4)
                          + 3.0 / 8.0 * (9.0 * lam * lam + 1.0 + 2.0 * c2) * (4.0 * c3 * (k * a24 - b22) + k * c4))
        d31 = 3.0 / (64.0 * lam * lam) * (4.0 * c3 * a24 + c4)
        d32 = 3.0 / (64.0 * lam * lam) * (4.0 * c3 * (a23 - d21) + c4 * (4.0 + k * k))
        den = 2.0 * lam * (lam * (1.0 + k * k) - 2.0 * k)
        s1 = (1.5 * c3 * (2.0 * a21 * (k * k - 2.0) - a23 * (k * k + 2.0) - 2.0 * k * b21)
              - 3.0 / 8.0 * c4 * (3.0 * k ** 4 - 8.0 * k * k + 8.0)) / den
        s2 = (1.5 * c3 * (2.0 * a22 * (k * k - 2.0) + a24 * (k * k + 2.0) + 2.0 * k * b22 + 5.0 * d21)
              + 3.0 / 8.0 * c4 * (12.0 - k * k)) / den
        l1 = -1.5 * c3 * (2.0 * a21 + a23 + 5.0 * d21) - 3.0 / 8.0 * c4 * (12.0 - k * k) + 2.0 * lam * lam * s1
        l2 = 1.5 * c3 * (a24 - 2.0 * a22) + 9.0 / 8.0 * c4 + 2.0 * lam * lam * s2
        self.dn = 1.0 if delta >= 0.0 else -1.0
        Az = min(abs(delta) / g, AZ_MAX)
        Ax = math.sqrt(max(0.0, (-D - l2 * Az * Az) / l1))
        self.Ax, self.Az = Ax, Az
        self.nu = 1.0 + s1 * Ax * Ax + s2 * Az * Az
        self.lam = lam
        self.k = k
        self.c = (c2, c3, c4)
        self._k = (k, a21, a22, a23, a24, a31, a32, b21, b22, b31, b32, d21, d31, d32)

    def periode(self) -> float:
        """Période (unités de temps du repère tournant : 2π = un tour des deux astres)."""
        return 2.0 * math.pi / (self.lam * self.nu)

    def etat(self, t1: float):
        """État (x, y, z, vx, vy, vz) dans le repère tournant à la phase τ₁ = λντ."""
        k, a21, a22, a23, a24, a31, a32, b21, b22, b31, b32, d21, d31, d32 = self._k
        Ax, Az, dn, g = self.Ax, self.Az, self.dn, self.gamma
        c1, c2_, c3_ = math.cos(t1), math.cos(2.0 * t1), math.cos(3.0 * t1)
        s1_, s2_, s3_ = math.sin(t1), math.sin(2.0 * t1), math.sin(3.0 * t1)
        ax2, ax3 = a23 * Ax * Ax - a24 * Az * Az, a31 * Ax ** 3 - a32 * Ax * Az * Az
        by2, by3 = b21 * Ax * Ax - b22 * Az * Az, b31 * Ax ** 3 - b32 * Ax * Az * Az
        z3 = d32 * Az * Ax * Ax - d31 * Az ** 3
        x = a21 * Ax * Ax + a22 * Az * Az - Ax * c1 + ax2 * c2_ + ax3 * c3_
        y = k * Ax * s1_ + by2 * s2_ + by3 * s3_
        z = dn * (Az * c1 + d21 * Ax * Az * (c2_ - 3.0) + z3 * c3_)
        w = self.lam * self.nu
        vx = w * (Ax * s1_ - 2.0 * ax2 * s2_ - 3.0 * ax3 * s3_)
        vy = w * (k * Ax * c1 + 2.0 * by2 * c2_ + 3.0 * by3 * c3_)
        vz = w * dn * (-Az * s1_ - 2.0 * d21 * Ax * Az * s2_ - 3.0 * z3 * s3_)
        return (self.xl + g * x, g * y, g * z, g * vx, g * vy, g * vz)

    def courbe(self, n: int = 180) -> list:
        return [self.etat(2.0 * math.pi * j / n)[:3] for j in range(n + 1)]


def halo(mu: float, point: str, delta: float) -> Halo:
    return Halo(mu, point, delta)
