"""Trois vues d'un spectre (threeviewsspectra) : l'ordre le long de la visée décide du spectre.  L'ampoule est
opaque : vue devant le nuage, elle le cache (spectre continu) ; l'absorption n'existe que si la visée traverse le gaz
PUIS l'ampoule.  Le classement est comparé, sur un balayage de tous les angles, à une marche le long du rayon écrite
indépendamment ; le télescope et son étiquette restent hors du halo de l'ampoule (mêmes tests que Coupole Web)."""
from __future__ import annotations

import math

import pytest

from coupole.modules.anim.animations.kirchhoff import (AMPOULE, L_TUBE, NUAGE, R_HALO, R_TELESCOPE,
                                                       type_de_spectre, vue)


def spectre(angle, cible):
    return type_de_spectre(vue(angle, cible))


def marche(angle, cible):
    """Marche le long du rayon par pas de 10⁻³ : le premier objet opaque arrête la visée."""
    a = math.radians(angle)
    tx, ty = R_TELESCOPE * math.cos(a), R_TELESCOPE * math.sin(a)
    gx, gy = (NUAGE if cible == 'nuage' else AMPOULE)[:2]
    n = math.hypot(gx - tx, gy - ty)
    dx, dy = (gx - tx) / n, (gy - ty) / n
    gaz = False
    for i in range(20000):
        s = i * 1e-3
        x, y = tx + s * dx, ty + s * dy
        if math.hypot(x - AMPOULE[0], y - AMPOULE[1]) < AMPOULE[2]:
            return 'absorption' if gaz else 'continu'
        if math.hypot(x - NUAGE[0], y - NUAGE[1]) < NUAGE[2]:
            gaz = True
    return 'emission' if gaz else 'rien'


def test_ampoule_devant_le_nuage_donne_un_continu():
    v = vue(0.0, 'nuage')
    assert v['ampoule'] and v['s_nuage'] is not None and v['s_ampoule'] < v['s_nuage']
    assert spectre(0.0, 'nuage') == 'continu'


def test_gaz_devant_l_ampoule_donne_l_absorption():
    assert spectre(180.0, 'nuage') == 'absorption'


@pytest.mark.parametrize('angle', [0, 30, 60, 90, 270, 300, 330])
def test_ampoule_hors_nuage_continu(angle):
    assert spectre(angle, 'ampoule') == 'continu'


@pytest.mark.parametrize('angle', [60, 90, 120, 240, 270, 300])
def test_nuage_seul_emission(angle):
    assert spectre(angle, 'nuage') == 'emission'


def test_balayage_contre_la_marche_le_long_du_rayon():
    ecarts = [(i / 4, c) for i in range(0, 1440, 3) for c in ('nuage', 'ampoule')
              if spectre(i / 4, c) != marche(i / 4, c)]
    # la marche par pas finis peut manquer une tangence exacte : quelques angles rasants tolérés
    assert len(ecarts) <= 2, ecarts[:5]


def test_absorption_jamais_nuage_derriere_l_ampoule():
    for i in range(3600):
        for c in ('nuage', 'ampoule'):
            v = vue(i / 10, c)
            if type_de_spectre(v) == 'absorption':
                assert v['s_nuage'] < v['s_ampoule']


def test_tube_hors_du_halo():
    assert R_TELESCOPE - L_TUBE > AMPOULE[0] + R_HALO


@pytest.fixture(scope='module')
def appli():
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_etiquette_du_telescope_hors_du_halo(appli):
    from coupole.modules.anim import catalogue, dessin
    a = catalogue.PAR_ID['threeviewsspectra'].charger()()
    a.resize(1000, 700)
    for w, h in ((420, 560), (720, 470), (1280, 800), (2560, 1440)):
        for angle in (0, 5, 355, 180, 90):
            a.angle.setValue(angle)
            a.image(w, h)
            cx, cy, k = a._scene
            hx, hy, rh = cx + AMPOULE[0] * k, cy, R_HALO * k
            for bx, by, bw, bh in dessin.etiquettes_posees():
                px, py = max(bx, min(hx, bx + bw)), max(by, min(hy, by + bh))
                assert math.hypot(px - hx, py - hy) > rh, (w, h, angle)
    a.close()
