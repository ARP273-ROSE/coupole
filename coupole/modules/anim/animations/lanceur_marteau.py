"""Hammer Thrower Comparison : un lanceur de marteau qui fait tourner la boule tourne lui-même autour de leur centre
de masse commun, comme une étoile autour du centre de masse qu'elle partage avec sa planète.  Les deux corps
tournent avec la même période, sur des cercles de rayons inversement proportionnels à leurs masses :
r₁ / r₂ = m₂ / m₁.  L'original montrait un film d'athlète ; ici les deux systèmes sont simulés côte à côte, avec un
marteau réglementaire (7,26 kg) et une étoile (masse de l'original : 6,2 pour 1,2)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre

MARTEAU_KG = 7.26                 # masse du marteau masculin (World Athletics)
RAYON_M = 2.0                     # distance lanceur-boule (bras + câble de 1,215 m au plus), ≈


class LanceurMarteau(Animation):
    ID = 'hammerthrower'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.m_lanceur = self.curseur('lanceur', 40.0, 150.0, 110.0, dec=0, unite='kg')
        self.m_marteau = self.curseur('marteau', 1.0, 20.0, MARTEAU_KG, dec=2, unite='kg')
        self.rapport = self.curseur('rapport', 1.0, 20.0, 6.2 / 1.2, dec=2)
        self.c_trajets = self.coche('trajets', True)
        self.angle = 0.0

    def etat_initial(self):
        self.angle = 0.0

    def avancer(self, dt):
        self.angle += dt * 2 * math.pi * 0.35

    def valeurs(self):
        m1, m2 = self.m_lanceur.value(), self.m_marteau.value()
        r1 = RAYON_M * m2 / (m1 + m2)
        q = self.rapport.value()
        return [(tr('anim_hammerthrower_r_lanceur'), '%s m' % nombre(r1, 3)),
                (tr('anim_hammerthrower_r_boule'), '%s m' % nombre(RAYON_M - r1, 3)),
                (tr('anim_hammerthrower_rapport_v'), '%s / %s = %s' % (nombre(r1, 3), nombre(RAYON_M - r1, 3),
                                                                      nombre(m2 / m1, 3))),
                (tr('anim_hammerthrower_r_etoile'), '%s %%' % nombre(100 / (1 + q), 1))]

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.95)
        m1, m2 = self.m_lanceur.value(), self.m_marteau.value()
        self._systeme(p, dessin.cadre(p, z[0], tr('anim_hammerthrower_titre_lanceur')), m1, m2, 'lanceur')
        q = self.rapport.value()
        self._systeme(p, dessin.cadre(p, z[1], tr('anim_hammerthrower_titre_etoile')), q, 1.0, 'etoile')

    def _systeme(self, p, r, m1, m2, genre):
        cx, cy = r.center().x(), r.center().y() + 6
        d = min(r.width(), r.height()) * 0.40
        r1, r2 = d * m2 / (m1 + m2), d * m1 / (m1 + m2)
        a = self.angle
        x1, y1 = cx - r1 * math.cos(a), cy + r1 * math.sin(a)
        x2, y2 = cx + r2 * math.cos(a), cy - r2 * math.sin(a)
        if self.c_trajets.isChecked():
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.setPen(dessin.stylo('accent1' if genre == 'etoile' else 'accent2', 1.0, 0.7, True))
            p.drawEllipse(QPointF(cx, cy), r1, r1)
            p.setPen(dessin.stylo('equateur', 1.0, 0.7, True))
            p.drawEllipse(QPointF(cx, cy), r2, r2)
        # tailles proportionnées au panneau : le lanceur (ou l'étoile) ne recouvre jamais la boule (ou la planète)
        rg = max(6.0, min(16.0, d * 0.16))
        rp = max(4.0, min(7.0, d * 0.07))
        p.setPen(dessin.stylo('doux', 1.5))
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        p.setPen(dessin.stylo('accent3', 2.0))
        p.drawLine(QPointF(cx - 6, cy), QPointF(cx + 6, cy))
        p.drawLine(QPointF(cx, cy - 6), QPointF(cx, cy + 6))
        dessin.reserver(p, cx, cy, 7)
        if genre == 'lanceur':
            dessin.disque(p, x1, y1, rg, 'accent2', bord='texte')
            dessin.disque(p, x2, y2, rp, 'doux', bord='texte')
            noms = ((x1, y1, rg, tr('anim_hammerthrower_lanceur_n'), 'accent2'),
                    (x2, y2, rp, tr('anim_hammerthrower_boule'), 'doux'))
        else:
            dessin.disque(p, x1, y1, rg, 'soleil')
            dessin.disque(p, x2, y2, rp, 'equateur', bord='texte')
            noms = ((x1, y1, rg, tr('anim_c_etoile'), 'accent1'), (x2, y2, rp, tr('anim_c_planete'), 'equateur'))
        # étiquettes autour des objets (placeur commun : jamais l'une sur l'autre ni sur un objet)
        dessin.etiquette(p, cx, cy, tr('anim_c_barycentre'), 'accent3', 9)
        for x, y, rr, s_, cle in noms:
            dessin.etiquette(p, x, y, s_, cle, rr * 0.75 + 5)
