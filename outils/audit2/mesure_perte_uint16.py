"""Ce que coûte le « XISF compatible » (UInt16) sur de vraies poses de la banque : pixels négatifs mis à 0, pixels
> 65 535 écrêtés, arrondi, écart du fond (médiane) et de la moyenne du fond, par groupe (télescope, pose).

    python mesure_perte_uint16.py RACINE_BANQUE LISTE.txt [PIEDESTAL]   (chemins relatifs ; lecture seule)"""
import collections, json, os, re, sys

import numpy as np

from coupole.core import xisf
from coupole.modules.ohp import formats

racine, liste = sys.argv[1], sys.argv[2]
PIED = float(sys.argv[3]) if len(sys.argv) > 3 else formats.PIEDESTAL_U16
par = collections.defaultdict(list)
for rel in open(liste).read().split():
    a, inf = xisf.lire(os.path.join(racine, rel))
    m = re.search(r'_(\d+(?:\.\d+)?)s\.xisf$', rel)
    pose = float(m.group(1)) if m else -1
    tel = 'IRIS' if 'IRIS' in rel else 'T120'
    groupe = '%s %s' % (tel, '≤ 2 s' if pose <= 2 else '≤ 10 s' if pose <= 10 else '≤ 60 s' if pose <= 60 else '> 60 s')
    if a.dtype.kind != 'f':
        par[groupe + ' (déjà UInt16)'].append({'n': a.size})
        continue
    r = a.astype(np.float64)
    u, perte = formats.vers_uint16(r, PIED)
    u = u.astype(np.float64) - PIED                    # comparé en ADU d'origine
    fini = np.isfinite(r)
    fond = np.median(r[fini])
    # fond « moyen » : pixels sous la médiane + 3 MAD (ni étoiles ni objet) — moyenne avant et après
    mad = np.median(np.abs(r[fini] - fond)) * 1.4826
    masque = fini & (r < fond + 3 * mad)
    par[groupe].append({'n': int(a.size), 'neg': perte['u16_negatifs'], 'haut': perte['u16_hauts'],
                        'fond': float(fond), 'bruit': float(mad), 'd_mediane': perte['u16_ecart_fond'],
                        'd_moyenne_fond': float(u[masque].mean() - r[masque].mean()),
                        'arrondi_max': perte['u16_ecart_max']})
out = {}
for g, v in sorted(par.items()):
    if 'neg' not in v[0]:
        out[g] = {'poses': len(v), 'perte': 'aucune (entiers)'}
        continue
    n = sum(x['n'] for x in v)
    out[g] = {'poses': len(v), 'pixels_negatifs_pct': round(100 * sum(x['neg'] for x in v) / n, 3),
              'pire_pose_negatifs_pct': round(max(100 * x['neg'] / x['n'] for x in v), 2),
              'pixels_hauts_pct': round(100 * sum(x['haut'] for x in v) / n, 4),
              'fond_median_adu': round(float(np.median([x['fond'] for x in v])), 1),
              'bruit_fond_adu': round(float(np.median([x['bruit'] for x in v])), 1),
              'ecart_mediane_max_adu': round(max(abs(x['d_mediane']) for x in v), 3),
              'ecart_moyenne_fond_max_adu': round(max(abs(x['d_moyenne_fond']) for x in v), 3),
              'arrondi_max_adu': round(max(x['arrondi_max'] for x in v), 3)}
print(json.dumps(out, ensure_ascii=False, indent=1))
