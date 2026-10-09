"""Tout objet Qt naît, vit et MEURT dans le fil graphique.

Cause du plantage natif intermittent de la 0.1.6 (enquête 0.1.7, ``PROGRESSION.md``) : le ramasse-miettes
cyclique de Python se déclenche dans le fil qui alloue au moment où un seuil est franchi — souvent un fil de
calcul (chargement de l'inventaire, sondes, tuiles).  Une fenêtre fermée, retenue seulement par un cycle de
références (fermetures Python, ``Tache`` ↔ panneau…), était alors détruite par CE fil : le destructeur C++ de la
fenêtre et de tous ses widgets tournait hors du fil graphique, pendant que celui-ci continuait de servir les
minuteurs des mêmes widgets.  Constaté (pile Python + pile native, ``gdb``) : le minuteur d'étapes d'un panneau
OHP appelait ``self.recherche.text()`` sur un champ déjà détruit par l'autre fil (« wrapped C/C++ object of type
QLineEdit has been deleted ») ; sans crochet d'exception, PyQt6 en fait un ``qFatal`` → SIGABRT.  Un rang plus
tôt ou plus tard, c'est une écriture en mémoire libérée (SIGSEGV).

Remède (``installer_ramasse_miettes``) : le ramassage automatique est coupé et refait à cadence fixe par un
minuteur du fil graphique — les objets d'un cycle meurent donc toujours dans ce fil.  C'est le remède connu des
applications PyQt à fils (pyqtgraph fait de même).  Le comptage de références, lui, ne change pas : un objet
sans cycle meurt toujours tout de suite, là où sa dernière référence disparaît.

``installer_garde`` (mode test, ``tests/conftest.py`` ; ou ``COUPOLE_GARDE_FIL=1``) fait échouer tout appel de
méthode d'affichage courante hors du fil graphique, et relève les avertissements de Qt qui trahissent un objet
manipulé depuis le mauvais fil.
"""
from __future__ import annotations

import gc
import logging
import threading
import time

log = logging.getLogger(__name__)

PERIODE_MS = 100             # cadence du ramassage dans le fil graphique : petites bouchées (pyqtgraph : 1 s)
COMPLET_MIN_S = 10.0         # au plus un ramassage COMPLET (génération 2) toutes les 10 s…
COMPLET_PART_MAX = 0.02      # …et jamais plus de 2 % du temps (un tas de 80 000 lignes : ~0,1–0,3 s par passage)

_minuteur = None             # QTimer du ramasse-miettes (gardé : sans référence il serait détruit)
_seuils = (700, 10, 10)
_dernier_complet = [0.0, 0.0]    # (instant, durée) du dernier ramassage complet


def fil_principal() -> bool:
    return threading.current_thread() is threading.main_thread()


def _ramasser():
    """Un tour du ramasse-miettes selon les seuils habituels de Python.  Python ne lance un ramassage complet que
    si le quart des objets anciens est nouveau ; faute d'accès à ce compte, on le borne dans le temps : au plus
    un toutes les COMPLET_MIN_S, et au plus COMPLET_PART_MAX du temps (pas de gel sur un gros tas)."""
    c0, c1, c2 = gc.get_count()
    if c0 <= _seuils[0]:
        return
    if c1 <= _seuils[1]:
        gc.collect(0)
        return
    maintenant = time.monotonic()
    instant, duree = _dernier_complet
    if c2 > _seuils[2] and maintenant - instant >= max(COMPLET_MIN_S, duree / COMPLET_PART_MAX):
        gc.collect(2)
        _dernier_complet[:] = [time.monotonic(), time.monotonic() - maintenant]
    else:
        gc.collect(1)


def installer_ramasse_miettes(app=None, periode_ms: int = PERIODE_MS):
    """Coupe le ramassage automatique (qui tournerait dans n'importe quel fil) et le refait dans le fil graphique
    toutes les `periode_ms`.  À appeler une fois, depuis le fil graphique, quand la QApplication existe."""
    global _minuteur, _seuils
    if not fil_principal():
        raise RuntimeError('installer_ramasse_miettes() must be called from the GUI thread')
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication
    app = app or QApplication.instance()
    if _minuteur is not None:
        try:
            from PyQt6 import sip
            if not sip.isdeleted(_minuteur):
                gc.disable()
                return _minuteur
        except Exception:
            pass
    t = gc.get_threshold()
    if t and t[0] > 0:
        _seuils = (t[0], t[1] if len(t) > 1 else 10, t[2] if len(t) > 2 else 10)
    gc.disable()
    _minuteur = QTimer(app)
    _minuteur.setInterval(max(50, int(periode_ms)))
    _minuteur.timeout.connect(_ramasser)
    _minuteur.start()
    if app is not None:
        app.aboutToQuit.connect(_minuteur.stop)
    return _minuteur


def ramasse_miettes_actif() -> bool:
    return _minuteur is not None and not gc.isenabled()


# ======================================================================== garde du mode test
_violations: list[str] = []
_verrou = threading.Lock()
_garde_posee = False

# Méthodes d'affichage NON virtuelles appelées par l'application (une méthode virtuelle remplacée par une fonction
# Python serait prise par sip pour une réimplémentation : on n'y touche pas).
METHODES_GARDEES = {
    'QWidget': ('update', 'repaint', 'show', 'hide', 'setEnabled', 'setToolTip', 'setStyleSheet', 'resize',
                'move', 'setGeometry', 'adjustSize', 'setMinimumSize', 'setMaximumSize', 'setFixedSize',
                'setWindowTitle', 'setFocus', 'raise_', 'activateWindow', 'setCursor', 'updateGeometry'),
    'QLabel': ('setText', 'setPixmap', 'clear', 'setNum'),
    'QLineEdit': ('setText', 'clear', 'setPlaceholderText'),
    'QAbstractButton': ('setText', 'setChecked', 'setIcon', 'click'),
    'QProgressBar': ('setValue', 'setMaximum', 'setMinimum', 'setRange', 'setFormat', 'reset'),
    'QStatusBar': ('showMessage', 'clearMessage'),
    'QPlainTextEdit': ('setPlainText', 'appendPlainText', 'clear'),
    'QTextEdit': ('setPlainText', 'setHtml', 'append', 'clear'),
    'QComboBox': ('addItem', 'addItems', 'clear', 'setCurrentIndex', 'insertItem', 'removeItem'),
    'QSpinBox': ('setValue', 'setRange'),
    'QDoubleSpinBox': ('setValue', 'setRange'),
    'QListWidget': ('addItem', 'addItems', 'clear', 'setCurrentRow'),
    'QTabWidget': ('setCurrentIndex', 'addTab', 'setTabText'),
    'QStackedWidget': ('setCurrentIndex', 'addWidget'),
    'QAbstractItemView': ('clearSelection',),
    'QTableView': ('setColumnWidth', 'resizeColumnsToContents', 'sortByColumn', 'setColumnHidden', 'selectRow'),
}

# Avertissements de Qt qui signalent un objet manipulé depuis un autre fil que le sien.
MOTS_DU_MAUVAIS_FIL = ('another thread', 'different thread', 'outside the GUI thread', 'outside the main thread',
                       'Destroyed while thread is still running', 'can only be used with threads started with QThread',
                       'not safe to use pixmaps outside')


def violations() -> list[str]:
    with _verrou:
        return list(_violations)


def vider_violations() -> list[str]:
    with _verrou:
        v = list(_violations)
        _violations.clear()
    return v


def _noter(texte: str):
    with _verrou:
        _violations.append(texte)


def _gardee(classe: str, nom: str, origine):
    def methode(self, *args, **kwargs):
        if not fil_principal():
            texte = '%s.%s() called from thread %r' % (classe, nom, threading.current_thread().name)
            _noter(texte)
            raise RuntimeError('Qt GUI call outside the GUI thread: ' + texte)
        return origine.__get__(self, type(self))(*args, **kwargs)
    methode.__name__ = nom
    methode.__qualname__ = '%s.%s' % (classe, nom)
    methode._coupole_origine = origine
    return methode


def _rappel_gc(phase, info):
    if phase == 'start' and not fil_principal():
        _noter('Python garbage collection (generation %s) in thread %r: Qt objects of a reference cycle would be '
               'destroyed outside the GUI thread' % (info.get('generation'), threading.current_thread().name))


def installer_garde():
    """Mode test : appel d'affichage hors du fil graphique → RuntimeError + violation notée ; avertissement Qt
    « mauvais fil » et ramassage cyclique hors du fil graphique → violation notée (le test échoue, conftest)."""
    global _garde_posee
    if _garde_posee:
        return
    from PyQt6 import QtWidgets
    from PyQt6.QtCore import qInstallMessageHandler
    for classe, noms in METHODES_GARDEES.items():
        cls = getattr(QtWidgets, classe)
        for nom in noms:
            origine = cls.__dict__.get(nom)
            if origine is None or hasattr(origine, '_coupole_origine'):
                continue
            setattr(cls, nom, _gardee(classe, nom, origine))
    precedent = None

    def messages_qt(mode, contexte, message):
        if any(m in message for m in MOTS_DU_MAUVAIS_FIL):
            _noter('Qt: %s (thread %r)' % (message, threading.current_thread().name))
        if precedent is not None:
            precedent(mode, contexte, message)
        else:
            import sys
            sys.stderr.write(message + '\n')
    precedent = qInstallMessageHandler(messages_qt)
    gc.callbacks.append(_rappel_gc)
    _garde_posee = True
