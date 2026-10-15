"""Sun's Position on Horizon : l'horizon est (ou ouest) vu par l'observateur ; le point de lever (ou de coucher) du
Soleil glisse le long de l'horizon au fil de l'année, entre ses positions extrêmes des solstices ; aux équinoxes il
est plein est (ouest).  La trajectoire du Soleil coupe l'horizon sous l'angle 90° − |φ|."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..maintenant import heure_solaire
from ..base import Animation, angle, date_du_jour

ANNEE = 2026
EPS = astro.obliquite_moyenne(astro.jj_jour_de_l_annee(ANNEE, 0))


class LeverHorizon(Animation):
    ID = 'horizon'
    JOURS_PAR_S = 20.0

    TEMPS = ('jour',)
    HEURE_SOLAIRE = True

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        j, h = heure_solaire(m.i, m.lon)
        self.poser(self.jour, j)
        if m.lat is not None:
            self.poser(self.lat, m.lat)

    def construire(self):
        self.cote = self.choix('cote', [('anim_horizon_est', 'est'), ('anim_horizon_ouest', 'ouest')], 'est')
        self.lat = self.curseur('latitude', -66.0, 66.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.jour = self.curseur('jour', 0.0, 364.0, 79.0, dec=0, cle_texte='anim_c_jour')
        self.c_trace = self.coche('trace', True)

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def _azimut(self, d: float):
        az = astro.azimut_lever(d, self.lat.value())
        if az is None:
            return None
        return az if self.cote.currentData() == 'est' else 360.0 - az

    def valeurs(self):
        d = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['delta']
        az = self._azimut(d)
        a_n, a_s = self._azimut(EPS), self._azimut(-EPS)
        out = [(tr('anim_c_date'), date_du_jour(self.jour.value())), (tr('anim_c_dec'), angle(d)),
               (tr('anim_horizon_azimut'), angle(az) if az is not None else '—')]
        if a_n is not None and a_s is not None:
            out.append((tr('anim_horizon_amplitude'), angle(abs(a_s - a_n))))
        return out

    def dessiner(self, p, rect):
        lat = self.lat.value()
        est = self.cote.currentData() == 'est'
        centre_az = 90.0 if est else 270.0
        larg_deg = 100.0
        sol = rect.bottom() - rect.height() * 0.3

        def x_de(az):
            dx = (az - centre_az) / larg_deg
            return rect.center().x() + (dx if est else dx) * rect.width()

        def y_de(h):
            return sol - h / 45.0 * (sol - rect.y())

        p.fillRect(QRectF(rect.x(), rect.y(), rect.width(), sol - rect.y()), dessin.c('ciel', 0.35))
        p.fillRect(QRectF(rect.x(), sol, rect.width(), rect.bottom() - sol), dessin.c('sol', 0.6))
        p.setPen(dessin.stylo('horizon', 2.0))
        p.drawLine(QPointF(rect.x(), sol), QPointF(rect.right(), sol))
        dessin.police(p, 0.9)
        for az, cle in ((0, 'anim_pc_n'), (45, 'NE'), (90, 'anim_pc_e'), (135, 'SE'), (180, 'anim_pc_s'),
                        (225, 'SW'), (270, 'anim_pc_o'), (315, 'NW'), (360, 'anim_pc_n')):
            x = x_de(az)
            if rect.x() <= x <= rect.right():
                lab = tr(cle) if cle.startswith('anim_') else tr('anim_horizon_' + cle.lower())
                dessin.texte(p, x, sol + 16, lab, 'horizon')
                p.setPen(dessin.stylo('horizon', 1.0, 0.6))
                p.drawLine(QPointF(x, sol), QPointF(x, sol + 5))
        dessin.police(p, 1 / 0.9)
        if self.c_trace.isChecked():
            for cle, dd, coul in (('solstice_juin', EPS, 'accent3'), ('equinoxes', 0.0, 'accent1'),
                                  ('solstice_dec', -EPS, 'accent2')):
                az = self._azimut(dd)
                if az is None:
                    continue
                x = x_de(az)
                p.setPen(dessin.stylo(coul, 1.5, 0.8, pointille=True))
                p.drawLine(QPointF(x, sol), QPointF(x, rect.y() + 20))
                dessin.texte(p, x, rect.y() + 12, tr('anim_sunpaths_' + cle), coul, fond=True)
        d = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['delta']
        az = self._azimut(d)
        if az is not None:
            # portion de la course du Soleil près de l'horizon (montante à l'est, descendante à l'ouest)
            pts = []
            h0 = astro.angle_horaire_lever(d, lat)
            for k in range(0, 41):
                hh = (-h0 + k * 1.5) if est else (h0 - k * 1.5)
                a2, alt = astro.equatorial_vers_horizon(hh, d, lat)
                pts.append(QPointF(x_de(a2), y_de(alt)))
            p.setPen(dessin.stylo('soleil', 2.0, 0.8))
            for a, b in zip(pts[:-1], pts[1:]):
                p.drawLine(a, b)
            dessin.disque(p, x_de(az), sol, 10, 'soleil')
            dessin.texte(p, x_de(az), sol - 24, angle(az), 'soleil', fond=True)
        dessin.police(p, 1.1, gras=True)
        dessin.texte(p, rect.x() + 12, rect.y() + 40, date_du_jour(self.jour.value()), centre=False)
        dessin.police(p, 1 / 1.1)
