"""Panneau de l'outil « Parallaxe (Lune, ISS) » : paires simultanées, visées A et B, calcul, rapport.

Les mesures sur les images (centre de la Lune, position de l'ISS) et les calculs tournent hors du fil graphique.
"""
from __future__ import annotations

import datetime as D
import html
import math
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QPlainTextEdit, QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout,
                             QWidget)

from .....core.i18n import decimal as _dec
from .....core.i18n import tr
from .....gui import fichiers, memoire, ouvrir
from .....gui.adaptatif import Flux, defilable
from .....gui.modele import ModeleTableau, equiper_entete, vue_tableau
from .....gui.outils import Tache, aide, bouton, bouton_principal, champ, decimal, liste
from ... import astro
from . import calcul as C
from . import paires as P

UTC = D.timezone.utc


def _flottant(t: str):
    from ...mesures import angle
    t = (t or '').strip()
    if not t:
        return None
    return angle(t).valeur


def _instant(t: str):
    from ...mesures import instant
    t = (t or '').strip()
    if not t:
        return None
    return instant(t if any(x in t.upper() for x in ('UTC', ' TU', 'Z')) else t + ' UTC').valeur


class EditeurVisee(QGroupBox):
    """Ce qu'un observateur a mesuré : lieu, points datés (α, δ ou h, az), incertitudes."""

    def __init__(self, lettre: str, parent=None):
        super().__init__(tr('pc_visee', l=lettre), parent)
        self.lettre = lettre
        v = QVBoxLayout(self)
        f = QFormLayout()
        self.e_nom = champ('pc_nom_aide')
        self.e_lat = champ('pc_lat_aide', '', 'pc_lat_indice')
        self.e_lon = champ('pc_lon_aide', '', 'pc_lon_indice')
        self.e_alt = champ('pc_alt_aide', '0')
        f.addRow(tr('pc_nom'), self.e_nom)
        f.addRow(tr('pc_lat'), self.e_lat)
        f.addRow(tr('pc_lon'), self.e_lon)
        f.addRow(tr('pc_alt'), self.e_alt)
        self.c_mode = liste('pc_mode_aide', [(tr('pc_mode_radec'), 'radec'), (tr('pc_mode_altaz_mesuree'), 'mesuree'),
                                             (tr('pc_mode_altaz_vraie'), 'vraie')])
        self.c_mode.currentIndexChanged.connect(lambda *_: self._entetes())
        f.addRow(tr('pc_mode'), self.c_mode)
        v.addLayout(f)
        self.t_points = aide(QTableWidget(0, 3), 'pc_points_aide')
        equiper_entete(self.t_points)
        self.t_points.horizontalHeader().setStretchLastSection(True)
        self.t_points.setMinimumHeight(110)
        self._entetes()
        v.addWidget(self.t_points, 1)
        h = Flux()
        h.addWidget(bouton('pc_point_ajouter', lambda: self.ajouter_point()))
        h.addWidget(bouton('pc_point_retirer', self.retirer_point))
        h.addWidget(bouton('pc_point_inverser', self.inverser))
        v.addLayout(h)
        f2 = QFormLayout()
        self.s_sigma = decimal('pc_sigma_aide', 0.1, 36000.0, 30.0, 'pc_unite_arcsec')
        self.s_sigma_t = decimal('pc_sigma_t_aide', 0.0, 3600.0, 0.5, 'pc_unite_s')
        self.s_sigma_pos = decimal('pc_sigma_pos_aide', 0.0, 100000.0, 30.0, 'pc_unite_m')
        self.s_horloge = decimal('pc_horloge_aide', -3600.0, 3600.0, 0.0, 'pc_unite_s')
        self.s_horloge.setDecimals(2)
        f2.addRow(tr('pc_sigma'), self.s_sigma)
        f2.addRow(tr('pc_sigma_t'), self.s_sigma_t)
        f2.addRow(tr('pc_sigma_pos'), self.s_sigma_pos)
        f2.addRow(tr('pc_horloge'), self.s_horloge)
        v.addLayout(f2)
        self.l_source = QLabel('')
        self.l_source.setWordWrap(True)
        v.addWidget(self.l_source)

    def _entetes(self):
        m = self.c_mode.currentData()
        t = [tr('pc_col_instant'), tr('pc_col_ra') if m == 'radec' else tr('pc_col_h'),
             tr('pc_col_dec') if m == 'radec' else tr('pc_col_az')]
        self.t_points.setHorizontalHeaderLabels(t)

    def ajouter_point(self, instant: D.datetime | None = None, a=None, b=None):
        r = self.t_points.rowCount()
        self.t_points.insertRow(r)
        vals = ['' if instant is None else instant.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                '' if a is None else '%.6f' % a, '' if b is None else '%.6f' % b]
        for k, x in enumerate(vals):
            self.t_points.setItem(r, k, QTableWidgetItem(x))

    def retirer_point(self):
        r = self.t_points.currentRow()
        if r >= 0:
            self.t_points.removeRow(r)

    def inverser(self):
        """Inverse l'ordre des instants (extrémités d'un trait dont le sens était supposé à tort)."""
        n = self.t_points.rowCount()
        dates = [self.t_points.item(r, 0).text() if self.t_points.item(r, 0) else '' for r in range(n)]
        for r, d in enumerate(reversed(dates)):
            self.t_points.setItem(r, 0, QTableWidgetItem(d))

    def vider(self):
        self.t_points.setRowCount(0)

    def remplir_lieu(self, nom='', lat=None, lon=None, alt=None, source=''):
        if nom and not self.e_nom.text().strip():
            self.e_nom.setText(nom)
        if lat is not None:
            self.e_lat.setText(('%.6f' % lat).rstrip('0').rstrip('.'))
        if lon is not None:
            self.e_lon.setText(('%.6f' % lon).rstrip('0').rstrip('.'))
        if alt is not None:
            self.e_alt.setText('%.0f' % alt)
        if source:
            self.l_source.setText(source)

    def visee(self) -> C.Visee:
        lat, lon = _flottant(self.e_lat.text()), _flottant(self.e_lon.text())
        if lat is None or lon is None:
            raise C.ErreurCalcul('pc_err_lieu', nom=self.lettre)
        try:
            alt = float((self.e_alt.text() or '0').replace(',', '.'))
        except ValueError:
            alt = 0.0
        mode = self.c_mode.currentData()
        pts = []
        for r in range(self.t_points.rowCount()):
            cel = [self.t_points.item(r, k).text() if self.t_points.item(r, k) else '' for k in range(3)]
            t = _instant(cel[0])
            if t is None:
                continue
            a = _flottant(cel[1]) if mode != 'radec' else _ra(cel[1])
            b = _flottant(cel[2])
            if a is None or b is None:
                continue
            pts.append(C.Point(t, a, b) if mode == 'radec' else C.Point(t, None, None, a, b))
        if not pts:
            raise C.ErreurCalcul('pc_err_point_vide', nom=self.lettre)
        return C.Visee(self.e_nom.text().strip() or self.lettre, lat, lon, alt, pts,
                       'mesuree' if mode == 'mesuree' else 'sans', self.s_sigma.value(), self.s_sigma_t.value(),
                       self.s_sigma_pos.value(), self.s_horloge.value())


def _ra(t: str):
    """α en degrés, ou en heures si écrit « 0h41m50s » / « 00:41:50 »."""
    from ...mesures import angle
    t = (t or '').strip()
    if not t:
        return None
    heures = 'h' in t.lower() or t.count(':') >= 2
    return angle(t, heures=heures).valeur


class PanneauParallaxe(QWidget):
    def __init__(self, contexte, parent=None):
        super().__init__(parent)
        self.contexte = contexte
        self.paires: list = []
        self.resultat = None
        self.a_calcule = False
        self._taches = []
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        intro = QLabel(tr('pc_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        f = Flux()
        f.addWidget(QLabel(tr('pc_seuil_iss')))
        self.s_iss = decimal('pc_seuil_iss_aide', 0.1, 600.0, P.SEUILS_S['iss'], 'pc_unite_s')
        f.addWidget(self.s_iss)
        f.addWidget(QLabel(tr('pc_seuil_lune')))
        self.s_lune = decimal('pc_seuil_lune_aide', 1.0, 3600.0, P.SEUILS_S['lune'], 'pc_unite_s')
        f.addWidget(self.s_lune)
        f.addWidget(QLabel(tr('pc_base_min')))
        self.s_base = decimal('pc_base_min_aide', 0.0, 20000.0, P.BASE_MIN_KM, 'pc_unite_km')
        f.addWidget(self.s_base)
        f.addWidget(bouton('pc_chercher', self.chercher_paires))
        f.addWidget(bouton('pc_lire_entetes', self.lire_entetes))
        v.addLayout(f)
        sp = QSplitter(Qt.Orientation.Vertical)
        self.modele = ModeleTableau([tr('pc_p_' + c) for c in ('cible', 'a', 'b', 'ecart', 'base', 'source',
                                                                'remarques')])
        self.vue, self.proxy = vue_tableau(self.modele, 'pc_paires_aide', selection_multiple=False)
        self.vue.message_vide = lambda: tr('pc_paires_vide')
        self.vue.doubleClicked.connect(lambda *_: self.prendre_paire())
        self.vue.selectionModel().selectionChanged.connect(lambda *_: self.prendre_paire())
        sp.addWidget(self.vue)
        bas = QWidget()
        vb = QVBoxLayout(bas)
        vb.setContentsMargins(0, 0, 0, 0)
        f = Flux()
        f.addWidget(QLabel(tr('pc_cible')))
        self.c_cible = liste('pc_cible_aide', [(tr('pt_cible_lune'), 'lune'), (tr('pt_cible_iss'), 'iss')])
        f.addWidget(self.c_cible)
        f.addWidget(QLabel(tr('pc_methode')))
        self.c_methode = liste('pc_methode_aide', [(tr('pc_m_deux'), 'deux'), (tr('pc_m_diurne'), 'diurne'),
                                                   (tr('pc_m_vitesse'), 'vitesse'), (tr('pc_m_orbite'), 'orbite')])
        f.addWidget(self.c_methode)
        self.l_eph = aide(QLabel(''), 'pc_eph_aide')
        f.addWidget(self.l_eph)
        self.b_de440 = bouton('pc_de440', self.telecharger_de440)
        f.addWidget(self.b_de440)
        vb.addLayout(f)
        h = QHBoxLayout()
        self.a = EditeurVisee('A')
        self.b = EditeurVisee('B')
        h.addWidget(self.a)
        h.addWidget(self.b)
        vb.addLayout(h, 1)
        f = Flux()
        f.addWidget(QLabel(tr('pc_etoile')))
        self.e_etoile = champ('pc_etoile_aide', '', 'pc_etoile_indice')
        self.e_etoile.setMinimumWidth(180)
        f.addWidget(self.e_etoile)
        f.addWidget(QLabel(tr('pc_tle')))
        self.e_tle = aide(QPlainTextEdit(), 'pc_tle_aide')
        self.e_tle.setMaximumHeight(52)
        self.e_tle.setMinimumWidth(420)
        f.addWidget(self.e_tle)
        f.addWidget(bouton('pc_tle_charger', self.charger_tle))
        vb.addLayout(f)
        f = Flux()
        self.b_calculer = bouton_principal('pc_calculer', self.calculer)
        f.addWidget(self.b_calculer)
        self.b_html = bouton('pc_rapport_html', lambda: self.rapport('html'))
        self.b_pdf = bouton('pc_rapport_pdf', lambda: self.rapport('pdf'))
        self.b_html.setEnabled(False)
        self.b_pdf.setEnabled(False)
        f.addWidget(self.b_html)
        f.addWidget(self.b_pdf)
        vb.addLayout(f)
        self.resultats = aide(QTextBrowser(), 'pc_resultats_aide')
        self.resultats.setMinimumHeight(140)
        vb.addWidget(self.resultats, 1)
        sp.addWidget(defilable(bas))
        sp.setStretchFactor(0, 1)
        sp.setStretchFactor(1, 3)
        v.addWidget(sp, 1)
        memoire.separateur(sp, 'modules.partages.parallaxe.separateur')
        self._maj_ephemeride()
        self.donnees_changees()

    # ------------------------------------------------------------------ éphéméride
    def _maj_ephemeride(self):
        src = astro.source_ephemeride()
        self.l_eph.setText(tr('pc_eph_etat_' + src))
        self.b_de440.setVisible(src != 'de440')
        self.b_de440.setEnabled(astro.jplephem_present())
        if not astro.jplephem_present():
            self.b_de440.setToolTip(tr('pc_de440_sans_jplephem'))

    def telecharger_de440(self):
        from .....core import reseau, sources
        url = sources.valeur('ephemerides.de440s')
        dest = str(astro.dossier_ephemerides() / astro.NOM_DE440)
        self.b_de440.setEnabled(False)
        self.contexte.statut(tr('pc_de440_en_cours'))
        t = Tache(reseau.telecharger, url, dest, parent=self)
        t.quand_fini(lambda r: (self._maj_ephemeride(), self.contexte.statut(tr('pc_de440_ok'))))
        t.quand_erreur(lambda e: (self.b_de440.setEnabled(True), self.contexte.statut(tr('pc_de440_echec',
                                                                                          erreur=e[:200]))))
        self._taches.append(t)
        t.start()

    def charger_tle(self):
        chemin, _ = fichiers.choisir_fichier(self, tr('pc_tle_charger'), memoire.dossier('modules.partages.tle', ''))
        if chemin:
            memoire.retenir('modules.partages.tle', chemin, est_fichier=True)
            with open(chemin, encoding='utf-8', errors='replace') as fh:
                self.e_tle.setPlainText(fh.read()[:2000])

    # ------------------------------------------------------------------ paires
    def donnees_changees(self):
        self.chercher_paires(silencieux=True)

    def observations(self) -> list:
        ctx = self.contexte
        if ctx.session is None:
            return []
        obs = []
        for t in ctx.tableaux_mesures():
            obs += P.depuis_tableau(t, ctx.appliquer_corrections)
        if ctx.session.structure is not None:
            par_tableau = {x for o in obs for x in o.fichiers}
            obs += [o for o in P.depuis_structure(ctx.session.structure, ctx.session.entetes_lieux())
                    if not any(os.path.basename(c) in par_tableau for c in o.fichiers)]
        return obs

    def chercher_paires(self, silencieux=False):
        seuils = {'iss': self.s_iss.value(), 'tiangong': self.s_iss.value(), 'lune': self.s_lune.value()}
        self.paires = P.trouver(self.observations(), seuils, self.s_base.value())
        lignes = []
        for p in self.paires:
            lignes.append((tr('pt_cible_' + p.cible), self._obs_txt(p.a), self._obs_txt(p.b), _dec(p.ecart_s, 1),
                           _dec(p.base_km, 0) if p.base_km is not None else '—',
                           '%s / %s' % (tr('pc_source_' + p.a.source), tr('pc_source_' + p.b.source)),
                           ' · '.join(tr(n) for n in p.notes)))
        self.modele.remplir(lignes, self.paires)
        if not silencieux:
            r = P.resume_synchro(self.paires)
            self.contexte.statut(tr('pc_paires_trouvees', n=r['paires'], s=r['a_la_seconde']))

    @staticmethod
    def _obs_txt(o) -> str:
        return '%s · %s' % (o.observateur or tr('pt_inconnu'), o.debut.strftime('%Y-%m-%d %H:%M:%S'))

    def prendre_paire(self):
        from .....gui.modele import lignes_choisies
        sel = lignes_choisies(self.vue, self.proxy, self.modele)
        if not sel:
            return
        p = sel[0]
        self.c_cible.setCurrentIndex(max(0, self.c_cible.findData(p.cible)))
        for ed, o in ((self.a, p.a), (self.b, p.b)):
            ed.e_nom.setText(o.observateur or '')
            ed.remplir_lieu('', o.lat, o.lon, o.alt_m, tr('pc_source_fichiers', f=', '.join(
                os.path.basename(x) for x in o.fichiers[:4])))
            ed.vider()
            ed.c_mode.setCurrentIndex(0)
            ed.ajouter_point(o.debut)
        self.contexte.statut(tr('pc_paire_prise'))

    def lire_entetes(self):
        st = self.contexte.session.structure if self.contexte.session else None
        if st is None:
            return
        fits_ = [f for f in st.fichiers if f.genre == 'fits' and f.chemin not in self.contexte.session.entetes]
        self.contexte.lire_entetes(fits_)

    # ------------------------------------------------------------------ mesure sur image
    def actions_menu(self, menu, sel):
        images = [f for f in sel if f.genre in ('fits', 'jpeg', 'png', 'tiff')]
        for lettre, ed in (('A', self.a), ('B', self.b)):
            ouvrir.action(menu, tr('pc_menu_mesurer', l=lettre, n=len(images)), bool(images),
                          tr('pc_menu_mesurer_aide')).triggered.connect(
                lambda _=False, e=ed, i=images: self.mesurer(e, i))

    def mesurer(self, ed: EditeurVisee, images: list):
        """Télécharge (cache) puis mesure : Lune → centre du disque ; ISS → objet mobile d'une série, ou trait."""
        s = self.contexte.session
        cible = self.c_cible.currentData()
        self.contexte.statut(tr('pc_mesure_en_cours', n=len(images)))

        def travail():
            from . import image as I
            locaux = [s.fichier_local(f.chemin, f.taille) for f in images]
            out = {'points': [], 'lieu': None, 'notes': []}
            imgs = [I.lire(c) for c in locaux]
            for img, f in zip(imgs, images):
                lh = I.lieu_et_heure(img.entete)
                if out['lieu'] is None and lh['lat'] is not None:
                    out['lieu'] = lh
            if cible == 'lune':
                for img, f in zip(imgs, images):
                    lh = I.lieu_et_heure(img.entete)
                    ech = I.echelle_arcsec(img)
                    r_att = (math.degrees(math.asin(astro.R_LUNE_KM / 384400.0)) * 3600 / ech
                             if ech == ech else None)
                    c = I.centre_lune(img.donnees, r_att)
                    ra, dec = I.pixel_vers_radec(img, c['x'], c['y'])
                    t = lh['milieu'] or f.instant
                    out['points'].append((t, ra, dec))
                    out['notes'].append(tr('pc_note_lune', nom=f.nom, x=_dec(c['x'], 1), y=_dec(c['y'], 1),
                                           r=_dec(c['r'], 1), s=_dec(c['sigma_px'] * ech, 1)))
                    out['sigma'] = max(out.get('sigma', 0), c['sigma_px'] * ech)
                    if c.get('douteux'):            # Lune saturée ou disque de la mauvaise taille : centre douteux
                        out['notes'].append(tr('pc_note_sature', nom=f.nom, s=_dec(100 * c['saturation'], 0),
                                               r=_dec(c['rapport_rayon'] or 0, 2)))
                        out['sigma'] = max(out['sigma'], abs(c['r'] - (r_att or c['r'])) * ech)
            else:
                if len(imgs) >= 3:
                    for k, (img, f) in enumerate(zip(imgs, images)):
                        vois = [imgs[j].donnees for j in (k - 1, k + 1) if 0 <= j < len(imgs)]
                        o = I.objet_mobile(img.donnees, vois)
                        ra, dec = I.pixel_vers_radec(img, o['x'], o['y'])
                        lh = I.lieu_et_heure(img.entete)
                        out['points'].append((lh['milieu'] or f.instant, ra, dec))
                else:
                    img, f = imgs[0], images[0]
                    o = I.trait_principal(img.donnees)
                    lh = I.lieu_et_heure(img.entete)
                    t0 = lh['instant'] or f.instant
                    t1 = t0 + D.timedelta(seconds=lh['pose_s'] or 0)
                    for (x, y), t in (((o['x1'], o['y1']), t0), ((o['x2'], o['y2']), t1)):
                        ra, dec = I.pixel_vers_radec(img, x, y)
                        out['points'].append((t, ra, dec))
                    out['notes'].append(tr('pc_note_trait'))
            return out
        t = Tache(travail, parent=self)
        t.quand_fini(lambda r, e=ed: self._mesure(e, r))
        t.quand_erreur(lambda e: self.contexte.statut(tr('pc_mesure_echec', erreur=e[:300])))
        self._taches.append(t)
        t.start()

    def _mesure(self, ed, r):
        ed.c_mode.setCurrentIndex(0)
        ed.vider()
        for t, a, b in r['points']:
            ed.ajouter_point(t, a, b)
        if r['lieu']:
            ed.remplir_lieu('', r['lieu']['lat'], r['lieu']['lon'], r['lieu']['alt_m'])
        if r.get('sigma'):
            ed.s_sigma.setValue(max(1.0, r['sigma']))
        ed.l_source.setText('\n'.join(r['notes']))
        self.contexte.statut(tr('pc_mesure_ok', n=len(r['points'])))

    # ------------------------------------------------------------------ calcul
    def calculer(self):
        cible, methode = self.c_cible.currentData(), self.c_methode.currentData()
        try:
            va = self.a.visee()
            vb = self.b.visee() if methode == 'deux' else None
        except C.ErreurCalcul as e:
            self.resultats.setHtml('<p>%s</p>' % html.escape(tr(e.cle, **e.valeurs)))
            return
        etoile = None
        if self.e_etoile.text().strip():
            morceaux = self.e_etoile.text().replace(';', ' ').split()
            if len(morceaux) >= 2:
                ra, dec = _ra(morceaux[0]), _flottant(morceaux[1])
                if ra is not None and dec is not None:
                    etoile = (ra, dec)
        tle = [x for x in self.e_tle.toPlainText().splitlines() if x.strip()]

        def travail():
            if methode == 'deux':
                if cible == 'lune':
                    return C.distance_lune(va, vb, etoile)
                return C.altitude_iss(va, vb, tle=tuple(tle) if len(tle) >= 2 else None)
            if methode == 'diurne':
                return dict(C.lune_parallaxe_diurne(va), genre='diurne')
            if methode == 'vitesse':
                return dict(C.iss_vitesse_angulaire(va), genre='vitesse')
            return dict(C.iss_orbite_circulaire(va), genre='orbite')
        self.b_calculer.setEnabled(False)
        t = Tache(travail, parent=self)
        t.quand_fini(self._resultat)
        t.quand_erreur(self._erreur)
        self._taches.append(t)
        t.start()

    def _erreur(self, texte):
        self.b_calculer.setEnabled(True)
        cle = next((m for m in texte.replace(':', ' ').split() if m.startswith('pc_err_')), '')
        self.resultats.setHtml('<p>%s</p>' % html.escape(tr(cle) if cle else texte[:400]))

    def _resultat(self, r):
        from .rapport import lignes_resultats
        self.b_calculer.setEnabled(True)
        self.resultat = r
        self.a_calcule = True
        e = html.escape
        if r.get('genre') in ('lune', 'iss'):
            h = ['<table>'] + ['<tr><th align="left">%s</th><td>%s</td></tr>' % (e(a), e(b))
                               for a, b in lignes_resultats(r)] + ['</table>']
            self.b_html.setEnabled(True)
            self.b_pdf.setEnabled(True)
        else:
            h = ['<p>%s</p>' % e(tr('pc_res_' + r['genre'], **{k: _dec(v, 2) if isinstance(v, float) else v
                                                                for k, v in r.items() if k != 'instant'}))]
        self.resultats.setHtml(''.join(h))
        if hasattr(self.contexte, '_maj_guide'):
            self.contexte._maj_guide()

    def notes_rapport(self) -> list:
        notes = []
        if self.contexte.appliquer_corrections:
            for t in self.contexte.tableaux_mesures():
                for m in t.mesures:
                    if m.corrections:
                        notes.append(tr('pc_note_correction', ligne=m.ligne, champs=', '.join(sorted(m.corrections))))
        for ed in (self.a, self.b):
            if ed.l_source.text():
                notes.append(ed.l_source.text())
        return notes

    def rapport(self, genre: str):
        if not self.resultat:
            return
        from .rapport import ecrire_html, ecrire_pdf
        nom = 'parallaxe_%s_%s.%s' % (self.resultat['genre'], self.resultat['instant'].strftime('%Y%m%d-%H%M%S'),
                                      genre)
        dossier = memoire.dossier('modules.partages.rapports', self.contexte._sortie())
        chemin, _ = fichiers.choisir_enregistrement(self, tr('pc_rapport_' + genre), os.path.join(dossier, nom),
                                                    'HTML (*.html)' if genre == 'html' else 'PDF (*.pdf)')
        if not chemin:
            return
        memoire.retenir('modules.partages.rapports', chemin, est_fichier=True)
        (ecrire_html if genre == 'html' else ecrire_pdf)(chemin, self.resultat, '', self.notes_rapport())
        self.contexte.statut(tr('pc_rapport_ecrit', chemin=chemin))
        ouvrir.ouvrir_defaut(chemin)

    def aide_html(self) -> str:
        return tr('pc_aide_html')


_ = (QComboBox, QDoubleSpinBox, QLineEdit)
