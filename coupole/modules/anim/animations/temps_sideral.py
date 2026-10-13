"""Sidereal and Solar Time Simulator : la Terre tourne sur elle-même en parcourant son orbite.  Le temps solaire
suit le Soleil, le temps sidéral les étoiles : en une année de N jours solaires, la Terre fait N + 1 tours par
rapport aux étoiles, d'où un jour sidéral de 86 400 × N / (N + 1) s.

Origine (comme l'original) : à midi solaire de l'équinoxe de mars, le temps sidéral vaut 0 h."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, heures_minutes, nombre

ANNEES = (('anim_siderealsolartime_simple', 365.0), ('anim_siderealsolartime_julienne', 365.25),
          ('anim_siderealsolartime_tropique', astro.ANNEE_TROPIQUE_J))
MIDI = 0.5


def temps_sideral_h(t_jours: float, annee: float) -> float:
    """Temps sidéral (heures) au temps solaire t (jours depuis minuit de l'équinoxe)."""
    return 24.0 * (((t_jours - MIDI) * (annee + 1.0) / annee) % 1.0)


def temps_solaire_pour_sideral(ts_h: float, t_jours: float, annee: float) -> float:
    """Prochain instant (jours) ≥ t où le temps sidéral vaut ts_h."""
    k = (annee + 1.0) / annee
    actuel = temps_sideral_h(t_jours, annee)
    return t_jours + ((ts_h - actuel) % 24.0) / 24.0 / k


class TempsSideral(Animation):
    ID = 'siderealSolarTime'
    JOURS_PAR_S = 0.1

    def construire(self):
        self.annee = self.choix('annee', list(ANNEES), 365.0)
        self.t = MIDI
        for cle, h in (('anim_siderealsolartime_minuit', 0.0), ('anim_siderealsolartime_lever', 6.0),
                       ('anim_siderealsolartime_midi', 12.0), ('anim_siderealsolartime_coucher', 18.0)):
            self.bouton(cle, lambda _=False, x=h: self._solaire(x))
        for h in (0, 6, 12, 18):
            self.bouton('anim_siderealsolartime_ts%d' % h, lambda _=False, x=h: self._sideral(x))
        self.bouton('anim_siderealsolartime_plus1_sol', lambda: self._ajouter(1.0))
        self.bouton('anim_siderealsolartime_plus10_sol', lambda: self._ajouter(10.0))
        self.bouton('anim_siderealsolartime_plus1_sid', lambda: self._ajouter(self._jour_sideral()))
        self.bouton('anim_siderealsolartime_plus10_sid', lambda: self._ajouter(10 * self._jour_sideral()))
        for i, cle in enumerate(('equinoxe_mars', 'solstice_juin', 'equinoxe_sept', 'solstice_dec')):
            self.bouton('anim_sunsrays_' + cle, lambda _=False, k=i: self._saison(k))

    def _n(self) -> float:
        return float(self.annee.currentData())

    def _jour_sideral(self) -> float:
        return self._n() / (self._n() + 1.0)

    def _ajouter(self, jours: float):
        self.t += jours
        self.rafraichir()

    def _solaire(self, h: float):
        base = math.floor(self.t)
        cible = base + h / 24.0
        if cible < self.t - 1e-9:
            cible += 1.0
        self.t = cible
        self.rafraichir()

    def _sideral(self, h: float):
        self.t = temps_solaire_pour_sideral(h, self.t + 1e-9, self._n())
        self.rafraichir()

    def _saison(self, k: int):
        n = self._n()
        cycles = math.floor(self.t / n)
        heure = self.t % 1.0
        self.t = cycles * n + round(k * n / 4.0) + heure
        self.rafraichir()

    def etat_initial(self):
        self.t = MIDI

    def avancer(self, dt):
        self.t += dt * self.JOURS_PAR_S

    def valeurs(self):
        n = self._n()
        js = astro.jour_sideral_s(n)
        hh = int(js // 3600)
        mm = int((js - 3600 * hh) // 60)
        ss = js - 3600 * hh - 60 * mm
        return [(tr('anim_siderealsolartime_solaire'), heures_minutes(24 * (self.t % 1.0))),
                (tr('anim_siderealsolartime_sideral'), heures_minutes(temps_sideral_h(self.t, n))),
                (tr('anim_siderealsolartime_jours'), nombre(self.t % n, 2)),
                (tr('anim_siderealsolartime_duree_sid'), '%d h %02d min %s s' % (hh, mm, nombre(ss, 3))),
                (tr('anim_siderealsolartime_ecart'), '%s s' % nombre(86400 - js, 2))]

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.9)
        self._orbite(p, dessin.cadre(p, z[0], tr('anim_siderealsolartime_vue_orbite')))
        r = dessin.cadre(p, z[1], tr('anim_siderealsolartime_horloges'))
        h2 = dessin.zones(r, 2, 0.9)
        n = self._n()
        self._horloge(p, h2[0], 24 * (self.t % 1.0), tr('anim_siderealsolartime_solaire'), 'soleil')
        self._horloge(p, h2[1], temps_sideral_h(self.t, n), tr('anim_siderealsolartime_sideral'), 'accent2')

    def _orbite(self, p, r):
        n = self._n()
        cx, cy = r.center().x(), r.center().y()
        ro = min(r.width(), r.height()) * 0.36
        p.setPen(dessin.stylo('grille', 1.2))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), ro, ro)
        dessin.disque(p, cx, cy, ro * 0.12, 'soleil')
        jours = self.t - MIDI
        a_orb = 2 * math.pi * (jours % n) / n - math.pi / 2          # Terre en bas à l'équinoxe de mars
        ex, ey = cx + ro * math.cos(a_orb), cy - ro * math.sin(a_orb)
        rt = ro * 0.16
        dessin.disque(p, ex, ey, rt, 'terre')
        # moitié nuit (opposée au Soleil)
        vers_soleil = math.degrees(math.atan2(-(cy - ey), cx - ex))
        p.setPen(dessin.Qt.PenStyle.NoPen)
        p.setBrush(dessin.c('nuit', 0.7))
        p.drawPie(QRectF(ex - rt, ey - rt, 2 * rt, 2 * rt), int((vers_soleil + 90) * 16), 180 * 16)
        # observateur : face au Soleil à midi ; rotation propre de 360° (N+1)/N par jour solaire
        a_obs = math.radians(vers_soleil) + 2 * math.pi * (self.t % 1.0 - 0.5)
        ox, oy = ex + rt * math.cos(a_obs), ey - rt * math.sin(a_obs)
        p.setPen(dessin.stylo('accent3', 2.5))
        p.drawLine(QPointF(ox, oy), QPointF(ox + rt * 0.9 * math.cos(a_obs), oy - rt * 0.9 * math.sin(a_obs)))
        # direction d'une étoile lointaine (fixe) : flèche vers le haut de l'écran
        p.setPen(dessin.stylo('accent2', 1.2, 0.8, pointille=True))
        p.drawLine(QPointF(ex, ey), QPointF(ex, r.y() + 8))
        dessin.texte(p, ex + 8, r.y() + 16, tr('anim_siderealsolartime_etoile'), 'accent2', centre=False)
        p.setPen(dessin.stylo('soleil', 1.2, 0.8, pointille=True))
        p.drawLine(QPointF(ex, ey), QPointF(cx, cy))

    def _horloge(self, p, r, heures: float, titre: str, cle: str):
        cx, cy = r.center().x(), r.center().y() + 8
        rr = min(r.width(), r.height()) * 0.36
        p.setPen(dessin.stylo('grille', 1.5))
        p.setBrush(dessin.c('sphere', 0.4))
        p.drawEllipse(QPointF(cx, cy), rr, rr)
        dessin.police(p, 0.75)
        for h in range(24):
            a = math.radians(90 - h * 15 - 180)                        # 0 h en bas, 12 h en haut
            p.setPen(dessin.stylo('doux', 1.0))
            p.drawLine(QPointF(cx + rr * 0.9 * math.cos(a), cy - rr * 0.9 * math.sin(a)),
                       QPointF(cx + rr * math.cos(a), cy - rr * math.sin(a)))
            if h % 3 == 0:
                dessin.texte(p, cx + rr * 0.74 * math.cos(a), cy - rr * 0.74 * math.sin(a), str(h), 'doux')
        dessin.police(p, 1 / 0.75)
        a = math.radians(90 - heures * 15 - 180)
        dessin.fleche(p, cx, cy, cx + rr * 0.8 * math.cos(a), cy - rr * 0.8 * math.sin(a), dessin.stylo(cle, 3.0), 9)
        dessin.texte(p, cx, r.y() + 12, titre, cle)
        dessin.texte(p, cx, cy + rr + 14, heures_minutes(heures), 'texte')
