"""Panneau « Planificateur de parallaxe » : deux lieux → créneaux classés (tableau), ciel des deux lieux (dessin),
détail du créneau, exports CSV et agenda .ics."""
from __future__ import annotations

import datetime as D
import html
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QAbstractItemView, QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                             QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget)

from ...core.i18n import tr
from ...gui import fichiers, memoire
from ...gui.adaptatif import Flux, defilable
from ...gui.outils import Tache, aide, bouton, bouton_principal, champ, decimal, liste
from . import coordonnees as K
from . import planif as P
from .presentation import _n

UTC = D.timezone.utc
COULEURS = ('#e0803a', '#3a9be0')          # lieu 1, lieu 2 (lisibles sur fond clair et sombre)


class Ciel(QWidget):
    """Deux ciels côte à côte (projection azimutale équidistante : zénith au centre, horizon au bord)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.c = None
        self.noms = ['', '']
        self.setMinimumHeight(200)
        aide(self, 'pl_ciel_aide')

    def montrer(self, c, noms):
        self.c, self.noms = c, noms
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = self.palette()
        texte = pal.color(pal.ColorRole.WindowText)
        fond = pal.color(pal.ColorRole.Base)
        w, h = self.width(), self.height()
        r = max(min(w / 4.0, h / 2.0) - 22, 30)
        for n in (0, 1):
            cx, cy = w * (0.25 + 0.5 * n), h / 2.0 + 6
            p.setPen(QPen(texte, 1))
            p.setBrush(fond)
            p.drawEllipse(QPointF(cx, cy), r, r)
            grille = QColor(texte)
            grille.setAlpha(70)
            p.setPen(QPen(grille, 1, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            for hh in (30, 60):
                rr = r * (90 - hh) / 90
                p.drawEllipse(QPointF(cx, cy), rr, rr)
            p.setPen(QPen(texte, 1))
            for cle, az in (('pl_N', 0), ('pl_E', 90), ('pl_S', 180), ('pl_O', 270)):
                x, y = self._xy(cx, cy, r, -6, az)
                p.drawText(QRectF(x - 10, y - 9, 20, 18), Qt.AlignmentFlag.AlignCenter, tr(cle))
            p.drawText(QRectF(cx - r, 0, 2 * r, 16), Qt.AlignmentFlag.AlignCenter, self.noms[n] or tr('pl_lieu', n=n + 1))
            if not self.c or not self.c.trace:
                continue
            coul = QColor(COULEURS[n])
            chemin, premier = QPainterPath(), True
            for t, h1, a1, h2, a2 in self.c.trace:
                hh, az = (h1, a1) if n == 0 else (h2, a2)
                if hh < 0:
                    premier = True
                    continue
                x, y = self._xy(cx, cy, r, hh, az)
                if premier:
                    chemin.moveTo(x, y)
                    premier = False
                else:
                    chemin.lineTo(x, y)
            p.setPen(QPen(coul, 2))
            p.drawPath(chemin)
            x, y = self._xy(cx, cy, r, self.c.h[n], self.c.az[n])
            p.setBrush(coul)
            p.drawEllipse(QPointF(x, y), 5, 5)
        p.end()

    @staticmethod
    def _xy(cx, cy, r, h, az):
        rr = r * (90 - h) / 90
        a = math.radians(az)
        return cx + rr * math.sin(a), cy - rr * math.cos(a)


class PanneauPlanif(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.res = None
        self._taches = []
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        intro = QLabel(tr('pl_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        sp = QSplitter(Qt.Orientation.Horizontal)
        gauche = QWidget()
        vg = QVBoxLayout(gauche)
        vg.setContentsMargins(0, 0, 0, 0)
        f = QFormLayout()
        self.c_cible = liste('pl_cible_aide', [(tr('td_cible_iss'), 'iss'), (tr('td_cible_lune'), 'lune')])
        f.addRow(tr('pl_cible'), self.c_cible)
        vg.addLayout(f)
        self.e = {}
        for n in (1, 2):
            g = QGroupBox(tr('pl_lieu', n=n))
            fl = QFormLayout(g)
            for cle, aide_, indice in (('nom', 'pl_nom_aide', 'pl_nom_indice'), ('p', 'td_p_aide', 'td_p_indice'),
                                       ('alt', 'td_alt_aide', 'td_alt_indice')):
                w = champ(aide_, '', indice)
                self.e[cle + str(n)] = w
                fl.addRow(tr('pl_nom' if cle == 'nom' else 'td_' + cle), w)
                memoire.champ(w, 'modules.td.planif.%s%d' % (cle, n))
            vg.addWidget(g)
        f = QFormLayout()
        self.e_debut = champ('pl_debut_aide', '', 'pl_debut_indice')
        memoire.champ(self.e_debut, 'modules.td.planif.debut')
        f.addRow(tr('pl_debut'), self.e_debut)
        self.s_jours = decimal('pl_jours_aide', 0.5, 400.0, 7.0, 'pl_unite_j')
        self.s_hmin = decimal('pl_hmin_aide', 0.0, 85.0, 20.0, 'td_unite_deg')
        self.s_soleil = decimal('pl_soleil_aide', -18.0, 0.0, -6.0, 'td_unite_deg')
        f.addRow(tr('pl_jours'), self.s_jours)
        f.addRow(tr('pl_hmin'), self.s_hmin)
        f.addRow(tr('pl_soleil'), self.s_soleil)
        vg.addLayout(f)
        self.g_lune = QGroupBox(tr('td_cible_lune'))
        fl = QFormLayout(self.g_lune)
        self.s_mag = decimal('pl_mag_aide', 0.0, 5.5, 4.5)
        self.s_sep = decimal('pl_sep_aide', 0.5, 15.0, 5.0, 'td_unite_deg')
        self.s_phase = decimal('pl_phase_aide', 5.0, 100.0, 95.0, 'pl_unite_pct')
        fl.addRow(tr('pl_mag'), self.s_mag)
        fl.addRow(tr('pl_sep'), self.s_sep)
        fl.addRow(tr('pl_phase'), self.s_phase)
        vg.addWidget(self.g_lune)
        for w, cle in ((self.s_jours, 'jours'), (self.s_hmin, 'hmin'), (self.s_soleil, 'soleil'), (self.s_mag, 'mag'),
                       (self.s_sep, 'sep'), (self.s_phase, 'phase')):
            memoire.nombre(w, 'modules.td.planif.' + cle)
        self.c_tendance = aide(QCheckBox(tr('pl_tendance')), 'pl_tendance_aide')
        memoire.case(self.c_tendance, 'modules.td.planif.tendance')
        self.c_tendance.toggled.connect(self._cible)
        vg.addWidget(self.c_tendance)
        self.c_locale = aide(QCheckBox(tr('pl_locale')), 'pl_locale_aide')
        memoire.case(self.c_locale, 'modules.td.planif.locale')
        self.c_locale.toggled.connect(lambda _: self._remplir())
        vg.addWidget(self.c_locale)
        fl = Flux()
        self.b_chercher = bouton_principal('pl_chercher', self.chercher)
        fl.addWidget(self.b_chercher)
        fl.addWidget(bouton('pl_exemple', self.exemple))
        self.b_csv = bouton('pl_csv', self.exporter_csv)
        self.b_ics = bouton('pl_ics', self.exporter_ics)
        for b in (self.b_csv, self.b_ics):
            b.setEnabled(False)
            fl.addWidget(b)
        vg.addLayout(fl)
        vg.addStretch(1)
        sp.addWidget(defilable(gauche))
        droite = QSplitter(Qt.Orientation.Vertical)
        self.tableau = aide(QTableWidget(0, 7), 'pl_tableau_aide')
        self.tableau.setHorizontalHeaderLabels([tr(k) for k in ('pl_col_date', 'pl_col_heure', 'pl_col_note',
                                                               'pl_col_h', 'pl_col_mesure', 'pl_col_sujet',
                                                               'pl_col_infos')])
        self.tableau.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableau.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tableau.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableau.verticalHeader().setVisible(False)
        self.tableau.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tableau.horizontalHeader().setStretchLastSection(True)
        self.tableau.currentCellChanged.connect(lambda r, *_: self._choisir(r))
        droite.addWidget(self.tableau)
        self.ciel = Ciel()
        droite.addWidget(self.ciel)
        self.detail = aide(QTextBrowser(), 'pl_detail_aide')
        droite.addWidget(self.detail)
        droite.setSizes([300, 260, 260])
        sp.addWidget(droite)
        sp.setStretchFactor(0, 2)
        sp.setStretchFactor(1, 3)
        v.addWidget(sp, 1)
        self.l_etat = QLabel('')
        self.l_etat.setWordWrap(True)
        v.addWidget(self.l_etat)
        memoire.liste(self.c_cible, 'modules.td.planif.cible')
        memoire.separateur(sp, 'modules.td.planif.separateur')
        self.c_cible.currentIndexChanged.connect(self._cible)
        self._cible()

    # ------------------------------------------------------------------ saisie
    def _cible(self, *_):
        lune = self.c_cible.currentData() == 'lune'
        self.g_lune.setVisible(lune)
        self.c_tendance.setVisible(not lune)
        tendance = not lune and self.c_tendance.isChecked()
        self.s_jours.setMaximum(P.JOURS_MAX['lune' if lune else 'tendance' if tendance else 'iss'])

    def exemple(self):
        for n, (nom, pos, alt) in enumerate((('Paris', '48.8366 N, 2.3360 E', '67'),
                                             ('Lyon', '45.7597 N, 4.8422 E', '170')), 1):
            self.e['nom%d' % n].setText(nom)
            self.e['p%d' % n].setText(pos)
            self.e['alt%d' % n].setText(alt)

    def _debut(self):
        t = self.e_debut.text().strip()
        if not t:
            return D.datetime.now(UTC)
        from ..partages.mesures import instant
        v = instant(t if any(x in t.upper() for x in ('UTC', ' TU', 'Z')) else t + ' UTC').valeur
        if v is None:
            try:
                v = D.datetime.fromisoformat(t).replace(tzinfo=UTC)
            except ValueError:
                raise K.CoordonneeIllisible('pl_err_debut', texte=t) from None
        return v

    def entrees(self):
        sites = []
        for n in (1, 2):
            txt = self.e['p%d' % n].text()
            if not txt.strip():
                raise K.CoordonneeIllisible('pl_err_lieux')
            pos = K.lire_position(txt)
            sites.append(P.Site(pos.lat, pos.lon, K.lire_altitude(self.e['alt%d' % n].text()),
                                self.e['nom%d' % n].text().strip()))
        c = P.Criteres(self.c_cible.currentData(), self._debut(), self.s_jours.value(), self.s_hmin.value(),
                       self.s_soleil.value(), self.s_mag.value(), self.s_sep.value(), self.s_phase.value() / 100.0)
        c.tendance = c.cible == 'iss' and self.c_tendance.isChecked()
        return sites, c

    def chercher(self):
        try:
            sites, c = self.entrees()
        except K.CoordonneeIllisible as ex:
            self.l_etat.setText(tr(ex.cle, **ex.valeurs))
            return
        self.b_chercher.setEnabled(False)
        self.l_etat.setText(tr('pl_en_cours'))
        t = Tache(P.chercher_avec_tle, sites[0], sites[1], c, parent=self)
        t.quand_fini(self._resultat)
        t.quand_erreur(self._erreur)
        self._taches.append(t)
        t.start()

    def _erreur(self, texte):
        self.b_chercher.setEnabled(True)
        cle = next((m for m in texte.replace(':', ' ').split() if m.startswith(('pl_err_', 'td_err_'))), '')
        self.l_etat.setText(tr(cle, erreur='') if cle else texte[:300])

    def _resultat(self, r):
        self.b_chercher.setEnabled(True)
        self.res = r
        self._remplir()
        for b in (self.b_csv, self.b_ics):
            b.setEnabled(bool(r['creneaux']))
        if not r['creneaux']:
            self.l_etat.setText(tr('pl_aucun'))
            return
        msg = tr('pl_fini', n=r['nombre_total'], debut=self._t(r['debut'], '%d/%m/%Y'),
                 fin=self._t(r['fin'], '%d/%m/%Y'), base=_n(r['base_km'], 1), source=r['source'])
        for a in r.get('alertes', []):
            msg += ' ' + tr(a)
        self.l_etat.setText(msg)

    # ------------------------------------------------------------------ affichage
    def _t(self, x: D.datetime, fmt: str) -> str:
        x = x.astimezone() if self.c_locale.isChecked() else x.astimezone(UTC)
        s = x.strftime(fmt)
        return s if self.c_locale.isChecked() or '%H' not in fmt else s + ' UTC'

    def _remplir(self):
        r = self.res
        self.tableau.setRowCount(0)
        self.detail.clear()
        self.ciel.montrer(None, ['', ''])
        if not r:
            return
        self.tableau.setRowCount(len(r['creneaux']))
        for i, c in enumerate(r['creneaux']):
            if c.cible == 'iss':
                mesure = '%s°' % _n(c.parallaxe_deg, 1)
            else:
                mesure = 'Δφ %s′ (%s)' % (_n(c.etoile['delta_arcmin'], 2), c.etoile['nom'])
            err = '—' if c.erreur_sujet_pct is None else '%s %%' % _n(c.erreur_sujet_pct, 1)
            heure = self._t(c.meilleur, '%H:%M' if c.marge_s > 120 else '%H:%M:%S')
            if c.marge_s > 120:
                heure += ' ± %d min' % round(c.marge_s / 60)
            vals = (self._t(c.meilleur, '%d/%m/%Y'), heure, '%d' % round(c.note),
                    '%s° / %s°' % (_n(c.h[0], 0), _n(c.h[1], 0)), mesure, err,
                    ', '.join(tr(k) for k in c.remarques))
            for j, x in enumerate(vals):
                it = QTableWidgetItem(x)
                if j in (2, 5):
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tableau.setItem(i, j, it)
        if r['creneaux']:
            self.tableau.selectRow(0)
            self._choisir(0)

    def _choisir(self, i):
        r = self.res
        if not r or not (0 <= i < len(r['creneaux'])):
            return
        c = r['creneaux'][i]
        noms = [s.nom or tr('pl_lieu', n=k + 1) for k, s in enumerate(r['sites'])]
        self.ciel.montrer(c, noms)
        self.detail.setHtml(html_creneau(c, noms, self._t))

    def exporter_csv(self):
        if not self.res:
            return
        ch, _ = fichiers.choisir_enregistrement(self, tr('pl_csv'), 'parallaxe_creneaux.csv', 'CSV (*.csv)')
        if ch:
            with open(ch, 'w', encoding='utf-8-sig', newline='') as fh:
                fh.write(P.csv(self.res, self.c_locale.isChecked()))
            self.l_etat.setText(tr('pl_exporte', chemin=ch))

    def exporter_ics(self):
        if not self.res:
            return
        ch, _ = fichiers.choisir_enregistrement(self, tr('pl_ics'), 'parallaxe_creneaux.ics', 'iCalendar (*.ics)')
        if ch:
            with open(ch, 'w', encoding='utf-8', newline='') as fh:
                fh.write(P.ics(self.res))
            self.l_etat.setText(tr('pl_exporte', chemin=ch))

    def aide_html(self) -> str:
        return tr('pl_aide_html')


def html_creneau(c, noms, t) -> str:
    e = html.escape
    titre = tr('pl_d_titre_' + c.cible, date=t(c.meilleur, '%d/%m/%Y'))
    lignes = ['<h3>%s</h3>' % e(titre),
              '<p>%s</p>' % tr('pl_d_creneau', debut=e(t(c.debut, '%H:%M:%S')), fin=e(t(c.fin, '%H:%M:%S')),
                                meilleur=e(t(c.meilleur, '%H:%M:%S')), note='%d' % round(c.note)), '<ul>']
    for n in (0, 1):
        li = tr('pl_d_lieu', nom=e(noms[n]), h=_n(c.h[n], 1), az=_n(c.az[n], 1), d=_n(c.distance_km[n], 0),
                s=_n(c.soleil[n], 1))
        if c.magnitude:
            li += tr('pl_d_mag', m=_n(c.magnitude[n], 1))
        lignes.append('<li><span style="color:%s">●</span> %s</li>' % (COULEURS[n], li))
    lignes.append('</ul>')
    if c.cible == 'iss':
        lignes.append('<p>%s</p>' % tr('pl_d_parallaxe', p=_n(c.parallaxe_deg, 2), alt=_n(c.altitude_km, 0)))
        lignes.append('<p>%s</p>' % tr('pl_d_plan', e=_n(c.ecart_plan_deg, 1),
                                       ou=tr('pl_d_entre' if c.entre else 'pl_d_cote')))
        lignes.append('<p>%s</p>' % (tr('pl_d_sujet', e=_n(c.erreur_sujet_pct, 1)) if c.erreur_sujet_pct is not None
                                     else tr('pl_d_sujet_na')))
        lignes.append('<p>%s</p>' % tr('pl_d_synchro_iss', v=_n(c.vitesse_deg_s, 2), s=_n(c.synchro_s, 2)))
        if c.marge_s > 120:
            lignes.append('<p><b>%s</b></p>' % tr('pl_d_marge', m='%d' % round(c.marge_s / 60),
                                                  a=_n(c.marge_s / (2 * P.DERIVE_TLE_S_PAR_JOUR), 0)))
        if c.etoiles_proches:
            lignes.append('<p>%s</p>' % tr('pl_d_etoiles', liste=', '.join(
                '%s (%s, %s°)' % (e(x['nom']), _n(x['V'], 1), _n(x['sep'], 1)) for x in c.etoiles_proches)))
    else:
        s = c.etoile
        lignes.append('<p>%s</p>' % tr('pl_d_phase', p=_n(100 * c.phase, 0)))
        lignes.append('<p>%s</p>' % tr('pl_d_etoile', nom=e(s['nom']), V=_n(s['V'], 1), p1=_n(s['sep1'], 3),
                                       p2=_n(s['sep2'], 3), d=_n(s['delta_arcmin'], 2), i=_n(s['ideal_arcmin'], 2)))
        if c.erreur_sujet_pct is not None:
            lignes.append('<p>%s</p>' % tr('pl_d_sujet_lune', e=_n(c.erreur_sujet_pct, 1)))
        lignes.append('<p>%s</p>' % tr('pl_d_synchro_lune', s=_n(c.synchro_s, 0)))
    if c.remarques:
        lignes.append('<p>%s</p>' % tr('pl_d_remarques', liste=', '.join(tr(k) for k in c.remarques)))
    lignes.append('<p><i>%s</i></p>' % tr('pl_d_conseil'))
    return '\n'.join(lignes)
