r"""Ouvrir une image : application associée du système, « Ouvrir avec… » un logiciel d'astronomie qui sait VRAIMENT
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
    Vérifié aussi par décodage réel d'un de nos fichiers sur le poste d'un utilisateur (N.I.N.A. 3.3 nightly).
  ASTAP — page officielle (hnsky.org/astap.htm, 8/10/2026) : « Import … XISF (uncompressed) » ; .fits.fz Rice
    « from version 2026.07.16 », « GZIP compression is not supported ».
  Aladin — non vérifié pour le XISF et le .fits.fz : proposé pour le FITS seulement (format natif).

Lancement (0.1.12) — toujours le programme détecté, arguments en liste, jamais de shell, tout journalisé
(`core/lancement.py`) :
  PixInsight — Linux : le script `bin/PixInsight.sh`, pas le binaire : « the PixInsight core executable cannot be
    executed directly on Linux. You must use the launcher shell script instead: PixInsight.sh » (Juan Conejero,
    pixinsight.com/forum, fil 15197).  Ce script reconstruit ses arguments puis fait `eval "$dirname/$appname $args"`
    en n'entourant de guillemets que les arguments qui contiennent une espace (constaté sur le poste d'un utilisateur) : un
    chemin à `$`, `` ` ``, `'`, `"`, antislash, `(`, `*`… serait interprété → un tel chemin passe par un lien symbolique
    temporaire au nom sans caractère spécial (`lien_temporaire`).  Windows : `bin\PixInsight.exe <options>
    <fichier>` (forum, fil 14614 : « C:\Program Files\PixInsight\bin\PixInsight.exe --help »).  macOS :
    `open -a PixInsight.app <fichier>`, ou `open -n -a PixInsight.app --args -n <fichier>` pour une nouvelle
    instance (`open(1)` : -n « Open a new instance of the application », --args « All remaining arguments are passed
    to the opened application »).  Options du cœur (`PixInsight --help`, relevé sur le poste d'un utilisateur) : `-n[=slot]`
    nouvelle instance, `-y[=slot]` céder à une instance ouverte (par défaut), `-e` liste des instances ; slots 1 à 256
    (forum, fil 15888).  Essai réel (un utilisateur, Manjaro) : instance occupée → « Yielded execution to running application
    instance #1 », code 0, rien d'ouvert ; avec `-n` l'image s'ouvre.  D'où le réglage `pixinsight_instance`
    (défaut : nouvelle fenêtre).  Instance ouverte détectée par la présence du processus (`/proc/*/comm`, `pgrep`,
    `tasklist`) : `-e` lancerait le cœur à chaque menu.
  Siril — `siril <fichier>` ; flatpak : `flatpak run --file-forwarding org.free_astro.siril @@ <fichier> @@` (le
    fichier passe par le portail de documents si le bac à sable ne le voit pas ; manifeste Flathub :
    `--filesystem=host`, qui exclut /tmp, /run (sauf /run/media), /usr… ; un `flatpak override` peut le retirer).
  N.I.N.A. — n'ouvre pas d'image passée en argument : ses seules options sont -p/--profileid, -s/--sequencefile,
    -r/--runsequence, -x/--exitaftersequence, -d/--debug, -g/--disable-hardware-acceleration
    (NINA/Utility/CommandLineOptions.cs, github.com/isbeorn/nina) → grisé dans « Ouvrir avec », avec la raison.
  ASTAP, Aladin — `<programme> <fichier>`.
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from . import lancement
from .lancement import Lancement

log = logging.getLogger('coupole.lancement')

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
# logiciels qui n'ouvrent pas un fichier passé en argument (vérifié dans leur code) : grisés, avec la raison
SANS_FICHIER = {'nina': 'lg_raison_nina_argument'}
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
    # le script d'abord : le binaire seul ne démarre pas sous Linux (voir l'en-tête)
    e = _premier(['/opt/PixInsight/bin/PixInsight.sh', shutil.which('PixInsight.sh'), '/opt/PixInsight/bin/PixInsight',
                  shutil.which('PixInsight')])
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
        if lit.get(lg) and lg in SANS_FICHIER:
            out.append((lg, False, SANS_FICHIER[lg]))
        elif lit.get(lg):
            out.append((lg, True, ''))
        else:
            out.append((lg, False, RAISONS.get((nat, lg), 'lg_raison_non_verifie' if lg not in lit else 'lg_raison_format')))
    return out


# ------------------------------------------------------------------ lancement (0.1.12)
class ErreurLancement(Exception):
    def __init__(self, cle: str, detail: str = ''):
        super().__init__(cle)
        self.cle, self.detail = cle, detail


SURS_EVAL = frozenset(' _-.,/+=:@%')


def chemin_sur_pour_eval(chemin) -> bool:
    """Le chemin traverse-t-il sans dommage l'`eval` de PixInsight.sh (guillemets doubles seulement s'il contient
    une espace) ?  Lettres et chiffres (accents compris), espace et `_-.,/+=:@%` ; tout le reste (`$`, `` ` ``,
    `'`, `"`, antislash, `(`, `)`, `*`, `?`, `[`, `{`, `;`, `&`, `|`, `<`, `>`, `!`, `#`, `~`, tabulation…) non."""
    return all(c.isalnum() or c in SURS_EVAL for c in str(chemin))


def nom_sur(nom: str) -> str:
    n = ''.join(c if (c.isalnum() or c in '_-.,+=@%') else '_' for c in nom).strip('.') or 'image'
    return n


def _dossier_liens(dossier=None) -> str:
    if dossier:
        return str(dossier)
    uid = os.getuid() if hasattr(os, 'getuid') else 0
    base = os.path.join(tempfile.gettempdir(), 'coupole-liens-%d' % uid)
    if not chemin_sur_pour_eval(base):
        base = '/tmp/coupole-liens-%d' % uid
    return base


def lien_temporaire(chemin, dossier=None, age_max: float = 2 * 86400) -> str:
    """Lien symbolique vers `chemin`, dans un dossier temporaire privé, au nom sans caractère spécial ; les liens
    de plus de deux jours sont retirés (jamais leurs cibles).  Lève ErreurLancement si impossible."""
    base = _dossier_liens(dossier)
    try:
        os.makedirs(base, mode=0o700, exist_ok=True)
        maintenant = time.time()
        for d in os.listdir(base):
            sd = os.path.join(base, d)
            try:
                if os.path.isdir(sd) and not os.path.islink(sd) and maintenant - os.lstat(sd).st_mtime > age_max:
                    for x in os.listdir(sd):
                        os.unlink(os.path.join(sd, x))          # le lien, pas sa cible
                    os.rmdir(sd)
            except OSError:
                continue
        d = tempfile.mkdtemp(prefix='l', dir=base)
        lien = os.path.join(d, nom_sur(os.path.basename(str(chemin))))
        os.symlink(os.path.abspath(str(chemin)), lien)
    except OSError as e:
        raise ErreurLancement('lg_err_lien', str(e))
    if not chemin_sur_pour_eval(lien):
        raise ErreurLancement('lg_err_lien', lien)
    log.info('launch: special characters in %r, temporary link %s', str(chemin), lien)
    return lien


def pixinsight_ouvert(plateforme: str = sys.platform, racine_proc: str = '/proc') -> bool:
    """Une instance de PixInsight tourne-t-elle ?  Processus « PixInsight » (le cœur ; le script s'appelle
    PixInsight.sh).  Jamais d'exception ; False si on ne sait pas."""
    try:
        if plateforme.startswith('linux'):
            for d in os.listdir(racine_proc):
                if not d.isdigit():
                    continue
                try:
                    with open(os.path.join(racine_proc, d, 'comm'), encoding='utf-8', errors='replace') as f:
                        if f.read().strip() == 'PixInsight':
                            return True
                except OSError:
                    continue
            return False
        if plateforme == 'darwin':
            code, _ = lancement.executer(['pgrep', '-x', 'PixInsight'], 'pgrep', 2)
            return code == 0
        if plateforme == 'win32':
            code, sortie = lancement.executer(['tasklist', '/FI', 'IMAGENAME eq PixInsight.exe', '/NH'], 'tasklist', 3)
            return code == 0 and 'pixinsight.exe' in (sortie or '').lower()
    except Exception:
        return False
    return False


RESERVES_FLATPAK = ('/app', '/bin', '/boot', '/dev', '/efi', '/etc', '/lib', '/lib32', '/lib64', '/proc', '/root',
                    '/run', '/sbin', '/sys', '/tmp', '/usr', '/var')


def _sous(p: str, d: str) -> bool:
    d = d.rstrip('/') or '/'
    return p == d or p.startswith(d + '/') or d == '/'


def flatpak_voit(ident: str, chemin, permissions: str | None = None, maison: str | None = None) -> bool | None:
    """Le bac à sable flatpak `ident` voit-il `chemin` (`flatpak info --show-permissions`, réglages `override`
    compris) ?  None si on ne sait pas.  `host` : tout sauf les dossiers réservés (flatpak-metadata(5)), /run/media
    compris ; `home`, `~/…`, chemins absolus ; les entrées `!…` retirent l'accès."""
    if permissions is None:
        code, permissions = lancement.executer(['flatpak', 'info', '--show-permissions', ident], 'flatpak', 5)
        if code != 0:
            return None
    fs = []
    for ligne in (permissions or '').splitlines():
        if ligne.strip().startswith('filesystems='):
            fs = [x.strip() for x in ligne.split('=', 1)[1].split(';') if x.strip()]
    p = os.path.abspath(str(chemin))
    try:
        p = os.path.realpath(p)
    except OSError:
        pass
    maison = maison or os.path.expanduser('~')
    oui = non = False
    for e in fs:
        neg = e.startswith('!')
        e = e.lstrip('!').split(':')[0]
        if e == 'host':
            vu = _sous(p, '/run/media') or not any(_sous(p, r) for r in RESERVES_FLATPAK)
        elif e == 'home':
            vu = _sous(p, maison)
        elif e.startswith('~/'):
            vu = _sous(p, os.path.join(maison, e[2:]))
        elif e.startswith('/'):
            vu = _sous(p, e)
        else:
            continue
        if vu:
            non, oui = (True, oui) if neg else (non, True)
    return oui and not non


def _instance_voulue(nouvelle) -> bool:
    if nouvelle is not None:
        return bool(nouvelle)
    try:
        from . import config
        return config.reglages()['pixinsight_instance'] != 'envoyer'
    except Exception:
        return True


def preparer_commande(lg: str, commande: list, chemin, nouvelle: bool | None = None, plateforme: str = sys.platform,
                      dossier_liens=None, permissions_flatpak: str | None = None) -> tuple[list, list, dict]:
    """(argv, notes, paramètres) pour ouvrir `chemin` dans le logiciel `lg` lancé par `commande` (détection).
    Lève ErreurLancement si ce n'est pas possible proprement.  Jamais de shell."""
    commande = [str(c) for c in commande]
    p = os.path.abspath(str(chemin))
    notes, params = [], {}
    if not commande:
        raise ErreurLancement('lg_err_introuvable', lg)
    if lg in SANS_FICHIER:
        raise ErreurLancement(SANS_FICHIER[lg], NOMS.get(lg, lg))
    if lg == 'pixinsight':
        nouvelle = _instance_voulue(nouvelle)
        if plateforme == 'darwin' and commande[:2] == ['open', '-a']:
            app = commande[2]
            argv = ['open', '-n', '-a', app, '--args', '-n', p] if nouvelle else ['open', '-a', app, p]
            return argv, notes, params
        if plateforme == 'win32':
            return commande[:1] + (['-n'] if nouvelle else []) + [p], notes, params
        prog = commande[0]
        if os.path.basename(prog) == 'PixInsight':                 # le binaire : préférer son script
            sh = os.path.join(os.path.dirname(prog), 'PixInsight.sh')
            if os.path.isfile(sh):
                prog = sh
        script = prog.endswith('.sh')
        base = ['/bin/sh', prog] if script and not os.access(prog, os.X_OK) else [prog]
        if script and not chemin_sur_pour_eval(p):
            p = lien_temporaire(p, dossier_liens)
            notes.append('lg_note_pixinsight_lien')
        return base + (['-n'] if nouvelle else []) + [p], notes, params
    if commande[:2] == ['flatpak', 'run'] and len(commande) >= 3:
        ident = commande[2]
        vu = flatpak_voit(ident, p, permissions_flatpak)
        if vu is not True:
            notes.append('lg_note_flatpak_portail')
            params.update(ident=ident, dossier=os.path.dirname(p))
        # --file-forwarding : le portail de documents n'exporte le fichier que si le bac à sable ne le voit pas
        return ['flatpak', 'run', '--file-forwarding'] + commande[3:] + [ident, '@@', p, '@@'], notes, params
    return commande + [p], notes, params


# messages reconnus dans la sortie des premières secondes
MOTIFS_SORTIE = {'pixinsight': (('Yielded execution', 'lg_note_pixinsight_cede'),)}


def lancer_logiciel(lg: str, chemin, installes: dict | None = None, nouvelle: bool | None = None,
                    commande: list | None = None, **kw) -> Lancement:
    """Ouvre `chemin` dans le logiciel `lg` (programme détecté, liste d'arguments, journalisé)."""
    installes = detecter() if installes is None and commande is None else (installes or {})
    commande = commande or installes.get(lg)
    nom = NOMS.get(lg, lg)
    if not commande:
        return Lancement('logiciel', [str(chemin)], nom).echec('lg_err_introuvable', nom)
    try:
        argv, notes, params = preparer_commande(lg, commande, chemin, nouvelle, **kw)
    except ErreurLancement as e:
        l = Lancement('logiciel', list(commande) + [str(chemin)], nom)
        return l.echec(e.cle, e.detail)
    l = lancement.demarrer(argv, 'logiciel:' + lg, nom)
    l.notes.extend(notes)
    l.params.update(params)
    l.motifs = MOTIFS_SORTIE.get(lg, ())
    return l


def lancer(commande: list, chemin, logiciel: str = '') -> Lancement:
    """Compatibilité : lance `commande` + fichier (voir `lancer_logiciel`)."""
    lg = logiciel or next((k for k, v in detecter().items() if list(v) == list(commande)), '')
    return lancer_logiciel(lg, chemin, commande=commande) if lg else \
        lancement.demarrer(list(commande) + [str(chemin)], 'commande')


MOTS_LOGICIELS = (('pixinsight', 'pixinsight'), ('siril', 'siril'), ('astap', 'astap'), ('aladin', 'aladin'))


def logiciel_de_exec(exec_ligne: str, installes: dict | None = None) -> tuple[str, list]:
    """(logiciel, commande) reconnus dans une ligne Exec= d'un .desktop ; ('', []) sinon."""
    bas = (exec_ligne or '').lower()
    prog = lancement.programme_exec(exec_ligne)
    for lg, mot in MOTS_LOGICIELS:
        if mot in bas:
            installes = detecter() if installes is None else installes
            if installes.get(lg):
                return lg, list(installes[lg])
            if prog and os.path.isfile(prog):
                return lg, [prog]
    return '', []


def ouvrir_defaut(chemin, installes: dict | None = None, plateforme: str = sys.platform,
                  application: dict | None = None) -> Lancement | None:
    """Ouverture par l'application associée (double-clic, « Ouvrir »).  Linux : si le .desktop de l'application
    par défaut ne reçoit pas de fichier (Exec= sans %f/%F/%u/%U), xdg-open lancerait l'application vide → logiciel
    reconnu lancé directement ; sinon message (rien lancé).  None : aucun moyen (l'appelant essaie Qt)."""
    if plateforme.startswith('linux'):
        info = lancement.application_par_defaut(chemin) if application is None else application
        if info.get('fichier') and info.get('accepte_fichier') is False:
            lg, cmd = logiciel_de_exec(info.get('exec', ''), installes)
            if lg:
                log.info('default application %s does not receive files: %s launched directly', info['desktop'], lg)
                l = lancer_logiciel(lg, chemin, commande=cmd)
                l.notes.append('lg_note_desktop_sans_fichier')
                l.params.setdefault('desktop', info.get('desktop', ''))
                return l
            l = Lancement('xdg-open', [str(chemin)], info.get('desktop', ''))
            l.params['desktop'] = info.get('desktop', '')
            return l.echec('lg_err_desktop_sans_fichier', info.get('exec', ''))
    return lancement.ouvrir_systeme(chemin)


def montrer_dans_dossier(chemin) -> Lancement | None:
    """Ouvre le gestionnaire de fichiers sur le dossier, le fichier sélectionné quand le système le permet :
    Explorateur (/select,), Finder (open -R), gestionnaire freedesktop (D-Bus FileManager1.ShowItems : Dolphin,
    Nautilus, Nemo, Thunar…), sinon le dossier par xdg-open.  Journalisé ; None si aucun moyen."""
    p = os.path.abspath(str(chemin))
    dossier = p if os.path.isdir(p) else os.path.dirname(p)
    if os.name == 'nt':
        l = lancement.demarrer(['explorer', '/select,', p] if os.path.isfile(p) else ['explorer', dossier],
                               'explorer', 'Explorer')
        l.ignorer_code = True                  # explorer.exe rend 1 même quand il a ouvert la fenêtre
        return l
    if sys.platform == 'darwin':
        return lancement.demarrer(['open', '-R', p] if os.path.isfile(p) else ['open', dossier], 'open', 'Finder')
    if os.path.isfile(p) and shutil.which('gdbus'):
        from urllib.parse import quote
        uri = 'file://' + quote(p)
        code, _ = lancement.executer(['gdbus', 'call', '--session', '--dest', 'org.freedesktop.FileManager1',
                                      '--object-path', '/org/freedesktop/FileManager1', '--method',
                                      'org.freedesktop.FileManager1.ShowItems', "['%s']" % uri.replace("'", "%27"),
                                      ''], 'gdbus', 5)
        if code == 0:
            return lancement.fait('gdbus', ['FileManager1.ShowItems', p], 'FileManager1')
    return lancement.ouvrir_systeme(dossier)
