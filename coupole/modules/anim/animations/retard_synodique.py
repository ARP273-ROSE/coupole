"""Synodic Lag : différence entre jour sidéral et jour solaire.  La Terre tourne sur elle-même tout en avançant sur
son orbite : après un tour complet par rapport aux étoiles (jour sidéral), elle doit encore tourner un peu pour
que le Soleil revienne au méridien (jour solaire).  1 / jour solaire = 1 / jour sidéral − 1 / année.  Comme dans
l'original, la rotation peut être ralentie (240 h, 1 200 h) pour rendre le retard visible."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, duree_hm, nombre

ANNEE_H = astro.ANNEE_SIDERALE_J * 24.0                     # 8 766,15 h, comme l'original
JOUR_SIDERAL_H = astro.jour_sideral_s(astro.ANNEE_SIDERALE_J) / 3600.0    # 23 h 56 min 4,1 s
ROTATIONS = (('reel', JOUR_SIDERAL_H), ('h240', 240.0), ('h1200', 1200.0))
SECONDES_PAR_TOUR = 3.0


class RetardSynodique(Animation):
    ID = 'synodiclag'

    def construire(self):
        self.rotation = self.choix('rotation', [('anim_synodiclag_r_' + k, v) for k, v in ROTATIONS], 240.0)
        self.bouton('anim_synodiclag_sideral', lambda: self.lancer('sideral'))
        self.bouton('anim_synodiclag_solaire', lambda: self.lancer('solaire'))
        self.bouton('anim_synodiclag_midi', self.realigner)
        self.c_ombre = self.coche('ombre', True)
        self.etat_initial()

    def etat_initial(self):
        self.theta, self.phi = 0.0, 0.0                 # orbite et rotation (degrés), midi au départ
        self.depart = (0.0, 0.0)
        self.mode = None                                  # 'sideral' / 'solaire' : s'arrête au bout d'un jour
        self.ecoule_h = 0.0

    def reglage_change(self):
        if getattr(self, '_rot', None) != self.rotation.currentData():
            self._rot = self.rotation.currentData()
            self.realigner()
        super().reglage_change()

    def realigner(self):
        """Remet la Terre à midi (le méridien de l'observateur tourné vers le Soleil), comme « realign to noon »."""
        self.phi = self.theta
        self.depart = (self.theta, self.phi)
        self.ecoule_h = 0.0
        self.mode = None
        self.rafraichir()

    def lancer(self, mode: str):
        self.depart = (self.theta, self.phi)
        self.ecoule_h = 0.0
        self.mode = mode
        if not self.en_lecture:
            self.basculer_lecture()

    def durees(self) -> tuple[float, float]:
        rot = self.rotation.currentData()
        return rot, astro.jour_solaire(rot, ANNEE_H)

    def avancer(self, dt):
        rot, sol = self.durees()
        dh = dt * rot / SECONDES_PAR_TOUR                  # un tour en SECONDES_PAR_TOUR secondes
        fin = None
        if self.mode == 'sideral':
            fin = rot
        elif self.mode == 'solaire':
            fin = sol
        if fin is not None and self.ecoule_h + dh >= fin:
            dh = fin - self.ecoule_h
            self.mode = None
            if self.en_lecture:
                self.basculer_lecture()
        self.ecoule_h += dh
        self.theta += 360.0 * dh / ANNEE_H
        self.phi += 360.0 * dh / rot

    def valeurs(self):
        rot, sol = self.durees()
        return [(tr('anim_synodiclag_jour_sideral'), duree_hm(rot) if rot < 100 else '%s h' % nombre(rot, 0)),
                (tr('anim_synodiclag_jour_solaire'), self._duree(sol)),
                (tr('anim_synodiclag_retard'), self._duree(sol - rot)),
                (tr('anim_synodiclag_angle_soleil'), angle((self.phi - self.theta) % 360.0, 2)),
                (tr('anim_synodiclag_tour_etoiles'), angle((self.phi - self.depart[1]) % 360.0 if self.ecoule_h else 0.0, 2)),
                (tr('anim_synodiclag_ecoule'), self._duree(self.ecoule_h))]

    @staticmethod
    def _duree(h: float) -> str:
        if h < 1.0:
            return '%s min %s s' % (int(h * 60), nombre((h * 3600) % 60, 1))
        return duree_hm(h) if h < 100 else '%s h' % nombre(h, 2)

    def dessiner(self, p, rect):
        cx, cy = rect.center().x(), rect.center().y()
        ro = min(rect.width(), rect.height()) * 0.36
        rt = max(14.0, ro * 0.17)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), ro, ro)
        dessin.disque(p, cx, cy, max(10.0, ro * 0.1), 'soleil')
        # étoiles lointaines : la direction fixe de référence
        dessin.fleche(p, rect.right() - 60, rect.y() + 24, rect.right() - 14, rect.y() + 24,
                      dessin.stylo('etoile', 1.4, 0.8), 7)
        dessin.texte(p, rect.right() - 74, rect.y() + 42, tr('anim_synodiclag_vers_etoiles'), 'doux')
        if self.c_ombre.isChecked() and self.ecoule_h > 0:
            self._terre(p, cx, cy, ro, rt, *self.depart, fantome=True)
        self._terre(p, cx, cy, ro, rt, self.theta, self.phi)

    def _terre(self, p, cx, cy, ro, rt, theta, phi, fantome=False):
        t = math.radians(theta)
        ex, ey = cx + ro * math.cos(t), cy - ro * math.sin(t)
        a = 0.35 if fantome else 1.0
        if not fantome:
            p.setPen(dessin.stylo('soleil', 1.0, 0.5, pointille=True))
            p.drawLine(QPointF(cx, cy), QPointF(ex, ey))
        dessin.disque(p, ex, ey, rt, 'terre', alpha=a)
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('nuit', 0.65 * a))
        p.drawPie(dessin.QRectF(ex - rt, ey - rt, 2 * rt, 2 * rt), int((theta - 90) * 16), 180 * 16)
        # méridien de l'observateur : pointe vers le Soleil à midi (φ = θ)
        f = math.radians(phi + 180.0)
        dessin.fleche(p, ex, ey, ex + 1.5 * rt * math.cos(f), ey - 1.5 * rt * math.sin(f),
                      dessin.stylo('accent3', 2.2, a), 7)
        # direction fixe (étoiles) attachée à la Terre au départ du jour
        if not fantome:
            g = math.radians(self.depart[1] + 180.0)
            p.setPen(dessin.stylo('etoile', 1.2, 0.6, pointille=True))
            p.drawLine(QPointF(ex, ey), QPointF(ex + 1.9 * rt * math.cos(g), ey - 1.9 * rt * math.sin(g)))
