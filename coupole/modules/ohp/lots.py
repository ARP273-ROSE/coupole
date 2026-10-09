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

from ...core.astro import ecart_angle_np, mediane_angle, sep_deg, sep_deg_matrice, sexa, utc
from ...core.i18n import tr
from .astrometrie import TOL_ANGLE, TOL_ECHELLE
from .cibles import FIXES, MOBILES, dossier_categorie, nom_affiche
from .conversion import sur

SANS = {'fr': '_sans_solution_astrometrique', 'en': '_no_astrometric_solution'}
FICHIER_EMPREINTES = 'lots_empreintes.json'     # dans _traitement/ : empreinte du dernier LOT.txt écrit par lot
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


def _champs_np(infos):
    return {k: np.array([x[k] for x in infos], dtype=float) for k in ('ra', 'dec', 'angle', 'parite', 'echelle', 'nx')}


def _compatibles_np(a, b):
    """Matrice « a[i] et b[j] se superposent » (même règle que la version par paire : séparation < champ/4,
    angle à 5°, même parité, échelle à 2 %)."""
    fov = (a['nx'] * a['echelle'] / 3600)[:, None]
    with np.errstate(divide='ignore', invalid='ignore'):
        ech = np.abs(a['echelle'][:, None] / b['echelle'][None, :] - 1) < TOL_ECHELLE
    return ((sep_deg_matrice(a['ra'], a['dec'], b['ra'], b['dec']) < fov / 4) &
            (ecart_angle_np(a['angle'][:, None], b['angle'][None, :]) < TOL_ANGLE) &
            (a['parite'][:, None] == b['parite'][None, :]) & ech)


def grouper_champs(items):
    """items : [(id, info)] d'un même objet fixe et instrument → groupes de même pointage.

    Le pointage le plus « central » (le plus de voisins compatibles, sur 600 poses au plus) fonde un groupe avec
    toutes les poses compatibles, et l'on recommence sur le reste.  Comptes en matrices numpy : 0,67 s → quelques
    dizaines de ms pour la banque entière (532 585 appels Python évités)."""
    reste = list(items)
    groupes = []
    while reste:
        echant = reste if len(reste) <= 600 else reste[::len(reste) // 600 + 1]
        e = _champs_np([it[1] for it in echant])
        best = echant[int(np.argmax(_compatibles_np(e, e).sum(axis=1)))]
        r = _champs_np([it[1] for it in reste])
        ok = _compatibles_np(_champs_np([best[1]]), r)[0]
        g = [it for it, o in zip(reste, ok) if o]
        if not any(it is best for it in g):
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


class _Listages:
    """Contenu des dossiers de destination, lu une fois par dossier (un `listdir` au lieu d'un `stat` par
    fichier : sur un partage réseau chaque appel est un aller-retour)."""

    def __init__(self):
        self.memo = {}

    def existe(self, chemin: str) -> bool:
        d, nom = os.path.split(chemin)
        if d not in self.memo:
            try:
                self.memo[d] = {n.lower() for n in os.listdir(chemin_os(d))}
            except OSError:
                self.memo[d] = set()
        return nom.lower() in self.memo[d]


def _libre(cible: str, pris: set, actuels: set, listages: '_Listages | None' = None) -> str:
    """Nom de fichier libre : ni déjà prévu dans ce rangement (casse indifférente : Windows), ni déjà présent sur
    le disque pour un fichier étranger au rangement (jamais d'écrasement).

    Un fichier déjà à sa place (son nom est l'un des emplacements actuels) n'interroge pas le disque."""
    base, ext = cible, ''
    for e in ('.fits.fz', '.xisf', '.fits'):
        if cible.lower().endswith(e):
            base, ext = cible[:-len(e)], cible[-len(e):]
            break
    existe = listages.existe if listages is not None else os.path.exists
    nom, n = cible, 1
    while nom.lower() in pris or (os.path.abspath(nom).lower() not in actuels and existe(nom)):
        n += 1
        nom = '%s_%d%s' % (base, n, ext)
    return nom


def _lire_empreintes(racine) -> dict:
    try:
        with open(os.path.join(racine, '_traitement', FICHIER_EMPREINTES), encoding='utf-8') as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _ecrire_si_change(chemin, texte, encodage, cle, empreintes, nouvelles):
    """Écrit (atomiquement) seulement si le contenu a changé depuis le dernier rangement : relancer un
    traitement pour une image ne réécrit plus les 682 LOT.txt de la banque."""
    import hashlib
    from ...core.config import ecrire_atomique
    h = hashlib.sha1(texte.encode('utf-8')).hexdigest()
    nouvelles[cle] = h
    if empreintes.get(cle) == h and os.path.exists(chemin_os(chemin)):    # (un LOT.txt effacé est récrit)
        return False
    if cle not in empreintes:                       # premier rangement connu : le fichier existant est peut-être le bon
        try:
            with open(chemin_os(chemin), encoding=encodage, newline='') as f:
                if f.read() == texte:
                    return False
        except (OSError, UnicodeError):
            pass
    ecrire_atomique(chemin, texte, encodage)
    return True


def ranger(racine, tout, L, maj_info, ext='.xisf', conflits=None):
    """Déplace les fichiers convertis à leur place (jamais d'écrasement), écrit LOT.txt et INDEX_LOTS.csv.

    tout : [(id, info)] ; maj_info(id, info) enregistre le nouvel emplacement.  `conflits` (liste) reçoit
    (nom voulu, nom retenu) quand un fichier étranger occupait déjà le nom.  Renvoie la liste de l'index.
    """
    lots = plan_des_lots(tout, L)
    pris = set()
    actuels = {os.path.abspath(info.get('final') or info['staging']).lower() for _, info in tout}
    listages = _Listages()
    plan = []
    for cle in sorted(lots):
        dossier = os.path.join(racine, *cle)
        for i, info in sorted(lots[cle], key=lambda it: (it[1]['mjd'], it[0])):
            ext_i = info.get('extension', ext)
            voulu = os.path.join(dossier, nom_fichier(info, L) + ext_i)
            cible = _libre(voulu, pris, actuels, listages)
            if cible != voulu and conflits is not None and not voulu.lower() in pris:
                conflits.append((voulu, cible))
            pris.add(cible.lower())
            plan.append((cle, i, info, cible))
    # deux temps : ce qui doit bouger repasse par la zone de conversion, puis rejoint sa place
    staging_dir = os.path.join(racine, '_traitement', 'converties')
    quittes = set()                                   # dossiers d'où un fichier est parti (peut-être vidés)
    for cle, i, info, cible in plan:
        actuel = info.get('final') or info['staging']
        if actuel != cible and actuel != info['staging'] and os.path.exists(actuel):
            quittes.add(os.path.dirname(actuel))
            if not os.path.isdir(os.path.dirname(info['staging'])):
                os.makedirs(staging_dir, exist_ok=True)
                info['staging'] = os.path.join(staging_dir, i + os.path.splitext(actuel)[1])
            os.replace(chemin_os(actuel), chemin_os(info['staging']))
            info['final'] = None
    crees = set()
    for cle, i, info, cible in plan:
        actuel = info.get('final') or info['staging']
        if actuel != cible:
            d = os.path.dirname(cible)
            if d not in crees:
                os.makedirs(chemin_os(d), exist_ok=True)
                crees.add(d)
            quittes.add(os.path.dirname(actuel))
            os.replace(chemin_os(info['staging']), chemin_os(cible))
            info['final'] = cible
            maj_info(i, info)
    par_lot = C.defaultdict(list)                     # (une passe : plus de filtrage du plan entier par lot)
    for c, i, info, _ in plan:
        par_lot[c].append((i, info))
    empreintes = _lire_empreintes(racine)
    nouvelles = {}
    # LOT.txt écrits par 8 fils : sur un partage réseau, chaque écriture atomique coûte plusieurs allers-retours
    # (création, écriture, renommage) que des fils recouvrent ; l'ordre de l'index reste celui des lots
    import concurrent.futures as F
    with F.ThreadPoolExecutor(8, thread_name_prefix='lots') as pool:
        index = list(pool.map(lambda cle: ecrire_lot(cle, os.path.join(racine, *cle), par_lot[cle], L, empreintes,
                                                     nouvelles), sorted(lots)))
    # dossiers devenus vides (lots disparus) : seulement ceux qu'un fichier a quittés, et leurs parents — plus de
    # parcours de toute l'arborescence à chaque rangement
    _nettoyer_vides(racine, quittes)
    import io
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow([tr('csv_' + c, 'fr') + ' (' + tr('csv_' + c, 'en') + ')' if tr('csv_' + c, 'fr') != tr('csv_' + c, 'en')
                else tr('csv_' + c, 'fr') for c in ('dossier', 'type', 'objet', 'lot', 'filtre', 'poses',
                                                     'pose_totale_s', 'nuits', 'centre_ra', 'centre_dec',
                                                     'angle_deg', 'alignement')])
    for r in index:
        w.writerow(r)
    _ecrire_si_change(os.path.join(racine, 'INDEX_LOTS.csv'), buf.getvalue(), 'utf-8-sig', '__index__', empreintes,
                      nouvelles)
    if nouvelles != empreintes:
        from ...core.config import ecrire_json_atomique
        try:
            ecrire_json_atomique(os.path.join(racine, '_traitement', FICHIER_EMPREINTES), nouvelles, indent=None)
        except OSError:
            pass
    return index


def _nettoyer_vides(racine, dossiers):
    """Retire les dossiers vidés (ou ne contenant plus que LOT.txt / QUALITE.*) parmi `dossiers` et leurs
    parents, sans jamais remonter au-dessus de `racine` ni toucher `_traitement`."""
    racine = os.path.abspath(racine)
    candidats = set()
    for d in dossiers:
        d = os.path.abspath(d)
        while d.startswith(racine + os.sep) and d != racine:
            if '_traitement' in os.path.relpath(d, racine).split(os.sep):
                break
            candidats.add(d)
            d = os.path.dirname(d)
    for r in sorted(candidats, key=lambda t: -len(t)):
        try:
            contenu = os.listdir(chemin_os(r))
        except OSError:
            continue
        if contenu and set(contenu) <= {'LOT.txt', 'QUALITE.csv', 'QUALITE.txt'}:
            for f in contenu:
                os.remove(chemin_os(os.path.join(r, f)))
            contenu = []
        if not contenu:
            try:
                os.rmdir(chemin_os(r))
            except OSError:
                pass


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


def ecrire_lot(cle, dossier, items, L, empreintes=None, nouvelles=None):
    """LOT.txt du lot (réécrit seulement s'il a changé quand `empreintes` est fourni) ; rend la ligne d'index."""
    infos = [it[1] for it in items]
    fr, geo, n, tot, nuits, sans, mobile = _textes_lot(cle, infos, items, 'fr')
    en = _textes_lot(cle, infos, items, 'en')[0]
    texte = '\n'.join(['=== Français ==='] + fr + ['', '=== English ==='] + en) + '\n'
    _ecrire_si_change(os.path.join(dossier, 'LOT.txt'), texte, 'utf-8', '/'.join(cle),
                      empreintes if empreintes is not None else {}, nouvelles if nouvelles is not None else {})
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
