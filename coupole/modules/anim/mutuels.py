"""Phénomènes mutuels des satellites galiléens (sans Qt, jumeau de ``src/calc/mutuels.ts`` de Coupole Web).

Tous les six ans environ (équinoxes de Jupiter), la Terre et le Soleil passent dans le plan des orbites des satellites
galiléens : vus de la Terre, ils peuvent s'occulter l'un l'autre (« 1O2 » : Io occulte Europe) ; vus du Soleil, l'un
peut faire de l'ombre à l'autre (« 2E1 » : Europe éclipse Io).  L'éclat total des deux baisse pendant quelques
minutes : la courbe de lumière donne leurs positions à quelques kilomètres près.

Géométrie (simplifiée et dite) : orbites circulaires et coplanaires (plan de l'équateur de Jupiter), mouvement uniforme
pendant le phénomène ; observateur (la Terre) à la latitude B au-dessus de ce plan, Soleil à la même latitude et à
l'angle de phase φ ; disques uniformes (sans assombrissement centre-bord), éclat ∝ p R² (albédo géométrique p).
- Occultation : l'éclat perdu est l'aire commune des deux disques, A(d, r₁, r₂) = r₁² arccos(c₁) + r₂² arccos(c₂)
  − ½ √((−d + r₁ + r₂)(d + r₁ − r₂)(d − r₁ + r₂)(d + r₁ + r₂)), c₁ = (d² + r₁² − r₂²)/(2 d r₁)… ;
- Éclipse : vu d'un point du satellite éclipsé, le satellite actif (rayon angulaire R/ℓ, ℓ distance entre eux le long
  de la direction du Soleil) cache une part du disque solaire (rayon angulaire R☉/D) ; cette part, qui ne dépend que
  de la distance s à l'axe de l'ombre, est moyennée sur le disque éclipsé (intégrale en s, arcs de cercle) : ombre et
  pénombre.
La rencontre a lieu à l'instant 0, à l'abscisse x₀ (vue de l'observateur ou du Soleil) ; l'écart des deux centres
perpendiculairement au plan y vaut (Y_a − Y_p) sin B : il n'y a de phénomène que si |B| est petit."""
from __future__ import annotations

import math

R_JUPITER = 71_492.0                 # km (rayon équatorial)
R_SOLEIL = 695_700.0                 # km (UAI 2015)
UA = 149_597_870.7
D_JUPITER = 5.2029 * UA              # km

# satellites : clé, numéro, demi-grand axe (km), rayon (km), période (jours), albédo géométrique (NASA, fiches)
SATELLITES = (('io', 1, 421_800.0, 1821.6, 1.769_138, 0.63), ('europe', 2, 671_100.0, 1560.8, 3.551_181, 0.67),
              ('ganymede', 3, 1_070_400.0, 2631.2, 7.154_553, 0.43), ('callisto', 4, 1_882_700.0, 2410.3, 16.689_017,
                                                                        0.17))
N_SIMPSON = 32                       # intervalles de Simpson entre deux points anguleux de l'intégrande
N_COURBE = 240                       # points de la courbe de lumière


def satellite(cle: str) -> tuple:
    return next(s for s in SATELLITES if s[0] == cle)


def aire_commune(d: float, r1: float, r2: float) -> float:
    """Aire commune de deux disques de rayons r1, r2 dont les centres sont à la distance d."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        r = min(r1, r2)
        return math.pi * r * r
    c1 = max(-1.0, min(1.0, (d * d + r1 * r1 - r2 * r2) / (2.0 * d * r1)))
    c2 = max(-1.0, min(1.0, (d * d + r2 * r2 - r1 * r1) / (2.0 * d * r2)))
    k = (-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2)
    return r1 * r1 * math.acos(c1) + r2 * r2 * math.acos(c2) - 0.5 * math.sqrt(max(0.0, k))


def flux_propre(cle: str) -> float:
    s = satellite(cle)
    return s[5] * s[3] * s[3]


class Rencontre:
    """Positions des deux satellites autour de l'instant 0 de la rencontre (temps en minutes)."""

    def __init__(self, actif: str, passif: str, genre: str, b_deg: float, phase_deg: float, f_x0: float):
        self.actif, self.passif, self.genre = actif, passif, genre
        sa, sp = satellite(actif), satellite(passif)
        self.aa, self.ra, self.na = sa[2], sa[3], 2.0 * math.pi / (sa[4] * 1440.0)
        self.ap, self.rp, self.np = sp[2], sp[3], 2.0 * math.pi / (sp[4] * 1440.0)
        self.b = math.radians(b_deg)
        self.psi = math.radians(phase_deg) if genre == 'eclipse' else 0.0     # azimut de la direction de visée
        x0 = f_x0 * min(self.aa, self.ap)
        cote = 1.0 if self.aa < self.ap else -1.0        # l'actif est le plus proche du viseur (Terre ou Soleil)
        self.la0 = self._lambda(self.aa, x0, cote)
        self.lp0 = self._lambda(self.ap, x0, cote)

    def _lambda(self, a: float, x0: float, cote: float) -> float:
        # dans le repère du viseur : X = a cos λ′ = x0, Y = a sin λ′ (Y > 0 : derrière le plan du ciel)
        return math.atan2(cote * math.sqrt(max(0.0, a * a - x0 * x0)), x0) + self.psi

    def positions(self, t: float) -> tuple:
        """Positions (km) dans le plan des orbites, X à droite vu de la Terre, Y en s'éloignant d'elle."""
        la, lp = self.la0 + self.na * t, self.lp0 + self.np * t
        return (self.aa * math.cos(la), self.aa * math.sin(la)), (self.ap * math.cos(lp), self.ap * math.sin(lp))

    def ciel(self, P, psi: float) -> tuple:
        """(x, y, profondeur) vus d'une direction d'azimut ψ et de latitude B (profondeur > 0 : vers le viseur)."""
        c, s = math.cos(psi), math.sin(psi)
        X, Y = c * P[0] + s * P[1], -s * P[0] + c * P[1]
        return X, Y * math.sin(self.b), -Y * math.cos(self.b)

    def ombre(self, t: float) -> tuple:
        """(d, ℓ) : distance (km) entre l'axe de l'ombre de l'actif et le centre du passif, vus du Soleil, et distance
        entre les deux le long de la direction du Soleil (ℓ ≤ 0 : pas d'ombre)."""
        Pa, Pp = self.positions(t)
        xa, ya, za = self.ciel(Pa, self.psi)
        xp, yp, zp = self.ciel(Pp, self.psi)
        return math.hypot(xa - xp, ya - yp), za - zp

    def eclairement(self, t: float) -> float:
        """Éclairement moyen du disque passif (1 = plein Soleil).  Un point à la distance s de l'axe de l'ombre perd la
        part h(s) = A(s/ℓ, R/ℓ, ρ☉)/(π ρ☉²) du disque solaire ; les points à la distance s forment, sur le disque
        passif (rayon Rₚ, centre à d de l'axe), un arc de longueur 2s·arccos((s² + d² − Rₚ²)/(2sd)) : on intègre
        h(s) × arc en s (Simpson entre les points anguleux, variable s = u + (v − u)(1 − cos θ)/2)."""
        d, ell = self.ombre(t)
        if ell <= 0.0:
            return 1.0
        rho = R_SOLEIL / D_JUPITER
        Rp = self.rp
        s0, s1 = max(0.0, d - Rp), min(d + Rp, self.ra + ell * rho)
        if s1 <= s0:
            return 1.0
        coupures = sorted({s0, s1, *[x for x in (Rp - d, self.ra - ell * rho, self.ra + ell * rho) if s0 < x < s1]})

        def f(s):
            if s <= 0.0:
                return 0.0
            if d + s <= Rp:
                arc = 2.0 * math.pi * s
            else:
                c = max(-1.0, min(1.0, (s * s + d * d - Rp * Rp) / (2.0 * s * d)))
                arc = 2.0 * s * math.acos(c)
            return arc * aire_commune(s / ell, self.ra / ell, rho) / (math.pi * rho * rho)
        tot = 0.0
        for u, v in zip(coupures[:-1], coupures[1:]):
            # s = u + (v − u)(1 − cos θ)/2 : les racines carrées aux bornes deviennent lisses en θ
            demi = (v - u) / 2.0
            h = math.pi / N_SIMPSON
            acc = 0.0
            for k in range(1, N_SIMPSON):
                th = k * h
                acc += (4.0 if k % 2 else 2.0) * f(u + demi * (1.0 - math.cos(th))) * demi * math.sin(th)
            tot += acc * h / 3.0
        return max(0.0, 1.0 - tot / (math.pi * Rp * Rp))

    def flux(self, t: float) -> float:
        """Éclat total des deux satellites rapporté à celui d'avant le phénomène."""
        fa, fp = flux_propre(self.actif), flux_propre(self.passif)
        if self.genre == 'eclipse':
            return (fa + fp * self.eclairement(t)) / (fa + fp)
        Pa, Pp = self.positions(t)
        xa, ya, _ = self.ciel(Pa, 0.0)
        xp, yp, _ = self.ciel(Pp, 0.0)
        d = math.hypot(xa - xp, ya - yp)
        cache = aire_commune(d, self.ra, self.rp) / (math.pi * self.rp * self.rp)
        return (fa + fp * (1.0 - cache)) / (fa + fp)

    def vitesse_relative(self) -> float:
        """Vitesse relative des deux centres sur le ciel du viseur à l'instant 0 (km/min)."""
        va = self.aa * self.na
        vp = self.ap * self.np
        dla = self.la0 - self.psi
        dlp = self.lp0 - self.psi
        vxa, vya = -va * math.sin(dla), va * math.cos(dla) * math.sin(self.b)
        vxp, vyp = -vp * math.sin(dlp), vp * math.cos(dlp) * math.sin(self.b)
        return math.hypot(vxa - vxp, vya - vyp)

    def parametre_impact(self) -> float:
        """Écart des centres (km) à l'instant 0, vu du viseur."""
        Pa, Pp = self.positions(0.0)
        _, ya, _ = self.ciel(Pa, self.psi)
        _, yp, _ = self.ciel(Pp, self.psi)
        return abs(ya - yp)

    def demi_fenetre(self) -> float:
        """Demi-durée (min) de la fenêtre tracée : 1,6 fois le temps de passage, bornée à 6 h."""
        Pa, Pp = self.positions(0.0)
        ell = abs(self.ciel(Pa, self.psi)[2] - self.ciel(Pp, self.psi)[2])
        taille = self.ra + self.rp + (ell * R_SOLEIL / D_JUPITER if self.genre == 'eclipse' else 0.0)
        v = self.vitesse_relative()
        return min(360.0, 1.6 * taille / max(v, 1e-6))

    def courbe(self, n: int = N_COURBE) -> list:
        T = self.demi_fenetre()
        return [(-T + 2.0 * T * k / n, self.flux(-T + 2.0 * T * k / n)) for k in range(n + 1)]

    def b_limite(self) -> float:
        """Latitude B (°) au-delà de laquelle les disques (ou l'ombre) ne se touchent plus à cette rencontre."""
        Pa, Pp = self.positions(0.0)
        c, s = math.cos(self.psi), math.sin(self.psi)
        dY = abs((-s * Pa[0] + c * Pa[1]) - (-s * Pp[0] + c * Pp[1]))
        taille = self.ra + self.rp + (dY * R_SOLEIL / D_JUPITER if self.genre == 'eclipse' else 0.0)
        return math.degrees(math.asin(min(1.0, taille / max(dY, 1e-9))))


def resume(courbe: list) -> tuple:
    """(flux minimal, instant du minimum, durée en minutes où le flux est sous 1)."""
    fmin, tmin = min((f, t) for t, f in courbe)
    dedans = [t for t, f in courbe if f < 1.0 - 1e-9]
    duree = (dedans[-1] - dedans[0]) if dedans else 0.0
    return fmin, tmin, duree
