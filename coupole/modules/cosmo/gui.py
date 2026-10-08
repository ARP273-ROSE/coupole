"""Panneau « Cosmologie » : redshift → distances, âges, volume, module de distance, échelle ; courbes ; export CSV."""
from __future__ import annotations

from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtWidgets import (QDoubleSpinBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QSplitter,
                             QVBoxLayout, QWidget)

from ...core.i18n import langue, tr
from ...gui.adaptatif import Flux
from ...gui.modele import ModeleTableau, vue_tableau
from ...gui.outils import Tache, aide, bouton, case, champ, liste
from ...gui.trace import TraceCourbes
from . import calcul, formats

EXEMPLES = [('cosmo_ex_m87', 0.00428), ('cosmo_ex_3c273', 0.158), ('cosmo_ex_z1', 1.0), ('cosmo_ex_z234', 2.34),
            ('cosmo_ex_ulas', 7.085), ('cosmo_ex_gnz11', 10.6), ('cosmo_ex_reion', 20.0), ('cosmo_ex_cmb', 1089.8)]


def _calcul_complet(z, modele, H0, Om, Ok, shoes, avec_courbes):
    """Hors du fil graphique : grandeurs (et courbes si les paramètres ont changé)."""
    d = calcul.calculer(z, modele, H0, Om, Ok, incertitudes=(modele == 'planck18'), shoes=shoes)
    c = calcul.courbes(calcul.grille_z(), modele, H0, Om, Ok) if avec_courbes else None
    return d, c


def _paire(cle_libelle, widget):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 10, 0)
    h.addWidget(QLabel(tr(cle_libelle)))
    h.addWidget(widget)
    return w


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resultat = None
        self.courbes = None
        self._cle_courbes = None
        self._tache = None
        self._en_attente = False
        v = QVBoxLayout(self)

        # ---------------------------------------------------------------- paramètres
        g = QGroupBox(tr('cosmo_modele'))
        vg = QVBoxLayout(g)
        f = Flux()
        self.modele = liste('cosmo_modele_aide', [(tr('cosmo_mod_' + m), m) for m in calcul.MODELES])
        f.addWidget(self.modele)
        self.h0 = self._spin('cosmo_h0_aide', 0.0, 300.0, 2, calcul.H0_PLANCK, 0.1)
        self.om = self._spin('cosmo_om_aide', 0.0, 5.0, 4, calcul.OM_PLANCK, 0.01)
        self.ok = self._spin('cosmo_ok_aide', -2.0, 2.0, 4, 0.0, 0.01)
        for cle, w in (('cosmo_h0', self.h0), ('cosmo_om', self.om), ('cosmo_ok', self.ok)):
            f.addWidget(_paire(cle, w))
        self.shoes = case('cosmo_shoes')
        f.addWidget(self.shoes)
        vg.addLayout(f)
        self.l_params = QLabel('')
        self.l_params.setWordWrap(True)
        vg.addWidget(self.l_params)
        b = calcul.BORNES
        self.l_bornes = QLabel(tr('cosmo_bornes', h0a=self._n(b['H0'][0]), h0b=self._n(b['H0'][1]),
                                  oma=self._n(b['Om'][0]), omb=self._n(b['Om'][1]), oka=self._n(b['Ok_perso'][0]),
                                  okb=self._n(b['Ok_perso'][1]), okpa=self._n(b['Ok_planck18'][0]),
                                  okpb=self._n(b['Ok_planck18'][1])))
        self.l_bornes.setWordWrap(True)
        vg.addWidget(self.l_bornes)
        v.addWidget(g)

        # ---------------------------------------------------------------- saisie
        f = Flux()
        self.z = champ('cosmo_z_aide', '1', 'cosmo_z_indice')
        self.z.setMaximumWidth(self.z.fontMetrics().horizontalAdvance('0' * 14))
        self.z.returnPressed.connect(self.calculer)
        f.addWidget(_paire('cosmo_z', self.z))
        f.addWidget(bouton('cosmo_calculer', self.calculer))
        self.objet = champ('cosmo_objet_aide', '', 'cosmo_objet_indice')
        self.objet.setMinimumWidth(self.objet.fontMetrics().horizontalAdvance('M' * 10))
        self.objet.returnPressed.connect(self.chercher)
        f.addWidget(_paire('cosmo_objet', self.objet))
        self.b_chercher = bouton('cosmo_chercher', self.chercher)
        f.addWidget(self.b_chercher)
        self.candidats = liste('cosmo_candidats_aide', [])
        self.candidats.setVisible(False)
        self.candidats.activated.connect(self._candidat_choisi)
        f.addWidget(self.candidats)
        v.addLayout(f)
        f = Flux()
        for cle, zz in EXEMPLES:
            f.addWidget(bouton(cle, lambda _=False, x=zz: self.definir_z(x)))
        v.addLayout(f)
        self.l_etat = QLabel('')
        self.l_etat.setWordWrap(True)
        v.addWidget(self.l_etat)

        # ---------------------------------------------------------------- résultats
        sp = QSplitter(Qt.Orientation.Horizontal)
        self.m_res = ModeleTableau([tr('cosmo_col_grandeur'), tr('cosmo_col_valeur'), tr('cosmo_col_sigma'),
                                    tr('cosmo_col_shoes')])
        self.v_res, self.p_res = vue_tableau(self.m_res, 'cosmo_table_aide', selection_multiple=False)
        self.v_res.setSortingEnabled(False)
        sp.addWidget(self.v_res)
        self.trace = aide(TraceCourbes(), 'cosmo_courbes_aide')
        sp.addWidget(self.trace)
        sp.setSizes([760, 400])
        sp.setStretchFactor(0, 3)
        sp.setStretchFactor(1, 2)
        v.addWidget(sp, 1)
        f = Flux()
        f.addWidget(bouton('cosmo_csv_table', self.exporter_tableau))
        f.addWidget(bouton('cosmo_csv_courbes', self.exporter_courbes))
        self.l_credits = QLabel(tr('cosmo_credits'))
        self.l_credits.setWordWrap(True)
        v.addLayout(f)
        v.addWidget(self.l_credits)

        self.modele.currentIndexChanged.connect(self._modele_change)
        for w in (self.h0, self.om, self.ok):
            w.valueChanged.connect(self.calculer)
        self.shoes.toggled.connect(self.calculer)
        self._modele_change()

    # ------------------------------------------------------------ outils
    @staticmethod
    def _n(x):
        return formats.chiffres(x, 3)

    @staticmethod
    def _spin(cle_aide, mini, maxi, dec, valeur, pas):
        s = QDoubleSpinBox()
        s.setRange(mini, maxi)
        s.setDecimals(dec)
        s.setSingleStep(pas)
        s.setValue(valeur)
        s.setKeyboardTracking(False)          # calcul quand la saisie est finie, pas à chaque chiffre
        if langue() == 'fr':                  # virgule décimale, comme partout ailleurs dans l'interface
            s.setLocale(QLocale(QLocale.Language.French, QLocale.Country.France))
        else:
            s.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom))
        return aide(s, cle_aide)

    def _parametres(self):
        m = self.modele.currentData()
        return m, self.h0.value(), self.om.value(), (self.ok.value() if m in calcul.AVEC_COURBURE else 0.0)

    def _modele_change(self, *_):
        m = self.modele.currentData()
        perso = m == 'perso'
        for w in (self.h0, self.om):
            w.setEnabled(perso)
        self.ok.setEnabled(m in calcul.AVEC_COURBURE)
        self.shoes.setEnabled(m == 'planck18')
        if not perso:
            for w in (self.h0, self.om):
                w.blockSignals(True)
            self.h0.setValue(calcul.H0_PLANCK)
            self.om.setValue(calcul.OM_PLANCK)
            for w in (self.h0, self.om):
                w.blockSignals(False)
        self.calculer()

    # ------------------------------------------------------------ calcul
    def definir_z(self, z):
        self.z.setText(formats.court(z))
        self.calculer()

    def recevoir_redshift(self, z: float, nom: str = ''):
        """Point d'entrée des autres modules (fiche en ligne → « envoyer ce redshift »)."""
        self.objet.setText(nom)
        self.candidats.setVisible(False)
        self.definir_z(z)
        self.l_etat.setText(tr('cosmo_recu', nom=nom) if nom else '')

    def occupe(self):
        return False

    def calculer(self, *_):
        if self._tache is not None and self._tache.isRunning():
            self._en_attente = True                 # un seul calcul à la fois ; le dernier réglage gagne
            return
        modele, H0, Om, Ok = self._parametres()
        try:
            z = calcul.verifier_z(self.z.text())
            calcul.construire(modele, H0, Om, Ok)
        except calcul.ErreurCosmo as e:
            self.l_etat.setText(tr(e.cle, **{k: self._n(v) if isinstance(v, float) else v
                                             for k, v in e.valeurs.items()}))
            return
        cle = (modele, round(H0, 4), round(Om, 5), round(Ok, 5))
        avec = cle != self._cle_courbes
        if avec:
            self.l_etat.setText(tr('cosmo_calcul_courbes'))
        self._tache = Tache(_calcul_complet, z, modele, H0, Om, Ok, self.shoes.isChecked(), avec)
        self._tache.fini.connect(lambda r, k=cle: self._afficher(r, k))
        self._tache.erreur.connect(self._erreur)
        self._tache.start()

    def _erreur(self, e):
        self.l_etat.setText(e)
        self._suite()

    def _suite(self):
        if self._en_attente:
            self._en_attente = False
            self.calculer()

    def _afficher(self, r, cle):
        d, c = r
        if c is not None:
            self.courbes, self._cle_courbes = c, cle
            k = 1e-3 * calcul.al_par_mpc() / 1e6       # Mpc → G al
            self.trace.definir([(tr('cosmo_courbe_dc'), c['z'], c['comoving'] * k),
                                (tr('cosmo_courbe_dl'), c['z'], c['luminosity'] * k),
                                (tr('cosmo_courbe_da'), c['z'], c['angular_diameter'] * k),
                                (tr('cosmo_courbe_dlt'), c['z'], c['lookback'] * k)],
                               tr('cosmo_axe_z'), tr('cosmo_axe_d'))
            self.trace.format_x = 'z = {:.4g}'
            self.trace.format_y = '{:.4g}'
        self.trace.placer_marqueur(d['z'])
        self.resultat = d
        p = d['parametres']
        self.l_params.setText(tr('cosmo_params', h0=self._n(p['H0']), om=formats.chiffres(p['Om'], 4),
                                 onu=formats.chiffres(p['Onu0'], 3) if p['Onu0'] else '0',
                                 ode=formats.chiffres(p['Ode0'], 5), ok=formats.chiffres(p['Ok0'], 3) if
                                 abs(p['Ok0']) > 1e-12 else '0', og=formats.chiffres(p['Ogamma0'], 4) if
                                 p['Ogamma0'] else '0', t=formats.chiffres(p['Tcmb0'], 5) if p['Tcmb0'] else '0',
                                 neff=formats.chiffres(p['Neff'], 4), mnu=formats.chiffres(p['mnu'], 2) if p['mnu']
                                 else '0'))
        lignes, bulles = [], []
        for k, _ in calcul.GRANDEURS:
            s = (d.get('sigma') or {}).get(k)
            sh = d.get('shoes')
            txt_sh = ''
            if sh and k in sh:
                e = sh['ecart_pct'].get(k)
                txt_sh = formats.valeur(k, sh[k]) + ('  (%s%s %%)' % ('+' if e >= 0 else '−', formats.nombre(abs(e), 1))
                                                     if e is not None else '')
            lignes.append((tr('cosmo_g_' + k), formats.valeur(k, d[k]), formats.incertitude(k, d[k], s), txt_sh))
            bulles.append(tr('cosmo_g_' + k + '_aide'))
        self.m_res.remplir(lignes, [k for k, _ in calcul.GRANDEURS], bulles)
        self.v_res.setColumnHidden(2, 'sigma' not in d)
        self.v_res.setColumnHidden(3, 'shoes' not in d)
        self.v_res.resizeColumnsToContents()
        self.l_etat.setText(' '.join(tr(a) for a in d['avertissements']))
        self._suite()

    # ------------------------------------------------------------ SIMBAD
    def chercher(self):
        nom = self.objet.text().strip()
        if not nom:
            return
        from ...core import enligne
        self.b_chercher.setEnabled(False)
        self.candidats.setVisible(False)
        self.l_etat.setText(tr('cosmo_recherche', nom=nom))
        self._t_nom = Tache(enligne.redshift, nom)
        self._t_nom.fini.connect(self._nom_trouve)
        self._t_nom.erreur.connect(lambda e: self._nom_trouve({'etat': 'hors_ligne', 'erreur': e, 'demande': nom}))
        self._t_nom.start()

    def _nom_trouve(self, r):
        self.b_chercher.setEnabled(True)
        etat = r.get('etat')
        if etat == 'ok':
            self._appliquer_objet(r['nom'], r.get('type', ''), r.get('z'), r.get('cache'))
        elif etat == 'ambigu':
            self.candidats.clear()
            self.candidats.addItem(tr('cosmo_candidats_choix'), None)
            for c in r['candidats']:
                zt = formats.court(c['z']) if c.get('z') is not None else '—'
                self.candidats.addItem('%s (%s) z = %s' % (c['nom'], c.get('type', ''), zt), c)
            self.candidats.setVisible(True)
            self.l_etat.setText(tr('cosmo_ambigu', n=len(r['candidats']), nom=r.get('demande', '')))
        elif etat == 'hors_ligne':
            self.l_etat.setText(tr('cosmo_hors_ligne', erreur=(r.get('erreur') or '')[:120]))
        elif etat == 'desactive':
            self.l_etat.setText(tr('cosmo_desactive'))
        else:
            self.l_etat.setText(tr('cosmo_introuvable', nom=r.get('demande', '')))

    def _candidat_choisi(self, i):
        c = self.candidats.itemData(i)
        if c:
            self._appliquer_objet(c['nom'], c.get('type', ''), c.get('z'), False)

    def _appliquer_objet(self, nom, typ, z, cache):
        if z is None or z <= 0:
            self.l_etat.setText(tr('cosmo_trouve_sans_z', nom=nom, type=typ, z=formats.chiffres(z, 4)
                                   if z is not None else '—'))
            return
        self.objet.setText(nom)
        self.definir_z(z)
        self._message_objet = tr('cosmo_trouve', nom=nom, type=typ, z=formats.court(z),
                                 cache=tr('fiche_depuis_cache') if cache else '')
        self.l_etat.setText(self._message_objet)

    # ------------------------------------------------------------ export
    def exporter_tableau(self):
        if not self.resultat:
            QMessageBox.information(self, tr('cosmo_csv_table'), tr('cosmo_rien_a_exporter'))
            return
        f, _ = QFileDialog.getSaveFileName(self, tr('cosmo_csv_table'), 'cosmologie_z%g.csv' % self.resultat['z'],
                                           'CSV (*.csv)')
        if f:
            formats.ecrire_csv_resultats(f, [self.resultat])
            self.l_etat.setText(tr('cosmo_ecrit', chemin=f))

    def exporter_courbes(self):
        if not self.courbes:
            QMessageBox.information(self, tr('cosmo_csv_courbes'), tr('cosmo_rien_a_exporter'))
            return
        f, _ = QFileDialog.getSaveFileName(self, tr('cosmo_csv_courbes'), 'cosmologie_courbes.csv', 'CSV (*.csv)')
        if f:
            formats.ecrire_csv_courbes(f, self.courbes)
            self.l_etat.setText(tr('cosmo_ecrit', chemin=f))

    def aide_html(self):
        return tr('cosmo_aide_html')
