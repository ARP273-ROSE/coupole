"""Panneau « Archives des observatoires » : recherche (noms usuels, corps du Système solaire, suggestions), un
produit logique par filtre (variantes en option), nature et temps de pose, taille estimée d'emblée, fiche et
vignette, téléchargement en deux phases (débit, temps restant), état final, réorganisation des téléchargements,
catalogue des cibles, guide du Hubble Ultra Deep Field, topo instruments et filtres, alignement et couleur.

Rien de lent dans le fil graphique : résolution du nom, recherche, mesure des tailles, vignettes, lecture de la base
d'état, téléchargements et alignement passent par des `Tache` ou des fils enregistrés (`lancer_fil`), dont les
événements arrivent par une `FileEvenements` lue à cadence fixe.  Le tableau est paresseux (`ModeleParesseux`) :
50 000 observations s'affichent et se trient sans gel.
"""
from __future__ import annotations

import hashlib
import html
import math
import os
import threading

from PyQt6.QtCore import QStringListModel, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QComboBox, QCompleter, QDoubleSpinBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QMenu, QMessageBox, QProgressBar, QSplitter, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from ...core import config
from ...core.i18n import tr
from ...gui import fichiers, memoire, ouvrir
from ...gui.adaptatif import Flux, coupable, texte_reel
from ...gui.modele import ModeleParesseux, vue_tableau
from ...gui.outils import FileEvenements, Tache, aide, bouton, case, champ, enregistrer_arret, lancer_fil, liste
from . import telechargement as T
from .services import ARCHIVES, PAR_DEFAUT

COLONNES = ('etat', 'mission', 'instrument', 'filtre', 'lambda', 'nature', 'exposition', 'date', 'cible', 'distance',
            'taille', 'archive')
ESTIMATION_MAX = 60               # tailles mesurées d'emblée (courtoisie) ; au-delà, extrapolées par groupe
CLE = 'modules.archives.'


def _taille(o) -> str:
    if not o:
        return ''
    return tr('taille_go', v='%.2f' % (o / 1e9)) if o >= 1e9 else tr('taille_mo', v='%.1f' % (o / 1e6))


def telecharger_vignette(url: str) -> str:
    """(Compatibilité 0.2.1) Vignette officielle réduite (voir ``apercus.py``) ; chemin du PNG ou ''."""
    from .apercus import vignette_officielle
    return vignette_officielle(url)[0]


def _tr_ou(cle: str, defaut: str = '') -> str:
    t = tr(cle)
    return defaut if t == cle else t


def _langue() -> str:
    from ...core.i18n import langue
    return langue()


def _duree(s: float) -> str:
    s = max(0, int(round(s)))
    if s < 60:
        return tr('arc_duree_s', s=s)
    if s < 3600:
        return tr('arc_duree_min', m=s // 60, s='%02d' % (s % 60))
    return tr('arc_duree_h', h=s // 3600, m='%02d' % ((s % 3600) // 60))


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.observations: list[dict] = []
        self.possession: dict = {}
        self.requete = None
        self._arret_recherche = threading.Event()
        self._arret_dl = enregistrer_arret(threading.Event())
        self._arret_estimation = enregistrer_arret(threading.Event())
        self._pause_dl = threading.Event()
        self._fil_dl = None
        self._taches = []
        self._octets_session = 0
        self._a_telecharger = 0
        self._programmes = ()
        v = QVBoxLayout(self)
        self.onglets = QTabWidget()
        self.onglets.addTab(self._onglet_recherche(), tr('arc_onglet_recherche'))
        from .gui_onglets import OngletCatalogue, OngletHudf, OngletInstruments
        self.catalogue = OngletCatalogue(self)
        self.hudf = OngletHudf(self)
        self.instruments = OngletInstruments(self)
        self.onglets.addTab(self.catalogue, tr('arc_onglet_catalogue'))
        self.onglets.addTab(self.hudf, tr('arc_onglet_hudf'))
        self.onglets.addTab(self.instruments, tr('arc_onglet_instruments'))
        self.onglets.addTab(self._onglet_alignement(), tr('arc_onglet_alignement'))
        for k, cle in enumerate(('arc_onglet_recherche_aide', 'arc_onglet_catalogue_aide', 'arc_onglet_hudf_aide',
                                 'arc_onglet_instruments_aide', 'arc_onglet_alignement_aide')):
            self.onglets.setTabToolTip(k, tr(cle))
        v.addWidget(self.onglets, 1)
        self.l_etat = QLabel(tr('arc_pret'))
        self.l_etat.setWordWrap(True)
        v.addWidget(self.l_etat)
        self._evts = FileEvenements(self, self._evenements, 150)
        self._memoriser()
        self.rafraichir_possession()

    # ================================================================================================ construction
    def _onglet_recherche(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        f = Flux()
        self.e_nom = champ('arc_nom_aide', '', 'arc_nom_indice')
        self.e_nom.returnPressed.connect(self.chercher)
        self.e_nom.setMinimumWidth(220)
        self._suggestions = QStringListModel([], self)
        cp = QCompleter(self._suggestions, self)
        cp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        cp.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.e_nom.setCompleter(cp)
        self.e_nom.textEdited.connect(self._proposer)
        f.addWidget(QLabel(tr('arc_nom')))
        f.addWidget(self.e_nom)
        self.s_rayon = aide(QDoubleSpinBox(), 'arc_rayon_aide')
        self.s_rayon.setRange(0.1, 180.0)
        self.s_rayon.setDecimals(1)
        self.s_rayon.setValue(3.0)
        self.s_rayon.setSuffix(' ' + tr('arc_arcmin'))
        f.addWidget(QLabel(tr('arc_rayon')))
        f.addWidget(self.s_rayon)
        self.b_chercher = bouton('arc_chercher', self.chercher)
        self.b_chercher.setDefault(True)
        f.addWidget(self.b_chercher)
        self.b_arreter_recherche = bouton('arc_arreter_recherche', self.arreter_recherche)
        self.b_arreter_recherche.setEnabled(False)
        f.addWidget(self.b_arreter_recherche)
        v.addLayout(f)
        f = Flux()
        self.cases_archives = {}
        for a in ARCHIVES.values():
            c = case('arc_case_archive', a.id in PAR_DEFAUT, cle_aide='arc_case_archive_aide')
            c.setText(tr('arc_nom_' + a.id))
            c.setToolTip(tr('arc_info_' + a.id))
            self.cases_archives[a.id] = c
            f.addWidget(c)
        v.addLayout(f)
        f = Flux()
        self.e_instrument = champ('arc_instrument_aide', '', 'arc_instrument_indice')
        self.e_filtre = champ('arc_filtre_aide', '', 'arc_filtre_indice')
        self.e_debut = champ('arc_debut_aide', '', 'arc_date_indice')
        self.e_fin = champ('arc_fin_aide', '', 'arc_date_indice')
        for cle, e in (('arc_instrument', self.e_instrument), ('arc_filtre', self.e_filtre),
                       ('arc_debut', self.e_debut), ('arc_fin', self.e_fin)):
            e.setMinimumWidth(110)
            f.addWidget(QLabel(tr(cle)))
            f.addWidget(e)
        self.c_finaux = case('arc_finaux', True)
        self.c_publics = case('arc_publics', True)
        self.c_variantes = case('arc_variantes', False)
        self.c_variantes.toggled.connect(lambda *_: self._afficher())
        f.addWidget(self.c_finaux)
        f.addWidget(self.c_publics)
        f.addWidget(self.c_variantes)
        v.addLayout(f)
        sp = QSplitter(Qt.Orientation.Horizontal)
        self.modele = ModeleParesseux([tr('arc_col_' + c) for c in COLONNES], self._ligne, style=self._style,
                                      bulle=self._bulle, cle=self._cle)
        self.vue, self.proxy = vue_tableau(self.modele, 'arc_table_aide')
        self.vue.message_vide = lambda: tr('arc_table_vide')
        self.vue.selectionModel().selectionChanged.connect(lambda *_: self._selection())
        self.vue.doubleClicked.connect(lambda *_: self._ouvrir_prepare())
        self.vue.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vue.customContextMenuRequested.connect(self._menu)
        sp.addWidget(self.vue)
        droite = QWidget()
        vd = QVBoxLayout(droite)
        vd.setContentsMargins(0, 0, 0, 0)
        self.l_vignette = aide(QLabel(), 'arc_vignette_aide')
        self.l_vignette.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l_vignette.setMinimumHeight(120)
        self.l_vignette.setWordWrap(True)
        vd.addWidget(self.l_vignette)
        self.fiche = aide(QTextBrowser(), 'arc_fiche_aide')
        self.fiche.setOpenExternalLinks(True)
        vd.addWidget(self.fiche, 1)
        sp.addWidget(droite)
        sp.setStretchFactor(0, 3)
        sp.setStretchFactor(1, 1)
        sp.setSizes([900, 360])
        self.sp = sp
        v.addWidget(sp, 1)
        self.l_selection = aide(QLabel(''), 'arc_selection_aide')
        v.addWidget(self.l_selection)
        f = Flux()
        f.addWidget(QLabel(tr('arc_dossier')))
        self.l_dossier = aide(QLabel(coupable(T.sortie_par_defaut())), 'arc_dossier_aide')
        self.l_dossier.setWordWrap(True)
        f.addWidget(self.l_dossier)
        f.addWidget(bouton('arc_choisir_dossier', self.choisir_dossier))
        self.c_format = liste('arc_format_aide', [(tr('arc_format_xisf'), 'xisf'), (tr('arc_format_fits'), 'fits')])
        f.addWidget(self.c_format)
        self.c_garder = case('arc_garder', False)
        self.c_masque = case('arc_masque', False)
        f.addWidget(self.c_garder)
        f.addWidget(self.c_masque)
        self.b_reorganiser = bouton('arc_reorganiser', self.reorganiser)
        f.addWidget(self.b_reorganiser)
        v.addLayout(f)
        f = Flux()
        self.b_telecharger = bouton('arc_telecharger', self.telecharger)
        self.b_pause = bouton('arc_pause', self.pause)
        self.b_annuler = bouton('arc_annuler', self.annuler)
        self.b_ouvrir_dossier = bouton('arc_ouvrir_dossier', self.ouvrir_dossier)
        for b in (self.b_telecharger, self.b_pause, self.b_annuler, self.b_ouvrir_dossier):
            f.addWidget(b)
        self.b_pause.setEnabled(False)
        self.b_annuler.setEnabled(False)
        self.barre = aide(QProgressBar(), 'arc_barre_aide')
        self.barre.setRange(0, 1000)
        self.barre.setValue(0)
        self.barre.setTextVisible(True)
        self.barre.setFormat('')
        v.addLayout(f)
        v.addWidget(self.barre)
        self.l_progres = aide(QLabel(''), 'arc_progres_aide')
        self.l_progres.setWordWrap(True)
        v.addWidget(self.l_progres)
        return w

    def _onglet_alignement(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        intro = QLabel(tr('arc_al_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        f = Flux()
        f.addWidget(bouton('arc_al_rafraichir', self.rafraichir_possession))
        f.addWidget(bouton('arc_al_ajouter', self.ajouter_fichiers))
        f.addWidget(bouton('arc_al_retirer', self.retirer_fichiers))
        v.addLayout(f)
        sp = QSplitter(Qt.Orientation.Horizontal)
        self.l_fichiers = aide(QListWidget(), 'arc_al_liste_aide')
        self.l_fichiers.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.l_fichiers.itemChanged.connect(lambda *_: self._maj_references())
        sp.addWidget(self.l_fichiers)
        self.l_apercu = aide(QLabel(tr('arc_al_pas_apercu')), 'arc_al_apercu_aide')
        self.l_apercu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l_apercu.setWordWrap(True)
        self.l_apercu.setMinimumSize(160, 160)
        from PyQt6.QtWidgets import QSizePolicy
        self.l_apercu.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        sp.addWidget(self.l_apercu)
        self.sp_al = sp
        v.addWidget(sp, 1)
        f = Flux()
        f.addWidget(QLabel(tr('arc_al_reference')))
        self.c_reference = liste('arc_al_reference_aide', [(tr('arc_al_optimale'), -1)])
        f.addWidget(self.c_reference)
        f.addWidget(QLabel(tr('arc_al_methode')))
        self.c_methode = liste('arc_al_methode_aide', [(tr('arc_al_bilineaire'), 'bilineaire'),
                                                       (tr('arc_al_adaptative'), 'adaptative'),
                                                       (tr('arc_al_exacte'), 'exacte'), (tr('arc_al_proche'), 'proche')])
        f.addWidget(self.c_methode)
        f.addWidget(QLabel(tr('arc_al_echelle')))
        self.s_echelle = aide(QDoubleSpinBox(), 'arc_al_echelle_aide')
        self.s_echelle.setRange(1.0, 16.0)
        self.s_echelle.setDecimals(1)
        self.s_echelle.setValue(1.0)
        f.addWidget(self.s_echelle)
        self.c_recadrer = case('arc_al_recadrer', True)
        f.addWidget(self.c_recadrer)
        self.b_aligner = bouton('arc_al_aligner', self.aligner)
        f.addWidget(self.b_aligner)
        v.addLayout(f)
        self.t_compo = aide(QTextBrowser(), 'arc_al_compo_aide')
        self.t_compo.setMaximumHeight(160)
        v.addWidget(self.t_compo)
        return w

    def _memoriser(self):
        memoire.champ(self.e_nom, CLE + 'nom')
        memoire.nombre(self.s_rayon, CLE + 'rayon')
        for k, c in self.cases_archives.items():
            memoire.case(c, CLE + 'archive.' + k)
        for nom, e in (('instrument', self.e_instrument), ('filtre', self.e_filtre), ('debut', self.e_debut),
                       ('fin', self.e_fin)):
            memoire.champ(e, CLE + nom)
        memoire.case(self.c_finaux, CLE + 'finaux')
        memoire.case(self.c_publics, CLE + 'publics')
        memoire.case(self.c_variantes, CLE + 'variantes')
        memoire.case(self.c_garder, CLE + 'garder_022')          # nouvelle clé : décochée par défaut depuis 0.2.2
        memoire.case(self.c_masque, CLE + 'masque')
        memoire.liste(self.c_format, CLE + 'format')
        memoire.liste(self.c_methode, CLE + 'methode')
        memoire.case(self.c_recadrer, CLE + 'recadrer')
        memoire.onglets(self.onglets, CLE + 'onglet')
        memoire.separateur(self.sp, CLE + 'separateur')
        memoire.separateur(self.sp_al, CLE + 'separateur_alignement')
        memoire.entete(self.vue, CLE + 'colonnes_022')
        from ...core.etat_interface import etat
        d = etat().lire(CLE + 'dossier', '', str)
        if d:
            self.l_dossier.setText(coupable(d))
        memoire.memoire().suivre(CLE + 'dossier', lambda: texte_reel(self.l_dossier.text()), self.l_dossier)

    # ================================================================================================ tableau
    def _statut(self, o) -> str:
        return self.possession.get(o['id'], {}).get('statut', 'absente')

    @staticmethod
    def nature(o) -> str:
        n = o.get('nature') or ''
        if not n:
            return ''
        if n in ('combine', 'mosaique') and o.get('poses') and o['poses'] > 1:
            t = tr('arc_nature_%s_n' % n, n=o['poses'])
        else:
            t = tr('arc_nature_' + n)
        if o.get('variante'):
            t += ' · ' + tr('arc_variante_court')
        elif o.get('final') and n == 'pose':
            t += ' · ' + tr('arc_calibree_court')
        elif o.get('final') and n != 'detection':
            t += ' · ' + tr('arc_final_court')
        return t

    def _ligne(self, o):
        from .produits import resume_exposition
        st = self._statut(o)
        return (tr('arc_statut_' + st), o['mission'], o['instrument'], o['filtre'],
                ('%.0f' % o['lambda_nm']) if o['lambda_nm'] else '', self.nature(o),
                resume_exposition(o.get('exposition'), o.get('poses')), (o['debut'] or '')[:10], o['cible'],
                ('%.2f' % (o['distance'] * 60)) if o['distance'] is not None else '',
                (('≈ ' if o.get('taille_estimee') else '') + _taille(o['taille'])) if o.get('taille') else
                (tr('arc_taille_en_cours') if o.get('_mesure') else ''),
                tr('arc_nom_' + o['archive']))

    def _style(self, o):
        from ...gui import pastilles
        st = self._statut(o)
        nom = {'ok': 'ok', 'echec': 'echec'}.get(st, 'absente')
        s = {'icones': {0: pastilles.pastille(nom)}}
        if st in ('ok', 'echec'):
            s['couleurs'] = {0: pastilles.couleur_statut(nom)}
        if not o['public'] or o.get('variante'):
            s['couleur'] = pastilles.couleur_statut('ecarte')
        s['bulles'] = {COLONNES.index('filtre'): lambda o=o: self._bulle_filtre(o),
                       COLONNES.index('nature'): lambda o=o: self._bulle_nature(o),
                       COLONNES.index('exposition'): lambda: tr('arc_exposition_aide'),
                       COLONNES.index('taille'): lambda: tr('arc_taille_aide')}
        return s

    def _bulle_filtre(self, o):
        from ...core.i18n import langue
        from .instruments import bulle_filtre
        return bulle_filtre(o['filtre'], o['instrument'], langue()) or tr('arc_filtre_inconnu', filtre=o['filtre'])

    def _bulle_nature(self, o):
        t = [tr('arc_nature_aide_' + o['nature'])] if o.get('nature') else []
        if o.get('produit') and o['produit'] not in ('autre',):
            t.append(_tr_ou('arc_produit_' + o['produit']))
        if o.get('raison'):
            t.append(tr(o['raison']))
        return '\n'.join(x for x in t if x)

    def _bulle(self, o):
        return tr('arc_bulle', id=o['id'], credit=o['credit'] or '-')

    def _cle(self, col):
        nom = COLONNES[col] if 0 <= col < len(COLONNES) else ''
        if nom == 'lambda':
            return lambda o: o['lambda_nm'] if o['lambda_nm'] is not None else math.inf
        if nom == 'distance':
            return lambda o: o['distance'] if o['distance'] is not None else math.inf
        if nom == 'taille':
            return lambda o: o.get('taille') or 0
        if nom == 'exposition':
            return lambda o: o.get('exposition') or 0
        if nom == 'nature':
            return lambda o: (bool(o.get('variante')), o.get('nature') or '')
        if nom == 'date':
            return lambda o: o['debut'] or ''
        if nom == 'etat':
            return lambda o: {'ok': 0, 'echec': 1}.get(self._statut(o), 2)
        return None

    def choisies(self) -> list[dict]:
        sm = self.vue.selectionModel()
        rangs = sorted({self.proxy.mapToSource(i).row() for i in sm.selectedRows()})
        return [self.modele.donnees[r] for r in rangs]

    # ================================================================================================ recherche
    def _proposer(self, texte):
        from ...core.i18n import langue
        from .recherche import suggestions
        self._suggestions.setStringList(suggestions(texte, langue()))

    def _requete_ui(self):
        from .services.base import Requete
        archives = tuple(k for k, c in self.cases_archives.items() if c.isChecked())
        texte = self.e_nom.text().strip()
        q = Requete(nom=texte, rayon=self.s_rayon.value() / 60.0, archives=archives,
                    instruments=tuple(x.strip() for x in self.e_instrument.text().split(',') if x.strip()),
                    filtres=tuple(x.strip() for x in self.e_filtre.text().split(',') if x.strip()),
                    date_min=self.e_debut.text().strip(), date_max=self.e_fin.text().strip(),
                    finaux=self.c_finaux.isChecked(), publics=self.c_publics.isChecked())
        if self._programmes:
            q.extra['programmes'] = tuple(self._programmes)
        return q

    def chercher_texte(self, texte: str, rayon_arcmin: float | None = None, programmes=()):
        """Recherche lancée depuis le catalogue ou le guide (texte, rayon, programmes à garder)."""
        self.onglets.setCurrentIndex(0)
        self.e_nom.setText(texte)
        if rayon_arcmin:
            self.s_rayon.setValue(rayon_arcmin)
        self._programmes = tuple(programmes or ())
        self.chercher()
        self._programmes = ()

    def chercher(self):
        if not self.e_nom.text().strip():
            self.l_etat.setText(tr('arc_nom_requis'))
            return
        q = self._requete_ui()
        from .recherche import interpreter
        i = interpreter(q.nom)
        if i['genre'] != 'corps' and not any(self.cases_archives[a].isChecked() and ARCHIVES[a].celeste
                                             for a in self.cases_archives):
            self.l_etat.setText(tr('arc_aucune_archive'))
            return
        self._arret_recherche = threading.Event()
        self.b_chercher.setEnabled(False)
        self.b_arreter_recherche.setEnabled(True)
        self.l_etat.setText(tr('arc_recherche_en_cours'))
        evts = self._evts
        arret = self._arret_recherche

        def travail():
            from .recherche import archives_pour, chercher, resoudre, toutes
            if i['genre'] == 'corps':
                q.cible = i['corps']['en']
                archives = archives_pour(q, q.archives)
                evts({'genre': 'corps', 'nom': i['corps'].nom(_langue()), 'archives': archives})
            else:
                r = resoudre(q.nom)
                q.ra, q.dec = r['ra'], r['dec']
                evts({'genre': 'resolu', 'ra': q.ra, 'dec': q.dec, 'nom': r.get('nom') or q.nom})
                archives = archives_pour(q, q.archives)
            resultats = chercher(q, archives, arret, rapporter=lambda **e: evts(dict(e)))
            return q, resultats, toutes(resultats)
        t = Tache(travail, parent=self)
        t.quand_fini(self._resultats)
        t.quand_erreur(self._erreur_recherche)
        self._taches.append(t)
        t.start()

    def arreter_recherche(self):
        self._arret_recherche.set()
        self.b_arreter_recherche.setEnabled(False)

    def _erreur_recherche(self, e):
        self.b_chercher.setEnabled(True)
        self.b_arreter_recherche.setEnabled(False)
        if e.startswith('LookupError'):
            from .recherche import suggestions
            prop = suggestions(self.e_nom.text().strip(), _langue(), 5)
            self.l_etat.setText(tr('arc_introuvable', nom=self.e_nom.text().strip()) +
                                ((' ' + tr('arc_peut_etre', noms=', '.join(prop))) if prop else '') + ' ' +
                                tr('arc_introuvable_conseil'))
        else:
            self.l_etat.setText(tr('arc_resolution_impossible', erreur=e))

    def _resultats(self, r):
        q, resultats, obs = r
        self.requete = q
        self.b_chercher.setEnabled(True)
        self.b_arreter_recherche.setEnabled(False)
        self.observations = obs
        self._afficher()
        if obs and not getattr(self, '_colonnes_ajustees', False):
            self._colonnes_ajustees = True
            for c in range(len(COLONNES) - 1):
                self.vue.resizeColumnToContents(c)
        morceaux = []
        for x in resultats:
            nom = tr('arc_nom_' + x.archive)
            if x.compte_requis:
                morceaux.append(tr('arc_compte_requis', archive=nom))
            elif x.non_pris_en_charge:
                morceaux.append(tr('arc_non_pris', archive=nom, lien=x.erreur))
            elif x.erreur:
                morceaux.append(tr('arc_erreur_archive', archive=nom, erreur=x.erreur[:160]))
            else:
                morceaux.append(tr('arc_resultat_archive', archive=nom, n=len(x.observations), s='%.1f' % x.secondes) +
                                (' ' + tr('arc_tronque') if x.tronque else ''))
        caches = sum(1 for o in obs if o.get('variante'))
        texte = tr('arc_total', n=len(obs) - caches)
        if caches and not self.c_variantes.isChecked():
            texte += ' ' + tr('arc_variantes_cachees', n=caches)
        self.l_etat.setText(texte + ' — ' + ' ; '.join(morceaux))
        self.rafraichir_possession()
        self.estimer_auto()

    def visibles(self) -> list[dict]:
        from .produits import visibles
        return visibles(self.observations, self.c_variantes.isChecked())

    def _afficher(self):
        self.modele.remplir_objets(self.visibles())
        self._maj_selection()

    # ------------------------------------------------------------------ tailles d'emblée
    def estimer_auto(self, obs=None):
        """Mesure en fond les tailles inconnues (requête d'un octet, une à la fois par archive, au plus
        `ESTIMATION_MAX` fichiers ; les autres extrapolées) ; le tableau et le total se mettent à jour seuls."""
        obs = [o for o in (obs if obs is not None else self.visibles()) if not o.get('taille') and not o.get('_mesure')]
        if not obs:
            return
        self._arret_estimation.set()
        self._arret_estimation = enregistrer_arret(threading.Event())
        arret = self._arret_estimation
        for o in obs:
            o['_mesure'] = True
        evts = self._evts

        def travail():
            try:
                lot = obs[:ESTIMATION_MAX * 4]
                T.estimer(lot, arret=arret, progression=lambda n: evts({'genre': 'taille'}))
            finally:
                for o in obs:
                    o['_mesure'] = False
                evts({'genre': 'taille', 'fin': True})
        lancer_fil(travail)

    def estimer(self):
        """(Compatibilité) estimation des lignes choisies, désormais automatique."""
        self.estimer_auto(self.choisies())

    def _maj_selection(self):
        sel = self.choisies()
        if not sel:
            vis = self.modele.donnees
            tot = sum(o.get('taille') or 0 for o in vis)
            self.l_selection.setText(tr('arc_selection_aucune', n=len(vis), taille=_taille(tot) or '?') if vis else '')
            return
        tot = sum(o.get('taille') or 0 for o in sel)
        inconnus = sum(1 for o in sel if not o.get('taille'))
        approx = any(o.get('taille_estimee') for o in sel) or inconnus
        self.l_selection.setText(tr('arc_selection', n=len(sel), taille=('≈ ' if approx else '') + (_taille(tot) or '0'))
                                 + ((' ' + tr('arc_selection_inconnus', n=inconnus)) if inconnus else ''))

    # ================================================================================================ fiche
    def _selection(self):
        self._maj_selection()
        sel = self.choisies()
        if len(sel) != 1:
            if sel:
                self.fiche.setHtml('<p>%s</p>' % html.escape(self.l_selection.text()))
                if any(not o.get('taille') for o in sel):
                    self.estimer_auto(sel)
            return
        o = sel[0]
        self.fiche.setHtml(self.html_fiche(o))
        self.l_vignette.clear()
        self.l_vignette.setText(tr('arc_apercu_chargement'))
        from .apercus import vignette
        t = Tache(vignette, o, self._prepare(o), parent=self)
        t.quand_fini(lambda r, ident=o['id']: self._vignette(r, ident))
        self._taches.append(t)
        t.start()

    def _vignette(self, r, ident):
        sel = self.choisies()
        if len(sel) != 1 or sel[0]['id'] != ident:
            return
        chemin, raison = r if isinstance(r, tuple) else (r, '')
        pm = QPixmap(chemin) if chemin else QPixmap()
        if pm.isNull():
            self.l_vignette.setText(tr('arc_pas_de_vignette') + ' — ' + tr(raison or 'arc_apercu_illisible'))
            return
        self.l_vignette.setPixmap(pm.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
        self.l_vignette.setToolTip(tr(raison) if raison else tr('arc_vignette_aide'))

    def html_fiche(self, o) -> str:
        from .produits import resume_exposition
        e = html.escape
        lignes = [('arc_f_archive', tr('arc_nom_' + o['archive'])), ('arc_f_mission', o['mission']),
                  ('arc_f_instrument', o['instrument']), ('arc_f_filtre', o['filtre']),
                  ('arc_f_lambda', ('%.0f nm' % o['lambda_nm']) if o['lambda_nm'] else ''),
                  ('arc_f_nature', self.nature(o)),
                  ('arc_f_exposition', resume_exposition(o.get('exposition'), o.get('poses'))),
                  ('arc_f_debut', o['debut']), ('arc_f_publique', o['publique']), ('arc_f_cible', o['cible']),
                  ('arc_f_coord', ('%.5f° %+.5f°' % (o['ra'], o['dec'])) if o['ra'] is not None else ''),
                  ('arc_f_programme', o['programme']), ('arc_f_pi', o['pi']), ('arc_f_titre', o['titre']),
                  ('arc_f_calib', _tr_ou('arc_calib_%s' % o['calib'], str(o['calib'])) if o['calib'] is not None else ''),
                  ('arc_f_fichier', o['fichier']), ('arc_f_taille', _taille(o.get('taille')))]
        h = ['<h3>%s</h3>' % e(o['obs_id'] or o['id'])]
        if o.get('final') and not o.get('variante') and o.get('nature') not in ('detection', 'pose'):
            h.append('<p><span style="background:#2e7d32;color:white">&nbsp;%s&nbsp;</span> %s</p>' % (
                e(tr('arc_badge_final')), e(tr('arc_badge_final_aide'))))
        elif o.get('final') and o.get('nature') == 'pose':
            h.append('<p><span style="background:#1565c0;color:white">&nbsp;%s&nbsp;</span> %s</p>' % (
                e(tr('arc_badge_pose')), e(tr('arc_badge_pose_aide'))))
        h.append('<table>')
        for cle, val in lignes:
            if val:
                h.append('<tr><td><b>%s</b>&nbsp;</td><td>%s</td></tr>' % (e(tr(cle)), e(str(val))))
        h.append('</table>')
        bf = self._bulle_filtre(o)
        if bf and o['filtre']:
            h.append('<p>%s</p>' % e(bf).replace('\n', '<br>'))
        if o.get('produit') and o['produit'] != 'autre':
            h.append('<p><b>%s</b> %s</p>' % (e(tr('arc_f_produit')), e(_tr_ou('arc_produit_' + o['produit']))))
        if o.get('raison'):
            h.append('<p><i>%s</i></p>' % e(tr(o['raison'])))
        if o.get('produit') == 'mvm':
            h.append('<p>%s</p>' % e(tr('arc_f_mvm_taille')))
        if o.get('nature'):
            h.append('<p>%s</p>' % e(tr('arc_nature_aide_' + o['nature'])))
        h.append('<p>%s</p>' % e(tr('arc_unites_aide')))
        if not o['public']:
            h.append('<p><b>%s</b></p>' % e(tr('arc_f_reservee')))
        p = self.possession.get(o['id'], {})
        if p.get('statut') == 'ok':
            h.append('<p>%s</p>' % e(tr('arc_f_possede', chemin=p.get('prepare', ''))))
            if p.get('forme_origine') and p.get('forme') and list(p['forme_origine']) != list(p['forme']):
                h.append('<p>%s</p>' % e(tr('arc_f_recadre', avant='%d × %d' % (p['forme_origine'][1], p['forme_origine'][0]),
                                             apres='%d × %d' % (p['forme'][1], p['forme'][0]))))
        h.append('<p><b>%s</b> %s</p>' % (e(tr('arc_f_credit')), e(o['credit'])))
        if o['conditions']:
            h.append('<p>%s</p>' % e(tr(o['conditions'])))
        if o['page']:
            h.append('<p><a href="%s">%s</a></p>' % (e(o['page']), e(tr('arc_f_page'))))
        return ''.join(h)

    # ================================================================================================ possession
    def dossier(self) -> str:
        return texte_reel(self.l_dossier.text())

    def choisir_dossier(self):
        d = fichiers.choisir_dossier(self, tr('arc_choisir_dossier'), self.dossier())
        if d:
            self.l_dossier.setText(coupable(d))
            memoire.memoire().signaler()
            self.rafraichir_possession()

    def rafraichir_possession(self):
        t = Tache(T.possession, self.dossier(), parent=self)
        t.quand_fini(self._possession)
        self._taches.append(t)
        t.start()

    def _possession(self, p):
        self.possession = p or {}
        self.modele.invalider()
        self._remplir_fichiers()

    def _remplir_fichiers(self):
        coches = {self.l_fichiers.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.l_fichiers.count())
                  if self.l_fichiers.item(i).checkState() == Qt.CheckState.Checked}
        manuels = [self.l_fichiers.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.l_fichiers.count())
                   if self.l_fichiers.item(i).data(Qt.ItemDataRole.UserRole + 1)]
        self.l_fichiers.blockSignals(True)
        self.l_fichiers.clear()
        racine = T.dossier_archives(self.dossier())
        for ident, d in sorted(self.possession.items(), key=lambda kv: (kv[1].get('cible', ''), kv[1].get('lambda_nm') or 0)):
            if d.get('statut') != 'ok' or not d.get('wcs'):
                continue
            prepares = [d['prepare']] + list(d.get('autres') or [])
            for k, rel in enumerate(prepares):
                chemin = os.path.join(racine, rel)
                it = QListWidgetItem('%s — %s %s %s%s' % (d.get('cible', ''), d.get('mission', ''), d.get('instrument', ''),
                                                          d.get('filtre', ''), (' #%d' % (k + 1)) if len(prepares) > 1 else ''))
                it.setData(Qt.ItemDataRole.UserRole, chemin)
                it.setToolTip(chemin)
                it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                it.setCheckState(Qt.CheckState.Checked if chemin in coches else Qt.CheckState.Unchecked)
                self.l_fichiers.addItem(it)
        for chemin in manuels:
            self._ajouter_fichier(chemin, chemin in coches)
        self.l_fichiers.blockSignals(False)
        self._maj_references()

    def _ajouter_fichier(self, chemin, coche=True):
        it = QListWidgetItem(os.path.basename(chemin))
        it.setData(Qt.ItemDataRole.UserRole, chemin)
        it.setData(Qt.ItemDataRole.UserRole + 1, True)
        it.setToolTip(chemin)
        it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        it.setCheckState(Qt.CheckState.Checked if coche else Qt.CheckState.Unchecked)
        self.l_fichiers.addItem(it)

    def ajouter_fichiers(self):
        c, _ = fichiers.choisir_fichier(self, tr('arc_al_ajouter'), self.dossier(), tr('arc_al_filtre_fichiers'))
        if c:
            self._ajouter_fichier(c)
            self._maj_references()

    def retirer_fichiers(self):
        for it in self.l_fichiers.selectedItems():
            self.l_fichiers.takeItem(self.l_fichiers.row(it))
        self._maj_references()

    def fichiers_coches(self) -> list[str]:
        return [self.l_fichiers.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.l_fichiers.count())
                if self.l_fichiers.item(i).checkState() == Qt.CheckState.Checked]

    def _maj_references(self):
        avant = self.c_reference.currentData()
        self.c_reference.blockSignals(True)
        self.c_reference.clear()
        self.c_reference.addItem(tr('arc_al_optimale'), -1)
        for k, c in enumerate(self.fichiers_coches()):
            self.c_reference.addItem(os.path.basename(c), k)
        i = self.c_reference.findData(avant)
        self.c_reference.setCurrentIndex(max(0, i))
        self.c_reference.blockSignals(False)

    # ================================================================================================ téléchargement
    def _a_traiter(self) -> list[dict]:
        return self.choisies()

    def telecharger(self, obs=None, cible: str | None = None):
        obs = [o for o in (obs if obs is not None else self._a_traiter()) if self._statut(o) != 'ok']
        if not obs:
            self.l_etat.setText(tr('arc_rien_a_telecharger'))
            return
        if self._fil_dl is not None and self._fil_dl.is_alive():
            return
        self.b_telecharger.setEnabled(False)
        self.l_etat.setText(tr('arc_estimation_en_cours', n=len(obs)))
        t = Tache(T.estimer, obs, parent=self)
        t.quand_fini(lambda e: self._confirmer(obs, e, cible))
        t.quand_erreur(lambda e: (self.b_telecharger.setEnabled(True), self.l_etat.setText(e)))
        self._taches.append(t)
        t.start()

    def _confirmer(self, obs, e, cible=None):
        self.modele.invalider(styles=False)
        if e['octets'] > T.seuil_octets():
            r = QMessageBox.question(self, tr('arc_confirmer_titre'),
                                     tr('arc_confirmer', n=e['n'], taille=_taille(e['octets']),
                                        seuil=_taille(T.seuil_octets())))
            if r != QMessageBox.StandardButton.Yes:
                self.b_telecharger.setEnabled(True)
                self.l_etat.setText(tr('arc_pret'))
                return
        self._lancer(obs, e['octets'], cible)

    def _lancer(self, obs, octets, cible=None):
        r = config.reglages()
        debit = float(r.get('archives_debit_mo_s', r['debit_max_mo_s']) or 8.0) * 1e6
        if cible is None:
            cible = self.requete.nom if self.requete is not None and self.requete.nom else ''
            from .recherche import interpreter
            i = interpreter(cible) if cible else {'genre': 'vide'}
            if i['genre'] == 'coordonnees':
                cible = i.get('alias') and cible or ''
            elif i['genre'] == 'corps':
                cible = i['corps'].nom(_langue())
        self._arret_dl.clear()
        self._pause_dl.clear()
        self._octets_session = 0
        self._a_telecharger = len(obs)
        self._faits = 0
        self._prepares = 0
        self._telecharges = 0
        self._ids_dl = set()
        self._erreurs = 0
        self._tailles = {o['id']: o.get('taille') or 0 for o in obs}
        self._total_octets = max(1, sum(self._tailles.values()))
        self._recus = {}
        self._debits = []                     # (instant, octets) pour le débit glissant
        import time
        self._t0 = time.monotonic()
        self.barre.setRange(0, 1000)
        self.barre.setValue(0)
        self.barre.setFormat(tr('arc_phase_telechargement') + ' %p %')
        evts = self._evts
        t = T.Telechargement(self.dossier(), obs, cible=cible, fmt=self.c_format.currentData() or 'xisf',
                             garder_original=self.c_garder.isChecked(), masque=self.c_masque.isChecked(),
                             debit_octets_s=debit, paralleles=2, rapporter=lambda ev: evts(dict(ev, source='dl')),
                             arret=self._arret_dl, pause=self._pause_dl)
        self._fil_dl = lancer_fil(t.executer)
        self.b_pause.setEnabled(True)
        self.b_annuler.setEnabled(True)
        self.l_etat.setText(tr('arc_telechargement_en_cours', n=len(obs)))

    def pause(self):
        if self._pause_dl.is_set():
            self._pause_dl.clear()
            self.b_pause.setText(tr('arc_pause'))
        else:
            self._pause_dl.set()
            self.b_pause.setText(tr('arc_reprendre'))

    def annuler(self):
        self._arret_dl.set()
        self._pause_dl.clear()
        self.b_annuler.setEnabled(False)

    def _maj_progression(self):
        """Barre en deux phases : 0 → 70 % pendant le téléchargement (octets), 70 → 100 % pendant la préparation
        (fichiers) ; texte : débit glissant, temps restant du fichier en cours et de l'ensemble."""
        import time
        n = max(1, self._a_telecharger)
        frac_dl = min(1.0, self._octets_session / self._total_octets) if self._total_octets else 0
        frac_dl = max(frac_dl, self._telecharges / n)
        frac_prep = self._faits / n
        self.barre.setValue(int(1000 * (0.7 * frac_dl + 0.3 * frac_prep)))
        en_prep = self._telecharges >= n or (self._telecharges > self._faits)
        self.barre.setFormat((tr('arc_phase_preparation') if en_prep and frac_dl >= 0.999 else
                              tr('arc_phase_telechargement')) + ' %p %')
        t = time.monotonic()
        self._debits = [(a, b) for a, b in self._debits if t - a <= 8] + [(t, self._octets_session)]
        debit = 0.0
        if len(self._debits) >= 2 and self._debits[-1][0] > self._debits[0][0]:
            debit = (self._debits[-1][1] - self._debits[0][1]) / (self._debits[-1][0] - self._debits[0][0])
        reste = max(0, self._total_octets - self._octets_session)
        morceaux = [tr('arc_progres_fichiers', telecharges=self._telecharges, prepares=self._faits, n=n),
                    tr('arc_progres_octets', fait=_taille(self._octets_session) or '0', total=_taille(self._total_octets))]
        if debit > 0:
            morceaux.append(tr('arc_progres_debit', debit='%.1f' % (debit / 1e6)))
            if reste:
                morceaux.append(tr('arc_progres_reste', duree=_duree(reste / debit)))
            for ident, recu in self._recus.items():
                tot = self._tailles.get(ident) or 0
                if tot and recu < tot:
                    morceaux.append(tr('arc_progres_fichier', fait=_taille(recu) or '0', total=_taille(tot),
                                       duree=_duree((tot - recu) / debit)))
                    break
        self.l_progres.setText(' — '.join(morceaux))

    def _evenements(self, evs):
        maj = False
        for ev in evs:
            g = ev.get('genre')
            if g == 'resolu':
                self.l_etat.setText(tr('arc_position', ra='%.5f' % ev['ra'], dec='%+.5f' % ev['dec'],
                                       r='%.1f' % self.s_rayon.value()))
            elif g == 'corps':
                self.l_etat.setText(tr('arc_corps_recherche', nom=ev['nom'],
                                       archives=', '.join(tr('arc_nom_' + a) for a in ev['archives'])))
            elif g == 'taille':
                maj = True
            elif g == 'aligne_image':
                self.l_etat.setText(tr('arc_alignement_image', k=ev['k'] + 1, n=ev['n'], nom=ev['nom']))
            elif g == 'reorg':
                self.l_progres.setText(tr('arc_reorg_progres', k=ev['k'], n=ev['n']))
                self.barre.setRange(0, max(1, ev['n']))
                self.barre.setValue(ev['k'])
            elif g == 'archive_debut':
                self.l_etat.setText(tr('arc_interroge', archive=tr('arc_nom_' + ev['archive'])))
            elif g == 'octets':
                self._octets_session = ev['octets']
                self._recus = ev.get('recus') or {}
                self._maj_progression()
            elif g == 'telecharge':
                self._ids_dl.add(ev['id'])
                self._telecharges = len(self._ids_dl)
                self._recus.pop(ev['id'], None)
                self._maj_progression()
            elif g in ('fini', 'deja', 'erreur'):
                self._faits = getattr(self, '_faits', 0) + 1
                self._ids_dl.add(ev['id'])
                self._telecharges = len(self._ids_dl)
                if g == 'erreur':
                    self._erreurs += 1
                    self.l_etat.setText(tr('arc_echec', id=ev['id'], erreur=ev['erreur'][:200]))
                if g == 'fini' and ev.get('forme_origine') and ev['forme_origine'] != ev.get('forme'):
                    fo, fn = ev['forme_origine'], ev['forme']
                    self.l_etat.setText(tr('arc_fini_recadre', chemin=os.path.basename(ev['chemin']),
                                           avant='%d × %d' % (fo[1], fo[0]), apres='%d × %d' % (fn[1], fn[0])))
                self._maj_progression()
            elif g == 'fin':
                b = ev['bilan']
                self.b_pause.setEnabled(False)
                self.b_annuler.setEnabled(False)
                self.b_telecharger.setEnabled(True)
                self.b_pause.setText(tr('arc_pause'))
                self.barre.setValue(1000)
                cle = 'arc_termine_annule' if b.get('annule') else 'arc_termine'
                self.barre.setFormat(tr('arc_phase_termine'))
                self.l_progres.setText('')
                self.l_etat.setText(tr(cle, n=b.get('ok', 0) + b.get('deja', 0),
                                       telecharge=_taille(b.get('octets', 0)) or '0',
                                       garde=_taille(b.get('octets_gardes', 0)) or '0', erreurs=b.get('echec', 0),
                                       s=_duree(b.get('secondes', 0))))
                self.b_ouvrir_dossier.setFocus()
                self.rafraichir_possession()
        if maj:
            self.modele.invalider(styles=False)
            self._maj_selection()

    # ------------------------------------------------------------------ réorganisation
    def reorganiser(self):
        from . import rangement as RG
        if self._fil_dl is not None and self._fil_dl.is_alive():
            return
        sortie = self.dossier()
        actions = RG.plan(sortie)
        if not actions:
            self.l_etat.setText(tr('arc_reorg_rien'))
            return
        variantes = sum(1 for a in actions if a['variante'])
        exemples = '\n'.join('  %s\n  → %s' % (a['de'], a['vers']) for a in actions[:4])
        r = QMessageBox.question(self, tr('arc_reorg_titre'),
                                 tr('arc_reorg_confirmer', n=len(actions), variantes=variantes, exemples=exemples))
        if r != QMessageBox.StandardButton.Yes:
            return
        self.b_reorganiser.setEnabled(False)
        evts = self._evts
        t = Tache(RG.reorganiser, sortie, True, self.c_masque.isChecked(), False,
                  lambda k, n: evts({'genre': 'reorg', 'k': k, 'n': n}), parent=self)
        t.quand_fini(self._reorganise)
        t.quand_erreur(lambda e: (self.b_reorganiser.setEnabled(True), self.l_etat.setText(e)))
        self._taches.append(t)
        t.start()

    def _reorganise(self, b):
        self.b_reorganiser.setEnabled(True)
        self.barre.setRange(0, 1000)
        self.barre.setValue(1000)
        self.l_progres.setText('')
        self.l_etat.setText(tr('arc_reorg_fini', deplaces=b['deplaces'], recadres=b['recadres'], masques=b['masques'],
                               avant=_taille(b['octets_avant']) or '0', apres=_taille(b['octets_apres']) or '0',
                               erreurs=len(b['erreurs'])))
        self.rafraichir_possession()

    # ================================================================================================ fichiers
    def _prepare(self, o) -> str:
        p = self.possession.get(o['id'], {})
        return os.path.join(T.dossier_archives(self.dossier()), p['prepare']) if p.get('prepare') else ''

    def _ouvrir_prepare(self):
        sel = self.choisies()
        if len(sel) == 1 and self._prepare(sel[0]) and os.path.exists(self._prepare(sel[0])):
            ouvrir.ouvrir_defaut(self._prepare(sel[0]))

    def _menu(self, pos):
        sel = self.choisies()
        if len(sel) != 1:
            return
        m = QMenu(self.vue)
        ouvrir.remplir_menu(m, self._prepare(sel[0]))
        if sel[0]['page']:
            from PyQt6.QtCore import QUrl
            from PyQt6.QtGui import QDesktopServices
            a = ouvrir.action(m, tr('arc_f_page'), True, tr('arc_f_page'))
            a.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(sel[0]['page'])))
        ouvrir.montrer_menu(m, self.vue.viewport().mapToGlobal(pos))

    def ouvrir_dossier(self):
        d = T.dossier_archives(self.dossier())
        os.makedirs(d, exist_ok=True)
        ouvrir.montrer_emplacement(d)

    # ================================================================================================ alignement
    def aligner(self):
        chemins = self.fichiers_coches()
        if len(chemins) < 2:
            self.l_etat.setText(tr('arc_al_deux'))
            return
        ref = self.c_reference.currentData()
        import datetime as D
        dest = os.path.join(T.dossier_archives(self.dossier()), '_alignes',
                            D.datetime.now().strftime('%Y%m%d-%H%M%S'))
        self.b_aligner.setEnabled(False)
        self.l_etat.setText(tr('arc_al_en_cours', n=len(chemins)))
        evts = self._evts
        from .alignement import aligner
        t = Tache(aligner, chemins, dest, None if ref in (None, -1) else int(ref), self.c_methode.currentData(),
                  self.s_echelle.value(), self.c_recadrer.isChecked(), self.c_format.currentData() or 'xisf',
                  None, lambda k, n, nom: evts({'genre': 'aligne_image', 'k': k, 'n': n, 'nom': nom}), parent=self)
        t.quand_fini(self._aligne)
        t.quand_erreur(lambda e: (self.b_aligner.setEnabled(True), self.l_etat.setText(tr('arc_al_erreur', erreur=e))))
        self._taches.append(t)
        t.start()

    def _aligne(self, r):
        self.b_aligner.setEnabled(True)
        self.l_etat.setText(tr('arc_aligne', n=len(r['fichiers']), forme='%d×%d' % (r['forme'][1], r['forme'][0]),
                               dest=os.path.dirname(r['apercu'])))
        self._pm_apercu = QPixmap(r['apercu'])
        self._montrer_apercu()
        e = html.escape
        lignes = ['<table><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
            e(tr('arc_al_col_image')), e(tr('arc_col_filtre')), e(tr('arc_col_lambda')), e(tr('arc_al_col_couleur')))]
        for c in sorted(r['composition'], key=lambda c: c['rang']):
            rgb = '#%02x%02x%02x' % tuple(int(x * 255) for x in c['couleur'])
            lignes.append('<tr><td>%s</td><td>%s</td><td>%s</td><td><span style="color:%s">&#9632;</span> %s</td></tr>' % (
                e(c['nom']), e(c['filtre']), '%.0f' % c['lambda_nm'] if c['lambda_nm'] else '?', rgb, rgb))
        lignes.append('</table><p>%s</p>' % e(tr('arc_al_fichiers', dest=os.path.dirname(r['apercu']))))
        self.t_compo.setHtml(''.join(lignes))

    def _montrer_apercu(self):
        pm = getattr(self, '_pm_apercu', None)
        if pm is None or pm.isNull():
            return
        t = self.l_apercu.size()
        self.l_apercu.setPixmap(pm.scaled(max(120, t.width() - 4), max(120, t.height() - 4),
                                          Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._montrer_apercu()

    # ================================================================================================ cycle de vie
    def occupe(self):
        return self._fil_dl is not None and self._fil_dl.is_alive()

    def arreter(self):
        self._arret_recherche.set()
        self._arret_estimation.set()
        self._arret_dl.set()
        self._pause_dl.clear()

    def aide_html(self):
        return tr('arc_aide_html')
