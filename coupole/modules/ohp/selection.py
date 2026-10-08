"""Recherche et filtres sur l'inventaire, estimation du volume avant téléchargement."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import formats

# filtre court → valeurs de filter_name (« R » vise aussi « Rcousins »)
COURTS = {'B': ['Johnson B', 'Bcousins'], 'V': ['Johnson V', 'Vcousins'], 'R': ['Johnson R', 'Rcousins'],
          'Bc': ['Bcousins'], 'Vc': ['Vcousins'], 'Rc': ['Rcousins'], 'Ha': ['Ha'], 'OIII': ['OIII'],
          'g': ['SDSS g'], 'r': ['SDSS r'], 'i': ['SDSS i', 'iGunn'], 'z': ['SDSS z']}


def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def objets_correspondants(images, requete: str) -> list[str]:
    """Objets canoniques : égalité exacte (objet ou nom de la base), puis inclusion."""
    from .cibles import noms_en
    NOMS_EN = noms_en()
    q = norm(requete)
    if not q:
        return []
    en = {v: k for k, v in NOMS_EN.items()}
    for champ in ('objet', 'target_name'):
        objs = sorted({x['objet'] for x in images if norm(x[champ]) == q})
        if objs:
            return objs
    objs = sorted({en[o] for o in en if norm(o) == q})
    if objs:
        return objs
    return sorted({x['objet'] for x in images if q in norm(x['objet']) or q in norm(x['target_name'])
                   or q in norm(NOMS_EN.get(x['objet'], ''))})


def filtres_voulus(arg) -> set | None:
    if not arg:
        return None
    vals = arg if isinstance(arg, (list, tuple, set)) else str(arg).split(',')
    out = set()
    for f in vals:
        f = f.strip()
        out.update(COURTS.get(f, [f]))
    return out


@dataclass
class Criteres:
    objets: list = field(default_factory=list)      # objets canoniques ; vide = tous
    categories: list = field(default_factory=list)  # 'ast', 'neb'...
    telescopes: list = field(default_factory=list)  # 'T120', 'IRIS'
    filtres: list = field(default_factory=list)     # courts ou exacts
    nuits: list = field(default_factory=list)       # 'AAAA-MM-JJ'
    sans_dates_douteuses: bool = False
    avec_doublons: bool = True                      # garder les doublons pour le journal (jamais téléchargés)


def selectionner(images, c: Criteres) -> list[dict]:
    fv = filtres_voulus(c.filtres)
    objs = set(c.objets)
    nuits = {str(n).strip() for n in c.nuits}
    out = []
    for x in images:
        if objs and x['objet'] not in objs:
            continue
        if c.categories and x['cat'] not in c.categories:
            continue
        if c.telescopes and x['tel'] not in c.telescopes:
            continue
        if fv and x['filter_name'] not in fv:
            continue
        if nuits and str(x['nuit']) not in nuits:
            continue
        if c.sans_dates_douteuses and (x['date_partagee'] or x['diurne']) and not x['doublon']:
            continue
        if x['doublon'] and not c.avec_doublons:
            continue
        out.append(x)
    return out


def estimer(selection, fmt='xisf') -> dict:
    """Volume à télécharger et volume attendu en sortie (rapports mesurés, formats.RATIOS)."""
    utiles = [x for x in selection if not x['doublon']]
    fits_ = sum(x['access_estsize'] * 1024 for x in utiles)
    sortie = sum(x['access_estsize'] * 1024 * formats.RATIOS[fmt].get(x['tel'], 1.0) for x in utiles)
    plus_gros = max((x['access_estsize'] * 1024 for x in utiles), default=0)
    return {'images': len(utiles), 'doublons': len(selection) - len(utiles), 'octets_fits': fits_,
            'octets_sortie': sortie, 'plus_gros': plus_gros,
            'nuits': len({str(x['nuit']) for x in utiles}), 'objets': len({x['objet'] for x in utiles})}


def place_necessaire(est: dict, conversions: int, telechargements: int) -> float:
    """Octets à prévoir à destination : la sortie + les FITS en attente (fenêtre du pilote)."""
    return est['octets_sortie'] + (2 * conversions + telechargements) * est['plus_gros'] * 2
