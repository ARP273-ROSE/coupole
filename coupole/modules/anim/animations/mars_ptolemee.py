"""Ptolemaic Orbit of Mars : le modèle de l'Almageste.  La Terre est au centre ; le centre du déférent est décalé
(excentrique) ; le centre de l'épicycle parcourt le déférent à vitesse angulaire constante vue du point équant
(symétrique de la Terre) en 1,881 an ; Mars parcourt l'épicycle en un an (son rayon reste parallèle à la direction
Terre-Soleil moyen).  Le Soleil tourne sur son propre cercle excentrique.  Paramètres de l'original."""
from __future__ import annotations

import collections
import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre

SEGMENTS = 175                       # longueur de la traînée (comme l'original)
PAS_TRACE = 0.02                     # années entre deux points de la traînée


class MarsPtolemee(Animation):
    ID = 'marsorbit'
    ANNEES_PAR_S = 0.3
    LECTURE_AU_DEPART = False

    def construire(self):
        self.t = 0.0
        self.trace = collections.deque(maxlen=SEGMENTS)
        self.c_soleil = self.coche('soleil', True)
        self.c_cercles = self.coche('cercles', True)
        self._remplir()

    def _remplir(self):
        self.trace.clear()
        n = SEGMENTS
        for i in range(n):
            self.trace.append(astro.ptolemee_mars(self.t - (n - 1 - i) * PAS_TRACE)['mars'])

    def etat_initial(self):
        self.t = 0.0
        self._remplir()

    def avancer(self, dt):
        t1 = self.t + dt * self.ANNEES_PAR_S
        k = int(t1 / PAS_TRACE) - int(self.t / PAS_TRACE)
        for i in range(1, k + 1):
            self.trace.append(astro.ptolemee_mars((int(self.t / PAS_TRACE) + i) * PAS_TRACE)['mars'])
        self.t = t1

    def valeurs(self):
        m = astro.ptolemee_mars(self.t)
        lam_m = m['longitude']
        sx, sy = astro.ptolemee_soleil(self.t)
        lam_s = (math.degrees(math.atan2(sy, sx)) + astro.PTOLEMEE_SOLEIL['apogee']) % 360.0
        dl = astro.mod180(astro.ptolemee_mars(self.t + 0.005)['longitude'] - astro.ptolemee_mars(self.t - 0.005)['longitude'])
        return [(tr('anim_marsorbit_temps'), '%s %s' % (nombre(self.t, 2), tr('anim_u_annees'))),
                (tr('anim_marsorbit_long_mars'), angle(lam_m)), (tr('anim_marsorbit_long_soleil'), angle(lam_s)),
                (tr('anim_marsorbit_elongation'), angle(abs(astro.mod180(lam_m - lam_s)))),
                (tr('anim_marsorbit_sens'), tr('anim_marsorbit_retro' if dl < 0 else 'anim_marsorbit_direct'))]

    def dessiner(self, p, rect):
        P = astro.PTOLEMEE_MARS
        cx, cy = rect.center().x(), rect.center().y()
        k = min(rect.width(), rect.height()) * 0.46 / (P['R'] + P['e'] + P['r'])
        rot = math.radians(P['apogee'])

        def ecr(x, y, apogee=rot):                   # repère tourné de l'apogée → écran (y vers le haut)
            xx = x * math.cos(apogee) - y * math.sin(apogee)
            yy = x * math.sin(apogee) + y * math.cos(apogee)
            return QPointF(cx + k * xx, cy - k * yy)

        m = astro.ptolemee_mars(self.t)
        if self.c_cercles.isChecked():
            c = ecr(*m['deferent'])
            p.setPen(dessin.stylo('grille', 1.2))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(c, P['R'] * k, P['R'] * k)
            e = ecr(*m['centre'])
            p.setPen(dessin.stylo('doux', 1.2))
            p.drawEllipse(e, P['r'] * k, P['r'] * k)
            p.drawLine(e, ecr(*m['mars']))
            q = ecr(*m['equant'])
            p.setPen(dessin.stylo('accent2', 1.0, 0.7, pointille=True))
            p.drawLine(q, e)
            dessin.disque(p, q.x(), q.y(), 3, 'accent2')
            dessin.texte(p, q.x() + 8, q.y() + 12, tr('anim_marsorbit_equant'), 'accent2', centre=False)
            dessin.disque(p, c.x(), c.y(), 2.5, 'grille')
        pts = list(self.trace)
        n = len(pts)
        for i in range(1, n):
            p.setPen(dessin.stylo('mars', 1.6, i / n))
            p.drawLine(ecr(*pts[i - 1]), ecr(*pts[i]))
        if self.c_soleil.isChecked():
            S = astro.PTOLEMEE_SOLEIL
            ks = k * 1.64 / 2.5 * (P['R'] / S['R'])     # échelle de l'original (le Soleil sur son propre cercle)
            sx, sy = astro.ptolemee_soleil(self.t)
            a = math.radians(S['apogee'])
            pc = QPointF(cx + ks * (S['e'] * math.cos(a)), cy - ks * (S['e'] * math.sin(a)))
            p.setPen(dessin.stylo('soleil', 1.0, 0.5))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(pc, S['R'] * ks, S['R'] * ks)
            xx = sx * math.cos(a) - sy * math.sin(a)
            yy = sx * math.sin(a) + sy * math.cos(a)
            dessin.disque(p, cx + ks * xx, cy - ks * yy, 8, 'soleil')
        mp = ecr(*m['mars'])
        dessin.disque(p, mp.x(), mp.y(), 6, 'mars')
        dessin.disque(p, cx, cy, 7, 'terre')
        dessin.texte(p, cx, cy + 16, tr('anim_shadowsim_terre'), 'doux')
        dessin.texte(p, mp.x() + 10, mp.y() - 10, tr('anim_marsorbit_mars'), 'mars', centre=False)
