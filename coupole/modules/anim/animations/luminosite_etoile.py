"""Stellar Luminosity Calculator : la luminosité d'une étoile d'après son rayon et sa température.  Loi de
Stefan-Boltzmann L = 4π R² σ T⁴, soit L / L☉ = (R / R☉)² (T / T☉)⁴ ; température tirée du type spectral (table de
l'original, séquence principale).  Constantes de l'UAI : R☉ = 695 700 km, L☉ = 3,828 × 10²⁶ W, T☉ = 5 772 K
(l'original prenait 5 830 K)."""
from __future__ import annotations

import math

from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import dessin, hr
from ..base import Animation, nombre
from .gravitation import scientifique


class LuminositeEtoile(Animation):
    ID = 'stellarlum'
    ANIMEE = False

    def construire(self):
        self.r = self.curseur('rayon', 0.01, 100.0, 1.0, dec=2, unite='R☉', log=True)
        self.sp = self.curseur('type', 7.0, 66.0, 42.0, dec=1)

    def grandeurs(self) -> dict:
        r, t = self.r.value(), hr.temperature_de_type(self.sp.value())
        return {'r': r, 't': t, 'l': hr.luminosite_solaire(r, t), 'w': hr.puissance_w(r * hr.R_SOLEIL_M, t)}

    def valeurs(self):
        g = self.grandeurs()
        return [(tr('anim_stellarlum_type_v'), hr.nom_type(self.sp.value())),
                (tr('anim_stellarlum_temperature'), '%s K (%s T☉)' % (nombre(g['t'], 0), nombre(g['t'] / hr.T_SOLEIL, 2))),
                (tr('anim_stellarlum_rayon_m'), '%s m' % scientifique(g['r'] * hr.R_SOLEIL_M)),
                (tr('anim_stellarlum_lum'), '%s L☉ = %s W' % (scientifique(g['l']), scientifique(g['w'])))]

    def dessiner(self, p, rect):
        g = self.grandeurs()
        cx, cy = rect.center().x() - rect.width() * 0.12, rect.center().y()
        rmax = min(rect.width() * 0.32, rect.height() * 0.42)
        # diamètre à l'échelle logarithmique (de 0,01 à 100 R☉), le Soleil en repère
        def taille(r):
            return 4 + (rmax - 4) * (math.log10(r) + 2) / 4

        couleur = QColor(*hr.couleur_rvb(g['t']))
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(couleur)
        p.drawEllipse(dessin.QPointF(cx, cy), taille(g['r']), taille(g['r']))
        sx = rect.right() - rect.width() * 0.14
        dessin.disque(p, sx, cy, taille(1.0), QColor(*hr.couleur_rvb(hr.T_SOLEIL)))
        dessin.texte(p, sx, cy + taille(1.0) + 14, tr('anim_stellarlum_soleil'), 'doux')
        dessin.police(p, 1.15)
        y = rect.bottom() - 52
        dessin.texte(p, rect.center().x(), y, 'L / L☉ = (R / R☉)² (T / T☉)⁴ = (%s)² × (%s)⁴ = %s'
                     % (nombre(g['r'], 2), nombre(g['t'] / hr.T_SOLEIL, 3), scientifique(g['l'])))
        dessin.police(p, 1 / 1.15)
        dessin.texte(p, rect.center().x(), y + 24, 'L = 4π R² σ T⁴ = %s W' % scientifique(g['w']), 'doux')
        dessin.texte(p, rect.x() + 10, rect.y() + 16, tr('anim_stellarlum_echelle'), 'doux', centre=False)
