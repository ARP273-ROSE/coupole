"""Synodic Period Calculator : la période sidérale P d'une planète d'après sa période synodique S (retour à la même
configuration vue de la Terre), et réciproquement.  Planète supérieure : 1/S = 1/E − 1/P ; planète inférieure :
1/S = 1/P − 1/E, E étant l'année sidérale de la Terre (365,256 jours ; l'original prenait 365,25).  L'animation
montre les deux planètes repasser en conjonction au bout de S."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre

# périodes sidérales réelles (années sidérales de la Terre), pour les préréglages
PLANETES = (('mercure', 87.969), ('venus', 224.701), ('mars', 686.980), ('jupiter', 4_332.589),
            ('saturne', 10_759.22), ('uranus', 30_685.4), ('neptune', 60_189.0))


class PeriodeSynodique(Animation):
    ID = 'synodiccalculator'
    ANNEES_PAR_S = 0.25

    def construire(self):
        self.genre = self.choix('genre', [('anim_synodiccalculator_superieure', 'sup'),
                                        ('anim_synodiccalculator_inferieure', 'inf')], 'sup')
        self.p = self.curseur('p', 0.05, 300.0, 1.8808, dec=4, unite=tr('anim_u_annees'), log=True, rafraichir=False)
        self.s = self.curseur('s', 0.05, 300.0, 2.135, dec=4, unite=tr('anim_u_annees'), log=True, rafraichir=False)
        self.choix_planete = self.choix('planete', [('anim_kepler_aucune', '')] +
                                        [('anim_planete_' + n, n) for n, _ in PLANETES], '')
        self.choix_planete.activated.connect(self._planete)
        self._sync = False
        self.p.valueChanged.connect(self._de_p)
        self.s.valueChanged.connect(self._de_s)
        self.genre.currentIndexChanged.connect(self._type)
        self.t = 0.0
        self._type()

    def superieure(self) -> bool:
        return self.genre.currentData() == 'sup'

    def _type(self, *_):
        if self.superieure():
            self.p.borner(1.0005, 300.0)
        else:
            self.p.borner(0.05, 0.9995)
        self._de_p()

    def _planete(self, *_):
        for n, j in PLANETES:
            if n == self.choix_planete.currentData():
                per = j / astro.ANNEE_SIDERALE_J
                self.genre.setCurrentIndex(self.genre.findData('sup' if per > 1 else 'inf'))
                self.p.setValue(per)

    def _de_p(self, *_):
        if self._sync:
            return
        self._sync = True
        self.s.setValue(astro.periode_synodique(self.p.value(), 1.0))
        self._sync = False
        self.rafraichir()

    def _de_s(self, *_):
        if self._sync:
            return
        per = astro.periode_siderale(self.s.value(), 1.0, self.superieure())
        if math.isfinite(per) and per > 0:
            self._sync = True
            self.p.setValue(per)
            self._sync = False
        self.rafraichir()

    def reinitialiser(self):
        super().reinitialiser()
        self._type()

    def etat_initial(self):
        self.t = 0.0

    def avancer(self, dt):
        self.t += dt * self.ANNEES_PAR_S

    def valeurs(self):
        per = self.p.value()
        s = astro.periode_synodique(per, 1.0)
        j = astro.ANNEE_SIDERALE_J
        formule = '1/S = 1/E − 1/P' if self.superieure() else '1/S = 1/P − 1/E'
        return [(tr('anim_synodiccalculator_formule'), formule),
                (tr('anim_synodiccalculator_p'), '%s %s = %s %s' % (nombre(per, 4), tr('anim_u_annees'),
                                                                    nombre(per * j, 2), tr('anim_u_jours'))),
                (tr('anim_synodiccalculator_s'), '%s %s = %s %s' % (nombre(s, 4), tr('anim_u_annees'),
                                                                    nombre(s * j, 2), tr('anim_u_jours'))),
                (tr('anim_synodiccalculator_conjonctions'), nombre(self.t / s, 2) if math.isfinite(s) else '—')]

    def dessiner(self, p, rect):
        cx, cy = rect.center().x(), rect.center().y()
        per = self.p.value()
        a = astro.demi_grand_axe(per)
        k = min(rect.width(), rect.height()) * 0.44 / max(1.0, a)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for r in (1.0, a):
            p.drawEllipse(QPointF(cx, cy), r * k, r * k)
        dessin.disque(p, cx, cy, max(7.0, k * 0.08), 'soleil')
        at, ap = 2 * math.pi * self.t, 2 * math.pi * self.t / per
        tx, ty = cx + k * math.cos(at), cy - k * math.sin(at)
        px, py = cx + k * a * math.cos(ap), cy - k * a * math.sin(ap)
        p.setPen(dessin.stylo('accent2', 1.0, 0.6, pointille=True))
        p.drawLine(QPointF(cx, cy), QPointF(cx + 1.15 * k * max(1, a) * math.cos(at),
                                            cy - 1.15 * k * max(1, a) * math.sin(at)))
        dessin.disque(p, tx, ty, 6, 'terre', bord='texte')
        dessin.disque(p, px, py, 6, 'mars', bord='texte')
        dessin.texte(p, tx, ty - 14, tr('anim_planete_terre'), fond=True)
        dessin.texte(p, px, py - 14, tr('anim_synodiccalculator_planete_p'), fond=True)
