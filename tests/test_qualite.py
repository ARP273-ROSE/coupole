"""Module Qualité : chaque mesure doit retrouver les valeurs injectées (sinon elle est retirée)."""
import numpy as np
import pytest

from coupole.modules.qualite import mesures as M

from .synthetique import image

pytestmark = pytest.mark.skipif(not M.disponible(), reason='sep absent (dépendance facultative)')


@pytest.mark.parametrize('profil', ['gauss', 'moffat'])
@pytest.mark.parametrize('fwhm', [2.5, 4.0, 7.0])
def test_fwhm(profil, fwhm):
    r = M.analyser(image(fwhm=fwhm, profil=profil, etoiles=80), {'EXPTIME': 60})
    assert abs(r['fwhm_px'] / fwhm - 1) < 0.02, r['fwhm_px']
    assert r['ellipticite'] < 0.02 and r['etoiles'] > 40


@pytest.mark.parametrize('e', [0.1, 0.25])
def test_ellipticite(e):
    r = M.analyser(image(fwhm=4.0, e=e, etoiles=80), {})
    assert abs(r['ellipticite'] - e) < 0.02


def test_fond_bruit_echelle():
    r = M.analyser(image(fond=800, bruit=12, etoiles=60), {'EXPTIME': 40, 'PIXSCALE': 0.77})
    assert abs(r['fond_adu'] / 800 - 1) < 0.005 and abs(r['bruit_adu'] / 12 - 1) < 0.05
    assert abs(r['fond_adu_s'] - r['fond_adu'] / 40) < 1e-9
    assert abs(r['fwhm_arcsec'] - r['fwhm_px'] * 0.77) < 1e-9 and r['echantillonnage'] == 'correct'
    assert r['gradient_pct'] < 0.5 and r['residu_pct'] < 1.0


def test_gradient_et_vignetage():
    r = M.analyser(image(gradient=0.10, etoiles=60), {})
    # gradient horizontal de 10 % sur la largeur → 10 % × √2 sur la diagonale, divisé par le fond médian (1,05)
    attendu = 10 * np.sqrt(2) / 1.05
    assert abs(r['gradient_pct'] - attendu) < 0.8 and abs(r['gradient_angle']) < 5
    v = M.analyser(image(vignetage=0.08, etoiles=60), {})
    assert v['gradient_pct'] < 1.0 and 5.0 < v['residu_pct'] < 9.0


def test_carte_3x3_variation_de_champ():
    r = M.analyser(image(etoiles=400, fwhm_fn=lambda x, y: 3.0 + 3.0 * x / 1024), {})
    lignes = r['carte_fwhm']
    for ligne in lignes:
        assert ligne[0] < ligne[1] < ligne[2]
    assert abs(lignes[1][0] - 3.5) < 0.25 and abs(lignes[1][2] - 5.5) < 0.25


def test_saturation_et_trainee():
    r = M.analyser(image(satures=5, trainee=True, etoiles=60), {})
    assert r['satures'] == 5
    assert r['trainees'] == 1
    r2 = M.analyser(image(etoiles=60), {})
    assert r2['satures'] == 0 and r2['trainees'] == 0


def test_rsn_seulement_avec_le_gain():
    img = image(etoiles=60)
    assert M.analyser(img, {})['rsn'] is None
    r = M.analyser(img, {'EGAIN': 1.5})
    assert r['rsn'] is not None and r['rsn'] > 10


def test_echantillonnage():
    assert M.analyser(image(fwhm=1.6, profil='gauss', etoiles=60), {})['echantillonnage'] == 'sous'
    assert M.analyser(image(fwhm=7.0, etoiles=60), {})['echantillonnage'] == 'sur'
