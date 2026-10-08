"""Tri en lots empilables, fiches LOT.txt, INDEX_LOTS.csv et journal.csv (repris de ohp_xisf.py).

Un lot = ce qu'on empile ensemble : même objet, même instrument, même filtre,
et en plus même champ (objet fixe, toutes nuits confondues) ou même nuit
(objet mobile).  LOT.txt est écrit en français puis en anglais ; les en-têtes
de colonnes des CSV sont bilingues.
"""
from __future__ import annotations

import collections as C
import csv
import datetime as D
import json
import math
import os

import numpy as np

from ...core.astro import ecart_angle, mediane_angle, sep_deg, sexa, utc
from ...core.i18n import tr
from .astrometrie import TOL_ANGLE, TOL_ECHELLE
from .cibles import FIXES, MOBILES, dossier_categorie, nom_affiche
from .conversion import sur

SANS = {'fr': '_sans_solution_astrometrique', 'en': '_no_astrometric_solution'}
BONS = ('confirmee', 'validee', 'refaite')


def etiquette_instrument(info) -> str:
    if info['tel'] == 'T120':
        if info['nx'] == 2048:
            return 'T120-bin1'
        if info.get('echelle') and info['echelle'] < 0.70:
            return 'T120-sCMOS'
        return 'T120'
    if info['tel'] == 'IRIS':
        return 'IRIS-%d' % info['nx']
    return '%s-%d' % (sur(info['tel']), info['nx'])


def grouper_champs(items):
    """items : [(id, info)] d'un même objet fixe et instrument → groupes de même pointage."""
    reste = list(items)
    groupes = []

    def compatibles(a, b):
        fov = a['nx'] * a['echelle'] / 3600
        return (sep_deg(a['ra'], a['dec'], b['ra'], b['dec']) < fov / 4 and
                ecart_angle(a['angle'], b['angle']) < TOL_ANGLE and a['parite'] == b['parite'] and
                abs(a['echelle'] / b['echelle'] - 1) < TOL_ECHELLE)

    while reste:
        echant = reste if len(reste) <= 600 else reste[::len(reste) // 600 + 1]
        best = max(echant, key=lambda a: sum(1 for b in echant if compatibles(a[1], b[1])))
        g = [it for it in reste if compatibles(best[1], it[1])]
        if best not in g:
            g.append(best)
        ids = {id(it) for it in g}
        reste = [it for it in reste if id(it) not in ids]
        groupes.append(g)
    groupes.sort(key=lambda g: (-len(g), min(it[1]['mjd'] for it in g)))
    return groupes


def nom_fichier(info, L) -> str:
    d = D.datetime.fromisoformat(info['debut']) if info.get('debut') else utc(info['mjd'])
    pose = ('%g' % info['pose']).replace('.', 'p')
    return '%s_%s_%s_%ss' % (d.strftime('%Y%m%d-%H%M%S'), sur(nom_affiche(info['objet'], L)),
                             info['filtre_dossier'], pose)


def plan_des_lots(tout, L):
    """tout : [(id, info)] des images converties → {clé de lot (tuple de dossiers): [(id, info)]}."""
    lots = C.defaultdict(list)
    nuit_ = 'nuit' if L == 'fr' else 'night'
    champ_ = 'champ' if L == 'fr' else 'field'
    for i, info in tout:
        obj = sur(nom_affiche(info['objet'], L))
        lab = etiquette_instrument(info)
        if info.get('wcs') not in BONS:
            lots[(SANS[L], obj, '%s_%s' % (info['nuit'], lab), info['filtre_dossier'])].append((i, info))
        elif info['cat'] in MOBILES:
            lots[(dossier_categorie(info['cat'], L), obj, '%s_%s_%s' % (nuit_, info['nuit'], lab),
                  info['filtre_dossier'])].append((i, info))
    par_obj = C.defaultdict(list)
    for i, info in tout:
        if info.get('wcs') in BONS and info['cat'] in FIXES:
            par_obj[(info['cat'], info['objet'], etiquette_instrument(info))].append((i, info))
    for (cat, obj, lab), items in sorted(par_obj.items()):
        for k, g in enumerate(grouper_champs(items), 1):
            for i, info in g:
                lots[(dossier_categorie(cat, L), sur(nom_affiche(obj, L)), '%s_%d_%s' % (champ_, k, lab),
                      info['filtre_dossier'])].append((i, info))
    return lots


def chemin_os(p: str) -> str:
    """Chemin tel que le système le veut : sous Windows, au-delà de ~250 caractères, préfixe « \\\\?\\ » (chemins longs)."""
    if os.name == 'nt' and len(p) > 250 and not p.startswith('\\\\?\\'):
        return '\\\\?\\' + os.path.abspath(p)
    return p


def _libre(cible: str, pris: set, actuels: set) -> str:
    """Nom de fichier libre : ni déjà prévu dans ce rangement (casse indifférente : Windows), ni déjà présent sur
    le disque pour un fichier étranger au rangement (jamais d'écrasement)."""
    base, ext = cible, ''
    for e in ('.fits.fz', '.xisf', '.fits'):
        if cible.lower().endswith(e):
            base, ext = cible[:-len(e)], cible[-len(e):]
            break
    nom, n = cible, 1
    while nom.lower() in pris or (os.path.exists(nom) and os.path.abspath(nom).lower() not in actuels):
        n += 1
        nom = '%s_%d%s' % (base, n, ext)
    return nom


def ranger(racine, tout, L, maj_info, ext='.xisf', conflits=None):
    """Déplace les fichiers convertis à leur place (jamais d'écrasement), écrit LOT.txt et INDEX_LOTS.csv.

    tout : [(id, info)] ; maj_info(id, info) enregistre le nouvel emplacement.  `conflits` (liste) reçoit
    (nom voulu, nom retenu) quand un fichier étranger occupait déjà le nom.  Renvoie la liste de l'index.
    """
    lots = plan_des_lots(tout, L)
    pris = set()
    actuels = {os.path.abspath(info.get('final') or info['staging']).lower() for _, info in tout}
    plan = []
    for cle in sorted(lots):
        dossier = os.path.join(racine, *cle)
        for i, info in sorted(lots[cle], key=lambda it: (it[1]['mjd'], it[0])):
            ext_i = info.get('extension', ext)
            voulu = os.path.join(dossier, nom_fichier(info, L) + ext_i)
            cible = _libre(voulu, pris, actuels)
            if cible != voulu and conflits is not None and not voulu.lower() in pris:
                conflits.append((voulu, cible))
            pris.add(cible.lower())
            plan.append((cle, i, info, cible))
    # deux temps : ce qui doit bouger repasse par la zone de conversion, puis rejoint sa place
    staging_dir = os.path.join(racine, '_traitement', 'converties')
    for cle, i, info, cible in plan:
        actuel = info.get('final') or info['staging']
        if actuel != cible and actuel != info['staging'] and os.path.exists(actuel):
            if not os.path.isdir(os.path.dirname(info['staging'])):
                os.makedirs(staging_dir, exist_ok=True)
                info['staging'] = os.path.join(staging_dir, i + os.path.splitext(actuel)[1])
            os.replace(chemin_os(actuel), chemin_os(info['staging']))
            info['final'] = None
    for cle, i, info, cible in plan:
        actuel = info.get('final') or info['staging']
        if actuel != cible:
            os.makedirs(chemin_os(os.path.dirname(cible)), exist_ok=True)
            os.replace(chemin_os(info['staging']), chemin_os(cible))
            info['final'] = cible
            maj_info(i, info)
    index = []
    for cle in sorted(lots):
        items = [(i, info) for c, i, info, _ in plan if c == cle]
        index.append(ecrire_lot(cle, os.path.join(racine, *cle), items, L))
    # dossiers devenus vides (lots disparus)
    for r, _, _ in sorted(os.walk(racine), key=lambda t: -len(t[0])):
        if os.path.basename(r) == '_traitement' or '_traitement' in os.path.relpath(r, racine).split(os.sep) \
                or r == racine or not os.path.isdir(r):
            continue
        if os.listdir(r) and set(os.listdir(r)) <= {'LOT.txt', 'QUALITE.csv', 'QUALITE.txt'}:
            for f in os.listdir(r):
                os.remove(os.path.join(r, f))
        if not os.listdir(r):
            os.rmdir(r)
    import io
    from ...core.config import ecrire_atomique
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow([tr('csv_' + c, 'fr') + ' (' + tr('csv_' + c, 'en') + ')' if tr('csv_' + c, 'fr') != tr('csv_' + c, 'en')
                else tr('csv_' + c, 'fr') for c in ('dossier', 'type', 'objet', 'lot', 'filtre', 'poses',
                                                     'pose_totale_s', 'nuits', 'centre_ra', 'centre_dec',
                                                     'angle_deg', 'alignement')])
    for r in index:
        w.writerow(r)
    ecrire_atomique(os.path.join(racine, 'INDEX_LOTS.csv'), buf.getvalue(), 'utf-8-sig')
    return index


def _textes_lot(cle, infos, items, L):
    n = len(infos)
    tot = sum(x['pose'] for x in infos)
    nuits = sorted({x['nuit'] for x in infos})
    poses = C.Counter('%g' % x['pose'] for x in infos)
    systemes = sorted({x.get('filtre_sys', '') for x in infos})
    ok = [x for x in infos if x.get('ra') is not None]
    T = lambda k, **kw: tr('lot_' + k, L, **kw)  # noqa: E731
    l = [T('lot', v='/'.join(cle)),
         T('objet', objet=nom_affiche(infos[0]['objet'], L), type=cle[0]),
         T('noms', v=', '.join(sorted({x['nom_base'] for x in infos}))),
         T('instrument', v=etiquette_instrument(infos[0])),
         T('filtre', f=infos[0]['filtre'], s=', '.join(s or '?' for s in systemes)),
         T('poses', n=n, tot='%.0f' % tot, hms=str(D.timedelta(seconds=round(tot)))),
         T('durees', v=', '.join('%s x %s s' % (v, k) for k, v in sorted(poses.items(), key=lambda t: float(t[0])))),
         T('nuits', v=', '.join(nuits))]
    geo = None
    if ok:
        vx = sum(math.cos(math.radians(x['dec'])) * math.cos(math.radians(x['ra'])) for x in ok)
        vy = sum(math.cos(math.radians(x['dec'])) * math.sin(math.radians(x['ra'])) for x in ok)
        vz = sum(math.sin(math.radians(x['dec'])) for x in ok)
        ra = math.degrees(math.atan2(vy, vx)) % 360
        de = math.degrees(math.atan2(vz, math.hypot(vx, vy)))
        ang = mediane_angle([x['angle'] for x in ok])
        ech = float(np.median([x['echelle'] for x in ok]))
        dmax = max(sep_deg(ra, de, x['ra'], x['dec']) for x in ok) * 60
        geo = (ra, de, ang)
        l += [T('centre', ra=sexa(ra, heures=True, signe=False, dec=1), de=sexa(de, dec=0), rad='%.5f' % ra,
                ded='%+.5f' % de, dmax='%.1f' % dmax),
              T('angle', a='%.1f' % ang, e='%.3f' % ech)]
    st = C.Counter(x.get('wcs') for x in infos)
    l.append(T('solutions', v=', '.join('%s %d' % ((k if L == 'fr' else tr('ohp_wcs_' + (k or 'aucune'), 'en')), n)
                                         for k, n in sorted(st.items(), key=lambda kv: str(kv[0])))))
    dp = sum(1 for x in infos if x.get('date_partagee'))
    if dp:
        l.append(T('dates', n=dp))
    sans = cle[0] in SANS.values()
    mobile = infos[0]['cat'] in MOBILES
    if sans:
        l.append(T('conseil_sans'))
    elif mobile:
        l.append(T('conseil_mobile'))
    else:
        l.append(T('conseil_fixe_8' if n >= 8 else 'conseil_fixe_3' if n >= 3 else 'conseil_fixe_peu'))
    fmt = infos[0].get('format', 'xisf')
    l.append(T('fichiers_' + fmt))
    l.append('')
    l.append('%-44s %-8s %10s %-10s' % (T('col_fichier'), T('col_pose'), T('col_wcs'), T('col_date')))
    for i, x in items:
        l.append('%-44s %-8g %10s %-10s' % (os.path.basename(x['final']), x['pose'], x.get('wcs'),
                                           T('oui') if x.get('date_partagee') else ''))
    return l, geo, n, tot, nuits, sans, mobile


def ecrire_lot(cle, dossier, items, L):
    infos = [it[1] for it in items]
    fr, geo, n, tot, nuits, sans, mobile = _textes_lot(cle, infos, items, 'fr')
    en = _textes_lot(cle, infos, items, 'en')[0]
    from ...core.config import ecrire_atomique
    ecrire_atomique(os.path.join(dossier, 'LOT.txt'),
                    '\n'.join(['=== Français ==='] + fr + ['', '=== English ==='] + en) + '\n')
    alignement = (tr('lot_align_aucun', 'fr') + ' / ' + tr('lot_align_aucun', 'en')) if sans \
        else 'CometAlignment' if mobile else 'StarAlignment'
    return ['/'.join(cle), cle[0], nom_affiche(infos[0]['objet'], L), cle[2], infos[0]['filtre'], n, round(tot, 1),
            ' '.join(nuits), round(geo[0], 5) if geo else '', round(geo[1], 5) if geo else '',
            round(geo[2], 2) if geo else '', alignement]


COLONNES_JOURNAL = ['fichier_source', 'destination', 'octets_fits', 'octets_xisf', 'ratio', 'ecart_max_adu',
                    'statut', 'wcs', 'doutes', 'ecart_astap_arcsec', 'deplacement_centre_arcsec',
                    'mots_cles_modifies', 'date', 'pose', 'doublon_de', 'erreur', 'url']


def ecrire_journal(chemin, racine, lignes):
    """lignes : [(id, url, statut, info)] → journal.csv (mêmes colonnes que le traitement de référence)."""
    import io
    from ...core.config import ecrire_atomique
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow(COLONNES_JOURNAL)
    for i, url, st, info in lignes:
        x = json.loads(info) if isinstance(info, str) else (info or {})
        try:
            dest = os.path.relpath(x['final'], racine) if x.get('final') else ''
        except ValueError:                          # autre lecteur Windows : chemin absolu
            dest = x.get('final', '')
        w.writerow([x.get('source', ''), dest,
                    x.get('octets_fits', ''), x.get('octets_sortie', x.get('octets_xisf', '')), x.get('ratio', ''),
                    x.get('ecart_max', ''), st, x.get('wcs', ''), ' | '.join(x.get('doutes', [])),
                    x.get('ecart_astap_arcsec', ''), x.get('deplacement_centre_arcsec', ''),
                    ' '.join(x.get('modifs', [])), x.get('date', ''), x.get('pose_ctrl', ''),
                    x.get('doublon_de', ''), x.get('erreur', ''), url])
    ecrire_atomique(chemin, buf.getvalue(), 'utf-8-sig')
