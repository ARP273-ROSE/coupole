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

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QMessageBox, QPlainTextEdit, QProgressBar, QSplitter, QTabWidget, QVBoxLayout, QWidget)

from ...core import config, i18n
from ...core.i18n import tr
from ...gui.adaptatif import Flux, coupable
from ...gui.dialogues import DialogueASTAP, ouvrir_fichier
from ...gui import memoire, pastilles
from ...gui.modele import (DelegueProgression, ModeleParesseux, ModeleTableau, Progression, lignes_choisies,
                           vue_tableau)
from ...gui.outils import (FileEvenements, Tache, aide, bouton, case, champ, decimal, enregistrer_arret, est_detruit,
                           lancer_fil, liste, nombre)
from . import cibles
from .possession import Possession


def _taille(o: float) -> str:
    return tr('taille_go', v='%.2f' % (o / 1e9)) if o >= 1e8 else tr('taille_mo', v='%.1f' % (o / 1e6))


from .gui_sans_qt import duree_lisible  # noqa: E402

# bits du code « drapeaux » d'une image (clé de tri précalculée ; le texte affiché en dépend seul)
_D_DOUBLON, _D_DATE, _D_DIURNE, _D_NOUVEAU = 1, 2, 4, 8


def texte_drapeaux(doublon, date_partagee, diurne, nouveau, vu_le) -> str:
    """Colonne « drapeaux » de la table des images (une seule écriture : affichage et clé de tri)."""
    dr = []
    if doublon:
        dr.append(tr('ohp_drapeau_doublon'))
    if date_partagee:
        dr.append(tr('ohp_drapeau_date'))
    if diurne:
        dr.append(tr('ohp_drapeau_diurne'))
    if nouveau:
        dr.append(tr('ohp_etat_nouveau', date=vu_le))
    return ', '.join(dr)


def cles_de_tri_images(images) -> tuple[dict, dict, list]:
    """Clés de tri des colonnes « heure du site » et « drapeaux », calculées UNE fois par inventaire (fil de fond).

    * heure du site : la cellule affiche « HH:MM:SS (UTC±hhmm) » (vide sans site connu) et se triait comme ce
      texte ; la clé entière ``secondes_du_jour × 100000 + signe × 10000 + hhmm`` (signe 0 pour « + », 1 pour
      « − », comme l'ordre des caractères) donne exactement le même ordre, −1 pour une cellule vide ;
    * drapeaux : un code (bits doublon / date partagée / plein jour / nouveau + rang de la date « vu le ») ; le
      rang du texte affiché est calculé au moment du tri pour les quelques codes distincts (langue courante).

    Rend ({id(image): clé heure}, {id(image): code drapeaux}, [dates « vu le »])."""
    from ...core import sites as sites_mod
    from ...core.temps import mjd_vers_utc
    zones = {s_.id: s_.zone() for s_ in sites_mod.sites()}
    heure, drap, vus, rang_vu = {}, {}, [], {}
    for x in images:
        z = zones.get(x.get('site'))
        if z is None:
            kh = -1
        else:
            loc = mjd_vers_utc(x['t_min']).astimezone(z)
            o = int(loc.utcoffset().total_seconds())
            a = -o if o < 0 else o
            kh = ((loc.hour * 3600 + loc.minute * 60 + loc.second) * 100000 + (10000 if o < 0 else 0)
                  + (a // 3600) * 100 + (a % 3600) // 60)
        c = ((_D_DOUBLON if x['doublon'] else 0) | (_D_DATE if x['date_partagee'] else 0)
             | (_D_DIURNE if x['diurne'] else 0))
        if x['nouveau']:
            v = x['vu_le']
            r = rang_vu.get(v)
            if r is None:
                r = rang_vu[v] = len(vus)
                vus.append(v)
            c |= _D_NOUVEAU | (r << 4)
        i = id(x)
        heure[i] = kh
        drap[i] = c
    return heure, drap, vus


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
        self.possession = Possession.vide()        # ce qu'on possède déjà à destination (lu en fond, jamais bloquant)
        self._infos_ok = []
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
        self._etat_astap = None
        self._memoriser()
        self._charger_apres_premier_dessin()

    # ================================================================ disposition gardée d'une fois à l'autre
    def _memoriser(self):
        """Filtres, recherche, colonnes, séparateur, onglet, objets choisis : rétablis maintenant (ou dès que les
        listes qu'ils visent sont remplies), relus à chaque écriture différée (gui/memoire.py)."""
        from ...core.etat_interface import etat
        e, m, k = etat(), memoire.memoire(), 'modules.ohp.'
        memoire.champ(self.recherche, k + 'recherche')
        memoire.liste(self.f_cat, k + 'type')
        memoire.liste(self.f_tel, k + 'telescope')
        memoire.case(self.f_nouveaux, k + 'nouveaux')
        memoire.case(self.f_verifier, k + 'a_verifier')
        memoire.case(self.f_manquantes, k + 'a_telecharger')
        memoire.case(self.f_dates, k + 'sans_dates_douteuses')
        memoire.case(self.f_anom_nouv, k + 'anomalies_nouvelles')
        memoire.liste(self.ciel_cat, k + 'ciel_type')
        memoire.separateur(self.sp_catalogue, k + 'separateur')
        memoire.entete(self.v_obj, k + 'colonnes_objets')
        memoire.entete(self.v_img, k + 'colonnes_images')
        memoire.entete(self.v_lots, k + 'colonnes_lots')
        memoire.entete(self.v_anom, k + 'colonnes_anomalies')
        memoire.onglets(self.onglets, k + 'onglet')
        # listes remplies plus tard (nuits et filtres des objets choisis, genres d'anomalies), objets choisis
        # (après le chargement de l'inventaire) : valeur « attendue », appliquée une fois, gardée en attendant
        self._nuit_attendue = e.lire(k + 'nuit', None, str) or None
        self._filtre_attendu = e.lire(k + 'filtre', None, str) or None
        self._genre_attendu = e.lire(k + 'genre_anomalie', None, str) or None
        objets = e.lire(k + 'objets', None, list)
        self._objets_attendus = [o for o in objets if isinstance(o, str)][:200] if objets else None
        m.suivre(k + 'nuit', lambda: self._nuit_attendue or self.f_nuit.currentData() or '', self.f_nuit,
                 self.f_nuit.currentIndexChanged)
        m.suivre(k + 'filtre', lambda: self._filtre_attendu or self.f_filtre.currentData() or '', self.f_filtre,
                 self.f_filtre.currentIndexChanged)
        m.suivre(k + 'genre_anomalie', lambda: self._genre_attendu or self.f_genre.currentData() or '',
                 self.f_genre, self.f_genre.currentIndexChanged)
        m.suivre(k + 'objets', lambda: self._objets_attendus if self._objets_attendus is not None
                 else sorted(getattr(self, '_objets', set()))[:200], self.v_obj,
                 self.v_obj.selectionModel().selectionChanged)

    def _restaurer_selection(self):
        """Objets choisis à la dernière fermeture : sélectionnés une fois, au premier remplissage du catalogue."""
        voulus = self._objets_attendus
        if not voulus or not self.m_obj.donnees:
            return
        self._objets_attendus = None
        from PyQt6.QtCore import QItemSelection, QItemSelectionModel
        voulus = set(voulus)
        sel = QItemSelection()
        premier = None
        for r, o in enumerate(self.m_obj.donnees):
            if o['objet'] in voulus:
                idx = self.p_obj.mapFromSource(self.m_obj.index(r, 0))
                if idx.isValid():                    # masqué par les filtres : on ne le force pas
                    sel.select(idx, idx)
                    premier = premier or idx
        if premier is not None:
            self.v_obj.selectionModel().select(sel, QItemSelectionModel.SelectionFlag.ClearAndSelect |
                                               QItemSelectionModel.SelectionFlag.Rows)
            self.v_obj.scrollTo(premier)

    # ================================================================ chargement initial
    def _charger_apres_premier_dessin(self):
        """Le chargement de l'inventaire part 200 ms après le premier dessin du catalogue (au plus tard 500 ms après
        la construction, si le panneau n'est pas affiché).  Second audit : lancé dès la construction, le fil de
        chargement (Python pur, GIL gardé jusqu'à 5 ms d'affilée) disputait le GIL à chaque rappel Python de la
        mise en place de la fenêtre (premier dessin, mises en page des rangées souples, polices) — 100 à 180 ms
        de gel à 10 × la banque, rien une fois l'affichage posé (≈ 0,1–0,3 s après le premier dessin)."""
        self._chargement_lance = False
        self._premier_dessin = False
        self._minuteur_chargement = QTimer(self)
        self._minuteur_chargement.setSingleShot(True)
        self._minuteur_chargement.timeout.connect(self._chargement_initial)
        self._minuteur_chargement.start(500)
        self.v_obj.viewport().installEventFilter(self)

    def eventFilter(self, objet, evenement):
        if not self._premier_dessin and evenement.type() == QEvent.Type.Paint and objet is self.v_obj.viewport():
            self._premier_dessin = True
            if not self._chargement_lance:
                self._minuteur_chargement.start(200)
        return super().eventFilter(objet, evenement)

    def _chargement_initial(self):
        self.v_obj.viewport().removeEventFilter(self)
        if not self._chargement_lance:
            self.charger(False)

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
        dest = os.path.abspath(os.path.expanduser(self.dest.text().strip())) if hasattr(self, 'dest') else ''
        if forcer:
            self.window().statusBar().showMessage(tr('ohp_nouv_verification'), 5000)
        self._t_nouv = Tache(self.nouveautes_preparees, dest, forcer, self._dest_courante(), self.dest.text(),
                             self.ciel_cat.currentData(), parent=self)
        self._t_nouv.quand_fini(lambda n, f=forcer: self._nouveautes_pretes(n, f))
        self._t_nouv.quand_erreur(lambda e, f=forcer: f and self.window().statusBar().showMessage(tr('ohp_nouv_hors_ligne'), 8000))
        self._t_nouv.start()

    @staticmethod
    def nouveautes_preparees(dest, forcer, dest_courante, texte, cat):
        """Fil de fond : vérification des nouveautés, et l'inventaire frais préparé comme au chargement."""
        from .inventaire import verifier_nouveautes
        n = verifier_nouveautes(dest, forcer)
        if n is not None and n.get('inv') is not None:
            Panneau.preparer_objets(n['inv'])
            n['_pre'] = Panneau.precharger(n['inv'], dest_courante, texte, cat)
        return n

    def _nouveautes_pretes(self, n, forcer):
        if n is None:
            if forcer:
                self.window().statusBar().showMessage(tr('ohp_nouv_hors_ligne'), 8000)
            return
        inv = n.pop('inv', None)
        pre = n.pop('_pre', None)
        if inv is not None:
            self._inventaire_pret(inv, pre)
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
        self.f_manquantes = case('ohp_f_manquantes')
        self.f_manquantes.toggled.connect(self._filtrer_objets)
        self.f_manquantes.toggled.connect(self._remplir_images)
        h.addWidget(self.f_manquantes)
        self.b_rafraichir = bouton('ohp_rafraichir', lambda: self.charger(True))
        h.addWidget(self.b_rafraichir)
        v.addLayout(h)
        self.l_inventaire = QLabel(tr('ohp_chargement'))
        self.l_inventaire.setWordWrap(True)
        v.addWidget(self.l_inventaire)
        sp = QSplitter(Qt.Orientation.Horizontal)
        self.m_obj = ModeleTableau([tr('ohp_col_type'), tr('ohp_col_objet'), tr('ohp_col_remarque'), tr('ohp_col_images'),
                                    tr('ohp_col_possede'), tr('ohp_col_volume'), tr('ohp_col_nuits'),
                                    tr('ohp_col_telescopes'), tr('ohp_col_filtres'), tr('ohp_col_etat')])
        self.COL_POSSEDE = 4
        self.v_obj, self.p_obj = vue_tableau(self.m_obj, 'ohp_table_objets_aide', filtrable=True)
        self.v_obj.setItemDelegateForColumn(self.COL_POSSEDE, DelegueProgression(self.v_obj, lambda: pastilles.couleur_statut('ok')))
        self.v_obj.horizontalHeader().setToolTip(tr('ohp_legende_aide'))
        # sélection à la souris (glisser, Maj+clic) : une rafale de signaux → un seul remplissage, 40 ms après
        self._minuteur_choix = QTimer(self)
        self._minuteur_choix.setSingleShot(True)
        self._minuteur_choix.setInterval(40)
        self._minuteur_choix.timeout.connect(self._objets_choisis)
        self.v_obj.selectionModel().selectionChanged.connect(lambda *_: self._minuteur_choix.start())
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
        self.m_img = ModeleParesseux([tr('ohp_col_possede'), tr('ohp_col_date'), tr('ohp_col_heure_site'),
                                      tr('ohp_col_nuit'), tr('ohp_col_tel'), tr('ohp_col_filtre'),
                                      tr('ohp_col_pose'), tr('ohp_col_drapeaux'), tr('ohp_col_noms')],
                                     self._ligne_image, self._style_image, self._bulle_image, self._cle_image)
        self.v_img, self.p_img = vue_tableau(self.m_img, 'ohp_table_images_aide')
        self.v_img.horizontalHeader().setToolTip(tr('ohp_legende_aide'))
        vd.addWidget(self.v_img)
        self.l_legende = QLabel()                 # légende compacte des pastilles (FR/EN, couleurs du thème)
        self.l_legende.setWordWrap(True)
        aide(self.l_legende, 'ohp_legende_aide')
        self._maj_legende()
        vd.addWidget(self.l_legende)
        sp.addWidget(droite)
        sp.setSizes([560, 620])
        self.sp_catalogue = sp
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
        self._chargement_lance = True
        self.b_rafraichir.setEnabled(False)
        self.l_inventaire.setText(tr('ohp_interrogation_tap') if rafraichir else tr('ohp_chargement'))
        self._t_inv = Tache(self.charger_et_preparer, rafraichir, self._dest_courante(), self.dest.text(),
                            self.ciel_cat.currentData(), parent=self)
        self._t_inv.quand_fini(self._chargement_pret)
        self._t_inv.quand_erreur(self._inventaire_erreur)
        self._t_inv.start()

    @staticmethod
    def charger_et_preparer(rafraichir, dest='', texte='', cat=''):
        """Dans le fil de fond : inventaire, catalogue des objets, chaîne de recherche de chaque objet, clés de tri,
        PUIS tout ce que l'affichage du chargement demande (points du ciel, anomalies, possession de la
        destination et ses lots) — en série, dans ce seul fil.

        Second audit : à 10 × la banque, le fil graphique restait figé 0,5–0,8 s après le chargement alors que
        chacun de ses créneaux Python durait moins de 40 ms.  Cause : trois calculs de fond (anomalies,
        possession, carte du ciel) tournaient EN MÊME TEMPS que le premier dessin des tables ; chaque rappel de
        Qt vers Python (une cellule, un rôle) doit reprendre le GIL à un fil de calcul qui le garde jusqu'à
        5 ms.  Calculés ici avant la remise de l'inventaire, ils ne disputent plus rien au dessin.
        Rend (inventaire, préchargement)."""
        from .inventaire import Inventaire
        inv = Inventaire.charger(rafraichir)
        Panneau.preparer_objets(inv)
        return inv, Panneau.precharger(inv, dest, texte, cat)

    @staticmethod
    def precharger(inv, dest, texte='', cat=''):
        """Résultats de fond de l'affichage initial, pour CET inventaire et CETTE destination (ignorés sinon).

        dest : destination absolue (possession) ; texte : le champ tel quel (anomalies du traitement, lots),
        exactement comme les calculs faits un par un."""
        pre = {'images': inv.images, 'dest': dest, 'texte': texte, 'langue': i18n.langue()}
        pre['ciel'] = (cat, Panneau.points_ciel(inv.images, cat))
        pre['anomalies'] = Panneau.anomalies_de(inv, texte)
        if dest:
            poss, infos = Possession.lire_avec_infos(dest)
            pre['possession'] = (poss, infos, poss.compte_objets(inv.images), inv.images)
            pre['lots'] = Panneau.lire_lots(texte, inv.images, poss, infos)
        return pre

    @staticmethod
    def anomalies_de(inv, dest):
        """Anomalies de l'inventaire (médoïdes, détection : calculées une fois par inventaire) + celles du
        traitement de la destination (relues à chaque fois)."""
        from . import anomalies
        from .astrometrie import attentes
        memo = getattr(inv, '_anom_memo', (None,))
        if memo[0] is not inv.images:
            med, medo = attentes(inv.images)
            memo = inv._anom_memo = (inv.images, anomalies.detecter(inv.images, medo))
        return memo[1] + anomalies.depuis_traitement(os.path.join(dest, '_traitement', 'etat.sqlite'))

    def _chargement_pret(self, resultat):
        inv, pre = resultat if isinstance(resultat, tuple) else (resultat, None)
        self._inventaire_pret(inv, pre)

    def _prendre(self, cle):
        """Un résultat préchargé en fond, s'il vaut encore (même inventaire, même destination, même langue) ;
        consommé (un second appel recalcule)."""
        pre = getattr(self, '_pre', None)
        if not pre or cle not in pre or self.inv is None or pre['images'] is not self.inv.images:
            return None
        if pre['dest'] != self._dest_courante() or pre['texte'] != self.dest.text() or pre['langue'] != i18n.langue():
            return None
        return pre.pop(cle)

    def _plus_tard(self, f, *args):
        """Une étape d'affichage au prochain tour de boucle : le dessin des tables passe entre deux étapes."""
        if not hasattr(self, '_etapes'):
            self._etapes = []
            self._minuteur_etapes = QTimer(self)        # enfant du panneau : rien ne part vers un panneau fermé
            self._minuteur_etapes.setSingleShot(True)
            self._minuteur_etapes.setInterval(0)
            self._minuteur_etapes.timeout.connect(self._etape_suivante)
        self._etapes.append((f, args))
        self._minuteur_etapes.start()

    def _etape_suivante(self):
        if self._etapes:
            f, args = self._etapes.pop(0)
            if self._etapes:
                self._minuteur_etapes.start()
            f(*args)

    @staticmethod
    def preparer_objets(inv):
        for o in inv.objets():
            if '_recherche' not in o:
                o['_recherche'] = '\x00'.join([o['objet'].lower(), cibles.nom_affiche(o['objet']).lower()] +
                                               [n.lower() for n in o['noms']])
        if getattr(inv, '_index_memo', (None,))[0] is not inv.images:
            # images triées une fois (date, adresse) et rangées par objet : choisir des objets ou filtrer ne trie
            # ni ne parcourt plus tout l'inventaire à chaque geste
            triees = sorted(inv.images, key=lambda x: (x['t_min'], x['access_url']))
            par_objet, valeurs = {}, {}
            for x in triees:
                par_objet.setdefault(x['objet'], []).append(x)
                v = valeurs.setdefault(x['objet'], (set(), set()))
                v[0].add(str(x['nuit']))
                v[1].add(str(x['filter_name']))
            inv._index_memo = (inv.images, triees, par_objet, valeurs)
        if not hasattr(inv, '_resume_memo'):
            inv._resume_memo = {'doublons': sum(1 for x in inv.images if x['doublon']),
                                'octets': sum(x['access_estsize'] * 1024 for x in inv.images),
                                'nuits': len({str(x['nuit']) for x in inv.images})}
        if getattr(inv, '_cles_memo', (None,))[0] is not inv.images:
            inv._cles_memo = (inv.images,) + cles_de_tri_images(inv.images)

    def _inventaire_erreur(self, e):
        self.b_rafraichir.setEnabled(True)
        self.l_inventaire.setText(tr('ohp_inventaire_erreur', erreur=e))

    def _inventaire_pret(self, inv, pre=None):
        self.inv = inv
        self._pre = pre
        self.b_rafraichir.setEnabled(True)
        m = inv.meta
        n = inv.nouveautes or {}
        self.preparer_objets(inv)                    # déjà fait en fond (sans effet), sauf inventaire passé à la main
        r = inv._resume_memo
        self._comptes = None
        texte = tr('ohp_inventaire_resume', n=len(inv.images), objets=len(inv.objets()), doublons=r['doublons'],
                   taille=_taille(r['octets']), nuits=r['nuits'], date=m.get('date', '?')[:16],
                   source=m.get('source', '?')).replace('\n', ' — ')
        if n and not n.get('premiere') and (n.get('images') or n.get('noms')):
            texte += ' — ' + tr('ohp_nouveautes', images=len(n['images']), noms=len(n['noms']),
                                depuis=n.get('depuis') or '?').rstrip(' :')
        self.l_inventaire.setText(texte)
        self._remplir_objets()
        if pre:                                      # préchargé en fond : une étape par tour de boucle
            self._plus_tard(self._remplir_anomalies)
            self._plus_tard(self._remplir_ciel)
            self._plus_tard(self._charger_possession)
        else:
            self._remplir_anomalies()
            self._remplir_ciel()
            self._charger_possession()
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
                           o['images'], Progression(0, o['images']), _taille(o['octets']), len(o['nuits']),
                           ', '.join(sorted(o['tel'])), ', '.join(sorted(o['filtres'])), ', '.join(etat)))
            donnees.append(o)
            bulles.append(tr('ohp_bulle_objet', noms=', '.join(sorted(o['noms'])), doublons=o['doublons']))
        self.m_obj.remplir(lignes, donnees, bulles)
        self._appliquer_possession_objets()
        memoire.ajuster_colonnes(self.v_obj)
        self._filtrer_objets()
        self._restaurer_selection()

    # ---------------------------------------------------------------- ce qu'on possède déjà
    def _dest_courante(self) -> str:
        return os.path.abspath(os.path.expanduser(self.dest.text().strip())) if hasattr(self, 'dest') and \
            self.dest.text().strip() else ''

    def _charger_possession(self):
        """Relit l'état de la destination hors du fil graphique, puis rafraîchit pastilles, comptes et lots."""
        dest = self._dest_courante()
        if not dest:
            return
        pre = self._prendre('possession')
        if pre is not None:
            self._possession_prete(pre)
            return
        images = self.inv.images if self.inv else []

        def lire(d=dest, imgs=images):
            poss, infos = Possession.lire_avec_infos(d)
            return poss, infos, poss.compte_objets(imgs), imgs   # comptes par objet : en fond aussi
        self._t_poss = Tache(lire, parent=self)
        self._t_poss.quand_fini(self._possession_prete)
        self._t_poss.start()

    def _possession_prete(self, resultat):
        self.possession, self._infos_ok = resultat[:2]
        self._pre_possession = self.possession       # lots préchargés valables pour cette possession seulement
        if len(resultat) > 3 and self.inv is not None and resultat[3] is self.inv.images:
            self._comptes = resultat[2]              # comptes calculés en fond pour CET inventaire
        else:
            self._comptes = None
        self._appliquer_possession_objets()
        self._filtrer_objets()
        if self.f_manquantes.isChecked():
            self._remplir_images()                   # la liste elle-même dépend de la possession
        else:
            self._restyler_images()
            self._estimer()
        self._remplir_lots()

    def _appliquer_possession_objets(self):
        """Colonne « possédé » (n / total, mini-barre) et pastille de chaque objet, sans perdre la sélection."""
        if not self.inv or not self.m_obj.lignes:
            return
        comptes = getattr(self, '_comptes', None)
        if comptes is None:
            if self.possession.existe:
                self._charger_possession()           # comptes recalculés en fond, appliqués au retour
            return                                   # en attendant : barres à zéro (« 0 / n »)
        lignes, styles = [], []
        for ligne, o in zip(self.m_obj.lignes, self.m_obj.donnees):
            c = comptes.get(o['objet'], {'possedees': 0, 'doublons': 0, 'echecs': 0, 'absentes': 0, 'total': o['images']})
            etat = Possession.etat_objet(c)
            l = list(ligne)
            l[self.COL_POSSEDE] = Progression(c['possedees'] + c['doublons'], c['total'])
            lignes.append(tuple(l))
            bulle = tr('ohp_bulle_possession_objet', possedees=c['possedees'], doublons=c['doublons'],
                       echecs=c['echecs'], absentes=c['absentes'], total=c['total'])
            styles.append({'icones': {self.COL_POSSEDE: pastilles.pastille(etat)} if etat != 'aucun' else {},
                           'bulles': {self.COL_POSSEDE: bulle}})
        self.m_obj.remplacer_lignes(lignes, styles)

    def _maj_legende(self):
        if not hasattr(self, 'l_legende'):
            return
        c = {k: pastilles.couleur_statut(k).name() for k in ('ok', 'ecarte', 'echec', 'absente')}
        self.l_legende.setText(
            '<span style="color:%s">&#10004;</span> %s &nbsp; <span style="color:%s">&#9679;</span> %s &nbsp; '
            '<span style="color:%s">&#9650;</span> %s &nbsp; <span style="color:%s">&#8681;</span> %s'
            % (c['ok'], tr('ohp_statut_possession_ok'), c['ecarte'], tr('ohp_statut_possession_doublon'),
               c['echec'], tr('ohp_statut_possession_echec'), c['absente'], tr('ohp_statut_possession_absente')))

    def _filtrer_objets(self):
        q = self.recherche.text().strip().lower()
        cat, tel = self.f_cat.currentData(), self.f_tel.currentData()
        nouveaux, verifier, manquantes = (self.f_nouveaux.isChecked(), self.f_verifier.isChecked(),
                                          self.f_manquantes.isChecked())
        visibles = set()
        for ligne, o in zip(self.m_obj.lignes, self.m_obj.donnees):
            ok = (not cat or o['cat'] == cat) and (not tel or tel in o['tel']) and \
                 (not nouveaux or o['nouveau']) and (not verifier or o['a_verifier'])
            if ok and manquantes:
                prog = ligne[self.COL_POSSEDE]
                ok = not (isinstance(prog, Progression) and prog.total > 0 and prog.n >= prog.total)
            if ok and q:
                ok = q in (o.get('_recherche') or o['objet'].lower())
            if ok:
                visibles.add(id(o))
        # un seul passage du filtre du proxy (et non un setRowHidden par ligne) ; suit les re-tris
        self.p_obj.definir_visibles(None if len(visibles) == len(self.m_obj.donnees) else visibles)

    def _objets_choisis(self, *_):
        objs = {o['objet'] for o in lignes_choisies(self.v_obj, self.p_obj, self.m_obj)}
        self._objets = objs
        nuits, filtres = set(), set()
        if self.inv:
            valeurs = self._index_inventaire()[3]
            for o in objs:
                v = valeurs.get(o)
                if v:
                    nuits |= v[0]
                    filtres |= v[1]
        for combo, vals, tous in ((self.f_nuit, nuits, 'ohp_toutes_nuits'), (self.f_filtre, filtres,
                                                                            'ohp_tous_filtres')):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(tr(tous), '')
            for val in sorted(vals):
                combo.addItem(val, val)
            combo.blockSignals(False)
        if objs and (self._nuit_attendue or self._filtre_attendu):
            for combo, attr in ((self.f_nuit, '_nuit_attendue'), (self.f_filtre, '_filtre_attendu')):
                i = combo.findData(getattr(self, attr)) if getattr(self, attr) else -1
                if i >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(i)
                    combo.blockSignals(False)
                setattr(self, attr, None)            # appliquée une fois (ou absente de ces objets : oubliée)
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

    def _index_inventaire(self):
        if getattr(self.inv, '_index_memo', (None,))[0] is not self.inv.images:
            self.preparer_objets(self.inv)
        return self.inv._index_memo

    def _images_filtrees(self):
        """Images des objets choisis, dans l'ordre (date, adresse), après les filtres de la vue."""
        objs = getattr(self, '_objets', set())
        nuit, filtre = self.f_nuit.currentData(), self.f_filtre.currentData()
        dates, manquantes = self.f_dates.isChecked(), self.f_manquantes.isChecked()
        out = []
        if not self.inv or not objs:
            return out
        _, triees, par_objet, _ = self._index_inventaire()
        if len(objs) * 4 < len(par_objet):           # peu d'objets : leurs listes (déjà triées), fusionnées
            import heapq
            source = heapq.merge(*(par_objet.get(o, []) for o in objs), key=lambda x: (x['t_min'], x['access_url']))
        else:                                        # beaucoup : l'inventaire trié, filtré
            source = triees
            if len(objs) >= len(par_objet) and all(o in objs for o in par_objet):
                objs = None                          # tous les objets choisis : aucun à écarter
                if not (nuit or filtre or dates or manquantes):
                    return list(triees)              # « tout sélectionner » sans filtre : rien à parcourir
        for x in source:
            if objs is not None and x['objet'] not in objs:
                continue
            if nuit and str(x['nuit']) != nuit:
                continue
            if filtre and x['filter_name'] != filtre:
                continue
            if dates and (x['date_partagee'] or x['diurne']) and not x['doublon']:
                continue
            if manquantes and self.possession.possedee(x):
                continue
            out.append(x)
        return out

    def _sites_par_id(self):
        d = getattr(self, '_sites_cache', None)
        if d is None:
            from ...core import sites as sites_mod
            d = self._sites_cache = {s_.id: s_ for s_ in sites_mod.sites()}
        return d

    def _ligne_image(self, x):
        """Cellules d'une ligne d'image, calculées seulement quand la vue l'affiche (modèle paresseux)."""
        from ...core import temps
        u = temps.mjd_vers_utc(x['t_min'])
        s_ = self._sites_par_id().get(x.get('site'))
        loc = temps.heure_locale(u, s_).strftime('%H:%M:%S (UTC%z)') if s_ else ''
        return (tr('ohp_statut_possession_' + self.possession.statut(x)), u.strftime('%Y-%m-%d %H:%M:%S'), loc,
                str(x['nuit']), x['tel'], x['filter_name'], x['t_exptime'],
                texte_drapeaux(x['doublon'], x['date_partagee'], x['diurne'], x['nouveau'], x['vu_le']),
                x['target_name'])

    def _bulle_image(self, x):
        from ...core import temps
        u = temps.mjd_vers_utc(x['t_min'])
        return temps.formater(u, self._sites_par_id().get(x.get('site'))) + '\n' + x['access_url']

    def _style_image(self, x):
        """Style d'une ligne d'image ; l'info-bulle de possession est composée au survol seulement."""
        st = self.possession.statut(x)
        communs = self.__dict__.setdefault('_styles_communs', {})
        c = communs.get(st)
        if c is None:
            c = communs[st] = ({0: pastilles.pastille(st)},
                               pastilles.couleur_statut(st) if st != 'absente' else None)
        return {'icones': c[0], 'couleur': c[1], 'bulles': {0: lambda x=x: self._bulle_possession(x)}}

    def _bulle_possession(self, x):
        d = self.possession.detail(x)
        return tr('ohp_bulle_possession', statut=tr('ohp_statut_possession_' + d['statut']),
                  date=d['date'] or '—', chemin=d['chemin'] or '—')

    def _cles_tri(self):
        if getattr(self.inv, '_cles_memo', (None,))[0] is not self.inv.images:
            self.preparer_objets(self.inv)
        return self.inv._cles_memo

    def _cle_image(self, col):
        """Clés de tri rapides (sans calculer les cellules) pour toutes les colonnes de la table des images.

        Chaque clé donne exactement l'ordre de la valeur affichée triée par `cle_de_tri` (même rang pour un même
        texte : le tri stable garde alors l'ordre courant).  Heure du site et drapeaux : clés entières
        précalculées en fond au chargement (`cles_de_tri_images`), triées par numpy (second audit : ces deux
        colonnes calculaient sinon toutes leurs cellules, ~0,5 s à 80 000 lignes)."""
        from ...gui.modele import cle_de_tri

        def rangs(textes):                           # {valeur: rang de sa cellule dans l'ordre de cle_de_tri}
            cles = {v: cle_de_tri(t) for v, t in textes.items()}
            r = {c: k for k, c in enumerate(sorted(set(cles.values())))}
            return {v: r[c] for v, c in cles.items()}
        if col == 0:
            cles = rangs({st: tr('ohp_statut_possession_' + st) for st in ('ok', 'doublon', 'echec', 'absente')})
            return lambda x: cles[self.possession.statut(x)]
        if col in (1, 3):                            # (même ordre que (0, t_min, 0) : une seule catégorie)
            return lambda x: float(x['t_min'])
        if col in (2, 7) and self.inv is not None:
            _, heure, drap, vus = self._cles_tri()
            if not all(id(x) in heure for x in self.m_img.donnees):
                return None                          # image hors de l'inventaire indexé : valeur des cellules
            if col == 2:
                return lambda x: heure[id(x)]
            codes = rangs({c: texte_drapeaux(c & _D_DOUBLON, c & _D_DATE, c & _D_DIURNE, c & _D_NOUVEAU,
                                             vus[c >> 4] if c & _D_NOUVEAU else '')
                           for c in set(drap.values())})
            return lambda x: codes[drap[id(x)]]
        champ = {4: 'tel', 5: 'filter_name', 6: 't_exptime', 8: 'target_name'}.get(col)
        if champ:
            try:                                     # rang de chaque valeur distincte (clés entières → numpy)
                r = rangs({x[champ]: x[champ] for x in self.m_img.donnees})
                return lambda x: r[x[champ]]
            except (TypeError, KeyError):            # valeur non hachable : clé de la cellule
                return lambda x: cle_de_tri(x[champ])
        return None

    def _restyler_images(self, lignes=True):
        """Thème ou possession changés : colonne « possédé » et styles recalculés à l'affichage ; ni
        reconstruction, ni perte de la sélection."""
        self.__dict__.pop('_styles_communs', None)
        self.m_img.invalider(lignes=lignes)

    def _remplir_images(self, *_):
        imgs = self._images_filtrees()               # déjà dans l'ordre (date, adresse)
        vide_avant = self.m_img.rowCount() == 0
        self.m_img.remplir_objets(imgs)              # aucune ligne construite ici : seulement à l'affichage
        if vide_avant or not getattr(self, '_colonnes_images_ajustees', False):
            memoire.ajuster_colonnes(self.v_img)     # une fois : ensuite l'utilisateur garde ses largeurs
            self._colonnes_images_ajustees = bool(imgs)
        self.selection = imgs
        self._estimer()

    def _estimer(self, *_):
        """Volume, place libre (un appel système sur la destination, peut-être un partage réseau) et images
        manquantes : calculés hors du fil graphique (80 000 images : ~0,3 s), affichés au retour.  Lancé 120 ms
        après le dernier geste : le fil de calcul ne dispute pas le GIL à l'interface pendant qu'elle se remplit."""
        if not hasattr(self, '_minuteur_estimation'):
            self._minuteur_estimation = QTimer(self)
            self._minuteur_estimation.setSingleShot(True)
            self._minuteur_estimation.setInterval(120)
            self._minuteur_estimation.timeout.connect(self._estimer_maintenant)
        self._gen_estimation = getattr(self, '_gen_estimation', 0) + 1      # un résultat en route est périmé
        self._minuteur_estimation.start()

    def _estimer_maintenant(self):
        if not self.selection:
            self.l_estimation.setText(tr('ohp_aucune_selection'))
            return
        fmt = self.format.currentData() if hasattr(self, 'format') else 'xisf'
        dest = self.dest.text() if hasattr(self, 'dest') else ''
        sel, poss = list(self.selection), self.possession
        gen = self._gen_estimation
        self._t_est = Tache(self.texte_estimation, sel, poss, fmt, dest, parent=self)
        self._t_est.quand_fini(lambda t, g=gen: g == self._gen_estimation and self.l_estimation.setText(t))
        self._t_est.start()

    @staticmethod
    def texte_estimation(selection, possession, fmt, dest) -> str:
        from ...core.machine import disque_libre_go
        from .selection import estimer
        manquantes = possession.manquantes(selection)
        utiles = [x for x in selection if not x['doublon']]
        if len(manquantes) < len(utiles):            # une partie est déjà là : on n'estime que ce qui manque
            e = estimer(manquantes, fmt)
            texte = tr('ohp_estimation_manquantes', manquantes=len(manquantes), total=len(utiles),
                       possedees=len(utiles) - len(manquantes), fits=_taille(e['octets_fits']),
                       sortie=_taille(e['octets_sortie']), format=fmt.upper())
        else:
            e = estimer(selection, fmt)
            texte = tr('ohp_estimation', images=e['images'], objets=e['objets'], nuits=e['nuits'],
                       doublons=e['doublons'], fits=_taille(e['octets_fits']),
                       sortie=_taille(e['octets_sortie']), format=fmt.upper())
        return texte + '  ' + tr('ohp_libre', libre=_taille(disque_libre_go(dest or '.') * 1e9))

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
        self.dest.editingFinished.connect(self._charger_possession)
        # gardé dès qu'il est modifié (écriture différée et groupée : jamais une écriture par frappe)
        self.dest.textEdited.connect(lambda t: memoire.reglage_differe('dossier_sortie', t.strip()))
        h.addWidget(self.dest, 1)
        h.addWidget(bouton('reg_parcourir', self._parcourir))
        f.addRow(tr('reg_dest'), h)
        self.format = liste('reg_format_aide', [(tr('fmt_xisf'), 'xisf'), (tr('fmt_fz'), 'fz'), (tr('fmt_fits'), 'fits')])
        self.format.setCurrentIndex(max(0, self.format.findData(r['format_sortie'])))
        self.format.currentIndexChanged.connect(self._estimer)
        self.format.currentIndexChanged.connect(
            lambda *_: memoire.reglage_differe('format_sortie', self.format.currentData()))
        f.addRow(tr('reg_format'), self.format)
        noms = r['langue_noms'] if r['langue_noms'] in ('fr', 'en') else i18n.langue()
        self.noms = liste('reg_noms_aide', [('Français', 'fr'), ('English', 'en')])
        self.noms.setCurrentIndex(max(0, self.noms.findData(noms)))
        self.noms.currentIndexChanged.connect(
            lambda *_: memoire.reglage_differe('langue_noms', self.noms.currentData()))
        f.addRow(tr('reg_noms'), self.noms)
        self.garder_doublons = case('ohp_garder_doublons', r.lire('ohp_garder_doublons', bool))
        self.garder_fits = case('ohp_garder_fits', r.lire('ohp_garder_fits', bool))
        f.addRow('', self.garder_doublons)
        f.addRow('', self.garder_fits)
        self.qualite = case('ohp_qualite', r.lire('ohp_verifier_qualite', bool))
        f.addRow('', self.qualite)
        for cle, c in (('ohp_garder_doublons', self.garder_doublons), ('ohp_garder_fits', self.garder_fits),
                       ('ohp_verifier_qualite', self.qualite)):
            c.toggled.connect(lambda oui, k=cle: memoire.reglage_differe(k, bool(oui)))
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
        self.mode_astap.setCurrentIndex(max(0, self.mode_astap.findData(r.lire('ohp_mode_astap', str))))
        self.mode_astap.currentIndexChanged.connect(
            lambda *_: memoire.reglage_differe('ohp_mode_astap', self.mode_astap.currentData()))
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
            memoire.reglage_differe('dossier_sortie', d)
            self._estimer()
            self._remplir_lots()
            self._charger_possession()

    def _astap(self):
        DialogueASTAP(self).exec()
        self.reglages_changes()

    def reglages_changes(self):
        """Détection d'ASTAP (sous-processus) et sondes de la machine : hors du fil graphique."""
        from ...core import astap, machine
        r = config.reglages()
        self._suivre_preferences(r)
        pastilles.vider_cache()                    # le thème a pu changer : pastilles et légende aux bonnes couleurs
        self._maj_legende()
        if self.inv and self.m_obj.lignes:
            self._appliquer_possession_objets()
            self._restyler_images(lignes=False)      # couleurs seulement : ni reconstruction ni relecture
            self._restyler_lots()
        self.l_astap.setText(tr('astapdlg_recherche'))

        def sonder():
            return machine.detecter(), astap.detecter(r['astap_executable'], r['astap_catalogue'])
        self._t_astap = Tache(sonder, parent=self)
        self._t_astap.quand_fini(self._sondes_pretes)
        self._t_astap.start()

    def _suivre_preferences(self, r):
        """Les Préférences ont changé le dossier de sortie, le format ou la langue des noms : l'onglet suit.
        Seulement ce qui a changé DANS les réglages depuis la dernière fois (un changement de thème ne touche à rien)."""
        vus = getattr(self, '_prefs_vues', None)
        actuels = (r['dossier_sortie'], r['format_sortie'], r['langue_noms'])
        self._prefs_vues = actuels
        if vus is None or vus == actuels or self.occupe():
            return
        d = actuels[0]
        if d and d != vus[0] and d != self.dest.text().strip():
            self.dest.setText(d)
            self._remplir_lots()
            self._charger_possession()
            self._estimer()
        for combo, val, avant in ((self.format, actuels[1], vus[1]), (self.noms, actuels[2], vus[2])):
            i = combo.findData(val)
            if val != avant and i >= 0 and i != combo.currentIndex():
                combo.setCurrentIndex(i)

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
        memoire.reglage_differe('dossier_sortie', d)
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
        src = QFileDialog.getExistingDirectory(self, tr('ohp_reorganiser_titre'),
                                               memoire.dossier('ohp_reorganiser', self.dest.text()))
        if not src:
            return
        memoire.retenir('ohp_reorganiser', src)
        dest = os.path.abspath(os.path.expanduser(self.dest.text().strip()))
        from .pilote import Traitement
        from ...core.parallele import Plan
        inv = self.inv
        fmt, L = self.format.currentData(), self.noms.currentData()

        arret = self.arret = enregistrer_arret(threading.Event())
        evts = FileEvenements(self, self._progression_reorg)

        def travail():
            t = Traitement(dest, inv, Plan(1, 1, True, ''), {'format': fmt, 'langue': L}, arret=arret)
            try:
                return t.reorganiser(src, progression=lambda fait, total: evts((fait, total)))
            finally:
                t.fermer()

        def fini(r):
            evts.arreter()
            self.b_lancer.setEnabled(True)
            self.b_arreter.setEnabled(False)
            self._remplir_lots()
            self._charger_possession()
            self._log(tr('ohp_reorganise_fait', n=r['ranges'], lots=r['lots'], ignores=len(r['ignores'])))

        def erreur(e):
            evts.arreter()
            self.b_lancer.setEnabled(True)
            self.b_arreter.setEnabled(False)
            QMessageBox.warning(self, tr('ohp_reorganiser'), e)
        self.b_lancer.setEnabled(False)
        self.b_arreter.setEnabled(True)               # arrêt immédiat : ce qui est rattaché est rangé
        self._t_reorg = Tache(travail, parent=self)
        self._t_reorg.quand_fini(fini)
        self._t_reorg.quand_erreur(erreur)
        self._t_reorg.start()

    def _progression_reorg(self, evs):
        fait, total = evs[-1]
        self.barre.setMaximum(max(1, total))
        self.barre.setValue(fait)
        self.l_stats.setText(tr('ohp_reorganise_progression', fait=fait, total=total))

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
        libre = disque_libre_go(dest) * 1e9
        # fenêtre de FITS en attente réduite à la place libre plutôt qu'un refus (le pilote le signale au journal)
        besoin = place_necessaire(est, plan.conversions, plan.telechargements, libre)
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
        from ..qualite import moteur
        from ..qualite.gui_sans_qt import duree_lisible
        dest = self.dest.text()
        q = FileEvenements(self, lambda evs: [self._log(e) for e in evs])
        self._evts_qualite = q
        arret = self.arret or enregistrer_arret(threading.Event())
        L = i18n.langue()

        def rapporter(ev):
            if ev['type'] == 'lot':
                q(tr('qual_lot', lot=os.path.relpath(ev['lot'], dest), n=len(ev['lignes'])) + ' — ' +
                  rapport.resume(ev['lignes'], L)[1 if ev['lignes'] else 0])
            elif ev['type'] == 'fin':
                q(tr('qual_fini', n=ev['n'], lots=ev['lots'], deja=ev['deja'], duree=duree_lisible(ev['duree'])))

        plan_machine = self._plan()[1]

        def travail():
            # échantillon par lot au-delà de 200 images : le contrôle après traitement doit rester court
            plan_dossier = moteur.planifier(dest, None)          # un seul parcours, repris par le moteur
            ech = moteur.ECHANTILLON_DEFAUT if plan_dossier['total_dossier'] > moteur.SEUIL_GROS_DOSSIER else None
            moteur.Mesureur(dest, plan_machine, ech, rapporter=rapporter, arret=arret, langue=L,
                            plan_dossier=plan_dossier).lancer()
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
        # panneau fermé : plus aucune étape d'affichage ni minuterie différée ne repart vers ses widgets
        if getattr(self, '_etapes', None):
            self._etapes.clear()
        for nom in ('_minuteur_etapes', '_minuteur_chargement', '_minuteur_choix', '_minuteur_estimation'):
            m = getattr(self, nom, None)
            if m is not None and not est_detruit(m):
                m.stop()

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
            elif t == 'fenetre':
                self._log(tr('ohp_fenetre_reduite', libre=_taille(ev['libre']), fenetre=ev['fenetre'],
                             nominale=ev['nominale']))
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
                self._charger_possession()
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
                                     tr('ohp_col_complet'), tr('csv_pose_totale_s'), tr('csv_nuits'),
                                     tr('csv_alignement')])
        self.COL_LOT_COMPLET = 4
        self.v_lots, self.p_lots = vue_tableau(self.m_lots, 'ohp_table_lots_aide')
        self.v_lots.doubleClicked.connect(lambda *_: self._ouvrir_lot())
        v.addWidget(self.v_lots, 1)
        return w

    @staticmethod
    def lire_lots(dest, images, possession, infos_ok):
        """INDEX_LOTS.csv lu et complétude calculée HORS du fil graphique (la destination peut être un partage
        réseau : chaque accès y coûte un aller-retour).  Rend [(ligne, dossier, complétude ou None)]."""
        chemin = os.path.join(dest, 'INDEX_LOTS.csv')
        out = []
        completude = possession.lots(images, infos_ok) if images else {}
        try:
            with open(chemin, encoding='utf-8-sig') as f:
                for i, r in enumerate(csv.reader(f, delimiter=';')):
                    if i == 0 or len(r) < 12:
                        continue
                    dossier = os.path.join(dest, *r[0].split('/'))
                    try:
                        ligne = (r[0], r[2], r[4], int(r[5]), '', float(r[6]), r[7], r[11])
                    except ValueError:
                        continue
                    out.append((ligne, dossier, completude.get(os.path.normcase(os.path.abspath(dossier)))))
        except OSError:
            pass
        return out

    def _remplir_lots(self):
        dest = self.dest.text()
        images = self.inv.images if self.inv else None
        pre = self._prendre('lots') if images is not None else None
        if pre is not None and getattr(self, '_pre_possession', None) is self.possession:
            self._lots_prets(dest, pre)
            return
        self._t_lots = Tache(self.lire_lots, dest, images, self.possession, self._infos_ok, parent=self)
        self._t_lots.quand_fini(lambda r, d=dest: self._lots_prets(d, r))
        self._t_lots.start()

    def _style_lot(self, c):
        if c and c['base']:
            etat = tr('ohp_lot_complet' if c['complet'] else 'ohp_lot_incomplet',
                      converties=c['converties'], base=c['base'])
            return etat, {'icones': {self.COL_LOT_COMPLET: pastilles.pastille('complet' if c['complet'] else 'partiel')},
                          'bulles': {self.COL_LOT_COMPLET: tr('ohp_lot_complet_aide')}}
        return '', {}

    def _lots_prets(self, dest, resultat):
        if dest != self.dest.text():
            return                                   # la destination a changé entre-temps : un autre calcul suit
        self._lots_lus = resultat
        lignes, donnees, styles = [], [], []
        for ligne, dossier, c in resultat:
            etat, style = self._style_lot(c)
            lignes.append(ligne[:self.COL_LOT_COMPLET] + (etat,) + ligne[self.COL_LOT_COMPLET + 1:])
            donnees.append(dossier)
            styles.append(style)
        self.m_lots.remplir(lignes, donnees, None, styles)
        memoire.ajuster_colonnes(self.v_lots)
        self.l_lots.setText(tr('ohp_lots_resume', n=len(lignes), dest=coupable(dest)) if lignes
                            else tr('ohp_lots_aucun', dest=coupable(dest)))

    def _restyler_lots(self):
        par_dossier = {d: c for _, d, c in getattr(self, '_lots_lus', [])}
        styles = [self._style_lot(par_dossier.get(d))[1] for d in self.m_lots.donnees]
        self.m_lots.restyler(styles)

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
        inv, dest = self.inv, self.dest.text()
        pre = self._prendre('anomalies')
        if pre is not None:
            self._anomalies_pretes(pre)
            return
        self._t_anom = Tache(self.anomalies_de, inv, dest, parent=self)
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
        if self._genre_attendu:
            self.f_genre.setCurrentIndex(max(0, self.f_genre.findData(self._genre_attendu)))
            self._genre_attendu = None
        self.f_genre.blockSignals(False)
        self.l_anom.setText(tr('ohp_anomalies_intro') + ' ' + tr('ohp_anomalies_total', n=len(anoms)))
        self._filtrer_anomalies()

    def _filtrer_anomalies(self, *_):
        g = self.f_genre.currentData()
        sel = [a for a in self._anoms if (not g or a['genre'] == g) and (not self.f_anom_nouv.isChecked() or a['nouveau'])]
        self.m_anom.remplir([(a['genre'], tr('anom_action_' + a['action']), cibles.nom_affiche(a['objet']), a['nuit'],
                              a['fichier'], a['detail'], tr('anom_' + a['genre'])) for a in sel], sel,
                            [a['url'] for a in sel])
        memoire.ajuster_colonnes(self.v_anom)

    def _exporter_anomalies(self):
        from . import anomalies
        f, _ = QFileDialog.getSaveFileName(self, tr('ohp_anom_csv'),
                                           os.path.join(memoire.dossier('ohp_anomalies'), 'anomalies.csv'),
                                           'CSV (*.csv)')
        if f:
            memoire.retenir('ohp_anomalies', f, est_fichier=True)
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
        """Points de la carte (un par objet fixe, un par objet mobile et par nuit, à la médiane des poses) :
        regroupement et médianes hors du fil graphique."""
        if not self.inv:
            return
        cat = self.ciel_cat.currentData()
        pre = self._prendre('ciel')
        if pre is not None and pre[0] == cat:
            self._ciel_pret(pre[1])
            return
        self._t_ciel = Tache(self.points_ciel, self.inv.images, cat, parent=self)
        self._t_ciel.quand_fini(self._ciel_pret)
        self._t_ciel.start()

    @staticmethod
    def points_ciel(images, cat):
        import math
        import numpy as np
        groupes = {}
        for x in images:
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
            pts.append((ra, de, min(r, 14), x0['cat'],
                        tr('ohp_ciel_bulle', nom=nom, n=len(xs), cat=tr('ohp_cat_' + x0['cat'])), x0['objet']))
        return pts

    def _ciel_pret(self, pts):
        from PyQt6.QtGui import QColor
        couleurs = {}
        for c in {p[3] for p in pts}:
            couleurs[c] = QColor(self.COULEURS.get(c, '#95A5A6'))
        self.ciel.definir([(ra, de, r, couleurs[c], b, o) for ra, de, r, c, b, o in pts])

    def _ciel_clic(self, objet):
        for r, o in enumerate(self.m_obj.donnees):
            if o['objet'] == objet:
                idx = self.p_obj.mapFromSource(self.m_obj.index(r, 0))
                if not idx.isValid():                # objet masqué par les filtres du catalogue : on les lève
                    for c in (self.f_nouveaux, self.f_verifier, self.f_manquantes):
                        c.setChecked(False)
                    self.f_cat.setCurrentIndex(0)
                    self.f_tel.setCurrentIndex(0)
                    self.recherche.setText('')
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
        memoire.dialogue(self, 'correction')        # taille gardée d'une ouverture à l'autre

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
