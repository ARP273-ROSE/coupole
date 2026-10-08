"""Le temps : TOUJOURS en UTC en interne ; heure locale du site et de l'utilisateur pour l'affichage.

* Lecture des en-têtes : TIMESYS, DATE-OBS (avec ou sans heure, avec ou sans
  « Z » ou décalage), MJD-OBS, JD / JD-OBS, UT / TIME-OBS / UTSTART (heure
  seule, avec la date de DATE-OBS).  Une date sans fuseau n'est jamais gardée
  comme telle : elle est interprétée en UTC (norme FITS) puis contrôlée.
* Heure locale écrite par erreur : DATE-OBS en désaccord avec MJD-OBS/JD d'un
  nombre entier d'heures égal au décalage du fuseau du site, ou observation de
  nuit dont l'heure, lue en UTC, tombe en plein jour au site alors qu'elle
  tomberait de nuit une fois corrigée du décalage → signalé (jamais corrigé
  en silence).
* « Date du soir » d'une nuit : date locale du site à midi précédent (heure
  locale − 12 h), pas la date de Paris.
* Hauteur du Soleil au site (astropy), vectorisée.  Hors ligne : la table IERS
  livrée avec astropy suffit (précision bien meilleure que la minute d'arc
  nécessaire ici) ; aucun téléchargement n'est déclenché.
"""
from __future__ import annotations

import datetime as D
import re
import threading
from collections import OrderedDict

UTC = D.timezone.utc

# Cache de la hauteur du Soleil par (site, minute UTC).  Dans un processus de conversion, le contrôle « heure locale
# écrite par erreur » demande deux hauteurs par image (≈ 25 ms d'astropy) ; les poses d'une même minute (séries
# courtes d'un objet mobile) partagent le calcul.  Un cache par processus suffit (les conversions sont des processus
# séparés) ; le verrou protège les fils d'un même processus.  Le Soleil bouge de 0,25°/min au plus : deux instants
# de la même minute reçoivent la valeur du premier calculé, sans conséquence sur un test de seuil à 0° ou −12°.
_CACHE_SOLEIL_MAX = 4096
_cache_soleil: OrderedDict = OrderedDict()
_cache_soleil_verrou = threading.Lock()
_cache_soleil_stats = {'calculs': 0, 'reutilisations': 0}


def _astropy_hors_ligne():
    try:
        from astropy.utils import iers
        iers.conf.auto_download = False
        iers.conf.auto_max_age = None
    except Exception:
        pass


def iso_vers_utc(texte: str, timesys: str = 'UTC') -> D.datetime | None:
    """Date ISO 8601 → datetime UTC (aware).  Un décalage explicite est respecté ; sinon UTC (norme FITS)."""
    if not texte:
        return None
    t = texte.strip().replace(' ', 'T')
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})(?:T(\d{1,2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?)?\s*(Z|[+-]\d{2}:?\d{2})?$', t)
    if not m:
        return None
    a, mo, j, h, mi, s, frac, tz = m.groups()
    us = int((frac or '0')[:6].ljust(6, '0'))
    dt = D.datetime(int(a), int(mo), int(j), int(h or 0), int(mi or 0), int(s or 0), us)
    if tz and tz != 'Z':
        sg = 1 if tz[0] == '+' else -1
        hh, mm = int(tz[1:3]), int(tz[-2:])
        dt = dt - sg * D.timedelta(hours=hh, minutes=mm)
    dt = dt.replace(tzinfo=UTC)
    ts = (timesys or 'UTC').upper()
    if ts in ('TT', 'TAI', 'TDB', 'GPS'):
        _astropy_hors_ligne()
        from astropy.time import Time
        dt = Time(dt.replace(tzinfo=None), scale=ts.lower()).utc.to_datetime().replace(tzinfo=UTC)
    return dt


def mjd_vers_utc(mjd: float) -> D.datetime:
    return (D.datetime(1858, 11, 17) + D.timedelta(days=float(mjd))).replace(tzinfo=UTC)


def utc_vers_mjd(dt: D.datetime) -> float:
    if dt.tzinfo is None:
        raise ValueError('naive datetime refused')
    return (dt.astimezone(UTC).replace(tzinfo=None) - D.datetime(1858, 11, 17)).total_seconds() / 86400


def lire_temps(entete: dict) -> dict:
    """entete : {mot-clé: valeur (texte ou nombre)} → {'utc': datetime|None, 'source', 'alertes': [...]}.

    Ordre de confiance : DATE-OBS avec heure ; MJD-OBS ; JD ; DATE-OBS (date seule) + UT/TIME-OBS.
    """
    g = {k.upper(): v for k, v in entete.items()}
    ts = str(g.get('TIMESYS') or 'UTC').strip("' ").upper()
    alertes = []
    candidats = []
    d_obs = str(g.get('DATE-OBS') or '').strip("' ")
    if d_obs and 'T' in d_obs.replace(' ', 'T') and len(d_obs) > 10:
        u = iso_vers_utc(d_obs, ts)
        if u:
            candidats.append(('DATE-OBS', u))
    for cle in ('MJD-OBS', 'MJD_OBS'):
        if g.get(cle) not in (None, ''):
            try:
                candidats.append((cle, mjd_vers_utc(float(g[cle]))))
            except (TypeError, ValueError):
                pass
            break
    for cle in ('JD', 'JD-OBS', 'JD_OBS'):
        if g.get(cle) not in (None, ''):
            try:
                candidats.append((cle, mjd_vers_utc(float(g[cle]) - 2400000.5)))
            except (TypeError, ValueError):
                pass
            break
    if d_obs and len(d_obs) <= 10:
        heure = str(g.get('TIME-OBS') or g.get('UT') or g.get('UTSTART') or '').strip("' ")
        u = iso_vers_utc(d_obs + ('T' + heure if heure else ''), ts)
        if u:
            candidats.append(('DATE-OBS+UT' if heure else 'DATE-OBS(date)', u))
    if not candidats:
        return {'utc': None, 'source': '', 'alertes': ['aucune_date']}
    source, utc = candidats[0]
    for s2, u2 in candidats[1:]:
        ecart = (u2 - utc).total_seconds()
        if abs(ecart) > 2:
            alertes.append('desaccord:%s:%+.0fs' % (s2, ecart))
    return {'utc': utc, 'source': source, 'alertes': alertes, 'candidats': candidats}


def heure_locale(utc: D.datetime, site) -> D.datetime:
    if utc.tzinfo is None:
        raise ValueError('naive datetime refused')
    return utc.astimezone(site.zone())


def decalage_heures(utc: D.datetime, site) -> float:
    return heure_locale(utc, site).utcoffset().total_seconds() / 3600


def date_du_soir(utc: D.datetime, site) -> D.date:
    """Date du soir de la nuit au site : heure locale − 12 h."""
    return (heure_locale(utc, site) - D.timedelta(hours=12)).date()


def hauteur_soleil(utcs, site):
    """Hauteur du Soleil (degrés) au site, pour un ou plusieurs instants UTC (datetime aware ou MJD)."""
    _astropy_hors_ligne()
    import numpy as np
    from astropy import units as u
    from astropy.coordinates import AltAz, EarthLocation, get_body
    from astropy.time import Time
    seul = not isinstance(utcs, (list, tuple)) and not hasattr(utcs, '__len__')
    vals = [utcs] if seul else list(utcs)
    if vals and isinstance(vals[0], D.datetime):
        t = Time([v.astimezone(UTC).replace(tzinfo=None) for v in vals], scale='utc')
    else:
        t = Time(np.asarray(vals, dtype=float), format='mjd', scale='utc')
    lieu = EarthLocation.from_geodetic(site.lon * u.deg, site.lat * u.deg, site.alt * u.m)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        soleil = get_body('sun', t, lieu)
        alt = soleil.transform_to(AltAz(obstime=t, location=lieu)).alt.deg
    return float(alt[0]) if seul else alt


def _cle_soleil(utc: D.datetime, site) -> tuple:
    """Clé du cache : site (coordonnées arrondies au mètre près) et minute UTC."""
    u = utc.astimezone(UTC)
    return (round(site.lat, 5), round(site.lon, 5), round(site.alt, 0), u.year, u.month, u.day, u.hour, u.minute)


def hauteurs_soleil_cachees(utcs, site) -> list[float]:
    """Hauteurs du Soleil (degrés) aux instants `utcs` (datetime aware) au site, via le cache par (site, minute UTC).

    Les instants absents du cache sont calculés **en un seul appel** astropy (le coût est par appel, pas par instant),
    puis mémorisés.  Le calcul se fait sous le verrou : deux fils qui demandent la même minute en même temps ne
    calculent qu'une fois et reçoivent la même valeur (sans quoi chacun calculerait à son propre instant).  Borné
    (_CACHE_SOLEIL_MAX entrées, les plus anciennes sortent).
    """
    cles = [_cle_soleil(u, site) for u in utcs]
    with _cache_soleil_verrou:
        valeurs = [_cache_soleil.get(c) for c in cles]
        manquants = {}
        for u, c, v in zip(utcs, cles, valeurs):
            if v is not None:
                _cache_soleil.move_to_end(c)
            elif c not in manquants:
                manquants[c] = u
        nouveaux: dict = {}
        if manquants:
            calc = hauteur_soleil(list(manquants.values()), site)
            nouveaux = {c: float(h) for c, h in zip(manquants, calc)}
            _cache_soleil_stats['calculs'] += 1
            _cache_soleil.update(nouveaux)
            while len(_cache_soleil) > _CACHE_SOLEIL_MAX:
                _cache_soleil.popitem(last=False)
        _cache_soleil_stats['reutilisations'] += sum(1 for v in valeurs if v is not None)
        return [nouveaux[c] if v is None else v for c, v in zip(cles, valeurs)]


def vider_cache_soleil() -> None:
    with _cache_soleil_verrou:
        _cache_soleil.clear()
        _cache_soleil_stats.update(calculs=0, reutilisations=0)


def statistiques_cache_soleil() -> dict:
    with _cache_soleil_verrou:
        return dict(_cache_soleil_stats, entrees=len(_cache_soleil))


def soupcon_heure_locale(r: dict, site, nocturne: bool = True) -> str | None:
    """Indice qu'une date a été écrite en heure locale : renvoie une raison (texte technique) ou None."""
    if r.get('utc') is None:
        return None
    dec = decalage_heures(r['utc'], site)
    if abs(dec) < 0.5:
        return None
    for a in r.get('alertes', []):
        m = re.match(r'desaccord:[^:]+:([+-]\d+)s', a)
        if m and abs(abs(float(m.group(1))) / 3600 - abs(dec)) < 0.02:
            return 'ecart_fuseau:%+.1fh' % dec
    if nocturne:
        # les deux hauteurs (heure lue, heure corrigée du décalage) en un seul calcul, mis en cache par minute
        h_lue, h_corr = hauteurs_soleil_cachees([r['utc'], r['utc'] - D.timedelta(hours=dec)], site)
        if h_lue > 0 and h_corr < -12:
            return 'soleil:%.0f->%.0f' % (h_lue, h_corr)
    return None


def formater(utc: D.datetime, site=None, local_utilisateur: bool = True) -> str:
    """« 2025-07-16 22:20:23 UTC — 00:20:23 heure du site (UTC+2) [— 08:20 chez vous] »."""
    s = utc.astimezone(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
    if site is not None:
        loc = heure_locale(utc, site)
        s += ' — %s (%s)' % (loc.strftime('%Y-%m-%d %H:%M:%S'), _nom_decalage(loc))
    if local_utilisateur:
        moi = utc.astimezone()
        if site is None or moi.utcoffset() != heure_locale(utc, site).utcoffset():
            s += ' — %s (%s)' % (moi.strftime('%Y-%m-%d %H:%M:%S'), _nom_decalage(moi))
    return s


def _nom_decalage(dt: D.datetime) -> str:
    o = dt.utcoffset().total_seconds() / 3600
    return 'UTC%+g' % o if o else 'UTC'
