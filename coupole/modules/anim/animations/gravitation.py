"""Newton's Law of Gravity Calculator : la force de gravitation entre deux masses, de l'électron à la Voie lactée,
à des distances du proton au rayon de l'Univers observable.  F = G M₁ M₂ / R² (G = 6,674 30 × 10⁻¹¹, CODATA 2018 ;
l'original prenait 6,67 × 10⁻¹¹), et l'accélération de chaque corps a = F / M.  Curseurs en puissances de dix,
préréglages de l'original (valeurs actuelles), mémoire des résultats comme l'original."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre

# préréglages (masses en kg, distances en m) ; valeurs de référence actuelles
MASSES = (('electron', 9.109_383_7e-31), ('proton', 1.672_621_9e-27), ('pomme', 0.102), ('kilogramme', 1.0),
          ('personne', 72.0), ('montagne', 1e15), ('asteroide', 1e18), ('lune', astro.MASSE_LUNE_KG),
          ('mars', 6.4171e23), ('terre', astro.MASSE_TERRE_KG), ('jupiter', 1.898_19e27),
          ('soleil', astro.MASSE_SOLEIL_KG), ('voie_lactee', 1.15e42))
DISTANCES = (('proton', 1e-15), ('atome', 1e-10), ('metre', 1.0), ('deux_metres', 2.0),
             ('rayon_terre', 6.371e6), ('lune', astro.D_LUNE_KM * 1e3), ('mars', 5.7e10),
             ('soleil', astro.UA_KM * 1e3), ('jupiter', 5.9e11), ('etoile', 4.0e16), ('voie_lactee', 4.7e20),
             ('univers', 4.4e26))
LOG_M = (math.log10(9.1e-31), math.log10(1.2e42))
LOG_R = (-15.0, math.log10(8.8e26))
_EXPOSANTS = str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹')


def scientifique(x: float, chiffres: int = 3) -> str:
    """« 6,67 × 10⁻¹¹ » (virgule décimale selon la langue)."""
    if x == 0 or not math.isfinite(x):
        return nombre(x, 0)
    e = math.floor(math.log10(abs(x)))
    m = x / 10 ** e
    if round(m, chiffres - 1) >= 10:
        m, e = m / 10, e + 1
    s = nombre(m, chiffres - 1)
    return s if e == 0 else '%s × 10%s' % (s, str(e).translate(_EXPOSANTS))


def calcul(m1: float, m2: float, r: float) -> dict:
    f = astro.force_gravitation(m1, m2, r)
    return {'F': f, 'a1': f / m1, 'a2': f / m2}


class Gravitation(Animation):
    ID = 'gravcalc'
    ANIMEE = False

    def construire(self):
        self.lm1 = self.curseur('m1', *LOG_M, math.log10(0.102), dec=3, unite='log kg', rafraichir=False)
        self.p1 = self.choix('pm1', [('anim_gravcalc_libre', '')] + [('anim_gravcalc_m_' + k, k) for k, _ in MASSES],
                             'pomme')
        self.lm2 = self.curseur('m2', *LOG_M, math.log10(astro.MASSE_TERRE_KG), dec=3, unite='log kg', rafraichir=False)
        self.p2 = self.choix('pm2', [('anim_gravcalc_libre', '')] + [('anim_gravcalc_m_' + k, k) for k, _ in MASSES],
                             'terre')
        self.lr = self.curseur('r', *LOG_R, math.log10(6.371e6), dec=3, unite='log m', rafraichir=False)
        self.pr = self.choix('pr', [('anim_gravcalc_libre', '')] + [('anim_gravcalc_d_' + k, k) for k, _ in DISTANCES],
                             'rayon_terre')
        self.bouton('anim_gravcalc_memoriser', self.memoriser)
        self.bouton('anim_gravcalc_effacer', self.effacer)
        self.memoire = []
        self._sync = False
        for prereglage, reglage, table in ((self.p1, self.lm1, MASSES), (self.p2, self.lm2, MASSES),
                                           (self.pr, self.lr, DISTANCES)):
            prereglage.activated.connect(lambda _=0, pr=prereglage, rg=reglage, tb=table: self._prereglage(pr, rg, tb))
            reglage.valueChanged.connect(lambda _=0, pr=prereglage, rg=reglage, tb=table: self._libre(pr, rg, tb))

    def _prereglage(self, pr, rg, table):
        for k, v in table:
            if k == pr.currentData():
                self._sync = True
                rg.setValue(math.log10(v))
                self._sync = False
        self.rafraichir()

    def _libre(self, pr, rg, table):
        if not self._sync:
            cle = next((k for k, v in table if abs(math.log10(v) - rg.value()) < 5e-4), '')
            pr.blockSignals(True)
            pr.setCurrentIndex(max(0, pr.findData(cle)))
            pr.blockSignals(False)
        self.rafraichir()

    def grandeurs(self):
        """Valeurs exactes du préréglage choisi, sinon 10 ** (valeur du curseur)."""
        out = []
        for pr, rg, table in ((self.p1, self.lm1, MASSES), (self.p2, self.lm2, MASSES), (self.pr, self.lr, DISTANCES)):
            exacte = dict(table).get(pr.currentData())
            out.append(exacte if exacte is not None else 10 ** rg.value())
        return tuple(out)

    def memoriser(self):
        m1, m2, r = self.grandeurs()
        self.memoire = (self.memoire + [(m1, m2, r, calcul(m1, m2, r)['F'])])[-6:]
        self.rafraichir()

    def effacer(self):
        self.memoire = []
        self.rafraichir()

    def etat_initial(self):
        self.memoire = []

    def valeurs(self):
        m1, m2, r = self.grandeurs()
        c = calcul(m1, m2, r)
        return [('M₁', '%s kg' % scientifique(m1)), ('M₂', '%s kg' % scientifique(m2)), ('R', '%s m' % scientifique(r)),
                (tr('anim_gravcalc_force'), '%s N' % scientifique(c['F'])),
                (tr('anim_gravcalc_a1'), '%s m/s²' % scientifique(c['a1'])),
                (tr('anim_gravcalc_a2'), '%s m/s²' % scientifique(c['a2']))]

    def dessiner(self, p, rect):
        m1, m2, r = self.grandeurs()
        c = calcul(m1, m2, r)
        cx = rect.center().x()
        y = rect.y() + rect.height() * 0.18
        dessin.police(p, 1.25)
        dessin.formule(p, cx, y, 'F = G M₁ M₂ / R²')
        dessin.formule(p, cx, y + 44, '= (%s) (%s) (%s) / (%s)²' % (scientifique(astro.G_SI), scientifique(m1),
                                                                 scientifique(m2), scientifique(r)), 'doux')
        dessin.police(p, 1.25, gras=True)
        dessin.texte(p, cx, y + 86, '= %s N' % scientifique(c['F']), 'accent1')
        dessin.police(p, 1 / 1.25 / 1.25)
        # deux corps, flèches d'accélération à l'échelle logarithmique
        yc = rect.y() + rect.height() * 0.55
        x1, x2 = rect.x() + rect.width() * 0.25, rect.x() + rect.width() * 0.75
        r1 = 8 + 3 * (self.lm1.value() - LOG_M[0]) / (LOG_M[1] - LOG_M[0]) * 10
        r2 = 8 + 3 * (self.lm2.value() - LOG_M[0]) / (LOG_M[1] - LOG_M[0]) * 10
        for x, rr, a, sens, cle in ((x1, r1, c['a1'], 1, 'accent3'), (x2, r2, c['a2'], -1, 'accent2')):
            lg = max(0.0, min(1.0, (math.log10(a) + 40) / 80)) * (x2 - x1) * 0.42 if a > 0 else 0
            if lg > 3:
                dessin.fleche(p, x + sens * rr, yc, x + sens * (rr + lg), yc, dessin.stylo(cle, 2.4), 9)
            dessin.disque(p, x, yc, rr, cle)
            dessin.texte(p, x, yc + rr + 14, 'a = %s m/s²' % scientifique(a), cle)
        if self.memoire:
            self._table(p, QRectF(rect.x() + 10, rect.y() + rect.height() * 0.70, rect.width() - 20,
                                  rect.height() * 0.30 - 8))

    def _table(self, p, r):
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.c('sphere', 0.2))
        p.drawRoundedRect(r, 6, 6)
        dessin.police(p, 0.8)
        cols = ('M₁ (kg)', 'M₂ (kg)', 'R (m)', 'F (N)')
        lh = min(18.0, r.height() / (len(self.memoire) + 1.5))
        for j, titre in enumerate(cols):
            x = r.x() + r.width() * (j + 0.5) / 4
            dessin.texte(p, x, r.y() + lh * 0.8, titre, 'doux')
            for i, ligne in enumerate(self.memoire):
                dessin.texte(p, x, r.y() + lh * (i + 1.8), scientifique(ligne[j]))
        dessin.police(p, 1 / 0.8)
