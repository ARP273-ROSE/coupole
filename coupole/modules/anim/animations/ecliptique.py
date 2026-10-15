"""Ecliptic Simulator : carte du ciel (ascension droite, déclinaison) avec l'équateur céleste et l'écliptique,
tan δ = tan ε sin α ; le Soleil la parcourt au fil de l'année, entre une date de début et une date de fin.  Vue
depuis l'intérieur de la sphère (le ciel tel qu'on le voit : α croît vers la gauche, l'est) ou depuis
l'extérieur."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..maintenant import heure_solaire
from ..base import Animation, angle, date_du_jour, heures_minutes, jour_de_date

ANNEE = 2026


def dec_ecliptique(ra_deg: float, eps: float) -> float:
    """Déclinaison du point de l'écliptique d'ascension droite α : tan δ = tan ε sin α."""
    return math.degrees(math.atan(math.tan(math.radians(eps)) * math.sin(math.radians(ra_deg))))


class Ecliptique(Animation):
    ID = 'seasonsim'
    JOURS_PAR_S = 30.0

    TEMPS = ('jour',)
    HEURE_SOLAIRE = True

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        j, h = heure_solaire(m.i, m.lon)
        self.poser(self.jour, j)

    def construire(self):
        self.jour = self.curseur('jour', 0.0, 364.0, 79.0, dec=0, cle_texte='anim_c_jour')
        mois = [('anim_mois_%d' % m, m) for m in range(1, 13)]
        self.m_debut = self.choix('mois_debut', mois, 3)
        self.j_debut = self.curseur('jour_debut', 1, 31, 21, dec=0)
        self.m_fin = self.choix('mois_fin', mois, 3)
        self.j_fin = self.curseur('jour_fin', 1, 31, 20, dec=0)
        self.cote = self.choix('cote', [('anim_seasonsim_dedans', 'dedans'), ('anim_seasonsim_dehors', 'dehors')],
                               'dedans')
        self.bouton('anim_seasonsim_aller_debut', self.aller_debut)

    def _debut(self):
        return jour_de_date(self.m_debut.currentData(), min(int(self.j_debut.value()), 28 if
                                                            self.m_debut.currentData() == 2 else 31))

    def _fin(self):
        return jour_de_date(self.m_fin.currentData(), min(int(self.j_fin.value()), 28 if
                                                          self.m_fin.currentData() == 2 else 31))

    def aller_debut(self):
        self.jour.setValue(self._debut())

    def basculer_lecture(self):
        if not self.en_lecture and abs(self.jour.value() - self._fin()) < 0.5:
            self.aller_debut()                       # arrivé à la fin : on repart du début
        super().basculer_lecture()

    def avancer(self, dt):
        """Le Soleil avance jusqu'à la date de fin, puis l'animation s'arrête (comme l'original)."""
        j, fin = self.jour.value(), self._fin()
        reste = (fin - j) % 365.0
        pas = dt * self.JOURS_PAR_S
        if pas >= reste:
            self.jour.setValue(fin)
            self.basculer_lecture()
            return
        self.jour.setValue((j + pas) % 365.0)

    def valeurs(self):
        s = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)
        return [(tr('anim_c_date'), date_du_jour(self.jour.value())), (tr('anim_c_ra'), heures_minutes(s['alpha'] / 15)),
                (tr('anim_c_dec'), angle(s['delta'])), (tr('anim_seasonsim_lambda'), angle(s['lambda']))]

    def dessiner(self, p, rect):
        eps = astro.obliquite_moyenne(astro.jj_jour_de_l_annee(ANNEE, 0))
        r = rect.adjusted(52, 30, -18, -40)
        dedans = self.cote.currentData() == 'dedans'

        def x_de(ra_deg):
            t = (ra_deg % 360.0) / 360.0
            return r.right() - t * r.width() if dedans else r.x() + t * r.width()

        def y_de(dec):
            return r.center().y() - dec / 90.0 * r.height() / 2

        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.c('sphere', 0.25))
        p.drawRect(r)
        dessin.police(p, 0.8)
        for h in range(0, 25, 3):
            x = x_de(15 * h) if h < 24 else (r.x() if dedans else r.right())
            p.setPen(dessin.stylo('grille', 0.8, 0.7))
            p.drawLine(QPointF(x, r.y()), QPointF(x, r.bottom()))
            dessin.texte(p, x, r.bottom() + 12, '%d h' % h, 'doux')
        for d in range(-90, 91, 30):
            y = y_de(d)
            p.setPen(dessin.stylo('grille', 0.8, 0.7))
            p.drawLine(QPointF(r.x(), y), QPointF(r.right(), y))
            dessin.texte(p, r.x() - 26, y, angle(d, 0), 'doux')
        dessin.police(p, 1 / 0.8)
        p.setPen(dessin.stylo('equateur', 2.0))
        p.drawLine(QPointF(r.x(), y_de(0)), QPointF(r.right(), y_de(0)))
        pts = []
        for a in np.linspace(0, 360, 361):
            pts.append(QPointF(x_de(a) if a < 360 else (r.x() if dedans else r.right()), y_de(dec_ecliptique(a, eps))))
        p.setPen(dessin.stylo('ecliptique', 2.2))
        p.drawPolyline(QPolygonF(pts))
        # trajet de la date de début à la date courante
        debut, j = self._debut(), self.jour.value()
        n = int((j - debut) % 365)
        if n > 0:
            seg = []
            for k in range(n + 1):
                s = astro.soleil_jour(ANNEE, debut + k + 0.5)
                seg.append((s['alpha'], s['delta']))
            p.setPen(dessin.stylo('soleil', 3.0, 0.7))
            for (a0, d0), (a1, d1) in zip(seg[:-1], seg[1:]):
                if abs(a1 - a0) < 180:
                    p.drawLine(QPointF(x_de(a0), y_de(d0)), QPointF(x_de(a1), y_de(d1)))
        s = astro.soleil_jour(ANNEE, j + 0.5)
        dessin.disque(p, x_de(s['alpha']), y_de(s['delta']), 9, 'soleil')
        dessin.texte(p, r.center().x(), r.y() - 14, tr('anim_seasonsim_titre_dedans' if dedans
                                                        else 'anim_seasonsim_titre_dehors'), 'doux')
        dessin.police(p, 0.8)
        for cle, lam in (('anim_seasonsim_pv', 0.0), ('anim_seasonsim_se', 90.0), ('anim_seasonsim_pa', 180.0),
                         ('anim_seasonsim_sh', 270.0)):
            a, d = astro.ecliptique_vers_equatorial(lam, 0.0, eps)
            w = p.fontMetrics().horizontalAdvance(tr(cle)) / 2 + 4
            x = min(max(x_de(a), r.x() + w), r.right() - w)
            dessin.texte(p, x, y_de(d) + (16 if d >= 0 else -16), tr(cle), 'ecliptique', fond=True)
        dessin.police(p, 1 / 0.8)
