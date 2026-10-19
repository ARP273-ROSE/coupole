"""Partages du DU, outil Parallaxe (0.8.0) : mesures sur images synthétiques (centre de la Lune, Lune saturée,
objet mobile d'une série, trait d'une pose longue), WCS d'un FITS et lieu/heure de l'en-tête."""
import datetime as D
import io

import numpy as np
import pytest

from coupole.modules.partages.analyses.parallaxe import image as I

from . import partages_exemple as X


@pytest.mark.parametrize('terminateur', [False, True], ids=['pleine', 'gibbeuse'])
def test_centre_de_la_lune(terminateur):
    a = X.disque(600, 800, 412.3, 287.8, 95.0, terminateur)
    c = I.centre_lune(a, 95.0)
    assert abs(c['x'] - 412.3) < 0.3 and abs(c['y'] - 287.8) < 0.3 and abs(c['r'] - 95.0) < 1.0
    assert not c['douteux'] and c['saturation'] < 0.5


def test_lune_saturee_signalee():
    """Smartphone : disque réel de 35 px, tache saturée de 80 px (valeur maximale partout)."""
    a = X.disque(500, 500, 250.0, 240.0, 80.0, False)
    a = np.minimum(a, 255.0)
    c = I.centre_lune(a, 35.0)
    assert c['douteux'] and c['saturation'] > 0.5


def test_objet_mobile_et_trait():
    rng = np.random.default_rng(1)
    fond = [rng.normal(100, 3, (200, 300)).astype(np.float32) for _ in range(3)]
    for k, f in enumerate(fond):
        yy, xx = np.mgrid[0:200, 0:300]
        f += 500 * np.exp(-((xx - 50 - 60 * k) ** 2 + (yy - 80 - 10 * k) ** 2) / 4.0)
    o = I.objet_mobile(fond[1], [fond[0], fond[2]])
    assert abs(o['x'] - 110) < 0.5 and abs(o['y'] - 90) < 0.5
    pose = rng.normal(100, 3, (300, 400)).astype(np.float32)
    for t in np.linspace(0, 1, 400):
        x, y = 60 + 250 * t, 50 + 150 * t
        pose[int(round(y)), int(round(x))] += 400
    tr = I.trait_principal(pose)
    bouts = sorted([(tr['x1'], tr['y1']), (tr['x2'], tr['y2'])])
    assert np.hypot(bouts[0][0] - 60, bouts[0][1] - 50) < 4 and np.hypot(bouts[1][0] - 310, bouts[1][1] - 200) < 4


def test_fits_wcs_lieu_et_heure(tmp_path):
    octets, (ra, dec) = X.fits_lune(X.PARIS, X.T_LUNE, 'Observateur A')
    p = tmp_path / 'a.fits'
    p.write_bytes(octets)
    img = I.lire(str(p))
    assert img.wcs is not None and abs(I.echelle_arcsec(img) - 8.0) < 1e-6
    assert I.pixel_vers_radec(img, 300.0, 250.0) == pytest.approx((ra, dec), abs=1e-9)
    lh = I.lieu_et_heure(img.entete)
    assert (lh['lat'], lh['lon'], lh['alt_m']) == pytest.approx(X.PARIS)
    assert lh['milieu'] == X.T_LUNE + D.timedelta(seconds=0.5)
    assert I.lieu_et_heure({'SITELAT': '+44:13:51:00', 'SITELONG': '+02:33:48:99', 'DATE-OBS': '2025-11-03',
                            'TIME-OBS': '18:38:25.5'})['lat'] == pytest.approx(44 + 13 / 60 + 51 / 3600)
    # WCS posée à côté (fichier .wcs d'astrometry.net / ASTAP)
    from astropy.io import fits
    q = tmp_path / 'b.fits'
    fits.PrimaryHDU(img.donnees).writeto(q)
    h = fits.Header()
    for k in ('CTYPE1', 'CTYPE2', 'CRVAL1', 'CRVAL2', 'CRPIX1', 'CRPIX2', 'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2'):
        h[k] = img.entete[k]
    s = io.BytesIO()
    fits.PrimaryHDU(header=h).writeto(s)
    (tmp_path / 'b.wcs').write_bytes(s.getvalue())
    assert I.pixel_vers_radec(I.lire(str(q)), 300.0, 250.0) == pytest.approx((ra, dec), abs=1e-9)
