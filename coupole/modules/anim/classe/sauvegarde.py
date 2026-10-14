"""Sauvegarde de la progression — format commun à Coupole Web et à Coupole (bureau), version 1.

Portage Python, fonction pour fonction, de `coupole-web/src/contenu/sauvegarde.ts` (même logique, mêmes noms en
snake_case) ; destiné à `coupole/modules/anim/classe/sauvegarde.py`.  Sans dépendance, sans entrée-sortie : le
stockage (fichier JSON dans le dossier de données de l'utilisateur, écriture atomique) reste à l'application.
Format et règles : `SAUVEGARDE.md` ; schéma : `sauvegarde.schema.json` ; parité : `sauvegarde_cas.json`, rejoué
par `test_sauvegarde.py` et `sauvegarde.test.ts`.

Points de fidélité au JavaScript : longueurs de chaînes comptées en unités UTF-16, `trim` JavaScript, ordre des clés
d'objet (clés « entières » d'abord, croissantes), nombres écrits comme `String(x)`, `Math.round`, expressions
rationnelles en ASCII ancrées sur toute la chaîne.
"""
from __future__ import annotations

import copy
import json
import math
import random
import re
import time
from datetime import datetime, timezone

FORMAT = 'coupole-sauvegarde'
VERSION = 1
MAX_TENTATIVES = 50
GENRES = ('question', 'animation', 'fiche', 'table', 'image')
PARTIES = ('animation', 'module', 'reglages', 'reponses', 'mes_modules', 'preferences', 'tout')

_CLE = re.compile(r'[A-Za-z0-9_:.\-]{1,80}')
_CLE_REGLAGE = re.compile(r'[A-Za-z0-9_]{1,40}')
_DATE = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,3})?Z')
_EPOQUE = '1970-01-01T00:00:00Z'
_ESPACES_JS = '\t\n\v\f\r                  　﻿'


# ------------------------------------------------------------------ outils de fidélité au JavaScript
def _lg(s: str) -> int:
    """Longueur JavaScript (unités UTF-16)."""
    return len(s.encode('utf-16-le', 'surrogatepass')) // 2


def _tranche(s: str, n: int) -> str:
    """`s.slice(0, n)` en unités UTF-16."""
    if _lg(s) <= n:
        return s
    b = s.encode('utf-16-le', 'surrogatepass')[:2 * n]
    return b.decode('utf-16-le', 'surrogatepass')


def _trim(s: str) -> str:
    return s.strip(_ESPACES_JS)


def _est_nombre(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _objet(v):
    return v if isinstance(v, dict) else None


def _cles_tri(o: dict) -> list:
    """`Object.keys(o).sort()` : tri par unités UTF-16."""
    return sorted(o.keys(), key=lambda k: k.encode('utf-16-be', 'surrogatepass'))


def _index_tableau(k: str) -> bool:
    return bool(re.fullmatch(r'0|[1-9][0-9]*', k)) and int(k) < 4294967295


def _ordre_js(d: dict) -> dict:
    """Ordre d'énumération d'un objet JavaScript : clés « entières » croissantes, puis ordre d'insertion."""
    ent = sorted((k for k in d if _index_tableau(k)), key=int)
    return {**{k: d[k] for k in ent}, **{k: v for k, v in d.items() if not _index_tableau(k)}}


def nombre_js(x) -> str:
    """Écriture d'un nombre identique à String(x) en JavaScript."""
    x = float(x)
    if x != x:
        return 'NaN'
    if x in (math.inf, -math.inf):
        return 'Infinity' if x > 0 else '-Infinity'
    if x == 0:
        return '0'
    r = repr(x)
    neg = r.startswith('-')
    if neg:
        r = r[1:]
    m, e = (r.split('e')[0], int(r.split('e')[1])) if 'e' in r else (r, 0)
    a, b = m.split('.') if '.' in m else (m, '')
    if b == '0':
        b = ''
    chiffres = (a + b).lstrip('0')
    e10 = len(a.lstrip('0')) - 1 + e if a.strip('0') else -(len(b) - len(b.lstrip('0'))) - 1 + e
    chiffres = chiffres.rstrip('0') or '0'
    k, n = len(chiffres), e10 + 1
    if k <= n <= 21:
        s = chiffres + '0' * (n - k)
    elif 0 < n <= 21:
        s = chiffres[:n] + '.' + chiffres[n:]
    elif -6 < n <= 0:
        s = '0.' + '0' * (-n) + chiffres
    else:
        ex = n - 1
        s = chiffres[0] + ('.' + chiffres[1:] if k > 1 else '') + 'e' + ('+' if ex >= 0 else '-') + str(abs(ex))
    return ('-' if neg else '') + s


def json_js(v, indent: int | None = None, _niveau: int = 0) -> str:
    """`JSON.stringify(v, null, indent)` (ordre des clés JavaScript, nombres comme String(x))."""
    if v is None:
        return 'null'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if _est_nombre(v):
        return nombre_js(v) if math.isfinite(v) else 'null'
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    sep, fin = ('\n' + ' ' * (indent * (_niveau + 1)), '\n' + ' ' * (indent * _niveau)) if indent else ('', '')
    if isinstance(v, (list, tuple)):
        if not v:
            return '[]'
        return '[' + ','.join(sep + json_js(x, indent, _niveau + 1) for x in v) + fin + ']'
    if isinstance(v, dict):
        if not v:
            return '{}'
        deux = ': ' if indent else ':'
        return '{' + ','.join(sep + json.dumps(k, ensure_ascii=False) + deux + json_js(x, indent, _niveau + 1) for k, x in _ordre_js(v).items()) + fin + '}'
    raise TypeError(type(v))


def _clone(v):
    return copy.deepcopy(v)


# ------------------------------------------------------------------ base
def maintenant() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def vide(application: str = '', date: str = _EPOQUE) -> dict:
    return {'format': FORMAT, 'version': VERSION, 'application': application, 'modifie': date, 'preferences': {},
            'animations': {}, 'questions': {}, 'modules': {}, 'mes_modules': []}


def _date(v, defaut: str = _EPOQUE) -> str:
    return v if isinstance(v, str) and _DATE.fullmatch(v) else defaut


def _texte(v, maxi: int = 200):
    return v if isinstance(v, str) and _lg(v) <= maxi else None


def reglages_valides(v) -> dict:
    """Valeurs acceptées : nombres finis, booléens, chaînes courtes (≤ 80), null ; clés simples."""
    out = {}
    o = _objet(v)
    if o is None:
        return out
    for k in _cles_tri(o):
        if not _CLE_REGLAGE.fullmatch(k):
            continue
        x = o[k]
        if isinstance(x, bool):
            out[k] = x
        elif _est_nombre(x) and math.isfinite(x):
            out[k] = x
        elif isinstance(x, str) and _lg(x) <= 80:
            out[k] = x
        elif x is None:
            out[k] = None
    return _ordre_js(out)


def _tentative_valide(v):
    o = _objet(v)
    if o is None:
        return None
    rep = [x for x in o.get('reponse') if isinstance(x, str) and _lg(x) <= 40][:26] if isinstance(o.get('reponse'), list) else []
    prm = {}
    p = _objet(o.get('parametres'))
    if p is not None:
        for k in _cles_tri(p):
            if _CLE.fullmatch(k) and isinstance(p[k], str) and _lg(p[k]) <= 80:
                prm[k] = p[k]
    g = _texte(o.get('graine'), 80)
    return {'date': _date(o.get('date')), 'reponse': rep, 'juste': o.get('juste') is True, 'parametres': _ordre_js(prm),
            'graine': '0' if g is None else g}


def _suivi_valide(v):
    o = _objet(v)
    if o is None:
        return None
    t = [x for x in (_tentative_valide(y) for y in o['tentatives']) if x is not None] if isinstance(o.get('tentatives'), list) else []
    t.sort(key=lambda x: x['date'])
    return {'tentatives': t[-MAX_TENTATIVES:], 'reponse_vue': o.get('reponse_vue') is True,
            'indice_vu': o.get('indice_vu') is True, 'a_revoir': o.get('a_revoir') is True}


def _element_valide(v):
    o = _objet(v)
    if o is None:
        return None
    g = o.get('genre')
    i = _texte(o.get('id'), 80)
    if not i or not _CLE.fullmatch(i) or not isinstance(g, str) or g not in GENRES:
        return None
    return {'genre': g, 'id': i}


def _mon_module_valide(v):
    o = _objet(v)
    if o is None:
        return None
    i = _texte(o.get('id'), 80)
    nom = _texte(o.get('nom'), 120)
    if not i or not _CLE.fullmatch(i) or nom is None:
        return None
    els, vus = [], set()
    for e in (o['elements'] if isinstance(o.get('elements'), list) else []):
        x = _element_valide(e)
        if x is None:
            continue
        k = x['genre'] + ':' + x['id']
        if k in vus:
            continue
        vus.add(k)
        els.append(x)
    return {'id': i, 'nom': _trim(nom) or i, 'cree': _date(o.get('cree')), 'modifie': _date(o.get('modifie')), 'elements': els[:2000]}


def migrer(brut, application: str = ''):
    """Toute sauvegarde (version 0 ou 1, éventuellement abîmée) → sauvegarde version 1 valide, sans jamais d'erreur.
    Une version future rend None (pour ne rien écraser)."""
    o = _objet(brut)
    if o is None:
        return vide(application)
    version = o['version'] if _est_nombre(o.get('version')) else 0
    if version > VERSION:
        return None
    s = vide(application, _date(o.get('modifie')))
    if version == 0:
        r = _objet(o.get('reglages'))
        if r is not None:
            for i in _cles_tri(r):
                if _CLE.fullmatch(i):
                    x = reglages_valides(r[i])
                    if x:
                        s['animations'][i] = {'reglages': x, 'modifie': s['modifie']}
            s['animations'] = _ordre_js(s['animations'])
        for k in ('theme', 'langue'):
            if isinstance(o.get(k), str):
                s['preferences'][k] = o[k]
        return s
    if o.get('format') != FORMAT:
        return vide(application)
    p = _objet(o.get('preferences'))
    if p is not None:
        for k in _cles_tri(p):
            x = reglages_valides({k: p[k]})
            if k in x:
                s['preferences'][k] = x[k]
        s['preferences'] = _ordre_js(s['preferences'])
    a = _objet(o.get('animations'))
    if a is not None:
        for i in _cles_tri(a):
            e = _objet(a[i])
            if not _CLE.fullmatch(i) or e is None:
                continue
            s['animations'][i] = {'reglages': reglages_valides(e.get('reglages')), 'modifie': _date(e.get('modifie'))}
        s['animations'] = _ordre_js(s['animations'])
    q = _objet(o.get('questions'))
    if q is not None:
        for i in _cles_tri(q):
            e = _suivi_valide(q[i])
            if _CLE.fullmatch(i) and e is not None:
                s['questions'][i] = e
        s['questions'] = _ordre_js(s['questions'])
    m = _objet(o.get('modules'))
    if m is not None:
        for i in _cles_tri(m):
            e = _objet(m[i])
            if not _CLE.fullmatch(i) or e is None:
                continue
            dq = _texte(e.get('derniere_question'), 80)
            s['modules'][i] = {'derniere_question': dq if dq and _CLE.fullmatch(dq) else None, 'visite': _date(e.get('visite'))}
        s['modules'] = _ordre_js(s['modules'])
    vus = set()
    for x in (o['mes_modules'] if isinstance(o.get('mes_modules'), list) else []):
        mm = _mon_module_valide(x)
        if mm is not None and mm['id'] not in vus:
            vus.add(mm['id'])
            s['mes_modules'].append(mm)
    return s


# ------------------------------------------------------------------ fusion (import « ajouter à mes données »)
def _plus_recent(a: str, b: str) -> bool:
    return b > a


def fusionner(a: dict, b: dict) -> dict:
    """Fusionne `b` (importée) dans `a` : tentatives réunies sans doublon, le plus récent l'emporte ailleurs."""
    s = migrer(_clone(a))
    for k, v in b['preferences'].items():
        s['preferences'][k] = v
    s['preferences'] = _ordre_js(s['preferences'])
    for i, e in b['animations'].items():
        x = s['animations'].get(i)
        if x is None or not _plus_recent(e['modifie'], x['modifie']):
            s['animations'][i] = {'reglages': dict(e['reglages']), 'modifie': e['modifie']}
    s['animations'] = _ordre_js(s['animations'])
    for i, e in b['questions'].items():
        x = s['questions'].get(i)
        if x is None:
            s['questions'][i] = _clone(e)
            continue
        cles = {json_js(t) for t in x['tentatives']}
        for t in e['tentatives']:
            if json_js(t) not in cles:
                x['tentatives'].append({**t, 'reponse': list(t['reponse']), 'parametres': dict(t['parametres'])})
        x['tentatives'].sort(key=lambda t: t['date'])
        x['tentatives'] = x['tentatives'][-MAX_TENTATIVES:]
        x['reponse_vue'] = x['reponse_vue'] or e['reponse_vue']
        x['indice_vu'] = x['indice_vu'] or e['indice_vu']
        x['a_revoir'] = x['a_revoir'] or e['a_revoir']
    s['questions'] = _ordre_js(s['questions'])
    for i, e in b['modules'].items():
        x = s['modules'].get(i)
        if x is None or not _plus_recent(e['visite'], x['visite']):
            s['modules'][i] = dict(e)
    s['modules'] = _ordre_js(s['modules'])
    for m in b['mes_modules']:
        k = next((j for j, x in enumerate(s['mes_modules']) if x['id'] == m['id']), -1)
        if k < 0:
            s['mes_modules'].append(_clone(m))
        elif not _plus_recent(m['modifie'], s['mes_modules'][k]['modifie']):
            s['mes_modules'][k] = _clone(m)
    s['modifie'] = a['modifie'] if a['modifie'] > b['modifie'] else b['modifie']
    return s


# ------------------------------------------------------------------ réinitialisation « tout ou partie »
def reinitialiser(s: dict, p: dict) -> dict:
    """p = {partie: animation, id} | {partie: module, id, questions[]} | {partie: reglages | reponses | mes_modules |
    preferences | tout}."""
    n = migrer(_clone(s))
    partie = p['partie']
    if partie == 'animation':
        n['animations'].pop(p['id'], None)
    elif partie == 'module':
        for q in p['questions']:
            n['questions'].pop(q, None)
        n['modules'].pop(p['id'], None)
    elif partie == 'reglages':
        n['animations'] = {}
    elif partie == 'reponses':
        n['questions'] = {}
        n['modules'] = {}
    elif partie == 'mes_modules':
        n['mes_modules'] = []
    elif partie == 'preferences':
        n['preferences'] = {}
    elif partie == 'tout':
        return vide(s['application'], s['modifie'])
    return n


# ------------------------------------------------------------------ questions et progression
def _suivi(s: dict, qid: str) -> dict:
    if qid not in s['questions']:
        s['questions'][qid] = {'tentatives': [], 'reponse_vue': False, 'indice_vu': False, 'a_revoir': False}
        s['questions'] = _ordre_js(s['questions'])
    return s['questions'][qid]


def noter_tentative(s: dict, qid: str, t: dict) -> None:
    e = _suivi(s, qid)
    e['tentatives'].append(t)
    if len(e['tentatives']) > MAX_TENTATIVES:
        del e['tentatives'][:len(e['tentatives']) - MAX_TENTATIVES]
    if not t['juste']:
        e['a_revoir'] = True


def marquer(s: dict, qid: str, champ: str, v: bool = True) -> None:
    assert champ in ('reponse_vue', 'indice_vu', 'a_revoir')
    _suivi(s, qid)[champ] = v


def etat_question(s: dict, qid: str) -> str:
    """'jamais' | 'vue' | 'reussie' | 'ratee' : la dernière tentative décide ; sans tentative, « vue » si la réponse
    (ou l'indice) a été montrée."""
    e = s['questions'].get(qid)
    if e is None:
        return 'jamais'
    if e['tentatives']:
        return 'reussie' if e['tentatives'][-1]['juste'] else 'ratee'
    return 'vue' if e['reponse_vue'] or e['indice_vu'] else 'jamais'


def bilan(s: dict, questions: list) -> dict:
    b = {'total': len(questions), 'essayees': 0, 'reussies': 0, 'ratees': 0, 'a_revoir': 0, 'tentatives': 0, 'score': 0, 'premier_coup': 0}
    for q in questions:
        e = s['questions'].get(q)
        et = etat_question(s, q)
        if et == 'reussie':
            b['reussies'] += 1
        if et == 'ratee':
            b['ratees'] += 1
        if e is not None:
            b['tentatives'] += len(e['tentatives'])
            if e['tentatives']:
                b['essayees'] += 1
            if e['tentatives'] and e['tentatives'][0]['juste']:
                b['premier_coup'] += 1
            if e['a_revoir'] or et == 'ratee':
                b['a_revoir'] += 1
    b['score'] = math.floor(100 * b['reussies'] / b['essayees'] + 0.5) if b['essayees'] else 0   # Math.round
    return b


# ------------------------------------------------------------------ « Mes modules »
_compteur = 0


def _base36(n: int) -> str:
    c = '0123456789abcdefghijklmnopqrstuvwxyz'
    s = ''
    while True:
        n, r = divmod(n, 36)
        s = c[r] + s
        if n == 0:
            return s


def nouvel_id(prefixe: str = 'mm') -> str:
    global _compteur
    _compteur = (_compteur + 1) % 1296
    return f'{prefixe}_{_base36(int(time.time() * 1000))}{_base36(random.randrange(46656)).rjust(3, "0")}{_base36(_compteur).rjust(2, "0")}'


def creer_module(s: dict, nom: str, elements: list | None = None, id: str | None = None, quand: str | None = None) -> dict:
    quand = quand or maintenant()
    m = _mon_module_valide({'id': id or nouvel_id(), 'nom': _tranche(nom, 120), 'cree': quand, 'modifie': quand, 'elements': elements or []})
    s['mes_modules'].append(m)
    return m


def trouver_module(s: dict, id: str):
    return next((m for m in s['mes_modules'] if m['id'] == id), None)


def renommer_module(s: dict, id: str, nom: str, quand: str | None = None) -> bool:
    m = trouver_module(s, id)
    n = _tranche(_trim(nom), 120)
    if m is None or not n:
        return False
    m['nom'] = n
    m['modifie'] = quand or maintenant()
    return True


def supprimer_module(s: dict, id: str) -> bool:
    for k, m in enumerate(s['mes_modules']):
        if m['id'] == id:
            del s['mes_modules'][k]
            return True
    return False


def ajouter_element(s: dict, id: str, e: dict, quand: str | None = None) -> bool:
    m = trouver_module(s, id)
    x = _element_valide(e)
    if m is None or x is None or any(y['genre'] == x['genre'] and y['id'] == x['id'] for y in m['elements']):
        return False
    m['elements'].append(x)
    m['modifie'] = quand or maintenant()
    return True


def retirer_element(s: dict, id: str, e: dict, quand: str | None = None) -> bool:
    m = trouver_module(s, id)
    if m is None:
        return False
    for k, y in enumerate(m['elements']):
        if y['genre'] == e.get('genre') and y['id'] == e.get('id'):
            del m['elements'][k]
            m['modifie'] = quand or maintenant()
            return True
    return False


def deplacer_element(s: dict, id: str, de: int, vers: int, quand: str | None = None) -> bool:
    m = trouver_module(s, id)
    if m is None or de < 0 or de >= len(m['elements']):
        return False
    v = max(0, min(len(m['elements']) - 1, vers))
    if v == de:
        return False
    x = m['elements'].pop(de)
    m['elements'].insert(v, x)
    m['modifie'] = quand or maintenant()
    return True


def nom_libre(s: dict, base: str, numeroter: bool = False) -> str:
    """« Nouveau module 1 », « Copie de X », « Copie de X (2) »…"""
    pris = {m['nom'] for m in s['mes_modules']}
    if numeroter:
        i = 1
        while f'{base} {i}' in pris:
            i += 1
        return f'{base} {i}'
    if base not in pris:
        return base
    i = 2
    while f'{base} ({i})' in pris:
        i += 1
    return f'{base} ({i})'


# ------------------------------------------------------------------ export / import
def _tri(v):
    if isinstance(v, list):
        return [_tri(x) for x in v]
    if isinstance(v, dict):
        return _ordre_js({k: _tri(v[k]) for k in _cles_tri(v)})
    return v


def exporter(s: dict) -> str:
    """Texte JSON stable (clés triées, indentation 1) : le même document donne le même fichier sur le web et au bureau."""
    return json_js(_tri(s), 1) + '\n'


def _refuser_constante(c):
    raise ValueError(c)


def importer(texte: str, application: str = ''):
    try:
        brut = json.loads(texte, parse_constant=_refuser_constante)
    except (ValueError, RecursionError):
        return None
    o = _objet(brut)
    v0 = o is not None and _est_nombre(o.get('version')) and o.get('version') == 0
    if o is None or (o.get('format') != FORMAT and not v0 and 'reglages' not in o):
        return None
    return migrer(brut, application)
