"""Les éléments d'une orbite : les six nombres qui fixent l'orbite d'un satellite autour de la Terre et sa position —
demi-grand axe a, excentricité e, inclinaison i, longitude du nœud ascendant Ω, argument du périgée ω, et le temps
(anomalie moyenne M).  Vue en 3D (plan de l'équateur, point vernal, ligne des nœuds, ligne des apsides, angles Ω, ω
et i dessinés) et trace au sol (la Terre tourne sous l'orbite).  Orbites types : station spatiale, héliosynchrone,
GPS, Molniya, géostationnaire.  Calculs : ``elements_orbitaux.py`` (équation de Kepler, vis-viva)."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, elements_orbitaux as eo
from ..base import Animation, angle, nombre
from .longitude_latitude import dessiner_cotes_carte

ORBITES_PAR_S = 0.1              # une révolution en 10 s à la vitesse ×1


def duree(t_s: float) -> str:
    """Durée en secondes → « 92 min 41 s », « 11 h 58 min » ou « 3,2 j »."""
    t = max(0.0, t_s)
    if t < 3600.0:
        m, s = divmod(int(round(t)), 60)
        return tr('anim_orbitalelements_d_ms', m=m, s='%02d' % s)
    if t < 4 * 86400.0:
        h, m = divmod(int(round(t / 60.0)), 60)
        return tr('anim_orbitalelements_d_hm', h=h, m='%02d' % m)
    return tr('anim_orbitalelements_d_j', j=nombre(t / 86400.0, 1))


class ElementsOrbite(Animation):
    ID = 'orbitalelements'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.vue3d = self.vue(20.0, 38.0)
        self.orbite = self.choix('orbite', [('anim_orbitalelements_o_libre', 'libre')] +
                                 [('anim_orbitalelements_o_' + k, k) for k in eo.ORBITES], 'libre')
        self.a = self.curseur('a', 6600.0, 100000.0, 18000.0, dec=0, unite='km', log=True)
        self.e = self.curseur('e', 0.0, 0.95, 0.3, dec=3)
        self.i = self.curseur('i', 0.0, 180.0, 40.0, dec=1, unite='°')
        self.om = self.curseur('noeud', 0.0, 360.0, 45.0, dec=1, unite='°')
        self.w = self.curseur('perigee', 0.0, 360.0, 60.0, dec=1, unite='°')
        self.c_angles = self.coche('angles', True)
        self.c_plan = self.coche('plan', True)
        self.c_trace = self.coche('trace', True)
        self._applique = self.orbite.currentData()
        self.etat_initial()

    def etat_initial(self):
        self.t = 0.0

    def reglage_change(self):
        k = self.orbite.currentData()
        if k != getattr(self, '_applique', k):
            self._applique = k
            if k in eo.ORBITES:
                a, e, i, om, w = eo.ORBITES[k]
                for r, v in ((self.a, a), (self.e, e), (self.i, i), (self.om, om), (self.w, w)):
                    r.setValue(v)
                self.t = 0.0
        super().reglage_change()

    def elements(self):
        return self.a.value(), self.e.value(), self.i.value(), self.om.value(), self.w.value()

    def anomalie_moyenne(self) -> float:
        return (360.0 * self.t / eo.periode_s(self.a.value())) % 360.0

    def avancer(self, dt):
        self.t += dt * ORBITES_PAR_S * eo.periode_s(self.a.value())

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        a, e, i, om, w = self.elements()
        m = self.anomalie_moyenne()
        s = eo.etat(a, e, i, om, w, m)
        rp, ra = a * (1 - e), a * (1 + e)
        km = tr('anim_orbitalelements_km')
        alt = tr('anim_orbitalelements_altitude')
        kms = 'km·s⁻¹'
        return [(tr('anim_orbitalelements_v_periode'), duree(eo.periode_s(a))),
                (tr('anim_orbitalelements_v_perigee'), '%s %s — %s %s %s' % (nombre(rp, 0), km, alt, nombre(rp - eo.R_TERRE_KM, 0), km)),
                (tr('anim_orbitalelements_v_apogee'), '%s %s — %s %s %s' % (nombre(ra, 0), km, alt, nombre(ra - eo.R_TERRE_KM, 0), km)),
                (tr('anim_orbitalelements_v_vitesses'), '%s / %s %s' % (nombre(eo.vitesse(rp, a), 2), nombre(eo.vitesse(ra, a), 2), kms)),
                (tr('anim_orbitalelements_v_position'), 'M = %s — ν = %s — %s %s %s — v = %s %s' % (
                    angle(m, 1), angle(s['nu'], 1), alt, nombre(s['r'] - eo.R_TERRE_KM, 0), km, nombre(s['v'], 2), kms)),
                (tr('anim_orbitalelements_v_temps'), duree(self.t)),
                (tr('anim_orbitalelements_v_genre'), tr('anim_orbitalelements_g_' + eo.genre_orbite(a, e, i)))]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        if self.c_trace.isChecked():
            z = dessin.zones_principale(rect, 2, 0.58)
            self._espace(p, dessin.cadre(p, z[0], tr('anim_orbitalelements_t_espace')))
            self._carte(p, dessin.cadre(p, z[1], tr('anim_orbitalelements_t_trace')))
            self._plan(p, dessin.cadre(p, z[2], tr('anim_orbitalelements_t_plan')))
        else:
            z = dessin.zones_principale(rect, 1, 0.62)
            self._espace(p, dessin.cadre(p, z[0], tr('anim_orbitalelements_t_espace')))
            self._plan(p, dessin.cadre(p, z[1], tr('anim_orbitalelements_t_plan')))

    def _espace(self, p, r):
        self.zone_rotative(r, self.vue3d)
        a, e, i, om, w = self.elements()
        rot = eo.rotation(i, om, w)
        ech = max(1.15 * a * (1 + e), 2.4 * eo.R_TERRE_KM)            # km pour une unité de la scène
        rr = min(r.width(), r.height()) * 0.44
        pe = dessin.Peintre3D(p, self.vue3d, r.center().x(), r.center().y(), rr)
        rt = eo.R_TERRE_KM / ech

        def u(v):
            return np.array(v, dtype=float) / ech

        # plan de l'équateur
        if self.c_plan.isChecked():
            pe.plan('equateur', 0.10, 1.0, 'equateur')
        # orbite : morceaux cachés par la Terre d'abord, puis la Terre, puis le reste (pointillé sous l'équateur)
        nus = np.linspace(0.0, 360.0, 361)
        pts = np.array([u(eo.point_orbite(a, e, rot, nu)) for nu in nus])
        xs, ys, zs, hs = pe.ecran(pts, repere_monde=True)
        cache = (zs < 0) & (np.hypot(xs - pe.cx, ys - pe.cy) < rt * rr)
        self._polyligne(p, xs, ys, cache, hs, True)
        xo, yo, _, _ = pe.ecran((0.0, 0.0, 0.0), repere_monde=True)
        dessin.disque(p, xo[0], yo[0], rt * rr, 'terre', bord='texte')
        pe.courbe(dessin.cercle((0, 0, 1)) * rt, 'equateur', 1.0, 0.8, arriere='cache', profondeur=False)
        pe.segment((0, 0, -1.25 * rt), (0, 0, 1.25 * rt), 'doux', 1.2, 0.9)
        self._polyligne(p, xs, ys, cache, hs, False)
        # point vernal, ligne des nœuds, ligne des apsides
        pe.segment((0, 0, 0), (1.0, 0, 0), 'accent1', 1.3, 0.9)
        pe.etiquette((1.06, 0, 0), tr('anim_orbitalelements_vernal'), 'accent1')
        n = np.array([math.cos(math.radians(om)), math.sin(math.radians(om)), 0.0])
        na = u(eo.point_orbite(a, e, rot, -w))
        nd = u(eo.point_orbite(a, e, rot, 180.0 - w))
        pe.segment(nd, na, 'arc1', 1.3, 0.9)
        pe.point(na, 'arc1', 4.5, etiquette=tr('anim_orbitalelements_noeud_asc'), toujours=True)
        pe.point(nd, 'arc1', 3.5, toujours=True)
        per = u(eo.point_orbite(a, e, rot, 0.0))
        apo = u(eo.point_orbite(a, e, rot, 180.0))
        if e > 0.005:
            pe.courbe(np.vstack([apo, per]), 'accent3', 1.1, 0.8, arriere='normal', profondeur=False)
            pe.point(per, 'accent3', 4.0, etiquette=tr('anim_orbitalelements_perigee_m'), toujours=True)
            pe.point(apo, 'accent3', 3.5, etiquette=tr('anim_orbitalelements_apogee_m'), toujours=True)
        # angles Ω (dans l'équateur), ω (dans le plan de l'orbite), i (au nœud ascendant)
        if self.c_angles.isChecked():
            k = max(0.30, 1.25 * rt)
            if om > 0.5:
                arc = np.array([(k * math.cos(t), k * math.sin(t), 0.0) for t in np.radians(np.linspace(0, om, 60))])
                pe.courbe(arc, 'accent1', 2.0, 1.0, arriere='normal', profondeur=False)
                pe.etiquette(arc[len(arc) // 2] * 1.18, 'Ω', 'accent1')
            if w > 0.5 and i > 0.5:
                kw = max(1.3 * rt, min(0.40, 0.8 * a * (1 - e) / ech))
                arc = np.array([np.array(eo.appliquer(rot, (kw * math.cos(t), kw * math.sin(t), 0.0)))
                                for t in np.radians(np.linspace(-w, 0.0, 60))])
                pe.courbe(arc, 'accent3', 2.0, 1.0, arriere='normal', profondeur=False)
                pe.etiquette(arc[len(arc) // 2] * 1.15, 'ω', 'accent3')
            if i > 0.5:
                h = np.array(eo.appliquer(rot, (0.0, 0.0, 1.0)))
                q_eq = np.array([-n[1], n[0], 0.0])
                q_or = np.cross(h, n)
                ki = 0.16
                arc = np.array([na + ki * (math.cos(t) * q_eq + math.sin(t) * np.cross(n, q_eq))
                                for t in np.radians(np.linspace(0.0, i, 40))])
                pe.courbe(arc, 'accent2', 2.0, 1.0, arriere='normal', profondeur=False)
                pe.segment(na, na + 0.24 * q_eq, 'accent2', 1.0, 0.7)
                pe.segment(na, na + 0.24 * q_or, 'accent2', 1.0, 0.7)
                pe.etiquette(arc[len(arc) // 2] * 1.0 + 0.06 * q_eq, 'i', 'accent2')
        # le satellite et sa vitesse
        s = eo.etat(a, e, i, om, w, self.anomalie_moyenne())
        sat = u(s['pos'])
        v = np.array(s['vit'])
        bout = sat + v / np.linalg.norm(v) * 0.16
        x0, y0, _, _ = pe.ecran(sat, repere_monde=True)
        x1, y1, _, _ = pe.ecran(bout, repere_monde=True)
        dessin.fleche(p, x0[0], y0[0], x1[0], y1[0], dessin.stylo('accent2', 1.6), 7)
        pe.point(sat, 'accent1', 5.5, bord='texte', etiquette=tr('anim_orbitalelements_satellite'), toujours=True)

    def _polyligne(self, p, xs, ys, cache, hs, cachee: bool):
        """Orbite : les points cachés par la Terre (cachee=True) ou les autres ; pointillé sous l'équateur."""
        for k in range(len(xs) - 1):
            if bool(cache[k] or cache[k + 1]) != cachee:
                continue
            dessous = (hs[k] + hs[k + 1]) < 0
            p.setPen(dessin.stylo('accent1', 2.0 if not cachee else 1.2, 0.35 if cachee else 1.0, pointille=dessous))
            p.drawLine(QPointF(xs[k], ys[k]), QPointF(xs[k + 1], ys[k + 1]))

    def _carte(self, p, r):
        w = min(r.width() - 10, (r.height() - 14) * 2.0)
        carte = QRectF(r.center().x() - w / 2, r.center().y() - w / 4, w, w / 2)

        def xy(la, lo):
            return QPointF(carte.x() + (lo + 180.0) / 360.0 * carte.width(), carte.y() + (90.0 - la) / 180.0 * carte.height())
        p.fillRect(carte, dessin.c('terre', 0.30))
        dessiner_cotes_carte(p, carte, 'texte', 0.7, 0.7)
        p.setPen(dessin.stylo('grille', 0.6, 0.6))
        for lo in range(-150, 181, 30):
            p.drawLine(xy(90, lo), xy(-90, lo))
        for la in (-60, -30, 30, 60):
            p.drawLine(xy(la, -180), xy(la, 180))
        p.setPen(dessin.stylo('equateur', 1.0, 0.9))
        p.drawLine(xy(0, -180), xy(0, 180))
        a, e, i, om, w_ = self.elements()
        t_orb = eo.periode_s(a)
        duree_trace = min(3.0 * t_orb, 2.0 * eo.JOUR_SIDERAL_S)
        tr_ = eo.trace_au_sol(a, e, i, om, w_, 0.0, max(0.0, self.t - duree_trace), self.t, 360)
        p.setPen(dessin.stylo('accent1', 1.6, 0.9))
        for k in range(len(tr_) - 1):
            (la0, lo0), (la1, lo1) = tr_[k], tr_[k + 1]
            if abs(lo1 - lo0) < 180.0:
                p.drawLine(xy(la0, lo0), xy(la1, lo1))
        la, lo = tr_[-1]
        q = xy(la, lo)
        dessin.disque(p, q.x(), q.y(), 5.0, 'accent1', bord='texte')

    def _plan(self, p, r):
        """L'orbite vue de face, dans son plan : la Terre au foyer, le périgée à droite, l'anomalie vraie ν, le rayon r
        et la direction du nœud ascendant (ν = −ω)."""
        a, e, i, om, w = self.elements()
        b = a * math.sqrt(1 - e * e)
        ech = min((r.width() - 30) / (2 * a), (r.height() - 30) / (2 * b)) if a > 0 else 1.0
        # centre de l'ellipse au centre du panneau ; foyer (Terre) décalé de a e vers la droite
        xc, yc = r.center().x(), r.center().y()
        fx = xc + a * e * ech

        def q(nu_deg):
            nu = math.radians(nu_deg)
            rr = a * (1 - e * e) / (1 + e * math.cos(nu))
            return QPointF(fx + rr * math.cos(nu) * ech, yc - rr * math.sin(nu) * ech)
        p.setPen(dessin.stylo('accent1', 1.8))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(xc, yc), a * ech, b * ech)
        dessin.disque(p, fx, yc, max(3.0, eo.R_TERRE_KM * ech), 'terre', bord='texte')
        p.setPen(dessin.stylo('accent3', 1.0, 0.8, pointille=True))
        p.drawLine(q(180.0), q(0.0))
        p.setPen(dessin.stylo('arc1', 1.0, 0.9, pointille=True))
        p.drawLine(q(180.0 - w), q(-w))
        dessin.texte(p, q(-w).x(), q(-w).y(), '☊', 'arc1', fond=True)
        s = eo.etat(a, e, i, om, w, self.anomalie_moyenne())
        m = q(s['nu'])
        p.setPen(dessin.stylo('accent2', 1.4))
        p.drawLine(QPointF(fx, yc), m)
        ra = max(3.0, eo.R_TERRE_KM * ech) + 14.0
        p.setPen(dessin.stylo('accent2', 1.6))
        p.drawArc(QRectF(fx - ra, yc - ra, 2 * ra, 2 * ra), 0, int(16 * s['nu']))
        dessin.texte(p, fx + 1.5 * ra * math.cos(math.radians(s['nu'] / 2)),
                     yc - 1.5 * ra * math.sin(math.radians(s['nu'] / 2)), 'ν', 'accent2', fond=True)
        dessin.disque(p, m.x(), m.y(), 5.0, 'accent1', bord='texte')
        if e > 0.005:
            dessin.texte(p, q(0.0).x() - 4, q(0.0).y() + 12, tr('anim_orbitalelements_perigee_m'), 'accent3')
