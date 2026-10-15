#!/usr/bin/env python3
"""Géométrie réelle des éclipses de la table (2015–2044) et distances extrêmes de la Lune, par l'éphéméride DE440
(skyfield + de440s.bsp ; lancé dans python-lab, voir PROGRESSION.md).

    python geometrie_eclipses.py eclipses.json de440s.bsp sortie.json

Pour chaque éclipse : instant du maximum (au plus près de l'axe), distances Terre–Lune et Terre–Soleil, position de l'axe d'ombre
(Soleil) ou de la Lune (Lune) dans le plan fondamental (x vers l'est, y vers le nord, km) et sa vitesse (km/h).
- Soleil : axe Soleil → Lune ; point de l'axe le plus proche du centre de la Terre ; gamma = distance / R⊕.
- Lune : axe anti-solaire issu du centre de la Terre ; centre de la Lune par rapport à cet axe (positions
  apparentes, comme les tables de la NASA).
Distances extrêmes : minimum et maximum de la distance centre à centre Terre–Lune, 1900–2100 (pas de 1 h, affinés).
"""
import json
import sys

import numpy as np
from skyfield.api import load

RT = 6378.137


def main(src, bsp, out):
    E = json.load(open(src))
    ts = load.timescale()
    eph = load(bsp)
    terre, lune, soleil = eph['earth'], eph['moon'], eph['sun']

    def vecteurs(t, solaire=True):
        # conventions des tables de la NASA (Espenak) : positions astrométriques pour les éclipses de Soleil,
        # apparentes pour celles de Lune (gamma retrouvé à 10⁻⁴ près : 2017-08-21 0,4367 ; 2015-04-04 0,4460)
        e = terre.at(t)
        m, s = e.observe(lune), e.observe(soleil)
        if not solaire:
            m, s = m.apparent(), s.apparent()
        return np.asarray(m.position.km), np.asarray(s.position.km)

    N = np.array([0.0, 0.0, 1.0])

    def repere(z):
        z = z / np.linalg.norm(z, axis=0)
        x = np.cross(N, z, axis=0)
        x = x / np.linalg.norm(x, axis=0)
        y = np.cross(z, x, axis=0)
        return x, y, z

    def plan(t, solaire):
        m, s = vecteurs(t, solaire)
        if solaire:
            u = (m - s) / np.linalg.norm(m - s, axis=0)          # Soleil → Lune
            p = m - np.sum(m * u, axis=0) * u                      # point de l'axe le plus proche du centre de la Terre
            x, y, _ = repere(-u)
        else:
            a = -s / np.linalg.norm(s, axis=0)                     # axe de l'ombre de la Terre
            p = m - np.sum(m * a, axis=0) * a                      # Lune par rapport à l'axe
            x, y, _ = repere(a)
        return np.sum(p * x, axis=0), np.sum(p * y, axis=0), np.linalg.norm(m, axis=0), np.linalg.norm(s, axis=0)

    res = {}
    for nom, solaire in (('soleil', True), ('lune', False)):
        for i, e in enumerate(E[nom]):
            a, mo, j = e[0], e[1], e[2]
            h = np.arange(-18 * 60, (24 + 18) * 60, 2.0)           # minutes autour du jour (UT)
            t = ts.utc(a, mo, j, 0, h)
            X, Y, D, _ = plan(t, solaire)
            k = int(np.argmin(np.hypot(X, Y)))
            # affinage à la seconde
            h2 = h[k] + np.arange(-3.0, 3.0, 1 / 60)
            t2 = ts.utc(a, mo, j, 0, h2)
            X2, Y2, D2, S2 = plan(t2, solaire)
            k2 = int(np.argmin(np.hypot(X2, Y2)))
            tm = ts.utc(a, mo, j, 0, h2[k2])
            tt = ts.utc(a, mo, j, 0, np.array([h2[k2] - 10, h2[k2] + 10]))
            Xv, Yv, _, _ = plan(tt, solaire)
            res[('S' if solaire else 'L') + str(i)] = {
                'date': [a, mo, j], 'type': e[3], 'jj_ut': float(tm.ut1), 'iso': tm.utc_iso(),
                'd_km': round(float(D2[k2]), 1), 's_km': round(float(S2[k2]), 0), 'x_km': round(float(X2[k2]), 1), 'y_km': round(float(Y2[k2]), 1),
                'vx_kmh': round(float((Xv[1] - Xv[0]) * 3), 1), 'vy_kmh': round(float((Yv[1] - Yv[0]) * 3), 1),
                'gamma': round(float(np.sign(Y2[k2]) * np.hypot(X2[k2], Y2[k2]) / RT), 4),
            }
    # distances extrêmes de la Lune 1900–2100
    t = ts.utc(1900, 1, 1, np.arange(0, 201 * 365.25 * 24, 1.0))
    D = np.linalg.norm(terre.at(t).observe(lune).position.km, axis=0)
    ext = {}
    for nom, f in (('perigee_min', np.argmin), ('apogee_max', np.argmax)):
        k = int(f(D))
        tf = ts.tt_jd(t.tt[k] + np.arange(-2, 2, 1 / 1440) / 24)
        Df = np.linalg.norm(terre.at(tf).observe(lune).position.km, axis=0)
        kf = int(f(Df))
        ext[nom] = {'km': round(float(Df[kf]), 1), 'date': tf[kf].utc_iso()}
    ext['periode'] = '1900-2100'
    json.dump({'format': 'coupole-geometrie-eclipses/1', 'source': 'JPL DE440 (de440s.bsp), skyfield', 'rayon_terre_km': RT,
               'eclipses': res, 'distances_lune': ext}, open(out, 'w'), ensure_ascii=False, indent=1)
    print(len(res), 'éclipses ;', ext)


if __name__ == '__main__':
    main(*sys.argv[1:4])
