"""Big Dipper Clock : les étoiles tournent autour de l'étoile Polaire, d'un tour par jour sidéral (23 h 56 min) ;
à heure fixe, elles avancent d'environ 1° par jour au fil des saisons.  Le ciel du nord est dessiné en projection
stéréographique centrée sur le pôle céleste (les étoiles y tournent sans se déformer), avec l'horizon de
l'observateur ; positions J2000 (SIMBAD) précessées à la date, temps sidéral IAU 1982, Soleil de Meeus pour la
couleur du ciel (nuit noire sous −7°, comme l'original)."""
from __future__ import annotations

import datetime
import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainterPath, QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, date_du_jour, heures_minutes, jour_de_date
from ..etoiles_reelles import couleur_reelle, reelle

ANNEE = 2026
# (nom, α J2000 en degrés, δ J2000, magnitude V) — SIMBAD ; η UMi sans magnitude V dans SIMBAD : 4,95 (BSC)
ETOILES = {
    'dubhe': (165.93196, 61.75103, 1.79), 'merak': (165.46033, 56.38243, 2.37), 'phecda': (178.45770, 53.69476, 2.44),
    'megrez': (183.85650, 57.03262, 3.32), 'alioth': (193.50729, 55.95982, 1.77), 'mizar': (200.98142, 54.92535, 2.22),
    'alkaid': (206.88516, 49.31327, 1.86),
    'polaire': (37.95456, 89.26411, 2.02), 'yildun': (263.05416, 86.58646, 4.34), 'eps_umi': (251.49268, 82.03726, 4.21),
    'zet_umi': (236.01466, 77.79449, 4.27), 'eta_umi': (244.37613, 75.75534, 4.95), 'kochab': (222.67636, 74.15550, 2.08),
    'pherkad': (230.18210, 71.83403, 3.00),
    'caph': (2.29452, 59.14978, 2.27), 'schedar': (10.12685, 56.53733, 2.23), 'navi': (14.17721, 60.71674, 2.39),
    'ruchbah': (21.45396, 60.23528, 2.68), 'segin': (28.59889, 63.67010, 3.37),
}
FIGURES = {
    'grande_ourse': ('dubhe', 'merak', 'phecda', 'megrez', 'alioth', 'mizar', 'alkaid', None, 'megrez', 'dubhe'),
    'petite_ourse': ('polaire', 'yildun', 'eps_umi', 'zet_umi', 'kochab', 'pherkad', 'eta_umi', 'zet_umi'),
    'cassiopee': ('caph', 'schedar', 'navi', 'ruchbah', 'segin'),
}
ETIQUETTES = {'grande_ourse': 'megrez', 'petite_ourse': 'kochab', 'cassiopee': 'navi', 'polaire': 'polaire'}
CREPUSCULE = 7.0


def ciel(jour: float, heure: float, lat: float) -> dict:
    """Temps sidéral local (degrés, observateur sur le méridien de Greenwich : heure = temps universel), Soleil,
    et angle horaire / déclinaison de chaque étoile (précessée à la date)."""
    jj = astro.jj_jour_de_l_annee(ANNEE, jour + heure / 24.0)
    tsl = astro.tsmg(jj)
    s = astro.soleil(jj)
    _, h_sol = astro.equatorial_vers_horizon(tsl - s['alpha'], s['delta'], lat)
    etoiles = {}
    for n, (ra, dec, mag) in ETOILES.items():
        r, d = astro.precession(ra, dec, jj)
        etoiles[n] = (astro.mod(tsl - r, 360.0), d, mag)
    return {'tsl': tsl, 'h_soleil': h_sol, 'etoiles': etoiles}


def stereo(h: float, dec: float) -> tuple[float, float]:
    """Projection stéréographique centrée sur le pôle nord céleste, vue vers le nord : le méridien supérieur (H = 0)
    au-dessus du pôle, l'ouest à gauche.  Rend (x, y) avec y vers le haut, rayon 2 tan(p / 2)."""
    r = 2 * math.tan(math.radians(90.0 - dec) / 2)
    return -r * math.sin(math.radians(h)), r * math.cos(math.radians(h))


class HorlogeGrandeOurse(Animation):
    ID = 'dipperclock'
    HEURES_PAR_S = 1.0
    FICHES = True

    def construire(self):
        self.jour = self.curseur('jour', 0.0, 364.0, 78.0, dec=0, cle_texte='anim_c_jour')
        self.heure = self.curseur('heure', 0.0, 24.0, 1.2, dec=2, unite='h', cle_texte='anim_c_heure')
        self.lat = self.curseur('latitude', 10.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.c_noms = self.coche('noms', True)
        self.bouton('anim_dipperclock_maintenant', self.maintenant)

    def maintenant(self):
        t = datetime.datetime.now()
        self.jour.setValue(min(364, jour_de_date(t.month, min(t.day, 28) if t.month == 2 else t.day)))
        self.heure.setValue(t.hour + t.minute / 60.0)

    def avancer(self, dt):
        h = self.heure.value() + dt * self.HEURES_PAR_S
        if h >= 24.0:
            h -= 24.0
            self.jour.setValue((self.jour.value() + 1) % 365)
        self.heure.setValue(h)

    def valeurs(self):
        c = ciel(self.jour.value(), self.heure.value(), self.lat.value())
        h_do = c['etoiles']['dubhe'][0]
        return [(tr('anim_c_date'), date_du_jour(self.jour.value())), (tr('anim_c_heure'), heures_minutes(self.heure.value())),
                (tr('anim_c_tsl'), heures_minutes(c['tsl'] / 15.0)),
                (tr('anim_lunar_applet_h_soleil'), angle(c['h_soleil'])),
                (tr('anim_dipperclock_dubhe'), heures_minutes(h_do / 15.0))]

    def dessiner(self, p, rect):
        c = ciel(self.jour.value(), self.heure.value(), self.lat.value())
        cx, cy = rect.center().x(), rect.y() + rect.height() * 0.46
        k = min(rect.width(), rect.height()) * 0.5 / 1.05
        nuit = max(0.0, min(1.0, -c['h_soleil'] / CREPUSCULE))          # 0 : jour, 1 : nuit noire
        p.fillRect(rect, dessin.c('ciel', 0.9 - 0.75 * nuit))
        lat = self.lat.value()

        def q(h, d):
            x, y = stereo(h, d)
            return QPointF(cx + k * x, cy - k * y)

        # horizon et sol : points d'azimut −120° à +120° (autour du nord) à hauteur 0
        pts = []
        for az in np.linspace(-150.0, 150.0, 121):
            h, d = astro.horizon_vers_equatorial(az % 360.0, 0.0, lat)
            pts.append(q(h, d))
        sol = QPainterPath()
        sol.addPolygon(QPolygonF(pts + [QPointF(rect.right() + 10, rect.bottom() + 10),
                                        QPointF(rect.x() - 10, rect.bottom() + 10)]))
        sol.closeSubpath()
        p.setPen(dessin.stylo('horizon', 1.5))
        p.setBrush(dessin.c('sol', 0.95))
        p.drawPath(sol)
        dessin.texte(p, q(*astro.horizon_vers_equatorial(0.0, 0.0, lat)).x(),
                     q(*astro.horizon_vers_equatorial(0.0, 0.0, lat)).y() + 14, tr('anim_pc_n'), 'horizon')
        # étoiles et figures (au-dessus de l'horizon seulement)
        if nuit > 0.05:
            vis = {n: q(h, d) for n, (h, d, _) in c['etoiles'].items()
                   if astro.equatorial_vers_horizon(h, d, lat)[1] > -0.5}
            p.setPen(dessin.stylo('accent2', 1.2, 0.55 * nuit))
            for fig in FIGURES.values():
                for a, b in zip(fig, fig[1:]):
                    if a and b and a in vis and b in vis:
                        p.drawLine(vis[a], vis[b])
            for n, pt in vis.items():
                mag = c['etoiles'][n][2]
                # couleur vraie (corps noir à T_eff) ; un fin contour la garde visible sur un ciel clair
                r = max(1.5, 4.2 - 0.6 * mag)
                col = couleur_reelle('dipperclock', n)
                if col is not None:
                    col.setAlphaF(max(0.0, min(1.0, nuit)))
                dessin.disque(p, pt.x(), pt.y(), r, col if col is not None else 'etoile',
                              'doux' if dessin.theme() == 'clair' else None, alpha=nuit)
                f = reelle('dipperclock', n)
                if f:
                    self.survolable(p, f['fiche'], pt.x(), pt.y(), max(5.0, r + 2), mag)
            if self.c_noms.isChecked():
                dessin.police(p, 0.85)
                for cle, etoile in ETIQUETTES.items():
                    if etoile in vis:
                        dessin.texte(p, vis[etoile].x() + 16, vis[etoile].y() - 12, tr('anim_dipperclock_' + cle),
                                     'texte', alpha=nuit)
                dessin.police(p, 1 / 0.85)
        self._horloge(p, QRectF(rect.right() - 96, rect.y() + 8, 88, 88))

    def _horloge(self, p, r):
        """Cadran de 24 heures (midi en haut, comme une horloge) et aiguille des heures."""
        cx, cy, rr = r.center().x(), r.center().y(), r.width() / 2 - 4
        p.setPen(dessin.stylo('grille', 1.2))
        p.setBrush(dessin.c('fond', 0.8))
        p.drawEllipse(QPointF(cx, cy), rr, rr)
        dessin.police(p, 0.7)
        for h in (0, 6, 12, 18):
            a = math.radians(90.0 - (h - 12) * 15.0)
            dessin.texte(p, cx + 0.72 * rr * math.cos(a), cy - 0.72 * rr * math.sin(a), str(h), 'doux')
        dessin.police(p, 1 / 0.7)
        a = math.radians(90.0 - (self.heure.value() - 12.0) * 15.0)
        p.setPen(dessin.stylo('accent3', 2.4))
        p.drawLine(QPointF(cx, cy), QPointF(cx + 0.55 * rr * math.cos(a), cy - 0.55 * rr * math.sin(a)))
