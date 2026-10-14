"""Tidal Bulge Simulation : la Lune, le Soleil et la rotation de la Terre produisent les marées.  Vue du pôle nord :
le bourrelet d'eau (très exagéré) suit la marée d'équilibre statique, somme des effets de la Lune et du Soleil ;
flèches de la force de marée (différence entre l'attraction en un point et au centre de la Terre) ; courbe du
niveau de la mer pour un observateur de l'équateur.  Marée d'équilibre d'un astre de masse M à la distance d :
ζ(ψ) = (M / M⊕)(R / d)³ R (3 cos² ψ − 1) / 2 ; effet du Soleil ≈ 0,46 fois celui de la Lune."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, heures_minutes, nombre

D_LUNE_M = astro.D_LUNE_KM * 1000.0
D_SOLEIL_M = astro.UA_KM * 1000.0


def niveau(angle_point: float, elong: float, avec_soleil: bool, decalage: float = 0.0) -> float:
    """Hauteur (m) de la marée d'équilibre en un point de l'équateur d'angle `angle_point` (vu du nord, depuis la
    direction du Soleil), la Lune étant à l'élongation `elong` ; `decalage` : avance des bourrelets (degrés) dans le
    sens de la rotation terrestre."""
    a = angle_point - decalage
    h = astro.maree_equilibre(a - elong, astro.MASSE_LUNE_KG, D_LUNE_M)
    if avec_soleil:
        h += astro.maree_equilibre(a, astro.MASSE_SOLEIL_KG, D_SOLEIL_M)
    return h


def type_de_maree(elong: float) -> str:
    """Vives eaux près des syzygies (nouvelle et pleine lune), mortes eaux près des quadratures."""
    c = abs(math.cos(math.radians(elong)))
    return 'vives' if c > 0.92 else ('mortes' if c < 0.38 else 'moyennes')


class Marees(Animation):
    ID = 'tidesim'
    JOURS_PAR_S = 0.25

    def construire(self):
        self.c_soleil = self.coche('soleil', False)
        self.c_fleches = self.coche('fleches', True)
        self.decalage = self.curseur('decalage', 0.0, 30.0, 0.0, dec=0, unite='°')
        self.exageration = self.curseur('exageration', 1.0, 10.0, 4.0, dec=1, unite='×')
        self.etat_initial()

    def etat_initial(self):
        self.t = 0.0                    # jours depuis la nouvelle lune, à minuit
        self.e0 = 0.0

    def elong(self) -> float:
        return (self.e0 + 360.0 * self.t / astro.MOIS_SYNODIQUE_J) % 360.0

    def heure(self) -> float:
        return (24.0 * self.t) % 24.0

    def angle_observateur(self, t: float | None = None) -> float:
        """Observateur de l'équateur : face au Soleil à midi (angle 0), tourne de 15° par heure (vers l'est)."""
        h = (24.0 * (self.t if t is None else t)) % 24.0
        return 15.0 * (h - 12.0)

    def avancer(self, dt):
        self.t += dt * self.JOURS_PAR_S

    def _niveau_obs(self, t: float) -> float:
        e = (self.e0 + 360.0 * t / astro.MOIS_SYNODIQUE_J) % 360.0
        return niveau(self.angle_observateur(t), e, self.c_soleil.isChecked(), self.decalage.value())

    def valeurs(self):
        e = self.elong()
        lune_seule = astro.maree_equilibre(0.0, astro.MASSE_LUNE_KG, D_LUNE_M) - astro.maree_equilibre(
            90.0, astro.MASSE_LUNE_KG, D_LUNE_M)
        out = [(tr('anim_c_heure'), heures_minutes(self.heure())),
               (tr('anim_lunar_applet_nom_phase'), tr('anim_phase_' + astro.nom_de_phase(e))),
               (tr('anim_tidesim_niveau'), '%s cm' % nombre(100 * self._niveau_obs(self.t), 1)),
               (tr('anim_tidesim_marnage_lune'), '%s cm' % nombre(100 * lune_seule, 1)),
               (tr('anim_tidesim_rapport'), nombre(astro.rapport_marees_soleil_lune(), 3))]
        if self.c_soleil.isChecked():
            out.append((tr('anim_tidesim_type'), tr('anim_tidesim_t_' + type_de_maree(e))))
        return out

    def dessiner(self, p, rect):
        haut = rect.height() * 0.70
        self._terre(p, QRectF(rect.x(), rect.y(), rect.width(), haut))
        self._courbe(p, dessin.cadre(p, QRectF(rect.x(), rect.y() + haut, rect.width(), rect.height() - haut),
                                     tr('anim_tidesim_courbe')))

    def _terre(self, p, r):
        cx, cy = r.center().x(), r.center().y()
        rt = min(r.width(), r.height()) * 0.24
        e = self.elong()
        avec_soleil = self.c_soleil.isChecked()
        amp_ref = astro.maree_equilibre(0.0, astro.MASSE_LUNE_KG, D_LUNE_M) * 1.46
        k = rt * 0.08 * self.exageration.value() / amp_ref
        a = np.linspace(0.0, 360.0, 181)
        pts = []
        for x in a:
            h = niveau(x, e, avec_soleil, self.decalage.value())
            rr = rt * 1.08 + k * h
            pts.append(QPointF(cx + rr * math.cos(math.radians(x)), cy - rr * math.sin(math.radians(x))))
        p.setPen(dessin.stylo('equateur', 1.4))
        p.setBrush(dessin.c('equateur', 0.35))
        p.drawPolygon(QPolygonF(pts))
        dessin.disque(p, cx, cy, rt, 'sol')
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('nuit', 0.55))
        p.drawPie(QRectF(cx - rt, cy - rt, 2 * rt, 2 * rt), 90 * 16, 180 * 16)
        # observateur
        o = math.radians(self.angle_observateur())
        dessin.disque(p, cx + rt * math.cos(o), cy - rt * math.sin(o), 4.5, 'accent3', bord='texte')
        # Lune
        dm = min(r.width() * 0.46, r.height() * 0.46)
        em = math.radians(e)
        mx, my = cx + dm * math.cos(em), cy - dm * math.sin(em)
        p.setPen(dessin.stylo('grille', 1.0, 0.6, pointille=True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), dm, dm)
        dessin.disque(p, mx, my, max(6.0, rt * 0.27), 'lune')
        # Soleil (loin à droite)
        for kk in (-0.5, 0.0, 0.5):
            dessin.fleche(p, r.right() - 6, cy + kk * rt * 2, r.right() - 46, cy + kk * rt * 2,
                          dessin.stylo('soleil', 1.2, 0.8 if avec_soleil else 0.35), 6)
        if self.c_fleches.isChecked():
            self._fleches(p, cx, cy, rt, e, avec_soleil)

    def _fleches(self, p, cx, cy, rt, e, avec_soleil):
        """Force de marée en douze points de l'équateur : M/d³ (3 (r·u) u − r), somme Lune (+ Soleil)."""
        sources = [(e, astro.MASSE_LUNE_KG / D_LUNE_M ** 3)]
        if avec_soleil:
            sources.append((0.0, astro.MASSE_SOLEIL_KG / D_SOLEIL_M ** 3))
        ref = astro.MASSE_LUNE_KG / D_LUNE_M ** 3 * 2
        for x in range(0, 360, 30):
            rv = np.array([math.cos(math.radians(x)), math.sin(math.radians(x))])
            f = np.zeros(2)
            for a, c in sources:
                u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
                f += c * (3 * (rv @ u) * u - rv)
            f *= rt * 0.32 / ref
            x0, y0 = cx + rt * 0.72 * rv[0], cy - rt * 0.72 * rv[1]
            if np.hypot(*f) > 1.5:
                dessin.fleche(p, x0, y0, x0 + f[0], y0 - f[1], dessin.stylo('accent1', 1.6), 5)

    def _courbe(self, p, r):
        """Niveau de la mer pour l'observateur, de −1,5 à +1,5 jour autour de l'instant présent."""
        ts = np.linspace(self.t - 1.5, self.t + 1.5, 241)
        hs = np.array([self._niveau_obs(t) for t in ts])
        hmax = 0.9
        x0, x1 = r.x() + 30, r.right() - 6
        ym = r.center().y()
        k = (r.height() / 2 - 4) / hmax
        p.setPen(dessin.stylo('grille', 1.0))
        p.drawLine(QPointF(x0, ym), QPointF(x1, ym))
        p.drawLine(QPointF((x0 + x1) / 2, r.y()), QPointF((x0 + x1) / 2, r.bottom()))
        dessin.police(p, 0.75)
        for v in (-0.5, 0.5):
            dessin.texte(p, x0 - 14, ym - k * v, nombre(v, 1), 'doux')
        dessin.texte(p, x0 - 14, r.y() + 6, 'm', 'doux')
        dessin.police(p, 1 / 0.75)
        poly = [QPointF(x0 + (x1 - x0) * i / (len(ts) - 1), ym - k * h) for i, h in enumerate(hs)]
        p.setPen(dessin.stylo('equateur', 1.8))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF(poly))
        dessin.disque(p, (x0 + x1) / 2, ym - k * self._niveau_obs(self.t), 4, 'accent3')
