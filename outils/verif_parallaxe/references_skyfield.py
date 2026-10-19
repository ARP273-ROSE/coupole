"""Références INDÉPENDANTES (skyfield + JPL DE440, sans le code de Coupole) pour les calculs de parallaxe.

Usage (une seule fois ; le résultat est versionné) :
    python outils/verif_parallaxe/references_skyfield.py CHEMIN/de440s.bsp DOSSIER_IERS > tests/parallaxe_reference_skyfield.json

skyfield (licence MIT) avec les tables IERS « finals2000A.all » du jour (UT1 − UTC mesuré et prédit ; la table
intégrée à skyfield s'arrête à sa date de publication) ; DE440 (domaine public, JPL/NASA).  Rien n'est importé de
Coupole : les essais (tests/test_partages_calculs.py) comparent les calculs de Coupole (ERFA, Meeus ou DE440 via
jplephem) à ces valeurs.

* ``lune`` : pour quelques lieux et instants, direction ASTROMÉTRIQUE topocentrique de la Lune (α, δ ICRS, distance),
  hauteur et azimut APPARENTS sans réfraction, position de l'observateur dans le GCRS.
* ``paires_lune`` : deux observateurs éloignés ; directions astrométriques du centre de la Lune (au même instant ou à
  quelques secondes d'écart) et distance géocentrique astrométrique : la triangulation doit la retrouver.
* ``iss`` : un TLE réel de l'ISS (Celestrak, 18/10/2026) ; position terrestre (ITRS) et altitude WGS84 prédites,
  directions (α, δ) GCRS géométriques vues de deux lieux à t, t+1 s, t+2 s : la triangulation doit retrouver
  l'altitude.
"""
import json
import sys

import numpy as np
from skyfield.api import EarthSatellite, Loader, load, wgs84

TLE = ('1 25544U 98067A   26291.78980200  .00007771  00000+0  14938-3 0  9993',
       '2 25544  51.6325  48.4339 0006764 280.4294  79.5932 15.48929442590914')
LIEUX = {'paris': (48.8566, 2.3522, 35.0), 'marseille': (43.2965, 5.3698, 12.0), 'strasbourg': (48.5734, 7.7521, 140.0),
         'lyon': (45.7640, 4.8357, 170.0), 'perth': (-31.9523, 115.8613, 20.0), 'brest': (48.3904, -4.4861, 50.0)}


def main(bsp):
    ts = Loader(sys.argv[2] if len(sys.argv) > 2 else '.').timescale(builtin=False)   # IERS finals2000A à jour
    eph = load(bsp)
    terre, lune = eph['earth'], eph['moon']
    out = {'source': 'skyfield %s, %s' % (__import__('skyfield').__version__, bsp.rsplit('/', 1)[-1]),
           'tle': list(TLE), 'lune': [], 'paires_lune': [], 'iss': []}
    for quand, lieux in (((2025, 11, 3, 18, 38, 26.0), ('paris', 'marseille', 'perth')),
                         ((2026, 10, 17, 4, 29, 11.204), ('paris', 'strasbourg', 'brest')),
                         ((2024, 4, 8, 18, 18, 0.0), ('lyon',))):
        t = ts.utc(*quand)
        for nom in lieux:
            la, lo, h = LIEUX[nom]
            site = wgs84.latlon(la, lo, h)
            a = (terre + site).at(t).observe(lune)
            ra, dec, dist = a.radec()
            alt, az, _ = a.apparent().altaz()
            out['lune'].append({'utc': list(quand), 'lieu': nom, 'lat': la, 'lon': lo, 'alt_m': h,
                                'ra_deg': ra._degrees, 'dec_deg': dec.degrees, 'distance_km': dist.km,
                                'h_apparente_deg': alt.degrees, 'az_deg': az.degrees,
                                'observateur_gcrs_km': site.at(t).position.km.tolist()})
    for quand, dt, (n1, n2) in (((2025, 11, 3, 18, 38, 26.0), 0.0, ('paris', 'marseille')),
                                ((2025, 11, 3, 18, 38, 26.0), 20.0, ('paris', 'marseille')),
                                ((2026, 1, 15, 21, 5, 0.0), 0.0, ('brest', 'strasbourg')),
                                ((2026, 1, 15, 21, 5, 0.0), 0.0, ('lyon', 'perth'))):
        t1 = ts.utc(*quand)
        t2 = ts.utc(*(list(quand[:5]) + [quand[5] + dt]))
        tm = ts.tt_jd((t1.tt + t2.tt) / 2)
        dirs = []
        for nom, t in ((n1, t1), (n2, t2)):
            la, lo, h = LIEUX[nom]
            obs = (terre + wgs84.latlon(la, lo, h)).at(t)
            ra, dec, dist = obs.observe(lune).radec()
            geom = float(np.linalg.norm(lune.at(t).position.km - obs.position.km))
            dirs.append({'distance_topo_geometrique_km': geom, 'lieu': nom, 'lat': la, 'lon': lo, 'alt_m': h, 'utc': [float(x) for x in t.utc], 'ra_deg': ra._degrees,
                         'dec_deg': dec.degrees, 'distance_topo_km': dist.km})
        geo = terre.at(tm).observe(lune)
        out['paires_lune'].append({'observateurs': dirs, 'distance_geo_km': geo.distance().km,
                                   'distance_geometrique_km': float(np.linalg.norm((lune - terre).at(tm).position.km))})
    sat = EarthSatellite(*TLE, 'ISS', ts)
    for quand, (n1, n2) in (((2026, 10, 18, 18, 30, 0.0), ('paris', 'lyon')),
                            ((2026, 10, 19, 5, 0, 0.0), ('paris', 'strasbourg'))):
        t0 = ts.utc(*quand)
        # choisir, au voisinage, un instant où l'ISS est haute pour les deux lieux (recherche minute par minute)
        meilleur = None
        for k in range(0, 24 * 60 * 2):
            t = ts.utc(*(list(quand[:4]) + [quand[4], quand[5] + 30.0 * k]))
            hs = [(sat - wgs84.latlon(*LIEUX[n][:2], LIEUX[n][2])).at(t).altaz()[0].degrees for n in (n1, n2)]
            if min(hs) > 25:
                meilleur = t
                break
        if meilleur is None:
            continue
        cas = {'lieux': [n1, n2], 'points': {}, 'itrs_km': [], 'altitude_km': [], 'utc': []}
        for s in (0.0, 1.0, 2.0):
            t = ts.tt_jd(meilleur.tt + s / 86400.0)
            g = sat.at(t)
            cas['utc'].append([float(x) for x in t.utc])
            cas['itrs_km'].append(g.frame_xyz(__import__('skyfield.framelib', fromlist=['itrs']).itrs).km.tolist())
            cas['altitude_km'].append(wgs84.height_of(g).km)
            for n in (n1, n2):
                la, lo, h = LIEUX[n]
                ra, dec, _ = (sat - wgs84.latlon(la, lo, h)).at(t).radec()
                cas['points'].setdefault(n, []).append([ra._degrees, dec.degrees])
        sp = wgs84.subpoint_of(sat.at(ts.tt_jd(meilleur.tt + 1 / 86400.0)))
        cas['sous_point'] = [sp.latitude.degrees, sp.longitude.degrees]
        out['iss'].append(cas)
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main(sys.argv[1])
