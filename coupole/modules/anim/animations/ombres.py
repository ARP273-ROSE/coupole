"""Eclipse Shadow Simulator : Terre et Lune à déplacer à la souris, avec leurs cônes d'ombre (umbra) et de
pénombre, tracés par les tangentes communes au Soleil et au corps (géométrie du simulateur d'origine).  Le type
d'éclipse produit est indiqué.  Un encart donne les proportions réelles d'une éclipse centrale de Lune (méthode
d'Aristarque : l'ombre de la Terre, à la distance de la Lune, fait environ 2,65 diamètres lunaires)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, duree_hm, nombre

R_SOLEIL, R_TERRE, R_LUNE = 60.0, 22.0, 9.0           # rayons à l'écran (proportions de l'original, pas à l'échelle)


def geometrie(sx, sy, ox, oy, r_source, r_objet, loin: float = 3000.0) -> dict:
    """Points des cônes d'ombre et de pénombre d'un disque (ox, oy, r_objet) éclairé par (sx, sy, r_source)."""
    d = math.hypot(ox - sx, oy - sy)
    ang = math.atan2(oy - sy, ox - sx)
    ca, sa = math.cos(ang), math.sin(ang)

    def rep(x, y):                          # repère (Soleil à l'origine, objet sur +x) → écran
        return QPointF(sx + ca * x - sa * y, sy + sa * x + ca * y)

    s_a = min(0.999, (r_source + r_objet) / d)
    a = math.asin(s_a)
    x2, y2 = d - r_objet * s_a, r_objet * math.cos(a)
    x3 = r_source / s_a
    x4, y4 = loin, (loin - x3) * math.tan(a)
    s_b = (r_source - r_objet) / d
    b = math.asin(s_b)
    x6, y6 = d + r_objet * s_b, r_objet * math.cos(b)
    x7 = d + r_objet / s_b
    y8 = (loin - x7) * math.tan(b)
    return {'penombre': [rep(x2, y2), rep(x4, y4), rep(x4, -y4), rep(x2, -y2)],
            'ombre': [rep(x6, y6), rep(x7, 0), rep(x6, -y6)],
            'antiombre': [rep(x7, 0), rep(loin, y8), rep(loin, -y8)],
            'axe': (ca, sa), 'd': d, 'sommet': x7 - d, 'k_ombre': s_b,
            'k_penombre': (r_source + r_objet) / d}


def type_eclipse(sx, sy, ox, oy, r_objet, cx, cy, r_cible) -> str:
    """Ombre portée par l'objet (ox, oy) sur la cible (cx, cy) : 'totale', 'annulaire', 'partielle',
    'penombre' ou ''."""
    d = math.hypot(ox - sx, oy - sy)
    ux, uy = (ox - sx) / d, (oy - sy) / d
    x = (cx - ox) * ux + (cy - oy) * uy                   # distance derrière l'objet, le long de l'axe
    if x <= 0:
        return ''
    dist = abs(-(cx - ox) * uy + (cy - oy) * ux)
    k_u = (R_SOLEIL - r_objet) / d
    k_p = (R_SOLEIL + r_objet) / d
    ru = r_objet - x * k_u
    rp = r_objet + x * k_p
    if dist - r_cible >= rp:
        return ''
    if ru > 0:
        if dist + r_cible <= ru:
            return 'totale'
        if dist - r_cible < ru:
            return 'partielle'
        return 'penombre'
    if dist < -ru - r_cible:                                # dans l'antiombre (le cône prolongé)
        return 'annulaire'
    return 'partielle' if dist - r_cible < -ru else 'penombre'


class OmbresEclipse(Animation):
    ID = 'shadowsim'
    ANIMEE = False

    def construire(self):
        self.terre = None
        self.lune = None
        self.c_reel = self.coche('reel', True)
        self._rect = None

    def etat_initial(self):
        self.terre = None
        self.lune = None

    def _positions(self, rect):
        if self.terre is None:
            self.terre = (0.55, 0.5)
            self.lune = (0.80, 0.5)
        t = QPointF(rect.x() + self.terre[0] * rect.width(), rect.y() + self.terre[1] * rect.height())
        lu = QPointF(rect.x() + self.lune[0] * rect.width(), rect.y() + self.lune[1] * rect.height())
        return t, lu

    def presser(self, pos, bouton):
        if self._rect is None:
            return False
        t, lu = self._positions(self._rect)
        for nom, q, r in (('lune', lu, R_LUNE), ('terre', t, R_TERRE)):
            if math.hypot(pos.x() - q.x(), pos.y() - q.y()) <= r + 6:
                self._glisse = lambda p, n=nom: self._tirer(n, p)
                return True
        return False

    def _tirer(self, nom, pos):
        r = self._rect
        x = (pos.x() - r.x()) / r.width()
        y = (pos.y() - r.y()) / r.height()
        sx = (r.x() + R_SOLEIL * 0.4 - r.x()) / r.width()
        x = max(sx + (R_SOLEIL + 30) / r.width(), min(0.98, x))
        y = max(0.02, min(0.98, y))
        setattr(self, nom, (x, y))

    def _eclipses(self):
        r = self._rect
        if r is None:
            return '', ''
        t, lu = self._positions(r)
        sx, sy = r.x() + R_SOLEIL * 0.4, r.center().y()
        lunaire = type_eclipse(sx, sy, t.x(), t.y(), R_TERRE, lu.x(), lu.y(), R_LUNE)
        solaire = type_eclipse(sx, sy, lu.x(), lu.y(), R_LUNE, t.x(), t.y(), R_TERRE)
        return lunaire, solaire

    def valeurs(self):
        lunaire, solaire = self._eclipses()
        e = astro.eclipse_de_lune()
        out = [(tr('anim_shadowsim_lunaire'), tr('anim_shadowsim_' + (lunaire or 'aucune'))),
               (tr('anim_shadowsim_solaire'), tr('anim_shadowsim_' + (solaire or 'aucune')))]
        if self.c_reel.isChecked():
            out += [(tr('anim_shadowsim_rayon_ombre'), '%s km (%s × %s)' % (
                        nombre(e['rayon_ombre_km'], 0), nombre(e['ombre_en_diametres_lunaires'], 2),
                        tr('anim_shadowsim_diam_lune'))),
                    (tr('anim_shadowsim_longueur_ombre'), '%s km' % nombre(e['longueur_ombre_km'], 0)),
                    (tr('anim_shadowsim_totalite'), duree_hm(e['totalite_h'])),
                    (tr('anim_shadowsim_phase_ombre'), duree_hm(e['ombre_totale_h']))]
        return out

    def dessiner(self, p, rect):
        reel = self.c_reel.isChecked()
        principal = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * (0.72 if reel else 1.0))
        self._rect = principal
        t, lu = self._positions(principal)
        sx, sy = principal.x() + R_SOLEIL * 0.4, principal.center().y()
        p.save()
        p.setClipRect(principal)
        for (ox, oy), r in (((t.x(), t.y()), R_TERRE), ((lu.x(), lu.y()), R_LUNE)):
            g = geometrie(sx, sy, ox, oy, R_SOLEIL, r)
            p.setPen(dessin.stylo('grille', 0.8, 0.6))
            p.setBrush(dessin.c('penombre', 0.22))
            p.drawPolygon(QPolygonF(g['penombre']))
            p.setBrush(dessin.c('umbra', 0.85))
            p.drawPolygon(QPolygonF(g['ombre']))
            p.setPen(dessin.stylo('grille', 1.0, 0.8, pointille=True))
            a = g['antiombre']
            p.drawLine(a[0], a[1])
            p.drawLine(a[0], a[2])
        dessin.disque(p, sx, sy, R_SOLEIL, 'soleil')
        dessin.disque(p, t.x(), t.y(), R_TERRE, 'terre', bord='texte')
        dessin.disque(p, lu.x(), lu.y(), R_LUNE, 'lune', bord='texte')
        p.restore()
        dessin.texte(p, t.x(), t.y() - R_TERRE - 10, tr('anim_shadowsim_terre'), fond=True)
        dessin.texte(p, lu.x(), lu.y() - R_LUNE - 10, tr('anim_shadowsim_lune'), fond=True)
        dessin.police(p, 0.85)
        dessin.texte(p, principal.x() + 8, principal.bottom() - 10, tr('anim_shadowsim_aide_souris'), 'doux',
                     centre=False)
        dessin.police(p, 1 / 0.85)
        if reel:
            self._aristarque(p, QRectF(rect.x(), principal.bottom(), rect.width(), rect.height() - principal.height()))

    def _aristarque(self, p, r):
        """Traversée centrale de l'ombre de la Terre par la Lune, proportions réelles."""
        r = dessin.cadre(p, r, tr('anim_shadowsim_titre_reel'))
        e = astro.eclipse_de_lune()
        k = min(r.height() * 0.42 / e['rayon_penombre_km'], r.width() * 0.2 / e['rayon_penombre_km'])
        cx, cy = r.x() + r.width() * 0.35, r.center().y()
        dessin.disque(p, cx, cy, e['rayon_penombre_km'] * k, 'penombre', alpha=0.25)
        dessin.disque(p, cx, cy, e['rayon_ombre_km'] * k, 'umbra', alpha=0.9)
        rl = astro.R_LUNE_KM * k
        for dx in (-(e['rayon_ombre_km'] + astro.R_LUNE_KM), -(e['rayon_ombre_km'] - astro.R_LUNE_KM), 0.0,
                   e['rayon_ombre_km'] - astro.R_LUNE_KM, e['rayon_ombre_km'] + astro.R_LUNE_KM):
            p.setPen(dessin.stylo('lune', 1.2))
            p.setBrush(dessin.c('lune', 0.15))
            p.drawEllipse(QPointF(cx + dx * k, cy), rl, rl)
        x = r.x() + r.width() * 0.62
        dessin.texte(p, x, r.y() + 14, tr('anim_shadowsim_rapport', x=nombre(e['ombre_en_diametres_lunaires'], 2)),
                     centre=False)
        dessin.texte(p, x, r.y() + 34, tr('anim_shadowsim_duree_tot', d=duree_hm(e['totalite_h'])), centre=False)
