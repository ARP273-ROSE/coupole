"""Références du calculateur « Parallaxe (TP du cours) » tirées de Coupole (astropy) pour Coupole Web : pour chaque
cas de cas_td.json, la géométrie, la formule du sujet et le calcul exact.  Vérifiées contre SageMath par
tests/test_td_parallaxe.py (bureau) ; comparées au TypeScript par tests/unit/td_parallaxe.test.ts (web).
    python outils/verif_td/references_td.py > tests/td_parallaxe_reference.json"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1]))

from coupole.modules.td import parallaxe_tp as T  # noqa: E402

out = {'source': 'Coupole (astropy EarthLocation, WGS84)', 'cas': []}
for c in json.loads((ICI / 'cas_td.json').read_text(encoding='utf-8'))['cas']:
    o1, o2 = (T.Lieu(*x) for x in (c['o1'], c['o2']))
    r = T.calculer(T.Entrees(o1, o2, 'iss', configuration=c['config']))
    g = r['geometrie']
    out['cas'].append({'id': c['id'], 'corde_km': g['corde_km'], 'surface_km': g['surface_km'],
                       'fleche_km': g['fleche_km'], 'profondeur_deg': g['profondeur_deg'],
                       'angle_centre_deg': g['angle_centre_deg'], 'r1': g['r1'], 'r2': g['r2'],
                       'configuration': r['configuration'], 'D_corde_km': r['sujet_corde']['D_km'],
                       'D_surface_km': r['sujet_surface']['D_km'], 'distances_km': r['exact']['distances_km'],
                       'altitude_km': r['exact']['altitude_km'], 'sigma_sujet_km': r['incertitudes']['sujet_total_km'],
                       'sigma_exact_km': r['incertitudes']['exact_total_km']})
json.dump(out, sys.stdout, indent=1)
print()
