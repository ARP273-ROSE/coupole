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
