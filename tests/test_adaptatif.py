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
    # chemin long sans espace, comme sous Windows (C:\\Users\\…) : il doit pouvoir passer à la ligne
    ancien = config.reglages()['dossier_sortie']
    config.reglages()['dossier_sortie'] = ('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\'
                                           'pytest-0\\un_dossier_de_sortie_au_nom_tres_long\\OHP_DU_ECU')
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
    config.reglages()['dossier_sortie'] = ancien


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


def test_chemins_coupables_et_reversibles():
    from coupole.gui.adaptatif import coupable, texte_reel
    for s in ('C:\\Users\\x\\OHP_DU_ECU', '/home/x/OHP_DU_ECU', 'http://tap-ufe.obspm.fr/tap', 'sans separateur'):
        assert texte_reel(coupable(s)) == s
    assert '\u200b' in coupable('/a/b')


def _pages_affichees(app_qt, f):
    """Chaque module, puis chaque onglet de chaque QTabWidget du module : (nom, panneau) après affichage."""
    from PyQt6.QtWidgets import QTabWidget
    for i in range(f.barre.count()):
        f.barre.setCurrentRow(i)
        _attendre(app_qt, 0.15)
        p = f.panneaux[i]
        onglets = [t for t in p.findChildren(QTabWidget) if t.isVisibleTo(p)]
        if not onglets:
            yield '%d' % i, p
        for t in onglets:
            for k in range(t.count()):
                t.setCurrentIndex(k)
                _attendre(app_qt, 0.1)
                yield '%d/%s' % (i, t.tabText(k)), p


@pytest.mark.parametrize('largeur', [1366, 2000])
def test_entetes_de_tableaux_jamais_tronques(app_qt, fenetre_adaptative, largeur):
    """Retour d'utilisateur (Qualité, 0.1.8) : « étoiles mesurées » affiché « toiles mesurée ».  Chaque section visible
    de chaque tableau visible est au moins aussi large que son titre (police de l'en-tête, échelle comprise :
    lancé aussi à QT_SCALE_FACTOR = 1,5 et 2), et le titre entier est en info-bulle."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QTableView
    f = fenetre_adaptative
    f.resize(largeur, 900)
    _attendre(app_qt)
    vus, fautes = 0, []
    for nom, p in _pages_affichees(app_qt, f):
        for v in p.findChildren(QTableView):
            h = v.horizontalHeader()
            if not v.isVisibleTo(p) or v.model() is None or h.isHidden():
                continue
            fm = h.fontMetrics()
            for c in range(h.count()):
                if h.isSectionHidden(c):
                    continue
                texte = str(v.model().headerData(c, Qt.Orientation.Horizontal) or '')
                if not texte:
                    continue
                vus += 1
                besoin = fm.horizontalAdvance(texte)
                if h.sectionSize(c) < besoin:
                    fautes.append((nom, texte, h.sectionSize(c), besoin))
                assert v.model().headerData(c, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole) == texte
    assert vus > 20 and not fautes, fautes


def test_entete_garde_la_largeur_du_titre(app_qt):
    """Une largeur mémorisée trop petite, ou un glissement de la séparation, ne tronque pas le titre."""
    from coupole.gui.modele import ModeleTableau, vue_tableau
    m = ModeleTableau(['fichier', 'étoiles mesurées', 'FWHM (px)'])
    v, _ = vue_tableau(m, 'qual_table_aide')
    v.resize(800, 300)
    v.show()
    _attendre(app_qt, 0.1)
    h = v.horizontalHeader()
    besoin = h.fontMetrics().horizontalAdvance('étoiles mesurées')
    assert h.sectionSize(1) >= besoin
    v.setColumnWidth(1, 20)
    assert h.sectionSize(1) >= besoin
    v.close()


def test_conteneurs_sans_info_bulle_sur_leurs_enfants(app_qt, fenetre_adaptative):
    """Retour d'utilisateur : l'info-bulle des onglets de la Banque OHP restait affichée par-dessus le groupe
    « Solution astrométrique ».  Un QTabWidget, une zone défilante ou un groupe n'a pas d'info-bulle propre (elle
    s'afficherait au survol de n'importe lequel de ses enfants) : l'aide des onglets est sur chaque onglet."""
    from PyQt6.QtWidgets import QGroupBox, QScrollArea, QStackedWidget, QTabWidget
    f = fenetre_adaptative
    fautes = []
    for p in f.panneaux:
        for typ in (QTabWidget, QScrollArea, QGroupBox, QStackedWidget):
            for w in p.findChildren(typ):
                if w.toolTip():
                    fautes.append((type(w).__name__, w.toolTip()[:60]))
                if isinstance(w, QScrollArea) and w.viewport().toolTip():
                    fautes.append(('viewport', w.viewport().toolTip()[:60]))
    for t in (t for p in f.panneaux for t in p.findChildren(QTabWidget)):
        if t.count() > 1:
            assert all(t.tabToolTip(k) for k in range(t.count())), [t.tabText(k) for k in range(t.count())]
    assert not fautes, fautes
