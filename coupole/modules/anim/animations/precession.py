"""La précession des équinoxes : l'axe de la Terre décrit un cône en 25 772 ans ; le pôle céleste fait le tour du pôle
de l'écliptique et passe près de Thuban (−2800), de Polaris (2100), de Véga (vers 13 800) ; le point vernal recule
le long du zodiaque (Poissons, puis Verseau vers 2600).  Carte du ciel autour du pôle de l'écliptique, bande du
zodiaque, axe de la Terre.  Calculs : ``precession.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, precession as pr
from ..base import Animation, angle, nombre

ANS_PAR_SECONDE = 1000.0
AN_MIN, AN_MAX = -13000.0, 15000.0
RAYON_CARTE = 52.0               # degrés montrés autour du pôle de l'écliptique
ZODIAQUE = ('psc', 'ari', 'tau', 'gem', 'cnc', 'leo', 'vir', 'lib', 'sco', 'oph', 'sgr', 'cap', 'aqr')


def an(y: int) -> str:
    return ('%d' % y).replace('-', '−')


def annee_texte(y: float) -> str:
    y = int(round(y))
    if y <= 0:
        return tr('anim_precession_av_jc', a=an(y), b=an(1 - y))
    return an(y)


def nom_etoile(n: str) -> str:
    k = pr.NOMS.get(n)
    return '%s (%s)' % (tr('anim_precession_e_' + k), n) if k else n


class Precession(Animation):
    ID = 'precession'

    def construire(self):
        self.annee = self.curseur('annee', AN_MIN, AN_MAX, 2026.0, dec=0)
        self.c_noms = self.coche('noms', True)
        self.c_dates = self.coche('dates', True)

    def avancer(self, dt):
        y = self.annee.value() + dt * ANS_PAR_SECONDE
        if y > AN_MAX:
            y = AN_MIN + (y - AN_MAX)
        self.annee.setValue(y)

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        y = self.annee.value()
        n, d = pr.plus_proche(y)
        vp = pr.point_vernal(y)
        cst = pr.constellation(vp)
        i = ZODIAQUE.index(cst)
        suivante = ZODIAQUE[(i - 1) % len(ZODIAQUE)]
        y_suiv = pr.annee_entree(suivante, y)
        decal = -pr.P_DEG_AN * (y - 2000.0)
        return [(tr('anim_precession_v_annee'), annee_texte(y)),
                (tr('anim_precession_v_periode'), tr('anim_precession_periode', p=nombre(pr.PERIODE_ANS, 0),
                                                     v=nombre(pr.P_ARCSEC_SIECLE / 100.0, 2))),
                (tr('anim_precession_v_decalage'), angle(decal, 2)),
                (tr('anim_precession_v_polaire'), tr('anim_precession_a', e=nom_etoile(n), d=angle(d, 2))),
                (tr('anim_precession_v_polaris'), angle(pr.distance_au_pole('α UMi', y), 2)),
                (tr('anim_precession_v_vega'), angle(pr.declinaison('α Lyr', y), 1)),
                (tr('anim_precession_v_equinoxe'), tr('anim_cst_' + cst)),
                (tr('anim_precession_v_suivante'), tr('anim_precession_vers', c=tr('anim_cst_' + suivante),
                                                      a=annee_texte(y_suiv)))]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.56)
        self._carte(p, dessin.cadre(p, z[0], tr('anim_precession_t_carte')))
        self._zodiaque(p, dessin.cadre(p, z[1], tr('anim_precession_t_zodiaque')))
        self._terre(p, dessin.cadre(p, z[2], tr('anim_precession_t_terre')))

    def _carte(self, p, r):
        R = 0.47 * min(r.width(), r.height() - 8)
        cx, cy = r.center().x(), r.center().y() + 4

        def pt(lam, beta):
            rr = (90.0 - beta) / RAYON_CARTE * R
            a = math.radians(lam)
            return QPointF(cx + rr * math.cos(a), cy - rr * math.sin(a))
        p.save()
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.c('nuit', 0.5))
        p.drawEllipse(QPointF(cx, cy), R, R)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        rp = pr.EPS / RAYON_CARTE * R
        p.setPen(dessin.stylo('accent2', 1.2, 0.8, pointille=True))
        p.drawEllipse(QPointF(cx, cy), rp, rp)
        dessin.etiquette(p, cx, cy, tr('anim_precession_pole_ecl'), 'doux')
        dessin.disque(p, cx, cy, 2.5, 'doux')
        if self.c_dates.isChecked():
            for y in range(-10000, 14001, 2000):
                q = pt(*pr.pole(y))
                dessin.disque(p, q.x(), q.y(), 2.2, 'accent2')
                dessin.texte(p, q.x() + (q.x() - cx) * 0.11, q.y() + (q.y() - cy) * 0.11, an(y), 'accent2')
        y = self.annee.value()
        vp = pr.vecteur(*pr.pole(y))
        for n, l, b, m in pr.etoiles_ecliptiques():
            if 90.0 - b > RAYON_CARTE:
                continue
            q = pt(l, b)
            dessin.disque(p, q.x(), q.y(), max(1.2, 4.2 - 0.9 * m), 'etoile')
            if self.c_noms.isChecked() and n in pr.NOMS and pr.ecart(pr.vecteur(l, b), vp) > 4.0:
                dessin.etiquette(p, q.x(), q.y(), tr('anim_precession_e_' + pr.NOMS[n]), 'texte')
        q = pt(*pr.pole(y))
        r10 = 10.0 / RAYON_CARTE * R
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('accent3', 1.0, 0.7, pointille=True))
        p.drawEllipse(q, r10, r10)
        p.setPen(dessin.stylo('accent3', 2.0))
        p.drawLine(QPointF(q.x() - 7, q.y()), QPointF(q.x() + 7, q.y()))
        p.drawLine(QPointF(q.x(), q.y() - 7), QPointF(q.x(), q.y() + 7))
        dessin.etiquette(p, q.x(), q.y(), tr('anim_precession_pole'), 'accent3')
        p.restore()
        if r.height() > 330:
            dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_precession_legende_carte'), 'doux', centre=False,
                         fond=True)

    def _zodiaque(self, p, r):
        x0, x1 = r.left() + 10, r.right() - 10
        W = x1 - x0
        xc = (x0 + x1) / 2.0
        yb = r.center().y() + 6
        h = min(34.0, r.height() * 0.3)
        vp = pr.point_vernal(self.annee.value())       # au milieu ; longitudes croissantes vers la gauche (ciel)
        p.save()
        lims = sorted(pr.LIMITES_2026, key=lambda x: x[1])
        for k, (cle, l0) in enumerate(lims):
            l1 = lims[(k + 1) % len(lims)][1]
            a0 = (l0 - pr.P_DEG_AN * 26.0) % 360.0
            larg = (l1 - l0) % 360.0
            rel = (a0 - vp + 180.0) % 360.0 - 180.0
            xa = xc - rel / 360.0 * W
            xb = xa - larg / 360.0 * W
            p.setPen(dessin.stylo('grille', 1.0))
            p.setBrush(dessin.c('sphere', 0.5 if k % 2 else 0.25))
            for d in (-W, 0.0, W):
                g, dr = max(xb + d, x0), min(xa + d, x1)
                if dr - g > 0:
                    rr = QRectF(g, yb - h / 2.0, dr - g, h)
                    p.drawRect(rr)
                    if rr.width() > 26:
                        dessin.texte(p, rr.center().x(), yb, cle.capitalize(), 'doux')
        p.setPen(dessin.stylo('accent3', 2.2))
        p.drawLine(QPointF(xc, yb - h / 2.0 - 10), QPointF(xc, yb + h / 2.0 + 4))
        dessin.texte(p, xc, yb - h / 2.0 - 18, tr('anim_precession_gamma'), 'accent3', fond=True)
        p.restore()
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_precession_legende_zodiaque'), 'doux', centre=False,
                     fond=True)

    def _terre(self, p, r):
        y = self.annee.value()
        lam_p = math.radians(pr.pole(y)[0] - 90.0)          # le pôle de 2000 à droite
        eps = math.radians(pr.EPS)
        R = 0.22 * min(r.width(), r.height())
        cx, cy = r.center().x(), r.center().y() + 0.12 * r.height()
        incl = math.radians(25.0)                             # on regarde un peu d'au-dessus

        def proj(x, y_, z):
            return QPointF(cx + R * x, cy - R * (z * math.cos(incl) - y_ * math.sin(incl)))
        L = 2.0
        p.save()
        p.setPen(dessin.stylo('doux', 1.0, 0.8, pointille=True))
        p.drawLine(proj(0, 0, -1.6), proj(0, 0, L + 0.3))
        dessin.texte(p, proj(0, 0, L + 0.45).x(), proj(0, 0, L + 0.45).y(), tr('anim_precession_normale'), 'doux')
        # cercle décrit par le bout de l'axe
        pts = [proj(L * math.sin(eps) * math.cos(t / 60 * 2 * math.pi), L * math.sin(eps) * math.sin(t / 60 * 2 * math.pi),
                    L * math.cos(eps)) for t in range(61)]
        p.setPen(dessin.stylo('accent2', 1.2, 0.8, pointille=True))
        for a, b in zip(pts[:-1], pts[1:]):
            p.drawLine(a, b)
        dessin.disque(p, cx, cy, R, 'terre')
        tip = proj(L * math.sin(eps) * math.cos(lam_p), L * math.sin(eps) * math.sin(lam_p), L * math.cos(eps))
        bas = proj(-L * 0.8 * math.sin(eps) * math.cos(lam_p), -L * 0.8 * math.sin(eps) * math.sin(lam_p),
                   -L * 0.8 * math.cos(eps))
        p.setPen(dessin.stylo('accent3', 2.2))
        p.drawLine(bas, tip)
        dessin.etiquette(p, tip.x(), tip.y(), tr('anim_precession_axe'), 'accent3')
        p.restore()
