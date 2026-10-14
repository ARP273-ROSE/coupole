"""Fiche flottante d'un objet désigné (survol de la souris, toucher, clavier) : petite boîte discrète posée dans la
toile, jamais par-dessus l'objet (à côté de lui, du côté où il y a le plus de place) ; son résumé (nom, type, distance,
température) est annoncé aux lecteurs d'écran.  Elle ne capte pas la souris (le survol continue dessous).  Même
placement que src/app/fiche_flottante.ts du web (placer_fiche)."""
from __future__ import annotations

import html
import math

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ...core.i18n import tr
from . import dessin
from .fiche_texte import contenu_fiche
from .fiches import fiche


def placer_fiche(x: float, y: float, r: float, w: float, h: float, W: float, H: float, ecart: float = 10.0):
    """Boîte w × h posée près d'un objet (x, y, r) dans une scène W × H : jamais sur l'objet, dans la scène si possible."""
    m = 4.0

    def borne(v, a, b):
        return max(a, min(b, v))

    d = r + ecart
    droite = (x + d, borne(y - h / 2, m, H - h - m))
    gauche = (x - d - w, borne(y - h / 2, m, H - h - m))
    dessous = (borne(x - w / 2, m, W - w - m), y + d)
    dessus = (borne(x - w / 2, m, W - w - m), y - d - h)
    cotes = [droite, gauche] if W - x >= x else [gauche, droite]
    cotes += [dessous, dessus] if H - y >= y else [dessus, dessous]

    def recouvre(bx, by):
        cx, cy = borne(x, bx, bx + w), borne(y, by, by + h)
        return math.hypot(cx - x, cy - y) < r + 2

    # chaque côté tel quel, puis ramené dans la scène ; le recouvrement de l'objet est exclu tant qu'on peut l'éviter
    cands = cotes + [(borne(bx, m, max(m, W - w - m)), borne(by, m, max(m, H - h - m))) for bx, by in cotes]
    meilleur, cout = cands[0], math.inf
    for bx, by in cands:
        hors = max(0, m - bx) + max(0, bx + w - (W - m)) + max(0, m - by) + max(0, by + h - (H - m))
        c = hors * 10 + (1e6 if recouvre(bx, by) else 0)
        if c < cout:
            cout, meilleur = c, (bx, by)
            if c == 0:
                break
    bx, by = meilleur
    return bx, by


def lignes_compactes(lignes: list) -> list:
    """Lignes d'une fiche compacte : type, magnitude, distance, température, taille, âge ; sources raccourcies."""
    gardees = [tr(k) for k in ('anim_fiche_type', 'anim_fiche_mag_v', 'anim_fiche_distance', 'anim_fiche_distance_affichee',
                               'anim_fiche_teff', 'anim_fiche_taille', 'anim_fiche_age')]
    return [dict(l, source=(l['source'][:43].rstrip() + '…') if len(l['source']) > 44 else l['source'])
            for l in lignes if l['libelle'] in gardees]


class FicheFlottante(QFrame):
    def __init__(self, toile):
        super().__init__(toile)
        self.toile = toile
        self.setObjectName('fiche_objet')
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAutoFillBackground(True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(9, 7, 9, 8)
        self.label = QLabel(self)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        lay.addWidget(self.label)
        f = self.label.font()
        f.setPointSizeF(max(7.0, f.pointSizeF() * 0.82))
        self.label.setFont(f)
        self.actuelle = None
        self.cible = None
        self.resume = ''
        self.hide()

    def _style(self):
        pal = self.palette()
        fond = QColor(dessin.c('fond'))
        fond.setAlphaF(0.94)
        pal.setColor(QPalette.ColorRole.Window, fond)
        pal.setColor(QPalette.ColorRole.WindowText, dessin.c('texte'))
        self.setPalette(pal)
        self.label.setPalette(pal)

    def montrer(self, cible):
        """cible : (fiche, x, y, r) en pixels de la toile, ou None pour cacher."""
        self.cible = cible
        if cible is None:
            self.cacher()
            return
        f = fiche(cible[0])
        if f is None:
            self.cacher()
            return
        # petite toile : fiche compacte (valeurs principales, sources raccourcies), comme le web
        compact = self.toile.width() < 560 or self.toile.height() < 480
        cle = (cible[0], compact)
        if self.actuelle != cle:
            self.actuelle = cle
            t = contenu_fiche(f)
            if compact:
                t['lignes'] = lignes_compactes(t['lignes'])
            doux = dessin.c('doux').name()
            alerte = dessin.c('accent1').name()
            pastille = ('<span style="color:%s">●</span> ' % html.escape(t['couleur'])) if t['couleur'] else ''
            lignes = ''.join(
                '<tr><td style="color:%s;padding-right:8px;vertical-align:top">%s</td><td>%s%s</td></tr>' % (
                    doux, html.escape(l['libelle']),
                    ('<span style="color:%s">%s</span>' % (alerte, html.escape(l['valeur']))) if l['alerte']
                    else html.escape(l['valeur']),
                    ('<br><small style="color:%s">%s</small>' % (doux, html.escape(l['source']))) if l['source'] else '')
                for l in t['lignes'])
            sous = ('<div style="color:%s">%s</div>' % (doux, html.escape(t['sous_titre']))) if t['sous_titre'] else ''
            self.label.setText('<div><b>%s%s</b></div>%s<table style="margin-top:4px">%s</table>' % (
                pastille, html.escape(t['titre']), sous, lignes))
            self.resume = t['resume']
            self._style()
            self.annoncer(t['resume'])
        self.placer()
        self.show()
        self.raise_()

    def annoncer(self, texte: str):
        """Le résumé est lu par les lecteurs d'écran : description accessible de la toile (Qt signale le changement
        aux technologies d'assistance) et nom accessible de la fiche."""
        self.toile.setAccessibleDescription(texte)
        self.setAccessibleName(texte)

    def placer(self):
        c = self.cible
        if c is None:
            return
        W, H = self.toile.width(), self.toile.height()
        larg = int(max(160, min(300, W - 16)))
        self.setMaximumWidth(larg)
        self.setMaximumHeight(max(60, H - 8))
        self.label.setMaximumWidth(larg - 18)
        self.adjustSize()
        w, h = self.width(), self.height()
        x, y = placer_fiche(c[1], c[2], c[3], w, h, W, H)
        self.move(int(round(x)), int(round(y)))

    def suivre(self, cible):
        if self.cible is None or self.cible[0] != cible[0]:
            self.montrer(cible)
        else:
            self.cible = cible
            self.placer()

    def cacher(self):
        self.cible = None
        self.actuelle = None
        if self.isVisible():
            self.hide()
            self.toile.setAccessibleDescription('')

    @property
    def affichee(self):
        return self.cible[0] if self.cible is not None and self.isVisible() else None
