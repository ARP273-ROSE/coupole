"""L'atmosphère terrestre : épaisseur traversée, absorption et réfraction (0.8.0, propre à Coupole).

Thème « Télescopes » : l'atmosphère est le premier « instrument » que traverse la lumière ; elle explique pourquoi on
observe haut sur l'horizon, en altitude, ou depuis l'espace.  Quatre vues :
1. **Épaisseur traversée** : coupe de la Terre et de l'atmosphère (couches, échelle de hauteur 8 km, épaisseur
   agrandie et dite), trajet de la lumière qui s'allonge vers l'horizon ; masse d'air par sec z, Kasten & Young
   (1989), Pickering (2002) et coquille sphérique.
2. **Extinction et rougissement** : épaisseur optique Rayleigh (∝ λ⁻⁴), aérosols (Ångström) et ozone ; Δm = k X dans
   les bandes U B V R I ; couleur du Soleil transmis selon sa hauteur.
3. **Fenêtres atmosphériques** : transmission au zénith de 0,3 à 30 µm (modèle de ciel de l'ESO, Paranal) et schéma
   des domaines γ, X, UV, infrarouge lointain, submillimétrique, radio, ionosphère.
4. **Réfraction** : hauteur apparente et vraie (Bennett, Sæmundsson), aplatissement du Soleil à l'échelle, lever
   avancé et coucher retardé, dispersion (Ciddor 1996), pression et température ; rayon courbé (option exagérée).
Calculs dans ``atmosphere_calc.py`` (mêmes formules dans Coupole Web)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPainterPath

from ....core.i18n import tr
from .. import atmosphere_calc as A
from .. import dessin, lumiere
from ..base import Animation, angle, nombre
from ..graphe import Axes

VUES = ('epaisseur', 'extinction', 'fenetres', 'refraction')
COULEURS_BANDES = {'U': 'arc1', 'B': 'accent2', 'V': 'horizon', 'R': 'accent3', 'I': 'doux'}


def arcmin(deg: float) -> str:
    return '%s′' % nombre(deg * 60, 1)


class Atmosphere(Animation):
    ID = 'earthatmosphere'
    ANIMEE = False

    def construire(self):
        self.vue_c = self.choix('vue', [('anim_earthatmosphere_v_' + v, v) for v in VUES], 'epaisseur')
        self.h = self.curseur('hauteur', -1.0, 90.0, 20.0, dec=1, unite='°')
        self.pression = self.curseur('pression', 500.0, 1050.0, 1010.0, dec=0, unite='hPa')
        self.temperature = self.curseur('temperature', -30.0, 40.0, 10.0, dec=0, unite='°C')
        self.beta = self.curseur('aerosols', 0.0, 0.3, 0.05, dec=2)
        self.latitude = self.curseur('latitude', 0.0, 65.0, 48.8, dec=1, unite='°')
        self.exagerer = self.coche('exagerer', False)
        self.vue_c.currentIndexChanged.connect(self._reglages_utiles)
        self._reglages_utiles()

    def _reglages_utiles(self, *_):
        """Seuls les réglages qui changent la vue affichée sont montrés (température et latitude : réfraction)."""
        v = self.vue_c.currentData()
        self.pression.setVisible(v != 'fenetres')
        self.temperature.setVisible(v in ('epaisseur', 'refraction'))
        self.beta.setVisible(v == 'extinction')
        self.latitude.setVisible(v == 'refraction')
        self.exagerer.setVisible(v == 'refraction')

    def _p(self):
        return self.pression.value(), self.temperature.value()

    # ------------------------------------------------------------------ valeurs
    def valeurs(self):
        h = self.h.value()
        P, T = self._p()
        v = self.vue_c.currentData()
        hv = max(h, 0.0)
        X = A.masse_air_kasten_young(hv)
        out = [(tr('anim_earthatmosphere_val_x_secz'), nombre(A.masse_air_secz(hv), 3) if hv >= 1 else '—'),
               (tr('anim_earthatmosphere_val_x_ky'), nombre(X, 3)),
               (tr('anim_earthatmosphere_val_x_pickering'), nombre(A.masse_air_pickering(hv), 3)),
               (tr('anim_earthatmosphere_val_chemin'), '%s km' % nombre(A.chemin_sphere_km(hv), 1))]
        if v in ('extinction', 'fenetres'):
            for b in ('B', 'V'):
                k = A.k_bande(A.BANDES[b], P, self.beta.value())
                out.append((tr('anim_earthatmosphere_val_dm', b=b), '%s mag (k = %s)' % (nombre(k * X, 2),
                                                                                          nombre(k, 3))))
        if v == 'refraction' or v == 'epaisseur':
            r = A.refraction_vraie(h, P, T)
            out.append((tr('anim_earthatmosphere_val_refraction'), arcmin(r)))
            out.append((tr('anim_earthatmosphere_val_apparente'), angle(h + r)))
        if v == 'refraction':
            ap = A.aplatissement(0.0, 0.2666, P, T)
            out.append((tr('anim_earthatmosphere_val_aplatissement'), nombre(ap['rapport'], 3)))
            out.append((tr('anim_earthatmosphere_val_avance'), '%s min' % nombre(A.avance_lever_min(
                self.latitude.value()), 1)))
            d = (A.refraction_lambda(h, 0.45, P, T) - A.refraction_lambda(h, 0.65, P, T)) * 3600
            out.append((tr('anim_earthatmosphere_val_dispersion'), '%s″' % nombre(d, 2)))
        return out

    # ------------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        {'epaisseur': self._epaisseur, 'extinction': self._extinction, 'fenetres': self._fenetres,
         'refraction': self._refraction}[self.vue_c.currentData()](p, rect)

    def _epaisseur(self, p, rect):
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.62)
        bas = QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height())
        r = dessin.cadre(p, haut, tr('anim_earthatmosphere_t_coupe'))
        h = max(self.h.value(), 0.0)
        agr = 25.0                                        # épaisseur de l'atmosphère agrandie (dite sur le dessin)
        R = A.R_TERRE_KM
        # cadre : de l'observateur au bord de l'atmosphère dans la direction la plus longue (horizon)
        Ld = A.chemin_sphere_km(0.0, A.H_ECHELLE_KM * agr)
        k = min(r.width() * 0.47 / Ld, r.height() * 0.8 / (A.H_ECHELLE_KM * agr * 2.4))
        ox, oy = r.center().x(), r.bottom() - 18
        cy = oy + R * k                                   # centre de la Terre (hors cadre)
        p.save()
        p.setClipRect(r)
        couches = (('anim_earthatmosphere_c_meso', 85.0, 'nuit'), ('anim_earthatmosphere_c_strato', 50.0, 'arc1'),
                   ('anim_earthatmosphere_c_tropo', 12.0, 'accent2'))
        for cle, z, couleur in couches:
            zz = z / 85.0 * A.H_ECHELLE_KM * agr * 2.2
            p.setPen(dessin.stylo('doux', 0.8, 0.6))
            p.setBrush(dessin.c(couleur, 0.10))
            rr = (R + zz) * k
            p.drawEllipse(QPointF(ox, cy), rr, rr)
        # couche « homogène » d'épaisseur H (échelle de hauteur), sur laquelle on mesure le trajet
        p.setPen(dessin.stylo('accent3', 1.4, pointille=True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        rh = (R + A.H_ECHELLE_KM * agr) * k
        p.drawEllipse(QPointF(ox, cy), rh, rh)
        self._couche_y = cy - rh
        p.setPen(dessin.stylo('horizon', 1.5))
        p.setBrush(dessin.c('horizon', 0.35))
        p.drawEllipse(QPointF(ox, cy), R * k, R * k)
        # trajet de la lumière dans la couche homogène
        L = A.chemin_sphere_km(h, A.H_ECHELLE_KM * agr)
        a = math.radians(h)
        ex, ey = ox - L * k * math.cos(a), oy - L * k * math.sin(a)
        p.setPen(dessin.stylo('soleil', 3.0))
        p.drawLine(QPointF(ex, ey), QPointF(ox, oy))
        p.setPen(dessin.stylo('soleil', 1.2, 0.6, pointille=True))
        p.drawLine(QPointF(ex, ey), QPointF(ex - 60 * math.cos(a), ey - 60 * math.sin(a)))
        p.restore()
        dessin.disque(p, ox, oy, 4, 'texte')
        dessin.etiquette(p, (ex + ox) / 2, (ey + oy) / 2, tr('anim_earthatmosphere_e_trajet', l=nombre(
            A.chemin_sphere_km(h), 0), x=nombre(A.masse_air_sphere(h), 2)), 'soleil')
        for cle, z, couleur in couches:
            zz = z / 85.0 * A.H_ECHELLE_KM * agr * 2.2
            dessin.etiquette(p, r.left() + 70, oy - zz * k, tr(cle), 'doux')
        dessin.etiquette(p, r.right() - 160, self._couche_y + 6, tr('anim_earthatmosphere_e_couche'), 'accent3')
        dessin.police(p, 0.8)
        dessin.texte(p, r.right() - 150, r.top() + 16, tr('anim_earthatmosphere_e_agrandie', k=int(agr)), 'doux')
        dessin.police(p, 1 / 0.8)
        # masse d'air selon la hauteur, quatre modèles
        r2 = dessin.cadre(p, bas, tr('anim_earthatmosphere_t_masse'))
        ax = Axes(r2, 0.0, 90.0, 0.0, 40.0, marges=(40, 6, 12, 22)).avec(p)
        ax.fond(p, '%s (°)' % tr('anim_earthatmosphere_hauteur'), 'X', n_x=9, n_y=4)
        hs = [i * 0.25 for i in range(1, 361)]
        for f, cle, ep in ((A.masse_air_secz, 'doux', 1.2), (A.masse_air_kasten_young, 'accent1', 2.2),
                           (A.masse_air_pickering, 'accent2', 1.4), (A.masse_air_sphere, 'accent3', 1.4)):
            ax.courbe([(x, min(40.0, f(x))) for x in hs], cle, ep)
        ax.verticale(h, 'soleil', etiquette='X = %s' % nombre(A.masse_air_kasten_young(h), 2))
        dessin.police(p, 0.8)
        y = r2.top() + 14
        for cle, nom in (('doux', 'sec z'), ('accent1', 'Kasten & Young'), ('accent2', 'Pickering'),
                         ('accent3', tr('anim_earthatmosphere_sphere'))):
            dessin.texte(p, ax.r.right() - 70, y, nom, cle)
            y += 14
        dessin.police(p, 1 / 0.8)

    def _extinction(self, p, rect):
        P = self.pression.value()
        beta = self.beta.value()
        h = max(self.h.value(), 0.0)
        X = A.masse_air_kasten_young(h)
        gauche = QRectF(rect.x(), rect.y(), rect.width() * 0.66, rect.height())
        droite = QRectF(gauche.right(), rect.y(), rect.width() - gauche.width(), rect.height())
        r = dessin.cadre(p, gauche, tr('anim_earthatmosphere_t_tau'))
        ax = Axes(r, 0.3, 1.0, 0.0, 1.2 * min(max(X, 1.0), 6.0), marges=(40, 6, 12, 22)).avec(p)
        ax.bande_visible(0.15, echelle=0.001)
        ax.fond(p, 'λ (µm)', 'τ', n_x=7, n_y=4)
        # le long de la visée : τ × X (masse d'air à la hauteur choisie)
        ax.courbe([(l, X * A.tau_total(l, P, beta)) for l in [0.3 + i * 0.005 for i in range(141)]], 'accent1', 1.6,
                  pointille=True)
        ls = [0.3 + i * 0.005 for i in range(141)]
        ax.courbe([(l, A.tau_rayleigh(l, P)) for l in ls], 'accent2', 1.4)
        ax.courbe([(l, A.tau_aerosols(l, beta)) for l in ls], 'doux', 1.4)
        ax.courbe([(l, A.tau_ozone(l)) for l in ls], 'arc1', 1.4)
        ax.courbe([(l, A.tau_total(l, P, beta)) for l in ls], 'accent1', 2.4)
        for b, l in A.BANDES.items():
            ax.verticale(l, COULEURS_BANDES[b], etiquette='%s : k = %s' % (b, nombre(A.k_bande(l, P, beta), 2)))
        dessin.police(p, 0.8)
        yy = r.top() + r.height() * 0.35
        for cle, nom in (('accent1', tr('anim_earthatmosphere_total')),
                         ('accent1', '- - ' + tr('anim_earthatmosphere_visee', x=nombre(X, 2))), ('accent2', 'Rayleigh ∝ λ⁻⁴'),
                         ('doux', tr('anim_earthatmosphere_aerosols')), ('arc1', tr('anim_earthatmosphere_ozone'))):
            dessin.texte(p, ax.r.right() - 130, yy, nom, cle)
            yy += 14
        dessin.police(p, 1 / 0.8)
        # Soleil transmis à la hauteur choisie
        r2 = dessin.cadre(p, droite, tr('anim_earthatmosphere_t_soleil'))
        def flux(w, X=X):
            return lumiere.valeur('soleil', w, 'v') * math.exp(-X * A.tau_total(w / 1000.0, P, beta))
        x0, y0, z0 = lumiere.xyz(lambda w: lumiere.valeur('soleil', w, 'v'))
        x, y, z = lumiere.xyz(flux)
        rgb = lumiere.rgb_de_xyz(x / max(y, 1e-12), 1.0, z / max(y, 1e-12))
        cx, cy = r2.center().x(), r2.top() + r2.height() * 0.38
        rr = min(r2.width(), r2.height()) * 0.22
        p.setPen(dessin.stylo('doux', 1.0))
        p.setBrush(QColor(*rgb))
        p.drawEllipse(QPointF(cx, cy), rr, rr)
        dessin.etiquette(p, cx, cy + rr + 14, tr('anim_earthatmosphere_e_transmis', t=nombre(100 * y / y0, 0),
                                                 x=nombre(X, 2)), 'texte')
        dessin.etiquette(p, cx, r2.bottom() - 22, tr('anim_earthatmosphere_e_rougit'), 'doux')

    def _fenetres(self, p, rect):
        d = A.transmission_eso()
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.42)
        bas = QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height())
        r = dessin.cadre(p, haut, tr('anim_earthatmosphere_t_fenetres'))
        ax = Axes(r, 1e-6, 1e9, 0.0, 1.05, xlog=True, marges=(40, 8, 30, 22)).avec(p)
        ax.fond(p, 'λ (µm)', '', n_y=2)
        # schéma (hors du modèle de l'ESO) puis données de l'ESO
        dessin.police(p, 0.75)
        for cle, a, b, tt in A.DOMAINES:
            ax.remplir([(a, tt), (b, tt)], 'doux', 0.35)
            dessin.etiquette(p, ax.px(math.sqrt(a * b)), ax.r.top() + 12, tr('anim_earthatmosphere_d_' + cle), 'doux')
        dessin.police(p, 1 / 0.75)
        pts = list(zip(d['lambda_um'], d['total']))
        ax.remplir(pts, 'accent1', 0.5)
        ax.bande_visible(0.25, echelle=0.001)
        dessin.etiquette(p, ax.px(3e5), ax.py(0.5), tr('anim_earthatmosphere_e_radio'), 'texte')
        dessin.etiquette(p, ax.px(1e-3), ax.py(0.5), tr('anim_earthatmosphere_e_espace'), 'texte')
        # zoom : du proche UV à l'infrarouge moyen, avec les bandes photométriques et la masse d'air choisie
        r2 = dessin.cadre(p, bas, tr('anim_earthatmosphere_t_fenetres_zoom'))
        ax2 = Axes(r2, 0.3, 30.0, 0.0, 1.05, xlog=True, marges=(40, 8, 30, 22)).avec(p)
        ax2.bande_visible(0.18, echelle=0.001)
        ax2.fond(p, 'λ (µm)', tr('anim_earthatmosphere_transmission'), n_y=4)
        X = A.masse_air_kasten_young(max(self.h.value(), 0.0))
        ax2.remplir(pts, 'accent1', 0.3)
        ax2.courbe(pts, 'accent1', 1.2)
        ax2.courbe([(l, tt ** X) for l, tt in pts], 'accent3', 1.0)
        for nom, l in (('U', 0.36), ('V', 0.55), ('I', 0.8), ('J', 1.25), ('H', 1.65), ('K', 2.2), ('L', 3.5),
                       ('M', 4.8), ('N', 10.0), ('Q', 20.0)):
            ax2.verticale(l, 'horizon', epaisseur=0.8, etiquette=nom)
        for nom, l in (('H₂O', 1.4), ('H₂O', 1.9), ('H₂O', 6.3), ('CO₂', 15.0), ('O₃', 9.6), ('CO₂', 4.3)):
            dessin.etiquette(p, ax2.px(l), ax2.py(0.06), nom, 'accent2')
        dessin.police(p, 0.75)
        dessin.texte(p, ax2.r.right() - 120, ax2.r.top() + 28, tr('anim_earthatmosphere_e_x', x=nombre(X, 2)),
                     'accent3')
        dessin.texte(p, r2.center().x(), r2.bottom() - 6, tr('anim_earthatmosphere_source_eso'), 'doux')
        dessin.police(p, 1 / 0.75)

    def _refraction(self, p, rect):
        P, T = self._p()
        h = self.h.value()
        gauche = QRectF(rect.x(), rect.y(), rect.width() * 0.5, rect.height())
        droite = QRectF(gauche.right(), rect.y(), rect.width() - gauche.width(), rect.height())
        # rayon dans des couches d'indice décroissant (courbure exagérée sur demande)
        r = dessin.cadre(p, QRectF(gauche.x(), gauche.y(), gauche.width(), gauche.height() * 0.55),
                         tr('anim_earthatmosphere_t_rayon'))
        n_couches = 12
        ex = 40.0 if self.exagerer.isChecked() else 1.0
        ox, oy = r.left() + 30, r.bottom() - 16
        hauteur = r.height() - 40
        for i in range(n_couches):
            y = oy - hauteur * (i + 1) / n_couches
            p.setPen(dessin.stylo('doux', 0.6, 0.4))
            p.drawLine(QPointF(r.left() + 4, y), QPointF(r.right() - 4, y))
            p.fillRect(QRectF(r.left() + 4, y, r.width() - 8, hauteur / n_couches),
                       dessin.c('accent2', 0.25 * math.exp(-i / 4.0)))
        # tracé : réfraction cumulée répartie selon la densité (n − 1 ∝ e^(−z/H)) ; distances horizontales
        # ramenées à la largeur du cadre (les hauteurs restent celles des couches)
        R_tot = A.refraction_vraie(h, P, T) * ex
        ang = h + R_tot                                    # direction apparente à l'observateur
        xs, ys = [0.0], [0.0]
        for i in range(n_couches):
            part = (math.exp(-i / 4.0) - math.exp(-(i + 1) / 4.0)) / (1 - math.exp(-n_couches / 4.0))
            ang -= R_tot * part
            a = math.radians(max(ang, 0.2))
            xs.append(xs[-1] + (hauteur / n_couches) / math.tan(a))
            ys.append(ys[-1] + hauteur / n_couches)
        kx = 0.25                     # compression horizontale FIXE (× 4) : l'angle dessiné suit la hauteur
        path = QPainterPath(QPointF(ox, oy))
        for x_, y_ in zip(xs[1:], ys[1:]):
            path.lineTo(QPointF(ox + kx * x_, oy - y_))
        p.save()
        p.setClipRect(r)
        p.setPen(dessin.stylo('soleil', 2.2))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        a0 = math.radians(max(h + R_tot, 0.2))
        p.setPen(dessin.stylo('accent1', 1.2, pointille=True))
        L0 = 1.2 * hauteur / math.tan(a0)
        p.drawLine(QPointF(ox, oy), QPointF(ox + kx * L0, oy - 1.2 * hauteur))
        p.restore()
        dessin.etiquette(p, r.center().x(), r.bottom() - 6, tr('anim_earthatmosphere_e_comprime', k=nombre(1 / kx, 0)),
                         'doux')
        dessin.disque(p, ox, oy, 4, 'texte')
        dessin.etiquette(p, ox + 60, oy - 18, tr('anim_earthatmosphere_e_apparente'), 'accent1')
        if self.exagerer.isChecked():
            dessin.etiquette(p, r.right() - 90, r.top() + 14, tr('anim_earthatmosphere_e_exagere'), 'doux')
        # réfraction selon la hauteur
        r2 = dessin.cadre(p, QRectF(gauche.x(), gauche.y() + gauche.height() * 0.55, gauche.width(),
                                    gauche.height() * 0.45), tr('anim_earthatmosphere_t_refraction'))
        ax = Axes(r2, -1.0, 90.0, 0.0, 40.0, marges=(40, 6, 12, 22)).avec(p)
        ax.fond(p, '%s (°)' % tr('anim_earthatmosphere_hauteur'), '′', n_x=9, n_y=4)
        hs = [-1.0 + i * 0.25 for i in range(365)]
        ax.courbe([(x_, 60 * A.refraction_vraie(x_, P, T)) for x_ in hs], 'accent1', 2.0)
        ax.verticale(h, 'soleil', etiquette=arcmin(A.refraction_vraie(h, P, T)))
        # Soleil à la hauteur choisie, à l'échelle : la vue suit le Soleil, l'horizon sort du cadre s'il le faut
        r3 = dessin.cadre(p, droite, tr('anim_earthatmosphere_t_soleil_couchant'))
        ap = A.aplatissement(h, 0.2666, P, T)
        kk = r3.height() * 0.35 / 0.6                      # pixels par degré
        cx = r3.center().x()
        yc = min(max(r3.top() + r3.height() * 0.62 - h * kk, r3.top() + r3.height() * 0.40),
                 r3.top() + r3.height() * 0.68)            # centre vrai du Soleil, gardé dans le cadre
        hy = yc + h * kk                                   # ordonnée de l'horizon (hauteur 0)
        p.save()
        p.setClipRect(r3)
        if hy < r3.bottom() - 50:
            p.setPen(dessin.stylo('horizon', 1.5))
            p.drawLine(QPointF(r3.left() + 8, hy), QPointF(r3.right() - 8, hy))
        # disque vrai (pointillés) et apparent (forme exacte point par point)
        p.setPen(dessin.stylo('doux', 1.0, pointille=True))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, yc), 0.2666 * kk, 0.2666 * kk)
        forme = QPainterPath()
        for i in range(73):
            t = 2 * math.pi * i / 72
            hv = h + 0.2666 * math.sin(t)
            ha = hv + A.refraction_vraie(hv, P, T)
            pt = QPointF(cx + 0.2666 * kk * math.cos(t), hy - ha * kk)
            forme.moveTo(pt) if i == 0 else forme.lineTo(pt)
        p.setPen(dessin.stylo('soleil', 1.5))
        p.setBrush(dessin.c('soleil', 0.8))
        p.drawPath(forme)
        p.restore()
        if hy >= r3.bottom() - 50:
            dessin.etiquette(p, cx, r3.bottom() - 56, tr('anim_earthatmosphere_e_horizon_bas', h=nombre(h, 1)), 'doux')
        dessin.etiquette(p, cx, hy - (ap['haut_apparent'] + 0.05) * kk, tr(
            'anim_earthatmosphere_e_aplati', r=nombre(ap['rapport'], 3)), 'texte')
        dessin.etiquette(p, cx, yc + 0.35 * kk, tr('anim_earthatmosphere_e_vrai'), 'doux')
        dessin.etiquette(p, cx, r3.bottom() - 34, tr('anim_earthatmosphere_e_avance', t=nombre(
            A.avance_lever_min(self.latitude.value()), 1), lat=nombre(self.latitude.value(), 0)), 'texte')
        # dispersion : images bleue, verte, rouge d'une étoile à la hauteur choisie
        d = [(A.refraction_lambda(h, l, P, T) - A.refraction_lambda(h, 0.55, P, T)) * 3600 for l in (0.45, 0.55,
                                                                                                    0.65)]
        x0, y0 = r3.left() + 40, r3.top() + 80
        kd = min(6.0, 40.0 / max(abs(d[0]), abs(d[2]), 1e-9))
        for (cle, dd) in zip(('accent2', 'horizon', 'accent3'), d):
            dessin.disque(p, x0, y0 - dd * kd, 4, cle)
        dessin.etiquette(p, x0 + 12, y0, tr('anim_earthatmosphere_e_dispersion', d=nombre(d[0] - d[2], 2)), 'texte')
