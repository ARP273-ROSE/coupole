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
from PyQt6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QMessageBox, QPlainTextEdit, QProgressBar, QSplitter, QTabWidget, QVBoxLayout, QWidget)

from ...core import config, i18n
from ...core.i18n import tr
from ...gui.dialogues import DialogueASTAP, ouvrir_fichier
from ...gui.modele import ModeleTableau, lignes_choisies, vue_tableau
from ...gui.outils import FileEvenements, Tache, aide, bouton, case, champ, decimal, liste, nombre
from . import cibles


def _taille(o: float) -> str:
    return tr('taille_go', v='%.2f' % (o / 1e9)) if o >= 1e8 else tr('taille_mo', v='%.1f' % (o / 1e6))


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inv = None
        self.selection = []
        self.traitement = None
        self.arret = None
        self._fil = None
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        self.onglets = aide(QTabWidget(), 'ohp_onglets_aide')
        v.addWidget(self.onglets)
        self.onglets.addTab(self._onglet_catalogue(), tr('ohp_onglet_catalogue'))
        self.onglets.addTab(self._onglet_traitement(), tr('ohp_onglet_traitement'))
        self.onglets.addTab(self._onglet_lots(), tr('ohp_onglet_lots'))
        self.onglets.addTab(self._onglet_anomalies(), tr('ohp_onglet_anomalies'))
        self.onglets.addTab(self._onglet_ciel(), tr('ohp_onglet_ciel'))
        sc = QShortcut(QKeySequence('Ctrl+R'), self)
        sc.activated.connect(lambda: self.charger(True))
        self.charger(False)

    # ================================================================ catalogue
    def _onglet_catalogue(self):
        w = QWidget()
        v = QVBoxLayout(w)
        h = QHBoxLayout()
        self.recherche = champ('ohp_recherche_aide', '', 'ohp_recherche_indice')
        self.recherche.textChanged.connect(self._filtrer_objets)
        h.addWidget(self.recherche, 2)
        self.f_cat = liste('ohp_f_cat_aide', [(tr('ohp_tous_types'), '')] +
                           [(tr('ohp_cat_' + c), c) for c in cibles.CATEGORIES])
        self.f_cat.currentIndexChanged.connect(self._filtrer_objets)
        h.addWidget(self.f_cat, 1)
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
        hf = QHBoxLayout()
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
        h = QHBoxLayout()
        self.l_estimation = QLabel(tr('ohp_aucune_selection'))
        self.l_estimation.setWordWrap(True)
        h.addWidget(self.l_estimation, 1)
        h.addWidget(bouton('ohp_corriger', self.corriger))
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
        self._t_inv.fini.connect(self._inventaire_pret)
        self._t_inv.erreur.connect(self._inventaire_erreur)
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
        v.addWidget(g)
        g = QGroupBox(tr('ohp_groupe_astrometrie'))
        hg = QHBoxLayout(g)
        self.l_astap = QLabel()
        self.l_astap.setWordWrap(True)
        hg.addWidget(self.l_astap, 1)
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
        for i, (cle, wid) in enumerate((('reg_dl', self.n_dl), ('reg_conv', self.n_conv), ('reg_debit', self.debit))):
            gl.addWidget(QLabel(tr(cle)), 1, 2 * i)
            gl.addWidget(wid, 1, 2 * i + 1)
        gl.addWidget(self.eco, 2, 0, 1, 3)
        for wid in (self.n_dl, self.n_conv, self.eco):
            (wid.valueChanged if hasattr(wid, 'valueChanged') else wid.toggled).connect(self._maj_plan)
        v.addWidget(g)
        h = QHBoxLayout()
        self.b_lancer = bouton('ohp_lancer', self.lancer)
        self.b_arreter = bouton('ohp_arreter', self.arreter_traitement)
        self.b_arreter.setEnabled(False)
        h.addWidget(self.b_lancer)
        h.addWidget(self.b_arreter)
        self.barre = aide(QProgressBar(), 'ohp_barre_aide')
        h.addWidget(self.barre, 1)
        v.addLayout(h)
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
        from ...core import astap
        r = config.reglages()
        self._etat_astap = astap.detecter(r['astap_executable'], r['astap_catalogue'])
        e = self._etat_astap
        if e.utilisable:
            self.l_astap.setText(tr('ohp_avec_astap', exe=e.executable, cat=e.catalogue.upper()))
        else:
            self.l_astap.setText(tr(e.message_cle()) + ' ' + tr('astap_sans_effet'))
        self.mode_astap.setEnabled(e.utilisable)
        self._maj_plan()

    def _plan(self):
        from ...core import machine, parallele
        m = machine.detecter()
        return m, parallele.planifier(m, self.n_dl.value(), self.n_conv.value(), True if self.eco.isChecked() else None)

    def _maj_plan(self, *_):
        m, p = self._plan()
        self.l_plan.setText(tr('ohp_machine', cpu=m.coeurs_physiques, log=m.coeurs_logiques,
                               ram='%.1f' % (m.memoire_disponible_mo / 1024), dl=p.telechargements,
                               conv=p.conversions, raison=tr(p.raison)))

    def occupe(self):
        return self._fil is not None and self._fil.is_alive()

    def lancer(self):
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
        if disque_libre_go(dest) * 1e9 < besoin:
            QMessageBox.warning(self, tr('ohp_onglet_traitement'), tr('ohp_place_insuffisante'))
            return
        if est['octets_fits'] > 5e9 and QMessageBox.question(
                self, tr('ohp_onglet_traitement'), tr('ohp_confirmer_gros_gui', taille=_taille(est['octets_fits']))) \
                != QMessageBox.StandardButton.Yes:
            return
        r = config.reglages()
        r['dossier_sortie'] = dest
        r['format_sortie'] = fmt
        etat = self._etat_astap if self._etat_astap.utilisable and self.mode_astap.currentData() != 'jamais' else None
        self.arret = threading.Event()
        self.journal.clear()
        self.barre.setValue(0)
        self._octets, self._t0, self._total = 0, time.time(), 0
        self._evts = FileEvenements(self, self._evenements)
        opts = {'format': fmt, 'langue': self.noms.currentData(), 'astap': etat,
                'mode_astap': self.mode_astap.currentData(), 'debit_octets_s': self.debit.value() * 1e6,
                'garder_fits': self.garder_fits.isChecked(), 'garder_doublons': self.garder_doublons.isChecked()}
        self._log(tr('ohp_journal_debut', n=est['images'], dest=dest, format=fmt.upper()))
        if etat is None:
            self._log(tr('ohp_sans_astap') if not self._etat_astap.utilisable else tr('ohp_astap_desactive'))

        def travail():
            t = None
            try:
                t = Traitement(dest, self.inv, plan, opts, rapporter=self._evts, arret=self.arret)
                t.lancer(sel)
            except Exception as e:
                import traceback
                from ...core import rapports
                rapports.signaler_plantage(traceback.format_exc(), contexte='traitement')
                self._evts({'type': 'erreur', 'erreur': '%s: %s' % (type(e).__name__, e)})
            finally:
                if t is not None:
                    t.fermer()
                self._evts({'type': 'termine'})
        self.b_lancer.setEnabled(False)
        self.b_arreter.setEnabled(True)
        self._fil = threading.Thread(target=travail, name='traitement', daemon=True)
        self._fil.start()

    def arreter_traitement(self):
        if self.arret is not None:
            self.arret.set()
            self._log(tr('ohp_arret_demande'))
            self.b_arreter.setEnabled(False)

    def arreter(self):
        if self.arret is not None:
            self.arret.set()

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
            elif t == 'erreur':
                self._log(tr('ohp_erreur_traitement', erreur=ev['erreur']))
            elif t == 'fin':
                b = ev['bilan']
                of, ox = b['octets_fits'], b['octets_sortie']
                self._log(tr('ohp_bilan', ok=b['statuts'].get('ok', 0), doublons=b['statuts'].get('doublon', 0),
                             echecs=b['statuts'].get('echec', 0), fits=_taille(of), sortie=_taille(ox),
                             ratio='%.1f' % (100 * ox / of if of else 0), lots=b.get('lots', '?'),
                             dest=self.dest.text()))
                if b.get('annule'):
                    self._log(tr('interrompu_reprise'))
            elif t == 'termine':
                self.b_lancer.setEnabled(True)
                self.b_arreter.setEnabled(False)
                self._evts.timer.stop()
                self._remplir_lots()
                self._remplir_anomalies()

    # ================================================================ lots
    def _onglet_lots(self):
        w = QWidget()
        v = QVBoxLayout(w)
        h = QHBoxLayout()
        h.addWidget(bouton('ohp_lots_actualiser', self._remplir_lots))
        h.addWidget(bouton('ohp_lots_ouvrir', self._ouvrir_lot))
        h.addWidget(bouton('ohp_lots_dossier', lambda: ouvrir_fichier(self.dest.text())))
        h.addStretch(1)
        v.addLayout(h)
        self.l_lots = QLabel('')
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
        self.l_lots.setText(tr('ohp_lots_resume', n=len(lignes), dest=self.dest.text()) if lignes
                            else tr('ohp_lots_aucun', dest=self.dest.text()))

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
        h = QHBoxLayout()
        self.f_genre = liste('ohp_f_genre_aide', [(tr('ohp_tous_genres'), '')])
        self.f_genre.currentIndexChanged.connect(self._filtrer_anomalies)
        self.f_anom_nouv = case('ohp_f_nouveaux')
        self.f_anom_nouv.toggled.connect(self._filtrer_anomalies)
        h.addWidget(self.f_genre)
        h.addWidget(self.f_anom_nouv)
        h.addStretch(1)
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
        self._t_anom.fini.connect(self._anomalies_pretes)
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
        h = QHBoxLayout()
        self.ciel_cat = liste('ohp_f_cat_aide', [(tr('ohp_tous_types'), '')] +
                              [(tr('ohp_cat_' + c), c) for c in cibles.CATEGORIES])
        self.ciel_cat.currentIndexChanged.connect(self._remplir_ciel)
        h.addWidget(self.ciel_cat)
        self.l_ciel = QLabel(tr('ohp_ciel_intro'))
        self.l_ciel.setWordWrap(True)
        h.addWidget(self.l_ciel, 1)
        v.addLayout(h)
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
