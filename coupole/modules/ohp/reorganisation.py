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
    racine = ET.fromstring(xml)
    im = racine.find(xisf.NS + 'Image')
    if im is None:
        raise xisf.ErreurXISF('no image')
    mots = [(k.get('name'), k.get('value', ''), k.get('comment', '')) for k in im.findall(xisf.NS + 'FITSKeyword')]
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


def rattacher(chemin, inventaire) -> tuple[dict | None, dict | None, str]:
    """(ligne d'inventaire, info prête pour le rangement, raison d'échec) pour un fichier converti."""
    bas = chemin.lower()
    try:
        if bas.endswith('.xisf'):
            mots, props = lire_entete_xisf(chemin)
        elif bas.endswith(('.fits', '.fits.fz', '.fit')):
            mots, props = lire_entete_fits(chemin)
        else:
            return None, None, 'format'
    except Exception:
        return None, None, 'illisible'
    source = source_de(mots, props)
    if not source:
        return None, None, 'pas_coupole'
    ent = _entete(mots)
    candidats = [x for x in inventaire.images if x['access_url'].rsplit('/', 1)[-1] == source]
    if not candidats:
        return None, None, 'inconnu_inventaire'
    d_hdr = ent.gets('DATE-OBS')
    x = candidats[0]
    if len(candidats) > 1 and d_hdr:
        try:
            d = D.datetime.fromisoformat(d_hdr[:23])
            x = min(candidats, key=lambda y: abs((utc(y['t_min']) - d).total_seconds()))
        except ValueError:
            pass
    nx, ny = int(props.get('_nx') or ent.getf('NAXIS1') or x['s_xel1']), int(props.get('_ny') or ent.getf('NAXIS2') or x['s_xel2'])
    info = info_de_base(x)
    sol = wcs_de(ent, nx, ny) if nx and ny else None
    statut = props.get('OHP:Astrometry:Status') or ('validee' if sol else 'echec')
    if sol is not None:
        info.update(ra=sol['ra'], dec=sol['dec'], echelle=sol['echelle'], angle=sol['angle'], parite=sol['parite'])
    info['wcs'] = statut if statut in ('confirmee', 'validee', 'refaite', 'douteuse', 'echec') else 'echec'
    if sol is None and info['wcs'] in ('confirmee', 'validee', 'refaite'):
        info['wcs'] = 'echec'
    f_norm, f_sys, f_dos = FILTRES.get(x['filter_name'], (x['filter_name'], '', sur(x['filter_name'])))
    info.update(filtre=f_norm, filtre_sys=f_sys, filtre_dossier=f_dos, nx=nx, ny=ny,
                debut=(d_hdr or utc(x['t_min']).isoformat(timespec='milliseconds')),
                objet_affiche=ent.gets('OBJECT') or x['objet'], format='xisf' if bas.endswith('.xisf') else
                ('fz' if bas.endswith('.fz') else 'fits'), reorganise=True)
    try:
        info['octets_sortie'] = os.path.getsize(chemin)
    except OSError:
        pass
    return x, info, ''


def inventorier(dossier_source, inventaire, racine) -> tuple[list, list]:
    """Parcourt `dossier_source` : ([(chemin, x, info)], [(chemin, raison)]) ; `_traitement/` est ignoré."""
    trouves, ignores = [], []
    dossier_source = os.path.abspath(dossier_source)
    for d, sous, fs in os.walk(dossier_source):
        sous[:] = [s for s in sous if s != '_traitement']
        for f in sorted(fs):
            if not f.lower().endswith(EXTENSIONS) or f.lower().endswith('.tmp'):
                continue
            chemin = os.path.join(d, f)
            x, info, raison = rattacher(chemin, inventaire)
            if x is None:
                ignores.append((chemin, raison))
            else:
                trouves.append((chemin, x, info))
    return trouves, ignores


def nettoyer_dossiers_vides(dossier_source, racine):
    """Retire les dossiers vidés par la réorganisation (hors la racine de sortie et `_traitement`)."""
    dossier_source = os.path.abspath(dossier_source)
    for d, sous, fs in sorted(os.walk(dossier_source), key=lambda t: -len(t[0])):
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
