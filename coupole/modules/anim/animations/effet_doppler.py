"""Doppler Shift Demonstrator : une source émet des ondes (crêtes = cercles qui s'élargissent à la vitesse c de
l'onde) en se déplaçant ; l'observateur (qu'on fait glisser) reçoit les crêtes plus serrées quand la source
s'approche, plus espacées quand elle s'éloigne.  Le signal reçu est calculé exactement par le temps retardé τ :
|observateur − source(τ)| = c (t − τ) ; la fréquence reçue vaut alors f₀ dτ/dt = f₀ / (1 − v_r / c), v_r étant la
vitesse de la source vers l'observateur au moment de l'émission (ondes dans un milieu au repos, comme le son)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre

L, H = 100.0, 60.0                 # boîte (unités arbitraires)
C_ONDE = 15.0                      # vitesse de l'onde (unités par seconde)
F0 = 1.5                           # fréquence émise (Hz)
A = 36.0                           # demi-course de la source
FENETRE_S = 6.0                    # durée montrée par les graphes


class EffetDoppler(Animation):
    ID = 'dopplershift'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.v = self.curseur('vitesse', 0.0, 0.9, 0.5, dec=2)
        self.dir = self.curseur('direction', 0.0, 180.0, 0.0, dec=0, unite='°')
        self.c_emission = self.coche('emission', True)
        self.c_trace = self.coche('trajectoire', False)
        self.obs = [80.0, 12.0]
        self._zone = None
        self.etat_initial()

    def etat_initial(self):
        self.t = 0.0
        self.historique = []                   # (t, signal émis, signal reçu)
        self.emissions = [(0.0, None)] if self.c_emission.isChecked() else []     # intervalles d'émission

    def reglage_change(self):
        # la trajectoire de la source change : on repart d'un temps propre (les crêtes déjà émises restent cohérentes
        # avec l'ancienne trajectoire seulement si rien ne change)
        on = self.c_emission.isChecked()
        if self.emissions and self.emissions[-1][1] is None and not on:
            self.emissions[-1] = (self.emissions[-1][0], self.t)
        elif on and (not self.emissions or self.emissions[-1][1] is not None):
            self.emissions.append((self.t, None))
        cle = (self.v.value(), self.dir.value())
        if getattr(self, '_cle', cle) != cle:
            self.t = 0.0
            self.historique = []
            self.emissions = [(0.0, None)] if on else []
        self._cle = cle
        super().reglage_change()

    # ------------------------------------------------------------ cinématique
    def position(self, t: float):
        """Source : va-et-vient à vitesse constante v c le long de la direction choisie, autour du centre."""
        v = self.v.value() * C_ONDE
        d = math.radians(self.dir.value())
        if v <= 0:
            s = 0.0
        else:
            u = (v * t / (4 * A)) % 1.0                         # onde triangulaire d'amplitude A
            s = A * (4 * u if u < 0.25 else (2 - 4 * u if u < 0.75 else 4 * u - 4))
        return L / 2 + s * math.cos(d), H / 2 + s * math.sin(d)

    def vitesse_source(self, t: float):
        h = 1e-4
        (x0, y0), (x1, y1) = self.position(t - h), self.position(t + h)
        return (x1 - x0) / (2 * h), (y1 - y0) / (2 * h)

    def emet(self, t: float) -> bool:
        return any(a <= t and (b is None or t < b) for a, b in self.emissions)

    def retard(self, t: float) -> float:
        return lumiere.temps_retarde(t, self.position, self.obs, C_ONDE, t_min=-1e6)

    def recu(self, t: float):
        tau = self.retard(t)
        return (math.sin(2 * math.pi * F0 * tau) if self.emet(tau) and tau >= 0 else None), tau

    def avancer(self, dt):
        t0, self.t = self.t, self.t + dt
        n = max(1, int(math.ceil(dt * 150)))           # 150 échantillons par seconde : ≥ 10 par période reçue
        for i in range(1, n + 1):
            t = t0 + dt * i / n
            s, _ = self.recu(t)
            self.historique.append((t, math.sin(2 * math.pi * F0 * t) if self.emet(t) else None, s))
        while self.historique and self.historique[0][0] < self.t - FENETRE_S:
            self.historique.pop(0)

    def frequence_recue(self):
        """(fréquence mesurée par dτ/dt, fréquence prédite f₀ / (1 − v_r / c))."""
        t = self.t
        h = 1e-3
        mesuree = F0 * (self.retard(t + h) - self.retard(t - h)) / (2 * h)
        tau = self.retard(t)
        x, y = self.position(tau)
        dx, dy = self.obs[0] - x, self.obs[1] - y
        n = math.hypot(dx, dy) or 1.0
        vx, vy = self.vitesse_source(tau)
        vr = (vx * dx + vy * dy) / n
        return mesuree, F0 / (1 - vr / C_ONDE), vr

    def valeurs(self):
        mes, pred, vr = self.frequence_recue()
        return [(tr('anim_dopplershift_f0'), '%s Hz' % nombre(F0, 2)),
                (tr('anim_dopplershift_vr'), '%s c' % nombre(vr / C_ONDE, 3)),
                (tr('anim_dopplershift_f_recue'), '%s Hz' % nombre(mes, 3)),
                (tr('anim_dopplershift_f_formule'), '%s Hz' % nombre(pred, 3))]

    # ------------------------------------------------------------ souris
    def presser(self, pos, bouton):
        if self._zone is not None and self._zone[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        r, k = self._zone
        self.obs = [max(1.0, min(L - 1, (pos.x() - r.left()) / k)), max(1.0, min(H - 1, (pos.y() - r.top()) / k))]
        self.historique = []

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.6)
        r = dessin.cadre(p, z[0])
        k = min(r.width() / L, r.height() / H)
        boite = QRectF(r.center().x() - L * k / 2, r.center().y() - H * k / 2, L * k, H * k)
        self._zone = (boite, k)
        p.save()
        p.setClipRect(boite)
        p.fillRect(boite, dessin.c('sphere', 0.35))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        t = self.t
        kmax = int(math.floor(t * F0))
        portee = math.hypot(L, H) / C_ONDE + 1
        p.setPen(dessin.stylo('accent2', 1.2, 0.85))
        for n in range(kmax, max(-1, kmax - int(portee * F0) - 1), -1):
            te = n / F0
            if not self.emet(te):
                continue
            x, y = self.position(te)
            rr = C_ONDE * (t - te) * k
            p.drawEllipse(QPointF(boite.left() + x * k, boite.top() + y * k), rr, rr)
        if self.c_trace.isChecked() and self.v.value() > 0:
            d = math.radians(self.dir.value())
            p.setPen(dessin.stylo('grille', 1.0, None, True))
            p.drawLine(QPointF(boite.left() + (L / 2 - A * math.cos(d)) * k, boite.top() + (H / 2 - A * math.sin(d)) * k),
                       QPointF(boite.left() + (L / 2 + A * math.cos(d)) * k, boite.top() + (H / 2 + A * math.sin(d)) * k))
        p.restore()
        x, y = self.position(t)
        dessin.disque(p, boite.left() + x * k, boite.top() + y * k, 7, 'accent1', bord='texte')
        ox, oy = boite.left() + self.obs[0] * k, boite.top() + self.obs[1] * k
        dessin.disque(p, ox, oy, 7, 'accent3', bord='texte')
        dessin.texte(p, ox, oy - 15, tr('anim_c_observateur'), 'accent3', fond=True)
        self._signal(p, dessin.cadre(p, z[1], tr('anim_dopplershift_titre_emis')), 1)
        self._signal(p, dessin.cadre(p, z[2], tr('anim_dopplershift_titre_recu')), 2)

    def _signal(self, p, r, i):
        p.setPen(dessin.stylo('grille', 1.0))
        p.drawLine(QPointF(r.left(), r.center().y()), QPointF(r.right(), r.center().y()))
        if not self.historique:
            return
        t1 = self.t
        morceau = []
        p.setPen(dessin.stylo('accent1' if i == 1 else 'accent3', 1.5))
        pas = max(1, int(len(self.historique) / max(50.0, r.width())))     # au plus un point par pixel
        for e in self.historique[::pas]:
            v = e[i]
            if v is None:
                if len(morceau) > 1:
                    p.drawPolyline(QPolygonF(morceau))
                morceau = []
                continue
            morceau.append(QPointF(r.right() - r.width() * (t1 - e[0]) / FENETRE_S, r.center().y() - v * r.height() * 0.4))
        if len(morceau) > 1:
            p.drawPolyline(QPolygonF(morceau))
