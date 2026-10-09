"""Inventaire : conformité au classement de référence, tolérance aux changements de la base, anomalies."""
import json
import sys

import pytest

from coupole.modules.ohp import anomalies, cibles, inventaire, selection
from coupole.modules.ohp.astrometrie import attentes


def test_instantane_livre(inventaire):
    assert len(inventaire.images) == 7989
    assert sum(x['doublon'] for x in inventaire.images) == 144
    assert len(inventaire.objets()) == 166
    assert sum(x['date_partagee'] for x in inventaire.images) == 1654


def test_identique_au_classement_de_reference(inventaire, reference):
    sys.path.insert(0, str(reference))
    import cibles as ref
    d0 = ref.charger(str(reference / 'inventaire.json'))
    a = {x['access_url']: x for x in d0}
    b = {x['access_url']: x for x in inventaire.images}
    assert set(a) == set(b)
    for cle in ('nuit', 'tel', 'objet', 'cat', 'sbdb', 'rem', 'doublon', 'date_partagee', 'diurne'):
        assert sum(a[u][cle] != b[u][cle] for u in a) == 0, cle


def _lignes(inventaire, n=300):
    l, _ = inventaire_brut()
    return [dict(x) for x in l[:n]]


def inventaire_brut():
    return inventaire.lire(inventaire.INSTANTANE)


def test_colonnes_en_plus_ou_en_moins():
    l, _ = inventaire_brut()
    brut = [dict(x) for x in l[:200]]
    for x in brut:
        x.pop('s_region')
        x.pop('facility_name')
        x['nouvelle_colonne_obscore'] = 'x'
    lignes = [inventaire._convertir(x) for x in brut]
    d = inventaire.enrichir(lignes)
    assert len(d) == 200 and all('objet' in x for x in d)
    attentes(d)                                        # pas de s_region : angle inconnu, aucune erreur
    anomalies.detecter(d, attentes(d)[1])


def test_valeurs_malformees_et_nouveautes_de_la_base():
    l, _ = inventaire_brut()
    base = [dict(x) for x in l[:50]]
    neuf = dict(base[0], access_url='http://exemple/nouveau1.fits', instrument_name='T193 SOPHIE', filter_name='Lyot-Ha',
                target_name='Objet Jamais Vu 2027', t_exptime='abc', s_ra='', dataproduct_type='spectrum')
    lignes = [inventaire._convertir(x) for x in base + [neuf]]
    d = inventaire.enrichir(lignes)
    x = next(y for y in d if y['access_url'].endswith('nouveau1.fits'))
    assert x['tel'] == 'T193SOPHIE' and x['t_exptime'] == 0.0 and x['cat'] in cibles.CATEGORIES
    assert x['a_verifier'] and not x['diurne']           # spectre : jamais « de jour »
    an = anomalies.detecter(d, attentes(d)[1])
    assert any(a['genre'] == 'instrument' for a in an) and any(a['genre'] == 'classement' for a in an)
    # tout le reste de la chaîne passe
    est = selection.estimer(d, 'xisf')
    assert est['images'] == len([y for y in d if not y['doublon']])


def test_alias_par_position():
    l, _ = inventaire_brut()
    ngc = next(x for x in l if x['target_name'] == 'NGC 6888')
    inconnu = dict(ngc, access_url='http://exemple/croissant.fits', target_name='Croissant de Test')
    d = inventaire.enrichir([inventaire._convertir(x) for x in l[:400] + [ngc, inconnu]])
    x = next(y for y in d if y['access_url'].endswith('croissant.fits'))
    assert x['objet'] == 'NGC 6888' and x['classement'] == 'position' and x['a_verifier']


def test_correction_utilisateur_memorisee():
    cibles.corriger('Croissant de Test', 'NGC 6888', 'neb')
    try:
        assert cibles.classer('Croissant de Test')[:2] == ('NGC 6888', 'neb')
        assert cibles.classer('Croissant de Test')[4] == 'utilisateur'
    finally:
        cibles.corriger('Croissant de Test', None)
    assert cibles.classer('Croissant de Test')[4] == 'inconnu'


def test_nouveautes_detectees(tmp_path, monkeypatch):
    from coupole.core import config
    monkeypatch.setattr(inventaire, 'chemin_historique', lambda: tmp_path / 'h.json')
    l, _ = inventaire_brut()
    n1 = inventaire.noter_vus(l[:100], '2026-10-01')
    assert n1['premiere'] and not n1['images']
    neuf = dict(l[0], access_url='http://exemple/ete2027.fits', target_name='2027 AB1')
    n2 = inventaire.noter_vus(l[:100] + [neuf], '2027-08-30')
    assert n2['images'] == ['http://exemple/ete2027.fits'] and n2['noms'] == ['2027 AB1']
    assert n2['depuis'] == '2026-10-01'


def test_anomalies_de_la_banque(inventaire):
    an = anomalies.detecter(inventaire.images, attentes(inventaire.images)[1])
    r = anomalies.resume(an)
    assert r['meme_fichier'] + r['copie_diurne'] == 144       # les 144 doublons, chacun expliqué
    assert r['date_partagee'] == 1654
    assert all(a['action'] == 'ecartee' for a in an if a['genre'] in anomalies.ECARTEES)


def test_selection_et_estimation(inventaire):
    objs = selection.objets_correspondants(inventaire.images, 'Pluto')      # nom anglais accepté
    assert objs == ['(134340) Pluton']
    sel = selection.selectionner(inventaire.images, selection.Criteres(objets=['NGC 6888'], filtres=['B', 'V', 'R'],
                                                                           nuits=['2025-07-16']))
    est = selection.estimer(sel)
    assert est['images'] == 800 and 6.5e9 < est['octets_fits'] < 7.0e9
