"""Snell's Law Demonstrator : un rayon passe d'un milieu à un autre et change de direction : n₁ sin θ₁ = n₂ sin θ₂.
Allant vers un milieu moins réfringent, au-delà de l'angle limite (sin θ_c = n₂ / n₁), il est entièrement réfléchi.
En plus de l'original : la part réfléchie (formules de Fresnel, lumière naturelle) et l'angle de Brewster.  Indices de
l'original (air 1,00, eau 1,33, huile 1,50, verre flint 1,66, zircon 1,92, diamant 2,42) ; celui de l'air vaut en
réalité 1,000 3."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre

MILIEUX = (('air', 1.00), ('eau', 1.33), ('huile', 1.50), ('flint', 1.66), ('zircon', 1.92), ('diamant', 2.42))


class Snell(Animation):
    ID = 'snellslaw'
    ANIMEE = False

    def construire(self):
        self.m1 = self.choix('milieu1', [('anim_snellslaw_m_' + k, k) for k, _ in MILIEUX], 'air')
        self.m1.activated.connect(lambda *_: self.n1.setValue(dict(MILIEUX)[self.m1.currentData()]))
        self.n1 = self.curseur('n1', 1.0, 2.5, 1.0, dec=3)
        self.m2 = self.choix('milieu2', [('anim_snellslaw_m_' + k, k) for k, _ in MILIEUX], 'eau')
        self.m2.activated.connect(lambda *_: self.n2.setValue(dict(MILIEUX)[self.m2.currentData()]))
        self.n2 = self.curseur('n2', 1.0, 2.5, 1.33, dec=3)
        self.theta = self.curseur('angle', 0.0, 89.9, 40.0, dec=1, unite='°')
        self._zone = None

    def valeurs(self):
        n1, n2, t1 = self.n1.value(), self.n2.value(), self.theta.value()
        t2 = lumiere.snell(t1, n1, n2)
        lim = lumiere.angle_critique(n1, n2)
        f = lumiere.fresnel(t1, n1, n2)
        return [(tr('anim_snellslaw_t2'), ('%s°' % nombre(t2, 1)) if t2 is not None else tr('anim_snellslaw_totale')),
                (tr('anim_snellslaw_limite'), ('%s°' % nombre(lim, 1)) if lim is not None else tr('anim_snellslaw_pas_de_limite')),
                (tr('anim_snellslaw_reflechie'), '%s %%' % nombre(100 * f['r'], 1)),
                (tr('anim_snellslaw_brewster'), '%s°' % nombre(lumiere.angle_brewster(n1, n2), 1)),
                ('n₁ sin θ₁ = n₂ sin θ₂', '%s = %s' % (nombre(n1 * math.sin(math.radians(t1)), 4),
                                                         nombre(n2 * math.sin(math.radians(t2)), 4) if t2 is not None else '—'))]

    def presser(self, pos, bouton):
        if self._zone is not None and pos.y() < self._zone[1]:
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        cx, cy = self._zone
        self.theta.setValue(max(0.0, min(89.9, math.degrees(math.atan2(abs(pos.x() - cx), max(1e-6, cy - pos.y()))))))

    def dessiner(self, p, rect):
        n1, n2, t1 = self.n1.value(), self.n2.value(), self.theta.value()
        r = rect.adjusted(6, 6, -6, -6)
        cx, cy = r.center().x(), r.center().y()
        self._zone = (cx, cy)
        teinte = lambda n: min(0.55, 0.08 + 0.3 * (n - 1.0))
        p.fillRect(QRectF(r.left(), r.top(), r.width(), cy - r.top()), dessin.c('equateur', teinte(n1)))
        p.fillRect(QRectF(r.left(), cy, r.width(), r.bottom() - cy), dessin.c('equateur', teinte(n2)))
        dessin.texte(p, r.left() + 10, r.top() + 16, '%s : n₁ = %s' % (tr('anim_snellslaw_haut'), nombre(n1, 3)), 'texte',
                     centre=False)
        dessin.texte(p, r.left() + 10, r.bottom() - 10, '%s : n₂ = %s' % (tr('anim_snellslaw_bas'), nombre(n2, 3)),
                     'texte', centre=False)
        L = min(r.width() / 2, r.height() / 2) * 0.92
        p.setPen(dessin.stylo('doux', 1.0, None, True))
        p.drawLine(QPointF(cx, cy - L), QPointF(cx, cy + L))
        a = math.radians(t1)
        x0, y0 = cx - L * math.sin(a), cy - L * math.cos(a)
        f = lumiere.fresnel(t1, n1, n2)
        p.setPen(dessin.stylo('accent3', 3.0))
        p.drawLine(QPointF(x0, y0), QPointF(cx, cy))
        p.setPen(dessin.stylo('accent3', 2.0, 0.25 + 0.75 * f['r']))
        p.drawLine(QPointF(cx, cy), QPointF(cx + L * math.sin(a), cy - L * math.cos(a)))
        t2 = lumiere.snell(t1, n1, n2)
        if t2 is not None:
            b = math.radians(t2)
            p.setPen(dessin.stylo('accent3', 3.0, 0.3 + 0.7 * (1 - f['r'])))
            p.drawLine(QPointF(cx, cy), QPointF(cx + L * math.sin(b), cy + L * math.cos(b)))
            self._arc(p, cx, cy, 70, -90.0, t2, 'accent1', 'θ₂')
        self._arc(p, cx, cy, 60, 90.0, t1, 'accent2', 'θ₁')
        # le laser
        p.save()
        p.translate(x0, y0)
        p.rotate(90 - t1 + 180)
        p.fillRect(QRectF(-34, -7, 34, 14), dessin.c('doux'))
        p.restore()

    @staticmethod
    def _arc(p, cx, cy, rayon, depart, etendue, cle, nom):
        """Arc d'angle depuis la normale : `depart` = direction de la normale (degrés, sens trigonométrique depuis la
        droite, y vers le haut), `etendue` = angle balayé."""
        if abs(etendue) < 0.5:
            return
        p.setPen(dessin.stylo(cle, 2.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        q = QRectF(cx - rayon, cy - rayon, 2 * rayon, 2 * rayon)
        p.drawArc(q, int(depart * 16), int(etendue * 16))
        m = math.radians(depart + etendue / 2)
        dessin.texte(p, cx + (rayon + 14) * math.cos(m), cy - (rayon + 14) * math.sin(m), nom, cle)
