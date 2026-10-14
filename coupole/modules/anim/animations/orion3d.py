"""Orion en 3D, sur le modèle de « Grande Ourse 3D » : les étoiles principales d'Orion (Bételgeuse, Bellatrix, Meissa,
Mintaka, Alnilam, Alnitak, Saiph, Rigel, et l'épée : Hatysa et le Trapèze de M42) à leur distance mesurée, la Terre en
bas, les lignes de visée, et leurs projections sur la sphère céleste où se dessine la figure familière.  On fait tourner
la scène au glisser : de face on retrouve la constellation, de côté on voit que ses étoiles sont à des profondeurs très
différentes (77 à 400 pc).  La nébuleuse d'Orion (M42) et la Tête de Cheval sont posées à leur place ; les nuages
moléculaires Orion A et B en option.  Animation propre à Coupole (pas dans ClassAction) ; données : SIMBAD, Gaia DR3,
Hipparcos 2007 et articles cités (fiches au survol) ; couleur vraie (corps noir → CIE).  Scène fixe (pas de lecture) :
elle n'est redessinée que lorsqu'on la tourne ou qu'on change un réglage.  Même rendu que Coupole Web
(src/anim/animations/orion3d.ts) ; géométrie commune : orion3d_geo.py."""
from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPixmap, QRadialGradient

from ....core.i18n import langue, tr
from .. import astro, dessin
from .. import nebuleuses_orion as N
from .. import orion3d_geo as O
from ..base import Animation, nombre
from ..couleur_etoile import accentuer, couleur_etoile, rayon_disque

# étoiles de la scène : la figure (8) et l'épée (Hatysa, θ¹ Ori C au cœur de M42)
ETOILES = ('alf_ori', 'gam_ori', 'lam_ori', 'del_ori', 'eps_ori', 'zet_ori', 'kap_ori', 'bet_ori', 'iot_ori', 'tet01_ori_c')
# figure tracée (Stellarium, ciel « moderne »), et l'épée en tirets
TRAITS = (('lam_ori', 'alf_ori'), ('lam_ori', 'gam_ori'), ('alf_ori', 'zet_ori'), ('gam_ori', 'del_ori'),
          ('del_ori', 'eps_ori'), ('eps_ori', 'zet_ori'), ('zet_ori', 'kap_ori'), ('del_ori', 'bet_ori'))
EPEE = (('eps_ori', 'tet01_ori_c'), ('tet01_ori_c', 'iot_ori'))
RAYON_PC = 450.0                 # rayon de la sphère céleste dessinée : un peu au-delà de l'étoile la plus lointaine
PC_AL = 3.2615637772
CIEL = QColor(6, 8, 14)
# vue de côté (la Terre en bas, Orion en haut : les profondeurs) et vue de face (depuis la Terre : la figure)
VUE_COTE = (172.5, 12.0)
VUE_FACE = (352.5, -55.0)

# Repère de dessin : la direction d'Orion (α = 84°, δ = −1°) est ramenée là où la Grande Ourse se trouve dans
# « Grande Ourse 3D » (α = 187,5°, δ = 55°), l'est et le nord du ciel conservés : même mise en scène, même vue de départ.
CENTRE_ORION = O.direction(84.0, -1.0)
CENTRE_SCENE = tuple(astro.vecteur_equatorial(15 * 12.5, 55.0))


def _base(c):
    est = O.unitaire(O.cross((0.0, 0.0, 1.0), c))
    nord = O.cross(c, est)
    return est, nord, tuple(c)


E0, N0, C0 = _base(CENTRE_ORION)
E1, N1, C1 = _base(CENTRE_SCENE)


def scene(v) -> np.ndarray:
    """Vecteur du ciel (ICRS) → repère de la scène (rotation : Orion à la place de la Grande Ourse)."""
    x, y, z = O.dot(v, E0), O.dot(v, N0), O.dot(v, C0)
    return np.array([x * E1[i] + y * N1[i] + z * C1[i] for i in range(3)])


_PAR_ID = {e['id']: e for e in O.DONNEES['etoiles']}


def etoile(i: str) -> dict:
    return _PAR_ID[i]


def avec_ecart(v: float, moins: float, plus: float, dec: int = 1) -> str:
    """« 264,6 ± 3,1 » ou « 264,6 (−21,8/+26,2) »."""
    if abs(moins - plus) < 0.05:
        return '%s ± %s' % (nombre(v, dec), nombre(moins, dec))
    return '%s (−%s/+%s)' % (nombre(v, dec), nombre(moins, dec), nombre(plus, dec))


class Orion3D(Animation):
    ID = 'orion3d'
    ANIMEE = False
    FICHES = True

    def construire(self):
        self.vue3d = self.vue(VUE_COTE[0], VUE_COTE[1], -89.0, 89.0)
        self.bouton('anim_orion3d_b_face', lambda: self._regarder(VUE_FACE))
        self.bouton('anim_orion3d_b_cote', lambda: self._regarder(VUE_COTE))
        self.unite = self.choix('unite', [('anim_orion3d_u_al', 'al'), ('anim_orion3d_u_pc', 'pc')], 'al')
        self.c_lignes = self.coche('lignes', True)
        self.c_noms = self.coche('noms', True)
        self.c_sphere = self.coche('sphere', True)
        self.c_figure = self.coche('figure', True)
        self.c_nebuleuses = self.coche('nebuleuses', True)
        self.c_nuages = self.coche('nuages', False)
        self.c_barres = self.coche('barres', True)
        self.c_brutes = self.coche('brutes', False)
        self.c_accent = self.coche('accentuees', False)

    def _regarder(self, v):
        """Vue instantanée (aucune lecture : la scène n'est redessinée qu'une fois)."""
        self.vue3d.regler(v[0], v[1])
        self.rafraichir()

    @staticmethod
    def nom(e) -> str:
        if e['id'] == 'tet01_ori_c':
            return tr('anim_orion3d_trapeze')
        return e['nom'].get(langue()) or e['nom']['fr']

    def distance(self, e) -> float:
        """Distance retenue (pc) : distance publiée du groupe (Alnilam, Mintaka, Meissa, Hatysa) ou mesure brute."""
        return e['d_affichage'] if not self.c_brutes.isChecked() and e.get('d_affichage') else e['d']

    def _texte_distance(self, pc: float) -> str:
        if self.unite.currentData() == 'pc':
            return '%s pc' % nombre(pc, 0)
        return '%s %s' % (nombre(pc * PC_AL, 0), tr('anim_fiche_al'))

    def valeurs(self):
        al = tr('anim_fiche_al')
        out = []
        for i in ETOILES:
            e = etoile(i)
            d = self.distance(e)
            mesure = '%s pc' % avec_ecart(e['d'], e['d_moins'] or 0.0, e['d_plus'] or 0.0)
            if d != e['d']:
                v = '≈ %s pc · %s %s (%s %s)' % (nombre(d, 0), nombre(d * PC_AL, 0), al, tr('anim_orion3d_mesure'), mesure)
            else:
                v = '%s · %s %s' % (mesure, nombre(d * PC_AL, 0), al)
            out.append((self.nom(e), v))
        m42 = O.norme(N.nebuleuses()[0]['centre'])
        tete = O.norme(O.DONNEES['primitives']['tete_de_cheval']['centre'])
        out.append((tr('anim_orion3d_n_m42'), '%s pc · %s %s' % (nombre(m42, 0), nombre(m42 * PC_AL, 0), al)))
        out.append((tr('anim_orion3d_n_tete'), '%s pc · %s %s' % (nombre(tete, 1), nombre(tete * PC_AL, 0), al)))
        out.append((tr('anim_orion3d_v_distances'), tr('anim_orion3d_d_brutes' if self.c_brutes.isChecked()
                                                       else 'anim_orion3d_d_publiees')))
        if self.c_accent.isChecked():
            out.append((tr('anim_orion3d_v_couleurs'), tr('anim_orion3d_couleurs_accentuees')))
        return out

    def _couleur(self, e) -> QColor:
        c = couleur_etoile(e.get('teff') or 5772)
        if self.c_accent.isChecked():
            c = accentuer(c)
        return QColor(*c)

    def double_clic(self, pos) -> bool:
        self.vue3d.reinitialiser()
        self.rafraichir()
        return True

    def dessiner(self, p, rect):
        # ciel nocturne dans les deux thèmes : les couleurs physiques des nébuleuses et des étoiles ressortent
        dessin.forcer_theme('sombre')
        try:
            p.fillRect(rect, CIEL)
            self._scene3d(p, rect)
        finally:
            dessin.forcer_theme(None)

    def _scene3d(self, p, rect):
        self._court = rect.width() < 600
        self.zone_rotative(rect, self.vue3d)
        dirs = {i: scene(O.direction(etoile(i)['ra'], etoile(i)['dec'])) for i in ETOILES}

        def reel(i):
            return dirs[i] * self.distance(etoile(i)) / RAYON_PC

        # toute la scène (la Terre, les étoiles à leur distance, le ciel) cadrée dans la toile, quelle que soit sa forme
        tous = np.vstack([np.zeros(3)] + list(dirs.values()) + [reel(i) for i in ETOILES])
        x, y, _ = self.vue3d.projeter(tous)
        marge = 46
        bw, bh = max(1e-6, float(x.max() - x.min())), max(1e-6, float(y.max() - y.min()))
        r = max(10.0, min((rect.width() - 2 * marge) / bw, (rect.height() - 2 * marge) / bh))
        cx = rect.center().x() - r * float(x.max() + x.min()) / 2
        cy = rect.center().y() + r * float(y.max() + y.min()) / 2
        self.vue3d.rayon_px = r
        pe = dessin.Peintre3D(p, self.vue3d, cx, cy, r)
        plat = dict(arriere='normal', profondeur=False)

        # sphère céleste : quadrillage d'Orion (δ = −10°, 0°, +10° ; α = 5 h, 5 h 30, 6 h), figure et épée projetées
        if self.c_sphere.isChecked():
            for dec in (-10, 0, 10):
                pe.courbe(np.array([scene(O.direction(ra, dec)) for ra in np.linspace(73, 95, 30)]), 'grille', 1.0, **plat)
            for ra in (75, 82.5, 90):
                pe.courbe(np.array([scene(O.direction(ra, dec)) for dec in np.linspace(-14, 14, 30)]), 'grille', 1.0,
                          **plat)
            for a, b in TRAITS:
                pe.courbe(dessin.arc(dirs[a], dirs[b], 10), 'accent1', 1.6, **plat)
            for a, b in EPEE:
                pe.courbe(dessin.arc(dirs[a], dirs[b], 6), 'accent1', 1.0, 0.7, **plat)
        # place réservée pour les étiquettes : étoiles, projections, Terre
        for v in [reel(i) for i in ETOILES] + (list(dirs.values()) if self.c_sphere.isChecked() else []) + [np.zeros(3)]:
            xs, ys, _, _ = pe.ecran(v)
            dessin.reserver(p, xs[0], ys[0], 7)
        # nuages moléculaires (option) : squelettes publiés d'Orion A et B (Zucker et al. 2021), traits transparents
        if self.c_nuages.isChecked():
            for cle, fiche, n in (('orion_a', 'orion:orion_a', 'anim_orion3d_n_orion_a'),
                                  ('orion_b', 'orion:orion_b', 'anim_orion3d_n_orion_b')):
                pts = np.array([scene(P) / RAYON_PC for P in O.DONNEES['primitives'][cle]['points']])
                pe.courbe(pts, QColor(130, 150, 200), 9, 0.22, **plat)
                pe.courbe(pts, QColor(130, 150, 200), 3, 0.45, **plat)
                xs, ys, _, _ = pe.ecran(pts[len(pts) // 2])
                self.survolable(p, fiche, xs[0], ys[0], 10, 40)
                if self.c_noms.isChecked():
                    dessin.etiquette(p, xs[0], ys[0], tr(n), 'doux', 8)
        # figure dans l'espace : les mêmes traits entre les étoiles à leur distance (rien ne les relie vraiment)
        if self.c_figure.isChecked():
            for a, b in TRAITS:
                pe.segment(reel(a), reel(b), 'accent1', 1.0, 0.45)
            for a, b in EPEE:
                pe.segment(reel(a), reel(b), 'accent1', 0.8, 0.3)
        # M42 et la Tête de Cheval : petites formes légères à leur place
        noms = []
        if self.c_nebuleuses.isChecked():
            self._nebuleuses(p, pe, r, noms)
        # étoiles : ligne de visée, barre d'erreur, disque en couleur vraie, projection sur la sphère
        for i in ETOILES:
            e = etoile(i)
            v = dirs[i]
            d = self.distance(e)
            if self.c_lignes.isChecked():
                pe.segment(np.zeros(3), v if self.c_sphere.isChecked() else v * d / RAYON_PC, 'doux', 0.8, 0.35)
            # barre d'erreur de la mesure affichée (une étoile placée à la distance de son groupe n'en a pas : sa mesure
            # propre, très incertaine, est dans les valeurs et dans sa fiche)
            if self.c_barres.isChecked() and d == e['d'] and e['d_moins'] is not None and e['d_plus'] is not None:
                pe.segment(v * (e['d'] - e['d_moins']) / RAYON_PC, v * (e['d'] + e['d_plus']) / RAYON_PC, 'accent2', 3.0)
            rayon = 3.2 if i == 'tet01_ori_c' else rayon_disque(e['V'], 0, 6, 2.6, 7.5)
            q = pe.point(reel(i), self._couleur(e), rayon, bord='grille', toujours=True)
            if q:
                self.survolable(p, 'orion:' + i, q[0], q[1], max(7.0, rayon + 2), e['V'])
                if self.c_noms.isChecked():
                    # toile étroite : le nom seul (la distance est dans les valeurs et dans la fiche)
                    noms.append((q[0], q[1], self.nom(e) if self._court else '%s (%s)' % (self.nom(e), self._texte_distance(d)),
                                 rayon + 4))
            if self.c_sphere.isChecked():
                pe.point(v, 'accent1', 2.6, toujours=True)
        t = pe.point(np.zeros(3), 'terre', 6.0, toujours=True)
        # étiquettes lisibles : police plus grande et grasse, cartouche contrasté, sans chevauchement
        p.save()
        dessin.police(p, 1.08, True)
        for xx, yy, s_, ecart in noms:
            dessin.etiquette(p, xx, yy, s_, 'texte', ecart)
        if t:
            dessin.etiquette(p, t[0], t[1], tr('anim_shadowsim_terre'), 'texte', 9)
        p.restore()
        dessin.texte(p, rect.x() + 10, rect.y() + rect.height() - 12, tr('anim_orion3d_legende'), 'doux', centre=False)
        if self.c_nebuleuses.isChecked():
            dessin.texte(p, rect.x() + 10, rect.y() + rect.height() - 30, tr('anim_orion3d_agrandi', k=N.AGRANDI), 'doux',
                         centre=False)

    _couche = None

    def _peindre_particules(self, p, pe, liste, pts, echelle):
        """Particules de l'arrière vers l'avant (gaz en mélange additif, poussière opaque), sprites dégradés."""
        xs, ys, zs, _ = pe.ecran(pts)
        ordre = np.argsort(zs, kind='stable').tolist()
        k = echelle / RAYON_PC
        # vue de face (depuis la Terre), les nuages agrandis masqueraient la figure : ils s'estompent
        face = max(0.0, -float(np.dot(self.vue3d.d, CENTRE_SCENE)))
        voile = 1 - 0.65 * face * face
        rp = np.maximum(1.2, _RAYONS * k).tolist()
        xl, yl = xs.tolist(), ys.tolist()
        plus = QPainter.CompositionMode.CompositionMode_Plus
        dessus = QPainter.CompositionMode.CompositionMode_SourceOver
        mode = None
        for i in ordre:
            q = liste[i]
            x, y, r = xl[i], yl[i], rp[i]
            if not (math.isfinite(x) and math.isfinite(y)):
                continue
            m = plus if q['genre'] == 'gaz' else dessus
            if m is not mode:
                p.setCompositionMode(m)
                mode = m
            p.setOpacity(q['alpha'] * voile)
            p.drawPixmap(QRectF(x - r, y - r, 2 * r, 2 * r), _sprite(q['rvb']), _SOURCE)

    def _nebuleuses(self, p, pe, echelle, noms):
        """M42 et IC 434 / Tête de Cheval en volume : particules pré-calculées (géométrie publiée, taille agrandie
        ×AGRANDI), projetées puis dessinées de l'arrière vers l'avant ; gaz ionisé en mélange additif, poussière opaque ;
        sprites dégradés préparés une fois par couleur."""
        liste, pts = _particules_scene()
        # couche des nébuleuses gardée tant que la vue et la taille ne changent pas (survol, fiche, valeurs : la scène
        # est redessinée sans repeindre les 1 038 particules)
        dev = p.device()
        dpr = dev.devicePixelRatioF() if dev is not None else 1.0
        tw, th = (dev.width(), dev.height()) if dev is not None else (800, 600)
        cle = (round(self.vue3d.az, 6), round(self.vue3d.alt, 6), tw, th, round(dpr, 3), round(echelle, 4),
               round(pe.cx, 3), round(pe.cy, 3))
        if self._couche is None or self._couche[0] != cle:
            img = QImage(max(1, int(tw * dpr)), max(1, int(th * dpr)), QImage.Format.Format_ARGB32_Premultiplied)
            img.setDevicePixelRatio(dpr)
            img.fill(Qt.GlobalColor.transparent)
            q = QPainter(img)
            q.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            self._peindre_particules(q, pe, liste, pts, echelle)
            q.end()
            self._couche = (cle, img)
        p.drawImage(QPointF(0, 0), self._couche[1])
        # étoiles excitatrices (Trapèze, σ Ori) et repères à fiche
        for n in N.nebuleuses():
            for e in n['etoiles']:
                et = etoile(e['id'])
                q = pe.point(scene(e['p']) / RAYON_PC, self._couleur(et), 3.4 if e['id'] == 'sig_ori' else 2.2,
                             toujours=True)
                if q:
                    self.survolable(p, 'orion:' + e['id'], q[0], q[1], 6, 30)
                    if e['id'] == 'sig_ori' and self.c_noms.isChecked():
                        noms.append((q[0], q[1], self.nom(et), 6))
            for rp in n['reperes']:
                xq, yq, _, _ = pe.ecran(scene(rp['p']) / RAYON_PC)
                self.survolable(p, rp['fiche'], xq[0], yq[0], 16 if rp['fiche'] == 'orion:m42' else 9, 20)
            if self.c_noms.isChecked():
                xc, yc, _, _ = pe.ecran(scene(n['centre']) / RAYON_PC)
                if self._court:
                    noms.append((xc[0], yc[0], 'M42' if n['id'] == 'm42' else 'IC 434', 16))
                else:
                    nom = tr('anim_orion3d_n_m42' if n['id'] == 'm42' else 'anim_orion3d_n_ic434')
                    noms.append((xc[0], yc[0], '%s (%s)' % (nom, self._texte_distance(O.norme(n['centre']))), 16))


_PS = None


_RAYONS = None


def _particules_scene():
    """Particules des deux nébuleuses dans le repère de la scène (calculées une fois)."""
    global _PS, _RAYONS
    if _PS is None:
        liste = [q for n in N.nebuleuses() for q in n['particules']]
        _PS = (liste, np.array([scene(q['p']) / RAYON_PC for q in liste]))
        _RAYONS = np.array([q['r'] for q in liste])
    return _PS


_SPRITES: dict = {}
_SOURCE = QRectF(0, 0, 48, 48)


def _sprite(rvb) -> QPixmap:
    """Disque dégradé (couleur pleine au centre → transparent au bord), préparé une fois par couleur."""
    img = _SPRITES.get(rvb)
    if img is None:
        img = QImage(48, 48, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        q = QPainter(img)
        g = QRadialGradient(QPointF(24, 24), 24)
        for pos, a in ((0.0, 1.0), (0.45, 0.55), (1.0, 0.0)):
            c = QColor(*rvb)
            c.setAlphaF(a)
            g.setColorAt(pos, c)
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QBrush(g))
        q.drawRect(0, 0, 48, 48)
        q.end()
        img = QPixmap.fromImage(img)
        _SPRITES[rvb] = img
    return img
