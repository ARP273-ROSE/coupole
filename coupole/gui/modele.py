"""Modèle de tableau générique (rapide sur des milliers de lignes) avec tri et filtre."""
from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableView

from .outils import aide


class ModeleTableau(QAbstractTableModel):
    """lignes : liste de tuples de valeurs affichables ; donnees : objet associé à chaque ligne."""

    def __init__(self, entetes: list[str], parent=None):
        super().__init__(parent)
        self.entetes = entetes
        self.lignes: list[tuple] = []
        self.donnees: list = []
        self.infobulles: list = []

    def remplir(self, lignes, donnees=None, infobulles=None):
        self.beginResetModel()
        self.lignes = list(lignes)
        self.donnees = list(donnees) if donnees is not None else [None] * len(self.lignes)
        self.infobulles = list(infobulles) if infobulles is not None else []
        self.endResetModel()

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
        if role == Qt.ItemDataRole.ToolTipRole and self.infobulles:
            return self.infobulles[index.row()]
        if role == Qt.ItemDataRole.TextAlignmentRole and isinstance(v, (int, float)):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
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
