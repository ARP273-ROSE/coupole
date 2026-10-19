"""Paires simultanées : deux observateurs différents, même cible, presque au même instant, assez loin l'un de l'autre.

Seuils par défaut (réglables) : écart d'heure ≤ 5 s pour l'ISS (elle parcourt 7,7 km par seconde : à 1 s d'écart, son
image se déplace de ~1° vu d'un observateur, à corriger le long du trait), ≤ 60 s pour la Lune (≈ 33″ de mouvement
propre par minute, corrigé par l'éphéméride) ; base ≥ 100 km (la parallaxe de la Lune vaut ~1′ par 100 km).

Une observation est un point (une photo datée) ou un intervalle (une série de poses, une vidéo) : l'écart entre deux
intervalles qui se recouvrent est nul.
"""
from __future__ import annotations

import datetime as D
import math
from dataclasses import dataclass, field

from ...structure import normaliser

SEUILS_S = {'iss': 5.0, 'tiangong': 5.0, 'lune': 60.0}
SEUIL_DEFAUT_S = 60.0
BASE_MIN_KM = 100.0


@dataclass
class Observation:
    ident: str
    observateur: str
    cible: str
    debut: D.datetime
    fin: D.datetime | None = None
    lat: float | None = None
    lon: float | None = None
    alt_m: float | None = None
    source: str = ''                       # 'tableau' | 'entete' | 'nom'
    fichiers: list = field(default_factory=list)
    heure_sure: bool = True                # False : heure lue dans un nom de fichier (souvent l'heure locale)

    @property
    def fin_(self) -> D.datetime:
        return self.fin or self.debut


@dataclass
class Paire:
    a: Observation
    b: Observation
    cible: str
    ecart_s: float
    base_km: float | None
    notes: list = field(default_factory=list)       # clés pc_p_*

    @property
    def synchro_seconde(self) -> bool:
        return self.ecart_s <= 1.0


def base_km(a: Observation, b: Observation) -> float | None:
    if None in (a.lat, a.lon, b.lat, b.lon):
        return None
    from ... import astro
    import numpy as np
    return float(np.linalg.norm(astro.ecef(a.lat, a.lon, a.alt_m or 0) - astro.ecef(b.lat, b.lon, b.alt_m or 0)))


def ecart_s(a: Observation, b: Observation) -> float:
    if a.fin_ < b.debut:
        return (b.debut - a.fin_).total_seconds()
    if b.fin_ < a.debut:
        return (a.debut - b.fin_).total_seconds()
    return 0.0


def meme_observateur(a: Observation, b: Observation) -> bool:
    na, nb = normaliser(a.observateur), normaliser(b.observateur)
    if na and nb and (na == nb or na in nb or nb in na):
        return True
    d = base_km(a, b)
    return d is not None and d < 1.0


def trouver(observations: list, seuils: dict | None = None, base_min: float = BASE_MIN_KM,
            garder_sans_lieu: bool = True) -> list[Paire]:
    seuils = dict(SEUILS_S, **(seuils or {}))
    obs = sorted([o for o in observations if o.debut is not None], key=lambda o: o.debut)
    out = []
    for i, a in enumerate(obs):
        for b in obs[i + 1:]:
            s_max = max(seuils.get(a.cible, SEUIL_DEFAUT_S), seuils.get(b.cible, SEUIL_DEFAUT_S))
            if (b.debut - a.fin_).total_seconds() > s_max:
                break
            if not a.cible or a.cible != b.cible or meme_observateur(a, b):
                continue
            e = ecart_s(a, b)
            if e > seuils.get(a.cible, SEUIL_DEFAUT_S):
                continue
            base = base_km(a, b)
            notes = []
            if base is None:
                if not garder_sans_lieu:
                    continue
                notes.append('pc_p_sans_lieu')
            elif base < base_min:
                continue
            if not (a.heure_sure and b.heure_sure):
                notes.append('pc_p_heure_nom')
            out.append(Paire(a, b, a.cible, e, base, notes))
    out.sort(key=lambda p: (p.ecart_s, -(p.base_km or 0)))
    return out


def depuis_tableau(t, appliquer: bool = True) -> list[Observation]:
    """Observations tirées d'un tableau de mesures (mesures.Tableau) : corrections proposées appliquées."""
    out = []
    for m in t.mesures:
        inst = m.retenu('instant', appliquer)
        if inst is None or not m.cible:
            continue
        out.append(Observation('L%d' % m.ligne, m.auteur, m.cible, inst, None, m.retenu('lat', appliquer),
                               m.retenu('lon', appliquer), m.alt_m, 'tableau', [m.fichier] if m.fichier else []))
    return _fusionner(out)


def _fusionner(obs: list) -> list[Observation]:
    """Une même prise décrite par plusieurs lignes (FITS, PNG, TIFF…) : une seule observation."""
    vus: dict[tuple, Observation] = {}
    for o in obs:
        cle = (normaliser(o.observateur), o.cible, o.debut.replace(microsecond=0), round(o.lat or 0, 2),
               round(o.lon or 0, 2))
        if cle in vus:
            vus[cle].fichiers.extend(o.fichiers)
            vus[cle].ident += '+' + o.ident
        else:
            vus[cle] = o
    return list(vus.values())


def depuis_structure(structure, entetes: dict | None = None) -> list[Observation]:
    """Observations tirées de la structure d'un partage : une par série (intervalle), lieu et heure des en-têtes
    quand ils sont connus (`entetes` : {chemin: lieu_et_heure}), sinon heure du nom (marquée « peu sûre »)."""
    entetes = entetes or {}
    out = []
    for s in structure.series:
        lieux = [entetes[f.chemin] for f in s.fichiers if f.chemin in entetes]
        heures = sorted(e['milieu'] for e in lieux if e.get('milieu'))
        lat = next((e['lat'] for e in lieux if e.get('lat') is not None), None)
        lon = next((e['lon'] for e in lieux if e.get('lon') is not None), None)
        alt = next((e['alt_m'] for e in lieux if e.get('alt_m') is not None), None)
        if heures:
            debut, fin, sure = heures[0], heures[-1], True
        else:
            debut, fin, sure = s.debut, s.fin, False
        out.append(Observation(s.ident, s.observateur, s.cible, debut, fin, lat, lon, alt,
                               'entete' if heures else 'nom', [f.chemin for f in s.fichiers], sure))
    return out


def resume_synchro(paires: list[Paire]) -> dict:
    return {'paires': len(paires), 'a_la_seconde': sum(1 for p in paires if p.synchro_seconde),
            'iss': sum(1 for p in paires if p.cible == 'iss'), 'lune': sum(1 for p in paires if p.cible == 'lune')}


def distance_minimale_km(a: Observation, b: Observation) -> float:
    d = base_km(a, b)
    return d if d is not None else math.nan
