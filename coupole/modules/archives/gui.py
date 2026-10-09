"""Panneau « Archives des observatoires » : recherche, fiche et vignette, estimation, téléchargement, possession,
alignement et composition couleur.

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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu,
                             QMessageBox, QProgressBar, QSplitter, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from ...core import config
from ...core.i18n import tr
from ...gui import fichiers, memoire, ouvrir
from ...gui.adaptatif import Flux, coupable, texte_reel
from ...gui.modele import ModeleParesseux, vue_tableau
from ...gui.outils import FileEvenements, Tache, aide, bouton, case, champ, enregistrer_arret, lancer_fil, liste
from . import telechargement as T
from .services import ARCHIVES, PAR_DEFAUT

COLONNES = ('etat', 'mission', 'instrument', 'filtre', 'lambda', 'date', 'cible', 'distance', 'taille', 'archive')
CLE = 'modules.archives.'


def _taille(o) -> str:
    if not o:
        return ''
    return tr('taille_go', v='%.2f' % (o / 1e9)) if o >= 1e9 else tr('taille_mo', v='%.1f' % (o / 1e6))


def telecharger_vignette(url: str) -> str:
    """Vignette en cache disque (``cache/archives_vignettes``) ; rend le chemin, '' si indisponible."""
    if not url:
        return ''
    d = config.dossier_cache() / 'archives_vignettes'
    d.mkdir(parents=True, exist_ok=True)
    p = d / (hashlib.sha1(url.encode()).hexdigest()[:20] + '.img')
    if p.exists() and p.stat().st_size > 0:
        return str(p)
    from ...core import reseau
    try:
        with reseau.requete(url, delai=20) as r:
            b = r.read(3 * 2**20)
    except Exception:
        return ''
    if not b:
        return ''
    config.ecrire_atomique(p, b.decode('latin-1'), encodage='latin-1')
    return str(p)


class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.observations: list[dict] = []
        self.possession: dict = {}
        self.requete = None
        self._arret_recherche = threading.Event()
        self._arret_dl = enregistrer_arret(threading.Event())
        self._pause_dl = threading.Event()
        self._fil_dl = None
        self._taches = []
        self._octets_session = 0
        self._a_telecharger = 0
        v = QVBoxLayout(self)
        self.onglets = QTabWidget()
        self.onglets.addTab(self._onglet_recherche(), tr('arc_onglet_recherche'))
        self.onglets.addTab(self._onglet_alignement(), tr('arc_onglet_alignement'))
        self.onglets.setTabToolTip(0, tr('arc_onglet_recherche_aide'))
        self.onglets.setTabToolTip(1, tr('arc_onglet_alignement_aide'))
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
        f.addWidget(self.c_finaux)
        f.addWidget(self.c_publics)
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
        f = Flux()
        f.addWidget(QLabel(tr('arc_dossier')))
        self.l_dossier = aide(QLabel(coupable(T.sortie_par_defaut())), 'arc_dossier_aide')
        self.l_dossier.setWordWrap(True)
        f.addWidget(self.l_dossier)
        f.addWidget(bouton('arc_choisir_dossier', self.choisir_dossier))
        self.c_format = liste('arc_format_aide', [(tr('arc_format_xisf'), 'xisf'), (tr('arc_format_fits'), 'fits')])
        f.addWidget(self.c_format)
        self.c_garder = case('arc_garder', True)
        f.addWidget(self.c_garder)
        v.addLayout(f)
        f = Flux()
        self.b_estimer = bouton('arc_estimer', self.estimer)
        self.b_telecharger = bouton('arc_telecharger', self.telecharger)
        self.b_pause = bouton('arc_pause', self.pause)
        self.b_annuler = bouton('arc_annuler', self.annuler)
        self.b_ouvrir_dossier = bouton('arc_ouvrir_dossier', self.ouvrir_dossier)
        for b in (self.b_estimer, self.b_telecharger, self.b_pause, self.b_annuler, self.b_ouvrir_dossier):
            f.addWidget(b)
        self.b_pause.setEnabled(False)
        self.b_annuler.setEnabled(False)
        self.barre = aide(QProgressBar(), 'arc_barre_aide')
        self.barre.setRange(0, 1)
        self.barre.setValue(0)
        v.addLayout(f)
        v.addWidget(self.barre)
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
        memoire.case(self.c_garder, CLE + 'garder')
        memoire.liste(self.c_format, CLE + 'format')
        memoire.liste(self.c_methode, CLE + 'methode')
        memoire.case(self.c_recadrer, CLE + 'recadrer')
        memoire.onglets(self.onglets, CLE + 'onglet')
        memoire.separateur(self.sp, CLE + 'separateur')
        memoire.separateur(self.sp_al, CLE + 'separateur_alignement')
        memoire.entete(self.vue, CLE + 'colonnes')
        from ...core.etat_interface import etat
        d = etat().lire(CLE + 'dossier', '', str)
        if d:
            self.l_dossier.setText(coupable(d))
        memoire.memoire().suivre(CLE + 'dossier', lambda: texte_reel(self.l_dossier.text()), self.l_dossier)

    # ================================================================================================ tableau
    def _statut(self, o) -> str:
        return self.possession.get(o['id'], {}).get('statut', 'absente')

    def _ligne(self, o):
        st = self._statut(o)
        return (tr('arc_statut_' + st), o['mission'], o['instrument'], o['filtre'],
                ('%.0f' % o['lambda_nm']) if o['lambda_nm'] else '', (o['debut'] or '')[:10], o['cible'],
                ('%.2f' % (o['distance'] * 60)) if o['distance'] is not None else '',
                (('≈ ' if o.get('taille_estimee') else '') + _taille(o['taille'])) if o.get('taille') else '',
                tr('arc_nom_' + o['archive']))

    def _style(self, o):
        from ...gui import pastilles
        st = self._statut(o)
        nom = {'ok': 'ok', 'echec': 'echec'}.get(st, 'absente')
        s = {'icones': {0: pastilles.pastille(nom)}}
        if st in ('ok', 'echec'):
            s['couleurs'] = {0: pastilles.couleur_statut(nom)}
        if not o['public']:
            s['couleur'] = pastilles.couleur_statut('ecarte')
        return s

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
    def _requete_ui(self):
        from .services.base import Requete
        archives = tuple(k for k, c in self.cases_archives.items() if c.isChecked())
        texte = self.e_nom.text().strip()
        celestes = [a for a in archives if ARCHIVES[a].celeste]
        q = Requete(nom=texte, rayon=self.s_rayon.value() / 60.0, archives=archives,
                    instruments=tuple(x.strip() for x in self.e_instrument.text().split(',') if x.strip()),
                    filtres=tuple(x.strip() for x in self.e_filtre.text().split(',') if x.strip()),
                    date_min=self.e_debut.text().strip(), date_max=self.e_fin.text().strip(),
                    finaux=self.c_finaux.isChecked(), publics=self.c_publics.isChecked(),
                    cible=texte if not celestes else '')
        if any(not ARCHIVES[a].celeste for a in archives):
            q.extra['corps'] = texte
        return q

    def chercher(self):
        if not self.e_nom.text().strip():
            self.l_etat.setText(tr('arc_nom_requis'))
            return
        if not any(c.isChecked() for c in self.cases_archives.values()):
            self.l_etat.setText(tr('arc_aucune_archive'))
            return
        q = self._requete_ui()
        self._arret_recherche = threading.Event()
        self.b_chercher.setEnabled(False)
        self.b_arreter_recherche.setEnabled(True)
        self.l_etat.setText(tr('arc_recherche_en_cours'))
        evts = self._evts

        def travail():
            from .recherche import chercher, resoudre, toutes
            from .services.base import Requete
            celestes = [a for a in q.archives if ARCHIVES[a].celeste]
            planetaires = [a for a in q.archives if not ARCHIVES[a].celeste]
            resultats = []
            if celestes:
                r = resoudre(q.nom)
                q.ra, q.dec = r['ra'], r['dec']
                evts({'genre': 'resolu', 'ra': q.ra, 'dec': q.dec, 'nom': r.get('nom') or q.nom})
                resultats += chercher(q, tuple(celestes), self._arret_recherche,
                                      rapporter=lambda **e: evts(dict(e)))
            if planetaires:
                qp = Requete(**{**q.__dict__, 'cible': q.extra.get('corps') or q.nom, 'ra': None, 'dec': None})
                resultats += chercher(qp, tuple(planetaires), self._arret_recherche,
                                      rapporter=lambda **e: evts(dict(e)))
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
            self.l_etat.setText(tr('arc_introuvable', nom=self.e_nom.text().strip()))
        else:
            self.l_etat.setText(tr('arc_resolution_impossible', erreur=e))

    def _resultats(self, r):
        q, resultats, obs = r
        self.requete = q
        self.b_chercher.setEnabled(True)
        self.b_arreter_recherche.setEnabled(False)
        self.observations = obs
        self.modele.remplir_objets(obs)
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
        self.l_etat.setText(tr('arc_total', n=len(obs)) + ' — ' + ' ; '.join(morceaux))
        self.rafraichir_possession()

    # ================================================================================================ fiche
    def _selection(self):
        sel = self.choisies()
        if len(sel) != 1:
            if sel:
                tot = sum(o.get('taille') or 0 for o in sel)
                self.fiche.setHtml('<p>%s</p>' % html.escape(tr('arc_selection', n=len(sel), taille=_taille(tot) or '?')))
            return
        o = sel[0]
        self.fiche.setHtml(self.html_fiche(o))
        self.l_vignette.clear()
        if o['apercu']:
            t = Tache(telecharger_vignette, o['apercu'], parent=self)
            t.quand_fini(lambda p, ident=o['id']: self._vignette(p, ident))
            self._taches.append(t)
            t.start()
        else:
            self.l_vignette.setText(tr('arc_pas_de_vignette'))

    def _vignette(self, chemin, ident):
        sel = self.choisies()
        if len(sel) != 1 or sel[0]['id'] != ident:
            return
        pm = QPixmap(chemin) if chemin else QPixmap()
        if pm.isNull():
            self.l_vignette.setText(tr('arc_pas_de_vignette'))
            return
        self.l_vignette.setPixmap(pm.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))

    def html_fiche(self, o) -> str:
        e = html.escape
        lignes = [('arc_f_archive', tr('arc_nom_' + o['archive'])), ('arc_f_mission', o['mission']),
                  ('arc_f_instrument', o['instrument']), ('arc_f_filtre', o['filtre']),
                  ('arc_f_lambda', ('%.0f nm' % o['lambda_nm']) if o['lambda_nm'] else ''),
                  ('arc_f_debut', o['debut']), ('arc_f_publique', o['publique']), ('arc_f_cible', o['cible']),
                  ('arc_f_coord', ('%.5f° %+.5f°' % (o['ra'], o['dec'])) if o['ra'] is not None else ''),
                  ('arc_f_programme', o['programme']), ('arc_f_pi', o['pi']), ('arc_f_titre', o['titre']),
                  ('arc_f_calib', '' if o['calib'] is None else str(o['calib'])),
                  ('arc_f_fichier', o['fichier']), ('arc_f_taille', _taille(o.get('taille')))]
        h = ['<h3>%s</h3><table>' % e(o['obs_id'] or o['id'])]
        for cle, val in lignes:
            if val:
                h.append('<tr><td><b>%s</b>&nbsp;</td><td>%s</td></tr>' % (e(tr(cle)), e(str(val))))
        h.append('</table>')
        if not o['public']:
            h.append('<p><b>%s</b></p>' % e(tr('arc_f_reservee')))
        p = self.possession.get(o['id'], {})
        if p.get('statut') == 'ok':
            h.append('<p>%s</p>' % e(tr('arc_f_possede', chemin=p.get('prepare', ''))))
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

    # ================================================================================================ estimation, téléchargement
    def _a_traiter(self) -> list[dict]:
        sel = self.choisies()
        return sel if sel else []

    def estimer(self):
        obs = self._a_traiter()
        if not obs:
            self.l_etat.setText(tr('arc_rien_selectionne'))
            return
        self.b_estimer.setEnabled(False)
        self.l_etat.setText(tr('arc_estimation_en_cours', n=len(obs)))
        t = Tache(T.estimer, obs, parent=self)
        t.quand_fini(self._estime)
        t.quand_erreur(lambda e: (self.b_estimer.setEnabled(True), self.l_etat.setText(e)))
        self._taches.append(t)
        t.start()

    def _estime(self, e, suite=None):
        self.b_estimer.setEnabled(True)
        self.modele.invalider(styles=False)
        self.l_etat.setText(tr('arc_estimation', n=e['n'], taille=_taille(e['octets']) or '0', connus=e['connus'],
                               mesures=e['mesures'], estimes=e['estimes'], inconnus=e['inconnus']))
        if suite:
            suite(e)

    def telecharger(self):
        obs = [o for o in self._a_traiter() if self._statut(o) != 'ok']
        if not obs:
            self.l_etat.setText(tr('arc_rien_a_telecharger'))
            return
        if self._fil_dl is not None and self._fil_dl.is_alive():
            return
        self.b_telecharger.setEnabled(False)
        self.l_etat.setText(tr('arc_estimation_en_cours', n=len(obs)))
        t = Tache(T.estimer, obs, parent=self)
        t.quand_fini(lambda e: self._estime(e, lambda e2: self._confirmer(obs, e2)))
        t.quand_erreur(lambda e: (self.b_telecharger.setEnabled(True), self.l_etat.setText(e)))
        self._taches.append(t)
        t.start()

    def _confirmer(self, obs, e):
        if e['octets'] > T.seuil_octets():
            r = QMessageBox.question(self, tr('arc_confirmer_titre'),
                                     tr('arc_confirmer', n=e['n'], taille=_taille(e['octets']),
                                        seuil=_taille(T.seuil_octets())))
            if r != QMessageBox.StandardButton.Yes:
                self.b_telecharger.setEnabled(True)
                return
        self._lancer(obs, e['octets'])

    def _lancer(self, obs, octets):
        r = config.reglages()
        debit = float(r.get('archives_debit_mo_s', r['debit_max_mo_s']) or 8.0) * 1e6
        cible = self.requete.nom if self.requete is not None and self.requete.nom else ''
        from .recherche import lire_coordonnees
        if cible and lire_coordonnees(cible):
            cible = ''
        self._arret_dl.clear()
        self._pause_dl.clear()
        self._octets_session = 0
        self._a_telecharger = len(obs)
        self._faits = 0
        self.barre.setRange(0, max(1, len(obs)))
        self.barre.setValue(0)
        self._total_octets = octets
        evts = self._evts
        t = T.Telechargement(self.dossier(), obs, cible=cible, fmt=self.c_format.currentData() or 'xisf',
                             garder_original=self.c_garder.isChecked(), debit_octets_s=debit, paralleles=2,
                             rapporter=lambda ev: evts(dict(ev, source='dl')), arret=self._arret_dl,
                             pause=self._pause_dl)
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

    def _evenements(self, evs):
        for ev in evs:
            g = ev.get('genre')
            if g == 'resolu':
                self.l_etat.setText(tr('arc_position', ra='%.5f' % ev['ra'], dec='%+.5f' % ev['dec'],
                                       r='%.1f' % self.s_rayon.value()))
            elif g == 'aligne_image':
                self.l_etat.setText(tr('arc_alignement_image', k=ev['k'] + 1, n=ev['n'], nom=ev['nom']))
            elif g == 'archive_debut':
                self.l_etat.setText(tr('arc_interroge', archive=tr('arc_nom_' + ev['archive'])))
            elif g == 'octets':
                self._octets_session = ev['octets']
                self.l_etat.setText(tr('arc_progression', fait=self._faits, n=self._a_telecharger,
                                       taille=_taille(self._octets_session) or '0'))
            elif g in ('fini', 'deja', 'erreur'):
                self._faits = getattr(self, '_faits', 0) + 1
                self.barre.setValue(self._faits)
                if g == 'erreur':
                    self.l_etat.setText(tr('arc_echec', id=ev['id'], erreur=ev['erreur'][:200]))
            elif g == 'fin':
                b = ev['bilan']
                self.b_pause.setEnabled(False)
                self.b_annuler.setEnabled(False)
                self.b_telecharger.setEnabled(True)
                self.b_pause.setText(tr('arc_pause'))
                self.l_etat.setText(tr('arc_bilan_session', ok=b.get('ok', 0), deja=b.get('deja', 0),
                                       echec=b.get('echec', 0), taille=_taille(b.get('octets', 0)) or '0',
                                       s='%.0f' % b.get('secondes', 0)))
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
        self._arret_dl.set()
        self._pause_dl.clear()

    def aide_html(self):
        return tr('arc_aide_html')
