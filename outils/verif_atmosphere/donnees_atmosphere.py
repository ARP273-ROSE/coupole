"""Transmission de l'atmosphère pour l'animation « L'atmosphère terrestre » (0.8.0) : modèle de ciel de l'ESO
(SkyCalc 2.0.9, Noll et al. 2012, A&A 543, A92 ; Jones et al. 2013, A&A 560, A91), site de Paranal (2 635 m),
masse d'air 1, vapeur d'eau précipitable 2,5 mm, 0,3 à 30 µm, résolution spectrale 3 000.

    pip install skycalc_cli
    python outils/verif_atmosphere/donnees_atmosphere.py SORTIE.fits    # interroge le service de l'ESO
    python outils/verif_atmosphere/donnees_atmosphere.py SORTIE.fits coupole/modules/anim/donnees/atmosphere_eso.json

Les colonnes gardées (moyenne par intervalle, 360 intervalles logarithmiques) : transmission totale, diffusion
Rayleigh, diffusion par les aérosols (Mie), absorption par l'ozone, absorption moléculaire (H₂O, CO₂, O₂…)."""
import json
import sys

import numpy as np


def interroger(sortie):
    from skycalc_cli.skycalc import SkyModel
    s = SkyModel()
    p = dict(s.params)
    p.update({'airmass': 1.0, 'pwv_mode': 'pwv', 'pwv': 2.5, 'incl_moon': 'N', 'incl_starlight': 'N',
              'incl_zodiacal': 'N', 'incl_loweratm': 'N', 'incl_upperatm': 'N', 'incl_airglow': 'N',
              'incl_therm': 'N', 'wmin': 300.0, 'wmax': 30000.0, 'wgrid_mode': 'fixed_spectral_resolution',
              'wres': 3000, 'vacair': 'vac', 'observatory': 'paranal'})
    s.callwith(p)
    open(sortie, 'wb').write(s.data)


def reduire(fits_chemin, json_chemin, n=360):
    from astropy.io import fits
    d = fits.getdata(fits_chemin, 1)
    lam = np.asarray(d['lam'], float) / 1000.0                     # µm
    bords = np.geomspace(0.3, 30.0, n + 1)
    out = {'source': 'ESO SkyCalc 2.0.9 (Noll et al. 2012 ; Jones et al. 2013), Paranal, masse d’air 1, PWV 2,5 mm',
           'lambda_um': [], 'total': [], 'rayleigh': [], 'aerosols': [], 'ozone': [], 'molecules': []}
    for a, b in zip(bords[:-1], bords[1:]):
        m = (lam >= a) & (lam < b)
        if not m.any():
            continue
        out['lambda_um'].append(round(float(np.sqrt(a * b)), 5))
        for cle, col in (('total', 'trans'), ('rayleigh', 'trans_rs'), ('aerosols', 'trans_ms'), ('ozone', 'trans_o3'),
                         ('molecules', 'trans_ma')):
            out[cle].append(round(float(np.mean(d[col][m])), 4))
    with open(json_chemin, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(len(out['lambda_um']), 'intervalles')


if __name__ == '__main__':
    if len(sys.argv) == 2:
        interroger(sys.argv[1])
    else:
        reduire(sys.argv[1], sys.argv[2])
