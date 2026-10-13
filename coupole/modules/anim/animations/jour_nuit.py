"""Daylight Simulator : carte plane de la Terre avec la zone de jour et de nuit.  Le point subsolaire est à la
latitude δ☉ et à la longitude où il est midi solaire vrai ; la zone éclairée glisse vers l'ouest au fil du jour
(15° par heure) et son contour change au fil de l'année.  Animation « jour » (l'heure avance) ou « année » (la
date avance à heure fixe)."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, date_du_jour, heures_minutes
from .longitude_latitude import cotes, decimal

ANNEE = 2026


def subsolaire(jour: float) -> tuple[float, float]:
    """(latitude, longitude) du point subsolaire au « jour » (fraction = temps universel)."""
    s = astro.soleil_jour(ANNEE, jour)
    tu = (jour % 1.0) * 24.0
    lon = -((tu - 12.0) * 15.0 + s['eqt'] / 4.0)
    return s['delta'], astro.mod180(lon)


def latitude_terminateur(lon: np.ndarray, dec: float, lon_ss: float) -> np.ndarray:
    """Latitude du terminateur (h = 0) pour chaque longitude : tan φ = −cos H / tan δ."""
    h = np.radians(lon - lon_ss)
    d = math.radians(dec if abs(dec) > 1e-6 else 1e-6)
    return np.degrees(np.arctan(-np.cos(h) / math.tan(d)))


def latitude_hauteur(lon: float, dec: float, lon_ss: float, h: float) -> float:
    """Latitude où le Soleil est à la hauteur h (degrés) le long du méridien `lon`, du côté nuit du terminateur :
    a sin φ + b cos φ = sin h, avec a = sin δ, b = cos δ cos H.  Sans solution : pôle obscur."""
    hh = math.radians(lon - lon_ss)
    a, b = math.sin(math.radians(dec)), math.cos(math.radians(dec)) * math.cos(hh)
    rr = math.hypot(a, b)
    if rr < 1e-12 or abs(math.sin(math.radians(h)) / rr) > 1:
        return -90.0 if dec >= 0 else 90.0
    psi = math.atan2(b, a)
    base = math.asin(math.sin(math.radians(h)) / rr)
    sols = []
    for phi in (base - psi, math.pi - base - psi):
        phi = (phi + math.pi) % (2 * math.pi) - math.pi
        if -math.pi / 2 - 1e-9 <= phi <= math.pi / 2 + 1e-9:
            sols.append(math.degrees(phi))
    if not sols:
        return -90.0 if dec >= 0 else 90.0
    ref = float(latitude_terminateur(np.array([lon]), dec, lon_ss)[0])
    # côté nuit : vers le pôle obscur depuis le terminateur
    nuit = [x for x in sols if (x <= ref + 1e-9 if dec >= 0 else x >= ref - 1e-9)]
    return (nuit or sols)[0]


class JourNuit(Animation):
    ID = 'daylightsimulator'
    HEURES_PAR_S = 1.0
    JOURS_PAR_S = 10.0

    def construire(self):
        self.mode = self.choix('mode', [('anim_daylightsimulator_jour', 'jour'),
                                        ('anim_daylightsimulator_annee', 'annee')], 'jour')
        self.jour = self.curseur('jour', 0.0, 364.0, 79.0, dec=0, cle_texte='anim_c_jour')
        self.heure = self.curseur('heure', 0.0, 24.0, 12.0, dec=2, unite='h', cle_texte='anim_daylightsimulator_tu')
        self.lat = self.curseur('latitude', -90.0, 90.0, 0.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.lon = self.curseur('longitude', -180.0, 180.0, 0.0, dec=1, unite='°', cle_texte='anim_c_longitude')
        self.c_crepuscule = self.coche('crepuscule', False)
        self._carte = None

    def avancer(self, dt):
        if self.mode.currentData() == 'jour':
            h = self.heure.value() + dt * self.HEURES_PAR_S
            if h >= 24.0:
                self.jour.setValue((self.jour.value() + 1) % 365.0)
            self.heure.setValue(h % 24.0)
        else:
            self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def _jour(self):
        return self.jour.value() + self.heure.value() / 24.0

    def valeurs(self):
        dec, lon_ss = subsolaire(self._jour())
        h_obs = astro.mod180(self.lon.value() - lon_ss) / 15.0 + 12.0
        s = astro.soleil_jour(ANNEE, self._jour())
        az, alt = astro.equatorial_vers_horizon(astro.mod180(self.lon.value() - lon_ss), dec, self.lat.value())
        return [(tr('anim_c_date'), date_du_jour(self.jour.value()) + ', ' + heures_minutes(self.heure.value()) + ' TU'),
                (tr('anim_daylightsimulator_subsolaire'), '%s, %s' % (
                    decimal(dec, tr('anim_pc_n'), tr('anim_pc_s')), decimal(lon_ss, tr('anim_pc_e'), tr('anim_pc_o')))),
                (tr('anim_sunmotions_heure_vraie'), heures_minutes(h_obs)),
                (tr('anim_daylightsimulator_h_soleil'), angle(alt))]

    def presser(self, pos, bouton):
        if self._carte is not None and self._carte.contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        r = self._carte
        self.lon.setValue(max(-180.0, min(180.0, (pos.x() - r.x()) / r.width() * 360.0 - 180.0)))
        self.lat.setValue(max(-90.0, min(90.0, 90.0 - (pos.y() - r.y()) / r.height() * 180.0)))

    def dessiner(self, p, rect):
        w = min(rect.width() - 20, (rect.height() - 20) * 2.0)
        carte = QRectF(rect.center().x() - w / 2, rect.center().y() - w / 4, w, w / 2)
        self._carte = carte

        def xy(la, lo):
            return QPointF(carte.x() + (lo + 180.0) / 360.0 * carte.width(), carte.y() + (90.0 - la) / 180.0 *
                           carte.height())
        p.fillRect(carte, dessin.c('terre', 0.35))
        p.setPen(dessin.stylo('texte', 0.8, 0.8))
        for poly in cotes():
            if len(poly) < 5:
                continue
            la = np.degrees(np.arcsin(np.clip(poly[:, 2], -1, 1)))
            lo = np.degrees(np.arctan2(poly[:, 1], poly[:, 0]))
            pts = []
            for i in range(len(la)):
                if pts and abs(lo[i] - lo[i - 1]) > 180:
                    p.drawPolyline(QPolygonF(pts))
                    pts = []
                pts.append(xy(la[i], lo[i]))
            if len(pts) > 1:
                p.drawPolyline(QPolygonF(pts))
        dec, lon_ss = subsolaire(self._jour())
        lons = np.linspace(-180.0, 180.0, 361)
        # nuit : du terminateur jusqu'au pôle plongé dans l'obscurité (pôle Sud si δ > 0)
        for decalage, alpha in (((0.0, 0.55),) + (((6.0, 0.25), (12.0, 0.2), (18.0, 0.15))
                                                  if self.c_crepuscule.isChecked() else ())):
            if decalage == 0.0:
                lats = latitude_terminateur(lons, dec, lon_ss)
            else:
                # courbe de hauteur −decalage : sin h = sin φ sin δ + cos φ cos δ cos H, résolue en φ
                lats = np.array([latitude_hauteur(lo, dec, lon_ss, -decalage) for lo in lons])
            pole = -90.0 if dec >= 0 else 90.0
            poly = [xy(la, lo) for la, lo in zip(lats, lons)] + [xy(pole, 180.0), xy(pole, -180.0)]
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c('nuit', alpha))
            p.drawPolygon(QPolygonF(poly))
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawRect(carte)
        q = xy(dec, lon_ss)
        dessin.disque(p, q.x(), q.y(), 8, 'soleil', bord='fond')
        o = xy(self.lat.value(), self.lon.value())
        dessin.disque(p, o.x(), o.y(), 5, 'accent3', bord='fond')
        dessin.police(p, 1.1, gras=True)
        dessin.texte(p, rect.x() + 12, rect.y() + 18, date_du_jour(self.jour.value()) + ', ' +
                     heures_minutes(self.heure.value()) + ' TU', centre=False)
        dessin.police(p, 1 / 1.1)
