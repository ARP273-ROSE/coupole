"""Données du lot 3 des animations, tirées des sources de l'original (ClassAction, Apache 2.0).

    python outils/verif_anim/donnees_lot3.py <scripts décompilés> <sprites SVG> <galacticRedshift> <sortie>

- <scripts décompilés> : dossier où JPEXS FFDec a exporté les scripts (« -export script ») de filters.swf
  (sous-dossier filters/scripts) ;
- <sprites SVG> : dossier où FFDec a exporté en SVG les sprites (« -format sprite:svg -export sprite ») de
  eclipsingbinarysim.swf : les symboles « <nom> - flux » contiennent les courbes de lumière observées en images PNG ;
- <galacticRedshift> : dossier flash-animations/flashdev2/galacticRedshift (fichier m32.as) ;
- <sortie> : dossier coupole/modules/anim/donnees.

Produit spectres.json.gz (filtres U, B, V, R de Landolt et atmosphère, spectre solaire, fonctions colorimétriques,
spectre de M32) et binaires.json.gz (courbes numérisées : chaque colonne de pixels est découpée en segments
sombres ; un point au milieu d'un segment court, un point tous les 3 pixels le long d'un segment long ; phase =
x / 320, flux = (220 − y) / 200, comme le tracé de l'original)."""
import base64
import glob
import gzip
import io
import json
import os
import re
import sys

import numpy as np
from PIL import Image


def spectres(dec: str, src: str) -> dict:
    out = {}
    s = open(os.path.join(dec, 'filters', 'scripts', 'Filter Data.as'), encoding='utf-8').read()
    for nom in 'UBVR':
        m = re.search(r'_global\.%s_Filter = \{name:"%s",maxTransmittance:([\d.]+),offset:([-\d.e]+),color:\d+,'
                      r'data:\[(.*?)\]\}' % (nom, nom), s, re.S)
        d = [(int(w), float(t)) for w, t in re.findall(r'w:(\d+),t:([\d.e-]+)', m.group(3))]
        assert [w for w, _ in d] == list(range(d[0][0], d[-1][0] + 1))
        out['filtre_' + nom] = {'w0': d[0][0], 't': [t for _, t in d], 't_max': float(m.group(1)),
                                'decalage': float(m.group(2))}
    m = re.search(r'atmosphericTransmittance = \[(.*?)\]', s, re.S)
    d = [(int(w), float(t)) for w, t in re.findall(r'w:(\d+),t:([\d.e-]+)', m.group(1))]
    out['atmosphere'] = {'w0': d[0][0], 't': [t for _, t in d]}
    s = open(os.path.join(dec, 'filters', 'scripts', 'Source Data.as'), encoding='utf-8').read()
    d = [(int(float(w)), float(v)) for w, v in re.findall(r'w:([\d.]+),v:([\d.e-]+)', s)]
    out['soleil'] = {'w0': d[0][0], 'v': [v for _, v in d]}
    s = open(os.path.join(dec, 'filters', 'scripts', 'Filters Simulator.as'), encoding='utf-8').read()
    m = re.search(r'p\.matchingFunctions = \[(.*?)\];', s, re.S)
    d = [(int(w), float(x), float(y), float(z)) for w, x, y, z in
         re.findall(r'w:(\d+),x:([\d.e-]+),y:([\d.e-]+),z:([\d.e-]+)', m.group(1))]
    assert [r[0] for r in d] == list(range(380, 826, 5))
    out['cie'] = {'w0': 380, 'pas': 5, 'x': [r[1] for r in d], 'y': [r[2] for r in d], 'z': [r[3] for r in d]}
    s = open(os.path.join(src, 'm32.as'), encoding='utf-8-sig').read()
    d = [(float(w), float(f)) for w, f in re.findall(r'\{w: ([\d.]+), f: ([\d.eE+-]+)\}', s)]
    pas = round(d[1][0] - d[0][0], 6)
    out['m32'] = {'w0': d[0][0], 'pas': pas, 'f': [f for _, f in d],
                  'z_original': float(re.search(r'_redshiftOffset:Number = ([\d.e-]+)', s).group(1))}
    return out


def courbes(svg: str) -> dict:
    res = {}
    for d in sorted(glob.glob(os.path.join(svg, '*- flux'))):
        nom = os.path.basename(d).split('_', 2)[2].rsplit(' - flux', 1)[0]
        s = open(os.path.join(d, '1.svg'), encoding='utf-8').read()
        b64 = re.search(r'base64,([A-Za-z0-9+/=]+)', s).group(1)
        im = np.array(Image.open(io.BytesIO(base64.b64decode(b64))).convert('RGB')).astype(float)
        assert im.shape[:2] == (220, 320), nom
        a = np.clip((255.0 - im[:, :, 0]) / (255.0 - 153.0), 0, 1)        # points gris (153) sur fond blanc
        pts = set()
        for x in range(320):
            ys = np.flatnonzero(a[:, x] > 0.35)
            if not len(ys):
                continue
            for run in np.split(ys, np.flatnonzero(np.diff(ys) > 1) + 1):
                ycs = [float((run * a[run, x]).sum() / a[run, x].sum())] if len(run) <= 4 else \
                    list(np.arange(run[0] + 1.0, run[-1], 3.0))
                for yc in ycs:
                    pts.add((round((x + 0.5) / 320.0, 4), round((220.0 - (yc + 0.5)) / 200.0, 4)))
        res[nom] = [[int(round(p * 10000)), int(round(f * 10000))] for p, f in sorted(pts)]
    return {'unite': 10000, 'courbes': res}


if __name__ == '__main__':
    dec, svg, src, sortie = sys.argv[1:5]
    with gzip.open(os.path.join(sortie, 'spectres.json.gz'), 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(spectres(dec, src), f, separators=(',', ':'))
    with gzip.open(os.path.join(sortie, 'binaires.json.gz'), 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(courbes(svg), f, separators=(',', ':'))
