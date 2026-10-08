"""Conversion d'une vraie image de la banque (exemple/ex.fits : T120, C/2021 S3, R, 60 s) et cas pièges."""
import csv
import os
import shutil
import subprocess
import sys

import numpy as np
import pytest

from coupole.core import xisf
from coupole.modules.ohp import astrometrie, conversion


@pytest.fixture(scope='module')
def ex(reference, inventaire, tmp_path_factory):
    src = reference / 'exemple' / 'ex.fits'
    if not src.exists():
        pytest.skip('exemple/ex.fits absent')
    d = tmp_path_factory.mktemp('ex')
    shutil.copy(src, d / 'ex.fits')
    urls = [x for x in inventaire.images if x['access_url'].endswith('2021S3_R_60000_0097b5bd6c037ef93af4b016990d003a_aux.fits')]
    x = next(u for u in urls if not u['doublon'])
    med, medo = astrometrie.attentes(inventaire.images)
    m1, m2 = astrometrie.attentes_pour(x, med, medo)
    return d, x, m1, m2


def test_conversion_sans_astap_comme_la_reference(ex, reference):
    d, x, m1, m2 = ex
    info = conversion.convertir(x, str(d / 'ex.fits'), str(d / 'ex.xisf'), m1, m2, {'format': 'xisf', 'langue': 'fr'})
    assert info['wcs'] == 'validee' and not info['doutes']          # sans ASTAP : contrôles de cohérence
    assert info['position'] == 'inversee' and info['site_mots_cles'] == 'ok'
    with open(reference / 'traitement' / 'journal.csv', encoding='utf-8-sig') as f:
        ref = next(r for r in csv.DictReader(f, delimiter=';') if r['url'] == x['access_url'] and r['statut'] == 'ok')
    assert ' '.join(info['modifs']) == ref['mots_cles_modifies']
    assert abs(info['ratio'] - float(ref['ratio'])) < 0.002
    assert abs(info['ecart_max'] - float(ref['ecart_max_adu'])) < 1e-9
    data, inf = xisf.lire(d / 'ex.xisf')
    mots = {k: v for k, v, c in inf['mots_cles'] if k not in ('HISTORY', 'COMMENT')}
    assert mots['LATITUDE'] == "'43 55 55'" and mots['SITELAT'] == "'+43 55 54.7'"
    assert mots['OBJECT'] == "'C/2021 S3 (PANSTARRS)'" and mots['FILTER'] == "'R'" and mots['DATEDOUT'] == 'T'
    assert any("valeur d'origine : LATITUDE = '05 42 44'" in c for k, v, c in inf['mots_cles'] if k == 'HISTORY')
    assert inf['proprietes']['OHP:Astrometry:Status'] == 'validee'
    assert inf['bounds'] == '-1000.0:65535.0' and data.dtype == np.dtype('<f4')


def test_en_tetes_en_anglais(ex):
    d, x, m1, m2 = ex
    info = conversion.convertir(x, str(d / 'ex.fits'), str(d / 'ex_en.xisf'), m1, m2, {'format': 'xisf', 'langue': 'en'})
    _, inf = xisf.lire(d / 'ex_en.xisf')
    h = [c for k, v, c in inf['mots_cles'] if k == 'HISTORY']
    assert any(c.startswith('original value: LATITUDE') for c in h)
    assert info['objet_affiche'] == 'C/2021 S3 (PANSTARRS)'


def test_ctype_sip_sans_coefficients(tmp_path, inventaire):
    """PinPoint (IRIS) : CTYPE annonce -SIP sans A_/B_ → ramené à TAN, ancienne valeur en HISTORY."""
    from astropy.io import fits
    x = next(y for y in inventaire.images if y['tel'] == 'IRIS' and not y['doublon'] and y['cat'] == 'neb')
    h = fits.Header()
    h.update(CTYPE1='RA---TAN-SIP', CTYPE2='DEC--TAN-SIP', CRVAL1=x['s_ra'], CRVAL2=x['s_dec'], CRPIX1=32.5,
             CRPIX2=32.5, CD1_1=-0.68 / 3600, CD1_2=0.0, CD2_1=0.0, CD2_2=0.68 / 3600, LATITUDE='05 42 44',
             LONGITUD='43 55 54', DATE_OBS=None)
    h['DATE-OBS'] = '2024-07-04T22:58:47.000'
    rng = np.random.default_rng(0)
    fits.PrimaryHDU((rng.normal(30000, 50, (64, 64)) - 32768).astype('>i2'), header=h).writeto(tmp_path / 'i.fits')
    with fits.open(tmp_path / 'i.fits', mode='update') as hd:
        hd[0].header['BZERO'] = 32768
        hd[0].header['BSCALE'] = 1
    info = conversion.convertir(x, str(tmp_path / 'i.fits'), str(tmp_path / 'i.xisf'), {}, {}, {'format': 'xisf'})
    _, inf = xisf.lire(tmp_path / 'i.xisf')
    mots = {k: v for k, v, c in inf['mots_cles'] if k not in ('HISTORY', 'COMMENT')}
    assert mots['CTYPE1'] == "'RA---TAN'" and inf['format'] == 'UInt16'
    assert info['bitpix'] == 16


def test_doublon_de_pixels_detecte(tmp_path, ex):
    from coupole.modules.ohp.pilote import Etat
    e = Etat(str(tmp_path / 'etat.sqlite'))
    assert e.empreinte('abc', 'img1') is None
    assert e.empreinte('abc', 'img2') == 'img1'                  # mêmes pixels : doublon de img1
    assert e.empreinte('abc', 'img1') is None                    # idempotent pour la même image
    e.fermer()


@pytest.mark.skipif(not os.environ.get('COUPOLE_TEST_RESEAU'), reason='essai réseau : COUPOLE_TEST_RESEAU=1')
def test_bout_en_bout_reseau(tmp_path, reference):
    """Télécharge (914) Palisana + 2 IRIS (109 Mo) et compare au traitement de référence."""
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, os.path.join(racine, 'outils', 'essai_reel.py'), str(tmp_path / 'sortie')],
                   check=True)
    copie = os.environ.get('COUPOLE_COPIE_REFERENCE', '')
    r = subprocess.run([sys.executable, os.path.join(racine, 'outils', 'comparer_reference.py'),
                        str(tmp_path / 'sortie'), str(reference / 'traitement')] + ([copie] if copie else []),
                       capture_output=True, text=True, check=True)
    assert 'aucun écart' in r.stdout, r.stdout
