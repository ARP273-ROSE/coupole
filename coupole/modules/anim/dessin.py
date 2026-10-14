"""Dessin des animations : projection orthographique d'une sphère (3D simple, calculée), couleurs selon le thème,
tracés en deux passes (sous puis sur un plan) et petits outils de QPainter.

Le repère « monde » d'une vue est direct : pour une sphère locale x = nord, y = ouest, z = zénith ; pour une sphère
céleste x = point vernal, y = 6 h, z = pôle nord.  Le point de vue est donné par son azimut (compté comme
l'azimut astronomique, depuis +x vers −y) et sa hauteur au-dessus du plan xy.
"""
from __future__ import annotations

import math
import re

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QLinearGradient, QPainterPath, QPen, QPolygonF,
                         QRadialGradient)

from ...core import config

DEG = math.pi / 180.0

# Couleurs : douces, lisibles sur le fond sombre (défaut) comme sur le fond clair ; « ciel » et « sol » pour les
# sphères locales.  Contraste des textes sur le fond vérifié par tests/test_anim_gui.py.
PALETTES = {
    'sombre': {'fond': '#1B1F26', 'texte': '#D9DDE2', 'doux': '#A3ABB6', 'grille': '#4A525E', 'sphere': '#2A3240',
               'ciel': '#2C4A6B', 'sol': '#3E5B3A', 'horizon': '#7FA36F', 'equateur': '#6FA8DC', 'ecliptique': '#E8A85C',
               'meridien': '#C9A0DC', 'soleil': '#FFD25A', 'lune': '#D8D8D0', 'terre': '#4F86C6', 'mars': '#E07050',
               'etoile': '#FFFFFF', 'accent1': '#F2C14E', 'accent2': '#7CC4E8', 'accent3': '#F28C8C',
               'ombre': '#000000', 'nuit': '#0E1218', 'arc1': '#A99BFF', 'arc2': '#FF8F87',
               'umbra': '#05070A', 'penombre': '#9AA6B6'},
    'clair': {'fond': '#FBFBF8', 'texte': '#2E333B', 'doux': '#646C77', 'grille': '#C9CED4', 'sphere': '#E6ECF2',
              'ciel': '#BFD7EE', 'sol': '#A9C79B', 'horizon': '#4E7A3E', 'equateur': '#2F6FAF', 'ecliptique': '#C2701C',
              'meridien': '#8A4FA6', 'soleil': '#C08400', 'lune': '#8C8C84', 'terre': '#2F6FAF', 'mars': '#B8452C',
              'etoile': '#2E333B', 'accent1': '#B07A00', 'accent2': '#1F7AA6', 'accent3': '#B5403C',
              'ombre': '#000000', 'nuit': '#5A6270', 'arc1': '#4B3FC9', 'arc2': '#C0392B',
              'umbra': '#1B1F26', 'penombre': '#5A6270'},
}


def theme() -> str:
    try:
        nom = config.reglages()['apparence']
    except Exception:
        nom = 'sombre'
    return nom if nom in PALETTES else 'sombre'


_COULEURS: dict = {}


def c(cle: str, alpha: float | None = None) -> QColor:
    k = (theme(), cle)
    base = _COULEURS.get(k)
    if base is None:
        base = _COULEURS[k] = QColor(PALETTES[k[0]][cle])
    col = QColor(base)
    if alpha is not None:
        col.setAlphaF(max(0.0, min(1.0, alpha)))
    return col


def stylo(cle_ou_couleur, epaisseur: float = 1.5, alpha: float | None = None, pointille: bool = False) -> QPen:
    col = c(cle_ou_couleur, alpha) if isinstance(cle_ou_couleur, str) else QColor(cle_ou_couleur)
    if alpha is not None and not isinstance(cle_ou_couleur, str):
        col.setAlphaF(alpha)
    p = QPen(col, epaisseur)
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    if pointille:
        p.setStyle(Qt.PenStyle.DashLine)
    return p


def police(p, taille_relative: float = 1.0, gras: bool = False) -> QFont:
    f = QFont(p.font())
    f.setPointSizeF(max(6.0, f.pointSizeF() * taille_relative))
    f.setBold(gras)
    p.setFont(f)
    return f


# ==================================================================== étiquettes sans chevauchement
# Toutes les étiquettes à cartouche (texte(..., fond=True) et etiquette()) d'une image passent par un placeur commun :
# si la place voulue est prise (autre étiquette, petit objet, texte déjà écrit, bord de la toile), l'étiquette essaie
# 24 positions autour de son point d'accroche (en haut à droite, en bas à droite, en haut à gauche, en bas à gauche,
# dessus, dessous, droite, gauche, sur trois distances) et prend la première libre, sinon la moins encombrée ; déplacée,
# elle est reliée à sa place d'origine par un trait de rappel.  Boîtes en pixels de la toile (transformations
# comprises) ; les textes tournés ne sont pas déplacés.  Mêmes règles que Coupole Web (src/noyau/dessin.ts).
_etiquettes: list = []
_objets: list = []
_cadre = None
_lumiere = None


def debut_image(p=None, r: QRectF | None = None):
    """À appeler au début de chaque image (fait par la toile et Animation.image) : `r` est toute la toile."""
    global _etiquettes, _objets, _cadre, _lumiere
    _etiquettes, _objets, _cadre, _lumiere = [], [], None, None
    if p is not None and r is not None:
        a, d, e, f, _ = _matrice(p)
        _cadre = (a * r.x() + e, d * r.y() + f, abs(a * r.width()), abs(d * r.height()))


def etiquettes_posees() -> list:
    """Boîtes (x, y, l, h) des étiquettes posées depuis le début de l'image (tests)."""
    return list(_etiquettes)


def _matrice(p):
    m = p.worldTransform()
    return m.m11(), m.m22(), m.dx(), m.dy(), abs(m.m12()) > 1e-6 or abs(m.m21()) > 1e-6


def _commun(a, b) -> float:
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def reserver(p, x: float, y: float, r: float, toujours: bool = False):
    """Un petit objet (astre, point…) que les étiquettes évitent ; les grands disques ne sont pas réservés, sauf si
    `toujours` (halo qu'une étiquette ne doit pas couvrir)."""
    if not (r > 0) or (r > 24 and not toujours):
        return
    a, d, e, f, tourne = _matrice(p)
    if tourne:
        return
    k = abs(a)
    _objets.append((a * x + e - r * k, d * y + f - r * k, 2 * r * k, 2 * r * k))


def _encombrement(b) -> float:
    c_ = (b[2] * b[3] - _commun(b, _cadre)) * 8 if _cadre else 0.0
    for o in _etiquettes:
        c_ += _commun(b, o) * 4
    for o in _objets:
        c_ += _commun(b, o)
    return c_


def _placer(p, x0, y0, w, h, ax, ay, ecart):
    """Place une boîte w × h voulue en (x0, y0) (coin haut gauche, repère local) ; rend le coin retenu."""
    a, d, e, f, tourne = _matrice(p)
    if tourne:
        return x0, y0

    def dev(x, y):
        X, Y = a * x + e, d * y + f
        return (min(X, X + a * w), min(Y, Y + d * h), abs(a * w), abs(d * h))

    meilleur = (x0, y0)
    cout = _encombrement(dev(x0, y0))
    if cout > 0.5:
        cands = []
        for k in (1, 2, 3):
            ec = ecart * k + (k - 1) * h * 0.6
            cands += [(ax + ec, ay - ec - h), (ax + ec, ay + ec), (ax - ec - w, ay - ec - h), (ax - ec - w, ay + ec),
                      (ax - w / 2, ay - ec - h), (ax - w / 2, ay + ec), (ax + ec, ay - h / 2),
                      (ax - ec - w, ay - h / 2)]
        for cx, cy in cands:
            dep = 0.02 * math.hypot(cx - x0, cy - y0)
            cc = _encombrement(dev(cx, cy)) + dep
            if cc < cout - 1e-9:
                cout, meilleur = cc, (cx, cy)
                if cc < 0.5 + dep:
                    break
    _etiquettes.append(dev(*meilleur))
    return meilleur


_PUISSANCE = re.compile('10([⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)')
_EXP_VERS = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺', '0123456789−+')


def _morceaux_puissances(s: str):
    """« 6,67 × 10⁻¹¹ » → [('6,67 × 10', False), ('−11', True)] : les puissances de dix sont composées en vrai
    exposant (chiffres de la police, plus petits et surélevés) plutôt qu'avec les caractères en exposant."""
    out, i = [], 0
    for m in _PUISSANCE.finditer(s):
        out.append((s[i:m.start(1)], False))
        out.append((m.group(1).translate(_EXP_VERS), True))
        i = m.end()
    out.append((s[i:], False))
    return [(t, e) for t, e in out if t]


def _largeur_texte(p, s: str) -> float:
    if not _PUISSANCE.search(s):
        return p.fontMetrics().horizontalAdvance(s)
    fm = p.fontMetrics()
    f = QFont(p.font())
    if f.pointSizeF() > 0:
        f.setPointSizeF(f.pointSizeF() * 0.72)
    else:
        f.setPixelSize(max(6, int(f.pixelSize() * 0.72)))
    fe = QFontMetricsF(f, p.device())
    return sum(fe.horizontalAdvance(t) + 1 if e else fm.horizontalAdvance(t) for t, e in _morceaux_puissances(s))


def _ecrire(p, x0: float, y0: float, s: str):
    if not _PUISSANCE.search(s):
        p.drawText(QPointF(x0, y0), s)
        return
    fm = p.fontMetrics()
    normale = QFont(p.font())
    petite = QFont(normale)
    if petite.pointSizeF() > 0:
        petite.setPointSizeF(petite.pointSizeF() * 0.72)
    else:
        petite.setPixelSize(max(6, int(petite.pixelSize() * 0.72)))
    x = x0
    for t, e in _morceaux_puissances(s):
        if e:
            p.setFont(petite)
            p.drawText(QPointF(x + 0.5, y0 - fm.ascent() * 0.42), t)
            x += p.fontMetrics().horizontalAdvance(t) + 1
            p.setFont(normale)
        else:
            p.drawText(QPointF(x, y0), t)
            x += fm.horizontalAdvance(t)


def texte(p, x: float, y: float, s: str, cle: str = 'texte', centre: bool = True, alpha: float | None = None,
          fond: bool = False):
    """Texte centré (ou aligné à gauche) au point (x, y) ; `fond` : petit cartouche sous le texte, placé sans
    chevaucher les autres étiquettes.  Un texte plus large que la toile est réduit (8 px au moins) ; un texte qui
    déborde à peine de la toile est ramené dedans."""
    fm = p.fontMetrics()
    w = _largeur_texte(p, s)
    police_avant = None
    a, d, e, f, tourne = _matrice(p)
    if _cadre and not tourne and a > 0 and w * a > _cadre[2] - 8:
        police_avant = QFont(p.font())
        nf = QFont(police_avant)
        px = nf.pixelSize() if nf.pixelSize() > 0 else nf.pointSizeF() * p.device().logicalDpiY() / 72.0
        nf.setPixelSize(max(8, int(px * (_cadre[2] - 8) / (w * a))))
        p.setFont(nf)
        fm = p.fontMetrics()
        w = _largeur_texte(p, s)
    h = fm.height()
    x0 = x - w / 2 if centre else x
    y0 = y + fm.ascent() / 2 - 1 if centre else y
    if _cadre and not tourne and a > 0:
        X0 = a * x0 + e
        X1 = X0 + a * w
        g, dr = _cadre[0] + 2, _cadre[0] + _cadre[2] - 2
        if X0 < g < X1:
            x0 += (g - X0) / a
        elif X0 < dr < X1:
            x0 -= (X1 - dr) / a
    if fond:
        bx, by = x0 - 3, y0 - fm.ascent() - 1
        ax, ay = x, (y if centre else y0 - fm.ascent() / 2)
        nx, ny = _placer(p, bx, by, w + 6, h + 2, ax, ay, 6)
        if abs(nx - bx) > 0.5 or abs(ny - by) > 0.5:
            px_, py_ = max(nx, min(nx + w + 6, ax)), max(ny, min(ny + h + 2, ay))
            p.save()
            p.setPen(stylo(cle, 0.9, 0.55 * (alpha if alpha is not None else 1.0)))
            p.drawLine(QPointF(ax, ay), QPointF(px_, py_))
            p.restore()
            x0, y0 = nx + 3, ny + fm.ascent() + 1
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c('fond', 0.78))
        p.drawRoundedRect(QRectF(x0 - 3, y0 - fm.ascent() - 1, w + 6, h + 2), 4, 4)
        p.restore()
    elif not tourne and s.strip():
        # texte sans cartouche (titres, graduations) : il ne bouge pas, mais les étiquettes l'évitent
        X, Y = a * x0 + e, d * (y0 - fm.ascent()) + f
        _objets.append((min(X, X + a * w), min(Y, Y + d * h), abs(a * w), abs(d * h)))
    p.setPen(c(cle, alpha))
    _ecrire(p, x0, y0, s)
    if police_avant is not None:
        p.setFont(police_avant)


def etiquette(p, x: float, y: float, s: str, cle: str = 'texte', ecart: float = 8.0, alpha: float | None = None):
    """Étiquette d'un objet en (x, y) : à côté de lui (en haut à droite si la place est libre), jamais par-dessus
    une autre étiquette ; reliée à l'objet par un trait de rappel si elle a dû s'en éloigner."""
    fm = p.fontMetrics()
    w, h = _largeur_texte(p, s) + 6, fm.height() + 2
    nx, ny = _placer(p, x + ecart, y - ecart - h, w, h, x, y, ecart)
    if math.hypot(nx - (x + ecart), ny - (y - ecart - h)) > 0.5 and \
            (abs(nx + w / 2 - x) > w / 2 + ecart * 1.6 or abs(ny + h / 2 - y) > h / 2 + ecart * 1.6):
        px_, py_ = max(nx, min(nx + w, x)), max(ny, min(ny + h, y))
        p.save()
        p.setPen(stylo(cle, 0.9, 0.55))
        p.drawLine(QPointF(x, y), QPointF(px_, py_))
        p.restore()
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(c('fond', 0.78))
    p.drawRoundedRect(QRectF(nx, ny, w, h), 4, 4)
    p.restore()
    p.setPen(c(cle, alpha))
    _ecrire(p, nx + 3, ny + 1 + fm.ascent(), s)


def formule(p, x: float, y: float, s: str, cle: str = 'texte', centre: bool = True):
    """Formule mise en forme (fractions empilées, exposants, indices, italiques ; police STIX Two Math) : centrée en
    (x, y), ou à partir de x (ligne de base y) si `centre` est faux.  Elle devient un obstacle pour les étiquettes."""
    from . import formule as fo
    bx, by, bw, bh = fo.dessiner(p, x, y, s, centre, c(cle))
    a, d, e, f, tourne = _matrice(p)
    if not tourne:
        X, Y = a * bx + e, d * by + f
        _objets.append((min(X, X + a * bw), min(Y, Y + d * bh), abs(a * bw), abs(d * bh)))
    return bw


def formule_texte(p, x: float, y: float, f: str, suite: str, cle: str = 'texte', cle_suite: str | None = None):
    """Une formule mise en forme suivie d'un texte simple (résultat avec unité : « = 3,98 × 10²⁶ W »), le tout centré
    en (x, y)."""
    from . import formule as fo
    wf = fo.largeur(p, f)
    ws = _largeur_texte(p, suite)
    x0 = x - (wf + ws) / 2
    formule(p, x0, y + p.fontMetrics().ascent() / 2 - 1, f, cle, centre=False)
    yb = y + p.fontMetrics().ascent() / 2 - 1
    texte(p, x0 + wf, yb, suite, cle_suite or cle, centre=False)


# ==================================================================== corps célestes en sphères
ASTRES = frozenset(('soleil', 'lune', 'terre', 'mars'))


def oublier_lumiere():
    """Oublie la source de lumière (début d'image, nouveau panneau)."""
    global _lumiere
    _lumiere = None


def _fonce(col: QColor, k: float, alpha: float) -> QColor:
    out = QColor.fromRgbF(col.redF() * k, col.greenF() * k, col.blueF() * k)
    out.setAlphaF(alpha)
    return out


def _avec(col: QColor, alpha: float) -> QColor:
    out = QColor(col)
    out.setAlphaF(max(0.0, min(1.0, alpha)))
    return out


_BROSSES: dict = {}


def _brosse(cle: str, al: float, genre: str, *param):
    """Brosses des astres, en coordonnées relatives à la boîte de l'ellipse (ObjectBoundingMode) : indépendantes de
    la position et du rayon, donc mises en cache (une image peut compter des centaines d'astres)."""
    k = (theme(), cle, round(al, 3), genre) + param
    br = _BROSSES.get(k)
    if br is not None:
        return br
    base = c(cle)
    if genre == 'soleil':
        g = QRadialGradient(QPointF(0.5, 0.5), 0.5)
        g.setColorAt(0.0, _avec(base.lighter(118), al))
        g.setColorAt(0.65, _avec(base, al))
        g.setColorAt(1.0, _fonce(base, 0.78, al))
    elif genre == 'halo':
        g = QRadialGradient(QPointF(0.5, 0.5), 0.5)
        h0 = _avec(base, 0.28 * al)
        g.setColorAt(0.0, h0)
        g.setColorAt(param[0], h0)
        g.setColorAt(1.0, _avec(base, 0.0))
    elif genre == 'volume':
        lx, ly, nuit = param
        g = QRadialGradient(QPointF(0.5, 0.5), 0.5, QPointF(0.5 + lx * 0.21, 0.5 + ly * 0.21), 0.025)
        g.setColorAt(0.0, _avec(base.lighter(132 if nuit else 122), al))
        g.setColorAt(0.55, _avec(base, al))
        g.setColorAt(1.0, _fonce(base, 0.62 if nuit else 0.7, al))
    else:                                              # 'nuit' : voile au-delà du terminateur
        lx, ly = param
        g = QLinearGradient(QPointF(0.5 + lx * 0.5, 0.5 + ly * 0.5), QPointF(0.5 - lx * 0.5, 0.5 - ly * 0.5))
        g.setColorAt(0.0, _avec(base, 0.0))
        g.setColorAt(0.47, _avec(base, 0.0))
        g.setColorAt(0.56, _avec(base, 0.62 * al))
        g.setColorAt(1.0, _avec(base, 0.8 * al))
    g.setCoordinateMode(QRadialGradient.CoordinateMode.ObjectBoundingMode)
    br = _BROSSES[k] = QBrush(g)
    if len(_BROSSES) > 4000:
        _BROSSES.clear()
    return br


def astre(p, x: float, y: float, r: float, cle: str, bord=None, alpha: float | None = None):
    """Corps céleste à l'aspect d'une sphère : dégradé radial (volume) au foyer décalé de 0,42 r vers la lumière,
    limbe assombri et, si un Soleil a été dessiné dans le panneau, côté nuit ombré au-delà du terminateur ; le Soleil
    a un limbe assombri et un halo discret.  Vectoriel ; brosses mises en cache : coût négligeable."""
    global _lumiere
    al = 1.0 if alpha is None else alpha
    a, d, e, f, tourne = _matrice(p)
    centre = QPointF(x, y)
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    if cle == 'soleil':
        if r >= 5:
            rh = r + min(0.9 * r, 26.0)
            p.setBrush(_brosse(cle, al, 'halo', round(r * 0.9 / rh, 2)))
            p.drawEllipse(centre, rh, rh)
        p.setBrush(_brosse(cle, al, 'soleil'))
        p.setPen(stylo(bord, 1.0) if bord else Qt.PenStyle.NoPen)
        p.drawEllipse(centre, r, r)
        p.restore()
        if not tourne:
            _lumiere = (a * x + e, d * y + f)
        return
    lx, ly, nuit = -0.55, -0.83, False
    if _lumiere is not None and not tourne and a != 0 and d != 0:
        sx, sy = (_lumiere[0] - e) / a, (_lumiere[1] - f) / d
        dist = math.hypot(sx - x, sy - y)
        if dist > r * 1.2:
            # direction du Soleil, arrondie au degré (cache des brosses)
            ang = round(math.degrees(math.atan2(sy - y, sx - x)))
            lx, ly, nuit = math.cos(math.radians(ang)), math.sin(math.radians(ang)), True
    p.setBrush(_brosse(cle, al, 'volume', round(lx, 4), round(ly, 4), nuit))
    p.drawEllipse(centre, r, r)
    if nuit:
        # côté nuit : le terminateur est le diamètre perpendiculaire à la direction du Soleil
        p.setBrush(_brosse('nuit', al, 'nuit', round(lx, 4), round(ly, 4)))
        p.drawEllipse(centre, r, r)
    if bord:
        p.setPen(stylo(bord, 1.0, 0.6 * al))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(centre, r, r)
    p.restore()


def disque(p, x: float, y: float, r: float, cle_ou_couleur='soleil', bord=None, alpha: float | None = None):
    """Disque ; le Soleil, la Lune, la Terre et Mars (dès 3,5 px de rayon) sont dessinés en sphères (astre())."""
    if isinstance(cle_ou_couleur, str) and cle_ou_couleur in ASTRES and r >= 3.5:
        astre(p, x, y, r, cle_ou_couleur, bord, alpha)
    else:
        col = c(cle_ou_couleur, alpha) if isinstance(cle_ou_couleur, str) else cle_ou_couleur
        p.setBrush(QBrush(col))
        p.setPen(stylo(bord, 1.0) if bord else Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(x, y), r, r)
    reserver(p, x, y, r)


def fleche(p, x0, y0, x1, y1, pen: QPen, tete: float = 8.0):
    p.setPen(pen)
    p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
    a = math.atan2(y1 - y0, x1 - x0)
    pts = [QPointF(x1, y1), QPointF(x1 - tete * math.cos(a - 0.4), y1 - tete * math.sin(a - 0.4)),
           QPointF(x1 - tete * math.cos(a + 0.4), y1 - tete * math.sin(a + 0.4))]
    p.setBrush(pen.color())
    p.drawPolygon(QPolygonF(pts))


def phase_lune(p, x: float, y: float, r: float, angle: float, cle_eclairee='lune', cle_sombre='nuit',
               rotation: float = 0.0):
    """Disque de la Lune vu de la Terre pour l'angle de phase `angle` (0 nouvelle, 90 premier quartier, 180 pleine),
    côté éclairé à droite pour 0 < angle < 180 (hémisphère nord), limbe et terminateur exacts (ellipse)."""
    p.save()
    p.translate(x, y)
    p.rotate(rotation)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(c(cle_sombre) if isinstance(cle_sombre, str) else QColor(cle_sombre))
    p.drawEllipse(QPointF(0, 0), r, r)
    a = angle % 360.0
    k = math.cos(a * DEG)                      # demi-axe du terminateur (en rayons), signé
    chemin = QPainterPath()
    droite = a <= 180.0                        # croissante : partie éclairée à droite
    n = 64
    pts = []
    for i in range(n + 1):                     # limbe éclairé (demi-cercle)
        t = -math.pi / 2 + math.pi * i / n
        pts.append(QPointF(r * math.cos(t) * (1 if droite else -1), r * math.sin(t)))
    for i in range(n + 1):                     # terminateur (demi-ellipse) en retour
        t = math.pi / 2 - math.pi * i / n
        xx = r * math.cos(t) * k * (1 if droite else -1)
        pts.append(QPointF(xx, r * math.sin(t)))
    chemin.addPolygon(QPolygonF(pts))
    base = c(cle_eclairee) if isinstance(cle_eclairee, str) else QColor(cle_eclairee)
    if r >= 6:
        # partie éclairée : léger volume (plus clair vers le Soleil, limbe assombri)
        g = QRadialGradient(QPointF(0, 0), r * 1.02, QPointF((1 if droite else -1) * r * 0.35, -r * 0.15), r * 0.05)
        g.setColorAt(0.0, base.lighter(116))
        g.setColorAt(0.6, base)
        g.setColorAt(1.0, _fonce(base, 0.8, base.alphaF()))
        p.setBrush(QBrush(g))
    else:
        p.setBrush(base)
    p.drawPath(chemin)
    p.setPen(stylo('doux', 1.0, 0.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(0, 0), r, r)
    p.restore()


def polygone(xs, ys) -> QPolygonF:
    """QPolygonF depuis deux tableaux de coordonnées, sans créer un QPointF par point (copie directe dans la mémoire
    du polygone ; repli point par point si la liaison Qt ne l'expose pas)."""
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    n = len(xs)
    try:
        poly = QPolygonF()
        poly.resize(n)
        if n:
            ptr = poly.data()
            ptr.setsize(16 * n)
            a = np.frombuffer(ptr, dtype=np.float64).reshape(n, 2)
            a[:, 0] = xs
            a[:, 1] = ys
        return poly
    except Exception:
        return QPolygonF(list(map(QPointF, xs.tolist(), ys.tolist())))


# ==================================================================== projection d'une sphère
class Vue3D:
    """Point de vue d'une scène 3D (projection orthographique) : azimut et hauteur en degrés, bornés."""

    def __init__(self, az: float = 215.0, alt: float = 30.0, alt_min: float = -89.0, alt_max: float = 89.0):
        self.alt_min, self.alt_max = alt_min, alt_max
        self.defaut = (az, alt)
        self.rayon_px = 0.0                    # rayon à l'écran de la dernière sphère dessinée avec cette vue
        self.regler(az, alt)

    def regler(self, az: float, alt: float):
        if not (math.isfinite(az) and math.isfinite(alt)):
            return                              # garde-fou : jamais d'état invalide (NaN) gardé
        self.az = az % 360.0
        self.alt = max(self.alt_min, min(self.alt_max, alt))
        a, h = self.az * DEG, self.alt * DEG
        d = np.array([math.cos(h) * math.cos(a), -math.cos(h) * math.sin(a), math.sin(h)])    # vers l'observateur
        haut = np.array([0.0, 0.0, 1.0])
        droite = np.cross(haut, d)
        n = np.linalg.norm(droite)
        droite = droite / n if n > 1e-9 else np.array([0.0, 1.0, 0.0])
        self.d, self.droite, self.haut = d, droite, np.cross(d, droite)

    def reinitialiser(self):
        self.regler(*self.defaut)

    def tourner(self, dx_px: float, dy_px: float, sensibilite: float | None = None):
        """Glisser de (dx, dy) pixels : le point de la sphère sous la souris suit la souris (vers la droite, la face
        visible part vers la droite ; vers le bas, elle descend), au rythme d'un radian par rayon de sphère ; sans
        rayon connu, 0,4° par pixel."""
        if not (math.isfinite(dx_px) and math.isfinite(dy_px)):
            return
        if sensibilite is None:
            s = min(0.6, 180.0 / math.pi / self.rayon_px) if self.rayon_px > 20 and math.isfinite(self.rayon_px) \
                else 0.4
            # à la hauteur h, un tour d'azimut ne déplace le centre de l'image que de cos h : on compense (borné)
            k = 1.0 / max(0.35, math.cos(self.alt * DEG))
        else:
            s, k = sensibilite, 1.0
        self.regler(self.az + dx_px * s * k, self.alt + dy_px * s)

    def projeter(self, pts: np.ndarray):
        """pts (N, 3) → x (droite), y (haut), profondeur (> 0 : devant le centre)."""
        pts = np.asarray(pts, dtype=float).reshape(-1, 3)
        return pts @ self.droite, pts @ self.haut, pts @ self.d


def cercle(normale, angle_centre: float = 90.0, n: int = 181, debut: float = 0.0, fin: float = 360.0,
           origine=None) -> np.ndarray:
    """Points (n, 3) d'un cercle de la sphère unité : tous les points à `angle_centre` degrés de la direction
    `normale` (90 : grand cercle).  `origine` : direction du point d'angle 0 (projetée), sinon arbitraire.
    Le sens est direct autour de la normale."""
    nrm = np.asarray(normale, dtype=float)
    nrm = nrm / np.linalg.norm(nrm)
    o = np.asarray(origine, dtype=float) if origine is not None else (
        np.array([0.0, 0.0, 1.0]) if abs(nrm[2]) < 0.9 else np.array([1.0, 0.0, 0.0]))
    u = o - nrm * float(o @ nrm)
    if np.linalg.norm(u) < 1e-9:
        u = np.cross(nrm, [1.0, 0.0, 0.0])
        if np.linalg.norm(u) < 1e-9:
            u = np.cross(nrm, [0.0, 1.0, 0.0])
    u = u / np.linalg.norm(u)
    w = np.cross(nrm, u)
    t = np.linspace(debut * DEG, fin * DEG, n)
    ca, sa = math.cos(angle_centre * DEG), math.sin(angle_centre * DEG)
    return (nrm[None, :] * ca + sa * (np.cos(t)[:, None] * u[None, :] + np.sin(t)[:, None] * w[None, :]))


def arc(a, b, n: int = 60) -> np.ndarray:
    """Arc de grand cercle (le plus court) entre deux directions unitaires."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    om = math.acos(max(-1.0, min(1.0, float(a @ b))))
    if om < 1e-9:
        return np.vstack([a, b])
    t = np.linspace(0.0, 1.0, n)
    return (np.sin((1 - t) * om)[:, None] * a + np.sin(t * om)[:, None] * b) / math.sin(om)


class Peintre3D:
    """Dessine dans une vue : centre et rayon (pixels) de la sphère unité.

    `passe` : None (tout), 'dessous' ou 'dessus' (par rapport au plan z = 0 du repère monde, pour qu'un plan
    d'horizon semi-transparent masque ce qui est dessous).  Ce qui est derrière la sphère (profondeur < 0) est
    tracé en pointillé et plus pâle."""

    def __init__(self, p, vue: Vue3D, cx: float, cy: float, rayon: float, transformer=None):
        self.p, self.vue, self.cx, self.cy, self.r = p, vue, cx, cy, rayon
        if rayon > 20:
            vue.rayon_px = rayon
        self.passe = None
        self.transformer = transformer         # fonction (N, 3) → (N, 3) : repère de l'objet → monde

    def _monde(self, pts, repere_monde: bool):
        pts = np.asarray(pts, dtype=float).reshape(-1, 3)
        if self.transformer is not None and not repere_monde:
            pts = self.transformer(pts)
        return pts

    def ecran(self, v, repere_monde: bool = False):
        pts = self._monde(v, repere_monde)
        x, y, z = self.vue.projeter(pts)
        return self.cx + self.r * x, self.cy - self.r * y, z, pts[:, 2]

    def _garder(self, haut: bool) -> bool:
        if self.passe is None:
            return True
        dessus = self.vue.alt >= 0
        return (haut == dessus) if self.passe == 'dessus' else (haut != dessus)

    def courbe(self, pts, couleur, epaisseur: float = 1.5, alpha: float = 1.0, arriere: str = 'pointille',
               repere_monde: bool = False, ferme: bool = False, profondeur: bool = True):
        """Polyligne 3D ; `arriere` : 'pointille', 'pale', 'cache' ou 'normal' pour la partie derrière la sphère.

        Les segments sont classés (devant / derrière la sphère, dessus / dessous du plan) en une passe numpy, puis
        tracés par morceaux contigus de même classe."""
        xs, ys, zs, hs = self.ecran(pts, repere_monde)
        if len(xs) < 2:
            return
        if ferme:
            xs, ys, zs, hs = (np.append(t, t[0]) for t in (xs, ys, zs, hs))
        av = ((zs[:-1] + zs[1:]) >= 0) if profondeur else np.ones(len(xs) - 1, dtype=bool)
        ha = (hs[:-1] + hs[1:]) >= -1e-9
        cl = av.astype(np.int8) * 2 + ha.astype(np.int8)
        coupures = np.flatnonzero(np.diff(cl)) + 1
        debuts = np.concatenate(([0], coupures))
        fins = np.concatenate((coupures, [len(cl)]))
        col = c(couleur) if isinstance(couleur, str) else QColor(couleur)
        for d, f in zip(debuts.tolist(), fins.tolist()):
            devant, dessus = bool(av[d]), bool(ha[d])
            if not self._garder(dessus) or (not devant and arriere == 'cache'):
                continue
            pen_col = QColor(col)
            a = alpha if (devant or arriere == 'normal') else alpha * 0.45
            pen_col.setAlphaF(max(0.0, min(1.0, a * col.alphaF())))
            pen = QPen(pen_col, epaisseur if devant else max(1.0, epaisseur * 0.7))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            if not devant and arriere == 'pointille':
                pen.setStyle(Qt.PenStyle.DashLine)
            self.p.setPen(pen)
            self.p.drawPolyline(polygone(xs[d:f + 1], ys[d:f + 1]))

    def point(self, v, couleur, rayon_px: float = 5.0, repere_monde: bool = False, etiquette: str | None = None,
              decal=(10, -10), bord=None, toujours: bool = False):
        xs, ys, zs, hs = self.ecran(v, repere_monde)
        if not toujours and not self._garder(hs[0] >= -1e-9):
            return None
        av = zs[0] >= 0
        if isinstance(couleur, str) and couleur in ASTRES and rayon_px >= 3.5:
            astre(self.p, xs[0], ys[0], rayon_px, couleur, bord, 1.0 if av else 0.4)
        else:
            col = c(couleur) if isinstance(couleur, str) else QColor(couleur)
            if not av:
                col.setAlphaF(col.alphaF() * 0.4)
            self.p.setPen(stylo(bord, 1.0) if bord else Qt.PenStyle.NoPen)
            self.p.setBrush(QBrush(col))
            self.p.drawEllipse(QPointF(xs[0], ys[0]), rayon_px, rayon_px)
        reserver(self.p, xs[0], ys[0], rayon_px + 1)
        if etiquette:
            texte(self.p, xs[0] + decal[0], ys[0] + decal[1], etiquette, alpha=1.0 if av else 0.5, fond=True)
        return xs[0], ys[0], av

    def etiquette(self, v, s: str, cle: str = 'texte', repere_monde: bool = False, toujours: bool = True):
        xs, ys, zs, hs = self.ecran(v, repere_monde)
        if not toujours and not self._garder(hs[0] >= -1e-9):
            return
        texte(self.p, xs[0], ys[0], s, cle, alpha=1.0 if zs[0] >= 0 else 0.5, fond=True)

    def segment(self, a, b, couleur, epaisseur=1.5, alpha=1.0, repere_monde=False):
        self.courbe(np.vstack([a, b]), couleur, epaisseur, alpha, arriere='normal', repere_monde=repere_monde,
                    profondeur=False)

    def contour(self, cle='grille', remplir: str | None = 'sphere', alpha_remplir: float = 0.35):
        self.p.setPen(stylo(cle, 1.2))
        self.p.setBrush(c(remplir, alpha_remplir) if remplir else Qt.BrushStyle.NoBrush)
        self.p.drawEllipse(QPointF(self.cx, self.cy), self.r, self.r)

    def plan(self, couleur='sol', alpha=0.55, rayon: float = 1.0, bord='horizon', repere_monde: bool = True):
        """Disque du plan z = 0 (horizon, plan de l'orbite…)."""
        t = np.linspace(0, 2 * math.pi, 121)
        pts = np.stack([rayon * np.cos(t), rayon * np.sin(t), np.zeros_like(t)], axis=1)
        xs, ys, _, _ = self.ecran(pts, repere_monde)
        poly = QPolygonF([QPointF(x, y) for x, y in zip(xs, ys)])
        self.p.setPen(stylo(bord, 1.2) if bord else Qt.PenStyle.NoPen)
        self.p.setBrush(c(couleur, alpha))
        self.p.drawPolygon(poly)

    def depuis_ecran(self, x: float, y: float):
        """Point de la face avant de la sphère sous le pixel (x, y), dans le repère monde, ou None."""
        u = (x - self.cx) / self.r
        v = -(y - self.cy) / self.r
        w2 = 1 - u * u - v * v
        if w2 < 0:
            return None
        w = math.sqrt(w2)
        return u * self.vue.droite + v * self.vue.haut + w * self.vue.d


def hemisphere_nuit(pe: 'Peintre3D', soleil, couleur='nuit', alpha: float = 0.6):
    """Ombre la moitié de la sphère opposée à la direction `soleil` (repère monde) : demi-ellipse du terminateur
    visible, fermée par le bord du disque du côté opposé au Soleil."""
    s = np.asarray(soleil, dtype=float)
    s = s / np.linalg.norm(s)
    d = pe.vue.d
    a = np.cross(s, d)
    pe.p.save()
    pe.p.setPen(Qt.PenStyle.NoPen)
    pe.p.setBrush(c(couleur, alpha))
    if np.linalg.norm(a) < 1e-6:
        if float(s @ d) < 0:
            pe.p.drawEllipse(QPointF(pe.cx, pe.cy), pe.r, pe.r)
        pe.p.restore()
        return
    a = a / np.linalg.norm(a)
    b = np.cross(s, a)
    if float(b @ d) < 0:
        b = -b
    cc = np.cross(d, a)
    cc = cc / np.linalg.norm(cc)
    if float(cc @ s) > 0:
        cc = -cc
    t = np.linspace(0.0, math.pi, 61)
    terminateur = np.cos(t)[:, None] * a + np.sin(t)[:, None] * b          # de a à −a, face avant
    limbe = -np.cos(t)[:, None] * a + np.sin(t)[:, None] * cc             # de −a à a, côté nuit
    pts = np.vstack([terminateur, limbe])
    x, y, _ = pe.vue.projeter(pts)
    pe.p.drawPolygon(QPolygonF([QPointF(pe.cx + pe.r * u, pe.cy - pe.r * v) for u, v in zip(x, y)]))
    pe.p.restore()


def scene_en_deux_passes(pe: Peintre3D, dessiner, plan=None):
    """Appelle dessiner(pe) sous le plan, dessine le plan (fonction sans argument), puis dessiner(pe) au-dessus."""
    pe.passe = 'dessous'
    dessiner(pe)
    if plan is not None:
        plan()
    pe.passe = 'dessus'
    dessiner(pe)
    pe.passe = None


def zones(rect: QRectF, n: int, rapport_min: float = 0.8):
    """Partage `rect` en n panneaux côte à côte si la place le permet (largeur ≥ n × hauteur × rapport_min),
    sinon les uns sous les autres, ou en grille 2 × k pour n ≥ 3."""
    w, h = rect.width(), rect.height()
    if n <= 1:
        return [QRectF(rect)]
    if w >= n * h * rapport_min:
        lw = w / n
        return [QRectF(rect.x() + i * lw, rect.y(), lw, h) for i in range(n)]
    if n >= 3 and w >= h * 0.9:
        cols = 2
        lignes = (n + 1) // 2
        lw, lh = w / cols, h / lignes
        return [QRectF(rect.x() + (i % cols) * lw, rect.y() + (i // cols) * lh, lw, lh) for i in range(n)]
    lh = h / n
    return [QRectF(rect.x(), rect.y() + i * lh, w, lh) for i in range(n)]


def zones_principale(rect: QRectF, n_secondaires: int = 2, part: float = 0.56):
    """Une grande zone et `n_secondaires` petites empilées à côté (ou, si la place est haute et étroite, toutes
    empilées) : rend [grande, petite 1, petite 2…]."""
    w, h = rect.width(), rect.height()
    if w < h * 1.1:
        return zones(rect, 1 + n_secondaires, 10.0)
    gw = w * part
    out = [QRectF(rect.x(), rect.y(), gw, h)]
    lh = h / n_secondaires
    out += [QRectF(rect.x() + gw, rect.y() + i * lh, w - gw, lh) for i in range(n_secondaires)]
    return out


def cadre(p, r: QRectF, titre: str | None = None):
    """Fond arrondi d'un panneau, avec son titre en haut à gauche ; rend le rectangle utile.  Un nouveau panneau
    oublie la source de lumière des astres."""
    oublier_lumiere()
    p.save()
    p.setPen(stylo('grille', 1.0, 0.8))
    p.setBrush(c('sphere', 0.18))
    p.drawRoundedRect(r.adjusted(3, 3, -3, -3), 10, 10)
    p.restore()
    if titre:
        police(p, 0.95, gras=True)
        texte(p, r.x() + 12, r.y() + 8 + p.fontMetrics().ascent(), titre, centre=False)
        police(p, 1 / 0.95)
        return r.adjusted(8, 10 + p.fontMetrics().height(), -8, -8)
    return r.adjusted(8, 8, -8, -8)


def disque_phase(p, x: float, y: float, r: float, i: float, direction_soleil: float = 0.0, cle_eclairee='lune',
                 cle_sombre='nuit'):
    """Disque d'un corps vu sous l'angle de phase `i` (0 : plein, 180 : nouveau), le limbe éclairé tourné vers la
    direction `direction_soleil` de l'écran (degrés, sens trigonométrique depuis la droite, y vers le haut)."""
    phase_lune(p, x, y, r, 180.0 - max(0.0, min(180.0, i)), cle_eclairee, cle_sombre, rotation=-direction_soleil)


def graduations(p, x0: float, x1: float, y: float, valeurs, positions, cle: str = 'doux', haut: bool = False):
    """Petites graduations étiquetées le long d'un axe horizontal (valeurs : textes, positions : abscisses)."""
    p.setPen(stylo('grille', 1.0))
    for s, x in zip(valeurs, positions):
        if x0 - 1 <= x <= x1 + 1:
            p.drawLine(QPointF(x, y), QPointF(x, y + (-4 if haut else 4)))
            texte(p, x, y + (-12 if haut else 13), s, cle)
