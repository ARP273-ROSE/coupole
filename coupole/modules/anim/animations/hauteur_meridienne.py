"""Meridional Altitude Simulator : le plan du méridien vu de côté.  L'équateur céleste culmine à 90° − φ au-dessus
de l'horizon sud (nord dans l'hémisphère sud) ; un astre de déclinaison δ passe au méridien à la hauteur
h = 90° − φ + δ (vers le sud), ou 180° − (90° − φ + δ) au nord du zénith.  Plages du Soleil (±23,44°) et de la Lune
(±28,6° : 23,44° + 5,14° d'inclinaison de son orbite)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre

EPS = 23.44
I_LUNE = 5.14


def culmination(lat: float, dec: float) -> tuple[float, str]:
    """Hauteur au passage au méridien supérieur et côté (S ou N), comme le simulateur d'origine."""
    h = 90.0 - lat + dec
    if h > 90.0:
        return 180.0 - h, 'N'
    if h < -90.0:
        return -180.0 - h, 'N'
    return h, 'S'


class HauteurMeridienne(Animation):
    ID = 'meridaltdiagram'
    ANIMEE = False

    def construire(self):
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.dec = self.curseur('dec', -90.0, 90.0, 23.5, dec=1, unite='°', cle_texte='anim_c_dec')
        self.objet = self.choix('objet', [('anim_meridaltdiagram_etoile', 'etoile'),
                                          ('anim_meridaltdiagram_soleil', 'soleil'),
                                          ('anim_meridaltdiagram_lune', 'lune'),
                                          ('anim_meridaltdiagram_planete', 'planete'),
                                          ('anim_meridaltdiagram_aucun', 'aucun')], 'soleil')
        self.c_soleil = self.coche('plage_soleil', False)
        self.c_lune = self.coche('plage_lune', False)

    def valeurs(self):
        lat, dec = self.lat.value(), self.dec.value()
        h, cote = culmination(lat, dec)
        formule = '90° − %s + %s = %s' % (angle(lat), '(%s)' % angle(dec) if dec < 0 else angle(dec), angle(90 - lat + dec))
        if cote == 'N':
            formule = '180° − (%s) = %s' % (formule.rsplit(' = ', 1)[0], angle(h))
        out = [(tr('anim_meridaltdiagram_hauteur'), '%s (%s)' % (angle(h), tr('anim_pc_s' if cote == 'S' else
                                                                            'anim_pc_n'))),
               (tr('anim_meridaltdiagram_formule'), formule),
               (tr('anim_meridaltdiagram_eq'), angle(90 - abs(lat)))]
        if h < 0:
            out.append((tr('anim_meridaltdiagram_remarque'), tr('anim_meridaltdiagram_jamais')))
        return out

    def dessiner(self, p, rect):
        lat, dec = self.lat.value(), self.dec.value()
        cx, cy = rect.center().x(), rect.bottom() - rect.height() * 0.2
        rr = min(rect.width() * 0.42, rect.height() * 0.68)
        # horizon (sud à gauche, nord à droite), demi-cercle du ciel
        p.setPen(dessin.stylo('horizon', 2.5))
        p.drawLine(QPointF(cx - rr * 1.1, cy), QPointF(cx + rr * 1.1, cy))
        p.setPen(dessin.stylo('grille', 1.2))
        p.setBrush(dessin.c('ciel', 0.2))
        p.drawPie(QRectF(cx - rr, cy - rr, 2 * rr, 2 * rr), 0, 180 * 16)
        dessin.texte(p, cx - rr * 1.05, cy + 16, tr('anim_pc_s'), 'horizon')
        dessin.texte(p, cx + rr * 1.05, cy + 16, tr('anim_pc_n'), 'horizon')
        dessin.texte(p, cx, cy - rr - 12, tr('anim_altazimuth_zenith'), 'doux')

        def point(h_sud):
            """Hauteur mesurée depuis l'horizon sud (0 → 180 en passant par le zénith)."""
            a = math.radians(180.0 - h_sud)
            return QPointF(cx + rr * math.cos(a), cy - rr * math.sin(a))

        def arc(h1, h2, coul, ep, alpha=1.0):
            a1, a2 = sorted((h1, h2))
            p.setPen(dessin.stylo(coul, ep, alpha))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(cx - rr, cy - rr, 2 * rr, 2 * rr), int((180 - a2) * 16), int((a2 - a1) * 16))

        eq = 90.0 - lat                                    # hauteur de l'équateur céleste depuis le sud
        if self.c_lune.isChecked():
            arc(eq - EPS - I_LUNE, eq + EPS + I_LUNE, 'lune', 10, 0.35)
        if self.c_soleil.isChecked():
            arc(eq - EPS, eq + EPS, 'soleil', 6, 0.5)
        # axe du monde et équateur céleste
        pole = point(180.0 - lat if lat >= 0 else -lat)    # pôle élevé : nord à hauteur φ (côté N)
        p.setPen(dessin.stylo('equateur', 1.6))
        p.drawLine(QPointF(cx, cy), pole)
        q = point(eq)
        p.setPen(dessin.stylo('equateur', 2.0, pointille=True))
        p.drawLine(QPointF(cx, cy), q)
        dessin.texte(p, q.x() - 10, q.y() - 12, tr('anim_radecdemo_l_equateur_celeste'), 'equateur', fond=True)
        dessin.texte(p, pole.x(), pole.y() - 12, tr('anim_radecdemo_l_pnc' if lat >= 0 else 'anim_radecdemo_l_psc'),
                     'equateur', fond=True)
        # angle 90° − φ entre l'horizon sud et l'équateur
        p.setPen(dessin.stylo('accent1', 1.5))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        r2 = rr * 0.25
        p.drawArc(QRectF(cx - r2, cy - r2, 2 * r2, 2 * r2), int((180 - eq) * 16), int(eq * 16))
        dessin.texte(p, cx - r2 * 1.35, cy - r2 * 0.5, angle(eq), 'accent1', fond=True)
        if self.objet.currentData() != 'aucun':
            hs = eq + dec                                  # depuis le sud ; > 90 : passé le zénith, côté nord
            o = point(hs)
            p.setPen(dessin.stylo('texte', 1.0, 0.6, pointille=True))
            p.drawLine(QPointF(cx, cy), o)
            cle = {'etoile': 'etoile', 'soleil': 'soleil', 'lune': 'lune', 'planete': 'mars'}[self.objet.currentData()]
            dessin.disque(p, o.x(), o.y(), 9, cle, bord='fond')
            arc(eq, hs, 'arc2', 3.0)
            h, cote = culmination(lat, dec)
            dessin.texte(p, o.x(), o.y() - 18, 'h = %s' % angle(h), 'texte', fond=True)
        dessin.formule(p, rect.x() + 10, rect.y() + 20, 'h = 90° − φ + δ', 'texte', centre=False)
