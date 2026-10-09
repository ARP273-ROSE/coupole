#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construit le paquet Debian/Ubuntu (.deb) de Coupole à partir du paquet Linux autonome.

Point de départ : `dist/<NomApp>/` tel que le laisse `build_unix.py` (CPython autonome dans `python/`, code dans
`app/`, lanceur `<NomApp>.sh`). Rien n'est reconstruit ici : le .deb RANGE ce paquet là où la politique Debian le
demande, et dit à apt de quelles bibliothèques système Qt a besoin.

    /opt/coupole/{python,app}                         le paquet autonome, tel quel (plus les .pyc précompilés)
    /usr/bin/coupole                                  lanceur : sans argument l'interface, avec arguments la ligne de commande
    /usr/share/applications/coupole.desktop           entrée de menu (Name[fr], Comment[fr])
    /usr/share/icons/hicolor/<taille>/apps/coupole.png + scalable/apps/coupole.svg
    /usr/share/doc/coupole/{copyright,changelog.gz,changelog.en.gz,README.md}
    /usr/share/man/man1/coupole.1.gz

Il n'a besoin que de Python et de `dpkg-deb` (paquet dpkg, présent sur toute machine Debian/Ubuntu) et ne demande pas
d'être root : `dpkg-deb --root-owner-group` attribue tout à root dans l'archive.

Usage :
    python3 build_deb.py [--version X.Y.Z] [--source dist/Coupole] [--arch amd64|arm64] [--sortie DOSSIER]

Résultat : `coupole_<version>_<arch>.deb` à la racine du dépôt, et sa copie au nom stable `coupole-linux-<arch>.deb`
(l'adresse `releases/latest/download/coupole-linux-amd64.deb` ne change donc jamais).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KIT = json.loads((ROOT / 'kit.json').read_text(encoding='utf-8'))
NOM = KIT['nom_fichier']                       # Coupole
TECH = KIT['nom_technique']                    # coupole
NOM_AFFICHE = KIT.get('nom_affiche', NOM)
POINT_ENTREE = KIT['point_entree']
DEPOT = KIT['depot_distribution']
MAINTENEUR = 'ARP273-ROSE <227281227+ARP273-ROSE@users.noreply.github.com>'
HOMEPAGE = 'https://github.com/%s' % DEPOT
PREFIXE = Path('opt') / TECH
TAILLES_ICONES = (16, 24, 32, 48, 64, 128, 256, 512)

# Bibliothèques système dont le paquet a besoin et qu'il n'embarque pas. Établies par `ldd` sur les bibliothèques
# Qt 6.11 de PyQt6 (libQt6Core, Gui, Widgets, DBus, Network, OpenGL, Svg, XcbQpa, WaylandClient, greffons) et sur
# l'interpréteur CPython de python-build-standalone, puis vérifiées en installant le paquet dans des conteneurs
# ubuntu:22.04 et ubuntu:24.04 nus (voir PROGRESSION.md). Qt embarque lui-même ICU, OpenSSL est statique dans
# CPython ; numpy, scipy, astropy, zstandard, lz4 et SEP n'ont besoin que de la glibc et de libstdc++.
# Les alternatives « t64 » couvrent la transition time_t 64 bits d'Ubuntu 24.04 / Debian 13 (les paquets renommés
# déclarent bien un Provides vers l'ancien nom, mais un nom explicite ne dépend pas de l'âge d'apt).
DEPENDS = [
    'libc6 (>= 2.28)', 'libstdc++6', 'libgcc-s1',
    'libglib2.0-0t64 | libglib2.0-0', 'libdbus-1-3',
    'libfontconfig1', 'libfreetype6', 'libpng16-16t64 | libpng16-16', 'libzstd1', 'zlib1g',
    'libgl1', 'libegl1', 'libopengl0',
    'libx11-6', 'libx11-xcb1', 'libxcb1', 'libxkbcommon0', 'libxkbcommon-x11-0',
    'libxcb-cursor0', 'libxcb-icccm4', 'libxcb-image0', 'libxcb-keysyms1', 'libxcb-randr0', 'libxcb-render0',
    'libxcb-render-util0', 'libxcb-shape0', 'libxcb-shm0', 'libxcb-sync1', 'libxcb-util1', 'libxcb-xfixes0',
    'libxcb-xkb1', 'libxcb-glx0',
    'libwayland-client0', 'libwayland-cursor0', 'libwayland-egl1',
    'libgssapi-krb5-2',                            # libQt6Network (authentification SPNEGO), lié dynamiquement
]
# Vérification réelle (9 oct. 2026) : après installation dans ubuntu:22.04 et ubuntu:24.04 nus, `ldd` sur tous les .so
# ne signale plus que libgtk-3/libcups (greffons facultatifs, dans Recommends) ; GUI offscreen et CLI hors ligne OK.
# Confort, jamais indispensables : thème GTK des boîtes de dialogue sous GNOME, portails xdg, ASTAP (facultatif).
RECOMMENDS = ['libgtk-3-0t64 | libgtk-3-0', 'libcups2t64 | libcups2', 'xdg-desktop-portal', 'fonts-dejavu-core']
SUGGESTS = ['astap']

DESCRIPTION_COURTE = 'toolbox for the DU ECU students (Observatoire de Paris) - FR/EN'
DESCRIPTION_LONGUE = """\
Coupole is a free toolbox for the students of the « Explorer et Comprendre
l'Univers » university diploma (DU ECU) of the Observatoire de Paris: OHP image
bank (TAP inventory, resumable downloads, astrometric checks, XISF / compressed
FITS conversion, stackable sets), image quality measurements, spectra and
series, cosmology calculator, observing sites and times. Graphical interface
(PyQt6) and complete command line, in French and English.
.
This package bundles its own Python interpreter and every library under
/opt/coupole; nothing else is needed. ASTAP (optional) is not included.
.
Coupole est une boîte à outils libre pour les étudiants du DU « Explorer et
Comprendre l'Univers » (DU ECU) de l'Observatoire de Paris : banque d'images de
l'OHP (inventaire TAP, téléchargement reprenable, contrôle astrométrique,
conversion XISF / FITS compressé, lots empilables), qualité des images,
spectres et séries, calculateur de cosmologie, sites et heures d'observation.
Interface graphique (PyQt6) et ligne de commande complète, en français et en
anglais. Ce paquet embarque son interpréteur Python et toutes ses bibliothèques
sous /opt/coupole ; rien d'autre n'est à installer. ASTAP (facultatif) n'est
pas inclus."""


def log(msg):
    print(f'  {msg}', flush=True)


def architecture_deb(valeur: str | None) -> str:
    if valeur:
        return valeur
    m = platform.machine().lower()
    if m in ('aarch64', 'arm64'):
        return 'arm64'
    if m in ('x86_64', 'amd64'):
        return 'amd64'
    raise SystemExit(f'Architecture non prise en charge : {m} (préciser --arch)')


def version_du_paquet(source: Path, voulue: str | None) -> str:
    """La version que le paquet annonce ; elle doit être celle demandée, sinon l'application proposerait sans fin
    une mise à jour déjà installée (même contrôle que release.yml)."""
    fichier = source / 'app' / KIT.get('fichier_version', 'VERSION')
    vue = fichier.read_text(encoding='utf-8').strip() if fichier.exists() else ''
    if voulue and vue and voulue != vue:
        raise SystemExit(f'Le paquet autonome annonce {vue!r} mais --version dit {voulue!r} : relancer build_unix.py.')
    v = voulue or vue
    if not v:
        raise SystemExit('Version introuvable (ni --version, ni app/VERSION).')
    return v


# ------------------------------------------------------------------------------------------------ arborescence
def copier_paquet(source: Path, racine: Path):
    """`python/` et `app/` sous /opt/coupole, droits conformes (0755 dossiers, 0644 fichiers, 0755 exécutables)."""
    cible = racine / PREFIXE
    cible.mkdir(parents=True)
    for nom in ('python', 'app'):
        shutil.copytree(source / nom, cible / nom, symlinks=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'reglages.json'))
    # Rien de ce que l'installeur « profil utilisateur » pose n'a sa place ici : le menu et le lanceur sont ceux du
    # système.
    for parasite in (cible / 'app' / f'{TECH}.desktop', cible / 'app' / 'installer.sh'):
        parasite.unlink(missing_ok=True)
    nb = 0
    for chemin in cible.rglob('*'):
        if chemin.is_symlink():
            continue
        if chemin.is_dir():
            chemin.chmod(0o755)
        else:
            chemin.chmod(0o755 if _executable(chemin) else 0o644)
            nb += 1
    log(f'/opt/{TECH} : {nb} fichiers')
    return cible


def _executable(chemin: Path) -> bool:
    """Seuls les vrais exécutables gardent le bit x : l'interpréteur, les ELF (bibliothèques comprises : c'est
    l'usage Debian pour les .so) et les scripts de bin/ ; pas un .py ou un .c qui l'avait reçu par accident."""
    if chemin.parent.name == 'bin':
        return True
    try:
        with open(chemin, 'rb') as f:
            debut = f.read(4)
    except OSError:
        return False
    return debut.startswith(b'\x7fELF')


def marquer_installation_systeme(cible: Path, arch: str):
    """Le fichier que `coupole.core.maj` lit pour savoir qu'il ne doit pas se mettre à jour par archive."""
    fiche = {'type': 'deb', 'architecture': arch, 'actif': f'{TECH}-linux-{arch}.deb',
             'commande': f'sudo apt install ./{TECH}-linux-{arch}.deb', 'prefixe': f'/{PREFIXE}'}
    (cible / 'app' / 'installation_systeme.json').write_text(json.dumps(fiche, indent=2, ensure_ascii=False) + '\n',
                                                              encoding='utf-8')


def precompiler(cible: Path):
    """Octets compilés (.pyc) écrits une fois pour toutes : /opt n'est pas inscriptible par l'utilisateur, sans eux
    Python recompilerait numpy, astropy et Qt à chaque démarrage. `unchecked-hash` : valides quels que soient les
    horodatages que dpkg restitue ; dpkg les retire avec le reste à la désinstallation puisqu'ils sont dans le paquet."""
    exe = cible / 'python' / 'bin' / 'python3'
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': ''}
    for dossier in (cible / 'app', cible / 'python' / 'lib'):
        r = subprocess.run([str(exe), '-m', 'compileall', '-q', '-j', '0', '--invalidation-mode', 'unchecked-hash',
                            str(dossier)], capture_output=True, text=True, env=env)
        if r.returncode not in (0, 1):     # 1 : un fichier n'a pas compilé (exemples Python 2 dans certaines dépendances)
            raise RuntimeError('compileall : ' + (r.stderr or r.stdout)[-2000:])
    for pyc in cible.rglob('*.pyc'):
        pyc.chmod(0o644)
    log(f'bytecode précompilé : {sum(1 for _ in cible.rglob("*.pyc"))} fichiers')


def lanceur(racine: Path):
    bin_ = racine / 'usr' / 'bin'
    bin_.mkdir(parents=True)
    script = bin_ / TECH
    script.write_text(
        '#!/bin/sh\n'
        f'# {NOM_AFFICHE} : sans argument, l\'interface graphique ; avec arguments, la ligne de commande\n'
        f'# (coupole --help). Installé par le paquet {TECH} ; les fichiers vivent sous /{PREFIXE}.\n'
        '# Les .pyc sont livrés par le paquet : ne pas en écrire ailleurs (dossier de modules utilisateur compris).\n'
        'export PYTHONDONTWRITEBYTECODE=1\n'
        f'exec "/{PREFIXE}/python/bin/python3" "/{PREFIXE}/app/{POINT_ENTREE}" "$@"\n', encoding='utf-8')
    script.chmod(0o755)


def entree_de_menu(racine: Path):
    apps = racine / 'usr' / 'share' / 'applications'
    apps.mkdir(parents=True)
    (apps / f'{TECH}.desktop').write_text(
        '[Desktop Entry]\n'
        'Type=Application\n'
        'Version=1.5\n'
        f'Name={NOM_AFFICHE}\n'
        f'Name[fr]={NOM_AFFICHE}\n'
        'GenericName=Astronomy toolbox\n'
        'GenericName[fr]=Boîte à outils d\'astronomie\n'
        'Comment=Toolbox for the DU ECU students (Observatoire de Paris): OHP image bank, image quality, cosmology\n'
        'Comment[fr]=Boîte à outils du DU « Explorer et Comprendre l\'Univers » (Observatoire de Paris) : banque OHP, '
        'qualité des images, cosmologie\n'
        f'Exec={TECH}\n'
        f'TryExec={TECH}\n'
        f'Icon={TECH}\n'
        'Terminal=false\n'
        f'StartupWMClass={TECH}\n'
        'Categories=Science;Astronomy;Education;\n'
        'Keywords=astronomy;FITS;XISF;OHP;telescope;cosmology;\n'
        'Keywords[fr]=astronomie;FITS;XISF;OHP;télescope;cosmologie;\n', encoding='utf-8')


def icones(racine: Path):
    hicolor = racine / 'usr' / 'share' / 'icons' / 'hicolor'
    for taille in TAILLES_ICONES:
        src = ROOT / 'logo' / f'{TECH}_{taille}.png'
        if not src.exists():
            continue
        dest = hicolor / f'{taille}x{taille}' / 'apps'
        dest.mkdir(parents=True)
        shutil.copyfile(src, dest / f'{TECH}.png')
        (dest / f'{TECH}.png').chmod(0o644)
    svg = ROOT / 'logo' / f'{TECH}.svg'
    if svg.exists():
        dest = hicolor / 'scalable' / 'apps'
        dest.mkdir(parents=True)
        shutil.copyfile(svg, dest / f'{TECH}.svg')
        (dest / f'{TECH}.svg').chmod(0o644)
    log(f'icônes : {sum(1 for _ in hicolor.rglob("*") if _.is_file())}')


def _gz(contenu: bytes, dest: Path):
    """gzip reproductible (sans horodatage ni nom), comme le veut lintian."""
    with open(dest, 'wb') as f:
        with gzip.GzipFile(fileobj=f, mode='wb', compresslevel=9, mtime=0) as g:
            g.write(contenu)
    dest.chmod(0o644)


def documentation(racine: Path, version: str, date: str):
    doc = racine / 'usr' / 'share' / 'doc' / TECH
    doc.mkdir(parents=True)
    annee = time.strftime('%Y')
    (doc / 'copyright').write_text(
        'Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n'
        f'Upstream-Name: {NOM_AFFICHE}\n'
        f'Upstream-Contact: {MAINTENEUR}\n'
        f'Source: {HOMEPAGE}\n'
        '\n'
        'Files: *\n'
        f'Copyright: 2026-{annee} ARP273-ROSE\n'
        'License: GPL-3+\n'
        '\n'
        f'Files: opt/{TECH}/python/*\n'
        'Copyright: 2001-2026 Python Software Foundation and contributors (CPython, python-build-standalone);\n'
        ' The Qt Company Ltd. and contributors (Qt 6, LGPL-3.0); Riverbank Computing Limited (PyQt6, GPL-3.0);\n'
        ' NumPy, SciPy, Astropy developers (BSD-3-Clause); Gregory Szorc (python-zstandard, BSD-3-Clause);\n'
        ' Jonathan Underwood (python-lz4, BSD-3-Clause); Kyle Barbary (SEP, LGPL-3.0 / MIT);\n'
        ' lxml contributors (BSD-3-Clause); Python Software Foundation (tzdata, Apache-2.0)\n'
        'License: other\n'
        ' Third-party libraries bundled unchanged with their own licences; each one keeps its licence text in its\n'
        f' .dist-info folder under /opt/{TECH}/python/lib/python3.*/site-packages/ (PyQt6 and Qt: GPL-3.0 and\n'
        ' LGPL-3.0, see PyQt6/Qt6 therein; CPython: PSF-2.0, see /opt/coupole/python/share or\n'
        ' https://docs.python.org/3/license.html).\n'
        '\n'
        'License: GPL-3+\n'
        ' This program is free software: you can redistribute it and/or modify it under the terms of the GNU\n'
        ' General Public License as published by the Free Software Foundation, either version 3 of the License,\n'
        ' or (at your option) any later version.\n'
        ' .\n'
        ' This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even\n'
        ' the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public\n'
        ' License for more details.\n'
        ' .\n'
        ' On Debian systems, the complete text of the GNU General Public License version 3 can be found in\n'
        ' /usr/share/common-licenses/GPL-3.\n', encoding='utf-8')
    (doc / 'copyright').chmod(0o644)
    # Historique : changelog.gz au format Debian (une entrée par version, tirée du CHANGELOG), et les CHANGELOG
    # complets (français, référence ; anglais) tels quels.
    _gz(changelog_debian(version).encode('utf-8'), doc / 'changelog.gz')
    for nom in ('CHANGELOG.md', 'CHANGELOG.en.md', 'README.md'):
        if (ROOT / nom).exists():
            shutil.copyfile(ROOT / nom, doc / nom)
            (doc / nom).chmod(0o644)

    man = racine / 'usr' / 'share' / 'man' / 'man1'
    man.mkdir(parents=True)
    page = (
        f'.TH COUPOLE 1 "{date}" "{NOM_AFFICHE} {version}" "User Commands"\n'
        '.SH NAME\n'
        f'{TECH} \\- toolbox for the DU ECU students (Observatoire de Paris) / boîte à outils du DU ECU\n'
        '.SH SYNOPSIS\n'
        f'.B {TECH}\n'
        '.br\n'
        f'.B {TECH}\n'
        '[\\fB\\-\\-lang\\fR fr|en] [\\fB\\-\\-json\\fR] \\fIcommand\\fR [\\fIarguments\\fR]\n'
        '.SH DESCRIPTION\n'
        f'Without argument, \\fB{TECH}\\fR opens the graphical interface. With arguments, it runs the command line:\n'
        'OHP image bank (catalogue, estimate, download, process, anomalies, all, new, reorganise), image quality,\n'
        'spectra and series, cosmology, sites, machine diagnosis, ASTAP assistant, sources, update check, reports.\n'
        f'Run \\fB{TECH} \\-\\-help\\fR for the full list in the language of the system (\\fB\\-\\-lang\\fR to force it).\n'
        '.PP\n'
        f'Sans argument, \\fB{TECH}\\fR ouvre l\'interface graphique ; avec des arguments, la ligne de commande\n'
        f'(\\fB{TECH} \\-\\-help\\fR). Manuel complet : \\fB{TECH} manuel\\fR (PDF, français et anglais).\n'
        '.SH FILES\n'
        f'.TP\n/{PREFIXE}\nInterpreter, libraries and application (managed by dpkg, not updated by the application).\n'
        '.TP\n~/.config/coupole, ~/.cache/coupole\nSettings, cache and reports of the user (kept on removal).\n'
        '.SH SEE ALSO\n'
        f'{HOMEPAGE}\n')
    _gz(page.encode('utf-8'), man / f'{TECH}.1.gz')


def changelog_debian(version: str) -> str:
    """Le CHANGELOG.md (## X.Y.Z — date, puis des « - » à plusieurs lignes) au format du changelog Debian."""
    import email.utils
    import re
    texte = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8') if (ROOT / 'CHANGELOG.md').exists() else ''
    entrees = re.split(r'^## ', texte, flags=re.M)[1:]
    sortie = []
    for bloc in entrees:
        titre, _, corps = bloc.partition('\n')
        v = titre.split('—')[0].strip()
        if not re.match(r'^\d+(\.\d+)*$', v):
            continue
        import textwrap
        puces = []
        for ligne in corps.splitlines():
            if ligne.startswith('- '):
                puces.append(ligne[2:].strip())
            elif ligne.startswith('  ') and puces:
                puces[-1] += ' ' + ligne.strip()
        lignes = []
        for puce in puces:                           # lignes ≤ 80 colonnes (lintian : debian-changelog-line-too-long)
            lignes.extend(textwrap.wrap(puce, width=76, initial_indent='  * ', subsequent_indent='    '))
        if not lignes:
            lignes = ['  * ' + titre.strip()]
        date = email.utils.format_datetime(email.utils.parsedate_to_datetime(email.utils.formatdate(localtime=True)))
        sortie.append(f'{TECH} ({v}) unstable; urgency=medium\n\n' + '\n'.join(lignes) +
                      f'\n\n -- {MAINTENEUR}  {date}\n')
    return '\n'.join(sortie) if sortie else (f'{TECH} ({version}) unstable; urgency=medium\n\n  * Version {version}.\n\n'
                                             f' -- {MAINTENEUR}  {email.utils.formatdate(localtime=True)}\n')


def scripts_mainteneur(debian: Path):
    """Rafraîchir les caches du bureau quand les outils existent ; jamais d'échec : un bureau absent (serveur) n'est
    pas une erreur d'installation."""
    postinst = (
        '#!/bin/sh\n'
        'set -e\n'
        'if [ "$1" = "configure" ]; then\n'
        '  if command -v update-desktop-database >/dev/null 2>&1; then\n'
        '    update-desktop-database -q /usr/share/applications || true\n'
        '  fi\n'
        '  if command -v gtk-update-icon-cache >/dev/null 2>&1 && [ -f /usr/share/icons/hicolor/index.theme ]; then\n'
        '    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true\n'
        '  fi\n'
        'fi\n'
        'exit 0\n')
    postrm = (
        '#!/bin/sh\n'
        'set -e\n'
        'case "$1" in\n'
        '  remove|purge)\n'
        '    if command -v update-desktop-database >/dev/null 2>&1; then\n'
        '      update-desktop-database -q /usr/share/applications || true\n'
        '    fi\n'
        '    if command -v gtk-update-icon-cache >/dev/null 2>&1 && [ -f /usr/share/icons/hicolor/index.theme ]; then\n'
        '      gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true\n'
        '    fi\n'
        '    ;;\n'
        'esac\n'
        'exit 0\n')
    for nom, contenu in (('postinst', postinst), ('postrm', postrm)):
        (debian / nom).write_text(contenu, encoding='utf-8')
        (debian / nom).chmod(0o755)


def taille_installee_ko(racine: Path) -> int:
    total = 0
    for chemin in racine.rglob('*'):
        if chemin.name == 'DEBIAN' or 'DEBIAN' in chemin.parts:
            continue
        if chemin.is_file() and not chemin.is_symlink():
            total += chemin.stat().st_size
    return (total + 1023) // 1024


def controle(debian: Path, racine: Path, version: str, arch: str):
    longue = '\n'.join((' ' + ligne) if ligne != '.' else ' .' for ligne in DESCRIPTION_LONGUE.splitlines())
    (debian / 'control').write_text(
        f'Package: {TECH}\n'
        f'Version: {version}\n'
        'Section: science\n'
        'Priority: optional\n'
        f'Architecture: {arch}\n'
        f'Maintainer: {MAINTENEUR}\n'
        f'Installed-Size: {taille_installee_ko(racine)}\n'
        f'Depends: {", ".join(DEPENDS)}\n'
        f'Recommends: {", ".join(RECOMMENDS)}\n'
        f'Suggests: {", ".join(SUGGESTS)}\n'
        f'Homepage: {HOMEPAGE}\n'
        f'Description: {DESCRIPTION_COURTE}\n'
        f'{longue}\n', encoding='utf-8')
    (debian / 'control').chmod(0o644)


def md5sums(debian: Path, racine: Path):
    lignes = []
    for chemin in sorted(racine.rglob('*')):
        if 'DEBIAN' in chemin.parts or not chemin.is_file() or chemin.is_symlink():
            continue
        rel = chemin.relative_to(racine).as_posix()
        lignes.append(f'{hashlib.md5(chemin.read_bytes()).hexdigest()}  {rel}\n')
    (debian / 'md5sums').write_text(''.join(lignes), encoding='utf-8')
    (debian / 'md5sums').chmod(0o644)


def construire(racine: Path, sortie: Path):
    if sortie.exists():
        sortie.unlink()
    # xz : lisible par tout dpkg depuis 2012 (zstd ne le serait pas par Debian 11). --root-owner-group : tout à
    # root sans fakeroot ni privilège.
    cmd = ['dpkg-deb', '--root-owner-group', '-Zxz', '-z6', '-b', str(racine), str(sortie)]
    log(' '.join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--version', default=None, help='version attendue (celle de app/VERSION par défaut)')
    ap.add_argument('--source', default=str(ROOT / 'dist' / NOM), help='paquet autonome produit par build_unix.py')
    ap.add_argument('--arch', default=None, choices=('amd64', 'arm64'), help='architecture Debian (détectée)')
    ap.add_argument('--sortie', default=str(ROOT), help='dossier où écrire le .deb')
    ap.add_argument('--sans-precompilation', action='store_true', help='ne pas livrer de .pyc (plus petit, plus lent)')
    args = ap.parse_args()

    source = Path(args.source).resolve()
    if not (source / 'python' / 'bin' / 'python3').exists() or not (source / 'app' / POINT_ENTREE).exists():
        raise SystemExit(f'Paquet autonome introuvable dans {source} : lancer d\'abord build_unix.py.')
    if shutil.which('dpkg-deb') is None:
        raise SystemExit('dpkg-deb introuvable (paquet dpkg).')
    arch = architecture_deb(args.arch)
    version = version_du_paquet(source, args.version)
    date = time.strftime('%Y-%m-%d')
    print(f'== {NOM_AFFICHE} {version} — paquet Debian {arch} ==')

    travail = ROOT / 'dist' / 'deb'
    racine = travail / f'{TECH}_{version}_{arch}'
    if racine.exists():
        shutil.rmtree(racine)
    racine.mkdir(parents=True)
    debian = racine / 'DEBIAN'
    debian.mkdir()
    debian.chmod(0o755)

    cible = copier_paquet(source, racine)
    marquer_installation_systeme(cible, arch)
    if not args.sans_precompilation:
        precompiler(cible)
    lanceur(racine)
    entree_de_menu(racine)
    icones(racine)
    documentation(racine, version, date)
    scripts_mainteneur(debian)
    controle(debian, racine, version, arch)
    md5sums(debian, racine)
    for d in racine.rglob('*'):
        if d.is_dir() and not d.is_symlink():
            d.chmod(0o755)

    sortie = Path(args.sortie).resolve() / f'{TECH}_{version}_{arch}.deb'
    construire(racine, sortie)
    stable = sortie.with_name(f'{TECH}-linux-{arch}.deb')
    shutil.copyfile(sortie, stable)
    log(f'paquet : {sortie.name} ({sortie.stat().st_size / 1e6:.1f} Mo), copie : {stable.name}')
    shutil.rmtree(racine, ignore_errors=True)
    print('== termine ==')


if __name__ == '__main__':
    main()
