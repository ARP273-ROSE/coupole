"""Pilote du traitement : téléchargements (fils), conversions (processus), état, rangement, journal.

* État dans ``<destination>/_traitement/etat.sqlite`` (journal DELETE, jamais
  WAL : la destination peut être un partage réseau) : un traitement interrompu
  (coupure, annulation, plantage) reprend là où il s'était arrêté ; une image
  convertie n'est jamais refaite.  Sur un partage réseau (où SQLite ne peut pas
  écrire sous Linux), base de travail locale recopiée sur le partage toutes les
  30 s, en fin de session et à l'arrêt (``core/base_partagee.py``).
* Chaîne en pipeline (producteur / consommateur, file bornée) : les
  téléchargements (fils) et les conversions (processus séparés : zstd, numpy et
  ASTAP tournent hors du GIL) se recouvrent ; pas plus de
  ``2 x conversions + téléchargements`` FITS en attente sur le disque.
* L'interface reçoit des événements (dictionnaires) par ``rapporter`` ; elle
  ne bloque jamais : ce pilote tourne dans un fil à part.  Les octets reçus
  sont agrégés (au plus ~10 événements par seconde), jamais un par bloc.
* Annulation : l'événement ``arret`` interrompt les téléchargements, les
  processus de conversion sont terminés (et ASTAP tué avec eux) ; l'appelant
  n'attend jamais la fin d'une image de 4 minutes.  ``pause`` suspend
  l'alimentation du pipeline sans rien perdre.
* Journal lisible et bilingue ``_traitement/JOURNAL.txt`` (sessions, images,
  écarts, erreurs, reprises ; rotation à 5 Mo), en plus de ``journal.csv``.
"""
from __future__ import annotations

import collections
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
from ...core import base_partagee, reseau
from ...core.i18n import bilingue, tr
from ...core.parallele import Plan
from . import formats, lots
from .astrometrie import attentes, attentes_pour
from .conversion import convertir, ident, info_de_base

VERSION_MODULE = '1.1.0'
JOURNAL_MAX = 5 * 2**20            # octets : au-delà, JOURNAL.txt tourne (JOURNAL-1.txt, JOURNAL-2.txt)
JOURNAL_COPIES = 2
CADENCE_OCTETS = 0.1               # secondes entre deux événements « octets » (10 Hz)
DELAI_VALIDATION = 1.0             # secondes : la base d'état et JOURNAL.txt sont écrits au plus une fois par seconde


class Etat:
    """Base SQLite d'état (même schéma que le traitement de référence).

    Validations groupées : une écriture n'est validée (`commit`) que si la précédente validation date de plus de
    `delai` secondes ; `valider()` force, `fermer()` valide.  En journal DELETE, chaque `commit` crée, écrit,
    synchronise puis efface un fichier de journal : 77 ms par validation sur un partage réseau (2 ms par
    aller-retour), soit 3 validations par image auparavant.  Une coupure perd au plus `delai` secondes d'état :
    les images concernées sont simplement refaites à la reprise.  `delai=0` : validation à chaque écriture.
    """

    def __init__(self, chemin, delai: float = 0.0, reseau: bool | None = None, rapporter=None,
                 intervalle: float = base_partagee.INTERVALLE_S):
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        self.delai = float(delai)
        self._derniere = time.monotonic()
        self._en_attente = False
        self.chemin = chemin
        # partage réseau (ou base verrouillée) : base de travail locale, recopiée sur le partage (core/base_partagee)
        self.base = base_partagee.BasePartagee(chemin, reseau=reseau, intervalle=intervalle, rapporter=rapporter)
        travail = self.base.ouvrir()                  # Divergence : rien n'est ouvert ni écrasé
        self.locale = self.base.mode == 'local'
        self.db = sqlite3.connect(travail, check_same_thread=False, timeout=60)
        self.db.execute('PRAGMA journal_mode=DELETE')
        self.db.execute('CREATE TABLE IF NOT EXISTS images (id TEXT PRIMARY KEY, url TEXT, statut TEXT, '
                        'essais INTEGER DEFAULT 0, info TEXT, maj TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS empreintes (sha TEXT PRIMARY KEY, id TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT)')
        self.db.commit()
        self.verrou = threading.Lock()

    def synchroniser_si_du(self):
        """Base de travail locale : recopie sur le partage toutes les `intervalle` s (transfert dans un fil)."""
        return self.locale and self.base.envoyer_si_du(self.db, verrou=self.verrou)

    def synchroniser(self) -> bool:
        """Recopie immédiate (fin de session) ; True si le partage est à jour."""
        if not self.locale:
            return True
        self.valider()
        return self.base.fermer(self.db, verrou=self.verrou)

    def lire(self, i):
        with self.verrou:
            r = self.db.execute('SELECT statut, essais, info FROM images WHERE id=?', (i,)).fetchone()
        return (r[0], r[1], json.loads(r[2]) if r[2] else {}) if r else (None, 0, {})

    def _peut_etre_valider(self):
        """(sous le verrou) valide si le délai est écoulé, sinon garde l'écriture en attente."""
        self._en_attente = True
        t = time.monotonic()
        if self.delai <= 0 or t - self._derniere >= self.delai:
            self.db.commit()
            self._derniere = t
            self._en_attente = False

    def valider_si_du(self):
        """Valide l'écriture en attente si elle a dépassé le délai (appelé à chaque tour du pilote : rien ne reste
        non validé pendant une pause ou une longue conversion)."""
        if self._en_attente and time.monotonic() - self._derniere >= self.delai:
            self.valider()

    def valider(self):
        with self.verrou:
            if self._en_attente:
                self.db.commit()
                self._derniere = time.monotonic()
                self._en_attente = False

    def ecrire(self, i, url, statut, info, essais=None):
        with self.verrou:
            if essais is None:
                essais = (self.db.execute('SELECT essais FROM images WHERE id=?', (i,)).fetchone() or [0])[0]
            self.db.execute('INSERT OR REPLACE INTO images VALUES (?,?,?,?,?,?)',
                            (i, url, statut, essais, json.dumps(info, ensure_ascii=False, default=str),
                             D.datetime.now().isoformat(timespec='seconds')))
            self._peut_etre_valider()

    def empreinte(self, sha, i):
        """Renvoie l'id déjà associé à ces pixels, ou None (et enregistre `i`)."""
        with self.verrou:
            r = self.db.execute('SELECT id FROM empreintes WHERE sha=?', (sha,)).fetchone()
            if r is None:
                self.db.execute('INSERT INTO empreintes VALUES (?,?)', (sha, i))
                self._peut_etre_valider()
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

    def statuts(self) -> dict:
        """{id: statut} de toutes les images connues (reprise, nouveautés)."""
        with self.verrou:
            return dict(self.db.execute('SELECT id, statut FROM images').fetchall())

    def statuts_essais(self) -> dict:
        """{id: (statut, essais)} en une requête (reprise : plus de lecture par image)."""
        with self.verrou:
            return {i: (st, e or 0) for i, st, e in self.db.execute('SELECT id, statut, essais FROM images')}

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
            try:
                if self._en_attente:
                    self.db.commit()
                    self._en_attente = False
            except sqlite3.Error:
                pass
        try:
            if self.locale:                           # dernière recopie (fin, arrêt, annulation)
                self.base.fermer(self.db, verrou=self.verrou)
        finally:
            with self.verrou:
                self.db.close()


# ============================================================================ journal lisible
class Journal:
    """``_traitement/JOURNAL.txt`` : une ligne horodatée (UTC) et bilingue par événement ; rotation."""

    def __init__(self, dossier, delai: float = 0.0):
        self.chemin = os.path.join(dossier, 'JOURNAL.txt')
        self.verrou = threading.Lock()
        self.delai = float(delai)             # > 0 : lignes regroupées, écrites au plus une fois par `delai` s
        self._tampon: list[str] = []
        self._derniere = time.monotonic()

    def _tourner(self):
        try:
            if os.path.exists(self.chemin) and os.path.getsize(self.chemin) > JOURNAL_MAX:
                for k in range(JOURNAL_COPIES, 0, -1):
                    src = self.chemin.replace('.txt', '-%d.txt' % (k - 1)) if k > 1 else self.chemin
                    dst = self.chemin.replace('.txt', '-%d.txt' % k)
                    if os.path.exists(src):
                        os.replace(src, dst)
        except OSError:
            pass

    def ecrire(self, cle: str, **valeurs):
        """`cle` : clé de traduction (texte FR / texte EN sur la même ligne)."""
        ligne = '%s | %s\n' % (D.datetime.now(D.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                               bilingue(cle, ' / ', **valeurs))
        with self.verrou:
            self._tampon.append(ligne)
            if self.delai <= 0 or time.monotonic() - self._derniere >= self.delai:
                self._vider()

    def vider(self):
        with self.verrou:
            self._vider()

    def vider_si_du(self):
        if self._tampon and time.monotonic() - self._derniere >= self.delai:
            self.vider()

    def _vider(self):
        """(sous le verrou) une ouverture du fichier pour toutes les lignes en attente (et non une par ligne)."""
        self._derniere = time.monotonic()
        if not self._tampon:
            return
        lignes, self._tampon = ''.join(self._tampon), []
        self._tourner()
        try:
            with open(self.chemin, 'a', encoding='utf-8') as f:
                f.write(lignes)
        except OSError:
            pass


def _initialiser_processus():
    """Dans chaque processus de conversion : SIGTERM tue ASTAP en cours puis quitte (annulation propre) ; sous
    Windows (pas de signal), le processus se place dans un job object « kill on close » : l'ASTAP qu'il lancera
    meurt avec lui dès que le pilote le termine (core/processus.py ; repli silencieux si l'API refuse)."""
    try:
        from ...core import astap, processus
        astap.installer_arret_propre()
        processus.confiner_descendance()
    except Exception:
        pass


class Traitement:
    """Télécharge, convertit et range une sélection d'images.

    options : format, langue (noms et en-têtes), astap (EtatASTAP ou None), mode_astap,
              debit_octets_s, garder_fits (bool), garder_doublons (bool).
    arret : threading.Event (annulation) ; pause : threading.Event (suspend l'alimentation du pipeline).
    """

    def __init__(self, racine, inventaire, plan: Plan, options: dict, rapporter=None, arret=None, pause=None):
        self.racine = os.path.abspath(racine)
        self.trav = os.path.join(self.racine, '_traitement')
        self.dl = os.path.join(self.trav, 'telechargements')
        self.staging = os.path.join(self.trav, 'converties')
        for d in (self.trav, self.dl, self.staging):
            os.makedirs(d, exist_ok=True)
        self._verifier_inscriptible()
        self.inventaire = inventaire
        self.plan = plan
        self.options = dict(options)
        self.options.setdefault('format', 'xisf')
        self.options.setdefault('langue', 'fr')
        self.options.setdefault('mode_astap', 'tous')
        self.options['createur'] = 'Coupole %s (ohp %s)' % (__version__, VERSION_MODULE)
        self.rapporter = rapporter or (lambda ev: None)
        self.arret = arret or threading.Event()
        self.pause = pause or threading.Event()
        self.journal = Journal(self.trav, DELAI_VALIDATION)
        self.etat = Etat(os.path.join(self.trav, 'etat.sqlite'), DELAI_VALIDATION, rapporter=self._avis_base)
        self._verifier_coherence()
        self.limiteur = reseau.LimiteurDebit(self.options.get('debit_octets_s', 8e6))
        self._med = self._medo = None
        self._essais = {}
        self._octets = 0
        self._octets_t = 0.0
        self._octets_verrou = threading.Lock()

    def _avis_base(self, cle, **valeurs):
        """Messages de la base de travail locale (partage réseau) : JOURNAL.txt et interface."""
        self.journal.ecrire(cle, **valeurs)
        self.journal.vider()
        self.rapporter({'type': 'base_locale', 'cle': cle, 'valeurs': valeurs})

    def _verifier_inscriptible(self):
        """Un dossier de sortie non inscriptible se détecte avant de télécharger quoi que ce soit."""
        test = os.path.join(self.trav, '.ecriture-%d' % os.getpid())
        try:
            with open(test, 'wb') as f:
                f.write(b'ok')
            os.remove(test)
        except OSError as e:
            raise OSError('%s: %s' % (tr('ohp_dest_non_inscriptible', dest=self.racine), e)) from e

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
    def _progression(self, n):
        """Octets reçus, agrégés : un événement au plus toutes les CADENCE_OCTETS secondes."""
        with self._octets_verrou:
            self._octets += n
            t = time.monotonic()
            if t - self._octets_t < CADENCE_OCTETS:
                return
            total, self._octets, self._octets_t = self._octets, 0, t
        self.rapporter({'type': 'octets', 'n': total})

    def _vider_octets(self):
        with self._octets_verrou:
            total, self._octets = self._octets, 0
        if total:
            self.rapporter({'type': 'octets', 'n': total})

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
        t0 = time.time()
        from ...core import sources
        etat, recu = reseau.telecharger(sources.reecrire_url(x['access_url']), fic,
                                        taille_attendue=int(x['access_estsize'] * 1024),
                                        limiteur=self.limiteur, arret=self.arret, progression=self._progression,
                                        verifier=verifier)
        return fic, round(time.time() - t0, 1), recu

    def _sortie_staging(self, x):
        return os.path.join(self.staging, ident(x) + formats.EXTENSIONS[self.options['format']])

    # ---------------------------------------------------------------- principal
    def a_faire(self, selection: list[dict]) -> tuple[list[dict], list[dict]]:
        """(images à traiter, images utiles de la sélection) d'après l'état : ce qui est fait n'est pas refait."""
        garder = bool(self.options.get('garder_doublons'))
        xs = sorted([x for x in selection if garder or not x['doublon']], key=lambda x: (x['t_min'], x['access_url']))
        connus = self.etat.statuts_essais()            # une requête pour toute la sélection
        self._essais = {i: e for i, (_, e) in connus.items()}
        out = []
        for x in xs:
            st, essais = connus.get(ident(x), (None, 0))
            if st in ('ok', 'doublon'):
                continue
            if essais < 5:
                out.append(x)
        return out, xs

    def lancer(self, selection: list[dict]) -> dict:
        """Traite `selection` (lignes enrichies de l'inventaire, doublons compris)."""
        med, medo = self.attentes()
        garder = bool(self.options.get('garder_doublons'))
        connus = self.etat.statuts() if not garder else {}       # une requête, et non une par doublon
        for x in selection:
            if x['doublon'] and not garder:
                i = ident(x)
                if connus.get(i) is None:
                    connus[i] = 'doublon'
                    self.etat.ecrire(i, x['access_url'], 'doublon',
                                     dict(info_de_base(x), doublon_de='inventaire'), 0)
                    self.journal.ecrire('jrn_doublon_inventaire', source=x['access_url'].rsplit('/', 1)[1],
                                        raison=x.get('raison_doublon') or 'meme_fichier')
        self.etat.valider()
        a_faire, xs = self.a_faire(selection)
        total = len(a_faire)
        reprise = len(xs) - total
        fits_retrouves = sum(1 for x in a_faire if os.path.exists(os.path.join(self.dl, ident(x) + '.fits')))
        self.journal.ecrire('jrn_session_debut', version=__version__, n=total, deja=reprise, dest=self.racine,
                            format=self.options['format'].upper(), dl=self.plan.telechargements,
                            conv=self.plan.conversions)
        if (reprise or fits_retrouves) and total:
            self.journal.ecrire('jrn_reprise', deja=reprise, fits=fits_retrouves)
        self.rapporter({'type': 'debut', 'total': total, 'deja': reprise,
                        'octets': sum(x['access_estsize'] * 1024 for x in a_faire),
                        'plan': {'telechargements': self.plan.telechargements, 'conversions': self.plan.conversions}})
        compte = {'ok': 0, 'doublon': 0, 'echec': 0}
        echecs: list[dict] = []
        fenetre = self._fenetre(a_faire)
        ctx = mp.get_context('spawn')
        options_proc = dict(self.options)
        astap = options_proc.get('astap')
        if astap is not None and not isinstance(astap, dict):
            options_proc['astap'] = {k: getattr(astap, k) for k in ('executable', 'version', 'est_cli',
                                                                     'catalogue_dossier', 'catalogue',
                                                                     'catalogue_fichiers', 'catalogue_complet')}
        file_ = collections.deque(a_faire)
        en_dl: dict = {}
        en_conv: dict = {}
        prets: list = []
        pool_dl = F.ThreadPoolExecutor(max(1, self.plan.telechargements), thread_name_prefix='dl')
        pool_cv = self._nouveau_pool(ctx)
        t0 = time.time()
        en_pause = False
        try:
            while (file_ or en_dl or en_conv or prets) and not self.arret.is_set():
                self.etat.valider_si_du()
                self.etat.synchroniser_si_du()
                self.journal.vider_si_du()
                if self.pause.is_set():
                    if not en_pause:
                        en_pause = True
                        self.journal.ecrire('jrn_pause')
                        self.rapporter({'type': 'pause', 'actif': True})
                elif en_pause:
                    en_pause = False
                    self.journal.ecrire('jrn_reprise_pause')
                    self.rapporter({'type': 'pause', 'actif': False})
                # alimenter les téléchargements sans dépasser la fenêtre disque (pas pendant une pause)
                while file_ and not en_pause and len(en_dl) < self.plan.telechargements and \
                        len(en_dl) + len(prets) + len(en_conv) < fenetre:
                    x = file_.popleft()
                    i = ident(x)
                    essais = self._essais.get(i, 0) + 1       # (lus une fois dans a_faire)
                    self._essais[i] = essais
                    self.etat.ecrire(i, x['access_url'], 'en_cours', info_de_base(x), essais)
                    en_dl[pool_dl.submit(self._telecharger, x)] = x
                # alimenter les conversions
                while prets and not en_pause and len(en_conv) < self.plan.conversions:
                    x, fic, t_dl = prets.pop(0)
                    m1, m2 = attentes_pour(x, med, medo)
                    xx = {k: (str(v) if k == 'nuit' else v) for k, v in x.items()}
                    fut = pool_cv.submit(convertir, xx, fic, self._sortie_staging(x), m1, m2, options_proc)
                    en_conv[fut] = (x, fic, t_dl)
                attente = list(en_dl) + list(en_conv)
                if not attente:
                    if en_pause or (file_ and len(en_dl) + len(prets) + len(en_conv) >= fenetre):
                        self.arret.wait(0.25)
                    continue
                fait, _ = F.wait(attente, timeout=0.5, return_when=F.FIRST_COMPLETED)
                for fut in fait:
                    if fut in en_dl:
                        x = en_dl.pop(fut)
                        try:
                            fic, t_dl, recu = fut.result()
                            prets.append((x, fic, t_dl))
                            self._vider_octets()
                            self.rapporter({'type': 'telecharge', 'id': ident(x), 'source': x['access_url']})
                            self.journal.ecrire('jrn_telechargee', source=x['access_url'].rsplit('/', 1)[1],
                                                octets=recu, duree=t_dl)
                        except reseau.Annule:
                            pass
                        except Exception as e:
                            self._echec(x, 'download: %s — %s' % (e, tr('ohp_url_injoignable')))
                            compte['echec'] += 1
                            echecs.append({'source': x['access_url'], 'erreur': str(e)[:200]})
                    elif fut in en_conv:
                        x, fic, t_dl = en_conv.pop(fut)
                        try:
                            info = fut.result()
                        except F.process.BrokenProcessPool as e:
                            # un processus de conversion est mort (mémoire, plantage natif) : l'image est notée en
                            # échec, le bassin est reconstruit, les autres conversions en cours sont remises en file
                            self._echec(x, 'BrokenProcessPool: %s' % e)
                            compte['echec'] += 1
                            echecs.append({'source': x['access_url'], 'erreur': 'worker crashed'})
                            self.journal.ecrire('jrn_processus_perdu', source=x['access_url'].rsplit('/', 1)[1])
                            pool_cv.shutdown(wait=False, cancel_futures=True)
                            pool_cv = self._nouveau_pool(ctx)
                            for fut2, v in list(en_conv.items()):
                                prets.insert(0, v)
                            en_conv.clear()
                            break                        # les autres futurs de ce bassin sont caducs
                        except Exception as e:
                            self._echec(x, '%s: %s' % (type(e).__name__, e), getattr(e, '__traceback__', None))
                            compte['echec'] += 1
                            echecs.append({'source': x['access_url'], 'erreur': '%s: %s' % (type(e).__name__, str(e)[:160])})
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
            self._vider_octets()
            pool_dl.shutdown(wait=True, cancel_futures=True)
            if annule:
                self._terminer_processus(pool_cv)
            pool_cv.shutdown(wait=not annule, cancel_futures=True)
            # les FITS téléchargés mais pas convertis restent dans telechargements/ : la reprise
            # les retrouve (taille complète) sans les retélécharger
            for fic in [v[1] for v in en_conv.values()]:
                self._supprimer(fic + '.tmp')
        self.etat.valider()                              # l'état de chaque image est sur le disque avant le rangement
        self.journal.vider()
        index = self.ranger()
        self.etat.valider()
        self.etat.synchroniser()                         # base de travail locale : le partage est à jour
        bilan = self.etat.bilan()
        bilan.update(compte=compte, lots=len(index), annule=annule, duree=round(time.time() - t0, 1),
                     echecs=echecs[:50], images=total)
        self.journal.ecrire('jrn_session_fin', ok=compte['ok'], doublons=compte['doublon'], echecs=compte['echec'],
                            duree=int(bilan['duree']), sortie='%.2f' % (bilan['octets_sortie'] / 1e9), lots=len(index),
                            etat='interrompu / interrupted' if annule else 'terminé / finished')
        self.journal.vider()
        self.rapporter({'type': 'fin', 'bilan': bilan})
        return bilan

    def _fenetre(self, a_faire) -> int:
        """FITS en attente autorisés : la fenêtre nominale (2 × conversions + téléchargements), réduite si la place
        libre à destination est juste — le traitement continue, un peu moins recouvert, au lieu d'être refusé."""
        from ...core.machine import disque_libre_go
        from .selection import estimer, fenetre_adaptee, fenetre_nominale
        nominale = fenetre_nominale(self.plan.conversions, self.plan.telechargements)
        try:
            est = estimer(a_faire, self.options.get('format', 'xisf'))
            libre = disque_libre_go(self.racine) * 1e9
            fenetre = fenetre_adaptee(est, self.plan.conversions, self.plan.telechargements, libre)
        except Exception:                                   # l'estimation ne fait jamais échouer un traitement
            return nominale
        if fenetre < nominale:
            self.journal.ecrire('jrn_fenetre_reduite', fenetre=fenetre, nominale=nominale, libre='%.2f' % (libre / 1e9))
            self.rapporter({'type': 'fenetre', 'fenetre': fenetre, 'nominale': nominale, 'libre': libre})
        return fenetre

    def _nouveau_pool(self, ctx):
        return F.ProcessPoolExecutor(max(1, self.plan.conversions), mp_context=ctx, initializer=_initialiser_processus)

    @staticmethod
    def _terminer_processus(pool):
        """Annulation : les processus de conversion sont terminés tout de suite (ASTAP compris : par leur
        gestionnaire SIGTERM sous Linux/macOS, par le job object sous Windows) au lieu d'attendre la fin de
        l'image en cours."""
        procs = getattr(pool, '_processes', None) or {}
        for p in list(procs.values()):
            try:
                p.terminate()
            except Exception:
                pass
        for p in list(procs.values()):
            try:
                p.join(3)
                if p.is_alive():
                    p.kill()
            except Exception:
                pass

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
        self.journal.ecrire('jrn_echec', source=info['source'], erreur=msg[:200])
        self.rapporter({'type': 'echec', 'id': i, 'source': info['source'], 'erreur': msg[:300]})

    def _enregistrer(self, x, fic, info, t_dl):
        i = ident(x)
        info['t_telechargement'] = t_dl
        info['extension'] = formats.EXTENSIONS[self.options['format']]
        autre = self.etat.empreinte(info['sha_pixels'], i)
        if autre is not None:
            if self.options.get('garder_doublons'):
                info['doublon_de'] = autre          # gardée à la demande, signalée dans le journal
                self.journal.ecrire('jrn_pixels_identiques_gardee', source=info['source'], autre=autre)
            else:                                   # mêmes pixels qu'une image déjà convertie : écartée
                info['doublon_de'] = autre
                self._supprimer(info['staging'])
                if not self.options.get('garder_fits'):
                    self._supprimer(fic)
                self.etat.ecrire(i, x['access_url'], 'doublon', info)
                self.journal.ecrire('jrn_pixels_identiques', source=info['source'], autre=autre)
                return 'doublon'
        if self.options.get('garder_fits'):
            dest = os.path.join(self.trav, 'fits_origine', os.path.basename(x['access_url']))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(fic, dest)
        else:
            self._supprimer(fic)
        self.etat.ecrire(i, x['access_url'], 'ok', info)
        self.journal.ecrire('jrn_convertie', source=info['source'], wcs=info.get('wcs', ''),
                            ratio='%.0f' % (100 * info.get('ratio', 0)), duree=info.get('t_conversion', 0))
        return 'ok'

    def ranger(self):
        tout = self.etat.ok()
        if not tout:
            lots.ecrire_journal(os.path.join(self.trav, 'journal.csv'), self.racine, self.etat.toutes())
            return []

        def maj(i, info):
            self.etat.ecrire(i, info['url'], 'ok', info)
        conflits = []
        index = lots.ranger(self.racine, tout, self.options['langue'], maj,
                            formats.EXTENSIONS[self.options['format']], conflits=conflits)
        for c in conflits:
            self.journal.ecrire('jrn_conflit_nom', voulu=c[0], retenu=c[1])
        lots.ecrire_journal(os.path.join(self.trav, 'journal.csv'), self.racine, self.etat.toutes())
        return index

    # ---------------------------------------------------------------- réorganiser des fichiers déjà convertis
    def reorganiser(self, dossier_source, progression=None) -> dict:
        """Range dans l'arborescence des lots des fichiers convertis par Coupole qui se trouvent ailleurs (ou
        selon un ancien rangement) : déplacement, jamais de copie ni d'écrasement, une ligne de journal par fichier.

        Chaque fichier est identifié par son en-tête (adresse d'origine OHP:Source:URL ou carte HISTORY « converti
        de <fichier> ») et rattaché à la ligne d'inventaire correspondante.  Renvoie
        {'ranges': n, 'ignores': [(chemin, raison)], 'lots': n}.
        """
        from . import reorganisation
        trouves, ignores = reorganisation.inventorier(dossier_source, self.inventaire, self.racine,
                                                      progression=progression, arret=self.arret)
        n = 0
        statuts = self.etat.statuts()                 # une requête ; les infos ne sont relues que pour les « ok »
        for chemin, x, info in trouves:
            i = ident(x)
            st, _, ancienne = self.etat.lire(i) if statuts.get(i) == 'ok' else (statuts.get(i), 0, {})
            deja = ancienne.get('final') and os.path.exists(ancienne['final']) and \
                os.path.abspath(ancienne['final']) != os.path.abspath(chemin) and \
                os.path.getsize(ancienne['final']) == ancienne.get('octets_sortie', -1)
            if st == 'ok' and deja:                  # la même image est déjà rangée (taille identique) : on la garde
                ignores.append((chemin, 'deja_rangee'))
                self.journal.ecrire('jrn_reorg_ignore', fichier=chemin, raison=bilingue('reorg_deja_rangee'))
                continue
            info['staging'] = chemin
            info['final'] = None
            info['extension'] = os.path.splitext(chemin)[1] if not chemin.endswith('.fits.fz') else '.fits.fz'
            self.etat.ecrire(i, x['access_url'], 'ok', info)
            if info.get('sha_pixels'):
                self.etat.empreinte(info['sha_pixels'], i)
            n += 1
            self.journal.ecrire('jrn_reorg_fichier', fichier=chemin, objet=info['objet'])
        for chemin, raison in ignores:
            if raison != 'deja_rangee':
                self.journal.ecrire('jrn_reorg_ignore', fichier=chemin, raison=bilingue('reorg_' + raison))
        index = self.ranger() if n else []
        reorganisation.nettoyer_dossiers_vides(dossier_source, self.racine,
                                               {os.path.dirname(c) for c, _, _ in trouves})
        return {'ranges': n, 'ignores': ignores, 'lots': len(index)}

    def fermer(self):
        self.journal.vider()
        self.etat.fermer()


# ============================================================================ estimations (avant de lancer)
def estimation_temps(octets: float, debit_octets_s: float) -> float:
    """Durée (s) du téléchargement au débit plafond ; la conversion se recouvre avec le réseau (pipeline)."""
    return octets / max(1.0, debit_octets_s)


def dossier_sortie_propose() -> str:
    """Dossier par défaut selon le système : Documents/Coupole/OHP_DU_ECU (Documents du système si connu)."""
    import sys
    from pathlib import Path
    h = Path.home()
    docs = None
    if sys.platform == 'win32':
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:   # CSIDL_PERSONAL
                docs = Path(buf.value)
        except Exception:
            docs = None
    else:
        try:                                     # xdg-user-dirs (Linux) ; macOS : ~/Documents
            conf = Path(os.environ.get('XDG_CONFIG_HOME') or h / '.config') / 'user-dirs.dirs'
            for ligne in conf.read_text(encoding='utf-8').splitlines():
                if ligne.startswith('XDG_DOCUMENTS_DIR='):
                    docs = Path(os.path.expandvars(ligne.split('=', 1)[1].strip().strip('"')))
        except OSError:
            pass
    if docs is None or not docs.is_dir():
        docs = h / 'Documents' if (h / 'Documents').is_dir() else h
    return str(docs / 'Coupole' / 'OHP_DU_ECU')
