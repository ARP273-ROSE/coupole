"""Petits formats partagés par l'interface et la ligne de commande du module Qualité (sans Qt)."""
from __future__ import annotations

from ...core.i18n import tr


def duree_lisible(s: float | None) -> str:
    """« 12 s », « 3 min 05 s », « 1 h 20 min » ; « — » quand la durée n'est pas encore estimable."""
    if s is None:
        return '—'
    s = int(round(max(0.0, float(s))))
    if s < 60:
        return tr('duree_s', n=s)
    if s < 3600:
        return tr('duree_min', n=s // 60, s=s % 60)
    return tr('duree_h', h=s // 3600, m=(s % 3600) // 60)
