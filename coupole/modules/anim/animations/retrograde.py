"""Retrograde Motion : la Terre (1 ua) rattrape Mars (1,524 ua) sur leurs orbites autour du Soleil ; la ligne de
visée Terre → Mars se projette sur les étoiles lointaines.  Autour de l'opposition, Mars semble reculer vers
l'ouest (mouvement rétrograde), entre deux stations.  Orbites circulaires (périodes : 3e loi de Kepler) ;
l'inclinaison réelle de l'orbite de Mars (1,85°) fait apparaître une boucle."""
from __future__ import annotations

import collections
import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre

A_MARS = 1.524
INCLINAISON = 1.85                      # degrés (orbite de Mars sur l'écliptique)
NOEUD = 49.6                            # longitude du nœud ascendant (degrés)
T0 = -0.25                              # début : un trimestre avant l'opposition (t = 0)


def positions(t: float, inclinee: bool) -> dict:
    """Terre et Mars (héliocentriques) et coordonnées géocentriques de Mars (λ, β) au temps t (années)."""
    xt, yt = astro.position_circulaire(1.0, 1.0, t)
    pm = astro.periode_annees(A_MARS)
    u = 2 * math.pi * t / pm                       # opposition à t = 0, dans la direction x
    xm, ym, zm = A_MARS * math.cos(u), A_MARS * math.sin(u), 0.0
    if inclinee:
        i, om = math.radians(INCLINAISON), math.radians(NOEUD)
        arg = u - om
        xm = A_MARS * (math.cos(om) * math.cos(arg) - math.sin(om) * math.sin(arg) * math.cos(i))
        ym = A_MARS * (math.sin(om) * math.cos(arg) + math.cos(om) * math.sin(arg) * math.cos(i))
        zm = A_MARS * math.sin(arg) * math.sin(i)
    dx, dy, dz = xm - xt, ym - yt, zm
    lam = math.degrees(math.atan2(dy, dx)) % 360.0
    beta = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return {'terre': (xt, yt), 'mars': (xm, ym), 'lambda': lam, 'beta': beta}


class Retrograde(Animation):
    ID = 'retrograde'
    ANNEES_PAR_S = 0.12

    def construire(self):
        self.c_incl = self.coche('inclinaison', True)
        self.c_lignes = self.coche('lignes', True)
        self.t = T0
        self.trace = collections.deque(maxlen=400)
        self.lignes = collections.deque(maxlen=12)

    def etat_initial(self):
        self.t = T0
        self.trace.clear()
        self.lignes.clear()

    def reglage_change(self):
        self.trace.clear()
        super().reglage_change()

    def avancer(self, dt):
        t1 = self.t + dt * self.ANNEES_PAR_S
        if t1 > -T0 + 0.05:                       # fin de la séquence : on recommence (comme l'original)
            self.etat_initial()
            return
        n = max(1, int((t1 - self.t) / 0.002))
        for i in range(1, n + 1):
            tt = self.t + (t1 - self.t) * i / n
            pz = positions(tt, self.c_incl.isChecked())
            self.trace.append((pz['lambda'], pz['beta']))
        if int(t1 / 0.04) != int(self.t / 0.04):
            self.lignes.append(positions(t1, False))
        self.t = t1

    def _vitesse(self) -> float:
        a = positions(self.t - 0.001, self.c_incl.isChecked())['lambda']
        b = positions(self.t + 0.001, self.c_incl.isChecked())['lambda']
        return astro.mod180(b - a) / (0.002 * astro.ANNEE_JULIENNE_J)        # degrés par jour

    def _message(self) -> str:
        """Commentaire de l'original, selon la phase du mouvement (stations de la théorie circulaire)."""
        ts = astro.retrogradation(A_MARS)['demi_duree_annees']
        if self.t < -ts:
            return 'anim_retrograde_msg_est'
        if self.t < ts:
            return 'anim_retrograde_msg_ouest'
        if self.t < ts + 0.15:
            return 'anim_retrograde_msg_reprend'
        return 'anim_retrograde_msg_est'

    def valeurs(self):
        pz = positions(self.t, self.c_incl.isChecked())
        r = astro.retrogradation(A_MARS)
        v = self._vitesse()
        return [(tr('anim_retrograde_jours'), nombre(self.t * astro.ANNEE_JULIENNE_J, 0)),
                (tr('anim_retrograde_lambda'), angle(pz['lambda'])), (tr('anim_retrograde_beta'), angle(pz['beta'], 2)),
                (tr('anim_retrograde_vitesse'), '%s%s' % (nombre(v, 3), tr('anim_retrograde_u_vitesse'))),
                (tr('anim_retrograde_sens'), tr('anim_marsorbit_retro' if v < 0 else 'anim_marsorbit_direct')),
                (tr('anim_retrograde_theorie'), tr('anim_retrograde_theorie_val', j=nombre(r['duree_j'], 0),
                                                   a=angle(r['amplitude'], 1)))]

    def dessiner(self, p, rect):
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.62)
        bas = QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height())
        cx, cy = haut.center().x(), haut.bottom() - 10
        k = min(haut.width() * 0.45, haut.height() * 0.6) / A_MARS / 1.15
        p.save()
        p.setClipRect(haut)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), k, k)
        p.drawEllipse(QPointF(cx, cy), k * A_MARS, k * A_MARS)
        dessin.disque(p, cx, cy, 8, 'soleil')
        pz = positions(self.t, False)
        # repère tourné : l'opposition (t = 0) vers le haut de l'écran
        def ecr(x, y):
            return QPointF(cx - k * y, cy - k * x)
        if self.c_lignes.isChecked():
            for i, l in enumerate(self.lignes):
                a, b = ecr(*l['terre']), ecr(*l['mars'])
                d = math.hypot(b.x() - a.x(), b.y() - a.y()) or 1
                fin = QPointF(a.x() + (b.x() - a.x()) / d * 2000, a.y() + (b.y() - a.y()) / d * 2000)
                p.setPen(dessin.stylo('mars', 1.0, 0.15 + 0.5 * (i + 1) / len(self.lignes)))
                p.drawLine(a, fin)
        a, b = ecr(*pz['terre']), ecr(*pz['mars'])
        d = math.hypot(b.x() - a.x(), b.y() - a.y()) or 1
        p.setPen(dessin.stylo('mars', 2.0))
        p.drawLine(a, QPointF(a.x() + (b.x() - a.x()) / d * 2000, a.y() + (b.y() - a.y()) / d * 2000))
        dessin.disque(p, a.x(), a.y(), 6, 'terre')
        dessin.disque(p, b.x(), b.y(), 5, 'mars')
        p.restore()
        # bande des étoiles lointaines : λ (l'est à gauche, comme dans le ciel) et β (exagéré)
        r = dessin.cadre(p, bas, tr('anim_retrograde_ciel'))
        lam0 = 0.0
        largeur_deg = 50.0
        rng = np.random.default_rng(3)
        etoiles = rng.uniform(0, 1, (40, 2))
        for x, y in etoiles:
            dessin.disque(p, r.x() + x * r.width(), r.y() + y * r.height(), 1.2, 'etoile', alpha=0.6)

        def ec(lam, beta):
            dl = astro.mod180(lam - lam0)
            return QPointF(r.center().x() - dl / largeur_deg * r.width(), r.center().y() - beta / 6.0 * r.height() * 0.45)
        pts = list(self.trace)
        for i in range(1, len(pts)):
            p.setPen(dessin.stylo('mars', 2.0, 0.3 + 0.7 * i / len(pts)))
            p.drawLine(ec(*pts[i - 1]), ec(*pts[i]))
        pzi = positions(self.t, self.c_incl.isChecked())
        q = ec(pzi['lambda'], pzi['beta'])
        dessin.disque(p, q.x(), q.y(), 5, 'mars')
        dessin.texte(p, r.x() + 8, r.bottom() - 8, tr('anim_pc_e'), 'doux', centre=False)
        dessin.texte(p, r.right() - 16, r.bottom() - 8, tr('anim_pc_o'), 'doux', centre=False)
        dessin.texte(p, haut.x() + 12, haut.y() + 20, tr(self._message()), 'texte', centre=False, fond=True)
