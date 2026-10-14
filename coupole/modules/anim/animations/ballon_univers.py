"""Balloon Universe : un ballon qui se gonfle, des galaxies collées à sa surface.  Les galaxies ne grandissent pas
(comme les pièces de monnaie de l'original), mais leurs distances, mesurées le long de la surface, augmentent toutes
dans la même proportion : vue de n'importe quelle galaxie, les autres s'éloignent à une vitesse proportionnelle à
leur distance, v = H d avec H = (da/dt) / a (loi de Hubble-Lemaître), et aucune n'est au centre.  L'original était
un film ; ici le ballon se gonfle à la demande, se tourne à la souris, et la loi de Hubble est mesurée."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre
from ..graphe import Axes

N_GALAXIES = 40
A_MIN, A_MAX = 1.0, 3.0


class BallonUnivers(Animation):
    ID = 'balloon'

    def construire(self):
        self.a = self.curseur('rayon', A_MIN, A_MAX, A_MIN, dec=3)
        self.taux = self.curseur('taux', 0.02, 0.5, 0.1, dec=3, unite='/s')
        self.c_distances = self.coche('distances', True)
        g = np.random.default_rng(9)
        v = g.normal(size=(N_GALAXIES, 3))
        self.dirs = v / np.linalg.norm(v, axis=1)[:, None]
        self.dirs[0] = (0.35, -0.6, 0.72)
        self.dirs[0] /= np.linalg.norm(self.dirs[0])
        self.vue3d = self.vue(200.0, 25.0)

    def avancer(self, dt):
        a = self.a.value() + self.taux.value() * dt
        if a >= A_MAX:
            a = A_MAX
            self.arreter()
        self.a.setValue(a)

    def distances(self) -> np.ndarray:
        """Distances le long de la surface depuis la galaxie de référence : d = a θ."""
        c = np.clip(self.dirs @ self.dirs[0], -1.0, 1.0)
        return self.a.value() * np.arccos(c)

    def valeurs(self):
        d = self.distances()
        h = self.taux.value() / self.a.value()
        return [(tr('anim_balloon_rayon_v'), nombre(self.a.value(), 3)),
                (tr('anim_balloon_h'), '%s /s' % nombre(h, 4)),
                (tr('anim_balloon_age'), '%s s' % nombre(1 / h, 1)),
                (tr('anim_balloon_plus_proche'), nombre(float(np.sort(d)[1]), 3))]

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.95)
        r = dessin.cadre(p, z[0], tr('anim_balloon_titre_ballon'))
        self.zone_rotative(r, self.vue3d)
        cx, cy = r.center().x(), r.center().y()
        R = min(r.width(), r.height()) * 0.45 * self.a.value() / A_MAX
        pe = dessin.Peintre3D(p, self.vue3d, cx, cy, R)
        pe.contour('grille', 'arc2', 0.18)
        xs, ys, zs, _ = pe.ecran(self.dirs, repere_monde=True)
        taille = min(r.width(), r.height()) * 0.011            # les galaxies ne grandissent pas
        for k in np.argsort(zs):
            devant = zs[k] >= 0
            cle = 'accent1' if k == 0 else 'accent2'
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c(cle, 1.0 if devant else 0.25))
            p.drawEllipse(QPointF(xs[k], ys[k]), taille * 1.4, taille * 0.8)
        if self.c_distances.isChecked():
            for k in np.argsort(self.distances())[1:6]:
                arc = dessin.arc(self.dirs[0], self.dirs[k], 30)
                pe.courbe(arc, 'accent1', 1.2, 0.8, arriere='cache', repere_monde=True)
        dessin.texte(p, xs[0], ys[0] - 14, tr('anim_balloon_nous'), 'accent1', fond=True)
        # loi de Hubble mesurée depuis la galaxie de référence
        r2 = dessin.cadre(p, z[1], tr('anim_balloon_titre_hubble'))
        d = self.distances()
        h = self.taux.value() / self.a.value()
        dmax = A_MAX * math.pi
        ax = Axes(r2, 0, dmax, 0, self.taux.value() * math.pi * 1.1, marges=(46, 10, 10, 30)).avec(p)
        ax.fond(p, tr('anim_balloon_axe_d'), tr('anim_balloon_axe_v'))
        ax.points([(float(x), float(h * x)) for x in d[1:]], 'accent2', 3.5, 0.9)
        ax.courbe([(0, 0), (dmax, h * dmax)], 'accent1', 1.2, 0.8, True)
