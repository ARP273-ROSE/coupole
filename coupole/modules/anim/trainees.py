"""Traînées de météoroïdes éjectés par une comète (sans Qt, jumeau de ``src/calc/trainees.ts`` de Coupole Web).

À chaque passage au périhélie, la comète lâche des grains à quelques mètres par seconde (directions au hasard, vitesses
tirées uniformément dans une boule de rayon Δv) ; la pression de radiation diminue en outre la gravité qu'ils
ressentent : GM(1 − β), avec β = 5,7 × 10⁻⁵ Q/(ρ s) (ρ en g·cm⁻³, s rayon en cm, Q ≈ 1 ; J. A. Burns, P. L. Lamy et
S. Soter, Icarus 40, 1, 1979).  Chaque grain suit sa propre orbite de Kepler autour du Soleil : leurs périodes
diffèrent un peu, ils s'étalent le long de l'orbite (une traînée par passage), puis finissent par la remplir (essaim).

La Terre croise l'essaim chaque année près du nœud de la comète : un grain passe à son nœud à la distance r_n du
Soleil, au temps τ ; la Terre y passe à la date t_E, à la distance r_E.  Les prévisions d'averses se lisent sur le
diagramme (Δt = τ − t_E, Δr = r_n − r_E) : une traînée jeune et dense qui passe près de (0, 0) donne une averse.

Modèle : deux corps (Soleil et grain), sans perturbations des planètes (en réalité Jupiter déplace les traînées et
l'orbite de la comète elle-même, ce que les modèles de prévision intègrent) ; éjection au périhélie seulement ; orbite
de la Terre képlérienne (éléments moyens J2000 de E. M. Standish, JPL) ; comète aux éléments de la base SBDB du JPL
(arrondis), gardés fixes d'un passage à l'autre ; constante de Gauss k = 0,017 202 098 95."""
from __future__ import annotations

import math

from .meteores import Aleatoire

DEUX_PI = 2.0 * math.pi
K_GAUSS = 0.017_202_098_95
GM = (K_GAUSS * 365.25) ** 2           # ua³ par an julien²
JOUR = 1.0 / 365.25                    # an
UA_KM = 149_597_870.7
MS_EN_UA_AN = 365.25 * 86_400.0 / (UA_KM * 1000.0)      # 1 m·s⁻¹ en ua par an

# Terre : éléments moyens J2000 (Standish), inclinaison négligée
A_TERRE, E_TERRE = 1.000_002_61, 0.016_711_23
VARPI_TERRE, L0_TERRE = 102.937_681_93, 100.464_571_66        # degrés
N_TERRE = 35_999.372_449_81 / 100.0                            # degrés par an julien

# comètes : clé, a (ua), e, i (°), Ω (°), ω (°), passage au périhélie (année décimale), essaim — SBDB du JPL, arrondis
COMETES = (('tempel_tuttle', 10.3383, 0.905_553, 162.487, 235.271, 172.500, 1998.1591, 'leonides'),
           ('swift_tuttle', 26.0921, 0.963_226, 113.454, 139.381, 152.982, 1992.9459, 'perseides'),
           ('fictive', 10.3383, 0.905_553, 162.487, 235.271, None, 1998.1591, 'fictif'))
# tailles des grains (rayon) et β pour ρ = 1 g·cm⁻³, Q = 1
TAILLES = (('cm', 1.0), ('mm', 0.1), ('dixieme', 0.01))
N_GRAINS = 200                          # grains par passage
ANS_APRES = 80.0                        # années suivies après le passage de référence (avant : 3,5 périodes, 240 ans au moins)
EPS_R = 0.01                            # ua : « filet » de la Terre en distance au nœud
EPS_T = 10.0                            # jours : … et en écart de date


def beta(rayon_cm: float, rho: float = 1.0) -> float:
    return 5.7e-5 / (rho * rayon_cm)


def kepler(m: float, e: float) -> float:
    E = m if e < 0.8 else math.pi
    for _ in range(60):
        d = (E - e * math.sin(E) - m) / (1.0 - e * math.cos(E))
        E -= d
        if abs(d) < 1e-13:
            break
    return E


def m_de_nu(nu: float, e: float) -> float:
    E = 2.0 * math.atan2(math.sqrt(1.0 - e) * math.sin(nu / 2.0), math.sqrt(1.0 + e) * math.cos(nu / 2.0))
    return E - e * math.sin(E)


# ------------------------------------------------------------------ la Terre
def r_terre(lam_deg: float) -> float:
    nu = math.radians(lam_deg - VARPI_TERRE)
    return A_TERRE * (1.0 - E_TERRE ** 2) / (1.0 + E_TERRE * math.cos(nu))


def date_terre(lam_deg: float, annee: int) -> float:
    """Date (année décimale) où la Terre passe à la longitude héliocentrique vraie λ, dans l'année civile donnée."""
    m = math.degrees(m_de_nu(math.radians(lam_deg - VARPI_TERRE), E_TERRE))
    L = (m + VARPI_TERRE - L0_TERRE) % 360.0
    t = 2000.0 + L / N_TERRE
    an = 360.0 / N_TERRE
    t += math.floor((annee - t) / an) * an
    while t < annee:
        t += an
    while t >= annee + 1.0:
        t -= an
    return t


# ------------------------------------------------------------------ orbites
class Orbite:
    """Orbite képlérienne (μ en ua³/an²) : éléments en radians, anomalie moyenne m0 à la date t0."""

    __slots__ = ('a', 'e', 'i', 'o', 'w', 'm0', 't0', 'n', 'mu', 'p', '_mat')

    def __init__(self, a, e, i, o, w, m0, t0, mu=GM):
        self.a, self.e, self.i, self.o, self.w, self.m0, self.t0, self.mu = a, e, i, o, w, m0, t0, mu
        self.n = math.sqrt(mu / a ** 3)
        self.p = a * (1.0 - e * e)
        co, so, ci, si, cw, sw = math.cos(o), math.sin(o), math.cos(i), math.sin(i), math.cos(w), math.sin(w)
        self._mat = (co * cw - so * sw * ci, -co * sw - so * cw * ci, so * cw + co * sw * ci, -so * sw + co * cw * ci,
                     sw * si, cw * si)

    def periode(self) -> float:
        return DEUX_PI / self.n

    def etat(self, t: float):
        """Position et vitesse (ua, ua/an) à la date t."""
        e = self.e
        E = kepler((self.m0 + self.n * (t - self.t0)) % DEUX_PI, e)
        cE, sE = math.cos(E), math.sin(E)
        b = math.sqrt(1.0 - e * e)
        xo, yo = self.a * (cE - e), self.a * b * sE
        f = self.n * self.a / (1.0 - e * cE)
        vxo, vyo = -f * sE, f * b * cE
        m = self._mat
        return ((m[0] * xo + m[1] * yo, m[2] * xo + m[3] * yo, m[4] * xo + m[5] * yo),
                (m[0] * vxo + m[1] * vyo, m[2] * vxo + m[3] * vyo, m[4] * vxo + m[5] * vyo))

    def position(self, t: float):
        e = self.e
        E = kepler((self.m0 + self.n * (t - self.t0)) % DEUX_PI, e)
        xo, yo = self.a * (math.cos(E) - e), self.a * math.sqrt(1.0 - e * e) * math.sin(E)
        m = self._mat
        return m[0] * xo + m[1] * yo, m[2] * xo + m[3] * yo, m[4] * xo + m[5] * yo


def orbite_de(r, v, t: float, mu: float):
    """Orbite képlérienne passant par (r, v) à la date t, ou None si elle n'est pas fermée."""
    x, y, z = r
    vx, vy, vz = v
    rn = math.sqrt(x * x + y * y + z * z)
    v2 = vx * vx + vy * vy + vz * vz
    en = v2 / 2.0 - mu / rn
    if en >= 0.0:
        return None
    a = -mu / (2.0 * en)
    hx, hy, hz = y * vz - z * vy, z * vx - x * vz, x * vy - y * vx
    h = math.sqrt(hx * hx + hy * hy + hz * hz)
    i = math.acos(max(-1.0, min(1.0, hz / h)))
    o = math.atan2(hx, -hy)
    rv = x * vx + y * vy + z * vz
    ex = ((v2 - mu / rn) * x - rv * vx) / mu
    ey = ((v2 - mu / rn) * y - rv * vy) / mu
    ez = ((v2 - mu / rn) * z - rv * vz) / mu
    e = math.sqrt(ex * ex + ey * ey + ez * ez)
    # argument du périhélie : angle du nœud ascendant (n = (cos Ω, sin Ω, 0)) au vecteur excentricité
    nx, ny = math.cos(o), math.sin(o)
    cw = (nx * ex + ny * ey) / e
    sw = (ny * ez * hx - nx * ez * hy + (nx * ey - ny * ex) * hz) / (h * e)
    w = math.atan2(sw, cw)
    # anomalie vraie
    cnu = (ex * x + ey * y + ez * z) / (e * rn)
    nu = math.acos(max(-1.0, min(1.0, cnu)))
    if rv < 0.0:
        nu = DEUX_PI - nu
    return Orbite(a, e, i, o, w, m_de_nu(nu, e) % DEUX_PI, t, mu)


def comete(cle: str) -> tuple:
    c = next(x for x in COMETES if x[0] == cle)
    if c[5] is None:                      # comète fictive : ω tourné pour que le nœud descendant soit sur l'orbite
        a, e, o = c[1], c[2], c[4]
        rE = r_terre(o + 180.0)
        w = math.degrees(math.acos((1.0 - a * (1.0 - e * e) / rE) / e))
        c = c[:5] + (w,) + c[6:]
    return c


def orbite_comete(cle: str) -> Orbite:
    _, a, e, i, o, w, tp, _ = comete(cle)
    return Orbite(a, e, math.radians(i), math.radians(o), math.radians(w), 0.0, tp)


def noeud(orb: Orbite, genre: str) -> tuple:
    """(r_n, λ_n en degrés, anomalie moyenne au nœud) pour le nœud 'asc' ou 'desc'."""
    nu = -orb.w if genre == 'asc' else math.pi - orb.w
    r = orb.p / (1.0 + orb.e * math.cos(nu))
    lam = math.degrees(orb.o) + (0.0 if genre == 'asc' else 180.0)
    return r, lam % 360.0, m_de_nu(nu, orb.e) % DEUX_PI


def noeud_terrestre(orb: Orbite) -> str:
    """Le nœud le plus proche de l'orbite terrestre."""
    best = None
    for g in ('asc', 'desc'):
        r, lam, _ = noeud(orb, g)
        d = abs(r - r_terre(lam))
        if best is None or d < best[0]:
            best = (d, g)
    return best[1]


def passages(orb: Orbite, t0: float, t1: float) -> list:
    P = orb.periode()
    k = math.ceil((t0 - orb.t0) / P)
    out = []
    while orb.t0 + k * P <= t1:
        out.append(orb.t0 + k * P)
        k += 1
    return out


def fenetre(cle: str) -> tuple[int, int]:
    """Années suivies : de 3,5 périodes (240 ans au moins) avant le passage de référence à 80 ans après."""
    tp = comete(cle)[6]
    P = orbite_comete(cle).periode()
    return int(math.floor(tp - max(240.0, 3.5 * P))), int(math.floor(tp + ANS_APRES))


def ejecter(orb: Orbite, t: float, dv_ms: float, b: float, n: int = N_GRAINS, graine: int = 1) -> list:
    """Orbites des n grains lâchés à la date t (au périhélie) ; None pour un grain qui s'échappe."""
    g = Aleatoire(graine)
    r, v = orb.etat(t)
    mu = GM * (1.0 - b)
    out = []
    for _ in range(n):
        cz = 2.0 * g() - 1.0
        ph = DEUX_PI * g()
        s = dv_ms * MS_EN_UA_AN * g() ** (1.0 / 3.0)
        sz = math.sqrt(max(0.0, 1.0 - cz * cz))
        dv = (s * sz * math.cos(ph), s * sz * math.sin(ph), s * cz)
        out.append(orbite_de(r, (v[0] + dv[0], v[1] + dv[1], v[2] + dv[2]), t, mu))
    return out


class Essaim:
    """Grains de chaque passage entre debut et fin ; nœud suivi : celui de la comète le plus proche de la Terre."""

    def __init__(self, cle: str, dv_ms: float, taille: str, debut: float, fin: float):
        self.comete = orbite_comete(cle)
        self.genre = noeud_terrestre(self.comete)
        b = beta(dict(TAILLES)[taille])
        self.beta = b
        self.ejections = passages(self.comete, debut, fin)
        self.traines = []
        for k, tk in enumerate(self.ejections):
            grains = [o for o in ejecter(self.comete, tk, dv_ms, b, graine=1000 + k) if o is not None]
            noeuds = []
            for o in grains:
                r, lam, mn = noeud(o, self.genre)
                tau0 = tk + ((mn - o.m0) % DEUX_PI) / o.n
                noeuds.append((r, lam, tau0, o.periode()))
            self.traines.append((tk, grains, noeuds))

    def ecarts(self, annee: int) -> list:
        """Pour l'année donnée : [(Δt en jours, Δr en ua, numéro de la traînée)] des grains déjà lâchés."""
        out = []
        for k, (tk, _, noeuds) in enumerate(self.traines):
            for r, lam, tau0, P in noeuds:
                tE = date_terre(lam, annee)
                if tE <= tk:
                    continue
                j = max(0, round((tE - tau0) / P))
                out.append(((tau0 + j * P - tE) * 365.25, r - r_terre(lam), k))
        return out

    def activite(self, a0: int, a1: int) -> dict:
        """Nombre de grains « dans le filet » (|Δr| < EPS_R, |Δt| < EPS_T) par année, de a0 à a1 inclus."""
        out = {y: 0 for y in range(a0, a1 + 1)}
        for tk, _, noeuds in self.traines:
            for r, lam, tau0, P in noeuds:
                if abs(r - r_terre(lam)) >= EPS_R:
                    continue
                tE0 = date_terre(lam, a0)
                an = 360.0 / N_TERRE
                j = 0
                while tau0 + j * P <= a1 + 1.0:
                    tau = tau0 + j * P
                    y = round((tau - tE0) / an)
                    if 0 <= y <= a1 - a0 and abs(tau - (tE0 + y * an)) * 365.25 < EPS_T and tE0 + y * an > tk:
                        out[a0 + y] += 1
                    j += 1
        return out


def terre(t: float) -> tuple[float, float]:
    """Position (x, y) de la Terre dans l'écliptique (ua) à la date t (année décimale)."""
    m = math.radians((L0_TERRE + N_TERRE * (t - 2000.0) - VARPI_TERRE) % 360.0)
    E = kepler(m, E_TERRE)
    nu = 2.0 * math.atan2(math.sqrt(1.0 + E_TERRE) * math.sin(E / 2.0), math.sqrt(1.0 - E_TERRE) * math.cos(E / 2.0))
    lam = nu + math.radians(VARPI_TERRE)
    r = A_TERRE * (1.0 - E_TERRE * math.cos(E))
    return r * math.cos(lam), r * math.sin(lam)
