"""« L'atmosphère terrestre » (0.8.0) : formules contre SageMath (outils/verif_atmosphere/atmosphere_verif.sage →
atmosphere_sage.json), ordres de grandeur connus, données de l'ESO, rendu des quatre vues."""
import json
from pathlib import Path

import pytest

from coupole.modules.anim import atmosphere_calc as A

SAGE = json.loads((Path(__file__).parent / 'atmosphere_sage.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('c', SAGE['masse_air'], ids=lambda c: str(c['h']))
def test_masse_air(c):
    if c['secz'] is not None:
        assert A.masse_air_secz(c['h']) == pytest.approx(c['secz'], rel=1e-12)
    assert A.masse_air_kasten_young(c['h']) == pytest.approx(c['kasten_young'], rel=1e-12)
    assert A.masse_air_pickering(c['h']) == pytest.approx(c['pickering'], rel=1e-12)
    assert A.chemin_sphere_km(c['h']) == pytest.approx(c['chemin_km'], rel=1e-10)
    assert A.masse_air_sphere(c['h']) == pytest.approx(c['sphere'], rel=1e-10)


@pytest.mark.parametrize('c', SAGE['bandes'], ids=lambda c: '%s-%g' % (c['bande'], c['P']))
def test_extinction(c):
    assert A.tau_rayleigh(c['lambda'], c['P']) == pytest.approx(c['tau_r'], rel=1e-12)
    assert A.tau_aerosols(c['lambda']) == pytest.approx(c['tau_a'], rel=1e-12)
    assert A.tau_ozone(c['lambda']) == pytest.approx(c['tau_o'], rel=1e-12, abs=1e-15)
    assert A.k_bande(c['lambda'], c['P']) == pytest.approx(c['k'], rel=1e-12)


@pytest.mark.parametrize('c', SAGE['refraction'], ids=lambda c: '%g-%g' % (c['h'], c['P']))
def test_refraction(c):
    assert A.refraction_apparente(c['h'], c['P'], c['T']) == pytest.approx(c['bennett'], rel=1e-12, abs=1e-15)
    assert A.refraction_vraie(c['h'], c['P'], c['T']) == pytest.approx(c['saemundsson'], rel=1e-12, abs=1e-15)


def test_ciddor_aplatissement_lever():
    for c in SAGE['ciddor']:
        assert A.indice_ciddor(c['lambda']) == pytest.approx(c['n_moins_1'], rel=1e-12)
    for c in SAGE['aplatissement']:
        assert A.aplatissement(0.0, 0.2666, c['P'], c['T'])['rapport'] == pytest.approx(c['rapport'], rel=1e-10)
    for c in SAGE['avance']:
        assert A.avance_lever_min(c['lat']) == pytest.approx(c['minutes'], rel=1e-9)


def test_ordres_de_grandeur():
    assert 37 < A.masse_air_kasten_young(0) < 39 and A.masse_air_kasten_young(90) == pytest.approx(1.0, abs=1e-3)
    assert 33 / 60 < A.refraction_apparente(0.0) < 36 / 60                      # ≈ 34′ à l'horizon
    assert A.refraction_vraie(45.0) * 60 == pytest.approx(1.0, abs=0.05)          # ≈ 1′ à 45°
    assert 0.1 < A.k_bande(0.551) < 0.35 and A.k_bande(0.365) > 2 * A.k_bande(0.658)
    assert 2.2 < A.avance_lever_min(0) < 2.4                                      # ≈ 2 min à l'équateur
    assert A.indice_ciddor(0.45) > A.indice_ciddor(0.65)                          # le bleu est plus réfracté
    r, v, b = A.couleur_transmise(38.0)
    assert r == 1.0 and b < 0.2                                                   # Soleil couchant : rouge
    d = A.transmission_eso()
    assert len(d['lambda_um']) > 300 and 'SkyCalc' in d['source']
    t = dict(zip(d['lambda_um'], d['total']))
    assert max(v for l, v in t.items() if 2.0 < l < 2.4) > 0.85                  # bande K transparente
    assert max(v for l, v in t.items() if 5.8 < l < 7.0) < 0.1                    # vapeur d'eau : opaque


@pytest.mark.parametrize('vue', ['epaisseur', 'extinction', 'fenetres', 'refraction'])
def test_vues(app_qt, vue):
    from PyQt6.QtGui import QImage
    from coupole.modules.anim.animations.atmosphere import Atmosphere
    w = Atmosphere()
    w.resize(1000, 680)
    w.vue_c.setCurrentIndex(w.vue_c.findData(vue))
    for h in (-1.0, 0.0, 3.0, 45.0, 90.0):
        w.h.setValue(h)
        w.exagerer.setChecked(h == 3.0)
        img = w.image(720, 470) if hasattr(w, 'image') else None
        assert img is None or isinstance(img, QImage)
        assert w.valeurs()
    w.deleteLater()
