"""Traffic Density Analogy : un tracteur lent sur une route ; les voitures ralentissent pour le dépasser, se serrent
derrière lui, puis repartent.  Le bouchon avance avec le tracteur, mais ce ne sont jamais les mêmes voitures qui le
forment.  Les bras spiraux d'une galaxie sont des ondes de densité du même genre : les étoiles les traversent.
Conservation du débit dans le repère du tracteur : n_bouchon (v_lente − v_tracteur) = n (v − v_tracteur), d'où la
densité du bouchon.  L'original montrait des voitures dessinées ; ici la route est vue dans le repère du tracteur
(le marquage au sol défile), avec un flot régulier de voitures qui suivent cette règle."""
from __future__ import annotations

from PyQt6.QtCore import QLineF, QRectF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre

ARRIERE, AVANT = 640.0, 260.0           # route montrée : de 640 m derrière le tracteur à 260 m devant
ZONE = 120.0                            # zone de dépassement derrière le tracteur (m)
ESPACEMENT = 33.0                       # distance entre deux voitures sur route libre (m)
LONGUEUR_VOITURE = 4.5


def rapport_densite(v: float, v_lente: float, v_tracteur: float) -> float:
    """Densité dans la zone lente / densité ailleurs (régime établi) : (v − v_t) / (v_lente − v_t)."""
    return (v - v_tracteur) / (v_lente - v_tracteur)


class OndesDensite(Animation):
    ID = 'trafficdensity'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.v = self.curseur('vitesse', 15.0, 40.0, 30.0, dec=1, unite='m/s')
        self.v_lente = self.curseur('lente', 4.0, 14.0, 10.0, dec=1, unite='m/s')
        self.v_tracteur = self.curseur('v_tracteur', 1.0, 12.0, 5.0, dec=1, unite='m/s')
        self.etat_initial()

    def etat_initial(self):
        n = int((ARRIERE + AVANT) / ESPACEMENT)
        self.u = [-ARRIERE + k * ESPACEMENT for k in range(n)]     # positions dans le repère du tracteur
        self.injection = 0.0
        self.route = 0.0                                          # défilement du marquage au sol

    def vitesses(self):
        vt = min(self.v_tracteur.value(), self.v_lente.value() - 0.5)
        return self.v.value(), self.v_lente.value(), vt

    @staticmethod
    def dans_zone(u: float) -> bool:
        return -ZONE <= u < 0.0

    def avancer(self, dt):
        v, vl, vt = self.vitesses()
        for _ in range(4):
            h = dt / 4
            self.u = [u + ((vl if self.dans_zone(u) else v) - vt) * h for u in self.u if u <= AVANT]
            self.injection += (v - vt) * h
            while self.injection >= ESPACEMENT:                   # flot régulier venant de l'arrière
                self.injection -= ESPACEMENT
                self.u.insert(0, -ARRIERE + self.injection)
            self.route = (self.route + vt * h) % 20.0

    def densites(self):
        dedans = sum(1 for u in self.u if self.dans_zone(u))
        derriere = sum(1 for u in self.u if -ARRIERE + 40 <= u < -ZONE - 40)
        return dedans, (dedans / ZONE) / (derriere / (ARRIERE - ZONE - 80)) if derriere else 0.0

    def valeurs(self):
        v, vl, vt = self.vitesses()
        dedans, mesure = self.densites()
        return [(tr('anim_trafficdensity_prevu'), '× %s' % nombre(rapport_densite(v, vl, vt), 2)),
                (tr('anim_trafficdensity_mesure'), '× %s' % nombre(mesure, 2)),
                (tr('anim_trafficdensity_dans_zone'), str(dedans))]

    def dessiner(self, p, rect):
        r = dessin.cadre(p, rect, tr('anim_trafficdensity_titre'))
        k = (r.width() - 20) / (ARRIERE + AVANT)
        x_de = lambda u: r.left() + 10 + (u + ARRIERE) * k
        y = r.top() + r.height() * 0.35
        p.fillRect(QRectF(r.left() + 6, y - 22, r.width() - 12, 44), dessin.c('sphere', 0.6))
        p.fillRect(QRectF(x_de(-ZONE), y - 22, ZONE * k, 44), dessin.c('accent3', 0.15))
        # marquage au sol : il recule à la vitesse du tracteur (on suit le tracteur)
        p.setPen(dessin.stylo('grille', 2.0))
        u = -ARRIERE - self.route
        traits = []
        while u < AVANT:
            traits.append(QLineF(x_de(u), y, x_de(u + 8), y))
            u += 20.0
        p.drawLines(traits)
        lv = max(3.0, LONGUEUR_VOITURE * k)
        for uu in self.u:
            p.fillRect(QRectF(x_de(uu) - lv, y + 6, lv, 9), dessin.c('accent2'))
        p.fillRect(QRectF(x_de(0.0), y - 16, max(6.0, 6 * k), 12), dessin.c('horizon'))
        dessin.texte(p, x_de(0.0), y - 32, tr('anim_trafficdensity_tracteur'), 'horizon', fond=True)
        dessin.texte(p, x_de(-ZONE / 2), y + 34, tr('anim_trafficdensity_zone'), 'accent3', fond=True)
        # nombre de voitures le long de la route
        yb = r.top() + r.height() * 0.62
        hb = r.bottom() - yb - 6
        nb = 36
        w = (r.width() - 20) / nb
        comptes = [0] * nb
        for uu in self.u:
            i = int((uu + ARRIERE) / (ARRIERE + AVANT) * nb)
            if 0 <= i < nb:
                comptes[i] += 1
        mx = max(comptes) or 1
        for i, c in enumerate(comptes):
            h = hb * c / mx
            p.fillRect(QRectF(r.left() + 10 + i * w, yb + hb - h, w - 1, h), dessin.c('accent2', 0.6))
        dessin.texte(p, r.left() + 10, yb - 6, tr('anim_trafficdensity_densite'), 'doux', centre=False)
