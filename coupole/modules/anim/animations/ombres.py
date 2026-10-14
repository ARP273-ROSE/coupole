"""Eclipse Shadow Simulator : Terre et Lune à déplacer à la souris, avec leurs cônes d'ombre (umbra) et de
pénombre, tracés par les tangentes communes au Soleil et au corps (géométrie du simulateur d'origine).  Le type
d'éclipse produit est indiqué.  Un encart donne les proportions réelles d'une éclipse centrale de Lune (méthode
d'Aristarque : l'ombre de la Terre, à la distance de la Lune, fait environ 2,65 diamètres lunaires).

« Rejouer une éclipse » montre une éclipse de la table 2015–2044 en proportions réelles (ombre et pénombre de la
Terre à la distance de la Lune, ou ombre de la Lune sur la Terre).  L'écart à l'axe de l'ombre vient de l'argument de
latitude moyen de la Lune (Meeus) : y = D sin(5,145°) sin F, ramené dans le domaine compatible avec le type de la
table (les éléments moyens ne sont qu'approchés)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainterPath, QPolygonF

from ....core.i18n import langue, tr
from .. import astro, dessin
from ..base import Animation, duree_hm, nombre
from ..donnees_eclipses import LUNE, SOLEIL
from .table_eclipses import format_duree, verifier

R_SOLEIL, R_TERRE, R_LUNE = 60.0, 22.0, 9.0           # rayons à l'écran (proportions de l'original, pas à l'échelle)
MARGE_SOLEIL = 8.0                                    # le Soleil est dessiné en entier, à 8 px du bord
INCLINAISON_LUNE = 5.145


def date_eclipse(e) -> str:
    nom = tr('anim_mois_%d' % e[1])
    return ('%d %s %d' % (e[2], nom, e[0])) if langue() == 'fr' else ('%d %s %d' % (e[2], nom, e[0]))


def rejeu(cle: str):
    """Géométrie d'une éclipse de la table (clé « S<i> » ou « L<i> »), en proportions réelles, ou None."""
    solaire = cle[:1] == 'S'
    table = SOLEIL if solaire else LUNE
    try:
        e = table[int(cle[1:])]
    except (ValueError, IndexError):
        return None
    v = verifier(e, solaire)
    f = math.radians(v['F'])
    y = astro.D_LUNE_KM * math.sin(math.radians(INCLINAISON_LUNE)) * math.sin(f)
    pente = math.tan(math.radians(INCLINAISON_LUNE)) * (1 if math.cos(f) >= 0 else -1) * 0.92
    RL, RT = astro.R_LUNE_KM, astro.R_TERRE_KM

    def borne(a, b):
        sg = 1 if y >= 0 else -1
        return sg * max(a, min(b, abs(y)))

    typ = e[3]
    if not solaire:
        o = astro.eclipse_de_lune()
        ru, rp = o['rayon_ombre_km'], o['rayon_penombre_km']
        if typ == 'total':
            y = borne(0, (ru - RL) * 0.9)
        elif typ == 'partial':
            y = borne(ru - RL + 150, ru + RL - 150)
        else:
            y = borne(ru + RL + 150, rp + RL - 150)
        return {'solaire': False, 'e': e, 'y_km': y, 'pente': pente, 'ru_km': ru, 'rp_km': rp,
                'demi_km': (rp + RL) * 1.08}
    c = astro.cones_ombre(astro.R_SOLEIL_KM, RL, astro.UA_KM)
    rp = c['rayon_penombre'](astro.D_LUNE_KM - RT)
    # l'ombre (totale) ou l'anti-ombre (annulaire) : son rayon dépend de la distance de la Lune (±5 %)
    ru = 70.0 if typ == 'total' else 15.0 if typ == 'hybrid' else -90.0
    y = borne(RT + 200, RT + rp - 200) if typ == 'partial' else borne(0, RT * 0.95)
    return {'solaire': True, 'e': e, 'y_km': y, 'pente': pente, 'ru_km': ru, 'rp_km': rp,
            'demi_km': (RT + rp) * 1.12}


def geometrie(sx, sy, ox, oy, r_source, r_objet, loin: float = 3000.0) -> dict:
    """Points des cônes d'ombre et de pénombre d'un disque (ox, oy, r_objet) éclairé par (sx, sy, r_source)."""
    d = math.hypot(ox - sx, oy - sy)
    ang = math.atan2(oy - sy, ox - sx)
    ca, sa = math.cos(ang), math.sin(ang)

    def rep(x, y):                          # repère (Soleil à l'origine, objet sur +x) → écran
        return QPointF(sx + ca * x - sa * y, sy + sa * x + ca * y)

    s_a = min(0.999, (r_source + r_objet) / d)
    a = math.asin(s_a)
    x2, y2 = d - r_objet * s_a, r_objet * math.cos(a)
    x3 = r_source / s_a
    x4, y4 = loin, (loin - x3) * math.tan(a)
    s_b = (r_source - r_objet) / d
    b = math.asin(s_b)
    x6, y6 = d + r_objet * s_b, r_objet * math.cos(b)
    x7 = d + r_objet / s_b
    y8 = (loin - x7) * math.tan(b)
    return {'penombre': [rep(x2, y2), rep(x4, y4), rep(x4, -y4), rep(x2, -y2)],
            'ombre': [rep(x6, y6), rep(x7, 0), rep(x6, -y6)],
            'antiombre': [rep(x7, 0), rep(loin, y8), rep(loin, -y8)],
            'axe': (ca, sa), 'd': d, 'sommet': x7 - d, 'k_ombre': s_b,
            'k_penombre': (r_source + r_objet) / d}


def type_eclipse(sx, sy, ox, oy, r_objet, cx, cy, r_cible) -> str:
    """Ombre portée par l'objet (ox, oy) sur la cible (cx, cy) : 'totale', 'annulaire', 'partielle',
    'penombre' ou ''."""
    d = math.hypot(ox - sx, oy - sy)
    ux, uy = (ox - sx) / d, (oy - sy) / d
    x = (cx - ox) * ux + (cy - oy) * uy                   # distance derrière l'objet, le long de l'axe
    if x <= 0:
        return ''
    dist = abs(-(cx - ox) * uy + (cy - oy) * ux)
    k_u = (R_SOLEIL - r_objet) / d
    k_p = (R_SOLEIL + r_objet) / d
    ru = r_objet - x * k_u
    rp = r_objet + x * k_p
    if dist - r_cible >= rp:
        return ''
    if ru > 0:
        if dist + r_cible <= ru:
            return 'totale'
        if dist - r_cible < ru:
            return 'partielle'
        return 'penombre'
    if dist < -ru - r_cible:                                # dans l'antiombre (le cône prolongé)
        return 'annulaire'
    return 'partielle' if dist - r_cible < -ru else 'penombre'


class OmbresEclipse(Animation):
    ID = 'shadowsim'
    ANIMEE = False

    def construire(self):
        self.terre = None
        self.lune = None
        self.c_reel = self.coche('reel', True)
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
        self._rect = None

    def _rejeu_change(self, *_):
        self.instant.setVisible(self.rejouer.currentData() != 'libre')
        self.instant.setValue(0.0)

    def rejeu(self):
        k = self.rejouer.currentData()
        return None if not k or k == 'libre' else rejeu(k)

    def etat_initial(self):
        self.terre = None
        self.lune = None

    def _positions(self, rect):
        if self.terre is None:
            self.terre = (0.55, 0.5)
            self.lune = (0.80, 0.5)
        t = QPointF(rect.x() + self.terre[0] * rect.width(), rect.y() + self.terre[1] * rect.height())
        lu = QPointF(rect.x() + self.lune[0] * rect.width(), rect.y() + self.lune[1] * rect.height())
        return t, lu

    def presser(self, pos, bouton):
        if self._rect is None:
            return False
        t, lu = self._positions(self._rect)
        for nom, q, r in (('lune', lu, R_LUNE), ('terre', t, R_TERRE)):
            if math.hypot(pos.x() - q.x(), pos.y() - q.y()) <= r + 6:
                self._glisse = lambda p, n=nom: self._tirer(n, p)
                return True
        return False

    def _tirer(self, nom, pos):
        r = self._rect
        x = (pos.x() - r.x()) / r.width()
        y = (pos.y() - r.y()) / r.height()
        sx = (R_SOLEIL + MARGE_SOLEIL) / r.width()
        x = max(sx + (R_SOLEIL + 30) / r.width(), min(0.98, x))
        y = max(0.02, min(0.98, y))
        setattr(self, nom, (x, y))

    def _eclipses(self):
        r = self._rect
        if r is None:
            return '', ''
        t, lu = self._positions(r)
        sx, sy = r.x() + R_SOLEIL + MARGE_SOLEIL, r.center().y()
        lunaire = type_eclipse(sx, sy, t.x(), t.y(), R_TERRE, lu.x(), lu.y(), R_LUNE)
        solaire = type_eclipse(sx, sy, lu.x(), lu.y(), R_LUNE, t.x(), t.y(), R_TERRE)
        return lunaire, solaire

    def valeurs(self):
        lunaire, solaire = self._eclipses()
        e = astro.eclipse_de_lune()
        out = [(tr('anim_shadowsim_lunaire'), tr('anim_shadowsim_' + (lunaire or 'aucune'))),
               (tr('anim_shadowsim_solaire'), tr('anim_shadowsim_' + (solaire or 'aucune')))]
        if self.c_reel.isChecked():
            out += [(tr('anim_shadowsim_rayon_ombre'), '%s km (%s × %s)' % (
                        nombre(e['rayon_ombre_km'], 0), nombre(e['ombre_en_diametres_lunaires'], 2),
                        tr('anim_shadowsim_diam_lune'))),
                    (tr('anim_shadowsim_longueur_ombre'), '%s km' % nombre(e['longueur_ombre_km'], 0)),
                    (tr('anim_shadowsim_totalite'), duree_hm(e['totalite_h'])),
                    (tr('anim_shadowsim_phase_ombre'), duree_hm(e['ombre_totale_h']))]
        rj = self.rejeu()
        if rj:
            ec = rj['e']
            out += [(tr('anim_shadowsim_rejouee'), '%s · %s, %s' % (
                        date_eclipse(ec), tr('anim_shadowsim_soleil' if rj['solaire'] else 'anim_shadowsim_lune_t'),
                        tr('anim_eclipsetable_t_' + ec[3]))),
                    (tr('anim_eclipsetable_grandeur'), nombre(ec[5], 3)),
                    (tr('anim_eclipsetable_duree'), format_duree(ec[6])),
                    (tr('anim_shadowsim_ecart'), '%s km %s' % (nombre(abs(rj['y_km']), 0),
                                                              tr('anim_pc_n' if rj['y_km'] >= 0 else 'anim_pc_s')))]
        return out

    def dessiner(self, p, rect):
        rj = self.rejeu()
        reel = self.c_reel.isChecked() or rj is not None
        principal = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * (0.72 if reel else 1.0))
        self._rect = principal
        t, lu = self._positions(principal)
        sx, sy = principal.x() + R_SOLEIL + MARGE_SOLEIL, principal.center().y()
        p.save()
        p.setClipRect(principal)
        for (ox, oy), r in (((t.x(), t.y()), R_TERRE), ((lu.x(), lu.y()), R_LUNE)):
            g = geometrie(sx, sy, ox, oy, R_SOLEIL, r)
            p.setPen(dessin.stylo('grille', 0.8, 0.6))
            p.setBrush(dessin.c('penombre', 0.22))
            p.drawPolygon(QPolygonF(g['penombre']))
            p.setBrush(dessin.c('umbra', 0.85))
            p.drawPolygon(QPolygonF(g['ombre']))
            p.setPen(dessin.stylo('grille', 1.0, 0.8, pointille=True))
            a = g['antiombre']
            p.drawLine(a[0], a[1])
            p.drawLine(a[0], a[2])
        dessin.disque(p, sx, sy, R_SOLEIL, 'soleil')
        dessin.disque(p, t.x(), t.y(), R_TERRE, 'terre', bord='texte')
        dessin.disque(p, lu.x(), lu.y(), R_LUNE, 'lune', bord='texte')
        p.restore()
        dessin.texte(p, t.x(), t.y() - R_TERRE - 10, tr('anim_shadowsim_terre'), fond=True)
        dessin.texte(p, lu.x(), lu.y() - R_LUNE - 10, tr('anim_shadowsim_lune'), fond=True)
        bas = QRectF(rect.x(), principal.bottom(), rect.width(), rect.height() - principal.height())
        if rj:
            self._rejouer(p, bas, rj)
        elif reel:
            self._aristarque(p, bas)

    def _rejouer(self, p, r0, rj):
        """L'éclipse choisie dans la table, en proportions réelles ; l'instant fait avancer la Lune ou son ombre."""
        r = dessin.cadre(p, r0, tr('anim_shadowsim_titre_soleil' if rj['solaire'] else 'anim_shadowsim_titre_lune',
                                   date=date_eclipse(rj['e'])))
        RL, RT = astro.R_LUNE_KM, astro.R_TERRE_KM
        demi_h = max(rj['rp_km'] + (0 if rj['solaire'] else RL), RT) * 1.08 + abs(rj['y_km'])
        k = min(r.width() / (2 * rj['demi_km']), r.height() / (2 * demi_h))
        cx, cy = r.center().x(), r.center().y()
        t = self.instant.value()
        # la Lune va d'ouest en est : vers la gauche dans le ciel (éclipse de Lune), vers l'est sur la carte (Soleil)
        sens = 1 if rj['solaire'] else -1

        def pos(u):
            return QPointF(cx + sens * u * rj['demi_km'] * k * 0.9,
                           cy - (rj['y_km'] + rj['pente'] * u * rj['demi_km'] * 0.9) * k)

        p.save()
        p.setClipRect(r)
        p.setPen(dessin.stylo('doux', 1.0, 0.7, True))
        p.drawLine(pos(-1), pos(1))
        a, b = pos(0.82), pos(1)
        dessin.fleche(p, a.x(), a.y(), b.x(), b.y(), dessin.stylo('doux', 1.2, 0.8), 7)
        if not rj['solaire']:
            dessin.disque(p, cx, cy, rj['rp_km'] * k, 'penombre', alpha=0.25)
            dessin.disque(p, cx, cy, rj['ru_km'] * k, 'umbra', alpha=0.88)
            for u in (-1, 1):
                q = pos(u)
                p.setPen(dessin.stylo('lune', 1.0, 0.5))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawEllipse(q, RL * k, RL * k)
            q = pos(t)
            dessin.disque(p, q.x(), q.y(), RL * k, 'lune', bord='texte')
            p.save()                                       # la partie de la Lune dans l'ombre
            ch = QPainterPath()
            ch.addEllipse(q, RL * k, RL * k)
            p.setClipPath(ch, dessin.Qt.ClipOperation.IntersectClip)
            dessin.disque(p, cx, cy, rj['ru_km'] * k, 'arc2', alpha=0.55)
            p.restore()
        else:
            dessin.disque(p, cx, cy, RT * k, 'terre', bord='texte')
            q = pos(t)
            p.save()
            ch = QPainterPath()
            ch.addEllipse(QPointF(cx, cy), RT * k, RT * k)
            p.setClipPath(ch, dessin.Qt.ClipOperation.IntersectClip)
            dessin.disque(p, q.x(), q.y(), rj['rp_km'] * k, 'umbra', alpha=0.35)
            if rj['ru_km'] > 0:
                dessin.disque(p, q.x(), q.y(), max(2.5, rj['ru_km'] * k), 'umbra', alpha=0.95)
            p.restore()
            p.setPen(dessin.stylo('penombre', 1.0, 0.8, True))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(q, rj['rp_km'] * k, rj['rp_km'] * k)
            if rj['ru_km'] < 0:
                p.setPen(dessin.stylo('accent1', 1.4))
                rr = max(3.0, -rj['ru_km'] * k)
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
