"""Valeurs du calculateur cosmologie-redshift (cosmo_core) et d'astropy construit indépendamment,
sur une grille de z et de courbures.  Sortie : JSON lu par le script Sage.

Vérification refaite le 8 octobre 2026 avant l'intégration dans Coupole (le dépôt du calculateur n'est pas modifié) :

    python dump_calc.py CHEMIN/cosmologie-redshift/programme calc.json      # copie du dossier, sans cache
    python dump_coupole.py CHEMIN/Coupole coupole.json
    sage verif_independante.sage calc.json rapport.json
    sage verif_independante.sage coupole.json rapport_coupole.json

Résultat : calculateur et Coupole ≤ 3e-6 (distances) et ≤ 2e-5 (âges, E) de la référence Sage ; l'écart restant
vient de l'ajustement de Komatsu (2011) des neutrinos massifs utilisé par astropy (≤ 1e-9 contre une référence Sage
qui emploie le même ajustement).  Constantes du calculateur (t0, D_H, horizons, maximum de D_A) : ≤ 5e-6.
Volume comobile d'astropy faux à z ≲ 1e-6 en univers courbe (annulation numérique) : remplacé dans Coupole.
Les valeurs de référence des tests (tests/cosmo_reference_sage.json) viennent de rapport_coupole.json.
"""
import json
import sys

import numpy as np
from astropy import units as u, constants as const
from astropy.cosmology import Planck18, LambdaCDM, FlatLambdaCDM

sys.path.insert(0, sys.argv[1])          # dossier programme/ du calculateur (copie)
import cosmo_core as C                    # noqa: E402

Z = [0.0, 1e-8, 1e-6, 1e-4, 1e-3, 0.00428, 0.01, 0.05, 0.1, 0.158, 0.3, 0.5, 1.0, 1.5, 1.59213, 2.0, 2.34, 3.0,
     5.0, 7.085, 10.0, 10.6, 20.0, 50.0, 100.0, 300.0, 500.0, 1000.0, 1089.8, 1100.0]
OKS = [-0.05, -0.01, 0.0, 0.01, 0.05]


def astropy_direct(Ok):
    """Construction indépendante : mêmes paramètres que Planck 2018, Ω_Λ ajusté pour la courbure demandée."""
    if Ok == 0:
        return FlatLambdaCDM(H0=67.66, Om0=0.30966, Tcmb0=2.7255, Neff=3.046, m_nu=[0, 0, 0.06] * u.eV, Ob0=0.04897)
    p = Planck18
    return LambdaCDM(H0=p.H0, Om0=p.Om0, Ode0=p.Ode0 - Ok, Tcmb0=p.Tcmb0, Neff=p.Neff, m_nu=p.m_nu, Ob0=p.Ob0)


def grandeurs_astropy(m, z):
    tl = m.lookback_time(z)
    return {
        'comoving': m.comoving_distance(z).to_value(u.lyr),
        'transverse': m.comoving_transverse_distance(z).to_value(u.lyr),
        'luminosity': m.luminosity_distance(z).to_value(u.lyr),
        'angular_diameter': m.angular_diameter_distance(z).to_value(u.lyr),
        'lookback': (tl * const.c).to_value(u.lyr),
        'lookback_gyr': tl.to_value(u.Gyr),
        'age_at_z': m.age(z).to_value(u.Gyr),
        'E': float(m.efunc(z)),
        'v_flrw': (m.H0 * m.comoving_distance(z)).to_value(u.km / u.s),
        'vol_gpc3': m.comoving_volume(z).to_value(u.Gpc ** 3) if z > 0 else 0.0,
        'distmod': m.distmod(z).value if z > 0 else None,
        'kpc_arcsec': (1 / m.arcsec_per_kpc_proper(z)).to_value(u.kpc / u.arcsec) if z > 0 else None,
    }


out = {'Z': Z, 'OKS': OKS, 'calc': {}, 'astropy': {}, 'modeles': {}}
for Ok in OKS:
    mc = C.make_cosmology(C.H0_PLANCK, C.OM_PLANCK, Ok)
    ma = astropy_direct(Ok)
    out['modeles'][str(Ok)] = {'calc': {'H0': mc.H0.value, 'Om0': mc.Om0, 'Ode0': mc.Ode0, 'Ok0': mc.Ok0,
                                        'Onu0': mc.Onu0, 'Ogamma0': mc.Ogamma0},
                               'astropy': {'H0': ma.H0.value, 'Om0': ma.Om0, 'Ode0': ma.Ode0, 'Ok0': ma.Ok0,
                                           'Onu0': ma.Onu0, 'Ogamma0': ma.Ogamma0}}
    rc, ra = [], []
    for z in Z:
        d = C.compute(z, Ok=Ok, with_sigma=False, with_shoes=False)
        rc.append({k: d[k] for k in ('comoving', 'transverse', 'luminosity', 'angular_diameter', 'lookback',
                                     'lookback_gyr', 'age_at_z', 'E', 'v_flrw', 't0_model')})
        ra.append(grandeurs_astropy(ma, z))
    out['calc'][str(Ok)] = rc
    out['astropy'][str(Ok)] = ra
    out.setdefault('liste', []).append({
        'nom': 'Planck 2018, Ok = %+.2f' % Ok,
        'params': {'H0': 67.66, 'Om0': 0.30966, 'Ok0': Ok, 'Tcmb0': 2.7255, 'Neff': 3.046, 'm_nu': [0, 0, 0.06]},
        'candidats': {'calculateur': rc, 'astropy': ra}})

# constantes écrites en dur dans cosmo_core
out['constantes'] = {k: getattr(C, k) for k in ('T0_GYR', 'D_H_GLYR', 'PARTICLE_HORIZON_GLYR', 'EVENT_HORIZON_GLYR',
                                                'Z_DA_MAX', 'DA_MAX_GLYR', 'H0_PLANCK', 'OM_PLANCK', 'SIGMA_H0',
                                                'SIGMA_OM', 'RHO_H0_OM')}
# incertitudes et SH0ES, à z = 1
d = C.compute(1.0)
out['sigma_z1'] = d['sigma']
out['shoes_z1'] = {k: d['shoes'][k] for k in ('comoving', 'luminosity', 'age_at_z')}
# courbes (sans cache disque) : mêmes valeurs que compute ?
g = np.array([0.1, 1.0, 10.0, 1089.8])
cv = C.curves(g, use_cache=False)
out['curves'] = {k: list(map(float, v)) for k, v in cv.items()}
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print('ok', len(Z) * len(OKS))
