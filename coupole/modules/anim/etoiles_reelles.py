"""Étoiles réelles dessinées par les animations (Grande Ourse 3D, horloge de la Grande Ourse, lever héliaque,
comparaison des repères, diagramme HR) : identifiant de leur fiche au survol, T_eff et couleur vraie (corps noir →
CIE 1931 → sRGB, couleur_etoile.py), distance (al) mise à jour.  Données : SIMBAD, Gaia DR3, Hipparcos 2007 (requêtes
du 14/10/2026) ; même fichier que Coupole Web (src/anim/etoiles_reelles.ts)."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from PyQt6.QtGui import QColor

from .couleur_etoile import couleur_etoile, rvb_hex

with gzip.open(Path(__file__).with_name('donnees') / 'etoiles_reelles.json.gz', 'rt', encoding='utf-8') as _f:
    _A = json.load(_f)['animations']


def reelle(anim: str, cle: str) -> dict | None:
    """L'étoile `cle` de l'animation `anim` (ex. « bigdipper », « Merak ») : fiche, teff, al, al_moins, al_plus."""
    ligne = _A.get(anim, {}).get(cle)
    if not ligne:
        return None
    return {'fiche': ligne[0], 'teff': ligne[1], 'al': ligne[3], 'al_moins': ligne[4], 'al_plus': ligne[5]}


def couleur_reelle(anim: str, cle: str) -> QColor | None:
    """Couleur vraie de l'étoile (T_eff publiée → corps noir → CIE), ou None si elle n'a pas de T_eff."""
    ligne = _A.get(anim, {}).get(cle)
    if not ligne:
        return None
    if ligne[1] is not None:
        return QColor(*couleur_etoile(ligne[1]))
    if ligne[2]:
        return QColor(*rvb_hex(ligne[2]))
    return None
