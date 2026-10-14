"""Pulsar Period Simulator : un pulsar émet une impulsion à intervalles parfaitement réguliers.  S'il tourne autour
d'un compagnon (ou s'il est accompagné de planètes), les impulsions partent de points différents de son orbite : celles
émises en s'approchant de la Terre arrivent plus serrées, celles émises en s'éloignant plus espacées.  Les
intervalles d'arrivée, calculés exactement (t_arrivée = t_émission + distance / c), oscillent autour de la période
vraie : P (1 + v_r / c) au premier ordre.  C'est ainsi qu'ont été découvertes les premières exoplanètes, autour du
pulsar PSR B1257+12 (1992).  Unités réduites : la vitesse de la lumière vaut 1."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre
from ..graphe import Axes

C = 1.0                    # vitesse de la lumière (unités réduites)
R_ORBITE = 1.0
D_TERRE = 9.0              # distance centre de l'orbite – Terre
FENETRE = 60.0             # durée montrée sur le graphe


class Pulsar(Animation):
    ID = 'pulsarPeriodSim'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.mouvement = self.choix('mouvement', [('anim_pulsarperiodsim_immobile', 'immobile'),
                                                  ('anim_pulsarperiodsim_orbite', 'orbite')], 'orbite')
        self.p_pulsar = self.curseur('periode', 0.2, 2.0, 0.5, dec=2)
        self.p_orbite = self.curseur('periode_orbite', 8.0, 60.0, 20.0, dec=1)
        self.c_couleurs = self.coche('couleurs', True)
        self.etat_initial()

    def etat_initial(self):
        self.t = 0.0
        self.n_emis = 0
        self.impulsions = []          # (t_e, x_e, y_e, t_a, v_r)
        self.arrivees = []            # (t_a, intervalle, v_r)
        self._derniere = None

    def reglage_change(self):
        cle = (self.mouvement.currentData(), self.p_pulsar.value(), self.p_orbite.value())
        if getattr(self, '_cle', cle) != cle:
            self.etat_initial()
        self._cle = cle
        super().reglage_change()

    def position(self, t):
        if self.mouvement.currentData() == 'immobile':
            return 0.0, 0.0, 0.0
        w = 2 * math.pi / self.p_orbite.value()
        x, y = R_ORBITE * math.cos(w * t), R_ORBITE * math.sin(w * t)
        vx, vy = -R_ORBITE * w * math.sin(w * t), R_ORBITE * w * math.cos(w * t)
        dx, dy = D_TERRE - x, -y
        n = math.hypot(dx, dy)
        return x, y, -(vx * dx + vy * dy) / n            # v_r > 0 : le pulsar s'éloigne de la Terre

    def avancer(self, dt):
        self.t += dt
        p = self.p_pulsar.value()
        while self.n_emis * p <= self.t:
            te = self.n_emis * p
            x, y, vr = self.position(te)
            ta = te + math.hypot(D_TERRE - x, y) / C
            self.impulsions.append((te, x, y, ta, vr))
            self.n_emis += 1
        restantes = []
        for imp in self.impulsions:
            if imp[3] <= self.t:
                if self._derniere is not None:
                    self.arrivees.append((imp[3], imp[3] - self._derniere, imp[4]))
                self._derniere = imp[3]
            else:
                restantes.append(imp)
        self.impulsions = restantes
        while self.arrivees and self.arrivees[0][0] < self.t - FENETRE:
            self.arrivees.pop(0)

    def extremes(self):
        """Intervalles d'arrivée extrêmes prévus au premier ordre : P (1 ± v / c)."""
        p = self.p_pulsar.value()
        if self.mouvement.currentData() == 'immobile':
            return p, p
        v = 2 * math.pi * R_ORBITE / self.p_orbite.value()
        return p * (1 - v / C), p * (1 + v / C)

    def valeurs(self):
        mini, maxi = self.extremes()
        out = [(tr('anim_pulsarperiodsim_p_vraie'), nombre(self.p_pulsar.value(), 3)),
               (tr('anim_pulsarperiodsim_v_c'), nombre((maxi / self.p_pulsar.value() - 1), 3)),
               (tr('anim_pulsarperiodsim_prevu'), '%s – %s' % (nombre(mini, 3), nombre(maxi, 3)))]
        if self.arrivees:
            iv = [a[1] for a in self.arrivees]
            out.append((tr('anim_pulsarperiodsim_mesure'), '%s – %s' % (nombre(min(iv), 3), nombre(max(iv), 3))))
        return out

    def _couleur(self, vr):
        if not self.c_couleurs.isChecked() or self.mouvement.currentData() == 'immobile':
            return 'accent1'
        return 'accent3' if vr > 0 else 'accent2'

    def dessiner(self, p, rect):
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.5)
        r = dessin.cadre(p, haut, tr('anim_pulsarperiodsim_titre_scene'))
        k = min(r.width() / (D_TERRE + 3.0), r.height() / 2.8)
        ox, oy = r.left() + 1.5 * k, r.center().y()
        if self.mouvement.currentData() == 'orbite':
            p.setPen(dessin.stylo('grille', 1.0, None, True))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(ox, oy), R_ORBITE * k, R_ORBITE * k)
        x, y, vr = self.position(self.t)
        for te, xe, ye, ta, v in self.impulsions:
            f = (self.t - te) / (ta - te)
            px, py = ox + (xe + (D_TERRE - xe) * f) * k, oy - (ye * (1 - f)) * k
            p.setPen(dessin.stylo(self._couleur(v), 2.5))
            p.drawLine(QPointF(px, py - 6), QPointF(px, py + 6))
        dessin.disque(p, ox + x * k, oy - y * k, 6, 'accent1', bord='texte')
        dessin.texte(p, ox + x * k, oy - y * k - 14, tr('anim_pulsarperiodsim_pulsar'), 'accent1', fond=True)
        dessin.disque(p, ox + D_TERRE * k, oy, 9, 'terre', bord='texte')
        dessin.texte(p, ox + D_TERRE * k, oy + 20, tr('anim_planete_terre'), 'doux')
        # intervalles d'arrivée
        r2 = dessin.cadre(p, QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height()),
                          tr('anim_pulsarperiodsim_titre_graphe'))
        mini, maxi = self.extremes()
        marge = 0.15 * max(maxi - mini, 0.1 * self.p_pulsar.value())
        t1 = max(self.t, FENETRE)
        ax = Axes(r2, t1 - FENETRE, t1, mini - marge, maxi + marge, marges=(48, 8, 10, 26)).avec(p)
        ax.fond(p, tr('anim_pulsarperiodsim_axe_t'), tr('anim_pulsarperiodsim_axe_i'), dec_y=2)
        ax.horizontale(self.p_pulsar.value(), 'doux', 1.0, True, tr('anim_pulsarperiodsim_p_vraie'))
        groupes = {}
        for ta, iv, v in self.arrivees:
            groupes.setdefault(self._couleur(v), []).append((ta, iv))
        for cle, pts in groupes.items():
            ax.points(pts, cle, 2.6, 1.0)
