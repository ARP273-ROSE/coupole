"""Spectroscopic Parallax Simulator : la distance d'une étoile sans mesurer sa parallaxe.  Le spectre donne le type
spectral et la classe de luminosité ; le diagramme HR donne alors la magnitude absolue M ; avec la magnitude
apparente m, le module de distance donne d = 10^((m − M + 5) / 5) parsecs.  Spectre, T_eff et M_V : modèle physique
(spectre_physique.py) ; là où aucune M_V n'est publiée (classes I hors O, II, IV, III de B à F), ancien étalonnage
(celui de l'original), signalé.  Même rendu que Coupole Web (parallaxe_spectro.ts)."""
from __future__ import annotations

import functools
import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPolygonF

from ....core.i18n import tr
from .. import astro, dessin, hr
from ..base import Animation, nombre
from ..spectre_physique import FAMILLES, couleur_etoile_teff, dessiner_bande, modele, remarques

LOG_T = (3.3617, 4.6812)
LOG_L = (-4.0, 6.0)
CLASSES = (('I', 1), ('II', 2), ('III', 3), ('IV', 4), ('V', 5))
NOM_CLASSE = {n: c for c, n in CLASSES}


@functools.lru_cache(maxsize=4096)                  # pure : la courbe de chaque classe est redessinée à chaque image
def magnitude_absolue(t: float, classe: int) -> dict:
    """Magnitude absolue M_V d'une étoile de type t et de classe n (1 = I … 5 = V) : T_eff et M_V du nouvel étalonnage
    (Mamajek 2022 pour V, Martins 2005 / van Belle 2021 pour III, Martins 2005 pour les supergéantes O) quand ils sont
    publiés ; sinon M_V de l'ancien étalonnage (celui de l'original : courbe de la classe au log T de l'original),
    signalé.  La température est toujours celle du nouvel étalonnage (celle du spectre)."""
    e = modele().etalonnage(t, NOM_CLASSE[classe])
    lt = math.log10(e['teff'])
    if e['mv'] is not None:
        ll = e['logl'] if e['logl'] is not None else hr.log_lum_de_mbol(e['mv'] + hr.correction_bolometrique(lt))
        return {'log_t': lt, 'log_l': ll, 'M': e['mv'], 'ancien': False, 'source': e['source'], 'dans_domaine': True}
    lt0 = hr.log_temp_de_type(t)
    ll = hr.log_lum_classe(lt0, classe)
    a, b = hr.CLASSES[classe]
    return {'log_t': lt, 'log_l': ll, 'M': hr.mbol_de_log_lum(ll) - hr.correction_bolometrique(lt0), 'ancien': True,
            'source': '', 'dans_domaine': a <= lt0 <= b}


def intensites(t: float, classe: str) -> dict:
    """Intensité (0 à 100) des familles de raies au type t et à la classe (modèle physique)."""
    return modele().intensites(t, classe)


def etiquette_lum(ll: int) -> str:
    return nombre(10.0 ** ll, max(0, -ll)) if ll < 3 else '10%s' % str(ll).translate(
        str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹'))


class ParallaxeSpectro(Animation):
    ID = 'spectroparallax'
    ANIMEE = False

    def construire(self):
        self.sp = self.curseur('type', 0.0, 69.0, 42.0, dec=0)
        self.classe = self.choix('classe', [('anim_spectroparallax_c_' + c, n) for c, n in CLASSES], 5)
        self.m = self.curseur('m', -5.0, 15.0, 1.0, dec=2)
        self.c_emission = self.coche('emission', False)
        self.echelle = self.choix('echelle', [('anim_spectrum010_e_pedago', 'pedagogique'),
                                              ('anim_spectrum010_e_realiste', 'realiste')], 'pedagogique',
                                  cle_texte='anim_spectrum010_echelle')
        self._graphe = None

    def _cl(self) -> str:
        return NOM_CLASSE[self.classe.currentData()]

    def resultat(self) -> dict:
        r = dict(magnitude_absolue(self.sp.value(), self.classe.currentData()))     # copie : le résultat est en cache
        r['d'] = astro.distance_du_module(self.m.value() - r['M'])
        return r

    def valeurs(self):
        r = self.resultat()
        out = [(tr('anim_spectroparallax_type_c'), '%s %s' % (hr.nom_type(self.sp.value()), self._cl())),
               (tr('anim_stellarlum_temperature'), '%s K' % nombre(10 ** r['log_t'], 0)),
               (tr('anim_spectroparallax_lum'), '%s L☉' % nombre(10 ** r['log_l'], 3 if r['log_l'] < 1 else 0)),
               (tr('anim_spectroparallax_M'), nombre(r['M'], 2)),
               (tr('anim_spectroparallax_module'), nombre(self.m.value() - r['M'], 2)),
               (tr('anim_spectroparallax_distance'), '%s pc (%s %s)' % (
                   nombre(r['d'], 1 if r['d'] < 1000 else 0), nombre(r['d'] * astro.PC_EN_AL, 0),
                   tr('anim_spectroparallax_al'))),
               (tr('anim_spectroparallax_raies'), self._description()),
               (tr('anim_spectroparallax_etalonnage'), tr('anim_spectroparallax_ancien') if r['ancien'] else r['source'])]
        rq = [x for x in remarques(self.sp.value(), self._cl()) if not r['ancien'] or x != tr('spectres_d_interpole')]
        if rq:
            out.append((tr('anim_spectrum010_remarque'), ' ; '.join(rq)))
        out.append((tr('anim_spectrum010_echelle_v'), tr('anim_spectrum010_e_pedago_v' if self.echelle.currentData() ==
                                                         'pedagogique' else 'anim_spectrum010_e_realiste_v')))
        return out

    def _description(self) -> str:
        parts = []
        it = intensites(self.sp.value(), self._cl())
        for famille in FAMILLES + ('ch',):
            v = it[famille]
            if v >= 1:
                q = 'tf' if v < 20 else 'f' if v < 40 else 'm' if v < 60 else 'F' if v < 85 else 'tF'
                parts.append(tr('anim_spectroparallax_q_' + q, f=tr('anim_spectroparallax_f_' + famille)))
        return ', '.join(parts)

    def presser(self, pos, bouton):
        if self._graphe is not None and self._graphe[0].contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        """Le doigt choisit une température sur l'axe : le type de la classe choisie qui l'a."""
        _, x0, x1 = self._graphe
        if not math.isfinite(pos.x()) or not x1 > x0:
            return
        lt = LOG_T[1] - (LOG_T[1] - LOG_T[0]) * (max(x0, min(x1, pos.x())) - x0) / (x1 - x0)
        m, cl = modele(), self._cl()
        meilleur, ecart = 0, float('inf')
        for t in range(70):
            d = abs(math.log10(m.etalonnage(t, cl)['teff']) - lt)
            if d < ecart:
                ecart, meilleur = d, t
        self.sp.setValue(meilleur)

    def dessiner(self, p, rect):
        haut = rect.height() * 0.7
        self._diagramme(p, dessin.cadre(p, QRectF(rect.x(), rect.y(), rect.width(), haut), tr('anim_spectroparallax_diagramme')))
        self._spectre(p, dessin.cadre(p, QRectF(rect.x(), rect.y() + haut, rect.width(), rect.height() - haut),
                                      tr('anim_spectroparallax_spectre')))

    def _diagramme(self, p, r):
        x0, x1, y0, y1 = r.x() + 40, r.right() - 8, r.y() + 4, r.bottom() - 30
        self._graphe = (QRectF(r), x0, x1)

        def xy(lt, ll):
            return QPointF(x1 - (x1 - x0) * (lt - LOG_T[0]) / (LOG_T[1] - LOG_T[0]),
                           y1 - (y1 - y0) * (ll - LOG_L[0]) / (LOG_L[1] - LOG_L[0]))

        p.setPen(dessin.stylo('grille', 1.0, 0.5))
        dessin.police(p, 0.72)
        for ll in range(-4, 7, 2):
            q = xy(LOG_T[0], ll)
            p.drawLine(QPointF(x0, q.y()), QPointF(x1, q.y()))
            dessin.texte(p, x0 - 18, q.y(), etiquette_lum(ll), 'doux')
        m = modele()
        for k, lettre in enumerate(hr.LETTRES):                       # types spectraux en abscisse (nouvelle classe V)
            q = xy(math.log10(m.etalonnage(10 * k + 5, 'V')['teff']), LOG_L[0])
            dessin.texte(p, q.x(), y1 + 12, lettre, 'doux')
        dessin.texte(p, (x0 + x1) / 2, y1 + 24, tr('anim_spectroparallax_axe_x'), 'doux')
        dessin.police(p, 1 / 0.72)
        for nom, n in CLASSES:
            choisie = n == self.classe.currentData()
            # nouvel étalonnage en trait plein, ancien en pointillé
            pts = [u for u in (magnitude_absolue(k / 2, n) for k in range(139)) if u['dans_domaine']]
            d = 0
            while d < len(pts) - 1:
                f = d + 1
                while f < len(pts) - 1 and pts[f]['ancien'] == pts[d]['ancien']:
                    f += 1
                morceau = [xy(u['log_t'], u['log_l']) for u in pts[d:f + 1]]
                p.setPen(dessin.stylo('accent3' if choisie else 'arc1', 2.2 if choisie else 1.0, 1.0 if choisie else 0.6,
                                      pointille=pts[d]['ancien']))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawPolyline(QPolygonF(morceau))
                d = f
            if pts:
                q0 = xy(pts[-1]['log_t'], pts[-1]['log_l'])
                dessin.etiquette(p, min(x1 - 14, q0.x()), q0.y(), nom, 'accent3' if choisie else 'doux', 5)
        res = self.resultat()
        q = xy(res['log_t'], res['log_l'])
        p.setPen(dessin.stylo('accent1', 1.0, 0.7, pointille=True))
        p.drawLine(QPointF(q.x(), y0), QPointF(q.x(), y1))
        p.drawLine(QPointF(x0, q.y()), QPointF(x1, q.y()))
        dessin.disque(p, q.x(), q.y(), 6, couleur_etoile_teff(10 ** res['log_t']), bord='texte')

    def _spectre(self, p, r):
        bande = QRectF(r.x() + 8, r.y() + 2, r.width() - 16, max(10.0, r.height() - 18))
        dessiner_bande(p, bande, self.sp.value(), self._cl(), 'emission' if self.c_emission.isChecked() else 'absorption',
                       None, True, self.echelle.currentData() == 'pedagogique', note=False)
