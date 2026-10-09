"""0.2.1 — possession non reconnue sous Windows (dossier de sortie sur un lecteur réseau).

Retour d'utilisateur : une copie complète de la banque, sur un partage SMB vu par une lettre de lecteur mappée
(``O:\\OHP_DU_ECU``), apparaissait entièrement possédée sous Linux et « tout à télécharger » sous Windows, base
d'état en journal DELETE.  Cause : l'URI SQLite de lecture était construite par ``Path.resolve().as_uri()`` ;
sous Windows, ``resolve()`` remplace la lettre d'un lecteur réseau par le chemin UNC du partage, et ``as_uri()``
en fait ``file://serveur/partage/…`` — autorité non vide que SQLite refuse (« invalid uri authority »).
L'erreur était avalée : base illisible → rien de possédé, sans un mot.

Ce fichier vérifie, partout : la construction de l'URI (lettre, UNC, caractères spéciaux), la lecture par copie
locale (base WAL, partage), l'erreur dite au lieu d'une possession vide, la reconnaissance des fichiers rangés.
Sous Windows (CI) : un vrai partage administratif ``\\\\localhost\\C$`` en UNC ET par une lettre mappée par
``net use`` (``COUPOLE_TEST_LECTEUR_RESEAU``, ``subst`` ne donne pas DRIVE_REMOTE), base WAL puis DELETE, premier
lancement (aucune base de travail) et base de travail ancienne d'un essai antérieur.
"""
import json
import os
import shutil
import sqlite3
from pathlib import Path, PureWindowsPath

import numpy as np
import pytest

from coupole.core import base_partagee as B
from coupole.core.chemins import uri_sqlite_lecture_seule
from coupole.modules.ohp.possession import Possession

from .test_copie_ancienne import DONNEES, _journal, faire_copie

ATTENDUS = {r[0]: r[2] for r in json.loads((DONNEES / 'etat.json').read_text(encoding='utf-8'))}


def _copie(racine: Path, mode='wal') -> Path:
    dest = faire_copie(racine)
    if mode == 'delete':                         # base réécrite par une session récente (journal DELETE)
        db = sqlite3.connect(str(dest / '_traitement' / 'etat.sqlite'))
        db.execute('PRAGMA journal_mode=DELETE')
        db.close()
    tete = (dest / '_traitement' / 'etat.sqlite').read_bytes()[18:20]
    assert tete == (b'\x02\x02' if mode == 'wal' else b'\x01\x01')
    return dest


# ================================================================ URI SQLite
@pytest.mark.parametrize('chemin, uri', [
    (r'O:\OHP_DU_ECU\_traitement\etat.sqlite', 'file:///O:/OHP_DU_ECU/_traitement/etat.sqlite?mode=ro'),
    ('O:/OHP_DU_ECU/_traitement/etat.sqlite', 'file:///O:/OHP_DU_ECU/_traitement/etat.sqlite?mode=ro'),
    (r'\\serveur\partage\OHP_DU_ECU\_traitement\etat.sqlite',
     'file:////serveur/partage/OHP_DU_ECU/_traitement/etat.sqlite?mode=ro'),
    ('//serveur/partage/OHP DU ECU/_traitement/etat.sqlite',
     'file:////serveur/partage/OHP%20DU%20ECU/_traitement/etat.sqlite?mode=ro'),
    (r'D:\Données #1\100%\a?b\etat.sqlite', 'file:///D:/Donn%C3%A9es%20%231/100%25/a%3Fb/etat.sqlite?mode=ro'),
])
def test_uri_windows(chemin, uri):
    assert uri_sqlite_lecture_seule(chemin, windows=True) == uri


def test_uri_unix():
    assert uri_sqlite_lecture_seule('/mnt/partage/OHP DU ECU/é#?.sqlite', windows=False) == \
        'file:///mnt/partage/OHP%20DU%20ECU/%C3%A9%23%3F.sqlite?mode=ro'


def test_cause_l_ancienne_uri_d_un_lecteur_resolu_en_unc_est_refusee():
    """Ce que faisait la 0.2.0 d'un lecteur réseau : `resolve()` → UNC → `as_uri()` → autorité refusée."""
    ancienne = PureWindowsPath(r'\\serveur\partage\OHP_DU_ECU\_traitement\etat.sqlite').as_uri() + '?mode=ro'
    assert ancienne.startswith('file://serveur/')
    with pytest.raises(sqlite3.OperationalError, match='authority'):
        sqlite3.connect(ancienne, uri=True)


def test_uri_ouvre_vraiment(tmp_path):
    d = tmp_path / 'é #%' / '_traitement'
    d.mkdir(parents=True)
    db = sqlite3.connect(str(d / 'etat.sqlite'))
    db.execute('CREATE TABLE t (x)')
    db.execute('INSERT INTO t VALUES (1)')
    db.commit()
    db.close()
    db = sqlite3.connect(uri_sqlite_lecture_seule(str(d / 'etat.sqlite')), uri=True)
    assert db.execute('SELECT x FROM t').fetchall() == [(1,)]
    db.close()


# ================================================================ lecture robuste
@pytest.mark.parametrize('mode', ['wal', 'delete'])
@pytest.mark.parametrize('reseau', [False, True])
def test_possession_reconnue_wal_ou_delete_local_ou_partage(tmp_path, monkeypatch, mode, reseau):
    dest = _copie(tmp_path, mode)
    monkeypatch.setattr(B, 'est_reseau', lambda d: reseau)
    lignes, provenance = B.lire_base(str(dest / '_traitement' / 'etat.sqlite'), 'SELECT id, statut FROM images')
    assert dict(lignes) == ATTENDUS
    assert provenance == ('copie' if (reseau or mode == 'wal') else 'directe')
    poss = Possession.lire(dest)
    assert poss.statuts == ATTENDUS and not poss.erreur
    # la base d'origine n'est jamais modifiée par une lecture
    assert (dest / '_traitement' / 'etat.sqlite').read_bytes()[18:20] == (b'\x02\x02' if mode == 'wal' else b'\x01\x01')


def test_copie_de_lecture_refaite_seulement_si_la_base_change(tmp_path, monkeypatch):
    dest = _copie(tmp_path, 'delete')
    chemin = str(dest / '_traitement' / 'etat.sqlite')
    copies = []
    vraie = B._copier_base
    monkeypatch.setattr(B, '_copier_base', lambda s, d: copies.append(s) or vraie(s, d))
    monkeypatch.setattr(B, 'est_reseau', lambda d: True)
    for _ in range(3):
        assert len(Possession.lire(dest).statuts) == len(ATTENDUS)
    assert len(copies) == 1
    db = sqlite3.connect(chemin)
    db.execute("INSERT INTO images VALUES ('neuve', 'u', 'ok', 1, '{}', '2026-10-09T21:50:00')")
    db.commit()
    db.close()
    os.utime(chemin, ns=(os.stat(chemin).st_mtime_ns + 10**9,) * 2)
    assert Possession.lire(dest).statuts['neuve'] == 'ok'
    assert len(copies) == 2


def test_lecture_directe_refusee_alors_copie(tmp_path, monkeypatch):
    dest = _copie(tmp_path, 'delete')
    chemin = str(dest / '_traitement' / 'etat.sqlite')
    vraie = B._lire_ro

    def refuser(c, *a):
        if os.path.abspath(c) == os.path.abspath(chemin):
            raise sqlite3.OperationalError('unable to open database file')
        return vraie(c, *a)
    monkeypatch.setattr(B, '_lire_ro', refuser)
    assert Possession.lire(dest).statuts == ATTENDUS


def test_base_illisible_dite_et_journalisee(tmp_path, caplog):
    dest = tmp_path / 'OHP_DU_ECU'
    (dest / '_traitement').mkdir(parents=True)
    (dest / '_traitement' / 'etat.sqlite').write_bytes(b'ceci n est pas une base SQLite' * 100)
    with caplog.at_level('INFO'):
        poss, infos = Possession.lire_avec_infos(dest)
    assert poss.statuts == {} and infos == [] and poss.erreur
    assert 'illisible' in caplog.text and str(dest) in caplog.text
    assert not poss.base_absente


def test_journal_dit_le_dossier_et_le_nombre_lu(tmp_path, caplog):
    dest = _copie(tmp_path, 'delete')
    with caplog.at_level('INFO'):
        Possession.lire(dest)
    assert '20 possédée(s) lue(s)' in caplog.text or '20 image(s) possédée(s) lue(s)' in caplog.text
    assert 'lecture directe' in caplog.text


def test_base_absente_avec_fichiers_ranges(tmp_path):
    dest = faire_copie(tmp_path)
    shutil.rmtree(dest / '_traitement')
    poss = Possession.lire(dest)
    assert poss.base_absente and poss.fichiers_sans_base and not poss.erreur
    vide = tmp_path / 'vide'
    vide.mkdir()
    p2 = Possession.lire(vide)
    assert p2.base_absente and not p2.fichiers_sans_base


# ================================================================ reconnaître les fichiers existants
def _copie_sans_base_avec_entetes(racine: Path, avec_url=True) -> Path:
    """Fichiers rangés comme les produit Coupole (adresse d'origine dans l'en-tête), sans `_traitement/`."""
    from coupole.core import xisf
    dest = racine / 'OHP_DU_ECU'
    for l in _journal():
        if not l['destination']:
            continue
        f = dest.joinpath(*l['destination'].split('/'))
        f.parent.mkdir(parents=True, exist_ok=True)
        mc = [('NAXIS1', '4', ''), ('NAXIS2', '4', ''), ('TELESCOP', "'T120'", '')]
        props = [('OHP:Source:URL', 'String', l['url'])] if avec_url else []
        if not avec_url:
            mc.append(('HISTORY', '', 'Coupole : converti de %s' % l['url'].rsplit('/', 1)[1]))
        xisf.ecrire(f, np.zeros((4, 4), '<u2'), mc, props)
    return dest


@pytest.mark.parametrize('avec_url', [True, False])
def test_reconnaitre_les_fichiers_existants(tmp_path, inventaire, avec_url):
    from coupole.modules.ohp.reconnaissance import reconnaitre
    dest = _copie_sans_base_avec_entetes(tmp_path, avec_url)
    attendus = {l['url'] for l in _journal() if l['destination']}
    avant = sorted(p.relative_to(dest) for p in dest.rglob('*') if p.is_file())
    r = reconnaitre(dest, inventaire, processus=1)
    assert r['reconnus'] == len(attendus) == 14 and r['ignores'] == []
    poss, infos = Possession.lire_avec_infos(dest)
    from coupole.modules.ohp.conversion import _ident_url
    assert {i for i, s in poss.statuts.items() if s == 'ok'} == {_ident_url(u) for u in attendus}
    assert all(poss.details[i]['origine'] == 'base' and (dest / poss.details[i]['chemin']).is_file()
               for i in poss.statuts)
    # rien d'autre n'a bougé : seule la base de suivi est apparue
    apres = sorted(p.relative_to(dest) for p in dest.rglob('*') if p.is_file() and '_traitement' not in p.parts)
    assert apres == avant
    r2 = reconnaitre(dest, inventaire, processus=1)              # une seconde fois : rien de neuf
    assert r2['reconnus'] == 0 and r2['deja'] == 14


# ================================================================ interface
def test_bandeau_base_illisible_et_reconnaissance(app_qt, tmp_path, monkeypatch, inventaire):
    from coupole.core import config
    from coupole.modules.ohp import gui
    from .test_catalogue_possession import attendre
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    dest = tmp_path / 'OHP_DU_ECU'
    (dest / '_traitement').mkdir(parents=True)
    (dest / '_traitement' / 'etat.sqlite').write_bytes(b'abime' * 1000)
    p = gui.Panneau()
    try:
        assert attendre(app_qt, lambda: p.inv is not None, 60)
        p.dest.setText(str(dest))
        p._charger_possession()
        assert attendre(app_qt, lambda: p.bandeau_base.isVisibleTo(p))
        assert "La base de suivi de ce dossier n'a pas pu être lue" in p.l_bandeau_base.text()
        assert not p.b_reconnaitre.isVisibleTo(p)
        assert 'Dossier de suivi : %s — base illisible' % dest in p.l_inventaire.text()
        # base retirée, fichiers rangés : proposition de reconnaissance, puis possession reconnue
        shutil.rmtree(dest)
        _copie_sans_base_avec_entetes(tmp_path)
        p._charger_possession()
        assert attendre(app_qt, lambda: p.b_reconnaitre.isVisibleTo(p))
        assert 'pas de base de suivi' in p.l_inventaire.text()
        p.reconnaitre()
        assert attendre(app_qt, lambda: 'Fichiers reconnus : 14' in p.journal.toPlainText(), 60)
        assert attendre(app_qt, lambda: not p.bandeau_base.isVisibleTo(p))
        assert attendre(app_qt, lambda: 'Dossier de suivi : %s — 14 images possédées lues' % dest
                        in p.l_inventaire.text())
    finally:
        from coupole.gui.outils import attendre_taches
        p.arreter()
        attendre_taches(30000)
        app_qt.processEvents()
        p.close()
        p.deleteLater()
        app_qt.processEvents()


def test_rafraichir_l_inventaire_relit_la_possession(app_qt, tmp_path, monkeypatch):
    from coupole.core import config
    from coupole.modules.ohp import gui
    from coupole.modules.ohp.inventaire import Inventaire
    from .test_catalogue_possession import attendre
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    vrai = Inventaire.charger.__func__
    monkeypatch.setattr(Inventaire, 'charger', classmethod(lambda cls, rafraichir_=False: vrai(cls, False)))
    dest = _copie(tmp_path, 'delete')
    p = gui.Panneau()
    try:
        assert attendre(app_qt, lambda: p.inv is not None, 60)
        p.dest.setText(str(tmp_path / 'ailleurs'))
        p._charger_possession()
        assert attendre(app_qt, lambda: p.possession.dest == str(tmp_path / 'ailleurs'))
        assert not p.possession.statuts
        p.dest.setText(str(dest))                 # sans relire : c'est « Rafraîchir l'inventaire » qui relit
        p.charger(True)
        assert attendre(app_qt, lambda: p.possession.statuts == ATTENDUS, 60)
        assert 'Dossier de suivi : %s — 20 images possédées lues' % dest in p.l_inventaire.text()
    finally:
        from coupole.gui.outils import attendre_taches
        p.arreter()
        attendre_taches(30000)
        app_qt.processEvents()
        p.close()
        p.deleteLater()
        app_qt.processEvents()


# ================================================================ Windows : vrai partage, UNC et lettre mappée
def _unc_de(chemin: str) -> str | None:
    """Le dossier vu par le partage administratif de la machine, sous un nom de serveur qui n'est PAS « localhost »
    (SQLite accepte l'autorité « localhost » dans une URI : le défaut de la 0.2.0 ne se verrait pas)."""
    lecteur, reste = os.path.splitdrive(chemin)
    if not lecteur.endswith(':'):
        return None
    for serveur in (os.environ.get('COMPUTERNAME', ''), '127.0.0.1', 'localhost'):
        unc = '\\\\%s\\%s$%s' % (serveur, lecteur[0], reste)
        if serveur and os.path.isdir(unc):
            return unc
    return None


def _vues_windows(tmp_path):
    """[(nom, dossier de travail vu par le partage)] : UNC toujours, lettre mappée si `net use` l'a posée."""
    unc = _unc_de(str(tmp_path))
    if not unc:
        pytest.skip('partage administratif C$ inaccessible')
    vues = [('unc', unc)]
    lettre = os.environ.get('COUPOLE_TEST_LECTEUR_RESEAU', '').rstrip('\\').rstrip(':')
    if lettre:
        lecteur, reste = os.path.splitdrive(str(tmp_path))
        assert lecteur.upper() == 'C:', 'le lecteur réseau de test est mappé sur le partage C$'
        vues.append(('lettre', lettre + ':' + reste))
    return vues


@pytest.mark.skipif(os.name != 'nt', reason='partage Windows réel')
@pytest.mark.parametrize('mode', ['wal', 'delete'])
def test_windows_partage_reel_premier_lancement(tmp_path, mode):
    from coupole.core.chemins import est_reseau
    for nom, racine in _vues_windows(tmp_path):
        local = tmp_path / nom
        _copie(local, mode)
        dest = os.path.join(racine, nom, 'OHP_DU_ECU')
        assert os.path.isfile(os.path.join(dest, '_traitement', 'etat.sqlite'))
        assert est_reseau(dest), (nom, dest)                   # DRIVE_REMOTE pour la lettre, UNC sinon
        print('%s : %s ; realpath = %s ; uri = %s' % (nom, dest, os.path.realpath(dest),
                                                       uri_sqlite_lecture_seule(os.path.join(dest, 'x.sqlite'))))
        poss, infos = Possession.lire_avec_infos(dest)
        assert not poss.erreur, poss.erreur
        assert poss.statuts == ATTENDUS, (nom, mode)
        assert len(infos) == 14 and all(os.path.isfile(os.path.join(dest, poss.details[i]['chemin']))
                                        for i, _ in infos)
        # lecture directe (sans copie) : l'URI de la 0.2.1 ouvre aussi le partage en DELETE
        if mode == 'delete':
            lignes = B._lire_ro(os.path.join(dest, '_traitement', 'etat.sqlite'), 'SELECT id, statut FROM images')
            assert dict(lignes) == ATTENDUS


@pytest.mark.skipif(os.name != 'nt', reason='partage Windows réel')
def test_windows_ancienne_uri_d_un_lecteur_mappe(tmp_path):
    """La cause, sur un vrai lecteur mappé : `resolve()` rend l'UNC, l'URI de la 0.2.0 est refusée par SQLite."""
    vues = dict(_vues_windows(tmp_path))
    if 'lettre' not in vues:
        pytest.skip('pas de lecteur réseau mappé (COUPOLE_TEST_LECTEUR_RESEAU)')
    _copie(tmp_path / 'lettre', 'delete')
    chemin = os.path.join(vues['lettre'], 'lettre', 'OHP_DU_ECU', '_traitement', 'etat.sqlite')
    resolu = Path(chemin).resolve()
    print('resolve() :', resolu)
    assert str(resolu).startswith('\\\\'), resolu
    with pytest.raises(sqlite3.OperationalError):
        sqlite3.connect(resolu.as_uri() + '?mode=ro', uri=True).execute('SELECT 1 FROM images').fetchall()


@pytest.mark.skipif(os.name != 'nt', reason='partage Windows réel')
def test_windows_base_de_travail_d_un_essai_anterieur(tmp_path):
    """Une base de travail locale existe déjà (essai antérieur, base du partage alors en WAL et à moitié remplie),
    puis la base du partage est réécrite ailleurs (DELETE, complète) : la possession suit le partage, la base de
    travail n'écrase rien."""
    from coupole.modules.ohp.pilote import Etat
    for nom, racine in _vues_windows(tmp_path):
        local = tmp_path / nom
        dest_local = _copie(local, 'wal')
        chemin_local = dest_local / '_traitement' / 'etat.sqlite'
        db = sqlite3.connect(str(chemin_local))                 # essai antérieur : base partielle
        db.execute("DELETE FROM images WHERE id IN (SELECT id FROM images LIMIT 12)")
        db.commit()
        db.close()
        dest = os.path.join(racine, nom, 'OHP_DU_ECU')
        e = Etat(os.path.join(dest, '_traitement', 'etat.sqlite'))   # base de travail créée (premier essai)
        assert e.base.mode == 'local'
        e.fermer()
        assert len(Possession.lire(dest).statuts) == len(ATTENDUS) - 12
        # la base du partage est réécrite ailleurs (autre machine), complète, en DELETE
        refaite = _copie(tmp_path / (nom + '_complete'), 'delete') / '_traitement' / 'etat.sqlite'
        shutil.copyfile(refaite, str(chemin_local) + '.neuf')
        os.replace(str(chemin_local) + '.neuf', chemin_local)
        for suffixe in ('-wal', '-shm'):
            if os.path.exists(str(chemin_local) + suffixe):
                os.remove(str(chemin_local) + suffixe)
        poss = Possession.lire(dest)
        assert not poss.erreur and poss.statuts == ATTENDUS, nom
        e = Etat(os.path.join(dest, '_traitement', 'etat.sqlite'))   # nouvelle session : partage plus récent repris
        assert len(e.statuts()) == len(ATTENDUS)
        e.fermer()
        assert Possession.lire(dest).statuts == ATTENDUS
