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


# ------------------------------------------------------------------ recherche (même règle que Coupole Web)
def normaliser(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


def mots(s: str) -> list:
    return [m for m in re.split(r'[^\w]+', normaliser(s)) if m and m != '_']


def noter(e: dict, cherches: list) -> tuple:
    """(nombre de mots trouvés, score) : préfixe d'un mot du titre (1,5), des mots-clés (1,3), du résumé (1)."""
    n, score = 0, 0.0
    for c in cherches:
        s = (1.5 if any(w.startswith(c) for w in e['titres']) else 0) + \
            (1.3 if any(w.startswith(c) for w in e['cles']) else 0) + \
            (1.0 if any(w.startswith(c) for w in e['resume']) else 0)
        if s:
            n += 1
        score += s
    return n, score


@functools.lru_cache(maxsize=None)
def _index() -> list:
    from .. import catalogue
    from ....core import i18n
    genre = {'q': 'question', 'f': 'fiche', 't': 'table', 'i': 'image'}
    out = []
    for e in _lire('recherche')['entrees']:
        out.append({'g': genre[e['g']], 'id': e['id'], 'm': e['m'], 't': e['t'],
                    'titres': mots(e['t']['fr'] + ' ' + e['t']['en']), 'cles': mots(e['k']['fr'] + ' ' + e['k']['en']),
                    'resume': mots(e['r']['fr'] + ' ' + e['r']['en'])})
    T = i18n.toutes_les_cles()
    for a in catalogue.ENTREES:
        if not a.faite:
            continue
        t = {lg: T.get('anim_nom_' + a.cle, {}).get(lg, a.titre) for lg in ('fr', 'en')}
        d = ' '.join(T.get('anim_desc_' + a.cle, {}).get(lg, '') for lg in ('fr', 'en'))
        th = ' '.join(T.get('anim_theme_' + a.theme, {}).get(lg, '') for lg in ('fr', 'en'))
        out.append({'g': 'animation', 'id': a.id, 'm': [], 't': t, 'titres': mots(t['fr'] + ' ' + t['en'] + ' ' + a.titre),
                    'cles': mots(a.id + ' ' + th), 'resume': mots(d)})
    return out


def chercher(texte: str) -> list:
    cherches = mots(texte)
    if not cherches:
        return []
    res = []
    for e in _index():
        n, s = noter(e, cherches)
        if n:
            res.append((n, s, e))
    res.sort(key=lambda x: (-x[0], -x[1]))
    return [e for _, _, e in res]
