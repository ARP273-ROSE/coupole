"""Three Views Spectrum Demonstrator : les trois lois de Kirchhoff.  Une ampoule (corps chaud et dense) et un nuage
de gaz froid et peu dense ; selon l'endroit d'où le télescope regarde : l'ampoule seule donne un spectre continu,
le gaz seul un spectre de raies d'émission, l'ampoule vue à travers le gaz un spectre continu creusé de raies
d'absorption, aux mêmes longueurs d'onde.  On fait glisser le télescope tout autour (l'original le limitait à trois
positions) ; raies réelles du gaz choisi (longueurs d'onde dans l'air)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre
from ..graphe import bande_spectre

# principales raies visibles (nm, dans l'air) ; toutes dessinées avec la même intensité
GAZ = {'hydrogene': (656.28, 486.13, 434.05, 410.17, 397.01),
       'helium': (706.52, 667.82, 587.56, 501.57, 492.19, 471.31, 447.15, 388.86),
       'sodium': (588.995, 589.592),
       'mercure': (579.07, 576.96, 546.07, 435.83, 404.66)}
NUAGE = (0.0, 0.0, 1.0)              # x, y, rayon (unités de la scène)
AMPOULE = (3.2, 0.0, 0.55)
# rayon du cercle où se déplace le télescope : hors du halo de l'ampoule (3,2 + 2,2 × 0,55 = 4,41), tube compris
R_TELESCOPE = 5.6
L_TUBE = 0.9                         # longueur du tube du télescope
R_HALO = 2.2 * AMPOULE[2]            # rayon du halo de l'ampoule


def _entree(obj, tx: float, ty: float, dx: float, dy: float):
    """Distance s (≥ 0) le long de la visée (origine t, direction unitaire d) où elle entre dans le disque, ou None."""
    ox, oy, r = obj
    fx, fy = tx - ox, ty - oy
    b = fx * dx + fy * dy
    disc = b * b - (fx * fx + fy * fy - r * r)
    if disc <= 0:
        return None
    q = math.sqrt(disc)
    if -b + q <= 0:                  # tout le disque est derrière le télescope
        return None
    return max(0.0, -b - q)


def vue(angle_deg: float, cible: str) -> dict:
    """Ce que voit le télescope placé à l'angle donné sur le cercle (autour du nuage) et visant `cible`
    ('nuage' ou 'ampoule').  L'ordre le long de la visée compte : l'ampoule est opaque et cache ce qui est derrière
    elle.  Absorption seulement si la visée traverse le gaz PUIS l'ampoule (télescope → nuage → ampoule) ; l'ampoule
    devant le nuage donne un spectre continu.  Rend {'nuage': gaz vu (traversé avant l'ampoule ou sans elle),
    'ampoule': ampoule sur la visée, 's_nuage', 's_ampoule': distances d'entrée le long de la visée ou None}."""
    a = math.radians(angle_deg)
    tx, ty = R_TELESCOPE * math.cos(a), R_TELESCOPE * math.sin(a)
    cx, cy = (NUAGE if cible == 'nuage' else AMPOULE)[:2]
    dx, dy = cx - tx, cy - ty
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    sa = _entree(AMPOULE, tx, ty, dx, dy)
    sn = _entree(NUAGE, tx, ty, dx, dy)
    return {'nuage': sn is not None and (sa is None or sn < sa), 'ampoule': sa is not None,
            's_nuage': sn, 's_ampoule': sa}


def type_de_spectre(v: dict) -> str:
    if v['ampoule'] and v['nuage']:
        return 'absorption'
    if v['ampoule']:
        return 'continu'
    if v['nuage']:
        return 'emission'
    return 'rien'


class Kirchhoff(Animation):
    ID = 'threeviewsspectra'
    ANIMEE = False

    def construire(self):
        self.angle = self.curseur('position', 0.0, 360.0, 180.0, dec=0, unite='°')
        self.cible = self.choix('cible', [('anim_threeviewsspectra_v_nuage', 'nuage'),
                                          ('anim_threeviewsspectra_v_ampoule', 'ampoule')], 'nuage')
        self.gaz = self.choix('gaz', [('anim_threeviewsspectra_g_' + g, g) for g in GAZ], 'hydrogene')
        self._scene = None

    def spectre(self) -> str:
        return type_de_spectre(vue(self.angle.value(), self.cible.currentData()))

    def valeurs(self):
        return [(tr('anim_threeviewsspectra_spectre'), tr('anim_threeviewsspectra_s_' + self.spectre())),
                (tr('anim_threeviewsspectra_loi'), tr('anim_threeviewsspectra_l_' + self.spectre()))]

    def presser(self, pos, bouton):
        if self._scene is not None:
            cx, cy, k = self._scene
            if math.hypot(pos.x() - cx, pos.y() - cy) > 1.5 * k:
                self._glisse = self._tirer
                self._tirer(pos)
                return True
        return False

    def _tirer(self, pos):
        cx, cy, k = self._scene
        self.angle.setValue(math.degrees(math.atan2(-(pos.y() - cy), pos.x() - cx)) % 360.0)

    def dessiner(self, p, rect):
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.68)
        r = dessin.cadre(p, haut, tr('anim_threeviewsspectra_titre_scene'))
        # le cercle du télescope (rayon 5,6) et son étiquette tiennent dans le panneau
        k = min(r.width() / 13.4, r.height() / 12.6)
        cx, cy = r.center().x(), r.center().y()
        self._scene = (cx, cy, k)
        p.setPen(dessin.stylo('grille', 1.0, None, True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), R_TELESCOPE * k, R_TELESCOPE * k)
        # ampoule : halo chaud
        ax_, ay_ = cx + AMPOULE[0] * k, cy - AMPOULE[1] * k
        for f, a in ((R_HALO / AMPOULE[2], 0.08), (1.6, 0.15)):
            dessin.disque(p, ax_, ay_, AMPOULE[2] * k * f, 'soleil', alpha=a)
        dessin.reserver(p, ax_, ay_, R_HALO * k, toujours=True)
        dessin.disque(p, ax_, ay_, AMPOULE[2] * k, 'soleil', bord='texte')
        dessin.texte(p, ax_, ay_ + AMPOULE[2] * k + 14, tr('anim_threeviewsspectra_ampoule'), 'doux')
        # nuage de gaz
        dessin.disque(p, cx, cy, NUAGE[2] * k, 'equateur', alpha=0.28)
        p.setPen(dessin.stylo('equateur', 1.0, None, True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), NUAGE[2] * k, NUAGE[2] * k)
        dessin.texte(p, cx, cy + NUAGE[2] * k + 14, tr('anim_threeviewsspectra_nuage'), 'doux')
        # télescope et ligne de visée
        a = math.radians(self.angle.value())
        tx, ty = cx + R_TELESCOPE * k * math.cos(a), cy - R_TELESCOPE * k * math.sin(a)
        cible = NUAGE if self.cible.currentData() == 'nuage' else AMPOULE
        gx, gy = cx + cible[0] * k, cy - cible[1] * k
        d = math.hypot(gx - tx, gy - ty)
        ux, uy = (gx - tx) / d, (gy - ty) / d
        # la visée s'arrête sur l'ampoule, opaque : ce qui est derrière elle n'est pas vu
        v = vue(self.angle.value(), self.cible.currentData())
        portee = v['s_ampoule'] * k if v['s_ampoule'] is not None else 12 * k
        p.setPen(dessin.stylo('accent1', 1.0, 0.7, True))
        p.drawLine(QPointF(tx, ty), QPointF(tx + ux * portee, ty + uy * portee))
        nx, ny = -uy, ux
        w, l = 0.28 * k, L_TUBE * k
        poly = QPolygonF([QPointF(tx + nx * w, ty + ny * w), QPointF(tx + ux * l + nx * w * 1.3, ty + uy * l + ny * w * 1.3),
                          QPointF(tx + ux * l - nx * w * 1.3, ty + uy * l - ny * w * 1.3),
                          QPointF(tx - nx * w, ty - ny * w)])
        p.setPen(dessin.stylo('texte', 1.2))
        p.setBrush(dessin.c('accent2', 0.8))
        p.drawPolygon(poly)
        # étiquette du télescope : à l'extérieur du cercle, placée sans chevauchement (le tube est réservé)
        dessin.reserver(p, tx + ux * l * 0.5, ty + uy * l * 0.5, min(24.0, l * 0.6))
        nom = tr('anim_threeviewsspectra_telescope')
        fm = p.fontMetrics()
        demi = 0.5 * (fm.horizontalAdvance(nom) + 6)
        recul = 12 + demi * abs(ux) + 0.5 * (fm.height() + 2) * abs(uy)
        lx, ly = tx - ux * recul, ty - uy * recul
        # dehors, l'étiquette sortirait du panneau : elle passe au-dessus (ou au-dessous) du télescope
        if lx - demi < r.x() or lx + demi > r.right():
            lx = max(r.x() + demi, min(r.right() - demi, tx))
            ly = ty + (1 if ty > cy else -1) * (0.6 * k + 4 + 0.5 * fm.height())
        dessin.texte(p, lx, ly, nom, 'texte', fond=True)
        # spectre vu
        bas = QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height())
        rb = dessin.cadre(p, bas, tr('anim_threeviewsspectra_titre_spectre'))
        bande = QRectF(rb.x() + 8, rb.y() + 2, rb.width() - 16, max(16.0, rb.height() - 18))
        s = self.spectre()
        raies = [(lam, 1.0, 3.0) for lam in GAZ[self.gaz.currentData()]]
        if s == 'continu':
            bande_spectre(p, bande, 380, 720, lambda lam: 1.0)
        elif s == 'absorption':
            bande_spectre(p, bande, 380, 720, lambda lam: 1.0, [(lam, 0.85, e) for lam, _, e in raies], True)
        elif s == 'emission':
            bande_spectre(p, bande, 380, 720, None, raies)
        else:
            bande_spectre(p, bande, 380, 720, None)
        dessin.police(p, 0.8)
        for lam in range(400, 701, 100):
            dessin.texte(p, bande.left() + bande.width() * (lam - 380) / 340, bande.bottom() + 9, '%d nm' % lam, 'doux')
        dessin.police(p, 1 / 0.8)
