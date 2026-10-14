"""Declination Ranges Simulator : coupe de la Terre et de la sphère céleste.  À la latitude φ, l'horizon est
tangent à la Terre ; les étoiles de déclinaison δ > 90° − φ sont circumpolaires, celles de δ < −(90° − φ) ne se
lèvent jamais, les autres se lèvent et se couchent (hémisphère nord ; symétrique au sud)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle


class PlagesDeclinaison(Animation):
    ID = 'latsim'
    ANIMEE = False

    def construire(self):
        self.lat = self.curseur('latitude', -90.0, 90.0, 40.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.c_agrandir = self.coche('agrandir', False)
        self._geo = None

    def valeurs(self):
        pl = astro.plages_declinaison(self.lat.value())

        def plage(x):
            if x is None:
                return tr('anim_latsim_aucune')
            return '%s → %s' % (angle(x[0]), angle(x[1]))
        return [(tr('anim_latsim_circumpolaire'), plage(pl['circumpolaire'])),
                (tr('anim_latsim_lever'), plage(pl['lever_coucher'])), (tr('anim_latsim_jamais'), plage(pl['jamais'])),
                (tr('anim_latsim_hauteur_pole'), angle(abs(self.lat.value())))]

    def presser(self, pos, bouton):
        if self._geo is not None:
            cx, cy, rt = self._geo
            a = math.atan2(cy - pos.y(), pos.x() - cx)
            ox, oy = cx + rt * math.cos(math.radians(self.lat.value())), cy - rt * math.sin(math.radians(self.lat.value()))
            if math.hypot(pos.x() - ox, pos.y() - oy) < 18 or math.hypot(pos.x() - cx, pos.y() - cy) < rt:
                self._glisse = self._tirer
                return True
        return False

    def _tirer(self, pos):
        cx, cy, _ = self._geo
        a = math.degrees(math.atan2(cy - pos.y(), pos.x() - cx))
        if a > 90:
            a = 180 - a
        elif a < -90:
            a = -180 - a
        self.lat.setValue(a)

    def dessiner(self, p, rect):
        lat = self.lat.value()
        cx, cy = rect.center().x() - rect.width() * 0.1, rect.center().y()
        rc = min(rect.width() * 0.36, rect.height() * 0.42)          # sphère céleste
        rt = rc * (0.6 if self.c_agrandir.isChecked() else 0.12)     # Terre (pas à l'échelle)
        self._geo = (cx, cy, rt)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.c('sphere', 0.25))
        p.drawEllipse(QPointF(cx, cy), rc, rc)
        # bandes colorées sur le bord : angles = déclinaisons (axe du monde vertical)
        pl = astro.plages_declinaison(lat)
        ep = max(8.0, rc * 0.06)
        for cle, coul in (('circumpolaire', 'accent1'), ('lever_coucher', 'accent2'), ('jamais', 'accent3')):
            x = pl[cle]
            if x is None:
                continue
            for cote in (0, 180):
                debut = x[0] if cote == 0 else 180 - x[1]
                p.setPen(dessin.stylo(coul, ep, 0.85))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                rr = rc + ep / 2 + 2
                p.drawArc(QRectF(cx - rr, cy - rr, 2 * rr, 2 * rr), int(debut * 16), int((x[1] - x[0]) * 16))
        # équateur céleste et axe du monde
        p.setPen(dessin.stylo('equateur', 1.5, pointille=True))
        p.drawLine(QPointF(cx - rc, cy), QPointF(cx + rc, cy))
        p.setPen(dessin.stylo('equateur', 2.0))
        p.drawLine(QPointF(cx, cy - rc * 1.08), QPointF(cx, cy + rc * 1.08))
        dessin.texte(p, cx, cy - rc * 1.14, tr('anim_radecdemo_l_pnc'), 'equateur')
        dessin.texte(p, cx, cy + rc * 1.14, tr('anim_radecdemo_l_psc'), 'equateur')
        # Terre et observateur
        dessin.disque(p, cx, cy, rt, 'terre', alpha=0.85 if not self.c_agrandir.isChecked() else 0.5)
        a = math.radians(lat)
        ox, oy = cx + rt * math.cos(a), cy - rt * math.sin(a)
        # horizon (tangent) prolongé jusqu'à la sphère céleste, et zénith
        tx, ty = -math.sin(a), -math.cos(a)                               # direction tangente (vers le nord)
        p.setPen(dessin.stylo('horizon', 2.0))
        p.drawLine(QPointF(cx - tx * rc, cy - ty * rc), QPointF(cx + tx * rc, cy + ty * rc))
        p.setPen(dessin.stylo('horizon', 2.0, 0.6))
        p.drawLine(QPointF(ox - tx * rt * 2, oy - ty * rt * 2), QPointF(ox + tx * rt * 2, oy + ty * rt * 2))
        p.setPen(dessin.stylo('accent3', 2.0))
        p.drawLine(QPointF(ox, oy), QPointF(ox + math.cos(a) * rt * 0.9, oy - math.sin(a) * rt * 0.9))
        dessin.disque(p, ox, oy, 4.5, 'accent3')
        dessin.texte(p, cx + math.cos(a) * rc * 1.07, cy - math.sin(a) * rc * 1.07, tr('anim_altazimuth_zenith'),
                     'accent3', fond=True)
        # légende
        # légende : assez à gauche pour que les libellés tiennent dans la toile
        larg = max(p.fontMetrics().horizontalAdvance(tr(k)) for k in ('anim_latsim_circumpolaire', 'anim_latsim_lever',
                                                                      'anim_latsim_jamais'))
        x0, y0 = min(rect.right() - rect.width() * 0.22, rect.right() - 10 - 28 - larg), rect.y() + 30
        for i, (cle, coul) in enumerate((('anim_latsim_circumpolaire', 'accent1'), ('anim_latsim_lever', 'accent2'),
                                         ('anim_latsim_jamais', 'accent3'))):
            p.setPen(dessin.stylo(coul, 8.0))
            p.drawLine(QPointF(x0, y0 + i * 26), QPointF(x0 + 20, y0 + i * 26))
            dessin.texte(p, x0 + 28, y0 + i * 26 + 4, tr(cle), 'texte', centre=False)
        dessin.texte(p, x0, y0 + 90, '%s : %s' % (tr('anim_c_latitude'), angle(lat)), 'texte', centre=False)
