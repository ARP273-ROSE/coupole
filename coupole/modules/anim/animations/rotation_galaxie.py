"""Milky Way Rotational Velocity : vitesse de rotation de la Voie lactée selon la distance au centre, et masse
contenue dans le cercle de rayon R.  La courbe reste presque plate loin du centre, là où l'on ne voit presque plus
d'étoiles : si toute la masse était au centre, v décroîtrait comme 1/√R (courbe képlérienne).  C'est un indice de
matière noire.

Courbe d'un modèle de masse publié, lisse et physique : McMillan (2017, arXiv:1608.00971 ; bulbe, disques d'étoiles
mince et épais, gaz HI et H2, halo NFW de matière noire), calculé avec galpy, total et par composante ; mesures
réelles avec barres d'erreur : Eilers et al. (2019, ApJ 871, 120, table 1) de 5 à 25 kpc, compilation galkin (Pato &
Iocco 2017) de 2 à 5 kpc.  La courbe képlérienne part de la masse que le modèle contient dans la sphère de rayon R.
Galaxie vue du pôle Nord galactique, à l'échelle : bras spiraux log-périodiques de Reid et al. (2019, table 2), barre
longue de Wegg et al. (2015).  Mêmes données et mêmes choix que Coupole Web (src/anim/animations/rotation_galaxie.ts).
Données : donnees/voie_lactee.json.gz (outils/verif_anim/voie_lactee.py, vérifié par voie_lactee_verif.sage)."""
from __future__ import annotations

import bisect
import functools
import gzip
import json
import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QBrush, QRadialGradient

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre
from ..graphe import Axes
from .gravitation import scientifique

KPC_M = astro.PC_M * 1000.0
G_KPC = astro.GM_SOLEIL / (KPC_M * 1e6)          # G en kpc (km/s)² / M☉ : 4,3009 × 10⁻⁶
R_MAX = 25.0


@functools.lru_cache(maxsize=1)
def donnees() -> dict:
    return json.loads(gzip.decompress((Path(__file__).resolve().parents[1] / 'donnees' / 'voie_lactee.json.gz')
                                      .read_bytes()))


R_SOLEIL_KPC = donnees()['R0']                    # distance du Soleil au centre du modèle de McMillan (2017)


def _interpoler(xs, ys, x: float) -> float:
    if x <= xs[0]:
        return ys[0] * (x / xs[0])
    if x >= xs[-1]:
        return ys[-1]
    i = bisect.bisect_right(xs, x)
    t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
    return ys[i - 1] + t * (ys[i] - ys[i - 1])


def vitesse(r: float, cle: str = 'v') -> float:
    """Vitesse circulaire du modèle (km/s) à r kpc du centre ; `cle` : 'v' (total), 'bulbe', 'disques' ou 'halo'."""
    m = donnees()['modele']
    return _interpoler(m['R'], m[cle], r)


def masse_sphere(r: float) -> float:
    """Masse (M☉) que le modèle contient dans la sphère de rayon r kpc (interpolée en log au-delà de 0,5 kpc)."""
    m = donnees()['modele']
    if r <= m['Rm'][0]:
        return m['M'][0] * (r / m['Rm'][0]) ** 2
    if r >= m['Rm'][-1]:
        return m['M'][-1]
    return math.exp(_interpoler(m['Rm'], [math.log(x) for x in m['M']], r))


def masse(r: float) -> float:
    """Masse « dynamique » (M☉) : v² r / G."""
    return vitesse(r) ** 2 * r / G_KPC


# Bras de Reid et al. (2019), table 2 : nom, β_kink (°), R_kink (kpc), ψ< (°), ψ> (°), largeur (kpc), β tracé (°) ;
# Reid et al. ont adopté R0 = 8,15 kpc pour les bras, tracés tels quels (écart de 0,06 kpc)
BRAS = (('norma', 18, 4.46, -1.0, 19.5, 0.14, -25, 54), ('outer', 18, 12.24, 3.0, 9.4, 0.65, -40, 110),
        ('sctcen', 23, 4.91, 14.1, 12.1, 0.23, -110, 104), ('sgrcar', 24, 6.04, 17.1, 1.0, 0.27, -130, 97),
        ('perseus', 40, 8.87, 10.3, 8.7, 0.35, -60, 160), ('local', 9, 8.26, 11.4, 11.4, 0.31, -8, 34),
        ('3kpc', 15, 3.52, -4.2, -4.2, 0.18, 15, 18))
COULEURS_BRAS = {'norma': 'arc2', 'outer': 'arc2', 'sctcen': 'accent2', 'sgrcar': 'arc1', 'perseus': 'equateur',
                 'local': 'accent1', '3kpc': 'accent3'}
# barre longue (Wegg et al. 2015) : demi-longueur 5,0 kpc, angle à la ligne de visée 28 à 33° (milieu : 30,5°)
BARRE_DEMI = 5.0
BARRE_ANGLE = 30.5


def point_bras(b, beta: float):
    """Point d'un bras (centre à l'origine, Soleil sur +y, l = 90° vers +x), en kpc : spirale log-périodique
    ln(R/R_kink) = −(β − β_kink) tan ψ."""
    _, bk, rk, p1, p2 = b[:5]
    psi = p1 if beta <= bk else p2
    r = rk * math.exp(-(beta - bk) * math.pi / 180 * math.tan(math.radians(psi)))
    a = math.radians(beta)
    return r * math.sin(a), r * math.cos(a)


class RotationGalaxie(Animation):
    ID = 'milkywayrotationalvelocity'
    ANIMEE = False

    def construire(self):
        self.r = self.curseur('rayon', 0.5, R_MAX, R_SOLEIL_KPC, dec=2, unite='kpc')
        self.c_kepler = self.coche('kepler', True)
        self.c_composantes = self.coche('composantes', True)
        self.c_mesures = self.coche('mesures', True)
        self._axes = None

    def valeurs(self):
        r = self.r.value()
        tour = 2 * math.pi * r * KPC_M / (vitesse(r) * 1000) / (astro.ANNEE_JULIENNE_J * 86400) / 1e6
        return [(tr('anim_milkywayrotationalvelocity_r'), '%s kpc (%s %s)' % (
                    nombre(r, 2), nombre(r * 1000 * astro.PC_EN_AL, 0), tr('anim_spectroparallax_al'))),
                (tr('anim_milkywayrotationalvelocity_v'), '%s km/s' % nombre(vitesse(r), 1)),
                (tr('anim_milkywayrotationalvelocity_m'), '%s M☉' % scientifique(masse(r))),
                (tr('anim_milkywayrotationalvelocity_masse_sphere'), '%s M☉' % scientifique(masse_sphere(r))),
                (tr('anim_milkywayrotationalvelocity_tour'), '%s %s' % (nombre(tour, 0),
                                                                         tr('anim_milkywayrotationalvelocity_ma')))]

    def presser(self, pos, bouton):
        if self._axes is not None and self._axes.r.adjusted(-10, -10, 10, 10).contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        self.r.setValue(self._axes.x_de_px(pos.x()))

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.56)
        self._courbe(p, dessin.cadre(p, z[0], tr('anim_milkywayrotationalvelocity_titre_courbe')))
        self._galaxie(p, dessin.cadre(p, z[1], tr('anim_milkywayrotationalvelocity_titre_galaxie')))

    def _courbe(self, p, r):
        d = donnees()
        m = d['modele']
        ax = Axes(r, 0, R_MAX, 0, 300, marges=(46, 10, 12, 30)).avec(p)
        self._axes = ax
        ax.fond(p, tr('anim_milkywayrotationalvelocity_axe_r'), tr('anim_milkywayrotationalvelocity_axe_v'))

        def serie(cle):
            return list(zip(m['R'], m[cle]))
        if self.c_composantes.isChecked():
            ax.courbe(serie('bulbe'), 'accent3', 1.2, 0.8, True)
            ax.courbe(serie('disques'), 'equateur', 1.2, 0.8, True)
            ax.courbe(serie('halo'), 'arc1', 1.2, 0.8, True)
        ax.courbe([(0.0, 0.0)] + serie('v'), 'accent1', 2.6)
        if self.c_mesures.isChecked():
            def barre(x, v, bas, haut, cle):
                p.setPen(dessin.stylo(cle, 1.0, 0.85))
                p.drawLine(QPointF(ax.px(x), ax.py(v - bas)), QPointF(ax.px(x), ax.py(v + haut)))
                p.setPen(dessin.Qt.PenStyle.NoPen)
                p.setBrush(dessin.c(cle))                # points de mesure : pas des obstacles pour les étiquettes
                p.drawEllipse(QPointF(ax.px(x), ax.py(v)), 2.6, 2.6)
            for x, v, e, _ in d['galkin']:
                barre(x, v, e, e, 'accent2')
            for x, v, em, ep in d['eilers']:
                barre(x, v, em, ep, 'texte')
        rr = self.r.value()
        if self.c_kepler.isChecked():
            # la masse contenue dans la sphère de rayon R, supposée toute au centre : v = √(G M / r)
            mm = masse_sphere(rr)
            n = int((R_MAX - rr) / 0.1) + 1
            kep = [(rr + 0.1 * i, math.sqrt(G_KPC * mm / (rr + 0.1 * i))) for i in range(n)]
            ax.courbe(kep, 'accent2', 1.6, 0.9, True)
            s_ = tr('anim_milkywayrotationalvelocity_k')
            dessin.texte(p, ax.px(R_MAX) - 4 - p.fontMetrics().horizontalAdvance(s_),
                         ax.py(math.sqrt(G_KPC * mm / R_MAX)) + 14, s_, 'accent2', centre=False)
        ax.verticale(R_SOLEIL_KPC, 'doux', 1.0, True, tr('anim_milkywayrotationalvelocity_soleil'))
        ax.verticale(rr, 'accent3', 1.2, True)
        ax.points([(rr, vitesse(rr))], 'accent3', 6, 1.0)
        # légende (pas sur les petits panneaux : elle cacherait les courbes)
        if ax.r.width() < 420 or ax.r.height() < 240:
            return
        dessin.police(p, 0.8)
        leg = [('accent1', tr('anim_milkywayrotationalvelocity_modele'), True)]
        if self.c_composantes.isChecked():
            leg += [('accent3', tr('anim_milkywayrotationalvelocity_bulbe'), True),
                    ('equateur', tr('anim_milkywayrotationalvelocity_disques'), True),
                    ('arc1', tr('anim_milkywayrotationalvelocity_halo'), True)]
        if self.c_mesures.isChecked():
            leg += [('texte', tr('anim_milkywayrotationalvelocity_eilers'), False),
                    ('accent2', tr('anim_milkywayrotationalvelocity_galkin'), False)]
        y = ax.r.bottom() - 10 - 13 * (len(leg) - 1)
        x = ax.r.left() + ax.r.width() * 0.45
        for cle, nom, ligne in leg:
            if ligne:
                p.setPen(dessin.stylo(cle, 2.0))
                p.drawLine(QPointF(x, y - 4), QPointF(x + 16, y - 4))
            else:
                dessin.disque(p, x + 8, y - 4, 2.6, cle)
            dessin.texte(p, x + 22, y, nom, 'doux', centre=False)
            y += 13
        dessin.police(p, 1 / 0.8)

    def _galaxie(self, p, r):
        """Galaxie vue du pôle Nord galactique, à l'échelle (disque de 25 kpc), Soleil en haut, l = 90° à droite."""
        cx, cy = r.center().x(), r.center().y()
        k = min(r.width(), r.height()) * 0.48 / R_MAX
        if not k > 0.5:
            return

        def ecran(x, y):
            return QPointF(cx + x * k, cy - y * k)

        etiquettes = self._fond_galaxie(p, r, cx, cy, k)
        # centre, Soleil, cercle du rayon choisi
        dessin.disque(p, cx, cy, 3, 'texte')
        rr = self.r.value()
        p.setPen(dessin.stylo('accent3', 1.6, None, True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), rr * k, rr * k)
        s = ecran(0, R_SOLEIL_KPC)
        dessin.disque(p, s.x(), s.y(), 5, 'soleil', bord='texte')
        # sens de rotation : horaire vu du pôle Nord galactique (le Soleil va vers l = 90°)
        dessin.fleche(p, s.x() + 9, s.y(), s.x() + 34, s.y() + 4, dessin.stylo('soleil', 1.6), 7)
        dessin.police(p, 0.8)
        for q, cle, nom in etiquettes:
            dessin.etiquette(p, q.x(), q.y(), nom, cle, 4)
        dessin.etiquette(p, s.x(), s.y(), tr('anim_milkywayrotationalvelocity_soleil'), 'soleil', 7)
        a = math.radians(BARRE_ANGLE)
        bq = ecran(-BARRE_DEMI * 0.8 * math.sin(a), -BARRE_DEMI * 0.8 * math.cos(a))
        dessin.etiquette(p, bq.x(), bq.y(), tr('anim_milkywayrotationalvelocity_barre'), 'doux', 4)
        for d_ in range(10, 26, 5):
            dessin.texte(p, cx + d_ * k * math.cos(-0.6), cy - d_ * k * math.sin(-0.6) + 10, '%d kpc' % d_, 'doux')
        dessin.police(p, 1 / 0.8)

    def _fond_galaxie(self, p, r, cx, cy, k):
        """Disque, anneaux, barre et bras : statiques, rendus une fois par taille dans une image (rendu rapide)."""
        from PyQt6.QtGui import QImage, QPainter
        dpr = 1.0
        try:
            dpr = max(1.0, float(p.device().devicePixelRatioF()))
        except Exception:
            pass
        cle = (round(r.width()), round(r.height()), round(k, 5), dessin.theme(), dpr, tr('anim_milkywayrotationalvelocity_bras_outer'))
        if getattr(self, '_cache_galaxie', (None,))[0] != cle:
            img = QImage(max(1, int(r.width() * dpr)), max(1, int(r.height() * dpr)),
                         QImage.Format.Format_ARGB32_Premultiplied)
            img.setDevicePixelRatio(dpr)
            img.fill(0)
            q = QPainter(img)
            q.setRenderHint(QPainter.RenderHint.Antialiasing)
            ox, oy = r.x(), r.y()
            q.translate(-ox, -oy)
            etiquettes = self._dessiner_fond(q, cx, cy, k)
            q.end()
            self._cache_galaxie = (cle, img, etiquettes)
        _, img, etiquettes = self._cache_galaxie
        p.drawImage(QPointF(r.x(), r.y()), img)
        return etiquettes

    def _dessiner_fond(self, p, cx, cy, k):
        def ecran(x, y):
            return QPointF(cx + x * k, cy - y * k)

        # disque : lueur exponentielle (longueur d'échelle du disque mince, 2,5 kpc), anneaux tous les 5 kpc
        g = QRadialGradient(QPointF(cx, cy), R_MAX * k)
        for t in (0, 0.08, 0.16, 0.3, 0.5, 0.75, 1):
            g.setColorAt(t, dessin.c('soleil', 0.5 * math.exp(-t * R_MAX / 2.5 / 2.2)))
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R_MAX * k, R_MAX * k)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for a in range(5, 26, 5):
            p.setPen(dessin.stylo('grille', 0.7, 0.6))
            p.drawEllipse(QPointF(cx, cy), a * k, a * k)
        # barre (épaisseur schématique) ; l'extrémité proche est du côté l > 0
        p.save()
        p.translate(cx, cy)
        p.rotate(-(90 - BARRE_ANGLE))
        gb = QRadialGradient(QPointF(0, 0), BARRE_DEMI * k)
        gb.setColorAt(0, dessin.c('soleil', 0.75))
        gb.setColorAt(1, dessin.c('soleil', 0.15))
        p.setBrush(QBrush(gb))
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(0, 0), BARRE_DEMI * k, BARRE_DEMI * k * 0.3)
        p.restore()
        # bras spiraux, avec leur largeur (1 σ de Reid et al.)
        etiquettes = []
        for b in BRAS:
            nom, larg, b0, b1 = b[0], b[5], b[6], b[7]
            cle = COULEURS_BRAS[nom]

            def trace(de, a):
                pts = []
                pas = 1 if de <= a else -1
                beta = de
                while (beta <= a) if pas > 0 else (beta >= a):
                    x, y = point_bras(b, beta)
                    if not 2.8 <= math.hypot(x, y) <= 17:
                        break
                    pts.append(ecran(x, y))
                    beta += pas
                return pts
            # partie mesurée (plage d'azimut des masers), puis prolongements estompés de part et d'autre
            mesure = trace(b0, b1)
            if len(mesure) < 2:
                continue
            prolong = [] if nom in ('3kpc', 'local') else [trace(b0, b0 - 200), trace(b1, b1 + 200)]
            for pts in prolong:
                if len(pts) < 2:
                    continue
                p.setPen(dessin.stylo(cle, max(2.5, 4 * larg * k), 0.14))
                p.drawPolyline(pts)
                p.setPen(dessin.stylo(cle, 1.0, 0.45, True))
                p.drawPolyline(pts)
            p.setPen(dessin.stylo(cle, max(2.5, 4 * larg * k), 0.32))
            p.drawPolyline(mesure)
            p.setPen(dessin.stylo(cle, 1.4, 0.95))
            p.drawPolyline(mesure)
            etiquettes.append((mesure[int(len(mesure) * 0.62)], cle, tr('anim_milkywayrotationalvelocity_bras_' + nom)))
        return etiquettes
