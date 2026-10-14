"""Couleur vraie d'une étoile réelle, commune au bureau et au web (src/calc/couleur_etoile.ts de Coupole Web, mêmes
tests sur tests/couleurs_reference.json).  Table précalculée : corps noir de T_eff → CIE 1931 2° (CIE, CC BY-SA 4.0)
→ sRGB (primaires W3C CSS Color 4), composante linéaire maximale = 1 ; vérifiée par SageMath.  La luminosité est rendue
à part (taille du disque selon la magnitude), la table ne donne que la teinte."""
from __future__ import annotations

import bisect
import gzip
import json
import math
from pathlib import Path

with gzip.open(Path(__file__).with_name('donnees') / 'couleurs_etoiles.json.gz', 'rt', encoding='utf-8') as _f:
    _T = json.load(_f)
_TR, _BV = _T['T_rgb'], _T['bv_teff_naines']
_LT = [math.log10(r[0]) for r in _TR]


def _round(x: float) -> int:
    """Arrondi de Math.round (moitiés vers +∞), comme le web."""
    return int(math.floor(x + 0.5))


def couleur_etoile(t: float) -> tuple[int, int, int]:
    """Teinte sRGB (0–255) d'une étoile de température effective t (K), interpolée en log T ; bornée à 1 000–50 000 K."""
    if t is None or not math.isfinite(t):
        t = 5772.0
    x = math.log10(min(max(t, _TR[0][0]), _TR[-1][0]))
    hi = min(max(bisect.bisect_right(_LT, x), 1), len(_LT) - 1)
    lo = hi - 1
    if _LT[hi] <= x:
        lo = hi
    f = 0.0 if hi == lo else (x - _LT[lo]) / (_LT[hi] - _LT[lo])
    return tuple(_round(_TR[lo][k] + f * (_TR[hi][k] - _TR[lo][k])) for k in (1, 2, 3))


def teff_de_bv(bv: float) -> float:
    """T_eff (K) d'une NAINE de couleur B−V (Pecaut & Mamajek 2013) — repli quand aucune T_eff publiée n'existe."""
    if bv <= _BV[0][0]:
        return _BV[0][1]
    for (x0, t0), (x1, t1) in zip(_BV, _BV[1:]):
        if bv <= x1:
            return t0 + (t1 - t0) * (bv - x0) / (x1 - x0) if x1 > x0 else t0
    return _BV[-1][1]


def rayon_disque(v: float, v_ref: float = 0.0, r_ref: float = 4.5, r_min: float = 1.2, r_max: float = 7.0) -> float:
    """Rayon de disque (px) selon la magnitude V : flux ∝ 10^(−0,4 V), rayon ∝ flux^(1/4) (lisibilité, borné)."""
    if v is None or not math.isfinite(v):
        return r_min
    return min(r_max, max(r_min, r_ref * 10 ** (-0.1 * (v - v_ref))))


def _lin(v: float) -> float:
    x = v / 255
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _gam(x: float) -> int:
    return _round(255 * (1.055 * x ** (1 / 2.4) - 0.055 if x > 0.0031308 else 12.92 * x))


def accentuer(c, k: float = 2.5) -> tuple[int, int, int]:
    """Couleur « accentuée » pour l'enseignement (réglage explicite, jamais par défaut) : en lumière linéaire, l'écart à
    la luminance (Y, coefficients sRGB) est multiplié par k, puis la composante maximale ramenée à 1."""
    lin = [_lin(v) for v in c]
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    s = [max(0.0, y + k * (v - y)) for v in lin]
    m = max(max(s), 1e-9)
    return tuple(_gam(min(1.0, v / m)) for v in s)


def rvb_hex(h: str) -> tuple[int, int, int]:
    v = int(h[1:], 16)
    return (v >> 16) & 255, (v >> 8) & 255, v & 255
