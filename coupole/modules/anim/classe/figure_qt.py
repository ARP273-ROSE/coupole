"""Rendu QPainter des figures des questions, développées par le moteur (moteur/SPEC.md § 6) : même rendu que
src/contenu/figure_svg.ts de Coupole Web.  y vers le bas ; angles en degrés dans le sens trigonométrique VU À L'ÉCRAN ;
épaisseur 1,5 par défaut ; couleurs = jetons (thème sombre ou clair) ou #rrggbb.  `**…**` : partie variable (gras,
couleur « valeur ») ; `$…$` : formule (moteur de formules) ; `\\n` : lignes de 1,2 × la taille.  Réponse montrée : les
éléments liés à une bonne réponse passent en couleur « accent », plus épais."""
from __future__ import annotations

import math
import re

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QImage, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QSizePolicy, QWidget

from .. import formule
from . import contenu

CONTRASTE_MIN = 3.0          # seuil WCAG des grands textes : en dessous, couleur de repli (figure_svg.ts : même seuil)

_COTES = None


def cotes():
    """Côtes Natural Earth (domaine public) embarquées par le module Animations, en [lon, lat]."""
    global _COTES
    if _COTES is None:
        import gzip
        import json
        from pathlib import Path
        with gzip.open(Path(__file__).resolve().parents[1] / 'donnees' / 'cotes.json.gz', 'rt', encoding='utf-8') as f:
            _COTES = json.load(f).get('polygones', [])
    return _COTES


def a_des_cotes(fig) -> bool:
    def voir(e):
        return isinstance(e, dict) and (e.get('type') in ('carte', 'globe') or (e.get('type') == 'groupe' and any(map(voir, e.get('elements', [])))))
    return bool(fig) and any(map(voir, fig.get('elements', [])))


class Peintre:
    def __init__(self, p: QPainter, theme: str, reponse=False, indice=False, bonnes=()):
        self.p, self.theme = p, theme
        self.reponse, self.indice, self.bonnes = reponse, indice, set(bonnes)
        self.jetons = contenu.jetons()
        self._images = {}
        self.fonds = []          # (chemin en coordonnées de l'appareil, couleur) des remplissages opaques déjà peints

    # ------------------------------------------------------------ contraste des textes (0.7.0)
    def noter_fond(self, chemin: QPainterPath, brosse):
        """Retient un remplissage opaque (pour choisir la couleur des textes posés dessus)."""
        if isinstance(brosse, QBrush) and brosse.style() != Qt.BrushStyle.NoBrush and brosse.color().alphaF() * self.p.opacity() > 0.5:
            self.fonds.append((self.p.transform().map(chemin), brosse.color()))

    def dessous(self, pt: QPointF) -> QColor:
        """Couleur du dernier remplissage opaque sous le point (coordonnées locales), sinon le fond de la figure."""
        q = self.p.transform().map(pt)
        for chemin, c in reversed(self.fonds):
            if chemin.contains(q):
                return c
        return self.fond

    @staticmethod
    def luminance(c: QColor) -> float:
        f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(c.redF()) + 0.7152 * f(c.greenF()) + 0.0722 * f(c.blueF())

    @classmethod
    def contraste(cls, a: QColor, b: QColor) -> float:
        la, lb = sorted((cls.luminance(a), cls.luminance(b)), reverse=True)
        return (la + 0.05) / (lb + 0.05)

    def candidats(self):
        """Couleurs de texte de repli : le texte courant des deux thèmes (comme Coupole Web, figure_svg.ts)."""
        a = self.jetons.get('avant', {})
        return [QColor(a.get('sombre', '#f2f2f2')), QColor(a.get('clair', '#1a1a1a'))]

    def lisible(self, jeton, pt: QPointF) -> QColor:
        """Couleur du texte : celle demandée si elle se lit (contraste ≥ 3, WCAG grands textes) sur la surface peinte
        dessous ; sinon la plus lisible du texte courant des deux thèmes (un texte posé sur un ciel nocturne dessiné en
        dur dans le thème clair devient clair).  Même règle que Coupole Web."""
        c = self.coul(jeton)
        fond = self.dessous(pt)
        k = self.contraste(c, fond)
        if k >= CONTRASTE_MIN:
            return c
        meilleur = max(self.candidats(), key=lambda x: self.contraste(x, fond))
        return meilleur if self.contraste(meilleur, fond) > k else c

    def halo(self, couleur: QColor, pt: QPointF):
        """Liseré d'un texte de réponse (orange imposé) peu lisible sur la surface dessous : la couleur la plus
        contrastée avec l'orange (comme le web), sinon None."""
        if self.contraste(couleur, self.dessous(pt)) >= CONTRASTE_MIN:
            return None
        return max(self.candidats(), key=lambda x: self.contraste(couleur, x))

    def coul(self, c, alpha=None) -> QColor:
        if c is None or c == 'aucune':
            q = QColor(0, 0, 0, 0)
            return q
        s = str(c)
        q = QColor(s) if s.startswith('#') else QColor(self.jetons.get(s, self.jetons.get('trait', {})).get(self.theme, '#888888'))
        if alpha is not None:
            q.setAlphaF(max(0.0, min(1.0, float(alpha))))
        return q

    def stylo(self, e, defaut_trait=True):
        trait = e['trait'] if 'trait' in e else ('trait' if defaut_trait else None)
        if trait is None or trait == 'aucune':
            return Qt.PenStyle.NoPen
        pen = QPen(self.coul(trait, e.get('opacite')), float(e.get('epaisseur', 1.5)))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        if e.get('tirets'):
            ep = float(e.get('epaisseur', 1.5)) or 1
            pen.setDashPattern([max(0.1, x / ep) for x in e['tirets']])
        return pen

    def brosse(self, e, defaut=None):
        r = e['remplissage'] if 'remplissage' in e else defaut
        if r is None or r == 'aucune':
            return Qt.BrushStyle.NoBrush
        return QBrush(self.coul(r, e.get('opacite')))

    def visible(self, e) -> bool:
        a = e.get('afficher', 'toujours')
        return {'reponse': self.reponse, 'sans_reponse': not self.reponse, 'indice': self.indice}.get(a, True)

    def elt(self, e):
        if not isinstance(e, dict) or not self.visible(e):
            return
        p = self.p
        t = e.get('type')
        if self.reponse and e.get('choix') in self.bonnes and t != 'groupe':
            e = dict(e)
            if t == 'texte':
                e['couleur'] = 'accent'
                e['_reponse'] = True
            else:
                e['trait'] = 'accent'
                e['epaisseur'] = max(3.0, e.get('epaisseur', 1.5))
        if t == 'ligne':
            p.setPen(self.stylo(e))
            p.drawLine(QPointF(e['x1'], e['y1']), QPointF(e['x2'], e['y2']))
        elif t == 'fleche':
            p.setPen(self.stylo(e))
            p.drawLine(QPointF(e['x1'], e['y1']), QPointF(e['x2'], e['y2']))
            tete = e.get('tete', 8)
            a = math.atan2(e['y2'] - e['y1'], e['x2'] - e['x1'])
            poly = QPolygonF([QPointF(e['x2'], e['y2']),
                              QPointF(e['x2'] - tete * math.cos(a - 0.4), e['y2'] - tete * math.sin(a - 0.4)),
                              QPointF(e['x2'] - tete * math.cos(a + 0.4), e['y2'] - tete * math.sin(a + 0.4))])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.coul(e.get('trait', 'trait')))
            p.drawPolygon(poly)
        elif t in ('polyligne', 'polygone'):
            poly = QPolygonF([QPointF(x, y) for x, y in e['points']])
            p.setPen(self.stylo(e))
            if t == 'polyligne':
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPolyline(poly)
            else:
                p.setBrush(self.brosse(e))
                p.drawPolygon(poly)
                ch = QPainterPath()
                ch.addPolygon(poly)
                self.noter_fond(ch, p.brush())
        elif t == 'rect':
            p.setPen(self.stylo(e))
            p.setBrush(self.brosse(e))
            r = e.get('rayon', 0)
            p.drawRoundedRect(QRectF(e['x'], e['y'], e['l'], e['h']), r, r)
            ch = QPainterPath()
            ch.addRect(QRectF(e['x'], e['y'], e['l'], e['h']))
            self.noter_fond(ch, p.brush())
        elif t == 'cercle':
            p.setPen(self.stylo(e))
            p.setBrush(self.brosse(e))
            p.drawEllipse(QPointF(e['cx'], e['cy']), e['r'], e['r'])
            ch = QPainterPath()
            ch.addEllipse(QPointF(e['cx'], e['cy']), e['r'], e['r'])
            self.noter_fond(ch, p.brush())
        elif t == 'ellipse':
            p.setPen(self.stylo(e))
            p.setBrush(self.brosse(e))
            p.save()
            p.translate(e['cx'], e['cy'])
            p.rotate(-e.get('rotation', 0))
            p.drawEllipse(QPointF(0, 0), e['rx'], e['ry'])
            ch = QPainterPath()
            ch.addEllipse(QPointF(0, 0), e['rx'], e['ry'])
            self.noter_fond(ch, p.brush())
            p.restore()
        elif t == 'arc':
            cx, cy, r, a1, a2 = e['cx'], e['cy'], e['r'], e['debut'], e['fin']
            ecart = (a2 - a1) % 360 if abs(a2 - a1) < 360 else 359.999
            if ecart == 0:
                ecart = 359.999 if a2 != a1 else 0
            rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
            p.setPen(self.stylo(e))
            if e.get('secteur'):
                p.setBrush(self.brosse(e))
                path = QPainterPath(QPointF(cx, cy))
                path.arcTo(rect, a1, ecart)
                path.closeSubpath()
                p.drawPath(path)
                self.noter_fond(path, p.brush())
            else:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawArc(rect, int(round(a1 * 16)), int(round(ecart * 16)))
        elif t == 'texte':
            self.texte(e)
        elif t == 'carte':
            self.carte(e)
        elif t == 'globe':
            self.globe(e)
        elif t == 'image':
            im = contenu.images_questions().get(str(e.get('ref')))
            img = None
            if im:
                img = self._images.get(im['id'])
                if img is None:
                    img = self._images[im['id']] = QImage(str(contenu.chemin_image(im['fichier'])))
            r = QRectF(e['x'], e['y'], e['l'], e['h'])
            if img is not None and not img.isNull():
                s = min(r.width() / img.width(), r.height() / img.height())
                w, h = img.width() * s, img.height() * s
                ri = QRectF(r.center().x() - w / 2, r.center().y() - h / 2, w, h)
                p.drawImage(ri, img)
                ch = QPainterPath()
                ch.addRect(ri)
                moy = img.scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation).pixelColor(0, 0)
                moy.setAlpha(255)
                self.noter_fond(ch, QBrush(moy))
            else:
                p.fillRect(r, self.coul('gris_fonce'))
        elif t == 'groupe':
            p.save()
            if 'translation' in e:
                p.translate(e['translation'][0], e['translation'][1])
            if 'rotation' in e:
                p.rotate(-e['rotation'])
            if 'echelle' in e:
                p.scale(e['echelle'], e['echelle'])
            if 'opacite' in e:
                p.setOpacity(p.opacity() * e['opacite'])
            if 'decoupe' in e:
                x, y, l, h = e['decoupe']
                p.setClipRect(QRectF(x, y, l, h), Qt.ClipOperation.IntersectClip)
            for x in e.get('elements', []):
                self.elt(x)
            p.restore()

    # ------------------------------------------------------------ texte riche
    def texte(self, e):
        p = self.p
        taille = float(e.get('taille', 14))
        anc = e.get('ancre', 'debut')
        base = e.get('base', 'alphabetique')
        lignes = str(e.get('texte', '')).split('\n')
        n = len(lignes)
        dy0 = {'haut': taille * 0.8, 'milieu': taille * 0.35 - (n - 1) * taille * 1.2 / 2,
               'bas': -(n - 1) * taille * 1.2 - taille * 0.2}.get(base, 0.0)
        f = QFont('Verdana')
        f.setPixelSize(max(1, int(round(taille))))
        f.setBold(bool(e.get('gras')))
        f.setItalic(bool(e.get('italique')))
        jeton = e.get('couleur', 'avant')
        p.save()
        p.translate(e['x'], e['y'])
        if e.get('rotation'):
            p.rotate(-e['rotation'])
        for k, ligne in enumerate(lignes):
            morceaux = []          # (genre, texte, gras)
            for m in re.split(r'(\*\*.+?\*\*)', ligne):
                if not m:
                    continue
                gras = m.startswith('**') and m.endswith('**') and len(m) > 4
                m2 = m[2:-2] if gras else m
                for j, x in enumerate(re.split(r'\$([^$]+)\$', m2)):
                    if x:
                        morceaux.append(('formule' if j % 2 else 'texte', x, gras))
            larg = []
            for g, x, gras in morceaux:
                f2 = QFont(f)
                f2.setBold(f.bold() or gras)
                p.setFont(f2)
                larg.append(formule.largeur(p, x) if g == 'formule' else QFontMetricsF(f2).horizontalAdvance(x))
            total = sum(larg)
            x0 = {'debut': 0.0, 'milieu': -total / 2, 'fin': -total}.get(anc, 0.0)
            y = dy0 + k * taille * 1.2
            milieu = QPointF(x0 + total / 2, y - taille * 0.35)
            if e.get('_reponse'):                       # bonne réponse montrée : orange gardé, lisere si besoin
                couleur = valeur = self.coul(jeton)
                lisere = self.halo(couleur, milieu)
            else:
                couleur = self.lisible(jeton, milieu)
                valeur = self.lisible('valeur', milieu)
                lisere = None
            for (g, x, gras), w in zip(morceaux, larg):
                f2 = QFont(f)
                f2.setBold(f.bold() or gras)
                p.setFont(f2)
                c = valeur if gras else couleur
                if g == 'formule':
                    formule.dessiner(p, x0, y, x, couleur=c)
                elif lisere is not None:
                    ch = QPainterPath()
                    ch.addText(QPointF(x0, y), f2, x)
                    p.strokePath(ch, QPen(lisere, max(2.5, taille * 0.22), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                          Qt.PenJoinStyle.RoundJoin))
                    p.fillPath(ch, c)
                else:
                    p.setPen(c)
                    p.drawText(QPointF(x0, y), x)
                x0 += w
        p.restore()

    # ------------------------------------------------------------ cartes et globes
    def carte(self, e):
        p = self.p
        x0, y0, l, h = e['x'], e['y'], e['l'], e['h']
        lo0, lo1 = e.get('lon_min', -180), e.get('lon_max', 180)
        la0, la1 = e.get('lat_min', -90), e.get('lat_max', 90)
        p.save()
        p.setClipRect(QRectF(x0, y0, l, h), Qt.ClipOperation.IntersectClip)
        p.fillRect(QRectF(x0, y0, l, h), self.coul(e.get('remplissage', 'mer')))
        ch = QPainterPath()
        ch.addRect(QRectF(x0, y0, l, h))
        self.noter_fond(ch, QBrush(self.coul(e.get('remplissage', 'mer'))))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.coul(e.get('terre', 'sol')))
        for poly in cotes():
            p.drawPolygon(QPolygonF([QPointF(x0 + (lo - lo0) / (lo1 - lo0) * l, y0 + (la1 - la) / (la1 - la0) * h)
                                     for lo, la in poly]))
        p.restore()

    def globe(self, e):
        p = self.p
        cx, cy, r = e['cx'], e['cy'], e['r']
        l0, p0 = math.radians(e.get('lon0', 0)), math.radians(e.get('lat0', 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.coul('mer'))
        p.drawEllipse(QPointF(cx, cy), r, r)
        ch = QPainterPath()
        ch.addEllipse(QPointF(cx, cy), r, r)
        self.noter_fond(ch, QBrush(self.coul('mer')))
        p.setBrush(self.coul('sol'))
        c0, s0 = math.cos(p0), math.sin(p0)
        for poly in cotes():
            seg = []
            for lo, la in poly:
                cl, sl, dl = math.cos(math.radians(la)), math.sin(math.radians(la)), math.radians(lo) - l0
                if s0 * sl + c0 * cl * math.cos(dl) < 0:
                    continue
                seg.append(QPointF(cx + r * cl * math.sin(dl), cy - r * (c0 * sl - s0 * cl * math.cos(dl))))
            if len(seg) > 2:
                p.drawPolygon(QPolygonF(seg))
        p.setPen(QPen(self.coul('gris_clair'), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)


def peindre(p: QPainter, fig: dict, cible: QRectF, theme='sombre', reponse=False, indice=False, bonnes=()):
    """Dessine la figure développée dans `cible` (proportions gardées, centrée)."""
    if not fig:
        return
    w, h = fig['vue']
    k = min(cible.width() / max(w, 1e-6), cible.height() / max(h, 1e-6))
    pe = Peintre(p, theme, reponse, indice, bonnes)
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    p.translate(cible.x() + (cible.width() - w * k) / 2, cible.y() + (cible.height() - h * k) / 2)
    p.scale(k, k)
    p.setClipRect(QRectF(0, 0, w, h))
    pe.fond = pe.coul(fig.get('fond', 'fond'))
    p.fillRect(QRectF(0, 0, w, h), pe.fond)
    for e in fig.get('elements', []):
        pe.elt(e)
    p.restore()


class FigureWidget(QWidget):
    """Figure d'une question (ou d'un choix), à rapport fixe ; nom accessible = texte alternatif."""

    def __init__(self, fig: dict, theme='sombre', libelle='', parent=None, hauteur_max=None):
        super().__init__(parent)
        self.fig, self.theme = fig, theme
        self.reponse = self.indice = False
        self.bonnes = ()
        self.hauteur_max = hauteur_max
        self.setAccessibleName(libelle)
        pol = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        pol.setHeightForWidth(True)
        self.setSizePolicy(pol)
        self.setMinimumSize(120, 60)

    def regler(self, reponse, indice, bonnes):
        self.reponse, self.indice, self.bonnes = reponse, indice, bonnes
        self.update()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        h = int(w * self.fig['vue'][1] / max(1, self.fig['vue'][0]))
        return min(h, self.hauteur_max) if self.hauteur_max else h

    def sizeHint(self):
        return QSize(560, self.heightForWidth(560))

    def paintEvent(self, _):
        p = QPainter(self)
        peindre(p, self.fig, QRectF(self.rect()), self.theme, self.reponse, self.indice, self.bonnes)
        p.end()
