#!/usr/bin/env python3
"""Cas communs de la mécanique du « Canon de Newton » (canon_meca.py ↔ src/calc/canon.ts de Coupole Web) : éléments
de Kepler de tirs variés, préréglages, contextes et verdicts des défis, densité de l'air, trajectoire prévue, puis
des tirs intégrés par une suite fixe d'appels de avancer() (état, temps, angle balayé, issue, tours, trace).  Sans
air, les deux programmes retrouvent les mêmes nombres au bit près (seulement + − × ÷ √) ; avec l'air, la densité
passe par exp(), dont le dernier bit peut différer d'un langage à l'autre : écart relatif toléré 10⁻⁹.

    python3 outils/cas_canon.py [CHEMIN_WEB]   → tests/canon_cas.json (et CHEMIN_WEB/tests/references/canon_cas.json)
"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
from coupole.modules.anim import canon_meca as C  # noqa: E402

TIRS = [
    # astre, altitude (m), vitesse (m·s⁻¹), angle (°), air, projectile, durée d'un appel (s), appels
    ('terre', 100e3, 5000.0, 0.0, False, 'boulet', 30.0, 20),
    ('terre', 100e3, 7844.134671376244, 0.0, False, 'boulet', 300.0, 40),
    ('terre', 100e3, 9607.0, 20.0, False, 'boulet', 900.0, 40),
    ('terre', 100e3, 11093.281637341306, 0.0, False, 'boulet', 3000.0, 40),
    ('terre', 100e3, 13586.0, -10.0, False, 'boulet', 3000.0, 40),
    ('terre', 100e3, 3000.0, 90.0, False, 'boulet', 60.0, 40),
    ('lune', 10e3, 1000.0, 30.0, False, 'boulet', 60.0, 40),
    ('dimorphos', 10.0, 0.0579, 0.0, False, 'boulet', 1000.0, 20),
    ('ceres', 2e3, 364.0, 5.0, False, 'boulet', 1000.0, 20),
    ('terre', 200e3, 7742.306851451222, 0.0, True, 'capsule', 120.0, 40),
    ('terre', 100e3, 5000.0, 0.0, True, 'boulet', 30.0, 20),
    ('terre', 180e3, 7796.143919940982, 0.0, True, 'satellite', 3000.0, 20),
    ('mars', 50e3, 2500.0, 10.0, True, 'boulet', 30.0, 20),
]


def etat(t):
    b = t.boulet
    return {'t': t.t, 'x': b.x, 'y': b.y, 'vx': b.vx, 'vy': b.vy, 'etat': t.etat, 'phi': t.phi, 'tours': t.tours(),
            'n_trace': len(t.x), 'h_min': t.h_min}


def el(e):
    return {k: (None if isinstance(v, float) and v != v else (str(v) if isinstance(v, float) and abs(v) == float('inf')
                                                                 else v)) for k, v in e.items()}


def main(web=None):
    out = {'elements': [], 'prereglages': {}, 'defis': {}, 'densites': [], 'coniques': [], 'tirs': []}
    for astre in C.NOMS_ASTRES:
        A = C.ASTRES[astre]
        for alt in (C.REGLAGES[astre]['a0'] * C.REGLAGES[astre]['ua'],):
            for kv in (0.3, 0.9, 1.0, 1.2, 1.35, 1.4142135623730951, 1.6):
                for ang in (0.0, 30.0, 90.0, -20.0):
                    r0 = A['r'] + alt
                    v = kv * C.v_satellisation(A['gm'], r0)
                    x, y, vx, vy = C.etat_tir(A['r'], alt, v, ang)
                    out['elements'].append({'astre': astre, 'alt': alt, 'v': v, 'angle': ang,
                                            'el': el(C.elements(A['gm'], A['r'], x, y, vx, vy))})
                    if ang in (0.0, 30.0) and kv in (0.3, 1.2, 1.35, 1.6):
                        e = C.elements(A['gm'], A['r'], x, y, vx, vy)
                        out['coniques'].append({'astre': astre, 'alt': alt, 'v': v, 'angle': ang,
                                                'pts': C.conique(e, x, y, A['r'], 4 * e['r'])})
        for p in C.PREREGLAGES:
            out['prereglages']['%s_%s' % (astre, p)] = C.prereglage(p, astre)
    for d in C.DEFIS:
        out['defis'][d] = C.contexte_defi(d)
    for astre in ('terre', 'mars', 'lune'):
        for h in (-10.0, 0.0, 12e3, 25e3, 99.9e3, 100e3, 150e3, 415e3, 999e3, 1500e3, 3e6):
            out['densites'].append([astre, h, C.densite(astre, h), C.hauteur_echelle(astre, h)
                                    if C.hauteur_echelle(astre, h) != float('inf') else 'inf'])
    for (astre, alt, v, ang, air, proj, dt, n) in TIRS:
        t = C.Tir(1, astre, alt, v, ang, air, proj)
        cas = {'astre': astre, 'alt': alt, 'v': v, 'angle': ang, 'air': air, 'projectile': proj, 'dt': dt,
               'depart': etat(t), 'etapes': [], 'verdicts': []}
        for _ in range(n):
            k = t.avancer(dt)
            e = etat(t)
            e['pas'] = k
            cas['etapes'].append(e)
            cas['verdicts'].append([list(C.juger(d, t)) for d in C.DEFIS])
        cas['trace'] = [t.x[::max(1, len(t.x) // 50)], t.y[::max(1, len(t.y) // 50)]]
        out['tirs'].append(cas)
    txt = json.dumps(out, indent=0, sort_keys=True) + '\n'
    (ICI / 'tests' / 'canon_cas.json').write_text(txt, encoding='utf-8')
    if web:
        (Path(web) / 'tests' / 'references' / 'canon_cas.json').write_text(txt, encoding='utf-8')
    print('%d tirs, %d éléments' % (len(out['tirs']), len(out['elements'])))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
