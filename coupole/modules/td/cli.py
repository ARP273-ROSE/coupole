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
    s = sous.add_parser('planifier', aliases=['plan'], help=tr('pl_cli'), description=tr('pl_cli'),
                        formatter_class=p.formatter_class)
    for n in (1, 2):
        s.add_argument('--p%d' % n, required=True, metavar=tr('td_meta_texte'), help=tr('pl_cli_p', n=n))
        s.add_argument('--alt%d' % n, default='', metavar=tr('td_meta_texte'), help=tr('td_cli_alt', n=n))
    s.add_argument('--cible', '--target', choices=('iss', 'lune', 'moon'), default='iss', help=tr('pl_cible_aide'))
    s.add_argument('--debut', '--start', default='', metavar=tr('td_meta_texte'), help=tr('pl_cli_debut'))
    s.add_argument('--jours', '--days', type=float, default=0.0, help=tr('pl_cli_jours'))
    s.add_argument('--hmin', type=float, default=20.0, help=tr('pl_hmin_aide'))
    s.add_argument('--soleil', '--sun', type=float, default=-6.0, help=tr('pl_soleil_aide'))
    s.add_argument('--ics', default='', metavar=tr('td_meta_texte'), help=tr('pl_cli_ics'))
    s.add_argument('--csv', action='store_true', help=tr('pl_csv_aide'))
    s.add_argument('--tendance', '--outlook', action='store_true', help=tr('pl_cli_tendance'))
    s.set_defaults(fonction=cmd_planifier)


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


def cmd_planifier(a):
    import datetime as D

    from . import coordonnees as K
    from . import planif as P
    from .presentation import _n
    try:
        sites = []
        for n in (1, 2):
            pos = K.lire_position(getattr(a, 'p%d' % n))
            sites.append(P.Site(pos.lat, pos.lon, K.lire_altitude(getattr(a, 'alt%d' % n))))
        cible = 'lune' if a.cible in ('lune', 'moon') else 'iss'
        debut = None
        if a.debut:
            try:
                debut = D.datetime.fromisoformat(a.debut).replace(tzinfo=D.timezone.utc)
            except ValueError:
                raise K.CoordonneeIllisible('pl_err_debut', texte=a.debut) from None
        tendance = cible == 'iss' and a.tendance
        c = P.Criteres(cible, debut, a.jours or (60.0 if tendance else 7.0 if cible == 'iss' else 60.0), a.hmin, a.soleil,
                       tendance=tendance)
        r = P.chercher_avec_tle(sites[0], sites[1], c)
    except (K.CoordonneeIllisible, P.ErreurPlanif) as ex:
        print(tr(ex.cle, **{'erreur': '', **ex.valeurs}), file=sys.stderr)
        return 2
    if a.ics:
        with open(a.ics, 'w', encoding='utf-8', newline='') as fh:
            fh.write(P.ics(r))
    if a.csv:
        sys.stdout.write(P.csv(r))
        return 0
    if not r['creneaux']:
        print(tr('pl_aucun'))
        return 0
    for c in r['creneaux']:
        mesure = ('%s°' % _n(c.parallaxe_deg, 1) if c.cible == 'iss'
                  else 'Δφ %s′ %s' % (_n(c.etoile['delta_arcmin'], 2), c.etoile['nom']))
        date = c.meilleur.strftime('%Y-%m-%d %H:%M:%S UTC')
        if c.marge_s > 120:
            date = c.meilleur.strftime('%Y-%m-%d %H:%M UTC') + ' ± %d min' % round(c.marge_s / 60)
        print(tr('pl_cli_ligne', date=date, note=round(c.note),
                 h1=_n(c.h[0], 0), h2=_n(c.h[1], 0), mesure=mesure,
                 err='—' if c.erreur_sujet_pct is None else '%s %%' % _n(c.erreur_sujet_pct, 1),
                 infos=', '.join(tr(k) for k in c.remarques)))
    for k in r.get('alertes', []):
        print(tr(k))
    return 0
