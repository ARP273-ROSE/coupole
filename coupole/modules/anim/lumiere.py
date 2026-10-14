"""Lumière et spectres : relations physiques exactes des animations du lot 3 (sans Qt).

Constantes du SI exactes depuis 2019 (h, c, k, e), constante de Rydberg et rapport des masses électron/proton
CODATA 2018.  Loi de Planck, loi de Wien (constante tirée de la racine de x = 5 (1 − e⁻ˣ), et non de la valeur
arrondie 2,8978 × 10⁻³ de l'original), loi de Stefan-Boltzmann (σ exacte), énergie d'un photon, niveaux de
l'atome d'hydrogène (modèle de Bohr avec masse réduite : 13,598 eV au lieu des 13,6 eV de l'original), lois de
Snell-Descartes et de Fresnel, effet Doppler d'une source en mouvement (temps retardé), couleur perçue d'un spectre
(fonctions colorimétriques CIE 1931 corrigées par Judd et Vos, sRGB de la norme IEC 61966-2-1), magnitudes dans les
filtres U, B, V, R (courbes de Landolt 1992 et points zéro de l'original)."""
from __future__ import annotations

import functools
import gzip
import json
import math
from pathlib import Path

H = 6.626_070_15e-34                 # J s (exacte)
C = 299_792_458.0                    # m/s (exacte)
KB = 1.380_649e-23                   # J/K (exacte)
EV = 1.602_176_634e-19               # J (exacte)
SIGMA = 2 * math.pi ** 5 * KB ** 4 / (15 * H ** 3 * C ** 2)      # 5,670 374 419… × 10⁻⁸ W m⁻² K⁻⁴
HC_EV_NM = H * C / EV * 1e9          # 1 239,841 98… eV nm
R_INFINI = 10_973_731.568_160        # m⁻¹ (CODATA 2018)
ME_SUR_MP = 1 / 1_836.152_673_43     # CODATA 2018


def _racine_wien() -> float:
    """x tel que x = 5 (1 − e⁻ˣ) (maximum de B_λ) : 4,965 114 231…"""
    x = 5.0
    for _ in range(60):
        f = x - 5 * (1 - math.exp(-x))
        x -= f / (1 - 5 * math.exp(-x))
    return x


X_WIEN = _racine_wien()
WIEN_B = H * C / (KB * X_WIEN)       # 2,897 771 955… × 10⁻³ m K


# ---------------------------------------------------------------- corps noir
def planck(lam_m: float, t: float) -> float:
    """Luminance spectrale B_λ(T) = 2hc² / λ⁵ / (e^(hc/λkT) − 1), en W m⁻² sr⁻¹ m⁻¹."""
    if t <= 0 or lam_m <= 0:
        return 0.0
    x = H * C / (lam_m * KB * t)
    if x > 700:
        return 0.0
    return 2 * H * C * C / lam_m ** 5 / math.expm1(x)


def pic_wien_m(t: float) -> float:
    """Longueur d'onde du maximum de B_λ : λ_max = b / T."""
    return WIEN_B / t


def temperature_de_pic(lam_m: float) -> float:
    return WIEN_B / lam_m


def exitance(t: float) -> float:
    """Puissance émise par unité de surface : σ T⁴ (W/m²)."""
    return SIGMA * t ** 4


# ---------------------------------------------------------------- photons
def energie_photon_j(lam_m: float) -> float:
    return H * C / lam_m


def frequence(lam_m: float) -> float:
    return C / lam_m


def domaine_em(lam_m: float) -> str:
    """Domaine du spectre électromagnétique (bornes de l'original : 1 pm, 1 nm, 400 nm, 750 nm, 2,5 µm, 25 µm,
    1 mm)."""
    for borne, nom in ((1e-12, 'gamma'), (1e-9, 'x'), (4e-7, 'uv'), (7.5e-7, 'visible'), (2.5e-6, 'ir_proche'),
                       (2.5e-5, 'ir'), (1e-3, 'micro_ondes')):
        if lam_m < borne:
            return nom
    return 'radio'


# ---------------------------------------------------------------- atome d'hydrogène
R_HYDROGENE = R_INFINI / (1 + ME_SUR_MP)                     # 10 967 758,34… m⁻¹
E_IONISATION_EV = H * C * R_HYDROGENE / EV                    # 13,598 43… eV


def niveau_ev(n: int) -> float:
    """Énergie du niveau n (eV), comptée depuis l'ionisation : −13,598 eV / n²."""
    return -E_IONISATION_EV / (n * n)


def transition_ev(n_bas: int, n_haut: int) -> float:
    return niveau_ev(n_haut) - niveau_ev(n_bas)


def longueur_onde_nm(energie_ev: float) -> float:
    """Longueur d'onde dans le vide d'un photon d'énergie donnée : λ = hc / E."""
    return HC_EV_NM / energie_ev


SERIES = {1: 'lyman', 2: 'balmer', 3: 'paschen', 4: 'brackett', 5: 'pfund'}


# ---------------------------------------------------------------- réfraction
def snell(theta1_deg: float, n1: float, n2: float):
    """Angle de réfraction (degrés) par n₁ sin θ₁ = n₂ sin θ₂, ou None (réflexion totale)."""
    s = n1 * math.sin(math.radians(theta1_deg)) / n2
    if abs(s) > 1:
        return None
    return math.degrees(math.asin(s))


def angle_critique(n1: float, n2: float):
    """Angle limite de réflexion totale (degrés) pour n₁ > n₂, sinon None."""
    return math.degrees(math.asin(n2 / n1)) if n1 > n2 else None


def fresnel(theta1_deg: float, n1: float, n2: float) -> dict:
    """Coefficients de réflexion en intensité (polarisations s et p, lumière naturelle : moyenne)."""
    t2 = snell(theta1_deg, n1, n2)
    if t2 is None:
        return {'rs': 1.0, 'rp': 1.0, 'r': 1.0}
    c1, c2 = math.cos(math.radians(theta1_deg)), math.cos(math.radians(t2))
    rs = ((n1 * c1 - n2 * c2) / (n1 * c1 + n2 * c2)) ** 2
    rp = ((n1 * c2 - n2 * c1) / (n1 * c2 + n2 * c1)) ** 2
    return {'rs': rs, 'rp': rp, 'r': (rs + rp) / 2}


def angle_brewster(n1: float, n2: float) -> float:
    return math.degrees(math.atan2(n2, n1))


# ---------------------------------------------------------------- effet Doppler (ondes dans un milieu)
def frequence_recue(f0: float, v_source, v_obs, direction, c: float) -> float:
    """Fréquence reçue d'une source mobile par un observateur mobile dans un milieu immobile (ondes sonores ou
    vagues) : f = f₀ (c − v_obs·u) / (c − v_src·u), u vecteur unitaire de la source vers l'observateur."""
    ux, uy = direction
    return f0 * (c - (v_obs[0] * ux + v_obs[1] * uy)) / (c - (v_source[0] * ux + v_source[1] * uy))


def temps_retarde(t: float, position_source, obs, c: float, t_min: float = -1e9) -> float:
    """Instant d'émission τ ≤ t de l'onde qui atteint l'observateur fixe `obs` à l'instant t :
    |obs − x_s(τ)| = c (t − τ) (source plus lente que l'onde), par bissection puis Newton sécante."""
    def g(tau):
        x, y = position_source(tau)
        return math.hypot(obs[0] - x, obs[1] - y) - c * (t - tau)
    hi = t
    if g(hi) <= 0:
        return t
    lo = t - 1.0
    while g(lo) > 0 and lo > t_min:
        lo = t - 2 * (t - lo)
    for _ in range(80):
        mi = (lo + hi) / 2
        if g(mi) > 0:
            hi = mi
        else:
            lo = mi
        if hi - lo < 1e-12 * max(1.0, abs(t)):
            break
    return (lo + hi) / 2


# ---------------------------------------------------------------- données spectrales
_DOSSIER = Path(__file__).with_name('donnees')


@functools.lru_cache(maxsize=None)
def spectres() -> dict:
    """Filtres U, B, V, R et transmission atmosphérique (Landolt 1992, par l'original), spectre solaire hors
    atmosphère (relatif), fonctions colorimétriques (CIE 1931 corrigées Judd-Vos, 380–825 nm, pas 5 nm), spectre de
    M32 (Santos et al. 2002)."""
    with gzip.open(_DOSSIER / 'spectres.json.gz', 'rt', encoding='utf-8') as f:
        return json.load(f)


def table(nom: str, cle: str = 't'):
    """(λ₀ en nm, pas en nm, valeurs) d'une table de spectres()."""
    d = spectres()[nom]
    return d['w0'], d.get('pas', 1), d[cle]


def valeur(nom: str, lam_nm: float, cle: str = 't') -> float:
    """Valeur interpolée linéairement (0 hors de la table)."""
    w0, pas, v = table(nom, cle)
    x = (lam_nm - w0) / pas
    i = int(math.floor(x))
    if i < 0 or i >= len(v) - 1:
        return v[-1] if i == len(v) - 1 and x == len(v) - 1 else 0.0
    f = x - i
    return v[i] * (1 - f) + v[i + 1] * f


FILTRES = ('U', 'B', 'V', 'R')


def somme_filtre(nom: str, flux) -> float:
    """Σ T(λ) F(λ) Δλ (Δλ = 1 nm, exprimé en mètres comme l'original) d'un flux F(λ en nm)."""
    w0, _, t = table('filtre_' + nom)
    return sum(ti * flux(w0 + i) for i, ti in enumerate(t)) * 1e-9


def magnitude(nom: str, flux) -> float:
    """Magnitude dans le filtre : décalage − 2,5 log₁₀ Σ T F Δλ (points zéro de l'original, étalonnés sur
    l'étoile HD 94028)."""
    s = somme_filtre(nom, flux)
    if s <= 0:
        return math.inf
    return spectres()['filtre_' + nom]['decalage'] - 2.5 * math.log10(s)


def magnitudes_corps_noir(t: float) -> dict:
    return {f: magnitude(f, lambda w: planck(w * 1e-9, t)) for f in FILTRES}


# ---------------------------------------------------------------- couleur perçue
_XYZ_VERS_RGB = ((3.240_479, -1.537_150, -0.498_535),
                 (-0.969_256, 1.875_992, 0.041_556),
                 (0.055_648, -0.204_043, 1.057_311))                    # IEC 61966-2-1 (D65)


def xyz(flux) -> tuple[float, float, float]:
    """Composantes trichromatiques X, Y, Z d'un spectre F(λ en nm) (somme au pas de 5 nm)."""
    d = spectres()['cie']
    x = y = z = 0.0
    for i in range(len(d['x'])):
        f = flux(d['w0'] + d['pas'] * i)
        x += f * d['x'][i]
        y += f * d['y'][i]
        z += f * d['z'][i]
    return x, y, z


def _gamma_srgb(u: float) -> float:
    u = max(0.0, u)
    return 12.92 * u if u <= 0.003_130_8 else 1.055 * u ** (1 / 2.4) - 0.055


def rgb_de_xyz(x: float, y: float, z: float, luminosite: float | None = None) -> tuple[int, int, int]:
    """Couleur sRGB (0–255) ; `luminosite` : si donnée, la couleur est normalisée (Y ramené à cette valeur, la
    teinte seule compte), sinon X, Y, Z sont pris tels quels (Y = 1 : blanc)."""
    if luminosite is not None and y > 0:
        k = luminosite / y
        x, y, z = x * k, y * k, z * k
    lin = [a * x + b * y + c * z for a, b, c in _XYZ_VERS_RGB]
    m = min(lin)
    if m < 0:                                     # hors du gamut : on désature vers le blanc (comme l'original)
        lin = [v - m for v in lin]
    mx = max(lin)
    if mx > 1:
        lin = [v / mx for v in lin]
    return tuple(int(round(255 * _gamma_srgb(v))) for v in lin)


@functools.lru_cache(maxsize=512)
def couleur_corps_noir(t_arrondie: int) -> tuple[int, int, int]:
    """Couleur perçue d'un corps noir (normalisée en luminosité) : rgb_de_xyz(xyz(B_λ(T)), Y = 0,85)."""
    x, y, z = xyz(lambda w: planck(w * 1e-9, t_arrondie))
    return rgb_de_xyz(x, y, z, 0.85)


def couleur_longueur_onde(lam_nm: float) -> tuple[int, int, int]:
    """Couleur approchée d'une raie monochromatique (380–780 nm), pour le dessin des spectres."""
    if lam_nm < 380 or lam_nm > 780:
        return (120, 120, 120)
    if lam_nm < 440:
        r, g, b = (440 - lam_nm) / 60, 0.0, 1.0
    elif lam_nm < 490:
        r, g, b = 0.0, (lam_nm - 440) / 50, 1.0
    elif lam_nm < 510:
        r, g, b = 0.0, 1.0, (510 - lam_nm) / 20
    elif lam_nm < 580:
        r, g, b = (lam_nm - 510) / 70, 1.0, 0.0
    elif lam_nm < 645:
        r, g, b = 1.0, (645 - lam_nm) / 65, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    f = 1.0
    if lam_nm < 420:
        f = 0.3 + 0.7 * (lam_nm - 380) / 40
    elif lam_nm > 700:
        f = 0.3 + 0.7 * (780 - lam_nm) / 80
    return tuple(int(round(255 * (v * f) ** 0.8)) for v in (r, g, b))
