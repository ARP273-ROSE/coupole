"""XISF 1.0 révision 2 (octobre 2026) : blocs compressés en sous-blocs, sous-blocs incompressibles stockés tels quels.

PixInsight ≥ 1.9.6 écrit ainsi tout XISF compressé (sous-blocs de 4 Mio).  Les fichiers sont fabriqués ici par un
encodeur indépendant du lecteur de Coupole, d'après le § 10.6 de la spécification : byte shuffling sur le bloc entier,
découpe, chaque sous-bloc compressé à part, stocké tel quel (c == u) s'il ne raccourcit pas.
"""
import hashlib
import zlib

import numpy as np
import pytest

from coupole.core import xisf

TAILLE_SB = 64 * 1024        # 4 Mio chez PixInsight ; plus petit ici pour garder des images de test légères


def _melanger(octets, n):
    a = np.frombuffer(octets, np.uint8)
    m = len(a) // n
    return a.reshape(m, n).T.tobytes()


def _compresser(base, octets):
    if base == 'zlib':
        return zlib.compress(octets, 6)
    if base == 'zstd':
        zstandard = pytest.importorskip('zstandard')
        return zstandard.ZstdCompressor(level=10).compress(octets)
    lz4b = pytest.importorskip('lz4.block')
    if base == 'lz4hc':
        return lz4b.compress(octets, mode='high_compression', compression=9, store_size=False)
    return lz4b.compress(octets, store_size=False)


def _ecrire_rev2(chemin, a, codec, taille_sb=TAILLE_SB, checksum='sha1', subblocks_force=None):
    """Écrit un XISF monolithique au format de la révision 2 ; rend la liste des sous-blocs (c, u)."""
    brut = a.tobytes()
    item = a.dtype.itemsize
    base = codec.split('+')[0]
    donnees = _melanger(brut, item) if codec.endswith('+sh') else brut
    morceaux, sb = [], []
    for i in range(0, len(donnees), taille_sb):
        p = donnees[i:i + taille_sb]
        z = _compresser(base, p)
        if len(z) >= len(p):
            z = p
        morceaux.append(z)
        sb.append((len(z), len(p)))
    bloc = b''.join(morceaux)
    comp = '%s:%d:%d' % (codec, len(brut), item) if codec.endswith('+sh') else '%s:%d' % (codec, len(brut))
    attr_sb = subblocks_force or ':'.join('%d,%d' % s for s in sb)
    fmt = {'<u2': 'UInt16', '<f4': 'Float32'}[a.dtype.str]
    bounds = ' bounds="0:1"' if fmt == 'Float32' else ''
    h = getattr(hashlib, checksum.replace('-', '_'))(bloc).hexdigest()
    pos = 8192
    xml = ('<?xml version="1.0" encoding="UTF-8"?><xisf version="1.0" xmlns="http://www.pixinsight.com/xisf">'
           '<Image geometry="%d:%d:1" sampleFormat="%s"%s location="attachment:%d:%d" compression="%s" '
           'subblocks="%s" checksum="%s:%s"/></xisf>'
           % (a.shape[1], a.shape[0], fmt, bounds, pos, len(bloc), comp, attr_sb, checksum, h)).encode()
    with open(chemin, 'wb') as f:
        f.write(b'XISF0100' + len(xml).to_bytes(4, 'little') + b'\0' * 4 + xml)
        f.write(b'\0' * (pos - 16 - len(xml)) + bloc)
    return sb


def _image(dtype, bruit=True):
    """Fond lisse (octets forts compressibles) + bruit (octets faibles incompressibles) : comme une vraie pose."""
    rng = np.random.default_rng(7)
    ny, nx = 300, 400
    fond = 1000 + 50 * np.sin(np.arange(nx) / 40.0)[None, :] + np.zeros((ny, 1))
    a = fond + (rng.normal(0, 400, (ny, nx)) if bruit else 0)
    if dtype == '<f4':
        return (a / 65535).astype('<f4')
    return np.clip(a, 0, 65535).astype('<u2')


@pytest.mark.parametrize('codec', ['zlib+sh', 'zstd+sh', 'lz4hc+sh', 'lz4+sh', 'zlib', 'zstd'])
@pytest.mark.parametrize('dtype', ['<u2', '<f4'])
def test_sous_blocs_relus_bit_a_bit(tmp_path, codec, dtype):
    a = _image(dtype)
    p = tmp_path / 'rev2.xisf'
    sb = _ecrire_rev2(p, a, codec)
    assert len(sb) > 1
    b, inf = xisf.lire(p)
    assert b.dtype == a.dtype and np.array_equal(a, b)


def test_sous_blocs_non_compresses_presents_et_relus(tmp_path):
    """Le cas qui faisait échouer l'ancien lecteur : des sous-blocs stockés tels quels (c == u)."""
    a = _image('<f4')
    p = tmp_path / 'brut.xisf'
    sb = _ecrire_rev2(p, a, 'zstd+sh')
    assert any(c == u for c, u in sb) and any(c < u for c, u in sb)
    assert np.array_equal(xisf.lire(p)[0], a)


def test_sous_blocs_incoherents_refuses(tmp_path):
    a = _image('<u2')
    p = tmp_path / 'faux.xisf'
    sb = _ecrire_rev2(p, a, 'zlib+sh')
    faux = ':'.join('%d,%d' % (c, u) for c, u in sb[:-1])          # il manque le dernier sous-bloc
    _ecrire_rev2(p, a, 'zlib+sh', subblocks_force=faux)
    with pytest.raises(xisf.ErreurXISF):
        xisf.lire(p)


@pytest.mark.parametrize('algo', ['sha3-256', 'sha3-512'])
def test_checksums_sha3(tmp_path, algo):
    a = _image('<u2')
    p = tmp_path / 'sha3.xisf'
    _ecrire_rev2(p, a, 'zlib+sh', checksum=algo)
    assert np.array_equal(xisf.lire(p)[0], a)


def test_bloc_unique_inchange(tmp_path):
    """Les fichiers sans attribut subblocks (N.I.N.A., ASIAIR, Coupole, PixInsight ≤ 1.9.5) se lisent comme avant."""
    a = _image('<u2')
    p = tmp_path / 'mono.xisf'
    xisf.ecrire(p, a, [], codec='zlib+sh', niveau=6)
    assert np.array_equal(xisf.lire(p, strict=True)[0], a)


def test_second_lecteur_pypi_revision_2(tmp_path):
    """La bibliothèque PyPI « xisf » ≥ 1.0.1 lit la révision 2 : elle confirme les fichiers de l'encodeur de test."""
    mod = pytest.importorskip('xisf')
    try:
        version = tuple(int(v) for v in mod.__version__.split('.')[:3])
    except (AttributeError, ValueError):
        pytest.skip('version de xisf inconnue')
    if version < (1, 0, 1):
        pytest.skip('xisf < 1.0.1 ne lit pas les sous-blocs')
    a = _image('<f4')
    p = tmp_path / 'pypi.xisf'
    _ecrire_rev2(p, a, 'zstd+sh')
    assert np.array_equal(np.asarray(mod.XISF(str(p)).read_image(0)).reshape(a.shape), a)
