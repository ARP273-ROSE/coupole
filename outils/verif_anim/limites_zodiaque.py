"""Longitudes écliptiques où le Soleil franchit les limites des constellations (UAI 1930 ; données de
N. G. Roman 1987 livrées avec astropy), pour l'écliptique et l'équinoxe moyens d'une époque.

    python outils/verif_anim/limites_zodiaque.py [ANNEE]

Affiche la liste (clé, longitude de début en degrés) à recopier dans coupole/modules/anim/astro.py."""
import sys

import numpy as np
from astropy import units as u
from astropy.coordinates import GeocentricMeanEcliptic, SkyCoord, get_constellation
from astropy.time import Time

ANNEE = float(sys.argv[1]) if len(sys.argv) > 1 else 2026.0
EPOQUE = Time(ANNEE, format='jyear')


def noms(lam):
    c = SkyCoord(lon=lam * u.deg, lat=np.zeros_like(lam) * u.deg,
                 frame=GeocentricMeanEcliptic(equinox=EPOQUE, obstime=EPOQUE))
    return np.array(get_constellation(c, short_name=True))


def limites(pas=0.05):
    lam = np.arange(0.0, 360.0, pas)
    n = noms(lam)
    out = []
    for i in range(len(lam)):
        if n[i] != n[i - 1]:
            lo, hi = lam[i] - pas, lam[i]           # affinage par dichotomie
            for _ in range(30):
                mid = (lo + hi) / 2
                if noms(np.array([mid]))[0] == n[i - 1]:
                    lo = mid
                else:
                    hi = mid
            out.append((str(n[i]).lower(), round((lo + hi) / 2 % 360, 3)))
    return out


if __name__ == '__main__':
    for cle, l0 in limites():
        print("    ('%s', %.3f)," % (cle, l0))
