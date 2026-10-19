"""Ligne de commande du module « Partages du DU » : coupole partages <commande>."""
from __future__ import annotations

import datetime as D
import json
import os
import sys

from ...core.i18n import decimal as _dec
from ...core.i18n import tr


def enregistrer(p):
    sous = p.add_subparsers(dest='pt_commande', metavar=tr('cli_commande'), title=tr('cli_commandes'))
    fmt = p.formatter_class

    s = sous.add_parser('ajouter', aliases=['add'], help=tr('pt_cli_ajouter'), description=tr('pt_cli_ajouter_desc'),
                        formatter_class=fmt)
    s.add_argument('nom', metavar=tr('pt_meta_nom'), help=tr('pt_cli_nom'))
    s.add_argument('lien', metavar=tr('pt_meta_lien'), help=tr('pt_cli_lien'))
    s.add_argument('--mot-de-passe', '--password', dest='mdp', default='', metavar=tr('pt_meta_mdp'), help=tr('pt_cli_mdp'))
    s.set_defaults(fonction=cmd_ajouter)

    s = sous.add_parser('liste', aliases=['list'], help=tr('pt_cli_liste'), description=tr('pt_cli_liste'),
                        formatter_class=fmt)
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_liste)

    s = sous.add_parser('oublier', aliases=['forget'], help=tr('pt_cli_oublier'), description=tr('pt_cli_oublier'),
                        formatter_class=fmt)
    s.add_argument('nom', metavar=tr('pt_meta_nom'), help=tr('pt_cli_nom'))
    s.set_defaults(fonction=cmd_oublier)

    s = sous.add_parser('explorer', aliases=['explore'], help=tr('pt_cli_explorer'),
                        description=tr('pt_cli_explorer_desc'), formatter_class=fmt)
    s.add_argument('nom', metavar=tr('pt_meta_nom'), help=tr('pt_cli_nom'))
    s.add_argument('--fichiers', '--files', action='store_true', help=tr('pt_cli_fichiers'))
    s.add_argument('--vus', '--seen', action='store_true', help=tr('pt_cli_vus'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_explorer)

    s = sous.add_parser('tableau', aliases=['table'], help=tr('pt_cli_tableau'), description=tr('pt_cli_tableau_desc'),
                        formatter_class=fmt)
    s.add_argument('nom', metavar=tr('pt_meta_nom'), help=tr('pt_cli_nom'))
    s.add_argument('chemin', nargs='?', default='', metavar=tr('pt_meta_chemin'), help=tr('pt_cli_chemin_tableau'))
    s.add_argument('--entetes', '--headers', action='store_true', help=tr('pt_cli_avec_entetes'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_tableau)

    s = sous.add_parser('entetes', aliases=['headers'], help=tr('pt_cli_entetes'), description=tr('pt_cli_entetes'),
                        formatter_class=fmt)
    s.add_argument('nom', metavar=tr('pt_meta_nom'), help=tr('pt_cli_nom'))
    s.add_argument('dossier', nargs='?', default='', metavar=tr('pt_meta_chemin'), help=tr('pt_cli_dossier'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_entetes)

    s = sous.add_parser('paires', aliases=['pairs'], help=tr('pt_cli_paires'), description=tr('pt_cli_paires_desc'),
                        formatter_class=fmt)
    s.add_argument('nom', metavar=tr('pt_meta_nom'), help=tr('pt_cli_nom'))
    s.add_argument('--iss', type=float, default=5.0, metavar='S', help=tr('pt_cli_seuil_iss'))
    s.add_argument('--lune', '--moon', type=float, default=60.0, metavar='S', help=tr('pt_cli_seuil_lune'))
    s.add_argument('--base', type=float, default=100.0, metavar='N', help=tr('pt_cli_base'))
    s.add_argument('--entetes', '--headers', action='store_true', help=tr('pt_cli_avec_entetes'))
    s.add_argument('--sans-corrections', '--no-corrections', action='store_true', help=tr('pt_cli_sans_corrections'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_paires)

    s = sous.add_parser('telecharger', aliases=['download'], help=tr('pt_cli_telecharger'),
                        description=tr('pt_cli_telecharger_desc'), formatter_class=fmt)
    s.add_argument('nom', metavar=tr('pt_meta_nom'), help=tr('pt_cli_nom'))
    s.add_argument('chemins', nargs='+', metavar=tr('pt_meta_chemin'), help=tr('pt_cli_chemins'))
    s.add_argument('--dossier', '--folder', default='', metavar=tr('cli_meta_dossier'), help=tr('pt_cli_sortie'))
    s.add_argument('--format', choices=('xisf', 'fits'), default='xisf', help=tr('pt_cli_format'))
    s.add_argument('--astrometrie', '--astrometry', choices=('wcs', 'auto', 'astap', 'astrometry.net', 'nova'),
                   default='wcs', help=tr('pt_cli_astrometrie'))
    s.add_argument('--en-ligne', '--online', action='store_true', help=tr('pt_cli_en_ligne'))
    s.add_argument('--sans-originaux', '--no-originals', action='store_true', help=tr('pt_cli_sans_originaux'))
    s.set_defaults(fonction=cmd_telecharger)

    s = sous.add_parser('mesurer', aliases=['measure'], help=tr('pt_cli_mesurer'), description=tr('pt_cli_mesurer_desc'),
                        formatter_class=fmt)
    s.add_argument('images', nargs='+', metavar=tr('cli_meta_fichier'), help=tr('pt_cli_images'))
    s.add_argument('--cible', '--target', choices=('lune', 'moon', 'iss'), default='lune', help=tr('pt_cli_cible'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_mesurer)

    s = sous.add_parser('calculer', aliases=['compute'], help=tr('pt_cli_calculer'),
                        description=tr('pt_cli_calculer_desc'), formatter_class=fmt)
    s.add_argument('fichier', metavar=tr('cli_meta_fichier'), help=tr('pt_cli_fichier_visees'))
    s.add_argument('--html', default='', metavar=tr('cli_meta_fichier'), help=tr('pt_cli_html'))
    s.add_argument('--pdf', default='', metavar=tr('cli_meta_fichier'), help=tr('pt_cli_pdf'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_calculer)

    s = sous.add_parser('deposer', aliases=['upload'], help=tr('pt_cli_deposer'), description=tr('pt_cli_deposer_desc'),
                        formatter_class=fmt)
    s.add_argument('nom', metavar=tr('pt_meta_nom'), help=tr('pt_cli_nom'))
    s.add_argument('fichiers', nargs='*', metavar=tr('cli_meta_fichier'), help=tr('pt_cli_fichiers_depot'))
    s.add_argument('--dossier', '--folder', default='', metavar=tr('pt_meta_chemin'), help=tr('pt_cli_dossier_depot'))
    s.add_argument('--tableau', '--table', default='', metavar=tr('pt_meta_chemin'), help=tr('pt_cli_tableau_depot'))
    s.add_argument('--valeur', '--value', dest='valeurs', action='append', default=[], metavar=tr('pt_meta_valeur'),
                   help=tr('pt_cli_valeur'))
    s.add_argument('--oui', '--yes', action='store_true', help=tr('pt_cli_oui'))
    s.set_defaults(fonction=cmd_deposer)

    s = sous.add_parser('de440', help=tr('pt_cli_de440'), description=tr('pt_cli_de440'), formatter_class=fmt)
    s.set_defaults(fonction=cmd_de440)
    p.set_defaults(fonction=lambda a: (p.print_help(), 0)[1])


def _session(nom):
    from . import etat
    from .session import Session
    x = etat.trouver(nom)
    if x is None:
        print(tr('pt_cli_inconnu', nom=nom), file=sys.stderr)
        return None
    return Session(x)


def _erreur(e) -> int:
    from .webdav import ErreurPartage, LienInvalide
    if isinstance(e, (ErreurPartage, LienInvalide)):
        print(tr(e.cle), file=sys.stderr)
        return 3
    print('%s: %s' % (type(e).__name__, e), file=sys.stderr)
    return 1


def cmd_ajouter(a):
    from . import etat
    from .gui_sans_qt import texte_droits
    from .webdav import Client, analyser_lien
    try:
        p = analyser_lien(a.lien, mot_de_passe=a.mdp)
        info = Client(p).verifier()
    except Exception as e:
        return _erreur(e)
    x = etat.ajouter(a.nom, a.lien, a.mdp, info.droits)
    print(tr('pt_ajoute', nom=x.nom))
    print(texte_droits(info.droits))
    return 0


def cmd_liste(a):
    from . import etat
    l = etat.lister()
    if a.json:
        print(json.dumps([{'nom': x.nom, 'serveur': x.partage().serveur, 'droits': x.droits,
                           'derniere_visite': x.derniere_visite} for x in l], ensure_ascii=False, indent=1))
        return 0
    if not l:
        print(tr('pt_aucun_partage'))
    for x in l:
        print('%-30s %s  [%s]' % (x.nom, x.partage().masque(), ', '.join(tr('pt_droit_' + d) for d in x.droits)))
    return 0


def cmd_oublier(a):
    from . import etat
    x = etat.trouver(a.nom)
    if x is None:
        print(tr('pt_cli_inconnu', nom=a.nom), file=sys.stderr)
        return 2
    etat.retirer(x.ident)
    print(tr('pt_oublie', nom=x.nom))
    return 0


def cmd_explorer(a):
    from .apercus import taille_lisible
    s = _session(a.nom)
    if s is None:
        return 2
    try:
        st = s.rafraichir()
    except Exception as e:
        return _erreur(e)
    if a.json:
        print(json.dumps({'resume': st.resume(), 'series': [
            {'dossier': x.dossier, 'observateur': x.observateur, 'cible': x.cible, 'debut': x.debut.isoformat(),
             'fin': x.fin.isoformat(), 'fichiers': len(x.fichiers), 'genres': x.genres()} for x in st.series],
            'tableaux': [f.chemin for f in st.tableaux],
            'fichiers': [{'chemin': f.chemin, 'genre': f.genre, 'taille': f.taille, 'nouveau': f.nouveau,
                          'instant': f.instant.isoformat() if f.instant else None, 'observateur': f.observateur,
                          'cible': f.cible} for f in st.fichiers] if a.fichiers else []},
            ensure_ascii=False, indent=1))
    else:
        r = st.resume()
        print(tr('pt_resume', n=r['fichiers'], d=r['dossiers'], o=taille_lisible(r['octets']), s=r['series'],
                 obs=r['observateurs'], t=r['tableaux']))
        if r['nouveaux']:
            print(tr('pt_nouveautes', n=r['nouveaux']))
        for d in sorted(st.dossiers.values(), key=lambda x: x.chemin):
            if not d.chemin:
                continue
            print('  %s/  (%d, %s)' % (d.chemin, len(d.tous_les_fichiers()), taille_lisible(d.taille())))
        for x in st.series:
            print('  ' + tr('pt_n_serie', obs=x.observateur or tr('pt_inconnu'), debut=x.debut.strftime('%H:%M:%S'),
                            fin=x.fin.strftime('%H:%M:%S'), n=len(x.fichiers),
                            genres=', '.join('%d %s' % (v, tr('pt_genre_' + k)) for k, v in sorted(x.genres().items())))
                  + '  [%s, %s]' % (x.dossier or '/', x.debut.strftime('%Y-%m-%d')))
        for f in st.tableaux:
            print('  ' + tr('pt_cli_un_tableau', chemin=f.chemin))
        if a.fichiers:
            for f in st.fichiers:
                print('    %s%s  %s  %s' % ('* ' if f.nouveau else '', f.chemin, tr('pt_genre_' + f.genre),
                                           taille_lisible(f.taille)))
    if a.vus:
        s.marquer_vus()
    return 0


def _lire_entetes(s, fichiers_):
    n = 0
    for f in fichiers_:
        if f.genre == 'fits' and f.chemin not in s.entetes:
            try:
                s.lire_entete_fits(f.chemin)
                n += 1
            except Exception:
                continue
    return n


def cmd_tableau(a):
    from .gui_sans_qt import texte_anomalie
    s = _session(a.nom)
    if s is None:
        return 2
    try:
        st = s.rafraichir()
        if a.entetes:
            _lire_entetes(s, st.fichiers)
        chemins = [a.chemin] if a.chemin else [f.chemin for f in st.tableaux]
        sortie = []
        for c in chemins:
            _, ts = s.lire_tableau(c)
            for t in ts:
                for m in t.mesures:
                    sortie.append((c, t, m))
    except Exception as e:
        return _erreur(e)
    if a.json:
        print(json.dumps([{'tableau': c, 'feuille': t.feuille, 'ligne': m.ligne, 'niveau': m.niveau,
                           'cible': m.cible, 'auteur': m.auteur, 'fichier': m.fichier,
                           'instant': m.instant.isoformat() if m.instant else None, 'lat': m.lat, 'lon': m.lon,
                           'alt_m': m.alt_m, 'az': m.az, 'h': m.h,
                           'corrections': {k: (v.isoformat() if isinstance(v, D.datetime) else v)
                                           for k, v in m.corrections.items()},
                           'anomalies': [{'niveau': x.niveau, 'champ': x.champ, 'code': x.cle,
                                          'texte': texte_anomalie(x)} for x in m.anomalies]}
                          for c, t, m in sortie], ensure_ascii=False, indent=1))
        return 0
    for c, t, m in sortie:
        print('%s:%d  [%s]  %s  %s  %s  %s' % (c, m.ligne, tr('pt_niveau_' + m.niveau), m.cible_brute, m.auteur,
                                               m.instant.strftime('%Y-%m-%d %H:%M:%S') if m.instant else '—',
                                               m.fichier))
        for x in m.anomalies:
            print('      %s : %s' % (tr('pt_niveau_' + x.niveau), texte_anomalie(x)))
    if not sortie:
        print(tr('pt_mesures_pas_tableau'))
    return 0


def cmd_entetes(a):
    s = _session(a.nom)
    if s is None:
        return 2
    try:
        st = s.rafraichir()
        fs = [f for f in st.fichiers if f.genre == 'fits' and f.chemin.startswith(a.dossier.strip('/'))]
        for f in fs:
            s.lire_entete_fits(f.chemin)
    except Exception as e:
        return _erreur(e)
    res = {f.chemin: s.entetes.get(f.chemin) for f in fs}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
        return 0
    for c, e in res.items():
        if e:
            print('%s  %s  %s  %s  %s' % (c, e.get('milieu') or '—', _deg(e.get('lat')), _deg(e.get('lon')),
                                         e.get('objet') or ''))
    return 0


def _deg(v):
    return '—' if v is None else _dec(v, 4) + '°'


def cmd_paires(a):
    from .analyses.parallaxe import paires as P
    s = _session(a.nom)
    if s is None:
        return 2
    try:
        st = s.rafraichir()
        if a.entetes:
            _lire_entetes(s, st.fichiers)
        obs = []
        for f in st.tableaux:
            _, ts = s.lire_tableau(f.chemin)
            for t in ts:
                obs += P.depuis_tableau(t, not a.sans_corrections)
        deja = {os.path.basename(x) for o in obs for x in o.fichiers}
        obs += [o for o in P.depuis_structure(st, s.entetes_lieux())
                if not any(os.path.basename(c) in deja for c in o.fichiers)]
    except Exception as e:
        return _erreur(e)
    paires = P.trouver(obs, {'iss': a.iss, 'tiangong': a.iss, 'lune': a.lune}, a.base)
    if a.json:
        print(json.dumps([{'cible': p.cible, 'ecart_s': p.ecart_s, 'base_km': p.base_km,
                           'a': {'observateur': p.a.observateur, 'debut': p.a.debut.isoformat(), 'source': p.a.source,
                                 'fichiers': p.a.fichiers},
                           'b': {'observateur': p.b.observateur, 'debut': p.b.debut.isoformat(), 'source': p.b.source,
                                 'fichiers': p.b.fichiers},
                           'notes': p.notes} for p in paires], ensure_ascii=False, indent=1))
        return 0
    r = P.resume_synchro(paires)
    print(tr('pc_paires_trouvees', n=r['paires'], s=r['a_la_seconde']))
    for p in paires:
        print('  %-6s  %s  ×  %s   Δt = %s s   %s' % (
            tr('pt_cible_' + p.cible), '%s %s' % (p.a.observateur or '?', p.a.debut.strftime('%Y-%m-%d %H:%M:%S')),
            '%s %s' % (p.b.observateur or '?', p.b.debut.strftime('%H:%M:%S')), _dec(p.ecart_s, 1),
            (tr('pc_cli_base', b=_dec(p.base_km, 0)) if p.base_km is not None else tr('pc_p_sans_lieu'))))
    return 0


def cmd_telecharger(a):
    from .telechargement import Telechargement, sortie_par_defaut
    s = _session(a.nom)
    if s is None:
        return 2
    try:
        st = s.rafraichir()
    except Exception as e:
        return _erreur(e)
    voulus = [c.strip('/') for c in a.chemins]
    fs = [f for f in st.fichiers if any(f.chemin == c or f.chemin.startswith(c + '/') for c in voulus)]
    if not fs:
        print(tr('pt_rien_a_telecharger'), file=sys.stderr)
        return 2

    def evt(ev):
        if ev.get('genre') == 'fini':
            print(tr('pt_cli_fini', chemin=ev['local']))
        elif ev.get('genre') == 'erreur':
            print(tr('pt_dl_erreur', chemin=ev.get('chemin', ''), erreur=ev.get('erreur', '')), file=sys.stderr)
    from ...core import nova
    en_ligne = bool(a.en_ligne) and a.astrometrie in ('auto', 'nova')
    if en_ligne and not nova.configure():
        print(tr('pt_nova_sans_cle'), file=sys.stderr)
        return 2
    r = Telechargement(s, fs, a.dossier or sortie_par_defaut(), a.format, not a.sans_originaux, a.astrometrie,
                       rapporter=evt, en_ligne=en_ligne).executer()
    print(tr('pt_dl_fin', ok=r.get('ok', 0), deja=r.get('deja', 0), echec=r.get('echec', 0),
             annule=r.get('annule', 0), dossier=r.get('dossier', '')))
    return 0 if not r.get('echec') else 1


def cmd_mesurer(a):
    import math

    from . import astro
    from .analyses.parallaxe import image as I
    out = []
    for c in a.images:
        try:
            img = I.lire(c)
            lh = I.lieu_et_heure(img.entete)
            ech = I.echelle_arcsec(img)
            if a.cible in ('lune', 'moon'):
                r_att = math.degrees(math.asin(astro.R_LUNE_KM / 384400.0)) * 3600 / ech if ech == ech else None
                m = I.centre_lune(img.donnees, r_att)
                m.pop('essais', None)
            else:
                m = I.trait_principal(img.donnees)
            ra, dec = I.pixel_vers_radec(img, m['x'], m['y']) if img.wcs is not None else (None, None)
        except Exception as e:
            print('%s : %s' % (c, e), file=sys.stderr)
            return 1
        out.append({'fichier': c, 'mesure': m, 'ra': ra, 'dec': dec, 'echelle_arcsec': ech,
                    'instant': lh['milieu'].isoformat() if lh['milieu'] else None, 'lat': lh['lat'],
                    'lon': lh['lon']})
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1, default=float))
        return 0
    for o in out:
        print(tr('pt_cli_mesure', fichier=o['fichier'], x=_dec(o['mesure']['x'], 2), y=_dec(o['mesure']['y'], 2),
                 ra='—' if o['ra'] is None else _dec(o['ra'], 5), dec='—' if o['dec'] is None else _dec(o['dec'], 5),
                 t=o['instant'] or '—'))
    return 0


def visees_depuis_json(d: dict):
    """Format du fichier de visées (voir l'aide de `coupole partages calculer`)."""
    from .analyses.parallaxe import calcul as C

    def t(x):
        return D.datetime.fromisoformat(str(x).replace('Z', '+00:00')).astimezone(D.timezone.utc)
    vs = []
    for v in d['visees']:
        pts = [C.Point(t(p['instant']), p.get('ra'), p.get('dec'), p.get('h'), p.get('az')) for p in v['points']]
        vs.append(C.Visee(v.get('nom', ''), float(v['lat']), float(v['lon']), float(v.get('alt_m', 0)), pts,
                          v.get('refraction', 'sans'), float(v.get('sigma_arcsec', 30)), float(v.get('sigma_t', 0.5)),
                          float(v.get('sigma_pos_m', 30)), float(v.get('decalage_horloge', 0))))
    return vs


def cmd_calculer(a):
    from .analyses.parallaxe import calcul as C
    from .analyses.parallaxe import rapport as R
    try:
        with open(a.fichier, encoding='utf-8') as fh:
            d = json.load(fh)
        vs = visees_depuis_json(d)
        cible = d.get('cible', 'lune')
        methode = d.get('methode', 'deux')
        if methode == 'deux':
            if len(vs) < 2:
                raise C.ErreurCalcul('pc_err_deux_visees')
            res = C.distance_lune(vs[0], vs[1], tuple(d['etoile']) if d.get('etoile') else None) if cible == 'lune' \
                else C.altitude_iss(vs[0], vs[1], tle=tuple(d['tle']) if d.get('tle') else None)
        elif methode == 'diurne':
            res = dict(C.lune_parallaxe_diurne(vs[0]), genre='diurne')
        elif methode == 'vitesse':
            res = dict(C.iss_vitesse_angulaire(vs[0], d.get('cap')), genre='vitesse')
        else:
            res = dict(C.iss_orbite_circulaire(vs[0]), genre='orbite')
    except C.ErreurCalcul as e:
        print(tr(e.cle, **e.valeurs), file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError) as e:
        print('%s: %s' % (type(e).__name__, e), file=sys.stderr)
        return 2
    if a.html and res.get('genre') in ('lune', 'iss'):
        R.ecrire_html(a.html, res)
    if a.pdf and res.get('genre') in ('lune', 'iss'):
        R.ecrire_pdf(a.pdf, res)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
        return 0
    if res.get('genre') in ('lune', 'iss'):
        for k, v in R.lignes_resultats(res):
            print('%-45s %s' % (k, v))
    else:
        print(tr('pc_res_' + res['genre'], **{k: _dec(v, 2) if isinstance(v, float) else v for k, v in res.items()
                                              if k != 'instant'}))
    return 0


def cmd_deposer(a):
    from . import depot
    from .mesures import angle, instant, nombre
    s = _session(a.nom)
    if s is None:
        return 2
    try:
        s.rafraichir()
        tableau = None
        if a.tableau:
            _, ts = s.lire_tableau(a.tableau)
            tableau = ts[0] if ts else None
        mesure = {}
        for x in a.valeurs:
            role, _, v = x.partition('=')
            role = role.strip()
            if role == 'date':
                mesure[role] = instant(v if any(z in v.upper() for z in ('UTC', 'TU', 'Z')) else v + ' UTC').valeur
            elif role in ('latitude', 'longitude', 'azimut', 'hauteur', 'ra', 'dec'):
                mesure[role] = angle(v).valeur
            elif role == 'altitude':
                mesure[role] = nombre(v).valeur
            else:
                mesure[role] = v
        plan = depot.preparer(s, a.dossier, a.fichiers, a.tableau if tableau else '', tableau, mesure,
                              mesure.get('auteur', ''))
    except Exception as e:
        return _erreur(e)
    print(tr('pt_cli_plan', partage=s.memorise.nom))
    for f in plan.fichiers:
        print('  %s → %s' % (f.local, f.distant))
    if plan.tableau:
        print('  ' + tr('pt_depot_confirmer_ligne', tableau=plan.tableau, feuille=plan.feuille))
        for t, v in plan.colonnes:
            if v:
                print('      %s = %s' % (t, v))
    if not a.oui:
        print(tr('pt_cli_sans_oui'))
        return 0
    try:
        r = depot.executer(s, plan, str(s.dossier / 'sauvegardes'))
    except Exception as e:
        return _erreur(e)
    print(tr('pt_depot_ok_fichiers', n=len(r['fichiers'])))
    if r['tableau'] == 'ligne':
        print(tr('pt_depot_ok_ligne', ligne=r['ligne'], sauvegarde=r['sauvegarde']))
    elif r['tableau'] == 'csv':
        print(tr('pt_depot_ok_csv', csv=r['csv'], sauvegarde=r['sauvegarde']))
    return 0


def cmd_de440(a):
    from ...core import reseau, sources
    from . import astro
    dest = str(astro.dossier_ephemerides() / astro.NOM_DE440)
    try:
        reseau.telecharger(sources.valeur('ephemerides.de440s'), dest)
    except Exception as e:
        return _erreur(e)
    print(tr('pc_de440_ok'))
    if not astro.jplephem_present():
        print(tr('pc_de440_sans_jplephem'))
    return 0
