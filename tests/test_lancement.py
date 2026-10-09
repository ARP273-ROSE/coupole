"""0.1.12 — lancement des logiciels externes : « Ouvrir », « Ouvrir avec », « Ouvrir l'emplacement ».

Faux exécutables qui notent leurs arguments dans un fichier ; faux PixInsight.sh qui reproduit l'`eval` du vrai
script (guillemets seulement autour des arguments qui contiennent une espace) ; instance déjà ouverte simulée ;
.desktop sans %F ; journalisation ; aucun `shell=True` dans le code."""
import ast
import json
import logging
import os
import stat
import sys
from pathlib import Path

import pytest

from coupole.core import lancement, logiciels

POSIX = pytest.mark.skipif(os.name == 'nt', reason='scripts shell et liens symboliques : Linux/macOS')

# noms difficiles : espace, $, apostrophe, parenthèses, accents, accent grave, guillemet, astérisque
NOMS = ['simple.xisf', 'avec espace.xisf', 'dollar$HOME.xisf', "apos'trophe.xisf", 'paren (1).xisf',
        'accentué é.xisf', 'dollar et espace $USER x.xisf', 'étoile*.xisf']
NOMS_POSIX = NOMS + ['back`id`tick.xisf', 'guil"lemet.xisf', 'anti\\slash.xisf']

FAUX_PROGRAMME = '''import json, os, sys
with open(os.environ['COUPOLE_FAUX_JOURNAL'], 'a', encoding='utf-8') as f:
    f.write(json.dumps({'prog': os.path.basename(sys.argv[0]), 'args': sys.argv[1:],
                        'theme': os.environ.get('QT_QPA_PLATFORMTHEME')}) + '\\n')
if os.environ.get('COUPOLE_FAUX_INSTANCE') and '-n' not in sys.argv[1:]:
    print('Yielded execution to running application instance #1')
code = int(os.environ.get('COUPOLE_FAUX_CODE', '0'))
if code:
    sys.stderr.write('boom: erreur simulee\\n')
sys.exit(code)
'''

# reproduction du script de lancement Linux de PixInsight (constatée sur un poste réel)
FAUX_WRAPPER = '''#!/bin/sh
dirname=`dirname "$0"`
appname=PixInsight
args=
for arg in "$@"; do
  case "$arg" in
    *" "*) args="$args \\"$arg\\"" ;;
    *) args="$args $arg" ;;
  esac
done
eval "$dirname/$appname $args"
'''


def _executable(chemin: Path, texte: str):
    chemin.write_text(texte, encoding='utf-8')
    chemin.chmod(chemin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return chemin


def _faux_python(chemin: Path):
    return _executable(chemin, '#!%s\n%s' % (sys.executable, FAUX_PROGRAMME))


@pytest.fixture
def journal(tmp_path, monkeypatch):
    j = tmp_path / 'appels.jsonl'
    monkeypatch.setenv('COUPOLE_FAUX_JOURNAL', str(j))
    monkeypatch.delenv('COUPOLE_FAUX_INSTANCE', raising=False)
    monkeypatch.delenv('COUPOLE_FAUX_CODE', raising=False)

    def lire():
        if not j.exists():
            return []
        return [json.loads(l) for l in j.read_text(encoding='utf-8').splitlines() if l.strip()]
    return lire


@pytest.fixture
def pixinsight(tmp_path):
    """/opt/PixInsight/bin simulé : PixInsight.sh (eval) + PixInsight (note ses arguments)."""
    b = tmp_path / 'opt' / 'PixInsight' / 'bin'
    b.mkdir(parents=True)
    _faux_python(b / 'PixInsight')
    return _executable(b / 'PixInsight.sh', FAUX_WRAPPER)


def _images(racine: Path, noms, dossier='Données (copie) $nuit'):
    d = racine / dossier                       # par défaut, dossier lui aussi « difficile »
    d.mkdir(parents=True, exist_ok=True)
    out = []
    for n in noms:
        p = d / n
        p.write_bytes(b'XISF0100')
        out.append(p)
    return out


# ------------------------------------------------------------------ aucun shell
def test_aucun_shell_true_dans_le_code():
    racine = Path(logiciels.__file__).resolve().parents[1]
    fautes = []
    for f in racine.rglob('*.py'):
        arbre = ast.parse(f.read_text(encoding='utf-8'))
        for n in ast.walk(arbre):
            if isinstance(n, ast.Call):
                for k in n.keywords:
                    if k.arg == 'shell' and not (isinstance(k.value, ast.Constant) and k.value.value is False):
                        fautes.append('%s:%s' % (f.relative_to(racine), n.lineno))
                if isinstance(n.func, ast.Attribute) and n.func.attr in ('system', 'popen') and \
                        isinstance(n.func.value, ast.Name) and n.func.value.id == 'os':
                    fautes.append('%s:%s os.%s' % (f.relative_to(racine), n.lineno, n.func.attr))
    assert not fautes, fautes


# ------------------------------------------------------------------ PixInsight (Linux) : eval du script
@POSIX
def test_temoin_le_script_casse_les_chemins_speciaux(pixinsight, tmp_path, journal):
    """Témoin : appelé directement, le script de PixInsight transmet mal un chemin à `$` (le test mesure bien le
    défaut contourné)."""
    p = _images(tmp_path, ['dollar$HOME.xisf'])[0]
    l = lancement.demarrer([str(pixinsight), '-n', str(p)], 'temoin').attendre()
    recu = journal()
    assert l.termine
    assert not recu or recu[-1]['args'][-1] != str(p)


@POSIX
@pytest.mark.parametrize('nouvelle', [True, False])
def test_pixinsight_linux_chemins_speciaux(pixinsight, tmp_path, journal, caplog, nouvelle):
    caplog.set_level(logging.INFO, logger='coupole.lancement')
    images = _images(tmp_path, NOMS_POSIX) + _images(tmp_path, ['simple.xisf', 'avec espace.xisf', 'accentué é.xisf'],
                                                     'Nuit 1 é')
    assert sum(logiciels.chemin_sur_pour_eval(p) for p in images) == 3      # les deux cas sont essayés
    liens = tmp_path / 'liens'
    for p in images:
        l = logiciels.lancer_logiciel('pixinsight', p, {'pixinsight': [str(pixinsight)]}, nouvelle=nouvelle,
                                      dossier_liens=liens).attendre()
        assert l.ok, (p.name, l.erreur, l.detail)
        recu = journal()[-1]
        assert recu['prog'] == 'PixInsight'
        attendu = ['-n'] if nouvelle else []
        assert recu['args'][:-1] == attendu, recu
        # le fichier reçu EST l'image (directement, ou par un lien temporaire au nom sûr)
        assert os.path.realpath(recu['args'][-1]) == os.path.realpath(p), (p.name, recu)
        assert ('lg_note_pixinsight_lien' in l.notes) == (not logiciels.chemin_sur_pour_eval(p))
    # tout est journalisé : programme, arguments, pid, sortie
    texte = caplog.text
    assert 'program=' in texte and 'PixInsight.sh' in texte and 'exited with code 0' in texte


@POSIX
def test_binaire_detecte_remplace_par_son_script(pixinsight, tmp_path, journal):
    """Sous Linux le binaire seul ne démarre pas (Pleiades) : si la détection rend le binaire, son script est
    employé."""
    p = _images(tmp_path, ['a.xisf'], 'nuit')[0]
    binaire = pixinsight.parent / 'PixInsight'
    argv, notes, _ = logiciels.preparer_commande('pixinsight', [str(binaire)], p, nouvelle=True, plateforme='linux')
    assert argv == [str(pixinsight), '-n', str(p)]
    pixinsight.chmod(0o644)                                  # script sans bit x : passé à /bin/sh
    argv, _, _ = logiciels.preparer_commande('pixinsight', [str(pixinsight)], p, nouvelle=False, plateforme='linux')
    assert argv == ['/bin/sh', str(pixinsight), str(p)]


@POSIX
def test_instance_ouverte_simulee(pixinsight, tmp_path, journal, monkeypatch):
    """Instance occupée : sans -n, PixInsight « cède la main » et sort 0 sans rien ouvrir → note affichée ; avec -n
    (défaut), nouvelle instance."""
    monkeypatch.setenv('COUPOLE_FAUX_INSTANCE', '1')
    p = _images(tmp_path, ['m31.xisf'], 'nuit')[0]
    l = logiciels.lancer_logiciel('pixinsight', p, {'pixinsight': [str(pixinsight)]}, nouvelle=False).attendre()
    assert l.ok and l.code == 0 and l.notes[0] == 'lg_note_pixinsight_cede'
    assert 'Yielded execution' in l.sortie
    assert l.message()[0] == 'lg_note_pixinsight_cede'
    l = logiciels.lancer_logiciel('pixinsight', p, {'pixinsight': [str(pixinsight)]}).attendre()   # réglage par défaut
    assert l.ok and not l.notes and journal()[-1]['args'] == ['-n', str(p)]


def test_reglage_par_defaut_nouvelle_fenetre():
    from coupole.core import config
    assert config.DEFAUTS['pixinsight_instance'] == 'nouvelle'
    assert logiciels._instance_voulue(None) is True


def test_detection_d_une_instance(tmp_path):
    proc = tmp_path / 'proc'
    for pid, nom in (('1', 'systemd'), ('42', 'PixInsight.sh'), ('self', 'x')):
        (proc / pid).mkdir(parents=True)
        (proc / pid / 'comm').write_text(nom + '\n')
    assert not logiciels.pixinsight_ouvert('linux', str(proc))
    (proc / '77').mkdir()
    (proc / '77' / 'comm').write_text('PixInsight\n')
    assert logiciels.pixinsight_ouvert('linux', str(proc))
    assert not logiciels.pixinsight_ouvert('linux', str(tmp_path / 'absent'))


def test_pixinsight_macos_et_windows():
    app = '/Applications/PixInsight/PixInsight.app'
    p = os.path.abspath('/données/M 42 (Orion) $1.xisf')
    assert logiciels.preparer_commande('pixinsight', ['open', '-a', app], p, nouvelle=False, plateforme='darwin')[0] \
        == ['open', '-a', app, p]
    assert logiciels.preparer_commande('pixinsight', ['open', '-a', app], p, nouvelle=True, plateforme='darwin')[0] \
        == ['open', '-n', '-a', app, '--args', '-n', p]
    exe = 'C:/Program Files/PixInsight/bin/PixInsight.exe'
    assert logiciels.preparer_commande('pixinsight', [exe], p, nouvelle=True, plateforme='win32')[0] == [exe, '-n', p]
    assert logiciels.preparer_commande('pixinsight', [exe], p, nouvelle=False, plateforme='win32')[0] == [exe, p]


def test_chemin_sur_pour_eval():
    assert logiciels.chemin_sur_pour_eval('/mnt/partage/OHP_DU_ECU/09_Galaxies/NGC 891/é_1.xisf')
    for c in '$`\'"\\()*?[]{};&|<>!#~\t':
        assert not logiciels.chemin_sur_pour_eval('/a/b%sc.xisf' % c), c
    assert logiciels.nom_sur("M 42 (Orion) $1'.xisf") == 'M_42__Orion___1_.xisf'


# ------------------------------------------------------------------ Siril, ASTAP, Aladin : programme direct
@POSIX
@pytest.mark.parametrize('lg', ['siril', 'astap', 'aladin'])
def test_logiciels_directs_chemins_speciaux(lg, tmp_path, journal):
    prog = _faux_python(tmp_path / lg)
    for p in _images(tmp_path, NOMS_POSIX):
        l = logiciels.lancer_logiciel(lg, p, {lg: [str(prog)]}).attendre()
        assert l.ok, (p.name, l.erreur)
        assert journal()[-1]['args'] == [str(p)]                  # tel quel : aucun shell


def test_programme_direct_toutes_plates_formes(tmp_path, journal):
    """Sous tous les systèmes (Windows compris) : liste d'arguments transmise telle quelle."""
    script = tmp_path / 'faux.py'
    script.write_text(FAUX_PROGRAMME, encoding='utf-8')
    for p in _images(tmp_path, NOMS if os.name != 'nt' else [n for n in NOMS if '*' not in n]):
        l = logiciels.lancer_logiciel('siril', p, commande=[sys.executable, str(script)]).attendre()
        assert l.ok, (p.name, l.erreur, l.detail)
        assert journal()[-1]['args'] == [str(p)]


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason='flatpak : Linux seulement (/tmp → /private/tmp sous macOS)')
def test_flatpak_portail_et_permissions(tmp_path):
    cmd = ['flatpak', 'run', 'org.free_astro.siril']
    host = '[Context]\nshared=network;ipc;\nfilesystems=host;xdg-run/gvfs;\n'
    p = '/mnt/partage/OHP_DU_ECU/a.xisf'
    argv, notes, params = logiciels.preparer_commande('siril', cmd, p, permissions_flatpak=host)
    assert argv == ['flatpak', 'run', '--file-forwarding', 'org.free_astro.siril', '@@', p, '@@']
    assert notes == []
    # /tmp n'est pas couvert par « host » ; un override qui retire /mnt non plus → message clair
    assert logiciels.flatpak_voit('x', '/tmp/a.xisf', host) is False
    assert logiciels.flatpak_voit('x', '/run/media/u/disque/a.xisf', host) is True
    sans_mnt = '[Context]\nfilesystems=host;!/mnt;\n'
    argv, notes, params = logiciels.preparer_commande('siril', cmd, p, permissions_flatpak=sans_mnt)
    assert notes == ['lg_note_flatpak_portail'] and params['dossier'] == os.path.dirname(os.path.abspath(p))
    maison = '[Context]\nfilesystems=home;/srv/astro:ro;\n'
    assert logiciels.flatpak_voit('x', '/srv/astro/a.fits', maison) is True
    assert logiciels.flatpak_voit('x', '/mnt/a.fits', maison) is False
    assert logiciels.flatpak_voit('x', os.path.join(os.path.expanduser('~'), 'a.fits'), maison) is True


def test_nina_grise_avec_sa_raison(tmp_path):
    p = _images(tmp_path, ['u.xisf'])[0]
    l = logiciels.lancer_logiciel('nina', p, {'nina': ['NINA.exe']})
    assert not l.ok and l.erreur == 'lg_raison_nina_argument'
    from coupole.core.i18n import tr
    assert 'N.I.N.A.' in tr(l.erreur)


# ------------------------------------------------------------------ erreurs : jamais de silence
def test_programme_introuvable_journalise(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger='coupole.lancement')
    l = logiciels.lancer_logiciel('siril', tmp_path / 'a.fits', commande=[str(tmp_path / 'absent' / 'siril')])
    assert not l.ok and l.erreur == 'lg_err_introuvable'
    assert 'launch failed' in caplog.text
    from coupole.core.i18n import tr
    cle, params = l.message()
    assert 'Siril' in tr(cle, 'fr', **params) and 'Siril' in tr(cle, 'en', **params)


def test_code_de_retour_et_stderr(tmp_path, journal, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger='coupole.lancement')
    monkeypatch.setenv('COUPOLE_FAUX_CODE', '3')
    script = tmp_path / 'faux.py'
    script.write_text(FAUX_PROGRAMME, encoding='utf-8')
    l = logiciels.lancer_logiciel('astap', tmp_path / 'a.fits', commande=[sys.executable, str(script)]).attendre()
    assert l.code == 3 and l.erreur == 'lg_err_code' and 'boom' in l.detail
    assert 'exited with code 3' in caplog.text and 'boom' in caplog.text


def test_environnement_sans_le_theme_pose_par_coupole():
    env = {'QT_QPA_PLATFORMTHEME': 'xdgdesktopportal', 'COUPOLE_QPA_THEME_POSE': 'xdgdesktopportal', 'A': '1'}
    assert lancement.environnement_enfant(env) == {'A': '1'}
    env = {'QT_QPA_PLATFORMTHEME': 'kde', 'A': '1'}                  # posé par l'utilisateur : gardé
    assert lancement.environnement_enfant(env) == env


# ------------------------------------------------------------------ ouverture par défaut : .desktop sans %F
def _desktop(tmp_path, monkeypatch, exec_ligne):
    apps = tmp_path / 'xdg' / 'applications'
    apps.mkdir(parents=True)
    (apps / 'pixinsight.desktop').write_text('[Desktop Entry]\nType=Application\nName=PixInsight\nExec=%s\n'
                                             % exec_ligne, encoding='utf-8')
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    monkeypatch.setenv('XDG_DATA_DIRS', str(tmp_path / 'vide'))

    def faux_executer(argv, methode, delai=5.0):
        if argv[:3] == ['xdg-mime', 'query', 'filetype']:
            return 0, 'application/x-kdeuser1'
        if argv[:3] == ['xdg-mime', 'query', 'default']:
            return 0, 'pixinsight.desktop'
        return 1, ''
    return faux_executer


@POSIX
def test_desktop_sans_code_de_fichier(pixinsight, tmp_path, monkeypatch, journal):
    ex = _desktop(tmp_path, monkeypatch, str(pixinsight))
    p = _images(tmp_path, ["NGC 891 'b'.xisf"])[0]
    info = lancement.application_par_defaut(p, executer_=ex)
    assert info['type'] == 'application/x-kdeuser1' and info['accepte_fichier'] is False
    assert info['programme'] == str(pixinsight)
    l = logiciels.ouvrir_defaut(p, {'pixinsight': [str(pixinsight)]}, plateforme='linux', application=info).attendre()
    assert l.ok and 'lg_note_desktop_sans_fichier' in l.notes
    assert os.path.realpath(journal()[-1]['args'][-1]) == os.path.realpath(p)


def test_desktop_inconnu_sans_code_de_fichier(tmp_path, monkeypatch):
    ex = _desktop(tmp_path, monkeypatch, '/usr/bin/visionneuse-inconnue')
    info = lancement.application_par_defaut(tmp_path / 'a.xisf', executer_=ex)
    l = logiciels.ouvrir_defaut(tmp_path / 'a.xisf', {}, plateforme='linux', application=info)
    assert not l.ok and l.erreur == 'lg_err_desktop_sans_fichier' and l.params['desktop'] == 'pixinsight.desktop'


def test_desktop_avec_code_de_fichier(tmp_path, monkeypatch):
    ex = _desktop(tmp_path, monkeypatch, '/opt/PixInsight/bin/PixInsight.sh %F')
    info = lancement.application_par_defaut(tmp_path / 'a.xisf', executer_=ex)
    assert info['accepte_fichier'] is True
    appels = []
    monkeypatch.setattr(lancement, 'ouvrir_systeme', lambda c: appels.append(str(c)) or 'xdg')
    assert logiciels.ouvrir_defaut(tmp_path / 'a.xisf', {}, plateforme='linux', application=info) == 'xdg'
    assert appels == [str(tmp_path / 'a.xisf')]


def test_programme_exec():
    assert lancement.programme_exec('"/opt/Pix Insight/PixInsight.sh" %F') == '/opt/Pix Insight/PixInsight.sh'
    assert lancement.programme_exec('env QT_X=1 /usr/bin/siril %f') == '/usr/bin/siril'
    assert lancement.exec_accepte_fichier('siril %f') and not lancement.exec_accepte_fichier('siril')


# ------------------------------------------------------------------ interface
def test_menu_pixinsight_instance_ouverte(app_qt, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QMenu
    from coupole.core import config
    from coupole.gui import ouvrir
    p = tmp_path / 'f.fits'
    p.write_bytes(b'SIMPLE  =                    T' + b' ' * 50 + b'BITPIX  =                  -32' + b' ' * 49 +
                  b' ' * (2880 - 160))
    monkeypatch.setattr(ouvrir, 'installes', lambda rafraichir=False: {'pixinsight': ['/opt/PixInsight/bin/PixInsight.sh']})
    appels = []
    monkeypatch.setattr(logiciels, 'lancer_logiciel', lambda lg, c, i=None, nouvelle=None, **k:
                        appels.append((lg, nouvelle)) or True)
    for ouvert, reglage, attendus in ((False, 'nouvelle', ['PixInsight']),
                                      (True, 'nouvelle', ['PixInsight (nouvelle fenêtre)',
                                                          'PixInsight (fenêtre ouverte, essai)']),
                                      (True, 'envoyer', ['PixInsight (fenêtre ouverte, essai)',
                                                         'PixInsight (nouvelle fenêtre)'])):
        monkeypatch.setattr(logiciels, 'pixinsight_ouvert', lambda *a, o=ouvert, **k: o)
        monkeypatch.setitem(config.reglages().valeurs, 'pixinsight_instance', reglage)
        m = QMenu()
        ouvrir.remplir_menu(m, str(p), existe=True)
        avec = next(a for a in m.actions() if a.menu() is not None).menu()
        textes = [a.text() for a in avec.actions()]
        assert textes == attendus, textes
        for a in avec.actions():
            a.trigger()
        m.deleteLater()
    assert appels == [('pixinsight', None), ('pixinsight', True), ('pixinsight', False), ('pixinsight', False),
                      ('pixinsight', True)]


def test_erreur_en_barre_d_etat(app_qt, tmp_path):
    from PyQt6.QtWidgets import QMainWindow
    from coupole.gui import ouvrir
    f = QMainWindow()
    f.show()
    try:
        l = logiciels.lancer_logiciel('siril', tmp_path / 'a.fits', commande=[str(tmp_path / 'absent')])
        ouvrir.suivre(l)
        assert 'Siril' in f.statusBar().currentMessage() and 'introuvable' in f.statusBar().currentMessage()
    finally:
        f.close()
        f.deleteLater()


def test_suivi_jusqu_a_l_etat_final(app_qt, tmp_path, journal, monkeypatch):
    from PyQt6.QtWidgets import QMainWindow
    import time
    from coupole.gui import ouvrir
    monkeypatch.setenv('COUPOLE_FAUX_CODE', '2')
    script = tmp_path / 'faux.py'
    script.write_text(FAUX_PROGRAMME, encoding='utf-8')
    f = QMainWindow()
    f.show()
    try:
        l = ouvrir.suivre(logiciels.lancer_logiciel('astap', tmp_path / 'a.fits', commande=[sys.executable, str(script)]))
        assert 'ASTAP' in f.statusBar().currentMessage()                  # « Ouverture dans ASTAP… »
        fin = time.monotonic() + 15
        while time.monotonic() < fin and 'code 2' not in f.statusBar().currentMessage():
            app_qt.processEvents()
            time.sleep(0.02)
        assert 'code 2' in f.statusBar().currentMessage() and 'boom' in f.statusBar().currentMessage()
        assert l.termine
    finally:
        f.close()
        f.deleteLater()
