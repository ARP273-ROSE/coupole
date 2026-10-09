"""Modèle de tableau générique (rapide sur des milliers de lignes) avec tri et filtre."""
from __future__ import annotations

import math

from PyQt6.QtCore import QAbstractItemModel, QAbstractTableModel, QModelIndex, QRect, QSortFilterProxyModel, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (QAbstractItemView, QHeaderView, QStyle, QStyledItemDelegate, QStyleOptionHeader,
                             QTableView)

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


class Nombre:
    """Valeur numérique affichée avec un format choisi (« 2.345 ») mais triée par sa valeur (et non comme texte,
    où « 10.2 » passerait avant « 2.3 »)."""

    __slots__ = ('v', 'texte')

    def __init__(self, v: float, fmt: str = '%.4g'):
        self.v = float(v)
        self.texte = fmt % v

    def __str__(self):
        return self.texte


def cle_de_tri(v):
    """Clé de tri d'une cellule, calculée une fois par ligne (jamais de comparaison Python par paire) :
    nombres et `Progression` d'abord (par valeur), puis textes, puis cellules vides ou NaN."""
    if v is None:
        return (2, 0.0, '')
    if isinstance(v, Progression):
        return (0, v.fraction, v.total)
    if isinstance(v, Nombre):
        return (2, 0.0, '') if math.isnan(v.v) else (0, v.v, 0)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        f = float(v)
        return (2, 0.0, '') if math.isnan(f) else (0, f, 0)
    return (1, 0.0, v if isinstance(v, str) else str(v))


def permutation_triee(cles: list, decroissant: bool = False) -> list[int]:
    """Indices qui trient `cles` — exactement l'ordre de ``sorted(range(n), key=cles.__getitem__,
    reverse=decroissant)`` (tri stable : à clé égale, l'ordre courant est gardé, y compris en décroissant).

    Clés entières (rangs précalculés : heure du site, drapeaux, possession) ou réelles sans NaN (date) :
    `numpy.argsort` stable, quelques millisecondes pour 80 000 lignes ; autres clés : le tri de Python."""
    n = len(cles)
    if n > 1000:
        import numpy as np
        a = None
        if all(type(c) is int for c in cles):
            try:
                a = np.fromiter(cles, dtype=np.int64, count=n)
            except OverflowError:                      # entier hors de 64 bits : tri de Python
                a = None
            if a is not None and a.min() == np.iinfo(np.int64).min:
                a = None                               # (son opposé déborderait)
        elif all(type(c) is float for c in cles):
            a = np.fromiter(cles, dtype=np.float64, count=n)
            if np.isnan(a).any():                      # NaN : l'ordre de Python n'est pas celui de numpy
                a = None
        if a is not None:
            return np.argsort(-a if decroissant else a, kind='stable').tolist()
    return sorted(range(n), key=cles.__getitem__, reverse=decroissant)


class ModeleTableau(QAbstractTableModel):
    """lignes : liste de tuples de valeurs affichables ; donnees : objet associé à chaque ligne.

    styles (facultatif) : un dict par ligne — ``couleur`` (QColor du texte de toute la ligne), ``icones``
    ({colonne: QIcon}), ``bulles`` ({colonne: info-bulle propre à la cellule, prioritaire sur celle de la ligne}).

    Le tri se fait ICI, dans le modèle source (`sort`), par une clé calculée une fois par ligne et le tri de
    Python (C) : 80 000 lignes en quelques dizaines de millisecondes.  Le `Proxy` ne trie plus lui-même (son
    `lessThan` Python était appelé n·log n fois : 4 s pour 80 000 lignes) ; il ne sert plus qu'au filtrage et
    reste transparent.  Le tri choisi est conservé : `remplir` et `ajouter` rendent des lignes déjà triées.
    """

    def __init__(self, entetes: list[str], parent=None):
        super().__init__(parent)
        self.entetes = entetes
        self.lignes: list[tuple] = []
        self.donnees: list = []
        self.infobulles: list = []
        self.styles: list = []
        self._rang: list[int] = []            # ordre d'arrivée : rétabli par un tri sur la colonne -1
        self._tri: tuple | None = None        # (colonne, ordre) en vigueur, None = ordre d'arrivée
        self._suivant = 0

    # ---------------------------------------------------------------- tri
    def _permutation(self) -> list[int]:
        n = len(self.lignes)
        if self._tri is None:
            return sorted(range(n), key=self._rang.__getitem__)
        col, ordre = self._tri
        cles = [cle_de_tri(l[col]) if col < len(l) else (2, 0.0, '') for l in self.lignes]
        perm = sorted(range(n), key=cles.__getitem__, reverse=(ordre == Qt.SortOrder.DescendingOrder))
        return perm

    def _reordonner(self, perm: list[int]):
        n = len(perm)
        self.lignes = [self.lignes[i] for i in perm]
        self._rang = [self._rang[i] for i in perm]
        if len(self.donnees) == n:
            self.donnees = [self.donnees[i] for i in perm]
        if len(self.infobulles) == n:
            self.infobulles = [self.infobulles[i] for i in perm]
        if len(self.styles) == n:
            self.styles = [self.styles[i] for i in perm]

    def sort(self, colonne, ordre=Qt.SortOrder.AscendingOrder):
        self._tri = None if colonne is None or colonne < 0 else (int(colonne), ordre)
        self._trier_en_place()

    def _trier_en_place(self):
        if len(self.lignes) < 2:
            return
        perm = self._permutation()
        if all(i == k for k, i in enumerate(perm)):
            return
        hint = QAbstractItemModel.LayoutChangeHint.VerticalSortHint
        self.layoutAboutToBeChanged.emit([], hint)
        nouveau = [0] * len(perm)
        for k, i in enumerate(perm):
            nouveau[i] = k
        anciens = self.persistentIndexList()
        self._reordonner(perm)
        if anciens:
            self.changePersistentIndexList(anciens, [self.index(nouveau[i.row()], i.column()) if i.isValid()
                                                     and i.row() < len(nouveau) else QModelIndex()
                                                     for i in anciens])
        self.layoutChanged.emit([], hint)

    # ---------------------------------------------------------------- contenu
    def remplir(self, lignes, donnees=None, infobulles=None, styles=None):
        self.beginResetModel()
        self.lignes = list(lignes)
        self.donnees = list(donnees) if donnees is not None else [None] * len(self.lignes)
        self.infobulles = list(infobulles) if infobulles is not None else []
        self.styles = list(styles) if styles is not None else []
        self._rang = list(range(len(self.lignes)))
        self._suivant = len(self.lignes)
        if self._tri is not None and len(self.lignes) > 1:
            self._reordonner(self._permutation())        # déjà trié : la vue n'a rien à refaire
        self.endResetModel()

    def remplacer_lignes(self, lignes, styles=None):
        """Nouvelles valeurs pour les MÊMES lignes (dans l'ordre courant) : pas de reconstruction, la sélection
        reste ; re-trié si le tri porte sur une valeur qui a pu changer."""
        self.lignes = list(lignes)
        if styles is not None:
            self.styles = list(styles)
        if self.lignes:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.lignes) - 1, len(self.entetes) - 1))
        if self._tri is not None:
            self._trier_en_place()

    def restyler(self, styles):
        """Change seulement les styles (couleurs, icônes) : la vue redessine sans perdre sélection ni tri."""
        self.styles = list(styles) if styles is not None else []
        if self.lignes:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.lignes) - 1, len(self.entetes) - 1))

    def ajouter(self, lignes, donnees=None, infobulles=None):
        """Ajoute des lignes sans reconstruire le modèle (beginInsertRows) : la vue ne redessine que l'ajout
        (puis un seul re-tri, par clés, si un tri est en vigueur)."""
        lignes = list(lignes)
        if not lignes:
            return
        debut = len(self.lignes)
        self.beginInsertRows(QModelIndex(), debut, debut + len(lignes) - 1)
        self.lignes.extend(lignes)
        self._rang.extend(range(self._suivant, self._suivant + len(lignes)))
        self._suivant += len(lignes)
        self.donnees.extend(list(donnees) if donnees is not None else [None] * len(lignes))
        if self.infobulles or infobulles:
            self.infobulles.extend(list(infobulles) if infobulles is not None else [''] * len(lignes))
        if self.styles:
            self.styles.extend([{}] * len(lignes))
        self.endInsertRows()
        if self._tri is not None:
            self._trier_en_place()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.lignes)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.entetes)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        v = self._ligne(index.row())[index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(v, float):
                return '%g' % v
            return '' if v is None else str(v)
        if role == Qt.ItemDataRole.UserRole:          # valeur brute pour le tri
            return v
        st = self._style(index.row())
        if role == Qt.ItemDataRole.ToolTipRole:
            if st and index.column() in (st.get('bulles') or {}):
                b = st['bulles'][index.column()]
                return b() if callable(b) else b      # info-bulle composée au survol seulement
            return self._bulle(index.row())
        if role == Qt.ItemDataRole.TextAlignmentRole and isinstance(v, (int, float, Nombre)):
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

    # accès par ligne (redéfinis par ModeleParesseux)
    def _ligne(self, r):
        return self.lignes[r]

    def _style(self, r):
        return self.styles[r] if self.styles and r < len(self.styles) else None

    def _bulle(self, r):
        return self.infobulles[r] if self.infobulles else None


class ModeleParesseux(ModeleTableau):
    """Table de milliers à centaines de milliers de lignes dont les cellules ne sont calculées qu'à l'affichage.

    `remplir_objets(donnees)` ne construit AUCUNE ligne : la vue ne demande que les ~40 lignes visibles, et
    `ligne(x)` / `style(x)` / `bulle(x)` (fonctions fournies) sont appelées pour elles seulement, puis gardées en
    cache.  Le tri passe par `cle(x, colonne)` quand une clé rapide est fournie (sinon la valeur de la cellule).
    Changer les couleurs ou la possession = vider un cache (`invalider`), pas reconstruire 80 000 lignes.
    """

    def __init__(self, entetes, ligne, style=None, bulle=None, cle=None, parent=None):
        super().__init__(entetes, parent)
        self._f_ligne, self._f_style, self._f_bulle, self._f_cle = ligne, style, bulle, cle
        self._c_lignes: dict = {}
        self._c_styles: dict = {}
        self._version = 0                 # change à chaque remplissage ou invalidation des cellules
        self._version_triee = -1          # version déjà triée selon self._tri

    def sort(self, colonne, ordre=Qt.SortOrder.AscendingOrder):
        """Comme `ModeleTableau.sort`, sans refaire un tri déjà fait : `QTableView.sortByColumn` demande deux fois
        le même tri (indicateur de l'en-tête, puis appel direct) — 80 000 clés recalculées pour rien."""
        tri = None if colonne is None or colonne < 0 else (int(colonne), ordre)
        if tri == self._tri and self._version_triee == self._version:
            return
        super().sort(colonne, ordre)
        self._version_triee = self._version

    # -- vue « liste de lignes » pour le code qui lit modele.lignes (rare : export, tests)
    class _Lignes:
        def __init__(self, m):
            self.m = m

        def __len__(self):
            return len(self.m.donnees)

        def __getitem__(self, r):
            if isinstance(r, slice):
                return [self.m._ligne(k) for k in range(*r.indices(len(self)))]
            return self.m._ligne(r)

        def __iter__(self):
            return (self.m._ligne(k) for k in range(len(self)))

        def __bool__(self):
            return bool(self.m.donnees)

    @property
    def lignes(self):
        return ModeleParesseux._Lignes(self)

    @lignes.setter
    def lignes(self, valeur):                       # affectations de la classe de base : sans objet ici
        pass

    def _ligne(self, r):
        x = self.donnees[r]
        k = id(x)
        v = self._c_lignes.get(k)
        if v is None:
            v = self._c_lignes[k] = tuple(self._f_ligne(x))
        return v

    def _style(self, r):
        if self._f_style is None:
            return None
        x = self.donnees[r]
        k = id(x)
        v = self._c_styles.get(k)
        if v is None:
            v = self._c_styles[k] = self._f_style(x) or {}
        return v

    def _bulle(self, r):
        return self._f_bulle(self.donnees[r]) if self._f_bulle else None

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.donnees)

    def _permutation(self):
        n = len(self.donnees)
        if self._tri is None:
            return sorted(range(n), key=self._rang.__getitem__)
        col, ordre = self._tri
        cle = None if self._f_cle is None else self._f_cle(col)
        if cle is not None:
            cles = [cle(x) for x in self.donnees]
        else:
            cles = [cle_de_tri(self._ligne(r)[col]) for r in range(n)]
        return permutation_triee(cles, ordre == Qt.SortOrder.DescendingOrder)

    def _reordonner(self, perm):
        self.donnees = [self.donnees[i] for i in perm]
        self._rang = [self._rang[i] for i in perm]

    def _trier_en_place(self):
        if len(self.donnees) >= 2:
            super()._trier_en_place()

    def remplir_objets(self, donnees):
        self.beginResetModel()
        self.donnees = list(donnees)
        self._rang = list(range(len(self.donnees)))
        self._suivant = len(self.donnees)
        if len(self._c_lignes) > 4 * max(1000, len(self.donnees)):   # cache borné (anciens remplissages)
            self._c_lignes.clear()
            self._c_styles.clear()
        if self._tri is not None and len(self.donnees) > 1:
            self._reordonner(self._permutation())
        self._version += 1
        self._version_triee = self._version
        self.endResetModel()

    def invalider(self, lignes=True, styles=True):
        """Possession, thème ou langue changés : cellules recalculées au prochain affichage, sans reconstruction ;
        re-trié si nécessaire ; sélection et défilement conservés."""
        if lignes:
            self._c_lignes.clear()
            self._version += 1
        if styles:
            self._c_styles.clear()
        if self.donnees:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.donnees) - 1, len(self.entetes) - 1))
        if self._tri is not None and lignes:
            self._trier_en_place()
        if lignes:
            self._version_triee = self._version

    def remplir(self, lignes, donnees=None, infobulles=None, styles=None):
        raise TypeError('ModeleParesseux : remplir_objets(donnees)')


class Proxy(QSortFilterProxyModel):
    """Filtre seulement : le tri est délégué au modèle source (`ModeleTableau.sort`, clés calculées une fois)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSortRole(Qt.ItemDataRole.UserRole)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterKeyColumn(-1)

    def sort(self, colonne, ordre=Qt.SortOrder.AscendingOrder):
        src = self.sourceModel()
        if isinstance(src, ModeleTableau):
            if self.sortColumn() != -1:
                super().sort(-1)                      # le proxy garde l'ordre de la source
            src.sort(colonne, ordre)
        else:
            super().sort(colonne, ordre)

    def lessThan(self, a, b):
        va, vb = a.data(Qt.ItemDataRole.UserRole), b.data(Qt.ItemDataRole.UserRole)
        try:
            return va < vb
        except TypeError:
            return str(va) < str(vb)


PRECISION_COLONNES = 120


class ProxyFiltre(Proxy):
    """Proxy qui n'affiche que les lignes dont l'objet (modele.donnees) est dans un ensemble : un filtre calculé
    une fois en Python, appliqué en une passe, et qui suit les re-tris du modèle (identité de l'objet, pas
    numéro de ligne)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._visibles = None

    def definir_visibles(self, ids):
        if ids is None and self._visibles is None:
            return
        self._visibles = ids
        self.invalidateRowsFilter() if hasattr(self, 'invalidateRowsFilter') else self.invalidateFilter()

    def filterAcceptsRow(self, ligne, parent):
        if self._visibles is None:
            return True
        m = self.sourceModel()
        return 0 <= ligne < len(m.donnees) and id(m.donnees[ligne]) in self._visibles


class EnTete(QHeaderView):
    """En-tête de colonnes dessiné sans interroger la sélection.

    `QHeaderView` (Qt 6) calcule pour chaque section dessinée si la colonne voisine est « entièrement
    sélectionnée » (`QItemSelectionModel::isColumnSelected`), ce qui parcourt TOUTES les lignes du modèle — et
    chaque ligne coûte deux appels Python (rowCount/columnCount) : après « tout sélectionner » sur 80 000 lignes,
    chaque dessin de l'en-tête (défilement, survol) prenait 0,7 s.  Ici la section est dessinée par le style avec
    les mêmes options, sans cette information purement décorative (rendu identique au pixel près, vérifié).
    """

    def paintSection(self, painter, rect, logique):
        if not rect.isValid():
            return
        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.rect = rect
        opt.section = logique
        etat = opt.state
        if self.isEnabled():
            etat |= QStyle.StateFlag.State_Enabled
        if self.window().isActiveWindow():
            etat |= QStyle.StateFlag.State_Active
        opt.state = etat | QStyle.StateFlag.State_Raised
        m = self.model()
        texte = m.headerData(logique, self.orientation(), Qt.ItemDataRole.DisplayRole) if m is not None else None
        opt.text = '' if texte is None else str(texte)
        opt.textAlignment = self.defaultAlignment()
        opt.iconAlignment = Qt.AlignmentFlag.AlignVCenter
        if self.isSortIndicatorShown() and self.sortIndicatorSection() == logique:
            opt.sortIndicator = (QStyleOptionHeader.SortIndicator.SortDown
                                 if self.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder
                                 else QStyleOptionHeader.SortIndicator.SortUp)
        visuel, n = self.visualIndex(logique), self.count()
        P = QStyleOptionHeader.SectionPosition
        opt.position = (P.OnlyOneSection if n == 1 else P.Beginning if visuel == 0 else P.End if visuel == n - 1
                        else P.Middle)
        opt.orientation = self.orientation()
        self.style().drawControl(QStyle.ControlElement.CE_Header, opt, painter, self)


def vue_tableau(modele: ModeleTableau, cle_aide: str, selection_multiple=True,
                filtrable=False) -> tuple[QTableView, Proxy]:
    proxy = ProxyFiltre() if filtrable else Proxy()
    proxy.setSourceModel(modele)
    v = QTableView()
    entete = EnTete(Qt.Orientation.Horizontal, v)
    entete.setSectionsClickable(True)                          # (réglage par défaut de l'en-tête de QTableView)
    v.setHorizontalHeader(entete)
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
    # « ajuster les colonnes au contenu » mesure au plus 120 lignes (et non 1000 : 9 colonnes × 1000 lignes ×
    # plusieurs rôles = des dizaines de milliers d'appels Python par ajustement)
    v.horizontalHeader().setResizeContentsPrecision(PRECISION_COLONNES)
    v.horizontalHeader().setHighlightSections(False)        # (voir EnTete : la sélection n'est pas consultée)
    v.verticalHeader().setResizeContentsPrecision(PRECISION_COLONNES)
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
