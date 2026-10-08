"""Outils communs de l'interface : widgets traduits avec info-bulle, travail hors du fil graphique.

Règle : tout widget interactif reçoit une info-bulle (clé ``<cle>_aide``), et tout
texte passe par ``tr``.  Les fabriques ci-dessous l'imposent.
"""
from __future__ import annotations

import queue
import threading
import traceback

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
                             QToolButton)

from ..core.i18n import tr


def aide(widget, cle_aide: str, **kw):
    t = tr(cle_aide, **kw)
    widget.setToolTip(t)
    if hasattr(widget, 'setStatusTip'):
        widget.setStatusTip(t)
    if hasattr(widget, 'setWhatsThis'):
        widget.setWhatsThis(t)
    return widget


def bouton(cle: str, rappel=None, cle_aide: str | None = None, parent=None) -> QPushButton:
    b = QPushButton(tr(cle), parent)
    aide(b, cle_aide or cle + '_aide')
    if rappel:
        b.clicked.connect(rappel)
    return b


def bouton_outil(cle: str, rappel=None, cle_aide: str | None = None, parent=None) -> QToolButton:
    b = QToolButton(parent)
    b.setText(tr(cle))
    aide(b, cle_aide or cle + '_aide')
    if rappel:
        b.clicked.connect(rappel)
    return b


def action(parent, cle: str, rappel=None, raccourci=None, cle_aide: str | None = None) -> QAction:
    a = QAction(tr(cle), parent)
    aide(a, cle_aide or cle + '_aide')
    if raccourci:
        a.setShortcut(raccourci)
    if rappel:
        a.triggered.connect(rappel)
    return a


def etiquette(cle: str, parent=None, **kw) -> QLabel:
    return QLabel(tr(cle, **kw), parent)


def case(cle: str, coche=False, cle_aide: str | None = None) -> QCheckBox:
    c = QCheckBox(tr(cle))
    c.setChecked(coche)
    return aide(c, cle_aide or cle + '_aide')


def liste(cle_aide: str, elements: list[tuple[str, object]]) -> QComboBox:
    """elements : [(texte affiché, donnée)] ; textes déjà traduits par l'appelant."""
    c = QComboBox()
    for texte, donnee in elements:
        c.addItem(texte, donnee)
    return aide(c, cle_aide)


def champ(cle_aide: str, texte: str = '', cle_indice: str | None = None) -> QLineEdit:
    e = QLineEdit(texte)
    if cle_indice:
        e.setPlaceholderText(tr(cle_indice))
    return aide(e, cle_aide)


def nombre(cle_aide: str, mini: int, maxi: int, valeur: int, cle_special: str | None = None) -> QSpinBox:
    s = QSpinBox()
    s.setRange(mini, maxi)
    s.setValue(valeur)
    if cle_special:
        s.setSpecialValueText(tr(cle_special))
    return aide(s, cle_aide)


def decimal(cle_aide: str, mini: float, maxi: float, valeur: float, suffixe_cle: str | None = None) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(mini, maxi)
    s.setDecimals(1)
    s.setValue(valeur)
    if suffixe_cle:
        s.setSuffix(' ' + tr(suffixe_cle))
    return aide(s, cle_aide)


class _Signaux(QObject):
    fini = pyqtSignal(object)
    erreur = pyqtSignal(str)


_actives: set = set()


def attendre_taches(delai_ms: int = 5000):
    """À la fermeture : laisse finir les travaux en cours (jamais de QThread détruit en marche)."""
    for t in list(_actives):
        t.wait(delai_ms)


class Tache(QThread):
    """Exécute `fonction(*args)` hors du fil graphique ; `fini(resultat)` ou `erreur(texte)` à la fin.

    Le fil n'a pas de parent Qt : il survit à la fermeture du panneau qui l'a lancé (un QThread détruit
    pendant qu'il tourne fait planter le processus) ; une référence est gardée jusqu'à la fin.
    `parent` est accepté pour compatibilité mais ignoré.
    """

    def __init__(self, fonction, *args, parent=None, **kwargs):
        super().__init__(None)
        self.fonction, self.args, self.kwargs = fonction, args, kwargs
        self.s = _Signaux()
        self.fini, self.erreur = self.s.fini, self.s.erreur
        _actives.add(self)
        self.finished.connect(lambda: _actives.discard(self))

    def run(self):
        try:
            r = self.fonction(*self.args, **self.kwargs)
        except Exception as e:  # rapportée à l'interface, jamais un plantage
            from ..core import rapports
            texte = traceback.format_exc()
            try:
                rapports.signaler_plantage(texte, contexte='tache')
            except Exception:
                pass
            self.erreur.emit('%s: %s' % (type(e).__name__, e))
            return
        self.fini.emit(r)


class FileEvenements:
    """Événements d'un fil de travail lus par l'interface à cadence fixe (jamais d'appel Qt hors du fil graphique)."""

    def __init__(self, parent, traiter, periode_ms=200):
        self.q: queue.Queue = queue.Queue()
        self.traiter = traiter
        self.timer = QTimer(parent)
        self.timer.timeout.connect(self._vider)
        self.timer.start(periode_ms)

    def __call__(self, ev):
        self.q.put(ev)

    def _vider(self):
        evs = []
        try:
            while len(evs) < 2000:
                evs.append(self.q.get_nowait())
        except queue.Empty:
            pass
        if evs:
            self.traiter(evs)


def lancer_fil(fonction, *args, **kwargs) -> threading.Thread:
    t = threading.Thread(target=fonction, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t
