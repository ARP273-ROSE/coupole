"""Calculs astronomiques des animations (sans Qt, sans dépendance lourde).

Formules : J. Meeus, *Astronomical Algorithms* (2e éd., 1998) pour le jour julien, le temps sidéral (IAU 1982),
la position du Soleil (précision ≈ 0,01°) et l'équation du temps ; P03 / IAU 2006 pour l'obliquité moyenne ;
trigonométrie sphérique classique pour les changements de repère.  Chaque fonction est vérifiée par
``outils/verif_anim/verif_anim.sage`` (SageMath, précision étendue) et par ``tests/test_anim_calculs.py``
(valeurs de référence figées dans ``tests/anim_reference_sage.json``, et comparaison à astropy).

Conventions : angles en degrés ; azimut compté depuis le nord vers l'est ; angle horaire H = TSL − α, positif vers
l'ouest ; « jour » d'une année = jours écoulés depuis le 1er janvier à 0 h (temps universel = temps solaire moyen
sur le méridien de Greenwich).
"""
from __future__ import annotations

import functools
import math

DEG = math.pi / 180.0
RAD = 180.0 / math.pi

# ---------------------------------------------------------------- constantes (sources dans le manuel)
UA_KM = 149_597_870.700                 # unité astronomique (IAU 2012, exacte)
AL_M = 9_460_730_472_580_800.0           # année-lumière (IAU, exacte)
PC_M = UA_KM * 1000.0 * 648_000.0 / math.pi   # parsec (IAU 2015 B2)
PC_EN_AL = PC_M / AL_M                   # 3,261 563 777…
R_SOLEIL_KM = 695_700.0                  # rayon solaire nominal (IAU 2015 B3)
R_TERRE_KM = 6_378.137                   # rayon équatorial terrestre
R_LUNE_KM = 1_737.4                      # rayon moyen de la Lune
D_LUNE_KM = 384_400.0                    # distance moyenne Terre-Lune
MOIS_SYNODIQUE_J = 29.530_588_861        # lunaison moyenne (Meeus, éq. 49.1)
ANNEE_TROPIQUE_J = 365.242_19            # année tropique moyenne
ANNEE_JULIENNE_J = 365.25
GM_SOLEIL = 1.327_124_400_18e20          # m³ s⁻² (IAU 2009/2012)
ZODIAQUE_NOMS = ('psc', 'ari', 'tau', 'gem', 'cnc', 'leo', 'vir', 'lib', 'sco', 'oph', 'sgr', 'cap', 'aqr')


def mod(x: float, m: float) -> float:
    r = math.fmod(x, m)
    return r + m if r < 0 else r


def mod180(x: float) -> float:
    """Ramène un angle dans ]-180, 180]."""
    r = mod(x, 360.0)
    return r - 360.0 if r > 180.0 else r


# ---------------------------------------------------------------- temps
def jour_julien(annee: int, mois: int, jour: float, heure: float = 0.0) -> float:
    """Jour julien d'une date du calendrier grégorien (Meeus, chap. 7)."""
    if mois <= 2:
        annee -= 1
        mois += 12
    a = annee // 100
    b = 2 - a + a // 4
    return int(365.25 * (annee + 4716)) + int(30.6001 * (mois + 1)) + jour + heure / 24.0 + b - 1524.5


def jj_jour_de_l_annee(annee: int, jour: float) -> float:
    """Jour julien du « jour » `jour` de l'année (0 = 1er janvier à 0 h TU)."""
    return jour_julien(annee, 1, 1.0) + jour


def siecles_j2000(jj: float) -> float:
    return (jj - 2_451_545.0) / 36_525.0


def tsmg(jj: float) -> float:
    """Temps sidéral moyen de Greenwich, en degrés (IAU 1982, Meeus éq. 12.4) ; jj en TU."""
    t = siecles_j2000(jj)
    return mod(280.460_618_37 + 360.985_647_366_29 * (jj - 2_451_545.0) + 0.000_387_933 * t * t
               - t ** 3 / 38_710_000.0, 360.0)


def jour_sideral_s(annee_jours: float = ANNEE_TROPIQUE_J) -> float:
    """Durée du jour sidéral (en secondes de temps solaire moyen) quand l'année compte `annee_jours` jours
    solaires : la Terre fait un tour de plus par rapport aux étoiles qu'au Soleil chaque année."""
    return 86_400.0 * annee_jours / (annee_jours + 1.0)


# ---------------------------------------------------------------- obliquité, Soleil
def obliquite_moyenne(jj: float = 2_451_545.0) -> float:
    """Obliquité moyenne de l'écliptique (P03, IAU 2006), en degrés."""
    t = siecles_j2000(jj)
    s = (84_381.406 - 46.836_769 * t - 0.000_183_1 * t ** 2 + 0.002_003_40 * t ** 3
         - 5.76e-7 * t ** 4 - 4.34e-8 * t ** 5)
    return s / 3600.0


def soleil(jj: float) -> dict:
    """Position apparente du Soleil (Meeus, chap. 25, précision ≈ 0,01°) et équation du temps.

    Rend {'lambda', 'alpha', 'delta' (degrés), 'distance' (ua), 'eqt' (minutes : temps solaire vrai − temps
    solaire moyen), 'L0', 'M'}."""
    t = siecles_j2000(jj)
    l0 = mod(280.466_46 + 36_000.769_83 * t + 0.000_303_2 * t * t, 360.0)
    m = mod(357.529_11 + 35_999.050_29 * t - 0.000_153_7 * t * t, 360.0)
    e = 0.016_708_634 - 0.000_042_037 * t - 0.000_000_126_7 * t * t
    mr = m * DEG
    c = ((1.914_602 - 0.004_817 * t - 0.000_014 * t * t) * math.sin(mr)
         + (0.019_993 - 0.000_101 * t) * math.sin(2 * mr) + 0.000_289 * math.sin(3 * mr))
    vraie = l0 + c
    nu = m + c
    r = 1.000_001_018 * (1 - e * e) / (1 + e * math.cos(nu * DEG))
    omega = 125.04 - 1_934.136 * t
    lam = vraie - 0.005_69 - 0.004_78 * math.sin(omega * DEG)
    eps = obliquite_moyenne(jj) + 0.002_56 * math.cos(omega * DEG)
    alpha = mod(math.atan2(math.cos(eps * DEG) * math.sin(lam * DEG), math.cos(lam * DEG)) * RAD, 360.0)
    delta = math.asin(math.sin(eps * DEG) * math.sin(lam * DEG)) * RAD
    dpsi = -0.004_78 * math.sin(omega * DEG)                  # nutation en longitude (approchée), degrés
    eqt = mod180(l0 - 0.005_718_3 - alpha + dpsi * math.cos(eps * DEG)) * 4.0     # 1° = 4 min
    return {'lambda': mod(lam, 360.0), 'alpha': alpha, 'delta': delta, 'distance': r, 'eqt': eqt, 'L0': l0, 'M': m}


def soleil_jour(annee: int, jour: float) -> dict:
    return soleil(jj_jour_de_l_annee(annee, jour))


# ---------------------------------------------------------------- repères
def ecliptique_vers_equatorial(lam: float, beta: float, eps: float) -> tuple[float, float]:
    """(λ, β) → (α, δ), degrés."""
    l, b, e = lam * DEG, beta * DEG, eps * DEG
    sd = math.sin(b) * math.cos(e) + math.cos(b) * math.sin(e) * math.sin(l)
    a = math.atan2(math.sin(l) * math.cos(e) - math.tan(b) * math.sin(e), math.cos(l))
    return mod(a * RAD, 360.0), math.asin(max(-1.0, min(1.0, sd))) * RAD


def equatorial_vers_horizon(h: float, dec: float, lat: float) -> tuple[float, float]:
    """(angle horaire H, déclinaison δ, latitude φ) → (azimut depuis le nord vers l'est, hauteur), degrés."""
    hr, d, p = h * DEG, dec * DEG, lat * DEG
    sh = math.sin(p) * math.sin(d) + math.cos(p) * math.cos(d) * math.cos(hr)
    az = math.atan2(-math.cos(d) * math.sin(hr), math.sin(d) * math.cos(p) - math.cos(d) * math.cos(hr) * math.sin(p))
    return mod(az * RAD, 360.0), math.asin(max(-1.0, min(1.0, sh))) * RAD


def horizon_vers_equatorial(az: float, alt: float, lat: float) -> tuple[float, float]:
    """(azimut, hauteur, latitude) → (angle horaire H, déclinaison), degrés."""
    a, h, p = az * DEG, alt * DEG, lat * DEG
    sd = math.sin(p) * math.sin(h) + math.cos(p) * math.cos(h) * math.cos(a)
    ha = math.atan2(-math.cos(h) * math.sin(a), math.sin(h) * math.cos(p) - math.cos(h) * math.cos(a) * math.sin(p))
    return mod(ha * RAD, 360.0), math.asin(max(-1.0, min(1.0, sd))) * RAD


def angle_horaire_lever(dec: float, lat: float, h0: float = 0.0):
    """Demi-arc diurne H₀ (degrés) d'un astre de déclinaison δ vu à la latitude φ, pour la hauteur h₀ du lever.

    Rend 180 si l'astre ne se couche pas (circumpolaire), 0 s'il ne se lève pas."""
    p, d = lat * DEG, dec * DEG
    den = math.cos(p) * math.cos(d)
    if abs(den) < 1e-12:
        return 180.0 if math.sin(p) * math.sin(d) > math.sin(h0 * DEG) else 0.0
    c = (math.sin(h0 * DEG) - math.sin(p) * math.sin(d)) / den
    if c <= -1.0:
        return 180.0
    if c >= 1.0:
        return 0.0
    return math.acos(c) * RAD


def duree_du_jour_h(dec: float, lat: float, h0: float = 0.0) -> float:
    """Durée pendant laquelle l'astre est au-dessus de h₀, en heures sidérales ≈ solaires (2 H₀ / 15)."""
    return 2.0 * angle_horaire_lever(dec, lat, h0) / 15.0


def azimut_lever(dec: float, lat: float, h0: float = 0.0):
    """Azimut du lever (degrés depuis le nord vers l'est), ou None si l'astre ne se lève ni ne se couche."""
    h = angle_horaire_lever(dec, lat, h0)
    if h <= 0.0 or h >= 180.0:
        return None
    return equatorial_vers_horizon(-h, dec, lat)[0]


def hauteur_culmination(dec: float, lat: float) -> float:
    """Hauteur au passage au méridien supérieur : 90° − |φ − δ|."""
    return 90.0 - abs(lat - dec)


def plages_declinaison(lat: float) -> dict:
    """Déclinaisons circumpolaires, qui se lèvent et se couchent, jamais levées (horizon géométrique).

    Rend {'circumpolaire': (dmin, dmax) | None, 'lever_coucher': (dmin, dmax) | None, 'jamais': (dmin, dmax) | None},
    bornes en degrés (intervalles ouverts aux limites ; δ = ±(90° − |φ|))."""
    c = 90.0 - abs(lat)
    if abs(lat) < 1e-9:
        return {'circumpolaire': None, 'lever_coucher': (-90.0, 90.0), 'jamais': None}
    if c < 1e-9:
        nord = lat > 0
        return {'circumpolaire': (0.0, 90.0) if nord else (-90.0, 0.0), 'lever_coucher': None,
                'jamais': (-90.0, 0.0) if nord else (0.0, 90.0)}
    if lat > 0:
        return {'circumpolaire': (c, 90.0), 'lever_coucher': (-c, c), 'jamais': (-90.0, -c)}
    return {'circumpolaire': (-90.0, -c), 'lever_coucher': (-c, c), 'jamais': (c, 90.0)}


# ---------------------------------------------------------------- vecteurs (dessin 3D)
def vecteur_horizon(az: float, alt: float) -> tuple[float, float, float]:
    """Repère local direct (x = nord, y = ouest, z = zénith)."""
    a, h = az * DEG, alt * DEG
    return (math.cos(h) * math.cos(a), -math.cos(h) * math.sin(a), math.sin(h))


def vecteur_equatorial(ra_deg: float, dec: float) -> tuple[float, float, float]:
    """Repère équatorial direct (x = point vernal, y = α 6 h, z = pôle nord céleste)."""
    a, d = ra_deg * DEG, dec * DEG
    return (math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d))


def matrice_equatorial_vers_horizon(tsl_deg: float, lat: float):
    """Matrice 3×3 (liste de lignes) qui envoie un vecteur équatorial dans le repère local (nord, ouest, zénith)."""
    t, p = tsl_deg * DEG, lat * DEG
    # vecteur (α, δ) → (cos δ cos H, −cos δ sin H, sin δ) avec H = t − α, puis base (méridien sud, est, pôle)
    ct, st = math.cos(t), math.sin(t)
    # colonnes de la rotation d'angle −t autour du pôle, composée avec l'inclinaison du pôle
    x0 = (-math.sin(p), 0.0, math.cos(p))        # point de l'équateur au méridien (H = 0)
    e = (0.0, -1.0, 0.0)                          # point est de l'horizon (H = −6 h), y = ouest
    pole = (math.cos(p), 0.0, math.sin(p))
    # u = (cos δ cos α, cos δ sin α, sin δ) ; cos H = ct cos α + st sin α ; −sin H = −st cos α + ct sin α
    m = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        m[i][0] = x0[i] * ct - e[i] * st
        m[i][1] = x0[i] * st + e[i] * ct
        m[i][2] = pole[i]
    return m


def appliquer(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


# ---------------------------------------------------------------- Kepler
def resoudre_kepler(m_rad: float, e: float) -> float:
    """Anomalie excentrique E (radians) telle que E − e sin E = M (Newton, départ de Danby)."""
    m = math.fmod(m_rad, 2 * math.pi)
    ee = m + 0.85 * e * (1 if math.sin(m) >= 0 else -1)
    for _ in range(50):
        f = ee - e * math.sin(ee) - m
        d = f / (1 - e * math.cos(ee))
        ee -= d
        if abs(d) < 1e-15:
            break
    return ee


def periode_annees(a_ua: float, masse_soleils: float = 1.0) -> float:
    """3e loi de Kepler en unités solaires : P² = a³ / M (P en années, a en ua)."""
    return math.sqrt(a_ua ** 3 / masse_soleils)


def orbite(a_ua: float, e: float, fraction: float) -> dict:
    """Position sur l'orbite à la fraction `fraction` de période après le périhélie (foyer = Soleil à l'origine,
    périhélie sur +x).  Rend x, y (ua), r (ua), anomalies vraie et excentrique (degrés), vitesse (km/s, vis-viva)."""
    m = 2 * math.pi * (fraction % 1.0)
    ee = resoudre_kepler(m, e)
    x = a_ua * (math.cos(ee) - e)
    y = a_ua * math.sqrt(1 - e * e) * math.sin(ee)
    r = math.hypot(x, y)
    nu = mod(math.atan2(y, x) * RAD, 360.0)
    v = math.sqrt(GM_SOLEIL * (2.0 / (r * UA_KM * 1000.0) - 1.0 / (a_ua * UA_KM * 1000.0))) / 1000.0
    return {'x': x, 'y': y, 'r': r, 'nu': nu, 'E': mod(ee * RAD, 360.0), 'v': v}


def aire_balayee(a_ua: float, e: float, f0: float, f1: float) -> float:
    """Aire balayée par le rayon vecteur entre deux fractions de période (ua²) : π a b (f1 − f0) (2e loi)."""
    return math.pi * a_ua * a_ua * math.sqrt(1 - e * e) * (f1 - f0)


# ---------------------------------------------------------------- distances stellaires
def parsecs_de_parallaxe(p_arcsec: float) -> float:
    return 1.0 / p_arcsec


def module_de_distance(d_pc: float) -> float:
    """m − M = 5 log₁₀(d / 10 pc)."""
    return 5.0 * math.log10(d_pc) - 5.0


def distance_du_module(mu: float) -> float:
    return 10.0 ** ((mu + 5.0) / 5.0)


# ---------------------------------------------------------------- ombres et éclipses
def cones_ombre(r_source: float, r_objet: float, distance: float) -> dict:
    """Ombre et pénombre d'un corps sphérique éclairé par une source sphérique (mêmes unités de longueur).

    Rend la longueur du cône d'ombre (du centre de l'objet au sommet), les demi-angles des cônes (degrés) et
    deux fonctions rayon(x) de l'ombre et de la pénombre à la distance x derrière l'objet."""
    k_u = (r_source - r_objet) / distance
    k_p = (r_source + r_objet) / distance
    return {'longueur_ombre': r_objet / k_u if k_u > 0 else math.inf,
            'demi_angle_ombre': math.asin(min(1.0, k_u)) * RAD,
            'demi_angle_penombre': math.asin(min(1.0, k_p)) * RAD,
            'rayon_ombre': lambda x: r_objet - x * k_u,
            'rayon_penombre': lambda x: r_objet + x * k_p}


def eclipse_de_lune(d_lune_km: float = D_LUNE_KM, d_soleil_km: float = UA_KM, r_terre: float = R_TERRE_KM,
                    r_lune: float = R_LUNE_KM, r_soleil: float = R_SOLEIL_KM,
                    mois_j: float = MOIS_SYNODIQUE_J) -> dict:
    """Géométrie d'une éclipse centrale de Lune (méthode d'Aristarque) : rayons de l'ombre et de la pénombre à la
    distance de la Lune, rapport au diamètre lunaire, durées de la totalité et de la phase partielle (heures),
    la Lune traversant l'ombre à sa vitesse synodique 2π d / lunaison."""
    c = cones_ombre(r_soleil, r_terre, d_soleil_km)
    ru, rp = c['rayon_ombre'](d_lune_km), c['rayon_penombre'](d_lune_km)
    v = 2 * math.pi * d_lune_km / (mois_j * 24.0)             # km/h, mouvement relatif à la direction du Soleil
    return {'rayon_ombre_km': ru, 'rayon_penombre_km': rp, 'ombre_en_diametres_lunaires': ru / r_lune,
            'longueur_ombre_km': c['longueur_ombre'], 'vitesse_kmh': v,
            'totalite_h': max(0.0, 2 * (ru - r_lune) / v), 'ombre_totale_h': 2 * (ru + r_lune) / v,
            'penombre_h': 2 * (rp + r_lune) / v}


# ---------------------------------------------------------------- Lune
def fraction_eclairee(elongation: float) -> float:
    """Fraction éclairée du disque lunaire pour l'angle de phase compté depuis la nouvelle lune (0 → 0, 180 → 1)."""
    return (1.0 - math.cos(elongation * DEG)) / 2.0


def nom_de_phase(angle: float, tol_quartier: float = 5.0, tol_lune: float = 12.0) -> str:
    """Nom de la phase (mêmes tolérances que le simulateur d'origine : ±12° autour des nouvelle et pleine lunes,
    ±5° autour des quartiers).  Rend une clé : nl, pc, pq, gc, pl, gd, dq, dc."""
    a = mod(angle, 360.0)
    for borne, cle in ((tol_lune, 'nl'), (90 - tol_quartier, 'pc'), (90 + tol_quartier, 'pq'),
                       (180 - tol_lune, 'gc'), (180 + tol_lune, 'pl'), (270 - tol_quartier, 'gd'),
                       (270 + tol_quartier, 'dq'), (360 - tol_lune, 'dc')):
        if a <= borne:
            return cle
    return 'nl'


# ---------------------------------------------------------------- modèles planétaires
def position_circulaire(a: float, periode: float, t: float, phase0_deg: float = 0.0) -> tuple[float, float]:
    th = phase0_deg * DEG + 2 * math.pi * t / periode
    return a * math.cos(th), a * math.sin(th)


def longitude_geocentrique(a_planete: float, t_annees: float, phase_planete: float = 0.0,
                           phase_terre: float = 0.0) -> float:
    """Longitude écliptique géocentrique d'une planète sur orbite circulaire coplanaire (Terre : a = 1 ua,
    période 1 an ; planète : période a^1,5), degrés."""
    xp, yp = position_circulaire(a_planete, periode_annees(a_planete), t_annees, phase_planete)
    xt, yt = position_circulaire(1.0, 1.0, t_annees, phase_terre)
    return mod(math.atan2(yp - yt, xp - xt) * RAD, 360.0)


@functools.lru_cache(maxsize=32)
def retrogradation(a_planete: float) -> dict:
    """Mouvement rétrograde d'une planète supérieure (orbites circulaires coplanaires) autour de l'opposition :
    durée (jours de 365,25 j) et amplitude (degrés) de la boucle, entre les deux stations (dλ/dt = 0), cherchées
    par dichotomie sur dλ/dt entre l'opposition (t = 0) et la conjonction suivante."""
    p = periode_annees(a_planete)
    w = 2 * math.pi * (1 - 1 / p)           # vitesse angulaire relative (rad/an)

    def dlam(t):
        h = 1e-6
        return mod180(longitude_geocentrique(a_planete, t + h) - longitude_geocentrique(a_planete, t - h)) / (2 * h)

    lo, hi = 0.0, 0.5 * (2 * math.pi / w)    # de l'opposition à la conjonction
    if dlam(lo) >= 0:
        return {'duree_j': 0.0, 'amplitude': 0.0}
    for _ in range(80):
        mid = (lo + hi) / 2
        if dlam(mid) < 0:
            lo = mid
        else:
            hi = mid
    ts = (lo + hi) / 2
    amp = 2 * abs(mod180(longitude_geocentrique(a_planete, ts) - longitude_geocentrique(a_planete, 0.0)))
    return {'duree_j': 2 * ts * ANNEE_JULIENNE_J, 'amplitude': amp, 'demi_duree_annees': ts}


# Modèle de Ptolémée pour Mars (valeurs de l'Almageste reprises du simulateur d'origine : rayon du déférent 60,
# excentricité 6, épicycle 39,5 ; apogée 106,67° ; période 1,881 an ; époque κ₀ = 3,53°, α₀ = 327,22°)
PTOLEMEE_MARS = {'R': 60.0, 'e': 6.0, 'r': 39.5, 'apogee': 106.67, 'kappa0': 3.53, 'alpha0': 327.22,
                 'periode': 1.881}
PTOLEMEE_SOLEIL = {'R': 60.0, 'e': 2.5, 'apogee': 65.5, 'kappa0': 265.25}


def ptolemee_mars(t_annees: float, p: dict = PTOLEMEE_MARS) -> dict:
    """Positions (repère du déférent tourné de l'apogée ; Terre à l'origine, centre du déférent en (e, 0),
    point équant en (2e, 0)) du centre de l'épicycle et de Mars.  Le centre de l'épicycle tourne uniformément
    vu de l'équant ; Mars parcourt l'épicycle en un an."""
    kappa = (p['kappa0'] - p['apogee']) * DEG + 2 * math.pi * t_annees / p['periode']
    gamma = (p['alpha0'] + p['kappa0'] - p['apogee']) * DEG + 2 * math.pi * t_annees
    e, rd = p['e'], p['R']
    m = -e * math.cos(kappa) + math.sqrt(rd * rd - e * e * math.sin(kappa) ** 2)
    cx, cy = 2 * e + m * math.cos(kappa), m * math.sin(kappa)
    mx, my = cx + p['r'] * math.cos(gamma), cy + p['r'] * math.sin(gamma)
    return {'centre': (cx, cy), 'mars': (mx, my), 'equant': (2 * e, 0.0), 'deferent': (e, 0.0),
            'kappa': mod(kappa * RAD, 360.0), 'longitude': mod(math.atan2(my, mx) * RAD + p['apogee'], 360.0)}


def ptolemee_soleil(t_annees: float, p: dict = PTOLEMEE_SOLEIL) -> tuple[float, float]:
    k = p['kappa0'] * DEG + 2 * math.pi * t_annees
    return p['e'] + p['R'] * math.cos(k), p['R'] * math.sin(k)


def epicycles(t: float, r_interieur: float = 85.0, r_exterieur: float = 200.0, centre: int = 1) -> dict:
    """Démonstration des épicycles : trois corps (1 jaune au centre, 2 bleu, 3 rouge en orbite circulaire, périodes
    selon la 3e loi), positions vues depuis le corps `centre` (1, 2 ou 3).  t en périodes du corps 2."""
    p3 = (r_exterieur / r_interieur) ** 1.5
    b = (r_interieur * math.cos(2 * math.pi * t), r_interieur * math.sin(2 * math.pi * t))
    c = (r_exterieur * math.cos(2 * math.pi * t / p3), r_exterieur * math.sin(2 * math.pi * t / p3))
    corps = {1: (0.0, 0.0), 2: b, 3: c}
    o = corps[centre]
    return {k: (v[0] - o[0], v[1] - o[1]) for k, v in corps.items()} | {'periode3': p3}


# ---------------------------------------------------------------- zodiaque
# Longitudes écliptiques (équinoxe et écliptique de 2026,0) où le Soleil franchit les limites officielles des
# constellations (UAI 1930, Delporte ; données de N. G. Roman 1987 livrées avec astropy) : calculées une fois par
# outils/verif_anim/limites_zodiaque.py, vérifiées par tests/test_anim_calculs.py.
LIMITES_ZODIAQUE_2026 = (('ari', 29.050), ('tau', 53.779), ('gem', 90.503), ('cnc', 118.351), ('leo', 138.402),
                         ('vir', 174.214), ('lib', 218.172), ('sco', 241.424), ('oph', 248.001), ('sgr', 266.601),
                         ('cap', 300.020), ('aqr', 327.852), ('psc', 352.013))


def constellation_du_soleil(lam: float, limites=None):
    """Clé de la constellation (psc, ari, … oph …) devant laquelle se trouve un point de l'écliptique."""
    lim = limites or LIMITES_ZODIAQUE_2026
    lam = mod(lam, 360.0)
    debut = sorted(lim, key=lambda x: x[1])
    nom = debut[-1][0]
    for cle, l0 in debut:
        if lam >= l0:
            nom = cle
    return nom
