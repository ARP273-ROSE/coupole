"""Panneau « Ma machine » — exemple minimal de module graphique."""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ...core.i18n import tr
from ...gui.outils import Tache, aide, bouton
from . import cli


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        titre = QLabel('<h2>%s</h2>' % tr('mach_titre'))
        v.addWidget(titre)
        self.table = aide(QTableWidget(0, 2), 'mach_tableau_aide')
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.table, 1)
        note = QLabel(tr('mach_gpu_note'))
        note.setWordWrap(True)
        v.addWidget(note)
        h = QHBoxLayout()
        h.addWidget(bouton('mach_rafraichir', self.actualiser))
        h.addWidget(bouton('mach_copier', self.copier))
        h.addStretch(1)
        v.addLayout(h)
        self._lignes = []
        self.actualiser()

    def actualiser(self):
        self._t = Tache(cli.rapport, parent=self)          # sondes système : hors du fil graphique
        self._t.quand_fini(self._afficher)
        self._t.start()

    def _afficher(self, d):
        self._lignes = cli.lignes(d)
        self.table.setRowCount(len(self._lignes))
        for i, (k, val) in enumerate(self._lignes):
            self.table.setItem(i, 0, QTableWidgetItem(k))
            self.table.setItem(i, 1, QTableWidgetItem(str(val)))
        self.table.resizeColumnToContents(0)

    def copier(self):
        QApplication.clipboard().setText('\n'.join('%s: %s' % kv for kv in self._lignes))
        self.window().statusBar().showMessage(tr('mach_copie_faite'), 4000)

    def aide_html(self):
        return '<p>%s</p><p>%s</p>' % (tr('mach_tableau_aide'), tr('mach_gpu_note'))
