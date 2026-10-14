"""Fiches au survol (étoiles et nébuleuses) : chargées à la première demande.  Chaque valeur porte sa source (SIMBAD,
Gaia DR3, Hipparcos 2007, article) ; même fichier que Coupole Web (src/anim/fiches.ts)."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

_DONNEES: dict | None = None


def _charger() -> dict:
    global _DONNEES
    if _DONNEES is None:
        with gzip.open(Path(__file__).with_name('donnees') / 'fiches.json.gz', 'rt', encoding='utf-8') as f:
            _DONNEES = json.load(f)
    return _DONNEES


def fiche(ident: str) -> dict | None:
    """Fiche d'identifiant `ident`, ou None."""
    return _charger()['fiches'].get(ident)


def toutes_les_fiches() -> dict:
    return _charger()['fiches']
