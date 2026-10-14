"""Obliquity Simulator : l'obliquité est l'angle entre l'axe de rotation d'une planète et la perpendiculaire au
plan de son orbite (de façon équivalente, entre l'équateur et le plan de l'orbite)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle

# Obliquités (degrés) : Terre calculée (IAU 2006) ; Mars 25,19° et Uranus 97,77° (fiches planétaires de la NASA)
PLANETES = (('terre', None), ('mars', 25.19), ('uranus', 97.77))


class Obliquite(Animation):
    ID = 'obliquity'
    ANIMEE = False

    def construire(self):
        self.obl = self.curseur('obliquite', 0.0, 180.0, 23.5, dec=2, unite='°')
        for cle, val in PLANETES:
            self.bouton('anim_obliquity_' + cle,
                        lambda _=False, v=val: self.obl.setValue(v if v is not None else
                                                                 round(astro.obliquite_moyenne(
                                                                     astro.jour_julien(2026, 1, 1)), 3)))

    def valeurs(self):
        e26 = astro.obliquite_moyenne(astro.jour_julien(2026, 1, 1))
        return [(tr('anim_obliquity_obliquite'), angle(self.obl.value(), 2)),
                (tr('anim_obliquity_terre_j2000'), angle(astro.obliquite_moyenne(), 4)),
                (tr('anim_obliquity_terre_2026'), angle(e26, 4))]

    def dessiner(self, p, rect):
        o = self.obl.value()
        cx, cy = rect.center().x(), rect.center().y() + 10
        rt = min(rect.width(), rect.height()) * 0.26
        # plan de l'orbite (vu par la tranche)
        p.setPen(dessin.stylo('grille', 1.5))
        p.drawLine(QPointF(rect.x() + 20, cy), QPointF(rect.right() - 20, cy))
        # libellé du plan : à droite de la Terre s'il y tient, sinon à gauche, sinon tout en bas
        lib = tr('anim_obliquity_plan')
        w = p.fontMetrics().horizontalAdvance(lib)
        if rect.right() - 24 - w > cx + rt + 6:
            dessin.texte(p, rect.right() - 24 - w, cy + 16, lib, 'doux', centre=False)
        elif rect.x() + 20 + w < cx - rt - 6:
            dessin.texte(p, rect.x() + 20, cy + 16, lib, 'doux', centre=False)
        else:
            dessin.texte(p, rect.x() + 20, rect.bottom() - 8, lib, 'doux', centre=False)
        dessin.disque(p, cx, cy, rt, 'terre')
        # perpendiculaire au plan de l'orbite
        p.setPen(dessin.stylo('doux', 1.5, pointille=True))
        p.drawLine(QPointF(cx, cy - rt * 1.7), QPointF(cx, cy + rt * 1.7))
        a = math.radians(o)
        dx, dy = math.sin(a), -math.cos(a)
        # équateur incliné
        p.setPen(dessin.stylo('equateur', 2.0))
        p.drawLine(QPointF(cx - rt * math.cos(a), cy - rt * math.sin(a)), QPointF(cx + rt * math.cos(a),
                                                                                    cy + rt * math.sin(a)))
        # axe de rotation
        p.setPen(dessin.stylo('texte', 2.5))
        p.drawLine(QPointF(cx - dx * rt * 1.6, cy - dy * rt * 1.6), QPointF(cx + dx * rt * 1.6, cy + dy * rt * 1.6))
        dessin.texte(p, cx + dx * rt * 1.75, cy + dy * rt * 1.75, tr('anim_pc_n'), 'texte')
        rr = rt * 1.25
        p.setPen(dessin.stylo('accent1', 2.5))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(cx - rr, cy - rr, 2 * rr, 2 * rr), 90 * 16, int(-o * 16))
        b = math.radians(o / 2)
        dessin.texte(p, cx + math.sin(b) * rr * 1.18, cy - math.cos(b) * rr * 1.18, angle(o, 1), 'accent1', fond=True)
