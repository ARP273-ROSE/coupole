#!/usr/bin/env python3
"""Cas de parité du type d'éclipse (eclipses_geo, Python ↔ TypeScript) et vérification contre la table :
à l'instant du maximum (géométrie DE440 de donnees/eclipses_geometrie.json), le type calculé doit être celui de la
table pour les 133 éclipses de 2015–2044.  python3 outils/cas_eclipses_geo.py [CHEMIN_DE_COUPOLE_WEB]"""
from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))

from coupole.modules.anim import eclipses_geo as G  # noqa: E402

TYPES = {'total': 'totale', 'annular': 'annulaire', 'hybrid': 'hybride', 'partial': 'partielle', 'penumbral': 'penombrale'}


def main() -> int:
    with gzip.open(ICI / 'coupole' / 'modules' / 'anim' / 'donnees' / 'eclipses_geometrie.json.gz', 'rt', encoding='utf-8') as f:
        geo = json.load(f)
    RT = G.R_TERRE_KM
    cas, table, ecarts = [], [], []
    for cle, e in geo['eclipses'].items():
        delta = abs(e['gamma']) * RT
        x = math.sqrt(max(0.0, e['d_km'] ** 2 - delta ** 2))
        r = G.eclipse_soleil(-x, delta, e['s_km']) if cle[0] == 'S' else G.eclipse_lune(x, delta, e['s_km'])
        attendu = TYPES[e['type']]
        table.append([cle, attendu, r['type']])
        if r['type'] != attendu:
            ecarts.append((cle, e['date'], attendu, r['type'], e['gamma'], e['d_km']))
    # cas synthétiques (alignement exact, périgée/apogée extrêmes, décalages)
    for nom, x, delta in (('perigee_aligne', -G.PERIGEE_MIN_KM, 0.0), ('apogee_aligne', -G.APOGEE_MAX_KM, 0.0),
                          ('moyenne_alignee', -G.D_LUNE_KM, 0.0), ('gamma_0_8_perigee', -G.PERIGEE_MIN_KM, 0.8 * RT),
                          ('decale_1_3_rayon', -G.D_LUNE_KM, 1.3 * RT), ('grand_decalage', -G.D_LUNE_KM, 3 * RT),
                          ('cote_terre', 20000.0, 0.0)):
        cas.append(['soleil', nom, x, delta, G.eclipse_soleil(x, delta)])
    for nom, x, delta in (('totale', G.D_LUNE_KM, 0.0), ('partielle', G.D_LUNE_KM, 0.9 * RT), ('penombrale', G.D_LUNE_KM, 1.1 * RT),
                          ('aucune', G.D_LUNE_KM, 2 * RT), ('cote_soleil', -G.D_LUNE_KM, 0.0)):
        cas.append(['lune', nom, x, delta, G.eclipse_lune(x, delta)])
    orbite = [[p, n, list(G.position_orbite(G.D_LUNE_KM, p, n))] for p in (0, 45, 90, 180, 270, 333.3) for n in (0, 90, 200)]
    texte = json.dumps({'format': 'coupole-eclipses-geo-cas', 'version': 1, 'cas': cas, 'table': table, 'orbite': orbite},
                       ensure_ascii=False, indent=1) + '\n'
    (ICI / 'tests' / 'eclipses_geo_cas.json').write_text(texte, encoding='utf-8')
    if len(sys.argv) > 1:
        (Path(sys.argv[1]) / 'tests' / 'references' / 'eclipses_geo_cas.json').write_text(texte, encoding='utf-8')
    print(len(table), 'éclipses de la table ;', len(ecarts), 'écarts')
    for e in ecarts:
        print('  ', e)
    for c in cas:
        print(c[0], c[1], c[4]['type'], round(c[4].get('largeur_km', 0)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
