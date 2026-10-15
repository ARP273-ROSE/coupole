"""Paths of the Sun : sur la sphère locale, les trajectoires diurnes du Soleil aux solstices et aux équinoxes
(parallèles de déclinaison ±23,44° et 0°), et celle du jour choisi, avec les points de lever et de coucher.
La partie au-dessus de l'horizon donne la durée du jour ; leur inclinaison sur l'horizon vaut 90° − |φ|."""
from __future__ import annotations

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..maintenant import heure_solaire
from ..base import Animation, angle, date_du_jour, duree_hm

ANNEE = 2026
EPS = astro.obliquite_moyenne(astro.jj_jour_de_l_annee(ANNEE, 0))
CHEMINS = (('solstice_juin', EPS, 'accent3'), ('equinoxes', 0.0, 'accent1'), ('solstice_dec', -EPS, 'accent2'))


class TrajectoiresSoleil(Animation):
    ID = 'sunpaths'
    JOURS_PAR_S = 20.0

    TEMPS = ('jour',)
    HEURE_SOLAIRE = True

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        j, h = heure_solaire(m.i, m.lon)
        self.poser(self.jour, j)
        if m.lat is not None:
            self.poser(self.lat, m.lat)

    def construire(self):
        self.vue3d = self.vue(200.0, 25.0, 1.0, 89.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.jour = self.curseur('jour', 0.0, 364.0, 120.0, dec=0, cle_texte='anim_c_jour')
        self.c_ref = self.coche('reference', True)
        self.c_jour = self.coche('du_jour', True)

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def valeurs(self):
        lat = self.lat.value()
        d = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['delta']
        out = [(tr('anim_c_date'), date_du_jour(self.jour.value())), (tr('anim_c_dec'), angle(d)),
               (tr('anim_sunmotions_duree'), duree_hm(astro.duree_du_jour_h(d, lat))),
               (tr('anim_sunmotions_culmination'), angle(astro.hauteur_culmination(d, lat)))]
        az = astro.azimut_lever(d, lat)
        if az is not None:
            out.append((tr('anim_sunmotions_az_lever'), '%s / %s' % (angle(az), angle(360 - az))))
        for cle, dd, _ in CHEMINS:
            out.append((tr('anim_sunpaths_duree_' + cle), duree_hm(astro.duree_du_jour_h(dd, lat))))
        return out

    def dessiner(self, p, rect):
        self.zone_rotative(rect, self.vue3d)
        r = min(rect.width(), rect.height()) * 0.40
        cx, cy = rect.center().x(), rect.center().y() + 6
        lat = self.lat.value()
        conv = scenes.eq_vers_local(0.0, lat)
        d = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['delta']

        def chemin(pe, dd, coul, ep):
            pe.courbe(conv(scenes.cercle_declinaison(dd, 241)), coul, ep, arriere='pale')
            for signe in (-1, 1):
                h0 = astro.angle_horaire_lever(dd, lat)
                if 0 < h0 < 180:
                    pe.point(conv(astro.vecteur_equatorial(signe * h0, dd)), coul, 4.0)

        def scene(pe):
            pe.courbe(dessin.cercle((0, -1, 0), debut=0, fin=180, origine=(1, 0, 0)), 'meridien', 1.4,
                      repere_monde=True)
            pe.segment(conv((0, 0, 1)), conv((0, 0, 1.2)), 'equateur', 2.0)
            if self.c_ref.isChecked():
                for _, dd, coul in CHEMINS:
                    chemin(pe, dd, coul, 2.0)
            if self.c_jour.isChecked():
                chemin(pe, d, 'soleil', 3.0)

        pe = scenes.sphere_locale(p, self.vue3d, cx, cy, r, scene)
        if self.c_ref.isChecked():
            for cle, dd, coul in CHEMINS:
                h = astro.hauteur_culmination(dd, lat)
                if h > 0:
                    pe.etiquette(np.array(astro.vecteur_horizon(180.0 if lat >= dd else 0.0, h)) * 1.06,
                                 tr('anim_sunpaths_' + cle), coul)
        dessin.police(p, 1.1, gras=True)
        dessin.texte(p, rect.x() + 12, rect.y() + 22, date_du_jour(self.jour.value()), centre=False)
        dessin.police(p, 1 / 1.1)


class VueEnsembleSoleil(Animation):
    """Sun Motions Overview : construction pas à pas de la sphère locale (pôles, équateur céleste, trajet des
    équinoxes, trajets des solstices) pour une latitude, comme les quatre étapes de l'original."""
    ID = 'sunmotionsoverview'
    HEURES_PAR_S = 2.0

    TEMPS = ('heure',)
    HEURE_SOLAIRE = True

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        j, h = heure_solaire(m.i, m.lon)
        self.poser(self.heure, h)
        if m.lat is not None:
            self.poser(self.lat, m.lat)

    def construire(self):
        self.vue3d = self.vue(215.0, 25.0, 1.0, 89.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.heure = self.curseur('heure', 0.0, 24.0, 12.0, dec=2, unite='h', cle_texte='anim_c_heure')
        self.etapes = [self.coche('etape%d' % i, False) for i in range(1, 5)]

    def avancer(self, dt):
        self.heure.setValue((self.heure.value() + dt * self.HEURES_PAR_S) % 24.0)

    def valeurs(self):
        lat = self.lat.value()
        out = [(tr('anim_latsim_hauteur_pole'), angle(abs(lat))),
               (tr('anim_meridaltdiagram_eq'), angle(90 - abs(lat)))]
        for cle, dd, _ in CHEMINS:
            out.append((tr('anim_sunpaths_duree_' + cle), duree_hm(astro.duree_du_jour_h(dd, lat))))
        return out

    def dessiner(self, p, rect):
        self.zone_rotative(rect, self.vue3d)
        r = min(rect.width(), rect.height()) * 0.40
        cx, cy = rect.center().x(), rect.center().y() + 6
        lat = self.lat.value()
        conv = scenes.eq_vers_local(0.0, lat)
        e = [c.isChecked() for c in self.etapes]
        h = (self.heure.value() - 12.0) * 15.0

        def scene(pe):
            if e[0]:
                pe.segment(conv((0, 0, -1.2)), conv((0, 0, 1.2)), 'equateur', 2.0)
            if e[1]:
                pe.courbe(conv(dessin.cercle((0, 0, 1))), 'equateur', 2.0)
            for k, (_, dd, coul) in enumerate(CHEMINS):
                if (k == 1 and e[2]) or (k != 1 and e[3]):
                    pe.courbe(conv(scenes.cercle_declinaison(dd, 241)), coul, 2.2, arriere='pale')
                    pe.point(conv(astro.vecteur_equatorial(-h, dd)), 'soleil', 6.0)

        pe = scenes.sphere_locale(p, self.vue3d, cx, cy, r, scene)
        if e[0]:
            pe.etiquette(conv((0, 0, 1.3)), tr('anim_radecdemo_l_pnc'), 'equateur')
            pe.etiquette(conv((0, 0, -1.3)), tr('anim_radecdemo_l_psc'), 'equateur')
