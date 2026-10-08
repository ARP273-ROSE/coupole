"""Module Cosmologie : valeurs comparées à une intégration indépendante (SageMath), bornes, export, CLI."""
import csv
import json
import math
from pathlib import Path

import pytest

from coupole import cli
from coupole.modules.cosmo import calcul, formats

REFERENCE = json.loads((Path(__file__).parent / 'cosmo_reference_sage.json').read_text(encoding='utf-8'))
DISTANCES = ('comoving', 'transverse', 'luminosity', 'angular_diameter', 'lookback')


@pytest.mark.parametrize('jeu', REFERENCE['jeux'], ids=lambda j: j['nom'])
def test_accord_avec_sagemath(jeu):
    """Écart relatif < 1e-4 sur toutes les grandeurs, de z = 10⁻⁶ au fond diffus, univers plats et courbes.
    (Constaté : ≤ 3·10⁻⁶ sur les distances, ≤ 2·10⁻⁵ sur les âges — ajustement de Komatsu des neutrinos.)"""
    al = calcul.al_par_mpc()
    for ref in jeu['valeurs']:
        d = calcul.calculer(ref['z'], jeu['modele'], jeu['H0'], jeu['Om'], jeu['Ok'], incertitudes=False)
        for k, v_ref in ref.items():
            if k == 'z' or v_ref in (None, 0):
                continue
            v = d[k] * al if k in DISTANCES else d[k]
            assert abs(v / v_ref - 1) < 1e-4, (jeu['nom'], ref['z'], k, v, v_ref)


def test_planck18_est_la_realisation_d_astropy():
    from astropy.cosmology import Planck18
    assert calcul.construire('planck18') is Planck18
    d = calcul.calculer(1.0)
    assert abs(d['lookback_gyr'] + d['age_at_z'] - d['t0_model']) < 1e-6 * d['t0_model']
    assert abs(d['t0_model'] - 13.7869) < 1e-3


def test_incertitudes_avec_le_terme_croise():
    d = calcul.calculer(1.0)
    pct = 100 * d['sigma']['comoving'] / d['comoving']
    assert 0.2 < pct < 0.5                           # 0,31 % (même valeur que le calculateur d'origine)
    assert d['sigma']['comoving'] < d['sigma_indep']['comoving']   # H0 et Ωm anticorrélés : l'incertitude baisse
    assert 'sigma' not in calcul.calculer(1.0, 'wmap9')


def test_shoes():
    d = calcul.calculer(1.0, shoes=True)
    assert d['shoes']['comoving'] < d['comoving'] and -9 < d['shoes']['ecart_pct']['comoving'] < -6


@pytest.mark.parametrize('z,cle', [('0', 'cosmo_err_z_negatif'), ('-0.001', 'cosmo_err_z_negatif'),
                                   ('2000', 'cosmo_err_z_grand'), ('abc', 'cosmo_err_z_illisible'),
                                   ('nan', 'cosmo_err_z_illisible')])
def test_z_refuse_avec_explication(z, cle):
    with pytest.raises(calcul.ErreurCosmo) as e:
        calcul.calculer(z)
    assert e.value.cle == cle


def test_virgule_acceptee():
    assert calcul.verifier_z('0,158') == pytest.approx(0.158)


def test_parametres_hors_bornes():
    for args, cle in ((('planck18', None, None, 0.1), 'cosmo_err_ok'), (('perso', 30.0, 0.3, 0.0), 'cosmo_err_h0'),
                      (('perso', 70.0, 0.05, 0.0), 'cosmo_err_om'), (('perso', 70.0, 0.3, 0.5), 'cosmo_err_ok')):
        with pytest.raises(calcul.ErreurCosmo) as e:
            calcul.construire(*args)
        assert e.value.cle == cle


def test_univers_sans_big_bang_refuse(monkeypatch):
    monkeypatch.setitem(calcul.BORNES, 'Om', (0.01, 1.0))
    monkeypatch.setitem(calcul.BORNES, 'Ok_perso', (-2.0, 2.0))
    with pytest.raises(calcul.ErreurCosmo) as e:
        calcul.construire('perso', 70.0, 0.02, -1.5)       # ΩΛ ≈ 2,5 : rebond
    assert e.value.cle in ('cosmo_err_rebond', 'cosmo_err_parametres')


def test_avertissements():
    assert 'cosmo_av_proche' in calcul.calculer(0.004)['avertissements']
    assert calcul.calculer(0.5)['avertissements'] == []
    assert 'cosmo_av_opaque' in calcul.calculer(1200)['avertissements']


def test_volume_developpement_raccorde_forme_fermee():
    """Le développement limité (petit Ωk·x²) et la forme fermée de Hogg se raccordent sans saut."""
    m = calcul.construire('perso', 70.0, 0.3, 0.2)
    dh = calcul.c_kms() / 70.0
    for u in (0.9e-3, 1.1e-3):
        dm = dh * math.sqrt(u / 0.2)
        v = calcul.volume_comobile_gpc3(m, dm)
        x = dm / dh
        r = math.sqrt(0.2)
        ferme = 4 * math.pi * dh ** 3 / (2 * 0.2) * (x * math.sqrt(1 + u) - math.asinh(r * x) / r) / 1e9
        assert abs(v / ferme - 1) < 1e-8
    assert calcul.volume_comobile_gpc3(m, 1e-3) > 0          # là où astropy rend un volume négatif


def test_courbes_et_csv(tmp_path, langue):
    langue('fr')
    c = calcul.courbes(calcul.grille_z(0.01, 10, 20))
    assert len(c['z']) == 20 and all(c['comoving'][i] < c['comoving'][i + 1] for i in range(19))
    formats.ecrire_csv_courbes(tmp_path / 'c.csv', c)
    lignes = list(csv.reader(open(tmp_path / 'c.csv', encoding='utf-8-sig'), delimiter=';'))
    assert lignes[0][:3] == ['z', 'D_C_Mpc', 'D_M_Mpc'] and len(lignes) == 21
    d = calcul.calculer(0.158, shoes=True)
    formats.ecrire_csv_resultats(tmp_path / 'r.csv', [d])
    lignes = list(csv.reader(open(tmp_path / 'r.csv', encoding='utf-8-sig'), delimiter=';'))
    assert len(lignes) == 1 + len(calcul.GRANDEURS)
    dc = next(l for l in lignes if l[1] == 'comoving')
    assert dc[4] == 'Mpc' and abs(float(dc[3]) - d['comoving']) < 1e-6 and float(dc[5]) > 0 and float(dc[6]) > 0


def test_formats_dans_les_deux_langues(langue):
    langue('fr')
    assert formats.court(0.158) == '0,158' and 'G al' in formats.valeur('comoving', 5000.0)
    assert "milliards d'années" in formats.valeur('age_at_z', 5.9)
    langue('en')
    assert formats.court(0.158) == '0.158' and 'Gly' in formats.valeur('comoving', 5000.0)


def test_cli(capsys, tmp_path):
    code = cli.main(['--lang', 'en', 'cosmo', '1', '--json'])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and abs(out['resultats'][0]['age_at_z'] - 5.86) < 0.01
    code = cli.main(['--lang', 'fr', 'cosmo', '0.158', '--modele', 'wmap9', '--csv', str(tmp_path / 'x.csv')])
    out = capsys.readouterr().out
    assert code == 0 and 'Distance de luminosité' in out and (tmp_path / 'x.csv').exists()
    assert cli.main(['cosmo', '0']) == 2
    assert cli.main(['cosmo']) == 2
    assert cli.main(['cosmo', '--courbes', '0.01', '10', '5', '--csv', str(tmp_path / 'c.csv')]) == 0
    assert (tmp_path / 'c.csv').read_text(encoding='utf-8-sig').count('\n') == 6
