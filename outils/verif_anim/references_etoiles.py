"""Références croisées bureau ⇄ web d'« Orion en 3D », des fiches au survol et de leur placement : la géométrie
(orion3d_geo.py ↔ orion3d.ts), le contenu des fiches (fiche_texte.py ↔ fiche_texte.ts, FR et EN) et la pose de la
fiche flottante (fiche_flottante.placer_fiche ↔ placer_fiche) sont calculés ici en Python ; les deux suites de tests
(tests/test_anim_orion3d.py et, dans Coupole Web, tests/unit/orion3d.test.ts) les retrouvent à 10⁻⁹ près.

Usage : python3 outils/verif_anim/references_etoiles.py   (écrit tests/orion3d_reference.json)"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ICI))


def main() -> None:
    from coupole.core import i18n
    from coupole.modules.anim import orion3d_geo as O
    from coupole.modules.anim.fiche_texte import contenu_fiche
    from coupole.modules.anim.fiches import toutes_les_fiches
    from coupole.modules.anim.fiche_flottante import placer_fiche
    from coupole.modules.anim import textes  # noqa: F401  (enregistre les textes)
    try:
        from coupole.cli import initialiser
        initialiser('fr')
    except Exception:
        pass
    g = random.Random(2026)
    cameras = []
    cibles = ('orion', 'm42', 'tete')
    for k in range(40):
        a, b = g.choice(cibles), g.choice(cibles)
        args = [a, b, round(g.random(), 3), round(g.random(), 3), round(g.uniform(-180, 180), 2),
                round(g.uniform(-80, 80), 2), g.choice((360, 800, 1280)), g.choice((420, 560, 720))]
        if k < 3:
            args = ['orion', 'orion', 1.0, 0.0, 0.0, 0.0, 800, 600] if k == 0 else \
                ['m42', 'm42', 1.0, 1.0, 0.0, 0.0, 800, 600] if k == 1 else ['orion', 'tete', 0.5, 0.5, 30.0, 10.0, 640, 480]
        c = O.camera(*args)
        pts = []
        for e in O.DONNEES['etoiles'][::7]:
            pts.append(O.projeter(c, O.deplier(e['xyz'], args[3])))
        cameras.append({'args': args, 'camera': {k2: (list(v) if isinstance(v, tuple) else v) for k2, v in c.items()},
                        'projections': [list(p) if p else None for p in pts]})
    coquille = [list(O.point_coquille(O.direction(ra, dec), O.DONNEES['icrs_vers_gal']))
                for ra, dec in ((80, -4), (88, 0), (85, -10), (78, 5))]
    fiches = toutes_les_fiches()
    ids = sorted(fiches)
    choisies = [i for i in ids if i.startswith('orion:')][:40:3] + ids[::23] + ['orion:tet01_ori_c', 'orion:m42',
                                                                             'orion:eps_ori', 'orion:alf_ori']
    contenus = {}
    for lg in ('fr', 'en'):
        i18n.choisir_langue(lg)
        contenus[lg] = {i: contenu_fiche(fiches[i], lg) for i in dict.fromkeys(choisies)}
    poses = []
    for _ in range(300):
        W, H = g.choice((360, 800, 1280)), g.choice((420, 600, 760))
        w, h = g.uniform(120, 300), g.uniform(60, 260)
        x, y, r = g.uniform(0, W), g.uniform(0, H), g.uniform(2, 30)
        poses.append({'entree': [x, y, r, w, h, W, H], 'sortie': list(placer_fiche(x, y, r, w, h, W, H))})
    sortie = ICI / 'tests' / 'orion3d_reference.json'
    sortie.write_text(json.dumps({'cameras': cameras, 'coquille': coquille, 'fiches': contenus, 'placements': poses},
                                 ensure_ascii=False, indent=0) + '\n', encoding='utf-8')
    print(sortie, sortie.stat().st_size, 'octets')


if __name__ == '__main__':
    main()
