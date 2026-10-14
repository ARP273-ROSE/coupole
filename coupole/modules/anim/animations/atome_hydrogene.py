"""Hydrogen Atom Simulator (NAAP) : un photon frappe un atome d'hydrogène.  Il n'est absorbé que si son énergie
vaut exactement l'écart entre le niveau de l'électron et un niveau supérieur, E = 13,598 eV (1/n² − 1/m²) ; s'il
dépasse l'énergie d'ionisation du niveau, l'électron est arraché ; sinon il passe.  L'atome excité retombe ensuite
vers un niveau inférieur en émettant un photon (choix au hasard, équiprobable, comme l'original ; les vraies
probabilités suivent les coefficients d'Einstein).  Niveaux de Bohr avec la masse réduite (13,598 eV, et non
13,6 eV) et hc = 1 239,84 eV nm (l'original : 1 240) ; longueurs d'onde dans le vide."""
from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPolygonF

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre

N_MAX = 6
TOLERANCE_EV = 0.01            # résonance volontairement large, pour qu'on puisse viser au curseur
VOL_S = 1.2                    # durée du trajet d'un photon jusqu'à l'atome
ATTENTE_S = 2.5                # durée de vie de l'état excité (original : 2,5 s)
RECOMBINAISON = (0.2, 0.2, 0.2, 0.2, 0.1, 0.1)     # niveau de recapture (original)
TRANSITIONS = [(a, b) for a in (1, 2, 3) for b in range(a + 1, N_MAX + 1)]


def evenement_photon(n: int, e: float):
    """Issue d'un photon d'énergie e (eV) sur un électron au niveau n (0 : atome ionisé).
    Rend ('absorbe', m) | ('ionise', énergie cinétique) | ('passe', None)."""
    if n == 0:
        return ('passe', None)
    for m in range(n + 1, N_MAX + 1):
        if abs(e - lumiere.transition_ev(n, m)) <= TOLERANCE_EV:
            return ('absorbe', m)
    seuil = -lumiere.niveau_ev(n)
    if e >= seuil:
        return ('ionise', e - seuil)
    return ('passe', None)


class AtomeHydrogene(Animation):
    ID = 'hydrogenatom'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.e = self.curseur('energie', 0.5, 14.0, 10.2, dec=2, unite='eV')
        self.transition = self.choix('transition', [('anim_hydrogenatom_t_%d_%d' % ab, '%d-%d' % ab)
                                                    for ab in TRANSITIONS], '1-2')
        self.bouton('anim_hydrogenatom_tirer', self.tirer)
        self.bouton('anim_hydrogenatom_tirer_transition', self.tirer_transition)
        self.etat_initial()

    def etat_initial(self):
        self.n = 1
        self.photons = []             # dicts : e, t (âge), sortant, angle, issue
        self.journal = []
        self.attente = None           # instant de la désexcitation / recombinaison
        self.t = 0.0
        self.alea = random.Random(1)

    # ------------------------------------------------------------ actions
    def tirer(self, e=None):
        e = self.e.value() if e is None or isinstance(e, bool) else e
        self.photons.append({'e': e, 't': 0.0, 'sortant': False, 'angle': 0.0})
        self._noter('tir', e=e)
        if not self.en_lecture:
            self.basculer_lecture()

    def tirer_transition(self):
        a, b = map(int, self.transition.currentData().split('-'))
        self.e.setValue(round(lumiere.transition_ev(a, b), 2))
        self.tirer(lumiere.transition_ev(a, b))

    def _noter(self, cle, **v):
        self.journal.append(tr('anim_hydrogenatom_j_' + cle, **{k: (nombre(x, 2) if isinstance(x, float) else x)
                                                                 for k, x in v.items()}))
        self.journal = self.journal[-6:]

    def _emettre(self, e):
        self.photons.append({'e': e, 't': 0.0, 'sortant': True, 'angle': self.alea.uniform(-2.6, 2.6)})

    # ------------------------------------------------------------ temps
    def avancer(self, dt):
        self.t += dt
        for ph in list(self.photons):
            ph['t'] += dt
            if not ph['sortant'] and ph['t'] >= VOL_S and 'issue' not in ph:
                issue, x = evenement_photon(self.n, ph['e'])
                ph['issue'] = issue
                if issue == 'absorbe':
                    self._noter('absorbe', a=self.n, b=x)
                    self.n = x
                    self.photons.remove(ph)
                    self.attente = self.t + ATTENTE_S
                elif issue == 'ionise':
                    self._noter('ionise', a=self.n, k=x)
                    self.n = 0
                    self.photons.remove(ph)
                    self.attente = self.t + ATTENTE_S
                else:
                    self._noter('passe')
            if ph in self.photons and ph['t'] > 2.6 * VOL_S:
                self.photons.remove(ph)
        if self.attente is not None and self.t >= self.attente:
            self.attente = None
            if self.n == 0:                                        # recombinaison
                m = self.alea.choices(range(1, N_MAX + 1), RECOMBINAISON)[0]
                self.n = m
                self._emettre(-lumiere.niveau_ev(m))
                self._noter('recombine', b=m)
                if m > 1:
                    self.attente = self.t + ATTENTE_S
            elif self.n > 1:                                       # désexcitation, niveau inférieur au hasard
                m = self.alea.randrange(1, self.n)
                e = lumiere.transition_ev(m, self.n)
                self._noter('emet', a=self.n, b=m, l=nombre(lumiere.longueur_onde_nm(e), 1))
                self._emettre(e)
                self.n = m
                if m > 1:
                    self.attente = self.t + ATTENTE_S

    def valeurs(self):
        e = self.e.value()
        out = [(tr('anim_hydrogenatom_niveau'), str(self.n) if self.n else tr('anim_hydrogenatom_ionise')),
               (tr('anim_hydrogenatom_photon'), '%s eV → λ = %s nm' % (nombre(e, 2), nombre(lumiere.longueur_onde_nm(e), 1)))]
        if self.n:
            out.append((tr('anim_hydrogenatom_e_niveau'), '%s eV' % nombre(lumiere.niveau_ev(self.n), 3)))
        if self.journal:
            out.append((tr('anim_hydrogenatom_dernier'), self.journal[-1]))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.6) if rect.width() >= 560 else dessin.zones(rect, 2, 10.0)
        self._atome(p, dessin.cadre(p, z[0], tr('anim_hydrogenatom_titre_atome')))
        self._niveaux(p, dessin.cadre(p, z[1], tr('anim_hydrogenatom_titre_niveaux')))

    def _couleur(self, e):
        lam = lumiere.longueur_onde_nm(e)
        if 380 <= lam <= 750:
            return QColor(*lumiere.couleur_longueur_onde(lam))
        return dessin.c('arc1') if lam < 380 else dessin.c('accent3')

    def _atome(self, p, r):
        cx, cy = r.left() + r.width() * 0.4, r.center().y()
        rmax = min(r.width() * 0.38, r.height() * 0.46)
        k = rmax / N_MAX ** 2
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for n in range(1, N_MAX + 1):
            p.setPen(dessin.stylo('grille', 1.0))
            p.drawEllipse(QPointF(cx, cy), k * n * n, k * n * n)
        dessin.disque(p, cx, cy, 5, 'accent3')
        if self.n:
            a = 0.8 + self.t * 1.5 / self.n
            rr = k * self.n * self.n
            dessin.disque(p, cx + rr * math.cos(a), cy - rr * math.sin(a), 5, 'accent2', bord='texte')
        else:
            d = rmax * 1.05
            dessin.disque(p, cx + d * 0.7, cy - d * 0.7, 5, 'accent2', bord='texte')
        for ph in self.photons:
            col = self._couleur(ph['e'])
            lam_px = max(4.0, min(30.0, 8 * lumiere.longueur_onde_nm(ph['e']) / 300))
            if ph['sortant']:
                s = rmax * 1.2 * ph['t'] / VOL_S
                ang = ph['angle']
                x0, y0 = cx + s * math.cos(ang), cy - s * math.sin(ang)
                dx, dy = math.cos(ang), -math.sin(ang)
            else:
                x_dep = r.right() - 10
                s = (x_dep - cx) * (1 - ph['t'] / VOL_S)
                x0, y0, dx, dy = cx + s, cy, -1.0, 0.0
            self._onde(p, x0, y0, dx, dy, lam_px, col)

    @staticmethod
    def _onde(p, x0, y0, dx, dy, lam_px, col):
        pts = []
        nx, ny = -dy, dx
        for i in range(31):
            s = -i * 1.5
            a = 5 * math.sin(2 * math.pi * s / lam_px)
            pts.append(QPointF(x0 + dx * s + nx * a, y0 + dy * s + ny * a))
        p.setPen(dessin.stylo(col, 2.0))
        p.drawPolyline(QPolygonF(pts))

    def _niveaux(self, p, r):
        y_de = lambda e: r.top() + 12 + (r.height() - 30) * (e / -lumiere.E_IONISATION_EV)
        x0, x1 = r.left() + 40, r.right() - 10
        dessin.police(p, 0.85)
        for n in range(1, N_MAX + 1):
            y = y_de(lumiere.niveau_ev(n))
            p.setPen(dessin.stylo('accent2' if n == self.n else 'grille', 2.0 if n == self.n else 1.0))
            p.drawLine(QPointF(x0, y), QPointF(x1, y))
            if n <= 4:
                dessin.texte(p, r.left() + 4, y + 4, 'n=%d' % n, 'doux', centre=False)
                dessin.texte(p, x1 - 4 - p.fontMetrics().horizontalAdvance('%s eV' % nombre(lumiere.niveau_ev(n), 2)),
                             y - 4, '%s eV' % nombre(lumiere.niveau_ev(n), 2), 'doux', centre=False)
        y = y_de(0.0)
        p.setPen(dessin.stylo('accent3' if self.n == 0 else 'doux', 1.5, None, True))
        p.drawLine(QPointF(x0, y), QPointF(x1, y))
        dessin.texte(p, r.left() + 4, y - 4, tr('anim_hydrogenatom_ionisation'), 'doux', centre=False)
        dessin.police(p, 1 / 0.85)
