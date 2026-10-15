"""Proton-Proton Animation, CNO Cycle Animation : les réactions qui font briller le Soleil.  Quatre protons
deviennent un noyau d'hélium 4 ; la masse perdue devient énergie, E = Δm c².  Énergie libérée par chaque étape
calculée à partir des excès de masse atomique (AME 2020) : 0,420 + 1,022 (annihilation du positon) MeV, 5,493 MeV,
12,860 MeV pour la chaîne proton-proton ; 26,731 MeV au total (dont une petite part emportée par les neutrinos :
0,265 MeV en moyenne pour pp, 0,707 et 0,997 MeV pour ¹³N et ¹⁵O).  L'original montrait des films sans chiffres."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import dessin, donnees_lot3 as D
from ..base import Animation, nombre

E = D.EXCES_MASSE_KEV
ME = D.ME_KEV
NU = D.NEUTRINO_MOYEN_KEV
DUREE_ETAPE = 4.0

# étape : (réactifs, produits, Q en keV (énergie cinétique + γ), neutrino emporté (keV), annihilation (keV), fois)
ETAPES_PP = (
    (('p', 'p'), ('d', 'e+', 'nu'), 2 * E['p'] - E['d'] - 2 * ME, NU['pp'], 2 * ME, 2),
    (('d', 'p'), ('he3', 'gamma'), E['d'] + E['p'] - E['he3'], 0.0, 0.0, 2),
    (('he3', 'he3'), ('he4', 'p', 'p'), 2 * E['he3'] - E['he4'] - 2 * E['p'], 0.0, 0.0, 1),
)
ETAPES_CNO = (
    (('c12', 'p'), ('n13', 'gamma'), E['c12'] + E['p'] - E['n13'], 0.0, 0.0, 1),
    (('n13',), ('c13', 'e+', 'nu'), E['n13'] - E['c13'] - 2 * ME, NU['n13'], 2 * ME, 1),
    (('c13', 'p'), ('n14', 'gamma'), E['c13'] + E['p'] - E['n14'], 0.0, 0.0, 1),
    (('n14', 'p'), ('o15', 'gamma'), E['n14'] + E['p'] - E['o15'], 0.0, 0.0, 1),
    (('o15',), ('n15', 'e+', 'nu'), E['o15'] - E['n15'] - 2 * ME, NU['o15'], 2 * ME, 1),
    (('n15', 'p'), ('c12', 'he4'), E['n15'] + E['p'] - E['c12'] - E['he4'], 0.0, 0.0, 1),
)
# symbole, nombre de protons, nombre de nucléons
NOYAUX = {'p': ('¹H', 1, 1), 'd': ('²H', 1, 2), 'he3': ('³He', 2, 3), 'he4': ('⁴He', 2, 4), 'c12': ('¹²C', 6, 12),
          'n13': ('¹³N', 7, 13), 'c13': ('¹³C', 6, 13), 'n14': ('¹⁴N', 7, 14), 'o15': ('¹⁵O', 8, 15),
          'n15': ('¹⁵N', 7, 15)}
# neutrino : la lettre grecque nu (U+03BD), avec l'indice e (neutrino électronique), jamais la lettre latine v
LEPTONS = {'e+': 'e⁺', 'nu': 'νₑ', 'gamma': 'γ'}
RAYON_MIN_LEPTON = 10.0        # rayon minimal (px) des particules légères à l'écran : agrandies, la légende le dit


def energie_totale(etapes) -> float:
    """Énergie totale libérée (keV), annihilations comprises : 4 Δ(¹H) − Δ(⁴He) = 26 731 keV."""
    return sum((q + ann) * n for _, _, q, _, ann, n in etapes)


def energie_neutrinos(etapes) -> float:
    return sum(nu * n for _, _, _, nu, _, n in etapes)


def equation(etape) -> str:
    nom = lambda k: NOYAUX[k][0] if k in NOYAUX else LEPTONS[k]
    return '%s → %s' % (' + '.join(nom(k) for k in etape[0]), ' + '.join(nom(k) for k in etape[1]))


class _Fusion(Animation):
    ETAPES = ETAPES_PP
    LECTURE_AU_DEPART = True

    def construire(self):
        self.bouton('anim_fusion_suivante', self.suivante)
        self.etat_initial()

    def etat_initial(self):
        self.t = 0.0
        self.leptons = []          # particules légères de la dernière image : (genre, x, y, rayon) (tests)

    def suivante(self):
        self.t = (math.floor(self.t / DUREE_ETAPE) + 1) * DUREE_ETAPE % (len(self.ETAPES) * DUREE_ETAPE)
        self.rafraichir()

    def avancer(self, dt):
        self.t = (self.t + dt) % (len(self.ETAPES) * DUREE_ETAPE)

    def etape(self):
        return int(self.t // DUREE_ETAPE), (self.t % DUREE_ETAPE) / DUREE_ETAPE

    def valeurs(self):
        k, _ = self.etape()
        et = self.ETAPES[k]
        out = [(tr('anim_fusion_etape'), '%d / %d – %s' % (k + 1, len(self.ETAPES), equation(et))),
               (tr('anim_fusion_q'), '%s MeV' % nombre((et[2] + et[4]) / 1000, 3))]
        out += [(tr('anim_fusion_total'), '%s MeV' % nombre(energie_totale(self.ETAPES) / 1000, 3)),
                (tr('anim_fusion_neutrinos'), '%s MeV' % nombre(energie_neutrinos(self.ETAPES) / 1000, 3))]
        return out

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.6) if rect.width() >= 640 else dessin.zones(rect, 2, 10.0)
        self._scene(p, dessin.cadre(p, z[0], tr('anim_fusion_titre_scene')))
        self._tableau(p, dessin.cadre(p, z[1], tr('anim_fusion_titre_etapes')))

    def _noyau(self, p, x, y, k, s):
        sym, z, a = NOYAUX[k]
        r = s * (0.7 + 0.35 * a ** (1 / 3))
        dessin.disque(p, x, y, r, 'accent3' if a == 1 else ('accent1' if k.startswith('he') else 'equateur'),
                      bord='texte')
        dessin.texte(p, x, y, sym, 'fond')

    def _lepton(self, p, x, y, k, s, dx, dy):
        """Particule légère, reconnaissable et agrandie (rayon ≥ RAYON_MIN_LEPTON) : positon = petite sphère marquée
        « + », neutrino = flèche fine en pointillé, photon γ = flèche ondulée jaune ; étiquette à taille normale, posée
        par le placeur anti-collision (trait de rappel s'il l'éloigne)."""
        n = math.hypot(dx, dy) or 1.0
        ux, uy = dx / n, dy / n
        r = max(RAYON_MIN_LEPTON, s * 0.45)
        self.leptons.append((k, x, y, r))
        if k == 'gamma':
            longueur = r * 4.2
            pts = []
            for i in range(41):
                d = -(i / 40) * longueur
                a = r * 0.45 * math.sin((i / 40) * math.pi * 6)
                pts.append(QPointF(x + ux * d - uy * a, y + uy * d + ux * a))
            p.setPen(dessin.stylo('soleil', 2.2))
            p.drawPolyline(QPolygonF(pts))
            dessin.fleche(p, x - ux * 2, y - uy * 2, x + ux * r * 0.6, y + uy * r * 0.6, dessin.stylo('soleil', 2.2), 9)
            dessin.etiquette(p, x, y, 'γ', 'soleil', r)
        elif k == 'e+':
            dessin.disque(p, x, y, r, 'accent2', bord='texte')
            dessin.police(p, 1.15, True)
            dessin.texte(p, x, y + 1, '+', 'fond')
            dessin.police(p, 1 / 1.15)
            dessin.etiquette(p, x, y, 'e⁺', 'accent2', r)
        else:
            p.setPen(dessin.stylo('doux', 1.4, 0.95, True))
            p.drawLine(QPointF(x - ux * r * 3.6, y - uy * r * 3.6), QPointF(x, y))
            dessin.fleche(p, x - ux * 2, y - uy * 2, x + ux * r * 0.5, y + uy * r * 0.5, dessin.stylo('doux', 1.4), 8)
            dessin.etiquette(p, x, y, 'νₑ', 'doux', r)

    def _legende(self, p, r):
        """Légende des symboles (coin haut gauche) ; rappel que les particules légères ne sont pas à l'échelle."""
        dessin.police(p, 0.82)
        fm = p.fontMetrics()
        h = fm.height() + 4
        x, y = r.left() + 8, r.top() + 6

        def positon(cx, cy):
            dessin.disque(p, cx, cy, 6, 'accent2', bord='texte')

        def neutrino(cx, cy):
            p.setPen(dessin.stylo('doux', 1.3, 0.95, True))
            p.drawLine(QPointF(cx - 9, cy), QPointF(cx + 6, cy))
            dessin.fleche(p, cx + 2, cy, cx + 8, cy, dessin.stylo('doux', 1.3), 5)

        def gamma(cx, cy):
            p.setPen(dessin.stylo('soleil', 1.6))
            p.drawPolyline(QPolygonF([QPointF(cx - 9 + i / 16 * 15, cy + 2.5 * math.sin(i / 16 * math.pi * 4))
                                      for i in range(17)]))

        for f, cle in ((positon, 'anim_fusion_legende_positon'), (neutrino, 'anim_fusion_legende_neutrino'),
                       (gamma, 'anim_fusion_legende_gamma')):
            f(x + 9, y + h / 2)
            dessin.texte(p, x + 24, y + h / 2 + fm.ascent() / 2 - 1, tr(cle), 'texte', centre=False)
            y += h
        dessin.texte(p, x, y + h / 2 + fm.ascent() / 2 - 1, tr('anim_fusion_echelle'), 'doux', centre=False)
        dessin.police(p, 1 / 0.82)

    def _scene(self, p, r):
        k, f = self.etape()
        reac, prod = self.ETAPES[k][0], self.ETAPES[k][1]
        self.leptons = []
        self._legende(p, r)
        # la réaction, centrée et grande (l'équation est écrite en bas)
        cx, cy = r.center().x(), r.center().y() - 8
        s = min(r.width(), r.height()) / 10.5
        L = min(r.width() * 0.36, r.height() * 0.32)
        if f < 0.45:                                    # approche des réactifs
            u = 1 - f / 0.45
            for i, n in enumerate(reac):
                d = L * u if len(reac) > 1 else 0.0             # une désintégration : le noyau reste au centre
                self._noyau(p, cx + (-d if i == 0 else d), cy, n, s)
        else:                                           # éclair puis produits qui s'écartent
            u = (f - 0.45) / 0.55
            if u < 0.15:
                dessin.disque(p, cx, cy, s * 2.2 * (1 - u / 0.15) + 1, 'soleil', alpha=0.6)
            for i, n in enumerate(prod):
                ang = -math.pi / 2 + 2 * math.pi * i / len(prod) + 0.4
                d = L * 0.9 * u
                x, y = cx + d * math.cos(ang), cy + d * math.sin(ang)
                if n in NOYAUX:
                    self._noyau(p, x, y, n, s)
                else:
                    self._lepton(p, x, y, n, s, math.cos(ang), math.sin(ang))
        dessin.police(p, 1.1)
        dessin.texte(p, cx, r.bottom() - 12, equation(self.ETAPES[k]), 'texte')
        dessin.police(p, 1 / 1.1)

    def _tableau(self, p, r):
        k, _ = self.etape()
        n = len(self.ETAPES)
        h = min(40.0, r.height() / (n + 1.5))
        dessin.police(p, 0.9)
        for i, et in enumerate(self.ETAPES):
            y = r.top() + i * h
            if i == k:
                p.fillRect(QRectF(r.left(), y + 2, r.width(), h - 4), dessin.c('accent1', 0.18))
            fois = ' (×%d)' % et[5] if et[5] > 1 else ''
            dessin.texte(p, r.left() + 6, y + h / 2 + 4, equation(et) + fois, 'texte', centre=False)
            q = '%s MeV' % nombre((et[2] + et[4]) / 1000, 3)
            dessin.texte(p, r.right() - 6 - p.fontMetrics().horizontalAdvance(q), y + h / 2 + 4, q, 'accent1',
                         centre=False)
        y = r.top() + n * h + 8
        tot = tr('anim_fusion_bilan', e=nombre(energie_totale(self.ETAPES) / 1000, 3))
        dessin.texte(p, r.left() + 6, y + 10, tot, 'accent3', centre=False)
        dessin.police(p, 1 / 0.9)


class FusionPP(_Fusion):
    ID = 'fusion01'
    ETAPES = ETAPES_PP


class FusionCNO(_Fusion):
    ID = 'fusion02'
    ETAPES = ETAPES_CNO
