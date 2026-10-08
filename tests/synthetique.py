"""Images synthétiques à paramètres connus (FWHM, ellipticité, fond, bruit, gradient, saturation, traînées)
pour valider le module Qualité.  Les étoiles sont intégrées sur le pixel (sur-échantillonnage 5 × 5)."""
import math

import numpy as np


def etoile(img, x0, y0, flux, fwhm, e=0.0, ang=0.0, profil='moffat', beta=3.0, sur=5):
    ny, nx = img.shape
    r = int(5 * fwhm) + 3
    xi, yi = int(x0), int(y0)
    ys, xs = np.mgrid[yi - r:yi + r + 1, xi - r:xi + r + 1]
    off = (np.arange(sur) + 0.5) / sur - 0.5
    acc = np.zeros(xs.shape)
    a, b = fwhm / math.sqrt(1 - e), fwhm * math.sqrt(1 - e)          # FWHM moyenne géométrique conservée
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for ox in off:
        for oy in off:
            dx, dy = xs + ox - x0, ys + oy - y0
            u, v = c * dx + s * dy, -s * dx + c * dy
            if profil == 'gauss':
                acc += np.exp(-0.5 * ((u / (a / 2.3548)) ** 2 + (v / (b / 2.3548)) ** 2))
            else:
                k = 2 * math.sqrt(2 ** (1 / beta) - 1)
                acc += (1 + (u / (a / k)) ** 2 + (v / (b / k)) ** 2) ** (-beta)
    acc *= flux / acc.sum()
    y0c, x0c = max(0, yi - r), max(0, xi - r)
    bloc = acc[y0c - (yi - r):, x0c - (xi - r):]
    h, w = min(bloc.shape[0], ny - y0c), min(bloc.shape[1], nx - x0c)
    img[y0c:y0c + h, x0c:x0c + w] += bloc[:h, :w]


def image(n=1024, fwhm=4.0, e=0.0, ang=30.0, profil='moffat', fond=800.0, bruit=12.0, etoiles=150, seed=1,
          gradient=0.0, vignetage=0.0, fwhm_fn=None, satures=0, trainee=False):
    rng = np.random.default_rng(seed)
    img = np.full((n, n), fond, dtype=float)
    yy, xx = np.mgrid[0:n, 0:n]
    if gradient:                                   # gradient linéaire : `gradient` × fond sur toute la largeur
        img += fond * gradient * (xx / (n - 1))
    if vignetage:                                  # baisse radiale : −vignetage au coin
        r2 = ((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (2 * (n / 2) ** 2)
        img *= 1 - vignetage * r2
    for _ in range(etoiles):
        x, y = rng.uniform(40, n - 40, 2)
        etoile(img, x, y, rng.uniform(2e4, 2e5), fwhm_fn(x, y) if fwhm_fn else fwhm, e, ang, profil)
    for _ in range(satures):
        x, y = rng.uniform(60, n - 60, 2)
        etoile(img, x, y, 5e7, fwhm, 0.0, 0.0, profil)
    if trainee:                                    # segment de 300 px, 2 px de large
        t = np.linspace(0, 1, 3000)
        for x, y in zip(200 + 300 * t, 300 + 120 * t):
            img[int(y) - 1:int(y) + 1, int(x)] += 60.0
    img += rng.normal(0, bruit, img.shape)
    if satures:
        img = np.minimum(img, 65535.0)
    return img
