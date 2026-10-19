"""Sidereal Time and Hour Angle Demonstrator : sphère locale à la latitude φ ; le ciel tourne avec le temps
sidéral local (TSL).  L'angle horaire d'une étoile vaut H = TSL − α (compté vers l'ouest depuis le méridien)."""
from __future__ import annotations

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..maintenant import tsl_heures
from ..base import Animation, angle, heures_minutes, nombre


def angle_horaire_h(tsl_h: float, ra_h: float) -> float:
    """H = TSL − α, ramené entre −12 h et +12 h (comme le simulateur d'origine)."""
    h = (tsl_h - ra_h + 24.0) % 24.0
    return h - 24.0 if h > 12.0 else h


class AngleHoraire(Animation):
    ID = 'siderealTimeAndHourAngleDemo'
    VITESSE_H_PAR_S = 1.0          # heures sidérales par seconde à la vitesse ×1

    TEMPS = ('tsl',)

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        # temps sidéral local à la longitude retenue (« Ma position », sinon méridien du fuseau)
        self.poser(self.tsl, tsl_heures(m.i.jj, m.lon))
        if m.lat is not None:
            self.poser(self.lat, m.lat)

    def construire(self):
        self.vue3d = self.vue(160.0, 35.0, 7.0, 89.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.tsl = self.curseur('tsl', 0.0, 24.0, 2.0, dec=2, unite='h', cle_texte='anim_c_tsl')
        self.ra = self.curseur('ra', 0.0, 24.0, 4.0, dec=2, unite='h', cle_texte='anim_c_ra')
        self.dec = self.curseur('dec', -90.0, 90.0, 30.0, dec=1, unite='°', cle_texte='anim_c_dec')
        self.c_arc = self.coche('arc', True)          # 0.8.0 : arc de H affiché par défaut (choix mémorisé gardé)

    def avancer(self, dt):
        self.tsl.setValue((self.tsl.value() + dt * self.VITESSE_H_PAR_S) % 24.0)

    def valeurs(self):
        h = angle_horaire_h(self.tsl.value(), self.ra.value())
        az, alt = astro.equatorial_vers_horizon(15 * h, self.dec.value(), self.lat.value())
        return [(tr('anim_c_tsl'), heures_minutes(self.tsl.value())),
                (tr('anim_c_ra'), heures_minutes(self.ra.value())),
                (tr('anim_siderealtimeandhourangledemo_h'), '%s h (%s)' % (nombre(h, 2), angle(15 * h))),
                (tr('anim_c_azimut'), angle(az)), (tr('anim_c_hauteur'), angle(alt))]

    def dessiner(self, p, rect):
        r = min(rect.width(), rect.height()) * 0.40
        cx, cy = rect.center().x(), rect.center().y() + 6
        self.zone_rotative(rect, self.vue3d)
        lat, tsl = self.lat.value(), 15 * self.tsl.value()
        ra, dec = 15 * self.ra.value(), self.dec.value()
        h = angle_horaire_h(self.tsl.value(), self.ra.value())
        m = np.array(astro.matrice_equatorial_vers_horizon(tsl, lat))

        def eq(pts):
            return np.asarray(pts, dtype=float).reshape(-1, 3) @ m.T

        def scene(pe):
            pe.courbe(eq(scenes.cercle_horaire(90.0)), 'grille', 1.0, 0.6)
            pe.courbe(eq(scenes.cercle_horaire(270.0)), 'grille', 1.0, 0.6)
            pe.courbe(eq(dessin.cercle((0, 0, 1))), 'equateur', 1.5)
            pe.courbe(eq(scenes.cercle_horaire(0.0)), 'equateur', 1.5)
            # méridien de l'observateur (du sud au nord en passant par le zénith)
            pe.courbe(dessin.cercle((0, -1, 0), debut=0, fin=180, origine=(1, 0, 0)), 'meridien', 2.0,
                      repere_monde=True)
            pe.courbe(eq(scenes.cercle_horaire(ra)), 'grille', 1.2)
            pe.courbe(eq(scenes.cercle_declinaison(dec)), 'grille', 1.2)
            if ra > 1e-6:
                pe.courbe(eq(scenes.arc_equateur(0.0, ra)), 'arc1', 3.0)
            if abs(dec) > 1e-6:
                pe.courbe(eq(scenes.cercle_horaire(ra, 0.0, dec, 60)), 'arc2', 3.0)
            if self.c_arc.isChecked() and abs(h) > 1e-6:
                # le long du parallèle de l'étoile, du méridien (α = TSL) jusqu'à l'étoile
                pe.courbe(eq(scenes.arc_equateur(tsl, tsl - 15 * h, dec, 90)), 'accent1', 3.0)
            pe.point(eq(astro.vecteur_equatorial(ra, dec)), 'etoile', 6.0, bord='soleil')
            pe.segment(eq((0, 0, 1)), eq((0, 0, 1.2)), 'equateur', 2.0)
            pe.segment(eq((0, 0, -1)), eq((0, 0, -1.2)), 'equateur', 2.0)

        pe = scenes.sphere_locale(p, self.vue3d, cx, cy, r, scene)
        pe.etiquette(eq(astro.vecteur_equatorial(ra / 2, -6)), '%s h' % nombre(self.ra.value(), 1), 'arc1')
        pe.etiquette(eq(astro.vecteur_equatorial(ra + 12, dec / 2)), angle(dec), 'arc2')
        if self.c_arc.isChecked():
            pe.etiquette(eq(np.array(astro.vecteur_equatorial(tsl - 7.5 * h, dec + 6))),
                         '%s h' % nombre(h, 1), 'accent1')
        pe.etiquette(eq((0, 0, 1.28)), tr('anim_radecdemo_l_pnc'), 'equateur')
