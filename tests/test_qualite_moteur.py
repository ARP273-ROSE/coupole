"""Moteur du module Qualité sur un dossier simulé de 300 petits XISF : processus parallèles, résultats incrémentaux
(CSV écrit au fil de l'eau), cache et reprise, annulation immédiate, échantillon par lot, temps restant cohérent,
détection de dossier réseau, estimation avant lancement."""
import os
import threading
import time

import numpy as np
import pytest

from coupole.core import xisf
from coupole.core.parallele import Plan
from coupole.modules.qualite import mesures as M, moteur, rapport

from .synthetique import image

pytestmark = pytest.mark.skipif(not M.disponible(), reason='sep absent (dépendance facultative)')

N_LOTS, PAR_LOT = 6, 50


@pytest.fixture(scope='module')
def dossier(tmp_path_factory):
    """6 lots de 50 XISF 160 × 160 (5 étoiles, FWHM de 3 à 5 px), nommés dans l'ordre chronologique."""
    racine = tmp_path_factory.mktemp('qualite')
    rng = np.random.default_rng(3)
    for lot in range(N_LOTS):
        d = racine / ('Objet_%d' % lot) / 'T120' / 'R'
        d.mkdir(parents=True)
        for k in range(PAR_LOT):
            a = image(n=160, fwhm=3.0 + 0.4 * lot, etoiles=5, seed=int(rng.integers(1 << 30)), fond=500.0, bruit=8.0)
            xisf.ecrire(str(d / ('20250716-%06d_img.xisf' % (k * 30))), np.clip(a, 0, 65535).astype('<u2'),
                        [('EXPTIME', '30.0', ''), ('PIXSCALE', '0.77', '')])
    return racine


def plan():
    return Plan(telechargements=1, conversions=2, econome=False, raison='x')


def lancer(racine, rapporter=None, arret=None, ech=None, ecrire=True, processus_max=None):
    evts = []
    m = moteur.Mesureur(racine, plan(), ech, rapporter=lambda ev: (evts.append(ev), rapporter(ev) if rapporter else None),
                        arret=arret, ecrire_rapports=ecrire, processus_max=processus_max)
    return m.lancer(), evts


def test_echantillon_repartit_dans_le_temps():
    imgs = list(range(50))
    assert moteur.echantillon(imgs, 5) == [0, 12, 24, 37, 49]
    assert moteur.echantillon(imgs, 1) == [25] and moteur.echantillon(imgs, 0) == imgs
    assert moteur.echantillon(imgs, 100) == imgs and moteur.echantillon(imgs[:3], 5) == [0, 1, 2]
    assert moteur.echantillon(imgs, 2) == [0, 49]


def test_dossier_local_n_est_pas_reseau(tmp_path):
    assert moteur.est_reseau(tmp_path) is False
    assert moteur.est_reseau('/chemin/qui/n/existe/pas') is False


def test_mesure_complete_puis_cache_et_reprise(dossier):
    t0 = time.monotonic()
    b, evts = lancer(dossier)
    assert b['n'] == N_LOTS * PAR_LOT and b['mesurees'] == N_LOTS * PAR_LOT and b['deja'] == 0 and not b['annule']
    assert b['lots'] == N_LOTS and b['echecs'] == 0 and b['processus'] == 2
    debut = next(e for e in evts if e['type'] == 'debut')
    assert debut['total'] == 300 and debut['processus'] == 2 and debut['reseau'] is False
    # chaque image : un événement, et le CSV de son lot écrit au fil de l'eau (51 lignes à la fin)
    assert sum(1 for e in evts if e['type'] == 'image') == 300
    for lot in range(N_LOTS):
        d = dossier / ('Objet_%d' % lot) / 'T120' / 'R'
        assert (d / 'QUALITE.csv').exists() and (d / 'QUALITE.txt').exists()
        lignes = (d / 'QUALITE.csv').read_text(encoding='utf-8-sig').splitlines()
        assert len(lignes) == PAR_LOT + 1
        assert not list(d.glob('*.tmp'))
    # progression agrégée : ≤ 10 Hz, temps restant qui décroît, dernier événement complet
    prog = [e for e in evts if e['type'] == 'progression']
    assert prog and prog[-1]['fait'] == 300
    duree = time.monotonic() - t0
    assert len(prog) <= 10 * duree + 5
    etas = [e['eta_s'] for e in prog if e['eta_s'] is not None]
    assert etas and etas[-1] < 2.0 and etas[0] >= etas[-1]
    assert prog[-1]['debit'] > 0
    # FWHM retrouvée (3 à 5 px selon le lot)
    lignes_lot0 = b['lignes'][str(dossier / 'Objet_0' / 'T120' / 'R')]
    fw = [l['fwhm_px'] for l in lignes_lot0 if l.get('fwhm_px')]
    assert len(fw) >= 25 and 2.0 < np.median(fw) < 4.5                 # peu d'étoiles isolées sur 160 px, mais l'ordre y est
    # cache : relancer ne mesure rien, tout vient du cache, les CSV sont réécrits à l'identique
    c = moteur.CacheMesures(dossier)
    assert c.compte() == 300
    c.fermer()
    assert (dossier / '_traitement' / 'qualite.sqlite').exists()
    b2, evts2 = lancer(dossier)
    assert b2['mesurees'] == 0 and b2['deja'] == 300 and b2['n'] == 300
    assert all(e['deja'] for e in evts2 if e['type'] == 'image')
    assert b2['duree'] < 5


def test_annulation_immediate_puis_reprise(dossier, tmp_path):
    """Annuler après quelques images : fin rapide, processus terminés ; relancer finit le reste sans refaire."""
    import shutil
    racine = tmp_path / 'copie'
    shutil.copytree(dossier / 'Objet_1', racine / 'A')
    shutil.copytree(dossier / 'Objet_2', racine / 'B')
    arret = threading.Event()
    vues = []

    def rapporter(ev):
        if ev['type'] == 'image':
            vues.append(ev)
            if len(vues) >= 5:
                arret.set()
    t0 = time.monotonic()
    b, evts = lancer(racine, rapporter, arret)
    assert b['annule'] and 5 <= b['n'] < 100 and time.monotonic() - t0 < 30
    b2, evts2 = lancer(racine)
    assert not b2['annule'] and b2['n'] == 100 and b2['deja'] >= 5 and b2['mesurees'] == 100 - b2['deja']
    for d in ('A', 'B'):
        assert len((racine / d / 'T120' / 'R' / 'QUALITE.csv').read_text(encoding='utf-8-sig').splitlines()) == 51


def test_echantillon_par_lot(dossier, tmp_path):
    import shutil
    racine = tmp_path / 'ech'
    shutil.copytree(dossier / 'Objet_3', racine / 'C')
    shutil.copytree(dossier / 'Objet_4', racine / 'D')
    b, evts = lancer(racine, ech=5)
    assert b['n'] == 10 and b['lots'] == 2
    debut = next(e for e in evts if e['type'] == 'debut')
    assert debut['echantillon'] == 5 and debut['total'] == 10 and debut['total_dossier'] == 100
    for d in ('C', 'D'):
        lignes = (racine / d / 'T120' / 'R' / 'QUALITE.csv').read_text(encoding='utf-8-sig').splitlines()
        assert len(lignes) == 6
        noms = [l.split(';')[0] for l in lignes[1:]]
        assert noms[0] == '20250716-000000_img.xisf' and noms[-1] == '20250716-%06d_img.xisf' % ((PAR_LOT - 1) * 30)
    # planifier / estimer_duree : ce qui reste et la durée annoncée
    p = moteur.planifier(racine, None)
    assert p['total_dossier'] == 100 and p['retenus'] == 100 and p['deja'] == 10 and p['a_mesurer'] == 90
    p['chemin'] = str(racine)
    est = moteur.estimer_duree(p, processus=2, n_essai=3)
    assert est['essais'] == 3 and est['par_image_s'] > 0 and est['duree_s'] >= 0
    assert moteur.planifier(racine, None)['deja'] == 13          # les essais sont allés au cache


def test_image_illisible_n_arrete_pas(tmp_path):
    d = tmp_path / 'lot'
    d.mkdir()
    (d / 'a.xisf').write_bytes(b'pas un xisf')
    a = image(n=96, fwhm=3.0, etoiles=10, seed=5)
    xisf.ecrire(str(d / 'b.xisf'), np.clip(a, 0, 65535).astype('<u2'), [])
    b, evts = lancer(tmp_path)
    assert b['n'] == 2 and b['echecs'] == 1 and not b['annule']
    assert moteur.CacheMesures(tmp_path).compte() == 1              # l'échec n'est pas mis en cache


def test_processus_limites_sur_un_partage(monkeypatch):
    assert moteur.processus_pour(Plan(1, 6, False, 'x'), reseau=True) == moteur.LECTEURS_RESEAU_MAX
    assert moteur.processus_pour(Plan(1, 6, False, 'x'), reseau=False) == 6
    assert moteur.processus_pour(Plan(1, 6, False, 'x'), reseau=False, maximum=2) == 2
    assert moteur.processus_pour(Plan(2, 1, True, 'x'), reseau=False) == 1


def test_cli_qualite(dossier, capsys, tmp_path):
    from coupole import cli
    import shutil
    racine = tmp_path / 'cli'
    shutil.copytree(dossier / 'Objet_5', racine / 'E')
    for f in (racine / 'E' / 'T120' / 'R').glob('QUALITE.*'):
        f.unlink()                                   # rapports copiés avec le lot du premier test
    assert cli.main(['--lang', 'fr', 'qualite', str(racine), '--echantillon', '3', '--processus', '1']) == 0
    out = capsys.readouterr().out
    assert 'Échantillon : 3 par lot' in out and 'Terminé : 3 image(s)' in out and 'FWHM médiane' in out
    assert not (racine / 'E' / 'T120' / 'R' / 'QUALITE.csv').exists()          # sans --ecrire
    assert cli.main(['--lang', 'en', 'qualite', str(racine), '--sample', '3', '--write']) == 0
    assert 'from the cache' in capsys.readouterr().out
    assert (racine / 'E' / 'T120' / 'R' / 'QUALITE.csv').exists()
