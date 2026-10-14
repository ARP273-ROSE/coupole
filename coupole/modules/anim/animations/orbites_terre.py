"""Earth Orbit Plot : période d'un satellite de la Terre selon le rayon de son orbite (circulaire).  P = 2π √(r³ / GM),
v = √(GM / r), GM = 3,986 004 418 × 10¹⁴ m³ s⁻² (l'original prenait 3,983 781 × 10¹⁴).  Points remarquables :
le « boulet de Newton » au ras du sol, la Station spatiale, les satellites GPS, l'orbite géostationnaire (un jour
sidéral) et la Lune (pour elle, la masse de la Lune s'ajoute : G (M⊕ + M☾) donne sa vraie période)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, duree_hm, nombre

R_MIN, R_MAX = 6_378_137.0, 450_000_000.0
JOUR_SIDERAL_S = astro.jour_sideral_s(astro.ANNEE_SIDERALE_J)
# rayons d'orbite (m) : Newton (surface), Station spatiale (≈ 420 km d'altitude), GPS (demi-grand axe 26 560 km),
# géostationnaire (période = un jour sidéral), Lune (distance moyenne)
POINTS = (('newton', R_MIN), ('iss', 6_798_000.0), ('gps', 26_560_000.0),
          ('geo', astro.rayon_orbite_terre(JOUR_SIDERAL_S)), ('lune', astro.D_LUNE_KM * 1000.0))


def texte_periode(s: float) -> str:
    if s < 3 * 3600:
        return '%s min' % nombre(s / 60, 1)
    if s < 86_400 * 2:
        return duree_hm(s / 3600)
    return '%s %s' % (nombre(s / 86_400, 2), tr('anim_u_jours'))


class OrbitesTerre(Animation):
    ID = 'earthorbitplot'
    ANIMEE = False

    def construire(self):
        self.r = self.curseur('r', R_MIN / 1000, R_MAX / 1000, 42_164.0, dec=0, unite='km', log=True)
        self.choix_point = self.choix('point', [('anim_gravcalc_libre', '')] +
                                      [('anim_earthorbitplot_p_' + k, k) for k, _ in POINTS], 'geo')
        self.choix_point.activated.connect(self._point)
        self.c_log = self.coche('log', False)
        self._graphe = None

    def _point(self, *_):
        for k, r in POINTS:
            if k == self.choix_point.currentData():
                self.r.setValue(r / 1000.0)

    def rayon_m(self) -> float:
        exact = dict(POINTS).get(self.choix_point.currentData())
        if exact is not None and abs(exact / 1000.0 - self.r.value()) < 1.0:
            return exact
        return self.r.value() * 1000.0

    def valeurs(self):
        r = self.rayon_m()
        out = [(tr('anim_earthorbitplot_rayon'), '%s km' % nombre(r / 1000, 0)),
               (tr('anim_earthorbitplot_altitude'), '%s km' % nombre((r - R_MIN) / 1000, 0)),
               (tr('anim_earthorbitplot_periode'), texte_periode(astro.periode_orbite_terre(r))),
               (tr('anim_earthorbitplot_vitesse'), '%s km·s⁻¹' % nombre(astro.vitesse_circulaire(r) / 1000, 3))]
        if self.choix_point.currentData() == 'lune':
            gm = astro.GM_TERRE * (1 + astro.MASSE_LUNE_KG / astro.MASSE_TERRE_KG)
            out.append((tr('anim_earthorbitplot_lune_vraie'), texte_periode(astro.periode_orbite_terre(r, gm))))
        return out

    def presser(self, pos, bouton):
        if self._graphe is not None and self._graphe[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return super().presser(pos, bouton)

    def _tirer(self, pos):
        _, x0, x1 = self._graphe
        f = max(0.0, min(1.0, (pos.x() - x0) / (x1 - x0)))
        self.r.setValue(10 ** (math.log10(R_MIN) + f * (math.log10(R_MAX) - math.log10(R_MIN))) / 1000.0)
        self.choix_point.setCurrentIndex(0)

    def dessiner(self, p, rect):
        x0, x1 = rect.x() + 60, rect.right() - 16
        y0, y1 = rect.y() + 16, rect.bottom() - 40
        self._graphe = (QRectF(rect), x0, x1)
        lr0, lr1 = math.log10(R_MIN), math.log10(R_MAX)
        pmin, pmax = astro.periode_orbite_terre(R_MIN), astro.periode_orbite_terre(R_MAX)
        log_y = self.c_log.isChecked()
        if log_y:
            ly0, ly1 = math.log10(pmin) - 0.1, math.log10(pmax) + 0.1
        else:
            ly0, ly1 = 0.0, pmax * 1.05

        def xy(r, per):
            x = x0 + (x1 - x0) * (math.log10(r) - lr0) / (lr1 - lr0)
            v = math.log10(per) if log_y else per
            return QPointF(x, y1 - (y1 - y0) * (v - ly0) / (ly1 - ly0))

        p.setPen(dessin.stylo('grille', 1.0, 0.6))
        dessin.police(p, 0.75)
        for r in (6_378e3, 1e7, 2e7, 4e7, 1e8, 2e8, 4e8):
            q = xy(r, pmin)
            p.drawLine(QPointF(q.x(), y0), QPointF(q.x(), y1))
            dessin.texte(p, q.x(), y1 + 12, nombre(r / 1000, 0), 'doux')
        jours = (1 / 24, 1 / 4, 1, 7, 28) if log_y else (7, 14, 21, 28, 35)
        for j in jours:
            q = xy(R_MIN, j * 86_400)
            if y0 <= q.y() <= y1:
                p.drawLine(QPointF(x0, q.y()), QPointF(x1, q.y()))
                dessin.texte(p, x0 - 28, q.y(), nombre(j, 2 if j < 1 else 0), 'doux')
        dessin.texte(p, (x0 + x1) / 2, y1 + 28, tr('anim_earthorbitplot_axe_r'), 'doux')
        dessin.texte(p, x0 + 4, y0 - 4, tr('anim_earthorbitplot_axe_p'), 'doux', centre=False)
        dessin.police(p, 1 / 0.75)
        pts = []
        for i in range(201):
            r = 10 ** (lr0 + (lr1 - lr0) * i / 200)
            pts.append(xy(r, astro.periode_orbite_terre(r)))
        p.setPen(dessin.stylo('accent2', 2.0))
        p.drawPolyline(QPolygonF(pts))
        r = self.rayon_m()
        q = xy(r, astro.periode_orbite_terre(r))
        p.setPen(dessin.stylo('accent1', 1.0, 0.8, pointille=True))
        p.drawLine(QPointF(q.x(), y1), q)
        p.drawLine(QPointF(x0, q.y()), q)
        dessin.disque(p, q.x(), q.y(), 6, 'accent1', bord='texte')
        dessin.police(p, 0.8)
        # étiquettes en dernier : le placeur commun les écarte du point réglé et les unes des autres
        for i, (k, r) in enumerate(POINTS):
            q = xy(r, astro.periode_orbite_terre(r))
            dessin.disque(p, q.x(), q.y(), 4, 'accent3')
            dy = -10 - 14 * (i % 2) if i < 2 else -10
            dessin.texte(p, q.x() + 6, q.y() + dy, tr('anim_earthorbitplot_p_' + k), 'doux', centre=False, fond=True)
        dessin.police(p, 1 / 0.8)
