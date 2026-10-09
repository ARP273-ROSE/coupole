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
        self._chemin = None
        self._fond = None
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
        """Axes et courbe dessinés une fois dans une image gardée (tant que données, taille, échelle d'écran et
        couleurs ne changent pas) ; le survol ne redessine que le curseur par-dessus, au lieu de toute la courbe
        à chaque mouvement de souris."""
        from PyQt6.QtGui import QPixmap
        dpr = float(self.devicePixelRatioF())
        cle = (self.width(), self.height(), dpr, id(self.x), 0 if self.x is None else len(self.x),
               self.palette().base().color().rgba(), self.palette().text().color().rgba(), self.titre_x, self.titre_y)
        if getattr(self, '_fond', None) is None or self._cle_fond != cle:
            pm = QPixmap(max(1, int(self.width() * dpr)), max(1, int(self.height() * dpr)))
            pm.setDevicePixelRatio(dpr)
            q = QPainter(pm)
            self._dessiner_fond(q)
            q.end()
            self._fond, self._cle_fond = pm, cle
        p = QPainter(self)
        p.drawPixmap(0, 0, self._fond)
        if self._curseur is not None and self.x is not None and len(self.x) >= 2:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            r = self._cadre()
            x0, x1, _, _ = self._limites()
            n = len(self.x)
            cx = self._curseur
            v = x0 + (cx - r.left()) / r.width() * (x1 - x0)
            i = int(np.clip(np.searchsorted(self.x, v), 0, n - 1))
            X = r.left() + (self.x[i] - x0) / (x1 - x0) * r.width()
            p.setClipRect(r)
            p.setPen(QPen(QColor('#B5382B'), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(X, r.top()), QPointF(X, r.bottom()))
            p.setClipping(False)
            f = QFont(self.font())
            f.setPointSizeF(max(7.0, f.pointSizeF() * 0.85))
            p.setFont(f)
            p.setPen(self.palette().text().color())
            p.drawText(QRectF(r.left() + 6, r.top() + 4, r.width() - 12, 18), Qt.AlignmentFlag.AlignRight,
                       self.format_lecture.format(x=self.x[i], y=self.y[i]))
        p.end()

    def _dessiner_fond(self, p):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = self.palette()
        p.fillRect(self.rect(), pal.base())
        r = self._cadre()
        p.setPen(QPen(pal.text().color(), 1))
        p.drawRect(r)
        if self.x is None or len(self.x) < 2:
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
        # courbe : au plus 2 points par pixel (min/max par colonne, en numpy) pour rester rapide sur 10^6 points ;
        # le chemin est gardé tant que ni les données ni la taille ne changent (le survol ne redessine que le
        # curseur au lieu de recalculer la courbe à chaque mouvement de souris)
        n = len(self.x)
        cle = (r.width(), r.height(), id(self.x), n)
        chemin = getattr(self, '_chemin', None)
        if chemin is None or self._cle_chemin != cle:
            chemin = self._chemin_courbe(r, n, px, py)
            self._chemin, self._cle_chemin = chemin, cle
        p.setClipRect(r)
        p.setPen(QPen(QColor('#1C6DB4'), 1.4))
        p.drawPath(chemin)

    def _chemin_courbe(self, r, n, px, py):
        chemin = QPainterPath()
        larg = int(r.width())
        if n > 4 * larg:
            idx = np.linspace(0, n, larg + 1).astype(int)
            debut = idx[:-1]
            plein = idx[1:] > debut
            debut = debut[plein]
            mins = np.minimum.reduceat(self.y, debut)
            maxs = np.maximum.reduceat(self.y, debut)
            X = (r.left() + np.flatnonzero(plein)).astype(float)
            xs = np.repeat(X, 2)
            ys = py(np.column_stack([mins, maxs]).ravel())
        else:
            xs, ys = px(self.x), py(self.y)
        xs, ys = xs.tolist(), ys.tolist()
        chemin.moveTo(xs[0], ys[0])
        for a, b in zip(xs[1:], ys[1:]):
            chemin.lineTo(a, b)
        return chemin

    def mouseMoveEvent(self, ev):
        r = self._cadre()
        x = ev.position().x()
        self._curseur = x if r.left() <= x <= r.right() else None
        self.update()

    def leaveEvent(self, ev):
        self._curseur = None
        self.update()


# Couleurs des séries (palette catégorielle validée, ordre fixe ; un pas par thème).
SERIES = {'clair': ['#2a78d6', '#eb6834', '#1baf7a', '#eda100'],
          'sombre': ['#3987e5', '#d95926', '#199e70', '#c98500']}


def _theme_courant() -> str:
    try:
        from ..core import config
        return 'sombre' if config.reglages()['apparence'] == 'sombre' else 'clair'
    except Exception:
        return 'clair'


def _graduations_log(a: float, b: float):
    """Puissances de 10 entre a et b (a, b > 0), complétées de 2 et 5 si la plage est courte."""
    lo, hi = math.floor(math.log10(a)), math.ceil(math.log10(b))
    out = [10.0 ** k for k in range(lo, hi + 1) if a <= 10.0 ** k <= b]
    if len(out) < 3:
        out = sorted({m * 10.0 ** k for k in range(lo, hi + 1) for m in (1, 2, 5) if a <= m * 10.0 ** k <= b})
    return out


def _texte_nombre(v: float) -> str:
    if v == 0:
        return '0'
    if 1 <= abs(v) < 1e7 and v == int(v):
        return '{:,d}'.format(int(v)).replace(',', '\u202f')
    if 1e-3 <= abs(v) < 1e7:
        return '%.4g' % v
    return '%.0e' % v


class TraceCourbes(QWidget):
    """Plusieurs courbes sur un même axe (une seule échelle verticale), axes logarithmiques au choix,
    légende au-dessus, étiquette directe en bout de courbe, marqueur vertical, lecture au curseur
    (réticule + valeurs de toutes les séries).  Sans matplotlib."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.series = []                # [(nom, x, y)]
        self.log_x = self.log_y = True
        self.titre_x = self.titre_y = ''
        self.marqueur = None            # abscisse d'un trait vertical (valeur courante)
        self.format_x = '{:.4g}'
        self.format_y = '{:.4g}'
        self._curseur = None
        self.setMouseTracking(True)
        self.setMinimumSize(220, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def definir(self, series, titre_x='', titre_y='', log_x=True, log_y=True):
        propres = []
        for nom, x, y in series:
            x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
            ok = np.isfinite(x) & np.isfinite(y)
            if log_x:
                ok &= x > 0
            if log_y:
                ok &= y > 0
            o = np.argsort(x[ok])
            propres.append((nom, x[ok][o], y[ok][o]))
        self.series, self.titre_x, self.titre_y, self.log_x, self.log_y = propres, titre_x, titre_y, log_x, log_y
        self.update()

    def placer_marqueur(self, x):
        self.marqueur = x
        self.update()

    # ------------------------------------------------------------ géométrie
    def _limites(self):
        xs = [s[1] for s in self.series if len(s[1])]
        ys = [s[2] for s in self.series if len(s[2])]
        if not xs:
            return None
        x0, x1 = min(float(v.min()) for v in xs), max(float(v.max()) for v in xs)
        y0, y1 = min(float(v.min()) for v in ys), max(float(v.max()) for v in ys)
        if self.log_y:
            y0, y1 = y0 / 1.3, y1 * 1.3
        else:
            m = (y1 - y0) * 0.05 or 1.0
            y0, y1 = y0 - m, y1 + m
        if x1 <= x0:
            x1 = x0 * 10 if self.log_x else x0 + 1
        return x0, x1, y0, y1

    def _t(self, v, log):
        return math.log10(v) if log else v

    def _cadre(self, hauteur_legende):
        return QRectF(64, 10 + hauteur_legende, max(10, self.width() - 64 - 70), max(10, self.height() - 52 - hauteur_legende))

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = self.palette()
        encre = pal.text().color()
        douce = pal.placeholderText().color()
        p.fillRect(self.rect(), pal.base())
        f = QFont(self.font())
        f.setPointSizeF(max(7.0, f.pointSizeF() * 0.9))
        p.setFont(f)
        fm = p.fontMetrics()
        couleurs = SERIES[_theme_courant()]
        # légende (une rangée, qui passe à la ligne si besoin)
        x, y, h = 64.0, 4.0, fm.height()
        for i, (nom, _, _) in enumerate(self.series):
            w = 22 + fm.horizontalAdvance(nom) + 14
            if x + w > self.width() - 8 and x > 64:
                x, y = 64.0, y + h + 2
            p.setPen(QPen(QColor(couleurs[i % len(couleurs)]), 2))
            p.drawLine(QPointF(x, y + h / 2), QPointF(x + 16, y + h / 2))
            p.setPen(encre)
            p.drawText(QRectF(x + 20, y, w, h), Qt.AlignmentFlag.AlignVCenter, nom)
            x += w
        r = self._cadre(y + h + 4 - 10 if self.series else 0)
        lim = self._limites()
        p.setPen(QPen(douce, 1))
        p.drawLine(r.bottomLeft(), r.bottomRight())
        p.drawLine(r.bottomLeft(), r.topLeft())
        if lim is None:
            p.end()
            return
        x0, x1, y0, y1 = lim
        tx0, tx1 = self._t(x0, self.log_x), self._t(x1, self.log_x)
        ty0, ty1 = self._t(y0, self.log_y), self._t(y1, self.log_y)

        def px(v):
            return r.left() + (self._t(v, self.log_x) - tx0) / (tx1 - tx0) * r.width()

        def py(v):
            return r.bottom() - (self._t(v, self.log_y) - ty0) / (ty1 - ty0) * r.height()
        self._px, self._r, self._lim = px, r, lim
        grille = QPen(QColor(douce.red(), douce.green(), douce.blue(), 45), 1)
        gx = _graduations_log(x0, x1) if self.log_x else graduations(x0, x1)
        gy = _graduations_log(y0, y1) if self.log_y else graduations(y0, y1)
        for v in gx:
            X = px(v)
            p.setPen(grille)
            p.drawLine(QPointF(X, r.top()), QPointF(X, r.bottom()))
            p.setPen(douce)
            p.drawText(QRectF(X - 40, r.bottom() + 3, 80, h), Qt.AlignmentFlag.AlignHCenter, _texte_nombre(v))
        for v in gy:
            Y = py(v)
            p.setPen(grille)
            p.drawLine(QPointF(r.left(), Y), QPointF(r.right(), Y))
            p.setPen(douce)
            p.drawText(QRectF(0, Y - h / 2, r.left() - 5, h), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       _texte_nombre(v))
        p.setPen(encre)
        p.drawText(QRectF(r.left(), r.bottom() + h + 6, r.width(), h + 2), Qt.AlignmentFlag.AlignHCenter, self.titre_x)
        p.save()
        p.translate(12, r.center().y())
        p.rotate(-90)
        p.drawText(QRectF(-r.height() / 2, -h / 2, r.height(), h + 2), Qt.AlignmentFlag.AlignHCenter, self.titre_y)
        p.restore()
        p.setClipRect(r.adjusted(-2, -2, 2, 2))
        fins = []
        for i, (nom, xs, ys) in enumerate(self.series):
            if len(xs) < 2:
                continue
            chemin = QPainterPath()
            chemin.moveTo(px(xs[0]), py(ys[0]))
            for a, b in zip(xs[1:], ys[1:]):
                chemin.lineTo(px(a), py(b))
            p.setPen(QPen(QColor(couleurs[i % len(couleurs)]), 2))
            p.drawPath(chemin)
            fins.append((py(ys[-1]), nom))
        if self.marqueur is not None and x0 <= self.marqueur <= x1:
            p.setPen(QPen(encre, 1, Qt.PenStyle.DashLine))
            X = px(self.marqueur)
            p.drawLine(QPointF(X, r.top()), QPointF(X, r.bottom()))
            for i, (nom, xs, ys) in enumerate(self.series):
                if len(xs) < 2:
                    continue
                yv = float(np.interp(self._t(self.marqueur, self.log_x), [self._t(v, self.log_x) for v in xs],
                                     [self._t(v, self.log_y) for v in ys]))
                Y = r.bottom() - (yv - ty0) / (ty1 - ty0) * r.height()
                p.setPen(QPen(pal.base().color(), 2))
                p.setBrush(QColor(couleurs[i % len(couleurs)]))
                p.drawEllipse(QPointF(X, Y), 4.5, 4.5)
        p.setClipping(False)
        # étiquettes directes en bout de courbe (texte à l'encre du thème, décalées pour ne pas se chevaucher)
        p.setPen(encre)
        dernier = -1e9
        for Y, nom in sorted(fins):
            Y = max(Y, dernier + h)
            dernier = Y
            court = nom.split(' ')[0] if ' ' in nom else nom
            p.drawText(QRectF(r.right() + 4, Y - h / 2, 66, h), Qt.AlignmentFlag.AlignVCenter, court)
        # réticule et valeurs au curseur
        if self._curseur is not None:
            cx = min(max(self._curseur, r.left()), r.right())
            tv = tx0 + (cx - r.left()) / r.width() * (tx1 - tx0)
            xv = 10 ** tv if self.log_x else tv
            p.setPen(QPen(douce, 1, Qt.PenStyle.DotLine))
            p.drawLine(QPointF(cx, r.top()), QPointF(cx, r.bottom()))
            lignes = [self.format_x.format(xv)]
            for nom, xs, ys in self.series:
                if len(xs) >= 2 and xs[0] <= xv <= xs[-1]:
                    yv = float(np.interp(self._t(xv, self.log_x), [self._t(v, self.log_x) for v in xs],
                                         [self._t(v, self.log_y) for v in ys]))
                    lignes.append('%s : %s' % (nom, self.format_y.format(10 ** yv if self.log_y else yv)))
            largeur = max(fm.horizontalAdvance(s) for s in lignes) + 16
            hauteur = len(lignes) * h + 10
            bx = cx + 10 if cx + 10 + largeur < self.width() else cx - 10 - largeur
            boite = QRectF(bx, r.top() + 6, largeur, hauteur)
            p.setPen(QPen(douce, 1))
            p.setBrush(pal.toolTipBase())
            p.drawRoundedRect(boite, 6, 6)
            p.setPen(pal.toolTipText().color())
            for k, s in enumerate(lignes):
                p.drawText(QRectF(bx + 8, r.top() + 11 + k * h, largeur, h), Qt.AlignmentFlag.AlignVCenter, s)
        p.end()

    def mouseMoveEvent(self, ev):
        self._curseur = ev.position().x() if self.series else None
        self.update()

    def leaveEvent(self, ev):
        self._curseur = None
        self.update()
