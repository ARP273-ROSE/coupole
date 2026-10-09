"""Réglages conservés d'une fermeture à l'autre (0.1.6) : fermer puis rouvrir la fenêtre retrouve chaque élément ;
réglages corrompus ou d'un mauvais type → défauts ; position hors écran → fenêtre recentrée ; aucune écriture
disque pendant la frappe ; réinitialisation (Préférences, ligne de commande)."""
import json
import os
import time

import pytest

pytest.importorskip('PyQt6')


def attendre(app, condition, delai=30):
    t0 = time.time()
    while not condition() and time.time() - t0 < delai:
        app.processEvents()
        time.sleep(0.01)
    return condition()


def _repartir_du_disque():
    """Comme un nouveau lancement : réglages, état de l'interface et mémoire relus depuis le disque."""
    from coupole.core import config, etat_interface
    from coupole.gui import memoire
    memoire.reinitialiser_pour_tests()
    config.reinitialiser_pour_tests()
    etat_interface.reinitialiser_pour_tests()
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False


def _ouvrir(app):
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.show()
    assert attendre(app, lambda: f.panneau_module('ohp').inv is not None, 60)
    return f


def _fermer(f):
    from coupole.gui.outils import attendre_taches
    f.close()
    attendre_taches()


def _zone():
    from PyQt6.QtGui import QGuiApplication
    return QGuiApplication.primaryScreen().availableGeometry()


def _taille_attendue(l, h):
    """Taille d'une fenêtre principale une fois bornée à l'écran (à 200 %, l'écran de test fait 400 × 400)."""
    from coupole.gui.adaptatif import TAILLE_MIN
    z = _zone()
    return (max(min(l, z.width()), min(TAILLE_MIN.width(), z.width())),
            max(min(h, z.height()), min(TAILLE_MIN.height(), z.height())))


def _rang(f, ident):
    return next(i for i, p in enumerate(f.panneaux) if getattr(getattr(p, 'module', None), 'id', '') == ident)


@pytest.fixture
def propre(app_qt):
    """Réglages remis comme au départ après le test (les autres tests partagent le dossier des réglages)."""
    from coupole.core import config
    avant = dict(config.reglages().valeurs)
    _repartir_du_disque()
    yield
    from coupole.gui import memoire
    memoire.reinitialiser_pour_tests()
    r = config.reglages()
    r.valeurs.clear()
    r.valeurs.update(avant)
    r.enregistrer()
    from coupole.core import etat_interface
    etat_interface.effacer_fichier()
    etat_interface.reinitialiser_pour_tests()


def test_fermer_rouvrir_retrouve_chaque_element(app_qt, propre, tmp_path, monkeypatch):
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QFileDialog
    from coupole.core import config, etat_interface
    from coupole.gui import dialogues, memoire

    f = _ouvrir(app_qt)
    ohp = f.panneau_module('ohp')
    # ---------------------------------------------------------------- fenêtre
    f.resize(int(_zone().width() * 0.9), int(_zone().height() * 0.7))
    f.move(10, 15)
    app_qt.processEvents()
    geo = f.geometry()
    # ---------------------------------------------------------------- catalogue OHP : filtres, choix, colonnes
    cible = next(o for o in ohp.inv.objets() if 'T120' in o['tel'] and len(o['nuits']) >= 2 and len(o['filtres']) >= 2)
    ohp.f_cat.setCurrentIndex(ohp.f_cat.findData(cible['cat']))
    ohp.f_tel.setCurrentIndex(ohp.f_tel.findData('T120'))
    ohp.f_manquantes.setChecked(True)
    ohp.f_dates.setChecked(True)
    ohp.f_anom_nouv.setChecked(True)
    ohp.ciel_cat.setCurrentIndex(ohp.ciel_cat.findData(cible['cat']))
    ohp.recherche.setText(cible['objet'][:6].lower())
    app_qt.processEvents()
    r = next(r for r, o in enumerate(ohp.m_obj.donnees) if o['objet'] == cible['objet'])
    ohp.v_obj.selectRow(ohp.p_obj.mapFromSource(ohp.m_obj.index(r, 0)).row())
    assert attendre(app_qt, lambda: ohp.f_nuit.count() > 2 and ohp.f_filtre.count() > 2)
    ohp.f_nuit.setCurrentIndex(2)
    ohp.f_filtre.setCurrentIndex(2)
    nuit, filtre = ohp.f_nuit.currentData(), ohp.f_filtre.currentData()
    monkeypatch.setattr(memoire, '_bouton_gauche_enfonce', lambda: True)     # comme un glisser à la souris
    ohp.v_obj.setColumnWidth(1, 222)
    monkeypatch.setattr(memoire, '_bouton_gauche_enfonce', lambda: False)
    ohp.v_obj.horizontalHeader().moveSection(2, 6)
    ohp.v_obj.sortByColumn(3, Qt.SortOrder.DescendingOrder)
    ohp.v_img.sortByColumn(5, Qt.SortOrder.AscendingOrder)
    ordre_objets = [ohp.v_obj.horizontalHeader().logicalIndex(i) for i in range(10)]
    ohp.sp_catalogue.setSizes([260, 420])
    app_qt.processEvents()
    tailles = ohp.sp_catalogue.sizes()
    ohp.onglets.setCurrentIndex(3)
    # ---------------------------------------------------------------- traitement : tout est gardé dès la saisie
    dest = str(tmp_path / 'sortie')
    ohp.dest.clear()
    QTest.keyClicks(ohp.dest, dest)
    ohp.format.setCurrentIndex(ohp.format.findData('fz'))
    ohp.noms.setCurrentIndex(ohp.noms.findData('en'))
    ohp.garder_doublons.setChecked(True)
    ohp.garder_fits.setChecked(True)
    ohp.qualite.setChecked(True)
    ohp.mode_astap.setCurrentIndex(ohp.mode_astap.findData('suspectes'))
    # ---------------------------------------------------------------- qualité
    qual = f.panneau_module('qualite')
    analyse = tmp_path / 'analyse'
    analyse.mkdir()
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', staticmethod(lambda *a, **k: str(analyse)))
    qual.choisir()
    qual.echantillon.setChecked(True)
    qual.n_echantillon.setValue(7)
    # ---------------------------------------------------------------- spectres et séries : fichier, dossier, récents
    don = f.panneau_module('donnees')
    dossier_csv = tmp_path / 'series'
    dossier_csv.mkdir()
    fichiers = []
    for i in range(12):
        c = dossier_csv / ('serie%02d.csv' % i)
        c.write_text('t,flux\n1,2\n2,3\n3,5\n', encoding='utf-8')
        fichiers.append(str(c))
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: (fichiers[0], '')))
    don.ouvrir()
    assert attendre(app_qt, lambda: don.ds)
    for c in fichiers[1:]:
        don.ouvrir(c)
        assert attendre(app_qt, lambda c=c: etat_interface.etat().recents('donnees')[:1] == [c])
    don.axe.setCurrentIndex(don.axe.findData('mhz'))
    # ---------------------------------------------------------------- cosmologie
    cos = f.panneau_module('cosmo')
    cos.modele.setCurrentIndex(cos.modele.findData('perso'))
    cos.h0.setValue(70.5)
    cos.om.setValue(0.25)
    cos.ok.setValue(0.01)
    cos.shoes.setChecked(True)
    cos.echelle.setCurrentIndex(cos.echelle.findData('lin'))
    cos.z.setText('2.5')
    # ---------------------------------------------------------------- sites et heures
    sit = f.panneau_module('sites')
    sit.table.selectRow(1)
    site = sit.sites[1].id
    sit.carte.definir_vue({'z': 6, 'lon': 5.7, 'lat': 43.9})
    sit.en_ligne.setChecked(False)
    # ---------------------------------------------------------------- un dialogue, et le module affiché
    d = dialogues.DialogueReglages(f)
    d.show()
    d.resize(700, 470)
    d.onglets.setCurrentIndex(1)
    app_qt.processEvents()
    d.reject()
    f.barre.setCurrentRow(_rang(f, 'sites'))
    _fermer(f)

    # ================================================================ sur le disque
    home = config.dossier_config()
    doc = json.loads((home / 'interface.json').read_text(encoding='utf-8'))
    assert doc['version'] == etat_interface.VERSION
    assert json.loads((home / 'reglages.json').read_text(encoding='utf-8'))['dossier_sortie'] == dest
    texte = json.dumps(doc)
    assert 'lancer' not in texte and 'traitement' not in texte     # rien qui rejouerait un traitement

    # ================================================================ second lancement
    _repartir_du_disque()
    f = _ouvrir(app_qt)
    ohp = f.panneau_module('ohp')
    assert f.pile.currentIndex() == _rang(f, 'sites')
    assert (f.geometry().width(), f.geometry().height()) == (geo.width(), geo.height())
    assert (f.geometry().x(), f.geometry().y()) == (geo.x(), geo.y())
    assert f.placement == 'restauree'
    # catalogue
    assert ohp.f_cat.currentData() == cible['cat'] and ohp.f_tel.currentData() == 'T120'
    assert ohp.f_manquantes.isChecked() and ohp.f_dates.isChecked() and ohp.f_anom_nouv.isChecked()
    assert not ohp.f_nouveaux.isChecked() and not ohp.f_verifier.isChecked()
    assert ohp.ciel_cat.currentData() == cible['cat']
    assert ohp.recherche.text() == cible['objet'][:6].lower()
    assert attendre(app_qt, lambda: getattr(ohp, '_objets', set()) == {cible['objet']})
    assert attendre(app_qt, lambda: ohp.f_nuit.currentData() == nuit and ohp.f_filtre.currentData() == filtre)
    h = ohp.v_obj.horizontalHeader()
    assert [h.logicalIndex(i) for i in range(10)] == ordre_objets
    assert ohp.v_obj.columnWidth(1) == 222
    assert (h.sortIndicatorSection(), h.sortIndicatorOrder()) == (3, Qt.SortOrder.DescendingOrder)
    hi = ohp.v_img.horizontalHeader()
    assert (hi.sortIndicatorSection(), hi.sortIndicatorOrder()) == (5, Qt.SortOrder.AscendingOrder)
    assert ohp.m_img._tri == (5, Qt.SortOrder.AscendingOrder)       # le modèle trie vraiment
    f.barre.setCurrentRow(_rang(f, 'ohp'))
    attendre(app_qt, lambda: False, 0.2)
    # même partage (la largeur totale dépend d'un ascenseur vertical, selon l'onglet affiché)
    t2 = ohp.sp_catalogue.sizes()
    assert abs(t2[0] / sum(t2) - tailles[0] / sum(tailles)) < 0.015, (t2, tailles)
    assert ohp.onglets.currentIndex() == 3
    # traitement
    assert ohp.dest.text() == dest and ohp.format.currentData() == 'fz' and ohp.noms.currentData() == 'en'
    assert ohp.garder_doublons.isChecked() and ohp.garder_fits.isChecked() and ohp.qualite.isChecked()
    assert ohp.mode_astap.currentData() == 'suspectes'
    assert not ohp.occupe() and not ohp.journal.toPlainText()          # aucun traitement relancé seul
    # qualité
    qual = f.panneau_module('qualite')
    from coupole.gui.adaptatif import texte_reel
    assert texte_reel(qual.l_dossier.text()) == str(analyse)
    assert qual.echantillon.isChecked() and qual.n_echantillon.value() == 7
    # spectres et séries : 10 récents au plus, le plus récent d'abord ; le dialogue rouvre dans le dossier
    don = f.panneau_module('donnees')
    recents = etat_interface.etat().recents('donnees')
    assert recents == list(reversed(fichiers))[:10]
    don._remplir_recents()
    assert len([a for a in don.menu_recents.actions() if a.text().startswith(str(dossier_csv))]) == 10
    assert attendre(app_qt, lambda: memoire.dossier('donnees_ouvrir') == str(dossier_csv), 10)
    assert don.axe.currentData() == 'mhz'
    # cosmologie : paramètres personnalisés gardés même en repassant par Planck
    cos = f.panneau_module('cosmo')
    assert cos.modele.currentData() == 'perso'
    assert abs(cos.h0.value() - 70.5) < 1e-9 and abs(cos.om.value() - 0.25) < 1e-9 and abs(cos.ok.value() - 0.01) < 1e-9
    assert cos.shoes.isChecked() and cos.echelle.currentData() == 'lin' and cos.z.text() == '2.5'
    cos.modele.setCurrentIndex(cos.modele.findData('planck18'))
    cos.modele.setCurrentIndex(cos.modele.findData('perso'))
    assert abs(cos.h0.value() - 70.5) < 1e-9 and abs(cos.om.value() - 0.25) < 1e-9
    # sites et heures
    sit = f.panneau_module('sites')
    assert sit._site.id == site and sit.table.currentRow() == 1
    assert sit.carte.vue() == {'z': 6, 'lon': 5.7, 'lat': 43.9}
    assert not sit.en_ligne.isChecked() and not sit.carte.en_ligne
    # dialogue : taille et onglet
    d = dialogues.DialogueReglages(f)
    assert (d.width(), d.height()) == (min(700, _zone().width()), min(470, _zone().height()))
    assert d.onglets.currentIndex() == 1
    d.reject()
    _fermer(f)


def test_maximisee_et_ecran_disparu(app_qt, propre):
    from coupole.core.etat_interface import etat
    e = etat()
    l, h = int(_zone().width() * 0.85), int(_zone().height() * 0.8)
    e.ecrire('fenetre.geometrie', {'x': 10, 'y': 20, 'l': l, 'h': h, 'maximisee': True, 'ecran': ''})
    e.enregistrer()
    _repartir_du_disque()
    f = _ouvrir(app_qt)
    assert f.isMaximized()
    assert f.normalGeometry().width() == _taille_attendue(l, h)[0]
    _fermer(f)
    _repartir_du_disque()
    e = etat()
    assert e.lire('fenetre.geometrie.maximisee') is True and e.lire('fenetre.geometrie.l') == _taille_attendue(l, h)[0]
    # écran débranché depuis la dernière fois : recentrée sur l'écran principal
    e.ecrire('fenetre.geometrie', {'x': 10, 'y': 20, 'l': 700, 'h': 500, 'maximisee': False, 'ecran': 'HDMI-ABSENT'})
    e.enregistrer()
    _repartir_du_disque()
    f = _ouvrir(app_qt)
    assert f.placement == 'recentree' and not f.isMaximized()
    _fermer(f)


@pytest.mark.parametrize('x,y', [(5000, 5000), (-3000, 100), (100, -900), (790, 790)])
def test_position_hors_ecran_recentree(app_qt, propre, x, y):
    from PyQt6.QtGui import QGuiApplication
    from coupole.core.etat_interface import etat
    etat().ecrire('fenetre.geometrie', {'x': x, 'y': y, 'l': 9000, 'h': 7000, 'maximisee': False, 'ecran': ''})
    etat().enregistrer()
    _repartir_du_disque()
    f = _ouvrir(app_qt)
    zone = QGuiApplication.primaryScreen().availableGeometry()
    assert f.placement == 'recentree'
    g = f.geometry()
    assert zone.contains(g.topLeft()) and g.width() <= zone.width() and g.height() <= zone.height()
    _fermer(f)


def test_placer_garde_fous(app_qt):
    """La fonction de placement seule : valeurs absurdes refusées, taille bornée à l'écran, position gardée."""
    from PyQt6.QtWidgets import QMainWindow
    from coupole.gui import memoire
    w = QMainWindow()
    for g in (None, 'abc', {}, {'x': 'a', 'y': 0, 'l': 1, 'h': 1}, {'x': True, 'y': 0, 'l': 500, 'h': 400},
              {'x': 0, 'y': 0, 'l': -5, 'h': 400}, {'x': 10 ** 9, 'y': 0, 'l': 500, 'h': 400}):
        assert memoire.placer(w, g) == 'aucune'
    assert memoire.placer(w, {'x': 30, 'y': 40, 'l': 300, 'h': 200}) == 'restauree'
    assert (w.geometry().x(), w.geometry().y(), w.width(), w.height()) == (30, 40, 300, 200)
    assert memoire.placer(w, {'x': 30, 'y': 40, 'l': 30000, 'h': 20000}) == 'ajustee'      # bornée à l'écran
    assert _zone().contains(w.geometry())
    w.close()


def test_reglages_corrompus_donnent_les_defauts(app_qt, propre):
    from coupole.core import config, etat_interface
    home = config.dossier_config()
    (home / 'interface.json').write_text('{"version": 1, "fenetre": {', encoding='utf-8')
    _repartir_du_disque()
    f = _ouvrir(app_qt)
    assert etat_interface.etat().restaure
    assert list(home.glob('interface.json.corrompu-*'))
    assert f.pile.currentIndex() == 0 and f.panneau_module('ohp').onglets.currentIndex() == 0
    _fermer(f)
    # JSON valide, mais des types faux partout, des chemins disparus et une version inconnue d'un sous-arbre
    mauvais = {'version': 1,
               'fenetre': {'geometrie': 'abc', 'module': 5},
               'dialogues': {'reglages': ['a', 3], 'reglages_onglet': 99},
               'dossiers': {'donnees_ouvrir': '/chemin/qui/n/existe/plus'},
               'recents': {'donnees': 'pas une liste'},
               'modules': {'ohp': {'recherche': 12, 'onglet': 99, 'type': ['x'], 'nouveaux': 'oui',
                                   'colonnes_objets': {'n': 'x', 'largeurs': 'y'},
                                   'colonnes_images': {'n': 9, 'ordre': [0, 0, 1, 2, 3, 4, 5, 6, 7], 'tri': [99, 0]},
                                   'separateur': [1, 'a'], 'objets': 'tous', 'nuit': 3},
                           'qualite': {'echantillon_n': 999, 'echantillon': 1, 'dossier': 42},
                           'cosmo': {'perso': ['a', 2], 'z': 'abc', 'modele': 'inconnu', 'ok': 'x'},
                           'sites': {'carte': {'z': True, 'lon': 'x'}, 'site': 4, 'carte_en_ligne': 'non'}}}
    (home / 'interface.json').write_text(json.dumps(mauvais), encoding='utf-8')
    (home / 'reglages.json').write_text(json.dumps({'ohp_garder_fits': 'oui', 'ohp_mode_astap': 3,
                                                    'ohp_verifier_qualite': None}), encoding='utf-8')
    _repartir_du_disque()
    f = _ouvrir(app_qt)
    ohp = f.panneau_module('ohp')
    assert f.pile.currentIndex() == 0 and ohp.onglets.currentIndex() == 0 and ohp.recherche.text() == ''
    assert ohp.f_cat.currentIndex() == 0 and not ohp.f_nouveaux.isChecked()
    assert not ohp.garder_fits.isChecked() and ohp.mode_astap.currentData() == 'tous' and not ohp.qualite.isChecked()
    qual = f.panneau_module('qualite')
    assert qual.n_echantillon.value() != 999 and not qual.echantillon.isChecked()
    cos = f.panneau_module('cosmo')
    assert cos.modele.currentData() == 'planck18' and cos.z.text() == '1'
    sit = f.panneau_module('sites')
    assert sit.en_ligne.isChecked() and sit.carte.z >= 1
    e = etat_interface.etat()
    assert e.recents('donnees') == []
    attendre(app_qt, lambda: '/chemin/qui/n/existe/plus' in e.existence, 10)
    assert e.dossier('donnees_ouvrir', 'DEFAUT') == 'DEFAUT'
    _fermer(f)


def test_aucune_ecriture_disque_pendant_la_frappe(app_qt, propre, tmp_path):
    from PyQt6.QtTest import QTest
    from coupole.core import config, etat_interface
    from coupole.gui import memoire
    f = _ouvrir(app_qt)
    ohp = f.panneau_module('ohp')
    memoire.memoire().ecrire()                     # ce que l'ouverture a pu changer : écrit avant de compter
    e, r = etat_interface.etat(), config.reglages()
    avant = (e.ecritures, r.ecritures)
    t0 = time.monotonic()
    ohp.recherche.clear()
    QTest.keyClicks(ohp.recherche, 'nebuleuse de la lyre m57')
    ohp.dest.clear()
    for car in str(tmp_path / 'un_dossier_de_sortie'):
        QTest.keyClicks(ohp.dest, car)
        app_qt.processEvents()
    assert time.monotonic() - t0 < memoire.DELAI_MS / 1000 * 0.8, 'frappe trop lente pour ce test'
    assert (e.ecritures, r.ecritures) == avant              # aucune écriture pendant la frappe
    # puis UNE écriture groupée (au plus toutes les 2 s) avec tout ce qui a été tapé
    assert attendre(app_qt, lambda: e.ecritures > avant[0] and r.ecritures > avant[1], 5)
    assert e.ecritures == avant[0] + 1 and r.ecritures == avant[1] + 1
    home = config.dossier_config()
    assert json.loads((home / 'interface.json').read_text(encoding='utf-8'))['modules']['ohp']['recherche'] == \
        'nebuleuse de la lyre m57'
    assert json.loads((home / 'reglages.json').read_text(encoding='utf-8'))['dossier_sortie'] == \
        str(tmp_path / 'un_dossier_de_sortie')
    # rien de changé : aucune écriture de plus
    attendre(app_qt, lambda: False, 2.3)
    assert e.ecritures == avant[0] + 1 and r.ecritures == avant[1] + 1
    _fermer(f)


def test_reinitialiser_la_disposition(app_qt, propre, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    from coupole.core import config, etat_interface
    from coupole.gui import dialogues
    f = _ouvrir(app_qt)
    ohp = f.panneau_module('ohp')
    ohp.recherche.setText('m57')
    ohp.onglets.setCurrentIndex(2)
    f.barre.setCurrentRow(_rang(f, 'cosmo'))
    _fermer(f)
    home = config.dossier_config()
    assert (home / 'interface.json').exists()
    # Préférences > « Réinitialiser la disposition » : immédiat, réglages intacts
    _repartir_du_disque()
    config.reglages()['format_sortie'] = 'fz'
    f = _ouvrir(app_qt)
    assert f.panneau_module('ohp').recherche.text() == 'm57'
    monkeypatch.setattr(QMessageBox, 'question', staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    monkeypatch.setattr(dialogues.DialogueReglages, 'exec', lambda self: (self._reinitialiser_disposition(),
                                                                          self.result())[1])
    f.reglages()
    ohp = f.panneau_module('ohp')
    assert ohp.recherche.text() == '' and ohp.onglets.currentIndex() == 0 and f.pile.currentIndex() == 0
    assert not (home / 'interface.json').exists()
    assert config.reglages()['format_sortie'] == 'fz'
    _fermer(f)
    # ligne de commande
    assert (home / 'interface.json').exists()                 # la fermeture a réécrit la disposition d'origine
    from coupole.cli import main
    assert main(['--reinitialiser-interface']) == 0
    assert not (home / 'interface.json').exists()
    assert main(['--reset-interface']) == 0                   # rien à effacer : pas une erreur
    etat_interface.reinitialiser_pour_tests()


def test_etat_interface_lecture_tolerante(tmp_path):
    from coupole.core.etat_interface import EtatInterface, VERSION
    c = tmp_path / 'interface.json'
    c.write_text(json.dumps({'version': VERSION + 5, 'a': {'b': 1}}), encoding='utf-8')
    e = EtatInterface(c)
    assert e.lire('a.b') is None                              # version future : ignorée, pas mal interprétée
    assert e.ecrire('a.b', 3) and not e.ecrire('a.b', 3)      # inchangé : rien à écrire
    assert e.lire('a.b', 0, int) == 3 and e.lire('a.b', 'x', str) == 'x'
    assert e.ecrire('a.c', True) and e.lire('a.c', 0, int) == 0     # un booléen n'est pas un nombre
    assert e.lire('a.b.c', 'd') == 'd' and e.lire('', 'd') == 'd'
    assert not e.ecrire('a.n', float('nan')) and not e.ecrire('a.o', object())
    assert e.lire_entier('a.b', 7, 0, 2) == 7
    assert e.enregistrer() and not e.enregistrer() and e.ecritures == 1
    for i in range(15):
        e.ajouter_recent('r', str(tmp_path / ('f%d' % i)))
    e.ajouter_recent('r', str(tmp_path / 'f3'))
    assert len(e.recents('r')) == 10 and e.recents('r')[0] == str(tmp_path / 'f3')
    assert len(set(e.recents('r'))) == 10
    e2 = EtatInterface(c)
    assert e2.lire('a.b') == 3
    t = e2.verifier_existence_en_fond()
    t.join(5)
    assert e2.reinitialiser() and not c.exists()
    # dossier illisible, disque plein : jamais d'exception
    e3 = EtatInterface(tmp_path / 'absent' / 'x' / 'interface.json')
    assert e3.lire('rien', 1) == 1
    assert os.path.basename(e3.chemin) == 'interface.json'
