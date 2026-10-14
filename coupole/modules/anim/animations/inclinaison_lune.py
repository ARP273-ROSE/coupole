"""Moon Inclination : l'orbite de la Lune est inclinée de 5,1° sur l'écliptique ; à la plupart des nouvelles et
pleines lunes, la Lune passe au-dessus ou au-dessous de l'alignement Soleil–Terre et il n'y a pas d'éclipse.  Les
éclipses n'arrivent que lorsque le Soleil est près de la ligne des nœuds : deux « saisons d'éclipses » par année
draconitique (346,62 jours).  Repère attaché aux nœuds : le Soleil y tourne en 346,62 jours, la Lune parcourt son
orbite en un mois draconitique (27,212 jours) ; leur combinaison redonne la lunaison de 29,53 jours.  Éclipse
possible quand la Lune passe dans l'ombre ou la pénombre (géométrie des cônes, distances moyennes)."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre

MOIS_DRACONITIQUE_J = 1.0 / (1.0 / astro.MOIS_SYNODIQUE_J + 1.0 / astro.ANNEE_DRACONITIQUE_J)   # 27,2122 j
R_T, R_L = astro.R_TERRE_KM, astro.R_LUNE_KM
_TERRE = astro.cones_ombre(astro.R_SOLEIL_KM, R_T, astro.UA_KM)
_LUNE = astro.cones_ombre(astro.R_SOLEIL_KM, R_L, astro.UA_KM - astro.D_LUNE_KM)
OMBRE_TERRE_KM = _TERRE['rayon_ombre'](astro.D_LUNE_KM)          # ≈ 4 600 km à la distance de la Lune
PENOMBRE_TERRE_KM = _TERRE['rayon_penombre'](astro.D_LUNE_KM)
PENOMBRE_LUNE_KM = _LUNE['rayon_penombre'](astro.D_LUNE_KM)       # pénombre de la Lune au niveau de la Terre


def geometrie(t: float, inclinaison: float = astro.INCLINAISON_LUNE) -> dict:
    """Configuration au jour t (t = 0 : nouvelle lune au nœud ascendant).  Rend la direction du Soleil s (degrés,
    depuis le nœud ascendant), l'argument de latitude F de la Lune, sa position (unité : distance Terre-Lune), sa
    latitude écliptique, l'élongation, et l'écart (km) de la Lune à l'axe Soleil-Terre côté Soleil ou côté nuit."""
    s = 360.0 * t / astro.ANNEE_DRACONITIQUE_J
    f = 360.0 * t / MOIS_DRACONITIQUE_J
    fr, ir = math.radians(f), math.radians(inclinaison)
    lune = np.array([math.cos(fr), math.sin(fr) * math.cos(ir), math.sin(fr) * math.sin(ir)])
    u = np.array([math.cos(math.radians(s)), math.sin(math.radians(s)), 0.0])
    axial = float(lune @ u)
    ecart = float(np.linalg.norm(lune - axial * u)) * astro.D_LUNE_KM
    beta = math.degrees(math.asin(lune[2]))
    elong = math.degrees(math.atan2(lune[1], lune[0])) - s
    return {'s': s % 360.0, 'F': f % 360.0, 'lune': lune, 'beta': beta, 'elongation': elong % 360.0,
            'axial': axial, 'ecart_km': ecart}


def eclipse(g: dict) -> str | None:
    """Type d'éclipse en cours ('soleil', 'lune_ombre', 'lune_penombre') d'après l'écart de la Lune à l'axe."""
    if g['axial'] > 0 and g['ecart_km'] < R_T + PENOMBRE_LUNE_KM:
        return 'soleil'
    if g['axial'] < 0:
        if g['ecart_km'] < OMBRE_TERRE_KM + R_L:
            return 'lune_ombre'
        if g['ecart_km'] < PENOMBRE_TERRE_KM + R_L:
            return 'lune_penombre'
    return None


class InclinaisonLune(Animation):
    ID = 'mooninc'
    JOURS_PAR_S = 2.5
    LECTURE_AU_DEPART = True

    def construire(self):
        self.vue3d = self.vue(235.0, 22.0, -60.0, 89.0)
        self.c_plan = self.coche('plan', True)
        self.c_orbite = self.coche('orbite', True)
        self.c_tailles = self.coche('tailles', False)
        self.etat_initial()

    def etat_initial(self):
        self.t = 0.0

    def avancer(self, dt):
        self.t += dt * self.JOURS_PAR_S

    def valeurs(self):
        g = geometrie(self.t)
        e = eclipse(g)
        sn = astro.mod180(g['s'])
        if abs(sn) > 90:
            sn = astro.mod180(sn + 180.0)
        return [(tr('anim_mooninc_jours'), nombre(self.t, 1)),
                (tr('anim_lunar_applet_nom_phase'), tr('anim_phase_' + astro.nom_de_phase(g['elongation']))),
                (tr('anim_mooninc_latitude'), angle(g['beta'], 2)),
                (tr('anim_mooninc_soleil_noeud'), angle(abs(sn), 1)),
                (tr('anim_mooninc_eclipse'), tr('anim_mooninc_e_' + (e or 'aucune')))]

    def dessiner(self, p, rect):
        haut = rect.height() * 0.80
        z = dessin.zones_principale(QRectF(rect.x(), rect.y(), rect.width(), haut), 1, 0.64)
        self._espace(p, dessin.cadre(p, z[0], tr('anim_mooninc_vue')))
        self._depuis_soleil(p, dessin.cadre(p, z[1], tr('anim_mooninc_depuis_soleil')))
        self._frise(p, dessin.cadre(p, QRectF(rect.x(), rect.y() + haut, rect.width(), rect.height() - haut)))

    def _espace(self, p, r):
        self.zone_rotative(r, self.vue3d)
        g = geometrie(self.t)
        cx, cy = r.center().x(), r.center().y()
        rr = min(r.width(), r.height()) * 0.40
        pe = dessin.Peintre3D(p, self.vue3d, cx, cy, rr)
        k = 3.0 if self.c_tailles.isChecked() else 1.0
        orbite = dessin.cercle((0.0, -math.sin(math.radians(astro.INCLINAISON_LUNE)),
                                math.cos(math.radians(astro.INCLINAISON_LUNE))), 90.0, 181, origine=(1, 0, 0))
        s = math.radians(g['s'])
        u = np.array([math.cos(s), math.sin(s), 0.0])

        def scene(pe):
            if self.c_orbite.isChecked():
                pe.courbe(orbite, 'lune', 1.4, 0.9, arriere='normal', profondeur=False)
            pe.point(g['lune'], 'lune', 4.0 * k, bord='doux')

        def plan():
            if self.c_plan.isChecked():
                pe.plan('ecliptique', 0.18, 1.25, 'ecliptique')

        dessin.scene_en_deux_passes(pe, scene, plan)
        pe.segment(-1.3 * np.array([1.0, 0, 0]), 1.3 * np.array([1.0, 0, 0]), 'doux', 1.0, 0.7)
        pe.etiquette((1.38, 0, 0), tr('anim_mooninc_noeud_asc'), 'doux')
        pe.etiquette((-1.38, 0, 0), tr('anim_mooninc_noeud_desc'), 'doux')
        for d in (-0.25, 0.0, 0.25):                          # lumière du Soleil
            n = np.array([-math.sin(s), math.cos(s), 0.0]) * d
            a, b = 1.9 * u + n, 1.45 * u + n
            xa, ya, _, _ = pe.ecran(a)
            xb, yb, _, _ = pe.ecran(b)
            dessin.fleche(p, xa[0], ya[0], xb[0], yb[0], dessin.stylo('soleil', 1.4, 0.85), 6)
        pe.segment((0, 0, 0), -1.25 * u, 'ombre', 3.0, 0.5)    # direction de l'ombre de la Terre
        xs, ys, _, _ = pe.ecran((0, 0, 0))
        dessin.disque(p, xs[0], ys[0], 6.0 * k, 'terre', bord='texte')

    def _depuis_soleil(self, p, r):
        """Vue depuis le Soleil, à l'échelle : la Terre, son ombre (à la distance de la Lune) et la Lune quand elle
        est près de l'alignement (nouvelle lune devant la Terre, pleine lune derrière)."""
        g = geometrie(self.t)
        cx, cy = r.center().x(), r.center().y()
        demi = 6.0 * R_T                                     # demi-largeur de la fenêtre, km
        k = min(r.width(), r.height()) / 2 / demi
        s = math.radians(g['s'])
        e1 = np.array([-math.sin(s), math.cos(s), 0.0])       # droite de l'image vue du Soleil
        e2 = np.array([0.0, 0.0, 1.0])                         # nord de l'écliptique en haut
        lx = float(g['lune'] @ e1) * astro.D_LUNE_KM
        ly = float(g['lune'] @ e2) * astro.D_LUNE_KM
        derriere = g['axial'] < 0
        for rad, cle, al in ((PENOMBRE_TERRE_KM, 'penombre', 0.25), (OMBRE_TERRE_KM, 'umbra', 0.55)):
            p.setPen(dessin.stylo('grille', 1.0, 0.6, pointille=True))
            p.setBrush(dessin.c(cle, al))
            p.drawEllipse(QPointF(cx, cy), rad * k, rad * k)
        lune = (cx + lx * k, cy - ly * k)
        visible = abs(lx) < demi * 1.3 and abs(ly) < demi * 1.3
        if visible and derriere:
            dessin.disque(p, *lune, R_L * k, 'lune', bord='doux')
        dessin.disque(p, cx, cy, R_T * k, 'terre')
        if visible and not derriere:
            dessin.disque(p, *lune, R_L * k, 'nuit', bord='lune')
        e = eclipse(g)
        if e:
            dessin.texte(p, cx, r.bottom() - 12, tr('anim_mooninc_e_' + e), 'accent1', fond=True)

    def _frise(self, p, r):
        """Frise du temps : ±60 jours autour d'aujourd'hui, saisons d'éclipses (Soleil à moins de 18,5° d'un nœud),
        nouvelles et pleines lunes."""
        x0, x1 = r.x() + 6, r.right() - 6
        portee = 60.0

        def x_de(t):
            return x0 + (x1 - x0) * (t - (self.t - portee)) / (2 * portee)

        y0, y1 = r.y() + 6, r.bottom() - 18
        demi = 18.5 / (360.0 / astro.ANNEE_DRACONITIQUE_J)    # jours
        n0 = math.floor((self.t - portee) / (astro.ANNEE_DRACONITIQUE_J / 2)) - 1
        for n in range(n0, n0 + 4):
            tc = n * astro.ANNEE_DRACONITIQUE_J / 2
            a, b = max(x0, x_de(tc - demi)), min(x1, x_de(tc + demi))
            if b > a:
                p.setPen(dessin.Qt.PenStyle.NoPen)
                p.setBrush(dessin.c('accent1', 0.22))
                p.drawRect(QRectF(a, y0, b - a, y1 - y0))
        m0 = math.floor((self.t - portee) / astro.MOIS_SYNODIQUE_J) - 1
        for m in range(m0, m0 + 6):
            for frac, cle in ((0.0, 'nuit'), (0.5, 'lune')):
                tm = (m + frac) * astro.MOIS_SYNODIQUE_J
                x = x_de(tm)
                if x0 <= x <= x1:
                    dessin.disque(p, x, (y0 + y1) / 2, 5, cle, bord='doux')
        p.setPen(dessin.stylo('accent3', 2.0))
        p.drawLine(QPointF(x_de(self.t), y0 - 2), QPointF(x_de(self.t), y1 + 2))
        dessin.police(p, 0.8)
        dessin.texte(p, x0, r.bottom() - 6, tr('anim_mooninc_frise'), 'doux', centre=False)
        dessin.police(p, 1 / 0.8)
