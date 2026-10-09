"""Base SQLite d'un dossier qui peut être sur un partage réseau : base de travail locale, recopiée sur le partage.

Pourquoi : sous Linux, le client cifs du noyau transmet les verrous de SQLite (``fcntl``) au serveur comme verrous
de plage SMB, et l'écriture échoue (« database is locked » au bout du délai d'attente, fichier de 0 octet) sur un
partage monté avec les options par défaut — mesuré sur un vrai Samba (``docs/AUDIT2_2026-10.md`` § 9 et § 10).
La lecture seule (``mode=ro``) et la copie de fichier, elles, fonctionnent.  macOS (smbfs) et Windows (UNC, lecteur
réseau) passent par le même chemin : aucun verrou réseau n'est jamais demandé, quel que soit le client.

Principe (une base de travail par base du partage, clé = chemin normalisé) :

* la base de travail est dans le dossier de cache de l'utilisateur ; elle est créée par **copie de fichier** de la
  base du partage (plus son ``-journal`` éventuel : SQLite annule localement une transaction interrompue) ;
* elle est **recopiée sur le partage** par copie atomique : instantané cohérent (API de sauvegarde de SQLite) dans un
  fichier local, ``PRAGMA integrity_check`` sur cet instantané, copie dans un fichier temporaire **du même dossier
  du partage**, relecture d'un bloc et comparaison de l'empreinte SHA-256, puis ``os.replace`` ; jamais de fichier
  à moitié écrit, jamais de verrou posé sur le partage (donc jamais de verrou orphelin) ;
* un fichier d'accompagnement (``.sync.json``) note l'état du partage après chaque synchronisation (date, taille,
  empreinte, compteur de version ``meta.version_partage``) et l'empreinte de la base de travail ;
* à l'ouverture : partage inchangé et base de travail inchangée → rien ; partage plus récent → recopié (réuni à la
  base de travail si elle a des images qu'il n'a plus : une recopie remplacée par un autre écrivain) ; base de
  travail modifiée et non recopiée (plantage, coupure) → recopiée sur le partage ; **les deux modifiées** (deux
  écrivains) → rien n'est écrasé, :class:`Divergence` est levée et :func:`fusionner` propose l'union.

Fusion (:func:`fusionner`) : par identifiant d'image, le statut le plus avancé gagne (ok > doublon > echec >
en_cours) ; à égalité, la ligne la plus récente ; essais = le maximum ; empreintes de pixels : union.  Les deux bases
d'origine sont gardées à côté de la base de travail (``etat.sqlite.local-<date>``, ``etat.sqlite.partage-<date>``).
"""
from __future__ import annotations

import datetime as D
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import threading
import time
from pathlib import Path

from . import config
from .chemins import est_reseau, uri_sqlite_lecture_seule

INTERVALLE_S = 30.0                 # recopie sur le partage pendant un traitement
ATTENTE_VERROU_S = 3.0              # dossier non reconnu comme partage : au-delà, base verrouillée → base locale
ESSAIS_REMPLACEMENT = 5             # os.replace refusé (Windows : fichier ouvert ailleurs) : nouvel essai
CLE_VERSION = 'version_partage'
RANG = {'ok': 4, 'doublon': 3, 'echec': 2, 'en_cours': 1}


class Divergence(Exception):
    """La base du partage et la base de travail locale ont été modifiées chacune de leur côté."""

    def __init__(self, partage: str, locale: str, copie_partage: str):
        self.partage, self.locale, self.copie_partage = partage, locale, copie_partage
        super().__init__('divergence: %s / %s' % (partage, locale))


# ============================================================================ outils
def empreinte(chemin) -> str:
    """SHA-256 du fichier (lu par blocs de 1 Mo : sur un partage, une requête par Mo et non par page) ; '' si
    absent."""
    h = hashlib.sha256()
    try:
        with open(chemin, 'rb') as f:
            for bloc in iter(lambda: f.read(1 << 20), b''):
                h.update(bloc)
    except OSError:
        return ''
    return h.hexdigest()


def _stat(chemin):
    try:
        s = os.stat(chemin)
        return [int(s.st_mtime_ns), int(s.st_size)]
    except OSError:
        return [0, 0]


def integre(chemin) -> bool:
    """``PRAGMA integrity_check`` = ok (base locale, lecture seule)."""
    try:
        db = sqlite3.connect(uri_sqlite_lecture_seule(chemin), uri=True, timeout=5)
        try:
            return db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        finally:
            db.close()
    except sqlite3.Error:
        return False


def _version(chemin) -> int:
    try:
        db = sqlite3.connect(uri_sqlite_lecture_seule(chemin), uri=True, timeout=5)
        try:
            r = db.execute('SELECT valeur FROM meta WHERE cle=?', (CLE_VERSION,)).fetchone()
            return int(r[0]) if r else 0
        finally:
            db.close()
    except (sqlite3.Error, ValueError, TypeError):
        return 0


def _horodatage() -> str:
    return D.datetime.now().strftime('%Y%m%d-%H%M%S')


def cle(chemin_partage) -> str:
    """Clé de la base de travail : chemin absolu normalisé (casse ignorée sous Windows et macOS)."""
    p = os.path.normpath(os.path.abspath(os.path.expanduser(str(chemin_partage))))
    if os.name == 'nt' or sys.platform == 'darwin':
        p = p.lower()
    return hashlib.sha1(p.encode('utf-8', 'surrogatepass')).hexdigest()[:16]


def dossier_travail(chemin_partage) -> Path:
    return config.dossier_cache() / 'bases' / cle(chemin_partage)


def chemin_travail(chemin_partage) -> str:
    return str(dossier_travail(chemin_partage) / os.path.basename(str(chemin_partage)))


def _copier_base(src, dst):
    """Copie de fichier (et du ``-journal`` éventuel, que SQLite rejouera localement) vers `dst` ; la copie est
    ouverte une fois (annulation du journal), vérifiée, puis mise en place.  OSError / ValueError si illisible."""
    tmp = dst + '.arrivee'
    for suffixe in ('', '-journal'):
        try:
            os.remove(tmp + suffixe)
        except OSError:
            pass
    try:
        shutil.copyfile(src, tmp)
        j = src + '-journal'
        if os.path.isfile(j) and os.path.getsize(j) > 0:
            shutil.copyfile(j, tmp + '-journal')
        if os.path.getsize(tmp) > 0:
            db = sqlite3.connect(tmp, timeout=5)        # rejoue (annule) un journal chaud
            try:
                db.execute('SELECT count(*) FROM sqlite_master').fetchone()
            finally:
                db.close()
            if not integre(tmp):
                raise ValueError('integrity_check: %s' % src)
        os.replace(tmp, dst)
    finally:
        for suffixe in ('', '-journal'):
            try:
                os.remove(tmp + suffixe)
            except OSError:
                pass


# ============================================================================ base partagée
class BasePartagee:
    """Une base SQLite `chemin` (dans le dossier de sortie).  `ouvrir()` rend le chemin à ouvrir en écriture : la
    base elle-même (disque local), ou la base de travail locale (partage réseau, base verrouillée).

    `reseau` : None = détecté.  `rapporter(cle, **valeurs)` : messages pour le journal et l'interface.
    """

    def __init__(self, chemin, reseau: bool | None = None, intervalle: float = INTERVALLE_S, rapporter=None):
        self.partage = os.path.abspath(str(chemin))
        self.reseau = est_reseau(os.path.dirname(self.partage)) if reseau is None else bool(reseau)
        self.intervalle = float(intervalle)
        self.rapporter = rapporter or (lambda cle, **v: None)
        self.locale = chemin_travail(self.partage)
        self.sync = self.locale + '.sync.json'
        self.mode = 'direct'
        self._derniere = time.monotonic()
        self._fil: threading.Thread | None = None
        self._verrou = threading.Lock()
        self.erreur_envoi: str | None = None
        self.divergence = False

    # ------------------------------------------------------------------ ouverture
    def ouvrir(self) -> str:
        """Chemin à ouvrir.  Lève :class:`Divergence` (rien n'est écrasé) si les deux bases ont changé."""
        if not self.reseau and self._direct_possible():
            self.mode = 'direct'
            return self.partage
        self.mode = 'local'
        os.makedirs(os.path.dirname(self.locale), exist_ok=True)
        try:
            self._preparer()
        except (sqlite3.DatabaseError, ValueError) as e:     # base du partage abîmée : rien n'est écrasé
            raise OSError('%s: %s' % (self.partage, e)) from e
        self.rapporter('base_locale_avis', dest=os.path.dirname(os.path.dirname(self.partage)),
                       secondes=int(self.intervalle))
        return self.locale

    def _direct_possible(self) -> bool:
        """Disque local : SQLite écrit-il ici ?  Essai court (3 s) ; « database is locked » ou erreur d'E/S → base
        de travail locale (partage non reconnu, montage FUSE, verrou d'un autre programme)."""
        try:
            os.makedirs(os.path.dirname(self.partage), exist_ok=True)
            neuf = not os.path.exists(self.partage)
            db = sqlite3.connect(self.partage, timeout=ATTENTE_VERROU_S)
            try:
                db.execute('PRAGMA journal_mode=DELETE')
                db.execute('BEGIN IMMEDIATE')               # demande le verrou d'écriture
                db.execute('CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT)')
                db.commit()
            finally:
                db.close()
            return True
        except sqlite3.OperationalError:
            try:                                            # base de 0 octet créée par l'essai : retirée
                if neuf and os.path.getsize(self.partage) == 0:
                    os.remove(self.partage)
            except OSError:
                pass
            return False

    def _lire_sync(self) -> dict:
        try:
            with open(self.sync, encoding='utf-8') as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def _ecrire_sync(self, **valeurs):
        d = self._lire_sync()
        d.update(valeurs, partage_chemin=self.partage, date=D.datetime.now().isoformat(timespec='seconds'))
        config.ecrire_json_atomique(self.sync, d)

    def _noter(self, empreinte_locale: str, empreinte_partage: str, version: int):
        self._ecrire_sync(partage=_stat(self.partage), empreinte_partage=empreinte_partage,
                          empreinte_locale=empreinte_locale, version=version)

    def _partage_existe(self) -> bool:
        try:
            return os.path.getsize(self.partage) > 0
        except OSError:
            return False

    def _partage_change(self, s: dict) -> tuple[bool, str | None]:
        """(changé ?, copie locale du partage si elle a dû être lue).  Date et taille d'abord ; si elles diffèrent,
        le contenu (empreinte) tranche : une date touchée par une sauvegarde ou une copie ne compte pas."""
        if _stat(self.partage) == list(s.get('partage') or [0, 0]):
            return False, None
        if not self._partage_existe():
            return True, None
        if empreinte(self.partage) == s.get('empreinte_partage'):
            self._ecrire_sync(partage=_stat(self.partage))
            return False, None
        copie = self.locale + '.partage'
        _copier_base(self.partage, copie)
        return True, copie

    def _preparer(self):
        s = self._lire_sync()
        locale_existe = os.path.isfile(self.locale) and os.path.getsize(self.locale) > 0
        if not locale_existe or not s or s.get('partage_chemin') not in (None, self.partage):
            if locale_existe and s.get('partage_chemin') != self.partage:   # (collision de clé : improbable)
                os.replace(self.locale, self.locale + '.orpheline-' + _horodatage())
            if self._partage_existe():
                _copier_base(self.partage, self.locale)
                self.rapporter('base_locale_copiee')
            else:
                for p in (self.locale, self.locale + '-journal'):
                    if os.path.exists(p):
                        os.remove(p)
            self._noter(empreinte(self.locale), empreinte(self.partage), _version(self.partage))
            return
        sale = empreinte(self.locale) != s.get('empreinte_locale')
        change, copie = self._partage_change(s)
        if not change:
            if sale:                                     # plantage, coupure : écritures non recopiées
                self.rapporter('base_locale_reprise')
                self.envoyer_fichier()
            return
        if not sale:                                     # partage plus récent (autre machine, NAS) : recopié
            if copie:
                # ce que la base de travail avait déjà recopié doit s'y trouver ; sinon (deux recopies simultanées,
                # la nôtre remplacée), l'union le rend au partage au lieu de le perdre
                fusion = self.locale + '.union'
                ajouts = fusionner_bases(copie, self.locale, fusion).get('de_la_locale', 0)
                if ajouts:
                    os.replace(fusion, self.locale)
                    os.remove(copie)
                else:
                    os.remove(fusion)
                    os.replace(copie, self.locale)
                self._noter('' if ajouts else empreinte(self.locale), empreinte(self.partage), _version(self.partage))
                self.rapporter('base_locale_rafraichie')
                if ajouts:
                    self.envoyer_fichier()
                return
            # base retirée du partage : on repart de zéro, comme lui (l'ancienne base de travail est gardée)
            os.replace(self.locale, self.locale + '.retiree-' + _horodatage())
            self._noter(empreinte(self.locale), empreinte(self.partage), _version(self.partage))
            self.rapporter('base_locale_rafraichie')
            return
        if copie is None:                                # base retirée du partage, écritures locales : recopiées
            self.envoyer_fichier()
            return
        self.divergence = True
        raise Divergence(self.partage, self.locale, copie)

    # ------------------------------------------------------------------ recopie sur le partage
    def envoyer(self, db: sqlite3.Connection, attendre: bool = True, verrou=None) -> bool:
        """Recopie la base de travail sur le partage.  `db` : la connexion d'écriture (instantané pris par l'API de
        sauvegarde, sous `verrou` s'il est donné, après validation) ; le transfert se fait dans un fil si
        `attendre` est faux.  Rend False si rien n'a été recopié (rien à faire, envoi en cours, échec noté)."""
        if self.mode != 'local' or self.divergence:
            return False
        if self._fil is not None and self._fil.is_alive():
            if not attendre:
                return False
            self._fil.join()
        instantane = self.locale + '.envoi'
        try:
            os.remove(instantane)
        except OSError:
            pass
        ctx = verrou if verrou is not None else _Rien()
        with ctx:
            if db.in_transaction:
                db.commit()
            empreinte_locale = empreinte(self.locale)
            if empreinte_locale == self._lire_sync().get('empreinte_locale'):
                self._derniere = time.monotonic()
                return False                             # rien de neuf depuis la dernière recopie
            dst = sqlite3.connect(instantane)
            try:
                db.backup(dst)
            finally:
                dst.close()
        self._derniere = time.monotonic()
        if attendre:
            return self._transferer(instantane, empreinte_locale)
        self._fil = threading.Thread(target=self._transferer, args=(instantane, empreinte_locale),
                                     name='base-partagee', daemon=True)
        self._fil.start()
        return True

    def envoyer_si_du(self, db, verrou=None) -> bool:
        if self.mode == 'local' and time.monotonic() - self._derniere >= self.intervalle:
            return self.envoyer(db, attendre=False, verrou=verrou)
        return False

    def envoyer_fichier(self) -> bool:
        """Recopie la base de travail fermée (reprise après plantage, fusion)."""
        instantane = self.locale + '.envoi'
        shutil.copyfile(self.locale, instantane)
        return self._transferer(instantane, empreinte(self.locale))

    def _transferer(self, instantane: str, empreinte_locale: str) -> bool:
        with self._verrou:
            tmp = None
            try:
                s = self._lire_sync()
                if _stat(self.partage) != list(s.get('partage') or [0, 0]) and \
                        empreinte(self.partage) != s.get('empreinte_partage', ''):
                    if self._partage_existe():           # quelqu'un d'autre a écrit : on n'écrase pas
                        self.divergence = True
                        self.rapporter('base_locale_divergence_en_cours', partage=self.partage)
                        return False
                j = self.partage + '-journal'
                if os.path.isfile(j) and os.path.getsize(j) > 0:   # écrivain direct en cours (ou planté) sur le partage
                    self.erreur_envoi = 'journal'
                    self.rapporter('base_locale_partage_occupe', partage=self.partage)
                    return False
                version = int(s.get('version') or 0) + 1
                db = sqlite3.connect(instantane)
                try:
                    db.execute('CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT)')
                    db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (CLE_VERSION, str(version)))
                    db.commit()
                finally:
                    db.close()
                if not integre(instantane):
                    self.erreur_envoi = 'integrity_check'
                    self.rapporter('base_locale_envoi_echec', erreur='integrity_check')
                    return False
                attendu = empreinte(instantane)
                os.makedirs(os.path.dirname(self.partage), exist_ok=True)
                tmp = os.path.join(os.path.dirname(self.partage),
                                   '.%s.%d.%s.tmp' % (os.path.basename(self.partage), os.getpid(), _horodatage()))
                shutil.copyfile(instantane, tmp)
                if empreinte(tmp) != attendu:            # relu d'un bloc : la copie sur le partage est identique
                    raise OSError('copy differs from the snapshot: %s' % tmp)
                for k in range(ESSAIS_REMPLACEMENT):
                    try:
                        os.replace(tmp, self.partage)
                        tmp = None
                        break
                    except PermissionError:              # Windows : la base est ouverte par un autre programme
                        if k == ESSAIS_REMPLACEMENT - 1:
                            raise
                        time.sleep(0.5 * (k + 1))
                self._noter(empreinte_locale, attendu, version)
                self.erreur_envoi = None
                return True
            except (OSError, sqlite3.Error) as e:
                self.erreur_envoi = str(e)
                self.rapporter('base_locale_envoi_echec', erreur=str(e)[:200])
                return False
            finally:
                for p in (tmp, instantane):
                    if p:
                        try:
                            os.remove(p)
                        except OSError:
                            pass

    def fermer(self, db: sqlite3.Connection | None = None, verrou=None) -> bool:
        """Dernière recopie (fin de session, arrêt, annulation) puis attente du fil."""
        ok = True
        if self._fil is not None:
            self._fil.join()
        if self.mode == 'local' and db is not None:
            r = self.envoyer(db, attendre=True, verrou=verrou)
            ok = r or (self.erreur_envoi is None and not self.divergence)
        return ok


class _Rien:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ============================================================================ lecture
def chemin_lecture(chemin_partage) -> str:
    """Base à lire pour `chemin_partage` : la base de travail locale si elle est au moins aussi récente que celle
    du partage (aucune lecture page par page sur le réseau ; écritures pas encore recopiées comprises), sinon la
    base du partage.  Jamais d'exception."""
    try:
        locale = chemin_travail(chemin_partage)
        if not os.path.isfile(locale):
            return str(chemin_partage)
        with open(locale + '.sync.json', encoding='utf-8') as f:
            s = json.load(f)
        if s.get('partage_chemin') == os.path.abspath(str(chemin_partage)) and \
                _stat(chemin_partage) == list(s.get('partage') or [0, 0]) and os.path.getsize(locale) > 0:
            return locale
    except (OSError, ValueError, AttributeError):
        pass
    return str(chemin_partage)


# ============================================================================ fusion
def _lignes(chemin) -> tuple[dict, list, dict]:
    db = sqlite3.connect(chemin, timeout=5)
    try:
        try:
            images = {r[0]: r for r in db.execute('SELECT id, url, statut, essais, info, maj FROM images')}
        except sqlite3.OperationalError:                 # base encore vide (pas de table)
            images = {}
        try:
            emp = db.execute('SELECT sha, id FROM empreintes').fetchall()
        except sqlite3.Error:
            emp = []
        try:
            meta = dict(db.execute('SELECT cle, valeur FROM meta').fetchall())
        except sqlite3.Error:
            meta = {}
        return images, emp, meta
    finally:
        db.close()


def fusionner_bases(partage: str, locale: str, sortie: str) -> dict:
    """Union de deux bases d'état dans `sortie` (créée à partir de `partage`).  Rend les comptes."""
    ip, ep, mp = _lignes(partage)
    il, el, ml = _lignes(locale)
    tmp = sortie + '.fusion'
    if os.path.exists(tmp):
        os.remove(tmp)
    shutil.copyfile(partage, tmp)
    comptes = {'partage': len(ip), 'locale': len(il), 'de_la_locale': 0, 'conflits': 0, 'meta_differentes': []}
    db = sqlite3.connect(tmp)
    try:
        for i, rl in il.items():
            rp = ip.get(i)
            if rp is None:
                gagnante = rl
                comptes['de_la_locale'] += 1
            else:
                kp, kl = (RANG.get(rp[2], 0), rp[5] or ''), (RANG.get(rl[2], 0), rl[5] or '')
                if rp[2] != rl[2] or rp[4] != rl[4]:
                    comptes['conflits'] += 1
                gagnante = rl if kl > kp else rp
                if gagnante is rl:
                    comptes['de_la_locale'] += 1
                essais = max(rp[3] or 0, rl[3] or 0)
                gagnante = gagnante[:3] + (essais,) + gagnante[4:]
            db.execute('CREATE TABLE IF NOT EXISTS images (id TEXT PRIMARY KEY, url TEXT, statut TEXT, '
                       'essais INTEGER DEFAULT 0, info TEXT, maj TEXT)')
            db.execute('INSERT OR REPLACE INTO images (id, url, statut, essais, info, maj) VALUES (?,?,?,?,?,?)',
                       gagnante)
        db.execute('CREATE TABLE IF NOT EXISTS empreintes (sha TEXT PRIMARY KEY, id TEXT)')
        db.executemany('INSERT OR IGNORE INTO empreintes VALUES (?,?)', el)
        db.execute('CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT)')
        for k, v in ml.items():
            if k == CLE_VERSION:
                continue
            if k not in mp:
                db.execute('INSERT INTO meta VALUES (?,?)', (k, v))
            elif mp[k] != v:
                comptes['meta_differentes'].append(k)       # celle du partage est gardée
        db.commit()
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('integrity_check after merge')
        comptes['total'] = db.execute('SELECT count(*) FROM images').fetchone()[0]
    finally:
        db.close()
    os.replace(tmp, sortie)
    return comptes


def fusionner(chemin_partage, rapporter=None) -> dict:
    """Résout une divergence : garde les deux bases d'origine, écrit leur union dans la base de travail, la recopie
    sur le partage.  Rend les comptes de :func:`fusionner_bases` (+ 'copies' : les deux bases gardées)."""
    b = BasePartagee(chemin_partage, reseau=True, rapporter=rapporter)
    b.mode = 'local'
    pile = _horodatage()
    copie_partage = b.locale + '.partage'
    _copier_base(b.partage, copie_partage)
    garde_locale = b.locale + '.local-' + pile
    garde_partage = b.locale + '.partage-' + pile
    shutil.copyfile(b.locale, garde_locale)
    shutil.copyfile(copie_partage, garde_partage)
    comptes = fusionner_bases(copie_partage, b.locale, b.locale)
    os.remove(copie_partage)
    s = b._lire_sync()
    # la base du partage lue ici devient la référence : la recopie la remplace (rien d'autre n'a écrit entre-temps,
    # sinon une nouvelle divergence est signalée)
    b._ecrire_sync(partage=_stat(b.partage), empreinte_partage=empreinte(b.partage),
                   version=max(int(s.get('version') or 0), _version(garde_partage)), empreinte_locale='')
    comptes['envoyee'] = b.envoyer_fichier()
    comptes['copies'] = [garde_locale, garde_partage]
    return comptes


def divergence_en_attente(chemin_partage) -> bool:
    """Une base de travail locale existe, a des écritures non recopiées ET le partage a changé (sans rien lire du
    partage au-delà de sa date et de sa taille)."""
    try:
        locale = chemin_travail(chemin_partage)
        with open(locale + '.sync.json', encoding='utf-8') as f:
            s = json.load(f)
        return empreinte(locale) != s.get('empreinte_locale') and \
            _stat(chemin_partage) != list(s.get('partage') or [0, 0]) and os.path.getsize(chemin_partage) > 0
    except (OSError, ValueError):
        return False
