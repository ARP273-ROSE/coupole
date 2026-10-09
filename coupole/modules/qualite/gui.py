"""Panneau « Qualité des images » : mesures en processus parallèles (moteur.Mesureur), résultats incrémentaux,
cache et reprise, échantillon par lot pour les gros dossiers, temps restant estimé, annulation immédiate."""
from __future__ import annotations

import os
import threading

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QProgressBar, QSplitter,
                             QVBoxLayout, QWidget)

from ...core import config
from ...core.i18n import langue, tr
from ...gui import fichiers, memoire
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
        self.sp = sp
        self._memoriser()
        self._fil = None
        self._arret = threading.Event()
        self._lignes = []
        self._evts = None
        self._mesureur = None
        self._question = None
        self.bilan = None

    def _memoriser(self):
        """Dossier analysé, échantillon et N, séparateur, colonnes : gardés d'une fermeture à l'autre."""
        from ...core.etat_interface import etat
        k = 'modules.qualite.'
        d = etat().lire_texte(k + 'dossier', '')
        self._dossier_choisi = bool(d)               # sinon : le dossier de sortie (Préférences), qu'on suit
        if d:
            self.l_dossier.setText(coupable(d))      # affiché tel quel ; un dossier absent est signalé au lancement
        memoire.memoire().suivre(k + 'dossier', lambda: texte_reel(self.l_dossier.text()) if self._dossier_choisi
                                 else None, self.l_dossier)
        memoire.case(self.echantillon, k + 'echantillon')
        memoire.nombre(self.n_echantillon, k + 'echantillon_n')
        memoire.separateur(self.sp, k + 'separateur')
        memoire.entete(self.vue, k + 'colonnes')

    def reglages_changes(self):
        """Préférences modifiées : tant qu'aucun dossier n'a été choisi ici, on analyse le dossier de sortie."""
        if not self._dossier_choisi and not self.occupe():
            self.l_dossier.setText(coupable(config.reglages()['dossier_sortie'] or
                                            str(config.dossier_sortie_defaut() / 'OHP_DU_ECU')))

    def choisir(self):
        d = fichiers.choisir_dossier(self, tr('qual_choisir'), texte_reel(self.l_dossier.text()))
        if d:
            self.l_dossier.setText(coupable(d))
            self._dossier_choisi = True
            memoire.memoire().signaler()

    def occupe(self):
        return self._fil is not None and self._fil.is_alive()

    # ---------------------------------------------------------------- lancement : inventaire et mesure en flux
    def lancer(self, dossier=None, tout: bool | None = None):
        """`tout` : None = demander si le dossier est gros ; True = tout mesurer ; False = échantillon.

        La mesure commence dès le premier lot trouvé, pendant que l'inventaire continue ; pour un gros dossier la
        question (échantillon ou tout) est posée quand l'inventaire est fini, sans arrêter la mesure de
        l'échantillon, qui sert dans les deux cas."""
        if self.occupe():
            return
        racine = dossier or texte_reel(self.l_dossier.text())
        if dossier:
            self.l_dossier.setText(coupable(dossier))
            self._dossier_choisi = True
            memoire.memoire().signaler()
        self.b_lancer.setEnabled(False)
        self.l_progression.setText(tr('qual_inventaire'))
        n_lot = int(self.n_echantillon.value())
        ech = n_lot if (tout is False or (tout is None and self.echantillon.isChecked())) else None
        self._demarrer(racine, ech, demander=tout is None and ech is None, n_lot=n_lot)

    def _demarrer(self, racine, ech, demander: bool = False, n_lot: int = moteur.ECHANTILLON_DEFAUT):
        self.barre.setMaximum(0)                     # inventaire : barre animée tant que le total est inconnu
        self.barre.setValue(0)
        self._lignes = []
        self.modele.remplir([])
        self.resume.setPlainText('')
        self._arret.clear()
        if self._question is not None:
            self._question.close()
            self._question = None
        evts = FileEvenements(self, self._evenements)
        self._evts = evts
        arret = self._arret
        plan = None                                  # plan machine calculé dans le fil de mesure (sondes hors du fil graphique)
        m = moteur.Mesureur(racine, plan, ech, rapporter=evts, arret=arret, langue=langue(), demander=demander,
                            n_echantillon=n_lot)
        self._mesureur = m

        def travail():
            try:
                m.lancer()
            except Exception as e:
                evts({'type': 'erreur', 'erreur': '%s: %s' % (type(e).__name__, e)})
        self.b_arreter.setEnabled(True)              # l'inventaire lui-même s'annule
        from ...gui.outils import enregistrer_arret, lancer_fil
        enregistrer_arret(self._arret)
        self._fil = lancer_fil(travail)

    def _questionner(self, ev):
        """Gros dossier : échantillon ou tout ?  Boîte non modale (la mesure de l'échantillon continue)."""
        texte = tr('qual_gros_dossier', images=ev['total_dossier'], lots=ev['lots'], a_mesurer=ev['a_mesurer'],
                   par_image='%.1f' % ev['par_image_s'], processus=ev['processus'],
                   duree=duree_lisible(ev['duree_s']), n=ev['n'])
        if ev['reseau']:
            texte += '\n\n' + tr('qual_reseau')
        b = QMessageBox(QMessageBox.Icon.Question, tr('qual_gros_dossier_titre'), texte, parent=self)
        b_ech = b.addButton(tr('qual_btn_echantillon', n=ev['n']), QMessageBox.ButtonRole.AcceptRole)
        b_tout = b.addButton(tr('qual_btn_tout', duree=duree_lisible(ev['duree_s'])), QMessageBox.ButtonRole.AcceptRole)
        b.addButton(QMessageBox.StandardButton.Cancel)
        m = self._mesureur

        def repondre(*_):
            if self._question is b:
                self._question = None
            clic = b.clickedButton()
            if m is not self._mesureur or not self.occupe():
                return
            if clic is b_ech:
                self.echantillon.setChecked(True)
                m.decider('echantillon')
            elif clic is b_tout:
                m.decider('tout')
            else:
                self.arreter()
        b.finished.connect(repondre)
        self._question = b
        b.open()

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
            if t == 'inventaire':
                if not ev['fini']:
                    self.l_progression.setText(tr('qual_inventaire_n', trouves=ev['trouves'], lots=ev['lots'],
                                                  fait=ev['fait']))
            elif t == 'question':
                self._questionner(ev)
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
                if ev['inventaire_fini']:
                    self.barre.setMaximum(max(1, ev['total']))
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
                self.barre.setMaximum(max(1, ev['n']))
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
        if self._question is not None:
            self._question.close()
            self._question = None
        self.b_lancer.setEnabled(mesures.disponible())
        self.b_arreter.setEnabled(False)
        if self._evts is not None:
            self._evts.arreter()

    def aide_html(self):
        return tr('qual_aide_html')
