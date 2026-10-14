"""Phase Positions Demonstrator : deux corps qu'on place librement autour du Soleil ; chacun est vu de l'autre avec
la phase que donne la géométrie.  Approché assez près de l'autre, un corps devient sa lune (il se place sur une
orbite de rayon fixe autour de lui, comme dans l'original).  Angle de phase : angle, au corps observé, entre le
Soleil et l'observateur ; fraction éclairée (1 + cos i) / 2."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre

DISTANCE_LUNE = 0.15            # en demi-largeurs de la zone (original : 30 px sur 200)
CAPTURE = 0.21                  # distance de capture en lune (original : 42 px)
PRES_DU_SOLEIL = 0.25           # distance minimale au Soleil (original : 50 px)
DEPART = {1: (0.5, 0.8), 2: (0.6, 0.2)}


def vu_de(cible, observateur) -> tuple[float, bool]:
    """Angle de phase du corps `cible` vu depuis `observateur` (Soleil à l'origine) et côté éclairé (True : droite,
    le haut de l'écran étant le nord du plan de l'orbite)."""
    i = astro.angle_de_phase(cible, (0.0, 0.0), observateur)
    dx, dy = cible[0] - observateur[0], cible[1] - observateur[1]
    droite = (dy, -dx)
    return i, (-cible[0]) * droite[0] + (-cible[1]) * droite[1] >= 0


class PositionsPhases(Animation):
    ID = 'phaseDemonstrator'
    ANIMEE = False

    def construire(self):
        self.c_orbites = self.coche('orbites', True)
        self.c_phase1 = self.coche('phase1', True)
        self.c_phase2 = self.coche('phase2', True)
        self.etat_initial()

    def etat_initial(self):
        self.pos = {1: DEPART[1], 2: DEPART[2]}
        self.lune = None              # numéro du corps devenu la lune de l'autre
        self._zone = None

    # ------------------------------------------------------------ placement (règles de l'original)
    def placer(self, ident: int, x: float, y: float):
        autre = 3 - ident
        x, y = max(-0.92, min(0.92, x)), max(-0.92, min(0.92, y))
        r = math.hypot(x, y)
        if r < PRES_DU_SOLEIL:
            a = math.atan2(y, x)
            x, y = PRES_DU_SOLEIL * math.cos(a), PRES_DU_SOLEIL * math.sin(a)
        ox, oy = self.pos[autre]
        if self.lune == autre:                         # on déplace la planète : sa lune suit
            a = math.atan2(oy - y, ox - x)
            self.pos[autre] = (x + DISTANCE_LUNE * math.cos(a), y + DISTANCE_LUNE * math.sin(a))
        else:
            if math.hypot(x - ox, y - oy) < CAPTURE:   # assez près : devient la lune de l'autre
                a = math.atan2(y - oy, x - ox)
                x, y = ox + DISTANCE_LUNE * math.cos(a), oy + DISTANCE_LUNE * math.sin(a)
                self.lune = ident
            elif self.lune == ident:
                self.lune = None
        self.pos[ident] = (x, y)
        self.rafraichir()

    def _nom(self, k: int) -> str:
        return tr('anim_phasedemonstrator_lune' if self.lune == k else 'anim_phasedemonstrator_planete', n=k)

    def valeurs(self):
        p1, p2 = self.pos[1], self.pos[2]
        i1, _ = vu_de(p1, p2)
        i2, _ = vu_de(p2, p1)
        return [(tr('anim_phasedemonstrator_vu', a=self._nom(1), b=self._nom(2)),
                 '%s (%s %%)' % (angle(i1), nombre(100 * astro.fraction_eclairee_phase(i1), 1))),
                (tr('anim_phasedemonstrator_vu', a=self._nom(2), b=self._nom(1)),
                 '%s (%s %%)' % (angle(i2), nombre(100 * astro.fraction_eclairee_phase(i2), 1))),
                (tr('anim_phasedemonstrator_dist_soleil'), '%s / %s' % (nombre(math.hypot(*p1), 2),
                                                                         nombre(math.hypot(*p2), 2))),
                (tr('anim_phasedemonstrator_dist_mutuelle'), nombre(math.hypot(p1[0] - p2[0], p1[1] - p2[1]), 2))]

    # ------------------------------------------------------------ souris
    def presser(self, pos, bouton):
        if self._zone is None or not self._zone[0].contains(pos):
            return super().presser(pos, bouton)
        _, cx, cy, s = self._zone
        meilleurs = sorted((math.hypot(pos.x() - (cx + s * x), pos.y() - (cy - s * y)), k)
                           for k, (x, y) in self.pos.items())
        if meilleurs[0][0] < 22:
            k = meilleurs[0][1]
            self._glisse = lambda q, k=k: self.placer(k, (q.x() - self._zone[1]) / self._zone[3],
                                                      (self._zone[2] - q.y()) / self._zone[3])
            return True
        return False

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.6)
        self._plan(p, dessin.cadre(p, z[0], tr('anim_phasedemonstrator_plan')))
        for k, (a, b) in enumerate(((1, 2), (2, 1))):
            r = dessin.cadre(p, z[k + 1], tr('anim_phasedemonstrator_vu', a=self._nom(a), b=self._nom(b)))
            montrer = (self.c_phase1, self.c_phase2)[a - 1].isChecked()
            rr = min(r.width(), r.height()) * 0.36
            if montrer:
                i, droite = vu_de(self.pos[a], self.pos[b])
                dessin.disque_phase(p, r.center().x(), r.center().y(), rr, i, 0.0 if droite else 180.0,
                                    ('accent3', 'accent2')[a - 1], 'nuit')
            else:
                p.setPen(dessin.stylo('grille', 1.2, pointille=True))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawEllipse(r.center(), rr, rr)
                dessin.texte(p, r.center().x(), r.center().y(), '?', 'doux')

    def _plan(self, p, r):
        s = min(r.width(), r.height()) / 2 * 0.95
        cx, cy = r.center().x(), r.center().y()
        self._zone = (QRectF(r), cx, cy, s)
        couleurs = {1: 'accent3', 2: 'accent2'}
        if self.c_orbites.isChecked():
            for k, (x, y) in self.pos.items():
                p.setPen(dessin.stylo(couleurs[k], 1.0, 0.45))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                if self.lune == k:
                    ox, oy = self.pos[3 - k]
                    p.drawEllipse(QPointF(cx + s * ox, cy - s * oy), s * DISTANCE_LUNE, s * DISTANCE_LUNE)
                else:
                    rr = math.hypot(x, y) * s
                    p.drawEllipse(QPointF(cx, cy), rr, rr)
        dessin.disque(p, cx, cy, max(8.0, s * 0.07), 'soleil')
        for k, (x, y) in self.pos.items():
            px, py = cx + s * x, cy - s * y
            rr = max(6.0, s * 0.045)
            dessin.disque(p, px, py, rr, 'nuit')
            a = math.degrees(math.atan2(-y, -x))                     # moitié éclairée tournée vers le Soleil
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c(couleurs[k]))
            p.drawPie(QRectF(px - rr, py - rr, 2 * rr, 2 * rr), int((a - 90) * 16), 180 * 16)
            dessin.texte(p, px + rr + 9, py - rr - 6, str(k), couleurs[k], fond=True)
        dessin.texte(p, r.x() + 8, r.bottom() - 10, tr('anim_phasedemonstrator_glisser'), 'doux', centre=False)
