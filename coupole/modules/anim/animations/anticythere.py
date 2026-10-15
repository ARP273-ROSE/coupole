"""La machine d'Anticythère en 3D, adaptée d'Anticythere3D (du même auteur) : mêmes nombres de dents, mêmes trains,
mêmes rapports exacts, même implantation des arbres, mêmes cadrans gravés (``anticythere_meca``).  Même rendu que
Coupole Web (src/anim/animations/anticythere.ts).

Rendu sans OpenGL, en QPainter : projection orthographique maison, orientation par quaternion (garde-fous : jamais
d'orientation non finie ou non unitaire), algorithme du peintre.  Toutes les pièces sont planes et parallèles (roues,
plaques, aiguilles, cadrans) : chacune est dessinée dans son plan par une transformation affine exacte (projection
orthographique d'un plan), et les plans sont triés le long de la visée ; les arbres sont coupés en tronçons aux plans
des roues qui peuvent les recouvrir.  Le coffret fermé est convexe : seules ses faces tournées vers l'observateur sont
dessinées.  Cadrans gravés : dessin vectoriel (mêmes tracés que dialface.py) mis en cache dans une image dont la
résolution suit le zoom ; dentures remplacées par leur cercle primitif quand une dent ferait moins de 3 pixels."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QImage, QPainter, QPainterPath, QPen, QPolygonF,
                         QRadialGradient, QTransform)

from ....core.i18n import langue, tr
from .. import anticythere_meca as M
from .. import dessin
from ..base import Animation, angle, nombre

DEG = math.pi / 180.0


# ==================================================================== caméra : quaternion
def q_mul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return (w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2)


def q_axe(x, y, z, t):
    n = math.sqrt(x * x + y * y + z * z)
    if not (n > 1e-12) or not math.isfinite(t):
        return (1.0, 0.0, 0.0, 0.0)
    s = math.sin(t / 2) / n
    return (math.cos(t / 2), x * s, y * s, z * s)


def q_valide(q) -> bool:
    """Quaternion fini et unitaire à 1e-6 près."""
    try:
        return len(q) == 4 and all(math.isfinite(v) for v in q) and abs(math.sqrt(sum(v * v for v in q)) - 1) < 1e-6
    except TypeError:
        return False


def q_normer(q):
    n = math.sqrt(sum(v * v for v in q))
    if not math.isfinite(n) or n < 1e-9:
        return None
    r = tuple(v / n for v in q)
    return r if q_valide(r) else None


def q_matrice(q):
    """Lignes : axes de vue (droite, haut, vers l'observateur) dans le repère de la machine."""
    w, x, y, z = q
    return (1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
            2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
            2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y))


VUES = {'avant': (1.0, 0.0, 0.0, 0.0), 'arriere': q_axe(0, 1, 0, math.pi),
        'trois_quarts': q_mul(q_axe(1, 0, 0, 24 * DEG), q_axe(0, 1, 0, -34 * DEG))}


def tourner_camera(q, dx, dy, r, repli=VUES['avant']):
    """Glisser de (dx, dy) pixels : « boule de commande » autour de l'axe de l'écran perpendiculaire au glisser,
    d'angle |d| / r.  Entrées non finies ignorées ; résultat renormé et validé, sinon l'orientation de base."""
    base = q if q_valide(q) else repli
    try:
        d = math.hypot(dx, dy)
    except TypeError:
        return base
    if not math.isfinite(d) or not (r > 0) or not math.isfinite(r) or d < 1e-9:
        return base
    n = q_normer(q_mul(q_axe(dy / d, dx / d, 0, d / r), base))
    return n or base


# ==================================================================== couleurs
def rvb(c, a: float = 1.0) -> QColor:
    col = QColor(int(round(max(0, min(255, c[0])))), int(round(max(0, min(255, c[1])))),
                 int(round(max(0, min(255, c[2])))))
    col.setAlphaF(max(0.0, min(1.0, a)))
    return col


BRONZE_CLAIR = (226, 200, 140)
BRONZE_MOYEN = (198, 168, 106)
BRONZE_PALE = (236, 214, 160)
GRAVE = QColor(74, 58, 30)
GRAVE_DOUX = QColor(116, 96, 56)
BOIS = (102, 69, 38)
AIGUILLE_SOLEIL = (217, 166, 38)
AIGUILLE_LUNE = (204, 209, 219)


def couleur_sous_ensemble(sub: str, sombre: bool):
    """Couleur d'un sous-ensemble : celle d'Anticythere3D en thème clair, éclaircie en thème sombre."""
    c = M.COLORS.get(sub, M.COLORS['input'])
    return tuple(c) if not sombre else tuple(round(x + (255 - x) * 0.38) for x in c)


# ==================================================================== géométrie des roues
def contour_roue(n: int, module: float = M.MODULE) -> list:
    rp = module * n / 2
    ra, rf = rp + 0.55 * module, rp - 0.65 * module
    out = []
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 0.5) / n
        out += [(rf * math.cos(a0), rf * math.sin(a0)), (ra * math.cos(a1), ra * math.sin(a1))]
    return out


def _cercle(path: QPainterPath, r: float, n: int = 48, sens: int = 1):
    path.addPolygon(QPolygonF([QPointF(r * math.cos(sens * 2 * math.pi * i / n), r * math.sin(sens * 2 * math.pi * i / n))
                               for i in range(n + 1)]))
    path.closeSubpath()


_CHEMINS: dict = {}


def chemins_roue(nom: str):
    """(denture complète, cercle primitif) en QPainterPath (repère de la roue, mm) ; roues à bras évidées."""
    c = _CHEMINS.get(nom)
    if c:
        return c
    n = M.TEETH[nom]
    rp = M.MODULE * n / 2
    dents, cer = QPainterPath(), QPainterPath()
    dents.addPolygon(QPolygonF([QPointF(x, y) for x, y in contour_roue(n)]))
    dents.closeSubpath()
    _cercle(cer, rp + 0.2, max(24, min(64, n)))
    bras = M.SPOKED.get(nom)
    if bras:
        for p in (dents, cer):
            _cercle(p, rp * 0.86, 48, -1)
            for k in range(bras):
                a = 2 * math.pi * k / bras
                ca, sa = math.cos(a), math.sin(a)
                p.addPolygon(QPolygonF([QPointF(u * ca - v * sa, u * sa + v * ca)
                                        for u, v in ((6, -3.5), (rp * 0.87, -3.5), (rp * 0.87, 3.5), (6, 3.5), (6, -3.5))]))
                p.closeSubpath()
            _cercle(p, 9, 24)
    for p in (dents, cer):
        p.setFillRule(Qt.FillRule.OddEvenFill)
    c = (dents, cer)
    _CHEMINS[nom] = c
    return c


# ==================================================================== cadrans gravés (dialface.py)
def _police(p: QPainter, px: float, gras: bool = True):
    f = QFont(p.font())
    f.setPixelSize(max(1, int(px)))
    f.setBold(gras)
    p.setFont(f)
    return f


def _texte_anneau(p, cx, cy, rayon, angle_deg, s, px, couleur):
    """Texte le long d'un rayon, tourné pour suivre le cercle (repère y vers le bas)."""
    p.save()
    p.translate(cx, cy)
    rot = (90.0 - angle_deg) % 360.0
    renverse = 90.0 < rot < 270.0
    p.rotate(-angle_deg + 90.0 + (180.0 if renverse else 0.0))
    f = _police(p, px)
    p.setPen(couleur)
    w = QFontMetricsF(f).horizontalAdvance(s)
    p.drawText(QPointF(-w / 2, rayon + px * 0.8 if renverse else -rayon), s)
    p.restore()


def _trait(p, x0, y0, x1, y1, couleur, e):
    p.setPen(QPen(couleur, e))
    p.drawLine(QPointF(x0, y0), QPointF(x1, y1))


def _rond(p, cx, cy, r, couleur, e, fond=None):
    p.setPen(QPen(couleur, e) if couleur is not None else Qt.PenStyle.NoPen)
    p.setBrush(QBrush(fond) if fond is not None else Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(cx, cy), max(0.0, r), max(0.0, r))


def _degrade(cx, cy, R, k=1.3, arrets=((0.0, (242, 222, 172)), (0.65, BRONZE_CLAIR), (1.0, BRONZE_MOYEN))):
    g = QRadialGradient(cx, cy - R * 0.2, R * k)
    for t, col in arrets:
        g.setColorAt(t, rvb(col))
    return g


def peindre_face_avant(p, cx, cy, R, lg):
    """Face avant sans l'anneau calendaire mobile : zodiaque (360 divisions, noms grecs), plage centrale."""
    s = R / 0.485
    rzo, rzi, rface = R * 0.825, R * 0.63, R * 0.61
    _rond(p, cx, cy, R * 0.845, GRAVE_DOUX, s * 0.004, _degrade(cx, cy, R))
    for r in (rzi, rzo):
        _rond(p, cx, cy, r, GRAVE, s * 0.0035)
    for d in range(360):
        a = (90 - d) * DEG
        if d % 30 == 0:
            r0, e, col = rzi, 0.0026, GRAVE
        elif d % 5 == 0:
            r0, e, col = rzo - (rzo - rzi) * 0.38, 0.0014, GRAVE
        else:
            r0, e, col = rzo - (rzo - rzi) * 0.2, 0.0008, GRAVE_DOUX
        _trait(p, cx + r0 * math.cos(a), cy - r0 * math.sin(a), cx + rzo * math.cos(a), cy - rzo * math.sin(a), col, s * e)
    for i, (grec, fr, en) in enumerate(M.ZODIAC_GREEK):
        a = 90 - 30 * (i + 0.5)
        _texte_anneau(p, cx, cy, (rzi + rzo) / 2 + s * 0.01, a, grec, s * 0.017, GRAVE)
        _texte_anneau(p, cx, cy, (rzi + rzo) / 2 - s * 0.016, a, fr if lg == 'fr' else en, s * 0.011, GRAVE_DOUX)
        _texte_anneau(p, cx, cy, rzi + s * 0.012, 90 - 30 * i - 2, M.PARAPEGMA_LETTERS[i % len(M.PARAPEGMA_LETTERS)],
                      s * 0.012, GRAVE_DOUX)
    _rond(p, cx, cy, rface, GRAVE_DOUX, s * 0.0022, rvb(BRONZE_PALE))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(150, 170, 140, 24))
    for dx, dy, rr in ((-0.26, -0.34, 0.1), (0.3, 0.2, 0.06), (-0.4, 0.38, 0.045)):
        p.drawEllipse(QPointF(cx + s * dx, cy + s * dy), s * rr, s * rr * 0.8)


def peindre_anneau_calendrier(p, cx, cy, R):
    """Anneau calendaire égyptien (mobile) : 365 traits, mois de 30 jours nommés, 5 jours épagomènes."""
    s = R / 0.485
    ro, ri = R, R * 0.845
    anneau = QPainterPath()
    anneau.addEllipse(QPointF(cx, cy), ro, ro)
    anneau.addEllipse(QPointF(cx, cy), ri, ri)
    anneau.setFillRule(Qt.FillRule.OddEvenFill)
    p.fillPath(anneau, QBrush(_degrade(cx, cy, R)))
    for r in (ri, ro):
        _rond(p, cx, cy, r, GRAVE, s * 0.0035)
    for i in range(365):
        a = (90 - 360 * i / 365) * DEG
        long_ = i % 30 == 0
        r0 = ri if long_ else ro - (ro - ri) * 0.42
        _trait(p, cx + r0 * math.cos(a), cy - r0 * math.sin(a), cx + ro * math.cos(a), cy - ro * math.sin(a),
               GRAVE if long_ else GRAVE_DOUX, s * (0.0022 if long_ else 0.0011))
    for i in range(12):
        _texte_anneau(p, cx, cy, (ri + ro) / 2 - s * 0.006, 90 - 360 * (30 * i + 15) / 365, M.EGYPTIAN_GREEK[i],
                      s * 0.0195, GRAVE)
    _texte_anneau(p, cx, cy, (ri + ro) / 2 - s * 0.006, 90 - 360 * 362.5 / 365, 'Ε', s * 0.0195, GRAVE_DOUX)


def _texte_centre(p, x, y, s):
    fm = QFontMetricsF(p.font())
    p.drawText(QPointF(x - fm.horizontalAdvance(s) / 2, y + (fm.ascent() - fm.descent()) / 2), s)


def _spirale(p, cx, cy, s, turns, cells, r0, r1, titre, texte_case, forts, titre_dessous):
    n = 1400
    pts = []
    for i in range(n + 1):
        t = turns * 2 * math.pi * i / n
        r = r0 + (r1 - r0) * i / n
        pts.append(QPointF(cx + r * math.cos(t - math.pi / 2), cy - r * math.sin(t - math.pi / 2)))
    p.setPen(QPen(GRAVE, s * 0.0032))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolyline(QPolygonF(pts))
    couloir = (r1 - r0) / turns
    w = couloir * 0.42
    dth = turns * 2 * math.pi / cells
    for k in range(cells):
        a = dth * k - math.pi / 2
        r = r0 + (r1 - r0) * k / cells
        fort = k in forts
        _trait(p, cx + (r - w) * math.cos(a), cy - (r - w) * math.sin(a), cx + (r + w) * math.cos(a),
               cy - (r + w) * math.sin(a), GRAVE if fort else GRAVE_DOUX, s * (0.002 if fort else 0.0009))
    if texte_case is not None:
        p.setPen(GRAVE)
        for k in range(cells):
            v = texte_case(k)
            if not v:
                continue
            txt, gras = v
            t = dth * (k + 0.5)
            r = r0 + (r1 - r0) * (k + 0.5) / cells + couloir * 0.27
            arc = r * dth
            px = min(couloir * 0.42, arc / len(txt) * 1.45)
            if px < 2.0:
                continue
            a = t - math.pi / 2
            p.save()
            p.translate(cx + r * math.cos(a), cy - r * math.sin(a))
            deg = -math.degrees(a) - 90.0
            if 90 < deg % 360 < 270:
                deg += 180
            p.rotate(deg)
            _police(p, math.floor(px), gras)
            _texte_centre(p, 0, 0, txt)
            p.restore()
    _police(p, math.floor(s * 0.016))
    p.setPen(GRAVE)
    _texte_centre(p, cx, cy + (r1 + s * 0.006 if titre_dessous else -r1 - s * 0.03) + s * 0.013, titre)


def _petit_cadran(p, cx, cy, s, rad, secteurs, etiquettes, titre, titre_dessus):
    _rond(p, cx, cy, rad, GRAVE, s * 0.0026, rvb(BRONZE_PALE))
    for k in range(secteurs):
        a = (90 - 360 * k / secteurs) * DEG
        _trait(p, cx, cy, cx + rad * math.cos(a), cy - rad * math.sin(a), GRAVE_DOUX, s * 0.0014)
    p.setPen(GRAVE)
    _police(p, math.floor(rad * 0.155))
    for k, txt in enumerate(etiquettes):
        a = (90 - 360 * (k + 0.5) / secteurs) * DEG
        _texte_centre(p, cx + rad * 0.58 * math.cos(a), cy - rad * 0.58 * math.sin(a), txt)
    _police(p, math.floor(rad * 0.17))
    _texte_centre(p, cx, cy - rad * 1.33 if titre_dessus else cy + rad * 1.33, titre)


def peindre_face_arriere(p, cx, cy, R, miroir: bool = True):
    """Face arrière : spirales métonique (5 tours, 235 cases) et du Saros (4 tours, 223 cases, glyphes Η et Σ),
    cadrans callippique, de l'exeligmos et des Jeux, chacun centré sur l'arbre qui porte son aiguille.  `miroir` : vue
    par-derrière (x inversés), comme la texture d'Anticythere3D."""
    s = R / 0.485
    ppm = s / M.BACK_DIAL_SPAN
    sx = -1 if miroir else 1

    def at(mx, my):
        return cx + sx * (mx - M.CASE_CX) * ppm, cy - (my - M.CASE_CY) * ppm

    bw, bh = M.CASE_WIDTH * ppm, M.CASE_HEIGHT * ppm
    p.setBrush(QBrush(_degrade(cx, cy, R, 1.35, ((0.0, (240, 220, 168)), (1.0, BRONZE_MOYEN)))))
    p.setPen(QPen(GRAVE_DOUX, s * 0.004))
    p.drawRect(QRectF(cx - bw / 2, cy - bh / 2, bw, bh))
    debuts = M.metonic_year_starts()
    annee_de = {}
    for an, premier in enumerate(debuts):
        dernier = debuts[an + 1] if an + 1 < len(debuts) else 235
        for mois in range(premier, dernier):
            annee_de[mois] = (an, mois - premier)

    def case_meton(k):
        an, rang = annee_de[k]
        if rang == 0:
            return M.GREEK_NUMERALS[an], True
        if k >= debuts[15]:
            return M.CORINTHIAN_MONTHS[rang % 12][1], False
        return None

    def case_saros(k):
        g = M.saros_glyph(k)
        return (g, True) if g else None

    nx, ny = at(*M.ARBORS['n'])
    gx, gy = at(*M.ARBORS['g'])
    _spirale(p, nx, ny, s, 5, 235, M.METONIC_RADIUS * 0.275 * ppm, M.METONIC_RADIUS * ppm, 'ΜΕΤΩΝ · 235', case_meton,
             set(debuts), False)
    _spirale(p, gx, gy, s, 4, 223, M.SAROS_RADIUS * 0.27 * ppm, M.SAROS_RADIUS * ppm, 'ΣΑΡΟΣ · 223', case_saros,
             {0, 56, 112, 168}, True)
    ox, oy = at(*M.ARBORS['o'])
    ix, iy = at(*M.ARBORS['i'])
    _petit_cadran(p, ox, oy, s, M.CALLIPPIC_RADIUS * ppm, 4, ('Α', 'Β', 'Γ', 'Δ'), 'ΚΑΛΛΙΠΠΟΣ', True)
    _petit_cadran(p, ix, iy, s, M.EXELIGMOS_RADIUS * ppm, 3, M.EXELIGMOS_LABELS, 'ΕΞΕΛΙΓΜΟΣ', False)
    jx, jy = at(*M.GAMES_CENTER)
    _petit_cadran(p, jx, jy, s, M.GAMES_RADIUS * ppm, 4, M.GAMES_GREEK, 'ΑΓΩΝΕΣ', False)


ENV_AVANT = M.FRONT_DIAL_SPAN / 2 / 0.485
ENV_ARRIERE = M.BACK_DIAL_SPAN
_IMAGES: dict = {}


def image_cadran(face: str, cote: int, lg: str) -> QImage:
    """Image d'un cadran (cache par face, langue et résolution : niveau de détail selon le zoom)."""
    cle = (face, cote, lg)
    im = _IMAGES.get(cle)
    if im is not None:
        return im
    im = QImage(cote, cote, QImage.Format.Format_ARGB32_Premultiplied)
    im.fill(Qt.GlobalColor.transparent)
    p = QPainter(im)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    R = cote * 0.485
    if face == 'avant':
        peindre_face_avant(p, cote / 2, cote / 2, R, lg)
    elif face == 'calendrier':
        peindre_anneau_calendrier(p, cote / 2, cote / 2, R)
    else:
        peindre_face_arriere(p, cote / 2, cote / 2, R, True)
    p.end()
    if len(_IMAGES) > 9:
        _IMAGES.clear()
    _IMAGES[cle] = im
    return im


# ==================================================================== projection
def projeter(pr, x, y, z):
    R, s, cx, cy, C = pr['R'], pr['s'], pr['cx'], pr['cy'], pr['C']
    dx, dy, dz = x - C[0], y - C[1], z - C[2]
    return (cx + s * (R[0] * dx + R[1] * dy + R[2] * dz), cy - s * (R[3] * dx + R[4] * dy + R[5] * dz),
            R[6] * dx + R[7] * dy + R[8] * dz)


def affine_plan(pr, z0) -> QTransform:
    """Transformation qui projette le plan z = z0 de la machine (repère x, y en mm)."""
    R, s = pr['R'], pr['s']
    e, f, _ = projeter(pr, 0.0, 0.0, z0)
    return QTransform(s * R[0], -s * R[3], s * R[1], -s * R[4], e, f)


def sous_pixel(pr, X, Y, z0):
    """Point (x, y) de la machine sous le pixel, dans le plan z = z0 ; None si ce plan est vu par la tranche."""
    R, s, cx, cy, C = pr['R'], pr['s'], pr['cx'], pr['cy'], pr['C']
    vx, vy = (X - cx) / s, -(Y - cy) / s
    if abs(R[8]) < 0.15:
        return None
    t = (z0 - C[2] - R[2] * vx - R[5] * vy) / R[8]
    return C[0] + R[0] * vx + R[3] * vy + R[6] * t, C[1] + R[1] * vx + R[4] * vy + R[7] * t


# ==================================================================== textes des valeurs
def date_texte(jd: float) -> str:
    y, m, d, _ = M.from_julian_day(jd)
    an = tr('anim_antikythera_av_jc', a=1 - y) if y <= 0 else str(y)
    return tr('anim_antikythera_greg' if jd >= 2299160.5 else 'anim_antikythera_jul', d='%02d/%02d/%s' % (d, m, an))


def egypte_texte(jd: float) -> str:
    mois, jour = M.egyptian_date(jd)
    return tr('anim_antikythera_epagomene', j=jour) if mois == 12 else '%s %d' % (M.EGYPTIAN_MONTHS[mois], jour)


def signe_texte(lon_deg: float) -> str:
    # arrondi au dixième AVANT de choisir le signe : jamais « Verseau 30,0° »
    i, deg = M.zodiac_sign(round((lon_deg % 360.0) * 10) / 10)
    nom = M.ZODIAC_GREEK[i]
    return '%s %s' % (nom[1] if langue() == 'fr' else nom[2], angle(deg, 1))


def fiche_roue(nom: str) -> str:
    r = M.GEAR_RATES[nom]
    return tr('anim_antikythera_roue_val', nom=nom, dents=M.TEETH[nom], rapport=str(abs(r)),
              sens=tr('anim_antikythera_sens_inverse') if r < 0 else '',
              fonction=tr('anim_antikythera_sub_' + M.SUBSYSTEM_OF.get(nom, 'input')))


SYMBOLES = {'moon': '☾', 'mercury': '☿', 'venus': '♀', 'sun': '☉', 'mars': '♂', 'jupiter': '♃', 'saturn': '♄'}
#: date de départ : 12 août 2026 à midi (UTC), jour d'une éclipse totale de Soleil (glyphe Η du Saros)
JD_DEPART = M.julian_day(2026, 8, 12, 12)


def _aiguille(p, x, y, a, longueur, larg, col):
    p.save()
    p.translate(x, y)
    p.rotate(math.degrees(a))
    p.setPen(QPen(QColor(30, 30, 30, 178), 0.4))
    p.setBrush(rvb(col))
    p.drawPolygon(QPolygonF([QPointF(-6, -larg / 2), QPointF(longueur, -larg / 4), QPointF(longueur * 1.05, 0),
                             QPointF(longueur, larg / 4), QPointF(-6, larg / 2)]))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(71, 71, 77))
    p.drawEllipse(QPointF(0, 0), 3.4, 3.4)
    p.restore()


def _sphere_phase(p, r, elong):
    """Sphère demi-argentée : la part éclairée suit l'élongation (0 : nouvelle, 180 : pleine), limbe vers +x."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(28, 28, 32))
    p.drawEllipse(QPointF(0, 0), r, r)
    k = math.cos((elong % 360) * DEG)
    lit = QPainterPath()
    lit.moveTo(0, -r)
    lit.arcTo(QRectF(-r, -r, 2 * r, 2 * r), 90, -180)          # demi-cercle du côté +x
    kr = abs(k) * r + 1e-6
    # terminateur : demi-ellipse vers +x (croissant) ou vers −x (gibbeuse)
    lit.arcTo(QRectF(-kr, -r, 2 * kr, 2 * r), -90, 180 if k > 0 else -180)
    lit.closeSubpath()
    p.setBrush(QColor(214, 218, 224))
    p.drawPath(lit)
    p.setPen(QPen(QColor(20, 20, 20, 204), 0.4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(0, 0), r, r)


_SILLONS: dict = {}


def _sillon(ctr, rad, tours) -> QPolygonF:
    """Spirale du dos vue de devant (en miroir de la gravure), calculée une fois."""
    cle = (ctr, rad, tours)
    poly = _SILLONS.get(cle)
    if poly is None:
        r0 = rad * (0.275 if tours == 5 else 0.27)
        pts = []
        for i in range(401):
            t = tours * 2 * math.pi * i / 400
            rr = r0 + (rad - r0) * i / 400
            pts.append(QPointF(ctr[0] - rr * math.cos(t - math.pi / 2), ctr[1] + rr * math.sin(t - math.pi / 2)))
        poly = _SILLONS[cle] = QPolygonF(pts)
    return poly


class Anticythere(Animation):
    ID = 'antikythera'
    ANIMEE = True

    TEMPS = ()

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        self.regler_jd(m.i.jj)

    def construire(self):
        self.meca = M.machine_calee()
        self.q = VUES['avant']
        self.roue = None
        self._zone = None
        self.pr = None
        self._s_fige = None
        self._decalage = (0.0, 0.0)
        self._prise = None
        self._angle_prise = None
        self._dernier = None
        self._bouge = False
        self.duree_ms = 0.0
        self.enveloppe = self.coche('enveloppe', True)
        self.eclatement = self.curseur('eclatement', 0, 100, 0, dec=0, unite='%')
        self.face = self.choix('face', [('anim_antikythera_f_avant', 'avant'), ('anim_antikythera_f_arriere', 'arriere'),
                                        ('anim_antikythera_f_trois_quarts', 'trois_quarts')], 'avant')
        self.face.currentIndexChanged.connect(self._vue_choisie)
        self.bouton('anim_antikythera_lunaison', lambda: self.regler_jd(self.jd() + M.SYNODIC_MONTH))
        self.bouton('anim_antikythera_annee', lambda: self.regler_jd(self.jd() + M.TROPICAL_YEAR))
        self.etat_initial()

    def _vue_choisie(self, *_):
        self.q = VUES.get(self.face.currentData(), VUES['avant'])
        self._s_fige = None

    def etat_initial(self):
        self.meca.days = JD_DEPART - M.J2000
        self.q = VUES.get(self.face.currentData(), VUES['avant'])
        self.roue = None
        self._s_fige = None

    def jd(self) -> float:
        return M.J2000 + self.meca.days

    def regler_jd(self, jd: float):
        if math.isfinite(jd):
            self.meca.days = jd - M.J2000
            self.rafraichir()

    def avancer(self, dt: float):
        """Lecture : la manivelle fait un tour par seconde (× vitesse), soit 48/223 d'année."""
        if math.isfinite(dt):
            self.meca.turns += dt / -M.CRANK_PER_TURN

    def explode(self) -> float:
        return self.eclatement.value() / 100

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        o = self.meca.outputs()
        jd = self.jd()
        v = [(tr('anim_antikythera_v_date'), date_texte(jd)),
             (tr('anim_antikythera_v_egypte'), egypte_texte(jd)),
             (tr('anim_antikythera_v_soleil'), signe_texte(o['mean_sun'] * 360)),
             (tr('anim_antikythera_v_lune'), signe_texte(o['moon_true'] * 360)),
             (tr('anim_antikythera_v_phase'), tr('anim_antikythera_phase_val',
                                                  nom=tr('anim_antikythera_phase_%d' % M.phase_index(o['phase_turns'])),
                                                  pc=nombre(o['phase_illum'] * 100, 0))),
             (tr('anim_antikythera_v_anomalie'), ('+' if o['moon_anomaly_deg'] >= 0 else '') + angle(o['moon_anomaly_deg'], 2)),
             (tr('anim_antikythera_v_noeud'), signe_texte(o['nodes'] * 360)),
             (tr('anim_antikythera_v_meton'), tr('anim_antikythera_meton_val', case=o['metonic_cell'], an=o['metonic_year'])),
             (tr('anim_antikythera_v_callippe'), tr('anim_antikythera_callippe_val', q=o['callippic_quarter'])),
             (tr('anim_antikythera_v_jeux'), tr('anim_antikythera_jeux_' + o['games_name']))]
        gl = M.saros_glyph(o['saros_cell'] - 1)
        sv = tr('anim_antikythera_saros_val', case=o['saros_cell'])
        v.append((tr('anim_antikythera_v_saros'), tr('anim_antikythera_glyphe', v=sv, g=gl) if gl else sv))
        v.append((tr('anim_antikythera_v_exeligmos'), tr('anim_antikythera_exel_val', h=o['exeligmos_hours'])))
        e = M.eclipse_possible(jd)
        et = tr({'solar': 'anim_antikythera_eclipse_sol', 'lunar': 'anim_antikythera_eclipse_lune'}.get(
            e['type'], 'anim_antikythera_eclipse_aucune'))
        if e['certain']:
            et = tr('anim_antikythera_eclipse_certaine', t=et)
        v.append((tr('anim_antikythera_v_eclipse'), et))
        for k in M.NOMS_PLANETES:
            v.append((tr('anim_antikythera_v_planete', nom=tr('anim_antikythera_pl_' + k)),
                      signe_texte(M.geocentric_longitude(k, o['planets'][k], o['mean_sun']))))
        ds = (o['mean_sun'] * 360 - M.sun_mean_longitude(jd) + 180) % 360 - 180
        dl = (o['moon_true'] * 360 - M.moon_longitude(jd) + 180) % 360 - 180

        def sg(x):
            return ('+' if x >= 0 else '') + angle(x, 2)
        v.append((tr('anim_antikythera_v_ecart'), tr('anim_antikythera_ecart_val', s=sg(ds), l=sg(dl))))
        v.append((tr('anim_antikythera_v_manivelle'), tr('anim_antikythera_manivelle_val',
                                                         t=nombre(o['turns'] * -M.CRANK_PER_TURN, 1),
                                                         j=nombre(o['days'], 0))))
        v.append((tr('anim_antikythera_v_roue'), fiche_roue(self.roue) if self.roue else tr('anim_antikythera_roue_aucune')))
        return v

    # ------------------------------------------------------------ souris
    def presser(self, pos, bouton) -> bool:
        if self._zone is None or not self._zone.contains(pos):
            return False
        self._dernier = QPointF(pos)
        self._bouge = False
        if bouton == Qt.MouseButton.LeftButton and self.sur_manivelle(pos):
            self._prise = 'manivelle'
            self._angle_prise = self.angle_manivelle(pos)
        else:
            self._prise = 'vue'
            if self.pr:
                self._s_fige = self.pr['s']
        return True

    def glisser(self, pos, dx, dy):
        if not self._prise or not (math.isfinite(dx) and math.isfinite(dy)):
            return
        if self._dernier is not None and math.hypot(pos.x() - self._dernier.x(), pos.y() - self._dernier.y()) > 3:
            self._bouge = True
        if self._prise == 'manivelle':
            a = self.angle_manivelle(pos)
            if a is not None and self._angle_prise is not None:
                d = (a - self._angle_prise + math.pi) % (2 * math.pi) - math.pi
                if math.isfinite(d):
                    self.meca.turns += d / (2 * math.pi) / M.CRANK_PER_TURN
            self._angle_prise = a
            self.rafraichir()
            return
        r = min(self._zone.width(), self._zone.height()) * 0.45 if self._zone is not None else 200.0
        self.q = tourner_camera(self.q, dx, dy, r, VUES.get(self.face.currentData(), VUES['avant']))
        self.toile.update()

    def relacher(self, pos):
        if self._prise == 'vue' and not self._bouge:
            # toucher une roue la désigne ; toucher à côté efface la désignation
            self.roue = self.roue_sous(pos)
        self._prise = None
        self._angle_prise = None
        self._s_fige = None
        self.rafraichir()

    def survoler(self, pos) -> bool:
        r = self.roue_sous(pos)
        if r == self.roue:
            return False
        self.roue = r
        self.rafraichir()
        return True

    def double_clic(self, pos) -> bool:
        self._vue_choisie()
        self.rafraichir()
        return True

    def _manivelle(self):
        ax, ay = M.ARBORS['a']
        z0 = M.Z_FRONT - 2 + M.front_shift(self.explode())
        a = 2 * math.pi * self.meca.gear_angles()['a1']
        return dict(ax=ax, ay=ay, z0=z0, zp=z0 + M.CRANK_SHAFT + 4 + (M.CRANK_HANDLE + 6) / 2,
                    hx=ax + M.CRANK_RADIUS * math.cos(a), hy=ay + M.CRANK_RADIUS * math.sin(a))

    def sur_manivelle(self, pos) -> bool:
        pr = self.pr
        if not pr or pr['R'][8] < 0.05:
            return False
        m = self._manivelle()
        x0, y0, _ = projeter(pr, m['hx'], m['hy'], m['z0'] + M.CRANK_SHAFT + 4)
        x1, y1, _ = projeter(pr, m['hx'], m['hy'], m['z0'] + M.CRANK_SHAFT + 4 + M.CRANK_HANDLE + 6)
        lx, ly = x1 - x0, y1 - y0
        l2 = lx * lx + ly * ly
        t = max(0.0, min(1.0, ((pos.x() - x0) * lx + (pos.y() - y0) * ly) / l2)) if l2 > 1e-9 else 0.0
        return math.hypot(pos.x() - (x0 + t * lx), pos.y() - (y0 + t * ly)) <= max(16.0, 7 * pr['s'])

    def angle_manivelle(self, pos):
        pr = self.pr
        if not pr:
            return None
        m = self._manivelle()
        q = sous_pixel(pr, pos.x(), pos.y(), m['zp'])
        if q and math.hypot(q[0] - m['ax'], q[1] - m['ay']) > 1:
            return math.atan2(q[1] - m['ay'], q[0] - m['ax'])
        cx, cy, _ = projeter(pr, m['ax'], m['ay'], m['zp'])
        a = math.atan2(-(pos.y() - cy), pos.x() - cx)
        return a if pr['R'][8] >= 0 else -a

    def roue_sous(self, pos):
        """Roue la plus proche de l'observateur dont le disque contient le point (machine ouverte)."""
        pr = self.pr
        if not pr or self.enveloppe.isChecked():
            return None
        e = self.explode()
        car = self.meca.raw('carrier_e3')
        angles = None
        meilleur, prof = None, -math.inf
        for nom in M.LEVELS:
            gx, gy, gz = M.gear_placement(nom, e, car)
            z = gz + M.GEAR_THICKNESS if pr['R'][8] >= 0 else gz
            q = sous_pixel(pr, pos.x(), pos.y(), z)
            if not q:
                continue
            rp = M.MODULE * M.TEETH[nom] / 2
            r = math.hypot(q[0] - gx, q[1] - gy)
            if r > rp + 0.6:
                continue
            if nom in M.SPOKED and 9.5 < r < rp * 0.86:
                angles = angles or self.meca.gear_angles()
                pas = 2 * math.pi / M.SPOKED[nom]
                a = (math.atan2(q[1] - gy, q[0] - gx) - 2 * math.pi * angles[nom]) % pas
                if min(a, pas - a) * r > 3.5:
                    continue
            vz = projeter(pr, q[0], q[1], z)[2]
            if vz > prof:
                meilleur, prof = nom, vz
        return meilleur

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        import time
        t0 = time.perf_counter()
        ferme = self.enveloppe.isChecked()
        if not q_valide(self.q):
            self.q = VUES.get(self.face.currentData(), VUES['avant'])
        R = q_matrice(self.q)
        e = self.explode()
        shift = M.front_shift(e)
        titre = (('anim_antikythera_titre_avant' if R[8] >= 0 else 'anim_antikythera_titre_arriere') if ferme
                 else 'anim_antikythera_titre_ouverte')
        r = dessin.cadre(p, rect, tr(titre))
        self._zone = QRectF(r)
        zf, zb = M.Z_FRONT + shift, M.Z_BACK
        C = (M.CASE_CX, M.CASE_CY, (zf + zb) / 2)
        s = self._s_fige
        dxc, dyc = self._decalage
        if s is None or not math.isfinite(s):
            hw, hh = M.CASE_WIDTH / 2, M.CASE_HEIGHT / 2
            ax, ay = M.ARBORS['a']
            zm = M.Z_FRONT - 2 + shift + M.CRANK_SHAFT + 4 + M.CRANK_HANDLE + 6
            pts = [(x, y, z) for x in (M.CASE_CX - hw, M.CASE_CX + hw) for y in (M.CASE_CY - hh, M.CASE_CY + hh)
                   for z in (zb, zf)]
            pts += [(ax + dx * M.CRANK_RADIUS, ay + dy * M.CRANK_RADIUS, zm) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            vx = [R[0] * (x - C[0]) + R[1] * (y - C[1]) + R[2] * (z - C[2]) for x, y, z in pts]
            vy = [R[3] * (x - C[0]) + R[4] * (y - C[1]) + R[5] * (z - C[2]) for x, y, z in pts]
            s = min(r.width() / (max(vx) - min(vx)), r.height() / (max(vy) - min(vy))) * 0.95
            dxc, dyc = -(min(vx) + max(vx)) / 2, -(min(vy) + max(vy)) / 2
            self._decalage = (dxc, dyc)
        if not (s > 0) or not math.isfinite(s):
            s = 1.0
        pr = {'R': R, 's': s, 'cx': r.center().x() + dxc * s, 'cy': r.center().y() - dyc * s, 'C': C}
        self.pr = pr
        sombre = dessin.theme() == 'sombre'
        k_ecran = math.hypot(p.worldTransform().m11(), p.worldTransform().m12())
        px_mm = s * k_ecran
        p.save()
        p.setClipRect(r.adjusted(2, 2, -2, -2))
        pieces = []
        sens = 1 if R[8] >= 0 else -1

        def ajoute(z, f):
            pieces.append((z * sens, len(pieces), f))

        def plan(z, f):
            p.save()
            p.setTransform(affine_plan(pr, z), True)
            f()
            p.restore()

        angles = self.meca.gear_angles()
        o = self.meca.outputs()
        car = o['carrier_e3']
        if ferme:
            self._coffret(p, pr, plan, zf, zb, px_mm, o)
        else:
            self._roues(p, pr, plan, ajoute, angles, car, e, s, sombre)
            self._arbres(p, pr, ajoute, car, e, s, sombre)
            self._reperes(p, plan, ajoute, zf, zb, sombre)
            ajoute(zf + 9.5, lambda: plan(zf + 9.5, lambda: self._cosmos_et_aiguilles(p, o)))
            ajoute(zb - 2, lambda: plan(zb - 2, lambda: self._aiguilles_dos(p, o)))
        if not ferme or R[8] > -0.05:
            self._manivelle_pieces(p, pr, ajoute, sombre)
        pieces.sort(key=lambda x: (x[0], x[1]))
        for _, _, f in pieces:
            f()
        p.restore()
        if ferme:
            self._etiquettes_cosmos(p, pr, zf, o)
        else:
            self._legende(p, r, sombre)
        if self.roue:
            gx, gy, gz = M.gear_placement(self.roue, e, car)
            X, Y, _ = projeter(pr, gx, gy, gz + M.GEAR_THICKNESS)
            dessin.police(p, 0.9)
            dessin.etiquette(p, X, Y, '%s · %s · %s' % (self.roue, tr('anim_antikythera_dents', n=M.TEETH[self.roue]),
                                                       M.GEAR_RATES[self.roue]), 'texte')
            dessin.police(p, 1 / 0.9)
        self.duree_ms = (time.perf_counter() - t0) * 1000

    def _roues(self, p, pr, plan, ajoute, angles, car, e, s, sombre):
        R = pr['R']
        voile = self.roue is not None
        dent_px = math.pi * M.MODULE * s
        incline = abs(R[8]) < 0.985
        lum = 0.78 + 0.22 * abs(R[8])
        avant = R[8] >= 0
        for nom in M.LEVELS:
            gx, gy, gz = M.gear_placement(nom, e, car)
            base = couleur_sous_ensemble(M.SUBSYSTEM_OF.get(nom, 'input'), sombre)
            dents, cercle = chemins_roue(nom)
            chemin = dents if dent_px >= 3 else cercle
            rot = 360.0 * angles[nom]
            survol = self.roue == nom
            alpha = 0.55 if voile and not survol else 1.0
            zc, zv = (gz, gz + M.GEAR_THICKNESS) if avant else (gz + M.GEAR_THICKNESS, gz)

            def arriere(gx=gx, gy=gy, base=base, alpha=alpha, zc=zc, nom=nom):
                # face cachée : seul son bord dépasse (de l'épaisseur de la roue, vue de biais) : une couronne
                # de 3 mm suffit, bien moins coûteuse qu'un disque plein
                def f():
                    rp = M.MODULE * M.TEETH[nom] / 2
                    p.setPen(QPen(rvb([x * lum * 0.62 for x in base], alpha), 3.0))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawEllipse(QPointF(gx, gy), rp - 1.3, rp - 1.3)
                plan(zc, f)

            def devant(gx=gx, gy=gy, rot=rot, base=base, chemin=chemin, alpha=alpha, zv=zv, survol=survol, nom=nom):
                def f():
                    p.translate(gx, gy)
                    p.rotate(rot)
                    p.fillPath(chemin, rvb([x * lum for x in base], alpha))
                    if survol:
                        p.strokePath(chemin, QPen(dessin.c('accent1'), 2.2 / s))
                    p.setPen(QPen(rvb([x * 0.55 for x in base]), 1.2 / s))
                    p.drawLine(QPointF(0, 0), QPointF(M.MODULE * M.TEETH[nom] / 2 * 0.9, 0))
                plan(zv, f)
            if incline:
                ajoute(zc, arriere)
            ajoute(zv, devant)

    def _arbres(self, p, pr, ajoute, car, e, s, sombre):
        gris = (170, 174, 182) if sombre else (71, 71, 77)
        roues = [(*M.gear_placement(g, e, car), M.MODULE * M.TEETH[g] / 2 + 1) for g in M.LEVELS]
        stylo = QPen(rvb(gris), max(1.0, 2 * M.ARBOR_RADIUS * s))
        stylo.setCapStyle(Qt.PenCapStyle.RoundCap)
        for arbre in M.ARBORS:
            if arbre == 'a':
                continue
            ax, ay = M.arbor_position(arbre, car)
            z0, z1 = M.arbor_span(arbre, e)
            coupes = set()
            for gx, gy, gz, ra in roues:
                if math.hypot(gx - ax, gy - ay) > ra + 20:
                    continue
                for z in (gz, gz + M.GEAR_THICKNESS):
                    if z0 < z < z1:
                        coupes.add(z)
            cuts = [z0] + sorted(coupes) + [z1]
            for za, zc in zip(cuts, cuts[1:]):
                def f(ax=ax, ay=ay, za=za, zc=zc):
                    x0, y0, _ = projeter(pr, ax, ay, za)
                    x1, y1, _ = projeter(pr, ax, ay, zc)
                    p.setPen(stylo)
                    p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
                ajoute((za + zc) / 2, f)

    def _reperes(self, p, plan, ajoute, zf, zb, sombre):
        """Machine ouverte : anneau du zodiaque (façade) et spirales (dos), vus de devant."""
        def zodiaque():
            anneau = QPainterPath()
            anneau.addEllipse(QPointF(0, 0), 100.6, 100.6)
            anneau.addEllipse(QPointF(0, 0), 76.9, 76.9)
            anneau.setFillRule(Qt.FillRule.OddEvenFill)
            p.fillPath(anneau, rvb(BRONZE_CLAIR, 0.55))
            p.setPen(QPen(GRAVE_DOUX, 0.6))
            for i in range(12):
                a = (90 - 30 * i) * DEG
                p.drawLine(QPointF(76.9 * math.cos(a), 76.9 * math.sin(a)), QPointF(100.6 * math.cos(a), 100.6 * math.sin(a)))
        ajoute(zf - 2, lambda: plan(zf - 2, zodiaque))
        for ctr, rad, tours, sub in ((M.METONIC_CENTER, M.METONIC_RADIUS, 5, 'metonic'),
                                     (M.SAROS_CENTER, M.SAROS_RADIUS, 4, 'saros')):
            def spir(ctr=ctr, rad=rad, tours=tours, sub=sub):
                p.setPen(QPen(rvb(couleur_sous_ensemble(sub, sombre), 0.8), 1.2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPolyline(_sillon(ctr, rad, tours))
            ajoute(zb + 1.2, lambda spir=spir: plan(zb + 1.2, spir))

    def _coffret(self, p, pr, plan, zf, zb, px_mm, o):
        """Machine fermée : faces du coffret tournées vers l'observateur, cadrans gravés, aiguilles."""
        R = pr['R']
        W, H = M.CASE_WIDTH, M.CASE_HEIGHT
        X0, Y0 = M.CASE_CX - W / 2, M.CASE_CY - H / 2
        flancs = (((1, 0, 0), ((X0 + W, Y0, zb), (X0 + W, Y0 + H, zb), (X0 + W, Y0 + H, zf), (X0 + W, Y0, zf))),
                  ((-1, 0, 0), ((X0, Y0, zb), (X0, Y0 + H, zb), (X0, Y0 + H, zf), (X0, Y0, zf))),
                  ((0, 1, 0), ((X0, Y0 + H, zb), (X0 + W, Y0 + H, zb), (X0 + W, Y0 + H, zf), (X0, Y0 + H, zf))),
                  ((0, -1, 0), ((X0, Y0, zb), (X0 + W, Y0, zb), (X0 + W, Y0, zf), (X0, Y0, zf))))
        for n, coins in flancs:
            nz = R[6] * n[0] + R[7] * n[1] + R[8] * n[2]
            if nz <= 0.01:
                continue
            poly = QPolygonF([QPointF(*projeter(pr, *q)[:2]) for q in coins])
            p.setPen(QPen(QColor(0, 0, 0, 89), 1))
            p.setBrush(rvb([x * (0.7 + 0.3 * nz) for x in BOIS]))
            p.drawPolygon(poly)
        if R[8] > 0.01:
            def facade():
                p.setBrush(rvb(BRONZE_MOYEN))
                p.setPen(QPen(GRAVE_DOUX, 0.8))
                p.drawRect(QRectF(X0, Y0, W, H))
                self._cadran(p, 'avant', 0, 0, ENV_AVANT, 0, px_mm, False)
                lam = (90 - 360 * o['mean_sun']) * DEG
                date = (90 - 360 * (M.egyptian_day(self.jd()) + 0.5) / 365) * DEG
                self._cadran(p, 'calendrier', 0, 0, ENV_AVANT, lam - date, px_mm, False)
                self._cosmos_et_aiguilles(p, o)
            plan(zf, facade)
        if R[8] < -0.01:
            def dos():
                self._cadran(p, 'arriere', M.CASE_CX, M.CASE_CY, ENV_ARRIERE, 0, px_mm, True)
                self._aiguilles_dos(p, o)
            plan(zb, dos)

    def _cadran(self, p, face, x, y, env, rot, px_mm, miroir):
        """Cadran en image (cache) : résolution selon le zoom (256 à 2048 px), repère y vers le bas."""
        p.save()
        p.translate(x, y)
        p.rotate(math.degrees(rot))
        p.scale(-1 if miroir else 1, -1)
        voulu = max(1.0, env * px_mm)
        cote = int(min(2048, max(256, 2 ** math.ceil(math.log2(voulu)))))
        im = image_cadran(face, cote, langue())
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.drawImage(QRectF(-env / 2, -env / 2, env, env), im)
        p.restore()

    def longitude_cosmos(self, nom, o):
        if nom == 'sun':
            return (o['mean_sun'] * 360) % 360
        if nom == 'moon':
            return (o['moon_true'] * 360) % 360
        return M.geocentric_longitude(nom, o['planets'][nom], o['mean_sun'])

    def _cosmos_et_aiguilles(self, p, o):
        """Anneaux du Cosmos (longitudes géocentriques), aiguilles du Soleil et de la Lune, sphère de phase."""
        for nom, rayon, col in M.COSMOS_RINGS:
            p.setPen(QPen(rvb(col, 0.85), 1.6))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(0, 0), rayon, rayon)
            a = (90 - self.longitude_cosmos(nom, o)) * DEG
            p.setPen(QPen(QColor(40, 40, 46, 230), 0.4))
            p.setBrush(rvb(col))
            p.drawEllipse(QPointF(rayon * math.cos(a), rayon * math.sin(a)), 3.1, 3.1)
        ls = (90 - 360 * o['mean_sun']) * DEG
        _aiguille(p, 0, 0, ls, M.SUN_HAND, 3.2, AIGUILLE_SOLEIL)
        al = (90 - 360 * o['moon_true']) * DEG
        _aiguille(p, 0, 0, al, M.MOON_HAND, 2.4, AIGUILLE_LUNE)
        bx, by = 82 * math.cos(al), 82 * math.sin(al)
        elong = (o['phase_turns'] * 360) % 360
        vers_soleil = math.atan2(math.sin(ls) * 97 - by, math.cos(ls) * 97 - bx)
        p.save()
        p.translate(bx, by)
        p.rotate(math.degrees(vers_soleil + (math.pi if elong > 180 else 0)))
        _sphere_phase(p, 5.5, elong)
        p.restore()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(71, 71, 77))
        p.drawEllipse(QPointF(0, 0), 4.2, 4.2)

    def _aiguilles_dos(self, p, o):
        """Aiguilles du dos : un point (u, v) de l'image (v vers le bas) est à (−u, −v) de son centre dans le repère
        de la machine ; le curseur suit le sillon de la spirale."""
        def spir(ctr, rad, tours, val, col, r0f):
            t = 2 * math.pi * (val % tours)
            r0 = rad * r0f
            rr = r0 + (rad - r0) * t / (tours * 2 * math.pi)
            x = ctr[0] - rr * math.cos(t - math.pi / 2)
            y = ctr[1] + rr * math.sin(t - math.pi / 2)
            _aiguille(p, ctr[0], ctr[1], math.atan2(y - ctr[1], x - ctr[0]), rad * 1.04, 2.4, col)
            p.setPen(QPen(QColor(30, 30, 30, 204), 0.4))
            p.setBrush(rvb(col))
            p.drawEllipse(QPointF(x, y), 2.2, 2.2)
        spir(M.METONIC_CENTER, M.METONIC_RADIUS, 5, o['metonic'], M.COLORS['metonic'], 0.275)
        spir(M.SAROS_CENTER, M.SAROS_RADIUS, 4, o['saros'], M.COLORS['saros'], 0.27)

        def petit(ctr, rad, frac):
            ia = math.pi / 2 - 2 * math.pi * (frac % 1)
            _aiguille(p, ctr[0], ctr[1], math.atan2(math.sin(ia), -math.cos(ia)), rad * 0.92, 1.6, (71, 71, 77))
        petit(M.ARBORS['o'], M.CALLIPPIC_RADIUS, o['callippic'])
        petit(M.ARBORS['i'], M.EXELIGMOS_RADIUS, o['exeligmos'])
        petit(M.GAMES_CENTER, M.GAMES_RADIUS, o['turns'] / 4)

    def _manivelle_pieces(self, p, pr, ajoute, sombre):
        m = self._manivelle()
        bois = (190, 146, 80) if sombre else (140, 107, 51)
        z1 = m['z0'] + M.CRANK_SHAFT

        def seg(x0, y0, za, x1, y1, zc, larg, col):
            def f():
                a, b, _ = projeter(pr, x0, y0, za)
                d, e, _ = projeter(pr, x1, y1, zc)
                st = QPen(rvb(col), max(1.5, larg * pr['s']))
                st.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(st)
                p.drawLine(QPointF(a, b), QPointF(d, e))
            ajoute((za + zc) / 2, f)
        zp0 = z1 + 4
        zp1 = zp0 + M.CRANK_HANDLE + 6
        seg(m['ax'], m['ay'], m['z0'], m['ax'], m['ay'], z1 + 2, 6.4, bois)
        seg(m['ax'], m['ay'], z1 + 2, m['hx'], m['hy'], z1 + 2, 6, bois)
        seg(m['hx'], m['hy'], zp0, m['hx'], m['hy'], zp1, 6.5, [min(255, x * 1.15) for x in bois])

    def _etiquettes_cosmos(self, p, pr, zf, o):
        """Symboles des planètes au bout de leur anneau (machine fermée, face avant)."""
        if pr['R'][8] < 0.45:
            return
        dessin.police(p, 0.85)
        for nom, rayon, _ in M.COSMOS_RINGS:
            a = (90 - self.longitude_cosmos(nom, o)) * DEG
            X, Y, _ = projeter(pr, rayon * math.cos(a), rayon * math.sin(a), zf + 9.5)
            dessin.reserver(p, X, Y, max(2.0, 3.1 * pr['s']))
            dessin.etiquette(p, X, Y, SYMBOLES[nom], 'texte', 5)
        dessin.police(p, 1 / 0.85)

    def _legende(self, p, r, sombre):
        """Légende des couleurs des sous-ensembles (machine ouverte)."""
        dessin.police(p, 0.82)
        fm = QFontMetricsF(p.font())
        h = fm.height() + 3
        noms = [tr('anim_antikythera_sub_' + k) for k in M.SUBSYSTEM_KEYS]
        w = max(fm.horizontalAdvance(n) for n in noms) + 28
        if w + 16 > r.width() * 0.6 or h * 7 + 8 > r.height() * 0.6:
            dessin.police(p, 1 / 0.82)
            return
        x0, y0 = r.x() + 6, r.bottom() - 7 * h - 10
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('fond', 0.82))
        p.drawRoundedRect(QRectF(x0, y0, w + 8, 7 * h + 6), 5, 5)
        for i, k in enumerate(M.SUBSYSTEM_KEYS):
            y = y0 + 4 + i * h
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(rvb(couleur_sous_ensemble(k, sombre)))
            p.drawRect(QRectF(x0 + 5, y + 2, 14, h - 6))
            dessin.texte(p, x0 + 24, y + fm.ascent() + 1, noms[i], 'texte', centre=False)
        dessin.police(p, 1 / 0.82)
