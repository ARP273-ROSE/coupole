"""Moteur de mesure : processus parallèles, cache des mesures, échantillon par lot, reprise, annulation, ETA.

Sans Qt.  L'interface et la ligne de commande lui passent une fonction `rapporter(événement)` :

  {'type': 'debut', 'total', 'deja', 'processus', 'reseau', 'echantillon', 'lots'}
  {'type': 'image', 'lot', 'ligne', 'deja'}                  une image mesurée (ou relue du cache)
  {'type': 'progression', 'fait', 'total', 'eta_s', 'debit'} agrégée, au plus 10 fois par seconde
  {'type': 'lot', 'lot', 'lignes'}                           un lot terminé (QUALITE.csv et QUALITE.txt écrits)
  {'type': 'fin', 'n', 'lots', 'duree', 'annule', 'echecs'}

Le travail lourd (lecture + décompression zstd, SEP, ajustement des étoiles) tourne dans des processus séparés
(`multiprocessing` en mode spawn, comme le pilote de la Banque OHP) dimensionnés par le plan machine ; la lecture
d'une image recouvre le calcul des autres.  Chaque image mesurée est écrite aussitôt dans le QUALITE.csv de son lot
(écriture atomique) et mise en cache dans ``<racine>/_traitement/qualite.sqlite`` par (chemin, taille, mtime) :
relancer ne refait pas ce qui est déjà mesuré, fermer puis rouvrir reprend.
"""
from __future__ import annotations

import concurrent.futures as F
import json
import multiprocessing as mp
import os
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
CADENCE_PROGRESSION = 0.1         # secondes entre deux événements « progression » (10 Hz)


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
        types_reseau = ('cifs', 'smb3', 'smbfs', 'nfs', 'nfs4', 'fuse.sshfs', 'sshfs', 'afpfs', 'webdav', 'davfs',
                        'fuse.rclone', '9p')
        montages = []
        if os.path.exists('/proc/mounts'):
            with open('/proc/mounts', encoding='utf-8', errors='replace') as f:
                for ligne in f:
                    morceaux = ligne.split()
                    if len(morceaux) >= 3:
                        montages.append((morceaux[1].replace('\\040', ' '), morceaux[2]))
        else:                                                               # macOS, BSD : sortie de `mount`
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
        return bool(meilleur) and meilleur_type.lower() in types_reseau
    except Exception:
        return False


# ============================================================================ cache des mesures
class CacheMesures:
    """``_traitement/qualite.sqlite`` : une mesure par (chemin, taille, mtime).  Jamais d'exception vers l'appelant :
    un cache illisible ou non inscriptible se comporte comme un cache vide."""

    def __init__(self, racine):
        self.chemin = self._chemin(racine)
        self.db = None
        self.verrou = threading.Lock()
        try:
            os.makedirs(os.path.dirname(self.chemin), exist_ok=True)
            self.db = sqlite3.connect(self.chemin, check_same_thread=False, timeout=30)
            self.db.execute('PRAGMA journal_mode=DELETE')
            self.db.execute('CREATE TABLE IF NOT EXISTS mesures (chemin TEXT PRIMARY KEY, taille INTEGER, mtime REAL, '
                            'mesure TEXT, maj TEXT)')
            self.db.commit()
        except (sqlite3.Error, OSError):
            self.db = None

    @staticmethod
    def _chemin(racine) -> str:
        racine = Path(racine)
        base = racine if racine.is_dir() else racine.parent
        if os.access(str(base), os.W_OK):
            return str(base / '_traitement' / 'qualite.sqlite')
        # dossier en lecture seule (DVD, partage protégé) : cache dans le dossier de cache de l'utilisateur
        import hashlib
        return str(config.dossier_cache() / 'qualite' / (hashlib.sha1(str(base).encode()).hexdigest()[:16] + '.sqlite'))

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

    def ecrire(self, chemin: str, taille: int, mtime: float, mesure: dict):
        if self.db is None:
            return
        try:
            with self.verrou:
                self.db.execute('INSERT OR REPLACE INTO mesures VALUES (?,?,?,?,?)',
                                (chemin, taille, mtime, json.dumps(mesure, ensure_ascii=False, default=str),
                                 time.strftime('%Y-%m-%dT%H:%M:%S')))
                self.db.commit()
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
            try:
                with self.verrou:
                    self.db.close()
            except sqlite3.Error:
                pass
            self.db = None


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
def _empreinte(chemin: str):
    st = os.stat(chemin)
    return int(st.st_size), float(st.st_mtime)


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


# ============================================================================ plan et estimation
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


def planifier(racine, echantillon_par_lot: int | None) -> dict:
    """Inventaire du dossier en une passe (os.walk unique) et ce qu'il reste à mesurer.

    Rend {'lots': {dossier: [images retenues]}, 'total_dossier', 'a_mesurer', 'deja', 'reseau', 'echantillon'}.
    `echantillon_par_lot` : None ou 0 = tout ; n = n images par lot."""
    lots = rapport.fichiers(racine)
    total = sum(len(v) for v in lots.values())
    retenus = {d: echantillon(v, echantillon_par_lot) for d, v in lots.items()}
    cache = CacheMesures(racine)
    deja = 0
    try:
        for d, imgs in retenus.items():
            for f in imgs:
                try:
                    taille, mtime = _empreinte(f)
                except OSError:
                    continue
                if cache.lire(f, taille, mtime) is not None:
                    deja += 1
    finally:
        cache.fermer()
    n_retenus = sum(len(v) for v in retenus.values())
    return {'lots': retenus, 'total_dossier': total, 'retenus': n_retenus, 'a_mesurer': n_retenus - deja, 'deja': deja,
            'reseau': est_reseau(racine), 'echantillon': echantillon_par_lot or 0}


def estimer_duree(plan_: dict, processus: int, n_essai: int = 3) -> dict:
    """Temps par image mesuré sur les `n_essai` premières images à faire (dans ce processus, une après l'autre),
    puis durée totale estimée avec `processus` en parallèle.  Les images d'essai vont au cache : rien n'est perdu."""
    cache = CacheMesures(plan_['chemin']) if 'chemin' in plan_ else None
    essais = []
    t_total = 0.0
    for f in (f for imgs in plan_['lots'].values() for f in imgs):
        if len(essais) >= max(1, n_essai):
            break
        try:
            taille, mtime = _empreinte(f)
        except OSError:
            continue
        if cache is not None and cache.lire(f, taille, mtime) is not None:
            continue                                 # déjà mesurée : on chronomètre une image qui reste à faire
        r = mesurer_une(f)
        if cache is not None and 'erreur' not in r:
            cache.ecrire(f, taille, mtime, r)
        essais.append(r['duree'])
        t_total += r['duree']
    if cache is not None:
        cache.fermer()
    par_image = (t_total / len(essais)) if essais else 0.0
    reste = max(0, plan_['a_mesurer'] - len(essais))
    return {'par_image_s': par_image, 'essais': len(essais),
            'duree_s': reste * par_image / max(1, processus), 'processus': processus}


# ============================================================================ le moteur
class Mesureur:
    """Mesure un dossier de lots.  `rapporter(ev)` reçoit les événements ; `arret` (threading.Event) annule tout de
    suite (processus terminés, l'image en cours abandonnée, les mesures faites restent au cache)."""

    def __init__(self, racine, plan: Plan | None = None, echantillon_par_lot: int | None = None, rapporter=None,
                 arret: threading.Event | None = None, ecrire_rapports: bool = True, processus_max: int | None = None,
                 langue: str | None = None):
        self.racine = os.path.abspath(os.path.expanduser(str(racine)))
        self.plan = plan
        self.echantillon = echantillon_par_lot
        self.rapporter = rapporter or (lambda ev: None)
        self.arret = arret or threading.Event()
        self.ecrire_rapports = ecrire_rapports
        self.processus_max = processus_max
        self.langue = langue
        self.cache = None

    # ---------------------------------------------------------------- utilitaires
    def _ecrire_lot(self, dossier, lignes, final: bool):
        if not self.ecrire_rapports:
            return
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

    # ---------------------------------------------------------------- lancement
    def lancer(self) -> dict:
        t0 = time.monotonic()
        plan_ = planifier(self.racine, self.echantillon)
        lots = plan_['lots']
        n_proc = processus_pour(self.plan, plan_['reseau'], self.processus_max)
        self.cache = CacheMesures(self.racine)
        total = plan_['retenus']
        self.rapporter({'type': 'debut', 'total': total, 'deja': plan_['deja'], 'processus': n_proc,
                        'reseau': plan_['reseau'], 'echantillon': plan_['echantillon'], 'lots': len(lots),
                        'total_dossier': plan_['total_dossier']})
        resultats = {d: [None] * len(imgs) for d, imgs in lots.items()}
        restant = {d: len(imgs) for d, imgs in lots.items()}
        file_ = []                                   # (dossier, indice, chemin, taille, mtime)
        fait = 0
        deja = 0
        echecs = 0
        # 1) ce que le cache connaît déjà : affiché tout de suite
        for d, imgs in lots.items():
            for i, f in enumerate(imgs):
                try:
                    taille, mtime = _empreinte(f)
                except OSError as e:
                    resultats[d][i] = {'fichier': os.path.basename(f), 'chemin': f, 'erreur': str(e)[:200]}
                    restant[d] -= 1
                    fait += 1
                    echecs += 1
                    continue
                r = self.cache.lire(f, taille, mtime)
                if r is not None:
                    resultats[d][i] = r
                    restant[d] -= 1
                    fait += 1
                    deja += 1
                    self.rapporter({'type': 'image', 'lot': d, 'ligne': r, 'deja': True})
                else:
                    file_.append((d, i, f, taille, mtime))
        for d in list(lots):
            if restant[d] == 0 and lots[d]:
                self._ecrire_lot(d, resultats[d], final=True)
                self.rapporter({'type': 'lot', 'lot': d, 'lignes': resultats[d]})
        a_mesurer = len(file_)
        annule = False
        derniere_progression = 0.0
        t_mesure = time.monotonic()
        mesurees = 0
        if file_ and not self.arret.is_set():
            ctx = mp.get_context('spawn')
            pool = F.ProcessPoolExecutor(n_proc, mp_context=ctx, initializer=_initialiser_processus)
            en_cours = {}
            fenetre = 2 * n_proc                     # lectures recouvertes : toujours une image d'avance par processus
            try:
                while (file_ or en_cours) and not self.arret.is_set():
                    while file_ and len(en_cours) < fenetre:
                        d, i, f, taille, mtime = file_.pop(0)
                        en_cours[pool.submit(mesurer_une, f)] = (d, i, f, taille, mtime)
                    finis, _ = F.wait(list(en_cours), timeout=0.2, return_when=F.FIRST_COMPLETED)
                    for fut in finis:
                        d, i, f, taille, mtime = en_cours.pop(fut)
                        try:
                            r = fut.result()
                        except Exception as e:            # processus mort (OOM) : l'image est en échec, on continue
                            r = {'fichier': os.path.basename(f), 'chemin': f, 'erreur': '%s: %s' % (type(e).__name__, e)}
                        if 'erreur' in r:
                            echecs += 1
                        else:
                            self.cache.ecrire(f, taille, mtime, r)
                        resultats[d][i] = r
                        restant[d] -= 1
                        fait += 1
                        mesurees += 1
                        self.rapporter({'type': 'image', 'lot': d, 'ligne': r, 'deja': False})
                        self._ecrire_lot(d, [x for x in resultats[d] if x is not None], final=restant[d] == 0)
                        if restant[d] == 0:
                            self.rapporter({'type': 'lot', 'lot': d, 'lignes': resultats[d]})
                    maintenant = time.monotonic()
                    if maintenant - derniere_progression >= CADENCE_PROGRESSION or fait >= total:
                        derniere_progression = maintenant
                        ecoule = maintenant - t_mesure
                        debit = mesurees / ecoule * 60 if ecoule > 0 and mesurees else 0.0
                        eta = (a_mesurer - mesurees) * ecoule / mesurees if mesurees else None
                        self.rapporter({'type': 'progression', 'fait': fait, 'total': total, 'eta_s': eta,
                                        'debit': debit, 'mesurees': mesurees, 'a_mesurer': a_mesurer})
                annule = self.arret.is_set() and (bool(file_) or bool(en_cours))
            finally:
                if annule:
                    self._terminer(pool)
                else:
                    pool.shutdown(wait=True)
        self.cache.fermer()
        bilan = {'type': 'fin', 'n': fait, 'mesurees': mesurees, 'deja': deja, 'lots': len(lots), 'echecs': echecs,
                 'duree': time.monotonic() - t0, 'annule': annule, 'processus': n_proc, 'reseau': plan_['reseau'],
                 'lignes': {d: [x for x in v if x is not None] for d, v in resultats.items()}}
        self.rapporter(bilan)
        return bilan
