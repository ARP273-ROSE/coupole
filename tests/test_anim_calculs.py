"""Module « Animations » : calculs astronomiques comparés aux valeurs de référence recalculées par SageMath
(outils/verif_anim/verif_anim.sage → tests/anim_reference_sage.json), aux exemples publiés de Meeus et à astropy."""
import json
import math
from pathlib import Path

import pytest

from coupole.modules.anim import astro

REF = json.loads((Path(__file__).with_name('anim_reference_sage.json')).read_text(encoding='utf-8'))


def ecart_angle(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def test_jour_julien():
    for a, m, j, h, attendu in REF['jour_julien']:
        assert astro.jour_julien(a, m, j, h) == pytest.approx(attendu, abs=1e-9)


def test_temps_sideral_iau1982():
    for jj, attendu in REF['tsmg']:
        assert ecart_angle(astro.tsmg(jj), attendu) < 2e-6          # 0,0005 s de temps
    for jj, attendu in REF['tsmg_meeus']:                              # exemples 12.a et 12.b de Meeus
        assert ecart_angle(astro.tsmg(jj), attendu) < 1e-5


def test_obliquite_iau2006():
    for jj, attendu in REF['obliquite']:
        assert astro.obliquite_moyenne(jj) == pytest.approx(attendu, abs=1e-12)
    assert astro.obliquite_moyenne() == pytest.approx(84381.406 / 3600, abs=1e-12)


def test_soleil_identique_a_sage():
    for jj, lam, alpha, delta, eqt in REF['soleil']:
        s = astro.soleil(jj)
        assert ecart_angle(s['lambda'], lam) < 1e-9
        assert ecart_angle(s['alpha'], alpha) < 1e-9
        assert s['delta'] == pytest.approx(delta, abs=1e-9)
        assert s['eqt'] == pytest.approx(eqt, abs=1e-8)


def test_soleil_exemple_meeus():
    m = REF['soleil_meeus']
    s = astro.soleil(m['jj'])
    assert ecart_angle(s['lambda'], m['lambda']) < 2e-5
    assert ecart_angle(s['alpha'], m['alpha']) < 2e-5
    assert s['delta'] == pytest.approx(m['delta'], abs=2e-5)
    assert s['eqt'] == pytest.approx(m['eqt_min'], abs=0.02)          # 13 min 42,6 s (méthode précise : à 1 s)


def test_soleil_proche_d_astropy():
    """Précision annoncée (≈ 0,01°) contre astropy : Soleil apparent dans le repère vrai de la date (TETE)."""
    pytest.importorskip('astropy')
    from astropy.coordinates import TETE, get_sun
    from astropy.time import Time
    from astropy.utils import iers
    iers.conf.auto_download = False
    for jj in (2451545.0, 2455000.25, 2461041.5, 2461120.0, 2461300.75):
        t = Time(jj, format='jd', scale='tt')
        c = get_sun(t).transform_to(TETE(obstime=t))
        s = astro.soleil(jj)
        assert ecart_angle(s['alpha'], c.ra.deg) < 0.01
        assert abs(s['delta'] - c.dec.deg) < 0.01


def test_horizon_par_rotations():
    for h, dec, lat, az, alt in REF['horizon']:
        a2, h2 = astro.equatorial_vers_horizon(h, dec, lat)
        assert h2 == pytest.approx(alt, abs=1e-9)
        if abs(alt) < 89.999:
            assert ecart_angle(a2, az) < 1e-8
        hh, dd = astro.horizon_vers_equatorial(a2, h2, lat)            # aller-retour
        assert dd == pytest.approx(dec, abs=1e-9)
        if abs(dec) < 89.999:
            assert ecart_angle(hh, h) < 1e-8


def test_matrice_et_vecteurs_coherents():
    import numpy as np
    for tsl, lat, ra, dec in ((100.0, 45.0, 70.0, 20.0), (0.0, -33.0, 300.0, -60.0), (250.0, 66.0, 10.0, 85.0)):
        m = astro.matrice_equatorial_vers_horizon(tsl, lat)
        v = astro.appliquer(m, astro.vecteur_equatorial(ra, dec))
        az, alt = astro.equatorial_vers_horizon(tsl - ra, dec, lat)
        assert np.allclose(v, astro.vecteur_horizon(az, alt), atol=1e-12)
        mm = np.array(m)
        assert np.allclose(mm @ mm.T, np.eye(3), atol=1e-12) and np.linalg.det(mm) == pytest.approx(1.0)


def test_lever_et_coucher():
    for dec, lat, h0, attendu in REF['lever']:
        assert astro.angle_horaire_lever(dec, lat, h0) == pytest.approx(attendu, abs=1e-7)
    assert astro.duree_du_jour_h(0.0, 0.0) == pytest.approx(12.0)
    assert astro.angle_horaire_lever(30.0, 70.0) == 180.0               # circumpolaire
    assert astro.angle_horaire_lever(-30.0, 70.0) == 0.0                # jamais levé


def test_plages_et_culmination():
    p = astro.plages_declinaison(48.85)
    assert p['circumpolaire'] == pytest.approx((41.15, 90.0))
    assert p['jamais'] == pytest.approx((-90.0, -41.15))
    assert astro.plages_declinaison(0.0)['circumpolaire'] is None
    assert astro.plages_declinaison(-30.0)['circumpolaire'] == pytest.approx((-90.0, -60.0))
    assert astro.plages_declinaison(90.0)['lever_coucher'] is None
    assert astro.hauteur_culmination(23.44, 48.85) == pytest.approx(64.59)
    assert astro.hauteur_culmination(-23.44, 48.85) == pytest.approx(17.71)


def test_kepler():
    for m_deg, e, attendu in REF['kepler']:
        ee = astro.resoudre_kepler(math.radians(m_deg), e)
        assert ee % (2 * math.pi) == pytest.approx(attendu % (2 * math.pi), abs=1e-12)
    for a, e, f, r, v in REF['vis_viva']:
        o = astro.orbite(a, e, f)
        assert o['r'] == pytest.approx(r, rel=1e-12)
        assert o['v'] == pytest.approx(v, rel=1e-10)
    for a, p in REF['periode']:
        assert astro.periode_annees(a) == pytest.approx(p, rel=1e-12)
    # 2e loi : aire balayée proportionnelle au temps (intégration numérique du triangle balayé)
    a, e = 1.0, 0.6
    def aire(f0, f1, n=4000):
        s = 0.0
        for k in range(n):
            p0 = astro.orbite(a, e, f0 + (f1 - f0) * k / n)
            p1 = astro.orbite(a, e, f0 + (f1 - f0) * (k + 1) / n)
            s += 0.5 * (p0['x'] * p1['y'] - p1['x'] * p0['y'])
        return s
    assert aire(0.0, 0.1) == pytest.approx(aire(0.45, 0.55), rel=1e-5)
    assert aire(0.0, 0.1) == pytest.approx(astro.aire_balayee(a, e, 0.0, 0.1), rel=1e-5)


def test_distances_stellaires():
    assert astro.PC_EN_AL == pytest.approx(REF['pc_en_al'], rel=1e-15)
    for d, mu in REF['module']:
        assert astro.module_de_distance(d) == pytest.approx(mu, abs=1e-12)
        assert astro.distance_du_module(mu) == pytest.approx(d, rel=1e-12)
    assert astro.parsecs_de_parallaxe(0.7680665) == pytest.approx(1.30197, rel=1e-5)   # Proxima


def test_eclipse_de_lune_aristarque():
    e = astro.eclipse_de_lune()
    for cle, v in REF['eclipse_lune'].items():
        assert e[cle] == pytest.approx(v, rel=1e-12), cle
    assert 2.6 < e['ombre_en_diametres_lunaires'] < 2.7
    assert 1.6 < e['totalite_h'] < 1.8


def test_cones_ombre_tangentes():
    """Les bords du cône d'ombre sont tangents aux deux sphères (distances aux bords = rayons)."""
    c = astro.cones_ombre(10.0, 2.0, 100.0)
    assert c['longueur_ombre'] == pytest.approx(25.0)
    assert c['rayon_ombre'](25.0) == pytest.approx(0.0)
    assert c['rayon_penombre'](0.0) == pytest.approx(2.0)


def test_retrogradation():
    for a, duree, amp in REF['retrogradation']:
        r = astro.retrogradation(a)
        assert r['duree_j'] == pytest.approx(duree, rel=1e-6)
        assert r['amplitude'] == pytest.approx(amp, rel=1e-6)


def test_ptolemee_equant():
    for t, cx, cy in REF['ptolemee']:
        m = astro.ptolemee_mars(t)
        assert m['centre'][0] == pytest.approx(cx, abs=1e-9) and m['centre'][1] == pytest.approx(cy, abs=1e-9)
        # le centre de l'épicycle reste sur le déférent
        assert math.hypot(m['centre'][0] - 6.0, m['centre'][1]) == pytest.approx(60.0, abs=1e-9)
        # Mars sur l'épicycle
        assert math.hypot(m['mars'][0] - cx, m['mars'][1] - cy) == pytest.approx(39.5, abs=1e-9)


def test_epicycles_equivalence():
    """Même configuration relative quel que soit le corps gardé fixe."""
    for t in (0.0, 0.37, 1.9):
        a = astro.epicycles(t, centre=1)
        b = astro.epicycles(t, centre=2)
        for k in (1, 2, 3):
            assert (a[k][0] - a[2][0]) == pytest.approx(b[k][0]) and (a[k][1] - a[2][1]) == pytest.approx(b[k][1])


def test_jour_sideral():
    for y, s in REF['jour_sideral']:
        assert astro.jour_sideral_s(y) == pytest.approx(s, rel=1e-14)
    assert astro.jour_sideral_s() == pytest.approx(86164.09, abs=0.01)    # 23 h 56 min 4,09 s


def test_phases_lune():
    assert astro.fraction_eclairee(0) == 0 and astro.fraction_eclairee(180) == pytest.approx(1)
    assert astro.fraction_eclairee(90) == pytest.approx(0.5)
    assert [astro.nom_de_phase(a) for a in (0, 45, 90, 135, 180, 225, 270, 315, 359)] == \
        ['nl', 'pc', 'pq', 'gc', 'pl', 'gd', 'dq', 'dc', 'nl']


def test_zodiaque_limites_astropy():
    """Les limites du tableau correspondent aux constellations officielles données par astropy (±0,05°)."""
    pytest.importorskip('astropy')
    import numpy as np
    from astropy import units as u
    from astropy.coordinates import GeocentricMeanEcliptic, SkyCoord, get_constellation
    from astropy.time import Time
    ep = Time(2026.0, format='jyear')
    lam = []
    for cle, l0 in astro.LIMITES_ZODIAQUE_2026:
        lam += [l0 - 0.05, l0 + 0.05]
    c = SkyCoord(lon=np.array(lam) * u.deg, lat=np.zeros(len(lam)) * u.deg,
                 frame=GeocentricMeanEcliptic(equinox=ep, obstime=ep))
    noms = [n.lower() for n in get_constellation(c, short_name=True)]
    for i, (cle, l0) in enumerate(astro.LIMITES_ZODIAQUE_2026):
        assert noms[2 * i + 1] == cle
        assert astro.constellation_du_soleil(l0 + 0.05) == cle
        assert astro.constellation_du_soleil(l0 - 0.05) == noms[2 * i]
    assert len(astro.LIMITES_ZODIAQUE_2026) == 13                       # Ophiuchus compris


def test_equinoxes_solstices_2026():
    from coupole.modules.anim.animations.rayons_soleil import REMARQUABLES
    # équinoxe de mars 2026 : 20 mars vers 14 h 46 TU ; solstice de juin : 21 juin vers 8 h 24 TU (≈ 0,01 j)
    assert REMARQUABLES['equinoxe_mars'] == pytest.approx(78 + 14.77 / 24, abs=0.02)
    assert REMARQUABLES['solstice_juin'] == pytest.approx(171 + 8.4 / 24, abs=0.02)


# ---------------------------------------------------------------- lot 1 bis (coordonnées et mouvements)
def test_hauteur_meridienne():
    from coupole.modules.anim.animations.hauteur_meridienne import culmination
    assert culmination(41.0, 23.5) == (pytest.approx(72.5), 'S')
    assert culmination(41.0, 60.0) == (pytest.approx(71.0), 'N')          # au nord du zénith : 180° − 109°
    assert culmination(-33.9, 0.0) == (pytest.approx(56.1), 'N')
    for lat, dec in ((48.85, 23.44), (0.0, -10.0), (-45.0, 30.0)):
        assert culmination(lat, dec)[0] == pytest.approx(astro.hauteur_culmination(dec, lat))


def test_antipode():
    from coupole.modules.anim.animations.antipodes import antipode
    assert antipode(48.85, 2.35) == pytest.approx((-48.85, -177.65))
    assert antipode(-33.9, -151.2) == pytest.approx((33.9, 28.8))
    for la, lo in ((10.0, 20.0), (-80.0, -170.0), (0.0, 180.0)):
        a = antipode(la, lo)
        v1 = astro.vecteur_equatorial(lo, la)
        v2 = astro.vecteur_equatorial(a[1], a[0])
        assert sum(x * y for x, y in zip(v1, v2)) == pytest.approx(-1.0)


def test_terminateur_et_point_subsolaire():
    from coupole.modules.anim.animations import jour_nuit as J
    import numpy as np
    jour = 172.0 + 0.5                              # 22 juin, 12 h TU
    dec, lon = J.subsolaire(jour)
    s = astro.soleil_jour(J.ANNEE, jour)
    assert dec == pytest.approx(s['delta'])
    assert lon == pytest.approx(-s['eqt'] / 4.0)
    # sur le terminateur, le Soleil est à l'horizon ; sur la courbe de −6°, à −6°
    lons = np.linspace(-180, 180, 37)
    for lo, la in zip(lons, J.latitude_terminateur(lons, dec, lon)):
        assert astro.equatorial_vers_horizon(lo - lon, dec, la)[1] == pytest.approx(0.0, abs=1e-7)
    for lo in lons:
        la = J.latitude_hauteur(lo, dec, lon, -6.0)
        if abs(la) < 89.99:
            assert astro.equatorial_vers_horizon(lo - lon, dec, la)[1] == pytest.approx(-6.0, abs=1e-6)


def test_courbe_duree_du_jour():
    from coupole.modules.anim.animations.duree_jour import courbe_duree
    import numpy as np
    jours, durees = courbe_duree(0.0)
    assert durees == pytest.approx(np.full(len(durees), 12.0), abs=1e-9)
    jours, durees = courbe_duree(48.85)
    assert durees.max() == pytest.approx(16.0, abs=0.1) and durees.min() == pytest.approx(8.0, abs=0.1)
    assert durees.mean() == pytest.approx(12.0, abs=0.1)
    _, polaire = courbe_duree(70.0)
    assert polaire.max() == 24.0 and polaire.min() == 0.0


def test_azimut_du_lever_aux_solstices():
    # à 41° N, l'azimut du lever au solstice de juin vaut acos(sin ε / cos φ) depuis le nord
    eps = 23.44
    az = astro.azimut_lever(eps, 41.0)
    assert az == pytest.approx(math.degrees(math.acos(math.sin(math.radians(eps)) / math.cos(math.radians(41.0)))),
                               abs=1e-9)
    assert astro.azimut_lever(0.0, 41.0) == pytest.approx(90.0)


# ---------------------------------------------------------------- lot 2 (0.3.1) : Lune, Renaissance, antique
def test_periodes_synodiques():
    for p1, p2, s in REF['synodique']:
        assert astro.periode_synodique(p1, p2) == pytest.approx(s, rel=1e-12)
    # retour inverse : période sidérale d'après la synodique (Mars supérieure, Vénus inférieure)
    s_mars = astro.periode_synodique(1.0, 1.8808)
    assert astro.periode_siderale(s_mars, 1.0, superieure=True) == pytest.approx(1.8808, rel=1e-12)
    s_venus = astro.periode_synodique(1.0, 0.6152)
    assert astro.periode_siderale(s_venus, 1.0, superieure=False) == pytest.approx(0.6152, rel=1e-12)
    assert math.isinf(astro.periode_siderale(0.9, 1.0, superieure=True))
    # lunaison = combinaison du mois sidéral et de l'année sidérale
    assert astro.periode_synodique(astro.MOIS_SIDERAL_J, astro.ANNEE_SIDERALE_J) == pytest.approx(
        astro.MOIS_SYNODIQUE_J, abs=2e-4)


def test_troisieme_loi_inverse():
    for per, m, a in REF['kepler3_inverse']:
        assert astro.demi_grand_axe(per, m) == pytest.approx(a, rel=1e-12)
        assert astro.periode_annees(a, m) == pytest.approx(per, rel=1e-12)
    from coupole.modules.anim.animations.kepler3 import PLANETES
    for _, a, jours in PLANETES:          # P² = a³ à 1 % près pour les vraies planètes (perturbations, masse propre)
        assert (jours / astro.ANNEE_SIDERALE_J) ** 2 == pytest.approx(a ** 3, rel=1e-2)


def test_gravitation_et_satellites():
    for m1, m2, r, f in REF['gravitation']:
        assert astro.force_gravitation(m1, m2, r) == pytest.approx(f, rel=1e-12)
    for r, per, v in REF['orbite_terre']:
        assert astro.periode_orbite_terre(r) == pytest.approx(per, rel=1e-12)
        assert astro.vitesse_circulaire(r) == pytest.approx(v, rel=1e-12)
    g = REF['geostationnaire']
    assert astro.jour_sideral_s(astro.ANNEE_SIDERALE_J) == pytest.approx(g['jour_sideral_s'], rel=1e-13)
    assert astro.rayon_orbite_terre(g['jour_sideral_s']) == pytest.approx(g['rayon_m'], rel=1e-12)
    assert g['rayon_m'] == pytest.approx(42_164_170, abs=50)                 # orbite géostationnaire
    from coupole.modules.anim.animations import orbites_terre as O
    assert dict(O.POINTS)['geo'] == pytest.approx(g['rayon_m'], rel=1e-12)
    gm = astro.GM_TERRE * (1 + astro.MASSE_LUNE_KG / astro.MASSE_TERRE_KG)
    assert astro.periode_orbite_terre(astro.D_LUNE_KM * 1e3, gm) / 86400 == pytest.approx(
        REF['lune_periode_deux_corps_j'], rel=1e-12)
    # pesanteur à la surface (préréglages de l'original : petite pomme, Terre, rayon terrestre) ≈ 9,82 m/s²
    from coupole.modules.anim.animations.gravitation import calcul, scientifique
    assert calcul(0.102, astro.MASSE_TERRE_KG, 6.371e6)['a1'] == pytest.approx(9.820, abs=1e-3)
    assert scientifique(6.6743e-11) in ('6,67 × 10⁻¹¹', '6.67 × 10⁻¹¹')


def test_petits_angles():
    for d, dd, exact, approche in REF['petits_angles']:
        r = astro.diametre_angulaire(d, dd)
        assert r['sphere'] == pytest.approx(exact, rel=1e-12)
        assert r['petits_angles'] == pytest.approx(approche, rel=1e-12)
    assert astro.SECONDES_D_ARC_PAR_RADIAN == pytest.approx(206_264.806_247, rel=1e-12)


def test_marees_d_equilibre():
    m = REF['marees']
    assert astro.maree_equilibre(0.0, astro.MASSE_LUNE_KG, astro.D_LUNE_KM * 1e3) == pytest.approx(
        m['amplitude_lune_m'], rel=1e-12)
    assert astro.rapport_marees_soleil_lune() == pytest.approx(m['rapport_soleil_lune'], rel=1e-12)
    from coupole.modules.anim.animations.marees import niveau, type_de_maree
    assert niveau(0.0, 0.0, False) - niveau(90.0, 0.0, False) == pytest.approx(m['marnage_lune_m'], rel=1e-12)
    # vives eaux à la pleine lune, mortes eaux au premier quartier ; deux marées hautes opposées
    vives = niveau(0.0, 180.0, True) - niveau(90.0, 180.0, True)
    mortes = niveau(90.0, 90.0, True) - niveau(0.0, 90.0, True)
    assert vives / mortes == pytest.approx((1 + m['rapport_soleil_lune']) / (1 - m['rapport_soleil_lune']), rel=1e-12)
    assert niveau(37.0, 37.0, False) == pytest.approx(niveau(217.0, 37.0, False), abs=1e-12)
    assert (type_de_maree(0.0), type_de_maree(90.0)) == ('vives', 'mortes')


def test_phases_de_venus():
    from coupole.modules.anim.animations import phases_venus as V
    for av, at, d, elong, i in REF['venus']:
        g = V.copernic(av, at)
        assert g['distance'] == pytest.approx(d, rel=1e-6)          # a = 0,723 332 ua dans les deux calculs
        assert abs(g['elongation']) == pytest.approx(elong, abs=1e-6)
        assert g['i'] == pytest.approx(i, abs=1e-6)
    assert math.degrees(math.asin(V.A_VENUS)) == pytest.approx(REF['venus_elongation_max'], abs=1e-9)
    # Ptolémée : jamais plus qu'un croissant (Vénus toujours entre la Terre et le Soleil)
    for t in [k * 0.037 for k in range(60)]:
        g = V.ptolemee(360.0 * t, 360.0 * t / V.PTOLEMEE['periode'])
        assert astro.fraction_eclairee_phase(g['i']) < 0.5
        assert abs(g['elongation']) <= math.degrees(math.asin(108 / 150)) + 1e-9
    # Copernic : pleine près de la conjonction supérieure, nouvelle à la conjonction inférieure
    assert V.copernic(180.0, 0.0)['i'] == pytest.approx(0.0, abs=1e-9)
    assert V.copernic(0.0, 0.0)['i'] == pytest.approx(180.0, abs=1e-9)


def test_configurations_planetaires():
    from coupole.modules.anim.animations.configurations import configurations
    for a_obs, a_c, s, t1 in REF['configurations']:
        c = configurations(a_obs, a_c)
        assert c['S'] == pytest.approx(s, rel=1e-12)
        assert c['temps'][1] == pytest.approx(t1, abs=1e-6)
        assert c['temps'][3] == pytest.approx(s - t1, abs=1e-6)


def test_phases_moyennes_et_argument_de_latitude():
    for k, jde, f in REF['phases_moyennes']:
        assert astro.phase_moyenne_jde(k) == pytest.approx(jde, abs=1e-6)
        assert ecart_angle(astro.argument_latitude_lune(k), f) < 1e-8
    # exemple 49.a de Meeus : nouvelle lune moyenne de février 1977, k = −283 : JDE 2443192,94102
    assert astro.phase_moyenne_jde(-283) == pytest.approx(2443192.94102, abs=1e-5)


def test_table_des_eclipses():
    """Chaque éclipse de la table : phase moyenne à moins de 1,1 jour et |sin F| < 0,36 (condition de Meeus) ; et
    toutes tombent dans une saison d'éclipses (±20,3 jours d'un passage du Soleil à un nœud)."""
    from coupole.modules.anim.animations import table_eclipses as T
    assert len(T.SOLEIL) == 66 and len(T.LUNE) == 67
    noeuds = [jj for jj, _ in astro.soleil_au_noeud(astro.jour_julien(2014, 6, 1), astro.jour_julien(2045, 6, 1))]
    for donnees, solaire in ((T.SOLEIL, True), (T.LUNE, False)):
        for e in donnees:
            v = T.verifier(e, solaire)
            assert abs(v['ecart_j']) < 1.1 and v['sinF'] < 0.36, e
            jj = astro.jour_julien(*e[:3], 12.0)
            assert min(abs(jj - n) for n in noeuds) < T.DEMI_SAISON_J, e
    # passages du Soleil aux nœuds en 2026, contre SageMath
    passages = astro.soleil_au_noeud(astro.jour_julien(2026, 1, 1), astro.jour_julien(2027, 1, 1))
    for (cible, jj_ref), (jj, nom) in zip(REF['soleil_noeuds_2026'], passages):
        assert jj == pytest.approx(jj_ref, abs=1e-6) and nom == ('asc' if cible == 0 else 'desc')
    assert T.format_duree('03h29m (00h05m)').startswith('3 h 29 min')


def test_zones_traduites():
    from coupole.modules.anim import donnees_eclipses as D
    for e in D.SOLEIL + D.LUNE:
        fr = D.zones(e[7], 'fr')
        for mot in ('Africa', 'Asia', 'Pacific', 'America', 'Total:', 'Annular:'):
            assert mot not in fr, (e, fr)


def test_precession():
    for ra, dec, jd, ra2, dec2 in REF['precession']:
        a, d = astro.precession(ra, dec, jd)
        assert ecart_angle(a, ra2) < 1e-8 and d == pytest.approx(dec2, abs=1e-8)


def test_precession_proche_d_astropy():
    pytest.importorskip('astropy')
    from astropy import units as u
    from astropy.coordinates import FK5, SkyCoord
    from astropy.time import Time
    for ra, dec, jd, _, _ in REF['precession']:
        c = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame=FK5(equinox='J2000')).transform_to(
            FK5(equinox=Time(jd, format='jd')))
        a, d = astro.precession(ra, dec, jd)
        assert ecart_angle(a, c.ra.deg) * math.cos(math.radians(d)) < 1e-4 and abs(d - c.dec.deg) < 1e-4


def test_lever_heliaque():
    for nom, ra, dec, lat, jours, hauteurs in REF['heliaque']:
        j, h = astro.lever_heliaque(ra, dec, lat)
        assert j == jours, nom
        for jour, hh in hauteurs:
            assert h[jour] == pytest.approx(hh, abs=1e-6), (nom, jour)
    # Sirius à 40,8° N : mi-août (modèle de l'original, horizon géométrique, Soleil à −7°)
    assert REF['heliaque'][0][4] == [222]


def test_pleine_lune_declinaison():
    from coupole.modules.anim.animations.pleine_lune_declinaison import pleine_lune
    for lam, beta, eps, dec in REF['dec_ecliptique']:
        assert astro.ecliptique_vers_equatorial(lam, beta, eps)[1] == pytest.approx(dec, abs=1e-9)
    hiver, ete = pleine_lune(355.0, 40.8), pleine_lune(172.0, 40.8)     # pleines lunes de décembre et de juin
    assert hiver['dec'] == pytest.approx(23.44, abs=0.02) and ete['dec'] == pytest.approx(-23.44, abs=0.02)
    assert hiver['h'] == pytest.approx(90 - 40.8 + hiver['dec'], abs=1e-9)
    assert hiver['dec_max'] - hiver['dec_min'] == pytest.approx(2 * astro.INCLINAISON_LUNE, abs=0.01)


def test_inclinaison_et_eclipses():
    from coupole.modules.anim.animations import inclinaison_lune as I
    # combinaison des périodes : la lunaison
    assert astro.periode_synodique(I.MOIS_DRACONITIQUE_J, astro.ANNEE_DRACONITIQUE_J) == pytest.approx(
        astro.MOIS_SYNODIQUE_J, rel=1e-12)
    assert I.MOIS_DRACONITIQUE_J == pytest.approx(27.212_22, abs=1e-4)
    # nouvelle lune au nœud : éclipse de Soleil ; pleine lune une demi-lunaison plus tard : éclipse de Lune
    assert I.eclipse(I.geometrie(0.0)) == 'soleil'
    assert I.eclipse(I.geometrie(astro.MOIS_SYNODIQUE_J / 2)) in ('lune_ombre', 'lune_penombre')
    # trois lunaisons plus tard, le Soleil est à 32° du nœud : la Lune passe à côté
    assert I.eclipse(I.geometrie(3 * astro.MOIS_SYNODIQUE_J)) is None
    assert 4500 < I.OMBRE_TERRE_KM < 4700


def test_jour_solaire_et_sideral():
    from coupole.modules.anim.animations import retard_synodique as R
    assert astro.jour_solaire(R.JOUR_SIDERAL_H, R.ANNEE_H) == pytest.approx(24.0, abs=1e-9)
    assert R.JOUR_SIDERAL_H * 3600 == pytest.approx(86_164.0989, abs=1e-3)
    assert astro.jour_solaire(240.0, R.ANNEE_H) == pytest.approx(1 / (1 / 240 - 1 / R.ANNEE_H), rel=1e-12)


def test_phases_vues_de_partout():
    from coupole.modules.anim.animations import ballon_phases as B, positions_phases as P, trois_vues as T3
    from coupole.modules.anim.animations.questionnaire_phases import elongation, meme_phase
    for e in range(0, 360, 15):
        i, droite = T3.vue_depuis(T3.psi_de_la_terre(e))
        assert astro.fraction_eclairee_phase(i) == pytest.approx(astro.fraction_eclairee(e), abs=1e-12)
        if 0 < e < 180:
            assert droite                                  # croissante : éclairée à droite (hémisphère nord)
        v = B.vue_de_l_oeil((e - 180.0) % 360.0)
        assert v['elongation'] == pytest.approx(e % 360.0, abs=1e-9) or e in (0, 180)
    i, _ = P.vu_de((1.0, 0.0), (2.0, 0.0))                 # planète entre le Soleil et l'observateur : « nouvelle »
    assert i == pytest.approx(180.0)
    assert elongation(135.0, 45.0) == 90.0 and meme_phase(90.0, 93.0) and not meme_phase(90.0, 97.0)


def test_lune_horizon_positions():
    from coupole.modules.anim.animations import lune_horizon as L
    assert L.heure_du_soleil(3) == 12.0 and L.heure_du_soleil(1) == 6.0 and L.heure_du_soleil(7) == 0.0
    assert L.elongation(4, 2) == 90.0                       # deux positions vers l'est : premier quartier
    assert L.elongation(3, 7) == 180.0


def test_ombre_du_batiment():
    from coupole.modules.anim.animations import ombre_batiment as O
    # au midi vrai, hauteur du Soleil = 90° − φ + δ ; ombre vers le nord, longueur cotan(hauteur)
    s = O.soleil_local(172.0, 12.0, 40.8, midi_vrai=True)
    assert s['alt'] == pytest.approx(90 - 40.8 + s['dec'], abs=1e-9) and s['az'] == pytest.approx(180.0, abs=1e-7)
    poly = O.ombre(s['az'], s['alt'])
    assert max(y for _, y in poly) == pytest.approx(O.PROFONDEUR / 2 + 1 / math.tan(math.radians(s['alt'])), abs=1e-9)
    assert O.ombre(180.0, -3.0) is None


def test_lever_et_horloge_de_la_grande_ourse():
    from coupole.modules.anim.animations import horloge_grande_ourse as H
    c = H.ciel(78.0, 1.2, 41.0)
    assert c['etoiles']['polaire'][1] > 89.2                 # Polaire à moins de 0,8° du pôle
    x, y = H.stereo(0.0, 60.0)
    assert x == pytest.approx(0.0) and y > 0                  # méridien supérieur au-dessus du pôle
    x, _ = H.stereo(90.0, 60.0)
    assert x < 0                                              # six heures après : à l'ouest (à gauche)


# ---------------------------------------------------------------- lot 2 bis : propriétés stellaires
def test_stefan_boltzmann_et_constantes_solaires():
    from coupole.modules.anim import hr
    s = REF['stellaire']
    assert hr.T_SOLEIL == pytest.approx(s['t_soleil'], rel=1e-12)
    assert hr.T_SOLEIL == pytest.approx(5772.0, abs=0.01)                 # UAI 2015 B3
    for r, t, l in s['luminosites']:
        assert hr.luminosite_solaire(r, t) == pytest.approx(l, rel=1e-12)
        assert hr.puissance_w(r * hr.R_SOLEIL_M, t) / hr.L_SOLEIL_W == pytest.approx(l, rel=1e-12)
        assert hr.rayon_solaire(l, t) == pytest.approx(r, rel=1e-12)
    assert hr.UA_PAR_AN_KM_S == pytest.approx(s['ua_par_an_km_s'], rel=1e-14)
    assert hr.mbol_de_log_lum(0.0) == 4.74 and hr.log_lum_de_mbol(4.74 - 5.0) == pytest.approx(2.0)


def test_flux_et_vitesses():
    from coupole.modules.anim import hr
    s = REF['stellaire']
    for w, d, f in s['flux']:
        assert hr.flux(w, d) == pytest.approx(f, rel=1e-12)
    for lam, v, vrel in s['doppler']:
        assert hr.vitesse_radiale(lam, 656.28) == pytest.approx(v, abs=1e-9)
        assert hr.vitesse_radiale(lam, 656.28, relativiste=True) == pytest.approx(vrel, abs=1e-9)
    assert hr.vitesse_transverse(1.0, 1.0) == pytest.approx(4.740_47, abs=1e-5)
    from coupole.modules.anim.animations.vitesse_etoile import H_ALPHA_NM
    assert H_ALPHA_NM == 656.28


def test_parallaxe_spectroscopique():
    from coupole.modules.anim import hr
    from coupole.modules.anim.animations.parallaxe_spectro import intensites, magnitude_absolue
    for m, mm, d in REF['stellaire']['distances']:
        assert astro.distance_du_module(m - mm) == pytest.approx(d, rel=1e-12)
    soleil = magnitude_absolue(42, 5)                      # G2 V : le Soleil, M_V ≈ 4,8
    assert soleil['M'] == pytest.approx(4.83, abs=0.1) and 10 ** soleil['log_t'] == pytest.approx(5772, rel=0.02)
    # intensités des raies de l'original : hélium ionisé dans les O, molécules dans les M, hydrogène maximal vers A0
    assert intensites(0)['he_ii'] == 100 and intensites(5)['molecules'] == 0 and intensites(69)['molecules'] > 90
    assert max(range(70), key=lambda t: intensites(t)['h']) in (19, 20)
    # position HR du Soleil d'après sa magnitude absolue
    lt, ll = hr.position_hr(42, 4.83)
    assert ll == pytest.approx(0.0, abs=0.05) and 10 ** lt == pytest.approx(5772, rel=0.02)


def test_donnees_du_diagramme_hr():
    from coupole.modules.anim import donnees_etoiles as E, hr
    assert len(E.PROCHES) == 119 and len(E.BRILLANTES) == 144 and len(E.COMMUNES) == 5
    proxima = E.PROCHES[0]
    assert proxima[0] == 'Proxima Centauri' and proxima[3].startswith('M5.5')
    for etoiles in (E.PROCHES, E.BRILLANTES):
        for _, t, mv, _ in etoiles:
            lt, ll = hr.position_hr(t, mv)
            assert 3.3 < lt < 4.75 and -6 < ll < 7
    assert hr.nom_type(42) == 'G2' and hr.nom_type(0) == 'O0' and hr.nom_type(65) == 'M5'
    assert hr.temperature_de_type(42) == pytest.approx(5830.0)            # table de l'original (G2 V)
