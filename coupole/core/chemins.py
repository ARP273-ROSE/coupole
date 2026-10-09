"""Chemins locaux et réseau : partages montés (cifs, nfs, gvfs, kio-fuse…), chemins UNC Windows, URI SQLite.

Un dossier de sortie peut se trouver sur un NAS : ``\\\\serveur\\partage\\…`` (UNC, Windows),
``/run/user/1000/gvfs/smb-share:server=nas,share=astro/…`` (GNOME, KDE avec kio-fuse), un montage cifs ou nfs
(``/mnt/partage``), ``/Volumes/astro`` (macOS). Tout ce qui manipule ces chemins passe par ici.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote

# types de systèmes de fichiers distants (/proc/mounts sous Linux, `mount` sous macOS)
TYPES_RESEAU = ('cifs', 'smb3', 'smbfs', 'nfs', 'nfs4', 'fuse.sshfs', 'sshfs', 'afpfs', 'webdav', 'davfs',
                'fuse.rclone', '9p', 'fuse.gvfsd-fuse', 'fuse.kio-fuse', 'fuse.smbnetfs', 'ceph', 'glusterfs')


def _desechapper(champ: str) -> str:
    """/proc/mounts code espace, tabulation, saut de ligne et barre oblique inverse en octal (\\040…)."""
    for code, car in (('\\040', ' '), ('\\011', '\t'), ('\\012', '\n'), ('\\134', '\\')):
        champ = champ.replace(code, car)
    return champ


def lire_montages(texte: str | None = None) -> list[tuple[str, str, str]]:
    """[(point de montage, type, source)] d'après /proc/mounts (ou `texte`, pour les tests). Jamais d'exception."""
    if texte is None:
        try:
            with open('/proc/mounts', encoding='utf-8', errors='replace') as f:
                texte = f.read()
        except OSError:
            return []
    sortie = []
    for ligne in texte.splitlines():
        m = ligne.split()
        if len(m) >= 3:
            sortie.append((_desechapper(m[1]), m[2], _desechapper(m[0])))
    return sortie


def montages_reseau(texte: str | None = None) -> list[str]:
    """Points de montage des partages réseau (cifs, nfs, sshfs, gvfs…), dans l'ordre de /proc/mounts."""
    return [point for point, typ, _src in lire_montages(texte) if typ.lower() in TYPES_RESEAU]


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


def est_unc(chemin: str) -> bool:
    """``\\\\serveur\\partage`` ou ``//serveur/partage`` (hors préfixe de chemin long ``\\\\?\\``)."""
    c = str(chemin).replace('/', '\\')
    return c.startswith('\\\\') and not c.startswith('\\\\?\\') and not c.startswith('\\\\.\\')


def chemin_os(p: str) -> str:
    """Chemin tel que Windows le veut au-delà de ~250 caractères : préfixe ``\\\\?\\`` (chemins longs), et
    ``\\\\?\\UNC\\serveur\\partage\\…`` pour un partage réseau. Ailleurs : inchangé."""
    if os.name == 'nt' and len(p) > 250 and not p.startswith('\\\\?\\'):
        absolu = os.path.abspath(p)
        if est_unc(absolu):
            return '\\\\?\\UNC\\' + absolu.replace('/', '\\').lstrip('\\')
        return '\\\\?\\' + absolu
    return p


def uri_sqlite_lecture_seule(chemin: str, windows: bool | None = None) -> str:
    """URI SQLite en lecture seule (espaces, accents, « ? », « : » et « , » des chemins gvfs, UNC Windows).

    SQLite refuse une URI ``file://serveur/…`` (autorité non vide) : un chemin UNC s'écrit ``file:////serveur/…``,
    autorité vide et chemin ``//serveur/partage/…``, que Windows ouvre comme ``\\\\serveur\\partage\\…``."""
    windows = (os.name == 'nt') if windows is None else windows
    if windows and est_unc(str(chemin)):
        p = str(chemin).replace('\\', '/')
        return 'file://' + quote(p, safe='/') + '?mode=ro'
    return Path(chemin).resolve().as_uri() + '?mode=ro'


def emplacements_systeme(env: dict | None = None, montages_texte: str | None = None, uid: int | None = None,
                         existe=os.path.isdir) -> list[str]:
    """Emplacements à proposer dans la barre latérale du dialogue de fichiers de Qt (quand le système n'en fournit
    pas) : disques amovibles, montages, partages réseau montés (gvfs, cifs, nfs…). Seulement ceux qui existent."""
    env = os.environ if env is None else env
    sortie: list[str] = []

    def ajouter(p):
        if p and p not in sortie and existe(p):
            sortie.append(p)

    if sys.platform == 'darwin':
        ajouter('/Volumes')
        for point in montages_reseau(montages_texte) if montages_texte is not None else ():
            ajouter(point)
        return sortie
    if os.name == 'nt':
        return sortie
    utilisateur = env.get('USER') or env.get('LOGNAME') or ''
    uid = os.getuid() if uid is None else uid
    runtime = env.get('XDG_RUNTIME_DIR') or '/run/user/%d' % uid
    gvfs = os.path.join(runtime, 'gvfs')
    ajouter(gvfs)
    try:                                        # chaque partage ouvert dans Nautilus/Dolphin (smb-share:…) en direct
        if existe(gvfs):
            for nom in sorted(os.listdir(gvfs))[:12]:
                ajouter(os.path.join(gvfs, nom))
    except OSError:
        pass
    for point in montages_reseau(montages_texte):
        ajouter(point)
    if utilisateur:
        ajouter('/run/media/' + utilisateur)     # Arch, Manjaro, Fedora (udisks2)
        ajouter('/media/' + utilisateur)         # Debian, Ubuntu
    ajouter('/media')
    ajouter('/mnt')
    return sortie
