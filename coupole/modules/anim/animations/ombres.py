"""Eclipse Shadow Simulator : la Lune (et la Terre) à placer librement ; les cônes d'ombre, d'antombre et de pénombre
de la Terre ET de la Lune sont tracés en vraie géométrie, et le type d'éclipse est calculé avec les tailles et la
distance réelles de la Lune telle que placée (eclipses_geo.py : totale, annulaire, hybride, partielle, pénombrale,
aucune ; largeur de la bande).  Même rendu et mêmes nombres que Coupole Web (src/anim/animations/ombres.ts).

Vue de côté : Soleil à gauche, si loin que ses rayons sont parallèles (hors échelle) ; le long de l'axe, 1 px vaut
kx km (la distance Terre–Lune affichée est celle de la figure) ; en travers, 1 px vaut ky km (tailles et écarts
agrandis du rapport kx / ky, indiqué).  Vue 3D : orbite de la Lune inclinée de 5,145° sur le plan Terre–Soleil, ligne
des nœuds, Lune au-dessus ou au-dessous de l'axe ; curseurs « position sur l'orbite » et « angle Soleil – nœuds ».
« Rejouer une éclipse » replace la Lune selon la géométrie réelle de l'éclipse choisie (JPL DE440 : distance, gamma,
trajectoire ; donnees/eclipses_geometrie.json.gz, outils/verif_anim/geometrie_eclipses.py), dans les trois vues."""
from __future__ import annotations

import gzip
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainterPath, QPolygonF

from ....core.i18n import langue, tr
from .. import astro, dessin
from .. import eclipses_geo as G
from ..base import Animation, duree_hm, nombre
from ..donnees_eclipses import LUNE, SOLEIL
from .table_eclipses import format_duree

INCLINAISON_LUNE = 5.145
AGRANDISSEMENT = 6            # vue de côté : tailles et écarts (en travers) agrandis par rapport aux distances le long de l'axe
DONNEES = Path(__file__).resolve().parent.parent / 'donnees' / 'eclipses_geometrie.json.gz'


@lru_cache(maxsize=1)
def geometrie_eclipses() -> dict:
    with gzip.open(DONNEES, 'rt', encoding='utf-8') as f:
        return json.load(f)['eclipses']


def date_eclipse(e) -> str:
    nom = tr('anim_mois_%d' % e[1])
    return ('%d %s %d' % (e[2], nom, e[0])) if langue() == 'fr' else ('%d %s %d' % (e[2], nom, e[0]))


def rejeu(cle: str):
    """Éclipse de la table (clé « S<i> » ou « L<i> ») et sa géométrie réelle (DE440), ou None."""
    solaire = cle[:1] == 'S'
    table = SOLEIL if solaire else LUNE
    try:
        e = table[int(cle[1:])]
    except (ValueError, IndexError):
        return None
    g = geometrie_eclipses().get(cle)
    if g is None:
        return None
    v = max(1.0, math.hypot(g['vx_kmh'], g['vy_kmh']))
    delta = abs(g['gamma']) * G.R_TERRE_KM
    x = math.sqrt(max(0.0, g['d_km'] ** 2 - delta ** 2))
    if solaire:
        rayon = G.R_TERRE_KM + G.eclipse_soleil(-x, 0.0, g['s_km'])['penombre_km']
    else:
        rayon = G.eclipse_lune(x, 0.0, g['s_km'])['penombre_km'] + G.R_LUNE_KM
    return {'cle': cle, 'solaire': solaire, 'e': e, 'g': g, 'demi_h': rayon * 1.08 / v}


def lune_rejeu(rj: dict, u: float) -> tuple:
    """Lune (km, repère de la Terre : x vers l'opposé du Soleil, y nord, z est) à l'instant u ∈ [−1, 1]."""
    g = rj['g']
    dt = u * rj['demi_h']
    est = g['x_km'] + g['vx_kmh'] * dt
    nord = g['y_km'] + g['vy_kmh'] * dt
    delta = math.hypot(est, nord)
    le_long = math.sqrt(max(0.0, g['d_km'] ** 2 - delta ** 2))
    return (-le_long if rj['solaire'] else le_long, nord, est)


def types(x: float, y: float, z: float, d_soleil: float = G.UA_KM) -> dict:
    """Types d'éclipse pour une Lune en (x, y, z) km par rapport à la Terre."""
    delta = math.hypot(y, z)
    return {'soleil': G.eclipse_soleil(x, delta, d_soleil), 'lune': G.eclipse_lune(x, delta, d_soleil),
            'distance_km': math.sqrt(x * x + y * y + z * z), 'delta_km': delta}


class OmbresEclipse(Animation):
    ID = 'shadowsim'
    ANIMEE = False

    def construire(self):
        self.vue3d = self.vue(215.0, 22.0, -80.0, 85.0)
        self.terre = (0.42, 0.5)
        self.lune = (G.D_LUNE_KM, 0.0, 0.0)
        self.c_reel = self.coche('reel', True)
        self.c_3d = self.coche('vue3d', True)
        self.position = self.curseur('position', 0.0, 360.0, 180.0, dec=0, unite='°')
        self.noeuds = self.curseur('noeuds', 0.0, 360.0, 0.0, dec=0, unite='°')
        self.position.valueChanged.connect(self._orbite)
        self.noeuds.valueChanged.connect(self._orbite)
        toutes = [(e, 'S%d' % i, True) for i, e in enumerate(SOLEIL)] + [(e, 'L%d' % i, False) for i, e in enumerate(LUNE)]
        toutes.sort(key=lambda t: (t[0][0], t[0][1], t[0][2]))
        self.rejouer = self.choix('rejouer', [('anim_shadowsim_libre', 'libre')] +
                                  [('anim_shadowsim_libre', cle) for _, cle, _ in toutes], 'libre')
        for i, (e, _, sol) in enumerate(toutes, start=1):
            self.rejouer.setItemText(i, '%s · %s, %s' % (date_eclipse(e), tr('anim_shadowsim_soleil' if sol else
                                                                           'anim_shadowsim_lune_t'),
                                                        tr('anim_eclipsetable_t_' + e[3])))
        self.instant = self.curseur('instant', -1.0, 1.0, 0.0, dec=2)
        self.instant.setVisible(self.rejouer.currentData() != 'libre')
        self.rejouer.currentIndexChanged.connect(self._rejeu_change)
        self.instant.valueChanged.connect(self._instant_change)
        self._cote = None
        self._echelle = (G.D_LUNE_KM / 186.0, G.D_LUNE_KM / 186.0 / AGRANDISSEMENT)   # avant le premier dessin

    def _orbite(self, *_):
        if self.rejeu():
            return
        d = math.sqrt(sum(v * v for v in self.lune)) or G.D_LUNE_KM
        self.lune = G.position_orbite(d, self.position.value(), self.noeuds.value(), INCLINAISON_LUNE)

    def _rejeu_change(self, *_):
        rj = self.rejeu()
        self.instant.setVisible(rj is not None)
        self.instant.setValue(0.0)
        if rj:
            self.lune = lune_rejeu(rj, 0.0)

    def _instant_change(self, *_):
        rj = self.rejeu()
        if rj:
            self.lune = lune_rejeu(rj, self.instant.value())

    def rejeu(self):
        k = self.rejouer.currentData()
        return None if not k or k == 'libre' else rejeu(k)

    def etat_initial(self):
        self.terre = (0.42, 0.5)
        pos = self.position.value() if hasattr(self, 'position') else 180.0
        nd = self.noeuds.value() if hasattr(self, 'noeuds') else 0.0
        self.lune = G.position_orbite(G.D_LUNE_KM, pos, nd, INCLINAISON_LUNE)

    def etat(self) -> dict:
        rj = self.rejeu()
        return types(*self.lune, rj['g']['s_km'] if rj else G.UA_KM)

    # ------------------------------------------------------------ souris
    def _ecran(self, r: QRectF) -> dict:
        kx, ky = self._echelle
        ex, ey = r.x() + self.terre[0] * r.width(), r.y() + self.terre[1] * r.height()
        return {'ex': ex, 'ey': ey, 'lx': ex + self.lune[0] / kx, 'ly': ey - self.lune[1] / ky, 'kx': kx, 'ky': ky,
                'rt': G.R_TERRE_KM / ky, 'rl': G.R_LUNE_KM / ky}

    def presser(self, pos, bouton):
        r = self._cote
        if r is not None and r.contains(pos) and not self.rejeu():
            e = self._ecran(r)
            if math.hypot(pos.x() - e['lx'], pos.y() - e['ly']) <= max(e['rl'], 10) + 8:
                self._glisse = self._tirer_lune
                return True
            if math.hypot(pos.x() - e['ex'], pos.y() - e['ey']) <= e['rt'] + 6:
                self._glisse = self._tirer_terre
                return True
        return super().presser(pos, bouton)

    def _tirer_lune(self, pos):
        r = self._cote
        e = self._ecran(r)
        px = max(r.x() + 4, min(r.right() - 4, pos.x()))
        py = max(r.y() + 4, min(r.bottom() - 4, pos.y()))
        dx, dy = px - e['ex'], py - e['ey']
        mini = e['rt'] + e['rl'] + 2                  # jamais dans la Terre
        d = math.hypot(dx, dy)
        if d < mini:
            ux, uy = (dx / d, dy / d) if d > 1e-6 else (1.0, 0.0)
            dx, dy = ux * mini, uy * mini
        if not (math.isfinite(dx) and math.isfinite(dy)):
            return
        self.lune = (dx * e['kx'], -dy * e['ky'], 0.0)

    def _tirer_terre(self, pos):
        r = self._cote
        x = max(0.2, min(0.8, (pos.x() - r.x()) / r.width()))
        y = max(0.12, min(0.88, (pos.y() - r.y()) / r.height()))
        if math.isfinite(x) and math.isfinite(y):
            self.terre = (x, y)

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        t = self.etat()
        s, lu = t['soleil'], t['lune']

        def km(v):
            return nombre(math.floor(v + 0.5), 0)            # Math.round du web

        sens = tr('anim_shadowsim_nord') if self.lune[1] >= 0 else tr('anim_shadowsim_sud')
        d = t['distance_km']
        cle_d = 'anim_shadowsim_dist_moins' if d < G.PERIGEE_MIN_KM else \
            'anim_shadowsim_dist_plus' if d > G.APOGEE_MAX_KM else 'anim_shadowsim_dist_dans'
        soleil = tr('anim_shadowsim_aucune') if s['type'] == 'aucune' else tr('anim_shadowsim_s_' + s['type'], l=km(s['largeur_km']))
        lune = tr('anim_shadowsim_aucune') if lu['type'] == 'aucune' else tr('anim_shadowsim_l_' + lu['type'])
        out = [(tr('anim_shadowsim_solaire'), soleil),
               (tr('anim_shadowsim_lunaire'), lune),
               (tr('anim_shadowsim_distance'), tr(cle_d, d=km(d), p=km(G.PERIGEE_MIN_KM), a=km(G.APOGEE_MAX_KM))),
               (tr('anim_shadowsim_ecart'), tr('anim_shadowsim_ecart_val', r=nombre(abs(self.lune[1]) / G.R_TERRE_KM, 2),
                                               km=km(abs(self.lune[1])), dir=sens))]
        if abs(self.lune[2]) > 1:
            out.append((tr('anim_shadowsim_hors_plan'), '%s km' % km(abs(self.lune[2]))))
        out.append((tr('anim_shadowsim_echelle'), tr('anim_shadowsim_echelle_val', k=nombre(AGRANDISSEMENT, 0))))
        rj = self.rejeu()
        if rj:
            ec, g = rj['e'], rj['g']
            jj = g['jj_ut'] + self.instant.value() * rj['demi_h'] / 24.0
            h = ((jj + 0.5) % 1.0 + 1.0) % 1.0
            hm = '%02d:%02d' % (math.floor(h * 24), math.floor((h * 24 % 1) * 60))
            out += [(tr('anim_shadowsim_rejouee'), '%s · %s, %s' % (
                        date_eclipse(ec), tr('anim_shadowsim_soleil' if rj['solaire'] else 'anim_shadowsim_lune_t'),
                        tr('anim_eclipsetable_t_' + ec[3]))),
                    (tr('anim_shadowsim_instant_ut'), '%s %s' % (hm, tr('anim_shadowsim_tu'))),
                    (tr('anim_shadowsim_gamma'), nombre(g['gamma'], 4)),
                    (tr('anim_eclipsetable_grandeur'), nombre(ec[5], 3)),
                    (tr('anim_eclipsetable_duree'), format_duree(ec[6]))]
        elif self.c_reel.isChecked():
            e = astro.eclipse_de_lune()
            out += [(tr('anim_shadowsim_rayon_ombre'), '%s km (%s × %s)' % (
                        nombre(e['rayon_ombre_km'], 0), nombre(e['ombre_en_diametres_lunaires'], 2),
                        tr('anim_shadowsim_diam_lune'))),
                    (tr('anim_shadowsim_longueur_ombre'), '%s km' % nombre(e['longueur_ombre_km'], 0)),
                    (tr('anim_shadowsim_totalite'), duree_hm(e['totalite_h'])),
                    (tr('anim_shadowsim_phase_ombre'), duree_hm(e['ombre_totale_h']))]
        return out

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        rj = self.rejeu()
        encart = self.c_reel.isChecked() or rj is not None
        # l'éclipse rejouée, vue de face, a besoin d'un peu plus de place que l'encart d'Aristarque
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * (0.6 if rj else 0.7 if encart else 1.0))
        cote, r3d = haut, None
        if self.c_3d.isChecked():
            if haut.width() > haut.height() * 1.25:
                cote = QRectF(haut.x(), haut.y(), haut.width() * 0.62, haut.height())
                r3d = QRectF(haut.x() + haut.width() * 0.62, haut.y(), haut.width() * 0.38, haut.height())
            else:
                cote = QRectF(haut.x(), haut.y(), haut.width(), haut.height() * 0.58)
                r3d = QRectF(haut.x(), haut.y() + haut.height() * 0.58, haut.width(), haut.height() * 0.42)
        self._vue_de_cote(p, cote)
        if r3d is not None:
            self._vue_orbite(p, r3d)
        bas = QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height())
        if rj:
            self._rejouer(p, bas, rj)
        elif encart:
            self._aristarque(p, bas)

    def _vue_de_cote(self, p, r0):
        """Soleil à gauche (hors échelle), Terre, Lune et leurs cônes en vraie géométrie (deux échelles)."""
        r = dessin.cadre(p, r0, tr('anim_shadowsim_titre_cote'))
        self._cote = QRectF(r)
        # 384 400 km = 30 % de la largeur ; en travers, AGRANDISSEMENT fois plus grand
        kx = G.D_LUNE_KM / (r.width() * 0.3)
        self._echelle = (kx, kx / AGRANDISSEMENT)
        e = self._ecran(r)
        t = self.etat()
        rj = self.rejeu()
        ds = rj['g']['s_km'] if rj else G.UA_KM
        p.save()
        p.setClipRect(r)
        rs = r.height() * 0.9
        dessin.disque(p, r.x() - rs + 16, r.center().y(), rs, 'soleil')
        p.setPen(dessin.stylo('soleil', 0.8, 0.25))
        for k in range(-3, 4):
            yy = r.center().y() + k * r.height() / 8
            p.drawLine(QPointF(r.x() + 20, yy), QPointF(r.right(), yy))

        def cone(ox, oy, rkm, d_sm, couleur):
            ku, kp = (G.R_SOLEIL_KM - rkm) / d_sm, (G.R_SOLEIL_KM + rkm) / d_sm
            fin = r.right() - ox
            if fin <= 0:
                return
            xkm = fin * e['kx']
            rp_fin = (rkm + xkm * kp) / e['ky']
            p.setPen(dessin.stylo('grille', 0.8, 0.5))
            p.setBrush(dessin.c('penombre', 0.2))
            p.drawPolygon(QPolygonF([QPointF(ox, oy - rkm / e['ky']), QPointF(r.right(), oy - rp_fin),
                                     QPointF(r.right(), oy + rp_fin), QPointF(ox, oy + rkm / e['ky'])]))
            longueur = rkm / ku / e['kx']
            p.setBrush(dessin.c(couleur, 0.85))
            if longueur < fin:
                p.drawPolygon(QPolygonF([QPointF(ox, oy - rkm / e['ky']), QPointF(ox + longueur, oy),
                                         QPointF(ox, oy + rkm / e['ky'])]))
                ra = (fin - longueur) * e['kx'] * ku / e['ky']
                p.setPen(dessin.stylo('accent1', 1.1, 0.85, True))
                p.setBrush(dessin.c('accent1', 0.12))
                p.drawPolygon(QPolygonF([QPointF(ox + longueur, oy), QPointF(r.right(), oy - ra), QPointF(r.right(), oy + ra)]))
            else:
                ru_fin = (rkm - xkm * ku) / e['ky']
                p.drawPolygon(QPolygonF([QPointF(ox, oy - rkm / e['ky']), QPointF(r.right(), oy - ru_fin),
                                         QPointF(r.right(), oy + ru_fin), QPointF(ox, oy + rkm / e['ky'])]))

        cone(e['ex'], e['ey'], G.R_TERRE_KM * G.ATMOSPHERE, ds, 'umbra')
        cone(e['lx'], e['ly'], G.R_LUNE_KM, ds + self.lune[0], 'umbra')
        p.setPen(dessin.stylo('doux', 0.8, 0.6, True))
        p.drawLine(QPointF(r.x() + 16, e['ey']), QPointF(r.right(), e['ey']))
        dessin.disque(p, e['ex'], e['ey'], e['rt'], 'terre', bord='texte')
        hors_plan = abs(self.lune[2]) > G.R_TERRE_KM
        dessin.disque(p, e['lx'], e['ly'], max(2.5, e['rl']), 'lune', bord=None if hors_plan else 'texte',
                      alpha=0.45 if hors_plan else None)
        p.restore()
        dessin.texte(p, e['ex'], e['ey'] - e['rt'] - 10, tr('anim_shadowsim_terre'), fond=True)
        dessin.texte(p, e['lx'], e['ly'] - max(e['rl'], 4) - 10, tr('anim_shadowsim_lune'), fond=True)
        dessin.police(p, 0.8)
        dessin.texte(p, r.x() + 22, r.y() + 12, tr('anim_shadowsim_soleil_loin'), 'doux', centre=False, fond=True)
        if t['soleil']['type'] != 'aucune':
            etiquette = tr('anim_shadowsim_solaire') + ' : ' + tr('anim_shadowsim_' + t['soleil']['type'])
        elif t['lune']['type'] != 'aucune':
            etiquette = tr('anim_shadowsim_lunaire') + ' : ' + tr('anim_shadowsim_' + t['lune']['type'])
        else:
            etiquette = ''
        if etiquette:
            w = p.fontMetrics().horizontalAdvance(etiquette)
            dessin.texte(p, r.right() - 8 - w, r.y() + 12, etiquette, 'accent3', centre=False, fond=True)
        dessin.police(p, 1 / 0.8)

    def _vue_orbite(self, p, r0):
        """Plan Terre–Soleil, orbite inclinée de la Lune, ligne des nœuds, Lune au-dessus ou au-dessous de l'axe."""
        r = dessin.cadre(p, r0, tr('anim_shadowsim_titre_3d'))
        self.zone_rotative(r, self.vue3d)
        v = self.vue3d
        R = min(r.width() * 0.42, r.height() * 0.4)
        cx, cy = r.center().x(), r.center().y() + r.height() * 0.04

        def proj(pts):
            x, y, prof = v.projeter(np.asarray(pts, dtype=float))
            return [QPointF(cx + a * R, cy - b * R) for a, b in zip(x, y)]

        def cercle(rayon, f):
            a = np.linspace(0.0, 2 * math.pi, 97)
            return [tuple(rayon * c for c in f(t)) for t in a]

        p.save()
        p.setClipRect(r)
        plan = cercle(1.18, lambda a: (math.cos(a), math.sin(a), 0.0))
        p.setPen(dessin.stylo('grille', 0.8, 0.6))
        p.setBrush(dessin.c('ecliptique', 0.07))
        p.drawPolygon(QPolygonF(proj(plan)))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('soleil', 1.0, 0.7, True))
        a, b = proj([(-1.35, 0, 0), (1.35, 0, 0)])
        p.drawLine(a, b)
        s0, s1 = proj([(-1.3, 0, 0), (-1.05, 0, 0)])
        dessin.fleche(p, s1.x(), s1.y(), s0.x(), s0.y(), dessin.stylo('soleil', 1.4), 7)
        dessin.texte(p, s0.x(), s0.y() - 12, tr('anim_shadowsim_vers_soleil'), 'soleil', fond=True)
        rj = self.rejeu()
        om = math.radians(0.0 if rj else self.noeuds.value())
        inc = math.radians(INCLINAISON_LUNE)
        n = (-math.cos(om), math.sin(om), 0.0)
        m = (math.sin(om) * math.cos(inc), math.cos(om) * math.cos(inc), math.sin(inc))
        if not rj:
            orb = cercle(1.0, lambda a: tuple(n[k] * math.cos(a) + m[k] * math.sin(a) for k in range(3)))
            p.setPen(dessin.stylo('lune', 1.3, 0.85))
            p.drawPolyline(QPolygonF(proj(orb)))
        p.setPen(dessin.stylo('meridien', 1.0, 0.9, True))
        a, b = proj([(n[0] * 1.12, n[1] * 1.12, 0.0), (-n[0] * 1.12, -n[1] * 1.12, 0.0)])
        p.drawLine(a, b)
        dessin.police(p, 0.8)
        dessin.texte(p, a.x(), a.y() + 12, tr('anim_shadowsim_noeud_asc'), 'meridien', fond=True)
        dessin.police(p, 1 / 0.8)
        t0, = proj([(0.0, 0.0, 0.0)])
        dessin.disque(p, t0.x(), t0.y(), max(5.0, R * 0.07), 'terre', bord='texte')
        d = math.sqrt(sum(c * c for c in self.lune)) or 1.0
        lx, ly, lz = self.lune[0] / d, self.lune[2] / d, self.lune[1] / d
        l3, l0 = proj([(lx, ly, lz), (lx, ly, 0.0)])
        p.setPen(dessin.stylo('accent2' if lz >= 0 else 'accent3', 1.4))
        p.drawLine(l0, l3)
        dessin.disque(p, l3.x(), l3.y(), max(3.5, R * 0.035), 'lune', bord='texte')
        p.restore()
        ec = abs(self.lune[1]) / G.R_TERRE_KM
        dessin.police(p, 0.85)
        dessin.texte(p, r.x() + 8, r.bottom() - 26, tr('anim_shadowsim_orbite_lune'), 'lune', centre=False)
        dessin.texte(p, r.x() + 8, r.bottom() - 10, tr('anim_shadowsim_decalage_3d', r=nombre(ec, 2),
                                                       dir=tr('anim_shadowsim_nord') if self.lune[1] >= 0 else
                                                       tr('anim_shadowsim_sud')), centre=False)
        dessin.police(p, 1 / 0.85)

    def _rejouer(self, p, r0, rj):
        """L'éclipse choisie, vue de face (plan fondamental, vraie géométrie DE440) ; l'instant fait avancer la Lune."""
        r = dessin.cadre(p, r0, tr('anim_shadowsim_titre_soleil' if rj['solaire'] else 'anim_shadowsim_titre_lune',
                                   date=date_eclipse(rj['e'])))
        RL, RT = G.R_LUNE_KM, G.R_TERRE_KM
        a0, a1 = lune_rejeu(rj, -1.0), lune_rejeu(rj, 1.0)
        t = self.etat()
        rp = t['soleil']['penombre_km'] if rj['solaire'] else t['lune']['penombre_km']
        portee = max(abs(a0[2]), abs(a1[2]), abs(a0[1]), abs(a1[1])) + max(rp + RL, RT) * 1.05
        k = min(r.width() / (2 * portee),
                r.height() / (2 * (max(abs(a0[1]), abs(a1[1])) + max(rp + RL, RT) * 1.1)))
        cx, cy = r.center().x(), r.center().y()
        sens = 1 if rj['solaire'] else -1

        def pos(u):
            q = lune_rejeu(rj, u)
            return QPointF(cx + sens * q[2] * k, cy - q[1] * k)

        u = self.instant.value()
        p.save()
        p.setClipRect(r)
        p.setPen(dessin.stylo('doux', 1.0, 0.7, True))
        p.drawLine(pos(-1), pos(1))
        a, b = pos(0.82), pos(1)
        dessin.fleche(p, a.x(), a.y(), b.x(), b.y(), dessin.stylo('doux', 1.2, 0.8), 7)
        if not rj['solaire']:
            dessin.disque(p, cx, cy, t['lune']['penombre_km'] * k, 'penombre', alpha=0.25)
            dessin.disque(p, cx, cy, t['lune']['ombre_km'] * k, 'umbra', alpha=0.88)
            for v in (-1, 1):
                q = pos(v)
                p.setPen(dessin.stylo('lune', 1.0, 0.5))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawEllipse(q, RL * k, RL * k)
            q = pos(u)
            dessin.disque(p, q.x(), q.y(), RL * k, 'lune', bord='texte')
            p.save()
            ch = QPainterPath()
            ch.addEllipse(q, RL * k, RL * k)
            p.setClipPath(ch, dessin.Qt.ClipOperation.IntersectClip)
            dessin.disque(p, cx, cy, t['lune']['ombre_km'] * k, 'arc2', alpha=0.55)
            p.restore()
        else:
            s = t['soleil']
            dessin.disque(p, cx, cy, RT * k, 'terre', bord='texte')
            q = pos(u)
            p.save()
            ch = QPainterPath()
            ch.addEllipse(QPointF(cx, cy), RT * k, RT * k)
            p.setClipPath(ch, dessin.Qt.ClipOperation.IntersectClip)
            dessin.disque(p, q.x(), q.y(), s['penombre_km'] * k, 'umbra', alpha=0.35)
            if s['ombre_surface_km'] > 0:
                dessin.disque(p, q.x(), q.y(), max(2.5, s['ombre_surface_km'] * k), 'umbra', alpha=0.95)
            p.restore()
            p.setPen(dessin.stylo('penombre', 1.0, 0.8, True))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(q, s['penombre_km'] * k, s['penombre_km'] * k)
            if s['ombre_surface_km'] < 0:
                p.setPen(dessin.stylo('accent1', 1.4))
                rr = max(3.0, -s['ombre_surface_km'] * k)
                p.drawEllipse(q, rr, rr)
        p.restore()
        dessin.police(p, 0.85)
        dessin.texte(p, r.left() + 4, r.bottom() - 4, tr('anim_shadowsim_note'), 'doux', centre=False)
        dessin.texte(p, r.right() - 14, r.top() + 12, tr('anim_pc_n') + ' ↑', 'doux')
        dessin.police(p, 1 / 0.85)

    def _aristarque(self, p, r):
        """Traversée centrale de l'ombre de la Terre par la Lune, proportions réelles."""
        r = dessin.cadre(p, r, tr('anim_shadowsim_titre_reel'))
        e = astro.eclipse_de_lune()
        k = min(r.height() * 0.42 / e['rayon_penombre_km'], r.width() * 0.2 / e['rayon_penombre_km'])
        cx, cy = r.x() + r.width() * 0.35, r.center().y()
        dessin.disque(p, cx, cy, e['rayon_penombre_km'] * k, 'penombre', alpha=0.25)
        dessin.disque(p, cx, cy, e['rayon_ombre_km'] * k, 'umbra', alpha=0.9)
        rl = astro.R_LUNE_KM * k
        for dx in (-(e['rayon_ombre_km'] + astro.R_LUNE_KM), -(e['rayon_ombre_km'] - astro.R_LUNE_KM), 0.0,
                   e['rayon_ombre_km'] - astro.R_LUNE_KM, e['rayon_ombre_km'] + astro.R_LUNE_KM):
            p.setPen(dessin.stylo('lune', 1.2))
            p.setBrush(dessin.c('lune', 0.15))
            p.drawEllipse(QPointF(cx + dx * k, cy), rl, rl)
        x = r.x() + r.width() * 0.62
        dessin.texte(p, x, r.y() + 14, tr('anim_shadowsim_rapport', x=nombre(e['ombre_en_diametres_lunaires'], 2)),
                     centre=False)
        dessin.texte(p, x, r.y() + 34, tr('anim_shadowsim_duree_tot', d=duree_hm(e['totalite_h'])), centre=False)
