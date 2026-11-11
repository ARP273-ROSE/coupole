"""Le canon de Newton : l'expérience de pensée des Principia (Newton, 1687) — un canon au sommet d'une montagne tire
de plus en plus vite ; le boulet retombe de plus en plus loin, puis fait le tour de l'astre (satellisation), puis
s'en va pour toujours (libération).  Code, dessins et textes propres à Coupole.

Mouvement intégré par canon_meca.py (moteur de « Gravité et orbites » : Yoshida d'ordre 4, pas adaptatif ; air en
option, traînée et densité réelles).  Ergonomie : flèche à tirer (angle et vitesse d'un seul geste), repères v₁ et
v₂ sur le curseur et autour du canon, trajectoire prévue en pointillés pendant le réglage, gros bouton « Feu ! » et
touche Espace, cadrage automatique qui suit le boulet (molette pour zoomer, double-clic ou « Recadrer » pour revenir),
préréglages en un clic, tirs précédents gardés en couleurs avec leur légende, défis vérifiés automatiquement.
Jumeau : src/anim/animations/canon_newton.ts de Coupole Web (même rendu, mêmes valeurs au caractère près)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QPolygonF
from PyQt6.QtWidgets import QPushButton

from ....core.i18n import tr
from ....gui.outils import aide
from .. import canon_meca as C
from .. import dessin
from ..base import Animation, nombre

#: couleurs des tirs successifs
COULEURS_TIRS = ('accent1', 'accent2', 'accent3', 'arc1', 'arc2', 'ecliptique', 'meridien', 'equateur')
#: tirs gardés au plus
MAX_TIRS = 8
#: couleur de chaque astre (les deux petits corps sont gris : sphères « lune » et « doux »)
COULEUR_ASTRE = {'terre': 'terre', 'lune': 'lune', 'mars': 'mars', 'ceres': 'lune', 'dimorphos': 'doux'}
#: longueur de la flèche à la vitesse maximale du curseur (fraction du plus petit côté du panneau)
FLECHE = 0.30
POINTS_TRACE = 700        # points dessinés au plus par trace
G0 = 9.80665              # pesanteur normale (pour exprimer le freinage en g)


def duree(s: float) -> str:
    """Durée lisible : « 45 s », « 12 min 05 s », « 5 h 07 min », « 3,2 j »."""
    if not math.isfinite(s):
        return '—'
    if s < 60:
        return '%s s' % nombre(s, 1 if s < 10 else 0)
    if s < 3600:
        m = int(s // 60)
        return '%d min %02d s' % (m, int(s - 60 * m))
    if s < 172800:
        h = int(s // 3600)
        return '%d h %02d min' % (h, int((s - 3600 * h) // 60))
    return '%s %s' % (nombre(s / 86400, 1), tr('anim_newtoncannon_j'))


def periode(s: float) -> str:
    """Période fine, pour comparer la mesure et Kepler : minutes à deux décimales (jours au-delà de deux jours)."""
    if s is None or not math.isfinite(s):
        return '—'
    if s < 172800:
        return '%s min' % nombre(s / 60, 2)
    return '%s %s' % (nombre(s / 86400, 3), tr('anim_newtoncannon_j'))


def echelle_nette(x: float) -> float:
    """Plus grande longueur 1, 2 ou 5 × 10ⁿ inférieure ou égale à x."""
    if not x > 0:
        return 1.0
    e = math.floor(math.log10(x))
    b = 10.0 ** e
    for m in (5, 2, 1):
        if m * b <= x:
            return m * b
    return b


class CanonNewton(Animation):
    ID = 'newtoncannon'

    def construire(self):
        self.tirs = []
        self.n_tirs = 0
        self.manuel = None               # cadrage manuel : {'s': px/m rapporté au plus petit côté, 'ox', 'oy'}
        self._cam = dict(cx=0.0, cy=0.0, s=1.0, ox=0.0, oy=0.0, L=1.0)
        self._apercu = (None, [])
        self._panneau = QRectF(0, 0, 1, 1)
        self.vitesse.hide()              # le temps se règle par « Temps » (×1 … ×1 000)
        self.b_feu = QPushButton(tr('anim_newtoncannon_feu'))
        self.b_feu.setObjectName('principal')
        f = self.b_feu.font()
        f.setPointSizeF(f.pointSizeF() * 1.25)
        f.setBold(True)
        self.b_feu.setFont(f)
        self.b_feu.setMinimumWidth(120)
        aide(self.b_feu, 'anim_newtoncannon_feu_aide')
        self.b_feu.clicked.connect(self.feu)
        self.barre.addWidget(self.b_feu)
        self.bouton('anim_newtoncannon_recommencer', self.recommencer, flux=self.barre)
        self.bouton('anim_newtoncannon_effacer', self.effacer, flux=self.barre)
        self.bouton('anim_newtoncannon_recadrer', self.recadrer, flux=self.barre)
        self.c_temps = self.choix('temps', [('anim_newtoncannon_t_%d' % k, k) for k in C.TEMPS], 100,
                                  flux=self.barre)
        self.c_astre = self.choix('astre', [('anim_newtoncannon_a_' + a, a) for a in C.NOMS_ASTRES], 'terre')
        self.r_alt = {}
        self.r_vit = {}
        for a in C.NOMS_ASTRES:
            R = C.REGLAGES[a]
            self.r_alt[a] = self.curseur('altitude_' + a, R['amin'], R['amax'], R['a0'], dec=R['da'], unite=R['na'],
                                         log=True, cle_texte='anim_newtoncannon_altitude')
        for a in C.NOMS_ASTRES:
            R = C.REGLAGES[a]
            self.r_vit[a] = self.curseur('vitesse_' + a, 0.0, R['vmax'], R['v0'], dec=R['dv'], unite=R['nv'],
                                         cle_texte='anim_newtoncannon_vitesse')
        self.r_angle = self.curseur('angle', -90.0, 90.0, 0.0, dec=1, unite='°')
        self.c_air = self.coche('air', False)
        self.c_projectile = self.choix('projectile', [('anim_newtoncannon_p_' + k, k) for k in C.BALISTIQUE], 'boulet')
        self.c_apercu = self.coche('apercu', True)
        for nom in C.PREREGLAGES:
            self.bouton('anim_newtoncannon_pr_' + nom, lambda _=False, n=nom: self.prereglage(n))
        self.c_defi = self.choix('defi', [('anim_newtoncannon_d_' + d, d) for d in C.DEFIS], 'aucun')
        self.c_astre.currentIndexChanged.connect(lambda *_: self._astre_change())
        self.c_defi.currentIndexChanged.connect(lambda *_: self._defi_change())
        self.c_air.toggled.connect(lambda *_: self._visibilites())
        for a in C.NOMS_ASTRES:
            self.r_alt[a].valueChanged.connect(lambda *_: self._reperes())
        self._visibilites()
        self._reperes()

    # ------------------------------------------------------------ réglages
    def astre(self) -> str:
        return self.c_astre.currentData() or 'terre'

    def altitude_m(self) -> float:
        a = self.astre()
        return self.r_alt[a].value() * C.REGLAGES[a]['ua']

    def vitesse_ms(self) -> float:
        a = self.astre()
        return self.r_vit[a].value() * C.REGLAGES[a]['uv']

    def air(self) -> bool:
        return self.c_air.isChecked() and C.atmosphere(self.astre())

    def _visibilites(self):
        a = self.astre()
        for k in C.NOMS_ASTRES:
            self.r_alt[k].setVisible(k == a)
            self.r_vit[k].setVisible(k == a)
        self.c_air.setVisible(C.atmosphere(a))
        self.c_projectile._boite.setVisible(self.air())

    def _reperes(self):
        """Repères v₁ et v₂ sous le curseur de vitesse de l'astre choisi (ils glissent avec l'altitude)."""
        a = self.astre()
        A = C.ASTRES[a]
        r0 = A['r'] + self.altitude_m()
        uv = C.REGLAGES[a]['uv']
        self.r_vit[a].poser_reperes([(C.v_satellisation(A['gm'], r0) / uv, 'v₁', 'accent2'),
                                     (C.v_liberation(A['gm'], r0) / uv, 'v₂', 'accent3')])

    def _astre_change(self):
        a = self.astre()
        self.tirs = []
        self.manuel = None
        self.arreter()
        self.c_temps.setCurrentIndex(max(0, self.c_temps.findData(C.REGLAGES[a]['temps'])))
        self._visibilites()
        self._reperes()

    def _defi_change(self):
        ctx = C.contexte_defi(self.c_defi.currentData() or 'aucun')
        if not ctx:
            self.rafraichir()
            return
        self.c_astre.setCurrentIndex(max(0, self.c_astre.findData(ctx['astre'])))
        a = ctx['astre']
        self.r_alt[a].setValue(ctx['altitude'] / C.REGLAGES[a]['ua'])
        self.c_air.setChecked(ctx['air'])
        self.c_projectile.setCurrentIndex(max(0, self.c_projectile.findData(ctx['projectile'])))
        self.tirs = []
        self.manuel = None
        self._visibilites()
        self._reperes()
        self.rafraichir()

    def prereglage(self, nom: str):
        """Applique un préréglage (astre, altitude, vitesse, angle, air) et tire aussitôt."""
        p = C.prereglage(nom, self.astre())
        if p['astre'] != self.astre():
            self.c_astre.setCurrentIndex(max(0, self.c_astre.findData(p['astre'])))
        a = p['astre']
        R = C.REGLAGES[a]
        self.r_alt[a].setValue(p['altitude'] / R['ua'])
        self.r_vit[a].setValue(p['v'] / R['uv'])
        self.r_angle.setValue(p['angle'])
        self.c_air.setChecked(p['air'])
        self.c_projectile.setCurrentIndex(max(0, self.c_projectile.findData(p['projectile'])))
        self._visibilites()
        self._reperes()
        self.feu()

    def etat_initial(self):
        self.tirs = []
        self.n_tirs = 0
        self.manuel = None
        self._visibilites()
        self._reperes()

    # ------------------------------------------------------------ tirs
    def feu(self):
        self.n_tirs += 1
        t = C.Tir(self.n_tirs, self.astre(), self.altitude_m(), self.vitesse_ms(), self.r_angle.value(), self.air(),
                  self.c_projectile.currentData() or 'boulet')
        t.couleur = COULEURS_TIRS[(self.n_tirs - 1) % len(COULEURS_TIRS)]
        self.tirs.append(t)
        if len(self.tirs) > MAX_TIRS:
            del self.tirs[0]
        if not self.en_lecture:
            self.basculer_lecture()
        self.rafraichir()

    def recommencer(self):
        if not self.tirs:
            self.feu()
            return
        d = self.tirs[-1]
        t = C.Tir(d.n, d.astre, d.altitude, d.v, d.angle, d.air, d.projectile)
        t.couleur = d.couleur
        self.tirs[-1] = t
        if not self.en_lecture:
            self.basculer_lecture()
        self.rafraichir()

    def effacer(self):
        self.tirs = []
        self.rafraichir()

    def recadrer(self):
        self.manuel = None
        self.rafraichir()

    def courant(self):
        return self.tirs[-1] if self.tirs else None

    def avancer(self, dt):
        t = self.courant()
        if t is None or t.etat != 'vol':
            return
        t.avancer(dt * float(self.c_temps.currentData() or 100))

    # ------------------------------------------------------------ souris et clavier
    def _vers_ecran(self, x, y):
        v = self._cam
        return v['cx'] + (x - v['ox']) * v['s'], v['cy'] - (y - v['oy']) * v['s']

    def _vers_monde(self, X, Y):
        v = self._cam
        return v['ox'] + (X - v['cx']) / v['s'], v['oy'] - (Y - v['cy']) / v['s']

    def _k_fleche(self):
        """Pixels par m·s⁻¹ de la flèche (la vitesse maximale du curseur fait FLECHE × le plus petit côté)."""
        a = self.astre()
        return FLECHE * self._cam['L'] / (C.REGLAGES[a]['vmax'] * C.REGLAGES[a]['uv'])

    def _bouche(self):
        A = C.ASTRES[self.astre()]
        return self._vers_ecran(0.0, A['r'] + self.altitude_m())

    def _bout(self):
        X, Y = self._bouche()
        L = self.vitesse_ms() * self._k_fleche()
        a = math.radians(self.r_angle.value())
        return X + L * math.cos(a), Y - L * math.sin(a)

    def presser(self, pos, bouton) -> bool:
        tx, ty = self._bout()
        X, Y = self._bouche()
        if math.hypot(pos.x() - tx, pos.y() - ty) <= 16 or math.hypot(pos.x() - X, pos.y() - Y) <= 12:
            # vue figée pendant qu'on tire la flèche (sinon le cadrage suivrait la trajectoire prévue et la flèche fuirait)
            self._fige = True
            self._glisse = self._tirer_fleche
            return True
        if self.manuel is not None:
            self._depart_pan = (pos.x(), pos.y(), self.manuel['ox'], self.manuel['oy'])
            self._glisse = self._deplacer_vue
            return True
        return False

    def relacher(self, pos):
        super().relacher(pos)
        if getattr(self, '_fige', False):
            self._fige = False
            self.rafraichir()

    def _tirer_fleche(self, q):
        X, Y = self._bouche()
        dx, dy = q.x() - X, -(q.y() - Y)
        if not (math.isfinite(dx) and math.isfinite(dy)):
            return
        a = self.astre()
        ang = math.degrees(math.atan2(dy, dx))
        if abs(ang) <= 1.5:
            ang = 0.0                    # aimanté à l'horizontale (le tir de Newton)
        self.r_angle.setValue(max(-90.0, min(90.0, ang)))
        self.r_vit[a].setValue(self.r_vit[a].aimanter(math.hypot(dx, dy) / self._k_fleche() / C.REGLAGES[a]['uv']))

    def _deplacer_vue(self, q):
        x0, y0, ox, oy = self._depart_pan
        s = self._cam['s']
        if self.manuel is not None and s > 0:
            self.manuel['ox'] = ox - (q.x() - x0) / s
            self.manuel['oy'] = oy + (q.y() - y0) / s

    def molette(self, pos, delta) -> bool:
        self.zoomer(1.2 ** max(-10.0, min(10.0, delta / 120.0)), pos.x(), pos.y())
        return True

    def zoomer(self, f: float, X: float, Y: float):
        """Zoom de f autour du point (X, Y) de la toile : le cadrage devient manuel."""
        if not (math.isfinite(f) and f > 0):
            return
        v = self._cam
        x, y = self._vers_monde(X, Y)
        s = max(1e-12, v['s'] * f)
        ox = x - (X - v['cx']) / s
        oy = y + (Y - v['cy']) / s
        self.manuel = {'s': s / v['L'], 'ox': ox, 'oy': oy}
        self.rafraichir()

    def double_clic(self, pos) -> bool:
        self.recadrer()
        return True

    def touche(self, ev) -> bool:
        k = ev.key()
        maj = bool(ev.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        a = self.astre()
        if k in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.feu()
        elif k in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            r = self.r_vit[a]
            pas = (5 if maj else 1) * C.REGLAGES[a]['vmax'] / 200
            r.setValue(r.value() + (pas if k == Qt.Key.Key_Up else -pas))
        elif k in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            pas = 5.0 if maj else 1.0
            self.r_angle.setValue(self.r_angle.value() + (pas if k == Qt.Key.Key_Left else -pas))
        elif k in (Qt.Key.Key_Plus, Qt.Key.Key_Equal, Qt.Key.Key_Minus):
            c = self._panneau.center()
            self.zoomer(1.25 if k != Qt.Key.Key_Minus else 0.8, c.x(), c.y())
        elif k == Qt.Key.Key_0:
            self.recadrer()
        else:
            return False
        return True

    # ------------------------------------------------------------ valeurs
    def _dist(self, m: float) -> str:
        R = C.REGLAGES[self.astre()]
        if R['na'] == 'm':
            return '%s m' % nombre(m, 0 if abs(m) >= 100 else 1)
        km = m / 1000
        return '%s km' % nombre(km, 0 if abs(km) >= 100 else 1)

    def _vit(self, v: float, a: str | None = None) -> str:
        R = C.REGLAGES[a or self.astre()]
        return '%s %s' % (nombre(v / R['uv'], R['dv']), R['nv'])

    def _energie(self, e: float) -> str:
        a = self.astre()
        f, u = {'ceres': (1e3, 'kJ·kg⁻¹'), 'dimorphos': (1e-3, 'mJ·kg⁻¹')}.get(a, (1e6, 'MJ·kg⁻¹'))
        return '%s %s' % (nombre(e / f, 2), u)

    def _tir_regle(self):
        A = C.ASTRES[self.astre()]
        x, y, vx, vy = C.etat_tir(A['r'], self.altitude_m(), self.vitesse_ms(), self.r_angle.value())
        return (x, y), C.elements(A['gm'], A['r'], x, y, vx, vy)

    def valeurs(self):
        a = self.astre()
        A = C.ASTRES[a]
        r0 = A['r'] + self.altitude_m()
        v1, v2 = C.v_satellisation(A['gm'], r0), C.v_liberation(A['gm'], r0)
        v = self.vitesse_ms()
        out = [(tr('anim_newtoncannon_v_reperes'), tr('anim_newtoncannon_v_reperes_val', v1=self._vit(v1),
                                                         v2=self._vit(v2))),
               (tr('anim_newtoncannon_v_tir'), tr('anim_newtoncannon_v_tir_val', v=self._vit(v), k1=nombre(v / v1, 2),
                                                  k2=nombre(v / v2, 2), a=nombre(self.r_angle.value(), 1) + '°'))]
        _, el = self._tir_regle()
        out.append((tr('anim_newtoncannon_v_trajectoire'),
                    tr('anim_newtoncannon_v_type_val', t=tr('anim_newtoncannon_ty_' + el['type']),
                       e=nombre(el['e'], 3))))
        hp = el['rp'] - A['r']
        p_txt = self._dist(hp) if hp >= 0 else tr('anim_newtoncannon_sous_sol', h=self._dist(hp))
        a_txt = self._dist(el['ra'] - A['r']) if math.isfinite(el['ra']) else tr('anim_newtoncannon_infini')
        out.append((tr('anim_newtoncannon_v_apsides'), '%s · %s' % (p_txt, a_txt)))
        if el['type'] in ('cercle', 'ellipse'):
            out.append((tr('anim_newtoncannon_v_periode'), '%s (%s)' % (periode(el['T']), duree(el['T']))))
        cle = 'anim_newtoncannon_lie' if el['eps'] < 0 else 'anim_newtoncannon_libre'
        out.append((tr('anim_newtoncannon_v_energie'), tr(cle, e=self._energie(el['eps']))))
        t = self.courant()
        if t is not None:
            out.append((tr('anim_newtoncannon_v_tir_n', n=t.n), self._bilan(t)))
            if t.air and t.etat == 'vol':
                fr = t.freinage()
                b = t.boulet
                rho = C.densite(t.astre, math.sqrt(b.x * b.x + b.y * b.y) - t.R)
                out.append((tr('anim_newtoncannon_v_freinage'),
                            tr('anim_newtoncannon_freinage_val', a='%s m·s⁻²' % nombre(fr, 2),
                               g=nombre(fr / G0, 2), r=self._densite(rho))))
        d = self.c_defi.currentData() or 'aucun'
        if d != 'aucun':
            out.append((tr('anim_newtoncannon_v_defi'), '%s %s' % (tr('anim_newtoncannon_de_' + d),
                                                                   self._verdict(d, t))))
        return out

    def _densite(self, rho: float) -> str:
        from .gravite_orbites import sci
        return '%s kg·m⁻³' % (sci(rho, 3) if rho > 0 else nombre(0, 0))

    def _bilan(self, t) -> str:
        if t.etat == 'impact':
            return tr('anim_newtoncannon_impact', t=duree(t.t), d=self._dist(t.distance_sol()),
                      a=nombre(t.angle_balaye_deg(), 1) + '°')
        if t.etat == 'libere':
            return tr('anim_newtoncannon_libere', d=self._dist(t.rayon()), t=duree(t.t))
        h = self._dist(t.rayon() - t.R)
        if t.tours() >= 1:
            return tr('anim_newtoncannon_en_orbite', n=t.tours(), T=periode(t.periode()), Tk=periode(t.el0['T']), h=h)
        return tr('anim_newtoncannon_en_vol', t=duree(t.t), h=h, v=self._vit(t.vitesse(), t.astre))

    def verdict(self, d=None, t=None):
        """(état, texte) du défi en cours pour le dernier tir."""
        d = d or self.c_defi.currentData() or 'aucun'
        t = self.courant() if t is None else t
        if t is None:
            return 'attente', tr('anim_newtoncannon_ve_a_tirer')
        etat, cle, p = C.juger(d, t)
        if etat == 'aucun':
            return etat, ''
        q = {}
        for k, x in p.items():
            if k == 'e':
                q[k] = nombre(x, 3)
            elif k == 'p':
                q[k] = nombre(x, 1)
            elif k == 'h':
                q[k] = self._dist(x)
            elif k == 'd':
                q[k] = nombre(x, 1) + '°'
        if etat == 'reussi':
            return etat, tr('anim_newtoncannon_ve_reussi', d=tr('anim_newtoncannon_ve_' + cle, **q))
        return etat, tr('anim_newtoncannon_ve_' + cle, **q)

    def _verdict(self, d, t) -> str:
        return '— ' + self.verdict(d, t)[1]

    # ------------------------------------------------------------ cadrage
    def _apercu_pts(self):
        A = C.ASTRES[self.astre()]
        cle = (self.astre(), self.altitude_m(), self.vitesse_ms(), self.r_angle.value())
        if self._apercu[0] != cle:
            (x, y), el = self._tir_regle()
            self._apercu = (cle, C.conique(el, x, y, A['r'], C.limite_apercu(el)))
        return self._apercu[1]

    def _cadrer(self, r: QRectF):
        A = C.ASTRES[self.astre()]
        R = A['r']
        L = min(r.width(), r.height())
        if getattr(self, '_fige', False) and self._cam['L'] == L:
            return
        self._cam['L'] = L
        self._cam['cx'], self._cam['cy'] = r.center().x(), r.center().y()
        if self.manuel is not None:
            self._cam.update(s=self.manuel['s'] * L, ox=self.manuel['ox'], oy=self.manuel['oy'])
            return
        # bande du haut laissée à la légende des tirs (et au temps écoulé)
        haut_l = min(0.25 * r.height(), 18.0 + 15.0 * len(self.tirs)) if self.tirs else 0.0
        self._cam['cy'] = r.center().y() + haut_l / 2
        r0 = R + self.altitude_m()
        x0, x1, y0, y1 = -R, R, -R, max(R, r0)
        pts = [q for q in self._apercu_pts() if q is not None] if self.c_apercu.isChecked() else []
        t = self.courant()
        if t is not None and t.astre == self.astre():
            n = len(t.x)
            pas = max(1, n // 400)
            pts += [(t.x[i], t.y[i]) for i in range(0, n, pas)]
            b = t.boulet
            pts.append((b.x, b.y))
        for x, y in pts:
            if x < x0:
                x0 = x
            if x > x1:
                x1 = x
            if y < y0:
                y0 = y
            if y > y1:
                y1 = y
        s = min(0.9 * r.width() / (x1 - x0), 0.88 * (r.height() - haut_l) / (y1 - y0))
        self._cam.update(s=s, ox=(x0 + x1) / 2, oy=(y0 + y1) / 2)
        # la flèche reste dans le panneau (sa longueur est en pixels)
        tx, ty = self._bout()
        X, Y = self._bouche()
        dy = 0.0
        haut = min(ty, Y) - (r.top() + 14)
        if haut < 0:
            dy = haut
        bas = max(ty, Y) - (r.bottom() - 14)
        if bas > 0 and dy == 0:
            dy = bas
        dx = 0.0
        if tx > r.right() - 14:
            dx = tx - (r.right() - 14)
        elif tx < r.left() + 14:
            dx = tx - (r.left() + 14)
        self._cam['ox'] += dx / s
        self._cam['oy'] -= dy / s

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        a = self.astre()
        A = C.ASTRES[a]
        r = dessin.cadre(p, rect, tr('anim_newtoncannon_titre', a=tr('anim_newtoncannon_a_' + a)))
        self._panneau = QRectF(r)
        self._cadrer(r)
        s = self._cam['s']
        p.save()
        p.setClipRect(r)
        cx, cy = self._vers_ecran(0.0, 0.0)
        R = A['r'] * s
        # atmosphère (à l'échelle : 100 km, ou 10 hauteurs d'échelle sur Mars)
        if self.air():
            ep = (C.KARMAN if a == 'terre' else 10 * C.H_MARS) * s
            if ep >= 1.5:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(dessin.c('ciel', 0.45)))
                p.drawEllipse(QPointF(cx, cy), R + ep, R + ep)
        dessin.astre(p, cx, cy, max(R, 2.0), COULEUR_ASTRE[a])
        self._montagne(p)
        for t in self.tirs:
            self._trace(p, t)
        if self.c_apercu.isChecked():
            self._dessiner_apercu(p)
        self._canon(p)
        for t in self.tirs:
            self._boulet(p, t)
        p.restore()
        self._legende(p, r)
        self._echelle(p, r)
        self._bandeau(p, r)

    def _montagne(self, p):
        A = C.ASTRES[self.astre()]
        R = A['r']
        h = self.altitude_m()
        s = self._cam['s']
        demi = max(1.1 * h, 9.0 / s) / R          # demi-largeur angulaire de la base
        demi = min(demi, 0.6)
        X, Y = self._vers_ecran(0.0, R + h)
        pts = [QPointF(X, Y)]
        for k in range(9):
            u = demi - 2 * demi * k / 8
            pts.append(QPointF(*self._vers_ecran(-R * math.sin(u), R * math.cos(u))))
        p.setPen(dessin.stylo('horizon', 1.2))
        p.setBrush(QBrush(dessin.c('sol', 0.9)))
        p.drawPolygon(QPolygonF(pts))

    def _canon(self, p):
        X, Y = self._bouche()
        ang = math.radians(self.r_angle.value())
        ux, uy = math.cos(ang), -math.sin(ang)
        # fût
        p.setPen(dessin.stylo('texte', 5.0))
        p.drawLine(QPointF(X - 4 * ux, Y - 4 * uy), QPointF(X + 12 * ux, Y + 12 * uy))
        p.setPen(dessin.stylo('texte', 1.2))
        p.setBrush(QBrush(dessin.c('fond')))
        p.drawEllipse(QPointF(X - 2 * ux, Y + 4), 3.5, 3.5)
        # cercles v₁, v₂ (vitesses à porter de flèche) et flèche
        A = C.ASTRES[self.astre()]
        r0 = A['r'] + self.altitude_m()
        k = self._k_fleche()
        for v, cle, txt in ((C.v_satellisation(A['gm'], r0), 'accent2', 'anim_newtoncannon_v1'),
                            (C.v_liberation(A['gm'], r0), 'accent3', 'anim_newtoncannon_v2')):
            rr = v * k
            p.setPen(dessin.stylo(cle, 1.2, 0.8, True))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(X - rr, Y - rr, 2 * rr, 2 * rr), -20 * 16, 220 * 16)
            # étiquette sur l'arc, au premier endroit qui tient dans le panneau
            dessin.police(p, 0.82)
            w = p.fontMetrics().horizontalAdvance(tr(txt)) / 2 + 6
            hh = p.fontMetrics().height()
            pr = self._panneau
            for deg in (55, 125, 90, 20, 160, -15):
                ex, ey = X + rr * math.cos(math.radians(deg)), Y - rr * math.sin(math.radians(deg))
                if pr.left() + w <= ex <= pr.right() - w and pr.top() + hh <= ey <= pr.bottom() - hh:
                    dessin.texte(p, ex, ey, tr(txt), cle, fond=True)
                    break
            dessin.police(p, 1 / 0.82)
        tx, ty = self._bout()
        if math.hypot(tx - X, ty - Y) > 3:
            dessin.fleche(p, X, Y, tx, ty, dessin.stylo('horizon', 2.6), 10)
        p.setPen(dessin.stylo('horizon', 1.6))
        p.setBrush(QBrush(dessin.c('horizon', 0.3)))
        p.drawEllipse(QPointF(tx, ty), 7, 7)
        dessin.reserver(p, tx, ty, 8, True)

    def _dessiner_apercu(self, p):
        p.setPen(dessin.stylo('doux', 1.3, 0.9, True))
        p.setBrush(Qt.BrushStyle.NoBrush)
        morceau = []
        for q in list(self._apercu_pts()) + [None]:     # None : coupure (ellipse sortie du cadre, puis retour)
            if q is not None:
                morceau.append(QPointF(*self._vers_ecran(*q)))
                continue
            if len(morceau) >= 2:
                p.drawPolyline(QPolygonF(morceau))
            morceau = []

    def _trace(self, p, t):
        if t.astre != self.astre() or len(t.x) < 1:
            return
        n = len(t.x)
        pas = max(1, math.ceil(n / POINTS_TRACE))
        idx = list(range(0, n, pas))
        if idx[-1] != n - 1:
            idx.append(n - 1)
        pts = [QPointF(*self._vers_ecran(t.x[i], t.y[i])) for i in idx]
        b = t.boulet
        if t.etat == 'vol':
            pts.append(QPointF(*self._vers_ecran(b.x, b.y)))
        courant = t is self.courant()
        p.setPen(dessin.stylo(t.couleur, 2.0 if courant else 1.4, 1.0 if courant else 0.75))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF(pts))

    def _boulet(self, p, t):
        if t.astre != self.astre():
            return
        b = t.boulet
        X, Y = self._vers_ecran(b.x, b.y)
        if t.etat == 'impact':
            p.setPen(dessin.stylo(t.couleur, 2.0))
            for dx, dy in ((5, 5), (5, -5)):
                p.drawLine(QPointF(X - dx, Y - dy), QPointF(X + dx, Y + dy))
        else:
            dessin.disque(p, X, Y, 4.5 if t is self.courant() else 3.0, t.couleur, bord='fond')

    def _legende(self, p, r):
        if not self.tirs:
            return
        dessin.police(p, 0.85)
        fm = p.fontMetrics()
        y = r.top() + 4 + fm.ascent()
        # cartouche sous la légende : les arcs et les traces passent dessous sans gêner la lecture
        larg = max(fm.horizontalAdvance(tr('anim_newtoncannon_legende', n=t.n, v=self._vit(t.v, t.astre),
                                           a=nombre(t.angle, 1) + '°')) for t in self.tirs)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(dessin.c('fond', 0.78)))
        p.drawRoundedRect(QRectF(r.left() + 1, r.top() + 2, larg + 26, fm.height() * len(self.tirs) + 4), 4, 4)
        for t in self.tirs:
            s = tr('anim_newtoncannon_legende', n=t.n, v=self._vit(t.v, t.astre), a=nombre(t.angle, 1) + '°')
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(dessin.c(t.couleur)))
            p.drawRoundedRect(QRectF(r.left() + 4, y - fm.ascent() + 2, 12, fm.ascent() - 2), 2, 2)
            dessin.texte(p, r.left() + 20, y, s, 'texte' if t.astre == self.astre() else 'doux', centre=False)
            y += fm.height()
        dessin.police(p, 1 / 0.85)

    def _echelle(self, p, r):
        s = self._cam['s']
        lg = echelle_nette(0.22 * r.width() / s)
        w = lg * s
        x0, y0 = r.left() + 10, r.bottom() - 10
        p.setPen(dessin.stylo('texte', 1.6))
        p.drawLine(QPointF(x0, y0), QPointF(x0 + w, y0))
        p.drawLine(QPointF(x0, y0 - 4), QPointF(x0, y0 + 1))
        p.drawLine(QPointF(x0 + w, y0 - 4), QPointF(x0 + w, y0 + 1))
        dessin.police(p, 0.85)
        dessin.texte(p, x0 + w + 6, y0 + 4, self._dist(lg), 'texte', centre=False)
        dessin.police(p, 1 / 0.85)

    def _bandeau(self, p, r):
        t = self.courant()
        dessin.police(p, 0.9)
        if t is not None:
            k = int(self.c_temps.currentData() or 100)
            s = tr('anim_newtoncannon_temps_ecoule', t=duree(t.t), k='×' + nombre(k, 0))
            w = p.fontMetrics().horizontalAdvance(s)
            dessin.texte(p, r.right() - w - 6, r.top() + 12, s, 'texte', centre=False, fond=True)
        d = self.c_defi.currentData() or 'aucun'
        if d != 'aucun':
            etat, txt = self.verdict(d, t)
            if etat in ('reussi', 'echec'):
                cle = 'horizon' if etat == 'reussi' else 'accent3'
                titre = tr('anim_newtoncannon_reussi' if etat == 'reussi' else 'anim_newtoncannon_rate')
                dessin.police(p, 1.15, gras=True)
                dessin.texte(p, r.center().x(), r.bottom() - 34, titre, cle, fond=True)
                dessin.police(p, 1 / 1.15)
        dessin.police(p, 1 / 0.9)
