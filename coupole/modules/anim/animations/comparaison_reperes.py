"""Coordinate Systems Comparison : à gauche la sphère céleste (étoiles fixes, la Terre tourne au centre avec
l'observateur et son plan d'horizon), à droite le diagramme d'horizon de l'observateur (le ciel tourne).
Régions circumpolaire, de lever et coucher, jamais levée ; traînées d'étoiles ; Grande Ourse, Orion, Croix du Sud
(positions J2000 reprises du simulateur d'origine)."""
from __future__ import annotations

import math
import random

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..base import Animation, angle, heures_minutes
from ..etoiles_reelles import couleur_reelle, reelle

# (α en heures, δ en degrés), tracés comme dans l'original (suites d'indices)
CONSTELLATIONS = {
    'grande_ourse': ([(11.06215, 61.75092), (11.03068, 56.38236), (11.89717, 53.69475), (12.25709, 57.03258),
                      (12.90048, 55.95989), (13.39875, 54.92539), (13.79235, 49.31336)],
                     [(0, 1), (1, 2), (2, 3), (3, 0), (3, 4), (4, 5), (5, 6)]),
    'orion': ([(5.91953, 7.40706), (5.67931, -1.94257), (5.60356, -1.20192), (5.53344, -0.29909),
               (5.41885, 6.3497), (5.79594, -9.6696), (5.2423, -8.20164)],
              [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (1, 5), (3, 6)]),
    'croix_du_sud': ([(12.4433, -63.09905), (12.51943, -57.11321), (12.79535, -59.68876), (12.25242, -58.74893)],
                     [(0, 1), (2, 3)]),
}
DUREES = (0.0, 1.0, 3.0, 6.0, 12.0)              # 0 : en continu
TRAINEES = {'aucune': 0.0, 'courtes': 30.0, 'longues': 90.0}     # longueur en degrés d'angle horaire


class ComparaisonReperes(Animation):
    ID = 'celhorcomp'
    FICHES = True
    HEURES_PAR_S = 1.0

    def construire(self):
        self.celeste = self.vue(225.0, 20.0)
        self.locale = self.vue(200.0, 30.0, 1.0, 89.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.tsl = self.curseur('tsl', 0.0, 24.0, 6.0, dec=2, unite='h', cle_texte='anim_c_tsl')
        self.duree = self.choix('duree', [('anim_celhorcomp_continu', 0.0), ('anim_celhorcomp_1h', 1.0),
                                          ('anim_celhorcomp_3h', 3.0), ('anim_celhorcomp_6h', 6.0),
                                          ('anim_celhorcomp_12h', 12.0)], 0.0)
        self.trainees = self.choix('trainees', [('anim_celhorcomp_aucune', 'aucune'),
                                                ('anim_celhorcomp_courtes', 'courtes'),
                                                ('anim_celhorcomp_longues', 'longues')], 'aucune')
        self.c_cons = {k: self.coche(k, k == 'grande_ourse') for k in CONSTELLATIONS}
        self.c_circ = self.coche('circumpolaire', False)
        self.c_lever = self.coche('lever', False)
        self.c_jamais = self.coche('jamais', False)
        self.c_equateur = self.coche('equateur', True)
        self.c_zero = self.coche('zero', False)
        self.bouton('anim_celhorcomp_ajouter', self.ajouter_etoile)
        self.bouton('anim_celhorcomp_retirer', self.retirer_etoiles)
        self.etoiles = []
        self._ecoule = 0.0
        self._hasard = random.Random(7)

    def ajouter_etoile(self):
        z = self._hasard.uniform(-1.0, 1.0)
        self.etoiles.append((self._hasard.uniform(0, 360.0), math.degrees(math.asin(z))))
        self.rafraichir()

    def retirer_etoiles(self):
        self.etoiles = []
        self.rafraichir()

    def etat_initial(self):
        self.etoiles = []
        self._ecoule = 0.0

    def basculer_lecture(self):
        self._ecoule = 0.0
        super().basculer_lecture()

    def avancer(self, dt):
        pas = dt * self.HEURES_PAR_S
        limite = self.duree.currentData() or 0.0
        if limite and self._ecoule + pas >= limite:
            pas = limite - self._ecoule
            self._ecoule = 0.0
            self.tsl.setValue((self.tsl.value() + pas) % 24.0)
            self.basculer_lecture()
            return
        self._ecoule += pas
        self.tsl.setValue((self.tsl.value() + pas) % 24.0)

    def valeurs(self):
        pl = astro.plages_declinaison(self.lat.value())

        def plage(x):
            return tr('anim_latsim_aucune') if x is None else '%s → %s' % (angle(x[0]), angle(x[1]))
        return [(tr('anim_c_tsl'), heures_minutes(self.tsl.value())),
                (tr('anim_latsim_circumpolaire'), plage(pl['circumpolaire'])),
                (tr('anim_latsim_lever'), plage(pl['lever_coucher'])), (tr('anim_latsim_jamais'), plage(pl['jamais']))]

    def _objets(self):
        out = []
        for k, (etoiles, traits) in CONSTELLATIONS.items():
            if self.c_cons[k].isChecked():
                out.append((k, [(15 * a, d) for a, d in etoiles], traits))
        out.append(('libres', list(self.etoiles), []))
        return out

    def _bandes(self, pe, conv, lat):
        """Régions de déclinaison (bandes de la sphère)."""
        pl = astro.plages_declinaison(lat)
        for cle, case, coul in (('circumpolaire', self.c_circ, 'accent1'), ('lever_coucher', self.c_lever, 'accent2'),
                                ('jamais', self.c_jamais, 'accent3')):
            if case.isChecked() and pl[cle] is not None:
                for d in np.linspace(pl[cle][0], pl[cle][1], 7):
                    pe.courbe(conv(scenes.cercle_declinaison(float(d), 121)), coul, 2.0, 0.55)

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.8)
        lat, tsl = self.lat.value(), 15 * self.tsl.value()
        lon_trainee = TRAINEES[self.trainees.currentData()]
        objets = self._objets()
        # ---------------------------------------------------------------- sphère céleste
        r1 = dessin.cadre(p, z[0], tr('anim_celhorcomp_celeste'))
        self.zone_rotative(r1, self.celeste)
        rr = min(r1.width(), r1.height()) * 0.40
        pe = dessin.Peintre3D(p, self.celeste, r1.center().x(), r1.center().y(), rr)
        pe.contour('grille', 'sphere', 0.3)
        ident = (lambda x: np.asarray(x, dtype=float).reshape(-1, 3))
        self._bandes(pe, ident, lat)
        if self.c_equateur.isChecked():
            pe.courbe(dessin.cercle((0, 0, 1)), 'equateur', 1.8)
        if self.c_zero.isChecked():
            pe.courbe(scenes.cercle_horaire(0.0), 'equateur', 1.8)
        pe.segment((0, 0, 1), (0, 0, 1.2), 'equateur', 2.0)
        pe.segment((0, 0, -1), (0, 0, -1.2), 'equateur', 2.0)
        # horizon de l'observateur (grand cercle de pôle le zénith, α = TSL, δ = φ) et zénith
        zen = np.array(astro.vecteur_equatorial(tsl, lat))
        pe.courbe(dessin.cercle(zen), 'horizon', 2.0)
        pe.point(zen, 'horizon', 4.0)
        terre = dessin.Peintre3D(p, self.celeste, r1.center().x(), r1.center().y(), rr * 0.18)
        terre.contour('terre', 'terre', 0.6)
        terre.point(zen, 'accent3', 3.5)
        self._etoiles(pe, objets, ident, tsl, 0.0)          # étoiles fixes : pas de traînée
        pe.etiquette(zen * 1.12, tr('anim_altazimuth_zenith'), 'horizon')
        # ---------------------------------------------------------------- diagramme d'horizon
        r2 = dessin.cadre(p, z[1], tr('anim_celhorcomp_locale'))
        self.zone_rotative(r2, self.locale)
        rr2 = min(r2.width(), r2.height()) * 0.40
        conv = scenes.eq_vers_local(tsl, lat)

        def scene(pe2):
            self._bandes(pe2, conv, lat)
            if self.c_equateur.isChecked():
                pe2.courbe(conv(dessin.cercle((0, 0, 1))), 'equateur', 1.8)
            if self.c_zero.isChecked():
                pe2.courbe(conv(scenes.cercle_horaire(0.0)), 'equateur', 1.8)
            pe2.segment(conv((0, 0, 1)), conv((0, 0, 1.2)), 'equateur', 2.0)
            self._etoiles(pe2, objets, conv, tsl, lon_trainee)

        scenes.sphere_locale(p, self.locale, r2.center().x(), r2.center().y() + 4, rr2, scene)

    def _etoiles(self, pe, objets, conv, tsl, lon_trainee):
        for nom, etoiles, traits in objets:
            pts = [np.array(astro.vecteur_equatorial(a, d)) for a, d in etoiles]
            for i, j in traits:
                pe.courbe(conv(dessin.arc(pts[i], pts[j], 12)), 'accent1', 1.4, 0.8)
            for k, ((a, d), v) in enumerate(zip(etoiles, pts)):
                if lon_trainee > 0:
                    pe.courbe(conv(scenes.arc_equateur(a, a + lon_trainee, d, 30)), 'etoile', 1.0, 0.45)
                # étoiles réelles des constellations : couleur vraie et fiche ; étoiles « libres » : couleur du thème
                f = reelle('celhorcomp', '%s_%d' % (nom, k)) if nom != 'libres' else None
                col = couleur_reelle('celhorcomp', '%s_%d' % (nom, k)) if f else None
                q = pe.point(conv(v), col or 'etoile', 3.0, bord='doux' if f and dessin.theme() == 'clair' else None)
                if q and q[2] and f:
                    self.survolable(pe.p, f['fiche'], q[0], q[1], 6, k)
