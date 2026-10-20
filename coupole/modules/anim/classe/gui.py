"""Navigation par modules au bureau (même organisation que Coupole Web) : accueil (22 modules, bonus, favoris,
bibliothèque, reprise), page d'un module à onglets (Questions, Animations, Fiches, Tables, Images ; Organiser pour une
collection), question (menus « Adapter la question », choix, Valider, Montrer la réponse qui clignote, indice,
explication, ressources liées ★, précédente / suivante W → G → C → D en boucle, plein écran), recherche bilingue
(moteur commun avec Coupole Web : recherche.py), « Mes favoris » (étoile sur tout atelier ; collections au second
plan), bibliothèque (présentation d'origine de ClassAction : tout le contenu d'un type, par module), « Ma progression »
(sauvegarde : export, import, réinitialisation tout ou partie avec copie et annulation).  Fil d'Ariane en haut ;
ressources ouvertes dans des fenêtres séparées ; aperçu au survol."""
from __future__ import annotations

import html as _html
import random

from PyQt6.QtCore import QPoint, QRect, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QTextBrowser,
                             QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QCheckBox, QProgressBar, QAbstractButton, QAbstractSpinBox,
                             QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QTabWidget, QTableWidget,
                             QTableWidgetItem, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
                             QInputDialog, QLayout, QHeaderView)

from ....core.i18n import langue, tr
from .. import catalogue
from . import contenu
from . import sauvegarde as S
from .favoris_qt import BoutonFavori, action_favori, basculer as basculer_favori, est_favori, icone_etoile
from .figure_qt import FigureWidget
from .recherche import extrait, surligner
from .moteur_questions import instancier, variantes
from .ressources_qt import apercu, etiquette, ouvrir_ressource, texte_html, theme_courant, Repliable
from .stockage import stockage

bi = contenu.bi
ROLE = Qt.ItemDataRole.UserRole
ROLE_TITRE = Qt.ItemDataRole.UserRole.value + 1          # titre seul (favoris, menus)
TYPES = ('W', 'G', 'C', 'D')
SYMBOLES = {'jamais': '○', 'vue': '◐', 'reussie': '✓', 'ratee': '✗'}


def _titre(texte: str, facteur=1.35) -> QLabel:
    lab = QLabel(texte)
    lab.setWordWrap(True)
    f = lab.font()
    f.setPointSizeF(f.pointSizeF() * facteur)
    f.setBold(True)
    lab.setFont(f)
    lab.setAccessibleName(texte)
    return lab


def _vider(lay):
    while lay.count():
        it = lay.takeAt(0)
        w = it.widget()
        if w is not None:
            w.deleteLater()
        elif it.layout() is not None:
            _vider(it.layout())


def questions_de(cle: str, perso: dict | None) -> list:
    """[{id, n, ok, titre, module}] : questions d'un module (numéros W/G/C/D), ou d'un module personnel (numérotées par
    catégorie dans leur ordre d'ajout)."""
    if not perso:
        m = contenu.module(cle) or {'questions': []}
        return [{'id': q['id'], 'n': q['n'], 'ok': q['ok'], 'titre': bi(q['t']) if q['t'] else q['id'], 'module': cle}
                for q in m['questions']]
    info = contenu.info_questions()
    rang = dict.fromkeys(TYPES, 0)
    out = []
    for e in perso['elements']:
        if e['genre'] != 'question' or e['id'] not in info:
            continue
        i = info[e['id']]
        t = i['n'][0]
        rang[t] += 1
        out.append({'id': e['id'], 'n': t + str(rang[t]), 'ok': i['ok'], 'titre': bi(i['t']) if i['t'] else e['id'],
                    'module': i['module']})
    return out


def ordre(qs: list) -> list:
    """Ordre de passage : W → G → C → D (en boucle)."""
    return [q for t in TYPES for q in sorted((q for q in qs if q['n'].startswith(t) and q['ok']), key=lambda q: int(q['n'][1:]))]


# ------------------------------------------------------------------ « Ajouter à… »
def menu_ajouter(parent, genre: str, i: str, titre: str, apres=None, annoncer=None) -> QMenu:
    s = stockage().doc
    m = QMenu(tr('classe_ajouter_a'), parent)
    m.addAction(action_favori(m, genre, i, titre, annoncer))
    m.addSeparator()
    for mm in s['mes_modules']:
        dedans = any(e['genre'] == genre and e['id'] == i for e in mm['elements'])
        a = QAction(mm['nom'], m)
        a.setCheckable(True)
        a.setChecked(dedans)

        def basculer(_=False, mm=mm, dedans=dedans):
            (S.retirer_element if dedans else S.ajouter_element)(s, mm['id'], {'genre': genre, 'id': i})
            stockage().modifie()
            if apres:
                apres()
        a.triggered.connect(basculer)
        m.addAction(a)
    m.addSeparator()
    nv = QAction(tr('classe_nouveau_module_avec'), m)

    def nouveau():
        S.creer_module(s, S.nom_libre(s, tr('classe_nouveau_module'), True), [{'genre': genre, 'id': i}])
        stockage().modifie()
        if apres:
            apres()
    nv.triggered.connect(nouveau)
    m.addAction(nv)
    return m


class ListeRessources(QListWidget):
    """Liste de ressources : double-clic ou Entrée ouvre, survol = aperçu, menu contextuel « Ajouter à… »/« Retirer »."""
    ouvrir = pyqtSignal(str, str)

    def __init__(self, parent=None, retirer=None):
        super().__init__(parent)
        self.retirer = retirer
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self.itemActivated.connect(lambda it: self.ouvrir.emit(*it.data(ROLE)))
        self.itemEntered.connect(lambda it: it.data(ROLE) and apercu().programmer(*it.data(ROLE), self.viewport().mapToGlobal(
            self.visualItemRect(it).bottomLeft())))
        # favoris : étoile dorée devant les éléments marqués, Ctrl+D bascule l'élément courant
        QShortcut(QKeySequence('Ctrl+D'), self, self._basculer_courant)
        stockage().abonner_faible(self.maj_favoris)

    def _basculer_courant(self):
        it = self.currentItem()
        if it is not None and it.data(ROLE):
            g, i = it.data(ROLE)
            basculer_favori(g, i, it.data(ROLE_TITRE) or it.text())

    def maj_favoris(self):
        try:
            for k in range(self.count()):
                it = self.item(k)
                if it.data(ROLE):
                    it.setIcon(icone_etoile(True) if est_favori(*it.data(ROLE)) else QIcon())
        except RuntimeError:
            pass

    def leaveEvent(self, ev):
        apercu().cacher()
        super().leaveEvent(ev)

    def ajouter(self, genre: str, i: str, texte: str, etoile=False, sous=''):
        it = QListWidgetItem(('★ ' if etoile else '') + texte + ('  —  ' + sous if sous else ''))
        it.setData(ROLE, (genre, i))
        it.setData(ROLE_TITRE, texte)
        it.setToolTip(tr('classe_ouvrir_aide'))
        if est_favori(genre, i):
            it.setIcon(icone_etoile(True))
        self.addItem(it)
        return it

    def _menu(self, pos):
        it = self.itemAt(pos)
        if it is None:
            return
        genre, i = it.data(ROLE)
        if self.retirer:
            m = QMenu(self)
            m.addAction(action_favori(m, genre, i, it.data(ROLE_TITRE) or it.text()))
            a = m.addAction(tr('classe_retirer'))
            a.triggered.connect(lambda: self.retirer(genre, i))
        else:
            m = menu_ajouter(self, genre, i, it.data(ROLE_TITRE) or it.text())
        m.exec(self.viewport().mapToGlobal(pos))


# ================================================================== pages
class GrilleCartes(QLayout):
    """Grille de cartes de même largeur : autant de colonnes que la largeur en permet (largeur minimale `lmin`),
    toutes les cartes d'une rangée à la même hauteur ; hauteur dépendante de la largeur (défilement vertical)."""

    def __init__(self, parent=None, lmin=250, espace=8):
        super().__init__(parent)
        self.items, self.lmin, self.espace = [], lmin, espace
        self._hauteurs = {}
        self.setContentsMargins(0, 0, 0, 0)

    def invalidate(self):
        self._hauteurs = {}
        super().invalidate()

    def addItem(self, it):
        self.items.append(it)

    def count(self):
        return len(self.items)

    def itemAt(self, i):
        return self.items[i] if 0 <= i < len(self.items) else None

    def takeAt(self, i):
        return self.items.pop(i) if 0 <= i < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        h = self._hauteurs.get(w)
        if h is None:
            h = self._hauteurs[w] = self._placer(QRect(0, 0, w, 0), False)
        return h

    def setGeometry(self, r):
        super().setGeometry(r)
        self._placer(r, True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        from PyQt6.QtCore import QSize
        return QSize(min(self.lmin, 200), max((it.minimumSize().height() for it in self.items), default=0))

    def colonnes(self, w):
        return max(1, (w + self.espace) // (self.lmin + self.espace))

    def _placer(self, r, poser):
        if not self.items:
            return 0
        n = min(self.colonnes(r.width()), len(self.items))
        lc = (r.width() - (n - 1) * self.espace) / n
        y = r.y()
        for k in range(0, len(self.items), n):
            rang = self.items[k:k + n]
            h = max(it.widget().heightForWidth(int(lc)) if it.widget() and it.widget().hasHeightForWidth()
                    else it.sizeHint().height() for it in rang)
            if poser:
                for j, it in enumerate(rang):
                    x = r.x() + j * (lc + self.espace)
                    it.setGeometry(QRect(int(round(x)), y, int(round(x + lc)) - int(round(x)), h))
            y += h + self.espace
        return y - self.espace - r.y()


class Carte(QAbstractButton):
    """Carte d'un module, dessinée d'un seul tenant (un widget au lieu de cinq : la page d'accueil reste légère et un
    changement de thème n'a rien à repolir) : numéro, titre en gras, contenu (comptes sans les zéros, au singulier ou
    au pluriel), barre de progression fine.  Couleurs du thème lues au dessin ; survol, focus clavier, accessible."""

    MARGE_X, MARGE_Y = 12, 9

    def __init__(self, titre: str, details: str = '', n=None, progres=None, parent=None):
        super().__init__(parent)
        self.titre, self.details, self.n, self.progres = titre, details, n, progres
        self.setObjectName('carteModule')
        self.setText(titre)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(titre + (' — ' + details if details else ''))
        pol = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        pol.setHeightForWidth(True)
        self.setSizePolicy(pol)

    def _polices(self):
        from PyQt6.QtGui import QFont
        ft = QFont(self.font())
        ft.setBold(True)
        return ft, self.font()

    def _decalage(self) -> int:
        from PyQt6.QtGui import QFontMetrics
        return QFontMetrics(self._polices()[0]).horizontalAdvance('00') + 8 if self.n else 0

    def changeEvent(self, ev):
        self.__dict__.pop('_memo', None)              # police ou style changés : mesures à refaire
        super().changeEvent(ev)

    def _rects(self, w: int):
        memo = self.__dict__.setdefault('_memo', {})
        if w not in memo:
            memo[w] = self._mesurer(w)
        return memo[w]

    def _mesurer(self, w: int):
        from PyQt6.QtGui import QFontMetrics
        ft, fd = self._polices()
        x0 = self.MARGE_X + self._decalage()
        larg = max(40, w - x0 - self.MARGE_X)
        drap = int(Qt.TextFlag.TextWordWrap)
        rt = QFontMetrics(ft).boundingRect(QRect(0, 0, larg, 10000), drap, self.titre)
        rd = QFontMetrics(fd).boundingRect(QRect(0, 0, w - 2 * self.MARGE_X, 10000), drap, self.details) \
            if self.details else QRect()
        return x0, larg, rt.height(), rd.height()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        _, _, ht, hd = self._rects(w)
        return 2 * self.MARGE_Y + ht + (3 + hd if hd else 0) + (10 if self.progres is not None else 0)

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(280, self.heightForWidth(280))

    def minimumSizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(180, 48)

    def paintEvent(self, _):
        from PyQt6.QtCore import QRectF
        from PyQt6.QtGui import QColor, QPainter, QPen
        from ....gui.theme import THEMES
        c = THEMES.get(theme_courant(), THEMES['sombre'])
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        actif = self.underMouse() or self.isDown()
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(c['selection'] if (actif or self.hasFocus()) else c['bordure']), 1.4 if self.hasFocus() else 1))
        p.setBrush(QColor(c['survol'] if actif else c['base']))
        p.drawRoundedRect(r, 10, 10)
        x0, larg, ht, hd = self._rects(self.width())
        ft, fd = self._polices()
        drap = int(Qt.TextFlag.TextWordWrap)
        y = self.MARGE_Y
        if self.n:
            p.setFont(ft)
            p.setPen(QColor(c['lien']))
            p.drawText(QRect(self.MARGE_X, y, x0 - self.MARGE_X, ht), int(Qt.AlignmentFlag.AlignTop), '%02d' % self.n)
        p.setFont(ft)
        p.setPen(QColor(c['texte']))
        p.drawText(QRect(x0, y, larg, ht), drap, self.titre)
        y += ht
        if hd:
            y += 3
            p.setFont(fd)
            p.setPen(QColor(c['texte_doux']))
            p.drawText(QRect(self.MARGE_X, y, self.width() - 2 * self.MARGE_X, hd), drap, self.details)
            y += hd
        if self.progres is not None:
            fait, total = self.progres
            yb = self.height() - self.MARGE_Y - 4
            lb = self.width() - 2 * self.MARGE_X
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(c['bordure']))
            p.drawRoundedRect(QRectF(self.MARGE_X, yb, lb, 4), 2, 2)
            if total and fait:
                p.setBrush(QColor(c['statut_ok']))
                p.drawRoundedRect(QRectF(self.MARGE_X, yb, max(4.0, lb * fait / total), 4), 2, 2)
        p.end()


def icone_plein_ecran(couleur) -> 'QIcon':
    """Quatre coins (plein écran), à la couleur du texte du thème : l'icône standard du style était sombre sur fond
    sombre."""
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QIcon, QPainter, QPen, QPixmap
    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(couleur, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        cx, cy = 16 - sx * 11, 16 - sy * 11
        p.drawPolyline([QPointF(cx, cy + sy * 8), QPointF(cx, cy), QPointF(cx + sx * 8, cy)])
    p.end()
    return QIcon(pm)


def comptes(m: dict) -> str:
    """« 18 questions · 1 anim. · 5 fiches » : les zéros omis, singulier pour 1 (comme Coupole Web)."""
    out = []
    for g, c in (('questions', 'q'), ('animations', 'a'), ('fiches', 'f'), ('tables', 't'), ('images', 'i')):
        n = len(m.get(g) or ())
        if n:
            out.append('%d\u00a0%s' % (n, tr('classe_%s_court%s' % (c, '1' if n == 1 and c != 'a' else ''))))
    return ' · '.join(out)


def bulles(racine):
    """Info-bulle de chaque élément interactif qui n'en a pas : son texte, son nom accessible ou son indication."""
    for w in [racine] + racine.findChildren(QWidget):
        if not isinstance(w, (QAbstractButton, QComboBox, QLineEdit, QAbstractSpinBox, QAbstractItemView)) or w.toolTip().strip():
            continue
        t = (w.text() if hasattr(w, 'text') and callable(w.text) and isinstance(w, QAbstractButton) else '') or \
            w.accessibleName() or (w.placeholderText() if isinstance(w, QLineEdit) else '')
        w.setToolTip((t or tr('classe_ouvrir_aide')).replace('&&', '&').strip())


class PageAccueil(QWidget):
    def __init__(self, vue):
        super().__init__()
        self.vue = vue
        v = QVBoxLayout(self)
        v.addWidget(_titre(tr('classe_accueil_titre'), 1.6))
        intro = QLabel(tr('classe_accueil_texte'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        self.reprise = QPushButton()
        self.reprise.setVisible(False)
        v.addWidget(self.reprise, 0, Qt.AlignmentFlag.AlignLeft)
        zone = QScrollArea()
        zone.setWidgetResizable(True)
        self.corps = QWidget()
        self.grille = QVBoxLayout(self.corps)
        zone.setWidget(self.corps)
        v.addWidget(zone, 1)
        self.remplir()

    def _carte(self, titre: str, details: str, rappel, n=None, progres=None) -> QPushButton:
        b = Carte(titre, details, n, progres)
        b.setToolTip(titre + ('\n' + tr('classe_progres_texte', r=progres[0], n=progres[1]) if progres and progres[1] else ''))
        b.clicked.connect(rappel)
        return b

    def remplir(self):
        _vider(self.grille)
        s = stockage().doc
        for titre_cle, liste in (('classe_modules', [m for m in contenu.modules() if m['affiche']]),
                                 ('classe_modules_bonus', [m for m in contenu.modules() if not m['affiche']])):
            self.grille.addWidget(_titre(tr(titre_cle), 1.15))
            g = GrilleCartes()
            for k, m in enumerate(liste):
                ids = [q['id'] for q in m['questions'] if q['ok']]
                b = S.bilan(s, ids)
                details = comptes(m) + (('  ·  ' + tr('classe_progres_texte', r=b['reussies'], n=b['total'])) if b['essayees'] else '')
                g.addWidget(self._carte(bi(m['titre']), details, lambda _=False, c=m['cle']: self.vue.aller_module(c, False),
                                        k + 1 if m['affiche'] else None, (b['reussies'], b['total'])))
            self.grille.addLayout(g)
            self.grille.addSpacing(6)
        # la bibliothèque : questions, fiches, tables et images, comme dans ClassAction
        ms = contenu.modules()
        n = lambda k: len({i for m in ms for i in m[k]})      # noqa: E731
        b = self._carte('📚  ' + tr('classe_bibliotheque_carte'), tr(
            'classe_bibliotheque_carte_texte', q=len({q['id'] for m in ms for q in m['questions']}), f=n('fiches'),
            t=n('tables'), i=n('images')), self.vue.aller_bibliotheque)
        g = GrilleCartes()
        g.addWidget(b)
        self.grille.addLayout(g)
        self.grille.addSpacing(6)
        # mes favoris (les plus récents d'abord)
        tete = QHBoxLayout()
        tete.addWidget(_titre('★ ' + tr('classe_favoris'), 1.15))
        tete.addStretch(1)
        tout = QPushButton(tr('classe_tout_voir'))
        tout.clicked.connect(self.vue.aller_favoris)
        tete.addWidget(tout)
        self.grille.addLayout(tete)
        g = GrilleCartes()
        favs = [f for f in favoris_affiches(s) if f['ok']][::-1][:12]
        for f in favs:
            g.addWidget(self._carte(f['titre'], tr('classe_genre_' + f['genre']) + ('  ·  ' + f['sous'] if f['sous'] else ''),
                                    lambda _=False, f=f: ouvrir_favori(self.vue, f)))
        if not favs:
            vide = QLabel(tr('classe_favoris_vide'))
            vide.setWordWrap(True)
            self.grille.addWidget(vide)
        self.grille.addLayout(g)
        self.grille.addStretch(1)
        vus = sorted(((k, v) for k, v in s['modules'].items() if v.get('derniere_question')), key=lambda x: x[1]['visite'], reverse=True)
        self.reprise.setVisible(False)
        if vus and contenu.module(vus[0][0]):
            k, v = vus[0]
            self.reprise.setText('▶ ' + tr('classe_reprendre', module=bi(contenu.module(k)['titre'])))
            try:
                self.reprise.clicked.disconnect()
            except TypeError:
                pass
            self.reprise.clicked.connect(lambda: self.vue.aller_question(k, v['derniere_question'], False))
            self.reprise.setVisible(True)
        bulles(self)


class PageModule(QWidget):
    def __init__(self, vue, cle: str, perso: bool, onglet: str = 'questions'):
        super().__init__()
        self.vue, self.cle, self.perso = vue, cle, perso
        s = stockage().doc
        self.mm = S.trouver_module(s, cle) if perso else None
        self.m = None if perso else contenu.module(cle)
        v = QVBoxLayout(self)
        self.titre = _titre(self.mm['nom'] if perso else bi(self.m['titre']))
        v.addWidget(self.titre)
        # une seule rangée sous le titre : titre d'origine, progression (texte + barre fine), actions
        actions = QHBoxLayout()
        actions.setSpacing(8)
        if not perso and self.m['original'] and self.m['original'] != bi(self.m['titre']):
            orig = QLabel(tr('classe_titre_origine', titre=self.m['original']))
            orig.setStyleSheet('color: palette(placeholder-text);')
            actions.addWidget(orig)
            actions.addSpacing(10)
        self.qs = questions_de(cle, self.mm)
        b = S.bilan(s, [q['id'] for q in self.qs if q['ok']])
        if self.qs:
            barre = QProgressBar()
            barre.setObjectName('progresFin')
            barre.setTextVisible(False)
            barre.setFixedWidth(140)
            barre.setRange(0, max(1, b['total']))
            barre.setValue(b['reussies'])
            barre.setFormat(tr('classe_progres_texte', r=b['reussies'], n=b['total']))
            barre.setAccessibleName(barre.format())
            self.l_progres = QLabel(barre.format())
            actions.addWidget(self.l_progres)
            actions.addWidget(barre)
        actions.addStretch(1)
        self.b_favori = BoutonFavori('module', cle, self.titre.text(), self, vue.annoncer, libelle=True)
        actions.addWidget(self.b_favori)
        if not perso:
            actions.addWidget(self._bouton('classe_copier_module', self._copier))
        else:
            actions.addWidget(self._bouton('classe_renommer', self._renommer))
            actions.addWidget(self._bouton('classe_copier', self._copier))
            actions.addWidget(self._bouton('classe_supprimer', self._supprimer))
        if self.qs:
            actions.addWidget(self._bouton('classe_reinit_progression', self._raz))
        v.addLayout(actions)
        self.onglets = QTabWidget()
        self.onglets.setAccessibleName(tr('classe_contenu_module'))
        v.addWidget(self.onglets, 1)
        self.remplir(onglet)
        if not perso:
            s['modules'][cle] = {'derniere_question': (s['modules'].get(cle) or {}).get('derniere_question'), 'visite': S.maintenant()}
            stockage().modifie()

    @staticmethod
    def _bouton(cle, rappel) -> QPushButton:
        b = QPushButton(tr(cle))
        b.clicked.connect(rappel)
        return b

    def ids(self, g):
        if self.mm:
            return [e['id'] for e in self.mm['elements'] if e['genre'] == g]
        return list(self.m[g + 's'])

    def remplir(self, onglet='questions'):
        self.onglets.clear()
        self.qs = questions_de(self.cle, self.mm)
        s = stockage().doc
        # questions
        arbre = QTreeWidget()
        arbre.setHeaderHidden(True)
        arbre.setAccessibleName(tr('classe_onglet_questions'))
        for t in TYPES:
            l = [q for q in self.qs if q['n'].startswith(t)]
            if not l:
                continue
            r = QTreeWidgetItem([tr('classe_type_' + t)])
            r.setFlags(Qt.ItemFlag.ItemIsEnabled)
            arbre.addTopLevelItem(r)
            for q in l:
                e = S.etat_question(s, q['id'])
                it = QTreeWidgetItem(['%s  %s  %s%s' % (SYMBOLES[e], q['n'], q['titre'], '' if q['ok'] else '  — ' + tr('classe_a_venir'))])
                it.setData(0, ROLE, q['id'])
                if est_favori('question', q['id']):
                    it.setIcon(0, icone_etoile(True))
                it.setToolTip(0, tr('classe_etat_' + e))
                if not q['ok']:
                    it.setDisabled(True)
                r.addChild(it)
            r.setExpanded(True)
        arbre.itemActivated.connect(lambda it, *_: it.data(0, ROLE) and self.vue.aller_question(self.cle, it.data(0, ROLE), self.perso))
        arbre.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        arbre.customContextMenuRequested.connect(lambda pos: self._menu_question(arbre, pos))
        self.onglets.addTab(arbre, '%s (%d)' % (tr('classe_onglet_questions'), len(self.qs)))
        # ressources
        retirer = (lambda g, i: self._retirer(g, i)) if self.perso else None
        for g in ('animation', 'fiche', 'table', 'image'):
            liste = ListeRessources(retirer=retirer)
            ids = [i for i in self.ids(g) if g != 'animation' or i in catalogue.PAR_ID]
            for i in ids:
                sous = tr('anim_theme_' + catalogue.PAR_ID[i].theme) if g == 'animation' else ''
                liste.ajouter(g, i, contenu.titre(g, i), sous=sous)
            if not ids:
                vide = QListWidgetItem(tr('classe_rien_' + g))
                vide.setFlags(Qt.ItemFlag.NoItemFlags)
                liste.addItem(vide)
            liste.ouvrir.connect(self.vue.ouvrir_ressource)
            k = self.onglets.addTab(liste, '%s (%d)' % (tr('classe_onglet_' + g + 's'), len(ids)))
            self.onglets.setTabEnabled(k, bool(ids))            # onglet vide : visible (le compte 0 informe) mais grisé
        if self.perso:
            self.onglets.addTab(self._organiser(), '%s (%d)' % (tr('classe_onglet_organiser'), len(self.mm['elements'])))
        noms = ['questions', 'animations', 'fiches', 'tables', 'images', 'organiser']
        if onglet in noms and noms.index(onglet) < self.onglets.count():
            self.onglets.setCurrentIndex(noms.index(onglet))
        bulles(self)

    def _menu_question(self, arbre, pos):
        it = arbre.itemAt(pos)
        if it is None or not it.data(0, ROLE):
            return
        if self.perso:
            m = QMenu(self)
            m.addAction(action_favori(m, 'question', it.data(0, ROLE), it.text(0), self.vue.annoncer))
            m.addAction(tr('classe_retirer')).triggered.connect(lambda: self._retirer('question', it.data(0, ROLE)))
        else:
            m = menu_ajouter(self, 'question', it.data(0, ROLE), it.text(0), annoncer=self.vue.annoncer)
        m.exec(arbre.viewport().mapToGlobal(pos))

    def _organiser(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel(tr('classe_organiser_aide')))
        self.liste_org = QListWidget()
        self.liste_org.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.liste_org.setAccessibleName(tr('classe_onglet_organiser'))
        for e in self.mm['elements']:
            it = QListWidgetItem('%s — %s' % (tr('classe_genre_' + e['genre']), contenu.titre(e['genre'], e['id'])))
            it.setData(ROLE, (e['genre'], e['id']))
            self.liste_org.addItem(it)
        self.liste_org.model().rowsMoved.connect(lambda *_: self._ordre_depuis_liste())
        v.addWidget(self.liste_org, 1)
        h = QHBoxLayout()
        for cle, f in (('classe_monter', lambda: self._deplacer(-1)), ('classe_descendre', lambda: self._deplacer(1)),
                       ('classe_retirer', self._retirer_courant)):
            b = QPushButton(tr(cle))
            b.clicked.connect(f)
            h.addWidget(b)
        h.addStretch(1)
        v.addLayout(h)
        QShortcut(QKeySequence('Alt+Up'), self.liste_org, lambda: self._deplacer(-1))
        QShortcut(QKeySequence('Alt+Down'), self.liste_org, lambda: self._deplacer(1))
        return w

    def _deplacer(self, d):
        i = self.liste_org.currentRow()
        if i < 0 or not S.deplacer_element(stockage().doc, self.cle, i, i + d):
            return
        stockage().modifie()
        self.remplir('organiser')
        self.liste_org.setCurrentRow(max(0, min(len(self.mm['elements']) - 1, i + d)))

    def _ordre_depuis_liste(self):
        nouveaux = [{'genre': self.liste_org.item(k).data(ROLE)[0], 'id': self.liste_org.item(k).data(ROLE)[1]}
                    for k in range(self.liste_org.count())]
        self.mm['elements'] = nouveaux
        self.mm['modifie'] = S.maintenant()
        stockage().modifie()

    def _retirer_courant(self):
        it = self.liste_org.currentItem()
        if it is not None:
            self._retirer(*it.data(ROLE))

    def _retirer(self, g, i):
        if S.retirer_element(stockage().doc, self.cle, {'genre': g, 'id': i}):
            stockage().modifie()
            self.remplir(['questions', 'animations', 'fiches', 'tables', 'images', 'organiser'][self.onglets.currentIndex()])

    def _copier(self):
        s = stockage().doc
        if self.perso:
            els, base = self.mm['elements'], self.mm['nom']
        else:
            els = [{'genre': 'question', 'id': q['id']} for q in self.qs] + \
                  [{'genre': g, 'id': i} for g in ('animation', 'fiche', 'table', 'image') for i in self.ids(g)]
            base = bi(self.m['titre'])
        n = S.creer_module(s, S.nom_libre(s, tr('classe_copie_de', nom=base)), els)
        stockage().modifie()
        self.vue.aller_module(n['id'], True)

    def _renommer(self):
        v, ok = QInputDialog.getText(self, tr('classe_renommer_module'), tr('classe_renommer_module'), text=self.mm['nom'])
        if ok and S.renommer_module(stockage().doc, self.cle, v):
            stockage().modifie()
            self.titre.setText(self.mm['nom'])
            self.vue.maj_fil()

    def _supprimer(self):
        if QMessageBox.question(self, tr('classe_supprimer'), tr('classe_supprimer_module_q', nom=self.mm['nom'])) != QMessageBox.StandardButton.Yes:
            return
        s = stockage().doc
        copie = S._clone(self.mm) if hasattr(S, '_clone') else dict(self.mm)
        k = s['mes_modules'].index(self.mm)
        S.supprimer_module(s, self.cle)
        stockage().modifie()
        self.vue.aller_mes_modules()
        self.vue.annoncer(tr('classe_module_supprime', nom=copie['nom']), lambda: (s['mes_modules'].insert(k, copie), stockage().modifie(), self.vue.aller_module(copie['id'], True)))

    def _raz(self):
        self.vue.effacer({'partie': 'module', 'id': self.cle, 'questions': [q['id'] for q in self.qs]},
                         tr('classe_reinit_module_q', nom=self.titre.text()))


class BoutonChoix(QPushButton):
    def __init__(self, lettre: str, texte_riche: str, fig, parent):
        super().__init__(parent)
        self.setObjectName('choix')
        self.setCheckable(True)
        self.setMinimumHeight(48)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        self.l_lettre = QLabel('<b>%s</b>' % lettre)
        self.l_lettre.setFixedWidth(26)
        lay.addWidget(self.l_lettre)
        corps = QVBoxLayout()
        if texte_riche:
            self.lab = etiquette(texte_riche, self)
            self.lab.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            corps.addWidget(self.lab)
        self.fig = None
        if fig:
            self.fig = FigureWidget(fig, theme_courant(), lettre, self, hauteur_max=180)
            self.fig.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            corps.addWidget(self.fig)
        lay.addLayout(corps, 1)

    def sizeHint(self):
        return self.layout().sizeHint()


class PageQuestion(QWidget):
    def __init__(self, vue, cle: str, qid: str, perso: bool):
        super().__init__()
        self.vue, self.cle, self.qid, self.perso = vue, cle, qid, perso
        self.q = contenu.question(qid)
        self.mm = S.trouver_module(stockage().doc, cle) if perso else None
        self.qs = ordre(questions_de(cle, self.mm))
        k = next((n for n, x in enumerate(self.qs) if x['id'] == qid), 0)
        self.info = self.qs[k] if self.qs else {'n': '', 'titre': ''}
        self.prec = self.qs[(k - 1) % len(self.qs)] if self.qs else None
        self.suiv = self.qs[(k + 1) % len(self.qs)] if self.qs else None
        self.parametres, self.graine = {}, '1'
        self.choisis, self.valide, self.reponse, self.indice = set(), False, False, False
        self.variantes = variantes(self.q)
        self.macros = contenu.macros()
        racine = QHBoxLayout(self)
        gauche = QScrollArea()
        gauche.setWidgetResizable(True)
        self.carte = QWidget()
        self.v = QVBoxLayout(self.carte)
        gauche.setWidget(self.carte)
        racine.addWidget(gauche, 3)
        self.panneau_liees = self._liees()
        racine.addWidget(self.panneau_liees, 1)
        tete = QHBoxLayout()
        self.b_prec = QToolButton()
        self.b_prec.setArrowType(Qt.ArrowType.LeftArrow)
        self.b_suiv = QToolButton()
        self.b_suiv.setArrowType(Qt.ArrowType.RightArrow)
        for b, x, cle_aide in ((self.b_prec, self.prec, 'classe_question_prec'), (self.b_suiv, self.suiv, 'classe_question_suiv')):
            if x:
                b.setToolTip(tr(cle_aide, n=x['n'], titre=x['titre']))
                b.setAccessibleName(b.toolTip())
                b.clicked.connect(lambda _=False, x=x: self.vue.aller_question(self.cle, x['id'], self.perso))
            tete.addWidget(b)
        typ = self.info['n'][:1] or {'warmup': 'W', 'general': 'G', 'challenge': 'C', 'discussion': 'D'}.get(self.q['type'], 'G')
        tete.addWidget(QLabel('<b>%s</b> · %s' % (self.info['n'], tr('classe_type_' + typ))))
        if self.q.get('statut_reponse') in ('corrigee', 'etablie_par_nous'):
            st = QLabel('<i>%s</i>' % tr('classe_statut_' + self.q['statut_reponse']))
            tete.addWidget(st)
        tete.addStretch(1)
        # ressources liées : panneau à droite en fenêtre large, menu « ★ n » en fenêtre étroite, rien s'il n'y en a pas
        self.b_liees = QToolButton()
        self.b_liees.setText('★ %d' % len(self.liees))
        self.b_liees.setToolTip(tr('classe_ressources_liees'))
        self.b_liees.setAccessibleName(tr('classe_ressources_liees'))
        self.b_liees.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self.b_liees)
        for g, i, texte in self.liees:
            menu.addAction(texte).triggered.connect(lambda _=False, g=g, i=i: self.vue.ouvrir_ressource(g, i))
        self.b_liees.setMenu(menu)
        self.b_liees.setVisible(False)
        tete.addWidget(self.b_liees)
        self.b_favori = BoutonFavori('question', qid, bi(self.q['titre']), self, self.vue.annoncer)
        tete.addWidget(self.b_favori)
        self.b_ajouter = QToolButton()
        self.b_ajouter.setText('+')
        self.b_ajouter.setToolTip(tr('classe_ajouter_a'))
        self.b_ajouter.setAccessibleName(tr('classe_ajouter_a'))
        self.b_ajouter.clicked.connect(lambda: menu_ajouter(self, 'question', qid, bi(self.q['titre'])).exec(self.b_ajouter.mapToGlobal(QPoint(0, self.b_ajouter.height()))))
        tete.addWidget(self.b_ajouter)
        self.b_plein = QToolButton()
        self.b_plein.setIcon(icone_plein_ecran(self.palette().color(self.palette().ColorRole.WindowText)))
        self.b_plein.setToolTip(tr('classe_presentation'))
        self.b_plein.setAccessibleName(tr('classe_presentation'))
        self.b_plein.clicked.connect(self.vue.basculer_plein_ecran)
        tete.addWidget(self.b_plein)
        self.v.addLayout(tete)
        self.l_titre = _titre(bi(self.q['titre']))
        self.v.addWidget(self.l_titre)
        self.menus = QHBoxLayout()
        self.v.addLayout(self.menus)
        self.l_enonce = etiquette('')
        f = self.l_enonce.font()
        f.setPointSizeF(f.pointSizeF() * 1.1)
        self.l_enonce.setFont(f)
        self.v.addWidget(self.l_enonce)
        self.zone_fig = QVBoxLayout()
        self.v.addLayout(self.zone_fig)
        self.zone_choix = QGridLayout()
        self.v.addLayout(self.zone_choix)
        act = QHBoxLayout()
        self.ouverte = self.q.get('forme') == 'ouverte'
        self.b_valider = QPushButton(tr('classe_valider'))
        self.b_valider.clicked.connect(self.valider)
        self.b_reponse = QPushButton(tr('classe_montrer_reponse'))
        self.b_reponse.setCheckable(True)
        self.b_reponse.clicked.connect(self.basculer_reponse)
        a_indice = bool(self.q.get('indice') or self.q.get('figure_indice') or '"afficher": "indice"' in str(self.q.get('figure')))
        self.b_indice = QPushButton(tr('classe_montrer_indice'))
        self.b_indice.setCheckable(True)
        self.b_indice.setVisible(a_indice)
        self.b_indice.clicked.connect(self.basculer_indice)
        aleatoire = bool(self.q.get('aleatoire') or self.q.get('melange') or self.q.get('choix_conserves') is not None)
        self.b_tirage = QPushButton(tr('classe_nouveau_tirage'))
        self.b_tirage.setVisible(aleatoire)
        self.b_tirage.clicked.connect(self.nouveau_tirage)
        self.b_revoir = QPushButton(tr('classe_a_revoir'))
        self.b_revoir.setCheckable(True)
        self.b_revoir.setChecked(bool((stockage().doc['questions'].get(qid) or {}).get('a_revoir')))
        self.b_revoir.clicked.connect(self.basculer_revoir)
        for b in (self.b_valider, self.b_reponse, self.b_indice, self.b_tirage, self.b_revoir):
            act.addWidget(b)
        self.b_valider.setVisible(not self.ouverte)
        act.addStretch(1)
        self.v.addLayout(act)
        self.l_retour = QLabel('')
        self.l_retour.setAccessibleName(tr('classe_retour'))
        self.v.addWidget(self.l_retour)
        self.l_indice = etiquette('')
        self.l_indice.setVisible(False)
        self.v.addWidget(self.l_indice)
        self.fig_indice_zone = QVBoxLayout()
        self.v.addLayout(self.fig_indice_zone)
        self.l_explication = etiquette('')
        self.l_explication.setVisible(False)
        self.v.addWidget(self.l_explication)
        if self.q.get('correction'):
            self.v.addWidget(Repliable(tr('classe_ce_qui_a_change'), '<ul>%s</ul>' % ''.join('<li>%s</li>' % texte_html(bi(c)) for c in self.q['correction'])))
        cr = QLabel('<small>%s</small>' % _html.escape(tr('classe_credit_question')))
        cr.setWordWrap(True)
        self.v.addWidget(cr)
        self.v.addStretch(1)
        for touche, f2 in (('R', self.b_reponse.click), ('I', lambda: self.b_indice.isVisible() and self.b_indice.click()),
                           ('N', lambda: self.b_tirage.isVisible() and self.b_tirage.click()), ('F', self.b_plein.click),
                           ('Right', self.b_suiv.click), ('Left', self.b_prec.click), ('Return', self.valider)):
            QShortcut(QKeySequence(touche), self, f2, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        for i, lettre in enumerate('ABCDEFGH'):
            QShortcut(QKeySequence(lettre), self, lambda i=i: self._choisir_rang(i), context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        s = stockage().doc
        s['modules'][cle] = {'derniere_question': qid, 'visite': S.maintenant()}
        stockage().modifie()
        self.calculer()
        self.remplir()

    LARGEUR_PANNEAU = 980          # en dessous, les ressources liées passent dans le menu « ★ n » de l'en-tête

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if hasattr(self, 'b_liees') and hasattr(self, 'fig'):
            self._adapter()

    def _hauteur_figure(self) -> int:
        """Figure bornée à ~45 % de la hauteur visible (160 à 420 px) : les choix restent en vue en petite fenêtre."""
        return int(max(160, min(420, 0.45 * max(1, self.height()))))

    def _adapter(self):
        large = self.width() >= self.LARGEUR_PANNEAU
        self.panneau_liees.setVisible(large and bool(self.liees))
        self.b_liees.setVisible(not large and bool(self.liees))
        for f in [getattr(self, 'fig', None)]:
            if f is not None and f.hauteur_max != self._hauteur_figure():
                f.hauteur_max = self._hauteur_figure()
                f.updateGeometry()

    # ------------------------------------------------------------ état
    def calculer(self):
        try:
            self.inst = instancier(self.q, self.graine, self.parametres, langue(), macros=self.macros)
        except Exception:
            self.parametres = {}
            self.inst = instancier(self.q, '1', {}, langue(), macros=self.macros)
        self.parametres = dict(self.inst['parametres'])
        self.multiple = len(self.inst['bonnes']) > 1

    def remplir(self):
        _vider(self.menus)
        for prm in self.q.get('parametres', []):
            cb = QComboBox()
            cb.setAccessibleName(bi(prm['libelle']))
            dispo = {v.get(prm['id']) for v in self.variantes if all(v.get(k) == x for k, x in self.parametres.items() if k != prm['id'] and k in v)}
            for o in prm['options']:
                if o['id'] in dispo:
                    cb.addItem(bi(o['libelle']), o['id'])
            cb.setCurrentIndex(max(0, cb.findData(self.parametres.get(prm['id']))))
            cb.currentIndexChanged.connect(lambda _=0, cb=cb, prm=prm: self._menu(prm['id'], cb.currentData()))
            lab = QLabel(bi(prm['libelle']))
            lab.setBuddy(cb)
            self.menus.addWidget(lab)
            self.menus.addWidget(cb)
        self.menus.addStretch(1)
        self.l_enonce.setText(texte_html(self.inst['enonce'] or '', self.l_enonce))
        _vider(self.zone_fig)
        self.fig = None
        if self.inst['figure']:
            self.fig = FigureWidget(self.inst['figure'], theme_courant(), bi(self.q['figure'].get('alt')) if isinstance(self.q.get('figure'), dict) and self.q['figure'].get('alt') else tr('classe_figure_question'), hauteur_max=self._hauteur_figure())
            self.zone_fig.addWidget(self.fig)
            cr = self._credits(self.inst['figure'])
            if cr:
                self.zone_fig.addWidget(etiquette(cr))
        _vider(self.zone_choix)
        self.boutons = {}
        disp = self.q.get('disposition_choix')
        ncol = {'ligne': max(1, len(self.inst['choix'])), 'grille': 2, 'colonnes': 2}.get(disp, 1)
        for k, c in enumerate(self.inst['choix']):
            b = BoutonChoix(c['lettre'], texte_html(c.get('texte') or '', self), c.get('figure'), self)
            b.setAccessibleName('%s. %s' % (c['lettre'], (c.get('texte') or tr('classe_figure_choix')).replace('**', '').replace('$', '')))
            b.clicked.connect(lambda _=False, i=c['id']: self.choisir(i))
            self.boutons[c['id']] = b
            self.zone_choix.addWidget(b, k // ncol, k % ncol)
        self.l_indice.setText('<b>%s</b><br>%s' % (_html.escape(tr('classe_indice')), texte_html(self.inst['indice'] or '', self.l_indice)))
        _vider(self.fig_indice_zone)
        if self.indice and self.inst.get('figure_indice'):
            self.fig_indice_zone.addWidget(FigureWidget(self.inst['figure_indice'], theme_courant(), tr('classe_figure_indice'), hauteur_max=300))
        ex = ''
        if self.ouverte or self.inst['elements_de_reponse']:
            ex += '<b>%s</b><ul>%s</ul>' % (_html.escape(tr('classe_elements_reponse')),
                                            ''.join('<li>%s</li>' % texte_html(t) for t in self.inst['elements_de_reponse']))
        if self.inst['explication']:
            ex += '<b>%s</b><br>%s' % (_html.escape(tr('classe_explication')), texte_html(self.inst['explication'], self.l_explication))
        self.l_explication.setText(ex)
        bulles(self)
        self.maj()

    @staticmethod
    def _credits(fig) -> str:
        refs = set()

        def voir(e):
            if isinstance(e, dict):
                if e.get('type') == 'image' and e.get('ref'):
                    refs.add(str(e['ref']))
                for x in e.values():
                    voir(x)
            elif isinstance(e, list):
                for x in e:
                    voir(x)
        voir(fig)
        from .ressources_qt import credit_html
        im = contenu.images_questions()
        return ' · '.join(credit_html(im[r]) for r in sorted(refs) if r in im)

    def maj(self):
        for i, b in self.boutons.items():
            b.setChecked(i in self.choisis)
            bonne = i in self.inst['bonnes']
            if (self.reponse or self.valide) and bonne:
                b.setStyleSheet('QPushButton{border:2px solid #ff9900; background: rgba(255,153,0,40);}')
            elif self.valide and i in self.choisis:
                b.setStyleSheet('QPushButton{border:2px solid #e5736a;}')
            else:
                b.setStyleSheet('')
            if b.fig:
                b.fig.regler(self.reponse, self.indice, self.inst['bonnes'])
        if self.fig:
            self.fig.regler(self.reponse, self.indice, self.inst['bonnes'])
        self.b_valider.setEnabled(bool(self.choisis) and not self.valide)
        self.l_indice.setVisible(self.indice)
        self.l_explication.setVisible(self.reponse or self.valide)

    # ------------------------------------------------------------ actions
    def _menu(self, mid, val):
        if val is None or self.parametres.get(mid) == val:
            return
        self.parametres[mid] = val
        self._nouvelle()

    def nouveau_tirage(self):
        self.graine = format(random.getrandbits(30), 'x')
        self._nouvelle()

    def _nouvelle(self):
        self.calculer()
        self.choisis, self.valide, self.reponse = set(), False, False
        self.b_reponse.setChecked(False)
        self.b_reponse.setText(tr('classe_montrer_reponse'))
        self.l_retour.setText('')
        self.remplir()

    def _choisir_rang(self, i):
        if i < len(self.inst['choix']):
            self.choisir(self.inst['choix'][i]['id'])
            self.boutons[self.inst['choix'][i]['id']].setFocus()

    def choisir(self, i):
        if self.valide:
            self.valide = False
            self.l_retour.setText('')
        if self.multiple:
            self.choisis ^= {i}
        else:
            self.choisis = {i}
        self.maj()

    def valider(self):
        if not self.choisis or self.valide or self.ouverte:
            return
        bonnes = set(self.inst['bonnes'])
        juste = self.choisis == bonnes
        s = stockage().doc
        S.noter_tentative(s, self.qid, {'date': S.maintenant(), 'reponse': sorted(self.choisis), 'juste': juste,
                                        'parametres': dict(self.parametres), 'graine': self.graine})
        s['modules'][self.cle] = {'derniere_question': self.qid, 'visite': S.maintenant()}
        stockage().modifie()
        self.valide = True
        from ....gui.theme import THEMES
        c = THEMES.get(theme_courant(), THEMES['sombre'])
        self.l_retour.setText('<b style="color:%s">%s</b>' % (c['statut_ok'] if juste else c['statut_echec'], _html.escape(
            tr('classe_juste') if juste else tr('classe_faux', lettres=', '.join(self.inst['bonnes_lettres'])))))
        self.b_revoir.setChecked(bool(s['questions'][self.qid].get('a_revoir')))
        self.maj()

    def basculer_reponse(self):
        self.reponse = self.b_reponse.isChecked()
        self.b_reponse.setText(tr('classe_cacher_reponse' if self.reponse else 'classe_montrer_reponse'))
        if self.reponse:
            S.marquer(stockage().doc, self.qid, 'reponse_vue')
            stockage().modifie()
            self._clignoter(7)
        self.maj()

    def _clignoter(self, n):
        """La bonne réponse clignote en orange (200 ms, 1,5 s) puis reste orange, comme dans ClassAction."""
        if n <= 0 or not self.reponse:
            return self.maj()
        for i in self.inst['bonnes']:
            b = self.boutons.get(i)
            if b:
                b.setStyleSheet('QPushButton{border:2px solid #ff9900; background: rgba(255,153,0,%d);}' % (110 if n % 2 else 20))
        if not hasattr(self, '_minuterie_clignotement'):        # enfant de la page : rien ne survit à la page
            self._minuterie_clignotement = QTimer(self)
            self._minuterie_clignotement.setSingleShot(True)
            self._minuterie_clignotement.timeout.connect(self._clignoter_suite)   # méthode liée, pas de lambda
        self._reste_clignotements = n - 1
        self._minuterie_clignotement.start(200)

    def _clignoter_suite(self):
        self._clignoter(self._reste_clignotements)

    def basculer_indice(self):
        self.indice = self.b_indice.isChecked()
        self.b_indice.setText(tr('classe_cacher_indice' if self.indice else 'classe_montrer_indice'))
        if self.indice:
            S.marquer(stockage().doc, self.qid, 'indice_vu')
            stockage().modifie()
        _vider(self.fig_indice_zone)
        if self.indice and self.inst.get('figure_indice'):
            self.fig_indice_zone.addWidget(FigureWidget(self.inst['figure_indice'], theme_courant(), tr('classe_figure_indice'), hauteur_max=300))
        self.maj()

    def basculer_revoir(self):
        S.marquer(stockage().doc, self.qid, 'a_revoir', self.b_revoir.isChecked())
        stockage().modifie()

    def _liees(self) -> QWidget:
        w = QFrame()
        w.setObjectName('panneauLiees')
        w.setFrameShape(QFrame.Shape.StyledPanel)
        w.setMinimumWidth(220)
        w.setMaximumWidth(340)
        v = QVBoxLayout(w)
        v.addWidget(_titre('★ ' + tr('classe_ressources_liees'), 1.05))
        l = contenu.liees(self.qid)
        liste = ListeRessources()
        liste.setWordWrap(True)
        liste.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.liees = []
        for g in ('animations', 'fiches', 'tables', 'images'):
            for i, lien in l.get(g, []):
                if g == 'animations' and i not in catalogue.PAR_ID:
                    continue
                liste.ajouter(g[:-1], i, contenu.titre(g[:-1], i), etoile=lien != 'mots-clés',
                              sous=tr('classe_genre_' + g[:-1]) + (' · ' + tr('classe_lien_mots_cles') if lien == 'mots-clés' else ''))
                self.liees.append((g[:-1], i, ('★ ' if lien != 'mots-clés' else '') + contenu.titre(g[:-1], i) + '  —  ' + tr('classe_genre_' + g[:-1])))
        if not self.liees:
            liste.addItem(QListWidgetItem(tr('classe_aucune_liee')))
        liste.ouvrir.connect(self.vue.ouvrir_ressource)
        v.addWidget(liste, 1)
        if (self.q.get('animation') or {}).get('role'):
            v.addWidget(etiquette(texte_html(bi(self.q['animation']['role']))))
        return w


def _html_surligne(texte: str, mots) -> str:
    return ''.join('<b style="background-color:%s">%s</b>' % ('rgba(224,165,38,0.32)', _html.escape(t)) if m else _html.escape(t)
                   for t, m in surligner(texte, mots))


class PageRecherche(QWidget):
    """Recherche bilingue (moteur commun avec Coupole Web) : résultats groupés par type, dans l'ordre du meilleur
    résultat de chaque type, titres et passages surlignés dans la langue de l'interface ; quand la correspondance
    n'est que dans l'autre langue, le titre de l'autre langue suit.  Lien ☆/★ : favori."""

    PAR_GROUPE = 30

    def __init__(self, vue, q0=''):
        super().__init__()
        self.vue = vue
        v = QVBoxLayout(self)
        v.addWidget(_titre(tr('classe_recherche_titre')))
        self.champ = QLineEdit(q0)
        self.champ.setPlaceholderText(tr('classe_recherche_indice'))
        self.champ.setClearButtonEnabled(True)
        self.champ.setAccessibleName(tr('classe_recherche_titre'))
        self.champ.setAccessibleDescription(tr('classe_recherche_bilingue'))
        v.addWidget(self.champ)
        h = QHBoxLayout()
        aide = QLabel(tr('classe_recherche_bilingue'))
        aide.setWordWrap(True)
        aide.setStyleSheet('color: palette(placeholder-text);')
        h.addWidget(aide, 1)
        self.fav = QCheckBox(tr('classe_favoris_seulement'))
        self.fav.toggled.connect(lambda *_: self.maj())
        h.addWidget(self.fav)
        v.addLayout(h)
        self.compte = QLabel('')
        v.addWidget(self.compte)
        self.vue_res = QTextBrowser()
        self.vue_res.setOpenLinks(False)
        self.vue_res.setAccessibleName(tr('classe_recherche_titre'))
        self.vue_res.anchorClicked.connect(self._lien)
        v.addWidget(self.vue_res, 1)
        self.deplies = set()
        self.minuteur = QTimer(self)
        self.minuteur.setSingleShot(True)
        self.minuteur.setInterval(150)
        self.minuteur.timeout.connect(self.maj)
        self.champ.textChanged.connect(lambda *_: (self.deplies.clear(), self.minuteur.start()))
        stockage().abonner_faible(self._sauvegarde_changee)
        self.maj()

    def _sauvegarde_changee(self):
        self.minuteur.start()

    def resultats(self) -> list:
        r = contenu.chercher(self.champ.text())
        if self.fav.isChecked():
            r = [x for x in r if est_favori(x['doc']['g'], x['doc']['id'])]
        return r

    def maj(self):
        try:
            texte = self.champ.text()
        except RuntimeError:
            return
        r = self.resultats()
        self.compte.setText(tr('classe_n_resultats', n=len(r)) if r else (tr('classe_aucun_resultat', q=texte) if texte.strip() else ''))
        lg = langue()
        autre = 'en' if lg == 'fr' else 'fr'
        info = contenu.info_questions()
        ordre = []
        for x in r:
            if x['doc']['g'] not in ordre:
                ordre.append(x['doc']['g'])
        morceaux = []
        for g in ordre:
            tous = [x for x in r if x['doc']['g'] == g]
            montres = tous if g in self.deplies else tous[:self.PAR_GROUPE]
            morceaux.append('<h3>%s <span style="color:gray">(%d)</span></h3>' % (_html.escape(tr('classe_onglet_' + g + 's')), len(tous)))
            for x in montres:
                d = x['doc']
                titre = (d['t'] or {}).get(lg) or (d['t'] or {}).get(autre) or d['id']
                if g == 'question':
                    mod = info[d['id']]['module']
                elif g == 'module':
                    mod = d['id']
                else:
                    mod = (d.get('m') or [''])[0]
                sous = bi(contenu.module(mod)['titre']) if mod and contenu.module(mod) and g != 'module' else ''
                if g == 'animation':
                    e = catalogue.PAR_ID.get(d['id'])
                    sous = tr('anim_theme_' + e.theme) if e else ''
                etoile = '★' if est_favori(g, d['id']) else '☆'
                ligne = '<p style="margin:2px 0 8px 0"><a href="ouvrir:%s:%s:%s">%s</a>' % (g, d['id'], mod, _html_surligne(titre, x['mots']))
                if sous:
                    ligne += ' <span style="color:gray">— %s</span>' % _html.escape(sous)
                ligne += ' &nbsp;<a href="favori:%s:%s" title="%s">%s</a>' % (g, d['id'], _html.escape(tr('classe_favori_nom', titre=titre)), etoile)
                ici = any(m for _, m in surligner(titre, x['mots']))
                autres = [t for t in ((d['t'] or {}).get(autre, ''), d.get('o') or '') if t and t != titre and any(m for _, m in surligner(t, x['mots']))]
                rtxt = (d.get('r') or {}).get(lg, '') if isinstance(d.get('r'), dict) else ''
                if not ici and autres:
                    ligne += '<br><i style="color:gray">%s</i>' % _html_surligne(tr('classe_aussi_en', titre=autres[0]), x['mots'])
                elif rtxt and any(m for _, m in surligner(rtxt, x['mots'])):
                    ligne += '<br><span style="color:gray">%s</span>' % _html_surligne(extrait(rtxt, x['mots'], 150), x['mots'])
                morceaux.append(ligne + '</p>')
            if len(montres) < len(tous):
                morceaux.append('<p><a href="plus:%s">%s</a></p>' % (g, _html.escape('+ %d' % (len(tous) - len(montres)))))
        barre = self.vue_res.verticalScrollBar().value()
        self.vue_res.setHtml(''.join(morceaux))
        self.vue_res.verticalScrollBar().setValue(barre)

    def _lien(self, url):
        quoi, _, reste = url.toString().partition(':')
        if quoi == 'plus':
            self.deplies.add(reste)
            return self.maj()
        if quoi == 'favori':
            g, _, i = reste.partition(':')
            return basculer_favori(g, i, contenu.titre(g, i) if g != 'module' else bi((contenu.module(i) or {}).get('titre')), self.vue.annoncer)
        g, i, mod = (reste.split(':') + ['', ''])[:3]
        if g == 'question':
            self.vue.aller_question(mod, i, False)
        elif g == 'module':
            self.vue.aller_module(i, False)
        else:
            self.vue.ouvrir_ressource(g, i)


# ================================================================== favoris et bibliothèque
ORDRE_FAVORIS = ('module', 'animation', 'question', 'fiche', 'table', 'image')


def favoris_affiches(s) -> list:
    """Favoris dans l'ordre d'ajout : {genre, id, titre, sous, ajoute, ok, module} (titres dans la langue de
    l'interface ; un favori qui n'existe plus reste, marqué « indisponible »)."""
    info = contenu.info_questions()
    out = []
    for f in s['favoris']:
        g, i = f['genre'], f['id']
        d = {'genre': g, 'id': i, 'ajoute': f['ajoute'], 'ok': True, 'sous': '', 'module': ''}
        if g == 'module':
            m = contenu.module(i)
            mm = S.trouver_module(s, i)
            if m:
                d.update(titre=bi(m['titre']), module=i)
            elif mm:
                d.update(titre=mm['nom'], sous=tr('classe_genre_collection'), module=i, perso=True)
            else:
                d.update(titre=i, sous=tr('classe_indisponible'), ok=False)
        elif g == 'animation':
            e = catalogue.PAR_ID.get(i)
            d.update(titre=tr('anim_nom_' + e.cle), sous=tr('anim_theme_' + e.theme)) if e else d.update(titre=i, sous=tr('classe_indisponible'), ok=False)
        elif g == 'question':
            q = info.get(i)
            if q and q['ok']:
                d.update(titre=bi(q['t']) if q['t'] else i, sous='%s · %s' % (bi(contenu.module(q['module'])['titre']), q['n']), module=q['module'])
            else:
                d.update(titre=i, sous=tr('classe_indisponible'), ok=False)
        else:
            o = {'fiche': contenu.fiche, 'table': contenu.table, 'image': contenu.image}[g](i)
            d.update(titre=bi(o['titre'])) if o else d.update(titre=i, sous=tr('classe_indisponible'), ok=False)
        out.append(d)
    return out


def ouvrir_favori(vue, f: dict):
    if not f['ok']:
        return
    if f['genre'] == 'module':
        vue.aller_module(f['id'], bool(f.get('perso')))
    elif f['genre'] == 'question':
        vue.aller_question(f['module'], f['id'], False)
    else:
        vue.ouvrir_ressource(f['genre'], f['id'])


class PageFavoris(QWidget):
    """« Mes favoris » : groupés par type, filtre par type, tri (ajout récent, ancien, titre) ; clic droit ou Suppr :
    retirer ; les collections (ex-« Mes modules ») au second plan, par « Organiser en collections… »."""

    def __init__(self, vue):
        super().__init__()
        self.vue = vue
        v = QVBoxLayout(self)
        v.addWidget(_titre(tr('classe_favoris')))
        t = QLabel(tr('classe_favoris_texte'))
        t.setWordWrap(True)
        v.addWidget(t)
        h = QHBoxLayout()
        h.addWidget(QLabel(tr('classe_filtre_type')))
        self.type = QComboBox()
        self.type.setAccessibleName(tr('classe_filtre_type'))
        self.type.addItem(tr('classe_tous_types'), '')
        for g in ORDRE_FAVORIS:
            self.type.addItem(tr('classe_onglet_' + g + 's'), g)
        h.addWidget(self.type)
        h.addSpacing(12)
        h.addWidget(QLabel(tr('classe_trier')))
        self.tri = QComboBox()
        self.tri.setAccessibleName(tr('classe_trier'))
        for k in ('recent', 'ancien', 'titre'):
            self.tri.addItem(tr('classe_tri_' + k), k)
        h.addWidget(self.tri)
        h.addStretch(1)
        v.addLayout(h)
        self.arbre = QTreeWidget()
        self.arbre.setHeaderHidden(True)
        self.arbre.setAccessibleName(tr('classe_favoris'))
        self.arbre.itemActivated.connect(lambda it, *_: it.data(0, ROLE) and ouvrir_favori(self.vue, it.data(0, ROLE)))
        self.arbre.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.arbre.customContextMenuRequested.connect(self._menu)
        QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self.arbre, self._retirer_courant)
        QShortcut(QKeySequence('Ctrl+D'), self.arbre, self._retirer_courant)
        v.addWidget(self.arbre, 1)
        bas = QHBoxLayout()
        b = QPushButton(tr('classe_organiser_collections'))
        b.clicked.connect(vue.aller_mes_modules)
        bas.addWidget(b)
        aide = QLabel(tr('classe_collections_aide'))
        aide.setStyleSheet('color: palette(placeholder-text);')
        bas.addWidget(aide, 1)
        v.addLayout(bas)
        self.type.currentIndexChanged.connect(lambda *_: self.remplir())
        self.tri.currentIndexChanged.connect(lambda *_: self.remplir())
        self._differe = QTimer(self)
        self._differe.setSingleShot(True)
        self._differe.setInterval(0)
        self._differe.timeout.connect(self._remplir_sur)
        stockage().abonner_faible(self._demander)
        self.remplir()

    def _demander(self):
        self._differe.start()

    def _remplir_sur(self):
        try:
            self.remplir()
        except RuntimeError:
            pass

    def remplir(self):
        self.arbre.clear()
        tous = favoris_affiches(stockage().doc)
        tri = self.tri.currentData()
        if tri == 'recent':
            tous = tous[::-1]
        elif tri == 'titre':
            import locale
            tous = sorted(tous, key=lambda f: locale.strxfrm(f['titre'].casefold()))
        filtre = self.type.currentData()
        if not tous:
            it = QTreeWidgetItem([tr('classe_favoris_vide')])
            it.setFlags(Qt.ItemFlag.NoItemFlags)
            self.arbre.addTopLevelItem(it)
            return
        for g in ORDRE_FAVORIS:
            l = [f for f in tous if f['genre'] == g and (not filtre or filtre == g)]
            if not l:
                continue
            r = QTreeWidgetItem(['%s (%d)' % (tr('classe_onglet_' + g + 's'), len(l))])
            r.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.arbre.addTopLevelItem(r)
            for f in l:
                it = QTreeWidgetItem([f['titre'] + ('  —  ' + f['sous'] if f['sous'] else '')])
                it.setIcon(0, icone_etoile(True))
                it.setData(0, ROLE, f)
                if not f['ok']:
                    it.setDisabled(True)
                r.addChild(it)
            r.setExpanded(True)

    def _retirer(self, f):
        basculer_favori(f['genre'], f['id'], f['titre'], self.vue.annoncer)

    def _retirer_courant(self):
        it = self.arbre.currentItem()
        if it is not None and it.data(0, ROLE):
            self._retirer(it.data(0, ROLE))

    def _menu(self, pos):
        it = self.arbre.itemAt(pos)
        if it is None or not it.data(0, ROLE):
            return
        f = it.data(0, ROLE)
        m = QMenu(self)
        m.addAction(icone_etoile(False, self.palette().color(self.palette().ColorRole.WindowText)),
                    tr('classe_favori_retirer')).triggered.connect(lambda: self._retirer(f))
        if f['genre'] != 'module':
            m.addMenu(menu_ajouter(m, f['genre'], f['id'], f['titre']))
        m.exec(self.arbre.viewport().mapToGlobal(pos))


_VIGNETTES: dict = {}


class PageBibliotheque(QWidget):
    """La présentation d'origine de ClassAction : un onglet par type (Questions, Fiches, Tables, Images) montre tout le
    contenu de ce type, rangé par module dans l'ordre d'origine ; filtres module et favoris ; vignettes des images
    (dessinées une à une, aux moments creux) ; étoile (Ctrl+D, clic droit).  Les animations ont leur propre vue
    (bouton « Animations ») : l'onglet qui la répétait a été retiré."""

    ONGLETS = ('questions', 'fiches', 'tables', 'images')
    GENRE = {'questions': 'question', 'fiches': 'fiche', 'tables': 'table', 'images': 'image'}

    def __init__(self, vue, onglet='questions', module='', favoris=False):
        super().__init__()
        self.vue = vue
        v = QVBoxLayout(self)
        v.addWidget(_titre(tr('classe_bibliotheque')))
        t = QLabel(tr('classe_bibliotheque_texte'))
        t.setWordWrap(True)
        v.addWidget(t)
        h = QHBoxLayout()
        h.addWidget(QLabel(tr('classe_filtre_module')))
        self.module = QComboBox()
        self.module.setAccessibleName(tr('classe_filtre_module'))
        self.module.addItem(tr('classe_tous_les_modules'), '')
        for m in contenu.modules():
            self.module.addItem(bi(m['titre']) + ('' if m['affiche'] else ' (%s)' % tr('classe_modules_bonus').lower()), m['cle'])
        self.module.setCurrentIndex(max(0, self.module.findData(module)))
        h.addWidget(self.module)
        h.addSpacing(12)
        self.fav = QCheckBox(tr('classe_favoris_seulement'))
        self.fav.setChecked(favoris)
        h.addWidget(self.fav)
        h.addStretch(1)
        v.addLayout(h)
        self.affichage = QLabel('')
        v.addWidget(self.affichage)
        self.onglets = QTabWidget()
        self.onglets.setAccessibleName(tr('classe_bibliotheque'))
        v.addWidget(self.onglets, 1)
        self._file = []
        self._minuteur = QTimer(self)
        self._minuteur.setInterval(15)
        self._minuteur.timeout.connect(self._vignette_suivante)
        self.module.currentIndexChanged.connect(lambda *_: self.remplir())
        self.fav.toggled.connect(lambda *_: self.remplir())
        self.onglets.currentChanged.connect(lambda *_: (self._maj_affichage(), self._file and self._minuteur.start()))
        self.remplir(onglet)

    def elements(self, m, onglet) -> list:
        g = self.GENRE[onglet]
        ids = [q['id'] for q in m['questions']] if onglet == 'questions' else list(m[onglet])
        if onglet == 'animations':
            ids = [i for i in ids if i in catalogue.PAR_ID]
        if self.fav.isChecked():
            ids = [i for i in ids if est_favori(g, i)]
        return ids

    def modules_vus(self) -> list:
        k = self.module.currentData()
        return [m for m in contenu.modules() if not k or m['cle'] == k]

    def total(self, onglet) -> int:
        return len({i for m in self.modules_vus() for i in self.elements(m, onglet)})

    def remplir(self, onglet=None):
        onglet = onglet or (self.ONGLETS[self.onglets.currentIndex()] if self.onglets.count() else 'questions')
        self._file = []
        self.onglets.blockSignals(True)
        self.onglets.clear()
        s = stockage().doc
        for o in self.ONGLETS:
            g = self.GENRE[o]
            if o in ('animations', 'images'):
                w = QListWidget()
                w.setViewMode(QListWidget.ViewMode.IconMode)
                w.setIconSize(QSize(176, 112))
                w.setGridSize(QSize(200, 160))
                w.setResizeMode(QListWidget.ResizeMode.Adjust)
                w.setWordWrap(True)
                w.setMovement(QListWidget.Movement.Static)
                w.setAccessibleName(tr('classe_onglet_' + o))
                for m in self.modules_vus():
                    ids = self.elements(m, o)
                    if not ids:
                        continue
                    sep = QListWidgetItem('— %s (%d) —' % (bi(m['titre']), len(ids)))
                    sep.setFlags(Qt.ItemFlag.NoItemFlags)
                    w.addItem(sep)
                    for i in ids:
                        titre = contenu.titre(g, i)
                        it = QListWidgetItem(('★ ' if est_favori(g, i) else '') + titre)
                        it.setData(ROLE, (g, i))
                        it.setData(ROLE_TITRE, titre)
                        it.setToolTip(titre)
                        if (g, i) in _VIGNETTES:
                            it.setIcon(_VIGNETTES[(g, i)])
                        else:
                            self._file.append((w, it, g, i))
                        w.addItem(it)
                w.itemActivated.connect(lambda it, *_: it.data(ROLE) and self.vue.ouvrir_ressource(*it.data(ROLE)))
                w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                w.customContextMenuRequested.connect(lambda pos, w=w: self._menu(w, pos))
                QShortcut(QKeySequence('Ctrl+D'), w, lambda w=w: self._basculer(w.currentItem()))
            else:
                w = QTreeWidget()
                w.setHeaderHidden(True)
                w.setAccessibleName(tr('classe_onglet_' + o))
                for m in self.modules_vus():
                    ids = self.elements(m, o)
                    if not ids:
                        continue
                    r = QTreeWidgetItem(['%s (%d)' % (bi(m['titre']), len(ids))])
                    r.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    w.addTopLevelItem(r)
                    if o == 'questions':
                        for t in TYPES:
                            for q in [q for q in m['questions'] if q['n'].startswith(t) and q['id'] in ids]:
                                e = S.etat_question(s, q['id'])
                                titre = bi(q['t']) if q['t'] else q['id']
                                it = QTreeWidgetItem(['%s  %s  %s%s' % (SYMBOLES[e], q['n'], titre, '' if q['ok'] else '  — ' + tr('classe_a_venir'))])
                                it.setData(0, ROLE, ('question', q['id'], m['cle']))
                                it.setData(0, ROLE_TITRE, titre)
                                if est_favori('question', q['id']):
                                    it.setIcon(0, icone_etoile(True))
                                if not q['ok']:
                                    it.setDisabled(True)
                                r.addChild(it)
                    else:
                        for i in ids:
                            titre = contenu.titre(g, i)
                            it = QTreeWidgetItem([titre])
                            it.setData(0, ROLE, (g, i, m['cle']))
                            it.setData(0, ROLE_TITRE, titre)
                            if est_favori(g, i):
                                it.setIcon(0, icone_etoile(True))
                            r.addChild(it)
                    r.setExpanded(True)
                w.itemActivated.connect(lambda it, *_: self._ouvrir_arbre(it))
                w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                w.customContextMenuRequested.connect(lambda pos, w=w: self._menu(w, pos))
                QShortcut(QKeySequence('Ctrl+D'), w, lambda w=w: self._basculer(w.currentItem()))
            self.onglets.addTab(w, '%s (%d)' % (tr('classe_onglet_' + o), self.total(o)))
        self.onglets.setCurrentIndex(self.ONGLETS.index(onglet) if onglet in self.ONGLETS else 0)
        self.onglets.blockSignals(False)
        self._maj_affichage()
        if self._file:
            self._minuteur.start()

    def _maj_affichage(self):
        o = self.ONGLETS[max(0, self.onglets.currentIndex())]
        quoi = tr('classe_affichage_favoris' if self.fav.isChecked() else 'classe_affichage_tout')
        if self.module.currentData():
            quoi += ' · ' + self.module.currentText()
        self.affichage.setText(tr('classe_affichage', quoi=quoi, n=self.total(o)))

    def _ouvrir_arbre(self, it):
        d = it.data(0, ROLE)
        if not d:
            return
        g, i, mod = d
        if g == 'question':
            self.vue.aller_question(mod, i, False)
        else:
            self.vue.ouvrir_ressource(g, i)

    def _donnees(self, it):
        if it is None:
            return None
        d = it.data(0, ROLE) if isinstance(it, QTreeWidgetItem) else it.data(ROLE)
        if not d:
            return None
        titre = it.data(0, ROLE_TITRE) if isinstance(it, QTreeWidgetItem) else it.data(ROLE_TITRE)
        return d[0], d[1], titre

    def _basculer(self, it):
        d = self._donnees(it)
        if d:
            basculer_favori(d[0], d[1], d[2], self.vue.annoncer)
            self.remplir()

    def _menu(self, w, pos):
        d = self._donnees(w.itemAt(pos))
        if not d:
            return
        m = menu_ajouter(self, d[0], d[1], d[2], apres=self.remplir, annoncer=self.vue.annoncer)
        m.triggered.connect(lambda *_: QTimer.singleShot(0, self.remplir))
        m.exec(w.viewport().mapToGlobal(pos))

    def _vignette_suivante(self):
        """Une vignette par battement, d'abord celles de l'onglet visible (image : photo ou schéma ; animation :
        dessinée par l'animation elle-même) ; sans onglet visible, on attend (repris au changement d'onglet)."""
        def visible(w):
            try:
                return w.isVisible()
            except RuntimeError:
                return False
        self._file = [x for x in self._file if not _detruit(x[0])]
        k = next((n for n, x in enumerate(self._file) if visible(x[0])), None)
        if k is None:
            self._minuteur.stop()
            return
        w, it, g, i = self._file.pop(k)
        icone = _VIGNETTES.get((g, i)) or vignette(g, i)
        if icone is not None:
            _VIGNETTES[(g, i)] = icone
            try:
                it.setIcon(icone)
            except RuntimeError:
                pass

    def showEvent(self, ev):
        super().showEvent(ev)
        if self._file:
            self._minuteur.start()


def _detruit(w) -> bool:
    try:
        w.objectName()
        return False
    except RuntimeError:
        return True


def vignette(g: str, i: str):
    """Vignette 176 × 112 d'une image (photo ou schéma) ou d'une animation (état de départ, thème courant)."""
    from PyQt6.QtGui import QImage, QPainter, QPixmap
    try:
        if g == 'animation':
            e = catalogue.PAR_ID[i]
            a = e.charger()()
            a.en_lecture = False
            img = a.image(352, 224)
            a.deleteLater()
            return QIcon(QPixmap.fromImage(img).scaled(176, 112, Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation))
        o = contenu.image(i)
        if o is None:
            return None
        if o.get('nature') == 'photo':
            pm = QPixmap(str(contenu.chemin_image(i)))
            if pm.isNull():
                return None
            return QIcon(pm.scaled(176, 112, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        if o.get('schemas') and contenu.schema(o['schemas'][0]):
            from .schema_qt import peindre
            img = QImage(352, 224, QImage.Format.Format_ARGB32_Premultiplied)
            img.fill(Qt.GlobalColor.transparent)
            p = QPainter(img)
            try:
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                peindre(p, contenu.schema(o['schemas'][0]), QRectF(0, 0, 352, 224), theme_courant())
            finally:
                p.end()
            return QIcon(QPixmap.fromImage(img).scaled(176, 112, Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation))
    except Exception:                                  # une vignette ratée n'empêche rien
        import logging
        logging.getLogger(__name__).debug('vignette %s %s', g, i, exc_info=True)
    return None


class PageMesModules(QWidget):
    def __init__(self, vue):
        super().__init__()
        self.vue = vue
        v = QVBoxLayout(self)
        v.addWidget(_titre(tr('classe_mes_modules')))
        t = QLabel(tr('classe_mes_modules_texte'))
        t.setWordWrap(True)
        v.addWidget(t)
        h = QHBoxLayout()
        b = QPushButton('+ ' + tr('classe_creer_module'))
        b.clicked.connect(vue.creer_module)
        h.addWidget(b)
        h.addStretch(1)
        v.addLayout(h)
        self.liste = QListWidget()
        self.liste.setAccessibleName(tr('classe_mes_modules'))
        self.liste.itemActivated.connect(lambda it: it.data(ROLE) and vue.aller_module(it.data(ROLE), True))
        self.liste.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.liste.customContextMenuRequested.connect(self._menu)
        v.addWidget(self.liste, 1)
        self.remplir()

    def remplir(self):
        self.liste.clear()
        s = stockage().doc
        if not s['mes_modules']:
            it = QListWidgetItem(tr('classe_mes_modules_vide'))
            it.setFlags(Qt.ItemFlag.NoItemFlags)
            self.liste.addItem(it)
        for m in s['mes_modules']:
            it = QListWidgetItem('%s  —  %s' % (m['nom'], tr('classe_n_elements', n=len(m['elements']))))
            it.setData(ROLE, m['id'])
            self.liste.addItem(it)

    def _menu(self, pos):
        it = self.liste.itemAt(pos)
        if it is None or not it.data(ROLE):
            return
        s = stockage().doc
        mm = S.trouver_module(s, it.data(ROLE))
        m = QMenu(self)

        def renommer():
            v, ok = QInputDialog.getText(self, tr('classe_renommer_module'), tr('classe_renommer_module'), text=mm['nom'])
            if ok and S.renommer_module(s, mm['id'], v):
                stockage().modifie()
                self.remplir()

        def copier():
            S.creer_module(s, S.nom_libre(s, tr('classe_copie_de', nom=mm['nom'])), mm['elements'])
            stockage().modifie()
            self.remplir()

        def supprimer():
            k = s['mes_modules'].index(mm)
            S.supprimer_module(s, mm['id'])
            stockage().modifie()
            self.remplir()
            self.vue.annoncer(tr('classe_module_supprime', nom=mm['nom']), lambda: (s['mes_modules'].insert(k, mm), stockage().modifie(), self.remplir()))
        m.addAction(tr('classe_renommer')).triggered.connect(renommer)
        m.addAction(tr('classe_copier')).triggered.connect(copier)
        m.addAction(tr('classe_supprimer')).triggered.connect(supprimer)
        m.exec(self.liste.viewport().mapToGlobal(pos))


class PageProgression(QWidget):
    def __init__(self, vue):
        super().__init__()
        self.vue = vue
        zone = QScrollArea(self)
        zone.setWidgetResizable(True)
        corps = QWidget()
        v = QVBoxLayout(corps)
        zone.setWidget(corps)
        QVBoxLayout(self).addWidget(zone)
        s = stockage().doc
        v.addWidget(_titre(tr('classe_ma_progression')))
        info = contenu.info_questions()
        toutes = [i for i, x in info.items() if x['ok']]
        b = S.bilan(s, toutes)
        v.addWidget(QLabel('  ·  '.join('%s : <b>%s</b>' % (tr(k), val) for k, val in (
            ('classe_essayees', '%d / %d' % (b['essayees'], b['total'])), ('classe_reussies', b['reussies']),
            ('classe_ratees', b['ratees']), ('classe_a_revoir', b['a_revoir']), ('classe_premier_coup', b['premier_coup']),
            ('classe_tentatives', b['tentatives'])))))
        v.addWidget(_titre(tr('classe_par_module'), 1.1))
        mods = [m for m in contenu.modules() if any(q['ok'] for q in m['questions'])]
        tab = QTableWidget(len(mods), 4)
        tab.setHorizontalHeaderLabels([tr('classe_module'), tr('classe_reussies'), tr('classe_ratees'), tr('classe_score')])
        tab.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tab.setAccessibleName(tr('classe_par_module'))
        for k, m in enumerate(mods):
            x = S.bilan(s, [q['id'] for q in m['questions'] if q['ok']])
            for j, val in enumerate((bi(m['titre']), x['reussies'], x['ratees'], ('%d\u202f%%' % x['score']) if x['essayees'] else '—')):
                it = QTableWidgetItem(str(val))
                if j:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tab.setItem(k, j, it)
        tab.resizeColumnsToContents()
        tab.verticalHeader().setVisible(False)
        tab.setAlternatingRowColors(True)
        tab.setShowGrid(False)
        tab.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # toute la table d'un bloc : la page défile, pas un second ascenseur dans la table
        tab.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tab.setFixedHeight(tab.horizontalHeader().sizeHint().height() + sum(tab.rowHeight(r) for r in range(len(mods))) + 4)
        tab.cellDoubleClicked.connect(lambda r, _c: vue.aller_module(mods[r]['cle'], False))
        v.addWidget(tab)
        v.addWidget(_titre(tr('classe_a_revoir_titre'), 1.1))
        rev = QListWidget()
        for i in toutes:
            e = S.etat_question(s, i)
            if (s['questions'].get(i) or {}).get('a_revoir') or e == 'ratee':
                it = QListWidgetItem('%s %s — %s · %s' % (SYMBOLES.get(e, '⚑'), bi(info[i]['t']), bi(contenu.module(info[i]['module'])['titre']), info[i]['n']))
                it.setData(ROLE, (info[i]['module'], i))
                rev.addItem(it)
        if not rev.count():
            rev.addItem(QListWidgetItem(tr('classe_rien_a_revoir')))
        rev.itemActivated.connect(lambda it: it.data(ROLE) and vue.aller_question(it.data(ROLE)[0], it.data(ROLE)[1], False))
        rev.setMaximumHeight(200)
        v.addWidget(rev)
        v.addWidget(_titre(tr('classe_sauvegarde'), 1.1))
        lab = QLabel(tr('classe_sauvegarde_texte', chemin=str(stockage().chemin)) +
                     ('<br><b>%s</b>' % _html.escape(tr('classe_sauvegarde_future')) if stockage().lecture_seule else ''))
        lab.setWordWrap(True)
        lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(lab)
        h = QHBoxLayout()
        b1 = QPushButton(tr('classe_exporter'))
        b1.clicked.connect(self.exporter)
        h.addWidget(b1)
        self.mode = QComboBox()
        self.mode.addItem(tr('classe_import_fusionner'), 'fusionner')
        self.mode.addItem(tr('classe_import_remplacer'), 'remplacer')
        self.mode.setAccessibleName(tr('classe_import_mode'))
        h.addWidget(QLabel(tr('classe_import_mode')))
        h.addWidget(self.mode)
        b2 = QPushButton(tr('classe_importer'))
        b2.clicked.connect(self.importer)
        h.addWidget(b2)
        h.addStretch(1)
        v.addLayout(h)
        h2 = QHBoxLayout()
        self.partie = QComboBox()
        self.partie.setAccessibleName(tr('classe_raz_quoi'))
        for val, cle in (('reponses', 'classe_raz_reponses'), ('reglages', 'classe_raz_reglages'), ('favoris', 'classe_raz_favoris'), ('mes_modules', 'classe_raz_mes_modules'),
                         ('preferences', 'classe_raz_preferences'), ('tout', 'classe_raz_tout')):
            self.partie.addItem(tr(cle), val)
        for m in mods:
            self.partie.addItem(tr('classe_raz_module', nom=bi(m['titre'])), 'module:' + m['cle'])
        for i in s['animations']:
            if i in catalogue.PAR_ID:
                self.partie.addItem(tr('classe_raz_animation', nom=tr('anim_nom_' + catalogue.PAR_ID[i].cle)), 'animation:' + i)
        h2.addWidget(QLabel(tr('classe_raz_quoi')))
        h2.addWidget(self.partie)
        b3 = QPushButton(tr('classe_reinitialiser'))
        b3.clicked.connect(self.raz)
        h2.addWidget(b3)
        h2.addStretch(1)
        v.addLayout(h2)
        v.addStretch(1)

    def exporter(self):
        from ....gui import fichiers
        ch, _ = fichiers.choisir_enregistrement(self, tr('classe_exporter'), stockage().nom_export(), 'JSON (*.json)')
        if ch:
            stockage().exporter_vers(ch)
            self.vue.annoncer(tr('classe_exporte', chemin=ch))

    def importer(self):
        from ....gui import fichiers
        ch, _ = fichiers.choisir_fichier(self, tr('classe_importer'), '', 'JSON (*.json)')
        if ch:
            self.vue.importer_fichier(ch, self.mode.currentData())

    def raz(self):
        v = self.partie.currentData()
        if v.startswith('module:'):
            m = contenu.module(v[7:])
            p = {'partie': 'module', 'id': m['cle'], 'questions': [q['id'] for q in m['questions']]}
        elif v.startswith('animation:'):
            p = {'partie': 'animation', 'id': v[10:]}
        else:
            p = {'partie': v}
        self.vue.effacer(p, self.partie.currentText() + ' ?')


# ================================================================== vue d'ensemble (fil d'Ariane, pages)
class VueClasse(QWidget):
    """Pages des modules dans le panneau « Animations » ; `panneau` sert à ouvrir une animation."""
    ouvrir_animation = pyqtSignal(str)

    def __init__(self, panneau=None, parent=None):
        super().__init__(parent)
        self.panneau = panneau
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        barre = QHBoxLayout()
        self.b_retour = QToolButton()
        self.b_retour.setArrowType(Qt.ArrowType.LeftArrow)
        self.b_retour.setToolTip(tr('classe_precedent'))
        self.b_retour.setAccessibleName(tr('classe_precedent'))
        self.b_retour.clicked.connect(self.retour)
        barre.addWidget(self.b_retour)
        self.fil = QLabel('')
        self.fil.setTextFormat(Qt.TextFormat.RichText)
        self.fil.setAccessibleName(tr('classe_fil'))
        self.fil.linkActivated.connect(self._lien)
        barre.addWidget(self.fil, 1)
        self.recherche = QLineEdit()
        self.recherche.setPlaceholderText(tr('classe_recherche_indice'))
        self.recherche.setClearButtonEnabled(True)
        self.recherche.setAccessibleName(tr('classe_recherche_titre'))
        self.recherche.returnPressed.connect(lambda: self.aller_recherche(self.recherche.text()))
        self.recherche.setMaximumWidth(340)
        barre.addWidget(self.recherche)
        v.addLayout(barre)
        self.annonce = QLabel('')
        self.annonce.setVisible(False)
        self.annonce.setTextFormat(Qt.TextFormat.RichText)
        self.annonce.linkActivated.connect(lambda *_: self._annuler())
        v.addWidget(self.annonce)
        self.pile = QStackedWidget()
        v.addWidget(self.pile, 1)
        bulles(self)
        self.histoire = []
        self.courante = None
        self._annulation = None
        self.aller_accueil()

    # ------------------------------------------------------------ navigation
    def _montrer(self, page, fil: list, cle):
        if self.courante is not None:
            self.histoire.append(self.courante)
            del self.histoire[:-20]
        self._poser(page, fil, cle)

    def _poser(self, page, fil, cle):
        apercu().cacher()
        ancienne = self.pile.currentWidget()
        self.pile.addWidget(page)
        self.pile.setCurrentWidget(page)
        if ancienne is not None:
            self.pile.removeWidget(ancienne)
            ancienne.deleteLater()
        self.courante = cle
        self._fil = fil
        self.maj_fil()
        bulles(page)
        self.b_retour.setEnabled(bool(self.histoire))

    def maj_fil(self):
        morceaux = []
        for t, lien in self._fil:
            morceaux.append('<a href="%s">%s</a>' % (lien, _html.escape(t)) if lien else '<b>%s</b>' % _html.escape(t))
        self.fil.setText(' › '.join(morceaux))

    def _lien(self, lien: str):
        g, _, x = lien.partition(':')
        if g == 'accueil':
            self.aller_accueil()
        elif g == 'm':
            self.aller_module(x, False)
        elif g == 'mm':
            self.aller_module(x, True)
        elif g == 'mes':
            self.aller_mes_modules()
        elif g == 'favoris':
            self.aller_favoris()
        elif g == 'bibliotheque':
            self.aller_bibliotheque()

    def retour(self):
        if not self.histoire:
            return
        cle = self.histoire.pop()
        self.courante = None
        g = cle[0]
        if g == 'accueil':
            self._poser(PageAccueil(self), [(tr('classe_accueil'), '')], cle)
        elif g == 'module':
            self._aller_module(*cle[1:], pousser=False)
        elif g == 'question':
            self._aller_question(*cle[1:], pousser=False)
        else:
            {'mes': self.aller_mes_modules, 'progression': self.aller_progression, 'favoris': self.aller_favoris,
             'bibliotheque': self.aller_bibliotheque}.get(g, self.aller_accueil)()
        self.b_retour.setEnabled(bool(self.histoire))

    def aller_accueil(self):
        self._montrer(PageAccueil(self), [(tr('classe_accueil'), '')], ('accueil',))

    def aller_module(self, cle, perso, onglet='questions'):
        self._aller_module(cle, perso, onglet)

    def _aller_module(self, cle, perso, onglet='questions', pousser=True):
        if (perso and not S.trouver_module(stockage().doc, cle)) or (not perso and not contenu.module(cle)):
            return self.aller_accueil()
        page = PageModule(self, cle, perso, onglet)
        fil = [(tr('classe_accueil'), 'accueil:')] + ([(tr('classe_favoris'), 'favoris:'), (tr('classe_mes_modules'), 'mes:')] if perso else []) + [(page.titre.text(), '')]
        (self._montrer if pousser else self._poser)(page, fil, ('module', cle, perso, onglet))

    def aller_question(self, cle, qid, perso):
        self._aller_question(cle, qid, perso)

    def _aller_question(self, cle, qid, perso, pousser=True):
        if not contenu.question(qid):
            return
        page = PageQuestion(self, cle, qid, perso)
        nom = S.trouver_module(stockage().doc, cle)['nom'] if perso else bi(contenu.module(cle)['titre'])
        fil = [(tr('classe_accueil'), 'accueil:'), (nom, ('mm:' if perso else 'm:') + cle), ('%s %s' % (page.info['n'], bi(page.q['titre'])), '')]
        (self._montrer if pousser else self._poser)(page, fil, ('question', cle, qid, perso))

    def aller_recherche(self, q=''):
        self._montrer(PageRecherche(self, q), [(tr('classe_accueil'), 'accueil:'), (tr('classe_recherche_titre'), '')], ('recherche',))

    def aller_mes_modules(self):
        self._montrer(PageMesModules(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_favoris'), 'favoris:'),
                                             (tr('classe_mes_modules'), '')], ('mes',))

    def aller_favoris(self):
        self._montrer(PageFavoris(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_favoris'), '')], ('favoris',))

    def aller_bibliotheque(self, onglet='questions', module='', favoris=False):
        self._montrer(PageBibliotheque(self, onglet, module, favoris), [(tr('classe_accueil'), 'accueil:'), (tr('classe_bibliotheque'), '')],
                      ('bibliotheque',))

    def aller_progression(self):
        self._montrer(PageProgression(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_ma_progression'), '')], ('progression',))

    def rafraichir(self):
        """Page courante reconstruite (après import ou réinitialisation)."""
        cle = self.courante
        self.courante = None
        if cle is None or cle[0] == 'accueil':
            self._poser(PageAccueil(self), [(tr('classe_accueil'), '')], ('accueil',))
        elif cle[0] == 'module':
            self._aller_module(*cle[1:], pousser=False)
        elif cle[0] == 'question':
            self._aller_question(*cle[1:], pousser=False)
        elif cle[0] == 'progression':
            self._poser(PageProgression(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_ma_progression'), '')], cle)
        elif cle[0] == 'mes':
            self._poser(PageMesModules(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_favoris'), 'favoris:'),
                                               (tr('classe_mes_modules'), '')], cle)
        elif cle[0] == 'favoris':
            self._poser(PageFavoris(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_favoris'), '')], cle)
        elif cle[0] == 'bibliotheque':
            self._poser(PageBibliotheque(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_bibliotheque'), '')], cle)
        else:
            self.aller_accueil()

    def ouvrir_ressource(self, genre, i):
        apercu().cacher()
        if genre == 'animation':
            self.ouvrir_animation.emit(i)
        elif genre == 'question':
            info = contenu.info_questions().get(i)
            if info:
                self.aller_question(info['module'], i, False)
        else:
            ouvrir_ressource(genre, i)

    def creer_module(self):
        s = stockage().doc
        v, ok = QInputDialog.getText(self, tr('classe_creer_module'), tr('classe_nom_nouveau_module'),
                                     text=S.nom_libre(s, tr('classe_nouveau_module'), True))
        if ok and v.strip():
            m = S.creer_module(s, v.strip())
            stockage().modifie()
            self.aller_module(m['id'], True)

    def basculer_plein_ecran(self):
        f = self.window()
        f.showNormal() if f.isFullScreen() else f.showFullScreen()

    # ------------------------------------------------------------ annonces et sauvegarde
    def annoncer(self, texte: str, annuler=None, duree_ms=10000):
        self._annulation = annuler
        self.annonce.setText(_html.escape(texte) + (' — <a href="annuler">%s</a>' % _html.escape(tr('classe_defaire')) if annuler else ''))
        self.annonce.setVisible(True)
        self.annonce.setAccessibleName(texte)
        # minuterie enfant de la vue : détruite avec elle (une lambda survivait à un changement de langue et visait une
        # étiquette détruite, 0.7.0)
        if not hasattr(self, '_minuterie_annonce'):
            self._minuterie_annonce = QTimer(self)
            self._minuterie_annonce.setSingleShot(True)
            self._minuterie_annonce.timeout.connect(self._cacher_annonce)   # méthode liée : déconnectée à la destruction
        self._minuterie_annonce.start(duree_ms)

    def _cacher_annonce(self):
        self.annonce.setVisible(False)

    def _annuler(self):
        f, self._annulation = self._annulation, None
        self.annonce.setVisible(False)
        if f:
            f()
            self.rafraichir()

    def copie_avant(self, suffixe: str) -> str:
        """Copie de la sauvegarde dans le dossier de configuration (sauvegardes/), avant effacement ou remplacement."""
        from ....core import config
        d = config.dossier_config() / 'sauvegardes'
        d.mkdir(parents=True, exist_ok=True)
        ch = d / stockage().nom_export(suffixe)
        stockage().exporter_vers(ch)
        return str(ch)

    def effacer(self, partie: dict, titre: str) -> bool:
        boite = QMessageBox(QMessageBox.Icon.Warning, titre, tr('classe_effacer_texte'),
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, self)
        # la case appartient à la boîte (parent Qt) : sans parent, Python la détruirait à la sortie de la fonction et
        # la boîte garderait un pointeur vers elle (plantage au changement de thème suivant) ; la boîte est détruite
        # aussitôt lue.
        case = QCheckBox(tr('classe_exporter_avant'), boite)
        case.setChecked(True)
        boite.setCheckBox(case)
        boite.button(QMessageBox.StandardButton.Yes).setText(tr('classe_effacer'))
        oui = boite.exec() == QMessageBox.StandardButton.Yes
        exporter = case.isChecked()
        boite.deleteLater()
        if not oui:
            return False
        copie = self.copie_avant('-avant-effacement') if exporter else None
        avant = S.migrer(S._clone(stockage().doc) if hasattr(S, '_clone') else stockage().doc)
        stockage().remplacer(S.reinitialiser(stockage().doc, partie))
        self._appliquer_preferences()
        self.annoncer(tr('classe_efface') + (' ' + tr('classe_copie_gardee', chemin=copie) if copie else ''),
                      lambda: (stockage().remplacer(avant), self._appliquer_preferences()))
        self.rafraichir()
        return True

    def importer_fichier(self, chemin: str, mode: str) -> bool:
        try:
            texte = open(chemin, encoding='utf-8').read()
        except OSError:
            texte = ''
        imp = S.importer(texte, stockage().doc.get('application', ''))
        if imp is None:
            QMessageBox.warning(self, tr('classe_importer'), tr('classe_import_illisible'))
            return False
        avant = S.migrer(S._clone(stockage().doc) if hasattr(S, '_clone') else stockage().doc)
        if mode == 'remplacer':
            self.copie_avant('-avant-import')
            stockage().remplacer(imp)
        else:
            stockage().remplacer(S.fusionner(stockage().doc, imp))
        self._appliquer_preferences()
        self.annoncer(tr('classe_importe', q=len(imp['questions']), a=len(imp['animations']), f=len(imp.get('favoris', [])),
                         m=len(imp['mes_modules'])),
                      lambda: (stockage().remplacer(avant), self._appliquer_preferences()))
        self.rafraichir()
        return True

    def _appliquer_preferences(self):
        if self.panneau is not None and hasattr(self.panneau, 'appliquer_sauvegarde'):
            self.panneau.appliquer_sauvegarde()
