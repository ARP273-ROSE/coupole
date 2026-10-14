"""Propriétés stellaires : relations physiques exactes et étalonnages empiriques des animations ClassAction.

Exact : loi de Stefan-Boltzmann L = 4π R² σ T⁴ (σ exacte, CODATA 2018), constantes solaires nominales de l'UAI
(résolution 2015 B3 : R☉ = 695 700 km, L☉ = 3,828 × 10²⁶ W, d'où T☉ = 5 772 K), magnitude bolométrique absolue du
Soleil 4,74 (UAI 2015 B2) et loi de Pogson (facteur 2,5 ; l'original écrivait 2,51189, soit 10^0,4, par erreur),
flux F = L / 4π d², vitesses (effet Doppler, mouvement propre).

Empirique (repris tel quel de l'original, comme une table de mesures) : température selon le type spectral (table
par classe de luminosité, et polynômes du diagramme HR), corrections bolométriques, séquences des classes de
luminosité, indice de couleur B − V, couleur d'affichage d'une étoile selon sa température."""
from __future__ import annotations

import math

SIGMA = 5.670_374_419e-8                  # W m⁻² K⁻⁴ (exacte depuis la redéfinition du SI)
R_SOLEIL_M = 6.957e8                      # UAI 2015 B3
L_SOLEIL_W = 3.828e26                     # UAI 2015 B3
T_SOLEIL = (L_SOLEIL_W / (4 * math.pi * R_SOLEIL_M ** 2 * SIGMA)) ** 0.25    # 5 772,0 K
MBOL_SOLEIL = 4.74                        # UAI 2015 B2
C_KM_S = 299_792.458
UA_PAR_AN_KM_S = 149_597_870.700 / (365.25 * 86_400)                          # 4,740 470 km/s


# ---------------------------------------------------------------- physique exacte
def luminosite_solaire(rayon_rsol: float, temperature: float) -> float:
    """L / L☉ = (R / R☉)² (T / T☉)⁴."""
    return rayon_rsol ** 2 * (temperature / T_SOLEIL) ** 4


def puissance_w(rayon_m: float, temperature: float) -> float:
    """L = 4π R² σ T⁴ (watts)."""
    return 4 * math.pi * rayon_m ** 2 * SIGMA * temperature ** 4


def rayon_solaire(luminosite_lsol: float, temperature: float) -> float:
    """R / R☉ = √(L / L☉) / (T / T☉)²."""
    return math.sqrt(luminosite_lsol) / (temperature / T_SOLEIL) ** 2


def flux(puissance: float, distance: float) -> float:
    """Flux reçu à la distance d d'une source isotrope : F = P / 4π d²."""
    return puissance / (4 * math.pi * distance ** 2)


def mbol_de_log_lum(log_l: float) -> float:
    return MBOL_SOLEIL - 2.5 * log_l


def log_lum_de_mbol(mbol: float) -> float:
    return (MBOL_SOLEIL - mbol) / 2.5


def vitesse_radiale(lambda_obs: float, lambda_repos: float, relativiste: bool = False) -> float:
    """Vitesse radiale (km/s, > 0 : éloignement) d'après le décalage d'une raie : c Δλ / λ₀, ou la formule de l'effet
    Doppler relativiste longitudinal c (r² − 1) / (r² + 1) avec r = λ / λ₀."""
    if relativiste:
        r = lambda_obs / lambda_repos
        return C_KM_S * (r * r - 1) / (r * r + 1)
    return C_KM_S * (lambda_obs - lambda_repos) / lambda_repos


def vitesse_transverse(mouvement_propre_arcsec_an: float, distance_pc: float) -> float:
    """v_t = 4,74 μ d (km/s ; μ en ″/an, d en parsecs) : 1 ua/an = 4,740 47 km/s."""
    return UA_PAR_AN_KM_S * mouvement_propre_arcsec_an * distance_pc


# ---------------------------------------------------------------- étalonnages empiriques de l'original
_TABLES_TYPES = {
    'V': ((7, 38000), (9, 33200), (9.5, 31450), (10, 29700), (11, 25600), (12, 22300), (13, 19000), (14, 17200),
          (15, 15400), (16, 14100), (17, 13000), (18, 11800), (19, 10700), (20, 9480), (22, 8810), (25, 8160),
          (27, 7930), (30, 7020), (32, 6750), (35, 6530), (37, 6240), (40, 5930), (42, 5830), (44, 5740),
          (46, 5620), (50, 5240), (52, 5010), (54, 4560), (55, 4340), (57, 4040), (60, 3800), (61, 3680),
          (62, 3530), (63, 3380), (64, 3180), (65, 3030), (66, 2850)),
    'III': ((40, 5910), (44, 5190), (46, 5050), (48, 4960), (50, 4810), (51, 4610), (52, 4500), (53, 4320),
            (54, 4080), (55, 3980), (60, 3820), (61, 3780), (62, 3710), (63, 3630), (64, 3560), (65, 3420),
            (66, 3250)),
    'I': ((9, 32500), (10, 26000), (11, 20700), (12, 17800), (13, 15600), (14, 13900), (15, 13400), (16, 12700),
          (17, 12000), (18, 11200), (19, 10500), (20, 9730), (21, 9230), (22, 9080), (25, 8510), (30, 7700),
          (32, 7170), (35, 6640), (38, 6100), (40, 5510), (43, 4980), (48, 4590), (50, 4420), (51, 4330),
          (52, 4260), (53, 4130), (55, 3850), (60, 3650), (61, 3550), (62, 3450), (63, 3200), (64, 2980)),
}
LETTRES = 'OBAFGKM'


def nom_type(x: float) -> str:
    """Type spectral numérique (O0 = 0, B0 = 10 … M9 = 69) → « G2 », « B9,5 » (virgule selon la langue)."""
    from .base import nombre
    lettre = LETTRES[max(0, min(6, int(x // 10)))]
    n = x - 10 * (x // 10)
    return lettre + (str(int(round(n))) if abs(n - round(n)) < 1e-9 else nombre(n, 1))


def temperature_de_type(x: float, classe: str = 'V') -> float:
    """Température effective (K) par interpolation linéaire dans la table de l'original (classes V, III, I ;
    extrapolation aux bords comme l'original)."""
    t = _TABLES_TYPES[classe]
    i = 0
    while i < len(t) and x >= t[i][0]:
        i += 1
    i1, i2 = (0, 1) if i == 0 else ((len(t) - 2, len(t) - 1) if i == len(t) else (i - 1, i))
    (x1, y1), (x2, y2) = t[i1], t[i2]
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


def _poly(x, morceaux, dernier):
    for borne, c in morceaux:
        if x < borne:
            return c[0] + x * (c[1] + x * (c[2] + x * c[3]))
    return dernier[0] + x * (dernier[1] + x * (dernier[2] + x * dernier[3]))


def log_temp_de_type(x: float) -> float:
    """log₁₀ T selon le type spectral numérique (polynômes du diagramme HR de l'original)."""
    return _poly(x, ((8.5167, (4.7009, -0.01, 0.0000392, -0.00014247)),
                     (16.1, (4.4348, 0.08374, -0.010967, 0.000288299)),
                     (23.2167, (6.0516, -0.21754, 0.007746, -0.000099133)),
                     (34.1833, (5.0538, -0.08861, 0.0021924, -0.000019396)),
                     (50.5108, (4.7553, -0.06241, 0.0014259, -0.000011922)),
                     (57.9775, (1.1584, 0.15122, -0.0028034, 0.000015988)),
                     (64.3942, (26.4612, -1.15805, 0.019779, -0.000113846))),
                 (-115.7858, 5.46896, -0.0831343, 0.000418879))


def correction_bolometrique(log_t: float) -> float:
    """BC (magnitudes) selon log₁₀ T (polynômes de l'original) ; M_bol = M_V + BC."""
    return _poly(log_t, ((3.588, (-1873.0763, 1364.8081, -328.11949, 25.958485)),
                         (3.6978, (-4208.8678, 3317.811, -872.43468, 76.5266)),
                         (3.7957, (-2920.8124, 2272.8215, -589.83737, 51.052264)),
                         (3.903, (1749.5431, -1418.5107, 382.67484, -34.353217)),
                         (4.1317, (-2011.2742, 1472.2021, -357.96384, 28.900577))),
                 (123.5421, -77.8864, 17.20884, -1.367489))


CLASSES = {1: (3.39, 4.65), 2: (3.39, 4.45), 3: (3.38, 4.3), 4: (3.38, 4.0), 5: (3.359, 4.701)}


def log_lum_classe(log_t: float, classe: int) -> float:
    """log₁₀ (L / L☉) de la classe de luminosité (1 = I … 5 = V, séquence principale) à la température donnée."""
    x = log_t
    if classe == 1:
        c = (44.8387, -30.1309, 7.59468, -0.636977) if x < 4.1476 else (-459.5864, 334.7205, -80.37116, 6.432557)
    elif classe == 2:
        c = (-36.2843, 39.6781, -12.545, 1.280459) if x < 4.0358 else (-37.0612, 40.2556, -12.68811, 1.292279)
    elif classe == 3:
        c = (-53.8721, 59.2071, -19.71611, 2.108195) if x < 3.9092 else (161.9073, -106.3856, 22.64341, -1.503738)
    elif classe == 4:
        c = (-167.256, 125.271, -31.96691, 2.804002) if x < 4.1372 else (54.567, -35.5787, 6.91186, -0.328444)
    else:
        return _poly(x, ((3.5081, (-4686.707, 4157.5332, -1232.05177, 121.875554)),
                         (3.5799, (22801.9307, -19349.4898, 5468.65774, -514.806626)),
                         (3.728, (-9950.2659, 8097.5483, -2198.40972, 199.100683)),
                         (3.8287, (10594.1896, -8435.0942, 2236.33537, -197.427256)),
                         (3.9156, (-7990.8168, 6127.2576, -1567.12652, 133.707956)),
                         (4.2129, (277.0365, -207.2491, 50.62412, -4.009536)),
                         (4.6015, (-280.446, 189.7309, -43.6049, 3.446011))),
                     (-9724.5727, 6346.9359, -1381.69136, 100.377185))
    return c[0] + x * (c[1] + x * (c[2] + x * c[3]))


def position_hr(type_num: float, mv: float) -> tuple[float, float]:
    """Point du diagramme HR (log T, log L/L☉) d'une étoile de type spectral et de magnitude absolue visuelle donnés."""
    lt = log_temp_de_type(type_num)
    return lt, log_lum_de_mbol(mv + correction_bolometrique(lt))


def couleur_rvb(temperature: float) -> tuple[int, int, int]:
    """Couleur d'affichage d'une étoile (polynômes de l'original, du rouge à 1 000 K au bleu à 40 000 K)."""
    t = max(1000.0, min(40000.0, temperature))
    lt = math.log10(t)
    r = 22686.34111 - lt * 15082.52755 + lt * lt * 3375.333832 - lt ** 3 * 252.4073853
    if t <= 6500:
        g = -811.6499145 + lt * 36.97365953 + lt * lt * 160.7861677 - lt ** 3 * 25.57573664
    else:
        g = 13836.23586 - lt * 9069.078214 + lt * lt * 2015.254756 - lt ** 3 * 149.7766966
    b = -11545.34298 + lt * 8529.658165 - lt * lt * 2150.198586 + lt ** 3 * 190.0306573
    return tuple(int(max(0, min(255, v))) for v in (r, g, b))
