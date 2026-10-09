"""Ligne de commande du module « Archives » : coupole archives <commande>."""
from __future__ import annotations

import csv
import json
import os
import sys
import threading

from ...core import config
from ...core.i18n import tr


def _taille(o: float) -> str:
    if o >= 1e9:
        return tr('taille_go', v='%.2f' % (o / 1e9))
    return tr('taille_mo', v='%.1f' % (o / 1e6))


def _recherche_args(p):
    p.add_argument('nom', nargs='?', default='', metavar=tr('arc_meta_nom'), help=tr('arc_aide_nom'))
    p.add_argument('--rayon', '--radius', type=float, default=3.0, metavar=tr('arc_meta_arcmin'), help=tr('arc_aide_rayon'))
    p.add_argument('--archive', dest='archives', action='append', metavar='A', help=tr('arc_aide_archive'))
    p.add_argument('--mission', dest='missions', action='append', metavar='M', help=tr('arc_aide_mission'))
    p.add_argument('--instrument', dest='instruments', action='append', metavar='I', help=tr('arc_aide_instrument'))
    p.add_argument('--filtre', '--filter', dest='filtres', action='append', metavar='F', help=tr('arc_aide_filtre'))
    p.add_argument('--debut', '--from', default='', metavar=tr('arc_meta_date'), help=tr('arc_aide_debut'))
    p.add_argument('--fin', '--to', default='', metavar=tr('arc_meta_date'), help=tr('arc_aide_fin'))
    p.add_argument('--tous-niveaux', '--all-levels', action='store_true', help=tr('arc_aide_tous_niveaux'))
    p.add_argument('--non-publiques', '--proprietary', action='store_true', help=tr('arc_aide_non_publiques'))
    p.add_argument('--corps', '--body', default='', metavar=tr('arc_meta_corps'), help=tr('arc_aide_corps'))
    p.add_argument('--limite', '--limit', type=int, default=2000, metavar='N', help=tr('arc_aide_limite'))
    p.add_argument('--id', dest='ids', action='append', metavar=tr('cli_meta_id'), help=tr('arc_aide_id'))


def enregistrer(p):
    sous = p.add_subparsers(dest='arc_commande', metavar=tr('cli_commande'), title=tr('cli_commandes'))
    fmt = p.formatter_class

    s = sous.add_parser('liste', aliases=['list'], help=tr('arc_cli_liste'), description=tr('arc_cli_liste'),
                        formatter_class=fmt)
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_liste)

    s = sous.add_parser('chercher', aliases=['search'], help=tr('arc_cli_chercher'),
                        description=tr('arc_cli_chercher_desc'), formatter_class=fmt)
    _recherche_args(s)
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.add_argument('--csv', metavar=tr('cli_meta_fichier'), help=tr('arc_aide_csv'))
    s.set_defaults(fonction=cmd_chercher)

    s = sous.add_parser('estimer', aliases=['estimate'], help=tr('arc_cli_estimer'),
                        description=tr('arc_cli_estimer_desc'), formatter_class=fmt)
    _recherche_args(s)
    s.set_defaults(fonction=cmd_estimer)

    s = sous.add_parser('telecharger', aliases=['download'], help=tr('arc_cli_telecharger'),
                        description=tr('arc_cli_telecharger_desc'), formatter_class=fmt)
    _recherche_args(s)
    s.add_argument('--dest', metavar=tr('cli_meta_dossier'), help=tr('arc_aide_dest'))
    s.add_argument('--format', choices=['xisf', 'fits'], default=None, help=tr('arc_aide_format'))
    s.add_argument('--sans-original', '--no-original', action='store_true', help=tr('arc_aide_sans_original'))
    s.add_argument('--debit', '--rate', type=float, default=None, metavar=tr('arc_meta_mos'), help=tr('arc_aide_debit'))
    s.add_argument('--paralleles', '--parallel', type=int, default=2, metavar='N', help=tr('arc_aide_paralleles'))
    s.add_argument('--max', type=int, default=0, metavar='N', help=tr('arc_aide_max'))
    s.add_argument('--oui', '--yes', action='store_true', help=tr('arc_aide_oui'))
    s.set_defaults(fonction=cmd_telecharger)

    s = sous.add_parser('preparer', aliases=['prepare'], help=tr('arc_cli_preparer'),
                        description=tr('arc_cli_preparer_desc'), formatter_class=fmt)
    s.add_argument('fichiers', nargs='+', metavar=tr('cli_meta_fichier'), help=tr('arc_aide_fichiers'))
    s.add_argument('--format', choices=['xisf', 'fits'], default='xisf', help=tr('arc_aide_format'))
    s.add_argument('--etiquette', '--label', metavar=tr('cli_meta_fichier'), help=tr('arc_aide_etiquette'))
    s.set_defaults(fonction=cmd_preparer)

    s = sous.add_parser('aligner', aliases=['align'], help=tr('arc_cli_aligner'),
                        description=tr('arc_cli_aligner_desc'), formatter_class=fmt)
    s.add_argument('fichiers', nargs='+', metavar=tr('cli_meta_fichier'), help=tr('arc_aide_fichiers_aligner'))
    s.add_argument('--dest', required=True, metavar=tr('cli_meta_dossier'), help=tr('arc_aide_dest_aligner'))
    g = s.add_mutually_exclusive_group()
    g.add_argument('--reference', type=int, default=0, metavar='N', help=tr('arc_aide_reference'))
    g.add_argument('--optimale', '--optimal', action='store_true', help=tr('arc_aide_optimale'))
    s.add_argument('--methode', '--method', choices=['bilineaire', 'adaptative', 'exacte', 'proche'], default='bilineaire',
                   help=tr('arc_aide_methode'))
    s.add_argument('--echelle', '--scale', type=float, default=1.0, metavar='X', help=tr('arc_aide_echelle'))
    s.add_argument('--sans-recadrage', '--no-crop', action='store_true', help=tr('arc_aide_sans_recadrage'))
    s.add_argument('--format', choices=['xisf', 'fits'], default='xisf', help=tr('arc_aide_format'))
    s.set_defaults(fonction=cmd_aligner)

    s = sous.add_parser('bilan', aliases=['status'], help=tr('arc_cli_bilan'), description=tr('arc_cli_bilan'),
                        formatter_class=fmt)
    s.add_argument('--dest', metavar=tr('cli_meta_dossier'), help=tr('arc_aide_dest'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_bilan)
    p.set_defaults(fonction=lambda a: (p.print_help(), 0)[1])


# ===================================================================================== commandes
def cmd_liste(a):
    from .services import ARCHIVES, PAR_DEFAUT
    lignes = []
    for x in ARCHIVES.values():
        etat = 'compte' if x.compte else ('non_pris' if x.id == 'smoka' else 'ok')
        lignes.append({'id': x.id, 'nom': x.nom, 'etape': x.etape, 'missions': list(x.missions), 'credit': x.credit,
                       'defaut': x.id in PAR_DEFAUT, 'etat': etat, 'recherche': 'coordonnees' if x.celeste else 'corps'})
    if a.json:
        print(json.dumps(lignes, ensure_ascii=False, indent=1))
        return 0
    for l in lignes:
        print('%-8s %-36s %s %-28s %s%s' % (l['id'], l['nom'], tr('arc_etape_n', n=l['etape']), ', '.join(l['missions']),
                                           tr('arc_etat_' + l['etat']), ' *' if l['defaut'] else ''))
    print(tr('arc_liste_defaut'))
    return 0


def _requete(a):
    from .recherche import requete
    from .services import ARCHIVES
    archives = tuple(a.archives or ())
    inconnues = [x for x in archives if x not in ARCHIVES]
    if inconnues:
        print(tr('arc_archive_inconnue', a=', '.join(inconnues), connues=', '.join(ARCHIVES)), file=sys.stderr)
        return None
    planetaire = bool(a.corps) or (archives and all(not ARCHIVES[x].celeste for x in archives))
    if planetaire:
        if not archives:
            archives = ('opus', 'pds')
        return requete('', a.rayon, archives=archives, missions=tuple(a.missions or ()),
                       instruments=tuple(a.instruments or ()), filtres=tuple(a.filtres or ()), date_min=a.debut,
                       date_max=a.fin, finaux=not a.tous_niveaux, publics=not a.non_publiques,
                       cible=a.corps or a.nom, limite=a.limite)
    if not a.nom:
        print(tr('arc_nom_requis'), file=sys.stderr)
        return None
    try:
        return requete(a.nom, a.rayon, archives=archives, missions=tuple(a.missions or ()),
                       instruments=tuple(a.instruments or ()), filtres=tuple(a.filtres or ()), date_min=a.debut,
                       date_max=a.fin, finaux=not a.tous_niveaux, publics=not a.non_publiques, limite=a.limite)
    except LookupError:
        print(tr('arc_introuvable', nom=a.nom), file=sys.stderr)
    except Exception as e:
        print(tr('arc_resolution_impossible', erreur=str(e)), file=sys.stderr)
    return None


def _chercher(a):
    from .recherche import chercher, toutes
    q = _requete(a)
    if q is None:
        return None, None
    if q.ra is not None:
        print(tr('arc_position', ra='%.5f' % q.ra, dec='%+.5f' % q.dec, r='%.1f' % (q.rayon * 60)), file=sys.stderr)
    res = chercher(q, rapporter=lambda **e: None)
    for r in res:
        if r.compte_requis:
            print(tr('arc_compte_requis', archive=r.archive), file=sys.stderr)
        elif r.non_pris_en_charge:
            print(tr('arc_non_pris', archive=r.archive, lien=r.erreur), file=sys.stderr)
        elif r.erreur:
            print(tr('arc_erreur_archive', archive=r.archive, erreur=r.erreur), file=sys.stderr)
        else:
            print(tr('arc_resultat_archive', archive=r.archive, n=len(r.observations), s='%.1f' % r.secondes) +
                  (' ' + tr('arc_tronque') if r.tronque else ''), file=sys.stderr)
    obs = toutes(res)
    if a.ids:
        obs = [o for o in obs if any(correspond(o, v) for v in a.ids)]
    return q, obs


def correspond(o: dict, v: str) -> bool:
    """`--id` : identifiant complet (« eso:ADP.… »), sans le préfixe de l'archive (« ADP.… »), identifiant de
    l'observation, ou début du nom de fichier."""
    return v in (o['id'], o['obs_id']) or o['id'].endswith(':' + v) or o['fichier'].startswith(v)


def _ligne(o: dict) -> str:
    return '%-44s %-7s %-16s %-10s %-10s %s %s' % (
        o['id'][:44], o['mission'][:7], o['instrument'][:16], o['filtre'][:10], (o['debut'] or '')[:10],
        _taille(o['taille']) if o.get('taille') else '?', o['cible'][:20])


def cmd_chercher(a):
    q, obs = _chercher(a)
    if obs is None:
        return 2
    if a.json:
        print(json.dumps(obs, ensure_ascii=False, indent=1, default=str))
    else:
        for o in obs:
            print(_ligne(o))
        print(tr('arc_total', n=len(obs)))
    if a.csv:
        cles = ['id', 'archive', 'mission', 'instrument', 'filtre', 'lambda_nm', 'debut', 'publique', 'calib', 'cible',
                'ra', 'dec', 'distance', 'taille', 'url', 'apercu', 'page', 'programme', 'pi', 'titre', 'credit']
        with open(a.csv, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cles, extrasaction='ignore')
            w.writeheader()
            w.writerows(obs)
    return 0


def cmd_estimer(a):
    from .telechargement import estimer, seuil_octets
    q, obs = _chercher(a)
    if obs is None:
        return 2
    e = estimer(obs)
    print(tr('arc_estimation', n=e['n'], taille=_taille(e['octets']), connus=e['connus'], mesures=e['mesures'],
             estimes=e['estimes'], inconnus=e['inconnus']))
    if e['octets'] > seuil_octets():
        print(tr('arc_au_dela_seuil', seuil=_taille(seuil_octets())))
    return 0


def cmd_telecharger(a):
    from .telechargement import Telechargement, estimer, seuil_octets, sortie_par_defaut
    q, obs = _chercher(a)
    if obs is None:
        return 2
    if a.max and len(obs) > a.max:
        obs = obs[:a.max]
    if not obs:
        print(tr('arc_rien'))
        return 0
    e = estimer(obs)
    print(tr('arc_estimation', n=e['n'], taille=_taille(e['octets']), connus=e['connus'], mesures=e['mesures'],
             estimes=e['estimes'], inconnus=e['inconnus']))
    if e['octets'] > seuil_octets() and not a.oui:
        print(tr('arc_confirmer_cli', seuil=_taille(seuil_octets())))
        return 3
    dest = a.dest or sortie_par_defaut()
    r = config.reglages()
    debit = (a.debit if a.debit is not None else r.get('archives_debit_mo_s', r['debit_max_mo_s'])) * 1e6
    fmt = a.format or r.get('archives_format', 'xisf')
    cible = a.nom if a.nom and not _ressemble_coordonnees(a.nom) else (a.corps or '')

    def evt(ev):
        if ev.get('genre') == 'fini':
            print(tr('arc_fini', chemin=ev['chemin']))
        elif ev.get('genre') == 'erreur':
            print(tr('arc_echec', id=ev['id'], erreur=ev['erreur']), file=sys.stderr)
        elif ev.get('genre') == 'deja':
            print(tr('arc_deja', id=ev['id']))
    t = Telechargement(dest, obs, cible=cible, fmt=fmt, garder_original=not a.sans_original, debit_octets_s=debit,
                       paralleles=a.paralleles, rapporter=evt, arret=threading.Event())
    b = t.executer()
    print(tr('arc_bilan_session', ok=b.get('ok', 0), deja=b.get('deja', 0), echec=b.get('echec', 0),
             taille=_taille(b.get('octets', 0)), s='%.0f' % b.get('secondes', 0)))
    return 0 if not b.get('echec') else 1


def _ressemble_coordonnees(t: str) -> bool:
    from .recherche import lire_coordonnees
    return lire_coordonnees(t) is not None


def cmd_preparer(a):
    from .extraction import Inexploitable, preparer
    code = 0
    for f in a.fichiers:
        base = os.path.splitext(f[:-3] if f.lower().endswith(('.gz', '.fz')) else f)[0]
        if base.lower().endswith(('.fits', '.fit')):
            base = os.path.splitext(base)[0]
        try:
            r = preparer(f, base + '_sci', None, a.format, a.etiquette)
            print(tr('arc_prepare', chemin=r['chemin'], forme='%d×%d' % (r['forme'][1], r['forme'][0]), nan=r['nan'],
                     bunit=r['bunit'] or '-', wcs=tr('oui') if r['wcs'] else tr('non')))
        except (Inexploitable, ValueError, OSError) as e:
            print(tr('arc_echec', id=f, erreur=str(e)), file=sys.stderr)
            code = 1
    return code


def cmd_aligner(a):
    from .alignement import aligner, reproject_disponible
    if not reproject_disponible():
        print(tr('arc_sans_reproject'), file=sys.stderr)
    try:
        r = aligner(a.fichiers, a.dest, reference=None if a.optimale else a.reference, methode=a.methode,
                    echelle=a.echelle, recadrer=not a.sans_recadrage, fmt=a.format,
                    progression=lambda k, n, nom: print(tr('arc_alignement_image', k=k + 1, n=n, nom=nom)))
    except (ValueError, OSError, MemoryError, IndexError) as e:
        print(tr('arc_echec', id='aligner', erreur=str(e)), file=sys.stderr)
        return 1
    print(tr('arc_aligne', n=len(r['fichiers']), forme='%d×%d' % (r['forme'][1], r['forme'][0]), dest=a.dest))
    for c in sorted(r['composition'], key=lambda c: c['rang']):
        print('  %-40s %-10s %8s nm  RVB %.2f %.2f %.2f' % (c['nom'][:40], c['filtre'][:10],
                                                          '%.0f' % c['lambda_nm'] if c['lambda_nm'] else '?', *c['couleur']))
    return 0


def cmd_bilan(a):
    import collections
    from .telechargement import possession, sortie_par_defaut
    p = possession(a.dest or sortie_par_defaut())
    c = collections.Counter(v['statut'] for v in p.values())
    par_mission = collections.Counter(v.get('mission', '?') for v in p.values() if v['statut'] == 'ok')
    if a.json:
        print(json.dumps({'statuts': dict(c), 'missions': dict(par_mission)}, ensure_ascii=False, indent=1))
        return 0
    print(tr('arc_bilan', ok=c.get('ok', 0), echec=c.get('echec', 0), absente=c.get('absente', 0)))
    for m, n in sorted(par_mission.items()):
        print('  %-10s %d' % (m, n))
    return 0
