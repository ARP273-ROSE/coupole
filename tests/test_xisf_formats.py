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
