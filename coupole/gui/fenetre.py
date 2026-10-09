"""Fenêtre principale : barre latérale des modules, menus, aide, barre d'état."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QKeySequence
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
                             QStackedWidget, QWidget)

from .. import __version__
from ..core import config, i18n, modules
from ..core.i18n import tr
from . import adaptatif, dialogues, memoire, plateforme, theme
from .outils import action, aide
from .ressources import icone_application


class FenetrePrincipale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(icone_application())
        adaptatif.ajuster(self, 1400, 900)
        self.setMinimumSize(adaptatif.TAILLE_MIN.boundedTo(adaptatif.zone_utile(self)))
        self.panneaux = []
        self.construire()
        # taille, position, écran et état maximisé de la dernière fois (garde-fous : écran disparu, position hors
        # des écrans → fenêtre recentrée ; taille bornée à l'écran, comme adaptatif.ajuster)
        from ..core.etat_interface import etat
        self.placement = memoire.placer(self, etat().lire('fenetre.geometrie', None, dict),
                                        adaptatif.TAILLE_MIN)

    # ---------------------------------------------------------------- construction (et reconstruction : langue)
    def construire(self, capturer: bool = True):
        """(Re)construit menus et panneaux.  `capturer` : l'état des panneaux actuels (filtres, colonnes…) est
        relu avant d'être rétabli dans les nouveaux (changement de langue) ; False après une réinitialisation."""
        m = memoire.memoire()
        if capturer:
            m.capturer()
        m.oublier_sources()
        self.setWindowTitle('Coupole %s' % __version__)
        self.menuBar().clear()
        central = QWidget()
        h = QHBoxLayout(central)
        h.setContentsMargins(4, 4, 4, 4)
        self.barre = aide(QListWidget(), 'fen_modules_aide')
        self.barre.setObjectName('barreModules')
        self.barre.setIconSize(QSize(40, 40))
        self.barre.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.barre.setWordWrap(True)
        self.barre.setSpacing(2)
        self.pile = QStackedWidget()
        h.addWidget(self.barre)
        h.addWidget(self.pile, 1)
        self.setCentralWidget(central)
        for p in self.panneaux:
            if hasattr(p, 'arreter'):
                p.arreter()
        self.panneaux = []
        for mod in modules.decouvrir():
            try:
                classe = mod.classe_gui()
                if classe is None:
                    continue
                panneau = classe(self)
            except Exception as e:  # un module défectueux ne bloque pas l'application
                panneau = QLabel(tr('fen_module_erreur', module=mod.nom_local(), erreur=str(e)))
                panneau.setWordWrap(True)
            panneau.module = mod
            it = QListWidgetItem(mod.nom_local())
            ic = mod.chemin_icone()
            if ic is not None and ic.exists():
                it.setIcon(QIcon(str(ic)))
            it.setToolTip('%s\n%s' % (mod.nom_local(), mod.description_locale()))  # nom visible aussi en barre compacte
            self.barre.addItem(it)
            adaptatif.assouplir(panneau)
            self.pile.addWidget(adaptatif.defilable(panneau))
            self.panneaux.append(panneau)
        self.barre.currentRowChanged.connect(self.pile.setCurrentIndex)
        self.barre.setCurrentRow(0)
        self._suivre_disposition()
        self._menus()
        self._largeur_barre()
        self.statusBar().showMessage(tr('fen_pret'))

    # ---------------------------------------------------------------- disposition gardée (gui/memoire.py)
    def _suivre_disposition(self):
        """Module affiché et géométrie de la fenêtre : rétablis, puis relus à chaque écriture différée."""
        from ..core.etat_interface import etat
        m = memoire.memoire()
        ident = etat().lire('fenetre.module', '', str)
        for i, p in enumerate(self.panneaux):
            if ident and getattr(getattr(p, 'module', None), 'id', '') == ident:
                self.barre.setCurrentRow(i)
                break

        def module():
            p = self.panneau_courant()
            return getattr(getattr(p, 'module', None), 'id', None) if p is not None else None
        m.suivre('fenetre.module', module, self.barre, self.barre.currentRowChanged)
        m.suivre('fenetre.geometrie', lambda: memoire.geometrie_fenetre(self), self)

    def moveEvent(self, ev):
        super().moveEvent(ev)
        memoire.memoire().signaler()

    def changeEvent(self, ev):
        super().changeEvent(ev)
        from PyQt6.QtCore import QEvent
        if ev.type() == QEvent.Type.WindowStateChange:
            memoire.memoire().signaler()

    def reinitialiser_disposition(self):
        """Préférences > « Réinitialiser la disposition » : tout revient à l'origine, tout de suite si possible."""
        m = memoire.memoire()
        if any(getattr(p, 'occupe', lambda: False)() for p in self.panneaux):
            m.reinitialiser()
            m.suspendue = True                      # rien ne sera réécrit : l'origine reviendra au prochain lancement
            QMessageBox.information(self, tr('reg_disposition'), tr('fen_disposition_plus_tard'))
            return
        m.reinitialiser()
        self.showNormal()
        adaptatif.ajuster(self, 1400, 900)
        self.construire(capturer=False)
        self.statusBar().showMessage(tr('fen_disposition_reinitialisee'), 6000)

    # ---------------------------------------------------------------- barre des modules adaptative
    SEUIL_COMPACT = 1100                 # en dessous (pixels logiques), la barre ne garde que les icônes

    def _largeur_barre(self):
        fm = self.barre.fontMetrics()
        icone = self.barre.iconSize().width()
        compacte = self.width() < self.SEUIL_COMPACT
        if compacte:
            largeur = icone + 30
        else:
            textes = [self.barre.item(i).data(Qt.ItemDataRole.UserRole) or self.barre.item(i).text()
                      for i in range(self.barre.count())]
            largeur = icone + 46 + max((fm.horizontalAdvance(s) for s in textes), default=80)
            largeur = min(largeur, max(icone + 30, self.width() // 4))
        for i in range(self.barre.count()):
            it = self.barre.item(i)
            if it.data(Qt.ItemDataRole.UserRole) is None:
                it.setData(Qt.ItemDataRole.UserRole, it.text())
            it.setText('' if compacte else it.data(Qt.ItemDataRole.UserRole))
        self.barre.setFixedWidth(largeur)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if hasattr(self, 'barre'):
            self._largeur_barre()
        memoire.memoire().signaler()

    def _menus(self):
        mb = self.menuBar()
        m = mb.addMenu(tr('menu_fichier'))
        a = action(self, 'act_reglages', self.reglages, QKeySequence('Ctrl+,'))
        a.setMenuRole(QAction.MenuRole.PreferencesRole)      # macOS : menu de l'application, Cmd+,
        m.addAction(a)
        m.addSeparator()
        a = action(self, 'act_quitter', self.close, QKeySequence('Ctrl+Q'))
        a.setMenuRole(QAction.MenuRole.QuitRole)
        m.addAction(a)
        m = mb.addMenu(tr('menu_affichage'))
        for i, mod in enumerate(modules.decouvrir()[:9]):
            a = action(self, 'act_module', lambda _=False, k=i: self.barre.setCurrentRow(k),
                       QKeySequence('Ctrl+%d' % (i + 1)), cle_aide='act_module_aide')
            a.setText(mod.nom_local())
            m.addAction(a)
        m.addSeparator()
        # Apparence : le thème sombre (défaut) ou clair, propre à Coupole ; même réglage que les Préférences.
        sm = self.menu_apparence = m.addMenu(tr('menu_apparence'))
        aide(sm.menuAction(), 'menu_apparence_aide')
        groupe = QActionGroup(self)
        groupe.setExclusive(True)
        self.act_apparence = {}
        for nom, cle in (('clair', 'act_apparence_clair'), ('sombre', 'act_apparence_sombre')):
            a = action(self, cle, lambda _=False, n=nom: self.changer_apparence(n), cle_aide='act_apparence_aide')
            a.setCheckable(True)
            groupe.addAction(a)
            sm.addAction(a)
            self.act_apparence[nom] = a
        sm.addSeparator()
        sm.addAction(action(self, 'act_apparence_basculer', self.basculer_apparence, QKeySequence('Ctrl+Shift+D')))
        self.synchroniser_apparence()
        self._menu_disposition_cosmo(m)
        m = mb.addMenu(tr('menu_langue'))
        for code, nom in (('auto', tr('reg_langue_auto')), ('fr', 'Français'), ('en', 'English')):
            a = action(self, 'act_langue', lambda _=False, c=code: self.changer_langue(c), cle_aide='act_langue_aide')
            a.setText(nom)
            a.setCheckable(True)
            a.setChecked(config.reglages()['langue'] == code)
            m.addAction(a)
        m = mb.addMenu(tr('menu_outils'))
        m.addAction(action(self, 'act_astap', self.astap, QKeySequence('Ctrl+Shift+A')))
        m = mb.addMenu(tr('menu_aide'))
        m.addAction(action(self, 'act_aide_ecran', self.aide_ecran, QKeySequence('F1')))
        m.addAction(action(self, 'act_manuel', self.manuel, QKeySequence('Shift+F1')))
        m.addAction(action(self, 'act_raccourcis', lambda: dialogues.afficher_raccourcis(self)))
        m.addSeparator()
        m.addAction(action(self, 'act_signaler', lambda: dialogues.DialogueSignaler(self).exec()))
        self.act_rapports = action(self, 'act_rapports', self.basculer_rapports)
        self.act_rapports.setCheckable(True)
        from ..core import rapports
        self.act_rapports.setChecked(rapports.consentement() is True)
        m.addAction(self.act_rapports)
        m.addAction(action(self, 'act_maj', lambda: dialogues.verifier_maj(self)))
        m.addSeparator()
        a = action(self, 'act_apropos', lambda: dialogues.DialogueAPropos(self).exec())
        a.setMenuRole(QAction.MenuRole.AboutRole)
        m.addAction(a)

    # ---------------------------------------------------------------- actions
    def panneau_courant(self):
        i = self.pile.currentIndex()
        return self.panneaux[i] if 0 <= i < len(self.panneaux) else None

    def _menu_disposition_cosmo(self, menu):
        """Affichage > Disposition de la Cosmologie : automatique / côte à côte / empilée (même choix que la liste
        du module, synchronisés)."""
        p = self.panneau_module('cosmo')
        if p is None or not hasattr(p, 'definir_disposition'):
            return
        from ..modules.cosmo.gui import DISPOSITIONS
        sm = menu.addMenu(tr('menu_cosmo_disposition'))
        aide(sm.menuAction(), 'cosmo_disposition_aide')
        groupe = QActionGroup(self)
        groupe.setExclusive(True)
        self.act_disposition_cosmo = {}
        for d in DISPOSITIONS:
            cle = 'cosmo_disposition_' + d
            a = action(self, cle, lambda _=False, x=d: p.definir_disposition(x), cle_aide='cosmo_disposition_aide')
            a.setCheckable(True)
            a.setChecked(p.disposition_choisie == d)
            groupe.addAction(a)
            sm.addAction(a)
            self.act_disposition_cosmo[d] = a
        p.disposition_changee.connect(lambda d: self.act_disposition_cosmo[d].setChecked(True))

    def panneau_module(self, ident: str):
        """Panneau du module `ident` (None s'il est absent ou défectueux)."""
        for p in self.panneaux:
            if getattr(getattr(p, 'module', None), 'id', '') == ident:
                return p
        return None

    def ouvrir_module(self, ident: str):
        """Affiche le module `ident` et rend son panneau (liens entre modules : fiche → Cosmologie...)."""
        for i, p in enumerate(self.panneaux):
            if getattr(getattr(p, 'module', None), 'id', '') == ident:
                self.barre.setCurrentRow(i)
                return p
        return None

    def aide_ecran(self):
        p = self.panneau_courant()
        if p is None:
            return
        titre = p.module.nom_local() if hasattr(p, 'module') else 'Coupole'
        texte = p.aide_html() if hasattr(p, 'aide_html') else tr('aide_generale')
        dialogues.afficher_aide(self, titre, texte + tr('aide_dossier_reseau') + tr('aide_ouvrir_avec') +
                                 tr('aide_reglages_conserves'))

    def manuel(self):
        from ..cli import chemin_manuel
        c = chemin_manuel()
        if c:
            dialogues.ouvrir_fichier(c)
        else:
            QMessageBox.information(self, tr('act_manuel'), tr('manuel_absent'))

    def reglages(self):
        d = dialogues.DialogueReglages(self)
        ok = d.exec()
        if ok and getattr(d, 'disposition_reinitialisee', False):
            if getattr(d, 'langue_changee', False):
                i18n.choisir_langue(config.reglages()['langue'])
                plateforme.installer_traductions(QApplication.instance(), i18n.langue())
            self.reinitialiser_disposition()
            return
        if ok and getattr(d, 'langue_changee', False):
            self.changer_langue(config.reglages()['langue'])
        else:
            self.synchroniser_apparence()          # le dialogue a pu changer le thème : le menu suit
            for p in self.panneaux:
                if hasattr(p, 'reglages_changes'):
                    p.reglages_changes()

    # ---------------------------------------------------------------- apparence (menu Affichage, Préférences)
    def changer_apparence(self, nom: str):
        """Applique le thème `nom` tout de suite, l'enregistre, et met le menu d'accord."""
        if nom not in theme.THEMES:
            return
        if config.reglages()['apparence'] != nom:
            config.reglages()['apparence'] = nom      # enregistré : le réglage prime sur le défaut au prochain lancement
        theme.appliquer(nom=nom)
        self.synchroniser_apparence()
        for p in self.panneaux:                      # courbes et carte dessinées avec les couleurs du thème
            if hasattr(p, 'reglages_changes'):
                p.reglages_changes()
        self.statusBar().showMessage(tr('apparence_appliquee', nom=tr('reg_apparence_' + nom)), 4000)

    def basculer_apparence(self):
        self.changer_apparence('clair' if config.reglages()['apparence'] == 'sombre' else 'sombre')

    def synchroniser_apparence(self):
        """Coche l'entrée du thème en vigueur (après les Préférences, un raccourci, ou à la construction)."""
        courant = config.reglages()['apparence']
        for nom, a in getattr(self, 'act_apparence', {}).items():
            a.setChecked(nom == courant)

    def astap(self):
        dialogues.DialogueASTAP(self).exec()
        for p in self.panneaux:
            if hasattr(p, 'reglages_changes'):
                p.reglages_changes()

    def basculer_rapports(self, coche):
        from ..core import rapports
        rapports.definir_consentement(bool(coche))
        self.statusBar().showMessage(tr('rapports_etat_' + ('oui' if coche else 'non')), 6000)

    def changer_langue(self, code):
        if any(getattr(p, 'occupe', lambda: False)() for p in self.panneaux):
            QMessageBox.information(self, tr('menu_langue'), tr('fen_langue_occupe'))
            return
        config.reglages()['langue'] = code
        i18n.choisir_langue(code)
        plateforme.installer_traductions(QApplication.instance(), i18n.langue())   # textes fournis par Qt
        idx = self.pile.currentIndex()
        self.construire()
        self.barre.setCurrentRow(max(0, idx))

    def closeEvent(self, ev):
        if any(getattr(p, 'occupe', lambda: False)() for p in self.panneaux):
            if QMessageBox.question(self, tr('fen_quitter_titre'), tr('fen_quitter_occupe')) != \
                    QMessageBox.StandardButton.Yes:
                ev.ignore()
                return
        self.statusBar().showMessage(tr('fen_arret_en_cours'))
        try:
            memoire.memoire().ecrire()                # disposition et réglages différés : écrits avant l'arrêt
        except Exception:
            pass
        for p in self.panneaux:
            if hasattr(p, 'arreter'):
                try:
                    p.arreter()                       # lève l'événement d'arrêt du panneau et attend son fil
                except Exception:
                    pass
        from .outils import arreter_tout
        arreter_tout()                                # tous les fils, pools et QThread : arrêtés et attendus
        ev.accept()
