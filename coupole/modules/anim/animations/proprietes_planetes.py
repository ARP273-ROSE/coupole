"""Solar System Properties Explorer : histogrammes des propriétés des planètes (telluriques, géantes) et de Pluton :
distance au Soleil, période orbitale, masse, rayon, nombre de satellites, rotation, densité.  Valeurs de la NASA
Planetary Fact Sheet (2026), rapportées à la Terre ; l'original datait d'avant 2006 (Jupiter 28 satellites, Saturne 30,
Uranus 21, Neptune 8, Pluton 1 : aujourd'hui 95, 274, 28, 16 et 5)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QRectF

from ....core.i18n import tr
from .. import astro, dessin, donnees_lot3 as D
from ..base import Animation, nombre
from ..graphe import Axes

TERRE = D.PLANETES_FICHE[2]
PROPRIETES = ('distance', 'periode', 'masse', 'rayon', 'satellites', 'rotation', 'densite')
COULEURS = {'tellurique': 'accent3', 'geante': 'accent2', 'naine': 'accent1'}


def valeur(planete, prop: str) -> float:
    nom, masse, diam, dens, rot, dist, per, sat, groupe = planete
    return {'distance': dist * 1e6 / astro.UA_KM, 'periode': per / astro.ANNEE_SIDERALE_J,
            'masse': masse / TERRE[1], 'rayon': diam / TERRE[2], 'satellites': float(sat),
            'rotation': rot / 24.0, 'densite': dens / 1000.0}[prop]


class ProprietesPlanetes(Animation):
    ID = 'solarsystemproperties'
    ANIMEE = False

    def construire(self):
        self.prop = self.choix('propriete', [('anim_solarsystemproperties_p_' + k, k) for k in PROPRIETES], 'distance')
        self.cases = {g: self.coche('g_' + g, True) for g in ('tellurique', 'geante', 'naine')}
        self.c_log = self.coche('log', False)

    def planetes(self):
        return [pl for pl in D.PLANETES_FICHE if self.cases[pl[8]].isChecked()]

    def valeurs(self):
        prop = self.prop.currentData()
        out = []
        for pl in self.planetes():
            v = valeur(pl, prop)
            out.append((tr('anim_planete_' + pl[0]), nombre(v, 0 if prop == 'satellites' else (3 if abs(v) < 10 else 1))))
        return out

    def dessiner(self, p, rect):
        prop = self.prop.currentData()
        pls = self.planetes()
        r = dessin.cadre(p, rect, '%s (%s)' % (tr('anim_solarsystemproperties_p_' + prop),
                                               tr('anim_solarsystemproperties_u_' + prop)))
        if not pls:
            return
        vals = [valeur(pl, prop) for pl in pls]
        log = self.c_log.isChecked() and prop not in ('rotation',) and min(vals) > 0
        if log:
            lo, hi = 10 ** math.floor(math.log10(min(vals))), 10 ** math.ceil(math.log10(max(vals)))
            ax = Axes(r, 0, len(pls), lo, hi, ylog=True, marges=(52, 10, 10, 34)).avec(p)
        else:
            lo, hi = min(0.0, min(vals) * 1.1), max(vals) * 1.1 if max(vals) > 0 else 1.0
            ax = Axes(r, 0, len(pls), lo, hi, marges=(52, 10, 10, 34)).avec(p)
        ax.fond(p, '', '', fmt_x=lambda v: '', n_x=1)
        base = lo if log else 0.0
        for k, (pl, v) in enumerate(zip(pls, vals)):
            x0, x1 = ax.px(k + 0.18), ax.px(k + 0.82)
            y0, y1 = ax.py(base), ax.py(v)
            p.fillRect(QRectF(x0, min(y0, y1), x1 - x0, abs(y1 - y0)), dessin.c(COULEURS[pl[8]], 0.8))
            dessin.police(p, 0.85)
            # noms en quinconce quand la place manque
            nom = tr('anim_planete_' + pl[0])
            serre = p.fontMetrics().horizontalAdvance(nom) > ax.px(k + 1) - ax.px(k) - 2
            dessin.texte(p, (x0 + x1) / 2, ax.r.bottom() + 11 + (11 if serre and k % 2 else 0), nom, 'texte')
            txt = nombre(v, 0 if prop == 'satellites' else (2 if abs(v) < 10 else 0))
            dessin.texte(p, (x0 + x1) / 2, min(y0, y1) - 8, txt, 'doux')
            dessin.police(p, 1 / 0.85)
