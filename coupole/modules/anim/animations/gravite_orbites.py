"""Gravité et orbites : d'après la simulation PhET « Gravity and Orbits » (PhET Interactive Simulations, University of
Colorado Boulder, https://phet.colorado.edu) — idée et fonctions reprises ; code, dessins et textes propres à Coupole
(aucune partie de PhET).  Le Soleil, la Terre, la Lune, la station spatiale (et une comète) en gravitation
newtonienne, intégrés par gravite_meca.py (Yoshida d'ordre 4, pas adaptatif, constantes officielles).

Deux vues : « Modèle » (astres agrandis, distance Terre–Lune agrandie, pour lire) et « À l'échelle » (tailles et
distances vraies : vus du Soleil, la Terre et la Lune ne font qu'un point), avec un passage en douceur de l'une à
l'autre (rayons et écart Terre–Lune interpolés en logarithme).  Flèches de force (bleues) et de vitesse (vertes),
trajectoires, grille avec échelle, ruban de mesure, gravité coupable, masses, astres déplaçables, vitesses à tirer,
temps en jours terrestres, pas à pas et retour, périodes mesurées comparées aux vraies, énergie et moment cinétique,
et la trajectoire de la Lune vue du Soleil (toujours tournée vers lui).  Jumeau : src/anim/animations/gravite_orbites.ts
de Coupole Web (même rendu, mêmes valeurs au caractère près)."""
from __future__ import annotations

import math
import time

from PyQt6.QtCore import QLineF, QPointF, QRectF, QTimer
from PyQt6.QtGui import QBrush, QPolygonF
from PyQt6.QtCore import Qt

from ....core.i18n import tr
from .. import dessin
from .. import gravite_meca as g
from ..base import Animation, nombre

UA = g.UA
#: par scénario : distance caractéristique D (0,44 × le plus petit côté), centre ox, secondes simulées par seconde,
#: pas et longueur des traces, rayons « Modèle » (fraction de la demi-largeur de vue), corps de référence, unité
CONF = {
    'soleil_terre': dict(D=UA, ox=0.0, rythme=10 * g.JOUR, pas_trace=0.5 * g.JOUR, max_trace=1500,
                         rmod={'soleil': 0.14, 'terre': 0.055}, ref='terre', ua=True),
    'soleil_terre_lune': dict(D=UA, ox=0.0, rythme=5 * g.JOUR, pas_trace=0.05 * g.JOUR, max_trace=8000,
                              rmod={'soleil': 0.14, 'terre': 0.055, 'lune': 0.028}, ref='terre', ua=True),
    'terre_lune': dict(D=g.A_LUNE, ox=0.0, rythme=g.JOUR, pas_trace=0.02 * g.JOUR, max_trace=3000,
                       rmod={'terre': 0.16, 'lune': 0.06}, ref='lune', ua=False),
    'terre_iss': dict(D=g.RAYONS['terre'] + g.ALT_ISS, ox=0.0, rythme=180.0, pas_trace=10.0, max_trace=1500,
                      rmod={'terre': g.RAYONS['terre'] / (g.RAYONS['terre'] + g.ALT_ISS), 'iss': 0.06}, ref='iss',
                      ua=False),
    'libre': dict(D=1.6 * UA, ox=0.9 * UA, rythme=10 * g.JOUR, pas_trace=0.1 * g.JOUR, max_trace=8000,
                  rmod={'soleil': 0.1, 'terre': 0.045, 'lune': 0.024, 'comete': 0.03}, ref='terre', ua=True),
}
ECART_LUNE = 0.2          # écart Terre–Lune dessiné en vue « Modèle » : ECART_LUNE ua (agrandi ×78)
COULEUR = {'soleil': 'soleil', 'terre': 'terre', 'lune': 'lune', 'iss': 'texte', 'comete': 'accent2'}
DUREE_TRANSITION = 0.9    # passage d'une vue à l'autre (s)
SUP = '⁰¹²³⁴⁵⁶⁷⁸⁹'
MAX_POINTS = 600          # points dessinés au plus par trace (encart : 240)



def norme(x: float, y: float) -> float:
    """√(x² + y²) calculé comme au web (math.hypot et Math.hypot n'arrondissent pas pareil)."""
    return math.sqrt(x * x + y * y)


def sci(x: float, chiffres: int = 3) -> str:
    """x en écriture scientifique (« 2,65 × 10³³ »), mêmes arrondis que nombre()."""
    if x == 0 or not math.isfinite(x):
        return nombre(x, 0)
    e = math.floor(math.log10(abs(x)))

    def mant(k):
        return x / 10 ** k if k >= 0 else x * 10 ** -k
    m = mant(e)
    if float('%.*f' % (chiffres - 1, abs(m))) >= 10:
        e += 1
        m = mant(e)
    t = nombre(m, chiffres - 1)
    if e == 0:
        return t
    return '%s × 10%s%s' % (t, '⁻' if e < 0 else '', ''.join(SUP[int(ch)] for ch in str(abs(e))))


class GraviteOrbites(Animation):
    ID = 'gravityorbits'

    def construire(self):
        self.sys = g.Systeme()
        self.sc = 'soleil_terre'
        self.depart = None
        self.t_mode = self.t_cible = 1.0
        self.k_f = []
        self.k_v = 0.0
        self.ruban = [0.0, 0.0, 0.0, 0.0]
        self.saisi = False
        self._modifie = False
        self._cam = dict(cx=0.0, cy=0.0, s=1.0, L=1.0, ox=0.0)
        self._transition = QTimer(self)
        self._transition.setInterval(16)
        self._transition.timeout.connect(self._pas_transition)
        self._t_trans = None
        self.c_scenario = self.choix('scenario', [('anim_gravityorbits_sc_' + s, s) for s in g.SCENARIOS],
                                     'soleil_terre')
        self.c_mode = self.choix('mode', [('anim_gravityorbits_mode_modele', 'modele'),
                                          ('anim_gravityorbits_mode_echelle', 'echelle')], 'modele')
        self.m_soleil = self.curseur('masse_soleil', 0.5, 2.0, 1.0, dec=2, unite='M☉')
        self.m_terre = self.curseur('masse_terre', 0.5, 2.0, 1.0, dec=2, unite='M⊕')
        self.m_lune = self.curseur('masse_lune', 0.5, 2.0, 1.0, dec=2, unite='M☾')
        self.c_force = self.coche('force', True)
        self.c_vitesse = self.coche('vecteurs_vitesse', False)
        self.c_traces = self.coche('traces', True)
        self.c_grille = self.coche('grille', False)
        self.c_ruban = self.coche('ruban', False)
        self.c_gravite = self.coche('gravite', True)
        self.c_lune_soleil = self.coche('lune_soleil', False)
        self.bouton('anim_gravityorbits_pas', lambda: self.pas(0.1))
        self.bouton('anim_gravityorbits_retour', self.retour)
        self.bouton('anim_gravityorbits_effacer', self._effacer)
        self.c_scenario.currentIndexChanged.connect(lambda *_: self.charger())
        self.c_mode.currentIndexChanged.connect(lambda *_: self._changer_vue())
        for r in (self.m_soleil, self.m_terre, self.m_lune):
            r.valueChanged.connect(lambda *_: self._appliquer_masses())
        self.c_gravite.toggled.connect(self._gravite)
        self.t_mode = self.t_cible = 0.0 if self.c_mode.currentData() == 'echelle' else 1.0
        self.charger()

    def etat_initial(self):
        self.charger()
        self._transition.stop()
        self.t_mode = self.t_cible = 0.0 if self.c_mode.currentData() == 'echelle' else 1.0

    # ------------------------------------------------------------ état
    def charger(self):
        """Charge le scénario choisi (masses des curseurs, gravité de la case)."""
        self.sc = self.c_scenario.currentData() or 'soleil_terre'
        self.depart = None
        cf = CONF[self.sc]
        cs = g.scenario(self.sc)
        self.sys = g.Systeme([], cf['pas_trace'])
        self.sys.max_trace = cf['max_trace']
        self.sys.gravite = self.c_gravite.isChecked()
        # échelles des flèches au départ (masses nominales, avec gravité)
        ax, ay = [], []
        g.accelerations(cs, True, ax, ay)
        L = 1.0
        self.k_f = []
        for i, c in enumerate(cs):
            f = c.m * math.hypot(ax[i], ay[i])
            self.k_f.append(0.22 * L / f if f > 0 else 0.0)
        ref = next(c for c in cs if c.nom == cf['ref'])
        self.k_v = 0.3 * L / math.hypot(ref.vx, ref.vy)
        p = cs[ref.primaire] if ref.primaire >= 0 else cs[0]
        self.ruban = [p.x, p.y, ref.x, ref.y]
        self.sys.charger(cs)
        self._masses()
        self.sys.remesurer()
        self.sys.effacer_traces()
        self.depart = self.sys.instantane()
        noms = {c.nom for c in cs}
        self.m_soleil.setVisible('soleil' in noms)
        self.m_terre.setVisible('terre' in noms)
        self.m_lune.setVisible('lune' in noms)
        self.c_lune_soleil.setVisible(self.sys.trio is not None)
        self.rafraichir()

    def _masses(self):
        f = {'soleil': self.m_soleil.value(), 'terre': self.m_terre.value(), 'lune': self.m_lune.value()}
        for c in self.sys.corps:
            c.m = g.MASSES[c.nom] * f.get(c.nom, 1.0)
        if self.depart:
            for c in self.depart['corps']:
                c.m = g.MASSES[c.nom] * f.get(c.nom, 1.0)

    def _appliquer_masses(self):
        self._masses()
        self.sys.remesurer()
        self.rafraichir()

    def _gravite(self, b):
        self.sys.gravite = bool(b)
        self.sys.remesurer()

    def _effacer(self):
        self.sys.effacer_traces()
        self.rafraichir()

    def retour(self):
        if self.depart:
            self.sys.restaurer(self.depart)
            self._masses()
            self.sys.remesurer()
            self.sys.effacer_traces()
        self.rafraichir()

    def basculer_lecture(self):
        if not self.en_lecture and hasattr(self, 'sys'):
            self.depart = self.sys.instantane()
        super().basculer_lecture()

    def avancer(self, dt):
        if self.saisi:
            return
        self.sys.avancer(dt * CONF[self.sc]['rythme'])

    def _changer_vue(self):
        """Passage en douceur vers la vue choisie (minuterie arrêtée une fois arrivé : aucune image de plus)."""
        self.t_cible = 0.0 if self.c_mode.currentData() == 'echelle' else 1.0
        if not self.isVisible():
            self.t_mode = self.t_cible
            self.rafraichir()
            return
        self._t_trans = time.monotonic()
        self._transition.start()

    def _pas_transition(self):
        t = time.monotonic()
        dt = min(0.25, t - (self._t_trans or t))
        self._t_trans = t
        pas = dt / DUREE_TRANSITION
        if self.t_mode < self.t_cible:
            self.t_mode = min(self.t_cible, self.t_mode + pas)
        else:
            self.t_mode = max(self.t_cible, self.t_mode - pas)
        if self.t_mode == self.t_cible:
            self._transition.stop()
        self.rafraichir()

    # ------------------------------------------------------------ géométrie de la vue
    def _lisse(self):
        t = self.t_mode
        return t * t * (3 - 2 * t)

    def _ecart(self):
        if not self.sys.trio:
            return 1.0
        kmod = ECART_LUNE * UA / g.A_LUNE
        return math.exp(self._lisse() * math.log(kmod))

    def _satellite(self, i):
        c = self.sys.corps[i]
        return c.primaire if (self.sys.trio and c.nom == 'lune') else -1

    def _vers_ecran(self, x, y):
        v = self._cam
        return v['cx'] + (x - v['ox']) * v['s'], v['cy'] - y * v['s']

    def _vers_monde(self, X, Y):
        v = self._cam
        return v['ox'] + (X - v['cx']) / v['s'], -(Y - v['cy']) / v['s']

    def _pos_dessin(self, i):
        c = self.sys.corps[i]
        p = self._satellite(i)
        if p < 0:
            return c.x, c.y
        q = self.sys.corps[p]
        k = self._ecart()
        return q.x + k * (c.x - q.x), q.y + k * (c.y - q.y)

    def _rayon(self, i):
        c = self.sys.corps[i]
        v = self._cam
        reel = c.rayon * v['s']
        mod = CONF[self.sc]['rmod'].get(c.nom, 0.03) * v['L']
        t = self._lisse()
        return max(1.5, math.exp((1 - t) * math.log(max(reel, 1e-9)) + t * math.log(mod)))

    def _nom(self, n):
        return tr('anim_gravityorbits_n_' + n)

    # ------------------------------------------------------------ souris
    def presser(self, pos, bouton) -> bool:
        cs = self.sys.corps
        px, py = pos.x(), pos.y()
        if self.c_vitesse.isChecked():
            for i in range(len(cs) - 1, -1, -1):
                if not cs[i].actif:
                    continue
                bx, by = self._vers_ecran(*self._pos_dessin(i))
                tx, ty = self._bout_vitesse(i, bx, by)
                if math.hypot(tx - bx, ty - by) > self._rayon(i) + 4 and math.hypot(px - tx, py - ty) <= 10:
                    def tirer(q, i=i):
                        c = self.sys.corps[i]
                        x0, y0 = self._vers_ecran(*self._pos_dessin(i))
                        k = self.k_v * self._cam['L']
                        c.vx = (q.x() - x0) / k
                        c.vy = -(q.y() - y0) / k
                    self._tenir(tirer)
                    return True
        if self.c_ruban.isChecked():
            for b in (0, 2):
                X, Y = self._vers_ecran(self.ruban[b], self.ruban[b + 1])
                if math.hypot(px - X, py - Y) <= 10:
                    def bout(q, b=b):
                        x, y = self._vers_monde(q.x(), q.y())
                        self.ruban[b] = x
                        self.ruban[b + 1] = y
                    self._tenir(bout, False)
                    return True
        for i in sorted(range(len(cs)), key=self._rayon):
            if not cs[i].actif:
                continue
            X, Y = self._vers_ecran(*self._pos_dessin(i))
            if math.hypot(px - X, py - Y) <= max(self._rayon(i), 9):
                self._tenir(lambda q, i=i: self._deplacer(i, q))
                return True
        return False

    def _tenir(self, f, etat=True):
        """Saisie d'un objet : le temps est suspendu jusqu'au relâcher ; `etat` : l'état des corps change."""
        self.saisi = True
        self._modifie = etat
        self._glisse = f

    def relacher(self, pos):
        super().relacher(pos)
        if self.saisi and self._modifie:
            self.sys.remesurer()
            self.sys.effacer_traces()
            self.depart = self.sys.instantane()
        self.saisi = False
        self._modifie = False
        self.rafraichir()

    def _deplacer(self, i, q):
        """Déplace le corps i sous le pointeur ; ses satellites (Lune, ISS) le suivent."""
        cs = self.sys.corps
        c = cs[i]
        x, y = self._vers_monde(q.x(), q.y())
        p = self._satellite(i)
        if p >= 0:
            k = self._ecart()
            x = cs[p].x + (x - cs[p].x) / k
            y = cs[p].y + (y - cs[p].y) / k
        if not (math.isfinite(x) and math.isfinite(y)):
            return
        dx, dy = x - c.x, y - c.y
        c.x, c.y = x, y
        for s in cs:
            if s is not c and s.primaire == i and s.nom in ('lune', 'iss'):
                s.x += dx
                s.y += dy

    def _bout_vitesse(self, i, bx, by):
        c = self.sys.corps[i]
        k = self.k_v * self._cam['L']
        dx, dy = c.vx * k, -c.vy * k
        lmax = 0.9 * self._cam['L']
        l = math.hypot(dx, dy)
        if l > lmax:
            dx *= lmax / l
            dy *= lmax / l
        return bx + dx, by + dy

    # ------------------------------------------------------------ valeurs
    def _distance(self, d):
        if CONF[self.sc]['ua'] and d >= 0.02 * UA:
            return '%s %s (%s)' % (nombre(d / UA, 4), tr('anim_gravityorbits_ua'),
                                   tr('anim_gravityorbits_millions_km', n=nombre(d / 1e9, 1)))
        return '%s km' % nombre(d / 1000, 0)

    def _duree(self, s, nom):
        if nom == 'iss':
            return '%s min' % nombre(s / 60, 1)
        return '%s %s' % (nombre(s / g.JOUR, 1 if nom == 'comete' else 2), tr('anim_gravityorbits_j'))

    def valeurs(self):
        sys_ = self.sys
        cs = sys_.corps
        out = []
        jours = tr('anim_gravityorbits_jours', n=nombre(sys_.t / g.JOUR, 4 if self.sc == 'terre_iss' else 1))
        out.append((tr('anim_gravityorbits_v_temps'),
                    '%s (%s)' % (tr('anim_gravityorbits_minutes', n=nombre(sys_.t / 60, 1)), jours)
                    if self.sc == 'terre_iss' else jours))
        for i, c in enumerate(cs):
            if c.primaire < 0 or not c.actif or not cs[c.primaire].actif:
                continue
            p = cs[c.primaire]
            a, b = self._nom(c.nom), self._nom(p.nom)
            out.append((tr('anim_gravityorbits_v_distance', a=a, b=b), self._distance(norme(c.x - p.x, c.y - p.y))))
            out.append((tr('anim_gravityorbits_v_vitesse', a=a, b=b),
                        '%s km·s⁻¹' % nombre(norme(c.vx - p.vx, c.vy - p.vy) / 1000, 2)))
            if not sys_.gravite:
                continue
            T = sys_.periode(i)
            if c.nom in g.VRAIES_J:
                Tv = g.VRAIES_J[c.nom] * g.JOUR
                ref = tr('anim_gravityorbits_v_vraie', t='%s %s' % (nombre(g.VRAIES_J[c.nom], 3),
                                                                     tr('anim_gravityorbits_j')))
            else:
                # période de Kepler de l'orbite de départ (demi-grand axe tiré de l'énergie du couple)
                Tv = self._kepler(i)
                ref = tr('anim_gravityorbits_v_kepler', t=self._duree(Tv, c.nom))
            if T is None:
                v = '— (%s) · %s' % (tr('anim_gravityorbits_v_attente'), ref)
            else:
                v = '%s · %s · %s' % (self._duree(T, c.nom), ref,
                                      tr('anim_gravityorbits_v_ecart', e=nombre(100 * abs(T - Tv) / Tv, 2)))
            out.append((tr('anim_gravityorbits_v_periode', a=a), v))
        if sys_.gravite:
            de, dl = sys_.derives()
            out.append((tr('anim_gravityorbits_v_energie'),
                        '%s J · %s' % (sci(g.energie(cs), 4), tr('anim_gravityorbits_v_derive', d=sci(de, 1)))))
            out.append((tr('anim_gravityorbits_v_moment'), sci(dl, 1)))
        else:
            out.append((tr('anim_gravityorbits_v_gravite'), tr('anim_gravityorbits_v_gravite_coupee')))
        if self.c_ruban.isChecked():
            x0, y0, x1, y1 = self.ruban
            out.append((tr('anim_gravityorbits_v_ruban'), self._distance(norme(x1 - x0, y1 - y0))))
        if self.c_lune_soleil.isChecked() and sys_.trio and sys_.courbures:
            a, b = nombre(sys_.courbure_min, 2), nombre(sys_.courbure_max, 2)
            cle = 'anim_gravityorbits_v_courbure_val' if sys_.courbure_min > 0 else 'anim_gravityorbits_v_courbure_neg'
            out.append((tr('anim_gravityorbits_v_courbure'), tr(cle, a=a, b=b)))
        for nom, sur, _t in sys_.collisions:
            out.append((tr('anim_gravityorbits_v_collision'),
                        tr('anim_gravityorbits_v_collision_val', a=self._nom(nom), b=self._nom(sur))))
        if self.t_cible == 1:
            out.append((tr('anim_gravityorbits_v_dessin'), self._agrandi()))
        return out

    def _kepler(self, i):
        """Période de Kepler (s) du corps i autour de son primaire, d'après l'état de départ (énergie du couple)."""
        d = self.depart or self.sys.instantane()
        c = d['corps'][i]
        p = d['corps'][c.primaire]
        mu = g.G * (c.m + p.m)
        r = norme(c.x - p.x, c.y - p.y)
        v2 = (c.vx - p.vx) * (c.vx - p.vx) + (c.vy - p.vy) * (c.vy - p.vy)
        a = 1 / (2 / r - v2 / mu)
        return 2 * math.pi * math.sqrt(a * a * a / mu) if a > 0 else math.nan

    def _agrandi(self):
        """« astres ×N ; distance Terre–Lune ×K » (rapports du dessin « Modèle » au vrai, indépendants de la toile)."""
        cf = CONF[self.sc]
        k = cf['rmod'].get(cf['ref'], 0.03) * (cf['D'] / g.RAYONS[cf['ref']])
        n = nombre(k, 1 if k < 10 else 0)
        if self.sc == 'terre_iss':
            return tr('anim_gravityorbits_agrandi_iss', k=n)
        if not self.sys.trio:
            return tr('anim_gravityorbits_agrandi_astres', k=n)
        return tr('anim_gravityorbits_agrandi', k=n, l=nombre(ECART_LUNE * UA / g.A_LUNE, 0))

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        titre = tr('anim_gravityorbits_titre_modele' if self.t_cible == 1 else 'anim_gravityorbits_titre_echelle')
        r = dessin.cadre(p, rect, titre)
        cf = CONF[self.sc]
        L = 0.44 * min(r.width(), r.height())
        self._cam = dict(cx=r.center().x(), cy=r.center().y(), s=L / cf['D'], L=L, ox=cf['ox'])
        p.save()
        p.setClipRect(r)
        if self.c_grille.isChecked():
            self._grille(p, r)
        if self.c_traces.isChecked():
            self._traces(p)
        self._corps(p)
        if self.c_ruban.isChecked():
            self._dessiner_ruban(p)
        p.restore()
        sys_ = self.sys
        jours = tr('anim_gravityorbits_jours', n=nombre(sys_.t / g.JOUR, 3 if self.sc == 'terre_iss' else 1))
        s = ('%s = %s' % (tr('anim_gravityorbits_minutes', n=nombre(sys_.t / 60, 1)), jours)
             if self.sc == 'terre_iss' else jours)
        w = p.fontMetrics().horizontalAdvance(s)
        dessin.texte(p, r.right() - w - 6, r.top() + 14, s, 'texte', centre=False, fond=True)
        if not sys_.gravite:
            dessin.texte(p, r.center().x(), r.top() + 14, tr('anim_gravityorbits_sans_gravite'), 'accent3', fond=True)
        if self.t_cible == 1:
            dessin.police(p, 0.85)
            m = self._agrandi()
            wm = p.fontMetrics().horizontalAdvance(m)
            dessin.texte(p, r.right() - wm - 6, r.top() + 34, m, 'doux', centre=False)
            dessin.police(p, 1 / 0.85)
        if self.c_lune_soleil.isChecked() and sys_.trio:
            self._encart(p, r)

    def _grille(self, p, r):
        cf = CONF[self.sc]
        s = self._cam['s']
        if cf['ua']:
            cands = [x * UA for x in (0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1, 2, 5)]
        else:
            cands = sorted(x for m in (1, 2, 5, 10, 20, 50, 100, 200, 500) for x in (m * 1e3, m * 1e6))
        pas = next((x for x in cands if x * s >= max(36, 0.22 * self._cam['L'])), cf['D'])
        lignes = []
        x0, _ = self._vers_monde(r.left(), 0)
        x1, _ = self._vers_monde(r.right(), 0)
        for k in range(math.ceil(x0 / pas), math.floor(x1 / pas) + 1):
            X, _ = self._vers_ecran(k * pas, 0)
            lignes.append(QLineF(X, r.top(), X, r.bottom()))
        _, y0 = self._vers_monde(0, r.bottom())
        _, y1 = self._vers_monde(0, r.top())
        for k in range(math.ceil(y0 / pas), math.floor(y1 / pas) + 1):
            _, Y = self._vers_ecran(0, k * pas)
            lignes.append(QLineF(r.left(), Y, r.right(), Y))
        p.setPen(dessin.stylo('grille', 0.7, 0.55))
        p.drawLines(lignes)
        if cf['ua']:
            d = '%s %s' % (nombre(pas / UA, 2 if pas / UA < 1 else 0), tr('anim_gravityorbits_ua'))
        else:
            d = '%s km' % nombre(pas / 1000, 0)
        dessin.police(p, 0.85)
        dessin.texte(p, r.left() + 6, r.bottom() - 6, tr('anim_gravityorbits_carreau', d=d), 'doux', centre=False,
                     fond=True)
        dessin.police(p, 1 / 0.85)

    def _traces(self, p):
        sys_ = self.sys
        k = self._ecart()
        for i, c in enumerate(sys_.corps):
            t = sys_.traces[i] if i < len(sys_.traces) else None
            if t is None or len(t.x) < 2:
                continue
            sat = self._satellite(i) >= 0
            n = len(t.x)
            pas = max(1, math.ceil(n / MAX_POINTS))
            idx = list(range(0, n, pas))
            if (n - 1) % pas:
                idx.append(n - 1)
            v = self._cam
            cx, cy, sc, ox = v['cx'], v['cy'], v['s'], v['ox']
            X, Y, PX, PY = t.x, t.y, t.px, t.py
            if sat:
                pts = [QPointF(cx + (PX[j] + k * (X[j] - PX[j]) - ox) * sc, cy - (PY[j] + k * (Y[j] - PY[j])) * sc)
                       for j in idx]
            else:
                pts = [QPointF(cx + (X[j] - ox) * sc, cy - Y[j] * sc) for j in idx]
            # 1 px : la voie rapide de Qt (un trait plus épais remplit le contour du chemin, 20 fois plus lent pour une
            # trace qui se recoupe, la Lune en vue « Modèle »)
            p.setPen(dessin.stylo(COULEUR.get(c.nom, 'texte'), 1.0, 0.55))
            p.drawPolyline(QPolygonF(pts))

    def _corps(self, p):
        sys_ = self.sys
        cs = sys_.corps
        pos = [self._vers_ecran(*self._pos_dessin(i)) for i in range(len(cs))]
        ray = [self._rayon(i) for i in range(len(cs))]
        ordre = sorted(range(len(cs)), key=lambda i: 0 if cs[i].nom == 'soleil' else 1)
        for i in ordre:
            c = cs[i]
            if not c.actif:
                continue
            X, Y = pos[i]
            rr = ray[i]
            # astre réduit à un point (à l'échelle) : un anneau discret aide à le trouver
            if rr < 3:
                p.setPen(dessin.stylo(COULEUR.get(c.nom, 'texte'), 1.0, 0.45))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(X, Y), 7, 7)
            if c.nom == 'iss':
                self._station(p, X, Y, rr)
            elif c.nom == 'comete':
                self._comete(p, X, Y, rr, cs)
            else:
                dessin.disque(p, X, Y, rr, COULEUR.get(c.nom, 'texte'))
        L = self._cam['L']
        if self.c_force.isChecked() and sys_.gravite:
            ax, ay = [], []
            g.accelerations(cs, True, ax, ay)
            for i, c in enumerate(cs):
                if not c.actif or not self.k_f[i]:
                    continue
                dx, dy = c.m * ax[i] * self.k_f[i] * L, -c.m * ay[i] * self.k_f[i] * L
                l = math.hypot(dx, dy)
                if not l >= 2:
                    continue
                if l > 0.9 * L:
                    dx *= 0.9 * L / l
                    dy *= 0.9 * L / l
                X, Y = pos[i]
                dessin.fleche(p, X, Y, X + dx, Y + dy, dessin.stylo('equateur', 2.2), 8)
        if self.c_vitesse.isChecked():
            for i, c in enumerate(cs):
                if not c.actif:
                    continue
                X, Y = pos[i]
                tx, ty = self._bout_vitesse(i, X, Y)
                if math.hypot(tx - X, ty - Y) < 2:
                    continue
                dessin.fleche(p, X, Y, tx, ty, dessin.stylo('horizon', 2.2), 8)
                if math.hypot(tx - X, ty - Y) > ray[i] + 4:
                    p.setPen(dessin.stylo('horizon', 1.4))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawEllipse(QPointF(tx, ty), 6, 6)
        trio = sys_.trio
        confondues = False
        if trio and cs[trio[1]].actif and cs[trio[2]].actif:
            a, b = pos[trio[1]], pos[trio[2]]
            confondues = math.hypot(a[0] - b[0], a[1] - b[1]) < max(ray[trio[1]], ray[trio[2]]) + 3
        for i, c in enumerate(cs):
            if not c.actif:
                continue
            if confondues and i == trio[2]:
                continue
            nom = self._nom('terre_lune') if confondues and i == trio[1] else self._nom(c.nom)
            X, Y = pos[i]
            rr = ray[i]
            if rr > 0.6 * L:
                continue                   # la Terre qui remplit la vue (ISS à l'échelle) : pas d'étiquette dessus
            dessin.etiquette(p, X + rr * 0.6, Y - rr * 0.6, nom, COULEUR.get(c.nom, 'texte'), 6)

    def _station(self, p, x, y, r):
        """La station spatiale : un module et deux ailes de panneaux solaires (un point si elle est minuscule)."""
        if r < 4:
            dessin.disque(p, x, y, max(r, 1.5), 'texte')
            return
        p.setPen(dessin.stylo('texte', 1.0))
        p.setBrush(QBrush(dessin.c('doux')))
        p.drawRect(QRectF(x - r * 0.35, y - r * 0.18, r * 0.7, r * 0.36))
        p.setBrush(QBrush(dessin.c('equateur', 0.85)))
        p.drawRect(QRectF(x - r, y - r * 0.32, r * 0.55, r * 0.64))
        p.drawRect(QRectF(x + r * 0.45, y - r * 0.32, r * 0.55, r * 0.64))
        dessin.reserver(p, x, y, r)

    def _comete(self, p, x, y, r, cs):
        """La comète : noyau et queue opposée au Soleil, d'autant plus longue qu'elle en est proche."""
        s = next((c for c in cs if c.nom == 'soleil' and c.actif), None)
        c = next(k for k in cs if k.nom == 'comete')
        if s is not None and self.sys.gravite:
            dx, dy = c.x - s.x, c.y - s.y
            d = math.hypot(dx, dy)
            l = min(0.5, 0.12 * (UA / d) ** 2) * self._cam['L'] if d > 0 else 0
            if d > 0 and l > 3:
                p.setPen(dessin.stylo('accent2', max(1.2, r * 0.8), 0.45))
                p.drawLine(QPointF(x, y), QPointF(x + dx / d * l, y - dy / d * l))
        dessin.disque(p, x, y, r, 'accent2')

    def _dessiner_ruban(self, p):
        x0, y0, x1, y1 = self.ruban
        A, B = self._vers_ecran(x0, y0), self._vers_ecran(x1, y1)
        p.setPen(dessin.stylo('accent1', 2.0))
        p.drawLine(QPointF(*A), QPointF(*B))
        p.setBrush(QBrush(dessin.c('accent1', 0.35)))
        for X, Y in (A, B):
            p.drawEllipse(QPointF(X, Y), 6, 6)
        dessin.texte(p, (A[0] + B[0]) / 2, (A[1] + B[1]) / 2 - 12, self._distance(norme(x1 - x0, y1 - y0)), 'accent1',
                     fond=True)

    def _encart(self, p, r):
        """Encart « Lune vue du Soleil » : vraie trajectoire héliocentrique de la Lune et de la Terre sur les 60
        derniers jours (même échelle en x et en y : les deux chemins se confondent, sans boucle), et le rapport des
        courbures Lune / Terre au cours du temps : toujours positif, donc toujours tourné vers le Soleil."""
        sys_ = self.sys
        i_s, i_t, i_l = sys_.trio
        ts, tt, tl = sys_.traces[i_s], sys_.traces[i_t], sys_.traces[i_l]
        etroit = r.width() < 420
        w = r.width() if etroit else max(200.0, 0.42 * r.width())
        h = max(130.0, (0.46 if etroit else 0.44) * r.height())
        R = QRectF(r.right() - w, r.bottom() - h, w, h)
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(dessin.c('fond', 0.94)))
        p.drawRoundedRect(R.adjusted(3, 3, -3, -3), 10, 10)
        p.restore()
        ri = dessin.cadre(p, R, tr('anim_gravityorbits_titre_lune_soleil'))
        n = min(len(ts.x), len(tt.x), len(tl.x))
        N = min(n, math.ceil(60 * g.JOUR / sys_.pas_trace) + 1)
        if N < 3:
            return
        haut = QRectF(ri.x(), ri.y(), ri.width(), ri.height() * 0.56)
        bas = QRectF(ri.x(), ri.y() + ri.height() * 0.6, ri.width(), ri.height() * 0.4)

        def j0(k, t):
            return len(t.x) - N + k
        m = N // 2
        ex = tt.x[j0(m, tt)] - ts.x[j0(m, ts)]
        ey = tt.y[j0(m, tt)] - ts.y[j0(m, ts)]
        a = math.atan2(ey, ex)
        ca, sa = math.cos(math.pi / 2 - a), math.sin(math.pi / 2 - a)

        def rot(t, k):
            x = t.x[j0(k, t)] - ts.x[j0(k, ts)]
            y = t.y[j0(k, t)] - ts.y[j0(k, ts)]
            return ca * x - sa * y, sa * x + ca * y
        pas = max(1, math.ceil(N / 240))
        ks = list(range(0, N, pas)) + ([N - 1] if (N - 1) % pas else [])
        pl = [rot(tl, k) for k in ks]
        pt = [rot(tt, k) for k in ks]
        xs = [x for x, _ in pl + pt]
        ys = [y for _, y in pl + pt]
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        k = min((haut.width() - 16) / max(xmax - xmin, 1), (haut.height() - 22) / max(ymax - ymin, 1))
        cx = haut.center().x() - (xmin + xmax) / 2 * k
        cy = haut.center().y() + 4 + (ymin + ymax) / 2 * k
        for pts, cle in ((pt, 'terre'), (pl, 'lune')):
            p.setPen(dessin.stylo(cle, 1.0) if cle == 'lune' else dessin.stylo(cle, 2.5, 0.5))
            p.drawPolyline(QPolygonF([QPointF(cx + x * k, cy - y * k) for x, y in pts]))
        dessin.fleche(p, haut.center().x(), haut.bottom() - 16, haut.center().x(), haut.bottom() + 2,
                      dessin.stylo('soleil', 1.6), 6)
        dessin.police(p, 0.82)
        dessin.texte(p, haut.center().x() + 8, haut.bottom() - 4, tr('anim_gravityorbits_vers_soleil'), 'soleil',
                     centre=False)
        kb = sys_.courbures[-N:][::max(1, math.ceil(N / 240))]
        if len(kb) >= 2:
            hi, lo = max(1.6, *kb), min(-0.2, *kb)

            def Y(v):
                return bas.bottom() - (v - lo) / (hi - lo) * bas.height()
            p.setPen(dessin.stylo('accent3', 1.0, 0.8, True))
            p.drawLine(QPointF(bas.left(), Y(0)), QPointF(bas.right(), Y(0)))
            p.setPen(dessin.stylo('grille', 0.8, 0.7))
            p.drawLine(QPointF(bas.left(), Y(1)), QPointF(bas.right(), Y(1)))
            p.setPen(dessin.stylo('lune', 1.0))
            p.drawPolyline(QPolygonF([QPointF(bas.left() + j / (len(kb) - 1) * bas.width(), Y(v))
                                      for j, v in enumerate(kb)]))
            dessin.texte(p, bas.left() + 2, Y(0) + 11, '0', 'accent3', centre=False)
            dessin.texte(p, bas.left() + 2, Y(1) - 3, '1', 'doux', centre=False)
            dessin.texte(p, bas.left() + 14, bas.top() + 2, tr('anim_gravityorbits_courbure_graphe'), 'lune',
                         centre=False, fond=True)
        dessin.police(p, 1 / 0.82)
