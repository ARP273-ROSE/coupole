"""Fenêtre principale : barre latérale des modules, menus, aide, barre d'état."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QKeySequence
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
                             QStackedWidget, QWidget)

from .. import __version__
from ..core import config, i18n, modules
from ..core.i18n import tr
from . import adaptatif, dialogues
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

    # ---------------------------------------------------------------- construction (et reconstruction : langue)
    def construire(self):
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
        self._menus()
        self._largeur_barre()
        self.statusBar().showMessage(tr('fen_pret'))

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

    def _menus(self):
        mb = self.menuBar()
        m = mb.addMenu(tr('menu_fichier'))
        m.addAction(action(self, 'act_reglages', self.reglages, QKeySequence('Ctrl+,')))
        m.addSeparator()
        m.addAction(action(self, 'act_quitter', self.close, QKeySequence('Ctrl+Q')))
        m = mb.addMenu(tr('menu_affichage'))
        for i, mod in enumerate(modules.decouvrir()[:9]):
            a = action(self, 'act_module', lambda _=False, k=i: self.barre.setCurrentRow(k),
                       QKeySequence('Ctrl+%d' % (i + 1)), cle_aide='act_module_aide')
            a.setText(mod.nom_local())
            m.addAction(a)
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
        m.addAction(action(self, 'act_apropos', lambda: dialogues.DialogueAPropos(self).exec()))

    # ---------------------------------------------------------------- actions
    def panneau_courant(self):
        i = self.pile.currentIndex()
        return self.panneaux[i] if 0 <= i < len(self.panneaux) else None

    def aide_ecran(self):
        p = self.panneau_courant()
        if p is None:
            return
        titre = p.module.nom_local() if hasattr(p, 'module') else 'Coupole'
        texte = p.aide_html() if hasattr(p, 'aide_html') else tr('aide_generale')
        dialogues.afficher_aide(self, titre, texte)

    def manuel(self):
        from ..cli import chemin_manuel
        c = chemin_manuel()
        if c:
            dialogues.ouvrir_fichier(c)
        else:
            QMessageBox.information(self, tr('act_manuel'), tr('manuel_absent'))

    def reglages(self):
        d = dialogues.DialogueReglages(self)
        if d.exec() and getattr(d, 'langue_changee', False):
            self.changer_langue(config.reglages()['langue'])
        else:
            for p in self.panneaux:
                if hasattr(p, 'reglages_changes'):
                    p.reglages_changes()

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
        idx = self.pile.currentIndex()
        self.construire()
        self.barre.setCurrentRow(max(0, idx))

    def closeEvent(self, ev):
        if any(getattr(p, 'occupe', lambda: False)() for p in self.panneaux):
            if QMessageBox.question(self, tr('fen_quitter_titre'), tr('fen_quitter_occupe')) != \
                    QMessageBox.StandardButton.Yes:
                ev.ignore()
                return
        for p in self.panneaux:
            if hasattr(p, 'arreter'):
                p.arreter()
        ev.accept()
