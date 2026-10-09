"""0.1.11 — copie produite par l'ancien script `ohp_xisf.py` (avant Coupole), lue d'une autre machine.

Retour de Kevin (Linux, 0.1.10, `/mnt/nas/Astronomie/OHP_DU_ECU`) : objets entièrement possédés (4/4, pastille
verte) mais « Ouvrir le dossier de la cible », « Ouvrir avec », « Ouvrir l'emplacement » et le double-clic grisés
ou sans effet (« Rien n'est encore téléchargé pour cet objet »).  Cause : la base d'état de cette copie ne note que
le chemin absolu de la machine qui a traité (`final` = « /workspace/Workspace/OHP_DU_ECU/… », conteneur) ; le
chemin relatif est dans `_traitement/journal.csv`.

Reproduction réduite : 20 lignes RÉELLES de la base et du journal de la copie de Kevin ((914) Palisana : 10
converties + 6 doublons ; NGC 5866 : 4 converties), `tests/donnees/copie_ohp_xisf/`, et des XISF factices aux
chemins de `destination`.
"""
import csv
import json
import os
import shutil
import sqlite3
import time
from pathlib import Path

import numpy as np
import pytest

from coupole.modules.ohp import emplacements
from coupole.modules.ohp.conversion import ident
from coupole.modules.ohp.possession import Possession

DONNEES = Path(__file__).parent / 'donnees' / 'copie_ohp_xisf'
ANCIENNE = '/workspace/Workspace/OHP_DU_ECU'


def _journal():
    with open(DONNEES / 'journal.csv', encoding='utf-8-sig', newline='') as f:
        lignes = list(csv.reader(f, delimiter=';'))
    return [dict(zip(lignes[0], l)) for l in lignes[1:]]


def faire_copie(racine: Path, journal=True, fichiers=True) -> Path:
    """Dossier de sortie comme celui de Kevin : base (mode WAL, comme ohp_xisf.py), journal.csv, INDEX_LOTS.csv,
    XISF factices (en-tête instrument) aux chemins du journal."""
    from coupole.core import xisf
    dest = racine / 'OHP_DU_ECU'
    (dest / '_traitement').mkdir(parents=True)
    db = sqlite3.connect(str(dest / '_traitement' / 'etat.sqlite'))
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE images (id TEXT PRIMARY KEY, url TEXT, statut TEXT, essais INTEGER DEFAULT 0, '
               'info TEXT, maj TEXT)')
    db.execute('CREATE TABLE empreintes (sha TEXT PRIMARY KEY, id TEXT)')
    db.executemany('INSERT INTO images VALUES (?,?,?,?,?,?)',
                   [tuple(r) for r in json.loads((DONNEES / 'etat.json').read_text(encoding='utf-8'))])
    db.commit()
    db.close()
    if journal:
        shutil.copyfile(DONNEES / 'journal.csv', dest / '_traitement' / 'journal.csv')
    shutil.copyfile(DONNEES / 'INDEX_LOTS.csv', dest / 'INDEX_LOTS.csv')
    if fichiers:
        mc = [('NAXIS1', '4', ''), ('NAXIS2', '4', ''), ('TELESCOP', "'T120'", ''), ('XPIXSZ', '13.5', ''),
              ('XBINNING', '1', ''), ('FOCALLEN', '7234.1', ''), ('PIXSCALE', '0.3849', '')]
        for l in _journal():
            if l['destination']:
                f = dest.joinpath(*l['destination'].split('/'))
                f.parent.mkdir(parents=True, exist_ok=True)
                xisf.ecrire(f, np.zeros((4, 4), '<u2'), mc)
    return dest


def _infos(dest):
    db = sqlite3.connect(str(dest / '_traitement' / 'etat.sqlite'))
    try:
        return {i: json.loads(s) for i, s in db.execute("SELECT id, info FROM images WHERE statut='ok'")}
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _cache_propre():
    emplacements.oublier_cache()
    yield
    emplacements.oublier_cache()


# ================================================================ résolution (sans interface)
def test_la_base_ne_connait_que_le_chemin_d_une_autre_machine(tmp_path):
    dest = faire_copie(tmp_path)
    infos = _infos(dest)
    assert len(infos) == 14
    assert all(d['final'].startswith(ANCIENNE + '/') and 'chemin' not in d for d in infos.values())
    assert not any(os.path.exists(d['final']) for d in infos.values())


def test_resolution_par_journal(tmp_path):
    dest = faire_copie(tmp_path)
    poss, infos_ok = Possession.lire_avec_infos(dest)
    attendus = {l['url']: l['destination'] for l in _journal() if l['destination']}
    ok = [i for i, s in poss.statuts.items() if s == 'ok']
    assert len(ok) == 14 and sum(1 for s in poss.statuts.values() if s == 'doublon') == 6
    for i, d in infos_ok:
        det = poss.details[i]
        assert det['origine'] == 'journal'
        assert det['chemin'] == attendus[d['url']].replace('/', os.sep)
        assert not os.path.isabs(det['chemin'])
        assert os.path.isfile(os.path.join(str(dest), det['chemin']))
        assert d['final'] == os.path.join(str(dest), det['chemin'])       # en mémoire : pour la complétude des lots
    assert sorted(i for i, _ in poss.a_migrer) == sorted(ok)
    # complétude des lots calculée sur les chemins locaux
    from coupole.modules.ohp.inventaire import Inventaire
    images = Inventaire.charger().images
    lots = poss.lots(images, infos_ok)
    palisana = os.path.normcase(os.path.abspath(str(dest / '01_Asteroides' / '914_Palisana' / 'nuit_2023-08-15_T120' / 'R')))
    assert lots[palisana]['converties'] == 10 and lots[palisana]['complet']


def test_journal_en_cache_et_relu_s_il_change(tmp_path, monkeypatch):
    dest = faire_copie(tmp_path)
    ouvertures = []
    vrai_open = open

    def compter(f, *a, **k):
        if str(f).endswith('journal.csv'):
            ouvertures.append(f)
        return vrai_open(f, *a, **k)
    import builtins
    monkeypatch.setattr(builtins, 'open', compter)
    j1 = emplacements.lire_journal(dest)
    j2 = emplacements.lire_journal(dest)
    assert j1 is j2 and len(ouvertures) == 1 and len(j1['url']) == 14 and 0 < len(j1['source']) <= 14
    p = dest / '_traitement' / 'journal.csv'
    tout = p.read_text(encoding='utf-8-sig').splitlines()
    texte = [tout[0]] + [l for l in tout[1:] if l.split(';')[1]][:4]
    # 4 lignes, dont un « fichier_source » porté par deux images : ambigu, pas d'index par ce nom
    double = texte[1].split(';')[0]
    autre = texte[2].split(';')
    texte[2] = ';'.join([double] + autre[1:])
    p.write_text('\n'.join(texte) + '\n', encoding='utf-8-sig')
    os.utime(p, ns=(time.time_ns() + 10**9, time.time_ns() + 10**9))
    j3 = emplacements.lire_journal(dest)
    assert len(ouvertures) == 2 and len(j3['url']) == 4
    assert double not in j3['source'] and len(j3['source']) <= 2


def test_secours_par_fichier_source(tmp_path):
    dest = faire_copie(tmp_path)
    j = emplacements.lire_journal(dest)
    info = {'source': '914_Palisana_R_20s_inexistant.fits', 'final': '/ailleurs/x.xisf'}
    assert emplacements.resoudre(dest, info, j) == ('', '')
    l = next(l for l in _journal() if l['destination'] and l['fichier_source'] in j['source'])
    assert emplacements.resoudre(dest, {'source': l['fichier_source']}, j) == (l['destination'], 'journal')


def test_sans_journal_par_l_ancienne_racine(tmp_path):
    dest = faire_copie(tmp_path, journal=False)
    poss, _ = Possession.lire_avec_infos(dest)
    oks = [i for i, s in poss.statuts.items() if s == 'ok']
    assert all(poss.details[i]['origine'] == 'rebase' for i in oks)
    assert all(os.path.isfile(os.path.join(str(dest), poss.details[i]['chemin'])) for i in oks)
    assert poss.a_migrer == []                    # seul le journal fait foi pour écrire dans la base


def test_rebase_sans_staging_par_dossier_de_type():
    assert emplacements.rebaser('C:\\Users\\k\\09_Galaxies\\sauvegarde\\09_Galaxies\\M31\\champ_1_T120\\R\\a.xisf') == \
        '09_Galaxies/M31/champ_1_T120/R/a.xisf'
    assert emplacements.rebaser('/x/_sans_solution_astrometrique/M1/2021-01-01_T120/R/a.xisf') == \
        '_sans_solution_astrometrique/M1/2021-01-01_T120/R/a.xisf'
    assert emplacements.rebaser('/x/y/a.xisf') == ''
    assert emplacements.relatif_valide('../a.xisf') == '' and emplacements.relatif_valide('/a') == ''
    assert emplacements.relatif_valide('C:/a') == '' and emplacements.relatif_valide('a\\b.xisf') == 'a/b.xisf'


def test_recherche_par_nom_dans_le_dossier_du_lot(tmp_path):
    """Ni chemin, ni journal, ni ancienne racine : le nom attendu (calcul de lot du rangement) — y compris le
    « _2 » d'un nom pris deux fois (deux poses de Palisana à la même seconde)."""
    dest = faire_copie(tmp_path)
    attendus = {l['url']: l['destination'] for l in _journal() if l['destination']}
    infos = [(i, dict(d, _id=i)) for i, d in _infos(dest).items()]
    for i, d in infos:
        meme_objet = [(j, e) for j, e in infos if e['objet'] == d['objet']]
        assert emplacements.chercher_par_nom(dest, d, meme_objet) == attendus[d['url']], d['source']
    assert any(v.endswith('_2.xisf') for v in attendus.values())


def test_dossier_attendu(tmp_path):
    dest = faire_copie(tmp_path)
    assert emplacements.dossier_attendu(dest, 'ast', '(914) Palisana') == str(dest / '01_Asteroides' / '914_Palisana')
    assert emplacements.dossier_attendu(dest, 'gal', 'NGC 5866') == str(dest / '09_Galaxies' / 'NGC_5866')
    assert emplacements.dossier_attendu(dest, 'gal', 'NGC 1') == ''


# ================================================================ migration
def test_migration_ecrit_le_chemin_relatif(tmp_path):
    dest = faire_copie(tmp_path)
    poss, _ = Possession.lire_avec_infos(dest)
    assert emplacements.migrer(dest, poss.a_migrer) == 14
    infos = _infos(dest)
    assert all(not os.path.isabs(d['chemin']) and (dest / d['chemin']).is_file() for d in infos.values())
    assert all(d['final'].startswith(ANCIENNE) for d in infos.values())   # rien d'autre n'est touché
    assert emplacements.migrer(dest, poss.a_migrer) == 0                     # déjà fait
    (dest / '_traitement' / 'journal.csv').unlink()                          # le journal n'est plus nécessaire
    poss2, _ = Possession.lire_avec_infos(dest)
    assert all(poss2.details[i]['origine'] == 'base' for i, s in poss2.statuts.items() if s == 'ok')
    assert poss2.a_migrer == []


def test_migration_sur_un_partage_par_la_base_de_travail(tmp_path, monkeypatch):
    from coupole.core import base_partagee
    monkeypatch.setattr(base_partagee, 'est_reseau', lambda *_: True)
    dest = faire_copie(tmp_path)
    poss, _ = Possession.lire_avec_infos(dest)
    assert emplacements.migrer(dest, poss.a_migrer) == 14
    locale = base_partagee.chemin_travail(str(dest / '_traitement' / 'etat.sqlite'))
    assert os.path.isfile(locale)                                            # écrit par la base de travail locale
    infos = _infos(dest)                                                     # … puis recopié sur le « partage »
    assert all(d.get('chemin') for d in infos.values())
    assert not [f for f in os.listdir(dest / '_traitement') if f.endswith('.tmp')]


def test_migration_impossible_garde_la_resolution(tmp_path, monkeypatch):
    from coupole.core import base_partagee
    dest = faire_copie(tmp_path)

    def refuse(self):
        raise OSError('read-only file system')
    monkeypatch.setattr(base_partagee.BasePartagee, 'ouvrir', refuse)
    poss, _ = Possession.lire_avec_infos(dest)
    assert emplacements.migrer(dest, poss.a_migrer) == 0
    poss2, _ = Possession.lire_avec_infos(dest)
    assert all(poss2.details[i]['chemin'] for i, s in poss2.statuts.items() if s == 'ok')


def test_metadonnees_reecrire_note_les_chemins(tmp_path):
    from coupole.modules.ohp import metadonnees
    dest = faire_copie(tmp_path)
    r = metadonnees.reecrire_dossier(str(dest), 'fr', simuler=False)
    assert r['erreurs'] == 0 and r['chemins'] == 14
    assert all(d.get('chemin') for d in _infos(dest).values())


def test_cli_metadonnees_reecrire(tmp_path, capsys):
    from coupole.cli import main
    dest = faire_copie(tmp_path)
    assert main(['ohp', 'metadonnees', str(dest), '--reecrire']) == 0
    out = capsys.readouterr().out
    assert 'emplacements notés : 14' in out or 'locations recorded: 14' in out
    assert all(d.get('chemin') for d in _infos(dest).values())


def test_ranger_sur_la_copie_ne_casse_rien(tmp_path, inventaire):
    """Relancer un traitement vers la copie : le rangement rapporte `final` au dossier courant (aucun déplacement
    « fantôme », aucune erreur) et journal.csv garde ses destinations relatives."""
    from coupole.core.parallele import Plan
    from coupole.modules.ohp.pilote import Traitement
    dest = faire_copie(tmp_path)
    avant = sorted(str(p.relative_to(dest)) for p in dest.rglob('*.xisf'))
    t = Traitement(str(dest), inventaire, Plan(1, 1, True, ''), {'format': 'xisf', 'langue': 'fr'})
    try:
        t.ranger()
    finally:
        t.fermer()
    assert sorted(str(p.relative_to(dest)) for p in dest.rglob('*.xisf')) == avant
    j = {l['url']: l['destination'] for l in csv.DictReader(
        open(dest / '_traitement' / 'journal.csv', encoding='utf-8-sig'), delimiter=';') if l['destination']}
    assert j == {l['url']: l['destination'] for l in _journal() if l['destination']}
    assert all(d['chemin'] and d['final'].startswith(str(dest)) for d in _infos(dest).values())


# ================================================================ interface
def attendre(app, cond, delai=30):
    fin = time.time() + delai
    while not cond() and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)
    return cond()


@pytest.fixture
def panneau(app_qt, monkeypatch):
    from coupole.core import config
    from coupole.modules.ohp.gui import Panneau
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    p = Panneau()
    p.resize(1300, 800)
    p.show()
    assert attendre(app_qt, lambda: p.inv is not None and p.m_obj.rowCount() > 0)
    assert attendre(app_qt, lambda: not getattr(p, '_etapes', None) and getattr(p, '_comptes', None) is not None)
    yield p
    p.arreter()
    p.close()
    p.deleteLater()
    app_qt.processEvents()


def _ouvrir_copie(p, app_qt, dest):
    p.dest.setText(str(dest))
    p._charger_possession()
    assert attendre(app_qt, lambda: p.possession.dest == p._dest_courante() and p.possession.existe)
    assert attendre(app_qt, lambda: (getattr(p, '_lots_par_objet', {}) or {}).get('(914) Palisana'))


def _ligne_objet(p, nom):
    src = next(r for r, o in enumerate(p.m_obj.donnees) if o['objet'] == nom)
    return p.p_obj.mapFromSource(p.m_obj.index(src, 0))


def _menu(p, ouvrir_menu, vue, index):
    """Ouvre le menu contextuel comme un clic droit sur `index` ; rend le menu affiché (popup, pas exec)."""
    from PyQt6.QtWidgets import QMenu
    vue.scrollTo(index)
    ouvrir_menu(vue.visualRect(index).center())
    m = p._menu_contextuel
    assert isinstance(m, QMenu) and m.isVisible() and not m.toolTipsVisible()
    return m


def _action(menu, debut):
    return next(a for a in menu.actions() if a.text().startswith(debut))


@pytest.mark.parametrize('partage', [False, True])
def test_toutes_les_actions_sur_la_copie(panneau, app_qt, tmp_path, monkeypatch, partage):
    from coupole.core import base_partagee, logiciels
    from coupole.gui import ouvrir
    if partage:
        monkeypatch.setattr(base_partagee, 'est_reseau', lambda *_: True)
    dest = faire_copie(tmp_path)
    appels = []
    monkeypatch.setattr(logiciels, 'montrer_dans_dossier', lambda c: appels.append(('montrer', str(c))) or True)
    monkeypatch.setattr(logiciels, 'lancer', lambda cmd, c: appels.append(('lancer', cmd[0], str(c))) or True)
    monkeypatch.setattr(ouvrir, 'ouvrir_defaut', lambda c: appels.append(('defaut', str(c))) or True)
    monkeypatch.setattr(ouvrir, 'installes', lambda rafraichir=False: {'pixinsight': ['/opt/PixInsight/bin/PixInsight']})
    p = panneau
    _ouvrir_copie(p, app_qt, dest)
    # migration en fond : chemins notés dans la base (par la base de travail locale si « partage »)
    assert attendre(app_qt, lambda: all(d.get('chemin') for d in _infos(dest).values()))
    cible = str(dest / '01_Asteroides' / '914_Palisana')
    o = next(o for o in p.m_obj.donnees if o['objet'] == '(914) Palisana')
    assert p.dossier_objet(o) == cible
    # double-clic sur l'objet
    p.v_obj.clearSelection()
    i_obj = _ligne_objet(p, '(914) Palisana')
    p.v_obj.selectRow(i_obj.row())
    p._ouvrir_dossier_objet()
    assert appels.pop() == ('montrer', cible)
    # menu de l'objet : dossier et lots actifs, et ils agissent
    m = _menu(p, p._menu_objet, p.v_obj, i_obj)
    a = _action(m, 'Ouvrir le dossier de la cible')
    assert a.isEnabled() and a.text() == 'Ouvrir le dossier de la cible'
    a.trigger()
    assert appels.pop() == ('montrer', cible)
    b = _action(m, 'Voir les lots')
    assert b.isEnabled()
    b.trigger()
    assert p.onglets.currentIndex() == 2 and p.l_filtre_lots.text().endswith(': 1')
    m.close()
    # encadré Lots (en-tête des XISF lu dans le dossier du lot) et complétude 10 / 10
    lot = next(r for r in range(p.p_lots.rowCount()) if not p.v_lots.isRowHidden(r))
    p.v_lots.selectRow(lot)
    assert attendre(app_qt, lambda: p._astro_valeurs['focale'].text() != '—')
    assert p._astro_valeurs['focale'].text().startswith('7234')
    src = p.p_lots.mapToSource(p.p_lots.index(lot, 0)).row()
    assert str(p.m_lots.lignes[src][p.COL_LOT_COMPLET]).startswith('complet')
    ml = _menu(p, p._menu_lot, p.v_lots, p.p_lots.index(lot, 0))
    c = _action(ml, 'Ouvrir le dossier du lot')
    assert c.isEnabled()
    c.trigger()
    assert appels.pop() == ('montrer', os.path.join(cible, 'nuit_2023-08-15_T120', 'R'))
    ml.close()
    p.onglets.setCurrentIndex(0)
    # images de l'objet : double-clic, Ouvrir, Ouvrir avec, Ouvrir l'emplacement
    p.v_obj.selectRow(i_obj.row())
    assert attendre(app_qt, lambda: p.m_img.rowCount() > 0 and
                    all(x['objet'] == '(914) Palisana' for x in p.m_img.donnees))
    r = next(r for r in range(p.p_img.rowCount())
             if p.possession.statut(p.m_img.donnees[p.p_img.mapToSource(p.p_img.index(r, 0)).row()]) == 'ok')
    x = p.m_img.donnees[p.p_img.mapToSource(p.p_img.index(r, 0)).row()]
    fichier = p.chemin_image(x)
    assert os.path.isfile(fichier) and fichier.startswith(str(dest))
    p.v_img.clearSelection()
    p.v_img.selectRow(r)
    p._ouvrir_image()
    assert appels.pop() == ('defaut', fichier)
    mi = _menu(p, p._menu_image, p.v_img, p.p_img.index(r, 0))
    o1 = _action(mi, 'Ouvrir')
    assert o1.isEnabled() and o1.text() == 'Ouvrir'
    o1.trigger()
    assert appels.pop() == ('defaut', fichier)
    avec = _action(mi, 'Ouvrir avec')
    assert avec.isEnabled() and avec.text() == 'Ouvrir avec'
    px = _action(avec.menu(), 'PixInsight')
    assert px.isEnabled()
    px.trigger()
    assert appels.pop() == ('lancer', '/opt/PixInsight/bin/PixInsight', fichier)
    e = _action(mi, "Ouvrir l'emplacement")
    assert e.isEnabled()
    e.trigger()
    assert appels.pop() == ('montrer', fichier)
    mi.close()


def test_motif_dans_le_libelle_quand_rien_n_est_telecharge(panneau, app_qt, tmp_path):
    """Image non téléchargée : entrées désactivées, motif court DANS le libellé, motif complet en barre d'état —
    jamais d'info-bulle par-dessus le menu (KDE : elle en captait la souris)."""
    p = panneau
    dest = faire_copie(tmp_path)
    _ouvrir_copie(p, app_qt, dest)
    nom = next(o['objet'] for o in p.m_obj.donnees
               if o['objet'] not in ('(914) Palisana', 'NGC 5866') and not emplacements.dossier_attendu(
                   dest, o['cat'], o['objet']))
    i_obj = _ligne_objet(p, nom)
    m = _menu(p, p._menu_objet, p.v_obj, i_obj)
    a = _action(m, 'Ouvrir le dossier de la cible')
    assert not a.isEnabled() and a.text().endswith('(rien de téléchargé)')
    assert a.statusTip() == "Rien n'est encore téléchargé pour cet objet." and not a.toolTip().startswith('Rien')
    m.close()


def test_dossier_attendu_quand_aucune_image_n_a_de_chemin(panneau, app_qt, tmp_path):
    p = panneau
    dest = faire_copie(tmp_path)
    p.dest.setText(str(dest))
    o = next(o for o in p.m_obj.donnees if o['objet'] == 'NGC 5866')
    p.possession = Possession(p._dest_courante())                      # rien de résolu
    assert p.dossier_objet(o) == str(dest / '09_Galaxies' / 'NGC_5866')
