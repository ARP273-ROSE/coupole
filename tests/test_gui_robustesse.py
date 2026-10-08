"""Interface : signaux vers des widgets détruits, slots qui lèvent, fermeture qui arrête tout, aucune sonde ni
requête dans le fil graphique au démarrage, listes déroulantes jamais coupées, tableau de la Cosmologie sans
défilement horizontal à 1400 px."""
import threading
import time

import pytest

pytest.importorskip('PyQt6')
from PyQt6.QtWidgets import QComboBox, QWidget  # noqa: E402

from coupole.gui import outils  # noqa: E402


def _tourner(app, s):
    t0 = time.monotonic()
    while time.monotonic() - t0 < s:
        app.processEvents()
        time.sleep(0.005)


def test_tache_vers_widget_detruit_ne_rappelle_pas(app_qt):
    w = QWidget()
    appels = []
    t = outils.Tache(lambda: time.sleep(0.4) or 'r', parent=w)
    t.quand_fini(lambda r: appels.append(r))
    t.start()
    from PyQt6 import sip
    sip.delete(w)                                         # la fenêtre disparaît pendant le travail
    assert outils.est_detruit(w)
    t.wait(5000)
    _tourner(app_qt, 0.3)
    assert appels == []                                   # rien n'est livré à un widget qui n'existe plus


def test_slot_qui_leve_nest_jamais_fatal(app_qt, monkeypatch):
    from coupole.core import rapports
    signales = []
    monkeypatch.setattr(rapports, 'signaler_plantage', lambda texte, **c: signales.append(c) or {})
    w = QWidget()
    t = outils.Tache(lambda: 1, parent=w)

    def slot(r):
        raise ValueError('boum')
    t.quand_fini(slot)
    t.start()
    t.wait(5000)
    _tourner(app_qt, 0.3)
    assert signales and signales[0].get('contexte') == 'slot'   # rapporté, l'application continue


def test_arreter_tout_arrete_fils_et_taches(app_qt):
    arret = outils.enregistrer_arret(threading.Event())
    vu = {'fin': False}

    def boucle():
        arret.wait(30)
        vu['fin'] = True
    fil = outils.lancer_fil(boucle)
    t = outils.Tache(lambda: arret.wait(30))
    t.start()
    t0 = time.monotonic()
    bilan = outils.arreter_tout(delai_s=10)
    assert time.monotonic() - t0 < 5 and vu['fin'] and not fil.is_alive() and bilan['restants'] == 0
    outils.ARRET_GLOBAL.clear()


def test_fenetre_se_ferme_pendant_un_travail(app_qt, monkeypatch):
    """Fermer la fenêtre pendant une tâche de fond : tout est arrêté et attendu, aucun fil ne survit."""
    from coupole.core import config
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.show()
    _tourner(app_qt, 0.2)
    ohp = f.panneaux[0]
    ohp.arret = outils.enregistrer_arret(threading.Event())
    ohp._fil = outils.lancer_fil(lambda: ohp.arret.wait(30))
    from PyQt6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, 'question', staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    t0 = time.monotonic()
    f.close()                                             # « un traitement est en cours, quitter ? » → oui
    _tourner(app_qt, 0.2)
    assert time.monotonic() - t0 < 10 and not ohp._fil.is_alive()
    outils.ARRET_GLOBAL.clear()


def test_aucune_sonde_bloquante_au_demarrage(app_qt, monkeypatch):
    """Détection d'ASTAP (sous-processus), sondes machine, requêtes réseau : jamais dans le fil graphique."""
    from coupole.core import astap, machine, reseau
    fil_gui = threading.get_ident()
    fautes = []

    def garde(nom, orig):
        def f(*a, **k):
            if threading.get_ident() == fil_gui:
                fautes.append(nom)
            return orig(*a, **k)
        return f
    monkeypatch.setattr(astap, 'detecter', garde('astap.detecter', astap.detecter))
    monkeypatch.setattr(machine, 'detecter', garde('machine.detecter', machine.detecter))
    monkeypatch.setattr(reseau, 'requete', garde('reseau.requete', reseau.requete))
    monkeypatch.setattr(reseau, 'tap_sync', garde('reseau.tap_sync', reseau.tap_sync))
    from coupole.core import config
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.show()
    t0 = time.monotonic()
    while f.panneaux[0].inv is None and time.monotonic() - t0 < 60:
        _tourner(app_qt, 0.02)
    for i in range(f.barre.count()):                       # chaque module affiché une fois
        f.barre.setCurrentRow(i)
        _tourner(app_qt, 0.3)
    from coupole.gui import dialogues
    for classe in (dialogues.DialogueASTAP, dialogues.DialogueAPropos):
        d = classe(f)
        d.show()
        _tourner(app_qt, 0.3)
        d.close()
    f.close()
    outils.attendre_taches()
    assert fautes == []


def test_listes_deroulantes_jamais_coupees(app_qt):
    """Le libellé le plus long de chaque liste déroulante tient dans sa largeur minimale (« Planck 2018 (référence) »)."""
    from coupole.core import config
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.resize(1400, 860)
    f.show()
    _tourner(app_qt, 0.3)
    coupes = []
    for cb in f.findChildren(QComboBox):
        if cb.count() == 0 or not cb.isVisibleTo(f):
            continue
        fm = cb.fontMetrics()
        plus_long = max(fm.horizontalAdvance(cb.itemText(i)) for i in range(cb.count()))
        marge = 36                                          # flèche et bordures
        if plus_long + marge > cb.minimumSizeHint().width() + 2 and len(max((cb.itemText(i) for i in range(cb.count())), key=len)) <= 32:
            coupes.append((cb.toolTip()[:40], max((cb.itemText(i) for i in range(cb.count())), key=len)))
    f.close()
    outils.attendre_taches()
    assert not coupes, coupes


def test_cosmologie_sans_defilement_horizontal_a_1400(app_qt):
    from coupole.core import config
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    from coupole.gui.fenetre import FenetrePrincipale
    from PyQt6.QtCore import Qt
    f = FenetrePrincipale()
    f.resize(1400, 860)
    f.show()
    p = f.ouvrir_module('cosmo')
    p.shoes.setChecked(True)
    t0 = time.monotonic()
    while (p.resultat is None or 'shoes' not in p.resultat) and time.monotonic() - t0 < 60:
        _tourner(app_qt, 0.05)
    _tourner(app_qt, 0.3)
    assert p.splitter.orientation() == Qt.Orientation.Vertical       # courbes sous le tableau à 1400 px
    v = p.v_res
    visibles = [c for c in range(p.m_res.columnCount()) if not v.isColumnHidden(c)]
    assert 3 in visibles                                            # colonne SH0ES affichée
    assert sum(v.columnWidth(c) for c in visibles) <= v.viewport().width() + 2
    assert v.horizontalScrollBar().maximum() == 0
    f.resize(1920, 1080)
    _tourner(app_qt, 0.3)
    assert p.splitter.orientation() == Qt.Orientation.Horizontal
    f.close()
    outils.attendre_taches()
