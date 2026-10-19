"""Calculateur « Parallaxe (TP du cours) » : la démarche EXACTE du sujet officiel du DU (TP « Calcul de l'altitude de
l'ISS par mesure de parallaxe » et « Calcul de la distance Terre-Lune par mesure de parallaxe »), puis le calcul
exact, avec les nombres de l'utilisateur.

Démarche du sujet :
1. relever dans Stellarium les élévations h₁ et h₂ de l'objet vu des deux lieux, au même instant (TP de l'ISS ; le TP
   de la Lune mesure les distances angulaires Lune–étoile φ₁ et φ₂ : même calcul) ;
2. parallaxe 2α = h₁ − h₂ (en valeur absolue) ;
3. distance R entre les observateurs, « par exemple avec Google Earth » (distance à la SURFACE) ou mieux avec
   ``EarthLocation`` d'astropy (distance en ligne droite, la CORDE) ;
4. 2α = R / D (2α en radians), d'où D.

Ce que le calculateur ajoute :
* la corde R = |r₁ − r₂| entre les positions géocentriques WGS84 (``EarthLocation.from_geodetic`` d'astropy, « le
  modèle astropy du cours »), la distance à la surface (géodésique de l'ellipsoïde, méthode de Vincenty) et l'écart
  corde/surface ; la FLÈCHE (sagitta) : écart entre la corde et la surface au milieu de la corde (≈ R²/(8 R⊕)) ; la
  profondeur de la corde sous l'horizon de chaque lieu ;
* le calcul exact : les deux horizons ne sont pas parallèles (ils font l'angle θ, l'angle au centre de la Terre) ;
  avec les azimuts, triangulation des deux visées dans l'espace ; sans azimut, l'objet est supposé dans le plan
  vertical qui contient les deux lieux, entre eux (ISS) ou du même côté (Lune) ;
* avec l'heure : l'éphéméride (Lune : JPL DE440 si le fichier est là, sinon Meeus ; ISS : TLE de CelesTrak et SGP4),
  élévations prédites à comparer aux mesures ;
* les incertitudes propagées (élévations, positions, heure).
"""
from __future__ import annotations

import datetime as D
import math
from dataclasses import dataclass, field

import numpy as np

A_WGS84 = 6378.137                     # km
F_WGS84 = 1 / 298.257223563
R_TERRE_MOYEN = 6371.0088              # km (rayon moyen de l'UGGI, pour l'ordre de grandeur de la flèche)
UTC = D.timezone.utc


class ErreurTP(ValueError):
    def __init__(self, cle: str, **valeurs):
        super().__init__(cle)
        self.cle, self.valeurs = cle, valeurs


@dataclass
class Lieu:
    lat: float
    lon: float
    alt_m: float = 0.0
    h: float | None = None          # angle mesuré (élévation, ou distance Lune–étoile), degrés
    az: float | None = None         # azimut facultatif (nord 0°, est 90°)
    nom: str = ''


# ============================================================================================== géométrie terrestre
def ecef(lat: float, lon: float, alt_m: float = 0.0) -> np.ndarray:
    """Position géocentrique (km) : EarthLocation.from_geodetic d'astropy, ellipsoïde WGS84."""
    import astropy.units as u
    from astropy.coordinates import EarthLocation
    p = EarthLocation.from_geodetic(lon * u.deg, lat * u.deg, alt_m * u.m, ellipsoid='WGS84')
    return np.array([p.x.to_value(u.km), p.y.to_value(u.km), p.z.to_value(u.km)])


def geodetique(xyz) -> tuple[float, float, float]:
    """Position géocentrique (km) → (latitude °, longitude °, hauteur km) sur l'ellipsoïde WGS84 (astropy)."""
    import astropy.units as u
    from astropy.coordinates import EarthLocation
    p = EarthLocation.from_geocentric(*[float(c) for c in xyz], unit=u.km)
    g = p.to_geodetic('WGS84')
    return float(g.lat.deg), float(g.lon.deg), float(g.height.to_value(u.km))


def enu(lat: float, lon: float):
    la, lo = math.radians(lat), math.radians(lon)
    E = np.array([-math.sin(lo), math.cos(lo), 0.0])
    N = np.array([-math.sin(la) * math.cos(lo), -math.sin(la) * math.sin(lo), math.cos(la)])
    Z = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
    return E, N, Z


def direction(lat, lon, h, az) -> np.ndarray:
    E, N, Z = enu(lat, lon)
    h, a = math.radians(h), math.radians(az)
    return math.cos(h) * math.sin(a) * E + math.cos(h) * math.cos(a) * N + math.sin(h) * Z


def azimut_vers(o: Lieu, cible: np.ndarray) -> float:
    E, N, _ = enu(o.lat, o.lon)
    v = cible - ecef(o.lat, o.lon, o.alt_m)
    return math.degrees(math.atan2(v @ E, v @ N)) % 360.0


def geodesique_km(lat1, lon1, lat2, lon2) -> float:
    """Distance à la surface de l'ellipsoïde WGS84 (méthode inverse de Vincenty, 1975 ; à 0,5 mm près ; repli
    sphérique pour deux points presque antipodaux)."""
    a, f = A_WGS84, F_WGS84
    b = a * (1 - f)
    L = math.radians(lon2 - lon1)
    U1 = math.atan((1 - f) * math.tan(math.radians(lat1)))
    U2 = math.atan((1 - f) * math.tan(math.radians(lat2)))
    sU1, cU1, sU2, cU2 = math.sin(U1), math.cos(U1), math.sin(U2), math.cos(U2)
    lam = L
    for _ in range(200):
        sl, cl = math.sin(lam), math.cos(lam)
        ss = math.hypot(cU2 * sl, cU1 * sU2 - sU1 * cU2 * cl)
        if ss == 0:
            return 0.0
        cs = sU1 * sU2 + cU1 * cU2 * cl
        sig = math.atan2(ss, cs)
        sa = cU1 * cU2 * sl / ss
        c2a = 1 - sa * sa
        c2sm = cs - 2 * sU1 * sU2 / c2a if c2a else 0.0
        C = f / 16 * c2a * (4 + f * (4 - 3 * c2a))
        prec = lam
        lam = L + (1 - C) * f * sa * (sig + C * ss * (c2sm + C * cs * (-1 + 2 * c2sm * c2sm)))
        if abs(lam - prec) < 1e-13:
            break
    else:
        return R_TERRE_MOYEN * math.acos(max(-1, min(1, math.sin(math.radians(lat1)) * math.sin(math.radians(lat2))
                                                   + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
                                                   * math.cos(L))))
    u2 = c2a * (a * a - b * b) / (b * b)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    ds = B * ss * (c2sm + B / 4 * (cs * (-1 + 2 * c2sm * c2sm) - B / 6 * c2sm * (-3 + 4 * ss * ss)
                                   * (-3 + 4 * c2sm * c2sm)))
    return b * A * (sig - ds)


def geometrie_base(o1: Lieu, o2: Lieu) -> dict:
    """Corde, surface, flèche, angle au centre, profondeur de la corde sous chaque horizon."""
    r1, r2 = ecef(o1.lat, o1.lon, o1.alt_m), ecef(o2.lat, o2.lon, o2.alt_m)
    v = r2 - r1
    R = float(np.linalg.norm(v))
    s = geodesique_km(o1.lat, o1.lon, o2.lat, o2.lon)
    # flèche : milieu de la corde entre les deux points AU NIVEAU de l'ellipsoïde, sa profondeur sous la surface
    s1, s2 = ecef(o1.lat, o1.lon, 0.0), ecef(o2.lat, o2.lon, 0.0)
    fleche = -geodetique((s1 + s2) / 2)[2] if R > 0 else 0.0
    corde0 = float(np.linalg.norm(s2 - s1))
    prof = []
    for o, w in ((o1, v), (o2, -v)):
        _, _, Z = enu(o.lat, o.lon)
        prof.append(math.degrees(math.asin(max(-1.0, min(1.0, float(w @ Z) / R)))) if R > 0 else 0.0)
    _, _, Z1 = enu(o1.lat, o1.lon)
    _, _, Z2 = enu(o2.lat, o2.lon)
    theta = math.degrees(math.acos(max(-1.0, min(1.0, float(Z1 @ Z2)))))
    return {'corde_km': R, 'surface_km': s, 'ecart_corde_surface_km': s - R, 'fleche_km': fleche,
            'fleche_approchee_km': corde0 ** 2 / (8 * R_TERRE_MOYEN), 'corde_sol_km': corde0,
            'profondeur_deg': prof, 'angle_centre_deg': theta, 'r1': r1.tolist(), 'r2': r2.tolist(),
            'az_1_vers_2': azimut_vers(o1, r2), 'az_2_vers_1': azimut_vers(o2, r1)}


def inversion_probable(o1: Lieu, o2: Lieu) -> int | None:
    """Base énorme (> 3000 km) qui devient raisonnable (< 1500 km) si l'on échange latitude et longitude d'UN des
    deux lieux : rend 1 ou 2 (le lieu suspect), 0 si l'échange de l'un OU de l'autre convient (on ne peut pas dire
    lequel), sinon None.  Signalé, jamais corrigé d'office."""
    def base(a, b):
        return float(np.linalg.norm(ecef(a.lat, a.lon) - ecef(b.lat, b.lon)))
    if base(o1, o2) < 3000:
        return None
    ok = [k for k, (a, b) in enumerate(((o1, o2), (o2, o1)), 1)
          if abs(a.lon) <= 90 and base(Lieu(a.lon, a.lat), b) < 1500]
    return None if not ok else ok[0] if len(ok) == 1 else 0


# ============================================================================================== calculs
def calcul_sujet(R_km: float, h1: float, h2: float, entre: bool = False) -> dict:
    """La formule du sujet : 2α = |h₁ − h₂| (en radians), D = R / 2α.  Quand l'objet est ENTRE les deux lieux
    (chacun le voit du côté de l'autre), les deux visées se croisent au-dessus de la base : en Terre plate,
    2α = 180° − h₁ − h₂ (la différence du sujet vaut pour un objet vu du même côté par les deux)."""
    deux_alpha = (180.0 - h1 - h2) if entre else abs(h1 - h2)
    if deux_alpha <= 0:
        raise ErreurTP('td_err_parallaxe_nulle')
    rad = math.radians(deux_alpha)
    return {'deux_alpha_deg': deux_alpha, 'deux_alpha_rad': rad, 'alpha_deg': deux_alpha / 2, 'D_km': R_km / rad,
            'entre': entre}


def trianguler(O1, u1, O2, u2):
    u1, u2 = u1 / np.linalg.norm(u1), u2 / np.linalg.norm(u2)
    w, c = O2 - O1, float(u1 @ u2)
    d1, d2 = np.linalg.solve([[1.0, -c], [c, -1.0]], [w @ u1, w @ u2])
    P1, P2 = O1 + d1 * u1, O2 + d2 * u2
    return (P1 + P2) / 2, float(d1), float(d2), float(np.linalg.norm(P1 - P2))


def calcul_exact(o1: Lieu, o2: Lieu, configuration: str = 'entre') -> dict:
    """Triangulation exacte.  Avec les azimuts des deux lieux : visées dans l'espace.  Sans : l'objet est dans le
    plan vertical des deux lieux ; `configuration` 'entre' (chacun regarde vers l'autre lieu) ou 'meme_cote' (les
    deux regardent du même côté : l'objet est au-delà du lieu qui le voit le plus haut)."""
    if o1.h is None or o2.h is None:
        raise ErreurTP('td_err_hauteurs')
    g = geometrie_base(o1, o2)
    r1, r2 = np.array(g['r1']), np.array(g['r2'])
    avec_az = o1.az is not None and o2.az is not None
    if avec_az:
        az1, az2 = o1.az, o2.az
    elif configuration == 'entre':
        az1, az2 = g['az_1_vers_2'], g['az_2_vers_1']
    elif o1.h >= o2.h:                       # au-delà du lieu 1 : on regarde dans le sens 2 → 1
        az1, az2 = (g['az_1_vers_2'] + 180.0) % 360.0, g['az_2_vers_1']
    else:                                    # au-delà du lieu 2 : sens 1 → 2
        az1, az2 = g['az_1_vers_2'], (g['az_2_vers_1'] + 180.0) % 360.0
    u1, u2 = direction(o1.lat, o1.lon, o1.h, az1), direction(o2.lat, o2.lon, o2.h, az2)
    M, d1, d2, ecart = trianguler(r1, u1, r2, u2)
    if d1 <= 0 or d2 <= 0:
        raise ErreurTP('td_err_derriere')
    lat, lon, H = geodetique(M)
    p = math.degrees(math.acos(max(-1.0, min(1.0, float(u1 @ u2) / (np.linalg.norm(u1) * np.linalg.norm(u2))))))
    return {'avec_azimuts': avec_az, 'configuration': configuration if not avec_az else 'azimuts',
            'az_utilises': [az1, az2], 'distances_km': [d1, d2], 'distance_geo_km': float(np.linalg.norm(M)),
            'altitude_km': H, 'sous_point': [lat, lon], 'ecart_droites_km': ecart, 'parallaxe_vraie_deg': p,
            'M': M.tolist(), 'geometrie': g}


# ============================================================================================== éphémérides
def ephemeride_lune(o1: Lieu, o2: Lieu, t: D.datetime) -> dict:
    """Lune vue des deux lieux (module Partages : DE440 si le fichier est là, Meeus sinon) : distances
    topocentriques et géocentrique (géométriques), élévations prédites (sans réfraction, comme Stellarium sans
    atmosphère, et avec)."""
    from ..partages import astro
    ti = astro.Instant(t)
    geo, src = astro.lune_geocentrique(ti)
    out = {'source': src, 'distance_geo_km': float(np.linalg.norm(geo)), 'lieux': []}
    R = astro.c2t(ti)
    for o in (o1, o2):
        O = astro.observateur_gcrs(o.lat, o.lon, o.alt_m, ti)
        v, _ = astro.lune_astrometrique(ti, O)
        h, az = astro.altaz(o.lat, o.lon, R @ v)
        out['lieux'].append({'distance_km': float(np.linalg.norm(geo - O)), 'h_deg': h,
                             'h_refraction_deg': h + astro.refraction_vraie(h), 'az_deg': az})
    t2 = astro.Instant(t + D.timedelta(seconds=60))
    O = astro.observateur_gcrs(o1.lat, o1.lon, o1.alt_m, t2)
    v, _ = astro.lune_astrometrique(t2, O)
    out['vitesse_h_deg_s'] = (astro.altaz(o1.lat, o1.lon, astro.c2t(t2) @ v)[0] - out['lieux'][0]['h_deg']) / 60
    return out


def position_iss(tle: tuple, t: D.datetime) -> tuple[np.ndarray, float]:
    """Position terrestre (km) de l'ISS d'après un TLE (SGP4 ; TEME → terrestre par le temps sidéral GMST 1982) et
    âge du TLE (jours)."""
    from sgp4.api import Satrec, jday

    from ..partages import astro
    l1, l2 = [x for x in tle if x.strip().startswith(('1 ', '2 '))][:2]
    sat = Satrec.twoline2rv(l1, l2)
    jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)
    e, r, _ = sat.sgp4(jd, fr)
    if e != 0:
        raise ErreurTP('td_err_tle')
    import erfa
    ti = astro.Instant(t)
    th = erfa.gmst82(ti.ut11, ti.ut12)
    c, s = math.cos(th), math.sin(th)
    X = np.array([c * r[0] + s * r[1], -s * r[0] + c * r[1], r[2]])
    return X, (jd + fr) - (sat.jdsatepoch + sat.jdsatepochF)


def ephemeride_iss(o1: Lieu, o2: Lieu, t: D.datetime, tle: tuple) -> dict:
    X, age = position_iss(tle, t)
    lat, lon, H = geodetique(X)
    X2, _ = position_iss(tle, t + D.timedelta(seconds=1))
    out = {'source': 'tle', 'age_jours': age, 'altitude_km': H, 'sous_point': [lat, lon], 'lieux': []}
    for o in (o1, o2):
        O = ecef(o.lat, o.lon, o.alt_m)
        E, N, Z = enu(o.lat, o.lon)
        v = X - O
        d = float(np.linalg.norm(v))
        h = math.degrees(math.asin(float(v @ Z) / d))
        v2 = X2 - O
        h2 = math.degrees(math.asin(float(v2 @ Z) / float(np.linalg.norm(v2))))
        out['lieux'].append({'distance_km': d, 'h_deg': h, 'az_deg': math.degrees(math.atan2(v @ E, v @ N)) % 360,
                             'vitesse_h_deg_s': h2 - h})
    return out


# ============================================================================================== tout
@dataclass
class Entrees:
    o1: Lieu
    o2: Lieu
    cible: str = 'iss'                       # 'iss' | 'lune'
    instant: D.datetime | None = None
    tle: tuple | None = None
    configuration: str = ''                  # '' : d'après la cible (ISS : entre ; Lune : même côté)
    sigma_h_deg: float = 0.1
    sigma_pos_m: float = 20.0
    sigma_t_s: float = 1.0
    notes: list = field(default_factory=list)


def calculer(e: Entrees) -> dict:
    o1, o2 = e.o1, e.o2
    if o1.h is None or o2.h is None:
        raise ErreurTP('td_err_hauteurs')
    if o1.az is not None and o2.az is not None:       # azimuts donnés : « entre » si l'on regarde l'un vers l'autre
        conf = 'entre' if abs((o1.az - o2.az + 180.0) % 360.0 - 180.0) > 90 else 'meme_cote'
    else:
        conf = e.configuration or 'meme_cote'
    g = geometrie_base(o1, o2)
    if g['corde_km'] < 0.01:
        raise ErreurTP('td_err_meme_lieu')
    entre = conf == 'entre'
    res = {'cible': e.cible, 'configuration': conf, 'geometrie': g,
           'sujet_surface': calcul_sujet(g['surface_km'], o1.h, o2.h, entre),
           'sujet_corde': calcul_sujet(g['corde_km'], o1.h, o2.h, entre), 'alertes': list(e.notes)}
    if e.cible == 'lune' and (o1.az is None or o2.az is None):
        res['alertes'].append(('td_a_lune_azimuts', {}))
    k = inversion_probable(o1, o2)
    if k is not None:
        res['alertes'].append(('td_a_inversion_probable', {'n': k}) if k else ('td_a_inversion_un_des_deux', {}))
    try:
        res['exact'] = calcul_exact(o1, o2, conf)
    except (ErreurTP, np.linalg.LinAlgError) as ex:
        res['exact'] = None
        res['alertes'].append((getattr(ex, 'cle', 'td_err_derriere'), {}))
    if e.instant is not None:
        try:
            if e.cible == 'lune':
                res['ephemeride'] = ephemeride_lune(o1, o2, e.instant)
            elif e.tle:
                res['ephemeride'] = ephemeride_iss(o1, o2, e.instant, e.tle)
                if abs(res['ephemeride']['age_jours']) > 3:
                    res['alertes'].append(('td_a_tle_ancien', {'j': '%.1f' % res['ephemeride']['age_jours']}))
        except ErreurTP as ex:
            res['alertes'].append((ex.cle, {}))
        except ImportError:
            res['alertes'].append(('td_a_sans_sgp4', {}))
    res['incertitudes'] = incertitudes(e, res, conf)
    return res


def incertitudes(e: Entrees, res: dict, conf: str) -> dict:
    """σ sur D (sujet, corde) et sur la distance exacte : dérivées numériques par rapport à h₁, h₂ (σ_h), aux
    positions (σ_pos, en latitude et en longitude) et à l'heure (σ_t × vitesse de l'objet en élévation, d'après
    l'éphéméride si l'heure est donnée)."""
    o1, o2 = e.o1, e.o2
    D0 = res['sujet_corde']['D_km']
    ex0 = res['exact']['distances_km'][0] if res.get('exact') else None
    vit = 0.0
    eph = res.get('ephemeride')
    if eph:
        vit = abs(eph.get('vitesse_h_deg_s') or eph['lieux'][0].get('vitesse_h_deg_s') or 0.0)
    sig_h = math.hypot(e.sigma_h_deg, vit * e.sigma_t_s)
    contrib_s, contrib_e = [], []

    def refaire(a: Lieu, b: Lieu):
        g = geometrie_base(a, b)
        s = calcul_sujet(g['corde_km'], a.h, b.h, conf == 'entre')['D_km']
        try:
            x = calcul_exact(a, b, conf)['distances_km'][0]
        except (ErreurTP, np.linalg.LinAlgError):
            x = None
        return s, x
    dl = e.sigma_pos_m / 111_320.0
    for nom, a, b in (('h1', Lieu(o1.lat, o1.lon, o1.alt_m, o1.h + sig_h, o1.az), o2),
                      ('h2', o1, Lieu(o2.lat, o2.lon, o2.alt_m, o2.h + sig_h, o2.az)),
                      ('pos1', Lieu(o1.lat + dl, o1.lon + dl, o1.alt_m, o1.h, o1.az), o2),
                      ('pos2', o1, Lieu(o2.lat + dl, o2.lon + dl, o2.alt_m, o2.h, o2.az))):
        s, x = refaire(a, b)
        contrib_s.append((nom, abs(s - D0)))
        if ex0 is not None and x is not None:
            contrib_e.append((nom, abs(x - ex0)))
    return {'sigma_h_effectif_deg': sig_h, 'sujet': contrib_s, 'sujet_total_km': math.sqrt(sum(c[1] ** 2 for c in
                                                                                            contrib_s)),
            'exact': contrib_e, 'exact_total_km': math.sqrt(sum(c[1] ** 2 for c in contrib_e)) if contrib_e else None}


# ============================================================================================== exemple (fictif)
def exemple(cible: str = 'iss') -> dict:
    """Données FICTIVES cohérentes, pour découvrir le calculateur : deux grandes villes (coordonnées publiques),
    élévations et azimuts calculés pour une ISS fictive à 420 km d'altitude au-dessus de Lille, ou pour la Lune
    (skyfield + DE440, sans réfraction) le 3 novembre 2025 à 18 h 38 min 26 s TU."""
    if cible == 'lune':
        # positions exactes au centième de seconde : 12 m d'écart sur un lieu inclinent sa verticale de 0,4″, soit
        # 0,15 % de la parallaxe de la Lune (≈ 500 km sur la distance)
        return {'cible': 'lune', 'p1': '48°51′23,76″ N 2°21′07,92″ E', 'p2': '43°17′47,40″ N 5°22′11,28″ E',
                'alt1': '35',
                'alt2': '12', 'h1': '31,96731', 'h2': '36,41708', 'az1': '117,50126', 'az2': '116,88005',
                'instant': '2025-11-03 18:38:26'}
    return {'cible': 'iss', 'p1': '48.8566, 2.3522', 'p2': '45.7640, 4.8357', 'alt1': '35', 'alt2': '170',
            'h1': '62,483', 'h2': '33,603', 'az1': '14,184', 'az2': '346,928', 'instant': ''}
