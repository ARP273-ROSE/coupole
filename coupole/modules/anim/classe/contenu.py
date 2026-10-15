"""Contenus des modules (mêmes données que Coupole Web, importées par outils/importer_contenu.py) : modules, questions,
fiches, tables, schémas, images, ressources liées, index de recherche.  Lecture paresseuse, une fois par session."""
from __future__ import annotations

import functools
import gzip
import json
import re
import unicodedata
from pathlib import Path

from ....core.i18n import langue, tr

DOSSIER = Path(__file__).with_name('donnees')
GENRES = ('question', 'animation', 'fiche', 'table', 'image')


@functools.lru_cache(maxsize=None)
def _lire(nom: str):
    with gzip.open(DOSSIER / (nom + '.json.gz'), 'rt', encoding='utf-8') as f:
        return json.load(f)


def bi(v, lg: str | None = None) -> str:
    """Texte dans la langue (objet {fr, en}) ou tel quel."""
    if isinstance(v, dict):
        return str(v.get(lg or langue()) or v.get('en') or v.get('fr') or '')
    return '' if v is None else str(v)


def modules() -> list:
    return _lire('modules')['modules']


def module(cle: str):
    return next((m for m in modules() if m['cle'] == cle), None)


@functools.lru_cache(maxsize=None)
def _questions() -> dict:
    return {q['id']: q for q in _lire('questions')['questions']}


def question(qid: str):
    return _questions().get(qid)


def toutes_les_questions() -> dict:
    return _questions()


def macros() -> dict:
    return _lire('macros')['macros']


def jetons() -> dict:
    return _lire('couleurs')['jetons']


def fiche(i: str):
    return _lire('fiches').get(i)


def table(i: str):
    return _lire('tables').get(i)


def schema(i: str):
    return _lire('schemas').get(i)


@functools.lru_cache(maxsize=None)
def _images() -> dict:
    return {i['id']: i for i in _lire('images')['images']}


def image(i: str):
    return _images().get(i)


@functools.lru_cache(maxsize=None)
def images_questions() -> dict:
    try:
        return {i['id']: i for i in _lire('images_questions')['images']}
    except FileNotFoundError:
        return {}


def chemin_image(fichier_ou_id: str) -> Path:
    return DOSSIER / 'images' / (Path(fichier_ou_id).name if fichier_ou_id.endswith('.webp') else fichier_ou_id + '.webp')


def sources() -> dict:
    return _lire('sources')


def liees(qid: str) -> dict:
    return _lire('relevant').get(qid, {})


def info_questions() -> dict:
    """id → {n, ok, titre(bi), module} (premier module qui contient la question)."""
    out = {}
    for m in modules():
        for q in m['questions']:
            out.setdefault(q['id'], {'n': q['n'], 'ok': q['ok'], 't': q['t'], 'module': m['cle']})
    return out


def titre(genre: str, i: str) -> str:
    """Titre d'une ressource dans la langue courante."""
    if genre == 'animation':
        from .. import catalogue
        e = catalogue.PAR_ID.get(i)
        return tr('anim_nom_' + e.cle) if e else i
    if genre == 'question':
        q = info_questions().get(i)
        return bi(q['t']) if q and q['t'] else i
    o = {'fiche': fiche, 'table': table, 'image': image}[genre](i)
    return bi(o['titre']) if o else i


# ------------------------------------------------------------------ recherche (moteur commun avec Coupole Web)
def documents() -> list:
    """Documents de la recherche, construits comme au web (`src/app/page_recherche.ts`, `documents()`) : questions,
    fiches, tables, images (index importé), animations (noms, descriptions, titres d'origine, thèmes), modules."""
    from .. import catalogue
    from ....core import i18n, modules as M
    M.decouvrir()                                      # textes des animations enregistrés (noms, descriptions)
    genre = {'q': 'question', 'f': 'fiche', 't': 'table', 'i': 'image'}
    out = []
    for e in _lire('recherche')['entrees']:
        out.append({'g': genre[e['g']], 'id': e['id'], 'm': e['m'], 't': e['t'], 'k': e['k'], 'r': e['r']})
    T = i18n.toutes_les_cles()
    for a in catalogue.ENTREES:
        if not a.faite:
            continue
        t = {lg: T.get('anim_nom_' + a.cle, {}).get(lg, a.titre) for lg in ('fr', 'en')}
        th = {lg: T.get('anim_theme_' + a.theme, {}).get(lg, '') for lg in ('fr', 'en')}
        out.append({'g': 'animation', 'id': a.id, 'm': [], 't': t, 'o': a.titre,
                    'k': {'fr': a.id + ' ' + th['fr'], 'en': th['en']},
                    'r': {lg: T.get('anim_desc_' + a.cle, {}).get(lg, '') for lg in ('fr', 'en')}})
    for m in modules():
        out.append({'g': 'module', 'id': m['cle'], 'm': [m['cle']], 't': m['titre'], 'o': m.get('original') or '',
                    'k': {'fr': m['cle'], 'en': ''}, 'r': {'fr': '', 'en': ''}})
    return out


@functools.lru_cache(maxsize=None)
def index():
    from .recherche import Index
    return Index(documents())


def chercher(texte: str) -> list:
    """Résultats du moteur commun : [{doc, n, score, mots}] (questions absentes de tout module écartées)."""
    info = info_questions()
    return [r for r in index().chercher(texte) if r['doc']['g'] != 'question' or (r['doc']['id'] in info and info[r['doc']['id']]['ok'])]
