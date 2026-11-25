"""La précession des équinoxes (sans Qt, jumeau de ``src/calc/precession.ts`` de Coupole Web).

L'axe de la Terre décrit un cône autour de la perpendiculaire à l'écliptique, en sens rétrograde : le pôle céleste
fait le tour du pôle de l'écliptique, à ε = 23,44° de lui, en 25 772 ans (précession générale en longitude
p = 5 028,796 195″ par siècle, UAI 2006).  Modèle simple : écliptique fixe (celui de J2000), obliquité constante
(elle varie en réalité de 22,1° à 24,5° en 41 000 ans), vitesse uniforme, mouvements propres des étoiles négligés —
les dates des « étoiles polaires » sont justes à quelques siècles près.  Le point vernal recule le long de
l'écliptique de p par an : l'équinoxe de mars passe des Poissons au Verseau vers 2600."""
from __future__ import annotations

import math

P_ARCSEC_SIECLE = 5028.796_195           # précession générale en longitude (UAI 2006)
P_DEG_AN = P_ARCSEC_SIECLE / 3600.0 / 100.0
PERIODE_ANS = 360.0 / P_DEG_AN
EPS = 84381.406 / 3600.0                 # obliquité J2000 (UAI 2006), 23,439 279°
LIMITES_2026 = (('ari', 29.050), ('tau', 53.779), ('gem', 90.503), ('cnc', 118.351), ('leo', 138.402),
                ('vir', 174.214), ('lib', 218.172), ('sco', 241.424), ('oph', 248.001), ('sgr', 266.601),
                ('cap', 300.020), ('aqr', 327.852), ('psc', 352.013))   # = astro.LIMITES_ZODIAQUE_2026 (de la date)

# étoiles boréales brillantes : désignation de Bayer, α et δ (J2000, °), V — Yale Bright Star Catalogue (arrondis)
ETOILES = (
    ('α Lyr', 279.24, 38.79, 0.0), ('α Aur', 79.17, 45.99, 0.1), ('β Gem', 116.32, 28.03, 1.1),
    ('α Cyg', 310.36, 45.28, 1.2), ('β Tau', 81.57, 28.61, 1.6), ('ε UMa', 193.51, 55.96, 1.8),
    ('α Per', 51.08, 49.86, 1.8), ('α UMa', 165.93, 61.75, 1.8), ('η UMa', 206.88, 49.31, 1.9),
    ('β Aur', 89.88, 44.95, 1.9), ('α Gem', 113.65, 31.89, 2.0), ('α UMi', 37.98, 89.26, 2.0),
    ('α And', 2.1, 29.09, 2.1), ('β And', 17.43, 35.62, 2.1), ('β UMi', 222.68, 74.16, 2.1),
    ('β Per', 47.04, 40.96, 2.1), ('γ Cyg', 305.56, 40.26, 2.2), ('α Cas', 10.13, 56.54, 2.2),
    ('γ Dra', 269.15, 51.49, 2.2), ('γ1 And', 30.98, 42.33, 2.3), ('β Cas', 2.3, 59.15, 2.3),
    ('ζ UMa', 200.98, 54.93, 2.3), ('β UMa', 165.46, 56.38, 2.4), ('β Peg', 345.95, 28.08, 2.4),
    ('γ UMa', 178.46, 53.69, 2.4), ('α Cep', 319.65, 62.59, 2.4), ('ε Cyg', 311.56, 33.97, 2.5),
    ('γ Cas', 14.18, 60.72, 2.5), ('θ Aur', 89.93, 37.21, 2.6), ('δ Cas', 21.46, 60.23, 2.7),
    ('ι Aur', 74.25, 33.17, 2.7), ('η Dra', 246.0, 61.51, 2.7), ('β Dra', 262.61, 52.3, 2.8),
    ('ζ Her', 250.32, 31.61, 2.8), ('ζ Per', 58.53, 31.88, 2.9), ('δ Cyg', 296.24, 45.13, 2.9),
    ('ε Per', 59.46, 40.01, 2.9), ('α2 CVn', 194.0, 38.32, 2.9), ('γ Per', 46.2, 53.51, 2.9),
    ('η Peg', 340.75, 30.22, 2.9), ('ε Aur', 75.49, 43.82, 3.0), ('β Tri', 32.39, 34.99, 3.0),
    ('δ Per', 55.73, 47.79, 3.0), ('ψ UMa', 167.42, 44.5, 3.0), ('γ Boo', 218.02, 38.31, 3.0),
    ('μ UMa', 155.58, 41.5, 3.0), ('γ UMi', 230.18, 71.83, 3.0), ('δ Dra', 288.14, 67.66, 3.1),
    ('α Lyn', 140.26, 34.39, 3.1), ('ι UMa', 134.8, 48.04, 3.1), ('π Her', 258.76, 36.81, 3.2),
    ('η Aur', 76.63, 41.23, 3.2), ('θ UMa', 143.2, 51.67, 3.2), ('ζ Dra', 257.2, 65.71, 3.2),
    ('ζ Cyg', 318.23, 30.23, 3.2), ('γ Cep', 354.83, 77.63, 3.2), ('β Cep', 322.17, 70.56, 3.2),
    ('γ Lyr', 284.74, 32.69, 3.2), ('δ And', 9.83, 30.86, 3.3), ('ι Dra', 231.23, 58.97, 3.3),
    ('α Dra', 211.1, 64.38, 3.6), ('ι Her', 264.87, 46.01, 3.8), ('κ Dra', 188.37, 69.79, 3.9),
    ('τ Her', 244.93, 46.31, 3.9),
)
NOMS = {'α UMi': 'polaris', 'α Lyr': 'vega', 'α Dra': 'thuban', 'α Cyg': 'deneb', 'β UMi': 'kochab',
        'α Cep': 'alderamin', 'γ Cep': 'errai', 'ι Her': 'iota_her', 'δ Cyg': 'delta_cyg', 'α Aur': 'capella'}


def ecliptique(ra_deg: float, dec_deg: float) -> tuple[float, float]:
    """(λ, β) en degrés, écliptique et équinoxe J2000."""
    a, d, e = math.radians(ra_deg), math.radians(dec_deg), math.radians(EPS)
    lam = math.atan2(math.sin(a) * math.cos(e) + math.tan(d) * math.sin(e), math.cos(a))
    beta = math.asin(math.sin(d) * math.cos(e) - math.cos(d) * math.sin(e) * math.sin(a))
    return math.degrees(lam) % 360.0, math.degrees(beta)


def vecteur(lam_deg: float, beta_deg: float) -> tuple[float, float, float]:
    l, b = math.radians(lam_deg), math.radians(beta_deg)
    return math.cos(b) * math.cos(l), math.cos(b) * math.sin(l), math.sin(b)


def pole(annee: float) -> tuple[float, float]:
    """Pôle nord céleste de l'année (λ, β) dans le repère écliptique J2000."""
    return (90.0 - P_DEG_AN * (annee - 2000.0)) % 360.0, 90.0 - EPS


def ecart(u, v) -> float:
    """Angle (°) entre deux directions unitaires (formule de l'arc tangente, juste aux petits angles)."""
    cx, cy, cz = u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]
    return math.degrees(math.atan2(math.sqrt(cx * cx + cy * cy + cz * cz), u[0] * v[0] + u[1] * v[1] + u[2] * v[2]))


_ECL = [(n, *ecliptique(a, d), m) for n, a, d, m in ETOILES]


def etoiles_ecliptiques():
    """[(nom, λ, β, V)] en J2000."""
    return _ECL


def distance_au_pole(nom: str, annee: float) -> float:
    for n, l, b, _ in _ECL:
        if n == nom:
            return ecart(vecteur(l, b), vecteur(*pole(annee)))
    raise KeyError(nom)


def plus_proche(annee: float, v_max: float = 3.7) -> tuple[str, float]:
    """L'étoile (V ≤ v_max) la plus proche du pôle céleste, et sa distance (°)."""
    p = vecteur(*pole(annee))
    meilleur = ('', 180.0)
    for n, l, b, m in _ECL:
        if m <= v_max:
            d = ecart(vecteur(l, b), p)
            if d < meilleur[1]:
                meilleur = (n, d)
    return meilleur


def point_vernal(annee: float) -> float:
    """Longitude (J2000) du point vernal de l'année."""
    return (-P_DEG_AN * (annee - 2000.0)) % 360.0


def constellation(lam_j2000: float) -> str:
    """Constellation zodiacale (limites de l'UAI) d'une longitude écliptique J2000."""
    lam = (lam_j2000 + P_DEG_AN * 26.0) % 360.0                # longitude de la date 2026
    nom = LIMITES_2026[-1][0]
    for cle, l0 in sorted(LIMITES_2026, key=lambda x: x[1]):
        if lam >= l0:
            nom = cle
    return nom


def annee_entree(cle: str, apres: float) -> float:
    """Première année après « apres » où le point vernal entre dans la constellation « cle » (il recule : il y entre
    par sa limite est, la plus grande longitude)."""
    lims = sorted(LIMITES_2026, key=lambda x: x[1])
    j = [k for k, _ in lims].index(cle)
    fin = lims[(j + 1) % len(lims)][1]                          # limite est de la constellation (date 2026)
    lam0 = (fin - P_DEG_AN * 26.0) % 360.0                       # en J2000
    # point_vernal(y) = lam0 (mod 360) : y = 2000 − (lam0 + 360 k)/p ; plus petit y > apres
    y = 2000.0 - lam0 / P_DEG_AN
    while y <= apres:
        y += PERIODE_ANS
    while y - PERIODE_ANS > apres:
        y -= PERIODE_ANS
    return y


def declinaison(nom: str, annee: float) -> float:
    return 90.0 - distance_au_pole(nom, annee)
