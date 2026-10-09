"""Bibliothèques facultatives : lesquelles sont présentes, en quelle version (« Ma machine », « À propos »).

Coupole fonctionne sans elles, mais une fonction s'en trouve réduite ou plus lente : sans ``reproject``,
l'alignement du module Archives retombe sur un rééchantillonnage bilinéaire de scipy ; sans ``sep``, le module
Qualité des images ne mesure rien.  Les paquets autonomes (installeur Windows, .dmg, tar.gz, .deb) les embarquent
toutes depuis 0.2.1, sauf CuPy (carte NVIDIA + CUDA, plusieurs centaines de Mo, inutilisé pour l'instant).

Détection sans import (``importlib.util.find_spec`` + métadonnées du paquet) : rien de lourd au démarrage.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util

# (module importé, distribution pip, extra de pyproject, rôle)
FACULTATIVES = (
    ('sep', 'sep', 'qualite', 'qualite'),
    ('reproject', 'reproject', 'alignement', 'alignement'),
    ('astropy_healpix', 'astropy-healpix', 'alignement', 'alignement'),
    ('psutil', 'psutil', '', 'machine'),
    ('lxml', 'lxml', 'validation', 'validation'),
    ('cupy', 'cupy-cuda12x', 'gpu', 'gpu'),
)
EMBARQUEES = ('sep', 'reproject', 'astropy_healpix', 'psutil', 'lxml')     # contrôlées dans chaque paquet


def _version(module: str, distribution: str) -> str:
    for nom in (distribution, module):
        try:
            return importlib.metadata.version(nom)
        except Exception:
            continue
    return '?'


def facultatives() -> list[dict]:
    """[{'module', 'distribution', 'extra', 'role', 'version' (None si absente)}] dans l'ordre de FACULTATIVES."""
    out = []
    for module, dist, extra, role in FACULTATIVES:
        try:
            present = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            present = False
        out.append({'module': module, 'distribution': dist, 'extra': extra, 'role': role,
                    'version': _version(module, dist) if present else None})
    return out


def resume(liste: list[dict] | None = None) -> tuple[str, str]:
    """(présentes « sep 1.4.1, reproject 0.21.0 … », absentes « cupy-cuda12x … ») ; '' si aucune."""
    liste = facultatives() if liste is None else liste
    presentes = ', '.join('%s %s' % (b['distribution'], b['version']) for b in liste if b['version'])
    absentes = ', '.join(b['distribution'] for b in liste if not b['version'])
    return presentes, absentes


def essai_embarquees() -> dict:
    """Essai réel des bibliothèques que chaque paquet autonome doit embarquer (contrôle des paquets en CI) :
    import, rééchantillonnage `reproject_interp` d'une petite image, fond et extraction SEP.  Lève à la première
    absence ou panne ; rend {module: version}."""
    import numpy as np
    from astropy.wcs import WCS
    import reproject
    import sep
    from reproject import reproject_interp
    w = WCS(naxis=2)
    w.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    w.wcs.crval = [10.0, 20.0]
    w.wcs.crpix = [16.5, 16.5]
    w.wcs.cdelt = [-1e-3, 1e-3]
    yy, xx = np.mgrid[0:32, 0:32]
    image = (100 + 500 * np.exp(-((xx - 15.0) ** 2 + (yy - 17.0) ** 2) / 4.0)).astype('f4')
    sortie, couverture = reproject_interp((image, w), w, shape_out=image.shape)
    if not np.isfinite(sortie).any() or float(np.nanmax(np.abs(sortie - image))) > 1e-2:
        raise RuntimeError('reproject_interp: unexpected result')
    fond = sep.Background(np.ascontiguousarray(image, dtype='f4'))
    objets = sep.extract(image - fond.back(), 5.0, err=fond.globalrms + 1.0)
    if len(objets) < 1:
        raise RuntimeError('sep.extract: no source found')
    import astropy_healpix  # noqa: F401  (tiré par reproject)
    import psutil  # noqa: F401
    import lxml.etree  # noqa: F401
    return {b['module']: b['version'] for b in facultatives() if b['module'] in EMBARQUEES}
