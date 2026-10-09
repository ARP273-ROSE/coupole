"""0.1.8 — explorateur de fichiers du système, textes de Qt traduits, dossiers réseau, lanceur et paquets.

Retour d'usage (Manjaro, KDE Plasma, paquet autonome 0.1.7) : le dialogue « Dossier de sortie » était celui de Qt,
en anglais, sans les emplacements du système (le NAS monté dans Dolphin restait inatteignable) ; un lien
~/.local/bin/coupole vers Coupole.sh ne démarrait pas.
"""
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from coupole.core import chemins
from coupole.gui import plateforme

RACINE = Path(__file__).resolve().parents[1]
LINUX = sys.platform.startswith('linux')


# ================================================================ décision du thème de plateforme (fonction pure)
@pytest.mark.parametrize('env, portail, gtk3, preference, attendu', [
    # KDE Plasma avec le portail : Dolphin (et Réseau/SMB) par xdg-desktop-portal-kde
    ({'XDG_CURRENT_DESKTOP': 'KDE', 'DISPLAY': ':0'}, True, False, 'systeme', ('xdgdesktopportal', 'portail')),
    # GNOME (Wayland) avec le portail : Nautilus par xdg-desktop-portal-gnome
    ({'XDG_CURRENT_DESKTOP': 'GNOME', 'WAYLAND_DISPLAY': 'wayland-0'}, True, True, 'systeme',
     ('xdgdesktopportal', 'portail')),
    # GNOME sans portail, greffon GTK 3 présent : dialogue GTK
    ({'XDG_CURRENT_DESKTOP': 'ubuntu:GNOME', 'DISPLAY': ':0'}, False, True, 'systeme', ('gtk3', 'gtk3')),
    # KDE sans portail : dialogue de Qt (traduit, enrichi)
    ({'XDG_CURRENT_DESKTOP': 'KDE', 'DISPLAY': ':0'}, False, True, 'systeme', (None, 'repli_qt')),
    # bureau inconnu sans portail ni GTK
    ({'DISPLAY': ':0'}, False, False, 'systeme', (None, 'repli_qt')),
    # variable déjà posée par l'utilisateur (ou la distribution) : respectée, même avec un portail
    ({'XDG_CURRENT_DESKTOP': 'KDE', 'DISPLAY': ':0', 'QT_QPA_PLATFORMTHEME': 'kde'}, True, True, 'systeme',
     (None, 'utilisateur')),
    # Préférences > Boîtes de dialogue de fichiers : Qt
    ({'XDG_CURRENT_DESKTOP': 'KDE', 'DISPLAY': ':0'}, True, True, 'qt', (None, 'preference_qt')),
    # sans écran (tests, serveur)
    ({'XDG_CURRENT_DESKTOP': 'KDE', 'DISPLAY': ':0', 'QT_QPA_PLATFORM': 'offscreen'}, True, True, 'systeme',
     (None, 'sans_ecran')),
    ({}, True, True, 'systeme', (None, 'sans_ecran')),
])
def test_decision_du_theme_linux(env, portail, gtk3, preference, attendu):
    assert plateforme.decider_theme(env, plateforme='linux', preference=preference, portail=portail,
                                    gtk3=gtk3) == attendu


@pytest.mark.parametrize('systeme', ['win32', 'darwin'])
def test_windows_et_macos_gardent_leur_dialogue_natif(systeme):
    """Ni greffon à choisir ni variable posée : QFileDialog y est natif (IFileDialog, NSOpenPanel)."""
    for preference in ('systeme', 'qt'):
        assert plateforme.decider_theme({'DISPLAY': ':0'}, plateforme=systeme, preference=preference,
                                        portail=True, gtk3=True) == (None, 'natif')


def _xdg(tmp_path, service=True, moteur='org.freedesktop.impl.portal.FileChooser;org.freedesktop.impl.portal.Print'):
    d = tmp_path / 'share'
    if service:
        (d / 'dbus-1' / 'services').mkdir(parents=True)
        (d / 'dbus-1' / 'services' / 'org.freedesktop.portal.Desktop.service').write_text(
            '[D-BUS Service]\nName=org.freedesktop.portal.Desktop\nExec=/usr/lib/xdg-desktop-portal\n')
    if moteur is not None:
        (d / 'xdg-desktop-portal' / 'portals').mkdir(parents=True)
        (d / 'xdg-desktop-portal' / 'portals' / 'kde.portal').write_text(
            '[portal]\nDBusName=org.freedesktop.impl.portal.desktop.kde\nInterfaces=%s\nUseIn=KDE\n' % moteur)
    return {'XDG_DATA_DIRS': str(d), 'XDG_DATA_HOME': str(tmp_path / 'maison'), 'COUPOLE_XDG_SEULS': '1',
            'DBUS_SESSION_BUS_ADDRESS': 'unix:path=%s' % (tmp_path / 'bus-absent'), 'XDG_CURRENT_DESKTOP': 'KDE',
            'DISPLAY': ':0'}


@pytest.mark.skipif(os.name == 'nt', reason='portail XDG : Linux (et Unix)')
def test_sonde_du_portail(tmp_path):
    """Service activable + moteur qui choisit des fichiers → portail ; sans bus de session ou sans moteur
    FileChooser → non. Rapide (aucune attente) même quand le bus ne répond pas."""
    import time
    env = _xdg(tmp_path / 'a')
    t0 = time.perf_counter()
    assert plateforme.portail_disponible(env, unites=())
    assert time.perf_counter() - t0 < 2
    sans_bus = dict(env)
    del sans_bus['DBUS_SESSION_BUS_ADDRESS']
    sans_bus['XDG_RUNTIME_DIR'] = str(tmp_path / 'pas-de-runtime')
    assert not plateforme.portail_disponible(sans_bus, unites=())
    assert not plateforme.portail_disponible(_xdg(tmp_path / 'b', moteur='org.freedesktop.impl.portal.Print'),
                                             unites=())
    t0 = time.perf_counter()                       # ni service ni nom sur le bus (bus absent) : non, sans attendre
    assert not plateforme.portail_disponible(_xdg(tmp_path / 'c', service=False), unites=(), delai=0.5)
    assert time.perf_counter() - t0 < 3


@pytest.mark.skipif(not LINUX, reason='Linux seulement')
def test_preparer_pose_la_variable_avant_qapplication(tmp_path):
    env = _xdg(tmp_path)
    plateforme.preparer('systeme', env=env)
    assert env['QT_QPA_PLATFORMTHEME'] == 'xdgdesktopportal' and plateforme.decision['raison'] == 'portail'
    assert plateforme.dialogue_natif_attendu()
    env = _xdg(tmp_path / 'u')
    env['QT_QPA_PLATFORMTHEME'] = 'gtk3'                  # choix de l'utilisateur : intouché
    plateforme.preparer('systeme', env=env)
    assert env['QT_QPA_PLATFORMTHEME'] == 'gtk3' and plateforme.decision['raison'] == 'utilisateur'
    env = _xdg(tmp_path / 'q')
    plateforme.preparer('qt', env=env)
    assert 'QT_QPA_PLATFORMTHEME' not in env and not plateforme.dialogue_natif_attendu()
    plateforme.decision.update(theme=None, raison='non_decide')


def test_l_application_prepare_avant_qapplication():
    """L'ordre compte : la variable n'a d'effet que posée avant la création de QApplication."""
    texte = (RACINE / 'coupole' / 'gui' / 'app.py').read_text(encoding='utf-8')
    assert texte.index('plateforme.preparer(') < texte.index('QApplication(sys.argv)')
    assert texte.index('QApplication(sys.argv)') < texte.index('plateforme.installer_traductions(')


# ================================================================ appels de dialogues
def test_aucun_dialogue_statique_ni_dialogue_qt_force():
    """Tous les choix de fichiers passent par gui/fichiers.py (parent transmis, natif sauf réglage « Qt »)."""
    for f in (RACINE / 'coupole').rglob('*.py'):
        texte = f.read_text(encoding='utf-8')
        assert not re.search(r'QFileDialog\.get(ExistingDirectory|OpenFileName|SaveFileName|OpenFileNames)\(', texte), f
        if f.name != 'fichiers.py':
            assert 'DontUseNativeDialog' not in texte, f
    texte = (RACINE / 'coupole' / 'gui' / 'fichiers.py').read_text(encoding='utf-8')
    assert 'fen = _parent_visible(parent)' in texte and 'QFileDialog(fen,' in texte


@pytest.fixture
def dialogue_simule(app_qt, monkeypatch):
    from PyQt6.QtWidgets import QDialog, QFileDialog
    vus = []

    def executer(self):
        vus.append(self)
        self._choix = self.directory().absolutePath()
        return QDialog.DialogCode.Accepted.value
    monkeypatch.setattr(QFileDialog, 'exec', executer)
    monkeypatch.setattr(QFileDialog, 'selectedFiles', lambda self: [self._choix])
    return vus


@pytest.mark.parametrize('reglage', ['systeme', 'qt'])
def test_dialogue_dossier_natif_ou_qt_selon_le_reglage(app_qt, dialogue_simule, monkeypatch, tmp_path, reglage):
    from PyQt6.QtWidgets import QFileDialog, QWidget
    from coupole.core import config
    from coupole.gui import fichiers
    monkeypatch.setitem(config.reglages().valeurs, 'dialogues_fichiers', reglage)
    parent = QWidget()
    parent.show()                             # fenêtre visible : c'est elle qui porte le dialogue
    assert fichiers.choisir_dossier(parent, 'Dossier de sortie', str(tmp_path)) == str(tmp_path).replace(os.sep, '/')
    d = dialogue_simule[-1]
    assert d.parent() is parent and d.windowTitle() == 'Dossier de sortie'
    assert d.fileMode() == QFileDialog.FileMode.Directory
    assert d.testOption(QFileDialog.Option.DontUseNativeDialog) == (reglage == 'qt')
    if reglage == 'qt':                       # barre latérale : dossier personnel et emplacements du système
        lieux = [u.toLocalFile() for u in d.sidebarUrls()]
        assert os.path.expanduser('~').replace(os.sep, '/') in [x.rstrip('/') for x in lieux]
    parent.deleteLater()


def test_emplacements_reseau_dans_la_barre_laterale(tmp_path):
    """Montages cifs/nfs/sshfs, partages gvfs (Nautilus, Dolphin + kio-fuse), disques amovibles."""
    montages = ('/dev/nvme0n1p2 / ext4 rw 0 0\n'
                '//nas/Astronomie /mnt/partage/Astronomie cifs rw,vers=3.1.1 0 0\n'
                'nas:/volume1/photo /mnt/photo\\040NAS nfs4 rw 0 0\n'
                'gvfsd-fuse /run/user/1000/gvfs fuse.gvfsd-fuse rw 0 0\n'
                'tmpfs /tmp tmpfs rw 0 0\n')
    assert chemins.montages_reseau(montages) == ['/mnt/partage/Astronomie', '/mnt/photo NAS', '/run/user/1000/gvfs']
    if not LINUX:
        return
    gvfs = tmp_path / 'gvfs'
    (gvfs / 'smb-share:server=nas,share=astronomie').mkdir(parents=True)
    lieux = chemins.emplacements_systeme({'USER': 'astro', 'XDG_RUNTIME_DIR': str(tmp_path)}, montages, uid=1000,
                                         existe=lambda p: p.startswith(str(tmp_path)) or p.startswith(('/mnt', '/run/media', '/media')))
    assert str(gvfs) in lieux and str(gvfs / 'smb-share:server=nas,share=astronomie') in lieux
    assert '/mnt/partage/Astronomie' in lieux and '/mnt/photo NAS' in lieux and '/run/media/astro' in lieux
    assert '/mnt' in lieux and '/tmp' not in lieux


# ================================================================ textes de Qt traduits
def test_textes_de_qt_traduits_et_recharges(app_qt):
    from PyQt6.QtWidgets import QDialogButtonBox
    std = QDialogButtonBox.StandardButton
    try:
        assert plateforme.installer_traductions(app_qt, 'fr')
        bb = QDialogButtonBox(std.Ok | std.Cancel | std.Yes | std.No)
        assert bb.button(std.Cancel).text().replace('&', '') == 'Annuler'
        assert bb.button(std.Yes).text().replace('&', '') == 'Oui'
        # changer de langue dans l'application recharge le bon catalogue (l'anglais : textes source de Qt)
        assert not plateforme.installer_traductions(app_qt, 'en')
        bb2 = QDialogButtonBox(std.Cancel)
        assert bb2.button(std.Cancel).text().replace('&', '') == 'Cancel'
    finally:
        plateforme.installer_traductions(app_qt, 'en')


def test_dialogue_qt_de_repli_en_francais(app_qt):
    from PyQt6.QtWidgets import QFileDialog, QLabel
    try:
        plateforme.installer_traductions(app_qt, 'fr')
        d = QFileDialog(None, 'x')
        d.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        d.show()
        app_qt.processEvents()
        textes = {l.text() for l in d.findChildren(QLabel)}
        # deux libellés manquent au catalogue de Qt 6 : complétés par l'application
        assert {'&Voir dans\u00a0:', 'Fichiers de &type\u00a0:'} <= textes, textes
        assert not any(re.search(r'Look in|Files of|File name|Directory', t.replace('&', '')) for t in textes), textes
        d.close()
        d.deleteLater()
    finally:
        plateforme.installer_traductions(app_qt, 'en')


def test_le_paquet_garde_greffons_et_traductions(tmp_path, monkeypatch):
    """Le Qt installé contient ce qu'il faut, et l'élagage de build_unix.py ne le retire pas."""
    import PyQt6
    qt = Path(PyQt6.__file__).parent / 'Qt6'
    assert (qt / 'translations' / 'qtbase_fr.qm').is_file()
    if LINUX:
        for nom in ('libqxdgdesktopportal.so', 'libqgtk3.so'):
            assert (qt / 'plugins' / 'platformthemes' / nom).is_file(), nom
    sys.path.insert(0, str(RACINE))
    try:
        import build_unix
    finally:
        sys.path.remove(str(RACINE))
    # paquet simulé : arborescence de PyQt6 avec ce que l'élagage garde et ce qu'il retire
    dist = tmp_path / 'dist'
    pkg = dist / 'Coupole'
    sp = pkg / 'python' / 'lib' / 'python3.12' / 'site-packages' / 'PyQt6' / 'Qt6'
    fichiers = ['plugins/platforms/libqxcb.so', 'plugins/platforms/libqvnc.so',
                'plugins/platformthemes/libqxdgdesktopportal.so', 'plugins/platformthemes/libqgtk3.so',
                'plugins/sqldrivers/libqsqlite.so', 'translations/qtbase_fr.qm', 'translations/qt_fr.qm',
                'translations/qtbase_en.qm', 'translations/qtbase_de.qm', 'lib/libQt6Core.so.6',
                'lib/libQt6Quick.so.6']
    for f in fichiers:
        (sp / f).parent.mkdir(parents=True, exist_ok=True)
        (sp / f).write_bytes(b'x')
    (pkg / 'python' / 'bin').mkdir(parents=True)
    monkeypatch.setattr(build_unix, 'DIST', dist)
    monkeypatch.setattr(build_unix, 'PKG', pkg)
    build_unix.step_elaguer()
    assert not (sp / 'translations/qtbase_de.qm').exists() and not (sp / 'lib/libQt6Quick.so.6').exists()
    assert build_unix.controler_qt(pkg, 'linux') == []
    (sp / 'plugins/platformthemes/libqxdgdesktopportal.so').unlink()
    assert build_unix.controler_qt(pkg, 'linux') == ['plugins/platformthemes/libqxdgdesktopportal.so']
    # paquet Windows : même contrôle dans build_package.py
    sys.path.insert(0, str(RACINE))
    try:
        import build_package
    finally:
        sys.path.remove(str(RACINE))
    win = tmp_path / 'win'
    qtw = win / 'python' / 'Lib' / 'site-packages' / 'PyQt6' / 'Qt6'
    for f in build_package.QT_ATTENDUS:
        (qtw / f).parent.mkdir(parents=True, exist_ok=True)
        (qtw / f).write_bytes(b'x')
    assert build_package.controler_qt(win) == []
    (qtw / 'translations' / 'qtbase_fr.qm').unlink()
    assert build_package.controler_qt(win) == ['translations/qtbase_fr.qm']


# ================================================================ chemins réseau : UNC, gvfs, cifs
def test_uri_sqlite_d_un_chemin_unc():
    """SQLite refuse « file://serveur/… » : un UNC s'écrit avec une autorité vide."""
    u = chemins.uri_sqlite_lecture_seule(r'\\nas\Astronomie\OHP DU ECU\_traitement\etat.sqlite', windows=True)
    assert u == 'file:////nas/Astronomie/OHP%20DU%20ECU/_traitement/etat.sqlite?mode=ro'
    assert chemins.est_unc(r'\\nas\partage') and chemins.est_unc('//nas/partage')
    assert not chemins.est_unc(r'\\?\C:\x') and not chemins.est_unc('C:\\x') and not chemins.est_unc('/mnt/partage')


def _base_etat(dest):
    os.makedirs(os.path.join(dest, '_traitement'), exist_ok=True)
    db = sqlite3.connect(os.path.join(dest, '_traitement', 'etat.sqlite'))
    db.execute('CREATE TABLE images (id TEXT PRIMARY KEY, url TEXT, statut TEXT, maj TEXT, info TEXT)')
    db.execute("INSERT INTO images VALUES ('a', 'u', 'ok', '2026-10-09T10:00:00', '{\"final\": \"x.xisf\"}')")
    db.commit()
    db.close()


@pytest.mark.skipif(os.name == 'nt', reason='« : » interdit dans un nom de dossier Windows ; gvfs : Linux')
def test_dossier_au_nom_de_partage_gvfs(tmp_path):
    """Un chemin gvfs (« : », « , », « = ») : possession lue, place libre, inscriptible, affichage coupable."""
    from coupole.core.machine import disque_libre_go
    from coupole.gui.adaptatif import coupable, texte_reel
    from coupole.modules.ohp.possession import Possession
    dest = str(tmp_path / 'gvfs' / 'smb-share:server=nas,share=astronomie' / 'OHP_DU_ECU')
    _base_etat(dest)
    p = Possession.lire(dest)
    assert p.existe and p.statuts == {'a': 'ok'}
    assert disque_libre_go(os.path.join(dest, 'pas_encore_cree')) > 0
    assert texte_reel(coupable(dest)) == dest
    test = os.path.join(dest, '.ecriture')
    open(test, 'wb').close()
    os.remove(test)


def _unc_local(tmp_path):
    """Le dossier temporaire vu par le partage administratif \\\\localhost\\C$ (Windows), s'il est accessible."""
    lecteur, reste = os.path.splitdrive(str(tmp_path))
    if not lecteur or not lecteur.endswith(':'):
        return None
    unc = '\\\\localhost\\%s$%s' % (lecteur[0], reste)
    return unc if os.path.isdir(unc) else None


@pytest.mark.skipif(os.name != 'nt', reason='chemins UNC : Windows')
def test_chemin_unc_reel(tmp_path):
    from coupole.core.machine import disque_libre_go
    from coupole.modules.ohp.possession import Possession
    from coupole.modules.qualite.moteur import est_reseau
    unc = _unc_local(tmp_path)
    if unc is None:
        pytest.skip('partage administratif \\\\localhost\\C$ inaccessible')
    dest = os.path.join(unc, 'OHP_DU_ECU')
    _base_etat(dest)
    assert Possession.lire(dest).statuts == {'a': 'ok'}
    assert disque_libre_go(dest) > 0 and est_reseau(dest)
    long = os.path.join(dest, *(['d' * 60] * 5))
    os.makedirs(chemins.chemin_os(long), exist_ok=True)
    assert os.path.isdir(chemins.chemin_os(long))
    assert chemins.chemin_os(long).startswith('\\\\?\\UNC\\localhost\\')


# ================================================================ lanceur et installeur du paquet Linux
def _paquet_simule(tmp_path):
    sys.path.insert(0, str(RACINE))
    try:
        import build_unix
    finally:
        sys.path.remove(str(RACINE))
    pkg = tmp_path / 'paquet' / 'Coupole'
    (pkg / 'python' / 'bin').mkdir(parents=True)
    py = pkg / 'python' / 'bin' / 'python3'                 # l'interpréteur des tests (venv compris)
    py.write_text('#!/bin/sh\nexec "%s" "$@"\n' % sys.executable, encoding='utf-8')
    py.chmod(0o755)
    os.symlink(RACINE, pkg / 'app')                     # app/lancer.py et app/coupole : le dépôt lui-même
    lanceur = pkg / 'Coupole.sh'
    lanceur.write_text(build_unix.texte_lanceur(), encoding='utf-8')
    lanceur.chmod(0o755)
    return build_unix, pkg, lanceur


@pytest.mark.skipif(os.name == 'nt' or not shutil.which('sh'), reason='lanceur shell : Linux, macOS')
def test_lanceur_par_lien_symbolique(tmp_path):
    from coupole import __version__
    from coupole.core import maj
    build_unix, pkg, lanceur = _paquet_simule(tmp_path)
    assert maj.LANCEUR_LINUX == build_unix.texte_lanceur()      # le lanceur réparé est celui du paquet
    assert 'readlink -f' not in build_unix.texte_lanceur('../Resources')   # macOS < 12.3
    liens = tmp_path / 'bin'
    liens.mkdir()
    os.symlink(lanceur, liens / 'coupole')                    # ~/.local/bin/coupole -> Coupole.sh
    os.symlink('coupole', liens / 'coupole2')                 # lien relatif vers un lien
    (tmp_path / 'ailleurs').mkdir()
    os.symlink(os.path.relpath(liens / 'coupole2', tmp_path / 'ailleurs'), tmp_path / 'ailleurs' / 'c3')
    env = {**os.environ, 'COUPOLE_SANS_RESEAU': '1'}
    for appel in (lanceur, liens / 'coupole', liens / 'coupole2', tmp_path / 'ailleurs' / 'c3'):
        r = subprocess.run([str(appel), '--version'], capture_output=True, text=True, timeout=120, env=env,
                           cwd=str(tmp_path))
        assert r.returncode == 0 and __version__ in r.stdout, (appel, r.stdout, r.stderr)


@pytest.mark.skipif(os.name == 'nt' or not shutil.which('sh'), reason='lanceur shell : Linux, macOS')
def test_lanceur_ancien_repare(tmp_path):
    from coupole.core import maj
    ancien = ('#!/bin/sh\n# Lanceur : tout est relatif au dossier du paquet, rien n\'est\n# installe dans le systeme.\n'
              'ICI=$(cd "$(dirname "$0")" && pwd)\nexec "$ICI/python/bin/python3" "$ICI/app/lancer.py" "$@"\n')
    l = tmp_path / 'Coupole.sh'
    l.write_text(ancien, encoding='utf-8')
    l.chmod(0o755)
    assert maj.reparer_lanceur(tmp_path) and l.read_text(encoding='utf-8') == maj.LANCEUR_LINUX
    assert os.access(l, os.X_OK)
    assert not maj.reparer_lanceur(tmp_path)                  # déjà à jour : rien
    l.write_text('#!/bin/sh\necho personnalise\n', encoding='utf-8')
    assert not maj.reparer_lanceur(tmp_path)                  # lanceur modifié à la main : intouché


@pytest.mark.skipif(not LINUX or not shutil.which('sed'), reason='installer.sh : paquet Linux')
def test_installer_pose_le_lien_et_signale_le_path(tmp_path):
    from coupole import __version__
    build_unix, pkg, lanceur = _paquet_simule(tmp_path)
    (pkg / 'installer.sh').write_text(build_unix.texte_installeur(), encoding='utf-8')
    (pkg / 'coupole.desktop').write_text('[Desktop Entry]\nExec=__ICI__/Coupole.sh\n__ICONE__Name=Coupole\n')
    # le paquet simulé pointe sur le dépôt par liens : on le rend autonome pour la copie
    (pkg / 'app').unlink()
    (pkg / 'app').mkdir()
    shutil.copy2(RACINE / 'lancer.py', pkg / 'app' / 'lancer.py')
    shutil.copytree(RACINE / 'coupole', pkg / 'app' / 'coupole', ignore=shutil.ignore_patterns('__pycache__'))
    for f in ('VERSION', 'pyproject.toml'):
        if (RACINE / f).exists():
            shutil.copy2(RACINE / f, pkg / 'app' / f)
    maison = tmp_path / 'maison'
    maison.mkdir()
    env = {'HOME': str(maison), 'PATH': '/usr/bin:/bin', 'LANG': 'fr_FR.UTF-8'}
    r = subprocess.run(['sh', str(pkg / 'installer.sh')], capture_output=True, text=True, timeout=120, env=env)
    assert r.returncode == 0, r.stderr
    lien = maison / '.local' / 'bin' / 'coupole'
    assert lien.is_symlink() and 'PATH' in r.stdout and 'export PATH=' in r.stdout
    assert (maison / '.local' / 'share' / 'applications' / 'coupole.desktop').read_text().count(
        str(maison / '.local' / 'share' / 'coupole')) >= 1
    r = subprocess.run([str(lien), '--version'], capture_output=True, text=True, timeout=120,
                       env={**os.environ, 'COUPOLE_SANS_RESEAU': '1'})
    assert r.returncode == 0 and __version__ in r.stdout, r.stderr
    # PATH déjà bon : pas d'avertissement
    env['PATH'] = '%s:/usr/bin:/bin' % (maison / '.local' / 'bin')
    r = subprocess.run(['sh', str(pkg / 'installer.sh')], capture_output=True, text=True, timeout=120, env=env)
    assert r.returncode == 0 and 'export PATH=' not in r.stdout
