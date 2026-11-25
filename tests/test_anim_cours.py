"""Animations tirées des cours (propres à Coupole) : calculs comparés aux valeurs recalculées par SageMath
(outils/verif_anim/*_verif.sage → tests/*_sage.json), comportements de l'interface."""
import json
import math
from pathlib import Path

import pytest

from coupole.modules.anim import diffraction as dif

ICI = Path(__file__).resolve().parent


def sage(nom):
    return json.loads((ICI / ('%s_sage.json' % nom)).read_text(encoding='utf-8'))


# ---------------------------------------------------------------- diffraction et pouvoir de résolution
def test_diffraction_constantes():
    s = sage('resolution')
    assert dif.V1 == pytest.approx(s['v1'], abs=1e-12)
    assert dif.RAYLEIGH == pytest.approx(s['rayleigh'], abs=1e-12)
    assert dif.FWHM_AIRY == pytest.approx(s['fwhm_airy'], abs=1e-12)


def test_diffraction_bessel():
    s = sage('resolution')
    for x, v in s['j1'].items():
        assert dif.j1(float(x)) == pytest.approx(v, abs=2e-8), x
        assert dif.j1(-float(x)) == pytest.approx(-v, abs=2e-8), x
    for x, v in s['i0e'].items():
        assert dif.i0e(float(x)) == pytest.approx(v, rel=2e-6), x


def test_diffraction_zeros_et_anneau():
    s = sage('resolution')
    assert dif.premier_zero(0.0) == pytest.approx(s['v1'], abs=1e-6)
    for e, v in s['zeros'].items():
        assert dif.premier_zero(float(e)) == pytest.approx(v, abs=1e-6), e
    # éclat du premier anneau : 1,75 % du centre
    vm = max(dif.airy(dif.V1 + k * 0.001) for k in range(3200))
    assert vm == pytest.approx(s['anneau1'], rel=1e-4)


def test_diffraction_rayleigh_et_instruments():
    s = sage('resolution')
    for k, d, _ in dif.INSTRUMENTS:
        assert dif.rayleigh_arcsec(d, 550.0) == pytest.approx(s['instruments'][k], rel=1e-9), k
    for cle, v in s['turbulence'].items():
        seeing, lam = cle.split('_')
        assert dif.diametre_turbulence(float(seeing), float(lam)) == pytest.approx(v, rel=1e-9)
    pr = dif.Profil(0.2, 550.0)
    theta = dif.rayleigh_arcsec(0.2, 550.0)
    assert pr.t1 == pytest.approx(theta, rel=1e-6)
    assert dif.creux_milieu(pr, theta) / 100.0 == pytest.approx(s['creux_rayleigh'], abs=2e-3)
    fw = dif.largeur_mi_hauteur(pr) / (550e-9 / 0.2 * dif.SEC_PAR_RAD)
    assert fw == pytest.approx(s['fwhm_airy'], abs=2e-3)


def test_diffraction_pose_longue():
    s = sage('resolution')
    pr = dif.Profil(0.2, 550.0, 0.0, 0.3)
    assert pr.mode == 'convolution'
    for r, v in s['pose_longue'].items():
        assert pr.valeur(float(r)) == pytest.approx(v, abs=3e-3), r
    # turbulence forte : gaussienne de largeur quadratique
    g = dif.Profil(8.2, 550.0, 0.14, 0.8)
    assert g.mode == 'gauss'
    attendu = math.hypot(0.8, dif.FWHM_AIRY * 550e-9 / 8.2 * dif.SEC_PAR_RAD)
    assert dif.largeur_mi_hauteur(g) == pytest.approx(attendu, rel=5e-3)


def test_diffraction_coupe_et_verdict():
    pr = dif.Profil(0.2, 550.0)
    th = dif.rayleigh_arcsec(0.2, 550.0)
    assert dif.coupe(pr, 0.5 * th)['creux'] is None                  # un seul sommet
    assert dif.coupe(pr, 3 * th)['creux'] < 1.0                       # bien séparées : creux noir
    assert dif.verdict(2 * th, 0.2, 550.0, 0.0) == 'separees'
    assert dif.verdict(th, 0.2, 550.0, 0.0) == 'limite'
    assert dif.verdict(0.5 * th, 0.2, 550.0, 0.0) == 'confondues'
    assert dif.verdict(2 * th, 0.2, 550.0, 3.0) == 'confondues'      # la turbulence décide


def test_resolution_interface(app_qt):
    from coupole.modules.anim.animations.resolution import Resolution
    a = Resolution()
    a.resize(900, 640)
    a.instrument.setCurrentIndex(a.instrument.findData('hubble'))
    assert a.diametre.value() == pytest.approx(240.0) and a.obstruction.value() == pytest.approx(0.33)
    a.diametre.setValue(30.0)                                           # réglage libre ensuite
    assert a.instrument.currentData() == 'hubble' and a.diametre.value() == pytest.approx(30.0)
    v = dict(a.valeurs())
    assert 'Premier anneau noir' in v and '1,22 λ / D' in v
    for s in (0.0, 0.5, 3.0):
        a.seeing.setValue(s)
        assert not a.image(640, 420).isNull()


# ---------------------------------------------------------------- les éléments d'une orbite
def test_orbite_periodes_et_vitesses():
    from coupole.modules.anim import elements_orbitaux as eo
    s = sage('elements_orbite')
    for k, (a, e, i, om, w) in eo.ORBITES.items():
        assert eo.periode_s(a) == pytest.approx(s['periodes'][k], rel=1e-12), k
        vp, va = s['vitesses'][k]
        assert eo.vitesse(a * (1 - e), a) == pytest.approx(vp, rel=1e-12)
        assert eo.vitesse(a * (1 + e), a) == pytest.approx(va, rel=1e-12)
    assert eo.demi_grand_axe_de_periode(eo.JOUR_SIDERAL_S) == pytest.approx(s['a_geo'], rel=1e-12)
    assert eo.demi_grand_axe_de_periode(eo.JOUR_SIDERAL_S / 2) == pytest.approx(s['a_molniya'], rel=1e-12)
    # les orbites types sont bien ce qu'elles disent
    assert eo.genre_orbite(*eo.ORBITES['geo'][:3]) == 'geostationnaire'
    assert abs(eo.ORBITES['geo'][0] - s['a_geo']) < 1.0 and abs(eo.ORBITES['molniya'][0] - s['a_molniya']) < 1.0
    assert eo.genre_orbite(*eo.ORBITES['polaire'][:3]) == 'polaire'
    assert eo.genre_orbite(6000.0, 0.0, 10.0) == 'heurte'


def test_orbite_position_vitesse_trace():
    from coupole.modules.anim import elements_orbitaux as eo
    for c in sage('elements_orbite')['cas']:
        a, e, i, om, w, m = c['el']
        st = eo.etat(a, e, i, om, w, m)
        assert st['E'] == pytest.approx(c['E'], abs=1e-9)
        assert st['nu'] == pytest.approx(c['nu'], abs=1e-9)
        assert st['r'] == pytest.approx(c['r'], rel=1e-12)
        assert st['v'] == pytest.approx(c['v'], rel=1e-12)
        assert st['pos'] == pytest.approx(c['pos'], abs=1e-7)
        assert st['vit'] == pytest.approx(c['vit'], abs=1e-10)
        assert math.sqrt(sum(x * x for x in st['vit'])) == pytest.approx(c['norme_vit'], rel=1e-12)
        lat, lon = eo.sous_satellite(st['pos'], c['t'])
        assert lat == pytest.approx(c['lat'], abs=1e-9) and lon == pytest.approx(c['lon'], abs=1e-9)


def test_orbite_interface(app_qt):
    from coupole.modules.anim.animations.elements_orbite import ElementsOrbite
    a = ElementsOrbite()
    a.resize(900, 640)
    a.orbite.setCurrentIndex(a.orbite.findData('molniya'))
    assert a.e.value() == pytest.approx(0.74) and a.i.value() == pytest.approx(63.4) and a.w.value() == pytest.approx(270.0)
    v = dict(a.valeurs())
    assert v['Période T'] == '11 h 58 min'
    a.orbite.setCurrentIndex(a.orbite.findData('geo'))
    assert 'géostationnaire' in dict(a.valeurs())['Orbite']
    for _ in range(30):
        a.pas(0.2)
    for trace in (True, False):
        a.c_trace.setChecked(trace)
        assert not a.image(640, 420).isNull()


# ---------------------------------------------------------------- le transfert de Hohmann
def test_hohmann_bilans():
    from coupole.modules.anim import hohmann_meca as hm
    s = sage('hohmann')
    for k, (mu, r1, r2, *_r) in hm.SCENARIOS.items():
        b = hm.bilan(mu, r1, r2)
        for x in ('v1', 'v2', 'vd', 'va', 'dv1', 'dv2', 'dv', 't', 'phase', 'synodique'):
            assert b[x] == pytest.approx(s[k][x], rel=1e-11, abs=1e-12), (k, x)
        for f, (r, ang) in s[k]['position'].items():
            rr, aa = hm.position_transfert(b, r1, r2, 0.0, b['t'] * float(f))
            assert rr == pytest.approx(r, rel=1e-11), (k, f)
            assert math.remainder(aa - ang, 2 * math.pi) == pytest.approx(0.0, abs=1e-9), (k, f)
        # au bout de la demi-ellipse : r₂, à l'opposé du départ ; partir à l'angle de phase = rendez-vous
        rr, aa = hm.position_transfert(b, r1, r2, 0.3, b['t'])
        assert rr == pytest.approx(r2, rel=1e-9) and math.remainder(aa - 0.3 - math.pi, 2 * math.pi) == pytest.approx(0, abs=1e-7)
        assert hm.ecart_rendez_vous(b, b['phase']) == pytest.approx(0.0, abs=1e-9)
        assert hm.attente_fenetre(b, b['phase']) == pytest.approx(0.0, abs=1e-6 * b['synodique']) or \
            hm.attente_fenetre(b, b['phase']) == pytest.approx(b['synodique'], rel=1e-6)


def test_hohmann_interface(app_qt):
    from coupole.modules.anim.animations.hohmann import Hohmann
    a = Hohmann()
    a.resize(900, 640)
    a.scenario.setCurrentIndex(a.scenario.findData('terre_mars'))
    a.c_auto.setChecked(True)
    for _ in range(120):                              # attente, départ à la fenêtre, transfert, arrivée
        a.pas(0.1)
    assert a.etape() == 'arrive' and abs(a.ecart()) < 0.5
    assert 'rendez-vous réussi' in dict(a.valeurs())['Vaisseau']
    a.recommencer()
    a.c_auto.setChecked(False)
    a.lancer()                                        # départ immédiat : la cible n'y est pas
    for _ in range(70):
        a.pas(0.1)
    assert a.etape() == 'arrive' and abs(a.ecart()) > 2
    for k in ('leo_geo', 'terre_venus', 'terre_lune'):
        a.scenario.setCurrentIndex(a.scenario.findData(k))
        assert a.etape() == 'attente' and not a.image(640, 420).isNull()
