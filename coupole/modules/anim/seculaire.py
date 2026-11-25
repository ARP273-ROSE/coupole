"""Précession séculaire d'une orbite qui croise celle de la Terre (sans Qt, jumeau de ``src/calc/seculaire.ts`` de
Coupole Web).

Théorie séculaire linéaire de Laplace-Lagrange pour une particule test (C. D. Murray et S. F. Dermott, « Solar System
Dynamics », 1999, chapitre 7) : en moyenne sur les révolutions, le demi-grand axe a d'un astéroïde ne change pas,
mais son orbite tourne.  Avec des planètes perturbatrices sur des orbites circulaires et coplanaires (ici les quatre
planètes géantes, dans l'écliptique), les éléments forcés sont nuls et
    ϖ = ϖ₀ + A t,   Ω = Ω₀ − A t   (donc ω = ϖ − Ω = ω₀ + 2A t ; e et i ne changent pas),
    A = (n/4) Σⱼ (mⱼ/M☉) αⱼ² b⁽¹⁾₃/₂(αⱼ),   αⱼ = a/aⱼ < 1,
n moyen mouvement de l'astéroïde, b⁽¹⁾₃/₂ coefficient de Laplace :
    b⁽ʲ⁾ₛ(α) = (1/π) ∫₀^2π cos(jψ) dψ / (1 − 2α cos ψ + α²)^s.
Au premier ordre en α, A = ¾ n Σ (mⱼ/M☉) αⱼ³ (la limite quadrupolaire, celle du mécanisme de Kozai-Lidov à e = 0).

L'orbite perce l'écliptique aux nœuds, à r☊ = p/(1 + e cos ω) et r☋ = p/(1 − e cos ω), p = a(1 − e²) : elle coupe
l'orbite de la Terre (cercle de 1 ua) quand un nœud y passe, quatre fois par tour de ω si q < 1 < Q.  La distance
minimale entre les deux orbites (MOID) ne dépend que de a, e, i et ω (l'orbite terrestre est un cercle) : elle s'annule
à chaque croisement.

Limites : théorie linéaire (exacte pour e et i petits ; ordre de grandeur pour un géocroiseur) ; les planètes
telluriques, que ces orbites croisent, sont laissées de côté (la théorie y diverge) : elles accélèrent en vrai la
précession ; les rencontres proches et les résonances ne sont pas représentées."""
from __future__ import annotations

import math

DEUX_PI = 2.0 * math.pi
SEC_PAR_RAD = 180.0 / math.pi * 3600.0
N_LAPLACE = 256                      # points de la quadrature (trapèzes, exacte à 10⁻¹⁵ pour α < 0,6)
AN_DEPART = 2026.0                   # époque des éléments

# planètes géantes : clé, a (ua, éléments moyens J2000 de E. M. Standish, JPL, arrondis), M☉/m (UAI 2009)
GEANTES = (('jupiter', 5.2029, 1047.348_644), ('saturne', 9.5367, 3497.9018), ('uranus', 19.1892, 22_902.98),
           ('neptune', 30.0699, 19_412.26))

# astéroïdes géocroiseurs : clé, a (ua), e, i (°), Ω (°), ω (°) — base SBDB du JPL, époque 2026, arrondis
OBJETS = (('apollo', 1.47, 0.56, 6.35, 35.5, 286.0), ('icare', 1.08, 0.827, 22.8, 87.9, 31.4),
          ('phaethon', 1.27, 0.89, 22.3, 265.0, 322.0), ('adonis', 1.87, 0.764, 1.32, 349.0, 43.7),
          ('toutatis', 2.54, 0.625, 0.448, 125.0, 278.0))


def laplace_b(s: float, j: int, alpha: float, n: int = N_LAPLACE) -> float:
    """Coefficient de Laplace b⁽ʲ⁾ₛ(α) par la règle des trapèzes (fonction périodique : convergence géométrique)."""
    tot = 0.0
    for k in range(n):
        psi = DEUX_PI * k / n
        tot += math.cos(j * psi) / (1.0 - 2.0 * alpha * math.cos(psi) + alpha * alpha) ** s
    return 2.0 * tot / n


def moyen_mouvement(a: float) -> float:
    """n en radians par an (a en ua, masse de l'astéroïde négligée)."""
    return DEUX_PI / (a * math.sqrt(a))


def terme(a: float, aj: float, rapport: float) -> float:
    """Contribution (sans dimension) d'une planète extérieure : (m/M☉) α² b⁽¹⁾₃/₂(α)."""
    al = a / aj
    return al * al * laplace_b(1.5, 1, al) / rapport


def frequence(a: float) -> float:
    """A (radians par an) : vitesse de rotation de ϖ (et, en sens inverse, de Ω)."""
    return moyen_mouvement(a) / 4.0 * sum(terme(a, aj, m) for _, aj, m in GEANTES)


def frequence_quadrupole(a: float) -> float:
    """Limite α → 0 : ¾ n Σ (m/M☉) α³."""
    return 0.75 * moyen_mouvement(a) * sum((a / aj) ** 3 / m for _, aj, m in GEANTES)


def angles(w0: float, o0: float, A: float, t: float) -> tuple[float, float, float]:
    """(ω, Ω, ϖ) en degrés (0–360) au temps t (années depuis l'époque)."""
    d = math.degrees(A * t)
    o = (o0 - d) % 360.0
    w = (w0 + 2.0 * d) % 360.0
    return w, o, (w + o) % 360.0


def noeuds(a: float, e: float, w_deg: float) -> tuple[float, float]:
    """Distances au Soleil (ua) des nœuds ascendant et descendant."""
    p = a * (1.0 - e * e)
    c = e * math.cos(math.radians(w_deg))
    return p / (1.0 + c), p / (1.0 - c)


def croise(a: float, e: float) -> bool:
    """Un nœud peut-il passer sur l'orbite de la Terre (q ≤ 1 ≤ Q) ?"""
    return a * (1.0 - e) <= 1.0 <= a * (1.0 + e)


def croisements(a: float, e: float, w0: float, A: float, t0: float, t1: float) -> list:
    """Instants (années depuis l'époque, triés) où un nœud est à 1 ua, entre t0 et t1 : [(t, 'asc' | 'desc')]."""
    if not croise(a, e) or e <= 0.0 or A <= 0.0:
        return []
    c = (a * (1.0 - e * e) - 1.0) / e
    c = max(-1.0, min(1.0, c))
    ac = math.acos(c)
    demi = math.pi / A                            # période de ω
    out = []
    for genre, cible in (('asc', ac), ('asc', -ac), ('desc', math.pi - ac), ('desc', math.pi + ac)):
        t = (cible - math.radians(w0)) / (2.0 * A)
        k = math.ceil((t0 - t) / demi)
        tk = t + k * demi
        while tk <= t1:
            out.append((tk, genre))
            tk += demi
    out.sort()
    return out


def _d2(p: float, e: float, ci: float, si: float, w: float, nu: float) -> float:
    """Carré de la distance entre le point d'anomalie vraie ν et le cercle de rayon 1 de l'écliptique."""
    r = p / (1.0 + e * math.cos(nu))
    u = w + nu
    cu, su = math.cos(u), math.sin(u)
    rho = r * math.sqrt(cu * cu + su * su * ci * ci)
    z = r * su * si
    return (rho - 1.0) ** 2 + z * z


N_MOID = 360
OR = (math.sqrt(5.0) - 1.0) / 2.0


def moid(a: float, e: float, i_deg: float, w_deg: float, n: int = N_MOID) -> float:
    """Distance minimale (ua) entre l'orbite et l'orbite terrestre (cercle de 1 ua) : n points, puis section dorée."""
    p = a * (1.0 - e * e)
    i, w = math.radians(i_deg), math.radians(w_deg)
    ci, si = math.cos(i), math.sin(i)
    pas = DEUX_PI / n
    kmin, dmin = 0, float('inf')
    for k in range(n):
        d = _d2(p, e, ci, si, w, k * pas)
        if d < dmin:
            kmin, dmin = k, d
    lo, hi = (kmin - 1) * pas, (kmin + 1) * pas
    x1, x2 = hi - OR * (hi - lo), lo + OR * (hi - lo)
    f1, f2 = _d2(p, e, ci, si, w, x1), _d2(p, e, ci, si, w, x2)
    for _ in range(40):
        if f1 < f2:
            hi, x2, f2 = x2, x1, f1
            x1 = hi - OR * (hi - lo)
            f1 = _d2(p, e, ci, si, w, x1)
        else:
            lo, x1, f1 = x1, x2, f2
            x2 = lo + OR * (hi - lo)
            f2 = _d2(p, e, ci, si, w, x2)
    return math.sqrt(min(dmin, f1, f2))


def table_moid(a: float, e: float, i_deg: float, n: int = 120) -> list:
    """MOID pour ω = 0, 360/n, … 360° (n + 1 valeurs ; sans affinage, pour le graphe)."""
    return [moid(a, e, i_deg, 360.0 * k / n, 180) for k in range(n + 1)]


def orbite(a: float, e: float, i_deg: float, o_deg: float, w_deg: float, n: int = 180) -> list:
    """Points (x, y, z) de l'orbite dans le repère de l'écliptique (ua)."""
    i, o, w = math.radians(i_deg), math.radians(o_deg), math.radians(w_deg)
    co, so, ci, si = math.cos(o), math.sin(o), math.cos(i), math.sin(i)
    p = a * (1.0 - e * e)
    out = []
    for k in range(n + 1):
        nu = DEUX_PI * k / n
        r = p / (1.0 + e * math.cos(nu))
        u = w + nu
        cu, su = math.cos(u), math.sin(u)
        out.append((r * (co * cu - so * su * ci), r * (so * cu + co * su * ci), r * su * si))
    return out
