"""Intégration au système : dialogues de fichiers natifs et traductions des textes fournis par Qt.

Sous Linux, le Qt embarqué dans le paquet autonome ne peut pas charger le greffon de thème du bureau installé sur
le système (celui de KDE Plasma, compilé pour une autre version de Qt) : il retombait sur le dialogue de fichiers
générique de Qt, en anglais et sans les emplacements du système (partages réseau, disques montés). Le remède est
le **portail XDG** (``org.freedesktop.portal.Desktop``), service D-Bus du bureau : Qt lui délègue le choix du
fichier, et c'est le vrai explorateur du système qui s'ouvre (Dolphin sous KDE, Nautilus sous GNOME…).

La variable ``QT_QPA_PLATFORMTHEME`` doit être posée **avant** la création de ``QApplication`` : la décision se prend
donc sans Qt, par des tests légers (fichiers de service D-Bus, puis au besoin une question au bus de session
bornée à une seconde). Ce module n'importe rien de Qt au chargement.
"""
from __future__ import annotations

import glob
import logging
import os
import shutil
import subprocess
import sys

log = logging.getLogger(__name__)

PORTAIL = 'org.freedesktop.portal.Desktop'
INTERFACE_FICHIERS = 'org.freedesktop.impl.portal.FileChooser'
# bureaux dont les dialogues natifs sont ceux de GTK (Qt ajoute de lui-même « gtk3 » pour eux)
BUREAUX_GTK = ('gnome', 'unity', 'x-cinnamon', 'cinnamon', 'xfce', 'mate', 'pantheon', 'budgie', 'lxde', 'deepin')
PLATEFORMES_SANS_ECRAN = ('offscreen', 'minimal', 'vnc', 'linuxfb', 'eglfs')

# décision prise au démarrage (consultée par les dialogues et les Préférences)
decision = {'theme': None, 'raison': 'non_decide'}


# ---------------------------------------------------------------------------------------------------- décision pure
def decider_theme(env: dict, *, plateforme: str, preference: str = 'systeme', portail: bool = False,
                  gtk3: bool = False) -> tuple[str | None, str]:
    """Valeur à donner à ``QT_QPA_PLATFORMTHEME`` (None : n'y rien changer) et la raison du choix.

    `portail` : le portail XDG est joignable et sait choisir des fichiers ; `gtk3` : le greffon GTK 3 de Qt et la
    bibliothèque GTK 3 du système sont présents. Fonction pure (testée sans bureau ni bus)."""
    if env.get('QT_QPA_PLATFORMTHEME'):
        return None, 'utilisateur'                 # posée par l'utilisateur ou la distribution : on la respecte
    if not plateforme.startswith('linux'):
        return None, 'natif'                       # Windows et macOS : dialogues natifs sans greffon à choisir
    if preference == 'qt':
        return None, 'preference_qt'
    if env.get('QT_QPA_PLATFORM', '').split(':')[0] in PLATEFORMES_SANS_ECRAN:
        return None, 'sans_ecran'
    if not (env.get('DISPLAY') or env.get('WAYLAND_DISPLAY')):
        return None, 'sans_ecran'
    if portail:
        return 'xdgdesktopportal', 'portail'
    bureaux = [b.strip().lower() for b in env.get('XDG_CURRENT_DESKTOP', '').split(':') if b.strip()]
    if gtk3 and any(b in BUREAUX_GTK for b in bureaux):
        return 'gtk3', 'gtk3'
    return None, 'repli_qt'


# ---------------------------------------------------------------------------------------------------- sondes
def _dossiers_donnees(env: dict) -> list[str]:
    maison = env.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')
    autres = (env.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':')
    vus, sortie = set(), []
    # les dossiers usuels en plus, sauf si on les écarte explicitement (tests : COUPOLE_XDG_SEULS)
    usuels = [] if env.get('COUPOLE_XDG_SEULS') else ['/usr/share', '/usr/local/share']
    for d in [maison] + autres + usuels:
        if d and d not in vus:
            vus.add(d)
            sortie.append(d)
    return sortie


def _bus_de_session(env: dict) -> bool:
    if env.get('DBUS_SESSION_BUS_ADDRESS'):
        return True
    runtime = env.get('XDG_RUNTIME_DIR') or '/run/user/%d' % os.getuid()
    return os.path.exists(os.path.join(runtime, 'bus'))


UNITES_SYSTEMD = ('/usr/lib/systemd/user', '/lib/systemd/user', '/etc/systemd/user')


def _service_installe(env: dict, unites=UNITES_SYSTEMD) -> bool:
    """Le portail est-il activable (fichier de service D-Bus ou unité systemd utilisateur) ?"""
    for d in _dossiers_donnees(env):
        if os.path.isfile(os.path.join(d, 'dbus-1', 'services', PORTAIL + '.service')):
            return True
    for d in unites:
        if os.path.isfile(os.path.join(d, 'xdg-desktop-portal.service')):
            return True
    return False


def _moteur_fichiers(env: dict) -> bool | None:
    """Un moteur du portail (kde, gtk, gnome, lxqt…) sait-il choisir des fichiers ? None : impossible à dire."""
    vu_un = False
    for d in _dossiers_donnees(env):
        for f in glob.glob(os.path.join(d, 'xdg-desktop-portal', 'portals', '*.portal')):
            vu_un = True
            try:
                with open(f, encoding='utf-8', errors='replace') as h:
                    if INTERFACE_FICHIERS in h.read():
                        return True
            except OSError:
                continue
    return False if vu_un else None


def _nom_sur_le_bus(delai: float = 1.0) -> bool:
    """Le portail tourne-t-il déjà (nom pris sur le bus de session) ? Question bornée à `delai` secondes."""
    for outil, args in (('dbus-send', ['--session', '--print-reply', '--reply-timeout=%d' % int(delai * 1000),
                                       '--dest=org.freedesktop.DBus', '/org/freedesktop/DBus',
                                       'org.freedesktop.DBus.NameHasOwner', 'string:' + PORTAIL]),
                        ('gdbus', ['call', '--session', '--timeout', str(max(1, int(delai))),
                                   '--dest', 'org.freedesktop.DBus', '--object-path', '/org/freedesktop/DBus',
                                   '--method', 'org.freedesktop.DBus.NameHasOwner', PORTAIL])):
        exe = shutil.which(outil)
        if not exe:
            continue
        try:
            r = subprocess.run([exe] + args, capture_output=True, text=True, timeout=delai + 0.5,
                               stdin=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            return False
        return r.returncode == 0 and 'true' in r.stdout
    return False


def portail_disponible(env: dict | None = None, delai: float = 1.0, unites=UNITES_SYSTEMD) -> bool:
    """Portail XDG joignable et capable d'ouvrir un sélecteur de fichiers. Jamais d'exception, jamais long."""
    env = os.environ if env is None else env
    try:
        if not _bus_de_session(env):
            return False
        moteur = _moteur_fichiers(env)
        if moteur is False:
            return False                           # portail présent mais aucun moteur ne choisit de fichiers
        return _service_installe(env, unites) or _nom_sur_le_bus(delai)
    except Exception:
        return False


def dossier_qt(quoi: str) -> str:
    """Dossier des greffons ('plugins') ou des traductions ('translations') du Qt réellement chargé."""
    try:
        from PyQt6.QtCore import QLibraryInfo
        lp = QLibraryInfo.LibraryPath
        chemin = QLibraryInfo.path(lp.PluginsPath if quoi == 'plugins' else lp.TranslationsPath)
        if chemin and os.path.isdir(chemin):
            return chemin
        import PyQt6
        repli = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', quoi)
        return repli if os.path.isdir(repli) else chemin
    except Exception:
        return ''


def gtk3_disponible() -> bool:
    """Greffon GTK 3 de Qt présent et bibliothèque GTK 3 installée sur le système."""
    greffon = os.path.join(dossier_qt('plugins'), 'platformthemes', 'libqgtk3.so')
    if not os.path.isfile(greffon):
        return False
    motifs = ('/usr/lib/libgtk-3.so.0', '/usr/lib64/libgtk-3.so.0', '/usr/lib/*-linux-gnu*/libgtk-3.so.0',
              '/lib/*-linux-gnu*/libgtk-3.so.0', '/usr/local/lib/libgtk-3.so.0')
    if any(glob.glob(m) for m in motifs):              # emplacements usuels : aucun sous-processus
        return True
    try:
        import ctypes.util
        return ctypes.util.find_library('gtk-3') is not None
    except Exception:
        return False


def preparer(preference: str = 'systeme', env=None) -> tuple[str | None, str]:
    """À appeler AVANT ``QApplication`` : pose ``QT_QPA_PLATFORMTHEME`` s'il y a mieux que le dialogue de Qt."""
    env = os.environ if env is None else env
    portail = gtk3 = False
    if sys.platform.startswith('linux') and not env.get('QT_QPA_PLATFORMTHEME') and preference != 'qt':
        if env.get('DISPLAY') or env.get('WAYLAND_DISPLAY'):
            portail = portail_disponible(env)
            if not portail:
                gtk3 = gtk3_disponible()
    theme, raison = decider_theme(dict(env), plateforme=sys.platform, preference=preference, portail=portail,
                                  gtk3=gtk3)
    if theme:
        env['QT_QPA_PLATFORMTHEME'] = theme
        env['COUPOLE_QPA_THEME_POSE'] = theme    # retiré de l'environnement des programmes lancés (core/lancement)
    decision.update(theme=theme or env.get('QT_QPA_PLATFORMTHEME') or None, raison=raison)
    log.info('file dialogs: platform theme %s (%s)', decision['theme'], raison)
    return theme, raison


def dialogue_natif_attendu() -> bool:
    """Le système fournira-t-il ses propres dialogues (sinon : dialogue de Qt, à enrichir) ?"""
    if not sys.platform.startswith('linux'):
        return True
    return decision['raison'] in ('portail', 'gtk3', 'utilisateur')


# ---------------------------------------------------------------------------------------------------- traductions Qt
_traducteurs: list = []

# Textes que le catalogue français de Qt 6 ne traduit pas encore (libellés du dialogue de fichiers de repli, avec
# raccourci clavier depuis Qt 6) : vérifié en ouvrant ce dialogue avec qtbase_fr.qm (tests/test_dialogues_systeme.py).
COMPLEMENTS = {
    'fr': {('QFileDialog', '&Look in:'): '&Voir dans\u00a0:',
           ('QFileDialog', 'Files of &type:'): 'Fichiers de &type\u00a0:'},
}


def _complement(app, table: dict):
    from PyQt6.QtCore import QTranslator

    class Complement(QTranslator):
        def translate(self, contexte, source, desambiguation=None, n=-1):
            return table.get((contexte, source))     # None (chaîne nulle) : Qt interroge le traducteur suivant

        def isEmpty(self):
            return not table
    return Complement(app)


def installer_traductions(app, langue: str) -> bool:
    """Charge les textes de Qt (boutons standard, dialogue de fichiers de repli, menus des champs) dans `langue`.

    Rappelée à chaque changement de langue : les traducteurs précédents sont retirés. Retourne True si un catalogue
    a été chargé (l'anglais n'en a pas besoin : c'est la langue des textes source de Qt)."""
    from PyQt6.QtCore import QCoreApplication, QTranslator
    for t in _traducteurs:
        QCoreApplication.removeTranslator(t)
    _traducteurs.clear()
    if not langue or langue == 'en':
        return False
    dossier = dossier_qt('translations')
    charge = False
    for catalogue in ('qtbase', 'qt'):          # qtbase : boutons, dialogues ; qt : méta-catalogue (repli)
        t = QTranslator(app)
        if t.load('%s_%s' % (catalogue, langue), dossier):
            QCoreApplication.installTranslator(t)
            _traducteurs.append(t)
            charge = True
            break
    if not charge:
        log.warning('Qt translations for %r not found in %s', langue, dossier)
    if langue in COMPLEMENTS:                    # installé en dernier : consulté en premier
        t = _complement(app, COMPLEMENTS[langue])
        QCoreApplication.installTranslator(t)
        _traducteurs.append(t)
    return charge
