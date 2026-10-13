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
