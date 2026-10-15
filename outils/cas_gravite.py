#!/usr/bin/env python3
"""Cas communs de la mécanique de « Gravité et orbites » (gravite_meca.py ↔ src/calc/gravite.ts de Coupole Web) :
pour chaque scénario, l'état initial, puis l'état, le temps, les périodes mesurées, les dérives et la courbure après
une suite fixe d'appels de avancer() (dont un sans gravité et un avec des masses changées).  Les deux programmes
doivent retrouver les mêmes nombres au bit près (comparés en hexadécimal).

    python3 outils/cas_gravite.py [CHEMIN_WEB]   → tests/gravite_cas.json (et CHEMIN_WEB/tests/references/gravite_cas.json)
"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
from coupole.modules.anim import gravite_meca as g  # noqa: E402

JOUR = g.JOUR
PROGRAMMES = {
    'soleil_terre': [[400 * JOUR, 1.0, True]] * 1 + [[3.7 * JOUR, 1.0, True]] * 3,
    'soleil_terre_lune': [[30 * JOUR, 1.0, True]] * 15,
    'terre_lune': [[1.3 * JOUR, 1.0, True]] * 70 + [[2 * JOUR, 1.0, False]],
    'terre_iss': [[600.0, 1.0, True]] * 20,
    'libre': [[50 * JOUR, 1.0, True]] * 6 + [[50 * JOUR, 1.7, True]] * 4,
}


def h(x):
    return float(x).hex()


def etat(s):
    return [[c.nom, h(c.m), h(c.x), h(c.y), h(c.vx), h(c.vy), c.actif] for c in s.corps]


def main():
    cas = {}
    for nom, prog in PROGRAMMES.items():
        cs = g.scenario(nom)
        s = g.Systeme(cs, JOUR / 10 if nom != 'terre_iss' else 10.0)
        depart = etat(s)
        etapes = []
        for duree, masse, gravite in prog:
            # facteur de masse appliqué au premier corps (comme un curseur de masse), gravité coupée ou non
            s.corps[0].m = g.MASSES[s.corps[0].nom] * masse
            if s.gravite != gravite:
                s.gravite = gravite
                s.remesurer()
            s.avancer(duree)
            etapes.append({
                'duree': h(duree), 'masse': masse, 'gravite': gravite, 't': h(s.t), 'etat': etat(s),
                'periodes': [None if s.periode(i) is None else h(s.periode(i)) for i in range(len(s.corps))],
                'derives': [h(x) for x in s.derives()],
                'courbure': None if s.courbure_lune() is None else h(s.courbure_lune()),
                'n_traces': [len(t.x) for t in s.traces],
                'pas': s.derniers_pas,
            })
        cas[nom] = {'pas_trace': h(s.pas_trace), 'depart': depart, 'etapes': etapes}
    texte = json.dumps(cas, indent=0, sort_keys=True) + '\n'
    (ICI / 'tests' / 'gravite_cas.json').write_text(texte, encoding='utf-8')
    if len(sys.argv) > 1:
        (Path(sys.argv[1]) / 'tests' / 'references' / 'gravite_cas.json').write_text(texte, encoding='utf-8')
    print('%d scénarios' % len(cas))


if __name__ == '__main__':
    main()
