"""Kepler's Third Law : la période d'une planète d'après son demi-grand axe, et réciproquement.  P² = a³ / M (P en
années, a en unités astronomiques, M masse de l'étoile en masses solaires ; M = 1 pour le Soleil, comme
l'original).  Graphique logarithmique : la loi est une droite de pente 3/2, sur laquelle tombent les planètes."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre

# demi-grand axe (ua) et période sidérale (jours) des planètes (valeurs de référence courantes)
PLANETES = (('mercure', 0.387_098, 87.969), ('venus', 0.723_332, 224.701), ('terre', 1.000_001, 365.256),
            ('mars', 1.523_679, 686.980), ('jupiter', 5.2026, 4_332.589), ('saturne', 9.5549, 10_759.22),
            ('uranus', 19.2184, 30_685.4), ('neptune', 30.1104, 60_189.0), ('pluton', 39.48, 90_560.0))
A_MIN, A_MAX = 0.01, 1000.0


class Kepler3(Animation):
    ID = 'keplers_third'
    ANIMEE = False

    def construire(self):
        self.a = self.curseur('a', A_MIN, A_MAX, 1.0, dec=4, unite='ua', log=True, rafraichir=False)
        self.p = self.curseur('p', astro.periode_annees(A_MIN), astro.periode_annees(A_MAX), 1.0, dec=4,
                              unite=tr('anim_u_annees'), log=True, rafraichir=False)
        self.m = self.curseur('masse', 0.1, 10.0, 1.0, dec=2, unite='M☉', log=True, rafraichir=False)
        self.choix_planete = self.choix('planete', [('anim_kepler_aucune', '')] +
                                        [('anim_planete_' + n, n) for n, _, _ in PLANETES], '')
        self.choix_planete.activated.connect(self._planete)
        self._sync = False
        self.a.valueChanged.connect(self._de_a)
        self.p.valueChanged.connect(self._de_p)
        self.m.valueChanged.connect(self._de_a)
        self._de_a()

    def _planete(self, *_):
        for n, a, _ in PLANETES:
            if n == self.choix_planete.currentData():
                self.a.setValue(a)

    def _de_a(self, *_):
        if self._sync:
            return
        self._sync = True
        self.p.setValue(astro.periode_annees(self.a.value(), self.m.value()))
        self._sync = False
        self.rafraichir()

    def _de_p(self, *_):
        if self._sync:
            return
        self._sync = True
        self.a.setValue(astro.demi_grand_axe(self.p.value(), self.m.value()))
        self._sync = False
        self.rafraichir()

    def reinitialiser(self):
        super().reinitialiser()
        self._de_a()

    def valeurs(self):
        a, m = self.a.value(), self.m.value()
        p = astro.periode_annees(a, m)
        return [(tr('anim_keplers_third_a'), '%s ua' % nombre(a, 4)),
                (tr('anim_keplers_third_p'), '%s %s (%s %s)' % (nombre(p, 4), tr('anim_u_annees'),
                                                               nombre(p * astro.ANNEE_SIDERALE_J, 1), tr('anim_u_jours'))),
                (tr('anim_keplers_third_verif'), 'P² = %s ; a³ / M = %s' % (nombre(p * p, 4), nombre(a ** 3 / m, 4)))]

    def dessiner(self, p, rect):
        x0, x1 = rect.x() + 54, rect.right() - 14
        y0, y1 = rect.y() + 14, rect.bottom() - 34
        la0, la1 = math.log10(A_MIN), math.log10(A_MAX)
        lp0, lp1 = math.log10(astro.periode_annees(A_MIN) / 3.2), math.log10(astro.periode_annees(A_MAX) * 3.2)

        def xy(a, per):
            return QPointF(x0 + (x1 - x0) * (math.log10(a) - la0) / (la1 - la0),
                           y1 - (y1 - y0) * (math.log10(per) - lp0) / (lp1 - lp0))

        p.setPen(dessin.stylo('grille', 1.0, 0.6))
        dessin.police(p, 0.75)
        for k in range(-2, 4):
            q = xy(10.0 ** k, 1.0)
            p.drawLine(QPointF(q.x(), y0), QPointF(q.x(), y1))
            dessin.texte(p, q.x(), y1 + 12, nombre(10.0 ** k, max(0, -k)), 'doux')
        for k in range(-3, 6):
            q = xy(1.0, 10.0 ** k)
            if y0 <= q.y() <= y1:
                p.drawLine(QPointF(x0, q.y()), QPointF(x1, q.y()))
                dessin.texte(p, x0 - 24, q.y(), nombre(10.0 ** k, max(0, -k)), 'doux')
        dessin.texte(p, (x0 + x1) / 2, y1 + 26, tr('anim_keplers_third_axe_a'), 'doux')
        dessin.texte(p, x0 + 4, y0 + 2, tr('anim_keplers_third_axe_p'), 'doux', centre=False)
        dessin.police(p, 1 / 0.75)
        m = self.m.value()
        p.setPen(dessin.stylo('accent2', 1.8))
        p.drawPolyline(QPolygonF([xy(10 ** (la0 + (la1 - la0) * i / 50), astro.periode_annees(
            10 ** (la0 + (la1 - la0) * i / 50), m)) for i in range(51)]))
        dessin.police(p, 0.8)
        for n, a, pj in PLANETES:
            q = xy(a, pj / astro.ANNEE_SIDERALE_J)
            dessin.disque(p, q.x(), q.y(), 4, dessin.c('soleil' if n == self.choix_planete.currentData() else 'accent1'))
            dessin.reserver(p, q.x(), q.y(), 4)
        for n, a, pj in PLANETES:                      # noms placés sans chevauchement (placeur commun)
            q = xy(a, pj / astro.ANNEE_SIDERALE_J)
            dessin.etiquette(p, q.x(), q.y(), tr('anim_planete_' + n), 'doux', 5)
        dessin.police(p, 1 / 0.8)
        q = xy(self.a.value(), astro.periode_annees(self.a.value(), m))
        p.setPen(dessin.stylo('accent3', 1.0, 0.8, pointille=True))
        p.drawLine(QPointF(q.x(), y1), q)
        p.drawLine(QPointF(x0, q.y()), q)
        dessin.disque(p, q.x(), q.y(), 6, 'accent3', bord='texte')
