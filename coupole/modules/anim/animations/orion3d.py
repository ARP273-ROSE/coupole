"""Orion en 3D : la constellation telle qu'on la voit, puis « dépliée » en trois dimensions (chaque étoile à sa distance
mesurée) ; les nuages moléculaires Orion A et B, la nébuleuse d'Orion (M42, modèle en « blister »), la Tête de Cheval,
l'anneau de λ Orionis et la boucle de Barnard à leurs distances publiées ; plongée vers M42 et la Tête de Cheval avec
les images de l'ESO et de l'ESA/Hubble posées sur le ciel.  Animation propre à Coupole (pas dans ClassAction) ; données
: SIMBAD, Gaia DR3, Hipparcos 2007 et articles cités (fiches au survol).  Tout est à l'échelle, sauf la taille des
disques d'étoiles (selon la magnitude) ; couleur vraie (corps noir → CIE 1931).  Même rendu que Coupole Web
(src/anim/animations/orion3d.ts) ; géométrie commune : orion3d_geo.py."""
from __future__ import annotations

import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPen, QPolygonF, QRadialGradient, QTransform

from ....core.i18n import langue, tr
from .. import dessin
from .. import orion3d_geo as O
from ..base import Animation, nombre
from ..couleur_etoile import accentuer, couleur_etoile, rayon_disque

NOMMEES = {'bet_ori', 'alf_ori', 'gam_ori', 'eps_ori', 'zet_ori', 'kap_ori', 'del_ori', 'lam_ori', 'pi_03_ori', 'iot_ori'}
NOMMEES_ZOOM = {'orion': NOMMEES,
                'm42': {'tet01_ori_c', 'tet01_ori_a', 'tet01_ori_b', 'tet01_ori_d', 'tet02_ori_a', 'iot_ori'},
                'tete': {'sig_ori', 'sig_ori_e', 'sig_ori_d', 'zet_ori'}}
CIEL = QColor(4, 6, 12)
DUREE_TRANSITION = 2.2
VITESSE_DEPLIEMENT = 100 / DUREE_TRANSITION
TOUR_PAR_S = 6.0
_IMAGES: dict = {}


def texture(fichier: str):
    """Image d'une texture (chargée une fois), ou None si illisible."""
    if fichier not in _IMAGES:
        img = QImage(str(Path(__file__).resolve().parents[1] / 'donnees' / 'orion' / fichier))
        _IMAGES[fichier] = None if img.isNull() else img
    return _IMAGES[fichier]


def _c(r, g, b, a=1.0) -> QColor:
    col = QColor(int(r), int(g), int(b))
    col.setAlphaF(max(0.0, min(1.0, a)))
    return col


def _stylo(col: QColor, ep: float, pointille: bool = False) -> QPen:
    pen = QPen(col, ep)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    if pointille:
        pen.setStyle(Qt.PenStyle.DashLine)
    return pen


class Orion3D(Animation):
    ID = 'orion3d'
    ANIMEE = True
    FICHES = True

    def construire(self):
        self.vue3d = self.vue(0, 0, -80, 80)
        self.dep = self.curseur('depliement', 0, 100, 0, dec=0, unite='%')
        self.bouton('anim_orion3d_b_ciel', lambda: self._aller(0))
        self.bouton('anim_orion3d_b_3d', lambda: self._aller(100))
        self.cible = self.choix('cible', [('anim_orion3d_c_orion', 'orion'), ('anim_orion3d_c_m42', 'm42'),
                                          ('anim_orion3d_c_tete', 'tete')], 'orion')
        self.photo = self.choix('image', [('anim_orion3d_i_sol', 'sol'), ('anim_orion3d_i_hubble', 'hubble')], 'sol')
        self.c_figure = self.coche('figure', True)
        self.c_noms = self.coche('noms', True)
        self.c_nebuleuses = self.coche('nebuleuses', True)
        self.c_images = self.coche('images', True)
        self.c_barres = self.coche('barres', True)
        self.c_accent = self.coche('accentuees', False)
        self.c_brutes = self.coche('brutes', False)
        self._credits = []
        self.etat_initial()
        self.cible.currentIndexChanged.connect(lambda *_: self._changer_cible())

    def etat_initial(self):
        self._but = None
        self._lecture_auto = False
        c = self.cible.currentData() if hasattr(self, 'cible') else 'orion'
        self._de = self._vers = c or 'orion'
        self._k = 1.0

    def _aller(self, v: float):
        """Bouton « vue du ciel » / « vue 3D » : le dépliement va vers v en ~2 s (lecture lancée au besoin)."""
        self._but = v
        if not self.en_lecture:
            self._lecture_auto = True
            self.basculer_lecture()

    def _changer_cible(self):
        c = self.cible.currentData()
        if c == self._vers:
            return
        self._de = self._vers if self._k >= 0.5 else self._de
        self._vers = c
        self._k = 0.0
        if not self.en_lecture:
            self._lecture_auto = True
            self.basculer_lecture()

    def avancer(self, dt: float):
        bouge = False
        if self._but is not None:
            v = self.dep.value()
            n = min(self._but, v + VITESSE_DEPLIEMENT * dt) if v < self._but else max(self._but, v - VITESSE_DEPLIEMENT * dt)
            self.dep.setValue(n)
            if n == self._but:
                self._but = None
            else:
                bouge = True
        if self._k < 1:
            self._k = min(1.0, self._k + dt / DUREE_TRANSITION)
            if self._k < 1:
                bouge = True
            else:
                self._de = self._vers
        if not bouge and self._lecture_auto:
            self._lecture_auto = False
            self.arreter()
        elif not bouge and self.dep.value() > 0:
            # lecture demandée : la scène tourne lentement (tourne-disque)
            self.vue3d.regler(self.vue3d.az + TOUR_PAR_S * dt, self.vue3d.alt)

    def basculer_lecture(self):
        if self.en_lecture:
            self._lecture_auto = False
        super().basculer_lecture()

    def double_clic(self, pos) -> bool:
        self.vue3d.reinitialiser()
        self.rafraichir()
        return True

    def credits_visibles(self) -> list:
        return self._credits

    def _u(self) -> float:
        return max(0.0, min(1.0, self.dep.value() / 100))

    def camera(self, w: float, h: float) -> dict:
        lacet = math.fmod(self.vue3d.az + 180, 360) - 180
        return O.camera(self._de, self._vers, self._k, self._u(), lacet, self.vue3d.alt, w, h)

    def _couleur(self, e) -> QColor:
        c = couleur_etoile(e['teff'] if e['teff'] is not None else 5772)
        if self.c_accent.isChecked():
            c = accentuer(c)
        return QColor(*c)

    @staticmethod
    def _nom(e) -> str:
        return e['nom'].get(langue()) or e['nom']['fr']

    def distance(self, e) -> float:
        return e['d_affichage'] if not self.c_brutes.isChecked() and e['d_affichage'] else e['d']

    def valeurs(self):
        u = self._u()
        fig = {i for ligne in O.DONNEES['figure'] for i in ligne}
        etoiles = [e for e in O.DONNEES['etoiles'] if e['id'] in fig]
        proche = etoiles[0]
        loin = etoiles[0]
        for e in etoiles[1:]:
            if self.distance(e) < self.distance(proche):
                proche = e
            if self.distance(e) > self.distance(loin):
                loin = e
        par_id = {e['id']: e for e in O.DONNEES['etoiles']}
        ceinture = [par_id[i] for i in ('zet_ori', 'eps_ori', 'del_ori')]

        def al(pc):
            return nombre(pc * 3.2615637772, 0)

        c = self.cible.currentData()
        vue = tr('anim_orion3d_vue_ciel') if u <= 0 else tr('anim_orion3d_vue_3d') if u >= 1 else \
            tr('anim_orion3d_vue_entre', p=nombre(100 * u, 0))
        out = [(tr('anim_orion3d_v_vue'), vue),
               (tr('anim_orion3d_v_cible'), tr('anim_orion3d_c_' + c)),
               (tr('anim_orion3d_v_proche'), '%s : %s pc (%s %s)' % (self._nom(proche), nombre(self.distance(proche), 1),
                                                                    al(self.distance(proche)), tr('anim_fiche_al'))),
               (tr('anim_orion3d_v_loin'), '%s : %s pc (%s %s)' % (self._nom(loin), nombre(self.distance(loin), 0),
                                                                  al(self.distance(loin)), tr('anim_fiche_al'))),
               (tr('anim_orion3d_v_ceinture'), ' · '.join('%s %s pc' % (self._nom(e), nombre(self.distance(e), 0))
                                                          for e in ceinture)),
               (tr('anim_orion3d_v_distances'), tr('anim_orion3d_d_brutes' if self.c_brutes.isChecked()
                                                   else 'anim_orion3d_d_publiees')),
               (tr('anim_orion3d_v_echelle'), tr('anim_orion3d_echelle'))]
        if self.c_accent.isChecked():
            out.append((tr('anim_orion3d_v_couleurs'), tr('anim_orion3d_couleurs_accentuees')))
        return out

    # ------------------------------------------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        p.fillRect(rect, CIEL)
        self.zone_rotative(rect, self.vue3d)
        self.vue3d.rayon_px = 0.45 * min(rect.width(), rect.height())
        cam = self.camera(rect.width(), rect.height())
        cam['cx'] += rect.x()
        cam['cy'] += rect.y()
        u = self._u()
        s = O.lisse(u)
        p.save()
        p.setClipRect(rect)
        self._credits = []
        if self.c_nebuleuses.isChecked():
            self._nebuleuses(p, cam, u, s)
        if self.c_images.isChecked():
            self._textures(p, cam, u, s, rect)
        if self.c_nebuleuses.isChecked():
            self._m42_blister(p, cam, u)
        self._etoiles(p, cam, u, s, rect)
        p.restore()
        self._legendes(p, cam, rect, s)

    @staticmethod
    def _proj(cam, P, u):
        return O.projeter(cam, O.deplier(P, u))

    @staticmethod
    def _lueur(p, x, y, r, col: QColor, alpha: float):
        if not (r > 0.5) or not math.isfinite(x) or not math.isfinite(y) or alpha <= 0.01:
            return
        g = QRadialGradient(QPointF(x, y), r)
        g.setColorAt(0, _c(col.red(), col.green(), col.blue(), alpha))
        g.setColorAt(0.45, _c(col.red(), col.green(), col.blue(), alpha * 0.45))
        g.setColorAt(1, _c(col.red(), col.green(), col.blue(), 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(x, y), r, r)

    def _tube(self, p, cam, pts, rayon_pc, u, col: QColor, alpha):
        """Nuage en tube : trait épais et transparent le long d'une épine (halo puis cœur), une polyligne par
        morceau visible, épaisseur selon la profondeur moyenne du morceau."""
        q = [self._proj(cam, P, u) for P in pts]
        morceaux, courant = [], []
        for x in q + [None]:
            if x is None:
                if len(courant) > 1:
                    morceaux.append(courant)
                courant = []
            else:
                courant.append(x)
        for m in morceaux:
            z = sum(v[2] for v in m) / len(m)
            poly = QPolygonF([QPointF(v[0], v[1]) for v in m])
            for k, larg in ((2.6, alpha * 0.35), (1.0, alpha)):
                w = max(1.5, k * 2 * cam['F'] * rayon_pc / z)
                # de près (plongée), le tube serait une bande énorme sans forme publiée : il s'efface
                f = max(0.0, min(1.0, (48 - w / k) / 24))
                if f <= 0:
                    continue
                p.setPen(_stylo(_c(col.red(), col.green(), col.blue(), larg * f), w))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPolyline(poly)
        return [x for x in q if x is not None]

    def _marque(self, p, q, fiche: str, r: float, ordre: float):
        self.survolable(p, fiche, q[0], q[1], max(5.0, min(40.0, r)), ordre)

    def _nebuleuses(self, p, cam, u, s):
        P = O.DONNEES['primitives']
        gal = O.DONNEES['icrs_vers_gal']
        # boucle de Barnard : arc Hα de 14° à l'est d'Orion ; en 3D, sur la coquille d'Orion (Foley et al. 2023)
        bb = P['boucle_barnard']
        rb = bb['diametre_deg'] / 2 * O.DEG
        arc = []
        for k in range(49):
            pa = (-15 + 210 * k / 48) * O.DEG
            d = O.decaler(bb['centre_radec'][0], bb['centre_radec'][1], rb * math.sin(pa), rb * math.cos(pa))
            r = O.norme(O.point_coquille(d, gal))
            arc.append(O.comb(d, (1 - u) * O.R0 + u * r, (0, 0, 0), 0))
        qa = [x for x in (O.projeter(cam, X) for X in arc) if x is not None]
        if len(qa) > 1:
            poly = QPolygonF([QPointF(x[0], x[1]) for x in qa])
            for ep, al in ((14, 0.08), (6, 0.16), (2, 0.32)):
                p.setPen(_stylo(_c(232, 80, 104, al), ep))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPolyline(poly)
            self._marque(p, qa[int(math.floor(len(qa) * 0.3))], 'orion:boucle_barnard', 10, 30)
        # λ Orionis : bulle H II (lueur rouge) et anneau de poussière
        lb = P['lambda_ori_bulle']
        ql = self._proj(cam, lb['centre'], u)
        if ql:
            self._lueur(p, ql[0], ql[1], cam['F'] * lb['rayon_pc'] / ql[2], QColor(220, 70, 90), 0.16)
        anneau = self._tube(p, cam, P['lambda_ori_anneau']['points'], P['lambda_ori_anneau']['rayon_pc'], u,
                            QColor(150, 118, 96), 0.22)
        if anneau:
            self._marque(p, anneau[len(anneau) // 4], 'orion:lambda_ori', 10, 31)
        # nuages moléculaires Orion A et B
        oa = self._tube(p, cam, P['orion_a']['points'], P['orion_a']['rayon_pc'], u, QColor(120, 138, 178), 0.3)
        if oa:
            self._marque(p, oa[int(math.floor(len(oa) * 0.6))], 'orion:orion_a', 10, 32)
        ob = self._tube(p, cam, P['orion_b']['points'], P['orion_b']['rayon_pc'], u, QColor(120, 138, 178), 0.26)
        if ob:
            self._marque(p, ob[len(ob) // 2], 'orion:orion_b', 10, 33)
        # M42 (lueur), IC 434 derrière la Tête de Cheval
        m = self._proj(cam, P['m42_bol']['sommet'], u)
        if m:
            r = max(4.0, cam['F'] * P['m42_bol']['rayon_pc'] / m[2])
            f = 1 - self._visibilite_image(cam, u, 'm42')
            self._lueur(p, m[0], m[1], r * 1.6, QColor(255, 110, 140), 0.45 * f)
            self._lueur(p, m[0], m[1], r * 0.5, QColor(130, 230, 220), 0.35 * (1 - s * 0.5) * f)
            self._marque(p, m, 'orion:m42', max(6.0, r), 20)
        t = self._proj(cam, P['tete_de_cheval']['centre'], u)
        if t:
            r = max(3.0, cam['F'] * 0.9 / t[2])
            self._lueur(p, t[0], t[1] - r * 0.3, r * 2.2, QColor(230, 60, 80),
                        0.3 * (1 - self._visibilite_image(cam, u, 'tete_de_cheval')))
            self._marque(p, t, 'orion:tete_de_cheval', max(5.0, cam['F'] * 0.4 / t[2]), 21)

    def _visibilite_image(self, cam, u, objet: str) -> float:
        """Part (0–1) de l'image de l'objet montrée (taille à l'écran) : les lueurs dessinées s'effacent devant elle."""
        if not self.c_images.isChecked():
            return 0.0
        t = next((x for x in O.DONNEES['textures'] if x['objet'] == objet), None)
        if t is None:
            return 0.0
        P = O.DONNEES['primitives']
        centre = P['m42_bol']['sommet'] if objet == 'm42' else P['tete_de_cheval']['centre']
        e = t['echelle_arcmin_px'] * t['taille_px'][0] / 60 / 2 * O.DEG
        a = self._proj(cam, O.comb(O.decaler(t['centre_radec'][0], t['centre_radec'][1], e, 0), O.norme(centre), (0, 0, 0), 0), u)
        b = self._proj(cam, O.comb(O.decaler(t['centre_radec'][0], t['centre_radec'][1], -e, 0), O.norme(centre), (0, 0, 0), 0), u)
        if a is None or b is None:
            return 0.0
        return max(0.0, min(1.0, (math.hypot(a[0] - b[0], a[1] - b[1]) - 24) / 60))

    def _textures(self, p, cam, u, s, rect):
        """Images posées sur le ciel (plan perpendiculaire à la ligne de visée, à la distance de l'objet)."""
        P = O.DONNEES['primitives']
        choix = ('m42_hubble', 'tete_de_cheval_hubble_ir') if self.photo.currentData() == 'hubble' \
            else ('m42_vst', 'tete_de_cheval_vlt')
        for t in O.DONNEES['textures']:
            if t['id'] not in choix:
                continue
            centre = P['m42_bol']['sommet'] if t['objet'] == 'm42' else P['tete_de_cheval']['centre']
            dist = O.norme(centre)
            w, h = t['taille_px']
            e = t['echelle_arcmin_px'] / 60 * O.DEG
            ra, dec = t['centre_radec']

            def coin(xi, eta):
                return self._proj(cam, O.comb(O.decaler(ra, dec, xi, eta), dist, (0, 0, 0), 0), u)

            hg, hd, bg = coin(w / 2 * e, h / 2 * e), coin(-w / 2 * e, h / 2 * e), coin(w / 2 * e, -h / 2 * e)
            if hg is None or hd is None or bg is None:
                continue
            taille = math.hypot(hd[0] - hg[0], hd[1] - hg[1])
            if not taille > 24:
                continue
            xs = (hg[0], hd[0], bg[0], hd[0] + bg[0] - hg[0])
            ys = (hg[1], hd[1], bg[1], hd[1] + bg[1] - hg[1])
            if max(xs) < rect.left() or min(xs) > rect.right() or max(ys) < rect.top() or min(ys) > rect.bottom():
                continue
            self._credits.append(('%s %s (%s)' % (tr('anim_orion3d_image'), t['credit'], t['licence']), t['page']))
            img = texture(t['fichier'])
            if img is None:
                continue
            p.save()
            p.setOpacity(max(0.35, 1 - 0.55 * s) * min(1.0, (taille - 24) / 60))
            p.setTransform(QTransform((hd[0] - hg[0]) / w, (hd[1] - hg[1]) / w, (bg[0] - hg[0]) / h,
                                      (bg[1] - hg[1]) / h, hg[0], hg[1]), True)
            p.setRenderHint(p.RenderHint.SmoothPixmapTransform, True)
            p.drawImage(QPointF(0, 0), img)
            p.restore()

    def _m42_blister(self, p, cam, u):
        """M42 de près : front d'ionisation en bol, Voile, à l'échelle (modèle en « blister »)."""
        P = O.DONNEES['primitives']
        b = P['m42_bol']
        S = b['sommet']
        ax = O.unitaire(b['axe_vers_observateur'])
        R = b['rayon_pc']
        q0 = self._proj(cam, S, u)
        s = O.lisse(u)
        if q0 is None or cam['F'] * R / q0[2] < 40 or s < 0.05:
            return
        e1 = O.unitaire(O.cross(ax, (0, 0, 1)))
        e2 = O.cross(ax, e1)

        def anneau(rr, dz):
            out = []
            for k in range(49):
                a = 2 * math.pi * k / 48
                X = O.comb(O.comb(S, 1, e1, rr * math.cos(a)), 1, O.comb(e2, rr * math.sin(a), ax, dz), 1)
                q = self._proj(cam, X, u)
                if q:
                    out.append(QPointF(q[0], q[1]))
            return out

        # front d'ionisation : z(r) = −0,2 (1 − (r/R)²) pc par rapport au plan de θ¹ Ori C (Wen & O'Dell 1995)
        for i in range(1, 6):
            rr = R * i / 5
            pts = anneau(rr, 0.2 * (rr / R) ** 2)
            if len(pts) > 2:
                p.setPen(_stylo(_c(255, 130, 150, 0.55 * s), 1.2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPolyline(QPolygonF(pts))
        # Voile : disque à ≈ 2 pc devant le Trapèze (O'Dell et al. 2009)
        v = P['m42_voile']
        voile = anneau(v['rayon_pc'], O.dot(O.comb(v['centre'], 1, S, -1), ax))
        if len(voile) > 2:
            p.setPen(_stylo(_c(170, 190, 230, 0.6 * s), 1.0, True))
            p.setBrush(_c(120, 140, 200, 0.07 * s))
            p.drawPolygon(QPolygonF(voile))

    def _etoiles(self, p, cam, u, s, rect):
        brutes = self.c_brutes.isChecked()
        pos = {e['id']: self._proj(cam, O.position_etoile(e, brutes), u) for e in O.DONNEES['etoiles']}
        fig = []
        for ligne in O.DONNEES['figure']:
            for i in ligne:
                if i not in fig:
                    fig.append(i)
        soleil = O.projeter(cam, (0, 0, 0))
        if s > 0.02 and soleil:
            p.setPen(_stylo(_c(200, 210, 230, 0.12 * s), 0.8))
            for i in fig:
                q = pos.get(i)
                if q:
                    p.drawLine(QPointF(soleil[0], soleil[1]), QPointF(q[0], q[1]))
        if self.c_figure.isChecked():
            p.setPen(_stylo(_c(242, 193, 78, 0.55), 1.3))
            for ligne in O.DONNEES['figure']:
                for i in range(len(ligne) - 1):
                    a, b = pos.get(ligne[i]), pos.get(ligne[i + 1])
                    if a and b:
                        p.drawLine(QPointF(a[0], a[1]), QPointF(b[0], b[1]))
        cible = self._vers if self._k >= 0.5 else self._de
        # barres d'erreur le long de la ligne de visée ; mesure brute d'une distance d'affichage en tirets
        if self.c_barres.isChecked() and u > 0.02:
            for e in O.DONNEES['etoiles']:
                if e['id'] not in fig and not e['id'].startswith('tet01'):
                    continue
                d = O.direction(e['ra'], e['dec'])
                if not brutes and e.get('xyz_affichage'):
                    a, b = pos.get(e['id']), self._proj(cam, e['xyz'], u)
                    if a and b:
                        p.setPen(_stylo(_c(124, 196, 232, 0.6 * s), 1.0, True))
                        p.drawLine(QPointF(a[0], a[1]), QPointF(b[0], b[1]))
                        p.setBrush(Qt.BrushStyle.NoBrush)
                        p.drawEllipse(QPointF(b[0], b[1]), 2.5, 2.5)
                elif e['d_moins'] is not None and e['d_plus'] is not None:
                    a = self._proj(cam, O.comb(d, e['d'] - e['d_moins'], (0, 0, 0), 0), u)
                    b = self._proj(cam, O.comb(d, e['d'] + e['d_plus'], (0, 0, 0), 0), u)
                    if a and b:
                        p.setPen(_stylo(_c(124, 196, 232, (0.75 if cible == 'orion' else 0.45) * s),
                                        2.4 if cible == 'orion' else 1.4))
                        p.drawLine(QPointF(a[0], a[1]), QPointF(b[0], b[1]))
        # étoiles, de la plus lointaine à la plus proche
        zoom = 1.25 if cible != 'orion' else 1.0
        ordre = sorted((e for e in O.DONNEES['etoiles'] if pos.get(e['id'])), key=lambda e: -pos[e['id']][2])
        noms = []
        for e in ordre:
            q = pos[e['id']]
            if q[0] < rect.left() - 20 or q[0] > rect.right() + 20 or q[1] < rect.top() - 20 or q[1] > rect.bottom() + 20:
                continue
            r = rayon_disque(e['V'], 0, 5.5, 1.3, 8) * zoom
            col = self._couleur(e)
            if r > 2.2:
                self._lueur(p, q[0], q[1], r * 2.6, col, 0.22)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(col))
            p.drawEllipse(QPointF(q[0], q[1]), r, r)
            if r >= 2:
                dessin.reserver(p, q[0], q[1], r + 1)
            self.survolable(p, 'orion:' + e['id'], q[0], q[1], max(r, 5.0), e['V'])
            if self.c_noms.isChecked() and e['id'] in NOMMEES_ZOOM[cible]:
                dd = self.distance(e)
                txt = '%s %s pc' % (self._nom(e), nombre(dd, 1 if dd < 10 else 0)) if s > 0.5 else self._nom(e)
                noms.append((q[0], q[1], txt))
        if soleil and s > 0.05 and rect.contains(QPointF(soleil[0], soleil[1])):
            dessin.disque(p, soleil[0], soleil[1], 4.5, 'soleil')
            noms.append((soleil[0], soleil[1], tr('anim_stellarlum_soleil')))
        dessin.police(p, 0.82)
        for x, y, t in noms:
            dessin.etiquette(p, x, y, t, 'texte', 7)
        if self.c_noms.isChecked() and self.c_nebuleuses.isChecked():
            P = O.DONNEES['primitives']
            if cible == 'orion':
                lieux = [(P['m42_bol']['sommet'], 'anim_orion3d_n_m42'), (P['tete_de_cheval']['centre'], 'anim_orion3d_n_tete'),
                         (P['orion_a']['points'][11], 'anim_orion3d_n_orion_a'),
                         (P['orion_b']['points'][45], 'anim_orion3d_n_orion_b'),
                         (P['lambda_ori_anneau']['points'][12], 'anim_orion3d_n_lambda')]
            elif cible == 'm42':
                lieux = [(P['m42_bol']['sommet'], 'anim_orion3d_n_m42')]
            else:
                lieux = [(P['tete_de_cheval']['centre'], 'anim_orion3d_n_tete')]
            for X, cle in lieux:
                q = self._proj(cam, X, u)
                if q and rect.contains(QPointF(q[0], q[1])):
                    dessin.etiquette(p, q[0], q[1], tr(cle), 'accent3', 9)
            if cible == 'orion':
                bb = P['boucle_barnard']
                d = O.decaler(bb['centre_radec'][0], bb['centre_radec'][1], bb['diametre_deg'] / 2 * O.DEG, 0)
                X = O.comb(d, (1 - u) * O.R0 + u * O.norme(O.point_coquille(d, O.DONNEES['icrs_vers_gal'])), (0, 0, 0), 0)
                q = O.projeter(cam, X)
                if q and rect.contains(QPointF(q[0], q[1])):
                    dessin.etiquette(p, q[0], q[1], tr('anim_orion3d_n_barnard'), 'accent3', 9)
        dessin.police(p, 1 / 0.82)

    def _legendes(self, p, cam, rect, s):
        """Échelle (en 3D), crédits des images, légende des couleurs."""
        dessin.police(p, 0.78)
        fm = p.fontMetrics()
        y = rect.bottom() - 8
        for t, _ in reversed(self._credits):
            dessin.texte(p, rect.left() + 8, y, t, 'doux', centre=False, fond=True)
            y -= fm.height() + 4
        if s > 0.3:
            cible = self._vers if self._k >= 0.5 else self._de
            L = 100 if cible == 'orion' else 2 if cible == 'm42' else 1
            px = cam['F'] * L / cam['D']
            if 12 < px < rect.width() * 0.6:
                x1, yb = rect.right() - 12, rect.top() + 14
                p.setPen(dessin.stylo('texte', 1.6))
                p.drawLine(QPointF(x1 - px, yb), QPointF(x1, yb))
                p.drawLine(QPointF(x1 - px, yb - 4), QPointF(x1 - px, yb + 4))
                p.drawLine(QPointF(x1, yb - 4), QPointF(x1, yb + 4))
                dessin.texte(p, x1 - px / 2, yb + 12, tr('anim_orion3d_barre', l=nombre(L, 0)), 'texte', fond=True)
        leg = tr('anim_orion3d_legende')
        dessin.texte(p, rect.right() - 8 - fm.horizontalAdvance(leg), rect.bottom() - 8, leg, 'doux', centre=False,
                     fond=True)
        dessin.police(p, 1 / 0.78)
