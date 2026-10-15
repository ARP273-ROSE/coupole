"""Favoris au bureau (même sauvegarde que Coupole Web, `favoris` de la version 2) : bouton étoile des pages (module,
question, fiche, table, image, animation), action « Ajouter aux favoris / Retirer des favoris » des menus contextuels
(raccourci Ctrl+D dans les listes), icône étoile des éléments favoris dans les listes.  Tous les boutons d'un même
atelier restent d'accord (abonnement à la sauvegarde)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QToolButton

from ....core.i18n import tr
from . import sauvegarde as S
from .stockage import stockage

OR = QColor('#E0A526')


def chemin_etoile(cx: float, cy: float, r: float) -> QPainterPath:
    ch = QPainterPath()
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        q = QPointF(cx + rr * math.cos(a), cy + rr * math.sin(a))
        ch.moveTo(q) if k == 0 else ch.lineTo(q)
    ch.closeSubpath()
    return ch


_ICONES: dict = {}


def icone_etoile(pleine: bool, couleur: QColor | None = None, taille: int = 32) -> QIcon:
    """Étoile dessinée (pleine : dorée ; vide : contour de la couleur du texte)."""
    cle = (pleine, couleur.name() if couleur else '', taille)
    if cle not in _ICONES:
        pm = QPixmap(taille, taille)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ch = chemin_etoile(taille / 2, taille / 2 + 1, taille * 0.44)
        if pleine:
            p.setPen(QPen(OR.darker(125), taille / 16))
            p.setBrush(OR)
        else:
            p.setPen(QPen(couleur or QColor('#888888'), taille / 14))
            p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(ch)
        p.end()
        _ICONES[cle] = QIcon(pm)
    return _ICONES[cle]


def est_favori(genre: str, i: str) -> bool:
    return S.est_favori(stockage().doc, genre, i)


def basculer(genre: str, i: str, titre: str, annoncer=None) -> bool:
    """Ajoute ou retire ; annonce le résultat (fonction `annoncer(texte)` de la vue) ; rend le nouvel état."""
    on = S.basculer_favori(stockage().doc, genre, i)
    stockage().modifie()
    if annoncer is not None:
        annoncer(tr('classe_favori_ajoute' if on else 'classe_favori_retire', titre=titre))
    return on


def action_favori(parent, genre: str, i: str, titre: str, annoncer=None) -> QAction:
    """Action de menu « Ajouter aux favoris » / « Retirer des favoris » (Ctrl+D)."""
    on = est_favori(genre, i)
    a = QAction(icone_etoile(on, parent.palette().color(parent.palette().ColorRole.WindowText)),
                tr('classe_favori_retirer' if on else 'classe_favori_ajouter'), parent)
    a.setShortcut('Ctrl+D')
    a.triggered.connect(lambda: basculer(genre, i, titre, annoncer))
    return a


class BoutonFavori(QToolButton):
    """Bascule étoile (cochée = favori), nom accessible « Favori : titre » ; reste d'accord avec la sauvegarde."""

    def __init__(self, genre: str, i: str, titre: str, parent=None, annoncer=None, libelle: bool = False):
        super().__init__(parent)
        self.genre, self.i, self.titre, self._annoncer = genre, i, titre, annoncer
        self.setCheckable(True)
        self.setAutoRaise(True)
        self.setAccessibleName(tr('classe_favori_nom', titre=titre))
        if libelle:
            self.setText(tr('classe_favori'))
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._maj()
        self.toggled.connect(self._bascule)
        stockage().abonner_faible(self._maj)

    def changer(self, genre: str, i: str, titre: str):
        self.genre, self.i, self.titre = genre, i, titre
        self.setAccessibleName(tr('classe_favori_nom', titre=titre))
        self._maj()

    def _maj(self):
        try:
            on = est_favori(self.genre, self.i)
        except RuntimeError:                         # objet Qt déjà détruit
            return
        self.blockSignals(True)
        self.setChecked(on)
        self.blockSignals(False)
        self.setIcon(icone_etoile(on, self.palette().color(self.palette().ColorRole.WindowText)))
        self.setToolTip(tr('classe_favori_retirer' if on else 'classe_favori_ajouter'))

    def _bascule(self, _):
        basculer(self.genre, self.i, self.titre, self._annoncer)
        self._maj()
