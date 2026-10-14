"""Three Views Simulator : la phase dépend du point de vue.  La Lune sur son orbite (vue de dessus, le Soleil
loin à droite) est montrée vue de la Terre, vue du Soleil (toujours pleine) et vue d'un point quelconque de
l'espace (l'œil qu'on fait tourner autour de la Lune).  Pour chaque point de vue, l'angle de phase est l'angle, au
centre de la Lune, entre la direction du Soleil et celle de l'observateur."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre


def vue_depuis(psi: float) -> tuple[float, bool]:
    """Observateur lointain dans la direction ψ (degrés, vue de dessus, sens trigonométrique depuis la direction du
    Soleil) vue de la Lune : angle de phase et côté éclairé (True : à droite, le nord de l'écliptique en haut)."""
    u = (math.cos(math.radians(psi)), math.sin(math.radians(psi)))
    i = astro.angle_de_phase((0.0, 0.0), (1.0, 0.0), u)
    return i, math.sin(math.radians(psi)) < 0


def psi_de_la_terre(elongation: float) -> float:
    """Direction de la Terre vue de la Lune quand la Lune est à l'élongation e : ψ = e + 180°."""
    return (elongation + 180.0) % 360.0


class TroisVues(Animation):
    ID = 'moonphases'
    JOURS_PAR_S = 2.0

    def construire(self):
        self.phase = self.curseur('phase', 0.0, 360.0, 45.0, dec=1, unite='°', cle_texte='anim_lunar_applet_phase')
        self.psi = self.curseur('psi', 0.0, 360.0, 270.0, dec=1, unite='°')
        self._dessus = None

    def avancer(self, dt):
        self.phase.setValue((self.phase.value() + 360.0 * dt * self.JOURS_PAR_S / astro.MOIS_SYNODIQUE_J) % 360.0)

    def _points_de_vue(self):
        e = self.phase.value()
        return {'terre': vue_depuis(psi_de_la_terre(e)), 'soleil': vue_depuis(0.0), 'libre': vue_depuis(self.psi.value())}

    def valeurs(self):
        v = self._points_de_vue()
        out = []
        for cle in ('terre', 'soleil', 'libre'):
            i, _ = v[cle]
            out.append((tr('anim_moonphases_vu_' + cle), '%s (%s %%)' % (angle(i), nombre(100 * astro.fraction_eclairee_phase(i), 1))))
        out.append((tr('anim_lunar_applet_nom_phase'), tr('anim_phase_' + astro.nom_de_phase(self.phase.value()))))
        return out

    # ------------------------------------------------------------ souris
    def presser(self, pos, bouton):
        if self._dessus is not None and self._dessus[0].contains(pos):
            _, cx, cy, ro, mx, my, ox, oy = self._dessus
            if math.hypot(pos.x() - ox, pos.y() - oy) < 16:
                self._glisse = self._tirer_oeil
            else:
                self._glisse = self._tirer_lune
            self._glisse(pos)
            return True
        return super().presser(pos, bouton)

    def _tirer_lune(self, pos):
        _, cx, cy = self._dessus[:3]
        self.phase.setValue(math.degrees(math.atan2(cy - pos.y(), pos.x() - cx)) % 360.0)

    def _tirer_oeil(self, pos):
        mx, my = self._dessus[4:6]
        self.psi.setValue(math.degrees(math.atan2(my - pos.y(), pos.x() - mx)) % 360.0)

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 3, 0.58)
        self._orbite(p, dessin.cadre(p, z[0], tr('anim_moonphases_vue_dessus')))
        v = self._points_de_vue()
        for k, cle in enumerate(('terre', 'soleil', 'libre')):
            r = dessin.cadre(p, z[k + 1], tr('anim_moonphases_vu_' + cle))
            i, droite = v[cle]
            rr = min(r.width(), r.height()) * 0.38
            dessin.disque_phase(p, r.center().x(), r.center().y(), rr, i, 0.0 if droite else 180.0)

    def _orbite(self, p, r):
        cx, cy = r.center().x() - r.width() * 0.08, r.center().y()
        ro = min(r.width() * 0.8, r.height()) * 0.36
        for k in (-0.8, -0.4, 0.0, 0.4, 0.8):                                    # lumière du Soleil
            y = cy + k * ro
            dessin.fleche(p, r.right() - 4, y, r.right() - ro * 0.4, y, dessin.stylo('soleil', 1.3, 0.7), 6)
        dessin.texte(p, r.right() - ro * 0.22, r.y() + 12, tr('anim_moonphases_vers_soleil'), 'soleil')
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), ro, ro)
        rt = ro * 0.16
        dessin.disque(p, cx, cy, rt, 'terre')
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('nuit', 0.7))
        p.drawPie(QRectF(cx - rt, cy - rt, 2 * rt, 2 * rt), 90 * 16, 180 * 16)
        e = math.radians(self.phase.value())
        mx, my = cx + ro * math.cos(e), cy - ro * math.sin(e)
        rl = max(6.0, rt * 0.5)
        dessin.disque(p, mx, my, rl, 'nuit')
        p.setBrush(dessin.c('lune'))
        p.drawPie(QRectF(mx - rl, my - rl, 2 * rl, 2 * rl), -90 * 16, 180 * 16)
        # œil libre
        ps = math.radians(self.psi.value())
        do = ro * 0.55
        ox, oy = mx + do * math.cos(ps), my - do * math.sin(ps)
        p.setPen(dessin.stylo('accent2', 1.2, 0.7, pointille=True))
        p.drawLine(QPointF(ox, oy), QPointF(mx, my))
        p.setPen(dessin.stylo('accent3', 1.0, 0.5, pointille=True))
        p.drawLine(QPointF(cx, cy), QPointF(mx, my))
        dessin.disque(p, ox, oy, 7, 'accent2', bord='texte')
        dessin.texte(p, ox, oy - 16, tr('anim_basketball_oeil'), 'accent2', fond=True)
        self._dessus = (QRectF(r), cx, cy, ro, mx, my, ox, oy)
