"""Inventaire du module Qualité (0.1.9) : aucune image ouverte, au plus un `stat` par image, base d'état d'une
sortie Coupole à la place du parcours (seuls les dossiers des lots sont lus), INDEX_LOTS.csv, mesure qui commence pendant l'inventaire, annulation
pendant l'inventaire, cache jamais écrit sur un partage réseau ni bloqué par une base verrouillée.

Retour de Kevin (0.1.8, partage SMB monté, ≈ 1 800 XISF) : « Inventaire du dossier… » interminable.  Mesuré sur
un vrai partage Samba monté par le client cifs du noyau : 90 s, dont 90,1 s d'attente de verrou SQLite (trois
ouvertures du cache sur le partage, 30 s chacune, « database is locked », fichier de 0 octet)."""
import builtins
import io
import json
import os
import sqlite3
import threading
import time

import pytest

from coupole.core import parcours
from coupole.core.parallele import Plan
from coupole.modules.qualite import moteur


def plan():
    return Plan(1, 1, False, 'x')


def arbre(racine, lots=4, par_lot=7, sous='R'):
    """Images vides (l'inventaire ne lit rien) : racine/Objet_k/<sous>/2025-…xisf."""
    out = {}
    for k in range(lots):
        d = racine / ('Objet_%d' % k) / sous
        d.mkdir(parents=True)
        out[str(d)] = []
        for i in range(par_lot):
            f = d / ('2025-%04d.xisf' % i)
            f.write_bytes(b'')
            out[str(d)].append(str(f))
        (d / 'LOT.txt').write_text('x')               # ni compté ni daté : pas une image
    return out


class _Compteur:
    """Compte les ouvertures et les `stat` d'images (.xisf) faits par CE processus."""

    def __init__(self, monkeypatch):
        self.ouvertures, self.stats, self.listes = [], [], []
        vrai_open, vrai_io_open, vrai_os_open = builtins.open, io.open, os.open
        vrai_stat, vrai_scandir = os.stat, os.scandir
        c = self

        def est_image(p):
            return str(p).lower().endswith('.xisf')

        def open_(f, *a, **k):
            if est_image(f):
                c.ouvertures.append(f)
            return vrai_open(f, *a, **k)

        def os_open(f, *a, **k):
            if est_image(f):
                c.ouvertures.append(f)
            return vrai_os_open(f, *a, **k)

        def stat_(f, *a, **k):
            if est_image(f):
                c.stats.append(str(f))
            return vrai_stat(f, *a, **k)

        class Entree:
            def __init__(self, e):
                self._e = e
                self.name, self.path = e.name, e.path

            def is_dir(self, **k):
                return self._e.is_dir(**k)

            def is_file(self, **k):
                return self._e.is_file(**k)

            def stat(self, **k):
                if est_image(self.path):
                    c.stats.append(self.path)
                return self._e.stat(**k)

        class Liste:
            def __init__(self, d):
                c.listes.append(str(d))
                self._it = vrai_scandir(d)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                self._it.close()

            def __iter__(self):
                return (Entree(e) for e in self._it)

        monkeypatch.setattr(builtins, 'open', open_)
        monkeypatch.setattr(io, 'open', open_)
        monkeypatch.setattr(os, 'open', os_open)
        monkeypatch.setattr(os, 'stat', stat_)
        monkeypatch.setattr(os, 'scandir', Liste)


def _inventaire(racine, a_dater=lambda fs: fs):
    source, lots = None, {}
    for x in moteur.inventorier(racine, a_dater, threading.Event()):
        if x[0] == 'source':
            source = x[1]
        else:
            lots[x[0]] = (x[1], x[2])
    return source, lots


# ------------------------------------------------------------------ budget d'appels système
def test_parcours_aucune_ouverture_un_stat_par_image(tmp_path, monkeypatch):
    attendu = arbre(tmp_path)
    c = _Compteur(monkeypatch)
    source, lots = _inventaire(tmp_path)
    assert source == 'parcours'
    assert {d: v[0] for d, v in lots.items()} == attendu
    assert all(e is not None for v in lots.values() for e in v[1].values())
    assert c.ouvertures == []
    assert sorted(c.stats) == sorted(f for v in attendu.values() for f in v)      # exactement un par image
    # échantillon : seules les images retenues sont datées
    c.stats.clear()
    source, lots = _inventaire(tmp_path, lambda fs: moteur.echantillon(fs, 2))
    assert len(c.stats) == 2 * len(attendu) and c.ouvertures == []


def _sortie_coupole(base, lots=3, par_lot=5, ancienne='/ancienne/machine/SORTIE', windows=False, manque=None):
    """Sortie Coupole déplacée : la base d'état parle de chemins d'une autre machine."""
    (base / '_traitement').mkdir(parents=True)
    db = sqlite3.connect(str(base / '_traitement' / 'etat.sqlite'))
    db.execute('CREATE TABLE images (id TEXT PRIMARY KEY, url TEXT, statut TEXT, essais INTEGER, info TEXT, maj TEXT)')
    sep = '\\' if windows else '/'
    attendu = {}
    n = 0
    for k in range(lots):
        rel = ['09_Galaxies', 'M%d' % k, 'nuit_2025-07-16_T120', 'R']
        d = base.joinpath(*rel)
        d.mkdir(parents=True)
        for i in range(par_lot):
            nom = '20250716-%06d_M%d_R_60s.xisf' % (i, k)
            if manque != (k, i):
                (d / nom).write_bytes(b'')
            attendu.setdefault(str(d), []).append(str(d / nom))
            info = {'final': sep.join([ancienne] + rel + [nom]),
                    'staging': sep.join([ancienne, '_traitement', 'converties', 'id%d.xisf' % n])}
            db.execute('INSERT INTO images VALUES (?,?,?,?,?,?)', ('id%d' % n, 'u', 'ok', 1, json.dumps(info), ''))
            n += 1
    db.execute('INSERT INTO images VALUES (?,?,?,?,?,?)', ('dbl', 'u', 'doublon', 1, '{}', ''))
    db.commit()
    db.close()
    return attendu


@pytest.mark.parametrize('windows', [False, True])
def test_sortie_coupole_inventaire_par_la_base_sans_parcours(tmp_path, monkeypatch, windows):
    base = tmp_path / 'OHP_DU_ECU'
    attendu = _sortie_coupole(base, ancienne='C:\\Users\\k\\Coupole\\OHP_DU_ECU' if windows else
                              '/workspace/Workspace/OHP_DU_ECU', windows=windows)
    (base / '09_Galaxies' / '_traitement').mkdir()                 # cache d'un ancien passage : ignoré
    c = _Compteur(monkeypatch)
    source, lots = _inventaire(base / '09_Galaxies')
    assert source == 'base'
    assert {d: v[0] for d, v in lots.items()} == attendu
    assert sorted(c.listes) == sorted(attendu)                       # seuls les dossiers des lots sont listés
    assert c.ouvertures == [] and len(c.stats) == sum(len(v) for v in attendu.values())
    # un lot seulement (sous-dossier d'une sortie) : la base du parent sert encore
    un = sorted(attendu)[1]
    source, lots = _inventaire(un)
    assert source == 'base' and list(lots) == [un]


def test_sortie_coupole_image_absente_ignoree(tmp_path):
    base = tmp_path / 'S'
    _sortie_coupole(base, lots=2, par_lot=4, manque=(1, 2))
    lot0 = base / '09_Galaxies' / 'M0' / 'nuit_2025-07-16_T120' / 'R'
    (lot0 / 'ajoutee_a_la_main.xisf').write_bytes(b'')                 # pas dans la base, mais dans un lot : vue
    b = moteur.Mesureur(base, plan(), None, ecrire_rapports=False, processus_max=1).lancer()
    assert b['source'] == 'base' and b['absentes'] == 1 and b['n'] == 8 and b['total_dossier'] == 8


def test_index_lots_seuls_les_dossiers_des_lots_sont_lus(tmp_path, monkeypatch):
    attendu = arbre(tmp_path / 'S', lots=3)
    rel = sorted(os.path.relpath(d, tmp_path / 'S') for d in attendu)[:2]
    (tmp_path / 'S' / 'INDEX_LOTS.csv').write_text('\ufeffdossier;type\n' + ''.join('%s;x\n' % r for r in rel),
                                                  encoding='utf-8')
    c = _Compteur(monkeypatch)
    source, lots = _inventaire(tmp_path / 'S')
    assert source == 'index' and sorted(lots) == [str(tmp_path / 'S' / r) for r in rel]
    assert sorted(c.listes) == sorted(lots) and c.ouvertures == []


# ------------------------------------------------------------------ flux, annulation
def _remplir_cache(racine, fichiers):
    c = moteur.CacheMesures(racine)
    for f in fichiers:
        st = os.stat(f)
        c.ecrire(f, st.st_size, st.st_mtime, {'fichier': os.path.basename(f), 'fwhm_px': 3.0})
    c.fermer()


def test_mesure_commence_pendant_l_inventaire(tmp_path, monkeypatch):
    attendu = arbre(tmp_path, lots=6, par_lot=3)
    _remplir_cache(tmp_path, [f for v in attendu.values() for f in v])
    vrai = parcours._lister_dossier

    def lent(d, *a, **k):
        if os.path.basename(d) == 'R' and not d.endswith('Objet_0' + os.sep + 'R'):
            time.sleep(0.4)
        return vrai(d, *a, **k)
    monkeypatch.setattr(parcours, '_lister_dossier', lent)
    ordre = []
    t0 = time.monotonic()
    b = moteur.Mesureur(tmp_path, plan(), None, ecrire_rapports=False,
                        rapporter=lambda ev: ordre.append((ev['type'], ev.get('fini'), time.monotonic() - t0))).lancer()
    assert b['n'] == 18 and b['deja'] == 18
    premiere = next(t for typ, _, t in ordre if typ == 'image')
    fin_inventaire = next(t for typ, fini, t in ordre if typ == 'inventaire' and fini)
    assert premiere < fin_inventaire - 0.2, ordre[:5]
    assert any(typ == 'inventaire' and fini is False for typ, fini, _ in ordre)    # progression visible


def test_annulation_pendant_l_inventaire(tmp_path, monkeypatch):
    arbre(tmp_path, lots=8, par_lot=2)
    vrai = parcours._lister_dossier
    monkeypatch.setattr(parcours, '_lister_dossier', lambda d, *a, **k: (time.sleep(0.5), vrai(d, *a, **k))[1])
    arret = threading.Event()
    t0 = time.monotonic()
    threading.Timer(0.3, arret.set).start()
    b = moteur.Mesureur(tmp_path, plan(), None, arret=arret, ecrire_rapports=False).lancer()
    assert b['annule'] and time.monotonic() - t0 < 2.5


# ------------------------------------------------------------------ cache : jamais sur un partage, jamais bloqué
def test_cache_hors_du_partage_et_ancien_cache_relu(tmp_path, monkeypatch):
    (tmp_path / '_traitement').mkdir()
    ancien = sqlite3.connect(str(tmp_path / '_traitement' / 'qualite.sqlite'))
    ancien.execute('CREATE TABLE mesures (chemin TEXT PRIMARY KEY, taille INTEGER, mtime REAL, mesure TEXT, maj TEXT)')
    ancien.execute("INSERT INTO mesures VALUES ('/a.xisf', 1, 2.0, '{}', '')")
    ancien.commit()
    ancien.close()
    c = moteur.CacheMesures(tmp_path, reseau=True)
    assert not c.chemin.startswith(str(tmp_path)) and c.db is not None
    c.ecrire('/b.xisf', 3, 4.0, {'k': 1})
    assert set(c.tout()) == {'/a.xisf', '/b.xisf'}
    c.fermer()
    with sqlite3.connect(str(tmp_path / '_traitement' / 'qualite.sqlite')) as db:          # rien écrit sur le partage
        assert db.execute('SELECT COUNT(*) FROM mesures').fetchone()[0] == 1


def test_cache_verrouille_repli_local_sans_attendre(tmp_path, monkeypatch):
    """Comme sur un partage cifs dont les verrous de plage échouent : la base ne s'écrit pas → cache local, en
    quelques secondes au plus (0.1.8 : 30 s d'attente, puis aucun cache)."""
    monkeypatch.setattr(moteur, 'ATTENTE_VERROU_S', 0.3)
    (tmp_path / '_traitement').mkdir()
    bloqueur = sqlite3.connect(str(tmp_path / '_traitement' / 'qualite.sqlite'), isolation_level=None)
    bloqueur.execute('BEGIN EXCLUSIVE')
    try:
        t0 = time.monotonic()
        c = moteur.CacheMesures(tmp_path, reseau=False)
        assert time.monotonic() - t0 < 2.0
        assert c.db is not None and not c.chemin.startswith(str(tmp_path))
        c.ecrire('/x.xisf', 1, 1.0, {})
        assert c.compte() == 1
        c.fermer()
    finally:
        bloqueur.execute('ROLLBACK')
        bloqueur.close()
