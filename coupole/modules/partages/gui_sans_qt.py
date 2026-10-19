"""Textes communs à l'interface et à la ligne de commande (sans Qt)."""
from __future__ import annotations

from ...core.i18n import tr


def texte_anomalie(a) -> str:
    v = {k: ('' if x is None else x) for k, x in a.valeurs.items()}
    return tr(a.cle, **v)


def texte_droits(droits: list) -> str:
    t = tr('pt_droits') + ' ' + (', '.join(tr('pt_droit_' + d) for d in droits) or tr('pt_droit_aucun'))
    if 'supprimer' in droits or 'renommer' in droits or 'deplacer' in droits:
        t += '\n' + tr('pt_attention') + ' ' + tr('pt_droit_suppression')
    return t
