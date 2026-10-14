"""Stellar Velocity Calculator : la vitesse d'une étoile dans l'espace d'après sa vitesse radiale (effet Doppler sur
la raie Hα) et sa vitesse transverse (mouvement propre et distance).  v_r = c Δλ / λ₀ (λ₀ = 656,28 nm, Hα dans
l'air ; l'original prenait 656,3 nm et c = 300 000 km/s) ; v_t = 4,740 47 μ d (μ en ″/an, d en parsecs) ;
v = √(v_r² + v_t²).  Réglages de l'original : λ de 655 à 657 nm, μ de 0 à 10 ″/an, d de 1 à 10 pc."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, hr
from ..base import Animation, angle, nombre

H_ALPHA_NM = 656.28


class VitesseEtoile(Animation):
    ID = 'stellarvel'
    ANIMEE = False

    def construire(self):
        self.lam = self.curseur('lambda', 655.0, 657.0, 656.5, dec=3, unite='nm')
        self.mu = self.curseur('mu', 0.0, 10.0, 10.0, dec=2, unite='″/an')
        self.d = self.curseur('distance', 1.0, 10.0, 10.0, dec=2, unite='pc')
        self._zone = None

    def vitesses(self) -> dict:
        vr = hr.vitesse_radiale(self.lam.value(), H_ALPHA_NM)
        vt = hr.vitesse_transverse(self.mu.value(), self.d.value())
        return {'vr': vr, 'vt': vt, 'v': math.hypot(vr, vt), 'angle': math.degrees(math.atan2(vt, vr)),
                'vr_rel': hr.vitesse_radiale(self.lam.value(), H_ALPHA_NM, relativiste=True)}

    def valeurs(self):
        v = self.vitesses()
        return [(tr('anim_stellarvel_vr'), '%s km/s (%s)' % (nombre(v['vr'], 2), tr(
                    'anim_stellarvel_eloigne' if v['vr'] > 0 else 'anim_stellarvel_approche'))),
                (tr('anim_stellarvel_vt'), '%s km/s' % nombre(v['vt'], 2)),
                (tr('anim_stellarvel_v'), '%s km/s' % nombre(v['v'], 2)),
                (tr('anim_stellarvel_angle'), angle(v['angle'], 1)),
                (tr('anim_stellarvel_relativiste'), '%s km/s' % nombre(v['vr_rel'], 2))]

    def presser(self, pos, bouton):
        if self._zone is not None:
            x0, k, cy = self._zone
            if abs(pos.x() - (x0 + k * self.d.value())) < 18 and abs(pos.y() - cy) < 18:
                self._glisse = lambda q: self.d.setValue((q.x() - self._zone[0]) / self._zone[1])
                return True
        return False

    def dessiner(self, p, rect):
        v = self.vitesses()
        x0 = rect.x() + 40
        cy = rect.y() + rect.height() * 0.55
        k = (rect.width() - 150) / 10.0
        self._zone = (x0, k, cy)
        # observateur (Terre), ligne de visée, étoile à sa distance
        dessin.disque(p, x0, cy, 8, 'terre', bord='texte')
        p.setPen(dessin.stylo('grille', 1.0, pointille=True))
        p.drawLine(QPointF(x0, cy), QPointF(rect.right() - 20, cy))
        xs = x0 + k * self.d.value()
        echelle = min(rect.width(), rect.height()) * 0.30 / max(80.0, hr.vitesse_transverse(10, 10), abs(
            hr.vitesse_radiale(657.0, H_ALPHA_NM)))
        lr, lt = v['vr'] * echelle, v['vt'] * echelle
        if abs(lr) > 2:
            dessin.fleche(p, xs, cy, xs + lr, cy, dessin.stylo('accent3' if v['vr'] > 0 else 'accent2', 2.4), 9)
        if lt > 2:
            dessin.fleche(p, xs, cy, xs, cy - lt, dessin.stylo('horizon', 2.4), 9)
        if abs(lr) > 2 or lt > 2:
            dessin.fleche(p, xs, cy, xs + lr, cy - lt, dessin.stylo('accent1', 2.4), 9)
        dessin.disque(p, xs, cy, 9, 'soleil', bord='texte')
        dessin.police(p, 0.85)
        dessin.texte(p, xs + lr / 2, cy + 16, 'v_r', 'accent3' if v['vr'] > 0 else 'accent2')
        dessin.texte(p, xs - 18, cy - lt / 2, 'v_t', 'horizon')
        dessin.texte(p, xs + lr / 2 + 16, cy - lt / 2 - 10, 'v', 'accent1')
        for d in range(0, 11, 2):
            dessin.texte(p, x0 + k * d, cy + 34, '%d pc' % d, 'doux')
        dessin.police(p, 1 / 0.85)
        # spectre : la raie Hα au repos et observée
        self._spectre(p, QRectF(rect.x() + 20, rect.y() + 12, rect.width() - 40, rect.height() * 0.18))

    def _spectre(self, p, r):
        def x_de(lam):
            return r.x() + r.width() * (lam - 654.5) / 3.0

        p.fillRect(r, dessin.c('arc2', 0.6))                     # le rouge du spectre autour de Hα
        p.setPen(dessin.stylo('nuit', 3.0))
        xo = x_de(self.lam.value())
        p.drawLine(QPointF(xo, r.y()), QPointF(xo, r.bottom()))
        p.setPen(dessin.stylo('texte', 1.0, pointille=True))
        xr = x_de(H_ALPHA_NM)
        p.drawLine(QPointF(xr, r.y() - 4), QPointF(xr, r.bottom() + 4))
        dessin.police(p, 0.8)
        dessin.texte(p, xr, r.bottom() + 12, 'Hα %s nm' % nombre(H_ALPHA_NM, 2), 'doux')
        dessin.texte(p, xo, r.y() - 8, '%s nm' % nombre(self.lam.value(), 3), 'texte')
        dessin.police(p, 1 / 0.8)
