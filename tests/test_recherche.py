"""Recherche bilingue (0.7.1) : moteur commun avec Coupole Web.  Les cas de tests/recherche_cas.json (produits par
outils/cas_recherche.py) sont rejoués ici et par tests/unit/recherche.test.ts au web : mêmes fonctions, mêmes
résultats sur un petit corpus et sur les vrais contenus (817 documents)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from coupole.modules.anim.classe import contenu
from coupole.modules.anim.classe import recherche as R

CAS = json.loads((Path(__file__).with_name('recherche_cas.json')).read_text('utf-8'))


def _resume(r):
    return {'g': r['doc']['g'], 'id': r['doc']['id'], 'n': r['n'], 'score': r['score'], 'mots': r['mots']}


def test_unitaires_identiques_au_web():
    u = CAS['unitaires']
    for a, b in u['normaliser']:
        assert R.normaliser(a) == b
    for a, b in u['mots']:
        assert R.mots(a) == b
    for a, b in u['racine']:
        assert R.racine(a) == b, a
    for a, b in u['termes']:
        assert R.termes(a) == b, a
    for a, b, k, d in u['distance']:
        assert R.distance(a, b, k) == d, (a, b)
    for t, mots, attendu in u['surligner']:
        assert [list(x) for x in R.surligner(t, mots)] == attendu
    for t, mots, lg, attendu in u['extrait']:
        assert R.extrait(t, set(mots), lg) == attendu


def test_corpus_identique_au_web():
    idx = R.Index(CAS['corpus']['documents'])
    for q, attendu in CAS['corpus']['requetes']:
        assert [_resume(r) for r in idx.chercher(q)] == attendu, q


def test_vrais_contenus_identiques_au_web():
    idx = contenu.index()
    assert len(idx.docs) == CAS['reel']['documents']
    assert len(idx.vocab) == CAS['reel']['vocabulaire']
    for q, attendu in CAS['reel']['requetes']:
        assert [_resume(r) for r in idx.chercher(q, 8)] == attendu, q


def _premiers(q, g, n=3):
    return [r['doc']['id'] for r in contenu.index().chercher(q) if r['doc']['g'] == g][:n]


def test_bilingue_accents_pluriels_fautes():
    assert 'eclipticsimulator' in _premiers('seasons', 'animation')
    assert 'eclipticsimulator' in _premiers('saisons', 'animation')
    assert _premiers('Kepler’s third law', 'animation', 1) == ['keplers_third']
    assert _premiers('troisième loi de Kepler', 'animation', 1) == ['keplers_third']
    assert _premiers('anticythère', 'animation', 1) == ['antikythera']
    assert _premiers('notions de base', 'module', 1) == ['intro']
    for q in ('Rétrograde', 'retrograde', 'RETROGRADES', 'retrogarde'):
        assert _premiers(q, 'animation', 1) == ['retrograde'], q
    assert contenu.index().chercher('xqzwv') == []


def test_surlignage_dans_la_langue_affichee():
    r = contenu.index().chercher('saisons')
    e = next(x for x in r if x['doc']['id'] == 'eclipticsimulator')
    morceaux = R.surligner(e['doc']['t']['fr'], e['mots'])
    assert ('saisons', True) in morceaux


def test_recherche_rapide():
    idx = contenu.index()
    t = time.perf_counter()
    for q in ('seasons', 'kepler third law', 'paralaxe', 'galaxies', 'phases de la lune') * 4:
        idx.chercher(q)
    assert time.perf_counter() - t < 6.0                # 20 recherches (≈ 50 ms chacune sur le NAS)
