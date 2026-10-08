"""Calcul sur carte graphique : API commune pour les modules.

Le module « Banque OHP » n'utilise PAS la carte graphique, et c'est voulu :
son travail est dominé par le réseau, la lecture/écriture disque et la
compression Zstandard, qui tourne sur le processeur.  Copier chaque image vers
la carte graphique coûterait plus que les quelques opérations faites dessus.

Pour les modules futurs (simulateurs, empilement, transformées de Fourier sur
de grands tableaux), ``tableaux()`` rend un espace de noms compatible numpy :
CuPy si une carte NVIDIA et CuPy sont présents et que l'utilisateur l'a
demandé, numpy sinon.  CuPy reste une dépendance facultative
(``pip install cupy-cuda12x``).
"""
from __future__ import annotations

import numpy as np

from . import machine as _machine


def cupy_disponible() -> bool:
    try:
        import cupy  # type: ignore
        return cupy.cuda.runtime.getDeviceCount() > 0
    except Exception:
        return False


def tableaux(preferer_gpu: bool = False):
    """Module de tableaux à utiliser : ``cupy`` si demandé et possible, sinon ``numpy``."""
    if preferer_gpu and cupy_disponible():
        import cupy  # type: ignore
        return cupy
    return np


def vers_numpy(a):
    """Ramène un tableau (numpy ou cupy) en mémoire centrale."""
    if hasattr(a, 'get') and type(a).__module__.startswith('cupy'):
        return a.get()
    return np.asarray(a)


def resume_gpu() -> dict:
    """Ce qui est détecté, et ce qui est utilisable pour le calcul."""
    cartes = _machine.detecter().cartes
    return {'cartes': [c.nom for c in cartes],
            'nvidia': any(c.fabricant == 'NVIDIA' for c in cartes),
            'cupy': cupy_disponible()}
