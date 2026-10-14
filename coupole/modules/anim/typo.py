"""Règle typographique appliquée aux textes affichés par les animations (src/noyau/typo.ts de Coupole Web, mêmes cas
de référence : tests/typographie_reference.json), sur le formateur commun aux ressources et aux applis
(typographie.py : unite, nombre, sci, normaliser, controle ; cas : tests/typographie_cas.json) : unités à la manière SI
(m·s⁻¹, km·s⁻¹, m·s⁻², W·m⁻², g·cm⁻³, J·K⁻¹… — jamais « m/s »), signe moins typographique (−, U+2212), puissances de
dix en exposant (10⁻¹¹, jamais « 10^-11 » ni « e-11 »).

* ``typo(s)`` corrige un texte affiché (filet de sécurité : les sources sont déjà écrites ainsi) ;
* ``interdit(s)`` dit si un texte affiché enfreint la règle (tests de toutes les animations)."""
from __future__ import annotations

import re

from .typographie import unite

MOINS = '−'
EXPOSANTS = str.maketrans('0123456789-+', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺')

# unités composées (barre oblique → exposants négatifs), du plus long au plus court
UNITES = (
    ('km/s/Mpc', unite('km s-1 Mpc-1')),
    ('m/s²', unite('m s-2')), ('m/s2', unite('m s-2')),
    ('km/s', unite('km s-1')), ('m/s', unite('m s-1')),
    ('W/m²', unite('W m-2')), ('W/m2', unite('W m-2')),
    ('g/cm³', unite('g cm-3')), ('g/cm3', unite('g cm-3')),
    ('kg/m³', unite('kg m-3')), ('kg/m3', unite('kg m-3')),
    ('J/K', unite('J K-1')),
    ('ph/s', unite('ph s-1')),
    ('ans/s', unite('a s-1')), ('years/s', unite('a s-1')),
    ('″/an', unite('″ a-1')), ('″/yr', unite('″ a-1')),
)
_RE_UNITES = re.compile('(?<![A-Za-z])(' + '|'.join(re.escape(u) for u, _ in UNITES) + ')(?![A-Za-z0-9])')
_TABLE_UNITES = dict(UNITES)
# « - » utilisé comme signe moins : en début de texte ou après un espace, une parenthèse, un signe, devant un chiffre
_RE_MOINS = re.compile(r'(^|[\s(\[{=:;,≈~<>±→])-(?=\.?\d)')
_RE_PUISSANCE = re.compile(r'10\^([-+]?\d+)')

_INTERDITS = (
    re.compile(r'(?<![A-Za-z])(?:k?m|W|g|kg|J|ph|ans|years|″)\s?/\s?(?:s|m|cm|K|an|yr)(?![A-Za-z])'),
    re.compile(r'/s(?![A-Za-z])'),
    re.compile(r'10\^'),
    re.compile(r'\d[eE][-+]?\d'),
    _RE_MOINS,
)


def typo(s: str) -> str:
    """Le texte selon la règle typographique : unités SI, signe moins, puissances de dix."""
    # chemin rapide (appelé pour chaque texte de la toile) : rien à corriger sans « - », « / » ni « ^ »
    if not s or ('-' not in s and '/' not in s and '^' not in s):
        return s
    s = _RE_UNITES.sub(lambda m: _TABLE_UNITES[m.group(1)], s)
    s = _RE_PUISSANCE.sub(lambda m: '10' + m.group(1).translate(EXPOSANTS), s)
    return _RE_MOINS.sub(lambda m: m.group(1) + MOINS, s)


def interdit(s: str) -> bool:
    """Vrai si le texte contient « m/s », « /s », « 10^ », « e-11 » ou un « - » utilisé comme signe moins."""
    return any(r.search(s) for r in _INTERDITS) if s else False
