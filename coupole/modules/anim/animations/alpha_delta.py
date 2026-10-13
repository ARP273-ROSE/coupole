"""Celestial-Equatorial (RA/Dec) Demonstrator : sphère céleste avec la Terre au centre ; une étoile à placer,
arcs de l'ascension droite (le long de l'équateur céleste depuis le cercle horaire 0 h, vers l'est) et de la
déclinaison ; écliptique, pôles, équateurs à afficher."""
from __future__ import annotations

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..base import Animation, angle, nombre

EPS = astro.obliquite_moyenne()           # obliquité J2000 (23,439°)


class AlphaDelta(Animation):
    ID = 'radecdemo'
    ANIMEE = False

    def construire(self):
        self.vue3d = self.vue(217.0, 32.0)
        self.ra = self.curseur('ra', 0.0, 24.0, 4.0, dec=2, unite='h', cle_texte='anim_c_ra')
        self.dec = self.curseur('dec', -90.0, 90.0, 60.0, dec=1, unite='°', cle_texte='anim_c_dec')
        self.c_est = self.coche('est', False)
        self.c_ecliptique = self.coche('ecliptique', False)
        self.c_poles_terre = self.coche('poles_terre', False)
        self.c_equateur = self.coche('equateur', False)
        self.c_poles_ciel = self.coche('poles_ciel', False)
        self.c_equateur_celeste = self.coche('equateur_celeste', False)
        self.c_zero = self.coche('zero', False)
        self._pe = None

    def valeurs(self):
        h = self.ra.value()
        return [(tr('anim_c_ra'), '%s h = %s' % (nombre(h, 2), angle(15 * h))),
                (tr('anim_c_dec'), angle(self.dec.value()))]

    def presser(self, pos, bouton):
        if self._pe is not None:
            e = np.array(astro.vecteur_equatorial(15 * self.ra.value(), self.dec.value()))
            xs, ys, zs, _ = self._pe.ecran(e)
            if zs[0] >= 0 and abs(pos.x() - xs[0]) < 14 and abs(pos.y() - ys[0]) < 14:
                self._glisse = self._deplacer
                return True
        return super().presser(pos, bouton)

    def _deplacer(self, pos):
        v = self._pe.depuis_ecran(pos.x(), pos.y()) if self._pe else None
        if v is not None:
            self.ra.setValue((np.degrees(np.arctan2(v[1], v[0])) % 360.0) / 15.0)
            self.dec.setValue(float(np.degrees(np.arcsin(np.clip(v[2], -1, 1)))))

    def dessiner(self, p, rect):
        r = min(rect.width(), rect.height()) * 0.40
        cx, cy = rect.center().x(), rect.center().y()
        self.zone_rotative(rect, self.vue3d)
        pe = dessin.Peintre3D(p, self.vue3d, cx, cy, r)
        self._pe = pe
        ra, dec = 15 * self.ra.value(), self.dec.value()
        pe.contour('grille', 'sphere', 0.30)
        pe.courbe(scenes.cercle_horaire(90.0, -90, 90, 91), 'grille', 1.0, 0.7)
        pe.courbe(scenes.cercle_horaire(270.0, -90, 90, 91), 'grille', 1.0, 0.7)
        pe.courbe(scenes.cercle_horaire(180.0, -90, 90, 91), 'grille', 1.0, 0.7)
        pe.courbe(dessin.cercle((0, 0, 1)), 'equateur', 2.0)                       # équateur céleste
        pe.courbe(scenes.cercle_horaire(0.0), 'equateur', 2.0)                       # cercle horaire 0 h
        if self.c_ecliptique.isChecked():
            pe.courbe(scenes.ecliptique(EPS), 'ecliptique', 2.0)
            pe.etiquette(np.array(astro.vecteur_equatorial(*astro.ecliptique_vers_equatorial(
                (self.vue3d.az + 60) % 360, 0, EPS))) * 1.04, tr('anim_radecdemo_l_ecliptique'), 'ecliptique')
        # petite Terre au centre (équateur, axe)
        terre = dessin.Peintre3D(p, self.vue3d, cx, cy, r * 0.2)
        terre.contour('terre', 'terre', 0.55)
        terre.courbe(dessin.cercle((0, 0, 1)), 'equateur', 1.2)
        pe.segment((0, 0, 1), (0, 0, 1.25), 'doux', 2.0)
        pe.segment((0, 0, -1), (0, 0, -1.25), 'doux', 2.0)
        pe.segment((0, 0, 0.2), (0, 0, 1.0), 'doux', 1.0, 0.5)
        pe.courbe(scenes.cercle_horaire(ra), 'grille', 1.2)                           # cercle horaire de l'étoile
        pe.courbe(scenes.cercle_declinaison(dec), 'grille', 1.2)
        if ra > 1e-6:
            pe.courbe(scenes.arc_equateur(0.0, ra), 'arc1', 3.0)
        if abs(dec) > 1e-6:
            pe.courbe(scenes.cercle_horaire(ra, 0.0, dec, 60), 'arc2', 3.0)
        etoile = np.array(astro.vecteur_equatorial(ra, dec))
        pe.point(etoile, 'etoile', 6.0, bord='soleil')
        pe.etiquette(np.array(astro.vecteur_equatorial(ra / 2, -6)), '%s h' % nombre(self.ra.value(), 1), 'arc1')
        pe.etiquette(np.array(astro.vecteur_equatorial(ra + 14, dec / 2)), angle(dec), 'arc2')
        if self.c_est.isChecked():
            a = np.array(astro.vecteur_equatorial((-self.vue3d.az + 60) % 360, 0)) * 1.15
            b = np.array(astro.vecteur_equatorial((-self.vue3d.az + 75) % 360, 0)) * 1.15
            x0, y0, _, _ = pe.ecran(a)
            x1, y1, _, _ = pe.ecran(b)
            dessin.fleche(p, x0[0], y0[0], x1[0], y1[0], dessin.stylo('accent1', 2.0))
            dessin.texte(p, x1[0] + 12, y1[0], tr('anim_pc_e'), 'accent1')
        if self.c_poles_terre.isChecked():
            pe.etiquette((0, 0, 0.27), tr('anim_radecdemo_l_pole_nord'))
            pe.etiquette((0, 0, -0.27), tr('anim_radecdemo_l_pole_sud'))
        if self.c_equateur.isChecked():
            pe.etiquette(np.array(astro.vecteur_equatorial((-self.vue3d.az + 34) % 360, 0)) * 0.24,
                         tr('anim_radecdemo_l_equateur'), 'equateur')
        if self.c_poles_ciel.isChecked():
            pe.etiquette((0, 0, 1.33), tr('anim_radecdemo_l_pnc'))
            pe.etiquette((0, 0, -1.33), tr('anim_radecdemo_l_psc'))
        if self.c_equateur_celeste.isChecked():
            pe.etiquette(np.array(astro.vecteur_equatorial((-self.vue3d.az + 34) % 360, 0)) * 1.06,
                         tr('anim_radecdemo_l_equateur_celeste'), 'equateur')
        if self.c_zero.isChecked():
            pe.etiquette(np.array(astro.vecteur_equatorial(0, 35)) * 1.06, tr('anim_radecdemo_l_zero'), 'equateur')
