"""Phénomènes mutuels des satellites galiléens : quand la Terre et le Soleil passent dans le plan de leurs orbites (tous
les six ans), un satellite peut en occulter un autre (vu de la Terre) ou lui faire de l'ombre (vu du Soleil).  Les deux
disques vus de la Terre (ombre et pénombre en cas d'éclipse), le système vu du nord avec les directions de la Terre et
du Soleil, courbe de lumière de la paire.  Calculs : ``mutuels.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath

from ....core.i18n import tr
from .. import dessin, mutuels as mu
from ..base import Animation, angle, nombre
from ..graphe import Axes

DUREE_FENETRE_S = 12.0           # secondes réelles pour parcourir la fenêtre tracée (vitesse × 1)
COULEURS = {'io': 'accent1', 'europe': 'lune', 'ganymede': 'ecliptique', 'callisto': 'meridien'}


class Mutuels(Animation):
    ID = 'mutualevents'
    LECTURE_AU_DEPART = True

    def construire(self):
        opts = [('anim_mutualevents_s_' + s[0], s[0]) for s in mu.SATELLITES]
        self.actif = self.choix('actif', opts, 'europe')
        self.passif = self.choix('passif', opts, 'io')
        self.genre = self.choix('genre', [('anim_mutualevents_g_occultation', 'occultation'),
                                          ('anim_mutualevents_g_eclipse', 'eclipse')], 'occultation')
        self.B = self.curseur('B', 0.0, 1.5, 0.1, dec=3, unite='°')
        self.phase = self.curseur('phase', 0.0, 11.0, 8.0, dec=1, unite='°')
        self.fx = self.curseur('fx', -0.95, 0.95, 0.5, dec=2)
        self.t = 0.0
        self._cache = None

    # ------------------------------------------------------------ état
    def paire(self) -> tuple[str, str]:
        a, p = self.actif.currentData(), self.passif.currentData()
        if a == p:                                   # un satellite ne s'occulte pas lui-même : on prend le voisin
            cles = [s[0] for s in mu.SATELLITES]
            p = cles[(cles.index(a) + 1) % len(cles)]
        return a, p

    def rencontre(self):
        a, p = self.paire()
        cle = (a, p, self.genre.currentData(), self.B.value(), self.phase.value(), self.fx.value())
        if self._cache is None or self._cache[0] != cle:
            r = mu.Rencontre(*cle)
            c = r.courbe()
            self._cache = (cle, r, c, mu.resume(c))
        return self._cache[1:]

    def avancer(self, dt):
        r, c, _ = self.rencontre()
        T = r.demi_fenetre()
        self.t = (self.t + T + dt * 2.0 * T / DUREE_FENETRE_S) % (2.0 * T) - T

    def notation(self) -> str:
        a, p = self.paire()
        # « 2E1 » avec des espaces fines insécables (règle typographique : jamais « chiffre E chiffre »)
        return '%d\u202f%s\u202f%d' % (mu.satellite(a)[1], 'O' if self.genre.currentData() == 'occultation' else 'E',
                                       mu.satellite(p)[1])

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        r, c, (fmin, _, duree) = self.rencontre()
        a, p = self.paire()
        T = r.demi_fenetre()
        t = max(-T, min(T, self.t))
        phrase = tr('anim_mutualevents_phrase_' + self.genre.currentData(), a=tr('anim_mutualevents_s_' + a),
                    p=tr('anim_mutualevents_s_' + p))
        if duree > 0.0:
            baisse = tr('anim_mutualevents_baisse', pc=nombre(100.0 * (1.0 - fmin), 1),
                        dm=nombre(-2.5 * math.log10(fmin), 2))
            duree_txt = tr('anim_mutualevents_min', n=nombre(duree, 1))
        else:
            baisse = tr('anim_mutualevents_rien')
            duree_txt = '—'
        return [(tr('anim_mutualevents_v_phenomene'), tr('anim_mutualevents_notation', n=self.notation(), p=phrase)),
                (tr('anim_mutualevents_v_instant'), tr('anim_mutualevents_min', n=nombre(t, 1))),
                (tr('anim_mutualevents_v_eclat'), tr('anim_mutualevents_pc', x=nombre(100.0 * r.flux(t), 1))),
                (tr('anim_mutualevents_v_impact'), tr('anim_mutualevents_km', n=nombre(r.parametre_impact(), 0))),
                (tr('anim_mutualevents_v_vitesse'), tr('anim_mutualevents_kms', n=nombre(r.vitesse_relative() / 60.0, 2))),
                (tr('anim_mutualevents_v_duree'), duree_txt),
                (tr('anim_mutualevents_v_baisse'), baisse),
                (tr('anim_mutualevents_v_blim'), angle(r.b_limite(), 3))]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.5)
        self._ciel(p, dessin.cadre(p, z[0], tr('anim_mutualevents_t_ciel')))
        self._systeme(p, dessin.cadre(p, z[1], tr('anim_mutualevents_t_systeme')))
        self._courbe(p, dessin.cadre(p, z[2], tr('anim_mutualevents_t_courbe')))

    def _ciel(self, p, r):
        rc, _, _ = self.rencontre()
        a, ps = self.paire()
        T = rc.demi_fenetre()
        t = max(-T, min(T, self.t))
        Pa, Pp = rc.positions(t)
        xa, ya, _ = rc.ciel(Pa, 0.0)
        xp, yp, _ = rc.ciel(Pp, 0.0)
        champ = 3.2 * (rc.ra + rc.rp)                       # largeur (km) du champ montré
        k = min(r.width(), r.height() - 30) / champ
        cx, cy = r.center().x(), r.center().y() + 6
        p.save()
        p.setClipRect(r)
        sp = (cx, cy)
        sa = (cx + k * (xa - xp), cy - k * (ya - yp))
        ecl = self.genre.currentData() == 'eclipse'
        dessin.astre(p, sp[0], sp[1], k * rc.rp, COULEURS[ps])
        if ecl:
            # ombre portée : centres vus du Soleil, rapportés au disque passif
            xas, yas, zas = rc.ciel(Pa, rc.psi)
            xps, yps, zps = rc.ciel(Pp, rc.psi)
            ell = zas - zps
            if ell > 0.0:
                rho = mu.R_SOLEIL / mu.D_JUPITER
                ox, oy = cx + k * (xas - xps), cy - k * (yas - yps)
                chemin = QPainterPath()
                chemin.addEllipse(QPointF(*sp), k * rc.rp, k * rc.rp)
                p.save()
                p.setClipPath(chemin)
                p.setPen(dessin.Qt.PenStyle.NoPen)
                p.setBrush(dessin.c('penombre', 0.55))
                p.drawEllipse(QPointF(ox, oy), k * (rc.ra + ell * rho), k * (rc.ra + ell * rho))
                if rc.ra > ell * rho:
                    p.setBrush(dessin.c('umbra', 0.85))
                    p.drawEllipse(QPointF(ox, oy), k * (rc.ra - ell * rho), k * (rc.ra - ell * rho))
                p.restore()
        dessin.astre(p, sa[0], sa[1], k * rc.ra, COULEURS[a])
        p.restore()
        dessin.etiquette(p, sp[0], sp[1] - k * rc.rp, tr('anim_mutualevents_s_' + ps))
        dessin.etiquette(p, sa[0], sa[1] - k * rc.ra, tr('anim_mutualevents_s_' + a))
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_mutualevents_legende_ciel'), 'doux', centre=False,
                     fond=True)

    def _systeme(self, p, r):
        rc, _, _ = self.rencontre()
        a, ps = self.paire()
        T = rc.demi_fenetre()
        t = max(-T, min(T, self.t))
        amax = max(rc.aa, rc.ap) * 1.12
        k = min(r.width(), r.height() - 12) / (2.0 * amax)
        cx, cy = r.center().x(), r.center().y() + 4
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        for cle, rr in ((a, rc.aa), (ps, rc.ap)):
            p.setPen(dessin.stylo('grille', 1.0))
            p.drawEllipse(QPointF(cx, cy), k * rr, k * rr)
        dessin.astre(p, cx, cy, max(3.0, k * mu.R_JUPITER), 'ecliptique')
        Pa, Pp = rc.positions(t)
        # vue du nord : X à droite, Y (en s'éloignant de la Terre) vers le haut ; la Terre est en bas
        for cle, P in ((a, Pa), (ps, Pp)):
            dessin.disque(p, cx + k * P[0], cy - k * P[1], 4.5, COULEURS[cle], 'texte')
        L = 0.92 * min(r.width(), r.height()) / 2.0
        dessin.fleche(p, cx, cy + 0.42 * L, cx, cy + 0.78 * L, dessin.stylo('terre', 1.6), 6.0)
        dessin.etiquette(p, cx, cy + 0.78 * L, tr('anim_mutualevents_terre'), 'terre')
        if self.genre.currentData() == 'eclipse':
            s, c = math.sin(rc.psi), math.cos(rc.psi)
            x0, y0 = cx + 0.42 * L * s, cy + 0.42 * L * c
            dessin.fleche(p, x0, y0, cx + 0.78 * L * s, cy + 0.78 * L * c, dessin.stylo('soleil', 1.6), 6.0)
            dessin.etiquette(p, cx + 0.78 * L * s, cy + 0.78 * L * c, tr('anim_mutualevents_soleil'), 'soleil')
        p.restore()

    def _courbe(self, p, r):
        rc, c, (fmin, _, _) = self.rencontre()
        T = rc.demi_fenetre()
        y0 = max(0.0, min(0.9, fmin - 0.08))
        ax = Axes(r, -T, T, y0, 1.03, marges=(44, 8, 10, 30)).avec(p)
        ax.fond(p, tr('anim_mutualevents_axe_t'), tr('anim_mutualevents_axe_f'))
        ax.courbe(c, 'accent1', 1.8)
        t = max(-T, min(T, self.t))
        ax.verticale(t, 'texte', 1.2, False)
        dessin.disque(p, ax.px(t), ax.py(rc.flux(t)), 4.5, 'accent3', 'texte')
