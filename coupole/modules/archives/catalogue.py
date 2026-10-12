"""Catalogue des cibles de chaque archive, sans critère de recherche : cibles les plus observées, type d'objet,
programmes célèbres.  Pages de 100 lignes ; cache daté (30 jours) ; jamais dans le fil graphique.

Requêtes agrégées (``GROUP BY target_name``) mesurées le 12 octobre 2026 :

* MAST, Hubble : sur toute la table, la passerelle répond 504 après 65 s ; restreinte aux mosaïques multi-visites
  (``provenance_name = 'HAP-MVM'``, qui regroupent toutes les poses publiques ACS et WFC3 d'une cellule du ciel) :
  12 à 17 s → c'est elle qu'on interroge (WFPC2 n'y figure pas : le dire) ;
* MAST, JWST (produits ``_i2d``) : 34 s ;
* ESO (``ivoa.ObsCore``, images) : 1,7 s ;
* OPUS (Voyager, Cassini) : ``meta/mults/target.json`` (comptes par cible, < 1 s) ;
* PDS Imaging Atlas (JunoCam) : facettes Solr sur ``TARGET_NAME`` (< 1 s) ;
* IRSA (Spitzer SEIP, AllWISE, 2MASS) : relevés du ciel entier ou mosaïques sans nom de cible utile → pas de
  liste (on cherche par position) ; NOIRLab, KOA, SDSS : idem (expliqué dans l'interface) ; Gemini (compte
  exigé), SMOKA (formulaire web) : non pris en charge.
"""
from __future__ import annotations

import datetime as D
import json
import os
import urllib.parse

from ...core import config, sources
from .services.base import lire_json, lire_url, lire_tableau, nombre

PAGE = 100
VALIDITE_JOURS = 30

# catalogue : (archive, mission, requête) ; requête = ('tap', service, adql) | ('opus', instrument) | ('pds',)
CATALOGUES = {
    'hst': ('mast', 'HST', ('tap', 'archives.mast.tap',
            "SELECT TOP 3000 target_name, MIN(target_classification) AS type, COUNT(*) AS n, AVG(s_ra) AS ra, "
            "AVG(s_dec) AS dec, SUM(t_exptime) AS t FROM dbo.obspointing WHERE obs_collection='HST' AND "
            "calib_level=3 AND dataproduct_type='image' AND provenance_name='HAP-MVM' AND intenttype='science' "
            "AND target_name <> 'ANY' GROUP BY target_name ORDER BY n DESC")),
    'jwst': ('mast', 'JWST', ('tap', 'archives.mast.tap',
             "SELECT TOP 3000 target_name, MIN(target_classification) AS type, COUNT(*) AS n, AVG(s_ra) AS ra, "
             "AVG(s_dec) AS dec, SUM(t_exptime) AS t FROM dbo.obspointing WHERE obs_collection='JWST' AND "
             "calib_level=3 AND dataproduct_type='image' AND intenttype='science' AND dataurl LIKE '%_i2d.fits' "
             "AND target_name <> 'UNKNOWN' GROUP BY target_name ORDER BY n DESC")),
    'eso': ('eso', 'ESO', ('tap', 'archives.eso.tap',
            "SELECT TOP 3000 target_name, MIN(instrument_name) AS type, COUNT(*) AS n, AVG(s_ra) AS ra, "
            "AVG(s_dec) AS dec, SUM(t_exptime) AS t FROM ivoa.ObsCore WHERE dataproduct_type='image' "
            "GROUP BY target_name ORDER BY n DESC")),
    'voyager': ('opus', 'Voyager', ('opus', 'Voyager ISS')),
    'cassini': ('opus', 'Cassini', ('opus', 'Cassini ISS')),
    'juno': ('pds', 'Juno', ('pds',)),
}
SANS_LISTE = ('irsa', 'noirlab', 'koa', 'sdss', 'goa', 'smoka')

# type d'objet : mots de la classification des propositions (MAST) → catégorie
CATEGORIES = (('exoplanet', 'etoile'), ('solar system', 'systeme_solaire'), ('planet', 'systeme_solaire'), ('comet', 'systeme_solaire'),
              ('cluster of galaxies', 'amas_galaxies'), ('clusters of ga', 'amas_galaxies'),
              ('galax', 'galaxie'), ('quasar', 'galaxie'), ('agn', 'galaxie'), ('globular', 'amas_stellaire'),
              ('stellar cluster', 'amas_stellaire'), ('open cluster', 'amas_stellaire'), ('nebula', 'nebuleuse'),
              ('ism', 'nebuleuse'), ('h ii', 'nebuleuse'), ('hii', 'nebuleuse'), ('star forming', 'nebuleuse'),
              ('supernova remnant', 'nebuleuse'), ('planetary nebula', 'nebuleuse'), ('high latitude field', 'champ'),
              ('deep field', 'champ'), ('parallel field', 'champ'), ('unidentified', 'champ'), ('star', 'etoile'),
              ('dwarf', 'etoile'), ('supernova', 'etoile'), ('nova', 'etoile'))


def categorie(classification: str) -> str:
    c = (classification or '').lower()
    if not c:
        return 'autre'
    if 'calibration' in c:
        return 'etalonnage'
    if 'planetary nebula' in c:
        return 'nebuleuse'
    for mot, cat in CATEGORIES:
        if mot in c:
            return cat
    return 'autre'


def chemin_cache(cle: str):
    return config.dossier_cache() / 'archives_catalogue' / ('%s.json' % cle)


def lire_cache(cle: str) -> dict | None:
    p = chemin_cache(cle)
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) and 'lignes' in d else None


def frais(d: dict) -> bool:
    try:
        t = D.datetime.fromisoformat(d['date'])
    except (KeyError, ValueError, TypeError):
        return False
    return (D.datetime.now(D.timezone.utc) - t).days < VALIDITE_JOURS


def _tap(cle_service: str, adql: str) -> list[dict]:
    corps = urllib.parse.urlencode({'REQUEST': 'doQuery', 'LANG': 'ADQL', 'FORMAT': 'csv', 'RESPONSEFORMAT': 'csv',
                                    'QUERY': adql}).encode()
    service = 'mast' if 'mast' in cle_service else 'eso'
    return lire_tableau(lire_url(sources.valeur(cle_service).rstrip('/') + '/sync', data=corps, delai=120,
                                 service=service))


def interroger(cle: str) -> list[dict]:
    """Lignes du catalogue : {'cible', 'n', 'ra', 'dec', 'exposition', 'type', 'categorie', 'recherche'}."""
    from .corps import reconnaitre
    archive, mission, req = CATALOGUES[cle]
    out = []
    if req[0] == 'tap':
        for l in _tap(req[1], req[2]):
            cible = (l.get('target_name') or '').strip()
            if not cible:
                continue
            typ = (l.get('type') or '').strip()
            cat = categorie(typ) if archive == 'mast' else 'autre'
            if cat == 'etalonnage':
                continue
            ra, dec = nombre(l.get('ra')), nombre(l.get('dec'))
            corps = reconnaitre(cible.split('-')[0].split('+')[0]) if (archive == 'mast' and cat in ('systeme_solaire', 'autre')) else None
            if corps is not None:
                cat, recherche = 'systeme_solaire', corps['en']
            elif ra is not None and dec is not None:
                recherche = '%.5f %+.5f' % (ra, dec)
            else:
                recherche = cible
            out.append({'cible': cible, 'n': int(nombre(l.get('n'), 0)), 'ra': ra, 'dec': dec,
                        'exposition': nombre(l.get('t')), 'type': typ, 'categorie': cat, 'recherche': recherche,
                        'archive': archive, 'mission': mission})
    elif req[0] == 'opus':
        url = sources.valeur('archives.opus.api').rstrip('/') + '/meta/mults/target.json?' + urllib.parse.urlencode(
            {'instrument': req[1]})
        rep = lire_json(url, service='opus')
        for cible, n in sorted((rep.get('mults') or {}).items(), key=lambda kv: -kv[1]):
            if cible in ('Dark', 'Dark Sky', 'Sky', 'Calibration Lamps', 'Plaque', 'Star', 'System', 'None'):
                continue
            out.append({'cible': cible, 'n': int(n), 'ra': None, 'dec': None, 'exposition': None, 'type': '',
                        'categorie': 'systeme_solaire', 'recherche': cible, 'archive': archive, 'mission': mission})
    else:
        p = [('q', '*:*'), ('rows', '0'), ('wt', 'json'), ('facet', 'true'), ('facet.field', 'TARGET_NAME'),
             ('facet.limit', '200'), ('facet.mincount', '1'), ('fq', 'ATLAS_MISSION_NAME:juno'),
             ('fq', 'ATLAS_INSTRUMENT_NAME:jnc')]
        rep = lire_json(sources.valeur('archives.pds.atlas') + '?' + urllib.parse.urlencode(p), service='pds')
        f = (((rep.get('facet_counts') or {}).get('facet_fields') or {}).get('TARGET_NAME')) or []
        for cible, n in zip(f[0::2], f[1::2]):
            if cible in ('space',) or not n:
                continue
            out.append({'cible': str(cible).title(), 'n': int(n), 'ra': None, 'dec': None, 'exposition': None,
                        'type': '', 'categorie': 'systeme_solaire', 'recherche': str(cible).title(),
                        'archive': archive, 'mission': mission})
    return out


def charger(cle: str, rafraichir: bool = False) -> dict:
    """{'lignes', 'date', 'cache' (bool), 'erreur'} ; cache frais rendu sans requête ; en cas d'échec réseau, le
    cache périmé est rendu (avec l'erreur)."""
    c = lire_cache(cle)
    if c and frais(c) and not rafraichir:
        return dict(c, cache=True, erreur='')
    try:
        lignes = interroger(cle)
    except Exception as e:
        if c:
            return dict(c, cache=True, erreur='%s: %s' % (type(e).__name__, e))
        return {'lignes': [], 'date': '', 'cache': False, 'erreur': '%s: %s' % (type(e).__name__, e)}
    d = {'lignes': lignes, 'date': D.datetime.now(D.timezone.utc).isoformat(timespec='seconds')}
    p = chemin_cache(cle)
    try:
        os.makedirs(p.parent, exist_ok=True)
        config.ecrire_atomique(p, json.dumps(d, ensure_ascii=False))
    except OSError:
        pass
    return dict(d, cache=False, erreur='')


def filtrer(lignes: list[dict], texte: str = '', categorie_: str = '') -> list[dict]:
    from .corps import normaliser
    t = normaliser(texte)
    return [l for l in lignes if (not t or t in normaliser(l['cible'])) and (not categorie_ or l['categorie'] == categorie_)]


def page(lignes: list[dict], numero: int, taille: int = PAGE) -> list[dict]:
    """Page `numero` (0 = première)."""
    return lignes[numero * taille:(numero + 1) * taille]


def nombre_pages(lignes: list[dict], taille: int = PAGE) -> int:
    return max(1, (len(lignes) + taille - 1) // taille)
