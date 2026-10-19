"""Aperçus des fichiers d'un partage, calculés hors du fil graphique (QImage, jamais QPixmap ici).

* JPEG, PNG, TIFF : le fichier entier (taille bornée) ;
* FITS : le fichier entier (mis en cache), image ramenée à la luminance, étirement par centiles ;
* SER (vidéo planétaire) : l'en-tête de 178 octets puis la SEULE première image, par une requête partielle ;
* AVI : le début du fichier, jusqu'à la première image (MJPEG ou image non compressée).
Les aperçus sont gardés en PNG dans le cache du partage (clé : chemin + ETag).
"""
from __future__ import annotations

import hashlib
import struct

import numpy as np

TAILLE = 512
MAX_IMAGE_AUTO = 40_000_000           # au-delà, l'aperçu d'une image se demande (bouton)
MAX_AVI_DEBUT = 8_000_000


class SansApercu(ValueError):
    def __init__(self, cle: str):
        super().__init__(cle)
        self.cle = cle


def _qimage_de_tableau(a: np.ndarray):
    from PyQt6.QtGui import QImage
    a = np.nan_to_num(np.asarray(a, np.float32))
    if a.ndim == 3:
        a = a.mean(axis=0) if a.shape[0] <= 4 else a.mean(axis=2)
    f = max(1, int(np.ceil(max(a.shape) / TAILLE)))
    if f > 1:
        h, w = (a.shape[0] // f) * f, (a.shape[1] // f) * f
        a = a[:h, :w].reshape(h // f, f, w // f, f).mean(axis=(1, 3))
    lo, hi = np.percentile(a, (0.5, 99.8))
    if hi <= lo:
        hi = lo + 1
    b = np.clip((a - lo) / (hi - lo), 0, 1)
    b = np.arcsinh(b * 10) / np.arcsinh(10)
    o = np.ascontiguousarray((b * 255).astype(np.uint8))
    img = QImage(o.data, o.shape[1], o.shape[0], o.strides[0], QImage.Format.Format_Grayscale8)
    return img.copy()


def _reduire(img):
    from PyQt6.QtCore import Qt
    if img.width() > TAILLE or img.height() > TAILLE:
        return img.scaled(TAILLE, TAILLE, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
    return img


def lire_ser(octets_entete: bytes) -> dict:
    """En-tête SER (178 octets) : largeur, hauteur, bits, couleur, nombre d'images."""
    if len(octets_entete) < 178 or not octets_entete[:14].startswith(b'LUCAM-RECORDER'):
        raise SansApercu('pt_ap_ser_illisible')
    couleur, petit_boutiste, w, h, bits, n = struct.unpack('<6i', octets_entete[18:42])
    plans = 3 if couleur in (100, 101) else 1
    return {'couleur': couleur, 'largeur': w, 'hauteur': h, 'bits': bits, 'images': n, 'plans': plans,
            'octets_image': w * h * plans * (2 if bits > 8 else 1), 'gros_boutiste': petit_boutiste == 0}


def image_ser(octets: bytes, info: dict) -> np.ndarray:
    dt = np.dtype('>u2' if info['gros_boutiste'] else '<u2') if info['bits'] > 8 else np.dtype('u1')
    a = np.frombuffer(octets[:info['octets_image']], dtype=dt)
    if info['plans'] == 3:
        return a.reshape(info['hauteur'], info['largeur'], 3).mean(axis=2)
    return a.reshape(info['hauteur'], info['largeur'])


def premiere_image_avi(octets: bytes):
    """Première image d'un AVI : MJPEG (« 00dc » commençant par FFD8) ou image DIB non compressée 8/24 bits."""
    from PyQt6.QtGui import QImage
    if octets[:4] != b'RIFF' or octets[8:12] != b'AVI ':
        raise SansApercu('pt_ap_avi_illisible')
    w = h = bits = 0
    k = octets.find(b'strf')
    if k > 0:
        try:
            _, w, h, _, bits = struct.unpack('<IiiHH', octets[k + 8:k + 24])
        except struct.error:
            pass
    k = octets.find(b'movi')
    while 0 <= k < len(octets) - 8:
        k = k + 4 if octets[k:k + 4] in (b'movi', b'LIST') else k
        cid, taille = octets[k:k + 4], struct.unpack('<I', octets[k + 4:k + 8])[0]
        corps = octets[k + 8:k + 8 + taille]
        if cid[2:] in (b'dc', b'db') and taille > 0:
            if corps[:2] == b'\xff\xd8':
                img = QImage()
                if img.loadFromData(corps):
                    return img
            elif w and h and bits in (8, 24) and len(corps) >= abs(h) * ((w * bits // 8 + 3) // 4 * 4):
                ligne = (w * bits // 8 + 3) // 4 * 4
                a = np.frombuffer(corps[:ligne * abs(h)], np.uint8).reshape(abs(h), ligne)[:, :w * bits // 8]
                if bits == 24:
                    a = a.reshape(abs(h), w, 3).mean(axis=2)
                if h > 0:
                    a = a[::-1]
                return _qimage_de_tableau(a.astype(np.float32))
            raise SansApercu('pt_ap_avi_codec')
        if taille == 0 and cid == b'\0\0\0\0':
            break
        k = k + 8 + taille + (taille & 1)
    raise SansApercu('pt_ap_avi_codec')


def cle_cache(chemin: str, etag: str) -> str:
    return hashlib.sha1(('%s|%s' % (chemin, etag)).encode('utf-8')).hexdigest()[:20] + '.png'


def apercu(session, f, forcer: bool = False):
    """QImage de l'aperçu de `f` (structure.Fichier) ; lève SansApercu(clé) sinon."""
    from PyQt6.QtGui import QImage
    from . import structure as S
    cache = session.dossier / 'apercus'
    cache.mkdir(exist_ok=True)
    c = cache / cle_cache(f.chemin, f.etag)
    if c.exists():
        img = QImage(str(c))
        if not img.isNull():
            return img
    if f.genre not in S.APERCU_POSSIBLE:
        raise SansApercu('pt_ap_genre')
    if f.genre in ('jpeg', 'png', 'tiff'):
        if f.taille > MAX_IMAGE_AUTO and not forcer:
            raise SansApercu('pt_ap_trop_grand')
        local = session.fichier_local(f.chemin, f.taille)
        img = QImage(local)
        if img.isNull():
            raise SansApercu('pt_ap_illisible')
        img = _reduire(img)
    elif f.genre == 'fits':
        if f.taille > MAX_IMAGE_AUTO and not forcer:
            raise SansApercu('pt_ap_trop_grand')
        from .analyses.parallaxe.image import lire
        local = session.fichier_local(f.chemin, f.taille)
        img = _qimage_de_tableau(lire(local).donnees[::-1])
    elif f.genre == 'ser':
        info = lire_ser(session.debut_fichier(f.chemin, 178))
        corps = session.client.lire(f.chemin, 178, 178 + info['octets_image'] - 1,
                                    max_octets=info['octets_image'] + 1024)
        img = _qimage_de_tableau(image_ser(corps, info).astype(np.float32))
    else:                                          # avi
        img = _reduire(premiere_image_avi(session.debut_fichier(f.chemin, min(f.taille or MAX_AVI_DEBUT,
                                                                             MAX_AVI_DEBUT))))
    try:
        img.save(str(c), 'PNG')
    except Exception:
        pass
    return img


def infos_video(session, f) -> dict:
    """Ce qu'on sait d'une vidéo sans la télécharger (SER : dimensions, profondeur, nombre d'images)."""
    if f.genre == 'ser':
        return lire_ser(session.debut_fichier(f.chemin, 178))
    return {}


def taille_lisible(n: int) -> str:
    from ...core.i18n import decimal, tr
    if n >= 1e9:
        return tr('taille_go', v=decimal(n / 1e9, 2))
    if n >= 1e6:
        return tr('taille_mo', v=decimal(n / 1e6, 1))
    return tr('pt_taille_ko', v=decimal(n / 1e3, 0))

