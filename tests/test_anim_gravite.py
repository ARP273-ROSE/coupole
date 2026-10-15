"""« Gravité et orbites » (0.7.2, d'après la simulation PhET Gravity and Orbits, University of Colorado Boulder ; code
propre) : mécanique identique au web au bit près (tests/gravite_cas.json, aussi rejoué par Coupole Web), contrôles
physiques (période de la Terre ≈ 365,25 j et de la Lune ≈ 27,3 j à 0,5 % près, énergie et moment cinétique conservés,
mouvement rectiligne sans gravité, collision), accord avec l'intégration indépendante de SageMath
(tests/gravite_orbites_sage.json), puis l'animation hors écran : réglages, glisser (astre, flèche, ruban), retour, vues,
passage en douceur qui s'arrête, valeurs, durée d'une image."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import pytest

from coupole.modules.anim import gravite_meca as g

ICI = Path(__file__).resolve().parent
CAS = json.loads((ICI / 'gravite_cas.json').read_text('utf-8'))
SAGE = json.loads((ICI / 'gravite_orbites_sage.json').read_text('utf-8'))
JOUR = g.JOUR


# ------------------------------------------------------------------ mécanique
@pytest.mark.parametrize('nom', sorted(CAS))
def test_identique_aux_cas_communs(nom):
    """Mêmes nombres au bit près que les cas communs (le web les rejoue aussi : tests/unit/gravite.test.ts)."""
    cas = CAS[nom]
    s = g.Systeme(g.scenario(nom), float.fromhex(cas['pas_trace']))

    def etat():
        return [[c.nom, c.m.hex(), c.x.hex(), c.y.hex(), c.vx.hex(), c.vy.hex(), c.actif] for c in s.corps]
    assert etat() == cas['depart']
    for e in cas['etapes']:
        s.corps[0].m = g.MASSES[s.corps[0].nom] * e['masse']
        if s.gravite != e['gravite']:
            s.gravite = e['gravite']
            s.remesurer()
        s.avancer(float.fromhex(e['duree']))
        assert s.t.hex() == e['t']
        assert etat() == e['etat']
        assert [None if s.periode(i) is None else s.periode(i).hex() for i in range(len(s.corps))] == e['periodes']
        assert [x.hex() for x in s.derives()] == e['derives']
        k = s.courbure_lune()
        assert (None if k is None else k.hex()) == e['courbure']
        assert [len(t.x) for t in s.traces] == e['n_traces']
        assert s.derniers_pas == e['pas']


def test_constantes_et_etats_initiaux_comme_sagemath():
    assert g.G == SAGE['constantes']['G'] and g.UA == SAGE['constantes']['ua']
    for k, m in SAGE['constantes']['masses'].items():
        assert abs(g.MASSES[k] - m) / m < 1e-15
    for nom, sc in SAGE['scenarios'].items():
        cs = g.scenario(nom)
        for c, (n, x, y, vx, vy) in zip(cs, sc['etat_initial_si']):
            assert c.nom == n
            for a, b in ((c.x, x), (c.y, y), (c.vx, vx), (c.vy, vy)):
                assert abs(a - b) / max(abs(b), (abs(x) + abs(y)) * 1e-6, 1) < 1e-12, (nom, n)


@pytest.mark.parametrize('sc,jours,corps,vraie', [
    ('soleil_terre', 800, 'terre', 365.256363), ('soleil_terre_lune', 800, 'terre', 365.256363),
    ('soleil_terre_lune', 800, 'lune', 27.321661), ('terre_lune', 120, 'lune', 27.321661)])
def test_periodes_a_un_demi_pour_cent_et_comme_sagemath(sc, jours, corps, vraie):
    s = g.Systeme(g.scenario(sc), JOUR)
    for _ in range(jours):
        s.avancer(JOUR)
    i = next(i for i, c in enumerate(s.corps) if c.nom == corps)
    T = s.periode(i) / JOUR
    assert abs(T - vraie) / vraie < 0.005
    ts = SAGE['scenarios'][sc]['periodes_j'][corps]
    assert abs(T - ts) / ts < 2e-6


def test_iss_et_comete_comme_kepler():
    s = g.Systeme(g.scenario('terre_iss'), 10.0)
    for _ in range(60):
        s.avancer(600.0)
    assert abs(s.periode(1) / 60 - SAGE['kepler_j']['iss_min']) / SAGE['kepler_j']['iss_min'] < 1e-5
    l = g.Systeme(g.scenario('libre'), JOUR)
    for _ in range(1500):
        l.avancer(JOUR)
    assert abs(l.periode(3) / JOUR - SAGE['scenarios']['libre']['periodes_j']['comete']) / 671 < 1e-5


def test_conservation_energie_et_moment_sur_dix_ans():
    s = g.Systeme(g.scenario('soleil_terre_lune'), JOUR)
    duree = 10 * 5 * JOUR / 60          # vitesse ×10, 60 images par seconde
    pire = 0.0
    for _ in range(int(3650 * JOUR / duree)):
        s.avancer(duree)
        pire = max(pire, s.derives()[0])
    assert pire < 1e-9
    assert s.derives()[1] < 1e-12
    assert 0.4 < s.courbure_min and s.courbure_max < 1.6       # toujours tournée vers le Soleil
    assert SAGE['lune_concave']['rapport'] > 2


def test_sans_gravite_ligne_droite():
    s = g.Systeme(g.scenario('terre_lune'), JOUR)
    s.gravite = False
    l0 = s.corps[1].copie()
    s.avancer(5 * JOUR)
    l1 = s.corps[1]
    assert (l1.vx, l1.vy) == (l0.vx, l0.vy)
    assert abs(l1.x - (l0.x + l0.vx * 5 * JOUR)) < 1e-6 and abs(l1.y - (l0.y + l0.vy * 5 * JOUR)) < 1e-3


def test_collision_chute_libre():
    cs = g.scenario('terre_lune')
    cs[1].vx = cs[1].vy = 0.0
    g.recentrer(cs)
    s = g.Systeme(cs, JOUR)
    for _ in range(10):
        if s.collisions:
            break
        s.avancer(JOUR)
    assert [(a, b) for a, b, _ in s.collisions] == [('lune', 'terre')]
    assert not s.corps[1].actif
    assert 4.5 < s.collisions[0][2] / JOUR < 5


def test_retour():
    s = g.Systeme(g.scenario('soleil_terre'), JOUR)
    e = s.instantane()
    s.avancer(100 * JOUR)
    s.restaurer(e)
    assert [(c.x, c.y, c.vx, c.vy) for c in s.corps] == [(c.x, c.y, c.vx, c.vy) for c in e['corps']] and s.t == 0


# ------------------------------------------------------------------ animation (hors écran)
def _anim(**reglages):
    from coupole.modules.anim.animations.gravite_orbites import GraviteOrbites
    a = GraviteOrbites()
    a.resize(1000, 760)
    for k, v in reglages.items():
        w = a._defauts[k][0]
        if hasattr(w, 'setChecked'):
            w.setChecked(v)
        elif hasattr(w, 'findData'):
            w.setCurrentIndex(w.findData(v))
        else:
            w.setValue(v)
    a.image(900, 600)
    return a


def _ecran(a, nom):
    i = next(i for i, c in enumerate(a.sys.corps) if c.nom == nom)
    return a._vers_ecran(*a._pos_dessin(i))


def test_glisser_la_terre_et_la_lune_suit(app_qt):
    from PyQt6.QtCore import QPointF, Qt
    a = _anim(scenario='soleil_terre_lune')
    t, l = a.sys.corps[1].copie(), a.sys.corps[2].copie()
    x, y = _ecran(a, 'terre')
    assert a.presser(QPointF(x, y), Qt.MouseButton.LeftButton)
    a.glisser(QPointF(x - 40, y + 30), -40, 30)
    a.avancer(1.0)
    assert a.sys.t == 0                          # temps suspendu pendant la saisie
    a.relacher(QPointF(x - 40, y + 30))
    t2, l2 = a.sys.corps[1], a.sys.corps[2]
    assert t2.x < t.x
    assert l2.x - t2.x == pytest.approx(l.x - t.x, abs=1.0) and l2.y - t2.y == pytest.approx(l.y - t.y, abs=1.0)
    x2 = t2.x
    a.avancer(3.0)
    a.retour()
    assert a.sys.corps[1].x == x2
    a.close()


def test_fleche_de_vitesse_et_ruban(app_qt):
    from PyQt6.QtCore import QPointF, Qt
    a = _anim(scenario='soleil_terre', vecteurs_vitesse=True)
    v0 = a.sys.corps[1].vy
    x, y = _ecran(a, 'terre')
    tx, ty = a._bout_vitesse(1, x, y)
    assert a.presser(QPointF(tx, ty), Qt.MouseButton.LeftButton)
    a.glisser(QPointF(tx, ty - 40), 0, -40)
    a.relacher(QPointF(tx, ty - 40))
    assert a.sys.corps[1].vy > 1.2 * v0
    a.close()
    b = _anim(scenario='terre_lune', ruban=True)
    assert dict(b.valeurs())['Ruban de mesure'] == '384 400 km'
    X, Y = b._vers_ecran(b.ruban[2], b.ruban[3])
    assert b.presser(QPointF(X, Y), Qt.MouseButton.LeftButton)
    b.glisser(QPointF(X + 50, Y), 50, 0)
    b.relacher(QPointF(X + 50, Y))
    assert b.ruban[2] > 1.1 * g.A_LUNE
    b.close()


def test_vues_echelle_et_modele(app_qt):
    a = _anim(scenario='soleil_terre_lune', mode='echelle')
    (tx, ty), (lx, ly) = _ecran(a, 'terre'), _ecran(a, 'lune')
    assert math.hypot(tx - lx, ty - ly) < 2 and a._rayon(0) < 3      # la Terre et la Lune : un seul point
    a.c_mode.setCurrentIndex(0)
    # hors écran (fenêtre non montrée) : le passage est immédiat ; montrée, une minuterie le fait en douceur
    a.image(900, 600)
    (tx, ty), (lx, ly) = _ecran(a, 'terre'), _ecran(a, 'lune')
    assert math.hypot(tx - lx, ty - ly) > 30 and a._rayon(0) > 20
    a.show()
    a.c_mode.setCurrentIndex(1)
    assert a._transition.isActive()
    from PyQt6.QtWidgets import QApplication
    t0 = time.monotonic()
    while a._transition.isActive() and time.monotonic() - t0 < 5:
        QApplication.processEvents()
        time.sleep(0.01)
    assert not a._transition.isActive() and a.t_mode == 0.0      # arrivé : plus aucune image
    a.close()


def test_valeurs_et_rendu(app_qt, langue):
    a = _anim(scenario='soleil_terre_lune', lune_soleil=True)
    for _ in range(80):
        a.avancer(1.0)                                             # 400 jours
    v = dict(a.valeurs())
    import re
    assert re.match(r'^365,2\d j · vraie : 365,256 j · écart 0,0\d\u202f%$', v['Période mesurée (Terre)'])
    assert re.match(r'^27,3\d j · vraie : 27,322 j · écart 0,\d\d\u202f%$', v['Période mesurée (Lune)'])
    assert re.match(r'^toujours vers le Soleil : de 0,\d\d à 1,\d\d fois celle de la Terre$',
                    v['Courbure de la Lune vue du Soleil'])
    langue('en')
    v = dict(a.valeurs())
    assert v['Measured period (Earth)'].startswith('365.2')
    a.close()


def test_rendu_rapide_tous_scenarios(app_qt):
    """Coût d'une image hors écran (minimum de 8), scénario chargé de trajectoires, toutes les cases : < 5 ms visé,
    borne large sur le NAS chargé et en intégration continue."""
    import os
    mesures = {}
    for sc in g.SCENARIOS:
        a = _anim(scenario=sc, vecteurs_vitesse=True, grille=True, ruban=True, lune_soleil=True)
        for _ in range(200):
            a.avancer(2.0)
        ts = []
        for _ in range(8):
            t0 = time.perf_counter()
            a.image(900, 600)
            ts.append(time.perf_counter() - t0)
        mesures[sc] = min(ts) * 1000
        a.close()
    print(mesures)
    assert max(mesures.values()) < (40 if os.environ.get('CI') else 20)
