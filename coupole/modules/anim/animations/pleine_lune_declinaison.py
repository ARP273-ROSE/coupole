"""Full Moon Declination Simulator : la pleine lune est à l'opposé du Soleil, donc près du point de l'écliptique
opposé au Soleil, à ±5,1° près (inclinaison de l'orbite lunaire).  Sa déclinaison suit à l'envers celle du Soleil :
la pleine lune d'hiver monte haut dans le ciel de minuit, celle d'été reste basse.  Courbe annuelle de la
déclinaison de la pleine lune (bande des latitudes écliptiques ±5,145°) et sphère locale à minuit vrai."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..maintenant import heure_solaire
from ..base import MOIS_JOURS, Animation, angle, date_du_jour

ANNEE = 2026


def pleine_lune(jour: float, lat: float) -> dict:
    """Pour le jour de l'année : Soleil (Meeus), point antisolaire, déclinaisons extrêmes d'une pleine lune
    (latitude écliptique ±i) et hauteurs correspondantes au passage au méridien (minuit vrai)."""
    s = astro.soleil_jour(ANNEE, jour)
    eps = astro.obliquite_moyenne(astro.jj_jour_de_l_annee(ANNEE, jour))
    lam = (s['lambda'] + 180.0) % 360.0
    _, d0 = astro.ecliptique_vers_equatorial(lam, 0.0, eps)
    ds = [astro.ecliptique_vers_equatorial(lam, b, eps)[1] for b in (-astro.INCLINAISON_LUNE, astro.INCLINAISON_LUNE)]
    dmin, dmax = min(ds), max(ds)
    return {'soleil': s, 'eps': eps, 'lambda': lam, 'dec': d0, 'dec_min': dmin, 'dec_max': dmax,
            'h': astro.hauteur_culmination(d0, lat), 'h_min': astro.hauteur_culmination(dmin, lat),
            'h_max': astro.hauteur_culmination(dmax, lat)}


class PleineLuneDeclinaison(Animation):
    ID = 'fullmoondec'
    JOURS_PAR_S = 12.0

    TEMPS = ('jour',)
    HEURE_SOLAIRE = True

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        j, h = heure_solaire(m.i, m.lon)
        self.poser(self.jour, j)
        if m.lat is not None:
            self.poser(self.lat, m.lat)

    def construire(self):
        self.vue3d = self.vue(200.0, 20.0, 7.0, 89.0)
        self.jour = self.curseur('jour', 0.0, 364.0, 45.0, dec=0, unite='', cle_texte='anim_c_jour')
        self.lat = self.curseur('latitude', -90.0, 90.0, 40.8, dec=1, unite='°', cle_texte='anim_c_latitude')
        self._graphe = None
        self._courbe = None

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def valeurs(self):
        f = pleine_lune(self.jour.value(), self.lat.value())
        return [(tr('anim_c_date'), date_du_jour(self.jour.value())),
                (tr('anim_fullmoondec_dec_soleil'), angle(f['soleil']['delta'])),
                (tr('anim_fullmoondec_dec_lune'), '%s … %s' % (angle(f['dec_min']), angle(f['dec_max']))),
                (tr('anim_fullmoondec_hauteur'), '%s … %s' % (angle(f['h_min']), angle(f['h_max'])))]

    # ------------------------------------------------------------ souris : glisser le curseur du jour
    def presser(self, pos, bouton):
        if self._graphe is not None and self._graphe[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return super().presser(pos, bouton)

    def _tirer(self, pos):
        _, x0, x1 = self._graphe
        self.jour.setValue(max(0.0, min(364.0, 365.0 * (pos.x() - x0) / (x1 - x0))))

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.8)
        self._ciel(p, dessin.cadre(p, z[0], tr('anim_fullmoondec_ciel')))
        self._trace(p, dessin.cadre(p, z[1], tr('anim_fullmoondec_graphe')))

    def _ciel(self, p, r):
        self.zone_rotative(r, self.vue3d)
        f = pleine_lune(self.jour.value(), self.lat.value())
        lat = self.lat.value()
        tsl = (f['soleil']['alpha'] + 180.0) % 360.0                        # minuit vrai : Soleil à H = 180°
        m = np.array(astro.matrice_equatorial_vers_horizon(tsl, lat))
        eps = f['eps']
        c, s_ = math.cos(math.radians(eps)), math.sin(math.radians(eps))
        rot = np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])               # écliptique → équatorial
        bandes = [(dessin.cercle((0, 0, 1), 90.0 - b, 181) @ rot.T) @ m.T
                  for b in (-astro.INCLINAISON_LUNE, astro.INCLINAISON_LUNE)]
        soleil = m @ np.array(astro.vecteur_equatorial(f['soleil']['alpha'], f['soleil']['delta']))
        ra_l, _ = astro.ecliptique_vers_equatorial(f['lambda'], 0.0, eps)
        lune = m @ np.array(astro.vecteur_equatorial(ra_l, f['dec']))

        def scene(pe):
            pe.courbe(dessin.cercle((0, 0, 1)) @ m.T, 'equateur', 1.3, 0.8)
            pe.courbe(scenes.ecliptique(eps) @ m.T, 'ecliptique', 1.3, 0.8)
            for b in bandes:
                pe.courbe(b, 'accent3', 1.0, 0.7)
            pe.point(soleil, 'soleil', 8.0, repere_monde=True)
            pe.point(lune, 'lune', 8.0, bord='doux', repere_monde=True)

        rr = min(r.width(), r.height()) * 0.42
        scenes.sphere_locale(p, self.vue3d, r.center().x(), r.center().y() + 6, rr, scene, couleur_ciel='nuit')

    def _trace(self, p, r):
        x0, x1 = r.x() + 34, r.right() - 6
        y0, y1 = r.y() + 6, r.bottom() - 22
        self._graphe = (QRectF(r), x0, x1)
        dmax = 35.0

        def xy(j, d):
            return QPointF(x0 + (x1 - x0) * j / 365.0, (y0 + y1) / 2 - (y1 - y0) / 2 * d / dmax)

        if self._courbe is None:                                     # 73 points, calculés une fois
            self._courbe = [(j, pleine_lune(j, 0.0)) for j in np.linspace(0.0, 365.0, 74)]
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('accent3', 0.22))
        p.drawPolygon(QPolygonF([xy(j, f['dec_max']) for j, f in self._courbe]
                                + [xy(j, f['dec_min']) for j, f in reversed(self._courbe)]))
        p.setPen(dessin.stylo('grille', 1.0))
        for d in (-30, -15, 0, 15, 30):
            q = xy(0, d)
            p.drawLine(QPointF(x0, q.y()), QPointF(x1, q.y()))
            dessin.police(p, 0.75)
            dessin.texte(p, x0 - 16, q.y(), '%+d°' % d if d else '0°', 'doux')
            dessin.police(p, 1 / 0.75)
        p.setPen(dessin.stylo('lune', 1.6))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF([xy(j, f['dec']) for j, f in self._courbe]))
        p.setPen(dessin.stylo('soleil', 1.2, 0.6, pointille=True))
        p.drawPolyline(QPolygonF([xy(j, f['soleil']['delta']) for j, f in self._courbe]))
        dessin.police(p, 0.75)
        for mo in range(1, 13, 2):
            j = sum(MOIS_JOURS[:mo - 1])
            dessin.texte(p, xy(j + 14, 0).x(), y1 + 12, tr('anim_mois_court_%d' % mo), 'doux')
        dessin.police(p, 1 / 0.75)
        j = self.jour.value()
        f = pleine_lune(j, self.lat.value())
        p.setPen(dessin.stylo('accent1', 1.6))
        p.drawLine(QPointF(xy(j, 0).x(), y0), QPointF(xy(j, 0).x(), y1))
        dessin.disque(p, xy(j, f['dec']).x(), xy(j, f['dec']).y(), 4.5, 'lune', bord='texte')

