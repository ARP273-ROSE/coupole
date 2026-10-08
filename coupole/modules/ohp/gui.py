"""Interface du module « Banque OHP » : Catalogue, Traitement, Lots, Anomalies.

Tout travail long (inventaire, traitement, anomalies) tourne hors du fil
graphique ; l'interface lit les événements à cadence fixe et reste réactive.
"""
from __future__ import annotations

import csv
import html
import os
import threading
import time

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QMessageBox, QPlainTextEdit, QProgressBar, QSplitter, QTabWidget, QVBoxLayout, QWidget)

from ...core import config, i18n
from ...core.i18n import tr
from ...gui.adaptatif import Flux, coupable
from ...gui.dialogues import DialogueASTAP, ouvrir_fichier
from ...gui.modele import ModeleTableau, lignes_choisies, vue_tableau
from ...gui.outils import (FileEvenements, Tache, aide, bouton, case, champ, decimal, enregistrer_arret, lancer_fil,
                           liste, nombre)
from . import cibles


def _taille(o: float) -> str:
    return tr('taille_go', v='%.2f' % (o / 1e9)) if o >= 1e8 else tr('taille_mo', v='%.1f' % (o / 1e6))


from .gui_sans_qt import duree_lisible  # noqa: E402


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inv = None
        self.selection = []
        self.traitement = None
        self.arret = None
        self.pause = None
        self._fil = None
        self._nouveautes = None
        self._mode_tout = False
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        self.bandeau = self._bandeau_nouveautes()
        self.bandeau.setVisible(False)
        v.addWidget(self.bandeau)
        self.onglets = aide(QTabWidget(), 'ohp_onglets_aide')
        v.addWidget(self.onglets)
        self.onglets.addTab(self._onglet_catalogue(), tr('ohp_onglet_catalogue'))
        self.onglets.addTab(self._onglet_traitement(), tr('ohp_onglet_traitement'))
        self.onglets.addTab(self._onglet_lots(), tr('ohp_onglet_lots'))
        self.onglets.addTab(self._onglet_anomalies(), tr('ohp_onglet_anomalies'))
        self.onglets.addTab(self._onglet_ciel(), tr('ohp_onglet_ciel'))
        from ...gui.fiche import FicheEnLigne
        self.fiche = FicheEnLigne()
        self.onglet_fiche = self.onglets.addTab(self.fiche, tr('fiche_titre'))
        self.onglets.currentChanged.connect(self._maj_fiche)
        self._remplir_lots()
        sc = QShortcut(QKeySequence('Ctrl+R'), self)
        sc.activated.connect(lambda: self.charger(True))
        self.charger(False)
        self._etat_astap = None

    # ================================================================ bandeau des nouveautés
    def _bandeau_nouveautes(self):
        w = QFrame()
        w.setObjectName('bandeauNouveautes')
        w.setFrameShape(QFrame.Shape.StyledPanel)
        aide(w, 'ohp_bandeau_aide')
        h = Flux(w, marge=6)
        self.l_bandeau = QLabel('')
        self.l_bandeau.setWordWrap(True)
        aide(self.l_bandeau, 'ohp_bandeau_aide')
        h.addWidget(self.l_bandeau)
        h.addWidget(bouton('ohp_nouv_telecharger', self.telecharger_nouveautes))
        h.addWidget(bouton('ohp_nouv_voir', self.voir_nouveautes))
        h.addWidget(bouton('ohp_nouv_plus_tard', lambda: self.bandeau.setVisible(False)))
        return w

    def verifier_nouveautes(self, forcer=False):
        """Compare l'inventaire TAP frais à la copie locale (fil de fond) ; bandeau si quelque chose est nouveau."""
        if self.occupe() or getattr(self, '_t_nouv', None) is not None and self._t_nouv.isRunning():
            return
        from .inventaire import verifier_nouveautes
        dest = os.path.abspath(os.path.expanduser(self.dest.text().strip())) if hasattr(self, 'dest') else ''
        if forcer:
            self.window().statusBar().showMessage(tr('ohp_nouv_verification'), 5000)
        self._t_nouv = Tache(verifier_nouveautes, dest, forcer, parent=self)
        self._t_nouv.quand_fini(lambda n, f=forcer: self._nouveautes_pretes(n, f))
        self._t_nouv.quand_erreur(lambda e, f=forcer: f and self.window().statusBar().showMessage(tr('ohp_nouv_hors_ligne'), 8000))
        self._t_nouv.start()

    def _nouveautes_pretes(self, n, forcer):
        if n is None:
            if forcer:
                self.window().statusBar().showMessage(tr('ohp_nouv_hors_ligne'), 8000)
            return
        inv = n.pop('inv', None)
        if inv is not None:
            self._inventaire_pret(inv)
        self._nouveautes = n
        dest = self.dest.text().strip() if hasattr(self, 'dest') else ''
        if not n['copie']:
            if forcer:
                self.window().statusBar().showMessage(tr('ohp_nouv_sans_copie', dest=dest), 8000)
            self.bandeau.setVisible(False)
            return
        if not n['images']:
            if forcer:
                self.window().statusBar().showMessage(tr('ohp_nouv_aucune', depuis=n['depuis'] or '?'), 8000)
            self.bandeau.setVisible(False)
            return
        self.l_bandeau.setText(tr('ohp_bandeau_nouveautes', n=len(n['images']), objets=len(n['objets']),
                                  taille=_taille(n['octets']), depuis=n['depuis'] or '?'))
        self.bandeau.setVisible(True)
        self.window().statusBar().showMessage(tr('ohp_nouv_statut', n=len(n['images']), taille=_taille(n['octets'])), 15000)

    def voir_nouveautes(self):
        self.onglets.setCurrentIndex(0)
        self.f_nouveaux.setChecked(True)

    def telecharger_nouveautes(self):
        n = self._nouveautes
        if not n or not n['images']:
            return
        self.bandeau.setVisible(False)
        self.selection = list(n['images'])
        self.l_sel.setText(tr('ohp_selection_courante', n=len(self.selection),
                              objets=', '.join(cibles.nom_affiche(o) for o in n['objets'])[:300]))
        self.onglets.setCurrentIndex(1)
        self.lancer(confirmer=True, apres_succes='nouveautes')

    # ================================================================ catalogue
    def _onglet_catalogue(self):
        w = QWidget()
        v = QVBoxLayout(w)
        h = Flux()                                 # filtres : passent à la ligne sur un écran étroit
        self.recherche = champ('ohp_recherche_aide', '', 'ohp_recherche_indice')
        self.recherche.textChanged.connect(self._filtrer_objets)
        self.recherche.setMinimumWidth(self.recherche.fontMetrics().horizontalAdvance('M' * 18))
        h.addWidget(self.recherche)
        self.f_cat = liste('ohp_f_cat_aide', [(tr('ohp_tous_types'), '')] +
                           [(tr('ohp_cat_' + c), c) for c in cibles.CATEGORIES])
        self.f_cat.currentIndexChanged.connect(self._filtrer_objets)
        h.addWidget(self.f_cat)
        self.f_tel = liste('ohp_f_tel_aide', [(tr('ohp_tous_tel'), ''), ('T120', 'T120'), ('IRIS', 'IRIS')])
        self.f_tel.currentIndexChanged.connect(self._filtrer_objets)
        h.addWidget(self.f_tel)
        self.f_nouveaux = case('ohp_f_nouveaux')
        self.f_nouveaux.toggled.connect(self._filtrer_objets)
        h.addWidget(self.f_nouveaux)
        self.f_verifier = case('ohp_f_verifier')
        self.f_verifier.toggled.connect(self._filtrer_objets)
        h.addWidget(self.f_verifier)
        self.b_rafraichir = bouton('ohp_rafraichir', lambda: self.charger(True))
        h.addWidget(self.b_rafraichir)
        v.addLayout(h)
        self.l_inventaire = QLabel(tr('ohp_chargement'))
        self.l_inventaire.setWordWrap(True)
        v.addWidget(self.l_inventaire)
        sp = QSplitter(Qt.Orientation.Horizontal)
        self.m_obj = ModeleTableau([tr('ohp_col_type'), tr('ohp_col_objet'), tr('ohp_col_remarque'), tr('ohp_col_images'),
                                    tr('ohp_col_volume'), tr('ohp_col_nuits'), tr('ohp_col_telescopes'),
                                    tr('ohp_col_filtres'), tr('ohp_col_etat')])
        self.v_obj, self.p_obj = vue_tableau(self.m_obj, 'ohp_table_objets_aide')
        self.v_obj.selectionModel().selectionChanged.connect(self._objets_choisis)
        sp.addWidget(self.v_obj)
        droite = QWidget()
        vd = QVBoxLayout(droite)
        vd.setContentsMargins(0, 0, 0, 0)
        hf = Flux()
        self.f_nuit = liste('ohp_f_nuit_aide', [(tr('ohp_toutes_nuits'), '')])
        self.f_nuit.currentIndexChanged.connect(self._remplir_images)
        self.f_filtre = liste('ohp_f_filtre_aide', [(tr('ohp_tous_filtres'), '')])
        self.f_filtre.currentIndexChanged.connect(self._remplir_images)
        self.f_dates = case('ohp_f_dates')
        self.f_dates.toggled.connect(self._remplir_images)
        hf.addWidget(self.f_nuit)
        hf.addWidget(self.f_filtre)
        hf.addWidget(self.f_dates)
        vd.addLayout(hf)
        self.m_img = ModeleTableau([tr('ohp_col_date'), tr('ohp_col_heure_site'), tr('ohp_col_nuit'), tr('ohp_col_tel'),
                                    tr('ohp_col_filtre'),
                                    tr('ohp_col_pose'), tr('ohp_col_drapeaux'), tr('ohp_col_noms')])
        self.v_img, self.p_img = vue_tableau(self.m_img, 'ohp_table_images_aide')
        vd.addWidget(self.v_img)
        sp.addWidget(droite)
        sp.setSizes([560, 620])
        v.addWidget(sp, 1)
        self.l_estimation = QLabel(tr('ohp_aucune_selection'))
        self.l_estimation.setWordWrap(True)
        v.addWidget(self.l_estimation)
        h = Flux()                                 # boutons : passent à la ligne sur un écran étroit
        h.addWidget(bouton('ohp_corriger', self.corriger))
        h.addWidget(bouton('ohp_voir_fiche', lambda: self.onglets.setCurrentIndex(self.onglet_fiche)))
        self.b_vers_traitement = bouton('ohp_vers_traitement', self.vers_traitement)
        h.addWidget(self.b_vers_traitement)
        v.addLayout(h)
        return w

    def charger(self, rafraichir):
        if self.occupe():
            return
        from .inventaire import Inventaire
        self.b_rafraichir.setEnabled(False)
        self.l_inventaire.setText(tr('ohp_interrogation_tap') if rafraichir else tr('ohp_chargement'))
        self._t_inv = Tache(Inventaire.charger, rafraichir, parent=self)
        self._t_inv.quand_fini(self._inventaire_pret)
        self._t_inv.quand_erreur(self._inventaire_erreur)
        self._t_inv.start()

    def _inventaire_erreur(self, e):
        self.b_rafraichir.setEnabled(True)
        self.l_inventaire.setText(tr('ohp_inventaire_erreur', erreur=e))

    def _inventaire_pret(self, inv):
        self.inv = inv
        self.b_rafraichir.setEnabled(True)
        m = inv.meta
        n = inv.nouveautes or {}
        texte = tr('ohp_inventaire_resume', n=len(inv.images), objets=len(inv.objets()),
                   doublons=sum(1 for x in inv.images if x['doublon']),
                   taille=_taille(sum(x['access_estsize'] * 1024 for x in inv.images)),
                   nuits=len({str(x['nuit']) for x in inv.images}), date=m.get('date', '?')[:16],
                   source=m.get('source', '?')).replace('\n', ' — ')
        if n and not n.get('premiere') and (n.get('images') or n.get('noms')):
            texte += ' — ' + tr('ohp_nouveautes', images=len(n['images']), noms=len(n['noms']),
                                depuis=n.get('depuis') or '?').rstrip(' :')
        self.l_inventaire.setText(texte)
        self._remplir_objets()
        self._remplir_anomalies()
        self._remplir_ciel()
        if not getattr(self, '_nouveautes_verifiees', False) and hasattr(self, 'dest'):
            self._nouveautes_verifiees = True        # une fois par lancement, si le réglage le demande (délai respecté)
            if config.reglages()['ohp_verifier_nouveautes'] and not os.environ.get('COUPOLE_SANS_RESEAU'):
                self.verifier_nouveautes(False)

    def _remplir_objets(self):
        if not self.inv:
            return
        lignes, donnees, bulles = [], [], []
        for o in self.inv.objets():
            etat = []
            if o['nouveau']:
                etat.append(tr('ohp_etat_nouveau', date=o['vu_le']))
            if o['a_verifier']:
                etat.append(tr('ohp_etat_verifier'))
            lignes.append((tr('ohp_cat_' + o['cat']), cibles.nom_affiche(o['objet']), cibles.remarque(o['rem']),
                           o['images'], _taille(o['octets']), len(o['nuits']), ', '.join(sorted(o['tel'])),
                           ', '.join(sorted(o['filtres'])), ', '.join(etat)))
            donnees.append(o)
            bulles.append(tr('ohp_bulle_objet', noms=', '.join(sorted(o['noms'])), doublons=o['doublons']))
        self.m_obj.remplir(lignes, donnees, bulles)
        self.v_obj.resizeColumnsToContents()
        self._filtrer_objets()

    def _filtrer_objets(self):
        q = self.recherche.text().strip().lower()
        cat, tel = self.f_cat.currentData(), self.f_tel.currentData()
        for r, o in enumerate(self.m_obj.donnees):
            ok = (not cat or o['cat'] == cat) and (not tel or tel in o['tel']) and \
                 (not self.f_nouveaux.isChecked() or o['nouveau']) and \
                 (not self.f_verifier.isChecked() or o['a_verifier'])
            if ok and q:
                ok = q in o['objet'].lower() or q in cibles.nom_affiche(o['objet']).lower() or \
                     any(q in n.lower() for n in o['noms'])
            src = self.m_obj.index(r, 0)
            row = self.p_obj.mapFromSource(src).row()
            if row >= 0:
                self.v_obj.setRowHidden(row, not ok)

    def _objets_choisis(self, *_):
        objs = {o['objet'] for o in lignes_choisies(self.v_obj, self.p_obj, self.m_obj)}
        self._objets = objs
        imgs = [x for x in (self.inv.images if self.inv else []) if x['objet'] in objs]
        for combo, cle, tous in ((self.f_nuit, 'nuit', 'ohp_toutes_nuits'), (self.f_filtre, 'filter_name',
                                                                            'ohp_tous_filtres')):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(tr(tous), '')
            for val in sorted({str(x[cle]) for x in imgs}):
                combo.addItem(val, val)
            combo.blockSignals(False)
        self._remplir_images()
        self._maj_fiche()

    def _maj_fiche(self, *_):
        """Fiche en ligne : seulement quand l'onglet est affiché, et pour un seul objet choisi."""
        if not hasattr(self, 'fiche') or self.onglets.currentIndex() != self.onglet_fiche:
            return
        objs = lignes_choisies(self.v_obj, self.p_obj, self.m_obj)
        if len(objs) != 1:
            self.fiche.demander(None)
            return
        o = objs[0]
        if self.fiche._demande and self.fiche._demande[0] == o['objet'] and self.fiche.resultat() is not None:
            return                                  # déjà affichée : pas de nouvelle requête
        self.fiche.demander(o['objet'], o['cat'], o.get('sbdb'), sorted(o.get('noms') or ()))

    def _images_filtrees(self):
        objs = getattr(self, '_objets', set())
        nuit, filtre = self.f_nuit.currentData(), self.f_filtre.currentData()
        out = []
        for x in (self.inv.images if self.inv else []):
            if x['objet'] not in objs:
                continue
            if nuit and str(x['nuit']) != nuit:
                continue
            if filtre and x['filter_name'] != filtre:
                continue
            if self.f_dates.isChecked() and (x['date_partagee'] or x['diurne']) and not x['doublon']:
                continue
            out.append(x)
        return out

    def _remplir_images(self, *_):
        from ...core.astro import utc
        from ...core import sites as sites_mod, temps
        imgs = sorted(self._images_filtrees(), key=lambda x: (x['t_min'], x['access_url']))
        sites_par_id = {s.id: s for s in sites_mod.sites()}
        lignes, bulles = [], []
        for x in imgs:
            dr = []
            if x['doublon']:
                dr.append(tr('ohp_drapeau_doublon'))
            if x['date_partagee']:
                dr.append(tr('ohp_drapeau_date'))
            if x['diurne']:
                dr.append(tr('ohp_drapeau_diurne'))
            if x['nouveau']:
                dr.append(tr('ohp_etat_nouveau', date=x['vu_le']))
            u = temps.mjd_vers_utc(x['t_min'])
            s_ = sites_par_id.get(x.get('site'))
            loc = temps.heure_locale(u, s_).strftime('%H:%M:%S (UTC%z)') if s_ else ''
            lignes.append((u.strftime('%Y-%m-%d %H:%M:%S'), loc, str(x['nuit']), x['tel'], x['filter_name'],
                           x['t_exptime'], ', '.join(dr), x['target_name']))
            bulles.append(temps.formater(u, s_) + '\n' + x['access_url'])
        self.m_img.remplir(lignes, imgs, bulles)
        self.v_img.resizeColumnsToContents()
        self.selection = imgs
        self._estimer()

    def _estimer(self):
        from ...core.machine import disque_libre_go
        from .selection import estimer
        if not self.selection:
            self.l_estimation.setText(tr('ohp_aucune_selection'))
            return
        fmt = self.format.currentData() if hasattr(self, 'format') else 'xisf'
        e = estimer(self.selection, fmt)
        dest = self.dest.text() if hasattr(self, 'dest') else ''
        self.l_estimation.setText(tr('ohp_estimation', images=e['images'], objets=e['objets'], nuits=e['nuits'],
                                     doublons=e['doublons'], fits=_taille(e['octets_fits']),
                                     sortie=_taille(e['octets_sortie']), format=fmt.upper()) + '  ' +
                                  tr('ohp_libre', libre=_taille(disque_libre_go(dest or '.') * 1e9)))

    def vers_traitement(self):
        if not self.selection:
            QMessageBox.information(self, tr('ohp_onglet_traitement'), tr('ohp_aucune_selection'))
            return
        self.l_sel.setText(tr('ohp_selection_courante', n=len([x for x in self.selection if not x['doublon']]),
                              objets=', '.join(sorted({cibles.nom_affiche(x['objet']) for x in self.selection}))[:300]))
        self.onglets.setCurrentIndex(1)

    def corriger(self):
        objs = lignes_choisies(self.v_obj, self.p_obj, self.m_obj)
        if len(objs) != 1:
            QMessageBox.information(self, tr('ohp_corriger'), tr('ohp_corriger_un'))
            return
        d = DialogueCorrection(objs[0], self.inv, self)
        if d.exec():
            self.charger(False)

    # ================================================================ traitement
    def _onglet_traitement(self):
        r = config.reglages()
        w = QWidget()
        v = QVBoxLayout(w)
        self.l_sel = QLabel(tr('ohp_aucune_selection'))
        self.l_sel.setWordWrap(True)
        v.addWidget(self.l_sel)
        g = QGroupBox(tr('ohp_groupe_sortie'))
        f = QFormLayout(g)
        h = QHBoxLayout()
        self.dest = champ('ohp_dest_aide', r['dossier_sortie'] or str(config.dossier_sortie_defaut() / 'OHP_DU_ECU'))
        h.addWidget(self.dest, 1)
        h.addWidget(bouton('reg_parcourir', self._parcourir))
        f.addRow(tr('reg_dest'), h)
        self.format = liste('reg_format_aide', [(tr('fmt_xisf'), 'xisf'), (tr('fmt_fz'), 'fz'), (tr('fmt_fits'), 'fits')])
        self.format.setCurrentIndex(max(0, self.format.findData(r['format_sortie'])))
        self.format.currentIndexChanged.connect(self._estimer)
        f.addRow(tr('reg_format'), self.format)
        noms = r['langue_noms'] if r['langue_noms'] in ('fr', 'en') else i18n.langue()
        self.noms = liste('reg_noms_aide', [('Français', 'fr'), ('English', 'en')])
        self.noms.setCurrentIndex(max(0, self.noms.findData(noms)))
        f.addRow(tr('reg_noms'), self.noms)
        self.garder_doublons = case('ohp_garder_doublons')
        self.garder_fits = case('ohp_garder_fits')
        f.addRow('', self.garder_doublons)
        f.addRow('', self.garder_fits)
        self.qualite = case('ohp_qualite')
        f.addRow('', self.qualite)
        v.addWidget(g)
        g = QGroupBox(tr('ohp_groupe_astrometrie'))
        vg = QVBoxLayout(g)                        # texte au-dessus, réglages dessous : tient sur un écran étroit
        self.l_astap = QLabel()
        self.l_astap.setWordWrap(True)
        vg.addWidget(self.l_astap)
        hg = Flux()
        vg.addLayout(hg)
        self.mode_astap = liste('ohp_mode_astap_aide', [(tr('ohp_astap_tous'), 'tous'),
                                                        (tr('ohp_astap_suspectes'), 'suspectes'),
                                                        (tr('ohp_astap_jamais'), 'jamais')])
        hg.addWidget(self.mode_astap)
        hg.addWidget(bouton('ohp_assistant_astap', self._astap))
        v.addWidget(g)
        g = QGroupBox(tr('ohp_groupe_machine'))
        gl = QGridLayout(g)
        self.l_plan = QLabel()
        self.l_plan.setWordWrap(True)
        gl.addWidget(self.l_plan, 0, 0, 1, 6)
        self.n_dl = nombre('reg_dl_aide', 0, 4, int(r['telechargements_max'] or 0), 'reg_auto')
        self.n_conv = nombre('reg_conv_aide', 0, 16, int(r['conversions_max'] or 0), 'reg_auto')
        self.debit = decimal('reg_debit_aide', 0.5, 20.0, float(r['debit_max_mo_s'] or 8.0), 'unite_mos')
        self.eco = case('reg_econome', bool(r['mode_econome']))
        flux = Flux()                              # paires « libellé + réglage » qui passent à la ligne
        for cle, wid in (('reg_dl', self.n_dl), ('reg_conv', self.n_conv), ('reg_debit', self.debit)):
            paire = QWidget()
            hp = QHBoxLayout(paire)
            hp.setContentsMargins(0, 0, 12, 0)
            hp.addWidget(QLabel(tr(cle)))
            hp.addWidget(wid)
            flux.addWidget(paire)
        gl.addLayout(flux, 1, 0, 1, 6)
        gl.addWidget(self.eco, 2, 0, 1, 3)
        for wid in (self.n_dl, self.n_conv, self.eco):
            (wid.valueChanged if hasattr(wid, 'valueChanged') else wid.toggled).connect(self._maj_plan)
        v.addWidget(g)
        h = Flux()
        self.b_lancer = bouton('ohp_lancer', self.lancer)
        self.b_tout = bouton('ohp_tout', self.tout_telecharger)
        self.b_pause = bouton('ohp_pause', self.basculer_pause)
        self.b_pause.setEnabled(False)
        self.b_arreter = bouton('ohp_arreter', self.arreter_traitement)
        self.b_arreter.setEnabled(False)
        h.addWidget(self.b_lancer)
        h.addWidget(self.b_tout)
        h.addWidget(self.b_pause)
        h.addWidget(self.b_arreter)
        h.addWidget(bouton('ohp_ouvrir_journal', self.ouvrir_journal))
        h.addWidget(bouton('ohp_reorganiser', self.reorganiser))
        h.addWidget(bouton('ohp_nouv_verifier', lambda: self.verifier_nouveautes(True)))
        v.addLayout(h)
        self.barre = aide(QProgressBar(), 'ohp_barre_aide')
        v.addWidget(self.barre)
        self.l_stats = QLabel('')
        v.addWidget(self.l_stats)
        self.journal = aide(QPlainTextEdit(), 'ohp_journal_aide')
        self.journal.setReadOnly(True)
        self.journal.setMaximumBlockCount(5000)
        v.addWidget(self.journal, 1)
        self.reglages_changes()
        return w

    def _parcourir(self):
        d = QFileDialog.getExistingDirectory(self, tr('reg_dest'), self.dest.text())
        if d:
            self.dest.setText(d)
            self._estimer()
            self._remplir_lots()

    def _astap(self):
        DialogueASTAP(self).exec()
        self.reglages_changes()

    def reglages_changes(self):
        """Détection d'ASTAP (sous-processus) et sondes de la machine : hors du fil graphique."""
        from ...core import astap, machine
        r = config.reglages()
        self.l_astap.setText(tr('astapdlg_recherche'))

        def sonder():
            return machine.detecter(), astap.detecter(r['astap_executable'], r['astap_catalogue'])
        self._t_astap = Tache(sonder, parent=self)
        self._t_astap.quand_fini(self._sondes_pretes)
        self._t_astap.start()

    def _sondes_pretes(self, resultat):
        self._machine, self._etat_astap = resultat
        e = self._etat_astap
        if e.utilisable:
            self.l_astap.setText(tr('ohp_avec_astap', exe=coupable(e.executable), cat=e.catalogue.upper()))
        else:
            self.l_astap.setText(tr(e.message_cle()) + ' ' + tr('astap_sans_effet'))
        self.mode_astap.setEnabled(e.utilisable)
        self._maj_plan()

    def _plan(self):
        from ...core import machine, parallele
        m = getattr(self, '_machine', None) or machine.detecter()   # détection déjà faite en fond (cache)
        return m, parallele.planifier(m, self.n_dl.value(), self.n_conv.value(), True if self.eco.isChecked() else None)

    def _maj_plan(self, *_):
        if getattr(self, '_machine', None) is None:
            return                                   # les sondes ne sont pas encore revenues
        m, p = self._plan()
        self.l_plan.setText(tr('ohp_machine', cpu=m.coeurs_physiques, log=m.coeurs_logiques,
                               ram='%.1f' % (m.memoire_disponible_mo / 1024), dl=p.telechargements,
                               conv=p.conversions, raison=tr(p.raison)))

    def occupe(self):
        return self._fil is not None and self._fil.is_alive()

    # ---------------------------------------------------------------- tout télécharger, journal, réorganiser
    def _choisir_dest_si_besoin(self) -> str | None:
        """Premier « Tout télécharger » (ou dossier non défini) : dialogue natif, défaut sensé selon le système."""
        from .pilote import dossier_sortie_propose
        r = config.reglages()
        actuel = self.dest.text().strip()
        if r['dossier_sortie'] and actuel:
            return os.path.abspath(os.path.expanduser(actuel))
        propose = actuel or dossier_sortie_propose()
        QMessageBox.information(self, tr('ohp_choisir_dest_titre'), tr('ohp_choisir_dest_texte', dest=propose))
        d = QFileDialog.getExistingDirectory(self, tr('ohp_choisir_dest_titre'), os.path.dirname(propose) or propose)
        if not d:
            return None
        if os.path.basename(d) != 'OHP_DU_ECU' and not os.path.exists(os.path.join(d, '_traitement')):
            d = os.path.join(d, 'OHP_DU_ECU')
        self.dest.setText(d)
        return os.path.abspath(d)

    def tout_telecharger(self):
        """Toute la banque : estimation (volume, temps au débit plafond, place libre), confirmation, puis traitement."""
        if self.occupe() or not self.inv:
            return
        dest = self._choisir_dest_si_besoin()
        if not dest:
            return
        self.selection = list(self.inv.images)
        self._mode_tout = True
        self.l_sel.setText(tr('ohp_selection_courante', n=len([x for x in self.selection if not x['doublon']]),
                              objets=tr('ohp_tous_types')))
        self.lancer(confirmer=True)

    def _estimation_tout(self, est, fmt, plan):
        from .pilote import estimation_temps
        debit = self.debit.value()
        return tr('ohp_estimation_tout', images=est['images'], objets=est['objets'], fits=_taille(est['octets_fits']),
                  sortie=_taille(est['octets_sortie']), format=fmt.upper(), debit='%.1f' % debit,
                  temps=duree_lisible(estimation_temps(est['octets_fits'], debit * 1e6)))

    def ouvrir_journal(self):
        p = os.path.join(self.dest.text().strip(), '_traitement', 'JOURNAL.txt')
        if os.path.exists(p):
            ouvrir_fichier(p)
        else:
            QMessageBox.information(self, tr('ohp_ouvrir_journal'), tr('ohp_journal_absent', dest=self.dest.text()))

    def reorganiser(self):
        """Range des fichiers déjà convertis (ailleurs, ancien rangement) dans l'arborescence des lots."""
        if self.occupe() or not self.inv:
            return
        src = QFileDialog.getExistingDirectory(self, tr('ohp_reorganiser_titre'), self.dest.text())
        if not src:
            return
        dest = os.path.abspath(os.path.expanduser(self.dest.text().strip()))
        from .pilote import Traitement
        from ...core.parallele import Plan
        inv = self.inv
        fmt, L = self.format.currentData(), self.noms.currentData()

        def travail():
            t = Traitement(dest, inv, Plan(1, 1, True, ''), {'format': fmt, 'langue': L})
            try:
                return t.reorganiser(src)
            finally:
                t.fermer()
        self.b_lancer.setEnabled(False)
        self._t_reorg = Tache(travail, parent=self)
        self._t_reorg.quand_fini(lambda r: (self.b_lancer.setEnabled(True), self._remplir_lots(),
                                            self._log(tr('ohp_reorganise_fait', n=r['ranges'], lots=r['lots'],
                                                         ignores=len(r['ignores'])))))
        self._t_reorg.quand_erreur(lambda e: (self.b_lancer.setEnabled(True),
                                              QMessageBox.warning(self, tr('ohp_reorganiser'), e)))
        self._t_reorg.start()

    def basculer_pause(self):
        if self.pause is None:
            return
        if self.pause.is_set():
            self.pause.clear()
            self.b_pause.setText(tr('ohp_pause'))
        else:
            self.pause.set()
            self.b_pause.setText(tr('ohp_reprendre'))

    def lancer(self, confirmer=False, apres_succes=None):
        from .pilote import Traitement
        from .selection import estimer, place_necessaire
        from ...core.machine import disque_libre_go
        if self.occupe():
            return
        sel = list(self.selection)
        if not sel:
            QMessageBox.information(self, tr('ohp_onglet_traitement'), tr('ohp_aucune_selection'))
            return
        dest = os.path.abspath(os.path.expanduser(self.dest.text().strip()))
        fmt = self.format.currentData()
        m, plan = self._plan()
        est = estimer(sel, fmt)
        besoin = place_necessaire(est, plan.conversions, plan.telechargements)
        libre = disque_libre_go(dest) * 1e9
        if libre < besoin:
            QMessageBox.warning(self, tr('ohp_onglet_traitement'),
                                tr('ohp_place_manque', besoin=_taille(besoin), libre=_taille(libre), dest=dest))
            return
        if confirmer or self._mode_tout:
            texte = tr('ohp_tout_question', estimation=self._estimation_tout(est, fmt, plan), dest=dest,
                       place=tr('ohp_place', besoin=_taille(besoin), libre=_taille(libre), dest=dest))
            if QMessageBox.question(self, tr('ohp_tout_titre'), texte) != QMessageBox.StandardButton.Yes:
                self._mode_tout = False
                return
        elif est['octets_fits'] > 5e9 and QMessageBox.question(
                self, tr('ohp_onglet_traitement'), tr('ohp_confirmer_gros_gui', taille=_taille(est['octets_fits']))) \
                != QMessageBox.StandardButton.Yes:
            return
        self._mode_tout = False
        self._apres_succes = apres_succes
        r = config.reglages()
        r['dossier_sortie'] = dest
        r['format_sortie'] = fmt
        e_astap = self._etat_astap
        etat = e_astap if (e_astap is not None and e_astap.utilisable and self.mode_astap.currentData() != 'jamais') else None
        self.arret = enregistrer_arret(threading.Event())
        self.pause = threading.Event()
        self.b_pause.setText(tr('ohp_pause'))
        self.journal.clear()
        self.barre.setValue(0)
        self._octets, self._t0, self._total = 0, time.time(), 0
        self._evts = FileEvenements(self, self._evenements)
        opts = {'format': fmt, 'langue': self.noms.currentData(), 'astap': etat,
                'mode_astap': self.mode_astap.currentData(), 'debit_octets_s': self.debit.value() * 1e6,
                'garder_fits': self.garder_fits.isChecked(), 'garder_doublons': self.garder_doublons.isChecked()}
        self._log(tr('ohp_journal_debut', n=est['images'], dest=dest, format=fmt.upper()))
        if etat is None:
            self._log(tr('ohp_sans_astap') if not (e_astap and e_astap.utilisable) else tr('ohp_astap_desactive'))
        evts, arret, pause, inv = self._evts, self.arret, self.pause, self.inv

        def travail():
            t = None
            try:
                t = Traitement(dest, inv, plan, opts, rapporter=evts, arret=arret, pause=pause)
                t.lancer(sel)
            except OSError as e:                     # dossier non inscriptible, disque plein, dossier retiré
                evts({'type': 'erreur', 'erreur': str(e)})
            except Exception as e:
                import traceback
                from ...core import rapports
                rapports.signaler_plantage(traceback.format_exc(), contexte='traitement')
                evts({'type': 'erreur', 'erreur': '%s: %s' % (type(e).__name__, e)})
            finally:
                if t is not None:
                    t.fermer()
                evts({'type': 'termine'})
        self.b_lancer.setEnabled(False)
        self.b_tout.setEnabled(False)
        self.b_pause.setEnabled(True)
        self.b_arreter.setEnabled(True)
        self._fil = lancer_fil(travail)

    def _verifier_qualite(self):
        """Contrôle de qualité demandé explicitement (case cochée) : lots du dossier de sortie, en fond."""
        try:
            from ..qualite import mesures, rapport
        except ImportError:                      # module Qualité retiré : rien à faire
            return
        if not mesures.disponible():
            self._log(tr('qual_absent'))
            return
        dest = self.dest.text()
        q = FileEvenements(self, lambda evs: [self._log(e) for e in evs])
        self._evts_qualite = q

        def travail():
            n = 0
            lots = rapport.fichiers(dest)
            for d, imgs in lots.items():
                lignes = rapport.analyser_lot(imgs)
                rapport.ecrire(d, lignes)
                n += len(lignes)
                q(tr('qual_lot', lot=os.path.relpath(d, dest), n=len(lignes)) + ' — ' +
                  rapport.resume(lignes, i18n.langue())[1 if len(lignes) else 0])
            q(tr('qual_fini', n=n, lots=len(lots)))
        lancer_fil(travail)

    def arreter_traitement(self):
        if self.arret is not None:
            self.arret.set()
            if self.pause is not None:
                self.pause.clear()
            self._log(tr('ohp_arret_demande'))
            self.b_arreter.setEnabled(False)
            self.b_pause.setEnabled(False)

    def arreter(self):
        """Fermeture : lève l'arrêt, débloque une pause, attend le fil du traitement (processus terminés par lui)."""
        if self.arret is not None:
            self.arret.set()
        if self.pause is not None:
            self.pause.clear()
        if self._fil is not None and self._fil.is_alive():
            self._fil.join(15)
        if getattr(self, '_evts', None) is not None:
            self._evts.arreter()

    def _log(self, texte):
        self.journal.appendPlainText(texte)

    def _evenements(self, evs):
        for ev in evs:
            t = ev['type']
            if t == 'octets':
                self._octets += ev['n']
            elif t == 'debut':
                self._total = ev['total']
                self.barre.setMaximum(max(1, ev['total']))
                self._log(tr('ohp_debut', total=ev['total'], deja=ev['deja']))
            elif t == 'image':
                self.barre.setValue(ev['n'])
                self._log(tr('ohp_ligne_image', n=ev['n'], total=ev['total'], statut=tr('ohp_statut_' + ev['statut']),
                             wcs=tr('ohp_wcs_' + (ev.get('wcs') or 'aucune')), source=(ev.get('source') or '')[:60],
                             debit='%.1f' % (self._octets / max(1e-6, time.time() - self._t0) / 1e6)))
                reste = (ev['total'] - ev['n']) * ev['ecoule'] / max(1, ev['n'])
                self.l_stats.setText(tr('ohp_stats', debit='%.1f' % (self._octets / max(1e-6, time.time() - self._t0) / 1e6),
                                        reste='%.0f' % (reste / 60)))
            elif t == 'echec':
                self._log(tr('ohp_ligne_echec', source=ev['source'], erreur=ev['erreur']))
            elif t == 'avis':
                self._log(tr(ev['cle'], valeur=ev['valeur']))
            elif t == 'pause':
                self._log(tr('ohp_pause_journal' if ev['actif'] else 'ohp_reprise_journal'))
            elif t == 'erreur':
                self._log(tr('ohp_erreur_traitement', erreur=ev['erreur']))
            elif t == 'fin':
                b = ev['bilan']
                of, ox = b['octets_fits'], b['octets_sortie']
                self._log(tr('ohp_bilan', ok=b['statuts'].get('ok', 0), doublons=b['statuts'].get('doublon', 0),
                             echecs=b['statuts'].get('echec', 0), fits=_taille(of), sortie=_taille(ox),
                             ratio='%.1f' % (100 * ox / of if of else 0), lots=b.get('lots', '?'),
                             dest=self.dest.text()))
                c = b.get('compte', {})
                self._log(tr('ohp_rapport_fin', images=b.get('images', 0), duree=duree_lisible(b.get('duree', 0)),
                             ok=c.get('ok', 0), doublons=c.get('doublon', 0), echecs=c.get('echec', 0),
                             sortie=_taille(ox), lots=b.get('lots', 0),
                             journal=os.path.join(self.dest.text(), '_traitement', 'JOURNAL.txt')))
                if b.get('echecs'):
                    self._log(tr('ohp_rapport_echecs', liste='; '.join(
                        '%s (%s)' % (e['source'].rsplit('/', 1)[-1], e['erreur'][:60]) for e in b['echecs'][:10])))
                if b.get('annule'):
                    self._log(tr('interrompu_reprise'))
                elif not c.get('echec') and getattr(self, '_apres_succes', None) == 'nouveautes':
                    from .inventaire import marquer_reference
                    marquer_reference()
                    self._nouveautes = None
            elif t == 'termine':
                self.b_lancer.setEnabled(True)
                self.b_tout.setEnabled(True)
                self.b_pause.setEnabled(False)
                self.b_arreter.setEnabled(False)
                self._evts.arreter()
                self._remplir_lots()
                self._remplir_anomalies()
                if self.qualite.isChecked() and not (self.arret and self.arret.is_set()):
                    self._verifier_qualite()

    # ================================================================ lots
    def _onglet_lots(self):
        w = QWidget()
        v = QVBoxLayout(w)
        h = Flux()                                 # rangée souple (écrans étroits)
        h.addWidget(bouton('ohp_lots_actualiser', self._remplir_lots))
        h.addWidget(bouton('ohp_lots_ouvrir', self._ouvrir_lot))
        h.addWidget(bouton('ohp_lots_dossier', lambda: ouvrir_fichier(self.dest.text())))
        v.addLayout(h)
        self.l_lots = QLabel('')
        self.l_lots.setWordWrap(True)
        v.addWidget(self.l_lots)
        self.m_lots = ModeleTableau([tr('csv_dossier'), tr('csv_objet'), tr('csv_filtre'), tr('csv_poses'),
                                     tr('csv_pose_totale_s'), tr('csv_nuits'), tr('csv_alignement')])
        self.v_lots, self.p_lots = vue_tableau(self.m_lots, 'ohp_table_lots_aide')
        self.v_lots.doubleClicked.connect(lambda *_: self._ouvrir_lot())
        v.addWidget(self.v_lots, 1)
        return w

    def _remplir_lots(self):
        chemin = os.path.join(self.dest.text(), 'INDEX_LOTS.csv')
        lignes, donnees = [], []
        if os.path.exists(chemin):
            with open(chemin, encoding='utf-8-sig') as f:
                for i, r in enumerate(csv.reader(f, delimiter=';')):
                    if i == 0 or len(r) < 12:
                        continue
                    lignes.append((r[0], r[2], r[4], int(r[5]), float(r[6]), r[7], r[11]))
                    donnees.append(os.path.join(self.dest.text(), *r[0].split('/')))
        self.m_lots.remplir(lignes, donnees)
        self.v_lots.resizeColumnsToContents()
        self.l_lots.setText(tr('ohp_lots_resume', n=len(lignes), dest=coupable(self.dest.text())) if lignes
                            else tr('ohp_lots_aucun', dest=coupable(self.dest.text())))

    def _ouvrir_lot(self):
        ch = lignes_choisies(self.v_lots, self.p_lots, self.m_lots)
        if ch:
            p = os.path.join(ch[0], 'LOT.txt')
            ouvrir_fichier(p if os.path.exists(p) else ch[0])

    # ================================================================ anomalies
    def _onglet_anomalies(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.l_anom = QLabel(tr('ohp_anomalies_intro'))
        self.l_anom.setWordWrap(True)
        v.addWidget(self.l_anom)
        h = Flux()                                 # rangée souple (écrans étroits)
        self.f_genre = liste('ohp_f_genre_aide', [(tr('ohp_tous_genres'), '')])
        self.f_genre.currentIndexChanged.connect(self._filtrer_anomalies)
        self.f_anom_nouv = case('ohp_f_nouveaux')
        self.f_anom_nouv.toggled.connect(self._filtrer_anomalies)
        h.addWidget(self.f_genre)
        h.addWidget(self.f_anom_nouv)
        h.addWidget(bouton('ohp_anom_csv', self._exporter_anomalies))
        v.addLayout(h)
        self.m_anom = ModeleTableau([tr('anom_col_genre'), tr('anom_col_action'), tr('anom_col_objet'),
                                     tr('anom_col_nuit'), tr('anom_col_fichier'), tr('anom_col_detail'),
                                     tr('anom_col_explication')])
        self.v_anom, self.p_anom = vue_tableau(self.m_anom, 'ohp_table_anom_aide')
        v.addWidget(self.v_anom, 1)
        self._anoms = []
        return w

    def _remplir_anomalies(self):
        if not self.inv:
            return
        from . import anomalies
        from .astrometrie import attentes
        inv, dest = self.inv, self.dest.text()

        def calcul():
            med, medo = attentes(inv.images)
            a = anomalies.detecter(inv.images, medo)
            return a + anomalies.depuis_traitement(os.path.join(dest, '_traitement', 'etat.sqlite'))
        self._t_anom = Tache(calcul, parent=self)
        self._t_anom.quand_fini(self._anomalies_pretes)
        self._t_anom.start()

    def _anomalies_pretes(self, anoms):
        from . import anomalies
        self._anoms = anoms
        res = anomalies.resume(anoms)
        self.f_genre.blockSignals(True)
        self.f_genre.clear()
        self.f_genre.addItem(tr('ohp_tous_genres'), '')
        for g, n in res.items():
            self.f_genre.addItem('%s (%d)' % (tr('anom_' + g), n), g)
        self.f_genre.blockSignals(False)
        self.l_anom.setText(tr('ohp_anomalies_intro') + ' ' + tr('ohp_anomalies_total', n=len(anoms)))
        self._filtrer_anomalies()

    def _filtrer_anomalies(self, *_):
        g = self.f_genre.currentData()
        sel = [a for a in self._anoms if (not g or a['genre'] == g) and (not self.f_anom_nouv.isChecked() or a['nouveau'])]
        self.m_anom.remplir([(a['genre'], tr('anom_action_' + a['action']), cibles.nom_affiche(a['objet']), a['nuit'],
                              a['fichier'], a['detail'], tr('anom_' + a['genre'])) for a in sel], sel,
                            [a['url'] for a in sel])
        self.v_anom.resizeColumnsToContents()

    def _exporter_anomalies(self):
        from . import anomalies
        f, _ = QFileDialog.getSaveFileName(self, tr('ohp_anom_csv'), 'anomalies.csv', 'CSV (*.csv)')
        if f:
            anomalies.ecrire_csv(f, self._anoms)
            QMessageBox.information(self, tr('ohp_anom_csv'), tr('ecrit', chemin=f))

    # ================================================================ carte du ciel
    COULEURS = {'ast': '#E07B39', 'neocp': '#C9A227', 'com': '#3FB0AC', 'pla': '#D94F70', 'tno': '#8E6CC8',
                'pn': '#5DADE2', 'neb': '#E74C3C', 'amas': '#F4D03F', 'gal': '#A9CCE3', 'eto': '#FFFFFF',
                'autre': '#95A5A6'}

    def _onglet_ciel(self):
        from ...gui.cartes import CarteCiel
        w = QWidget()
        v = QVBoxLayout(w)
        h = Flux()                                 # rangée souple (écrans étroits)
        self.ciel_cat = liste('ohp_f_cat_aide', [(tr('ohp_tous_types'), '')] +
                              [(tr('ohp_cat_' + c), c) for c in cibles.CATEGORIES])
        self.ciel_cat.currentIndexChanged.connect(self._remplir_ciel)
        h.addWidget(self.ciel_cat)
        self.l_ciel = QLabel(tr('ohp_ciel_intro'))
        self.l_ciel.setWordWrap(True)
        v.addLayout(h)
        self.l_ciel.setWordWrap(True)
        v.addWidget(self.l_ciel)
        self.ciel = aide(CarteCiel(), 'ohp_ciel_aide')
        self.ciel.point_clique.connect(self._ciel_clic)
        v.addWidget(self.ciel, 1)
        return w

    def _remplir_ciel(self, *_):
        if not self.inv:
            return
        import math
        import numpy as np
        from PyQt6.QtGui import QColor
        cat = self.ciel_cat.currentData()
        groupes = {}
        for x in self.inv.images:
            if x['doublon'] or (cat and x['cat'] != cat):
                continue
            cle = x['objet'] if x['cat'] in cibles.FIXES else (x['objet'], str(x['nuit']))
            groupes.setdefault(cle, []).append(x)
        pts = []
        for cle, xs in groupes.items():
            ra = float(np.median([x['s_ra'] for x in xs]))
            de = float(np.median([x['s_dec'] for x in xs]))
            x0 = xs[0]
            r = 2.5 + 1.2 * math.sqrt(len(xs)) if x0['cat'] in cibles.FIXES else 2.5
            nom = cibles.nom_affiche(x0['objet']) + ('' if x0['cat'] in cibles.FIXES else ' — ' + str(x0['nuit']))
            pts.append((ra, de, min(r, 14), QColor(self.COULEURS.get(x0['cat'], '#95A5A6')),
                        tr('ohp_ciel_bulle', nom=nom, n=len(xs), cat=tr('ohp_cat_' + x0['cat'])), x0['objet']))
        self.ciel.definir(pts)

    def _ciel_clic(self, objet):
        for r, o in enumerate(self.m_obj.donnees):
            if o['objet'] == objet:
                idx = self.p_obj.mapFromSource(self.m_obj.index(r, 0))
                self.v_obj.selectRow(idx.row())
                self.v_obj.scrollTo(idx)
                self.onglets.setCurrentIndex(0)
                return

    # ================================================================ aide
    def aide_html(self):
        return tr('ohp_aide_html')


class DialogueCorrection(QDialog):
    """Corriger le classement d'un objet : renommer, changer de type, fusionner avec un autre objet."""

    def __init__(self, objet: dict, inv, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('ohp_corriger'))
        self.objet = objet
        f = QFormLayout(self)
        info = QLabel(tr('ohp_corriger_texte', objet=objet['objet'], noms=', '.join(sorted(objet['noms']))))
        info.setWordWrap(True)
        f.addRow(info)
        self.nom = champ('ohp_corr_nom_aide', objet['objet'])
        f.addRow(tr('ohp_corr_nom'), self.nom)
        self.cat = liste('ohp_corr_cat_aide', [(tr('ohp_cat_' + c), c) for c in cibles.CATEGORIES])
        self.cat.setCurrentIndex(max(0, self.cat.findData(objet['cat'])))
        f.addRow(tr('ohp_corr_cat'), self.cat)
        autres = sorted({x['objet'] for x in inv.images} - {objet['objet']})
        self.fusion = liste('ohp_corr_fusion_aide', [(tr('ohp_corr_pas_fusion'), '')] +
                            [(cibles.nom_affiche(o), o) for o in autres])
        f.addRow(tr('ohp_corr_fusion'), self.fusion)
        self.inv = inv
        h = QHBoxLayout()
        h.addWidget(bouton('ohp_corr_oublier', self._oublier))
        h.addStretch(1)
        h.addWidget(bouton('dlg_annuler', self.reject))
        h.addWidget(bouton('ohp_corr_enregistrer', self.accept))
        f.addRow(h)

    def _oublier(self):
        for n in self.objet['noms']:
            cibles.corriger(n, None)
        super().accept()

    def accept(self):
        cible = self.fusion.currentData()
        if cible:
            ex = next(x for x in self.inv.images if x['objet'] == cible)
            for n in self.objet['noms']:
                cibles.corriger(n, cible, ex['cat'], ex['rem'], ex['sbdb'])
        else:
            for n in self.objet['noms']:
                cibles.corriger(n, self.nom.text().strip() or self.objet['objet'], self.cat.currentData(),
                                self.objet['rem'])
        super().accept()
