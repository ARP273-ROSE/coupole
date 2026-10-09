"""Ligne de commande de Coupole : tout ce que fait l'interface, sans interface.

    coupole                          interface graphique (si un écran est disponible)
    coupole --lang en ohp catalog    même chose en anglais
    coupole ohp traiter "NGC 6888" --nuit 2025-07-16 --dest ~/OHP
    coupole astap --guide
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from . import __version__
from .core import config, i18n
from .core.i18n import tr


def _langue_argv(argv) -> str | None:
    for i, a in enumerate(argv):
        if a in ('--lang', '--langue') and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith(('--lang=', '--langue=')):
            return a.split('=', 1)[1]
    return None


def initialiser(langue: str | None = None):
    """Langue, textes du cœur, modules.  Commun à la CLI et à l'interface."""
    from . import textes, textes_enligne
    i18n.enregistrer(textes.TEXTES)
    i18n.enregistrer(textes_enligne.TEXTES)
    choix = langue or config.reglages()['langue'] or 'auto'
    i18n.choisir_langue(choix)
    from .core import modules
    return modules.decouvrir()


class Formateur(argparse.RawDescriptionHelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=34, width=100)


def _traduire_argparse():
    """Les quelques mots qu'argparse écrit lui-même (usage, options...)."""
    import gettext as _g
    mots = {'usage: ': tr('argparse_usage'), 'options': tr('argparse_options'),
            'positional arguments': tr('argparse_positionnels'),
            'show this help message and exit': tr('argparse_aide'),
            'the following arguments are required: %s': tr('argparse_requis'),
            'invalid choice: %(value)r (choose from %(choices)s)': tr('argparse_choix'),
            'unrecognized arguments: %s': tr('argparse_inconnus'),
            '%(prog)s: error: %(message)s\n': tr('argparse_erreur')}
    argparse._ = lambda s: mots.get(s, s)  # type: ignore[attr-defined]
    _g.gettext  # noqa: B018


def construire_parseur(mods) -> argparse.ArgumentParser:
    _traduire_argparse()
    p = argparse.ArgumentParser(prog='coupole', description=tr('cli_description'), formatter_class=Formateur,
                                epilog=tr('cli_epilogue'))
    p.add_argument('--version', action='version', version='Coupole %s' % __version__, help=tr('cli_aide_version'))
    p.add_argument('--lang', '--langue', choices=['auto', 'fr', 'en'], help=tr('cli_aide_langue'))
    p.add_argument('-v', '--verbeux', '--verbose', action='store_true', help=tr('cli_aide_verbeux'))
    p.add_argument('--reinitialiser-interface', '--reset-interface', action='store_true',
                   help=tr('cli_aide_reinit_interface'))
    sous = p.add_subparsers(dest='commande', metavar=tr('cli_commande'), title=tr('cli_commandes'))

    g = sous.add_parser('gui', help=tr('cli_gui'), description=tr('cli_gui'), formatter_class=Formateur)
    g.set_defaults(fonction=lambda a: _gui())

    a = sous.add_parser('astap', help=tr('cli_astap'), description=tr('cli_astap_desc'), formatter_class=Formateur)
    a.add_argument('--guide', action='store_true', help=tr('cli_astap_guide'))
    a.add_argument('--definir', '--set', metavar=tr('cli_meta_chemin'), help=tr('cli_astap_definir'))
    a.add_argument('--catalogue', '--catalog', metavar=tr('cli_meta_dossier'), help=tr('cli_astap_catalogue'))
    a.add_argument('--oublier', '--forget', action='store_true', help=tr('cli_astap_oublier'))
    a.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    a.set_defaults(fonction=cmd_astap)

    r = sous.add_parser('rapports', aliases=['reports'], help=tr('cli_rapports'), description=tr('cli_rapports_desc'),
                        formatter_class=Formateur)
    grp = r.add_mutually_exclusive_group()
    grp.add_argument('--activer', '--enable', action='store_true', help=tr('cli_rapports_activer'))
    grp.add_argument('--desactiver', '--disable', action='store_true', help=tr('cli_rapports_desactiver'))
    r.set_defaults(fonction=cmd_rapports)

    m = sous.add_parser('maj', aliases=['update'], help=tr('cli_maj'), description=tr('cli_maj_desc'),
                        formatter_class=Formateur)
    m.add_argument('--appliquer', '--apply', action='store_true', help=tr('cli_maj_appliquer'))
    m.set_defaults(fonction=cmd_maj)

    so = sous.add_parser('sources', help=tr('cli_sources'), description=tr('cli_sources_desc'),
                         formatter_class=Formateur)
    so.add_argument('--forcer', '--set', nargs=2, metavar=(tr('cli_meta_cle'), tr('cli_meta_valeur')),
                    help=tr('cli_sources_forcer'))
    so.add_argument('--defaut', '--default', metavar=tr('cli_meta_cle'), help=tr('cli_sources_defaut'))
    so.add_argument('--tout-reinitialiser', '--reset-all', action='store_true', help=tr('cli_sources_reinit'))
    so.add_argument('--tester', '--test', metavar=tr('cli_meta_cle'), help=tr('cli_sources_tester'))
    so.add_argument('--distant', '--remote', action='store_true', help=tr('cli_sources_distant'))
    so.set_defaults(fonction=cmd_sources)

    ls = sous.add_parser('modules', help=tr('cli_modules'), description=tr('cli_modules'), formatter_class=Formateur)
    ls.set_defaults(fonction=lambda a: cmd_modules(a, mods))

    mn = sous.add_parser('manuel', aliases=['manual'], help=tr('cli_manuel'), description=tr('cli_manuel'),
                         formatter_class=Formateur)
    mn.set_defaults(fonction=cmd_manuel)

    for mod in mods:
        try:
            f = mod.fonction_cli()
        except Exception as e:  # module défectueux : signalé, jamais bloquant
            logging.getLogger(__name__).warning('module %s CLI: %s', mod.id, e)
            continue
        if f is None:
            continue
        sp = sous.add_parser(mod.id, help=mod.nom_local() + ' — ' + mod.description_locale(),
                             description=mod.description_locale(), formatter_class=Formateur)
        f(sp)
    return p


# ======================================================================== commandes du cœur
def cmd_astap(a):
    from .core import astap
    r = config.reglages()
    if a.oublier:
        r['astap_executable'] = ''
        r['astap_catalogue'] = ''
    if a.definir:
        r['astap_executable'] = os.path.abspath(os.path.expanduser(a.definir))
    if a.catalogue:
        r['astap_catalogue'] = os.path.abspath(os.path.expanduser(a.catalogue))
    e = astap.detecter(r['astap_executable'], r['astap_catalogue'])
    if a.json:
        d = dict(e.__dict__)
        d['utilisable'] = e.utilisable
        d['conseils'] = astap.conseils_installation()
        print(json.dumps(d, indent=1, ensure_ascii=False))
        return 0
    print(tr('astap_titre'))
    print('  ' + tr(e.message_cle()))
    print('  %s : %s' % (tr('astap_executable'), e.executable or '—'))
    if e.version:
        print('  %s : %s' % (tr('astap_version'), e.version))
    print('  %s : %s' % (tr('astap_catalogue'), ('%s (%d %s) — %s' % (e.catalogue.upper(), e.catalogue_fichiers,
                                                                      tr('astap_tuiles'), e.catalogue_dossier))
                         if e.catalogue else '—'))
    if not e.utilisable:
        print('\n' + tr('astap_sans_effet'))
    if a.guide or not e.utilisable:
        print()
        print(guide_astap_texte())
    return 0


def guide_astap_texte() -> str:
    from .core import astap
    c = astap.conseils_installation()
    l = [tr('astap_guide_titre', systeme=tr('os_' + c['systeme']), arch=c['arch'],
            famille=(' (' + c['famille'] + ')') if c['famille'] else ''),
         tr('astap_guide_pourquoi'), '', tr('astap_guide_catalogue'), '']
    n = 1
    l.append('%d. %s' % (n, tr('astap_guide_programme')))
    for cle, url in c['programme']:
        l.append('     %s : %s' % (tr(cle), url))
    if c['cli'] and all(url != c['cli'] for _, url in c['programme']):
        l.append('     %s : %s' % (tr('astap_lien_cli_zip'), c['cli']))
    n += 1
    l.append('%d. %s' % (n, tr('astap_guide_cat')))
    for cle, url in c['catalogue']:
        l.append('     %s : %s' % (tr(cle), url))
    for etape in c['etapes']:
        n += 1
        l.append('%d. %s' % (n, tr(etape, dossier=c['dossier'])))
    for note in c.get('notes', ()):
        l += ['', tr(note)]
    l += ['', tr('astap_guide_detection'), tr('astap_guide_page', page=c['page'])]
    return '\n'.join(l)


def cmd_sources(a):
    from .core import sources
    if a.forcer:
        sources.forcer(a.forcer[0], a.forcer[1])
    if a.defaut:
        sources.forcer(a.defaut, None)
    if a.tout_reinitialiser:
        sources.tout_reinitialiser()
    if a.distant:
        print(tr('sources_distant_ok' if sources.rafraichir_distant() else 'sources_distant_non'))
    if a.tester:
        ok, msg = sources.tester(a.tester)
        print(tr('sources_test_ok' if ok else 'sources_test_echec', cle=a.tester, detail=msg))
        return 0 if ok else 1
    for cle, (val, origine) in sources.toutes().items():
        print('%-26s %-12s %s' % (cle, tr('sources_origine_' + origine), val or '—'))
    return 0


def cmd_rapports(a):
    from .core import rapports
    if a.activer:
        rapports.definir_consentement(True)
    elif a.desactiver:
        rapports.definir_consentement(False)
    c = rapports.consentement()
    print(tr('rapports_etat_' + ('oui' if c is True else 'non' if c is False else 'inconnu')))
    print(tr('rapports_dossier', dossier=str(config.dossier_config() / '_rapports')))
    return 0


def cmd_maj(a):
    from .core import maj
    print(tr('maj_verification', depot=maj.depot()))
    m = maj.verifier(__version__)
    if not m:
        print(tr('maj_aucune', version=__version__))
        return 0
    print(tr('maj_disponible', version=m['version']))
    print(maj.notes_dans_la_langue(m['notes'], i18n.langue())[:2000])
    genre = maj.type_installation()
    if genre == 'pip':
        print(tr('maj_pip', commande=maj.commande_pip()))
        return 0
    if genre != 'paquet':                       # .deb ou dossier non inscriptible : on indique, on ne touche à rien
        c = maj.consigne_systeme(m)
        print(tr('maj_systeme', url=c['url'], commande=c['commande']))
        return 0
    if a.appliquer:
        maj.appliquer(m)
        print(tr('maj_faite'))
    else:
        print(tr('maj_appliquer_cli'))
    return 0


def cmd_modules(a, mods):
    from .core import modules
    for m in mods:
        print('%-10s %-8s %-28s %s' % (m.id, m.version, m.nom_local(), m.description_locale()))
    for paquet, err in modules.erreurs:
        print(tr('modules_erreur', paquet=paquet, erreur=err))
    return 0


def chemin_manuel() -> str:
    from pathlib import Path
    racine = Path(__file__).resolve().parent / 'docs'
    for nom in ('manuel_%s.pdf' % i18n.langue(), 'manuel_en.pdf', 'manuel_fr.pdf'):
        if (racine / nom).exists():
            return str(racine / nom)
    return ''


def cmd_manuel(a):
    p = chemin_manuel()
    print(p or tr('manuel_absent'))
    return 0 if p else 1


def _gui():
    try:
        from .gui.app import main as gui_main
    except ImportError as e:
        print(tr('gui_indisponible', erreur=str(e)), file=sys.stderr)
        return 2
    return gui_main()


def console_tolerante():
    """Console qui ne sait pas tout afficher (Windows cp1252, LANG=C) : remplacer au lieu de planter."""
    for flux in (sys.stdout, sys.stderr):
        try:
            if flux is not None and hasattr(flux, 'reconfigure') and (flux.encoding or '').lower() not in ('utf-8', 'utf8'):
                flux.reconfigure(errors='replace')
        except (AttributeError, ValueError, OSError):
            pass


def main(argv=None) -> int:
    console_tolerante()
    argv = list(sys.argv[1:] if argv is None else argv)
    mods = initialiser(_langue_argv(argv))
    if not argv:
        return _gui()
    p = construire_parseur(mods)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.verbeux else logging.WARNING, format='%(levelname)s %(message)s')
    if a.lang:
        i18n.choisir_langue(a.lang)
    if a.reinitialiser_interface:
        from .core import etat_interface
        if etat_interface.effacer_fichier():
            print(tr('cli_reinit_interface_fait', chemin=str(config.dossier_config() / etat_interface.NOM_FICHIER)))
        else:
            print(tr('cli_reinit_interface_rien'))
        return 0
    if not getattr(a, 'fonction', None):
        p.print_help()
        return 0
    from .core import rapports
    rapports.init()
    try:
        return a.fonction(a) or 0
    except KeyboardInterrupt:
        print('\n' + tr('interrompu'), file=sys.stderr)
        return 130
