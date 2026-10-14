"""Filters Simulator (NAAP) : une source de lumière, des filtres, un détecteur.  Le spectre reçu est le produit du
spectre de la source et des transmissions des filtres placés devant le détecteur ; la couleur perçue de chaque
spectre est calculée avec les fonctions colorimétriques CIE 1931 (corrigées par Judd et Vos) et la norme sRGB.
Sources : corps noir (loi de Planck), gaussienne, Soleil hors atmosphère ; filtres U, B, V, R (Landolt 1992) et
atmosphère terrestre (transmissions de l'original), plus un filtre gaussien réglable."""
from __future__ import annotations

import math

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre
from ..graphe import Axes

LAMBDA = (200.0, 1100.0)
PAS = 5.0
FILTRES = ('U', 'B', 'V', 'R', 'atmosphere', 'gauss')
COULEURS = {'U': 'arc1', 'B': 'accent2', 'V': 'horizon', 'R': 'accent3', 'atmosphere': 'doux', 'gauss': 'accent1'}


class Filtres(Animation):
    ID = 'filters'
    ANIMEE = False

    def construire(self):
        self.source = self.choix('source', [('anim_filters_s_corps_noir', 'corps_noir'),
                                            ('anim_filters_s_gauss', 'gauss'), ('anim_filters_s_soleil', 'soleil')],
                                 'corps_noir')
        self.t = self.curseur('temperature', 2000.0, 30000.0, 6000.0, dec=0, unite='K', log=True)
        self.lc = self.curseur('pic', 300.0, 1000.0, 600.0, dec=0, unite='nm')
        self.largeur = self.curseur('largeur', 5.0, 300.0, 50.0, dec=0, unite='nm')
        self.cases = {f: self.coche('f_' + f, f == 'V') for f in FILTRES}
        self.fc = self.curseur('filtre_centre', 300.0, 1000.0, 450.0, dec=0, unite='nm')
        self.fl = self.curseur('filtre_largeur', 5.0, 300.0, 40.0, dec=0, unite='nm')
        self._etat()

    def _etat(self):
        s = self.source.currentData()
        self.t.setEnabled(s == 'corps_noir')
        self.lc.setEnabled(s == 'gauss')
        self.largeur.setEnabled(s == 'gauss')
        g = self.cases['gauss'].isChecked()
        self.fc.setEnabled(g)
        self.fl.setEnabled(g)

    def reglage_change(self):
        self._etat()
        super().reglage_change()

    # ------------------------------------------------------------ spectres (relatifs, maximum 1)
    def source_brute(self):
        s = self.source.currentData()
        if s == 'corps_noir':
            t = self.t.value()
            ref = lumiere.planck(lumiere.pic_wien_m(t), t)
            return lambda w: lumiere.planck(w * 1e-9, t) / ref
        if s == 'gauss':
            c, sg = self.lc.value(), self.largeur.value() / 2.354_820_045        # largeur à mi-hauteur
            return lambda w: math.exp(-0.5 * ((w - c) / sg) ** 2)
        v = lumiere.spectres()['soleil']['v']
        ref = max(v)
        return lambda w: lumiere.valeur('soleil', w, 'v') / ref

    def transmission(self):
        actifs = [f for f in FILTRES if self.cases[f].isChecked()]
        c, sg = self.fc.value(), self.fl.value() / 2.354_820_045
        k = {f: lumiere.spectres()['filtre_' + f]['t_max'] / max(lumiere.table('filtre_' + f)[2])
             for f in lumiere.FILTRES}

        def t(w):
            v = 1.0
            for f in actifs:
                if f == 'atmosphere':
                    v *= lumiere.valeur('atmosphere', w) if w <= 1000 else 1.0
                elif f == 'gauss':
                    v *= math.exp(-0.5 * ((w - c) / sg) ** 2)
                else:
                    v *= lumiere.valeur('filtre_' + f, w) * k[f]
            return v
        return t

    def tables(self):
        src, tr_ = self.source_brute(), self.transmission()
        n = int((LAMBDA[1] - LAMBDA[0]) / PAS) + 1
        ws = [LAMBDA[0] + PAS * i for i in range(n)]
        s = [src(w) for w in ws]
        t = [tr_(w) for w in ws]
        return ws, s, t, [a * b for a, b in zip(s, t)]

    @staticmethod
    def couleur(ws, vals) -> tuple[QColor, float]:
        """Couleur perçue (teinte et éclat relatifs) d'un spectre tabulé."""
        d = dict(zip(ws, vals))
        x, y, z = lumiere.xyz(lambda w: d.get(w, 0.0))
        return x, y, z

    def valeurs(self):
        ws, s, t, d = self.tables()
        vis = [i for i, w in enumerate(ws) if 380 <= w <= 750]
        fs = sum(s[i] for i in vis)
        fd = sum(d[i] for i in vis)
        return [(tr('anim_filters_transmis'), '%s %%' % nombre(100 * fd / fs if fs else 0, 1)),
                (tr('anim_filters_transmis_tout'), '%s %%' % nombre(100 * sum(d) / sum(s) if sum(s) else 0, 1))]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        ws, s, t, d = self.tables()
        h = rect.height() / 3
        z = [QRectF(rect.x(), rect.y() + i * h, rect.width(), h) for i in range(3)]
        xs, ys, zs = self.couleur(ws, s)
        ref = ys or 1.0
        self._graphe(p, z[0], tr('anim_filters_titre_source'), ws, s, 'accent1', (xs, ys, zs), ref)
        self._graphe(p, z[1], tr('anim_filters_titre_filtres'), ws, t, 'accent2', None, ref, filtres=True)
        self._graphe(p, z[2], tr('anim_filters_titre_detecteur'), ws, d, 'accent3', self.couleur(ws, d), ref)

    def _graphe(self, p, zone, titre, ws, vals, cle, xyz, ref, filtres=False):
        r = dessin.cadre(p, zone, titre)
        ax = Axes(r, LAMBDA[0], LAMBDA[1], 0, 1.05, marges=(36, 4, 70, 22)).avec(p)
        ax.bande_visible(0.15)
        ax.fond(p, n_y=2, n_x=9)
        if filtres:
            for f in FILTRES:
                if self.cases[f].isChecked() and f not in ('atmosphere', 'gauss'):
                    w0, _, tt = lumiere.table('filtre_' + f)
                    k = lumiere.spectres()['filtre_' + f]['t_max'] / max(tt)
                    ax.courbe([(w0 + i, tt[i] * k) for i in range(0, len(tt), 3)], COULEURS[f], 1.0, 0.6)
        pts = list(zip(ws, vals))
        ax.remplir(pts, cle, 0.25)
        ax.courbe(pts, cle, 2.0)
        if xyz is not None:
            x, y, zz = xyz
            # teinte normalisée, éclat relatif à la source (une source plus faible paraît plus sombre)
            if y > 0:
                rgb = lumiere.rgb_de_xyz(x / ref, y / ref, zz / ref)
            else:
                rgb = (0, 0, 0)
            pastille = QRectF(ax.r.right() + 14, ax.r.top() + 4, 44, 44)
            p.setPen(dessin.stylo('doux', 1.0))
            p.setBrush(QColor(*rgb))
            p.drawRoundedRect(pastille, 6, 6)
            dessin.police(p, 0.8)
            dessin.texte(p, pastille.center().x(), pastille.bottom() + 10, tr('anim_filters_couleur'), 'doux')
            dessin.police(p, 1 / 0.8)
