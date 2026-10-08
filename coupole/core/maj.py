"""Mise à jour automatique depuis les Releases GitHub (Windows, macOS, Linux).

D'après « updater.py » du kit et sa version multiplateforme de MountMonitor :
on ne télécharge jamais d'exécutable.  On récupère l'archive applicative
``coupole-app-<version>.zip`` (du Python pur), on l'extrait par le code et on
remplace le contenu du dossier ``app/`` du paquet autonome.  L'interpréteur
embarqué et les bibliothèques compilées (``python/``) ne bougent pas.

Installation par pip/pipx ou depuis les sources : la mise à jour n'est pas
appliquée par l'application (elle n'a pas à modifier un environnement Python
qu'elle ne possède pas) ; elle est seulement signalée, avec la commande à
lancer.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import ssl
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlparse

log = logging.getLogger(__name__)

# Dépôt de distribution : PUBLIC, à créer.  Tant qu'il n'existe pas, l'API répond 404
# et la vérification dit simplement « aucune mise à jour trouvée ».


def depot() -> str:
    from . import sources
    return sources.valeur('maj.depot')

PREFIXE = 'coupole-app-'
POINT_ENTREE = 'lancer.py'
PROTEGES = {'reglages.json'}
DELAI = 20
ARCHIVE_MAX = 200 * 2**20          # octets téléchargés : l'archive applicative fait ~5 Mo
CONTENU_MAX = 1024 * 2**20         # octets une fois dépliés (protection contre une « zip bomb »)
MEMBRES_MAX = 20000
HOTES = ('github.com', 'api.github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com')
SECTIONS = {'fr': ('Français', 'Francais'), 'en': ('English',)}


def version_tuple(t):
    t = (t or '').strip().lstrip('vV')
    parts = []
    for morceau in t.split('.'):
        chiffres = ''
        for ch in morceau:
            if not ch.isdigit():
                break
            chiffres += ch
        parts.append(int(chiffres) if chiffres else 0)
    return tuple(parts or [0])


def plus_recente(distante, locale_):
    return version_tuple(distante) > version_tuple(locale_)


def dossier_app() -> Path:
    """Dossier `app/` du paquet autonome (ou racine des sources)."""
    return Path(__file__).resolve().parents[2]


def est_paquet() -> bool:
    base = dossier_app().parent / 'python'
    return (base / 'python.exe').exists() or (base / 'bin' / 'python3').exists()


def plateforme() -> str:
    if sys.platform.startswith('win'):
        return 'windows'
    return 'macos' if sys.platform == 'darwin' else 'linux'


def notes_dans_la_langue(corps: str, langue: str) -> str:
    """Section « ## Français » ou « ## English » des notes de version."""
    if not corps:
        return corps
    titres = {t: lg for lg, ts in SECTIONS.items() for t in ts}
    blocs, courant, lignes = {}, None, []
    for ligne in corps.splitlines():
        nu = ligne.strip()
        if nu.startswith('## ') and nu[3:].strip() in titres:
            if courant:
                blocs[courant] = '\n'.join(lignes).strip()
            courant, lignes = titres[nu[3:].strip()], []
        elif courant:
            lignes.append(ligne)
    if courant:
        blocs[courant] = '\n'.join(lignes).strip()
    return blocs.get(langue) or blocs.get('en') or corps


def _de_confiance(url) -> bool:
    d = urlparse(url)
    h = (d.hostname or '').lower()
    return d.scheme == 'https' and (h in HOTES or h.endswith('.githubusercontent.com'))


def _ouvrir(url):
    if not _de_confiance(url):
        raise RuntimeError('refused URL: %s' % url)
    from .. import __version__
    req = urllib.request.Request(url, headers={'User-Agent': 'Coupole/%s' % __version__,
                                               'Accept': 'application/vnd.github+json'})
    return urllib.request.urlopen(req, timeout=DELAI, context=ssl.create_default_context())


def verifier(version_courante: str):
    """Renvoie {'version', 'url', 'taille', 'notes'} si une version plus récente existe, sinon None."""
    if not version_courante or not depot():
        return None
    try:
        with _ouvrir('https://api.github.com/repos/%s/releases/latest' % depot()) as r:
            data = json.load(r)
    except Exception as e:
        log.info('update check impossible: %s', e)
        return None
    tag = (data.get('tag_name') or '').lstrip('vV')
    if not tag or not plus_recente(tag, version_courante):
        return None
    candidates = [a for a in data.get('assets', [])
                  if (a.get('name') or '').lower().startswith(PREFIXE) and a['name'].lower().endswith('.zip')]
    choix = [a for a in candidates if '-%s.' % plateforme() in a['name'].lower()] or \
        [a for a in candidates if not any('-%s.' % p in a['name'].lower() for p in ('windows', 'macos', 'linux'))]
    return {'version': tag, 'url': choix[0]['browser_download_url'] if choix else '',
            'taille': choix[0].get('size', 0) if choix else 0, 'notes': data.get('body') or '',
            'page': data.get('html_url') or 'https://github.com/%s/releases/latest' % depot()}


def appliquer(maj: dict, progression=None) -> bool:
    """Télécharge l'archive et remplace le contenu de app/ ; restaure l'ancienne version en cas d'échec."""
    if not est_paquet():
        raise RuntimeError('not a standalone package: use pipx/pip to upgrade')
    if not maj.get('url'):
        raise RuntimeError('no application archive in this release')
    cible = dossier_app()
    tmp = Path(tempfile.mkdtemp(prefix='coupole-maj-'))
    archive = tmp / 'maj.zip'
    sauvegarde = tmp / 'precedent'
    try:
        with _ouvrir(maj['url']) as r, open(archive, 'wb') as f:
            total = int(r.headers.get('Content-Length') or maj.get('taille') or 0)
            if total > ARCHIVE_MAX:
                raise RuntimeError('archive too large: %d bytes' % total)
            fait = 0
            while True:
                b = r.read(65536)
                if not b:
                    break
                fait += len(b)
                if fait > ARCHIVE_MAX:
                    raise RuntimeError('archive too large')
                f.write(b)
                if progression:
                    progression(fait, total)
        extrait = tmp / 'contenu'
        with zipfile.ZipFile(archive) as z:
            verifier_archive(z, extrait)
            z.extractall(extrait)
            if os.name != 'nt':                    # zipfile ne restitue pas le bit d'exécution
                for info in z.infolist():
                    if (info.external_attr >> 16) & 0o111:
                        p = extrait / info.filename
                        if p.exists():
                            p.chmod(p.stat().st_mode | 0o111)
        entrees = list(extrait.iterdir())
        if len(entrees) == 1 and entrees[0].is_dir():
            extrait = entrees[0]
        if not (extrait / POINT_ENTREE).exists() or not (extrait / 'coupole').is_dir():
            raise RuntimeError('incomplete archive')
        sauvegarde.mkdir()
        for item in extrait.iterdir():
            if item.name in PROTEGES:
                continue
            dest = cible / item.name
            if dest.exists():
                shutil.move(str(dest), str(sauvegarde / item.name))
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        return True
    except Exception:
        log.exception('update failed')
        try:
            if sauvegarde.exists():
                for item in sauvegarde.iterdir():
                    dest = cible / item.name
                    if dest.is_dir():
                        shutil.rmtree(dest, ignore_errors=True)
                    elif dest.exists():
                        dest.unlink()
                    shutil.move(str(item), str(dest))
        except Exception:
            log.exception('restore failed')
        raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verifier_archive(z: 'zipfile.ZipFile', extrait: Path) -> None:
    """Refuse toute archive qui écrirait hors de `extrait` (zip slip : « ../ », chemin absolu, lecteur Windows),
    un lien symbolique, un nombre de membres ou un volume déplié déraisonnables."""
    infos = z.infolist()
    if len(infos) > MEMBRES_MAX:
        raise RuntimeError('suspicious archive: %d members' % len(infos))
    total = 0
    base = os.path.realpath(str(extrait))
    for info in infos:
        nom = info.filename
        if not nom or nom.startswith(('/', '\\')) or ':' in nom.split('/')[0] or '..' in nom.replace('\\', '/').split('/'):
            raise RuntimeError('suspicious archive: %s' % nom)
        cible = os.path.realpath(os.path.join(base, *nom.replace('\\', '/').split('/')))
        if os.path.commonpath([base, cible]) != base:
            raise RuntimeError('suspicious archive: %s' % nom)
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise RuntimeError('suspicious archive: symbolic link %s' % nom)
        total += info.file_size
        if total > CONTENU_MAX:
            raise RuntimeError('suspicious archive: unpacked size over %d bytes' % CONTENU_MAX)


def relancer() -> bool:
    try:
        base = dossier_app().parent / 'python'
        script = dossier_app() / POINT_ENTREE
        for exe in (base / 'pythonw.exe', base / 'bin' / 'python3'):
            if exe.exists():
                os.spawnv(os.P_NOWAIT, str(exe), [str(exe), str(script)])
                return True
        os.spawnv(os.P_NOWAIT, sys.executable, [sys.executable, '-m', 'coupole'])
        return True
    except Exception:
        log.exception('restart failed')
        return False


def commande_pip() -> str:
    """Commande à proposer quand l'application est installée par pip/pipx."""
    url = 'git+https://github.com/%s' % depot()
    return 'pipx install --force %s   |   python -m pip install --upgrade %s' % (url, url)
