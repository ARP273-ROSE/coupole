"""Partages du DU, outil Parallaxe (0.8.0) : calculs comparés à des références INDÉPENDANTES.

* skyfield + JPL DE440 (``outils/verif_parallaxe/references_skyfield.py`` → ``parallaxe_reference_skyfield.json``) :
  position de l'observateur (GCRS), direction et distance de la Lune, triangulation d'une paire Lune, altitude de
  l'ISS par triangulation, prédiction TLE ;
* SageMath à 200 bits (``outils/verif_parallaxe/verif_parallaxe.sage`` → ``parallaxe_reference_sage.json``) :
  ellipsoïde WGS84 dans les deux sens, point le plus proche de deux droites, réfraction, cercle de Kåsa, orbite
  circulaire au zénith.
Le fichier DE440 n'est pas livré : sans lui, la Lune vient de l'approximation de Meeus (tolérances adaptées) ; les
essais DE440 tournent si ``COUPOLE_DE440`` désigne ``de440s.bsp``.
"""
import datetime as D
import json
import math
import os
from pathlib import Path

import numpy as np
import pytest

from coupole.modules.partages import astro
from coupole.modules.partages.analyses.parallaxe import calcul as C
from coupole.modules.partages.analyses.parallaxe import image as I
from coupole.modules.partages.analyses.parallaxe import paires as P

ICI = Path(__file__).parent
SKY = json.loads((ICI / 'parallaxe_reference_skyfield.json').read_text(encoding='utf-8'))
SAGE = json.loads((ICI / 'parallaxe_reference_sage.json').read_text(encoding='utf-8'))
UTC = D.timezone.utc
DE440 = bool(os.environ.get('COUPOLE_DE440')) and astro.jplephem_present()


def _dt(u):
    a, mo, j, h, mi, s = u
    return D.datetime(int(a), int(mo), int(j), int(h), int(mi), tzinfo=UTC) + D.timedelta(seconds=float(s))


def _sep_arcsec(ra1, dec1, ra2, dec2):
    return astro.separation_deg(astro.vecteur_radec(ra1, dec1), astro.vecteur_radec(ra2, dec2)) * 3600


# ============================================================================================== SageMath
@pytest.mark.parametrize('cas', SAGE['ecef'], ids=lambda c: '%g,%g' % (c['lat'], c['lon']))
def test_ecef_wgs84(cas):
    assert astro.ecef(cas['lat'], cas['lon'], cas['h_m']) == pytest.approx(cas['xyz_km'], abs=1e-9)


@pytest.mark.parametrize('cas', SAGE['geodesique'], ids=lambda c: str(c['xyz_km'][0]))
def test_geodesique_wgs84(cas):
    la, lo, h = astro.geodesique(cas['xyz_km'])
    assert (la, lo) == pytest.approx(cas['lat_lon_h'][:2], abs=1e-10) and h == pytest.approx(cas['lat_lon_h'][2],
                                                                                              abs=1e-9)


@pytest.mark.parametrize('cas', SAGE['trianguler'], ids=lambda c: str(c['d1'])[:8])
def test_point_le_plus_proche_de_deux_droites(cas):
    M, d1, d2, e = astro.trianguler(np.array(cas['O1']), cas['u1'], np.array(cas['O2']), cas['u2'])
    assert M == pytest.approx(cas['milieu'], rel=1e-8, abs=1e-7)
    assert (d1, d2) == pytest.approx((cas['d1'], cas['d2']), rel=1e-8) and e == pytest.approx(cas['ecart'], abs=1e-6)


@pytest.mark.parametrize('cas', SAGE['refraction'], ids=lambda c: str(c['h_deg']))
def test_refraction(cas):
    assert astro.refraction_bennett(cas['h_deg']) == pytest.approx(cas['bennett_deg'], rel=1e-12)
    assert astro.refraction_vraie(cas['h_deg']) == pytest.approx(cas['saemundsson_deg'], rel=1e-12)


def test_cercle_de_kasa():
    k = SAGE['kasa']
    x, y = np.array(k['points']).T
    assert I.ajuster_cercle(x, y) == pytest.approx((k['xc'], k['yc'], k['r']), abs=1e-8)


@pytest.mark.parametrize('cas', SAGE['orbite'], ids=lambda c: str(c['altitude_km']))
def test_orbite_circulaire_au_zenith(cas):
    """Méthode à un observateur a) : deux directions symétriques autour du zénith d'un lieu de l'équateur."""
    t0 = D.datetime(2026, 10, 17, 4, 29, 0, tzinfo=UTC)
    duree = 2.0
    tm = astro.Instant(t0 + D.timedelta(seconds=duree / 2))
    E, N, Z = astro.enu(0.0, 0.0)
    R = astro.c2t(tm).T
    th = cas['omega_rad_s'] * duree / 2
    u1, u2 = R @ (math.cos(th) * Z - math.sin(th) * N), R @ (math.cos(th) * Z + math.sin(th) * N)
    pts = [C.Point(t0, *astro.radec(u1)), C.Point(t0 + D.timedelta(seconds=duree), *astro.radec(u2))]
    r = C.iss_vitesse_angulaire(C.Visee('A', 0.0, 0.0, 0.0, pts))
    assert r['hauteur_deg'] == pytest.approx(90.0, abs=1e-6)
    assert r['altitude_km'] == pytest.approx(cas['racine_altitude_km'], abs=1e-6)


# ============================================================================================== skyfield + DE440
@pytest.mark.parametrize('cas', SKY['lune'], ids=lambda c: '%s-%d' % (c['lieu'], c['utc'][0]))
def test_observateur_et_lune_vus_d_un_lieu(cas):
    t = astro.Instant(_dt(cas['utc']))
    O = astro.observateur_gcrs(cas['lat'], cas['lon'], cas['alt_m'], t)
    # 2 m avec des tables IERS à jour ; jusqu'à ~15 m avec celles d'un astropy plus ancien (UT1 − UTC prédit)
    assert np.linalg.norm(O - np.array(cas['observateur_gcrs_km'])) < 0.02
    v, src = astro.lune_astrometrique(t, O)
    ra, dec = astro.radec(v)
    ecart, dist = _sep_arcsec(ra, dec, cas['ra_deg'], cas['dec_deg']), float(np.linalg.norm(v))
    if src == 'de440':
        assert ecart < 0.05 and abs(dist - cas['distance_km']) < 0.01
    else:                                   # Meeus (erfa.moon98) : quelques secondes d'arc, quelques km
        assert ecart < 10 and abs(dist - cas['distance_km']) < 15
    h, az, _, _ = astro.altaz_lune(cas['lat'], cas['lon'], cas['alt_m'], t, refraction=False)
    # direction astrométrique tournée dans le repère terrestre : sans l'aberration annuelle (≤ 20,5″)
    assert astro.separation_deg(astro.vecteur_altaz(0, 0, h, az),
                                astro.vecteur_altaz(0, 0, cas['h_apparente_deg'], cas['az_deg'])) * 3600 < 30


@pytest.mark.parametrize('cas', SKY['paires_lune'], ids=lambda c: '%s-%s-%d' % (
    c['observateurs'][0]['lieu'], c['observateurs'][1]['lieu'], round(c['observateurs'][1]['utc'][5])))
def test_distance_de_la_lune_par_deux_visees(cas):
    """Les directions viennent de skyfield + DE440 ; la triangulation (indépendante de l'éphéméride de Coupole)
    doit retrouver la distance géocentrique astrométrique."""
    v = [C.Visee(o['lieu'], o['lat'], o['lon'], o['alt_m'], [C.Point(_dt(o['utc']), o['ra_deg'], o['dec_deg'])],
                 sigma_arcsec=1.0) for o in cas['observateurs']]
    r = C.distance_lune(*v)
    assert abs(r['distance_geo_km'] - cas['distance_geometrique_km']) < 0.5
    for k in (0, 1) if r['dt_s'] == 0 else ():          # visées décalées : distances topocentriques à l'instant commun
        assert abs(r['distance_topo_km'][k] - cas['observateurs'][k]['distance_topo_geometrique_km']) < 0.5
    assert r['ecart_droites_km'] < 0.05 and r['parallaxe_arcsec'] > 30
    tol = 0.05 if r['ephemeride'] == 'de440' else 15
    assert abs(r['distance_geo_eph_km'] - cas['distance_geometrique_km']) < tol
    assert abs(r['distance_geo_astrometrique_eph_km'] - cas['distance_geo_km']) < tol
    assert abs(r['ecart_km']) < tol + 0.5 and max(r['ecart_direction_eph_arcsec']) < (0.01 if tol < 1 else 10)
    assert r['sigma_km'] > 0 and {b[0] for b in r['budget']} >= {'pc_b_direction', 'pc_b_position', 'pc_b_heure'}


@pytest.mark.skipif(not DE440, reason='COUPOLE_DE440 (de440s.bsp) et jplephem nécessaires')
def test_de440_reconnu():
    assert astro.source_ephemeride() == 'de440'


@pytest.mark.parametrize('n', [3, 2], ids=['trois-points', 'deux-points'])
@pytest.mark.parametrize('cas', SKY['iss'], ids=lambda c: '-'.join(c['lieux']))
def test_altitude_de_l_iss_par_deux_traces(cas, n):
    from .partages_exemple import LYON, PARIS, STRASBOURG
    lieux = {'paris': PARIS, 'lyon': LYON, 'strasbourg': STRASBOURG}
    idx = [0, 1, 2] if n == 3 else [0, 2]
    v = [C.Visee(nom, *lieux[nom], [C.Point(_dt(cas['utc'][k]), *cas['points'][nom][k]) for k in idx],
                 sigma_arcsec=5.0, sigma_t=0.01) for nom in cas['lieux']]
    r = C.altitude_iss(*v, tle=tuple(SKY['tle']))
    tol = 0.02 if n == 3 else 0.5                    # deux points : interpolation linéaire le long du trait
    assert abs(r['altitude_km'] - cas['altitude_km'][1]) < tol
    assert r['sous_point'] == pytest.approx(cas['sous_point'], abs=0.01 if n == 3 else 0.05)
    assert r['ecart_droites_km'] < (0.01 if n == 3 else 0.5)
    assert abs(r['horloge']['decalage_s']) < 0.05 and abs(r['plans']['altitude_km'] - cas['altitude_km'][1]) < 1.0
    assert abs(r['tle']['altitude_km'] - cas['altitude_km'][1]) < 0.01 and r['tle']['ecart_km'] < tol + 0.03
    assert r['somme_angles_deg'] == pytest.approx(180.0, abs=0.01)


def test_tle_dans_le_repere_terrestre():
    cas = SKY['iss'][0]
    for u, xyz in zip(cas['utc'], cas['itrs_km']):
        r = C.comparer_tle(tuple(SKY['tle']), astro.Instant(_dt(u)), np.array(xyz))
        assert r['ecart_km'] < 0.03 and 0 < r['age_j'] < 1                        # idem (UT1 des tables IERS)


def test_horloge_decalee_retrouvee():
    """Observateur B en retard de 0,8 s : l'estimation du décalage le retrouve et la triangulation se recale."""
    cas = SKY['iss'][0]
    from .partages_exemple import LYON, PARIS
    lieux = {'paris': PARIS, 'lyon': LYON}
    v1 = C.Visee('paris', *lieux['paris'], [C.Point(_dt(u), *p) for u, p in zip(cas['utc'], cas['points']['paris'])])
    v2 = C.Visee('lyon', *lieux['lyon'], [C.Point(_dt(u) - D.timedelta(seconds=0.8), *p)
                                          for u, p in zip(cas['utc'], cas['points']['lyon'])])
    r = C.altitude_iss(v1, v2)
    assert r['horloge']['decalage_s'] == pytest.approx(0.8, abs=0.05)
    v2.decalage_horloge = r['horloge']['decalage_s']
    assert abs(C.altitude_iss(v1, v2)['altitude_km'] - cas['altitude_km'][1]) < 0.2


def test_hauteur_azimut_mesurees_et_refraction():
    """Une visée en (h, az) mesurés sur le ciel réel : la réfraction est retirée avant le calcul."""
    cas = SKY['lune'][0]
    t = _dt(cas['utc'])
    h_mes = cas['h_apparente_deg'] + astro.refraction_vraie(cas['h_apparente_deg'])
    v = C.Visee('A', cas['lat'], cas['lon'], cas['alt_m'], [C.Point(t, h=h_mes, az=cas['az_deg'])],
                refraction='mesuree')
    u = C._direction_itrs(v, v.points[0], astro.Instant(t))
    assert astro.altaz(cas['lat'], cas['lon'], u)[0] == pytest.approx(cas['h_apparente_deg'], abs=2 / 3600)


def test_erreurs_lisibles():
    t = D.datetime(2025, 11, 3, 18, 38, 26, tzinfo=UTC)
    with pytest.raises(C.ErreurCalcul) as e:
        C.distance_lune(C.Visee('A', 48, 2), C.Visee('B', 43, 5, points=[C.Point(t, 10, 8)]))
    assert e.value.cle == 'pc_err_point_vide'
    with pytest.raises(C.ErreurCalcul) as e:
        C.iss_orbite_circulaire(C.Visee('A', 48, 2, points=[C.Point(t, 1, 1)]))
    assert e.value.cle == 'pc_err_quatre_points'


# ============================================================================================== paires
def _obs(i, qui, cible, t, lieu, fin=None, sure=True):
    return P.Observation(i, qui, cible, t, fin, lieu[0], lieu[1], lieu[2], 'tableau', [], sure)


def test_paires_simultanees():
    from .partages_exemple import LYON, MARSEILLE, PARIS, STRASBOURG
    t = D.datetime(2026, 10, 17, 4, 29, 11, tzinfo=UTC)
    s = D.timedelta(seconds=1)
    obs = [_obs('a', 'Observateur A', 'iss', t, PARIS, t + 10 * s),
           _obs('b', 'Observateur B', 'iss', t + 4 * s, LYON),                 # dans l'intervalle de A : écart 0
           _obs('c', 'Observateur C', 'iss', t + 30 * s, STRASBOURG),          # trop tard pour l'ISS
           _obs('d', 'Observateur A', 'iss', t + 2 * s, PARIS),                # même observateur : jamais une paire
           _obs('e', 'Observateur E', 'iss', t + 3 * s, (48.86, 2.36, 30)),    # à 1 km de A : base trop courte
           _obs('f', 'Observateur F', 'lune', t, MARSEILLE),
           _obs('g', 'Observateur G', 'lune', t + 45 * s, PARIS, sure=False)]  # Lune : 60 s tolérées
    p = P.trouver(obs)
    noms = {(x.a.ident, x.b.ident) for x in p}
    assert ('a', 'b') in noms and ('f', 'g') in noms and len(noms) == 4             # + (b, e) : Lyon–Paris
    ab = next(x for x in p if {x.a.ident, x.b.ident} == {'a', 'b'})
    assert ab.ecart_s == 0 and ab.synchro_seconde and 350 < ab.base_km < 450
    fg = next(x for x in p if x.cible == 'lune')
    assert fg.ecart_s == 45 and 'pc_p_heure_nom' in fg.notes
    assert not any('d' in (x.a.ident, x.b.ident) and 'a' in (x.a.ident, x.b.ident) for x in p)
    assert not any({x.a.ident, x.b.ident} == {'a', 'e'} for x in p)
    assert P.resume_synchro(p)['lune'] == 1
    assert P.trouver(obs, {'iss': 0.5}) and all(x.ecart_s <= 0.5 for x in P.trouver(obs, {'iss': 0.5}) if
                                               x.cible == 'iss')


def test_paires_depuis_le_tableau_d_exemple():
    from . import partages_exemple as X
    from coupole.modules.partages import mesures as M
    from coupole.modules.partages import tableur as T
    t = M.controler(M.lire_tableau(T.lire(X.classeur(X.lignes_mesures())).feuille(0)))
    obs = P.depuis_tableau(t)
    p = P.trouver(obs)
    paires = {frozenset((x.a.observateur, x.b.observateur)) for x in p}
    # A et B (B corrigé : Marseille), A et C (heure corrigée), B et C : toutes à moins de 60 s, bases > 100 km
    assert frozenset(('Observateur A', 'Observateur B')) in paires
    sans = {frozenset((x.a.observateur, x.b.observateur)) for x in P.trouver(P.depuis_tableau(t, appliquer=False))}
    assert sans != paires
