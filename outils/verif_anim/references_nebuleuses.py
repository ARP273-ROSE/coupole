"""Référence commune des volumes de M42 et d'IC 434 (« Orion en 3D ») : particules, étoiles et repères calculés par
coupole/modules/anim/nebuleuses_orion.py ; Coupole Web (src/calc/nebuleuses_orion.ts) doit les retrouver.

    python3 outils/verif_anim/references_nebuleuses.py      → tests/nebuleuses_orion_reference.json"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ICI))
from coupole.modules.anim import nebuleuses_orion as N  # noqa: E402

sortie = {'version': N.VERSION, 'agrandi': N.AGRANDI, 'nebuleuses': [
    {'id': n['id'], 'centre': list(n['centre']),
     'particules': [[*q['p'], q['r'], *q['rvb'], q['alpha'], q['genre']] for q in n['particules']],
     'etoiles': [[e['id'], *e['p']] for e in n['etoiles']],
     'reperes': [[r['fiche'], *r['p']] for r in n['reperes']]} for n in N.nebuleuses()]}
(ICI / 'tests' / 'nebuleuses_orion_reference.json').write_text(json.dumps(sortie, ensure_ascii=False, separators=(',', ':')))
print(sum(len(n['particules']) for n in sortie['nebuleuses']), 'particules')
