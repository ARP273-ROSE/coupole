"""Cratère d'impact : lois d'échelle de G. S. Collins, H. J. Melosh et R. A. Marcus (2005, « Earth Impact Effects
Program », Meteoritics & Planetary Science 40, 817) — sans Qt, jumeau de ``src/calc/cratere.ts`` de Coupole Web.

Unités SI (m, kg, s) sauf mention.  Cratère transitoire (éq. 21) :
    D_tc = 1,161 (ρ_i/ρ_t)^(1/3) L^0,78 v^0,44 g^(−0,22) sin^(1/3) θ        (cible rocheuse ; 1,365 dans l'eau)
    d_tc = D_tc / (2√2)                                                      (éq. 25)
Cratère final : simple si D_tc ≤ 2,56 km : D_fr = 1,25 D_tc (éq. 22), lentille de brèche V_br = 0,032 D_fr³ (23),
h_fr = 0,07 D_tc⁴/D_fr³ (48), t_br = 2,8 V_br (d_tc + h_fr)/(d_tc D_fr²) (24), d_fr = d_tc + h_fr − t_br (26) ;
complexe sinon : D_fr = 1,17 D_tc^1,13 / D_c^0,13 (27, en km, D_c = 3,2 km), d_fr = 0,4 D_fr^0,3 (28, km).
Énergie E = ½ m v², 1 Mt = 4,18 × 10¹⁵ J ; intervalle moyen entre deux impacts aussi énergiques sur la Terre
T ≈ 109 E_Mt^0,78 ans (éq. 3).  L'entrée atmosphérique (freinage, fragmentation) n'est pas modélisée : valable
pour un impacteur de plus de quelques centaines de mètres."""
from __future__ import annotations

import math

G_TERRE = 9.81
MT_J = 4.18e15
D_C_KM = 3.2                     # transition simple / complexe sur la Terre
D_TC_MAX_SIMPLE_KM = 2.56        # = D_C / 1,25
K_ROCHE, K_EAU = 1.161, 1.365

# impacteurs (densités proposées par le programme de Collins et al.) : clé → kg·m⁻³
IMPACTEURS = (('glace', 1000.0), ('poreux', 1500.0), ('rocheux', 3000.0), ('fer', 8000.0))
# cibles rocheuses : clé, densité, constante de l'éq. 21 (1,365 pour une cible d'eau, non proposée)
CIBLES = (('sedimentaire', 2500.0, K_ROCHE), ('cristalline', 2750.0, K_ROCHE))

# exemples : clé, L (m), v (km/s), θ (°), impacteur, cible
EXEMPLES = (('cours', 1500.0, 20.0, 45.0, 'rocheux', 'sedimentaire'),
            ('meteor_crater', 50.0, 12.0, 45.0, 'fer', 'sedimentaire'),
            ('chicxulub', 10000.0, 20.0, 45.0, 'rocheux', 'sedimentaire'))


def masse(L: float, rho_i: float) -> float:
    return math.pi / 6.0 * rho_i * L ** 3


def energie(L: float, rho_i: float, v: float) -> float:
    return 0.5 * masse(L, rho_i) * v * v


def transitoire(L: float, v: float, theta_deg: float, rho_i: float, rho_t: float, k: float = K_ROCHE,
                g: float = G_TERRE) -> float:
    """Diamètre du cratère transitoire (m) ; v en m/s."""
    return (k * (rho_i / rho_t) ** (1.0 / 3.0) * L ** 0.78 * v ** 0.44 * g ** -0.22
            * math.sin(math.radians(theta_deg)) ** (1.0 / 3.0))


def cratere(L: float, v: float, theta_deg: float, rho_i: float, rho_t: float, k: float = K_ROCHE) -> dict:
    """Dimensions (m) : transitoire, final, profondeur, hauteur du rempart, lentille de brèche, genre."""
    dtc_ = transitoire(L, v, theta_deg, rho_i, rho_t, k)
    ptc = dtc_ / (2.0 * math.sqrt(2.0))
    if dtc_ <= D_TC_MAX_SIMPLE_KM * 1000.0:
        dfr = 1.25 * dtc_
        hfr = 0.07 * dtc_ ** 4 / dfr ** 3
        vbr = 0.032 * dfr ** 3
        tbr = 2.8 * vbr * (ptc + hfr) / (ptc * dfr * dfr)
        prof = ptc + hfr - tbr
        genre = 'simple'
    else:
        dfr = 1.17 * (dtc_ / 1000.0) ** 1.13 / D_C_KM ** 0.13 * 1000.0
        hfr = 0.07 * dtc_ ** 4 / dfr ** 3
        tbr = 0.0
        prof = 0.4 * (dfr / 1000.0) ** 0.3 * 1000.0
        genre = 'complexe'
    return {'transitoire': dtc_, 'prof_transitoire': ptc, 'final': dfr, 'profondeur': prof, 'rempart': hfr,
            'breche': tbr, 'genre': genre}


def recurrence_ans(e_mt: float) -> float:
    return 109.0 * e_mt ** 0.78


def profil(c: dict, x: float) -> float:
    """Altitude (m) du profil schématique du cratère final à la distance x (m) du centre : cuvette parabolique de
    profondeur d_fr sous le rempart, rempart h_fr qui décroît en (R/x)³ au-dehors (éq. 31), fond plat au tiers du
    diamètre pour un cratère complexe."""
    R = c['final'] / 2.0
    h, d = c['rempart'], c['profondeur']
    ax = abs(x)
    if ax >= R:
        return h * (R / ax) ** 3
    fond = h - d
    if c['genre'] == 'complexe':
        r0 = R / 3.0
        if ax <= r0:
            return fond
        u = (ax - r0) / (R - r0)
        return fond + d * u * u
    u = ax / R
    return fond + d * u * u
