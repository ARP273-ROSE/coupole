"""Étoiles filantes et radiant : une nuit d'observation d'une pluie d'étoiles filantes (Quadrantides, Lyrides,
êta Aquarides, Perséides, Orionides, Léonides, Géminides) dans le ciel vu de dessous.  Les traînées, prolongées vers
l'arrière, se croisent au radiant (perspective de trajectoires parallèles) ; courtes près du radiant, longues loin
de lui.  Le radiant se lève, monte et culmine avec les étoiles ; le taux horaire suit sa hauteur
(ZHR × sin h) et la qualité du ciel.  Calculs : ``meteores.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin, meteores as me
from ..base import Animation, angle, heures_minutes, nombre
from ..graphe import Axes

HEURES_PAR_S = 0.25              # 15 min de nuit par seconde à la vitesse ×1
TAUX_AFFICHE = 1.0 / 25.0        # étoiles filantes montrées par seconde, par étoile filante et par heure réelle
DUREE_VIE = 0.8                  # durée d'une traînée à l'écran (s)


def vers_ecran(cx: float, cy: float, rr: float, az: float, alt: float) -> QPointF:
    """Projection du ciel vu de dessous (zénith au centre, nord en haut, est à gauche), équidistante en hauteur."""
    r = (90.0 - alt) / 90.0 * rr
    a = math.radians(az)
    return QPointF(cx - r * math.sin(a), cy - r * math.cos(a))


class Radiant(Animation):
    ID = 'meteorradiant'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.essaim = self.choix('essaim', [('anim_meteorradiant_e_' + k, k) for k in me.ESSAIMS], 'perseides')
        self.lat = self.curseur('latitude', -60.0, 70.0, 45.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.heure = self.curseur('heure', 18.0, 30.0, 22.0, dec=2, unite='h')
        self.mlim = self.curseur('mlim', 3.0, 7.0, 6.5, dec=1)
        self.c_prolonger = self.coche('prolonger', True)
        self.c_etoiles = self.coche('etoiles', True)
        self.fond = me.etoiles_de_fond()
        self.etat_initial()

    def etat_initial(self):
        self.alea = me.Aleatoire(4242)
        self.filantes = []          # [âge, az0, h0, az1, h1]
        self.reservoir = 0.0
        self.vues = 0

    def radiant(self):
        return me.hauteur_radiant(self.essaim.currentData(), self.heure.value(), self.lat.value())

    def avancer(self, dt):
        h = self.heure.value() + dt * HEURES_PAR_S
        if h >= 30.0:
            h = 18.0 + (h - 30.0) % 12.0
        self.heure.setValue(h)
        for f in self.filantes:
            f[0] += dt
        self.filantes = [f for f in self.filantes if f[0] < DUREE_VIE]
        az_r, h_r = self.radiant()
        hr = me.taux_horaire(self.essaim.currentData(), h_r, self.mlim.value())
        self.reservoir += hr * TAUX_AFFICHE * dt
        while self.reservoir >= 1.0:
            self.reservoir -= 1.0
            t = me.trainee(self.alea, az_r, h_r)
            if t is not None:
                self.filantes.append([0.0, t[0], t[1], t[2], t[3]])
                self.vues += 1

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        k = self.essaim.currentData()
        mois, jour, alpha, delta, v, zhr, r, cons = me.ESSAIMS[k]
        az_r, h_r = self.radiant()
        hr = me.taux_horaire(k, h_r, self.mlim.value())
        hc, hmax = me.culmination(k, self.lat.value())
        hs = me.hauteur_soleil(k, self.heure.value(), self.lat.value())
        ciel = 'nuit' if hs < -18 else ('crepuscule' if hs < 0 else 'jour')
        return [(tr('anim_meteorradiant_v_maximum'), tr('anim_meteorradiant_date', j=jour, m=tr('anim_mois_%d' % mois))),
                (tr('anim_meteorradiant_v_radiant'), 'α = %s, δ = %s — %s' % (tr('anim_meteorradiant_ad', h=int(alpha // 15), m='%02d' % round(alpha % 15 * 4)),
                                                                                ('+' if delta >= 0 else '') + angle(delta, 0),
                                                                                tr('anim_meteorradiant_c_' + cons))),
                (tr('anim_meteorradiant_v_vitesse'), '%s km·s⁻¹' % nombre(v, 0)),
                (tr('anim_meteorradiant_v_zhr'), nombre(zhr, 0)),
                (tr('anim_meteorradiant_v_heure'), heures_minutes(self.heure.value())),
                (tr('anim_meteorradiant_v_hauteur'), angle(h_r, 1) if h_r > 0 else tr('anim_meteorradiant_sous_horizon',
                                                                                         h=angle(h_r, 1))),
                (tr('anim_meteorradiant_v_taux'), tr('anim_meteorradiant_par_heure', n=nombre(hr, 0))),
                (tr('anim_meteorradiant_v_culmination'), '%s — %s' % (heures_minutes(hc), angle(hmax, 0))),
                (tr('anim_meteorradiant_v_soleil'), '%s — %s' % (angle(hs, 0), tr('anim_meteorradiant_ciel_' + ciel)))]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.6)
        self._ciel(p, dessin.cadre(p, z[0], tr('anim_meteorradiant_t_ciel')))
        self._nuit(p, dessin.cadre(p, z[1], tr('anim_meteorradiant_t_nuit')))

    def _ciel(self, p, r):
        rr = min(r.width(), r.height() - 20) / 2.0 - 14
        cx, cy = r.center().x(), r.center().y() + 4
        k = self.essaim.currentData()
        hs = me.hauteur_soleil(k, self.heure.value(), self.lat.value())
        nuit = max(0.0, min(1.0, (-hs - 2.0) / 14.0))       # 0 : jour, 1 : nuit noire (Soleil sous −16°)
        p.save()
        p.setPen(dessin.stylo('horizon', 1.4))
        p.setBrush(dessin.c('ciel', 0.25 + 0.55 * (1 - nuit)) if nuit < 1 else dessin.c('nuit', 0.95))
        p.drawEllipse(QPointF(cx, cy), rr, rr)
        p.restore()
        # étoiles de fond : elles tournent avec le temps sidéral
        tsl = astro.tsmg(me.jour_julien(k, self.heure.value()))
        lat = self.lat.value()
        if self.c_etoiles.isChecked() and nuit > 0.05:
            p.setPen(dessin.Qt.PenStyle.NoPen)
            for alpha, delta, mag in self.fond:
                az, h = astro.equatorial_vers_horizon(tsl - alpha, delta, lat)
                if h > 0:
                    q = vers_ecran(cx, cy, rr, az, h)
                    p.setBrush(dessin.c('etoile', nuit * max(0.25, 1.0 - (mag - 1.0) / 6.0)))
                    p.drawEllipse(q, max(0.7, 2.4 - 0.35 * mag), max(0.7, 2.4 - 0.35 * mag))
        # pôle céleste
        if abs(lat) > 1:
            qp = vers_ecran(cx, cy, rr, 0.0 if lat > 0 else 180.0, abs(lat))
            dessin.texte(p, qp.x(), qp.y(), '+', 'doux')
        # radiant
        az_r, h_r = self.radiant()
        qr = vers_ecran(cx, cy, rr, az_r, h_r) if h_r > -1 else None
        # traînées (et leur prolongement vers l'arrière, qui mène au radiant)
        for age, az0, h0, az1, h1 in self.filantes:
            a = max(0.0, 1.0 - age / DUREE_VIE)
            if self.c_prolonger.isChecked() and qr is not None:
                p.setPen(dessin.stylo('accent2', 0.9, 0.55 * a, pointille=True))
                self._arc(p, cx, cy, rr, me.arc(az_r, h_r, az0, h0, 24))
            p.setPen(dessin.stylo('accent1', 2.2, a))
            self._arc(p, cx, cy, rr, me.arc(az0, h0, az1, h1, 8))
        if qr is not None:
            p.setPen(dessin.stylo('accent3', 1.8))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(qr, 9.0, 9.0)
            dessin.texte(p, qr.x(), qr.y() + 20, tr('anim_meteorradiant_radiant'), 'accent3', fond=True)
        # points cardinaux (vus de dessous : est à gauche)
        for cle, az in (('n', 0.0), ('e', 90.0), ('s', 180.0), ('o', 270.0)):
            q = vers_ecran(cx, cy, rr + 10, az, 0.0)
            dessin.texte(p, q.x(), q.y(), tr('anim_meteorradiant_' + cle), 'doux')

    @staticmethod
    def _arc(p, cx, cy, rr, pts):
        qs = [vers_ecran(cx, cy, rr, az, h) for az, h in pts]
        p.drawPolyline(dessin.polygone([q.x() for q in qs], [q.y() for q in qs]))

    def _nuit(self, p, r):
        """Hauteur du radiant et taux horaire au fil de la nuit, avec le crépuscule (Soleil au-dessus de −18°)."""
        k = self.essaim.currentData()
        lat, m = self.lat.value(), self.mlim.value()
        zhr = me.ESSAIMS[k][5]
        ax = Axes(r, 18.0, 30.0, 0.0, 90.0, marges=(36, 8, 10, 30)).avec(p)
        heures = [18.0 + 0.1 * i for i in range(121)]
        hs = [me.hauteur_soleil(k, h, lat) for h in heures]
        # crépuscule et jour en grisé
        p.save()
        p.setPen(dessin.Qt.PenStyle.NoPen)
        for i in range(len(heures) - 1):
            if hs[i] > -18.0:
                p.setBrush(dessin.c('ciel', 0.35 if hs[i] < 0 else 0.6))
                p.drawRect(QRectF(ax.px(heures[i]), ax.r.top(), ax.px(heures[i + 1]) - ax.px(heures[i]) + 0.5,
                                  ax.r.height()))
        p.restore()
        ax.fond(p, tr('anim_meteorradiant_axe_heure'), tr('anim_meteorradiant_axe_hauteur'),
                fmt_x=lambda v: '%d h' % (int(round(v)) % 24))
        hr = [me.hauteur_radiant(k, h, lat)[1] for h in heures]
        ax.courbe(list(zip(heures, [max(0.0, x) for x in hr])), 'accent3', 2.0)
        taux = [me.taux_horaire(k, x, m) for x in hr]
        ax.courbe(list(zip(heures, [90.0 * t / zhr for t in taux])), 'accent1', 2.0, pointille=True)
        ax.verticale(self.heure.value(), 'texte', 1.2, pointille=False)
        dessin.police(p, 0.85)
        for i, (cle, col) in enumerate((('anim_meteorradiant_leg_hauteur', 'accent3'), ('anim_meteorradiant_leg_taux', 'accent1'),
                                        ('anim_meteorradiant_leg_grise', 'doux'))):
            dessin.texte(p, ax.r.left() + 6, ax.r.top() + 10 + 15 * i, tr(cle, zhr=nombre(zhr, 0)), col, centre=False,
                         fond=True)
        dessin.police(p, 1 / 0.85)
