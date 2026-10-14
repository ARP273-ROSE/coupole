#!/usr/bin/env python3
"""Côtes des globes et des cartes : Natural Earth 1:50m (ne_50m_land, domaine public), simplifiées.

Usage : python3 outils/verif_anim/cotes_natural_earth.py ne_50m_land.geojson
(fichier de https://github.com/nvkelso/natural-earth-vector, dossier geojson/)

Chaque anneau (contours extérieurs et grands lacs intérieurs, comme la Caspienne) est simplifié par
Douglas-Peucker (tolérance 0,07°), les îles de moins de 0,25 degré carré sont omises, les coordonnées
arrondies au centième de degré.  Sortie : coupole/modules/anim/donnees/cotes.json.gz (mêmes lignes que
Coupole Web, src/donnees/genere/cotes.json), même format qu'avant
({source, format, polygones: [[[lon, lat], ...], ...]}).
"""
import gzip
import json
import math
import sys
from pathlib import Path

TOLERANCE = 0.07
AIRE_MIN = 0.25
AIRE_MIN_TROU = 2.0


def aire(anneau):
    s = 0.0
    for (x0, y0), (x1, y1) in zip(anneau, anneau[1:] + anneau[:1]):
        s += x0 * y1 - x1 * y0
    return abs(s) / 2


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    garde = [False] * len(pts)
    garde[0] = garde[-1] = True
    pile = [(0, len(pts) - 1)]
    while pile:
        a, b = pile.pop()
        (xa, ya), (xb, yb) = pts[a], pts[b]
        dx, dy = xb - xa, yb - ya
        n = math.hypot(dx, dy)
        dmax, imax = -1.0, -1
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * (x - xa) - dx * (y - ya)) / n if n > 0 else math.hypot(x - xa, y - ya)
            if d > dmax:
                dmax, imax = d, i
        if dmax > tol:
            garde[imax] = True
            pile += [(a, imax), (imax, b)]
    return [p for p, g in zip(pts, garde) if g]


def main(source):
    doc = json.load(open(source, encoding='utf-8'))
    polys = []
    for f in doc['features']:
        g = f['geometry']
        groupes = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        for anneaux in groupes:
            for k, anneau in enumerate(anneaux):
                pts = [(round(x, 4), round(y, 4)) for x, y in anneau]
                if aire(pts) < (AIRE_MIN if k == 0 else AIRE_MIN_TROU):
                    continue
                # coupe l'anneau en deux pour que Douglas-Peucker garde sa forme fermée
                m = len(pts) // 2
                s = dp(pts[:m + 1], TOLERANCE)[:-1] + dp(pts[m:], TOLERANCE)
                s = [[round(x, 2), round(y, 2)] for x, y in s]
                if len(s) < 5:
                    continue
                # ferme l'anneau, puis le coupe aux bords artificiels (méridien ±180°, pôle Sud)
                s.append(s[0])
                artificiel = lambda a, b: (abs(a[0]) >= 179.99 and abs(b[0]) >= 179.99) or (a[1] <= -89.9 and b[1] <= -89.9)
                ligne = [s[0]]
                for a, b in zip(s, s[1:]):
                    if artificiel(a, b):
                        if len(ligne) >= 2:
                            polys.append(ligne)
                        ligne = [b]
                    else:
                        ligne.append(b)
                if len(ligne) >= 2:
                    polys.append(ligne)
    polys.sort(key=lambda p: -len(p))
    out = {
        'source': 'Natural Earth 1:50m, ne_50m_land (domaine public, naturalearthdata.com), simplifié '
                  f'(Douglas-Peucker {TOLERANCE}°, îles de moins de {AIRE_MIN} degré carré omises)',
        'format': '[[longitude, latitude], ...] en degrés, une ligne de côte ouverte (fermée si le dernier point est le premier)',
        'polygones': polys,
    }
    dest = Path(__file__).resolve().parents[2] / 'coupole' / 'modules' / 'anim' / 'donnees' / 'cotes.json.gz'
    brut = json.dumps(out, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    dest.write_bytes(gzip.compress(brut, 9, mtime=0))
    print(f'{dest} : {len(polys)} polygones, {sum(len(p) for p in polys)} points, {dest.stat().st_size} octets')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
