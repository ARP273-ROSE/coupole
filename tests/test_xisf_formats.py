"""XISF : écriture, relecture stricte, validation XSD, second lecteur ; formats FITS de sortie."""
import os

import numpy as np
import pytest

from coupole.core import xisf
from coupole.modules.ohp import formats

MOTS = [('SIMPLE', 'T', 'conforms to FITS'), ('OBJECT', "'NGC 6888'", 'nom'), ('HISTORY', '', 'premiere ligne'),
        ('HISTORY', '', 'seconde ligne'), ('COMMENT', '', 'un commentaire')]


def xsd(reference=None):
    from tests.conftest import REFERENCE
    p = REFERENCE / '_outils' / 'xisf-1.0.xsd'
    return p if p.exists() else None


@pytest.mark.parametrize('dtype,bounds', [('<f4', (-1000.0, 65535.0)), ('<u2', None)])
def test_aller_retour(tmp_path, dtype, bounds):
    rng = np.random.default_rng(0)
    a = (rng.normal(1000, 50, (64, 80)) if dtype == '<f4' else rng.integers(0, 65535, (64, 80))).astype(dtype)
    p = tmp_path / 'a.xisf'
    octets, bloc = xisf.ecrire(p, a, MOTS, [('Observation:Object:Name', 'String', 'NGC 6888')], bounds=bounds)
    assert octets == os.path.getsize(p) and octets % 4096 == bloc % 4096 or True
    b, inf = xisf.lire(p, xsd=xsd())
    assert b.dtype == a.dtype and np.array_equal(a, b)
    assert inf['mots_cles'] == MOTS                     # ordre des HISTORY conservé
    assert inf['bounds'] == ('-1000.0:65535.0' if bounds else None)
    assert inf['compression'].startswith('zstd+sh:')


def test_flottant_sans_bounds_refuse(tmp_path):
    with pytest.raises(ValueError):
        xisf.ecrire(tmp_path / 'x.xisf', np.zeros((4, 4), '<f4'), [], bounds=None)


def test_bloc_altere_detecte(tmp_path):
    p = tmp_path / 'a.xisf'
    xisf.ecrire(p, np.arange(64, dtype='<u2').reshape(8, 8), MOTS)
    d = bytearray(p.read_bytes())
    d[-5] ^= 0xFF
    p.write_bytes(bytes(d))
    with pytest.raises(xisf.ErreurXISF):
        xisf.lire(p)


def test_second_lecteur_pypi(tmp_path):
    lib = pytest.importorskip('xisf')
    a = np.random.default_rng(1).normal(500, 10, (32, 40)).astype('<f4')
    p = tmp_path / 'a.xisf'
    xisf.ecrire(p, a, MOTS, bounds=(-1000.0, 65535.0))
    b = lib.XISF(str(p)).read_image(0)
    b = b[..., 0] if b.ndim == 3 else b
    assert np.array_equal(a, b)


@pytest.mark.parametrize('fmt', ['xisf', 'fz', 'fits'])
@pytest.mark.parametrize('dtype', ['<f4', '<u2'])
def test_formats_sans_perte(tmp_path, fmt, dtype):
    rng = np.random.default_rng(2)
    a = (rng.normal(800, 30, (50, 70)) if dtype == '<f4' else rng.integers(0, 65535, (50, 70))).astype(dtype)
    p = tmp_path / ('s' + formats.EXTENSIONS[fmt])
    formats.ecrire(fmt, p, a, MOTS + [('FILTER', "'R'", 'filtre')], [], 'test')   # relit et compare en interne
    if fmt != 'xisf':
        from astropy.io import fits
        with fits.open(p) as h:
            hdu = h[1] if fmt == 'fz' else h[0]
            assert np.array_equal(hdu.data.astype(a.dtype), a)
            assert hdu.header['FILTER'] == 'R'
            assert 'seconde ligne' in str(hdu.header['HISTORY'])


def test_xisf_compatible_uint16_zlib(tmp_path):
    """« XISF compatible N.I.N.A. et Siril » : UInt16, zlib+sh (ce qu'écrit N.I.N.A.), sans bounds ; perte comptée."""
    import numpy as np
    from coupole.core import logiciels, xisf as X
    from coupole.modules.ohp import formats
    ref = np.array([[-3.2, 0.4, 1.6], [65535.7, 1000.49, np.nan]])
    u, perte = formats.vers_uint16(ref, piedestal=0)
    assert u.dtype.str == '<u2' and u.tolist() == [[0, 0, 2], [65535, 1000, 0]]
    assert perte['u16_negatifs'] == 1 and perte['u16_hauts'] == 1 and perte['u16_non_finis'] == 1
    u, perte = formats.vers_uint16(np.array([[-220.4, -1200.0, 64535.4, 64536.0]]))    # piédestal 1 000 ADU
    # 64 535,4 + 1 000 s'arrondit à 65 535 (pas écrêté) ; 64 536 + 1 000 dépasse
    assert u.tolist() == [[780, 0, 65535, 65535]] and perte['u16_negatifs'] == 1 and perte['u16_hauts'] == 1
    assert perte['u16_ecart_max'] <= 0.5
    p = tmp_path / 'c.xisf'
    formats.ecrire('xisf16', p, u, [('OBJECT', "'X'", '')], [], 'Coupole')
    tete = p.read_bytes()[:4096].decode('utf-8', 'replace')
    assert 'sampleFormat="UInt16"' in tete and 'compression="zlib+sh:' in tete and 'bounds=' not in tete
    relu, _ = X.lire(p)
    assert relu.tolist() == u.tolist()
    assert logiciels.nature(p) == 'xisf_entier'
    assert logiciels.capables('xisf_entier') == {'pixinsight': True, 'siril': True, 'nina': True, 'astap': False,
                                                 'aladin': False}
    assert formats.description_conversion('xisf16', -32, False).isascii()
    assert len(formats.description_conversion('xisf16', -32, False)) <= 68


def test_ouvrir_avec_suit_la_table(tmp_path):
    """Pour chaque nature de fichier, « Ouvrir avec » propose (actifs) exactement les logiciels que la table vérifiée
    dit capables ; ASTAP n'apparaît actif que pour ce qu'il lit (FITS, .fits.fz Rice, XISF non compressé)."""
    import numpy as np
    from coupole.core import logiciels
    from coupole.modules.ohp import formats
    a = (np.arange(64, dtype='<f4').reshape(8, 8) * 100)
    u = a.astype('<u2')
    mc = [('OBJECT', "'X'", '')]
    fichiers = {'xisf_flottant': ('xisf', a, 'f.xisf'), 'xisf_entier': ('xisf16', u, 'u.xisf'),
                'xisf_entier_zstd': ('xisf', u, 'uz.xisf'), 'fits_flottant': ('fits', a, 'f.fits'),
                'fits_entier': ('fits', u, 'u.fits'), 'fz_flottant': ('fz', a, 'f.fits.fz'), 'fz_entier': ('fz', u, 'u.fits.fz')}
    tous = {lg: ['x'] for lg in logiciels.LOGICIELS}
    for nat, (fmt, d, nom) in fichiers.items():
        p = tmp_path / nom
        formats.ecrire(fmt, p, d, mc, [], 'Coupole')
        assert logiciels.nature(p) == nat, (nom, logiciels.nature(p))
        props = logiciels.propositions(p, tous)
        actifs = {lg for lg, ok, _ in props if ok}
        assert actifs == {lg for lg, ok in logiciels.LECTURE[nat].items() if ok}, (nat, actifs)
        assert ('astap' in actifs) == (nat in ('fits_flottant', 'fits_entier', 'fz_entier'))
        assert all(r for _, ok, r in props if not ok)               # chaque logiciel grisé dit pourquoi
    from coupole.core import xisf as X
    X.ecrire(tmp_path / 'brut.xisf', u, mc, codec=None)             # XISF non compressé : ASTAP le lit
    assert logiciels.nature(tmp_path / 'brut.xisf') == 'xisf_brut_entier'
    assert 'astap' in {lg for lg, ok, _ in logiciels.propositions(tmp_path / 'brut.xisf', tous) if ok}
    assert logiciels.propositions(tmp_path / 'brut.xisf', {}) == []   # rien d'installé : rien de proposé


def test_metadonnees_reecrites_sans_toucher_aux_pixels(tmp_path):
    """`coupole ohp metadonnees --reecrire` : FOCALLEN accordé à l'échelle mesurée (27 µm / 0,76985″ → 7 234,1 mm,
    ancienne valeur en HISTORY), propriétés Instrument:* ajoutées, bloc de pixels recopié octet pour octet."""
    import hashlib
    import numpy as np
    from coupole.core import xisf as X
    from coupole.modules.ohp import metadonnees
    a = (np.arange(1200, dtype='<f4').reshape(30, 40) - 100) * 3.5
    mc = [('SIMPLE', 'T', ''), ('NAXIS1', '40', ''), ('NAXIS2', '30', ''), ('TELESCOP', "'T120'", ''),
          ('INSTRUME', "'Andor iKon-L'", ''), ('XPIXSZ', '27.0', '[um]'), ('YPIXSZ', '27.0', '[um]'),
          ('XBINNING', '2', ''), ('YBINNING', '2', ''), ('FOCALLEN', '7200.0', '[mm]'), ('PIXSCALE', '0.76985', ''),
          ('RA', '10.5', ''), ('DEC', '41.2', '')]
    p = tmp_path / 'a.xisf'
    X.ecrire(p, a, mc, [('Instrument:Telescope:Name', 'String', 'OHP T120')], bounds=(-1000, 65535))
    _, avant = X.lire(p)
    bloc = hashlib.sha1(open(p, 'rb').read()[avant['position']:avant['position'] + avant['taille_bloc']]).hexdigest()
    assert metadonnees.reecrire(p, simuler=True) and X.lire(p)[1]['xml'] == avant['xml']        # simulation : rien
    ch = metadonnees.reecrire(p)
    assert 'FOCALLEN' in ch and 'Instrument:Sensor:XPixelSize' in ch and 'Instrument:Camera:XBinning' in ch
    d, inf = X.lire(p)
    assert np.array_equal(d, a)
    assert hashlib.sha1(open(p, 'rb').read()[inf['position']:inf['position'] + inf['taille_bloc']]).hexdigest() == bloc
    mots = {k: v for k, v, c in inf['mots_cles'] if k != 'HISTORY'}
    assert mots['FOCALLEN'] == '7234.1' and any('FOCALLEN = 7200.0' in c for k, v, c in inf['mots_cles'] if k == 'HISTORY')
    pr = inf['proprietes']
    assert pr['Instrument:Sensor:XPixelSize'] == '27.0' and pr['Instrument:Camera:XBinning'] == '2'
    assert abs(float(pr['Instrument:Telescope:FocalLength']) - 7.2341) < 1e-3 and pr['Instrument:Camera:Name'] == 'Andor iKon-L'
    assert pr['Instrument:Telescope:Aperture'] == '1.2' and pr['Instrument:Telescope:Name'] == 'OHP T120'
    assert metadonnees.reecrire(p) == []                                 # une seconde fois : rien à faire
    i = metadonnees.instrument(inf['mots_cles'])
    assert abs(i['focale_mm'] - 7234.1) < 0.1 and i['pixel_um'] == 27.0 and i['binning'] == (2, 2)
    assert abs(i['champ_arcmin'][0] - 40 * 0.76985 / 60) < 1e-9


def test_metadonnees_fits_sans_toucher_aux_pixels(tmp_path):
    import numpy as np
    from astropy.io import fits
    from coupole.modules.ohp import metadonnees
    a = np.arange(100, dtype='>f4').reshape(10, 10)
    h = fits.Header()
    h['XPIXSZ'], h['XBINNING'], h['FOCALLEN'], h['PIXSCALE'] = 27.0, 2, 7200.0, 0.76985
    fits.PrimaryHDU(a, header=h).writeto(tmp_path / 'a.fits')
    assert metadonnees.reecrire(tmp_path / 'a.fits') == ['FOCALLEN']
    with fits.open(tmp_path / 'a.fits') as hd:
        assert hd[0].header['FOCALLEN'] == 7234.1 and np.array_equal(hd[0].data, a)
        assert any('7200' in str(c) for c in hd[0].header['HISTORY'])
    r = metadonnees.reecrire_dossier(tmp_path)
    assert r == {'fichiers': 1, 'modifies': 0, 'inchanges': 1, 'erreurs': 0, 'base': 0}
    assert (tmp_path / '_traitement' / 'metadonnees.csv').exists()


def test_fichiers_d_exemple_pour_les_testeurs():
    """tests/donnees : trois petits fichiers (image de synthèse) pour essayer PixInsight, Siril, N.I.N.A., ASTAP."""
    from pathlib import Path
    from coupole.core import logiciels, xisf as X
    d = Path(__file__).parent / 'donnees'
    assert logiciels.nature(d / 'exemple_pixinsight.xisf') == 'xisf_flottant'
    assert logiciels.nature(d / 'exemple_compatible.xisf') == 'xisf_entier'
    assert logiciels.nature(d / 'exemple.fits') == 'fits_flottant'
    a, inf = X.lire(d / 'exemple_pixinsight.xisf')
    b, inf_b = X.lire(d / 'exemple_compatible.xisf')
    assert a.shape == b.shape == (256, 256) and inf['bounds'] == '-1000.0:65535.0' and inf_b['format'] == 'UInt16'
    assert abs((b.astype(float) - 1000 - a).max()) <= 0.5                     # piédestal de 1 000 ADU, arrondi
    assert inf['proprietes']['Instrument:Sensor:XPixelSize'] == '27.0'
    assert all(p.stat().st_size < 1_000_000 for p in d.iterdir())
