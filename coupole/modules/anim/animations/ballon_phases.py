"""Basketball Phases Simulator : un ballon éclairé par une lampe, vu de plusieurs directions — l'analogie des
phases de la Lune.  Vue de dessus de la pièce (la lampe à gauche, le ballon au centre, l'œil qu'on fait tourner
autour) et ballon tel que l'œil le voit.  La partie éclairée visible ne dépend que de l'angle de phase i, angle au
ballon entre la lampe et l'œil : fraction (1 + cos i) / 2."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre
from .phases_lune import ANGLES_PHASES, PHASES


def vue_de_l_oeil(theta: float) -> dict:
    """Œil à l'angle θ autour du ballon (θ = 0 : entre la lampe et le ballon, sens trigonométrique vu de dessus) :
    angle de phase, côté éclairé vu par l'œil, élongation équivalente de la Lune et nom de la phase."""
    t = math.radians(theta)
    lampe = (-1.0, 0.0)                       # direction de la lampe vue du ballon (la lampe est à gauche)
    oeil = (-math.cos(t), -math.sin(t))        # θ = 0 : l'œil est du côté de la lampe
    i = astro.angle_de_phase((0.0, 0.0), lampe, oeil)
    d = (-oeil[0], -oeil[1])                   # regard de l'œil vers le ballon
    droite = (d[1], -d[0])
    a_droite = lampe[0] * droite[0] + lampe[1] * droite[1] >= 0
    elong = 180.0 - i if a_droite else 180.0 + i
    return {'i': i, 'a_droite': a_droite, 'elongation': elong % 360.0, 'nom': astro.nom_de_phase(elong)}


class BallonPhases(Animation):
    ID = 'basketball'
    TOURS_PAR_S = 0.05

    def construire(self):
        self.theta = self.curseur('angle', 0.0, 360.0, 180.0, dec=1, unite='°')
        self.choix_phase = self.choix('position', [('anim_phase_' + k, k) for k in PHASES], 'nl')
        self.choix_phase.activated.connect(self._phase_choisie)
        self.c_lune = self.coche('lune', True)
        self._piece = None

    def _phase_choisie(self, *_):
        # élongation e de la Lune ↔ œil à θ = e − 180° (croissante : lampe à droite de l'œil)
        self.theta.setValue((ANGLES_PHASES[self.choix_phase.currentData()] - 180.0) % 360.0)

    def avancer(self, dt):
        self.theta.setValue((self.theta.value() + 360.0 * self.TOURS_PAR_S * dt) % 360.0)

    def reglage_change(self):
        cle = vue_de_l_oeil(self.theta.value())['nom']
        if self.choix_phase.currentData() != cle:
            self.choix_phase.blockSignals(True)
            self.choix_phase.setCurrentIndex(self.choix_phase.findData(cle))
            self.choix_phase.blockSignals(False)
        super().reglage_change()

    def valeurs(self):
        v = vue_de_l_oeil(self.theta.value())
        return [(tr('anim_c_angle_phase'), angle(v['i'])),
                (tr('anim_c_eclairee'), '%s %%' % nombre(100 * astro.fraction_eclairee_phase(v['i']), 1)),
                (tr('anim_basketball_cote'), tr('anim_basketball_droite' if v['a_droite'] else 'anim_basketball_gauche')),
                (tr('anim_basketball_phase_lune'), tr('anim_phase_' + v['nom']))]

    # ------------------------------------------------------------ souris : l'œil se déplace autour du ballon
    def presser(self, pos, bouton):
        if self._piece is not None and self._piece[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return super().presser(pos, bouton)

    def _tirer(self, pos):
        _, cx, cy = self._piece
        a = math.degrees(math.atan2(cy - pos.y(), pos.x() - cx))
        self.theta.setValue((a - 180.0) % 360.0)

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.55) if self.c_lune.isChecked() else dessin.zones(rect, 2, 0.7)
        self._dessus(p, dessin.cadre(p, z[0], tr('anim_basketball_vue_dessus')))
        v = vue_de_l_oeil(self.theta.value())
        r1 = dessin.cadre(p, z[1], tr('anim_basketball_vue_oeil'))
        rr = min(r1.width(), r1.height()) * 0.36
        dessin.disque_phase(p, r1.center().x(), r1.center().y(), rr, v['i'], 0.0 if v['a_droite'] else 180.0,
                            'mars', 'nuit')
        if len(z) == 3:
            r2 = dessin.cadre(p, z[2], tr('anim_basketball_vue_lune'))
            rl = min(r2.width(), r2.height()) * 0.32
            dessin.phase_lune(p, r2.center().x(), r2.center().y() - 8, rl, v['elongation'])
            dessin.texte(p, r2.center().x(), r2.center().y() + rl + 10, tr('anim_phase_' + v['nom']), 'doux')

    def _dessus(self, p, r):
        cx, cy = r.center().x(), r.center().y()
        ro = min(r.width(), r.height()) * 0.36
        self._piece = (r, cx, cy)
        # lampe à gauche, rayons
        lx = r.x() + 18
        dessin.disque(p, lx, cy, 11, 'soleil')
        for k in (-0.6, -0.3, 0.0, 0.3, 0.6):
            dessin.fleche(p, lx + 18, cy + k * ro * 0.8, cx - ro * 0.35, cy + k * ro * 0.5,
                          dessin.stylo('soleil', 1.0, 0.45), 5)
        p.setPen(dessin.stylo('grille', 1.0, pointille=True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), ro, ro)
        # ballon : moitié éclairée tournée vers la lampe
        rb = max(8.0, ro * 0.16)
        dessin.disque(p, cx, cy, rb, 'nuit')
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('mars'))
        p.drawPie(dessin.QRectF(cx - rb, cy - rb, 2 * rb, 2 * rb), 90 * 16, 180 * 16)
        # œil et ligne de visée
        t = math.radians(self.theta.value())
        ox, oy = cx - ro * math.cos(t), cy + ro * math.sin(t)
        p.setPen(dessin.stylo('accent2', 1.2, 0.7, pointille=True))
        p.drawLine(QPointF(ox, oy), QPointF(cx, cy))
        dessin.disque(p, ox, oy, 7, 'accent2', bord='texte')
        dessin.disque(p, ox + 3 * (cx - ox) / ro, oy + 3 * (cy - oy) / ro, 2.5, 'fond')
        dessin.texte(p, ox, oy - 16, tr('anim_basketball_oeil'), 'accent2', fond=True)
