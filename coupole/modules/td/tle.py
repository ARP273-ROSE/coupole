"""Éléments orbitaux (TLE) de l'ISS : CelesTrak (source libre), gardés en cache.

CelesTrak ne publie que les éléments COURANTS ; l'historique des TLE n'est librement disponible qu'avec un compte
Space-Track (gratuit, mais personnel) : Coupole ne s'en sert pas et le dit.  Pour un instant donné, on prend le TLE du
cache dont l'époque est la plus proche ; s'il est à plus de 3 jours et que le réseau est permis, on récupère le TLE du
jour (utile pour un passage récent).  Hors ligne : saisie ou fichier.
"""
from __future__ import annotations

import datetime as D
import os
import re

from ...core import config

UTC = D.timezone.utc
AGE_MAX_J = 3.0


def dossier():
    p = config.dossier_cache() / 'tle'
    p.mkdir(parents=True, exist_ok=True)
    return p


def epoque(tle) -> D.datetime | None:
    """Époque d'un TLE (ligne 1, colonnes 19-32 : AAJJJ.JJJJJJJJ)."""
    l1 = next((x for x in tle if x.strip().startswith('1 ')), '')
    m = re.match(r'^1 .{16}(\d{2})(\d{3}\.\d+)', l1)
    if not m:
        return None
    a = int(m.group(1))
    a += 2000 if a < 57 else 1900
    return D.datetime(a, 1, 1, tzinfo=UTC) + D.timedelta(days=float(m.group(2)) - 1)


def lignes(texte: str) -> tuple | None:
    ls = [x.rstrip() for x in texte.splitlines() if x.strip()]
    l1 = next((x for x in ls if x.startswith('1 ')), None)
    l2 = next((x for x in ls if x.startswith('2 ')), None)
    return (l1, l2) if l1 and l2 else None


def en_cache() -> list[tuple]:
    out = []
    for f in sorted(dossier().glob('iss_*.tle')):
        try:
            t = lignes(f.read_text(encoding='ascii', errors='replace'))
        except OSError:
            continue
        if t and epoque(t):
            out.append(t)
    return out


def garder(tle: tuple) -> None:
    e = epoque(tle)
    if e is None:
        return
    p = dossier() / ('iss_%s.tle' % e.strftime('%Y%m%dT%H%M'))
    p.write_text('ISS (ZARYA)\n%s\n%s\n' % tle, encoding='ascii')


def telecharger() -> tuple:
    """TLE courant de CelesTrak (adresse dans les sources de Coupole) ; gardé en cache."""
    from ...core import reseau, sources
    texte = reseau.lire_texte(sources.valeur('tle.iss'), delai=20)
    t = lignes(texte)
    if not t:
        raise ValueError('no TLE in answer')
    garder(t)
    return t


def pour(instant: D.datetime, reseau_permis: bool = True) -> dict:
    """{'tle', 'epoque', 'age_jours', 'source': 'cache'|'celestrak'|'', 'erreur'} pour l'instant donné."""
    cands = en_cache()
    meilleur = min(cands, key=lambda t: abs((epoque(t) - instant).total_seconds()), default=None)
    age = abs((epoque(meilleur) - instant).total_seconds()) / 86400 if meilleur else None
    erreur = ''
    if (meilleur is None or age > AGE_MAX_J) and reseau_permis and not os.environ.get('COUPOLE_SANS_RESEAU'):
        try:
            t = telecharger()
            a2 = abs((epoque(t) - instant).total_seconds()) / 86400
            if meilleur is None or a2 < age:
                return {'tle': t, 'epoque': epoque(t), 'age_jours': a2, 'source': 'celestrak', 'erreur': ''}
        except Exception as e:                              # hors ligne, service indisponible
            erreur = '%s: %s' % (type(e).__name__, e)
    if meilleur is None:
        return {'tle': None, 'epoque': None, 'age_jours': None, 'source': '', 'erreur': erreur}
    return {'tle': meilleur, 'epoque': epoque(meilleur), 'age_jours': age, 'source': 'cache', 'erreur': erreur}
