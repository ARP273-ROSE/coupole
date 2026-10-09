"""Où se trouve, dans le dossier de sortie COURANT, le fichier converti d'une image possédée.

La base d'état note l'emplacement absolu (`info['final']`) sur la machine qui a traité : une copie faite par
`ohp_xisf.py` dans un conteneur porte « /srv/ancien/OHP_DU_ECU/… », introuvable sur le poste qui la lit
par « /mnt/partage/OHP_DU_ECU ».  Depuis 0.1.11, Coupole note aussi `info['chemin']`, relatif au dossier
de sortie, et retrouve celui des copies plus anciennes, dans cet ordre :

1. ``info['chemin']`` (relatif) ; ou ``info['final']`` s'il est dans le dossier de sortie courant ;
2. ``_traitement/journal.csv`` du dossier de sortie (colonne ``destination``, relative), par adresse (``url``) puis
   par fichier d'origine (``fichier_source``) — lu une fois, gardé en cache, relu si le fichier change ;
3. ``info['final']`` d'une autre machine rapporté au dossier de sortie à partir du dossier de type
   (« …/OHP_DU_ECU/07_Nebuleuses/… » → « 07_Nebuleuses/… ») ;
4. (à la demande, `chercher_par_nom`) le nom de fichier attendu dans le dossier du lot calculé comme au rangement.

Le chemin rendu est toujours relatif au dossier de sortie (jamais le chemin absolu d'une autre machine).
`migrer` écrit dans la base les chemins trouvés par le journal, par la base de travail locale si le dossier est
sur un partage (core/base_partagee) ; un échec n'empêche rien : la résolution par le journal continue de servir.
"""
from __future__ import annotations

import csv
import json
import os
import threading

_verrou = threading.Lock()
_cache: dict[str, tuple] = {}                 # chemin du journal → ((mtime_ns, taille), index)


# ============================================================================ chemins relatifs
def relatif_valide(rel) -> str:
    """`rel` normalisé avec « / » s'il est relatif et reste dans le dossier de sortie, sinon ''."""
    if not rel or not isinstance(rel, str):
        return ''
    r = rel.replace('\\', '/').strip()
    if not r or r.startswith('/') or (len(r) > 1 and r[1] == ':'):
        return ''
    parties = [p for p in r.split('/') if p not in ('', '.')]
    if not parties or '..' in parties:
        return ''
    return '/'.join(parties)


def dans_sortie(chemin, dest) -> str:
    """Chemin relatif (« / ») d'un chemin absolu situé dans `dest`, sinon ''."""
    if not chemin or not dest or not os.path.isabs(str(chemin)):
        return ''
    try:
        rel = os.path.relpath(os.path.abspath(str(chemin)), os.path.abspath(str(dest)))
    except ValueError:                           # autre lecteur sous Windows
        return ''
    return relatif_valide(rel)


def absolu(dest, rel) -> str:
    """Chemin local d'un chemin relatif (« / ») dans `dest`."""
    return os.path.join(str(dest), *rel.split('/')) if rel else ''


def _dossiers_type() -> set:
    from .cibles import CATEGORIES
    from .lots import SANS
    out = set(SANS.values())
    for fr, en, _ in CATEGORIES.values():
        out.update((fr, en))
    return out


def rebaser(final, staging='') -> str:
    """Chemin d'une autre machine rapporté au dossier de sortie, ou '' : d'après l'ancienne racine (le dossier
    qui contenait « _traitement » dans `staging`), sinon à partir du dossier de type (« 07_Nebuleuses »,
    « _sans_solution_astrometrique »…)."""
    if not final or not isinstance(final, str):
        return ''
    parties = [p for p in final.replace('\\', '/').split('/') if p]
    st = [p for p in (staging or '').replace('\\', '/').split('/') if p] if isinstance(staging, str) else []
    if '_traitement' in st:
        racine = st[:st.index('_traitement')]
        if racine and parties[:len(racine)] == racine and len(parties) > len(racine):
            return relatif_valide('/'.join(parties[len(racine):]))
    types = _dossiers_type()
    # le DERNIER dossier de type qui laisse au moins objet/lot/filtre/fichier (un parent nommé comme un type ne
    # trompe pas)
    for k in range(len(parties) - 1, -1, -1):
        if parties[k] in types and len(parties) - k >= 3:
            return relatif_valide('/'.join(parties[k:]))
    return ''


# ============================================================================ journal.csv
def chemin_journal(dest) -> str:
    return os.path.join(str(dest), '_traitement', 'journal.csv')


def _stat(p):
    try:
        s = os.stat(p)
        return (s.st_mtime_ns, s.st_size)
    except OSError:
        return None


def lire_journal(dest) -> dict:
    """{'url': {adresse: rel}, 'source': {fichier d'origine: rel}} d'après ``_traitement/journal.csv`` (séparateur
    « ; », BOM UTF-8), en cache tant que le fichier ne change pas ; {} vides sans journal.  Jamais d'exception."""
    vide = {'url': {}, 'source': {}}
    if not dest:
        return vide
    p = chemin_journal(dest)
    st = _stat(p)
    if st is None:
        return vide
    with _verrou:
        c = _cache.get(p)
        if c is not None and c[0] == st:
            return c[1]
    index = {'url': {}, 'source': {}}
    try:
        with open(p, encoding='utf-8-sig', newline='') as f:
            r = csv.reader(f, delimiter=';')
            tete = next(r, None) or []
            noms = [t.strip().split(' (')[0] for t in tete]
            try:
                i_dest = noms.index('destination')
            except ValueError:
                i_dest = 1
            i_src = noms.index('fichier_source') if 'fichier_source' in noms else 0
            i_url = noms.index('url') if 'url' in noms else len(noms) - 1
            sources_vues = {}
            for ligne in r:
                if len(ligne) <= max(i_dest, i_src):
                    continue
                src = ligne[i_src].strip()
                if src:                                  # toutes les lignes (doublons compris) pour l'ambiguïté
                    sources_vues[src] = sources_vues.get(src, 0) + 1
                rel = relatif_valide(ligne[i_dest])
                if not rel:
                    continue
                if 0 <= i_url < len(ligne) and ligne[i_url]:
                    index['url'][ligne[i_url].strip()] = rel
                if src:
                    index['source'][src] = rel
            for src, n in sources_vues.items():     # un nom d'origine porté par plusieurs images : ambigu
                if n > 1:
                    index['source'].pop(src, None)
    except (OSError, UnicodeError, csv.Error):
        index = vide
    with _verrou:
        _cache[p] = (st, index)
    return index


def oublier_cache():
    with _verrou:
        _cache.clear()


# ============================================================================ résolution
def resoudre(dest, info: dict, journal: dict | None = None) -> tuple[str, str]:
    """(chemin relatif, origine) d'une image convertie ; origine ∈ 'base', 'journal', 'rebase' ; ('', '') si rien.

    `journal` : index déjà lu (sinon lu ici au besoin)."""
    info = info or {}
    rel = relatif_valide(info.get('chemin'))
    if rel:
        return rel, 'base'
    final = info.get('final') or ''
    rel = dans_sortie(final, dest) if final and os.path.isabs(final) else relatif_valide(final)
    if rel:
        return rel, 'base'
    if journal is None:
        journal = lire_journal(dest)
    url = (info.get('url') or '').strip()
    if url and url in journal.get('url', {}):
        return journal['url'][url], 'journal'
    src = (info.get('source') or '').strip()
    if src and src in journal.get('source', {}):
        return journal['source'][src], 'journal'
    rel = rebaser(final, info.get('staging') or '')
    if rel:
        return rel, 'rebase'
    return '', ''


def chercher_par_nom(dest, info: dict, infos_objet) -> str:
    """Le fichier attendu (nom du rangement) dans le dossier de son lot (calcul de lot du rangement, en français
    puis en anglais), ou ''.  `infos_objet` : [(id, info)] des images converties du même objet (le découpage en
    champs dépend des autres poses) ; les infos portent leur identifiant en `_id`.  Les noms pris deux fois
    (« <nom>_2.xisf ») sont numérotés dans l'ordre du rangement.  Un `listdir` par dossier essayé."""
    from . import lots
    if not dest or not info:
        return ''
    ident = info.get('_id')
    infos_objet = list(infos_objet)
    for L in ('fr', 'en'):
        try:
            plan = lots.plan_des_lots(infos_objet, L)
        except Exception:                        # info incomplète (copie ancienne) : pas de calcul de lot
            continue
        cle = next((c for c, items in plan.items() if any(i == ident for i, _ in items)), None)
        if cle is None:
            continue
        try:
            noms = set(os.listdir(os.path.join(str(dest), *cle)))
        except OSError:
            continue
        attendu, pris = '', set()
        try:
            for i, inf in sorted(plan[cle], key=lambda it: (it[1].get('mjd') or 0, it[0])):
                ext = inf.get('extension') or '.xisf'
                base = lots.nom_fichier(inf, L)
                nom, n = base + ext, 1
                while nom.lower() in pris:
                    n += 1
                    nom = '%s_%d%s' % (base, n, ext)
                pris.add(nom.lower())
                if i == ident:
                    attendu = nom
                    break
        except Exception:
            continue
        if attendu in noms:
            return relatif_valide('/'.join(cle + (attendu,)))
        for e in ('.xisf', '.fits', '.fits.fz'):  # autre format que celui supposé
            racine = attendu.rsplit('.xisf', 1)[0] if attendu.endswith('.xisf') else attendu
            if racine + e in noms:
                return relatif_valide('/'.join(cle + (racine + e,)))
    return ''


def dossier_attendu(dest, cat: str, objet: str) -> str:
    """« <sortie>/<type>/<objet> » selon le nommage du rangement (français puis anglais) s'il existe, sinon ''."""
    from .cibles import dossier_categorie, nom_affiche
    from .conversion import sur
    if not dest or not objet:
        return ''
    for L in ('fr', 'en'):
        d = os.path.join(str(dest), dossier_categorie(cat or 'autre', L), sur(nom_affiche(objet, L)))
        if os.path.isdir(d):
            return d
    return ''


# ============================================================================ migration
def migrer(dest, paires, rapporter=None) -> int:
    """Écrit `info['chemin']` (relatif) dans la base d'état pour [(id, rel)] ; une transaction, base de travail
    locale recopiée si le dossier est sur un partage.  Rend le nombre d'images mises à jour ; 0 (sans lever) si
    la base n'est pas inscriptible, verrouillée ou en divergence."""
    import sqlite3
    from ...core import base_partagee
    paires = [(i, r) for i, r in paires if relatif_valide(r)]
    chemin = os.path.join(str(dest), '_traitement', 'etat.sqlite')
    if not paires or not os.path.isfile(chemin):
        return 0
    try:
        base = base_partagee.BasePartagee(chemin, rapporter=rapporter)
        db = sqlite3.connect(base.ouvrir(), timeout=5)
        try:
            # base d'ohp_xisf.py en WAL : écritures dans le -wal, base principale inchangée → la recopie vers
            # le partage ne voyait rien de neuf ; et un -wal ne passe pas un partage SMB
            db.execute('PRAGMA journal_mode=DELETE')
            voulu = dict(paires)
            maj = []
            ids = list(voulu)
            for k in range(0, len(ids), 500):
                bloc = ids[k:k + 500]
                for i, info in db.execute('SELECT id, info FROM images WHERE statut=\'ok\' AND id IN (%s)'
                                          % ','.join('?' * len(bloc)), bloc):
                    try:
                        d = json.loads(info or '{}')
                    except ValueError:
                        continue
                    if relatif_valide(d.get('chemin')) == voulu[i]:
                        continue
                    d['chemin'] = voulu[i]
                    maj.append((json.dumps(d, ensure_ascii=False, default=str), i))
            if maj:
                db.executemany('UPDATE images SET info=? WHERE id=?', maj)
                db.commit()
            base.fermer(db)
        finally:
            db.close()
    except (sqlite3.Error, OSError, base_partagee.Divergence):
        return 0
    return len(maj)


def migrer_dossier(dest) -> dict:
    """Pour `coupole ohp metadonnees --reecrire` : chemins de toutes les images converties résolus (base, journal,
    dossier de type) puis écrits.  Rend {'resolues', 'migrees', 'introuvables'}."""
    from .possession import Possession
    poss, _ = Possession.lire_avec_infos(dest)
    paires = poss.a_migrer
    n = migrer(dest, paires) if paires else 0
    sans = sum(1 for i, s in poss.statuts.items() if s == 'ok' and not poss.details.get(i, {}).get('chemin'))
    return {'resolues': sum(1 for s in poss.statuts.values() if s == 'ok') - sans, 'migrees': n, 'introuvables': sans}
