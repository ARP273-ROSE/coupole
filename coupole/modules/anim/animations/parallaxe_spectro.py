"""Spectroscopic Parallax Simulator : la distance d'une étoile sans mesurer sa parallaxe.  Le spectre donne le type
spectral (raies de l'hélium, de l'hydrogène, des métaux, des molécules) et la classe de luminosité ; le diagramme HR
donne alors la luminosité, donc la magnitude absolue M ; avec la magnitude apparente m, le module de distance donne
d = 10^((m − M + 5) / 5) parsecs.  Étalonnages du diagramme et intensités des raies : ceux de l'original ;
magnitude bolométrique du Soleil 4,74 et facteur 2,5 de Pogson (exacts)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPolygonF

from ....core.i18n import tr
from .. import astro, dessin, hr
from ..base import Animation, nombre

LOG_T = (3.3617, 4.6021)
LOG_L = (-4.0, 6.0)
CLASSES = (('I', 1), ('II', 2), ('III', 3), ('IV', 4), ('V', 5))
# raies de chaque famille (nm), comme l'original
RAIES = {'he_ii': (433.9, 454.2, 468.6), 'he_i': (402.6, 438.8, 447.1, 706.5), 'h': (397.0, 410.1, 434.0, 486.1, 656.3),
         'metaux_ionises': (393.3, 396.8, 407.7, 417.5, 421.5, 423.3, 424.6, 426.7, 430.0, 444.4, 448.1),
         'metaux': (403.2, 404.5, 432.5, 422.6, 589.0), 'molecules': (421.5, 430.0, 458.4, 462.5, 467.0, 469.7, 478.0)}


def intensites(t: int) -> dict:
    """Intensité (0 à 100) des raies de chaque famille pour le type spectral numérique t (0 à 69), d'après l'original."""
    def f(cond):
        for borne, a, b in cond:
            if t < borne:
                return max(0, math.floor(a * t + b))
        return 0
    return {'he_ii': f(((8, -12.5, 100),)),
            'he_i': f(((8, 3.75, 70), (21, -7.7, 161.7))),
            'h': f(((7, 0, 0), (20, 7.7, -53.9), (54, -2.94, 158.7))),
            'metaux_ionises': f(((11, 0, 0), (38, 3.7, -40.7), (52, -7.14, 371.3))),
            'metaux': f(((30, 0, 0), (49, 5.26, -157.8), (62, -7.7, 477.4))),
            'molecules': max(0, math.floor(5.26 * t - 263.16)) if t >= 50 else 0}


def magnitude_absolue(t: float, classe: int) -> dict:
    """Température, log L et magnitude absolue visuelle d'une étoile de type t et de classe de luminosité donnés."""
    lt = hr.log_temp_de_type(t)
    ll = hr.log_lum_classe(lt, classe)
    return {'log_t': lt, 'log_l': ll, 'M': hr.mbol_de_log_lum(ll) - hr.correction_bolometrique(lt)}


def couleur_raie(lam: float) -> QColor:
    """Couleur approchée d'une longueur d'onde visible (380 à 700 nm), pour le dessin du spectre."""
    h = max(0.0, min(1.0, (700.0 - lam) / 320.0)) * 270.0
    return QColor.fromHsvF(h / 360.0, 0.75, 0.95)


class ParallaxeSpectro(Animation):
    ID = 'spectroparallax'
    ANIMEE = False

    def construire(self):
        self.sp = self.curseur('type', 0.0, 69.0, 42.0, dec=0)
        self.classe = self.choix('classe', [('anim_spectroparallax_c_' + c, n) for c, n in CLASSES], 5)
        self.m = self.curseur('m', -5.0, 15.0, 1.0, dec=2)
        self.c_emission = self.coche('emission', False)
        self._graphe = None

    def resultat(self) -> dict:
        r = magnitude_absolue(self.sp.value(), self.classe.currentData())
        r['d'] = astro.distance_du_module(self.m.value() - r['M'])
        return r

    def valeurs(self):
        r = self.resultat()
        return [(tr('anim_spectroparallax_type_c'), '%s %s' % (hr.nom_type(self.sp.value()),
                                                             dict((n, c) for c, n in CLASSES)[self.classe.currentData()])),
                (tr('anim_stellarlum_temperature'), '%s K' % nombre(10 ** r['log_t'], 0)),
                (tr('anim_spectroparallax_lum'), '%s L☉' % nombre(10 ** r['log_l'], 3 if r['log_l'] < 1 else 0)),
                (tr('anim_spectroparallax_M'), nombre(r['M'], 2)),
                (tr('anim_spectroparallax_module'), nombre(self.m.value() - r['M'], 2)),
                (tr('anim_spectroparallax_distance'), '%s pc (%s %s)' % (nombre(r['d'], 1 if r['d'] < 1000 else 0),
                                                                        nombre(r['d'] * astro.PC_EN_AL, 0),
                                                                        tr('anim_spectroparallax_al'))),
                (tr('anim_spectroparallax_raies'), self._description())]

    def _description(self) -> str:
        parts = []
        for famille, v in intensites(int(self.sp.value())).items():
            if v > 0:
                q = 'tf' if v < 20 else 'f' if v < 40 else 'm' if v < 60 else 'F' if v < 85 else 'tF'
                parts.append(tr('anim_spectroparallax_q_' + q, f=tr('anim_spectroparallax_f_' + famille)))
        return ', '.join(parts)

    def presser(self, pos, bouton):
        if self._graphe is not None and self._graphe[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        _, x0, x1 = self._graphe
        self.sp.setValue(round(max(0.0, min(69.0, 70.0 * (pos.x() - x0) / (x1 - x0)))))

    def dessiner(self, p, rect):
        haut = rect.height() * 0.70
        self._diagramme(p, dessin.cadre(p, QRectF(rect.x(), rect.y(), rect.width(), haut),
                                        tr('anim_spectroparallax_diagramme')))
        self._spectre(p, dessin.cadre(p, QRectF(rect.x(), rect.y() + haut, rect.width(), rect.height() - haut),
                                      tr('anim_spectroparallax_spectre')))

    def _diagramme(self, p, r):
        x0, x1, y0, y1 = r.x() + 40, r.right() - 8, r.y() + 4, r.bottom() - 30
        self._graphe = (QRectF(r), x0, x1)

        def xy(lt, ll):
            return QPointF(x1 - (x1 - x0) * (lt - LOG_T[0]) / (LOG_T[1] - LOG_T[0]),
                           y1 - (y1 - y0) * (ll - LOG_L[0]) / (LOG_L[1] - LOG_L[0]))

        p.setPen(dessin.stylo('grille', 1.0, 0.5))
        dessin.police(p, 0.72)
        for ll in range(-4, 7, 2):
            q = xy(LOG_T[0], ll)
            p.drawLine(QPointF(x0, q.y()), QPointF(x1, q.y()))
            dessin.texte(p, x0 - 18, q.y(), nombre(10.0 ** ll, max(0, -ll)) if ll < 3 else '10%s' % str(ll).translate(
                str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')), 'doux')
        for k, lettre in enumerate(hr.LETTRES):                       # types spectraux en abscisse
            q = xy(hr.log_temp_de_type(10 * k + 5), LOG_L[0])
            dessin.texte(p, q.x(), y1 + 12, lettre, 'doux')
        dessin.texte(p, (x0 + x1) / 2, y1 + 24, tr('anim_spectroparallax_axe_x'), 'doux')
        dessin.police(p, 1 / 0.72)
        for _, n in CLASSES:
            a, b = hr.CLASSES[n]
            pts = [xy(a + (b - a) * i / 60, hr.log_lum_classe(a + (b - a) * i / 60, n)) for i in range(61)]
            choisie = n == self.classe.currentData()
            p.setPen(dessin.stylo('accent3' if choisie else 'arc1', 2.2 if choisie else 1.0, 1.0 if choisie else 0.6))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawPolyline(QPolygonF(pts))
            dessin.texte(p, pts[0].x() - 12, pts[0].y(), dict((k2, c) for c, k2 in CLASSES)[n], 'doux')
        res = self.resultat()
        q = xy(res['log_t'], res['log_l'])
        p.setPen(dessin.stylo('accent1', 1.0, 0.7, pointille=True))
        p.drawLine(QPointF(q.x(), y0), QPointF(q.x(), y1))
        p.drawLine(QPointF(x0, q.y()), QPointF(x1, q.y()))
        dessin.disque(p, q.x(), q.y(), 6, QColor(*hr.couleur_rvb(10 ** res['log_t'])), bord='texte')

    def _spectre(self, p, r):
        x0, x1 = r.x() + 8, r.right() - 8
        y0, y1 = r.y() + 2, r.bottom() - 16

        def x_de(lam):
            return x0 + (x1 - x0) * (lam - 390.0) / (710.0 - 390.0)

        emission = self.c_emission.isChecked()
        if not emission:                                    # spectre continu, raies sombres d'absorption
            degrade = QLinearGradient(x0, 0, x1, 0)
            for k in range(9):
                degrade.setColorAt(k / 8, couleur_raie(390.0 + 320.0 * k / 8))
            p.fillRect(QRectF(x0, y0, x1 - x0, y1 - y0), QBrush(degrade))
        else:
            p.fillRect(QRectF(x0, y0, x1 - x0, y1 - y0), dessin.c('nuit'))
        for famille, v in intensites(int(self.sp.value())).items():
            if v <= 0:
                continue
            for lam in RAIES[famille]:
                if 390 <= lam <= 710:
                    c = couleur_raie(lam) if emission else QColor(0, 0, 0)
                    c.setAlphaF(min(1.0, v / 100.0))
                    p.fillRect(QRectF(x_de(lam) - 1.2, y0, 2.4, y1 - y0), c)
        dessin.police(p, 0.72)
        for lam in (400, 450, 500, 550, 600, 650, 700):
            dessin.texte(p, x_de(lam), y1 + 8, '%d nm' % lam, 'doux')
        dessin.police(p, 1 / 0.72)
