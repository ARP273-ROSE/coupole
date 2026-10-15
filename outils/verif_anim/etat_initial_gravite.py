#!/usr/bin/env python3
"""État initial réel du scénario « Soleil, Terre et Lune » de l'animation « Gravité et orbites » : positions et
vitesses du Soleil, de la Terre et de la Lune le 1er janvier 2026 à 0 h TDB, par l'éphéméride DE440 (skyfield +
de440s.bsp ; lancé dans python-lab), dans le repère de l'écliptique J2000, ramenés dans le plan de l'écliptique en
faisant tourner chaque orbite (Terre autour du Soleil, Lune autour de la Terre) autour de sa ligne des nœuds : la
distance, la vitesse et leur produit scalaire sont gardés, donc le demi-grand axe, l'excentricité et la période
(une simple projection, z oublié, raccourcirait l'orbite de la Lune inclinée de 5° : 26,99 j au lieu de 27,3 j) ;
puis tourné pour que la Terre parte à droite du Soleil (axe +x), barycentre des trois corps au repos à l'origine.

    python etat_initial_gravite.py de440s.bsp sortie.json

Pourquoi : une Lune lancée sur un cercle de Kepler autour de la Terre, dans le champ de marée du Soleil, prend une
orbite déformée dont la période moyenne dépend de la phase de départ (27,05 à 27,81 j au lieu de 27,32 j) ; avec
l'état réel, le mois sidéral mesuré est le vrai.
"""
import json
import sys

import numpy as np
from skyfield.api import load
from skyfield.framelib import ecliptic_J2000_frame

GM = {'soleil': 1.3271244e20, 'terre': 3.986004e14, 'lune': 4.902800118e12}


def main(bsp, out):
    ts = load.timescale()
    eph = load(bsp)
    t = ts.tdb(2026, 1, 1, 0, 0, 0)
    noms = {'soleil': 'sun', 'terre': 'earth', 'lune': 'moon'}
    etat = {}
    for n, k in noms.items():
        p, v = eph[k].at(t).frame_xyz_and_velocity(ecliptic_J2000_frame)
        etat[n] = (np.array(p.m), np.array(v.m_per_s))

    def dans_le_plan(r, v):
        # rotation qui amène le moment cinétique r × v sur +z (autour de la ligne des nœuds)
        h = np.cross(r, v)
        h = h / np.linalg.norm(h)
        z = np.array([0.0, 0.0, 1.0])
        axe = np.cross(h, z)
        s = np.linalg.norm(axe)
        c = float(np.dot(h, z))
        if s < 1e-15:
            return r, v
        k = axe / s
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        Rm = np.eye(3) + s * K + (1 - c) * (K @ K)
        return Rm @ r, Rm @ v

    rs, vs = etat['soleil']
    rt, vt = etat['terre']
    rl, vl = etat['lune']
    rt2, vt2 = dans_le_plan(rt - rs, vt - vs)
    rl2, vl2 = dans_le_plan(rl - rt, vl - vt)
    plan = {'soleil': (rs * 0, vs * 0), 'terre': (rt2, vt2), 'lune': (rt2 + rl2, vt2 + vl2)}
    print('inclinaisons (°) : Terre %.4f, Lune %.4f' % tuple(
        np.degrees(np.arccos(np.cross(a, b)[2] / np.linalg.norm(np.cross(a, b)))) for a, b in
        ((rt - rs, vt - vs), (rl - rt, vl - vt))))
    for n in etat:
        r, v = plan[n]
        etat[n] = np.array([r[0], r[1], v[0], v[1]])
    # barycentre des trois corps au repos à l'origine (les masses n'interviennent que par leurs rapports)
    mt = sum(GM.values())
    b = sum(GM[n] * etat[n] for n in etat) / mt
    for n in etat:
        etat[n] = etat[n] - b
    # rotation : la Terre à droite du Soleil
    d = etat['terre'][:2] - etat['soleil'][:2]
    a = -np.arctan2(d[1], d[0])
    c, s = np.cos(a), np.sin(a)
    rot = np.array([[c, -s], [s, c]])
    res = {}
    for n in etat:
        p = rot @ etat[n][:2]
        v = rot @ etat[n][2:]
        res[n] = [float(p[0]), float(p[1]), float(v[0]), float(v[1])]
    res['_date'] = '2026-01-01T00:00:00 TDB'
    res['_rotation_deg'] = float(np.degrees(a))
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:3])
