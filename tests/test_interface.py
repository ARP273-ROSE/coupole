"""Interface graphique (sans écran) : info-bulles partout, deux langues, aucun blocage."""
import os
import time

import pytest

pytest.importorskip('PyQt6')
from PyQt6.QtWidgets import (QAbstractButton, QAbstractItemView, QAbstractSpinBox, QComboBox, QLineEdit,  # noqa: E402
                             QPlainTextEdit, QTabBar, QTextBrowser, QWidget, QDialog)

INTERACTIFS = (QAbstractButton, QComboBox, QLineEdit, QAbstractSpinBox, QAbstractItemView, QPlainTextEdit, QTextBrowser)


def attendre(app, condition, delai=30):
    t0 = time.time()
    while not condition() and time.time() - t0 < delai:
        app.processEvents()
        time.sleep(0.01)


def sans_info_bulle(racine):
    manque = []
    for w in racine.findChildren(QWidget):
        if not isinstance(w, INTERACTIFS) or w.objectName().startswith('qt_'):
            continue
        p = w.parentWidget()
        interne = False
        while p is not None and p is not racine:      # sous-widget d'un composite (spinbox, liste, onglets)
            if isinstance(p, (QAbstractSpinBox, QComboBox, QAbstractItemView, QTabBar)):
                interne = True
                break
            p = p.parentWidget()
        if interne or type(w).__name__ in ('QToolButton',) and isinstance(w.parentWidget(), QTabBar):
            continue
        if isinstance(w, QAbstractButton) and type(w).__name__ == 'QPushButton' and \
                w.parentWidget() is not None and type(w.parentWidget()).__name__ == 'QDialogButtonBox' and w.toolTip():
            continue
        if not w.toolTip().strip():
            manque.append('%s « %s »' % (type(w).__name__, getattr(w, 'text', lambda: '')()))
    return manque


@pytest.fixture(scope='module')
def fenetre(app_qt):
    from coupole.core import config
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.show()
    attendre(app_qt, lambda: f.panneaux[0].inv is not None)
    yield f
    f.close()
    from coupole.gui.outils import attendre_taches
    attendre_taches()


@pytest.mark.parametrize('code', ['fr', 'en'])
def test_info_bulles_partout(app_qt, fenetre, code):
    fenetre.changer_langue(code)
    attendre(app_qt, lambda: fenetre.panneaux[0].inv is not None)
    assert not sans_info_bulle(fenetre)
    for a in fenetre.findChildren(type(fenetre.menuBar().actions()[0])):
        if a.text() and not a.isSeparator() and a.menu() is None:
            assert a.toolTip().strip() and a.toolTip() != a.text().replace('&', ''), a.text()


def test_les_deux_langues_different(app_qt, fenetre):
    textes = {}
    for code in ('fr', 'en'):
        fenetre.changer_langue(code)
        attendre(app_qt, lambda: fenetre.panneaux[0].inv is not None)
        textes[code] = [a.text() for a in fenetre.menuBar().actions()] + \
            [fenetre.panneaux[0].onglets.tabText(i) for i in range(fenetre.panneaux[0].onglets.count())]
    assert textes['fr'] != textes['en']
    assert '&Aide' in textes['fr'] and '&Help' in textes['en']
    fenetre.changer_langue('fr')


@pytest.mark.parametrize('nom', ['DialogueASTAP', 'DialogueAPropos', 'DialogueReglages', 'DialogueSignaler',
                                 'DialogueConsentement'])
def test_dialogues(app_qt, nom):
    from coupole.gui import dialogues
    d = getattr(dialogues, nom)()
    d.show()
    app_qt.processEvents()
    assert not sans_info_bulle(d)
    d.close()


def test_aide_de_chaque_ecran(app_qt, fenetre):
    for p in fenetre.panneaux:
        assert hasattr(p, 'aide_html') and len(p.aide_html()) > 100


def test_catalogue_selection_et_estimation(app_qt, fenetre):
    ohp = fenetre.panneaux[0]
    attendre(app_qt, lambda: ohp.inv is not None and ohp.m_obj.rowCount() > 0)
    for r, o in enumerate(ohp.m_obj.donnees):
        if o['objet'] == '(914) Palisana':
            ohp.v_obj.selectRow(ohp.p_obj.mapFromSource(ohp.m_obj.index(r, 0)).row())
    # sélection appliquée après l'anti-rebond (40 ms), estimation calculée en fond
    attendre(app_qt, lambda: len(ohp.selection) == 16 and '10' in ohp.l_estimation.text(), 10)
    assert len(ohp.selection) == 16 and '10' in ohp.l_estimation.text()


def test_interface_reactive_pendant_un_travail(app_qt, fenetre):
    """Un travail de 1,5 s hors du fil graphique ne doit pas bloquer la boucle d'événements."""
    from coupole.gui.outils import Tache
    t = Tache(time.sleep, 1.5)
    battements = []
    from PyQt6.QtCore import QTimer
    minuteur = QTimer()
    minuteur.timeout.connect(lambda: battements.append(time.monotonic()))
    minuteur.start(50)
    t.start()
    t0 = time.monotonic()
    while t.isRunning() and time.monotonic() - t0 < 5:
        app_qt.processEvents()
        time.sleep(0.005)
    minuteur.stop()
    ecarts = [b - a for a, b in zip(battements, battements[1:])]
    # Un serveur partagé (CI Windows) peut avoir un hoquet isolé sans rapport avec l'application (0,69 s observé) :
    # on exige que 90 % des battements soient à l'heure et qu'aucun trou n'atteigne la seconde — un vrai gel du fil
    # graphique durerait les 1,5 s du travail.
    a_l_heure = sum(1 for e in ecarts if e < 0.1) / len(ecarts)
    assert len(battements) > 15 and a_l_heure >= 0.9 and max(ecarts) < 1.0


def _contraste(a, b):
    """Rapport de contraste WCAG 2 entre deux QColor."""
    def lum(c):
        def canal(v):
            v = v / 255
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * canal(c.red()) + 0.7152 * canal(c.green()) + 0.0722 * canal(c.blue())
    l1, l2 = sorted((lum(a), lum(b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def test_theme_independant_du_systeme_et_lisible(app_qt):
    """Le thème de Coupole remplace celui du système (même un système en mode sombre) et reste lisible :
    contraste WCAG ≥ 4,5 pour le texte, les champs, les boutons, les info-bulles et la sélection."""
    from PyQt6.QtGui import QColor, QPalette
    from coupole.gui import theme
    R = QPalette.ColorRole
    sombre_systeme = QPalette(QColor('#202020'))          # simule un système en mode sombre
    app_qt.setPalette(sombre_systeme)
    try:
        for nom in ('clair', 'sombre'):
            assert theme.appliquer(app_qt, nom) == nom
            assert str(app_qt.property('coupole_style')).lower() == 'fusion'
            p = app_qt.palette()
            for fond, texte in ((R.Window, R.WindowText), (R.Base, R.Text), (R.Button, R.ButtonText),
                                (R.ToolTipBase, R.ToolTipText), (R.Highlight, R.HighlightedText),
                                (R.AlternateBase, R.Text)):
                assert _contraste(p.color(fond), p.color(texte)) >= 4.5, (nom, fond, texte)
            # couleurs de statut (possédée, doublon écarté, échec) lisibles sur tous les fonds des tableaux
            for statut in ('statut_ok', 'statut_ecarte', 'statut_echec', 'statut_partiel', 'texte_doux'):
                for fond in ('base', 'alterne', 'fenetre'):
                    assert _contraste(QColor(theme.THEMES[nom][statut]), QColor(theme.THEMES[nom][fond])) >= 4.5, \
                        (nom, statut, fond)
            assert abs(app_qt.font().pointSizeF() - theme.TAILLE_POINTS) < 0.01
    finally:
        theme.appliquer(app_qt)


def test_menu_apparence_bascule_et_enregistre(app_qt, fenetre):
    """Affichage > Apparence : le thème sombre est le défaut ; la bascule (Ctrl+Maj+D) change la palette tout de
    suite, enregistre le réglage, coche la bonne entrée ; les Préférences lisent le même réglage."""
    from PyQt6.QtGui import QPalette
    from coupole.core import config
    from coupole.gui import theme
    assert config.DEFAUTS['apparence'] == 'sombre'
    config.reglages()['apparence'] = 'sombre'
    theme.appliquer(app_qt)
    fenetre.synchroniser_apparence()
    assert fenetre.act_apparence['sombre'].isChecked() and not fenetre.act_apparence['clair'].isChecked()
    fond_sombre = app_qt.palette().color(QPalette.ColorRole.Window)
    actions = fenetre.menu_apparence.actions()
    assert fenetre.act_apparence['sombre'] in actions and fenetre.act_apparence['clair'] in actions
    bascule = [a for a in actions if a.shortcut().toString() == 'Ctrl+Shift+D']
    assert len(bascule) == 1
    bascule[0].trigger()
    assert config.reglages()['apparence'] == 'clair'
    assert fenetre.act_apparence['clair'].isChecked() and not fenetre.act_apparence['sombre'].isChecked()
    fond_clair = app_qt.palette().color(QPalette.ColorRole.Window)
    assert fond_clair != fond_sombre and fond_clair.lightness() > fond_sombre.lightness()
    # enregistré sur le disque : un nouveau chargement des réglages retrouve « clair »
    import json
    assert json.loads(config.reglages().chemin.read_text(encoding='utf-8'))['apparence'] == 'clair'
    # l'entrée du menu applique directement ; les Préférences montrent le même choix
    fenetre.act_apparence['sombre'].trigger()
    assert config.reglages()['apparence'] == 'sombre'
    assert app_qt.palette().color(QPalette.ColorRole.Window) == fond_sombre
    from coupole.gui import dialogues
    d = dialogues.DialogueReglages(fenetre)
    assert d.apparence.currentData() == 'sombre'
    d.apparence.setCurrentIndex(d.apparence.findData('clair'))
    d.accept()
    assert config.reglages()['apparence'] == 'clair'
    fenetre.synchroniser_apparence()
    assert fenetre.act_apparence['clair'].isChecked()
    # retour au défaut pour les tests suivants
    fenetre.changer_apparence('sombre')
    assert fenetre.act_apparence['sombre'].isChecked()


def test_possession_pastilles_filtre_et_estimation(app_qt, fenetre, tmp_path, inventaire):
    """État simulé du dossier de sortie (ok / doublon / échec / absente) : pastilles et couleurs dans la liste des
    images, colonne « possédé » des objets, filtre « À télécharger seulement », estimation des manquantes, lots."""
    from PyQt6.QtCore import Qt
    from coupole.gui import pastilles
    from coupole.gui.modele import Progression
    from coupole.core import config
    from .test_possession import etat_simule
    ohp = fenetre.panneaux[0]
    attendre(app_qt, lambda: ohp.inv is not None and ohp.m_obj.rowCount() > 0)
    imgs = [x for x in inventaire.images if x['objet'] == '(914) Palisana']
    utiles = [x for x in imgs if not x['doublon']]
    finals = etat_simule(tmp_path, imgs, ok=utiles[:4], doublon=utiles[4:5], echec=utiles[5:6])
    # un index de lots minimal pointant sur le dossier des converties
    dossier_lot = os.path.relpath(os.path.dirname(next(iter(finals.values()))), str(tmp_path)).replace(os.sep, '/')
    (tmp_path / 'INDEX_LOTS.csv').write_text('a;b;c;d;e;f;g;h;i;j;k;l\n%s;ast;(914) Palisana;x;R;4;120;1;0;0;0;Comet\n'
                                             % dossier_lot, encoding='utf-8-sig')
    for nom in ('clair', 'sombre'):
        fenetre.changer_apparence(nom)
        ohp.dest.setText(str(tmp_path))
        ohp._charger_possession()
        attendre(app_qt, lambda: ohp.possession.existe and ohp.possession.dest == str(tmp_path), 20)
        ohp.f_manquantes.setChecked(False)
        for r, o in enumerate(ohp.m_obj.donnees):
            if o['objet'] == '(914) Palisana':
                rang = r
                ohp.v_obj.selectRow(ohp.p_obj.mapFromSource(ohp.m_obj.index(r, 0)).row())
        attendre(app_qt, lambda: len(ohp.selection) == 16 and 'manquante' in ohp.l_estimation.text()
                 and str(ohp.m_obj.lignes[rang][ohp.COL_POSSEDE]) == '5 / 10', 10)
        # objets : colonne « possédé » = (4 converties + 1 doublon) / 10 ; un échec → état « echec » : pastille
        # (triangle orange) en tête de ligne, nom de la même couleur (0.1.8)
        prog = ohp.m_obj.lignes[rang][ohp.COL_POSSEDE]
        assert isinstance(prog, Progression) and (prog.n, prog.total) == (5, 10) and str(prog) == '5 / 10'
        assert prog.etat == 'echec'
        tete = ohp.v_obj.horizontalHeader().logicalIndex(0)
        idx = ohp.m_obj.index(rang, tete)
        assert ohp.m_obj.data(idx, Qt.ItemDataRole.DecorationRole) is not None
        bulle = ohp.m_obj.data(idx, Qt.ItemDataRole.ToolTipRole)
        assert '5 possédées / 10' in bulle and '4 à télécharger' in bulle and '1 échec' in bulle, bulle
        assert '5 possédées / 10' in ohp.m_obj.data(ohp.m_obj.index(rang, ohp.COL_POSSEDE), Qt.ItemDataRole.ToolTipRole)
        assert ohp.m_obj.data(ohp.m_obj.index(rang, ohp.COL_OBJET), Qt.ItemDataRole.ForegroundRole) == \
            pastilles.couleur_statut('echec')
        # images : 16 lignes, statuts et couleurs par ligne, info-bulle avec le fichier local
        assert len(ohp.selection) == 16 and ohp.m_img.rowCount() == 16
        statuts = [ohp.m_img.lignes[r][0] for r in range(16)]
        assert statuts.count('possédée') == 4 and statuts.count('doublon écarté') == 1 and statuts.count('échec') == 1
        for r, x in enumerate(ohp.m_img.donnees):
            st = ohp.possession.statut(x)
            i0 = ohp.m_img.index(r, 0)
            assert ohp.m_img.data(i0, Qt.ItemDataRole.DecorationRole) is not None
            couleur = ohp.m_img.data(ohp.m_img.index(r, 3), Qt.ItemDataRole.ForegroundRole)
            if st == 'absente':
                assert couleur is None
            else:
                assert couleur == pastilles.couleur_statut(st)
            bulle = ohp.m_img.data(i0, Qt.ItemDataRole.ToolTipRole)
            if st == 'ok':
                assert 'img' in bulle and '.xisf' in bulle
        # estimation : seules les manquantes comptent (5 sur 10)
        assert '5' in ohp.l_estimation.text() and ('manquante' in ohp.l_estimation.text())
        # filtre « À télécharger seulement » : plus que les 5 manquantes + les 6 doublons de la base (jamais possédés)
        ohp.f_manquantes.setChecked(True)
        app_qt.processEvents()
        assert all(not ohp.possession.possedee(x) for x in ohp.selection)
        assert len([x for x in ohp.selection if not x['doublon']]) == 5
        ohp.f_manquantes.setChecked(False)
        # lots : colonne complet / incomplet
        ohp._remplir_lots()                       # lu en fond (la destination peut être un partage réseau)
        attendre(app_qt, lambda: ohp.m_lots.rowCount() == 1, 10)
        assert ohp.m_lots.rowCount() == 1
        assert 'incomplet' in ohp.m_lots.lignes[0][ohp.COL_LOT_COMPLET]
        # légende dans la langue et aux couleurs du thème
        assert 'possédée' in ohp.l_legende.text() and pastilles.couleur_statut('ok').name() in ohp.l_legende.text()
    fenetre.changer_apparence(config.DEFAUTS['apparence'])


def test_module_cosmologie(app_qt, fenetre):
    """Le module calcule au démarrage, accepte un redshift reçu d'un autre module, refuse z ≤ 0 en l'expliquant."""
    p = fenetre.ouvrir_module('cosmo')
    assert p is not None
    attendre(app_qt, lambda: p.resultat is not None and p.courbes is not None, 60)
    assert p.m_res.rowCount() > 10 and len(p.trace.series) == 4
    p.recevoir_redshift(0.158, '3C 273')
    attendre(app_qt, lambda: abs(p.resultat['z'] - 0.158) < 1e-9, 30)
    assert '3C 273' in p.objet.text() and p.v_res.isColumnHidden(2) is False
    p.z.setText('-1')
    p.calculer()
    assert 'M 31' in p.l_etat.text()
    p.modele.setCurrentIndex(p.modele.findData('wmap9'))
    p.definir_z(1.0)
    attendre(app_qt, lambda: p.resultat['modele'] == 'wmap9' and abs(p.resultat['z'] - 1) < 1e-9, 60)
    assert p.v_res.isColumnHidden(2) and not p.ok.isEnabled() and not p.shoes.isEnabled()
    p.modele.setCurrentIndex(p.modele.findData('planck18'))
    attendre(app_qt, lambda: p.resultat['modele'] == 'planck18', 60)
    from coupole.gui.outils import attendre_taches
    attendre_taches()


def test_fiche_en_ligne_vers_cosmologie(app_qt, fenetre, monkeypatch):
    """Onglet Fiche en ligne de la Banque OHP (réponse simulée) → « envoyer ce redshift » au module Cosmologie."""
    from coupole.core import enligne
    demandes = []

    def fiche(nom, cat=None, sbdb=None, autres=(), rafraichir=False, delai=8, en_ligne=None):
        demandes.append(nom)
        return {'etat': 'ok', 'demande': nom, 'cache': False, 'perime': False, 'erreur': '', 'raison': '',
                'date': '2026-10-08T12:00:00+00:00',
                'fiche': {'service': 'simbad', 'nom': 'M 31', 'otype': 'AGN', 'type': 'Galaxy', 'ra': 10.68,
                          'dec': 41.27, 'ra_s': '', 'dec_s': '', 'z': 0.5, 'vr': None, 'plx': None, 'flux': {},
                          'ids': [], 'liens': {'simbad': 'https://simbad.u-strasbg.fr/simbad/sim-id?Ident=M%2031'}}}
    monkeypatch.setattr(enligne, 'fiche_objet', fiche)
    ohp = fenetre.ouvrir_module('ohp')
    attendre(app_qt, lambda: ohp.inv is not None and ohp.m_obj.rowCount() > 0)
    for r, o in enumerate(ohp.m_obj.donnees):
        if o['objet'] == 'M31':
            ohp.v_obj.selectRow(ohp.p_obj.mapFromSource(ohp.m_obj.index(r, 0)).row())
    assert demandes == []                                   # onglet caché : aucune requête
    ohp.onglets.setCurrentIndex(ohp.onglet_fiche)
    attendre(app_qt, lambda: ohp.fiche.resultat() is not None, 10)
    assert demandes == ['M31'] and 'M 31' in ohp.fiche.vue.toPlainText()
    assert ohp.fiche.b_cosmo.isEnabled()
    ohp.fiche.b_cosmo.click()
    p = fenetre.panneau_module('cosmo')
    assert fenetre.panneau_courant() is p
    attendre(app_qt, lambda: p.resultat is not None and abs(p.resultat['z'] - 0.5) < 1e-9, 30)
    ohp.onglets.setCurrentIndex(0)
    fenetre.ouvrir_module('ohp')
    from coupole.gui.outils import attendre_taches
    attendre_taches()
