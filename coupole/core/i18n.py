"""Système de traduction FR/EN de Coupole.

Toute chaîne visible par l'utilisateur (interface, ligne de commande, messages,
fichiers LOT.txt...) passe par ``tr(cle, **valeurs)``.  Les textes vivent dans
des dictionnaires ``{cle: {'fr': ..., 'en': ...}}`` déclarés par le cœur
(``coupole.textes``) et par chaque module (``textes.py`` du module), enregistrés
avec ``enregistrer()``.

Translation system: every user-visible string goes through ``tr(key, **values)``.
"""
from __future__ import annotations

import locale
import os
import sys

LANGUES = {'fr': 'Français', 'en': 'English'}
LANGUE_DEFAUT = 'en'          # langue non traduite (de, es...) -> anglais

_courante = 'en'
_textes: dict[str, dict[str, str]] = {}


class CleEnDouble(ValueError):
    """Deux dictionnaires déclarent la même clé avec des textes différents."""


def enregistrer(textes: dict) -> None:
    """Ajoute un dictionnaire de traductions (appelé par le cœur et les modules)."""
    for cle, entree in textes.items():
        if cle in _textes and _textes[cle] != entree:
            raise CleEnDouble(cle)
        _textes[cle] = entree


def toutes_les_cles() -> dict:
    return dict(_textes)


def detecter_langue() -> str:
    """Langue du système, restreinte à celles qui sont traduites.

    Ordre : variables d'environnement (Linux, macOS, et Windows sous MSYS),
    langue d'affichage de Windows, préférences macOS, puis locale du processus.
    """
    codes: list[str] = []
    for var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        val = os.environ.get(var)
        if val:
            codes.extend(val.replace(':', ',').split(','))
    if sys.platform == 'win32':
        try:
            import ctypes
            n = ctypes.windll.kernel32.GetUserDefaultUILanguage()  # type: ignore[attr-defined]
            codes.append(locale.windows_locale.get(n, ''))
        except Exception:
            pass
    if sys.platform == 'darwin':
        try:
            import subprocess
            r = subprocess.run(['defaults', 'read', '-g', 'AppleLanguages'],
                               capture_output=True, text=True, timeout=3)
            codes.extend(c.strip(' "(),\n') for c in r.stdout.split('\n'))
        except Exception:
            pass
    try:
        codes.append(locale.setlocale(locale.LC_CTYPE) or '')
    except Exception:
        pass
    for code in codes:
        code = (code or '').strip().lower().replace('-', '_')
        if not code or code in ('c', 'posix', 'c.utf_8', 'c.utf-8'):
            continue
        racine = code.split('_')[0].split('.')[0]
        if racine in LANGUES:
            return racine
    return LANGUE_DEFAUT


def choisir_langue(langue: str | None) -> str:
    """'fr', 'en', ou 'auto'/None (détection). Un code inconnu donne l'anglais."""
    global _courante
    if not langue or langue == 'auto':
        _courante = detecter_langue()
    elif langue in LANGUES:
        _courante = langue
    else:
        _courante = LANGUE_DEFAUT
    return _courante


def langue() -> str:
    return _courante


def tr(cle: str, langue_: str | None = None, **valeurs) -> str:
    """Texte traduit.  Repli : anglais, puis la clé elle-même (jamais de vide)."""
    entree = _textes.get(cle)
    if entree is None:
        texte = cle
    else:
        texte = entree.get(langue_ or _courante) or entree.get(LANGUE_DEFAUT) or cle
    if valeurs:
        try:
            texte = texte.format(**valeurs)
        except (KeyError, IndexError, ValueError):
            pass
    return texte


def bilingue(cle: str, sep: str = ' / ', **valeurs) -> str:
    """« texte FR / texte EN » : pour les fichiers partagés (LOT.txt, CSV)."""
    fr, en = tr(cle, 'fr', **valeurs), tr(cle, 'en', **valeurs)
    return fr if fr == en else fr + sep + en
