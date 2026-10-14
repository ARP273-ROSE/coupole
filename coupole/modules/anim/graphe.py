"""Petit traceur de graphes pour les animations (QPainter) : axes linéaires ou logarithmiques, graduations,
courbes, points, bandes.  Tout est calculé à la volée (quelques centaines de points : rapide)."""
from __future__ import annotations

import math

import functools

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPolygonF

from . import dessin
from .base import nombre


def pas_lisible(etendue: float, n: int = 5) -> float:
    """Pas de graduation « rond » (1, 2, 5 × 10ᵏ) donnant environ n graduations."""
    if etendue <= 0:
        return 1.0
    brut = etendue / n
    e = math.floor(math.log10(brut))
    for m in (1, 2, 5, 10):
        if m * 10 ** e >= brut:
            return m * 10 ** e
    return 10 ** (e + 1)


class Axes:
    """Rectangle de tracé : x0..x1, y0..y1 en coordonnées de données (logarithmiques si demandé)."""

    def __init__(self, rect: QRectF, x0: float, x1: float, y0: float, y1: float, xlog: bool = False,
                 ylog: bool = False, marges=(46, 12, 14, 30)):
        g, h, d, b = marges
        self.cadre = QRectF(rect)
        self.r = QRectF(rect.x() + g, rect.y() + h, max(10.0, rect.width() - g - d), max(10.0, rect.height() - h - b))
        self.x0, self.x1, self.y0, self.y1, self.xlog, self.ylog = x0, x1, y0, y1, xlog, ylog

    def _t(self, v, a, b, log):
        if log:
            v = max(v, 1e-300)
            return (math.log10(v) - math.log10(a)) / (math.log10(b) - math.log10(a))
        return (v - a) / (b - a) if b != a else 0.0

    def px(self, x: float) -> float:
        return self.r.left() + self.r.width() * self._t(x, self.x0, self.x1, self.xlog)

    def py(self, y: float) -> float:
        return self.r.bottom() - self.r.height() * self._t(y, self.y0, self.y1, self.ylog)

    def pt(self, x: float, y: float) -> QPointF:
        return QPointF(self.px(x), self.py(y))

    def x_de_px(self, X: float) -> float:
        t = (X - self.r.left()) / self.r.width()
        if self.xlog:
            return 10 ** (math.log10(self.x0) + t * (math.log10(self.x1) - math.log10(self.x0)))
        return self.x0 + t * (self.x1 - self.x0)

    def y_de_px(self, Y: float) -> float:
        t = (self.r.bottom() - Y) / self.r.height()
        if self.ylog:
            return 10 ** (math.log10(self.y0) + t * (math.log10(self.y1) - math.log10(self.y0)))
        return self.y0 + t * (self.y1 - self.y0)

    # ------------------------------------------------------------ dessin
    def fond(self, p, titre_x: str = '', titre_y: str = '', grille: bool = True, dec_x=None, dec_y=None,
             fmt_x=None, fmt_y=None, n_x: int = 6, n_y: int = 5):
        p.save()
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.c('sphere', 0.15))
        p.drawRect(self.r)
        dessin.police(p, 0.85)
        gx = self._graduations(self.x0, self.x1, self.xlog, n_x)
        gy = self._graduations(self.y0, self.y1, self.ylog, n_y)
        if grille:
            p.setPen(dessin.stylo('grille', 0.6, 0.5))
            p.setRenderHint(p.RenderHint.Antialiasing, False)
            p.drawLines([QLineF(self.px(v), self.r.top(), self.px(v), self.r.bottom()) for v in gx] +
                        [QLineF(self.r.left(), self.py(v), self.r.right(), self.py(v)) for v in gy])
            p.setRenderHint(p.RenderHint.Antialiasing, True)
        for v in gx:
            X = self.px(v)
            dessin.texte(p, X, self.r.bottom() + 11, fmt_x(v) if fmt_x else self._etiq(v, self.xlog, dec_x), 'doux')
        for v in gy:
            Y = self.py(v)
            s = fmt_y(v) if fmt_y else self._etiq(v, self.ylog, dec_y)
            fm = p.fontMetrics()
            dessin.texte(p, self.r.left() - 4 - fm.horizontalAdvance(s), Y + fm.ascent() / 2 - 1, s, 'doux',
                         centre=False)
        if titre_x:
            dessin.texte(p, self.r.center().x(), self.r.bottom() + 24, titre_x, 'doux')
        if titre_y:
            p.save()
            p.translate(self.cadre.x() + 9, self.r.center().y())
            p.rotate(-90)
            dessin.texte(p, 0, 0, titre_y, 'doux')
            p.restore()
        dessin.police(p, 1 / 0.85)
        p.restore()

    @staticmethod
    def _graduations(a, b, log, n):
        lo, hi = min(a, b), max(a, b)
        if log:
            out = []
            for k in range(math.floor(math.log10(lo)), math.ceil(math.log10(hi)) + 1):
                v = 10.0 ** k
                if lo * 0.999 <= v <= hi * 1.001:
                    out.append(v)
            if len(out) <= 2:
                for k in range(math.floor(math.log10(lo)), math.ceil(math.log10(hi)) + 1):
                    for m in (2, 5):
                        v = m * 10.0 ** k
                        if lo * 0.999 <= v <= hi * 1.001:
                            out.append(v)
            return sorted(out)
        s = pas_lisible(hi - lo, n)
        v = math.ceil(lo / s - 1e-9) * s
        out = []
        while v <= hi + 1e-9 * s:
            out.append(0.0 if abs(v) < 1e-12 * s else v)
            v += s
        return out

    @staticmethod
    def _etiq(v, log, dec):
        if log:
            if v >= 1e5 or v < 1e-3:
                e = int(round(math.log10(v)))
                m = v / 10 ** e
                exp = str(e).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))
                return ('10%s' % exp) if abs(m - 1) < 1e-6 else ('%s×10%s' % (nombre(m, 0), exp))
            d = 0 if v >= 1 else int(math.ceil(-math.log10(v)))
            return nombre(v, d)
        if dec is None:
            dec = 0 if abs(v) >= 10 or v == int(v) else (1 if abs(v) >= 1 else 2)
        return nombre(v, dec)

    def polygone(self, pts) -> QPolygonF:
        """Points (x, y) de données → QPolygonF en pixels (conversion directe, sans appel par point)."""
        r = self.r
        if self.xlog:
            lx0, lx1 = math.log10(self.x0), math.log10(self.x1)
            fx = lambda x: r.left() + r.width() * (math.log10(max(x, 1e-300)) - lx0) / (lx1 - lx0)
        else:
            ax_, bx = r.width() / (self.x1 - self.x0), r.left() - r.width() * self.x0 / (self.x1 - self.x0)
            fx = lambda x: ax_ * x + bx
        if self.ylog:
            ly0, ly1 = math.log10(self.y0), math.log10(self.y1)
            fy = lambda y: r.bottom() - r.height() * (math.log10(max(y, 1e-300)) - ly0) / (ly1 - ly0)
        else:
            ay, by = -r.height() / (self.y1 - self.y0), r.bottom() + r.height() * self.y0 / (self.y1 - self.y0)
            fy = lambda y: ay * y + by
        if not self.xlog and not self.ylog and len(pts) > 32:
            # grandes séries : conversion vectorielle numpy, copie directe dans le polygone
            import numpy as np
            a = np.asarray(pts, dtype=float).reshape(-1, 2)
            a = a[np.isfinite(a[:, 1])]
            return dessin.polygone(ax_ * a[:, 0] + bx, ay * a[:, 1] + by)
        return QPolygonF([QPointF(fx(x), fy(y)) for x, y in pts if math.isfinite(y)])

    def courbe(self, pts, cle='accent1', epaisseur: float = 2.0, alpha: float = 1.0, pointille: bool = False,
               couper: bool = True):
        poly = self.polygone(pts)
        p = self._p
        p.save()
        if couper:
            p.setClipRect(self.r.adjusted(-1, -1, 1, 1))
        p.setPen(dessin.stylo(cle, epaisseur, alpha, pointille))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolyline(poly)
        p.restore()

    def remplir(self, pts, couleur, alpha: float = 0.3, base: float | None = None):
        b = self.y0 if base is None else base
        pts = [(x, y) for x, y in pts if math.isfinite(y)]
        if not pts:
            return
        poly = self.polygone([(pts[0][0], b)] + pts + [(pts[-1][0], b)])
        p = self._p
        p.save()
        p.setClipRect(self.r)
        p.setPen(Qt.PenStyle.NoPen)
        col = dessin.c(couleur, alpha) if isinstance(couleur, str) else QColor(couleur)
        if not isinstance(couleur, str):
            col.setAlphaF(alpha)
        p.setBrush(col)
        p.drawPolygon(poly)
        p.restore()

    def points(self, pts, cle='texte', rayon: float = 1.6, alpha: float = 0.8):
        p = self._p
        p.save()
        p.setClipRect(self.r)
        p.setPen(Qt.PenStyle.NoPen)
        col = dessin.c(cle, alpha) if isinstance(cle, str) else cle
        p.setBrush(col)
        for x, y in pts:
            p.drawEllipse(self.pt(x, y), rayon, rayon)
        p.restore()

    def verticale(self, x, cle='accent3', epaisseur: float = 1.2, pointille: bool = True, etiquette: str = ''):
        p = self._p
        X = self.px(x)
        if not (self.r.left() - 1 <= X <= self.r.right() + 1):
            return
        p.setPen(dessin.stylo(cle, epaisseur, None, pointille))
        p.drawLine(QPointF(X, self.r.top()), QPointF(X, self.r.bottom()))
        if etiquette:
            dessin.texte(p, X, self.r.top() + 10, etiquette, cle, fond=True)

    def horizontale(self, y, cle='accent3', epaisseur: float = 1.2, pointille: bool = True, etiquette: str = ''):
        p = self._p
        Y = self.py(y)
        if not (self.r.top() - 1 <= Y <= self.r.bottom() + 1):
            return
        p.setPen(dessin.stylo(cle, epaisseur, None, pointille))
        p.drawLine(QPointF(self.r.left(), Y), QPointF(self.r.right(), Y))
        if etiquette:
            dessin.texte(p, self.r.right() - 4 - p.fontMetrics().horizontalAdvance(etiquette), Y - 9, etiquette,
                         cle, centre=False, fond=True)

    def bande_visible(self, alpha: float = 0.22, lam0: float = 380.0, lam1: float = 750.0, echelle: float = 1.0):
        """Bande colorée du spectre visible (axe x en nm × echelle) : un seul dégradé, rapide."""
        p = self._p
        x0, x1 = self.px(lam0 * echelle), self.px(lam1 * echelle)
        if x1 < self.r.left() or x0 > self.r.right():
            return
        p.save()
        p.setClipRect(self.r)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(degrade_spectre(x0, x1, self.r.top(), alpha, lam0, lam1))
        p.drawRect(QRectF(x0, self.r.top(), x1 - x0, self.r.height()))
        p.restore()

    def avec(self, p):
        """Associe le QPainter (à appeler avant les tracés) ; rend self."""
        self._p = p
        return self


@functools.lru_cache(maxsize=64)
def _arrets(alpha: float, lam0: float, lam1: float, pas_nm: float):
    from .lumiere import couleur_longueur_onde
    n = max(2, int((lam1 - lam0) / pas_nm))
    out = []
    for k in range(n + 1):
        col = QColor(*couleur_longueur_onde(lam0 + (lam1 - lam0) * k / n))
        col.setAlphaF(alpha)
        out.append((k / n, col))
    return tuple(out)


def degrade_spectre(x0: float, x1: float, y: float, alpha: float = 1.0, lam0: float = 380.0, lam1: float = 750.0,
                    intensite=None, pas_nm: float = 5.0) -> QLinearGradient:
    """Dégradé horizontal des couleurs du spectre de lam0 à lam1 (nm) entre les abscisses x0 et x1."""
    g = QLinearGradient(QPointF(x0, y), QPointF(x1, y))
    if intensite is None:
        g.setStops(list(_arrets(round(alpha, 3), lam0, lam1, pas_nm)))
        return g
    from .lumiere import couleur_longueur_onde
    n = max(2, int((lam1 - lam0) / pas_nm))
    for k in range(n + 1):
        lam = lam0 + (lam1 - lam0) * k / n
        r, gg, b = couleur_longueur_onde(lam)
        f = max(0.0, min(1.0, intensite(lam)))
        col = QColor(int(r * f), int(gg * f), int(b * f))
        col.setAlphaF(alpha)
        g.setColorAt(k / n, col)
    return g


def bande_spectre(p, r: QRectF, lam0: float, lam1: float, intensite=None, raies=(), raies_absorption: bool = False,
                  pas_px: float = 4.0):
    """Bande d'un spectre visible de lam0 à lam1 nm dans le rectangle r : continuum coloré (intensite(λ) ∈ [0, 1],
    None : fond noir), raies (λ, force 0–1, épaisseur px) brillantes ou sombres."""
    from .lumiere import couleur_longueur_onde
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.fillRect(r, QColor(8, 8, 10))
    if intensite is not None:
        p.fillRect(r, degrade_spectre(r.left(), r.right(), r.top(), 1.0, lam0, lam1, intensite, pas_nm=pas_px))
    for lam, force, ep in raies:
        if lam0 <= lam <= lam1:
            X = r.left() + r.width() * (lam - lam0) / (lam1 - lam0)
            if raies_absorption:
                col = QColor(0, 0, 0)
                col.setAlphaF(max(0.0, min(1.0, force)))
            else:
                rr, gg, bb = couleur_longueur_onde(lam)
                col = QColor(rr, gg, bb)
                col.setAlphaF(max(0.0, min(1.0, force)))
            p.fillRect(QRectF(X - ep / 2, r.top(), ep, r.height()), col)
    p.setPen(dessin.stylo('grille', 1.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(r)
    p.restore()
