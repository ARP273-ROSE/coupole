"""Calculs de l'animation « L'atmosphère terrestre : absorption, épaisseur traversée, réfraction » (0.8.0).

Même code en TypeScript dans Coupole Web (src/calc/atmosphere.ts) ; valeurs vérifiées par SageMath
(outils/verif_atmosphere/atmosphere_verif.sage → tests/atmosphere_sage.json).

* **Masse d'air** X (épaisseur traversée rapportée à celle du zénith), h hauteur VRAIE en degrés :
  - plan-parallèle : X = 1 / sin h = sec z ;
  - Kasten & Young (1989, Applied Optics 28, 4735) : X = 1 / [sin h + 0,50572 (h + 6,07995°)^−1,6364] ;
  - Pickering (2002, DIO 12, 3) : X = 1 / sin(h + 244 / (165 + 47 h^1,1)) ;
  - coquille sphérique homogène d'épaisseur H (échelle de hauteur, 8 km) au-dessus d'une Terre de rayon R :
    L = √((R + H)² − R² cos² h) − R sin h, X = L / H (≈ 40 à l'horizon).
* **Extinction** Δm = k X, k = 1,0857 τ (τ : épaisseur optique au zénith) :
  - diffusion Rayleigh, Hansen & Travis (1974, Space Sci. Rev. 16, 527), au niveau de la mer :
    τ_R = 0,008569 λ⁻⁴ (1 + 0,0113 λ⁻² + 0,00013 λ⁻⁴), λ en µm, proportionnelle à la pression ;
  - aérosols, loi d'Ångström (1929) : τ_a = β λ^−α (β = trouble à 1 µm, α ≈ 1,3) ;
  - ozone (bande de Chappuis) : modèle simplifié, gaussienne centrée sur 0,60 µm, largeur 0,09 µm, τ = 0,042 à
    300 unités Dobson (section efficace ≈ 5 × 10⁻²¹ cm², Serdyuchenko et al. 2014).
* **Réfraction** (degrés) : Bennett (1982, J. Navigation 35, 255) pour une hauteur apparente
  R = cot(h + 7,31/(h + 4,4)) / 60, Sæmundsson (1986, Sky & Telescope 72, 70) pour une hauteur vraie
  R = 1,02 cot(h + 10,3/(h + 5,11)) / 60 ; facteur (P / 1010 hPa) × (283 K / T).
* **Dispersion** : indice de l'air sec standard de Ciddor (1996, Applied Optics 35, 1566),
  (n − 1) × 10⁸ = 5 792 105 / (238,0185 − σ²) + 167 917 / (57,362 − σ²), σ = 1/λ (µm⁻¹) ; la réfraction à λ vaut
  celle de la formule (rapportée à 0,55 µm) × (n_λ − 1) / (n_0,55 − 1).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

R_TERRE_KM = 6371.0
H_ECHELLE_KM = 8.0
BANDES = {'U': 0.365, 'B': 0.445, 'V': 0.551, 'R': 0.658, 'I': 0.806}      # µm (Bessell 1990)
SIN = math.sin
DEG = math.pi / 180.0


# ============================================================================================== masse d'air
def masse_air_secz(h: float) -> float:
    return 1.0 / math.sin(max(h, 1e-6) * DEG)


def masse_air_kasten_young(h: float) -> float:
    h = max(h, 0.0)
    return 1.0 / (math.sin(h * DEG) + 0.50572 * (h + 6.07995) ** -1.6364)


def masse_air_pickering(h: float) -> float:
    h = max(h, 0.0)
    return 1.0 / math.sin((h + 244.0 / (165.0 + 47.0 * h ** 1.1)) * DEG)


def chemin_sphere_km(h: float, H: float = H_ECHELLE_KM, R: float = R_TERRE_KM) -> float:
    s = math.sin(h * DEG)
    return math.sqrt((R + H) ** 2 - (R * math.cos(h * DEG)) ** 2) - R * s


def masse_air_sphere(h: float, H: float = H_ECHELLE_KM, R: float = R_TERRE_KM) -> float:
    return chemin_sphere_km(h, H, R) / H


# ============================================================================================== extinction
def tau_rayleigh(lam_um: float, pression_hpa: float = 1013.25) -> float:
    l2 = lam_um * lam_um
    return 0.008569 / (l2 * l2) * (1 + 0.0113 / l2 + 0.00013 / (l2 * l2)) * pression_hpa / 1013.25


def tau_aerosols(lam_um: float, beta: float = 0.05, alpha: float = 1.3) -> float:
    return beta * lam_um ** -alpha


def tau_ozone(lam_um: float, dobson: float = 300.0) -> float:
    return 0.042 * dobson / 300.0 * math.exp(-0.5 * ((lam_um - 0.60) / 0.09) ** 2)


def tau_total(lam_um: float, pression_hpa: float = 1013.25, beta: float = 0.05, dobson: float = 300.0) -> float:
    return tau_rayleigh(lam_um, pression_hpa) + tau_aerosols(lam_um, beta) + tau_ozone(lam_um, dobson)


def k_bande(lam_um: float, pression_hpa: float = 1013.25, beta: float = 0.05, dobson: float = 300.0) -> float:
    """Coefficient d'extinction (magnitudes par masse d'air)."""
    return 2.5 / math.log(10) * tau_total(lam_um, pression_hpa, beta, dobson)


def pression_altitude(alt_m: float) -> float:
    """Pression standard (hPa) à l'altitude d'un site : atmosphère isotherme d'échelle 8,4 km (ordre de grandeur)."""
    return 1013.25 * math.exp(-alt_m / 8400.0)


def couleur_transmise(X: float, pression_hpa: float = 1013.25, beta: float = 0.05, dobson: float = 300.0):
    """Teinte approchée de la lumière solaire transmise (rouge, vert, bleu entre 0 et 1, normalisés au plus fort) :
    transmission exp(−X τ) à 0,61, 0,55 et 0,46 µm."""
    t = [math.exp(-X * tau_total(lam, pression_hpa, beta, dobson)) for lam in (0.61, 0.55, 0.46)]
    m = max(t) or 1.0
    return tuple(x / m for x in t)


# ============================================================================================== réfraction
def facteur_pt(pression_hpa: float = 1010.0, temperature_c: float = 10.0) -> float:
    return (pression_hpa / 1010.0) * (283.0 / (273.0 + temperature_c))


def refraction_apparente(h_app: float, pression_hpa: float = 1010.0, temperature_c: float = 10.0) -> float:
    """Bennett : réfraction (°) pour une hauteur apparente."""
    h = max(-1.0, h_app)
    return max(0.0, 1.0 / math.tan((h + 7.31 / (h + 4.4)) * DEG)) / 60.0 * facteur_pt(pression_hpa, temperature_c)


def refraction_vraie(h_vraie: float, pression_hpa: float = 1010.0, temperature_c: float = 10.0) -> float:
    """Sæmundsson : réfraction (°) pour une hauteur vraie."""
    h = max(-1.0, h_vraie)
    return max(0.0, 1.02 / math.tan((h + 10.3 / (h + 5.11)) * DEG)) / 60.0 * facteur_pt(pression_hpa, temperature_c)


def indice_ciddor(lam_um: float) -> float:
    """n − 1 de l'air sec standard (15 °C, 1013,25 hPa, 450 ppm de CO₂), Ciddor (1996)."""
    s2 = 1.0 / (lam_um * lam_um)
    return (5792105.0 / (238.0185 - s2) + 167917.0 / (57.362 - s2)) * 1e-8


def refraction_lambda(h_vraie: float, lam_um: float, pression_hpa: float = 1010.0, temperature_c: float = 10.0) -> float:
    return refraction_vraie(h_vraie, pression_hpa, temperature_c) * indice_ciddor(lam_um) / indice_ciddor(0.55)


def aplatissement(h_centre_vrai: float, rayon_deg: float = 0.2666, pression_hpa: float = 1010.0,
                  temperature_c: float = 10.0) -> dict:
    """Disque (Soleil ou Lune) près de l'horizon : diamètres apparents vertical et horizontal, rapport."""
    bas = h_centre_vrai - rayon_deg
    haut = h_centre_vrai + rayon_deg
    hb = bas + refraction_vraie(bas, pression_hpa, temperature_c)
    hh = haut + refraction_vraie(haut, pression_hpa, temperature_c)
    vertical = hh - hb
    return {'vertical_deg': vertical, 'horizontal_deg': 2 * rayon_deg, 'rapport': vertical / (2 * rayon_deg),
            'bas_apparent': hb, 'haut_apparent': hh}


def avance_lever_min(latitude: float, declinaison: float = 0.0, h0: float = -0.5667) -> float:
    """Avance du lever (et retard du coucher), minutes : temps mis par l'astre pour monter de la réfraction à
    l'horizon (−0,5667° ≈ 34′), sans changer de déclinaison.  cos H = (sin h − sin φ sin δ) / (cos φ cos δ)."""
    p, d = latitude * DEG, declinaison * DEG

    def H(h):
        c = (math.sin(h * DEG) - math.sin(p) * math.sin(d)) / (math.cos(p) * math.cos(d))
        return math.degrees(math.acos(max(-1.0, min(1.0, c))))
    return (H(h0) - H(0.0)) / 15.0 * 60.0 * 0.99726957   # heures sidérales → minutes de temps moyen


# ============================================================================================== données
_ESO = None


def transmission_eso() -> dict:
    """Transmission au zénith à Paranal (ESO SkyCalc), 0,3 à 30 µm."""
    global _ESO
    if _ESO is None:
        _ESO = json.loads((Path(__file__).with_name('donnees') / 'atmosphere_eso.json').read_text(encoding='utf-8'))
    return _ESO


#: domaines hors du modèle de l'ESO (schéma : ordres de grandeur, sources dans NOTICE)
DOMAINES = (
    ('gamma_x', 1e-6, 0.01, 0.0),        # rayons γ et X : absorbés haut dans l'atmosphère
    ('uv_lointain', 0.01, 0.20, 0.0),    # O₂, N₂
    ('uv_ozone', 0.20, 0.30, 0.02),      # bande de Hartley de l'ozone
    ('ir_lointain', 30.0, 300.0, 0.0),   # vapeur d'eau
    ('submm', 300.0, 1000.0, 0.3),       # fenêtres 350, 450, 850 µm (sites très secs)
    ('mm', 1000.0, 1e4, 0.7),            # O₂ (5 mm), H₂O (1,35 cm)
    ('radio', 1e4, 1e7, 1.0),            # 1 cm à 10 m : fenêtre radio
    ('ionosphere', 1e7, 1e9, 0.0),       # au-delà de ~ 20 m : réfléchi par l'ionosphère
)
