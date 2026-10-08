"""Base des sites d'observation (livrée + sites ajoutés par l'utilisateur) et contrôle des en-têtes de position.

Correction des mots-clés de position : IDEMPOTENTE et CONDITIONNELLE.
  * valeurs justes (au site connu, ou à LAT-OBS/LONG-OBS)          → rien n'est touché ;
  * latitude et longitude échangées, et l'échange retombe sur le site → correction démontrée ;
  * autre chose (illisible, site différent, une seule valeur fausse)  → signalé, rien n'est touché.
Ainsi, le jour où la base de l'Observatoire corrige ses en-têtes, Coupole ne les ré-inverse pas.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .astro import parse_sexa, site_geodesique

FICHIER = Path(__file__).resolve().parent.parent / 'donnees' / 'sites.json'
TOLERANCE_DEG = 0.05          # ≈ 5 km : les en-têtes arrondissent à la minute d'arc, voire au degré près


@dataclass(eq=False)
class Site:
    id: str
    nom: str
    lat: float
    lon: float                      # degrés Est
    alt: float = 0.0
    fuseau: str = ''                # IANA ; vide : déduit de la longitude (approché)
    mpc: str = ''
    alias: list = field(default_factory=list)
    origine: str = 'livre'

    def zone(self):
        """Fuseau horaire (zoneinfo) ; repli : fuseau nautique fixe d'après la longitude (approché)."""
        import datetime as D
        if self.fuseau:
            try:
                from zoneinfo import ZoneInfo
                return ZoneInfo(self.fuseau)
            except Exception:
                pass
        return D.timezone(D.timedelta(hours=round(self.lon / 15)))

    @property
    def fuseau_approche(self) -> bool:
        if not self.fuseau:
            return True
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(self.fuseau)
            return False
        except Exception:
            return True


def _depuis_dict(d: dict, origine: str) -> Site:
    lat, lon, alt = d.get('lat'), d.get('lon'), d.get('alt', 0.0)
    if d.get('mpc_constantes'):            # source de vérité quand elle existe (pleine précision)
        lat, lon, alt = site_geodesique(*d['mpc_constantes'])
    return Site(id=str(d['id']), nom=str(d.get('nom', d['id'])), lat=float(lat), lon=float(lon),
                alt=float(alt or 0.0), fuseau=str(d.get('fuseau', '')), mpc=str(d.get('mpc', '')),
                alias=list(d.get('alias', [])), origine=origine)


def chemin_utilisateur() -> Path:
    return config.dossier_config() / 'sites_utilisateur.json'


def sites() -> list[Site]:
    out = {s['id']: _depuis_dict(s, 'livre') for s in json.loads(FICHIER.read_text(encoding='utf-8'))['sites']}
    try:
        for s in json.loads(chemin_utilisateur().read_text(encoding='utf-8')).get('sites', []):
            out[str(s['id'])] = _depuis_dict(s, 'utilisateur')
    except Exception:
        pass
    return list(out.values())


def site(ident: str) -> Site | None:
    return next((s for s in sites() if s.id == ident), None)


def par_nom(nom: str) -> Site | None:
    n = (nom or '').strip().lower()
    for s in sites():
        if n and (n == s.id or n == s.nom.lower() or n in (a.lower() for a in s.alias)):
            return s
    return None


def enregistrer_site(d: dict):
    """Ajoute ou remplace un site de l'utilisateur (id, nom, lat, lon, alt, fuseau, mpc)."""
    _depuis_dict(d, 'utilisateur')               # validation
    try:
        doc = json.loads(chemin_utilisateur().read_text(encoding='utf-8'))
    except Exception:
        doc = {'format': 1, 'sites': []}
    doc['sites'] = [s for s in doc.get('sites', []) if s.get('id') != d['id']] + [d]
    chemin_utilisateur().write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')


def supprimer_site(ident: str):
    try:
        doc = json.loads(chemin_utilisateur().read_text(encoding='utf-8'))
    except Exception:
        return
    doc['sites'] = [s for s in doc.get('sites', []) if s.get('id') != ident]
    chemin_utilisateur().write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')


# ======================================================================== contrôle des en-têtes de position
def _proche(a, b, tol=TOLERANCE_DEG):
    return a is not None and b is not None and abs(a - b) <= tol


def diagnostic_position(lat_txt, lon_txt, site_ref: Site | None, lat_obs=None, lon_obs=None) -> str:
    """'juste' | 'inversee' | 'ambigue' | 'absente' pour une paire LATITUDE/LONGITUD (texte).

    Référence : le site connu, à défaut LAT-OBS/LONG-OBS (valeurs numériques en degrés).
    Les longitudes Ouest négatives sont comparées telles quelles (convention degrés Est).
    """
    if lat_txt is None and lon_txt is None:
        return 'absente'
    la, lo = parse_sexa(lat_txt) if lat_txt is not None else None, parse_sexa(lon_txt) if lon_txt is not None else None
    if site_ref is not None:
        rl, rL = site_ref.lat, site_ref.lon
    elif lat_obs is not None and lon_obs is not None:
        rl, rL = lat_obs, lon_obs
    else:
        return 'ambigue'
    # en-têtes sans signe : comparer aussi en valeur absolue (hémisphère implicite)
    def eq(v, ref):
        return _proche(v, ref) or _proche(v, abs(ref)) if v is not None else False
    if (la is None or eq(la, rl)) and (lo is None or eq(lo, rL)):
        return 'juste'
    if la is not None and lo is not None and eq(la, rL) and eq(lo, rl) and not _proche(abs(rl), abs(rL), 1.0):
        return 'inversee'
    return 'ambigue'


def distance_km(lat1, lon1, lat2, lon2) -> float:
    r = math.radians
    a = math.sin(r(lat2 - lat1) / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(min(1, math.sqrt(a)))
