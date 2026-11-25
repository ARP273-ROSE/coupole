"""Étoiles de repère du planificateur de parallaxe : Yale Bright Star Catalogue, 5e révision (Hoffleit & Warren
1991, CDS V/50, fichier « catalog.gz »), étoiles de magnitude V ≤ 5,5, positions J2000 avancées au 1er janvier 2027
par le mouvement propre.  Sortie : coupole/modules/td/donnees/etoiles_v55.json.gz
[[ra°, dec°, V, désignation (Bayer/Flamsteed + constellation, ou « HR n »)], …].

Usage : python3 etoiles_td.py catalog.gz
"""
import gzip
import json
import sys
from pathlib import Path

GREC = {'Alp': 'α', 'Bet': 'β', 'Gam': 'γ', 'Del': 'δ', 'Eps': 'ε', 'Zet': 'ζ', 'Eta': 'η', 'The': 'θ', 'Iot': 'ι',
        'Kap': 'κ', 'Lam': 'λ', 'Mu': 'μ', 'Nu': 'ν', 'Xi': 'ξ', 'Omi': 'ο', 'Pi': 'π', 'Rho': 'ρ', 'Sig': 'σ',
        'Tau': 'τ', 'Ups': 'υ', 'Phi': 'φ', 'Chi': 'χ', 'Psi': 'ψ', 'Ome': 'ω'}
ANS = 27.0     # 2000.0 → 2027.0


def nom(ligne: str, hr: int) -> str:
    n = ligne[4:14]
    flam, bayer, cons = n[0:3].strip(), n[3:6].strip(), n[7:10].strip()
    if bayer and cons:
        g = GREC.get(bayer.rstrip('.'), bayer)
        indice = n[6].strip()
        return '%s%s %s' % (g, indice, cons)
    if flam and cons:
        return '%s %s' % (flam, cons)
    return 'HR %d' % hr


def main(src):
    out = []
    with gzip.open(src, 'rt', encoding='latin-1') as fh:
        for l in fh:
            if len(l) < 107 or not l[75:77].strip() or not l[102:107].strip():
                continue
            V = float(l[102:107])
            if V > 5.5:
                continue
            hr = int(l[0:4])
            ra = 15 * (int(l[75:77]) + int(l[77:79]) / 60 + float(l[79:83]) / 3600)
            dec = int(l[84:86]) + int(l[86:88]) / 60 + int(l[88:90]) / 3600
            if l[83] == '-':
                dec = -dec
            try:
                pmra, pmde = float(l[148:154]), float(l[154:160])     # ″/an ; pmRA déjà multiplié par cos δ
            except ValueError:
                pmra = pmde = 0.0
            import math
            dec2 = dec + pmde * ANS / 3600
            ra2 = ra + pmra * ANS / 3600 / max(math.cos(math.radians(dec)), 1e-6)
            out.append([round(ra2 % 360, 5), round(dec2, 5), V, nom(l, hr)])
    out.sort(key=lambda e: e[2])
    dest = Path(__file__).resolve().parents[2] / 'coupole/modules/td/donnees/etoiles_v55.json.gz'
    with gzip.open(dest, 'wt', encoding='utf-8') as fh:
        json.dump({'source': 'Yale Bright Star Catalogue 5th rev. (Hoffleit & Warren 1991), CDS V/50; '
                             'V <= 5.5; J2000 positions moved to 2027.0 by proper motion',
                   'etoiles': out}, fh, ensure_ascii=False, separators=(',', ':'))
    print(len(out), 'étoiles →', dest, dest.stat().st_size, 'octets')


if __name__ == '__main__':
    main(sys.argv[1])
