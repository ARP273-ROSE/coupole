"""Outils communs de l'interface : widgets traduits avec info-bulle, travail hors du fil graphique.

Règle : tout widget interactif reçoit une info-bulle (clé ``<cle>_aide``), et tout
texte passe par ``tr``.  Les fabriques ci-dessous l'imposent.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
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
_fils: set = set()                      # threading.Thread enregistrés (traitements, vérifications)
_arrets: set = set()                    # threading.Event à lever à la fermeture
_verrou = threading.Lock()
ARRET_GLOBAL = threading.Event()        # levé une fois pour toutes quand l'application se ferme


def est_detruit(obj) -> bool:
    """True si `obj` est un QObject dont la partie C++ a été détruite (fenêtre fermée)."""
    if obj is None:
        return False
    try:
        from PyQt6 import sip
        return sip.isdeleted(obj)
    except Exception:
        return False


def enregistrer_arret(evenement: threading.Event) -> threading.Event:
    """Un événement d'arrêt que `arreter_tout()` lèvera à la fermeture de l'application."""
    with _verrou:
        _arrets.add(evenement)
    return evenement


def enregistrer_fil(t: threading.Thread) -> threading.Thread:
    with _verrou:
        _fils.add(t)
    return t


def attendre_taches(delai_ms: int = 5000):
    """À la fermeture : laisse finir les travaux en cours (jamais de QThread détruit en marche)."""
    for t in list(_actives):
        t.wait(delai_ms)


def arreter_tout(delai_s: float = 10.0) -> dict:
    """Fermeture de l'application : lève tous les événements d'arrêt, attend les fils et les QThread.

    Renvoie un petit bilan {'taches': n, 'fils': n, 'restants': n} (pour les tests et le journal)."""
    ARRET_GLOBAL.set()
    with _verrou:
        arrets, fils = list(_arrets), list(_fils)
    for e in arrets:
        e.set()
    fin = time.monotonic() + delai_s
    for t in fils:
        if t.is_alive():
            t.join(max(0.05, fin - time.monotonic()))
    attendre_taches(int(max(200, (fin - time.monotonic()) * 1000)))
    restants = sum(1 for t in fils if t.is_alive()) + sum(1 for t in list(_actives) if t.isRunning())
    with _verrou:
        _fils.difference_update({t for t in fils if not t.is_alive()})
    return {'taches': len(_actives), 'fils': len(fils), 'restants': restants}


def _appeler_protege(slot, args, proprietaire):
    """Appelle `slot` dans le fil graphique, sauf si le widget propriétaire a été détruit entre-temps ; une
    exception dans le slot est journalisée et rapportée, jamais fatale (PyQt rendrait sinon l'exception fatale)."""
    if est_detruit(proprietaire):
        return
    try:
        slot(*args)
    except RuntimeError as e:                    # « wrapped C/C++ object … has been deleted »
        if 'deleted' in str(e):
            return
        _rapporter_exception()
    except Exception:
        _rapporter_exception()


def _rapporter_exception():
    from ..core import rapports
    texte = traceback.format_exc()
    logging.getLogger(__name__).error('exception in a slot:\n%s', texte)
    try:
        rapports.signaler_plantage(texte, contexte='slot')
    except Exception:
        pass


class Tache(QThread):
    """Exécute `fonction(*args)` hors du fil graphique ; `fini(resultat)` ou `erreur(texte)` à la fin.

    Le fil n'a pas de parent Qt : il survit à la fermeture du panneau qui l'a lancé (un QThread détruit
    pendant qu'il tourne fait planter le processus) ; une référence est gardée jusqu'à la fin.
    `parent` : le widget pour lequel on travaille.  S'il est détruit avant la fin (fenêtre fermée), rien n'est
    émis vers lui : les slots branchés par `quand_fini()` / `quand_erreur()` ne sont pas appelés, et aucun
    signal Qt ne vise un objet disparu.  `fini` et `erreur` restent disponibles pour les branchements
    directs sur des méthodes de QObject (que Qt débranche lui-même à la destruction du receveur).
    """

    def __init__(self, fonction, *args, parent=None, **kwargs):
        super().__init__(None)
        self.fonction, self.args, self.kwargs = fonction, args, kwargs
        self.proprietaire = parent if isinstance(parent, QObject) else None
        self.s = _Signaux()
        self.fini, self.erreur = self.s.fini, self.s.erreur
        with _verrou:
            _actives.add(self)
        self.finished.connect(self._terminee)

    def _terminee(self):
        with _verrou:
            _actives.discard(self)

    def quand_fini(self, slot):
        """Branche `slot(resultat)`, protégé : ignoré si le widget propriétaire est détruit, jamais fatal."""
        self.fini.connect(lambda r, s=slot, p=self.proprietaire: _appeler_protege(s, (r,), p))
        return self

    def quand_erreur(self, slot):
        self.erreur.connect(lambda e, s=slot, p=self.proprietaire: _appeler_protege(s, (e,), p))
        return self

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
            if not est_detruit(self.proprietaire):
                self.erreur.emit('%s: %s' % (type(e).__name__, e))
            return
        if not est_detruit(self.proprietaire):
            self.fini.emit(r)


class FileEvenements:
    """Événements d'un fil de travail lus par l'interface à cadence fixe (jamais d'appel Qt hors du fil graphique).

    Le minuteur a `parent` pour parent Qt : il s'arrête avec lui ; les événements d'un fil qui survit à la
    fenêtre sont alors simplement abandonnés."""

    def __init__(self, parent, traiter, periode_ms=200):
        self.q: queue.Queue = queue.Queue()
        self.traiter = traiter
        self.parent = parent
        self.timer = QTimer(parent)
        self.timer.timeout.connect(self._vider)
        self.timer.start(periode_ms)

    def __call__(self, ev):
        self.q.put(ev)

    def arreter(self):
        if not est_detruit(self.timer):
            self.timer.stop()

    def _vider(self):
        if est_detruit(self.parent):
            return
        evs = []
        try:
            while len(evs) < 2000:
                evs.append(self.q.get_nowait())
        except queue.Empty:
            pass
        if evs:
            _appeler_protege(self.traiter, (evs,), self.parent)


def lancer_fil(fonction, *args, **kwargs) -> threading.Thread:
    """Fil de fond enregistré : `arreter_tout()` l'attendra à la fermeture."""
    def corps():
        try:
            fonction(*args, **kwargs)
        except Exception:
            _rapporter_exception()
    t = threading.Thread(target=corps, daemon=True)
    enregistrer_fil(t)
    t.start()
    return t
