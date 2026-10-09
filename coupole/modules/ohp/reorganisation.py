"""Réorganiser des fichiers déjà convertis par Coupole (ailleurs, ou selon un ancien rangement).

Un fichier produit par Coupole porte son origine dans son en-tête : la propriété XISF ``OHP:Source:URL``
(adresse du FITS d'origine dans la banque) ou, pour les sorties FITS, la carte ``HISTORY « … : converti de
<fichier> »``.  On retrouve ainsi la ligne d'inventaire, puis tout ce dont ``lots.ranger`` a besoin (objet,
catégorie, nuit, instrument, filtre, solution astrométrique relue dans l'en-tête).  Rien n'est jamais copié ni
écrasé : les fichiers sont déplacés (``os.replace``) et un conflit de nom reçoit un suffixe, consigné dans
``JOURNAL.txt``.
"""
from __future__ import annotations

import datetime as D
import os
import re
import xml.etree.ElementTree as ET

from ...core import xisf
from ...core.astro import utc
from ...core.fitsentete import Entete
from .astrometrie import wcs_de
from .conversion import FILTRES, info_de_base, sur

EXTENSIONS = ('.xisf', '.fits', '.fits.fz', '.fit')
RE_CONVERTI = re.compile(r'(?:converti de|converted from)\s+(\S+)', re.I)


def lire_entete_xisf(chemin) -> tuple[list, dict]:
    """(cartes FITS [(nom, valeur, commentaire)], propriétés {id: valeur}) sans lire les pixels."""
    with open(chemin, 'rb') as f:
        debut = f.read(16)
        if debut[:8] != b'XISF0100':
            raise xisf.ErreurXISF('signature missing')
        lg = int.from_bytes(debut[8:12], 'little')
        if lg > xisf.ENTETE_MAX:
            raise xisf.ErreurXISF('header too large')
        xml = f.read(lg)
    try:
        racine = ET.fromstring(xml.rstrip(b'\0 \t\r\n'))     # (lecture tolérante : bourrage, autres logiciels)
    except ET.ParseError as e:
        raise xisf.ErreurXISF('invalid XML header: %s' % e)
    im = racine.find(xisf.NS + 'Image')
    if im is None:
        raise xisf.ErreurXISF('no image')
    mots = [(k.get('name'), k.get('value') or '', k.get('comment') or '') for k in im.findall(xisf.NS + 'FITSKeyword')
            if k.get('name')]
    props = {p.get('id'): (p.get('value') if p.get('value') is not None else (p.text or ''))
             for p in im.findall(xisf.NS + 'Property')}
    geo = [int(v) for v in (im.get('geometry') or '0:0:1').split(':')]
    props['_nx'], props['_ny'] = geo[0], geo[1]
    return mots, props


def lire_entete_fits(chemin) -> tuple[list, dict]:
    import warnings
    from astropy.io import fits
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with fits.open(chemin, memmap=True) as hd:
            h = hd[1].header if (len(hd) > 1 and hd[0].data is None) else hd[0].header
            mots = []
            for carte in h.cards:
                nom = carte.keyword
                if nom in ('HISTORY', 'COMMENT'):
                    mots.append((nom, '', str(carte.value)))
                else:
                    v = carte.value
                    mots.append((nom, ("'%s'" % v) if isinstance(v, str) else ('T' if v is True else 'F' if v is False
                                                                              else str(v)), carte.comment or ''))
            props = {'_nx': h.get('ZNAXIS1', h.get('NAXIS1', 0)), '_ny': h.get('ZNAXIS2', h.get('NAXIS2', 0))}
    return mots, props


def source_de(mots, props) -> str:
    """Nom du FITS d'origine (sans dossier) écrit dans l'en-tête, ou ''."""
    url = props.get('OHP:Source:URL', '')
    if url:
        return url.rsplit('/', 1)[-1]
    for nom, _, com in mots:
        if nom == 'HISTORY':
            m = RE_CONVERTI.search(com)
            if m:
                return m.group(1)
    return ''


def _entete(mots):
    cartes = []
    for nom, val, com in mots:
        if nom in ('HISTORY', 'COMMENT'):
            cartes.append(('%-8s %s' % (nom, com))[:80].ljust(80))
        else:
            cartes.append(('%-8s= %s / %s' % (nom, val, com))[:80].ljust(80))
    return Entete(cartes)


def analyser(chemin) -> dict:
    """Lecture de l'en-tête d'un fichier converti (sans les pixels) et de sa solution astrométrique.

    Sans l'inventaire : s'exécute dans un processus de lecture (le WCS d'astropy coûte ~8 ms par fichier, la
    lecture un aller-retour réseau).  Rend {'raison'} en cas d'échec, sinon les champs utiles au rattachement."""
    bas = chemin.lower()
    try:
        if bas.endswith('.xisf'):
            mots, props = lire_entete_xisf(chemin)
        elif bas.endswith(('.fits', '.fits.fz', '.fit')):
            mots, props = lire_entete_fits(chemin)
        else:
            return {'chemin': chemin, 'raison': 'format'}
    except Exception:
        return {'chemin': chemin, 'raison': 'illisible'}
    source = source_de(mots, props)
    if not source:
        return {'chemin': chemin, 'raison': 'pas_coupole'}
    ent = _entete(mots)
    nx = int(props.get('_nx') or ent.getf('NAXIS1') or 0)
    ny = int(props.get('_ny') or ent.getf('NAXIS2') or 0)
    sol = wcs_de(ent, nx, ny) if nx and ny else None
    try:
        taille = os.path.getsize(chemin)
    except OSError:
        taille = None
    return {'chemin': chemin, 'raison': '', 'source': source, 'date_obs': ent.gets('DATE-OBS'), 'nx': nx, 'ny': ny,
            'sol': sol, 'statut': props.get('OHP:Astrometry:Status'), 'objet_entete': ent.gets('OBJECT'),
            'taille': taille, 'url': props.get('OHP:Source:URL', '')}


def index_par_fichier(inventaire) -> dict:
    """{nom du FITS d'origine: [lignes d'inventaire]} : un dictionnaire, et non un parcours de l'inventaire par
    fichier (7 625 fichiers × 7 989 lignes = 61 millions de comparaisons)."""
    idx = {}
    for x in inventaire.images:
        idx.setdefault(x['access_url'].rsplit('/', 1)[-1], []).append(x)
    return idx


def rattacher_analyse(a: dict, index: dict) -> tuple[dict | None, dict | None, str]:
    """(ligne d'inventaire, info prête pour le rangement, raison d'échec) à partir de `analyser()`."""
    if a.get('raison'):
        return None, None, a['raison']
    chemin = a['chemin']
    bas = chemin.lower()
    candidats = index.get(a['source'], [])
    if not candidats:
        return None, None, 'inconnu_inventaire'
    d_hdr = a.get('date_obs')
    x = candidats[0]
    exacts = [y for y in candidats if a.get('url') and y['access_url'] == a['url']]
    if exacts:                                   # adresse complète dans l'en-tête : plus d'ambiguïté (T120/T152…)
        candidats = exacts
        x = exacts[0]
    if len(candidats) > 1 and d_hdr:
        try:
            d = D.datetime.fromisoformat(d_hdr[:23])
            x = min(candidats, key=lambda y: abs((utc(y['t_min']) - d).total_seconds()))
        except ValueError:
            pass
    nx, ny = int(a['nx'] or x['s_xel1']), int(a['ny'] or x['s_xel2'])
    info = info_de_base(x)
    sol = a.get('sol')
    statut = a.get('statut') or ('validee' if sol else 'echec')
    if sol is not None:
        info.update(ra=sol['ra'], dec=sol['dec'], echelle=sol['echelle'], angle=sol['angle'], parite=sol['parite'])
    info['wcs'] = statut if statut in ('confirmee', 'validee', 'refaite', 'douteuse', 'echec') else 'echec'
    if sol is None and info['wcs'] in ('confirmee', 'validee', 'refaite'):
        info['wcs'] = 'echec'
    f_norm, f_sys, f_dos = FILTRES.get(x['filter_name'], (x['filter_name'], '', sur(x['filter_name'])))
    info.update(filtre=f_norm, filtre_sys=f_sys, filtre_dossier=f_dos, nx=nx, ny=ny,
                debut=(d_hdr or utc(x['t_min']).isoformat(timespec='milliseconds')),
                objet_affiche=a.get('objet_entete') or x['objet'], format='xisf' if bas.endswith('.xisf') else
                ('fz' if bas.endswith('.fz') else 'fits'), reorganise=True)
    if a.get('taille') is not None:
        info['octets_sortie'] = a['taille']
    return x, info, ''


def rattacher(chemin, inventaire) -> tuple[dict | None, dict | None, str]:
    """(ligne d'inventaire, info prête pour le rangement, raison d'échec) pour un fichier converti."""
    return rattacher_analyse(analyser(chemin), index_par_fichier(inventaire))


SEUIL_PROCESSUS = 64            # au-delà, les en-têtes sont lus par plusieurs processus


def lister(dossier_source) -> list[str]:
    """Fichiers convertis sous `dossier_source` (parcours parallèle, `_traitement/` ignoré), triés."""
    from ...core import parcours
    return [f for fs in parcours.lister(os.path.abspath(dossier_source), EXTENSIONS).values() for f in fs
            if not f.lower().endswith('.tmp')]


def inventorier(dossier_source, inventaire, racine, progression=None, arret=None, processus=None) -> tuple[list, list]:
    """Parcourt `dossier_source` : ([(chemin, x, info)], [(chemin, raison)]) ; `_traitement/` est ignoré.

    En-têtes lus par un bassin de processus (au-delà de SEUIL_PROCESSUS fichiers), progression `progression(fait,
    total)` au plus 10 fois par seconde, arrêt immédiat par `arret` (threading.Event) : ce qui est déjà rattaché est
    rendu, le reste sera vu à la prochaine réorganisation."""
    import time
    fichiers = lister(dossier_source)
    index = index_par_fichier(inventaire)
    trouves, ignores = [], []
    total = len(fichiers)
    dernier = [0.0]

    def suivre(a, fait):
        x, info, raison = rattacher_analyse(a, index)
        if x is None:
            ignores.append((a['chemin'], raison))
        else:
            trouves.append((a['chemin'], x, info))
        if progression is not None and (time.monotonic() - dernier[0] >= 0.1 or fait == total):
            dernier[0] = time.monotonic()
            progression(fait, total)
    if total <= SEUIL_PROCESSUS or processus == 1:
        for k, f in enumerate(fichiers, 1):
            if arret is not None and arret.is_set():
                break
            suivre(analyser(f), k)
        return trouves, ignores
    import concurrent.futures as F
    import multiprocessing as mp
    n = processus or max(1, min(8, (os.cpu_count() or 2) - 1))
    pool = F.ProcessPoolExecutor(n, mp_context=mp.get_context('spawn'))
    # par paquets : peu d'échanges entre processus, et l'arrêt est vu entre deux paquets
    paquets = [fichiers[k:k + 32] for k in range(0, total, 32)]
    faits = set()
    fait = 0
    try:
        en_cours = {}
        suivant = 0
        while (suivant < len(paquets) or en_cours) and not (arret is not None and arret.is_set()):
            while suivant < len(paquets) and len(en_cours) < 2 * n:
                en_cours[pool.submit(_analyser_paquet, paquets[suivant])] = suivant
                suivant += 1
            finis, _ = F.wait(list(en_cours), timeout=0.2, return_when=F.FIRST_COMPLETED)
            for fut in finis:
                k = en_cours.pop(fut)
                for a in fut.result():
                    fait += 1
                    suivre(a, fait)
                faits.add(k)
    except Exception:                       # bassin cassé (processus tué, mémoire) : on finit ici, un par un
        for k, paquet in enumerate(paquets):
            if k in faits:
                continue
            for f in paquet:
                if arret is not None and arret.is_set():
                    break
                fait += 1
                suivre(analyser(f), fait)
    finally:
        pool.shutdown(wait=not (arret is not None and arret.is_set()), cancel_futures=True)
    trouves.sort(key=lambda t: t[0])
    ignores.sort(key=lambda t: t[0])
    return trouves, ignores


def _analyser_paquet(chemins):
    return [analyser(c) for c in chemins]


def nettoyer_dossiers_vides(dossier_source, racine, dossiers=None):
    """Retire les dossiers vidés par la réorganisation (hors la racine de sortie et `_traitement`).

    `dossiers` : ceux d'où des fichiers sont partis — seuls eux et leurs parents sont examinés (sans parcourir
    toute l'arborescence source, coûteux sur un partage) ; None = toute l'arborescence."""
    dossier_source = os.path.abspath(dossier_source)
    if dossiers is None:
        candidats = [d for d, _, _ in os.walk(dossier_source)]
    else:
        vus = set()
        for d in dossiers:
            d = os.path.abspath(d)
            while d.startswith(dossier_source + os.sep) and d not in vus:
                vus.add(d)
                d = os.path.dirname(d)
        candidats = list(vus)
    for d in sorted(candidats, key=lambda c: -len(c)):
        if d in (dossier_source, os.path.abspath(racine)) or '_traitement' in d.split(os.sep):
            continue
        try:
            reste = os.listdir(d)
            if reste and set(reste) <= {'LOT.txt', 'QUALITE.csv', 'QUALITE.txt'}:
                for f in reste:
                    os.remove(os.path.join(d, f))
                reste = []
            if not reste:
                os.rmdir(d)
        except OSError:
            pass
