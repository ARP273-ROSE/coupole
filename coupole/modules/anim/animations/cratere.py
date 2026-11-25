"""Cratère d'impact : un astéroïde ou une comète frappe la Terre ; la cavité transitoire se creuse puis s'effondre
en cratère simple (cuvette) ou complexe (fond plat, plus large que profond).  Lois d'échelle de Collins, Melosh et
Marcus (2005) : diamètre, profondeur, énergie en mégatonnes, fréquence de tels impacts.  Coupe à l'échelle et
diamètre final selon la taille de l'impacteur.  Calculs : ``cratere.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import cratere as cr, dessin
from ..base import Animation, angle, nombre
from ..graphe import Axes

DUREE = 6.0                      # secondes d'un cycle (chute, creusement, effondrement, repos)
EXPOSANTS = str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻')


def scientifique(x: float, dec: int = 2) -> str:
    """« 1,23 × 10¹⁵ » (décimal entre 0,01 et 10 000)."""
    if 0.01 <= x < 1e4:
        return nombre(x, dec)
    n = math.floor(math.log10(x))
    m = x / 10 ** n
    if round(m, dec) >= 10.0:
        n += 1
        m /= 10.0
    return '%s × 10%s' % (nombre(m, dec), str(n).translate(EXPOSANTS))


def longueur(m: float) -> str:
    if m < 1000.0:
        return '%s m' % nombre(m, 0)
    return '%s km' % nombre(m / 1000.0, 2 if m < 1e4 else 1)


def phases(t: float) -> tuple[float, float, float]:
    """(chute, creusement, effondrement) dans [0, 1] au temps t du cycle."""
    def rampe(a, b):
        return min(1.0, max(0.0, (t - a) / (b - a)))
    return rampe(0.0, 1.0), rampe(1.0, 2.2), rampe(2.6, 3.6)


class Cratere(Animation):
    ID = 'impactcrater'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.exemple = self.choix('exemple', [('anim_impactcrater_x_libre', 'libre')] +
                                  [('anim_impactcrater_x_' + k, k) for k, *_ in cr.EXEMPLES], 'cours')
        self.L = self.curseur('L', 10.0, 20000.0, 1500.0, dec=0, unite='m', log=True)
        self.v = self.curseur('v', 11.0, 72.0, 20.0, dec=1, unite='km·s⁻¹')
        self.theta = self.curseur('theta', 5.0, 90.0, 45.0, dec=0, unite='°')
        self.impacteur = self.choix('impacteur', [('anim_impactcrater_i_' + k, k) for k, _ in cr.IMPACTEURS],
                                    'rocheux')
        self.cible = self.choix('cible', [('anim_impactcrater_c_' + k, k) for k, *_ in cr.CIBLES], 'sedimentaire')
        self.t = 0.0
        self._applique = self.exemple.currentData()

    def reglage_change(self):
        k = self.exemple.currentData()
        if k != getattr(self, '_applique', k):
            self._applique = k
            for cle, L, v, th, imp, cib in cr.EXEMPLES:
                if cle == k:
                    self.L.setValue(L)
                    self.v.setValue(v)
                    self.theta.setValue(th)
                    self.impacteur.setCurrentIndex(self.impacteur.findData(imp))
                    self.cible.setCurrentIndex(self.cible.findData(cib))
            self.t = 0.0
        super().reglage_change()

    def avancer(self, dt):
        self.t = math.fmod(self.t + dt, DUREE)

    def parametres(self):
        rho_i = dict(cr.IMPACTEURS)[self.impacteur.currentData()]
        _, rho_t, k = [c for c in cr.CIBLES if c[0] == self.cible.currentData()][0]
        return self.L.value(), self.v.value() * 1000.0, self.theta.value(), rho_i, rho_t, k

    def resultat(self):
        return cr.cratere(*self.parametres())

    def valeurs(self):
        L, v, th, rho_i, rho_t, k = self.parametres()
        c = cr.cratere(L, v, th, rho_i, rho_t, k)
        e = cr.energie(L, rho_i, v)
        emt = e / cr.MT_J
        out = [(tr('anim_impactcrater_v_masse'), '%s kg' % scientifique(cr.masse(L, rho_i))),
               (tr('anim_impactcrater_v_energie'), tr('anim_impactcrater_energie', j=scientifique(e),
                                                      mt=scientifique(emt))),
               (tr('anim_impactcrater_v_transitoire'), '%s × %s' % (longueur(c['transitoire']),
                                                                   longueur(c['prof_transitoire']))),
               (tr('anim_impactcrater_v_final'), longueur(c['final'])),
               (tr('anim_impactcrater_v_profondeur'), longueur(c['profondeur'])),
               (tr('anim_impactcrater_v_genre'), tr('anim_impactcrater_g_' + c['genre'])),
               (tr('anim_impactcrater_v_rapport'), nombre(c['final'] / L, 1)),
               (tr('anim_impactcrater_v_frequence'), tr('anim_impactcrater_tous', n=scientifique(cr.recurrence_ans(emt))))]
        if L < 200.0:
            out.append((tr('anim_impactcrater_v_attention'), tr('anim_impactcrater_atmosphere')))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.6) if rect.width() > rect.height() * 1.1 else dessin.zones(rect, 2, 10)
        self._coupe(p, dessin.cadre(p, z[0], tr('anim_impactcrater_t_coupe')))
        self._graphe(p, dessin.cadre(p, z[1], tr('anim_impactcrater_t_graphe')))

    def _coupe(self, p, r):
        L, v, th, rho_i, rho_t, k = self.parametres()
        c = cr.cratere(L, v, th, rho_i, rho_t, k)
        chute, creuse, effondre = phases(self.t)
        demi = 0.75 * c['final']                       # demi-largeur montrée (m)
        k_ = (r.width() - 16) / (2.0 * demi)
        x0 = r.center().x()
        y_sol = r.top() + 0.42 * r.height()

        def pt(x, z):
            return QPointF(x0 + k_ * x, y_sol - k_ * z)
        demi = (r.width() - 4) / (2.0 * k_)             # tout le panneau
        n = 160
        # profil : transitoire (paraboloïde de diamètre D_tc et de profondeur d_tc) qui grandit, puis cratère final
        R_tc, d_tc = c['transitoire'] / 2.0, c['prof_transitoire']

        def z_transitoire(x, f):
            rr = R_tc * f
            if abs(x) >= rr or rr <= 0.0:
                return 0.0
            u = x / rr
            return -d_tc * f * (1.0 - u * u)
        prof = []
        for j in range(n + 1):
            x = -demi + 2.0 * demi * j / n
            zt = z_transitoire(x, creuse ** 0.5)
            zf = cr.profil(c, x)
            prof.append((x, (1.0 - effondre) * zt + effondre * zf if creuse >= 1.0 else zt))
        bas = r.bottom() - 4
        poly = [QPointF(pt(prof[0][0], 0).x(), bas)] + [pt(x, z) for x, z in prof] + [QPointF(pt(prof[-1][0], 0).x(), bas)]
        p.save()
        p.setClipRect(r)
        p.setPen(dessin.stylo('horizon', 1.6))
        p.setBrush(dessin.c('sol', 0.85))
        p.drawPolygon(dessin.polygone([q.x() for q in poly], [q.y() for q in poly]))
        if creuse >= 1.0 and effondre > 0.0:            # contour du transitoire, en pointillé
            p.setPen(dessin.stylo('accent3', 1.0, 0.8, pointille=True))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            pts = [pt(x, z_transitoire(x, 1.0)) for x in [-R_tc + 2 * R_tc * j / 80 for j in range(81)]]
            for a_, b_ in zip(pts[:-1], pts[1:]):
                p.drawLine(a_, b_)
        if chute < 1.0:                                 # l'impacteur arrive sous l'angle θ
            s = 1.0 - chute
            dist = 0.9 * demi * s
            ang = math.radians(th)
            xi, zi = -dist * math.cos(ang), dist * math.sin(ang) + L / 2.0
            dessin.disque(p, x0 + k_ * xi, y_sol - k_ * zi, max(2.5, k_ * L / 2.0), 'accent1', 'texte')
        p.restore()
        # cotes
        y = r.bottom() - 14
        if creuse >= 1.0 and effondre >= 1.0:
            xa, xb = pt(-c['final'] / 2.0, 0).x(), pt(c['final'] / 2.0, 0).x()
            p.setPen(dessin.stylo('accent3', 1.2))
            p.drawLine(QPointF(xa, y_sol - 16), QPointF(xb, y_sol - 16))
            dessin.texte(p, (xa + xb) / 2.0, y_sol - 26, tr('anim_impactcrater_cote', d=longueur(c['final'])),
                         'accent3', fond=True)
        dessin.texte(p, r.left() + 6, y, tr('anim_impactcrater_echelle'), 'doux', centre=False, fond=True)

    def _graphe(self, p, r):
        L, v, th, rho_i, rho_t, k = self.parametres()
        ax = Axes(r, 10.0, 20000.0, 0.1, 1000.0, xlog=True, ylog=True, marges=(44, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_impactcrater_axe_L'), tr('anim_impactcrater_axe_D'))
        pts = []
        for j in range(121):
            Lj = 10.0 * 2000.0 ** (j / 120)
            pts.append((Lj, cr.cratere(Lj, v, th, rho_i, rho_t, k)['final'] / 1000.0))
        ax.courbe(pts, 'accent2', 1.8)
        ax.horizontale(cr.D_C_KM, 'doux', 1.0, True, tr('anim_impactcrater_transition'))
        c = cr.cratere(L, v, th, rho_i, rho_t, k)
        dessin.disque(p, ax.px(L), ax.py(c['final'] / 1000.0), 5.0, 'accent3', 'texte')
