"""Tracé 1D léger (QPainter) : axes, graduations, courbe, lecture au curseur.  Sans matplotlib."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget


def graduations(a: float, b: float, n: int = 6):
    if not (math.isfinite(a) and math.isfinite(b)) or a == b:
        return [a]
    pas = (b - a) / n
    e = 10 ** math.floor(math.log10(abs(pas)))
    for m in (1, 2, 2.5, 5, 10):
        if abs(pas) <= m * e:
            pas = m * e * (1 if b > a else -1)
            break
    debut = math.ceil(a / pas) * pas
    out = []
    v = debut
    while (v <= b + 1e-12 * abs(b)) if pas > 0 else (v >= b - 1e-12 * abs(b)):
        out.append(round(v, 12))
        v += pas
        if len(out) > 50:
            break
    return out


class Trace(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.x = self.y = None
        self.titre_x = self.titre_y = ''
        self.setMouseTracking(True)
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._curseur = None
        self.format_lecture = '{x:.6g} ; {y:.6g}'

    def definir(self, x, y, titre_x='', titre_y=''):
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        ok = np.isfinite(x) & np.isfinite(y)
        ordre = np.argsort(x[ok])
        self.x, self.y = x[ok][ordre], y[ok][ordre]
        self.titre_x, self.titre_y = titre_x, titre_y
        self.update()

    def _cadre(self):
        return QRectF(70, 14, max(10, self.width() - 90), max(10, self.height() - 60))

    def _limites(self):
        x0, x1 = float(self.x.min()), float(self.x.max())
        y0, y1 = float(self.y.min()), float(self.y.max())
        if y0 == y1:
            y0, y1 = y0 - 1, y1 + 1
        m = (y1 - y0) * 0.05
        return x0, x1 if x1 > x0 else x0 + 1, y0 - m, y1 + m

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = self.palette()
        p.fillRect(self.rect(), pal.base())
        r = self._cadre()
        p.setPen(QPen(pal.text().color(), 1))
        p.drawRect(r)
        if self.x is None or len(self.x) < 2:
            p.end()
            return
        x0, x1, y0, y1 = self._limites()

        def px(v):
            return r.left() + (v - x0) / (x1 - x0) * r.width()

        def py(v):
            return r.bottom() - (v - y0) / (y1 - y0) * r.height()
        f = QFont(self.font())
        f.setPointSizeF(max(7.0, f.pointSizeF() * 0.85))
        p.setFont(f)
        grille = QPen(QColor(128, 128, 128, 60), 1)
        for v in graduations(x0, x1):
            X = px(v)
            p.setPen(grille)
            p.drawLine(QPointF(X, r.top()), QPointF(X, r.bottom()))
            p.setPen(pal.text().color())
            p.drawText(QRectF(X - 40, r.bottom() + 2, 80, 16), Qt.AlignmentFlag.AlignHCenter, '%.6g' % v)
        for v in graduations(y0, y1):
            Y = py(v)
            p.setPen(grille)
            p.drawLine(QPointF(r.left(), Y), QPointF(r.right(), Y))
            p.setPen(pal.text().color())
            p.drawText(QRectF(0, Y - 8, r.left() - 4, 16), Qt.AlignmentFlag.AlignRight, '%.5g' % v)
        p.drawText(QRectF(r.left(), r.bottom() + 20, r.width(), 18), Qt.AlignmentFlag.AlignHCenter, self.titre_x)
        p.save()
        p.translate(12, r.center().y())
        p.rotate(-90)
        p.drawText(QRectF(-r.height() / 2, -10, r.height(), 18), Qt.AlignmentFlag.AlignHCenter, self.titre_y)
        p.restore()
        # courbe : au plus 2 points par pixel (min/max par colonne) pour rester rapide sur 10^6 points
        chemin = QPainterPath()
        n = len(self.x)
        larg = int(r.width())
        if n > 4 * larg:
            idx = np.linspace(0, n, larg + 1).astype(int)
            premier = True
            for i in range(larg):
                seg = self.y[idx[i]:idx[i + 1]]
                if not len(seg):
                    continue
                X = r.left() + i
                for v in (seg.min(), seg.max()):
                    if premier:
                        chemin.moveTo(X, py(v))
                        premier = False
                    else:
                        chemin.lineTo(X, py(v))
        else:
            chemin.moveTo(px(self.x[0]), py(self.y[0]))
            for a, b in zip(self.x[1:], self.y[1:]):
                chemin.lineTo(px(a), py(b))
        p.setClipRect(r)
        p.setPen(QPen(QColor('#1C6DB4'), 1.4))
        p.drawPath(chemin)
        if self._curseur is not None:
            cx = self._curseur
            v = x0 + (cx - r.left()) / r.width() * (x1 - x0)
            i = int(np.clip(np.searchsorted(self.x, v), 0, n - 1))
            p.setPen(QPen(QColor('#B5382B'), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(px(self.x[i]), r.top()), QPointF(px(self.x[i]), r.bottom()))
            p.setClipping(False)
            p.setPen(pal.text().color())
            p.drawText(QRectF(r.left() + 6, r.top() + 4, r.width() - 12, 18), Qt.AlignmentFlag.AlignRight,
                       self.format_lecture.format(x=self.x[i], y=self.y[i]))
        p.end()

    def mouseMoveEvent(self, ev):
        r = self._cadre()
        x = ev.position().x()
        self._curseur = x if r.left() <= x <= r.right() else None
        self.update()

    def leaveEvent(self, ev):
        self._curseur = None
        self.update()
