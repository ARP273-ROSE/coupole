"""Spectrum Explorer : spectres continu, d'émission et d'absorption d'une étoile de type spectral et de classe de
luminosité choisis.  Modèle physique (spectre_physique.py) : intensités des familles de raies calculées par
Saha–Boltzmann sur des atmosphères ATLAS9 (courbes lisses, une par classe), 133 raies NIST, bandes TiO et CH dégradées,
continu de Planck coloré (CIE 1931).  Remplace les segments de droite et les 37 raies de l'original.  Même rendu que
Coupole Web (explorateur_spectres.ts)."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin, hr
from ..base import Animation, nombre
from ..graphe import Axes
from ..spectre_physique import (COULEURS_FAMILLES, FAMILLES, LAMBDA_MAX, LAMBDA_MIN, dessiner_bande, modele,
                                remarques)

T_AXE = (40000, 30000, 20000, 15000, 10000, 8000, 7000, 6000, 5000, 4000, 3500, 3000)
NOMS_H = {'656.3': 'Hα', '486.1': 'Hβ', '434.0': 'Hγ', '410.2': 'Hδ', '397.0': 'Hε', '388.9': 'H8', '383.5': 'H9'}
_COURBES: dict = {}


def courbes(classe: str) -> dict:
    """Courbes des intensités d'une classe (0 à 69 par quart de type), mises en cache."""
    c = _COURBES.get(classe)
    if c is None:
        m = modele()
        c = {f: [] for f in FAMILLES + ('ch',)}
        for k in range(277):
            t = k / 4
            it = m.intensites(t, classe)
            for f in c:
                c[f].append((t, it[f]))
        _COURBES[classe] = c
    return c


_TYPES_T: dict = {}


def type_de_temperature(T: float, classe: str):
    """Type spectral (réel) où la classe atteint la température T, ou None (premier croisement) ; mis en cache."""
    cle = (T, classe)
    if cle not in _TYPES_T:
        _TYPES_T[cle] = _type_de_temperature(T, classe)
    return _TYPES_T[cle]


def _type_de_temperature(T: float, classe: str):
    m = modele()
    avant = m.etalonnage(0, classe)['teff']
    for k in range(1, 691):
        t = k / 10
        v = m.etalonnage(t, classe)['teff']
        if (avant - T) * (v - T) <= 0 and avant != v:
            return t - 0.1 + 0.1 * (avant - T) / (avant - v)
        avant = v
    return None


def nom_raie(espece: str, lam: float) -> str:
    """Nom court d'une raie : Hα…Hε, sinon l'espèce (Ca II, Fe I…)."""
    return NOMS_H.get('%.1f' % lam, espece)


class ExplorateurSpectres(Animation):
    ID = 'spectrum010'
    ANIMEE = False

    def construire(self):
        self.mode = self.choix('mode', [('anim_spectrum010_continu', 'continu'), ('anim_spectrum010_emission', 'emission'),
                                        ('anim_spectrum010_absorption', 'absorption')], 'absorption')
        self.sp = self.curseur('type', 0.0, 69.0, 42.0, dec=0)
        self.classe = self.choix('classe', [('anim_spectroparallax_c_I', 'I'), ('anim_spectroparallax_c_III', 'III'),
                                            ('anim_spectroparallax_c_V', 'V')], 'V')
        self.cases = {f: self.coche('f_' + f, True) for f in FAMILLES}
        self._etat()

    def _etat(self):
        mode = self.mode.currentData()
        for c in self.cases.values():
            c.setEnabled(mode != 'continu')

    def reglage_change(self):
        self._etat()
        super().reglage_change()

    def _cl(self) -> str:
        return self.classe.currentData()

    def temperature(self) -> float:
        return modele().etalonnage(self.sp.value(), self._cl())['teff']

    def familles(self) -> list:
        return [f for f in FAMILLES if self.cases[f].isChecked()]

    def valeurs(self):
        mode = self.mode.currentData()
        t, cl = self.sp.value(), self._cl()
        e = modele().etalonnage(t, cl)
        out = [(tr('anim_spectrum010_mode_v'), tr('anim_spectrum010_' + mode)),
               (tr('anim_spectrum010_type_v'), '%s %s' % (hr.nom_type(t), cl)),
               (tr('anim_stellarlum_temperature'), '%s K' % nombre(e['teff'], 0)),
               (tr('anim_spectrum010_logg'), nombre(e['logg'], 2))]
        if mode != 'continu':
            it = modele().intensites(t, cl)
            fam = self.familles()
            fortes = [tr('anim_spectrum010_f_' + f) for f in fam if it[f] >= 50]
            out.append((tr('anim_spectrum010_fortes'), ', '.join(fortes) or tr('anim_c_aucun')))
            raies = sorted((r for r in modele().raies(t, cl) if r['famille'] in fam), key=lambda r: -r['W'])[:3]
            out.append((tr('anim_spectrum010_principales'),
                        ', '.join('%s %s nm' % (nom_raie(r['espece'], r['lambda']), nombre(r['lambda'], 1)) for r in raies)
                        or tr('anim_c_aucun')))
        rq = remarques(t, cl, e)
        if rq:
            out.append((tr('anim_spectrum010_remarque'), ' ; '.join(rq)))
        return out

    def dessiner(self, p, rect):
        mode = self.mode.currentData()
        t, cl = self.sp.value(), self._cl()
        z = dessin.zones(rect, 2, 10.0)
        r = dessin.cadre(p, z[0], tr('anim_spectrum010_titre_' + mode))
        fm = p.fontMetrics()
        rq = remarques(t, cl)
        bas_note = fm.height() + 2 if rq else 0
        haut_noms = fm.height() * 0.85 + 4 if mode == 'absorption' and r.height() > 90 else 0
        bande = QRectF(r.x() + 10, r.y() + 6 + haut_noms, r.width() - 20, max(24.0, r.height() - 34 - haut_noms - bas_note))
        fam = [] if mode == 'continu' else self.familles()
        dessiner_bande(p, bande, t, cl, mode, None if mode == 'continu' else fam)
        if haut_noms:
            self._noms_raies(p, bande, t, cl, fam)
        if rq:
            dessin.police(p, 0.8)
            dessin.texte(p, bande.left(), bande.bottom() + 14 + fm.height() * 0.8, '⚠ ' + ' ; '.join(rq), 'accent1',
                         centre=False)
            dessin.police(p, 1 / 0.8)
        self._intensites(p, z[1], t, cl)

    def _noms_raies(self, p, bande, t, cl, fam):
        """Noms des raies les plus fortes au-dessus de la bande (sans chevauchement)."""
        raies = sorted((r for r in modele().raies(t, cl) if r['famille'] in fam and LAMBDA_MIN <= r['lambda'] <= LAMBDA_MAX),
                       key=lambda r: -r['W'])
        n = 3 if bande.width() < 360 else 5 if bande.width() < 640 else 7
        dessin.police(p, 0.75)
        fm = p.fontMetrics()
        poses = []
        for r in raies[:n]:
            x = bande.left() + bande.width() * (r['lambda'] - LAMBDA_MIN) / (LAMBDA_MAX - LAMBDA_MIN)
            s = nom_raie(r['espece'], r['lambda'])
            w = fm.horizontalAdvance(s) + 4
            g = max(bande.left(), min(bande.right() - w, x - w / 2))
            if any(g < b and g + w > a for a, b in poses):
                continue
            poses.append((g, g + w))
            p.setPen(dessin.stylo('doux', 1.0, 0.8))
            p.drawLine(QPointF(x, bande.top() - 3), QPointF(x, bande.top()))
            dessin.texte(p, g + 2, bande.top() - 5, s, 'doux', centre=False)
        dessin.police(p, 1 / 0.75)

    def _intensites(self, p, zone, t, cl):
        """Graphe des intensités des familles (0–100) en fonction du type, températures de la classe en haut."""
        r2 = dessin.cadre(p, zone, tr('anim_spectrum010_titre_intensites'))
        dessin.police(p, 0.85)
        fm = p.fontMetrics()
        noms = [tr('anim_spectrum010_f_' + f) for f in FAMILLES]
        lmax = max(fm.horizontalAdvance(s) for s in noms) + 22
        ligne = fm.height() + 2
        a_droite = r2.width() - lmax - 50 >= 240
        rangees = []
        if not a_droite:
            x, rangee = 0, 0
            for i, _ in enumerate(FAMILLES):
                w = fm.horizontalAdvance(noms[i]) + 24
                if x > 0 and x + w > r2.width() - 12:
                    rangee += 1
                    x = 0
                rangees.append((i, x, rangee))
                x += w
        n_rangees = 0 if a_droite else max(q[2] for q in rangees) + 1
        haut_legende = n_rangees * ligne
        haut_t = fm.height() + 4 if r2.height() > 120 else 0
        dessin.police(p, 1 / 0.85)
        ax = Axes(r2, 0, 69, 0, 105, marges=(40, 6 + haut_t + haut_legende, lmax + 8 if a_droite else 10, 26)).avec(p)
        ax.fond(p, '', tr('anim_c_intensite'), fmt_x=lambda v: hr.nom_type(v), n_x=4 if r2.width() < 360 else 7)
        if haut_t:
            dessin.police(p, 0.75)
            fmt = p.fontMetrics()
            droite = -float('inf')
            for T in T_AXE:
                ty = type_de_temperature(T, cl)
                if ty is None or ty < 0 or ty > 69:
                    continue
                X = ax.px(ty)
                s = '%s K' % nombre(T, 0)
                w = fmt.horizontalAdvance(s)
                if X - w / 2 < droite + 8 or X - w / 2 < r2.left() or X + w / 2 > r2.right():
                    continue
                droite = X + w / 2
                p.setPen(dessin.stylo('grille', 1.0))
                p.drawLine(QPointF(X, ax.r.top() - 3), QPointF(X, ax.r.top()))
                dessin.texte(p, X, ax.r.top() - 6 - fmt.height() / 2 + 2, s, 'doux')
            dessin.police(p, 1 / 0.75)
        c = courbes(cl)
        dessin.police(p, 0.85)
        for i, f in enumerate(FAMILLES):
            actif = self.cases[f].isChecked()
            ax.courbe(c[f], COULEURS_FAMILLES[f], 2.0 if actif else 1.0, 1.0 if actif else 0.35)
            if f == 'molecules':
                ax.courbe(c['ch'], COULEURS_FAMILLES[f], 1.2, 0.8 if actif else 0.3, True)
            if a_droite:
                x, y = ax.r.right() + 8, ax.r.top() + 4 + ligne * i
            else:
                q = next(u for u in rangees if u[0] == i)
                x, y = r2.left() + 6 + q[1], r2.top() + 4 + haut_t + q[2] * ligne
            p.setPen(dessin.stylo(COULEURS_FAMILLES[f], 2.0, 1.0 if actif else 0.35))
            p.drawLine(QPointF(x, y + fm.height() / 2), QPointF(x + 14, y + fm.height() / 2))
            dessin.texte(p, x + 18, y + fm.ascent(), noms[i], COULEURS_FAMILLES[f], centre=False,
                         alpha=1.0 if actif else 0.6)
        dessin.police(p, 1 / 0.85)
        ax.verticale(t, 'texte', 1.5, False)
