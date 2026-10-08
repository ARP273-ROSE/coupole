"""Classement des cibles : nom dans la base → objet canonique, catégorie.  Aucune table figée dans le code.

Ordre de priorité (le premier qui répond l'emporte) :
  1. corrections de l'utilisateur (``ohp_corrections.json`` dans les réglages) ;
  2. alias publiés dans le fichier de sources distant (``alias_ohp``) ;
  3. table livrée ``data/classement.json`` (194 noms vérifiés le 7/10/2026 : JPL
     SBDB, JPL Horizons, positions ; Inventaire.pdf chapitre 3) ;
  4. règles sur la forme du nom (comètes « C AAAA XX », « nnnP », désignations
     provisoires, petits corps numérotés) ;
  5. résolutions en ligne mises en cache (JPL SBDB pour les petits corps,
     CDS Sesame/SIMBAD pour le ciel profond), faites seulement à la demande ;
  6. regroupement par position (dans ``inventaire.enrichir``) : un nom inconnu
     dont le champ tombe sur un objet fixe déjà connu en devient un alias ;
  7. sinon : catégorie « autre » (non classé), traitée comme un objet mobile
     (un lot par nuit : on ne mélange jamais deux pointages).
Tout ce qui vient de 4 à 7 est marqué « à vérifier » ; l'utilisateur corrige
ou fusionne (``coupole ohp classer``, ou l'onglet Catalogue).
"""
from __future__ import annotations

import collections as C
import json
import re
import threading
from pathlib import Path

from ...core import config, i18n

DONNEES = Path(__file__).resolve().parent / 'data' / 'classement.json'

# catégorie → (dossier FR, dossier EN, fixe ?)
CATEGORIES = C.OrderedDict([
    ('ast', ('01_Asteroides', '01_Asteroids', False)),
    ('neocp', ('02_NEOCP_non_identifies', '02_NEOCP_unidentified', False)),
    ('com', ('03_Cometes', '03_Comets', False)),
    ('pla', ('04_Planetes', '04_Planets', False)),
    ('tno', ('05_Transneptuniens', '05_Trans-Neptunian', False)),
    ('pn', ('06_Nebuleuses_planetaires', '06_Planetary_nebulae', True)),
    ('neb', ('07_Nebuleuses', '07_Nebulae', True)),
    ('amas', ('08_Amas', '08_Star_clusters', True)),
    ('gal', ('09_Galaxies', '09_Galaxies', True)),
    ('eto', ('10_Etoiles_variables', '10_Variable_stars', True)),
    ('autre', ('11_Non_classes', '11_Unclassified', False)),
])
FIXES = {k for k, v in CATEGORIES.items() if v[2]}
MOBILES = {k for k, v in CATEGORIES.items() if not v[2]}

_verrou = threading.Lock()
_donnees: dict | None = None


def donnees() -> dict:
    global _donnees
    if _donnees is None:
        _donnees = json.loads(DONNEES.read_text(encoding='utf-8'))
    return _donnees


def _alias_livres() -> dict:
    return donnees()['alias']


def noms_en() -> dict:
    return donnees().get('noms_en', {})


def remarques_en() -> dict:
    return donnees().get('remarques_en', {})


# ---------------------------------------------------------------- corrections de l'utilisateur
def chemin_corrections() -> Path:
    return config.dossier_config() / 'ohp_corrections.json'


def corrections() -> dict:
    try:
        return json.loads(chemin_corrections().read_text(encoding='utf-8'))
    except Exception:
        return {}


def corriger(nom_base: str, objet: str | None, cat: str | None = None, rem: str = '', sbdb=None):
    """Mémorise une correction (objet=None : supprime la correction)."""
    with _verrou:
        c = corrections()
        if objet is None:
            c.pop(nom_base, None)
        else:
            if cat is not None and cat not in CATEGORIES:
                raise ValueError(cat)
            c[nom_base] = {'objet': objet, 'cat': cat or 'autre', 'sbdb': sbdb, 'rem': rem}
        chemin_corrections().write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding='utf-8')


# ---------------------------------------------------------------- résolutions en ligne (cache)
def chemin_resolutions() -> Path:
    return config.dossier_cache() / 'ohp_resolutions.json'


def resolutions() -> dict:
    try:
        return json.loads(chemin_resolutions().read_text(encoding='utf-8'))
    except Exception:
        return {}


# ---------------------------------------------------------------- règles
def par_regles(nom: str):
    m = re.match(r'^C (\d{4}) ([A-Z]+\d*) (.+)$', nom)                 # « C 2017 K2 PANSTARRS »
    if m:
        return ('C/%s %s (%s)' % m.groups(), 'com', 'C/%s %s' % (m.group(1), m.group(2)), '')
    if re.match(r'^(\d{4} [A-Z]{2}\d*)$', nom):                         # « 2018 PT23 »
        return (nom, 'ast', nom, '')
    m = re.match(r'^(\d+) (.+?)(?: A\d{3} ?[A-Z]{2})?$', nom)          # « 3 Juno A804 RA »
    if m:
        num, reste = m.groups()
        if re.match(r'^\d{4} [A-Z]{2}\d*$', reste):
            return ('(%s) %s' % (num, reste), 'ast', num, '')
        return ('(%s) %s' % (num, re.sub(r' \d{4} [A-Z]{2}\d*$', '', reste)), 'ast', num, '')
    m = re.match(r'^(\d+P)[ /](.+)$', nom)                              # « 29P Schwassmann... »
    if m:
        return ('%s/%s' % m.groups(), 'com', m.group(1), '')
    return None


def classer(nom: str):
    """nom dans la base → (objet canonique, catégorie, clé SBDB ou None, remarque, origine)."""
    return Classeur().classer(nom)


class Classeur:
    """Instantané des tables (une lecture de fichier par enrichissement, pas par image)."""

    def __init__(self):
        from ...core import sources
        self.utilisateur = corrections()
        self.distants = sources.alias_distants()
        self.livres = _alias_livres()
        self.resolus = resolutions()

    def classer(self, nom: str):
        for table, origine in ((self.utilisateur, 'utilisateur'), (self.distants, 'distant'), (self.livres, 'table')):
            e = table.get(nom)
            if e and e.get('objet') and e.get('cat') in CATEGORIES:
                return (e['objet'], e['cat'], e.get('sbdb'), e.get('rem', ''), origine)
        r = par_regles(nom)
        if r:
            return r + ('regle',)
        e = self.resolus.get(nom)
        if e and e.get('objet') and e.get('cat') in CATEGORIES:
            return (e['objet'], e['cat'], e.get('sbdb'), e.get('rem', ''), e.get('source', 'en_ligne'))
        return ((nom or '').strip() or '?', 'autre', None, '', 'inconnu')


# ---------------------------------------------------------------- affichage
def nom_affiche(objet: str, langue: str | None = None) -> str:
    return noms_en().get(objet, objet) if (langue or i18n.langue()) == 'en' else objet


def remarque(rem: str, langue: str | None = None) -> str:
    return remarques_en().get(rem, rem) if (langue or i18n.langue()) == 'en' else rem


def dossier_categorie(cat: str, langue: str) -> str:
    fr, en, _ = CATEGORIES.get(cat, CATEGORIES['autre'])
    return en if langue == 'en' else fr


ORIGINES_SURES = {'utilisateur', 'distant', 'table', 'regle'}
