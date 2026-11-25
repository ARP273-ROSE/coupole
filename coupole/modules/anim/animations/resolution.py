"""Diffraction et pouvoir de résolution : l'image d'une étoile par un télescope n'est pas un point mais une tache
d'Airy (un disque entouré d'anneaux), de rayon 1,22 λ / D jusqu'au premier anneau noir.  Deux étoiles plus proches
que cela se confondent (critère de Rayleigh) ; l'obstruction centrale d'un télescope à miroir secondaire resserre
la tache mais renforce les anneaux ; à travers l'atmosphère, la turbulence (seeing) élargit l'image d'une pose
longue et, au-delà d'une dizaine de centimètres de diamètre, c'est elle qui décide de la finesse.  Calculs :
``diffraction.py`` (pupille circulaire, convolution par une gaussienne pour le seeing)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import dessin, diffraction as dif
from ..base import Animation, nombre
from ..graphe import Axes

N_IMAGE = 72                      # cases de l'image simulée (côté)


def angle_sec(x: float) -> str:
    """Angle en secondes d'arc, avec 3 chiffres significatifs (milliarcsecondes sous 0,1″)."""
    if x < 0.1:
        return '%s mas' % nombre(x * 1000.0, 1 if x * 1000 < 10 else 0)
    return '%s″' % nombre(x, 3 if x < 1 else (2 if x < 10 else 1))


def eclat(v: float, etirer: bool) -> float:
    """Éclat affiché d'une intensité v (0 à 1) ; étiré : échelle logarithmique sur trois décades (le premier anneau,
    à 1,7 % du centre, ressort à 42 %)."""
    return math.log10(1.0 + 1000.0 * max(0.0, v)) / 3.0 if etirer else v


class Resolution(Animation):
    ID = 'resolution'
    ANIMEE = False

    def construire(self):
        self.instrument = self.choix('instrument', [('anim_resolution_i_libre', 'libre')] +
                                     [('anim_resolution_i_' + k, k) for k, _, _ in dif.INSTRUMENTS], 'libre')
        self.diametre = self.curseur('diametre', 0.5, 4000.0, 20.0, dec=1, unite='cm', log=True)
        self.obstruction = self.curseur('obstruction', 0.0, 0.6, 0.0, dec=2)
        self.lam = self.curseur('lambda', 350.0, 2200.0, 550.0, dec=0, unite='nm')
        self.sep = self.curseur('separation', 0.01, 20.0, 1.0, dec=3, unite='″', log=True)
        self.dmag = self.curseur('dmag', 0.0, 5.0, 0.0, dec=1)
        self.seeing = self.curseur('seeing', 0.0, 3.0, 0.0, dec=2, unite='″')
        self.c_etirer = self.coche('etirer', True)
        self.c_anneau = self.coche('anneau', True)
        self._applique = self.instrument.currentData()
        self._cache = None

    def reglage_change(self):
        k = self.instrument.currentData()
        if k != getattr(self, '_applique', k):
            self._applique = k
            for cle, d, e in dif.INSTRUMENTS:
                if cle == k:
                    self.diametre.setValue(d * 100.0)
                    self.obstruction.setValue(e)
        super().reglage_change()

    # ------------------------------------------------------------ calculs
    def parametres(self):
        return (self.diametre.value() / 100.0, self.lam.value(), self.obstruction.value(), self.seeing.value())

    def profil(self) -> dif.Profil:
        cle = self.parametres()
        if self._cache is None or self._cache[0] != cle:
            d, lam, eps, s = cle
            self._cache = (cle, dif.Profil(d, lam, eps, s))
        return self._cache[1]

    def valeurs(self):
        d, lam, eps, s = self.parametres()
        pr = self.profil()
        sep = self.sep.value()
        rapport = 10 ** (-0.4 * self.dmag.value())
        cp = dif.coupe(pr, sep, rapport)
        theta = dif.rayleigh_arcsec(d, lam)
        out = [(tr('anim_resolution_v_rayleigh'), angle_sec(theta)),
               (tr('anim_resolution_v_anneau'), angle_sec(pr.t1)),
               (tr('anim_resolution_v_fwhm'), angle_sec(dif.largeur_mi_hauteur(pr))),
               (tr('anim_resolution_v_rapport'), nombre(sep / theta, 2)),
               (tr('anim_resolution_v_creux'), ('%s %% %s' % (nombre(cp['creux'], 0), tr('anim_resolution_du_sommet'))) if cp['creux'] is not None
                else tr('anim_resolution_aucun_creux')),
               (tr('anim_resolution_v_verdict'), tr('anim_resolution_' + dif.verdict(sep, d, lam, s)))]
        if s > 0:
            out.append((tr('anim_resolution_v_dturb'), '%s cm' % nombre(100.0 * dif.diametre_turbulence(s, lam), 1)))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.75)
        self._image(p, dessin.cadre(p, z[0], tr('anim_resolution_t_image')))
        self._coupe(p, dessin.cadre(p, z[1], tr('anim_resolution_t_coupe')))

    def _image(self, p, r):
        pr = self.profil()
        sep = self.sep.value()
        rapport = 10 ** (-0.4 * self.dmag.value())
        demi = dif.coupe(pr, sep, rapport, n=3)['demi']
        cote = max(10.0, min(r.width(), r.height() - 26))
        x0, y0 = r.center().x() - cote / 2, r.y() + (r.height() - 26 - cote) / 2
        p.save()
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0))
        p.drawRect(QRectF(x0, y0, cote, cote))
        n = N_IMAGE
        h = cote / n
        vals = []
        for j in range(n):
            y = (j + 0.5 - n / 2) * 2.0 * demi / n
            for i in range(n):
                x = (i + 0.5 - n / 2) * 2.0 * demi / n
                v = pr.valeur(math.hypot(x + sep / 2, y)) + rapport * pr.valeur(math.hypot(x - sep / 2, y))
                vals.append(v)
        m = max(vals) or 1.0
        etirer = self.c_etirer.isChecked()
        p.setRenderHint(p.RenderHint.Antialiasing, False)       # cases jointives, sans liseré
        bords = [math.floor(x0 + i * h) for i in range(n + 1)]
        hauts = [math.floor(y0 + j * h) for j in range(n + 1)]
        for j in range(n):
            for i in range(n):
                v = eclat(vals[j * n + i] / m, etirer)
                if v > 0.004:
                    p.setBrush(QColor(255, 246, 225, max(0, min(255, int(255 * v)))))
                    p.drawRect(QRectF(bords[i], hauts[j], bords[i + 1] - bords[i], hauts[j + 1] - hauts[j]))
        p.setRenderHint(p.RenderHint.Antialiasing, True)
        k = cote / (2.0 * demi)
        cx, cy = x0 + cote / 2, y0 + cote / 2
        if self.c_anneau.isChecked():
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.setPen(dessin.stylo('accent2', 1.0, 0.8, pointille=True))
            for sx in (-sep / 2, sep / 2):
                if abs(sx) * k < cote:
                    p.drawEllipse(QPointF(cx + sx * k, cy), pr.t1 * k, pr.t1 * k)
        p.restore()
        # barre d'échelle : 1-2-5 × 10ⁿ, environ un quart du champ
        cible = demi / 2
        e = 10 ** math.floor(math.log10(cible))
        lg = max(m_ for m_ in (e, 2 * e, 5 * e) if m_ <= cible)
        yb = y0 + cote + 12
        p.setPen(dessin.stylo('texte', 2.0))
        p.drawLine(QPointF(x0, yb), QPointF(x0 + lg * k, yb))
        dessin.texte(p, x0 + lg * k + 8, yb + 4, angle_sec(lg), 'doux', centre=False)

    def _coupe(self, p, r):
        pr = self.profil()
        sep = self.sep.value()
        rapport = 10 ** (-0.4 * self.dmag.value())
        cp = dif.coupe(pr, sep, rapport)
        ymax = max(1.05, 1.08 * max(cp['somme']))
        ax = Axes(r, -cp['demi'], cp['demi'], 0.0, ymax, marges=(40, 6, 10, 30)).avec(p)
        ax.fond(p, tr('anim_resolution_axe_x'), tr('anim_resolution_axe_y'), fmt_x=lambda v: nombre(v, 2))
        xs = cp['x']
        ax.courbe(list(zip(xs, cp['a'])), 'accent2', 1.3, 0.85, pointille=True)
        ax.courbe(list(zip(xs, cp['b'])), 'accent3', 1.3, 0.85, pointille=True)
        ax.courbe(list(zip(xs, cp['somme'])), 'accent1', 2.2)
        theta = dif.rayleigh_arcsec(*self.parametres()[:2])
        for sx in (-theta / 2, theta / 2):
            if abs(sx) < cp['demi']:
                ax.verticale(sx, 'doux', 1.0)
        dessin.texte(p, ax.px(0.0), ax.r.top() + 10, tr('anim_resolution_rayleigh_ecart'), 'doux', fond=True)
