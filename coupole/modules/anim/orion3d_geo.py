"""Géométrie d'« Orion en 3D », sans dessin (même calcul, ligne pour ligne, que src/calc/orion3d.ts de Coupole Web ;
tests croisés) : repère ICRS centré sur le Soleil, en parsecs ; caméra en perspective qui tourne autour d'un pivot
(Orion, M42 ou la Tête de Cheval) ; « dépliement » u de 0 (tout sur une sphère de rayon R0 : la figure du ciel, vue du
Soleil) à 1 (chaque objet à sa distance).  Vue du Soleil, la perspective est la projection gnomonique du ciel (nord en
haut, est à gauche)."""
from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

with gzip.open(Path(__file__).with_name('donnees') / 'orion3d.json.gz', 'rt', encoding='utf-8') as _f:
    DONNEES = json.load(_f)

DEG = math.pi / 180
R0 = 400.0                  # rayon de la sphère du ciel (dépliement nul) et distance du pivot d'Orion (affichage)
LACET_3D = 75.0             # vue 3D d'Orion entier : 75° de côté, 20° au-dessus (choix d'affichage)
TANGAGE_3D = 20.0


def dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norme(a) -> float:
    return math.sqrt(dot(a, a))


def unitaire(a):
    n = norme(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 0 else (1.0, 0.0, 0.0)


def comb(a, ka: float, b, kb: float):
    return (a[0] * ka + b[0] * kb, a[1] * ka + b[1] * kb, a[2] * ka + b[2] * kb)


def direction(ra: float, dec: float):
    """Direction (vecteur unitaire ICRS) d'ascension droite ra et de déclinaison dec (degrés)."""
    a, d = ra * DEG, dec * DEG
    return (math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d))


def decaler(ra: float, dec: float, xi: float, eta: float):
    """Direction décalée de (ξ vers l'est, η vers le nord) radians dans le plan tangent en (ra, dec) (gnomonique)."""
    a, d = ra * DEG, dec * DEG
    c = direction(ra, dec)
    est = (-math.sin(a), math.cos(a), 0.0)
    nord = (-math.sin(d) * math.cos(a), -math.sin(d) * math.sin(a), math.cos(d))
    return unitaire((c[0] + xi * est[0] + eta * nord[0], c[1] + xi * est[1] + eta * nord[1],
                     c[2] + xi * est[2] + eta * nord[2]))


def lisse(x: float) -> float:
    t = max(0.0, min(1.0, x))
    return t * t * (3 - 2 * t)


def deplier(P, u: float):
    """Position affichée d'un point P au dépliement u : sur sa ligne de visée, de la sphère R0 (u = 0) à sa distance."""
    r = norme(P)
    if not r > 0:
        return (0.0, 0.0, 0.0)
    k = (1 - u) * R0 / r + u
    return (P[0] * k, P[1] * k, P[2] * k)


def centre_figure():
    """Centre de la figure : direction moyenne des étoiles reliées par les lignes de la constellation."""
    ids = {i for ligne in DONNEES['figure'] for i in ligne}
    s = (0.0, 0.0, 0.0)
    for e in DONNEES['etoiles']:
        if e['id'] in ids:
            s = comb(s, 1, direction(e['ra'], e['dec']), 1)
    return unitaire(s)


_CENTRE = None


def parametres_cible(c: str) -> dict:
    global _CENTRE
    P = DONNEES['primitives']
    if c == 'm42':
        S = tuple(P['m42_bol']['sommet'])
        return {'pivot': S, 'demi_champ': 0.55, 'd3': 16.0, 's3': 6.0, 'pivot3': S, 'lacet3': 55.0}
    if c == 'tete':
        C = tuple(P['tete_de_cheval']['centre'])
        return {'pivot': C, 'demi_champ': 0.075, 'd3': 9.0, 's3': 4.6, 'pivot3': C, 'lacet3': 35.0}
    if _CENTRE is None:
        _CENTRE = centre_figure()
    return {'pivot': comb(_CENTRE, R0, (0, 0, 0), 0), 'demi_champ': 18.0, 'd3': 1000.0, 's3': 270.0,
            'pivot3': comb(_CENTRE, 300, (0, 0, 0), 0), 'lacet3': LACET_3D}


def camera(a: str, b: str, k: float, u: float, lacet: float, tangage: float, w: float, h: float) -> dict:
    """Caméra : pivot interpolé entre deux cibles (k : 0 → a, 1 → b), dépliement u, lacet et tangage du glisser
    (degrés), image w × h.  Vue du ciel (u = 0, sans glisser) : l'œil est au Soleil."""
    pa, pb = parametres_cible(a), parametres_cible(b)
    kk, s = lisse(k), lisse(u)
    pivot_ciel = comb(pa['pivot'], 1 - kk, pb['pivot'], kk)
    pivot = comb(pivot_ciel, 1 - s, comb(pa['pivot3'], 1 - kk, pb['pivot3'], kk), s)
    mi = max(10.0, min(w, h))

    def lg(x, y, t):
        return math.exp((1 - t) * math.log(x) + t * math.log(y))

    d_ciel = norme(pivot_ciel)
    f_ciel = 0.5 * mi / math.tan(lg(pa['demi_champ'], pb['demi_champ'], kk) * DEG)
    d3 = lg(pa['d3'], pb['d3'], kk)
    f3 = 0.46 * mi * d3 / lg(pa['s3'], pb['s3'], kk)
    D = lg(d_ciel, d3, s)
    F = lg(f_ciel, f3, s)
    av0 = unitaire(pivot_ciel)
    ha0 = comb((0, 0, 1), 1, av0, -av0[2])
    ha0 = unitaire(ha0) if norme(ha0) > 1e-9 else (1.0, 0.0, 0.0)
    dr0 = cross(av0, ha0)
    l = (lacet + s * ((1 - kk) * pa['lacet3'] + kk * pb['lacet3'])) * DEG
    t = (tangage + s * TANGAGE_3D) * DEG
    av1 = comb(av0, math.cos(l), dr0, math.sin(l))
    dr1 = comb(dr0, math.cos(l), av0, -math.sin(l))
    avant = comb(av1, math.cos(t), ha0, math.sin(t))
    haut = comb(ha0, math.cos(t), av1, -math.sin(t))
    oeil = comb(pivot, 1, avant, -D)
    return {'oeil': oeil, 'droite': dr1, 'haut': haut, 'avant': avant, 'F': F, 'cx': w / 2, 'cy': h / 2, 'D': D}


def projeter(c: dict, P):
    """Projection d'un point (pc) : (x, y, profondeur) en pixels, ou None derrière la caméra (ou non fini)."""
    o = c['oeil']
    r = (P[0] - o[0], P[1] - o[1], P[2] - o[2])
    z = dot(r, c['avant'])
    if not z > c['D'] * 1e-3:
        return None
    x = c['cx'] + c['F'] * dot(r, c['droite']) / z
    y = c['cy'] - c['F'] * dot(r, c['haut']) / z
    return (x, y, z) if math.isfinite(x) and math.isfinite(y) else None


def point_coquille(d, icrs_vers_gal):
    """Point de la coquille d'Orion (ellipsoïde de Foley et al. 2023) sur la ligne de visée d : milieu de la corde."""
    P = DONNEES['primitives']['coquille_orion']
    ax, c = P['demi_axes_gal_pc'], P['centre']
    dg = [dot(l, d) for l in icrs_vers_gal]
    cg = [dot(l, c) for l in icrs_vers_gal]
    num = sum(dg[i] * cg[i] / ax[i] ** 2 for i in range(3))
    den = sum(dg[i] ** 2 / ax[i] ** 2 for i in range(3))
    t = num / den if den > 0 else R0
    return (d[0] * t, d[1] * t, d[2] * t)


def position_etoile(e: dict, brutes: bool):
    """Position (pc) retenue : distance d'affichage publiée (par défaut) ou mesure brute."""
    return tuple(e['xyz_affichage']) if not brutes and e.get('xyz_affichage') else tuple(e['xyz'])
