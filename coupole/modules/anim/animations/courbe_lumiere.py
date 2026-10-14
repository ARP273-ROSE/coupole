"""Lightcurve Simulator : comment on construit la courbe de lumière d'une binaire à éclipses.  On observe le couple
(vu par la tranche) à différents moments et l'on reporte chaque mesure à sa phase, (temps écoulé / période) modulo 1 :
nuit après nuit, les points dessinent la courbe.  Période de 3,65 jours, comme l'original ; éclipses calculées par
l'aire de recouvrement de deux disques (l'original traçait des segments), mesures bruitées."""
from __future__ import annotations

import math
import random

from PyQt6.QtCore import QRectF

from ....core.i18n import tr
from .. import deux_corps as dc, dessin
from ..base import Animation, nombre
from ..graphe import Axes

PERIODE_J = 3.65
R1, R2 = 0.22, 0.16                 # rayons (fractions de la séparation)
S1, S2 = 1.0, 0.45                  # brillances de surface
I_DEG = 88.0
JOURS_PAR_S = 0.5                   # vitesse d'écoulement à la vitesse 1


def flux(phase: float) -> float:
    return dc.flux_deux_disques(phase, R1, R2, S1, S2, 0.0, I_DEG, 90.0) / (math.pi * (R1 * R1 * S1 + R2 * R2 * S2))


class CourbeLumiere(Animation):
    ID = 'lightcurve'

    def construire(self):
        self.c_auto = self.coche('auto', False)
        self.pas_mesure = self.curseur('intervalle', 0.05, 2.0, 0.37, dec=2, unite=tr('anim_c_jours'))
        self.bruit = self.curseur('bruit', 0.0, 0.05, 0.01, dec=3)
        self.bouton('anim_lightcurve_mesurer', self.mesurer)
        self.bouton('anim_lightcurve_effacer', self.effacer)
        self.etat_initial()

    def etat_initial(self):
        self.jours = 0.0
        self.points = []
        self._prochaine = 0.0
        self.alea = random.Random(3)

    def effacer(self):
        self.points = []
        self.rafraichir()

    def mesurer(self):
        ph = (self.jours / PERIODE_J) % 1.0
        self.points.append((ph, flux(ph) + self.alea.gauss(0.0, self.bruit.value())))
        self.rafraichir()

    def avancer(self, dt):
        self.jours += dt * JOURS_PAR_S
        if self.c_auto.isChecked():
            while self.jours >= self._prochaine:
                ph = (self._prochaine / PERIODE_J) % 1.0
                self.points.append((ph, flux(ph) + self.alea.gauss(0.0, self.bruit.value())))
                self._prochaine += self.pas_mesure.value()
            del self.points[:-2000]
        else:
            self._prochaine = self.jours

    def valeurs(self):
        ph = (self.jours / PERIODE_J) % 1.0
        return [(tr('anim_lightcurve_ecoule'), '%s %s' % (nombre(self.jours, 2), tr('anim_c_jours'))),
                (tr('anim_lightcurve_cycles'), str(int(self.jours // PERIODE_J))),
                (tr('anim_c_phase'), nombre(ph, 2)),
                (tr('anim_lightcurve_mesures'), str(len(self.points)))]

    def dessiner(self, p, rect):
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.42)
        r = dessin.cadre(p, haut, tr('anim_lightcurve_titre_couple'))
        ph = (self.jours / PERIODE_J) % 1.0
        x, y, z = dc.relative(ph, 1.0, 0.0, I_DEG, 90.0)
        cx, cy = r.center().x(), r.center().y()
        k = min(r.width() * 0.32, r.height() * 1.2)
        q = 0.4
        corps = [(-q * z, -q * x, -q * y, R1, 'soleil'), ((1 - q) * z, (1 - q) * x, (1 - q) * y, R2, 'accent3')]
        for _, xx, yy, rr, cle in sorted(corps, key=lambda c: c[0]):
            dessin.disque(p, cx + xx * k, cy - yy * k, rr * k, cle, bord='fond')
        r2 = dessin.cadre(p, QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height()),
                          tr('anim_lightcurve_titre_courbe'))
        ax = Axes(r2, 0, 1, 0.45, 1.08, marges=(46, 8, 10, 26)).avec(p)
        ax.fond(p, tr('anim_c_phase'), tr('anim_c_flux_relatif'), dec_x=1, dec_y=1)
        ax.points(self.points, 'accent2', 2.4, 0.9)
        ax.verticale(ph, 'accent3', 1.2, False)
