"""Phases of Venus et Ptolemaic Phases of Venus : l'aspect de Vénus au télescope, dans le système de Copernic
(Vénus et la Terre autour du Soleil) et dans celui de Ptolémée (Terre immobile ; Vénus sur un épicycle dont le
centre reste sur la ligne Terre–Soleil).  Chez Copernic, Vénus montre toutes les phases et sa taille apparente
varie de 10″ à 60″ environ : gibbeuse et petite près de la conjonction supérieure, fin croissant et grosse près de
la conjonction inférieure — ce que Galilée a vu en 1610.  Chez Ptolémée, elle reste toujours entre la Terre et le
Soleil : jamais plus qu'un croissant."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre
from .positions_phases import vu_de

A_VENUS = 0.723_332                     # demi-grand axe moyen (ua)
R_VENUS_KM = 6_051.8                    # rayon moyen de Vénus
# modèle de Ptolémée de l'original : rayons de l'orbite du Soleil, du déférent et de l'épicycle ; période de Vénus
PTOLEMEE = {'soleil': 290.0, 'deferent': 150.0, 'epicycle': 108.0, 'periode': 0.615_178}


def elongation_signee(planete, terre) -> float:
    """Élongation de la planète vue de la Terre, signée : > 0 à l'est du Soleil (étoile du soir), < 0 à l'ouest."""
    lp = math.atan2(planete[1] - terre[1], planete[0] - terre[0])
    ls = math.atan2(-terre[1], -terre[0])
    return astro.mod180(math.degrees(lp - ls))


def copernic(angle_venus: float, angle_terre: float) -> dict:
    v = (A_VENUS * math.cos(math.radians(angle_venus)), A_VENUS * math.sin(math.radians(angle_venus)))
    t = (math.cos(math.radians(angle_terre)), math.sin(math.radians(angle_terre)))
    d = math.hypot(v[0] - t[0], v[1] - t[1])
    i, droite = vu_de(v, t)
    return {'venus': v, 'terre': t, 'soleil': (0.0, 0.0), 'distance': d, 'i': i, 'droite': droite,
            'elongation': elongation_signee(v, t),
            'diametre': 2 * math.degrees(math.asin(R_VENUS_KM / (d * astro.UA_KM))) * 3600.0}


def ptolemee(angle_soleil: float, angle_venus: float) -> dict:
    """Terre à l'origine ; Soleil sur son cercle ; centre de l'épicycle sur la ligne Terre–Soleil."""
    s = math.radians(angle_soleil)
    soleil = (PTOLEMEE['soleil'] * math.cos(s), PTOLEMEE['soleil'] * math.sin(s))
    c = (PTOLEMEE['deferent'] * math.cos(s), PTOLEMEE['deferent'] * math.sin(s))
    v = (c[0] + PTOLEMEE['epicycle'] * math.cos(math.radians(angle_venus)),
         c[1] + PTOLEMEE['epicycle'] * math.sin(math.radians(angle_venus)))
    t = (0.0, 0.0)
    i = astro.angle_de_phase(v, soleil, t)
    dx, dy = v[0], v[1]
    droite = (soleil[0] - v[0]) * dy + (soleil[1] - v[1]) * (-dx) >= 0
    return {'venus': v, 'terre': t, 'soleil': soleil, 'centre': c, 'distance': math.hypot(*v), 'i': i,
            'droite': droite, 'elongation': astro.mod180(math.degrees(math.atan2(v[1], v[0]) - s))}


class _Venus(Animation):
    ANNEES_PAR_S = 0.1

    def _telescope(self, p, r, g, echelle):
        cx, cy = r.center().x(), r.center().y()
        rr = min(r.width(), r.height()) * 0.42 * echelle
        p.setPen(dessin.stylo('grille', 1.0, 0.5))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), min(r.width(), r.height()) * 0.46, min(r.width(), r.height()) * 0.46)
        dessin.disque_phase(p, cx, cy, max(2.0, rr), g['i'], 0.0 if g['droite'] else 180.0, 'etoile', 'nuit')

    def _valeurs_communes(self, g):
        e = g['elongation']
        return [(tr('anim_c_elongation'), '%s %s' % (angle(abs(e), 1), tr('anim_est' if e > 0 else 'anim_ouest'))),
                (tr('anim_c_angle_phase'), angle(g['i'], 1)),
                (tr('anim_c_eclairee'), '%s %%' % nombre(100 * astro.fraction_eclairee_phase(g['i']), 1))]


class PhasesVenus(_Venus):
    ID = 'venusphases'

    def construire(self):
        self.av = self.curseur('venus', 0.0, 360.0, math.degrees(0.5), dec=1, unite='°')
        self.at = self.curseur('terre', 0.0, 360.0, 0.0, dec=1, unite='°')
        self._plan = None

    def avancer(self, dt):
        da = dt * self.ANNEES_PAR_S
        self.av.setValue((self.av.value() + 360.0 * da / A_VENUS ** 1.5) % 360.0)
        self.at.setValue((self.at.value() + 360.0 * da) % 360.0)

    def valeurs(self):
        g = copernic(self.av.value(), self.at.value())
        return [(tr('anim_c_distance'), '%s ua' % nombre(g['distance'], 3))] + self._valeurs_communes(g) + [
            (tr('anim_venusphases_diametre'), '%s″' % nombre(g['diametre'], 1))]

    def presser(self, pos, bouton):
        if self._plan is not None and self._plan[0].contains(pos):
            _, cx, cy, s = self._plan
            g = copernic(self.av.value(), self.at.value())
            dv = math.hypot(pos.x() - cx - s * g['venus'][0], pos.y() - cy + s * g['venus'][1])
            dt_ = math.hypot(pos.x() - cx - s * g['terre'][0], pos.y() - cy + s * g['terre'][1])
            cible = self.av if dv < dt_ else self.at
            self._glisse = lambda q, c=cible: c.setValue(
                math.degrees(math.atan2(self._plan[2] - q.y(), q.x() - self._plan[1])) % 360.0)
            return True
        return super().presser(pos, bouton)

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.8)
        r = dessin.cadre(p, z[0], tr('anim_venusphases_orbites'))
        g = copernic(self.av.value(), self.at.value())
        cx, cy = r.center().x(), r.center().y()
        s = min(r.width(), r.height()) * 0.44
        self._plan = (QRectF(r), cx, cy, s)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for a in (A_VENUS, 1.0):
            p.drawEllipse(QPointF(cx, cy), a * s, a * s)
        dessin.disque(p, cx, cy, max(8.0, s * 0.07), 'soleil')
        vx, vy = cx + s * g['venus'][0], cy - s * g['venus'][1]
        tx, ty = cx + s * g['terre'][0], cy - s * g['terre'][1]
        p.setPen(dessin.stylo('accent2', 1.0, 0.6, pointille=True))
        p.drawLine(QPointF(tx, ty), QPointF(vx, vy))
        dessin.disque(p, vx, vy, 7, 'etoile', bord='doux')
        dessin.disque(p, tx, ty, 7, 'terre', bord='texte')
        dessin.texte(p, vx, vy - 15, tr('anim_planete_venus'), 'texte', fond=True)
        dessin.texte(p, tx, ty - 15, tr('anim_planete_terre'), 'texte', fond=True)
        r2 = dessin.cadre(p, z[1], tr('anim_venusphases_telescope'))
        self._telescope(p, r2, g, (1.0 - A_VENUS) / g['distance'])


class PhasesVenusPtolemee(_Venus):
    ID = 'ptolemaic'

    def construire(self):
        self.t = 0.0

    def etat_initial(self):
        self.t = 0.0

    def avancer(self, dt):
        self.t += dt * self.ANNEES_PAR_S

    def _g(self):
        return ptolemee(360.0 * self.t, 360.0 * self.t / PTOLEMEE['periode'])

    def valeurs(self):
        g = self._g()
        return [(tr('anim_ptolemaic_temps'), '%s %s' % (nombre(self.t, 2), tr('anim_u_annees')))] + \
            self._valeurs_communes(g) + [(tr('anim_ptolemaic_elong_max'), angle(math.degrees(math.asin(
                PTOLEMEE['epicycle'] / PTOLEMEE['deferent'])), 1))]

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.8)
        r = dessin.cadre(p, z[0], tr('anim_ptolemaic_modele'))
        g = self._g()
        cx, cy = r.center().x(), r.center().y()
        s = min(r.width(), r.height()) * 0.46 / PTOLEMEE['soleil']
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for rr in (PTOLEMEE['deferent'], PTOLEMEE['soleil']):
            p.drawEllipse(QPointF(cx, cy), rr * s, rr * s)
        ex, ey = cx + s * g['centre'][0], cy - s * g['centre'][1]
        p.setPen(dessin.stylo('accent2', 1.0, 0.8))
        p.drawEllipse(QPointF(ex, ey), PTOLEMEE['epicycle'] * s, PTOLEMEE['epicycle'] * s)
        sx, sy = cx + s * g['soleil'][0], cy - s * g['soleil'][1]
        p.setPen(dessin.stylo('soleil', 1.0, 0.5, pointille=True))
        p.drawLine(QPointF(cx, cy), QPointF(sx, sy))
        dessin.disque(p, sx, sy, max(8.0, s * 18), 'soleil')
        dessin.disque(p, cx, cy, 7, 'terre', bord='texte')
        dessin.disque(p, ex, ey, 2.5, 'accent2')
        vx, vy = cx + s * g['venus'][0], cy - s * g['venus'][1]
        dessin.disque(p, vx, vy, 6, 'etoile', bord='doux')
        dessin.texte(p, vx, vy - 14, tr('anim_planete_venus'), 'texte', fond=True)
        r2 = dessin.cadre(p, z[1], tr('anim_venusphases_telescope'))
        self._telescope(p, r2, g, (PTOLEMEE['deferent'] - PTOLEMEE['epicycle']) / g['distance'])
