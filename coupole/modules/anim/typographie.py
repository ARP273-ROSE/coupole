"""Typographie commune des ressources et des applis (copie du formateur commun ; même comportement que
src/noyau/typographie.ts de Coupole Web, mêmes cas de test : tests/typographie_cas.json).

- unite("km s-1 Mpc-1") → « km·s⁻¹·Mpc⁻¹ » (notation SI à exposants, point médian) ;
- nombre(x, lg, decimales) → virgule décimale en français, point en anglais, espace fine insécable (U+202F) entre
  les milliers à partir de 5 chiffres, vrai signe moins « − » ;
- sci(x, lg, chiffres) → « 6,674 × 10⁻¹¹ » ;
- normaliser(texte) → espaces de milliers transformées en espaces fines insécables ;
- controle(texte, lg) → liste des fautes typographiques (texte affiché, formules $…$ exclues sauf mention)."""
from __future__ import annotations

import math
import re

FINE = ' '
_SUP = str.maketrans('0123456789-+', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺')


def unite(code: str) -> str:
    """« kg m-3 » → « kg·m⁻³ » ; « m3 s-2 » → « m³·s⁻² »."""
    out = []
    for f in code.split():
        m = re.fullmatch(r'([^\d\-+]+)([-+]?\d+)?', f)
        if not m:
            raise ValueError(f'facteur d\'unité illisible : {f}')
        base, exp = m.groups()
        out.append(base + (exp.replace('+', '').translate(_SUP) if exp and exp != '1' else ''))
    return '·'.join(out)


def _grouper(ent: str) -> str:
    if len(ent) < 5:
        return ent
    g = []
    while ent:
        g.insert(0, ent[-3:])
        ent = ent[:-3]
    return FINE.join(g)


def nombre(x: float, lg: str = 'fr', decimales: int = 0) -> str:
    s = f'{abs(x):.{decimales}f}'
    ent, _, dec = s.partition('.')
    r = _grouper(ent) + ((',' if lg == 'fr' else '.') + dec if dec else '')
    return ('−' if x < 0 and float(s) != 0 else '') + r


def sci(x: float, lg: str = 'fr', chiffres: int = 3) -> str:
    if x == 0:
        return '0'
    e = math.floor(math.log10(abs(x)))
    m = x / 10 ** e
    if round(abs(m), chiffres - 1) >= 10:
        e += 1
        m = x / 10 ** e
    t = nombre(m, lg, chiffres - 1)
    return t if e == 0 else f'{t} × 10{str(e).translate(_SUP)}'


_MILLIERS = re.compile(r'(?<![\d,.])(\d{1,3})((?: \d{3})+)(?![\d])')


def normaliser(texte: str) -> str:
    return _MILLIERS.sub(lambda m: m.group(1) + m.group(2).replace(' ', FINE), texte)


_UNITE_BARRE = re.compile(r'(?<![\w])(k?m|cm|mm|µm|nm|k?g|W|k?J|N|Pa|eV|K|lbf?|ft|″|k?pc|Mpc|ua|au)\s?/\s?'
                          r'(s|s²|h|m|m²|m³|cm²|cm³|K|an|yr|Mpc|kpc|ft³|n²|j|d)(?![\w])')


def _hors_formules(t: str) -> str:
    return re.sub(r'\$[^$]*\$', ' ', t)


def controle(texte: str, lg: str = 'fr') -> list[str]:
    pb = []
    t = _hors_formules(texte)
    if _UNITE_BARRE.search(t):
        pb.append(f'unité écrite avec une barre oblique « {_UNITE_BARRE.search(t).group(0)} » (écrire m·s⁻¹)')
    if re.search(r'[A-Za-zα-ω]_\(?[A-Za-z0-9]', t):
        pb.append('indice écrit avec « _ » hors formule (utiliser $…$ ou les indices Unicode)')
    if re.search(r'\^', t):
        pb.append('puissance écrite avec « ^ » hors formule (utiliser les exposants ou $…$)')
    if re.search(r'\d[eE][−+-]?\d', t):
        pb.append('notation informatique « e-11 » (écrire × 10⁻¹¹)')
    if re.search(r'(?<![\w\-–])-\s?\d', t) or re.search(r'\d\s-\s\d', t):
        pb.append('tiret « - » utilisé comme signe moins (écrire −)')
    if re.search(r'\d\s?[x*]\s?\d', t):
        pb.append('« x » ou « * » comme multiplication (écrire ×)')
    pt = re.search(r'(?<![\w.])\d+\.\d+(?![\w.])', t)
    if lg == 'fr' and pt:
        pb.append(f'point décimal en français « {pt.group(0)} »')
    if lg == 'en' and re.search(r'(?<![\w,])\d+,(\d{1,2}|\d{4,})(?![\d])', t):
        pb.append('virgule décimale en anglais')
    if re.search(r'(?<![\d,.])\d{1,3}(?: \d{3})+(?!\d)', t):
        pb.append('milliers séparés par une espace ordinaire (espace fine insécable attendue)')
    return pb
