"""Petits formats partagés par la ligne de commande et l'interface (sans dépendance Qt)."""
from __future__ import annotations

from ...core.i18n import tr


def duree_lisible(s: float) -> str:
    """« 2 h 05 min », « 12 min », « 1 j 3 h »."""
    s = max(0.0, float(s))
    if s >= 86400:
        return tr('ohp_duree_j', j=int(s // 86400), h=int((s % 86400) // 3600))
    if s >= 3600:
        return tr('ohp_duree_h', h=int(s // 3600), m=int((s % 3600) // 60))
    return tr('ohp_duree_min', m=max(1, int(round(s / 60))))
