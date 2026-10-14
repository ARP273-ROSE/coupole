"""Lunar Phase Vocabulary : la Lune à chacune des phases nommées.  Un bouton par phase, ou l'animation de la
lunaison entière (durée à l'écran réglable, 29,53 s par défaut comme l'original : une seconde = un jour) ; le
compteur donne les jours écoulés.  Noms de phase avec les tolérances de l'original (±12° autour des nouvelle et
pleine lunes, ±5° autour des quartiers)."""
from __future__ import annotations

from ....core.i18n import tr
from .. import astro, dessin
from ..base import Animation, angle, nombre
from .phases_lune import ANGLES_PHASES, PHASES


class VocabulairePhases(Animation):
    ID = 'lunar_phaser'

    def construire(self):
        self.periode = self.curseur('periode', 5.0, 60.0, astro.MOIS_SYNODIQUE_J, dec=2, unite='s')
        self.phase = self.curseur('phase', 0.0, 360.0, 180.0, dec=1, unite='°', cle_texte='anim_lunar_applet_phase')
        for cle in PHASES:
            self.bouton('anim_lunar_phaser_b_' + cle, lambda _=False, k=cle: self.aller(k))
        self.c_bande = self.coche('bande', True)
        self.jours = 0.0

    def aller(self, cle: str):
        self.phase.setValue(ANGLES_PHASES[cle])
        self.jours = 0.0
        self.rafraichir()

    def etat_initial(self):
        self.jours = 0.0

    def avancer(self, dt):
        # une lunaison (29,53 jours) dure `periode` secondes à l'écran
        dj = dt * astro.MOIS_SYNODIQUE_J / self.periode.value()
        self.jours += dj
        self.phase.setValue((self.phase.value() + 360.0 * dj / astro.MOIS_SYNODIQUE_J) % 360.0)

    def valeurs(self):
        ph = self.phase.value()
        return [(tr('anim_lunar_applet_nom_phase'), tr('anim_phase_' + astro.nom_de_phase(ph))),
                (tr('anim_lunar_applet_phase'), angle(ph)),
                (tr('anim_lunar_applet_eclairee'), '%s %%' % nombre(100 * astro.fraction_eclairee(ph), 1)),
                (tr('anim_lunar_phaser_age'), '%s %s' % (nombre(astro.MOIS_SYNODIQUE_J * ph / 360.0, 1),
                                                          tr('anim_u_jours'))),
                (tr('anim_lunar_phaser_ecoules'), '%s %s' % (nombre(self.jours, 1), tr('anim_u_jours')))]

    def dessiner(self, p, rect):
        ph = self.phase.value()
        bande = self.c_bande.isChecked()
        haut = rect.height() * ((0.74 if rect.width() >= 640 else 0.56) if bande else 1.0)
        r = min(rect.width(), haut) * 0.36
        cx, cy = rect.center().x(), rect.y() + haut * 0.47
        dessin.phase_lune(p, cx, cy, r, ph)
        dessin.police(p, 1.3, gras=True)
        dessin.texte(p, cx, cy + r + 0.07 * haut + 6, tr('anim_phase_' + astro.nom_de_phase(ph)))
        dessin.police(p, 1 / 1.3)
        if not bande:
            return
        lignes = 1 if rect.width() >= 640 else 2                  # deux rangées de quatre si la place manque
        par_ligne = len(PHASES) // lignes
        h_ligne = (rect.height() - haut) / lignes
        pas = rect.width() / par_ligne
        rr = min(pas * 0.33, h_ligne * 0.30)
        courant = astro.nom_de_phase(ph)
        dessin.police(p, 0.8)
        for k, cle in enumerate(PHASES):
            x = rect.x() + pas * (k % par_ligne + 0.5)
            y = rect.y() + haut + h_ligne * (k // par_ligne + 0.42)
            if cle == courant:
                p.setPen(dessin.stylo('accent1', 2.0))
                p.setBrush(dessin.Qt.BrushStyle.NoBrush)
                p.drawEllipse(dessin.QPointF(x, y), rr + 5, rr + 5)
            dessin.phase_lune(p, x, y, rr, ANGLES_PHASES[cle])
            dessin.texte(p, x, y + rr + 14, tr('anim_phase_' + cle), 'texte' if cle == courant else 'doux')
        dessin.police(p, 1 / 0.8)
