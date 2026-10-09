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
PIXELS_MAX = 2**31                 # 2 Gpixel : au-delà, fichier refusé (une image de la banque fait 16 Mpixel)
ENTETE_MAX = 64 * 2**20            # octets : l'en-tête XML d'une image fait quelques ko
_FORMATS = {np.dtype('<f4'): 'Float32', np.dtype('<f8'): 'Float64', np.dtype('<u2'): 'UInt16',
            np.dtype('uint8'): 'UInt8', np.dtype('<u4'): 'UInt32'}
NS = '{http://www.pixinsight.com/xisf}'
TYPES = {'UInt8': 'u1', 'UInt16': '<u2', 'UInt32': '<u4', 'UInt64': '<u8', 'Float32': '<f4', 'Float64': '<f8'}
RE_ID = re.compile(r'^[_a-zA-Z][_a-zA-Z0-9]*(:[_a-zA-Z][_a-zA-Z0-9]*)*$')
RE_MOTCLE = re.compile(r'^[A-Z0-9_-]{1,8}$')


class ErreurXISF(Exception):
    pass


# ======================================================================== écriture
def melanger(octets, taille_item: int):
    """Byte shuffling (§ 10.6.2) ; la queue incomplète reste telle quelle.

    `octets` : bytes ou tableau d'octets ; rend un tableau numpy contigu (une seule copie, pas de `tobytes()`
    intermédiaire : 64 Mo de moins au pic sur une image IRIS 4096²)."""
    a = np.frombuffer(octets, np.uint8) if isinstance(octets, (bytes, bytearray, memoryview)) else octets.view(np.uint8).reshape(-1)
    if taille_item <= 1:
        return a
    n = len(a) // taille_item
    if n * taille_item == len(a):
        return np.ascontiguousarray(a.reshape(n, taille_item).T)
    return np.concatenate([np.ascontiguousarray(a[:n * taille_item].reshape(n, taille_item).T).reshape(-1), a[n * taille_item:]])


def compresser(octets, codec: str, niveau: int, taille_item: int) -> bytes:
    """`octets` : bytes ou tableau numpy (passé aux compresseurs par le protocole tampon, sans copie)."""
    if codec.endswith('+sh'):
        octets = melanger(octets, taille_item)
    if isinstance(octets, np.ndarray):
        octets = memoryview(np.ascontiguousarray(octets)).cast('B')
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
    taille_item = a.dtype.itemsize
    n_brut = a.nbytes
    if codec:
        bloc = compresser(a, codec, niveau, taille_item)          # le tableau lui-même : aucune copie en bytes
        compression = ('%s:%d:%d' % (codec, n_brut, taille_item)) if codec.endswith('+sh') \
            else '%s:%d' % (codec, n_brut)
    else:                                                         # sans compression (codec None ou '')
        bloc = a.tobytes()
        compression = None
    somme = hashlib.sha1(bloc).hexdigest()
    ny, nx = a.shape
    uid = str(_uuid.uuid4())
    maintenant = _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def entete(position):
        attrs = ['geometry="%d:%d:1"' % (nx, ny), 'sampleFormat="%s"' % fmt]
        if bounds is not None:
            attrs.append('bounds="%s:%s"' % (repr(float(bounds[0])), repr(float(bounds[1]))))
        attrs += ['colorSpace="Gray"', 'imageType="%s"' % type_image] + \
            (['compression="%s"' % compression] if compression else []) + \
            ['checksum="sha1:%s"' % somme, 'location="attachment:%d:%d"' % (position, len(bloc)), 'uuid="%s"' % uid]
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
    try:
        with open(tmp, 'wb') as f:
            f.write(b'XISF0100')
            f.write(len(x).to_bytes(4, 'little'))
            f.write(b'\0\0\0\0')
            f.write(x)
            f.write(b'\0' * (position - 16 - len(x)))
            f.write(bloc)
            f.flush()
        os.replace(tmp, chemin)
    except BaseException:                  # disque plein, dossier retiré, annulation : jamais de .tmp orphelin
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    return position + len(bloc), len(bloc)


# ======================================================================== lecture (contrôle strict)
def _verifier(cond, msg):
    if not cond:
        raise ErreurXISF(msg)


def _desordonner(octets, n):
    """Inverse du byte shuffling ; rend un tableau d'octets contigu (une seule copie)."""
    if n <= 1:
        return octets
    a = np.frombuffer(octets, np.uint8)
    m = len(a) // n
    if m * n == len(a):
        return np.ascontiguousarray(a.reshape(n, m).T).reshape(-1)
    return np.concatenate([np.ascontiguousarray(a[:m * n].reshape(n, m).T).reshape(-1), a[m * n:]])


def _decompresser(bloc, spec):
    parts = spec.split(':')
    _verifier(len(parts) >= 2 and parts[1].isdigit(), 'compression %s' % spec)
    codec = parts[0]
    taille = int(parts[1])
    _verifier(taille <= PIXELS_MAX * 8, 'uncompressed size too large: %d' % taille)
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
    return _desordonner(d, item) if codec.endswith('+sh') else np.frombuffer(d, np.uint8)


def valider_xsd(xml: bytes, xsd) -> None:
    from lxml import etree  # facultatif : seulement pour la validation par schéma
    schema = etree.XMLSchema(etree.parse(str(xsd)))
    if not schema.validate(etree.fromstring(xml)):
        raise ErreurXISF('XSD: %s' % schema.error_log.last_error)


def lire(chemin, xsd=None):
    """Lit et contrôle un XISF monolithique à une image.  Renvoie (tableau, infos)."""
    with open(chemin, 'rb') as f:
        debut = f.read(16)
        _verifier(debut[:8] == b'XISF0100', 'signature missing')
        lg = int.from_bytes(debut[8:12], 'little')
        _verifier(debut[12:16] == b'\0\0\0\0', 'reserved field not zero')
        _verifier(lg <= ENTETE_MAX, 'header too large: %d bytes' % lg)
        taille_fichier = os.fstat(f.fileno()).st_size
        _verifier(taille_fichier <= 16 + lg + PIXELS_MAX * 8 + ALIGNEMENT, 'file too large')
        f.seek(0)
        tout = f.read(16 + lg + ALIGNEMENT)                # en-tête et bourrage ; le bloc de pixels est lu à part
    xml = tout[16:16 + lg]
    _verifier(xml.startswith(b'<?xml version="1.0" encoding="UTF-8"?>'), 'XML declaration missing')
    try:
        xml.decode('utf-8')
        racine = ET.fromstring(xml)
    except (UnicodeDecodeError, ET.ParseError) as e:        # en-tête abîmé (fichier partiel, octets altérés)
        raise ErreurXISF('invalid XML header: %s' % e)
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
    try:
        geo = [int(v) for v in (im.get('geometry') or '').split(':')]
    except ValueError:
        raise ErreurXISF('geometry %s' % im.get('geometry'))
    _verifier(len(geo) == 3 and geo[2] == 1 and min(geo) > 0, 'geometry %s' % im.get('geometry'))
    _verifier(geo[0] * geo[1] <= PIXELS_MAX, 'image too large: %dx%d' % (geo[0], geo[1]))
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
    _verifier(pos >= 16 + lg and pos + taille <= taille_fichier, 'block outside the file')
    _verifier(not tout[16 + lg:pos].strip(b'\0'), 'unused space not zero')
    with open(chemin, 'rb') as f:
        f.seek(pos)
        bloc = f.read(taille)
    _verifier(len(bloc) == taille, 'block outside the file')
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
    data = (brut.view(dt) if isinstance(brut, np.ndarray) else np.frombuffer(brut, dt)).reshape(ny, nx)
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


# ======================================================================== en-tête seul (sans les pixels)
def lire_entete(chemin) -> dict:
    """En-tête d'un XISF sans lire ni décompresser les pixels (une lecture des premiers Ko, même sur un partage) :
    {'mots_cles': [(nom, valeur, commentaire)], 'proprietes': {id: valeur}, 'types': {id: type},
     'geometrie': (nx, ny), 'format', 'compression'}."""
    with open(chemin, 'rb') as f:
        debut = f.read(16)
        _verifier(debut[:8] == b'XISF0100', 'signature missing')
        lg = int.from_bytes(debut[8:12], 'little')
        _verifier(lg <= ENTETE_MAX, 'header too large: %d bytes' % lg)
        xml = f.read(lg)
    try:
        racine = ET.fromstring(xml)
    except ET.ParseError as e:
        raise ErreurXISF('invalid XML header: %s' % e)
    im = racine.find(NS + 'Image')
    _verifier(im is not None, 'no image')
    geo = [int(v) for v in (im.get('geometry') or '0:0:1').split(':')]
    props, types = {}, {}
    for p in im.findall(NS + 'Property'):
        props[p.get('id')] = p.get('value') if p.get('value') is not None else (p.text or '')
        types[p.get('id')] = p.get('type')
    return {'mots_cles': [(k.get('name'), k.get('value'), k.get('comment')) for k in im.findall(NS + 'FITSKeyword')],
            'proprietes': props, 'types': types, 'geometrie': (geo[0], geo[1]), 'format': im.get('sampleFormat'),
            'compression': im.get('compression')}


def reecrire_entete(chemin, mots_cles, proprietes) -> None:
    """Remplace les mots-clés FITS et les propriétés de l'image d'un XISF sans toucher aux pixels : le bloc de
    données (compressé) est recopié octet pour octet (même somme SHA-1), seul l'en-tête change ; écriture
    atomique (fichier temporaire puis remplacement).  `proprietes` : [(id, type, valeur)]."""
    with open(chemin, 'rb') as f:
        debut = f.read(16)
        _verifier(debut[:8] == b'XISF0100', 'signature missing')
        lg = int.from_bytes(debut[8:12], 'little')
        xml = f.read(lg).decode('utf-8')
    a = re.search(r'<Image\b[^>]*>', xml)
    b = xml.find('</Image>')
    _verifier(a is not None and b > a.end(), 'Image element not found')
    m = re.search(r'location="attachment:(\d+):(\d+)"', a.group(0))
    _verifier(m is not None, 'location')
    pos, taille = int(m.group(1)), int(m.group(2))
    interieur = [_propriete(pid, ptype, val) for pid, ptype, val in proprietes]
    interieur += ['<FITSKeyword name=%s value=%s comment=%s/>' % (quoteattr(xml_texte(n)), quoteattr(xml_texte(v)),
                                                                   quoteattr(xml_texte(c))) for n, v, c in mots_cles]
    with open(chemin, 'rb') as f:
        f.seek(pos)
        bloc = f.read(taille)
    _verifier(len(bloc) == taille, 'block outside the file')

    def entete(position):
        balise = a.group(0).replace(m.group(0), 'location="attachment:%d:%d"' % (position, taille))
        return (xml[:a.start()] + balise + '\n' + '\n'.join(interieur) + '\n' + xml[b:]).encode('utf-8')
    position = ALIGNEMENT
    for _ in range(10):
        x = entete(position)
        besoin = -(-(16 + len(x)) // ALIGNEMENT) * ALIGNEMENT
        if besoin == position:
            break
        position = besoin
    else:
        raise RuntimeError('unstable block position')
    tmp = str(chemin) + '.tmp'
    try:
        with open(tmp, 'wb') as f:
            f.write(b'XISF0100')
            f.write(len(x).to_bytes(4, 'little'))
            f.write(b'\0\0\0\0')
            f.write(x)
            f.write(b'\0' * (position - 16 - len(x)))
            f.write(bloc)
            f.flush()
        os.replace(tmp, chemin)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
