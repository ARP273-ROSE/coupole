"""Planetary Orbit Simulator (NAAP) : une planète fictive autour du Soleil selon les lois de Kepler.
1re loi : ellipse dont le Soleil occupe un foyer (centre, foyer vide, demi-axes) ; 2e loi : aires balayées égales
en temps égaux ; 3e loi : P² = a³ (P en années, a en ua).  Vitesse par la relation de vis-viva."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre

# Orbites du Système solaire de l'original (a en ua, e)
PLANETES = (('mercure', 0.387, 0.206), ('venus', 0.723, 0.007), ('terre', 1.0, 0.017), ('mars', 1.524, 0.093),
            ('jupiter', 5.203, 0.048), ('saturne', 9.54, 0.056), ('uranus', 19.18, 0.047), ('neptune', 30.06, 0.009),
            ('pluton', 39.44, 0.249))


class OrbiteKepler(Animation):
    ID = 'kepler'
    PERIODES_PAR_S = 0.1

    def construire(self):
        self.a = self.curseur('a', 0.1, 50.0, 1.0, dec=3, unite='ua', log=True)
        self.e = self.curseur('e', 0.0, 0.7, 0.017, dec=3)
        self.choix_planete = self.choix('planete', [('anim_kepler_aucune', '')] +
                                        [('anim_planete_' + n, n) for n, _, _ in PLANETES], '')
        self.choix_planete.activated.connect(self._planete)
        self.c_centre = self.coche('centre', False)
        self.c_foyer = self.coche('foyer_vide', False)
        self.c_axes = self.coche('axes', False)
        self.c_rayon = self.coche('rayon', True)
        self.c_vitesse = self.coche('vitesse', False)
        self.c_systeme = self.coche('systeme', False)
        self.balayage = self.curseur('balayage', 0.02, 0.5, 0.125, dec=3, cle_texte='anim_kepler_balayage')
        self.c_balayer = self.coche('balayer', False)
        self.bouton('anim_kepler_effacer', self._effacer)
        self.f = 0.0
        self.aires = []                  # [(f0, f1)] balayées
        self._debut_balayage = None

    def _planete(self, *_):
        n = self.choix_planete.currentData()
        for nom, a, e in PLANETES:
            if nom == n:
                self.e.setValue(e)
                self.a.setValue(a)

    def _effacer(self):
        self.aires = []
        self._debut_balayage = None
        self.rafraichir()

    def etat_initial(self):
        self.f = 0.0
        self._effacer()

    def reglage_change(self):
        cle = (self.a.value(), self.e.value())
        if getattr(self, '_orbite_balayee', cle) != cle:
            self.aires = []                         # nouvelle orbite : les aires précédentes n'ont plus de sens
            self._debut_balayage = None
        self._orbite_balayee = cle
        super().reglage_change()

    def avancer(self, dt):
        f1 = self.f + dt * self.PERIODES_PAR_S
        if self.c_balayer.isChecked():
            if self._debut_balayage is None:
                self._debut_balayage = self.f
            s = self.balayage.value()
            while f1 - self._debut_balayage >= s:
                self.aires.append((self._debut_balayage, self._debut_balayage + s))
                self.aires = self.aires[-8:]
                self._debut_balayage += 2 * s           # une aire sur deux, comme l'original
        else:
            self._debut_balayage = None
        self.f = f1

    def valeurs(self):
        a, e = self.a.value(), self.e.value()
        o = astro.orbite(a, e, self.f)
        p = astro.periode_annees(a)
        out = [(tr('anim_kepler_periode'), '%s %s' % (nombre(p, 3), tr('anim_u_annees'))),
               (tr('anim_kepler_b'), '%s ua' % nombre(a * math.sqrt(1 - e * e), 3)),
               (tr('anim_kepler_peri_aphe'), '%s / %s ua' % (nombre(a * (1 - e), 3), nombre(a * (1 + e), 3))),
               (tr('anim_kepler_r'), '%s ua' % nombre(o['r'], 3)), (tr('anim_kepler_v'), '%s km·s⁻¹' % nombre(o['v'], 2)),
               (tr('anim_kepler_temps'), '%s %s' % (nombre(self.f * p, 3), tr('anim_u_annees')))]
        if self.aires:
            f0, f1 = self.aires[-1]
            out.append((tr('anim_kepler_aire'), '%s ua² (%s %%)' % (nombre(astro.aire_balayee(a, e, f0, f1), 4),
                                                                      nombre(100 * (f1 - f0), 1))))
        return out

    def dessiner(self, p, rect):
        a, e = self.a.value(), self.e.value()
        b = a * math.sqrt(1 - e * e)
        c = a * e
        echelle = min((rect.width() - 40) / (2 * a), (rect.height() - 40) / (2 * b))
        if self.c_systeme.isChecked():
            echelle = min(echelle, (min(rect.width(), rect.height()) - 40) / (2 * 1.15 * max(a * (1 + e), 1.0)))
        # le centre de l'ellipse au milieu ; le Soleil (foyer) en (+c, 0)
        cx, cy = rect.center().x() - c * echelle, rect.center().y()
        fx = cx + c * echelle

        def ecr(x, y):                        # x, y : coordonnées par rapport au foyer (Soleil)
            return QPointF(fx + x * echelle, cy - y * echelle)

        if self.c_systeme.isChecked():
            for nom, ap, ep in PLANETES:
                t = np.linspace(0, 2 * math.pi, 181)
                xs = ap * (np.cos(t) - ep)
                ys = ap * math.sqrt(1 - ep * ep) * np.sin(t)
                p.setPen(dessin.stylo('grille', 1.0, 0.7))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawPolyline(QPolygonF([ecr(x, y) for x, y in zip(xs, ys)]))
        # aires balayées
        for f0, f1 in self.aires:
            pts = [ecr(0, 0)]
            for f in np.linspace(f0, f1, 40):
                o = astro.orbite(a, e, f)
                pts.append(ecr(o['x'], o['y']))
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c('accent2', 0.35))
            p.drawPolygon(QPolygonF(pts))
        t = np.linspace(0, 2 * math.pi, 241)
        p.setPen(dessin.stylo('texte', 1.6))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF([ecr(a * (math.cos(x) - e), b * math.sin(x)) for x in t]))
        if self.c_axes.isChecked():
            p.setPen(dessin.stylo('accent1', 1.5))
            p.drawLine(ecr(-c - a, 0), ecr(-c + a, 0))
            p.drawLine(ecr(-c, -b), ecr(-c, b))
            dessin.texte(p, ecr(-c + a / 2, 0).x(), ecr(0, 0).y() - 10, 'a', 'accent1')
            dessin.texte(p, ecr(-c, b / 2).x() + 10, ecr(-c, b / 2).y(), 'b', 'accent1')
        if self.c_centre.isChecked():
            q = ecr(-c, 0)
            dessin.disque(p, q.x(), q.y(), 3, 'accent1')
        if self.c_foyer.isChecked():
            q = ecr(-2 * c, 0)
            p.setPen(dessin.stylo('accent1', 1.5))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(q, 4, 4)
        o = astro.orbite(a, e, self.f)
        q = ecr(o['x'], o['y'])
        if self.c_rayon.isChecked():
            p.setPen(dessin.stylo('accent2', 1.4))
            p.drawLine(ecr(0, 0), q)
        if self.c_vitesse.isChecked():
            o2 = astro.orbite(a, e, self.f + 1e-4)
            dx, dy = o2['x'] - o['x'], o2['y'] - o['y']
            n = math.hypot(dx, dy) or 1
            longueur = 0.25 * a * echelle * o['v'] / astro.orbite(a, e, 0.0)['v']
            dessin.fleche(p, q.x(), q.y(), q.x() + dx / n * longueur, q.y() - dy / n * longueur,
                          dessin.stylo('accent3', 2.0), 8)
        dessin.disque(p, fx, cy, 9, 'soleil')
        dessin.disque(p, q.x(), q.y(), 6, 'terre', bord='texte')
