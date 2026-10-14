"""Moteur de rendu des schémas déclaratifs (« coupole-schema/1 ») en QPainter : même calcul que src/contenu/schema_svg.ts
de Coupole Web (portage de rendu_svg.py, l'implémentation de référence des ressources), avec la mesure réelle des
textes (QFontMetricsF) pour les marges des axes et le cadre de vue, et le même contrôle de non-recouvrement.

Repère : origine en haut à gauche, y vers le bas ; angles en degrés dans le sens trigonométrique VU À L'ÉCRAN.
Mise à l'échelle uniforme du cadre de vue dans le widget (comme viewBox + xMidYMid meet)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QSizePolicy, QWidget

from ....core.i18n import langue
from .. import formule

PALETTE = {
    'clair': {'fond': '#ffffff', 'fond2': '#eef1f5', 'texte': '#1d232b', 'trait': '#2b3440', 'fin': '#6b7684',
              'grille': '#d5dbe2', 'accent': '#c2410c', 'accent2': '#1d4ed8', 'accent3': '#15803d', 'soleil': '#f59e0b',
              'terre': '#2563eb', 'lune': '#9ca3af', 'planete': '#b45309', 'etoile': '#a16207', 'ombre': '#374151',
              'penombre': '#9ca3af', 'froid': '#2563eb', 'chaud': '#dc2626', 'eau': '#0ea5e9'},
    'sombre': {'fond': '#11161c', 'fond2': '#1c242e', 'texte': '#e6eaef', 'trait': '#cfd6de', 'fin': '#8d99a6',
               'grille': '#2f3a46', 'accent': '#fb923c', 'accent2': '#60a5fa', 'accent3': '#4ade80', 'soleil': '#fbbf24',
               'terre': '#60a5fa', 'lune': '#cbd5e1', 'planete': '#f59e0b', 'etoile': '#fde68a', 'ombre': '#0b0f14',
               'penombre': '#4b5563', 'froid': '#60a5fa', 'chaud': '#f87171', 'eau': '#38bdf8'},
}
TEXTUELS = ('titre_axe', 'graduation', 'texte', 'formule')


def largeur_estimee(t: str, taille: float, gras: bool = False) -> float:
    """Table de chasses de rendu_svg.py (sans Qt : tests)."""
    w = 0.0
    for c in t:
        if c in '0123456789':
            w += 0.56
        elif c == ' ':
            w += 0.28
        elif c in '  ':
            w += 0.18
        elif c in "il.,;:|!'’ıjfrtI":
            w += 0.3
        elif c in 'mwMWœŒ':
            w += 0.85
        elif c in '⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺₀₁₂₃₄₅₆₇₈₉ᵣₜ':
            w += 0.36
        elif c.isupper():
            w += 0.66
        else:
            w += 0.55
    return w * taille * (1.07 if gras else 1.0)


_POLICES: dict = {}


def mesure_reelle(t: str, taille: float, gras: bool = False) -> float:
    """Largeur réelle (QFontMetricsF) dans la police de l'application, à la taille donnée en pixels."""
    k = (round(taille * 4), gras)
    fm = _POLICES.get(k)
    if fm is None:
        from ....gui.theme import police          # la police de Coupole (pas celle du système, qui varie)
        f = police()
        f.setPixelSize(max(1, int(round(taille))))
        f.setBold(gras)
        fm = _POLICES[k] = QFontMetricsF(f)
    return fm.horizontalAdvance(t) * (taille / max(1, int(round(taille))))


def mesure_affichee(t: str, taille: float, gras: bool = False) -> float:
    """Largeur à l'écran : la mesure réelle, jamais plus large que la chasse estimée (0.7.0).  Un texte plus large
    dans la police du système (Segoe UI, SF Pro, DejaVu…) que la table de chasses est resserré horizontalement au
    dessin : la mise en page, vérifiée sans recouvrement avec la table, le reste sur tous les systèmes."""
    return min(mesure_reelle(t, taille, gras), largeur_estimee(t, taille, gras))


def _texte(v, lg):
    return str(v.get(lg, '')) if isinstance(v, dict) else ('' if v is None else str(v))


def nombre_axe(v, lg) -> str:
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e16:
        v = int(v)
    s = str(v)
    if isinstance(v, int) and abs(v) >= 10000:
        s = ('-' if v < 0 else '') + f'{abs(v):,}'.replace(',', ' ')
    if lg == 'fr':
        s = s.replace('.', ',')
    return s.replace('-', '−')


def boite_texte(txt, taille, x, y, ancre='m', base='milieu', rot=0, gras=False, mesure=largeur_estimee):
    lignes = txt.split('\n')
    w = max(mesure(li, taille, gras) for li in lignes)
    hh = taille * 1.2 * len(lignes)
    x0 = {'g': x, 'm': x - w / 2, 'd': x - w}[ancre]
    if len(lignes) > 1 and base == 'milieu':
        y0 = y - hh / 2
    else:
        y0 = {'haut': y, 'milieu': y - hh / 2, 'bas': y - taille * 0.95}[base]
    b = (x0, y0, x0 + w, y0 + hh)
    if rot:
        a = math.radians(-rot)
        pts = [(px, py) for px in (b[0], b[2]) for py in (b[1], b[3])]
        q = [(x + (px - x) * math.cos(a) - (py - y) * math.sin(a), y + (px - x) * math.sin(a) + (py - y) * math.cos(a))
             for px, py in pts]
        b = (min(p[0] for p in q), min(p[1] for p in q), max(p[0] for p in q), max(p[1] for p in q))
    return b


class _Carte:
    def __init__(self, r):
        self.x0, self.y0, self.l, self.h = r['cadre']
        self.ax, self.ay = r['x'], r['y']

    @staticmethod
    def _t(v, a):
        if a.get('log'):
            return (math.log10(v) - math.log10(a['min'])) / (math.log10(a['max']) - math.log10(a['min']))
        return (v - a['min']) / (a['max'] - a['min'])

    def __call__(self, p):
        return self.x0 + self._t(p[0], self.ax) * self.l, self.y0 + self.h - self._t(p[1], self.ay) * self.h


def _cles_python(v):
    """Clés d'étiquettes d'axes écrites par Python (str d'un float ou d'un int)."""
    out = [repr(v), str(v)]
    if isinstance(v, (int, float)) and float(v).is_integer() and abs(v) < 1e16:
        out += [str(int(v)), str(int(v)) + '.0']
    return out


def _etiquette(etiq, v):
    if not etiq:
        return None
    for k in _cles_python(v):
        if k in etiq:
            return etiq[k]
    return None


def rendre(s: dict, lg: str | None = None, mesure=largeur_estimee):
    """Opérations de dessin, géométrie (contrôles) et cadre de vue (x, y, l, h) du schéma."""
    lg = lg or langue()
    ops, G, cartes = [], [], {}
    for el in s['elements']:
        t = el['t']
        m = cartes.get(el.get('repere')) if el.get('repere') else None
        P = m if m else (lambda p: (p[0], p[1]))
        st = el.get('style') or {}
        if t == 'repere':
            mp = _Carte(el)
            cartes[el['id']] = mp
            _axes(el, mp, lg, G, ops, mesure)
        elif t in ('ligne', 'poly'):
            pts = [P(p) for p in el['p']]
            ops.append(('poly', pts, st, t == 'poly' and bool(el.get('ferme'))))
            G.append({'genre': 'courbe' if el.get('repere') and not st.get('tirets') else 'trait', 'pts': pts,
                      'repere': el.get('repere'), 'fond': bool(st.get('fond'))})
        elif t in ('cercle', 'point'):
            x, y = P(el['c'] if t == 'cercle' else el['p'])
            ops.append(('ellipse', x, y, el['r'], el['r'], 0, st))
        elif t == 'ellipse':
            x, y = P(el['c'])
            ops.append(('ellipse', x, y, el['rx'], el['ry'], el.get('rot', 0), st))
        elif t == 'arc':
            (cx, cy), r = P(el['c']), el['r']
            ops.append(('arc', cx, cy, r, el['a0'], el['a1'], st))
        elif t == 'rect':
            x, y = P(el['p'])
            ops.append(('rect', x, y, el['l'], el['h'], el.get('rayon', 0), st))
        elif t == 'texte':
            x, y = P(el['p'])
            txt = _texte(el['txt'], lg)
            taille = el.get('taille', 14)
            G.append({'genre': 'texte', 'boite': boite_texte(txt, taille, x, y, el.get('ancre', 'm'), el.get('base', 'milieu'),
                                                             el.get('rot', 0), bool(el.get('gras')), mesure),
                      'repere': el.get('repere'), 'txt': txt})
            ops.append(('texte', x, y, txt, taille, el.get('ancre', 'm'), el.get('base', 'milieu'), el.get('couleur', 'texte'),
                        bool(el.get('gras')), bool(el.get('italique')), el.get('rot', 0)))
        elif t == 'formule':
            x, y = P(el['p'])
            ta = el.get('taille', 16)
            src = _texte(el['src'], lg)
            fw = 0.5 * ta * len(src.replace(' ', '')) + 0.25 * ta * src.count(' ')
            fh = ta * (2.2 if '/' in src else 1.3)
            an, ba = el.get('ancre', 'm'), el.get('base', 'milieu')
            fx = {'g': x, 'm': x - fw / 2, 'd': x - fw}[an]
            fy = {'haut': y, 'milieu': y - fh / 2, 'bas': y - fh}[ba]
            G.append({'genre': 'formule', 'boite': (fx, fy, fx + fw, fy + fh), 'repere': el.get('repere'), 'txt': src})
            ops.append(('formule', x, y, src, ta, an, ba, el.get('couleur', 'texte')))
        elif t == 'spectre':
            ops.append(('spectre', el))
        else:
            raise ValueError('élément de schéma inconnu : %s' % t)
    return ops, G, _vue(s, G)


def _vue(s, G):
    l, h = s['taille']
    x0, y0, x1, y1 = 0.0, 0.0, float(l), float(h)
    if isinstance(s.get('vue'), list):
        x0, y0 = s['vue'][0], s['vue'][1]
        x1, y1 = x0 + s['vue'][2], y0 + s['vue'][3]
    for g in G:
        if g['genre'] in TEXTUELS:
            b = g['boite']
            x0, y0, x1, y1 = min(x0, b[0] - 4), min(y0, b[1] - 4), max(x1, b[2] + 4), max(y1, b[3] + 4)
    return (round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1))


def _axes(r, mp, lg, G, ops, mesure):
    x0, y0, l, h = r['cadre']
    T_GRAD, T_TITRE = 12, 13
    larg_max = 0.0
    for nom in ('x', 'y'):
        a = r[nom]
        for v in a.get('grad', []):
            lab = _etiquette(a.get('etiq'), v)
            lab = _texte(lab, lg) if lab is not None else nombre_axe(v, lg)
            if nom == 'x':
                X, _ = mp((v, r['y']['min']))
                if r.get('grille'):
                    ops.append(('ligne', X, y0, X, y0 + h, 'grille', 1))
                ops.append(('ligne', X, y0 + h, X, y0 + h + 5, 'trait', 1))
                ops.append(('texte', X, y0 + h + 8, lab, T_GRAD, 'm', 'haut', 'texte', False, False, 0))
                G.append({'genre': 'graduation', 'boite': boite_texte(lab, T_GRAD, X, y0 + h + 8, 'm', 'haut', 0, False, mesure),
                          'repere': r['id'], 'txt': lab})
            else:
                _, Y = mp((r['x']['min'], v))
                if r.get('grille'):
                    ops.append(('ligne', x0, Y, x0 + l, Y, 'grille', 1))
                ops.append(('ligne', x0 - 5, Y, x0, Y, 'trait', 1))
                ops.append(('texte', x0 - 8, Y, lab, T_GRAD, 'd', 'milieu', 'texte', False, False, 0))
                larg_max = max(larg_max, mesure(lab, T_GRAD))
                G.append({'genre': 'graduation', 'boite': boite_texte(lab, T_GRAD, x0 - 8, Y, 'd', 'milieu', 0, False, mesure),
                          'repere': r['id'], 'txt': lab})
    if not r['y'].get('cache'):
        ops.append(('ligne', x0, y0, x0, y0 + h, 'trait', 1.5))
    if not r['x'].get('cache'):
        ops.append(('ligne', x0, y0 + h, x0 + l, y0 + h, 'trait', 1.5))
    if r['x'].get('titre'):
        yt = y0 + h + 8 + (T_GRAD * 1.2 if r['x'].get('grad') else 0) + 6
        tt = _texte(r['x']['titre'], lg)
        ops.append(('texte', x0 + l / 2, yt, tt, T_TITRE, 'm', 'haut', 'texte', False, False, 0))
        G.append({'genre': 'titre_axe', 'boite': boite_texte(tt, T_TITRE, x0 + l / 2, yt, 'm', 'haut', 0, False, mesure),
                  'repere': r['id'], 'txt': tt})
    if r['y'].get('titre'):
        tt = _texte(r['y']['titre'], lg)
        X = x0 - 8 - larg_max - 8 - T_TITRE * 0.6          # à gauche de la PLUS LARGE graduation (mesurée)
        Y = y0 + h / 2
        ops.append(('texte', X, Y, tt, T_TITRE, 'm', 'milieu', 'texte', False, False, 90))
        G.append({'genre': 'titre_axe', 'boite': boite_texte(tt, T_TITRE, X, Y, 'm', 'milieu', 90, False, mesure),
                  'repere': r['id'], 'txt': tt})


def _inter(a, b, marge=1.0):
    return a[0] + marge < b[2] and b[0] + marge < a[2] and a[1] + marge < b[3] and b[1] + marge < a[3]


def _seg_boite(p, q, b, marge=1.0):
    x0, y0, x1, y1 = b[0] + marge, b[1] + marge, b[2] - marge, b[3] - marge
    if x0 >= x1 or y0 >= y1:
        return False
    n = max(2, int(math.hypot(q[0] - p[0], q[1] - p[1]) / 2))
    for i in range(n + 1):
        t = i / n
        x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if x0 < x < x1 and y0 < y < y1:
            return True
    return False


def recouvrements(s: dict, lg: str, mesure=largeur_estimee) -> list:
    """Contrôle repris de rendu_svg.recouvrements : textes sans recouvrement, courbes hors des titres et graduations."""
    _, G, _ = rendre(s, lg, mesure)
    tx = [g for g in G if g['genre'] in TEXTUELS]
    pb = []
    for i, a in enumerate(tx):
        for b in tx[i + 1:]:
            if _inter(a['boite'], b['boite']):
                pb.append('%s « %s » recouvre %s « %s »' % (a['genre'], a['txt'][:30], b['genre'], b['txt'][:30]))
    for c in (g for g in G if g['genre'] == 'courbe' and not g['fond']):
        for a in tx:
            if a['genre'] in ('titre_axe', 'graduation') or (a['repere'] and a['repere'] == c['repere']):
                if any(_seg_boite(p, q, a['boite']) for p, q in zip(c['pts'], c['pts'][1:])):
                    pb.append('courbe du repère %s traverse %s « %s »' % (c['repere'], a['genre'], a['txt'][:30]))
                    break
    return pb


def couleur_onde(nm: float) -> QColor:
    w = nm
    if 380 <= w < 440:
        r, g, b = -(w - 440) / 60, 0.0, 1.0
    elif 440 <= w < 490:
        r, g, b = 0.0, (w - 440) / 50, 1.0
    elif 490 <= w < 510:
        r, g, b = 0.0, 1.0, -(w - 510) / 20
    elif 510 <= w < 580:
        r, g, b = (w - 510) / 70, 1.0, 0.0
    elif 580 <= w < 645:
        r, g, b = 1.0, -(w - 645) / 65, 0.0
    elif 645 <= w <= 780:
        r, g, b = 1.0, 0.0, 0.0
    else:
        return QColor('#808080')
    f = 0.3 + 0.7 * (w - 380) / 40 if w < 420 else (0.3 + 0.7 * (780 - w) / 80 if w > 700 else 1.0)
    return QColor(*(int(round(255 * (c * f) ** 0.8)) if c > 0 else 0 for c in (r, g, b)))


# ------------------------------------------------------------------ peinture
def peindre(p: QPainter, s: dict, cible: QRectF, theme: str = 'sombre', lg: str | None = None):
    """Dessine le schéma dans `cible` (mise à l'échelle uniforme, centrée)."""
    pal = PALETTE['clair' if theme == 'clair' else 'sombre']
    ops, _, (vx, vy, vl, vh) = rendre(s, lg, mesure_affichee)
    k = min(cible.width() / max(vl, 1e-6), cible.height() / max(vh, 1e-6))
    ox = cible.x() + (cible.width() - vl * k) / 2
    oy = cible.y() + (cible.height() - vh * k) / 2

    def col(j, alpha=None):
        c = QColor('#00000000') if j in (None, 'none') else QColor(pal.get(j, j if str(j).startswith('#') else pal['trait']))
        if alpha is not None:
            c.setAlphaF(float(alpha))
        return c

    def stylo(st, defaut='trait'):
        pen = QPen(col(st.get('trait', defaut), st.get('opacite')), float(st.get('ep', 1.5)))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        if st.get('tirets'):
            ep = float(st.get('ep', 1.5)) or 1
            pen.setDashPattern([max(0.1, x / ep) for x in st['tirets']])
        return pen

    def brosse(st):
        return QBrush(col(st['fond'], st.get('opacite'))) if st.get('fond') else Qt.BrushStyle.NoBrush

    def tete(a, b, st):
        ep = st.get('ep', 1.5)
        L = 6 + 3 * ep
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        poly = QPolygonF([QPointF(*b), QPointF(b[0] - L * math.cos(ang - 0.4), b[1] - L * math.sin(ang - 0.4)),
                          QPointF(b[0] - L * math.cos(ang + 0.4), b[1] - L * math.sin(ang + 0.4))])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(col(st.get('trait', 'trait'), st.get('opacite')))
        p.drawPolygon(poly)

    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.translate(ox, oy)
    p.scale(k, k)
    p.translate(-vx, -vy)
    for op in ops:
        g = op[0]
        if g == 'poly':
            _, pts, st, ferme = op
            p.setPen(stylo(st))
            p.setBrush(brosse(st))
            poly = QPolygonF([QPointF(x, y) for x, y in pts])
            p.drawPolygon(poly) if ferme else p.drawPolyline(poly)
            f = st.get('fleche')
            if f in ('fin', 'deux') and len(pts) >= 2:
                tete(pts[-2], pts[-1], st)
            if f in ('debut', 'deux') and len(pts) >= 2:
                tete(pts[1], pts[0], st)
        elif g == 'ligne':
            _, x1, y1, x2, y2, c, ep = op
            p.setPen(QPen(col(c), ep))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        elif g == 'ellipse':
            _, x, y, rx, ry, rot, st = op
            p.setPen(stylo(st))
            p.setBrush(brosse(st))
            p.save()
            p.translate(x, y)
            p.rotate(-rot)
            p.drawEllipse(QPointF(0, 0), rx, ry)
            p.restore()
        elif g == 'arc':
            _, cx, cy, r, a0, a1, st = op
            p.setPen(stylo(st))
            p.setBrush(Qt.BrushStyle.NoBrush)
            if abs(a1 - a0) >= 360:
                p.drawEllipse(QPointF(cx, cy), r, r)
            else:
                p.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), int(round(a0 * 16)), int(round((a1 - a0) * 16)))
                if st.get('fleche'):
                    da = 0.05 if a1 > a0 else -0.05
                    b1 = math.radians(a1)
                    tete((cx + r * math.cos(b1 - da), cy - r * math.sin(b1 - da)), (cx + r * math.cos(b1), cy - r * math.sin(b1)), st)
        elif g == 'rect':
            _, x, y, w, h, rr, st = op
            p.setPen(stylo(st))
            p.setBrush(brosse(st))
            p.drawRoundedRect(QRectF(x, y, w, h), rr, rr)
        elif g == 'texte':
            _, x, y, txt, taille, ancre, base, c, gras, ital, rot = op
            f = QFont()
            f.setPixelSize(max(1, int(round(taille))))
            f.setBold(gras)
            f.setItalic(ital)
            p.setFont(f)
            p.setPen(col(c))
            fm = QFontMetricsF(f)
            lignes = txt.split('\n')
            dy = taille * 1.2
            p.save()
            p.translate(x, y)
            if rot:
                p.rotate(-rot)
            y0 = -dy * (len(lignes) - 1) / 2 if base == 'milieu' else 0
            for i, li in enumerate(lignes):
                w = fm.horizontalAdvance(li)
                k = min(1.0, largeur_estimee(li, taille, gras) / w) if w > 0 else 1.0   # voir mesure_affichee()
                xx = {'g': 0, 'm': -w * k / 2, 'd': -w * k}[ancre]
                yb = y0 + i * dy
                yy = {'haut': yb + fm.ascent(), 'milieu': yb + (fm.ascent() - fm.descent()) / 2, 'bas': yb}[base]
                if k < 1.0:
                    p.save()
                    p.translate(xx, yy)
                    p.scale(k, 1.0)
                    p.drawText(QPointF(0, 0), li)
                    p.restore()
                else:
                    p.drawText(QPointF(xx, yy), li)
            p.restore()
        elif g == 'formule':
            _, x, y, src, ta, an, ba, c = op
            f = QFont()
            f.setPixelSize(max(1, int(round(ta))))
            p.setFont(f)
            w = formule.largeur(p, src)
            xx = {'g': x, 'm': x - w / 2, 'd': x - w}[an]
            fm = QFontMetricsF(f)
            yy = {'haut': y + fm.ascent(), 'milieu': y + (fm.ascent() - fm.descent()) / 2, 'bas': y - fm.descent()}[ba]
            formule.dessiner(p, xx, yy, src, couleur=col(c))
        elif g == 'spectre':
            el = op[1]
            x, y = el['p']
            L, H, lmin, lmax = el['l'], el['h'], el['lmin'], el['lmax']
            if el.get('fond', 'continu') == 'continu':
                grad = QLinearGradient(x, 0, x + L, 0)
                for i in range(41):
                    grad.setColorAt(i / 40, couleur_onde(lmin + (lmax - lmin) * i / 40))
                p.fillRect(QRectF(x, y, L, H), QBrush(grad))
            else:
                p.fillRect(QRectF(x, y, L, H), QColor('#000000'))
            for rr in el.get('raies', []):
                xr = x + (rr['nm'] - lmin) / (lmax - lmin) * L
                ep = 1.5 + 2.5 * rr.get('force', 1)
                c2 = QColor('#000000') if rr['genre'] == 'absorption' else couleur_onde(rr['nm'])
                c2.setAlphaF(min(1.0, 0.4 + 0.6 * rr.get('force', 1)))
                p.fillRect(QRectF(xr - ep / 2, y, ep, H), c2)
    p.restore()


class SchemaWidget(QWidget):
    """Un schéma, redimensionnable (proportions gardées), thème de l'application, nom accessible."""

    def __init__(self, schema: dict, theme: str = 'sombre', parent=None):
        super().__init__(parent)
        self.schema = schema
        self.theme = theme
        _, _, (_, _, self._vl, self._vh) = rendre(schema, None, mesure_affichee)
        self.setAccessibleName(_texte(schema.get('titre'), langue()))
        self.setAccessibleDescription(_texte(schema.get('alt'), langue()))
        self.setToolTip(_texte(schema.get('alt'), langue()))
        pol = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        pol.setHeightForWidth(True)
        self.setSizePolicy(pol)
        self.setMinimumSize(160, 80)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return int(w * self._vh / max(1.0, self._vl))

    def sizeHint(self):
        return QSize(560, self.heightForWidth(560))

    def paintEvent(self, _):
        # thème suivi sur la palette du widget (texte clair sur fond sombre, ou l'inverse)
        theme = 'clair' if self.palette().window().color().lightness() > 128 else 'sombre'
        p = QPainter(self)
        peindre(p, self.schema, QRectF(self.rect()), theme)
        p.end()
