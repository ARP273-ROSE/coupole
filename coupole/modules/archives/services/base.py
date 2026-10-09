"""Socle commun des archives : requête, observation, lecture des réponses (VOTable, CSV, JSON), géométrie du ciel.

Une *observation* est un dictionnaire (léger : 50 000 lignes tiennent en mémoire et se trient vite) :

    id          identifiant unique « archive:identifiant » (clé de la base d'état et de la possession)
    archive     'mast' | 'eso' | 'irsa' | 'noirlab' | 'koa' | 'sdss' | 'opus' | 'pds'
    mission     collection ou mission (JWST, HST, GALEX, ESO, Spitzer, WISE, 2MASS, DECam, Keck, SDSS, Voyager…)
    instrument, filtre, lambda_nm (longueur d'onde centrale, nm, ou None)
    debut       date UTC du début de l'observation (ISO) ou ''
    publique    date de fin de la période réservée (ISO) ou '' ; public : bool (déjà publique)
    calib       niveau de calibration ObsCore (0 brut … 3 produit final) ; final : bool (produit final reconnu)
    cible, ra, dec (degrés ou None), distance (degrés au centre de la recherche ou None)
    url         adresse du fichier ; fichier : nom du fichier ; format : 'fits' | 'fits.gz' | 'fits.fz' | 'fits.bz2'
                | 'pds3' | 'vicar' | 'pds4' ; etiquette : adresse du label PDS détaché ('' sinon)
    taille      octets annoncés par l'archive (None : inconnu, mesuré avant téléchargement)
    apercu      adresse d'une vignette ('' sinon) ; page : page de l'archive
    programme, pi, titre, credit (crédit à afficher), conditions (clé de texte des conditions d'usage)

Aucune requête n'est faite à l'import ; chaque archive est une classe `Archive` (voir `catalogue.py`).
"""
from __future__ import annotations

import csv
import datetime as D
import io
import json
import math
import re
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from ....core import reseau, sources

DELAI = 90.0                  # secondes : une requête TAP lente (MAST) répond en quelques secondes
MAX_LIGNES = 20000            # par archive et par recherche ; au-delà, résultat tronqué (signalé)
INTERVALLE_MIN = 1.0          # secondes entre deux requêtes de recherche au même service (courtoisie)
TAILLE_REPONSE_MAX = 200 * 2**20


class CompteRequis(Exception):
    """L'archive refuse l'accès anonyme (un compte gratuit est nécessaire, même pour les données publiques)."""


class NonPrisEnCharge(Exception):
    """Archive sans interface de programmation utilisable (formulaire web seulement)."""


@dataclass
class Requete:
    """Ce que l'on cherche.  `ra`/`dec` en degrés (ICRS) ; `rayon` en degrés ; `nom` : nom donné (résolu
    ailleurs) ; filtres facultatifs, comparés sans casse ; `finaux` : seulement les produits finaux ;
    `publics` : seulement ce qui est déjà public.  Pour les sondes planétaires (OPUS, PDS) : `cible` = nom du corps
    (Jupiter, Saturne, Io…) et pas de coordonnées."""
    nom: str = ''
    ra: float | None = None
    dec: float | None = None
    rayon: float = 3.0 / 60
    archives: tuple = ()
    missions: tuple = ()
    instruments: tuple = ()
    filtres: tuple = ()
    date_min: str = ''
    date_max: str = ''
    calib_min: int | None = None
    finaux: bool = True
    publics: bool = True
    cible: str = ''
    limite: int = MAX_LIGNES
    extra: dict = field(default_factory=dict)


@dataclass
class Resultat:
    archive: str
    observations: list
    tronque: bool = False
    erreur: str = ''
    compte_requis: bool = False
    non_pris_en_charge: bool = False
    secondes: float = 0.0


# ----------------------------------------------------------------------------------- dates
def maintenant() -> D.datetime:
    return D.datetime.now(D.timezone.utc)


def mjd_vers_iso(mjd) -> str:
    try:
        f = float(mjd)
    except (TypeError, ValueError):
        return ''
    if not math.isfinite(f) or f <= 0:
        return ''
    t = D.datetime(1858, 11, 17, tzinfo=D.timezone.utc) + D.timedelta(days=f)
    return t.strftime('%Y-%m-%dT%H:%M:%S')


def iso_normal(s) -> str:
    """Date ISO tronquée à la seconde, sans fuseau (« 2013-02-11T01:44:50 ») ; '' si illisible."""
    s = (str(s or '')).strip().replace(' ', 'T')
    m = re.match(r'^(\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}(?::\d{2})?))?', s)
    if not m:
        return ''
    h = m.group(2) or ''
    if len(h) == 5:
        h += ':00'
    return m.group(1) + ('T' + h if h else '')


def deja_public(date_iso: str, droits: str = '') -> bool:
    """True si la date de mise à disposition est passée (et les droits ne disent pas « exclusif »)."""
    if droits and droits.upper() not in ('PUBLIC', ''):
        return False
    if not date_iso:
        return True                     # aucune date annoncée : l'archive ne la publie que pour le public
    return date_iso[:19] <= maintenant().strftime('%Y-%m-%dT%H:%M:%S')


def dans_periode(debut: str, date_min: str, date_max: str) -> bool:
    if not debut:
        return not (date_min or date_max)
    d = debut[:10]
    return (not date_min or d >= date_min[:10]) and (not date_max or d <= date_max[:10])


# ----------------------------------------------------------------------------------- géométrie
def distance_deg(ra1, dec1, ra2, dec2) -> float:
    """Distance angulaire (formule de Vincenty, stable aux petits et grands angles)."""
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    dr = r2 - r1
    num = math.hypot(math.cos(d2) * math.sin(dr), math.cos(d1) * math.sin(d2) - math.sin(d1) * math.cos(d2) * math.cos(dr))
    den = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(dr)
    return math.degrees(math.atan2(num, den))


def boite_ra(ra: float, dec: float, rayon: float) -> list[tuple[float, float]] | None:
    """Intervalles d'ascension droite qui contiennent le cercle (None : tout le cercle, près d'un pôle)."""
    if abs(dec) + rayon >= 89.0:
        return None
    w = rayon / max(math.cos(math.radians(abs(dec) + rayon)), 1e-3)
    if w >= 180:
        return None
    a, b = ra - w, ra + w
    if a < 0:
        return [(a + 360, 360.0), (0.0, b)]
    if b > 360:
        return [(a, 360.0), (0.0, b - 360)]
    return [(a, b)]


def polygone(s_region: str) -> list[tuple[float, float]]:
    """Sommets d'un s_region « POLYGON [ICRS] ra dec ra dec … » (STC-S) ; [] sinon."""
    if not s_region:
        return []
    t = s_region.replace(',', ' ').split()
    if not t or t[0].upper() != 'POLYGON':
        return []
    nombres = []
    for x in t[1:]:
        try:
            nombres.append(float(x))
        except ValueError:
            continue                    # repère (ICRS, J2000…)
    return [(nombres[i], nombres[i + 1]) for i in range(0, len(nombres) - 1, 2)]


def point_dans_polygone(ra, dec, sommets) -> bool:
    """Test de l'appartenance d'un point à un polygone de petite taille (plan tangent au point)."""
    if len(sommets) < 3:
        return False
    c = math.cos(math.radians(dec))
    pts = [(((a - ra + 540) % 360 - 180) * c, d - dec) for a, d in sommets]
    dedans = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > 0) != (yj > 0) and 0 < (xj - xi) * (0 - yi) / ((yj - yi) or 1e-30) + xi:
            dedans = not dedans
        j = i
    return dedans


def recouvre(obs: dict, ra: float, dec: float, rayon: float, s_region: str = '') -> bool:
    """L'observation touche-t-elle le cercle de recherche ?  Centre dans le cercle, ou cible dans l'empreinte."""
    if obs.get('ra') is None or obs.get('dec') is None:
        return True
    d = distance_deg(ra, dec, obs['ra'], obs['dec'])
    obs['distance'] = d
    if d <= rayon:
        return True
    return point_dans_polygone(ra, dec, polygone(s_region))


# ----------------------------------------------------------------------------------- réponses
def lire_votable(octets: bytes) -> list[dict]:
    """Lignes d'une VOTable (TABLEDATA) ; lève ValueError si le service signale une erreur."""
    racine = ET.fromstring(octets)
    ns = ''
    if racine.tag.startswith('{'):
        ns = racine.tag[:racine.tag.index('}') + 1]
    for info in racine.iter(ns + 'INFO'):
        if info.get('name') == 'QUERY_STATUS' and info.get('value') == 'ERROR':
            raise ValueError(' '.join((info.text or info.get('value') or '').split())[:400])
    lignes = []
    for table in racine.iter(ns + 'TABLE'):
        noms = [f.get('name') for f in table.findall(ns + 'FIELD')]
        for tr in table.iter(ns + 'TR'):
            cellules = [(td.text or '') for td in tr.findall(ns + 'TD')]
            lignes.append(dict(zip(noms, cellules)))
    return lignes


def lire_csv(texte: str) -> list[dict]:
    lignes = [l for l in texte.splitlines() if l and not l.startswith('#')]
    return list(csv.DictReader(io.StringIO('\n'.join(lignes))))


def lire_tableau(octets: bytes) -> list[dict]:
    """VOTable ou CSV, selon le début de la réponse."""
    debut = octets[:200].lstrip()
    if debut.startswith(b'<'):
        return lire_votable(octets)
    return lire_csv(octets.decode('utf-8', 'replace'))


def nombre(v, defaut=None):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return defaut
    return f if math.isfinite(f) else defaut


def entier(v, defaut=None):
    f = nombre(v)
    return int(f) if f is not None else defaut


# ----------------------------------------------------------------------------------- lignes reçues
_local = threading.local()


def remettre_compte():
    _local.lignes = 0


def noter_lignes(n: int):
    """Nombre de lignes rendues par le serveur (avant les filtres côté client) : sert à signaler une réponse
    tronquée par la limite (`Requete.limite`).  Une valeur par fil (une archive par fil)."""
    _local.lignes = max(getattr(_local, 'lignes', 0), int(n))


def lignes_recues() -> int:
    return getattr(_local, 'lignes', 0)


# ----------------------------------------------------------------------------------- requêtes polies
_verrou = threading.Lock()
_derniers: dict[str, float] = {}


def attendre_tour(service: str):
    """Au plus une requête de recherche par seconde et par service (tous fils confondus)."""
    while True:
        with _verrou:
            t = time.monotonic()
            d = _derniers.get(service, 0.0)
            if t - d >= INTERVALLE_MIN:
                _derniers[service] = t
                return
            attente = INTERVALLE_MIN - (t - d)
        time.sleep(attente)


def lire_url(url: str, data: bytes | None = None, delai: float = DELAI, en_tetes: dict | None = None,
             service: str = '') -> bytes:
    if service:
        attendre_tour(service)
    try:
        with reseau.requete(url, data=data, en_tetes=en_tetes, delai=delai) as r:
            b = r.read(TAILLE_REPONSE_MAX + 1)
    except Exception as e:
        code = getattr(e, 'code', None)
        if code in (401, 403):
            raise CompteRequis('HTTP %d' % code) from e
        raise reseau.ServiceInjoignable('%s: %s' % (type(e).__name__, e)) from e
    if len(b) > TAILLE_REPONSE_MAX:
        raise reseau.ServiceInjoignable('response too large')
    return b


def tap(url_service: str, adql: str, delai: float = DELAI, service: str = '') -> list[dict]:
    corps = urllib.parse.urlencode({'REQUEST': 'doQuery', 'LANG': 'ADQL', 'FORMAT': 'csv',
                                    'RESPONSEFORMAT': 'csv', 'QUERY': adql}).encode()
    lignes = lire_tableau(lire_url(url_service.rstrip('/') + '/sync', data=corps, delai=delai, service=service))
    noter_lignes(len(lignes))
    return lignes


def lire_json(url: str, data=None, delai: float = DELAI, service: str = ''):
    en_tetes = {'Content-Type': 'application/json'} if data is not None else None
    corps = json.dumps(data).encode() if data is not None else None
    return json.loads(lire_url(url, data=corps, delai=delai, en_tetes=en_tetes, service=service).decode('utf-8'))


def lien(cle: str, **valeurs) -> str:
    modele = sources.valeur(cle)
    if not modele:
        return ''
    try:
        return modele.format(**{k: urllib.parse.quote(str(v), safe=':/') for k, v in valeurs.items()})
    except (KeyError, IndexError, ValueError):
        return ''


def adql_texte(s: str) -> str:
    return "'%s'" % str(s).replace("'", "''")


def nom_fichier(url: str) -> str:
    """Nom du fichier d'une adresse (paramètre `uri=`, `dataset=`, `filehand=`, ou fin du chemin)."""
    u = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(u.query)
    for k in ('uri', 'dataset', 'filehand', 'file'):
        if k in q and q[k]:
            return q[k][0].rstrip('/').rsplit('/', 1)[-1].rsplit(':', 1)[-1]
    return u.path.rstrip('/').rsplit('/', 1)[-1]


def format_de(nom: str) -> str:
    n = nom.lower()
    for suffixe, fmt in (('.fits.gz', 'fits.gz'), ('.fit.gz', 'fits.gz'), ('.fits.fz', 'fits.fz'), ('.fz', 'fits.fz'),
                         ('.fits.bz2', 'fits.bz2'), ('.fits', 'fits'), ('.fit', 'fits'), ('.fts', 'fits'),
                         ('.img', 'pds3'), ('.xml', 'pds4')):
        if n.endswith(suffixe):
            return fmt
    return 'fits'


def observation(**valeurs) -> dict:
    """Observation complète (toutes les clés présentes, valeurs par défaut)."""
    o = {'id': '', 'archive': '', 'mission': '', 'instrument': '', 'filtre': '', 'lambda_nm': None, 'debut': '',
         'publique': '', 'public': True, 'calib': None, 'final': False, 'cible': '', 'ra': None, 'dec': None,
         'distance': None, 'url': '', 'fichier': '', 'format': 'fits', 'etiquette': '', 'taille': None, 'apercu': '',
         'page': '', 'programme': '', 'pi': '', 'titre': '', 'credit': '', 'conditions': '', 'obs_id': '',
         'type': 'image'}
    o.update(valeurs)
    if not o['fichier'] and o['url']:
        o['fichier'] = nom_fichier(o['url'])
    if o['fichier'] and valeurs.get('format') is None:
        o['format'] = format_de(o['fichier'])
    return o


def filtrer(observations: list[dict], q: Requete) -> list[dict]:
    """Filtres communs, appliqués côté client (toutes archives) : mission, instrument, filtre, dates, public,
    niveau.  Comparaisons sans casse, par sous-chaîne pour l'instrument et le filtre (« NIRCAM » trouve
    « NIRCAM/IMAGE »)."""
    mis = [m.lower() for m in q.missions if m]
    ins = [m.lower() for m in q.instruments if m]
    fil = [m.lower() for m in q.filtres if m]
    out = []
    for o in observations:
        if mis and o['mission'].lower() not in mis:
            continue
        if ins and not any(i in o['instrument'].lower() for i in ins):
            continue
        if fil and not any(f == o['filtre'].lower() or f in o['filtre'].lower().split(';') for f in fil):
            continue
        if (q.date_min or q.date_max) and not dans_periode(o['debut'], q.date_min, q.date_max):
            continue
        if q.publics and not o['public']:
            continue
        if q.finaux and not o['final']:
            continue
        if q.calib_min is not None and o['calib'] is not None and o['calib'] < q.calib_min:
            continue
        out.append(o)
    return out


class Archive:
    """Une archive.  `chercher(q)` rend une liste d'observations (non filtrées par `filtrer`, l'appelant le fait).
    `credit` : crédit à afficher ; `conditions` : clé de texte des conditions d'usage ; `compte` : True si un
    compte est exigé même pour les données publiques ; `celeste` : recherche par coordonnées (sinon par corps du
    Système solaire)."""
    id = ''
    nom = ''
    missions: tuple = ()
    credit = ''
    conditions = ''
    compte = False
    celeste = True
    etape = 1

    def chercher(self, q: Requete) -> list[dict]:          # pragma: no cover - abstrait
        raise NotImplementedError

    def adresse_fichier(self, o: dict) -> str:
        """Adresse à télécharger (certaines archives la résolvent au dernier moment : datalink)."""
        return o['url']
