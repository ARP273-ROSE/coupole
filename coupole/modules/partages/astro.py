"""Géométrie terrestre et céleste commune aux outils d'analyse des partages (sans skyfield).

* Échelles de temps et rotation de la Terre : ERFA (fourni avec astropy), modèle IAU 2006/2000A
  (``erfa.c2t06a`` : matrice GCRS → ITRS, sans mouvement du pôle, comme skyfield par défaut) ; UT1 − UTC tiré des
  tables IERS livrées avec astropy (aucun téléchargement : ``auto_download`` coupé), 0 à défaut (écart dit).
* Ellipsoïde WGS84 (``erfa.gd2gc`` / ``gc2gd``).
* Position de la Lune : éphéméride **JPL DE440** (fichier ``de440s.bsp`` lu par jplephem, si les deux sont
  présents), sinon l'approximation de Meeus (``erfa.moon98`` : 2,9″ et 6,1 km d'écart quadratique moyen d'après
  la documentation d'ERFA) — la source employée est toujours rendue avec le résultat.
* Réfraction atmosphérique (formule de Bennett, 1982), pour des hauteurs MESURÉES sur l'horizon.
"""
from __future__ import annotations

import datetime as D
import math
import os
import threading
from pathlib import Path

import numpy as np

UA_KM = 149597870.700
C_KM_S = 299792.458
R_LUNE_KM = 1737.4
UTC = D.timezone.utc
_verrou = threading.Lock()


# ============================================================================================== temps
class Instant:
    """Un instant UTC, avec ses dates juliennes TT et UT1 (deux parties, comme ERFA)."""

    def __init__(self, dt: D.datetime):
        import erfa
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        dt = dt.astimezone(UTC)
        self.dt = dt
        s = dt.second + dt.microsecond / 1e6
        self.utc1, self.utc2 = erfa.dtf2d('UTC', dt.year, dt.month, dt.day, dt.hour, dt.minute, s)
        tai1, tai2 = erfa.utctai(self.utc1, self.utc2)
        self.tt1, self.tt2 = erfa.taitt(tai1, tai2)
        self.dut1, self.dut1_source = dut1(dt)
        self.ut11, self.ut12 = erfa.utcut1(self.utc1, self.utc2, self.dut1)

    @property
    def jd_tt(self) -> float:
        return self.tt1 + self.tt2

    def plus(self, secondes: float) -> 'Instant':
        return Instant(self.dt + D.timedelta(seconds=secondes))

    def __sub__(self, autre: 'Instant') -> float:
        return (self.dt - autre.dt).total_seconds()


_dut1_cache: dict = {}


def dut1(dt: D.datetime) -> tuple[float, str]:
    """UT1 − UTC (s) d'après les tables IERS livrées avec astropy (aucun téléchargement) ; (0, 'zero') à défaut."""
    cle = dt.date()
    with _verrou:
        if cle in _dut1_cache:
            return _dut1_cache[cle]
    val = (0.0, 'zero')
    try:
        import warnings
        from astropy.time import Time
        from astropy.utils import iers
        iers.conf.auto_download = False
        iers.conf.auto_max_age = None
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            t = Time(dt.replace(tzinfo=None, hour=12, minute=0, second=0, microsecond=0), scale='utc')
            d, statut = t.get_delta_ut1_utc(return_status=True)
            if int(statut) >= 0 or int(statut) == -2:          # dans la table ou prédiction de l'IERS
                val = (float(d.to_value('s')), 'iers')
    except Exception:
        pass
    with _verrou:
        _dut1_cache[cle] = val
    return val


# ============================================================================================== repères
def c2t(t: Instant) -> np.ndarray:
    """Matrice GCRS → ITRS (IAU 2006/2000A, sans mouvement du pôle)."""
    import erfa
    return np.asarray(erfa.c2t06a(t.tt1, t.tt2, t.ut11, t.ut12, 0.0, 0.0))


def ecef(lat_deg: float, lon_deg: float, alt_m: float = 0.0) -> np.ndarray:
    """Coordonnées géodésiques WGS84 → vecteur terrestre (ITRS), en km."""
    import erfa
    return np.asarray(erfa.gd2gc(1, math.radians(lon_deg), math.radians(lat_deg), float(alt_m))) / 1000.0


def geodesique(xyz_km) -> tuple[float, float, float]:
    """Vecteur terrestre (km) → (latitude °, longitude °, hauteur au-dessus de l'ellipsoïde en km)."""
    import erfa
    lon, lat, h = erfa.gc2gd(1, np.asarray(xyz_km, float) * 1000.0)
    return math.degrees(lat), math.degrees(lon), h / 1000.0


def enu(lat_deg: float, lon_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vecteurs unitaires Est, Nord, Zénith (normale à l'ellipsoïde) dans le repère terrestre."""
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    E = np.array([-math.sin(lo), math.cos(lo), 0.0])
    N = np.array([-math.sin(la) * math.cos(lo), -math.sin(la) * math.sin(lo), math.cos(la)])
    Z = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
    return E, N, Z


def unitaire(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def vecteur_radec(ra_deg: float, dec_deg: float) -> np.ndarray:
    a, d = math.radians(ra_deg), math.radians(dec_deg)
    return np.array([math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)])


def radec(v) -> tuple[float, float]:
    v = unitaire(v)
    return math.degrees(math.atan2(v[1], v[0])) % 360.0, math.degrees(math.asin(max(-1.0, min(1.0, v[2]))))


def vecteur_altaz(lat_deg: float, lon_deg: float, h_deg: float, az_deg: float) -> np.ndarray:
    """Direction (repère terrestre) d'une hauteur et d'un azimut (compté du nord vers l'est)."""
    E, N, Z = enu(lat_deg, lon_deg)
    h, A = math.radians(h_deg), math.radians(az_deg)
    return math.cos(h) * math.sin(A) * E + math.cos(h) * math.cos(A) * N + math.sin(h) * Z


def altaz(lat_deg: float, lon_deg: float, v_terrestre) -> tuple[float, float]:
    """Hauteur et azimut (°) d'une direction donnée dans le repère terrestre."""
    E, N, Z = enu(lat_deg, lon_deg)
    u = unitaire(v_terrestre)
    return (math.degrees(math.asin(max(-1.0, min(1.0, u @ Z)))),
            math.degrees(math.atan2(u @ E, u @ N)) % 360.0)


def separation_deg(u, v) -> float:
    u, v = unitaire(u), unitaire(v)
    return math.degrees(2 * math.asin(min(1.0, np.linalg.norm(u - v) / 2)))


def trianguler(O1, u1, O2, u2):
    """Point le plus proche de deux droites O1 + d1 u1 et O2 + d2 u2 (moindres carrés).
    Rend (milieu, d1, d2, écart entre les droites)."""
    u1, u2 = unitaire(u1), unitaire(u2)
    w, c = np.asarray(O2, float) - np.asarray(O1, float), float(u1 @ u2)
    d1, d2 = np.linalg.solve([[1.0, -c], [c, -1.0]], [w @ u1, w @ u2])
    P1, P2 = O1 + d1 * u1, O2 + d2 * u2
    return (P1 + P2) / 2, float(d1), float(d2), float(np.linalg.norm(P1 - P2))


# ============================================================================================== réfraction
def refraction_bennett(h_apparente_deg: float, pression_hpa: float = 1010.0, temperature_c: float = 10.0) -> float:
    """Réfraction (degrés) pour une hauteur APPARENTE (mesurée) : formule de Bennett (1982), corrigée de la pression
    et de la température ; ≈ 34′ à l'horizon, 1′ à 45°.  Hauteur vraie = apparente − réfraction."""
    h = max(-1.0, float(h_apparente_deg))
    r_arcmin = 1.0 / math.tan(math.radians(h + 7.31 / (h + 4.4)))
    r_arcmin *= (pression_hpa / 1010.0) * (283.0 / (273.0 + temperature_c))
    return max(0.0, r_arcmin) / 60.0


def refraction_vraie(h_vraie_deg: float, pression_hpa: float = 1010.0, temperature_c: float = 10.0) -> float:
    """Réfraction (degrés) pour une hauteur VRAIE (Saemundsson, 1986) : apparente = vraie + réfraction."""
    h = max(-1.0, float(h_vraie_deg))
    r_arcmin = 1.02 / math.tan(math.radians(h + 10.3 / (h + 5.11)))
    r_arcmin *= (pression_hpa / 1010.0) * (283.0 / (273.0 + temperature_c))
    return max(0.0, r_arcmin) / 60.0


# ============================================================================================== éphémérides
NOM_DE440 = 'de440s.bsp'


def dossier_ephemerides() -> Path:
    from ...core.config import dossier_cache
    p = dossier_cache() / 'ephemerides'
    p.mkdir(parents=True, exist_ok=True)
    return p


def chemin_de440() -> Path | None:
    """Fichier DE440 disponible : variable COUPOLE_DE440, puis le cache de Coupole."""
    for p in (os.environ.get('COUPOLE_DE440', ''), str(dossier_ephemerides() / NOM_DE440)):
        if p and os.path.isfile(p) and os.path.getsize(p) > 1_000_000:
            return Path(p)
    return None


def jplephem_present() -> bool:
    try:
        import jplephem  # noqa: F401
        return True
    except ImportError:
        return False


_noyau = {'chemin': None, 'spk': None}


def _spk():
    p = chemin_de440()
    if p is None or not jplephem_present():
        return None
    with _verrou:
        if _noyau['chemin'] != str(p):
            from jplephem.spk import SPK
            if _noyau['spk'] is not None:
                try:
                    _noyau['spk'].close()
                except Exception:
                    pass
            _noyau['spk'] = SPK.open(str(p))
            _noyau['chemin'] = str(p)
        return _noyau['spk']


def source_ephemeride() -> str:
    """'de440' ou 'meeus' : ce que `lune_geocentrique` emploiera."""
    return 'de440' if _spk() is not None else 'meeus'


def lune_geocentrique(t: Instant, forcer: str = '') -> tuple[np.ndarray, str]:
    """Position géométrique de la Lune par rapport au centre de la Terre (km, axes ICRS/GCRS) à l'instant TT de t."""
    spk = None if forcer == 'meeus' else _spk()
    if spk is not None:
        jd1, jd2 = t.tt1, t.tt2          # TDB ≈ TT à 2 ms près : 2 m de mouvement de la Lune
        lune = spk[3, 301].compute(jd1, jd2)
        terre = spk[3, 399].compute(jd1, jd2)
        return np.asarray(lune - terre, float), 'de440'
    import erfa
    pv = erfa.moon98(t.tt1, t.tt2)
    return np.asarray(pv[0], float) * UA_KM, 'meeus'


def vitesse_terre_barycentrique(t: Instant) -> np.ndarray:
    """Vitesse de la Terre par rapport au barycentre du Système solaire (km/s, axes ICRS) — ERFA epv00."""
    import erfa
    _, pvb = erfa.epv00(t.tt1, t.tt2)
    return np.asarray(pvb[1], float) * UA_KM / 86400.0


def lune_astrometrique(t: Instant, O_gcrs_km=None, forcer: str = '') -> tuple[np.ndarray, str]:
    """Vecteur observateur → Lune tel que le donne une astrométrie sur les étoiles (direction « catalogue ») :
    Lune à l'instant d'émission (temps de lumière) moins l'observateur à l'instant de réception, déplacement de la
    Terre pendant le trajet de la lumière compris (≈ 38 km).  `O_gcrs_km` : observateur (km, GCRS), centre de la
    Terre par défaut."""
    O = np.zeros(3) if O_gcrs_km is None else np.asarray(O_gcrs_km, float)
    vE = vitesse_terre_barycentrique(t)
    M, src = lune_geocentrique(t, forcer)
    for _ in range(3):
        tau = np.linalg.norm(M - O) / C_KM_S
        Me, src = lune_geocentrique(t.plus(-tau), forcer)
        M = Me - vE * tau
    return M - O, src


def observateur_gcrs(lat: float, lon: float, alt_m: float, t: Instant) -> np.ndarray:
    return c2t(t).T @ ecef(lat, lon, alt_m)


def altaz_lune(lat: float, lon: float, alt_m: float, t: Instant, refraction: bool = True,
               forcer: str = '') -> tuple[float, float, float, str]:
    """(hauteur apparente °, azimut °, distance topocentrique km, source) de la Lune vue d'un lieu."""
    R = c2t(t)
    O = R.T @ ecef(lat, lon, alt_m)
    v, src = lune_astrometrique(t, O, forcer)
    h, az = altaz(lat, lon, R @ v)
    if refraction:
        h += refraction_vraie(h)
    return h, az, float(np.linalg.norm(v)), src
