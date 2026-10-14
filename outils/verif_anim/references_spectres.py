"""Références communes du moteur « spectres physiques » des deux applications (100 cas : 5 classes × 20 types) avec
l'étalonnage PCHIP et la grille fine des intensités (0.6.0).  Les cas et leur forme sont ceux du modèle
(tests/valeurs_reference.json du dossier « spectres physiques ») ; aux types entiers, l'étalonnage reste exactement
celui du modèle et les intensités à 0,02 près (test_spectres_types_entiers_comme_le_modele).

    python3 outils/verif_anim/references_spectres.py   → tests/spectres_physiques_reference.json.gz (Coupole Web : exporter)"""
import gzip
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ICI))
from coupole.modules.anim.spectre_physique import modele  # noqa: E402
from coupole.modules.anim.spectres_physiques import ModeleSpectres  # noqa: E402

chemin = ICI / 'tests' / 'spectres_physiques_reference.json.gz'
ref = json.load(gzip.open(chemin, 'rt', encoding='utf-8'))
if 'modele' not in ref:
    ref['modele'] = [{k: c[k] for k in ('type', 'classe', 'etalonnage', 'intensites')} for c in ref['cas']]
m = modele()
for c in ref['cas']:
    t, cl = c['type'], c['classe']
    e = m.etalonnage(t, cl)
    r = m.raies(t, cl)
    b = m.bandes(t, cl)
    c.update({'etalonnage': e, 'intensites': m.intensites(t, cl), 'n_raies': len(r),
              'raies_fortes': sorted(r, key=lambda x: -x['W'])[:6], 'n_bandes': len(b), 'bandes_premieres': b[:3],
              'spectre': m.spectre(t, cl, ref['lambdas']), 'spectre_r0p3': m.spectre(t, cl, ref['lambdas'], None, 0.3),
              'spectre_h_seul': m.spectre(t, cl, ref['lambdas'], ['h']),
              'spectre_sans_molecules': m.spectre(t, cl, ref['lambdas'], ['he_ii', 'he_i', 'h', 'metaux_ionises', 'metaux']),
              'couleur_etoile': list(m.couleur_etoile(e['teff'])),
              'continu': [ModeleSpectres.continu_relatif(e['teff'], lam) for lam in (400, 500, 600, 700)],
              'beta_prime_500': ModeleSpectres.beta_prime(e['teff'], 500)})
with gzip.open(chemin, 'wt', encoding='utf-8') as f:
    json.dump(ref, f, ensure_ascii=False, separators=(',', ':'))
print(len(ref['cas']), 'cas')
