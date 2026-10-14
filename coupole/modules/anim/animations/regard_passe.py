"""Lookback Time Simulator : la lumière met du temps à nous parvenir ; regarder loin, c'est regarder dans le passé.
Une étoile à d années-lumière explose l'année T : on ne voit l'explosion que l'année T + d.  Années historiques sans
année zéro (1 av. J.-C. précède 1 apr. J.-C.), comme l'original (frise de 8000 av. J.-C. à 10 000).  Exemples réels :
la supernova de 1054 (nébuleuse du Crabe, ≈ 6 500 années-lumière, Trimble 1973) et SN 1006 (≈ 7 100 années-lumière,
Winkler et al. 2003) : elles avaient explosé des millénaires avant d'être vues."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF

from ....core.i18n import tr
from .. import dessin
from ..base import Animation, nombre

AN_MIN, AN_MAX = -7999, 10000            # années astronomiques (0 = 1 av. J.-C.)
EXEMPLES = {'crabe': (1054, 6500.0), 'sn1006': (1006, 7100.0)}


def annee_texte(a: float) -> str:
    """Année astronomique → « 1054 apr. J.-C. » / « 5447 av. J.-C. » (pas d'année zéro)."""
    a = int(round(a))
    if a > 0:
        return tr('anim_lookbacktimesim_ap', a=a)
    return tr('anim_lookbacktimesim_av', a=1 - a)


def annee_observee(annee_explosion: float, distance_al: float) -> float:
    """La lumière parcourt une année-lumière par an (années juliennes, comme la définition de l'année-lumière)."""
    return annee_explosion + distance_al


class RegardPasse(Animation):
    ID = 'lookbacktimesim'

    def construire(self):
        self.exemple = self.choix('exemple', [('anim_lookbacktimesim_libre', 'libre'),
                                              ('anim_lookbacktimesim_crabe', 'crabe'),
                                              ('anim_lookbacktimesim_sn1006', 'sn1006')], 'libre')
        self.exemple.activated.connect(self._exemple)
        self.distance = self.curseur('distance', 100.0, 9000.0, 3000.0, dec=0, unite=tr('anim_spectroparallax_al'))
        self.explosion = self.curseur('explosion', AN_MIN, 9000.0, 1200.0, dec=0)
        self.vitesse_ans = self.curseur('vitesse_ans', 50.0, 3000.0, 600.0, dec=0, unite='a·s⁻¹',
                                        log=True)
        self.etat_initial()

    def _exemple(self, *_):
        k = self.exemple.currentData()
        if k in EXEMPLES:
            vu, d = EXEMPLES[k]
            self.distance.setValue(d)
            self.explosion.setValue(vu - d)
            self.etat_initial()
            self.rafraichir()

    def etat_initial(self):
        self.annee = self.explosion.value() - 500.0

    def reglage_change(self):
        cle = (self.distance.value(), self.explosion.value())
        if getattr(self, '_cle', cle) != cle:           # nouvelle étoile : on revient avant l'explosion
            self.etat_initial()
        self._cle = cle
        super().reglage_change()

    def avancer(self, dt):
        self.annee += dt * self.vitesse_ans.value()
        if self.annee >= AN_MAX:
            self.annee = AN_MAX
            self.arreter()

    def valeurs(self):
        t_sn, d = self.explosion.value(), self.distance.value()
        vu = annee_observee(t_sn, d)
        return [(tr('anim_lookbacktimesim_maintenant'), annee_texte(self.annee)),
                (tr('anim_lookbacktimesim_explose'), annee_texte(t_sn)),
                (tr('anim_lookbacktimesim_vue'), annee_texte(vu)),
                (tr('anim_lookbacktimesim_ce_qu_il_voit'),
                 tr('anim_lookbacktimesim_voit_sn') if self.annee >= vu else tr('anim_lookbacktimesim_voit_etoile'))]

    def dessiner(self, p, rect):
        t_sn, d = self.explosion.value(), self.distance.value()
        haut = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.62)
        r = dessin.cadre(p, haut, tr('anim_lookbacktimesim_titre_scene'))
        x_etoile = r.left() + 40
        x_obs = r.right() - 50
        k = (x_obs - x_etoile) / max(d, 1.0)
        cy = r.center().y() + 10
        explose = self.annee >= t_sn
        if explose:
            rr = (self.annee - t_sn) * k
            p.save()
            p.setClipRect(r)
            p.setPen(dessin.stylo('accent1', 2.0, 0.8))
            p.setBrush(dessin.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(x_etoile, cy), rr, rr)
            p.restore()
            dessin.disque(p, x_etoile, cy, 14, 'accent3', alpha=0.5)
            dessin.disque(p, x_etoile, cy, 6, 'accent1')
        else:
            dessin.disque(p, x_etoile, cy, 8, 'soleil')
        dessin.texte(p, x_etoile, cy + 26, tr('anim_c_etoile'), 'doux')
        dessin.disque(p, x_obs, cy, 9, 'accent2', bord='texte')
        dessin.texte(p, x_obs, cy + 26, tr('anim_c_observateur'), 'doux')
        # ce que voit l'observateur
        vu = self.annee >= annee_observee(t_sn, d)
        bx, by = x_obs - 20, r.top() + 34
        p.setPen(dessin.stylo('doux', 1.0))
        p.setBrush(dessin.c('sphere', 0.6))
        p.drawEllipse(QPointF(bx, by), 30, 22)
        if vu:
            dessin.disque(p, bx, by, 9, 'accent3', alpha=0.6)
            dessin.disque(p, bx, by, 4, 'accent1')
        else:
            dessin.disque(p, bx, by, 4, 'soleil')
        dessin.texte(p, (x_etoile + x_obs) / 2, cy - 14, '%s %s' % (nombre(d, 0), tr('anim_spectroparallax_al')), 'doux')
        # frise
        r2 = dessin.cadre(p, QRectF(rect.x(), haut.bottom(), rect.width(), rect.height() - haut.height()),
                          tr('anim_lookbacktimesim_titre_frise'))
        y = r2.center().y()
        x_de = lambda a: r2.left() + 10 + (r2.width() - 20) * (a - AN_MIN) / (AN_MAX - AN_MIN)
        p.setPen(dessin.stylo('doux', 2.0))
        p.drawLine(QPointF(x_de(AN_MIN), y), QPointF(x_de(AN_MAX), y))
        dessin.police(p, 0.8)
        pas = 2000 if r2.width() >= 700 else (4000 if r2.width() >= 420 else 6000)
        for a in range(-8000, 10001, pas):
            aa = a if a > 0 else (a + 1 if a < 0 else 1)
            p.drawLine(QPointF(x_de(aa), y - 4), QPointF(x_de(aa), y + 4))
            dessin.texte(p, x_de(aa), y + 15, annee_texte(aa), 'doux')
        dessin.police(p, 1 / 0.8)
        for a, cle, nom in ((t_sn, 'accent3', 'anim_lookbacktimesim_m_explosion'),
                            (annee_observee(t_sn, d), 'accent1', 'anim_lookbacktimesim_m_vue')):
            if AN_MIN <= a <= AN_MAX:
                dessin.disque(p, x_de(a), y, 5, cle)
                dessin.texte(p, x_de(a), y - 14, tr(nom), cle, fond=True)
        xc = x_de(max(AN_MIN, min(AN_MAX, self.annee)))
        p.setPen(dessin.stylo('texte', 2.0))
        p.drawLine(QPointF(xc, y - 22), QPointF(xc, y + 6))
