"""Eclipse Table : les éclipses de Soleil et de Lune de 2015 à 2044 (table de l'original),
placées selon l'année (en abscisse) et la date dans l'année (en ordonnée).  Elles se rangent en bandes obliques :
les saisons d'éclipses, quand le Soleil passe près d'un nœud de l'orbite lunaire, reviennent tous les 173,3 jours
(une demi-année draconitique) et avancent donc d'environ 19 jours par an.  Coupole trace le milieu de chaque
saison (Soleil sur un nœud : Meeus, chap. 25 et 47) et vérifie chaque éclipse : nouvelle ou pleine lune moyenne
à moins d'un jour et demi, et argument de latitude tel que |sin F| < 0,36 (Meeus, chap. 49 et 54)."""
from __future__ import annotations

import functools
import math
import re

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import langue, tr
from .. import astro, dessin
from ..base import MOIS_JOURS, Animation, nombre
from ..donnees_eclipses import LUNE, SOLEIL, zones

AN0, AN1 = 2015, 2045
LIMITE_F = math.degrees(math.asin(0.36))                       # 21,1°
DEMI_SAISON_J = LIMITE_F / (360.0 / astro.ANNEE_DRACONITIQUE_J)    # ≈ 20,3 jours


def fraction_d_annee(annee: int, mois: int, jour: int) -> float:
    """Comme l'original : (jours écoulés depuis le 1er janvier) / (365 ou 366)."""
    jj = astro.jour_julien(annee, mois, jour)
    j0 = astro.jour_julien(annee, 1, 1)
    return (jj - j0) / (astro.jour_julien(annee + 1, 1, 1) - j0)


def verifier(eclipse: tuple, solaire: bool) -> dict:
    """Phase moyenne la plus proche (Meeus 49.1) et argument de latitude F de la Lune à cet instant."""
    jj = astro.jour_julien(eclipse[0], eclipse[1], eclipse[2], 12.0)
    k = astro.phase_la_plus_proche(jj, pleine=not solaire)
    f = astro.argument_latitude_lune(k)
    return {'k': k, 'ecart_j': astro.phase_moyenne_jde(k) - jj, 'F': f, 'sinF': abs(math.sin(math.radians(f)))}


def format_duree(s: str) -> str:
    """« 02m47s » → « 2 min 47 s » ; « 03h29m (00h05m) » → « 3 h 29 min (totalité : 0 h 05 min) »."""
    if s.strip() in ('', '-'):
        return '—'

    def un(x):
        m = re.fullmatch(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?', x.strip())
        if not m:
            return x
        h, mi, se = m.groups()
        if h is not None:
            return '%d h %s min' % (int(h), mi or '00')
        return '%d min %s s' % (int(mi or 0), se or '00')

    principal, _, tot = s.partition('(')
    out = un(principal)
    if tot:
        out += ' (%s : %s)' % (tr('anim_eclipsetable_totalite'), un(tot.rstrip(')')))
    return out


@functools.lru_cache(maxsize=1)
def passages_aux_noeuds() -> tuple:
    """Milieux des saisons d'éclipses de AN0 − 1 à AN1 + 1 : (année décimale, fraction d'année, nœud)."""
    out = []
    for jj, nom in astro.soleil_au_noeud(astro.jour_julien(AN0 - 1, 1, 1), astro.jour_julien(AN1 + 1, 1, 1)):
        an = AN0 - 1
        while astro.jour_julien(an + 1, 1, 1) <= jj:
            an += 1
        j0, j1 = astro.jour_julien(an, 1, 1), astro.jour_julien(an + 1, 1, 1)
        out.append((an, (jj - j0) / (j1 - j0), nom))
    return tuple(out)


class TableEclipses(Animation):
    ID = 'eclipsetable'
    ANIMEE = False

    def construire(self):
        self.c_soleil = self.coche('soleil', True)
        self.c_lune = self.coche('lune', True)
        self.c_saisons = self.coche('saisons', True)
        self.choisie = ('soleil', 25)                    # éclipse totale du 12 août 2026
        self._points = []

    def etat_initial(self):
        self.choisie = ('soleil', 25)

    def presser(self, pos, bouton):
        meilleur = None
        for x, y, genre, i in self._points:
            d = math.hypot(pos.x() - x, pos.y() - y)
            if d < 14 and (meilleur is None or d < meilleur[0]):
                meilleur = (d, genre, i)
        if meilleur:
            self.choisie = meilleur[1:]
            self.rafraichir()
            return True
        return False

    def valeurs(self):
        genre, i = self.choisie
        e = (SOLEIL if genre == 'soleil' else LUNE)[i]
        v = verifier(e, genre == 'soleil')
        date = ('%d %s %d' % (e[2], tr('anim_mois_%d' % e[1]), e[0]) if langue() == 'fr'
                else '%s %d, %d' % (tr('anim_mois_%d' % e[1]), e[2], e[0]))
        duree = format_duree(e[6])
        return [(tr('anim_eclipsetable_eclipse'), tr('anim_eclipsetable_g_' + genre, date=date)),
                (tr('anim_eclipsetable_type'), tr('anim_eclipsetable_t_' + e[3])),
                (tr('anim_eclipsetable_saros'), str(e[4])), (tr('anim_eclipsetable_grandeur'), nombre(e[5], 3)),
                (tr('anim_eclipsetable_duree'), duree),
                (tr('anim_eclipsetable_zones'), zones(e[7], langue())),
                (tr('anim_eclipsetable_verif'), tr('anim_eclipsetable_verif_v', j=nombre(v['ecart_j'], 2),
                                                   f=nombre(v['F'], 1), s=nombre(v['sinF'], 2)))]

    def dessiner(self, p, rect):
        gauche, bas = 44, 26
        x0, x1 = rect.x() + gauche, rect.right() - 10
        y0, y1 = rect.y() + 10, rect.bottom() - bas

        def xy(an, frac):
            return x0 + (x1 - x0) * (an + frac - AN0) / (AN1 - AN0), y0 + (y1 - y0) * frac

        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        dessin.police(p, 0.75)
        for an in range(AN0, AN1 + 1, 5):
            x, _ = xy(an, 0.0)
            p.setPen(dessin.stylo('grille', 1.0, 0.5))
            p.drawLine(QPointF(x, y0), QPointF(x, y1))
            dessin.texte(p, x, y1 + 12, str(an), 'doux')
        for mo in range(1, 13):
            y = y0 + (y1 - y0) * sum(MOIS_JOURS[:mo - 1]) / 365.0
            p.setPen(dessin.stylo('grille', 1.0, 0.25))
            p.drawLine(QPointF(x0, y), QPointF(x1, y))
            dessin.texte(p, x0 - 22, y + (y1 - y0) / 24, tr('anim_mois_court_%d' % mo), 'doux')
        dessin.police(p, 1 / 0.75)
        if self.c_saisons.isChecked():
            self._saisons(p, xy, y0, y1)
        self._points = []
        for genre, donnees, coche in (('soleil', SOLEIL, self.c_soleil), ('lune', LUNE, self.c_lune)):
            if not coche.isChecked():
                continue
            for i, e in enumerate(donnees):
                x, y = xy(e[0], fraction_d_annee(*e[:3]))
                self._points.append((x, y, genre, i))
                self._icone(p, x, y, genre, e[3], (genre, i) == self.choisie)

    def _saisons(self, p, xy, y0, y1):
        """Bandes des saisons d'éclipses : ±20,3 jours autour de chaque passage du Soleil à un nœud."""
        demi = DEMI_SAISON_J / 365.25
        w = (xy(AN0 + 1, 0.0)[0] - xy(AN0, 0.0)[0]) * 0.18
        for an, frac, nom in passages_aux_noeuds():
            f0, f1 = frac - demi, frac + demi
            morceaux = [(an, max(0.0, f0), min(1.0, f1))]
            if f0 < 0:
                morceaux.append((an - 1, f0 + 1.0, 1.0))
            if f1 > 1:
                morceaux.append((an + 1, 0.0, f1 - 1.0))
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c('accent1' if nom == 'asc' else 'accent2', 0.16))
            for a, g0, g1 in morceaux:
                if not AN0 <= a < AN1:
                    continue
                (xa, ya), (xb, yb) = xy(a, g0), xy(a, g1)
                p.drawPolygon(QPolygonF([QPointF(xa - w, ya), QPointF(xa + w, ya), QPointF(xb + w, yb),
                                         QPointF(xb - w, yb)]))

    def _icone(self, p, x, y, genre, type_, choisie):
        r = 5.0
        if choisie:
            p.setPen(dessin.stylo('accent3', 2.0))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(x, y), r + 5, r + 5)
        if genre == 'soleil':
            plein = {'total': 'nuit', 'annular': 'nuit', 'hybrid': 'nuit'}.get(type_)
            dessin.disque(p, x, y, r, 'soleil')
            if plein:
                dessin.disque(p, x, y, r * (0.62 if type_ == 'annular' else 0.9), plein)
            else:
                dessin.disque(p, x + r * 0.45, y - r * 0.2, r * 0.8, 'nuit')
        else:
            couleur = {'total': 'mars', 'partial': 'accent3', 'penumbral': 'penombre'}.get(type_, 'lune')
            dessin.disque(p, x, y, r, 'lune')
            dessin.disque(p, x, y, r * (0.85 if type_ == 'total' else 0.6), couleur)

