"""Panneau « Partages du DU » : dossiers collaboratifs (Nextcloud) des défis et TP, tout en un seul endroit.

Même ergonomie que la Banque OHP : guide en trois étapes, liste à gauche (partages mémorisés et structure découverte
du partage choisi : dossiers datés, observateurs, séries, tableaux), contenu à droite (fichiers, aperçu), bouton bleu
« Télécharger », clic droit, double-clic qui propose, nouveautés depuis la dernière visite.  Onglets : Contenu,
Mesures (tableaux contrôlés ligne par ligne), Analyse (outil branché : Parallaxe…), Déposer ma mesure.

Rien de lent dans le fil graphique : chaque accès au réseau passe par une `Tache` ou un fil enregistré, dont les
événements arrivent par une `FileEvenements` lue à cadence fixe.
"""
from __future__ import annotations

import datetime as D
import html
import os
import threading

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QComboBox, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QMenu, QMessageBox, QProgressBar, QSplitter, QTabWidget, QTextBrowser, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget)

from ...core.i18n import decimal as _dec
from ...core.i18n import tr
from ...gui import fichiers, memoire, ouvrir, pastilles
from ...gui.adaptatif import Flux, coupable
from ...gui.modele import ModeleParesseux, vue_tableau
from ...gui.outils import (FileEvenements, Tache, aide, bouton, bouton_principal, case, champ, enregistrer_arret,
                           lancer_fil, liste)
from . import etat, structure as S
from .apercus import SansApercu, taille_lisible
from .gui_sans_qt import texte_anomalie

COLONNES = ('etat', 'nom', 'genre', 'taille', 'instant', 'observateur', 'cible', 'dossier')
COL_MESURES = ('ligne', 'niveau', 'cible', 'auteur', 'instant', 'lat', 'lon', 'alt', 'az', 'h', 'fichier', 'remarques')
ROLE = Qt.ItemDataRole.UserRole


def _heure(d) -> str:
    if d is None:
        return ''
    return d.strftime('%Y-%m-%d %H:%M:%S') + ('.%01d' % (d.microsecond // 100000) if d.microsecond else '')


class DialogueAjout(QDialog):
    """Ajouter un partage : nom libre, lien, mot de passe facultatif ; « Vérifier » lit les droits (en fond)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('pt_ajout_titre'))
        self.info = None
        self.partage = None
        v = QVBoxLayout(self)
        intro = QLabel(tr('pt_ajout_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        f = QFormLayout()
        self.e_nom = champ('pt_ajout_nom_aide', '', 'pt_ajout_nom_indice')
        self.e_lien = champ('pt_ajout_lien_aide', '', 'pt_ajout_lien_indice')
        self.e_mdp = champ('pt_ajout_mdp_aide')
        self.e_mdp.setEchoMode(QLineEdit.EchoMode.Password)
        f.addRow(tr('pt_ajout_nom'), self.e_nom)
        f.addRow(tr('pt_ajout_lien'), self.e_lien)
        f.addRow(tr('pt_ajout_mdp'), self.e_mdp)
        v.addLayout(f)
        h = QHBoxLayout()
        self.b_verifier = bouton('pt_ajout_verifier', self.verifier)
        h.addWidget(self.b_verifier)
        h.addStretch(1)
        v.addLayout(h)
        self.l_resultat = aide(QLabel(''), 'pt_ajout_resultat_aide')
        self.l_resultat.setWordWrap(True)
        self.l_resultat.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(self.l_resultat)
        from ...gui.dialogues import _boutons
        self.bb = _boutons(self)
        v.addWidget(self.bb)
        self.e_lien.textChanged.connect(lambda *_: self._invalider())
        self.e_mdp.textChanged.connect(lambda *_: self._invalider())
        self._invalider()
        self.resize(640, 320)

    def _invalider(self):
        self.info = None
        from PyQt6.QtWidgets import QDialogButtonBox
        self.bb.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def verifier(self):
        from .webdav import Client, LienInvalide, analyser_lien
        try:
            self.partage = analyser_lien(self.e_lien.text(), mot_de_passe=self.e_mdp.text())
        except LienInvalide as e:
            self.l_resultat.setText('<span style="color:%s">%s</span>' % (
                pastilles.couleur_statut('echec').name(), html.escape(tr(e.cle))))
            return
        self.l_resultat.setText(html.escape(tr('pt_ajout_en_cours')))
        self.b_verifier.setEnabled(False)
        t = Tache(Client(self.partage, 20).verifier, parent=self)
        t.quand_fini(self._verifie)
        t.quand_erreur(self._echec)
        self._tache = t
        t.start()

    def _echec(self, texte):
        self.b_verifier.setEnabled(True)
        cle = texte.split(':', 1)[-1].strip().split(' ')[0]
        msg = tr(cle) if cle.startswith('pt_err_') else texte
        self.l_resultat.setText('<span style="color:%s">%s</span>' % (pastilles.couleur_statut('echec').name(),
                                                                      html.escape(msg)))

    def _verifie(self, info):
        from PyQt6.QtWidgets import QDialogButtonBox
        self.b_verifier.setEnabled(True)
        self.info = info
        self.l_resultat.setText(html_droits(info.droits, len(info.entrees)))
        if not self.e_nom.text().strip():
            self.e_nom.setText(tr('pt_nom_defaut'))
        self.bb.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)


def html_droits(droits: list, n_entrees: int | None = None) -> str:
    txt = ', '.join(tr('pt_droit_' + d) for d in droits) or tr('pt_droit_aucun')
    h = '<b>%s</b> %s' % (html.escape(tr('pt_droits')), html.escape(txt))
    if n_entrees is not None:
        h += '<br>%s' % html.escape(tr('pt_ajout_ok', n=n_entrees))
    if 'supprimer' in droits or 'renommer' in droits or 'deplacer' in droits:
        h += '<br><span style="color:%s"><b>%s</b> %s</span>' % (pastilles.couleur_statut('echec').name(),
                                                                html.escape(tr('pt_attention')),
                                                                html.escape(tr('pt_droit_suppression')))
    return h


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = None
        self.selection: list = []
        self.possedes: dict = {}
        self._noeud = None
        self._arret_liste = enregistrer_arret(threading.Event())
        self._arret_dl = enregistrer_arret(threading.Event())
        self._pause_dl = threading.Event()
        self._fil_dl = None
        self._taches = []
        self._octets_total = 0
        self._apercu_jeton = 0
        self.appliquer_corrections = True
        v = QVBoxLayout(self)
        self.guide = self._guide()
        v.addWidget(self.guide)
        self.bandeau = QFrame()
        hb = QHBoxLayout(self.bandeau)
        hb.setContentsMargins(6, 2, 6, 2)
        self.l_bandeau = QLabel('')
        self.l_bandeau.setWordWrap(True)
        hb.addWidget(self.l_bandeau, 1)
        hb.addWidget(bouton('pt_nouveautes_voir', lambda: self._choisir_noeud(('nouveaux', ''))))
        hb.addWidget(bouton('pt_nouveautes_vus', self.marquer_vus))
        self.bandeau.setVisible(False)
        v.addWidget(self.bandeau)
        self.sp = QSplitter(Qt.Orientation.Horizontal)
        self.sp.addWidget(self._gauche())
        self.onglets = QTabWidget()
        self.onglets.addTab(self._onglet_contenu(), tr('pt_onglet_contenu'))
        self.onglets.addTab(self._onglet_mesures(), tr('pt_onglet_mesures'))
        self.onglet_analyse = QWidget()
        QVBoxLayout(self.onglet_analyse)
        self.onglets.addTab(self.onglet_analyse, tr('pt_onglet_analyse'))
        self.onglets.addTab(self._onglet_depot(), tr('pt_onglet_depot'))
        for k, c in enumerate(('pt_onglet_contenu_aide', 'pt_onglet_mesures_aide', 'pt_onglet_analyse_aide',
                               'pt_onglet_depot_aide')):
            self.onglets.setTabToolTip(k, tr(c))
        self.sp.addWidget(self.onglets)
        self.sp.setStretchFactor(0, 1)
        self.sp.setStretchFactor(1, 3)
        self.sp.setSizes([330, 1000])
        v.addWidget(self.sp, 1)
        self.l_etat = QLabel(tr('pt_pret'))
        self.l_etat.setWordWrap(True)
        v.addWidget(self.l_etat)
        self._evts = FileEvenements(self, self._evenements, 150)
        self.outil_panneau = None
        self._remplir_partages()
        memoire.separateur(self.sp, 'modules.partages.separateur')
        memoire.onglets(self.onglets, 'modules.partages.onglet')

    # ================================================================================================ construction
    def _guide(self):
        from ...core.etat_interface import etat as etat_ui
        w = QFrame()
        w.setObjectName('guideDebutant')
        aide(w, 'pt_guide_aide')
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 6, 10, 6)
        v.setSpacing(2)
        h = Flux(espace=14)
        h.addWidget(QLabel('<b>%s</b>' % html.escape(tr('pt_guide_titre'))))
        self.l_etapes = []
        for _ in range(3):
            lab = QLabel()
            lab.setTextFormat(Qt.TextFormat.RichText)
            self.l_etapes.append(lab)
            h.addWidget(lab)
        v.addLayout(h)
        h2 = QHBoxLayout()
        lab = QLabel(tr('pt_guide_suite'))
        lab.setWordWrap(True)
        h2.addWidget(lab, 1)
        h2.addWidget(bouton('pt_guide_fermer', self.masquer_guide), 0, Qt.AlignmentFlag.AlignVCenter)
        v.addLayout(h2)
        w.setVisible(not etat_ui().lire('modules.partages.guide_masque', False, bool))
        return w

    def _maj_guide(self):
        faites = (self.session is not None and self.session.structure is not None,
                  bool(self.selection), bool(self.possedes) or self.outil_panneau is not None
                  and getattr(self.outil_panneau, 'a_calcule', False))
        courante = next((k for k, f in enumerate(faites) if not f), None)
        for k, lab in enumerate(self.l_etapes):
            marque = '&#10004;' if faites[k] else '%d' % (k + 1)
            t = html.escape(tr('pt_guide_etape%d' % (k + 1)))
            if k == courante:
                t = '<b>%s</b>' % t
            couleur = pastilles.couleur_statut('ok' if faites[k] else 'partiel').name()
            lab.setText('<span style="font-weight:bold; color:%s">%s</span>&nbsp; %s' % (couleur, marque, t))

    def masquer_guide(self):
        from ...core.etat_interface import etat as etat_ui
        self.guide.setVisible(False)
        etat_ui().ecrire('modules.partages.guide_masque', True)
        memoire.memoire().signaler()

    def montrer_guide(self):
        from ...core.etat_interface import etat as etat_ui
        etat_ui().ecrire('modules.partages.guide_masque', False)
        memoire.memoire().signaler()
        self._maj_guide()
        self.guide.setVisible(True)

    def _gauche(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        h = QHBoxLayout()
        h.addWidget(QLabel(tr('pt_partage')))
        self.c_partages = liste('pt_partage_aide', [])
        self.c_partages.currentIndexChanged.connect(lambda *_: self._partage_choisi())
        h.addWidget(self.c_partages, 1)
        v.addLayout(h)
        f = Flux()
        self.b_ajouter = bouton('pt_ajouter', self.ajouter_partage)
        self.b_rafraichir = bouton('pt_rafraichir', self.rafraichir)
        self.b_gerer = bouton('pt_gerer', self._menu_gerer)
        for b in (self.b_ajouter, self.b_rafraichir, self.b_gerer):
            f.addWidget(b)
        v.addLayout(f)
        self.l_droits = aide(QLabel(''), 'pt_droits_aide')
        self.l_droits.setWordWrap(True)
        self.l_droits.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(self.l_droits)
        self.arbre = aide(QTreeWidget(), 'pt_arbre_aide')
        self.arbre.setHeaderHidden(True)
        self.arbre.itemSelectionChanged.connect(self._noeud_choisi)
        self.arbre.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.arbre.customContextMenuRequested.connect(self._menu_arbre)
        v.addWidget(self.arbre, 1)
        self.l_resume = aide(QLabel(''), 'pt_resume_aide')
        self.l_resume.setWordWrap(True)
        v.addWidget(self.l_resume)
        return w

    def _onglet_contenu(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        sp = QSplitter(Qt.Orientation.Horizontal)
        self.modele = ModeleParesseux([tr('pt_col_' + c) for c in COLONNES], self._ligne, style=self._style,
                                      bulle=self._bulle, cle=self._cle)
        self.modele.bulles_entetes = [tr('pt_col_%s_aide' % c) for c in COLONNES]
        self.vue, self.proxy = vue_tableau(self.modele, 'pt_table_aide')
        self.vue.message_vide = lambda: tr('pt_table_vide' if self.session else 'pt_table_sans_partage')
        self.vue.selectionModel().selectionChanged.connect(lambda *_: self._selection())
        self.vue.doubleClicked.connect(lambda *_: self._double_clic())
        self.vue.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vue.customContextMenuRequested.connect(self._menu_fichiers)
        sp.addWidget(self.vue)
        droite = QWidget()
        vd = QVBoxLayout(droite)
        vd.setContentsMargins(0, 0, 0, 0)
        self.l_apercu = aide(QLabel(tr('pt_apercu_rien')), 'pt_apercu_aide')
        self.l_apercu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l_apercu.setMinimumSize(200, 160)
        self.l_apercu.setWordWrap(True)
        vd.addWidget(self.l_apercu, 1)
        self.b_apercu = bouton('pt_apercu_forcer', lambda: self._apercu(forcer=True))
        self.b_apercu.setVisible(False)
        vd.addWidget(self.b_apercu)
        self.fiche = aide(QTextBrowser(), 'pt_fiche_aide')
        vd.addWidget(self.fiche, 1)
        sp.addWidget(droite)
        sp.setStretchFactor(0, 3)
        sp.setStretchFactor(1, 1)
        sp.setSizes([800, 330])
        v.addWidget(sp, 1)
        f = Flux()
        self.b_telecharger = bouton_principal('pt_telecharger', self.telecharger)
        self.b_pause = bouton('pt_pause', self.pause)
        self.b_annuler = bouton('pt_annuler', self.annuler)
        self.b_ouvrir = bouton('pt_ouvrir_dossier', self.ouvrir_dossier)
        for b in (self.b_telecharger, self.b_pause, self.b_annuler, self.b_ouvrir):
            f.addWidget(b)
        self.l_selection = aide(QLabel(''), 'pt_selection_aide')
        f.addWidget(self.l_selection)
        self.b_pause.setEnabled(False)
        self.b_annuler.setEnabled(False)
        v.addLayout(f)
        f = Flux()
        from .telechargement import sortie_par_defaut
        f.addWidget(QLabel(tr('pt_dossier')))
        self.l_dossier = aide(QLabel(coupable(memoire.dossier('modules.partages.sortie', sortie_par_defaut()))),
                              'pt_dossier_aide')
        self.l_dossier.setWordWrap(True)
        f.addWidget(self.l_dossier)
        f.addWidget(bouton('pt_choisir_dossier', self.choisir_dossier))
        self.c_format = liste('pt_format_aide', [(tr('pt_format_xisf'), 'xisf'), (tr('pt_format_fits'), 'fits')])
        memoire.liste(self.c_format, 'modules.partages.format')
        f.addWidget(self.c_format)
        self.c_astrometrie = liste('pt_astrometrie_aide', [(tr('pt_astro_wcs'), 'wcs'), (tr('pt_astro_auto'), 'auto'),
                                                           (tr('pt_astro_astap'), 'astap'),
                                                           (tr('pt_astro_anet'), 'astrometry.net'),
                                                           (tr('pt_astro_en_ligne'), 'en_ligne')])
        memoire.liste(self.c_astrometrie, 'modules.partages.astrometrie')
        f.addWidget(self.c_astrometrie)
        self.c_garder = case('pt_garder', True)
        memoire.case(self.c_garder, 'modules.partages.garder')
        f.addWidget(self.c_garder)
        v.addLayout(f)
        self.barre = aide(QProgressBar(), 'pt_barre_aide')
        self.barre.setRange(0, 1000)
        self.barre.setValue(0)
        self.barre.setFormat('')
        v.addWidget(self.barre)
        self.l_progres = aide(QLabel(''), 'pt_progres_aide')
        self.l_progres.setWordWrap(True)
        v.addWidget(self.l_progres)
        return w

    def _onglet_mesures(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        intro = QLabel(tr('pt_mesures_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        f = Flux()
        f.addWidget(QLabel(tr('pt_tableau')))
        self.c_tableaux = liste('pt_tableau_aide', [])
        self.c_tableaux.setMinimumWidth(260)
        self.c_tableaux.currentIndexChanged.connect(lambda *_: self._tableau_choisi())
        f.addWidget(self.c_tableaux)
        self.b_lire_tableau = bouton('pt_lire_tableau', self.lire_tableau)
        f.addWidget(self.b_lire_tableau)
        self.c_a_verifier = case('pt_a_verifier', False)
        self.c_a_verifier.toggled.connect(lambda *_: self._remplir_mesures())
        f.addWidget(self.c_a_verifier)
        self.c_corrections = case('pt_corrections', True)
        memoire.case(self.c_corrections, 'modules.partages.corrections')
        self.c_corrections.toggled.connect(self._corrections)
        f.addWidget(self.c_corrections)
        f.addWidget(bouton('pt_exporter_csv', self.exporter_csv))
        v.addLayout(f)
        self.modele_m = ModeleParesseux([tr('pt_m_' + c) for c in COL_MESURES], self._ligne_m, style=self._style_m)
        self.vue_m, self.proxy_m = vue_tableau(self.modele_m, 'pt_mesures_aide')
        self.vue_m.message_vide = lambda: tr('pt_mesures_vide')
        v.addWidget(self.vue_m, 1)
        self.l_mesures = aide(QLabel(''), 'pt_mesures_resume_aide')
        self.l_mesures.setWordWrap(True)
        v.addWidget(self.l_mesures)
        return w

    def _onglet_depot(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        intro = QLabel(tr('pt_depot_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        self.l_depot_droits = QLabel('')
        self.l_depot_droits.setWordWrap(True)
        v.addWidget(self.l_depot_droits)
        f = Flux()
        f.addWidget(bouton('pt_depot_ajouter', self._depot_ajouter))
        f.addWidget(bouton('pt_depot_retirer', self._depot_retirer))
        v.addLayout(f)
        self.l_depot_fichiers = aide(QListWidget(), 'pt_depot_fichiers_aide')
        self.l_depot_fichiers.setMaximumHeight(110)
        v.addWidget(self.l_depot_fichiers)
        form = QFormLayout()
        self.c_depot_dossier = QComboBox()
        self.c_depot_dossier.setEditable(True)
        aide(self.c_depot_dossier, 'pt_depot_dossier_aide')
        form.addRow(tr('pt_depot_dossier'), self.c_depot_dossier)
        self.c_depot_tableau = liste('pt_depot_tableau_aide', [(tr('pt_depot_sans_tableau'), '')])
        form.addRow(tr('pt_depot_tableau'), self.c_depot_tableau)
        self.e_depot = {}
        for role in ('auteur', 'cible', 'date', 'latitude', 'longitude', 'altitude', 'azimut', 'hauteur'):
            e = champ('pt_depot_%s_aide' % role, '', 'pt_depot_%s_indice' % role)
            self.e_depot[role] = e
            form.addRow(tr('pt_depot_' + role), e)
        memoire.champ(self.e_depot['auteur'], 'modules.partages.auteur')
        v.addLayout(form)
        f = Flux()
        self.b_depot = bouton_principal('pt_depot_preparer', self.preparer_depot)
        f.addWidget(self.b_depot)
        f.addWidget(bouton('pt_depot_lire_entete', self._depot_lire_entete))
        v.addLayout(f)
        self.l_depot = aide(QLabel(''), 'pt_depot_etat_aide')
        self.l_depot.setWordWrap(True)
        v.addWidget(self.l_depot)
        v.addStretch(1)
        from ...gui.adaptatif import defilable
        return defilable(w)

    # ================================================================================================ partages
    def _remplir_partages(self, choisir: str = ''):
        liste_p = etat.lister()
        courant = choisir or (self.session.ident if self.session else '')
        if not courant:
            from ...core.etat_interface import etat as etat_ui
            courant = etat_ui().lire('modules.partages.courant', '', str)
        self.c_partages.blockSignals(True)
        self.c_partages.clear()
        for x in liste_p:
            self.c_partages.addItem(x.nom, x.ident)
        k = max(0, self.c_partages.findData(courant)) if liste_p else -1
        self.c_partages.setCurrentIndex(k)
        self.c_partages.blockSignals(False)
        if not liste_p:
            self.session = None
            self.arbre.clear()
            self.l_droits.setText(html.escape(tr('pt_aucun_partage')))
            self._maj_guide()
            self._afficher([])
            return
        self._partage_choisi()

    def _partage_choisi(self):
        ident = self.c_partages.currentData()
        if not ident or (self.session is not None and self.session.ident == ident):
            return
        x = etat.trouver(ident)
        if x is None:
            return
        from ...core.etat_interface import etat as etat_ui
        etat_ui().ecrire('modules.partages.courant', ident)
        from .session import Session
        self._arret_liste.set()
        self._arret_liste = enregistrer_arret(threading.Event())
        self.session = Session(x)
        self.l_droits.setText(html_droits(x.droits) if x.droits else '')
        if self.session.depuis_cache() is not None:
            self._structure_prete(self.session.structure, cache=True)
        self.rafraichir()

    def ajouter_partage(self):
        d = DialogueAjout(self)
        if d.exec() != QDialog.DialogCode.Accepted or d.info is None:
            return
        x = etat.ajouter(d.e_nom.text(), d.e_lien.text(), d.e_mdp.text(), d.info.droits)
        self.session = None
        self._remplir_partages(x.ident)
        self.statut(tr('pt_ajoute', nom=x.nom))

    def ajouter_partage_direct(self, nom: str, lien: str, mot_de_passe: str = '', droits=None):
        """(Tests, ligne de commande) Ajoute et choisit un partage sans dialogue."""
        x = etat.ajouter(nom, lien, mot_de_passe, droits)
        self.session = None
        self._remplir_partages(x.ident)
        return x

    def _menu_gerer(self):
        m = QMenu(self.b_gerer)
        actif = self.session is not None
        ouvrir.action(m, tr('pt_renommer'), actif, tr('pt_renommer_aide')).triggered.connect(self.renommer_partage)
        ouvrir.action(m, tr('pt_verifier'), actif, tr('pt_verifier_aide')).triggered.connect(self.verifier_partage)
        ouvrir.action(m, tr('pt_copier_lien'), actif, tr('pt_copier_lien_aide')).triggered.connect(self.copier_lien)
        m.addSeparator()
        ouvrir.action(m, tr('pt_oublier'), actif, tr('pt_oublier_aide')).triggered.connect(self.oublier_partage)
        ouvrir.montrer_menu(m, self.b_gerer.mapToGlobal(self.b_gerer.rect().bottomLeft()))

    def renommer_partage(self):
        from PyQt6.QtWidgets import QInputDialog
        if self.session is None:
            return
        nom, ok = QInputDialog.getText(self, tr('pt_renommer'), tr('pt_renommer_question'),
                                       text=self.session.memorise.nom)
        if ok and nom.strip():
            etat.renommer(self.session.ident, nom)
            self.session.memorise.nom = nom.strip()
            self._remplir_partages(self.session.ident)

    def copier_lien(self):
        from PyQt6.QtWidgets import QApplication
        if self.session is not None:
            QApplication.clipboard().setText(self.session.partage.lien())
            self.statut(tr('pt_lien_copie'))

    def oublier_partage(self):
        if self.session is None:
            return
        if not self._confirmer(tr('pt_oublier_question', nom=self.session.memorise.nom), tr('pt_oublier')):
            return
        etat.retirer(self.session.ident)
        self.session = None
        self._remplir_partages()

    def verifier_partage(self):
        if self.session is None:
            return
        s = self.session
        t = Tache(s.verifier, parent=self)
        t.quand_fini(lambda info: self.l_droits.setText(html_droits(info.droits)))
        t.quand_erreur(self._erreur_reseau)
        self._taches.append(t)
        t.start()

    # ================================================================================================ liste
    def rafraichir(self):
        if self.session is None:
            return
        s = self.session
        arret = self._arret_liste
        self.b_rafraichir.setEnabled(False)
        self.statut(tr('pt_lecture'))

        def travail():
            info = s.verifier()
            st = s.rafraichir(arret, lambda n, m: self._evts({'genre': 'liste', 'dossiers': n, 'fichiers': m}))
            return info, st
        t = Tache(travail, parent=self)
        t.quand_fini(lambda r, s=s: self._liste_lue(s, r))
        t.quand_erreur(self._erreur_reseau)
        self._taches.append(t)
        t.start()

    def _liste_lue(self, s, r):
        self.b_rafraichir.setEnabled(True)
        if s is not self.session:
            return
        info, st = r
        self.l_droits.setText(html_droits(info.droits))
        self._structure_prete(st)

    def _erreur_reseau(self, texte):
        self.b_rafraichir.setEnabled(True)
        cle = ''
        for mot in texte.replace('(', ' ').split():
            if mot.startswith('pt_err_'):
                cle = mot
                break
        self.statut(tr(cle) if cle else tr('pt_erreur', erreur=texte[:200]))

    def _structure_prete(self, st, cache=False):
        from .telechargement import possedes
        self.possedes = possedes(self._sortie(), self.session.ident)
        self._remplir_arbre(st)
        r = st.resume()
        self.l_resume.setText(tr('pt_resume', n=r['fichiers'], d=r['dossiers'], o=taille_lisible(r['octets']),
                                 s=r['series'], obs=r['observateurs'], t=r['tableaux']))
        nouveaux = r['nouveaux']
        self.bandeau.setVisible(bool(nouveaux))
        if nouveaux:
            self.l_bandeau.setText(tr('pt_nouveautes', n=nouveaux))
        self._remplir_tableaux(st)
        self._remplir_depot(st)
        self._choisir_outil()
        if self._noeud is None:
            self._choisir_noeud(('nouveaux', '') if nouveaux else ('dossier', ''))
        else:
            self._choisir_noeud(self._noeud)
        self.statut(tr('pt_lu_cache' if cache else 'pt_lu', nom=self.session.memorise.nom))
        if etat.vus(self.session.ident) is None and not cache:
            self.session.marquer_vus()                  # première visite : tout est « vu », rien de « nouveau »
        self._maj_guide()

    def marquer_vus(self):
        if self.session is not None:
            self.session.marquer_vus()
            self.bandeau.setVisible(False)
            self._remplir_arbre(self.session.structure)
            self.modele.invalider()
            self._afficher(self.selection_noeud())

    # ------------------------------------------------------------------ arbre
    def _remplir_arbre(self, st):
        self.arbre.blockSignals(True)
        self.arbre.clear()
        nouveaux = [f for f in st.fichiers if f.nouveau]
        if nouveaux:
            it = QTreeWidgetItem([tr('pt_n_nouveaux', n=len(nouveaux))])
            it.setData(0, ROLE, ('nouveaux', ''))
            it.setToolTip(0, tr('pt_n_nouveaux_aide'))
            self.arbre.addTopLevelItem(it)
        if st.tableaux:
            it = QTreeWidgetItem([tr('pt_n_tableaux', n=len(st.tableaux))])
            it.setData(0, ROLE, ('tableaux', ''))
            it.setToolTip(0, tr('pt_n_tableaux_aide'))
            self.arbre.addTopLevelItem(it)
        racine = QTreeWidgetItem([tr('pt_n_tout', n=len(st.fichiers), o=taille_lisible(st.racine.taille()))])
        racine.setData(0, ROLE, ('dossier', ''))
        racine.setToolTip(0, tr('pt_n_tout_aide'))
        self.arbre.addTopLevelItem(racine)
        self._ajouter_dossiers(racine, st.racine, st)
        racine.setExpanded(True)
        self.arbre.blockSignals(False)

    def _ajouter_dossiers(self, parent_item, d, st):
        for sd in d.sous_dossiers:
            fs = sd.tous_les_fichiers()
            date = ''
            if sd.date is not None:
                date = str(sd.date.year) if sd.annee_seule else sd.date.strftime('%d/%m/%Y')
            it = QTreeWidgetItem([tr('pt_n_dossier', nom=sd.nom, n=len(fs), o=taille_lisible(sd.taille()))])
            it.setData(0, ROLE, ('dossier', sd.chemin))
            bulle = [tr('pt_n_dossier_aide', chemin=sd.chemin)]
            if date:
                bulle.append(tr('pt_n_date', date=date))
            if sd.lieu:
                bulle.append(tr('pt_n_lieu', lieu=sd.lieu))
            if sd.observateur:
                bulle.append(tr('pt_n_observateur', nom=sd.observateur))
            it.setToolTip(0, '\n'.join(bulle))
            if any(f.nouveau for f in fs):
                it.setForeground(0, pastilles.couleur_statut('partiel'))
            parent_item.addChild(it)
            for s in [x for x in st.series if x.dossier == sd.chemin]:
                g = s.genres()
                txt = tr('pt_n_serie', obs=s.observateur or tr('pt_inconnu'), debut=s.debut.strftime('%H:%M:%S'),
                         fin=s.fin.strftime('%H:%M:%S'), n=len(s.fichiers),
                         genres=', '.join('%d %s' % (v, tr('pt_genre_' + k)) for k, v in sorted(g.items())))
                si = QTreeWidgetItem([txt])
                si.setData(0, ROLE, ('serie', s.ident))
                si.setToolTip(0, tr('pt_n_serie_aide', date=s.debut.strftime('%d/%m/%Y'),
                                    cible=tr('pt_cible_' + s.cible) if s.cible else tr('pt_inconnue')))
                it.addChild(si)
            self._ajouter_dossiers(it, sd, st)
            it.setExpanded(True)

    def _noeud_choisi(self):
        it = self.arbre.currentItem()
        if it is None:
            return
        self._noeud = it.data(0, ROLE)
        self._afficher(self.selection_noeud())

    def _choisir_noeud(self, n):
        self._noeud = n
        trouve = None
        for it in self._items():
            if it.data(0, ROLE) == n:
                trouve = it
                break
        if trouve is not None:
            self.arbre.setCurrentItem(trouve)
        self._afficher(self.selection_noeud())

    def _items(self):
        pile = [self.arbre.topLevelItem(k) for k in range(self.arbre.topLevelItemCount())]
        while pile:
            it = pile.pop(0)
            yield it
            pile.extend(it.child(k) for k in range(it.childCount()))

    def selection_noeud(self) -> list:
        if self.session is None or self.session.structure is None or self._noeud is None:
            return []
        st = self.session.structure
        genre, cle = self._noeud
        if genre == 'nouveaux':
            return [f for f in st.fichiers if f.nouveau]
        if genre == 'tableaux':
            return list(st.tableaux)
        if genre == 'serie':
            s = next((x for x in st.series if x.ident == cle), None)
            return list(s.fichiers) if s else []
        d = st.dossiers.get(cle)
        return d.tous_les_fichiers() if d else []

    def _menu_arbre(self, pos):
        it = self.arbre.itemAt(pos)
        if it is None:
            return
        self.arbre.setCurrentItem(it)
        fs = self.selection_noeud()
        m = QMenu(self.arbre)
        n = len([f for f in fs if f.chemin not in self.possedes])
        a = ouvrir.action(m, tr('pt_menu_telecharger_tout', n=n, o=taille_lisible(sum(f.taille for f in fs))),
                          n > 0, tr('pt_telecharger_aide'))
        a.triggered.connect(lambda: self.telecharger(fs))
        ouvrir.action(m, tr('pt_menu_entetes'), any(f.genre == 'fits' for f in fs),
                      tr('pt_menu_entetes_aide')).triggered.connect(lambda: self.lire_entetes(fs))
        ouvrir.montrer_menu(m, self.arbre.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------------ table des fichiers
    def _afficher(self, fichiers_):
        self.modele.remplir_objets(list(fichiers_))
        self._selection()

    def _ligne(self, f):
        etat_ = tr('pt_etat_possede') if f.chemin in self.possedes else (tr('pt_etat_nouveau') if f.nouveau else '')
        instant = _heure(f.instant)
        if instant and f.instant_source == 'nom':
            instant += ' ' + tr('pt_heure_nom_court')
        if f.doute:
            instant += ' ?'
        return (etat_, f.nom, tr('pt_genre_' + f.genre) + (' ' + tr('pt_annote') if f.annotation else ''),
                taille_lisible(f.taille), instant, f.observateur, tr('pt_cible_' + f.cible) if f.cible else '',
                f.dossier)

    def _style(self, f):
        if f.chemin in self.possedes:
            return {'couleurs': {0: pastilles.couleur_statut('ok')}}
        if f.nouveau:
            return {'couleurs': {0: pastilles.couleur_statut('partiel')}}
        return {}

    def _bulle(self, f):
        t = [f.chemin]
        if f.instant_source == 'nom':
            t.append(tr('pt_heure_nom'))
        if f.doute:
            t.append(tr('pt_heure_douteuse'))
        if f.annotation:
            t.append(tr('pt_annotation_aide'))
        return '\n'.join(t)

    def _cle(self, f, col):
        nom = COLONNES[col]
        if nom == 'taille':
            return (0, float(f.taille), '')
        if nom == 'instant':
            return (0, f.instant.timestamp(), '') if f.instant else (1, 0.0, '')
        return None

    def choisis(self) -> list:
        from ...gui.modele import lignes_choisies
        return lignes_choisies(self.vue, self.proxy, self.modele)

    def _selection(self):
        sel = self.choisis()
        self.selection = sel or list(self.modele.donnees)
        n = len(self.selection)
        o = sum(f.taille for f in self.selection)
        manquants = [f for f in self.selection if f.chemin not in self.possedes]
        self.l_selection.setText(tr('pt_selection', n=n, o=taille_lisible(o)) if n else '')
        self._maj_bouton()
        if len(sel) == 1:
            self._fiche(sel[0])
            self._apercu()
        elif not sel:
            self.fiche.setHtml('')
            self.l_apercu.setPixmap(QPixmap())
            self.l_apercu.setText(tr('pt_apercu_rien'))
            self.b_apercu.setVisible(False)
        self._maj_guide()
        return manquants

    def _maj_bouton(self):
        manquants = [f for f in self.selection if f.chemin not in self.possedes]
        if self.occupe():
            self.b_telecharger.setText(tr('pt_telechargement_en_cours'))
            self.b_telecharger.setEnabled(False)
        elif not self.selection:
            self.b_telecharger.setText(tr('pt_telecharger'))
            self.b_telecharger.setEnabled(False)
        elif not manquants:
            self.b_telecharger.setText(tr('pt_deja'))
            self.b_telecharger.setEnabled(False)
        else:
            self.b_telecharger.setText(tr('pt_telecharger_n', n=len(manquants),
                                          o=taille_lisible(sum(f.taille for f in manquants))))
            self.b_telecharger.setEnabled(True)

    def _fiche(self, f):
        e = html.escape
        h = ['<p><b>%s</b></p>' % e(f.nom), '<p>%s</p>' % e(f.dossier or '/')]
        h.append('<p>%s : %s · %s</p>' % (e(tr('pt_col_genre')), e(tr('pt_genre_' + f.genre)),
                                           e(taille_lisible(f.taille))))
        if f.instant:
            h.append('<p>%s : %s UTC%s</p>' % (e(tr('pt_col_instant')), e(_heure(f.instant)),
                                               ' — ' + e(tr('pt_heure_nom')) if f.instant_source == 'nom' else ''))
        if f.observateur:
            h.append('<p>%s : %s</p>' % (e(tr('pt_col_observateur')), e(f.observateur)))
        ent = self.session.entetes.get(f.chemin) if self.session else None
        if ent:
            h.append('<p>%s</p>' % e(tr('pt_fiche_entete', lat=_dec(ent['lat'], 4) if ent.get('lat') is not None
                                        else '—', lon=_dec(ent['lon'], 4) if ent.get('lon') is not None else '—',
                                        t=ent.get('milieu') or '—', objet=ent.get('objet') or '—',
                                        wcs=tr('pt_oui') if ent.get('wcs') else tr('pt_non'))))
        if f.chemin in self.possedes:
            h.append('<p>%s</p>' % e(tr('pt_fiche_local', chemin=self.possedes[f.chemin])))
        self.fiche.setHtml(''.join(h))

    def _apercu(self, forcer=False):
        sel = self.choisis()
        if len(sel) != 1 or self.session is None:
            return
        f = sel[0]
        self._apercu_jeton += 1
        jeton = self._apercu_jeton
        self.b_apercu.setVisible(False)
        if f.genre not in S.APERCU_POSSIBLE:
            self.l_apercu.setPixmap(QPixmap())
            self.l_apercu.setText(tr('pt_ap_genre'))
            return
        self.l_apercu.setPixmap(QPixmap())
        self.l_apercu.setText(tr('pt_apercu_calcul'))
        from .apercus import apercu
        s = self.session

        def travail():
            try:
                return apercu(s, f, forcer)
            except SansApercu as e:
                return e.cle
        t = Tache(travail, parent=self)
        t.quand_fini(lambda r, j=jeton: self._apercu_pret(j, r))
        t.quand_erreur(lambda e, j=jeton: self._apercu_pret(j, 'pt_ap_illisible'))
        self._taches.append(t)
        t.start()

    def _apercu_pret(self, jeton, r):
        if jeton != self._apercu_jeton:
            return
        if isinstance(r, str):
            self.l_apercu.setPixmap(QPixmap())
            self.l_apercu.setText(tr(r))
            self.b_apercu.setVisible(r == 'pt_ap_trop_grand')
            return
        pm = QPixmap.fromImage(r)
        w = max(120, self.l_apercu.width() - 8)
        h = max(100, self.l_apercu.height() - 8)
        self.l_apercu.setPixmap(pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))

    def _double_clic(self):
        sel = self.choisis()
        if len(sel) != 1:
            return
        f = sel[0]
        if f.genre == 'tableau':
            self.ouvrir_tableau(f.chemin)
            return
        if f.chemin in self.possedes:
            ouvrir.ouvrir_defaut(self.possedes[f.chemin])
            return
        if self._confirmer(tr('pt_proposer', nom=f.nom, o=taille_lisible(f.taille)), tr('pt_telecharger')):
            self.telecharger([f])

    def _menu_fichiers(self, pos):
        sel = self.choisis()
        if not sel:
            return
        m = QMenu(self.vue)
        manquants = [f for f in sel if f.chemin not in self.possedes]
        a = ouvrir.action(m, tr('pt_menu_telecharger', n=len(manquants),
                                o=taille_lisible(sum(f.taille for f in manquants))),
                          bool(manquants) and not self.occupe(), tr('pt_telecharger_aide'), tr('pt_deja_aide'),
                          tr('pt_motif_deja'))
        a.triggered.connect(lambda: self.telecharger(sel))
        un = sel[0] if len(sel) == 1 else None
        ouvrir.action(m, tr('pt_menu_apercu'), un is not None and un.genre in S.APERCU_POSSIBLE,
                      tr('pt_apercu_aide')).triggered.connect(lambda: self._apercu(forcer=True))
        ouvrir.action(m, tr('pt_menu_entetes'), any(f.genre == 'fits' for f in sel),
                      tr('pt_menu_entetes_aide')).triggered.connect(lambda: self.lire_entetes(sel))
        ouvrir.action(m, tr('pt_menu_tableau'), un is not None and un.genre == 'tableau',
                      tr('pt_menu_tableau_aide')).triggered.connect(lambda: self.ouvrir_tableau(un.chemin))
        if self.outil_panneau is not None and hasattr(self.outil_panneau, 'actions_menu'):
            m.addSeparator()
            self.outil_panneau.actions_menu(m, sel)
        if un is not None and un.chemin in self.possedes:
            m.addSeparator()
            ouvrir.remplir_menu(m, self.possedes[un.chemin])
        m.addSeparator()
        ouvrir.action(m, tr('pt_menu_copier'), True, tr('pt_menu_copier_aide')).triggered.connect(
            lambda: self._copier('\n'.join(f.chemin for f in sel)))
        ouvrir.montrer_menu(m, self.vue.viewport().mapToGlobal(pos))

    def _copier(self, texte):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(texte)

    # ------------------------------------------------------------------ en-têtes
    def lire_entetes(self, fichiers_):
        if self.session is None:
            return
        fits_ = [f for f in fichiers_ if f.genre == 'fits']
        s = self.session

        def travail():
            n = 0
            for f in fits_:
                if self._arret_liste.is_set():
                    break
                try:
                    s.lire_entete_fits(f.chemin)
                    n += 1
                except Exception:
                    continue
                self._evts({'genre': 'entete', 'n': n, 'total': len(fits_)})
            return n
        t = Tache(travail, parent=self)
        t.quand_fini(lambda n: self._entetes_lues(n))
        t.quand_erreur(self._erreur_reseau)
        self._taches.append(t)
        self.statut(tr('pt_entetes_lecture', n=len(fits_)))
        t.start()

    def _entetes_lues(self, n):
        self.statut(tr('pt_entetes_lues', n=n))
        if self.session and self.session.structure:
            self._afficher(self.selection_noeud())
        if self.outil_panneau is not None and hasattr(self.outil_panneau, 'donnees_changees'):
            self.outil_panneau.donnees_changees()

    # ================================================================================================ télécharger
    def _sortie(self) -> str:
        from .telechargement import sortie_par_defaut
        return memoire.dossier('modules.partages.sortie', sortie_par_defaut())

    def choisir_dossier(self) -> str:
        d = fichiers.choisir_dossier(self, tr('pt_choisir_dossier'), self._sortie())
        if d:
            memoire.retenir('modules.partages.sortie', d)
            self.l_dossier.setText(coupable(d))
            if self.session:
                from .telechargement import possedes
                self.possedes = possedes(d, self.session.ident)
                self._afficher(self.selection_noeud())
        return d

    def telecharger(self, fichiers_=None):
        if self.session is None or self.occupe():
            return
        fs = [f for f in (fichiers_ if fichiers_ is not None else self.selection) if f.chemin not in self.possedes]
        if not fs:
            self.statut(tr('pt_rien_a_telecharger'))
            return
        if not memoire.dossier('modules.partages.sortie', '') and not os.environ.get('COUPOLE_SANS_DIALOGUE'):
            if not self.choisir_dossier():
                return
        from .telechargement import Telechargement
        astrometrie, en_ligne = self.c_astrometrie.currentData(), False
        if astrometrie == 'en_ligne':
            astrometrie, en_ligne = 'auto', self.accord_en_ligne(fs)
            if en_ligne is None:
                return
        self._arret_dl = enregistrer_arret(threading.Event())
        self._pause_dl.clear()
        self._octets_total = sum(f.taille for f in fs)
        self._t0 = D.datetime.now()
        dl = Telechargement(self.session, fs, self._sortie(), self.c_format.currentData(), self.c_garder.isChecked(),
                            astrometrie, 0.0, 3, self._evts, self._arret_dl, self._pause_dl, en_ligne)
        self.b_pause.setEnabled(True)
        self.b_annuler.setEnabled(True)
        self.barre.setValue(0)
        self.barre.setFormat('%p %')
        self._fil_dl = lancer_fil(dl.executer)
        self._maj_bouton()
        self.statut(tr('pt_dl_debut', n=len(fs), o=taille_lisible(self._octets_total)))

    def accord_en_ligne(self, fs) -> bool | None:
        """Astrométrie en ligne : clé d'API présente, puis accord explicite avant tout envoi (service tiers).
        Rend True (accord), False (pas de FITS concerné) ou None (refus : rien ne part)."""
        from ...core import nova
        if not any(f.genre == 'fits' for f in fs):
            return False
        if not nova.configure():
            self.statut(tr('pt_nova_sans_cle'))
            return None
        vis = tr('pt_nova_publiques' if nova.reglages()['public'] else 'pt_nova_privees')
        return True if self._confirmer(tr('pt_nova_accord', visibilite=vis), tr('pt_nova_accord_titre')) else None

    def pause(self):
        if self._pause_dl.is_set():
            self._pause_dl.clear()
            self.b_pause.setText(tr('pt_pause'))
        else:
            self._pause_dl.set()
            self.b_pause.setText(tr('pt_reprendre'))

    def annuler(self):
        self._arret_dl.set()
        self._pause_dl.clear()

    def ouvrir_dossier(self):
        d = self._sortie()
        os.makedirs(d, exist_ok=True)
        ouvrir.ouvrir_defaut(d)

    def _evenements(self, evs):
        fin = None
        for ev in evs:
            g = ev.get('genre')
            if g == 'octets' and self._octets_total:
                self.barre.setValue(int(1000 * min(1.0, ev['octets'] / self._octets_total)))
                dt = max(0.1, (D.datetime.now() - self._t0).total_seconds())
                self.l_progres.setText(tr('pt_dl_progres', o=taille_lisible(ev['octets']),
                                          t=taille_lisible(self._octets_total),
                                          d=_dec(ev['octets'] / dt / 1e6, 1)))
            elif g == 'fini':
                self.possedes[ev['chemin']] = ev['local']
            elif g == 'erreur':
                self.l_progres.setText(tr('pt_dl_erreur', chemin=ev.get('chemin', ''), erreur=ev.get('erreur', '')))
            elif g == 'fin':
                fin = ev['bilan']
            elif g == 'liste':
                self.statut(tr('pt_lecture_n', d=ev['dossiers'], f=ev['fichiers']))
            elif g == 'entete':
                self.statut(tr('pt_entetes_progres', n=ev['n'], t=ev['total']))
        if fin is not None:
            self.b_pause.setEnabled(False)
            self.b_annuler.setEnabled(False)
            self.barre.setValue(1000)
            self.statut(tr('pt_dl_fin', ok=fin.get('ok', 0), deja=fin.get('deja', 0), echec=fin.get('echec', 0),
                           annule=fin.get('annule', 0), dossier=fin.get('dossier', '')))
            self._fil_dl = None
            self._afficher(self.selection_noeud())
            self._maj_guide()
        if evs:
            self._maj_bouton()

    # ================================================================================================ mesures
    def _remplir_tableaux(self, st):
        self.c_tableaux.blockSignals(True)
        courant = self.c_tableaux.currentData()
        self.c_tableaux.clear()
        for f in st.tableaux:
            self.c_tableaux.addItem(f.chemin, f.chemin)
        k = self.c_tableaux.findData(courant)
        self.c_tableaux.setCurrentIndex(k if k >= 0 else (0 if st.tableaux else -1))
        self.c_tableaux.blockSignals(False)
        self._tableau_choisi()

    def _tableau_choisi(self):
        c = self.c_tableaux.currentData()
        if c and self.session and c in self.session.tableaux:
            self._remplir_mesures()
        else:
            self.modele_m.remplir_objets([])
            self.l_mesures.setText(tr('pt_mesures_pas_lu') if c else '')

    def ouvrir_tableau(self, chemin):
        k = self.c_tableaux.findData(chemin)
        if k >= 0:
            self.c_tableaux.setCurrentIndex(k)
        self.onglets.setCurrentIndex(1)
        self.lire_tableau()

    def lire_tableau(self):
        c = self.c_tableaux.currentData()
        if not c or self.session is None:
            return
        s = self.session
        self.statut(tr('pt_tableau_lecture', chemin=c))
        t = Tache(s.lire_tableau, c, parent=self)
        t.quand_fini(lambda r: self._tableau_lu(c))
        t.quand_erreur(self._erreur_reseau)
        self._taches.append(t)
        t.start()

    def _tableau_lu(self, chemin):
        self._remplir_mesures()
        self._choisir_outil()
        if self.outil_panneau is not None and hasattr(self.outil_panneau, 'donnees_changees'):
            self.outil_panneau.donnees_changees()
        self._remplir_depot(self.session.structure)
        self.statut(tr('pt_tableau_lu', chemin=chemin))

    def tableaux_mesures(self) -> list:
        return self.session.tableaux_de_mesures() if self.session else []

    def _remplir_mesures(self):
        c = self.c_tableaux.currentData()
        if not c or self.session is None or c not in self.session.tableaux:
            return
        _, ts = self.session.tableaux[c]
        lignes = [m for t in ts for m in t.mesures]
        if self.c_a_verifier.isChecked():
            lignes = [m for m in lignes if m.niveau in ('erreur', 'attention')]
        self.modele_m.remplir_objets(lignes)
        if not ts:
            self.l_mesures.setText(tr('pt_mesures_pas_tableau'))
            return
        r = {'lignes': 0, 'erreur': 0, 'attention': 0, 'info': 0}
        for t in ts:
            for k, v in t.resume().items():
                r[k] = r.get(k, 0) + v
        self.l_mesures.setText(tr('pt_mesures_resume', n=r['lignes'], e=r['erreur'], a=r['attention'], i=r['info']))

    def _ligne_m(self, m):
        ap = self.c_corrections.isChecked()

        def val(champ, chiffres=4):
            v = m.retenu(champ, ap)
            if v is None:
                return ''
            t = _dec(v, chiffres) if isinstance(v, float) else str(v)
            return t + (' *' if ap and champ in m.corrections else '')
        inst = m.retenu('instant', ap)
        return (str(m.ligne), tr('pt_niveau_' + m.niveau), m.cible_brute, m.auteur,
                (_heure(inst) + (' *' if ap and 'instant' in m.corrections else '')) if inst else '',
                val('lat'), val('lon'), val('alt_m', 0), val('az', 2), val('h', 2), m.fichier,
                ' · '.join(texte_anomalie(a) for a in m.anomalies if a.niveau != 'info')[:400])

    def _style_m(self, m):
        n = {'erreur': 'echec', 'attention': 'partiel', 'ok': 'ok'}.get(m.niveau)
        st = {'couleurs': {1: pastilles.couleur_statut(n)}} if n else {}
        st['bulles'] = {11: '\n'.join(texte_anomalie(a) for a in m.anomalies)}
        return st

    def _corrections(self, oui):
        self.appliquer_corrections = bool(oui)
        self.modele_m.invalider()
        self._remplir_mesures()
        if self.outil_panneau is not None and hasattr(self.outil_panneau, 'donnees_changees'):
            self.outil_panneau.donnees_changees()

    def exporter_csv(self):
        import csv
        c = self.c_tableaux.currentData()
        if not c or self.session is None or c not in self.session.tableaux:
            return
        chemin, _ = fichiers.choisir_enregistrement(self, tr('pt_exporter_csv'), os.path.join(
            self._sortie(), os.path.splitext(os.path.basename(c))[0] + '_normalise.csv'), 'CSV (*.csv)')
        if not chemin:
            return
        _, ts = self.session.tableaux[c]
        with open(chemin, 'w', newline='', encoding='utf-8-sig') as fh:
            w = csv.writer(fh, delimiter=';')
            w.writerow([tr('pt_m_' + x) for x in COL_MESURES])
            for t in ts:
                for m in t.mesures:
                    w.writerow(self._ligne_m(m))
        self.statut(tr('pt_exporte', chemin=chemin))

    # ================================================================================================ analyse
    def _choisir_outil(self):
        from .analyses import detecter, outil
        if self.session is None or self.session.structure is None:
            return
        choix = self.session.memorise.outil
        o = outil(choix) if choix else None
        if o is None:
            r = detecter(self.session.structure, self.tableaux_mesures())
            o = r[0][0] if r else None
        lay = self.onglet_analyse.layout()
        if self.outil_panneau is not None and getattr(self.outil_panneau, 'outil_id', '') == getattr(o, 'id', None):
            return
        while lay.count():
            w = lay.takeAt(0).widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        h = QHBoxLayout()
        bandeau = QWidget()
        bandeau.setLayout(h)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(QLabel(tr('pt_outil')))
        from .analyses import outils
        self.c_outil = liste('pt_outil_aide', [(tr(x.cle_nom), x.id) for x in outils()])
        if o is not None:
            self.c_outil.setCurrentIndex(max(0, self.c_outil.findData(o.id)))
        self.c_outil.currentIndexChanged.connect(lambda *_: self._outil_change())
        h.addWidget(self.c_outil)
        raisons = o.raisons(self.session.structure, self.tableaux_mesures()) if o else []
        lab = QLabel(tr('pt_outil_detecte', raisons=', '.join(tr(r) for r in raisons)) if raisons else
                     tr('pt_outil_choisi'))
        lab.setWordWrap(True)
        h.addWidget(lab, 1)
        lay.addWidget(bandeau)
        self.outil_panneau = o.panneau(self.onglet_analyse, self) if o is not None else None
        if self.outil_panneau is not None:
            self.outil_panneau.outil_id = o.id
            lay.addWidget(self.outil_panneau, 1)

    def _outil_change(self):
        if self.session is None:
            return
        etat.modifier(self.session.ident, outil=self.c_outil.currentData())
        self.session.memorise.outil = self.c_outil.currentData()
        self.outil_panneau = None
        self._choisir_outil()

    # ================================================================================================ dépôt
    def _remplir_depot(self, st):
        if st is None:
            return
        self.c_depot_dossier.clear()
        for chemin in sorted(st.dossiers):
            self.c_depot_dossier.addItem(chemin or '/', chemin)
        self.c_depot_tableau.blockSignals(True)
        self.c_depot_tableau.clear()
        self.c_depot_tableau.addItem(tr('pt_depot_sans_tableau'), '')
        for c, (_, ts) in (self.session.tableaux.items() if self.session else []):
            for t in ts:
                self.c_depot_tableau.addItem('%s — %s' % (c, t.feuille), (c, t.feuille))
        if self.c_depot_tableau.count() > 1:
            self.c_depot_tableau.setCurrentIndex(1)
        self.c_depot_tableau.blockSignals(False)
        droits = self.session.memorise.droits if self.session else []
        if self.session and self.session.info is not None:
            droits = self.session.info.droits
        ok = 'deposer' in droits or 'ecrire' in droits
        self.l_depot_droits.setText(tr('pt_depot_permis') if ok else tr('pt_depot_interdit'))
        self.b_depot.setEnabled(ok)

    def _depot_ajouter(self):
        d = memoire.dossier('modules.partages.depot', os.path.expanduser('~'))
        chemin, _ = fichiers.choisir_fichier(self, tr('pt_depot_ajouter'), d)
        if chemin:
            memoire.retenir('modules.partages.depot', chemin, est_fichier=True)
            self.l_depot_fichiers.addItem(chemin)

    def _depot_retirer(self):
        for it in self.l_depot_fichiers.selectedItems():
            self.l_depot_fichiers.takeItem(self.l_depot_fichiers.row(it))

    def depot_fichiers(self) -> list:
        return [self.l_depot_fichiers.item(k).text() for k in range(self.l_depot_fichiers.count())]

    def _depot_lire_entete(self):
        """Pré-remplit lieu et heure d'après l'en-tête FITS du premier fichier choisi."""
        fs = [x for x in self.depot_fichiers() if x.lower().endswith(('.fits', '.fit', '.fts'))]
        if not fs:
            self.l_depot.setText(tr('pt_depot_pas_fits'))
            return
        from .analyses.parallaxe.image import lieu_et_heure
        from .session import analyser_cartes
        with open(fs[0], 'rb') as fh:
            lh = lieu_et_heure(analyser_cartes(fh.read(2880 * 12)))
        if lh['milieu']:
            self.e_depot['date'].setText(lh['milieu'].strftime('%Y-%m-%d %H:%M:%S'))
        for role, cle in (('latitude', 'lat'), ('longitude', 'lon'), ('altitude', 'alt_m')):
            if lh[cle] is not None:
                self.e_depot[role].setText(('%.6f' % lh[cle]).rstrip('0').rstrip('.'))
        self.l_depot.setText(tr('pt_depot_entete_lu'))

    def mesure_saisie(self) -> dict:
        from .mesures import angle, instant, nombre
        m = {'auteur': self.e_depot['auteur'].text().strip(), 'cible': self.e_depot['cible'].text().strip()}
        t = self.e_depot['date'].text().strip()
        if t:
            v = instant(t + ('' if any(x in t.upper() for x in ('UTC', 'TU', 'Z')) else ' UTC'))
            m['date'] = v.valeur
        for role in ('latitude', 'longitude', 'azimut', 'hauteur'):
            x = self.e_depot[role].text().strip()
            if x:
                m[role] = angle(x).valeur
        x = self.e_depot['altitude'].text().strip()
        if x:
            m['altitude'] = nombre(x).valeur
        return m

    def preparer_depot(self):
        if self.session is None:
            return
        fs = self.depot_fichiers()
        dossier = self.c_depot_dossier.currentText().strip()
        dossier = '' if dossier == '/' else dossier.strip('/')
        choix = self.c_depot_tableau.currentData()
        tab, tableau = '', None
        if choix:
            tab, feuille = choix
            tableau = next((t for t in self.session.tableaux[tab][1] if t.feuille == feuille), None)
        mesure = self.mesure_saisie()
        if not fs and not tableau:
            self.l_depot.setText(tr('pt_depot_rien'))
            return
        if tableau is not None and (not mesure.get('date') or mesure.get('latitude') is None
                                    or mesure.get('longitude') is None):
            self.l_depot.setText(tr('pt_depot_incomplet'))
            return
        s = self.session
        from . import depot

        def travail():
            return depot.preparer(s, dossier, fs, tab, tableau, mesure, mesure.get('auteur', ''))
        t = Tache(travail, parent=self)
        t.quand_fini(self._plan_pret)
        t.quand_erreur(self._erreur_reseau)
        self._taches.append(t)
        self.l_depot.setText(tr('pt_depot_preparation'))
        t.start()

    def texte_plan(self, plan) -> str:
        e = html.escape
        h = ['<p>%s</p>' % e(tr('pt_depot_confirmer_intro', partage=self.session.memorise.nom))]
        if plan.fichiers:
            h.append('<p><b>%s</b></p><ul>' % e(tr('pt_depot_confirmer_fichiers', n=len(plan.fichiers),
                                                   o=taille_lisible(plan.octets()))))
            for f in plan.fichiers:
                h.append('<li>%s → <b>%s</b> (%s)</li>' % (e(os.path.basename(f.local)), e(f.distant),
                                                         e(taille_lisible(f.taille))))
            h.append('</ul>')
        if plan.tableau:
            h.append('<p><b>%s</b></p><table>' % e(tr('pt_depot_confirmer_ligne', tableau=plan.tableau,
                                                      feuille=plan.feuille)))
            for titre, v in plan.colonnes:
                if v:
                    h.append('<tr><td>%s</td><td><b>%s</b></td></tr>' % (e(str(titre)), e(v)))
            h.append('</table><p>%s</p>' % e(tr('pt_depot_confirmer_secours', csv=plan.csv_secours)))
        h.append('<p>%s</p>' % e(tr('pt_depot_confirmer_regles')))
        return ''.join(h)

    def _plan_pret(self, plan):
        self._plan = plan
        if not self._confirmer_html(self.texte_plan(plan), tr('pt_depot_envoyer')):
            self.l_depot.setText(tr('pt_depot_annule'))
            return
        self.executer_depot(plan)

    def executer_depot(self, plan):
        from . import depot
        s = self.session
        sauvegardes = str(s.dossier / 'sauvegardes')
        t = Tache(depot.executer, s, plan, sauvegardes, parent=self)
        t.quand_fini(self._depot_fini)
        t.quand_erreur(self._erreur_depot)
        self._taches.append(t)
        self.l_depot.setText(tr('pt_depot_envoi'))
        t.start()

    def _erreur_depot(self, texte):
        self.l_depot.setText(tr('pt_depot_echec', erreur=texte[:300]))

    def _depot_fini(self, r):
        lignes = [tr('pt_depot_ok_fichiers', n=len(r['fichiers']))]
        if r['tableau'] == 'ligne':
            lignes.append(tr('pt_depot_ok_ligne', ligne=r['ligne'], sauvegarde=r['sauvegarde']))
        elif r['tableau'] == 'csv':
            lignes.append(tr('pt_depot_ok_csv', csv=r['csv'], sauvegarde=r['sauvegarde']))
        self.l_depot.setText('\n'.join(lignes))
        self.rafraichir()

    # ================================================================================================ outils
    def _confirmer(self, texte, titre) -> bool:
        boite = QMessageBox(QMessageBox.Icon.Question, titre, texte, parent=self)
        oui = boite.addButton(titre, QMessageBox.ButtonRole.AcceptRole)
        boite.addButton(tr('dlg_annuler'), QMessageBox.ButtonRole.RejectRole)
        boite.setDefaultButton(oui)
        boite.exec()
        return boite.clickedButton() is oui

    def _confirmer_html(self, html_texte, titre) -> bool:
        from ...gui.dialogues import _boutons, navigateur
        d = QDialog(self)
        d.setWindowTitle(titre)
        v = QVBoxLayout(d)
        v.addWidget(navigateur(html_texte, 'pt_depot_confirmer_aide'), 1)
        bb = _boutons(d)
        from PyQt6.QtWidgets import QDialogButtonBox
        bb.button(QDialogButtonBox.StandardButton.Ok).setText(titre)
        v.addWidget(bb)
        d.resize(720, 520)
        return d.exec() == QDialog.DialogCode.Accepted

    def statut(self, texte):
        self.l_etat.setText(texte)

    def occupe(self):
        return self._fil_dl is not None and self._fil_dl.is_alive()

    def arreter(self):
        self._arret_liste.set()
        self._arret_dl.set()
        self._pause_dl.clear()

    def aide_html(self):
        h = tr('pt_aide_html')
        if self.outil_panneau is not None and hasattr(self.outil_panneau, 'aide_html'):
            h += self.outil_panneau.aide_html()
        return h

