"""Valeurs du module Cosmologie de Coupole sur la même grille, pour plusieurs jeux de paramètres."""
import json
import sys

sys.path.insert(0, sys.argv[1])
from coupole.modules.cosmo import calcul as K  # noqa: E402

Z = [1e-8, 1e-6, 1e-4, 1e-3, 0.00428, 0.01, 0.05, 0.1, 0.158, 0.3, 0.5, 1.0, 1.5, 1.59213, 2.0, 2.34, 3.0,
     5.0, 7.085, 10.0, 10.6, 20.0, 50.0, 100.0, 300.0, 500.0, 1000.0, 1089.8, 1100.0]
AL = K.al_par_mpc()
JEUX = [('planck18', None, None, Ok) for Ok in (-0.05, -0.01, 0.0, 0.01, 0.05)] + \
       [('planck15', None, None, 0.0), ('wmap9', None, None, 0.0), ('simple', None, None, 0.0),
        ('perso', 73.04, 0.3111, 0.0), ('perso', 70.0, 0.25, 0.2), ('perso', 60.0, 0.5, -0.2)]
liste = []
for modele, H0, Om, Ok in JEUX:
    m = K.construire(modele, H0, Om, Ok)
    lignes = []
    for z in Z:
        d = K.calculer(z, modele, H0, Om, Ok, incertitudes=False)
        r = {k: d[k] for k, _ in K.GRANDEURS if k not in ('a', 'H_z', 'v_cz', 'v_sr', 't0_model')}
        for k in K.DISTANCES:
            r[k] = d[k] * AL                          # Mpc → années-lumière (unité du script Sage)
        lignes.append(r)
    nus = [float(x) for x in m.m_nu.value] if m.m_nu is not None else []
    liste.append({'nom': '%s H0=%s Om=%s Ok=%+.2f' % (modele, m.H0.value, m.Om0 + m.Onu0, Ok),
                  'params': {'H0': m.H0.value, 'Om0': m.Om0, 'Ok0': Ok, 'Tcmb0': m.Tcmb0.value, 'Neff': m.Neff,
                             'm_nu': nus if m.Tcmb0.value > 0 else []},
                  'candidats': {'coupole': lignes}})
json.dump({'Z': Z, 'liste': liste}, open(sys.argv[2], 'w'), indent=1)
print('ok', len(liste))
