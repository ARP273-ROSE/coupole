"""Petits calculs de géométrie sphérique, dates et site (repris de ohp_xisf.py)."""
from __future__ import annotations

import datetime as D
import math

import numpy as np

# Minor Planet Center, liste des codes d'observatoire, code 511 « Haute Provence » :
# longitude 5,7157° E, rho cos(phi') = 0,72140, rho sin(phi') = +0,69034.
MPC511 = (5.7157, 0.72140, 0.69034)


def utc(mjd: float) -> D.datetime:
    return D.datetime(1858, 11, 17) + D.timedelta(days=mjd)


def nuit(mjd: float) -> D.date:
    """Date du soir de la nuit (UTC − 12 h) : une nuit = une date, même après minuit."""
    return (utc(mjd) - D.timedelta(hours=12)).date()


def site_geodesique(lon=MPC511[0], rc=MPC511[1], rs=MPC511[2]):
    """Coordonnées géocentriques du MPC → latitude, longitude, hauteur ellipsoïdale WGS 84."""
    a, f = 6378137.0, 1 / 298.257223563
    e2 = f * (2 - f)
    p, z = rc * a, rs * a
    lat = math.atan2(z, p * (1 - e2))
    h = 0.0
    for _ in range(20):
        N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        h = p / math.cos(lat) - N
        lat = math.atan2(z, p * (1 - e2 * N / (N + h)))
    return math.degrees(lat), lon, h


SITE_LAT, SITE_LON, SITE_H = site_geodesique()


def sexa(v, heures=False, signe=True, dec=1) -> str:
    s = '-' if v < 0 else '+'
    v = abs(v) / (15 if heures else 1)
    d = int(v)
    m = int((v - d) * 60)
    sec = ((v - d) * 60 - m) * 60
    if round(sec, dec) >= 60:
        sec = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    fmt = '%02d %02d %0' + str(2 if dec == 0 else 3 + dec) + '.' + str(dec) + 'f'
    return (s if signe else '') + fmt % (d, m, sec)


def parse_sexa(s):
    try:
        t = s.replace(':', ' ').split()
        sg = -1 if t[0].startswith('-') else 1
        v = [abs(float(u)) for u in t]
        return sg * (v[0] + (v[1] if len(v) > 1 else 0) / 60 + (v[2] if len(v) > 2 else 0) / 3600)
    except Exception:
        return None


def sep_deg(ra1, de1, ra2, de2) -> float:
    r = math.radians
    a = math.sin(r(de1 - de2) / 2) ** 2 + math.cos(r(de1)) * math.cos(r(de2)) * math.sin(r(ra1 - ra2) / 2) ** 2
    return math.degrees(2 * math.asin(min(1, math.sqrt(a))))


def cap(ra1, de1, ra2, de2) -> float:
    """Angle de position (E depuis N) du point 2 vu du point 1, en degrés [0, 360)."""
    r = math.radians
    da = r(ra2 - ra1)
    y = math.sin(da) * math.cos(r(de2))
    x = math.cos(r(de1)) * math.sin(r(de2)) - math.sin(r(de1)) * math.cos(r(de2)) * math.cos(da)
    return math.degrees(math.atan2(y, x)) % 360


def ecart_angle(a, b) -> float:
    """Écart d'angle de position modulo 180° (un retournement au méridien reste empilable)."""
    d = abs((a - b) % 360)
    d = min(d, 360 - d)
    return min(d, abs(180 - d))


def mediane_angle(v):
    if not v:
        return None
    ref = v[0]
    w = [ref + (((a - ref) + 90) % 180 - 90) for a in v]
    return float(np.median(w)) % 360
