"""Interférences et interférométrie : deux télescopes séparés d'une base B recombinent la lumière d'une étoile et
donnent des franges d'interfrange λ / B, comme les fentes d'Young.  Leur contraste (la visibilité) baisse quand la
source est résolue : disque d'une étoile (premier zéro à B = 1,22 λ / θ, la mesure de Bételgeuse par Michelson et
Pease), couple serré.  Un interféromètre résout ainsi λ / B, bien plus fin que le 1,22 λ / d d'un télescope seul.
Second montage : les anneaux de Newton (lame d'air entre une lentille et une lame de verre).
Calculs : ``interferometrie.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import dessin, interferometrie as itf
from ..base import Animation, nombre
from ..graphe import Axes
from ..lumiere import couleur_longueur_onde
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
        self.montage = self.choix('montage', [('anim_interferometry_m_interferometre', 'interferometre'),
                                              ('anim_interferometry_m_anneaux', 'anneaux')], 'interferometre')
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
        self.rayon = self.curseur('rayon', 0.1, 20.0, 1.0, dec=2, unite='m', log=True)
        self.indice = self.curseur('indice', 1.0, 1.7, 1.0, dec=2)
        self.cote = self.choix('cote', [('anim_interferometry_c_reflexion', 'reflexion'),
                                        ('anim_interferometry_c_transmission', 'transmission')], 'reflexion')
        self.c_blanche = self.coche('blanche', False)
        self._instrument = self.instrument.currentData()
        self._objet = self.objet.currentData()
        self._blanc = None
        self.t = 0.0
        self.montage.currentIndexChanged.connect(self._reglages_utiles)
        self._reglages_utiles()

    def anneaux(self) -> bool:
        return self.montage.currentData() == 'anneaux'

    def _reglages_utiles(self, *_):
        """Chaque montage n'active que ses réglages (la longueur d'onde sert aux deux)."""
        a = self.anneaux()
        if getattr(self, '_montre', None) == a:
            return
        self._montre = a
        # réglages des anneaux masqués pour l'interféromètre ; ceux de l'interféromètre seulement grisés pour les
        # anneaux (masquer coûte une mise en page par réglage : trop lent pour douze)
        for w in (self.instrument, self.base, self.diametre, self.objet, self.taille, self.dmag, self.c_balayer,
                  self.c_enveloppe):
            w.setEnabled(not a)
        for w in (self.rayon, self.indice, self.cote._boite, self.c_blanche):
            w.setVisible(a)

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
        if self.c_balayer.isChecked() and not self.anneaux():
            b0, b1 = self.axe_bases()
            b = self.base.value() * 10 ** (0.12 * dt)
            self.base.setValue(b0 if b > b1 else b)

    def valeurs(self):
        if self.anneaux():
            return self._valeurs_anneaux()
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

    def _valeurs_anneaux(self):
        R, lam, n, cote = self.rayon.value(), self.lam.value(), self.indice.value(), self.cote.currentData()
        rs = [itf.rayon_sombre(k, R, lam, n, cote) for k in (1, 2, 3)]
        out = [(tr('anim_interferometry_v_anneaux'), tr('anim_interferometry_trois', a=nombre(rs[0], 3),
                                                        b=nombre(rs[1], 3), c=nombre(rs[2], 3))),
               (tr('anim_interferometry_v_ecart10'), tr('anim_interferometry_mm', x=nombre(
                   itf.rayon_sombre(10, R, lam, n, cote) - itf.rayon_sombre(9, R, lam, n, cote), 3))),
               (tr('anim_interferometry_v_centre'), tr('anim_interferometry_centre_' + cote)),
               (tr('anim_interferometry_v_lame'), tr('anim_interferometry_nm', x=nombre(
                   itf.epaisseur_nm(rs[0], R), 0)))]
        if self.c_blanche.isChecked():
            out.append((tr('anim_interferometry_v_blanche'), tr('anim_interferometry_teintes')))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        if self.anneaux():
            z = dessin.zones_principale(rect, 2, 0.5)
            self._anneaux(p, dessin.cadre(p, z[0], tr('anim_interferometry_t_anneaux')))
            self._lame(p, dessin.cadre(p, z[1], tr('anim_interferometry_t_lame')))
            self._profil(p, dessin.cadre(p, z[2], tr('anim_interferometry_t_profil')))
            return
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

    # ------------------------------------------------------------ anneaux de Newton
    N_BANDES = 160

    def _r_max(self) -> float:
        return itf.rayon_sombre(itf.N_ANNEAUX, self.rayon.value(), self.lam.value(), self.indice.value()) * 1.04

    def _couleurs(self):
        """Couleur de chaque bande radiale (du centre au bord)."""
        R, lam, n, cote = self.rayon.value(), self.lam.value(), self.indice.value(), self.cote.currentData()
        rmax = self._r_max()
        blanche = self.c_blanche.isChecked()
        cle = (R, lam, n, cote, blanche)
        if self._blanc is not None and self._blanc[0] == cle:
            return rmax, self._blanc[1]
        out = []
        base = couleur_longueur_onde(lam)
        for j in range(self.N_BANDES):
            r = rmax * (j + 0.5) / self.N_BANDES
            if blanche:
                out.append(itf.couleur_blanche(r, R, n, cote))
            else:
                i = itf.newton(r, R, lam, n, cote)
                out.append(tuple(int(round(c * i)) for c in base))
        self._blanc = (cle, out)
        return rmax, out

    def _anneaux(self, p, r):
        rmax, cols = self._couleurs()
        cx, cy = r.center().x(), r.center().y() + 6
        Rp = 0.46 * min(r.width(), r.height() - 24)
        p.save()
        p.setPen(dessin.Qt.PenStyle.NoPen)
        n = len(cols)
        for j in range(n - 1, -1, -1):
            p.setBrush(QColor(*cols[j]))
            rr = Rp * (j + 1) / n
            p.drawEllipse(QPointF(cx, cy), rr, rr)
        p.restore()
        # échelle : 1 mm
        mm = Rp / rmax
        y0 = r.bottom() - 14
        if mm < r.width() * 0.8:
            p.setPen(dessin.stylo('texte', 1.6))
            p.drawLine(QPointF(r.left() + 12, y0), QPointF(r.left() + 12 + mm, y0))
            dessin.texte(p, r.left() + 12 + mm / 2, y0 - 9, tr('anim_interferometry_mm', x='1'), 'texte',
                         fond=True)

    def _lame(self, p, r):
        """Coupe (courbure très exagérée) : lentille plan-convexe sur une lame, lame d'air, rayons réfléchis."""
        w, h = r.width(), r.height()
        x0, x1 = r.left() + 0.08 * w, r.right() - 0.08 * w
        xc = (x0 + x1) / 2.0
        ybas = r.top() + 0.66 * h                      # dessus de la lame de verre
        R_ecran = 1.6 * (x1 - x0)                      # rayon de courbure dessiné (exagéré)
        p.save()
        p.setPen(dessin.stylo('grille', 1.2))
        p.setBrush(dessin.c('equateur', 0.25))
        p.drawRect(QRectF(x0, ybas, x1 - x0, 0.14 * h))
        pts_x, pts_y = [], []
        m = 60
        for j in range(m + 1):
            x = x0 + (x1 - x0) * j / m
            pts_x.append(x)
            pts_y.append(ybas - (R_ecran - math.sqrt(R_ecran ** 2 - (x - xc) ** 2)))
        ytop = min(pts_y) - 0.22 * h
        poly_x = pts_x + [x1, x0]
        poly_y = pts_y + [ytop, ytop]
        p.drawPolygon(dessin.polygone(poly_x, poly_y))
        # rayons : un incident, deux réfléchis (sur le dessous de la lentille et sur la lame)
        for k, f in enumerate((0.22, 0.38)):
            x = xc + f * (x1 - xc)
            e = R_ecran - math.sqrt(R_ecran ** 2 - (x - xc) ** 2)
            p.setPen(dessin.stylo('accent1', 1.4))
            dessin.fleche(p, x, r.top() + 22, x, ybas - e - 1, dessin.stylo('accent1', 1.4), 5)
            dessin.fleche(p, x, ybas - e, x - 6, r.top() + 26, dessin.stylo('accent2', 1.2, 0.9), 5)
            dessin.fleche(p, x + 3, ybas, x + 9, r.top() + 26, dessin.stylo('accent3', 1.2, 0.9), 5)
        p.restore()
        dessin.texte(p, xc, ybas + 0.07 * h, tr('anim_interferometry_verre'), 'doux')
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_interferometry_legende_lame'), 'doux', centre=False,
                     fond=True)

    def _profil(self, p, r):
        R, lam, n, cote = self.rayon.value(), self.lam.value(), self.indice.value(), self.cote.currentData()
        rmax = self._r_max()
        ax = Axes(r, 0.0, rmax, 0.0, 1.08, marges=(40, 6, 8, 30)).avec(p)
        ax.fond(p, tr('anim_interferometry_axe_r'), tr('anim_interferometry_axe_i'))
        pts = [(rmax * j / 400.0, itf.newton(rmax * j / 400.0, R, lam, n, cote)) for j in range(401)]
        ax.courbe(pts, 'accent1', 1.6)
        for k in range(1, 4):
            ax.verticale(itf.rayon_sombre(k, R, lam, n, cote), 'accent3', 1.0, True, 'r%s' % '₁₂₃'[k - 1])
