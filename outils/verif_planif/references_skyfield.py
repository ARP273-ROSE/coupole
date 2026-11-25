"""Contrôle indépendant du planificateur de parallaxe (coupole/modules/td/planif.py) par skyfield + DE440s :
pour chaque créneau trouvé, hauteur et azimut de l'objet aux deux lieux, hauteur du Soleil, ISS éclairée,
fraction éclairée de la Lune, distances Lune–étoile φ₁, φ₂.  Écarts maximaux affichés ; sortie
tests/td_planif_reference.json (cas de référence pour les tests).

Usage (venv du kit + skyfield) : python outils/verif_planif/references_skyfield.py [chemin/de440s.bsp]
"""
import datetime as D
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from skyfield.api import EarthSatellite, Star, load, load_file, wgs84  # noqa: E402

from coupole.modules.td import planif as P  # noqa: E402

UTC = D.timezone.utc
TLE = ('1 25544U 98067A   26329.13827943  .00005490  00000-0  10559-3 0  9990',
       '2 25544  51.6318 223.5847 0007441  62.8824 297.2922 15.49581740596707')
S1, S2 = P.Site(48.8366, 2.3360, 67, 'A'), P.Site(45.76, 4.84, 170, 'B')
DEBUT = D.datetime(2026, 11, 25, tzinfo=UTC)


def main():
    bsp = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / '.cache/skyfield/de440s.bsp')
    eph = load_file(bsp)
    ts = load.timescale()
    terre, soleil, lune = eph['earth'], eph['sun'], eph['moon']
    w = [wgs84.latlon(s.lat, s.lon, s.alt_m) for s in (S1, S2)]
    sat = EarthSatellite(*TLE, 'ISS', ts)
    sortie = {'tle': TLE, 'sites': [[s.lat, s.lon, s.alt_m] for s in (S1, S2)], 'debut': DEBUT.isoformat(),
              'iss': [], 'lune': []}
    r = P.chercher(S1, S2, P.Criteres('iss', DEBUT, jours=7, tle=TLE))
    eh = es = 0.0
    for c in r['creneaux']:
        t = ts.from_datetime(c.meilleur)
        sky = []
        for n in (0, 1):
            alt, az, d = (sat - w[n]).at(t).altaz()
            sky.append([alt.degrees, az.degrees])
            eh = max(eh, abs(alt.degrees - c.h[n]), abs((az.degrees - c.az[n] + 180) % 360 - 180))
            s_alt = (terre + w[n]).at(t).observe(soleil).apparent().altaz()[0].degrees
            es = max(es, abs(s_alt - c.soleil[n]))
        assert sat.at(t).is_sunlit(eph), c.meilleur
        sortie['iss'].append({'instant': c.meilleur.isoformat(), 'h': c.h, 'az': c.az, 'soleil': c.soleil,
                              'parallaxe_deg': c.parallaxe_deg, 'entre': c.entre, 'skyfield_h_az': sky})
    print('ISS : %d créneaux ; écart max hauteur/azimut %.4f° ; Soleil %.3f°' % (len(r['creneaux']), eh, es))
    r = P.chercher(S1, S2, P.Criteres('lune', DEBUT, jours=60))
    eh = ep = ef = 0.0
    u, V, noms = P.etoiles()
    import numpy as np
    for c in r['creneaux']:
        t = ts.from_datetime(c.meilleur)
        k = noms.index(c.etoile['nom'])
        ra = float(np.degrees(np.arctan2(u[k][1], u[k][0])) % 360)
        de = float(np.degrees(np.arcsin(u[k][2])))
        etoile = Star(ra_hours=ra / 15, dec_degrees=de)
        sky = []
        for n in (0, 1):
            o = terre + w[n]
            ml = o.at(t).observe(lune)                 # astrométrique, comme les étoiles du catalogue
            alt, az, _ = ml.apparent().altaz()
            sky.append(alt.degrees)
            eh = max(eh, abs(alt.degrees - c.h[n]))
            phi = ml.separation_from(o.at(t).observe(etoile)).degrees
            ep = max(ep, abs(phi - c.etoile['sep%d' % (n + 1)]) * 3600)
        f = (terre + w[0]).at(t).observe(lune).apparent().fraction_illuminated(soleil)
        ef = max(ef, abs(f - c.phase))
        sortie['lune'].append({'instant': c.meilleur.isoformat(), 'h': c.h, 'phase': c.phase, 'etoile': c.etoile,
                               'skyfield_h': sky, 'skyfield_phase': float(f)})
    print('Lune (%s) : %d créneaux ; écart max hauteur %.4f° ; φ %.1f″ ; fraction éclairée %.4f'
          % (r['source'], len(r['creneaux']), eh, ep, ef))
    (RACINE / 'tests/td_planif_reference.json').write_text(json.dumps(sortie, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
