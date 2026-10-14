"""EM Spectrum Module : le spectre électromagnétique, des rayons gamma aux ondes radio.  Pour une longueur d'onde
choisie : fréquence ν = c / λ, énergie du photon E = h ν, température d'un corps noir dont le maximum tombe là
(loi de Wien), domaine (bornes de l'original), et objets de taille comparable.  L'original montrait des
photographies ; ici l'onde est dessinée à côté d'objets de la même taille.  Constantes exactes du SI (l'original
prenait c = 3 × 10⁸ m/s, h = 6,6 × 10⁻³⁴ J s)."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPolygonF

from ....core.i18n import tr
from .. import dessin, lumiere
from ..base import Animation, nombre
from ..graphe import degrade_spectre
from .gravitation import scientifique

LOG_MIN, LOG_MAX = -16.0, 4.0                  # 0,1 fm (gamma) à 10 km (radio)
DOMAINES = (('gamma', -16.0, -12.0, 'arc1'), ('x', -12.0, -9.0, 'accent2'), ('uv', -9.0, math.log10(4e-7), 'meridien'),
            ('visible', math.log10(4e-7), math.log10(7.5e-7), 'accent1'),
            ('ir_proche', math.log10(7.5e-7), math.log10(2.5e-6), 'accent3'),
            ('ir', math.log10(2.5e-6), math.log10(2.5e-5), 'mars'), ('micro_ondes', math.log10(2.5e-5), -3.0, 'horizon'),
            ('radio', -3.0, 4.0, 'equateur'))
# objets de taille comparable (mètres)
OBJETS = (('noyau', 1e-14), ('atome', 1e-10), ('molecule', 1e-9), ('virus', 1e-7), ('bacterie', 1e-6),
          ('cellule', 1e-5), ('cheveu', 1e-4), ('tete_epingle', 1e-3), ('fourmi', 5e-3), ('balle', 0.1),
          ('humain', 1.7), ('immeuble', 100.0), ('montagne', 3000.0))


class SpectreEM(Animation):
    ID = 'emspectrum'
    ANIMEE = False

    def construire(self):
        self.l = self.curseur('log_lambda', LOG_MIN, LOG_MAX, math.log10(5.5e-7), dec=2)
        self._zone = None

    def lam(self) -> float:
        return 10 ** self.l.value()

    def objet(self, lam):
        return min(OBJETS, key=lambda o: abs(math.log10(o[1]) - math.log10(lam)))

    def valeurs(self):
        lam = self.lam()
        e = lumiere.energie_photon_j(lam)
        return [(tr('anim_emspectrum_domaine'), tr('anim_emspectrum_d_' + lumiere.domaine_em(lam))),
                (tr('anim_emspectrum_lambda_v'), '%s m' % scientifique(lam, 4)),
                (tr('anim_emspectrum_frequence'), '%s Hz' % scientifique(lumiere.frequence(lam), 4)),
                (tr('anim_emspectrum_energie'), '%s J = %s eV' % (scientifique(e, 4), scientifique(e / lumiere.EV, 4))),
                (tr('anim_emspectrum_temperature'), '%s K' % scientifique(lumiere.temperature_de_pic(lam), 3)),
                (tr('anim_emspectrum_objet'), tr('anim_emspectrum_o_' + self.objet(lam)[0]))]

    def presser(self, pos, bouton):
        if self._zone is not None and self._zone.adjusted(0, -10, 0, 10).contains(pos):
            self._glisse = self._tirer
            self._tirer(pos)
            return True
        return False

    def _tirer(self, pos):
        r = self._zone
        t = max(0.0, min(1.0, (pos.x() - r.left()) / r.width()))
        self.l.setValue(LOG_MIN + t * (LOG_MAX - LOG_MIN))

    def dessiner(self, p, rect):
        lam = self.lam()
        ll = math.log10(lam)
        # bande des domaines (échelle logarithmique), du gamma (à gauche) à la radio
        bande = QRectF(rect.x() + 20, rect.y() + 34, rect.width() - 40, 34)
        self._zone = QRectF(bande)
        def x_de(lg):
            return bande.left() + bande.width() * (lg - LOG_MIN) / (LOG_MAX - LOG_MIN)
        dessin.police(p, 0.85)
        fins = {}                                    # bord droit du dernier libellé de chaque rangée
        for nom, a, b, cle in DOMAINES:
            r = QRectF(x_de(a), bande.top(), x_de(b) - x_de(a), bande.height())
            if nom == 'visible':
                p.fillRect(r, degrade_spectre(r.left(), r.right(), r.top(), 1.0, 380, 750))
            else:
                p.fillRect(r, dessin.c(cle, 0.45))
            # libellés serrés (petite fenêtre) : sur la première rangée libre au-dessus de la bande
            s_ = tr('anim_emspectrum_c_' + nom)
            w = p.fontMetrics().horizontalAdvance(s_)
            rang = 1 if nom == 'visible' else 0
            while fins.get(rang, -1e9) > r.center().x() - w / 2 - 4:
                rang += 1
            fins[rang] = r.center().x() + w / 2
            dessin.texte(p, r.center().x(), bande.top() - 9 - 12 * rang, s_, cle if nom != 'visible' else 'texte')
        for k in range(int(LOG_MIN) + 2, int(LOG_MAX), 2 if bande.width() >= 600 else 4):
            dessin.texte(p, x_de(k), bande.bottom() + 11, '10%s m' % str(k).translate(
                str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹')), 'doux')
        dessin.police(p, 1 / 0.85)
        xc = x_de(ll)
        p.setPen(dessin.stylo('texte', 2.0))
        p.drawLine(QPointF(xc, bande.top() - 3), QPointF(xc, bande.bottom() + 3))
        p.setBrush(dessin.c('texte'))
        p.drawPolygon(QPolygonF([QPointF(xc, bande.bottom() + 2), QPointF(xc - 6, bande.bottom() + 12),
                                 QPointF(xc + 6, bande.bottom() + 12)]))
        # l'onde, à l'échelle d'un objet de même taille
        zone = QRectF(rect.x() + 10, bande.bottom() + 30, rect.width() - 20, rect.bottom() - bande.bottom() - 40)
        r = dessin.cadre(p, zone, tr('anim_emspectrum_titre_onde'))
        nom, taille = self.objet(lam)
        # échelle : la fenêtre fait 3 longueurs d'onde ou 2 objets, la plus grande des deux
        largeur_m = max(3 * lam, 2.2 * taille)
        k = r.width() / largeur_m
        cy = r.center().y()
        amp = min(r.height() * 0.3, 60.0)
        n = 400
        rgb = lumiere.couleur_longueur_onde(lam * 1e9) if 380e-9 <= lam <= 780e-9 else None
        col = QColor(*rgb) if rgb else dessin.c(dict((d[0], d[3]) for d in DOMAINES)[lumiere.domaine_em(lam)])
        pts = []
        for i in range(n + 1):
            x = r.left() + r.width() * i / n
            pts.append(QPointF(x, cy - amp * math.sin(2 * math.pi * (x - r.left()) / (k * lam))))
        p.setPen(dessin.stylo(col, 2.2))
        p.drawPolyline(QPolygonF(pts))
        # flèche de la longueur d'onde (une période)
        x0 = r.left() + k * lam * 0.25
        y0 = cy - amp - 12
        dessin.fleche(p, x0, y0, x0 + k * lam, y0, dessin.stylo('texte', 1.2), 6)
        dessin.texte(p, x0 + k * lam / 2, y0 - 10, 'λ', 'texte')
        # l'objet de même taille
        w = k * taille
        ox = r.right() - w - 10
        p.setPen(dessin.stylo('doux', 1.2))
        p.setBrush(dessin.c('sphere', 0.6))
        p.drawEllipse(QRectF(ox, cy + amp * 0.4, w, min(w, r.height() * 0.25)))
        dessin.texte(p, ox + w / 2, cy + amp * 0.4 + min(w, r.height() * 0.25) + 12,
                     '%s (≈ %s m)' % (tr('anim_emspectrum_o_' + nom), scientifique(taille, 1)), 'doux')
