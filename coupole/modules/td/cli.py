"""coupole td parallaxe --p1 POSITION --h1 ANGLE [--az1 ANGLE] [--alt1 M] --p2 … --h2 … [--cible iss|lune]
[--instant AAAA-MM-JJTHH:MM:SS] [--json] : le calculateur « Parallaxe (TP du cours) » en ligne de commande."""
from __future__ import annotations

import json
import sys

from ...core.i18n import tr


def enregistrer(p):
    sous = p.add_subparsers(dest='td_commande', metavar=tr('cli_commande'), title=tr('cli_commandes'))
    s = sous.add_parser('parallaxe', aliases=['parallax'], help=tr('td_cli_parallaxe'),
                        description=tr('td_cli_parallaxe'), formatter_class=p.formatter_class)
    for n in (1, 2):
        s.add_argument('--p%d' % n, required=True, metavar=tr('td_meta_texte'), help=tr('td_cli_p', n=n))
        s.add_argument('--h%d' % n, required=True, metavar=tr('td_meta_texte'), help=tr('td_cli_h', n=n))
        s.add_argument('--az%d' % n, default='', metavar=tr('td_meta_texte'), help=tr('td_cli_az', n=n))
        s.add_argument('--alt%d' % n, default='', metavar=tr('td_meta_texte'), help=tr('td_cli_alt', n=n))
    s.add_argument('--cible', '--target', choices=('iss', 'lune', 'moon'), default='iss', help=tr('td_cli_cible'))
    s.add_argument('--instant', default='', metavar=tr('td_meta_texte'), help=tr('td_cli_instant'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_parallaxe)


def cmd_parallaxe(a):
    import datetime as D

    from . import coordonnees as K
    from . import parallaxe_tp as T
    from .presentation import etapes
    try:
        lieux = []
        for n in (1, 2):
            pos = K.lire_position(getattr(a, 'p%d' % n))
            az = getattr(a, 'az%d' % n)
            lieux.append(T.Lieu(pos.lat, pos.lon, K.lire_altitude(getattr(a, 'alt%d' % n)),
                                K.lire_angle(getattr(a, 'h%d' % n)).valeur, K.lire_angle(az).valeur if az else None))
        inst = None
        if a.instant:
            from ..partages.mesures import instant
            inst = instant(a.instant + ' UTC').valeur
        cible = 'lune' if a.cible in ('lune', 'moon') else 'iss'
        tle = None
        if inst is not None and cible == 'iss':
            from . import tle as TL
            tle = TL.pour(inst)['tle']
        e = T.Entrees(lieux[0], lieux[1], cible, inst, tle)
        r = T.calculer(e)
    except (K.CoordonneeIllisible, T.ErreurTP) as ex:
        print(tr(ex.cle, **ex.valeurs), file=sys.stderr)
        return 2
    if a.json:
        r.pop('lieux', None)
        print(json.dumps(r, ensure_ascii=False, indent=1, default=lambda o: o.isoformat()
                         if isinstance(o, D.datetime) else str(o)))
        return 0
    for k, (titre, texte) in enumerate(etapes(e, r), 1):
        print('%d. %s\n   %s' % (k, titre, texte))
    for cle, v in r['alertes']:
        print('! ' + tr(cle, **v))
    return 0
