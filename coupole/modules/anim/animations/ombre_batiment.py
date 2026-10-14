"""Union Seasons Demonstrator : l'original montrait un film accéléré de l'ombre d'un bâtiment d'université, photographié
à la même heure pendant un an.  Coupole le remplace par une simulation : un bâtiment (pavé) et son ombre portée sur
le sol, à la latitude et à l'heure choisies, jour après jour.  La hauteur du Soleil au midi vrai vaut
90° − φ + δ : l'ombre de midi raccourcit jusqu'au solstice d'été et s'allonge jusqu'à celui d'hiver.  Soleil de
Meeus (déclinaison, équation du temps) ; ombre = projection des arêtes du toit le long des rayons du Soleil."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import MOIS_JOURS, Animation, angle, date_du_jour, heures_minutes, nombre

ANNEE = 2026
LARGEUR, PROFONDEUR = 1.6, 1.0           # emprise du bâtiment (unités : sa hauteur = 1), grand côté est-ouest


def soleil_local(jour: float, heure: float, lat: float, midi_vrai: bool) -> dict:
    """Azimut et hauteur du Soleil le jour donné, à l'heure solaire moyenne `heure` (ou au midi vrai)."""
    s = astro.soleil_jour(ANNEE, jour + 0.5)
    if midi_vrai:
        heure = 12.0 - s['eqt'] / 60.0
    h_angle = 15.0 * (heure - 12.0) + s['eqt'] / 4.0          # angle horaire du Soleil vrai, degrés
    az, alt = astro.equatorial_vers_horizon(h_angle, s['delta'], lat)
    return {'az': az, 'alt': alt, 'dec': s['delta'], 'eqt': s['eqt'], 'heure': heure}


def ombre(az: float, alt: float, hauteur: float = 1.0) -> np.ndarray | None:
    """Polygone (repère local : x vers l'est, y vers le nord) de l'ombre du pavé, ou None si le Soleil est couché.
    Chaque coin du toit (hauteur h) se projette au sol à h / tan(hauteur) dans la direction opposée au Soleil."""
    if alt <= 0.2:
        return None
    lg = hauteur / math.tan(math.radians(alt))
    dx, dy = -lg * math.sin(math.radians(az)), -lg * math.cos(math.radians(az))
    coins = [(-LARGEUR / 2, -PROFONDEUR / 2), (LARGEUR / 2, -PROFONDEUR / 2), (LARGEUR / 2, PROFONDEUR / 2),
             (-LARGEUR / 2, PROFONDEUR / 2)]
    pts = np.array(coins + [(x + dx, y + dy) for x, y in coins])
    return enveloppe(pts)


def enveloppe(pts: np.ndarray) -> np.ndarray:
    """Enveloppe convexe (algorithme de la chaîne monotone)."""
    p = sorted(map(tuple, pts))

    def croix(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    bas, haut = [], []
    for q in p:
        while len(bas) >= 2 and croix(bas[-2], bas[-1], q) <= 0:
            bas.pop()
        bas.append(q)
    for q in reversed(p):
        while len(haut) >= 2 and croix(haut[-2], haut[-1], q) <= 0:
            haut.pop()
        haut.append(q)
    return np.array(bas[:-1] + haut[:-1])


class OmbreBatiment(Animation):
    ID = 'transitmovie'
    JOURS_PAR_S = 8.0

    def construire(self):
        self.vue3d = self.vue(160.0, 35.0, 5.0, 89.0)
        self.jour = self.curseur('jour', 0.0, 364.0, 282.0, dec=0, cle_texte='anim_c_jour')
        self.heure = self.curseur('heure', 6.0, 18.0, 13.0, dec=2, unite='h', cle_texte='anim_c_heure')
        self.lat = self.curseur('latitude', -66.0, 66.0, 40.8, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.c_midi = self.coche('midi', False)
        self.c_trace = self.coche('trace', True)
        self._courbe = None

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def _soleil(self, jour=None):
        return soleil_local(self.jour.value() if jour is None else jour, self.heure.value(), self.lat.value(),
                            self.c_midi.isChecked())

    def valeurs(self):
        s = self._soleil()
        out = [(tr('anim_c_date'), date_du_jour(self.jour.value())), (tr('anim_c_heure'), heures_minutes(s['heure'])),
               (tr('anim_transitmovie_dec'), angle(s['dec'])), (tr('anim_c_hauteur'), angle(s['alt'])),
               (tr('anim_c_azimut'), angle(s['az']))]
        if s['alt'] > 0.2:
            out.append((tr('anim_transitmovie_longueur'), nombre(1.0 / math.tan(math.radians(s['alt'])), 2)))
        return out

    def dessiner(self, p, rect):
        haut = rect.height() * 0.74
        r = dessin.cadre(p, QRectF(rect.x(), rect.y(), rect.width(), haut), tr('anim_transitmovie_scene'))
        p.save()
        p.setClipRect(r.adjusted(-5, -5, 5, 5))           # le sol ne déborde pas du panneau
        self._scene(p, r)
        p.restore()
        self._annee(p, dessin.cadre(p, QRectF(rect.x(), rect.y() + haut, rect.width(), rect.height() - haut),
                                    tr('anim_transitmovie_graphe')))

    def _scene(self, p, r):
        self.zone_rotative(r, self.vue3d)
        v = self.vue3d
        cx, cy = r.center().x(), r.center().y() + r.height() * 0.08
        k = min(r.width(), r.height()) * 0.17
        s = self._soleil()

        def ecran(pts):
            # repère du dessin : x nord, y ouest, z zénith (comme les sphères locales) ; données en (est, nord, z)
            a = np.asarray(pts, dtype=float).reshape(-1, 3)
            monde = np.stack([a[:, 1], -a[:, 0], a[:, 2]], axis=1)
            x, y, d = v.projeter(monde)
            return [QPointF(cx + k * u, cy - k * w) for u, w in zip(x, y)], d

        sol = [(-3.2, -3.2, 0), (3.2, -3.2, 0), (3.2, 3.2, 0), (-3.2, 3.2, 0)]
        pts, _ = ecran(sol)
        p.setPen(dessin.stylo('horizon', 1.0))
        p.setBrush(dessin.c('sol', 0.75))
        p.drawPolygon(QPolygonF(pts))
        for lab, pos in (('anim_pc_n', (0, 3.6, 0)), ('anim_pc_s', (0, -3.6, 0)), ('anim_pc_e', (3.6, 0, 0)),
                         ('anim_pc_o', (-3.6, 0, 0))):
            q, _ = ecran([pos])
            dessin.texte(p, q[0].x(), q[0].y(), tr(lab), 'horizon')
        if self.c_trace.isChecked():                      # bout de l'ombre du coin nord-est du toit, toute la journée
            pts = []
            for h in np.linspace(4.0, 20.0, 97):
                ss = soleil_local(self.jour.value(), h, self.lat.value(), False)
                if ss['alt'] > 3.0:
                    lg = 1.0 / math.tan(math.radians(ss['alt']))
                    x = LARGEUR / 2 - lg * math.sin(math.radians(ss['az']))
                    y = PROFONDEUR / 2 - lg * math.cos(math.radians(ss['az']))
                    if abs(x) < 3.2 and abs(y) < 3.2:
                        pts.append((x, y, 0.0))
            if len(pts) > 1:
                q, _ = ecran(pts)
                p.setPen(dessin.stylo('accent1', 1.2, 0.7, pointille=True))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawPolyline(QPolygonF(q))
        poly = ombre(s['az'], s['alt'])
        if poly is not None:
            q, _ = ecran([(x, y, 0.0) for x, y in poly])
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c('ombre', 0.45))
            p.drawPolygon(QPolygonF(q))
        # le pavé : faces triées de la plus lointaine à la plus proche
        lx, ly = LARGEUR / 2, PROFONDEUR / 2
        b = [(-lx, -ly), (lx, -ly), (lx, ly), (-lx, ly)]
        faces = [[(*b[i], 0), (*b[(i + 1) % 4], 0), (*b[(i + 1) % 4], 1), (*b[i], 1)] for i in range(4)]
        faces.append([(*c, 1) for c in b])
        soleil_vec = np.array([math.sin(math.radians(s['az'])) * math.cos(math.radians(s['alt'])),
                               math.cos(math.radians(s['az'])) * math.cos(math.radians(s['alt'])),
                               math.sin(math.radians(s['alt']))])
        triees = []
        for f in faces:
            q, d = ecran(f)
            a = np.array(f, dtype=float)
            n = np.cross(a[1] - a[0], a[2] - a[0])
            n = n / np.linalg.norm(n)
            if float(np.mean(a, axis=0) @ n) < 0:
                n = -n
            eclairee = s['alt'] > 0 and float(n @ soleil_vec) > 0
            triees.append((float(np.mean(d)), q, eclairee))
        for _, q, eclairee in sorted(triees, key=lambda t: t[0]):
            p.setPen(dessin.stylo('grille', 1.0))
            p.setBrush(dessin.c('lune' if eclairee else 'penombre', 0.95 if eclairee else 0.7))
            p.drawPolygon(QPolygonF(q))
        if s['alt'] > 0:
            q, _ = ecran([tuple(2.9 * soleil_vec)])
            dessin.disque(p, q[0].x(), q[0].y(), 9, 'soleil')

    def _annee(self, p, r):
        """Hauteur du Soleil à cette heure (ou au midi vrai) tout au long de l'année."""
        x0, x1, y0, y1 = r.x() + 30, r.right() - 6, r.y() + 4, r.bottom() - 14
        cle = (self.heure.value(), self.lat.value(), self.c_midi.isChecked())
        if self._courbe is None or self._courbe[0] != cle:
            self._courbe = (cle, [soleil_local(j, self.heure.value(), self.lat.value(), self.c_midi.isChecked())['alt']
                                  for j in range(0, 366, 3)])
        hs = self._courbe[1]
        hmin, hmax = min(-5.0, min(hs)), max(90.0, max(hs))

        def xy(j, h):
            return QPointF(x0 + (x1 - x0) * j / 365.0, y1 - (y1 - y0) * (h - hmin) / (hmax - hmin))

        p.setPen(dessin.stylo('grille', 1.0, 0.6))
        dessin.police(p, 0.7)
        for h in (0, 30, 60, 90):
            q = xy(0, h)
            p.drawLine(QPointF(x0, q.y()), QPointF(x1, q.y()))
            dessin.texte(p, x0 - 14, q.y(), '%d°' % h, 'doux')
        for mo in range(1, 13, 2):
            dessin.texte(p, xy(sum(MOIS_JOURS[:mo - 1]) + 15, 0).x(), y1 + 8, tr('anim_mois_court_%d' % mo), 'doux')
        dessin.police(p, 1 / 0.7)
        p.setPen(dessin.stylo('soleil', 1.6))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF([xy(3 * i, h) for i, h in enumerate(hs)]))
        s = self._soleil()
        dessin.disque(p, xy(self.jour.value(), s['alt']).x(), xy(self.jour.value(), s['alt']).y(), 4.5, 'accent3',
                      bord='texte')
