"""Panneau « Sites et heures » : table des sites, carte OpenStreetMap, heure locale."""
from __future__ import annotations

import datetime as D

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QMessageBox, QSplitter,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ...core import sites, temps
from ...core.i18n import tr
from ...gui.cartes import CarteMonde
from ...gui.outils import aide, bouton, case, champ
from .cli import verifier_fuseau

COLS = ('id', 'nom', 'lat', 'lon', 'alt', 'mpc', 'fuseau', 'heure', 'origine')


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        h = QHBoxLayout()
        h.addWidget(bouton('sit_ajouter', self.ajouter))
        h.addWidget(bouton('sit_supprimer', self.supprimer))
        self.en_ligne = case('sit_en_ligne', True)
        self.en_ligne.toggled.connect(self._en_ligne)
        h.addWidget(self.en_ligne)
        h.addStretch(1)
        self.b_images = bouton('sit_voir_images', self.voir_images)
        h.addWidget(self.b_images)
        v.addLayout(h)
        sp = QSplitter(Qt.Orientation.Vertical)
        self.table = aide(QTableWidget(0, len(COLS)), 'sit_table_aide')
        self.table.setHorizontalHeaderLabels([tr('sit_col_' + c) for c in COLS])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._choisi)
        sp.addWidget(self.table)
        self.carte = aide(CarteMonde(self), 'sit_carte_aide')
        self.carte.site_clique.connect(self._clic_carte)
        sp.addWidget(self.carte)
        sp.setSizes([200, 520])
        v.addWidget(sp, 1)
        self.info = QLabel('')
        v.addWidget(self.info)
        self.remplir()
        self.horloge = QTimer(self)
        self.horloge.timeout.connect(self._heures)
        self.horloge.start(30000)

    def remplir(self):
        self.sites = sites.sites()
        self.table.setRowCount(len(self.sites))
        for i, s in enumerate(self.sites):
            for j, val in enumerate((s.id, s.nom, '%.5f' % s.lat, '%.5f' % s.lon, '%.0f' % s.alt, s.mpc,
                                     s.fuseau or '~', '', tr('sit_origine_' + s.origine))):
                self.table.setItem(i, j, QTableWidgetItem(val))
        self._heures()
        self.table.resizeColumnsToContents()
        self.carte.definir([(s.lon, s.lat, '%s\n%.5f°, %.5f° E, %.0f m%s\n%s' % (
            s.nom, s.lat, s.lon, s.alt, (' — MPC ' + s.mpc) if s.mpc else '', s.fuseau), s) for s in self.sites])
        if self.sites:
            self.carte.centrer(self.sites[0].lon, self.sites[0].lat, 4)

    def _heures(self):
        maintenant = D.datetime.now(D.timezone.utc)
        for i, s in enumerate(self.sites):
            self.table.setItem(i, 7, QTableWidgetItem(temps.heure_locale(maintenant, s).strftime('%Y-%m-%d %H:%M')))

    def _choisi(self):
        r = self.table.currentRow()
        if 0 <= r < len(self.sites):
            self._montrer(self.sites[r])

    def _clic_carte(self, s):
        self._montrer(s)

    def _montrer(self, s):
        self.carte.centrer(s.lon, s.lat)
        maintenant = D.datetime.now(D.timezone.utc)
        n = self._compter_images(s)
        self.info.setText(tr('sit_info', nom=s.nom, lat='%.5f' % s.lat, lon='%.5f' % s.lon, alt='%.0f' % s.alt,
                             fuseau=s.fuseau or '~', heure=temps.formater(maintenant, s)) +
                          ('  —  ' + tr('sit_images', n=n) if n is not None else ''))
        self._site = s

    def _compter_images(self, s):
        for p in getattr(self.window(), 'panneaux', []):
            inv = getattr(p, 'inv', None)
            if inv is not None:
                return sum(1 for x in inv.images if x.get('site') == s.id and not x['doublon'])
        return None

    def voir_images(self):
        f = self.window()
        for i, p in enumerate(getattr(f, 'panneaux', [])):
            if getattr(getattr(p, 'module', None), 'id', '') == 'ohp':
                f.barre.setCurrentRow(i)

    def _en_ligne(self, oui):
        self.carte.en_ligne = oui
        self.carte.update()

    def ajouter(self):
        d = DialogueSite(self)
        if d.exec():
            self.remplir()

    def supprimer(self):
        r = self.table.currentRow()
        if 0 <= r < len(self.sites) and self.sites[r].origine == 'utilisateur':
            sites.supprimer_site(self.sites[r].id)
            self.remplir()

    def aide_html(self):
        return tr('sit_aide_html')


class DialogueSite(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('sit_dlg_titre'))
        f = QFormLayout(self)
        self.id = champ('sit_champ_id_aide')
        self.nom = champ('sit_champ_nom_aide')
        self.lat = aide(QDoubleSpinBox(), 'sit_champ_lat_aide')
        self.lat.setRange(-90, 90)
        self.lat.setDecimals(5)
        self.lon = aide(QDoubleSpinBox(), 'sit_champ_lon_aide')
        self.lon.setRange(-180, 360)
        self.lon.setDecimals(5)
        self.alt = aide(QDoubleSpinBox(), 'sit_champ_alt_aide')
        self.alt.setRange(-500, 9000)
        self.fuseau = champ('sit_champ_fuseau_aide', 'UTC')
        self.mpc = champ('sit_champ_mpc_aide')
        for cle, w in (('sit_col_id', self.id), ('sit_col_nom', self.nom), ('sit_col_lat', self.lat),
                       ('sit_col_lon', self.lon), ('sit_col_alt', self.alt), ('sit_col_fuseau', self.fuseau),
                       ('sit_col_mpc', self.mpc)):
            f.addRow(tr(cle), w)
        h = QHBoxLayout()
        h.addStretch(1)
        h.addWidget(bouton('dlg_annuler', self.reject))
        h.addWidget(bouton('dlg_ok', self.accept))
        f.addRow(h)

    def accept(self):
        if not self.id.text().strip() or not verifier_fuseau(self.fuseau.text().strip()):
            QMessageBox.warning(self, tr('sit_dlg_titre'), tr('sit_fuseau_invalide', fuseau=self.fuseau.text()))
            return
        sites.enregistrer_site({'id': self.id.text().strip(), 'nom': self.nom.text().strip() or self.id.text().strip(),
                                'lat': self.lat.value(), 'lon': self.lon.value(), 'alt': self.alt.value(),
                                'fuseau': self.fuseau.text().strip(), 'mpc': self.mpc.text().strip()})
        super().accept()
