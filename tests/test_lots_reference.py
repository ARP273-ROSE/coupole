"""Tri en lots et comparaison avec le traitement de référence (INDEX_LOTS.csv, journal.csv)."""
import csv
import json

import pytest

from coupole.modules.ohp import lots
from coupole.modules.ohp.conversion import sur


def info(objet, cat, nuit, mjd, ra, dec, filtre='R', wcs='confirmee', tel='T120', nx=1024, angle=180.0, ech=0.77):
    return {'objet': objet, 'cat': cat, 'nuit': nuit, 'mjd': mjd, 'ra': ra, 'dec': dec, 'filtre': filtre,
            'filtre_dossier': filtre, 'wcs': wcs, 'tel': tel, 'nx': nx, 'angle': angle, 'echelle': ech, 'parite': 1,
            'pose': 30.0, 'debut': '2025-07-16T22:00:00.000', 'nom_base': objet, 'filtre_sys': 'Johnson'}


def test_fixes_par_champ_mobiles_par_nuit():
    tout = [('a', info('NGC 6888', 'neb', '2025-07-16', 1, 303.0, 38.35)),
            ('b', info('NGC 6888', 'neb', '2023-07-10', 2, 303.01, 38.36)),          # même champ, autre nuit
            ('c', info('NGC 6888', 'neb', '2023-07-10', 3, 302.5, 38.0)),            # autre pointage
            ('d', info('(3) Juno', 'ast', '2026-07-13', 4, 280.0, -10.0)),
            ('e', info('(3) Juno', 'ast', '2026-07-14', 5, 280.2, -10.1)),
            ('f', info('M27', 'pn', '2026-07-13', 6, 299.9, 22.7, wcs='echec'))]
    plan = lots.plan_des_lots(tout, 'fr')
    cles = {k: sorted(i for i, _ in v) for k, v in plan.items()}
    assert cles[('07_Nebuleuses', 'NGC_6888', 'champ_1_T120', 'R')] == ['a', 'b']
    assert cles[('07_Nebuleuses', 'NGC_6888', 'champ_2_T120', 'R')] == ['c']
    assert cles[('01_Asteroides', '3_Juno', 'nuit_2026-07-13_T120', 'R')] == ['d']
    assert cles[('01_Asteroides', '3_Juno', 'nuit_2026-07-14_T120', 'R')] == ['e']
    assert cles[('_sans_solution_astrometrique', 'M27', '2026-07-13_T120', 'R')] == ['f']
    en = lots.plan_des_lots(tout, 'en')
    assert ('07_Nebulae', 'NGC_6888', 'field_1_T120', 'R') in en


def test_noms_surs_sous_windows():
    assert sur('C/2021 S3 (PANSTARRS)') == 'C2021_S3_PANSTARRS'
    assert sur('53P/Van Biesbroeck') == '53P_Van_Biesbroeck'
    assert sur('(136199) Éris') == '136199_Eris'


def test_noms_de_dossiers_de_la_reference(reference, inventaire):
    """Chaque dossier d'objet de INDEX_LOTS.csv se retrouve à partir des objets de l'inventaire."""
    with open(reference / 'traitement' / 'INDEX_LOTS.csv', encoding='utf-8-sig') as f:
        rangs = list(csv.reader(f, delimiter=';'))[1:]
    objets = {sur(x['objet']) for x in inventaire.images}
    from coupole.modules.ohp.cibles import CATEGORIES
    types = {v[0] for v in CATEGORIES.values()} | {lots.SANS['fr']}
    for r in rangs:
        t, o = r[0].split('/')[:2]
        assert t in types and o in objets, r[0]


def test_journal_de_reference_coherent(reference, inventaire):
    """Statuts de la référence : 7 625 converties, 364 doublons ; nos clés d'identité retrouvent chaque ligne."""
    with open(reference / 'traitement' / 'journal.csv', encoding='utf-8-sig') as f:
        rangs = list(csv.DictReader(f, delimiter=';'))
    from collections import Counter
    st = Counter(r['statut'] for r in rangs)
    assert st['ok'] == 7625 and st['doublon'] == 364
    urls = {x['access_url'] for x in inventaire.images}
    assert all(r['url'] in urls for r in rangs)
    # les doublons d'inventaire de la référence sont exactement les nôtres
    ref_dbl = {r['url'] for r in rangs if r['statut'] == 'doublon' and not r['destination']}
    nos_dbl = {x['access_url'] for x in inventaire.images if x['doublon']}
    assert nos_dbl <= ref_dbl
