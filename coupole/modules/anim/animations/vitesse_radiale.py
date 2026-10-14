"""Vitesse radiale d'une étoile à planète : deux animations.

Radial Velocity Graph : l'étoile et sa planète tournent autour de leur centre de masse ; la vitesse de l'étoile le
long de la ligne de visée trace une sinusoïde.  Extrasolar Planet Radial Velocity Demonstrator : le même mouvement
vu dans le spectre, dont les raies se décalent vers le bleu puis vers le rouge (effet Doppler, Δλ / λ = v / c).

K = (2πG / P)^⅓ M_p sin i / (M_* + M_p)^⅔ (orbite circulaire) ; masses par les GM (UAI, JPL), 51 Pegasi b par
la NASA Exoplanet Archive."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import deux_corps as dc, dessin, donnees_lot3 as D, lumiere
from ..base import Animation, nombre
from ..graphe import Axes, bande_spectre

GM_TERRE_LUNE = D.GM_DE440_KM3_S2['terre'] * 1e9
# système : (M étoile en kg, M planète en kg, a en m, i en degrés)
SYSTEMES = {
    'soleil_jupiter': (dc.M_SOLEIL_KG, D.GM_DE440_KM3_S2['jupiter'] * 1e9 / dc.G,
                       D.ELEMENTS_STANDISH['jupiter'][0][0] * dc.UA_M, 90.0),
    'soleil_terre': (dc.M_SOLEIL_KG, GM_TERRE_LUNE / dc.G, D.ELEMENTS_STANDISH['terre'][0][0] * dc.UA_M, 90.0),
    '51peg': (1.07 * dc.M_SOLEIL_KG, 0.61 * dc.M_JUPITER_KG, 0.052 * dc.UA_M, 49.8),
}
K_PUBLIEE = {'51peg': 55.77}
RAIES = (656.28, 589.0, 486.13, 434.05)


def systeme(nom: str) -> dict:
    m1, m2, a, i = SYSTEMES[nom]
    p = dc.periode_s(a, m1, m2)
    return {'m1': m1, 'm2': m2, 'a': a, 'i': i, 'P': p, 'K': dc.amplitude_k(m1, m2, a, 0.0, i)}


def texte_duree(s: float) -> str:
    j = s / dc.JOUR_S
    if j < 1:
        return '%s %s' % (nombre(j * 24, 2), tr('anim_c_heures'))
    if j > 700:
        return '%s %s' % (nombre(j / 365.25, 2), tr('anim_c_ans'))
    return '%s %s' % (nombre(j, 3 if j < 10 else 1), tr('anim_c_jours'))


class CourbeVitesseRadiale(Animation):
    ID = 'ca_extrasolarplanets_graph'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.sys = self.choix('systeme', [('anim_ca_extrasolarplanets_graph_s_' + k, k) for k in SYSTEMES],
                              'soleil_jupiter')
        self.phase = 0.0

    def etat_initial(self):
        self.phase = 0.0

    def avancer(self, dt):
        self.phase = (self.phase + dt / 8.0) % 1.0           # une orbite en 8 s

    def valeurs(self):
        s = systeme(self.sys.currentData())
        v = -s['K'] * math.cos(2 * math.pi * self.phase)
        out = [(tr('anim_c_periode'), texte_duree(s['P'])),
               (tr('anim_ca_extrasolarplanets_graph_k'), '%s m·s⁻¹' % nombre(s['K'], 2)),
               (tr('anim_ca_extrasolarplanets_graph_v'), '%s m·s⁻¹' % nombre(v, 2))]
        kp = K_PUBLIEE.get(self.sys.currentData())
        if kp:
            out.append((tr('anim_ca_extrasolarplanets_graph_k_mesuree'), '%s m·s⁻¹' % nombre(kp, 2)))
        return out

    def dessiner(self, p, rect):
        s = systeme(self.sys.currentData())
        z = dessin.zones(rect, 2, 0.9)
        r = dessin.cadre(p, z[0], tr('anim_ca_extrasolarplanets_graph_titre_orbite'))
        cx, cy = r.center().x(), r.center().y() - 10
        rp = min(r.width(), r.height()) * 0.36
        q = s['m2'] / (s['m1'] + s['m2'])
        rs = max(6.0, rp * q * 40)                         # orbite de l'étoile très agrandie (indiquée)
        a = 2 * math.pi * self.phase
        # l'observateur est en bas : v_r = −K cos a, négative quand l'étoile descend vers lui
        sx, sy = cx - rs * math.cos(a), cy + rs * math.sin(a)
        px, py = cx + rp * math.cos(a), cy - rp * math.sin(a)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('equateur', 1.0, 0.6, True))
        p.drawEllipse(QPointF(cx, cy), rp, rp)
        p.setPen(dessin.stylo('accent1', 1.0, 0.8, True))
        p.drawEllipse(QPointF(cx, cy), rs, rs)
        v = -s['K'] * math.cos(a)
        col = 'accent2' if v < 0 else 'accent3'
        dessin.disque(p, sx, sy, 14, 'soleil')
        dessin.disque(p, px, py, 5, 'equateur', bord='texte')
        dessin.fleche(p, sx, sy, sx, sy - 40 * v / s['K'], dessin.stylo(col, 2.0), 7)
        p.setPen(dessin.stylo('accent3', 1.5))
        p.drawLine(QPointF(cx - 4, cy), QPointF(cx + 4, cy))
        p.drawLine(QPointF(cx, cy - 4), QPointF(cx, cy + 4))
        dessin.texte(p, cx, r.bottom() - 10, '↓ ' + tr('anim_c_vers_observateur'), 'doux')
        dessin.texte(p, r.left() + 8, r.top() + 10, tr('anim_ca_extrasolarplanets_graph_agrandie'), 'doux', centre=False)
        # courbe
        r2 = dessin.cadre(p, z[1], tr('anim_ca_extrasolarplanets_graph_titre_courbe'))
        k = s['K']
        ax = Axes(r2, 0, 2, -1.25 * k, 1.25 * k, marges=(52, 10, 12, 30)).avec(p)
        ax.fond(p, tr('anim_ca_extrasolarplanets_graph_axe_t'), tr('anim_c_vitesse_radiale'))
        ax.horizontale(0.0, 'grille', 1.0, False)
        pts = [(x / 100, -k * math.cos(2 * math.pi * x / 100)) for x in range(201)]
        ax.courbe(pts, 'accent1', 2.0)
        for n in (0, 1):
            x = self.phase + n
            ax.points([(x, v)], col, 6, 1.0)
        dessin.texte(p, ax.r.left() + 6, ax.r.top() + 10, tr('anim_ca_extrasolarplanets_graph_eloigne'), 'accent3',
                     centre=False)
        dessin.texte(p, ax.r.left() + 6, ax.r.bottom() - 6, tr('anim_ca_extrasolarplanets_graph_approche'), 'accent2',
                     centre=False)


class SpectreVitesseRadiale(Animation):
    ID = 'radialvelocitydemo'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.m_etoile = self.curseur('etoile', 0.3, 2.0, 1.0, dec=2, unite='M☉')
        self.m_planete = self.curseur('planete', 0.01, 20.0, 1.0, dec=2, unite='M♃', log=True)
        self.a = self.curseur('a', 0.02, 6.0, 0.05, dec=3, unite='ua', log=True)
        self.amplification = self.curseur('amplification', 1.0, 100000.0, 10000.0, dec=0, unite='×', log=True)
        self.phase = 0.0

    def etat_initial(self):
        self.phase = 0.0

    def avancer(self, dt):
        self.phase = (self.phase + dt / 8.0) % 1.0

    def grandeurs(self):
        m1 = self.m_etoile.value() * dc.M_SOLEIL_KG
        m2 = self.m_planete.value() * dc.M_JUPITER_KG
        a = self.a.value() * dc.UA_M
        k = dc.amplitude_k(m1, m2, a, 0.0, 90.0)
        v = -k * math.cos(2 * math.pi * self.phase)
        return {'P': dc.periode_s(a, m1, m2), 'K': k, 'v': v}

    def valeurs(self):
        g = self.grandeurs()
        return [(tr('anim_c_periode'), texte_duree(g['P'])),
                (tr('anim_ca_extrasolarplanets_graph_k'), '%s m·s⁻¹' % nombre(g['K'], 2)),
                (tr('anim_ca_extrasolarplanets_graph_v'), '%s m·s⁻¹' % nombre(g['v'], 2)),
                (tr('anim_radialvelocitydemo_dl'), '%s pm' % nombre(656.28e3 * g['v'] / lumiere.C, 4))]

    def dessiner(self, p, rect):
        g = self.grandeurs()
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.62)
        r = dessin.cadre(p, haut, tr('anim_radialvelocitydemo_titre_systeme'))
        cx, cy = r.center().x(), r.center().y() - 6
        rp = min(r.width() * 0.4, r.height() * 0.42)
        q = self.m_planete.value() * dc.M_JUPITER_KG / (self.m_etoile.value() * dc.M_SOLEIL_KG)
        rs = max(4.0, min(rp * 0.4, rp * q * 30))
        a = 2 * math.pi * self.phase
        sx, sy = cx - rs * math.cos(a), cy + rs * math.sin(a)
        px, py = cx + rp * math.cos(a), cy - rp * math.sin(a)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('equateur', 1.0, 0.6, True))
        p.drawEllipse(QPointF(cx, cy), rp, rp)
        dessin.disque(p, sx, sy, 13, 'soleil')
        dessin.disque(p, px, py, 4 + 2 * math.log10(1 + self.m_planete.value() * 10), 'equateur', bord='texte')
        dessin.texte(p, cx, r.bottom() - 8, '↓ ' + tr('anim_c_vers_observateur'), 'doux')
        bas = QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height())
        rb = dessin.cadre(p, bas, tr('anim_radialvelocitydemo_titre_spectre'))
        bande = QRectF(rb.x() + 8, rb.y() + 2, rb.width() - 16, max(16.0, rb.height() * 0.42))
        z = g['v'] / lumiere.C * self.amplification.value()
        bande_spectre(p, bande, 420, 680, lambda lam: 1.0, [(lam * (1 + z), 0.85, 3.0) for lam in RAIES], True)
        ref = QRectF(bande.left(), bande.bottom() + 6, bande.width(), max(10.0, rb.height() * 0.22))
        bande_spectre(p, ref, 420, 680, lambda lam: 0.55, [(lam, 0.85, 2.0) for lam in RAIES], True)
        dessin.police(p, 0.8)
        dessin.texte(p, ref.center().x(), ref.bottom() + 9, tr('anim_radialvelocitydemo_reference'), 'doux')
        dessin.police(p, 1 / 0.8)
