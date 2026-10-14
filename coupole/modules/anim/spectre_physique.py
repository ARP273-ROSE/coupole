"""Spectres sur bases physiques, communs à l'Explorateur de spectres et à la Parallaxe spectroscopique : un seul
modèle (spectres_physiques.py, données modele_spectres.json.gz : Saha–Boltzmann sur des atmosphères ATLAS9, 133 raies
NIST, bandes TiO et CH), bande de spectre colorée (continu de Planck × raies, couleurs CIE 1931 → sRGB), et
signalement des cas extrapolés ou bornés.  Même code, ligne pour ligne, que src/anim/spectre_physique.ts du web."""
from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage

from ...core.i18n import tr
from . import dessin
from .couleur_etoile import couleur_etoile
from .spectres_physiques import ModeleSpectres

_DOSSIER = Path(__file__).with_name('donnees')
_MODELE: ModeleSpectres | None = None


def modele() -> ModeleSpectres:
    """Le modèle (construit une fois)."""
    global _MODELE
    if _MODELE is None:
        with gzip.open(_DOSSIER / 'modele_spectres.json.gz', 'rt', encoding='utf-8') as f:
            _MODELE = ModeleSpectres(json.load(f))
    return _MODELE


FAMILLES = ('he_ii', 'he_i', 'h', 'metaux_ionises', 'metaux', 'molecules')
COULEURS_FAMILLES = {'he_ii': 'arc1', 'he_i': 'accent2', 'h': 'accent3', 'metaux_ionises': 'accent1', 'metaux': 'horizon',
                     'molecules': 'terre', 'ch': 'mars'}
LAMBDA_MIN = 380.0
LAMBDA_MAX = 720.0

# drapeaux de l'étalonnage (texte du modèle) → clé de texte (FR/EN)
_DRAPEAUX = (('hors domaine Malkov', 'spectres_d_borne'), ('hors table', 'spectres_d_borne'),
             ('interpolé', 'spectres_d_interpole'), ('M_V via BC_V', 'spectres_d_bc_naines'))

with gzip.open(_DOSSIER / 'spectres_atmosphere.json.gz', 'rt', encoding='utf-8') as _f:
    _ATM = json.load(_f)['classes']


def extrapolation_atmosphere(t: float, classe: str) -> int:
    """Codes d'extrapolation de l'atmosphère (bit 1 : log g hors grille ATLAS9 ; bit 2 : T_eff < 3 500 K) au type t."""
    tab = _ATM.get(classe)
    if not tab:
        return 0
    tt = max(0.0, min(len(tab) - 1, t))
    i = int(math.floor(tt))
    j = min(len(tab) - 1, int(math.ceil(tt)))
    return tab[i] | tab[j]


def remarques(t: float, classe: str, e: dict | None = None) -> list:
    """Remarques à afficher (textes traduits) : étalonnage borné ou interpolé, atmosphère extrapolée."""
    et = e if e is not None else modele().etalonnage(t, classe)
    cles = []
    for d in et['drapeaux']:
        for debut, cle in _DRAPEAUX:
            if d.startswith(debut) and cle not in cles:
                cles.append(cle)
    a = extrapolation_atmosphere(t, classe)
    if a & 1 and 'spectres_d_logg' not in cles:
        cles.append('spectres_d_logg')
    if a & 2 and 'spectres_d_froide' not in cles:
        cles.append('spectres_d_froide')
    return [tr(k) for k in cles]


# ------------------------------------------------------------ couleurs
def _lineaire(v: float) -> float:
    x = v / 255
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _srgb(v: float) -> int:
    x = max(0.0, min(1.0, v))
    return int(math.floor(255 * (1.055 * x ** (1 / 2.4) - 0.055 if x > 0.0031308 else 12.92 * x) + 0.5))


_LIN_LAMBDA: dict = {}


def _couleur_lineaire(lam: float):
    k = int(math.floor(lam * 10 + 0.5))
    c = _LIN_LAMBDA.get(k)
    if c is None:
        r, g, b = modele().couleur_lambda(k / 10)
        c = _LIN_LAMBDA[k] = (_lineaire(r), _lineaire(g), _lineaire(b))
    return c


def couleur_eclairee(lam: float, i: float) -> QColor:
    """Couleur d'une longueur d'onde éclairée à l'intensité i (0–1, lumière linéaire)."""
    r, g, b = _couleur_lineaire(lam)
    k = max(0.0, i)
    return QColor(_srgb(r * k), _srgb(g * k), _srgb(b * k))


def couleur_etoile_teff(teff: float) -> QColor:
    """Couleur d'une étoile de température teff (corps noir → CIE 1931 → sRGB), la même dans toutes les animations."""
    return QColor(*couleur_etoile(teff))


# ------------------------------------------------------------ bande de spectre
_CACHE: list = []          # deux dernières bandes : (clé, QImage n × 1)


def colonnes(t: float, classe: str, mode: str, familles, n: int) -> QImage:
    """Image n × 1 des couleurs d'une bande de spectre (λ de LAMBDA_MIN à LAMBDA_MAX) : continu de Planck à T_eff,
    multiplié par I/I_continu (raies et bandes moléculaires des familles choisies) en absorption ; raies élargies à une
    colonne au moins (largeur équivalente conservée).  Mise en cache (deux dernières)."""
    cle = (t, classe, mode, tuple(familles) if familles is not None else None, n)
    for k, img in _CACHE:
        if k == cle:
            return img
    m = modele()
    teff = m.etalonnage(t, classe)['teff']
    pas = (LAMBDA_MAX - LAMBDA_MIN) / n
    lams = [LAMBDA_MIN + (k + 0.5) * pas for k in range(n)]
    res = m.spectre(t, classe, lams, list(familles) if familles is not None else None, max(0.25, 1.2 * pas)) \
        if mode == 'absorption' else None
    img = QImage(n, 1, QImage.Format.Format_RGB32)
    for k, lam in enumerate(lams):
        i = ModeleSpectres.continu_relatif(teff, lam) * (max(0.0, res[k]) if res is not None else 1.0)
        img.setPixelColor(k, 0, couleur_eclairee(lam, i if math.isfinite(i) else 0.0))
    _CACHE.insert(0, (cle, img))
    del _CACHE[2:]
    return img


def dessiner_bande(p, r: QRectF, t: float, classe: str, mode: str, familles, graduer: bool = True):
    """Bande de spectre dans r : continu (« continu »), continu et raies d'absorption (« absorption ») ou raies
    d'émission sur fond noir (« emission ») ; graduations (nm) sous la bande si `graduer`."""
    if not (r.width() > 2 and r.height() > 2):
        return
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.fillRect(r, QColor(8, 8, 10))
    if mode == 'emission':
        m = modele()
        raies = [x for x in m.raies(t, classe) if familles is None or x['famille'] in familles]
        pmax = max([1e-6] + [x['profondeur'] for x in raies])
        kx = r.width() / (LAMBDA_MAX - LAMBDA_MIN)
        for x in raies:
            if x['lambda'] < LAMBDA_MIN or x['lambda'] > LAMBDA_MAX:
                continue
            a = min(1.0, max(0.12, x['profondeur'] / pmax))
            largeur = max(1.6, (x['fwhm'] or 0) * kx)
            col = couleur_eclairee(x['lambda'], 1.0)
            col.setAlphaF(a)
            p.fillRect(QRectF(r.left() + (x['lambda'] - LAMBDA_MIN) * kx - largeur / 2, r.top(), largeur, r.height()), col)
    else:
        n = max(60, min(720, int(math.floor(r.width() + 0.5))))
        img = colonnes(t, classe, mode, familles, n)
        p.setRenderHint(p.RenderHint.SmoothPixmapTransform, False)
        p.drawImage(r, img)
    p.setPen(dessin.stylo('grille', 1.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(r)
    p.restore()
    if graduer:
        dessin.police(p, 0.8)
        pas = 100 if r.width() < 300 else 50
        for lam in range(400, 701, pas):
            dessin.texte(p, r.left() + r.width() * (lam - LAMBDA_MIN) / (LAMBDA_MAX - LAMBDA_MIN), r.bottom() + 10,
                         '%d nm' % lam, 'doux')
        dessin.police(p, 1 / 0.8)

