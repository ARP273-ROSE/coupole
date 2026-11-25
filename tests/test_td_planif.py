"""Planificateur de parallaxe (Calculateurs de TD) : créneaux contre skyfield (références figées par
outils/verif_planif/references_skyfield.py), formules contre SageMath (outils/verif_planif/verif_planif_sage.py),
exports, ligne de commande, panneau."""
import datetime as D
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from coupole.modules.td import planif as P

ICI = Path(__file__).parent
REF = json.loads((ICI / 'td_planif_reference.json').read_text(encoding='utf-8'))
UTC = D.timezone.utc
S1, S2 = (P.Site(*x) for x in REF['sites'])
def _t(x):
    return D.datetime.strptime(x, '%Y%m%dT%H%M%SZ').replace(tzinfo=UTC)


DEBUT = _t(REF['debut'])
TLE = tuple(REF['tle'])


@pytest.fixture(scope='module')
def iss():
    return P.chercher(S1, S2, P.Criteres('iss', DEBUT, jours=7, tle=TLE))


@pytest.fixture(scope='module')
def lune():
    return P.chercher(S1, S2, P.Criteres('lune', DEBUT, jours=60))


def test_iss_contre_skyfield(iss):
    """Mêmes créneaux, mêmes instants ; hauteurs et azimuts à 0,15° de skyfield (SGP4 + ITRS complet)."""
    att = {x['instant']: x for x in REF['iss']}
    assert len(iss['creneaux']) == len(att)
    for c in iss['creneaux']:
        r = att[c.meilleur.strftime('%Y%m%dT%H%M%SZ')]
        for n in (0, 1):
            assert abs(c.h[n] - r['h'][n]) < 0.01            # non-régression (UT1 − UTC et DE440 varient selon la machine)
            assert abs(c.h[n] - r['skyfield_h_az'][n][0]) < 0.15                    # skyfield
            assert abs((c.az[n] - r['skyfield_h_az'][n][1] + 180) % 360 - 180) < 0.15
        assert c.entre == r['entre']
    assert iss['creneaux'][0].note >= iss['creneaux'][-1].note


def test_iss_conditions(iss):
    for c in iss['creneaux']:
        assert min(c.h) >= 20 and max(c.soleil) <= -6
        assert c.debut <= c.meilleur <= c.fin
        assert 300 < c.altitude_km < 500
        assert c.synchro_s > 0 and c.vitesse_deg_s > 0
        assert len(c.magnitude) == 2 and all(-5 < m < 5 for m in c.magnitude)


def test_iss_meilleur_creneau_formule_sujet(iss):
    """Le premier créneau est celui où la formule simple du sujet marche : ISS entre les deux lieux, près du plan
    commun, erreur de quelques %."""
    c = iss['creneaux'][0]
    assert c.entre and c.ecart_plan_deg < 5 and abs(c.erreur_sujet_pct) < 3


def test_lune_contre_references(lune):
    att = {x['instant']: x for x in REF['lune']}
    assert len(lune['creneaux']) == len(att)
    for c in lune['creneaux']:
        r = att[c.meilleur.strftime('%Y%m%dT%H%M%SZ')]
        assert c.etoile['nom'] == r['etoile']['nom']
        for n in (0, 1):
            assert abs(c.h[n] - r['h'][n]) < 0.02          # DE440 ou ERFA selon la machine
            assert abs(c.h[n] - r['skyfield_h'][n]) < 0.02
        assert abs(c.phase - r['skyfield_phase']) < 0.01
        assert abs(c.etoile['delta_arcmin'] - r['etoile']['delta_arcmin']) < 0.05
        assert c.phase <= 0.95 and min(c.h) >= 20 and max(c.soleil) <= -6
        assert c.etoile['sep1'] <= 5 and c.etoile['sep2'] <= 5 and c.etoile['V'] <= 4.5


def test_formules_sage():
    """Valeurs de outils/verif_planif/verif_planif_sage.py (SageMath, 80 bits)."""
    B = P.base(S1, S2)
    assert abs(B['corde_km'] - 390.866461) < 1e-5
    assert abs(B['corde_km'] / math.radians(180 - 66.0 - 56.9) - 392.207) < 1e-3
    import numpy as np
    for (d, b), m in zip(((450, 30), (1200, 90), (800, 120)), (-3.3962, -0.1612, 0.1219)):
        assert abs(float(P.magnitude_iss(np.array([d]), np.array([b]))[0]) - m) < 1e-4
    assert abs(B['corde_km'] / 384400 * 180 / math.pi * 60 - 3.49558) < 1e-5


def test_erreur_sujet():
    B = P.base(S1, S2)
    assert P.erreur_sujet(B, 45.0, 45.0, False, 400.0) is None          # 2α nul
    e = P.erreur_sujet(B, 60.0, 60.0, True, B['corde_km'] / math.radians(60.0))
    assert abs(e) < 1e-9


def test_plages():
    import numpy as np
    assert P._plages(np.array([0, 1, 1, 0, 1], bool)) == [(1, 2), (4, 4)]
    assert P._plages(np.zeros(3, bool)) == []


def test_exports(iss, lune):
    for r in (iss, lune):
        t = P.csv(r)
        lignes = t.strip().split('\n')
        assert len(lignes) == len(r['creneaux']) + 1
        assert all(l.count(';') == lignes[0].count(';') for l in lignes)
        i = P.ics(r)
        assert i.startswith('BEGIN:VCALENDAR') and i.count('BEGIN:VEVENT') == len(r['creneaux'])
        assert '\r\n' in i


def test_erreurs():
    with pytest.raises(P.ErreurPlanif):
        P.chercher(S1, S2, P.Criteres('mars', DEBUT))
    with pytest.raises(P.ErreurPlanif):
        P.chercher(S1, S2, P.Criteres('iss', DEBUT, tle=None))


def test_etoiles():
    u, V, noms = P.etoiles()
    assert len(V) > 2500 and V.max() <= 5.5
    k = noms.index('α Tau')
    assert abs(V[k] - 0.85) < 1e-9


def test_ligne_de_commande(tmp_path):
    from coupole.modules.td import tle
    env = dict(os.environ, COUPOLE_HOME=str(tmp_path), COUPOLE_SANS_RESEAU='1')
    code = ('import os,sys;from coupole.modules.td import tle;tle.garder(%r);from coupole.cli import main;'
            'sys.exit(main(sys.argv[1:]))' % (TLE,))
    ics = tmp_path / 'c.ics'
    r = subprocess.run([sys.executable, '-c', code, '--lang', 'fr', 'td', 'planifier', '--p1', '48.8366 N 2.3360 E', '--alt1', '67',
                        '--p2', '45.76 N 4.84 E', '--alt2', '170', '--debut', '2026-11-25', '--jours', '7',
                        '--ics', str(ics)], capture_output=True, text=True, env=env, cwd=ICI.parent, timeout=300)
    assert r.returncode == 0, r.stderr
    assert '2026-11-28 16:5' in r.stdout and 'note' in r.stdout
    assert ics.read_text(encoding='utf-8').count('BEGIN:VEVENT') == 7
    _ = tle


def test_panneau(qapp_planif):
    from coupole.modules.td.gui import Panneau
    t = Panneau()
    t.liste.setCurrentRow(1)
    p = t.planif
    p.exemple()
    p.e_debut.setText('2026-11-25')
    p.c_cible.setCurrentIndex(p.c_cible.findData('iss'))
    p.s_jours.setValue(3)
    p.chercher()
    import time
    fin = time.time() + 120
    while (p.res is None or not p.b_chercher.isEnabled()) and time.time() < fin:
        qapp_planif.processEvents()
        time.sleep(0.01)
    assert p.res is not None and p.tableau.rowCount() == len(p.res['creneaux'])
    assert p.detail.toPlainText()
    p.c_cible.setCurrentIndex(p.c_cible.findData('lune'))
    assert not p.g_lune.isHidden() and p.s_jours.maximum() == 400
    assert t.aide_html() == p.aide_html()
    t.close()


@pytest.fixture
def qapp_planif(tmp_path, monkeypatch):
    monkeypatch.setenv('QT_QPA_PLATFORM', os.environ.get('QT_QPA_PLATFORM', 'offscreen'))
    monkeypatch.setenv('COUPOLE_SANS_RESEAU', '1')
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(['coupole'])
    from coupole.modules.td import tle
    monkeypatch.setattr(tle, 'dossier', lambda: tmp_path)
    tle.garder(TLE)
    return app


def test_tendance_iss():
    """Tendance (90 jours au plus) : classement par date, marge qui croît avec l'âge du TLE, mêmes passages que la
    recherche précise sur la première semaine."""
    r = P.chercher(S1, S2, P.Criteres('iss', DEBUT, jours=30, tle=TLE, tendance=True))
    cs = r['creneaux']
    assert r['tendance'] and 'pl_a_tendance' in r['alertes'] and len(cs) > 15
    assert [c.meilleur for c in cs] == sorted(c.meilleur for c in cs)
    assert cs[-1].marge_s > cs[0].marge_s and cs[-1].marge_s > 120 and 'pl_r_indicatif' in cs[-1].remarques
    precis = P.chercher(S1, S2, P.Criteres('iss', DEBUT, jours=7, tle=TLE))
    semaine = [c for c in cs if c.meilleur < DEBUT + D.timedelta(days=7)]
    assert len(semaine) == len(precis['creneaux'])
    for a, b in zip(semaine, sorted(precis['creneaux'], key=lambda c: c.meilleur)):
        assert abs((a.meilleur - b.meilleur).total_seconds()) <= 10          # pas de 10 s au lieu de 5 s
    assert P.Criteres('iss', DEBUT, jours=200, tle=TLE, tendance=True) and P.JOURS_MAX['tendance'] == 90


def test_choisir_un_lieu(qapp_planif, monkeypatch):
    """« Carte / adresse… » : adresse (Nominatim simulé) → résultat → altitude (Open-Meteo simulé) ; clic sur la carte ;
    champs remplis dans le format que relit le lecteur de coordonnées."""
    import time
    from PyQt6.QtWidgets import QDialog, QLineEdit
    from coupole.modules.td import coordonnees as K
    from coupole.modules.td import gui_lieu as L
    monkeypatch.setattr(L, 'geocoder', lambda t, lg='fr': [{'nom': 'Observatoire, Paris, France', 'court': 'Paris',
                                                            'lat': 48.8366, 'lon': 2.3360}])
    monkeypatch.setattr(L, 'altitude', lambda lat, lon: 62.0)

    def attendre(cond):
        fin = time.time() + 20
        while not cond() and time.time() < fin:
            qapp_planif.processEvents()
            time.sleep(0.01)

    d = L.DialogueLieu(None)
    d.e_adresse.setText('Observatoire de Paris')
    d.chercher()
    attendre(lambda: d.choix is not None and d.choix['alt'] is not None)
    assert d.choix == {'lat': 48.8366, 'lon': 2.3360, 'alt': 62.0, 'nom': 'Paris'}
    d.carte.lieu_clique.emit(2.34, 48.84)                       # un clic tout près : le lieu est affiné, nom gardé
    attendre(lambda: d.choix['lat'] == 48.84 and d.choix['alt'] is not None)
    assert d.choix['nom'] == 'Paris'
    d.carte.lieu_clique.emit(4.84, 45.76)                       # un clic loin : autre lieu, sans nom
    attendre(lambda: d.choix['lat'] == 45.76 and d.choix['alt'] is not None)
    assert d.choix['lon'] == 4.84 and d.choix['nom'] == ''
    d.close()
    assert L.texte_position(-33.86, -70.5) == '33.86000 S, 70.50000 W'
    p = K.lire_position(L.texte_position(-33.86, -70.5))
    assert (p.lat, p.lon) == (-33.86, -70.5)
    # choisir() remplit position, altitude et nom (sans écraser un nom déjà saisi)
    pos, alt, nom = QLineEdit(), QLineEdit(), QLineEdit('Mon site')
    monkeypatch.setattr(L.DialogueLieu, 'exec', lambda self: (self._poser(45.76, 4.84, 170.0, 'Lyon', chercher_alt=False),
                                                              QDialog.DialogCode.Accepted)[1])
    assert L.choisir(None, pos, alt, nom)
    assert pos.text() == '45.76000 N, 4.84000 E' and alt.text() == '170' and nom.text() == 'Mon site'
