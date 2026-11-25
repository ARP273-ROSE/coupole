"""Traînées de météoroïdes éjectés par une comète : à chaque passage au périhélie, la comète lâche un nuage de grains qui
s'étire le long de son orbite (une traînée par passage) ; la Terre croise ces traînées chaque année près du nœud de la
comète, et ne rencontre beaucoup de grains (averse) que lorsqu'une traînée jeune et dense passe là en même temps
qu'elle.  Vue de dessus, diagramme (Δt, Δr) au nœud pour l'année en cours, activité année par année.
Calculs : ``trainees.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, trainees as tn
from ..base import Animation, date_du_jour, nombre
from ..graphe import Axes
from .precession import an

DUREE_S = 40.0                   # secondes réelles pour parcourir les années suivies (vitesse × 1)
COULEURS = ('accent2', 'accent1', 'accent3', 'arc1', 'arc2', 'meridien', 'ecliptique', 'equateur')
DT_MAX = 200.0                   # jours : demi-largeur du diagramme (Δt, Δr)
DR_MAX = 0.02                    # ua


def signe(x: float, dec: int) -> str:
    return ('+' if x > 0 else '') + nombre(x, dec)


class Trainees(Animation):
    ID = 'meteoroidtrails'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.comete = self.choix('comete', [('anim_meteoroidtrails_c_' + c[0], c[0]) for c in tn.COMETES],
                                 'tempel_tuttle')
        self.dv = self.curseur('dv', 1.0, 50.0, 10.0, dec=1, unite='m·s⁻¹', log=True)
        self.taille = self.choix('taille', [('anim_meteoroidtrails_t_' + k, k) for k, _ in tn.TAILLES], 'mm')
        self.cadrage = self.choix('cadrage', [('anim_meteoroidtrails_v_interieur', 'interieur'),
                                              ('anim_meteoroidtrails_v_orbite', 'orbite')], 'interieur')
        self.bouton('anim_meteoroidtrails_relancer', self.relancer)
        self._essaim = None
        self._ecarts = None
        self.t = float(tn.fenetre(self.comete.currentData())[0])

    # ------------------------------------------------------------ état
    def relancer(self):
        self.t = float(tn.fenetre(self.comete.currentData())[0])
        self.rafraichir()

    def essaim(self):
        cle = (self.comete.currentData(), self.dv.value(), self.taille.currentData())
        if self._essaim is None or self._essaim[0] != cle:
            a0, a1 = tn.fenetre(cle[0])
            e = tn.Essaim(cle[0], cle[1], cle[2], a0, a1)
            self._essaim = (cle, e, e.activite(a0, a1))
            self._ecarts = None
            if not a0 <= self.t <= a1 + 1.0:
                self.t = float(a0)
        return self._essaim[1], self._essaim[2]

    def annee(self) -> int:
        return int(math.floor(self.t))

    def ecarts(self):
        e, _ = self.essaim()
        y = self.annee()
        if self._ecarts is None or self._ecarts[0] != (id(e), y):
            self._ecarts = ((id(e), y), e.ecarts(y))
        return self._ecarts[1]

    def avancer(self, dt):
        a0, a1 = tn.fenetre(self.comete.currentData())
        span = a1 + 1.0 - a0
        self.t = a0 + (self.t - a0 + dt * span / DUREE_S) % span

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        e, act = self.essaim()
        c = self.comete.currentData()
        r, lam, _ = tn.noeud(e.comete, e.genre)
        tE = tn.date_terre(lam, self.annee())
        jour = (tE - math.floor(tE)) * 365.25
        lachees = sum(1 for tk in e.ejections if tk <= self.t)
        ymax = max(act, key=lambda y: (act[y], -y))
        return [(tr('anim_meteoroidtrails_v_essaim'), tr('anim_meteoroidtrails_e_' + tn.comete(c)[7])),
                (tr('anim_meteoroidtrails_v_date'), an(self.annee())),
                (tr('anim_meteoroidtrails_v_periode'), tr('anim_meteoroidtrails_ans', n=nombre(e.comete.periode(), 1))),
                (tr('anim_meteoroidtrails_v_beta'), tr('anim_meteoroidtrails_beta', x=nombre(e.beta * 1e4, 2))),
                (tr('anim_meteoroidtrails_v_lachees'), str(lachees)),
                (tr('anim_meteoroidtrails_v_noeud'), tr('anim_meteoroidtrails_noeud', r=nombre(r, 4),
                                                        d=signe(r - tn.r_terre(lam), 4))),
                (tr('anim_meteoroidtrails_v_terre'), date_du_jour(jour)),
                (tr('anim_meteoroidtrails_v_filet'), str(act.get(self.annee(), 0))),
                (tr('anim_meteoroidtrails_v_max'), tr('anim_meteoroidtrails_max', an=an(ymax), n=act[ymax]))]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.5)
        self._vue(p, dessin.cadre(p, z[0], tr('anim_meteoroidtrails_t_vue')))
        self._diagramme(p, dessin.cadre(p, z[1], tr('anim_meteoroidtrails_t_diagramme')))
        self._activite(p, dessin.cadre(p, z[2], tr('anim_meteoroidtrails_t_activite')))

    def _vue(self, p, r):
        e, _ = self.essaim()
        orb = e.comete
        demi = 2.0 if self.cadrage.currentData() == 'interieur' else orb.a * (1.0 + orb.e) * 1.05
        k = min(r.width(), r.height() - 8) / (2.0 * demi)
        cx, cy = r.center().x(), r.center().y() + 4
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('terre', 1.4))
        p.drawEllipse(QPointF(cx, cy), k, k)
        pts = [orb.position(orb.t0 + orb.periode() * j / 360.0) for j in range(361)]
        p.setPen(dessin.stylo('doux', 1.0, 0.8, pointille=True))
        for j in range(360):
            p.drawLine(QPointF(cx + k * pts[j][0], cy - k * pts[j][1]),
                       QPointF(cx + k * pts[j + 1][0], cy - k * pts[j + 1][1]))
        rayon = 1.6 if self.cadrage.currentData() == 'interieur' else 1.2
        for n, (tk, grains, _) in enumerate(e.traines):
            if tk > self.t:
                continue
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c(COULEURS[n % len(COULEURS)], 0.85))
            for o in grains:
                x, y, _ = o.position(self.t)
                if abs(x) < demi * 1.2 and abs(y) < demi * 1.2:
                    p.drawEllipse(QPointF(cx + k * x, cy - k * y), rayon, rayon)
        xc, yc, _ = orb.position(self.t)
        dessin.disque(p, cx + k * xc, cy - k * yc, 4.0, 'etoile', 'texte')
        xe, ye = tn.terre(self.t)
        dessin.disque(p, cx + k * xe, cy - k * ye, 5.0, 'terre', 'texte')
        dessin.disque(p, cx, cy, 6.0, 'soleil')
        p.restore()
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_meteoroidtrails_legende_vue'), 'doux', centre=False,
                     fond=True)

    def _diagramme(self, p, r):
        ax = Axes(r, -DT_MAX, DT_MAX, -DR_MAX, DR_MAX, marges=(52, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_meteoroidtrails_axe_dt'), tr('anim_meteoroidtrails_axe_dr'))
        p.save()
        p.setPen(dessin.stylo('accent3', 1.2, 0.9, pointille=True))
        p.setBrush(dessin.c('accent3', 0.12))
        x0, x1 = ax.px(-tn.EPS_T), ax.px(tn.EPS_T)
        y0, y1 = ax.py(tn.EPS_R), ax.py(-tn.EPS_R)
        p.drawRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        p.setPen(dessin.Qt.PenStyle.NoPen)
        for dt, dr, n in self.ecarts():
            if abs(dt) <= DT_MAX and abs(dr) <= DR_MAX:
                p.setBrush(dessin.c(COULEURS[n % len(COULEURS)], 0.9))
                p.drawEllipse(QPointF(ax.px(dt), ax.py(dr)), 2.0, 2.0)
        p.restore()
        dessin.disque(p, ax.px(0.0), ax.py(0.0), 5.0, 'terre', 'texte')
        dessin.texte(p, ax.r.right() - 30, ax.r.top() + 12, an(self.annee()), 'texte', fond=True)

    def _activite(self, p, r):
        _, act = self.essaim()
        a0, a1 = tn.fenetre(self.comete.currentData())
        vmax = max(4, max(act.values()))
        ax = Axes(r, a0, a1 + 1.0, 0.0, vmax * 1.1, marges=(40, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_meteoroidtrails_axe_an'), tr('anim_meteoroidtrails_axe_n'), fmt_x=lambda v: an(int(round(v))))
        p.save()
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('accent1', 0.9))
        larg = max(1.0, ax.px(a0 + 1.0) - ax.px(a0))
        for y, n in act.items():
            if n:
                p.drawRect(QRectF(ax.px(y), ax.py(n), larg, ax.py(0.0) - ax.py(n)))
        p.restore()
        e, _ = self.essaim()
        for tk in e.ejections:
            dessin.disque(p, ax.px(tk), ax.py(0.0), 3.0, 'etoile', 'texte')
        ax.verticale(self.t, 'texte', 1.2, False)
