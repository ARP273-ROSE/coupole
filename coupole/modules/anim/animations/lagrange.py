"""Les points de Lagrange : dans le repère qui tourne avec deux astres (Soleil et Terre, Terre et Lune, Soleil et
Jupiter, Pluton et Charon), cinq points d'équilibre.  L1 et L2 encadrent le petit astre à peu près au rayon de Hill
(SOHO, JWST) ; L4 et L5, en triangle équilatéral, retiennent les troyens si μ < 0,0385.  Un petit corps lâché près
d'eux trace un « têtard », un « fer à cheval » ou s'échappe ; les zones grisées lui sont interdites (constante de
Jacobi).  Calculs : ``lagrange.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import dessin, lagrange as lg
from ..base import Animation, nombre
from ..graphe import Axes

VITESSE = 4.0 * math.pi           # radians de temps (2 orbites) par seconde réelle, à la vitesse ×1
N_TRACE = 20000
PAS_TRACE = 0.05                  # radians de temps entre deux points de la trace
N_GRILLE = 90


def distance(x_a: float, a_km: float) -> str:
    """Distance en unités de a, et en km."""
    km = x_a * a_km
    s = nombre(km / 1e6, 2) + ' ' + tr('anim_lagrange_millions_km') if km >= 1e6 else nombre(km, 0) + ' km'
    return '%s a = %s' % (nombre(x_a, 4), s)


EXPOSANTS = str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻')


def scientifique(x: float) -> str:
    """x en écriture scientifique sous 0,01 (« 9,539 × 10⁻⁴ »), sinon en décimal."""
    if x >= 0.01:
        return nombre(x, 5)
    n = math.floor(math.log10(x))
    return '%s × 10%s' % (nombre(x / 10 ** n, 3), str(n).translate(EXPOSANTS))


class Lagrange(Animation):
    ID = 'lagrange'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.systeme = self.choix('systeme', [('anim_lagrange_s_' + k, k) for k, _, _ in lg.SYSTEMES],
                                  'soleil_jupiter')
        self.cas = self.choix('cas', [('anim_lagrange_c_' + k, k) for k, _ in lg.CAS], 'tetard')
        self.delta = self.curseur('delta', -0.03, 0.03, 0.005, dec=4)
        self.c_interdit = self.coche('interdit', True)
        self.c_hill = self.coche('hill', True)
        self.bouton('anim_lagrange_relancer', self.recommencer)
        self._cle = None
        self._cache = {}
        self._cas = self.cas.currentData()
        self.recommencer()

    def mu_a(self):
        return [(m, a) for k, m, a in lg.SYSTEMES if k == self.systeme.currentData()][0]

    def recommencer(self):
        mu, _ = self.mu_a()
        self.s = lg.depart(mu, self.cas.currentData(), self.delta.value())
        self.t = 0.0
        self.trace = [(self.s[0], self.s[1])]
        self.collision = False
        self._cle = (self.systeme.currentData(), self.cas.currentData(), self.delta.value())
        self.rafraichir()

    def reglage_change(self):
        c = self.cas.currentData()
        if c != getattr(self, '_cas', c):
            self._cas = c
            self.delta.setValue(dict(lg.CAS)[c])
        if self._cle is not None and self._cle != (self.systeme.currentData(), self.cas.currentData(),
                                                   self.delta.value()):
            self.recommencer()
        super().reglage_change()

    def avancer(self, dt):
        if self.collision:
            return
        mu, _ = self.mu_a()
        total = dt * VITESSE
        n = max(1, math.ceil(total / PAS_TRACE))               # un point de trace tous les PAS_TRACE au plus
        for _ in range(n):
            self.s, self.collision = lg.integrer(mu, self.s, total / n)
            self.t += total / n
            self.trace.append((self.s[0], self.s[1]))
            if self.collision:
                break
        if len(self.trace) > N_TRACE:
            del self.trace[:len(self.trace) - N_TRACE]

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        mu, a = self.mu_a()
        L = lg.points_lagrange(mu)
        sec = 1.0 - mu
        c = lg.jacobi(mu, *self.s)
        cl = {k: lg.jacobi(mu, x, y, 0.0, 0.0) for k, (x, y) in L.items()}
        out = [(tr('anim_lagrange_v_mu'), scientifique(mu)),
               (tr('anim_lagrange_v_l1'), distance(sec - L['L1'][0], a)),
               (tr('anim_lagrange_v_l2'), distance(L['L2'][0] - sec, a)),
               (tr('anim_lagrange_v_hill'), distance(lg.rayon_hill(mu), a)),
               (tr('anim_lagrange_v_l4'), tr('anim_lagrange_stables' if mu < lg.MU_ROUTH else 'anim_lagrange_instables')),
               (tr('anim_lagrange_v_c'), nombre(c, 6)),
               (tr('anim_lagrange_v_cl'), 'L1 %s · L2 %s · L3 %s · L4 %s' % tuple(nombre(cl[k], 6) for k in
                                                                               ('L1', 'L2', 'L3', 'L4'))),
               (tr('anim_lagrange_v_regions'), tr('anim_lagrange_' + lg.regions(mu, c))),
               (tr('anim_lagrange_v_temps'), tr('anim_lagrange_orbites', n=nombre(self.t / (2.0 * math.pi), 1)))]
        if self.collision:
            out.append((tr('anim_lagrange_v_etat'), tr('anim_lagrange_contact')))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.56)
        mu, _ = self.mu_a()
        self._carte(p, dessin.cadre(p, z[0], tr('anim_lagrange_t_carte')), mu, (0.0, 0.0), 1.55, True)
        rh = lg.rayon_hill(mu)
        self._carte(p, dessin.cadre(p, z[1], tr('anim_lagrange_t_zoom')), mu, (1.0 - mu, 0.0), 2.6 * rh, False)
        self._potentiel(p, dessin.cadre(p, z[2], tr('anim_lagrange_t_potentiel')), mu)

    def _carte(self, p, r, mu, centre, demi, grande):
        cote = min(r.width(), r.height() - 6)
        k = cote / (2.0 * demi)
        cx, cy = r.center().x(), r.center().y() + 4

        def pt(x, y):
            return QPointF(cx + k * (x - centre[0]), cy - k * (y - centre[1]))
        c = lg.jacobi(mu, *self.s)
        if self.c_interdit.isChecked():
            n = N_GRILLE
            cle = (mu, round(c, 12), centre, demi, round(cote, 1))
            cache = self._cache.get(grande)
            if cache is None or cache[0] != cle:
                cases = []
                for j in range(n):
                    for i in range(n):
                        x = centre[0] - demi + (i + 0.5) * 2.0 * demi / n
                        y = centre[1] + demi - (j + 0.5) * 2.0 * demi / n
                        if 2.0 * lg.omega(mu, x, y) < c:
                            cases.append((i, j))
                cache = (cle, cases)
                self._cache[grande] = cache
            h = cote / n
            x0, y0 = cx - cote / 2.0, cy - cote / 2.0
            p.save()
            p.setRenderHint(p.RenderHint.Antialiasing, False)
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c('grille', 0.45))
            for i, j in cache[1]:
                p.drawRect(QRectF(math.floor(x0 + i * h), math.floor(y0 + j * h),
                                  math.floor(x0 + (i + 1) * h) - math.floor(x0 + i * h),
                                  math.floor(y0 + (j + 1) * h) - math.floor(y0 + j * h)))
            p.restore()
        p.save()
        p.setClipRect(r)
        # les deux astres
        dessin.disque(p, pt(-mu, 0.0).x(), pt(-mu, 0.0).y(), 9.0 if grande else 4.0, 'soleil')
        dessin.disque(p, pt(1.0 - mu, 0.0).x(), pt(1.0 - mu, 0.0).y(), 5.0, 'terre')
        if self.c_hill.isChecked():
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.setPen(dessin.stylo('accent2', 1.0, 0.8, pointille=True))
            p.drawEllipse(pt(1.0 - mu, 0.0), lg.rayon_hill(mu) * k, lg.rayon_hill(mu) * k)
        # trace et corps
        tr_ = [pt(x, y) for x, y in self.trace]
        if len(tr_) >= 2:
            p.setPen(dessin.stylo('accent1', 1.2, 0.85))
            for q0, q1 in zip(tr_[:-1], tr_[1:]):
                if abs(q0.x() - q1.x()) + abs(q0.y() - q1.y()) < 4 * cote:
                    p.drawLine(q0, q1)
        q = pt(self.s[0], self.s[1])
        dessin.disque(p, q.x(), q.y(), 4.0, 'accent3', 'texte')
        # points de Lagrange
        for nom, (x, y) in lg.points_lagrange(mu).items():
            ql = pt(x, y)
            if r.contains(ql):
                p.setPen(dessin.stylo('accent2', 1.8))
                p.drawLine(QPointF(ql.x() - 5, ql.y() - 5), QPointF(ql.x() + 5, ql.y() + 5))
                p.drawLine(QPointF(ql.x() - 5, ql.y() + 5), QPointF(ql.x() + 5, ql.y() - 5))
                dessin.etiquette(p, ql.x(), ql.y(), nom, 'accent2')
        p.restore()

    def _potentiel(self, p, r, mu):
        L = lg.points_lagrange(mu)
        ymin, ymax = -4.0, -1.3
        ax = Axes(r, -1.6, 1.6, ymin, ymax, marges=(44, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_lagrange_axe_x'), tr('anim_lagrange_axe_phi'))
        m = 600
        pts = []
        for j in range(m + 1):
            x = -1.6 + 3.2 * j / m
            v = -lg.omega(mu, x, 0.0)
            pts.append((x, max(ymin - 1.0, v)))
        ax.courbe(pts, 'accent2', 1.8)
        c = lg.jacobi(mu, *self.s)
        ax.horizontale(-c / 2.0, 'accent3', 1.2)
        for nom in ('L1', 'L2', 'L3'):
            x = L[nom][0]
            v = -lg.omega(mu, x, 0.0)
            if ymin <= v <= ymax:
                dessin.disque(p, ax.px(x), ax.py(v), 3.5, 'accent2')
                dessin.etiquette(p, ax.px(x), ax.py(v), nom, 'accent2')
        dessin.texte(p, ax.r.left() + 6, ax.r.bottom() - 10, tr('anim_lagrange_legende_pot'), 'doux', centre=False,
                     fond=True)
