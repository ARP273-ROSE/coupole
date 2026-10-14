"""Driving Through Snow : en voiture sous la neige, les flocons semblent tous jaillir d'un même point devant soi.
Leur vitesse par rapport à la voiture est la même pour tous ; en perspective, des trajectoires parallèles convergent
vers un point de fuite.  C'est le « radiant » d'une pluie d'étoiles filantes : la Terre traverse un essaim de
poussières aux trajectoires parallèles.  Le radiant est à l'angle arctan(v_neige / v_voiture) au-dessus de
l'horizon.  Réglages de l'original : champ de vision 110°, vitesse 20, visibilité 100."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPolygonF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre

N = 1800
LARGEUR, HAUTEUR, PROFONDEUR, PRES = 60.0, 40.0, 120.0, 1.0


class Neige(Animation):
    ID = 'drivingthroughsnow'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.v_voiture = self.curseur('voiture', 0.0, 60.0, 20.0, dec=1)
        self.v_neige = self.curseur('neige', 0.0, 20.0, 1.0, dec=1)
        self.champ = self.curseur('champ', 30.0, 130.0, 110.0, dec=0, unite='°')
        self.visibilite = self.curseur('visibilite', 20.0, 120.0, 100.0, dec=0)
        self.c_radiant = self.coche('radiant', True)
        self.etat_initial()

    def etat_initial(self):
        g = np.random.default_rng(5)
        self.pos = np.column_stack([g.uniform(-LARGEUR, LARGEUR, N), g.uniform(PRES, PROFONDEUR, N),
                                    g.uniform(-HAUTEUR, HAUTEUR, N)])

    def avancer(self, dt):
        self.pos[:, 1] -= self.v_voiture.value() * dt
        self.pos[:, 2] -= self.v_neige.value() * dt
        b = self.pos[:, 1] < PRES
        self.pos[b, 1] += PROFONDEUR - PRES
        h = self.pos[:, 2] < -HAUTEUR
        self.pos[h, 2] += 2 * HAUTEUR

    def angle_radiant(self) -> float:
        """Hauteur du radiant au-dessus de l'horizon (degrés)."""
        return math.degrees(math.atan2(self.v_neige.value(), self.v_voiture.value()))

    def valeurs(self):
        return [(tr('anim_drivingthroughsnow_radiant_v'), '%s°' % nombre(self.angle_radiant(), 1))]

    def dessiner(self, p, rect):
        r = rect.adjusted(6, 6, -6, -6)
        p.fillRect(r, QColor(6, 8, 12))
        cx, cy = r.center().x(), r.center().y()
        f = (r.width() / 2) / math.tan(math.radians(self.champ.value() / 2))
        x, y, z = self.pos[:, 0], self.pos[:, 1], self.pos[:, 2]
        sx = cx + f * x / y
        sy = cy - f * z / y
        d = np.sqrt(x * x + y * y + z * z)
        lum = 1.0 - d / self.visibilite.value()
        ok = (lum > 0) & (sx >= r.left()) & (sx < r.right()) & (sy >= r.top()) & (sy < r.bottom())
        p.save()
        p.setClipRect(r)
        for k, (a, b) in enumerate(((0.0, 0.33), (0.33, 0.66), (0.66, 1.01))):
            sel = ok & (lum >= a) & (lum < b)
            if not sel.any():
                continue
            g = int(90 + 165 * (a + b) / 2)
            p.setPen(dessin.stylo(QColor(g, g, g), 1.0 + k))
            p.drawPoints(QPolygonF(list(map(QPointF, sx[sel].tolist(), sy[sel].tolist()))))
        if self.c_radiant.isChecked() and self.v_voiture.value() > 0:
            ry = cy - f * self.v_neige.value() / self.v_voiture.value()
            if r.top() < ry < r.bottom():
                p.setPen(dessin.stylo('accent3', 1.5))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(cx, ry), 9, 9)
                dessin.texte(p, cx, ry - 18, tr('anim_drivingthroughsnow_radiant'), 'accent3', fond=True)
        p.restore()
