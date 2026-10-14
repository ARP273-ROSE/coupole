"""Navigation par modules au bureau (même organisation que Coupole Web) : accueil (22 modules, bonus, Mes modules,
reprise), page d'un module à onglets (Questions, Animations, Fiches, Tables, Images ; Organiser pour un module
personnel), question (menus « Adapter la question », choix, Valider, Montrer la réponse qui clignote, indice,
explication, ressources liées ★, précédente / suivante W → G → C → D en boucle, plein écran), recherche FR/EN, « Mes
modules », « Ma progression » (sauvegarde : export, import, réinitialisation tout ou partie avec copie et annulation).
Fil d'Ariane en haut ; ressources ouvertes dans des fenêtres séparées ; aperçu au survol."""
from __future__ import annotations

import html as _html
import random

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QCheckBox, QProgressBar, QAbstractButton, QAbstractSpinBox,
                             QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QTabWidget, QTableWidget,
                             QTableWidgetItem, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
                             QInputDialog)

from ....core.i18n import langue, tr
from .. import catalogue
from . import contenu
from . import sauvegarde as S
from .figure_qt import FigureWidget
from .moteur_questions import instancier, variantes
from .ressources_qt import apercu, etiquette, ouvrir_ressource, texte_html, theme_courant, Repliable
from .stockage import stockage

bi = contenu.bi
ROLE = Qt.ItemDataRole.UserRole
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
def menu_ajouter(parent, genre: str, i: str, titre: str, apres=None) -> QMenu:
    s = stockage().doc
    m = QMenu(tr('classe_ajouter_a'), parent)
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
        self.itemEntered.connect(lambda it: apercu().programmer(*it.data(ROLE), self.viewport().mapToGlobal(
            self.visualItemRect(it).bottomLeft())))

    def leaveEvent(self, ev):
        apercu().cacher()
        super().leaveEvent(ev)

    def ajouter(self, genre: str, i: str, texte: str, etoile=False, sous=''):
        it = QListWidgetItem(('★ ' if etoile else '') + texte + ('  —  ' + sous if sous else ''))
        it.setData(ROLE, (genre, i))
        it.setToolTip(tr('classe_ouvrir_aide'))
        self.addItem(it)
        return it

    def _menu(self, pos):
        it = self.itemAt(pos)
        if it is None:
            return
        genre, i = it.data(ROLE)
        if self.retirer:
            m = QMenu(self)
            a = m.addAction(tr('classe_retirer'))
            a.triggered.connect(lambda: self.retirer(genre, i))
        else:
            m = menu_ajouter(self, genre, i, it.text())
        m.exec(self.viewport().mapToGlobal(pos))


# ================================================================== pages
class Carte(QPushButton):
    """Carte d'un module (bouton à deux lignes) : largeur minimale réduite, les cartes passent à la ligne."""

    def minimumSizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(200, 54)

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        h = super().sizeHint()
        return QSize(min(max(h.width(), 260), 380), max(54, h.height()))


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

    def _carte(self, texte: str, rappel, n=None, progres=0, total=0) -> QPushButton:
        b = Carte((('%02d  ' % n if n else '') + texte).replace('&', '&&'))
        b.setMinimumHeight(54)
        b.setStyleSheet('text-align:left; padding:6px 12px;')
        b.setAccessibleName(texte)
        b.setToolTip(texte.split('\n')[0] + ('\n' + tr('classe_progres_texte', r=progres, n=total) if total else ''))
        b.clicked.connect(rappel)
        return b

    def remplir(self):
        _vider(self.grille)
        s = stockage().doc
        for titre_cle, liste in (('classe_modules', [m for m in contenu.modules() if m['affiche']]),
                                 ('classe_modules_bonus', [m for m in contenu.modules() if not m['affiche']])):
            self.grille.addWidget(_titre(tr(titre_cle), 1.15))
            from ....gui.adaptatif import Flux
            g = Flux()
            for k, m in enumerate(liste):
                ids = [q['id'] for q in m['questions'] if q['ok']]
                b = S.bilan(s, ids)
                details = '%d %s · %d %s · %d %s · %d %s · %d %s' % (
                    len(m['questions']), tr('classe_q_court'), len(m['animations']), tr('classe_a_court'),
                    len(m['fiches']), tr('classe_f_court'), len(m['tables']), tr('classe_t_court'), len(m['images']), tr('classe_i_court'))
                carte = self._carte('%s\n%s%s' % (bi(m['titre']), details, ('  ·  ' + tr('classe_progres_texte', r=b['reussies'], n=b['total'])) if b['essayees'] else ''),
                                    lambda _=False, c=m['cle']: self.vue.aller_module(c, False), k + 1 if m['affiche'] else None)
                g.addWidget(carte)
            self.grille.addLayout(g)
        self.grille.addWidget(_titre(tr('classe_mes_modules'), 1.15))
        from ....gui.adaptatif import Flux
        g = Flux()
        for mm in s['mes_modules']:
            g.addWidget(self._carte('%s\n%s' % (mm['nom'], tr('classe_n_elements', n=len(mm['elements']))),
                                    lambda _=False, i=mm['id']: self.vue.aller_module(i, True)))
        g.addWidget(self._carte('+ ' + tr('classe_creer_module'), self.vue.creer_module))
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
        if not perso and self.m['original'] and self.m['original'] != bi(self.m['titre']):
            v.addWidget(QLabel(tr('classe_titre_origine', titre=self.m['original'])))
        self.qs = questions_de(cle, self.mm)
        b = S.bilan(s, [q['id'] for q in self.qs if q['ok']])
        if self.qs:
            barre = QProgressBar()
            barre.setRange(0, max(1, b['total']))
            barre.setValue(b['reussies'])
            barre.setFormat(tr('classe_progres_texte', r=b['reussies'], n=b['total']))
            barre.setAccessibleName(barre.format())
            v.addWidget(barre)
        actions = QHBoxLayout()
        if not perso:
            actions.addWidget(self._bouton('classe_copier_module', self._copier))
        else:
            actions.addWidget(self._bouton('classe_renommer', self._renommer))
            actions.addWidget(self._bouton('classe_copier', self._copier))
            actions.addWidget(self._bouton('classe_supprimer', self._supprimer))
        if self.qs:
            actions.addWidget(self._bouton('classe_reinit_progression', self._raz))
        actions.addStretch(1)
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
            self.onglets.addTab(liste, '%s (%d)' % (tr('classe_onglet_' + g + 's'), len(ids)))
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
            m.addAction(tr('classe_retirer')).triggered.connect(lambda: self._retirer('question', it.data(0, ROLE)))
        else:
            m = menu_ajouter(self, 'question', it.data(0, ROLE), it.text(0))
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
        racine.addWidget(self._liees(), 1)
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
        self.b_ajouter = QToolButton()
        self.b_ajouter.setText('+')
        self.b_ajouter.setToolTip(tr('classe_ajouter_a'))
        self.b_ajouter.setAccessibleName(tr('classe_ajouter_a'))
        self.b_ajouter.clicked.connect(lambda: menu_ajouter(self, 'question', qid, bi(self.q['titre'])).exec(self.b_ajouter.mapToGlobal(QPoint(0, self.b_ajouter.height()))))
        tete.addWidget(self.b_ajouter)
        self.b_plein = QToolButton()
        self.b_plein.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TitleBarMaxButton))
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
            self.fig = FigureWidget(self.inst['figure'], theme_courant(), bi(self.q['figure'].get('alt')) if isinstance(self.q.get('figure'), dict) and self.q['figure'].get('alt') else tr('classe_figure_question'), hauteur_max=420)
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
        self.l_retour.setText('<b style="color:%s">%s</b>' % ('#2e9d63' if juste else '#d0453a', _html.escape(
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
        QTimer.singleShot(200, lambda: self._clignoter(n - 1))

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
        w.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(w)
        v.addWidget(_titre('★ ' + tr('classe_ressources_liees'), 1.05))
        l = contenu.liees(self.qid)
        liste = ListeRessources()
        n = 0
        for g in ('animations', 'fiches', 'tables', 'images'):
            for i, lien in l.get(g, []):
                if g == 'animations' and i not in catalogue.PAR_ID:
                    continue
                liste.ajouter(g[:-1], i, contenu.titre(g[:-1], i), etoile=lien != 'mots-clés',
                              sous=tr('classe_genre_' + g[:-1]) + (' · ' + tr('classe_lien_mots_cles') if lien == 'mots-clés' else ''))
                n += 1
        if not n:
            liste.addItem(QListWidgetItem(tr('classe_aucune_liee')))
        liste.ouvrir.connect(self.vue.ouvrir_ressource)
        v.addWidget(liste, 1)
        if (self.q.get('animation') or {}).get('role'):
            v.addWidget(etiquette(texte_html(bi(self.q['animation']['role']))))
        return w


class PageRecherche(QWidget):
    def __init__(self, vue, q0=''):
        super().__init__()
        self.vue = vue
        v = QVBoxLayout(self)
        v.addWidget(_titre(tr('classe_recherche_titre')))
        self.champ = QLineEdit(q0)
        self.champ.setPlaceholderText(tr('classe_recherche_indice'))
        self.champ.setClearButtonEnabled(True)
        self.champ.setAccessibleName(tr('classe_recherche_titre'))
        v.addWidget(self.champ)
        self.compte = QLabel('')
        v.addWidget(self.compte)
        self.arbre = QTreeWidget()
        self.arbre.setHeaderHidden(True)
        self.arbre.itemActivated.connect(self._ouvrir)
        v.addWidget(self.arbre, 1)
        self.minuteur = QTimer(self)
        self.minuteur.setSingleShot(True)
        self.minuteur.setInterval(150)
        self.minuteur.timeout.connect(self.maj)
        self.champ.textChanged.connect(lambda *_: self.minuteur.start())
        self.maj()

    def maj(self):
        r = contenu.chercher(self.champ.text())
        self.arbre.clear()
        self.compte.setText(tr('classe_n_resultats', n=len(r)) if r else (tr('classe_aucun_resultat', q=self.champ.text()) if self.champ.text().strip() else ''))
        info = contenu.info_questions()
        for g in ('question', 'animation', 'fiche', 'table', 'image'):
            l = [e for e in r if e['g'] == g and (g != 'question' or (e['id'] in info and info[e['id']]['ok']))][:60]
            if not l:
                continue
            racine = QTreeWidgetItem(['%s (%d)' % (tr('classe_onglet_' + g + 's'), len(l))])
            racine.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.arbre.addTopLevelItem(racine)
            for e in l:
                mod = info[e['id']]['module'] if g == 'question' else (e['m'][0] if e['m'] else '')
                nm = bi(contenu.module(mod)['titre']) if mod and contenu.module(mod) else ''
                it = QTreeWidgetItem([bi(e['t']) + ('  —  ' + nm if nm else '')])
                it.setData(0, ROLE, (g, e['id'], mod))
                racine.addChild(it)
            racine.setExpanded(True)

    def _ouvrir(self, it, *_):
        d = it.data(0, ROLE)
        if not d:
            return
        g, i, mod = d
        if g == 'question':
            self.vue.aller_question(mod, i, False)
        else:
            self.vue.ouvrir_ressource(g, i)


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
            for j, val in enumerate((bi(m['titre']), x['reussies'], x['ratees'], ('%d %%' % x['score']) if x['essayees'] else '—')):
                it = QTableWidgetItem(str(val))
                if j:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tab.setItem(k, j, it)
        tab.resizeColumnsToContents()
        tab.horizontalHeader().setStretchLastSection(True)
        tab.setMinimumHeight(min(460, 30 + 26 * len(mods)))
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
        for val, cle in (('reponses', 'classe_raz_reponses'), ('reglages', 'classe_raz_reglages'), ('mes_modules', 'classe_raz_mes_modules'),
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
            {'mes': self.aller_mes_modules, 'progression': self.aller_progression}.get(g, self.aller_accueil)()
        self.b_retour.setEnabled(bool(self.histoire))

    def aller_accueil(self):
        self._montrer(PageAccueil(self), [(tr('classe_accueil'), '')], ('accueil',))

    def aller_module(self, cle, perso, onglet='questions'):
        self._aller_module(cle, perso, onglet)

    def _aller_module(self, cle, perso, onglet='questions', pousser=True):
        if (perso and not S.trouver_module(stockage().doc, cle)) or (not perso and not contenu.module(cle)):
            return self.aller_accueil()
        page = PageModule(self, cle, perso, onglet)
        fil = [(tr('classe_accueil'), 'accueil:')] + ([(tr('classe_mes_modules'), 'mes:')] if perso else []) + [(page.titre.text(), '')]
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
        self._montrer(PageMesModules(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_mes_modules'), '')], ('mes',))

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
            self._poser(PageMesModules(self), [(tr('classe_accueil'), 'accueil:'), (tr('classe_mes_modules'), '')], cle)
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
        QTimer.singleShot(duree_ms, lambda: self.annonce.setVisible(False))

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
        self.annoncer(tr('classe_importe', q=len(imp['questions']), a=len(imp['animations']), m=len(imp['mes_modules'])),
                      lambda: (stockage().remplacer(avant), self._appliquer_preferences()))
        self.rafraichir()
        return True

    def _appliquer_preferences(self):
        if self.panneau is not None and hasattr(self.panneau, 'appliquer_sauvegarde'):
            self.panneau.appliquer_sauvegarde()
