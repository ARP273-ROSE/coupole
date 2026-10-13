"""Azimuth/Altitude Demonstrator : le repère horizontal.  Une étoile à placer (curseurs ou souris) ; arcs de
l'azimut (le long de l'horizon depuis le nord, vers l'est) et de la hauteur (le long du vertical de l'étoile)."""
from __future__ import annotations

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..base import Animation, angle


class AzimutHauteur(Animation):
    ID = 'altazimuth'
    ANIMEE = False

    def construire(self):
        self.vue3d = self.vue(200.0, 28.0, 1.0, 89.0)
        self.az = self.curseur('azimut', 0.0, 360.0, 140.0, dec=1, unite='°', cle_texte='anim_c_azimut')
        self.alt = self.curseur('hauteur', -90.0, 90.0, 45.0, dec=1, unite='°', cle_texte='anim_c_hauteur')
        self.c_zenith = self.coche('zenith', False)
        self.c_nadir = self.coche('nadir', False)
        self.c_horizon = self.coche('horizon', False)
        self.c_meridien = self.coche('meridien', False)
        self._pe = None

    def valeurs(self):
        return [(tr('anim_c_azimut'), angle(self.az.value())), (tr('anim_c_hauteur'), angle(self.alt.value())),
                (tr('anim_altazimuth_distance_zenithale'), angle(90.0 - self.alt.value()))]

    def presser(self, pos, bouton):
        if self._pe is not None:
            v = self._pe.depuis_ecran(pos.x(), pos.y())
            etoile = np.array(astro.vecteur_horizon(self.az.value(), self.alt.value()))
            xs, ys, zs, _ = self._pe.ecran(etoile)
            if v is not None and zs[0] >= 0 and abs(pos.x() - xs[0]) < 14 and abs(pos.y() - ys[0]) < 14:
                self._glisse = self._deplacer
                return True
        return super().presser(pos, bouton)

    def _deplacer(self, pos):
        v = self._pe.depuis_ecran(pos.x(), pos.y()) if self._pe else None
        if v is not None:
            a, h = scenes.az_alt_de_vecteur(v)
            self.az.setValue(a)
            self.alt.setValue(h)

    def dessiner(self, p, rect):
        r = min(rect.width(), rect.height()) * 0.40
        cx, cy = rect.center().x(), rect.center().y() + 6
        self.zone_rotative(rect, self.vue3d)
        az, alt = self.az.value(), self.alt.value()
        etoile = np.array(astro.vecteur_horizon(az, alt))

        def scene(pe):
            pe.courbe(dessin.cercle((0, 1, 0)), 'grille', 1.0, 0.8)                     # méridien complet (pâle)
            if self.c_meridien.isChecked():
                pe.courbe(dessin.cercle((0, -1, 0), debut=0, fin=180, origine=(1, 0, 0)), 'meridien', 2.0)
            pe.courbe(dessin.cercle((0, 0, 1), 90.0 - alt), 'grille', 1.0)               # almucantarat
            v = np.array(astro.vecteur_horizon(az, 0.0))
            vert = np.array([np.cos(np.radians(t)) * v + np.sin(np.radians(t)) * np.array([0, 0, 1.0])
                             for t in np.linspace(-90, 90, 91)])
            pe.courbe(vert, 'grille', 1.0)                                               # vertical de l'étoile
            if abs(az) > 1e-6:
                pe.courbe(np.array([astro.vecteur_horizon(a, 0.0) for a in np.linspace(0, az, 90)]), 'arc1', 3.0)
            if abs(alt) > 1e-6:
                pe.courbe(np.array([astro.vecteur_horizon(az, h) for h in np.linspace(0, alt, 60)]), 'arc2', 3.0)
            pe.point(etoile, 'etoile', 6.0, bord='soleil')
            pe.segment((0, 0, 1), (0, 0, 1.18), 'doux', 2.0)
            pe.segment((0, 0, -1), (0, 0, -1.18), 'doux', 2.0)

        pe = scenes.sphere_locale(p, self.vue3d, cx, cy, r, scene)
        self._pe = pe
        pe.etiquette(np.array(astro.vecteur_horizon(az / 2, 0.0)) * 1.0 + np.array([0, 0, -0.07]),
                     angle(az), 'arc1')
        pe.etiquette(np.array(astro.vecteur_horizon(az + 12, alt / 2)), angle(alt), 'arc2')
        if self.c_zenith.isChecked():
            pe.etiquette((0, 0, 1.25), tr('anim_altazimuth_zenith'))
        if self.c_nadir.isChecked():
            pe.etiquette((0, 0, -1.25), tr('anim_altazimuth_nadir'))
        if self.c_horizon.isChecked():
            pe.etiquette(np.array(astro.vecteur_horizon((200 + 180 - self.vue3d.az) % 360, 0)) * 0.55,
                         tr('anim_altazimuth_plan_horizon'), 'horizon')
        if self.c_meridien.isChecked():
            pe.etiquette(np.array(astro.vecteur_horizon(180.0, 35.0)) * 1.04, tr('anim_altazimuth_meridien'),
                         'meridien')
