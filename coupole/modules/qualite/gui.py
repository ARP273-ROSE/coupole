"""Panneau « Qualité des images »."""
from __future__ import annotations

import os
import threading

from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QSplitter, QVBoxLayout,
                             QWidget)
from PyQt6.QtCore import Qt

from ...core import config
from ...core.i18n import langue, tr
from ...gui.adaptatif import coupable, texte_reel
from ...gui.modele import ModeleTableau, vue_tableau
from ...gui.outils import FileEvenements, aide, bouton
from . import mesures, rapport


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        h = QHBoxLayout()
        h.addWidget(bouton('qual_choisir', self.choisir))
        self.b_lancer = bouton('qual_lancer', self.lancer)
        self.b_arreter = bouton('qual_arreter', self.arreter)
        self.b_arreter.setEnabled(False)
        h.addWidget(self.b_lancer)
        h.addWidget(self.b_arreter)
        self.l_dossier = QLabel(coupable(config.reglages()['dossier_sortie'] or
                                        str(config.dossier_sortie_defaut() / 'OHP_DU_ECU')))
        h.addWidget(self.l_dossier, 1)
        v.addLayout(h)
        if not mesures.disponible():
            l = QLabel(tr('qual_absent'))
            l.setWordWrap(True)
            v.addWidget(l)
            self.b_lancer.setEnabled(False)
        self.barre = aide(QProgressBar(), 'qual_barre_aide')
        v.addWidget(self.barre)
        sp = QSplitter(Qt.Orientation.Vertical)
        self.modele = ModeleTableau([tr('qual_col_' + c) for c in rapport.COLONNES])
        self.vue, _ = vue_tableau(self.modele, 'qual_table_aide')
        sp.addWidget(self.vue)
        self.resume = aide(QPlainTextEdit(), 'qual_resume_aide')
        self.resume.setReadOnly(True)
        sp.addWidget(self.resume)
        v.addWidget(sp, 1)
        self._fil = None
        self._arret = threading.Event()
        self._lignes = []

    def choisir(self):
        d = QFileDialog.getExistingDirectory(self, tr('qual_choisir'), texte_reel(self.l_dossier.text()))
        if d:
            self.l_dossier.setText(coupable(d))

    def occupe(self):
        return self._fil is not None and self._fil.is_alive()

    def lancer(self, dossier=None):
        if self.occupe():
            return
        racine = dossier or texte_reel(self.l_dossier.text())
        lots = rapport.fichiers(racine)
        total = sum(len(v) for v in lots.values())
        self.barre.setMaximum(max(1, total))
        self.barre.setValue(0)
        self._lignes = []
        self.modele.remplir([])
        self._arret.clear()
        self._evts = FileEvenements(self, self._evenements)

        def travail():
            fait = 0
            for d, imgs in lots.items():
                lignes = rapport.analyser_lot(imgs, lambda k, n, r: self._evts(('image', r)), self._arret)
                fait += len(lignes)
                try:
                    rapport.ecrire(d, lignes)
                except OSError:
                    pass
                self._evts(('lot', d, lignes))
                if self._arret.is_set():
                    break
            self._evts(('fin', fait, len(lots)))
        self.b_lancer.setEnabled(False)
        self.b_arreter.setEnabled(True)
        self._fil = threading.Thread(target=travail, daemon=True)
        self._fil.start()

    def arreter(self):
        self._arret.set()

    def _evenements(self, evs):
        for ev in evs:
            if ev[0] == 'image':
                r = ev[1]
                self._lignes.append(r)
                self.barre.setValue(len(self._lignes))
            elif ev[0] == 'lot':
                self.resume.setPlainText('%s\n%s' % (ev[1], '\n'.join(rapport.resume(ev[2], langue()))))
            elif ev[0] == 'fin':
                self.resume.appendPlainText('\n' + tr('qual_fini', n=ev[1], lots=ev[2]))
                self.b_lancer.setEnabled(mesures.disponible())
                self.b_arreter.setEnabled(False)
                self._evts.timer.stop()
        self.modele.remplir([tuple(rapport._fmt(l.get(c), '%.4g') if c != 'echantillonnage' or not l.get(c)
                                   else tr('qual_ech_' + l[c]) for c in rapport.COLONNES) for l in self._lignes])

    def aide_html(self):
        return tr('qual_aide_html')
