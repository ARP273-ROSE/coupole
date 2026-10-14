"""Eccentricity Demonstrator : les grandeurs qui définissent l'excentricité d'une ellipse.  Demi-grand axe a,
distance c du centre à chaque foyer, excentricité e = c / a, demi-petit axe b = √(a² − c²).  Réglages de
l'original (a de 40 à 100, c de 0 à a − 1) ; en plus, un point qui parcourt l'ellipse montre que la somme de ses
distances aux deux foyers vaut toujours 2a (la méthode du jardinier)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre


def ellipse(a: float, c: float, t: float) -> dict:
    """Point d'angle paramétrique t (degrés) et ses distances aux foyers (−c, 0) et (+c, 0)."""
    b = math.sqrt(max(0.0, a * a - c * c))
    x, y = a * math.cos(math.radians(t)), b * math.sin(math.radians(t))
    return {'x': x, 'y': y, 'b': b, 'e': c / a, 'r1': math.hypot(x + c, y), 'r2': math.hypot(x - c, y)}


class Excentricite(Animation):
    ID = 'ellipsedemo'
    DEGRES_PAR_S = 30.0

    def construire(self):
        self.a = self.curseur('a', 40.0, 100.0, 100.0, dec=0)
        self.c = self.curseur('c', 0.0, 99.0, 40.0, dec=0)
        self.c_jardinier = self.coche('jardinier', True)
        self.c_b = self.coche('b', False)
        self.t = 60.0
        self._borner()

    def _borner(self):
        self.c.borner(0.0, self.a.value() - 1.0)

    def reglage_change(self):
        self._borner()
        super().reglage_change()

    def etat_initial(self):
        self.t = 60.0

    def avancer(self, dt):
        self.t = (self.t + dt * self.DEGRES_PAR_S) % 360.0

    def valeurs(self):
        a, c = self.a.value(), self.c.value()
        g = ellipse(a, c, self.t)
        out = [('a', nombre(a, 0)), ('c', nombre(c, 0)), ('b = √(a² − c²)', nombre(g['b'], 2)),
               (tr('anim_ellipsedemo_e'), 'c / a = %s' % nombre(g['e'], 3))]
        if self.c_jardinier.isChecked():
            out.append((tr('anim_ellipsedemo_somme'), '%s + %s = %s = 2a' % (nombre(g['r1'], 2), nombre(g['r2'], 2),
                                                                           nombre(g['r1'] + g['r2'], 2))))
        return out

    def dessiner(self, p, rect):
        a, c = self.a.value(), self.c.value()
        g = ellipse(a, c, self.t)
        k = min((rect.width() - 40) / 200.0, (rect.height() - 70) / 200.0)
        cx, cy = rect.center().x(), rect.center().y() - 10

        def q(x, y):
            return QPointF(cx + k * x, cy - k * y)

        p.setPen(dessin.stylo('texte', 1.8))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(q(0, 0), k * a, k * g['b'])
        p.setPen(dessin.stylo('grille', 1.0, pointille=True))
        p.drawLine(q(-a, 0), q(a, 0))
        for x in (-c, c):
            dessin.disque(p, q(x, 0).x(), q(x, 0).y(), 4.5, 'accent1')
        dessin.disque(p, cx, cy, 2.5, 'doux')
        # cotes a (sous l'axe) et c (au-dessus)
        ya, yc = -g['b'] - 12 / k, 10 / k
        dessin.fleche(p, q(0, ya).x(), q(0, ya).y(), q(a, ya).x(), q(a, ya).y(), dessin.stylo('accent2', 1.4), 7)
        dessin.texte(p, q(a / 2, ya).x(), q(a / 2, ya).y() + 11, 'a', 'accent2')
        if c > 0:
            dessin.fleche(p, q(0, yc).x(), q(0, yc).y(), q(c, yc).x(), q(c, yc).y(), dessin.stylo('accent3', 1.4), 6)
            dessin.texte(p, q(c / 2, yc).x(), q(c / 2, yc).y() - 10, 'c', 'accent3')
        if self.c_b.isChecked():
            p.setPen(dessin.stylo('arc1', 1.4))
            p.drawLine(q(0, 0), q(0, g['b']))
            dessin.texte(p, q(0, g['b'] / 2).x() + 10, q(0, g['b'] / 2).y(), 'b', 'arc1')
        if self.c_jardinier.isChecked():
            m = q(g['x'], g['y'])
            p.setPen(dessin.stylo('arc2', 1.4))
            p.drawLine(q(-c, 0), m)
            p.setPen(dessin.stylo('equateur', 1.4))
            p.drawLine(q(c, 0), m)
            dessin.disque(p, m.x(), m.y(), 5, 'accent1', bord='texte')
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(cx - 110, rect.bottom() - 36, 220, 34), 8, 8)
        dessin.police(p, 1.3, gras=True)
        dessin.texte(p, cx, rect.bottom() - 19, 'e = c / a = %s' % nombre(g['e'], 3))
        dessin.police(p, 1 / 1.3)
