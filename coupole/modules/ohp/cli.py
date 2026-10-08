"""Ligne de commande du module « Banque OHP » : coupole ohp <commande>."""
from __future__ import annotations

import csv
import json
import os
import sys
import threading
import time

from ...core import config, i18n
from ...core.i18n import tr


def _taille(o: float) -> str:
    return tr('taille_go', v='%.2f' % (o / 1e9)) if o >= 1e8 else tr('taille_mo', v='%.1f' % (o / 1e6))


def _selection_args(p, objet=True):
    if objet:
        p.add_argument('objets', nargs='*', metavar=tr('ohp_meta_objet'), help=tr('ohp_aide_objet'))
    p.add_argument('--type', dest='categories', action='append', metavar=tr('ohp_meta_cat'), help=tr('ohp_aide_type'))
    p.add_argument('--telescope', action='append', choices=['T120', 'IRIS'], help=tr('ohp_aide_telescope'))
    p.add_argument('--filtre', '--filter', dest='filtres', action='append', metavar='F', help=tr('ohp_aide_filtre'))
    p.add_argument('--nuit', '--night', dest='nuits', action='append', metavar=tr('ohp_meta_date'),
                   help=tr('ohp_aide_nuit'))
    p.add_argument('--sans-dates-douteuses', '--no-doubtful-dates', action='store_true',
                   help=tr('ohp_aide_dates'))
    p.add_argument('--tout', '--all', action='store_true', help=tr('ohp_aide_tout'))


def enregistrer(p):
    sous = p.add_subparsers(dest='ohp_commande', metavar=tr('cli_commande'), title=tr('cli_commandes'))
    fmt = p.formatter_class

    s = sous.add_parser('inventaire', aliases=['inventory'], help=tr('ohp_cli_inventaire'),
                        description=tr('ohp_cli_inventaire_desc'), formatter_class=fmt)
    s.add_argument('--rafraichir', '--refresh', action='store_true', help=tr('ohp_aide_rafraichir'))
    s.set_defaults(fonction=cmd_inventaire)

    s = sous.add_parser('catalogue', aliases=['catalog'], help=tr('ohp_cli_catalogue'),
                        description=tr('ohp_cli_catalogue_desc'), formatter_class=fmt)
    s.add_argument('--type', dest='categories', action='append', metavar=tr('ohp_meta_cat'), help=tr('ohp_aide_type'))
    s.add_argument('--telescope', action='append', choices=['T120', 'IRIS'], help=tr('ohp_aide_telescope'))
    s.add_argument('--chercher', '--search', metavar=tr('ohp_meta_texte'), help=tr('ohp_aide_chercher'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_catalogue)

    s = sous.add_parser('images', aliases=['list'], help=tr('ohp_cli_images'), description=tr('ohp_cli_images_desc'),
                        formatter_class=fmt)
    _selection_args(s)
    s.add_argument('--csv', metavar=tr('cli_meta_fichier'), help=tr('ohp_aide_csv'))
    s.set_defaults(fonction=cmd_images)

    s = sous.add_parser('estimer', aliases=['estimate'], help=tr('ohp_cli_estimer'),
                        description=tr('ohp_cli_estimer_desc'), formatter_class=fmt)
    _selection_args(s)
    s.add_argument('--format', choices=['xisf', 'fz', 'fits'], default=None, help=tr('ohp_aide_format'))
    s.add_argument('--dest', metavar=tr('cli_meta_dossier'), help=tr('ohp_aide_dest'))
    s.set_defaults(fonction=cmd_estimer)

    s = sous.add_parser('traiter', aliases=['process'], help=tr('ohp_cli_traiter'),
                        description=tr('ohp_cli_traiter_desc'), formatter_class=fmt)
    _selection_args(s)
    _options_traitement(s)
    s.set_defaults(fonction=cmd_traiter)

    s = sous.add_parser('tout', aliases=['all'], help=tr('ohp_cli_tout'), description=tr('ohp_cli_tout_desc'),
                        formatter_class=fmt)
    _options_traitement(s)
    s.set_defaults(fonction=cmd_tout)

    s = sous.add_parser('nouveautes', aliases=['new'], help=tr('ohp_cli_nouveautes'),
                        description=tr('ohp_cli_nouveautes_desc'), formatter_class=fmt)
    s.add_argument('--telecharger', '--download', action='store_true', help=tr('ohp_aide_telecharger_nouveautes'))
    _options_traitement(s)
    s.set_defaults(fonction=cmd_nouveautes)

    s = sous.add_parser('reorganiser', aliases=['reorganise', 'reorganize'], help=tr('ohp_cli_reorganiser'),
                        description=tr('ohp_cli_reorganiser_desc'), formatter_class=fmt)
    s.add_argument('source', metavar=tr('cli_meta_dossier'), help=tr('ohp_aide_source_reorg'))
    s.add_argument('--dest', metavar=tr('cli_meta_dossier'), help=tr('ohp_aide_dest'))
    s.set_defaults(fonction=cmd_reorganiser)

    s = sous.add_parser('telecharger', aliases=['download'], help=tr('ohp_cli_telecharger'),
                        description=tr('ohp_cli_telecharger_desc'), formatter_class=fmt)
    _selection_args(s)
    s.add_argument('--dest', metavar=tr('cli_meta_dossier'), help=tr('ohp_aide_dest'))
    s.add_argument('--telechargements', '--downloads', type=int, default=0, metavar='N', help=tr('ohp_aide_dl'))
    s.add_argument('--debit', '--rate', type=float, default=None, metavar=tr('ohp_meta_mos'), help=tr('ohp_aide_debit'))
    s.add_argument('--oui', '--yes', action='store_true', help=tr('ohp_aide_oui'))
    s.set_defaults(fonction=cmd_telecharger)

    s = sous.add_parser('anomalies', aliases=['anomalies-report'], help=tr('ohp_cli_anomalies'),
                        description=tr('ohp_cli_anomalies_desc'), formatter_class=fmt)
    s.add_argument('--dest', metavar=tr('cli_meta_dossier'), help=tr('ohp_aide_dest_anomalies'))
    s.add_argument('--csv', metavar=tr('cli_meta_fichier'), help=tr('ohp_aide_csv'))
    s.add_argument('--nouveaux', '--new', action='store_true', help=tr('ohp_aide_nouveaux'))
    s.set_defaults(fonction=cmd_anomalies)

    s = sous.add_parser('classer', aliases=['classify'], help=tr('ohp_cli_classer'),
                        description=tr('ohp_cli_classer_desc'), formatter_class=fmt)
    s.add_argument('nom', nargs='?', metavar=tr('ohp_meta_nom_base'), help=tr('ohp_aide_nom_base'))
    s.add_argument('--objet', '--object', metavar=tr('ohp_meta_objet'), help=tr('ohp_aide_classer_objet'))
    s.add_argument('--type', dest='categorie', choices=list(_categories()), help=tr('ohp_aide_type'))
    s.add_argument('--oublier', '--forget', action='store_true', help=tr('ohp_aide_classer_oublier'))
    s.add_argument('--en-ligne', '--online', action='store_true', help=tr('ohp_aide_en_ligne'))
    s.set_defaults(fonction=cmd_classer)

    s = sous.add_parser('ranger', aliases=['sort'], help=tr('ohp_cli_ranger'), description=tr('ohp_cli_ranger_desc'),
                        formatter_class=fmt)
    s.add_argument('--dest', required=True, metavar=tr('cli_meta_dossier'), help=tr('ohp_aide_dest'))
    s.set_defaults(fonction=cmd_ranger)

    s = sous.add_parser('bilan', aliases=['status'], help=tr('ohp_cli_bilan'), description=tr('ohp_cli_bilan'),
                        formatter_class=fmt)
    s.add_argument('--dest', required=True, metavar=tr('cli_meta_dossier'), help=tr('ohp_aide_dest'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_bilan)
    p.set_defaults(fonction=lambda a: (p.print_help(), 0)[1])


def _categories():
    from .cibles import CATEGORIES
    return CATEGORIES


def _options_traitement(s):
    s.add_argument('--dest', metavar=tr('cli_meta_dossier'), help=tr('ohp_aide_dest'))
    s.add_argument('--format', choices=['xisf', 'fz', 'fits'], default=None, help=tr('ohp_aide_format'))
    s.add_argument('--noms', '--names', choices=['fr', 'en'], default=None, help=tr('ohp_aide_noms'))
    s.add_argument('--astap', choices=['auto', 'tous', 'suspectes', 'jamais', 'all', 'suspicious', 'never'],
                   default='auto', help=tr('ohp_aide_astap'))
    s.add_argument('--telechargements', '--downloads', type=int, default=0, metavar='N', help=tr('ohp_aide_dl'))
    s.add_argument('--conversions', type=int, default=0, metavar='N', help=tr('ohp_aide_conv'))
    s.add_argument('--econome', '--eco', action='store_true', help=tr('ohp_aide_econome'))
    s.add_argument('--debit', '--rate', type=float, default=None, metavar=tr('ohp_meta_mos'), help=tr('ohp_aide_debit'))
    s.add_argument('--garder-fits', '--keep-fits', action='store_true', help=tr('ohp_aide_garder'))
    s.add_argument('--garder-doublons', '--keep-duplicates', action='store_true', help=tr('ohp_aide_garder_doublons'))
    s.add_argument('--oui', '--yes', action='store_true', help=tr('ohp_aide_oui'))


# ======================================================================== commandes
def _inventaire(rafraichir=False):
    from .inventaire import Inventaire
    return Inventaire.charger(rafraichir)


def cmd_inventaire(a):
    if a.rafraichir:
        print(tr('ohp_interrogation_tap'))
    inv = _inventaire(a.rafraichir)
    m = inv.meta
    n = inv.nouveautes
    if a.rafraichir and n and not n.get('premiere'):
        print(tr('ohp_nouveautes', images=len(n['images']), noms=len(n['noms']), depuis=n.get('depuis') or '?'))
        for nom in n['noms']:
            x = next((y for y in inv.images if y['target_name'] == nom), None)
            if x:
                print('   %-40s → %-30s %s' % (nom, x['objet'], tr('ohp_classement_' + x['classement'])))
    n_d = sum(1 for x in inv.images if x['doublon'])
    print(tr('ohp_inventaire_resume', n=len(inv.images), objets=len(inv.objets()), doublons=n_d,
             taille=_taille(sum(x['access_estsize'] * 1024 for x in inv.images)),
             nuits=len({(str(x['nuit'])) for x in inv.images}), date=m.get('date', '?'), source=m.get('source', '?')))
    return 0


def cmd_catalogue(a):
    from . import cibles
    from .selection import norm
    inv = _inventaire()
    objs = inv.objets()
    if a.categories:
        objs = [o for o in objs if o['cat'] in a.categories]
    if a.telescope:
        objs = [o for o in objs if o['tel'] & set(a.telescope)]
    if a.chercher:
        q = norm(a.chercher)
        objs = [o for o in objs if q in norm(o['objet']) or q in norm(cibles.nom_affiche(o['objet']))
                or any(q in norm(n) for n in o['noms'])]
    if a.json:
        print(json.dumps([{**o, 'noms': sorted(o['noms']), 'nuits': sorted(o['nuits']), 'tel': sorted(o['tel']),
                           'filtres': sorted(o['filtres']), 'nom': cibles.nom_affiche(o['objet']),
                           'categorie': tr('ohp_cat_' + o['cat'])} for o in objs], ensure_ascii=False, indent=1))
        return 0
    print('%-6s %-40s %6s %10s %6s  %s' % (tr('ohp_col_type'), tr('ohp_col_objet'), tr('ohp_col_images'),
                                           tr('ohp_col_volume'), tr('ohp_col_nuits'), tr('ohp_col_telescopes')))
    for o in objs:
        print('%-6s %-40s %6d %10s %6d  %s' % (o['cat'], cibles.nom_affiche(o['objet'])[:40], o['images'],
                                              _taille(o['octets']), len(o['nuits']), ', '.join(sorted(o['tel']))))
    print(tr('ohp_catalogue_total', n=len(objs)))
    return 0


def _choisir(a, inv):
    from .selection import Criteres, objets_correspondants, selectionner
    objets = []
    for q in a.objets or []:
        trouves = objets_correspondants(inv.images, q)
        if not trouves:
            print(tr('ohp_objet_inconnu', q=q), file=sys.stderr)
            return None
        if len(trouves) > 1:
            print(tr('ohp_objet_ambigu', q=q, liste=', '.join(trouves)), file=sys.stderr)
            return None
        objets += trouves
    if not (objets or a.categories or a.telescope or a.filtres or a.nuits or a.tout):
        print(tr('ohp_selection_vide'), file=sys.stderr)
        return None
    c = Criteres(objets=objets, categories=a.categories or [], telescopes=a.telescope or [],
                 filtres=a.filtres or [], nuits=a.nuits or [], sans_dates_douteuses=a.sans_dates_douteuses)
    return selectionner(inv.images, c)


def cmd_images(a):
    inv = _inventaire()
    sel = _choisir(a, inv)
    if sel is None:
        return 2
    from .cibles import nom_affiche
    lignes = sorted(sel, key=lambda x: (x['t_min'], x['access_url']))
    print('%-19s %-5s %-11s %7s %-28s %s' % (tr('ohp_col_date'), tr('ohp_col_tel'), tr('ohp_col_filtre'),
                                             tr('ohp_col_pose'), tr('ohp_col_objet'), tr('ohp_col_drapeaux')))
    from ...core.astro import utc
    for x in lignes:
        dr = []
        if x['doublon']:
            dr.append(tr('ohp_drapeau_doublon'))
        if x['date_partagee']:
            dr.append(tr('ohp_drapeau_date'))
        if x['diurne']:
            dr.append(tr('ohp_drapeau_diurne'))
        print('%-19s %-5s %-11s %7g %-28s %s' % (utc(x['t_min']).isoformat(timespec='seconds'), x['tel'],
                                                 x['filter_name'], x['t_exptime'], nom_affiche(x['objet'])[:28],
                                                 ', '.join(dr)))
    if a.csv:
        with open(a.csv, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(['url', 'objet', 'nom_base', 'nuit', 'date_utc', 'telescope', 'filtre', 'pose_s', 'ra_deg',
                        'dec_deg', 'octets', 'doublon', 'date_partagee', 'diurne'])
            for x in lignes:
                w.writerow([x['access_url'], x['objet'], x['target_name'], x['nuit'],
                            utc(x['t_min']).isoformat(timespec='seconds'), x['tel'], x['filter_name'],
                            '%g' % x['t_exptime'], '%.5f' % x['s_ra'], '%.5f' % x['s_dec'],
                            int(x['access_estsize'] * 1024), int(x['doublon']), int(x['date_partagee']),
                            int(x['diurne'])])
        print(tr('ecrit', chemin=a.csv))
    return 0


def _plan(a):
    from ...core import machine, parallele
    r = config.reglages()
    m = machine.detecter()
    return m, parallele.planifier(m, a.telechargements or r['telechargements_max'],
                                  getattr(a, 'conversions', 0) or r['conversions_max'],
                                  True if getattr(a, 'econome', False) or r['mode_econome'] else None)


def _afficher_estimation(est, fmt, dest, plan):
    from ...core.machine import disque_libre_go
    from .selection import place_necessaire
    print(tr('ohp_estimation', images=est['images'], objets=est['objets'], nuits=est['nuits'],
             doublons=est['doublons'], fits=_taille(est['octets_fits']), sortie=_taille(est['octets_sortie']),
             format=fmt.upper()))
    besoin = place_necessaire(est, plan.conversions, plan.telechargements)
    libre = disque_libre_go(dest) * 1e9
    print(tr('ohp_place', besoin=_taille(besoin), libre=_taille(libre), dest=dest))
    return libre >= besoin


def _dest(a):
    r = config.reglages()
    d = a.dest or r['dossier_sortie'] or str(config.dossier_sortie_defaut() / 'OHP_DU_ECU')
    return os.path.abspath(os.path.expanduser(d))


def cmd_estimer(a):
    from .selection import estimer
    inv = _inventaire()
    sel = _choisir(a, inv)
    if sel is None:
        return 2
    fmt = a.format or config.reglages()['format_sortie']
    m, plan = _plan(argparse_ns(a, telechargements=0))
    _afficher_estimation(estimer(sel, fmt), fmt, _dest(a), plan)
    return 0


def argparse_ns(a, **defauts):
    for k, v in defauts.items():
        if not hasattr(a, k):
            setattr(a, k, v)
    return a


def _astap_pour(mode):
    from ...core import astap
    r = config.reglages()
    if mode in ('jamais', 'never'):
        return None, 'jamais'
    e = astap.detecter(r['astap_executable'], r['astap_catalogue'])
    mode = {'all': 'tous', 'suspicious': 'suspectes', 'auto': 'tous'}.get(mode, mode)
    return e, mode


def _duree(s):
    from .gui_sans_qt import duree_lisible
    return duree_lisible(s)


def cmd_tout(a):
    """Toute la banque : estimation (volume, temps au débit plafond), confirmation (--oui), traitement reprenable."""
    from .pilote import estimation_temps
    from .selection import estimer
    r = config.reglages()
    inv = _inventaire()
    fmt = a.format or r['format_sortie']
    debit = (a.debit if a.debit is not None else r['debit_max_mo_s'])
    est = estimer(inv.images, fmt)
    print(tr('ohp_estimation_tout', images=est['images'], objets=est['objets'], fits=_taille(est['octets_fits']),
             sortie=_taille(est['octets_sortie']), format=fmt.upper(), debit='%.1f' % debit,
             temps=_duree(estimation_temps(est['octets_fits'], debit * 1e6))))
    if not a.oui:
        print(tr('ohp_confirmer_tout'), file=sys.stderr)
        return 4
    a.objets, a.tout = [], True
    return _traiter(a, inv, list(inv.images), confirmer_gros=False)


def cmd_nouveautes(a):
    """Nouveautés de la banque absentes de la copie locale ; --telecharger les traite dans la même arborescence."""
    from .inventaire import marquer_reference, nouveautes_locales
    dest = _dest(a)
    print(tr('ohp_nouv_verification'))
    try:
        inv = _inventaire(True)
    except Exception as e:
        print(tr('ohp_nouv_hors_ligne') + ' (%s)' % e, file=sys.stderr)
        return 3
    n = nouveautes_locales(inv, dest)
    if not n['copie']:
        print(tr('ohp_nouv_sans_copie', dest=dest))
        return 1
    if not n['images']:
        print(tr('ohp_nouv_aucune', depuis=n['depuis'] or '?'))
        return 0
    print(tr('ohp_nouv_liste', n=len(n['images']), objets=len(n['objets']), taille=_taille(n['octets']),
             depuis=n['depuis'] or '?'))
    from .cibles import nom_affiche
    from ...core.astro import utc
    for x in sorted(n['images'], key=lambda x: (x['t_min'], x['access_url']))[:200]:
        print('   %-19s %-5s %-11s %-28s %s' % (utc(x['t_min']).isoformat(timespec='seconds'), x['tel'],
                                               x['filter_name'], nom_affiche(x['objet'])[:28], x.get('vu_le', '')))
    if len(n['images']) > 200:
        print('   …')
    if not a.telecharger:
        return 0
    code = _traiter(a, inv, list(n['images']), confirmer_gros=not a.oui)
    if code == 0:
        marquer_reference()
    return code


def cmd_reorganiser(a):
    from .pilote import Traitement
    from ...core.parallele import Plan
    inv = _inventaire()
    r = config.reglages()
    t = Traitement(_dest(a), inv, Plan(1, 1, True, ''), {'format': r['format_sortie'], 'langue': i18n.langue()})
    try:
        res = t.reorganiser(a.source)
    finally:
        t.fermer()
    print(tr('ohp_reorganise_fait', n=res['ranges'], lots=res['lots'], ignores=len(res['ignores'])))
    for chemin, raison in res['ignores'][:50]:
        print('   %s : %s' % (chemin, tr('reorg_' + raison)))
    return 0


def cmd_traiter(a):
    inv = _inventaire()
    sel = _choisir(a, inv)
    if sel is None:
        return 2
    return _traiter(a, inv, sel)


def _traiter(a, inv, sel, confirmer_gros=True):
    from .pilote import Traitement
    from .selection import estimer
    r = config.reglages()
    fmt = a.format or r['format_sortie']
    dest = _dest(a)
    m, plan = _plan(a)
    print(tr('ohp_machine', cpu=m.coeurs_physiques, log=m.coeurs_logiques, ram='%.1f' % (m.memoire_disponible_mo / 1024),
             dl=plan.telechargements, conv=plan.conversions, raison=tr(plan.raison)))
    est = estimer(sel, fmt)
    assez = _afficher_estimation(est, fmt, dest, plan)
    if not est['images']:
        print(tr('ohp_rien'))
        return 0
    if not assez:
        print(tr('ohp_place_insuffisante'), file=sys.stderr)
        return 3
    if confirmer_gros and est['octets_fits'] > 5e9 and not a.oui:
        print(tr('ohp_confirmer_gros', taille=_taille(est['octets_fits'])), file=sys.stderr)
        return 4
    etat, mode = _astap_pour(a.astap)
    if etat is None or not etat.utilisable:
        print(tr('ohp_sans_astap') if etat is not None else tr('ohp_astap_desactive'))
    else:
        print(tr('ohp_avec_astap', exe=etat.executable, cat=etat.catalogue.upper()))
    langue = a.noms or (r['langue_noms'] if r['langue_noms'] in ('fr', 'en') else i18n.langue())
    debit = (a.debit if a.debit is not None else r['debit_max_mo_s']) * 1e6
    arret = threading.Event()
    etat_aff = {'octets': 0, 't': time.time()}

    def rapporter(ev):
        t = ev['type']
        if t == 'octets':
            etat_aff['octets'] += ev['n']
            return
        if t == 'debut':
            print(tr('ohp_debut', total=ev['total'], deja=ev['deja']))
        elif t == 'image':
            dt = max(1e-6, time.time() - etat_aff['t'])
            print(tr('ohp_ligne_image', n=ev['n'], total=ev['total'], statut=tr('ohp_statut_' + ev['statut']),
                     wcs=tr('ohp_wcs_' + (ev.get('wcs') or 'aucune')), source=ev.get('source', '')[:60],
                     debit='%.1f' % (etat_aff['octets'] / dt / 1e6)), flush=True)
        elif t == 'echec':
            print(tr('ohp_ligne_echec', source=ev['source'], erreur=ev['erreur']), flush=True)
        elif t == 'avis':
            print(tr(ev['cle'], valeur=ev['valeur']))
    try:
        tr_ = Traitement(dest, inv, plan, {'format': fmt, 'langue': langue, 'astap': etat, 'mode_astap': mode,
                                           'debit_octets_s': debit, 'garder_fits': a.garder_fits,
                                           'garder_doublons': a.garder_doublons},
                         rapporter=rapporter, arret=arret)
    except OSError as e:                              # dossier non inscriptible, disque retiré
        print(str(e), file=sys.stderr)
        return 3
    try:
        bilan = tr_.lancer(sel)
    except KeyboardInterrupt:
        arret.set()
        print(tr('interrompu_reprise'))
        return 130
    finally:
        tr_.fermer()
    _imprimer_bilan(bilan, dest)
    c = bilan.get('compte', {})
    print(tr('ohp_rapport_fin', images=bilan.get('images', 0), duree=_duree(bilan.get('duree', 0)), ok=c.get('ok', 0),
             doublons=c.get('doublon', 0), echecs=c.get('echec', 0), sortie=_taille(bilan['octets_sortie']),
             lots=bilan.get('lots', 0), journal=os.path.join(dest, '_traitement', 'JOURNAL.txt')))
    if bilan.get('echecs'):
        print(tr('ohp_rapport_echecs', liste='; '.join('%s (%s)' % (e['source'].rsplit('/', 1)[-1], e['erreur'][:60])
                                                     for e in bilan['echecs'][:10])))
    return 0 if not bilan['compte']['echec'] else 1


def _imprimer_bilan(b, dest):
    of, ox = b['octets_fits'], b['octets_sortie']
    print(tr('ohp_bilan', ok=b['statuts'].get('ok', 0), doublons=b['statuts'].get('doublon', 0),
             echecs=b['statuts'].get('echec', 0), fits=_taille(of), sortie=_taille(ox),
             ratio='%.1f' % (100 * ox / of if of else 0), lots=b.get('lots', '?'), dest=dest))
    print(tr('ohp_bilan_wcs', v=', '.join('%s %d' % (tr('ohp_wcs_' + (k or 'aucune')), v)
                                          for k, v in sorted(b['wcs'].items(), key=lambda kv: str(kv[0])))))
    if b['statuts'].get('echec'):
        print(tr('ohp_relancer'))


def cmd_ranger(a):
    from .pilote import Traitement
    inv = _inventaire()
    from ...core.parallele import Plan
    t = Traitement(_dest(a), inv, Plan(1, 1, True, ''), {'format': 'xisf', 'langue': 'fr'})
    try:
        idx = t.ranger()
    finally:
        t.fermer()
    print(tr('ohp_ranges', n=len(idx)))
    return 0


def cmd_bilan(a):
    from .pilote import Etat
    chemin = os.path.join(_dest(a), '_traitement', 'etat.sqlite')
    if not os.path.exists(chemin):
        print(tr('ohp_pas_de_traitement', dest=_dest(a)))
        return 1
    e = Etat(chemin)
    b = e.bilan()
    e.fermer()
    if a.json:
        print(json.dumps(b, indent=1))
        return 0
    b['lots'] = '?'
    _imprimer_bilan(b, _dest(a))
    return 0


def cmd_telecharger(a):
    """FITS d'origine seulement, sans conversion : <dest>/<objet>/<nuit>_<télescope>/<fichier>."""
    import concurrent.futures as F
    from ...core import reseau
    from .cibles import nom_affiche
    from .conversion import sur
    from .selection import estimer
    inv = _inventaire()
    sel = _choisir(a, inv)
    if sel is None:
        return 2
    xs = [x for x in sel if not x['doublon']]
    dest = _dest(a)
    m, plan = _plan(argparse_ns(a, conversions=0, econome=False))
    est = estimer(sel, 'fits')
    print(tr('ohp_estimation_fits', images=est['images'], doublons=est['doublons'], fits=_taille(est['octets_fits'])))
    if est['octets_fits'] > 5e9 and not a.oui:
        print(tr('ohp_confirmer_gros', taille=_taille(est['octets_fits'])), file=sys.stderr)
        return 4
    lim = reseau.LimiteurDebit((a.debit if a.debit is not None else config.reglages()['debit_max_mo_s']) * 1e6)
    pris, plan_f = set(), []
    for x in sorted(xs, key=lambda x: (x['t_min'], x['access_url'])):
        sous = os.path.join(dest, sur(nom_affiche(x['objet'])), '%s_%s' % (x['nuit'], x['tel']))
        nom = x['access_url'].rsplit('/', 1)[1]
        chemin, k = os.path.join(sous, nom), 1
        while chemin in pris:
            b, e = os.path.splitext(nom)
            chemin = os.path.join(sous, '%s__%d%s' % (b, k, e))
            k += 1
        pris.add(chemin)
        os.makedirs(sous, exist_ok=True)
        plan_f.append((x, chemin))
    echecs = 0
    with F.ThreadPoolExecutor(plan.telechargements) as ex:
        futs = {ex.submit(reseau.telecharger, x['access_url'], c, int(x['access_estsize'] * 1024), 2048, lim): (x, c)
                for x, c in plan_f}
        for n, fut in enumerate(F.as_completed(futs), 1):
            x, c = futs[fut]
            try:
                st, _ = fut.result()
                print('[%d/%d] %s %s' % (n, len(futs), tr('ohp_dl_' + st), os.path.relpath(c, dest)), flush=True)
            except Exception as e:
                echecs += 1
                print('[%d/%d] %s %s — %s' % (n, len(futs), tr('ohp_dl_echec'), os.path.relpath(c, dest), e))
    print(tr('ohp_dl_fin', n=len(plan_f) - echecs, echecs=echecs, dest=dest))
    return 1 if echecs else 0


def cmd_anomalies(a):
    from . import anomalies
    from .astrometrie import attentes
    inv = _inventaire()
    med, medo = attentes(inv.images)
    an = anomalies.detecter(inv.images, medo)
    if a.dest:
        an += anomalies.depuis_traitement(os.path.join(_dest(a), '_traitement', 'etat.sqlite'))
    if a.nouveaux:
        an = [x for x in an if x['nouveau']]
    for genre, n in anomalies.resume(an).items():
        act = 'ecartee' if genre in anomalies.ECARTEES else 'signalee'
        print('%6d  %-18s %-10s %s' % (n, genre, tr('anom_action_' + act), tr('anom_' + genre)))
    print(tr('ohp_anomalies_total', n=len(an)))
    if a.csv:
        anomalies.ecrire_csv(a.csv, an)
        print(tr('ecrit', chemin=a.csv))
    return 0


def cmd_classer(a):
    from . import cibles, resolution
    inv = _inventaire()
    if a.en_ligne:
        noms = resolution.noms_inconnus(inv.images)
        print(tr('ohp_resolution', n=len(noms)))
        r = resolution.resoudre(noms)
        for nom, v in r.items():
            print('   %-40s → %s' % (nom, ('%s [%s, %s]' % (v['objet'], v['cat'], v['source'])) if v else '—'))
        return 0
    if not a.nom:
        douteux = sorted({(x['target_name'], x['objet'], x['classement']) for x in inv.images if x['a_verifier']})
        for nom, obj, cl in douteux:
            print('   %-40s → %-30s %s' % (nom, obj, tr('ohp_classement_' + cl)))
        print(tr('ohp_a_verifier', n=len(douteux)))
        return 0
    if a.oublier:
        cibles.corriger(a.nom, None)
        print(tr('ohp_correction_oubliee', nom=a.nom))
        return 0
    if not a.objet:
        x = next((y for y in inv.images if y['target_name'] == a.nom), None)
        if x is None:
            print(tr('ohp_nom_absent', nom=a.nom), file=sys.stderr)
            return 2
        print('%s → %s [%s] %s' % (a.nom, x['objet'], x['cat'], tr('ohp_classement_' + x['classement'])))
        return 0
    cat = a.categorie
    if cat is None:                       # fusion dans un objet existant : on reprend sa catégorie
        ex = next((y for y in inv.images if y['objet'] == a.objet), None)
        cat = ex['cat'] if ex else 'autre'
    cibles.corriger(a.nom, a.objet, cat)
    print(tr('ohp_correction_faite', nom=a.nom, objet=a.objet, cat=cat))
    return 0
