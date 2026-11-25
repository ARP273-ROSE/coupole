"""Résonances et chaos : un astéroïde et son « jumeau » (lâché 78 km plus loin) tournent autour du Soleil sous l'effet de
Jupiter.  En résonance (Hilda 3:2, troyen 1:1), l'orbite dessine une figure fermée dans le repère qui tourne avec
Jupiter ; près des lacunes de Kirkwood (3:1, 2:1) l'excentricité varie ; une orbite qui frôle Jupiter (comète) est
chaotique : l'écart entre les jumeaux explose exponentiellement.  Calculs : ``resonances.py`` (et ``lagrange.py``)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import dessin, lagrange as lg, resonances as rs
from ..base import Animation, nombre
from ..graphe import Axes

VITESSE = 2.0 * math.pi           # une orbite de Jupiter par seconde, à la vitesse ×1
PAS_TRACE = 0.1
N_TRACE = 8000
FENETRE = 60.0                    # orbites de Jupiter montrées dans les graphes
EXPOSANTS = str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻')


def scientifique(x: float) -> str:
    if x < 1e4:
        return nombre(x, 0 if x >= 100 else 1)
    n = math.floor(math.log10(x))
    m = x / 10 ** n
    if round(m, 2) >= 10.0:
        n += 1
        m /= 10.0
    return '%s × 10%s' % (nombre(m, 2), str(n).translate(EXPOSANTS))


class Resonances(Animation):
    ID = 'resonances'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.cas = self.choix('cas', [('anim_resonances_c_' + k, k) for k, *_ in rs.CAS], 'hilda')
        self.a = self.curseur('a', 1.8, 6.0, 3.97, dec=3, unite='ua')
        self.e = self.curseur('e', 0.0, 0.9, 0.15, dec=2)
        self.phi = self.curseur('phi', 0.0, 360.0, 0.0, dec=0, unite='°')
        self.masse = self.choix('masse', [('anim_resonances_m_reelle', 'reelle'), ('anim_resonances_m_x10', 'x10')],
                                'reelle')
        self.repere = self.choix('repere', [('anim_resonances_r_tournant', 'tournant'),
                                            ('anim_resonances_r_fixe', 'fixe')], 'tournant')
        self.c_jumeau = self.coche('jumeau', True)
        self.bouton('anim_resonances_relancer', self.recommencer)
        self._cas = self.cas.currentData()
        self._cle_depart = None
        self.recommencer()

    def mu(self) -> float:
        return rs.MU_JUPITER * (10.0 if self.masse.currentData() == 'x10' else 1.0)

    def cle(self):
        return (self.a.value(), self.e.value(), self.phi.value(), self.masse.currentData())

    def recommencer(self):
        mu = self.mu()
        self.s1 = rs.etat_initial(self.a.value(), self.e.value(), self.phi.value(), mu)
        self.s2 = rs.jumeau(self.s1)
        self.t = 0.0
        self.trace1 = [(0.0, self.s1[0], self.s1[1])]
        self.trace2 = [(0.0, self.s2[0], self.s2[1])]
        a, e = rs.elements(self.s1, mu)
        self.histoire = [(0.0, a, e, rs.ecart(self.s1, self.s2))]
        self.collision = False
        self._cle_depart = self.cle()
        self.rafraichir()

    def reglage_change(self):
        c = self.cas.currentData()
        if c != getattr(self, '_cas', c):
            self._cas = c
            for k, a, e, phi in rs.CAS:
                if k == c:
                    self.a.setValue(a)
                    self.e.setValue(e)
                    self.phi.setValue(phi)
        if self._cle_depart is not None and self._cle_depart != self.cle():
            self.recommencer()
        super().reglage_change()

    def avancer(self, dt):
        if self.collision:
            return
        mu = self.mu()
        total = dt * VITESSE
        n = max(1, math.ceil(total / PAS_TRACE))
        for _ in range(n):
            self.s1, self.s2, self.collision = rs.avancer(mu, self.s1, self.s2, total / n)
            self.t += total / n
            self.trace1.append((self.t, self.s1[0], self.s1[1]))
            self.trace2.append((self.t, self.s2[0], self.s2[1]))
            a, e = rs.elements(self.s1, mu)
            self.histoire.append((self.t, a, e, rs.ecart(self.s1, self.s2)))
            if self.collision:
                break
        for tr_ in (self.trace1, self.trace2):
            if len(tr_) > N_TRACE:
                del tr_[:len(tr_) - N_TRACE]
        t_min = self.t - FENETRE * 2.0 * math.pi
        if self.histoire[0][0] < t_min - 10.0:
            self.histoire = [h for h in self.histoire if h[0] >= t_min]

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        mu = self.mu()
        a, e = rs.elements(self.s1, mu)
        orbites = self.t / (2.0 * math.pi)
        out = [(tr('anim_resonances_v_temps'), tr('anim_resonances_temps', n=nombre(orbites, 1),
                                                  ans=nombre(orbites * rs.ANNEE_JUPITER, 0)))]
        if math.isfinite(a):
            (p, q), d = rs.resonance_proche(a)
            out += [(tr('anim_resonances_v_a'), '%s ua' % nombre(a, 3)),
                    (tr('anim_resonances_v_e'), nombre(e, 3)),
                    (tr('anim_resonances_v_rapport'), nombre(rs.rapport_periodes(a), 3)),
                    (tr('anim_resonances_v_proche'), tr('anim_resonances_proche', p=p, q=q,
                                                        a=nombre(rs.A_JUPITER_UA * (q / p) ** (2.0 / 3.0), 2),
                                                        d=nombre(100.0 * d, 1)))]
        else:
            out.append((tr('anim_resonances_v_a'), tr('anim_resonances_ejecte')))
        d = rs.ecart(self.s1, self.s2)
        out.append((tr('anim_resonances_v_ecart'), tr('anim_resonances_ecart', km=scientifique(d * rs.A_JUPITER_UA *
                                                                                              149_597_870.7),
                                                      f=scientifique(d / rs.DELTA0))))
        if self.collision:
            out.append((tr('anim_resonances_v_etat'), tr('anim_resonances_collision')))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.56)
        titre = 'anim_resonances_t_tournant' if self.repere.currentData() == 'tournant' else 'anim_resonances_t_fixe'
        self._vue(p, dessin.cadre(p, z[0], tr(titre)))
        self._demi_axe(p, dessin.cadre(p, z[1], tr('anim_resonances_t_a')))
        self._ecart(p, dessin.cadre(p, z[2], tr('anim_resonances_t_ecart')))

    def _vue(self, p, r):
        mu = self.mu()
        fixe = self.repere.currentData() == 'fixe'
        demi = min(3.0, max(1.3, self.a.value() / rs.A_JUPITER_UA * (1.0 + self.e.value()) * 1.1))
        cote = min(r.width(), r.height() - 6)
        k = cote / (2.0 * demi)
        cx, cy = r.center().x(), r.center().y() + 4

        def pt(t, x, y):
            if fixe:
                x, y = rs.inertiel(x, y, t)
            return QPointF(cx + k * x, cy - k * y)
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('grille', 1.0, 0.8, pointille=True))
        p.drawEllipse(QPointF(cx, cy), k, k)
        for trace, cle, ep in ((self.trace2, 'accent2', 1.0), (self.trace1, 'accent1', 1.3)):
            if trace is self.trace2 and not self.c_jumeau.isChecked():
                continue
            pts = [pt(*q) for q in trace]
            p.setPen(dessin.stylo(cle, ep, 0.85))
            for q0, q1 in zip(pts[:-1], pts[1:]):
                if abs(q0.x() - q1.x()) + abs(q0.y() - q1.y()) < cote:
                    p.drawLine(q0, q1)
        sol = pt(self.t, -mu, 0.0)
        jup = pt(self.t, 1.0 - mu, 0.0)
        dessin.disque(p, sol.x(), sol.y(), 7.0, 'soleil')
        dessin.disque(p, jup.x(), jup.y(), 5.0, 'ecliptique')
        dessin.etiquette(p, jup.x(), jup.y(), tr('anim_resonances_jupiter'), 'doux')
        if not fixe:
            for nom in ('L4', 'L5'):
                x, y = lg.points_lagrange(mu)[nom]
                q = pt(self.t, x, y)
                p.setPen(dessin.stylo('doux', 1.2))
                p.drawLine(QPointF(q.x() - 4, q.y() - 4), QPointF(q.x() + 4, q.y() + 4))
                p.drawLine(QPointF(q.x() - 4, q.y() + 4), QPointF(q.x() + 4, q.y() - 4))
        if self.c_jumeau.isChecked():
            q2 = pt(self.t, self.s2[0], self.s2[1])
            dessin.disque(p, q2.x(), q2.y(), 3.5, 'accent2')
        q1 = pt(self.t, self.s1[0], self.s1[1])
        dessin.disque(p, q1.x(), q1.y(), 4.0, 'accent3', 'texte')
        p.restore()

    def _demi_axe(self, p, r):
        t1 = max(self.t, FENETRE * 2.0 * math.pi)
        t0 = t1 - FENETRE * 2.0 * math.pi
        a0 = self.a.value()
        ax = Axes(r, t0 / (2.0 * math.pi), t1 / (2.0 * math.pi), a0 - 0.25, a0 + 0.25,
                  marges=(44, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_resonances_axe_t'), tr('anim_resonances_axe_a'))
        for pp, qq in rs.RESONANCES:
            ar = rs.A_JUPITER_UA * (qq / pp) ** (2.0 / 3.0)
            if a0 - 0.25 < ar < a0 + 0.25:
                ax.horizontale(ar, 'accent3', 1.0, True, '%d:%d' % (pp, qq))
        pts = [(h[0] / (2.0 * math.pi), min(a0 + 1.0, max(a0 - 1.0, h[1]))) for h in self.histoire
               if math.isfinite(h[1])]
        if len(pts) >= 2:
            ax.courbe(pts, 'accent1', 1.4)

    def _ecart(self, p, r):
        t1 = max(self.t, FENETRE * 2.0 * math.pi)
        t0 = t1 - FENETRE * 2.0 * math.pi
        ax = Axes(r, t0 / (2.0 * math.pi), t1 / (2.0 * math.pi), 1e-7, 100.0, ylog=True,
                  marges=(44, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_resonances_axe_t'), tr('anim_resonances_axe_ecart'))
        pts = [(h[0] / (2.0 * math.pi), min(100.0, max(1e-7, h[3] * rs.A_JUPITER_UA))) for h in self.histoire]
        if len(pts) >= 2:
            ax.courbe(pts, 'accent2', 1.4)
