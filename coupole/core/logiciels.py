"""Ouvrir une image : application associée du système, « Ouvrir avec… » un logiciel d'astronomie qui sait VRAIMENT
lire ce fichier, « Ouvrir l'emplacement » (fichier sélectionné dans le gestionnaire de fichiers).

Table de compatibilité (`LECTURE`) : chaque case vient d'une vérification, source citée (0.1.9, octobre 2026) ;
rien n'y est supposé.  « oui » = l'image s'ouvre avec ses vraies valeurs ; « non » = ne s'ouvre pas, ou s'ouvre
fausse (image blanche) ; une case absente = non vérifié (le logiciel n'est alors pas proposé).

  PixInsight — code de PCL (gitlab.com/pixinsight/PCL, master du 28/09/2026) : XISF.cpp l. 355-369 (codecs zlib,
    lz4, lz4hc, zstd, avec ou sans +sh), XISFReader.cpp l. 577-600 (bounds obligatoire pour un flottant) et
    l. 2417-2440 (NORMALIZE_FLOAT_IMAGE : écrêtage à bounds puis ramené à [0, 1]) ; FITS : format natif.
  Siril — essai réel des AppImage officielles (siril-cli load/stat/save, pixels comparés) : 1.2.0 et 1.2.6 « file
    type not supported » ; 1.4.0 et 1.4.4 lisent tous nos XISF bit à bit (zstd, zlib, lz4, lz4hc, +sh, sans
    compression) ; mais un flottant XISF est gardé tel quel, hors de la plage [0, 1] de Siril (statistiques
    × 65 535 : moyenne 71 751 725 au lieu de 1 094,9) — src/io/image_formats_libraries.c, readxisf() ne normalise
    pas, alors que le lecteur FITS le fait (« Normalizing input data to our float range [0, 1] », essayé).
    Paquets Debian 13 (1.2.6) et Ubuntu 24.04 (1.2.1) : sans lecteur XISF (essayé).
  N.I.N.A. — code (github.com/isbeorn/nina, étiquette Version-3.2 du 27/11/2025) : NINA.Image/FileFormat/XISF/
    XISF.cs l. 304-328 (lz4, lz4hc, zlib, avec ou sans +sh ; zstd ajouté le 8/01/2026, commit 75c05a0d, branche
    develop seulement) ; DataConverter/Float32Converter.cs l. 23 et FITS/CfitsioNative.cs ToUshortArray :
    (ushort)(valeur × 65 535), bounds jamais lu → un flottant en ADU donne une image blanche ; UInt16 lu tel quel.
    Vérifié aussi par décodage réel d'un de nos fichiers sur le PC de Kevin (N.I.N.A. 3.3 nightly).
  ASTAP — page officielle (hnsky.org/astap.htm, 8/10/2026) : « Import … XISF (uncompressed) » ; .fits.fz Rice
    « from version 2026.07.16 », « GZIP compression is not supported ».
  Aladin — non vérifié pour le XISF et le .fits.fz : proposé pour le FITS seulement (format natif).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------------ nature d'un fichier image
NATURES = ('xisf_flottant', 'xisf_entier', 'xisf_entier_zstd', 'xisf_brut_entier', 'xisf_brut_flottant',
           'fits_flottant', 'fits_entier', 'fz_flottant', 'fz_entier')

LOGICIELS = ('pixinsight', 'siril', 'nina', 'astap', 'aladin')
NOMS = {'pixinsight': 'PixInsight', 'siril': 'Siril', 'nina': 'N.I.N.A.', 'astap': 'ASTAP', 'aladin': 'Aladin'}

# nature → logiciel → (lit correctement ?, clé de la raison)
LECTURE = {
    'xisf_flottant': {'pixinsight': True, 'siril': False, 'nina': False, 'astap': False, 'aladin': False},
    'xisf_entier': {'pixinsight': True, 'siril': True, 'nina': True, 'astap': False, 'aladin': False},
    'xisf_entier_zstd': {'pixinsight': True, 'siril': True, 'nina': False, 'astap': False, 'aladin': False},
    'xisf_brut_entier': {'pixinsight': True, 'siril': True, 'nina': True, 'astap': True, 'aladin': False},
    'xisf_brut_flottant': {'pixinsight': True, 'siril': False, 'nina': False, 'astap': True, 'aladin': False},
    'fits_flottant': {'pixinsight': True, 'siril': True, 'nina': False, 'astap': True, 'aladin': True},
    'fits_entier': {'pixinsight': True, 'siril': True, 'nina': True, 'astap': True, 'aladin': True},
    'fz_flottant': {'siril': True, 'astap': False},
    'fz_entier': {'siril': True, 'astap': True},
}
# raison affichée (info-bulle) quand un logiciel installé ne convient pas
RAISONS = {
    ('xisf_flottant', 'siril'): 'lg_raison_siril_flottant', ('xisf_brut_flottant', 'siril'): 'lg_raison_siril_flottant',
    ('xisf_flottant', 'nina'): 'lg_raison_nina_flottant', ('xisf_brut_flottant', 'nina'): 'lg_raison_nina_flottant',
    ('fits_flottant', 'nina'): 'lg_raison_nina_flottant', ('xisf_entier_zstd', 'nina'): 'lg_raison_nina_zstd',
    ('xisf_flottant', 'astap'): 'lg_raison_astap_xisf', ('xisf_entier', 'astap'): 'lg_raison_astap_xisf',
    ('xisf_entier_zstd', 'astap'): 'lg_raison_astap_xisf', ('fz_flottant', 'astap'): 'lg_raison_astap_gzip',
}


def nature(chemin) -> str | None:
    """Nature d'un fichier image d'après son extension et, pour un XISF ou un FITS, son en-tête (premiers Ko
    seulement : une lecture, même sur un partage).  None si ce n'est pas une image connue."""
    p = str(chemin)
    bas = p.lower()
    try:
        if bas.endswith('.xisf'):
            with open(p, 'rb') as f:
                tete = f.read(65536)
            if not tete.startswith(b'XISF0100'):
                return None
            xml = tete[16:].decode('utf-8', 'replace')
            import re
            m = re.search(r'<Image\b[^>]*>', xml)
            balise = m.group(0) if m else ''
            fmt = re.search(r'sampleFormat="([^"]+)"', balise)
            flottant = bool(fmt and fmt.group(1).startswith('Float'))
            comp = re.search(r'compression="([^"]+)"', balise)
            if not comp:
                return 'xisf_brut_flottant' if flottant else 'xisf_brut_entier'
            if flottant:
                return 'xisf_flottant'
            return 'xisf_entier_zstd' if comp.group(1).startswith('zstd') else 'xisf_entier'
        if bas.endswith(('.fits.fz', '.fz')):
            with open(p, 'rb') as f:
                tete = f.read(2880 * 4)
            return 'fz_flottant' if b"ZBITPIX = " in tete and _bitpix(tete, b'ZBITPIX') < 0 else 'fz_entier'
        if bas.endswith(('.fits', '.fit', '.fts')):
            with open(p, 'rb') as f:
                tete = f.read(2880)
            return 'fits_flottant' if _bitpix(tete, b'BITPIX') < 0 else 'fits_entier'
    except OSError:
        return None
    return None


def _bitpix(tete: bytes, cle: bytes) -> int:
    for k in range(0, len(tete) - 79, 80):
        carte = tete[k:k + 80]
        if carte[:8].rstrip() == cle:
            try:
                return int(carte[10:].split(b'/')[0].strip())
            except ValueError:
                return 0
    return 0


def capables(nat: str | None) -> dict:
    """{logiciel: True (lit) | False (ne lit pas, ou faux)} ; logiciels non vérifiés absents."""
    return dict(LECTURE.get(nat or '', {}))


# ------------------------------------------------------------------ logiciels installés
def _premier(chemins) -> str:
    for c in chemins:
        try:
            if c and Path(c).exists():
                return str(c)
        except OSError:
            continue
    return ''


def _flatpak(ident: str) -> bool:
    return any(Path(d, 'app', ident).is_dir() for d in ('/var/lib/flatpak', str(Path.home() / '.local/share/flatpak')))


def detecter() -> dict:
    """{logiciel: commande (liste) à laquelle on ajoute le fichier} pour les logiciels trouvés sur cette machine :
    PATH, emplacements usuels, flatpak, /Applications (macOS), Program Files (Windows)."""
    out = {}
    h = Path.home()
    if sys.platform == 'darwin':
        for lg, apps in (('pixinsight', ['/Applications/PixInsight/PixInsight.app', '/Applications/PixInsight.app']),
                         ('siril', ['/Applications/Siril.app']),
                         ('astap', ['/Applications/ASTAP.app']),
                         ('aladin', ['/Applications/Aladin.app', '/Applications/AladinDesktop.app'])):
            a = _premier(apps + [str(h / 'Applications' / Path(x).name) for x in apps])
            if a:
                out[lg] = ['open', '-a', a]
        return out
    if sys.platform == 'win32':
        pf = [os.environ.get(v) for v in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)') if os.environ.get(v)]
        for lg, rel in (('pixinsight', ['PixInsight/bin/PixInsight.exe']),
                        ('siril', ['Siril/bin/siril.exe']),
                        ('astap', ['astap/astap.exe']),
                        ('aladin', ['Aladin/Aladin.exe', 'AladinDesktop/Aladin.exe'])):
            e = _premier([Path(b) / r for b in pf for r in rel] + [Path('C:/astap/astap.exe')] * (lg == 'astap'))
            if e:
                out[lg] = [e]
        nina = _premier([Path(b) / "N.I.N.A. - Nighttime Imaging 'N' Astronomy" / 'NINA.exe' for b in pf])
        if nina:
            out['nina'] = [nina]
        return out
    # Linux et autres Unix
    e = _premier(['/opt/PixInsight/bin/PixInsight.sh', '/opt/PixInsight/bin/PixInsight', shutil.which('PixInsight')])
    if e:
        out['pixinsight'] = [e]
    e = shutil.which('siril')
    if e:
        out['siril'] = [e]
    elif _flatpak('org.free_astro.siril'):
        out['siril'] = ['flatpak', 'run', 'org.free_astro.siril']
    # ASTAP : le programme graphique (astap_cli n'affiche rien)
    e = _premier([shutil.which('astap'), '/opt/astap/astap', '/usr/bin/astap', str(h / 'astap' / 'astap')])
    if e:
        out['astap'] = [e]
    e = shutil.which('aladin') or shutil.which('Aladin')
    if e:
        out['aladin'] = [e]
    elif _flatpak('fr.u_strasbg.aladin'):
        out['aladin'] = ['flatpak', 'run', 'fr.u_strasbg.aladin']
    return out


def propositions(chemin, installes: dict | None = None) -> list[tuple[str, bool, str]]:
    """[(logiciel, utilisable, clé de la raison)] pour les logiciels INSTALLÉS : utilisable seulement s'il lit
    vraiment ce fichier (table vérifiée) ; les autres viennent grisés avec la raison."""
    installes = detecter() if installes is None else installes
    nat = nature(chemin)
    lit = capables(nat)
    out = []
    for lg in LOGICIELS:
        if lg not in installes:
            continue
        if lit.get(lg):
            out.append((lg, True, ''))
        else:
            out.append((lg, False, RAISONS.get((nat, lg), 'lg_raison_non_verifie' if lg not in lit else 'lg_raison_format')))
    return out


def lancer(commande: list, chemin) -> bool:
    """Lance `commande` + fichier, détaché (le logiciel survit à Coupole) ; jamais d'exception."""
    try:
        kw = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
        if os.name == 'nt':
            kw['creationflags'] = 0x00000008 | 0x00000200            # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        else:
            kw['start_new_session'] = True
        subprocess.Popen(list(commande) + [str(chemin)], **kw)
        return True
    except Exception:
        return False


def montrer_dans_dossier(chemin) -> bool:
    """Ouvre le gestionnaire de fichiers sur le dossier, le fichier sélectionné quand le système le permet :
    Explorateur (/select,), Finder (open -R), gestionnaire freedesktop (D-Bus FileManager1.ShowItems : Dolphin,
    Nautilus, Nemo, Thunar…), sinon le dossier par xdg-open."""
    p = os.path.abspath(str(chemin))
    dossier = p if os.path.isdir(p) else os.path.dirname(p)
    try:
        if os.name == 'nt':
            subprocess.Popen(['explorer', '/select,', p] if os.path.isfile(p) else ['explorer', dossier])
            return True
        if sys.platform == 'darwin':
            subprocess.Popen(['open', '-R', p] if os.path.isfile(p) else ['open', dossier])
            return True
        if os.path.isfile(p) and shutil.which('gdbus'):
            from urllib.parse import quote
            uri = 'file://' + quote(p)
            r = subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.freedesktop.FileManager1',
                                '--object-path', '/org/freedesktop/FileManager1', '--method',
                                'org.freedesktop.FileManager1.ShowItems', "['%s']" % uri.replace("'", "%27"), ''],
                               capture_output=True, timeout=5)
            if r.returncode == 0:
                return True
        if shutil.which('xdg-open'):
            subprocess.Popen(['xdg-open', dossier], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
            return True
    except Exception:
        return False
    return False
