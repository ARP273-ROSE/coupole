"""Références communes bureau / web du module « Pluies de météores » : sorties de td/meteores.py (Coupole) pour les
tests de Coupole Web (src/calc/td_meteores.ts).

Usage : python3 outils/verif_meteores/reference_web.py > ../coupole-web/tests/references/td_meteores_reference.json
"""
import datetime as D
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from coupole.modules.td import meteores as M  # noqa: E402
from coupole.modules.td import planif as P  # noqa: E402

iso = lambda t: t.astimezone(D.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if t else None
PARIS = P.Site(48.8366, 2.336, 67.0, 'Paris')
out = {'site': [PARIS.lat, PARIS.lon, PARIS.alt_m],
       'calendrier': {str(a): [{'code': e['code'], 'debut': iso(e['debut']), 'fin': iso(e['fin']), 'max': iso(e['max']),
                                'alpha': e['alpha'], 'delta': e['delta'], 'lune': e.get('lune')}
                               for e in M.calendrier(a)] for a in (2026, 2027)},
       'radiant': [], 'zhr': []}
for code in ('PER', 'GEM', 'QUA', 'ANT', 'COM', 'AND', 'ETA', 'LYR', 'URS', 'NTA'):
    for lam in range(0, 360, 3):
        out['radiant'].append([code, lam, *M.radiant(code, float(lam))])
        out['zhr'].append([code, lam, M.zhr(code, float(lam))])
nuits = []
for jour, codes in ((D.date(2026, 12, 13), None), (D.date(2027, 8, 12), ['PER']), (D.date(2027, 1, 3), None)):
    N = M.nuit(PARIS, jour, 6.0, 1.0, codes=codes)
    nuits.append({'jour': jour.isoformat(), 'codes': codes, 'debut': iso(N.debut), 'lune_frac': N.lune_frac,
                  'nuit': [int(x) for x in N.nuit] if N.nuit else None,
                  'soleil': [float(x) for x in N.soleil[::12]], 'lune': [float(x) for x in N.lune[::12]],
                  'pluies': [{'code': e['code'], 'attendu': e['attendu'], 'heures': e['heures'],
                              'meilleur': None if e['meilleur'] is None else int(e['meilleur']),
                              'h': [float(x) for x in e['h'][::12]], 'champ': e['champ']} for e in N.pluies]})
out['nuits'] = nuits
C = M.campagne(PARIS, D.date(2026, 12, 10), D.date(2026, 12, 16), 6.0, 1.0, 5.0)
out['campagne'] = [{'nuit': x['nuit'].isoformat(), 'code': x['code'], 'attendu': x['attendu'], 'note': x['note'],
                    'meilleur': iso(x['meilleur'])} for x in C]
print(json.dumps(out, ensure_ascii=False))
