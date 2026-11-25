"""Le diagramme demi-grand axe – excentricité : chaque point (a, e) est une orbite autour du Soleil.  Familles de
géocroiseurs (Atira, Aten, Apollo, Amor) sur les courbes q = a(1 − e) et Q = a(1 + e) constants, ceinture
principale et lacunes de Kirkwood, troyens, centaures, transneptuniens ; une trentaine de petits corps réels (base
SBDB du JPL) ; l'orbite choisie dessinée vue de dessus parmi celles des planètes, paramètre de Tisserand.
Calculs : ``diagramme_ae.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, diagramme_ae as ae
from ..base import Animation, angle, nombre
from ..graphe import Axes

A_MIN, A_MAX = 0.3, 100.0
SECONDES_PAR_ORBITE = 6.0


def ua(x: float) -> str:
    return '%s ua' % nombre(x, 3 if x < 10 else (1 if x < 1000 else 0))


class DiagrammeAE(Animation):
    ID = 'aediagram'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.objet = self.choix('objet', [('anim_aediagram_o_libre', 'libre')] +
                                [('anim_aediagram_o_' + k, k) for k, *_ in ae.OBJETS], 'ceres')
        self.a = self.curseur('a', A_MIN, A_MAX, 2.77, dec=3, unite='ua', log=True)
        self.e = self.curseur('e', 0.0, 0.99, 0.0797, dec=3)
        self.i = self.curseur('i', 0.0, 180.0, 10.6, dec=1, unite='°')
        self.c_familles = self.coche('familles', True)
        self.c_kirkwood = self.coche('kirkwood', True)
        self.c_objets = self.coche('objets', True)
        self.m = 0.0
        self._applique = self.objet.currentData()
        self._graphe = None

    def reglage_change(self):
        k = self.objet.currentData()
        if k != getattr(self, '_applique', k):
            self._applique = k
            for cle, a, e, i in ae.OBJETS:
                if cle == k:
                    self.a.setValue(a)
                    self.e.setValue(e)
                    self.i.setValue(i)
        super().reglage_change()

    def avancer(self, dt):
        self.m = math.fmod(self.m + 2.0 * math.pi * dt / SECONDES_PAR_ORBITE, 2.0 * math.pi)

    # ------------------------------------------------------------ souris : choisir un point du diagramme
    def presser(self, pos, bouton):
        if self._graphe is not None and self._graphe.r.contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        ax = self._graphe
        a = ax.x_de_px(max(ax.r.left(), min(ax.r.right(), pos.x())))
        e = ax.y_de_px(max(ax.r.top(), min(ax.r.bottom(), pos.y())))
        self.objet.setCurrentIndex(self.objet.findData('libre'))
        self.a.setValue(min(A_MAX, max(A_MIN, a)))
        self.e.setValue(min(0.99, max(0.0, e)))

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        a, e = self.a.value(), self.e.value()
        t = ae.tisserand(a, e, self.i.value())
        cr = ae.croisees(a, e)
        p = ae.periode(a)
        return [(tr('anim_aediagram_v_q'), ua(ae.perihelie(a, e))),
                (tr('anim_aediagram_v_Q'), ua(ae.aphelie(a, e))),
                (tr('anim_aediagram_v_p'), tr('anim_aediagram_ans', n=nombre(p, 2 if p < 10 else (1 if p < 1000 else 0)))),
                (tr('anim_aediagram_v_famille'), tr('anim_aediagram_f_' + ae.famille(a, e))),
                (tr('anim_aediagram_v_croise'), ', '.join(tr('anim_aediagram_p_' + k) for k in cr) if cr
                 else tr('anim_aediagram_aucune')),
                (tr('anim_aediagram_v_tisserand'), '%s : %s' % (nombre(t, 2), tr('anim_aediagram_t_' + ae.genre_tisserand(t)))),
                (tr('anim_aediagram_v_distance'), ua(ae.distance_soleil(a, e, self.m)))]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.6) if rect.width() > rect.height() * 1.1 else dessin.zones(rect, 2, 10)
        self._diagramme(p, dessin.cadre(p, z[0], tr('anim_aediagram_t_diagramme')))
        self._orbite(p, dessin.cadre(p, z[1], tr('anim_aediagram_t_orbite')))

    def _diagramme(self, p, r):
        ax = Axes(r, A_MIN, A_MAX, 0.0, 1.0, xlog=True, marges=(40, 8, 10, 30)).avec(p)
        self._graphe = ax
        ax.fond(p, tr('anim_aediagram_axe_a'), tr('anim_aediagram_axe_e'))
        n = 240
        if self.c_kirkwood.isChecked():
            for pq in ae.LACUNES:
                ax.verticale(ae.resonance(*pq), 'accent3', 1.0, True)
            for pq in ae.GROUPES:
                ax.verticale(ae.resonance(*pq), 'accent2', 1.0, True)
            for pq, rang, cle in (((3, 1), 0, 'accent3'), ((2, 1), 0, 'accent3'), ((3, 2), 1, 'accent2'),
                                  ((1, 1), 1, 'accent2')):
                dessin.texte(p, ax.px(ae.resonance(*pq)), ax.r.top() + 9 + 14 * rang, '%d:%d' % pq, cle)
        if self.c_familles.isChecked():
            for q, cle in ((ae.Q_APOLLO, 'accent1'), (ae.Q_GEOCROISEUR, 'accent1'), (ae.Q_MARS, 'doux')):
                pts = []
                for j in range(n + 1):
                    a = q * (A_MAX / q) ** (j / n)
                    pts.append((a, 1.0 - q / a))
                ax.courbe(pts, cle, 1.2)
            pts = []
            for j in range(n + 1):
                a = ae.Q_ATIRA / 2.0 + (1.0 - ae.Q_ATIRA / 2.0) * j / n
                pts.append((a, ae.Q_ATIRA / a - 1.0))
            ax.courbe(pts, 'accent1', 1.2, pointille=True)
            ax.verticale(1.0, 'accent1', 1.0, True)
            for cle, a, e in (('atira', 0.5, 0.06), ('aten', 0.72, 0.62), ('apollo', 2.2, 0.82), ('amor', 3.3, 0.66),
                              ('ceinture', 2.75, 0.025), ('troyen', 5.3, 0.17), ('centaure', 14.0, 0.17),
                              ('transneptunien', 55.0, 0.12)):
                dessin.texte(p, ax.px(a), ax.py(e), tr('anim_aediagram_l_' + cle), 'doux', fond=True)
        if self.c_objets.isChecked():
            for k, a, e, _ in ae.OBJETS:
                dessin.disque(p, ax.px(a), ax.py(e), 2.6, 'accent2')
        for k, a, e in ae.PLANETES:
            dessin.disque(p, ax.px(a), ax.py(e), 3.6, 'terre' if k == 'terre' else 'doux')
            dessin.texte(p, ax.px(a), ax.py(e) - 10, tr('anim_aediagram_p_' + k)[:2], 'doux')
        a, e = self.a.value(), self.e.value()
        q = QPointF(ax.px(a), ax.py(e))
        dessin.disque(p, q.x(), q.y(), 5.5, 'accent3', 'texte')
        k = self.objet.currentData()
        if k != 'libre':
            dessin.etiquette(p, q.x(), q.y(), tr('anim_aediagram_o_' + k), 'accent3')

    def _orbite(self, p, r):
        a, e = self.a.value(), self.e.value()
        Q = ae.aphelie(a, e)
        demi = max(1.7, Q * 1.08)
        cote = min(r.width(), r.height() - 6)
        k = cote / (2.0 * demi)
        cx = r.center().x() + 0.25 * k * a * e if Q < demi else r.center().x()
        cy = r.center().y() + 3

        def pt(x, y):
            return QPointF(cx + k * x, cy - k * y)
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for kp, ap, _ in ae.PLANETES:
            if ap * k >= 2.0:
                p.setPen(dessin.stylo('terre' if kp == 'terre' else 'grille', 1.4 if kp == 'terre' else 1.0, 0.9))
                p.drawEllipse(pt(0.0, 0.0), ap * k, ap * k)
                if ap < demi:
                    dessin.texte(p, cx, cy - ap * k - 7, tr('anim_aediagram_p_' + kp), 'doux')
        dessin.disque(p, cx, cy, 6.0, 'soleil')
        b = a * math.sqrt(1.0 - e * e)
        p.setPen(dessin.stylo('accent3', 1.8))
        p.drawEllipse(pt(-a * e, 0.0), a * k, b * k)
        x, y = ae.position(a, e, self.m)
        q = pt(x, y)
        dessin.disque(p, q.x(), q.y(), 4.5, 'accent3', 'texte')
        qp = pt(ae.perihelie(a, e), 0.0)
        dessin.etiquette(p, qp.x(), qp.y(), 'q', 'accent3')
        p.restore()
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_aediagram_echelle', d=ua(demi)), 'doux', centre=False,
                     fond=True)
