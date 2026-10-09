"""Interface qui s'adapte à la taille et à la densité de l'écran, sans rien tronquer ni déborder.

Principes :
* aucune taille fixe en pixels : les tailles voulues sont plafonnées à la zone utile de l'écran où s'ouvre la
  fenêtre (barre des tâches exclue), et les fenêtres sont centrées sur cet écran ;
* le contenu de chaque module et de chaque dialogue est placé dans une zone défilante : sur un petit écran (ou à
  150-200 % de mise à l'échelle), on fait défiler au lieu de couper ;
* les textes longs passent à la ligne, les listes déroulantes ne s'élargissent pas au texte le plus long, les
  tableaux gardent des colonnes redimensionnables et abrègent ce qui dépasse (texte complet en info-bulle) ;
* la barre des modules se réduit aux icônes quand la fenêtre est étroite.
Les tests (tests/test_adaptatif.py) vérifient chaque fenêtre et dialogue de 1024×600 à 3840×2160.
"""
from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (QAbstractItemView, QComboBox, QFrame, QHeaderView, QLabel, QLayout, QScrollArea,
                             QTableView, QWidget)

LONGUEUR_LIGNE = 60          # au-delà, un QLabel passe à la ligne
CONTENU_COMBO = 14           # largeur minimale d'une liste déroulante, en caractères (plancher)
CONTENU_COMBO_MAX = 32       # plafond : au-delà, le texte est abrégé plutôt que d'élargir la rangée
TAILLE_MIN = QSize(640, 420)  # plus petite fenêtre principale utilisable (en pixels logiques)


def zone_utile(widget: QWidget | None = None) -> QSize:
    """Zone utile de l'écran du widget (ou de l'écran principal), en pixels logiques."""
    ecran = None
    if widget is not None and widget.screen() is not None:
        ecran = widget.screen()
    if ecran is None:
        ecran = QGuiApplication.primaryScreen()
    if ecran is None:
        return QSize(1280, 800)
    return ecran.availableGeometry().size()


def ajuster(fenetre: QWidget, largeur: int, hauteur: int, part: float = 0.92, cle: str | None = None) -> None:
    """Taille voulue, plafonnée à `part` de la zone utile de l'écran, puis fenêtre centrée sur cet écran.

    `cle` : dialogue dont la taille est gardée d'une ouverture à l'autre (et d'une session à l'autre), toujours
    bornée à l'écran où il s'ouvre (gui/memoire.py)."""
    z = zone_utile(fenetre.parentWidget() or fenetre)
    l = min(largeur, int(z.width() * part))
    h = min(hauteur, int(z.height() * part))
    fenetre.resize(max(l, 200), max(h, 150))
    fenetre.setMaximumSize(QSize(16777215, 16777215))
    ecran = (fenetre.parentWidget() or fenetre).screen() or QGuiApplication.primaryScreen()
    if ecran is not None and fenetre.parentWidget() is None:
        g = ecran.availableGeometry()
        fenetre.move(g.x() + (g.width() - fenetre.width()) // 2, g.y() + (g.height() - fenetre.height()) // 2)
    if cle:
        from . import memoire
        memoire.dialogue(fenetre, cle)


def defilable(contenu: QWidget) -> QScrollArea:
    """Place `contenu` dans une zone défilante sans cadre, qui ne défile que si la place manque."""
    zone = QScrollArea()
    zone.setWidget(contenu)
    zone.setWidgetResizable(True)
    zone.setFrameShape(QFrame.Shape.NoFrame)
    zone.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    zone.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    if contenu.toolTip():
        zone.setToolTip(contenu.toolTip())
    return zone


def assouplir(racine: QWidget) -> None:
    """Rend souples tous les widgets d'un arbre : textes longs à la ligne, listes déroulantes étroites,
    tableaux à colonnes redimensionnables qui abrègent le texte."""
    for lab in racine.findChildren(QLabel):
        # Texte long, ou vide à la construction (rempli plus tard : résumés, états, statistiques) : à la ligne.
        if not lab.wordWrap() and lab.pixmap() is None and (len(lab.text()) > LONGUEUR_LIGNE or not lab.text()):
            lab.setWordWrap(True)
    for cb in racine.findChildren(QComboBox):
        ajuster_combo(cb)
    for t in racine.findChildren(QAbstractItemView):
        t.setTextElideMode(Qt.TextElideMode.ElideRight)
        t.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        if isinstance(t, QTableView):
            en_tete = t.horizontalHeader()
            en_tete.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            en_tete.setStretchLastSection(True)
            en_tete.setMinimumSectionSize(40)
            en_tete.setTextElideMode(Qt.TextElideMode.ElideRight)


def ajuster_combo(cb: QComboBox) -> None:
    """Largeur minimale d'une liste déroulante : assez pour son élément le plus long (jusqu'à CONTENU_COMBO_MAX
    caractères, au moins CONTENU_COMBO), sans jamais s'élargir à l'infini.  Un libellé comme « Planck 2018
    (référence) » n'est ainsi plus coupé."""
    cb.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    plus_long = max((len(cb.itemText(i)) for i in range(cb.count())), default=0)
    cb.setMinimumContentsLength(max(CONTENU_COMBO, min(CONTENU_COMBO_MAX, plus_long + 1)))


class Flux(QLayout):
    """Disposition « en flux » : les widgets se placent de gauche à droite et passent à la ligne suivante
    quand la largeur manque (barres de filtres, rangées de boutons).  D'après l'exemple « Flow Layout » de Qt."""

    def __init__(self, parent=None, marge: int = 0, espace: int = 6):
        super().__init__(parent)
        self._elements = []
        self.setContentsMargins(marge, marge, marge, marge)
        self.setSpacing(espace)

    def addItem(self, element):
        self._elements.append(element)

    def count(self):
        return len(self._elements)

    def itemAt(self, i):
        return self._elements[i] if 0 <= i < len(self._elements) else None

    def takeAt(self, i):
        return self._elements.pop(i) if 0 <= i < len(self._elements) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, largeur):
        return self._placer(QRect(0, 0, largeur, 0), simuler=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._placer(rect, simuler=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        taille = QSize()
        for e in self._elements:
            taille = taille.expandedTo(e.minimumSize())
        m = self.contentsMargins()
        return taille + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _placer(self, rect, simuler):
        m = self.contentsMargins()
        zone = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y, hauteur_ligne = zone.x(), zone.y(), 0
        esp = self.spacing()
        for e in self._elements:
            if e.widget() is not None and not e.widget().isVisibleTo(self.parentWidget() or e.widget()):
                continue
            t = e.sizeHint().expandedTo(e.minimumSize())
            if x + t.width() > zone.right() + 1 and hauteur_ligne > 0:
                x, y, hauteur_ligne = zone.x(), y + hauteur_ligne + esp, 0
            if not simuler:
                e.setGeometry(QRect(QPoint(x, y), QSize(min(t.width(), zone.width()), t.height())))
            x += t.width() + esp
            hauteur_ligne = max(hauteur_ligne, t.height())
        return y + hauteur_ligne - rect.y() + m.bottom()


ESPACE_INSECABLE_NUL = '​'   # espace de largeur nulle : point de coupure invisible


def coupable(texte: str) -> str:
    """Permet à un chemin ou une adresse (sans espaces) de passer à la ligne après chaque séparateur.
    À n'employer que pour l'affichage ; `texte_reel` rend la valeur d'origine."""
    s = str(texte)
    for sep in ('\\', '/'):
        s = s.replace(sep, sep + ESPACE_INSECABLE_NUL)
    return s


def texte_reel(texte: str) -> str:
    return str(texte).replace(ESPACE_INSECABLE_NUL, '')
