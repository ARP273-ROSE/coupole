"""L'assistance gravitationnelle : une sonde frôle une planète.  Vue de la planète, elle arrive et repart à la même
vitesse v∞, simplement tournée de δ ; vue du Soleil, on ajoute la vitesse de la planète, et la sonde repart plus
vite (passage derrière la planète) ou moins vite (devant).  Hyperbole du survol, triangle des vitesses, orbites
autour du Soleil avant et après.  Calculs : ``assistance.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import assistance as ga, dessin
from ..base import Animation, angle, nombre

DUREE = 5.0                      # secondes réelles pour un survol complet
N_CONIQUE = 360


def vitesse(v: float) -> str:
    return '%s km·s⁻¹' % nombre(v, 2)


def conique_soleil(a_ua: float, v: tuple[float, float], r_max: float) -> list:
    """Points (ua) de l'orbite autour du Soleil d'une sonde en (a, 0) de vitesse v = (vₜ le long du mouvement de la
    planète, vᵣ vers l'extérieur) ; la planète tourne dans le sens direct (vₜ selon +y).  Morceaux séparés par None
    là où la courbe sort du cadre ou part à l'infini."""
    mu = ga.GM_SOLEIL
    r = a_ua * ga.UA
    vt, vr = v
    vx, vy = vr, vt
    v2 = vx * vx + vy * vy
    rv = r * vx
    ex = ((v2 - mu / r) * r - rv * vx) / mu
    ey = (-rv * vy) / mu
    e = math.hypot(ex, ey)
    w = math.atan2(ey, ex)
    h = r * vy
    p = h * h / mu / ga.UA
    out = []
    for j in range(N_CONIQUE + 1):
        th = 2.0 * math.pi * j / N_CONIQUE
        d = 1.0 + e * math.cos(th - w)
        rr = p / d if d > 1e-6 else math.inf
        if rr > r_max:
            if out and out[-1] is not None:
                out.append(None)
            continue
        out.append((rr * math.cos(th), rr * math.sin(th)))
    return out


class Assistance(Animation):
    ID = 'gravityassist'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.planete = self.choix('planete', [('anim_gravityassist_p_' + k, k) for k, *_ in ga.PLANETES], 'jupiter')
        self.v_inf = self.curseur('vinf', 1.0, 20.0, 5.6, dec=1, unite='km·s⁻¹')
        self.r_p = self.curseur('rp', 1.02, 50.0, 5.0, dec=2, log=True)
        self.angle = self.curseur('angle', 0.0, 360.0, 170.0, dec=0, unite='°')
        self.cote = self.choix('cote', [('anim_gravityassist_derriere', 'derriere'),
                                        ('anim_gravityassist_devant', 'devant')], 'derriere')
        self.c_soleil = self.coche('soleil', True)
        self.t = 0.0

    def avancer(self, dt):
        self.t = math.fmod(self.t + dt / DUREE, 1.0)

    def survol(self):
        return ga.survol(self.planete.currentData(), self.v_inf.value(), self.r_p.value(), self.angle.value(),
                         self.cote.currentData() == 'derriere')

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        s = self.survol()
        gm, rayon, _ = ga.planete(self.planete.currentData())
        oa = s['orb_out']
        if math.isinf(oa['Q']):
            apres = tr('anim_gravityassist_liberee')
        else:
            apres = tr('anim_gravityassist_orbite', q=nombre(oa['q'], 2), Q=nombre(oa['Q'], 2))
        oi = s['orb_in']
        avant = tr('anim_gravityassist_liberee') if math.isinf(oi['Q']) else \
            tr('anim_gravityassist_orbite', q=nombre(oi['q'], 2), Q=nombre(oi['Q'], 2))
        return [(tr('anim_gravityassist_v_V'), vitesse(s['V'])),
                (tr('anim_gravityassist_v_rp'), '%s km' % nombre(s['r_p'] - rayon, 0)),
                (tr('anim_gravityassist_v_delta'), angle(math.degrees(s['delta']), 1)),
                (tr('anim_gravityassist_v_peri'), vitesse(s['v_peri'])),
                (tr('anim_gravityassist_v_dv'), vitesse(s['dv'])),
                (tr('anim_gravityassist_v_avant_apres'), '%s → %s' % (vitesse(math.hypot(*s['v_in'])),
                                                                    vitesse(math.hypot(*s['v_out'])))),
                (tr('anim_gravityassist_v_gain'), ('+' if s['gain'] >= 0.0 else '') + vitesse(s['gain'])),
                (tr('anim_gravityassist_v_avant'), avant),
                (tr('anim_gravityassist_v_apres'), apres)]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.5)
        s = self.survol()
        self._planete(p, dessin.cadre(p, z[0], tr('anim_gravityassist_t_planete')), s)
        self._vitesses(p, dessin.cadre(p, z[1], tr('anim_gravityassist_t_vitesses')), s)
        self._soleil(p, dessin.cadre(p, z[2], tr('anim_gravityassist_t_soleil')), s)

    def _planete(self, p, r, s):
        gm, rayon, _ = ga.planete(self.planete.currentData())
        demi = max(2.5 * s['r_p'], 1.5 * s['b'], 3.0 * rayon)
        cote = min(r.width(), r.height() - 6)
        k = cote / (2.0 * demi)
        cx, cy = r.center().x(), r.center().y() + 3

        def pt(x, y):
            return QPointF(cx + k * x, cy - k * y)
        a = s['r_p'] / (s['e'] - 1.0)
        f_max = math.acosh(min(1e6, (demi * 1.5 / a + 1.0) / s['e']))
        p.save()
        p.setClipRect(r)
        # asymptote d'entrée (pointillé) et trajectoire
        pts = [ga.hyperbole(s, gm, -f_max + 2.0 * f_max * j / 200) for j in range(201)]
        p.setPen(dessin.stylo('accent2', 1.6))
        for q0, q1 in zip(pts[:-1], pts[1:]):
            p.drawLine(pt(*q0), pt(*q1))
        pl = self.planete.currentData()
        dessin.disque(p, cx, cy, max(3.0, rayon * k), {'terre': 'terre', 'mars': 'mars', 'venus': 'lune', 'jupiter': 'ecliptique', 'saturne': 'soleil'}[pl])
        # sonde
        n_ = math.sqrt(gm / a ** 3)
        t_max = (s['e'] * math.sinh(f_max) - f_max) / n_
        f = ga.anomalie(s, gm, (2.0 * self.t - 1.0) * t_max)
        q = pt(*ga.hyperbole(s, gm, f))
        dessin.disque(p, q.x(), q.y(), 4.0, 'accent3', 'texte')
        p.restore()
        # sens de la planète, direction du Soleil
        x0, y0 = r.left() + 14, r.bottom() - 34
        dessin.fleche(p, x0, y0, x0 + 40, y0, dessin.stylo('accent1', 1.6))
        dessin.texte(p, x0 + 46, y0, tr('anim_gravityassist_mouvement'), 'accent1', centre=False, fond=True)
        dessin.fleche(p, x0, y0 + 6, x0, y0 + 24, dessin.stylo('soleil', 1.6), 6.0)
        dessin.texte(p, x0 + 8, y0 + 18, tr('anim_gravityassist_vers_soleil'), 'doux', centre=False, fond=True)

    def _vitesses(self, p, r, s):
        vmax = max(math.hypot(*s['v_in']), math.hypot(*s['v_out']), s['V'] + self.v_inf.value())
        k = min(r.width() - 20, (r.height() - 20) * 2.0) / (2.0 * vmax)
        ox, oy = r.left() + r.width() / 2.0 - k * s['V'] / 2.0, r.center().y() + 8

        def pt(vx, vy):
            return QPointF(ox + k * vx, oy - k * vy)
        V = s['V']
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('grille', 1.0, 0.9, pointille=True))
        p.drawEllipse(pt(V, 0.0), k * self.v_inf.value(), k * self.v_inf.value())
        dessin.fleche(p, ox, oy, pt(V, 0).x(), pt(V, 0).y(), dessin.stylo('accent1', 2.0))
        for cle, v, coul in (('in', s['v_in'], 'accent2'), ('out', s['v_out'], 'accent3')):
            dessin.fleche(p, ox, oy, pt(*v).x(), pt(*v).y(), dessin.stylo(coul, 2.0))
            dessin.fleche(p, pt(V, 0).x(), pt(V, 0).y(), pt(*v).x(), pt(*v).y(), dessin.stylo(coul, 1.2, 0.7,
                                                                                               pointille=True))
            dessin.etiquette(p, pt(*v).x(), pt(*v).y(), tr('anim_gravityassist_e_' + cle), coul)
        dessin.etiquette(p, pt(V / 2.0, 0).x(), pt(V / 2.0, 0).y(), 'V', 'accent1')
        p.restore()

    def _soleil(self, p, r, s):
        if not self.c_soleil.isChecked():
            dessin.texte(p, r.center().x(), r.center().y(), tr('anim_gravityassist_cache'), 'doux')
            return
        _, _, a = ga.planete(self.planete.currentData())
        oi, oo = s['orb_in'], s['orb_out']
        ext = max(a, min(4.0 * a, max(oi['Q'] if math.isfinite(oi['Q']) else 0.0,
                                      oo['Q'] if math.isfinite(oo['Q']) else 0.0)))
        demi = 1.08 * ext
        cote = min(r.width(), r.height() - 6)
        k = cote / (2.0 * demi)
        cx, cy = r.center().x(), r.center().y() + 3

        def pt(x, y):
            return QPointF(cx + k * x, cy - k * y)
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('grille', 1.0))
        p.drawEllipse(pt(0, 0), a * k, a * k)
        dessin.disque(p, cx, cy, 5.0, 'soleil')
        for v, coul, pointille in ((s['v_in'], 'accent2', True), (s['v_out'], 'accent3', False)):
            pts = conique_soleil(a, v, 1.5 * demi)
            p.setPen(dessin.stylo(coul, 1.6, None, pointille))
            for q0, q1 in zip(pts[:-1], pts[1:]):
                if q0 is not None and q1 is not None:
                    p.drawLine(pt(*q0), pt(*q1))
        dessin.disque(p, pt(a, 0).x(), pt(a, 0).y(), 4.0, 'doux')
        p.restore()
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_gravityassist_legende_soleil'), 'doux', centre=False,
                     fond=True)
