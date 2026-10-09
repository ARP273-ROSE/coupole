"""Rapport d'anomalies : ce qui est écarté ou signalé, et pourquoi.  Rien n'est supprimé en silence.

Niveaux de détection (rejoués à chaque rafraîchissement de l'inventaire) :
  meme_fichier      même pose sous deux chemins ou orthographes (date, filtre, pose, taille, nom à la
                    ponctuation près)                                         → écartée (doublon)
  copie_diurne      copie datée en plein jour d'une image bien datée (dossiers t120/, t152/)
                                                                              → écartée (doublon)
  memes_meta        mêmes date, filtre, pose et taille mais nom de fichier différent
                                                                              → signalée seulement
  date_partagee     DATE-OBS identique à celle d'une autre pose (pixels différents)
                                                                              → signalée, DATEDOUT = T
  date_diurne       pose datée entre 5 h et 17 h UTC                          → signalée
  champ_incoherent  centre du champ loin des autres poses de l'objet          → signalée
  classement        nom non classé, ou classé automatiquement (à vérifier)    → signalée
  instrument        instrument inconnu de la table                            → signalée
  pixels_identiques même empreinte SHA-1 des pixels qu'une autre image (au traitement)
                                                                              → écartée (doublon), sauf
                                                                                « garder les doublons »
L'option « garder les doublons » traite aussi ce qui est écarté : tout est réversible.
"""
from __future__ import annotations

import collections as C
import csv
import json
import os

from ...core.astro import sep_deg
from ...core.i18n import tr
from .astrometrie import DIST_FIXE, DIST_MOBILE, cle_groupe
from .cibles import FIXES
from .inventaire import INSTRUMENTS

ECARTEES = {'meme_fichier', 'copie_diurne', 'pixels_identiques'}


def detecter(images, medo=None) -> list[dict]:
    """Une ligne par (image, anomalie)."""
    out = []

    def ajouter(x, genre, detail=''):
        out.append({'url': x['access_url'], 'fichier': x['access_url'].rsplit('/', 1)[1], 'objet': x['objet'],
                    'nom_base': x['target_name'], 'nuit': str(x['nuit']), 'genre': genre,
                    'action': 'ecartee' if genre in ECARTEES else 'signalee', 'detail': detail,
                    'nouveau': x.get('nouveau', False)})
    meta = C.Counter((x['t_min'], x['filter_name'], x['t_exptime'], x['access_estsize']) for x in images
                     if not x['doublon'])
    for x in images:
        if x['doublon']:
            ajouter(x, x.get('raison_doublon') or 'meme_fichier')
            continue
        if meta[(x['t_min'], x['filter_name'], x['t_exptime'], x['access_estsize'])] > 1 and not x['date_partagee']:
            ajouter(x, 'memes_meta')
        if x['date_partagee']:
            ajouter(x, 'date_partagee')
        if x['diurne']:
            ajouter(x, 'date_diurne')
        if x.get('a_verifier'):
            ajouter(x, 'classement', x.get('classement', ''))
        if x['instrument_name'] not in INSTRUMENTS:
            ajouter(x, 'instrument', x['instrument_name'])
        if medo is not None:
            k = cle_groupe(x)
            if k in medo and medo[k][2] > 1:
                d = sep_deg(x['s_ra'], x['s_dec'], medo[k][0], medo[k][1])
                if d > (DIST_FIXE if x['cat'] in FIXES else DIST_MOBILE):
                    ajouter(x, 'champ_incoherent', '%.2f deg' % d)
    return out


def depuis_traitement(chemin_etat) -> list[dict]:
    """Doublons de pixels trouvés au traitement (base d'état d'un dossier de destination)."""
    if not os.path.exists(chemin_etat):
        return []
    import sqlite3
    from ...core.chemins import uri_sqlite_lecture_seule
    try:                                       # lecture seule (ne gêne pas un traitement qui écrit) ; jamais d'exception
        db = sqlite3.connect(uri_sqlite_lecture_seule(chemin_etat), uri=True, timeout=5)
        try:
            rows = db.execute("SELECT url, info FROM images WHERE statut='doublon'").fetchall()
        finally:
            db.close()
    except sqlite3.Error:
        return []
    out = []
    for url, info in rows:
        x = json.loads(info) if info else {}
        de = x.get('doublon_de', '')
        if de and de != 'inventaire':
            out.append({'url': url, 'fichier': url.rsplit('/', 1)[1], 'objet': x.get('objet', ''),
                        'nom_base': x.get('nom_base', ''), 'nuit': x.get('nuit', ''), 'genre': 'pixels_identiques',
                        'action': 'ecartee', 'detail': de, 'nouveau': False})
    return out


def resume(anoms) -> dict:
    c = C.Counter(a['genre'] for a in anoms)
    return dict(sorted(c.items()))


def ecrire_csv(chemin, anoms):
    with open(chemin, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['%s (%s)' % (tr('anom_col_' + c, 'fr'), tr('anom_col_' + c, 'en'))
                    for c in ('genre', 'action', 'objet', 'nuit', 'fichier', 'detail', 'explication', 'url')])
        for a in anoms:
            w.writerow([a['genre'], tr('anom_action_' + a['action'], 'fr') + ' / ' + tr('anom_action_' + a['action'], 'en'),
                        a['objet'], a['nuit'], a['fichier'], a['detail'],
                        tr('anom_' + a['genre'], 'fr') + ' / ' + tr('anom_' + a['genre'], 'en'), a['url']])
