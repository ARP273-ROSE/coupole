"""Adresses des services (TAP, portail, résolveurs, mise à jour...) : jamais en dur dans le code.

Trois couches, de la plus faible à la plus forte :
  1. ``coupole/donnees/sources.json``, livré avec l'application (et remplacé par
     ses mises à jour) ;
  2. le même fichier publié dans le dépôt GitHub, récupéré au démarrage en
     arrière-plan et gardé en cache s'il passe le contrôle de forme et s'il est
     plus récent (champ ``version``) ; injoignable ou mal formé : ignoré sans
     bruit, la valeur locale reste ;
  3. les valeurs forcées par l'utilisateur (Préférences ou ``coupole sources``),
     jamais écrasées par 1 ou 2.

Contrôle du fichier distant : pas de signature cryptographique (une clé
embarquée dans une application libre n'est pas un secret) ; à la place, un
contrôle de forme strict (format, types, clés connues) et une **liste blanche
de domaines** : une adresse distante ne peut viser que les domaines déjà
utilisés (Observatoire de Paris, CDS, JPL, NED, GitHub, point de collecte).  Un
fichier distant compromis ne peut donc pas rediriger les téléchargements
ailleurs.  Une valeur forcée par l'utilisateur, elle, est libre.
"""
from __future__ import annotations

import json
import logging
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from . import config

log = logging.getLogger(__name__)

FICHIER_DEFAUT = Path(__file__).resolve().parent.parent / 'donnees' / 'sources.json'
FORMAT = 1
DOMAINES_AUTORISES = ('obspm.fr', 'unistra.fr', 'u-strasbg.fr', 'nasa.gov', 'caltech.edu', 'github.com',
                      'githubusercontent.com', 'giff.re', 'openstreetmap.org')
CLES_TEXTE = {'ohp.collection', 'maj.depot', 'ohp.telechargement.de', 'ohp.telechargement.vers'}

_verrou = threading.Lock()
_defaut: dict | None = None


def _lire(p: Path) -> dict:
    return json.loads(p.read_text(encoding='utf-8'))


def defauts() -> dict:
    global _defaut
    if _defaut is None:
        _defaut = _lire(FICHIER_DEFAUT)
    return _defaut


def chemin_cache_distant() -> Path:
    return config.dossier_config() / 'sources_distant.json'


def _domaine_ok(url: str) -> bool:
    try:
        u = urlparse(url)
    except ValueError:
        return False
    h = (u.hostname or '').lower()
    return u.scheme in ('http', 'https') and any(h == d or h.endswith('.' + d) for d in DOMAINES_AUTORISES)


def valider(doc) -> list[str]:
    """Liste des défauts de forme (vide = acceptable)."""
    pb = []
    if not isinstance(doc, dict):
        return ['not an object']
    if doc.get('format') != FORMAT:
        pb.append('format %r' % doc.get('format'))
    if not isinstance(doc.get('version'), int):
        pb.append('version not an integer')
    vals = doc.get('valeurs')
    if not isinstance(vals, dict):
        pb.append('valeurs missing')
        vals = {}
    connues = set(defauts()['valeurs'])
    for k, v in vals.items():
        if k not in connues:
            pb.append('unknown key %s' % k)
        elif not isinstance(v, str) or len(v) > 500:
            pb.append('bad value for %s' % k)
        elif k == 'ohp.telechargement.vers' and v and not _domaine_ok(v):
            pb.append('domain not allowed for %s' % k)
        elif k not in CLES_TEXTE and v and not _domaine_ok(v):
            pb.append('domain not allowed for %s' % k)
    al = doc.get('alias_ohp', {})
    if not isinstance(al, dict):
        pb.append('alias_ohp not an object')
    else:
        for nom, e in al.items():
            if not (isinstance(nom, str) and isinstance(e, dict) and isinstance(e.get('objet'), str)
                    and isinstance(e.get('cat'), str)):
                pb.append('bad alias %r' % nom)
                break
    return pb


def distant() -> dict | None:
    """Fichier distant en cache, s'il est valide et plus récent que le fichier livré."""
    p = chemin_cache_distant()
    try:
        doc = _lire(p)
    except Exception:
        return None
    if valider(doc) or doc['version'] <= defauts()['version']:
        return None
    return doc


def forcees() -> dict:
    return dict(config.reglages().get('sources_forcees') or {})


def valeur(cle: str) -> str:
    f = forcees()
    if cle in f:
        return f[cle]
    d = distant()
    if d and cle in d['valeurs']:
        return d['valeurs'][cle]
    return defauts()['valeurs'].get(cle, '')


def toutes() -> dict:
    """{clé: (valeur effective, origine 'defaut'|'distant'|'utilisateur')}."""
    d = distant()
    out = {}
    for k, v in defauts()['valeurs'].items():
        if k in forcees():
            out[k] = (forcees()[k], 'utilisateur')
        elif d and k in d['valeurs']:
            out[k] = (d['valeurs'][k], 'distant')
        else:
            out[k] = (v, 'defaut')
    return out


def forcer(cle: str, val: str | None):
    """Force une valeur (None : revient à la valeur livrée/distante)."""
    if cle not in defauts()['valeurs']:
        raise KeyError(cle)
    r = config.reglages()
    f = forcees()
    if val is None:
        f.pop(cle, None)
    else:
        f[cle] = val
    r['sources_forcees'] = f


def tout_reinitialiser():
    config.reglages()['sources_forcees'] = {}


def alias_distants() -> dict:
    d = distant()
    return dict(d.get('alias_ohp', {})) if d else {}


def rafraichir_distant(delai=8) -> bool:
    """Récupère le fichier distant ; True s'il a été accepté.  Ne lève jamais."""
    url = valeur('sources.distant')
    if not url or not _domaine_ok(url):
        return False
    try:
        from .. import __version__
        req = urllib.request.Request(url, headers={'User-Agent': 'Coupole/%s' % __version__})
        with urllib.request.urlopen(req, timeout=delai) as r:
            doc = json.loads(r.read(200_000).decode('utf-8'))
    except Exception as e:
        log.info('remote sources unavailable: %s', e)
        return False
    pb = valider(doc)
    if pb:
        log.warning('remote sources rejected: %s', '; '.join(pb[:5]))
        return False
    if doc['version'] <= defauts()['version']:
        return False
    with _verrou:
        chemin_cache_distant().write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
    return True


def rafraichir_en_fond():
    threading.Thread(target=rafraichir_distant, name='sources', daemon=True).start()


def tester(cle: str, delai=10) -> tuple[bool, str]:
    """Test de connexion d'une adresse (TAP : une requête COUNT minuscule)."""
    url = valeur(cle)
    if not url:
        return False, 'empty'
    try:
        from . import reseau
        if cle == 'ohp.tap':
            rep = reseau.tap_sync(url, 'SELECT TOP 1 obs_id FROM ivoa.obscore', delai=delai)
            return (b'obs_id' in rep[:200]), rep[:80].decode('utf-8', 'replace')
        with reseau.requete(url, delai=delai) as r:
            return 200 <= r.status < 400, 'HTTP %d' % r.status
    except Exception as e:
        return False, '%s: %s' % (type(e).__name__, e)


def reecrire_url(url: str) -> str:
    """Applique la réécriture « ohp.telechargement.de → vers » (serveur déplacé)."""
    de, vers = valeur('ohp.telechargement.de'), valeur('ohp.telechargement.vers')
    if de and vers and url.startswith(de):
        return vers + url[len(de):]
    return url
