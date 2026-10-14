"""Aliasing in Wagon Wheels : une roue qui tourne, vue seulement à intervalles réguliers (images d'un film, ou mesures
d'une étoile variable) paraît tourner moins vite, s'arrêter ou même tourner à l'envers : c'est le repliement
(« aliasing »).  Entre deux images la roue tourne de Δθ = 360° Δt / P ; à cause de sa symétrie (n rayons), on ne voit
que Δθ ramené dans ]−180°/n, 180°/n].  Même piège pour la période d'une étoile variable mesurée trop rarement.
Réglages de l'original : période 1 à 10 s (5 s), 0,1 à 10 images par seconde (3)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre


def pas_apparent(periode_s: float, cadence_hz: float, rayons: int) -> float:
    """Rotation apparente par image (degrés, > 0 : même sens) d'une roue à `rayons` rayons."""
    sym = 360.0 / rayons
    d = (360.0 / (periode_s * cadence_hz)) % sym
    return d - sym if d > sym / 2 else d


def periode_apparente(periode_s: float, cadence_hz: float, rayons: int) -> float:
    """Période apparente de la roue (s) ; infinie si elle paraît immobile, négative si elle paraît reculer."""
    d = pas_apparent(periode_s, cadence_hz, rayons)
    if abs(d) < 1e-12:
        return math.inf
    return 360.0 / (d * cadence_hz)


class Repliement(Animation):
    ID = 'wagonwheel'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.periode = self.curseur('periode', 1.0, 10.0, 5.0, dec=2, unite='s')
        self.cadence = self.curseur('cadence', 0.1, 10.0, 3.0, dec=2, unite='/s')
        self.rayons = self.choix('rayons', [('anim_wagonwheel_r_%d' % n, n) for n in (1, 2, 4, 8)], 1)
        self.etat_initial()

    def etat_initial(self):
        self.t = 0.0
        self.t_image = 0.0

    def avancer(self, dt):
        self.t += dt
        pas = 1.0 / self.cadence.value()
        while self.t - self.t_image >= pas:
            self.t_image += pas

    def valeurs(self):
        n = self.rayons.currentData()
        pa = periode_apparente(self.periode.value(), self.cadence.value(), n)
        d = pas_apparent(self.periode.value(), self.cadence.value(), n)
        sens = tr('anim_wagonwheel_immobile') if not math.isfinite(pa) else (
            tr('anim_wagonwheel_avant') if pa > 0 else tr('anim_wagonwheel_arriere'))
        return [(tr('anim_wagonwheel_vrai'), '%s° / %s' % (nombre(360.0 / (self.periode.value() * self.cadence.value()), 1),
                                                            tr('anim_wagonwheel_image'))),
                (tr('anim_wagonwheel_apparent'), '%s° / %s' % (nombre(d, 1), tr('anim_wagonwheel_image'))),
                (tr('anim_wagonwheel_p_apparente'), '%s s' % nombre(abs(pa), 2) if math.isfinite(pa) else '∞'),
                (tr('anim_wagonwheel_sens'), sens)]

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.95)
        n = self.rayons.currentData()
        a_vrai = 360.0 * self.t / self.periode.value()
        a_vu = 360.0 * self.t_image / self.periode.value()
        self._roue(p, dessin.cadre(p, z[0], tr('anim_wagonwheel_titre_vraie')), a_vrai, n)
        self._roue(p, dessin.cadre(p, z[1], tr('anim_wagonwheel_titre_vue')), a_vu, n)

    @staticmethod
    def _roue(p, r, angle, n):
        cx, cy = r.center().x(), r.center().y()
        R = min(r.width(), r.height()) * 0.4
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('doux', 4.0))
        p.drawEllipse(QPointF(cx, cy), R, R)
        for k in range(n):
            a = math.radians(angle + 360.0 * k / n)
            p.setPen(dessin.stylo('accent1' if k == 0 else 'doux', 3.0))
            p.drawLine(QPointF(cx, cy), QPointF(cx + R * math.cos(a), cy - R * math.sin(a)))
        dessin.disque(p, cx, cy, 7, 'texte')
