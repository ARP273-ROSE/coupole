"""Moon Phases With Bisectors : trouver la phase avec deux plans.  Le plan perpendiculaire à la direction du
Soleil coupe la Lune (et la Terre) en une moitié éclairée et une moitié dans la nuit ; le plan perpendiculaire à
la ligne Terre–Lune la coupe en une moitié tournée vers la Terre et une moitié cachée.  Ce que l'on voit de la
Terre est la partie éclairée de la moitié tournée vers nous : les deux plans font l'angle de phase.  Étapes de
l'original : direction du Soleil, plans bissecteurs « Soleil », ombres, ligne Terre–Lune, plans « Terre–Lune »,
disque de la Lune vue de la Terre."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre

R_TERRE, R_LUNE, D_LUNE = 0.22, 0.12, 1.0          # pas à l'échelle (comme l'original)
DEMI_PLAN = 0.34


def vecteur(a_deg: float) -> np.ndarray:
    return np.array([math.cos(math.radians(a_deg)), math.sin(math.radians(a_deg)), 0.0])


def plan_bissecteur(centre, normale, demi: float = DEMI_PLAN) -> np.ndarray:
    """Carré (4 coins) du plan passant par `centre` et perpendiculaire à `normale` (dans le plan de l'orbite)."""
    n = np.asarray(normale, dtype=float)
    w = np.array([-n[1], n[0], 0.0])
    z = np.array([0.0, 0.0, 1.0])
    c = np.asarray(centre, dtype=float)
    return np.array([c + demi * (w + z), c + demi * (-w + z), c + demi * (-w - z), c + demi * (w - z)])


class PlansBissecteurs(Animation):
    ID = 'moonbisector'
    JOURS_PAR_S = 1.5

    def construire(self):
        self.vue3d = self.vue(240.0, 30.0, -89.0, 89.0)
        self.soleil = self.curseur('soleil', 0.0, 360.0, 0.0, dec=0, unite='°')
        self.lune = self.curseur('lune', 0.0, 360.0, 60.0, dec=0, unite='°')
        self.c1 = self.coche('etape1', True)
        self.c2 = self.coche('etape2', True)
        self.c3 = self.coche('etape3', True)
        self.c4 = self.coche('etape4', True)
        self.c5 = self.coche('etape5', True)
        self.c6 = self.coche('etape6', True)
        self.bouton('anim_moonbisector_dessus', lambda: self._vue(270.0, 89.0))
        self.bouton('anim_moonbisector_cote', lambda: self._vue(240.0, 30.0))

    def _vue(self, az, alt):
        self.vue3d.regler(az, alt)
        self.toile.update()

    def avancer(self, dt):
        self.lune.setValue((self.lune.value() + 360.0 * dt * self.JOURS_PAR_S / astro.MOIS_SYNODIQUE_J) % 360.0)

    def elongation(self) -> float:
        return (self.lune.value() - self.soleil.value()) % 360.0

    def valeurs(self):
        e = self.elongation()
        m = vecteur(self.lune.value()) * D_LUNE
        i = astro.angle_de_phase(m, m + 100 * vecteur(self.soleil.value()), (0.0, 0.0, 0.0))
        return [(tr('anim_lunar_applet_nom_phase'), tr('anim_phase_' + astro.nom_de_phase(e))),
                (tr('anim_moonbisector_angle_plans'), angle(i, 0)),
                (tr('anim_c_eclairee'), '%s %%' % nombre(100 * astro.fraction_eclairee_phase(i), 1))]

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.68) if rect.width() > rect.height() * 1.1 else dessin.zones(rect, 2, 10)
        self._espace(p, dessin.cadre(p, z[0], tr('anim_moonbisector_espace')))
        r = dessin.cadre(p, z[1], tr('anim_moonbisector_disque'))
        if self.c6.isChecked():
            rr = min(r.width(), r.height()) * 0.34
            dessin.phase_lune(p, r.center().x(), r.center().y(), rr, self.elongation())

    def _espace(self, p, r):
        self.zone_rotative(r, self.vue3d)
        cx, cy = r.center().x(), r.center().y()
        k = min(r.width(), r.height()) * 0.36
        v = self.vue3d
        s = vecteur(self.soleil.value())
        m = vecteur(self.lune.value()) * D_LUNE
        tm = m / np.linalg.norm(m)

        def ecran(pt):
            x, y, d = v.projeter(np.asarray(pt, dtype=float))
            return QPointF(cx + k * x[0], cy - k * y[0]), d[0]

        # orbite de la Lune
        t = np.linspace(0, 2 * math.pi, 121)
        orbite = np.stack([np.cos(t), np.sin(t), np.zeros_like(t)], axis=1) * D_LUNE
        xs, ys, _ = v.projeter(orbite)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF([QPointF(cx + k * a, cy - k * b) for a, b in zip(xs, ys)]))
        if self.c1.isChecked():                              # direction du Soleil : rayons parallèles
            for c in ((0, 0, 0), m):
                a, _ = ecran(np.asarray(c) + 0.42 * s)
                b, _ = ecran(np.asarray(c) + 0.72 * s)
                dessin.fleche(p, b.x(), b.y(), a.x(), a.y(), dessin.stylo('soleil', 1.6), 7)
        if self.c4.isChecked():
            a, _ = ecran((0, 0, 0))
            b, _ = ecran(m)
            p.setPen(dessin.stylo('accent2', 1.4, pointille=True))
            p.drawLine(a, b)
        # objets triés du fond vers l'avant
        objets = []
        for centre, rayon, cle in (((0.0, 0.0, 0.0), R_TERRE, 'terre'), (m, R_LUNE, 'lune')):
            pt, d = ecran(centre)
            objets.append((d, 'corps', (pt, rayon, cle)))
            if self.c2.isChecked():
                q = plan_bissecteur(centre, s, rayon * 1.7)
                objets.append((float(np.mean(v.projeter(q)[2])), 'plan', (q, 'soleil')))
            if self.c5.isChecked():
                q = plan_bissecteur(centre, tm, rayon * 1.7)
                objets.append((float(np.mean(v.projeter(q)[2])), 'plan', (q, 'accent2')))
        for _, genre, donnees in sorted(objets, key=lambda o: o[0]):
            if genre == 'corps':
                pt, rayon, cle = donnees
                pe = dessin.Peintre3D(p, v, pt.x(), pt.y(), k * rayon)
                dessin.disque(p, pt.x(), pt.y(), k * rayon, cle)
                if self.c3.isChecked():
                    dessin.hemisphere_nuit(pe, s, 'nuit', 0.75)
            else:
                q, cle = donnees
                xs, ys, _ = v.projeter(q)
                p.setPen(dessin.stylo(cle, 1.2, 0.9))
                p.setBrush(dessin.c(cle, 0.22))
                p.drawPolygon(QPolygonF([QPointF(cx + k * a, cy - k * b) for a, b in zip(xs, ys)]))
