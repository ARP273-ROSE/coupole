"""Mémoire de l'interface : tout ce qui se règle à l'écran est retrouvé à la réouverture.

Mécanisme unique pour toute l'application (modules compris) :

* chaque élément à garder est « suivi » sous une clé (``fenetre.geometrie``, ``modules.ohp.recherche``…) : sa
  valeur est rétablie tout de suite depuis ``interface.json`` (``core/etat_interface.py``), puis LUE au moment
  d'écrire (on ne recopie rien à chaque frappe) ;
* un changement ne fait que programmer une écriture : au plus une toutes les ``DELAI_MS`` (2 s), plus une à la
  fermeture de la fenêtre — jamais une écriture par frappe ni par pixel de glissement ;
* l'écriture est atomique et n'a lieu que si quelque chose a changé ; les réglages différés de ``reglages.json``
  (dossier de sortie tapé au clavier…) partent avec elle ;
* la lecture est tolérante : une valeur absente, d'un mauvais type ou hors bornes laisse le défaut.
"""
from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, QRect, QSize, Qt, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

from ..core import config
from ..core.etat_interface import etat

DELAI_MS = 2000
BANDE_TITRE = 32            # hauteur (pixels logiques) de la barre de titre qui doit rester sur un écran
VISIBLE_MIN = 120           # largeur minimale de cette barre visible sur un écran


def _detruit(w) -> bool:
    if w is None:
        return False
    try:
        from PyQt6 import sip
        return sip.isdeleted(w)
    except Exception:
        return False


class Memoire(QObject):
    """Un seul objet pour l'application : sources suivies, minuteur d'écriture différée."""

    def __init__(self):
        super().__init__()
        self.sources: dict[str, tuple] = {}
        self.suspendue = False                 # après « Réinitialiser la disposition » si l'application est occupée
        self.minuteur = QTimer(self)
        self.minuteur.setSingleShot(True)
        self.minuteur.setInterval(DELAI_MS)
        self.minuteur.timeout.connect(self._ecrire_protege)
        self._relier()
        etat().verifier_existence_en_fond()
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._ecrire_protege)

    def _relier(self):
        """Branche les rappels « valeur modifiée » sur l'état et les réglages en vigueur (les tests les recréent)."""
        etat().quand_modifie = self.signaler
        config.reglages().quand_modifie = self.signaler

    # ---------------------------------------------------------------- écriture différée
    def signaler(self, *_):
        """Quelque chose a changé : écriture au plus tard dans DELAI_MS (le minuteur n'est pas relancé à chaque
        changement, sinon une frappe continue repousserait l'écriture indéfiniment)."""
        if self.suspendue or _detruit(self.minuteur):
            return
        if not self.minuteur.isActive():
            self.minuteur.start()

    def capturer(self):
        """Lit la valeur actuelle de chaque élément suivi (widgets détruits : oubliés)."""
        e = etat()
        for cle, (lire, widget) in list(self.sources.items()):
            if _detruit(widget):
                self.sources.pop(cle, None)
                continue
            try:
                v = lire()
            except RuntimeError:                   # objet Qt détruit entre-temps
                self.sources.pop(cle, None)
                continue
            except Exception:
                continue
            if v is not None:
                e.ecrire(cle, v)

    def _ecrire_protege(self):
        """Slot du minuteur : une erreur imprévue d'écriture est journalisée, jamais fatale (PyQt6 ferait d'une
        exception dans un slot un arrêt brutal du processus)."""
        try:
            self.ecrire()
        except Exception:
            import logging
            logging.getLogger(__name__).exception('interface state not written')

    def ecrire(self):
        """Écrit maintenant (minuteur, fermeture) ce qui a changé ; rien si rien n'a changé."""
        if self.suspendue:
            return
        self._relier()
        if not _detruit(self.minuteur):
            self.minuteur.stop()
        self.capturer()
        config.reglages().enregistrer_si_modifie()
        etat().enregistrer()

    def suivre(self, cle: str, lire, widget=None, *signaux):
        """Suit `cle` : `lire()` rend la valeur à garder (None : ne rien changer) ; chaque signal programme une
        écriture différée."""
        self.sources[cle] = (lire, widget)
        for s in signaux:
            s.connect(self.signaler)

    def oublier_sources(self):
        """Avant de reconstruire l'interface (langue) : les anciens widgets ne sont plus lus."""
        self.sources.clear()

    def reinitialiser(self):
        """Oublie toute la disposition : fichier effacé, éléments suivis oubliés (ils ne seront pas réécrits)."""
        self.sources.clear()
        if not _detruit(self.minuteur):
            self.minuteur.stop()
        etat().reinitialiser()


_memoire: Memoire | None = None


def memoire() -> Memoire:
    global _memoire
    if _memoire is None or _detruit(_memoire):
        _memoire = Memoire()
    else:
        _memoire._relier()
    return _memoire


def reinitialiser_pour_tests():
    global _memoire
    if _memoire is not None and not _detruit(_memoire):
        _memoire.minuteur.stop()
        _memoire.sources.clear()
    _memoire = None


def reglage_differe(cle: str, valeur):
    """Un réglage de reglages.json changé au clavier : gardé en mémoire, écrit avec le reste (différé)."""
    memoire()
    config.reglages().differer(cle, valeur)


# ==================================================================== éléments courants
def case(w, cle: str):
    v = etat().lire(cle, None, bool)
    if v is not None:
        w.setChecked(v)
    memoire().suivre(cle, w.isChecked, w, w.toggled)


def _donnee_simple(v):
    return v if v is None or isinstance(v, (str, int, float, bool)) else None


def liste(w, cle: str):
    """Liste déroulante : on garde la DONNÉE de l'élément choisi (pas son rang, ni son texte traduit)."""
    v = etat().lire(cle, None, (str, int, float))
    if v is not None:
        i = w.findData(v)
        if i >= 0:
            w.setCurrentIndex(i)
    memoire().suivre(cle, lambda: _donnee_simple(w.currentData()) if w.currentIndex() >= 0 else None,
                     w, w.currentIndexChanged)


def champ(w, cle: str):
    v = etat().lire(cle, None, str)
    if v is not None:
        w.setText(v[:4096])
    memoire().suivre(cle, w.text, w, w.textChanged)


def nombre(w, cle: str):
    """QSpinBox / QDoubleSpinBox : valeur gardée, bornée par celles du widget."""
    v = etat().lire(cle, None, (int, float))
    if v is not None and w.minimum() <= v <= w.maximum():
        w.setValue(v if not hasattr(w, 'decimals') else float(v))
    memoire().suivre(cle, w.value, w, w.valueChanged)


def onglets(w, cle: str):
    i = etat().lire_entier(cle, None, 0, w.count() - 1)
    if i is not None:
        w.setCurrentIndex(i)
    memoire().suivre(cle, lambda: w.currentIndex() if w.currentIndex() >= 0 else None, w, w.currentChanged)


def separateur(sp, cle: str):
    """QSplitter : tailles des volets (rétablies si leur nombre correspond)."""
    v = etat().lire(cle, None, list)
    if v and len(v) == sp.count() and all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 100000
                                          for x in v) and sum(v) > 0:
        sp.setSizes(v)

    def lire():
        t = sp.sizes()
        return t if sum(t) > 0 else None           # jamais affiché : on garde ce qui était enregistré
    memoire().suivre(cle, lire, sp, sp.splitterMoved)


# ---------------------------------------------------------------- colonnes des tableaux
PROPRIETE_LARGEURS = 'coupole_largeurs_gardees'


def _bouton_gauche_enfonce() -> bool:
    """Une colonne redimensionnée bouton gauche enfoncé l'est par l'utilisateur (et non par Qt : dernière colonne
    étirée, ajustement au contenu)."""
    return bool(QApplication.mouseButtons() & Qt.MouseButton.LeftButton)


def entete(vue, cle: str, version: int = 1):
    """QTableView : largeur et ordre des colonnes, colonne et sens du tri.

    Les largeurs ne sont gardées qu'une fois choisies par l'utilisateur (glisser une séparation) ; tant qu'il ne
    l'a pas fait, les colonnes continuent de s'ajuster au contenu (voir `ajuster_colonnes`).

    `version` : à augmenter quand l'ordre par défaut des colonnes change (posé sur la vue AVANT l'appel). Un ordre
    gardé par une version antérieure qui est l'ordre d'origine (0, 1, 2…, jamais modifié à la main) cède alors la
    place au nouvel ordre par défaut ; un ordre choisi par l'utilisateur est toujours respecté."""
    h = vue.horizontalHeader()
    n = h.count()
    d = etat().lire(cle, None, dict)
    if d and d.get('n') == n:
        ordre = d.get('ordre')
        ancienne = not isinstance(d.get('version'), int) or d.get('version') < version
        if ancienne and ordre == list(range(n)):
            ordre = None                            # ordre d'origine d'une version antérieure : nouveau défaut
        if isinstance(ordre, list) and sorted(ordre) == list(range(n)) and \
                all(isinstance(x, int) and not isinstance(x, bool) for x in ordre):
            for visuel, logique in enumerate(ordre):
                actuel = h.visualIndex(logique)
                if actuel != visuel:
                    h.moveSection(actuel, visuel)
        larg = d.get('largeurs')
        if isinstance(larg, list) and len(larg) == n and \
                all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 5000 for x in larg):
            for c, l in enumerate(larg):
                if l > 0:
                    vue.setColumnWidth(c, max(h.minimumSectionSize(), l))
            vue.setProperty(PROPRIETE_LARGEURS, True)
        tri = d.get('tri')
        if isinstance(tri, list) and len(tri) == 2 and all(isinstance(x, int) and not isinstance(x, bool)
                                                           for x in tri) and -1 <= tri[0] < n and \
                vue.isSortingEnabled():
            ordre_qt = Qt.SortOrder.DescendingOrder if tri[1] == 1 else Qt.SortOrder.AscendingOrder
            if tri[0] >= 0:
                vue.sortByColumn(tri[0], ordre_qt)

    def redimensionnee(*_):
        if _bouton_gauche_enfonce():                # l'utilisateur glisse une séparation
            vue.setProperty(PROPRIETE_LARGEURS, True)
            memoire().signaler()

    def lire():
        hh = vue.horizontalHeader()
        m = hh.count()
        out = {'n': m, 'ordre': [hh.logicalIndex(i) for i in range(m)]}
        if version > 1:
            out['version'] = version
        if vue.isSortingEnabled():
            out['tri'] = [hh.sortIndicatorSection() if hh.sortIndicatorSection() < m else -1,
                          1 if hh.sortIndicatorOrder() == Qt.SortOrder.DescendingOrder else 0]
        if vue.property(PROPRIETE_LARGEURS):
            out['largeurs'] = [hh.sectionSize(c) for c in range(m)]
        elif d and isinstance(d.get('largeurs'), list):
            out['largeurs'] = d['largeurs']
        return out
    h.sectionResized.connect(redimensionnee)
    memoire().suivre(cle, lire, vue, h.sectionMoved, h.sortIndicatorChanged)


def ajuster_colonnes(vue):
    """Colonnes ajustées au contenu… sauf si l'utilisateur a choisi ses largeurs (gardées d'une fois à l'autre)."""
    if not vue.property(PROPRIETE_LARGEURS):
        vue.resizeColumnsToContents()


# ---------------------------------------------------------------- géométrie des fenêtres
def _ecran_nomme(nom):
    for s in QGuiApplication.screens():
        if s.name() == nom:
            return s
    return None


def geometrie_fenetre(f) -> dict:
    g = f.normalGeometry() if f.isMaximized() or f.isFullScreen() else f.geometry()
    if not g.isValid():
        g = f.geometry()
    ecran = f.screen()
    return {'x': g.x(), 'y': g.y(), 'l': g.width(), 'h': g.height(), 'maximisee': bool(f.isMaximized()),
            'ecran': ecran.name() if ecran is not None else ''}


def rectangle_visible(rect: QRect, zones) -> bool:
    """La barre de titre de `rect` est-elle assez sur l'un des écrans (zones utiles) pour qu'on puisse l'attraper ?"""
    bande = QRect(rect.x(), rect.y(), rect.width(), BANDE_TITRE)
    for z in zones:
        i = bande.intersected(z)
        if i.width() >= min(VISIBLE_MIN, rect.width()) and i.height() >= BANDE_TITRE // 2 and rect.y() >= z.y() - 2:
            return True
    return False


def placer(f, g, mini: QSize | None = None) -> str:
    """Rétablit la géométrie `g` (dict de `geometrie_fenetre`) avec garde-fous ; rend ce qui a été fait :
    'aucune' (rien de valide), 'restauree', 'ajustee' (plus grande que l'écran : réduite et ramenée dessus),
    'recentree' (écran disparu ou position hors des écrans)."""
    if not isinstance(g, dict):
        return 'aucune'
    try:
        x, y, l, h = (int(g[k]) for k in ('x', 'y', 'l', 'h'))
        if any(isinstance(g[k], bool) for k in ('x', 'y', 'l', 'h')):
            return 'aucune'
    except (KeyError, TypeError, ValueError):
        return 'aucune'
    if l <= 0 or h <= 0 or abs(x) > 10 ** 6 or abs(y) > 10 ** 6:
        return 'aucune'
    nom = g.get('ecran') if isinstance(g.get('ecran'), str) else ''
    ecran = _ecran_nomme(nom) if nom else None
    connu = ecran is not None
    if ecran is None:
        ecran = QGuiApplication.screenAt(QRect(x, y, l, h).center()) or QGuiApplication.primaryScreen()
    if ecran is None:
        f.resize(l, h)
        return 'restauree'
    zone = ecran.availableGeometry()
    mini = mini or QSize(200, 150)
    l0, h0 = l, h
    l = max(min(l, zone.width()), min(mini.width(), zone.width()))
    h = max(min(h, zone.height()), min(mini.height(), zone.height()))
    rect = QRect(x, y, l, h)
    zones = [s.availableGeometry() for s in QGuiApplication.screens()]
    resultat = 'restauree'
    if (nom and not connu) or not rectangle_visible(rect, zones):
        rect.moveTopLeft(zone.topLeft() + QRect(0, 0, zone.width() - l, zone.height() - h).center())
        resultat = 'recentree'
    elif (l, h) != (l0, h0):                       # plus grande que l'écran (résolution réduite) : ramenée dessus
        rect.moveLeft(max(zone.left(), min(rect.left(), zone.right() + 1 - l)))
        rect.moveTop(max(zone.top(), min(rect.top(), zone.bottom() + 1 - h)))
        resultat = 'ajustee'
    f.setGeometry(rect)                            # géométrie du contenu, comme celle qui a été gardée
    if g.get('maximisee') is True:
        f.setWindowState(f.windowState() | Qt.WindowState.WindowMaximized)
    return resultat


class _GardienDialogue(QObject):
    """Retient la taille d'un dialogue quand il se ferme (ou se cache)."""

    def __init__(self, dialogue, cle):
        super().__init__(dialogue)
        self.cle = cle

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.Type.Hide, QEvent.Type.Close):
            etat().ecrire(self.cle, [obj.width(), obj.height()])
        return False


def dialogue(d, cle: str):
    """Taille d'un dialogue gardée (`dialogues.<cle>`), bornée à l'écran ; la position suit la fenêtre principale."""
    cle = 'dialogues.' + cle
    v = etat().lire(cle, None, list)
    if v and len(v) == 2 and all(isinstance(x, int) and not isinstance(x, bool) and 100 <= x <= 20000 for x in v):
        ecran = (d.parentWidget() or d).screen() or QGuiApplication.primaryScreen()
        if ecran is not None:
            z = ecran.availableGeometry()
            mini = d.minimumSize()
            d.resize(max(min(v[0], z.width()), min(mini.width(), z.width())),
                     max(min(v[1], z.height()), min(mini.height(), z.height())))
    d.installEventFilter(_GardienDialogue(d, cle))
    memoire()


# ---------------------------------------------------------------- dialogues de fichiers
def dossier(cle: str, defaut: str = '') -> str:
    """Dossier où rouvrir le dialogue de fichiers `cle` (le dernier utilisé, s'il existe ; sinon `defaut`)."""
    memoire()
    return etat().dossier(cle, defaut)


def retenir(cle: str, chemin: str, est_fichier: bool = False):
    memoire()
    etat().retenir_dossier(cle, chemin, est_fichier)
