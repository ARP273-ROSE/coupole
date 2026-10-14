"""Distance Modulus Explorer : m − M = 5 log₁₀ d − 5 (d en parsecs).  On verrouille une des trois grandeurs
(M, m ou d) et on fait varier les deux autres ; l'étoile se place sur une échelle logarithmique des distances
(1 à 1 000 pc) et son éclat dessiné suit la magnitude absolue.  Bornes des curseurs comme dans l'original."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre

D_MIN, D_MAX = 1.0, 1000.0
M_ABS = (-8.0, 18.0)


class ModuleDistance(Animation):
    ID = 'stellarmag'
    ANIMEE = False

    def construire(self):
        self.verrou = self.choix('verrou', [('anim_stellarmag_verrou_M', 'M'), ('anim_stellarmag_verrou_m', 'm'),
                                            ('anim_stellarmag_verrou_d', 'd')], 'M')
        self.m = self.curseur('m', -8.0, 18.0, 5.0, dec=1, cle_texte='anim_stellarmag_m')
        self.M = self.curseur('M_abs', -8.0, 18.0, 5.0, dec=1, cle_texte='anim_stellarmag_M')
        self.d = self.curseur('d', D_MIN, D_MAX, 10.0, dec=1, unite='pc', log=True, cle_texte='anim_stellarmag_d')
        self._occupe = False
        self.m.valueChanged.connect(lambda v: self._bouge('m'))
        self.M.valueChanged.connect(lambda v: self._bouge('M'))
        self.d.valueChanged.connect(lambda v: self._bouge('d'))
        self._bornes()
        self._bouge('d')

    def _bornes(self):
        """Bornes dépendant du verrou (reprises de l'original) : les trois grandeurs restent compatibles."""
        v = self.verrou.currentData()
        lmax, lmin = math.log10(D_MAX), math.log10(D_MIN)
        self._occupe = True
        if v == 'M':
            self.m.borner(M_ABS[0] + (-5 + 5 * lmin), M_ABS[1] + (-5 + 5 * lmax))
            self.M.borner(*M_ABS)
            self.d.borner(D_MIN, D_MAX)
        elif v == 'm':
            self.m.borner(-13.0, 28.0)
            self.M.borner(*M_ABS)
            self.d.borner(D_MIN, D_MAX)
        else:
            mu = astro.module_de_distance(self.d.value())
            self.m.borner(M_ABS[0] + mu, M_ABS[1] + mu)
            self.M.borner(*M_ABS)
            self.d.borner(D_MIN, D_MAX)
        for w in (self.m, self.M, self.d):
            w.setEnabled(w is not {'M': self.M, 'm': self.m, 'd': self.d}[v])
        self._occupe = False

    def reglage_change(self):
        if not self._occupe and hasattr(self, 'd'):
            self._bornes()
        super().reglage_change()

    def _bouge(self, qui: str):
        """Recalcule la grandeur libre restante : m − M = 5 log d − 5."""
        if self._occupe:
            return
        self._occupe = True
        v = self.verrou.currentData()
        mu = astro.module_de_distance(self.d.value())
        if v == 'M':
            if qui == 'm':
                self.d.setValue(min(D_MAX, max(D_MIN, astro.distance_du_module(self.m.value() - self.M.value()))))
                self.m.setValue(self.M.value() + astro.module_de_distance(self.d.value()))
            else:
                self.m.setValue(self.M.value() + mu)
        elif v == 'm':
            if qui == 'M':
                self.d.setValue(min(D_MAX, max(D_MIN, astro.distance_du_module(self.m.value() - self.M.value()))))
                self.M.setValue(self.m.value() - astro.module_de_distance(self.d.value()))
            else:
                self.M.setValue(self.m.value() - mu)
        else:
            if qui == 'm':
                self.M.setValue(self.m.value() - mu)
            else:
                self.m.setValue(self.M.value() + mu)
        self._occupe = False
        self.rafraichir()

    def valeurs(self):
        mu = astro.module_de_distance(self.d.value())
        return [(tr('anim_stellarmag_equation'), '%s − (%s) = %s' % (nombre(self.m.value(), 1), nombre(self.M.value(), 1),
                                                                    nombre(self.m.value() - self.M.value(), 1))),
                (tr('anim_stellarmag_module'), '5 log₁₀(%s) − 5 = %s' % (nombre(self.d.value(), 1), nombre(mu, 2))),
                (tr('anim_stellarmag_d'), '%s pc = %s al' % (nombre(self.d.value(), 1),
                                                              nombre(self.d.value() * astro.PC_EN_AL, 0)))]

    def presser(self, pos, bouton):
        if self.verrou.currentData() != 'd' and getattr(self, '_axe', None) and abs(pos.y() - self._axe[2]) < 30:
            self._glisse = self._tirer
            return True
        return False

    def _tirer(self, pos):
        x0, x1, _ = self._axe
        t = max(0.0, min(1.0, (pos.x() - x0) / (x1 - x0)))
        self.d.setValue(10 ** (math.log10(D_MIN) + t * (math.log10(D_MAX) - math.log10(D_MIN))))

    def dessiner(self, p, rect):
        x0, x1 = rect.x() + 50, rect.right() - 40
        y = rect.center().y()
        self._axe = (x0, x1, y)
        p.setPen(dessin.stylo('grille', 1.5))
        p.drawLine(QPointF(x0, y), QPointF(x1, y))
        dessin.disque(p, x0 - 22, y, 9, 'terre')
        dessin.texte(p, x0 - 22, y - 20, tr('anim_shadowsim_terre'), 'doux')
        for dd in (1, 10, 100, 1000):
            x = x0 + (x1 - x0) * math.log10(dd) / 3
            p.setPen(dessin.stylo('doux', 1.0))
            p.drawLine(QPointF(x, y - 6), QPointF(x, y + 6))
            dessin.texte(p, x, y + 20, '%d pc' % dd, 'doux')
        t = math.log10(self.d.value()) / 3
        x = x0 + (x1 - x0) * t
        mabs = self.M.value()
        f = (mabs - M_ABS[0]) / (M_ABS[1] - M_ABS[0])
        rayon = 18 * (1.2 - 0.2 * f) * 0.7 + 4
        dessin.disque(p, x, y, rayon * 1.8, 'soleil', alpha=0.12 * (1 - f) + 0.05)
        dessin.disque(p, x, y, rayon, 'etoile', alpha=1.0 - 0.3 * f)
        dessin.texte(p, x, y - rayon - 14, 'd = %s pc' % nombre(self.d.value(), 1), 'accent2', fond=True)
        dessin.police(p, 1.25, gras=True)
        dessin.formule(p, rect.center().x(), rect.y() + 34, 'm − M = 5 log₁₀ d − 5', 'texte')
        dessin.police(p, 1 / 1.25)
        dessin.texte(p, rect.center().x(), rect.y() + 62, '%s − (%s) = %s' % (
            nombre(self.m.value(), 1), nombre(self.M.value(), 1), nombre(self.m.value() - self.M.value(), 1)), 'accent1')
