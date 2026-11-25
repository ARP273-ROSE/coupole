"""Rotation synchrone et libration : la Lune tourne sur elle-même en un mois, d'un mouvement uniforme, mais parcourt son
orbite elliptique à vitesse variable ; son équateur est incliné sur son orbite.  Vue de la Terre, elle semble osciller
d'est en ouest et du nord au sud : on finit par voir près de 60 % de sa surface.  Orbite vue de dessus (méridien
repère de la Lune), la Lune telle qu'on la voit (formations repères), courbe de la libration au fil du mois.
Calculs : ``libration.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import dessin, libration as lb
from ..base import Animation, angle, nombre
from ..graphe import Axes

JOURS_PAR_SECONDE = 3.0


class Libration(Animation):
    ID = 'libration'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.e = self.curseur('e', 0.0, 0.3, lb.E_LUNE, dec=4)
        self.i = self.curseur('i', 0.0, 20.0, lb.I_LUNE, dec=2, unite='°')
        self.varpi = self.curseur('varpi', 0.0, 360.0, 90.0, dec=0, unite='°')
        self.rotation = self.choix('rotation', [('anim_libration_r_synchrone', 'synchrone'),
                                                ('anim_libration_r_aucune', 'aucune')], 'synchrone')
        self.c_diurne = self.coche('diurne', True)
        self.c_grille = self.coche('grille', True)
        self.jours = 0.0
        self._cache = None

    def avancer(self, dt):
        self.jours = math.fmod(self.jours + dt * JOURS_PAR_SECONDE, lb.MOIS_SIDERAL_J)

    def m(self) -> float:
        return 2.0 * math.pi * self.jours / lb.MOIS_SIDERAL_J

    def synchrone(self) -> bool:
        return self.rotation.currentData() == 'synchrone'

    def lb_(self) -> tuple[float, float]:
        return lb.libration(self.m(), self.e.value(), self.i.value(), self.varpi.value(), self.synchrone())

    def fractions(self):
        rho = lb.rho_diurne(self.e.value()) if self.c_diurne.isChecked() else 0.0
        cle = (self.e.value(), self.i.value(), self.varpi.value(), self.synchrone(), rho)
        if self._cache is None or self._cache[0] != cle:
            self._cache = (cle, lb.fraction_mois(self.e.value(), self.i.value(), self.varpi.value(), self.synchrone(),
                                                 rho),
                           lb.fraction_annees(self.e.value(), self.i.value(), self.synchrone(), rho))
        return self._cache[1], self._cache[2]

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        l, b = self.lb_()
        e = self.e.value()
        mois, annees = self.fractions()
        approx = math.degrees(2.0 * e * math.sin(self.m()))
        out = [(tr('anim_libration_v_jour'), tr('anim_libration_jours', n=nombre(self.jours, 1))),
               (tr('anim_libration_v_l'), '%s (2e sin M : %s)' % (angle(l, 2), angle(approx, 2)) if self.synchrone()
                else angle(l, 1)),
               (tr('anim_libration_v_b'), angle(b, 2)),
               (tr('anim_libration_v_distance'), '%s km' % nombre(lb.distance(self.m(), e), 0)),
               (tr('anim_libration_v_mois'), '%s %%' % nombre(100.0 * mois, 1)),
               (tr('anim_libration_v_annees'), '%s %%' % nombre(100.0 * annees, 1))]
        if self.c_diurne.isChecked():
            out.append((tr('anim_libration_v_diurne'), angle(lb.rho_diurne(e), 2)))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.5)
        self._lune(p, dessin.cadre(p, z[0], tr('anim_libration_t_lune')))
        self._orbite(p, dessin.cadre(p, z[1], tr('anim_libration_t_orbite')))
        self._courbe(p, dessin.cadre(p, z[2], tr('anim_libration_t_courbe')))

    def _lune(self, p, r):
        l, b = self.lb_()
        R = 0.42 * min(r.width(), r.height() - 30)
        cx, cy = r.center().x(), r.center().y() + 4
        p.save()
        p.setPen(dessin.stylo('doux', 1.0))
        p.setBrush(dessin.c('lune', 0.55))
        p.drawEllipse(QPointF(cx, cy), R, R)
        if self.c_grille.isChecked():
            for lat in range(-60, 61, 30):                   # parallèles
                self._ligne(p, cx, cy, R, [(lat, lo) for lo in range(-180, 181, 5)], l, b, 'grille')
            for lo in range(-180, 180, 30):                  # méridiens ; ±90° : limbe moyen, en couleur
                cle = 'accent2' if lo in (-90, 90) else ('accent1' if lo == 0 else 'grille')
                self._ligne(p, cx, cy, R, [(la, lo) for la in range(-90, 91, 5)], l, b, cle)
        for k, la, lo in lb.FORMATIONS:
            x, y, zz = lb.projection(la, lo, l, b)
            if zz > 0.0:
                dessin.disque(p, cx + R * x, cy - R * y, 4.0, 'accent3')
                dessin.etiquette(p, cx + R * x, cy - R * y, tr('anim_libration_f_' + k), 'texte')
        p.restore()
        dessin.texte(p, cx, r.bottom() - 10, tr('anim_libration_legende_lune'), 'doux', fond=True)

    def _ligne(self, p, cx, cy, R, pts, l, b, cle):
        p.setPen(dessin.stylo(cle, 1.4 if cle != 'grille' else 0.8, 0.9))
        prec = None
        for la, lo in pts:
            x, y, zz = lb.projection(la, lo, l, b)
            q = QPointF(cx + R * x, cy - R * y) if zz >= 0.0 else None
            if q is not None and prec is not None:
                p.drawLine(prec, q)
            prec = q

    def _orbite(self, p, r):
        e = self.e.value()
        m = self.m()
        a = 1.0
        demi = a * (1.0 + e) * 1.25
        cote = min(r.width(), r.height() - 6)
        k = cote / (2.0 * demi)
        cx, cy = r.center().x() + k * a * e / 2.0, r.center().y() + 3

        def pt(x, y):
            return QPointF(cx + k * x, cy - k * y)
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('grille', 1.2))
        bb = a * math.sqrt(1.0 - e * e)
        p.drawEllipse(pt(-a * e, 0.0), a * k, bb * k)
        dessin.disque(p, cx, cy, 7.0, 'terre')
        nu = lb.anomalie_vraie(m, e)
        d = a * (1.0 - e * e) / (1.0 + e * math.cos(nu))
        q = pt(d * math.cos(nu), d * math.sin(nu))
        rl = 0.11 * cote
        dessin.disque(p, q.x(), q.y(), rl, 'lune')
        # vers la Terre (trait fin) et méridien repère de la Lune (trait épais)
        p.setPen(dessin.stylo('doux', 1.0, 0.8, pointille=True))
        p.drawLine(q, QPointF(cx, cy))
        rot = (m if self.synchrone() else 0.0) + math.pi
        p.setPen(dessin.stylo('accent1', 2.4))
        p.drawLine(q, QPointF(q.x() + rl * 1.5 * math.cos(rot), q.y() - rl * 1.5 * math.sin(rot)))
        p.restore()
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_libration_legende_orbite'), 'doux', centre=False,
                     fond=True)

    def _courbe(self, p, r):
        lim = 10.0 if self.synchrone() else 180.0
        limb = max(10.0, self.i.value() * 1.2)
        ax = Axes(r, -lim, lim, -limb, limb, marges=(40, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_libration_axe_l'), tr('anim_libration_axe_b'))
        pts = [lb.libration(2.0 * math.pi * j / 240, self.e.value(), self.i.value(), self.varpi.value(),
                            self.synchrone()) for j in range(241)]
        if self.synchrone():
            ax.courbe(pts, 'accent2', 1.6)
        else:
            ax.points(pts, 'accent2', 1.4)
        l, b = self.lb_()
        dessin.disque(p, ax.px(l), ax.py(b), 5.0, 'accent3', 'texte')
