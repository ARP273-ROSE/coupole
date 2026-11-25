"""Interférences et interférométrie (sans Qt, jumeau de ``src/calc/interferometrie.ts`` de Coupole Web).

Deux ouvertures de diamètre d, séparées d'une base B, reçoivent la lumière d'une étoile : les deux faisceaux
recombinés donnent des franges d'interférence d'interfrange angulaire λ / B (l'expérience des fentes d'Young, avec
une étoile pour source).  Chaque ouverture, seule, ne résout que 1,22 λ / d : les franges sont modulées par sa tache
d'Airy.  Le contraste des franges, la visibilité V, est le module de la transformée de Fourier de la répartition
d'éclat de la source, prise à la fréquence spatiale B / λ (théorème de Zernike et van Cittert) :

- étoile non résolue : V = 1 ;
- disque uniforme de diamètre θ : V = |2 J₁(x) / x|, x = π θ B / λ ; premier zéro pour B = 1,22 λ / θ (c'est ainsi
  que Michelson et Pease ont mesuré Bételgeuse en 1920) ; au-delà, la phase des franges est retournée ;
- couple de deux étoiles séparées de ρ le long de la base, rapport de flux r : V = |1 + r e^(−2iπ B ρ / λ)| / (1 + r),
  minimum (1 − r) / (1 + r) pour B = λ / (2ρ).

Coupe des franges : I(α) = A(α) [1 + V cos(2π B α / λ − φ)], où A est la tache d'Airy d'une ouverture (on la
suppose plus large que la source, θ ≪ λ / d).

Anneaux de Newton : une lentille plan-convexe de rayon de courbure R posée sur une lame de verre laisse entre elles
une lame d'air (ou d'un liquide d'indice n) d'épaisseur e(r) = r²/(2R) à la distance r du contact (r ≪ R).  En
réflexion, les ondes réfléchies sur les deux faces de la lame diffèrent de 2ne + λ/2 (déphasage de π à la réflexion
sur le verre, plus réfringent) : I = (1 − cos(4π n e / λ))/2, centre noir, anneaux sombres à r_k = √(kλR/n) ; en
transmission, la figure complémentaire.  En lumière blanche, chaque λ donne ses anneaux : teintes de Newton."""
from __future__ import annotations

import cmath
import functools
import math

from .diffraction import RAYLEIGH, SEC_PAR_RAD, airy, j1

MAS_PAR_RAD = SEC_PAR_RAD * 1000.0

# instruments : clé → (base B en m, diamètre d'une ouverture d en m)
INSTRUMENTS = (
    ('young', 0.0005, 0.0001),           # fentes d'Young : 0,5 mm d'écart, 0,1 mm de large
    ('michelson', 6.1, 0.15),            # interféromètre stellaire de Michelson et Pease (1920, mont Wilson)
    ('vlti_ut', 130.0, 8.2),             # VLTI, deux télescopes de 8,2 m
    ('vlti_at', 200.0, 1.8),             # VLTI, télescopes auxiliaires de 1,8 m
    ('chara', 331.0, 1.0),               # CHARA (mont Wilson), télescopes de 1 m
)

# objets : clé → (genre, taille en mas (diamètre ou séparation), Δm)
OBJETS = (
    ('point', 'point', 0.0, 0.0),
    ('disque', 'disque', 5.0, 0.0),
    ('couple', 'couple', 20.0, 0.0),
    ('betelgeuse', 'disque', 47.0, 0.0),   # Michelson et Pease 1921 : 0,047″ (disque uniforme, vers 575 nm)
    ('sirius', 'disque', 6.0, 0.0),        # Sirius A : 6,0 mas
    ('capella', 'couple', 56.0, 0.1),      # Capella : demi-grand axe 56 mas, composantes presque égales
)


def rad_de_mas(x: float) -> float:
    return x / MAS_PAR_RAD


def interfrange_mas(b_m: float, lam_nm: float) -> float:
    """Interfrange angulaire λ / B, en millisecondes d'arc."""
    return lam_nm * 1e-9 / b_m * MAS_PAR_RAD


def resolution_mas(d_m: float, lam_nm: float) -> float:
    """Pouvoir de résolution d'une ouverture seule, 1,22 λ / d, en millisecondes d'arc."""
    return RAYLEIGH * lam_nm * 1e-9 / d_m * MAS_PAR_RAD


def visibilite_complexe(genre: str, taille_mas: float, b_m: float, lam_nm: float, rapport: float = 1.0) -> complex:
    """Visibilité complexe normalisée (module = contraste des franges, argument = décalage des franges)."""
    u = b_m / (lam_nm * 1e-9)                       # fréquence spatiale, en cycles par radian
    t = rad_de_mas(taille_mas)
    if genre == 'disque':
        x = math.pi * t * u
        return complex(1.0 if x < 1e-8 else 2.0 * j1(x) / x, 0.0)
    if genre == 'couple':
        return (1.0 + rapport * cmath.exp(-2j * math.pi * u * t)) / (1.0 + rapport)
    return complex(1.0, 0.0)


def visibilite(genre: str, taille_mas: float, b_m: float, lam_nm: float, rapport: float = 1.0) -> float:
    return abs(visibilite_complexe(genre, taille_mas, b_m, lam_nm, rapport))


def base_premier_zero(genre: str, taille_mas: float, lam_nm: float, rapport: float = 1.0) -> float | None:
    """Base (m) du premier zéro de visibilité (disque : 1,22 λ / θ) ou du premier minimum (couple : λ / 2ρ)."""
    if taille_mas <= 0.0:
        return None
    lam = lam_nm * 1e-9
    if genre == 'disque':
        return RAYLEIGH * lam / rad_de_mas(taille_mas)
    if genre == 'couple':
        return lam / (2.0 * rad_de_mas(taille_mas))
    return None


def intensite(alpha_mas: float, b_m: float, d_m: float, lam_nm: float, v: complex) -> float:
    """Intensité (1 au centre pour V = 1) des franges à l'angle α du centre, pour la visibilité complexe v."""
    lam = lam_nm * 1e-9
    a = rad_de_mas(alpha_mas)
    env = airy(math.pi * d_m * a / lam)
    return 0.5 * env * (1.0 + abs(v) * math.cos(2.0 * math.pi * b_m * a / lam - cmath.phase(v)))


def champ_coupe(b_m: float, d_m: float, lam_nm: float) -> float:
    """Demi-largeur (mas) de la coupe affichée : le lobe central de l'enveloppe, ou six franges s'il y en a trop."""
    return min(1.3 * resolution_mas(d_m, lam_nm), 6.0 * interfrange_mas(b_m, lam_nm))


def coupe(b_m: float, d_m: float, lam_nm: float, v: complex, n: int = 401) -> tuple[list, list, float]:
    demi = champ_coupe(b_m, d_m, lam_nm)
    xs = [-demi + 2.0 * demi * k / (n - 1) for k in range(n)]
    return xs, [intensite(x, b_m, d_m, lam_nm, v) for x in xs], demi


SEUIL_RESOLU = 0.9        # visibilité sous laquelle la source est « résolue » (contraste mesurablement réduit)


def verdict(genre: str, taille_mas: float, d_m: float, lam_nm: float, v: float) -> str:
    """Ce que voit l'instrument de la source : résolue par un télescope seul, par l'interféromètre, ou pas du tout."""
    if genre == 'point' or taille_mas <= 0.0:
        return 'v_ponctuelle'
    if taille_mas >= resolution_mas(d_m, lam_nm):
        return 'v_seul'
    return 'v_interferometre' if v < SEUIL_RESOLU else 'v_non_resolue'


# ------------------------------------------------------------------ anneaux de Newton
N_ANNEAUX = 12                        # anneaux sombres montrés


def epaisseur_nm(r_mm: float, R_m: float) -> float:
    """Épaisseur de la lame (nm) à r (mm) du contact, lentille de rayon R (m) : r²/(2R)."""
    return (r_mm * 1e-3) ** 2 / (2.0 * R_m) * 1e9


def newton(r_mm: float, R_m: float, lam_nm: float, n: float, cote: str = 'reflexion') -> float:
    """Éclairement relatif (0–1) à r (mm) du centre."""
    return newton_e(epaisseur_nm(r_mm, R_m), lam_nm, n, cote)


def rayon_sombre(k: int, R_m: float, lam_nm: float, n: float, cote: str = 'reflexion') -> float:
    """Rayon (mm) du k-ième anneau sombre (k = 1, 2…) : √(kλR/n) en réflexion, √((k − ½)λR/n) en transmission."""
    kk = k if cote == 'reflexion' else k - 0.5
    return math.sqrt(kk * lam_nm * 1e-9 * R_m / n) * 1e3


@functools.lru_cache(maxsize=1)
def _cie():
    """Fonctions colorimétriques CIE 1931 (pas de 5 nm) et Y du blanc (spectre plat)."""
    from .lumiere import spectres
    d = spectres()['cie']
    ws = [d['w0'] + d['pas'] * i for i in range(len(d['x']))]
    yw = 0.0
    for v in d['y']:
        yw += v
    return ws, d['x'], d['y'], d['z'], yw


def couleur_blanche(r_mm: float, R_m: float, n: float, cote: str = 'reflexion') -> tuple[int, int, int]:
    """Couleur (sRGB) en lumière blanche (spectre plat, sommes CIE au pas de 5 nm), rapportée au blanc."""
    from .lumiere import rgb_de_xyz
    ws, xb, yb, zb, yw = _cie()
    e = epaisseur_nm(r_mm, R_m)
    x = y = z = 0.0
    for w, a, b, c in zip(ws, xb, yb, zb):
        f = newton_e(e, w, n, cote)
        x += f * a
        y += f * b
        z += f * c
    return rgb_de_xyz(x / yw, y / yw, z / yw)


def newton_e(e_nm: float, lam_nm: float, n: float, cote: str) -> float:
    i = (1.0 - math.cos(4.0 * math.pi * n * e_nm / lam_nm)) / 2.0
    return i if cote == 'reflexion' else 1.0 - i
