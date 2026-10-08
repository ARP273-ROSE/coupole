"""Inventaire de la banque « OHP student observations » par le service TAP public.

Service : http://tap-ufe.obspm.fr/tap (PADC, Observatoire de Paris), table
ivoa.obscore, requête ADQL synchrone.  Le résultat est mis en cache localement
(JSON compressé) ; un instantané daté est livré avec l'application pour
travailler hors ligne et pour les tests.

Chaque image est enrichie (comme cibles.charger) : nuit (date du soir), tel
(T120 / IRIS), go (taille annoncée en Go), objet, cat, sbdb, rem, diurne,
doublon (copie probable d'une autre ligne), date_partagee.
"""
from __future__ import annotations

import collections as C
import csv
import datetime as D
import gzip
import io
import json
import re
from pathlib import Path

from ...core import astro, config, reseau
from . import cibles

COLONNES = ['access_url', 'access_estsize', 'target_name', 'filter_name', 't_min', 't_exptime',
            'instrument_name', 's_ra', 's_dec', 's_fov', 's_region', 's_xel1', 's_xel2', 's_pixel_scale']
NUMERIQUES = {'access_estsize', 't_min', 't_exptime', 's_ra', 's_dec', 's_fov', 's_xel1', 's_xel2', 's_pixel_scale'}
INSTRUMENTS = {'OHP T120': 'T120', 'ACP->NTM': 'IRIS', 'IRIS OHP': 'IRIS'}
INSTANTANE = Path(__file__).resolve().parent / 'data' / 'inventaire.json.gz'


def adql() -> str:
    from ...core import sources
    return ("SELECT * FROM ivoa.obscore WHERE obs_collection = '%s'"
            % sources.valeur('ohp.collection').replace("'", "''"))


def _convertir(ligne: dict) -> dict:
    x = {}
    for c in COLONNES:
        v = ligne.get(c)
        if c in NUMERIQUES:
            try:
                v = float(v) if v not in (None, '') else 0.0
            except (TypeError, ValueError):
                v = 0.0
        else:
            v = '' if v is None else str(v)
        x[c] = v
    return x


def interroger_tap(service: str | None = None) -> list[dict]:
    """Une seule requête ADQL : toute la collection (≈ 8 000 lignes, quelques Mo).

    SELECT * : une colonne ObsCore ajoutée par la base est ignorée, une colonne retirée prend une valeur par
    défaut (_convertir) ; rien ne casse.
    """
    from ...core import sources
    brut = reseau.tap_sync(service or sources.valeur('ohp.tap'), adql())
    texte = brut.decode('utf-8', 'replace')
    if texte.lstrip().startswith('<'):
        raise IOError('TAP error: ' + re.sub(r'<[^>]+>', ' ', texte)[:300])
    return [_convertir(r) for r in csv.DictReader(io.StringIO(texte))]


def chemin_cache() -> Path:
    return config.dossier_cache() / 'ohp_inventaire.json.gz'


def ecrire(chemin: Path, lignes: list[dict], source: str):
    meta = {'date': D.datetime.now(D.timezone.utc).isoformat(timespec='seconds'), 'source': source,
            'n': len(lignes), 'colonnes': COLONNES}
    tmp = Path(str(chemin) + '.tmp')
    with gzip.open(tmp, 'wt', encoding='utf-8') as f:
        json.dump({'meta': meta, 'lignes': lignes}, f, ensure_ascii=False)
    tmp.replace(chemin)
    return meta


def lire(chemin: Path):
    with gzip.open(chemin, 'rt', encoding='utf-8') as f:
        d = json.load(f)
    return [_convertir(x) for x in d['lignes'] if x.get('access_url')], d['meta']


# ======================================================================== nouveautés
def chemin_historique() -> Path:
    return config.dossier_config() / 'ohp_historique.json'


def historique() -> dict:
    try:
        return json.loads(chemin_historique().read_text(encoding='utf-8'))
    except Exception:
        return {}


def noter_vus(lignes: list[dict], date: str) -> dict:
    """Mémorise la première apparition de chaque image et de chaque nom ; renvoie les nouveautés."""
    h = historique()
    premiere = not h
    urls = h.setdefault('urls', {})
    noms = h.setdefault('noms', {})
    depuis = h.get('dernier_rafraichissement', '')
    nouv_i, nouv_n = [], []
    for x in lignes:
        if x['access_url'] not in urls:
            urls[x['access_url']] = date
            if not premiere:
                nouv_i.append(x['access_url'])
        if x['target_name'] not in noms:
            noms[x['target_name']] = date
            if not premiere:
                nouv_n.append(x['target_name'])
    h['dernier_rafraichissement'] = date
    h.setdefault('reference', date)
    tmp = chemin_historique().with_suffix('.tmp')
    tmp.write_text(json.dumps(h, ensure_ascii=False), encoding='utf-8')
    tmp.replace(chemin_historique())
    return {'images': nouv_i, 'noms': sorted(set(nouv_n)), 'depuis': depuis, 'premiere': premiere}


def rafraichir(service: str | None = None):
    """Réinterroge le TAP ; renvoie (lignes, meta, nouveautés)."""
    from ...core import sources
    service = service or sources.valeur('ohp.tap')
    lignes = interroger_tap(service)
    if not lignes:
        raise IOError('empty TAP answer')
    if not historique():                       # première fois : l'état connu sert de référence
        try:
            noter_vus(charger_brut()[0], (charger_brut()[1].get('date') or '')[:10])
        except Exception:
            pass
    meta = ecrire(chemin_cache(), lignes, service)
    nouv = noter_vus(lignes, meta['date'][:10])
    return lignes, meta, nouv


def charger_brut(rafraichir_: bool = False):
    """(lignes, meta) : cache local s'il existe, sinon instantané livré ; rafraîchit à la demande."""
    if rafraichir_:
        return rafraichir()[:2]
    for p in (chemin_cache(), INSTANTANE):
        if p.exists():
            try:
                return lire(p)
            except Exception:
                continue
    return rafraichir()[:2]


# ======================================================================== enrichissement
def cle_doublon(x):
    """Identité d'une pose : date, filtre, pose, taille, nom de fichier à la ponctuation près."""
    fic = re.sub(r'[^a-z0-9]', '', x['access_url'].rsplit('/', 1)[1].lower())
    return (x['t_min'], x['filter_name'], x['t_exptime'], x['access_estsize'], fic)


def instrument(nom: str) -> str:
    """Nom d'instrument de la base → étiquette courte (inconnu : nom nettoyé, jamais d'erreur)."""
    if nom in INSTRUMENTS:
        return INSTRUMENTS[nom]
    n = re.sub(r'[^A-Za-z0-9]+', '', nom or '')
    return n[:16] or 'inconnu'


def enrichir(lignes: list[dict]) -> list[dict]:
    from ...core.astro import sep_deg
    d = [dict(x) for x in lignes]
    classeur = cibles.Classeur()
    h = historique()
    vus = h.get('urls', {})
    ref = h.get('reference', '')
    for x in d:
        x['nuit'] = astro.nuit(x['t_min'])
        x['tel'] = instrument(x['instrument_name'])
        x['go'] = x['access_estsize'] * 1024 / 1e9           # access_estsize en Kio
        x['objet'], x['cat'], x['sbdb'], x['rem'], x['classement'] = classeur.classer(x['target_name'])
        x['a_verifier'] = x['classement'] not in cibles.ORIGINES_SURES
        x['diurne'] = 5 <= astro.utc(x['t_min']).hour <= 17
        x['vu_le'] = vus.get(x['access_url'], '')
        x['nouveau'] = bool(ref and x['vu_le'] and x['vu_le'] > ref)
    # regroupement par position : un nom inconnu pointé sur un objet fixe connu en devient l'alias
    centres = C.defaultdict(list)
    for x in d:
        if x['cat'] in cibles.FIXES and not x['a_verifier']:
            centres[x['objet']].append((x['s_ra'], x['s_dec']))
    medianes = {}
    for o, pts in centres.items():
        import numpy as np
        medianes[o] = (float(np.median([p[0] for p in pts])), float(np.median([p[1] for p in pts])))
    for x in d:
        if x['classement'] != 'inconnu' or not medianes:
            continue
        lim = max(0.1, x['s_fov'] / 2 if x['s_fov'] else 0.1)
        o, dist = min(((o, sep_deg(x['s_ra'], x['s_dec'], c[0], c[1])) for o, c in medianes.items()),
                      key=lambda t: t[1])
        if dist <= lim:
            ex = next(y for y in d if y['objet'] == o)
            x['objet'], x['cat'], x['sbdb'], x['rem'] = o, ex['cat'], None, ''
            x['classement'] = 'position'
    vus_c = set()
    for x in sorted(d, key=lambda x: x['access_url']):
        x['doublon'] = cle_doublon(x) in vus_c
        x['raison_doublon'] = 'meme_fichier' if x['doublon'] else ''
        vus_c.add(cle_doublon(x))
    # copies datées en plein jour (dossiers t120/ et t152/) d'images bien datées
    bien = {(x['objet'], x['access_url'].rsplit('/', 1)[1]) for x in d if not x['diurne']}
    for x in d:
        if x['diurne'] and not x['doublon'] and (x['objet'], x['access_url'].rsplit('/', 1)[1]) in bien:
            x['doublon'] = True
            x['raison_doublon'] = 'copie_diurne'
    tm = C.Counter((x['tel'], x['t_min']) for x in d if not x['doublon'])
    for x in d:
        x['date_partagee'] = (not x['doublon']) and tm[(x['tel'], x['t_min'])] > 1
    return d


class Inventaire:
    """Inventaire enrichi + métadonnées (date, source)."""

    def __init__(self, lignes: list[dict], meta: dict, nouveautes: dict | None = None):
        self.meta = meta
        self.nouveautes = nouveautes or {}
        self.images = enrichir(lignes)

    @classmethod
    def charger(cls, rafraichir_: bool = False):
        if rafraichir_:
            return cls(*rafraichir())
        return cls(*charger_brut())

    def objets(self) -> list[dict]:
        """Catalogue des objets : une entrée par objet canonique."""
        ordre = list(cibles.CATEGORIES)
        par = C.OrderedDict()
        for x in sorted(self.images, key=lambda x: (ordre.index(x['cat']) if x['cat'] in ordre else 99, x['objet'])):
            o = par.setdefault(x['objet'], {'objet': x['objet'], 'cat': x['cat'], 'rem': x['rem'], 'noms': set(),
                                            'images': 0, 'doublons': 0, 'octets': 0, 'nuits': set(), 'tel': set(),
                                            'filtres': set(), 'a_verifier': False, 'nouveau': False,
                                            'vu_le': ''})
            o['noms'].add(x['target_name'])
            o['a_verifier'] |= x['a_verifier']
            o['nouveau'] |= x['nouveau']
            if x['nouveau']:
                o['vu_le'] = max(o['vu_le'], x['vu_le'])
            if x['doublon']:
                o['doublons'] += 1
                continue
            o['images'] += 1
            o['octets'] += x['access_estsize'] * 1024
            o['nuits'].add(str(x['nuit']))
            o['tel'].add(x['tel'])
            o['filtres'].add(x['filter_name'])
        return list(par.values())
