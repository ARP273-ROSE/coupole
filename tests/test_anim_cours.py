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
