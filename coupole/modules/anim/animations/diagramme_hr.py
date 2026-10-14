"""HR Explorer (NAAP) : le diagramme de Hertzsprung-Russell.  On déplace une étoile (température, luminosité) : son
rayon suit la loi de Stefan-Boltzmann R / R☉ = √(L / L☉) / (T / T☉)², comparé au Soleil.  Droites d'égal rayon,
séquence principale et autres classes de luminosité, et les étoiles les plus proches ou les plus brillantes du ciel
(données de l'original, placées d'après leur type spectral et leur magnitude absolue), en couleur vraie (corps noir
→ CIE 1931 → sRGB) avec leur fiche au survol.  T☉ = 5 772 K (l'original prenait 5 800 K)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPolygonF

from ....core.i18n import tr
from .. import dessin, hr
from ..base import Animation, nombre
from ..couleur_etoile import couleur_etoile
from ..donnees_etoiles import BRILLANTES, COMMUNES, PROCHES
from ..etoiles_reelles import reelle

LOG_T = (3.3617, 4.6021)
LOG_L = (-4.0, 6.0)
GROUPES = ('aucune', 'proches', 'brillantes', 'les_deux', 'communes')
RAYONS = (1e-4, 1e-3, 1e-2, 0.1, 1.0, 10.0, 100.0, 1000.0)


class DiagrammeHR(Animation):
    ID = 'hrexplorer'
    ANIMEE = False
    FICHES = True

    def construire(self):
        self.t = self.curseur('temperature', 2300.0, 40000.0, 5800.0, dec=0, unite='K', log=True)
        self.l = self.curseur('luminosite', 1e-4, 1e6, 1.0, dec=4, unite='L☉', log=True)
        self.groupe = self.choix('groupe', [('anim_hrexplorer_g_' + g, g) for g in GROUPES], 'aucune')
        self.c_sp = self.coche('sequence', True)
        self.c_classes = self.coche('classes', False)
        self.c_rayons = self.coche('rayons', True)
        self.c_couleur = self.coche('couleur_t', True)
        self._graphe = None

    def rayon(self) -> float:
        return hr.rayon_solaire(self.l.value(), self.t.value())

    def valeurs(self):
        r = self.rayon()
        return [(tr('anim_hrexplorer_temperature'), '%s K' % nombre(self.t.value(), 0)),
                (tr('anim_hrexplorer_luminosite'), '%s L☉' % nombre(self.l.value(), 4 if self.l.value() < 1 else 1)),
                (tr('anim_hrexplorer_rayon'), '%s R☉' % nombre(r, 4 if r < 0.1 else 2)),
                (tr('anim_hrexplorer_formule'), 'R / R☉ = √(L / L☉) / (T / T☉)²')]

    def presser(self, pos, bouton):
        if self._graphe is not None and self._graphe[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        _, x0, x1, y0, y1 = self._graphe
        fx = max(0.0, min(1.0, (x1 - pos.x()) / (x1 - x0)))
        fy = max(0.0, min(1.0, (y1 - pos.y()) / (y1 - y0)))
        self.t.setValue(10 ** (LOG_T[0] + fx * (LOG_T[1] - LOG_T[0])))
        self.l.setValue(10 ** (LOG_L[0] + fy * (LOG_L[1] - LOG_L[0])))

    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.68) if rect.width() > rect.height() * 1.1 else dessin.zones(rect, 2, 10)
        self._diagramme(p, dessin.cadre(p, z[0], tr('anim_hrexplorer_diagramme')))
        self._comparaison(p, dessin.cadre(p, z[1], tr('anim_hrexplorer_comparaison')))

    def _diagramme(self, p, r):
        x0, x1, y0, y1 = r.x() + 44, r.right() - 8, r.y() + 4, r.bottom() - 30
        self._graphe = (QRectF(r), x0, x1, y0, y1)

        def xy(lt, ll):
            return QPointF(x1 - (x1 - x0) * (lt - LOG_T[0]) / (LOG_T[1] - LOG_T[0]),
                           y1 - (y1 - y0) * (ll - LOG_L[0]) / (LOG_L[1] - LOG_L[0]))

        p.save()
        p.setClipRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        if self.c_rayons.isChecked():                         # droites d'égal rayon : log L = 2 log R + 4 log(T/T☉)
            for rr in RAYONS:
                a = xy(LOG_T[0], 2 * math.log10(rr) + 4 * (LOG_T[0] - math.log10(hr.T_SOLEIL)))
                b = xy(LOG_T[1], 2 * math.log10(rr) + 4 * (LOG_T[1] - math.log10(hr.T_SOLEIL)))
                p.setPen(dessin.stylo('horizon', 1.0, 0.5, pointille=True))
                p.drawLine(a, b)
        classes = ([1, 2, 3, 4] if self.c_classes.isChecked() else []) + ([5] if self.c_sp.isChecked() else [])
        for n in classes:
            a, b = hr.CLASSES[n]
            p.setPen(dessin.stylo('arc2' if n == 5 else 'arc1', 2.0 if n == 5 else 1.2, 0.85))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawPolyline(QPolygonF([xy(a + (b - a) * i / 60, hr.log_lum_classe(a + (b - a) * i / 60, n))
                                      for i in range(61)]))
        g = self.groupe.currentData()
        couches = {'aucune': (),
                   'proches': ((PROCHES, 'accent2', 'proches'), (COMMUNES, 'accent3', 'communes')),
                   'brillantes': ((BRILLANTES, 'accent1', 'brillantes'), (COMMUNES, 'accent3', 'communes')),
                   'les_deux': ((PROCHES, 'accent2', 'proches'), (BRILLANTES, 'accent1', 'brillantes'),
                                (COMMUNES, 'accent3', 'communes')),
                   'communes': ((COMMUNES, 'accent3', 'communes'),)}[g]
        vraie = self.c_couleur.isChecked()
        for etoiles, cle, groupe in couches:
            for nom, t, mv, _ in etoiles:
                lt, ll = hr.position_hr(t, mv)
                q = xy(lt, ll)
                # couleur = température (corps noir → CIE 1931) avec le contour du groupe, ou couleur du groupe
                if vraie:
                    dessin.disque(p, q.x(), q.y(), 3.0, QColor(*couleur_etoile(10 ** lt)), cle)
                else:
                    dessin.disque(p, q.x(), q.y(), 2.6, cle)
                f = reelle('hrexplorer:' + groupe, nom)
                if f and x0 <= q.x() <= x1 and y0 <= q.y() <= y1:
                    self.survolable(p, f['fiche'], q.x(), q.y(), 4, mv)
        p.restore()
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        dessin.police(p, 0.72)
        for ll in range(-4, 7, 2):
            q = xy(LOG_T[0], ll)
            dessin.texte(p, x0 - 20, q.y(), nombre(10.0 ** ll, max(0, -ll)) if ll < 3 else '10%s' % str(ll).translate(
                str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')), 'doux')
        for t in (2300, 5000, 10000, 20000, 40000):
            q = xy(math.log10(t), LOG_L[0])
            dessin.texte(p, q.x(), y1 + 11, nombre(t, 0), 'doux')
        dessin.texte(p, (x0 + x1) / 2, y1 + 23, tr('anim_hrexplorer_axe_t'), 'doux')
        if self.c_rayons.isChecked():
            for rr in RAYONS:
                ll = 2 * math.log10(rr) + 4 * (3.45 - math.log10(hr.T_SOLEIL))
                q = xy(3.45, ll)
                if y0 < q.y() < y1:
                    dessin.texte(p, q.x(), q.y(), '%s R☉' % nombre(rr, max(0, -int(math.floor(math.log10(rr))))),
                                 'horizon', fond=True)
        dessin.police(p, 1 / 0.72)
        q = xy(math.log10(self.t.value()), math.log10(self.l.value()))
        p.setPen(dessin.stylo('accent3', 2.0))
        p.drawLine(QPointF(q.x() - 9, q.y()), QPointF(q.x() + 9, q.y()))
        p.drawLine(QPointF(q.x(), q.y() - 9), QPointF(q.x(), q.y() + 9))

    def _comparaison(self, p, r):
        """Le Soleil et l'étoile côte à côte : même échelle tant que possible, sinon l'échelle est indiquée."""
        rr = self.rayon()
        cy = r.center().y()
        place = min(r.width() * 0.17, r.height() * 0.38)
        k = place / max(1.0, rr)                              # pixels par R☉
        rs, re = max(1.5, k), max(1.5, k * rr)
        xs, xe = r.x() + r.width() * 0.26, r.x() + r.width() * 0.72
        dessin.disque(p, xs, cy, rs, QColor(*couleur_etoile(hr.T_SOLEIL)), 'grille')
        dessin.disque(p, xe, cy, re, QColor(*couleur_etoile(self.t.value())), 'grille')
        dessin.texte(p, xs, r.bottom() - 26, tr('anim_stellarlum_soleil'), 'doux')
        dessin.texte(p, xe, r.bottom() - 26, '%s R☉' % nombre(rr, 4 if rr < 0.1 else 2), 'texte')
        if k * 1.0 < 1.5 or k * rr < 1.5:
            dessin.texte(p, r.center().x(), r.bottom() - 8, tr('anim_hrexplorer_hors_echelle'), 'doux')
