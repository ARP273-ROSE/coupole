"""Modèle de tableau générique (rapide sur des milliers de lignes) avec tri et filtre."""
from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QRect, QSortFilterProxyModel, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QStyle, QStyledItemDelegate, QTableView

from .outils import aide


class Progression:
    """Valeur de cellule « n / total » : s'affiche telle quelle, se trie par fraction, se dessine en mini-barre
    (`DelegueProgression`)."""

    __slots__ = ('n', 'total')

    def __init__(self, n: int, total: int):
        self.n, self.total = int(n), int(total)

    @property
    def fraction(self) -> float:
        return self.n / self.total if self.total > 0 else 0.0

    def __str__(self):
        return '%d / %d' % (self.n, self.total)

    def __lt__(self, autre):
        if not isinstance(autre, Progression):
            return NotImplemented
        return (self.fraction, self.total) < (autre.fraction, autre.total)

    def __eq__(self, autre):
        return isinstance(autre, Progression) and (self.n, self.total) == (autre.n, autre.total)

    def __hash__(self):
        return hash((self.n, self.total))


class ModeleTableau(QAbstractTableModel):
    """lignes : liste de tuples de valeurs affichables ; donnees : objet associé à chaque ligne.

    styles (facultatif) : un dict par ligne — ``couleur`` (QColor du texte de toute la ligne), ``icones``
    ({colonne: QIcon}), ``bulles`` ({colonne: info-bulle propre à la cellule, prioritaire sur celle de la ligne}).
    """

    def __init__(self, entetes: list[str], parent=None):
        super().__init__(parent)
        self.entetes = entetes
        self.lignes: list[tuple] = []
        self.donnees: list = []
        self.infobulles: list = []
        self.styles: list = []

    def remplir(self, lignes, donnees=None, infobulles=None, styles=None):
        self.beginResetModel()
        self.lignes = list(lignes)
        self.donnees = list(donnees) if donnees is not None else [None] * len(self.lignes)
        self.infobulles = list(infobulles) if infobulles is not None else []
        self.styles = list(styles) if styles is not None else []
        self.endResetModel()

    def restyler(self, styles):
        """Change seulement les styles (couleurs, icônes) : la vue redessine sans perdre sélection ni tri."""
        self.styles = list(styles) if styles is not None else []
        if self.lignes:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.lignes) - 1, len(self.entetes) - 1))

    def ajouter(self, lignes, donnees=None, infobulles=None):
        """Ajoute des lignes sans reconstruire le modèle (beginInsertRows) : la vue ne redessine que l'ajout."""
        lignes = list(lignes)
        if not lignes:
            return
        debut = len(self.lignes)
        self.beginInsertRows(QModelIndex(), debut, debut + len(lignes) - 1)
        self.lignes.extend(lignes)
        self.donnees.extend(list(donnees) if donnees is not None else [None] * len(lignes))
        if self.infobulles or infobulles:
            self.infobulles.extend(list(infobulles) if infobulles is not None else [''] * len(lignes))
        if self.styles:
            self.styles.extend([{}] * len(lignes))
        self.endInsertRows()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.lignes)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.entetes)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        v = self.lignes[index.row()][index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(v, float):
                return '%g' % v
            return '' if v is None else str(v)
        if role == Qt.ItemDataRole.UserRole:          # valeur brute pour le tri
            return v
        st = self.styles[index.row()] if self.styles and index.row() < len(self.styles) else None
        if role == Qt.ItemDataRole.ToolTipRole:
            if st and index.column() in (st.get('bulles') or {}):
                return st['bulles'][index.column()]
            return self.infobulles[index.row()] if self.infobulles else None
        if role == Qt.ItemDataRole.TextAlignmentRole and isinstance(v, (int, float)):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if st:
            if role == Qt.ItemDataRole.ForegroundRole and st.get('couleur') is not None:
                return st['couleur']
            if role == Qt.ItemDataRole.DecorationRole:
                return (st.get('icones') or {}).get(index.column())
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.entetes[section]
        return None


class Proxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSortRole(Qt.ItemDataRole.UserRole)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterKeyColumn(-1)

    def lessThan(self, a, b):
        va, vb = a.data(Qt.ItemDataRole.UserRole), b.data(Qt.ItemDataRole.UserRole)
        try:
            return va < vb
        except TypeError:
            return str(va) < str(vb)


def vue_tableau(modele: ModeleTableau, cle_aide: str, selection_multiple=True) -> tuple[QTableView, Proxy]:
    proxy = Proxy()
    proxy.setSourceModel(modele)
    v = QTableView()
    v.setModel(proxy)
    v.setSortingEnabled(True)
    v.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)   # ordre d'origine tant qu'on ne trie pas
    proxy.sort(-1)
    v.setAlternatingRowColors(True)
    v.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    v.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection if selection_multiple
                       else QAbstractItemView.SelectionMode.SingleSelection)
    v.verticalHeader().setVisible(False)
    v.verticalHeader().setDefaultSectionSize(22)
    v.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    v.horizontalHeader().setStretchLastSection(True)
    aide(v, cle_aide)
    return v, proxy


def lignes_choisies(vue: QTableView, proxy: Proxy, modele: ModeleTableau) -> list:
    rangs = {proxy.mapToSource(i).row() for i in vue.selectionModel().selectedRows()}
    return [modele.donnees[r] for r in sorted(rangs)]


class DelegueProgression(QStyledItemDelegate):
    """Dessine une cellule `Progression` : une mini-barre (fraction possédée) sous le texte « n / total »."""

    def __init__(self, parent=None, couleur=None):
        super().__init__(parent)
        self.couleur = couleur                 # fonction () -> QColor, pour suivre le thème

    def paint(self, painter: QPainter, option, index):
        v = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(v, Progression):
            return super().paint(painter, option, index)
        super().paint(painter, option, index)           # fond, sélection, icône et texte comme d'habitude
        r = option.rect
        if r.width() < 24 or r.height() < 10 or v.total <= 0:
            return
        marge = 4
        piste = QRect(r.left() + marge, r.bottom() - 4, r.width() - 2 * marge, 3)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        fond = option.palette.color(option.palette.ColorRole.Mid)
        fond.setAlpha(90)
        painter.fillRect(piste, fond)
        plein = QRect(piste)
        plein.setWidth(max(0, int(round(piste.width() * min(1.0, v.fraction)))))
        if plein.width() > 0:
            c = self.couleur() if self.couleur else option.palette.color(option.palette.ColorRole.Highlight)
            if option.state & QStyle.StateFlag.State_Selected:
                c = option.palette.color(option.palette.ColorRole.HighlightedText)
            painter.fillRect(plein, QColor(c))
        painter.restore()
