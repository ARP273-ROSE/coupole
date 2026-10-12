"""Noms lisibles et rangement par champ des fichiers d'archive ; réorganisation des téléchargements existants.

Nom d'un fichier préparé (0.2.2) : ``<cible>_<instrument>_<filtre>_<date>_<type>_<n>x<pose>s.xisf``, par exemple
``M16_ACS-WFC_F775W_2006-04-12_MVM_1x2000s.xisf`` ou ``Arp273_WFC3-UVIS_F390W_2010-12-17_MVM_8x1200s.xisf``.
L'identifiant de l'archive reste dans l'en-tête (``ARCHID``, ``ORIGFILE``) et dans la fiche.

Rangement « par champ », comme la Banque OHP : ``Archives/<champ>/`` contient les images préparées de toutes les
missions et de tous les filtres de ce champ ; ``_originaux/`` les fichiers d'origine (si on les garde) ;
``_variantes/`` les variantes et images de détection déplacées par la réorganisation.

La réorganisation ne copie ni n'écrase jamais : déplacement (``os.replace``) ; un nom déjà pris reçoit un suffixe
``_2``, ``_3``… ; chaque action est écrite dans ``_etat/JOURNAL.txt`` ; la base d'état suit les déplacements.
"""
from __future__ import annotations

import os
import re

from ..ohp.conversion import sur

TYPES = {'mvm': 'MVM', 'svm': 'SVM', 'pipeline': 'pipeline', 'pose': 'pose', 'detection': 'detection',
         'jwst_mosaique': 'i2d-mosaique', 'jwst_obs': 'i2d', 'galex': 'int', 'hlsp': 'HLSP'}
ORIGINAUX = '_originaux'
VARIANTES = '_variantes'


def jeton(s: str, defaut: str = 'x') -> str:
    """Morceau de nom : ASCII, lettres et chiffres, séparateurs ramenés à « - » (« WFC3/UVIS » → « WFC3-UVIS »)."""
    t = sur(str(s or '')).replace('_', '-').replace('.', '-')
    t = re.sub(r'-{2,}', '-', t).strip('-')
    return t or defaut


def nom_champ(o: dict, cible: str = '') -> str:
    """Dossier du champ : le nom cherché (« M 16 » → « M16 »), sinon la cible de l'archive, sinon les
    coordonnées.  Les espaces d'un numéro de catalogue sont retirés, les autres deviennent « - »."""
    n = cible or o.get('cible') or ''
    if n:
        n = re.sub(r'^([A-Za-z]+)\s+(\d)', r'\1\2', n.strip())
        return jeton(n, 'champ')
    if o.get('ra') is not None and o.get('dec') is not None:
        return 'RA%07.3f_DEC%+07.3f' % (o['ra'], o['dec'])
    return 'divers'


def instrument_court(instrument: str) -> str:
    i = (instrument or '').upper()
    for suffixe in ('/IMAGE', '/IMAGING'):
        if i.endswith(suffixe):
            i = i[:-len(suffixe)]
    return jeton(i, 'instrument')


def type_produit(o: dict) -> str:
    """« MVM », « SVM-v21 » (visite 21), « drz-v21 », « pose-v41 », « i2d »…"""
    p = o.get('produit') or ''
    if p in TYPES:
        t = TYPES[p]
        if p == 'pipeline':
            f = (o.get('fichier') or '').lower()
            t = 'drc' if '_drc' in f else ('drz' if '_drz' in f else 'pipeline')
        v = o.get('visite') or ''
        if p in ('svm', 'pipeline', 'pose', 'detection') and len(v) >= 6 and v[4:6].isalnum():
            t += '-v' + v[4:6]
        return t
    return {'pose': 'pose', 'mosaique': 'mosaique', 'combine': 'combine'}.get(o.get('nature') or '', 'produit')


def morceau_poses(poses, exposition) -> str:
    """« 8x650s » (n poses de t s), « 2000s » (total seul), '' si inconnu."""
    if exposition and poses and poses > 0:
        t = exposition / poses
        return '%dx%ss' % (poses, ('%d' % round(t)) if t >= 1 else ('%.2f' % t).rstrip('0').rstrip('.'))
    if exposition:
        return '%ds' % round(exposition) if exposition >= 1 else ('%.2fs' % exposition)
    return ''


def nom_lisible(o: dict, cible: str = '', entete=None) -> str:
    """Nom sans extension.  `entete` (après préparation) complète la date, le nombre de poses et le temps total."""
    h = entete if entete is not None else {}
    date = (o.get('debut') or '')[:10] or str(h.get('DATE-OBS', '') or '')[:10]
    poses = h.get('NPOSES') or o.get('poses')
    expo = None
    for k in ('TEXPTIME', 'XPOSURE', 'EFFEXPTM', 'EXPTIME'):
        v = h.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
            expo = float(v)
            break
    expo = expo or o.get('exposition')
    morceaux = [nom_champ(o, cible), instrument_court(o.get('instrument')), jeton(o.get('filtre'), 'sans-filtre')]
    if date:
        morceaux.append(date)
    morceaux.append(type_produit(o))
    p = morceau_poses(poses, expo)
    if p:
        morceaux.append(p)
    return '_'.join(morceaux)[:150]


def libre(chemin_sans_ext: str, extension: str, appartient=None) -> str:
    """Premier nom libre : ``nom.ext``, sinon ``nom_2.ext``… ; `appartient(chemin)` → True si le fichier existant
    est déjà le nôtre (on peut le remplacer)."""
    k = 1
    while True:
        c = chemin_sans_ext + ('' if k == 1 else '_%d' % k)
        if not os.path.exists(c + extension) or (appartient is not None and appartient(c + extension)):
            return c
        k += 1


# ================================================================================================ réorganisation
def _info_entete(chemin: str) -> dict:
    """Cartes FITS utiles d'une image préparée (XISF ou FITS), sans lire les pixels."""
    from ..ohp.reorganisation import lire_entete_fits, lire_entete_xisf
    from .extraction import valeur_fits
    try:
        if chemin.lower().endswith('.xisf'):
            mots, _ = lire_entete_xisf(chemin)
            return {k: valeur_fits(v) for k, v, _c in mots if k not in ('HISTORY', 'COMMENT')}
        mots, _ = lire_entete_fits(chemin)
        return {k: v for k, v, _c in mots}
    except Exception:
        return {}


def plan(sortie, possession: dict | None = None, variantes_a_part: bool = True) -> list[dict]:
    """Actions de réorganisation (rien n'est modifié ici) : [{'id', 'de', 'vers', 'masque', 'variante', 'raison'}].
    Chemins relatifs au dossier ``Archives``."""
    from . import produits
    from .services.base import observation
    from .telechargement import dossier_archives, possession as lire_possession
    racine = dossier_archives(sortie)
    p = possession if possession is not None else lire_possession(sortie)
    obs = []
    for ident, d in p.items():
        if d.get('statut') != 'ok' or not d.get('prepare'):
            continue
        h = _info_entete(os.path.join(racine, d['prepare']))
        o = observation(id=ident, archive=d.get('archive') or ident.split(':', 1)[0], mission=d.get('mission', ''),
                        instrument=d.get('instrument', ''), filtre=d.get('filtre', ''), debut=d.get('debut', ''),
                        cible=d.get('cible', ''), obs_id=ident.split(':', 1)[-1],
                        fichier=os.path.basename(d.get('fichier') or str(h.get('ORIGFILE', ''))),
                        exposition=h.get('TEXPTIME') or h.get('EXPTIME'), poses=h.get('NPOSES') or h.get('NUMEXP')
                        or h.get('NCOMBINE'), provenance='')
        o['_info'], o['_entete'] = d, h
        obs.append(o)
    produits.regrouper(obs)
    actions = []
    pris = set()
    for o in obs:
        d, h = o['_info'], o['_entete']
        champ = nom_champ(o, d.get('cible', ''))
        sous = VARIANTES if (variantes_a_part and o['variante']) else ''
        ext = os.path.splitext(d['prepare'])[1]
        base = os.path.join(champ, sous, nom_lisible(o, d.get('cible', ''), h)) if sous else \
            os.path.join(champ, nom_lisible(o, d.get('cible', ''), h))
        autres = list(d.get('autres') or [])
        for k, rel in enumerate([d['prepare']] + autres):
            b = base + ('_d%d' % (k + 1) if autres else '')
            n = 1
            cand = b
            while cand + ext in pris or (os.path.exists(os.path.join(racine, cand + ext))
                                         and os.path.normcase(cand + ext) != os.path.normcase(rel)):
                n += 1
                cand = '%s_%d' % (b, n)
            pris.add(cand + ext)
            actions.append({'id': o['id'], 'de': rel, 'vers': cand + ext, 'masque': d.get('masque', '') if k == 0 else '',
                            'variante': o['variante'], 'raison': o['raison'], 'original': d.get('fichier', '') if k == 0 else '',
                            'champ': champ})
    return actions


def reorganiser(sortie, recadrer: bool = True, garder_masques: bool = False, simuler: bool = False,
                progression=None) -> dict:
    """Applique `plan()` : renomme et range par champ, recadre les images sur leur zone utile (`recadrer`),
    supprime les masques pleine taille de 0.2.0/0.2.1 (ou les récrit compressés si `garder_masques`), range les
    variantes et images de détection dans ``_variantes/``.  Rend {'deplaces', 'recadres', 'masques',
    'octets_avant', 'octets_apres', 'actions', 'erreurs'}."""
    from ..ohp.pilote import Etat, Journal
    from .telechargement import dossier_archives
    racine = dossier_archives(sortie)
    actions = plan(sortie)
    bilan = {'deplaces': 0, 'recadres': 0, 'masques': 0, 'octets_avant': 0, 'octets_apres': 0, 'actions': actions,
             'erreurs': []}
    if simuler:
        for a in actions:
            for rel in (a['de'], a['masque']):
                if rel and os.path.exists(os.path.join(racine, rel)):
                    bilan['octets_avant'] += os.path.getsize(os.path.join(racine, rel))
        return bilan
    trav = os.path.join(racine, '_etat')
    journal = Journal(trav, 0.0)
    etat = Etat(os.path.join(trav, 'etat.sqlite'), 0.0)
    journal.ecrire('arc_j_reorg_debut', n=len(actions))
    try:
        for k, a in enumerate(actions):
            try:
                _appliquer(racine, a, recadrer, garder_masques, bilan, journal, etat)
            except Exception as e:                      # un fichier abîmé n'arrête pas les autres
                bilan['erreurs'].append('%s: %s' % (a['de'], e))
                journal.ecrire('arc_j_reorg_erreur', chemin=a['de'], raison='%s: %s' % (type(e).__name__, e))
            if progression:
                progression(k + 1, len(actions))
        _nettoyer_dossiers_vides(racine)
    finally:
        etat.fermer()
        journal.ecrire('arc_j_reorg_fin', deplaces=bilan['deplaces'], recadres=bilan['recadres'],
                       masques=bilan['masques'], avant='%.1f' % (bilan['octets_avant'] / 1e6),
                       apres='%.1f' % (bilan['octets_apres'] / 1e6))
        journal.vider()
    return bilan


def _appliquer(racine, a, recadrer, garder_masques, bilan, journal, etat):
    from .extraction import recadrer_prepare
    src = os.path.join(racine, a['de'])
    if not os.path.exists(src):
        return
    masque = os.path.join(racine, a['masque']) if a['masque'] else ''
    avant = os.path.getsize(src) + (os.path.getsize(masque) if masque and os.path.exists(masque) else 0)
    bilan['octets_avant'] += avant
    dst = os.path.join(racine, a['vers'])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.normcase(os.path.abspath(src)) != os.path.normcase(os.path.abspath(dst)):
        if os.path.exists(dst):
            raise FileExistsError(dst)                 # jamais d'écrasement (le plan a déjà choisi un nom libre)
        os.replace(src, dst)
        bilan['deplaces'] += 1
        journal.ecrire('arc_j_deplace', de=a['de'], vers=a['vers'])
    nouveau_masque = ''
    if recadrer or (masque and os.path.exists(masque)):
        r = recadrer_prepare(dst, masque if masque and os.path.exists(masque) else '', garder_masques)
        if r['recadre']:
            bilan['recadres'] += 1
            journal.ecrire('arc_j_recadre', chemin=a['vers'], avant='%d×%d' % tuple(r['avant'][::-1]),
                           apres='%d×%d' % tuple(r['apres'][::-1]))
        nouveau_masque = r['masque']
    if masque and os.path.exists(masque) and os.path.abspath(masque) != os.path.abspath(nouveau_masque or ''):
        os.remove(masque)
        bilan['masques'] += 1
        journal.ecrire('arc_j_masque_supprime', chemin=a['masque'])
    if a.get('original'):
        o_src = os.path.join(racine, a['original'])
        if os.path.exists(o_src):
            o_dst = os.path.join(racine, a['champ'], ORIGINAUX, os.path.basename(o_src))
            if os.path.abspath(o_src) != os.path.abspath(o_dst) and not os.path.exists(o_dst):
                os.makedirs(os.path.dirname(o_dst), exist_ok=True)
                os.replace(o_src, o_dst)
                journal.ecrire('arc_j_deplace', de=a['original'], vers=os.path.relpath(o_dst, racine))
                a['original'] = os.path.relpath(o_dst, racine)
    bilan['octets_apres'] += os.path.getsize(dst) + (os.path.getsize(nouveau_masque) if nouveau_masque else 0)
    statut, _essais, info = etat.lire(a['id'])
    with etat.verrou:
        r = etat.db.execute('SELECT url FROM images WHERE id=?', (a['id'],)).fetchone()
    url = r[0] if r else ''
    if statut:
        from .telechargement import chemin_relatif
        autres = [chemin_relatif(x) for x in (info.get('autres') or [])]
        if a['de'] == chemin_relatif(info.get('prepare') or ''):
            info['prepare'] = a['vers']
            info['masque'] = os.path.relpath(nouveau_masque, racine) if nouveau_masque else ''
            if a.get('original'):
                info['fichier'] = a['original']
        elif a['de'] in autres:
            autres[autres.index(a['de'])] = a['vers']
            info['autres'] = autres
        info['variante'] = a['variante']
        info['octets_prepare'] = os.path.getsize(dst)
        etat.ecrire(a['id'], url or '', statut, info)
        etat.valider_si_du()


def _nettoyer_dossiers_vides(racine):
    for d, sous, fichiers in sorted(os.walk(racine), key=lambda x: -len(x[0])):
        if d == racine or os.path.basename(d) == '_etat' or '_etat' in d.split(os.sep):
            continue
        try:
            if not os.listdir(d):
                os.rmdir(d)
        except OSError:
            pass
