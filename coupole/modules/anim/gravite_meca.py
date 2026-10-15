"""Mécanique de l'animation « Gravité et orbites » (d'après la simulation PhET Gravity and Orbits, University of
Colorado Boulder ; code propre à Coupole), sans Qt : N corps en gravitation newtonienne dans un plan, intégrés par le
schéma symplectique de Yoshida d'ordre 4 (trois « dérive – poussée » de Verlet de vitesse composées), à pas adaptatif
(une fraction η du temps dynamique de la paire la plus serrée).  Jumeau exact de src/calc/gravite.ts de Coupole Web :
mêmes opérations dans le même ordre, donc mêmes nombres au bit près (cas communs : tests/gravite_cas.json).

Constantes : G (CODATA 2018), GM☉ et GM⊕ nominaux (UAI 2015 B3), GM☾ (DE440), rayons nominaux (UAI 2015 B3) et de la
Lune (NASA), unité astronomique (UAI 2012 B2), ISS (NASA) ; vérifiées sous SageMath
(outils/verif_anim/gravite_orbites_verif.sage → tests/gravite_orbites_sage.json)."""
from __future__ import annotations

import math

G = 6.6743e-11
UA = 149597870700.0
JOUR = 86400.0
GM_SOLEIL = 1.3271244e20
GM_TERRE = 3.986004e14
GM_LUNE = 4.902800118e12
A_LUNE = 3.844e8
ALT_ISS = 415000.0

#: masses (kg)
MASSES = {'soleil': GM_SOLEIL / G, 'terre': GM_TERRE / G, 'lune': GM_LUNE / G, 'iss': 419725.0, 'comete': 1e14}
#: rayons réels (m) ; ISS : demi-envergure (109 m) ; comète : noyau de Halley (≈ 5,5 km)
RAYONS = {'soleil': 6.957e8, 'terre': 6.3781e6, 'lune': 1.7374e6, 'iss': 54.5, 'comete': 5.5e3}
#: périodes vraies (j) : année sidérale, mois sidéral (NASA)
VRAIES_J = {'terre': 365.256363, 'lune': 27.321661}

#: état réel du Soleil, de la Terre et de la Lune le 1er janvier 2026 à 0 h TDB (DE440, écliptique J2000), chaque
#: orbite ramenée dans le plan de l'écliptique par une rotation autour de sa ligne des nœuds (demi-grand axe,
#: excentricité et période gardés), le tout tourné pour que la Terre parte à droite du Soleil : [x, y, vx, vy] (m, m/s)
#: (outils/verif_anim/etat_initial_gravite.py).  Une Lune lancée sur un cercle de Kepler prendrait, dans le champ de
#: marée du Soleil, une orbite déformée de période 27,05 à 27,81 j selon la phase de départ.
ETAT_2026 = {
    'soleil': (-447268.19852799166, 7.429785804638976, 7.282139173820521e-05, -0.09207872686803291),
    'terre': (147103130738.3562, 7.429789767206905, -31.149223260146357, 30273.645476968926),
    'lune': (147402951395.03217, -201115268.94787067, 561.2687042467766, 31187.344882943245),
}

# coefficients de Yoshida (1990) d'ordre 4 : w₁ = 1 / (2 − ∛2), w₀ = −∛2 / (2 − ∛2) (SageMath)
Y_C1 = 0.6756035959798288
Y_C2 = -0.17560359597982883
Y_D1 = 1.3512071919596575
Y_D2 = -1.7024143839193153
#: fraction du temps dynamique √(r³ / G(m₁ + m₂)) prise pour pas d'intégration
ETA = 0.01
#: pas d'intégration au plus par appel de avancer() (au-delà, le temps simulé prend du retard)
MAX_PAS = 20000

SCENARIOS = ('soleil_terre', 'soleil_terre_lune', 'terre_lune', 'terre_iss', 'libre')


class Corps:
    __slots__ = ('nom', 'm', 'x', 'y', 'vx', 'vy', 'rayon', 'primaire', 'actif')

    def __init__(self, nom, m, x, y, vx, vy, rayon, primaire=-1, actif=True):
        self.nom, self.m, self.x, self.y, self.vx, self.vy = nom, m, x, y, vx, vy
        self.rayon, self.primaire, self.actif = rayon, primaire, actif

    def copie(self) -> 'Corps':
        return Corps(self.nom, self.m, self.x, self.y, self.vx, self.vy, self.rayon, self.primaire, self.actif)


def _deux(m1, m2, r):
    """Deux corps en orbite circulaire, barycentre au repos à l'origine : [x, y, vx, vy] de chacun."""
    v = math.sqrt(G * (m1 + m2) / r)
    x1 = -r * m2 / (m1 + m2)
    x2 = r * m1 / (m1 + m2)
    v1 = -v * m2 / (m1 + m2)
    v2 = v * m1 / (m1 + m2)
    return [x1, 0.0, 0.0, v1], [x2, 0.0, 0.0, v2]


def _corps(nom, s, primaire=-1) -> Corps:
    return Corps(nom, MASSES[nom], s[0], s[1], s[2], s[3], RAYONS[nom], primaire)


def recentrer(cs) -> None:
    """Quantité de mouvement totale nulle et barycentre à l'origine."""
    mt = cx = cy = px = py = 0.0
    for c in cs:
        if c.actif:
            mt += c.m
    for c in cs:
        if c.actif:
            cx += c.m * c.x
    for c in cs:
        if c.actif:
            cy += c.m * c.y
    for c in cs:
        if c.actif:
            px += c.m * c.vx
    for c in cs:
        if c.actif:
            py += c.m * c.vy
    cx /= mt
    cy /= mt
    px /= mt
    py /= mt
    for c in cs:
        c.x -= cx
        c.y -= cy
        c.vx -= px
        c.vy -= py


def scenario(nom: str) -> list:
    """Corps d'un scénario (masses nominales) : chaque couple part sur une orbite circulaire, le corps à +r sur l'axe x
    de son primaire, vitesse relative √(G (m + m_primaire) / r) selon +y (sens direct) ; le Soleil, la Terre et la Lune
    ensemble partent de leur état réel du 1er janvier 2026 (ETAT_2026) ; la comète du scénario libre part de son
    périhélie (0,6 ua) à −x vers −y (aphélie 2,4 ua)."""
    M = MASSES
    if nom == 'soleil_terre':
        a, b = _deux(M['soleil'], M['terre'], UA)
        cs = [_corps('soleil', a), _corps('terre', b, 0)]
    elif nom == 'terre_lune':
        a, b = _deux(M['terre'], M['lune'], A_LUNE)
        cs = [_corps('terre', a), _corps('lune', b, 0)]
    elif nom == 'terre_iss':
        a, b = _deux(M['terre'], M['iss'], RAYONS['terre'] + ALT_ISS)
        cs = [_corps('terre', a), _corps('iss', b, 0)]
    elif nom in ('soleil_terre_lune', 'libre'):
        cs = [_corps('soleil', ETAT_2026['soleil']), _corps('terre', ETAT_2026['terre'], 0),
              _corps('lune', ETAT_2026['lune'], 1)]
        if nom == 'libre':
            q, Q = 0.6 * UA, 2.4 * UA
            v = math.sqrt(G * (M['soleil'] + M['comete']) * (2 / q - 2 / (q + Q)))
            cs.append(_corps('comete', [-q, 0.0, 0.0, -v], 0))
    else:
        raise ValueError(nom)
    recentrer(cs)
    return cs


def accelerations(cs, gravite: bool, ax: list, ay: list) -> None:
    """Accélérations (m/s²) de tous les corps actifs ; nulles sans gravité."""
    n = len(cs)
    ax[:] = [0.0] * n
    ay[:] = [0.0] * n
    if not gravite:
        return
    for i in range(n):
        a = cs[i]
        if not a.actif:
            continue
        for j in range(i + 1, n):
            b = cs[j]
            if not b.actif:
                continue
            dx = b.x - a.x
            dy = b.y - a.y
            r2 = dx * dx + dy * dy
            r = math.sqrt(r2)
            f = G / (r2 * r)
            ax[i] = ax[i] + f * b.m * dx
            ay[i] = ay[i] + f * b.m * dy
            ax[j] = ax[j] - f * a.m * dx
            ay[j] = ay[j] - f * a.m * dy


def energie(cs) -> float:
    e = 0.0
    n = len(cs)
    for i in range(n):
        a = cs[i]
        if not a.actif:
            continue
        e += 0.5 * a.m * (a.vx * a.vx + a.vy * a.vy)
        for j in range(i + 1, n):
            b = cs[j]
            if not b.actif:
                continue
            dx = b.x - a.x
            dy = b.y - a.y
            e -= G * a.m * b.m / math.sqrt(dx * dx + dy * dy)
    return e


def moment(cs) -> float:
    """Moment cinétique total (kg·m²·s⁻¹) par rapport à l'origine."""
    l = 0.0
    for c in cs:
        if c.actif:
            l += c.m * (c.x * c.vy - c.y * c.vx)
    return l


class _Suivi:
    __slots__ = ('i', 'p', 'ux', 'uy', 'c_prec', 'sens', 'n', 't_dernier')

    def __init__(self, i, p, ux, uy):
        self.i, self.p, self.ux, self.uy = i, p, ux, uy
        self.c_prec, self.sens, self.n, self.t_dernier = 0.0, 0, 0, 0.0


class Trace:
    __slots__ = ('x', 'y', 'px', 'py')

    def __init__(self):
        self.x, self.y, self.px, self.py = [], [], [], []


class Systeme:
    """Système de N corps : état, intégration, périodes mesurées, traces, courbure de la Lune vue du Soleil."""

    def __init__(self, cs=(), pas_trace: float = JOUR):
        self.corps = []
        self.t = 0.0
        self.t0 = 0.0            # instant de départ des mesures (périodes, conservation)
        self.gravite = True
        self.e0 = 0.0
        self.l0 = 0.0
        self.suivis = []
        self.traces = []
        self.pas_trace = pas_trace
        self.t_trace = 0.0
        self.max_trace = 4000
        self.collisions = []     # (corps, sur, t)
        self.courbures = []      # rapport des courbures Lune / Terre (vues du Soleil), échantillonné avec les traces
        self.courbure_min = math.inf
        self.courbure_max = -math.inf
        self.trio = None         # indices (Soleil, Terre, Lune) quand le scénario les a tous trois
        self.derniers_pas = 0
        self._ax = []
        self._ay = []
        self.charger(list(cs))

    def charger(self, cs) -> None:
        self.corps = [c.copie() for c in cs]
        noms = [c.nom for c in self.corps]
        if all(n in noms for n in ('soleil', 'terre', 'lune')):
            self.trio = (noms.index('soleil'), noms.index('terre'), noms.index('lune'))
        else:
            self.trio = None
        self.collisions = []
        self.repartir()

    def repartir(self) -> None:
        """Nouveau départ des mesures (après un changement de l'état par l'utilisateur) ; traces effacées."""
        self.remesurer()
        self.effacer_traces()

    def remesurer(self) -> None:
        """Nouveau départ des mesures (périodes, énergie, moment cinétique), traces gardées (masse changée)."""
        self.t0 = self.t
        self.e0 = energie(self.corps)
        self.l0 = moment(self.corps)
        self.suivis = []
        for i, c in enumerate(self.corps):
            p = c.primaire
            if p < 0 or not c.actif or not self.corps[p].actif:
                continue
            rx = c.x - self.corps[p].x
            ry = c.y - self.corps[p].y
            r = math.sqrt(rx * rx + ry * ry)
            if not r > 0:
                continue
            self.suivis.append(_Suivi(i, p, rx / r, ry / r))

    def effacer_traces(self) -> None:
        self.traces = [Trace() for _ in self.corps]
        self.courbures = []
        self.courbure_min = math.inf
        self.courbure_max = -math.inf
        self.t_trace = self.t
        self._echantillonner()

    def pas(self) -> float:
        """Pas d'intégration : η × le plus court temps dynamique des paires actives (sans gravité : le pas des traces)."""
        if not self.gravite:
            return self.pas_trace
        tmin = math.inf
        cs = self.corps
        n = len(cs)
        for i in range(n):
            a = cs[i]
            if not a.actif:
                continue
            for j in range(i + 1, n):
                b = cs[j]
                if not b.actif:
                    continue
                dx = b.x - a.x
                dy = b.y - a.y
                r2 = dx * dx + dy * dy
                td = math.sqrt(r2 * math.sqrt(r2) / (G * (a.m + b.m)))
                if td < tmin:
                    tmin = td
        return self.pas_trace if tmin == math.inf else ETA * tmin

    def _deriver(self, h: float) -> None:
        for c in self.corps:
            if not c.actif:
                continue
            c.x += c.vx * h
            c.y += c.vy * h

    def _pousser(self, h: float) -> None:
        accelerations(self.corps, self.gravite, self._ax, self._ay)
        for i, c in enumerate(self.corps):
            if not c.actif:
                continue
            c.vx += self._ax[i] * h
            c.vy += self._ay[i] * h

    def yoshida(self, h: float) -> None:
        """Un pas de Yoshida d'ordre 4 (symplectique, réversible) de durée h."""
        self._deriver(Y_C1 * h)
        self._pousser(Y_D1 * h)
        self._deriver(Y_C2 * h)
        self._pousser(Y_D2 * h)
        self._deriver(Y_C2 * h)
        self._pousser(Y_D1 * h)
        self._deriver(Y_C1 * h)

    def avancer(self, duree: float) -> None:
        """Fait avancer le système de `duree` secondes (pas adaptatifs)."""
        reste = duree
        k = 0
        while reste > 0 and k < MAX_PAS:
            h = self.pas()
            if h > reste:
                h = reste
            if not h > 0:
                break
            self.yoshida(h)
            self.t += h
            reste -= h
            k += 1
            self._apres_pas(h)
        self.derniers_pas = k

    def _apres_pas(self, h: float) -> None:
        cs = self.corps
        # collisions (rayons réels) : le plus léger s'écrase, sa quantité de mouvement passe au plus lourd
        for i in range(len(cs)):
            a = cs[i]
            if not a.actif:
                continue
            for j in range(i + 1, len(cs)):
                b = cs[j]
                if not b.actif or not a.actif:
                    continue
                dx = b.x - a.x
                dy = b.y - a.y
                rr = a.rayon + b.rayon
                if dx * dx + dy * dy < rr * rr:
                    l, g = (a, b) if a.m < b.m else (b, a)
                    g.vx = (g.m * g.vx + l.m * l.vx) / g.m
                    g.vy = (g.m * g.vy + l.m * l.vy) / g.m
                    l.actif = False
                    self.collisions.append((l.nom, g.nom, self.t))
                    self.e0 = energie(cs)
                    self.l0 = moment(cs)
        # périodes : passages par la direction de départ (vue du primaire), instant interpolé dans le pas
        for s in self.suivis:
            c = cs[s.i]
            p = cs[s.p]
            if not c.actif or not p.actif:
                continue
            rx = c.x - p.x
            ry = c.y - p.y
            cr = s.ux * ry - s.uy * rx
            d = s.ux * rx + s.uy * ry
            if s.sens == 0 and cr != 0:
                s.sens = 1 if cr > 0 else -1
            if d > 0 and ((s.sens > 0 and s.c_prec < 0 <= cr) or (s.sens < 0 and s.c_prec > 0 >= cr)):
                tc = self.t - h + h * -s.c_prec / (cr - s.c_prec)
                s.n += 1
                s.t_dernier = tc - self.t0
            s.c_prec = cr
        if self.t >= self.t_trace:
            self._echantillonner()

    def _echantillonner(self) -> None:
        cs = self.corps
        for i, c in enumerate(cs):
            tr = self.traces[i] if i < len(self.traces) else None
            if tr is None or not c.actif:
                continue
            p = cs[c.primaire] if c.primaire >= 0 else c
            tr.x.append(c.x)
            tr.y.append(c.y)
            tr.px.append(p.x)
            tr.py.append(p.y)
            if len(tr.x) > self.max_trace * 1.25:
                k = len(tr.x) - self.max_trace
                del tr.x[:k], tr.y[:k], tr.px[:k], tr.py[:k]
        k = self.courbure_lune()
        if k is not None:
            self.courbures.append(k)
            if len(self.courbures) > self.max_trace * 1.25:
                del self.courbures[:len(self.courbures) - self.max_trace]
            if k < self.courbure_min:
                self.courbure_min = k
            if k > self.courbure_max:
                self.courbure_max = k
        while self.t_trace <= self.t:
            self.t_trace += self.pas_trace

    def courbure_lune(self):
        """Courbure de la trajectoire de la Lune vue du Soleil (vitesse et accélération relatives au Soleil), rapportée
        à celle de la Terre : positive = tournée du même côté (vers le Soleil).  None sans les trois corps."""
        if not self.trio or not self.gravite:
            return None
        s, t, l = self.trio
        cs = self.corps
        if not (cs[s].actif and cs[t].actif and cs[l].actif):
            return None
        ax, ay = [], []
        accelerations(cs, True, ax, ay)

        def k(i):
            vx = cs[i].vx - cs[s].vx
            vy = cs[i].vy - cs[s].vy
            gx = ax[i] - ax[s]
            gy = ay[i] - ay[s]
            v2 = vx * vx + vy * vy
            return (vx * gy - vy * gx) / (v2 * math.sqrt(v2))

        kt = k(t)
        return k(l) / kt if kt != 0 else None

    def periode(self, i: int):
        """Période mesurée (s) du corps i autour de son primaire, ou None avant le premier tour."""
        s = next((x for x in self.suivis if x.i == i), None)
        if s is None or s.n == 0:
            return None
        return s.t_dernier / s.n

    def tours(self, i: int) -> int:
        s = next((x for x in self.suivis if x.i == i), None)
        return s.n if s else 0

    def derives(self):
        """Écarts relatifs de l'énergie et du moment cinétique depuis le départ des mesures."""
        e = energie(self.corps)
        l = moment(self.corps)
        return abs((e - self.e0) / self.e0), (abs((l - self.l0) / self.l0) if self.l0 != 0 else abs(l))

    def instantane(self) -> dict:
        """Copie de l'état (pour « Retour »)."""
        return {'corps': [c.copie() for c in self.corps], 't': self.t}

    def restaurer(self, e: dict) -> None:
        self.corps = [c.copie() for c in e['corps']]
        self.t = e['t']
        self.collisions = []
        self.repartir()
