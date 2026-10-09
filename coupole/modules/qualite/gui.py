"""Panneau « Qualité des images » : mesures en processus parallèles (moteur.Mesureur), résultats incrémentaux,
cache et reprise, échantillon par lot pour les gros dossiers, temps restant estimé, annulation immédiate."""
from __future__ import annotations

import os
import threading

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QProgressBar, QSplitter,
                             QVBoxLayout, QWidget)

from ...core import config
from ...core.i18n import langue, tr
from ...gui.adaptatif import Flux, coupable, texte_reel
from ...gui.modele import ModeleTableau, Nombre, vue_tableau
from ...gui.outils import FileEvenements, aide, bouton, case, nombre
from . import mesures, moteur, rapport
from .gui_sans_qt import duree_lisible


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        h = Flux()
        h.addWidget(bouton('qual_choisir', self.choisir))
        self.b_lancer = bouton('qual_lancer', self.lancer)
        self.b_arreter = bouton('qual_arreter', self.arreter)
        self.b_arreter.setEnabled(False)
        h.addWidget(self.b_lancer)
        h.addWidget(self.b_arreter)
        self.l_dossier = QLabel(coupable(config.reglages()['dossier_sortie'] or
                                        str(config.dossier_sortie_defaut() / 'OHP_DU_ECU')))
        self.l_dossier.setWordWrap(True)
        h.addWidget(self.l_dossier)
        v.addLayout(h)
        h = Flux()
        self.echantillon = case('qual_echantillon')
        self.n_echantillon = nombre('qual_n_echantillon_aide', 1, 50, moteur.ECHANTILLON_DEFAUT)
        self.n_echantillon.setSuffix(' ' + tr('qual_n_suffixe'))
        h.addWidget(self.echantillon)
        h.addWidget(self.n_echantillon)
        v.addLayout(h)
        if not mesures.disponible():
            l = QLabel(tr('qual_absent'))
            l.setWordWrap(True)
            v.addWidget(l)
            self.b_lancer.setEnabled(False)
        self.barre = aide(QProgressBar(), 'qual_barre_aide')
        v.addWidget(self.barre)
        self.l_progression = aide(QLabel(''), 'qual_progression_aide')
        self.l_progression.setWordWrap(True)
        v.addWidget(self.l_progression)
        sp = QSplitter(Qt.Orientation.Vertical)
        self.modele = ModeleTableau([tr('qual_col_' + c) for c in rapport.COLONNES])
        self.vue, _ = vue_tableau(self.modele, 'qual_table_aide')
        sp.addWidget(self.vue)
        self.resume = aide(QPlainTextEdit(), 'qual_resume_aide')
        self.resume.setReadOnly(True)
        sp.addWidget(self.resume)
        v.addWidget(sp, 1)
        self._fil = None
        self._arret = threading.Event()
        self._lignes = []
        self._evts = None
        self.bilan = None

    def choisir(self):
        d = QFileDialog.getExistingDirectory(self, tr('qual_choisir'), texte_reel(self.l_dossier.text()))
        if d:
            self.l_dossier.setText(coupable(d))

    def occupe(self):
        return self._fil is not None and self._fil.is_alive()

    # ---------------------------------------------------------------- lancement en deux temps : plan, puis mesure
    def lancer(self, dossier=None, tout: bool | None = None):
        """`tout` : None = demander si le dossier est gros ; True = tout mesurer ; False = échantillon."""
        if self.occupe():
            return
        racine = dossier or texte_reel(self.l_dossier.text())
        if dossier:
            self.l_dossier.setText(coupable(dossier))
        self.b_lancer.setEnabled(False)
        self.l_progression.setText(tr('qual_inventaire'))
        n_lot = int(self.n_echantillon.value())
        ech = n_lot if (tout is False or (tout is None and self.echantillon.isChecked())) else None
        evts = FileEvenements(self, self._evenements)
        self._evts = evts
        demander = tout is None and ech is None

        def preparer():
            plan_ = moteur.planifier(racine, ech)
            estimation = None
            if demander and plan_['total_dossier'] > moteur.SEUIL_GROS_DOSSIER and plan_['a_mesurer'] > 3:
                plan_['chemin'] = racine
                estimation = moteur.estimer_duree(plan_, moteur.processus_pour(None, plan_['reseau']))
            evts({'type': 'plan', 'plan': plan_, 'estimation': estimation, 'racine': racine, 'echantillon': ech,
                  'n_lot': n_lot, 'demander': demander})
        from ...gui.outils import lancer_fil
        self._fil = lancer_fil(preparer)

    def _plan_pret(self, ev):
        plan_, est, racine, ech = ev['plan'], ev['estimation'], ev['racine'], ev['echantillon']
        if est is not None:                        # gros dossier : on demande avant d'engager des heures
            texte = tr('qual_gros_dossier', images=plan_['total_dossier'], lots=len(plan_['lots']),
                       a_mesurer=plan_['a_mesurer'], par_image='%.1f' % est['par_image_s'],
                       processus=est['processus'], duree=duree_lisible(est['duree_s']), n=ev['n_lot'])
            if plan_['reseau']:
                texte += '\n\n' + tr('qual_reseau')
            b = QMessageBox(QMessageBox.Icon.Question, tr('qual_gros_dossier_titre'), texte, parent=self)
            b_ech = b.addButton(tr('qual_btn_echantillon', n=ev['n_lot']), QMessageBox.ButtonRole.AcceptRole)
            b_tout = b.addButton(tr('qual_btn_tout', duree=duree_lisible(est['duree_s'])), QMessageBox.ButtonRole.AcceptRole)
            b.addButton(QMessageBox.StandardButton.Cancel)
            b.exec()
            if b.clickedButton() is b_ech:
                ech = ev['n_lot']
                self.echantillon.setChecked(True)
            elif b.clickedButton() is b_tout:
                ech = None
            else:
                self.b_lancer.setEnabled(mesures.disponible())
                self.l_progression.setText('')
                self._evts.arreter()
                return
        self._demarrer(racine, ech, plan_)

    def _demarrer(self, racine, ech, plan_dossier=None):
        self.barre.setMaximum(1)
        self.barre.setValue(0)
        self._lignes = []
        self.modele.remplir([])
        self.resume.setPlainText('')
        self._arret.clear()
        evts, arret = self._evts, self._arret
        plan = None                                  # plan machine calculé dans le fil de mesure (sondes hors du fil graphique)
        # le plan du dossier (parcours, tailles, cache) déjà fait pour le dialogue est repris tel quel
        m = moteur.Mesureur(racine, plan, ech, rapporter=evts, arret=arret, langue=langue(), plan_dossier=plan_dossier)

        def travail():
            try:
                m.lancer()
            except Exception as e:
                evts({'type': 'erreur', 'erreur': '%s: %s' % (type(e).__name__, e)})
        self.b_arreter.setEnabled(True)
        from ...gui.outils import enregistrer_arret, lancer_fil
        enregistrer_arret(self._arret)
        self._fil = lancer_fil(travail)

    def arreter(self):
        """Annulation immédiate : les processus de mesure sont terminés, les mesures faites restent au cache."""
        self._arret.set()
        self.b_arreter.setEnabled(False)

    # ---------------------------------------------------------------- événements du moteur (fil graphique)
    def _ligne(self, l):
        """Cellules d'une image : nombres triés comme nombres (FWHM, fond, RSN…), affichés comme dans QUALITE.csv."""
        out = []
        for c in rapport.COLONNES:
            v = l.get(c)
            if c == 'echantillonnage' and v:
                out.append(tr('qual_ech_' + v))
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append(Nombre(v))
            else:
                out.append(rapport._fmt(v, '%.4g'))
        return tuple(out)

    def _evenements(self, evs):
        nouvelles = []
        for ev in evs:
            t = ev['type']
            if t == 'plan':
                self._plan_pret(ev)
            elif t == 'debut':
                self.barre.setMaximum(max(1, ev['total']))
                texte = tr('qual_debut', total=ev['total'], lots=ev['lots'], deja=ev['deja'], processus=ev['processus'])
                if ev['echantillon']:
                    texte += ' ' + tr('qual_debut_echantillon', n=ev['echantillon'], dossier=ev['total_dossier'])
                if ev['reseau']:
                    texte += ' ' + tr('qual_reseau')
                self.resume.setPlainText(texte)
                self.l_progression.setText(texte)
            elif t == 'image':
                self._lignes.append(ev['ligne'])
                nouvelles.append(self._ligne(ev['ligne']))
            elif t == 'progression':
                self.barre.setValue(ev['fait'])
                self.l_progression.setText(tr('qual_progression', fait=ev['fait'], total=ev['total'],
                                              eta=duree_lisible(ev['eta_s']), debit='%.1f' % ev['debit']))
            elif t == 'lot':
                self.resume.setPlainText('%s\n%s' % (ev['lot'], '\n'.join(rapport.resume(ev['lignes'], langue()))))
            elif t == 'erreur':
                self.resume.appendPlainText(ev['erreur'])
                self._terminer()
            elif t == 'fin':
                self.bilan = ev
                self.barre.setValue(ev['n'])
                self.resume.appendPlainText('\n' + tr('qual_fini', n=ev['n'], lots=ev['lots'], deja=ev['deja'],
                                                      duree=duree_lisible(ev['duree'])) +
                                            (' ' + tr('interrompu_reprise') if ev['annule'] else ''))
                self.l_progression.setText(tr('qual_fini', n=ev['n'], lots=ev['lots'], deja=ev['deja'],
                                              duree=duree_lisible(ev['duree'])))
                self._terminer()
        if nouvelles:                                  # ajout incrémental : le modèle n'est pas reconstruit
            self.modele.ajouter(nouvelles)

    def _terminer(self):
        self.b_lancer.setEnabled(mesures.disponible())
        self.b_arreter.setEnabled(False)
        if self._evts is not None:
            self._evts.arreter()

    def aide_html(self):
        return tr('qual_aide_html')
