"""La limite de Roche : un satellite fait de grains tenus par leur seule gravité descend lentement vers sa planète ;
sous d = 2,44 R (ρ_M/ρ_m)^(1/3) (fluide) ou 1,44 R (ρ_M/ρ_m)^(1/3) (rigide), la marée l'emporte, il se disloque et
ses débris s'étalent en anneau.  Vue d'ensemble, gros plan sur le satellite et ses forces de marée, étirement rapporté
à la gravité propre selon la distance.  Calculs : ``roche.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import dessin, roche as ro
from ..base import Animation, nombre
from ..graphe import Axes

VITESSE = 2.0 * math.pi * 3.0 ** 1.5 / 2.0     # temps simulé par seconde réelle : une orbite à 3 R en 2 s
DESCENTE = 0.25                                # R par seconde réelle quand le satellite descend
D_MIN = 1.05


class Roche(Animation):
    ID = 'roche'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.systeme = self.choix('systeme', [('anim_roche_s_' + k, k) for k, *_ in ro.SYSTEMES], 'saturne_glace')
        self.rapport = self.curseur('rapport', 0.2, 5.0, 687.0 / 920.0, dec=3, log=True)
        self.d0 = self.curseur('d0', 1.2, 10.0, 3.08, dec=2)
        self.modele = self.choix('modele', [('anim_roche_m_fluide', 'fluide'), ('anim_roche_m_rigide', 'rigide')],
                                 'fluide')
        self.c_descente = self.coche('descente', True)
        self.bouton('anim_roche_relancer', self.recommencer)
        self.gs = ro.grains()
        self._sys = self.systeme.currentData()
        self._depart = None
        self.recommencer()

    def recommencer(self):
        self.d = self.d0.value()
        self.theta = 0.0
        self.t = 0.0
        self.debris = None             # éléments des grains après la dislocation
        self.t_rupture = 0.0
        self.tombes = set()
        self._depart = (self.d0.value(), self.rapport.value(), self.modele.currentData())
        self.rafraichir()

    def reglage_change(self):
        k = self.systeme.currentData()
        if k != getattr(self, '_sys', k):
            self._sys = k
            for cle, rm, rs_, _, d0 in ro.SYSTEMES:
                if cle == k:
                    self.rapport.setValue(rm / rs_)
                    self.d0.setValue(d0)
        if self._depart is not None and self._depart != (self.d0.value(), self.rapport.value(),
                                                         self.modele.currentData()):
            self.recommencer()
        super().reglage_change()

    def limite(self) -> float:
        return ro.limite(self.rapport.value(), self.modele.currentData())

    def etire(self) -> float:
        if self.modele.currentData() != 'fluide':
            return 0.0
        return ro.allongement(self.rapport.value(), self.d)

    def avancer(self, dt):
        dts = dt * VITESSE
        self.t += dts
        if self.debris is None:
            self.theta = math.fmod(self.theta + dts * self.d ** -1.5, 2.0 * math.pi)
            if self.c_descente.isChecked():
                self.d = max(D_MIN, self.d - dt * DESCENTE)
            if self.d < self.limite():
                self.debris = ro.liberer(self.d, self.theta, self.gs, self.etire())
                self.t_rupture = self.t
        else:
            for i, el in enumerate(self.debris):
                if i in self.tombes or el is None:
                    continue
                x, y = ro.position_kepler(el, self.t - self.t_rupture)
                if x * x + y * y < 1.0:
                    self.tombes.add(i)

    def positions(self):
        if self.debris is None:
            return [ro.position_intact(self.d, self.theta, g, self.etire()) for g in self.gs]
        return [ro.position_kepler(el, self.t - self.t_rupture) for i, el in enumerate(self.debris)
                if el is not None and i not in self.tombes]

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        r = self.rapport.value()
        R_km = [x for x in ro.SYSTEMES if x[0] == self.systeme.currentData()][0][3]
        lf, lr = ro.limite(r, 'fluide'), ro.limite(r, 'rigide')
        out = [(tr('anim_roche_v_fluide'), tr('anim_roche_r_km', r=nombre(lf, 2), km=nombre(lf * R_km, 0))),
               (tr('anim_roche_v_rigide'), tr('anim_roche_r_km', r=nombre(lr, 2), km=nombre(lr * R_km, 0))),
               (tr('anim_roche_v_d'), tr('anim_roche_r_km', r=nombre(self.d, 2), km=nombre(self.d * R_km, 0))),
               (tr('anim_roche_v_etirement'), nombre(ro.etirement(r, self.d), 3)),
               (tr('anim_roche_v_allongement'), '%s %%' % nombre(100.0 * ro.allongement(r, self.d), 1)),
               (tr('anim_roche_v_etat'), tr('anim_roche_intact') if self.debris is None else
                tr('anim_roche_disloque', n=len(self.positions()), m=len(self.gs)))]
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.56)
        self._vue(p, dessin.cadre(p, z[0], tr('anim_roche_t_vue')))
        self._gros_plan(p, dessin.cadre(p, z[1], tr('anim_roche_t_gros_plan')))
        self._graphe(p, dessin.cadre(p, z[2], tr('anim_roche_t_graphe')))

    def _vue(self, p, r):
        demi = max(self.d0.value(), ro.limite(self.rapport.value(), 'fluide')) * 1.12 + ro.R_SATELLITE
        cote = min(r.width(), r.height() - 6)
        k = cote / (2.0 * demi)
        cx, cy = r.center().x(), r.center().y() + 4
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for mod, cle in (('fluide', 'accent3'), ('rigide', 'accent2')):
            lim = ro.limite(self.rapport.value(), mod)
            p.setPen(dessin.stylo(cle, 1.2, 0.8, pointille=True))
            p.drawEllipse(QPointF(cx, cy), lim * k, lim * k)
        dessin.disque(p, cx, cy, k, {'terre_lune': 'terre', 'mars_phobos': 'mars'}.get(self.systeme.currentData(), 'ecliptique'))
        for x, y in self.positions():
            dessin.disque(p, cx + k * x, cy - k * y, max(1.5, 0.018 * k), 'lune')
        p.restore()
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_roche_legende_vue'), 'doux', centre=False, fond=True)

    def _gros_plan(self, p, r):
        cx, cy = r.center().x(), r.center().y() + 6
        R = 0.3 * min(r.width(), r.height())
        if self.debris is not None:
            dessin.texte(p, cx, cy, tr('anim_roche_plus_de_satellite'), 'doux')
            return
        et = self.etire()
        p.save()
        for g in self.gs:
            x, y = g[0] * (1.0 + et), g[1] / math.sqrt(1.0 + et)
            dessin.disque(p, cx + R * x, cy - R * y, max(1.5, 0.07 * R), 'lune')
        # forces de marée (direction de la planète : à gauche) : étirement 2x le long de l'axe, compression −y
        f = ro.etirement(self.rapport.value(), self.d) / 3.0
        L = 0.9 * R * min(1.0, 3.0 * f)
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            x, y = math.cos(a), math.sin(a)
            fx, fy = 2.0 * x, -y
            x0, y0 = cx + 1.15 * R * x, cy - 1.15 * R * y
            dessin.fleche(p, x0, y0, x0 + L * fx / 2.0, y0 - L * fy / 2.0, dessin.stylo('accent3', 1.8), 6.0)
        p.restore()
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_roche_legende_gros_plan'), 'doux', centre=False,
                     fond=True)

    def _graphe(self, p, r):
        ax = Axes(r, 1.0, 10.0, 0.001, 10.0, xlog=True, ylog=True, marges=(44, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_roche_axe_d'), tr('anim_roche_axe_rapport'))
        rp = self.rapport.value()
        pts = [(10.0 ** (j / 100.0), ro.etirement(rp, 10.0 ** (j / 100.0))) for j in range(101)]
        ax.courbe(pts, 'accent2', 1.8)
        ax.horizontale(1.0, 'doux', 1.0, True)
        ax.verticale(ro.limite(rp, 'rigide'), 'accent2', 1.0, True, tr('anim_roche_rigide_court'))
        ax.verticale(ro.limite(rp, 'fluide'), 'accent3', 1.0, True, tr('anim_roche_fluide_court'))
        if self.debris is None:
            dessin.disque(p, ax.px(self.d), ax.py(ro.etirement(rp, self.d)), 5.0, 'accent3', 'texte')
