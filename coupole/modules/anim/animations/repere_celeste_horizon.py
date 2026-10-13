"""Celestial and Horizon Systems Comparison : la même sphère vue de deux façons.  En repère céleste, le pôle nord
céleste est en haut, l'équateur céleste horizontal, et l'horizon de l'observateur est incliné ; en repère local, le
zénith est en haut et l'horizon horizontal.  Le passage de l'un à l'autre est une rotation d'angle 90° − φ autour
de l'axe est-ouest ; le bouton « Basculer » l'anime."""
from __future__ import annotations

import math

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..base import Animation, angle


def rotation_est_ouest(angle_deg: float) -> np.ndarray:
    """Rotation autour de l'axe ouest (y du repère local) : amène le zénith (t = 0) vers le pôle (t = 90° − φ)."""
    a = math.radians(angle_deg)
    return np.array([[math.cos(a), 0.0, -math.sin(a)], [0.0, 1.0, 0.0], [math.sin(a), 0.0, math.cos(a)]])


class RepereCelesteHorizon(Animation):
    ID = 'celestialhorizon'
    SECONDES_BASCULE = 2.0

    def construire(self):
        self.vue3d = self.vue(200.0, 15.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.melange = self.curseur('bascule', 0.0, 1.0, 0.0, dec=2)
        self.bouton('anim_celestialhorizon_basculer', self.basculer)
        self._cible = None

    def basculer(self):
        self._cible = 0.0 if self.melange.value() > 0.5 else 1.0
        if not self.en_lecture:
            self.basculer_lecture()

    def avancer(self, dt):
        if self._cible is None:
            return
        v = self.melange.value()
        pas = dt / self.SECONDES_BASCULE
        if abs(self._cible - v) <= pas:
            self.melange.setValue(self._cible)
            self._cible = None
            self.basculer_lecture()
        else:
            self.melange.setValue(v + pas if self._cible > v else v - pas)

    def valeurs(self):
        lat = self.lat.value()
        return [(tr('anim_latsim_hauteur_pole'), angle(abs(lat))), (tr('anim_celestialhorizon_rotation'),
                                                                    angle(90 - lat))]

    def dessiner(self, p, rect):
        self.zone_rotative(rect, self.vue3d)
        r = min(rect.width(), rect.height()) * 0.40
        lat = self.lat.value()
        t = self.melange.value()
        # repère local tourné : t = 0 → horizon horizontal ; t = 1 → pôle céleste en haut
        rot = rotation_est_ouest(t * (90.0 - lat))
        conv_eq = scenes.eq_vers_local(0.0, lat)

        def loc(pts):
            return np.asarray(pts, dtype=float).reshape(-1, 3) @ rot.T

        pe = dessin.Peintre3D(p, self.vue3d, rect.center().x(), rect.center().y(), r)
        pe.contour('grille', 'ciel', 0.25)
        pe.courbe(loc(dessin.cercle((0, 0, 1))), 'horizon', 2.5)                       # horizon
        pe.courbe(loc(conv_eq(dessin.cercle((0, 0, 1)))), 'equateur', 2.0)             # équateur céleste
        pe.courbe(loc(dessin.cercle((0, -1, 0), debut=0, fin=360, origine=(1, 0, 0))), 'meridien', 1.2, 0.7)
        pe.segment(loc(conv_eq((0, 0, -1.25))), loc(conv_eq((0, 0, 1.25))), 'equateur', 1.6)
        pe.segment(loc((0, 0, 0)), loc((0, 0, 1.0)), 'horizon', 1.2, 0.7)
        pe.etiquette(loc((0, 0, 1.12)), tr('anim_altazimuth_zenith'), 'horizon')
        pe.etiquette(loc(conv_eq((0, 0, 1.33))), tr('anim_radecdemo_l_pnc'), 'equateur')
        for cle, az in (('anim_pc_n', 0.0), ('anim_pc_e', 90.0), ('anim_pc_s', 180.0), ('anim_pc_o', 270.0)):
            pe.etiquette(loc(np.array(astro.vecteur_horizon(az, 0.0)) * 1.1), tr(cle), 'horizon')
        dessin.texte(p, rect.x() + 12, rect.y() + 20, tr('anim_celestialhorizon_titre_local' if t < 0.5 else
                                                         'anim_celestialhorizon_titre_celeste'), centre=False)
