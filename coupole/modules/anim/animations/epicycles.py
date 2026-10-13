"""Epicycles Demo : trois corps, le jaune au centre, le bleu et le rouge sur des orbites circulaires (périodes
selon la 3e loi de Kepler).  Vu en gardant fixe le jaune (héliocentrique), le bleu (géocentrique : le rouge
décrit des boucles, comme un épicycle) ou le rouge.  Pour des orbites circulaires, les deux descriptions
prédisent exactement les mêmes positions relatives."""
from __future__ import annotations

import collections

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre

R2, R3 = 85.0, 200.0
SEGMENTS = 120
PAS = 0.025


class Epicycles(Animation):
    ID = 'pathtracer'
    PERIODES_PAR_S = 0.5

    def construire(self):
        self.centre = self.choix('centre', [('anim_pathtracer_jaune', 1), ('anim_pathtracer_bleu', 2),
                                            ('anim_pathtracer_rouge', 3)], 1)
        self.t = 0.0
        self.traces = {2: collections.deque(maxlen=SEGMENTS), 3: collections.deque(maxlen=SEGMENTS),
                       1: collections.deque(maxlen=SEGMENTS)}

    def reglage_change(self):
        for d in self.traces.values():
            d.clear()
        super().reglage_change()

    def etat_initial(self):
        self.t = 0.0
        for d in self.traces.values():
            d.clear()

    def avancer(self, dt):
        t1 = self.t + dt * self.PERIODES_PAR_S
        n = max(1, int((t1 - self.t) / PAS))
        for i in range(1, n + 1):
            pos = astro.epicycles(self.t + (t1 - self.t) * i / n, R2, R3, self.centre.currentData())
            for k in (1, 2, 3):
                self.traces[k].append(pos[k])
        self.t = t1

    def valeurs(self):
        p3 = (R3 / R2) ** 1.5
        return [(tr('anim_pathtracer_temps'), nombre(self.t, 2)), (tr('anim_pathtracer_periode_rouge'), nombre(p3, 3))]

    def dessiner(self, p, rect):
        cx, cy = rect.center().x(), rect.center().y()
        k = min(rect.width(), rect.height()) * 0.47 / (R2 + R3)
        centre = self.centre.currentData()
        pos = astro.epicycles(self.t, R2, R3, centre)
        o = pos[1]
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for r in (R2, R3):
            p.drawEllipse(QPointF(cx + k * o[0], cy - k * o[1]), r * k, r * k)
        couleurs = {1: 'soleil', 2: 'accent2', 3: 'accent3'}
        for cle in (1, 2, 3):
            pts = list(self.traces[cle])
            n = len(pts)
            for i in range(1, n):
                p.setPen(dessin.stylo(couleurs[cle], 1.4, i / n))
                p.drawLine(QPointF(cx + k * pts[i - 1][0], cy - k * pts[i - 1][1]),
                           QPointF(cx + k * pts[i][0], cy - k * pts[i][1]))
        for cle, rr in ((1, 11), (2, 7), (3, 8)):
            x, y = pos[cle]
            dessin.disque(p, cx + k * x, cy - k * y, rr, couleurs[cle])
        dessin.texte(p, rect.x() + 12, rect.y() + 20, tr('anim_pathtracer_vu_depuis',
                                                         corps=tr(('anim_pathtracer_jaune', 'anim_pathtracer_bleu',
                                                                   'anim_pathtracer_rouge')[centre - 1])),
                     centre=False)
