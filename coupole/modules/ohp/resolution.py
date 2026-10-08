"""Résolution en ligne des noms inconnus (facultative, à la demande, avec cache).

* Petits corps : JPL Small-Body Database API (``resolution.sbdb`` dans les
  sources) — catégorie déduite du type (comète/astéroïde) et de la classe
  orbitale (TNO → transneptunien).
* Ciel profond : CDS Sesame (``resolution.sesame``), qui interroge SIMBAD,
  NED et VizieR — catégorie déduite du type d'objet SIMBAD.
Chaque résultat est mis en cache (``ohp_resolutions.json``) et marqué « à
vérifier ».  Hors ligne ou en cas d'erreur : rien n'est bloqué, le nom reste
non classé.  Délais courts, une requête par nom, au plus ``MAX_NOMS`` noms.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import xml.etree.ElementTree as ET

from ...core import reseau, sources
from . import cibles

MAX_NOMS = 50
DELAI = 10

# type d'objet SIMBAD (abréviations) → catégorie
OTYPES = [
    (('PN', 'PN?'), 'pn'),
    (('HII', 'RNe', 'SNR', 'DNe', 'ISM', 'Cld', 'MoC', 'GNe', 'BNe', 'EmO', 'SFR'), 'neb'),
    (('GlC', 'OpC', 'Cl*', 'As*', 'C?*', 'Gl?'), 'amas'),
    (('G', 'GiG', 'GiP', 'GiC', 'IG', 'PaG', 'Sy1', 'Sy2', 'SyG', 'AGN', 'LIN', 'QSO', 'BLL', 'SBG', 'H2G', 'EmG',
      'rG', 'LSB', 'bCG', 'GrG', 'CGG', 'ClG', 'SCG'), 'gal'),
    (('V*', 'No*', 'Ce*', 'RR*', 'Mi*', 'EB*', 'CV*', 'Ir*', 'Ro*', 'Pu*', 'sr*', 'Er*', 'gD*', 'dS*', 'NL*',
      'SN*', 'SN'), 'eto'),
]


def categorie_otype(otype: str) -> str | None:
    o = (otype or '').strip()
    for codes, cat in OTYPES:
        if o in codes:
            return cat
    return None


def ressemble_petit_corps(nom: str) -> bool:
    return bool(re.search(r'\d{4} ?[A-Z]{2}\d*|^\d+ |^[CPDXAI][/ ]\d{4}|^\d+P\b', nom))


def _json(url, delai=DELAI):
    with reseau.requete(url, delai=delai) as r:
        return json.loads(r.read(500_000).decode('utf-8'))


def via_sbdb(nom: str) -> dict | None:
    base = sources.valeur('resolution.sbdb')
    if not base:
        return None
    try:
        d = _json(base + '?' + urllib.parse.urlencode({'sstr': nom}))
    except Exception:
        return None
    o = d.get('object') if isinstance(d, dict) else None
    if not o:
        return None
    nom_complet = o.get('fullname') or nom
    kind = o.get('kind', '')
    classe = (o.get('orbit_class') or {}).get('code', '')
    if kind.startswith('c'):
        cat = 'com'
        objet = nom_complet.strip()
    else:
        cat = 'tno' if classe == 'TNO' else 'ast'
        m = re.match(r'^\s*(\d+)\s+(.+?)(?:\s+\(.*\))?\s*$', nom_complet)
        objet = '(%s) %s' % (m.group(1), m.group(2)) if m else nom_complet.strip()
    return {'objet': objet, 'cat': cat, 'sbdb': o.get('spkid') or o.get('des'), 'rem': classe,
            'source': 'sbdb'}


def via_sesame(nom: str) -> dict | None:
    base = sources.valeur('resolution.sesame')
    if not base:
        return None
    try:
        with reseau.requete(base + '?' + urllib.parse.quote(nom), delai=DELAI) as r:
            racine = ET.fromstring(r.read(500_000))
    except Exception:
        return None
    for res in racine.iter('Resolver'):
        otype = (res.findtext('otype') or '').strip()
        oname = (res.findtext('oname') or '').strip()
        ra, de = res.findtext('jradeg'), res.findtext('jdedeg')
        cat = categorie_otype(otype)
        if oname:
            d = {'objet': re.sub(r'\s+', ' ', oname), 'cat': cat or 'autre', 'sbdb': None, 'rem': otype,
                 'source': 'sesame'}
            try:
                d['ra'], d['dec'] = float(ra), float(de)
            except (TypeError, ValueError):
                pass
            return d
    return None


def resoudre(noms: list[str], progression=None) -> dict:
    """Résout les noms (au plus MAX_NOMS), enrichit le cache, renvoie {nom: résultat ou None}."""
    cache = cibles.resolutions()
    out = {}
    for k, nom in enumerate(noms[:MAX_NOMS]):
        if nom in cache:
            out[nom] = cache[nom]
            continue
        r = None
        ordre = (via_sbdb, via_sesame) if ressemble_petit_corps(nom) else (via_sesame, via_sbdb)
        for f in ordre:
            r = f(nom)
            if r:
                break
        out[nom] = r
        if r:
            cache[nom] = r
        if progression:
            progression(k + 1, len(noms))
    try:
        cibles.chemin_resolutions().write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
    except OSError:
        pass
    return out


def noms_inconnus(images) -> list[str]:
    return sorted({x['target_name'] for x in images if x['classement'] == 'inconnu'})
