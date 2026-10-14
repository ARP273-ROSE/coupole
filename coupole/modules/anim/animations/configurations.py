"""Planetary Configurations Simulator (NAAP) : deux planètes sur des orbites circulaires coplanaires (modèle de
Copernic simplifié, périodes par la 3e loi de Kepler) ; l'une sert d'observatoire (la Terre par défaut).  Les
configurations reviennent à chaque période synodique S (1/S = |1/P₁ − 1/P₂|) : opposition, quadratures et
conjonction pour une planète supérieure ; conjonctions inférieure et supérieure et plus grandes élongations
(sin E = a_int / a_ext) pour une planète inférieure.  L'animation peut s'arrêter ou faire une pause à chaque
configuration, comme l'original."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, QTimer

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre
from .phases_venus import elongation_signee

PLANETES = (('mercure', 0.387_098), ('venus', 0.723_332), ('terre', 1.000_001), ('mars', 1.523_679),
            ('jupiter', 5.2026), ('saturne', 9.5549))


def configurations(a_obs: float, a_cible: float) -> dict:
    """Période synodique et instants (fractions de S, en partant de la conjonction ou opposition alignée) des quatre
    configurations, comme l'original : 0, acos(a_int / a_ext) / ω, S/2, S − acos(a_int / a_ext) / ω."""
    p_obs, p_cible = astro.periode_annees(a_obs), astro.periode_annees(a_cible)
    s = astro.periode_synodique(p_obs, p_cible)
    a_int, a_ext = min(a_obs, a_cible), max(a_obs, a_cible)
    t1 = math.acos(a_int / a_ext) / (2 * math.pi / s)
    superieure = a_cible > a_obs
    noms = (('opposition', 'quadrature_est', 'conjonction', 'quadrature_ouest') if superieure else
            ('conj_inf', 'elong_ouest', 'conj_sup', 'elong_est'))
    return {'S': s, 'temps': (0.0, t1, s / 2, s - t1), 'noms': noms, 'superieure': superieure,
            'elongation_max': None if superieure else math.degrees(math.asin(a_cible / a_obs))}


def positions(a_obs: float, a_cible: float, t: float) -> tuple:
    """Positions à l'instant t (années) ; à t = 0 les deux planètes sont alignées du même côté du Soleil (longitude 0)."""
    out = []
    for a in (a_obs, a_cible):
        th = 2 * math.pi * t / astro.periode_annees(a)
        out.append((a * math.cos(th), a * math.sin(th)))
    return tuple(out)


class Configurations(Animation):
    ID = 'configurationssimulator'

    def construire(self):
        self.a_obs = self.curseur('a_obs', 0.25, 10.0, 1.0, dec=3, unite='ua')
        self.p_obs = self.choix('p_obs', [('anim_gravcalc_libre', 0.0)] +
                                [('anim_planete_' + n, a) for n, a in PLANETES], 1.000_001)
        self.a_cible = self.curseur('a_cible', 0.25, 10.0, 2.4, dec=3, unite='ua')
        self.p_cible = self.choix('p_cible', [('anim_gravcalc_libre', 0.0)] +
                                  [('anim_planete_' + n, a) for n, a in PLANETES], 0.0)
        self.p_obs.activated.connect(lambda *_: self._prereglage(self.p_obs, self.a_obs))
        self.p_cible.activated.connect(lambda *_: self._prereglage(self.p_cible, self.a_cible))
        self.action = self.choix('action', [('anim_configurationssimulator_continuer', 'continuer'),
                                            ('anim_configurationssimulator_arreter', 'arreter'),
                                            ('anim_configurationssimulator_pause', 'pause')], 'continuer')
        self.duree_pause = self.curseur('duree_pause', 1.0, 15.0, 5.0, dec=0, unite='s')
        self.c_elong = self.coche('elongation', True)
        self._reprise = QTimer(self)
        self._reprise.setSingleShot(True)
        self._reprise.timeout.connect(self._reprendre)
        self.t = 0.0

    def _prereglage(self, combo, reglage):
        if combo.currentData():
            reglage.setValue(combo.currentData())

    def _reprendre(self):
        if not self.en_lecture:
            self.basculer_lecture()

    def etat_initial(self):
        self.t = 0.0
        if hasattr(self, '_reprise'):
            self._reprise.stop()

    def systeme(self) -> dict:
        return configurations(self.a_obs.value(), self.a_cible.value())

    def prochain(self, t: float) -> tuple:
        """(instant, nom) de la prochaine configuration après t."""
        c = self.systeme()
        s = c['S']
        if not math.isfinite(s):
            return math.inf, ''
        n = math.floor(t / s)
        for k in (n, n + 1):
            for tk, nom in zip(c['temps'], c['noms']):
                if k * s + tk > t + 1e-12:
                    return k * s + tk, nom
        return math.inf, ''

    def avancer(self, dt):
        pas = dt * min(astro.periode_annees(self.a_obs.value()), astro.periode_annees(self.a_cible.value())) / 10.0
        t1 = self.t + pas
        tp, _ = self.prochain(self.t)
        action = self.action.currentData()
        if action != 'continuer' and t1 >= tp:
            self.t = tp
            if self.en_lecture:
                self.basculer_lecture()
            if action == 'pause':
                self._reprise.start(int(self.duree_pause.value() * 1000))
            return
        self.t = t1

    def basculer_lecture(self):
        if self.en_lecture and hasattr(self, '_reprise'):
            self._reprise.stop()
        super().basculer_lecture()
        if self.en_lecture:
            self.t += 1e-9                       # repartir au-delà de la configuration où l'on s'était arrêté

    def valeurs(self):
        c = self.systeme()
        obs, cible = positions(self.a_obs.value(), self.a_cible.value(), self.t)
        e = elongation_signee(cible, obs)
        tp, nom = self.prochain(self.t)
        out = [(tr('anim_configurationssimulator_s'), '%s %s' % (nombre(c['S'], 3), tr('anim_u_annees'))
                if math.isfinite(c['S']) else '—'),
               (tr('anim_c_elongation'), '%s %s' % (angle(abs(e), 1), tr('anim_est' if e > 0 else 'anim_ouest'))),
               (tr('anim_configurationssimulator_temps'), '%s %s' % (nombre(self.t, 3), tr('anim_u_annees')))]
        if nom:
            out.append((tr('anim_configurationssimulator_prochain'),
                        tr('anim_configurationssimulator_dans', nom=tr('anim_configurationssimulator_e_' + nom),
                           j=nombre((tp - self.t) * astro.ANNEE_SIDERALE_J, 0))))
        if c['elongation_max'] is not None:
            out.append((tr('anim_configurationssimulator_elong_max'), angle(c['elongation_max'], 1)))
        return out

    def dessiner(self, p, rect):
        haut = rect.height() * 0.80
        self._orbites(p, QRectF(rect.x(), rect.y(), rect.width(), haut))
        self._frise(p, dessin.cadre(p, QRectF(rect.x(), rect.y() + haut, rect.width(), rect.height() - haut)))

    def _orbites(self, p, r):
        a1, a2 = self.a_obs.value(), self.a_cible.value()
        cx, cy = r.center().x(), r.center().y()
        k = min(r.width(), r.height()) * 0.46 / max(a1, a2)
        obs, cible = positions(a1, a2, self.t)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for a in (a1, a2):
            p.drawEllipse(QPointF(cx, cy), a * k, a * k)
        dessin.disque(p, cx, cy, max(7.0, k * 0.06), 'soleil')
        ox, oy = cx + k * obs[0], cy - k * obs[1]
        tx, ty = cx + k * cible[0], cy - k * cible[1]
        if self.c_elong.isChecked():
            p.setPen(dessin.stylo('accent1', 1.2, 0.8))
            p.drawLine(QPointF(ox, oy), QPointF(cx, cy))
            p.drawLine(QPointF(ox, oy), QPointF(tx, ty))
            e = elongation_signee(cible, obs)
            ls = math.degrees(math.atan2(-obs[1], -obs[0]))
            rr = 26.0
            p.drawArc(QRectF(ox - rr, oy - rr, 2 * rr, 2 * rr), int(ls * 16), int(e * 16))
        dessin.disque(p, ox, oy, 7, 'terre', bord='texte')
        dessin.disque(p, tx, ty, 7, 'mars', bord='texte')
        dessin.texte(p, ox, oy - 15, tr('anim_configurationssimulator_observateur'), fond=True)
        dessin.texte(p, tx, ty - 15, tr('anim_configurationssimulator_cible'), fond=True)

    def _frise(self, p, r):
        """Un cycle synodique : les quatre configurations et l'instant présent."""
        c = self.systeme()
        s = c['S']
        if not math.isfinite(s):
            return
        x0, x1 = r.x() + 10, r.right() - 10
        y = r.center().y() - 4
        p.setPen(dessin.stylo('grille', 1.2))
        p.drawLine(QPointF(x0, y), QPointF(x1, y))
        dessin.police(p, 0.75)
        for i, (tk, nom) in enumerate(zip(c['temps'], c['noms'])):
            x = x0 + (x1 - x0) * tk / s
            dessin.disque(p, x, y, 4, 'accent2')
            texte = tr('anim_configurationssimulator_e_' + nom)
            demi = p.fontMetrics().horizontalAdvance(texte) / 2 + 2
            dessin.texte(p, min(max(x, x0 + demi), x1 - demi), y + (14 if i % 2 == 0 else -13), texte, 'doux')
        dessin.police(p, 1 / 0.75)
        x = x0 + (x1 - x0) * ((self.t % s) / s)
        p.setPen(dessin.stylo('accent3', 2.0))
        p.drawLine(QPointF(x, y - 9), QPointF(x, y + 5))
