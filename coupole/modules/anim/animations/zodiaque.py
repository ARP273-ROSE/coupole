"""Ecliptic (Zodiac) Simulator : le Soleil au centre, la Terre sur son orbite, et la bande des constellations
traversées par l'écliptique.  Vu de la Terre, le Soleil se projette devant une constellation, qui change au fil
de l'année ; à minuit on voit la constellation opposée.  Limites officielles des constellations (UAI) : 13
constellations dont Ophiuchus ; les « signes » astrologiques sont des secteurs de 30° comptés depuis l'équinoxe."""
from __future__ import annotations

import math

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin
from ..maintenant import heure_solaire
from ..base import Animation, angle, date_du_jour

ANNEE = 2026
SIGNES = ('ari', 'tau', 'gem', 'cnc', 'leo', 'vir', 'lib', 'sco', 'sgr', 'cap', 'aqr', 'psc')


def ecl(lam: float, r: float = 1.0, z: float = 0.0) -> np.ndarray:
    """Point du plan de l'écliptique (repère direct x = point vernal), longitude λ."""
    a = math.radians(lam)
    return np.array([r * math.cos(a), r * math.sin(a), z])


class Zodiaque(Animation):
    ID = 'zodiac'
    JOURS_PAR_S = 20.0

    TEMPS = ('jour',)
    HEURE_SOLAIRE = True

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        j, h = heure_solaire(m.i, m.lon)
        self.poser(self.jour, j)

    def construire(self):
        self.vue3d = self.vue(206.0, 30.0, 0.0, 50.0)
        self.jour = self.curseur('jour', 0.0, 364.0, 0.0, dec=0, cle_texte='anim_c_jour')
        self.c_signes = self.coche('signes', False)

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def valeurs(self):
        lam = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['lambda']
        return [(tr('anim_c_date'), date_du_jour(self.jour.value())), (tr('anim_seasonsim_lambda'), angle(lam)),
                (tr('anim_zodiac_derriere'), tr('anim_cst_' + astro.constellation_du_soleil(lam))),
                (tr('anim_zodiac_minuit'), tr('anim_cst_' + astro.constellation_du_soleil(lam + 180.0))),
                (tr('anim_zodiac_signe'), tr('anim_cst_' + SIGNES[int(lam // 30) % 12]))]

    def dessiner(self, p, rect):
        self.zone_rotative(rect, self.vue3d)
        r = min(rect.width() * 0.45, rect.height() * 0.55)
        cx, cy = rect.center().x(), rect.center().y() + 10
        pe = dessin.Peintre3D(p, self.vue3d, cx, cy, r)
        lam = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['lambda']
        lim = sorted(astro.LIMITES_ZODIAQUE_2026, key=lambda x: x[1])
        devant = astro.constellation_du_soleil(lam)
        minuit = astro.constellation_du_soleil(lam + 180.0)

        def bande(passe_avant: bool):
            for i, (cle, l0) in enumerate(lim):
                l1 = lim[(i + 1) % len(lim)][1]
                if l1 < l0:
                    l1 += 360.0
                ls = np.linspace(l0, l1, 24)
                mil = (l0 + l1) / 2
                av = float(ecl(mil) @ self.vue3d.d) >= 0
                if av != passe_avant:
                    continue
                coul = 'soleil' if cle == devant else 'accent2' if cle == minuit else 'grille'
                for z, a in ((0.12, 0.9), (-0.12, 0.9)):
                    pe.courbe(np.array([ecl(l, 1.0, z) for l in ls]), coul, 1.6, a, arriere='normal',
                              profondeur=False)
                pe.segment(ecl(l0, 1.0, -0.12), ecl(l0, 1.0, 0.12), 'grille', 1.2)
                pe.etiquette(ecl(mil, 1.0, 0.0), tr('anim_cst_' + cle), coul if coul != 'grille' else 'texte')

        bande(False)
        pe.plan('sphere', 0.25, rayon=0.62, bord='grille')
        if self.c_signes.isChecked():
            for k in range(12):
                pe.segment(ecl(30 * k, 0.62), ecl(30 * k, 0.9), 'ecliptique', 1.0, 0.7)
                pe.etiquette(ecl(30 * k + 15, 0.78), tr('anim_cst_' + SIGNES[k]), 'ecliptique')
        terre = ecl(lam + 180.0, 0.55)
        pe.courbe(np.array([ecl(l, 0.55) for l in np.linspace(0, 360, 121)]), 'grille', 1.2, arriere='normal',
                  profondeur=False)
        # visée Terre → Soleil → constellation, et Terre → minuit
        pe.segment(terre, ecl(lam, 1.0), 'soleil', 1.5, 0.7)
        pe.segment(terre, ecl(lam + 180.0, 1.0), 'accent2', 1.2, 0.6)
        xs, ys, _, _ = pe.ecran(np.zeros(3))
        dessin.disque(p, xs[0], ys[0], max(7.0, r * 0.06), 'soleil')
        pe.point(terre, 'terre', max(5.0, r * 0.03))
        bande(True)
        dessin.police(p, 1.1, gras=True)
        dessin.texte(p, rect.x() + 12, rect.y() + 22, date_du_jour(self.jour.value()), centre=False)
        dessin.police(p, 1 / 1.1)
