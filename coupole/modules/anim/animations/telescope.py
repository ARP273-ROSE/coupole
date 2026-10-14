"""Telescope Simulator : une lunette (objectif de 4, 6 ou 8 pouces, focales de l'original) et trois oculaires
(40, 20, 10 mm).  Grossissement G = F / f, champ réel = champ apparent de l'oculaire / G, pouvoir séparateur
1,22 λ / D (critère de Rayleigh à 550 nm ; Dawes : 116″ / D en mm, l'original 4,5″ / D en pouces), pouvoir
collecteur (D / 7 mm)² par rapport à l'œil.  Mise au point : un oculaire décalé de Δ étale chaque point en un disque
de Δ D / F (géométrie exacte).  Objets à leur vraie taille angulaire : la Lune (31′), Saturne (globe 17″, anneaux
40″ à 9,5 ua), un amas globulaire (≈ 20′)."""
from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainterPath, QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre

# objectif : (diamètre mm, focale mm) — 8, 6 et 4 pouces de l'original
OBJECTIFS = {'8': (203.2, 1400.0), '6': (152.4, 1220.0), '4': (101.6, 1020.0)}
# oculaire : (focale mm, champ apparent en degrés, déduit des champs réels de l'original)
OCULAIRES = {'40': (40.0, 44.0), '20': (20.0, 52.0), '10': (10.0, 59.0)}
PUPILLE_MM = 7.0
LAMBDA_M = 550e-9
LUNE_DEG = math.degrees(2 * astro.R_LUNE_KM / astro.D_LUNE_KM)
SATURNE_GLOBE_ARCSEC = 2 * 60_268.0 / (9.5 * astro.UA_KM) * astro.SECONDES_D_ARC_PAR_RADIAN
SATURNE_ANNEAUX_ARCSEC = 2 * 136_775.0 / (9.5 * astro.UA_KM) * astro.SECONDES_D_ARC_PAR_RADIAN
AMAS_DEG = 20.0 / 60.0
OEIL_ARCMIN = 1.0                     # pouvoir séparateur de l'œil, environ 1′


def optique(objectif: str, oculaire: str) -> dict:
    d, f = OBJECTIFS[objectif]
    fe, champ = OCULAIRES[oculaire]
    g = f / fe
    return {'D': d, 'F': f, 'fe': fe, 'G': g, 'champ_reel': champ / g, 'champ_apparent': champ,
            'rayleigh': 1.22 * LAMBDA_M / (d / 1000) * astro.SECONDES_D_ARC_PAR_RADIAN, 'dawes': 116.0 / d,
            'collecteur': (d / PUPILLE_MM) ** 2}


def flou_apparent_deg(delta_mm: float, o: dict) -> float:
    """Diamètre apparent (degrés, dans l'oculaire) du disque de flou d'une mise au point décalée de delta_mm."""
    return math.degrees(abs(delta_mm) * o['D'] / o['F'] / o['fe'])


class Telescope(Animation):
    ID = 'telescope10'
    ANIMEE = False

    def construire(self):
        self.objet = self.choix('objet', [('anim_telescope10_o_lune', 'lune'), ('anim_telescope10_o_saturne', 'saturne'),
                                          ('anim_telescope10_o_amas', 'amas')], 'lune')
        self.objectif = self.choix('objectif', [('anim_telescope10_d_' + k, k) for k in OBJECTIFS], '8')
        self.oculaire = self.choix('oculaire', [('anim_telescope10_e_' + k, k) for k in OCULAIRES], '40')
        self.mise_au_point = self.curseur('mise_au_point', -3.0, 3.0, 1.0, dec=2, unite='mm')
        alea = random.Random(13)
        self.etoiles = []
        for _ in range(260):
            r = AMAS_DEG / 2 * min(1.0, abs(alea.gauss(0, 0.35)))
            a = alea.uniform(0, 2 * math.pi)
            self.etoiles.append((r * math.cos(a), r * math.sin(a), alea.uniform(0.4, 1.0)))
        self.crateres = [(alea.uniform(-0.8, 0.8), alea.uniform(-0.8, 0.8), alea.uniform(0.03, 0.12)) for _ in range(40)]
        self.crateres = [c for c in self.crateres if math.hypot(c[0], c[1]) + c[2] < 0.97]

    def optique(self):
        return optique(self.objectif.currentData(), self.oculaire.currentData())

    def valeurs(self):
        o = self.optique()
        return [(tr('anim_telescope10_g'), '× %s' % nombre(o['G'], 1)),
                (tr('anim_telescope10_champ'), '%s° (%s′)' % (nombre(o['champ_reel'], 2), nombre(o['champ_reel'] * 60, 0))),
                (tr('anim_telescope10_resolution'), '%s″ (Dawes %s″)' % (nombre(o['rayleigh'], 2), nombre(o['dawes'], 2))),
                (tr('anim_telescope10_collecteur'), '× %s' % nombre(o['collecteur'], 0)),
                (tr('anim_telescope10_net'), tr('anim_oui') if abs(self.mise_au_point.value()) < 0.05 else tr('anim_non'))]

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.9)
        self._schema(p, dessin.cadre(p, z[0], tr('anim_telescope10_titre_lunette')))
        self._vue(p, dessin.cadre(p, z[1], tr('anim_telescope10_titre_vue')))

    def _schema(self, p, r):
        o = self.optique()
        cy = r.center().y()
        x0, x1 = r.left() + 20, r.right() - 30
        k = (x1 - x0) / (1400.0 + 40.0)
        hd = o['D'] / 203.2 * r.height() * 0.32
        xf = x0 + o['F'] * k                                     # foyer
        xo = xf + (o['fe'] + self.mise_au_point.value() * 8) * k * 1.0
        p.setPen(dessin.stylo('doux', 1.5))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawLine(QPointF(x0, cy - hd), QPointF(xf, cy - hd * 0.35))
        p.drawLine(QPointF(x0, cy + hd), QPointF(xf, cy + hd * 0.35))
        p.setBrush(dessin.c('accent2', 0.6))
        p.drawEllipse(QRectF(x0 - 5, cy - hd, 10, 2 * hd))
        p.drawEllipse(QRectF(xo - 4, cy - hd * 0.3, 8, 0.6 * hd))
        p.setPen(dessin.stylo('soleil', 1.2, 0.8))
        for s in (-1, 1):
            p.drawLine(QPointF(x0 - 30, cy + s * hd * 0.8), QPointF(x0, cy + s * hd * 0.8))
            p.drawLine(QPointF(x0, cy + s * hd * 0.8), QPointF(xf, cy))
            p.drawLine(QPointF(xf, cy), QPointF(xo, cy - s * hd * 0.8 * (xo - xf) / (xf - x0)))
        dessin.texte(p, x0 - 4, cy + hd + 16, 'D = %s mm, F = %s mm' % (nombre(o['D'], 1), nombre(o['F'], 0)), 'doux',
                     centre=False)
        s = 'f = %s mm' % nombre(o['fe'], 0)
        dessin.texte(p, min(xo, r.right() - 4 - p.fontMetrics().horizontalAdvance(s) / 2), cy + hd * 0.3 + 16, s, 'doux')

    def _vue(self, p, r):
        o = self.optique()
        cx, cy = r.center().x(), r.center().y()
        R = min(r.width(), r.height()) * 0.45
        px_par_deg = R / (o['champ_apparent'] / 2)               # degrés APPARENTS
        g = o['G']
        p.save()
        chemin = QPainterPath()
        chemin.addEllipse(QPointF(cx, cy), R, R)
        p.setClipPath(chemin)
        p.fillRect(r, dessin.c('nuit'))
        flou = flou_apparent_deg(self.mise_au_point.value(), o) * px_par_deg
        nettete = max(o['rayleigh'] / 3600 * g * px_par_deg, OEIL_ARCMIN / 60 * px_par_deg)
        rayon_point = max(0.8, nettete / 2 + flou / 2)
        lum = 0.35 + 0.65 * min(1.0, o['collecteur'] / 843.0)
        objet = self.objet.currentData()
        if objet == 'lune':
            rl = LUNE_DEG / 2 * g * px_par_deg
            dessin.disque(p, cx, cy, rl + flou / 2, 'lune', alpha=0.5 * lum)
            dessin.disque(p, cx, cy, rl, 'lune', alpha=lum)
            for x, y, rc in self.crateres:
                p.setPen(dessin.stylo('grille', max(0.5, 1.5 - flou / 10), 0.8))
                p.setBrush(dessin.c('doux', 0.25))
                p.drawEllipse(QPointF(cx + x * rl, cy + y * rl), rc * rl, rc * rl)
        elif objet == 'saturne':
            k = g * px_par_deg / 3600
            ra, rg = SATURNE_ANNEAUX_ARCSEC / 2 * k, SATURNE_GLOBE_ARCSEC / 2 * k
            p.setPen(dessin.stylo('accent1', max(1.0, rg * 0.15 + flou / 4), lum))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), ra, ra * 0.38)
            dessin.disque(p, cx, cy, rg + flou / 2, 'accent1', alpha=lum)
        else:
            k = g * px_par_deg
            p.setPen(dessin.Qt.PenStyle.NoPen)
            for x, y, b in self.etoiles:
                p.setBrush(dessin.c('etoile', b * lum * min(1.0, 4.0 / (rayon_point + 1))))
                p.drawEllipse(QPointF(cx + x * k, cy + y * k), rayon_point, rayon_point)
        p.restore()
        p.setPen(dessin.stylo('grille', 2.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), R, R)
        dessin.texte(p, cx, cy + R + 12, tr('anim_telescope10_champ_v', c=nombre(o['champ_reel'] * 60, 0)), 'doux')
