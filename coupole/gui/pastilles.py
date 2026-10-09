"""Pastilles d'état dessinées à la main (aucun fichier image), aux couleurs du thème courant.

Noms : ``ok`` (coche verte : possédée), ``ecarte`` (rond gris : doublon écarté), ``echec`` (triangle orange),
``absente`` (flèche de téléchargement, couleur du texte doux : à télécharger), ``complet`` (disque vert plein),
``partiel`` (demi-disque), ``aucun`` (cercle vide).  Mises en cache par (nom, thème, taille).
"""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

from . import theme

_cache: dict = {}


def couleur_statut(nom: str) -> QColor:
    """La couleur de texte associée à un statut (None → couleur normale du texte)."""
    return theme.couleur({'ok': 'statut_ok', 'complet': 'statut_ok', 'partiel': 'statut_ok',
                          'ecarte': 'statut_ecarte', 'doublon': 'statut_ecarte', 'aucun': 'statut_ecarte',
                          'echec': 'statut_echec'}.get(nom, 'texte_doux'))


def pastille(nom: str, taille: int = 14) -> QIcon:
    from ..core import config
    cle = (nom, config.reglages()['apparence'], taille)
    if cle in _cache:
        return _cache[cle]
    pm = QPixmap(taille, taille)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    c = couleur_statut(nom)
    t = float(taille)
    m = t * 0.12
    r = QRectF(m, m, t - 2 * m, t - 2 * m)
    stylo = QPen(c, max(1.4, t / 9))
    stylo.setCapStyle(Qt.PenCapStyle.RoundCap)
    stylo.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    if nom == 'ok':
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(r)
        blanc = QPen(theme.couleur('base'), max(1.6, t / 7))
        blanc.setCapStyle(Qt.PenCapStyle.RoundCap)
        blanc.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(blanc)
        chemin = QPainterPath(QPointF(t * 0.30, t * 0.52))
        chemin.lineTo(QPointF(t * 0.45, t * 0.67))
        chemin.lineTo(QPointF(t * 0.71, t * 0.36))
        p.drawPath(chemin)
    elif nom in ('ecarte', 'doublon'):
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(r.adjusted(t * 0.1, t * 0.1, -t * 0.1, -t * 0.1))
    elif nom == 'echec':
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(QPolygonF([QPointF(t / 2, m), QPointF(t - m, t - m), QPointF(m, t - m)]))
        p.setPen(QPen(theme.couleur('base'), max(1.2, t / 9)))
        p.drawLine(QPointF(t / 2, t * 0.40), QPointF(t / 2, t * 0.66))
        p.drawPoint(QPointF(t / 2, t * 0.80))
    elif nom == 'absente':
        p.setPen(stylo)
        p.drawLine(QPointF(t / 2, t * 0.18), QPointF(t / 2, t * 0.66))
        p.drawLine(QPointF(t * 0.28, t * 0.46), QPointF(t / 2, t * 0.68))
        p.drawLine(QPointF(t * 0.72, t * 0.46), QPointF(t / 2, t * 0.68))
        p.drawLine(QPointF(t * 0.22, t * 0.86), QPointF(t * 0.78, t * 0.86))
    elif nom == 'complet':
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(r)
    elif nom == 'partiel':
        p.setPen(stylo)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(r)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPie(r, 90 * 16, -180 * 16)          # moitié droite pleine
    else:                                         # 'aucun'
        p.setPen(stylo)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(r)
    p.end()
    ic = QIcon(pm)
    _cache[cle] = ic
    return ic


def vider_cache():
    _cache.clear()
