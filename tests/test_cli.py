"""Ligne de commande : tout est faisable sans interface, dans les deux langues."""
import json

import pytest

from coupole import cli


def lancer(capsys, *args):
    code = cli.main(list(args))
    return code, capsys.readouterr().out


def test_aide_bilingue(capsys):
    with pytest.raises(SystemExit):
        cli.main(['--lang', 'en', '--help'])
    en = capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.main(['--lang', 'fr', '--help'])
    fr = capsys.readouterr().out
    assert 'commands' in en and 'commandes' in fr and fr != en
    assert 'utilisation' in fr


def test_catalogue_json(capsys):
    code, out = lancer(capsys, '--lang', 'en', 'ohp', 'catalog', '--type', 'pla', '--json')
    d = json.loads(out)
    assert code == 0 and {o['nom'] for o in d} == {'Neptune', 'Saturn', 'Uranus'}


def test_images_et_estimation(capsys, tmp_path):
    code, out = lancer(capsys, '--lang', 'fr', 'ohp', 'images', 'palisana', '--csv', str(tmp_path / 'p.csv'))
    assert code == 0 and out.count('doublon') >= 6 and (tmp_path / 'p.csv').exists()
    code, out = lancer(capsys, '--lang', 'en', 'ohp', 'estimate', 'Palisana')
    assert '10 image(s)' in out and '6 duplicate(s)' in out


def test_selection_vide_ou_inconnue(capsys):
    assert cli.main(['ohp', 'traiter']) == 2
    assert cli.main(['ohp', 'traiter', 'objet-qui-n-existe-pas']) == 2


def test_machine_astap_sources_modules(capsys):
    code, out = lancer(capsys, 'machine', '--json')
    d = json.loads(out)
    assert code == 0 and d['plan']['conversions'] >= 1
    code, out = lancer(capsys, 'astap', '--json')
    d = json.loads(out)
    assert 'conseils' in d and d['conseils']['page'].startswith('https://www.hnsky.org')
    code, out = lancer(capsys, 'sources')
    assert 'ohp.tap' in out
    code, out = lancer(capsys, 'modules')
    assert 'ohp' in out and 'machine' in out


def test_anomalies_csv(capsys, tmp_path):
    code, out = lancer(capsys, '--lang', 'fr', 'ohp', 'anomalies', '--csv', str(tmp_path / 'a.csv'))
    assert code == 0 and 'copie_diurne' in out and (tmp_path / 'a.csv').stat().st_size > 1000


def test_sites_heure(capsys):
    code, out = lancer(capsys, '--lang', 'fr', 'sites', '--heure', '2025-07-16T22:20:23', '--site', 'ohp')
    assert '2025-07-17 00:20:23 (UTC+2)' in out and 'date du soir au site : 2025-07-16' in out


def test_version_unique():
    from pathlib import Path
    import coupole
    assert coupole.__version__ == (Path(__file__).resolve().parents[1] / 'VERSION').read_text().strip()


def test_manuel_accessible(capsys, langue):
    for l in ('fr', 'en'):
        langue(l)
        p = cli.chemin_manuel()
        assert p.endswith('manuel_%s.pdf' % l)
        with open(p, 'rb') as f:
            assert f.read(5) == b'%PDF-'


def test_guide_astap_liens_et_extraction_sure():
    """Retour de Kevin (Manjaro) : le lien D80 en .zip était mort (404) ; extraction du .deb sans toucher à /."""
    from coupole.core import astap
    from coupole import textes
    urls = {u for *_x, u in astap.urls_conseillees()}
    assert not any('d80_star_database.zip' in u for u in urls)
    assert all(u.startswith('https://') for u in urls)
    c = astap.conseils_installation('linux', 'x86_64', 'arch')
    assert [k for k, _ in c['catalogue']][0] == 'astap_lien_d80_aur' and c['notes'] == ['astap_note_arch_cli']
    assert textes.EXTRAIRE == astap.EXTRAIRE_D80_DEB
    assert '-C /opt/astap' in astap.EXTRAIRE_D80_DEB and '-C / ' not in astap.EXTRAIRE_D80_DEB
    assert '--no-same-owner' in astap.EXTRAIRE_D80_DEB and "'./opt/astap/d80_*'" in astap.EXTRAIRE_D80_DEB
    for s, a, f in (('linux', 'x86_64', 'rpm'), ('linux', 'arm64', 'autre'), ('windows', 'arm64', '')):
        assert not any('d80_star_database.zip' in u for _, u in astap.conseils_installation(s, a, f)['catalogue'])


def test_astap_cli_prefere_a_l_executable_graphique(tmp_path, monkeypatch):
    """astap (graphique) dans le PATH et astap_cli seulement dans un dossier usuel (paquet Arch : /opt/astap) :
    c'est astap_cli qui est choisi ; sans l'exécutable graphique, la détection marche aussi."""
    import os
    import sys
    from coupole.core import astap
    if sys.platform == 'win32':
        pytest.skip('noms Unix')
    chemin = tmp_path / 'bin'
    opt = tmp_path / 'opt'
    chemin.mkdir()
    opt.mkdir()
    for f in (chemin / 'astap', opt / 'astap_cli'):
        f.write_text('#!/bin/sh\necho "ASTAP version 2026.10.08"\n')
        f.chmod(0o755)
    monkeypatch.setenv('PATH', str(chemin))
    monkeypatch.setattr(astap, 'emplacements_par_defaut', lambda: [opt])
    e = astap.detecter()
    assert e.executable == str(opt / 'astap_cli') and e.est_cli
    (chemin / 'astap').unlink()
    assert astap.detecter().executable == str(opt / 'astap_cli')


@pytest.mark.skipif(not __import__('os').environ.get('COUPOLE_TEST_LIENS'),
                    reason='essai réseau : COUPOLE_TEST_LIENS=1 (lancé par la CI, étape « Liens du guide ASTAP »)')
def test_liens_astap_repondent():
    """Chaque adresse du guide, pour chaque système et architecture : HEAD (redirections suivies) → 200."""
    import urllib.request
    from coupole.core import astap
    fautes = []
    for u in sorted({u for *_x, u in astap.urls_conseillees()}):
        try:
            req = urllib.request.Request(u, method='HEAD', headers={'User-Agent': 'Mozilla/5.0 (Coupole tests)'})
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status != 200:
                    fautes.append((u, r.status))
        except Exception as e:                       # 404, 403… : en faute
            fautes.append((u, str(e)[:80]))
    assert not fautes, fautes
