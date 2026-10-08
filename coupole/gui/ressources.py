"""Icônes de l'application."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon

DOSSIER = Path(__file__).resolve().parent.parent / 'ressources'


def icone_application() -> QIcon:
    ic = QIcon()
    for nom in ('coupole.svg', 'coupole_256.png', 'coupole_64.png'):
        p = DOSSIER / nom
        if p.exists():
            ic.addFile(str(p))
    return ic
