"""Lunar Phases Simulator (NAAP) : la Lune sur son orbite (vue du dessus, le Soleil à droite), sa phase vue de la
Terre, et sa position dans le ciel de l'observateur selon l'heure.  Lunaison moyenne 29,53 jours.

Comme dans le simulateur d'origine, l'orbite de la Lune est ramenée dans le plan de l'équateur céleste : dans le
ciel local, le Soleil et la Lune sont sur l'équateur céleste, d'ascensions droites α☉ = 12 h − heure et
α☾ = α☉ + angle de phase / 15 (le temps sidéral local valant 0)."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..base import Animation, angle, heures_minutes, nombre

PHASES = ('nl', 'pc', 'pq', 'gc', 'pl', 'gd', 'dq', 'dc')
ANGLES_PHASES = {'nl': 0.0, 'pc': 45.0, 'pq': 90.0, 'gc': 135.0, 'pl': 180.0, 'gd': 225.0, 'dq': 270.0, 'dc': 315.0}


def ciel(heure: float, phase: float, lat: float) -> dict:
    """Hauteurs et azimuts du Soleil et de la Lune (sur l'équateur céleste) pour l'heure solaire locale."""
    h_sol = (heure - 12.0) * 15.0
    h_lune = h_sol - phase
    az_s, alt_s = astro.equatorial_vers_horizon(h_sol, 0.0, lat)
    az_l, alt_l = astro.equatorial_vers_horizon(h_lune, 0.0, lat)
    return {'az_soleil': az_s, 'alt_soleil': alt_s, 'az_lune': az_l, 'alt_lune': alt_l}


def temps_depuis_nouvelle(phase: float, mois: float = astro.MOIS_SYNODIQUE_J) -> float:
    return mois * (phase % 360.0) / 360.0


class PhasesLune(Animation):
    ID = 'lunar_applet'
    JOURS_PAR_S = 0.25

    def construire(self):
        self.ciel3d = self.vue(200.0, 25.0, 10.0, 89.0)
        self.phase = self.curseur('phase', 0.0, 360.0, 0.0, dec=1, unite='°', cle_texte='anim_lunar_applet_phase')
        self.heure = self.curseur('heure', 0.0, 24.0, 12.0, dec=2, unite='h', cle_texte='anim_c_heure')
        self.lat = self.curseur('latitude', -90.0, 90.0, 41.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.nom = self.choix('nom_phase', [('anim_phase_' + k, k) for k in PHASES], 'nl')
        self.nom.activated.connect(self._phase_choisie)
        for cle, dj in (('anim_lunar_applet_j_moins', -1.0), ('anim_lunar_applet_j_plus', 1.0),
                        ('anim_lunar_applet_h_moins', -1 / 24), ('anim_lunar_applet_h_plus', 1 / 24),
                        ('anim_lunar_applet_min_moins', -1 / 1440), ('anim_lunar_applet_min_plus', 1 / 1440)):
            self.bouton(cle, lambda _=False, d=dj: self.decaler(d))
        self.c_angle = self.coche('angle', False)
        self.c_heures = self.coche('reperes', False)
        self.c_repere = self.coche('repere', False)
        self._orbite_rect = None

    def _phase_choisie(self, *_):
        self.phase.setValue(ANGLES_PHASES[self.nom.currentData()])

    def decaler(self, jours: float):
        """Avance le temps de `jours` : l'heure tourne, la phase progresse de 360° par lunaison."""
        h = self.heure.value() + jours * 24.0
        self.heure.setValue(h % 24.0)
        self.phase.setValue((self.phase.value() + jours * 360.0 / astro.MOIS_SYNODIQUE_J) % 360.0)

    def avancer(self, dt):
        self.decaler(dt * self.JOURS_PAR_S)

    def reglage_change(self):
        cle = astro.nom_de_phase(self.phase.value())
        if self.nom.currentData() != cle:
            self.nom.blockSignals(True)
            self.nom.setCurrentIndex(self.nom.findData(cle))
            self.nom.blockSignals(False)
        super().reglage_change()

    def valeurs(self):
        ph = self.phase.value()
        t = temps_depuis_nouvelle(ph)
        c = ciel(self.heure.value(), ph, self.lat.value())
        return [(tr('anim_lunar_applet_nom_phase'), tr('anim_phase_' + astro.nom_de_phase(ph))),
                (tr('anim_lunar_applet_eclairee'), '%s %%' % nombre(100 * astro.fraction_eclairee(ph), 1)),
                (tr('anim_lunar_applet_depuis_nouvelle'), tr('anim_lunar_applet_jh', j=int(t),
                                                             h=int((t - int(t)) * 24))),
                (tr('anim_c_heure'), heures_minutes(self.heure.value())),
                (tr('anim_lunar_applet_elongation'), angle(ph if ph <= 180 else 360 - ph)),
                (tr('anim_lunar_applet_h_soleil'), angle(c['alt_soleil'])),
                (tr('anim_lunar_applet_h_lune'), angle(c['alt_lune']))]

    # ------------------------------------------------------------ souris (vue de l'orbite)
    def presser(self, pos, bouton):
        r = self._orbite_rect
        if r is not None and r[0].contains(pos):
            _, cx, cy, ro, rt = r
            mx, my = cx + ro * math.cos(math.radians(self.phase.value())), cy - ro * math.sin(
                math.radians(self.phase.value()))
            if math.hypot(pos.x() - mx, pos.y() - my) < 16:
                self._glisse = self._tirer_lune
            else:
                self._glisse = self._tirer_terre
            return True
        return super().presser(pos, bouton)

    def _tirer_lune(self, pos):
        _, cx, cy, _, _ = self._orbite_rect
        self.phase.setValue(math.degrees(math.atan2(cy - pos.y(), pos.x() - cx)) % 360.0)

    def _tirer_terre(self, pos):
        _, cx, cy, _, _ = self._orbite_rect
        a = math.degrees(math.atan2(cy - pos.y(), pos.x() - cx))
        self.heure.setValue((12.0 + a / 15.0) % 24.0)

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2)
        self._orbite(p, dessin.cadre(p, z[0], tr('anim_lunar_applet_vue_orbite')))
        self._phase(p, dessin.cadre(p, z[1], tr('anim_lunar_applet_vue_phase')))
        self._ciel(p, dessin.cadre(p, z[2], tr('anim_lunar_applet_vue_ciel')))

    def _orbite(self, p, r):
        cx, cy = r.center().x(), r.center().y()
        ro = min(r.width(), r.height()) * 0.38
        rt = ro * 0.22
        self._orbite_rect = (QRectF(r), cx, cy, ro, rt)
        for k in (-0.8, -0.4, 0.0, 0.4, 0.8):                                    # lumière du Soleil, à droite
            y = cy + k * ro
            dessin.fleche(p, r.right() - 6, y, r.right() - ro * 0.35, y, dessin.stylo('soleil', 1.3, 0.7), 6)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), ro, ro)
        # Terre : jour à droite, nuit à gauche
        dessin.disque(p, cx, cy, rt, 'terre')
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('nuit', 0.7))
        p.drawPie(QRectF(cx - rt, cy - rt, 2 * rt, 2 * rt), 90 * 16, 180 * 16)
        if self.c_heures.isChecked():
            dessin.police(p, 0.75)
            for hh in range(0, 24, 3):
                a = math.radians((hh - 12) * 15)
                dessin.texte(p, cx + rt * 1.55 * math.cos(a), cy - rt * 1.55 * math.sin(a), '%d h' % hh, 'doux')
            dessin.police(p, 1 / 0.75)
        # observateur
        a = math.radians((self.heure.value() - 12.0) * 15.0)
        ox, oy = cx + rt * math.cos(a), cy - rt * math.sin(a)
        p.setPen(dessin.stylo('accent3', 2.5))
        p.drawLine(QPointF(ox, oy), QPointF(ox + 0.6 * rt * math.cos(a), oy - 0.6 * rt * math.sin(a)))
        p.setPen(dessin.stylo('horizon', 1.5))
        p.drawLine(QPointF(ox - 0.7 * rt * math.sin(a), oy - 0.7 * rt * math.cos(a)),
                   QPointF(ox + 0.7 * rt * math.sin(a), oy + 0.7 * rt * math.cos(a)))
        # Lune : moitié éclairée tournée vers le Soleil (à droite)
        ph = math.radians(self.phase.value())
        mx, my = cx + ro * math.cos(ph), cy - ro * math.sin(ph)
        rl = max(5.0, rt * 0.45)
        dessin.disque(p, mx, my, rl, 'nuit')
        p.setBrush(dessin.c('lune'))
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.drawPie(QRectF(mx - rl, my - rl, 2 * rl, 2 * rl), -90 * 16, 180 * 16)
        if self.c_repere.isChecked():
            dessin.disque(p, mx - rl * 0.8 * math.cos(ph), my + rl * 0.8 * math.sin(ph), 2.2, 'accent3')
        if self.c_angle.isChecked():
            p.setPen(dessin.stylo('accent1', 1.5))
            p.drawLine(QPointF(cx, cy), QPointF(mx, my))
            p.drawLine(QPointF(cx, cy), QPointF(cx + ro * 0.6, cy))
            rr = ro * 0.45
            p.drawArc(QRectF(cx - rr, cy - rr, 2 * rr, 2 * rr), 0, int(self.phase.value() * 16))
            dessin.texte(p, cx + rr * 0.8 * math.cos(ph / 2), cy - rr * 0.8 * math.sin(ph / 2),
                         angle(self.phase.value(), 0), 'accent1')

    def _phase(self, p, r):
        rr = min(r.width(), r.height()) * 0.36
        cx, cy = r.center().x(), r.center().y() - 8
        dessin.phase_lune(p, cx, cy, rr, self.phase.value())
        if self.c_repere.isChecked():
            dessin.disque(p, cx, cy, 3, 'accent3')
        dessin.texte(p, cx, cy + rr + 16, tr('anim_phase_' + astro.nom_de_phase(self.phase.value())), 'texte')
        dessin.texte(p, cx, cy + rr + 34, '%s %%' % nombre(100 * astro.fraction_eclairee(self.phase.value()), 1),
                     'doux')

    def _ciel(self, p, r):
        self.zone_rotative(r, self.ciel3d)
        rr = min(r.width(), r.height()) * 0.40
        cx, cy = r.center().x(), r.center().y() + 4
        lat = self.lat.value()
        c = ciel(self.heure.value(), self.phase.value(), lat)
        soleil = np.array(astro.vecteur_horizon(c['az_soleil'], c['alt_soleil']))
        lune = np.array(astro.vecteur_horizon(c['az_lune'], c['alt_lune']))
        jour = c['alt_soleil'] > 0
        m = np.array(astro.matrice_equatorial_vers_horizon(0.0, lat))

        def scene(pe):
            pe.courbe(dessin.cercle((0, 0, 1)) @ m.T, 'equateur', 1.2, 0.8)
            pe.point(soleil, 'soleil', 8.0)
            pe.point(lune, 'lune', 7.0, bord='doux')

        scenes.sphere_locale(p, self.ciel3d, cx, cy, rr, scene, couleur_ciel='ciel' if jour else 'nuit')
