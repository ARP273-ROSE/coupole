"""XISF 1.0 : écrivain minimal et lecteur indépendant (contrôle strict).

Repris de ``_outils/xisf_ecrire.py`` et ``_outils/xisf_lire.py`` (traitement de
la banque OHP du 7-8 octobre 2026, 7 625 fichiers validés par le schéma XSD
officiel et relus par la bibliothèque PyPI ``xisf``).

Écrivain, d'après la spécification XISF 1.0 révision 1 :
  § 9.2  fichier monolithique : 'XISF0100' + longueur de l'en-tête (uint32 LE)
         + 4 octets nuls + en-tête XML, puis bourrage nul et bloc attaché ;
  § 10.3 location="attachment:position:taille" ; § 10.5 checksum SHA-1 du bloc
         COMPRESSÉ ; § 10.6.2 byte shuffling ; § 10.6.10 zstd+sh ;
  § 11.4.1 Metadata obligatoire ; § 11.5.1 bounds obligatoire pour les flottants ;
  § 11.6 FITSKeyword name/value/comment dans l'ordre d'origine.
Pourquoi pas la bibliothèque PyPI « xisf » pour écrire : elle impose
bounds="0:1" à toute image flottante (nos ADU seraient écrêtés à 1) et regroupe
les mots-clés par nom (l'ordre des cartes HISTORY se perd).

Les messages d'exception sont techniques (anglais) ; l'interface les présente
via le système de traduction.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
import uuid as _uuid
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

import numpy as np

ALIGNEMENT = 4096
_FORMATS = {np.dtype('<f4'): 'Float32', np.dtype('<f8'): 'Float64', np.dtype('<u2'): 'UInt16',
            np.dtype('uint8'): 'UInt8', np.dtype('<u4'): 'UInt32'}
NS = '{http://www.pixinsight.com/xisf}'
TYPES = {'UInt8': 'u1', 'UInt16': '<u2', 'UInt32': '<u4', 'UInt64': '<u8', 'Float32': '<f4', 'Float64': '<f8'}
RE_ID = re.compile(r'^[_a-zA-Z][_a-zA-Z0-9]*(:[_a-zA-Z][_a-zA-Z0-9]*)*$')
RE_MOTCLE = re.compile(r'^[A-Z0-9_-]{1,8}$')


class ErreurXISF(Exception):
    pass


# ======================================================================== écriture
def melanger(octets: bytes, taille_item: int) -> bytes:
    """Byte shuffling (§ 10.6.2) ; la queue incomplète reste telle quelle."""
    if taille_item <= 1:
        return octets
    a = np.frombuffer(octets, np.uint8)
    n = len(a) // taille_item
    return a[:n * taille_item].reshape(n, taille_item).T.tobytes() + a[n * taille_item:].tobytes()


def compresser(octets: bytes, codec: str, niveau: int, taille_item: int) -> bytes:
    if codec.endswith('+sh'):
        octets = melanger(octets, taille_item)
    base = codec.split('+')[0]
    if base == 'zstd':
        import zstandard
        return zstandard.ZstdCompressor(level=niveau).compress(octets)
    if base in ('lz4hc', 'lz4'):
        import lz4.block
        if base == 'lz4hc':
            return lz4.block.compress(octets, mode='high_compression', compression=niveau, store_size=False)
        return lz4.block.compress(octets, store_size=False)
    if base == 'zlib':
        import zlib
        return zlib.compress(octets, niveau)
    raise ValueError('unknown codec: %s' % codec)


def xml_texte(s) -> str:
    """Retire les caractères interdits en XML 1.0 (contrôles)."""
    return ''.join(c for c in str(s) if c in '\t\n\r' or ord(c) >= 0x20)


def _propriete(pid, ptype, valeur):
    if ptype == 'String':
        return '<Property id=%s type="String">%s</Property>' % (quoteattr(pid), escape(xml_texte(valeur)))
    if ptype in ('Float64', 'Float32'):
        v = repr(float(valeur))
    elif ptype == 'Boolean':
        v = 'true' if valeur else 'false'
    else:
        v = str(valeur)
    return '<Property id=%s type=%s value=%s/>' % (quoteattr(pid), quoteattr(ptype), quoteattr(v))


def ecrire(chemin, donnees, mots_cles, proprietes=(), bounds=None, codec='zstd+sh', niveau=9,
           createur='Coupole', type_image='Light', niveau_abstrait=None):
    """Écrit une image 2-D en niveaux de gris.  Renvoie (octets du fichier, octets compressés).

    donnees : tableau (lignes, colonnes), ligne 0 écrite en premier (ordre du FITS).
    mots_cles : [(nom, valeur, commentaire)] dans l'ordre ; proprietes : [(id, type, valeur)].
    """
    a = np.ascontiguousarray(donnees)
    if a.dtype.byteorder == '>' or (a.dtype.byteorder == '=' and not np.little_endian):
        a = a.astype(a.dtype.newbyteorder('<'))
    fmt = _FORMATS[np.dtype(a.dtype.str.replace('=', '<').replace('|', ''))]
    if fmt.startswith('Float') and bounds is None:
        raise ValueError('bounds required for a floating point image (XISF 11.5.1)')
    brut = a.tobytes()
    taille_item = a.dtype.itemsize
    bloc = compresser(brut, codec, niveau, taille_item)
    compression = ('%s:%d:%d' % (codec, len(brut), taille_item)) if codec.endswith('+sh') \
        else '%s:%d' % (codec, len(brut))
    somme = hashlib.sha1(bloc).hexdigest()
    ny, nx = a.shape
    uid = str(_uuid.uuid4())
    maintenant = _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def entete(position):
        attrs = ['geometry="%d:%d:1"' % (nx, ny), 'sampleFormat="%s"' % fmt]
        if bounds is not None:
            attrs.append('bounds="%s:%s"' % (repr(float(bounds[0])), repr(float(bounds[1]))))
        attrs += ['colorSpace="Gray"', 'imageType="%s"' % type_image, 'compression="%s"' % compression,
                  'checksum="sha1:%s"' % somme, 'location="attachment:%d:%d"' % (position, len(bloc)),
                  'uuid="%s"' % uid]
        lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
                  '<!--\nExtensible Image Serialization Format - XISF version 1.0\nCreated with %s\n-->'
                  % escape(createur),
                  '<xisf version="1.0" xmlns="http://www.pixinsight.com/xisf" '
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                  'xsi:schemaLocation="http://www.pixinsight.com/xisf http://pixinsight.com/xisf/xisf-1.0.xsd">',
                  '<Image %s>' % ' '.join(attrs)]
        for pid, ptype, val in proprietes:
            lignes.append(_propriete(pid, ptype, val))
        for nom, val, com in mots_cles:
            lignes.append('<FITSKeyword name=%s value=%s comment=%s/>'
                          % (quoteattr(xml_texte(nom)), quoteattr(xml_texte(val)), quoteattr(xml_texte(com))))
        lignes += ['</Image>', '<Metadata>',
                   _propriete('XISF:CreationTime', 'TimePoint', maintenant),
                   _propriete('XISF:CreatorApplication', 'String', createur),
                   _propriete('XISF:BlockAlignmentSize', 'UInt16', ALIGNEMENT),
                   _propriete('XISF:ChecksumAlgorithms', 'String', 'sha1')]
        if niveau_abstrait is not None:
            lignes.append(_propriete('XISF:CompressionLevel', 'Int32', niveau_abstrait))
        lignes += ['</Metadata>', '</xisf>']
        return '\n'.join(lignes).encode('utf-8')

    position = ALIGNEMENT
    for _ in range(10):            # la position s'écrit dans l'en-tête : itérer jusqu'à stabilité
        x = entete(position)
        besoin = -(-(16 + len(x)) // ALIGNEMENT) * ALIGNEMENT
        if besoin == position:
            break
        position = besoin
    else:
        raise RuntimeError('unstable block position')
    tmp = str(chemin) + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(b'XISF0100')
        f.write(len(x).to_bytes(4, 'little'))
        f.write(b'\0\0\0\0')
        f.write(x)
        f.write(b'\0' * (position - 16 - len(x)))
        f.write(bloc)
        f.flush()
    os.replace(tmp, chemin)
    return position + len(bloc), len(bloc)


# ======================================================================== lecture (contrôle strict)
def _verifier(cond, msg):
    if not cond:
        raise ErreurXISF(msg)


def _desordonner(octets, n):
    if n <= 1:
        return octets
    a = np.frombuffer(octets, np.uint8)
    m = len(a) // n
    return a[:m * n].reshape(n, m).T.tobytes() + a[m * n:].tobytes()


def _decompresser(bloc, spec):
    parts = spec.split(':')
    codec = parts[0]
    taille = int(parts[1])
    item = 1
    if codec.endswith('+sh'):
        _verifier(len(parts) == 3, 'compression %s: missing item size' % spec)
        item = int(parts[2])
    base = codec.split('+')[0]
    if base == 'zstd':
        import zstandard
        d = zstandard.ZstdDecompressor().decompress(bloc, max_output_size=taille)
    elif base in ('lz4', 'lz4hc'):
        import lz4.block
        d = lz4.block.decompress(bloc, uncompressed_size=taille)
    elif base == 'zlib':
        import zlib
        d = zlib.decompress(bloc)
    else:
        raise ErreurXISF('non standard codec: %s' % codec)
    _verifier(len(d) == taille, 'decompressed size %d != %d' % (len(d), taille))
    return _desordonner(d, item) if codec.endswith('+sh') else d


def valider_xsd(xml: bytes, xsd) -> None:
    from lxml import etree  # facultatif : seulement pour la validation par schéma
    schema = etree.XMLSchema(etree.parse(str(xsd)))
    if not schema.validate(etree.fromstring(xml)):
        raise ErreurXISF('XSD: %s' % schema.error_log.last_error)


def lire(chemin, xsd=None):
    """Lit et contrôle un XISF monolithique à une image.  Renvoie (tableau, infos)."""
    with open(chemin, 'rb') as f:
        tout = f.read()
    _verifier(tout[:8] == b'XISF0100', 'signature missing')
    lg = int.from_bytes(tout[8:12], 'little')
    _verifier(tout[12:16] == b'\0\0\0\0', 'reserved field not zero')
    xml = tout[16:16 + lg]
    _verifier(xml.startswith(b'<?xml version="1.0" encoding="UTF-8"?>'), 'XML declaration missing')
    xml.decode('utf-8')
    racine = ET.fromstring(xml)
    _verifier(racine.tag == NS + 'xisf', 'root %s' % racine.tag)
    _verifier(racine.get('version') == '1.0', 'root version')
    if xsd is not None:
        valider_xsd(xml, xsd)
    meta = racine.find(NS + 'Metadata')
    _verifier(meta is not None, 'Metadata missing')
    ids = {p.get('id') for p in meta.findall(NS + 'Property')}
    _verifier({'XISF:CreationTime', 'XISF:CreatorApplication'} <= ids, 'mandatory Metadata properties missing')
    images = racine.findall(NS + 'Image')
    _verifier(len(images) == 1, '%d images' % len(images))
    im = images[0]
    geo = [int(v) for v in im.get('geometry').split(':')]
    _verifier(len(geo) == 3 and geo[2] == 1 and min(geo) > 0, 'geometry %s' % im.get('geometry'))
    fmt = im.get('sampleFormat')
    _verifier(fmt in TYPES, 'sampleFormat %s' % fmt)
    bounds = im.get('bounds')
    if fmt.startswith('Float'):
        _verifier(bounds is not None, 'bounds missing for a floating point image')
    if bounds is not None:
        lo, hi = (float(v) for v in bounds.split(':'))
        _verifier(lo < hi, 'inconsistent bounds')
    _verifier(im.get('colorSpace', 'Gray') == 'Gray', 'colorSpace')
    _verifier(im.get('pixelStorage', 'Planar') == 'Planar', 'pixelStorage')
    m = re.match(r'^attachment:(\d+):(\d+)$', im.get('location', ''))
    _verifier(m is not None, 'location %s' % im.get('location'))
    pos, taille = int(m.group(1)), int(m.group(2))
    _verifier(pos >= 16 + lg and pos + taille <= len(tout), 'block outside the file')
    _verifier(not tout[16 + lg:pos].strip(b'\0'), 'unused space not zero')
    bloc = tout[pos:pos + taille]
    cs = im.get('checksum')
    if cs:
        algo, dig = cs.split(':')
        h = {'sha1': hashlib.sha1, 'sha-1': hashlib.sha1, 'sha256': hashlib.sha256, 'sha-256': hashlib.sha256,
             'sha512': hashlib.sha512, 'sha-512': hashlib.sha512}[algo]
        _verifier(h(bloc).hexdigest() == dig, 'wrong checksum: altered block')
    brut = _decompresser(bloc, im.get('compression')) if im.get('compression') else bloc
    dt = np.dtype(TYPES[fmt])
    if im.get('byteOrder') == 'big':
        dt = dt.newbyteorder('>')
    nx, ny = geo[0], geo[1]
    _verifier(len(brut) == nx * ny * dt.itemsize, 'pixel data size')
    data = np.frombuffer(brut, dt).reshape(ny, nx)
    mots = []
    for k in im.findall(NS + 'FITSKeyword'):
        nom = k.get('name')
        _verifier(nom is not None and k.get('value') is not None and k.get('comment') is not None,
                  'incomplete FITSKeyword')
        _verifier(RE_MOTCLE.match(nom) is not None, 'invalid FITS keyword name: %r' % nom)
        if nom in ('HISTORY', 'COMMENT'):
            _verifier(k.get('value') == '', '%s with a value' % nom)
        mots.append((nom, k.get('value'), k.get('comment')))
    props = {}
    for p in im.findall(NS + 'Property'):
        _verifier(RE_ID.match(p.get('id', '')) is not None, 'invalid property id %r' % p.get('id'))
        _verifier(p.get('id') not in props, 'duplicate property %s' % p.get('id'))
        props[p.get('id')] = p.get('value') if p.get('value') is not None else (p.text or '')
    return data, {'format': fmt, 'bounds': bounds, 'compression': im.get('compression'), 'mots_cles': mots,
                  'proprietes': props, 'taille_bloc': taille, 'position': pos, 'image_type': im.get('imageType'),
                  'xml': xml}
