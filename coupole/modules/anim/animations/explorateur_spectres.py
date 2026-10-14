"""Spectrum Explorer : spectres continu, d'émission et d'absorption.  Les raies de six familles (hélium ionisé,
hélium neutre, hydrogène, métaux ionisés, métaux neutres, molécules) apparaissent selon le type spectral de l'étoile :
leurs intensités, leurs longueurs d'onde et la température de chaque type sont celles de l'original (classes de
luminosité I, III et V ; l'original affinait les raies des supergéantes, plus étroites)."""
from __future__ import annotations

from PyQt6.QtCore import QRectF

from ....core.i18n import tr
from .. import dessin, hr
from ..base import Animation, nombre
from ..graphe import Axes, bande_spectre
from .parallaxe_spectro import RAIES, intensites

FAMILLES = ('he_ii', 'he_i', 'h', 'metaux_ionises', 'metaux', 'molecules')
COULEURS = {'he_ii': 'arc1', 'he_i': 'accent2', 'h': 'accent3', 'metaux_ionises': 'accent1', 'metaux': 'horizon',
            'molecules': 'terre'}
LAMBDA = (380.0, 720.0)
_TABLE = [intensites(t) for t in range(70)]             # intensités de chaque type (calculées une fois)


class ExplorateurSpectres(Animation):
    ID = 'spectrum010'
    ANIMEE = False

    def construire(self):
        self.mode = self.choix('mode', [('anim_spectrum010_continu', 'continu'), ('anim_spectrum010_emission', 'emission'),
                                        ('anim_spectrum010_absorption', 'absorption')], 'absorption')
        self.sp = self.curseur('type', 0.0, 69.0, 42.0, dec=0)
        self.classe = self.choix('classe', [('anim_spectroparallax_c_I', 'I'), ('anim_spectroparallax_c_III', 'III'),
                                            ('anim_spectroparallax_c_V', 'V')], 'V')
        self.cases = {f: self.coche('f_' + f, True) for f in FAMILLES}
        self._etat()

    def _etat(self):
        mode = self.mode.currentData()
        for w in (self.sp, self.classe):
            w.setEnabled(mode == 'absorption')
        for c in self.cases.values():
            c.setEnabled(mode != 'continu')

    def reglage_change(self):
        self._etat()
        super().reglage_change()

    def temperature(self) -> float:
        cl = self.classe.currentData()
        t = self.sp.value()
        if cl == 'III' and t < 40:              # la table des géantes commence à G0 : séquence principale avant
            cl = 'V'
        return hr.temperature_de_type(t, cl)

    def raies(self):
        """[(λ, force 0–1, famille)] des familles cochées, selon le mode et le type spectral."""
        mode = self.mode.currentData()
        if mode == 'continu':
            return []
        it = intensites(int(round(self.sp.value())))
        out = []
        for f in FAMILLES:
            if self.cases[f].isChecked():
                force = 1.0 if mode == 'emission' else it[f] / 100.0
                out += [(lam, force, f) for lam in RAIES[f]]
        return out

    def valeurs(self):
        mode = self.mode.currentData()
        out = [(tr('anim_spectrum010_mode_v'), tr('anim_spectrum010_' + mode))]
        if mode == 'absorption':
            out += [(tr('anim_spectrum010_type_v'), '%s %s' % (hr.nom_type(self.sp.value()), self.classe.currentData())),
                    (tr('anim_stellarlum_temperature'), '%s K' % nombre(self.temperature(), 0))]
            it = intensites(int(round(self.sp.value())))
            fortes = [tr('anim_spectrum010_f_' + f) for f in FAMILLES if it[f] >= 50]
            out.append((tr('anim_spectrum010_fortes'), ', '.join(fortes) or tr('anim_c_aucun')))
        return out

    def dessiner(self, p, rect):
        mode = self.mode.currentData()
        z = dessin.zones(rect, 2, 10.0)
        r = dessin.cadre(p, z[0], tr('anim_spectrum010_titre_' + mode))
        ep = {'I': 1.5, 'III': 2.5, 'V': 3.5}[self.classe.currentData()] if mode == 'absorption' else 2.5
        raies = [(lam, f, ep) for lam, f, _ in self.raies()]
        bande = QRectF(r.x() + 10, r.y() + 6, r.width() - 20, max(30.0, r.height() - 34))
        if mode == 'emission':
            bande_spectre(p, bande, *LAMBDA, None, raies)
        else:
            bande_spectre(p, bande, *LAMBDA, lambda lam: 1.0, raies, raies_absorption=True)
        dessin.police(p, 0.85)
        for lam in range(400, 701, 50):
            x = bande.left() + bande.width() * (lam - LAMBDA[0]) / (LAMBDA[1] - LAMBDA[0])
            dessin.texte(p, x, bande.bottom() + 12, '%d nm' % lam, 'doux')
        dessin.police(p, 1 / 0.85)
        # intensité des familles selon le type spectral (courbes de l'original)
        r2 = dessin.cadre(p, z[1], tr('anim_spectrum010_titre_intensites'))
        ax = Axes(r2, 0, 69, 0, 105, marges=(40, 10, 110, 26)).avec(p)
        ax.fond(p, '', tr('anim_c_intensite'), fmt_x=lambda v: hr.nom_type(v), n_x=7)
        for f in FAMILLES:
            pts = [(t, _TABLE[t][f]) for t in range(70)]
            actif = self.cases[f].isChecked()
            ax.courbe(pts, COULEURS[f], 2.0 if actif else 1.0, 1.0 if actif else 0.35)
            dessin.texte(p, ax.r.right() + 8, ax.r.top() + 10 + 16 * FAMILLES.index(f), tr('anim_spectrum010_f_' + f),
                         COULEURS[f], centre=False)
        ax.verticale(self.sp.value(), 'texte', 1.5, False)
