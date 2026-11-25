"""Le mécanisme de Kozai-Lidov : un perturbateur lointain, incliné, échange l'excentricité et l'inclinaison d'une
orbite (C = √(1 − e²) cos i conservé).  Au-delà de 39,2°, une orbite presque circulaire s'allonge jusqu'à
e_max = √(1 − 5/3 cos² i₀), puis revient, périodiquement.  Orbite en 3D, e(t) et i(t), portrait de phase (ω, e).
Calculs : ``kozai.py`` (équations séculaires quadrupolaires, forme vectorielle, Runge-Kutta 4)."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import dessin, kozai as kz
from ..base import Animation, angle, nombre
from ..graphe import Axes

VITESSE_TK = 2.0                 # t_K par seconde réelle, à la vitesse ×1
FENETRE = 40.0                   # largeur (t_K) du graphe e(t), i(t)
N_HISTOIRE = 4000


def annees(x: float) -> str:
    if x >= 1e6:
        return tr('anim_kozai_millions_ans', x=nombre(x / 1e6, 2))
    return tr('anim_kozai_ans', x=nombre(x, 0 if x >= 100 else 1))


class Kozai(Animation):
    ID = 'kozai'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.systeme = self.choix('systeme', [('anim_kozai_s_' + k, k) for k, *_ in kz.SYSTEMES], 'asteroide')
        self.i0 = self.curseur('i0', 0.0, 89.0, 65.0, dec=1, unite='°')
        self.e0 = self.curseur('e0', 0.001, 0.9, 0.05, dec=3, log=True)
        self.w0 = self.curseur('w0', 0.0, 360.0, 0.0, dec=0, unite='°')
        self.c_trace = self.coche('trace', True)
        self.bouton('anim_kozai_recommencer', self.recommencer)
        self.vue3d = self.vue(30.0, 25.0)
        self._cle = None
        self.recommencer()

    def recommencer(self):
        self.tau = 0.0
        self.ev, self.jv = kz.vecteurs(self.e0.value(), self.i0.value(), self.w0.value())
        e, i, w, _ = kz.elements(self.ev, self.jv)
        self.histoire = [(0.0, e, i, w)]
        self.e_max = e
        self.maxima = []
        self._s = None
        self._cle = (self.e0.value(), self.i0.value(), self.w0.value())
        self.rafraichir()

    def reglage_change(self):
        if self._cle is not None and self._cle != (self.e0.value(), self.i0.value(), self.w0.value()):
            self.recommencer()
        super().reglage_change()

    def avancer(self, dt):
        d = dt * VITESSE_TK
        tau0 = self.tau
        self.ev, self.jv = kz.integrer(self.ev, self.jv, d)
        self.tau += d
        e, i, w, _ = kz.elements(self.ev, self.jv)
        self.histoire.append((self.tau, e, i, w))
        if len(self.histoire) > N_HISTOIRE:
            del self.histoire[0]
        self.e_max = max(self.e_max, e)
        # maximum de e : e·de/dτ passe de + à −, instant interpolé
        de, _ = kz.derivees(self.ev, self.jv)
        s = sum(self.ev[k] * de[k] for k in range(3))
        if self._s is not None and self._s > 0.0 >= s:
            self.maxima.append(tau0 + d * self._s / (self._s - s))
        self._s = s

    # ------------------------------------------------------------ valeurs
    def t_k(self) -> float:
        m, ap, per = [x for k, *x in kz.SYSTEMES if k == self.systeme.currentData()][0]
        return kz.t_kozai_ans(m, ap, per)

    def valeurs(self):
        e, i, w, _ = kz.elements(self.ev, self.jv)
        c = kz.constante_c(e, i)
        tk = self.t_k()
        out = [(tr('anim_kozai_v_c'), tr('anim_kozai_c_conservee', c=nombre(c, 4),
                                         c0=nombre(kz.constante_c(self.e0.value(), self.i0.value()), 4))),
               (tr('anim_kozai_v_e'), nombre(e, 3)),
               (tr('anim_kozai_v_i'), angle(i, 1)),
               (tr('anim_kozai_v_w'), angle(w, 0)),
               (tr('anim_kozai_v_critique'), angle(kz.I_CRITIQUE, 2))]
        em = kz.e_max_circulaire(self.i0.value())
        out.append((tr('anim_kozai_v_emax_prevue'), nombre(em, 3) if em > 0 else tr('anim_kozai_sous_critique')))
        out.append((tr('anim_kozai_v_emax'), tr('anim_kozai_emax_i', e=nombre(self.e_max, 3),
                                                i=angle(kz.i_a_e(c, self.e_max), 1))))
        out.append((tr('anim_kozai_v_tk'), annees(tk)))
        if len(self.maxima) >= 2:
            per = self.maxima[-1] - self.maxima[-2]
            out.append((tr('anim_kozai_v_periode'), tr('anim_kozai_periode', p=nombre(per, 2), a=annees(per * tk))))
        else:
            out.append((tr('anim_kozai_v_periode'), tr('anim_kozai_en_mesure')))
        out.append((tr('anim_kozai_v_temps'), tr('anim_kozai_temps', t=nombre(self.tau, 1), a=annees(self.tau * tk))))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.46)
        self._orbite(p, dessin.cadre(p, z[0], tr('anim_kozai_t_orbite')))
        self._temps(p, dessin.cadre(p, z[1], tr('anim_kozai_t_temps')))
        self._phase(p, dessin.cadre(p, z[2], tr('anim_kozai_t_phase')))

    def _orbite(self, p, r):
        self.zone_rotative(r, self.vue3d)
        rr = 0.42 * min(r.width(), r.height() - 30)
        pe = dessin.Peintre3D(p, self.vue3d, r.center().x(), r.center().y() + 10, rr)
        pe.plan('equateur', 0.10, 1.0, 'equateur')
        # le perturbateur, dans son plan (loin : pas à l'échelle)
        pe.courbe(dessin.cercle((0, 0, 1)), 'ecliptique', 1.2, 0.8, arriere='normal', profondeur=False)
        ang = 0.6 * self.tau
        pe.point((math.cos(ang), math.sin(ang), 0.0), 'arc2', 6.0, etiquette=tr('anim_kozai_perturbateur'),
                 toujours=True)
        # l'orbite intérieure : a = 0,55
        ev, jv = np.array(self.ev), np.array(self.jv)
        e = float(np.linalg.norm(ev))
        g = float(np.linalg.norm(jv))
        nh = jv / g
        eh = ev / e if e > 1e-9 else np.cross(nh, (0.0, 0.0, 1.0)) if abs(nh[2]) < 0.999 else np.array((1.0, 0, 0))
        eh = eh / np.linalg.norm(eh)
        qh = np.cross(nh, eh)
        a = 0.55
        nu = np.linspace(0.0, 2.0 * math.pi, 181)
        rad = a * (1.0 - e * e) / (1.0 + e * np.cos(nu))
        pts = rad[:, None] * (np.cos(nu)[:, None] * eh + np.sin(nu)[:, None] * qh)
        pe.courbe(pts, 'accent1', 2.2, 1.0, arriere='pointille', profondeur=False)
        pe.point((0.0, 0.0, 0.0), 'soleil', 6.0, toujours=True)
        if e > 1e-3:
            per = a * (1.0 - e) * eh
            pe.segment((0.0, 0.0, 0.0), per, 'accent3', 1.3, 0.9)
            pe.point(per, 'accent3', 3.5, etiquette=tr('anim_kozai_periastre'), toujours=True)
        pe.segment((0.0, 0.0, 0.0), 0.45 * nh, 'accent2', 1.6, 0.9)
        pe.etiquette(0.5 * nh, tr('anim_kozai_normale'), 'accent2')
        pe.segment((0.0, 0.0, 0.0), (0.0, 0.0, 0.45), 'doux', 1.0, 0.7)

    def _temps(self, p, r):
        t1 = max(FENETRE, self.tau)
        t0 = t1 - FENETRE
        ax = Axes(r, t0, t1, 0.0, 1.05, marges=(40, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_kozai_axe_t'), tr('anim_kozai_axe_ei'))
        em = kz.e_max_circulaire(self.i0.value())
        if em > 0:
            ax.horizontale(em, 'accent1', 1.0)
        ax.horizontale(kz.I_CRITIQUE / 90.0, 'accent2', 1.0)
        h = [x for x in self.histoire if x[0] >= t0]
        if len(h) >= 2:
            ax.courbe([(t, e) for t, e, _, _ in h], 'accent1', 2.0)
            ax.courbe([(t, i / 90.0) for t, _, i, _ in h], 'accent2', 2.0)
        dessin.texte(p, ax.r.left() + 6, ax.r.top() + 10, tr('anim_kozai_legende_temps'), 'doux', centre=False,
                     fond=True)

    def _phase(self, p, r):
        ax = Axes(r, 0.0, 360.0, 0.0, 1.05, marges=(40, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_kozai_axe_w'), tr('anim_kozai_axe_e'), fmt_x=lambda x: nombre(x, 0))
        e, i, w, _ = kz.elements(self.ev, self.jv)
        c = kz.constante_c(e, i)
        lim = math.sqrt(max(0.0, 1.0 - c * c))
        ax.horizontale(lim, 'doux', 1.0)
        dessin.texte(p, ax.px(180.0), ax.py(lim) - 8, tr('anim_kozai_limite'), 'doux', fond=True)
        if self.c_trace.isChecked():
            ax.points([(x[3], x[1]) for x in self.histoire], 'accent3', 1.3, 0.6)
        dessin.disque(p, ax.px(w), ax.py(e), 4.5, 'accent1', 'texte')
