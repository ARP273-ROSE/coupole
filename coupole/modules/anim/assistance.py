"""L'assistance gravitationnelle (survol d'une planète) en coniques raccordées — sans Qt, jumeau de
``src/calc/assistance.ts`` de Coupole Web.

Dans le repère de la planète, la sonde arrive avec la vitesse d'excès hyperbolique v∞ et repart avec la même
vitesse, tournée de δ = 2 arcsin(1 / (1 + r_p v∞²/μ)) (r_p : distance au périastre, μ = GM de la planète).  Dans
le repère du Soleil, on ajoute la vitesse V de la planète : v = V + v∞.  Passer derrière la planète (par rapport à
son mouvement) tourne v∞ vers l'avant et accélère la sonde ; passer devant la freine.  Le gain vient de la planète,
qui ralentit d'une quantité infime.  Plan, planète sur une orbite circulaire, survol instantané à l'échelle du
Soleil.  Unités : km, s."""
from __future__ import annotations

import math

GM_SOLEIL = 1.327_124_400_18e11          # km³ s⁻²
UA = 149_597_870.7                       # km

# planètes : clé, GM (km³ s⁻²), rayon équatorial (km), a (ua)
PLANETES = (('venus', 324_858.59, 6051.8, 0.723), ('terre', 398_600.44, 6378.1, 1.0),
            ('mars', 42_828.37, 3396.2, 1.524), ('jupiter', 126_686_534.0, 71_492.0, 5.203),
            ('saturne', 37_931_187.0, 60_268.0, 9.537))


def planete(cle: str) -> tuple[float, float, float]:
    for k, gm, r, a in PLANETES:
        if k == cle:
            return gm, r, a
    raise KeyError(cle)


def vitesse_planete(a_ua: float) -> float:
    return math.sqrt(GM_SOLEIL / (a_ua * UA))


def deviation(v_inf: float, r_p: float, gm: float) -> float:
    """Angle δ (rad) dont tourne la vitesse relative."""
    return 2.0 * math.asin(1.0 / (1.0 + r_p * v_inf * v_inf / gm))


def tourner(v: tuple[float, float], ang: float) -> tuple[float, float]:
    c, s = math.cos(ang), math.sin(ang)
    return c * v[0] - s * v[1], s * v[0] + c * v[1]


def survol(cle: str, v_inf: float, r_p_rayons: float, angle_deg: float, derriere: bool) -> dict:
    """Bilan du survol.  La planète file selon +x ; v∞ arrive dans la direction `angle_deg` (0 : dans le sens de
    la planète).  `derriere` : la sonde passe du côté arrière de la planète."""
    gm, rayon, a = planete(cle)
    V = vitesse_planete(a)
    r_p = r_p_rayons * rayon
    ang = math.radians(angle_deg)
    u = (math.cos(ang), math.sin(ang))
    n = (-u[1], u[0])                                   # côté du passage : n pointe de la planète vers la sonde
    if n[0] != 0.0 and (n[0] < 0.0) != derriere:
        n = (-n[0], -n[1])
    d = deviation(v_inf, r_p, gm)
    u_out = (math.cos(d) * u[0] - math.sin(d) * n[0], math.cos(d) * u[1] - math.sin(d) * n[1])
    v_in = (V + v_inf * u[0], v_inf * u[1])
    v_out = (V + v_inf * u_out[0], v_inf * u_out[1])
    e = 1.0 + r_p * v_inf * v_inf / gm
    b = r_p * math.sqrt(1.0 + 2.0 * gm / (r_p * v_inf * v_inf))
    return {'V': V, 'r_p': r_p, 'delta': d, 'e': e, 'b': b, 'u_in': u, 'u_out': u_out, 'n': n,
            'v_in': v_in, 'v_out': v_out, 'gain': math.hypot(*v_out) - math.hypot(*v_in),
            'dv': 2.0 * v_inf * math.sin(d / 2.0), 'v_peri': math.sqrt(v_inf * v_inf + 2.0 * gm / r_p),
            'orb_in': orbite_soleil(a, v_in), 'orb_out': orbite_soleil(a, v_out)}


def orbite_soleil(a_ua: float, v: tuple[float, float]) -> dict:
    """Orbite autour du Soleil d'une sonde au point (a, 0) avec la vitesse v = (vₜ, vᵣ) (km/s) : demi-grand axe et
    excentricité (vecteur de Laplace), périhélie et aphélie en ua ; e ≥ 1 : libérée du Système solaire."""
    r = a_ua * UA
    vt, vr = v                                          # vₜ : composante le long du mouvement de la planète
    v2 = vt * vt + vr * vr
    en = v2 / 2.0 - GM_SOLEIL / r
    h = r * vt
    e = math.sqrt(max(0.0, 1.0 + 2.0 * en * h * h / (GM_SOLEIL * GM_SOLEIL)))
    if en >= 0.0:
        return {'a': math.inf, 'e': e, 'q': h * h / GM_SOLEIL / (1.0 + e) / UA, 'Q': math.inf}
    a = -GM_SOLEIL / (2.0 * en)
    return {'a': a / UA, 'e': e, 'q': a * (1.0 - e) / UA, 'Q': a * (1.0 + e) / UA}


def hyperbole(s: dict, gm: float, f: float) -> tuple[float, float]:
    """Point de l'hyperbole (km, repère de la planète) d'anomalie hyperbolique f (négative avant le périastre)."""
    a = s['r_p'] / (s['e'] - 1.0)
    p_ = _norme((s['u_in'][0] - s['u_out'][0], s['u_in'][1] - s['u_out'][1]))
    w = _norme((s['u_in'][0] + s['u_out'][0], s['u_in'][1] + s['u_out'][1]))
    x = a * (s['e'] - math.cosh(f))
    y = a * math.sqrt(s['e'] ** 2 - 1.0) * math.sinh(f)
    return x * p_[0] + y * w[0], x * p_[1] + y * w[1]


def anomalie(s: dict, gm: float, t: float) -> float:
    """Anomalie hyperbolique f au temps t (s) après le périastre : e sinh f − f = n t (Newton)."""
    a = s['r_p'] / (s['e'] - 1.0)
    m = math.sqrt(gm / a ** 3) * t
    f = math.asinh(m / s['e']) if s['e'] > 1.0 else 0.0
    for _ in range(60):
        d = (s['e'] * math.sinh(f) - f - m) / (s['e'] * math.cosh(f) - 1.0)
        f -= d
        if abs(d) < 1e-13:
            break
    return f


def _norme(v):
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n) if n > 0.0 else (1.0, 0.0)
