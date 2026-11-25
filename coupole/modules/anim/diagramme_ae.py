"""Le diagramme demi-grand axe – excentricité (sans Qt, jumeau de ``src/calc/diagramme_ae.ts`` de Coupole Web).

Un point (a, e) du diagramme fixe la forme et la taille d'une orbite autour du Soleil : périhélie q = a(1 − e),
aphélie Q = a(1 + e), période P = a^(3/2) (ans, a en ua).  Les familles de géocroiseurs (CNEOS) se lisent sur
des courbes de q ou de Q constants : Atira (a < 1, Q < 0,983), Aten (a < 1, Q > 0,983), Apollo (a > 1,
q < 1,017), Amor (a > 1, 1,017 < q < 1,3) ; puis croiseurs de Mars (q < 1,666), ceinture principale, troyens,
centaures, transneptuniens (classes orbitales de la base SBDB du JPL).  Le paramètre de Tisserand vis-à-vis de
Jupiter, T_J = a_J/a + 2 cos i √((a/a_J)(1 − e²)), sépare les orbites d'astéroïdes (T_J > 3) de celles des comètes
de la famille de Jupiter (2 < T_J < 3) et de type Halley (T_J < 2).  Les lacunes de Kirkwood tombent aux
résonances de moyen mouvement avec Jupiter : a = a_J (q/p)^(2/3)."""
from __future__ import annotations

import math

A_JUPITER = 5.2026                     # ua (comme lagrange.py)

# planètes : clé, a (ua), e (éléments moyens J2000, arrondis)
PLANETES = (('mercure', 0.387, 0.206), ('venus', 0.723, 0.007), ('terre', 1.0, 0.017), ('mars', 1.524, 0.093),
            ('jupiter', 5.203, 0.048), ('saturne', 9.537, 0.054), ('uranus', 19.19, 0.047),
            ('neptune', 30.07, 0.009))

# petits corps : clé, a (ua), e, i (°) — base SBDB du JPL (novembre 2026), arrondis à trois chiffres
OBJETS = (
    ('atira', 0.741, 0.322, 25.6), ('apophis', 0.922, 0.191, 3.34), ('tk7', 0.999, 0.19, 20.9),
    ('cruithne', 0.998, 0.515, 19.8), ('bennu', 1.13, 0.204, 6.03), ('ryugu', 1.19, 0.191, 5.87),
    ('itokawa', 1.32, 0.28, 1.62), ('icare', 1.08, 0.827, 22.8), ('phaethon', 1.27, 0.89, 22.3),
    ('didymos', 1.64, 0.383, 3.41), ('toutatis', 2.54, 0.625, 0.448), ('eros', 1.46, 0.223, 10.8),
    ('encke', 2.22, 0.847, 11.3), ('vesta', 2.36, 0.0902, 7.14), ('ceres', 2.77, 0.0797, 10.6),
    ('pallas', 2.77, 0.231, 34.9), ('hygie', 3.15, 0.107, 3.83), ('tchouri', 3.46, 0.641, 7.04),
    ('hilda', 3.97, 0.138, 7.83), ('hektor', 5.28, 0.0243, 18.1), ('hidalgo', 5.73, 0.662, 42.5),
    ('chiron', 13.7, 0.38, 6.93), ('halley', 17.9, 0.968, 162.0), ('swift_tuttle', 26.1, 0.963, 113.0),
    ('pluton', 39.6, 0.252, 17.1), ('arrokoth', 44.1, 0.0356, 2.45), ('eris', 67.9, 0.438, 43.9),
)

# limites des familles (ua)
Q_ATIRA = 0.983                        # aphélie de l'Atira < périhélie de la Terre
Q_APOLLO = 1.017                       # périhélie de l'Apollo < aphélie de la Terre
Q_GEOCROISEUR = 1.3
Q_MARS = 1.666                         # aphélie de Mars

# résonances de moyen mouvement avec Jupiter (p : q), lacunes de Kirkwood puis groupes retenus
LACUNES = ((3, 1), (5, 2), (7, 3), (2, 1))
GROUPES = ((3, 2), (1, 1))


def perihelie(a: float, e: float) -> float:
    return a * (1.0 - e)


def aphelie(a: float, e: float) -> float:
    return a * (1.0 + e)


def periode(a: float) -> float:
    """Période (ans) d'un corps de masse négligeable autour du Soleil, a en ua."""
    return a * math.sqrt(a)


def tisserand(a: float, e: float, i_deg: float, aj: float = A_JUPITER) -> float:
    return aj / a + 2.0 * math.cos(math.radians(i_deg)) * math.sqrt(a / aj * (1.0 - e * e))


def genre_tisserand(t: float) -> str:
    if t > 3.0:
        return 'asteroide'
    if t > 2.0:
        return 'comete_jupiter'
    return 'comete_halley'


def resonance(p: int, q: int, aj: float = A_JUPITER) -> float:
    """Demi-grand axe où le corps fait p tours quand Jupiter en fait q."""
    return aj * (q / p) ** (2.0 / 3.0)


def famille(a: float, e: float) -> str:
    q, Q = perihelie(a, e), aphelie(a, e)
    if q < Q_GEOCROISEUR:
        if a < 1.0:
            return 'atira' if Q < Q_ATIRA else 'aten'
        return 'apollo' if q < Q_APOLLO else 'amor'
    if a < 3.2:
        if q < Q_MARS:
            return 'croiseur_mars'
        return 'ceinture_int' if a < 2.0 else 'ceinture'
    if a < 4.6:
        return 'ceinture_ext'
    if a < 5.5:
        return 'troyen' if e < 0.3 else 'autre'
    if a < 30.1:
        return 'centaure'
    return 'transneptunien'


def croisees(a: float, e: float) -> list[str]:
    """Planètes dont l'orbite (supposée circulaire) est traversée : q < a_planète < Q."""
    q, Q = perihelie(a, e), aphelie(a, e)
    return [k for k, ap, _ in PLANETES if q < ap < Q]


def kepler(m: float, e: float) -> float:
    """Anomalie excentrique E (Newton, départ π si e > 0,8)."""
    m = math.fmod(m, 2.0 * math.pi)
    E = math.pi if e > 0.8 else m
    for _ in range(50):
        d = (E - e * math.sin(E) - m) / (1.0 - e * math.cos(E))
        E -= d
        if abs(d) < 1e-14:
            break
    return E


def position(a: float, e: float, m: float) -> tuple[float, float]:
    """Position dans le plan de l'orbite (périhélie sur +x), Soleil à l'origine, anomalie moyenne m."""
    E = kepler(m, e)
    return a * (math.cos(E) - e), a * math.sqrt(1.0 - e * e) * math.sin(E)


def distance_soleil(a: float, e: float, m: float) -> float:
    return a * (1.0 - e * math.cos(kepler(m, e)))
