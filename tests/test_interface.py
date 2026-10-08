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
    assert len(battements) > 15 and max(ecarts) < 0.25
