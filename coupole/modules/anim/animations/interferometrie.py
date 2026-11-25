"""Interférences et interférométrie : deux télescopes séparés d'une base B recombinent la lumière d'une étoile et
donnent des franges d'interfrange λ / B, comme les fentes d'Young.  Leur contraste (la visibilité) baisse quand la
source est résolue : disque d'une étoile (premier zéro à B = 1,22 λ / θ, la mesure de Bételgeuse par Michelson et
Pease), couple serré.  Un interféromètre résout ainsi λ / B, bien plus fin que le 1,22 λ / d d'un télescope seul.
Calculs : ``interferometrie.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import dessin, interferometrie as itf
from ..base import Animation, nombre
from ..graphe import Axes
from .resolution import angle_sec

B_MIN, B_MAX = 0.0001, 1000.0          # bornes du curseur de base (m)
INCLINAISON = 0.2                      # inclinaison du front d'onde dans le schéma (radians, exagérée)


def angle_mas(x: float) -> str:
    """Angle donné en millisecondes d'arc, écrit en mas ou en secondes d'arc."""
    return angle_sec(x / 1000.0)


def longueur(b: float) -> str:
    """Base ou diamètre (m), en mm sous 1 cm."""
    if b < 0.01:
        return '%s mm' % nombre(b * 1000.0, 2 if b < 0.001 else 1)
    return '%s m' % nombre(b, 2 if b < 10 else (1 if b < 100 else 0))


class Interferometrie(Animation):
    ID = 'interferometry'

    def construire(self):
        self.instrument = self.choix('instrument', [('anim_interferometry_i_libre', 'libre')] +
                                     [('anim_interferometry_i_' + k, k) for k, _, _ in itf.INSTRUMENTS], 'vlti_ut')
        self.base = self.curseur('base', B_MIN, B_MAX, 130.0, dec=4, unite='m', log=True)
        self.diametre = self.curseur('diametre', 0.0001, 10.0, 8.2, dec=4, unite='m', log=True)
        self.lam = self.curseur('lambda', 350.0, 2400.0, 2200.0, dec=0, unite='nm')
        self.objet = self.choix('objet', [('anim_interferometry_o_' + k, k) for k, _, _, _ in itf.OBJETS], 'disque')
        self.taille = self.curseur('taille', 0.1, 100.0, 5.0, dec=1, unite='mas', log=True)
        self.dmag = self.curseur('dmag', 0.0, 5.0, 0.0, dec=1)
        self.c_balayer = self.coche('balayer', False)
        self.c_enveloppe = self.coche('enveloppe', True)
        self._instrument = self.instrument.currentData()
        self._objet = self.objet.currentData()
        self.t = 0.0

    def reglage_change(self):
        k = self.instrument.currentData()
        if k != getattr(self, '_instrument', k):
            self._instrument = k
            for cle, b, d in itf.INSTRUMENTS:
                if cle == k:
                    self.base.setValue(b)
                    self.diametre.setValue(d)
        o = self.objet.currentData()
        if o != getattr(self, '_objet', o):
            self._objet = o
            for cle, _, taille, dm in itf.OBJETS:
                if cle == o and cle != 'point':
                    self.taille.setValue(taille)
                    self.dmag.setValue(dm)
        super().reglage_change()

    # ------------------------------------------------------------ calculs
    def genre(self) -> str:
        return dict((k, g) for k, g, _, _ in itf.OBJETS)[self.objet.currentData()]

    def rapport(self) -> float:
        return 10 ** (-0.4 * self.dmag.value())

    def v(self) -> complex:
        return itf.visibilite_complexe(self.genre(), self.taille.value(), self.base.value(), self.lam.value(),
                                       self.rapport())

    def axe_bases(self) -> tuple[float, float]:
        """Bornes (m) de l'axe des bases du graphe de visibilité : autour du premier zéro ou minimum de la source."""
        b0 = itf.base_premier_zero(self.genre(), self.taille.value(), self.lam.value(), self.rapport())
        if b0 is None:
            return B_MIN, B_MAX
        return max(B_MIN, b0 / 30.0), min(B_MAX, b0 * 4.0)

    def avancer(self, dt):
        self.t += dt
        if self.c_balayer.isChecked():
            b0, b1 = self.axe_bases()
            b = self.base.value() * 10 ** (0.12 * dt)
            self.base.setValue(b0 if b > b1 else b)

    def valeurs(self):
        b, d, lam = self.base.value(), self.diametre.value(), self.lam.value()
        g, t = self.genre(), self.taille.value()
        v = self.v()
        out = [(tr('anim_interferometry_v_frange'), angle_mas(itf.interfrange_mas(b, lam))),
               (tr('anim_interferometry_v_un_telescope'), angle_mas(itf.resolution_mas(d, lam))),
               (tr('anim_interferometry_v_gain'), '× %s' % nombre(b / d, 1 if b / d < 100 else 0)),
               (tr('anim_interferometry_v_visibilite'), '%s (%s %%)' % (nombre(abs(v), 3), nombre(100 * abs(v), 0)))]
        if g == 'disque':
            out.append((tr('anim_interferometry_v_phase'), tr('anim_interferometry_retournees' if v.real < 0 else
                                                              'anim_interferometry_centrees')))
        elif g == 'couple':
            ph = math.degrees(-math.atan2(v.imag, v.real)) if abs(v) > 1e-12 else 0.0
            out.append((tr('anim_interferometry_v_phase'), tr('anim_interferometry_decalees', x=nombre(ph, 0))))
        b0 = itf.base_premier_zero(g, t, lam, self.rapport())
        if b0 is not None:
            out.append((tr('anim_interferometry_v_zero' if g == 'disque' else 'anim_interferometry_v_minimum'),
                        longueur(b0)))
        out.append((tr('anim_interferometry_v_verdict'),
                    tr('anim_interferometry_' + itf.verdict(g, t, d, lam, abs(v)))))
        if b < 0.01:
            out.append((tr('anim_interferometry_v_ecran'), '%s mm' % nombre(lam * 1e-6 / b, 2)))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.46)
        self._schema(p, dessin.cadre(p, z[0], tr('anim_interferometry_t_schema')))
        self._franges(p, dessin.cadre(p, z[1], tr('anim_interferometry_t_franges')))
        self._visibilite(p, dessin.cadre(p, z[2], tr('anim_interferometry_t_visibilite')))

    def _schema(self, p, r):
        """Deux télescopes, les fronts d'onde inclinés qui les atteignent avec un retard δ = B sin α, la recombinaison
        (schéma, angles exagérés)."""
        g = self.genre()
        w, h = r.width(), r.height()
        sol = r.bottom() - 0.30 * h
        x1, x2 = r.x() + 0.18 * w, r.right() - 0.18 * w
        demi_t = max(6.0, min(18.0, 0.05 * w))
        # fronts d'onde : droites perpendiculaires à la direction de l'étoile, qui descendent
        sources = [(INCLINAISON, 'accent1', False)]
        if g == 'couple':
            sources.append((INCLINAISON + 0.12, 'accent2', True))
        espace = 0.11 * h
        p.save()
        p.setClipRect(QRectF(r.x(), r.y() + 22, w, sol - r.y() - 22))
        for a, cle, pointille in sources:
            ux, uy = math.sin(a), math.cos(a)                     # direction de propagation (vers le bas : +y écran)
            phase = (self.t * 0.6) % 1.0
            for k in range(-2, 16):
                s = (k + phase) * espace                            # distance le long de la propagation
                # front : points X tels que (X − X0)·u = s, X0 = télescope de gauche remonté
                cx = x1 + ux * (s - 12 * espace)
                cy = sol + uy * (s - 12 * espace)
                lg = 1.4 * w
                p.setPen(dessin.stylo(cle, 1.4, 0.55, pointille=pointille))
                p.drawLine(QPointF(cx - uy * lg, cy + ux * lg), QPointF(cx + uy * lg, cy - ux * lg))
        p.restore()
        # retard δ : le front d'onde qui touche le télescope de gauche doit encore parcourir δ = B sin α pour
        # atteindre celui de droite
        a = INCLINAISON
        ux, uy = math.sin(a), math.cos(a)
        delta = (x2 - x1) * ux                                      # projection de la base sur la propagation
        pied = QPointF(x2 - ux * delta, sol - uy * delta)
        p.setPen(dessin.stylo('doux', 1.0, 0.8, pointille=True))
        p.drawLine(QPointF(x1, sol), pied)
        p.setPen(dessin.stylo('accent3', 2.2))
        p.drawLine(pied, QPointF(x2, sol))
        dessin.texte(p, pied.x() - 52, (pied.y() + sol) / 2, 'δ = B sin α', 'accent3', fond=True)
        # sol et télescopes
        p.setPen(dessin.stylo('grille', 1.5))
        p.drawLine(QPointF(r.x() + 8, sol), QPointF(r.right() - 8, sol))
        for x in (x1, x2):
            p.setPen(dessin.stylo('texte', 2.0))
            p.setBrush(dessin.c('sphere', 0.9))
            p.drawPolygon(dessin.polygone([x - demi_t, x + demi_t, x + demi_t * 0.45, x - demi_t * 0.45],
                                          [sol - 4, sol - 4, sol + 10, sol + 10]))
        # base
        yb = sol + 0.07 * h
        p.setPen(dessin.stylo('texte', 1.2))
        dessin.fleche(p, (x1 + x2) / 2, yb, x1, yb, dessin.stylo('texte', 1.2), 6)
        dessin.fleche(p, (x1 + x2) / 2, yb, x2, yb, dessin.stylo('texte', 1.2), 6)
        dessin.texte(p, (x1 + x2) / 2, yb - 9, 'B = ' + longueur(self.base.value()), 'texte', fond=True)
        # recombinaison : les deux faisceaux vers le centre
        yr = r.bottom() - 0.08 * h
        xc = (x1 + x2) / 2
        p.setPen(dessin.stylo('accent1', 1.4, 0.8))
        for x in (x1, x2):
            p.drawLine(QPointF(x, sol + 10), QPointF(x, yr))
            p.drawLine(QPointF(x, yr), QPointF(xc + (6 if x > xc else -6), yr))
        p.setPen(dessin.stylo('texte', 1.2))
        p.setBrush(dessin.c('sphere', 0.9))
        p.drawRect(QRectF(xc - 6, yr - 8, 12, 16))
        dessin.texte(p, xc, yr - 17, tr('anim_interferometry_recombinaison'), 'doux', fond=True)
        dessin.texte(p, r.x() + 14, r.y() + 34, tr('anim_interferometry_vers_etoile'), 'doux', centre=False)

    def _franges(self, p, r):
        b, d, lam = self.base.value(), self.diametre.value(), self.lam.value()
        v = self.v()
        xs, ys, demi = itf.coupe(b, d, lam, v)
        en_sec = demi >= 1000.0
        k = 1000.0 if en_sec else 1.0
        # bande : l'image des franges
        hb = max(14.0, min(40.0, 0.22 * r.height()))
        bande = QRectF(r.x() + 40, r.y() + 24, r.width() - 46, hb)
        p.save()
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0))
        p.drawRect(bande)
        n = len(xs)
        p.setRenderHint(p.RenderHint.Antialiasing, False)
        bords = [math.floor(bande.x() + i * bande.width() / n) for i in range(n + 1)]
        for i in range(n):
            a = max(0, min(255, int(255 * ys[i])))
            if a > 1:
                p.setBrush(QColor(255, 236, 190, a))
                p.drawRect(QRectF(bords[i], bande.y(), max(1, bords[i + 1] - bords[i]), bande.height()))
        p.setRenderHint(p.RenderHint.Antialiasing, True)
        p.restore()
        r2 = QRectF(r.x(), bande.bottom() + 2, r.width(), r.bottom() - bande.bottom() - 2)
        ax = Axes(r2, -demi / k, demi / k, 0.0, 1.08, marges=(40, 6, 8, 30)).avec(p)
        ax.fond(p, tr('anim_interferometry_axe_sec' if en_sec else 'anim_interferometry_axe_mas'),
                tr('anim_interferometry_axe_i'), fmt_x=lambda x: nombre(x, 0 if abs(demi / k) >= 20 else
                                                                         (1 if abs(demi / k) >= 2 else 2)))
        if self.c_enveloppe.isChecked():
            env = [2.0 * itf.intensite(x, b, d, lam, 0j) for x in xs]          # tache d'Airy d'une ouverture
            ax.courbe([(x / k, e) for x, e in zip(xs, env)], 'doux', 1.0, 0.7, pointille=True)
            for sg in (1.0, -1.0):
                ax.courbe([(x / k, 0.5 * e * (1.0 + sg * abs(v))) for x, e in zip(xs, env)], 'accent3', 1.0, 0.8,
                          pointille=True)
        ax.courbe([(x / k, y) for x, y in zip(xs, ys)], 'accent1', 1.8)

    def _visibilite(self, p, r):
        g, t, lam, rap = self.genre(), self.taille.value(), self.lam.value(), self.rapport()
        b0, b1 = self.axe_bases()
        ax = Axes(r, b0, b1, 0.0, 1.05, xlog=True, marges=(40, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_interferometry_axe_b'), tr('anim_interferometry_axe_v'))
        n = 300
        pts = []
        for i in range(n + 1):
            b = b0 * (b1 / b0) ** (i / n)
            pts.append((b, itf.visibilite(g, t, b, lam, rap)))
        ax.courbe(pts, 'accent2', 2.0)
        bz = itf.base_premier_zero(g, t, lam, rap)
        if bz is not None and b0 <= bz <= b1:
            ax.verticale(bz, 'doux', 1.0)
        b = self.base.value()
        if b0 <= b <= b1:
            vv = itf.visibilite(g, t, b, lam, rap)
            ax.verticale(b, 'accent3', 1.4, pointille=False)
            dessin.disque(p, ax.px(b), ax.py(vv), 4.5, 'accent3')
        else:
            dessin.texte(p, ax.r.right() - 18 if b > b1 else ax.r.left() + 18, ax.r.top() + 10,
                         ('B →' if b > b1 else '← B'), 'accent3', fond=True)
