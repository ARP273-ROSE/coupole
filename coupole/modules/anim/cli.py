"""coupole anim liste [--faites] [--json] | coupole anim info ID"""
from __future__ import annotations

import json
import sys

from ...core.i18n import tr
from . import catalogue


def enregistrer(p):
    sp = p.add_subparsers(dest='anim_cmd')
    l = sp.add_parser('liste', help=tr('anim_cli_liste'))
    l.add_argument('--faites', action='store_true', help=tr('anim_cli_faites'))
    l.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    l.set_defaults(fonction=cmd_liste)
    i = sp.add_parser('info', help=tr('anim_cli_info'))
    i.add_argument('ident', metavar=tr('anim_cli_meta_id'), help=tr('anim_cli_id'))
    i.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    i.set_defaults(fonction=cmd_info)
    p.set_defaults(fonction=cmd_liste, faites=False, json=False)


def _dict(e):
    return {'id': e.id, 'theme': e.theme, 'titre_origine': e.titre, 'nom': tr('anim_nom_' + e.cle),
            'description': tr('anim_desc_' + e.cle), 'disponible': e.faite, 'fichier_origine': e.fichier}


def cmd_liste(a):
    entrees = [e for e in catalogue.ENTREES if e.faite or not a.faites]
    if a.json:
        print(json.dumps([_dict(e) for e in entrees], ensure_ascii=False, indent=1))
        return 0
    for t in catalogue.THEMES:
        sel = [e for e in entrees if e.theme == t]
        if not sel:
            continue
        print('== %s' % tr('anim_theme_' + t))
        for e in sel:
            print('  [%s] %-30s %s' % ('x' if e.faite else ' ', e.id, tr('anim_nom_' + e.cle)))
    print(tr('anim_compte', faites=len(catalogue.faites()), total=len(catalogue.ENTREES)))
    return 0


def cmd_info(a):
    e = catalogue.PAR_ID.get(a.ident) or next((x for x in catalogue.ENTREES if x.cle == a.ident.lower()), None)
    if e is None:
        print(tr('anim_cli_inconnue', id=a.ident), file=sys.stderr)
        return 1
    d = _dict(e)
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0
    print('%s — %s' % (d['nom'], tr('anim_disponible' if e.faite else 'anim_a_venir')))
    print(d['description'])
    print(tr('anim_titre_origine', titre=e.titre))
    print(tr('anim_theme_de', theme=tr('anim_theme_' + e.theme)))
    return 0
