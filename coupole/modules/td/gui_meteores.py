"""Panneau « Pluies de météores » : lieu et réglages à gauche ; onglets Calendrier, Une nuit (graphique heure par
heure et détail), Campagne (meilleures nuits, agenda .ics) et Réduction (ZHR, indice r).  Calcul : meteores.py."""
from __future__ import annotations

import datetime as D
import html
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QAbstractItemView, QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                             QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QTextBrowser,
                             QVBoxLayout, QWidget)

from ...core.i18n import langue, tr
from ...gui import fichiers, memoire
from ...gui.adaptatif import Flux, defilable
from ...gui.outils import Tache, aide, bouton, bouton_principal, champ, decimal, liste
from . import coordonnees as K
from . import meteores as M
from . import planif as P
from .presentation import _n

UTC = D.timezone.utc
COULEURS = ('#e0803a', '#3a9be0', '#4caf50', '#b05fd0', '#d0b030')


def _nom(p) -> str:
    return p['nom'].get(langue(), p['nom']['fr']) if isinstance(p, dict) else p.nom.get(langue(), p.nom['fr'])


def lire_date(texte: str) -> D.date:
    try:
        return D.date.fromisoformat(texte.strip())
    except ValueError:
        raise K.CoordonneeIllisible('mt_err_date', texte=texte) from None


def lire_instant(texte: str, locale: bool) -> D.datetime:
    t = texte.strip().replace('T', ' ')
    try:
        v = D.datetime.fromisoformat(t)
    except ValueError:
        raise K.CoordonneeIllisible('mt_err_date', texte=texte) from None
    if v.tzinfo is None:
        v = v.astimezone() if locale else v.replace(tzinfo=UTC)
    return v.astimezone(UTC)


def lire_magnitudes(texte: str) -> dict:
    out = {}
    for morceau in texte.replace(',', ' ').replace(';', ' ').split():
        m, _, n = morceau.partition(':')
        try:
            out[int(m)] = out.get(int(m), 0) + int(n)
        except ValueError:
            raise K.CoordonneeIllisible('mt_r_mags_aide') from None
    return out


class Graphe(QWidget):
    """Nuit de midi à midi (on montre la nuit et une heure de part et d'autre) : hauteurs des radiants, de la Lune,
    taux attendu de la première pluie (aire), crépuscule en gris."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.N, self.t = None, None
        self.setMinimumHeight(220)
        aide(self, 'mt_graphe_aide')

    def montrer(self, N, t):
        self.N, self.t = N, t
        self.update()

    def paintEvent(self, ev):
        N = self.N
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = self.palette()
        texte = pal.color(pal.ColorRole.WindowText)
        if N is None:
            return
        n = len(N.soleil)
        nuit = [i for i in range(n) if N.soleil[i] < 0]
        i0, i1 = (max(nuit[0] - 12, 0), min(nuit[-1] + 12, n - 1)) if nuit else (0, n - 1)
        fm = p.fontMetrics()
        g, d, hh, b = fm.horizontalAdvance('90°') + 10, fm.horizontalAdvance('000') + 12, fm.height() + 6, \
            fm.height() * 2 + 6
        R = QRectF(g, hh, max(self.width() - g - d, 50), max(self.height() - hh - b, 50))
        X = lambda i: R.left() + (i - i0) / max(i1 - i0, 1) * R.width()
        Y = lambda h: R.bottom() - max(min(h, 90.0), 0.0) / 90.0 * R.height()
        gris = QColor(texte)
        gris.setAlpha(35)
        debut = None                                              # crépuscule (Soleil > −12°), par plages
        for i in range(i0, i1 + 1):
            clair = N.soleil[i] >= M.SOLEIL_MAX and i < i1
            if clair and debut is None:
                debut = i
            elif not clair and debut is not None:
                p.fillRect(QRectF(X(debut), R.top(), X(i) - X(debut), R.height()), gris)
                debut = None
        grille = QColor(texte)
        grille.setAlpha(70)
        p.setPen(QPen(grille, 1, Qt.PenStyle.DotLine))
        for h in (20, 30, 60, 90):
            p.drawLine(QPointF(R.left(), Y(h)), QPointF(R.right(), Y(h)))
            p.drawText(QRectF(0, Y(h) - fm.height() / 2, g - 4, fm.height()),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, '%d°' % h)
        p.setPen(QPen(texte, 1))
        p.drawRect(R)
        t0 = self.t(N.instant(i0))                                # heures paires (fuseau affiché)
        marque = t0.replace(minute=0, second=0, microsecond=0) + D.timedelta(hours=1)
        while marque <= self.t(N.instant(i1)):
            if marque.hour % 2 == 0:
                x = X(i0 + (marque - t0).total_seconds() / N.pas_s)
                p.drawLine(QPointF(x, R.bottom()), QPointF(x, R.bottom() + 4))
                p.drawText(QRectF(x - 30, R.bottom() + 4, 60, fm.height()), Qt.AlignmentFlag.AlignHCenter,
                           marque.strftime('%Hh'))
            marque += D.timedelta(hours=1)
        # taux de la première pluie (aire, axe de droite)
        if N.pluies:
            e = N.pluies[0]
            tm = max(float(max(e['taux'][i0:i1 + 1])), 1.0)
            k = 10 ** math.floor(math.log10(tm))
            ech = next(m * k for m in (1, 2, 5, 10) if m * k >= tm)      # graduation « ronde » ≥ taux maximal
            c = QColor(COULEURS[0])
            c.setAlpha(60)
            chemin = QPainterPath(QPointF(X(i0), R.bottom()))
            for i in range(i0, i1 + 1):
                v = float(e['taux'][i]) if e['utile'][i] else 0.0
                chemin.lineTo(QPointF(X(i), R.bottom() - v / ech * R.height()))
            chemin.lineTo(QPointF(X(i1), R.bottom()))
            p.fillPath(chemin, c)
            p.setPen(QPen(texte, 1))
            for v in (0, ech / 2, ech):
                y = R.bottom() - v / ech * R.height()
                p.drawText(QRectF(R.right() + 4, y - fm.height() / 2, d, fm.height()),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, '%g' % v)
        # courbes
        def courbe(vals, couleur, style=Qt.PenStyle.SolidLine):
            p.setPen(QPen(QColor(couleur), 2, style))
            ch, dedans = QPainterPath(), False
            for i in range(i0, i1 + 1):
                if vals[i] > 0:
                    pt = QPointF(X(i), Y(float(vals[i])))
                    ch.lineTo(pt) if dedans else ch.moveTo(pt)
                    dedans = True
                else:
                    dedans = False
            p.drawPath(ch)
        courbe(N.lune, texte, Qt.PenStyle.DashLine)
        lg = [(tr('mt_leg_lune') + ' %d %%' % round(100 * N.lune_frac), None)]
        for k, e in enumerate(N.pluies[:len(COULEURS)]):
            courbe(e['h'], COULEURS[k])
            lg.append((e['code'], COULEURS[k]))
        x = R.left()
        p.setPen(QPen(texte, 1))
        p.drawText(QRectF(R.left(), 0, R.width(), hh), Qt.AlignmentFlag.AlignLeft, tr('mt_axe_h'))
        p.drawText(QRectF(R.left(), 0, R.width() + d, hh), Qt.AlignmentFlag.AlignRight, tr('mt_axe_taux'))
        y = R.bottom() + fm.height() + 6
        for nom, c in lg:
            p.setPen(QPen(QColor(c) if c else texte, 2, Qt.PenStyle.SolidLine if c else Qt.PenStyle.DashLine))
            p.drawLine(QPointF(x, y + fm.height() / 2), QPointF(x + 16, y + fm.height() / 2))
            p.setPen(QPen(texte, 1))
            w = fm.horizontalAdvance(nom)
            p.drawText(QRectF(x + 20, y, w + 4, fm.height()), Qt.AlignmentFlag.AlignLeft, nom)
            x += w + 36


def html_nuit(N, t, f_heure) -> str:
    e = html.escape
    L = ['<h3>%s</h3>' % e(tr('mt_n_titre', date=t(N.debut, '%d/%m/%Y')))]
    if N.nuit:
        L.append('<p>%s</p>' % tr('mt_n_noire', debut=e(f_heure(N.instant(N.nuit[0]))),
                                  fin=e(f_heure(N.instant(N.nuit[1])))))
    else:
        L.append('<p>%s</p>' % tr('mt_n_pas_nuit'))
    L.append('<p>%s%s</p>' % (tr('mt_n_lune', p='%d' % round(100 * N.lune_frac)),
                              tr('mt_n_lune_ok' if N.lune_frac <= M.LUNE_NEGLIGEABLE else 'mt_n_lune_ko')))
    if not N.pluies:
        L.append('<p>%s</p>' % tr('mt_n_aucune'))
    for x in N.pluies:
        if x['meilleur'] is None or x['attendu'] <= 0:
            s = tr('mt_n_pluie_rien', nom=e(_nom(x)))
        else:
            i = x['meilleur']
            s = tr('mt_n_pluie', nom=e(_nom(x)), n=_n(x['attendu'], 0), heures=_n(x['heures'], 1),
                   taux=_n(float(x['taux'][i]), 0 if x['taux'][i] >= 10 else 1), heure=e(f_heure(N.instant(i))),
                   h=_n(float(x['h'][i]), 0), z=_n(float(x['zhr'][i]), 0 if x['zhr'][i] >= 10 else 1))
            if x['champ']:
                s += ' ' + tr('mt_n_champ', az=_n(x['champ'][0], 0), h=_n(x['champ'][1], 0))
        if x['variable']:
            s += tr('mt_n_var')
        L.append('<p>%s</p>' % s)
    L.append('<p><i>%s</i></p>' % tr('mt_n_conseil'))
    L.append('<p><small>%s</small></p>' % tr('mt_sources'))
    return '\n'.join(L)


def _tableau(cles, cle_aide):
    t = aide(QTableWidget(0, len(cles)), cle_aide)
    t.setHorizontalHeaderLabels([tr(k) for k in cles])
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    return t


def _remplir(t, lignes, droite=()):
    t.setRowCount(len(lignes))
    for i, vals in enumerate(lignes):
        for j, x in enumerate(vals):
            it = QTableWidgetItem(x)
            if j in droite:
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            t.setItem(i, j, it)


class PanneauMeteores(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._taches = []
        self.N = None
        self.camp = []
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        intro = QLabel(tr('mt_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        sp = QSplitter(Qt.Orientation.Horizontal)
        gauche = QWidget()
        vg = QVBoxLayout(gauche)
        vg.setContentsMargins(0, 0, 0, 0)
        g = QGroupBox(tr('mt_lieu'))
        fl = QFormLayout(g)
        self.e = {}
        for cle, aide_, indice in (('nom', 'pl_nom_aide', 'pl_nom_indice'), ('p', 'td_p_aide', 'td_p_indice'),
                                   ('alt', 'td_alt_aide', 'td_alt_indice')):
            w = champ(aide_, '', indice)
            self.e[cle] = w
            fl.addRow(tr('pl_nom' if cle == 'nom' else 'td_' + cle), w)
            memoire.champ(w, 'modules.td.meteores.%s' % cle)
        fl.addRow('', bouton('lieu_bouton', self.choisir_lieu))
        vg.addWidget(g)
        f = QFormLayout()
        self.s_lm = decimal('mt_lm_aide', 2.0, 7.5, 6.0)
        self.s_f = decimal('mt_f_aide', 0.1, 1.0, 1.0)
        self.s_f.setDecimals(2)
        self.s_f.setSingleStep(0.05)
        f.addRow(tr('mt_lm'), self.s_lm)
        f.addRow(tr('mt_f'), self.s_f)
        vg.addLayout(f)
        memoire.nombre(self.s_lm, 'modules.td.meteores.lm')
        memoire.nombre(self.s_f, 'modules.td.meteores.f')
        self.c_locale = aide(QCheckBox(tr('mt_locale')), 'mt_locale_aide')
        memoire.case(self.c_locale, 'modules.td.meteores.locale')
        self.c_locale.toggled.connect(lambda _: self._rafraichir())
        vg.addWidget(self.c_locale)
        fl = Flux()
        fl.addWidget(bouton('pl_exemple', self.exemple))
        vg.addLayout(fl)
        vg.addStretch(1)
        sp.addWidget(defilable(gauche))
        self.onglets = QTabWidget()
        self.onglets.addTab(self._onglet_calendrier(), tr('mt_onglet_calendrier'))
        self.onglets.addTab(self._onglet_nuit(), tr('mt_onglet_nuit'))
        self.onglets.addTab(self._onglet_campagne(), tr('mt_onglet_campagne'))
        self.onglets.addTab(defilable(self._onglet_reduction()), tr('mt_onglet_reduction'))
        for k, cle in enumerate(('calendrier', 'nuit', 'campagne', 'reduction')):
            self.onglets.setTabToolTip(k, tr('mt_onglet_%s_aide' % cle))
        memoire.onglets(self.onglets, 'modules.td.meteores.onglet')
        sp.addWidget(self.onglets)
        sp.setStretchFactor(0, 2)
        sp.setStretchFactor(1, 5)
        memoire.separateur(sp, 'modules.td.meteores.separateur')
        v.addWidget(sp, 1)
        self.l_etat = QLabel('')
        self.l_etat.setWordWrap(True)
        v.addWidget(self.l_etat)
        self.e['p'].textChanged.connect(lambda _: self.calendrier())   # culmination au nouveau lieu (carte, saisie)
        self.calendrier()

    # ------------------------------------------------------------------ onglets
    def _onglet_calendrier(self):
        w = QWidget()
        v = QVBoxLayout(w)
        h = QHBoxLayout()
        h.addWidget(QLabel(tr('mt_annee')))
        self.s_annee = aide(QSpinBox(), 'mt_annee_aide')
        self.s_annee.setRange(1900, 2100)
        self.s_annee.setValue(D.date.today().year + (1 if D.date.today().month == 12 else 0))
        self.s_annee.valueChanged.connect(lambda _: self.calendrier())
        h.addWidget(self.s_annee)
        h.addWidget(bouton('mt_voir_nuit', self.voir_nuit_du_max))
        h.addStretch(1)
        v.addLayout(h)
        self.t_cal = _tableau(('mt_col_pluie', 'mt_col_activite', 'mt_col_max', 'mt_col_zhr', 'mt_col_r',
                               'mt_col_v', 'mt_col_radiant', 'mt_col_culm', 'mt_col_lune'), 'mt_calendrier_aide')
        self.t_cal.cellDoubleClicked.connect(lambda *_: self.voir_nuit_du_max())
        v.addWidget(self.t_cal, 1)
        s = QLabel(tr('mt_sources'))
        s.setWordWrap(True)
        v.addWidget(s)
        return w

    def _onglet_nuit(self):
        w = QWidget()
        v = QVBoxLayout(w)
        fl = Flux()
        fl.addWidget(QLabel(tr('mt_nuit_date')))
        self.e_nuit = champ('mt_nuit_date_aide', D.date.today().isoformat(), 'mt_nuit_indice')
        fl.addWidget(self.e_nuit)
        fl.addWidget(QLabel(tr('mt_nuit_pluie')))
        self.c_pluie = liste('mt_nuit_pluie', [(tr('mt_pluie_toutes'), '')] +
                             [('%s (%s)' % (_nom(p), p.code), p.code) for p in M.pluies()])
        fl.addWidget(self.c_pluie)
        fl.addWidget(QLabel(tr('mt_zhr_force')))
        self.s_zhr = decimal('mt_zhr_force_aide', 0.0, 10000.0, 0.0)
        self.s_zhr.setDecimals(0)
        fl.addWidget(self.s_zhr)
        self.b_nuit = bouton_principal('mt_calculer', self.calculer_nuit)
        fl.addWidget(self.b_nuit)
        v.addLayout(fl)
        sp = QSplitter(Qt.Orientation.Vertical)
        self.graphe = Graphe()
        sp.addWidget(self.graphe)
        self.d_nuit = aide(QTextBrowser(), 'mt_detail_aide')
        sp.addWidget(self.d_nuit)
        sp.setSizes([300, 260])
        v.addWidget(sp, 1)
        return w

    def _onglet_campagne(self):
        w = QWidget()
        v = QVBoxLayout(w)
        fl = Flux()
        fl.addWidget(QLabel(tr('mt_du')))
        self.e_du = champ('mt_du_aide', '', 'mt_nuit_indice')
        fl.addWidget(self.e_du)
        fl.addWidget(QLabel(tr('mt_au')))
        self.e_au = champ('mt_au_aide', '', 'mt_nuit_indice')
        fl.addWidget(self.e_au)
        fl.addWidget(QLabel(tr('mt_min')))
        self.s_min = decimal('mt_min_aide', 1.0, 1000.0, 20.0, 'mt_unite_met')
        self.s_min.setDecimals(0)
        fl.addWidget(self.s_min)
        memoire.nombre(self.s_min, 'modules.td.meteores.min')
        self.b_camp = bouton_principal('mt_chercher', self.chercher)
        fl.addWidget(self.b_camp)
        self.b_ics = bouton('mt_ics', self.exporter_ics)
        self.b_csv = bouton('mt_csv', self.exporter_csv)
        for b in (self.b_ics, self.b_csv):
            b.setEnabled(False)
            fl.addWidget(b)
        v.addLayout(fl)
        self.t_camp = _tableau(('mt_col_nuit', 'mt_col_pluie', 'mt_col_attendus', 'mt_col_heures',
                                'mt_col_meilleur', 'mt_col_taux', 'mt_col_hr', 'mt_col_lune', 'mt_col_note'),
                               'mt_campagne_aide')
        self.t_camp.cellDoubleClicked.connect(self._voir_nuit_campagne)
        v.addWidget(self.t_camp, 1)
        return w

    def _onglet_reduction(self):
        w = QWidget()
        v = QVBoxLayout(w)
        lab = QLabel(tr('mt_r_intro'))
        lab.setWordWrap(True)
        v.addWidget(lab)
        f = QFormLayout()
        self.c_rpluie = liste('mt_nuit_pluie', [('%s (%s)' % (_nom(p), p.code), p.code) for p in M.pluies()])
        self.c_rpluie.currentIndexChanged.connect(self._r_de_la_pluie)
        f.addRow(tr('mt_r_pluie'), self.c_rpluie)
        self.e_rdeb = champ('mt_r_heure_aide', '', 'pl_debut_indice')
        self.e_rfin = champ('mt_r_heure_aide', '', 'pl_debut_indice')
        f.addRow(tr('mt_r_debut'), self.e_rdeb)
        f.addRow(tr('mt_r_fin'), self.e_rfin)
        self.s_pause = decimal('mt_r_pause_aide', 0.0, 600.0, 0.0, 'mt_unite_min')
        self.s_pause.setDecimals(0)
        f.addRow(tr('mt_r_pause'), self.s_pause)
        self.s_n = aide(QSpinBox(), 'mt_r_n_aide')
        self.s_n.setRange(0, 100000)
        f.addRow(tr('mt_r_n'), self.s_n)
        self.s_r = decimal('mt_r_r_aide', 1.2, 5.0, 2.5)
        self.s_r.setDecimals(2)
        f.addRow(tr('mt_r_r'), self.s_r)
        v.addLayout(f)
        fl = Flux()
        fl.addWidget(bouton_principal('mt_r_calculer', self.reduire))
        v.addLayout(fl)
        self.l_zhr = QLabel('')
        self.l_zhr.setWordWrap(True)
        self.l_zhr.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(self.l_zhr)
        f = QFormLayout()
        self.e_mags = champ('mt_r_mags_aide', '', 'mt_r_mags_indice')
        f.addRow(tr('mt_r_mags'), self.e_mags)
        v.addLayout(f)
        fl = Flux()
        fl.addWidget(bouton('mt_r_r_calc', self.estimer_r))
        v.addLayout(fl)
        self.l_r = QLabel('')
        self.l_r.setWordWrap(True)
        v.addWidget(self.l_r)
        v.addStretch(1)
        for wd, cle in ((self.c_rpluie, 'rpluie'),):
            memoire.liste(wd, 'modules.td.meteores.' + cle)
        self._r_de_la_pluie()
        return w

    # ------------------------------------------------------------------ saisie
    def choisir_lieu(self):
        from .gui_lieu import choisir
        choisir(self, self.e['p'], self.e['alt'], self.e['nom'])

    def exemple(self):
        self.e['nom'].setText('Paris')
        self.e['p'].setText('48.8366 N, 2.3360 E')
        self.e['alt'].setText('67')
        self.calendrier()

    def site(self, obligatoire=True) -> P.Site | None:
        txt = self.e['p'].text()
        if not txt.strip():
            if obligatoire:
                raise K.CoordonneeIllisible('mt_err_lieu')
            return None
        pos = K.lire_position(txt)
        return P.Site(pos.lat, pos.lon, K.lire_altitude(self.e['alt'].text()), self.e['nom'].text().strip())

    def _t(self, x: D.datetime, fmt: str) -> str:
        x = x.astimezone() if self.c_locale.isChecked() else x.astimezone(UTC)
        s = x.strftime(fmt)
        return s if self.c_locale.isChecked() or '%H' not in fmt else s + ' UTC'

    def _heure(self, x: D.datetime) -> str:
        return self._t(x, '%H:%M')

    def _rafraichir(self):
        self.calendrier()
        if self.N is not None:
            self._montrer_nuit()
        self._remplir_campagne()

    def _probleme(self, ex):
        self.l_etat.setText(tr(ex.cle, **ex.valeurs))

    # ------------------------------------------------------------------ calendrier
    def calendrier(self):
        try:
            s = self.site(False)
        except K.CoordonneeIllisible:
            s = None
        self.cal = M.calendrier(self.s_annee.value(), s)
        lignes = []
        for e in self.cal:
            if e['note_zhr'] == 'var':
                z = tr('mt_zhr_var')
            elif e['note_zhr'] == '+':
                z = tr('mt_zhr_plus', z='%d' % e['zhr'])
            else:
                z = '%g' % e['zhr']
            culm = '—'
            if 'culmination' in e:
                culm = '%s°' % _n(e['culmination'], 0) if e['culmination'] > 0 else tr('mt_jamais')
            lignes.append(('%s (%s)' % (_nom(e), e['code']),
                           '%s – %s' % (self._t(e['debut'], '%d/%m'), self._t(e['fin'], '%d/%m')),
                           self._t(e['max'], '%d/%m %H:%M') if e['max'] else '—', z, _n(e['r'], 1), '%d' % e['v'],
                           '%s°, %s°' % (_n(e['alpha'], 0), _n(round(e['delta']) or 0.0, 0)), culm,
                           '%d %%' % round(100 * e['lune']) if 'lune' in e else '—'))
        _remplir(self.t_cal, lignes, droite=(3, 4, 5, 7, 8))

    def voir_nuit_du_max(self):
        i = self.t_cal.currentRow()
        if not (0 <= i < len(self.cal)) or not self.cal[i]['max']:
            return
        e = self.cal[i]
        t = e['max'].astimezone()
        # la nuit « du soir » : un maximum le matin appartient à la nuit de la veille
        jour = (t - D.timedelta(hours=12)).date()
        self.e_nuit.setText(jour.isoformat())
        self.c_pluie.setCurrentIndex(self.c_pluie.findData(e['code']))
        self.onglets.setCurrentIndex(1)
        self.calculer_nuit()

    # ------------------------------------------------------------------ une nuit
    def calculer_nuit(self):
        try:
            s, jour = self.site(), lire_date(self.e_nuit.text())
        except K.CoordonneeIllisible as ex:
            return self._probleme(ex)
        code = self.c_pluie.currentData()
        force = {code: self.s_zhr.value()} if code and self.s_zhr.value() > 0 else None
        self.N = M.nuit(s, jour, self.s_lm.value(), self.s_f.value(), codes=[code] if code else None,
                        zhr_force=force)
        self.l_etat.setText('')
        self._montrer_nuit()

    def _montrer_nuit(self):
        self.graphe.montrer(self.N, lambda x: x.astimezone() if self.c_locale.isChecked() else x.astimezone(UTC))
        self.d_nuit.setHtml(html_nuit(self.N, self._t, self._heure))

    # ------------------------------------------------------------------ campagne
    def _periode(self):
        du = lire_date(self.e_du.text()) if self.e_du.text().strip() else D.date.today()
        if self.e_au.text().strip():
            au = lire_date(self.e_au.text())
        else:
            au = D.date(du.year + (1 if (du.month, du.day) > (8, 31) else 0), 8, 31)
        return du, au

    def chercher(self):
        try:
            s = self.site()
            du, au = self._periode()
        except K.CoordonneeIllisible as ex:
            return self._probleme(ex)
        self.b_camp.setEnabled(False)
        self.l_etat.setText(tr('mt_en_cours'))
        t = Tache(M.campagne, s, du, au, self.s_lm.value(), self.s_f.value(), self.s_min.value(), parent=self)
        t.quand_fini(lambda r, du=du, au=au, s=s: self._campagne(r, du, au, s))
        t.quand_erreur(lambda texte: (self.b_camp.setEnabled(True), self.l_etat.setText(texte[:300])))
        self._taches.append(t)
        t.start()

    def _campagne(self, r, du, au, s):
        self.b_camp.setEnabled(True)
        self.camp, self.camp_site = r, s
        for b in (self.b_ics, self.b_csv):
            b.setEnabled(bool(r))
        self._remplir_campagne()
        self.l_etat.setText(tr('mt_c_fini', n=len({x['nuit'] for x in r}), debut=du.strftime('%d/%m/%Y'),
                               fin=au.strftime('%d/%m/%Y')) if r else tr('mt_c_aucun'))

    def _remplir_campagne(self):
        lignes = [(x['nuit'].strftime('%d/%m/%Y'), '%s (%s)' % (_nom(x), x['code']), _n(x['attendu'], 0),
                   _n(x['heures'], 1), self._heure(x['meilleur']), _n(x['taux_max'], 0), '%s°' % _n(x['h_radiant'], 0),
                   '%d %%' % round(100 * x['lune']), '%d' % x['note']) for x in self.camp]
        _remplir(self.t_camp, lignes, droite=(2, 3, 5, 6, 7, 8))

    def _voir_nuit_campagne(self, i, *_):
        if 0 <= i < len(self.camp):
            x = self.camp[i]
            self.e_nuit.setText(x['nuit'].isoformat())
            self.c_pluie.setCurrentIndex(self.c_pluie.findData(x['code']))
            self.onglets.setCurrentIndex(1)
            self.calculer_nuit()

    def exporter_ics(self):
        if not self.camp:
            return
        ch, _ = fichiers.choisir_enregistrement(self, tr('mt_ics'), 'meteores_nuits.ics', 'iCalendar (*.ics)')
        if ch:
            with open(ch, 'w', encoding='utf-8', newline='') as fh:
                fh.write(M.ics(self.camp, self.camp_site.nom))
            self.l_etat.setText(tr('mt_exporte', chemin=ch))

    def exporter_csv(self):
        if not self.camp:
            return
        ch, _ = fichiers.choisir_enregistrement(self, tr('mt_csv'), 'meteores_nuits.csv', 'CSV (*.csv)')
        if ch:
            with open(ch, 'w', encoding='utf-8-sig', newline='') as fh:
                fh.write(M.csv(self.camp, self.c_locale.isChecked()))
            self.l_etat.setText(tr('mt_exporte', chemin=ch))

    # ------------------------------------------------------------------ réduction
    def _r_de_la_pluie(self, *_):
        code = self.c_rpluie.currentData()
        if code:
            self.s_r.setValue(M.pluie(code).r)

    def reduire(self):
        try:
            s = self.site()
            t0 = lire_instant(self.e_rdeb.text(), self.c_locale.isChecked())
            t1 = lire_instant(self.e_rfin.text(), self.c_locale.isChecked())
        except K.CoordonneeIllisible as ex:
            return self._probleme(ex)
        code = self.c_rpluie.currentData()
        t_eff = ((t1 - t0).total_seconds() / 60.0 - self.s_pause.value()) / 60.0
        h = M.hauteur_radiant(s, code, t0 + (t1 - t0) / 2)
        try:
            r = M.reduction(self.s_n.value(), t_eff, self.s_lm.value(), self.s_f.value(), self.s_r.value(), h)
        except ValueError as ex:
            self.l_zhr.setText(tr(str(ex)))
            return
        if r['zhr'] is None:
            txt = tr('mt_r_couche')
        else:
            fa = r['facteurs']
            txt = tr('mt_r_resultat', z=_n(r['zhr'], 1), e=_n(r['err'], 1), t=_n(t_eff, 2), h=_n(h, 1))
            txt += '<br>' + tr('mt_r_facteurs', t=_n(fa['temps'], 2), f=_n(fa['champ'], 2), lm=_n(fa['lm'], 2),
                               h=_n(fa['hauteur'], 2))
        for a in r['alertes']:
            txt += '<br><b>%s</b>' % html.escape(tr(a))
        self.l_zhr.setText(txt)
        self.l_etat.setText('')

    def estimer_r(self):
        try:
            c = lire_magnitudes(self.e_mags.text())
        except K.CoordonneeIllisible as ex:
            self.l_r.setText(tr(ex.cle))
            return
        r = M.indice_population(c, self.s_lm.value())
        if r['r'] is None:
            self.l_r.setText(tr('mt_r_indice_aucun'))
            return
        self.l_r.setText(tr('mt_r_indice', r=_n(r['r'], 2),
                            liste=', '.join('%s' % _n(x, 2) for _, x in r['rapports'])))
        self.s_r.setValue(round(r['r'], 2))

    def aide_html(self) -> str:
        return tr('mt_aide_html')


_ = (QColor, QPen)
