"""Milky Way Rotational Velocity : vitesse de rotation de la Voie lactée selon la distance au centre, et masse
contenue dans le cercle de rayon R : M = v² R / G (répartition sphérique).  La courbe reste presque plate loin du
centre, là où l'on ne voit presque plus d'étoiles : si toute la masse était au centre, v décroîtrait comme 1/√R
(courbe képlérienne).  C'est un indice de matière noire.  Courbe : partie centrale de l'original (R < 4 kpc), puis
mesures de Gaia (Eilers et al. 2019, v = 229 − 1,7 (R − 8,122) km/s de 5 à 25 kpc) ; l'original montait jusqu'à
292 km/s à 39 kpc, ce que les mesures récentes ne confirment pas."""
from __future__ import annotations

import bisect
import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre
from ..graphe import Axes
from .gravitation import scientifique

KPC_M = astro.PC_M * 1000.0
G_KPC = astro.GM_SOLEIL / (KPC_M * 1e6)          # G en kpc (km/s)² / M☉ : 4,3009 × 10⁻⁶
R_SOLEIL_KPC = 8.122                              # GRAVITY 2018
R_MAX = 25.0
# partie centrale de l'original : courbes de Bézier quadratiques (pixels), échelles 0,055 031 kpc et 1,107 01 km/s
_DEPART = (7.75, 0.0)
_BEZIER = ((15.9, -134.3, 20.7, -219.8), (21.5, -233.1, 34.7, -222.9), (49.1, -211.7, 59.0, -196.2),
           (69.2, -180.0, 86.8, -183.2), (95.9, -184.8, 110.0, -201.5))
_SX, _SY = 0.055_031_446_540_880_505, -1.107_011_070_110_701_2


def _table_interne():
    x0, y0 = _DEPART
    pts = [(0.0, 0.0)]
    for cx, cy, ax, ay in _BEZIER:
        for k in range(1, 41):
            t = k / 40
            x = (1 - t) ** 2 * x0 + 2 * t * (1 - t) * cx + t * t * ax
            y = (1 - t) ** 2 * y0 + 2 * t * (1 - t) * cy + t * t * ay
            pts.append((x * _SX, y * _SY))
        x0, y0 = ax, ay
    return pts


_INTERNE = _table_interne()
_RS = [r for r, _ in _INTERNE]


def v_eilers(r: float) -> float:
    return 229.0 - 1.7 * (r - R_SOLEIL_KPC)


def v_interne(r: float) -> float:
    i = max(1, min(len(_RS) - 1, bisect.bisect_left(_RS, r)))
    (r0, v0), (r1, v1) = _INTERNE[i - 1], _INTERNE[i]
    return v0 + (v1 - v0) * (r - r0) / (r1 - r0) if r1 > r0 else v1


def vitesse(r: float) -> float:
    """Vitesse circulaire (km/s) à r kpc du centre."""
    if r >= 5.0:
        return v_eilers(r)
    if r <= 4.0:
        return v_interne(r)
    f = r - 4.0
    return (1 - f) * v_interne(r) + f * v_eilers(r)


def masse(r: float) -> float:
    """Masse (M☉) contenue dans la sphère de rayon r kpc : v² r / G."""
    return vitesse(r) ** 2 * r / G_KPC


class RotationGalaxie(Animation):
    ID = 'milkywayrotationalvelocity'
    ANIMEE = False

    def construire(self):
        self.r = self.curseur('rayon', 0.5, R_MAX, R_SOLEIL_KPC, dec=2, unite='kpc')
        self.c_kepler = self.coche('kepler', True)
        self._axes = None

    def valeurs(self):
        r = self.r.value()
        return [(tr('anim_milkywayrotationalvelocity_r'), '%s kpc (%s %s)' % (nombre(r, 2), nombre(r * 1000 * astro.PC_EN_AL, 0),
                                                                           tr('anim_spectroparallax_al'))),
                (tr('anim_milkywayrotationalvelocity_v'), '%s km/s' % nombre(vitesse(r), 1)),
                (tr('anim_milkywayrotationalvelocity_m'), '%s M☉' % scientifique(masse(r))),
                (tr('anim_milkywayrotationalvelocity_tour'), '%s %s' % (
                    nombre(2 * math.pi * r * KPC_M / (vitesse(r) * 1000) / (astro.ANNEE_JULIENNE_J * 86400) / 1e6, 0),
                    tr('anim_milkywayrotationalvelocity_ma')))]

    def presser(self, pos, bouton):
        if self._axes is not None and self._axes.r.adjusted(-10, -10, 10, 10).contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        self.r.setValue(self._axes.x_de_px(pos.x()))

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.62)
        r = dessin.cadre(p, z[0], tr('anim_milkywayrotationalvelocity_titre_courbe'))
        ax = Axes(r, 0, R_MAX, 0, 300, marges=(46, 10, 12, 30)).avec(p)
        self._axes = ax
        ax.fond(p, tr('anim_milkywayrotationalvelocity_axe_r'), tr('anim_milkywayrotationalvelocity_axe_v'))
        ax.courbe([(x / 10, vitesse(x / 10)) for x in range(0, int(R_MAX * 10) + 1)], 'accent1', 2.5)
        rr = self.r.value()
        if self.c_kepler.isChecked():
            v0 = vitesse(rr)
            ax.courbe([(x / 10, v0 * math.sqrt(rr / (x / 10))) for x in range(int(rr * 10), int(R_MAX * 10) + 1)],
                      'accent2', 1.6, 0.9, True)
            dessin.texte(p, ax.px(R_MAX) - 4 - p.fontMetrics().horizontalAdvance(tr('anim_milkywayrotationalvelocity_k')),
                         ax.py(v0 * math.sqrt(rr / R_MAX)) - 8, tr('anim_milkywayrotationalvelocity_k'), 'accent2',
                         centre=False)
        ax.verticale(R_SOLEIL_KPC, 'doux', 1.0, True, tr('anim_milkywayrotationalvelocity_soleil'))
        ax.verticale(rr, 'accent3', 1.2, True)
        ax.points([(rr, vitesse(rr))], 'accent3', 6, 1.0)
        self._galaxie(p, dessin.cadre(p, z[1], tr('anim_milkywayrotationalvelocity_titre_galaxie')))

    def _galaxie(self, p, r):
        cx, cy = r.center().x(), r.center().y()
        k = min(r.width(), r.height()) * 0.46 / R_MAX
        for i in range(2):                                  # deux bras schématiques (spirale logarithmique)
            pts = []
            for n in range(120):
                t = n / 119 * 3.6
                rr = 2.0 * math.exp(0.33 * t) * k
                a = t + math.pi * i
                pts.append(QPointF(cx + rr * math.cos(a), cy - rr * math.sin(a)))
            p.setPen(dessin.stylo('equateur', 6.0, 0.25))
            p.drawPolyline(pts)
        dessin.disque(p, cx, cy, 2.5 * k, 'soleil', alpha=0.5)
        p.setPen(dessin.stylo('accent3', 1.5, None, True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), self.r.value() * k, self.r.value() * k)
        dessin.disque(p, cx + R_SOLEIL_KPC * k, cy, 4, 'accent1', bord='texte')
        dessin.texte(p, cx + R_SOLEIL_KPC * k, cy + 14, tr('anim_milkywayrotationalvelocity_soleil'), 'accent1', fond=True)
