"""Base d'état sur un partage réseau (0.1.10) : base de travail locale recopiée sur le partage.

Le partage est simulé par un dossier local déclaré « réseau » (ou par l'échec d'écriture de SQLite, simulé) ; un
vrai partage SMB monté par cifs est essayé si ``COUPOLE_TEST_SMB`` donne un dossier inscriptible dessus (lent,
sauté en CI), et un vrai chemin UNC sous Windows (``\\\\localhost\\C$``)."""
import json
import os
import shutil
import sqlite3
import time

import pytest

from coupole.core import base_partagee as B
from coupole.modules.ohp.pilote import Etat


def _base(tmp_path, nom='nas'):
    return str(tmp_path / nom / 'OHP_DU_ECU' / '_traitement' / 'etat.sqlite')


def _lire(chemin, sql='SELECT id, statut FROM images'):
    from coupole.core.chemins import uri_sqlite_lecture_seule
    db = sqlite3.connect(uri_sqlite_lecture_seule(chemin), uri=True)
    try:
        return dict(db.execute(sql).fetchall())
    finally:
        db.close()


def _remplir_direct(chemin, lignes):
    e = Etat(chemin, reseau=False)
    for i, st in lignes.items():
        e.ecrire(i, 'https://x/%s.fits' % i, st, {'objet': 'M31'}, 1)
    e.fermer()


def _ecrire_ailleurs(chemin, lignes):
    """Un autre écrivain (autre machine, NAS) remplace la base du partage."""
    tmp = chemin + '.autre'
    shutil.copyfile(chemin, tmp)
    db = sqlite3.connect(tmp)
    for i, st in lignes.items():
        db.execute('INSERT OR REPLACE INTO images VALUES (?,?,?,?,?,?)', (i, 'u', st, 1, '{}', '2026-10-09T12:00:00'))
    db.commit()
    db.close()
    time.sleep(0.01)
    os.replace(tmp, chemin)
    st = os.stat(chemin)
    os.utime(chemin, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9))     # date distincte même sur un FS grossier


def test_partage_base_locale_puis_recopie(tmp_path):
    p = _base(tmp_path)
    _remplir_direct(p, {'a': 'ok', 'b': 'echec'})
    avis = []
    e = Etat(p, 1.0, reseau=True, rapporter=lambda c, **v: avis.append((c, v)))
    assert e.locale and e.base.mode == 'local'
    assert os.path.dirname(e.base.locale) != os.path.dirname(p)
    assert e.statuts() == {'a': 'ok', 'b': 'echec'}            # copiée depuis le partage
    cles = [c for c, _ in avis]
    assert cles == ['base_locale_copiee', 'base_locale_avis']
    assert avis[1][1]['secondes'] == 30
    e.ecrire('c', 'u', 'ok', {}, 1)
    e.ecrire('b', 'u', 'ok', {}, 2)
    assert _lire(p) == {'a': 'ok', 'b': 'echec'}               # rien d'écrit sur le partage avant la recopie
    e.fermer()
    assert _lire(p) == {'a': 'ok', 'b': 'ok', 'c': 'ok'}
    assert _lire(p, 'SELECT cle, valeur FROM meta')[B.CLE_VERSION] == '1'
    assert sorted(os.listdir(os.path.dirname(p))) == ['etat.sqlite']    # aucun temporaire, aucun journal
    assert B.chemin_lecture(p) == e.base.locale                # à jour : les lecteurs lisent la copie locale


def test_recopie_periodique_pendant_la_session(tmp_path):
    p = _base(tmp_path)
    e = Etat(p, 0.0, reseau=True, intervalle=0.0)
    e.ecrire('a', 'u', 'ok', {}, 1)
    e.synchroniser_si_du()
    e.base._fil.join(10)
    assert _lire(p) == {'a': 'ok'}
    e.ecrire('b', 'u', 'doublon', {}, 1)
    e.synchroniser_si_du()
    e.base._fil.join(10)
    assert _lire(p) == {'a': 'ok', 'b': 'doublon'}
    assert _lire(p, 'SELECT cle, valeur FROM meta')[B.CLE_VERSION] == '2'
    assert e.synchroniser_si_du() is False                     # rien de neuf : pas de recopie
    assert _lire(p, 'SELECT cle, valeur FROM meta')[B.CLE_VERSION] == '2'
    e.fermer()


def test_echec_ecriture_sqlite_simule(tmp_path, monkeypatch):
    """Partage non reconnu (montage inconnu) : « database is locked » à l'essai → base de travail locale, en 3 s
    au plus, sans fichier de 0 octet laissé sur le partage."""
    p = _base(tmp_path)
    vrai = sqlite3.connect

    def connect(chemin, *a, **k):
        if os.path.abspath(str(chemin)) == p:
            open(p, 'ab').close()                              # comme cifs : le fichier est créé, vide
            raise sqlite3.OperationalError('database is locked')
        return vrai(chemin, *a, **k)
    monkeypatch.setattr(B.sqlite3, 'connect', connect)
    t = time.monotonic()
    e = Etat(p, 0.0, reseau=False)
    assert time.monotonic() - t < 5
    assert e.base.mode == 'local'
    monkeypatch.setattr(B.sqlite3, 'connect', vrai)
    assert not os.path.exists(p)                               # le fichier de 0 octet a été retiré
    e.ecrire('a', 'u', 'ok', {}, 1)
    e.fermer()
    assert _lire(p) == {'a': 'ok'}


def test_disque_local_ecrit_directement(tmp_path):
    p = _base(tmp_path)
    e = Etat(p, 0.0, reseau=False)
    assert e.base.mode == 'direct' and not e.locale
    e.ecrire('a', 'u', 'ok', {}, 1)
    e.fermer()
    assert _lire(p) == {'a': 'ok'}
    assert B.chemin_lecture(p) == p


def test_reprise_apres_plantage(tmp_path):
    """Écritures validées dans la base de travail mais jamais recopiées (processus tué) : recopiées au démarrage."""
    p = _base(tmp_path)
    _remplir_direct(p, {'a': 'ok'})
    e = Etat(p, 0.0, reseau=True, intervalle=999)
    e.ecrire('b', 'u', 'ok', {}, 1)
    e.db.close()                                               # plantage : ni fermer() ni recopie
    assert _lire(p) == {'a': 'ok'}
    avis = []
    e2 = Etat(p, 0.0, reseau=True, rapporter=lambda c, **v: avis.append(c))
    assert 'base_locale_reprise' in avis
    assert _lire(p) == {'a': 'ok', 'b': 'ok'}
    e2.fermer()


def test_partage_plus_recent_recopie(tmp_path):
    p = _base(tmp_path)
    _remplir_direct(p, {'a': 'ok'})
    Etat(p, 0.0, reseau=True).fermer()
    _ecrire_ailleurs(p, {'n': 'ok'})                            # le NAS a traité entre deux sessions
    assert B.chemin_lecture(p) == p                            # copie locale périmée : lecture sur le partage
    avis = []
    e = Etat(p, 0.0, reseau=True, rapporter=lambda c, **v: avis.append(c))
    assert 'base_locale_rafraichie' in avis
    assert e.statuts() == {'a': 'ok', 'n': 'ok'}
    e.fermer()


def test_recopie_remplacee_par_un_autre_rien_n_est_perdu(tmp_path):
    """Deux recopies presque simultanées : la nôtre est remplacée par une base qui ne la contient pas.  Au démarrage
    suivant, l'union rend nos images au partage au lieu de les perdre."""
    p = _base(tmp_path)
    _remplir_direct(p, {'x': 'echec'})
    ancienne = p + '.ancienne'
    shutil.copyfile(p, ancienne)
    e = Etat(p, 0.0, reseau=True)
    e.ecrire('a', 'u', 'ok', {}, 1)
    e.fermer()                                                 # recopiée : le partage a « a »
    shutil.copyfile(ancienne, p + '.x')
    os.replace(p + '.x', p)
    _ecrire_ailleurs(p, {'n': 'ok'})                            # l'autre écrivain, parti de l'ancienne base
    os.remove(ancienne)
    e = Etat(p, 0.0, reseau=True)
    assert e.statuts() == {'x': 'echec', 'a': 'ok', 'n': 'ok'}
    e.fermer()
    assert _lire(p) == {'x': 'echec', 'a': 'ok', 'n': 'ok'}


def test_date_touchee_contenu_identique(tmp_path):
    """Une sauvegarde qui ne change que la date de la base du partage n'est pas une modification."""
    p = _base(tmp_path)
    Etat(p, 0.0, reseau=True).fermer()
    e = Etat(p, 0.0, reseau=True, intervalle=999)
    e.ecrire('a', 'u', 'ok', {}, 1)
    e.db.close()
    st = os.stat(p)
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5 * 10**9))
    e2 = Etat(p, 0.0, reseau=True)                             # pas de Divergence : recopie
    e2.fermer()
    assert _lire(p) == {'a': 'ok'}


def test_divergence_puis_fusion(tmp_path):
    p = _base(tmp_path)
    _remplir_direct(p, {'commun_echec': 'echec', 'commun_ok': 'ok', 'doublon_vs_echec': 'echec'})
    e = Etat(p, 0.0, reseau=True, intervalle=999)
    e.ecrire('local_seul', 'u', 'ok', {'objet': 'L'}, 1)
    e.ecrire('commun_echec', 'u', 'ok', {'objet': 'L'}, 3)      # locale plus avancée
    e.ecrire('doublon_vs_echec', 'u', 'doublon', {}, 1)
    e.ecrire('commun_ok', 'u', 'echec', {}, 4)                  # locale MOINS avancée : le partage garde « ok »
    e.empreinte('sha-local', 'local_seul')
    e.db.close()                                               # pas recopiée
    _ecrire_ailleurs(p, {'nas_seul': 'ok'})
    avant = open(p, 'rb').read()
    with pytest.raises(B.Divergence) as ex:
        Etat(p, 0.0, reseau=True)
    assert open(p, 'rb').read() == avant                        # rien d'écrasé
    assert ex.value.partage == p and os.path.isfile(ex.value.locale)
    assert B.divergence_en_attente(p)
    r = B.fusionner(p)
    assert r['envoyee'] and r['total'] == 5 and all(os.path.isfile(c) for c in r['copies'])
    assert _lire(p) == {'commun_echec': 'ok', 'commun_ok': 'ok', 'doublon_vs_echec': 'doublon',
                        'local_seul': 'ok', 'nas_seul': 'ok'}
    assert _lire(p, "SELECT id, essais FROM images WHERE id='commun_ok'") == {'commun_ok': 4}   # essais : maximum
    assert _lire(p, 'SELECT sha, id FROM empreintes') == {'sha-local': 'local_seul'}
    assert not B.divergence_en_attente(p)
    e = Etat(p, 0.0, reseau=True)                              # plus de divergence
    assert e.statuts()['nas_seul'] == 'ok'
    e.fermer()


def test_regles_de_fusion(tmp_path):
    """ok > doublon > echec > en_cours > absent ; à rang égal, la ligne la plus récente."""
    a, b = str(tmp_path / 'a.sqlite'), str(tmp_path / 'b.sqlite')
    for chemin, lignes in ((a, [('1', 'echec', '2026-01-01'), ('2', 'ok', '2026-01-01'), ('3', 'en_cours', '2026-01-01'),
                                ('5', 'ok', '2026-01-01')]),
                           (b, [('1', 'doublon', '2026-01-01'), ('2', 'echec', '2026-12-01'), ('3', 'echec', '2026-01-01'),
                                ('4', 'en_cours', '2026-01-01'), ('5', 'ok', '2026-06-01')])):
        db = sqlite3.connect(chemin)
        db.execute('CREATE TABLE images (id TEXT PRIMARY KEY, url TEXT, statut TEXT, essais INTEGER DEFAULT 0, '
                   'info TEXT, maj TEXT)')
        db.execute('CREATE TABLE meta (cle TEXT PRIMARY KEY, valeur TEXT)')
        db.execute("INSERT INTO meta VALUES ('langue', ?)", ('fr' if chemin == a else 'en',))
        for i, st, maj in lignes:
            db.execute('INSERT INTO images VALUES (?,?,?,?,?,?)', (i, 'u', st, 1, json.dumps({'de': chemin}), maj))
        db.commit()
        db.close()
    sortie = str(tmp_path / 's.sqlite')
    r = B.fusionner_bases(a, b, sortie)
    assert _lire(sortie) == {'1': 'doublon', '2': 'ok', '3': 'echec', '4': 'en_cours', '5': 'ok'}
    assert json.loads(_lire(sortie, "SELECT id, info FROM images WHERE id='5'")['5'])['de'] == b   # plus récente
    assert r['meta_differentes'] == ['langue']
    assert _lire(sortie, 'SELECT cle, valeur FROM meta') == {'langue': 'fr'}      # celle du partage


def test_divergence_pendant_la_session(tmp_path):
    p = _base(tmp_path)
    avis = []
    e = Etat(p, 0.0, reseau=True, rapporter=lambda c, **v: avis.append(c), intervalle=999)
    e.ecrire('a', 'u', 'ok', {}, 1)
    assert e.synchroniser()
    _ecrire_ailleurs(p, {'nas': 'ok'})
    e.ecrire('b', 'u', 'ok', {}, 1)
    assert not e.synchroniser()
    assert 'base_locale_divergence_en_cours' in avis
    assert _lire(p) == {'a': 'ok', 'nas': 'ok'}                 # pas écrasée
    e.fermer()
    with pytest.raises(B.Divergence):
        Etat(p, 0.0, reseau=True)


def test_integrite_verifiee_avant_remplacement(tmp_path, monkeypatch):
    p = _base(tmp_path)
    avis = []
    e = Etat(p, 0.0, reseau=True, rapporter=lambda c, **v: avis.append((c, v)))
    e.ecrire('a', 'u', 'ok', {}, 1)
    assert e.synchroniser()
    e.ecrire('b', 'u', 'ok', {}, 1)
    monkeypatch.setattr(B, 'integre', lambda chemin: False)
    assert not e.synchroniser()
    assert ('base_locale_envoi_echec', {'erreur': 'integrity_check'}) in avis
    assert _lire(p) == {'a': 'ok'}
    monkeypatch.undo()
    e.fermer()                                                 # nouvel essai à la fermeture : réussi
    assert _lire(p) == {'a': 'ok', 'b': 'ok'}
    assert not [f for f in os.listdir(os.path.dirname(p)) if f != 'etat.sqlite']


def test_base_du_partage_abimee(tmp_path):
    p = _base(tmp_path)
    os.makedirs(os.path.dirname(p))
    with open(p, 'wb') as f:
        f.write(b'pas une base SQLite' * 300)
    with pytest.raises(OSError):
        Etat(p, 0.0, reseau=True)
    assert open(p, 'rb').read().startswith(b'pas une base')    # jamais écrasée


def test_journal_chaud_sur_le_partage_reporte_la_recopie(tmp_path):
    p = _base(tmp_path)
    avis = []
    e = Etat(p, 0.0, reseau=True, rapporter=lambda c, **v: avis.append(c))
    e.ecrire('a', 'u', 'ok', {}, 1)
    with open(p + '-journal', 'wb') as f:                       # un écrivain direct est en pleine transaction
        f.write(b'x' * 512)
    assert not e.synchroniser()
    assert 'base_locale_partage_occupe' in avis
    os.remove(p + '-journal')
    assert e.synchroniser()
    e.fermer()


def test_lecteurs_lisent_la_base_de_travail(tmp_path):
    """Possession, nouveautés, anomalies : la base de travail locale à jour (écritures pas encore recopiées
    comprises) ; ils ne créent rien sur le partage."""
    from coupole.modules.ohp import anomalies, possession
    p = _base(tmp_path)
    dest = os.path.dirname(os.path.dirname(p))
    e = Etat(p, 0.0, reseau=True, intervalle=999)
    e.ecrire('a', 'u', 'ok', {'final': os.path.join(dest, 'M31', 'a.xisf')}, 1)
    assert e.synchroniser()
    e.ecrire('b', 'https://x/b.fits', 'doublon', {'doublon_de': 'a'}, 1)
    e.valider()
    assert possession.lire_statuts(dest) == {'a': 'ok', 'b': 'doublon'}
    assert possession.Possession.lire(dest).statuts == {'a': 'ok', 'b': 'doublon'}
    assert [x['fichier'] for x in anomalies.depuis_traitement(p)] == ['b.fits']
    e.fermer()
    assert sorted(os.listdir(os.path.dirname(p))) == ['etat.sqlite']


def test_traitement_complet_vers_un_partage(tmp_path, monkeypatch):
    """Chaîne réelle (serveur local, conversions) vers un dossier « réseau » : JOURNAL.txt, événements, base du
    partage complète à la fin."""
    from . import test_pilote_local as T
    from coupole.core import chemins
    monkeypatch.setattr(chemins, 'est_reseau', lambda c: True)
    monkeypatch.setattr(B, 'est_reseau', lambda c: True)
    import coupole.modules.ohp.inventaire as INV
    from .serveur_local import ServeurLocal
    brut, meta = INV.lire(INV.INSTANTANE)
    rangs = [x for x in brut if 'palisana' in x['access_url'].lower()][:2]
    s = ServeurLocal()
    try:
        lignes = []
        for k, x in enumerate(rangs):
            contenu = T.fits_synthetique(x['s_ra'], x['s_dec'], seed=k)
            s.fichiers['/i%d.fits' % k] = contenu
            lignes.append(dict(x, access_url=s.url('/i%d.fits' % k), access_estsize=len(contenu) / 1024))
        inv = INV.Inventaire(lignes, dict(meta, source='local'))
        dest = tmp_path / 'nas' / 'OHP_DU_ECU'
        evts = []
        b = T.lancer(dest, inv, inv.images, evts=evts)
    finally:
        s.fermer()
    assert b['compte']['ok'] == 2
    p = str(dest / '_traitement' / 'etat.sqlite')
    assert set(_lire(p).values()) == {'ok'} and len(_lire(p)) == 2
    assert any(ev['type'] == 'base_locale' and ev['cle'] == 'base_locale_avis' for ev in evts)
    journal = (dest / '_traitement' / 'JOURNAL.txt').read_text(encoding='utf-8')
    assert 'Dossier sur un partage réseau : base de travail locale, recopiée sur le partage toutes les 30 s' in journal
    assert 'Folder on a network share' in journal


def test_cli_fusionner(tmp_path, capsys):
    from coupole.modules.ohp import cli
    p = _base(tmp_path)
    dest = os.path.dirname(os.path.dirname(p))

    class A:
        pass
    a = A()
    a.dest = dest
    assert cli.cmd_fusionner(a) == 0 and 'rien à fusionner' in capsys.readouterr().out
    _remplir_direct(p, {'a': 'echec'})
    e = Etat(p, 0.0, reseau=True, intervalle=999)
    e.ecrire('a', 'u', 'ok', {}, 1)
    e.db.close()
    _ecrire_ailleurs(p, {'n': 'ok'})
    assert cli.cmd_fusionner(a) == 0
    assert 'fusionnées' in capsys.readouterr().out
    assert _lire(p) == {'a': 'ok', 'n': 'ok'}


# ---------------------------------------------------------------- vrais partages (hors CI)
@pytest.mark.skipif(not os.environ.get('COUPOLE_TEST_SMB'), reason='COUPOLE_TEST_SMB : dossier sur un vrai partage cifs')
def test_vrai_partage_cifs(tmp_path):
    """Lent : un vrai partage SMB monté par cifs (options par défaut).  SQLite n'y écrit pas ; la base de travail
    locale, si."""
    racine = os.path.join(os.environ['COUPOLE_TEST_SMB'], 'coupole-test-%d' % os.getpid())
    p = os.path.join(racine, '_traitement', 'etat.sqlite')
    os.makedirs(os.path.dirname(p))
    try:
        assert B.est_reseau(racine)
        db = sqlite3.connect(os.path.join(racine, 'essai.sqlite'), timeout=1)
        with pytest.raises(sqlite3.OperationalError, match='locked'):
            db.execute('CREATE TABLE t (x)')
            db.commit()
        db.close()
        e = Etat(p, 0.0)
        assert e.base.mode == 'local'
        for k in range(20):
            e.ecrire('i%d' % k, 'u', 'ok', {}, 1)
        e.fermer()
        assert len(_lire(p)) == 20
        e = Etat(p, 0.0)                                       # relance : rien à recopier
        e.ecrire('i99', 'u', 'echec', {}, 1)
        e.fermer()
        assert _lire(p)['i99'] == 'echec'
    finally:
        shutil.rmtree(racine, ignore_errors=True)


@pytest.mark.skipif(os.name != 'nt', reason='chemins UNC : Windows')
def test_chemin_unc_reel(tmp_path):
    from coupole.modules.ohp.possession import Possession
    lecteur, reste = os.path.splitdrive(str(tmp_path))
    unc = '\\\\localhost\\%s$%s' % (lecteur[0], reste) if lecteur.endswith(':') else None
    if not unc or not os.path.isdir(unc):
        pytest.skip('partage administratif \\\\localhost\\C$ inaccessible')
    dest = os.path.join(unc, 'OHP_DU_ECU')
    p = os.path.join(dest, '_traitement', 'etat.sqlite')
    e = Etat(p, 0.0)
    assert e.base.mode == 'local'                              # UNC : toujours la base de travail locale
    e.ecrire('a', 'u', 'ok', {}, 1)
    e.fermer()
    assert Possession.lire(dest).statuts == {'a': 'ok'}
    assert sorted(os.listdir(os.path.dirname(p))) == ['etat.sqlite']


# ---------------------------------------------------------------- interface
def test_interface_message_et_fusion(app_qt, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    from coupole.core import config
    from coupole.modules.ohp import gui
    from .test_catalogue_possession import attendre
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    p = gui.Panneau()
    try:
        p._evenements([{'type': 'base_locale', 'cle': 'base_locale_avis', 'valeurs': {'dest': '/mnt/partage/X', 'secondes': 30}}])
        assert 'Dossier sur un partage réseau : base de travail locale, recopiée sur le partage toutes les 30 s' in \
            p.journal.toPlainText()
        appels = []
        monkeypatch.setattr(gui.QMessageBox, 'question', lambda *a, **k: QMessageBox.StandardButton.Yes)
        monkeypatch.setattr(gui.base_partagee, 'fusionner',
                            lambda chemin: appels.append(chemin) or
                            {'total': 7, 'de_la_locale': 2, 'conflits': 1, 'envoyee': True, 'copies': ['a', 'b']})
        p.proposer_fusion('/mnt/partage/X/_traitement/etat.sqlite', '/cache/bases/x')
        assert attendre(app_qt, lambda: 'fusionnées' in p.journal.toPlainText())
        assert appels == ['/mnt/partage/X/_traitement/etat.sqlite']
    finally:
        p.arreter()
        p.close()
        p.deleteLater()
        app_qt.processEvents()
