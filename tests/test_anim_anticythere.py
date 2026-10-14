"""Machine d'Anticythère (adaptée d'Anticythere3D, du même auteur) : les tests du mécanisme d'Anticythere3D
(tests/test_mechanism.py) repris à l'identique, les valeurs recalculées indépendamment sous SageMath
(outils/verif_anim/anticythere_verif.sage → tests/anticythere_reference_sage.json), puis le rendu QPainter (caméra
quaternion et ses garde-fous, vues, roue survolée, manivelle) — mêmes cas que Coupole Web."""
from __future__ import annotations

import json
import math
import random
from fractions import Fraction as F
from pathlib import Path

import pytest

from coupole.modules.anim import anticythere_meca as M

SAGE = json.loads((Path(__file__).parent / 'anticythere_reference_sage.json').read_text(encoding='utf-8'))


# ------------------------------------------------------------------ [1] rapports
def test_rapports_exacts():
    assert M.self_check() == []
    for k, v in M.EXPECTED.items():
        assert M.RATIOS[k] == v, k
    for k, v in SAGE['rapports'].items():
        assert str(M.RATIOS[k]) == v, k
    assert M.RATIOS['moon_sid'] - 1 == F(235, 19) and SAGE['lunaisons_par_an'] == '235/19'
    assert M.RATIOS['saros'] == F(4, 223) * F(235, 19)
    assert M.RATIOS['callippic'] == F(1, 76)
    assert M.RATIOS['exeligmos'] == F(235, 12711) and abs(1 / float(M.RATIOS['exeligmos']) - 54.09) < 0.01
    assert '235/19' in SAGE['reduites_annee_sur_lunaison']


# ------------------------------------------------------------------ [2] porte-satellite et mois anomalistique
def test_porte_satellite_et_mois():
    per = 1 / float(M.RATIOS['carrier_e3'])
    assert abs(per - 8.8826) < 0.001 and per == pytest.approx(SAGE['porte_satellite_ans'], rel=1e-12)
    mois = M.TROPICAL_YEAR / (float(M.RATIOS['moon_sid']) - float(M.RATIOS['carrier_e3']))
    assert abs(mois - 27.5533) < 0.001 and abs(mois - 27.55455) < 0.002
    assert mois == pytest.approx(SAGE['mois_anomalistique_j'], rel=1e-12)
    sid = M.TROPICAL_YEAR / float(M.RATIOS['moon_sid'])
    assert abs(sid - 27.321266) < 1e-5 and sid == pytest.approx(SAGE['mois_sideral_j'], rel=1e-12)


# ------------------------------------------------------------------ [3] tenon et fente
def test_tenon_et_fente():
    p = M.PinAndSlot()
    assert abs(p.amplitude_deg - 6.5796) < 0.001
    assert p.amplitude_deg == pytest.approx(SAGE['tenon_fente_amplitude_deg'], rel=1e-12)
    pire = max(abs(p.delta_turns(x / 2000)) * 360 for x in range(2000))
    assert abs(pire - p.amplitude_deg) < 0.02
    assert abs(sum(p.delta_turns(x / 2000) for x in range(2000)) / 2000) < 1e-6
    assert abs(p.speed_ratio(0.0) - 9.6 / 10.7) < 1e-9 and abs(p.speed_ratio(0.5) - 9.6 / 8.5) < 1e-9


# ------------------------------------------------------------------ [4] cadrans
def test_retour_des_cadrans():
    m = M.Mechanism()
    m.turns = 19
    assert abs(m.outputs()['metonic'] - 5) < 1e-9
    m.turns = 76
    assert abs(m.outputs()['callippic'] - 1) < 1e-9
    sy = 223 * 19 / 235
    m.turns = sy
    o = m.outputs()
    assert abs(o['saros'] - 4) < 1e-9 and abs(o['exeligmos'] - 1 / 3) < 1e-9 and o['exeligmos_hours'] == 8
    m.turns = 2 * sy
    assert m.outputs()['exeligmos_hours'] == 16
    m.turns = 3 * sy
    assert abs(m.outputs()['exeligmos'] - 1) < 1e-9 and m.outputs()['exeligmos_hours'] == 0


def test_cases_des_cadrans():
    m = M.Mechanism()
    met, sar, ans, jeux = set(), set(), set(), set()
    for i in range(20000):
        m.turns = i / 20000 * 76
        o = m.outputs()
        met.add(o['metonic_cell'])
        sar.add(o['saros_cell'])
        ans.add(o['metonic_year'])
        jeux.add(o['games_name'])
    assert len(met) == 235 and min(met) == 1 and len(sar) == 223 and len(ans) == 19 and len(jeux) == 4
    assert len(M.metonic_year_starts()) == 19


# ------------------------------------------------------------------ [5] planètes
@pytest.mark.parametrize('nom,reel', [('mercury', 0.2408467), ('venus', 0.6151973), ('mars', 1.8808476),
                                      ('jupiter', 11.862615), ('saturn', 29.447498)])
def test_periodes_des_planetes(nom, reel):
    d = M.PLANETS[nom]
    assert abs((1 / float(d['sidereal_ratio'])) / reel - 1) < 1e-3
    assert str(d['sidereal_ratio']) == SAGE['planetes'][nom]['sidereal_ratio']


# ------------------------------------------------------------------ [6] astronomie et calage
def test_astronomie_de_reference():
    assert M.julian_day(2000, 1, 1, 12) == 2451545.0
    assert M.from_julian_day(2451545.0)[:3] == (2000, 1, 1)
    lon = M.sun_longitude(M.julian_day(2026, 3, 20, 9 + 46 / 60))
    assert min(lon, 360 - lon) < 0.2


def test_calage_sur_le_ciel():
    m = M.machine_calee()
    pire_l = pire_s = 0.0
    for an in range(1950, 2051, 5):
        jd = M.julian_day(an, 6, 15, 12)
        m.days = jd - M.J2000
        o = m.outputs()
        pire_l = max(pire_l, abs((o['moon_true'] * 360 - M.moon_longitude(jd) + 180) % 360 - 180))
        pire_s = max(pire_s, abs((o['mean_sun'] * 360 - M.sun_mean_longitude(jd) + 180) % 360 - 180))
    assert pire_s < 0.01
    budget = (1.274 + 0.658 + 0.186 + 0.114
              + 50 * float(M.RATIOS['moon_sid']) * 360 * abs(365.24219 / float(M.RATIOS['moon_sid']) / 27.321662 - 1)
              + 6.58 * abs(math.sin(2 * math.pi * abs(50 / 8.8826 - 50 / 8.8504))))
    assert 0.5 < pire_l < budget


def test_calendrier_egyptien():
    assert M.NABONASSAR_JD == SAGE['nabonassar_jd']
    assert M.julian_day(-746, 2, 26, 12) == M.NABONASSAR_JD
    assert M.egyptian_date(M.NABONASSAR_JD) == (0, 1)
    assert M.egyptian_date(M.NABONASSAR_JD + 359) == (11, 30)
    assert M.egyptian_date(M.NABONASSAR_JD + 360) == (12, 1)
    assert M.egyptian_date(M.NABONASSAR_JD + 365) == (0, 1)
    t1, t2 = M.egyptian_day(M.julian_day(2000, 1, 1, 12)), M.egyptian_day(M.julian_day(2004, 1, 1, 12))
    assert (t2 - t1) % 365 == 1


# ------------------------------------------------------------------ [9] implantation
def test_entraxes_et_vitesses():
    pire = 0.0
    for a, b in M.MESHES:
        (xa, ya), (xb, yb) = M.ARBORS[M.ARBOR_OF[a]], M.ARBORS[M.ARBOR_OF[b]]
        voulu = M.MODULE * (M.TEETH[a] + M.TEETH[b]) / 2
        assert voulu == SAGE['entraxes_mm']['%s-%s' % (a, b)]
        pire = max(pire, abs(math.hypot(xa - xb, ya - yb) - voulu))
    assert pire < 0.01
    (xk, yk), (xK, yK) = M.ARBORS['k'], M.ARBORS['K']
    assert abs(math.hypot(xk - xK, yk - yK) - 1.1 * M.MODULE / 0.5093) < 0.01
    assert len(M.LEVELS) == 33
    m = M.Mechanism()
    a0 = m.gear_angles()
    m.turns = 7
    a1 = m.gear_angles()
    for g in M.LEVELS:
        if g not in ('k2', 'e6', 'e1', 'b3'):
            assert (a1[g] - a0[g]) / 7 == pytest.approx(float(M.GEAR_RATES[g]), abs=1e-10), g
    assert str(M.GEAR_RATES['n1']) == '5/19' and str(M.GEAR_RATES['o1']) == '-1/76'
    assert M.TROPICAL_YEAR / -M.CRANK_PER_TURN == pytest.approx(SAGE['manivelle_jours_par_tour'], rel=1e-12)


# ------------------------------------------------------------------ rendu QPainter
@pytest.fixture(scope='module')
def appli():
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


@pytest.fixture
def anim(appli):
    from coupole.modules.anim import catalogue
    a = catalogue.PAR_ID['antikythera'].charger()()
    a.resize(1000, 700)
    yield a
    a.close()


def test_camera_garde_fous():
    from coupole.modules.anim.animations.anticythere import VUES, q_matrice, q_valide, tourner_camera
    for q in VUES.values():
        assert q_valide(q)
    R = q_matrice(VUES['arriere'])
    assert R[0] == pytest.approx(-1) and R[8] == pytest.approx(-1)
    rnd = random.Random(7)
    aberrants = [math.nan, math.inf, -math.inf, 1e308, -1e308, 0.0]
    q = VUES['trois_quarts']
    for i in range(1000):
        dx = aberrants[i % 6] if i % 17 == 0 else (rnd.random() - 0.5) * 400
        dy = aberrants[(i + 3) % 6] if i % 23 == 0 else (rnd.random() - 0.5) * 400
        r = aberrants[i % 6] if i % 31 == 0 else 50 + rnd.random() * 300
        q = tourner_camera(q, dx, dy, r)
        assert q_valide(q), i
    assert q_valide(tourner_camera((math.nan, 0, 0, 0), 10, 10, 100))


def _couleurs(img, pas=12) -> int:
    return len({img.pixel(x, y) for x in range(0, img.width(), pas) for y in range(0, img.height(), pas)})


@pytest.mark.parametrize('enveloppe,face', [(True, 'avant'), (True, 'arriere'), (True, 'trois_quarts'),
                                            (False, 'avant'), (False, 'arriere'), (False, 'trois_quarts')])
def test_rendu_non_vide(anim, enveloppe, face):
    anim.enveloppe.setChecked(enveloppe)
    anim.face.setCurrentIndex(anim.face.findData(face))
    for e in (0, 100):
        anim.eclatement.setValue(e)
        for w, h in ((420, 560), (720, 470), (1280, 800)):
            img = anim.image(w, h)
            assert _couleurs(img) > 40, (enveloppe, face, e, w)
            assert all(map(math.isfinite, anim.q))


def test_roue_survolee_et_touchee(anim):
    from PyQt6.QtCore import QPointF, Qt
    from coupole.modules.anim.animations.anticythere import fiche_roue, projeter
    anim.enveloppe.setChecked(False)
    anim.image(800, 520)
    gx, gy, gz = M.gear_placement('b1', 0, anim.meca.raw('carrier_e3'))
    a = 2 * math.pi * anim.meca.gear_angles()['b1']
    X, Y, _ = projeter(anim.pr, gx + 60 * math.cos(a), gy + 60 * math.sin(a), gz + M.GEAR_THICKNESS)
    assert anim.survoler(QPointF(X, Y))
    assert anim.roue == 'b1' and anim.valeurs()[-1][1] == fiche_roue('b1')
    assert '477/4237' in fiche_roue('e3') and '1/76' in fiche_roue('o1')
    anim.survoler(QPointF(2, 2))
    assert anim.roue is None
    gx, gy, gz = M.gear_placement('m1', 0, 0)
    X, Y, _ = projeter(anim.pr, gx - 25, gy, gz + M.GEAR_THICKNESS)
    anim.presser(QPointF(X, Y), Qt.MouseButton.LeftButton)
    anim.relacher(QPointF(X, Y))
    assert anim.roue is not None
    anim.presser(QPointF(12, 30), Qt.MouseButton.LeftButton)
    anim.relacher(QPointF(12, 30))
    assert anim.roue is None


def test_manivelle_a_la_souris(anim):
    from PyQt6.QtCore import QPointF, Qt
    from coupole.modules.anim.animations.anticythere import projeter
    anim.image(800, 520)
    ax, ay = M.ARBORS['a']
    zp = M.Z_FRONT - 2 + M.CRANK_SHAFT + 4 + (M.CRANK_HANDLE + 6) / 2
    ang0 = 2 * math.pi * anim.meca.gear_angles()['a1']

    def point(t):
        X, Y, _ = projeter(anim.pr, ax + M.CRANK_RADIUS * math.cos(t), ay + M.CRANK_RADIUS * math.sin(t), zp)
        return QPointF(X, Y)
    assert anim.sur_manivelle(point(ang0))
    j0 = anim.meca.days
    anim.presser(point(ang0), Qt.MouseButton.LeftButton)
    for k in range(1, 41):
        anim.glisser(point(ang0 - 2 * math.pi * k / 40), 1, 1)
    anim.relacher(point(ang0))
    assert anim.meca.days - j0 == pytest.approx(M.TROPICAL_YEAR * 48 / 223, abs=1e-6)


def test_glisser_pendant_la_lecture_sans_nan(anim):
    from PyQt6.QtCore import QPointF, Qt
    from coupole.modules.anim.animations.anticythere import q_valide
    anim.enveloppe.setChecked(False)
    anim.image(800, 520)
    for i in range(60):
        anim.presser(QPointF(400, 250), Qt.MouseButton.LeftButton)
        anim.glisser(QPointF(420 + i, 260), math.nan if i % 7 == 0 else 20 + i, math.inf if i % 11 == 0 else -10)
        anim.pas(0.05)
        anim.relacher(QPointF(420 + i, 260))
        assert _couleurs(anim.image(420, 560)) > 40
    assert q_valide(anim.q)


def test_lecture_et_boutons(anim):
    j0 = anim.meca.days
    anim.pas(1.0)
    assert anim.meca.days - j0 == pytest.approx(M.TROPICAL_YEAR * 48 / 223, abs=1e-9)
    j1 = anim.jd()
    anim.regler_jd(j1 + M.SYNODIC_MONTH)
    assert anim.jd() - j1 == pytest.approx(M.SYNODIC_MONTH, abs=1e-9)
    anim.regler_jd(math.nan)
    assert math.isfinite(anim.jd())


def test_rendu_rapide(anim):
    """Durée d'une image (minimum de 15 rendus, 720 × 470) : fermée et ouverte."""
    import time
    for enveloppe, face in ((True, 'avant'), (False, 'trois_quarts')):
        anim.enveloppe.setChecked(enveloppe)
        anim.face.setCurrentIndex(anim.face.findData(face))
        anim.image(720, 470)
        ts = []
        for _ in range(15):
            anim.pas(0.03)
            t0 = time.perf_counter()
            anim.image(720, 470)
            ts.append(time.perf_counter() - t0)
        assert min(ts) < 0.05, (enveloppe, min(ts))
