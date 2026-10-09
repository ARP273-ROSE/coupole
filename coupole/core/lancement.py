"""Lancement des programmes externes (0.1.12) : *Ouvrir*, *Ouvrir avec*, *Ouvrir l'emplacement*, dossier, manuel…

Règles :
  * toujours une **liste d'arguments**, jamais de shell (`shell=True` interdit : un chemin à `$`, `'`, `(`… serait
    interprété) ;
  * **tout est noté dans coupole.log** : méthode, programme, arguments, pid ; puis, si le programme se termine dans
    les premières secondes, son code de retour et le début de ce qu'il a écrit (stdout + stderr, capturés dans un
    fichier anonyme : un tube plein bloquerait un programme qui vit plus longtemps que Coupole) ;
  * le programme est **détaché** (il survit à Coupole) ;
  * une erreur n'est jamais silencieuse : `Lancement.message()` rend une clé de texte (FR/EN) pour la barre d'état.

Ouverture par défaut sous Linux : `xdg-open` lance l'application associée par son fichier .desktop.  Si la ligne
`Exec=` de ce .desktop n'a aucun code `%f %F %u %U` (cas du `pixinsight.desktop` créé à la main), l'application
démarre **sans le fichier** : `application_par_defaut()` le détecte (`xdg-mime query filetype` puis
`xdg-mime query default`, lecture du .desktop dans les dossiers XDG) ; l'appelant lance alors le logiciel
directement (voir `logiciels.ouvrir_defaut`).
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time

log = logging.getLogger('coupole.lancement')

ATTENTE_SORTIE = 3.0          # secondes pendant lesquelles on attend une sortie rapide (erreur, « cède la main »)
SORTIE_MAX = 4000             # octets de sortie gardés dans le journal


class Lancement:
    """Un programme lancé (ou qui n'a pas pu l'être).  `verifier()` est non bloquant ; `attendre()` bloque au plus
    `ATTENTE_SORTIE` secondes (ligne de commande, tests)."""

    def __init__(self, methode: str, argv: list, nom: str = ''):
        self.methode = methode
        self.argv = [str(a) for a in argv]
        self.nom = nom or (os.path.basename(self.argv[0]) if self.argv else methode)
        self.proc = None
        self.pid = None
        self.code = None              # code de retour s'il s'est terminé pendant l'attente
        self.sortie = ''              # début de stdout + stderr
        self.erreur = ''              # '' : lancé ; sinon clé de texte (lg_err_*)
        self.detail = ''              # message du système (exception, ligne d'erreur)
        self.notes = []               # remarques (clés de texte) : lien temporaire, portail flatpak, instance…
        self.params = {}              # paramètres des textes
        self.termine = False          # état final connu (sorti, ou toujours en marche après l'attente)
        self.motifs = ()              # ((texte cherché dans la sortie, clé de note), …)
        self.ignorer_code = False     # programme dont le code de retour ne dit rien (explorer.exe)
        self._fichier = None
        self._debut = time.monotonic()

    # ------------------------------------------------------------ état
    @property
    def ok(self) -> bool:
        return not self.erreur

    def echec(self, cle: str, detail: str = '') -> 'Lancement':
        self.erreur, self.detail, self.termine = cle, detail, True
        log.warning('launch failed [%s] %s %r: %s %s', self.methode, self.nom, self.argv, cle, detail)
        return self

    def _lire_sortie(self) -> str:
        f = self._fichier
        if f is None:
            return ''
        try:
            if hasattr(os, 'pread'):           # sans déplacer la position partagée avec le programme
                donnees = os.pread(f.fileno(), SORTIE_MAX, 0)
            elif self.code is not None:       # Windows : seulement une fois le programme sorti
                f.seek(0)
                donnees = f.read(SORTIE_MAX)
            else:
                donnees = b''
            return donnees.decode('utf-8', 'replace').strip()
        except (OSError, ValueError):
            return ''

    def _fermer(self):
        if self._fichier is not None:
            try:
                self._fichier.close()
            except OSError:
                pass
            self._fichier = None

    def verifier(self) -> bool:
        """True quand l'état est connu : programme sorti (code et sortie notés) ou toujours en marche après
        `ATTENTE_SORTIE` secondes.  Non bloquant."""
        if self.termine:
            return True
        if self.proc is None:
            self.termine = True
            return True
        code = self.proc.poll()
        if code is not None:
            self.code = code
            self.sortie = self._lire_sortie()
            self._fermer()
            self.termine = True
            self._reconnaitre()
            if code != 0 and not self.ignorer_code:
                self.erreur = 'lg_err_code'
                self.detail = premiere_ligne(self.sortie)
                log.warning('launch [%s] %s pid %s exited with code %s; output: %s', self.methode, self.nom, self.pid,
                            code, self.sortie or '(none)')
            else:
                log.info('launch [%s] %s pid %s exited with code 0; output: %s', self.methode, self.nom, self.pid,
                         self.sortie or '(none)')
            return True
        if time.monotonic() - self._debut >= ATTENTE_SORTIE:
            self.sortie = self._lire_sortie()
            self._fermer()
            self.termine = True
            self._reconnaitre()
            log.info('launch [%s] %s pid %s still running after %.0f s; output so far: %s', self.methode, self.nom,
                     self.pid, ATTENTE_SORTIE, self.sortie or '(none)')
            return True
        return False

    def _reconnaitre(self):
        for texte, cle in self.motifs:
            if texte in (self.sortie or '') and cle not in self.notes:
                self.notes.insert(0, cle)
                log.info('launch [%s] %s: output says %r -> %s', self.methode, self.nom, texte, cle)

    def attendre(self, delai: float | None = None) -> 'Lancement':
        fin = time.monotonic() + (ATTENTE_SORTIE if delai is None else delai) + 0.5
        while not self.verifier() and time.monotonic() < fin:
            time.sleep(0.05)
        return self

    def message(self) -> tuple[str, dict] | None:
        """(clé, paramètres) à afficher, ou None si rien à signaler."""
        p = dict(self.params, logiciel=self.nom, detail=self.detail or '—', code=self.code)
        if self.erreur:
            return self.erreur, p
        if self.notes:
            return self.notes[0], p
        return None


def premiere_ligne(texte: str) -> str:
    for ligne in (texte or '').splitlines():
        if ligne.strip():
            return ligne.strip()[:200]
    return ''


# ------------------------------------------------------------------ environnement des programmes lancés
def environnement_enfant(env=None) -> dict:
    """Environnement transmis aux programmes : celui de Coupole, SANS ce que Coupole a posé pour son propre Qt
    (`QT_QPA_PLATFORMTHEME` choisi par `gui/plateforme.preparer`) — un autre programme Qt ne doit pas en hériter."""
    e = dict(os.environ if env is None else env)
    pose = e.pop('COUPOLE_QPA_THEME_POSE', None)
    if pose is not None and e.get('QT_QPA_PLATFORMTHEME') == pose:
        e.pop('QT_QPA_PLATFORMTHEME', None)
    return e


def demarrer(argv: list, methode: str, nom: str = '', env: dict | None = None, cwd=None) -> Lancement:
    """Lance `argv` détaché, sortie capturée ; noté dans le journal.  Ne lève jamais."""
    l = Lancement(methode, argv, nom)
    if not l.argv:
        return l.echec('lg_err_introuvable', 'empty command')
    log.info('launch [%s] program=%s args=%r', methode, l.argv[0], l.argv[1:])
    try:
        f = tempfile.TemporaryFile()
    except OSError:
        f = None
    kw = {'stdin': subprocess.DEVNULL, 'stdout': f if f is not None else subprocess.DEVNULL,
          'stderr': subprocess.STDOUT if f is not None else subprocess.DEVNULL,
          'env': environnement_enfant(env), 'cwd': cwd}
    if os.name == 'nt':
        kw['creationflags'] = 0x00000008 | 0x00000200            # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        kw['start_new_session'] = True
    try:
        l.proc = subprocess.Popen(l.argv, **kw)
    except FileNotFoundError as e:
        if f is not None:
            f.close()
        return l.echec('lg_err_introuvable', str(e))
    except PermissionError as e:
        if f is not None:
            f.close()
        return l.echec('lg_err_permission', str(e))
    except Exception as e:                                       # OSError, ValueError…
        if f is not None:
            f.close()
        return l.echec('lg_err_systeme', '%s: %s' % (type(e).__name__, e))
    l.pid = l.proc.pid
    l._fichier = f
    log.info('launch [%s] %s started, pid %s', methode, l.nom, l.pid)
    return l


def executer(argv: list, methode: str, delai: float = 5.0) -> tuple[int | None, str]:
    """Commande courte attendue (gdbus, xdg-mime…) : (code, sortie) ; (None, motif) en cas d'échec.  Journalisée."""
    try:
        r = subprocess.run([str(a) for a in argv], capture_output=True, timeout=delai, env=environnement_enfant())
    except Exception as e:
        log.info('run [%s] %r failed: %s', methode, argv, e)
        return None, str(e)
    sortie = (r.stdout or b'').decode('utf-8', 'replace').strip()
    err = (r.stderr or b'').decode('utf-8', 'replace').strip()
    log.info('run [%s] %r -> code %s%s', methode, argv, r.returncode, (' stderr: ' + err[:500]) if err else '')
    return r.returncode, sortie if r.returncode == 0 else (err or sortie)


def fait(methode: str, argv: list, nom: str = '') -> Lancement:
    """Lancement terminé sans processus suivi (os.startfile, QDesktopServices) : noté, état final."""
    l = Lancement(methode, argv, nom)
    l.termine = True
    log.info('launch [%s] %r done', methode, l.argv)
    return l


# ------------------------------------------------------------------ ouverture par l'application du système
def ouvrir_systeme(chemin) -> Lancement | None:
    """Ouvre un fichier ou un dossier avec l'application associée : `os.startfile` (Windows), `open` (macOS),
    `xdg-open` (Linux).  None si aucun moyen (l'appelant essaie alors QDesktopServices, journalisé aussi)."""
    p = os.path.abspath(str(chemin))
    if os.name == 'nt':
        try:
            os.startfile(p)                                   # noqa: S606 — pas de shell, association Windows
        except OSError as e:
            l = Lancement('startfile', [p])
            return l.echec('lg_err_systeme', str(e))
        return fait('startfile', [p], 'Windows')
    if sys.platform == 'darwin':
        return demarrer(['open', p], 'open', 'open')
    xo = shutil.which('xdg-open')
    if xo:
        return demarrer([xo, p], 'xdg-open', 'xdg-open')
    log.info('launch: no xdg-open for %s', p)
    return None


# ------------------------------------------------------------------ .desktop de l'application par défaut (Linux)
CODES_FICHIER = ('%f', '%F', '%u', '%U')


def dossiers_applications(env=None) -> list[str]:
    e = os.environ if env is None else env
    maison = e.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')
    autres = (e.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':')
    return [os.path.join(d, 'applications') for d in [maison] + [a for a in autres if a]]


def trouver_desktop(ident: str, dossiers=None) -> str:
    """Chemin du fichier .desktop d'un identifiant (`kde4-foo.desktop` peut être `kde4/foo.desktop`)."""
    if not ident:
        return ''
    for d in (dossiers if dossiers is not None else dossiers_applications()):
        candidats = [os.path.join(d, ident)]
        if '-' in ident:
            candidats.append(os.path.join(d, *ident.split('-')))
        for c in candidats:
            if os.path.isfile(c):
                return c
    return ''


def lire_desktop(chemin) -> dict:
    """Clés de la section [Desktop Entry] (Exec, Name, MimeType, TryExec…)."""
    out = {}
    try:
        with open(chemin, encoding='utf-8', errors='replace') as f:
            section = ''
            for ligne in f:
                ligne = ligne.strip()
                if ligne.startswith('['):
                    section = ligne
                    continue
                if section == '[Desktop Entry]' and '=' in ligne and not ligne.startswith('#'):
                    k, v = ligne.split('=', 1)
                    out.setdefault(k.strip(), v.strip())
    except OSError:
        pass
    return out


def exec_accepte_fichier(exec_ligne: str) -> bool:
    return any(c in (exec_ligne or '') for c in CODES_FICHIER)


def programme_exec(exec_ligne: str) -> str:
    """Programme d'une ligne Exec= (premier mot, guillemets retirés)."""
    import shlex
    try:
        mots = shlex.split(exec_ligne or '')
    except ValueError:
        mots = (exec_ligne or '').split()
    mots = [m for m in mots if not m.startswith('%')]
    if mots and mots[0] == 'env':                      # Exec=env VAR=… programme
        mots = [m for m in mots[1:] if '=' not in m] or ['']
    return mots[0] if mots else ''


def application_par_defaut(chemin, executer_=None) -> dict:
    """Linux : {'type', 'desktop', 'fichier', 'exec', 'programme', 'accepte_fichier'} de l'application que
    `xdg-open` lancerait pour ce fichier ; {} si inconnu (pas de xdg-mime, pas d'association…)."""
    ex = executer_ or executer
    if not shutil.which('xdg-mime') and executer_ is None:
        return {}
    code, mime = ex(['xdg-mime', 'query', 'filetype', str(chemin)], 'xdg-mime')
    if code != 0 or not mime:
        return {}
    mime = mime.splitlines()[0].strip()
    code, ident = ex(['xdg-mime', 'query', 'default', mime], 'xdg-mime')
    ident = (ident or '').splitlines()[0].strip() if code == 0 and ident else ''
    out = {'type': mime, 'desktop': ident}
    if not ident:
        return out
    fichier = trouver_desktop(ident)
    out['fichier'] = fichier
    if not fichier:
        return out
    ent = lire_desktop(fichier)
    out['exec'] = ent.get('Exec', '')
    out['programme'] = programme_exec(out['exec'])
    out['accepte_fichier'] = exec_accepte_fichier(out['exec'])
    log.info('default application for %s: type %s, %s (%s), Exec=%s, receives the file: %s', chemin, mime, ident,
             fichier, out['exec'], out['accepte_fichier'])
    return out
