"""Seasons Simulator (NAAP) : géométrie de la Terre et du Soleil au fil de l'année.  Vue orbitale (axe de la
Terre fixe dans l'espace), Terre vue de côté ou depuis le Soleil (point subsolaire, latitude de l'observateur),
et, pour l'observateur, l'angle des rayons à midi ou l'étalement d'un faisceau sur le sol."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin
from ..maintenant import heure_solaire
from ..base import Animation, angle, date_du_jour, duree_hm, heures_minutes, nombre

ANNEE = 2026


def etat(jour: float, lat: float) -> dict:
    s = astro.soleil_jour(ANNEE, jour + 0.5)                        # à midi
    h_midi = astro.hauteur_culmination(s['delta'], lat)
    return {'soleil': s, 'h_midi': h_midi, 'duree': astro.duree_du_jour_h(s['delta'], lat, -0.833),
            'etalement': 1.0 / math.sin(math.radians(h_midi)) if h_midi > 0.5 else math.inf,
            'eps': astro.obliquite_moyenne(astro.jj_jour_de_l_annee(ANNEE, jour))}


class Saisons(Animation):
    ID = 'eclipticsimulator'
    JOURS_PAR_S = 20.0

    TEMPS = ('jour',)
    HEURE_SOLAIRE = True

    def maintenant(self, m):
        """« Maintenant » : date et heure de l'appareil (maintenant.py)."""
        j, h = heure_solaire(m.i, m.lon)
        self.poser(self.jour, j)
        if m.lat is not None:
            self.poser(self.lat, m.lat)

    def construire(self):
        self.orbite = self.vue(270.0, 30.0, 0.0, 89.0)
        self.jour = self.curseur('jour', 0.0, 364.0, 40.0, dec=0, cle_texte='anim_c_jour')
        self.lat = self.curseur('latitude', -90.0, 90.0, 10.0, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.vue_terre = self.choix('vue_terre', [('anim_eclipticsimulator_cote', 'cote'),
                                                  ('anim_eclipticsimulator_soleil', 'soleil')], 'cote')
        self.observ = self.choix('observateur', [('anim_eclipticsimulator_angle', 'angle'),
                                                 ('anim_eclipticsimulator_faisceau', 'faisceau')], 'angle')
        self.c_subsolaire = self.coche('subsolaire', True)
        self.c_etiquettes = self.coche('etiquettes', False)
        self._t = None

    def avancer(self, dt):
        self.jour.setValue((self.jour.value() + dt * self.JOURS_PAR_S) % 365.0)

    def valeurs(self):
        e = etat(self.jour.value(), self.lat.value())
        s = e['soleil']
        out = [(tr('anim_c_date'), date_du_jour(self.jour.value())), (tr('anim_c_dec'), angle(s['delta'])),
               (tr('anim_c_ra'), heures_minutes(s['alpha'] / 15.0)),
               (tr('anim_eclipticsimulator_h_midi'), angle(e['h_midi'])),
               (tr('anim_sunmotions_duree'), duree_hm(e['duree']))]
        if math.isfinite(e['etalement']):
            out.append((tr('anim_eclipticsimulator_etalement'), '× %s' % nombre(e['etalement'], 2)))
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        e = etat(self.jour.value(), self.lat.value())
        z = dessin.zones_principale(rect, 2)
        self._orbite(p, dessin.cadre(p, z[0], tr('anim_eclipticsimulator_vue_orbite')), e)
        self._terre(p, dessin.cadre(p, z[1], tr('anim_eclipticsimulator_vue_terre')), e)
        titre = 'anim_eclipticsimulator_vue_angle' if self.observ.currentData() == 'angle' else \
            'anim_eclipticsimulator_vue_faisceau'
        self._observateur(p, dessin.cadre(p, z[2], tr(titre)), e)

    def _orbite(self, p, r, e):
        """Repère écliptique (x = point vernal) ; la Terre est à la longitude λ☉ + 180°."""
        self.zone_rotative(r, self.orbite)
        ray = min(r.width(), r.height()) * 0.42
        cx, cy = r.center().x(), r.center().y()
        pe = dessin.Peintre3D(p, self.orbite, cx, cy, ray)
        pe.plan('sphere', 0.35, bord='grille')
        pe.courbe(dessin.cercle((0, 0, 1)), 'grille', 1.2, arriere='normal', profondeur=False)
        lam = e['soleil']['lambda']
        terre = np.array(astro.vecteur_horizon(-(lam + 180.0), 0.0))     # (cos λ, sin λ, 0)
        if self.c_etiquettes.isChecked():
            for cle, l in (('anim_eclipticsimulator_mars', 0), ('anim_eclipticsimulator_juin', 90),
                           ('anim_eclipticsimulator_sept', 180), ('anim_eclipticsimulator_dec', 270)):
                pe.etiquette(np.array(astro.vecteur_horizon(-(l + 180.0), 0.0)) * 1.18, tr(cle), 'doux')
        xs, ys, _, _ = pe.ecran(np.zeros(3))
        dessin.disque(p, xs[0], ys[0], max(6.0, ray * 0.09), 'soleil')
        pe.segment(np.zeros(3), terre * 0.88, 'soleil', 2.0, 0.8)
        # axe de la Terre fixe dans l'espace : le pôle nord céleste est en λ = 90°, β = 90° − ε
        eps = math.radians(e['eps'])
        axe = np.array([0.0, math.sin(eps), math.cos(eps)])
        xt, yt, _, _ = pe.ecran(terre)
        rt = max(5.0, ray * 0.07)
        dessin.disque(p, xt[0], yt[0], rt, 'terre')
        a0, a1 = terre - axe * 0.15, terre + axe * 0.15
        pe.segment(a0, a1, 'texte', 2.0)
        pe.etiquette(terre + axe * 0.2, tr('anim_pc_n'), 'doux')

    def _terre(self, p, r, e):
        """Terre vue de côté (le Soleil à gauche) ou depuis le Soleil ; latitude de l'observateur et point
        subsolaire (latitude δ)."""
        d = e['soleil']['delta']
        lat = self.lat.value()
        ray = min(r.width(), r.height()) * 0.36
        cx, cy = r.center().x(), r.center().y()
        de_cote = self.vue_terre.currentData() == 'cote'
        p.save()
        p.setClipRect(r)
        p.translate(cx, cy)
        dessin.disque(p, 0, 0, ray, 'terre')
        if de_cote:
            # moitié nuit à droite ; l'axe penche de δ par rapport à la verticale (vers le Soleil si δ > 0)
            p.setBrush(dessin.c('nuit', 0.65))
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.drawPie(QRectF(-ray, -ray, 2 * ray, 2 * ray), -90 * 16, 180 * 16)
            p.rotate(-d)
            for l, cle in ((0, 'equateur'), (23.44, 'grille'), (-23.44, 'grille'), (66.56, 'grille'),
                           (-66.56, 'grille')):
                y = -ray * math.sin(math.radians(l))
                x = ray * math.cos(math.radians(l))
                p.setPen(dessin.stylo(cle, 1.4 if l == 0 else 1.0))
                p.drawLine(QPointF(-x, y), QPointF(x, y))
            y = -ray * math.sin(math.radians(lat))
            x = ray * math.cos(math.radians(lat))
            p.setPen(dessin.stylo('accent3', 2.2))
            p.drawLine(QPointF(-x, y), QPointF(x, y))
            dessin.disque(p, -x, y, 5, 'accent3')
            p.setPen(dessin.stylo('texte', 2.0))
            p.drawLine(QPointF(0, -ray * 1.25), QPointF(0, ray * 1.25))
            dessin.texte(p, 0, -ray * 1.33, tr('anim_pc_n'), 'doux')
            p.rotate(d)
            if self.c_subsolaire.isChecked():
                dessin.disque(p, -ray, 0, 5, 'soleil', bord='fond')
            # rayons du Soleil : du bord du panneau jusqu'au limbe (le Soleil est loin à gauche), jamais au travers
            depart = max(-ray * 2.2, -(cx - r.left()) + 4)
            for k in (-0.6, -0.3, 0.0, 0.3, 0.6):
                limbe = -ray * math.sqrt(1 - k * k) - (7 if k == 0 and self.c_subsolaire.isChecked() else 2)
                if limbe - depart > 12:
                    dessin.fleche(p, depart, k * ray, limbe, k * ray, dessin.stylo('soleil', 1.4, 0.8), 6)
        else:
            # vue depuis le Soleil : parallèles projetés (ellipses écrasées selon δ), point subsolaire au centre
            sd, cd = math.sin(math.radians(d)), math.cos(math.radians(d))
            for l, cle in ((0, 'equateur'), (23.44, 'grille'), (-23.44, 'grille'), (66.56, 'grille'),
                           (-66.56, 'grille'), (lat, 'accent3')):
                t = np.linspace(-math.pi, math.pi, 121)
                cl, sl = math.cos(math.radians(l)), math.sin(math.radians(l))
                # point (cl cos t, cl sin t, sl) vu le long de l'axe x incliné : y_écran = sl cd − cl cos t sd
                xs = cl * np.sin(t)
                prof = cl * np.cos(t) * cd + sl * sd
                ys = -(sl * cd - cl * np.cos(t) * sd)
                vis = prof >= 0
                p.setPen(dessin.stylo(cle, 2.2 if cle == 'accent3' else 1.2))
                pts = [QPointF(ray * x, ray * y) for x, y, v in zip(xs, ys, vis) if v]
                if len(pts) > 1:
                    p.drawPolyline(QPolygonF(pts))
            yp = -ray * cd
            p.setPen(dessin.stylo('texte', 2.0))
            p.drawLine(QPointF(0, yp), QPointF(0, yp - ray * 0.25 * cd))
            if self.c_subsolaire.isChecked():
                dessin.disque(p, 0, 0, 5, 'soleil', bord='fond')
        p.restore()

    def _observateur(self, p, r, e):
        h = e['h_midi']
        cx, base = r.center().x(), r.bottom() - r.height() * 0.22
        larg = r.width() * 0.8
        p.save()
        p.setClipRect(r)
        p.setPen(dessin.stylo('horizon', 2.5))
        p.drawLine(QPointF(cx - larg / 2, base), QPointF(cx + larg / 2, base))
        if self.observ.currentData() == 'angle':
            lon = min(r.width(), r.height()) * 0.55
            hr = math.radians(max(h, 0.0))
            sens = -1 if self.lat.value() >= e['soleil']['delta'] else 1      # Soleil au sud (−) ou au nord
            x1 = cx + sens * lon * math.cos(hr)
            y1 = base - lon * math.sin(hr)
            if h > 0:
                dessin.fleche(p, x1, y1, cx, base, dessin.stylo('soleil', 2.5), 10)
                dessin.disque(p, x1, y1, 9, 'soleil')
            p.setPen(dessin.stylo('accent1', 1.5))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            rr = lon * 0.3
            debut = 180 if sens < 0 else 0
            p.drawArc(QRectF(cx - rr, base - rr, 2 * rr, 2 * rr), debut * 16, int(sens * max(h, 0) * 16))
            dessin.texte(p, cx + sens * rr * 1.5, base - 14, angle(h), 'accent1')
            dessin.texte(p, cx - larg / 2 + 10, base + 14, tr('anim_pc_s' if sens < 0 else 'anim_pc_n'), 'doux')
        else:
            w = min(r.width(), r.height()) * 0.18                              # largeur du faisceau
            et = e['etalement'] if math.isfinite(e['etalement']) else 50
            sol = min(larg, w * et)
            hr = math.radians(max(h, 1.0))
            dx, dy = math.cos(hr), math.sin(hr)
            hauteur = r.height() * 0.55
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c('soleil', 0.35))
            a = QPointF(cx - sol / 2, base)
            b = QPointF(cx + sol / 2, base)
            p.drawPolygon(QPolygonF([a, b, QPointF(b.x() - dx * hauteur, b.y() - dy * hauteur),
                                     QPointF(a.x() - dx * hauteur, a.y() - dy * hauteur)]))
            p.setPen(dessin.stylo('soleil', 3.0))
            p.drawLine(a, b)
            dessin.texte(p, cx, base + 16, tr('anim_eclipticsimulator_surface', x=nombre(et, 2)), 'texte')
        p.restore()
