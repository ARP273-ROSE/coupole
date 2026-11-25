"""Pluies d'étoiles filantes : radiant, hauteur, taux horaire (sans Qt, jumeau de ``src/calc/meteores.ts`` de
Coupole Web).

Les météoroïdes d'un même essaim arrivent parallèles ; vues du sol, leurs traînées semblent jaillir d'un point du
ciel, le radiant (effet de perspective).  Le taux observé dépend de la hauteur h du radiant et de la magnitude
limite du ciel : HR = ZHR × sin h ÷ r^(6,5 − m_lim) (r : indice de population de l'essaim ; formule de l'IMO, avec
l'exposant γ = 1).  Données des essaims : calendrier de l'International Meteor Organization (radiant au maximum,
vitesse d'entrée v∞, ZHR, r).  Heure : temps solaire moyen local (observateur supposé sur le méridien de Greenwich :
même heure locale, même ciel)."""
from __future__ import annotations

import math

from . import astro

# clé → (mois, jour du maximum, α en degrés, δ en degrés, v∞ km/s, ZHR, r, constellation)
ESSAIMS = {
    'quadrantides': (1, 4, 230.0, 49.0, 41.0, 80.0, 2.1, 'bouvier'),
    'lyrides': (4, 22, 271.0, 34.0, 49.0, 18.0, 2.1, 'lyre'),
    'eta_aquarides': (5, 6, 338.0, -1.0, 66.0, 50.0, 2.4, 'verseau'),
    'perseides': (8, 12, 48.0, 58.0, 59.0, 100.0, 2.2, 'persee'),
    'orionides': (10, 21, 95.0, 16.0, 66.0, 20.0, 2.5, 'orion'),
    'leonides': (11, 17, 152.0, 22.0, 71.0, 15.0, 2.5, 'lion'),
    'geminides': (12, 14, 112.0, 33.0, 35.0, 150.0, 2.6, 'gemeaux'),
}
ANNEE = 2026


def jour_julien(essaim: str, heure: float) -> float:
    """Jour julien (TU) de la nuit du maximum ; heure locale de 18 à 30 (30 = 6 h le lendemain matin)."""
    mois, jour = ESSAIMS[essaim][:2]
    return astro.jour_julien(ANNEE, mois, float(jour)) + heure / 24.0


def hauteur_radiant(essaim: str, heure: float, lat: float) -> tuple[float, float]:
    """Azimut (depuis le nord, vers l'est) et hauteur du radiant, en degrés."""
    alpha, delta = ESSAIMS[essaim][2:4]
    h = astro.tsmg(jour_julien(essaim, heure)) - alpha
    return astro.equatorial_vers_horizon(h, delta, lat)


def hauteur_soleil(essaim: str, heure: float, lat: float) -> float:
    s = astro.soleil(jour_julien(essaim, heure))
    h = astro.tsmg(jour_julien(essaim, heure)) - s['alpha']
    return astro.equatorial_vers_horizon(h, s['delta'], lat)[1]


def taux_horaire(essaim: str, h_radiant: float, m_lim: float = 6.5) -> float:
    """Nombre d'étoiles filantes par heure pour un observateur : ZHR × sin h ÷ r^(6,5 − m_lim) ; 0 sous l'horizon."""
    zhr, r = ESSAIMS[essaim][5:7]
    if h_radiant <= 0:
        return 0.0
    return zhr * math.sin(math.radians(h_radiant)) / r ** (6.5 - m_lim)


def culmination(essaim: str, lat: float) -> tuple[float, float]:
    """Heure locale (0–24) du passage du radiant au méridien, la nuit du maximum, et sa hauteur alors
    (90° − |φ − δ|)."""
    alpha, delta = ESSAIMS[essaim][2:4]
    theta0 = astro.tsmg(jour_julien(essaim, 18.0))
    heures = ((alpha - theta0) % 360.0) / 360.985_647_366_29 * 24.0
    return (18.0 + heures) % 24.0, 90.0 - abs(lat - delta)


class Aleatoire:
    """Générateur pseudo-aléatoire de Park et Miller (16807 x mod 2³¹ − 1) : exact en Python comme en JavaScript,
    donc mêmes étoiles filantes dans les deux applications."""

    M = 2_147_483_647

    def __init__(self, graine: int = 12345):
        self.x = graine % self.M or 1

    def __call__(self) -> float:
        self.x = (16807 * self.x) % self.M
        return self.x / self.M


def etoiles_de_fond(n: int = 320, graine: int = 2026) -> list:
    """Étoiles de fond (α, δ en degrés, magnitude) tirées uniformément sur la sphère (pas un vrai catalogue)."""
    g = Aleatoire(graine)
    out = []
    for _ in range(n):
        alpha = 360.0 * g()
        delta = math.degrees(math.asin(2.0 * g() - 1.0))
        out.append((alpha, delta, 1.0 + 5.0 * g() ** 0.45))
    return out


def vers_horizon(az: float, alt: float):
    """(azimut, hauteur) → vecteur unitaire (nord, est, zénith)."""
    a, h = math.radians(az), math.radians(alt)
    return (math.cos(h) * math.cos(a), math.cos(h) * math.sin(a), math.sin(h))


def depuis_vecteur(v) -> tuple[float, float]:
    x, y, z = v
    return math.degrees(math.atan2(y, x)) % 360.0, math.degrees(math.asin(max(-1.0, min(1.0, z))))


def trainee(g: Aleatoire, az_r: float, alt_r: float) -> tuple | None:
    """Une étoile filante : point d'apparition tiré au hasard dans le ciel (au-dessus de 8°), traînée dirigée à
    l'opposé du radiant le long d'un grand cercle, longueur 25° × sin D × (0,5 à 1,2) (D : distance au radiant ;
    près du radiant, les traînées sont courtes : on les voit presque de face).  Rend (az0, h0, az1, h1, D) ou None
    (point sous 8° de hauteur)."""
    u, w = g(), g()
    h0 = math.degrees(math.asin(u))
    az0 = 360.0 * w
    f = 0.5 + 0.7 * g()
    if h0 < 8.0:
        return None
    r = vers_horizon(az_r, alt_r)
    p = vers_horizon(az0, h0)
    c = max(-1.0, min(1.0, sum(a * b for a, b in zip(r, p))))
    d = math.acos(c)
    if d < math.radians(1.5):
        return (az0, h0, az0, h0, math.degrees(d))
    t = tuple((pi * c - ri) / math.sin(d) for pi, ri in zip(p, r))
    lg = math.radians(25.0 * math.sin(d) * f)
    q = tuple(pi * math.cos(lg) + ti * math.sin(lg) for pi, ti in zip(p, t))
    az1, h1 = depuis_vecteur(q)
    return (az0, h0, az1, h1, math.degrees(d))


def arc(az0: float, h0: float, az1: float, h1: float, n: int = 16) -> list:
    """Points (azimut, hauteur) de l'arc de grand cercle le plus court entre deux directions (une traînée est un arc
    de grand cercle : sur la carte du ciel, une courbe)."""
    a, b = vers_horizon(az0, h0), vers_horizon(az1, h1)
    c = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    om = math.acos(c)
    if om < 1e-9:
        return [(az0, h0), (az1, h1)]
    out = []
    for k in range(n + 1):
        t = k / n
        s0, s1 = math.sin((1 - t) * om) / math.sin(om), math.sin(t * om) / math.sin(om)
        out.append(depuis_vecteur(tuple(s0 * x + s1 * y for x, y in zip(a, b))))
    return out
