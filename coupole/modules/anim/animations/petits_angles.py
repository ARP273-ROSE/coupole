"""Small-Angle Approximation Demonstrator : le diamètre angulaire α d'un objet de diamètre d vu à la distance D.
Pour un petit angle, α (en secondes d'arc) ≈ 206 265 × d / D ; valeur exacte pour une sphère : 2 asin(d / 2D).
Réglages de l'original (diamètre 1 à 3 unités, distance 20 à 60, ici dès 2 pour voir l'approximation se dégrader) ;
on peut faire glisser la boule."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre


class PetitsAngles(Animation):
    ID = 'smallangledemo'
    ANIMEE = False

    def construire(self):
        self.d = self.curseur('diametre', 1.0, 3.0, 2.0, dec=2)
        self.dist = self.curseur('distance', 2.0, 60.0, 50.0, dec=2)
        for v in (20, 30, 40, 50, 60):
            self.bouton('anim_smallangledemo_b%d' % v, lambda _=False, x=v: self.dist.setValue(x))
        self._echelle = None

    def valeurs(self):
        r = astro.diametre_angulaire(self.d.value(), self.dist.value())
        err = 100 * (r['petits_angles'] - r['sphere']) / r['sphere']
        return [(tr('anim_smallangledemo_approche'), '%s″' % nombre(r['petits_angles'], 1)),
                (tr('anim_smallangledemo_exacte'), '%s″ (%s°)' % (nombre(r['sphere'], 1), nombre(r['sphere'] / 3600, 3))),
                (tr('anim_smallangledemo_erreur'), '%s %%' % nombre(err, 3))]

    def presser(self, pos, bouton):
        if self._echelle is not None:
            x0, cy, k = self._echelle
            bx = x0 + k * self.dist.value()
            if math.hypot(pos.x() - bx, pos.y() - cy) < max(14.0, k * self.d.value() / 2 + 4):
                self._glisse = lambda q: self.dist.setValue((q.x() - self._echelle[0]) / self._echelle[2])
                return True
        return False

    def dessiner(self, p, rect):
        x0 = rect.x() + 40
        cy = rect.center().y() - 20
        k = (rect.width() - 90) / 62.0
        self._echelle = (x0, cy, k)
        d, dist = self.d.value(), self.dist.value()
        bx, rb = x0 + k * dist, k * d / 2
        a = math.asin(min(1.0, rb / (k * dist)))
        lt = math.sqrt(max(0.0, (k * dist) ** 2 - rb * rb))
        tx, ty = x0 + lt * math.cos(a), lt * math.sin(a)
        p.setPen(dessin.stylo('doux', 1.0))
        p.drawLine(QPointF(x0, cy), QPointF(tx, cy - ty))
        p.drawLine(QPointF(x0, cy), QPointF(tx, cy + ty))
        ra = min(200.0, k * dist * 0.6)
        p.setPen(dessin.stylo('accent1', 2.5))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(x0 - ra, cy - ra, 2 * ra, 2 * ra), int(-math.degrees(a) * 16), int(2 * math.degrees(a) * 16))
        dessin.texte(p, x0 + ra + 12, cy - ra * math.sin(a) - 10, 'α', 'accent1')
        dessin.disque(p, bx, cy, max(2.0, rb), 'accent2', bord='texte')
        # l'observateur (œil) et les graduations de distance
        dessin.disque(p, x0, cy, 6, 'texte')
        p.setPen(dessin.stylo('grille', 1.0))
        y = rect.bottom() - 40
        p.drawLine(QPointF(x0, y), QPointF(x0 + k * 60, y))
        dessin.police(p, 0.8)
        for v in range(0, 61, 10):
            p.drawLine(QPointF(x0 + k * v, y - 4), QPointF(x0 + k * v, y + 4))
            dessin.texte(p, x0 + k * v, y + 14, str(v), 'doux')
        dessin.police(p, 1 / 0.8)
        dessin.formule(p, rect.center().x(), rect.y() + 28,
                       'α ≈ 206 265″ × d / D = %s″' % nombre(206_264.806 * d / dist, 1), 'texte')
