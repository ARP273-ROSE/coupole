"""Parallax Calculator : la parallaxe annuelle p est l'angle sous lequel on voit, depuis l'étoile, le rayon de
l'orbite terrestre (1 ua).  Distance d = 1 / p (d en parsecs, p en secondes d'arc) ; 1 pc = 3,2616 al.
Les trois champs se convertissent mutuellement ; le schéma exagère l'angle."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget

from ....core.i18n import langue, tr
from ....gui.outils import aide
from .. import astro, dessin
from ..base import Animation, nombre

# Parallaxes de référence (mas) : Proxima du Centaure (Gaia DR3), Sirius et Véga (nouvelle réduction d'Hipparcos)
EXEMPLES = (('proxima', 768.0665), ('sirius', 379.21), ('vega', 130.23))


def chiffres(x: float, n: int = 3) -> str:
    """n chiffres significatifs (comme Math.toSigDigits de l'original), dans la langue courante."""
    if x == 0 or not math.isfinite(x):
        return '…' if not math.isfinite(x) else '0'
    e = math.floor(math.log10(abs(x)))
    v = round(x, -e + n - 1)
    dec = max(0, n - 1 - e)
    s = '%.*f' % (dec, v)
    return s.replace('.', ',') if langue() == 'fr' else s


def lire(texte: str) -> float:
    try:
        return float(texte.strip().replace(',', '.').replace(' ', '').replace(' ', ''))
    except ValueError:
        return math.nan


class Parallaxe(Animation):
    ID = 'parallaxdiag'
    ANIMEE = False

    def construire(self):
        boite = QWidget()
        h = QHBoxLayout(boite)
        h.setContentsMargins(0, 0, 0, 0)
        self.champs = {}
        for cle in ('arcsec', 'pc', 'al'):
            lab = QLabel(tr('anim_parallaxdiag_' + cle))
            ch = QLineEdit()
            ch.setMaximumWidth(ch.fontMetrics().horizontalAdvance('0' * 14))
            aide(ch, 'anim_parallaxdiag_' + cle + '_aide')
            aide(lab, 'anim_parallaxdiag_' + cle + '_aide')
            ch.textEdited.connect(lambda texte, c=cle: self._saisi(c, texte))
            h.addWidget(lab)
            h.addWidget(ch)
            self.champs[cle] = ch
        self.flux.addWidget(boite)
        for cle, mas in EXEMPLES:
            self.bouton('anim_parallaxdiag_' + cle, lambda _=False, m=mas: self.definir_parallaxe(m / 1000.0))
        self.p = 0.5
        self.definir_parallaxe(0.5)

    def etat_initial(self):
        self.definir_parallaxe(0.5)

    def definir_parallaxe(self, p_arcsec: float):
        self.p = p_arcsec
        self._ecrire(None)
        self.rafraichir()

    def _ecrire(self, sauf):
        d = astro.parsecs_de_parallaxe(self.p) if self.p > 0 else math.inf
        valeurs = {'arcsec': self.p, 'pc': d, 'al': d * astro.PC_EN_AL}
        for cle, ch in self.champs.items():
            if cle != sauf:
                ch.setText(chiffres(valeurs[cle]))

    def _saisi(self, cle, texte):
        x = lire(texte)
        if not math.isfinite(x) or x <= 0:
            for c, ch in self.champs.items():
                if c != cle:
                    ch.setText('…')
            return
        self.p = x if cle == 'arcsec' else 1.0 / x if cle == 'pc' else astro.PC_EN_AL / x
        self._ecrire(cle)
        self.rafraichir()

    def valeurs(self):
        d = 1.0 / self.p if self.p > 0 else math.inf
        return [(tr('anim_parallaxdiag_arcsec'), chiffres(self.p, 4)), (tr('anim_parallaxdiag_pc'), chiffres(d, 4)),
                (tr('anim_parallaxdiag_al'), chiffres(d * astro.PC_EN_AL, 4)),
                (tr('anim_parallaxdiag_ua'), chiffres(d * 648000 / math.pi, 4)),
                (tr('anim_parallaxdiag_formule'), 'd = 1 / p')]

    def dessiner(self, p, rect):
        cy = rect.center().y()
        sx = rect.x() + rect.width() * 0.18
        ro = min(rect.height() * 0.32, rect.width() * 0.12)
        # Soleil, orbite terrestre, deux positions à six mois d'intervalle
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(sx, cy), ro, ro)
        dessin.disque(p, sx, cy, 8, 'soleil')
        t1, t2 = QPointF(sx, cy - ro), QPointF(sx, cy + ro)
        dessin.disque(p, t1.x(), t1.y(), 6, 'terre')
        dessin.disque(p, t2.x(), t2.y(), 6, 'terre')
        # étoile placée de façon à rendre l'angle lisible (schéma exagéré : distance ∝ log)
        dmax = rect.right() - 30 - sx
        d = 1.0 / self.p if self.p > 0 else 1e9
        frac = max(0.25, min(1.0, 0.35 + 0.22 * math.log10(max(d, 0.1))))
        ex = sx + dmax * frac
        e = QPointF(ex, cy)
        dessin.disque(p, ex, cy, 5, 'etoile', bord='soleil')
        p.setPen(dessin.stylo('accent2', 1.5))
        p.drawLine(t1, e)
        p.drawLine(t2, e)
        p.setPen(dessin.stylo('doux', 1.0, pointille=True))
        p.drawLine(QPointF(sx, cy), e)
        p.drawLine(t1, t2)
        a = math.degrees(math.atan2(ro, ex - sx))
        rr = min(80.0, (ex - sx) * 0.4)
        p.setPen(dessin.stylo('accent1', 2.0))
        p.drawArc(QRectF(ex - rr, cy - rr, 2 * rr, 2 * rr), int((180 - a) * 16), int(a * 16))
        dessin.texte(p, ex - rr - 14, cy - 12, 'p', 'accent1')
        dessin.texte(p, sx - 30, cy - ro / 2, tr('anim_parallaxdiag_une_ua'), 'doux')
        dessin.texte(p, (sx + ex) / 2, cy + 16, 'd', 'doux')
        dessin.texte(p, rect.center().x(), rect.y() + 18, tr('anim_parallaxdiag_schema'), 'doux')
