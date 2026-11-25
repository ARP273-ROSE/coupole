"""Résonances et chaos : un astéroïde soumis au Soleil et à Jupiter (problème restreint circulaire plan, mêmes équations
que ``lagrange.py``) — sans Qt, jumeau de ``src/calc/resonances.ts`` de Coupole Web.

Unités : distance Soleil-Jupiter a_J = 1, période de Jupiter 2π, masse totale 1 (Soleil 1 − μ, Jupiter μ).  On lâche
l'astéroïde à son périhélie, sur l'orbite képlérienne (a, e) autour du Soleil, à l'angle φ₀ de Jupiter ; un « jumeau »
part à δ₀ de lui.  Éléments osculateurs héliocentriques : a = 1/(2/r − v²/GM), vecteur excentricité, avec la vitesse
inertielle relative au Soleil.  Résonance p:q : l'astéroïde fait p tours quand Jupiter en fait q, à a = (q/p)^(2/3).
Écart entre les jumeaux : il croît comme le temps sur une orbite régulière, exponentiellement sur une orbite chaotique
(rencontres proches de Jupiter) — on ne peut plus prévoir la trajectoire au-delà de quelques temps de Lyapunov."""
from __future__ import annotations

import math

from . import lagrange as lg

A_JUPITER_UA = 5.2026
ANNEE_JUPITER = 11.862                   # période sidérale de Jupiter (ans)
MU_JUPITER = 1.0 / (1.0 + 1047.348_644)
DELTA0 = 1e-7                            # écart initial des jumeaux (en a_J : 78 km)

# cas : clé, a (ua), e, φ₀ (°)
CAS = (('kirkwood', 2.50, 0.10, 0.0), ('ceinture', 2.30, 0.10, 0.0), ('hilda', 3.97, 0.15, 0.0),
       ('troyen', 5.2026, 0.03, 60.0), ('deux_un', 3.28, 0.10, 90.0), ('comete', 3.6, 0.55, 150.0))
RESONANCES = ((1, 1), (3, 2), (2, 1), (7, 3), (5, 2), (3, 1), (4, 1))


def etat_initial(a_ua: float, e: float, phi_deg: float, mu: float) -> tuple:
    """(x, y, vx, vy) dans le repère tournant (barycentre, Jupiter sur +x) d'un astéroïde lâché à son périhélie."""
    a = a_ua / A_JUPITER_UA
    gm = 1.0 - mu
    r = a * (1.0 - e)
    v = math.sqrt(gm * (1.0 + e) / r)
    ph = math.radians(phi_deg)
    x, y = -mu + r * math.cos(ph), r * math.sin(ph)
    vx_i, vy_i = -v * math.sin(ph), v * math.cos(ph) - mu          # + vitesse inertielle du Soleil (0, −μ)
    return (x, y, vx_i + y, vy_i - x)                               # v_tournant = v_inertielle − ω × r


def jumeau(s: tuple, delta: float = DELTA0) -> tuple:
    return (s[0] + delta, s[1], s[2], s[3])


def elements(s: tuple, mu: float) -> tuple[float, float]:
    """(a en ua, e) osculateurs héliocentriques."""
    x, y, vx, vy = s
    dx, dy = x + mu, y
    ux, uy = vx - y, vy + x + mu                                    # vitesse inertielle relative au Soleil
    gm = 1.0 - mu
    r = math.sqrt(dx * dx + dy * dy)
    v2 = ux * ux + uy * uy
    en = v2 / 2.0 - gm / r
    rv = dx * ux + dy * uy
    ex = ((v2 - gm / r) * dx - rv * ux) / gm
    ey = ((v2 - gm / r) * dy - rv * uy) / gm
    e = math.sqrt(ex * ex + ey * ey)
    a = -gm / (2.0 * en) if en < 0.0 else math.inf
    return a * A_JUPITER_UA, e


def rapport_periodes(a_ua: float) -> float:
    """Période de Jupiter / période de l'astéroïde (3 pour la résonance 3:1)."""
    return (A_JUPITER_UA / a_ua) ** 1.5


def resonance_proche(a_ua: float) -> tuple[tuple[int, int], float]:
    """Résonance la plus proche (en a) et l'écart relatif."""
    meilleur = None
    for p, q in RESONANCES:
        ar = A_JUPITER_UA * (q / p) ** (2.0 / 3.0)
        d = (a_ua - ar) / ar
        if meilleur is None or abs(d) < abs(meilleur[1]):
            meilleur = ((p, q), d)
    return meilleur


def ecart(s1: tuple, s2: tuple) -> float:
    return math.hypot(s1[0] - s2[0], s1[1] - s2[1])


def inertiel(x: float, y: float, t: float) -> tuple[float, float]:
    """Du repère tournant au repère fixe (barycentre), au temps t."""
    c, s = math.cos(t), math.sin(t)
    return c * x - s * y, s * x + c * y


def avancer(mu: float, s1: tuple, s2: tuple, duree: float):
    """Avance les deux jumeaux de « duree » (RK4 de lagrange.py) ; rend (s1, s2, collision)."""
    s1, c1 = lg.integrer(mu, s1, duree)
    s2, c2 = lg.integrer(mu, s2, duree)
    return s1, s2, c1 or c2
