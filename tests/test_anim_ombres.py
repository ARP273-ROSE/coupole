"""Simulateur des ombres d'éclipse (0.7.1) : type d'éclipse par la géométrie réelle (eclipses_geo.py, identique au
web : tests/eclipses_geo_cas.json), les 133 éclipses de la table retrouvées à leur maximum (géométrie DE440),
rejeu (Lune replacée), cônes de la Lune dessinés, vue 3D tournante, glisser aberrant sans dégât."""
from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

from coupole.modules.anim import eclipses_geo as G

CAS = json.loads((Path(__file__).with_name('eclipses_geo_cas.json')).read_text('utf-8'))
T = {'total': 'totale', 'annular': 'annulaire', 'hybrid': 'hybride', 'partial': 'partielle', 'penumbral': 'penombrale'}


def test_identique_au_web():
    for genre, nom, x, delta, attendu in CAS['cas']:
        r = G.eclipse_soleil(x, delta) if genre == 'soleil' else G.eclipse_lune(x, delta)
        assert r['type'] == attendu['type'], nom
        for k, v in attendu.items():
            if isinstance(v, (int, float)):
                assert math.isclose(r[k], v, rel_tol=1e-12, abs_tol=1e-9), (nom, k)
    for p, n, attendu in CAS['orbite']:
        assert all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-6) for a, b in zip(G.position_orbite(G.D_LUNE_KM, p, n), attendu))


def test_table_retrouvee():
    from coupole.modules.anim.animations.ombres import geometrie_eclipses
    geo = geometrie_eclipses()
    assert len(geo) == 133
    for cle, e in geo.items():
        delta = abs(e['gamma']) * G.R_TERRE_KM
        x = math.sqrt(e['d_km'] ** 2 - delta ** 2)
        r = G.eclipse_soleil(-x, delta, e['s_km']) if cle[0] == 'S' else G.eclipse_lune(x, delta, e['s_km'])
        assert r['type'] == T[e['type']], cle


def test_cas_de_reference():
    assert G.eclipse_soleil(-G.PERIGEE_MIN_KM, 0.0)['type'] == 'totale'
    assert G.eclipse_soleil(-G.APOGEE_MAX_KM, 0.0)['type'] == 'annulaire'
    assert G.eclipse_soleil(-G.PERIGEE_MIN_KM, 0.8 * G.R_TERRE_KM)['type'] == 'totale'     # gamma 0,8 : centrale
    assert G.eclipse_soleil(-G.D_LUNE_KM, 1.3 * G.R_TERRE_KM)['type'] == 'partielle'
    assert G.eclipse_soleil(-G.D_LUNE_KM, 3 * G.R_TERRE_KM)['type'] == 'aucune'
    assert G.eclipse_lune(G.D_LUNE_KM, 0.0)['type'] == 'totale'
    assert G.eclipse_lune(G.D_LUNE_KM, 1.1 * G.R_TERRE_KM)['type'] == 'penombrale'


def test_rejeu_et_rendu(app_qt):
    from PyQt6.QtCore import QPointF, QRectF
    from PyQt6.QtGui import QImage, QPainter
    from coupole.modules.anim.animations import ombres as O
    a = O.OmbresEclipse()
    a.resize(1000, 700)
    # rejouer 5 éclipses de types différents : type au maximum = table ; Lune replacée
    vus = set()
    for i in range(1, a.rejouer.count()):
        cle = a.rejouer.itemData(i)
        rj = O.rejeu(cle)
        t = T[rj['e'][3]]
        if (cle[0], t) in vus:
            continue
        vus.add((cle[0], t))
        a.rejouer.setCurrentIndex(i)
        et = a.etat()
        assert (et['soleil'] if cle[0] == 'S' else et['lune'])['type'] == t, cle
        assert math.isclose(et['distance_km'], rj['g']['d_km'], rel_tol=1e-6)
        a.instant.setValue(1.0)
        et = a.etat()
        assert (et['soleil'] if cle[0] == 'S' else et['lune'])['type'] == 'aucune'
    assert len(vus) >= 5
    a.rejouer.setCurrentIndex(0)
    img = QImage(1000, 700, QImage.Format.Format_ARGB32)
    p = QPainter(img)
    a.dessiner(p, QRectF(0, 0, 1000, 700))
    p.end()
    # glisser aberrant de la Lune : jamais de valeur non finie
    r = a._cote
    e = a._ecran(r)
    assert a.presser(QPointF(e['lx'], e['ly']), 'gauche')
    for x, y in ((1e9, -1e9), (float('nan'), 3), (e['ex'], e['ey'])):
        a.glisser(QPointF(x, y), 1, 1)
    assert all(math.isfinite(v) for v in a.lune)
    a.relacher(QPointF(0, 0))
    a.deleteLater()


def test_donnees_compressees():
    with gzip.open(Path(G.__file__).with_name('donnees') / 'eclipses_geometrie.json.gz', 'rt', encoding='utf-8') as f:
        d = json.load(f)
    assert d['distances_lune']['perigee_min']['km'] == G.PERIGEE_MIN_KM
    assert d['distances_lune']['apogee_max']['km'] == G.APOGEE_MAX_KM
