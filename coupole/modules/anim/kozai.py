"""Mécanisme de Kozai-Lidov (sans Qt, jumeau de ``src/calc/kozai.ts`` de Coupole Web).

Un corps (astéroïde, satellite, planète) tourne autour d'un astre central ; un perturbateur lointain, sur une orbite
circulaire, le tire.  En moyenne sur les deux orbites (approximation séculaire, ordre quadrupolaire, particule test),
le demi-grand axe ne change pas, mais l'excentricité e et l'inclinaison i (sur le plan du perturbateur) s'échangent :
- C = √(1 − e²) cos i est conservé (moment cinétique le long de l'axe du perturbateur) ;
- l'énergie W = 2 + 3e² − 3 sin² i (1 − e² + 5 e² sin² ω) aussi ;
- au-delà de l'inclinaison critique i_c = arccos √(3/5) = 39,23°, une orbite presque circulaire devient très
  excentrique : e_max = √(1 − (5/3) cos² i₀), atteinte quand i est redescendue à 39,23° ;
- le temps caractéristique est t_K = (M / M′) (a′ / a)³ (1 − e′²)^(3/2) / n.

Équations en t_K (de Holman, Touma et Tremaine 1997 ; vérifiées par SageMath depuis le hamiltonien), intégrées ici
sous forme vectorielle (vecteur excentricité e, moment cinétique réduit j = √(1 − e²) n̂, ẑ normal au plan du
perturbateur), régulière même pour e = 0 (Tremaine, Touma et Kazandjian 2009) :
    dj/dτ = ¾ [(j·ẑ) j × ẑ − 5 (e·ẑ) e × ẑ]
    de/dτ = ¾ [(j·ẑ) e × ẑ + 2 j × e − 5 (e·ẑ) j × ẑ]
Le second membre ne fait que des produits : Coupole et Coupole Web donnent les mêmes nombres."""
from __future__ import annotations

import math

I_CRITIQUE = math.degrees(math.acos(math.sqrt(3.0 / 5.0)))       # 39,231 5°
JOUR_SIDERAL = 86_164.090_5                                      # s
ANNEE = 365.25 * 86_400.0                                        # année julienne (s)

# systèmes : clé → (M / M′, a′ / a, période de l'orbite intérieure en années)
SYSTEMES = (
    ('asteroide', 1047.348_644, 5.2026 / 2.7, 2.7 ** 1.5),               # astéroïde à 2,7 ua, Jupiter à 5,2 ua
    ('satellite', 81.300_568, 384_400.0 / 26_560.0, JOUR_SIDERAL / 2.0 / ANNEE),   # orbite de 12 h, la Lune
    ('exoplanete', 1.0, 100.0, 5.0 ** 1.5),                              # planète à 5 ua, étoile compagne à 500 ua
)


def t_kozai_ans(m_sur_mp: float, ap_sur_a: float, periode_ans: float, ep: float = 0.0) -> float:
    """Temps caractéristique t_K = (M/M′)(a′/a)³ (1 − e′²)^(3/2) P / 2π, en années."""
    return m_sur_mp * ap_sur_a ** 3 * (1.0 - ep * ep) ** 1.5 * periode_ans / (2.0 * math.pi)


def vecteurs(e: float, i_deg: float, w_deg: float, o_deg: float = 0.0):
    """Vecteur excentricité et moment cinétique réduit à partir des éléments (e, i, ω, Ω)."""
    i, w, o = math.radians(i_deg), math.radians(w_deg), math.radians(o_deg)
    eh = (math.cos(o) * math.cos(w) - math.sin(o) * math.sin(w) * math.cos(i),
          math.sin(o) * math.cos(w) + math.cos(o) * math.sin(w) * math.cos(i),
          math.sin(w) * math.sin(i))
    nh = (math.sin(o) * math.sin(i), -math.cos(o) * math.sin(i), math.cos(i))
    g = math.sqrt(1.0 - e * e)
    return [e * x for x in eh], [g * x for x in nh]


def _croix(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def derivees(ev, jv):
    """Second membre (de/dτ, dj/dτ) ; ẑ = (0, 0, 1), donc v × ẑ = (v_y, −v_x, 0)."""
    jz, ez = jv[2], ev[2]
    jxz = [jv[1], -jv[0], 0.0]
    exz = [ev[1], -ev[0], 0.0]
    jxe = _croix(jv, ev)
    dj = [0.75 * (jz * jxz[k] - 5.0 * ez * exz[k]) for k in range(3)]
    de = [0.75 * (jz * exz[k] + 2.0 * jxe[k] - 5.0 * ez * jxz[k]) for k in range(3)]
    return de, dj


def pas_rk4(ev, jv, h):
    """Un pas de Runge-Kutta d'ordre 4, de durée h (en t_K)."""
    def plus(v, d, f):
        return [v[k] + f * d[k] for k in range(3)]
    a1, b1 = derivees(ev, jv)
    a2, b2 = derivees(plus(ev, a1, h / 2.0), plus(jv, b1, h / 2.0))
    a3, b3 = derivees(plus(ev, a2, h / 2.0), plus(jv, b2, h / 2.0))
    a4, b4 = derivees(plus(ev, a3, h), plus(jv, b3, h))
    e2 = [ev[k] + h / 6.0 * (a1[k] + 2.0 * a2[k] + 2.0 * a3[k] + a4[k]) for k in range(3)]
    j2 = [jv[k] + h / 6.0 * (b1[k] + 2.0 * b2[k] + 2.0 * b3[k] + b4[k]) for k in range(3)]
    return e2, j2


H_MAX = 0.005                     # pas maximal (t_K)


def integrer(ev, jv, duree):
    """Avance de `duree` (t_K) par pas égaux d'au plus H_MAX."""
    n = max(1, math.ceil(duree / H_MAX))
    h = duree / n
    for _ in range(n):
        ev, jv = pas_rk4(ev, jv, h)
    return ev, jv


def elements(ev, jv):
    """(e, i en degrés, ω en degrés dans [0, 360[, Ω en degrés) à partir des vecteurs."""
    e = math.sqrt(ev[0] ** 2 + ev[1] ** 2 + ev[2] ** 2)
    jn = math.sqrt(jv[0] ** 2 + jv[1] ** 2 + jv[2] ** 2)
    i = math.degrees(math.acos(max(-1.0, min(1.0, jv[2] / jn))))
    o = math.degrees(math.atan2(jv[0], -jv[1]))                   # ligne des nœuds : ẑ × n̂
    nx, ny = -jv[1], jv[0]                                         # direction du nœud ascendant (non normée)
    nn = math.hypot(nx, ny)
    if e < 1e-12 or nn < 1e-12:
        return e, i, 0.0, o
    cos_w = (nx * ev[0] + ny * ev[1]) / (nn * e)
    sin_w = ev[2] / (e * math.sin(math.radians(i))) if i > 1e-9 else 0.0
    w = math.degrees(math.atan2(sin_w, cos_w)) % 360.0
    return e, i, w, o


def constante_c(e: float, i_deg: float) -> float:
    return math.sqrt(1.0 - e * e) * math.cos(math.radians(i_deg))


def energie(e: float, i_deg: float, w_deg: float) -> float:
    si2 = math.sin(math.radians(i_deg)) ** 2
    return 2.0 + 3.0 * e * e - 3.0 * si2 * (1.0 - e * e + 5.0 * e * e * math.sin(math.radians(w_deg)) ** 2)


def e_max_circulaire(i0_deg: float) -> float:
    """e_max partant d'une orbite circulaire inclinée de i₀ (0 sous l'inclinaison critique)."""
    c2 = math.cos(math.radians(i0_deg)) ** 2
    return math.sqrt(max(0.0, 1.0 - 5.0 / 3.0 * c2))


def i_a_e(c: float, e: float) -> float:
    """Inclinaison (degrés) qui accompagne l'excentricité e sur la trajectoire de constante C."""
    return math.degrees(math.acos(max(-1.0, min(1.0, c / math.sqrt(1.0 - e * e)))))
