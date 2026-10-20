"""Panneau « Animations » : catalogue des 92 animations ClassAction (thème, recherche, état), description, et
l'animation choisie (créée à la demande, une seule animée à la fois)."""
from __future__ import annotations


from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QBrush, QDesktopServices
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSplitter, QStackedWidget, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget)

from ...core.i18n import tr
from ...gui import memoire
from ...gui.adaptatif import Flux
from ...gui.outils import aide, champ, liste
from . import catalogue, formule

# Coupole Web : les mêmes animations dans un navigateur (ordinateur, tablette, téléphone), sans installation.
ADRESSE_WEB = 'https://arp273-rose.github.io/coupole-web/'

ROLE_ID = Qt.ItemDataRole.UserRole


_INDEX_ANIM = None
_DERNIERE = ('', frozenset())


def correspond(entree: catalogue.Entree, texte: str) -> bool:
    """Recherche bilingue (moteur commun avec Coupole Web) sur les animations : noms, descriptions, titres d'origine,
    thèmes, identifiants ; accents, casse, pluriels simples et petites fautes tolérés."""
    global _INDEX_ANIM, _DERNIERE
    q = texte.strip()
    if not q:
        return True
    if _DERNIERE[0] != q:
        if _INDEX_ANIM is None:
            from .classe import contenu
            from .classe.recherche import Index
            _INDEX_ANIM = Index([d for d in contenu.documents() if d['g'] == 'animation'])
        _DERNIERE = (q, frozenset(r['doc']['id'] for r in _INDEX_ANIM.chercher(q)))
    return entree.id in _DERNIERE[1]


def appliquer_reglages(w, reglages: dict, tout: bool = False):
    """Pose des réglages (clé → valeur) sur une animation ; `tout` : les autres reviennent à leur défaut."""
    from PyQt6.QtWidgets import QCheckBox, QComboBox
    from .base import Reglage
    for cle, (wid, defaut) in w._defauts.items():
        if cle not in reglages and not tout:
            continue
        v = reglages.get(cle, defaut)
        try:
            if isinstance(wid, Reglage) and isinstance(v, (int, float)) and not isinstance(v, bool):
                wid.setValue(float(v))
            elif isinstance(wid, QCheckBox) and isinstance(v, bool):
                wid.setChecked(v)
            elif isinstance(wid, QComboBox):
                k = wid.findData(v)
                if k >= 0:
                    wid.setCurrentIndex(k)
        except (TypeError, ValueError):
            continue


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
        self.l_desc.setOpenExternalLinks(True)          # lien croisé (Anticythere3D)
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
        tete = QHBoxLayout()
        tete.setContentsMargins(0, 0, 0, 0)
        tete.addWidget(self.l_titre, 1)
        from .classe.favoris_qt import BoutonFavori
        self.b_favori = BoutonFavori('animation', '', '', self)
        self.b_favori.setVisible(False)
        tete.addWidget(self.b_favori, 0, Qt.AlignmentFlag.AlignTop)
        self.b_web = QPushButton(tr('anim_version_web'))
        aide(self.b_web, 'anim_version_web_aide')
        self.b_web.clicked.connect(self.ouvrir_web)
        tete.addWidget(self.b_web, 0, Qt.AlignmentFlag.AlignTop)
        d.addLayout(tete)
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
        # navigation par modules (0.6.0) : pages des modules au-dessus du catalogue des animations
        from .classe.gui import VueClasse
        nav = QHBoxLayout()
        self.b_vues = {}
        for cle, texte in (('modules', 'classe_nav_modules'), ('animations', 'classe_nav_animations'),
                           ('bibliotheque', 'classe_nav_bibliotheque'), ('favoris', 'classe_nav_mes_modules'),
                           ('progression', 'classe_nav_progression')):
            b = QPushButton(tr(texte))
            b.setCheckable(True)
            b.setAutoExclusive(True)
            b.setToolTip(tr(texte))
            b.clicked.connect(lambda _=False, c=cle: self.montrer(c))
            nav.addWidget(b)
            self.b_vues[cle] = b
        nav.addStretch(1)
        v.addLayout(nav)
        self.vues = QStackedWidget()
        self.classe = VueClasse(self)
        self.classe.ouvrir_animation.connect(self.ouvrir)
        self.vues.addWidget(self.classe)
        self.vues.addWidget(sp)
        v.addWidget(self.vues, 1)
        self.montrer('modules')
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
            entrees.sort(key=lambda e: (not e.faite, catalogue.ORDRE.index(e.id) if e.id in catalogue.ORDRE else 99,
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

    def adresse_web(self) -> str:
        """Adresse de l'animation courante dans Coupole Web, avec ses réglages modifiés (lien partageable du site :
        #/a/<id>?clé=valeur&…), ou l'accueil du site."""
        w = self.animations.get(self.courante) if self.courante else None
        if w is None:
            return ADRESSE_WEB
        return ADRESSE_WEB + w.adresse_web()

    def ouvrir_web(self):
        QDesktopServices.openUrl(QUrl(self.adresse_web()))

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
        hors = catalogue.HORS_CLASSACTION.get(e.id)
        if hors:
            # animation hors ClassAction : sa provenance et le lien croisé vers l'application complète
            origine = '%s<br><a href="%s">%s</a> ↗' % (html.escape(tr('anim_%s_adapte' % e.cle)), html.escape(hors[1]),
                                                       html.escape(tr('anim_%s_lien' % e.cle)))
        else:
            origine = html.escape(tr('anim_titre_origine', titre=e.titre))
        h = ('<b>%s</b> — <i>%s</i><br>%s<br><span>%s</span><br><small>%s</small>'
             % (html.escape(tr('anim_nom_' + e.cle)), html.escape(etat), formule.enrichir(tr('anim_desc_' + e.cle)),
                origine, html.escape(tr('anim_theme_de', theme=tr('anim_theme_' + e.theme)))))
        return h + Panneau.a_voir(e.cle)

    @staticmethod
    def a_voir(cle: str) -> str:
        """« Ce qu'il faut voir » et ses encadrés (ex. « Dans l'hémisphère Sud », 0.8.0), quand ils existent."""
        import html
        from ...core import i18n
        cles = i18n.toutes_les_cles()
        h = ''
        if 'anim_%s_a_voir' % cle in cles:
            h += '<p><b>%s</b> — %s</p>' % (html.escape(tr('anim_a_voir_titre')),
                                           formule.enrichir(tr('anim_%s_a_voir' % cle)))
        if 'anim_%s_sud' % cle in cles:
            h += ('<table width="100%%" cellpadding="6" style="border:1px solid #6d8fb8"><tr><td><b>%s</b><br>%s'
                  '</td></tr></table>' % (html.escape(tr('anim_encadre_sud')), formule.enrichir(tr('anim_%s_sud' % cle))))
        return h

    # ------------------------------------------------------------ animation
    def montrer(self, vue: str):
        """Vue du panneau : modules (accueil), bibliothèque, animations (catalogue), Mes favoris (collections au second
        plan), Ma progression."""
        vue = {'mes': 'favoris'}.get(vue, vue)
        if vue == 'animations':
            self.vues.setCurrentIndex(1)
        else:
            self.vues.setCurrentIndex(0)
            {'modules': self.classe.aller_accueil, 'bibliotheque': self.classe.aller_bibliotheque,
             'favoris': self.classe.aller_favoris, 'progression': self.classe.aller_progression}[vue]()
        self.b_vues[vue].setChecked(True)

    def appliquer_sauvegarde(self):
        """Après un import ou une réinitialisation : réglages des animations ouvertes repris de la sauvegarde."""
        from .classe.stockage import stockage
        for ident, w in self.animations.items():
            appliquer_reglages(w, stockage().reglages_animation(ident), tout=True)

    def ouvrir(self, ident: str):
        """Affiche l'animation `ident` (créée au premier affichage) ; arrête celle qu'on quitte."""
        e = catalogue.PAR_ID.get(ident)
        if e is None:
            return None
        if hasattr(self, 'vues') and self.vues.currentIndex() != 1:
            self.vues.setCurrentIndex(1)
            self.b_vues['animations'].setChecked(True)
        if self.courante and self.courante in self.animations and self.courante != ident:
            self.animations[self.courante].arreter()
        self.courante = ident
        self.l_titre.setText(tr('anim_nom_' + e.cle))
        self.b_favori.changer('animation', ident, tr('anim_nom_' + e.cle))
        self.b_favori.setVisible(True)
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
            # sauvegarde commune (format de Coupole Web) : réglages repris, puis gardés à chaque changement
            from .classe.stockage import stockage
            appliquer_reglages(w, stockage().reglages_animation(ident))
            origine = w.reglage_change

            def reglage_change(w=w, origine=origine):
                origine()
                stockage().memoriser_reglages(w.ID, w.etat_reglages())
            w.reglage_change = reglage_change
            self.animations[ident] = w
            self.pile.addWidget(w)
        self.pile.setCurrentWidget(w)
        memoire.memoire().signaler()
        return w

    def arreter(self):
        for w in self.animations.values():
            w.arreter()

    def aide_html(self):
        return tr('classe_aide_html') + tr('anim_aide_html')
