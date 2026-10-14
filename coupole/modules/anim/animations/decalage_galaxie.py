"""Galactic Redshift Simulator : le spectre d'une galaxie décalé vers le rouge.  Toutes les longueurs d'onde sont
multipliées par (1 + z) : les raies d'absorption (calcium, magnésium, sodium, hydrogène) glissent vers le rouge, et
la lumière qui tombe dans chaque filtre U, B, V, R change, donc la couleur de la galaxie.  Spectre de la galaxie
elliptique M32 (Santos et al. 2002, catalogue VizieR III/219), ramené au repos comme dans l'original
(z_M32 = −6,84 × 10⁻⁴) ; filtres de Landolt (1992).  Vitesse correspondante par l'effet Doppler relativiste
(pour les grands z, le décalage cosmologique ne se traduit pas en vitesse aussi simplement)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QRectF

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre
from ..graphe import Axes, bande_spectre

LAMBDA = (250.0, 950.0)
RAIES = (('Ca K', 393.37), ('Ca H', 396.85), ('G', 430.8), ('Mg b', 517.3), ('Na D', 589.3), ('Hα', 656.28))


def spectre_repos():
    d = lumiere.spectres()['m32']
    k = 1.0 + d['z_original']
    return [(( d['w0'] + d['pas'] * i) * k, f) for i, f in enumerate(d['f'])]


def flux_observe(z: float):
    """F(λ observée) = F_repos(λ / (1 + z)) (spectre seulement décalé, comme l'original)."""
    d = lumiere.spectres()['m32']
    k = 1.0 + d['z_original']
    w0, pas, f = d['w0'], d['pas'], d['f']
    def flux(lam):
        x = (lam / (1 + z) / k - w0) / pas
        i = int(math.floor(x))
        if i < 0 or i >= len(f) - 1:
            return 0.0
        t = x - i
        return f[i] * (1 - t) + f[i + 1] * t
    return flux


def vitesse_relativiste(z: float) -> float:
    """Vitesse (km/s) donnant ce décalage par l'effet Doppler relativiste : v / c = ((1+z)² − 1) / ((1+z)² + 1)."""
    s = (1 + z) ** 2
    return lumiere.C / 1000 * (s - 1) / (s + 1)


class DecalageGalaxie(Animation):
    ID = 'galacticredshift'
    ANIMEE = False

    def construire(self):
        self.z = self.curseur('z', 0.0, 1.0, 0.0, dec=3)
        self.c_filtres = self.coche('filtres', True)
        self.c_raies = self.coche('raies', True)
        self._repos = spectre_repos()[::10]           # un point tous les 2 nm
        self._max = max(v for _, v in self._repos)

    def filtres(self, z: float) -> dict:
        """Sommes Σ T F Δλ et magnitudes dans les quatre filtres pour ce décalage (mémorisées)."""
        cache = self.__dict__.setdefault('_cache_z', {})
        if z not in cache:
            if len(cache) > 64:
                cache.clear()
            f = flux_observe(z)
            sommes = {n: lumiere.somme_filtre(n, f) for n in lumiere.FILTRES}
            cache[z] = {'s': sommes, 'm': {n: (lumiere.spectres()['filtre_' + n]['decalage'] - 2.5 * math.log10(v)
                                               if v > 0 else math.inf) for n, v in sommes.items()}}
        return cache[z]

    def magnitudes(self) -> dict:
        return self.filtres(self.z.value())['m']

    def valeurs(self):
        z = self.z.value()
        m = self.magnitudes()
        return [('z', nombre(z, 3)),
                (tr('anim_galacticredshift_v'), '%s km/s' % nombre(vitesse_relativiste(z), 0)),
                (tr('anim_galacticredshift_halpha'), '%s nm' % nombre(656.28 * (1 + z), 1)),
                ('B − V', nombre(m['B'] - m['V'], 2))]

    def dessiner(self, p, rect):
        z = self.z.value()
        k = 1 + z
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * (0.7 if self.c_filtres.isChecked() else 1.0))
        r = dessin.cadre(p, haut, tr('anim_galacticredshift_titre'))
        bande = QRectF(r.left() + 52, r.top(), r.width() - 66, 22)
        ax = Axes(QRectF(r.left(), bande.bottom() + 4, r.width(), r.height() - 26), LAMBDA[0], LAMBDA[1], 0, 1.05,
                  marges=(52, 6, 14, 28)).avec(p)
        f = flux_observe(z)
        mx = self._max
        bande_spectre(p, QRectF(ax.px(380), bande.top(), ax.px(750) - ax.px(380), bande.height()), 380, 750,
                      lambda lam: f(lam) / mx, pas_px=10.0)
        if self.c_filtres.isChecked():
            for n, cle in zip(lumiere.FILTRES, ('arc1', 'accent2', 'horizon', 'accent3')):
                w0, _, tt = lumiere.table('filtre_' + n)
                ax.remplir([(w0 + i, tt[i]) for i in range(0, len(tt), 4)], cle, 0.12)
        ax.fond(p, tr('anim_c_lambda_nm'), tr('anim_c_flux_relatif'))
        ax.courbe([(lam * k, v / mx) for lam, v in self._repos if LAMBDA[0] <= lam * k <= LAMBDA[1]], 'accent1', 0.0)
        if self.c_raies.isChecked():
            dessin.police(p, 0.8)
            for i, (nom, lam) in enumerate(RAIES):
                ax.verticale(lam * k, 'doux', 1.0, True)
                X = ax.px(lam * k)
                if ax.r.left() <= X <= ax.r.right():
                    dessin.texte(p, X, ax.r.top() + 10 + 12 * (i % 2), nom, 'texte', fond=True)
            dessin.police(p, 1 / 0.8)
        if self.c_filtres.isChecked():
            self._barres(p, dessin.cadre(p, QRectF(rect.x(), haut.bottom(), rect.width(),
                                                   rect.height() - haut.height()), tr('anim_galacticredshift_titre_f')))

    def _barres(self, p, r):
        fz = self.filtres(self.z.value())
        s, m = fz['s'], fz['m']
        m0 = self.filtres(0.0)['m']
        mx = max(self.filtres(0.0)['s'].values())
        w = r.width() / 4
        for i, (n, cle) in enumerate(zip(lumiere.FILTRES, ('arc1', 'accent2', 'horizon', 'accent3'))):
            h = (r.height() - 18) * min(1.0, s[n] / mx)
            x = r.left() + i * w + w * 0.15
            p.fillRect(QRectF(x, r.bottom() - 14 - h, w * 0.5, h), dessin.c(cle, 0.8))
            dessin.texte(p, x + w * 0.25, r.bottom() - 4, n, 'texte')
            dm = 'Δm = %s%s' % ('+' if m[n] >= m0[n] else '', nombre(m[n] - m0[n], 2))
            # à côté de la barre s'il y a la place, sinon au-dessus
            if p.fontMetrics().horizontalAdvance(dm) < w * 0.5 - 8:
                dessin.texte(p, x + w * 0.5 + 6, r.bottom() - 20, dm, 'doux', centre=False)
            else:
                dessin.texte(p, x + w * 0.25, max(r.top() + 8, r.bottom() - 22 - h), dm, 'doux')
