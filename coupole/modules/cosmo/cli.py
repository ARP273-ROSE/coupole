"""coupole cosmo [Z ...] [--objet NOM] [--modele planck18|planck15|wmap9|simple|perso] [--h0 --om --ok]
                [--shoes] [--sans-incertitudes] [--csv FICHIER] [--courbes ZMIN ZMAX N] [--json]"""
from __future__ import annotations

import json
import sys

from ...core.i18n import tr
from . import calcul, formats


def enregistrer(p):
    p.add_argument('z', nargs='*', metavar='Z', help=tr('cosmo_cli_z'))
    p.add_argument('--objet', '--object', metavar=tr('cosmo_meta_nom'), help=tr('cosmo_cli_objet'))
    p.add_argument('--modele', '--model', choices=list(calcul.MODELES), default='planck18', help=tr('cosmo_cli_modele'))
    p.add_argument('--h0', type=float, help=tr('cosmo_cli_h0'))
    p.add_argument('--om', type=float, help=tr('cosmo_cli_om'))
    p.add_argument('--ok', type=float, default=0.0, help=tr('cosmo_cli_ok'))
    p.add_argument('--shoes', action='store_true', help=tr('cosmo_cli_shoes'))
    p.add_argument('--sans-incertitudes', '--no-uncertainties', dest='sans_sigma', action='store_true',
                   help=tr('cosmo_cli_sans_sigma'))
    p.add_argument('--csv', metavar=tr('cli_meta_fichier'), help=tr('cosmo_cli_csv'))
    p.add_argument('--courbes', '--curves', nargs=3, type=float, metavar=('ZMIN', 'ZMAX', 'N'),
                   help=tr('cosmo_cli_courbes'))
    p.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    p.set_defaults(fonction=cmd)


def _json(d):
    return {k: v for k, v in d.items() if k != 'avertissements'} | {'avertissements': [tr(a) for a in
                                                                                         d['avertissements']]}


def cmd(a):
    zs = list(a.z)
    if a.objet:
        from ...core import enligne
        r = enligne.redshift(a.objet)
        if r['etat'] == 'ok' and r.get('z') is not None and r['z'] > 0:
            print(tr('cosmo_trouve', nom=r['nom'], type=r.get('type', ''), z=formats.court(r['z']),
                     cache=tr('fiche_depuis_cache') if r.get('cache') else ''), file=sys.stderr)
            zs.append(r['z'])
        elif r['etat'] == 'ok':
            print(tr('cosmo_trouve_sans_z', nom=r['nom'], type=r.get('type', ''),
                     z=formats.chiffres(r['z'], 4) if r.get('z') is not None else '—'), file=sys.stderr)
            return 2
        elif r['etat'] == 'ambigu':
            print(tr('cosmo_ambigu', n=len(r['candidats']), nom=a.objet), file=sys.stderr)
            for c in r['candidats']:
                print('  %-40s %-28s z = %s' % (c['nom'], c.get('type', ''), c.get('z')), file=sys.stderr)
            return 2
        elif r['etat'] == 'hors_ligne':
            print(tr('cosmo_hors_ligne', erreur=r.get('erreur', '')[:120]), file=sys.stderr)
            return 3
        elif r['etat'] == 'desactive':
            print(tr('cosmo_desactive'), file=sys.stderr)
            return 3
        else:
            print(tr('cosmo_introuvable', nom=a.objet), file=sys.stderr)
            return 2
    if not zs and not a.courbes:
        print(tr('cosmo_cli_aucun_z'), file=sys.stderr)
        return 2
    resultats = []
    try:
        for z in zs:
            resultats.append(calcul.calculer(z, a.modele, a.h0, a.om, a.ok, incertitudes=not a.sans_sigma,
                                             shoes=a.shoes))
        courbes = None
        if a.courbes:
            zmin, zmax, n = a.courbes
            courbes = calcul.courbes(calcul.grille_z(calcul.verifier_z(zmin), calcul.verifier_z(zmax),
                                                     max(2, int(n))), a.modele, a.h0, a.om, a.ok)
    except calcul.ErreurCosmo as e:
        print(tr(e.cle, **e.valeurs), file=sys.stderr)
        return 2
    if a.json:
        out = {'resultats': [_json(d) for d in resultats]}
        if courbes is not None:
            out['courbes'] = {k: [float(x) for x in v] for k, v in courbes.items()}
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for d in resultats:
            print(tr('cosmo_cli_titre', z=formats.court(d['z']), modele=tr('cosmo_mod_' + d['modele'])))
            for k, _ in calcul.GRANDEURS:
                s = (d.get('sigma') or {}).get(k)
                ligne = '  %-44s %s' % (tr('cosmo_g_' + k), formats.valeur(k, d[k]))
                if s:
                    ligne += '   ' + formats.incertitude(k, d[k], s)
                if d.get('shoes') and k in d['shoes']:
                    ligne += '   SH0ES ' + formats.valeur(k, d['shoes'][k])
                print(ligne)
            for av in d['avertissements']:
                print('  ! ' + tr(av))
            print()
    if a.csv:
        if courbes is not None:
            formats.ecrire_csv_courbes(a.csv, courbes)
        else:
            formats.ecrire_csv_resultats(a.csv, resultats)
        print(tr('cosmo_ecrit', chemin=a.csv), file=sys.stderr)
    return 0
