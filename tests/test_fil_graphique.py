"""Plantage natif intermittent de la 0.1.6 (enquête 0.1.7) : une fenêtre fermée, retenue seulement par un cycle de
références, était détruite par le ramasse-miettes de Python déclenché dans un FIL DE CALCUL, pendant que le fil
graphique servait encore les minuteurs de ses widgets → « wrapped C/C++ object of type QLineEdit has been
deleted » dans un slot de minuteur → qFatal (SIGABRT), ou écriture en mémoire libérée (SIGSEGV).

Ces tests forcent l'ordre qui plantait : objet Qt devenu un déchet cyclique, PUIS un fil qui alloue assez pour
franchir les seuils du ramasse-miettes.  Ils vérifient que la destruction a lieu dans le fil graphique, et que la
garde du mode test refuse les appels d'affichage depuis un autre fil."""
import gc
import threading
import time
import weakref

import pytest

pytest.importorskip('PyQt6')
from coupole.gui import fil_graphique  # noqa: E402


def _tourner(app, s, condition=None):
    t0 = time.monotonic()
    while time.monotonic() - t0 < s:
        app.processEvents()
        if condition is not None and condition():
            return True
        time.sleep(0.005)
    return condition() if condition is not None else True


def _allouer_des_cycles(n=200_000):
    """Ce que fait un fil de calcul ordinaire (astropy, inventaire…) : des conteneurs, dont des cycles."""
    garde = []
    for i in range(n):
        a = [i]
        a.append(a)                      # cycle
        if i % 1000 == 0:
            garde.append(a)
    return len(garde)


def _dans_un_fil(fonction):
    t = threading.Thread(target=fonction, name='fil-de-calcul')
    t.start()
    t.join(60)
    assert not t.is_alive()


def _noter_destruction(objet, journal):
    """Note le fil où l'enveloppe Python meurt : pour un widget sans parent (une fenêtre), c'est là que sip
    détruit l'objet C++ et tous ses enfants (le signal « destroyed » ne parvient plus à Python à ce moment)."""
    return weakref.ref(objet, lambda _r: journal.append(threading.current_thread().name))


def test_ramasse_miettes_dans_le_fil_graphique(app_qt, monkeypatch):
    monkeypatch.setattr(fil_graphique, 'COMPLET_MIN_S', 0.0)     # ramassage complet permis à chaque tour
    from PyQt6.QtWidgets import QLineEdit, QWidget
    assert fil_graphique.ramasse_miettes_actif() and not gc.isenabled()
    journal = []
    w = QWidget()
    champ = QLineEdit(w)
    w.moi = w                            # cycle : seul le ramasse-miettes cyclique peut libérer cette fenêtre
    r = _noter_destruction(w, journal)
    del w, champ
    _dans_un_fil(_allouer_des_cycles)    # avant 0.1.7 : la fenêtre était détruite ICI, dans le fil de calcul
    assert journal == [] and r() is not None
    assert _tourner(app_qt, 5, lambda: journal)
    assert journal == ['MainThread']


def test_cycles_toujours_liberes(app_qt, monkeypatch):
    monkeypatch.setattr(fil_graphique, 'COMPLET_MIN_S', 0.0)
    """Le ramassage automatique est coupé, pas supprimé : les cycles sont libérés à cadence fixe."""

    class Noeud:
        pass
    refs = []
    for _ in range(2000):
        n = Noeud()
        n.moi = n
        refs.append(weakref.ref(n))
    del n
    assert _tourner(app_qt, 5, lambda: all(r() is None for r in refs))


def test_fenetre_fermee_detruite_dans_le_fil_graphique(app_qt, monkeypatch):
    """L'ordre exact du plantage : fenêtre fermée pendant ses étapes d'affichage, mémoire de l'interface remise à
    zéro (la fenêtre n'est plus retenue que par des cycles), puis un fil de calcul qui alloue pendant que le fil
    graphique tourne ses événements."""
    from coupole.core import config
    from coupole.gui import memoire, outils
    from coupole.gui.fenetre import FenetrePrincipale
    from coupole.gui.outils import attendre_taches
    monkeypatch.setattr(fil_graphique, 'COMPLET_MIN_S', 0.0)    # la fenêtre est ancienne (génération 2)
    monkeypatch.setitem(config.reglages().valeurs, 'maj_auto', False)
    f = FenetrePrincipale()
    f.show()
    ohp = f.panneau_module('ohp')
    assert _tourner(app_qt, 60, lambda: ohp.inv is not None)
    journal = []
    refs = [_noter_destruction(f, journal)]
    ohp._plus_tard(ohp._filtrer_objets)               # une étape d'affichage encore en attente
    f.close()
    attendre_taches()
    # une Tache encore en cours (premier calcul de la carte du ciel, Cosmologie…) retient son panneau, donc la
    # fenêtre : on attend qu'elles soient toutes rendues (la remise se fait dans le fil graphique)
    # (des tests remplacent Tache.start : leurs tâches jamais lancées restent dans _actives, sans rien retenir d'ici)
    assert _tourner(app_qt, 120, lambda: not any(t.isRunning() for t in list(outils._actives))), \
        'tâches encore en cours'
    _tourner(app_qt, 0.3)
    memoire.reinitialiser_pour_tests()
    del f, ohp
    fin = threading.Event()

    def calcul():
        while not fin.is_set():
            _allouer_des_cycles(20_000)
    t = threading.Thread(target=calcul, name='fil-de-calcul')
    t.start()
    try:
        assert _tourner(app_qt, 30, lambda: journal), 'fenêtre fermée jamais libérée'
    finally:
        fin.set()
        t.join(30)
    assert journal == ['MainThread'] and refs[0]() is None


def test_garde_refuse_un_appel_hors_du_fil_graphique(app_qt):
    from PyQt6.QtWidgets import QLabel
    l = QLabel('a')
    erreurs = []

    def ecrire():
        try:
            l.setText('b')
        except RuntimeError as e:
            erreurs.append(str(e))
    _dans_un_fil(ecrire)
    assert erreurs and 'outside the GUI thread' in erreurs[0]
    assert l.text() == 'a'
    v = fil_graphique.vider_violations()               # attendue ici : ne fait pas échouer ce test
    assert any('QLabel.setText' in x for x in v)
    l.setText('c')                                     # dans le fil graphique : permis
    assert l.text() == 'c'


def test_garde_releve_les_avertissements_qt_du_mauvais_fil(app_qt):
    from PyQt6.QtCore import QTimer
    minuteur = QTimer()
    _dans_un_fil(lambda: minuteur.start(1000))         # Qt : « Timers cannot be started from another thread »
    v = fil_graphique.vider_violations()
    assert any('another thread' in x for x in v), v
    assert not minuteur.isActive()


def test_garde_releve_un_ramassage_hors_du_fil_graphique(app_qt):
    _dans_un_fil(lambda: gc.collect(0))
    v = fil_graphique.vider_violations()
    assert any('garbage collection' in x and 'fil-de-calcul' in x for x in v), v
