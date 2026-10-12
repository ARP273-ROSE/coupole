"""Aperçus (vignettes) des produits d'archive.

Diagnostic de la 0.2.1 (aucun aperçu sous Windows) : MAST donne en ``jpegurl`` un JPEG **pleine résolution** du
produit (3,7 à 4,2 Mo pour Arp 273 et M 16 ; 19 806 × 15 741 px pour la cellule de M 16) ; la vignette n'était lue
que jusqu'à 3 Mo (JPEG tronqué, « premature end of data segment ») et une telle image dépasse la limite
d'allocation de Qt (256 Mo).  Désormais :

1. **vignette officielle** (MAST ``jpegurl``, ESO ``previews/v1/files/<id>/thumbnail``, OPUS ``…_thumb.jpg``,
   PDS ``ATLAS_THUMBNAIL_URL``, SDSS ``ImgCutout``) lue en entier (jusqu'à 64 Mo), décodée **réduite** par
   ``QImageReader.setScaledSize`` (le JPEG n'est jamais décompressé en pleine taille), puis **recadrée sur la zone
   utile** (fond noir ou blanc) (une cellule du ciel presque vide redevient lisible) et gardée en PNG de 400 px dans le cache ;
2. sinon, après téléchargement, **vignette générée** depuis l'image préparée (étirement asinh) ;
3. sinon « pas d'aperçu » avec la raison (archive qui n'en fournit pas, téléchargement refusé…).

Fonctions appelées hors du fil graphique (``QImage`` et ``QImageReader`` sont utilisables dans un fil de travail).
"""
from __future__ import annotations

import hashlib
import os

from ...core import config

TAILLE = 400
MAX_OCTETS = 64 * 2**20
SANS_APERCU = {'irsa': 'arc_apercu_sans_irsa', 'koa': 'arc_apercu_sans_koa', 'noirlab': 'arc_apercu_sans_noirlab',
               'goa': 'arc_apercu_sans_compte', 'smoka': 'arc_apercu_sans_compte'}


def dossier_cache():
    d = config.dossier_cache() / 'archives_vignettes'
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cle(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:20]


def telecharger_brut(url: str) -> str:
    """Fichier officiel complet en cache (``.brut``) ; '' si indisponible."""
    from ...core import reseau
    # « .brut » et non « .img » : les « .img » de la 0.2.1 sont souvent tronqués à 3 Mo (ignorés, jamais relus)
    p = dossier_cache() / (_cle(url) + '.brut')
    if p.exists() and p.stat().st_size > 0:
        return str(p)
    try:
        with reseau.requete(url, delai=60) as r:
            b = r.read(MAX_OCTETS + 1)
    except Exception:
        return ''
    if not b or len(b) > MAX_OCTETS:
        return ''
    tmp = str(p) + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(b)
    os.replace(tmp, p)
    return str(p)


def zone_non_noire(img, seuil: int = 8):
    """(x0, y0, x1, y1) des pixels qui diffèrent du fond d'une QImage, ou None.  Le fond est la couleur des coins :
    noir ou **blanc** (les JPEG de MAST peignent en blanc les pixels sans donnée)."""
    import numpy as np
    from PyQt6.QtGui import QImage
    g = img.convertToFormat(QImage.Format.Format_Grayscale8)
    w, h, bpl = g.width(), g.height(), g.bytesPerLine()
    if not w or not h:
        return None
    ptr = g.constBits()
    ptr.setsize(g.sizeInBytes())
    a = np.frombuffer(ptr, np.uint8).reshape(h, bpl)[:, :w]
    coins = np.array([a[0, 0], a[0, -1], a[-1, 0], a[-1, -1]], dtype=np.int16)
    fond = int(np.median(coins))
    v = np.abs(a.astype(np.int16) - fond) > seuil
    if not v.any():
        return None
    ys, xs = np.nonzero(v.any(1))[0], np.nonzero(v.any(0))[0]
    return int(xs[0]), int(ys[0]), int(xs[-1]), int(ys[-1])


def reduire(chemin_source: str, chemin_png: str, taille: int = TAILLE) -> bool:
    """Décode `chemin_source` réduit, recadre sur sa zone non noire, écrit un PNG de `taille` px au plus."""
    from PyQt6.QtCore import QRect, QSize, Qt
    from PyQt6.QtGui import QImageReader
    r = QImageReader(chemin_source)
    r.setAutoTransform(True)
    plein = r.size()
    if not plein.isValid() or plein.isEmpty():
        return False
    apercu = QSize(plein).scaled(QSize(1200, 1200), Qt.AspectRatioMode.KeepAspectRatio)
    r.setScaledSize(apercu)
    img = r.read()
    if img.isNull():
        return False
    z = zone_non_noire(img)
    if z is not None:
        x0, y0, x1, y1 = z
        fx, fy = plein.width() / img.width(), plein.height() / img.height()
        clip = QRect(int(x0 * fx), int(y0 * fy), max(1, int((x1 - x0 + 1) * fx)), max(1, int((y1 - y0 + 1) * fy)))
        if clip.width() * clip.height() < 0.9 * plein.width() * plein.height():
            r2 = QImageReader(chemin_source)
            r2.setClipRect(clip)
            r2.setScaledSize(clip.size().scaled(QSize(taille, taille), Qt.AspectRatioMode.KeepAspectRatio))
            img2 = r2.read()
            if not img2.isNull():
                return img2.save(chemin_png, 'PNG')
    img = img.scaled(QSize(taille, taille), Qt.AspectRatioMode.KeepAspectRatio,
                     Qt.TransformationMode.SmoothTransformation)
    return img.save(chemin_png, 'PNG')


def vignette_officielle(url: str) -> tuple[str, str]:
    """(chemin du PNG, raison) ; raison '' si réussi."""
    if not url:
        return '', 'arc_apercu_aucune_adresse'
    png = dossier_cache() / (_cle(url) + '.png')
    if png.exists() and png.stat().st_size > 0:
        return str(png), ''
    brut = telecharger_brut(url)
    if not brut:
        return '', 'arc_apercu_injoignable'
    try:
        ok = reduire(brut, str(png))
    except Exception:
        ok = False
    if not ok:
        return '', 'arc_apercu_illisible'
    return str(png), ''


def vignette_generee(chemin_prepare: str) -> str:
    """Vignette PNG à partir d'une image préparée (cache, refaite si l'image change)."""
    if not chemin_prepare or not os.path.exists(chemin_prepare):
        return ''
    st = os.stat(chemin_prepare)
    png = dossier_cache() / (_cle('%s|%d|%d' % (os.path.abspath(chemin_prepare), st.st_size, int(st.st_mtime))) + '.png')
    if png.exists():
        return str(png)
    try:
        from .alignement import ecrire_apercu_gris
        from .extraction import lire_prepare
        donnees, _ = lire_prepare(chemin_prepare)
        ecrire_apercu_gris(str(png), donnees, cote=TAILLE)
    except Exception:
        return ''
    return str(png) if png.exists() else ''


def vignette(o: dict, chemin_prepare: str = '') -> tuple[str, str]:
    """Meilleure vignette d'une observation : officielle, sinon générée depuis le fichier préparé, sinon la raison."""
    if o.get('apercu'):
        p, raison = vignette_officielle(o['apercu'])
        if p:
            return p, 'arc_apercu_officiel'
    else:
        raison = SANS_APERCU.get(o.get('archive', ''), 'arc_apercu_aucune_adresse')
    if chemin_prepare:
        p = vignette_generee(chemin_prepare)
        if p:
            return p, 'arc_apercu_genere'
    return '', raison
