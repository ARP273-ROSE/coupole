"""Big Dipper 3D : les sept étoiles de la Grande Ourse sont à des distances très différentes (de 78 à 124
années-lumière) ; vues de la Terre, elles se projettent sur la sphère céleste en l'astérisme familier.  Tourner la
vue montre qu'il n'y a aucune figure dans l'espace.  Positions J2000 et distances (années-lumière, parallaxes
Hipparcos) reprises de l'original."""
from __future__ import annotations

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, nombre

# (nom, α en heures, δ en degrés, distance en années-lumière, incertitude)
ETOILES = (('Dubhe', 11.06215, 61.75092, 123.6, 2.5), ('Merak', 11.03068, 56.38236, 79.4, 1.2),
           ('Phecda', 11.89717, 53.69475, 83.7, 1.5), ('Megrez', 12.25709, 57.03258, 81.4, 1.2),
           ('Alioth', 12.90048, 55.95989, 80.9, 1.2), ('Mizar', 13.39875, 54.92539, 78.2, 1.1),
           ('Alkaid', 13.79235, 49.31336, 100.7, 2.3))
TRAITS = ((0, 1), (1, 2), (2, 3), (3, 0), (3, 4), (4, 5), (5, 6))
RAYON_AL = 250.0                       # rayon de la sphère céleste dessinée, en années-lumière (comme l'original)
CENTRE = np.array(astro.vecteur_equatorial(15 * 12.5, 55.0))


class GrandeOurse(Animation):
    ID = 'bigdipper'
    ANIMEE = False

    def construire(self):
        # vue de côté : la ligne de visée Terre → constellation (α = 12,5 h, δ = 55°) traverse l'écran
        self.vue3d = self.vue(262.5, 15.0, -89.0, 89.0)
        self.c_lignes = self.coche('lignes', True)
        self.c_noms = self.coche('noms', True)
        self.c_sphere = self.coche('sphere', True)

    def valeurs(self):
        return [(e[0], '%s ± %s al' % (nombre(e[3], 1), nombre(e[4], 1))) for e in ETOILES]

    def dessiner(self, p, rect):
        self.zone_rotative(rect, self.vue3d)
        pts = [np.array(astro.vecteur_equatorial(15 * a, d)) for _, a, d, _, _ in ETOILES]
        # on cadre toute la scène (la Terre, les étoiles à leur distance, le ciel) dans la toile, quelle que soit sa
        # forme : la Terre ne sort plus de l'image sur un écran très large
        tous = np.vstack([np.zeros(3)] + pts + [v * e[3] / RAYON_AL for e, v in zip(ETOILES, pts)])
        x, y, _ = self.vue3d.projeter(tous)
        marge = 46
        bw, bh = max(1e-6, float(x.max() - x.min())), max(1e-6, float(y.max() - y.min()))
        r = max(10.0, min((rect.width() - 2 * marge) / bw, (rect.height() - 2 * marge) / bh))
        cx = rect.center().x() - r * float(x.max() + x.min()) / 2
        cy = rect.center().y() + r * float(y.max() + y.min()) / 2
        pe = dessin.Peintre3D(p, self.vue3d, cx, cy, r)
        if self.c_sphere.isChecked():
            for dec in (50, 55, 60):
                pe.courbe(dessin.cercle((0, 0, 1), 90 - dec, 361, debut=0, fin=360)[150:220], 'grille', 1.0,
                          arriere='normal', profondeur=False)
            for h in (11, 12, 13, 14):
                a = np.radians(15 * h)
                ds = np.radians(np.linspace(46, 65, 30))
                pe.courbe(np.stack([np.cos(ds) * np.cos(a), np.cos(ds) * np.sin(a), np.sin(ds)], axis=1), 'grille',
                          1.0, arriere='normal', profondeur=False)
            for i, j in TRAITS:
                pe.courbe(dessin.arc(pts[i], pts[j], 10), 'accent1', 1.6, arriere='normal', profondeur=False)
        # étiquettes placées sans chevauchement : on réserve d'abord la place de toutes les étoiles
        reels = [v * e[3] / RAYON_AL for e, v in zip(ETOILES, pts)]
        for v in reels + (pts if self.c_sphere.isChecked() else []) + [np.zeros(3)]:
            xs, ys, _, _ = pe.ecran(v)
            dessin.reserver(p, xs[0], ys[0], 6)
        noms = []
        for (nom, a, d, dist, err), v, reel in zip(ETOILES, pts, reels):
            if self.c_lignes.isChecked():
                pe.segment(np.zeros(3), v, 'doux', 0.8, 0.35)
            pe.segment(v * (dist - err) / RAYON_AL, v * (dist + err) / RAYON_AL, 'accent2', 3.0)
            q = pe.point(reel, 'etoile', 4.5, bord='soleil', toujours=True)
            if q and self.c_noms.isChecked():
                noms.append((q[0], q[1], '%s (%s al)' % (nom, nombre(dist, 0))))
            if self.c_sphere.isChecked():
                pe.point(v, 'accent1', 3.0, toujours=True)
        t = pe.point(np.zeros(3), 'terre', 6.0, toujours=True)
        for x, y, s_ in noms:
            dessin.etiquette(p, x, y, s_, 'texte', 8)
        if t:
            dessin.etiquette(p, t[0], t[1], tr('anim_shadowsim_terre'), 'texte', 9)
