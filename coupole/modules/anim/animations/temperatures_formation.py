"""Planet Formation Temperatures Plot : la température de la nébuleuse solaire décroissait avec la distance au
Soleil.  Selon la température, chaque substance était gazeuse ou solide : métaux et silicates condensent près du
Soleil (planètes telluriques), glaces d'eau, d'ammoniac et de méthane au-delà de la « ligne des glaces »
(planètes géantes).  Modèle de l'original : loi de puissance passant par 600 K à 1 ua et 175 K à 5,2 ua,
T = 600 K × (d / 1 ua)^−0,747 ; températures de condensation de l'original."""
from __future__ import annotations

import math

from PyQt6.QtCore import QRectF

from ....core.i18n import tr
from .. import dessin, donnees_lot3 as D
from ..base import Animation, nombre
from ..graphe import Axes

(D0, T0), (D1, T1) = D.FORMATION_TERRE, D.FORMATION_JUPITER
PENTE = math.log(T0 / T1) / math.log(D1 / D0)            # 0,747 1…


def temperature(d_ua: float) -> float:
    return T0 * (d_ua / D0) ** -PENTE


def distance(t: float) -> float:
    return D0 * (T0 / t) ** (1 / PENTE)


class TemperaturesFormation(Animation):
    ID = 'formationtemps'
    ANIMEE = False

    def construire(self):
        self.t = self.curseur('temperature', 20.0, 2000.0, 175.0, dec=0, unite='K', log=True)

    def valeurs(self):
        t = self.t.value()
        solides = [tr('anim_formationtemps_s_' + n) for n, tc in D.CONDENSATION_K if t <= tc]
        return [(tr('anim_formationtemps_distance'), '%s %s' % (nombre(distance(t), 2), tr('anim_c_ua'))),
                (tr('anim_formationtemps_solides'), ', '.join(solides) or tr('anim_c_aucun'))]

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.62) if rect.width() >= 640 else dessin.zones(rect, 2, 10.0)
        r = dessin.cadre(p, z[0], tr('anim_formationtemps_titre'))
        ax = Axes(r, 0.1, 50.0, 20.0, 2000.0, xlog=True, ylog=True, marges=(50, 10, 12, 30)).avec(p)
        ax.fond(p, tr('anim_formationtemps_axe_d'), tr('anim_formationtemps_axe_t'))
        ax.courbe([(0.1 * 10 ** (k / 50), temperature(0.1 * 10 ** (k / 50))) for k in range(136)], 'accent1', 2.5)
        dessin.police(p, 0.85)
        for nom, d in D.DISTANCES_UA:
            t = temperature(d)
            ax.points([(d, t)], 'equateur', 5, 1.0)
            dessin.texte(p, ax.px(d) + 6, ax.py(t) - 10, tr('anim_planete_' + nom), 'texte', centre=False)
        dessin.police(p, 1 / 0.85)
        t = self.t.value()
        ax.horizontale(t, 'accent3', 1.2, True)
        ax.verticale(distance(t), 'accent3', 1.2, True)
        ax.points([(distance(t), t)], 'accent3', 7, 1.0)
        # tableau gaz / solide
        rt = dessin.cadre(p, z[1], tr('anim_formationtemps_titre_etats'))
        n = len(D.CONDENSATION_K)
        h = rt.height() / n
        dessin.police(p, 0.9)
        for k, (nom, tc) in enumerate(D.CONDENSATION_K):
            y = rt.top() + k * h
            solide = t <= tc
            p.fillRect(QRectF(rt.left(), y + 2, rt.width(), h - 4), dessin.c('accent2' if solide else 'grille', 0.25))
            dessin.texte(p, rt.left() + 6, y + h / 2 + 4, '%s (%d K)' % (tr('anim_formationtemps_s_' + nom), tc),
                         'texte', centre=False)
            etat = tr('anim_formationtemps_solide' if solide else 'anim_formationtemps_gaz')
            dessin.texte(p, rt.right() - 6 - p.fontMetrics().horizontalAdvance(etat), y + h / 2 + 4, etat,
                         'accent2' if solide else 'doux', centre=False)
        dessin.police(p, 1 / 0.9)
