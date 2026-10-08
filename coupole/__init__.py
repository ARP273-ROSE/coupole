"""Coupole — boîte à outils libre du DU « Explorer et Comprendre l'Univers ».

Free toolbox for the « Explorer et Comprendre l'Univers » university diploma
(Observatoire de Paris).  Licence GPL-3.0-or-later.
"""
from __future__ import annotations

from pathlib import Path


def _version() -> str:
    # 1) dépôt ou paquet autonome : le fichier VERSION à côté du dossier coupole/
    #    (seulement si kit.json est là aussi : ce n'est pas le VERSION d'un autre paquet)
    racine = Path(__file__).resolve().parent.parent
    if (racine / 'kit.json').exists():
        try:
            v = (racine / 'VERSION').read_text(encoding='utf-8').strip()
            if v:
                return v
        except OSError:
            pass
    # 2) installation par pip : métadonnées du paquet
    try:
        from importlib.metadata import version
        return version('coupole')
    except Exception:
        return '0.0.0'


__version__ = _version()
NOM = 'Coupole'
