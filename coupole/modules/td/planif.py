"""Planificateur du TP de parallaxe : trouver les dates et heures où deux observateurs peuvent mesurer ENSEMBLE la
parallaxe de l'ISS ou de la Lune, et classer ces créneaux du plus facile au plus difficile.

Pourquoi : les retours de la promotion (forum du DU, 25/11/2026) — calculs faux quand l'ISS ne passe pas entre les deux
observateurs, manipulation très longue, TP Lune plus difficile que prévu.  Le planificateur cherche les configurations
où la démarche simple du sujet marche (objet presque dans le plan vertical des deux lieux), où les deux voient haut,
dans un ciel noir, et donne pour chaque créneau l'erreur que ferait la formule du sujet, la précision d'horloge
nécessaire, les étoiles de repère.

ISS : TLE (CelesTrak, cache du module) et SGP4, TEME → terrestre par GMST 1982 (comme le calculateur) ; Soleil : ERFA
epv00 ; ombre de la Terre cylindrique (rayon équatorial) ; magnitude : −1,8 à 1000 km, phase d'une sphère diffuse.
Lune : JPL DE440 si le fichier est là (module Partages), sinon ERFA moon98 ; repère terrestre par ERA et la matrice
GCRS → CIRS (IAU 2006/2000A) du milieu de la période (la variation de cette matrice sur quelques semaines est de
l'ordre de la seconde d'arc), sans mouvement du pôle.  Étoiles : Yale Bright Star Catalogue (V ≤ 5,5).

Précision visée : celle d'un planning (quelques secondes pour l'ISS, la minute pour la Lune) ; la mesure elle-même se
dépouille ensuite avec le calculateur « Parallaxe (TP du cours) », qui fait le calcul exact.
"""
from __future__ import annotations

import datetime as D
import gzip
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

UTC = D.timezone.utc
R_EQ = 6378.137                     # km
UA_KM = 149597870.7
R_LUNE = 1737.4                     # km
MAG_ISS_1000 = -1.8                 # magnitude standard de l'ISS à 1000 km, pleine phase (usage courant)
JOURS_MAX = {'iss': 14.0, 'lune': 400.0, 'tendance': 90.0}
# Dérive mesurée d'un TLE de l'ISS : ≈ 3,8 s de retard ou d'avance par jour d'âge (TLE du 15/10 et du 01/11/2026
# comparés à celui du 25/11 : 158 s à 42 j, 89 s à 24 j) ; la marge affichée en vaut le double (relèvements d'orbite).
DERIVE_TLE_S_PAR_JOUR = 3.8


class ErreurPlanif(ValueError):
    def __init__(self, cle: str, **valeurs):
        super().__init__(cle)
        self.cle, self.valeurs = cle, valeurs


@dataclass
class Site:
    lat: float
    lon: float
    alt_m: float = 0.0
    nom: str = ''


@dataclass
class Criteres:
    cible: str = 'iss'                   # 'iss' | 'lune'
    debut: D.datetime | None = None      # UTC ; maintenant par défaut
    jours: float = 7.0
    h_min: float = 20.0                  # hauteur minimale de l'objet, vue des DEUX lieux (°)
    soleil_max: float = -6.0             # hauteur maximale du Soleil aux deux lieux (°) : −6 crépuscule civil
    # Lune
    etoile_mag_max: float = 4.5          # étoile de repère au plus de cette magnitude
    etoile_sep_max: float = 5.0          # à moins de tant de degrés du centre de la Lune
    phase_max: float = 0.95              # fraction éclairée maximale
    # ISS
    pas_s: float = 0.0                   # 0 : 5 s (ISS), 300 s (Lune)
    tle: tuple | None = None
    max_resultats: int = 40
    tendance: bool = False               # ISS : jusqu'à 90 jours, heures indicatives, classement par date


@dataclass
class Creneau:
    cible: str
    debut: D.datetime
    fin: D.datetime
    meilleur: D.datetime
    note: float                          # 0 à 100
    h: list                              # hauteurs aux deux lieux au meilleur instant (°)
    az: list
    distance_km: list                    # distances topocentriques
    soleil: list                         # hauteur du Soleil aux deux lieux
    parallaxe_deg: float                 # angle entre les deux visées (la vraie parallaxe)
    ecart_plan_deg: float                # écart de l'objet au plan vertical commun des deux lieux
    entre: bool                          # ISS entre les deux lieux (chacun la voit du côté de l'autre)
    erreur_sujet_pct: float | None       # erreur relative de la formule du sujet sur la distance
    vitesse_deg_s: float                 # vitesse angulaire de l'objet sur le ciel (lieu 1)
    synchro_s: float                     # décalage d'horloge qui fausse la parallaxe de 1 %
    magnitude: list = field(default_factory=list)      # ISS
    altitude_km: float | None = None                   # ISS
    phase: float | None = None                         # Lune : fraction éclairée
    etoile: dict | None = None                         # Lune : étoile de repère {nom, V, sep1, sep2, delta}
    etoiles_proches: list = field(default_factory=list)  # ISS : étoiles brillantes près de l'ISS (lieu 1)
    trace: list = field(default_factory=list)          # [(dt, h1, az1, h2, az2)] pour le dessin
    remarques: list = field(default_factory=list)      # clés de textes
    marge_s: float = 0.0                               # ISS : incertitude sur l'heure (âge du TLE)


# ============================================================================================== outils
def _ecef(s: Site) -> np.ndarray:
    import erfa
    return np.asarray(erfa.gd2gc(1, math.radians(s.lon), math.radians(s.lat), float(s.alt_m))) / 1000.0


def _enu(s: Site):
    la, lo = math.radians(s.lat), math.radians(s.lon)
    E = np.array([-math.sin(lo), math.cos(lo), 0.0])
    N = np.array([-math.sin(la) * math.cos(lo), -math.sin(la) * math.sin(lo), math.cos(la)])
    Z = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
    return E, N, Z


def _hauteur_az(s: Site, v: np.ndarray):
    """v : vecteurs lieu → objet (n, 3), repère terrestre → (hauteur °, azimut °, distance)."""
    E, N, Z = _enu(s)
    d = np.linalg.norm(v, axis=-1)
    h = np.degrees(np.arcsin(np.clip(v @ Z / d, -1, 1)))
    az = np.degrees(np.arctan2(v @ E, v @ N)) % 360.0
    return h, az, d


class _Temps:
    """Grille de temps régulière : dates juliennes UTC, TT, UT1 (deux parties), matrices de rotation."""

    def __init__(self, debut: D.datetime, secondes: np.ndarray):
        import erfa
        from ..partages import astro
        debut = debut.astimezone(UTC)
        self.debut, self.s = debut, secondes
        u1, u2 = erfa.dtf2d('UTC', debut.year, debut.month, debut.day, debut.hour, debut.minute,
                            debut.second + debut.microsecond / 1e6)
        a1, a2 = erfa.utctai(u1, u2)
        t1, t2 = erfa.taitt(a1, a2)
        self.dut1 = astro.dut1(debut)[0]
        j = secondes / 86400.0
        self.utc1, self.utc2 = u1, u2 + j
        self.tt1, self.tt2 = t1, t2 + j
        self.ut11, self.ut12 = u1, u2 + j + self.dut1 / 86400.0
        mid = len(secondes) // 2
        self.c2i = np.asarray(erfa.c2i06a(self.tt1, self.tt2[mid]))      # GCRS → CIRS
        self.era = np.asarray(erfa.era00(self.ut11, self.ut12))

    def vers_terre(self, v_gcrs: np.ndarray) -> np.ndarray:
        """(n, 3) GCRS → (n, 3) terrestre : R3(ERA) · C2I."""
        w = v_gcrs @ self.c2i.T
        c, s = np.cos(self.era), np.sin(self.era)
        return np.stack([c * w[:, 0] + s * w[:, 1], -s * w[:, 0] + c * w[:, 1], w[:, 2]], axis=1)

    def instant(self, k: int) -> D.datetime:
        return self.debut + D.timedelta(seconds=float(self.s[k]))


def soleil_gcrs(T: _Temps) -> np.ndarray:
    import erfa
    pvh, _ = erfa.epv00(T.tt1, T.tt2)
    return -np.asarray(pvh['p']) * UA_KM


def lune_gcrs(T: _Temps) -> tuple[np.ndarray, str]:
    from ..partages import astro
    spk = astro._spk()
    if spk is not None:
        jd1 = np.full_like(T.tt2, T.tt1)
        lune = spk[3, 301].compute(jd1, T.tt2)
        terre = spk[3, 399].compute(jd1, T.tt2)
        return np.asarray(lune - terre, float).T, 'de440'
    import erfa
    pv = erfa.moon98(T.tt1, T.tt2)
    return np.asarray(pv['p']) * UA_KM, 'meeus'


_ETOILES = None


def etoiles() -> tuple[np.ndarray, np.ndarray, list]:
    """(vecteurs unitaires GCRS (n, 3), magnitudes V, désignations) des étoiles V ≤ 5,5."""
    global _ETOILES
    if _ETOILES is None:
        p = Path(__file__).with_name('donnees') / 'etoiles_v55.json.gz'
        with gzip.open(p, 'rt', encoding='utf-8') as fh:
            L = json.load(fh)['etoiles']
        ra = np.radians([e[0] for e in L])
        de = np.radians([e[1] for e in L])
        u = np.stack([np.cos(de) * np.cos(ra), np.cos(de) * np.sin(ra), np.sin(de)], axis=1)
        _ETOILES = (u, np.array([e[2] for e in L]), [e[3] for e in L])
    return _ETOILES


def _plages(masque: np.ndarray) -> list[tuple[int, int]]:
    """Indices [i, j] (inclus) des suites de True."""
    if not masque.any():
        return []
    d = np.diff(np.concatenate([[0], masque.astype(np.int8), [0]]))
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1))


def _angle(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    nu = np.linalg.norm(u, axis=-1)
    nv = np.linalg.norm(v, axis=-1)
    return np.degrees(np.arccos(np.clip(np.sum(u * v, axis=-1) / (nu * nv), -1, 1)))


def base(s1: Site, s2: Site) -> dict:
    r1, r2 = _ecef(s1), _ecef(s2)
    n = np.cross(r1, r2)
    nn = float(np.linalg.norm(n))
    return {'r1': r1, 'r2': r2, 'corde_km': float(np.linalg.norm(r2 - r1)),
            'normale': n / nn if nn > 0 else None}


def _ecart_plan(B: dict, X: np.ndarray) -> np.ndarray:
    """Angle (°) entre l'objet et le plan qui contient les deux lieux et le centre de la Terre (le plan vertical commun
    du sujet), vu du milieu de la base."""
    if B['normale'] is None:
        return np.zeros(len(X))
    m = (B['r1'] + B['r2']) / 2
    v = X - m
    return np.degrees(np.arcsin(np.clip(np.abs(v @ B['normale']) / np.linalg.norm(v, axis=-1), 0, 1)))


def erreur_sujet(B: dict, h1: float, h2: float, entre: bool, distance_vraie: float) -> float | None:
    """Erreur relative (%) de la formule du sujet (D = R / 2α, 2α = |h₁ − h₂| ou 180° − h₁ − h₂ si l'objet est entre
    les deux lieux) sur la distance au milieu de la base."""
    deux_alpha = (180.0 - h1 - h2) if entre else abs(h1 - h2)
    if deux_alpha <= 1e-6:
        return None
    D_ = B['corde_km'] / math.radians(deux_alpha)
    return 100.0 * (D_ - distance_vraie) / distance_vraie


# ============================================================================================== ISS
def magnitude_iss(d_km: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    b = np.radians(phase_deg)
    f = (np.sin(b) + (math.pi - b) * np.cos(b)) / math.pi
    return MAG_ISS_1000 + 5 * np.log10(d_km / 1000.0) - 2.5 * np.log10(np.maximum(f, 1e-4))


def _iss_terre(tle: tuple, T: _Temps) -> np.ndarray:
    import erfa
    from sgp4.api import Satrec
    l1, l2 = [x for x in tle if x.strip().startswith(('1 ', '2 '))][:2]
    sat = Satrec.twoline2rv(l1, l2)
    jd = np.full_like(T.utc2, T.utc1)
    e, r, _ = sat.sgp4_array(jd, T.utc2)
    r = np.asarray(r, float)
    r[np.asarray(e) != 0] = np.nan
    th = np.asarray(erfa.gmst82(T.ut11, T.ut12))
    c, s = np.cos(th), np.sin(th)
    return np.stack([c * r[:, 0] + s * r[:, 1], -s * r[:, 0] + c * r[:, 1], r[:, 2]], axis=1)


def _note_iss(hmin, ecart, err, par):
    """0 à 100 : les deux voient haut, objet près du plan commun (la formule du sujet marche), parallaxe nette."""
    a = np.clip((hmin - 10.0) / 50.0, 0, 1)
    b = np.exp(-(ecart / 12.0) ** 2)
    c = np.clip(par / 15.0, 0, 1)
    e = np.where(np.isnan(err), 0.3, np.exp(-(np.abs(np.nan_to_num(err)) / 15.0) ** 2))
    return 100.0 * a ** 0.7 * (0.35 + 0.65 * b) * (0.4 + 0.6 * c) * (0.5 + 0.5 * e)


def chercher_iss(s1: Site, s2: Site, c: Criteres) -> dict:
    if not c.tle:
        raise ErreurPlanif('pl_err_tle')
    from . import tle as TL
    debut = (c.debut or D.datetime.now(UTC)).astimezone(UTC)
    jours = min(max(c.jours, 0.1), JOURS_MAX['tendance' if c.tendance else 'iss'])
    pas = c.pas_s or (10.0 if c.tendance else 5.0)
    T = _Temps(debut, np.arange(0.0, jours * 86400.0, pas))
    X = _iss_terre(c.tle, T)
    sol = T.vers_terre(soleil_gcrs(T))
    us = sol / np.linalg.norm(sol, axis=1)[:, None]
    proj = np.sum(X * us, axis=1)
    eclairee = (proj > 0) | (np.linalg.norm(X - proj[:, None] * us, axis=1) > R_EQ)
    B = base(s1, s2)
    H, AZ, DI, HS, V = [], [], [], [], []
    for s in (s1, s2):
        O = _ecef(s)
        v = X - O
        h, az, d = _hauteur_az(s, v)
        hs, _, _ = _hauteur_az(s, sol - O)
        H.append(h), AZ.append(az), DI.append(d), HS.append(hs), V.append(v)
    ok = (H[0] >= c.h_min) & (H[1] >= c.h_min) & (HS[0] <= c.soleil_max) & (HS[1] <= c.soleil_max) & eclairee
    ok &= ~np.isnan(X[:, 0])
    par = _angle(V[0], V[1])
    ecart = _ecart_plan(B, X)
    E1, _, _ = _enu(s1)
    # entre : chacun voit l'ISS du côté de l'autre lieu
    w = B['r2'] - B['r1']
    entre = (V[0] @ w > 0) & (V[1] @ (-w) > 0)
    m = (B['r1'] + B['r2']) / 2
    dist_mil = np.linalg.norm(X - m, axis=1)
    err = np.full(len(X), np.nan)
    hmin = np.minimum(H[0], H[1])
    out = []
    for i, j in _plages(ok):
        k = np.arange(i, j + 1)
        for q in k:
            e = erreur_sujet(B, float(H[0][q]), float(H[1][q]), bool(entre[q]), float(dist_mil[q]))
            err[q] = np.nan if e is None else e
        note = _note_iss(hmin[k], ecart[k], err[k], par[k])
        q = int(k[np.argmax(note)])
        phase = [float(_angle((sol[q] - X[q])[None], -V[n][q][None])[0]) for n in (0, 1)]
        mag = [float(magnitude_iss(np.array([DI[n][q]]), np.array([phase[n]]))[0]) for n in (0, 1)]
        vit = float(_angle(V[0][q][None], V[0][min(q + 1, len(X) - 1)][None])[0]) / pas if q + 1 < len(X) else 0.0
        cr = Creneau('iss', T.instant(i), T.instant(j), T.instant(q), float(note.max()),
                     [float(H[0][q]), float(H[1][q])], [float(AZ[0][q]), float(AZ[1][q])],
                     [float(DI[0][q]), float(DI[1][q])], [float(HS[0][q]), float(HS[1][q])],
                     float(par[q]), float(ecart[q]), bool(entre[q]),
                     None if np.isnan(err[q]) else float(err[q]), vit,
                     0.01 * float(par[q]) / vit if vit > 0 else math.inf, mag,
                     float(np.linalg.norm(X[q]) - R_EQ))
        cr.etoiles_proches = _etoiles_pres(T, q, V[0][q], s1, 15.0, 3)
        a, b = max(i - 12, 0), min(j + 12, len(X) - 1)
        cr.trace = [(T.instant(t), float(H[0][t]), float(AZ[0][t]), float(H[1][t]), float(AZ[1][t]))
                    for t in range(a, b + 1, 2)]
        if not cr.entre and cr.ecart_plan_deg < 15:
            cr.remarques.append('pl_r_meme_cote')
        if cr.ecart_plan_deg >= 15:
            cr.remarques.append('pl_r_hors_plan')
        if max(mag) > 1.5:
            cr.remarques.append('pl_r_faible')
        ep_ = TL.epoque(c.tle)
        if ep_ is not None:
            cr.marge_s = max(30.0, 2 * DERIVE_TLE_S_PAR_JOUR * abs((cr.meilleur - ep_).total_seconds()) / 86400)
            if cr.marge_s > 120:
                cr.remarques.append('pl_r_indicatif')
        out.append(cr)
    age = None
    ep = TL.epoque(c.tle)
    if ep is not None:
        age = (debut - ep).total_seconds() / 86400.0
    return {'creneaux': out, 'base_km': B['corde_km'], 'age_tle_j': age, 'debut': debut,
            'fin': debut + D.timedelta(days=jours), 'source': 'tle'}


def _etoiles_pres(T: _Temps, q: int, v_terre: np.ndarray, s: Site, rayon: float, n: int) -> list:
    """Les n étoiles les plus brillantes à moins de `rayon` degrés de la direction v (repère terrestre, instant q),
    au-dessus de l'horizon du lieu."""
    u, V, noms = etoiles()
    c, s_ = math.cos(T.era[q]), math.sin(T.era[q])
    w = u @ T.c2i.T
    w = np.stack([c * w[:, 0] + s_ * w[:, 1], -s_ * w[:, 0] + c * w[:, 1], w[:, 2]], axis=1)
    d = v_terre / np.linalg.norm(v_terre)
    sep = np.degrees(np.arccos(np.clip(w @ d, -1, 1)))
    idx = [i for i in np.argsort(V) if sep[i] <= rayon][:n]
    return [{'nom': noms[i], 'V': float(V[i]), 'sep': float(sep[i])} for i in idx]


# ============================================================================================== Lune
def _note_lune(hmin, delta_arcmin, phase, base_km):
    a = np.clip((hmin - 5.0) / 40.0, 0, 1)
    ideal = base_km / 384400.0 * 180 / math.pi * 60          # |Δφ| maximal possible (arcmin)
    b = np.clip(delta_arcmin / max(ideal, 1e-6), 0, 1)
    c = 1.0 - 0.5 * np.clip(phase, 0, 1)
    return 100.0 * a ** 0.6 * (0.2 + 0.8 * b) * c


def chercher_lune(s1: Site, s2: Site, c: Criteres) -> dict:
    debut = (c.debut or D.datetime.now(UTC)).astimezone(UTC)
    jours = min(max(c.jours, 0.5), JOURS_MAX['lune'])
    pas = c.pas_s or 300.0
    T = _Temps(debut, np.arange(0.0, jours * 86400.0, pas))
    M, source = lune_gcrs(T)
    S = soleil_gcrs(T)
    Mt, St = T.vers_terre(M), T.vers_terre(S)
    B = base(s1, s2)
    # étoiles candidates : à moins de (sep_max + 7°) du plan de l'écliptique… plus simplement, de la trajectoire
    u, Vm, noms = etoiles()
    sel = np.flatnonzero(Vm <= c.etoile_mag_max)
    um = M / np.linalg.norm(M, axis=1)[:, None]
    sep_geo = np.degrees(np.arccos(np.clip(um @ u[sel].T, -1, 1)))      # (n_t, n_et)
    proche = sep_geo <= c.etoile_sep_max + 1.5
    H, AZ, DI, HS, VV, O = [], [], [], [], [], []
    for s in (s1, s2):
        o = _ecef(s)
        v = Mt - o
        h, az, d = _hauteur_az(s, v)
        hs, _, _ = _hauteur_az(s, St - o)
        H.append(h), AZ.append(az), DI.append(d), HS.append(hs), VV.append(v), O.append(o)
    elong = _angle(M, S)
    phase = (1 - np.cos(np.radians(elong))) / 2      # fraction éclairée : (1 + cos i) / 2, angle de phase i ≈ 180° − élongation
    ok = (H[0] >= c.h_min) & (H[1] >= c.h_min) & (HS[0] <= c.soleil_max) & (HS[1] <= c.soleil_max)
    ok &= phase <= c.phase_max
    ok &= proche.any(axis=1)
    ecart = _ecart_plan(B, Mt)
    par = _angle(VV[0], VV[1])
    out = []
    for i, j in _plages(ok):
        meilleur = None
        for q in range(i, j + 1):
            cols = np.flatnonzero(proche[q])
            if not len(cols):
                continue
            # directions des étoiles dans le repère terrestre à l'instant q
            c_, s_ = math.cos(T.era[q]), math.sin(T.era[q])
            w = u[sel[cols]] @ T.c2i.T
            w = np.stack([c_ * w[:, 0] + s_ * w[:, 1], -s_ * w[:, 0] + c_ * w[:, 1], w[:, 2]], axis=1)
            phi = [np.degrees(np.arccos(np.clip(w @ (VV[n][q] / DI[n][q]), -1, 1))) for n in (0, 1)]
            rayon = [math.degrees(math.asin(R_LUNE / DI[n][q])) for n in (0, 1)]
            bon = (phi[0] <= c.etoile_sep_max) & (phi[1] <= c.etoile_sep_max) & \
                  (phi[0] > rayon[0] + 0.1) & (phi[1] > rayon[1] + 0.1)
            if not bon.any():
                continue
            delta = np.abs(phi[0] - phi[1]) * 60.0
            # une étoile plus brillante se mesure mieux : léger bonus
            score = delta * (1.0 + 0.08 * np.clip(c.etoile_mag_max - Vm[sel[cols]], 0, 5))
            score[~bon] = -1
            b = int(np.argmax(score))
            note = float(_note_lune(min(H[0][q], H[1][q]), delta[b], phase[q], B['corde_km']))
            if meilleur is None or note > meilleur[0]:
                meilleur = (note, q, int(sel[cols[b]]), float(phi[0][b]), float(phi[1][b]), float(delta[b]))
        if meilleur is None:
            continue
        note, q, ie, p1, p2, dl = meilleur
        vit = float(_angle(VV[0][q][None], VV[0][min(q + 1, len(Mt) - 1)][None])[0]) / pas
        dist_mil = float(np.linalg.norm(Mt[q] - (B['r1'] + B['r2']) / 2))
        ideal = B['corde_km'] / dist_mil * 180 / math.pi * 60
        cr = Creneau('lune', T.instant(i), T.instant(j), T.instant(q), note,
                     [float(H[0][q]), float(H[1][q])], [float(AZ[0][q]), float(AZ[1][q])],
                     [float(DI[0][q]), float(DI[1][q])], [float(HS[0][q]), float(HS[1][q])],
                     float(par[q]), float(ecart[q]), False,
                     None, vit, math.inf)
        # la Lune ne se déplace par rapport aux étoiles qu'à ≈ 0,55″/s : la synchro est peu exigeante
        vrel = 0.55 / 3600.0
        cr.synchro_s = 0.01 * dl / 60.0 / vrel
        # erreur de la formule du sujet : D = R / Δφ au lieu de D ; Δφ < R/D quand la base n'est pas dans la direction
        # Lune–étoile → distance surestimée
        cr.erreur_sujet_pct = 100.0 * (ideal / dl - 1.0) if dl > 0 else None
        cr.phase = float(phase[q])
        cr.etoile = {'nom': noms[ie], 'V': float(Vm[ie]), 'sep1': p1, 'sep2': p2, 'delta_arcmin': dl,
                     'ideal_arcmin': ideal}
        a, b = max(i - 6, 0), min(j + 6, len(Mt) - 1)
        pas_tr = max(1, (b - a) // 60)
        cr.trace = [(T.instant(t), float(H[0][t]), float(AZ[0][t]), float(H[1][t]), float(AZ[1][t]))
                    for t in range(a, b + 1, pas_tr)]
        if dl < 0.3 * ideal:
            cr.remarques.append('pl_r_lune_faible')
        if cr.phase > 0.8:
            cr.remarques.append('pl_r_lune_pleine')
        out.append(cr)
    return {'creneaux': out, 'base_km': B['corde_km'], 'age_tle_j': None, 'debut': debut,
            'fin': debut + D.timedelta(days=jours), 'source': source}


# ============================================================================================== tout
def chercher(s1: Site, s2: Site, c: Criteres) -> dict:
    if c.cible not in ('iss', 'lune'):
        raise ErreurPlanif('pl_err_cible')
    if abs(s1.lat) > 90 or abs(s2.lat) > 90:
        raise ErreurPlanif('pl_err_lieu')
    r = chercher_iss(s1, s2, c) if c.cible == 'iss' else chercher_lune(s1, s2, c)
    if c.tendance and c.cible == 'iss':
        r['creneaux'].sort(key=lambda x: x.meilleur)
        c.max_resultats = max(c.max_resultats, 400)
    else:
        r['creneaux'].sort(key=lambda x: -x.note)
    r['nombre_total'] = len(r['creneaux'])
    r['creneaux'] = r['creneaux'][:c.max_resultats]
    r['cible'] = c.cible
    r['sites'] = [s1, s2]
    r['tendance'] = bool(c.tendance and c.cible == 'iss')
    if r['tendance']:
        r.setdefault('alertes', []).append('pl_a_tendance')
    elif c.cible == 'iss' and r['age_tle_j'] is not None and r['age_tle_j'] + c.jours > 5:
        r.setdefault('alertes', []).append('pl_a_tle_vieux')
    return r


def chercher_avec_tle(s1: Site, s2: Site, c: Criteres, reseau_permis: bool = True) -> dict:
    """ISS sans TLE fourni : TLE le plus récent (cache, sinon CelesTrak)."""
    if c.cible == 'iss' and not c.tle:
        from . import tle as TL
        info = TL.pour(c.debut or D.datetime.now(UTC), reseau_permis)
        if not info['tle']:
            raise ErreurPlanif('pl_err_tle', erreur=info.get('erreur', ''))
        c.tle = tuple(info['tle'])
    return chercher(s1, s2, c)


def csv(r: dict, heure_locale: bool = False) -> str:
    """Les créneaux en CSV (séparateur « ; », décimales à point)."""
    def t(x):
        return (x.astimezone() if heure_locale else x).strftime('%Y-%m-%d %H:%M:%S%z')
    lignes = ['cible;debut;fin;meilleur;note;h1;az1;h2;az2;d1_km;d2_km;soleil1;soleil2;parallaxe_deg;'
              'ecart_plan_deg;entre;erreur_sujet_pct;vitesse_deg_s;synchro_s;mag1;mag2;phase;etoile;V;delta_arcmin;marge_s']
    for c in r['creneaux']:
        e = c.etoile or {}
        lignes.append(';'.join(str(x) for x in (
            c.cible, t(c.debut), t(c.fin), t(c.meilleur), round(c.note, 1), round(c.h[0], 2), round(c.az[0], 2),
            round(c.h[1], 2), round(c.az[1], 2), round(c.distance_km[0], 1), round(c.distance_km[1], 1),
            round(c.soleil[0], 1), round(c.soleil[1], 1), round(c.parallaxe_deg, 4), round(c.ecart_plan_deg, 2),
            int(c.entre), '' if c.erreur_sujet_pct is None else round(c.erreur_sujet_pct, 1),
            round(c.vitesse_deg_s, 4), '' if math.isinf(c.synchro_s) else round(c.synchro_s, 3),
            *(['%.1f' % m for m in c.magnitude] if c.magnitude else ['', '']),
            '' if c.phase is None else round(c.phase, 3), e.get('nom', ''), e.get('V', ''),
            '' if not e else round(e['delta_arcmin'], 2), round(c.marge_s) if c.marge_s else '')))
    return '\n'.join(lignes) + '\n'


def ics(r: dict) -> str:
    """Les créneaux en agenda iCalendar (un événement par créneau)."""
    def f(x):
        return x.astimezone(UTC).strftime('%Y%m%dT%H%M%SZ')
    now = f(D.datetime.now(UTC))
    out = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Coupole//Planificateur parallaxe//FR']
    for k, c in enumerate(r['creneaux']):
        titre = ('Parallaxe ISS' if c.cible == 'iss' else 'Parallaxe Lune') + ' (%d/100)' % round(c.note)
        desc = 'h1 %.1f° az1 %.1f° / h2 %.1f° az2 %.1f° ; meilleur instant %s UTC' % (
            c.h[0], c.az[0], c.h[1], c.az[1], c.meilleur.astimezone(UTC).strftime('%H:%M:%S'))
        if c.marge_s > 120:
            desc += ' ; heure indicative à ± %d min' % round(c.marge_s / 60)
        if c.etoile:
            desc += ' ; étoile %s (V %.1f), Δφ %.2f′' % (c.etoile['nom'], c.etoile['V'], c.etoile['delta_arcmin'])
        out += ['BEGIN:VEVENT', 'UID:coupole-planif-%s-%d@coupole' % (f(c.meilleur), k), 'DTSTAMP:' + now,
                'DTSTART:' + f(c.debut), 'DTEND:' + f(c.fin + D.timedelta(seconds=1)), 'SUMMARY:' + titre,
                'DESCRIPTION:' + desc.replace(';', '\\;').replace(',', '\\,'), 'END:VEVENT']
    out.append('END:VCALENDAR')
    return '\r\n'.join(out) + '\r\n'
