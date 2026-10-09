"""Moteur de mesure : inventaire en flux, processus parallèles, cache des mesures, échantillon par lot, reprise,
annulation, ETA.

Sans Qt.  L'interface et la ligne de commande lui passent une fonction `rapporter(événement)` :

  {'type': 'inventaire', 'trouves', 'lots', 'fini', 'source'}  avancement de l'inventaire (≤ 10 Hz, puis fini)
  {'type': 'question', 'total_dossier', 'lots', 'a_mesurer', 'a_mesurer_echantillon', 'par_image_s',
   'duree_s', 'duree_echantillon_s', 'processus', 'reseau', 'n'}
                                                         gros dossier (mode `demander`) : répondre par `decider`
  {'type': 'decision', 'decision', 'total_dossier', 'n'}   mode `auto` : échantillon choisi pour un gros dossier
  {'type': 'debut', 'total', 'deja', 'processus', 'reseau', 'echantillon', 'lots', 'total_dossier'}
                                                         inventaire fini et décision prise (le total est connu)
  {'type': 'image', 'lot', 'ligne', 'deja'}               une image mesurée (ou relue du cache)
  {'type': 'progression', 'fait', 'total', 'eta_s', 'debit', 'inventaire_fini'}   agrégée, au plus 10 fois par s
  {'type': 'lot', 'lot', 'lignes'}                        un lot terminé (QUALITE.csv et QUALITE.txt écrits)
  {'type': 'fin', 'n', 'lots', 'duree', 'annule', 'echecs', 'absentes'}

**Inventaire en flux** (0.1.9) : la mesure commence dès le premier lot trouvé, pendant que l'inventaire continue
(producteur dans un fil, consommateur ici).  L'inventaire ne lit aucun fichier (aucune ouverture : la mesure s'en
charge) et fait au plus un `stat` par image retenue (taille et date, pour reconnaître le cache) :

  * dossier qui est (ou est dans) une sortie Coupole — ``INDEX_LOTS.csv`` ou ``_traitement/etat.sqlite`` à la
    racine ou dans un parent : l'index des lots (≈ 100 Ko, lu d'un bloc), sinon la base d'état (destinations des
    images converties ; copiée d'un bloc si elle est sur un partage), donne les dossiers des lots, **sans
    parcourir le partage** : seuls ces dossiers sont lus, tous en même temps, et la liste de chacun donne taille
    et date (image de la base absente du disque : ignorée, comptée ; restes de traitement hors des lots, comme
    ``converties`` ou ``telechargements``, jamais pris pour des lots) ;
  * sinon parcours parallèle (`core.parcours.parcourir`), chaque dossier livré dès qu'il est lu, la taille et la
    date lues juste après la liste, dans le même fil.

Fils de lecture des dossiers : 16, et 32 sur un partage — chaque liste y coûte quelques allers-retours (ouvrir,
lire deux fois, fermer) ; mesuré sur un vrai partage SMB à 20 ms : 8 fils 3,5 s, 16 fils 1,5 s, 32 fils 0,7 s pour
les 209 dossiers de 09_Galaxies.

Le travail lourd (lecture + décompression zstd, SEP, ajustement des étoiles) tourne dans des processus séparés
(`multiprocessing` en mode spawn, comme le pilote de la Banque OHP) dimensionnés par le plan machine ; la lecture
d'une image recouvre le calcul des autres.  Chaque image mesurée est mise en cache par (chemin, taille, mtime) et
le QUALITE.csv de son lot est réécrit au plus toutes les 5 s : relancer ne refait pas ce qui est déjà mesuré.

**Cache** : ``<racine>/_traitement/qualite.sqlite`` sur un disque local ; **jamais sur un partage réseau** —
SQLite y écrit à travers les verrous de plage SMB, que le client cifs de Linux transmet au serveur : « database is
locked » au bout du délai d'attente (30 s par ouverture en 0.1.8, trois ouvertures avant la première mesure : 90 s
d'« Inventaire du dossier… » sur le vrai partage de Kevin, fichier de 0 octet).  Sur un partage, le cache va dans
le dossier de cache de l'utilisateur (un fichier par dossier analysé) ; un ancien cache du partage est seulement lu.
"""
from __future__ import annotations

import collections
import concurrent.futures as F
import csv
import io
import json
import multiprocessing as mp
import os
import queue
import sqlite3
import threading
import time
from pathlib import Path

from ...core import config
from ...core.parallele import Plan
from . import rapport

SEUIL_GROS_DOSSIER = 200          # au-delà, l'échantillon par lot est proposé par défaut
ECHANTILLON_DEFAUT = 5
LECTEURS_RESEAU_MAX = 3           # processus au plus quand le dossier est sur un partage
CADENCE_PROGRESSION = 0.1         # secondes entre deux événements « progression » / « inventaire » (10 Hz)
DELAI_VALIDATION = 1.0            # secondes : le cache est validé (commit) au plus une fois par seconde
ECRITURE_CSV_S = 5.0              # secondes : QUALITE.csv d'un lot en cours réécrit au plus toutes les 5 s
FILS_LISTE = 16                   # fils qui lisent les dossiers (allers-retours recouverts, GIL rendu)
FILS_LISTE_RESEAU = 32            # sur un partage (mesuré, cifs à 20 ms : 8 fils 3,5 s, 16 : 1,5 s, 32 : 0,7 s)
ESSAIS_ESTIMATION = 3             # images mesurées avant d'annoncer une durée (question « gros dossier »)
ATTENTE_VERROU_S = 3.0            # ouverture du cache : au-delà, base verrouillée → cache local


# ============================================================================ dossier réseau
def est_reseau(chemin) -> bool:
    """Le dossier est-il sur un partage (lettre réseau ou UNC sous Windows, cifs/smb/nfs/sshfs ailleurs) ?

    Jamais d'exception : en cas de doute, False."""
    try:
        p = os.path.abspath(os.path.expanduser(str(chemin)))
        if os.name == 'nt':
            if p.startswith('\\\\'):
                return True
            import ctypes
            racine = os.path.splitdrive(p)[0] + '\\'
            return ctypes.windll.kernel32.GetDriveTypeW(racine) == 4          # DRIVE_REMOTE
        from ...core.chemins import TYPES_RESEAU, lire_montages
        if os.path.exists('/proc/mounts'):
            montages = [(point, typ) for point, typ, _src in lire_montages()]
        else:                                                               # macOS, BSD : sortie de `mount`
            montages = []
            import subprocess
            out = subprocess.run(['mount'], capture_output=True, text=True, timeout=5).stdout
            for ligne in out.splitlines():
                if ' on ' in ligne and ' (' in ligne:
                    point = ligne.split(' on ', 1)[1].split(' (', 1)[0]
                    typ = ligne.split(' (', 1)[1].split(',', 1)[0].strip(')')
                    montages.append((point, typ))
        meilleur = ''
        for point, typ in montages:
            if (p == point or p.startswith(point.rstrip('/') + '/')) and len(point) >= len(meilleur):
                meilleur, meilleur_type = point, typ
        return bool(meilleur) and meilleur_type.lower() in TYPES_RESEAU
    except Exception:
        return False


# ============================================================================ cache des mesures
class CacheMesures:
    """Une mesure par (chemin, taille, mtime), dans ``_traitement/qualite.sqlite`` (disque local) ou dans le
    dossier de cache de l'utilisateur (partage réseau, dossier en lecture seule, base verrouillée).  Jamais
    d'exception vers l'appelant : un cache illisible ou non inscriptible se comporte comme un cache vide.

    `reseau` : None = détecté (`est_reseau`)."""

    def __init__(self, racine, delai: float = 0.0, reseau: bool | None = None):
        self.racine = racine
        self.reseau = est_reseau(racine) if reseau is None else bool(reseau)
        self.db = None
        self.verrou = threading.Lock()
        self.delai = float(delai)            # > 0 : validations groupées (voir DELAI_VALIDATION)
        self._derniere = time.monotonic()
        self._en_attente = False
        self.chemin = self._chemin(racine, self.reseau)
        self.db = self._ouvrir(self.chemin)
        local = self._chemin_local(racine)
        if self.db is None and self.chemin != local:     # verrouillée (partage non détecté) : cache local
            self.chemin = local
            self.db = self._ouvrir(local)

    @staticmethod
    def _ouvrir(chemin):
        try:
            os.makedirs(os.path.dirname(chemin), exist_ok=True)
            db = sqlite3.connect(chemin, check_same_thread=False, timeout=ATTENTE_VERROU_S)
            db.execute('PRAGMA journal_mode=DELETE')
            db.execute('CREATE TABLE IF NOT EXISTS mesures (chemin TEXT PRIMARY KEY, taille INTEGER, mtime REAL, '
                       'mesure TEXT, maj TEXT)')
            db.commit()
            db.execute('PRAGMA busy_timeout=30000')      # ouverte : un autre écrivain local peut faire attendre
            return db
        except (sqlite3.Error, OSError):
            return None

    @staticmethod
    def _base(racine) -> Path:
        racine = Path(racine)
        return racine if racine.is_dir() else racine.parent

    @classmethod
    def _chemin_local(cls, racine) -> str:
        import hashlib
        base = cls._base(racine)
        return str(config.dossier_cache() / 'qualite' / (hashlib.sha1(str(base).encode()).hexdigest()[:16] + '.sqlite'))

    @classmethod
    def _chemin(cls, racine, reseau: bool = False) -> str:
        base = cls._base(racine)
        if not reseau and os.access(str(base), os.W_OK):
            return str(base / '_traitement' / 'qualite.sqlite')
        # partage réseau, dossier en lecture seule (DVD, partage protégé) : dossier de cache de l'utilisateur
        return cls._chemin_local(racine)

    def lire(self, chemin: str, taille: int, mtime: float):
        if self.db is None:
            return None
        try:
            with self.verrou:
                r = self.db.execute('SELECT taille, mtime, mesure FROM mesures WHERE chemin=?', (chemin,)).fetchone()
            if r and r[0] == taille and abs(r[1] - mtime) < 1e-3:
                return json.loads(r[2])
        except (sqlite3.Error, ValueError):
            pass
        return None

    def tout(self) -> dict:
        """{chemin: (taille, mtime, mesure en JSON)} en UNE requête (et non une par image) ; sur un partage, un
        ancien cache resté dans ``_traitement`` (écrit par une version précédente ou depuis le serveur) est
        relu en lecture seule et complété par le cache local."""
        out = {}
        if self.reseau:
            ancien = str(self._base(self.racine) / '_traitement' / 'qualite.sqlite')
            if ancien != self.chemin:
                try:
                    if os.path.getsize(ancien) > 0:
                        from ...core.chemins import uri_sqlite_lecture_seule
                        db = sqlite3.connect(uri_sqlite_lecture_seule(ancien), uri=True, timeout=1)
                        try:
                            out = {c: (t, m, j) for c, t, m, j in
                                   db.execute('SELECT chemin, taille, mtime, mesure FROM mesures')}
                        finally:
                            db.close()
                except (OSError, sqlite3.Error):
                    pass
        if self.db is None:
            return out
        try:
            with self.verrou:
                out.update({c: (t, m, j) for c, t, m, j in
                            self.db.execute('SELECT chemin, taille, mtime, mesure FROM mesures')})
        except sqlite3.Error:
            pass
        return out

    def ecrire(self, chemin: str, taille: int, mtime: float, mesure: dict):
        if self.db is None:
            return
        try:
            with self.verrou:
                self.db.execute('INSERT OR REPLACE INTO mesures VALUES (?,?,?,?,?)',
                                (chemin, taille, mtime, json.dumps(mesure, ensure_ascii=False, default=str),
                                 time.strftime('%Y-%m-%dT%H:%M:%S')))
                self._en_attente = True
                t = time.monotonic()
                if self.delai <= 0 or t - self._derniere >= self.delai:
                    self.db.commit()
                    self._derniere, self._en_attente = t, False
        except sqlite3.Error:
            pass

    def valider(self):
        if self.db is None or not self._en_attente:
            return
        try:
            with self.verrou:
                self.db.commit()
                self._derniere, self._en_attente = time.monotonic(), False
        except sqlite3.Error:
            pass

    def compte(self) -> int:
        if self.db is None:
            return 0
        try:
            with self.verrou:
                return int(self.db.execute('SELECT COUNT(*) FROM mesures').fetchone()[0])
        except sqlite3.Error:
            return 0

    def fermer(self):
        if self.db is not None:
            self.valider()
            try:
                with self.verrou:
                    self.db.close()
            except sqlite3.Error:
                pass
            self.db = None


# ============================================================================ inventaire
def sortie_coupole(racine, niveaux: int = 8) -> str | None:
    """Racine de la sortie Coupole qui contient `racine` (dossier où se trouve ``_traitement/etat.sqlite`` ou
    ``INDEX_LOTS.csv``, `racine` elle-même ou un parent), ou None.  Un ou deux tests d'existence par niveau."""
    p = os.path.abspath(str(racine))
    if os.path.isfile(p):
        p = os.path.dirname(p)
    for _ in range(niveaux):
        if os.path.isfile(os.path.join(p, '_traitement', 'etat.sqlite')) or \
                os.path.isfile(os.path.join(p, 'INDEX_LOTS.csv')):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return None


def _sous(chemin: str, racine: str) -> bool:
    return chemin == racine or chemin.startswith(racine.rstrip(os.sep) + os.sep)


def _decouper(chemin: str) -> list[str]:
    """Composants d'un chemin écrit sur une autre machine (séparateurs / ou \\)."""
    return [c for c in chemin.replace('\\', '/').split('/') if c]


def inventaire_base(racine, base: str) -> dict | None:
    """{dossier: [images triées]} des images converties (statut « ok ») de la base d'état de la sortie `base`,
    gardées sous `racine` ; None si la base est illisible ou ne donne rien sous `racine`.

    Les chemins de la base sont ceux de la machine qui a traité (``/workspace/…``, ``C:\\…``) : ils sont
    rapportés à `base` d'après la racine d'alors (dossier qui contenait ``_traitement``, lue dans le chemin
    ``staging`` ; à défaut, le plus long suffixe commun aux chemins)."""
    from ...core.chemins import uri_sqlite_lecture_seule
    chemin = os.path.join(base, '_traitement', 'etat.sqlite')
    finals, ancienne = [], collections.Counter()
    copie = None
    try:
        if est_reseau(base):
            # SQLite lit page par page (4 Ko, un aller-retour chacune sur un partage) : copie locale d'un bloc
            import shutil
            import tempfile
            copie = tempfile.mkdtemp(prefix='coupole-etat-')
            for suffixe in ('', '-wal'):
                if os.path.exists(chemin + suffixe):
                    shutil.copyfile(chemin + suffixe, os.path.join(copie, 'etat.sqlite' + suffixe))
            chemin = os.path.join(copie, 'etat.sqlite')
        db = sqlite3.connect(uri_sqlite_lecture_seule(chemin), uri=True, timeout=5)
        try:
            for (info,) in db.execute("SELECT info FROM images WHERE statut='ok'"):
                try:
                    d = json.loads(info or '{}')
                except ValueError:
                    continue
                f = d.get('final')
                if not f:
                    continue
                finals.append(f)
                st = d.get('staging') or ''
                parts = _decouper(st)
                if '_traitement' in parts:
                    ancienne[tuple(_decouper(st)[:parts.index('_traitement')])] += 1
        finally:
            db.close()
    except (sqlite3.Error, OSError):
        return None
    finally:
        if copie is not None:
            import shutil
            shutil.rmtree(copie, ignore_errors=True)
    if not finals:
        return None
    racine = os.path.abspath(str(racine))
    base = os.path.abspath(base)
    r0 = list(ancienne.most_common(1)[0][0]) if ancienne else None
    nom_base = os.path.basename(base)
    lots: dict[str, list] = {}
    for f in finals:
        parts = _decouper(f)
        if r0 is not None and parts[:len(r0)] == r0:
            local = os.path.join(base, *parts[len(r0):])
        elif _sous(os.path.abspath(f), base):
            local = os.path.abspath(f)
        elif nom_base in parts:                                     # sans « staging » : par le nom de la sortie
            k = len(parts) - 1 - parts[::-1].index(nom_base)
            local = os.path.join(base, *parts[k + 1:])
        else:
            continue
        if not local.lower().endswith(rapport.EXTENSIONS) or not _sous(local, racine):
            continue
        if '_traitement' in _decouper(os.path.relpath(local, base)):
            continue
        lots.setdefault(os.path.dirname(local), []).append(local)
    if not lots:
        return None
    return {d: sorted(v) for d, v in sorted(lots.items())}


def lots_index(racine, base: str) -> list[str] | None:
    """Dossiers des lots d'après ``INDEX_LOTS.csv`` de la sortie `base`, gardés sous `racine` ; None sans index."""
    chemin = os.path.join(base, 'INDEX_LOTS.csv')
    try:
        with open(chemin, 'rb') as f:                    # d'un bloc : une requête sur un partage, pas une par 8 Ko
            texte = f.read().decode('utf-8-sig')
        lignes = list(csv.DictReader(io.StringIO(texte, newline=''), delimiter=';'))
    except (OSError, csv.Error, UnicodeDecodeError):
        return None
    racine = os.path.abspath(str(racine))
    out = sorted({os.path.join(base, *_decouper(l.get('dossier') or '')) for l in lignes if l.get('dossier')})
    out = [d for d in out if _sous(d, racine)]
    return out or None


def inventorier(racine, a_dater, arret: threading.Event, fils: int = FILS_LISTE):
    """Producteur : génère ('source', nom), ('absentes', n) et (dossier, [images triées], {image: (taille, mtime)
    ou None}) au fur et à mesure.  `a_dater(images triées)` → celles dont on lit taille et date (un `stat` chacune, en
    parallèle).  Aucune image n'est ouverte."""
    from ...core import parcours
    racine = os.path.abspath(os.path.expanduser(str(racine)))
    if os.path.isfile(racine):
        yield ('source', 'fichier')
        try:
            st = os.stat(racine)
            dates = {racine: (int(st.st_size), float(st.st_mtime))}
        except OSError:
            dates = {racine: None}
        yield os.path.dirname(racine), [racine], dates
        return
    if not os.path.isdir(racine) or '_traitement' in Path(racine).parts:
        yield ('source', 'vide')
        return
    base = sortie_coupole(racine)
    lots, dossiers, source = None, None, ''
    if base:
        # INDEX_LOTS.csv d'abord (≈ 100 Ko lus d'un bloc) ; la base d'état (≈ 17 Mo, lue page par page par SQLite :
        # 2 s à 10 ms de latence) seulement sans index
        dossiers, source = lots_index(racine, base), 'index'
        if not dossiers:
            lots = inventaire_base(racine, base)
            dossiers, source = (list(lots) if lots else None), 'base'
    if dossiers:
        # Seuls les dossiers des lots sont lus, tous en même temps (pas de descente niveau par niveau), et la
        # taille et la date viennent de la liste du dossier : sur un partage cifs, un `stat` isolé est un
        # aller-retour, alors que juste après la liste il est servi par le cache d'attributs du client (mesuré :
        # 831 `stat` isolés 2,9 s à 10 ms de latence, contre 0,7 s pour tout lister).  Une image de la base
        # absente du disque n'apparaît simplement pas (comptée) ; une image ajoutée à la main dans un lot est vue.
        yield ('source', source)
        exclus = {'_traitement'}
        with F.ThreadPoolExecutor(fils, thread_name_prefix='parcours') as pool:
            futs = {pool.submit(parcours._lister_dossier, d, rapport.EXTENSIONS, exclus, a_dater) for d in dossiers}
            try:
                while futs:
                    if arret.is_set():
                        return
                    finis, futs = F.wait(futs, timeout=0.2, return_when=F.FIRST_COMPLETED)
                    for fut in finis:
                        d, fs, _sous_dossiers, dates = fut.result()
                        if lots:
                            absentes = len(set(lots[d]) - set(fs))
                            if absentes:
                                yield ('absentes', absentes)
                        if fs:
                            yield d, fs, dates
            finally:
                for fut in futs:
                    fut.cancel()
        return
    yield ('source', 'parcours')
    yield from parcours.parcourir(racine, rapport.EXTENSIONS, ('_traitement',), fils, arret, a_dater)


# ============================================================================ échantillon
def echantillon(images: list, n: int) -> list:
    """`n` images réparties dans le temps (les fichiers sont nommés par leur date : l'ordre trié est l'ordre
    chronologique) : la première, la dernière, le milieu, puis les quarts… ; toutes si n ≥ len(images)."""
    if n is None or n <= 0 or n >= len(images):
        return list(images)
    if n == 1:
        return [images[len(images) // 2]]
    idx = sorted({int(round(k * (len(images) - 1) / (n - 1))) for k in range(n)})
    return [images[i] for i in idx]


# ============================================================================ une image (processus)
def mesurer_une(chemin: str) -> dict:
    """Dans un processus de mesure : lecture (zstd), SEP, ajustements.  Ne lève jamais : une image illisible rend
    une ligne avec `erreur`."""
    from . import mesures
    t0 = time.perf_counter()
    try:
        a, ent = mesures.lire_image(chemin)
        t1 = time.perf_counter()
        r = mesures.analyser(a, ent)
        del a
        r['t_lecture'] = round(t1 - t0, 3)
    except Exception as e:                       # fichier abîmé, format inconnu : on le dit, on continue
        r = {'erreur': '%s: %s' % (type(e).__name__, str(e)[:200])}
    r['fichier'] = os.path.basename(chemin)
    r['chemin'] = chemin
    r['duree'] = round(time.perf_counter() - t0, 3)
    return r


def _initialiser_processus():
    try:
        from ...core import processus
        processus.confiner_descendance()
    except Exception:
        pass


# ============================================================================ plan
def processus_pour(plan: Plan | None, reseau: bool, maximum: int | None = None) -> int:
    """Nombre de processus de mesure : les conversions du plan machine (cœurs − 1, mémoire, mode économe, bridage
    manuel), limité à LECTEURS_RESEAU_MAX sur un partage (la lecture par le réseau est le goulot : des lecteurs en
    plus ne feraient que se gêner)."""
    if plan is None:
        from ...core import machine, parallele
        r = config.reglages()
        plan = parallele.planifier(machine.detecter(), conversions=int(r['conversions_max'] or 0),
                                   econome=bool(r['mode_econome']) or None)
    n = max(1, int(plan.conversions))
    if reseau:
        n = min(n, LECTEURS_RESEAU_MAX)
    if maximum:
        n = min(n, int(maximum))
    return n



# ============================================================================ le moteur
class Mesureur:
    """Mesure un dossier de lots.  `rapporter(ev)` reçoit les événements ; `arret` (threading.Event) annule tout de
    suite (inventaire interrompu, processus terminés, l'image en cours abandonnée, les mesures faites restent au
    cache).

    Choix de l'échantillon :
      * `echantillon_par_lot` = n : n images par lot, seulement ;
      * `demander` : gros dossier (> SEUIL_GROS_DOSSIER images, des images hors échantillon à mesurer) → événement
        « question » quand l'inventaire est fini, réponse par `decider('tout' | 'echantillon')` ; en attendant,
        les images de l'échantillon (`n_echantillon` par lot) sont mesurées d'abord — elles le seront de toute
        façon : rien n'est perdu, et la durée annoncée vient des images déjà mesurées ;
      * `auto` : même ordre, et l'échantillon est choisi d'office pour un gros dossier (ligne de commande,
        contrôle après traitement) ;
      * sinon : tout."""

    def __init__(self, racine, plan: Plan | None = None, echantillon_par_lot: int | None = None, rapporter=None,
                 arret: threading.Event | None = None, ecrire_rapports: bool = True, processus_max: int | None = None,
                 langue: str | None = None, demander: bool = False, auto: bool = False,
                 n_echantillon: int = ECHANTILLON_DEFAUT):
        self.racine = os.path.abspath(os.path.expanduser(str(racine)))
        self.plan = plan
        self.echantillon = echantillon_par_lot or None
        self.rapporter = rapporter or (lambda ev: None)
        self.arret = arret or threading.Event()
        self.ecrire_rapports = ecrire_rapports
        self.processus_max = processus_max
        self.langue = langue
        self.demander = bool(demander) and not self.echantillon
        self.auto = bool(auto) and not self.echantillon and not self.demander
        self.n_echantillon = int(n_echantillon or ECHANTILLON_DEFAUT)
        self.cache = None
        self._ecrit_le = {}
        self._decision = queue.Queue()
        self.source = ''

    def decider(self, choix: str):
        """Réponse à la question « gros dossier » : 'tout' ou 'echantillon' (annuler : lever `arret`)."""
        self._decision.put(choix)

    # ---------------------------------------------------------------- utilitaires
    def _ecrire_lot(self, dossier, lignes, final: bool, force: bool = False):
        """QUALITE.csv du lot : à la fin du lot, et en cours de lot au plus toutes les ECRITURE_CSV_S secondes
        (le réécrire après CHAQUE image coûtait O(n²) octets par lot et, sur un partage, plusieurs allers-retours
        par image ; chaque mesure est de toute façon gardée au cache dès qu'elle arrive)."""
        if not self.ecrire_rapports:
            return
        t = time.monotonic()
        if not (final or force) and t - self._ecrit_le.get(dossier, 0.0) < ECRITURE_CSV_S:
            return
        self._ecrit_le[dossier] = t
        try:
            rapport.ecrire(dossier, lignes, txt=final)
        except OSError:
            pass

    @staticmethod
    def _terminer(pool):
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
        pool.shutdown(wait=False, cancel_futures=True)

    def _produire(self, file_inv: queue.Queue, a_dater, reseau: bool = False):
        try:
            for x in inventorier(self.racine, a_dater, self.arret, FILS_LISTE_RESEAU if reseau else FILS_LISTE):
                file_inv.put(x)
                if self.arret.is_set():
                    break
        except Exception as e:                       # jamais d'inventaire bloqué : l'erreur est rendue, la fin aussi
            file_inv.put(('erreur', '%s: %s' % (type(e).__name__, e)))
        file_inv.put(None)

    # ---------------------------------------------------------------- lancement
    def lancer(self) -> dict:
        t0 = time.monotonic()
        reseau = est_reseau(self.racine)
        self.cache = CacheMesures(self.racine, DELAI_VALIDATION, reseau=reseau)
        connus = self.cache.tout()                   # une requête, en mémoire : aucune requête par image
        n_proc = processus_pour(self.plan, reseau, self.processus_max)
        n_ech = self.echantillon or self.n_echantillon
        decision = 'echantillon' if self.echantillon else ('tout' if not (self.demander or self.auto) else None)

        def a_dater(fs):                             # mode échantillon : seules les images retenues sont datées
            return echantillon(fs, n_ech) if decision == 'echantillon' else fs

        file_inv: queue.Queue = queue.Queue()
        producteur = threading.Thread(target=self._produire, args=(file_inv, a_dater, reseau), daemon=True,
                                      name='inventaire-qualite')
        producteur.start()

        lots: dict[str, list] = {}                   # dossier → images (toutes, triées)
        ech_de: dict[str, set] = {}                  # dossier → indices de l'échantillon
        resultats: dict[str, dict] = {}              # dossier → {indice: ligne}
        attendus: dict[str, set] = {}                # dossier → indices encore attendus pour clore le lot
        clos: set = set()
        prio = collections.deque()                   # (dossier, indice, chemin, taille, mtime) à mesurer d'abord
        differe = collections.deque()                # hors échantillon, en attente de la décision
        en_cours = {}
        st = {'fait': 0, 'deja': 0, 'mesurees': 0, 'echecs': 0, 'absentes': 0, 'trouves': 0, 'duree_mesures': 0.0}
        inventaire_fini = False
        question_posee = debut_envoye = False
        annule = False
        pool = None
        fenetre = 2 * n_proc                         # lectures recouvertes : toujours une image d'avance par processus
        t_mesure = None
        derniere = derniere_inv = 0.0
        erreur_inventaire = None

        def rapporter_image(d, i, r, deja):
            resultats[d][i] = r
            attendus[d].discard(i)
            st['fait'] += 1
            self.rapporter({'type': 'image', 'lot': d, 'ligne': r, 'deja': deja})

        def lignes_de(d):
            return [resultats[d][i] for i in sorted(resultats[d])]

        def clore_si_fini(d):
            if d in clos or attendus[d] or decision is None:
                return
            clos.add(d)
            if resultats[d]:
                self._ecrire_lot(d, lignes_de(d), final=True)
                self.rapporter({'type': 'lot', 'lot': d, 'lignes': lignes_de(d)})

        def accueillir(d, fs, dates):
            lots[d] = fs
            resultats[d] = {}
            ech = echantillon(list(range(len(fs))), n_ech)
            ech_de[d] = set(ech)
            st['trouves'] += len(fs)
            vus = ech if decision == 'echantillon' else ech + [i for i in range(len(fs)) if i not in ech_de[d]]
            attendus[d] = set(vus)
            for i in vus:
                f = fs[i]
                e = dates.get(f) if dates else None
                if e is None:
                    rapporter_image(d, i, {'fichier': os.path.basename(f), 'chemin': f, 'erreur': 'unreadable (stat)'},
                                    False)
                    st['echecs'] += 1
                    continue
                taille, mtime = e
                c = connus.get(f)
                r = None
                if c is not None and c[0] == taille and abs(c[1] - mtime) < 1e-3:
                    try:
                        r = json.loads(c[2])
                    except ValueError:
                        r = None
                if r is not None:
                    st['deja'] += 1
                    rapporter_image(d, i, r, True)
                elif decision is None and i not in ech_de[d]:
                    differe.append((d, i, f, taille, mtime))
                else:
                    prio.append((d, i, f, taille, mtime))
            clore_si_fini(d)

        def total():
            return st['fait'] + len(prio) + len(en_cours) + (len(differe) if decision != 'echantillon' else 0)

        def appliquer(choix):
            nonlocal decision
            decision = 'echantillon' if choix == 'echantillon' else 'tout'
            if decision == 'tout':
                prio.extend(differe)
            else:
                for d in lots:                         # hors échantillon : plus attendu (le cache déjà lu reste)
                    attendus[d] = {i for i in attendus[d] if i in ech_de[d]}
            differe.clear()
            for d in list(lots):
                clore_si_fini(d)

        def envoyer_debut():
            nonlocal debut_envoye
            debut_envoye = True
            self.rapporter({'type': 'debut', 'total': total(), 'deja': st['deja'], 'processus': n_proc,
                            'reseau': reseau, 'echantillon': n_ech if decision == 'echantillon' else 0,
                            'lots': len(lots), 'total_dossier': st['trouves'], 'source': self.source,
                            'absentes': st['absentes']})

        try:
            while True:
                if self.arret.is_set():
                    annule = True
                    break
                # 1) inventaire : tout ce qui est arrivé, sans attendre
                while not inventaire_fini:
                    try:
                        x = file_inv.get_nowait() if (prio or en_cours or differe) else file_inv.get(timeout=0.05)
                    except queue.Empty:
                        break
                    if x is None:
                        inventaire_fini = True
                        self.rapporter({'type': 'inventaire', 'trouves': st['trouves'], 'lots': len(lots), 'fini': True,
                                        'source': self.source, 'mesurees': st['mesurees'], 'fait': st['fait']})
                    elif x[0] == 'source':
                        self.source = x[1]
                    elif x[0] == 'erreur':
                        erreur_inventaire = x[1]
                    elif x[0] == 'absentes':
                        st['absentes'] += x[1]
                    else:
                        accueillir(*x)
                maintenant = time.monotonic()
                if not inventaire_fini and maintenant - derniere_inv >= CADENCE_PROGRESSION:
                    derniere_inv = maintenant
                    self.rapporter({'type': 'inventaire', 'trouves': st['trouves'], 'lots': len(lots), 'fini': False,
                                    'source': self.source, 'mesurees': st['mesurees'], 'fait': st['fait']})
                # 2) décision (gros dossier) quand l'inventaire est fini
                if inventaire_fini and decision is None:
                    if st['trouves'] <= SEUIL_GROS_DOSSIER or not differe:
                        appliquer('tout')
                    elif self.auto:
                        appliquer('echantillon')
                        self.rapporter({'type': 'decision', 'decision': 'echantillon', 'total_dossier': st['trouves'],
                                        'n': n_ech})
                    elif not question_posee:
                        if st['mesurees'] < ESSAIS_ESTIMATION and not prio and not en_cours:
                            for _ in range(min(ESSAIS_ESTIMATION - st['mesurees'], len(differe))):
                                prio.append(differe.popleft())       # quelques images pour chronométrer
                        if st['mesurees'] >= ESSAIS_ESTIMATION or (not prio and not en_cours):
                            question_posee = True
                            par_image = st['duree_mesures'] / st['mesurees'] if st['mesurees'] else 0.0
                            reste_ech = len(prio) + len(en_cours)
                            reste = reste_ech + len(differe)
                            self.rapporter({'type': 'question', 'total_dossier': st['trouves'], 'lots': len(lots),
                                            'a_mesurer': reste, 'a_mesurer_echantillon': reste_ech,
                                            'par_image_s': par_image, 'duree_s': reste * par_image / n_proc,
                                            'duree_echantillon_s': reste_ech * par_image / n_proc,
                                            'processus': n_proc, 'reseau': reseau, 'n': n_ech, 'deja': st['deja']})
                    else:
                        try:
                            appliquer(self._decision.get_nowait())
                        except queue.Empty:
                            pass
                if inventaire_fini and decision is not None and not debut_envoye:
                    envoyer_debut()
                # 3) mesures
                if prio and pool is None:
                    ctx = mp.get_context('spawn')
                    pool = F.ProcessPoolExecutor(n_proc, mp_context=ctx, initializer=_initialiser_processus)
                    t_mesure = time.monotonic()
                while prio and len(en_cours) < fenetre:
                    d, i, f, taille, mtime = prio.popleft()
                    en_cours[pool.submit(mesurer_une, f)] = (d, i, f, taille, mtime)
                if en_cours:
                    finis, _ = F.wait(list(en_cours), timeout=0.1, return_when=F.FIRST_COMPLETED)
                    for fut in finis:
                        d, i, f, taille, mtime = en_cours.pop(fut)
                        try:
                            r = fut.result()
                        except Exception as e:            # processus mort (OOM) : l'image est en échec, on continue
                            r = {'fichier': os.path.basename(f), 'chemin': f, 'erreur': '%s: %s' % (type(e).__name__, e)}
                        if 'erreur' in r:
                            st['echecs'] += 1
                        else:
                            self.cache.ecrire(f, taille, mtime, r)
                        st['mesurees'] += 1
                        st['duree_mesures'] += float(r.get('duree') or 0.0)
                        rapporter_image(d, i, r, False)
                        if not attendus[d]:
                            clore_si_fini(d)
                        else:
                            self._ecrire_lot(d, lignes_de(d), final=False)
                elif inventaire_fini and decision is None and question_posee:
                    time.sleep(0.05)                      # on attend la réponse (l'arrêt reste immédiat)
                maintenant = time.monotonic()
                fini = inventaire_fini and decision is not None and not prio and not en_cours and not differe
                if maintenant - derniere >= CADENCE_PROGRESSION or fini:
                    derniere = maintenant
                    m = st['mesurees']
                    ecoule = maintenant - t_mesure if t_mesure is not None else 0.0
                    a_mesurer = m + len(prio) + len(en_cours) + (len(differe) if decision != 'echantillon' else 0)
                    debit = m / ecoule * 60 if ecoule > 0 and m else 0.0
                    eta = (a_mesurer - m) * ecoule / m if m and inventaire_fini else None
                    self.rapporter({'type': 'progression', 'fait': st['fait'], 'total': total(), 'eta_s': eta,
                                    'debit': debit, 'mesurees': m, 'a_mesurer': a_mesurer,
                                    'inventaire_fini': inventaire_fini, 'trouves': st['trouves']})
                if fini:
                    break
        finally:
            if pool is not None:
                if annule or en_cours:
                    self._terminer(pool)
                else:
                    pool.shutdown(wait=True)
            self.cache.fermer()
        for d in lots:                               # lots interrompus : leur QUALITE.csv contient tout ce qui est fait
            if d not in clos and resultats[d]:
                self._ecrire_lot(d, lignes_de(d), final=False, force=True)
        bilan = {'type': 'fin', 'n': st['fait'], 'mesurees': st['mesurees'], 'deja': st['deja'], 'lots': len(lots),
                 'echecs': st['echecs'], 'absentes': st['absentes'], 'duree': time.monotonic() - t0, 'annule': annule,
                 'processus': n_proc, 'reseau': reseau, 'source': self.source, 'total_dossier': st['trouves'],
                 'echantillon': n_ech if decision == 'echantillon' else 0, 'erreur_inventaire': erreur_inventaire,
                 'lignes': {d: lignes_de(d) for d in lots}}
        self.rapporter(bilan)
        return bilan
