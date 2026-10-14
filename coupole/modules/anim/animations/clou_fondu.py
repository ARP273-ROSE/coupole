"""Blackbody Curves of Melting : un clou chauffé jusqu'à la fusion puis refroidi.  Sa lumière est celle d'un corps
noir : loi de Planck, maximum à λ_max = b / T (loi de Wien), puissance σ T⁴.  L'original montrait un film ; ici le
clou est dessiné à la couleur et à l'éclat que donnent la loi de Planck et la vision humaine (fonctions
colorimétriques CIE) : invisible sous ≈ 800 K (point de Draper), rouge sombre puis orangé vers la fusion du fer
(1 811 K ; l'original montait à 1 800 K)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPolygonF

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre
from ..graphe import Axes
from .gravitation import scientifique

T_FROID, T_FUSION = 300.0, 1811.0          # ambiante ; fusion du fer pur
DUREE_S = 24.0                             # un cycle chauffe + refroidissement à vitesse 1


def temperature_du_cycle(f: float) -> float:
    """Température au moment f ∈ [0, 1] du cycle : chauffe régulière jusqu'à la fusion (60 %), puis
    refroidissement (loi exponentielle, comme un objet qui rayonne vers une pièce à 300 K)."""
    f = max(0.0, min(1.0, f))
    if f <= 0.6:
        return T_FROID + (T_FUSION - T_FROID) * f / 0.6
    return T_FROID + (T_FUSION - T_FROID) * math.exp(-(f - 0.6) / 0.08)


def fraction_visible(t: float) -> float:
    """Part de la puissance rayonnée entre 380 et 750 nm : π ∫ B_λ dλ / σ T⁴ (somme au pas de 1 nm)."""
    s = sum(lumiere.planck((380 + k + 0.5) * 1e-9, t) for k in range(370)) * 1e-9
    return math.pi * s / lumiere.exitance(t)


class ClouFondu(Animation):
    ID = 'meltednail'

    def construire(self):
        self.t = self.curseur('temperature', T_FROID, 2000.0, T_FROID, dec=0, unite='K')
        self.c_echelle = self.coche('echelle_fixe', True)
        self.f = 0.0
        self._y1800 = lumiere.xyz(lambda w: lumiere.planck(w * 1e-9, T_FUSION))[1]

    def etat_initial(self):
        self.f = 0.0

    def avancer(self, dt):
        self.f += dt / DUREE_S
        if self.f >= 1.0:
            self.f = 0.0
        self.t.setValue(temperature_du_cycle(self.f))

    def couleur_clou(self, t: float) -> QColor:
        """Lueur du clou : teinte du corps noir, éclat ∝ luminance Y relative à celle de la fusion."""
        base = dessin.c('grille')
        if t < 650:
            return base
        x, y, z = lumiere.xyz(lambda w: lumiere.planck(w * 1e-9, t))
        k = min(1.0, y / self._y1800)
        r, g, b = lumiere.rgb_de_xyz(x / self._y1800, y / self._y1800, z / self._y1800)
        a = min(1.0, k ** 0.35)
        return QColor(int(base.red() * (1 - a) + r * a), int(base.green() * (1 - a) + g * a),
                      int(base.blue() * (1 - a) + b * a))

    def valeurs(self):
        t = self.t.value()
        fv = 100 * fraction_visible(t)
        return [(tr('anim_meltednail_temperature_v'), '%s K (%s °C)' % (nombre(t, 0), nombre(t - 273.15, 0))),
                (tr('anim_c_pic_wien'), '%s nm' % nombre(lumiere.pic_wien_m(t) * 1e9, 0)),
                (tr('anim_c_exitance'), '%s W/m²' % scientifique(lumiere.exitance(t))),
                (tr('anim_meltednail_visible'), '%s %%' % (scientifique(fv) if fv < 0.01 else nombre(fv, 2)))]

    def dessiner(self, p, rect):
        t = self.t.value()
        z = dessin.zones(rect, 2, 0.9)
        self._clou(p, dessin.cadre(p, z[0], tr('anim_meltednail_titre_clou')), t)
        r = dessin.cadre(p, z[1], tr('anim_meltednail_titre_courbe'))
        lmax = 5000.0
        bmax = lumiere.planck(lumiere.pic_wien_m(T_FUSION), T_FUSION) if self.c_echelle.isChecked() else \
            lumiere.planck(lumiere.pic_wien_m(t), t)
        ax = Axes(r, 0, lmax, 0, bmax * 1.08 / 1e12).avec(p)
        ax.bande_visible(0.22)
        ax.fond(p, tr('anim_c_lambda_nm'), tr('anim_c_luminance_unite'))
        pts = [(lam, lumiere.planck(lam * 1e-9, t) / 1e12) for lam in range(50, int(lmax) + 1, 25)]
        ax.remplir(pts, 'accent1', 0.18)
        ax.courbe(pts, 'accent1', 2.2)
        lp = lumiere.pic_wien_m(t) * 1e9
        if lp < lmax:
            ax.verticale(lp, 'accent3', etiquette='%s nm' % nombre(lp, 0))

    def _clou(self, p, r, t):
        cx, cy = r.center().x(), r.center().y()
        L = min(r.width() * 0.8, r.height() * 1.6)
        e = L * 0.06
        col = self.couleur_clou(t)
        if t > 900:                                              # halo
            for k, a in ((3.2, 0.10), (2.2, 0.16)):
                halo = QColor(col)
                halo.setAlphaF(a * min(1.0, (t - 900) / 700))
                p.setPen(dessin.Qt.PenStyle.NoPen)
                p.setBrush(halo)
                p.drawRoundedRect(QRectF(cx - L / 2 - k * e, cy - k * e, L + 2 * k * e, 2 * k * e), k * e, k * e)
        x0 = cx - L / 2
        poly = QPolygonF([QPointF(x0 + L * 0.08, cy - e / 2), QPointF(x0 + L * 0.88, cy - e / 2),
                          QPointF(x0 + L, cy), QPointF(x0 + L * 0.88, cy + e / 2), QPointF(x0 + L * 0.08, cy + e / 2)])
        p.setPen(dessin.stylo('doux', 1.0))
        p.setBrush(col)
        p.drawPolygon(poly)
        p.drawRoundedRect(QRectF(x0, cy - e * 2.2, L * 0.08, e * 4.4), 3, 3)
        dessin.texte(p, cx, cy + e * 4.5, '%s K' % nombre(t, 0), 'texte')
        if t < 800:
            dessin.texte(p, cx, cy + e * 4.5 + 18, tr('anim_meltednail_invisible'), 'doux')
        elif t >= T_FUSION - 1:
            dessin.texte(p, cx, cy + e * 4.5 + 18, tr('anim_meltednail_fusion'), 'accent3')
