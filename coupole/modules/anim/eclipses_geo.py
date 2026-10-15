"""Type d'une éclipse d'après la géométrie réelle (tailles et distances en km) — commun au bureau et au web.

Portage ligne pour ligne de `coupole-web/src/calc/eclipses_geo.ts` ; cas de parité `tests/eclipses_geo_cas.json`
(`outils/cas_eclipses_geo.py`), rejoués par `tests/test_anim_ombres.py` et `tests/unit/eclipses_geo.test.ts`.

Le Soleil est si loin que ses rayons sont parallèles à l'échelle Terre–Lune : les axes d'ombre de la Terre et de la
Lune sont parallèles à la direction Soleil–Terre.  On mesure la Lune par rapport à la Terre :
- `x` : distance le long de l'axe (km) ; x < 0 : Lune du côté du Soleil (éclipse de Soleil possible), x > 0 : derrière
  la Terre (éclipse de Lune possible) ;
- `delta` : distance (km) entre l'axe d'ombre de la Lune et le centre de la Terre (Soleil), ou entre le centre de la
  Lune et l'axe d'ombre de la Terre (Lune) — c'est |gamma| × R⊕ des éléments de Bessel.
Soleil : rayon de l'ombre (ou de l'antombre, négatif) de la Lune au plan passant par le centre de la Terre et au
point de la surface terrestre le plus proche de la Lune : totale si l'ombre touche la surface, annulaire si c'est
l'antombre, hybride si l'ombre touche la surface mais pas le plan central ; partielle si seule la pénombre touche la
Terre ; largeur de la bande = diamètre de l'ombre (ou de l'antombre) à la surface.
Lune : ombre et pénombre de la Terre à la distance de la Lune, l'atmosphère comptée par la règle de Danjon (rayon
de la Terre augmenté de 1 %, celle des tables de la NASA ; la règle de Chauvenet, ombre agrandie de 2 %, classe à
tort la pénombrale du 29 septembre 2042 en partielle) ; totale si la Lune est entièrement dans l'ombre, partielle si
elle y entre, pénombrale si elle n'entre que dans la pénombre.
"""
from __future__ import annotations

import math

R_SOLEIL_KM = 695_700.0
R_TERRE_KM = 6_378.137
R_LUNE_KM = 1_737.4
UA_KM = 149_597_870.7
D_LUNE_KM = 384_400.0
ATMOSPHERE = 1.01                                   # Danjon : rayon de la Terre + 1 %
# distances extrêmes de la Lune (centre à centre), DE440, 1900–2100 (outils/verif_anim/geometrie_eclipses.py)
PERIGEE_MIN_KM = 356_375.3
APOGEE_MAX_KM = 406_711.7


def eclipse_soleil(x: float, delta: float, d_soleil: float = UA_KM) -> dict:
    """x < 0 (Lune côté Soleil), delta en km → {type, ombre_km (centre), ombre_surface_km, penombre_km, largeur_km}."""
    d = -x
    if d <= 0:
        return {'type': 'aucune', 'ombre_km': 0.0, 'ombre_surface_km': 0.0, 'penombre_km': 0.0, 'largeur_km': 0.0}
    d_sm = d_soleil - d
    ku = (R_SOLEIL_KM - R_LUNE_KM) / d_sm
    kp = (R_SOLEIL_KM + R_LUNE_KM) / d_sm
    ru = R_LUNE_KM - d * ku                        # au plan du centre de la Terre (négatif : antombre)
    rp = R_LUNE_KM + d * kp
    ds = d - math.sqrt(max(0.0, R_TERRE_KM ** 2 - min(delta, R_TERRE_KM) ** 2))
    rs = R_LUNE_KM - ds * ku                       # au point de la surface le plus proche de la Lune
    if delta >= R_TERRE_KM + rp:
        t = 'aucune'
    elif delta >= R_TERRE_KM + abs(ru):
        t = 'partielle'
    elif rs > 0 and ru > 0:
        t = 'totale'
    elif rs > 0:
        t = 'hybride'
    else:
        t = 'annulaire'
    largeur = 2 * abs(rs) if t in ('totale', 'annulaire', 'hybride') else 0.0
    return {'type': t, 'ombre_km': ru, 'ombre_surface_km': rs, 'penombre_km': rp, 'largeur_km': largeur}


def eclipse_lune(x: float, delta: float, d_soleil: float = UA_KM) -> dict:
    """x > 0 (Lune derrière la Terre), delta en km → {type, ombre_km, penombre_km}."""
    if x <= 0:
        return {'type': 'aucune', 'ombre_km': 0.0, 'penombre_km': 0.0}
    rt = R_TERRE_KM * ATMOSPHERE
    ru = rt - x * (R_SOLEIL_KM - rt) / d_soleil
    rp = rt + x * (R_SOLEIL_KM + rt) / d_soleil
    if delta + R_LUNE_KM <= ru:
        t = 'totale'
    elif delta - R_LUNE_KM < ru:
        t = 'partielle'
    elif delta - R_LUNE_KM < rp:
        t = 'penombrale'
    else:
        t = 'aucune'
    return {'type': t, 'ombre_km': ru, 'penombre_km': rp}


def position_orbite(d_km: float, position_deg: float, noeuds_deg: float, inclinaison_deg: float = 5.145) -> tuple:
    """Lune sur son orbite inclinée : (x le long de l'axe, vers l'opposé du Soleil ; y vers le nord de l'écliptique ;
    z hors du plan de la figure), km.  position : angle Terre-centré depuis la direction du Soleil (0 : nouvelle lune,
    180 : pleine lune) ; noeuds : angle du nœud ascendant depuis la direction du Soleil."""
    r = math.pi / 180.0
    u = (position_deg - noeuds_deg) * r            # argument de latitude
    i = inclinaison_deg * r
    beta = math.asin(math.sin(i) * math.sin(u))
    psi = noeuds_deg * r + math.atan2(math.cos(i) * math.sin(u), math.cos(u))
    return (-d_km * math.cos(beta) * math.cos(psi), d_km * math.sin(beta), d_km * math.cos(beta) * math.sin(psi))
