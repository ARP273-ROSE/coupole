"""Pluies de météores (TP « Observation des météores » du cours 3.2 d'astrodynamique) : calendrier des pluies pour
une année quelconque, une nuit à un lieu donné (hauteur du radiant, Soleil, Lune, taux attendu, champ à viser),
campagne d'observation (les meilleures nuits sur une période) et réduction d'une observation (ZHR, indice r).

Données : liste de travail des pluies visuelles et positions du radiant au fil de l'année du calendrier 2027 de
l'IMO (tableaux 5 et 6) ; pentes d'activité de Jenniskens (1994).  Fichier ``donnees/meteores_imo.json``.

Formules (cours de J. Vaubaillon, fiche IMO « Observation visuelle des météores ») :
  ZHR = N · r^(6,5 − LM) / (F · t_eff · sin h)      et réciproquement   n = ZHR · F · sin h / r^(6,5 − LM)
  profil d'activité ZHR(λ) = ZHR_max · 10^(−B |λ − λ_max|) (Jenniskens 1994 ; somme pondérée de deux termes pour
  les pluies à pic principal et fond) ; sans pente publiée, B est pris tel que la ZHR tombe à 1 % du maximum aux
  limites d'activité (B = 2 / |Δλ| de chaque côté) : profil indicatif.
Conditions (fiche IMO) : Soleil à plus de 12° sous l'horizon ; radiant à 20° au moins ; Lune négligeable à moins de
≈ 5 jours de la nouvelle lune (fraction éclairée ≤ 0,25), sinon sous l'horizon ; centre du champ à 50-70° de hauteur
et 20-40° du radiant.

Astronomie : Soleil ERFA epv00, Lune JPL DE440 si présent sinon ERFA moon98, repère terrestre comme le planificateur
de parallaxe (``planif._Temps``) ; longitude solaire J2000 = longitude apparente de Meeus (anim.astro.soleil) moins
la précession générale en longitude, comme Coupole Web.  Jumeau : ``src/calc/td_meteores.ts`` de Coupole Web.
"""
from __future__ import annotations

import datetime as D
import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

from ..anim import astro as A
from . import planif as P

UTC = D.timezone.utc
FICHIER = Path(__file__).with_name('donnees') / 'meteores_imo.json'
SOLEIL_MAX = -12.0                # hauteur maximale du Soleil (°) : fin du crépuscule nautique
H_RADIANT_MIN = 20.0              # en dessous, la fiche IMO déconseille l'observation
LUNE_NEGLIGEABLE = 0.25           # fraction éclairée ≈ 5 jours autour de la nouvelle lune
CHAMP_H = 60.0                    # centre du champ conseillé : 50-70° de hauteur …
CHAMP_SEP = 30.0                  # … et 20-40° du radiant
PRECESSION_DEG_SIECLE = 1.396_971_37   # précession générale en longitude (°/siècle julien)


# ================================================================================================= données
@dataclass
class Pluie:
    code: str
    nom: dict
    iau: int
    debut: str
    fin: str
    max: str | None
    lambda_max: float | None
    alpha: float
    delta: float
    v: float
    r: float
    zhr: float
    note_zhr: str = ''
    radiants: list = field(default_factory=list)
    profil: list = field(default_factory=list)

    @property
    def variable(self) -> bool:
        return self.note_zhr == 'var'


@lru_cache(maxsize=1)
def _doc() -> dict:
    return json.loads(FICHIER.read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def pluies() -> tuple:
    return tuple(Pluie(**e) for e in _doc()['pluies'])


def pluie(code: str) -> Pluie:
    for p in pluies():
        if p.code == code:
            return p
    raise KeyError(code)


def sources() -> dict:
    return dict(_doc()['source'])


# ================================================================================================= temps
def jj_de(t: D.datetime) -> float:
    return t.astimezone(UTC).timestamp() / 86400.0 + 2_440_587.5


def date_de_jj(jj: float) -> D.datetime:
    return D.datetime.fromtimestamp((jj - 2_440_587.5) * 86400.0, UTC)


def longitude_solaire(jj: float) -> float:
    """λ⊙ (°, équinoxe J2000) à la date julienne UTC jj (TT ≈ UTC + 69,184 s)."""
    jt = jj + 69.184 / 86400.0
    t = (jt - 2_451_545.0) / 36_525.0
    return (A.soleil(jt)['lambda'] - PRECESSION_DEG_SIECLE * t) % 360.0


def jj_longitude(lam: float, annee: int) -> float:
    """Instant (jj UTC) de l'année civile où λ⊙ = lam (J2000)."""
    j0 = A.jour_julien(annee, 1, 1.0)
    jj = j0 + ((lam - longitude_solaire(j0)) % 360.0) / 0.985_647
    for _ in range(6):
        d = (lam - longitude_solaire(jj) + 180.0) % 360.0 - 180.0
        jj += d / 0.985_647
        if abs(d) < 1e-7:
            break
    return jj


def _lam_date(mmjj: str, annee: int, fin_de_journee: bool = False) -> float:
    m, j = (int(x) for x in mmjj.split('-'))
    jj = A.jour_julien(annee, m, float(j)) + (1.0 if fin_de_journee else 0.0)   # « 01-00 » = 31 décembre précédent
    return longitude_solaire(jj)


@lru_cache(maxsize=None)
def _geometrie(code: str) -> dict:
    """λ du début, de la fin et du maximum ; positions tabulées du radiant en λ (tout en J2000)."""
    p = pluie(code)
    an = _doc()['annee_tableaux']
    l0, l1 = _lam_date(p.debut, an), _lam_date(p.fin, an, True)      # fin incluse
    lm = p.lambda_max if p.lambda_max is not None else None
    u = lambda lam: (lam - l0 + 30.0) % 360.0 - 30.0             # coordonnée le long de la période d'activité
    pts = sorted((u(_lam_date(d, an)), a, de) for d, a, de in p.radiants)
    if pts:                                                     # α sans saut à 0/360°
        a0 = pts[0][1]
        pts = [(x, a0 + (a - a0 + 180.0) % 360.0 - 180.0, de) for x, a, de in pts]
    return {'l0': l0, 'l1': l1, 'lm': lm, 'largeur': (l1 - l0) % 360.0,
            'um': u(lm) if lm is not None else None, 'pts': pts}


def actif(code: str, lam: float) -> bool:
    g = _geometrie(code)
    return (lam - g['l0']) % 360.0 <= g['largeur']


def radiant(code: str, lam: float) -> tuple[float, float]:
    """(α, δ) J2000 du radiant à la longitude solaire lam : interpolation (ou prolongement linéaire) du tableau 6,
    sinon la position du maximum (tableau 5)."""
    p, g = pluie(code), _geometrie(code)
    pts = g['pts']
    if not pts:
        return p.alpha, p.delta
    if len(pts) == 1:
        return pts[0][1] % 360.0, pts[0][2]
    x = (lam - g['l0'] + 30.0) % 360.0 - 30.0
    i = 0
    while i < len(pts) - 2 and x > pts[i + 1][0]:
        i += 1
    (x0, a0, d0), (x1, a1, d1) = pts[i], pts[i + 1]
    f = (x - x0) / (x1 - x0)
    return (a0 + f * (a1 - a0)) % 360.0, d0 + f * (d1 - d0)


def zhr(code: str, lam: float, zhr_max: float | None = None) -> float:
    """ZHR attendue à la longitude solaire lam (0 hors de la période d'activité)."""
    p, g = pluie(code), _geometrie(code)
    if not actif(code, lam):
        return 0.0
    zm = p.zhr if zhr_max is None else zhr_max
    if g['um'] is None:                                         # source antihélion : activité plate
        return zm
    x = (lam - g['l0'] + 30.0) % 360.0 - 30.0
    dl = x - g['um']
    if p.profil:
        tot = sum(c[0] for c in p.profil)
        return zm * sum(c[0] * 10.0 ** (-(c[1] if dl < 0 else c[2]) * abs(dl)) for c in p.profil) / tot
    cote = g['um'] if dl < 0 else g['largeur'] - g['um']        # distance du maximum à la limite de ce côté
    return zm * 10.0 ** (-2.0 * abs(dl) / max(cote, 0.5))


def pente_publiee(code: str) -> bool:
    return bool(pluie(code).profil) or _geometrie(code)['um'] is None


def taux_attendu(zhr_: float, h_radiant: float, lm: float = 6.5, f: float = 1.0, r: float = 2.5) -> float:
    """n = ZHR · F · sin h / r^(6,5 − LM) météores par heure (0 radiant couché)."""
    if h_radiant <= 0:
        return 0.0
    return zhr_ * f * math.sin(math.radians(h_radiant)) / r ** (6.5 - lm)


# ================================================================================================= calendrier
def calendrier(annee: int, site: P.Site | None = None) -> list[dict]:
    """Une ligne par pluie : début, fin, maximum de l'année (instants UTC), ZHR, r, V∞, radiant au maximum, fraction
    éclairée de la Lune au maximum, et pour un lieu la hauteur de culmination du radiant."""
    out = [dict(e) for e in _calendrier_annee(annee)]
    if site is not None:
        for e in out:
            e['culmination'] = 90.0 - abs(site.lat - e['delta'])
    return out


@lru_cache(maxsize=8)
def _calendrier_annee(annee: int) -> tuple:
    out = []
    for p in pluies():
        g = _geometrie(p.code)
        jm = jj_longitude(g['lm'], annee) if g['lm'] is not None else None
        # le maximum (à défaut, le début) tombe dans l'année demandée ; début avant, fin après.  Les limites
        # d'activité sont des dates : on donne le jour le plus proche (midi), le décalage d'une année à l'autre
        # (≈ 6 h, années bissextiles) ne fait pas changer de jour
        j0 = jj_longitude(g['l0'], annee)
        ref = jm if jm is not None else j0
        if j0 > ref:
            j0 = jj_longitude(g['l0'], annee - 1)
        j1 = jj_longitude(g['l1'], annee)
        if j1 < ref:
            j1 = jj_longitude(g['l1'], annee + 1)
        a, d = radiant(p.code, g['lm'] if g['lm'] is not None else g['l0'])
        e = {'code': p.code, 'nom': p.nom, 'iau': p.iau, 'debut': date_de_jj(j0 + 0.5), 'fin': date_de_jj(j1 - 0.5),
             'max': date_de_jj(jm) if jm is not None else None, 'lambda_max': g['lm'], 'zhr': p.zhr,
             'note_zhr': p.note_zhr, 'r': p.r, 'v': p.v, 'alpha': a, 'delta': d, 'pente': pente_publiee(p.code)}
        if jm is not None:
            e['lune'] = fraction_lune(date_de_jj(jm))
        out.append(e)
    out.sort(key=lambda e: e['max'] or e['debut'])
    return tuple(out)


# ================================================================================================= une nuit
def fraction_lune(t: D.datetime) -> float:
    T = P._Temps(t, np.array([0.0]))
    s, (l, _) = P.soleil_gcrs(T)[0], P.lune_gcrs(T)
    l = l[0]
    c = float(np.dot(s, l) / np.linalg.norm(s) / np.linalg.norm(l))
    return (1.0 - c) / 2.0


def _midi_local(site: P.Site, jour: D.date) -> D.datetime:
    """Midi solaire moyen du lieu, le jour donné : début de la « nuit du jour J au jour J+1 »."""
    return D.datetime(jour.year, jour.month, jour.day, 12, tzinfo=UTC) - D.timedelta(hours=site.lon / 15.0)


def _champ(az_r: float, h_r: float, az_l: float | None) -> tuple[float, float] | None:
    """Centre du champ conseillé (az, h) : hauteur CHAMP_H, à ≈ CHAMP_SEP du radiant, du côté opposé à la Lune."""
    if h_r < H_RADIANT_MIN:
        return None
    hr, hc = math.radians(h_r), math.radians(CHAMP_H)
    c = (math.cos(math.radians(CHAMP_SEP)) - math.sin(hr) * math.sin(hc)) / (math.cos(hr) * math.cos(hc))
    daz = math.degrees(math.acos(max(-1.0, min(1.0, c))))
    cands = [(az_r + daz) % 360.0, (az_r - daz) % 360.0]
    if az_l is not None:
        cands.sort(key=lambda a: -abs((a - az_l + 180.0) % 360.0 - 180.0))
    return cands[0], CHAMP_H


@dataclass
class Nuit:
    debut: D.datetime                    # midi local (UTC)
    pas_s: float
    soleil: np.ndarray                   # hauteurs (°)
    lune: np.ndarray
    lune_az: np.ndarray
    lune_frac: float                     # fraction éclairée au milieu de la nuit
    nuit: tuple | None                   # (i0, i1) Soleil < −12° (première plage), None si jamais
    pluies: list                         # dicts par pluie active

    def instant(self, i: int) -> D.datetime:
        return self.debut + D.timedelta(seconds=i * self.pas_s)


def nuit(site: P.Site, jour: D.date, lm: float = 6.0, f: float = 1.0, codes=None, pas_min: float = 5.0,
         zhr_force: dict | None = None) -> Nuit:
    """Nuit du jour J au jour J+1 (de midi à midi, heure solaire du lieu).  Pour chaque pluie active (ou chaque code
    demandé) : hauteur et azimut du radiant, ZHR et taux attendu à chaque pas, nombre attendu pendant le temps
    utile (Soleil < −12°, radiant ≥ 20°, Lune négligeable ou couchée), meilleur instant et champ conseillé."""
    zhr_force = zhr_force or {}
    t0 = _midi_local(site, jour)
    n = int(round(24 * 60 / pas_min)) + 1
    s = np.arange(n) * pas_min * 60.0
    T = P._Temps(t0, s)
    O = P._ecef(site)
    hs, _, _ = P._hauteur_az(site, T.vers_terre(P.soleil_gcrs(T)) - O)
    lg, _ = P.lune_gcrs(T)
    hl, azl, _ = P._hauteur_az(site, T.vers_terre(lg) - O)
    sm, lm_ = P.soleil_gcrs(T)[n // 2], lg[n // 2]
    frac = float((1.0 - np.dot(sm, lm_) / np.linalg.norm(sm) / np.linalg.norm(lm_)) / 2.0)
    noir = hs < SOLEIL_MAX
    plages = P._plages(noir)
    lune_ok = (hl < 0) | (frac <= LUNE_NEGLIGEABLE)
    jj0 = jj_de(t0)
    lam = np.array([longitude_solaire(jj0 + x / 86400.0) for x in (0.0, s[-1])])
    lam_t = lam[0] + ((lam[1] - lam[0]) % 360.0) * s / s[-1]
    out = []
    for p in pluies():
        if codes is not None and p.code not in codes:
            continue
        lmid = float(lam_t[n // 2] % 360.0)
        if codes is None and not actif(p.code, lmid):
            continue
        zm = zhr_force.get(p.code)
        a, d = radiant(p.code, lmid)
        u = np.array([math.cos(math.radians(d)) * math.cos(math.radians(a)),
                      math.cos(math.radians(d)) * math.sin(math.radians(a)), math.sin(math.radians(d))])
        hr, azr, _ = P._hauteur_az(site, T.vers_terre(np.tile(u, (n, 1))))
        z = np.array([zhr(p.code, float(x) % 360.0, zm) for x in lam_t])
        taux = z * f * np.sin(np.radians(np.clip(hr, 0, None))) / p.r ** (6.5 - lm)
        utile = noir & (hr >= H_RADIANT_MIN) & lune_ok
        heures = float(utile.sum()) * pas_min / 60.0
        attendu = float((taux * utile).sum()) * pas_min / 60.0
        e = {'code': p.code, 'nom': p.nom, 'alpha': a, 'delta': d, 'h': hr, 'az': azr, 'zhr': z, 'taux': taux,
             'utile': utile, 'heures': heures, 'attendu': attendu, 'r': p.r, 'variable': p.variable and zm is None,
             'meilleur': None, 'champ': None}
        if utile.any():
            i = int(np.argmax(np.where(utile, taux, -1.0)))
            e['meilleur'] = i
            e['champ'] = _champ(float(azr[i]), float(hr[i]), float(azl[i]) if hl[i] > 0 else None)
        out.append(e)
    out.sort(key=lambda e: -e['attendu'])
    return Nuit(t0, pas_min * 60.0, hs, hl, azl, frac, plages[0] if plages else None, out)


# ================================================================================================= campagne
def campagne(site: P.Site, debut: D.date, fin: D.date, lm: float = 6.0, f: float = 1.0, min_attendu: float = 5.0,
             codes=None, zhr_force: dict | None = None) -> list[dict]:
    """Les nuits de la période où une pluie donne au moins ``min_attendu`` météores attendus pendant le temps utile :
    une ligne par (nuit, pluie), triée par date ; la note (0-100) classe les nuits entre elles."""
    out = []
    j = debut
    while j <= fin:
        N = nuit(site, j, lm, f, codes=codes, pas_min=10.0, zhr_force=zhr_force)
        for e in N.pluies:
            if e['attendu'] >= min_attendu and e['meilleur'] is not None:
                i = e['meilleur']
                out.append({'nuit': j, 'code': e['code'], 'nom': e['nom'], 'attendu': e['attendu'],
                            'heures': e['heures'], 'meilleur': N.instant(i), 'taux_max': float(e['taux'][i]),
                            'h_radiant': float(e['h'][i]), 'zhr': float(e['zhr'][i]), 'lune': N.lune_frac,
                            'lune_levee': bool(N.lune[i] > 0), 'champ': e['champ']})
        j += D.timedelta(days=1)
    if out:
        m = max(x['attendu'] for x in out)
        for x in out:
            x['note'] = round(100.0 * math.log1p(x['attendu']) / math.log1p(m))
    return out


def csv(lignes: list[dict], heure_locale: bool = False) -> str:
    def t(x):
        x = x.astimezone() if heure_locale else x.astimezone(UTC)
        return x.strftime('%Y-%m-%d %H:%M') + ('' if heure_locale else ' UTC')
    L = ['nuit;code;pluie;attendus;heures_utiles;meilleur;taux_max_par_h;h_radiant_deg;zhr;lune_pct;note']
    for x in lignes:
        L.append(';'.join((x['nuit'].isoformat(), x['code'], x['nom']['fr'], '%.0f' % x['attendu'],
                           '%.1f' % x['heures'], t(x['meilleur']), '%.0f' % x['taux_max'], '%.0f' % x['h_radiant'],
                           '%.0f' % x['zhr'], '%.0f' % (100 * x['lune']), '%d' % x['note'])))
    return '\n'.join(L) + '\n'


def ics(lignes: list[dict], site_nom: str = '') -> str:
    def f(t):
        return t.astimezone(UTC).strftime('%Y%m%dT%H%M%SZ')
    L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Coupole//Meteores//FR', 'CALSCALE:GREGORIAN']
    for x in lignes:
        t = x['meilleur']
        L += ['BEGIN:VEVENT', 'UID:%s-%s@coupole' % (x['code'], f(t)), 'DTSTAMP:' + f(D.datetime.now(UTC)),
              'DTSTART:' + f(t - D.timedelta(hours=1)), 'DTEND:' + f(t + D.timedelta(hours=1)),
              'SUMMARY:%s (%d attendus)' % (x['nom']['fr'], round(x['attendu'])),
              'DESCRIPTION:%s ZHR %.0f, radiant %.0f°, %.0f h utiles, Lune %.0f %%' % (
                  site_nom, x['zhr'], x['h_radiant'], x['heures'], 100 * x['lune']), 'END:VEVENT']
    L.append('END:VCALENDAR')
    return '\r\n'.join(L) + '\r\n'


# ================================================================================================= réduction
def hauteur_az(site: P.Site, alpha: float, delta: float, t: D.datetime) -> tuple[float, float]:
    """(hauteur, azimut) en degrés d'une direction (α, δ) J2000 vue du lieu à l'instant t."""
    T = P._Temps(t, np.array([0.0]))
    a, d = math.radians(alpha), math.radians(delta)
    u = np.array([[math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)]])
    h, az, _ = P._hauteur_az(site, T.vers_terre(u))
    return float(h[0]), float(az[0])


def hauteur_radiant(site: P.Site, code: str, t: D.datetime) -> float:
    a, d = radiant(code, longitude_solaire(jj_de(t)))
    return hauteur_az(site, a, d, t)[0]


def reduction(n: int, t_eff: float, lm: float, f: float, r: float, h: float) -> dict:
    """ZHR = N · r^(6,5 − LM) / (F · t_eff · sin h) et son incertitude statistique ZHR/√N ; avertissements."""
    if t_eff <= 0 or f <= 0:
        raise ValueError('mt_err_entrees')
    alertes = []
    if h < H_RADIANT_MIN:
        alertes.append('mt_alerte_h')
    if f < 0.8:
        alertes.append('mt_alerte_f')
    if h <= 0:
        return {'zhr': None, 'err': None, 'facteurs': None, 'alertes': alertes}
    fac = {'temps': 1.0 / t_eff, 'champ': 1.0 / f, 'lm': r ** (6.5 - lm), 'hauteur': 1.0 / math.sin(math.radians(h))}
    z = n * fac['temps'] * fac['champ'] * fac['lm'] * fac['hauteur']
    return {'zhr': z, 'err': z / math.sqrt(n) if n > 0 else None, 'facteurs': fac, 'alertes': alertes}


def indice_population(comptes: dict, lm: float) -> dict:
    """r à partir des magnitudes notées : rapports des nombres cumulés Φ(m+1)/Φ(m) (Φ(m) : météores de magnitude
    ≤ m), comme r = N(m+1)/N(m) du cours mais moins sensible au hasard, jusqu'à m+1 ≤ LM − 1 (au-delà, les
    météores faibles manquent) et pour Φ(m) ≥ 3."""
    ms = sorted(comptes)
    if not ms:
        return {'r': None, 'rapports': []}
    cum, s = {}, 0
    for m in range(int(min(ms)), int(math.floor(lm)) + 1):
        s += comptes.get(m, 0)
        cum[m] = s
    rap = [(m, cum[m + 1] / cum[m]) for m in cum if m + 1 in cum and m + 1 <= lm - 1 and cum[m] >= 3]
    return {'r': sum(x for _, x in rap) / len(rap) if rap else None, 'rapports': rap}
