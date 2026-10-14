"""Standard des applications de bureau (kit commun, 0.7.0) appliqué à Coupole : modules communs `updater.py`,
`reporting.py`, `interface_kit.py` branchés (sans copie modifiée), kit.json complet, mise à jour par archive sur un
faux paquet (données de l'utilisateur jamais touchées, archive sans données), rapports sans envoi pendant les essais,
accord repris des anciennes versions, faulthandler armé avant le relevé de la trace précédente, logo d'une seule
source, manuels FR et EN, style figé, `--check`."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from coupole.core import config, maj, rapports

RACINE = Path(__file__).resolve().parents[1]


def kit_json() -> dict:
    return json.loads((RACINE / 'kit.json').read_text(encoding='utf-8'))


def test_kit_json_complet_et_modules_communs():
    k = kit_json()
    for cle in ('nom_technique', 'nom_fichier', 'depot_distribution', 'point_entree', 'fichier_version', 'icone',
                'appid', 'icone_png', 'icone_grande', 'icone_icns', 'nom_affiche_fr', 'nom_affiche_en',
                'description_fr', 'description_en', 'categories_linux', 'journal_technique'):
        assert k.get(cle), cle
    for m in ('updater.py', 'reporting.py', 'interface_kit.py', 'lancer.py'):
        assert m in k['modules'] and (RACINE / m).is_file(), m
    for f in (k['icone'], k['icone_png'], k['icone_grande'], k['icone_icns'], k['paquet_deb'], k['journal_technique']):
        assert (RACINE / f).is_file(), f
    # le journal technique décrit la version publiée (le workflow du kit le vérifie aussi)
    v = (RACINE / 'VERSION').read_text(encoding='utf-8').strip()
    assert ('## %s ' % v) in (RACINE / k['journal_technique']).read_text(encoding='utf-8')
    # les modules communs sont ceux que l'application emploie
    u, r = maj.kit('updater'), maj.kit('reporting')
    assert u.REPO == k['depot_distribution'] and u.PREFIXE_ARCHIVE == 'coupole-app-'
    assert set(k['fichiers_proteges']) <= u.PROTECTED
    assert r.ENDPOINT.startswith('https://')


def test_logo_une_seule_source():
    """logo/coupole.svg est la source : la copie de l'application et l'icône de l'installeur en dérivent."""
    assert (RACINE / 'logo' / 'coupole.svg').read_bytes() == (RACINE / 'coupole' / 'ressources' / 'coupole.svg').read_bytes()
    assert (RACINE / 'logo' / 'coupole.ico').read_bytes() == (RACINE / 'coupole.ico').read_bytes()
    for t in (16, 32, 48, 64, 128, 256, 512, 1024):
        assert (RACINE / 'logo' / ('coupole_%d.png' % t)).is_file()


def test_manuels_fr_et_en_livres_avec_l_application():
    for lg in ('fr', 'en'):
        p = RACINE / 'coupole' / 'docs' / ('manuel_%s.pdf' % lg)
        assert p.is_file() and p.stat().st_size > 500_000
        assert p.read_bytes()[:5] == b'%PDF-'


class _Reponse(io.BytesIO):
    headers: dict = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _faux_paquet(tmp_path, monkeypatch):
    """Paquet autonome factice : python/bin/python3, app/ avec une ancienne version, des données de l'utilisateur."""
    (tmp_path / 'python' / 'bin').mkdir(parents=True)
    (tmp_path / 'python' / 'bin' / 'python3').write_text('')
    app = tmp_path / 'app'
    (app / 'coupole').mkdir(parents=True)
    (app / 'lancer.py').write_text('# ancien\n')
    (app / 'coupole' / '__init__.py').write_text('# ancien\n')
    (app / 'VERSION').write_text('0.6.0\n')
    (app / '_rapports').mkdir()
    (app / '_rapports' / 'r.json').write_text('{"a": 1}')
    (app / 'reglages.json').write_text('{"perso": true}')
    u = maj.kit('updater')
    monkeypatch.setattr(maj, 'dossier_app', lambda: app)
    monkeypatch.setattr(u, 'app_dir', lambda: app)
    return app


def test_mise_a_jour_par_archive_garde_les_donnees(tmp_path, monkeypatch):
    app = _faux_paquet(tmp_path, monkeypatch)
    u = maj.kit('updater')
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('lancer.py', '# nouveau\n')
        z.writestr('coupole/__init__.py', '# nouveau\n')
        z.writestr('VERSION', '0.7.0\n')
    donnees = archive.getvalue()
    release = {'tag_name': 'v9.0.0', 'html_url': 'https://github.com/x/y/releases/v9.0.0', 'body': '## Francais\nN',
               'assets': [{'name': 'coupole-app-9.0.0.zip', 'size': len(donnees),
                           'browser_download_url': 'https://github.com/x/y/coupole-app-9.0.0.zip'}]}
    monkeypatch.setattr(u, '_open', lambda url: _Reponse(json.dumps(release).encode() if 'api.github' in url else donnees))
    m = maj.verifier('0.6.0')
    assert m and m['version'] == '9.0.0' and m['taille'] == len(donnees)
    assert maj.type_installation() == 'paquet' and maj.appliquer(m)
    assert (app / 'lancer.py').read_text() == '# nouveau\n' and (app / 'VERSION').read_text() == '0.7.0\n'
    assert (app / '_rapports' / 'r.json').exists() and json.loads((app / 'reglages.json').read_text()) == {'perso': True}
    # archive tronquée (taille annoncée différente) : refusée, l'installation reste intacte
    m['kit']['size'] = len(donnees) + 7
    with pytest.raises(RuntimeError):
        maj.appliquer(m)
    assert (app / 'lancer.py').read_text() == '# nouveau\n'


def test_archive_de_mise_a_jour_sans_donnees_utilisateur(tmp_path, monkeypatch):
    """build_unix.py construit l'archive commune : les fichiers protégés (données de l'utilisateur) n'y sont jamais."""
    sys.path.insert(0, str(RACINE))
    try:
        import build_unix
    finally:
        sys.path.remove(str(RACINE))
    pkg = tmp_path / 'Coupole'
    app = pkg / 'app'
    (app / 'coupole').mkdir(parents=True)
    (app / 'lancer.py').write_text('x')
    (app / 'coupole' / '__init__.py').write_text('')
    (app / '_rapports').mkdir()
    (app / '_rapports' / 'r.json').write_text('{}')
    (app / 'reglages.json').write_text('{}')
    monkeypatch.setattr(build_unix, 'ROOT', tmp_path)
    monkeypatch.setattr(build_unix, 'racine_paquet', lambda: pkg)
    sortie = build_unix.step_archive('9.9.9')
    with zipfile.ZipFile(sortie) as z:
        noms = z.namelist()
    assert 'lancer.py' in noms and 'coupole/__init__.py' in noms
    assert not any(n.startswith(('_rapports', 'reglages.json')) for n in noms), noms


def test_rapports_sans_envoi_pendant_les_essais_et_accord_repris(tmp_path, monkeypatch):
    r = maj.kit('reporting')
    reglages = config.Reglages(tmp_path / 'reglages.json')
    reglages['rapports_autorises'] = True                  # accord donné à Coupole ≤ 0.6
    monkeypatch.setattr(config, 'reglages', lambda: reglages)
    monkeypatch.setenv('COUPOLE_SANS_RESEAU', '1')
    monkeypatch.delenv('COUPOLE_RAPPORTS_URL', raising=False)
    rapports.init(tmp_path)
    try:
        assert rapports.consentement() is True                                 # repris, sans perte
        assert json.loads((tmp_path / 'reglages_rapports.json').read_text())['envoi_autorise'] is True
        assert r.ENDPOINT == rapports.COLLECTE_DESACTIVEE and '127.0.0.1' in r.ENDPOINT
        assert r._machine()['poste'] == 'install-' + reglages['id_installation']   # même identifiant qu'avant
        assert not r._poster(b'{}')                                            # rien ne part vers le vrai serveur
        rapports.definir_consentement(False)
        assert reglages['rapports_autorises'] is False
    finally:
        rapports.definir_consentement(False)


def test_faulthandler_arme_avant_le_releve_de_la_trace_precedente(tmp_path, monkeypatch):
    journal = tmp_path / '_crash_natif.log'
    journal.write_text('Fatal Python error: Segmentation fault\n  File "x.py", line 1\n', encoding='utf-8')
    vus = []
    monkeypatch.setattr(maj.kit('reporting'), 'envoyer', lambda genre, **c: vus.append((genre, c)) or {})
    import faulthandler
    try:
        rapports.armer_faulthandler(journal)
        assert faulthandler.is_enabled()
        assert vus and vus[0][0] == 'crash_natif' and 'Segmentation' in vus[0][1]['trace']
        assert journal.exists() and journal.stat().st_size == 0              # fichier armé, vide
        assert not journal.with_name('_crash_natif.precedent.log').exists()  # trace précédente relevée puis retirée
    finally:
        faulthandler.disable()
        if rapports._fichier_faulthandler:
            rapports._fichier_faulthandler.close()


def test_style_fige_et_explorateur_complet_sous_linux(app_qt):
    from coupole.gui import theme
    theme.appliquer(app_qt, 'clair')
    theme.appliquer(app_qt, 'sombre')
    assert str(app_qt.property('coupole_style')).lower() == 'fusion'      # Fusion + palette + feuille de Coupole
    assert app_qt.styleSheet() == theme.feuille_de_style('sombre')
    if sys.platform.startswith('linux'):
        assert config.DEFAUTS['dialogues_fichiers'] == 'qt'
    else:
        assert config.DEFAUTS['dialogues_fichiers'] == 'systeme'


def test_migration_des_dialogues_sous_linux(tmp_path, monkeypatch):
    p = tmp_path / 'reglages.json'
    p.write_text(json.dumps({'dialogues_fichiers': 'systeme', 'debit_sans_plafond_023': True}), encoding='utf-8')
    r = config.Reglages(p)
    attendu = 'qt' if sys.platform.startswith('linux') else 'systeme'
    assert r['dialogues_fichiers'] == attendu
    r['dialogues_fichiers'] = 'systeme'                     # choix fait ensuite : gardé
    assert config.Reglages(p)['dialogues_fichiers'] == 'systeme'


@pytest.mark.skipif(not os.environ.get('COUPOLE_TEST_CHECK') and not os.environ.get('CI'),
                    reason='essai complet de --check (20 à 60 s) : en CI, ou avec COUPOLE_TEST_CHECK=1')
def test_option_check():
    r = subprocess.run([sys.executable, str(RACINE / 'lancer.py'), '--check'], capture_output=True, text=True,
                       env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}, timeout=600, cwd=str(RACINE))
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    assert 'essai fumée' in r.stdout and 'OK' in r.stdout
