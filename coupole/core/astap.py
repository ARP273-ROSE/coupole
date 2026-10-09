"""ASTAP (solveur astrométrique de Han Kleijn, www.hnsky.org) : facultatif.

Coupole fonctionne entièrement sans ASTAP : les solutions astrométriques
présentes dans les en-têtes passent toujours les contrôles de cohérence
(échelle, angle, centre).  ASTAP n'ajoute qu'une chose : une vérification
INDÉPENDANTE de chaque solution, et la possibilité d'en refaire une fausse.

Ce module :
  * cherche ASTAP et son catalogue d'étoiles (emplacements par défaut de chaque
    système, PATH, variables d'environnement, choix manuel) ;
  * vérifie la version et que le catalogue est complet ;
  * décrit quoi installer selon le système et l'architecture (liens officiels
    relevés sur https://www.hnsky.org/astap.htm le 8 octobre 2026) ;
  * lance une résolution.

Pas d'ASTAP dans les paquets de Coupole : licence propre (MPL 2.0) et taille du
catalogue (1,2 à 1,3 Go pour D80).
"""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .fitsentete import Entete

_SANS_CONSOLE = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

# Processus ASTAP en cours dans CE processus (un seul à la fois par processus de conversion) : un arrêt
# demandé (annulation, fermeture, SIGTERM du pilote) le tue au lieu d'attendre jusqu'à 4 minutes.
_courant: dict = {'p': None}
_verrou = threading.Lock()


def tuer_en_cours() -> bool:
    with _verrou:
        p = _courant['p']
    if p is None or p.poll() is not None:
        return False
    try:
        p.kill()
    except OSError:
        return False
    return True


def installer_arret_propre():
    """Dans un processus de conversion : SIGTERM (annulation du pilote) tue ASTAP puis quitte."""
    import signal

    def h(signum, frame):
        tuer_en_cours()
        os._exit(1)
    try:
        signal.signal(signal.SIGTERM, h)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, h)
    except (ValueError, OSError):            # pas dans le fil principal : rien à faire
        pass

SITE = 'https://www.hnsky.org/astap.htm'
SF = 'https://sourceforge.net/projects/astap-program/files/'
NB_FICHIERS_CATALOGUE = 1476        # format 1476 (D05, D20, D50, D80, V50) : 1476 tuiles

# Catalogues : nom → (densité étoiles/deg², taille approximative du téléchargement en Mo,
# relevées sur SourceForge le 8/10/2026).  Le site officiel : « Is your field of view 0.6 degree
# or larger you can download either the D05 or D20 or D50 or D80 » ; les catalogues denses
# « will be beneficial for setups with a small field-of view ».
CATALOGUES = {
    'd80': (8000, 1250),
    'd50': (5000, 900),
    'd20': (2000, 400),
    'd05': (500, 100),
    'v50': (5000, None),
}


@dataclass
class EtatASTAP:
    executable: str = ''
    version: str = ''
    est_cli: bool = False
    catalogue_dossier: str = ''
    catalogue: str = ''                # 'd80', 'd50'...
    catalogue_fichiers: int = 0
    catalogue_complet: bool = False
    candidats_vus: list = field(default_factory=list)

    @property
    def utilisable(self) -> bool:
        return bool(self.executable) and self.catalogue_complet

    def message_cle(self) -> str:
        if not self.executable:
            return 'astap_absent'
        if not self.catalogue:
            return 'astap_sans_catalogue'
        if not self.catalogue_complet:
            return 'astap_catalogue_incomplet'
        return 'astap_pret'


# ======================================================================== emplacements
def _noms_executables() -> list[str]:
    if sys.platform == 'win32':
        return ['astap_cli.exe', 'astap.exe']
    return ['astap_cli', 'astap']


def emplacements_par_defaut() -> list[Path]:
    """Dossiers où chercher l'exécutable et le catalogue, du plus probable au moins probable."""
    h = Path.home()
    if sys.platform == 'win32':
        pf = [os.environ.get(v) for v in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)')]
        bases = [Path(p) / 'astap' for p in pf if p]
        bases += [Path(os.environ.get('LOCALAPPDATA', h / 'AppData' / 'Local')) / 'astap',
                  Path(os.environ.get('LOCALAPPDATA', h / 'AppData' / 'Local')) / 'Programs' / 'astap',
                  Path('C:/astap'), h / 'astap']
    elif sys.platform == 'darwin':
        bases = [Path('/Applications/ASTAP.app/Contents/MacOS'), h / 'Applications' / 'ASTAP.app' / 'Contents' / 'MacOS',
                 Path('/usr/local/opt/astap'), Path('/opt/homebrew/opt/astap'), Path('/usr/local/bin'),
                 h / 'astap', h / 'Applications' / 'astap']
    else:
        bases = [Path('/opt/astap'), Path('/usr/share/astap/data'), Path('/usr/bin'), Path('/usr/local/bin'),
                 Path('/usr/local/astap'), h / 'astap', h / '.local' / 'share' / 'astap', h / '.local' / 'bin',
                 h / 'Applications']
    return bases


def _dossiers_catalogue(exe: Path | None) -> list[Path]:
    """Où ASTAP lui-même cherche le catalogue : à côté du programme, puis les dossiers officiels."""
    d = []
    if exe is not None:
        d.append(exe.parent)
        if exe.parent.name == 'MacOS':
            d.append(exe.parent.parent / 'Resources')
    if sys.platform == 'darwin':
        d += [Path('/usr/local/opt/astap'), Path('/opt/homebrew/opt/astap')]
    elif sys.platform != 'win32':
        d += [Path('/opt/astap'), Path('/usr/share/astap/data')]
    return d + emplacements_par_defaut()


def analyser_catalogue(dossier) -> tuple[str, int]:
    """(nom du catalogue le plus dense trouvé, nombre de tuiles) dans `dossier`."""
    p = Path(dossier)
    if not p.is_dir():
        return '', 0
    compte: dict[str, int] = {}
    try:
        for f in p.iterdir():
            m = re.match(r'^([a-z]\d\d)_\d{4}\.1476$', f.name.lower())
            if m:
                compte[m.group(1)] = compte.get(m.group(1), 0) + 1
    except OSError:
        return '', 0
    if not compte:
        return '', 0
    ordre = ['d80', 'd50', 'v50', 'd20', 'd05']
    meilleur = sorted(compte, key=lambda c: (ordre.index(c) if c in ordre else 99, -compte[c]))[0]
    return meilleur, compte[meilleur]


def version_de(exe: str) -> tuple[str, bool]:
    """(version, est_cli).  Seul astap_cli est interrogé : l'exécutable graphique ouvrirait une fenêtre."""
    nom = Path(exe).name.lower()
    if 'cli' not in nom:
        return '', False
    try:
        r = subprocess.run([exe, '-h'], capture_output=True, text=True, timeout=10, creationflags=_SANS_CONSOLE)
        m = re.search(r'version\s+(\S+)', r.stdout + r.stderr)
        return (m.group(1) if m else ''), True
    except Exception:
        return '', True


def detecter(executable: str = '', catalogue: str = '') -> EtatASTAP:
    """Cherche ASTAP.  `executable`/`catalogue` : choix manuel (réglages), prioritaires."""
    e = EtatASTAP()
    candidats: list[Path] = []
    for v in (executable, os.environ.get('COUPOLE_ASTAP', '')):
        if v:
            p = Path(v).expanduser()
            if p.is_dir():
                candidats += [p / n for n in _noms_executables()]
            else:
                candidats.append(p)
    # astap_cli d'abord, PARTOUT (PATH puis dossiers usuels), puis seulement l'exécutable graphique : sur
    # Arch/Manjaro le paquet officiel ne met rien dans le PATH (/opt/astap seulement) et son « astap » graphique
    # demande GTK2 (AUR) ; sous Debian, /usr/bin/astap (graphique) passait avant /opt/astap/astap_cli.
    for n in _noms_executables():
        w = shutil.which(n)
        if w:
            candidats.append(Path(w))
        for b in emplacements_par_defaut():
            candidats.append(b / n)
    vus = []
    exe = None
    for c in candidats:
        vus.append(str(c))
        try:
            if c.is_file() and (sys.platform == 'win32' or os.access(c, os.X_OK)):
                exe = c.absolute()
                break
        except OSError:
            continue
    e.candidats_vus = vus
    if exe is not None:
        e.executable = str(exe)
        e.version, e.est_cli = version_de(e.executable)
    dossiers: list[Path] = []
    for v in (catalogue, os.environ.get('COUPOLE_ASTAP_CATALOGUE', '')):
        if v:
            dossiers.append(Path(v).expanduser())
    dossiers += _dossiers_catalogue(exe)
    for d in dossiers:
        nom, n = analyser_catalogue(d)
        if nom:
            e.catalogue_dossier, e.catalogue, e.catalogue_fichiers = str(d), nom, n
            e.catalogue_complet = n >= NB_FICHIERS_CATALOGUE
            break
    return e


# ======================================================================== conseils d'installation
def famille_linux() -> str:
    """'deb', 'rpm', 'arch' ou 'autre', d'après /etc/os-release."""
    try:
        txt = Path('/etc/os-release').read_text().lower()
    except OSError:
        return 'autre'
    ident = ' '.join(re.findall(r'^(?:id|id_like)=(.*)$', txt, re.M))
    if any(x in ident for x in ('debian', 'ubuntu', 'raspbian', 'mint')):
        return 'deb'
    if any(x in ident for x in ('fedora', 'rhel', 'centos', 'suse', 'opensuse')):
        return 'rpm'
    if 'arch' in ident or 'manjaro' in ident:
        return 'arch'
    return 'autre'


def plateforme() -> tuple[str, str]:
    """(système, architecture) normalisés : ('windows'|'macos'|'linux', 'x86_64'|'arm64'|...)."""
    s = 'windows' if sys.platform == 'win32' else 'macos' if sys.platform == 'darwin' else 'linux'
    a = platform.machine().lower()
    a = {'amd64': 'x86_64', 'x64': 'x86_64', 'aarch64': 'arm64'}.get(a, a)
    if s == 'linux' and a.startswith('armv7'):
        a = 'armhf'
    return s, a


def _u(chemin: str) -> str:
    return SF + chemin + '/download'


AUR_D80 = 'https://aur.archlinux.org/packages/d80-star-db-astap'
# Extraction SÛRE du D80 depuis le .deb hors Debian (vérifiée sur le vrai paquet : 1 213 392 756 octets,
# md5 1d0683cbc0d0330df03378fab9d899bf, 1 476 fichiers d80_*.1476 sous ./opt/astap).  Jamais « tar -x … -C / » en
# root : l'archive contient « ./ » et « ./opt/ », dont les droits remplaceraient ceux de / et de /opt.
EXTRAIRE_D80_DEB = ("bsdtar -xf d80_star_database.deb data.tar.xz && sudo mkdir -p /opt/astap && "
                    "sudo tar -xJf data.tar.xz -C /opt/astap --strip-components=3 --no-same-owner "
                    "--wildcards './opt/astap/d80_*'")


def conseils_installation(systeme: str | None = None, arch: str | None = None,
                          famille: str | None = None) -> dict:
    """Ce qu'il faut télécharger et les étapes (clés de traduction) pour cette machine.

    Renvoie {'programme': [(libellé_clé, url)], 'cli': url|None, 'catalogue': [(clé, url)],
             'etapes': [clés], 'notes': [clés], 'dossier': chemin par défaut, 'page'}.
    Liens relevés sur la page officielle www.hnsky.org/astap.htm et dans les dossiers SourceForge du projet
    (9/10/2026) ; chacun est vérifié par un test réseau (HEAD, redirections suivies, 200 attendu).  Il n'existe
    PAS de D80 en .zip (lien mort de la page officielle) : D80 en .exe (Windows), .pkg (macOS), .deb (Linux) ;
    D50 en .exe, .pkg, .deb, .zip et .pkg.tar.zst (Arch).
    """
    s0, a0 = plateforme()
    s, a = systeme or s0, arch or a0
    fam = famille or (famille_linux() if s == 'linux' else '')
    r = {'systeme': s, 'arch': a, 'famille': fam, 'programme': [], 'cli': None, 'catalogue': [],
         'etapes': [], 'notes': [], 'dossier': '', 'page': SITE}
    if s == 'windows':
        if a == 'arm64':
            r['cli'] = _u('windows_installer/astap_command-line_version_win11_aarch64.zip')
            r['programme'] = [('astap_lien_cli_zip', r['cli'])]
            r['catalogue'] = [('astap_lien_d80_exe', _u('star_databases/d80_star_database.exe')),
                              ('astap_lien_d50_zip', _u('star_databases/d50_star_database.zip'))]
            r['etapes'] = ['astap_etape_win_arm_1', 'astap_etape_win_arm_2', 'astap_etape_win_arm_3']
            r['dossier'] = 'C:\\astap'
        else:
            r['programme'] = [('astap_lien_installeur', _u('windows_installer/astap_setup.exe'))]
            r['cli'] = _u('windows_installer/astap_command-line_version_win64.zip')
            r['catalogue'] = [('astap_lien_d80_exe', _u('star_databases/d80_star_database.exe')),
                              ('astap_lien_d50_exe', _u('star_databases/d50_star_database.exe'))]
            r['etapes'] = ['astap_etape_win_1', 'astap_etape_win_2', 'astap_etape_win_3', 'astap_etape_win_4']
            r['dossier'] = 'C:\\Program Files\\astap'
    elif s == 'macos':
        if a == 'arm64':
            r['programme'] = [('astap_lien_pkg_m', _u('macOS%20installer/astap_M1.pkg'))]
            r['cli'] = _u('macOS%20installer/astap_command-line_version_macOS_M1.zip')
        else:
            r['programme'] = [('astap_lien_pkg_intel', _u('macOS%20installer/astap.pkg'))]
            r['cli'] = _u('macOS%20installer/astap_command-line_version_macOS_x86_64.zip')
        r['catalogue'] = [('astap_lien_d80_pkg', _u('star_databases/d80_star_database.pkg')),
                          ('astap_lien_d50_pkg', _u('star_databases/d50_star_database.pkg'))]
        r['etapes'] = ['astap_etape_mac_1', 'astap_etape_mac_2'] + \
            (['astap_etape_mac_m'] if a == 'arm64' else []) + ['astap_etape_mac_3']
        r['dossier'] = '/usr/local/opt/astap'
    else:
        if a == 'arm64':
            prog = {'deb': [('astap_lien_deb', _u('linux_installer/astap_aarch64.deb'))],
                    'arch': [('astap_lien_arch', _u('linux_installer/astap_aarch64.pkg.tar.zst'))]}
            r['programme'] = prog.get(fam, [('astap_lien_targz', _u('linux_installer/astap_aarch64.tar.gz'))])
            r['cli'] = _u('linux_installer/astap_command-line_version_Linux_aarch64.zip')
        elif a == 'armhf':
            prog = {'deb': [('astap_lien_deb', _u('linux_installer/astap_armhf.deb'))]}
            r['programme'] = prog.get(fam, [('astap_lien_targz', _u('linux_installer/astap_armhf.tar.gz'))])
            r['cli'] = _u('linux_installer/astap_command-line_version_Linux_armhf.zip')
        else:
            prog = {'deb': [('astap_lien_deb', _u('linux_installer/astap_amd64.deb'))],
                    'rpm': [('astap_lien_rpm', _u('linux_installer/astap_amd64.rpm'))],
                    'arch': [('astap_lien_arch_gtk3', _u('linux_installer/astap_amd64_gtk3.pkg.tar.zst')),
                             ('astap_lien_arch', _u('linux_installer/astap_amd64.pkg.tar.zst'))]}
            r['programme'] = prog.get(fam, [('astap_lien_targz', _u('linux_installer/astap_amd64.tar.gz'))])
            r['cli'] = _u('linux_installer/astap_command-line_version_Linux_amd64.zip')
        d80_deb = ('astap_lien_d80_deb', _u('star_databases/d80_star_database.deb'))
        if fam == 'deb':
            r['catalogue'] = [d80_deb, ('astap_lien_d50_deb', _u('star_databases/d50_star_database.deb'))]
            r['etapes'] = ['astap_etape_linux_deb_1', 'astap_etape_linux_deb_2', 'astap_etape_linux_3']
        elif fam == 'arch':
            r['catalogue'] = [('astap_lien_d80_aur', AUR_D80), d80_deb,
                              ('astap_lien_d50_arch', _u('star_databases/d50_star_database.pkg.tar.zst'))]
            r['etapes'] = ['astap_etape_linux_arch_1', 'astap_etape_linux_arch_2', 'astap_etape_linux_3']
            r['notes'] = ['astap_note_arch_cli']
        else:
            r['catalogue'] = [d80_deb, ('astap_lien_d50_zip', _u('star_databases/d50_star_database.zip'))]
            r['etapes'] = ['astap_etape_linux_autre_1', 'astap_etape_linux_autre_2', 'astap_etape_linux_3']
        r['dossier'] = '/opt/astap'
    return r


def urls_conseillees() -> list[tuple[str, str, str, str]]:
    """Toutes les adresses que le guide peut donner : (système, architecture, famille, url), pour le test réseau."""
    combos = [('windows', 'x86_64', ''), ('windows', 'arm64', ''), ('macos', 'arm64', ''), ('macos', 'x86_64', '')]
    combos += [('linux', a, f) for a in ('x86_64', 'arm64', 'armhf') for f in ('deb', 'rpm', 'arch', 'autre')]
    out = []
    for s, a, f in combos:
        c = conseils_installation(s, a, f)
        for u in [u for _, u in c['programme'] + c['catalogue']] + ([c['cli']] if c['cli'] else []) + [c['page']]:
            if (s, a, f, u) not in out:
                out.append((s, a, f, u))
    return out


def catalogue_conseille(champ_deg: float) -> str:
    """Catalogue conseillé pour un champ (hauteur de l'image, degrés).

    Au-dessus de 0,6° le site officiel accepte D05 à D80 ; en dessous il ne cite
    aucun seuil mais indique que les catalogues denses servent les petits champs :
    D80 (le plus dense, celui du traitement de référence de la banque).
    """
    return 'd80' if champ_deg < 0.6 else 'd50'


# ======================================================================== résolution
class _Resultat:
    def __init__(self, stdout, stderr):
        self.stdout, self.stderr = stdout or '', stderr or ''


def _lancer(cmd, delai, arret=None):
    """subprocess.run annulable : `arret` (threading.Event) tue le processus ; délai respecté."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         creationflags=_SANS_CONSOLE, stdin=subprocess.DEVNULL)
    with _verrou:
        _courant['p'] = p
    try:
        fin = time.monotonic() + delai
        while True:
            try:
                out, err = p.communicate(timeout=0.25)
                return _Resultat(out, err)
            except subprocess.TimeoutExpired:
                if arret is not None and arret.is_set():
                    p.kill()
                    p.communicate()
                    raise Annulee()
                if time.monotonic() > fin:
                    p.kill()
                    p.communicate()
                    raise subprocess.TimeoutExpired(cmd, delai)
    finally:
        with _verrou:
            if _courant['p'] is p:
                _courant['p'] = None


class Annulee(Exception):
    """Résolution interrompue à la demande de l'utilisateur."""


def resoudre(etat: EtatASTAP, chemin_fits: str, ra=None, dec=None, fov_h=0.0, rayon=3.0, extra=(),
             delai=240, arret=None):
    """Résout `chemin_fits` autour de (ra, dec) en degrés.  Renvoie (Entete WCS, message) ou (None, message).

    Arguments passés en liste (jamais de shell) ; `arret` : threading.Event qui interrompt ASTAP (lève Annulee).
    """
    if not etat.utilisable:
        return None, etat.message_cle()
    if not os.path.isfile(etat.executable) or not os.path.isfile(str(chemin_fits)):
        return None, 'ASTAP: executable or image missing'
    base = str(chemin_fits)[:-5] if str(chemin_fits).lower().endswith('.fits') else str(chemin_fits)
    for ext in ('.wcs', '.ini', '.log'):
        if os.path.exists(base + ext):
            os.remove(base + ext)
    cmd = [etat.executable, '-f', str(chemin_fits), '-D', etat.catalogue, '-d', etat.catalogue_dossier,
           '-wcs', '-sip', '-fov', '%.3f' % fov_h, '-z', '0'] + [str(x) for x in extra]
    if ra is not None:
        cmd += ['-ra', '%.6f' % (ra / 15), '-spd', '%.6f' % (dec + 90), '-r', '%.1f' % rayon]
    t0 = time.time()
    try:
        r = _lancer(cmd, delai, arret)
    except subprocess.TimeoutExpired:
        return None, 'ASTAP: timeout'
    except OSError as ex:
        return None, 'ASTAP: %s' % ex
    dt = time.time() - t0
    if not os.path.exists(base + '.wcs'):
        msg = (r.stdout + r.stderr).strip().splitlines()
        return None, 'ASTAP: no solution (%.1f s) %s' % (dt, msg[-1][:80] if msg else '')
    with open(base + '.wcs', 'rb') as f:
        txt = f.read().decode('ascii', 'replace')
    cartes = [txt[i:i + 80] for i in range(0, len(txt), 80)]
    cartes = [c for c in cartes if c[:8].strip() and not c.startswith('END')]
    e = Entete(cartes)
    if e.get('A_ORDER') is not None and not (e.gets('CTYPE1') or '').endswith('-SIP'):
        e.poser('CTYPE1', "'RA---TAN-SIP'", 'TAN projection + SIP distortion')
        e.poser('CTYPE2', "'DEC--TAN-SIP'", 'TAN projection + SIP distortion')
    for ext in ('.wcs', '.ini', '.log'):
        if os.path.exists(base + ext):
            os.remove(base + ext)
    if e.gets('PLTSOLVD') not in ('T', None) and e.gets('CTYPE1') is None:
        return None, 'ASTAP: PLTSOLVD=F'
    return e, '%.1f s' % dt
