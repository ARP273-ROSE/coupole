"""Écrit les tableaux LaTeX des commandes et options (docs/manuel/gen_cli_<langue>.tex) à partir des vrais
analyseurs argparse : le manuel ne peut pas diverger de la ligne de commande.

    python outils/tables_cli.py
"""
import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))


def tex(s: str) -> str:
    rep = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{',
           '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}', '«': r'«', '»': r'»'}
    return ''.join(rep.get(c, c) for c in str(s))


def options(p):
    out = []
    for a in p._actions:
        if isinstance(a, (argparse._HelpAction, argparse._SubParsersAction)):
            continue
        noms = ', '.join(a.option_strings) if a.option_strings else (a.metavar or a.dest)
        if a.choices and not isinstance(a.choices, dict):
            noms += ' {%s}' % ','.join(str(c) for c in a.choices)
        elif a.option_strings and a.nargs != 0 and not isinstance(a, (argparse._StoreTrueAction,
                                                                      argparse._StoreConstAction)):
            mv = a.metavar if isinstance(a.metavar, str) else (' '.join(a.metavar) if a.metavar else a.dest.upper())
            noms += ' ' + mv
        out.append((noms, a.help or ''))
    return out


def sous_parseurs(p):
    for a in p._actions:
        if isinstance(a, argparse._SubParsersAction):
            vus = set()
            for nom, sp in a.choices.items():
                if id(sp) in vus:
                    continue
                vus.add(id(sp))
                alias = [k for k, v in a.choices.items() if v is sp and k != nom]
                yield nom, alias, sp


def tableau(titre, lignes, f, description=''):
    if not lignes:
        return
    f.write('\\begin{tabularx}{\\linewidth}{@{}>{\\ttfamily\\small\\raggedright}p{0.38\\linewidth}X@{}}\n\\toprule\n')
    f.write('\\multicolumn{2}{@{}p{\\linewidth}@{}}{\\sffamily\\bfseries %s%s}\\\\\n\\midrule\n'
            % (tex(titre), ('\\newline\\normalfont\\small ' + tex(description)) if description else ''))
    for a, b in lignes:
        f.write('%s & %s\\\\\n' % (tex(a).replace(',', ',\\allowbreak{}'), tex(b)))
    f.write('\\bottomrule\n\\end{tabularx}\n\\par\\medskip\n')


def generer(langue):
    from coupole import cli
    from coupole.core import i18n, modules
    mods = cli.initialiser(langue)
    i18n.choisir_langue(langue)
    modules.decouvrir(recharger=True)
    p = cli.construire_parseur(modules.decouvrir())
    chemin = RACINE / 'docs' / 'manuel' / ('gen_cli_%s.tex' % langue)
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write('% Généré par outils/tables_cli.py — ne pas modifier à la main.\n')
        tableau('coupole', options(p), f)
        for nom, alias, sp in sous_parseurs(p):
            entete = 'coupole %s%s' % (nom, (' (' + ', '.join(alias) + ')') if alias else '')
            sous = list(sous_parseurs(sp))
            if sous:
                for n2, a2, sp2 in sous:
                    tableau('%s %s%s' % (entete, n2, (' (' + ', '.join(a2) + ')') if a2 else ''), options(sp2), f,
                            sp2.description or '')
            else:
                tableau(entete, options(sp), f, sp.description or '')
    print('écrit', chemin)


if __name__ == '__main__':
    for l in ('fr', 'en'):
        generer(l)
