"""Radial Velocity Simulator (NAAP) : la courbe de vitesse radiale d'une étoile à planète, pour une orbite
quelconque (masses, taille, excentricité, inclinaison, orientation), avec des mesures simulées bruitées.
v_r = K [cos(ν + ω) + e cos ω], K = (2πG / P)^⅓ M_p sin i / (M_* + M_p)^⅔ / √(1 − e²).  Planètes réelles : NASA
Exoplanet Archive (2026) ; le demi-grand axe est tiré de la période publiée par la 3e loi de Kepler."""
from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import deux_corps as dc, dessin, donnees_lot3 as D
from ..base import Animation, nombre
from ..graphe import Axes
from .vitesse_radiale import texte_duree

PRERELAGES = {**{t[0]: t for t in D.VITESSES_RADIALES_EXEMPLES}, **{t[0]: t for t in D.VITESSES_RADIALES}}


class VitessesRadiales(Animation):
    ID = 'radialvelocitysimulator'

    def construire(self):
        self.prereglage = self.choix('systeme', [('anim_radialvelocitysimulator_s_' + k, k) for k in 'abcd'] +
                                     [('anim_radialvelocitysimulator_s_' + t[0].lower().replace(' ', '_'), t[0])
                                      for t in D.VITESSES_RADIALES], 'a')
        self.prereglage.activated.connect(self._appliquer)
        self.ms = self.curseur('masse_etoile', 0.1, 3.0, 1.0, dec=3, unite='M☉')
        self.mp = self.curseur('masse_planete', 0.001, 30.0, 1.0, dec=3, unite='M♃', log=True)
        self.a = self.curseur('a', 0.01, 6.0, 1.0, dec=4, unite='ua', log=True)
        self.e = self.curseur('e', 0.0, 0.9, 0.0, dec=3)
        self.i = self.curseur('i', 0.0, 90.0, 90.0, dec=1, unite='°')
        self.w = self.curseur('omega', 0.0, 360.0, 0.0, dec=1, unite='°')
        self.bruit = self.curseur('bruit', 0.0, 50.0, 3.0, dec=1, unite='m·s⁻¹')
        self.n_mesures = self.curseur('mesures', 0.0, 200.0, 40.0, dec=0)
        self.phase = 0.0
        self._mesures = None

    def _appliquer(self, *_):
        t = PRERELAGES[self.prereglage.currentData()]
        if len(t) == 7:
            _, ms, mp, a, e, i, w = t
        else:
            _, ms, mp, a, e, i, w, periode, _k = t
            a = dc.demi_grand_axe_m(periode * dc.JOUR_S, ms * dc.M_SOLEIL_KG, mp * dc.M_JUPITER_KG) / dc.UA_M
        for reg, v in ((self.ms, ms), (self.mp, mp), (self.a, a), (self.e, e), (self.i, i), (self.w, w)):
            reg.setValue(v)
        self.rafraichir()

    def etat_initial(self):
        self.phase = 0.0
        self._mesures = None

    def reglage_change(self):
        self._mesures = None
        super().reglage_change()

    def systeme(self) -> dict:
        m1, m2 = self.ms.value() * dc.M_SOLEIL_KG, self.mp.value() * dc.M_JUPITER_KG
        a = self.a.value() * dc.UA_M
        e, i, w = self.e.value(), self.i.value(), self.w.value()
        return {'P': dc.periode_s(a, m1, m2), 'K': dc.amplitude_k(m1, m2, a, e, i), 'e': e, 'i': i, 'w': w,
                'q': m2 / (m1 + m2)}

    def mesures(self, s):
        if self._mesures is None:
            alea = random.Random(11)
            sig = self.bruit.value()
            self._mesures = []
            for _ in range(int(self.n_mesures.value())):
                ph = alea.random()
                self._mesures.append((ph, dc.vitesse_radiale(ph, s['K'], s['e'], s['w']) + alea.gauss(0.0, sig)))
        return self._mesures

    def avancer(self, dt):
        self.phase = (self.phase + dt / 10.0) % 1.0

    def valeurs(self):
        s = self.systeme()
        out = [(tr('anim_c_periode'), texte_duree(s['P'])),
               (tr('anim_ca_extrasolarplanets_graph_k'), '%s m·s⁻¹' % nombre(s['K'], 2)),
               (tr('anim_radialvelocitysimulator_msini'), '%s M♃' % nombre(self.mp.value() *
                                                                        math.sin(math.radians(s['i'])), 3))]
        t = PRERELAGES[self.prereglage.currentData()]
        if len(t) == 9:
            out.append((tr('anim_ca_extrasolarplanets_graph_k_mesuree'), '%s m·s⁻¹' % nombre(t[8], 1)))
        return out

    def dessiner(self, p, rect):
        s = self.systeme()
        z = dessin.zones(rect, 2, 0.95)
        self._orbite(p, dessin.cadre(p, z[0], tr('anim_radialvelocitysimulator_titre_orbite')), s)
        r = dessin.cadre(p, z[1], tr('anim_radialvelocitysimulator_titre_courbe'))
        k = max(s['K'], 1e-6)
        vmax = max(k * (1 + s['e']), 3 * self.bruit.value(), 1e-6)
        ax = Axes(r, 0, 1, -1.25 * vmax, 1.25 * vmax, marges=(54, 8, 10, 28)).avec(p)
        ax.fond(p, tr('anim_c_phase'), tr('anim_c_vitesse_radiale'), dec_x=1)
        ax.horizontale(0.0, 'grille', 1.0, False)
        if self.n_mesures.value() > 0:
            ax.points(self.mesures(s), 'doux', 2.2, 0.8)
        ax.courbe([(x / 200, dc.vitesse_radiale(x / 200, s['K'], s['e'], s['w'])) for x in range(201)], 'accent1', 2.0)
        ax.points([(self.phase, dc.vitesse_radiale(self.phase, s['K'], s['e'], s['w']))], 'accent3', 5, 1.0)

    def _orbite(self, p, r, s):
        """Orbite relative vue de dessus (observateur en bas), étoile au foyer ; l'étoile réelle décrit la même
        ellipse en réduction (facteur M_p / (M_* + M_p)), à l'opposé."""
        cx, cy = r.center().x(), r.center().y() - 8
        e, w = s['e'], math.radians(s['w'])
        k = min(r.width(), r.height()) * 0.38 / (1 + e)
        pts = []
        for n in range(121):
            nu = 2 * math.pi * n / 120
            rr = (1 - e * e) / (1 + e * math.cos(nu))
            u = nu + w
            pts.append(QPointF(cx + k * rr * math.cos(u), cy + k * rr * math.sin(u)))
        p.setPen(dessin.stylo('equateur', 1.0, 0.7, True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF(pts))
        # vue de dessus : x dans le plan du ciel, la composante vers l'observateur (r sin u) vers le bas
        nu = dc.anomalie_vraie(self.phase, e)
        rr = (1 - e * e) / (1 + e * math.cos(nu))
        u = nu + w
        px, py = cx + k * rr * math.cos(u), cy + k * rr * math.sin(u)
        q = max(s['q'], 0.02)
        dessin.disque(p, cx - (px - cx) * q, cy - (py - cy) * q, 11, 'soleil')
        dessin.disque(p, px, py, 5, 'equateur', bord='texte')
        dessin.texte(p, cx, r.bottom() - 8, '↓ ' + tr('anim_c_vers_observateur'), 'doux')
