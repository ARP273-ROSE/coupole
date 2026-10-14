"""Longitude/Latitude Demonstrator : globe interactif, côtes, villes, équateur, méridien d'origine, ligne de
changement de date ; un point à déplacer dont la latitude et la longitude s'affichent (décimal ou sexagésimal)."""
from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre

# Villes du simulateur d'origine (latitude, longitude en degrés et minutes ; la latitude de Lincoln, notée « W »
# dans l'original, est 40° 49′ N)
VILLES = (('buenos_aires', -34, 20, -58, 30), ('lima', -12, 6, -76, 55), ('casablanca', 33, 32, -7, 41),
          ('monrovia', 6, 20, -10, 46), ('sao_paulo', -23, 34, -46, 38), ('lincoln', 40, 49, -96, 40),
          ('bagdad', 33, 14, 44, 22), ('greenwich', 51, 40, 0, 0), ('singapour', 1, 22, 103, 45),
          ('la_havane', 23, 8, -82, 23), ('canberra', -35, 18, 149, 8), ('calcutta', 22, 32, 88, 22),
          ('pekin', 39, 55, 116, 23), ('reykjavik', 64, 9, -21, 58), ('mourmansk', 68, 59, 33, 8),
          ('washington', 38, 53, -77, 2), ('barrow', 71, 17, -156, 47), ('moscou', 55, 45, 37, 37),
          ('le_cap', -33, 55, 18, 27), ('mcmurdo', -77, 51, 166, 40))

# Ligne de changement de date (tracé simplifié de l'original), (latitude, longitude)
LIGNE_DATE = ((90, 180), (75, 180), (72, -169), (65.5, -169), (64, -175), (50.5, 167), (48, 180), (2, 180),
              (0, -179), (0, -165), (-3, -165), (-3, -160), (2, -160), (2, -162), (5, -162), (5, -154),
              (-8, -151), (-12, -151), (-12, -157), (-9, -157), (-9, -178), (-15, -175.5), (-44.75, -175.5),
              (-51.5, 180), (-90, 180))

_COTES = None
_COTES_TOUT = None
_CHEMIN_CARTE = None


def _lire_cotes() -> list:
    """Lignes de côte (Natural Earth 1:50m simplifié, domaine public) : liste de tableaux (N, 2) (longitude,
    latitude), lus une fois, au premier globe ou à la première carte affichés (chargement à la demande)."""
    doc = json.loads(gzip.decompress((Path(__file__).resolve().parents[1] / 'donnees' / 'cotes.json.gz').read_bytes()))
    return [np.asarray(poly, dtype=float) for poly in doc['polygones']]


def cotes():
    """Lignes de côte → liste de tableaux (N, 3) sur la sphère unité (chargées une fois)."""
    global _COTES
    if _COTES is None:
        _COTES = [globe_xyz(q[:, 1], q[:, 0]) for q in _lire_cotes()]
    return _COTES


def _cotes_tout():
    """Toutes les côtes dans un seul tableau (N, 3), et le masque des segments à ne pas tracer (entre deux lignes)."""
    global _COTES_TOUT
    if _COTES_TOUT is None:
        lignes = cotes()
        pts = np.vstack(lignes)
        relie = np.ones(len(pts) - 1, dtype=bool)
        fins = np.cumsum([len(q) for q in lignes])[:-1]
        relie[fins - 1] = False
        _COTES_TOUT = (pts, relie)
    return _COTES_TOUT


def dessiner_cotes_globe(pe, cle: str = 'doux', epaisseur: float = 1.0, alpha: float = 0.9):
    """Côtes de la face visible d'un globe (Peintre3D sans transformation) : une projection numpy de tous les points,
    puis un tracé par morceau visible."""
    pts, relie = _cotes_tout()
    x, y, z = pe.vue.projeter(pts)
    vis = relie & (z[:-1] >= 0) & (z[1:] >= 0)
    if not vis.any():
        return
    d = np.flatnonzero(np.diff(np.concatenate(([0], vis.astype(np.int8), [0]))))
    xs, ys = pe.cx + pe.r * x, pe.cy - pe.r * y
    pe.p.setPen(dessin.stylo(cle, epaisseur, alpha))
    pe.p.setBrush(Qt.BrushStyle.NoBrush)
    for a, b in zip(d[0::2].tolist(), d[1::2].tolist()):
        pe.p.drawPolyline(dessin.polygone(xs[a:b + 1], ys[a:b + 1]))


def chemin_carte():
    """Côtes en projection équirectangulaire, dans le repère (longitude, −latitude) en degrés (chemin mis en cache,
    coupé au passage de la ligne ±180°)."""
    global _CHEMIN_CARTE
    if _CHEMIN_CARTE is None:
        from PyQt6.QtGui import QPainterPath
        ch = QPainterPath()
        for q in _lire_cotes():
            lo, la = q[:, 0], q[:, 1]
            coupe = np.flatnonzero(np.abs(np.diff(lo)) > 180) + 1
            for morceau in np.split(np.arange(len(lo)), coupe):
                if len(morceau) < 2:
                    continue
                ch.addPolygon(dessin.polygone(lo[morceau], -la[morceau]))
        _CHEMIN_CARTE = ch
    return _CHEMIN_CARTE


def dessiner_cotes_carte(p, carte, cle: str = 'doux', epaisseur: float = 0.8, alpha: float = 0.8):
    """Côtes sur une carte équirectangulaire occupant le rectangle `carte` (longitude −180…180, latitude 90…−90)."""
    p.save()
    p.setClipRect(carte)
    p.translate(carte.x() + carte.width() / 2, carte.y() + carte.height() / 2)
    p.scale(carte.width() / 360.0, carte.height() / 180.0)
    pen = dessin.stylo(cle, epaisseur, alpha)
    pen.setCosmetic(True)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(chemin_carte())
    p.restore()


def globe_xyz(lat, lon) -> np.ndarray:
    """Repère terrestre direct : x = (0°, 0°), y = (0°, 90° E), z = pôle Nord."""
    lat, lon = np.radians(np.asarray(lat, dtype=float)), np.radians(np.asarray(lon, dtype=float))
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)


def sexagesimal(x: float, positif: str, negatif: str) -> str:
    """43,6047 → « 43° 36′ 17″ N »."""
    s = positif if x >= 0 else negatif
    a = abs(x)
    d = int(a)
    m = int((a - d) * 60)
    sec = (a - d - m / 60) * 3600
    if sec >= 59.5:
        sec, m = 0.0, m + 1
    if m >= 60:
        m, d = 0, d + 1
    return '%d° %02d′ %02d″ %s' % (d, m, int(round(sec)), s)


def decimal(x: float, positif: str, negatif: str) -> str:
    return '%s° %s' % (nombre(abs(x), 2), positif if x >= 0 else negatif)


class LongitudeLatitude(Animation):
    ID = 'longlat'
    ANIMEE = False

    def construire(self):
        self.globe = self.vue(75.0, 25.0, -89.0, 89.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 40.8, dec=2, unite='°', cle_texte='anim_c_latitude')
        self.lon = self.curseur('longitude', -180.0, 180.0, -96.7, dec=2, unite='°', cle_texte='anim_c_longitude')
        self.format = self.choix('format', [('anim_longlat_decimal', 'd'), ('anim_longlat_sexagesimal', 's')], 'd')
        self.c_reperes = self.coche('reperes', True)
        self.c_villes = self.coche('villes', False)
        self._zone = None

    def _textes(self):
        n, s, e, o = tr('anim_pc_n'), tr('anim_pc_s'), tr('anim_pc_e'), tr('anim_pc_o')
        f = sexagesimal if self.format.currentData() == 's' else decimal
        return f(self.lat.value(), n, s), f(self.lon.value(), e, o)

    def valeurs(self):
        la, lo = self._textes()
        return [(tr('anim_c_latitude'), la), (tr('anim_c_longitude'), lo)]

    # ------------------------------------------------------------ souris : déplacer le point ou tourner le globe
    def presser(self, pos, bouton):
        z = self._zone
        if z is None:
            return super().presser(pos, bouton)
        pe = z
        v = pe.depuis_ecran(pos.x(), pos.y())
        point = globe_xyz(self.lat.value(), self.lon.value())
        x, y, prof, _ = pe.ecran(point)
        if v is not None and prof[0] >= 0 and math.hypot(pos.x() - x[0], pos.y() - y[0]) < 14:
            self._glisse = self._deplacer_point
            return True
        if v is not None and bouton == Qt.MouseButton.RightButton:
            self._placer(v)
            return True
        return super().presser(pos, bouton)

    def _placer(self, v):
        self.lat.setValue(math.degrees(math.asin(max(-1.0, min(1.0, v[2])))))
        self.lon.setValue(math.degrees(math.atan2(v[1], v[0])))

    def _deplacer_point(self, pos):
        if self._zone is None:
            return
        v = self._zone.depuis_ecran(pos.x(), pos.y())
        if v is not None:
            self._placer(v)

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        r = min(rect.width(), rect.height()) * 0.42
        cx, cy = rect.center().x(), rect.center().y() + 4
        pe = dessin.Peintre3D(p, self.globe, cx, cy, r)
        self._zone = pe
        self.zone_rotative(rect, self.globe)
        pe.contour('grille', 'terre', 0.25)
        for lat in range(-60, 90, 30):                          # graticule pâle
            if lat:
                pe.courbe(dessin.cercle((0, 0, 1), 90 - lat), 'grille', 0.8, 0.6, arriere='cache')
        for lon in range(0, 180, 30):
            pe.courbe(dessin.cercle((math.sin(math.radians(lon)), -math.cos(math.radians(lon)), 0)), 'grille', 0.8,
                      0.6, arriere='cache')
        dessiner_cotes_globe(pe)
        if self.c_reperes.isChecked():
            pe.courbe(dessin.cercle((0, 0, 1)), 'equateur', 2.0, arriere='cache')
            pe.courbe(globe_xyz(np.linspace(-90, 90, 91), np.zeros(91)), 'accent1', 2.0, arriere='cache')
            pts = []
            for (la0, lo0), (la1, lo1) in zip(LIGNE_DATE[:-1], LIGNE_DATE[1:]):
                pts.append(dessin.arc(globe_xyz(la0, lo0), globe_xyz(la1, lo1), 12))
            pe.courbe(np.vstack(pts), 'accent1', 1.5, arriere='cache')
            pe.etiquette(globe_xyz(0, -self.globe.az + 25) * 1.08, tr('anim_longlat_equateur'), 'equateur')
            pe.etiquette(globe_xyz(45, 0) * 1.1, tr('anim_longlat_greenwich'), 'accent1')
            pe.etiquette(globe_xyz(30, 180) * 1.1, tr('anim_longlat_ligne_date'), 'accent1')
        if self.c_villes.isChecked():
            for cle, lad, lam, lod, lom in VILLES:
                la = lad + math.copysign(lam / 60, lad if lad else 1)
                lo = lod + math.copysign(lom / 60, lod if lod else 1)
                xs, ys, zs, _ = pe.ecran(globe_xyz(la, lo))
                if zs[0] > 0.05:
                    dessin.disque(p, xs[0], ys[0], 3.0, 'accent2')
                    dessin.police(p, 0.8)
                    dessin.texte(p, xs[0] + 5, ys[0] - 3, tr('anim_ville_' + cle), 'doux', centre=False)
                    dessin.police(p, 1 / 0.8)
        # arcs de latitude (le long du méridien du lieu) et de longitude (le long de l'équateur)
        la, lo = self.lat.value(), self.lon.value()
        pe.courbe(globe_xyz(np.linspace(0, la, 60), np.full(60, lo)), 'arc1', 3.0, arriere='pale')
        pe.courbe(globe_xyz(np.zeros(60), np.linspace(0, lo, 60)), 'arc2', 3.0, arriere='pale')
        pe.courbe(globe_xyz(np.full(181, la), np.linspace(-180, 180, 181)), 'grille', 1.0, 0.9, arriere='cache')
        pe.courbe(globe_xyz(np.linspace(-90, 90, 91), np.full(91, lo)), 'grille', 1.0, 0.9, arriere='cache')
        t_la, t_lo = self._textes()
        pe.etiquette(globe_xyz(la / 2, lo) * 1.02, t_la, 'arc1')
        pe.etiquette(globe_xyz(-6, lo / 2) * 1.02, t_lo, 'arc2')
        pe.point(globe_xyz(la, lo), 'soleil', 6.0, bord='fond')
