"""Mise à jour automatique : le module commun du kit (`updater.py`, identique au gabarit, réglé par kit.json), plus
ce qui est propre à Coupole autour de lui.

Le kit fait le travail : il interroge les Releases du dépôt de distribution, choisit l'archive applicative
(`coupole-app-X.Y.Z.zip`), vérifie sa taille et son empreinte (SHA256SUMS), refuse les archives suspectes, remplace
`app/` en gardant l'ancienne version de côté et relance l'application ; il reconnaît le paquet Windows comme ceux de
macOS et de Linux.

Ce module garde ce que le kit ne sait pas : une installation par le paquet système `.deb` (Debian, Ubuntu) ou dans
un dossier non inscriptible ne se met pas à jour par archive — l'application indique alors le `.deb` de la Release
et la commande `apt` ; une installation par pip propose la commande pip ; le lanceur Linux des paquets ≤ 0.1.7 est
réparé.  L'interface (dialogues.verifier_maj) n'appelle que ce module.
"""
from __future__ import annotations

import importlib
import json
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)

POINT_ENTREE = 'lancer.py'
# Posé par build_deb.py dans app/ : dit à l'application qu'elle est installée par un paquet système.
MARQUEUR_SYSTEME = 'installation_systeme.json'


def kit(nom: str):
    """Module commun du kit (`updater`, `reporting`, `interface_kit`) : à côté de lancer.py dans un paquet, à la
    racine du dépôt depuis les sources, installé avec Coupole par pip."""
    try:
        return importlib.import_module(nom)
    except ImportError:
        racine = str(Path(__file__).resolve().parents[2])
        if racine not in sys.path:
            sys.path.append(racine)
        return importlib.import_module(nom)


def _u():
    return kit('updater')


def depot() -> str:
    """Dépôt de distribution (kit.json), sinon celui du fichier de sources."""
    try:
        r = _u().REPO
    except Exception:
        r = ''
    if r:
        return r
    from . import sources
    return sources.valeur('maj.depot')


def version_tuple(t):
    return _u()._version_tuple(t)


def plus_recente(distante, locale_) -> bool:
    return _u().is_newer(distante, locale_)


def notes_dans_la_langue(corps: str, langue: str) -> str:
    """Section « ## Francais » ou « ## English » des notes de version (celle du kit ; « Français » accentué des
    anciennes Releases de Coupole reconnu aussi)."""
    return _u().notes_dans_la_langue((corps or '').replace('## Français', '## Francais'), langue)


def _de_confiance(url) -> bool:
    return _u()._hote_de_confiance(url)


def dossier_app() -> Path:
    """Dossier `app/` du paquet autonome (ou racine des sources)."""
    return Path(__file__).resolve().parents[2]


def est_paquet() -> bool:
    base = dossier_app().parent / 'python'
    return (base / 'python.exe').exists() or (base / 'bin' / 'python3').exists()


def installation_systeme() -> dict | None:
    """Fiche du paquet système (`.deb`…) qui a installé Coupole, ou None.

    Clés : ``type`` (« deb »), ``architecture`` (« amd64 », « arm64 »), ``actif`` (nom stable du fichier dans la
    Release), ``commande`` (ce qu'il faut lancer pour installer la nouvelle version).
    """
    marqueur = dossier_app() / MARQUEUR_SYSTEME
    if not marqueur.exists():
        return None
    try:
        fiche = json.loads(marqueur.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'type': 'systeme'}
    return fiche if isinstance(fiche, dict) else {'type': 'systeme'}


def type_installation() -> str:
    """« deb » (paquet système, /opt, géré par dpkg), « paquet » (autonome, se met à jour seul), « pip »."""
    fiche = installation_systeme()
    if fiche:
        return fiche.get('type') or 'systeme'
    if not est_paquet():
        return 'pip'
    # Paquet autonome posé dans un dossier que l'utilisateur ne peut pas modifier (copie sous /opt faite à la main,
    # compte administrateur…) : l'archive ne pourrait pas s'appliquer ; on le dit plutôt que d'échouer à mi-chemin.
    if not os.access(dossier_app(), os.W_OK):
        return 'systeme'
    return 'paquet'


def peut_appliquer() -> bool:
    """L'application peut-elle installer elle-même l'archive applicative ?"""
    return type_installation() == 'paquet'


def _architecture_deb() -> str:
    import platform
    return 'arm64' if platform.machine().lower() in ('aarch64', 'arm64') else 'amd64'


def plateforme() -> str:
    return _u().plateforme()


def verifier(version_courante: str):
    """{'version', 'url', 'taille', 'notes', 'page', 'deb', 'deb_nom', 'kit'} si une version plus récente est publiée,
    sinon None.  `kit` : la description du module commun, que `appliquer` lui rend telle quelle."""
    if not version_courante or not depot():
        return None
    u = _u()
    if not u.REPO:                      # paquet sans kit.json (sources anciennes) : dépôt du fichier de sources
        u.REPO = depot()
        u.API_LATEST = 'https://api.github.com/repos/%s/releases/latest' % u.REPO
    m = u.check(version_courante)
    if not m:
        return None
    # Le paquet Debian/Ubuntu de cette architecture : le nom stable (coupole-linux-amd64.deb) d'abord, sinon le nom
    # versionné (coupole_0.1.1_amd64.deb) ; une installation .deb s'en sert pour dire quoi télécharger.
    arch = _architecture_deb()
    debs = [a for a in m.get('actifs', []) if a['nom'].lower().endswith(('_%s.deb' % arch, '-%s.deb' % arch))]
    debs.sort(key=lambda a: 0 if a['nom'].lower() == 'coupole-linux-%s.deb' % arch else 1)
    return {'version': m['version'], 'url': m['url'], 'taille': m.get('size', 0), 'notes': m.get('notes', ''),
            'page': m.get('page') or 'https://github.com/%s/releases/latest' % depot(),
            'deb': debs[0]['url'] if debs else '', 'deb_nom': debs[0]['nom'] if debs else '', 'kit': m}


def appliquer(maj: dict, progression=None) -> bool:
    """Télécharge l'archive et remplace le contenu de app/ (module commun du kit) ; l'ancienne version est restaurée
    en cas d'échec."""
    if not est_paquet():
        raise RuntimeError('not a standalone package: use pipx/pip to upgrade')
    if type_installation() != 'paquet':
        raise RuntimeError('system package (%s): install the new package instead' % type_installation())
    if not maj.get('url'):
        raise RuntimeError('no application archive in this release')
    m = dict(maj.get('kit') or {'version': maj.get('version', ''), 'url': maj['url'], 'size': maj.get('taille', 0),
                                 'nom': '', 'sha256sums_url': ''})
    return _u().download_and_apply(m, progression)


def relancer() -> bool:
    return _u().restart()


def commande_pip() -> str:
    """Commande à proposer quand l'application est installée par pip/pipx."""
    url = 'git+https://github.com/%s' % depot()
    return 'pipx install --force %s   |   python -m pip install --upgrade %s' % (url, url)


def consigne_systeme(maj: dict | None = None) -> dict:
    """Quoi télécharger et quoi lancer quand Coupole est installé par un paquet système.

    Renvoie ``{'fichier', 'url', 'commande', 'page'}`` ; l'adresse vient de la Release si elle a été lue, sinon du
    nom stable du fichier (``releases/latest/download/…``).
    """
    fiche = installation_systeme() or {}
    arch = fiche.get('architecture') or _architecture_deb()
    fichier = fiche.get('actif') or 'coupole-linux-%s.deb' % arch
    page = (maj or {}).get('page') or 'https://github.com/%s/releases/latest' % depot()
    url = (maj or {}).get('deb') or 'https://github.com/%s/releases/latest/download/%s' % (depot(), fichier)
    if (maj or {}).get('deb_nom'):
        fichier = maj['deb_nom']
    commande = fiche.get('commande') or 'sudo apt install ./%s' % fichier
    if fichier not in commande:
        commande = 'sudo apt install ./%s' % fichier
    return {'fichier': fichier, 'url': url, 'commande': commande, 'page': page}


# Lanceur du paquet Linux autonome, identique à celui qu'écrit build_unix.py (vérifié par les tests) : il suit les
# liens symboliques (~/.local/bin/coupole -> Coupole.sh). La mise à jour automatique ne remplace que app/ : le
# lanceur d'un paquet 0.1.7 ou antérieur est donc réécrit par l'application elle-même (`reparer_lanceur`).
LANCEUR_LINUX = ('#!/bin/sh\n'
                 '# Lanceur : tout est relatif au dossier du paquet, rien n\'est\n'
                 '# installe dans le systeme.\n'
                 'CIBLE="$0"\n'
                 'while [ -L "$CIBLE" ]; do\n'
                 '    LIEN=$(readlink "$CIBLE")\n'
                 '    case "$LIEN" in\n'
                 '        /*) CIBLE="$LIEN" ;;\n'
                 '        *) CIBLE="$(dirname "$CIBLE")/$LIEN" ;;\n'
                 '    esac\n'
                 'done\n'
                 'ICI=$(cd "$(dirname "$CIBLE")" && pwd)\n'
                 'exec "$ICI/python/bin/python3" "$ICI/app/lancer.py" "$@"\n')


def reparer_lanceur(racine: Path | None = None) -> bool:
    """Réécrit `Coupole.sh` d'un paquet Linux autonome antérieur à la 0.1.8 (qui ne suivait pas les liens
    symboliques). Rend True s'il a été réécrit. Jamais d'exception ; ne touche à rien d'autre."""
    try:
        if racine is None:
            if not sys.platform.startswith('linux') or type_installation() != 'paquet':
                return False
            racine = dossier_app().parent
        lanceur = Path(racine) / 'Coupole.sh'
        if not lanceur.is_file() or lanceur.is_symlink():
            return False
        actuel = lanceur.read_text(encoding='utf-8', errors='replace')
        if actuel == LANCEUR_LINUX or not actuel.startswith('#!/bin/sh') or 'dirname "$0"' not in actuel or \
                'while [ -L' in actuel or 'app/lancer.py' not in actuel:
            return False
        tmp = lanceur.with_name('.Coupole.sh.tmp')
        tmp.write_text(LANCEUR_LINUX, encoding='utf-8')
        tmp.chmod(lanceur.stat().st_mode | 0o111)
        os.replace(tmp, lanceur)
        log.info('launcher rewritten to follow symbolic links: %s', lanceur)
        return True
    except Exception as e:
        log.warning('launcher not rewritten: %s', e)
        return False
