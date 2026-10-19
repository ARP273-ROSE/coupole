"""« Démonstrateur du temps sidéral et de l'angle horaire » (0.8.0) : arc de l'angle horaire affiché par défaut (un
choix mémorisé est gardé), « Ce qu'il faut voir » et encadré « Dans l'hémisphère Sud », affirmations vérifiées par
SageMath (``outils/verif_anim/temps_sideral_sud_verif.sage`` → ``temps_sideral_sud_sage.json``)."""
import json
from pathlib import Path

import pytest

from coupole.modules.anim import astro
from coupole.modules.anim.animations.angle_horaire import angle_horaire_h

SAGE = json.loads((Path(__file__).parent / 'temps_sideral_sud_sage.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('cas', SAGE['cas'], ids=lambda c: '%g,%g' % (c['lat'], c['dec']))
def test_hemisphere_sud_contre_sage(cas):
    lat, dec = cas['lat'], cas['dec']
    hs = [astro.equatorial_vers_horizon(15 * h / 10, dec, lat)[1] for h in range(-120, 121)]
    assert min(hs) == pytest.approx(cas['h_min'], abs=1e-9) and max(hs) == pytest.approx(cas['h_max'], abs=1e-9)
    assert (min(hs) > 0) == cas['circumpolaire'] == (dec < -(90 - abs(lat)))
    az_culm = astro.equatorial_vers_horizon(0.0, dec, lat)[0]
    if dec != lat:
        assert (abs(az_culm) < 1e-9 or abs(az_culm - 360) < 1e-9) == cas['culmine_au_nord'] == (dec > lat)
    e, o = (astro.equatorial_vers_horizon(15 * h, dec, lat)[0] for h in (-5, 5))
    assert (e, o) == pytest.approx(cas['az_lever_puis_coucher'], abs=1e-9)
    assert astro.equatorial_vers_horizon(-15.0, dec, lat)[1] > astro.equatorial_vers_horizon(-16.5, dec, lat)[1]


def test_convention_de_l_angle_horaire():
    assert angle_horaire_h(10.0, 12.0) == -2.0                  # avant la culmination : H < 0
    assert angle_horaire_h(14.0, 12.0) == 2.0                   # vers l'ouest après
    assert angle_horaire_h(1.0, 23.0) == 2.0


def test_textes_de_l_encadre_et_sigma_oct(langue):
    from coupole.core.i18n import tr
    langue('fr')
    t = tr('anim_siderealtimeandhourangledemo_sud')
    s = SAGE['sigma_oct']
    assert 'σ Octantis' in t and 'magnitude 5,4' in t and round(s['distance_pole_deg']) == 1 and \
        round(s['V'], 1) == 5.4
    assert 'environ 1°' in t and '−56°' in t and round(90 - 33.87) == 56 and 'NORD' in t
    langue('en')
    assert 'right to left' in tr('anim_siderealtimeandhourangledemo_sud')
    langue('fr')


def test_arc_par_defaut_et_fiche(propre_anim):
    from coupole.gui import memoire
    from coupole.modules.anim.animations.angle_horaire import AngleHoraire
    from coupole.modules.anim.catalogue import PAR_ID
    from coupole.modules.anim.gui import Panneau
    w = AngleHoraire()
    assert w.c_arc.isChecked()                                  # arc de H affiché par défaut
    w.c_arc.setChecked(False)                                   # choix de l'utilisateur…
    memoire.memoire().ecrire()
    w.deleteLater()
    w2 = AngleHoraire()
    assert not w2.c_arc.isChecked()                             # … gardé, jamais écrasé par le nouveau défaut
    w2.deleteLater()
    h = Panneau.description(PAR_ID['siderealTimeAndHourAngleDemo'])
    assert 'Ce qu’il faut voir' in h and 'Dans l’hémisphère Sud' in h and 'σ Octantis' in h


@pytest.fixture
def propre_anim(app_qt):
    from coupole.gui import memoire
    memoire.reinitialiser_pour_tests()
    yield app_qt
    memoire.reinitialiser_pour_tests()
