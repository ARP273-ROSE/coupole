"""Transit Simulator (NAAP) : une planète passe devant son étoile et en masque une petite partie.  Profondeur du
transit (R_p / R_*)² (disques uniformes, aire de recouvrement exacte), durée selon la taille de l'orbite et
l'inclinaison, période par la 3e loi de Kepler.  Mesures simulées avec du bruit.  Planètes réelles : paramètres de la
NASA Exoplanet Archive (2026) au lieu des valeurs de 2007 de l'original (ex. HD 209458 b : 1,39 R♃ au lieu de 1,32,
excentricité nulle au lieu de 0,07)."""
from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import deux_corps as dc, dessin, donnees_lot3 as D
from ..base import Animation, nombre
from ..graphe import Axes
from .vitesse_radiale import texte_duree

PRERELAGES = {'a': D.TRANSITS_EXEMPLES[0], 'b': D.TRANSITS_EXEMPLES[1], **{t[0]: t for t in D.TRANSITS}}


class Transits(Animation):
    ID = 'transitsimulator'

    def construire(self):
        self.prereglage = self.choix('systeme', [('anim_transitsimulator_s_a', 'a'), ('anim_transitsimulator_s_b', 'b')] +
                                     [('anim_transitsimulator_s_' + t[0].lower().replace(' ', '_').replace('-', '_'),
                                       t[0]) for t in D.TRANSITS], 'HD 209458 b')
        self.prereglage.activated.connect(self._appliquer)
        self.mp = self.curseur('masse_planete', 0.001, 15.0, 0.73, dec=3, unite='M♃', log=True)
        self.rp = self.curseur('rayon_planete', 0.05, 2.5, 1.39, dec=3, unite='R♃', log=True)
        self.ms = self.curseur('masse_etoile', 0.1, 3.0, 1.23, dec=3, unite='M☉')
        self.rs = self.curseur('rayon_etoile', 0.1, 4.0, 1.19, dec=3, unite='R☉')
        self.a = self.curseur('a', 0.01, 2.0, 0.048_57, dec=5, unite='ua', log=True)
        self.e = self.curseur('e', 0.0, 0.6, 0.0, dec=3)
        self.i = self.curseur('i', 75.0, 90.0, 86.71, dec=2, unite='°')
        self.w = self.curseur('omega', 0.0, 360.0, 90.0, dec=1, unite='°')
        self.bruit = self.curseur('bruit', 0.0, 0.01, 0.002, dec=4)
        self.n_mesures = self.curseur('mesures', 0.0, 1000.0, 200.0, dec=0)
        self.c_courbe = self.coche('courbe', True)
        self.phase = 0.0
        self._mesures = None

    def _appliquer(self, *_):
        t = PRERELAGES[self.prereglage.currentData()]
        _, mp, rp, ms, rs, a, e, i, w, periode = t
        if periode:                     # planète réelle : a tiré de la période publiée (3e loi), plus cohérent
            a = dc.demi_grand_axe_m(periode * dc.JOUR_S, ms * dc.M_SOLEIL_KG, mp * dc.M_JUPITER_KG) / dc.UA_M
        for reg, v in ((self.mp, mp), (self.rp, rp), (self.ms, ms), (self.rs, rs), (self.a, a), (self.e, e),
                       (self.i, i), (self.w, w)):
            reg.setValue(v)
        self.phase = 0.0
        self.rafraichir()

    def etat_initial(self):
        self.phase = 0.0
        self._mesures = None

    def reglage_change(self):
        self._mesures = None
        super().reglage_change()

    # ------------------------------------------------------------ modèle
    def systeme(self) -> dict:
        cle = tuple(r.value() for r in (self.mp, self.rp, self.ms, self.rs, self.a, self.e, self.i, self.w))
        if getattr(self, '_cache', (None,))[0] == cle:
            return self._cache[1]
        a_m = self.a.value() * dc.UA_M
        m1, m2 = self.ms.value() * dc.M_SOLEIL_KG, self.mp.value() * dc.M_JUPITER_KG
        r1, r2 = self.rs.value() * dc.R_SOLEIL_M / a_m, self.rp.value() * dc.R_JUPITER_M / a_m
        e, i, w = self.e.value(), self.i.value(), self.w.value()
        ph0 = dc.phase_conjonction(e, w)
        s = {'P': dc.periode_s(a_m, m1, m2), 'r1': r1, 'r2': r2, 'e': e, 'i': i, 'w': w, 'ph0': ph0,
             'duree': dc.duree_transit(ph0, r1, r2, e, i, w, n=2000)}
        h = self.fenetre(s)
        s['courbe'] = [(x, self.flux_relatif(s, ph0 + x)) for x in (-h + 2 * h * k / 300 for k in range(301))]
        s['profondeur'] = 1 - min(f for _, f in s['courbe'])
        self._cache = (cle, s)
        return s

    @staticmethod
    def flux_relatif(s, phase) -> float:
        x, y, z = dc.relative(phase, 1.0, s['e'], s['i'], s['w'])
        if z <= 0:
            return 1.0
        return 1.0 - dc.aire_recouvrement(s['r1'], s['r2'], math.hypot(x, y)) / (math.pi * s['r1'] ** 2)

    @staticmethod
    def fenetre(s):
        """Demi-largeur (en phase) du graphe, centré sur le transit."""
        return min(0.5, max(0.01, 1.5 * s['duree'] if s['duree'] > 0 else 0.03))

    def mesures(self, s):
        if self._mesures is None:
            alea = random.Random(7)
            h = self.fenetre(s)
            sig = self.bruit.value()
            self._mesures = [(dx, self.flux_relatif(s, s['ph0'] + dx) + alea.gauss(0.0, sig))
                             for dx in (alea.uniform(-h, h) for _ in range(int(self.n_mesures.value())))]
        return self._mesures

    def avancer(self, dt):
        s = self.systeme()
        h = self.fenetre(s)
        self.phase = (self.phase + dt * h / 4.0)           # traversée de la fenêtre en ≈ 8 s
        if self.phase > h:
            self.phase = -h

    def valeurs(self):
        s = self.systeme()
        b = math.cos(math.radians(s['i'])) / s['r1'] * (1 - s['e'] ** 2) / (1 + s['e'] * math.sin(math.radians(s['w'])))
        prof = s['profondeur']
        out = [(tr('anim_c_periode'), texte_duree(s['P'])),
               (tr('anim_transitsimulator_profondeur'), '%s %%' % nombre(100 * prof, 3)),
               (tr('anim_transitsimulator_rapport'), '(R_p / R_*)² = %s %%' % nombre(100 * (s['r2'] / s['r1']) ** 2, 3)),
               (tr('anim_transitsimulator_duree'), texte_duree(s['duree'] * s['P']) if s['duree'] else
                tr('anim_transitsimulator_pas_de_transit')),
               (tr('anim_transitsimulator_b'), nombre(b, 3))]
        pub = PRERELAGES[self.prereglage.currentData()][9]
        if pub:
            out.append((tr('anim_transitsimulator_p_publiee'), '%s %s' % (nombre(pub, 4), tr('anim_c_jours'))))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        s = self.systeme()
        z = dessin.zones(rect, 2, 10.0)
        self._vue(p, dessin.cadre(p, z[0], tr('anim_transitsimulator_titre_vue')), s)
        r = dessin.cadre(p, z[1], tr('anim_transitsimulator_titre_courbe'))
        h = self.fenetre(s)
        prof = (s['r2'] / s['r1']) ** 2
        bas = 1 - max(prof * 1.6, 4 * self.bruit.value(), 0.002)
        ax = Axes(r, -h, h, bas, 1 + max(prof * 0.4, 3 * self.bruit.value(), 0.0008), marges=(58, 8, 12, 28)).avec(p)
        ax.fond(p, tr('anim_transitsimulator_axe_phase'), tr('anim_c_flux_relatif'), dec_y=4 if prof < 0.01 else 3,
                dec_x=3)
        if self.n_mesures.value() > 0:
            ax.points(self.mesures(s), 'doux', 1.6, 0.7)
        if self.c_courbe.isChecked():
            ax.courbe(s['courbe'], 'accent1', 2.0)
        ax.verticale(self.phase, 'accent3', 1.2, False)

    def _vue(self, p, r, s):
        cx, cy = r.center().x(), r.center().y()
        k = min(r.width() * 0.3, r.height() * 0.42) / s['r1']
        dessin.disque(p, cx, cy, s['r1'] * k, 'soleil', alpha=0.9)
        # trajet de la planète devant l'étoile
        pts = [dc.relative(s['ph0'] + d, 1.0, s['e'], s['i'], s['w']) for d in (-0.05, 0.05)]
        p.setPen(dessin.stylo('grille', 1.0, None, True))
        p.drawLine(QPointF(cx + pts[0][0] * k, cy - pts[0][1] * k), QPointF(cx + pts[1][0] * k, cy - pts[1][1] * k))
        x, y, zz = dc.relative(s['ph0'] + self.phase, 1.0, s['e'], s['i'], s['w'])
        if zz > 0 or math.hypot(x, y) > s['r1']:
            dessin.disque(p, cx + x * k, cy - y * k, max(1.5, s['r2'] * k), 'nuit', bord='doux')
        dessin.texte(p, r.left() + 8, r.bottom() - 8, tr('anim_transitsimulator_echelle'), 'doux', centre=False)
