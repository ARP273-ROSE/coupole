"""Interface graphique (sans écran) : info-bulles partout, deux langues, aucun blocage."""
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
    app_qt.processEvents()
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
    # Un serveur partagé (CI Windows) peut avoir un hoquet isolé de ~0,3 s sans rapport avec l'application :
    # on exige que 90 % des battements soient à l'heure et qu'aucun trou n'atteigne une demi-seconde.
    a_l_heure = sum(1 for e in ecarts if e < 0.1) / len(ecarts)
    assert len(battements) > 15 and a_l_heure >= 0.9 and max(ecarts) < 0.5


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
            assert abs(app_qt.font().pointSizeF() - theme.TAILLE_POINTS) < 0.01
    finally:
        theme.appliquer(app_qt, 'clair')


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
