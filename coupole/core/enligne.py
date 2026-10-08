"""Fiche d'informations en ligne sur un objet (facultative, jamais bloquante).

Services (adresses dans ``coupole/donnees/sources.json``, modifiables comme les autres) :
  * SIMBAD (CDS) — ciel profond et étoiles : type, coordonnées, magnitudes, parallaxe, distance mesurée,
    vitesse radiale / redshift, taille angulaire, types spectral et morphologique, identifiants ;
  * CDS Sesame — repli quand SIMBAD ne connaît pas le nom (interroge aussi NED et VizieR) ;
  * JPL Small-Body Database — astéroïdes, comètes, transneptuniens : classe orbitale, éléments,
    diamètre, albédo, période de rotation.

Règles : une requête par objet demandé (jamais en rafale : intervalle minimal par service), délai court,
cache disque daté (``enligne.json`` dans le cache de Coupole, 30 jours ; un « introuvable » est gardé
un jour), et hors ligne un repli propre : la fiche en cache (avec sa date) ou un message clair.
Le travail se fait hors du fil graphique (``coupole.gui.fiche``).
"""
from __future__ import annotations

import datetime as D
import json
import re
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET

from . import config, reseau, simbad, sources

DELAI = 8.0
DUREE_CACHE = D.timedelta(days=30)
DUREE_CACHE_ABSENT = D.timedelta(days=1)
INTERVALLE_MIN = 1.0                 # secondes entre deux requêtes au même service
TAILLE_CACHE = 2000

_verrou = threading.Lock()
_derniers: dict[str, float] = {}
_cache: dict | None = None

# types d'objet SIMBAD (abréviations) des galaxies : lien NED proposé
_GALAXIES = {'G', 'GiG', 'GiP', 'GiC', 'IG', 'PaG', 'Sy1', 'Sy2', 'SyG', 'AGN', 'LIN', 'QSO', 'Bla', 'BLL', 'SBG',
             'H2G', 'EmG', 'rG', 'LSB', 'bCG', 'GrG', 'CGG', 'ClG', 'SCG', 'Sy*', 'AG?', 'G?', 'Q?', 'BiC', 'GtowG',
             'StarburstG', 'Seyfert', 'Seyfert1', 'Seyfert2', 'Galaxy', 'Blazar', 'RadioG', 'LINER', 'HIIG',
             'EmissionG', 'GinPair', 'GinGroup', 'GinCl', 'BrightestCG', 'GroupG', 'ClG', 'PartofG', 'PairG',
             'Compact_Gr_G', 'AGN_Candidate'}


# ---------------------------------------------------------------- cache disque daté
def chemin_cache():
    return config.dossier_cache() / 'enligne.json'


def _charger_cache() -> dict:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(chemin_cache().read_text(encoding='utf-8'))
            if not isinstance(_cache, dict):
                _cache = {}
        except Exception:
            _cache = {}
    return _cache


def _ecrire_cache():
    c = _charger_cache()
    if len(c) > TAILLE_CACHE:                       # on garde les plus récentes
        for k in sorted(c, key=lambda k: c[k].get('date', ''))[:len(c) - TAILLE_CACHE]:
            c.pop(k, None)
    try:
        tmp = chemin_cache().with_suffix('.tmp')
        tmp.write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
        tmp.replace(chemin_cache())
    except OSError:
        pass


def vider_cache():
    global _cache
    with _verrou:
        _cache = {}
        _ecrire_cache()


def _maintenant() -> D.datetime:
    return D.datetime.now(D.timezone.utc).replace(microsecond=0)


def _depuis_cache(cle: str):
    with _verrou:
        e = _charger_cache().get(cle)
    if not e:
        return None, False
    try:
        age = _maintenant() - D.datetime.fromisoformat(e['date'])
    except (KeyError, ValueError):
        return None, False
    frais = age < (DUREE_CACHE if e['resultat'].get('etat') == 'ok' else DUREE_CACHE_ABSENT)
    return e, frais


def _mettre_en_cache(cle: str, resultat: dict):
    with _verrou:
        _charger_cache()[cle] = {'date': resultat['date'], 'resultat': resultat}
        _ecrire_cache()


# ---------------------------------------------------------------- politesse
def _attendre_tour(service: str):
    """Au plus une requête par INTERVALLE_MIN et par service, tous fils confondus."""
    while True:
        with _verrou:
            t = time.monotonic()
            d = _derniers.get(service, -1e9)
            if t - d >= INTERVALLE_MIN:
                _derniers[service] = t
                return
            reste = INTERVALLE_MIN - (t - d)
        time.sleep(reste)


def _lire(service: str, url: str, delai: float, **kw) -> str:
    _attendre_tour(service)
    return reseau.lire_texte(url, delai=delai, **kw)


# ---------------------------------------------------------------- liens
def _lien(cle: str, **valeurs) -> str:
    gabarit = sources.valeur(cle)
    if not gabarit:
        return ''
    try:
        return gabarit.format(**{k: urllib.parse.quote(str(v), safe='') for k, v in valeurs.items()})
    except (KeyError, IndexError, ValueError):
        return ''


def est_galaxie(otype: str, otype_long: str = '', morpho: str = '') -> bool:
    return (otype or '') in _GALAXIES or 'galax' in (otype_long or '').lower() or bool(morpho)


def liens_simbad(f: dict) -> dict:
    out = {'simbad': _lien('simbad.page', id=f['nom'])}
    if f.get('ra') is not None and f.get('dec') is not None:
        dim = max(f.get('dim_x') or 0.0, f.get('dim_y') or 0.0)         # minutes d'arc
        fov = min(10.0, max(0.1, 2.5 * dim / 60.0)) if dim else 0.5
        out['aladin'] = _lien('aladin.page', ra='%.6f' % f['ra'], dec='%+.6f' % f['dec'], fov='%.2f' % fov)
    if est_galaxie(f.get('otype', ''), f.get('type', ''), f.get('morpho', '')):
        out['ned'] = _lien('ned.page', id=f['nom'])
    return {k: v for k, v in out.items() if v}


# ---------------------------------------------------------------- services
def via_simbad(noms: list[str], delai=DELAI) -> dict | None:
    ids = []
    for n in noms:
        for v in [n] + simbad.name_variants(n)[1:4]:
            if v and v not in ids:
                ids.append(v)
    _attendre_tour('simbad')
    f = simbad.fiche(ids[:12], timeout=delai)
    if not f:
        return None
    f['service'] = 'simbad'
    f['liens'] = liens_simbad(f)
    f['galaxie'] = est_galaxie(f.get('otype', ''), f.get('type', ''), f.get('morpho', ''))
    return f


def via_sesame(nom: str, delai=DELAI) -> dict | None:
    base = sources.valeur('resolution.sesame')
    if not base:
        return None
    texte = _lire('sesame', base + '?' + urllib.parse.quote(nom), delai)
    try:
        racine = ET.fromstring(texte.encode('utf-8'))
    except ET.ParseError:
        return None
    for res in racine.iter('Resolver'):
        oname = re.sub(r'\s+', ' ', (res.findtext('oname') or '').strip())
        if not oname:
            continue
        f = {'service': 'sesame', 'nom': oname, 'otype': (res.findtext('otype') or '').strip(), 'type': '',
             'resolveur': (res.get('name') or '').split('=')[-1].strip(), 'ids': [], 'flux': {}}
        for cle, balise in (('ra', 'jradeg'), ('dec', 'jdedeg')):
            try:
                f[cle] = float(res.findtext(balise))
            except (TypeError, ValueError):
                f[cle] = None
        f['ra_s'], f['dec_s'] = '', ''
        pos = (res.findtext('jpos') or '').strip()
        if pos:
            m = re.match(r'^(\S+ \S+ \S+)\s+(\S+ \S+ \S+)$', pos)
            if m:
                f['ra_s'], f['dec_s'] = m.group(1), m.group(2)
        z = res.find('z')
        vel = res.find('Vel')
        f['z'] = _float(z.findtext('v')) if z is not None else None
        f['vr'] = _float(vel.findtext('v')) if vel is not None else None
        f['ids'] = [re.sub(r'\s+', ' ', a.text.strip()) for a in res.findall('alias') if a.text]
        f['liens'] = liens_simbad(f)
        f['galaxie'] = est_galaxie(f['otype'])
        return f
    return None


def _float(t):
    try:
        return float(t)
    except (TypeError, ValueError):
        return None


def designation_sbdb(nom: str) -> str:
    """« (3) Juno » → « 3 » ; « (134340) Pluton » → « 134340 » ; « 14P/Wolf » → « 14P » ; sinon le nom."""
    n = (nom or '').strip()
    m = re.match(r'^\((\d+)\)', n)
    if m:
        return m.group(1)
    m = re.match(r'^(\d+[PDCXI])(?:/|-|$)', n)
    if m:
        return m.group(1)
    return n


def via_sbdb(designation: str, delai=DELAI) -> dict | None:
    base = sources.valeur('resolution.sbdb')
    if not base or not designation:
        return None
    url = base + '?' + urllib.parse.urlencode({'sstr': designation, 'phys-par': 'true', 'full-prec': 'true'})
    texte = _lire('sbdb', url, delai, accepter=(300, 400, 404))
    try:
        d = json.loads(texte)
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    if d.get('list'):                               # plusieurs objets : on n'en choisit aucun au hasard
        return {'service': 'sbdb', 'ambigu': True, 'nom': designation,
                'candidats': ['%s %s' % (c.get('pdes', ''), c.get('name', '')) for c in d['list']][:15],
                'liens': {}}
    o = d.get('object')
    if not o:
        return None
    orb = d.get('orbit') or {}
    elements = {e['name']: (_float(e.get('value')), e.get('units') or '') for e in orb.get('elements') or []
                if 'name' in e}
    phys = {}
    for p in d.get('phys_par') or []:
        v = _float(p.get('value'))
        phys[p.get('name', '')] = (v if v is not None else p.get('value'), p.get('units') or '')
    cls = o.get('orbit_class') or {}
    f = {'service': 'sbdb', 'nom': o.get('fullname') or o.get('shortname') or designation,
         'designation': o.get('des') or designation, 'genre': o.get('kind', ''),
         'classe': cls.get('name', ''), 'classe_code': cls.get('code', ''), 'neo': bool(o.get('neo')),
         'pha': bool(o.get('pha')), 'elements': elements, 'phys': phys, 'epoque_jd': _float(orb.get('epoch')),
         'liens': {}}
    lien = _lien('sbdb.page', id=o.get('spkid') or o.get('des') or designation)
    if lien:
        f['liens']['sbdb'] = lien
    return f


def ressemble_petit_corps(nom: str) -> bool:
    n = (nom or '').strip()
    return bool(re.search(r'^\(\d+\)|\d{4} ?[A-Z]{2}\d*|^\d+ |^[CPDXAI][/ ]\d{4}|^\d+[PD]\b', n))


# ---------------------------------------------------------------- point d'entrée
PETITS_CORPS = {'ast', 'com', 'tno'}


def fiche_objet(nom: str, cat: str | None = None, sbdb: str | None = None, autres: tuple = (),
                rafraichir: bool = False, delai: float = DELAI, en_ligne: bool | None = None) -> dict:
    """Fiche de l'objet, depuis le cache si elle est fraîche, sinon en ligne.

    Rend toujours un dict : ``etat`` = 'ok' | 'introuvable' | 'hors_ligne' | 'sans_fiche' | 'desactive'
    (services en ligne coupés dans les réglages, rien en cache),
    ``fiche`` (dict ou None), ``date`` (ISO, UTC), ``cache`` (bool), ``perime`` (cache trop vieux mais
    seul disponible), ``erreur`` (texte technique), ``raison`` (clé de traduction pour 'sans_fiche').
    """
    nom = (nom or '').strip()
    base = {'demande': nom, 'fiche': None, 'cache': False, 'perime': False, 'erreur': '', 'raison': '',
            'date': _maintenant().isoformat()}
    if not nom:
        return dict(base, etat='sans_fiche', raison='fiche_vide')
    if cat == 'pla':
        return dict(base, etat='sans_fiche', raison='fiche_planete')
    if cat == 'neocp':
        return dict(base, etat='sans_fiche', raison='fiche_neocp')
    petit = cat in PETITS_CORPS or bool(sbdb) or (cat is None and ressemble_petit_corps(nom))
    cle = '%s|%s|%s' % ('sbdb' if petit else 'ciel', (sbdb or nom).lower(), cat or '')
    e, frais = _depuis_cache(cle)
    if e and frais and not rafraichir:
        return dict(e['resultat'], cache=True)
    if not _autorise(en_ligne):
        return dict(e['resultat'], cache=True, perime=not frais) if e else dict(base, etat='desactive')
    try:
        f = None
        if petit:
            f = via_sbdb(sbdb or designation_sbdb(nom), delai)
        else:
            f = via_simbad([nom] + [a for a in autres if a and a != nom], delai)
            if f is None:
                f = via_sesame(nom, delai)
            if f is None and cat is None:
                f = via_sbdb(designation_sbdb(nom), delai)
    except reseau.ServiceInjoignable as ex:
        if e:                                       # hors ligne : la dernière fiche connue, avec sa date
            return dict(e['resultat'], cache=True, perime=True, erreur=str(ex))
        return dict(base, etat='hors_ligne', erreur=str(ex))
    r = dict(base, etat='ok' if f else 'introuvable', fiche=f)
    _mettre_en_cache(cle, r)
    return r


def _autorise(en_ligne: bool | None) -> bool:
    if en_ligne is not None:
        return bool(en_ligne)
    return bool(config.reglages()['services_en_ligne'])


def redshift(nom: str, delai: float = DELAI, en_ligne: bool | None = None) -> dict:
    """Redshift d'un objet nommé (pour le module Cosmologie).

    Rend {'etat': 'ok'|'introuvable'|'hors_ligne'|'ambigu'|'desactive', 'z', 'nom', 'type', 'candidats', 'erreur'}.
    Résolution tolérante (variantes, joker) ; plusieurs candidats → l'utilisateur choisit.
    """
    nom = (nom or '').strip()
    out = {'etat': 'introuvable', 'z': None, 'nom': '', 'type': '', 'candidats': [], 'erreur': '', 'demande': nom}
    if not nom:
        return out
    cle = 'z|' + simbad.flatten(nom)
    e, frais = _depuis_cache(cle)
    if e and frais:
        return dict(e['resultat'], cache=True)
    if not _autorise(en_ligne):
        return dict(e['resultat'], cache=True, perime=True) if e else dict(out, etat='desactive')
    try:
        _attendre_tour('simbad')
        objets, _ = simbad.resolve(nom, timeout=delai)
    except reseau.ServiceInjoignable as ex:
        if e:
            return dict(e['resultat'], cache=True, perime=True, erreur=str(ex))
        return dict(out, etat='hors_ligne', erreur=str(ex))
    if len(objets) == 1:
        o = objets[0]
        out.update(etat='ok', z=o.redshift, nom=re.sub(r'\s+', ' ', o.name), type=o.otype)
    elif objets:
        out.update(etat='ambigu', candidats=[{'nom': re.sub(r'\s+', ' ', o.name), 'type': o.otype, 'z': o.redshift} for o in objets])
    out['date'] = _maintenant().isoformat()
    _mettre_en_cache(cle, out)
    return out
