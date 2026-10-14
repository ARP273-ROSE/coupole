"""Influence of Planets on the Sun : le Soleil tourne autour du centre de masse du Système solaire.  Chaque
planète l'attire vers elle : le centre du Soleil décrit une boucle compliquée, à moins de ≈ 2,2 rayons solaires du
centre de masse, menée surtout par Jupiter (12 ans) et Saturne (29 ans).  Positions vraies des planètes (éléments
moyens de Standish, JPL, 1800–2050) et masses de l'éphéméride DE440 ; l'original plaçait les planètes au hasard sur
des cercles, avec des masses et des distances plus anciennes."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, deux_corps as dc, dessin
from ..base import Animation, nombre

PLANETES = ('mercure', 'venus', 'terre', 'mars', 'jupiter', 'saturne', 'uranus', 'neptune')
R_SOLEIL_UA = astro.R_SOLEIL_KM / astro.UA_KM
TRAINEE_ANS = 40.0
PAS_ANS = 0.1


class BarycentreSolaire(Animation):
    ID = 'ca_extrasolarplanets_starwobble'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.annee = self.curseur('annee', 1800.0, 2050.0, 2026.0, dec=1)
        self.vitesse_ans = self.curseur('ans_par_s', 0.1, 10.0, 2.0, dec=1, unite=tr('anim_c_ans') + '/s', log=True)
        self.cases = {n: self.coche('p_' + n, n in ('jupiter', 'saturne'))
                      for n in PLANETES}
        self.trainee = []                         # (année, x, y) en rayons solaires
        self._cle = None

    def choisies(self):
        return [n for n in PLANETES if self.cases[n].isChecked()]

    def position(self, annee):
        x, y, _ = dc.soleil_barycentrique((annee - 2000.0) / 100.0, self.choisies())
        return x / R_SOLEIL_UA, y / R_SOLEIL_UA

    def _recalculer(self):
        a1 = self.annee.value()
        n = int(TRAINEE_ANS / PAS_ANS)
        a0 = max(1800.0, a1 - TRAINEE_ANS)
        self.trainee = [(a, *self.position(a)) for a in (a0 + PAS_ANS * k for k in range(n + 1)) if a <= a1]
        self._cle = (tuple(self.choisies()), a1)

    def _completer(self):
        a1 = self.annee.value()
        cle = tuple(self.choisies())
        if self._cle is None or self._cle[0] != cle or not self.trainee or a1 < self.trainee[-1][0] or \
                a1 - self.trainee[-1][0] > TRAINEE_ANS:
            self._recalculer()
            return
        a = self.trainee[-1][0]
        while a + PAS_ANS <= a1:
            a += PAS_ANS
            self.trainee.append((a, *self.position(a)))
        while self.trainee and self.trainee[0][0] < a1 - TRAINEE_ANS:
            self.trainee.pop(0)
        self._cle = (cle, a1)

    def avancer(self, dt):
        a = self.annee.value() + dt * self.vitesse_ans.value()
        if a > 2050.0:
            a = 1800.0
        self.annee.setValue(a)

    def valeurs(self):
        x, y = self.position(self.annee.value())
        d = math.hypot(x, y)
        a = self.annee.value()
        return [(tr('anim_ca_extrasolarplanets_starwobble_date'), nombre(a, 1).replace('\u202f', '').replace(' ', '')),
                (tr('anim_ca_extrasolarplanets_starwobble_distance'),
                 '%s R☉ = %s km' % (nombre(d, 3), nombre(d * astro.R_SOLEIL_KM, 0))),
                (tr('anim_ca_extrasolarplanets_starwobble_dehors'),
                 tr('anim_oui') if d > 1 else tr('anim_non'))]

    def dessiner(self, p, rect):
        self._completer()
        r = dessin.cadre(p, rect, tr('anim_ca_extrasolarplanets_starwobble_titre'))
        cx, cy = r.center().x(), r.center().y()
        k = min(r.width(), r.height()) / 2 / 2.6               # 2,6 rayons solaires au bord
        p.setPen(dessin.stylo('grille', 1.0, None, True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for n in (1, 2):
            p.drawEllipse(QPointF(cx, cy), n * k, n * k)
            dessin.texte(p, cx + n * k * 0.707 + 4, cy - n * k * 0.707 - 4, '%d R☉' % n, 'doux', centre=False)
        x, y = self.position(self.annee.value())
        sx, sy = cx + x * k, cy - y * k
        dessin.disque(p, sx, sy, k, 'soleil', alpha=0.35)
        p.setPen(dessin.stylo('soleil', 1.2))
        p.drawEllipse(QPointF(sx, sy), k, k)
        if len(self.trainee) > 1:
            p.setPen(dessin.stylo('accent1', 1.6))
            p.drawPolyline(QPolygonF([QPointF(cx + tx * k, cy - ty * k) for _, tx, ty in self.trainee]))
        dessin.disque(p, sx, sy, 3.5, 'accent1')
        p.setPen(dessin.stylo('accent3', 2.0))
        p.drawLine(QPointF(cx - 7, cy), QPointF(cx + 7, cy))
        p.drawLine(QPointF(cx, cy - 7), QPointF(cx, cy + 7))
        dessin.texte(p, cx, cy + 16, tr('anim_c_barycentre'), 'accent3', fond=True)
        dessin.texte(p, r.left() + 8, r.bottom() - 8, tr('anim_ca_extrasolarplanets_starwobble_trainee'), 'doux',
                     centre=False)
