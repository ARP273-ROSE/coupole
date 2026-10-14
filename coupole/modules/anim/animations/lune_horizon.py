"""Moon Phases and the Horizon Diagram : relier la phase de la Lune, l'heure et la position de la Lune dans le
ciel.  Comme dans l'original, le Soleil et la Lune sont sur l'équateur céleste (temps sidéral 0) et occupent l'une
des huit positions repérées (de 3 h en 3 h) : la position du Soleil donne l'heure (6 h à la position 1, puis
+3 h par position), l'écart entre les deux donne la phase (élongation = 15° × (α☾ − α☉))."""
from __future__ import annotations

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..base import Animation, angle, heures_minutes

POSITIONS = 8


def ascension_droite(position: float) -> float:
    """Position 1 à 8 → ascension droite en heures (6 h, 3 h, 0 h, −3 h…) comme l'original."""
    return 6.0 - 3.0 * (position - 1.0)


def heure_du_soleil(position_soleil: float) -> float:
    return (6.0 + 3.0 * (position_soleil - 1.0)) % 24.0


def elongation(position_soleil: float, position_lune: float) -> float:
    return (15.0 * (ascension_droite(position_lune) - ascension_droite(position_soleil))) % 360.0


class LuneHorizon(Animation):
    ID = 'positionsdemonstrator'
    ANIMEE = False

    def construire(self):
        self.vue3d = self.vue(200.0, 25.0, 7.0, 89.0)
        self.ps = self.curseur('soleil', 1.0, POSITIONS, 4.0, dec=0)
        self.pm = self.curseur('lune', 1.0, POSITIONS, 2.0, dec=0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.c_reperes = self.coche('reperes', True)
        self.c_bande = self.coche('bande', False)
        self.c_heure = self.coche('heure', True)
        self.c_phase = self.coche('phase', True)

    def _ciel(self):
        lat = self.lat.value()
        hs = -15.0 * ascension_droite(self.ps.value())
        hm = -15.0 * ascension_droite(self.pm.value())
        az_s, alt_s = astro.equatorial_vers_horizon(hs, 0.0, lat)
        az_m, alt_m = astro.equatorial_vers_horizon(hm, 0.0, lat)
        return az_s, alt_s, az_m, alt_m

    def valeurs(self):
        e = elongation(self.ps.value(), self.pm.value())
        az_s, alt_s, az_m, alt_m = self._ciel()
        out = []
        if self.c_heure.isChecked():
            out.append((tr('anim_c_heure'), heures_minutes(heure_du_soleil(self.ps.value()))))
        if self.c_phase.isChecked():
            out.append((tr('anim_lunar_applet_nom_phase'), tr('anim_phase_' + astro.nom_de_phase(e))))
        out += [(tr('anim_c_elongation'), angle(e if e <= 180 else 360 - e, 0)),
                (tr('anim_lunar_applet_h_soleil'), angle(alt_s)), (tr('anim_lunar_applet_h_lune'), angle(alt_m))]
        return out

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.7) if rect.width() > rect.height() * 1.1 else dessin.zones(rect, 2, 10)
        r = dessin.cadre(p, z[0], tr('anim_positionsdemonstrator_ciel'))
        self.zone_rotative(r, self.vue3d)
        rr = min(r.width(), r.height()) * 0.42
        cx, cy = r.center().x(), r.center().y() + 6
        lat = self.lat.value()
        m = np.array(astro.matrice_equatorial_vers_horizon(0.0, lat))
        az_s, alt_s, az_m, alt_m = self._ciel()
        soleil = np.array(astro.vecteur_horizon(az_s, alt_s))
        lune = np.array(astro.vecteur_horizon(az_m, alt_m))
        e = elongation(self.ps.value(), self.pm.value())

        def scene(pe):
            if self.c_bande.isChecked():
                for d in (-30.0, 30.0):
                    pe.courbe(scenes.cercle_declinaison(d) @ m.T, 'ecliptique', 1.0, 0.6)
            pe.courbe(dessin.cercle((0, 0, 1)) @ m.T, 'equateur', 1.6, 0.9)
            if self.c_reperes.isChecked():
                for k in range(1, POSITIONS + 1):
                    v = m @ np.array(astro.vecteur_equatorial(15.0 * ascension_droite(k), 0.0))
                    pe.point(v * 1.0, 'doux', 3.0, repere_monde=True)
                    pe.etiquette(m @ np.array(astro.vecteur_equatorial(15.0 * ascension_droite(k), 12.0)), str(k),
                                 'doux', repere_monde=True, toujours=False)
            pe.point(soleil, 'soleil', 9.0, repere_monde=True)
            pe.point(lune, 'lune', 8.0, bord='doux', repere_monde=True)

        scenes.sphere_locale(p, self.vue3d, cx, cy, rr, scene, couleur_ciel='ciel' if alt_s > 0 else 'nuit')
        r2 = dessin.cadre(p, z[1], tr('anim_positionsdemonstrator_phase'))
        if self.c_phase.isChecked():
            rl = min(r2.width(), r2.height()) * 0.32
            dessin.phase_lune(p, r2.center().x(), r2.center().y() - 10, rl, e)
            dessin.texte(p, r2.center().x(), r2.center().y() + rl + 6, tr('anim_phase_' + astro.nom_de_phase(e)), 'doux')
        if self.c_heure.isChecked():
            dessin.police(p, 1.3, gras=True)
            dessin.texte(p, r2.center().x(), r2.bottom() - 18, heures_minutes(heure_du_soleil(self.ps.value())))
            dessin.police(p, 1 / 1.3)
