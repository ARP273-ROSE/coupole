"""Parallaxe à deux observateurs (Lune : distance ; ISS : altitude) et méthodes à un seul observateur.

Physique reprise du guide « Parallaxe de l'ISS » du DU (script ``parallaxe_iss.py``, skyfield) et des exemples
chiffrés des défis de la séance 2 ; mêmes formules, mêmes résultats (essais : exemple du guide, 429,1 km), mais la
rotation de la Terre et l'ellipsoïde viennent d'ERFA (``partages/astro.py``) au lieu de skyfield.

Lune — **méthode vectorielle topocentrique** : chaque observateur donne la direction (α, δ) du centre de la Lune,
lue sur la solution astrométrique de sa photo (repère des étoiles, ICRS).  Les positions des deux observateurs
(WGS84) sont ramenées dans le même repère (GCRS) ; le point le plus proche des deux droites est le centre de la
Lune.  Les directions d'une photo sont « astrométriques » (la Lune où elle était il y a ~1,2 s, vue de la Terre qui a
bougé depuis) : elles sont ramenées aux directions géométriques avant la triangulation (le temps de lumière n'est
pas le même pour les deux observateurs ; sans cette correction, ~20 km d'erreur).  Distance géocentrique,
distances topocentriques (géométriques), parallaxe, base projetée et budget d'erreur ; comparaison à l'éphéméride
(DE440 si présente, Meeus sinon) : distances géométriques, directions astrométriques comme les photos.  Si les deux photos ne sont pas prises au même instant,
chaque direction est ramenée à l'instant commun par le mouvement apparent de la Lune (petite correction, dite).
Hauteur et azimut au lieu de (α, δ) : acceptés (réfraction retirée s'ils sont mesurés sur le ciel réel).

ISS — **triangulation des deux visées** : chaque observateur donne une « trace » (extrémités datées d'un trait, ou
positions datées d'une série de poses) ; les directions sont passées dans le repère terrestre à leur propre instant
(rotation de la Terre comprise), interpolées le long de chaque trace à l'instant commun (milieu du recouvrement),
puis triangulées.  Le décalage d'horloge entre les deux observateurs se corrige le long du trait : on peut le
donner, ou le laisser estimer (le décalage qui rend les deux droites concourantes).  Contrôle sans horloge commune
(méthode des plans) ; comparaison à la prédiction d'un TLE (paquet sgp4 facultatif).
"""
from __future__ import annotations

import datetime as D
import math
from dataclasses import dataclass, field

import numpy as np

from ... import astro
from ...astro import Instant, unitaire

GM = 398600.4418           # km³/s² (WGS84)
OMEGA_T = 7.292115e-5      # rad/s
AS = 180.0 / math.pi * 3600.0


class ErreurCalcul(ValueError):
    def __init__(self, cle: str, **valeurs):
        super().__init__(cle)
        self.cle, self.valeurs = cle, valeurs


# ============================================================================================== entrées
@dataclass
class Point:
    """Une direction datée : (α, δ) ICRS en degrés, OU (h, az) en degrés (azimut du nord vers l'est)."""
    instant: D.datetime
    ra: float | None = None
    dec: float | None = None
    h: float | None = None
    az: float | None = None


@dataclass
class Visee:
    """Ce qu'un observateur a mesuré.  `points` : 1 point (Lune, ou ISS au même instant), 2 points (extrémités d'un
    trait : début et fin de pose), ou plus (série datée)."""
    nom: str
    lat: float
    lon: float
    alt_m: float = 0.0
    points: list = field(default_factory=list)
    refraction: str = 'sans'       # 'sans' (α, δ ou Stellarium sans atmosphère) | 'mesuree' (h mesurée : à retirer)
    sigma_arcsec: float = 30.0     # incertitude d'une direction (centrage, astrométrie)
    sigma_t: float = 0.5           # incertitude de l'heure (s)
    sigma_pos_m: float = 30.0      # incertitude de la position (m)
    decalage_horloge: float = 0.0  # secondes à AJOUTER aux heures de cet observateur (horloge connue en retard)
    source: str = ''

    def instants(self) -> list[D.datetime]:
        return [p.instant + D.timedelta(seconds=self.decalage_horloge) for p in self.points]


def _direction_itrs(v: Visee, p: Point, t: Instant) -> np.ndarray:
    """Direction observateur → objet dans le repère terrestre à l'instant t (comme direction_terrestre du guide)."""
    if p.ra is not None and p.dec is not None:
        return astro.c2t(t) @ astro.vecteur_radec(p.ra, p.dec)
    if p.h is None or p.az is None:
        raise ErreurCalcul('pc_err_point_vide', nom=v.nom)
    h = p.h - (astro.refraction_bennett(p.h) if v.refraction == 'mesuree' else 0.0)
    return astro.vecteur_altaz(v.lat, v.lon, h, p.az)


# ============================================================================================== Lune
def distance_lune(v1: Visee, v2: Visee, etoile: tuple | None = None, forcer_ephemeride: str = '') -> dict:
    """Distance de la Lune par deux visées simultanées (ou presque) du centre de la Lune.  Rend un dictionnaire de
    résultats (km, secondes d'arc, …) avec le budget d'erreur et la comparaison à l'éphéméride."""
    for v in (v1, v2):
        if not v.points:
            raise ErreurCalcul('pc_err_point_vide', nom=v.nom)
    t1 = Instant(v1.instants()[0])
    t2 = Instant(v2.instants()[0])
    tc = Instant(t1.dt + (t2.dt - t1.dt) / 2)
    res = _lune_noyau(v1, v2, t1, t2, tc, forcer_ephemeride)
    res['budget'] = _budget_lune(v1, v2, res, forcer_ephemeride)
    sig = math.sqrt(sum(x[1] ** 2 for x in res['budget']))
    res['sigma_km'] = sig
    res['sigma_rel'] = sig / res['distance_geo_km']
    if etoile is not None:
        res['methode_sujet'] = _methode_sujet(res, etoile)
    return res


def _lune_noyau(v1, v2, t1, t2, tc, forcer, perturb=None) -> dict:
    perturb = perturb or {}
    R = astro.c2t(tc)
    O = []
    U = []
    decal = []
    src = ''
    for k, (v, t) in enumerate(((v1, t1), (v2, t2))):
        lat = v.lat + perturb.get(('lat', k), 0.0)
        lon = v.lon + perturb.get(('lon', k), 0.0)
        Oi_tc = R.T @ astro.ecef(lat, lon, v.alt_m)
        Ot = astro.c2t(t).T @ astro.ecef(lat, lon, v.alt_m)
        u = astro.c2t(t).T @ _direction_itrs(v, v.points[0], t) if v.points[0].ra is None else \
            astro.vecteur_radec(v.points[0].ra, v.points[0].dec)
        if ('dir', k) in perturb:
            u = unitaire(u + perturb[('dir', k)])
        # ramener la direction à l'instant commun par le mouvement apparent prédit (petite correction)
        dt = tc - t + perturb.get(('t', k), 0.0)
        if abs(dt) > 1e-3:
            a, src = astro.lune_astrometrique(t, Ot, forcer)
            b, src = astro.lune_astrometrique(t.plus(dt), astro.c2t(t.plus(dt)).T @ astro.ecef(lat, lon, v.alt_m),
                                              forcer)
            du = unitaire(b) - unitaire(a)
            u = unitaire(u + du)
            decal.append(float(np.linalg.norm(du)) * AS)
        else:
            decal.append(0.0)
        O.append(Oi_tc)
        U.append(unitaire(u))
    # Directions ASTROMÉTRIQUES (photo calée sur les étoiles) → GÉOMÉTRIQUES à l'instant commun : chaque observateur
    # voit la Lune où elle était il y a τ = d/c ≈ 1,2 s, décalée de −(v_Terre + v_Lune) τ ; les deux τ diffèrent de
    # ~1 ms (≈ 40 m de décalage relatif, soit ~20 km d'erreur sur la distance pour une base de 600 km).  Le point vu à
    # la distance d sur la visée u est donc O + d (u + w/c) pour le point géométrique : on triangule avec ces visées.
    w = _vitesse_relative_lune(tc, forcer)
    U_astro = list(U)
    U = [unitaire(u + w / astro.C_KM_S) for u in U]
    M, d1, d2, ecart = astro.trianguler(O[0], U[0], O[1], U[1])
    if d1 <= 0 or d2 <= 0:
        raise ErreurCalcul('pc_err_derriere')
    base = O[1] - O[0]
    p = math.acos(max(-1.0, min(1.0, float(U[0] @ U[1]))))
    um = unitaire(U[0] + U[1])
    b_perp = float(np.linalg.norm(base - (base @ um) * um))
    res = {'genre': 'lune', 'instant': tc.dt, 'instants': [t1.dt, t2.dt], 'dt_s': t2 - t1,
           'distance_geo_km': float(np.linalg.norm(M)), 'distance_topo_km': [d1, d2], 'ecart_droites_km': ecart,
           'base_km': float(np.linalg.norm(base)), 'base_perp_km': b_perp, 'parallaxe_arcsec': p * AS,
           'distance_simple_km': b_perp / p if p > 0 else float('inf'), 'decalage_temps_arcsec': decal,
           'directions': [astro.radec(u) for u in U_astro], 'M_gcrs': M.tolist(),
           'correction_temps_lumiere_km': float(np.linalg.norm(w)) * float(np.linalg.norm(M)) / astro.C_KM_S,
           'observateurs': [{'nom': v.nom, 'lat': v.lat, 'lon': v.lon, 'alt_m': v.alt_m} for v in (v1, v2)]}
    # éphéméride : distances GÉOMÉTRIQUES (comme la mesure corrigée) ; directions astrométriques (comme les photos)
    pred, src = astro.lune_astrometrique(tc, None, forcer)
    res['ephemeride'] = src
    res['distance_geo_astrometrique_eph_km'] = float(np.linalg.norm(pred))
    geo_vrai, _ = astro.lune_geocentrique(tc, forcer)
    res['distance_geo_eph_km'] = res['distance_geo_geometrique_km'] = float(np.linalg.norm(geo_vrai))
    topo = []
    sep = []
    hauteurs = []
    for k, v in enumerate((v1, v2)):
        wk, _ = astro.lune_astrometrique(tc, O[k], forcer)
        topo.append(float(np.linalg.norm(geo_vrai - O[k])))
        sep.append(astro.separation_deg(wk, U_astro[k]) * 3600)
        h, az = astro.altaz(v.lat, v.lon, R @ wk)
        hauteurs.append((h, az))
    res['distance_topo_eph_km'] = topo
    res['ecart_direction_eph_arcsec'] = sep
    res['hauteurs'] = hauteurs
    res['ecart_km'] = res['distance_geo_km'] - res['distance_geo_eph_km']
    res['ecart_rel'] = res['ecart_km'] / res['distance_geo_eph_km']
    res['parallaxe_eph_arcsec'] = astro.separation_deg(
        astro.lune_astrometrique(tc, O[0], forcer)[0], astro.lune_astrometrique(tc, O[1], forcer)[0]) * 3600
    res['refraction_arcsec'] = [astro.refraction_vraie(h) * 3600 for h, _ in hauteurs]
    return res


def _vitesse_relative_lune(t: Instant, forcer: str = '') -> np.ndarray:
    """v_Terre (barycentrique) + v_Lune (géocentrique), km/s, axes GCRS : ce qui décale la Lune pendant le trajet
    de sa lumière (dérivée numérique sur ± 5 s ; une erreur de 1 % ne change pas le résultat)."""
    a, _ = astro.lune_geocentrique(t.plus(-5.0), forcer)
    b, _ = astro.lune_geocentrique(t.plus(5.0), forcer)
    return astro.vitesse_terre_barycentrique(t) + (b - a) / 10.0


def _perp(u):
    u = unitaire(u)
    a = np.array([0.0, 0.0, 1.0]) if abs(u[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = unitaire(np.cross(u, a))
    return e1, np.cross(u, e1)


def _budget_lune(v1, v2, res, forcer) -> list:
    """Contributions (clé, km) à l'incertitude de la distance géocentrique, par dérivées numériques."""
    t1, t2 = Instant(res['instants'][0]), Instant(res['instants'][1])
    tc = Instant(res['instant'])
    D0 = res['distance_geo_km']
    out = []
    for k, v in enumerate((v1, v2)):
        u = astro.vecteur_radec(*res['directions'][k])
        tot = 0.0
        for e in _perp(u):
            s = v.sigma_arcsec / AS
            r = _lune_noyau(v1, v2, t1, t2, tc, forcer, {('dir', k): e * s})
            tot += (r['distance_geo_km'] - D0) ** 2
        out.append(('pc_b_direction', math.sqrt(tot), v.nom))
        dlat = v.sigma_pos_m / 111_320.0
        dlon = dlat / max(0.1, math.cos(math.radians(v.lat)))
        r1 = _lune_noyau(v1, v2, t1, t2, tc, forcer, {('lat', k): dlat})
        r2 = _lune_noyau(v1, v2, t1, t2, tc, forcer, {('lon', k): dlon})
        out.append(('pc_b_position', math.hypot(r1['distance_geo_km'] - D0, r2['distance_geo_km'] - D0), v.nom))
        if v.sigma_t > 0:
            r = _lune_noyau(v1, v2, t1, t2, tc, forcer, {('t', k): v.sigma_t})
            out.append(('pc_b_heure', abs(r['distance_geo_km'] - D0), v.nom))
    if res['ephemeride'] == 'meeus':
        out.append(('pc_b_ephemeride', 0.0, ''))        # n'entre pas dans la mesure (seulement la comparaison)
    return out


def _methode_sujet(res: dict, etoile: tuple) -> dict:
    """Méthode du sujet (niveau 1) : 2α = φ2 − φ1, séparations Lune–étoile ; D = base / (φ2 − φ1)."""
    s = astro.vecteur_radec(*etoile)
    phi = [astro.separation_deg(astro.vecteur_radec(*d), s) for d in res['directions']]
    o1, o2 = res['observateurs']
    la1, lo1, la2, lo2 = (math.radians(x) for x in (o1['lat'], o1['lon'], o2['lat'], o2['lon']))
    gc = 6371.0 * math.acos(max(-1.0, min(1.0, math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2)
                                         * math.cos(lo2 - lo1))))
    dphi = abs(phi[1] - phi[0]) * math.pi / 180
    return {'phi_deg': phi, 'base_gc_km': gc, 'dphi_arcsec': dphi * AS,
            'distance_km': gc / dphi if dphi > 0 else float('inf')}


# ============================================================================================== ISS
def _trace(v: Visee) -> list:
    """[(Instant, direction ITRS unitaire)] triée dans le temps (décalage d'horloge appliqué)."""
    out = []
    for p, ti in zip(v.points, v.instants()):
        t = Instant(ti)
        out.append((t, unitaire(_direction_itrs(v, p, t))))
    out.sort(key=lambda x: x[0].jd_tt)
    return out


def _interpoler(trace: list, tc: Instant) -> tuple[np.ndarray, float, bool]:
    """Direction interpolée linéairement à tc (comme le guide) ; (u, fraction, extrapolée ?)."""
    if len(trace) == 1:
        return trace[0][1], 0.0, abs(trace[0][0] - tc) > 0.05
    k = 0
    while k < len(trace) - 2 and trace[k + 1][0].jd_tt < tc.jd_tt:
        k += 1
    (ta, ua), (tb, ub) = trace[k], trace[k + 1]
    f = (tc.jd_tt - ta.jd_tt) / (tb.jd_tt - ta.jd_tt)
    return unitaire((1 - f) * ua + f * ub), float(f), not (-1e-9 <= f <= 1 + 1e-9)


def _instant_commun(ta: list, tb: list) -> tuple[Instant, bool]:
    debut = max(ta[0][0].jd_tt, tb[0][0].jd_tt)
    fin = min(ta[-1][0].jd_tt, tb[-1][0].jd_tt)
    m = (debut + fin) / 2
    t0 = ta[0][0]
    return t0.plus((m - t0.jd_tt) * 86400.0), fin >= debut


def altitude_iss(v1: Visee, v2: Visee, instant_commun: D.datetime | None = None, tle: tuple | None = None,
                 estimer_horloge: bool = True) -> dict:
    """Altitude de l'ISS par triangulation de deux traces (même algorithme que le guide)."""
    for v in (v1, v2):
        if not v.points:
            raise ErreurCalcul('pc_err_point_vide', nom=v.nom)
    res = _iss_noyau(v1, v2, instant_commun)
    if estimer_horloge and len(v2.points) >= 2 and len(v1.points) >= 2:
        res['horloge'] = estimer_decalage(v1, v2, instant_commun)
    if len(v1.points) >= 2 and len(v2.points) >= 2:
        res['plans'] = _methode_plans(v1, v2, res)
    if tle:
        res['tle'] = comparer_tle(tle, Instant(res['instant']), np.asarray(res['M_itrs']))
    res['budget'] = _budget_iss(v1, v2, res, instant_commun)
    res['sigma_km'] = math.sqrt(sum(x[1] ** 2 for x in res['budget']))
    return res


def _iss_noyau(v1, v2, instant_commun=None, perturb=None) -> dict:
    perturb = perturb or {}
    tr = []
    for k, v in enumerate((v1, v2)):
        t = _trace(v)
        if ('dir', k) in perturb:
            t = [(ti, unitaire(u + perturb[('dir', k)])) for ti, u in t]
        if ('t', k) in perturb:
            t = [(ti.plus(perturb[('t', k)]), u) for ti, u in t]
        tr.append(t)
    if instant_commun is not None:
        tc, recouvre = Instant(instant_commun), True
    else:
        tc, recouvre = _instant_commun(tr[0], tr[1])
    O = [astro.ecef(v.lat + perturb.get(('lat', k), 0.0), v.lon + perturb.get(('lon', k), 0.0), v.alt_m)
         for k, v in enumerate((v1, v2))]
    uA, fA, xA = _interpoler(tr[0], tc)
    uB, fB, xB = _interpoler(tr[1], tc)
    base = float(np.linalg.norm(O[1] - O[0]))
    p = math.degrees(math.acos(max(-1.0, min(1.0, float(uA @ uB)))))
    aA = math.degrees(math.acos(float(uA @ unitaire(O[1] - O[0]))))
    aB = math.degrees(math.acos(float(uB @ unitaire(O[0] - O[1]))))
    M, dA, dB, ecart = astro.trianguler(O[0], uA, O[1], uB)
    if dA <= 0 or dB <= 0:
        raise ErreurCalcul('pc_err_derriere')
    lat, lon, H = astro.geodesique(M)
    traits = []
    for t in tr:
        if len(t) >= 2:
            traits.append((math.degrees(math.acos(max(-1.0, min(1.0, float(t[0][1] @ t[-1][1]))))),
                           t[-1][0] - t[0][0]))
        else:
            traits.append((0.0, 0.0))
    return {'genre': 'iss', 'instant': tc.dt, 'recouvrement': recouvre, 'fractions': [fA, fB],
            'extrapole': bool(xA or xB), 'base_km': base, 'parallaxe_deg': p, 'angles_deg': [aA, aB],
            'somme_angles_deg': aA + aB + p, 'distance_sym_km': base / 2 / math.tan(math.radians(p / 2)),
            'distance_petits_angles_km': base / math.radians(p), 'distances_km': [dA, dB],
            'ecart_droites_km': ecart, 'altitude_km': H, 'sous_point': [lat, lon], 'M_itrs': M.tolist(),
            'traits': traits, 'observateurs': [{'nom': v.nom, 'lat': v.lat, 'lon': v.lon, 'alt_m': v.alt_m}
                                               for v in (v1, v2)],
            'hauteurs': [astro.altaz(v.lat, v.lon, u) for v, u in ((v1, uA), (v2, uB))]}


def estimer_decalage(v1: Visee, v2: Visee, instant_commun=None, borne: float = 5.0) -> dict:
    """Décalage d'horloge de B (s) qui rend les deux droites concourantes (écart minimal) : recherche par sections
    dorées sur [−borne, +borne].  Rend {'decalage_s', 'ecart_km', 'altitude_km'} (None si mal conditionné)."""
    import copy

    def ecart(dt):
        w = copy.copy(v2)
        w.decalage_horloge = v2.decalage_horloge + dt
        try:
            return _iss_noyau(v1, w, instant_commun)
        except (ErreurCalcul, np.linalg.LinAlgError, ValueError):
            return None
    grille = np.linspace(-borne, borne, 41)
    vals = []
    for g in grille:
        r = ecart(g)
        vals.append(r['ecart_droites_km'] if r else float('inf'))
    k = int(np.argmin(vals))
    a, b = grille[max(0, k - 1)], grille[min(len(grille) - 1, k + 1)]
    phi = (math.sqrt(5) - 1) / 2
    for _ in range(40):
        c, d = b - phi * (b - a), a + phi * (b - a)
        rc, rd = ecart(c), ecart(d)
        if (rc['ecart_droites_km'] if rc else 1e9) < (rd['ecart_droites_km'] if rd else 1e9):
            b = d
        else:
            a = c
    dt = (a + b) / 2
    r = ecart(dt)
    if r is None:
        return {'decalage_s': None, 'ecart_km': None, 'altitude_km': None}
    return {'decalage_s': float(dt), 'ecart_km': r['ecart_droites_km'], 'altitude_km': r['altitude_km'],
            'au_bord': abs(dt) > borne - 0.3}


def _methode_plans(v1, v2, res) -> dict:
    """Contrôle sans horloge commune : chaque trait et son observateur définissent un plan ; l'ISS est sur la droite
    d'intersection des deux plans (guide, § 5)."""
    tr = [_trace(v) for v in (v1, v2)]
    O = [astro.ecef(v.lat, v.lon, v.alt_m) for v in (v1, v2)]
    nP = [unitaire(np.cross(t[0][1], t[-1][1])) for t in tr]
    dL = unitaire(np.cross(nP[0], nP[1]))
    X0 = np.linalg.solve(np.array([nP[0], nP[1], dL]), [nP[0] @ O[0], nP[1] @ O[1], dL @ O[0]])
    tc = Instant(res['instant'])
    uA, _, _ = _interpoler(tr[0], tc)
    M3, *_ = astro.trianguler(O[0], uA, X0, dL)
    return {'altitude_km': astro.geodesique(M3)[2],
            'angle_plans_deg': math.degrees(math.acos(min(1.0, abs(float(nP[0] @ nP[1])))))}


def _budget_iss(v1, v2, res, instant_commun) -> list:
    H0 = res['altitude_km']
    out = []
    for k, v in enumerate((v1, v2)):
        u = np.asarray(astro.vecteur_altaz(v.lat, v.lon, *res['hauteurs'][k]))
        tot = 0.0
        for e in _perp(u):
            try:
                r = _iss_noyau(v1, v2, instant_commun, {('dir', k): e * v.sigma_arcsec / AS})
                tot += (r['altitude_km'] - H0) ** 2
            except ErreurCalcul:
                pass
        out.append(('pc_b_direction', math.sqrt(tot), v.nom))
        if v.sigma_t > 0 and len(v.points) >= 2:
            try:
                r = _iss_noyau(v1, v2, instant_commun or res['instant'], {('t', k): v.sigma_t})
                out.append(('pc_b_heure', abs(r['altitude_km'] - H0), v.nom))
            except ErreurCalcul:
                pass
        dlat = v.sigma_pos_m / 111_320.0
        r = _iss_noyau(v1, v2, instant_commun, {('lat', k): dlat})
        out.append(('pc_b_position', abs(r['altitude_km'] - H0), v.nom))
    return out


def comparer_tle(tle: tuple, t: Instant, M_itrs=None) -> dict:
    """Position prédite par un TLE (sgp4, facultatif) : TEME → repère terrestre par le temps sidéral (GMST 1982),
    comme skyfield.  Rend {'altitude_km', 'ecart_km'} ou {'erreur': clé}."""
    try:
        from sgp4.api import Satrec, jday
    except ImportError:
        return {'erreur': 'pc_tle_sans_sgp4'}
    import erfa
    l1, l2 = [x for x in tle if x.strip().startswith(('1 ', '2 '))][:2]
    sat = Satrec.twoline2rv(l1, l2)
    dt = t.dt
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    e, r, _ = sat.sgp4(jd, fr)
    if e != 0:
        return {'erreur': 'pc_tle_erreur'}
    th = erfa.gmst82(t.ut11, t.ut12)
    c, s = math.cos(th), math.sin(th)
    X = np.array([c * r[0] + s * r[1], -s * r[0] + c * r[1], r[2]])
    out = {'altitude_km': astro.geodesique(X)[2], 'age_j': (jd + fr) - (sat.jdsatepoch + sat.jdsatepochF)}
    if M_itrs is not None:
        out['ecart_km'] = float(np.linalg.norm(np.asarray(M_itrs) - X))
    return out


# ============================================================================================== un seul observateur
def iss_vitesse_angulaire(v: Visee, cap_deg: float | None = None) -> dict:
    """a) Vitesse angulaire au point culminant (pose centrée sur la culmination, 2 points) + orbite circulaire
    (Kepler) → altitude (guide, § 7 a).  `cap_deg` : direction du mouvement (azimut) pour retirer la rotation."""
    if len(v.points) < 2:
        raise ErreurCalcul('pc_err_deux_points', nom=v.nom)
    t1, t2 = Instant(v.instants()[0]), Instant(v.instants()[-1])
    p1, p2 = v.points[0], v.points[-1]
    u1 = astro.vecteur_radec(p1.ra, p1.dec)
    u2 = astro.vecteur_radec(p2.ra, p2.dec)
    duree = t2 - t1
    omega = math.acos(max(-1.0, min(1.0, float(u1 @ u2)))) / duree
    tm = t1.plus(duree / 2)
    h = math.radians(astro.altaz(v.lat, v.lon, astro.c2t(tm) @ unitaire(u1 + u2))[0])
    R = float(np.linalg.norm(astro.ecef(v.lat, v.lon, v.alt_m)))
    phi = math.radians(v.lat)

    def ecart(r):
        d = math.sqrt(r ** 2 - (R * math.cos(h)) ** 2) - R * math.sin(h)
        vit = math.sqrt(GM / r)
        if cap_deg is not None:
            w = OMEGA_T * r * math.cos(phi)
            vit = math.sqrt(vit ** 2 - 2 * vit * w * math.sin(math.radians(cap_deg)) + w ** 2)
        return vit / d - omega
    a, b = R + 100.0, R + 3000.0
    for _ in range(100):
        c = (a + b) / 2
        a, b = (c, b) if ecart(c) > 0 else (a, c)
    return {'altitude_km': (a + b) / 2 - R, 'omega_deg_s': math.degrees(omega), 'hauteur_deg': math.degrees(h)}


def iss_orbite_circulaire(v: Visee, kepler: bool = False) -> dict:
    """c) Orbite circulaire centrée sur la Terre ajustée à une série de directions datées (guide, § 7 c)."""
    if len(v.points) < 4:
        raise ErreurCalcul('pc_err_quatre_points', nom=v.nom)
    ts = [Instant(x) for x in v.instants()]
    u = np.array([astro.vecteur_radec(p.ra, p.dec) for p in v.points])
    O = np.array([astro.c2t(t).T @ astro.ecef(v.lat, v.lon, v.alt_m) for t in ts])
    t0 = ts[0]
    tau_brut = np.array([t - t0 for t in ts])
    tref_s = float(np.mean(tau_brut))
    tau = tau_brut - tref_s
    tref = t0.plus(tref_s)

    def modele(x):
        r, n, th0, an, dn = x
        N = np.array([math.cos(dn) * math.cos(an), math.cos(dn) * math.sin(an), math.sin(dn)])
        e1 = unitaire(np.cross([0.0, 0.0, 1.0], N))
        e2 = np.cross(N, e1)
        th = th0 + n * tau
        return r * (np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2), e1, e2

    def residus(x):
        P, _, _ = modele(x)
        w = P - O
        return (w / np.linalg.norm(w, axis=1)[:, None] - u).ravel()
    R0 = float(np.linalg.norm(O[0])) + 400.0
    P0 = []
    for Ok, uk in zip(O, u):
        b = Ok @ uk
        P0.append(Ok + (-b + math.sqrt(b * b - Ok @ Ok + R0 ** 2)) * uk)
    P0 = np.array(P0)
    N = unitaire(np.cross(P0[0], P0[-1]))
    x = np.array([R0, math.acos(float(unitaire(P0[0]) @ unitaire(P0[-1]))) / (tau[-1] - tau[0]), 0.0,
                  math.atan2(N[1], N[0]), math.asin(N[2])])
    _, e1, e2 = modele(x)
    th = np.unwrap(np.arctan2(P0 @ e2, P0 @ e1))
    x[2] = np.polyval(np.polyfit(tau, th, 1), 0.0)
    libres = [0, 2, 3, 4] if kepler else [0, 1, 2, 3, 4]
    for _ in range(200):
        if kepler:
            x[1] = math.sqrt(GM / x[0] ** 3)
        r0 = residus(x)
        J = np.empty((r0.size, len(libres)))
        for j, k in enumerate(libres):
            dx = np.zeros(5)
            dx[k] = 1e-7 * max(1.0, abs(x[k]))
            xp = x + dx
            if kepler:
                xp[1] = math.sqrt(GM / xp[0] ** 3)
            J[:, j] = (residus(xp) - r0) / dx[k]
        pas = np.linalg.lstsq(J, -r0, rcond=None)[0]
        x[libres] += pas
        if np.max(np.abs(pas[1:])) < 1e-13 and abs(pas[0]) < 1e-7:
            break
    if kepler:
        x[1] = math.sqrt(GM / x[0] ** 3)
    _, e1, e2 = modele(x)
    Pm = x[0] * (math.cos(x[2]) * e1 + math.sin(x[2]) * e2)
    H = astro.geodesique(astro.c2t(tref) @ Pm)[2]
    rms = math.degrees(math.sqrt(float(np.mean(residus(x) ** 2)) * 3)) * 3600
    return {'altitude_km': H, 'rayon_km': float(x[0]), 'n_rad_s': float(x[1]), 'gm': float(x[1] ** 2 * x[0] ** 3),
            'rms_arcsec': rms, 'points': len(v.points)}


def lune_parallaxe_diurne(v: Visee) -> dict:
    """Parallaxe diurne de la Lune vue d'UN lieu : positions (α, δ) datées du centre de la Lune au long d'une nuit.
    La rotation de la Terre déplace l'observateur de plusieurs milliers de km ; on ajuste la distance D et le
    mouvement géocentrique de la Lune (α et δ du second degré en temps).  Il faut plusieurs heures de mesures
    (au moins 3 h ; l'incertitude rendue le dit)."""
    if len(v.points) < 6:
        raise ErreurCalcul('pc_err_six_points', nom=v.nom)
    ts = [Instant(x) for x in v.instants()]
    t0 = ts[0]
    tau = np.array([(t - t0) / 3600.0 for t in ts])
    tm = float(np.mean(tau))
    tau = tau - tm
    u = np.array([astro.vecteur_radec(p.ra, p.dec) for p in v.points])
    O = np.array([astro.c2t(t).T @ astro.ecef(v.lat, v.lon, v.alt_m) for t in ts])
    a0, d0 = astro.radec(u.mean(axis=0))

    def residus(x):
        Dk, a0_, a1, a2, d0_, d1, d2 = x
        a = np.radians(a0_ + a1 * tau + a2 * tau ** 2)
        d = np.radians(d0_ + d1 * tau + d2 * tau ** 2)
        g = np.stack([np.cos(d) * np.cos(a), np.cos(d) * np.sin(a), np.sin(d)], axis=1)
        w = Dk * 1e5 * g - O
        return ((w / np.linalg.norm(w, axis=1)[:, None]) - u).ravel()
    x = np.array([3.84, a0, 0.55, 0.0, d0, 0.0, 0.0])
    for _ in range(100):
        r0 = residus(x)
        J = np.empty((r0.size, 7))
        for k in range(7):
            dx = np.zeros(7)
            dx[k] = 1e-6 * max(1.0, abs(x[k]))
            J[:, k] = (residus(x + dx) - r0) / dx[k]
        pas = np.linalg.lstsq(J, -r0, rcond=None)[0]
        x += pas
        if np.max(np.abs(pas)) < 1e-10:
            break
    r0 = residus(x)
    dof = max(1, r0.size - 7)
    s2 = float(r0 @ r0) / dof
    try:
        cov = np.linalg.inv(J.T @ J) * s2
        sig = math.sqrt(max(0.0, cov[0, 0])) * 1e5
    except np.linalg.LinAlgError:
        sig = float('inf')
    rms = math.sqrt(float(np.mean(r0 ** 2)) * 3) * AS
    return {'distance_geo_km': float(x[0] * 1e5), 'sigma_km': sig, 'rms_arcsec': rms, 'duree_h': float(tau[-1] - tau[0]),
            'points': len(v.points), 'instant': (t0.plus(tm * 3600)).dt}
