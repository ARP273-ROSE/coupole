"""Heliacal Rising Simulator : le jour où une étoile redevient visible à l'aube (lever héliaque) dépend de la
latitude et de la position de l'étoile.  Comme l'original, une étoile est « visible » si elle est au-dessus de
l'horizon pendant que le Soleil est à plus de 7° sous l'horizon (réglable) ; le lever héliaque est le premier matin
où elle est levée au début de l'aube.  Graphique de l'année : nuit, crépuscules, et heures où l'étoile est levée ;
Soleil de Meeus, étoile précessée à la date (positions J2000 de SIMBAD)."""
from __future__ import annotations

import functools
import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QImage, QPainter

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..base import MOIS_JOURS, Animation, angle, date_du_jour, heures_minutes, nombre

ANNEE = 2026
# α (heures) et δ (degrés) J2000, SIMBAD ; l'original proposait Véga et Sirius
ETOILES = (('sirius', 101.287_155 / 15, -16.716_116), ('vega', 279.234_735 / 15, 38.783_689),
           ('aldebaran', 68.980_163 / 15, 16.509_302), ('spica', 201.298_247 / 15, -11.161_319),
           ('antares', 247.351_915 / 15, -26.432_003), ('fomalhaut', 344.412_693 / 15, -29.622_237),
           ('arcturus', 213.915_300 / 15, 19.182_409))


def heure_solaire(h_soleil_deg: float, eqt_min: float) -> float:
    """Heure solaire moyenne locale (h) pour un angle horaire du Soleil vrai : T = 12 + H/15 − E/60."""
    return (12.0 + h_soleil_deg / 15.0 - eqt_min / 60.0) % 24.0


@functools.lru_cache(maxsize=16)
def annee(ra_h: float, dec: float, lat: float, depression: float) -> tuple:
    """Pour chaque jour : (aube, lever du Soleil, coucher, fin du crépuscule, passage de l'étoile, demi-arc diurne de
    l'étoile en heures), en heures solaires moyennes ; None quand l'événement n'a pas lieu."""
    out = []
    for j in range(365):
        jj = astro.jj_jour_de_l_annee(ANNEE, j + 0.5)
        s = astro.soleil(jj)
        ra, de = astro.precession(ra_h * 15.0, dec, jj)
        lig = []
        for h0 in (-depression, -0.833):
            hh = astro.angle_horaire_lever(s['delta'], lat, h0)
            lig.append(None if hh in (0.0, 180.0) else hh)
        aube, lever = (None if x is None else heure_solaire(-x, s['eqt']) for x in lig)
        coucher, fin = (None if x is None else heure_solaire(x, s['eqt']) for x in reversed(lig))
        passage = heure_solaire(astro.mod180(ra - s['alpha']), s['eqt'])
        demi = astro.angle_horaire_lever(de, lat, 0.0) / 15.0 * (1.0 / 1.002_737_909)   # heures solaires
        out.append((aube, lever, coucher, fin, passage, demi))
    return tuple(out)


@functools.lru_cache(maxsize=16)
def _heliaques(ra_h: float, dec: float, lat: float, depression: float) -> tuple:
    return tuple(astro.lever_heliaque(ra_h * 15.0, dec, lat, ANNEE, depression)[0])


class LeverHeliaque(Animation):
    ID = 'heliacalrisingsim'
    JOURS_PAR_S = 10.0

    def construire(self):
        self.vue3d = self.vue(150.0, 35.0, 7.0, 89.0)
        self.etoile = self.choix('etoile', [('anim_gravcalc_libre', '')] +
                                 [('anim_heliacalrisingsim_e_' + k, k) for k, _, _ in ETOILES], 'sirius')
        self.etoile.activated.connect(self._etoile)
        self.ra = self.curseur('ra', 0.0, 24.0, ETOILES[0][1], dec=2, unite='h', cle_texte='anim_c_ra')
        self.dec = self.curseur('dec', -90.0, 90.0, ETOILES[0][2], dec=1, unite='°', cle_texte='anim_c_dec')
        self.lat = self.curseur('latitude', -90.0, 90.0, 40.8, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.depression = self.curseur('depression', 0.0, 18.0, 7.0, dec=1, unite='°')
        self.jour = self.curseur('jour', 0.0, 364.0, 78.0, dec=0, cle_texte='anim_c_jour')
        self.heure = self.curseur('heure', 0.0, 24.0, 5.0, dec=2, unite='h', cle_texte='anim_c_heure')
        self.c_aube = self.coche('aube', True)
        self._graphe = None

    def _etoile(self, *_):
        for k, ra, dec in ETOILES:
            if k == self.etoile.currentData():
                self.ra.setValue(ra)
                self.dec.setValue(dec)

    def reglage_change(self):
        cle = next((k for k, ra, dec in ETOILES if abs(ra - self.ra.value()) < 0.006 and abs(dec - self.dec.value()) < 0.06),
                   '')
        if self.etoile.currentData() != cle:
            self.etoile.blockSignals(True)
            self.etoile.setCurrentIndex(max(0, self.etoile.findData(cle)))
            self.etoile.blockSignals(False)
        super().reglage_change()

    def _donnees(self):
        return annee(round(self.ra.value(), 4), round(self.dec.value(), 3), round(self.lat.value(), 2),
                     round(self.depression.value(), 2))

    def heure_effective(self) -> float:
        if self.c_aube.isChecked():
            aube = self._donnees()[int(self.jour.value()) % 365][0]
            if aube is not None:
                return aube
        return self.heure.value()

    def heliaques(self) -> list:
        return _heliaques(round(self.ra.value(), 4), round(self.dec.value(), 3), round(self.lat.value(), 2),
                          round(self.depression.value(), 2))

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def valeurs(self):
        j = int(self.jour.value()) % 365
        h = astro.visible_a_l_aube(self.ra.value() * 15.0, self.dec.value(), self.lat.value(), ANNEE, j,
                                   self.depression.value())
        dates = ', '.join(date_du_jour(x) for x in self.heliaques()) or tr('anim_heliacalrisingsim_jamais')
        aube = self._donnees()[j][0]
        return [(tr('anim_c_date'), date_du_jour(j)),
                (tr('anim_heliacalrisingsim_aube'), heures_minutes(aube) if aube is not None else '—'),
                (tr('anim_heliacalrisingsim_h_aube'), angle(h) if h is not None else '—'),
                (tr('anim_heliacalrisingsim_lever'), dates)]

    # ------------------------------------------------------------ souris : glisser dans le graphe
    def presser(self, pos, bouton):
        if self._graphe is not None and self._graphe[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return super().presser(pos, bouton)

    def _tirer(self, pos):
        _, x0, x1, y0, y1 = self._graphe
        self.jour.setValue(max(0.0, min(364.0, 365.0 * (pos.x() - x0) / (x1 - x0))))
        if not self.c_aube.isChecked():
            self.heure.setValue(max(0.0, min(24.0, 24.0 * (pos.y() - y0) / (y1 - y0))))

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.62) if rect.width() > rect.height() * 1.1 else dessin.zones(rect, 2, 10)
        self._annee(p, dessin.cadre(p, z[0], tr('anim_heliacalrisingsim_graphe')))
        self._ciel(p, dessin.cadre(p, z[1], tr('anim_heliacalrisingsim_ciel')))

    def _annee(self, p, r):
        x0, x1, y0, y1 = r.x() + 34, r.right() - 6, r.y() + 4, r.bottom() - 20
        self._graphe = (QRectF(r), x0, x1, y0, y1)
        w = (x1 - x0) / 365.0

        def y_de(h):
            return y0 + (y1 - y0) * h / 24.0

        cle = (self.ra.value(), self.dec.value(), self.lat.value(), self.depression.value(), int(x1 - x0),
               int(y1 - y0), dessin.theme())
        if getattr(self, '_fond', (None, None))[0] != cle:          # image du fond, refaite seulement si elle change
            self._fond = (cle, self._fond_annee(int(x1 - x0), int(y1 - y0)))
        p.drawImage(QPointF(x0, y0), self._fond[1])
        dessin.police(p, 0.75)
        for h in (0, 6, 12, 18, 24):
            p.setPen(dessin.stylo('grille', 1.0, 0.5))
            p.drawLine(QPointF(x0, y_de(h)), QPointF(x1, y_de(h)))
            dessin.texte(p, x0 - 16, y_de(h), '%d h' % h, 'doux')
        for mo in range(1, 13, 2):
            j = sum(MOIS_JOURS[:mo - 1])
            dessin.texte(p, x0 + (j + 15) * w, y1 + 11, tr('anim_mois_court_%d' % mo), 'doux')
        dessin.police(p, 1 / 0.75)
        for j in self.heliaques():
            p.setPen(dessin.stylo('accent1', 2.0))
            p.drawLine(QPointF(x0 + (j + 0.5) * w, y0), QPointF(x0 + (j + 0.5) * w, y1))
        jx = x0 + (self.jour.value() + 0.5) * w
        dessin.disque(p, jx, y_de(self.heure_effective()), 5, 'accent3', bord='texte')

    def _fond_annee(self, larg: int, haut: int) -> QImage:
        """Nuit noire, nuit polaire et heures où l'étoile est levée, jour par jour, dans une image."""
        img = QImage(max(1, larg), max(1, haut), QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(dessin.c('ciel', 0.55))
        q = QPainter(img)
        w = larg / 365.0

        def y_de(h):
            return haut * h / 24.0

        for j, (aube, lever, coucher, fin, passage, demi) in enumerate(self._donnees()):
            x = round(j * w)
            w_j = max(1, round((j + 1) * w) - x)                    # colonnes jointives, sans recouvrement
            if aube is not None and fin is not None:              # nuit noire : de la fin du crépuscule à l'aube
                for a, b in ((0.0, aube), (fin, 24.0)) if fin > aube else ((fin, aube),):
                    q.fillRect(QRectF(x, y_de(a), w_j, y_de(b) - y_de(a)), dessin.c('nuit'))
            elif aube is None and lever is None:                   # nuit polaire
                q.fillRect(QRectF(x, 0, w_j, haut), dessin.c('nuit'))
            if demi > 0:                                           # étoile levée : passage ± demi-arc
                d0, d1 = passage - demi, passage + demi
                for a, b in ((d0, d1), (d0 + 24, d1 + 24), (d0 - 24, d1 - 24)):
                    a, b = max(0.0, a), min(24.0, b)
                    if b > a:
                        q.fillRect(QRectF(x, y_de(a), w_j, y_de(b) - y_de(a)), dessin.c('accent2', 0.35))
        q.end()
        return img

    def _ciel(self, p, r):
        self.zone_rotative(r, self.vue3d)
        lat = self.lat.value()
        j = self.jour.value()
        h = self.heure_effective()
        jj = astro.jj_jour_de_l_annee(ANNEE, j + h / 24.0)
        tsl = astro.tsmg(jj)
        s = astro.soleil(jj)
        ra, de = astro.precession(self.ra.value() * 15.0, self.dec.value(), jj)
        m = np.array(astro.matrice_equatorial_vers_horizon(tsl, lat))
        soleil = m @ np.array(astro.vecteur_equatorial(s['alpha'], s['delta']))
        etoile = m @ np.array(astro.vecteur_equatorial(ra, de))
        _, h_sol = astro.equatorial_vers_horizon(tsl - s['alpha'], s['delta'], lat)

        def scene(pe):
            pe.courbe(scenes.cercle_declinaison(de) @ m.T, 'accent2', 1.0, 0.7)
            pe.courbe(dessin.cercle((0, 0, 1)) @ m.T, 'equateur', 1.2, 0.8)
            pe.point(soleil, 'soleil', 8.0, repere_monde=True)
            pe.point(etoile, 'etoile', 5.0, bord='accent2', repere_monde=True)

        couleur = 'ciel' if h_sol > 0 else ('nuit' if h_sol < -self.depression.value() else 'grille')
        rr = min(r.width(), r.height()) * 0.40
        scenes.sphere_locale(p, self.vue3d, r.center().x(), r.center().y() + 6, rr, scene, couleur_ciel=couleur)
        dessin.texte(p, r.center().x(), r.bottom() - 10, '%s, %s' % (date_du_jour(j), heures_minutes(h)), 'doux')
