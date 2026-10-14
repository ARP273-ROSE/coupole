"""Gravity Algebra : comment la force de gravitation change quand on multiplie les masses ou la distance.  Loi de
Newton F = G M₁ M₂ / d² : multiplier M₁ par a, M₂ par b et d par c multiplie la force par a b / c² ; facteurs de
l'original (1/3, 1/2, 1, 2, 3), résultat donné en fraction exacte."""
from __future__ import annotations

from fractions import Fraction

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation

FACTEURS = (Fraction(1, 3), Fraction(1, 2), Fraction(1), Fraction(2), Fraction(3))


def facteur_force(m1: Fraction, m2: Fraction, d: Fraction) -> Fraction:
    """Facteur multiplicatif de la force : m₁ m₂ / d²."""
    return Fraction(m1) * Fraction(m2) / (Fraction(d) ** 2)


def texte_fraction(f: Fraction) -> str:
    return str(f.numerator) if f.denominator == 1 else '%d/%d' % (f.numerator, f.denominator)


class AlgebreGravitation(Animation):
    ID = 'gravalgebra'
    ANIMEE = False

    def construire(self):
        options = [('anim_gravalgebra_f_' + texte_fraction(f).replace('/', '_'), texte_fraction(f)) for f in FACTEURS]
        self.m1 = self.choix('m1', options, '1')
        self.m2 = self.choix('m2', options, '1')
        self.d = self.choix('d', options, '1')

    def facteurs(self):
        return tuple(Fraction(w.currentData()) for w in (self.m1, self.m2, self.d))

    def valeurs(self):
        a, b, c = self.facteurs()
        f = facteur_force(a, b, c)
        return [(tr('anim_gravalgebra_calcul'), '(%s × %s) / %s² = %s' % (texte_fraction(a), texte_fraction(b),
                                                                         texte_fraction(c), texte_fraction(f))),
                (tr('anim_gravalgebra_force'), tr('anim_gravalgebra_fois', f=texte_fraction(f)))]

    def dessiner(self, p, rect):
        a, b, c = self.facteurs()
        f = facteur_force(a, b, c)
        cx, cy = rect.center().x(), rect.y() + rect.height() * 0.42
        unite = min(rect.width() / 7.5, rect.height() / 3.2)
        dist = unite * 1.4 * float(c)
        r1, r2 = unite * 0.32 * float(a) ** (1 / 3), unite * 0.32 * float(b) ** (1 / 3)
        x1, x2 = cx - dist / 2, cx + dist / 2
        p.setPen(dessin.stylo('grille', 1.0, pointille=True))
        p.drawLine(QPointF(x1, cy + unite * 0.75), QPointF(x2, cy + unite * 0.75))
        dessin.texte(p, cx, cy + unite * 0.75 + 12, 'd × %s' % texte_fraction(c), 'doux')
        # flèches de force (longueur ∝ facteur, bornée) : chacune attire l'autre
        lf = min(unite * 0.6 * float(f), dist / 2 - 4, unite * 2.2)
        if lf > 2:
            dessin.fleche(p, x1 + r1, cy, x1 + r1 + lf, cy, dessin.stylo('accent1', 3.0), 10)
            dessin.fleche(p, x2 - r2, cy, x2 - r2 - lf, cy, dessin.stylo('accent1', 3.0), 10)
        dessin.disque(p, x1, cy, r1, 'accent3')
        dessin.disque(p, x2, cy, r2, 'accent2')
        dessin.texte(p, x1, cy - r1 - 12, 'M₁ × %s' % texte_fraction(a), 'accent3')
        dessin.texte(p, x2, cy - r2 - 12, 'M₂ × %s' % texte_fraction(b), 'accent2')
        # la formule
        y = rect.y() + rect.height() * 0.80
        dessin.police(p, 1.5)
        tc = texte_fraction(c) if c.denominator == 1 else '(%s)' % texte_fraction(c)
        dessin.formule(p, cx, y - 8, 'F × (%s × %s) / %s² = F × %s' % (texte_fraction(a), texte_fraction(b), tc,
                                                                      texte_fraction(f)))
        dessin.police(p, 1 / 1.5)
        dessin.formule(p, cx, y + 34, 'F = G M₁ M₂ / d²', 'doux')
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(rect.x() + 10, y - 40, rect.width() - 20, 96), 8, 8)
