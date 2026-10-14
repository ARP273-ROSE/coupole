#!/usr/bin/env python3
"""Courbe de rotation de la Voie lactée : modèle de masse et mesures, pour « Courbe de rotation de la Voie lactée ».

Usage (python 3, galpy ≥ 1.12 requis) :
    python3 outils/verif_anim/voie_lactee.py VCDATA_GALKIN EILERS_MAIN_TEX

- Modèle : McMillan (2017, arXiv:1608.00971), meilleur ajustement, tel qu'implémenté dans galpy
  (galpy/potential/McMillan17.py : bulbe, disques mince et épais, gaz HI et H2, halo NFW ; R0 = 8,21 kpc,
  v0 = 233,1 km/s).  v_c(R) dans le plan, de 0,05 à 25 kpc tous les 0,05 kpc, total et par composante ;
  masse contenue dans une sphère de rayon r (galpy, mass()), tous les 0,5 kpc.
- Mesures, extérieur : Eilers et al. (2019, ApJ 871, 120), table 1 (lignes publiées, 5,27 à 24,82 kpc),
  lue dans la source LaTeX de l'article (arXiv:1810.09466).
- Mesures, intérieur : compilation galkin (Pato & Iocco 2017, SoftwareX 6, 54),
  produite par bin/galkin_data_fast.py avec R0 = 8,21 kpc, V0 = 233,1 km/s et le mouvement solaire de
  Schönrich et al. (2010) ; points de 2 à 5,25 kpc regroupés par intervalles de 0,25 kpc : moyenne pondérée et
  dispersion des points de l'intervalle.
Sortie : coupole/modules/anim/donnees/voie_lactee.json.gz (mêmes données que Coupole Web).
Vérification de quelques valeurs : outils/verif_anim/voie_lactee_verif.sage.
"""
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
from galpy.potential import mass, vcirc
from galpy.potential.McMillan17 import McMillan17, McMillan_bulge, McMillan_disk, McMillan_halo

RO, VO = 8.21, 233.1


def modele():
    rs = np.round(np.arange(0.05, 25.0001, 0.05), 2)
    vc = lambda pot, r: round(float(vcirc(pot, r / RO, quantity=False)), 3)
    out = {'R': [float(r) for r in rs]}
    for nom, pot in (('v', McMillan17), ('bulbe', McMillan_bulge), ('disques', McMillan_disk), ('halo', McMillan_halo)):
        out[nom] = [vc(pot, r) for r in rs]
    rm = np.round(np.arange(0.5, 25.0001, 0.5), 2)
    out['Rm'] = [float(r) for r in rm]
    out['M'] = [float('%.5g' % sum(float(mass(p, r / RO, quantity=False)) for p in (McMillan_bulge, McMillan_disk, McMillan_halo))) for r in rm]
    return out


def eilers(tex):
    t = Path(tex).read_text(encoding='utf-8')
    bloc = t[t.index('\\startdata'):t.index('\\enddata')]
    lignes = []
    for l in bloc.splitlines():
        l = l.strip()
        if not l or l.startswith('%') or l.startswith('\\'):
            continue
        v = [float(x) for x in re.findall(r'[-\d.]+', l)[:4]]
        lignes.append(v)
    return lignes


def galkin(fichier, r0=2.0, r1=5.25, pas=0.25):
    pts = []
    for l in Path(fichier).read_text().splitlines():
        if l.startswith('#') or not l.strip():
            continue
        c = l.split()
        pts.append((float(c[0]), float(c[2]), float(c[3])))
    out = []
    a = r0
    while a < r1 - 1e-9:
        sel = [(v, e) for r, v, e in pts if a <= r < a + pas and e > 0]
        if len(sel) >= 3:
            w = np.array([1 / e ** 2 for _, e in sel])
            v = np.array([v for v, _ in sel])
            m = float((w * v).sum() / w.sum())
            s = float(np.sqrt((w * (v - m) ** 2).sum() / w.sum()))
            rr = [r for r, _, e in pts if a <= r < a + pas and e > 0]
            out.append([round(float(np.mean(rr)), 3), round(m, 2), round(max(s, 1.0), 2), len(sel)])
        a += pas
    return out


def main(vcdata, tex):
    doc = {
        'source': 'McMillan 2017 (galpy McMillan17) ; Eilers et al. 2019, table 1 ; galkin (Pato & Iocco 2017)',
        'R0': RO, 'v0': VO, 'modele': modele(), 'eilers': eilers(tex), 'galkin': galkin(vcdata),
    }
    dest = Path(__file__).resolve().parents[2] / 'coupole' / 'modules' / 'anim' / 'donnees' / 'voie_lactee.json.gz'
    dest.write_bytes(gzip.compress(json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), 9, mtime=0))
    print(dest, len(doc['eilers']), 'points Eilers,', len(doc['galkin']), 'intervalles galkin')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
