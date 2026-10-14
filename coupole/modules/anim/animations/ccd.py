"""CCD Simulator : un capteur CCD est une grille de « seaux » (pixels) qui recueillent les photons pendant la pose,
comme des seaux sous la pluie ; chaque photon libère un électron.  À la lecture, les charges glissent ligne par
ligne vers un registre, puis case par case vers un amplificateur qui les mesure une à une : on reconstruit l'image.
Les photons arrivent au hasard (loi de Poisson) : un pixel qui reçoit N photons en moyenne fluctue de √N.
Grille de 4 × 5 comme l'original, avec une étoile et le fond du ciel, et la saturation des pixels pleins."""
from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre

LIGNES, COLONNES = 4, 5
PUITS = 10_000                       # capacité d'un pixel (électrons)
PAS_LECTURE_S = 0.35


def poisson(alea: random.Random, lam: float) -> int:
    """Tirage de Poisson (Knuth pour les petites moyennes, approximation normale au-delà de 50)."""
    if lam <= 0:
        return 0
    if lam > 50:
        return max(0, int(round(alea.gauss(lam, math.sqrt(lam)))))
    l, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= alea.random()
        if p <= l:
            return k
        k += 1


def taux(i: int, j: int, etoile: float, ciel: float) -> float:
    """Photons par seconde attendus dans le pixel (i, j) : fond du ciel + étoile (profil gaussien centré entre les
    pixels (1, 2) et (2, 2), largeur 0,8 pixel)."""
    di, dj = i - 1.4, j - 2.1
    return ciel + etoile * math.exp(-(di * di + dj * dj) / (2 * 0.8 ** 2)) / (2 * math.pi * 0.8 ** 2)


class CCD(Animation):
    ID = 'buckets'

    def construire(self):
        self.pose = self.curseur('pose', 1.0, 60.0, 10.0, dec=0, unite='s')
        self.etoile = self.curseur('etoile', 0.0, 5000.0, 1500.0, dec=0, unite='ph/s')
        self.ciel = self.curseur('ciel', 0.0, 200.0, 20.0, dec=0, unite='ph/s')
        self.bouton('anim_buckets_poser', self.poser)
        self.bouton('anim_buckets_lire', self.lire)
        self.etat_initial()

    def etat_initial(self):
        self.alea = random.Random(17)
        self._pluie = random.Random(23)                 # dessin de la pluie seulement (n'influe pas sur les mesures)
        self.charges = [[0.0] * COLONNES for _ in range(LIGNES)]
        self.registre = [None] * COLONNES
        self.lues = [[None] * COLONNES for _ in range(LIGNES)]
        self.mode = 'repos'
        self.t_pose = 0.0
        self.t_lecture = 0.0
        self.lignes_descendues = 0
        self.dans_registre = None

    def poser(self):
        self.etat_initial()
        self.mode = 'pose'
        if not self.en_lecture:
            self.basculer_lecture()

    def lire(self):
        if self.mode in ('pose', 'repos'):
            self.mode = 'lecture'
            self.t_lecture = 0.0
            if not self.en_lecture:
                self.basculer_lecture()

    def avancer(self, dt):
        if self.mode == 'pose':
            reste = self.pose.value() - self.t_pose
            h = min(dt * 2.0, reste)                      # la pose défile deux fois plus vite que le temps réel
            for i in range(LIGNES):
                for j in range(COLONNES):
                    self.charges[i][j] = min(PUITS, self.charges[i][j] +
                                             poisson(self.alea, taux(i, j, self.etoile.value(), self.ciel.value()) * h))
            self.t_pose += h
            if self.t_pose >= self.pose.value() - 1e-9:
                self.mode = 'lecture'
                self.t_lecture = 0.0
        elif self.mode == 'lecture':
            self.t_lecture += dt
            while self.t_lecture >= PAS_LECTURE_S and self.mode == 'lecture':
                self.t_lecture -= PAS_LECTURE_S
                self._pas_lecture()

    def _pas_lecture(self):
        if all(c is None for c in self.registre):
            if self.lignes_descendues >= LIGNES:
                self.mode = 'fini'
                return
            # les charges descendent d'une ligne ; la ligne du bas entre dans le registre
            self.registre = [(j, q) for j, q in enumerate(self.charges[LIGNES - 1])]
            self.dans_registre = LIGNES - 1 - self.lignes_descendues
            self.charges = [[0.0] * COLONNES] + self.charges[:LIGNES - 1]
            self.lignes_descendues += 1
        else:
            # le registre glisse d'une case vers la droite : la dernière passe dans l'amplificateur et est mesurée
            dernier = self.registre[-1]
            if dernier is not None:
                col, q = dernier
                self.lues[self.dans_registre][col] = int(q)
            self.registre = [None] + self.registre[:-1]

    def valeurs(self):
        lues = [v for ligne in self.lues for v in ligne if v is not None]
        etat = tr('anim_buckets_m_' + self.mode)
        out = [(tr('anim_buckets_etat'), etat), (tr('anim_buckets_t_pose'), '%s s' % nombre(self.t_pose, 1))]
        attendu = sum(taux(i, j, self.etoile.value(), self.ciel.value()) for i in range(LIGNES)
                      for j in range(COLONNES)) * self.pose.value()
        out.append((tr('anim_buckets_attendu'), '%s e⁻ (± %s)' % (nombre(attendu, 0), nombre(math.sqrt(attendu), 0))))
        if lues:
            out.append((tr('anim_buckets_lus'), '%d / %d' % (len(lues), LIGNES * COLONNES)))
        return out

    def dessiner(self, p, rect):
        z = dessin.zones(rect, 2, 0.95)
        r = dessin.cadre(p, z[0], tr('anim_buckets_titre_ccd'))
        cw = min(r.width() / (COLONNES + 1.6), r.height() / (LIGNES + 2.4))
        x0 = r.left() + (r.width() - cw * (COLONNES + 1.2)) / 2
        y0 = r.top() + 6
        for i in range(LIGNES):
            for j in range(COLONNES):
                self._seau(p, QRectF(x0 + j * cw, y0 + i * cw, cw * 0.9, cw * 0.9), self.charges[i][j])
        yr = y0 + LIGNES * cw + cw * 0.3
        for j in range(COLONNES):
            c = self.registre[j]
            self._seau(p, QRectF(x0 + j * cw, yr, cw * 0.9, cw * 0.9), c[1] if c else 0.0,
                       'accent2' if c is not None else 'grille')
        dessin.texte(p, x0 + COLONNES * cw / 2, yr + cw * 1.05, tr('anim_buckets_registre'), 'doux')
        xa = x0 + COLONNES * cw + cw * 0.15
        dessin.disque(p, xa + cw * 0.35, yr + cw * 0.45, cw * 0.35, 'accent1', bord='texte')
        dessin.texte(p, xa + cw * 0.35, yr - 10, tr('anim_buckets_ampli'), 'accent1')
        if self.mode == 'pose':
            p.setPen(dessin.stylo('equateur', 1.0, 0.6))
            for k in range(40):
                x = x0 + self._pluie.random() * COLONNES * cw
                y = y0 + self._pluie.random() * LIGNES * cw
                p.drawLine(QPointF(x, y), QPointF(x - 2, y - 7))
        # image reconstruite
        r2 = dessin.cadre(p, z[1], tr('anim_buckets_titre_image'))
        cw2 = min(r2.width() / (COLONNES + 0.4), r2.height() / (LIGNES + 0.4))
        x2 = r2.left() + (r2.width() - cw2 * COLONNES) / 2
        mx = max([v for ligne in self.lues for v in ligne if v is not None] + [1])
        dessin.police(p, 0.85)
        for i in range(LIGNES):
            for j in range(COLONNES):
                v = self.lues[i][j]
                q = QRectF(x2 + j * cw2, r2.top() + i * cw2, cw2 - 2, cw2 - 2)
                if v is None:
                    p.fillRect(q, dessin.c('sphere', 0.4))
                    continue
                g = int(255 * (v / mx) ** 0.5)
                p.fillRect(q, QColor(g, g, g))
                fm = p.fontMetrics()
                t = nombre(v, 0)
                p.setPen(QColor(200, 40, 40) if v >= PUITS else (QColor(15, 15, 15) if g > 140 else QColor(240, 240, 240)))
                p.drawText(QPointF(q.center().x() - fm.horizontalAdvance(t) / 2, q.center().y() + fm.ascent() / 2 - 1), t)
        dessin.police(p, 1 / 0.85)

    @staticmethod
    def _seau(p, q, charge, cle='doux'):
        p.setPen(dessin.stylo(cle, 1.2))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawRect(q)
        f = min(1.0, charge / PUITS)
        if f > 0:
            p.fillRect(QRectF(q.left() + 1, q.bottom() - f * q.height(), q.width() - 2, f * q.height()),
                       dessin.c('accent3' if f >= 1 else 'equateur', 0.75))
