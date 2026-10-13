"""Panneau « Animations » : catalogue des 92 animations ClassAction (thème, recherche, état), description, et
l'animation choisie (créée à la demande, une seule animée à la fois)."""
from __future__ import annotations

import unicodedata

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush
from PyQt6.QtWidgets import (QLabel, QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from ...core.i18n import tr
from ...gui import memoire
from ...gui.adaptatif import Flux
from ...gui.outils import aide, champ, liste
from . import catalogue

ROLE_ID = Qt.ItemDataRole.UserRole


def _sans_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


def correspond(entree: catalogue.Entree, texte: str) -> bool:
    """Recherche insensible à la casse et aux accents, dans les deux langues et dans le titre d'origine."""
    if not texte.strip():
        return True
    from ...core import i18n
    cles = ('anim_nom_' + entree.cle, 'anim_desc_' + entree.cle)
    foin = ' '.join([entree.id, entree.titre] + [i18n.toutes_les_cles().get(k, {}).get(lg, '')
                                                   for k in cles for lg in ('fr', 'en')])
    foin = _sans_accents(foin)
    return all(m in foin for m in _sans_accents(texte).split())


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.courante = None
        self.animations = {}                       # id → widget de l'animation (créé à la demande)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        sp = QSplitter(Qt.Orientation.Horizontal)
        self.splitter = sp
        # ---------------------------------------------------------------- catalogue
        gauche = QWidget()
        g = QVBoxLayout(gauche)
        g.setContentsMargins(0, 0, 4, 0)
        self.recherche = champ('anim_recherche_aide', '', 'anim_recherche_indice')
        g.addWidget(self.recherche)
        f = Flux()
        self.theme = liste('anim_theme_aide', [(tr('anim_theme_tous'), '')] +
                           [(tr('anim_theme_' + t), t) for t in catalogue.THEMES])
        self.etat = liste('anim_etat_aide', [(tr('anim_etat_toutes'), 'toutes'), (tr('anim_etat_faites'), 'faites'),
                                             (tr('anim_etat_a_venir'), 'a_venir')])
        f.addWidget(self.theme)
        f.addWidget(self.etat)
        g.addLayout(f)
        self.l_compte = QLabel(tr('anim_compte', faites=len(catalogue.faites()), total=len(catalogue.ENTREES)))
        self.l_compte.setWordWrap(True)
        g.addWidget(self.l_compte)
        self.arbre = aide(QTreeWidget(), 'anim_liste_aide')
        self.arbre.setHeaderHidden(True)
        self.arbre.setMinimumWidth(200)
        self.arbre.setRootIsDecorated(True)
        self.arbre.setUniformRowHeights(True)
        g.addWidget(self.arbre, 1)
        self.l_desc = QLabel('')
        self.l_desc.setWordWrap(True)
        self.l_desc.setTextFormat(Qt.TextFormat.RichText)
        self.l_desc.setMinimumHeight(self.l_desc.fontMetrics().height() * 4)
        g.addWidget(self.l_desc)
        sp.addWidget(gauche)
        # ---------------------------------------------------------------- animation
        droite = QWidget()
        d = QVBoxLayout(droite)
        d.setContentsMargins(4, 0, 0, 0)
        self.l_titre = QLabel(tr('anim_choisir'))
        self.l_titre.setWordWrap(True)
        f2 = self.l_titre.font()
        f2.setPointSizeF(f2.pointSizeF() * 1.2)
        f2.setBold(True)
        self.l_titre.setFont(f2)
        d.addWidget(self.l_titre)
        self.pile = QStackedWidget()
        self.vide = QLabel(tr('anim_choisir'))
        self.vide.setWordWrap(True)
        self.vide.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pile.addWidget(self.vide)
        d.addWidget(self.pile, 1)
        self.l_credits = QLabel(tr('anim_credits'))
        self.l_credits.setWordWrap(True)
        d.addWidget(self.l_credits)
        sp.addWidget(droite)
        sp.setStretchFactor(0, 1)
        sp.setStretchFactor(1, 4)
        sp.setSizes([280, 1000])
        sp.setChildrenCollapsible(False)
        v.addWidget(sp, 1)
        self._remplir()
        self._memoriser()
        self.recherche.textChanged.connect(lambda *_: self._remplir())
        self.theme.currentIndexChanged.connect(lambda *_: self._remplir())
        self.etat.currentIndexChanged.connect(lambda *_: self._remplir())
        self.arbre.currentItemChanged.connect(self._selection)
        self.arbre.itemActivated.connect(lambda it, *_: self._ouvrir_element(it))
        self.arbre.itemDoubleClicked.connect(lambda it, *_: self._ouvrir_element(it))

    # ------------------------------------------------------------ mémoire de l'interface
    def _memoriser(self):
        from ...core.etat_interface import etat
        k = 'modules.anim.'
        memoire.champ(self.recherche, k + 'recherche')
        memoire.liste(self.theme, k + 'theme')
        memoire.liste(self.etat, k + 'etat')
        memoire.separateur(self.splitter, k + 'separateur')
        self._remplir()
        ident = etat().lire(k + 'courante', '', str)
        if ident in catalogue.PAR_ID and catalogue.PAR_ID[ident].faite:
            self.ouvrir(ident)
        memoire.memoire().suivre(k + 'courante', lambda: self.courante, self)

    # ------------------------------------------------------------ catalogue
    def _remplir(self):
        th, et, texte = self.theme.currentData(), self.etat.currentData(), self.recherche.text()
        self.arbre.blockSignals(True)
        self.arbre.clear()
        doux = QBrush(self.palette().placeholderText().color())
        choisi = None
        for t in catalogue.THEMES:
            if th and t != th:
                continue
            entrees = [e for e in catalogue.ENTREES if e.theme == t and correspond(e, texte) and
                       (et == 'toutes' or (et == 'faites') == e.faite)]
            if not entrees:
                continue
            racine = QTreeWidgetItem([tr('anim_theme_' + t) + ' (%d/%d)' % (sum(e.faite for e in entrees),
                                                                           len(entrees))])
            racine.setFlags(Qt.ItemFlag.ItemIsEnabled)
            f = racine.font(0)
            f.setBold(True)
            racine.setFont(0, f)
            self.arbre.addTopLevelItem(racine)
            # disponibles d'abord (dans l'ordre du lot), puis à venir par ordre alphabétique
            entrees.sort(key=lambda e: (not e.faite, catalogue.LOT1.index(e.id) if e.id in catalogue.LOT1 else 99,
                                        tr('anim_nom_' + e.cle).lower()))
            for e in entrees:
                it = QTreeWidgetItem([tr('anim_nom_' + e.cle) + ('' if e.faite else ' — ' + tr('anim_a_venir'))])
                it.setData(0, ROLE_ID, e.id)
                it.setToolTip(0, tr('anim_desc_' + e.cle))
                if not e.faite:
                    it.setForeground(0, doux)
                racine.addChild(it)
                if e.id == self.courante:
                    choisi = it
            racine.setExpanded(True)
        self.arbre.blockSignals(False)
        if choisi is not None:
            self.arbre.setCurrentItem(choisi)

    def _selection(self, it, *_):
        if it is None or it.data(0, ROLE_ID) is None:
            return
        e = catalogue.PAR_ID[it.data(0, ROLE_ID)]
        self.l_desc.setText(self.description(e))
        if e.faite:
            self.ouvrir(e.id)

    def _ouvrir_element(self, it):
        if it is not None and it.data(0, ROLE_ID):
            self.ouvrir(it.data(0, ROLE_ID))

    @staticmethod
    def description(e: catalogue.Entree) -> str:
        import html
        etat = tr('anim_disponible' if e.faite else 'anim_a_venir')
        return ('<b>%s</b> — <i>%s</i><br>%s<br><span>%s</span><br><small>%s</small>'
                % (html.escape(tr('anim_nom_' + e.cle)), html.escape(etat), html.escape(tr('anim_desc_' + e.cle)),
                   html.escape(tr('anim_titre_origine', titre=e.titre)),
                   html.escape(tr('anim_theme_de', theme=tr('anim_theme_' + e.theme)))))

    # ------------------------------------------------------------ animation
    def ouvrir(self, ident: str):
        """Affiche l'animation `ident` (créée au premier affichage) ; arrête celle qu'on quitte."""
        e = catalogue.PAR_ID.get(ident)
        if e is None:
            return None
        if self.courante and self.courante in self.animations and self.courante != ident:
            self.animations[self.courante].arreter()
        self.courante = ident
        self.l_titre.setText(tr('anim_nom_' + e.cle))
        self.l_desc.setText(self.description(e))
        if not e.faite:
            self.vide.setText(tr('anim_pas_encore'))
            self.pile.setCurrentWidget(self.vide)
            return None
        w = self.animations.get(ident)
        if w is None:
            try:
                w = e.charger()(self)
            except Exception as err:                       # une animation défectueuse ne bloque pas le module
                import logging
                logging.getLogger(__name__).exception('animation %s', ident)
                self.vide.setText(tr('anim_erreur', erreur=str(err)))
                self.pile.setCurrentWidget(self.vide)
                return None
            from ...gui import adaptatif
            adaptatif.assouplir(w)
            self.animations[ident] = w
            self.pile.addWidget(w)
        self.pile.setCurrentWidget(w)
        memoire.memoire().signaler()
        return w

    def arreter(self):
        for w in self.animations.values():
            w.arreter()

    def aide_html(self):
        return tr('anim_aide_html')
