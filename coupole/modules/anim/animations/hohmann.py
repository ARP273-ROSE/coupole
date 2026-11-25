"""Le transfert de Hohmann : passer d'une orbite circulaire à une autre avec deux poussées, au départ et à l'arrivée,
en parcourant une demi-ellipse tangente aux deux orbites.  Orbite basse → géostationnaire, → station spatiale, → Lune ;
Terre → Mars, Vénus, Jupiter autour du Soleil.  Bilan des vitesses (Δv), durée, angle de phase et fenêtres de tir :
partir trop tôt ou trop tard, et la cible n'est pas au rendez-vous.  Calculs : ``hohmann_meca.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, hohmann_meca as hm
from ..base import Animation, angle, nombre
from .elements_orbite import duree

DUREE_TRANSFERT_S = 6.0          # secondes réelles pour la demi-ellipse, à la vitesse ×1
COULEURS = {'terre': 'terre', 'mars': 'mars', 'venus': 'arc2', 'jupiter': 'ecliptique', 'lune': 'lune',
            'geo_sat': 'accent3', 'iss': 'accent3', 'leo': 'accent1'}


def signe(x: float, dec: int = 3) -> str:
    return ('+' if x >= 0 else '') + nombre(x, dec)


class Hohmann(Animation):
    ID = 'hohmann'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.scenario = self.choix('scenario', [('anim_hohmann_s_' + k, k) for k in hm.SCENARIOS], 'terre_mars')
        self.c_auto = self.coche('auto', True)
        self.c_fantome = self.coche('fantome', True)
        self.bouton('anim_hohmann_lancer', self.lancer)
        self.bouton('anim_hohmann_recommencer', self.recommencer)
        self._scenario = self.scenario.currentData()
        self.etat_initial()

    # ------------------------------------------------------------ état
    def etat_initial(self):
        self.t = 0.0
        self.t_depart = None
        self.theta_depart = 0.0

    def recommencer(self):
        self.etat_initial()
        self.rafraichir()

    def reglage_change(self):
        k = self.scenario.currentData()
        if k != getattr(self, '_scenario', k):
            self._scenario = k
            self.etat_initial()
        super().reglage_change()

    def donnees(self):
        mu, r1, r2, dep, arr, cible, avance = hm.SCENARIOS[self.scenario.currentData()]
        return mu, r1, r2, dep, arr, cible, avance, hm.bilan(mu, r1, r2)

    def angles(self, t: float):
        """Angles (radians) du point de départ et de la cible à l'instant t."""
        mu, r1, r2, dep, arr, cible, avance, b = self.donnees()
        return b['n1'] * t, math.radians(avance) + b['n2'] * t

    def etape(self) -> str:
        if self.t_depart is None:
            return 'attente'
        _, _, _, _, _, _, _, b = self.donnees()
        return 'transfert' if self.t < self.t_depart + b['t'] else 'arrive'

    def lancer(self):
        if self.t_depart is None:
            self.t_depart = self.t
            self.theta_depart = self.angles(self.t)[0]
            self.rafraichir()

    def avancer(self, dt):
        _, _, _, _, _, _, avance, b = self.donnees()
        dtp = dt * b['t'] / DUREE_TRANSFERT_S
        if self.t_depart is None and self.c_auto.isChecked():
            tw = self.t + hm.attente_fenetre(b, self.avance_actuelle())
            if tw <= self.t + dtp:
                self.t_depart = tw
                self.theta_depart = self.angles(tw)[0]
        self.t += dtp

    def avance_actuelle(self) -> float:
        """Avance angulaire de la cible sur le point de départ (degrés, −180…180)."""
        a1, a2 = self.angles(self.t)
        return (math.degrees(a2 - a1) + 180.0) % 360.0 - 180.0

    def vaisseau(self):
        """Rayon (km) et angle (radians) du vaisseau."""
        mu, r1, r2, dep, arr, cible, avance, b = self.donnees()
        e = self.etape()
        if e == 'attente':
            return r1, self.angles(self.t)[0]
        if e == 'transfert':
            return hm.position_transfert(b, r1, r2, self.theta_depart, self.t - self.t_depart)
        return r2, self.theta_depart + math.pi + b['n2'] * (self.t - self.t_depart - b['t'])

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        mu, r1, r2, dep, arr, cible, avance, b = self.donnees()
        kms = 'km·s⁻¹'
        out = [(tr('anim_hohmann_v_dv1'), '%s %s (%s → %s)' % (signe(b['dv1']), kms, nombre(b['v1'], 3), nombre(b['vd'], 3))),
               (tr('anim_hohmann_v_dv2'), '%s %s (%s → %s)' % (signe(b['dv2']), kms, nombre(b['va'], 3), nombre(b['v2'], 3))),
               (tr('anim_hohmann_v_dv'), '%s %s' % (nombre(b['dv'], 3), kms)),
               (tr('anim_hohmann_v_duree'), duree(b['t'])),
               (tr('anim_hohmann_v_phase'), angle(b['phase'], 1)),
               (tr('anim_hohmann_v_synodique'), duree(b['synodique']))]
        e = self.etape()
        if e == 'attente':
            out.append((tr('anim_hohmann_v_avance'), angle(self.avance_actuelle(), 1)))
            out.append((tr('anim_hohmann_v_etat'), tr('anim_hohmann_e_attente',
                                                      d=duree(hm.attente_fenetre(b, self.avance_actuelle())))))
        elif e == 'transfert':
            out.append((tr('anim_hohmann_v_etat'), tr('anim_hohmann_e_transfert', d=duree(self.t - self.t_depart))))
        else:
            ecart = self.ecart()
            if abs(ecart) < 2.0:
                out.append((tr('anim_hohmann_v_etat'), tr('anim_hohmann_e_reussi')))
            else:
                out.append((tr('anim_hohmann_v_etat'), tr('anim_hohmann_e_rate_avance' if ecart > 0 else
                                                          'anim_hohmann_e_rate_retard', x=angle(abs(ecart), 1))))
        return out

    def ecart(self) -> float:
        """Avance de la cible sur le vaisseau à l'arrivée (degrés)."""
        _, _, _, _, _, _, avance, b = self.donnees()
        a1, a2 = self.angles(self.t_depart)
        return hm.ecart_rendez_vous(b, math.degrees(a2 - a1))

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.68)
        self._orbites(p, dessin.cadre(p, z[0], tr('anim_hohmann_t_orbites')))
        self._vitesses(p, dessin.cadre(p, z[1], tr('anim_hohmann_t_vitesses')))

    def _orbites(self, p, r):
        mu, r1, r2, dep, arr, cible, avance, b = self.donnees()
        ech = min(r.width(), r.height()) / 2.0 / (1.12 * max(r1, r2))
        cx, cy = r.center().x(), r.center().y()

        def pt(rad, th):
            return QPointF(cx + rad * ech * math.cos(th), cy - rad * ech * math.sin(th))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('accent2', 1.2, 0.8))
        p.drawEllipse(QPointF(cx, cy), r1 * ech, r1 * ech)
        p.setPen(dessin.stylo('accent3', 1.2, 0.8))
        p.drawEllipse(QPointF(cx, cy), r2 * ech, r2 * ech)
        soleil = mu == hm.MU_SOLEIL
        dessin.disque(p, cx, cy, 9.0 if soleil else max(4.0, hm.R_T * ech), 'soleil' if soleil else 'terre',
                      bord=None if soleil else 'texte')
        etape = self.etape()
        a1, a2 = self.angles(self.t)
        # demi-ellipse de transfert : prévue (pointillés) avant le départ, parcourue ensuite
        th0 = a1 if etape == 'attente' else self.theta_depart
        n = 90
        pts = [pt(*hm.position_transfert(b, r1, r2, th0, b['t'] * k / n)) for k in range(n + 1)]
        p.setPen(dessin.stylo('accent1', 1.8 if etape != 'attente' else 1.2, 0.95, pointille=etape == 'attente'))
        p.drawPolyline(dessin.polygone([q.x() for q in pts], [q.y() for q in pts]))
        # angle de phase : avance de la cible maintenant (avant le départ)
        if etape == 'attente':
            ra = min(r1, r2) * ech * 0.55
            d0 = math.degrees(a1)
            p.setPen(dessin.stylo('arc1', 1.6))
            p.drawArc(QRectF(cx - ra, cy - ra, 2 * ra, 2 * ra), int(16 * d0), int(16 * self.avance_actuelle()))
            p.setPen(dessin.stylo('arc1', 0.9, 0.7, pointille=True))
            p.drawLine(QPointF(cx, cy), pt(r1, a1))
            p.drawLine(QPointF(cx, cy), pt(r2, a2))
            if self.c_fantome.isChecked():
                # où sera la cible à l'arrivée si l'on part maintenant
                g = pt(r2, a2 + b['n2'] * b['t'])
                p.setPen(dessin.stylo(COULEURS[cible], 1.4, 0.9, pointille=True))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawEllipse(g, 7.0, 7.0)
                dessin.texte(p, g.x(), g.y() - 16, tr('anim_hohmann_fantome_m'), 'doux', fond=True)
        # départ, cible, vaisseau
        if soleil:
            q = pt(r1, a1)
            dessin.disque(p, q.x(), q.y(), 6.0, 'terre', bord='texte')
            dessin.texte(p, q.x(), q.y() + 15, tr('anim_hohmann_n_terre'), 'doux', fond=True)
        q = pt(r2, a2)
        dessin.disque(p, q.x(), q.y(), 6.0, COULEURS[cible], bord='texte')
        dessin.texte(p, q.x(), q.y() - 15, tr('anim_hohmann_n_' + cible), 'texte', fond=True)
        rv, tv = self.vaisseau()
        v = pt(rv, tv)
        dessin.disque(p, v.x(), v.y(), 4.0, 'accent1', bord='texte')
        # poussées : flèches tangentes, longueur proportionnelle au Δv
        k = 0.6 * min(r.width(), r.height()) / max(1e-9, max(abs(b['dv1']), abs(b['dv2'])) * 6.0)
        if etape != 'attente':
            self._poussee(p, pt(r1, self.theta_depart), self.theta_depart, b['dv1'] * k, 'Δv₁')
        if etape == 'arrive':
            ta = self.theta_depart + math.pi
            self._poussee(p, pt(r2, ta), ta, b['dv2'] * k, 'Δv₂')

    def _poussee(self, p, q, th, longueur, nom):
        """Flèche tangente (sens du mouvement si longueur > 0) au point q de l'orbite d'angle th."""
        dx, dy = -math.sin(th), -math.cos(th)                 # tangente directe, y de l'écran vers le bas
        lg = max(12.0, abs(longueur)) * (1 if longueur >= 0 else -1)
        dessin.fleche(p, q.x(), q.y(), q.x() + lg * dx, q.y() + lg * dy, dessin.stylo('accent3', 2.2), 8)
        dessin.texte(p, q.x() + lg * dx + 12, q.y() + lg * dy - 10, nom, 'accent3', fond=True)

    def _vitesses(self, p, r):
        """Barres des quatre vitesses : orbite de départ, ellipse au départ, ellipse à l'arrivée, orbite d'arrivée."""
        mu, r1, r2, dep, arr, cible, avance, b = self.donnees()
        lignes = [('anim_hohmann_b_v1', b['v1'], 'accent2'), ('anim_hohmann_b_vd', b['vd'], 'accent1'),
                  ('anim_hohmann_b_va', b['va'], 'accent1'), ('anim_hohmann_b_v2', b['v2'], 'accent3')]
        vmax = max(v for _, v, _ in lignes) * 1.08
        h = r.height() / (len(lignes) + 1.2)
        x0, larg = r.x() + 8, r.width() - 16
        for k, (cle, v, col) in enumerate(lignes):
            y = r.y() + 6 + k * h
            dessin.texte(p, x0, y + 9, tr(cle), 'doux', centre=False)
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c(col, 0.85))
            p.drawRoundedRect(QRectF(x0, y + 20, larg * v / vmax, max(8.0, h * 0.32)), 3, 3)
            dessin.texte(p, x0 + 4, y + 20 + max(8.0, h * 0.32) + 11, '%s km·s⁻¹' % nombre(v, 2), 'texte', centre=False)
        dessin.texte(p, x0, r.bottom() - 12, tr('anim_hohmann_total', dv=nombre(b['dv'], 2)), 'accent3', centre=False)
