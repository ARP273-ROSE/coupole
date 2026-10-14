"""Blackbody Curves (NAAP) : jusqu'à cinq courbes de Planck à comparer.  Pour la courbe choisie : maximum
(loi de Wien λ_max = b / T), aire sous la courbe (σ T⁴ / π, loi de Stefan-Boltzmann), couleur perçue, et
magnitudes dans les filtres U, B, V, R (courbes de transmission de Landolt 1992, points zéro de l'original) avec les
indices de couleur.  Constantes exactes du SI : l'original prenait σ = 5,669 × 10⁻⁸ et b = 2,897 768 × 10⁻³ m K."""
from __future__ import annotations

import math

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre
from ..graphe import Axes
from .gravitation import scientifique

COULEURS = ('accent1', 'accent2', 'accent3', 'arc1', 'horizon')
N_MAX = 5
T_DEFAUT = 6000.0


class CorpsNoir(Animation):
    ID = 'bbexplorer'
    ANIMEE = False

    def construire(self):
        self.choisie = 0
        self.courbe = self.choix('courbe', [('anim_bbexplorer_courbe_%d' % (k + 1), k) for k in range(N_MAX)], 0)
        self.courbe.activated.connect(self._choisir)
        self.t = self.curseur('temperature', 3000.0, 25000.0, T_DEFAUT, dec=0, unite='K', log=True)
        self.temperatures = [self.t.value()]
        self.b_ajouter = self.bouton('anim_bbexplorer_ajouter', self._ajouter)
        self.b_retirer = self.bouton('anim_bbexplorer_retirer', self._retirer)
        self.lmax = self.curseur('lambda_max', 1000.0, 5000.0, 1000.0, dec=0, unite='nm')
        self.echelle = self.choix('echelle', [('anim_bbexplorer_e_toutes', 'toutes'),
                                              ('anim_bbexplorer_e_choisie', 'choisie'),
                                              ('anim_bbexplorer_e_fixe', 'fixe')], 'toutes')
        self.c_aire = self.coche('aire', False)
        self.c_pic = self.coche('pic', True)
        self.c_filtres = self.coche('filtres', False)
        self._fixe = None
        self._etat_boutons()

    # ------------------------------------------------------------ courbes
    def _etat_boutons(self):
        n = len(self.temperatures)
        self.b_ajouter.setEnabled(n < N_MAX)
        self.b_retirer.setEnabled(n > 1)
        for k in range(N_MAX):
            self.courbe.model().item(k).setEnabled(k < n)

    def _choisir(self, *_):
        k = self.courbe.currentData()
        if k >= len(self.temperatures):
            k = len(self.temperatures) - 1
            self.courbe.setCurrentIndex(k)
        self.choisie = k
        self.t.setValue(self.temperatures[k])
        self.rafraichir()

    def _ajouter(self):
        if len(self.temperatures) < N_MAX:
            self.temperatures.append(self.t.value())
            self.choisie = len(self.temperatures) - 1
            self.courbe.setCurrentIndex(self.choisie)
            self._etat_boutons()
            self.rafraichir()

    def _retirer(self):
        if len(self.temperatures) > 1:
            del self.temperatures[self.choisie]
            self.choisie = min(self.choisie, len(self.temperatures) - 1)
            self.courbe.setCurrentIndex(self.choisie)
            self.t.setValue(self.temperatures[self.choisie])
            self._etat_boutons()
            self.rafraichir()

    def etat_initial(self):
        self.temperatures = [self.t.value()]
        self.choisie = 0
        self.courbe.setCurrentIndex(0)
        self._fixe = None
        self._etat_boutons()

    def reglage_change(self):
        if self.choisie < len(self.temperatures):
            self.temperatures[self.choisie] = self.t.value()
        if self.echelle.currentData() != 'fixe':
            self._fixe = None
        super().reglage_change()

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        t = self.temperatures[self.choisie]
        m = lumiere.magnitudes_corps_noir(t)
        out = [(tr('anim_bbexplorer_temperature_v'), '%s K' % nombre(t, 0)),
               (tr('anim_c_pic_wien'), '%s nm' % nombre(lumiere.pic_wien_m(t) * 1e9, 1)),
               (tr('anim_c_exitance'), '%s W·m⁻²' % scientifique(lumiere.exitance(t))),
               (tr('anim_bbexplorer_rapport_soleil'), '× %s' % nombre((t / 5772.0) ** 4, 2))]
        if self.c_filtres.isChecked():
            out += [('U − B', nombre(m['U'] - m['B'], 2)), ('B − V', nombre(m['B'] - m['V'], 2)),
                    ('V − R', nombre(m['V'] - m['R'], 2))]
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        filtres = self.c_filtres.isChecked()
        if filtres:
            z = dessin.zones_principale(rect, 1, 0.68)
            r = dessin.cadre(p, z[0], tr('anim_bbexplorer_titre'))
        else:
            r = dessin.cadre(p, rect, tr('anim_bbexplorer_titre'))
        lmax = self.lmax.value()
        t_sel = self.temperatures[self.choisie]
        mode = self.echelle.currentData()
        if mode == 'choisie':
            ymax = self._max_courbe(t_sel, lmax)
        elif mode == 'fixe':
            if self._fixe is None:
                self._fixe = max(self._max_courbe(t, lmax) for t in self.temperatures)
            ymax = self._fixe
        else:
            ymax = max(self._max_courbe(t, lmax) for t in self.temperatures)
        ax = Axes(r, 0, lmax, 0, ymax * 1.1 / 1e12, marges=(54, 14, 14, 30)).avec(p)
        ax.bande_visible(0.18)
        ax.fond(p, tr('anim_c_lambda_nm'), tr('anim_c_luminance_unite'))
        if filtres:
            for f in lumiere.FILTRES:
                w0, _, tt = lumiere.table('filtre_' + f)
                pts = [(w0 + i, tt[i] * lumiere.planck((w0 + i) * 1e-9, t_sel) / 1e12) for i in range(0, len(tt), 4)]
                ax.remplir(pts, {'U': 'arc1', 'B': 'accent2', 'V': 'horizon', 'R': 'accent3'}[f], 0.35)
        pas = max(2.0, lmax / 220)
        for k, t in enumerate(self.temperatures):
            pts = [(pas * i, lumiere.planck(pas * i * 1e-9, t) / 1e12) for i in range(1, int(lmax / pas) + 1)]
            choisie = k == self.choisie
            if choisie and self.c_aire.isChecked():
                ax.remplir(pts, COULEURS[k], 0.25)
            ax.courbe(pts, COULEURS[k], 3.0 if choisie else 1.4, 1.0 if choisie else 0.75)
        # légende : couleur perçue de chaque courbe (avant l'étiquette du maximum, qui l'évite)
        dessin.police(p, 0.9)
        x, y = ax.r.right() - 150, ax.r.top() + 14
        for k, t in enumerate(self.temperatures):
            rgb = lumiere.couleur_corps_noir(int(round(t)))
            dessin.disque(p, x, y + 18 * k, 6, QColor(*rgb), bord=COULEURS[k])
            dessin.texte(p, x + 12, y + 18 * k + 4, '%s K' % nombre(t, 0), COULEURS[k], centre=False)
        dessin.police(p, 1 / 0.9)
        if self.c_pic.isChecked():
            lp = lumiere.pic_wien_m(t_sel) * 1e9
            ax.verticale(lp, COULEURS[self.choisie], etiquette=tr('anim_bbexplorer_pic_a', l=nombre(lp, 1)))
        if filtres:
            self._barres(p, dessin.cadre(p, z[1], tr('anim_bbexplorer_titre_filtres')), t_sel)

    @staticmethod
    def _max_courbe(t, lmax):
        lp = lumiere.pic_wien_m(t) * 1e9
        return lumiere.planck(min(lp, lmax) * 1e-9, t)

    def _barres(self, p, r, t):
        """Magnitudes U, B, V, R de la courbe choisie (barres : flux reçu dans chaque filtre, relatif au plus fort)."""
        flux = {f: lumiere.somme_filtre(f, lambda w: lumiere.planck(w * 1e-9, t)) for f in lumiere.FILTRES}
        m = lumiere.magnitudes_corps_noir(t)
        fmax = max(flux.values())
        n = len(lumiere.FILTRES)
        lw = r.width() / n
        hmax = r.height() - 46
        for k, f in enumerate(lumiere.FILTRES):
            h = hmax * flux[f] / fmax
            x = r.x() + k * lw + lw * 0.2
            p.fillRect(QRectF(x, r.bottom() - 30 - h, lw * 0.6, h),
                       dessin.c({'U': 'arc1', 'B': 'accent2', 'V': 'horizon', 'R': 'accent3'}[f], 0.8))
            dessin.texte(p, x + lw * 0.3, r.bottom() - 18, f, 'texte')
            dessin.texte(p, x + lw * 0.3, r.bottom() - 36 - h, nombre(m[f], 2), 'doux')
        dessin.texte(p, r.center().x(), r.bottom() - 4, tr('anim_bbexplorer_magnitudes'), 'doux')
