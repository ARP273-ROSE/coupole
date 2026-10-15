"""0.7.2 — télécharger sans manuel : le parcours d'un débutant, de bout en bout, sans écran ni réseau public.

Retour d'usage (0.4.1, Windows) : un étudiant voyait le catalogue, sélectionnait une image, faisait un clic droit et
ne trouvait que « Ouvrir (rien de téléchargé) / Ouvrir avec / Ouvrir l'emplacement » ; le vrai chemin (objets →
« Traiter cette sélection → » → onglet Traitement → Lancer) était introuvable — et, en 1366 × 768, le bouton
« Traiter cette sélection → » était sous le bord de la fenêtre.

Vérifié ici : premier lancement (guide en trois étapes, listes vides qui disent quoi faire, bouton grisé avec la
raison), choisir une cible → « Télécharger (N images · X → ≈ Y en XISF) » → dossier demandé la première fois →
fichiers convertis présents → « Ouvrir » disponible ; menus contextuels (images, objets) qui commencent par
« Télécharger… » ; double-clic qui propose de télécharger ; même logique dans les Archives des observatoires.
Serveur HTTP local seulement (tests/serveur_local.py) : aucune requête ne sort de la machine.
"""
import os
import time

import pytest

from coupole.modules.ohp import inventaire as INV

from .serveur_local import ServeurLocal
from .test_archives import B, obs_locale, serveur  # noqa: F401  (fixture « serveur » des Archives)
from .test_pilote_local import fits_synthetique


def attendre(app, cond, delai=30):
    fin = time.time() + delai
    while not cond() and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)
    return cond()


@pytest.fixture(scope='module')
def banque_locale():
    """(914) Palisana : six images de l'instantané servies par un serveur local (FITS synthétiques)."""
    brut, meta = INV.lire(INV.INSTANTANE)
    rangs = [x for x in brut if 'palisana' in x['access_url'].lower()][:6]
    assert len(rangs) == 6
    s = ServeurLocal()
    lignes = []
    for k, x in enumerate(rangs):
        contenu = fits_synthetique(x['s_ra'], x['s_dec'], seed=k)
        chemin = '/img%d.fits' % k
        s.fichiers[chemin] = contenu
        lignes.append(dict(x, access_url=s.url(chemin), access_estsize=len(contenu) / 1024))
    yield s, INV.Inventaire(lignes, dict(meta, source='local'))
    s.fermer()


@pytest.fixture
def panneau(app_qt, monkeypatch, tmp_path):
    """Banque OHP au tout premier lancement : rien de gardé, aucun dossier de sortie choisi."""
    from coupole.core import config
    from coupole.modules.ohp.gui import Panneau
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    monkeypatch.setitem(config.reglages().valeurs, 'dossier_sortie', '')
    p = Panneau()
    p.resize(1100, 680)                       # la part d'une fenêtre 1366 × 768 laissée au module
    p.show()
    assert attendre(app_qt, lambda: p.inv is not None and p.m_obj.rowCount() > 0)
    assert attendre(app_qt, lambda: not getattr(p, '_etapes', None) and getattr(p, '_comptes', None) is not None)
    p.dest.setText(str(tmp_path / 'jamais_choisi'))   # dossier proposé par défaut (rien dedans)
    yield p
    p.arreter()
    p.close()
    p.deleteLater()
    app_qt.processEvents()


def _choisir_objet(p, app_qt, nom):
    for r, o in enumerate(p.m_obj.donnees):
        if o['objet'] == nom:
            idx = p.p_obj.mapFromSource(p.m_obj.index(r, 0))
            p.v_obj.selectRow(idx.row())
            p.v_obj.scrollTo(idx)
            break
    else:
        raise AssertionError(nom)
    assert attendre(app_qt, lambda: p.m_img.rowCount() > 0, 10)


def _actions(menu):
    return [a for a in menu.actions() if not a.isSeparator()]


# ================================================================ premier lancement
def test_premier_lancement_guide_listes_vides_bouton_grise(panneau, app_qt):
    p = panneau
    from coupole.core.etat_interface import etat
    assert p.guide.isVisible() and p.onglets.currentIndex() == 0
    textes = [lab.text() for lab in p.l_etapes]
    assert 'Choisissez une cible' in textes[0] and '<b>' in textes[0]          # étape courante en gras
    assert 'Télécharger' in textes[2]
    # rien de choisi d'office : la liste des images dit quoi faire, le bouton aussi
    assert not p.v_obj.selectionModel().selectedRows()
    assert p.v_img.texte_vide().startswith('Aucune cible choisie : cliquez sur une cible')
    assert not p.b_telecharger.isEnabled() and 'cible' in p.b_telecharger.toolTip()
    assert p.b_telecharger.objectName() == 'principal'                           # couleur d'accent
    # chaque colonne s'explique au survol de son en-tête
    from PyQt6.QtCore import Qt
    for m in (p.m_obj, p.m_img):
        for c in range(m.columnCount()):
            bulle = m.headerData(c, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole)
            assert '\n' in bulle and len(bulle.split('\n')[1]) > 10, (c, bulle)
    # « Traiter cette sélection → » n'existe plus ; l'onglet s'appelle Téléchargement
    assert p.b_vers_traitement.text() == 'Options du téléchargement →'
    assert p.onglets.tabText(p.ONGLET_TELECHARGEMENT) == 'Téléchargement'
    assert 'Traite' not in ' '.join(p.onglets.tabText(k) for k in range(p.onglets.count()))
    # étape 1 faite : cochée, l'étape 2 puis 3 deviennent courantes
    _choisir_objet(p, app_qt, 'NGC 6888')
    assert attendre(app_qt, lambda: p.b_telecharger.isEnabled() and '840 images' in p.b_telecharger.text(), 10)
    assert '&#10004;' in p.l_etapes[0].text() or '✔' in p.l_etapes[0].text()
    assert '≈' in p.b_telecharger.text() and 'XISF' in p.b_telecharger.text()
    # fermé pour de bon, réaffiché par l'Aide
    p.masquer_guide()
    assert not p.guide.isVisible() and etat().lire('modules.ohp.guide_masque', False, bool)
    p.montrer_guide()
    assert p.guide.isVisible() and not etat().lire('modules.ohp.guide_masque', True, bool)


def test_bouton_telecharger_visible_en_1366x768(app_qt, monkeypatch):
    """Fenêtre entière en 1366 × 768 (et à 125 % : 1093 × 614 points) : le bouton Télécharger est à l'écran, sans
    défiler, et l'onglet Téléchargement n'impose plus sa hauteur au catalogue."""
    from coupole.core import config
    from coupole.gui.fenetre import FenetrePrincipale
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    f = FenetrePrincipale()
    try:
        for l, h in ((1366, 768), (1093, 614)):
            f.resize(l, h)
            f.show()
            ohp = f.panneau_module('ohp')
            assert attendre(app_qt, lambda: ohp.inv is not None and ohp.m_obj.rowCount() > 0)
            app_qt.processEvents()
            b = ohp.b_telecharger
            haut_gauche = b.mapTo(f, b.rect().topLeft())
            bas_droit = b.mapTo(f, b.rect().bottomRight())
            assert f.rect().contains(haut_gauche) and f.rect().contains(bas_droit), (l, h, haut_gauche, bas_droit)
            zone = f.pile.currentWidget()
            assert zone.verticalScrollBar().maximum() == 0, (l, h)
            # colonnes clés des images visibles sans défiler : état, date, télescope, filtre, pose
            hi = ohp.v_img.horizontalHeader()
            for col in (0, 1, 4, 5, 6):
                assert hi.sectionViewportPosition(col) + 20 <= ohp.v_img.viewport().width(), (l, h, col)
        # 125 % sur un portable : le texte du bouton tient (police de 10 points mise à l'échelle par Qt)
        assert f.font().pointSizeF() >= 9.5
    finally:
        f.close()
        f.deleteLater()
        app_qt.processEvents()


# ================================================================ le parcours complet, serveur local
def test_choisir_telecharger_puis_ouvrir(panneau, app_qt, banque_locale, tmp_path, monkeypatch):
    from coupole.gui import fichiers, ouvrir
    from coupole.modules.ohp import gui as G
    serveur_, inv = banque_locale
    p = panneau
    p._inventaire_pret(inv)
    assert attendre(app_qt, lambda: p.m_obj.rowCount() == 1, 10)
    choisi = tmp_path / 'mes_images'
    choisi.mkdir()
    demandes = []
    monkeypatch.setattr(fichiers, 'choisir_dossier', lambda *a, **k: demandes.append(a) or str(choisi))
    monkeypatch.setattr(G.QMessageBox, 'question', lambda *a, **k: pytest.fail('confirmation inattendue'))
    _choisir_objet(p, app_qt, inv.images[0]['objet'])
    assert attendre(app_qt, lambda: p.b_telecharger.isEnabled() and p.b_telecharger.text().startswith('Télécharger ('),
                    10), p.b_telecharger.text()
    p.b_telecharger.click()
    assert len(demandes) == 1                                       # dossier demandé la première fois
    dest = str(choisi / 'OHP_DU_ECU')
    assert p.dest.text() == dest
    assert p.barre_cat.isVisible() and p.b_arreter_cat.isVisible()  # progression sous le bouton
    assert not p.b_telecharger.isEnabled() and p.b_telecharger.text() == 'Téléchargement en cours…'
    assert attendre(app_qt, lambda: not p.occupe(), 120)
    assert attendre(app_qt, lambda: any(p.possession.possedee(x) for x in inv.images), 30)
    assert not p.barre_cat.isVisible()
    assert all(r.startswith('/img') for r, _ in serveur_.requetes)  # seulement le serveur local
    x = next(x for x in p.m_img.donnees if p.possession.statut(x) == 'ok')
    chemin = p.chemin_image(x, verifier=True)
    assert chemin.startswith(dest) and os.path.exists(chemin) and chemin.endswith('.xisf')
    # le bouton le dit, l'étape 3 est cochée
    assert attendre(app_qt, lambda: p.b_telecharger.text() == 'Déjà téléchargé ✓' or
                    'Télécharger (' in p.b_telecharger.text(), 10)
    # clic droit sur l'image téléchargée : « Télécharger » grisé (déjà là), « Ouvrir » disponible
    r = next(k for k, y in enumerate(p.m_img.donnees) if y is x)
    i = p.p_img.mapFromSource(p.m_img.index(r, 1))
    p.v_img.clearSelection()
    pos = p.v_img.visualRect(i).center()
    p._menu_image(pos)
    acts = _actions(p._menu_contextuel)
    assert acts[0].text().startswith('Télécharger cette image') and not acts[0].isEnabled()
    assert acts[1].text() == 'Ouvrir' and acts[1].isEnabled()
    p._menu_contextuel.close()
    # double-clic : ouvre le fichier
    ouverts = []
    monkeypatch.setattr(ouvrir, 'ouvrir_defaut', lambda c: ouverts.append(c))
    p.v_img.selectRow(i.row())
    p._ouvrir_image()
    assert ouverts == [chemin]
    # deuxième téléchargement : le dossier n'est plus demandé
    p.telecharger_selection()
    assert len(demandes) == 1
    attendre(app_qt, lambda: not p.occupe(), 60)


# ================================================================ menus contextuels, double-clic
def test_menu_image_commence_par_telecharger(panneau, app_qt, monkeypatch):
    p = panneau
    _choisir_objet(p, app_qt, 'NGC 6888')
    vus = []
    monkeypatch.setattr(p, 'telecharger_images', lambda imgs, confirmer=False: vus.append(list(imgs)) or True)
    pos = p.v_img.visualRect(p.p_img.index(0, 1)).center()
    p.v_img.clearSelection()
    p._menu_image(pos)
    acts = _actions(p._menu_contextuel)
    assert acts[0].text() == 'Télécharger cette image' and acts[0].isEnabled() and acts[0].font().bold()
    assert acts[1].text() == 'Ouvrir  (pas encore téléchargée)' and not acts[1].isEnabled()
    assert 'Télécharger cette image' in acts[1].statusTip()             # la raison dit quoi faire
    acts[0].trigger()
    assert len(vus) == 1 and len(vus[0]) == 1
    p._menu_contextuel.close()
    # plusieurs lignes choisies, clic droit sur l'une d'elles : « Télécharger ces 3 images »
    from PyQt6.QtCore import QItemSelectionModel
    for k in range(3):
        p.v_img.selectionModel().select(p.p_img.index(k, 0), QItemSelectionModel.SelectionFlag.Select |
                                        QItemSelectionModel.SelectionFlag.Rows)
    p._menu_image(pos)
    acts = _actions(p._menu_contextuel)
    assert acts[0].text() == 'Télécharger ces 3 images'
    acts[0].trigger()
    assert len(vus[1]) == 3
    p._menu_contextuel.close()


def test_double_clic_sur_une_image_absente_propose_de_la_telecharger(panneau, app_qt, monkeypatch):
    p = panneau
    _choisir_objet(p, app_qt, 'NGC 6888')
    questions, vus = [], []
    monkeypatch.setattr(p, '_confirmer_telechargement', lambda t: questions.append(t) or True)
    monkeypatch.setattr(p, 'telecharger_images', lambda imgs, confirmer=False: vus.append(list(imgs)) or True)
    p.v_img.selectRow(0)
    p._ouvrir_image()
    assert len(questions) == 1 and "n'est pas encore téléchargée" in questions[0]
    assert len(vus) == 1 and len(vus[0]) == 1
    # refus : rien ne part
    monkeypatch.setattr(p, '_confirmer_telechargement', lambda t: False)
    p._ouvrir_image()
    assert len(vus) == 1


def test_menu_et_double_clic_sur_une_cible(panneau, app_qt, monkeypatch):
    p = panneau
    _choisir_objet(p, app_qt, 'NGC 6888')
    vus = []
    monkeypatch.setattr(p, 'telecharger_images', lambda imgs, confirmer=False: vus.append(list(imgs)) or True)
    i = p.v_obj.currentIndex()
    p._menu_objet(p.v_obj.visualRect(i).center())
    acts = _actions(p._menu_contextuel)
    assert acts[0].text() == 'Télécharger toutes les images de NGC 6888' and acts[0].isEnabled()
    assert acts[1].text().startswith('Ouvrir le dossier de la cible') and not acts[1].isEnabled()
    acts[0].trigger()
    assert len(vus) == 1 and {x['objet'] for x in vus[0]} == {'NGC 6888'}
    assert len([x for x in vus[0] if not x['doublon']]) == 840
    p._menu_contextuel.close()
    # double-clic sur une cible dont rien n'est téléchargé : proposition
    questions = []
    monkeypatch.setattr(p, '_confirmer_telechargement', lambda t: questions.append(t) or True)
    p._ouvrir_dossier_objet()
    assert len(questions) == 1 and 'NGC 6888' in questions[0] and len(vus) == 2


def test_menus_grises_pendant_un_telechargement(panneau, app_qt, monkeypatch):
    p = panneau
    _choisir_objet(p, app_qt, 'NGC 6888')
    monkeypatch.setattr(p, 'occupe', lambda: True)
    p._maj_bouton_telecharger()
    assert not p.b_telecharger.isEnabled() and p.b_telecharger.text() == 'Téléchargement en cours…'
    p._menu_image(p.v_img.visualRect(p.p_img.index(0, 1)).center())
    a = _actions(p._menu_contextuel)[0]
    assert not a.isEnabled() and a.text() == 'Télécharger cette image  (téléchargement en cours)'
    p._menu_contextuel.close()


def test_aide_menu_guide_et_aide_f1(app_qt, monkeypatch):
    from coupole.core import config
    from coupole.gui.fenetre import FenetrePrincipale
    from coupole.core.i18n import tr
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    f = FenetrePrincipale()
    try:
        textes = [a.text() for m in f.menuBar().actions() for a in m.menu().actions()]
        assert 'Guide de démarrage (Banque OHP)' in textes
        ohp = f.panneau_module('ohp')
        ohp.masquer_guide()
        a = next(a for m in f.menuBar().actions() for a in m.menu().actions()
                 if a.text() == 'Guide de démarrage (Banque OHP)')
        a.trigger()
        assert not ohp.guide.isHidden()
        h = tr('ohp_aide_html')
        assert 'Télécharger' in h and 'Traiter cette sélection' not in h
    finally:
        f.close()
        f.deleteLater()
        app_qt.processEvents()


# ================================================================ Archives des observatoires
def test_archives_bouton_menu_double_clic(app_qt, tmp_path, monkeypatch, serveur):  # noqa: F811
    from coupole.modules.archives import gui as G
    monkeypatch.setattr(G.T, 'sortie_par_defaut', lambda: str(tmp_path))
    p = G.Panneau()
    p.resize(1100, 680)
    p.show()
    try:
        obs = [obs_locale(serveur, '/a_i2d.fits'), obs_locale(serveur, '/b_drz.fits')]
        p._resultats((B.Requete(nom='M 16'), [B.Resultat('mast', obs)], obs))
        app_qt.processEvents()
        assert not p.b_telecharger.isEnabled() and 'lignes' in p.b_telecharger.toolTip()
        assert p.b_telecharger.objectName() == 'principal'
        p.vue.selectAll()
        assert attendre(app_qt, lambda: p.b_telecharger.isEnabled(), 10)
        assert p.b_telecharger.text().startswith('Télécharger la sélection (2')
        # clic droit : « Télécharger ces 2 observations » d'abord, puis Ouvrir (grisé, avec la raison)
        pos = p.vue.visualRect(p.proxy.index(0, 1)).center()
        p._menu(pos)
        acts = _actions(p.vue._menu_contextuel)
        assert acts[0].text() == 'Télécharger ces 2 observations' and acts[0].isEnabled()
        assert acts[1].text() == 'Ouvrir  (pas encore téléchargé)' and not acts[1].isEnabled()
        p.vue._menu_contextuel.close()
        # double-clic sur une ligne absente : proposition, puis téléchargement réel (serveur local)
        p.vue.selectRow(0)
        questions = []
        monkeypatch.setattr(p, '_confirmer_telechargement', lambda t: questions.append(t) or True)
        p._ouvrir_prepare()
        assert len(questions) == 1
        assert attendre(app_qt, lambda: p.choisies() and p._statut(p.choisies()[0]) == 'ok', 60)
        assert attendre(app_qt, lambda: not getattr(p, '_dl_actif', False), 30)
        o = p.choisies()[0]
        assert os.path.exists(p._prepare(o))
        p._menu(p.vue.visualRect(p.proxy.index(0, 1)).center())
        acts = _actions(p.vue._menu_contextuel)
        assert not acts[0].isEnabled() and acts[0].text().endswith('(déjà téléchargé)')
        assert acts[1].text() == 'Ouvrir' and acts[1].isEnabled()
        p.vue._menu_contextuel.close()
        assert p.b_telecharger.text() == 'Déjà téléchargé ✓' and not p.b_telecharger.isEnabled()
    finally:
        p.arreter()
        p.close()
