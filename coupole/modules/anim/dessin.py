"""Dessin des animations : projection orthographique d'une sphère (3D simple, calculée), couleurs selon le thème,
tracés en deux passes (sous puis sur un plan) et petits outils de QPainter.

Le repère « monde » d'une vue est direct : pour une sphère locale x = nord, y = ouest, z = zénith ; pour une sphère
céleste x = point vernal, y = 6 h, z = pôle nord.  Le point de vue est donné par son azimut (compté comme
l'azimut astronomique, depuis +x vers −y) et sa hauteur au-dessus du plan xy.
"""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen, QPolygonF

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


def c(cle: str, alpha: float | None = None) -> QColor:
    col = QColor(PALETTES[theme()][cle])
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


def texte(p, x: float, y: float, s: str, cle: str = 'texte', centre: bool = True, alpha: float | None = None,
          fond: bool = False):
    """Texte centré (ou aligné à gauche) au point (x, y) ; `fond` : petit cartouche sous le texte."""
    fm = p.fontMetrics()
    w, h = fm.horizontalAdvance(s), fm.height()
    x0 = x - w / 2 if centre else x
    y0 = y + fm.ascent() / 2 - 1 if centre else y
    if fond:
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c('fond', 0.75))
        p.drawRoundedRect(QRectF(x0 - 3, y0 - fm.ascent() - 1, w + 6, h + 2), 4, 4)
        p.restore()
    p.setPen(c(cle, alpha))
    p.drawText(QPointF(x0, y0), s)


def disque(p, x: float, y: float, r: float, cle_ou_couleur='soleil', bord=None, alpha: float | None = None):
    col = c(cle_ou_couleur, alpha) if isinstance(cle_ou_couleur, str) else cle_ou_couleur
    p.setBrush(QBrush(col))
    p.setPen(stylo(bord, 1.0) if bord else Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(x, y), r, r)


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
    p.setBrush(c(cle_sombre))
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
    p.setBrush(c(cle_eclairee))
    p.drawPath(chemin)
    p.setPen(stylo('doux', 1.0, 0.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(0, 0), r, r)
    p.restore()


# ==================================================================== projection d'une sphère
class Vue3D:
    """Point de vue d'une scène 3D (projection orthographique) : azimut et hauteur en degrés, bornés."""

    def __init__(self, az: float = 215.0, alt: float = 30.0, alt_min: float = -89.0, alt_max: float = 89.0):
        self.alt_min, self.alt_max = alt_min, alt_max
        self.defaut = (az, alt)
        self.regler(az, alt)

    def regler(self, az: float, alt: float):
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

    def tourner(self, dx_px: float, dy_px: float, sensibilite: float = 0.4):
        self.regler(self.az - dx_px * sensibilite, self.alt + dy_px * sensibilite)

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
            self.p.drawPolyline(QPolygonF(list(map(QPointF, xs[d:f + 1].tolist(), ys[d:f + 1].tolist()))))

    def point(self, v, couleur, rayon_px: float = 5.0, repere_monde: bool = False, etiquette: str | None = None,
              decal=(10, -10), bord=None, toujours: bool = False):
        xs, ys, zs, hs = self.ecran(v, repere_monde)
        if not toujours and not self._garder(hs[0] >= -1e-9):
            return None
        av = zs[0] >= 0
        col = c(couleur) if isinstance(couleur, str) else QColor(couleur)
        if not av:
            col.setAlphaF(col.alphaF() * 0.4)
        self.p.setPen(stylo(bord, 1.0) if bord else Qt.PenStyle.NoPen)
        self.p.setBrush(QBrush(col))
        self.p.drawEllipse(QPointF(xs[0], ys[0]), rayon_px, rayon_px)
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
    """Fond arrondi d'un panneau, avec son titre en haut à gauche ; rend le rectangle utile."""
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
