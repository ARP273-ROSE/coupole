"""Panneau « Spectres et séries »."""
from __future__ import annotations

import csv

from PyQt6.QtWidgets import (QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QListWidget, QMessageBox,
                             QSplitter, QVBoxLayout, QWidget)
from PyQt6.QtCore import Qt

from ...core import donnees
from ...core.i18n import tr
from ...gui.adaptatif import coupable
from ...gui.outils import Tache, aide, bouton, liste
from ...gui.trace import Trace
from . import cli


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ds = []
        v = QVBoxLayout(self)
        h = QHBoxLayout()
        h.addWidget(bouton('don_ouvrir', self.ouvrir))
        h.addWidget(bouton('don_exporter', self.exporter))
        self.l_fichier = QLabel(tr('don_aucun'))
        self.l_fichier.setWordWrap(True)
        h.addWidget(self.l_fichier, 1)
        v.addLayout(h)
        sp = QSplitter(Qt.Orientation.Horizontal)
        gauche = QWidget()
        f = QFormLayout(gauche)
        self.liste = aide(QListWidget(), 'don_liste_aide')
        self.liste.currentRowChanged.connect(self.afficher)
        f.addRow(self.liste)
        self.axe = liste('don_axe_aide', [(tr('don_axe_brut'), 'brut'), (tr('don_axe_mhz'), 'mhz'),
                                          (tr('don_axe_vitesse'), 'vitesse')])
        self.axe.currentIndexChanged.connect(lambda *_: self.afficher(self.liste.currentRow()))
        f.addRow(tr('don_axe'), self.axe)
        self.f0 = aide(QDoubleSpinBox(), 'don_f0_aide')
        self.f0.setDecimals(6)
        self.f0.setRange(0.001, 1e6)
        self.f0.setValue(donnees.HI_HZ / 1e6)
        self.f0.valueChanged.connect(lambda *_: self.afficher(self.liste.currentRow()))
        f.addRow(tr('don_f0'), self.f0)
        self.colx = liste('don_colx_aide', [])
        self.coly = liste('don_coly_aide', [])
        self.colx.currentIndexChanged.connect(lambda *_: self.afficher(self.liste.currentRow(), garder_cols=True))
        self.coly.currentIndexChanged.connect(lambda *_: self.afficher(self.liste.currentRow(), garder_cols=True))
        f.addRow(tr('don_colx'), self.colx)
        f.addRow(tr('don_coly'), self.coly)
        self.info = QLabel('')
        self.info.setWordWrap(True)
        f.addRow(self.info)
        sp.addWidget(gauche)
        self.trace = aide(Trace(), 'don_trace_aide')
        sp.addWidget(self.trace)
        sp.setSizes([320, 900])
        v.addWidget(sp, 1)

    def ouvrir(self, chemin=None):
        if not chemin:
            filtres = ' '.join('*' + e for ext, _, _ in donnees._lecteurs for e in ext)
            chemin, _ = QFileDialog.getOpenFileName(self, tr('don_ouvrir'), '', '(%s)' % filtres)
        if not chemin:
            return
        self.l_fichier.setText(tr('don_lecture', fichier=coupable(chemin)))
        self._t = Tache(donnees.lire, chemin, parent=self)       # lecture FITS (parfois longue) hors du fil
        self._t.quand_fini(lambda ds, c=chemin: self._ouvert(c, ds))
        self._t.quand_erreur(lambda e: (self.l_fichier.setText(tr('don_aucun')),
                                        QMessageBox.warning(self, tr('don_ouvrir'), tr('don_erreur', erreur=e))))
        self._t.start()

    def _ouvert(self, chemin, ds):
        self.ds = ds
        self.l_fichier.setText(coupable(chemin))
        self.liste.clear()
        for d in self.ds:
            self.liste.addItem('%s — %s' % (tr('don_genre_' + d.genre), d.titre))
        premier = next((i for i, d in enumerate(self.ds) if d.x is not None), 0)
        self.liste.setCurrentRow(premier)

    def _courant(self):
        i = self.liste.currentRow()
        return self.ds[i] if 0 <= i < len(self.ds) else None

    def afficher(self, i, garder_cols=False):
        d = self._courant()
        if d is None:
            return
        if d.genre == 'image':
            self.info.setText(tr('don_image_ici', forme='×'.join(str(n) for n in d.image.shape)))
            return
        if d.table and not garder_cols:
            for c in (self.colx, self.coly):
                c.blockSignals(True)
                c.clear()
                for k in d.table:
                    c.addItem(k, k)
                c.blockSignals(False)
            self.colx.setCurrentIndex(max(0, self.colx.findData(d.nom_x)))
            self.coly.setCurrentIndex(max(0, self.coly.findData(d.nom_y)))
        if d.table and garder_cols and self.colx.currentData() and self.coly.currentData():
            d.x, d.y = d.table[self.colx.currentData()], d.table[self.coly.currentData()]
            d.nom_x, d.nom_y = self.colx.currentData(), self.coly.currentData()
        if d.x is None:
            return
        if d.meta.get('restfreq_hz') and not garder_cols:
            self.f0.blockSignals(True)
            self.f0.setValue(d.meta['restfreq_hz'] / 1e6)
            self.f0.blockSignals(False)
        x, tx = d.x, ('%s [%s]' % (d.nom_x, d.unite_x)) if d.unite_x else d.nom_x
        mode = self.axe.currentData()
        freq = d.meta.get('axe') == 'freq'
        self.axe.setEnabled(freq)
        try:
            if freq and mode == 'mhz':
                x, tx = donnees.en_hz(d.x, d.unite_x or 'Hz') / 1e6, tr('don_axe_mhz')
            elif freq and mode == 'vitesse':
                x = donnees.vitesse_radio(donnees.en_hz(d.x, d.unite_x or 'Hz'), self.f0.value() * 1e6)
                tx = tr('don_axe_vitesse')
        except ValueError:
            pass
        self.trace.definir(x, d.y, tx, ('%s [%s]' % (d.nom_y, d.unite_y)) if d.unite_y else d.nom_y)
        r = d.resume()
        texte = tr('don_info', genre=tr('don_genre_' + d.genre), n=r['n'], x=d.nom_x)
        if freq:
            texte += '\n' + tr('don_referentiel', specsys=d.meta.get('specsys') or tr('don_inconnu'))
        self.info.setText(texte)

    def exporter(self):
        d = self._courant()
        if d is None or d.x is None:
            return
        f, _ = QFileDialog.getSaveFileName(self, tr('don_exporter'), 'donnees.csv', 'CSV (*.csv)')
        if not f:
            return
        tete, cols = cli.colonnes(d, self.axe.currentData() == 'vitesse', self.f0.value())

        def ecrire():                                 # hors du fil graphique : 10^6 lignes = plusieurs secondes
            with open(f, 'w', newline='', encoding='utf-8') as fh:
                w = csv.writer(fh)
                w.writerow(tete)
                for ligne in zip(*cols):
                    w.writerow(['%.10g' % v for v in ligne])
            return f
        self._t_export = Tache(ecrire, parent=self)
        self._t_export.quand_fini(lambda c: QMessageBox.information(self, tr('don_exporter'), tr('ecrit', chemin=c)))
        self._t_export.quand_erreur(lambda e: QMessageBox.warning(self, tr('don_exporter'), e))
        self._t_export.start()

    def aide_html(self):
        return tr('don_aide_html')
