"""« Maintenant » et « En direct » : l'instant de l'appareil pour les animations qui dépendent de la date et de l'heure.

Portage ligne pour ligne de `coupole-web/src/calc/maintenant.ts` ; cas de parité : `tests/maintenant_cas.json`
(produits par `outils/cas_maintenant.py`, rejoués ici par `tests/test_maintenant.py` et au web par
`tests/unit/maintenant.test.ts`).

Règles (aucune erreur de fuseau ni d'heure d'été) :
- l'instant vient de l'horloge en temps universel absolu (`datetime.now(timezone.utc)` ; au web `Date.now()`) ;
- les calculs se font en TU (jour julien) ; l'heure LOCALE ne sert qu'à l'affichage, par le fuseau IANA de
  l'appareil (zoneinfo ; tzdata sous Windows) : « 09:20 heure de Paris (UTC+2) · 07:20 TU » ;
- une animation réglée en heure solaire (sans longitude) reçoit l'heure solaire moyenne TU + longitude / 15, la
  longitude étant celle de « Ma position » (géolocalisation demandée explicitement) ou, à défaut, le méridien du
  fuseau (décalage HORS heure d'été × 15°) : jamais l'heure de l'horloge, qui porte l'heure d'été ;
- le « jour » des animations est l'indice 0–364 d'une année de 365 jours (le 29 février compte comme le 28).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

MOIS_JOURS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def fuseau_local() -> str:
    """Nom IANA du fuseau de l'appareil (« Europe/Paris »), « UTC » à défaut."""
    try:
        from tzlocal import get_localzone_name          # facultatif
        n = get_localzone_name()
        if n:
            return n
    except Exception:
        pass
    import os
    tz = os.environ.get('TZ', '').lstrip(':')
    if tz and _zone(tz) is not None:
        return tz
    try:
        from pathlib import Path
        p = Path('/etc/localtime').resolve()
        if 'zoneinfo' in p.parts:
            n = '/'.join(p.parts[p.parts.index('zoneinfo') + 1:])
            if _zone(n) is not None:
                return n
    except Exception:
        pass
    # Windows sans nom IANA connu : le fuseau du système, heure d'été comprise (sans nom de ville)
    return LOCAL


LOCAL = 'local'


def _zone(nom: str):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(nom)
    except Exception:
        return None


@dataclass
class Instant:
    ms: int                 # millisecondes depuis 1970 (TU)
    tz: str                 # fuseau IANA
    decalage: int           # minutes, heure locale − TU, à cet instant (heure d'été comprise)
    decalage_standard: int  # minutes, hors heure d'été (méridien du fuseau)
    local: tuple            # (année, mois, jour, heure, minute, seconde)
    tu: tuple               # idem en TU
    jj: float               # jour julien (TU)


def jour_julien_ms(ms: float) -> float:
    return ms / 86_400_000.0 + 2_440_587.5


def _parties(ms: int, tz: str) -> tuple:
    if tz == LOCAL:
        d = datetime.fromtimestamp(math.floor(ms / 1000), tz=timezone.utc).astimezone()
    else:
        d = datetime.fromtimestamp(math.floor(ms / 1000), tz=_zone(tz) or timezone.utc)
    return (d.year, d.month, d.day, d.hour, d.minute, d.second)


def decalage_minutes(ms: int, tz: str) -> int:
    a, mo, j, h, mi, s = _parties(ms, tz)
    loc = datetime(a, mo, j, h, mi, s, tzinfo=timezone.utc).timestamp() * 1000
    return round((loc - math.floor(ms / 1000) * 1000) / 60000)


def decalage_standard(ms: int, tz: str) -> int:
    """Décalage hors heure d'été : le plus petit des décalages du 1er janvier et du 1er juillet de l'année."""
    an = _parties(ms, 'UTC')[0]
    j = int(datetime(an, 1, 1, 12, tzinfo=timezone.utc).timestamp() * 1000)
    k = int(datetime(an, 7, 1, 12, tzinfo=timezone.utc).timestamp() * 1000)
    return min(decalage_minutes(j, tz), decalage_minutes(k, tz))


def instant(ms: int, tz: str) -> Instant:
    if tz != LOCAL and _zone(tz) is None:
        tz = 'UTC'
    return Instant(ms=ms, tz=tz, decalage=decalage_minutes(ms, tz), decalage_standard=decalage_standard(ms, tz),
                   local=_parties(ms, tz), tu=_parties(ms, 'UTC'), jj=jour_julien_ms(ms))


@dataclass
class Moment:
    """Ce que reçoit une animation : l'instant, la longitude retenue pour l'heure solaire (« Ma position » si elle a
    été choisie, sinon méridien du fuseau) et la latitude de « Ma position » (None sinon : la position réglée reste)."""
    i: Instant
    lon: float
    lat: float | None
    position: bool


def moment(i: Instant, position: tuple | None = None) -> Moment:
    if position:
        return Moment(i, position[1], position[0], True)
    return Moment(i, meridien_du_fuseau(i), None, False)


def maintenant() -> Instant:
    return instant(int(datetime.now(timezone.utc).timestamp() * 1000), fuseau_local())


# ------------------------------------------------------------------ jours, heures
def jour_index(mois: int, jour: int) -> int:
    """Indice 0–364 (année de 365 jours ; 29 février → 28 février)."""
    return sum(MOIS_JOURS[:mois - 1]) + min(jour, MOIS_JOURS[mois - 1]) - 1


def heure_decimale(p: tuple) -> float:
    return p[3] + p[4] / 60.0 + p[5] / 3600.0


def jour_tu(i: Instant) -> float:
    """Jour (indice) + fraction du jour en TU (jour-nuit)."""
    return jour_index(i.tu[1], i.tu[2]) + heure_decimale(i.tu) / 24.0


def heure_solaire(i: Instant, longitude: float) -> tuple:
    """(indice du jour, heure solaire moyenne en heures) à la longitude (degrés, est positive)."""
    ms = i.ms + round(longitude / 15.0 * 3_600_000)
    p = _parties(ms, 'UTC')
    return jour_index(p[1], p[2]), heure_decimale(p)


def meridien_du_fuseau(i: Instant) -> float:
    return i.decalage_standard / 4.0          # minutes → degrés (15° par heure)


def tsl_heures(jj: float, longitude: float) -> float:
    """Temps sidéral local (heures) : TSMG (IAU 1982, Meeus 12.4) + longitude."""
    t = (jj - 2_451_545.0) / 36_525.0
    g = 280.460_618_37 + 360.985_647_366_29 * (jj - 2_451_545.0) + 0.000_387_933 * t * t - t ** 3 / 38_710_000.0
    return ((g + longitude) % 360.0 + 360.0) % 360.0 / 15.0


def annee_decimale(i: Instant) -> float:
    a = i.tu[0]
    d0 = datetime(a, 1, 1, tzinfo=timezone.utc).timestamp() * 1000
    d1 = datetime(a + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000
    return a + (i.ms - d0) / (d1 - d0)


def elongation_lune(jj: float) -> float:
    """Élongation de la Lune (degrés, 0 = nouvelle lune, 180 = pleine lune) : longitudes moyennes et principaux termes
    périodiques (Meeus, chap. 47 et 25, précision ≈ 0,3°)."""
    t = (jj - 2_451_545.0) / 36_525.0
    r = math.pi / 180.0
    lp = 218.316_447_7 + 481_267.881_234_21 * t
    d = 297.850_192_1 + 445_267.111_403_4 * t
    m = 357.529_109_2 + 35_999.050_290_9 * t
    mp = 134.963_396_4 + 477_198.867_505_5 * t
    f = 93.272_095_0 + 483_202.017_523_3 * t
    lune = lp + 6.288_774 * math.sin(mp * r) + 1.274_027 * math.sin((2 * d - mp) * r) + 0.658_314 * math.sin(2 * d * r) \
        + 0.213_618 * math.sin(2 * mp * r) - 0.185_116 * math.sin(m * r) - 0.114_332 * math.sin(2 * f * r) \
        + 0.058_793 * math.sin((2 * d - 2 * mp) * r) + 0.057_066 * math.sin((2 * d - m - mp) * r) \
        + 0.053_322 * math.sin((2 * d + mp) * r) + 0.045_758 * math.sin((2 * d - m) * r)
    l0 = 280.466_46 + 36_000.769_83 * t
    c = (1.914_602 - 0.004_817 * t) * math.sin(m * r) + 0.019_993 * math.sin(2 * m * r) + 0.000_289 * math.sin(3 * m * r)
    soleil = l0 + c
    return ((lune - soleil) % 360.0 + 360.0) % 360.0


# ------------------------------------------------------------------ textes
def libelle_decalage(minutes: int) -> str:
    """« UTC », « UTC+2 », « UTC+5:45 », « UTC−2:30 » (signe moins typographique)."""
    if minutes == 0:
        return 'UTC'
    s = '+' if minutes > 0 else '−'
    h, m = divmod(abs(minutes), 60)
    return 'UTC' + s + str(h) + (':%02d' % m if m else '')


def ville(tz: str) -> str:
    return tz.split('/')[-1].replace('_', ' ')


def hm(p: tuple) -> str:
    return '%02d:%02d' % (p[3], p[4])


def texte_heure(i: Instant, lg: str) -> str:
    """« 09:20 heure de Paris (UTC+2) · 07:20 TU » ; « 09:20 Paris time (UTC+2) · 07:20 UT »."""
    if i.tz in ('UTC', 'Etc/UTC', 'Etc/GMT'):
        return ('%s TU' if lg == 'fr' else '%s UT') % hm(i.tu)
    if i.tz == LOCAL:
        lieu = 'heure locale' if lg == 'fr' else 'local time'
    else:
        v = ville(i.tz)
        lieu = (('heure d’' if v[:1] in 'AEIOUYÉÈÎÔÂ' else 'heure de ') + v) if lg == 'fr' else v + ' time'
    return '%s %s (%s) · %s %s' % (hm(i.local), lieu, libelle_decalage(i.decalage), hm(i.tu), 'TU' if lg == 'fr' else 'UT')


def texte_date(i: Instant, lg: str) -> str:
    """Date locale : « 25 octobre 2026 » ; « October 25, 2026 »."""
    mois_fr = ('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre')
    mois_en = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')
    a, m, j = i.local[:3]
    return ('%d %s %d' % (j, mois_fr[m - 1], a)) if lg == 'fr' else ('%s %d, %d' % (mois_en[m - 1], j, a))
