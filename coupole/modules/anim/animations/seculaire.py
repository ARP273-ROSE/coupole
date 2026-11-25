"""Précession séculaire d'une orbite qui croise celle de la Terre : sous l'effet des planètes géantes, la ligne des
apsides d'un géocroiseur avance et sa ligne des nœuds recule (théorie de Laplace-Lagrange) ; ses nœuds passent tour à
tour sur l'orbite terrestre, quatre fois par tour de ω : ce n'est qu'à ces époques qu'une collision est possible.
Orbite vue du pôle de l'écliptique, distances des nœuds et distance minimale entre les orbites au fil des millénaires.
Calculs : ``seculaire.py``."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from ....core.i18n import tr
from .. import dessin, seculaire as sc
from ..base import Animation, angle, nombre
from ..graphe import Axes
from .precession import an

DUREE_TOUR_OMEGA_S = 30.0        # secondes réelles pour un tour de ω (vitesse × 1)
SEUIL_PHA = 0.05                 # ua : MOID d'un astéroïde potentiellement dangereux (définition du CNEOS)


class Seculaire(Animation):
    ID = 'secularprecession'
    LECTURE_AU_DEPART = True

    def construire(self):
        self.objet = self.choix('objet', [('anim_secularprecession_o_' + k, k) for k, *_ in sc.OBJETS], 'apollo')
        self.a = self.curseur('a', 0.6, 3.0, 1.47, dec=2, unite='ua')
        self.e = self.curseur('e', 0.0, 0.95, 0.56, dec=3)
        self.i = self.curseur('i', 0.0, 40.0, 6.35, dec=2, unite='°')
        self.o0 = self.curseur('o0', 0.0, 360.0, 35.5, dec=1, unite='°')
        self.w0 = self.curseur('w0', 0.0, 360.0, 286.0, dec=1, unite='°')
        self.bouton('anim_secularprecession_aujourdhui', self.aujourdhui)
        self.bouton('anim_secularprecession_suivant', self.suivant)
        self._objet = self.objet.currentData()
        self._table = None
        self.t = 0.0

    # ------------------------------------------------------------ état
    def aujourdhui(self):
        self.t = 0.0
        self.rafraichir()

    def suivant(self):
        """Saute au prochain croisement (un nœud sur l'orbite terrestre)."""
        A = self.freq()
        c = sc.croisements(self.a.value(), self.e.value(), self.w0.value(), A, self.t + 1e-6, self.t + math.pi / A + 1.0)
        if c:
            self.t = c[0][0]
        self.rafraichir()

    def reglage_change(self):
        k = self.objet.currentData()
        if k != getattr(self, '_objet', k):
            self._objet = k
            for cle, a, e, i, o, w in sc.OBJETS:
                if cle == k:
                    for r, v in ((self.a, a), (self.e, e), (self.i, i), (self.o0, o), (self.w0, w)):
                        r.setValue(v)
            self.t = 0.0
        super().reglage_change()

    def freq(self) -> float:
        return sc.frequence(self.a.value())

    def periode(self) -> float:
        return 2.0 * math.pi / self.freq()

    def avancer(self, dt):
        self.t = math.fmod(self.t + dt * self.periode() / 2.0 / DUREE_TOUR_OMEGA_S, self.periode())

    def etat(self):
        return sc.angles(self.w0.value(), self.o0.value(), self.freq(), self.t)

    def table(self):
        cle = (self.a.value(), self.e.value(), self.i.value())
        if self._table is None or self._table[0] != cle:
            self._table = (cle, sc.table_moid(*cle))
        return self._table[1]

    # ------------------------------------------------------------ valeurs
    def valeurs(self):
        a, e, i = self.a.value(), self.e.value(), self.i.value()
        A = self.freq()
        w, o, _ = self.etat()
        ra, rd = sc.noeuds(a, e, w)
        c = sc.croisements(a, e, self.w0.value(), A, self.t, self.t + math.pi / A + 1.0)
        if c:
            prochain = tr('anim_secularprecession_prochain', an=an(int(round(sc.AN_DEPART + c[0][0]))),
                          noeud=tr('anim_secularprecession_n_' + c[0][1]))
        else:
            prochain = tr('anim_secularprecession_jamais')
        return [(tr('anim_secularprecession_v_date'), tr('anim_secularprecession_an', an=an(int(round(sc.AN_DEPART + self.t))))),
                (tr('anim_secularprecession_v_vitesse'), tr('anim_secularprecession_sec_an',
                                                            x=nombre(A * sc.SEC_PAR_RAD, 2))),
                (tr('anim_secularprecession_v_tour'), tr('anim_secularprecession_ans', n=nombre(2.0 * math.pi / A, 0))),
                (tr('anim_secularprecession_v_tour_w'), tr('anim_secularprecession_ans', n=nombre(math.pi / A, 0))),
                (tr('anim_secularprecession_v_angles'), tr('anim_secularprecession_deux', a=angle(w, 1), b=angle(o, 1))),
                (tr('anim_secularprecession_v_noeuds'), tr('anim_secularprecession_ua', x=tr('anim_secularprecession_deux', a=nombre(ra, 3), b=nombre(rd, 3)))),
                (tr('anim_secularprecession_v_moid'), tr('anim_secularprecession_ua', x=nombre(sc.moid(a, e, i, w), 4))),
                (tr('anim_secularprecession_v_prochain'), prochain)]

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 2, 0.52)
        self._vue(p, dessin.cadre(p, z[0], tr('anim_secularprecession_t_vue')))
        self._noeuds(p, dessin.cadre(p, z[1], tr('anim_secularprecession_t_noeuds')))
        self._moid(p, dessin.cadre(p, z[2], tr('anim_secularprecession_t_moid')))

    def _vue(self, p, r):
        a, e, i = self.a.value(), self.e.value(), self.i.value()
        w, o, varpi = self.etat()
        demi = max(1.7, min(a * (1.0 + e), 4.0)) * 1.08
        k = min(r.width(), r.height() - 8) / (2.0 * demi)
        cx, cy = r.center().x(), r.center().y() + 4
        p.save()
        p.setClipRect(r)
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.setPen(dessin.stylo('terre', 1.6))
        p.drawEllipse(QPointF(cx, cy), k, k)
        p.setPen(dessin.stylo('mars', 1.0, 0.6, pointille=True))
        p.drawEllipse(QPointF(cx, cy), 1.524 * k, 1.524 * k)
        pts = sc.orbite(a, e, i, o, w)
        for j in range(len(pts) - 1):
            x0, y0, z0 = pts[j]
            x1, y1, _ = pts[j + 1]
            p.setPen(dessin.stylo('accent1', 2.0) if z0 >= 0.0 else dessin.stylo('accent1', 1.4, 0.7, pointille=True))
            p.drawLine(QPointF(cx + k * x0, cy - k * y0), QPointF(cx + k * x1, cy - k * y1))
        # ligne des nœuds et nœuds
        ra, rd = sc.noeuds(a, e, w)
        orad = math.radians(o)
        xa, ya = ra * math.cos(orad), ra * math.sin(orad)
        xd, yd = -rd * math.cos(orad), -rd * math.sin(orad)
        p.setPen(dessin.stylo('doux', 1.0, 0.8, pointille=True))
        p.drawLine(QPointF(cx + k * xa, cy - k * ya), QPointF(cx + k * xd, cy - k * yd))
        dessin.disque(p, cx + k * xa, cy - k * ya, 5.0, 'accent2', 'texte')
        dessin.disque(p, cx + k * xd, cy - k * yd, 5.0, 'accent3', 'texte')
        dessin.etiquette(p, cx + k * xa, cy - k * ya, '☊')
        dessin.etiquette(p, cx + k * xd, cy - k * yd, '☋')
        # périhélie
        q = a * (1.0 - e)
        vr = math.radians(varpi)
        dessin.fleche(p, cx, cy, cx + k * q * math.cos(vr), cy - k * q * math.sin(vr), dessin.stylo('accent1', 1.4), 6.0)
        dessin.disque(p, cx, cy, 6.0, 'soleil')
        p.restore()
        dessin.texte(p, r.left() + 6, r.bottom() - 10, tr('anim_secularprecession_legende_vue'), 'doux', centre=False,
                     fond=True)

    def _axe_t(self, r, y0, y1):
        T = self.periode() / 1000.0
        return Axes(r, 0.0, T, y0, y1, marges=(44, 8, 10, 30))

    def _noeuds(self, p, r):
        a, e = self.a.value(), self.e.value()
        A = self.freq()
        ymax = min(4.0, a * (1.0 + e)) * 1.05
        ax = self._axe_t(r, 0.0, ymax).avec(p)
        ax.fond(p, tr('anim_secularprecession_axe_t'), tr('anim_secularprecession_axe_r'))
        T = self.periode()
        for genre, cle in (('asc', 'accent2'), ('desc', 'accent3')):
            pts = []
            for j in range(201):
                t = T * j / 200.0
                w = (self.w0.value() + 2.0 * math.degrees(A * t)) % 360.0
                ra, rd = sc.noeuds(a, e, w)
                pts.append((t / 1000.0, min(ra if genre == 'asc' else rd, ymax)))
            ax.courbe(pts, cle, 1.6)
        ax.horizontale(1.0, 'terre', 1.4, False, tr('anim_secularprecession_terre'))
        for t, genre in sc.croisements(a, e, self.w0.value(), A, 0.0, T):
            dessin.disque(p, ax.px(t / 1000.0), ax.py(1.0), 3.5, 'accent2' if genre == 'asc' else 'accent3')
        ax.verticale(self.t / 1000.0, 'texte', 1.2, False)

    def _moid(self, p, r):
        tb = self.table()
        ymax = max(max(tb) * 1.08, 2.0 * SEUIL_PHA)
        ax = self._axe_t(r, 0.0, ymax).avec(p)
        ax.fond(p, tr('anim_secularprecession_axe_t'), tr('anim_secularprecession_axe_moid'))
        n = len(tb) - 1
        T = self.periode()
        A = self.freq()
        pts = []
        for j in range(201):
            t = T * j / 200.0
            w = (self.w0.value() + 2.0 * math.degrees(A * t)) % 360.0
            x = w / 360.0 * n
            k0 = min(int(x), n - 1)
            f = x - k0
            pts.append((t / 1000.0, tb[k0] * (1.0 - f) + tb[k0 + 1] * f))
        ax.remplir(pts, 'accent1', 0.25, 0.0)
        ax.courbe(pts, 'accent1', 1.6)
        ax.horizontale(SEUIL_PHA, 'accent3', 1.0, True, tr('anim_secularprecession_pha'))
        ax.verticale(self.t / 1000.0, 'texte', 1.2, False)
