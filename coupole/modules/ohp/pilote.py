"""Pilote du traitement : téléchargements (fils), conversions (processus), état, rangement.

* État dans ``<destination>/_traitement/etat.sqlite`` (journal DELETE, jamais
  WAL : la destination peut être un partage réseau) : un traitement interrompu
  (coupure, annulation, plantage) reprend là où il s'était arrêté ; une image
  convertie n'est jamais refaite.
* Mémoire bornée : une image par processus de conversion, et pas plus de
  ``2 x conversions + téléchargements`` FITS en attente sur le disque.
* L'interface reçoit des événements (dictionnaires) par ``rapporter`` ; elle
  ne bloque jamais : ce pilote tourne dans un fil à part.
"""
from __future__ import annotations

import concurrent.futures as F
import datetime as D
import json
import multiprocessing as mp
import os
import shutil
import sqlite3
import threading
import time
import traceback

from ... import __version__
from ...core import reseau
from ...core.parallele import Plan
from . import formats, lots
from .astrometrie import attentes, attentes_pour
from .conversion import convertir, ident, info_de_base

VERSION_MODULE = '1.0.0'


class Etat:
    """Base SQLite d'état (même schéma que le traitement de référence)."""

    def __init__(self, chemin):
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        self.db = sqlite3.connect(chemin, check_same_thread=False, timeout=60)
        self.db.execute('PRAGMA journal_mode=DELETE')
        self.db.execute('CREATE TABLE IF NOT EXISTS images (id TEXT PRIMARY KEY, url TEXT, statut TEXT, '
                        'essais INTEGER DEFAULT 0, info TEXT, maj TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS empreintes (sha TEXT PRIMARY KEY, id TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT)')
        self.db.commit()
        self.verrou = threading.Lock()

    def lire(self, i):
        with self.verrou:
            r = self.db.execute('SELECT statut, essais, info FROM images WHERE id=?', (i,)).fetchone()
        return (r[0], r[1], json.loads(r[2]) if r[2] else {}) if r else (None, 0, {})

    def ecrire(self, i, url, statut, info, essais=None):
        with self.verrou:
            if essais is None:
                essais = (self.db.execute('SELECT essais FROM images WHERE id=?', (i,)).fetchone() or [0])[0]
            self.db.execute('INSERT OR REPLACE INTO images VALUES (?,?,?,?,?,?)',
                            (i, url, statut, essais, json.dumps(info, ensure_ascii=False, default=str),
                             D.datetime.now().isoformat(timespec='seconds')))
            self.db.commit()

    def empreinte(self, sha, i):
        """Renvoie l'id déjà associé à ces pixels, ou None (et enregistre `i`)."""
        with self.verrou:
            r = self.db.execute('SELECT id FROM empreintes WHERE sha=?', (sha,)).fetchone()
            if r is None:
                self.db.execute('INSERT INTO empreintes VALUES (?,?)', (sha, i))
                self.db.commit()
                return None
            return r[0] if r[0] != i else None

    def meta(self, cle, valeur=None):
        with self.verrou:
            if valeur is not None:
                self.db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (cle, valeur))
                self.db.commit()
                return valeur
            r = self.db.execute('SELECT valeur FROM meta WHERE cle=?', (cle,)).fetchone()
            return r[0] if r else None

    def toutes(self):
        with self.verrou:
            return self.db.execute('SELECT id, url, statut, info FROM images ORDER BY id').fetchall()

    def ok(self):
        with self.verrou:
            rows = self.db.execute("SELECT id, info FROM images WHERE statut='ok'").fetchall()
        return [(i, json.loads(s)) for i, s in rows]

    def bilan(self):
        import collections as C
        with self.verrou:
            st = C.Counter(r[0] for r in self.db.execute('SELECT statut FROM images'))
            infos = [json.loads(s) for (s,) in self.db.execute("SELECT info FROM images WHERE statut='ok'")]
        w = C.Counter(x.get('wcs') for x in infos)
        of = sum(x.get('octets_fits', 0) for x in infos)
        ox = sum(x.get('octets_sortie', x.get('octets_xisf', 0)) for x in infos)
        return {'statuts': dict(st), 'wcs': dict(w), 'octets_fits': of, 'octets_sortie': ox}

    def fermer(self):
        with self.verrou:
            self.db.close()


class Traitement:
    """Télécharge, convertit et range une sélection d'images.

    options : format, langue (noms et en-têtes), astap (EtatASTAP ou None), mode_astap,
              debit_octets_s, garder_fits (bool).
    """

    def __init__(self, racine, inventaire, plan: Plan, options: dict, rapporter=None, arret=None):
        self.racine = os.path.abspath(racine)
        self.trav = os.path.join(self.racine, '_traitement')
        self.dl = os.path.join(self.trav, 'telechargements')
        self.staging = os.path.join(self.trav, 'converties')
        for d in (self.trav, self.dl, self.staging):
            os.makedirs(d, exist_ok=True)
        self.inventaire = inventaire
        self.plan = plan
        self.options = dict(options)
        self.options.setdefault('format', 'xisf')
        self.options.setdefault('langue', 'fr')
        self.options.setdefault('mode_astap', 'tous')
        self.options['createur'] = 'Coupole %s (ohp %s)' % (__version__, VERSION_MODULE)
        self.rapporter = rapporter or (lambda ev: None)
        self.arret = arret or threading.Event()
        self.etat = Etat(os.path.join(self.trav, 'etat.sqlite'))
        self._verifier_coherence()
        self.limiteur = reseau.LimiteurDebit(self.options.get('debit_octets_s', 8e6))
        self._med = self._medo = None

    def _verifier_coherence(self):
        """Une destination garde la même langue de noms et le même format (sinon deux arborescences)."""
        for cle in ('langue', 'format'):
            v = self.etat.meta(cle)
            if v is None:
                self.etat.meta(cle, self.options[cle])
            elif v != self.options[cle]:
                self.options[cle] = v
                self.rapporter({'type': 'avis', 'cle': 'ohp_avis_' + cle + '_impose', 'valeur': v})

    def attentes(self):
        if self._med is None:
            self._med, self._medo = attentes(self.inventaire.images)
        return self._med, self._medo

    # ---------------------------------------------------------------- étapes
    def _telecharger(self, x):
        i = ident(x)
        fic = os.path.join(self.dl, i + '.fits')

        def verifier(part):
            t = os.path.getsize(part)
            if t % 2880:
                raise IOError('size %d not a multiple of 2880: truncated FITS' % t)
            with open(part, 'rb') as f:
                if not f.read(30).startswith(b'SIMPLE  ='):
                    raise IOError('does not start with SIMPLE: not a FITS file')

        def prog(n):
            self.rapporter({'type': 'octets', 'n': n})
        t0 = time.time()
        from ...core import sources
        etat, recu = reseau.telecharger(sources.reecrire_url(x['access_url']), fic, taille_attendue=int(x['access_estsize'] * 1024),
                                        limiteur=self.limiteur, arret=self.arret, progression=prog,
                                        verifier=verifier)
        return fic, round(time.time() - t0, 1), recu

    def _sortie_staging(self, x):
        return os.path.join(self.staging, ident(x) + formats.EXTENSIONS[self.options['format']])

    # ---------------------------------------------------------------- principal
    def lancer(self, selection: list[dict]) -> dict:
        """Traite `selection` (lignes enrichies de l'inventaire, doublons compris)."""
        med, medo = self.attentes()
        garder = bool(self.options.get('garder_doublons'))
        for x in selection:
            if x['doublon'] and not garder:
                i = ident(x)
                if self.etat.lire(i)[0] is None:
                    self.etat.ecrire(i, x['access_url'], 'doublon',
                                     dict(info_de_base(x), doublon_de='inventaire'), 0)
        xs = sorted([x for x in selection if garder or not x['doublon']], key=lambda x: (x['t_min'], x['access_url']))
        a_faire = []
        for x in xs:
            st, essais, _ = self.etat.lire(ident(x))
            if st not in ('ok', 'doublon') and essais < 5:
                a_faire.append(x)
        total = len(a_faire)
        self.rapporter({'type': 'debut', 'total': total, 'deja': len(xs) - total,
                        'octets': sum(x['access_estsize'] * 1024 for x in a_faire),
                        'plan': {'telechargements': self.plan.telechargements, 'conversions': self.plan.conversions}})
        compte = {'ok': 0, 'doublon': 0, 'echec': 0}
        fenetre = 2 * self.plan.conversions + self.plan.telechargements
        ctx = mp.get_context('spawn')
        options_proc = dict(self.options)
        astap = options_proc.get('astap')
        if astap is not None and not isinstance(astap, dict):
            options_proc['astap'] = {k: getattr(astap, k) for k in ('executable', 'version', 'est_cli',
                                                                     'catalogue_dossier', 'catalogue',
                                                                     'catalogue_fichiers', 'catalogue_complet')}
        file_ = list(a_faire)
        en_dl: dict = {}
        en_conv: dict = {}
        prets: list = []
        pool_dl = F.ThreadPoolExecutor(max(1, self.plan.telechargements), thread_name_prefix='dl')
        pool_cv = F.ProcessPoolExecutor(max(1, self.plan.conversions), mp_context=ctx)
        t0 = time.time()
        try:
            while (file_ or en_dl or en_conv or prets) and not self.arret.is_set():
                # alimenter les téléchargements sans dépasser la fenêtre disque
                while file_ and len(en_dl) < self.plan.telechargements and \
                        len(en_dl) + len(prets) + len(en_conv) < fenetre:
                    x = file_.pop(0)
                    i = ident(x)
                    _, essais, _ = self.etat.lire(i)
                    self.etat.ecrire(i, x['access_url'], 'en_cours', info_de_base(x), essais + 1)
                    en_dl[pool_dl.submit(self._telecharger, x)] = x
                # alimenter les conversions
                while prets and len(en_conv) < self.plan.conversions:
                    x, fic, t_dl = prets.pop(0)
                    m1, m2 = attentes_pour(x, med, medo)
                    xx = {k: (str(v) if k == 'nuit' else v) for k, v in x.items()}
                    fut = pool_cv.submit(convertir, xx, fic, self._sortie_staging(x), m1, m2, options_proc)
                    en_conv[fut] = (x, fic, t_dl)
                attente = list(en_dl) + list(en_conv)
                if not attente:
                    continue
                fait, _ = F.wait(attente, timeout=0.5, return_when=F.FIRST_COMPLETED)
                for fut in fait:
                    if fut in en_dl:
                        x = en_dl.pop(fut)
                        try:
                            fic, t_dl, recu = fut.result()
                            prets.append((x, fic, t_dl))
                            self.rapporter({'type': 'telecharge', 'id': ident(x), 'source': x['access_url']})
                        except reseau.Annule:
                            pass
                        except Exception as e:
                            from ...core.i18n import tr
                            self._echec(x, 'download: %s — %s' % (e, tr('ohp_url_injoignable')))
                            compte['echec'] += 1
                    else:
                        x, fic, t_dl = en_conv.pop(fut)
                        try:
                            info = fut.result()
                        except F.process.BrokenProcessPool as e:
                            self._echec(x, 'BrokenProcessPool: %s' % e)
                            compte['echec'] += 1
                            pool_cv.shutdown(wait=False, cancel_futures=True)
                            pool_cv = F.ProcessPoolExecutor(max(1, self.plan.conversions), mp_context=ctx)
                            for fut2, v in list(en_conv.items()):
                                prets.insert(0, v)
                            en_conv.clear()
                            continue
                        except Exception as e:
                            self._echec(x, '%s: %s' % (type(e).__name__, e), getattr(e, '__traceback__', None))
                            compte['echec'] += 1
                            self._supprimer(self._sortie_staging(x))
                            continue
                        r = self._enregistrer(x, fic, info, t_dl)
                        compte[r] += 1
                        n = sum(compte.values())
                        self.rapporter({'type': 'image', 'statut': r, 'n': n, 'total': total,
                                        'wcs': info.get('wcs'), 'source': info.get('source'),
                                        'ratio': info.get('ratio'), 'ecoule': time.time() - t0})
        finally:
            annule = self.arret.is_set()
            pool_dl.shutdown(wait=True, cancel_futures=True)
            pool_cv.shutdown(wait=True, cancel_futures=True)
            # les FITS téléchargés mais pas convertis restent dans telechargements/ : la reprise
            # les retrouve (taille complète) sans les retélécharger
        index = self.ranger()
        bilan = self.etat.bilan()
        bilan.update(compte=compte, lots=len(index), annule=annule, duree=round(time.time() - t0, 1))
        self.rapporter({'type': 'fin', 'bilan': bilan})
        return bilan

    def _supprimer(self, p):
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass

    def _echec(self, x, msg, tb=None):
        i = ident(x)
        info = info_de_base(x)
        info['erreur'] = msg[:500]
        if tb is not None:
            info['trace'] = ''.join(traceback.format_tb(tb))[-800:]
        self.etat.ecrire(i, x['access_url'], 'echec', info)
        self.rapporter({'type': 'echec', 'id': i, 'source': info['source'], 'erreur': msg[:300]})

    def _enregistrer(self, x, fic, info, t_dl):
        i = ident(x)
        info['t_telechargement'] = t_dl
        info['extension'] = formats.EXTENSIONS[self.options['format']]
        autre = self.etat.empreinte(info['sha_pixels'], i)
        if autre is not None and self.options.get('garder_doublons'):
            info['doublon_de'] = autre          # gardée à la demande, signalée dans le journal
            autre = None
            info['doublon_de'] = autre
            self._supprimer(info['staging'])
            if not self.options.get('garder_fits'):
                self._supprimer(fic)
            self.etat.ecrire(i, x['access_url'], 'doublon', info)
            return 'doublon'
        if self.options.get('garder_fits'):
            dest = os.path.join(self.trav, 'fits_origine', os.path.basename(x['access_url']))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(fic, dest)
        else:
            self._supprimer(fic)
        self.etat.ecrire(i, x['access_url'], 'ok', info)
        return 'ok'

    def ranger(self):
        tout = self.etat.ok()
        if not tout:
            lots.ecrire_journal(os.path.join(self.trav, 'journal.csv'), self.racine, self.etat.toutes())
            return []

        def maj(i, info):
            self.etat.ecrire(i, info['url'], 'ok', info)
        index = lots.ranger(self.racine, tout, self.options['langue'], maj,
                            formats.EXTENSIONS[self.options['format']])
        lots.ecrire_journal(os.path.join(self.trav, 'journal.csv'), self.racine, self.etat.toutes())
        return index

    def fermer(self):
        self.etat.fermer()
