"""Sun's Rays Simulator : la Terre vue de côté, les rayons du Soleil arrivent parallèles.  Le rayon le plus direct
tombe à la latitude δ☉ (déclinaison du Soleil) : entre les tropiques (±23,44°) au fil de l'année ; au-delà des
cercles polaires (±66,56°), jour ou nuit polaire autour des solstices.  Une année dure 30 s à la vitesse ×1."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, date_du_jour

ANNEE = 2026
EPS = astro.obliquite_moyenne(astro.jj_jour_de_l_annee(ANNEE, 0))
TOLERANCE_J = 8                                  # jours autour d'un équinoxe ou d'un solstice pour le nommer


def jours_remarquables(annee: int = ANNEE) -> dict:
    """Jours (0 = 1er janvier) des équinoxes et solstices : λ☉ = 0, 90, 180, 270° (recherche par dichotomie)."""
    out = {}
    for cle, cible in (('equinoxe_mars', 0.0), ('solstice_juin', 90.0), ('equinoxe_sept', 180.0),
                       ('solstice_dec', 270.0)):
        lo = {0.0: 60.0, 90.0: 150.0, 180.0: 245.0, 270.0: 335.0}[cible]
        hi = lo + 40.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if astro.mod180(astro.soleil_jour(annee, mid)['lambda'] - cible) < 0:
                lo = mid
            else:
                hi = mid
        out[cle] = (lo + hi) / 2
    return out


REMARQUABLES = jours_remarquables()


class RayonsSoleil(Animation):
    ID = 'sunsrays'
    JOURS_PAR_S = 365.0 / 30.0

    def construire(self):
        self.jour = self.curseur('jour', 0.0, 364.0, 79.0, dec=0, cle_texte='anim_c_jour')
        self.c_cercles = self.coche('cercles', True)

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def _special(self, jour: float):
        for cle, j in REMARQUABLES.items():
            if abs(jour - j) < TOLERANCE_J:
                return cle, 1.0 - abs(jour - j) / TOLERANCE_J
        return None, 0.0

    def valeurs(self):
        d = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['delta']
        out = [(tr('anim_c_date'), date_du_jour(self.jour.value())),
               (tr('anim_sunsrays_latitude'), '%s %s' % (angle(abs(d), 2), tr('anim_pc_n' if d >= 0 else 'anim_pc_s'))),
               (tr('anim_sunsrays_jour_polaire'), '%s %s' % (angle(90 - abs(d), 2),
                                                             tr('anim_pc_n' if d >= 0 else 'anim_pc_s')))]
        cle, _ = self._special(self.jour.value())
        if cle:
            out.append((tr('anim_sunsrays_moment'), tr('anim_sunsrays_' + cle)))
        return out

    def dessiner(self, p, rect):
        d = astro.soleil_jour(ANNEE, self.jour.value() + 0.5)['delta']
        ray = min(rect.width() * 0.32, rect.height() * 0.40)
        cx, cy = rect.center().x() + rect.width() * 0.08, rect.center().y()
        # rayons parallèles venant de la gauche
        for k in range(-9, 10):
            y = cy + k * ray / 8
            if abs(k) == 0:
                continue
            x_fin = cx - math.sqrt(max(0.0, ray * ray - (y - cy) ** 2)) if abs(y - cy) < ray else cx + ray * 1.3
            p.setPen(dessin.stylo('soleil', 1.0, 0.45))
            p.drawLine(QPointF(rect.x() + 10, y), QPointF(x_fin, y))
        dessin.disque(p, cx, cy, ray, 'terre')
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('nuit', 0.7))
        p.drawPie(QRectF(cx - ray, cy - ray, 2 * ray, 2 * ray), -90 * 16, 180 * 16)
        p.save()
        p.translate(cx, cy)
        p.rotate(-d)                       # axe incliné : le point de latitude δ fait face au Soleil
        lignes = [(0.0, 'equateur', 'anim_sunsrays_equateur'), (EPS, 'accent1', 'anim_sunsrays_tropique_cancer'),
                  (-EPS, 'accent1', 'anim_sunsrays_tropique_capricorne')]
        if self.c_cercles.isChecked():
            lignes += [(90 - EPS, 'accent2', 'anim_sunsrays_cercle_arctique'),
                       (-(90 - EPS), 'accent2', 'anim_sunsrays_cercle_antarctique')]
        dessin.police(p, 0.8)
        for l, cle, lib in lignes:
            y = -ray * math.sin(math.radians(l))
            x = ray * math.cos(math.radians(l))
            p.setPen(dessin.stylo(cle, 1.5, 0.9))
            p.drawLine(QPointF(-x, y), QPointF(x, y))
            # le libellé suit son parallèle, à droite du globe s'il y tient, sinon dedans (côté nuit)
            w = p.fontMetrics().horizontalAdvance(tr(lib))
            dessin.texte(p, x + 6 if x + 6 + w < rect.right() - cx - 4 else x - 6 - w, y, tr(lib), cle, centre=False)
        dessin.police(p, 1 / 0.8)
        p.setPen(dessin.stylo('texte', 2.0))
        p.drawLine(QPointF(0, -ray * 1.2), QPointF(0, ray * 1.2))
        dessin.texte(p, 0, -ray * 1.27, tr('anim_pc_n'), 'doux')
        p.restore()
        # rayon le plus direct : vise le centre de la Terre, touche la latitude δ
        p.setPen(dessin.stylo('soleil', 3.0))
        p.drawLine(QPointF(rect.x() + 10, cy), QPointF(cx - ray, cy))
        dessin.disque(p, cx - ray, cy, 5, 'soleil', bord='fond')
        dessin.texte(p, cx - ray - 10, cy - 14, '%s %s' % (angle(abs(d), 1), tr('anim_pc_n' if d >= 0 else 'anim_pc_s')),
                     'soleil', centre=False, fond=True)
        dessin.police(p, 1.15, gras=True)
        dessin.texte(p, rect.x() + 14, rect.y() + 24, date_du_jour(self.jour.value()), centre=False)
        cle, force = self._special(self.jour.value())
        if cle:
            dessin.texte(p, rect.x() + 14, rect.y() + 48, tr('anim_sunsrays_' + cle), 'accent1', centre=False,
                         alpha=max(0.25, force))
        dessin.police(p, 1 / 1.15)
