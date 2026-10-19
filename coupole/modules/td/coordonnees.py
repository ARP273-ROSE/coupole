"""Lire une position géographique ou un angle écrits de N'IMPORTE QUELLE façon (même règles que Coupole Web,
``src/calc/coordonnees.ts`` ; cas communs : ``tests/td_coordonnees_cas.json``).

Angles acceptés : « 48.785 », « 48,785 », « -2.35 », « +44:13:51 », « 48°47′6″N », « 48° 47' 6" N », « 48 47 06 N »,
« 48d47m6s », « N 48 47 06 », « 2,45° E », « 2.45E », « O 1,6 » (ouest), « 1.6 W », « 48°47,1′ N » (minutes
décimales), symboles ° º ˚, ′ ' ’ ‘ ´, ″ " ” “ et « '' ».  Erreurs dites : minutes ou secondes ≥ 60, signe et lettre
contradictoires (« -48° N »), lettre inattendue (« 48° E » pour une latitude), texte illisible.

Position : deux angles dans n'importe quel ordre SI les lettres le disent (« 2°27′E 48°47′N ») ; sans lettre,
l'ordre est latitude puis longitude (comme Google Maps et la plupart des téléphones), et une latitude hors de
[−90°, 90°] avec une longitude possible est une inversion CERTAINE (corrigée et signalée).  Séparateurs : virgule
suivie d'une espace, point-virgule, barre, tabulation, ou simple espace entre deux nombres décimaux ; « 48 47 06 2 27
00 » (six nombres) se lit en deux groupes de trois.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LETTRES = {'N': ('lat', 1), 'S': ('lat', -1), 'E': ('lon', 1), 'O': ('lon', -1), 'W': ('lon', -1)}


class CoordonneeIllisible(ValueError):
    """`cle` : clé de texte (td_err_*) ; `valeurs` : champs du texte."""

    def __init__(self, cle: str, **valeurs):
        super().__init__(cle)
        self.cle, self.valeurs = cle, valeurs


@dataclass
class Angle:
    valeur: float
    genre: str = ''                  # 'lat' | 'lon' | '' (d'après la lettre)
    notes: list = field(default_factory=list)


def normaliser(t: str) -> str:
    t = (t or '').strip()
    for a, b in (('’', "'"), ('‘', "'"), ('´', "'"), ('`', "'"), ('′', "'"), ('″', '"'), ('”', '"'), ('“', '"'),
                 ("''", '"'), ('º', '°'), ('˚', '°'), ('−', '-'), ('–', '-'), (' ', ' '), (' ', ' ')):
        t = t.replace(a, b)
    return t.upper()


_NOMBRE = r'\d+(?:[.,]\d+)?'
RE_ANGLE = re.compile(
    r'^(?P<signe>[+-])?\s*(?P<d>' + _NOMBRE + r')\s*(?:°|D)?'
    r'(?:\s*(?::|\s)?\s*(?P<m>' + _NOMBRE + r")\s*(?:'|M)?"
    r'(?:\s*(?::|\s)?\s*(?P<s>' + _NOMBRE + r')\s*(?:"|S)?)?)?$')


def _f(x: str | None) -> float:
    return float((x or '0').replace(',', '.'))


def lire_angle(texte: str) -> Angle:
    """Un angle (degrés) ; lève CoordonneeIllisible."""
    t = normaliser(texte)
    if not t:
        raise CoordonneeIllisible('td_err_vide')
    notes = []
    lettre = ''
    m = re.match(r'^([NSEOW])\s*(.*)$', t)
    if m and not re.match(r'^[NSEOW]\s*$', t):
        lettre, t = m.group(1), m.group(2)
    else:
        m = re.match(r'^(.*?)\s*([NSEOW])$', t)
        if m and m.group(1):
            t, lettre = m.group(1), m.group(2)
    # « 48D47M6S » : le S final est le symbole des secondes, pas le Sud, s'il suit un M
    if lettre == 'S' and re.search(r'M\s*\d+(?:[.,]\d+)?$', t):
        t, lettre = t + 'S', ''
    t = t.strip()
    ma = RE_ANGLE.match(t)
    if not ma:
        raise CoordonneeIllisible('td_err_illisible', texte=texte.strip())
    d, mi, s = _f(ma.group('d')), _f(ma.group('m')), _f(ma.group('s'))
    if ma.group('m') is not None and (mi >= 60 or ('.' in ma.group('d') or ',' in ma.group('d'))):
        if mi >= 60:
            raise CoordonneeIllisible('td_err_minutes', texte=texte.strip())
        raise CoordonneeIllisible('td_err_illisible', texte=texte.strip())
    if ma.group('s') is not None and s >= 60:
        raise CoordonneeIllisible('td_err_secondes', texte=texte.strip())
    if ma.group('m') is not None:
        notes.append('td_n_dms')
    if ',' in t:
        notes.append('td_n_virgule')
    v = d + mi / 60.0 + s / 3600.0
    signe = -1.0 if ma.group('signe') == '-' else 1.0
    genre = ''
    if lettre:
        genre, s_lettre = LETTRES[lettre]
        if ma.group('signe') == '-' and s_lettre < 0:
            raise CoordonneeIllisible('td_err_signe', texte=texte.strip())
        if ma.group('signe') == '-' and s_lettre > 0:
            raise CoordonneeIllisible('td_err_signe', texte=texte.strip())
        signe = s_lettre
        notes.append('td_n_lettre')
    return Angle(signe * v, genre, notes)


def _decouper(t: str) -> list[str]:
    """Deux morceaux d'une position ; [] si on ne sait pas couper."""
    lettres = [m for m in re.finditer(r'[NSEOW]', t)
               if not (m.group(0) == 'S' and re.search(r'M\s*\d+(?:[.,]\d+)?\s*$', t[:m.start()]))]
    if len(lettres) == 2:
        if re.match(r'^\s*[NSEOW]', t):                    # lettres en tête : « N 48 47 E 2 27 »
            k = lettres[1].start()
            return [t[:k], t[k:]]
        k = lettres[0].end()                                # lettres en fin : « 48 47 N 2 27 E »
        return [t[:k], t[k:].lstrip(' ,;/')]
    for sep in (r'\s*;\s*', r'\s*/\s*', r'\t+', r',\s+', r'\s{2,}'):
        p = [x for x in re.split(sep, t) if x.strip()]
        if len(p) == 2:
            return p
    p = [x for x in re.split(r'(?<=["\'°DMS])\s+(?=[+-]?\d)', t) if x.strip()]
    if len(p) == 2:                                         # « 48°47'06" 2°27'00" »
        return p
    nombres = re.findall(r'[+-]?' + _NOMBRE, t)
    if re.fullmatch(r'\s*(?:[+-]?' + _NOMBRE + r'\s+)*[+-]?' + _NOMBRE + r'\s*', t) and len(nombres) in (2, 4, 6):
        k = len(nombres) // 2
        return [' '.join(nombres[:k]), ' '.join(nombres[k:])]
    if re.fullmatch(r'\s*[+-]?\d+(?:\.\d+)?\s*,\s*[+-]?\d+(?:\.\d+)?\s*', t):   # « 48.785,2.45 »
        return t.split(',')
    return []


@dataclass
class Position:
    lat: float
    lon: float
    notes: list = field(default_factory=list)       # td_n_* (normalisations) et td_a_* (alertes)


def lire_position(texte: str) -> Position:
    t = normaliser(texte)
    if not t:
        raise CoordonneeIllisible('td_err_vide')
    morceaux = _decouper(t)
    if len(morceaux) != 2:
        raise CoordonneeIllisible('td_err_deux_angles', texte=texte.strip())
    a, b = (lire_angle(x) for x in morceaux)
    notes = sorted(set(a.notes + b.notes))
    if a.genre and a.genre == b.genre:
        raise CoordonneeIllisible('td_err_deux_' + a.genre, texte=texte.strip())
    if a.genre == 'lon' or b.genre == 'lat':
        a, b = b, a
        notes.append('td_n_ordre_lettres')
    lat, lon = a.valeur, b.valeur
    if not (a.genre or b.genre) and abs(lat) > 90 and abs(lon) <= 90:
        lat, lon = lon, lat
        notes.append('td_a_inversion_certaine')
    if abs(lat) > 90:
        raise CoordonneeIllisible('td_err_latitude', texte=texte.strip())
    if abs(lon) > 360:
        raise CoordonneeIllisible('td_err_longitude', texte=texte.strip())
    if lon > 180:
        lon -= 360.0
        notes.append('td_n_longitude_360')
    return Position(lat, lon, notes)


def lire_altitude(texte: str) -> float:
    """« 120 », « 120 m », « 1,2 km », « 350,5 » → mètres ; vide → 0."""
    t = normaliser(texte).replace(' ', '')
    if not t:
        return 0.0
    km = t.endswith('KM')
    t = re.sub(r'(KM|M)$', '', t).replace(',', '.')
    try:
        return float(t) * (1000.0 if km else 1.0)
    except ValueError:
        raise CoordonneeIllisible('td_err_altitude', texte=texte.strip()) from None
