"""Flux Simulator : une ampoule et un détecteur qu'on éloigne.  La puissance de l'ampoule se répartit sur des
sphères de plus en plus grandes : le flux reçu suit la loi de l'inverse du carré, F = P / 4π d².  Ampoules de
l'original (20, 25, 50, 100, 400 et 500 W), détecteur de 1 à 5 m (on peut le faire glisser)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import dessin, hr
from ..base import Animation, nombre

PUISSANCES = (20, 25, 50, 100, 400, 500)
D_MIN, D_MAX = 1.0, 5.0


class FluxLumineux(Animation):
    ID = 'lightdetector'
    ANIMEE = False

    def construire(self):
        self.puissance = self.choix('puissance', [('anim_lightdetector_w%d' % w, w) for w in PUISSANCES], 25)
        self.d = self.curseur('distance', D_MIN, D_MAX, 1.0, dec=2, unite='m')
        self.c_spheres = self.coche('spheres', True)
        self._zone = None

    def valeurs(self):
        w, d = self.puissance.currentData(), self.d.value()
        f = hr.flux(w, d)
        return [(tr('anim_lightdetector_flux'), '%s W·m⁻²' % nombre(f, 3)),
                (tr('anim_lightdetector_rapport'), '1 / %s² = 1 / %s' % (nombre(d, 2), nombre(d * d, 2))),
                (tr('anim_lightdetector_aire'), '%s m²' % nombre(4 * math.pi * d * d, 2))]

    def presser(self, pos, bouton):
        if self._zone is not None and self._zone[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        _, x0, k = self._zone
        self.d.setValue((pos.x() - x0) / k)

    def dessiner(self, p, rect):
        w, d = self.puissance.currentData(), self.d.value()
        x0 = rect.x() + 50
        cy = rect.center().y() - 20
        k = (rect.width() - 110) / D_MAX
        self._zone = (QRectF(rect), x0, k)
        # ampoule : plus lumineuse pour une plus forte puissance
        lum = 0.35 + 0.65 * math.log10(w / 20) / math.log10(25)
        for r, a in ((30, 0.12), (22, 0.25)):
            dessin.disque(p, x0, cy, r * (0.8 + lum * 0.4), 'soleil', alpha=a * (0.5 + lum))
        dessin.disque(p, x0, cy, 14, 'soleil')
        dessin.texte(p, x0, cy + 40, '%d W' % w, 'texte')
        if self.c_spheres.isChecked():                       # arcs des sphères de rayon 1, 2, 3, 4, 5 m
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            demi = min(35.0, math.degrees(math.asin(min(1.0, (cy - rect.y() - 10) / (5 * k)))))
            for r in range(1, 6):
                p.setPen(dessin.stylo('grille', 1.0, 0.8))
                p.drawArc(QRectF(x0 - r * k, cy - r * k, 2 * r * k, 2 * r * k), int(-demi * 16), int(2 * demi * 16))
                dessin.texte(p, x0 + r * k + 12, cy + 14, '%d m' % r, 'doux')
        # faisceau intercepté par le détecteur (carré de côté fixe) : même angle solide, il se dilue
        xd = x0 + d * k
        cote = 0.18
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('soleil', 0.18))
        p.drawPolygon(QPolygonF([QPointF(x0, cy), QPointF(xd, cy - cote * k / 2), QPointF(xd, cy + cote * k / 2)]))
        p.setPen(dessin.stylo('texte', 1.2))
        p.setBrush(dessin.c('accent2'))
        p.drawRect(QRectF(xd - 5, cy - cote * k / 2, 10, cote * k))
        dessin.texte(p, xd, cy - cote * k / 2 - 14, tr('anim_lightdetector_detecteur'), 'accent2', fond=True)
        # jauge du flux (échelle logarithmique, de 0,01 à 50 W·m⁻²)
        f = hr.flux(w, d)
        gx, gy, gl = rect.x() + 30, rect.bottom() - 18, rect.width() - 60
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(gx, gy, gl, 12))
        t = max(0.0, min(1.0, (math.log10(f) + 2) / (math.log10(50) + 2)))
        p.fillRect(QRectF(gx, gy, gl * t, 12), dessin.c('accent1'))
        dessin.formule_texte(p, gx + gl / 2, gy - 24, 'F = P / 4π d²', ' = %s W·m⁻²' % nombre(f, 3), 'texte')
