"""Daylight Simulator : la Terre avec la zone de jour et de nuit.  Le point subsolaire est à la latitude δ☉ et à la
longitude où il est midi solaire vrai ; la zone éclairée glisse vers l'ouest au fil du jour (15° par heure) et son
contour change au fil de l'année.  Animation « jour » (l'heure avance) ou « année » (la date avance à heure fixe).

Quatre projections (mêmes choix que Coupole Web, src/anim/animations/jour_nuit.ts) :
- équirectangulaire : correspondance linéaire entre la souris et la latitude-longitude ;
- pôle Nord, pôle Sud : azimutale équidistante centrée sur le pôle (distance au pôle vraie), bord à l'équateur ou
  30° au-delà (les deux tropiques) ; vu du pôle, l'est tourne dans le sens direct.  Par défaut la Terre tourne sous un
  terminateur fixe (midi en bas au Nord, en haut au Sud) ; « Terminateur tournant » fixe la carte (Greenwich en bas
  au Nord).  Nuit et crépuscules : pour chaque méridien, la latitude exacte où h = 0 (ou −6°, −12°, −18°), bornée au
  bord : une boucle autour du pôle, sans artefact au pôle (au solstice, tangente au cercle polaire) ;
- globe 3D vu de l'espace : projection orthographique, rotation de « boule de commande » (le point saisi suit la
  souris, dans tous les sens, avec une légère inertie), molette : zoom, double-clic : face au point subsolaire, clic
  droit : placer l'observateur.  Lignes coupées au limbe au point exact de traversée ; nuit et crépuscules : parties
  visibles des calottes {p · s < −sin h}, bornées par le petit cercle et par le limbe."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, QTimer
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainterPath, QPolygonF, QRadialGradient

from ....core.i18n import tr
from .. import astro, dessin
from ..maintenant import heure_decimale, jour_index
from ..base import Animation, angle, date_du_jour, heures_minutes
from .longitude_latitude import _cotes_tout, _lire_cotes, decimal, dessiner_cotes_carte, globe_xyz

ANNEE = 2026
EPS = 23.44                                           # tropiques et cercles polaires (comme Coupole Web)
COUCHES = ((0.0, 0.55), (6.0, 0.25), (12.0, 0.2), (18.0, 0.15))


def subsolaire(jour: float) -> tuple[float, float]:
    """(latitude, longitude) du point subsolaire au « jour » (fraction = temps universel)."""
    s = astro.soleil_jour(ANNEE, jour)
    tu = (jour % 1.0) * 24.0
    lon = -((tu - 12.0) * 15.0 + s['eqt'] / 4.0)
    return s['delta'], astro.mod180(lon)


def latitude_terminateur(lon: np.ndarray, dec: float, lon_ss: float) -> np.ndarray:
    """Latitude du terminateur (h = 0) pour chaque longitude : tan φ = −cos H / tan δ."""
    h = np.radians(lon - lon_ss)
    d = math.radians(dec if abs(dec) > 1e-6 else 1e-6)
    return np.degrees(np.arctan(-np.cos(h) / math.tan(d)))


# ------------------------------------------------------------------ projection azimutale équidistante polaire
def latitude_hauteur(lon: float, dec: float, lon_ss: float, h: float) -> float:
    """Latitude où le Soleil est à la hauteur h (degrés) le long du méridien `lon`, du côté nuit du terminateur :
    a sin φ + b cos φ = sin h, avec a = sin δ, b = cos δ cos H.  Sans solution : pôle obscur."""
    hh = math.radians(lon - lon_ss)
    a, b = math.sin(math.radians(dec)), math.cos(math.radians(dec)) * math.cos(hh)
    rr = math.hypot(a, b)
    if rr < 1e-12 or abs(math.sin(math.radians(h)) / rr) > 1:
        return -90.0 if dec >= 0 else 90.0
    psi = math.atan2(b, a)
    base = math.asin(math.sin(math.radians(h)) / rr)
    sols = []
    for phi in (base - psi, math.pi - base - psi):
        phi = (phi + math.pi) % (2 * math.pi) - math.pi
        if -math.pi / 2 - 1e-9 <= phi <= math.pi / 2 + 1e-9:
            sols.append(math.degrees(phi))
    if not sols:
        return -90.0 if dec >= 0 else 90.0
    ref = float(latitude_terminateur(np.array([lon]), dec, lon_ss)[0])
    # côté nuit : vers le pôle obscur depuis le terminateur
    nuit = [x for x in sols if (x <= ref + 1e-9 if dec >= 0 else x >= ref - 1e-9)]
    return (nuit or sols)[0]




def latitudes_hauteur(lon: np.ndarray, dec: float, lon_ss: float, h: float) -> np.ndarray:
    """latitude_hauteur pour un tableau de longitudes (mêmes règles, calcul vectoriel)."""
    lon = np.asarray(lon, dtype=float)
    hh = np.radians(lon - lon_ss)
    a = math.sin(math.radians(dec))
    b = math.cos(math.radians(dec)) * np.cos(hh)
    rr = np.hypot(a, b)
    pole = -90.0 if dec >= 0 else 90.0
    sh = math.sin(math.radians(h))
    with np.errstate(divide='ignore', invalid='ignore'):
        k = sh / rr
        ok = (rr >= 1e-12) & (np.abs(k) <= 1)
        psi = np.arctan2(b, a)
        base = np.arcsin(np.clip(k, -1, 1))
    ref = latitude_terminateur(lon, dec, lon_ss)
    out = np.full(lon.shape, pole)
    choisi = np.zeros(lon.shape, dtype=bool)
    candidats = []
    for phi in (base - psi, math.pi - base - psi):
        phi = (phi + math.pi) % (2 * math.pi) - math.pi
        valide = ok & (phi >= -math.pi / 2 - 1e-9) & (phi <= math.pi / 2 + 1e-9)
        candidats.append((np.degrees(phi), valide))
    for x, valide in candidats:                       # côté nuit d'abord
        nuit = valide & ((x <= ref + 1e-9) if dec >= 0 else (x >= ref - 1e-9))
        prendre = nuit & ~choisi
        out[prendre] = x[prendre]
        choisi |= prendre
    for x, valide in candidats:
        prendre = valide & ~choisi
        out[prendre] = x[prendre]
        choisi |= prendre
    return out


# ------------------------------------------------------------------ vue polaire (azimutale équidistante)
def projeter_polaire(lat, lon, nord: bool = True, bord: float = 0.0, lon0: float = 0.0):
    """(latitude, longitude) → (u, v) dans le disque unité (bord = latitude du bord : 0 l'équateur, −30 au Nord ou
    +30 au Sud pour voir les tropiques), v vers le bas de l'écran ; le méridien lon0 est en bas (Nord) ou en haut
    (Sud), l'est tourne dans le sens direct vu du pôle."""
    pole = 1.0 if nord else -1.0
    rho = (90.0 - pole * np.asarray(lat, dtype=float)) / (90.0 - pole * bord)
    a = np.radians(np.asarray(lon, dtype=float) - lon0)
    return (rho * np.sin(a), rho * np.cos(a)) if nord else (rho * np.sin(a), -rho * np.cos(a))


def inverse_polaire(u: float, v: float, nord: bool = True, bord: float = 0.0, lon0: float = 0.0):
    """Inverse de projeter_polaire : (u, v) → (latitude, longitude) en degrés."""
    pole = 1.0 if nord else -1.0
    rho = math.hypot(u, v)
    lat = pole * (90.0 - rho * (90.0 - pole * bord))
    a = math.atan2(u, v) if nord else math.atan2(u, -v)
    return lat, astro.mod180(lon0 + math.degrees(a))


def nuit_polaire(dec: float, lon_ss: float, decalage: float, nord: bool, bord: float = 0.0, lon0: float = 0.0,
                 n: int = 721):
    """Contour d'une zone de nuit (h < −decalage) en vue polaire : boucle fermée autour du pôle (une latitude par
    méridien, bornée au bord), en coordonnées du disque unité, et `interieur` : la nuit est-elle du côté du pôle ?"""
    lons = np.linspace(-180.0, 180.0, n)
    la = latitude_terminateur(lons, dec, lon_ss) if decalage == 0 else latitudes_hauteur(lons, dec, lon_ss,
                                                                                          -decalage)
    la = np.maximum(bord, la) if nord else np.minimum(bord, la)
    u, v = projeter_polaire(la, lons, nord, bord, lon0)
    return np.stack([u, v], axis=1), (dec < 0) if nord else (dec >= 0)


def chemin_nuit_polaire(dec: float, lon_ss: float, decalage: float, nord: bool, bord: float = 0.0,
                        lon0: float = 0.0) -> QPainterPath:
    """Zone de nuit en vue polaire (disque unité ; à découper par le disque de la carte), remplissage pair-impair."""
    boucle, interieur = nuit_polaire(dec, lon_ss, decalage, nord, bord, lon0)
    ch = QPainterPath()
    ch.setFillRule(dessin.Qt.FillRule.OddEvenFill)
    ch.addPolygon(dessin.polygone(boucle[:, 0], boucle[:, 1]))
    ch.closeSubpath()
    if not interieur:
        ch.addEllipse(QPointF(0, 0), 1.02, 1.02)
    return ch


_CHEMINS_POLAIRES = {}


def chemin_cotes_polaire(nord: bool, bord: float = 0.0) -> QPainterPath:
    """Côtes en vue polaire pour lon0 = 0 (le peintre tourne ensuite de lon0), coupées hors du disque ; en cache."""
    cle = (nord, bord)
    if cle not in _CHEMINS_POLAIRES:
        ch = QPainterPath()
        for q in _lire_cotes():
            lo, la = q[:, 0], q[:, 1]
            garde = la >= bord - 1e-9 if nord else la <= bord + 1e-9
            for morceau in np.split(np.arange(len(lo)), np.flatnonzero(np.diff(garde.astype(np.int8)) != 0) + 1):
                if len(morceau) < 2 or not garde[morceau[0]]:
                    continue
                u, v = projeter_polaire(la[morceau], lo[morceau], nord, bord)
                ch.addPolygon(dessin.polygone(u, v))
        _CHEMINS_POLAIRES[cle] = ch
    return _CHEMINS_POLAIRES[cle]


# ------------------------------------------------------------------ globe 3D (orthographique)
def orientation(lat: float, lon: float) -> np.ndarray:
    """Vue centrée sur (lat, lon), nord en haut : lignes = est, nord, verticale du point central."""
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([[-math.sin(lo), math.cos(lo), 0.0],
                     [-math.sin(la) * math.cos(lo), -math.sin(la) * math.sin(lo), math.cos(la)],
                     [math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)]])


def rotation(k, t: float) -> np.ndarray:
    """Rotation d'angle t autour de l'axe unitaire k (formule de Rodrigues)."""
    x, y, z = k
    c, s = math.cos(t), math.sin(t)
    u = 1 - c
    return np.array([[c + x * x * u, x * y * u - z * s, x * z * u + y * s],
                     [y * x * u + z * s, c + y * y * u, y * z * u - x * s],
                     [z * x * u - y * s, z * y * u + x * s, c + z * z * u]])


def orthonormer(m: np.ndarray) -> np.ndarray:
    """Gram-Schmidt sur les lignes, contre la dérive des produits répétés."""
    with np.errstate(all='ignore'):
        a = m[0] / np.linalg.norm(m[0])
        b = m[1] - (m[1] @ a) * a
        b = b / np.linalg.norm(b)
    return np.vstack([a, b, np.cross(a, b)])


def tourner(m: np.ndarray, dx: float, dy: float, r: float) -> np.ndarray:
    """Glisser de (dx, dy) pixels sur un globe de rayon r : rotation « boule de commande » autour de l'axe du plan de
    l'écran perpendiculaire au glisser, d'angle |d| / r : le point sous la souris suit la souris."""
    if not (math.isfinite(dx) and math.isfinite(dy) and math.isfinite(r)):
        return m
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return m
    n = orthonormer(rotation((dy / d, dx / d, 0.0), min(d / max(1.0, r), math.pi)) @ m)
    return n if valide(n) else m


def valide(m) -> bool:
    """Une orientation utilisable : finie, orthonormée, directe (jamais d'état invalide gardé)."""
    m = np.asarray(m, dtype=float)
    return (m.shape == (3, 3) and bool(np.all(np.isfinite(m))) and np.allclose(m @ m.T, np.eye(3), atol=1e-6)
            and np.linalg.det(m) > 0)


def troncons(v: np.ndarray, relie: np.ndarray | None = None) -> list:
    """Tronçons visibles (z ≥ 0) de lignes de points en repère de vue (N, 3) ; `relie[i]` : le point i est relié au
    suivant.  Chaque tronçon est coupé au limbe au point exact de traversée (interpolé puis ramené sur le cercle).
    Rend une liste de tableaux (M, 2) de (X, Y)."""
    n = len(v)
    if n < 2:
        return []
    if relie is None:
        relie = np.ones(n - 1, dtype=bool)
    z = v[:, 2]
    devant = z >= 0
    vis = relie & devant[:-1] & devant[1:]
    entree = relie & ~devant[:-1] & devant[1:]          # segment qui entre dans la face visible
    sortie = relie & devant[:-1] & ~devant[1:]

    def limbe(i):                                       # point du limbe sur le segment (i, i + 1)
        a, b = v[i], v[i + 1]
        t = a[2] / (a[2] - b[2])
        x, y = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        l = math.hypot(x, y) or 1.0
        return np.array([x / l, y / l])

    # tronçons : suites de segments reliés et (au moins en partie) visibles ; un segment qui sort de la face visible
    # termine son tronçon, un segment qui y entre en commence un
    garde = vis | entree | sortie
    prec = np.concatenate(([False], garde[:-1]))
    prec_sortie = np.concatenate(([False], sortie[:-1]))
    debut = garde & (~prec | entree | prec_sortie)
    suiv_garde = np.concatenate((garde[1:], [False]))
    suiv_debut = np.concatenate((debut[1:], [False]))
    fin_run = garde & (~suiv_garde | suiv_debut)
    out = []
    for a, b in zip(np.flatnonzero(debut).tolist(), np.flatnonzero(fin_run).tolist()):
        # segments a … b : points a (ou le limbe s'il entre) … b + 1 (ou le limbe s'il sort)
        fin = b if sortie[b] else b + 1
        morceaux = [limbe(a)[None, :]] if entree[a] else [v[a:a + 1, :2]]
        morceaux.append(v[a + 1:fin + 1, :2])
        if sortie[b]:
            morceaux.append(limbe(b)[None, :])
        t = np.concatenate(morceaux)
        if len(t) > 1:
            out.append(t)
    return out


def nuit_orthographique(sv, decalage: float = 0.0, n: int = 240):
    """Partie visible de la calotte {p : p·s < −sin h} (nuit si h = 0, crépuscules sinon), s = direction du Soleil en
    repère de vue : liste de contours (X, Y) du disque unité (Y vers le haut) à remplir en pair-impair, ou None."""
    s = np.asarray(sv, dtype=float)
    s = s / np.linalg.norm(s)
    sh = math.sin(math.radians(decalage))
    cercle = dessin.cercle(s, 90.0 + decalage, n + 1)[:-1]
    limbe = np.stack([np.cos(t := np.linspace(0, 2 * math.pi, 240, endpoint=False)), np.sin(t), np.zeros(240)],
                     axis=1)

    def dans(q):
        return float(q @ s) < -sh

    vis = cercle[:, 2] >= 0
    if np.all(np.abs(cercle[:, 2]) < 1e-9) or not vis.any():
        return [limbe[:, :2]] if dans(np.array([0.0, 0.0, 1.0])) else None
    if vis.all():
        # contour entier visible : la calotte est dedans si son centre (−s) est de notre côté, sinon disque − contour
        return [cercle[:, :2]] if -s[2] >= 0 else [limbe[:, :2], cercle[:, :2]]
    # un seul arc visible : le parcourir depuis son début, puis revenir par le limbe du côté de la calotte
    i0 = int(np.flatnonzero(vis & ~np.roll(vis, 1))[0])
    idx = [(i0 - 1) % n]
    for k in range(n + 1):
        i = (i0 + k) % n
        idx.append(i)
        if not vis[i]:
            break
    tr_ = troncons(cercle[idx])
    if not tr_ or len(tr_[0]) < 2:
        return None
    arc = tr_[0]
    ta = math.atan2(arc[-1][1], arc[-1][0])
    tb = math.atan2(arc[0][1], arc[0][0])
    d = (tb - ta) % (2 * math.pi) or 2 * math.pi
    if not dans(np.array([math.cos(ta + d / 2), math.sin(ta + d / 2), 0.0])):
        d -= 2 * math.pi
    m = max(8, int(math.ceil(abs(d) / (2 * math.pi) * 120)))
    tt = ta + d * np.arange(1, m) / m
    return [np.vstack([arc, np.stack([np.cos(tt), np.sin(tt)], axis=1)])]


def _chemin_ecran(polys, cx, cy, rr) -> QPainterPath:
    ch = QPainterPath()
    ch.setFillRule(dessin.Qt.FillRule.OddEvenFill)
    for q in polys:
        q = np.asarray(q)
        ch.addPolygon(dessin.polygone(cx + rr * q[:, 0], cy - rr * q[:, 1]))
        ch.closeSubpath()
    return ch


_GRATICULE = None


def _graticule():
    """Méridiens tous les 15° et parallèles tous les 15° (sauf l'équateur) : (points, liaisons, marqués à 30°)."""
    global _GRATICULE
    if _GRATICULE is None:
        lignes = []
        for lo in range(-180, 180, 15):
            lignes.append((globe_xyz(np.arange(-90.0, 90.1, 3.0), np.full(61, float(lo))), lo % 30 == 0))
        for la in range(-75, 76, 15):
            if la:
                lignes.append((globe_xyz(np.full(121, float(la)), np.arange(-180.0, 180.1, 3.0)), la % 30 == 0))
        _GRATICULE = []
        for fort in (True, False):
            m = [q for q, f in lignes if f == fort]
            pts = np.vstack(m)
            relie = np.ones(len(pts) - 1, dtype=bool)
            relie[np.cumsum([len(q) for q in m])[:-1] - 1] = False
            _GRATICULE.append((pts, relie, fort))
    return _GRATICULE


class JourNuit(Animation):
    ID = 'daylightsimulator'
    HEURES_PAR_S = 1.0
    JOURS_PAR_S = 10.0

    TEMPS = ('jour', 'heure')

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        # heure en TU : jour et heure de Greenwich ; « Ma position » place aussi l'observateur
        self.poser(self.jour, jour_index(m.i.tu[1], m.i.tu[2]))
        self.poser(self.heure, heure_decimale(m.i.tu))
        if m.position:
            self.poser(self.lat, m.lat if m.lat is not None else self.lat.value())
            self.poser(self.lon, m.lon)

    def construire(self):
        self.mode = self.choix('mode', [('anim_daylightsimulator_jour', 'jour'),
                                        ('anim_daylightsimulator_annee', 'annee')], 'jour')
        self.jour = self.curseur('jour', 0.0, 364.0, 79.0, dec=0, cle_texte='anim_c_jour')
        self.heure = self.curseur('heure', 0.0, 24.0, 12.0, dec=2, unite='h', cle_texte='anim_daylightsimulator_tu')
        self.lat = self.curseur('latitude', -90.0, 90.0, 0.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.lon = self.curseur('longitude', -180.0, 180.0, 0.0, dec=1, unite='°', cle_texte='anim_c_longitude')
        self.c_crepuscule = self.coche('crepuscule', False)
        self.projection = self.choix('projection', [('anim_daylightsimulator_proj_equi', 'equi'),
                                                    ('anim_daylightsimulator_proj_nord', 'nord'),
                                                    ('anim_daylightsimulator_proj_sud', 'sud'),
                                                    ('anim_daylightsimulator_proj_globe', 'globe')], 'globe')
        self.bord = self.choix('bord', [('anim_daylightsimulator_bord_0', 0), ('anim_daylightsimulator_bord_30', 30)], 0)
        self.c_tournant = self.coche('tournant', False)
        self.c_axe = self.coche('axe', True)
        self._visibles()
        self.projection.currentIndexChanged.connect(self._visibles)
        self._carte = None
        self._disque = None                            # (cx, cy, rayon) du disque polaire ou du globe
        self.globe = orientation(25.0, -50.0)          # repère terrestre (tourné) → vue
        self._zoom = 1.0
        self._inertie = (0.0, 0.0)
        self._t_glisse = 0.0
        self._lancee = QTimer(self)
        self._lancee.setInterval(16)
        self._lancee.timeout.connect(self._inertie_pas)

    def _visibles(self, *_):
        pr = self.projection.currentData()
        self.bord._boite.setVisible(pr in ('nord', 'sud'))
        self.c_tournant.setVisible(pr != 'equi')
        self.c_axe.setVisible(pr == 'globe')

    def avancer(self, dt):
        if self.mode.currentData() == 'jour':
            h = self.heure.value() + dt * self.HEURES_PAR_S
            if h >= 24.0:
                self.jour.setValue((self.jour.value() + 1) % 365.0)
            self.heure.setValue(h % 24.0)
        else:
            self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def _jour(self):
        return self.jour.value() + self.heure.value() / 24.0

    def valeurs(self):
        dec, lon_ss = subsolaire(self._jour())
        h_obs = astro.mod180(self.lon.value() - lon_ss) / 15.0 + 12.0
        az, alt = astro.equatorial_vers_horizon(astro.mod180(self.lon.value() - lon_ss), dec, self.lat.value())
        out = [(tr('anim_c_date'), date_du_jour(self.jour.value()) + ', ' + heures_minutes(self.heure.value()) + ' TU'),
               (tr('anim_daylightsimulator_subsolaire'), '%s, %s' % (
                   decimal(dec, tr('anim_pc_n'), tr('anim_pc_s')), decimal(lon_ss, tr('anim_pc_e'), tr('anim_pc_o')))),
               (tr('anim_sunmotions_heure_vraie'), heures_minutes(h_obs)),
               (tr('anim_daylightsimulator_h_soleil'), angle(alt))]
        # au pôle Nord, le Soleil est à δ de hauteur toute la journée (−δ au pôle Sud)
        for nom, h in (('anim_daylightsimulator_pole_n', dec), ('anim_daylightsimulator_pole_s', -dec)):
            cle = ('anim_daylightsimulator_pole_horizon' if abs(h) < 0.05 else
                   'anim_daylightsimulator_jour_polaire' if h > 0 else 'anim_daylightsimulator_nuit_polaire')
            out.append((tr(nom), tr(cle, h=angle(h))))
        return out

    # ------------------------------------------------------------ souris
    def _nord(self):
        return self.projection.currentData() == 'nord'

    def _bord_lat(self, nord: bool) -> float:
        return -(1 if nord else -1) * float(self.bord.currentData() or 0)

    def _lon0(self, lon_ss: float) -> float:
        return 0.0 if self.c_tournant.isChecked() else lon_ss


    def recentrer(self):
        """Globe : face au point subsolaire, le nord en haut."""
        dec, lon_ss = subsolaire(self._jour())
        self.globe = orientation(dec, lon_ss if self.c_tournant.isChecked() else 0.0)
        self.toile.update()

    def tourner_globe(self, dx: float, dy: float, rayon: float | None = None):
        r = rayon if rayon is not None else (self._disque[2] if self._disque else 100.0)
        n = tourner(self.globe, dx, dy, r)
        # garde-fou : une orientation invalide (NaN, non orthonormée) n'est jamais gardée
        self.globe = n if valide(n) else (self.globe if valide(self.globe) else orientation(25.0, -50.0))
        self.toile.update()

    def vue_globe(self, lon_ss: float) -> np.ndarray:
        """Sans « terminateur tournant », la Terre tourne sous un Soleil fixe dans la vue."""
        if not valide(self.globe):
            self.globe = orientation(25.0, -50.0)
        if self.c_tournant.isChecked() or not math.isfinite(lon_ss):
            return self.globe
        return self.globe @ rotation((0.0, 0.0, 1.0), -math.radians(lon_ss))

    def molette(self, pos, delta):
        if self.projection.currentData() != 'globe':
            return False
        if not math.isfinite(delta):
            return True
        # molette ou pavé tactile très rapides (delta énorme) : borné avant la puissance (OverflowError sinon)
        self._zoom = max(0.6, min(4.0, self._zoom * (1.0015 ** max(-2400.0, min(2400.0, delta)))))
        self.toile.update()
        return True

    def double_clic(self, pos):
        if self.projection.currentData() != 'globe':
            return False
        self.recentrer()
        return True

    def presser(self, pos, bouton):
        proj = self.projection.currentData()
        dq = self._disque
        if proj == 'globe':
            if dq is None or math.hypot(pos.x() - dq[0], pos.y() - dq[1]) > dq[2] * 1.08:
                return False
            self._lancee.stop()
            if bouton == dessin.Qt.MouseButton.RightButton:
                self._placer_globe(pos)
                return True
            self._glisse = 'globe'
            self._inertie = (0.0, 0.0)
            return True
        if proj in ('nord', 'sud'):
            if dq is not None and math.hypot(pos.x() - dq[0], pos.y() - dq[1]) <= dq[2] + 4:
                self._glisse = self._tirer
                self._tirer(pos)
                return True
            return False
        if self._carte is not None and self._carte.contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def glisser(self, pos, dx, dy):
        if self._glisse == 'globe':
            import time
            self.tourner_globe(dx, dy)
            self._inertie = (dx, dy)
            self._t_glisse = time.monotonic()
            return
        super().glisser(pos, dx, dy)

    def relacher(self, pos):
        lance = self._glisse == 'globe'
        super().relacher(pos)
        import time
        # inertie légère : le globe continue un peu sur sa lancée (× 0,9 par image, arrêt sous 0,3 px)
        if lance and time.monotonic() - self._t_glisse < 0.08 and math.hypot(*self._inertie) >= 1.5:
            self._lancee.start()

    def _inertie_pas(self):
        vx, vy = self._inertie[0] * 0.9, self._inertie[1] * 0.9
        if not (math.isfinite(vx) and math.isfinite(vy)):
            vx = vy = 0.0
        self._inertie = (vx, vy)
        if math.hypot(vx, vy) < 0.3 or self.projection.currentData() != 'globe' or self._glisse is not None:
            self._lancee.stop()
            return
        self.tourner_globe(vx, vy)

    def _placer_globe(self, pos):
        cx, cy, rr = self._disque
        X, Y = (pos.x() - cx) / rr, -(pos.y() - cy) / rr
        if X * X + Y * Y > 1:
            return
        Z = math.sqrt(1 - X * X - Y * Y)
        _, lon_ss = subsolaire(self._jour())
        p = self.vue_globe(lon_ss).T @ np.array([X, Y, Z])          # inverse d'une rotation : la transposée
        self.lat.setValue(math.degrees(math.asin(max(-1.0, min(1.0, p[2])))))
        self.lon.setValue(math.degrees(math.atan2(p[1], p[0])))

    def _tirer(self, pos):
        proj = self.projection.currentData()
        if proj in ('nord', 'sud'):
            cx, cy, rr = self._disque
            nord = proj == 'nord'
            _, lon_ss = subsolaire(self._jour())
            u, v = (pos.x() - cx) / rr, (pos.y() - cy) / rr
            n = math.hypot(u, v)
            if n > 1:
                u, v = u / n, v / n
            la, lo = inverse_polaire(u, v, nord, self._bord_lat(nord), self._lon0(lon_ss))
            self.lat.setValue(max(-90.0, min(90.0, la)))
            self.lon.setValue(lo)
            return
        r = self._carte
        self.lon.setValue(max(-180.0, min(180.0, (pos.x() - r.x()) / r.width() * 360.0 - 180.0)))
        self.lat.setValue(max(-90.0, min(90.0, 90.0 - (pos.y() - r.y()) / r.height() * 180.0)))

    def dessiner(self, p, rect):
        if self.projection.currentData() in ('nord', 'sud'):
            self._dessiner_polaire(p, rect, self.projection.currentData() == 'nord')
            return
        if self.projection.currentData() == 'globe':
            self._dessiner_globe(p, rect)
            return
        self._disque = None
        w = min(rect.width() - 20, (rect.height() - 20) * 2.0)
        carte = QRectF(rect.center().x() - w / 2, rect.center().y() - w / 4, w, w / 2)
        self._carte = carte

        def xy(la, lo):
            return QPointF(carte.x() + (lo + 180.0) / 360.0 * carte.width(), carte.y() + (90.0 - la) / 180.0 *
                           carte.height())
        p.fillRect(carte, dessin.c('terre', 0.35))
        dessiner_cotes_carte(p, carte, 'texte', 0.8, 0.8)
        dec, lon_ss = subsolaire(self._jour())
        lons = np.linspace(-180.0, 180.0, 361)
        # nuit : du terminateur jusqu'au pôle plongé dans l'obscurité (pôle Sud si δ > 0)
        for decalage, alpha in (((0.0, 0.55),) + (((6.0, 0.25), (12.0, 0.2), (18.0, 0.15))
                                                  if self.c_crepuscule.isChecked() else ())):
            if decalage == 0.0:
                lats = latitude_terminateur(lons, dec, lon_ss)
            else:
                # courbe de hauteur −decalage : sin h = sin φ sin δ + cos φ cos δ cos H, résolue en φ
                lats = latitudes_hauteur(lons, dec, lon_ss, -decalage)
            pole = -90.0 if dec >= 0 else 90.0
            poly = [xy(la, lo) for la, lo in zip(lats, lons)] + [xy(pole, 180.0), xy(pole, -180.0)]
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c('nuit', alpha))
            p.drawPolygon(QPolygonF(poly))
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawRect(carte)
        q = xy(dec, lon_ss)
        dessin.disque(p, q.x(), q.y(), 8, 'soleil', bord='fond')
        o = xy(self.lat.value(), self.lon.value())
        dessin.disque(p, o.x(), o.y(), 5, 'accent3', bord='fond')
        dessin.police(p, 1.1, gras=True)
        dessin.texte(p, rect.x() + 12, rect.y() + 18, date_du_jour(self.jour.value()) + ', ' +
                     heures_minutes(self.heure.value()) + ' TU', centre=False)
        dessin.police(p, 1 / 1.1)

    def _couches(self):
        return COUCHES if self.c_crepuscule.isChecked() else COUCHES[:1]

    def _titre(self, p, rect):
        dessin.police(p, 1.1, gras=True)
        dessin.texte(p, rect.x() + 12, rect.y() + 18, date_du_jour(self.jour.value()) + ', ' +
                     heures_minutes(self.heure.value()) + ' TU', centre=False)
        dessin.police(p, 1 / 1.1)

    # ------------------------------------------------------------ vue polaire
    def _dessiner_polaire(self, p, rect, nord: bool):
        """Carte azimutale équidistante, terminateur exact, crépuscules, cercles remarquables."""
        self._carte = None
        rr = min(rect.width(), rect.height() - 40) / 2 - 22
        if not rr > 4:
            return
        cx, cy = rect.center().x(), rect.center().y() + 12
        self._disque = (cx, cy, rr)
        pole = 1 if nord else -1
        bord = self._bord_lat(nord)
        dec, lon_ss = subsolaire(self._jour())
        lon0 = self._lon0(lon_ss)

        def xy(la, lo):
            u, v = projeter_polaire(la, lo, nord, bord, lon0)
            return QPointF(cx + float(u) * rr, cy + float(v) * rr)

        def dedans(la):
            return la >= bord - 1e-9 if nord else la <= bord + 1e-9

        disque = QPainterPath()
        disque.addEllipse(QPointF(cx, cy), rr, rr)
        p.save()
        p.setClipPath(disque)
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('terre', 0.35))
        p.drawEllipse(QPointF(cx, cy), rr, rr)
        # grille : méridiens tous les 15° (30° marqués), parallèles tous les 15°
        for lo in range(-180, 180, 15):
            p.setPen(dessin.stylo('grille', 0.9 if lo % 30 == 0 else 0.5, 0.8 if lo % 30 == 0 else 0.5))
            p.drawLine(xy(pole * 90.0, lo), xy(bord, lo))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for la in range(-75, 76, 15):
            if not dedans(la):
                continue
            q = xy(la, 0.0)
            r = math.hypot(q.x() - cx, q.y() - cy)
            p.setPen(dessin.stylo('grille', 0.9 if la % 30 == 0 else 0.5, 0.8 if la % 30 == 0 else 0.5))
            p.drawEllipse(QPointF(cx, cy), r, r)
        # côtes (chemin en cache pour lon0 = 0, le peintre tourne de lon0)
        p.save()
        p.translate(cx, cy)
        p.rotate(lon0 if nord else -lon0)
        p.scale(rr, rr)
        pen = dessin.stylo('texte', 0.8, 0.8)
        pen.setCosmetic(True)
        p.setPen(pen)
        p.drawPath(chemin_cotes_polaire(nord, bord))
        p.restore()
        # nuit et crépuscules : boucle autour du pôle ; la nuit est dedans ou dehors selon la saison
        p.save()
        p.translate(cx, cy)
        p.scale(rr, rr)
        p.setPen(dessin.Qt.PenStyle.NoPen)
        for decalage, alpha in self._couches():
            p.setBrush(dessin.c('nuit', alpha))
            p.drawPath(chemin_nuit_polaire(dec, lon_ss, decalage, nord, bord, lon0))
        p.restore()
        # cercles remarquables : équateur, tropiques, cercles polaires
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for la, cle in ((0.0, 'equateur'), (EPS, 'accent1'), (-EPS, 'accent1'), (90 - EPS, 'accent2'),
                        (EPS - 90, 'accent2')):
            if not dedans(la):
                continue
            q = xy(la, 0.0)
            r = math.hypot(q.x() - cx, q.y() - cy)
            p.setPen(dessin.stylo(cle, 1.6 if la == 0 else 1.3, 0.9, la != 0))
            p.drawEllipse(QPointF(cx, cy), r, r)
        # Soleil au zénith (s'il est dans le disque) et observateur
        if dedans(dec):
            q = xy(dec, lon_ss)
            dessin.disque(p, q.x(), q.y(), 8, 'soleil', bord='fond')
        if dedans(self.lat.value()):
            o = xy(self.lat.value(), self.lon.value())
            dessin.disque(p, o.x(), o.y(), 5, dessin.c('accent3'), bord='fond')
        p.restore()
        p.setPen(dessin.stylo('grille', 1.2))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), rr, rr)
        # longitudes au bord
        dessin.police(p, 0.8)
        for lo in (0, 90, 180, -90):
            u, v = projeter_polaire(bord, lo, nord, bord, lon0)
            nom = '0°' if lo == 0 else '180°' if lo == 180 else '90° ' + tr('anim_pc_e' if lo > 0 else 'anim_pc_o')
            dessin.texte(p, cx + float(u) * (rr + 12), cy + float(v) * (rr + 12), nom, 'doux')
        dessin.police(p, 1 / 0.8)
        self._titre(p, rect)

    # ------------------------------------------------------------ globe 3D
    def _dessiner_globe(self, p, rect):
        """Globe vu de l'espace (orthographique) : sphère ombrée, côtes et cercles coupés au limbe, nuit et
        crépuscules exacts (calottes de la sphère), point subsolaire, axe des pôles, flèche vers le Soleil."""
        self._carte = None
        rr = (min(rect.width() - 70, rect.height() - 70) / 2) * self._zoom
        if not rr > 4:
            return
        cx, cy = rect.center().x(), rect.center().y() + 8
        self._disque = (cx, cy, rr)
        dec, lon_ss = subsolaire(self._jour())
        m = self.vue_globe(lon_ss)
        s = m @ globe_xyz(dec, lon_ss)
        p.save()
        p.setClipRect(rect)

        def ecran(q):
            return QPointF(cx + q[0] * rr, cy - q[1] * rr)

        def ligne(v, relie, pen):
            p.setPen(pen)
            for t in troncons(v, relie):
                p.drawPolyline(dessin.polygone(cx + rr * t[:, 0], cy - rr * t[:, 1]))

        # atmosphère fine
        p.setPen(dessin.Qt.PenStyle.NoPen)
        atm = QRadialGradient(QPointF(cx, cy), rr * 1.06)
        atm.setColorAt(0.98 / 1.06, dessin.c('ciel', 0.55))
        atm.setColorAt(0.0, dessin.c('ciel', 0.55))
        atm.setColorAt(1.0, dessin.c('ciel', 0.0))
        p.setBrush(QBrush(atm))
        p.drawEllipse(QPointF(cx, cy), rr * 1.06, rr * 1.06)
        # sphère éclairée : dégradé centré vers le point subsolaire projeté, limbe assombri
        base = dessin.c('terre')
        g = QRadialGradient(QPointF(cx, cy), rr, QPointF(cx + s[0] * rr * 0.45, cy - s[1] * rr * 0.45), rr * 0.05)
        c0, c1, c2 = base.lighter(135), QColor(base), base.lighter(60)
        c0.setAlphaF(0.55)
        c1.setAlphaF(0.42)
        c2.setAlphaF(0.6)
        g.setColorAt(0.0, c0)
        g.setColorAt(0.6, c1)
        g.setColorAt(1.0, c2)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), rr, rr)
        # graticule, côtes (coupés au limbe : pas besoin de découper par le disque)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for pts, relie, fort in _graticule():
            ligne(pts @ m.T, relie, dessin.stylo('grille', 0.9 if fort else 0.5, 0.8 if fort else 0.5))
        pts, relie = _cotes_tout()
        ligne(pts @ m.T, relie, dessin.stylo('texte', 0.8, 0.85))
        # nuit et crépuscules
        p.setPen(dessin.Qt.PenStyle.NoPen)
        for decalage, alpha in self._couches():
            polys = nuit_orthographique(s, decalage)
            if polys:
                p.setBrush(dessin.c('nuit', alpha))
                p.drawPath(_chemin_ecran(polys, cx, cy, rr))
        # côté nuit ombré façon sphère : voile qui s'épaissit vers l'antipode du Soleil
        n = math.hypot(s[0], s[1])
        if n > 1e-6:
            ux, uy = s[0] / n, -s[1] / n
            v = QLinearGradient(QPointF(cx + ux * rr, cy + uy * rr), QPointF(cx - ux * rr, cy - uy * rr))
            v.setColorAt(0.0, dessin.c('nuit', 0.0))
            v.setColorAt(max(0.0, min(1.0, 0.5 + 0.5 * s[2])), dessin.c('nuit', 0.0))
            v.setColorAt(1.0, dessin.c('nuit', 0.3))
            p.setBrush(QBrush(v))
            p.drawEllipse(QPointF(cx, cy), rr, rr)
        # cercles remarquables, étiquetés à leur point visible le plus à droite
        etiquettes = []
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for la, cle, nom in ((0.0, 'equateur', 'anim_sunsrays_equateur'), (EPS, 'accent1', 'anim_sunsrays_tropique_cancer'),
                             (-EPS, 'accent1', 'anim_sunsrays_tropique_capricorne'),
                             (90 - EPS, 'accent2', 'anim_sunsrays_cercle_arctique'),
                             (EPS - 90, 'accent2', 'anim_sunsrays_cercle_antarctique')):
            v = globe_xyz(np.full(121, la), np.arange(-180.0, 180.1, 3.0)) @ m.T
            ligne(v, None, dessin.stylo(cle, 1.6 if la == 0 else 1.3, 0.95, la != 0))
            vis = v[v[:, 2] > 0.15]
            if len(vis):
                q = vis[int(np.argmax(vis[:, 0]))]
                etiquettes.append((ecran(q), cle, tr(nom)))
        # axe des pôles : partie cachée derrière le globe en pointillé
        if self.c_axe.isChecked():
            nn = m @ np.array([0.0, 0.0, 1.0])

            def bout(k):
                return QPointF(cx + nn[0] * rr * k, cy - nn[1] * rr * k)

            for sgn in (1, -1):
                p.setPen(dessin.stylo('texte', 1.6, 0.85))
                p.drawLine(bout(sgn), bout(sgn * 1.25))
                p.setPen(dessin.stylo('texte', 1.2, 0.5, sgn * nn[2] < 0))
                p.drawLine(bout(0), bout(sgn))
            dessin.texte(p, bout(1.33).x(), bout(1.33).y(), tr('anim_pc_n'), 'texte')
        # point subsolaire et observateur
        if s[2] >= 0:
            q = ecran(s)
            dessin.disque(p, q.x(), q.y(), 7, 'soleil', bord='fond')
        o = m @ globe_xyz(self.lat.value(), self.lon.value())
        if o[2] >= 0:
            q = ecran(o)
            dessin.disque(p, q.x(), q.y(), 5, dessin.c('accent3'), bord='fond')
        p.restore()
        dessin.police(p, 0.8)
        for q, cle, nom in etiquettes:
            dessin.etiquette(p, q.x(), q.y(), nom, cle, 4)
        dessin.police(p, 1 / 0.8)
        # le Soleil est hors champ : flèche au bord du globe vers sa direction
        if n > 0.05:
            ux, uy = s[0] / n, -s[1] / n
            dessin.fleche(p, cx + ux * (rr + 10), cy + uy * (rr + 10), cx + ux * (rr + 34), cy + uy * (rr + 34),
                          dessin.stylo('soleil', 2.2), 8)
            dessin.texte(p, cx + ux * (rr + 48), cy + uy * (rr + 48), tr('anim_daylightsimulator_vers_soleil'),
                         'soleil', fond=True)
        self._titre(p, rect)
