"""L'interface tient sur tous les écrans, du petit portable (1024×600, ou 1366×768 à 150 %) à la 4K :
rien n'impose une taille plus grande que l'écran, rien n'est tronqué, la barre des modules se compacte."""
import time

import pytest

ECRANS = [(853, 480), (1024, 600), (1280, 720), (1366, 768), (1920, 1080), (3840, 2160)]


def _attendre(app, s=0.3):
    t0 = time.monotonic()
    while time.monotonic() - t0 < s:
        app.processEvents()


def _labels_coupes(racine):
    """QLabel visibles dont le texte ne tient pas (ni retour à la ligne, ni place suffisante)."""
    from PyQt6.QtWidgets import QLabel
    coupes = []
    for lab in racine.findChildren(QLabel):
        if not lab.isVisibleTo(racine) or not lab.text() or lab.wordWrap() or lab.pixmap() is not None:
            continue
        if lab.width() + 1 < lab.minimumSizeHint().width():
            coupes.append(lab.text()[:50])
    return coupes


@pytest.fixture(scope='module')
def fenetre_adaptative(app_qt):
    """Une seule fenêtre pour toutes les tailles ; on attend la fin des tâches de fond avant de la détruire."""
    from coupole.core import config
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    from coupole.gui.fenetre import FenetrePrincipale
    from coupole.gui.outils import attendre_taches
    f = FenetrePrincipale()
    f.show()
    t0 = time.monotonic()
    while f.panneaux[0].inv is None and time.monotonic() - t0 < 60:
        app_qt.processEvents()
        time.sleep(0.01)
    yield f
    f.close()
    attendre_taches()


@pytest.mark.parametrize('largeur,hauteur', ECRANS)
def test_fenetre_principale_tient_sur_l_ecran(app_qt, fenetre_adaptative, largeur, hauteur):
    f = fenetre_adaptative
    mini = f.minimumSizeHint().expandedTo(f.minimumSize())
    assert mini.width() <= max(largeur, 640) and mini.height() <= max(hauteur, 420), (mini, largeur, hauteur)
    f.resize(largeur, hauteur)
    _attendre(app_qt)
    assert f.width() <= max(largeur, 640) and f.height() <= max(hauteur, 420)
    for i in range(f.barre.count()):
        f.barre.setCurrentRow(i)
        _attendre(app_qt, 0.15)
        page = f.pile.currentWidget()
        assert page.geometry().right() <= f.width() and page.geometry().bottom() <= f.height()
        assert not _labels_coupes(f.panneaux[i]), (largeur, i, _labels_coupes(f.panneaux[i]))
        # aucun élément visible n'exige plus de largeur que la zone d'affichage (sinon : ascenseur horizontal)
        from PyQt6.QtWidgets import QWidget
        dispo = page.viewport().width() if hasattr(page, 'viewport') else page.width()
        if largeur >= 1024:
            trop = [(w.minimumSizeHint().width(), type(w).__name__) for w in f.panneaux[i].findChildren(QWidget)
                    if w.isVisibleTo(f.panneaux[i]) and w.minimumSizeHint().width() > dispo + 2]
            # pour le diagnostic : tous les descendants larges, visibles ou non (onglets cachés compris)
            larges = sorted(((w.minimumSizeHint().width(), type(w).__name__, (w.text()[:30] if hasattr(w, 'text')
                              and callable(w.text) else '') or w.toolTip()[:30])
                             for w in f.panneaux[i].findChildren(QWidget) if w.minimumSizeHint().width() > 500),
                            key=lambda x: x[0], reverse=True)
            assert not trop, (largeur, i, dispo, trop[:4], larges[:12])
    compacte = all(not f.barre.item(i).text() for i in range(f.barre.count()))
    assert compacte == (largeur < f.SEUIL_COMPACT)


def test_dialogues_tiennent_sur_un_petit_ecran(app_qt):
    from coupole.gui import dialogues as D
    for classe in (D.DialogueReglages, D.DialogueASTAP, D.DialogueAPropos, D.DialogueSignaler,
                   D.DialogueConsentement):
        d = classe()
        mini = d.minimumSizeHint().expandedTo(d.minimumSize())
        assert mini.width() <= 853 and mini.height() <= 480, (classe.__name__, mini)
        d.resize(853, 480)
        d.show()
        _attendre(app_qt, 0.1)
        assert not _labels_coupes(d), (classe.__name__, _labels_coupes(d))
        d.close()
    from coupole.gui.outils import attendre_taches
    attendre_taches()                            # l'assistant ASTAP cherche en fond : on attend avant de quitter
