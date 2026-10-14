"""Lunar Phase Quizzer : la vue habituelle de l'orbite lunaire (vue de dessus), en cachant au choix l'aspect de la
Lune, sa position sur l'orbite ou la direction du Soleil.  On répond (curseur de phase, ou en faisant glisser la
Lune ou la lumière du Soleil) puis on affiche la réponse ; Coupole dit en plus si la réponse donne la même phase
nommée (tolérances de l'original : ±12° autour des nouvelle et pleine lunes, ±5° autour des quartiers)."""
from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle

MODES = ('apparence', 'lune', 'soleil')


def elongation(angle_lune: float, angle_soleil: float) -> float:
    """Élongation (phase) de la Lune : angle, vu de la Terre, de la direction du Soleil à celle de la Lune, compté
    dans le sens du mouvement de la Lune (sens trigonométrique vu du nord)."""
    return (angle_lune - angle_soleil) % 360.0


def meme_phase(e1: float, e2: float) -> bool:
    return astro.nom_de_phase(e1) == astro.nom_de_phase(e2)


class QuestionnairePhases(Animation):
    ID = 'lunarphasequizzer'
    ANIMEE = False

    def construire(self):
        self.mode = self.choix('mode', [('anim_lunarphasequizzer_m_' + m, m) for m in MODES], 'apparence')
        self.reponse = self.curseur('reponse', 0.0, 360.0, 180.0, dec=0, unite='°')
        self.bouton('anim_lunarphasequizzer_nouvelle', self.nouvelle_question)
        self.b_reponse = self.bouton('anim_lunarphasequizzer_montrer', self.basculer_reponse)
        self._hasard = random.Random()
        self._schema = None
        self.etat_initial()

    def etat_initial(self):
        self.lune, self.soleil = 45.0, 0.0              # comme l'original : Lune à 45°, lumière venant de la droite
        self.devine = {'lune': 135.0, 'soleil': 180.0}
        self.montree = False
        if hasattr(self, 'b_reponse'):
            self.b_reponse.setText(tr('anim_lunarphasequizzer_montrer'))

    def nouvelle_question(self):
        self.lune = self._hasard.choice(range(0, 360, 15)) * 1.0
        self.soleil = self._hasard.choice(range(0, 360, 15)) * 1.0
        self.devine = {'lune': (self.lune + 120.0) % 360.0, 'soleil': (self.soleil + 120.0) % 360.0}
        self.montree = False
        self.b_reponse.setText(tr('anim_lunarphasequizzer_montrer'))
        self.rafraichir()

    def basculer_reponse(self):
        self.montree = not self.montree
        self.b_reponse.setText(tr('anim_lunarphasequizzer_cacher' if self.montree else 'anim_lunarphasequizzer_montrer'))
        self.rafraichir()

    def reponse_donnee(self) -> float:
        """Élongation correspondant à la réponse de l'utilisateur, selon la question posée."""
        m = self.mode.currentData()
        if m == 'apparence':
            return self.reponse.value()
        if m == 'lune':
            return elongation(self.devine['lune'], self.soleil)
        return elongation(self.lune, self.devine['soleil'])

    def valeurs(self):
        vraie = elongation(self.lune, self.soleil)
        out = [(tr('anim_lunarphasequizzer_question'), tr('anim_lunarphasequizzer_m_' + self.mode.currentData())),
               (tr('anim_lunarphasequizzer_votre'), tr('anim_phase_' + astro.nom_de_phase(self.reponse_donnee())))]
        if self.montree:
            ok = meme_phase(vraie, self.reponse_donnee())
            out += [(tr('anim_lunarphasequizzer_vraie'), '%s (%s)' % (tr('anim_phase_' + astro.nom_de_phase(vraie)),
                                                                      angle(vraie, 0))),
                    (tr('anim_lunarphasequizzer_verdict'), tr('anim_lunarphasequizzer_juste' if ok
                                                             else 'anim_lunarphasequizzer_faux'))]
        return out

    # ------------------------------------------------------------ souris
    def presser(self, pos, bouton):
        if self._schema is None or not self._schema[0].contains(pos):
            return super().presser(pos, bouton)
        m = self.mode.currentData()
        if m in ('lune', 'soleil') and not self.montree:
            self._glisse = lambda q, m=m: self._tirer(m, q)
            self._tirer(m, pos)
            return True
        return False

    def _tirer(self, m, pos):
        _, cx, cy, _ = self._schema
        self.devine[m] = math.degrees(math.atan2(cy - pos.y(), pos.x() - cx)) % 360.0

    # ------------------------------------------------------------ dessin
    def dessiner(self, p, rect):
        z = dessin.zones_principale(rect, 1, 0.62) if rect.width() > rect.height() * 1.1 else dessin.zones(rect, 2, 10)
        m = self.mode.currentData()
        self._orbite(p, dessin.cadre(p, z[0], tr('anim_lunarphasequizzer_schema')), m)
        r = dessin.cadre(p, z[1], tr('anim_lunarphasequizzer_aspect'))
        rr = min(r.width(), r.height()) * 0.34
        cx, cy = r.center().x(), r.center().y() - 6
        if m == 'apparence' and not self.montree:
            dessin.phase_lune(p, cx, cy, rr, self.reponse.value(), 'lune', 'nuit')
            dessin.texte(p, cx, cy + rr + 14, tr('anim_lunarphasequizzer_votre_reponse'), 'accent2')
        else:
            dessin.phase_lune(p, cx, cy, rr, elongation(self.lune, self.soleil))
        if self.montree:
            ok = meme_phase(elongation(self.lune, self.soleil), self.reponse_donnee())
            dessin.police(p, 1.2, gras=True)
            dessin.texte(p, cx, r.bottom() - 14, tr('anim_lunarphasequizzer_juste' if ok else 'anim_lunarphasequizzer_faux'),
                         'horizon' if ok else 'accent3')
            dessin.police(p, 1 / 1.2)

    def _orbite(self, p, r, m):
        cx, cy = r.center().x(), r.center().y()
        ro = min(r.width(), r.height()) * 0.36
        self._schema = (QRectF(r), cx, cy, ro)
        cache_soleil = m == 'soleil' and not self.montree
        cache_lune = m == 'lune' and not self.montree
        # lumière du Soleil : flèches parallèles venant de la direction du Soleil
        for sigma, cle, alpha in ((self.soleil, 'soleil', 0.8), (self.devine['soleil'], 'accent2', 0.8)):
            if (cle == 'soleil' and cache_soleil) or (cle == 'accent2' and m != 'soleil'):
                continue
            s = math.radians(sigma)
            ux, uy = math.cos(s), -math.sin(s)
            nx, ny = -uy, ux
            for k in (-0.6, -0.3, 0.0, 0.3, 0.6):
                x0, y0 = cx + ux * ro * 1.35 + nx * k * ro, cy + uy * ro * 1.35 + ny * k * ro
                dessin.fleche(p, x0, y0, x0 - ux * ro * 0.3, y0 - uy * ro * 0.3, dessin.stylo(cle, 1.3, alpha), 6)
        p.setPen(dessin.stylo('grille', 1.0))
        p.setBrush(dessin.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), ro, ro)
        rt = ro * 0.18
        dessin.disque(p, cx, cy, rt, 'terre')
        rl = max(6.0, rt * 0.5)
        for mu, cle in ((self.lune, 'lune'), (self.devine['lune'], 'accent2')):
            if (cle == 'lune' and cache_lune) or (cle == 'accent2' and m != 'lune'):
                continue
            a = math.radians(mu)
            mx, my = cx + ro * math.cos(a), cy - ro * math.sin(a)
            dessin.disque(p, mx, my, rl, 'nuit' if not cache_soleil else 'doux')
            if not cache_soleil:
                p.setPen(dessin.Qt.PenStyle.NoPen)
                p.setBrush(dessin.c(cle))
                p.drawPie(QRectF(mx - rl, my - rl, 2 * rl, 2 * rl), int((self.soleil - 90) * 16), 180 * 16)
        if not cache_soleil:
            p.setPen(dessin.Qt.PenStyle.NoPen)
            p.setBrush(dessin.c('nuit', 0.7))
            p.drawPie(QRectF(cx - rt, cy - rt, 2 * rt, 2 * rt), int((self.soleil + 90) * 16), 180 * 16)
        if m in ('lune', 'soleil') and not self.montree:
            dessin.texte(p, r.x() + 8, r.bottom() - 10, tr('anim_lunarphasequizzer_glisser_' + m), 'accent2',
                         centre=False)
