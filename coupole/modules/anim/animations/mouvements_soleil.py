"""Sun Motions Demonstrator : le Soleil sur la sphère locale.  Course diurne (parallèle de déclinaison),
culmination au méridien, changements au fil de l'année ; écliptique, mois, ombre de l'observateur, analemme.

Le temps est le temps solaire moyen du lieu (heure civile sans fuseau ni heure d'été) ; la position du Soleil vient
de astro.soleil (Meeus, 0,01°), le ciel tourne avec le temps sidéral local."""
from __future__ import annotations

import math

import numpy as np

from ....core.i18n import tr
from .. import astro, dessin, scenes
from ..base import Animation, angle, date_du_jour, duree_hm, heures_minutes, nombre

ANNEE = 2026
JOURS_MOIS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def etat_soleil(jour: float, lat: float, annee: int = ANNEE) -> dict:
    """Pour le « jour » (0 = 1er janvier 0 h, fraction = temps solaire moyen local) : position du Soleil,
    temps sidéral local, angle horaire, azimut, hauteur, lever/coucher (h₀ = −0,833°), durée du jour."""
    jj = astro.jj_jour_de_l_annee(annee, jour)
    s = astro.soleil(jj)
    tsl = astro.tsmg(jj)                                 # méridien de Greenwich : temps moyen local = TU
    h = astro.mod180(tsl - s['alpha'])
    az, alt = astro.equatorial_vers_horizon(h, s['delta'], lat)
    h0 = astro.angle_horaire_lever(s['delta'], lat, -0.833)
    midi = 12.0 - s['eqt'] / 60.0                        # midi vrai, en temps moyen
    return {'jj': jj, 'soleil': s, 'tsl': tsl, 'H': h, 'az': az, 'alt': alt, 'H0': h0, 'midi': midi,
            'lever': midi - h0 / 15.0 if 0 < h0 < 180 else None, 'coucher': midi + h0 / 15.0 if 0 < h0 < 180 else None,
            'duree': 2 * h0 / 15.0, 'culmination': astro.hauteur_culmination(s['delta'], lat)}


class MouvementsSoleil(Animation):
    ID = 'sunmotions'
    JOURS_PAR_S = 0.125                 # mode continu : 3 heures par seconde à la vitesse ×1
    PAS_JOURS_PAR_S = 15.0              # mode jour par jour

    def construire(self):
        self.vue3d = self.vue(215.0, 35.0, 5.0, 89.0)
        self.lat = self.curseur('latitude', -90.0, 90.0, 40.8, dec=1, unite='°', cle_texte='anim_c_latitude')
        self.jour = self.curseur('jour', 0.0, 364.0, 146.0, dec=0, cle_texte='anim_c_jour')
        self.heure = self.curseur('heure', 0.0, 24.0, 12.0, dec=2, unite='h', cle_texte='anim_c_heure')
        self.mode = self.choix('mode', [('anim_sunmotions_continu', 'continu'), ('anim_sunmotions_boucle', 'boucle'),
                                        ('anim_sunmotions_pas', 'pas')], 'continu')
        self.c_dec = self.coche('parallele', True)
        self.c_ecl = self.coche('ecliptique', True)
        self.c_mois = self.coche('mois', False)
        self.c_dessous = self.coche('dessous', True)
        self.c_ombre = self.coche('ombre', True)
        self.c_analemme = self.coche('analemme', False)

    def _jour(self) -> float:
        return self.jour.value() + self.heure.value() / 24.0

    def avancer(self, dt):
        mode = self.mode.currentData()
        if mode == 'pas':
            self.jour.setValue((self.jour.value() + dt * self.PAS_JOURS_PAR_S) % 365.0)
            return
        h = self.heure.value() + dt * self.JOURS_PAR_S * 24.0
        if mode == 'boucle':
            self.heure.setValue(h % 24.0)
            return
        if h >= 24.0:
            self.jour.setValue((self.jour.value() + int(h // 24.0)) % 365.0)
            h %= 24.0
        self.heure.setValue(h)

    def valeurs(self):
        e = etat_soleil(self._jour(), self.lat.value())
        s = e['soleil']
        out = [(tr('anim_c_date'), date_du_jour(self.jour.value()) + ', ' + heures_minutes(self.heure.value())),
               (tr('anim_sunmotions_heure_vraie'), heures_minutes(self.heure.value() + s['eqt'] / 60.0)),
               (tr('anim_c_hauteur'), angle(e['alt'])), (tr('anim_c_azimut'), angle(e['az'])),
               (tr('anim_c_ra'), heures_minutes(s['alpha'] / 15.0)), (tr('anim_c_dec'), angle(s['delta'])),
               (tr('anim_siderealtimeandhourangledemo_h'), angle(e['H'])),
               (tr('anim_c_tsl'), heures_minutes(e['tsl'] / 15.0)),
               (tr('anim_sunmotions_eqt'), '%s min' % nombre(s['eqt'], 1)),
               (tr('anim_sunmotions_culmination'), angle(e['culmination']) + ' (' + heures_minutes(e['midi']) + ')')]
        if e['lever'] is not None:
            az_l = astro.azimut_lever(s['delta'], self.lat.value(), -0.833)
            out.append((tr('anim_sunmotions_lever_coucher'), '%s / %s' % (heures_minutes(e['lever']),
                                                                          heures_minutes(e['coucher']))))
            out.append((tr('anim_sunmotions_az_lever'), '%s / %s' % (angle(az_l), angle(360 - az_l))))
            out.append((tr('anim_sunmotions_duree'), duree_hm(e['duree'])))
        else:
            out.append((tr('anim_sunmotions_duree'), tr('anim_sunmotions_jour_polaire' if e['H0'] >= 180
                                                        else 'anim_sunmotions_nuit_polaire')))
        return out

    def dessiner(self, p, rect):
        r = min(rect.width(), rect.height()) * 0.40
        cx, cy = rect.center().x(), rect.center().y() + 6
        self.zone_rotative(rect, self.vue3d)
        lat = self.lat.value()
        e = etat_soleil(self._jour(), lat)
        s = e['soleil']
        m = np.array(astro.matrice_equatorial_vers_horizon(e['tsl'], lat))
        eps = astro.obliquite_moyenne(e['jj'])
        soleil = m @ np.array(astro.vecteur_equatorial(s['alpha'], s['delta']))
        jour_ciel = max(0.0, min(1.0, (e['alt'] + 6) / 16))           # crépuscule civil → plein jour

        def eq(pts):
            return np.asarray(pts, dtype=float).reshape(-1, 3) @ m.T

        def scene(pe):
            if pe.passe == 'dessous' and not self.c_dessous.isChecked():
                return
            pe.courbe(dessin.cercle((0, 1, 0)), 'grille', 1.0, 0.5, repere_monde=True)
            pe.courbe(dessin.cercle((1, 0, 0)), 'grille', 1.0, 0.5, repere_monde=True)
            pe.courbe(eq(dessin.cercle((0, 0, 1))), 'equateur', 1.6, 0.8)
            pe.courbe(eq(scenes.cercle_horaire(0.0)), 'equateur', 1.6, 0.8)
            if self.c_ecl.isChecked():
                pe.courbe(eq(scenes.ecliptique(eps)), 'ecliptique', 1.6, 0.8)
            if self.c_dec.isChecked():
                pe.courbe(eq(scenes.cercle_declinaison(s['delta'])), 'soleil', 1.8, 0.8)
            if self.c_analemme.isChecked():
                pts = []
                for d in range(0, 365, 3):
                    ee = etat_soleil(d + self.heure.value() / 24.0, lat)
                    pts.append(astro.vecteur_horizon(ee['az'], ee['alt']))
                pe.courbe(np.array(pts), 'accent1', 1.6, ferme=True)
            pe.segment(eq((0, 0, 1)), eq((0, 0, 1.2)), 'equateur', 2.0)
            pe.segment(eq((0, 0, -1)), eq((0, 0, -1.2)), 'equateur', 2.0)
            pe.point(soleil, 'soleil', 9.0)

        pe = dessin.Peintre3D(p, self.vue3d, cx, cy, r)
        ciel = dessin.c('ciel')
        nuit = dessin.c('nuit')
        mel = ciel if jour_ciel >= 1 else nuit if jour_ciel <= 0 else \
            dessin.QColor(int(nuit.red() + (ciel.red() - nuit.red()) * jour_ciel),
                          int(nuit.green() + (ciel.green() - nuit.green()) * jour_ciel),
                          int(nuit.blue() + (ciel.blue() - nuit.blue()) * jour_ciel))
        p.setPen(dessin.stylo('grille', 1.2))
        mel.setAlphaF(0.45)
        p.setBrush(mel)
        p.drawEllipse(dessin.QPointF(cx, cy), r, r)

        def plan():
            pe.plan('sol', 0.6)
            if self.c_ombre.isChecked() and e['alt'] > 0.5:
                # ombre de l'observateur (longueur = taille / tan h, à l'opposé du Soleil)
                long = min(0.9, 0.12 / math.tan(math.radians(e['alt'])))
                d = -np.array(astro.vecteur_horizon(e['az'], 0.0)) * long
                pe.segment((0, 0, 0), d, 'ombre', 4.0, 0.45, repere_monde=True)

        dessin.scene_en_deux_passes(pe, scene, plan)
        scenes.points_cardinaux(pe)
        scenes.personnage(pe)
        if self.c_mois.isChecked():
            for i, j in enumerate(JOURS_MOIS):
                ss = astro.soleil_jour(ANNEE, j + 14.0)
                v = m @ np.array(astro.vecteur_equatorial(ss['alpha'], ss['delta'])) * 1.08
                if v[2] > -0.02 or self.c_dessous.isChecked():
                    pe.etiquette(v, tr('anim_mois_court_%d' % (i + 1)), 'ecliptique')
        pe.etiquette(soleil * 1.15, heures_minutes(self.heure.value()), 'soleil')
