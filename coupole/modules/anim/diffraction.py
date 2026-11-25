"""Diffraction par une pupille circulaire (avec obstruction centrale) et pouvoir de résolution (sans Qt, jumeau de
``src/calc/diffraction.ts`` de Coupole Web).

Tache d'Airy d'une pupille de diamètre D à obstruction centrale de rapport ε (diamètre du miroir secondaire / D) :

    I(v) = [2 J₁(v)/v − ε² · 2 J₁(εv)/(εv)]² / (1 − ε²)²,     v = π D θ / λ,

normalisée à 1 au centre.  Premier anneau noir : v = 3,8317 (ε = 0), soit θ = 1,22 λ/D (critère de Rayleigh).
Pose longue à travers la turbulence : tache d'Airy convoluée par une gaussienne de largeur à mi-hauteur égale au
seeing (convolution radiale exacte, ou gaussienne de largeur quadratique quand le seeing écrase la diffraction).
J₁ et I₀ : approximations rationnelles classiques (Numerical Recipes, § 6.5–6.6 ; erreur < 10⁻⁷), recopiées
telles quelles en TypeScript pour que les deux applications donnent les mêmes nombres."""
from __future__ import annotations

import math

SEC_PAR_RAD = 648_000.0 / math.pi            # 206 264,806…″ par radian
V1 = 3.831_705_970_207_512                   # premier zéro de J₁
RAYLEIGH = V1 / math.pi                      # 1,219 67 : θ = RAYLEIGH λ / D
FWHM_AIRY = 1.028_993_969_962_188            # largeur à mi-hauteur de la tache d'Airy, en λ / D
GAUSS_FWHM = 2.0 * math.sqrt(2.0 * math.log(2.0))     # 2,354 82 : largeur à mi-hauteur / σ

# Instruments proposés : (clé, diamètre en m, obstruction centrale ε)
INSTRUMENTS = (
    ('oeil', 0.007, 0.0),          # pupille d'un œil adapté à l'obscurité
    ('lunette80', 0.08, 0.0),
    ('sc200', 0.2032, 0.34),       # Schmidt-Cassegrain de 8 pouces (secondaire ≈ 34 % du diamètre)
    ('m1', 1.0, 0.0),
    ('hubble', 2.4, 0.33),         # Hubble : obstruction 0,33 (modèle optique de référence du télescope)
    ('vlt', 8.2, 0.14),            # un télescope du VLT (secondaire de 1,12 m)
    ('elt', 39.3, 0.0),            # ELT : obstruction non modélisée
)


def j1(x: float) -> float:
    """Fonction de Bessel J₁ (Numerical Recipes, bessj1)."""
    ax = abs(x)
    if ax < 8.0:
        y = x * x
        a1 = x * (72362614232.0 + y * (-7895059235.0 + y * (242396853.1 + y * (-2972611.439
                                                                              + y * (15704.48260 + y * -30.16036606)))))
        a2 = 144725228442.0 + y * (2300535178.0 + y * (18583304.74 + y * (99447.43394 + y * (376.9991397 + y))))
        return a1 / a2
    z = 8.0 / ax
    y = z * z
    xx = ax - 2.356194491
    a1 = 1.0 + y * (0.183105e-2 + y * (-0.3516396496e-4 + y * (0.2457520174e-5 + y * -0.240337019e-6)))
    a2 = 0.04687499995 + y * (-0.2002690873e-3 + y * (0.8449199096e-5 + y * (-0.88228987e-6 + y * 0.105787412e-6)))
    r = math.sqrt(0.636619772 / ax) * (math.cos(xx) * a1 - z * math.sin(xx) * a2)
    return -r if x < 0 else r


def i0e(x: float) -> float:
    """I₀(x) e^(−|x|) (Numerical Recipes, bessi0, sans l'exponentielle pour ne jamais déborder)."""
    ax = abs(x)
    if ax < 3.75:
        y = (x / 3.75) ** 2
        return (1.0 + y * (3.5156229 + y * (3.0899424 + y * (1.2067492 + y * (0.2659732 + y * (0.360768e-1
                                                                                            + y * 0.45813e-2)))))) \
            * math.exp(-ax)
    y = 3.75 / ax
    return (0.39894228 + y * (0.1328592e-1 + y * (0.225319e-2 + y * (-0.157565e-2 + y * (0.916281e-2 + y * (
        -0.2057706e-1 + y * (0.2635537e-1 + y * (-0.1647633e-1 + y * 0.392377e-2)))))))) / math.sqrt(ax)


def _i0e_np(np, x):
    """i0e() sur un tableau numpy (mêmes coefficients ; x ≥ 0)."""
    x = np.asarray(x, dtype=float)
    y = (x / 3.75) ** 2
    petit = (1.0 + y * (3.5156229 + y * (3.0899424 + y * (1.2067492 + y * (0.2659732 + y * (0.360768e-1
                                                                                         + y * 0.45813e-2)))))) \
        * np.exp(-x)
    z = 3.75 / np.maximum(x, 3.75)
    grand = (0.39894228 + z * (0.1328592e-1 + z * (0.225319e-2 + z * (-0.157565e-2 + z * (0.916281e-2 + z * (
        -0.2057706e-1 + z * (0.2635537e-1 + z * (-0.1647633e-1 + z * 0.392377e-2)))))))) / np.sqrt(np.maximum(x, 3.75))
    return np.where(x < 3.75, petit, grand)


def _amplitude(v: float, eps: float) -> float:
    """2 J₁(v)/v − ε² 2 J₁(εv)/(εv), divisé par (1 − ε²) : amplitude normalisée à 1 au centre."""
    if abs(v) < 1e-9:
        return 1.0
    a = 2.0 * j1(v) / v
    if eps > 0:
        ev = eps * v
        a -= eps * eps * (2.0 * j1(ev) / ev if abs(ev) > 1e-9 else 1.0)
    return a / (1.0 - eps * eps)


def airy(v: float, eps: float = 0.0) -> float:
    """Intensité de la tache d'Airy (1 au centre) à la variable réduite v = π D θ / λ."""
    a = _amplitude(v, eps)
    return a * a


def premier_zero(eps: float = 0.0) -> float:
    """Premier zéro de l'amplitude (v) : 3,8317 sans obstruction ; l'obstruction le rapproche du centre."""
    a, b = 0.5, 0.5
    fa = _amplitude(a, eps)
    while b < 12.0:
        b = a + 0.05
        fb = _amplitude(b, eps)
        if fa > 0 >= fb:
            break
        a, fa = b, fb
    for _ in range(80):                       # dichotomie
        m = 0.5 * (a + b)
        if _amplitude(m, eps) > 0:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def theta_v(d_m: float, lam_nm: float) -> float:
    """Angle (″) qui correspond à v = 1 : λ / (π D)."""
    return lam_nm * 1e-9 / (math.pi * d_m) * SEC_PAR_RAD


def rayleigh_arcsec(d_m: float, lam_nm: float) -> float:
    """Pouvoir de résolution (critère de Rayleigh) 1,22 λ / D en secondes d'arc."""
    return RAYLEIGH * lam_nm * 1e-9 / d_m * SEC_PAR_RAD


def diametre_turbulence(seeing: float, lam_nm: float) -> float:
    """Diamètre (m) dont la tache d'Airy a la taille du seeing (1,22 λ / D = seeing) : au-delà, la turbulence
    décide de la finesse d'une pose longue."""
    return RAYLEIGH * lam_nm * 1e-9 / (seeing / SEC_PAR_RAD)


class Profil:
    """Profil radial d'une étoile (intensité en fonction de l'angle au centre, en ″), tache d'Airy convoluée par une
    gaussienne de largeur à mi-hauteur `seeing` (0 : au-dessus de l'atmosphère).  Le profil est tabulé une fois ;
    `valeur(r)` l'interpole linéairement.  Normalisation : 1 au centre d'une étoile seule."""

    N = 240

    def __init__(self, d_m: float, lam_nm: float, eps: float = 0.0, seeing: float = 0.0, r_max: float = 0.0):
        self.d, self.lam, self.eps, self.seeing = d_m, lam_nm, eps, seeing
        self.tv = theta_v(d_m, lam_nm)                     # ″ pour v = 1
        self.t1 = premier_zero(eps) * self.tv               # premier anneau noir, ″
        sigma = seeing / GAUSS_FWHM
        self.sigma = sigma
        self.r_max = r_max if r_max > 0 else 6.0 * max(self.t1, seeing)
        self.mode = 'airy' if seeing <= 0 else ('gauss' if sigma > 3.0 * self.t1 else 'convolution')
        pas = self.r_max / (self.N - 1)
        self.pas = pas
        if self.mode == 'airy':
            brut = [airy(i * pas / self.tv, eps) for i in range(self.N)]
        elif self.mode == 'gauss':
            # la turbulence écrase la diffraction : gaussienne de largeur quadratique (seeing² + FWHM_Airy²)
            fw = math.hypot(seeing, FWHM_AIRY * lam_nm * 1e-9 / d_m * SEC_PAR_RAD)
            s = fw / GAUSS_FWHM
            brut = [math.exp(-0.5 * (i * pas / s) ** 2) for i in range(self.N)]
        else:
            brut = self._convolution(sigma)
        m = brut[0] if brut[0] > 0 else 1.0
        self.table = [b / m for b in brut]

    def _convolution(self, sigma: float) -> list:
        """I(r) = ∫ P(r′) e^(−(r − r′)²/2σ²) I₀e(r r′/σ²) r′ dr′ / σ² (gaussienne 2D intégrée sur l'angle ; méthode
        des trapèzes, pas = 1/30 du premier anneau)."""
        import numpy as np
        h = self.t1 / 30.0
        n = int((self.r_max + 6.0 * sigma) / h) + 2
        rp = np.arange(n) * h
        pp = np.array([airy(x / self.tv, self.eps) for x in rp]) * rp
        s2 = sigma * sigma
        out = []
        for i in range(self.N):
            r = i * self.pas
            # la gaussienne est nulle (< e⁻¹⁸) au-delà de 6σ : seuls les points de la fenêtre comptent
            k0, k1 = max(0, int((r - 6.0 * sigma) / h)), min(n - 1, int((r + 6.0 * sigma) / h) + 1)
            x = rp[k0:k1 + 1]
            w = pp[k0:k1 + 1] * np.exp(-0.5 * (r - x) ** 2 / s2) * _i0e_np(np, r * x / s2)
            tot = float(np.sum(w)) - 0.5 * float(w[0] + w[-1])
            out.append(tot * h / s2)
        return out

    def valeur(self, r: float) -> float:
        r = abs(r)
        if r >= self.r_max:
            return 0.0
        x = r / self.pas
        i = int(x)
        f = x - i
        if i >= self.N - 1:
            return self.table[-1]
        return self.table[i] * (1.0 - f) + self.table[i + 1] * f


def coupe(profil: Profil, sep: float, rapport: float = 1.0, n: int = 241, demi: float = 0.0) -> dict:
    """Coupe le long de la droite qui joint deux étoiles séparées de `sep` (″), la seconde `rapport` fois moins
    brillante : abscisses (″, origine au milieu), intensités de chaque étoile et somme, creux (plus faible intensité
    entre les deux étoiles rapportée à la plus faible des deux, en %, ou None si la somme n'y redescend pas)."""
    demi = demi if demi > 0 else max(1.5 * sep, 2.6 * profil.t1, 1.6 * profil.seeing)
    xs = [-demi + 2.0 * demi * k / (n - 1) for k in range(n)]
    a = [profil.valeur(x + sep / 2) for x in xs]
    b = [rapport * profil.valeur(x - sep / 2) for x in xs]
    s = [u + v for u, v in zip(a, b)]
    # sommets : la somme à l'emplacement de chaque étoile ; creux : son minimum entre les deux
    ia = min(range(n), key=lambda k: abs(xs[k] + sep / 2))
    ib = min(range(n), key=lambda k: abs(xs[k] - sep / 2))
    creux = None
    if ib - ia >= 2:
        haut = min(s[ia], s[ib])
        bas = min(s[ia:ib + 1])
        if bas < 0.999 * haut:
            creux = 100.0 * bas / haut
    return {'x': xs, 'a': a, 'b': b, 'somme': s, 'creux': creux, 'demi': demi}


def creux_milieu(profil: Profil, sep: float) -> float:
    """Intensité au milieu de deux étoiles égales rapportée à celle sur l'une d'elles (en %)."""
    milieu = 2.0 * profil.valeur(sep / 2)
    pic = profil.valeur(0.0) + profil.valeur(sep)
    return 100.0 * milieu / pic


def largeur_mi_hauteur(profil: Profil) -> float:
    """Largeur à mi-hauteur (″) du profil (interpolation linéaire)."""
    t = profil.table
    for i in range(1, len(t)):
        if t[i] <= 0.5:
            f = (t[i - 1] - 0.5) / (t[i - 1] - t[i])
            return 2.0 * (i - 1 + f) * profil.pas
    return 2.0 * profil.r_max


def verdict(sep: float, d_m: float, lam_nm: float, seeing: float) -> str:
    """'separees', 'limite' ou 'confondues' selon le critère de Rayleigh, la turbulence comptée comme une tache de la
    taille du seeing (la plus grande des deux limites décide)."""
    lim = max(rayleigh_arcsec(d_m, lam_nm), seeing)
    if sep >= 1.1 * lim:
        return 'separees'
    if sep >= 0.9 * lim:
        return 'limite'
    return 'confondues'
