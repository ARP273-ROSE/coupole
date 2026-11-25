"""Occultation d'une étoile par un astéroïde (sans Qt, jumeau de ``src/calc/occultation.ts`` de Coupole Web).

L'étoile est si loin que l'ombre de l'astéroïde sur la Terre a la taille de l'astéroïde : une ellipse (demi-axes a, b,
grand axe tourné de ψ) qui balaie le plan perpendiculaire à la direction de l'étoile à la vitesse v.  Un observateur
placé à la distance y de la trajectoire du centre voit l'étoile disparaître le temps que la corde de l'ellipse à
cette hauteur défile devant lui : durée = corde / v.  Avec plusieurs observateurs (des cordes parallèles), on retrouve
la taille et la forme ; une ellipse ajustée par moindres carrés sur les extrémités des cordes (au moins trois cordes)
la reconstitue, aux erreurs de chronométrage près.

Vitesse de l'ombre à l'opposition (orbites circulaires) : v = V_T − V_a = √(GM☉/1 ua) (1 − 1/√r), r en ua ;
distance à la Terre Δ = r − 1 ua.  Échelle de Fresnel √(λ Δ / 2) (la diffraction arrondit les bords) ; diamètre de
l'étoile projeté à la distance de l'astéroïde θ Δ (une étoile géante est occultée progressivement, voire en
partie seulement)."""
from __future__ import annotations

import math

from . import astro

V_TERRE = math.sqrt(astro.GM_SOLEIL / (astro.UA_KM * 1000.0)) / 1000.0     # 29,78 km/s
KM_PAR_MAS_UA = astro.UA_KM / (648_000_000.0 / math.pi)                    # 1 mas vu à 1 ua, en km
N_ETOILE = 15                       # points par côté de la grille qui échantillonne le disque de l'étoile

# objets : clé → (diamètre 2a en km, b/a, orientation ψ en degrés, distance au Soleil r en ua)
OBJETS = (
    ('ceinture', 100.0, 0.8, 30.0, 2.5),       # astéroïde de la ceinture principale
    ('troyen', 21.0, 0.75, 60.0, 5.2),          # petit troyen de Jupiter (taille de Polymele)
    ('eris', 2326.0, 1.0, 0.0, 96.0),           # Éris (occultation du 6 novembre 2010 : 2 326 km)
)


def vitesse_ombre(r_ua: float) -> float:
    """Vitesse de l'ombre sur la Terre à l'opposition (km/s), orbites circulaires coplanaires."""
    return V_TERRE * (1.0 - 1.0 / math.sqrt(r_ua))


def distance_terre(r_ua: float) -> float:
    """Distance Terre-astéroïde à l'opposition (ua)."""
    return r_ua - 1.0


def fresnel_km(lam_nm: float, delta_ua: float) -> float:
    """Échelle de Fresnel √(λ Δ / 2), en km."""
    return math.sqrt(lam_nm * 1e-12 * delta_ua * astro.UA_KM / 2.0)


def etoile_km(theta_mas: float, delta_ua: float) -> float:
    """Diamètre apparent de l'étoile projeté à la distance de l'astéroïde (km)."""
    return theta_mas * delta_ua * KM_PAR_MAS_UA


class Ellipse:
    """Ellipse de demi-axes a ≥ b, grand axe tourné de ψ (degrés) depuis la direction du mouvement (x)."""

    def __init__(self, a: float, b: float, psi_deg: float, x0: float = 0.0, y0: float = 0.0):
        self.a, self.b, self.psi, self.x0, self.y0 = a, b, psi_deg, x0, y0
        c, s = math.cos(math.radians(psi_deg)), math.sin(math.radians(psi_deg))
        ia, ib = 1.0 / (a * a), 1.0 / (b * b)
        self.m11 = c * c * ia + s * s * ib
        self.m12 = c * s * (ia - ib)
        self.m22 = s * s * ia + c * c * ib

    def dedans(self, x: float, y: float) -> bool:
        dx, dy = x - self.x0, y - self.y0
        return self.m11 * dx * dx + 2.0 * self.m12 * dx * dy + self.m22 * dy * dy <= 1.0

    def corde(self, y: float):
        """Corde à la hauteur y : (abscisse d'entrée, de sortie), ou None si la droite manque l'ellipse."""
        dy = y - self.y0
        disc = self.m11 - dy * dy / (self.a * self.a * self.b * self.b)
        if disc <= 0.0:
            return None
        xc = self.x0 - self.m12 * dy / self.m11
        demi = math.sqrt(disc) / self.m11
        return xc - demi, xc + demi

    def contour(self, n: int = 120) -> list:
        c, s = math.cos(math.radians(self.psi)), math.sin(math.radians(self.psi))
        out = []
        for k in range(n + 1):
            t = 2.0 * math.pi * k / n
            u, v = self.a * math.cos(t), self.b * math.sin(t)
            out.append((self.x0 + c * u - s * v, self.y0 + s * u + c * v))
        return out


def grille_etoile(n: int = N_ETOILE) -> list:
    """Points (en rayons de l'étoile) d'une grille régulière qui remplit le disque unité."""
    pts = []
    for i in range(n):
        for j in range(n):
            x, y = -1.0 + (2 * i + 1) / n, -1.0 + (2 * j + 1) / n
            if x * x + y * y <= 1.0:
                pts.append((x, y))
    return pts


GRILLE = grille_etoile()


def fraction_cachee(el: Ellipse, x: float, y: float, r_etoile: float) -> float:
    """Part du disque de l'étoile (rayon projeté r_etoile, en km) cachée par l'ellipse, l'observateur étant en (x, y)
    par rapport au plan de l'ombre."""
    if r_etoile <= 1e-9:
        return 1.0 if el.dedans(x, y) else 0.0
    n = sum(1 for u, v in GRILLE if el.dedans(x + u * r_etoile, y + v * r_etoile))
    return n / len(GRILLE)


def stations(n: int, espacement: float) -> list:
    """Distances (km) des n observateurs à la trajectoire prévue du centre de l'ombre, réparties symétriquement."""
    return [(k - (n - 1) / 2.0) * espacement for k in range(n)]


def cordes(el: Ellipse, ys: list) -> list:
    """Pour chaque observateur : (y, entrée, sortie) ou (y, None, None) s'il ne voit rien."""
    out = []
    for y in ys:
        c = el.corde(y)
        out.append((y, c[0], c[1]) if c else (y, None, None))
    return out


def bruiter(cs: list, sigma_km: float, graine: int = 2024) -> list:
    """Extrémités des cordes déplacées d'une erreur de chronométrage uniforme d'écart type sigma_km (Park et Miller,
    même suite qu'au web)."""
    m, x = 2_147_483_647, graine
    out = []
    for y, x1, x2 in cs:
        if x1 is None:
            out.append((y, None, None))
            continue
        e = []
        for _ in range(2):
            x = (16807 * x) % m
            e.append((2.0 * x / m - 1.0) * math.sqrt(3.0) * sigma_km)
        out.append((y, x1 + e[0], x2 + e[1]))
    return out


def ajuster_ellipse(points: list):
    """Ellipse ajustée par moindres carrés (conique A x² + B xy + C y² + D x + E y = 1) : (x0, y0, a, b, ψ en degrés)
    ou None (moins de 5 points, ou conique qui n'est pas une ellipse)."""
    if len(points) < 5:
        return None
    lignes = [(x * x, x * y, y * y, x, y) for x, y in points]
    n = 5
    mat = [[sum(l[i] * l[j] for l in lignes) for j in range(n)] + [sum(l[i] for l in lignes)] for i in range(n)]
    for col in range(n):                                     # élimination de Gauss à pivot partiel
        piv = max(range(col, n), key=lambda r: abs(mat[r][col]))
        if abs(mat[piv][col]) < 1e-300:
            return None
        mat[col], mat[piv] = mat[piv], mat[col]
        for r in range(n):
            if r != col:
                f = mat[r][col] / mat[col][col]
                mat[r] = [mat[r][k] - f * mat[col][k] for k in range(n + 1)]
    A, B, C, D, E = (mat[i][n] / mat[i][i] for i in range(n))
    det = 4.0 * A * C - B * B
    if det <= 0.0:
        return None
    x0 = (B * E - 2.0 * C * D) / det
    y0 = (B * D - 2.0 * A * E) / det
    # au centre, le gradient s'annule : A x0² + B x0 y0 + C y0² = −(D x0 + E y0)/2, d'où, en u = x − x0, v = y − y0,
    # A u² + B uv + C v² = k
    k = 1.0 - (D * x0 + E * y0) / 2.0
    if k <= 0.0:
        return None
    tr_, dif_ = A + C, math.hypot(A - C, B)
    l1, l2 = (tr_ - dif_) / 2.0, (tr_ + dif_) / 2.0            # l1 ≤ l2 : l1 donne le grand axe
    if l1 <= 0.0:
        return None
    psi = 0.5 * math.degrees(math.atan2(B, A - C)) + 90.0
    psi = (psi + 90.0) % 180.0 - 90.0
    return x0, y0, math.sqrt(k / l1), math.sqrt(k / l2), psi
