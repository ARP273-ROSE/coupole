"""Center of Mass Simulator : le centre de masse de deux corps est sur le segment qui les joint, aux distances
r₁ = d m₂ / (m₁ + m₂) et r₂ = d m₁ / (m₁ + m₂) : plus près du plus massif (r₁ m₁ = r₂ m₂).  Réglages de l'original
(masses 1 à 10, défauts 7 et 3, séparation 1 à 20, défaut 10) ; on peut en plus faire tourner le couple autour de
son centre de masse."""
from __future__ import annotations

import math

from PyQt6.QtCore import QLineF, QPointF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre


def distances(m1: float, m2: float, d: float) -> tuple[float, float]:
    return d * m2 / (m1 + m2), d * m1 / (m1 + m2)


class CentreMasse(Animation):
    ID = 'centerofmass'

    def construire(self):
        self.m1 = self.curseur('m1', 1.0, 10.0, 7.0, dec=1)
        self.m2 = self.curseur('m2', 1.0, 10.0, 3.0, dec=1)
        self.d = self.curseur('separation', 1.0, 20.0, 10.0, dec=1)
        self.c_fixe = self.coche('fixe', True)
        self.angle = 0.0

    def etat_initial(self):
        self.angle = 0.0

    def avancer(self, dt):
        self.angle += dt * 2 * math.pi / 6.0

    def valeurs(self):
        m1, m2, d = self.m1.value(), self.m2.value(), self.d.value()
        r1, r2 = distances(m1, m2, d)
        return [(tr('anim_centerofmass_r1'), nombre(r1, 2)), (tr('anim_centerofmass_r2'), nombre(r2, 2)),
                (tr('anim_centerofmass_produits'), 'm₁ r₁ = %s = m₂ r₂ = %s' % (nombre(m1 * r1, 2), nombre(m2 * r2, 2)))]

    def dessiner(self, p, rect):
        r = dessin.cadre(p, rect, tr('anim_centerofmass_titre'))
        m1, m2, d = self.m1.value(), self.m2.value(), self.d.value()
        r1, r2 = distances(m1, m2, d)
        k = min(r.width() * 0.8, r.height() * 1.6) / 20.0
        cx, cy = r.center().x(), r.center().y()
        if not self.c_fixe.isChecked():                   # le corps 1 reste en place : le centre de masse se déplace
            cx = r.center().x() - d * k / 2 + r1 * k
        # quadrillage (une unité de séparation)
        lignes = []
        n = int(r.width() / k / 2) + 1
        for i in range(-n, n + 1):
            x = cx + i * k
            if r.left() <= x <= r.right():
                lignes.append(QLineF(x, r.top() + 6, x, r.bottom() - 6))
        p.setPen(dessin.stylo('grille', 0.6, 0.5))
        p.setRenderHint(p.RenderHint.Antialiasing, False)
        p.drawLines(lignes)
        p.setRenderHint(p.RenderHint.Antialiasing, True)
        a = self.angle
        x1, y1 = cx - r1 * k * math.cos(a), cy + r1 * k * math.sin(a)
        x2, y2 = cx + r2 * k * math.cos(a), cy - r2 * k * math.sin(a)
        p.setPen(dessin.stylo('accent2', 2.0))
        p.drawLine(QPointF(x1, y1), QPointF(cx, cy))
        p.setPen(dessin.stylo('accent3', 2.0))
        p.drawLine(QPointF(cx, cy), QPointF(x2, y2))
        dessin.disque(p, x1, y1, 8 * m1 ** 0.37, 'accent2', bord='texte')
        dessin.disque(p, x2, y2, 8 * m2 ** 0.37, 'accent3', bord='texte')
        dessin.texte(p, x1, y1 - 8 * m1 ** 0.37 - 12, 'm₁ = %s' % nombre(m1, 1), 'accent2', fond=True)
        dessin.texte(p, x2, y2 - 8 * m2 ** 0.37 - 12, 'm₂ = %s' % nombre(m2, 1), 'accent3', fond=True)
        dessin.texte(p, (x1 + cx) / 2, (y1 + cy) / 2 + 14, 'r₁ = %s' % nombre(r1, 2), 'accent2', fond=True)
        dessin.texte(p, (x2 + cx) / 2, (y2 + cy) / 2 + 14, 'r₂ = %s' % nombre(r2, 2), 'accent3', fond=True)
        p.setPen(dessin.stylo('accent1', 2.0))
        p.drawLine(QPointF(cx - 7, cy - 7), QPointF(cx + 7, cy + 7))
        p.drawLine(QPointF(cx - 7, cy + 7), QPointF(cx + 7, cy - 7))
        dessin.texte(p, cx, cy + 34, tr('anim_c_barycentre'), 'accent1', fond=True)
