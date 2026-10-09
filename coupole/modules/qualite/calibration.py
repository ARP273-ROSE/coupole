"""Seules les poses de ciel (lights) sont mesurées : poses de calibration et fichiers intermédiaires exclus.

Trois niveaux, du moins cher au plus cher :

1. **Dossier** (à l'inventaire, sans rien ouvrir) : un dossier du chemin, sous le dossier analysé, nommé
   (ou commençant par) Flat(s), Dark(s), Bias, Offset(s), DarkFlat(s), FlatDark(s), Calibration, Master(s) —
   « FLAT L », « Dark-Bias » —, ou cosmetized, calibrated, registered, debayered, aligned, _platesolve…
   (casse et pluriels, français compris : Plats, Noirs, Biais) ;
2. **Nom de fichier** (à l'inventaire) : préfixes et suffixes de N.I.N.A. (`FLAT_`, `DARK_`, `BIAS_`, `DARKFLAT_`),
   de l'ASIAIR (`Flat_`, `Dark_`, `Bias_`), des masters PixInsight/Siril (`masterDark_`, `masterFlat`,
   `masterLight`, `superbias`), des sorties de WBPP (`_c`, `_cc`, `_d`, `_r` et leurs enchaînements,
   `integration`, `drizzle`) — même famille que l'expression d'exclusion d'astrosolver ;
3. **En-tête** (pendant la mesure, le fichier étant ouvert de toute façon) : `IMAGETYP`, `FRAME` ou la propriété
   XISF `Observation:Image:Type` qui désigne une pose de calibration ou un master (flat, dark, bias, offset,
   zero, master…) → « exclu (calibration) » ; Light, Light Frame, Science, Object (ou absent) → mesuré.

`Inclure aussi les poses de calibration` (interface) / `--avec-calibration` (ligne de commande) : rien n'est exclu.
"""
from __future__ import annotations

import os
import re

# 1. dossiers (un composant entier du chemin)
# (premier mot du nom : « Flats », « FLAT L », « Dark-Bias », « master OSC » ; « Nuit_2_master » n'en est pas)
RE_DOSSIER = re.compile(
    r'(?i)^(?:'
    r'(?:flats?|darks?|bias(?:es)?|offsets?|dark[ _-]?flats?|flat[ _-]?darks?|calibrations?|calib|masters?|'
    r'plats?|noirs?|biais)(?:[ _.-].*)?|'
    r'cosmeti[sz]ed|calibrated|registered|debayered|aligned|integrations?|drizzled?|'
    r'_?platesolve.*|pr[eé]traitements?'
    r')$')

# 2. noms de fichiers (préfixes de calibration, masters, sorties de WBPP) ; casse indifférente sauf les suffixes
# WBPP, toujours en minuscules (« M31_R.xisf » = filtre R, pas « registered »)
RE_FICHIER = re.compile(
    r'(?i)(?:'
    r'^master|_master|masterlight|^superbias|^superdark|'
    r'^flat[ _-]|^dark[ _-]|^bias[ _-]|^darkflat[ _-]|^flatdark[ _-]|^offset[ _-]|^dark[ _-]?flat[ _-]|'
    r'ln_reference|_reference_|integration|_autocrop|drizzle|'
    r'moon_[0-9.]+ms'
    r')')
RE_WBPP = re.compile(r'(?:_c|_cc|_d|_r)+(?:\.fits?\.fz|\.fits?|\.fts|\.xisf)$')

# 3. en-tête : mots qui désignent une pose de calibration ou un master
MOTS_CALIBRATION = ('flat', 'dark', 'bias', 'offset', 'zero', 'master', 'calib')


def motif_chemin(chemin: str, racine: str = '') -> str:
    """'' si le fichier est (a priori) une pose de ciel ; sinon le motif : 'dossier:<nom>' ou 'nom'."""
    try:
        rel = os.path.relpath(chemin, racine) if racine else chemin
    except ValueError:
        rel = chemin
    parties = rel.replace('\\', '/').split('/')
    for d in parties[:-1]:
        if d not in ('..', '.') and RE_DOSSIER.match(d):
            return 'dossier:' + d
    nom = parties[-1]
    if RE_FICHIER.search(nom) or RE_WBPP.search(nom):
        return 'nom'
    return ''


def motif_entete(type_image: str) -> str:
    """'' pour une pose de ciel (Light, Light Frame, Science, Object, ou type absent) ; sinon le type lu."""
    t = (type_image or '').strip().lower()
    if t and any(m in t for m in MOTS_CALIBRATION):
        return t
    return ''


def trier(fichiers, racine: str = '') -> tuple[list, list]:
    """(poses de ciel, [(fichier, motif)] exclus) d'après dossiers et noms, sans rien ouvrir."""
    gardes, exclus = [], []
    for f in fichiers:
        m = motif_chemin(f, racine)
        if m:
            exclus.append((f, m))
        else:
            gardes.append(f)
    return gardes, exclus


def texte_motif(motif: str, L: str | None = None) -> str:
    """Motif lisible (FR/EN)."""
    from ...core.i18n import tr
    if motif.startswith('dossier:'):
        return tr('qual_exclu_dossier', L, nom=motif.split(':', 1)[1])
    if motif == 'nom':
        return tr('qual_exclu_nom', L)
    return tr('qual_exclu_entete', L, type=motif.split(':', 1)[-1])
