"""Lecteur maison des formats planétaires simples : PDS3 (label attaché ou détaché), VICAR, PDS4 (Array_2D_Image).

Pourquoi un lecteur maison : les bibliothèques ``pdr`` et ``planetaryimage`` tirent de nombreuses dépendances
(pandas, pvl, multidict…) pour lire, dans notre cas, un tableau d'entiers ou de réels décrit par une poignée de
mots-clés.  Ce module ne dépend que de numpy et gère :

* PDS3 : ``^IMAGE`` (enregistrement 1-indexé, octets ``<BYTES>``, ou fichier séparé), ``LINES``,
  ``LINE_SAMPLES``, ``BANDS`` (BSQ), ``SAMPLE_BITS`` (8, 16, 32, 64), ``SAMPLE_TYPE`` (MSB/LSB/UNSIGNED/
  PC_REAL/IEEE_REAL/VAX_REAL n'est pas géré), ``LINE_PREFIX_BYTES``, ``LINE_SUFFIX_BYTES``, ``SCALING_FACTOR``,
  ``OFFSET`` ; objet ``IMAGE`` ou ``IMAGE`` imbriqué ;
* VICAR : ``LBLSIZE``, ``FORMAT`` (BYTE, HALF, FULL, REAL, DOUB), ``ORG`` (BSQ), ``NL``, ``NS``, ``NB``,
  ``NBB`` (octets binaires en tête de ligne), ``NLB`` (lignes binaires d'en-tête), ``INTFMT``/``REALFMT``
  (HIGH/LOW, IEEE/RIEEE) ;
* PDS4 : premier ``Array_2D_Image`` / ``Array_3D_Image`` de ``File_Area_Observational`` (``offset``,
  ``Axis_Array``, ``data_type`` : UnsignedByte, SignedMSB2, UnsignedLSB2, IEEE754MSBSingle…, ``scaling_factor``,
  ``value_offset``).

Non géré (signalé par une exception claire) : compression interne (Huffman de Voyager EDR, ``ENCODING_TYPE``),
VAX_REAL, entrelacement BIL/BIP à plusieurs bandes, tableaux PDS4 à plus de trois axes, géométrie (aucune WCS
céleste : une image planétaire n'en a pas).
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET

import numpy as np


class FormatNonGere(ValueError):
    """Fichier planétaire dont une particularité n'est pas gérée (message technique, anglais)."""


# ============================================================================================= PDS3 (ODL)
def _valeur(v: str):
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    if v.startswith('(') and v.endswith(')'):
        return [_valeur(x) for x in _decouper_liste(v[1:-1])]
    m = re.match(r'^([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*<\s*([A-Za-z]+)\s*>$', v)
    if m:
        return (float(m.group(1)) if '.' in m.group(1) or 'e' in m.group(1).lower() else int(m.group(1)), m.group(2).upper())
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v.strip("'")


def _decouper_liste(s: str) -> list[str]:
    out, cour, guill = [], '', False
    for c in s:
        if c == '"':
            guill = not guill
        if c == ',' and not guill:
            out.append(cour)
            cour = ''
        else:
            cour += c
    if cour.strip():
        out.append(cour)
    return out


def lire_label_odl(texte: str) -> dict:
    """Label PDS3 → dict imbriqué (OBJECT = X … END_OBJECT devient {'X': {...}} ; répétitions : liste)."""
    pile = [{}]
    cle_cour, val_cour, guill = None, '', False
    lignes = texte.splitlines()
    for ligne in lignes:
        l = ligne.split('/*')[0] if not guill else ligne
        if cle_cour is not None:                         # valeur sur plusieurs lignes
            val_cour += ' ' + l.strip()
            if (val_cour.count('"') % 2 == 0) and (val_cour.count('(') <= val_cour.count(')')):
                _poser(pile, cle_cour, val_cour)
                cle_cour = None
            continue
        s = l.strip()
        if not s:
            continue
        if s == 'END':
            break
        if '=' not in s:
            continue
        k, v = s.split('=', 1)
        k, v = k.strip().upper(), v.strip()
        if k == 'OBJECT':
            nouveau = {}
            _ajouter(pile[-1], v.upper(), nouveau)
            pile.append(nouveau)
            continue
        if k == 'END_OBJECT':
            if len(pile) > 1:
                pile.pop()
            continue
        if k in ('GROUP', 'END_GROUP'):
            continue
        if (v.count('"') % 2 == 1) or (v.count('(') > v.count(')')):
            cle_cour, val_cour = k, v
            continue
        _poser(pile, k, v)
    return pile[0]


def _poser(pile, k, v):
    _ajouter(pile[-1], k, _valeur(' '.join(v.split())))


def _ajouter(d: dict, k, v):
    if k in d:
        if not isinstance(d[k], list) or not d.get('_liste_' + k):
            d[k] = [d[k], v]
            d['_liste_' + k] = True
        else:
            d[k].append(v)
    else:
        d[k] = v


def _premier(v):
    return v[0] if isinstance(v, list) and v and isinstance(v[0], dict) else v


def _type_pds3(sample_type: str, bits: int) -> np.dtype:
    """SAMPLE_TYPE PDS3 → type numpy (ordre des octets explicite)."""
    t = (sample_type or 'UNSIGNED_INTEGER').upper().replace(' ', '_')
    n = max(1, bits // 8)
    if 'VAX' in t:
        raise FormatNonGere('VAX samples are not supported')
    petit = t.startswith(('LSB', 'PC_'))
    ordre = '<' if petit else '>'
    if 'REAL' in t or 'FLOAT' in t:
        return np.dtype('%sf%d' % (ordre, n))
    signe = 'u' if 'UNSIGNED' in t else 'i'
    if n == 1:
        return np.dtype(signe + '1')
    return np.dtype('%s%s%d' % (ordre, signe, n))


def _octet_debut(pointeur, record_bytes: int, dossier: str, nom_label: str) -> tuple[str | None, int]:
    """(fichier de données ou None = le même, position en octets) d'après ``^IMAGE``."""
    fichier = None
    if isinstance(pointeur, list):                      # ("fichier.IMG", 2) ou ("fichier.IMG", 2000 <BYTES>)
        fichier = pointeur[0] if pointeur else None
        pointeur = pointeur[1] if len(pointeur) > 1 else 1
    elif isinstance(pointeur, str) and not pointeur.strip().lstrip('-').isdigit():
        return pointeur, 0
    if isinstance(pointeur, tuple):                     # 2000 <BYTES>
        return fichier, int(pointeur[0]) - 1
    return fichier, (int(pointeur) - 1) * record_bytes


def lire_pds3(chemin, label: str | None = None) -> tuple[np.ndarray, dict]:
    """Image (lignes, colonnes) ou (bandes, lignes, colonnes) et métadonnées d'un produit PDS3.

    `label` : chemin d'un label détaché (.LBL) ; sinon le label est en tête du fichier."""
    chemin = str(chemin)
    if label:
        texte = open(label, 'rb').read().decode('latin-1')
        dossier = os.path.dirname(label)
    else:
        with open(chemin, 'rb') as f:
            tete = f.read(256 * 1024).decode('latin-1')
        fin = re.search(r'^\s*END\s*$', tete, re.M)
        if not tete.lstrip().startswith(('PDS_VERSION_ID', 'ODL_VERSION_ID', 'CCSD')) or not fin:
            raise FormatNonGere('no PDS3 label')
        texte = tete[:fin.end()]
        dossier = os.path.dirname(chemin)
    lab = lire_label_odl(texte)
    im = _premier(lab.get('IMAGE'))
    if not isinstance(im, dict):
        raise FormatNonGere('no IMAGE object in the label')
    if im.get('ENCODING_TYPE') and str(im.get('ENCODING_TYPE')).upper() not in ('N/A', 'NONE'):
        raise FormatNonGere('compressed image (%s) is not supported' % im.get('ENCODING_TYPE'))
    lignes, colonnes = int(_n(im.get('LINES'))), int(_n(im.get('LINE_SAMPLES')))
    bandes = int(_n(im.get('BANDS', 1)) or 1)
    bits = int(_n(im.get('SAMPLE_BITS', 8)))
    dt = _type_pds3(str(im.get('SAMPLE_TYPE', 'UNSIGNED_INTEGER')), bits)
    prefixe, suffixe = int(_n(im.get('LINE_PREFIX_BYTES', 0)) or 0), int(_n(im.get('LINE_SUFFIX_BYTES', 0)) or 0)
    rb = int(_n(lab.get('RECORD_BYTES', 0)) or 0)
    fichier, debut = _octet_debut(lab.get('^IMAGE', 1), rb, dossier, label or chemin)
    source = chemin
    if fichier and label:
        candidat = os.path.join(dossier, fichier)
        source = candidat if os.path.exists(candidat) else chemin
    if bandes > 1 and str(im.get('BAND_STORAGE_TYPE', 'BAND_SEQUENTIAL')).upper() not in ('BAND_SEQUENTIAL', 'N/A'):
        raise FormatNonGere('band interleaving %s is not supported' % im.get('BAND_STORAGE_TYPE'))
    donnees = _lire_bloc(source, debut, bandes, lignes, colonnes, dt, prefixe, suffixe)
    f, o = _n(im.get('SCALING_FACTOR', 1)), _n(im.get('OFFSET', 0))
    if (f not in (None, 1, 1.0)) or (o not in (None, 0, 0.0)):
        donnees = donnees.astype(np.float32) * np.float32(f or 1) + np.float32(o or 0)
    return donnees, meta_pds3(lab, im)


def meta_pds3(lab: dict, im: dict | None = None) -> dict:
    """Métadonnées utiles d'un label PDS3 analysé."""
    im = im if isinstance(im, dict) else (_premier(lab.get('IMAGE')) or {})
    meta = {k: v for k, v in lab.items() if not isinstance(v, (dict, list)) and not k.startswith('_')}
    for k in ('FILTER_NAME', 'TARGET_NAME', 'START_TIME', 'IMAGE_TIME', 'INSTRUMENT_NAME', 'INSTRUMENT_ID',
              'SPACECRAFT_NAME', 'INSTRUMENT_HOST_NAME', 'EXPOSURE_DURATION', 'PRODUCT_ID', 'DATA_SET_ID'):
        if k in lab and isinstance(lab[k], list):
            meta[k] = ', '.join(str(x) for x in lab[k] if not isinstance(x, dict))
    meta['_format'] = 'PDS3'
    meta['_unite'] = str(im.get('UNIT', '') or '') if isinstance(im, dict) else ''
    return meta


def _n(v):
    if isinstance(v, tuple):
        return v[0]
    if isinstance(v, list):
        return v[0] if v else None
    return v


def _lire_bloc(source, debut, bandes, lignes, colonnes, dt, prefixe=0, suffixe=0) -> np.ndarray:
    n = dt.itemsize
    largeur = prefixe + colonnes * n + suffixe
    attendu = debut + bandes * lignes * largeur
    taille = os.path.getsize(source)
    if taille < attendu:
        raise FormatNonGere('file too short: %d bytes, %d expected' % (taille, attendu))
    brut = np.memmap(source, dtype=np.uint8, mode='r', offset=debut, shape=(bandes * lignes, largeur))
    utile = np.ascontiguousarray(brut[:, prefixe:prefixe + colonnes * n])
    a = utile.view(dt).reshape(bandes, lignes, colonnes)
    a = a.astype(dt.newbyteorder('=')) if dt.byteorder not in ('=', '|') else a
    del brut
    return a[0] if bandes == 1 else a


# ============================================================================================= VICAR
def lire_entete_vicar(chemin) -> dict:
    with open(chemin, 'rb') as f:
        debut = f.read(64).decode('latin-1')
        m = re.match(r"LBLSIZE\s*=\s*(\d+)", debut)
        if not m:
            raise FormatNonGere('no VICAR label')
        n = int(m.group(1))
        f.seek(0)
        texte = f.read(n).decode('latin-1')
    d = {}
    for k, v in re.findall(r"([A-Z0-9_]+)\s*=\s*('(?:[^']|'')*'|\([^)]*\)|[^\s]+)", texte):
        if k not in d:
            d[k] = v.strip("'")
    return d


def lire_vicar(chemin) -> tuple[np.ndarray, dict]:
    h = lire_entete_vicar(chemin)
    fmt = h.get('FORMAT', 'BYTE').upper()
    intfmt, realfmt = h.get('INTFMT', 'HIGH').upper(), h.get('REALFMT', 'IEEE').upper()
    if realfmt == 'VAX' and fmt in ('REAL', 'DOUB'):
        raise FormatNonGere('VAX real samples are not supported')
    ordre_i = '>' if intfmt == 'HIGH' else '<'
    ordre_r = '>' if realfmt == 'IEEE' else '<'
    dt = {'BYTE': np.dtype('u1'), 'HALF': np.dtype(ordre_i + 'i2'), 'WORD': np.dtype(ordre_i + 'i2'),
          'FULL': np.dtype(ordre_i + 'i4'), 'LONG': np.dtype(ordre_i + 'i4'), 'REAL': np.dtype(ordre_r + 'f4'),
          'DOUB': np.dtype(ordre_r + 'f8')}.get(fmt)
    if dt is None:
        raise FormatNonGere('VICAR format %s is not supported' % fmt)
    if h.get('ORG', 'BSQ').upper() != 'BSQ' and int(h.get('NB', 1)) > 1:
        raise FormatNonGere('VICAR organisation %s is not supported' % h.get('ORG'))
    nl, ns, nb = int(h['NL']), int(h['NS']), int(h.get('NB', 1))
    lbl, nbb, nlb = int(h['LBLSIZE']), int(h.get('NBB', 0)), int(h.get('NLB', 0))
    recsize = int(h.get('RECSIZE', nbb + ns * dt.itemsize))
    donnees = _lire_bloc(chemin, lbl + nlb * recsize, nb, nl, ns, dt, nbb, recsize - nbb - ns * dt.itemsize)
    meta = {k: v for k, v in h.items()}
    meta['_format'] = 'VICAR'
    meta['_unite'] = ''
    return donnees, meta


# ============================================================================================= PDS4
TYPES_PDS4 = {'UnsignedByte': 'u1', 'SignedByte': 'i1', 'UnsignedMSB2': '>u2', 'UnsignedLSB2': '<u2',
              'SignedMSB2': '>i2', 'SignedLSB2': '<i2', 'UnsignedMSB4': '>u4', 'UnsignedLSB4': '<u4',
              'SignedMSB4': '>i4', 'SignedLSB4': '<i4', 'IEEE754MSBSingle': '>f4', 'IEEE754LSBSingle': '<f4',
              'IEEE754MSBDouble': '>f8', 'IEEE754LSBDouble': '<f8'}


def lire_pds4(label_xml, donnees_chemin=None) -> tuple[np.ndarray, dict]:
    racine = ET.parse(str(label_xml)).getroot()
    ns = racine.tag[:racine.tag.index('}') + 1] if racine.tag.startswith('{') else ''

    def t(e, nom):
        x = e.find('.//' + ns + nom)
        return x.text.strip() if x is not None and x.text else ''
    for fa in racine.iter(ns + 'File_Area_Observational'):
        nom = t(fa, 'file_name')
        for genre in ('Array_2D_Image', 'Array_3D_Image', 'Array_2D', 'Array_3D'):
            arr = fa.find(ns + genre)
            if arr is None:
                continue
            offset = int(t(arr, 'offset') or 0)
            axes = [(t(a, 'axis_name'), int(t(a, 'elements'))) for a in arr.findall(ns + 'Axis_Array')]
            dtype = TYPES_PDS4.get(t(arr, 'data_type'))
            if dtype is None:
                raise FormatNonGere('PDS4 data type %s is not supported' % t(arr, 'data_type'))
            if len(axes) > 3:
                raise FormatNonGere('PDS4 arrays with more than 3 axes are not supported')
            source = donnees_chemin or os.path.join(os.path.dirname(str(label_xml)), nom)
            forme = [n for _, n in axes]
            dt = np.dtype(dtype)
            total = int(np.prod(forme))
            brut = np.fromfile(source, dtype=dt, count=total, offset=offset).reshape(forme)
            a = brut.astype(dt.newbyteorder('=')) if dt.byteorder not in ('=', '|') else brut
            f, o = t(arr, 'scaling_factor'), t(arr, 'value_offset')
            if f or o:
                a = a.astype(np.float32) * np.float32(float(f or 1)) + np.float32(float(o or 0))
            cible = racine.find('.//' + ns + 'Target_Identification')
            meta = {'_format': 'PDS4', '_unite': t(arr, 'unit'),
                    'TARGET_NAME': t(cible, 'name') if cible is not None else '',
                    'START_TIME': t(racine, 'start_date_time'), 'PRODUCT_ID': t(racine, 'logical_identifier'),
                    'TITLE': t(racine, 'title')}
            if len(forme) == 3 and forme[0] == 1:
                a = a[0]
            return a, meta
    raise FormatNonGere('no image array in the PDS4 label')


# ============================================================================================= point d'entrée
def lire(chemin, label: str | None = None) -> tuple[np.ndarray, dict]:
    """Lit un produit planétaire : PDS4 (label XML), PDS3 (label détaché ou attaché), sinon VICAR."""
    c = str(chemin)
    if c.lower().endswith('.xml'):
        return lire_pds4(c)
    if label and str(label).lower().endswith('.xml'):
        return lire_pds4(label, c)
    with open(c, 'rb') as f:
        debut = f.read(32)
    if debut.startswith(b'LBLSIZE'):
        # Fichier VICAR (Voyager, Cassini) : son propre en-tête décrit exactement les données.  Le label PDS3
        # détaché de Cassini (CISSCAL) place l'image à l'enregistrement 2 alors qu'une ligne binaire (NLB = 1)
        # la précède : la taille du fichier le confirme (2 × 4096 + 1024 × 4096 octets).  Données lues d'après
        # VICAR, métadonnées complétées par le label PDS3.
        donnees, meta = lire_vicar(c)
        if label and os.path.exists(label):
            try:
                meta_l = meta_pds3(lire_label_odl(open(label, 'rb').read().decode('latin-1')))
                meta.update({k: v for k, v in meta_l.items() if not k.startswith('_')})
                meta['_format'] = 'VICAR + PDS3'
            except Exception:
                pass
        return donnees, meta
    if label and os.path.exists(label):
        return lire_pds3(c, label)
    return lire_pds3(c)
