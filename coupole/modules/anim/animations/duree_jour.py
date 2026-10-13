"""Daylight Hours Explorer : durée du jour au fil de l'année pour une latitude.  À gauche, la Terre éclairée et
le parallèle de l'observateur partagé en arc de jour et arc de nuit ; à droite, la courbe de la durée du jour avec
un point à faire glisser.  Comme l'original : horizon géométrique, cos H₀ = −tan φ tan δ ; en option, le lever au
bord supérieur du Soleil avec la réfraction (h₀ = −0,833°)."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, date_du_jour, duree_hm, nombre

ANNEE = 2026
JOURS_MOIS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def courbe_duree(lat: float, h0: float = 0.0, pas: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Jours (0 → 364) et durée du jour (heures) à midi de chaque jour."""
    jours = np.arange(0.0, 365.0, pas)
    durees = np.array([astro.duree_du_jour_h(astro.soleil_jour(ANNEE, j + 0.5)['delta'], lat, h0) for j in jours])
    return jours, durees


class DureeJour(Animation):
    ID = 'daylighthoursexplorer'
    JOURS_PAR_S = 30.0

    def construire(self):
        self.globe = self.vue(60.0, 15.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.jour = self.curseur('jour', 0.0, 364.0, 120.0, dec=0, cle_texte='anim_c_jour')
        self.c_moyenne = self.coche('moyenne', False)
        self.c_curseur = self.coche('point', True)
        self.c_refraction = self.coche('refraction', False)
        self._cache = None
        self._trace = None

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def _h0(self) -> float:
        return -0.833 if self.c_refraction.isChecked() else 0.0

    def _courbe(self):
        cle = (round(self.lat.value(), 3), self._h0())
        if self._cache is None or self._cache[0] != cle:
            self._cache = (cle, courbe_duree(self.lat.value(), self._h0()))
        return self._cache[1]

    def valeurs(self):
        d = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['delta']
        h = astro.duree_du_jour_h(d, self.lat.value(), self._h0())
        _, durees = self._courbe()
        return [(tr('anim_c_date'), date_du_jour(self.jour.value())), (tr('anim_c_dec'), angle(d)),
                (tr('anim_sunmotions_duree'), duree_hm(h)),
                (tr('anim_daylighthoursexplorer_moyenne'), duree_hm(float(durees.mean()))),
                (tr('anim_daylighthoursexplorer_extremes'), '%s / %s' % (duree_hm(float(durees.min())),
                                                                         duree_hm(float(durees.max()))))]

    def presser(self, pos, bouton):
        if self._trace is not None and self._trace.contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return super().presser(pos, bouton)

    def _tirer(self, pos):
        r = self._trace
        self.jour.setValue(max(0.0, min(364.0, (pos.x() - r.x()) / r.width() * 365.0)))

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.75)
        self._globe(p, dessin.cadre(p, z[0], tr('anim_daylighthoursexplorer_vue_globe')))
        self._graphe(p, dessin.cadre(p, z[1], tr('anim_daylighthoursexplorer_vue_courbe')))

    def _globe(self, p, r):
        """Repère équatorial ; le Soleil dans la direction α = 0 (méridien de midi face à l'écran ou presque)."""
        self.zone_rotative(r, self.globe)
        rr = min(r.width(), r.height()) * 0.38
        cx, cy = r.center().x(), r.center().y()
        pe = dessin.Peintre3D(p, self.globe, cx, cy, rr)
        d = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['delta']
        soleil = np.array(astro.vecteur_equatorial(0.0, d))
        pe.contour('grille', 'terre', 0.55)
        dessin.hemisphere_nuit(pe, soleil)
        pe.courbe(dessin.cercle((0, 0, 1)), 'equateur', 1.2, 0.8, arriere='cache')
        lat = max(-89.5, min(89.5, self.lat.value()))
        h0 = astro.angle_horaire_lever(d, lat, self._h0())
        # parallèle de l'observateur : arc de jour (|H| < H₀) en jaune, de nuit en gris
        hs = np.linspace(-180, 180, 241)
        pts3 = np.array([astro.vecteur_equatorial(-h, lat) for h in hs])
        jour = np.abs(hs) <= h0
        for masque, coul, ep in ((jour, 'soleil', 3.0), (~jour, 'doux', 1.5)):
            idx = np.flatnonzero(masque)
            if len(idx) > 1:
                groupes = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
                for g in groupes:
                    pe.courbe(pts3[g], coul, ep, arriere='pale')
        pe.segment((0, 0, 1), (0, 0, 1.18), 'texte', 2.0)
        pe.segment((0, 0, -1), (0, 0, -1.18), 'texte', 2.0)
        pe.etiquette(soleil * 1.25, tr('anim_marsorbit_soleil'), 'soleil')

    def _graphe(self, p, r):
        jours, durees = self._courbe()
        g = r.adjusted(44, 10, -10, -30)
        self._trace = QRectF(g)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.c('sphere', 0.2))
        p.drawRect(g)

        def xy(j, h):
            return QPointF(g.x() + j / 365.0 * g.width(), g.bottom() - h / 24.0 * g.height())
        dessin.police(p, 0.8)
        for h in range(0, 25, 6):
            q = xy(0, h)
            p.setPen(dessin.stylo('grille', 0.8, 0.6))
            p.drawLine(q, xy(365, h))
            dessin.texte(p, g.x() - 20, q.y(), '%d h' % h, 'doux')
        for m, j in enumerate(JOURS_MOIS):
            q = xy(j, 0)
            p.setPen(dessin.stylo('grille', 0.6, 0.4))
            p.drawLine(q, xy(j, 24))
            dessin.texte(p, xy(j + 15, 0).x(), g.bottom() + 12, tr('anim_mois_court_%d' % (m + 1)), 'doux')
        dessin.police(p, 1 / 0.8)
        p.setPen(dessin.stylo('soleil', 2.2))
        p.drawPolyline(QPolygonF([xy(j, h) for j, h in zip(jours, durees)]))
        if self.c_moyenne.isChecked():
            m = float(durees.mean())
            p.setPen(dessin.stylo('accent2', 1.5, pointille=True))
            p.drawLine(xy(0, m), xy(365, m))
            dessin.texte(p, g.right() - 60, xy(0, m).y() - 10, duree_hm(m), 'accent2', fond=True)
        if self.c_curseur.isChecked():
            j = self.jour.value()
            h = astro.duree_du_jour_h(astro.soleil_jour(ANNEE, j + 0.5)['delta'], self.lat.value(), self._h0())
            q = xy(j, h)
            p.setPen(dessin.stylo('accent3', 1.0, 0.7, pointille=True))
            p.drawLine(QPointF(q.x(), g.bottom()), q)
            dessin.disque(p, q.x(), q.y(), 6, 'accent3', bord='fond')
            dessin.texte(p, q.x(), q.y() - 16, nombre(h, 1) + ' h', 'accent3', fond=True)
