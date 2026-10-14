"""Eclipsing Binary Simulator (NAAP) : deux étoiles en orbite, vues presque par la tranche, s'éclipsent tour à
tour.  Flux visuel = somme des disques (uniformes) moins la partie cachée ; la brillance de surface de chaque étoile
dans le filtre V est calculée par la loi de Planck et la courbe de transmission V (Landolt 1992), au lieu des
corrections bolométriques empiriques de l'original.  Période par la 3e loi de Kepler (P = 2π √(a³ / G M) : 0,1158 j
pour a = 1 R☉ et M = 1 M☉ ; l'original écrivait 0,1155).  46 binaires réelles avec leurs courbes de lumière
observées (Catalog and Atlas of Eclipsing Binaries, numérisées depuis l'original) ; sept d'entre elles sont « à
compléter » : un paramètre y est volontairement faux, à retrouver."""
from __future__ import annotations

import functools
import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import deux_corps as dc, dessin, donnees_lot3 as D, lumiere
from ..base import Animation, nombre
from ..graphe import Axes
from .vitesse_radiale import texte_duree

EXEMPLES = {'exemple_%d' % (k + 1): v for k, v in enumerate(D.BINAIRES_EXEMPLES)}
REELLES = {b[0]: b for b in D.BINAIRES}


@functools.lru_cache(maxsize=256)
def brillance_v(t: int) -> float:
    """Brillance de surface dans le filtre V : Σ T_V(λ) B_λ(T) Δλ."""
    return lumiere.somme_filtre('V', lambda w: lumiere.planck(w * 1e-9, t))


class BinaireEclipses(Animation):
    ID = 'eclipsingbinarysim'

    def construire(self):
        self.prereglage = self.choix('systeme', [('anim_eclipsingbinarysim_' + k, k) for k in EXEMPLES] +
                                     [('anim_eclipsingbinarysim_s_' + n.lower().replace(' ', '_'), n) for n in REELLES],
                                     'exemple_1')
        self.prereglage.activated.connect(self._appliquer)
        self.m1 = self.curseur('m1', 0.1, 15.0, 1.0, dec=2, unite='M☉')
        self.m2 = self.curseur('m2', 0.1, 15.0, 1.0, dec=2, unite='M☉')
        self.r1 = self.curseur('r1', 0.05, 25.0, 1.0, dec=3, unite='R☉', log=True)
        self.r2 = self.curseur('r2', 0.05, 25.0, 1.0, dec=3, unite='R☉', log=True)
        self.t1 = self.curseur('t1', 2500.0, 35000.0, 6000.0, dec=0, unite='K', log=True)
        self.t2 = self.curseur('t2', 2500.0, 35000.0, 6000.0, dec=0, unite='K', log=True)
        self.a = self.curseur('a', 1.0, 100.0, 6.0, dec=2, unite='R☉', log=True)
        self.e = self.curseur('e', 0.0, 0.7, 0.0, dec=3)
        self.i = self.curseur('i', 0.0, 90.0, 90.0, dec=2, unite='°')
        self.w = self.curseur('omega', 0.0, 360.0, 0.0, dec=1, unite='°')
        self.decalage = self.curseur('decalage', -0.5, 0.5, 0.0, dec=3)
        self.unite = self.choix('unite', [('anim_eclipsingbinarysim_u_flux', 'flux'),
                                          ('anim_eclipsingbinarysim_u_mag', 'mag')], 'flux')
        self.c_donnees = self.coche('donnees', True)
        self.phase = 0.0

    def _appliquer(self, *_):
        k = self.prereglage.currentData()
        if k in EXEMPLES:
            m1, m2, a, r1, r2, t1, t2, i, w, e = EXEMPLES[k]
        else:
            _, m1, m2, a, r1, r2, t1, t2, i, w, e, _t, _v = REELLES[k]
        self.a.setValue(a)
        for reg, v in ((self.m1, m1), (self.m2, m2), (self.r1, r1 * a), (self.r2, r2 * a), (self.t1, t1),
                       (self.t2, t2), (self.e, e), (self.i, i), (self.w, w), (self.decalage, 0.0)):
            reg.setValue(v)
        self.rafraichir()

    def etat_initial(self):
        self.phase = 0.0

    def avancer(self, dt):
        self.phase = (self.phase + dt / 10.0) % 1.0

    # ------------------------------------------------------------ modèle
    def modele(self) -> dict:
        a = self.a.value()
        cle = tuple(r.value() for r in (self.m1, self.m2, self.r1, self.r2, self.t1, self.t2, self.a, self.e, self.i,
                                        self.w))
        if getattr(self, '_cache', (None,))[0] == cle:
            return self._cache[1]
        r1, r2 = self.r1.value() / a, self.r2.value() / a
        s1, s2 = brillance_v(int(round(self.t1.value()))), brillance_v(int(round(self.t2.value())))
        e, i, w = self.e.value(), self.i.value(), self.w.value()
        ph0 = dc.phase_conjonction(e, w)
        fmax = math.pi * (r1 * r1 * s1 + r2 * r2 * s2)
        courbe = [(x / 400, dc.flux_deux_disques(ph0 + x / 400, r1, r2, s1, s2, e, i, w) / fmax) for x in range(401)]
        m = {'r1': r1, 'r2': r2, 's1': s1, 's2': s2, 'e': e, 'i': i, 'w': w, 'ph0': ph0, 'courbe': courbe,
             'P': dc.periode_s(a * dc.R_SOLEIL_M, self.m1.value() * dc.M_SOLEIL_KG, self.m2.value() * dc.M_SOLEIL_KG),
             'fmax': fmax}
        self._cache = (cle, m)
        return m

    def flux_a(self, m, phase) -> float:
        return dc.flux_deux_disques(m['ph0'] + phase, m['r1'], m['r2'], m['s1'], m['s2'], m['e'], m['i'],
                                    m['w']) / m['fmax']

    def donnees(self):
        k = self.prereglage.currentData()
        return D.courbes_binaires().get(k) if self.c_donnees.isChecked() else None

    def ecart(self, m, pts) -> float:
        """Écart quadratique moyen entre le modèle et les mesures (flux relatif)."""
        d = self.decalage.value()
        cle = (self._cache[0], d, id(pts))
        if getattr(self, '_ecart', (None,))[0] != cle:
            self._ecart = (cle, math.sqrt(sum((self.flux_a(m, ph + d) - f) ** 2 for ph, f in pts) / len(pts)))
        return self._ecart[1]

    def valeurs(self):
        m = self.modele()
        k = self.prereglage.currentData()
        out = [(tr('anim_c_periode'), texte_duree(m['P'])),
               (tr('anim_eclipsingbinarysim_profondeur'), '%s %%' % nombre(100 * (1 - min(f for _, f in m['courbe'])), 1))]
        pts = D.courbes_binaires().get(k)
        if pts:
            out.append((tr('anim_eclipsingbinarysim_ecart'), nombre(self.ecart(m, pts), 4)))
            if k in D.BINAIRES_A_COMPLETER:
                out.append((tr('anim_eclipsingbinarysim_a_completer'), tr('anim_oui')))
            typ = REELLES[k][11]
            if typ:
                out.append((tr('anim_eclipsingbinarysim_types'), typ))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        m = self.modele()
        z = dessin.zones(rect, 2, 10.0)
        self._vue(p, dessin.cadre(p, z[0], tr('anim_eclipsingbinarysim_titre_vue')), m)
        r = dessin.cadre(p, z[1], tr('anim_eclipsingbinarysim_titre_courbe'))
        mag = self.unite.currentData() == 'mag'
        pts = self.donnees()
        fmin = min([f for _, f in m['courbe']] + ([f for _, f in pts] if pts else []))
        fmax = max([1.0] + ([f for _, f in pts] if pts else []))
        if mag:
            conv = lambda f: -2.5 * math.log10(max(f, 1e-6))
            y0, y1 = conv(fmax) - 0.05, conv(fmin) + 0.05
            ax = Axes(r, 0, 1, y1, y0, marges=(48, 8, 10, 28)).avec(p)
            ax.fond(p, tr('anim_c_phase'), tr('anim_eclipsingbinarysim_axe_mag'), dec_x=1, dec_y=2)
        else:
            conv = lambda f: f
            ax = Axes(r, 0, 1, max(0.0, fmin - 0.05), fmax + 0.03, marges=(48, 8, 10, 28)).avec(p)
            ax.fond(p, tr('anim_c_phase'), tr('anim_c_flux_relatif'), dec_x=1, dec_y=2)
        if pts:
            ax.points([(ph, conv(f)) for ph, f in pts], 'doux', 1.5, 0.75)
        d = self.decalage.value()
        ax.courbe(sorted(((x - d) % 1.0, conv(f)) for x, f in m['courbe']), 'accent1', 2.0)
        ax.verticale((self.phase - d) % 1.0, 'accent3', 1.2, False)

    def _vue(self, p, r, m):
        cx, cy = r.center().x(), r.center().y()
        x, y, z = dc.relative(m['ph0'] + self.phase, 1.0, m['e'], m['i'], m['w'])
        q = self.m2.value() / (self.m1.value() + self.m2.value())
        k = min(r.width() * 0.42 / (1 + m['e']), r.height() * 0.45 / max(0.3, abs(y) + m['r2'] + q * m['r1'], 0.5))
        x1, y1 = -q * x, -q * y
        x2, y2 = (1 - q) * x, (1 - q) * y
        c1 = QColor(*lumiere.couleur_corps_noir(int(round(self.t1.value()))))
        c2 = QColor(*lumiere.couleur_corps_noir(int(round(self.t2.value()))))
        corps = [(-q * z, x1, y1, m['r1'], c1, '1'), ((1 - q) * z, x2, y2, m['r2'], c2, '2')]
        for _, xx, yy, rr, col, nom in sorted(corps, key=lambda c: c[0]):        # le plus lointain d'abord
            dessin.disque(p, cx + xx * k, cy - yy * k, max(1.5, rr * k), col, bord='fond')
        for _, xx, yy, rr, col, nom in corps:
            dessin.texte(p, cx + xx * k, cy - yy * k - rr * k - 10, nom, 'doux')
        p.setPen(dessin.stylo('accent3', 1.5))
        p.drawLine(QPointF(cx - 5, cy), QPointF(cx + 5, cy))
        p.drawLine(QPointF(cx, cy - 5), QPointF(cx, cy + 5))
