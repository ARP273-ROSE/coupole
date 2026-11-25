"""Occultation d'une étoile par un astéroïde : l'ombre de l'astéroïde (sa taille même, l'étoile étant à l'infini)
balaie la Terre ; chaque observateur voit l'étoile disparaître le temps qu'une corde de l'ombre défile devant lui
(durée = corde / vitesse).  Plusieurs observateurs alignés en travers de la trajectoire donnent des cordes parallèles,
d'où la taille et la forme de l'astéroïde (ellipse ajustée), aux erreurs de chronométrage près.  Une étoile géante,
projetée plus grande que l'astéroïde, n'est cachée qu'en partie.  Calculs : ``occultation.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, occultation as oc
from ..base import Animation, nombre
from ..graphe import Axes

DUREE_PASSAGE = 8.0             # secondes réelles pour un passage complet de l'ombre, à la vitesse ×1


def km(x: float) -> str:
    """Longueur en km (en m sous le kilomètre)."""
    if x < 1.0:
        return '%s m' % nombre(x * 1000.0, 0)
    return '%s km' % nombre(x, 1 if x < 100 else 0)


class Occultation(Animation):
    ID = 'occultation'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.objet = self.choix('objet', [('anim_occultation_o_' + k, k) for k, *_ in oc.OBJETS] +
                                [('anim_occultation_o_libre', 'libre')], 'ceinture')
        self.diametre = self.curseur('diametre', 1.0, 5000.0, 100.0, dec=1, unite='km', log=True)
        self.forme = self.curseur('forme', 0.3, 1.0, 0.8, dec=2)
        self.orientation = self.curseur('orientation', -90.0, 90.0, 30.0, dec=0, unite='°')
        self.distance = self.curseur('distance', 1.5, 100.0, 2.5, dec=1, unite='ua', log=True)
        self.n_stations = self.curseur('stations', 1.0, 11.0, 7.0, dec=0)
        self.espacement = self.curseur('espacement', 0.1, 1000.0, 15.0, dec=1, unite='km', log=True)
        self.decalage = self.curseur('decalage', -1.0, 1.0, 0.1, dec=2)
        self.etoile = self.curseur('etoile', 0.0, 50.0, 0.1, dec=2, unite='mas')
        self.sigma = self.curseur('sigma', 0.0, 1.0, 0.1, dec=2, unite='s')
        self.c_vraie = self.coche('vraie', True)
        self.c_ajuster = self.coche('ajuster', True)
        self._objet = self.objet.currentData()
        self.t = None

    def reglage_change(self):
        k = self.objet.currentData()
        if k != getattr(self, '_objet', k):
            self._objet = k
            for cle, d, f, psi, r in oc.OBJETS:
                if cle == k:
                    self.diametre.setValue(d)
                    self.forme.setValue(f)
                    self.orientation.setValue(psi)
                    self.distance.setValue(r)
                    self.espacement.setValue(d / 6.0)
        super().reglage_change()

    # ------------------------------------------------------------ calculs
    def ellipse(self) -> oc.Ellipse:
        a = self.diametre.value() / 2.0
        return oc.Ellipse(a, a * self.forme.value(), self.orientation.value(), 0.0,
                          self.decalage.value() * self.diametre.value())

    def v(self) -> float:
        return oc.vitesse_ombre(self.distance.value())

    def r_etoile(self) -> float:
        return oc.etoile_km(self.etoile.value(), oc.distance_terre(self.distance.value())) / 2.0

    def ys(self) -> list:
        return oc.stations(int(round(self.n_stations.value())), self.espacement.value())

    def t_max(self) -> float:
        """Demi-durée (s) de la fenêtre montrée : l'ombre entre et sort du champ."""
        return (1.4 * self.diametre.value() / 2.0 + 2.0 * self.r_etoile()) / self.v()

    def instant(self) -> float:
        return -self.t_max() if self.t is None else self.t

    def avancer(self, dt):
        tm = self.t_max()
        t = self.instant() + dt * 2.0 * tm / DUREE_PASSAGE
        self.t = -tm if t > tm else t

    def mesures(self):
        el = self.ellipse()
        cs = oc.cordes(el, self.ys())
        return cs, oc.bruiter(cs, self.sigma.value() * self.v())

    def ajustement(self, bruitees):
        pts = [(x, y) for y, x1, x2 in bruitees if x1 is not None for x in (x1, x2)]
        return oc.ajuster_ellipse(pts)

    def valeurs(self):
        v, r = self.v(), self.distance.value()
        el = self.ellipse()
        cs, br = self.mesures()
        pos = [(x2 - x1) for _, x1, x2 in cs if x1 is not None]
        out = [(tr('anim_occultation_v_vitesse'), '%s km·s⁻¹' % nombre(v, 2)),
               (tr('anim_occultation_v_distance'), '%s ua' % nombre(oc.distance_terre(r), 2)),
               (tr('anim_occultation_v_cordes'), tr('anim_occultation_sur', n=len(pos), N=len(cs)))]
        if pos:
            L = max(pos)
            out.append((tr('anim_occultation_v_plus_longue'), tr('anim_occultation_duree_corde', d=nombre(L / v, 2),
                                                                 c=km(L))))
        aj = self.ajustement(br)
        d_vrai = 2.0 * math.sqrt(el.a * el.b)
        if aj is None:
            out.append((tr('anim_occultation_v_ajustee'), tr('anim_occultation_pas_assez')))
        else:
            out.append((tr('anim_occultation_v_ajustee'), '%s × %s' % (km(2 * aj[2]).replace(' km', ''), km(2 * aj[3]))))
            out.append((tr('anim_occultation_v_equivalent'),
                        tr('anim_occultation_vrai_ajuste', v=km(d_vrai), a=km(2.0 * math.sqrt(aj[2] * aj[3])))))
        out.append((tr('anim_occultation_v_erreur'), km(self.sigma.value() * v)))
        out.append((tr('anim_occultation_v_fresnel'), km(oc.fresnel_km(550.0, oc.distance_terre(r)))))
        re = 2.0 * self.r_etoile()
        out.append((tr('anim_occultation_v_etoile'), km(re) + ' — ' + tr(
            'anim_occultation_progressive' if re > 0.05 * 2.0 * el.b else 'anim_occultation_franche')))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.5)
        self._plan(p, dessin.cadre(p, z[0], tr('anim_occultation_t_plan')))
        self._courbes(p, dessin.cadre(p, z[1], tr('anim_occultation_t_courbes')))
        self._forme(p, dessin.cadre(p, z[2], tr('anim_occultation_t_forme')))

    def _echelle(self, r, ys, el):
        etendue = max(1.6 * el.a, max(abs(y) for y in ys) + 0.3 * el.a, abs(el.y0) + 1.2 * el.a)
        return min(r.width(), r.height() - 20) / (2.0 * etendue)

    def _plan(self, p, r):
        el = self.ellipse()
        ys = self.ys()
        t = self.instant()
        v = self.v()
        k = self._echelle(r, ys, el)
        cx, cy = r.center().x(), r.center().y() + 8
        xs = v * t                                             # centre de l'ombre (km, le long de la trajectoire)

        def pt(x, y):
            return QPointF(cx + k * x, cy - k * y)
        # trajectoire prévue du centre et sens du mouvement
        p.setPen(dessin.stylo('doux', 1.0, 0.6, pointille=True))
        p.drawLine(QPointF(r.x() + 8, cy), QPointF(r.right() - 8, cy))
        dessin.fleche(p, r.right() - 60, r.y() + 30, r.right() - 20, r.y() + 30, dessin.stylo('doux', 1.4), 7)
        dessin.texte(p, r.right() - 40, r.y() + 44, 'v', 'doux')
        # l'ombre
        ombre = oc.Ellipse(el.a, el.b, el.psi, xs, el.y0)
        p.setBrush(dessin.c('nuit', 0.75))
        p.setPen(dessin.stylo('accent2', 1.6))
        p.drawPolygon(dessin.polygone(*zip(*[(pt(x, y).x(), pt(x, y).y()) for x, y in ombre.contour()])))
        # cordes déjà parcourues, dessinées sur l'ombre
        for y, x1, x2 in oc.cordes(el, ys):
            if x1 is None:
                continue
            xr = -xs                                           # l'observateur vu depuis le centre de l'ombre
            if xr < x2:
                a_ = max(x1, xr)
                p.setPen(dessin.stylo('accent1', 2.4))
                p.drawLine(pt(xs + a_, y), pt(xs + x2, y))
        # le disque de l'étoile projeté, s'il est visible à cette échelle
        re = self.r_etoile()
        for y in ys:
            f = oc.fraction_cachee(el, -xs, y, re)
            q = pt(0.0, y)
            if re * k > 3.0:
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.setPen(dessin.stylo('accent3', 1.0, 0.6))
                p.drawEllipse(q, re * k, re * k)
            dessin.disque(p, q.x(), q.y(), 4.5, 'accent3' if f < 0.5 else 'grille', 'texte')
        dessin.texte(p, cx, r.bottom() - 10, tr('anim_occultation_observateurs'), 'doux', fond=True)

    def _courbes(self, p, r):
        el = self.ellipse()
        ys = self.ys()
        v, tm, t = self.v(), self.t_max(), self.instant()
        re = self.r_etoile()
        n = len(ys)
        ax = Axes(r, -tm, tm, -0.2, n + 0.1, marges=(40, 8, 8, 30)).avec(p)
        ax.fond(p, tr('anim_occultation_axe_t'), tr('anim_occultation_axe_flux'), grille=False,
                fmt_x=lambda x: nombre(x, 0 if tm >= 20 else (1 if tm >= 2 else 2)), fmt_y=lambda y: '')
        m = 200
        for i, y in enumerate(ys):                          # du bas (premier observateur) vers le haut
            base = i + 0.1
            pts = []
            for j in range(m + 1):
                tt = -tm + 2.0 * tm * j / m
                pts.append((tt, base + 0.75 * (1.0 - oc.fraction_cachee(el, -v * tt, y, re))))
            ax.courbe(pts, 'accent1' if el.corde(y) else 'doux', 1.4)
        ax.verticale(t, 'accent3', 1.2)

    def _forme(self, p, r):
        el = self.ellipse()
        ys = self.ys()
        cs, br = self.mesures()
        k = self._echelle(r, ys, el)
        cx, cy = r.center().x(), r.center().y() + 8

        def pt(x, y):
            return QPointF(cx + k * x, cy - k * (y - el.y0))
        sig = self.sigma.value() * self.v()
        if self.c_vraie.isChecked():
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.setPen(dessin.stylo('doux', 1.2, 0.8, pointille=True))
            p.drawPolygon(dessin.polygone(*zip(*[(pt(x, y).x(), pt(x, y).y()) for x, y in el.contour()])))
        for y, x1, x2 in br:
            if x1 is None:
                p.setPen(dessin.stylo('grille', 1.0, 0.8, pointille=True))
                p.drawLine(QPointF(r.x() + 10, pt(0, y).y()), QPointF(r.right() - 10, pt(0, y).y()))
                continue
            p.setPen(dessin.stylo('accent1', 2.2))
            p.drawLine(pt(x1, y), pt(x2, y))
            if sig * k > 1.0:
                p.setPen(dessin.stylo('accent3', 1.4))
                for x in (x1, x2):
                    p.drawLine(pt(x - sig, y), pt(x + sig, y))
        aj = self.ajustement(br) if self.c_ajuster.isChecked() else None
        if aj is not None:
            fit = oc.Ellipse(aj[2], aj[3], aj[4], aj[0], aj[1])
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.setPen(dessin.stylo('accent2', 1.8))
            p.drawPolygon(dessin.polygone(*zip(*[(pt(x, y).x(), pt(x, y).y()) for x, y in fit.contour()])))
        dessin.texte(p, cx, r.bottom() - 10, tr('anim_occultation_legende_forme'), 'doux', fond=True)
