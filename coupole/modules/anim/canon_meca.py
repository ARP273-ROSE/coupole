"""Mécanique de l'animation « Le canon de Newton » (idée des Principia de Newton, 1687 ; code propre à Coupole), sans
Qt.  Jumeau exact de src/calc/canon.ts de Coupole Web : mêmes opérations dans le même ordre (cas communs :
tests/canon_cas.json, produits par outils/cas_canon.py).

Un boulet est tiré du sommet d'une montagne, sur un astre sphérique et immobile.  Le mouvement est intégré par le
moteur de « Gravité et orbites » (gravite_meca.Systeme : Yoshida d'ordre 4, pas adaptatif, collisions) : l'astre et
un boulet de masse nulle (particule d'épreuve).  L'air, en option, freine le boulet par la traînée
a = −½ ρ v |v| / B (B = m / (C_d A), coefficient balistique), ajoutée à la gravité par `Systeme.acc_sup`, avec un pas
borné par le temps de freinage.  L'impact au sol est placé exactement sur la sphère (intersection du dernier pas).
Les éléments de l'orbite (type, excentricité, apoapside, périapside, période, énergie) sont calculés
analytiquement (Kepler) à partir de la position et de la vitesse.

Constantes : G (CODATA 2018) ; Terre : GM et rayon équatorial nominaux (UAI 2015 B3) ; Lune : GM (DE440), rayon
moyen (NASA) ; Mars : GM (DE440), rayon moyen 3 389,5 km (UAI, Archinal et al. 2018) ; Cérès : GM 62,629 05 km³·s⁻²
et volume 434,13 × 10⁶ km³ (Park et al. 2019, Dawn) → rayon de la sphère de même volume ; Dimorphos : masse
4,3 × 10⁹ kg et diamètre de la sphère de même volume 151 m (Daly et al. 2023, DART).  Atmosphères : Terre, modèle
exponentiel par tranches de 0 à 1 000 km (CIRA-72, table de Vallado 2013, tableau 8-4) ; Mars : ρ₀ = 0,020 kg·m⁻³,
H = 11,1 km (NASA, Mars Fact Sheet).  Vérification : outils/verif_anim/canon_newton_verif.sage →
tests/canon_newton_sage.json."""
from __future__ import annotations

import math

from . import gravite_meca as g

G = g.G
#: astres : GM (m³·s⁻²), rayon (m), couleur du dessin
ASTRES = {
    'terre': {'gm': g.GM_TERRE, 'r': g.RAYONS['terre'], 'couleur': 'terre'},
    'lune': {'gm': g.GM_LUNE, 'r': g.RAYONS['lune'], 'couleur': 'lune'},
    'mars': {'gm': 4.2828375816e13, 'r': 3.3895e6, 'couleur': 'mars'},
    'ceres': {'gm': 6.262905e10, 'r': 4.69725e5, 'couleur': 'lune'},
    'dimorphos': {'gm': G * 4.3e9, 'r': 75.5, 'couleur': 'lune'},
}
NOMS_ASTRES = ('terre', 'lune', 'mars', 'ceres', 'dimorphos')

#: atmosphère terrestre : (altitude de base (m), densité (kg·m⁻³), hauteur d'échelle (m)) par tranche
ATM_TERRE = tuple((h * 1000.0, r, H * 1000.0) for h, r, H in (
    (0, 1.225, 7.249), (25, 3.899e-2, 6.349), (30, 1.774e-2, 6.682), (40, 3.972e-3, 7.554),
    (50, 1.057e-3, 8.382), (60, 3.206e-4, 7.714), (70, 8.770e-5, 6.549), (80, 1.905e-5, 5.799),
    (90, 3.396e-6, 5.382), (100, 5.297e-7, 5.877), (110, 9.661e-8, 7.263), (120, 2.438e-8, 9.473),
    (130, 8.484e-9, 12.636), (140, 3.845e-9, 16.149), (150, 2.070e-9, 22.523), (180, 5.464e-10, 29.740),
    (200, 2.789e-10, 37.105), (250, 7.248e-11, 45.546), (300, 2.418e-11, 53.628), (350, 9.518e-12, 53.298),
    (400, 3.725e-12, 58.515), (450, 1.585e-12, 60.828), (500, 6.967e-13, 63.822), (600, 1.454e-13, 71.835),
    (700, 3.614e-14, 88.667), (800, 1.170e-14, 124.64), (900, 5.245e-15, 181.05), (1000, 3.019e-15, 268.00)))
#: au-delà, plus d'air (ρ < 10⁻¹⁷ kg·m⁻³)
PLAFOND_TERRE = 2.5e6
#: Mars : densité au sol et hauteur d'échelle uniques
RHO_MARS = 0.020
H_MARS = 11100.0
PLAFOND_MARS = 40 * H_MARS
#: limite conventionnelle de l'espace (ligne de Kármán, FAI)
KARMAN = 100000.0
#: coefficients balistiques B = m / (C_d A) (kg·m⁻²) : boulet de fonte de 12 cm (C_d 0,47) ; capsule (≈ 5,5 t, 3,9 m,
#: C_d 1,3) ; petit satellite à panneaux solaires
BALISTIQUE = {'boulet': 1300.0, 'capsule': 350.0, 'satellite': 50.0}

#: pas d'intégration au plus par appel de avancer() (au-delà, le temps simulé prend du retard : jamais de gel)
MAX_PAS_IMAGE = 2000
#: fraction du temps de freinage v / a_frottement prise pour pas quand l'air freine
ETA_AIR = 0.02
#: fraction de la hauteur d'échelle parcourue au plus par pas, verticalement, dans l'air
ETA_H = 0.02
#: pas raccourcis pour placer l'impact (le dernier pas est refait en SOUS_PAS morceaux)
SOUS_PAS = 32
#: au-delà de LOIN × la distance de départ, un boulet libéré (parabole, hyperbole) qui s'éloigne est laissé partir
LOIN = 12.0
#: seuils de classement : excentricité d'un cercle ; |v² / v_lib² − 1| d'une parabole
TOL_CERCLE = 0.005
TOL_PARABOLE = 0.005


def atmosphere(astre: str) -> bool:
    return astre in ('terre', 'mars')


def densite(astre: str, h: float) -> float:
    """Densité de l'air (kg·m⁻³) à l'altitude h (m) ; 0 sans atmosphère ou au-dessus du plafond."""
    if astre == 'terre':
        if h > PLAFOND_TERRE:
            return 0.0
        i = len(ATM_TERRE) - 1
        while i > 0 and ATM_TERRE[i][0] > h:
            i -= 1
        h0, r0, H = ATM_TERRE[i]
        return r0 * math.exp(-(h - h0) / H)
    if astre == 'mars':
        if h > PLAFOND_MARS:
            return 0.0
        return RHO_MARS * math.exp(-h / H_MARS)
    return 0.0


def hauteur_echelle(astre: str, h: float) -> float:
    """Hauteur d'échelle locale (m) de l'air à l'altitude h ; inf sans air."""
    if astre == 'terre' and h <= PLAFOND_TERRE:
        i = len(ATM_TERRE) - 1
        while i > 0 and ATM_TERRE[i][0] > h:
            i -= 1
        return ATM_TERRE[i][2]
    if astre == 'mars' and h <= PLAFOND_MARS:
        return H_MARS
    return math.inf


def v_satellisation(mu: float, r: float) -> float:
    return math.sqrt(mu / r)


def v_liberation(mu: float, r: float) -> float:
    return math.sqrt(2 * mu / r)


def elements(mu: float, R: float, x: float, y: float, vx: float, vy: float) -> dict:
    """Éléments de la conique (Kepler) passant par (x, y) à la vitesse (vx, vy) autour d'un astre de paramètre mu et
    de rayon R : énergie spécifique, moment cinétique, excentricité, demi-grand axe, périapside, apoapside (inf si
    l'orbite est ouverte), période (nan si ouverte), type ('retombe', 'cercle', 'ellipse', 'parabole', 'hyperbole')
    et vecteur excentricité."""
    r = math.sqrt(x * x + y * y)
    v2 = vx * vx + vy * vy
    eps = 0.5 * v2 - mu / r
    hz = x * vy - y * vx
    rv = x * vx + y * vy
    ex = ((v2 - mu / r) * x - rv * vx) / mu
    ey = ((v2 - mu / r) * y - rv * vy) / mu
    e = math.sqrt(ex * ex + ey * ey)
    p = hz * hz / mu
    rp = p / (1 + e)
    if eps < 0:
        a = -mu / (2 * eps)
        ra = a * (1 + e)
        T = 2 * math.pi * math.sqrt(a * a * a / mu)
    else:
        a = -mu / (2 * eps) if eps > 0 else math.inf
        ra = math.inf
        T = math.nan
    x_lib = v2 * r / (2 * mu)            # v² / v_lib²
    if abs(x_lib - 1) < TOL_PARABOLE:
        genre = 'parabole'
    elif eps > 0:
        genre = 'hyperbole'
    elif e < TOL_CERCLE:
        genre = 'cercle'
    else:
        genre = 'ellipse'
    ouverte = genre in ('parabole', 'hyperbole')
    if rp < R and (not ouverte or rv < 0):
        genre = 'retombe'
    return {'eps': eps, 'h': hz, 'e': e, 'a': a, 'rp': rp, 'ra': ra, 'T': T, 'type': genre, 'ex': ex, 'ey': ey,
            'r': r, 'v': math.sqrt(v2), 'x_lib': x_lib}


def etat_tir(R: float, altitude: float, v: float, angle_deg: float):
    """Position et vitesse au départ : canon au sommet (0, R + altitude), tir vers la droite (+x) à angle_deg
    au-dessus de l'horizontale locale."""
    a = angle_deg * math.pi / 180
    return 0.0, R + altitude, v * math.cos(a), v * math.sin(a)


def conique(el: dict, x0: float, y0: float, R: float, r_lim: float, n: int = 240) -> list:
    """Points (x, y) de la trajectoire prévue (sans air) depuis (x0, y0), dans le sens du mouvement : un tour pour une
    ellipse, jusqu'à r_lim pour une orbite ouverte, jusqu'au sol si elle le touche (dernier point sur la sphère).
    Ellipse qui sort de r_lim : la partie au-delà est omise (None marque la coupure) et le retour est tracé."""
    mu_h = el['h']
    e = el['e']
    r0 = el['r']
    if abs(mu_h) < 1e-9 * r0 * max(el['v'], 1e-30):
        # tir vertical : aller et retour le long de la verticale
        ux, uy = x0 / r0, y0 / r0
        haut = el['ra'] if el['ra'] < r_lim else r_lim
        pts = [(ux * r0, uy * r0), (ux * haut, uy * haut)]
        if el['type'] == 'retombe':
            pts.append((ux * R, uy * R))
        return pts
    sens = 1.0 if mu_h > 0 else -1.0
    if e > 1e-12:
        ax, ay = el['ex'] / e, el['ey'] / e
    else:
        ax, ay = x0 / r0, y0 / r0
    bx, by = -ay * sens, ax * sens               # 90° plus loin dans le sens du mouvement
    nu0 = math.atan2(sens * (ax * y0 - ay * x0), ax * x0 + ay * y0)
    param = r0 * (1 + e * math.cos(nu0))        # paramètre de la conique, h² / μ
    if e < 1:
        nu1 = nu0 + 2 * math.pi
    else:
        num = math.acos(-1 / e) if e > 1 else math.pi
        c = max(-1.0, min(1.0, (param / r_lim - 1) / e))   # ν où r = r_lim, sur la branche qui s'éloigne
        nu1 = min(math.acos(c), num - 1e-6)
        if nu1 <= nu0:
            nu1 = nu0
    pts = []
    prec = None
    dehors = None                                # dernier point hors de r_lim (ellipse : on reprend au retour)
    for k in range(n + 1):
        nu = nu0 + (nu1 - nu0) * k / n
        den = 1 + e * math.cos(nu)
        if den <= 1e-12:
            break
        r = param / den
        c, s = math.cos(nu), math.sin(nu)
        x = r * (c * ax + s * bx)
        y = r * (c * ay + s * by)
        if r < R:
            if prec is not None:
                # point du sol entre le précédent et celui-ci (intersection du segment et du cercle)
                xi, yi = intersection(prec[0], prec[1], x, y, R)
                pts.append((xi, yi))
            break
        if r > r_lim:
            if e >= 1:
                pts.append((x, y))
                break
            if prec is not None:                 # sortie du cadre : point de sortie, puis coupure
                pts.append((x, y))
                pts.append(None)
                prec = None
            dehors = (x, y)
            continue
        if prec is None and dehors is not None:  # retour dans le cadre : la ligne repart du dernier point dehors
            pts.append(dehors)
        dehors = None
        pts.append((x, y))
        prec = (x, y)
    return pts


def intersection(x0: float, y0: float, x1: float, y1: float, R: float):
    """Point du segment (x0, y0)→(x1, y1) sur le cercle de rayon R (le premier en partant de (x0, y0), extérieur)."""
    dx, dy = x1 - x0, y1 - y0
    a = dx * dx + dy * dy
    b = 2 * (x0 * dx + y0 * dy)
    c = x0 * x0 + y0 * y0 - R * R
    d = b * b - 4 * a * c
    if a == 0 or d < 0:
        return x1, y1
    t = (-b - math.sqrt(d)) / (2 * a)
    t = max(0.0, min(1.0, t))
    return x0 + t * dx, y0 + t * dy


class Tir:
    """Un tir : son système (astre + boulet), sa trace, son issue ('vol', 'impact', 'libere')."""

    def __init__(self, n: int, astre: str, altitude: float, v: float, angle: float, air: bool = False,
                 projectile: str = 'boulet'):
        A = ASTRES[astre]
        self.n, self.astre, self.altitude, self.v, self.angle = n, astre, altitude, v, angle
        self.air = bool(air) and atmosphere(astre)
        self.projectile = projectile
        self.mu = A['gm']
        self.R = A['r']
        self.k_air = 0.5 / BALISTIQUE.get(projectile, BALISTIQUE['boulet'])
        x, y, vx, vy = etat_tir(self.R, altitude, v, angle)
        self.r0 = self.R + altitude
        self.el0 = elements(self.mu, self.R, x, y, vx, vy)
        planete = g.Corps(astre, self.mu / G, 0.0, 0.0, 0.0, 0.0, self.R)
        boulet = g.Corps('boulet', 0.0, x, y, vx, vy, 0.0, 0)
        self.sys = g.Systeme([planete, boulet], 1e30)
        self.sys.max_trace = 2
        if self.air:
            self.sys.acc_sup = self._frottement
        self.etat = 'vol'
        self.t_fin = math.nan
        self.phi = 0.0                       # angle balayé autour du centre dans le sens du tir (rad)
        self._theta = math.atan2(y, x)
        self.x = [x]
        self.y = [y]
        self.h_min = altitude                # altitude la plus basse atteinte
        self.v_max = v

    # ------------------------------------------------------------ air
    def _frottement(self, cs, ax, ay):
        b = cs[1]
        if not b.actif:
            return
        h = math.sqrt(b.x * b.x + b.y * b.y) - self.R
        rho = densite(self.astre, h)
        if rho <= 0:
            return
        v = math.sqrt(b.vx * b.vx + b.vy * b.vy)
        k = self.k_air * rho * v
        ax[1] = ax[1] - k * b.vx
        ay[1] = ay[1] - k * b.vy

    def freinage(self) -> float:
        """Accélération de freinage de l'air (m·s⁻²) en ce moment."""
        if not self.air:
            return 0.0
        b = self.boulet
        h = math.sqrt(b.x * b.x + b.y * b.y) - self.R
        v2 = b.vx * b.vx + b.vy * b.vy
        return self.k_air * densite(self.astre, h) * v2

    # ------------------------------------------------------------ état
    @property
    def boulet(self):
        return self.sys.corps[1]

    @property
    def t(self) -> float:
        return self.t_fin if self.etat != 'vol' and math.isfinite(self.t_fin) else self.sys.t

    def rayon(self) -> float:
        b = self.boulet
        return math.sqrt(b.x * b.x + b.y * b.y)

    def vitesse(self) -> float:
        b = self.boulet
        return math.sqrt(b.vx * b.vx + b.vy * b.vy)

    def elements(self) -> dict:
        b = self.boulet
        return elements(self.mu, self.R, b.x, b.y, b.vx, b.vy)

    def tours(self) -> int:
        return self.sys.tours(1)

    def periode(self):
        return self.sys.periode(1)

    # ------------------------------------------------------------ intégration
    def avancer(self, duree: float, budget: int = MAX_PAS_IMAGE) -> int:
        """Avance de `duree` secondes au plus (pas de Yoshida un par un) ; rend le nombre de pas faits."""
        if self.etat != 'vol':
            return 0
        reste = duree
        k = 0
        s = self.sys
        b = s.corps[1]
        while reste > 0 and k < budget:
            h = s.pas()
            if self.air:
                a = self.freinage()
                if a > 0:
                    hv = ETA_AIR * self.vitesse() / a
                    if hv < h:
                        h = hv
                    r = math.sqrt(b.x * b.x + b.y * b.y)
                    vr = abs(b.x * b.vx + b.y * b.vy) / r
                    if vr > 0:
                        hh = ETA_H * hauteur_echelle(self.astre, r - self.R) / vr
                        if hh < h:
                            h = hh
            if h > reste:
                h = reste
            if not h > 0:
                break
            x0, y0, vx0, vy0, t0 = b.x, b.y, b.vx, b.vy, s.t
            s.avancer(h)
            k += 1
            reste -= h
            if not b.actif or b.x * b.x + b.y * b.y < self.R * self.R:
                # le pas a traversé le sol : refait en SOUS_PAS morceaux, puis impact sur la sphère
                b.x, b.y, b.vx, b.vy, b.actif = x0, y0, vx0, vy0, True
                s.t = t0
                hs = h / SOUS_PAS
                for _ in range(SOUS_PAS):
                    x0, y0 = b.x, b.y
                    s.avancer(hs)
                    if not b.actif or b.x * b.x + b.y * b.y < self.R * self.R:
                        break
                    self._suivre(b.x, b.y)
                    self._noter(b.x, b.y, False)
                xi, yi = intersection(x0, y0, b.x, b.y, self.R)
                dx, dy = b.x - x0, b.y - y0
                d = math.sqrt(dx * dx + dy * dy)
                f = math.sqrt((xi - x0) * (xi - x0) + (yi - y0) * (yi - y0)) / d if d > 0 else 1.0
                b.x, b.y = xi, yi
                b.actif = False
                self.etat = 'impact'
                self.t_fin = s.t - hs + f * hs
                self._suivre(b.x, b.y)
                self._noter(b.x, b.y, True)
                self.h_min = 0.0
                break
            self._suivre(b.x, b.y)
            self._noter(b.x, b.y, False)
            r = math.sqrt(b.x * b.x + b.y * b.y)
            if r - self.R < self.h_min:
                self.h_min = r - self.R
            v = math.sqrt(b.vx * b.vx + b.vy * b.vy)
            if v > self.v_max:
                self.v_max = v
            if r > LOIN * self.r0 and b.x * b.vx + b.y * b.vy > 0:
                el = self.elements()
                if el['type'] in ('parabole', 'hyperbole'):
                    self.etat = 'libere'
                    self.t_fin = s.t
                    self._noter(b.x, b.y, True)
                    break
        return k

    def _suivre(self, x, y):
        th = math.atan2(y, x)
        d = th - self._theta
        if d > math.pi:
            d -= 2 * math.pi
        elif d < -math.pi:
            d += 2 * math.pi
        self.phi -= d                        # sens des aiguilles d'une montre : le sens d'un tir vers la droite
        self._theta = th

    def _noter(self, x, y, force: bool):
        lx, ly = self.x[-1], self.y[-1]
        r = math.sqrt(x * x + y * y)
        seuil = 0.003 * (r if r > self.R else self.R)
        if force or (x - lx) * (x - lx) + (y - ly) * (y - ly) > seuil * seuil:
            self.x.append(x)
            self.y.append(y)
            if len(self.x) > 8000:
                pair = len(self.x) % 2 == 0
                dx, dy = self.x[-1], self.y[-1]
                self.x = self.x[::2]
                self.y = self.y[::2]
                if pair:
                    self.x.append(dx)
                    self.y.append(dy)

    def angle_balaye_deg(self) -> float:
        return self.phi * 180 / math.pi

    def distance_sol(self) -> float:
        """Distance parcourue au sol depuis le pied de la montagne (m), le long du grand cercle."""
        return abs(self.phi) * self.R


# ==================================================================== réglages, préréglages, défis (communs au web)
#: par astre : vitesse (facteur m·s⁻¹ → unité affichée, unité, décimales, maximum, défaut), altitude (facteur m →
#: unité, unité, décimales, minimum, maximum, défaut, « au ras du sol »), accélération du temps conseillée
REGLAGES = {
    'terre': dict(uv=1000.0, nv='km·s⁻¹', dv=2, vmax=16.0, v0=5.0,
                  ua=1000.0, na='km', da=0, amin=1.0, amax=40000.0, a0=100.0, ras=10.0, temps=100),
    'lune': dict(uv=1000.0, nv='km·s⁻¹', dv=3, vmax=3.5, v0=1.0,
                 ua=1000.0, na='km', da=1, amin=0.1, amax=20000.0, a0=10.0, ras=2.0, temps=100),
    'mars': dict(uv=1000.0, nv='km·s⁻¹', dv=2, vmax=7.5, v0=2.5,
                 ua=1000.0, na='km', da=0, amin=1.0, amax=30000.0, a0=50.0, ras=10.0, temps=100),
    'ceres': dict(uv=1.0, nv='m·s⁻¹', dv=1, vmax=750.0, v0=200.0,
                  ua=1000.0, na='km', da=1, amin=0.1, amax=5000.0, a0=10.0, ras=2.0, temps=1000),
    'dimorphos': dict(uv=0.01, nv='cm·s⁻¹', dv=2, vmax=15.0, v0=4.0,
                      ua=1.0, na='m', da=0, amin=1.0, amax=1000.0, a0=10.0, ras=2.0, temps=1000),
}
TEMPS = (1, 10, 100, 1000)
PREREGLAGES = ('pied', 'ras_sol', 'iss', 'ellipse', 'liberation', 'hyperbole', 'rentree')
#: altitude de l'ISS (m) ; périgée visé par la rentrée (m au-dessus du sol), depuis 200 km
ALT_ISS = g.ALT_ISS
ALT_RENTREE = 200000.0
PERIGEE_RENTREE = 60000.0


def prereglage(nom: str, astre: str) -> dict:
    """Réglages d'un préréglage (en unités SI : altitude en m, vitesse en m·s⁻¹, angle en degrés) pour l'astre
    choisi ; l'ISS et la rentrée atmosphérique se passent sur Terre.  Tir horizontal : e = v² / v₁² − 1 au-delà de
    v₁ (le canon est au périgée), d'où v = √(1 + e) v₁ pour l'ellipse (e = 0,5) et l'hyperbole (e = 2)."""
    if nom in ('iss', 'rentree'):
        astre = 'terre'
    A = ASTRES[astre]
    C = REGLAGES[astre]
    alt = C['a0'] * C['ua']
    air, projectile = False, 'boulet'
    if nom == 'ras_sol':
        alt = C['ras'] * C['ua']
    elif nom == 'iss':
        alt = ALT_ISS
    elif nom == 'rentree':
        alt = ALT_RENTREE
        air, projectile = True, 'capsule'
    r0 = A['r'] + alt
    v1 = v_satellisation(A['gm'], r0)
    v = {'pied': 0.3 * v1, 'ras_sol': v1, 'iss': v1, 'ellipse': math.sqrt(1.5) * v1, 'liberation': math.sqrt(2) * v1,
         'hyperbole': math.sqrt(3) * v1}.get(nom)
    if nom == 'rentree':
        rp = A['r'] + PERIGEE_RENTREE
        v = v1 * math.sqrt(2 * rp / (r0 + rp))
    return {'astre': astre, 'altitude': alt, 'v': v, 'angle': 0.0, 'air': air, 'projectile': projectile}


DEFIS = ('aucun', 'cercle', 'liberation', 'au_dessus', 'antipodes', 'dimorphos')
#: tolérances des défis : excentricité d'une orbite « circulaire » ; dépassement de v₂ ; écart aux antipodes (°)
DEFI_E = 0.02
DEFI_LIB = 1.02
DEFI_ANTIPODES = 3.0


def contexte_defi(nom: str) -> dict:
    """Situation de départ d'un défi (astre, altitude en m, air, projectile) ; vide pour « aucun »."""
    return {'cercle': {'astre': 'terre', 'altitude': 300000.0, 'air': False, 'projectile': 'boulet'},
            'liberation': {'astre': 'lune', 'altitude': 10000.0, 'air': False, 'projectile': 'boulet'},
            'au_dessus': {'astre': 'terre', 'altitude': 60000.0, 'air': True, 'projectile': 'satellite'},
            'antipodes': {'astre': 'terre', 'altitude': 100000.0, 'air': False, 'projectile': 'boulet'},
            'dimorphos': {'astre': 'dimorphos', 'altitude': 10.0, 'air': False, 'projectile': 'boulet'}}.get(nom, {})


def juger(nom: str, tir) -> tuple:
    """Verdict d'un défi sur un tir : ('reussi' | 'echec' | 'attente' | 'aucun', clé du message, paramètres)."""
    if nom == 'aucun' or tir is None:
        return ('aucun', '', {})
    el = tir.el0
    R = tir.R
    if nom == 'cercle':
        if el['type'] == 'retombe' or tir.etat == 'impact':
            return ('echec', 'sol', {})
        if el['e'] > DEFI_E:
            return ('echec', 'e', {'e': el['e']})
        return ('reussi', 'cercle', {'e': el['e']}) if tir.tours() >= 1 else ('attente', 'tour', {})
    if nom == 'liberation':
        x = el['x_lib']
        if x < 1 - 1e-9:
            return ('echec', 'lent', {'p': 100 * (1 - math.sqrt(x))})
        if el['type'] == 'retombe' or tir.etat == 'impact':
            return ('echec', 'sol', {})
        if math.sqrt(x) > DEFI_LIB:
            return ('echec', 'rapide', {'p': 100 * (math.sqrt(x) - 1)})
        return ('reussi', 'liberation', {'p': 100 * (math.sqrt(x) - 1)}) if tir.etat == 'libere' else \
            ('attente', 'loin', {})
    if nom == 'au_dessus':
        if tir.astre != 'terre':
            return ('echec', 'astre_terre', {})
        if el['type'] in ('parabole', 'hyperbole'):
            return ('echec', 'ouverte', {})
        if el['type'] == 'retombe' or tir.etat == 'impact':
            return ('echec', 'sol_indice', {})
        hp = el['rp'] - R
        if hp <= KARMAN:
            return ('echec', 'perigee', {'h': hp})
        return ('reussi', 'au_dessus', {'h': hp}) if tir.tours() >= 1 else ('attente', 'tour', {})
    if nom == 'antipodes':
        if tir.etat == 'impact':
            d = tir.angle_balaye_deg()
            if abs(d - 180) <= DEFI_ANTIPODES:
                return ('reussi', 'antipodes', {'d': d})
            return ('echec', 'impact', {'d': d})
        if el['type'] != 'retombe':
            return ('echec', 'pas_de_chute', {})
        return ('attente', 'chute', {})
    if nom == 'dimorphos':
        if tir.astre != 'dimorphos':
            return ('echec', 'astre_dimorphos', {})
        if tir.etat == 'impact' or el['type'] == 'retombe':
            return ('echec', 'sol', {})
        if el['type'] in ('parabole', 'hyperbole'):
            return ('echec', 'ouverte', {})
        return ('reussi', 'dimorphos', {}) if tir.tours() >= 1 else ('attente', 'tour', {})
    return ('aucun', '', {})
