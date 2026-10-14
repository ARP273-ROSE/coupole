"""Antipodes Explorer : un point de la Terre et son antipode (latitude −φ, longitude λ ± 180°), sur le globe et sur
une carte plane ; déplacement à la souris, éventuellement le long d'un parallèle ou d'un méridien, aimanté aux
multiples de 5°."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation
from .longitude_latitude import decimal, dessiner_cotes_carte, dessiner_cotes_globe, globe_xyz


def antipode(lat: float, lon: float) -> tuple[float, float]:
    lo = lon + 180.0 if lon <= 0 else lon - 180.0
    return -lat, lo


class Antipodes(Animation):
    ID = 'antipodesexplorer'
    ANIMEE = False

    def construire(self):
        self.globe = self.vue(30.0, 20.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 48.85, dec=2, unite='°', cle_texte='anim_c_latitude')
        self.lon = self.curseur('longitude', -180.0, 180.0, 2.35, dec=2, unite='°', cle_texte='anim_c_longitude')
        self.contrainte = self.choix('contrainte', [('anim_antipodesexplorer_libre', 'libre'),
                                                    ('anim_antipodesexplorer_parallele', 'parallele'),
                                                    ('anim_antipodesexplorer_meridien', 'meridien')], 'libre')
        self.c_aimant = self.coche('aimant', False)
        self._carte = None

    def _textes(self, la, lo):
        return decimal(la, tr('anim_pc_n'), tr('anim_pc_s')), decimal(lo, tr('anim_pc_e'), tr('anim_pc_o'))

    def valeurs(self):
        la, lo = self.lat.value(), self.lon.value()
        a1, a2 = antipode(la, lo)
        return [(tr('anim_antipodesexplorer_point'), '%s, %s' % self._textes(la, lo)),
                (tr('anim_antipodesexplorer_antipode'), '%s, %s' % self._textes(a1, a2))]

    def presser(self, pos, bouton):
        if self._carte is not None and self._carte.contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return super().presser(pos, bouton)

    def _tirer(self, pos):
        r = self._carte
        lo = (pos.x() - r.x()) / r.width() * 360.0 - 180.0
        la = 90.0 - (pos.y() - r.y()) / r.height() * 180.0
        if self.c_aimant.isChecked():
            la, lo = 5 * round(la / 5), 5 * round(lo / 5)
        c = self.contrainte.currentData()
        if c != 'parallele':
            self.lat.setValue(max(-90.0, min(90.0, la)))
        if c != 'meridien':
            self.lon.setValue(max(-180.0, min(180.0, lo)))

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.9)
        self._dessiner_globe(p, dessin.cadre(p, z[0], tr('anim_antipodesexplorer_globe')))
        self._dessiner_carte(p, dessin.cadre(p, z[1], tr('anim_antipodesexplorer_carte')))

    def _dessiner_globe(self, p, r):
        self.zone_rotative(r, self.globe)
        rr = min(r.width(), r.height()) * 0.42
        pe = dessin.Peintre3D(p, self.globe, r.center().x(), r.center().y(), rr)
        pe.contour('grille', 'terre', 0.25)
        dessiner_cotes_globe(pe)
        la, lo = self.lat.value(), self.lon.value()
        a1, a2 = antipode(la, lo)
        pe.segment(globe_xyz(la, lo), globe_xyz(a1, a2), 'accent2', 1.5, 0.7)
        pe.point(globe_xyz(la, lo), 'soleil', 6.0, bord='fond', toujours=True)
        pe.point(globe_xyz(a1, a2), 'accent3', 6.0, bord='fond', toujours=True)

    def _dessiner_carte(self, p, r):
        w = min(r.width(), r.height() * 2.0)
        carte = QRectF(r.center().x() - w / 2, r.center().y() - w / 4, w, w / 2)
        self._carte = carte

        def xy(la, lo):
            return QPointF(carte.x() + (lo + 180.0) / 360.0 * carte.width(), carte.y() + (90.0 - la) / 180.0 *
                           carte.height())
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.c('terre', 0.18))
        p.drawRect(carte)
        dessiner_cotes_carte(p, carte, 'doux', 0.8, 0.8)
        p.setPen(dessin.stylo('grille', 0.6, 0.6))
        for k in range(-60, 90, 30):
            p.drawLine(xy(k, -180), xy(k, 180))
        for k in range(-150, 180, 30):
            p.drawLine(xy(-90, k), xy(90, k))
        la, lo = self.lat.value(), self.lon.value()
        a1, a2 = antipode(la, lo)
        q1, q2 = xy(la, lo), xy(a1, a2)
        dessin.disque(p, q1.x(), q1.y(), 6, 'soleil', bord='fond')
        dessin.disque(p, q2.x(), q2.y(), 6, 'accent3', bord='fond')
        dessin.texte(p, q1.x(), q1.y() - 14, tr('anim_antipodesexplorer_point'), 'soleil', fond=True)
        dessin.texte(p, q2.x(), q2.y() - 14, tr('anim_antipodesexplorer_antipode'), 'accent3', fond=True)
