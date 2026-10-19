"""Calculateurs de TD (0.8.0), « Parallaxe (TP du cours) » : lecteur de coordonnées (cas communs avec Coupole Web),
géométrie et calculs contre SageMath (corde à 1 mm près), éphémérides, incertitudes, exemple."""
import datetime as D
import json
from pathlib import Path

import pytest

from coupole.modules.td import coordonnees as K
from coupole.modules.td import parallaxe_tp as T

ICI = Path(__file__).parent
CAS_COORD = json.loads((ICI / 'td_coordonnees_cas.json').read_text(encoding='utf-8'))['cas']
CAS = {c['id']: c for c in json.loads((ICI.parent / 'outils' / 'verif_td' / 'cas_td.json').read_text(
    encoding='utf-8'))['cas']}
SAGE = json.loads((ICI / 'td_parallaxe_sage.json').read_text(encoding='utf-8'))['cas']
UTC = D.timezone.utc


@pytest.mark.parametrize('cas', CAS_COORD, ids=lambda c: '%s:%s' % (c['type'], c['texte']))
def test_lecteur_de_coordonnees(cas):
    f = K.lire_angle if cas['type'] == 'angle' else K.lire_position
    if 'erreur' in cas:
        with pytest.raises(K.CoordonneeIllisible) as e:
            f(cas['texte'])
        assert e.value.cle == cas['erreur']
        return
    r = f(cas['texte'])
    v = r.valeur if cas['type'] == 'angle' else [r.lat, r.lon]
    assert v == pytest.approx(cas['attendu'], abs=1e-9)
    assert set(cas.get('notes', [])) <= set(r.notes)


def test_altitudes():
    assert K.lire_altitude('120') == 120 and K.lire_altitude('1,2 km') == 1200 and K.lire_altitude('') == 0
    assert K.lire_altitude('350,5 m') == 350.5
    with pytest.raises(K.CoordonneeIllisible):
        K.lire_altitude('haut')


def _lieux(c):
    return [T.Lieu(*x) for x in (c['o1'], c['o2'])]


@pytest.mark.parametrize('ref', SAGE, ids=lambda r: r['id'])
def test_contre_sage(ref):
    c = CAS[ref['id']]
    o1, o2 = _lieux(c)
    g = T.geometrie_base(o1, o2)
    assert abs(g['corde_km'] - ref['corde_km']) < 1e-6                                   # 1 mm
    assert abs(g['surface_km'] - ref['surface_km']) < 1e-6
    assert abs(g['fleche_km'] - ref['fleche_km']) < 1e-6
    assert g['fleche_approchee_km'] == pytest.approx(ref['fleche_approchee_km'], abs=1e-6)
    assert g['profondeur_deg'] == pytest.approx(ref['profondeur_deg'], abs=1e-9)
    assert g['angle_centre_deg'] == pytest.approx(ref['angle_centre_deg'], abs=1e-9)
    assert (g['az_1_vers_2'], g['az_2_vers_1']) == pytest.approx((ref['az_1_vers_2'], ref['az_2_vers_1']), abs=1e-8)
    r = T.calculer(T.Entrees(o1, o2, 'iss', configuration=c['config']))
    assert (r['configuration'] == 'entre') == ref['entre']
    assert r['sujet_corde']['deux_alpha_deg'] == pytest.approx(ref['deux_alpha_deg'], abs=1e-9)
    assert r['sujet_corde']['D_km'] == pytest.approx(ref['D_corde_km'], rel=1e-9)
    assert r['sujet_surface']['D_km'] == pytest.approx(ref['D_surface_km'], rel=1e-9)
    x = r['exact']
    assert x['distances_km'] == pytest.approx(ref['distances_km'], rel=1e-8)
    assert x['altitude_km'] == pytest.approx(ref['altitude_km'], abs=1e-5)
    assert x['sous_point'] == pytest.approx(ref['sous_point'], abs=1e-8)
    assert x['ecart_droites_km'] == pytest.approx(ref['ecart_droites_km'], abs=1e-6)


def test_ordres_de_grandeur_du_sujet():
    """Ce que le sujet dit : 400 km de base → parallaxe lunaire ~1/1000 rad ; la flèche de 400 km vaut ~3 km."""
    o1, o2 = T.Lieu(48.8566, 2.3522), T.Lieu(45.4, 2.3522)
    g = T.geometrie_base(o1, o2)
    assert 380 < g['corde_km'] < 390 and 2.5 < g['fleche_km'] < 3.2
    assert g['surface_km'] > g['corde_km'] and g['profondeur_deg'][0] < 0 and g['profondeur_deg'][1] < 0
    assert g['angle_centre_deg'] == pytest.approx(2 * -g['profondeur_deg'][0], rel=0.01)


def test_lune_l_horizon_n_est_pas_plat():
    """Exemple Lune : la formule du sujet appliquée aux élévations donne ~8 500 km (les horizons font 5° entre eux) ;
    le calcul exact retrouve la distance de la Lune."""
    ex = T.exemple('lune')
    p1, p2 = K.lire_position(ex['p1']), K.lire_position(ex['p2'])
    o1 = T.Lieu(p1.lat, p1.lon, 35.0, 31.96731, 117.50126)
    o2 = T.Lieu(p2.lat, p2.lon, 12.0, 36.41708, 116.88005)
    r = T.calculer(T.Entrees(o1, o2, 'lune', D.datetime(2025, 11, 3, 18, 38, 26, tzinfo=UTC)))
    assert 5000 < r['sujet_corde']['D_km'] < 12000
    eph = r['ephemeride']
    assert abs(r['exact']['distances_km'][0] - eph['lieux'][0]['distance_km']) / eph['lieux'][0]['distance_km'] < 0.003
    assert abs(eph['lieux'][0]['h_deg'] - 31.96731) < 0.01 and eph['source'] in ('de440', 'meeus')
    assert r['incertitudes']['exact_total_km'] > 0


def test_iss_tle_et_incertitudes():
    sky = json.loads((ICI / 'parallaxe_reference_skyfield.json').read_text(encoding='utf-8'))
    c = sky['iss'][0]
    t = D.datetime(*[int(x) for x in c['utc'][1][:5]], tzinfo=UTC) + D.timedelta(seconds=c['utc'][1][5])
    o1, o2 = T.Lieu(48.8566, 2.3522, 35.0), T.Lieu(45.764, 4.8357, 170.0)
    eph = T.ephemeride_iss(o1, o2, t, tuple(sky['tle']))
    assert eph['altitude_km'] == pytest.approx(c['altitude_km'][1], abs=0.01) and 0 < eph['age_jours'] < 1
    o1.h, o1.az = eph['lieux'][0]['h_deg'], eph['lieux'][0]['az_deg']
    o2.h, o2.az = eph['lieux'][1]['h_deg'], eph['lieux'][1]['az_deg']
    r = T.calculer(T.Entrees(o1, o2, 'iss', t, tuple(sky['tle'])))
    assert r['exact']['altitude_km'] == pytest.approx(c['altitude_km'][1], abs=0.01)
    assert r['exact']['distances_km'][0] == pytest.approx(eph['lieux'][0]['distance_km'], abs=0.01)
    inc = r['incertitudes']
    assert inc['sigma_h_effectif_deg'] > 0.1 and inc['exact_total_km'] > 0 and inc['sujet_total_km'] > 0
    assert not any(a[0] == 'td_a_tle_ancien' for a in r['alertes'])
    vieux = T.calculer(T.Entrees(o1, o2, 'iss', t + D.timedelta(days=8), tuple(sky['tle'])))
    assert any(a[0] == 'td_a_tle_ancien' for a in vieux['alertes'])


def test_inversion_et_erreurs():
    assert T.inversion_probable(T.Lieu(48.8566, 2.3522), T.Lieu(4.8357, 45.764)) == 0      # l'un ou l'autre
    assert T.inversion_probable(T.Lieu(-33.8688, 151.2093), T.Lieu(48.8566, 2.3522)) is None      # vraie base
    assert T.inversion_probable(T.Lieu(48.8566, 2.3522), T.Lieu(45.764, 4.8357)) is None
    with pytest.raises(T.ErreurTP):
        T.calcul_sujet(100.0, 30.0, 30.0)
    with pytest.raises(T.ErreurTP):
        T.calculer(T.Entrees(T.Lieu(45, 6, 0, 30), T.Lieu(45, 6, 0, 31)))
    assert T.geodesique_km(10, 20, 10, 20) == 0.0


# ============================================================================================== interface et CLI
def _attendre(app, cond, delai=30):
    import time
    fin = time.time() + delai
    while not cond() and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)
    return cond()


@pytest.mark.parametrize('cible', ['iss', 'lune'])
def test_interface_exemple_dessin_export(app_qt, cible, tmp_path):
    from PyQt6.QtGui import QImage
    from coupole.modules.td.gui import Panneau
    p = Panneau()
    p.resize(1200, 760)
    p.show()
    try:
        assert p.liste.count() >= 1 and p.liste.item(0).text().startswith(('Parallaxe', 'Parallax'))
        tp = p.parallaxe
        tp.c_cible.setCurrentIndex(tp.c_cible.findData(cible))
        tp.exemple()
        assert _attendre(app_qt, lambda: tp.res is not None)
        r = tp.res
        x = r['exact']
        if cible == 'iss':
            assert abs(x['altitude_km'] - 420) < 1                 # ISS fictive à 420 km
        else:
            assert abs(x['distances_km'][0] - 357936) / 357936 < 0.0003 and 'ephemeride' in r
        texte = tp.detail.toPlainText()
        assert texte.count('\n') >= 5 and 'R / 2α' in texte or 'R/2α' in texte or '2α' in texte
        for z in (10, 200, 600):
            tp.zoom.setValue(z)
            img = QImage(tp.schema.size(), QImage.Format.Format_ARGB32)
            tp.schema.render(img)
            assert len({img.pixel(i, j) for i in range(0, img.width(), 3) for j in range(0, img.height(), 3)}) > 20
        csv = __import__('coupole.modules.td.presentation', fromlist=['texte_export']).texte_export(r)
        assert csv.count('\n') >= 15 and ('Corde R' in csv or 'Chord R' in csv)
    finally:
        p.close()


def test_interface_saisie_fautive(app_qt):
    from coupole.modules.td.gui import Panneau
    p = Panneau()
    try:
        tp = p.parallaxe
        tp.e['p1'].setText('48°61′ N 2 E')
        tp.e['p2'].setText('45.76, 4.83')
        tp.e['h1'].setText('40')
        tp.e['h2'].setText('30')
        tp.calculer()
        assert '≥ 60' in tp.l_etat.text() and tp.res is None
        tp.e['p1'].setText('2.35, 48.86')                     # longitude puis latitude : sans lettre, ambigu
        tp.calculer()
        assert _attendre(app_qt, lambda: tp.res is not None)
        assert any(a[0].startswith('td_a_inversion') for a in tp.res['alertes'])
    finally:
        p.close()


def test_ligne_de_commande(capsys):
    from coupole.cli import main
    assert main(['--lang', 'fr', 'td', 'parallaxe', '--p1', '48.8566, 2.3522', '--h1', '62,483', '--az1', '14,184',
                 '--alt1', '35', '--p2', '45°45′50″N 4°50′09″E', '--h2', '33.603', '--az2', '346.928',
                 '--alt2', '170']) == 0
    sortie = capsys.readouterr().out
    assert '1. Relevés' in sortie and 'altitude 4' in sortie
    assert main(['--lang', 'fr', 'td', 'parallaxe', '--p1', 'x', '--h1', '1', '--p2', '45 5', '--h2', '2']) == 2


def test_references_communes_avec_coupole_web():
    """tests/td_parallaxe_reference.json (outils/verif_td/references_td.py) : ce que Coupole Web doit retrouver."""
    ref = json.loads((ICI / 'td_parallaxe_reference.json').read_text(encoding='utf-8'))['cas']
    sage = {c['id']: c for c in SAGE}
    for c in ref:
        o1, o2 = _lieux(CAS[c['id']])
        r = T.calculer(T.Entrees(o1, o2, 'iss', configuration=CAS[c['id']]['config']))
        assert r['geometrie']['corde_km'] == pytest.approx(c['corde_km'], abs=1e-9)
        assert r['exact']['distances_km'] == pytest.approx(c['distances_km'], rel=1e-9)
        assert abs(c['corde_km'] - sage[c['id']]['corde_km']) < 1e-6                     # ≤ 1 mm de SageMath


def test_tle_recupere_tout_seul(app_qt, monkeypatch):
    """ISS, instant donné, champ TLE vide : le TLE le plus proche est récupéré tout seul au calcul (sans clic), posé
    dans le champ, et cherché de nouveau quand l'instant change ; un TLE saisi à la main est gardé tel quel."""
    from coupole.modules.td import tle as TL
    from coupole.modules.td.gui import Panneau
    sky = json.loads((ICI / 'parallaxe_reference_skyfield.json').read_text(encoding='utf-8'))
    appels = []

    def pour(instant, reseau_permis=True):
        appels.append(instant)
        return {'tle': tuple(sky['tle']), 'epoque': TL.epoque(sky['tle']), 'age_jours': 0.2, 'source': 'celestrak',
                'erreur': ''}
    monkeypatch.setattr(TL, 'pour', pour)
    p = Panneau()
    try:
        tp = p.parallaxe
        tp.c_cible.setCurrentIndex(tp.c_cible.findData('iss'))
        tp.exemple()
        assert _attendre(app_qt, lambda: tp.res is not None)
        c = sky['iss'][0]
        tp.e_instant.setText('%04d-%02d-%02d %02d:%02d:%06.3f' % tuple(c['utc'][1]))
        tp.res = None
        tp.calculer()
        assert _attendre(app_qt, lambda: tp.res is not None)
        assert len(appels) == 1 and tp.e_tle.toPlainText().startswith('1 25544') and 'ephemeride' in tp.res
        tp.e_instant.setText('%04d-%02d-%02d %02d:%02d:%06.3f' % (tuple(c['utc'][1][:3]) + (c['utc'][1][3], 0, 0.0)))
        tp.res = None
        tp.calculer()
        assert _attendre(app_qt, lambda: tp.res is not None) and len(appels) == 2
        tp.e_tle.setPlainText('\n'.join(sky['tle']) + '\n')          # saisie : gardée
        tp.res = None
        tp.calculer()
        assert _attendre(app_qt, lambda: tp.res is not None) and len(appels) == 2
    finally:
        p.close()
