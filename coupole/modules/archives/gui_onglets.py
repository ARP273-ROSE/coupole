"""Onglets « Catalogue », « Hubble Ultra Deep Field » et « Instruments et filtres » du module Archives.

Rien de lent dans le fil graphique : le catalogue se charge par une `Tache` (cache daté, requête agrégée en fond).
"""
from __future__ import annotations

import html

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QTextBrowser, QVBoxLayout, QWidget)

from ...core.i18n import decimal as _dec
from ...core.i18n import langue, tr
from ...gui.adaptatif import Flux
from ...gui.modele import ModeleParesseux, vue_tableau
from ...gui.outils import Tache, aide, bouton, champ, liste
from . import catalogue as K
from . import celebres as C

CATEGORIES = ('', 'galaxie', 'amas_galaxies', 'amas_stellaire', 'nebuleuse', 'etoile', 'systeme_solaire', 'champ',
              'autre')
COLONNES_CAT = ('cible', 'categorie', 'n', 'exposition', 'position')


def _taille(o) -> str:
    if not o:
        return ''
    return tr('taille_go', v=_dec(o / 1e9, 2)) if o >= 1e9 else tr('taille_mo', v=_dec(o / 1e6, 1))


class OngletCatalogue(QWidget):
    """Toutes les cibles d'une archive, sans critère : les plus observées d'abord, filtre par type d'objet et par
    nom, pages de 100 ; double-clic → recherche de la cible.  Plus les programmes célèbres."""

    def __init__(self, panneau):
        super().__init__(panneau)
        self.panneau = panneau
        self.lignes: list[dict] = []
        self.filtrees: list[dict] = []
        self.numero = 0
        self._taches = []
        v = QVBoxLayout(self)
        intro = QLabel(tr('arc_cat_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        f = Flux()
        elements = [(tr('arc_cat_celebres'), 'celebres')] + [(tr('arc_cat_' + k), k) for k in K.CATALOGUES] + \
                   [(tr('arc_nom_' + a), 'sans:' + a) for a in K.SANS_LISTE]
        self.c_archive = liste('arc_cat_archive_aide', elements)
        self.c_archive.currentIndexChanged.connect(lambda *_: self.charger())
        f.addWidget(QLabel(tr('arc_cat_archive')))
        f.addWidget(self.c_archive)
        self.c_categorie = liste('arc_cat_categorie_aide', [(tr('arc_cat_toutes') if not c else tr('arc_catg_' + c), c)
                                                            for c in CATEGORIES])
        self.c_categorie.currentIndexChanged.connect(lambda *_: self.filtrer())
        f.addWidget(QLabel(tr('arc_cat_categorie')))
        f.addWidget(self.c_categorie)
        self.e_filtre = champ('arc_cat_filtre_aide', '', 'arc_cat_filtre_indice')
        self.e_filtre.textChanged.connect(lambda *_: self.filtrer())
        f.addWidget(self.e_filtre)
        self.b_actualiser = bouton('arc_cat_actualiser', lambda: self.charger(True))
        f.addWidget(self.b_actualiser)
        v.addLayout(f)
        self.modele = ModeleParesseux([tr('arc_catc_' + c) for c in COLONNES_CAT], self._ligne, cle=self._cle)
        self.vue, self.proxy = vue_tableau(self.modele, 'arc_cat_table_aide', selection_multiple=False)
        self.vue.message_vide = lambda: tr('arc_cat_vide')
        self.vue.doubleClicked.connect(lambda *_: self.chercher())
        v.addWidget(self.vue, 1)
        f = Flux()
        self.b_prec = bouton('arc_cat_precedente', lambda: self.aller(-1))
        self.b_suiv = bouton('arc_cat_suivante', lambda: self.aller(1))
        self.l_page = QLabel('')
        self.b_chercher = bouton('arc_cat_chercher', self.chercher)
        for w in (self.b_prec, self.l_page, self.b_suiv, self.b_chercher):
            f.addWidget(w)
        v.addLayout(f)
        self.l_info = QLabel('')
        self.l_info.setWordWrap(True)
        v.addWidget(self.l_info)
        self._charge = False

    def showEvent(self, ev):
        super().showEvent(ev)
        if not self._charge:                     # aucune requête avant que l'onglet soit ouvert
            self._charge = True
            self.charger()

    # ------------------------------------------------------------------ données
    def charger(self, rafraichir: bool = False):
        cle = self.c_archive.currentData()
        self.numero = 0
        if cle == 'celebres':
            self.lignes = [{'cible': (fr if langue() == 'fr' else en), 'categorie': 'programme', 'n': 0,
                            'exposition': None, 'ra': None, 'dec': None, 'recherche': recherche, 'rayon': rayon,
                            'programmes': tuple(x.strip() for x in prog.split(',')), 'type': '%s %s' % (mission, prog),
                            'mission': mission}
                           for _k, fr, en, mission, prog, recherche, rayon in C.PROGRAMMES]
            self.l_info.setText(tr('arc_cat_celebres_info'))
            self.filtrer()
            return
        if str(cle).startswith('sans:'):
            self.lignes = []
            self.l_info.setText(tr('arc_cat_sans_' + cle[5:]))
            self.filtrer()
            return
        self.l_info.setText(tr('arc_cat_chargement'))
        self.b_actualiser.setEnabled(False)
        t = Tache(K.charger, cle, rafraichir, parent=self)
        t.quand_fini(lambda d, cle=cle: self._charge_fini(cle, d))
        t.quand_erreur(lambda e: (self.b_actualiser.setEnabled(True), self.l_info.setText(e)))
        self._taches.append(t)
        t.start()

    def _charge_fini(self, cle, d):
        self.b_actualiser.setEnabled(True)
        if cle != self.c_archive.currentData():
            return
        self.lignes = d['lignes']
        info = tr('arc_cat_info', n=len(self.lignes), date=(d.get('date') or '')[:10] or '?',
                  source=tr('arc_cat_cache') if d.get('cache') else tr('arc_cat_en_ligne'))
        if cle == 'hst':
            info += ' ' + tr('arc_cat_hst_note')
        if d.get('erreur'):
            info += ' ' + tr('arc_cat_erreur', erreur=d['erreur'][:200])
        self.l_info.setText(info)
        self.filtrer()

    def filtrer(self):
        cat = self.c_categorie.currentData() or ''
        self.filtrees = K.filtrer(self.lignes, self.e_filtre.text(), cat if cat else '')
        if self.c_archive.currentData() == 'celebres':
            self.filtrees = K.filtrer(self.lignes, self.e_filtre.text(), '')
        self.numero = min(self.numero, K.nombre_pages(self.filtrees) - 1)
        self._page()

    def aller(self, d):
        self.numero = max(0, min(K.nombre_pages(self.filtrees) - 1, self.numero + d))
        self._page()

    def _page(self):
        self.modele.remplir_objets(K.page(self.filtrees, self.numero))
        if self.modele.donnees and not getattr(self, '_colonnes_ajustees', False):
            self._colonnes_ajustees = True
            for c in range(len(COLONNES_CAT)):
                self.vue.resizeColumnToContents(c)
        n = K.nombre_pages(self.filtrees)
        self.l_page.setText(tr('arc_cat_page', k=self.numero + 1, n=n, total=len(self.filtrees)))
        self.b_prec.setEnabled(self.numero > 0)
        self.b_suiv.setEnabled(self.numero < n - 1)

    def _ligne(self, l):
        from .produits import resume_exposition
        cat = l['categorie']
        return (l['cible'], l['type'] if cat == 'programme' else tr('arc_catg_' + cat), str(l['n']) if l['n'] else '',
                resume_exposition(l.get('exposition')),
                ('%.4f %+.4f' % (l['ra'], l['dec'])) if l.get('ra') is not None and cat != 'systeme_solaire' else l['recherche'])

    def _cle(self, col):
        nom = COLONNES_CAT[col] if 0 <= col < len(COLONNES_CAT) else ''
        if nom == 'n':
            return lambda l: l['n']
        if nom == 'exposition':
            return lambda l: l.get('exposition') or 0
        return None

    def chercher(self):
        sm = self.vue.selectionModel()
        rangs = [self.proxy.mapToSource(i).row() for i in sm.selectedRows()]
        if not rangs:
            return
        l = self.modele.donnees[rangs[0]]
        self.panneau.chercher_texte(l['recherche'], l.get('rayon') or (2.0 if l['categorie'] != 'systeme_solaire' else None),
                                    l.get('programmes') or ())


class OngletHudf(QWidget):
    """Guide du Hubble Ultra Deep Field : où le trouver, produits HLSP déjà empilés, temps de pose par filtre
    (chiffres vérifiés, sources citées), préréglage de téléchargement."""

    def __init__(self, panneau):
        super().__init__(panneau)
        self.panneau = panneau
        v = QHBoxLayout(self)
        self.texte = aide(QTextBrowser(), 'arc_hudf_texte_aide')
        self.texte.setOpenExternalLinks(True)
        self.texte.setHtml(html_hudf(langue()))
        v.addWidget(self.texte, 3)
        d = QVBoxLayout()
        d.addWidget(QLabel(tr('arc_hudf_fichiers')))
        self.liste = aide(QListWidget(), 'arc_hudf_liste_aide')
        for o in C.observations_hlsp():
            it = QListWidgetItem('%s %s — %s (%s)' % (o['programme'], o['filtre'], o['instrument'], _taille(o['taille'])))
            it.setData(Qt.ItemDataRole.UserRole, o['id'])
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if (o['programme'] == 'XDF' and o['filtre'] in C.PRESET_HUDF)
                             else Qt.CheckState.Unchecked)
            self.liste.addItem(it)
        d.addWidget(self.liste, 1)
        self.l_total = QLabel('')
        d.addWidget(self.l_total)
        self.liste.itemChanged.connect(lambda *_: self._total())
        d.addWidget(bouton('arc_hudf_preset', self.preset))
        d.addWidget(bouton('arc_hudf_telecharger', self.telecharger))
        d.addWidget(bouton('arc_hudf_chercher', lambda: self.panneau.chercher_texte('HUDF', 2.0)))
        v.addLayout(d, 2)
        self._total()

    def coches(self) -> list[dict]:
        ids = {self.liste.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.liste.count())
               if self.liste.item(i).checkState() == Qt.CheckState.Checked}
        return [o for o in C.observations_hlsp() if o['id'] in ids]

    def _total(self):
        obs = self.coches()
        self.l_total.setText(tr('arc_selection', n=len(obs), taille=_taille(sum(o['taille'] for o in obs)) or '0'))

    def preset(self):
        self.liste.blockSignals(True)
        for i in range(self.liste.count()):
            it = self.liste.item(i)
            o = next(x for x in C.observations_hlsp() if x['id'] == it.data(Qt.ItemDataRole.UserRole))
            it.setCheckState(Qt.CheckState.Checked if (o['programme'] == 'XDF' and o['filtre'] in C.PRESET_HUDF)
                             else Qt.CheckState.Unchecked)
        self.liste.blockSignals(False)
        self._total()

    def telecharger(self):
        obs = self.coches()
        if obs:
            self.panneau.onglets.setCurrentIndex(0)
            self.panneau.telecharger(obs, cible='HUDF')


class OngletInstruments(QWidget):
    def __init__(self, panneau):
        super().__init__(panneau)
        from .instruments import html_topo
        v = QVBoxLayout(self)
        self.texte = aide(QTextBrowser(), 'arc_instruments_aide')
        self.texte.setOpenExternalLinks(True)
        self.texte.setHtml(html_topo(langue()))
        v.addWidget(self.texte)


def html_hudf(langue_: str = 'fr') -> str:
    """Guide du HUDF (FR/EN) ; chiffres de ``celebres.py`` (vérifiés sur MAST et dans les readme des HLSP)."""
    e = html.escape
    fr = langue_ == 'fr'
    sep = ' ' if fr else ','

    def s(x):
        return '{:,.0f}'.format(x).replace(',', sep)
    t = ['<h3>%s</h3>' % e('Hubble Ultra Deep Field : le trouver, le télécharger' if fr else
                           'Hubble Ultra Deep Field: finding and downloading it')]
    t.append('<p>%s</p>' % e(
        "Le HUDF est un champ de 3,4′ dans le Fourneau (centre : 3 h 32 min 39 s, −27° 47′ 29″), photographié par "
        "Hubble de septembre 2003 à janvier 2004 (programmes 9978 et 10086, S. Beckwith), puis complété en infrarouge "
        "par WFC3 (programmes 11563 « HUDF09 » et 12498 « HUDF12 ») et par d'autres programmes.  Dans Coupole : "
        "tapez « HUDF » dans Rechercher (rayon 2′), ou choisissez « Programmes célèbres » dans le Catalogue." if fr else
        'The HUDF is a 3.4′ field in Fornax (centre: 3h32m39s, −27°47′29″), imaged by Hubble from September 2003 to '
        'January 2004 (programmes 9978 and 10086, S. Beckwith), then extended in the infrared by WFC3 (programmes '
        '11563 "HUDF09" and 12498 "HUDF12") and other programmes.  In Coupole: type "HUDF" in Search (2′ radius), or '
        'pick "Famous programmes" in the Catalogue.'))
    t.append('<h4>%s</h4><p>%s</p>' % (e('Poses unitaires ou image déjà empilée ?' if fr else
                                         'Single exposures or an already stacked image?'), e(
        "Les poses calibrées une à une (fichiers flt et flc, l'équivalent de vos « lights » calibrées) se comptent par "
        "centaines par filtre : les empiler soi-même est un vrai travail de professionnel (alignement, rejet, "
        "drizzle).  Les équipes ont publié des **produits de haut niveau** (HLSP) : des masters déjà empilés, "
        "alignés entre filtres, prêts à étirer.  Le plus complet est le XDF (Illingworth et al. 2013, ApJS 209, 6) : "
        "toutes les poses ACS et WFC3/IR de 2002 à 2012, environ 1,8 million de secondes." if fr else
        'Calibrated single exposures (flt and flc files, the equivalent of your calibrated lights) number in the '
        'hundreds per filter: stacking them yourself is real professional work (alignment, rejection, drizzle).  The '
        'teams published **high-level science products** (HLSP): masters already stacked, aligned between filters, '
        'ready to stretch.  The most complete is the XDF (Illingworth et al. 2013, ApJS 209, 6): every ACS and WFC3/IR '
        'exposure from 2002 to 2012, about 1.8 million seconds.').replace('**', '')))
    t.append('<h4>%s</h4>' % e('Temps de pose par filtre (HUDF d’origine, ACS/WFC)' if fr else
                                'Exposure time per filter (original HUDF, ACS/WFC)'))
    t.append('<table border="1" cellspacing="0" cellpadding="3"><tr><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        e('Filtre' if fr else 'Filter'), e('Programmes 9978 + 10086 (s)' if fr else 'Programmes 9978 + 10086 (s)'),
        e('XDF : médiane (ks) / poses' if fr else 'XDF: median (ks) / exposures')))
    for filtre, sec in C.HUDF_POSES['ACS/WFC'].items():
        x = C.XDF.get(filtre)
        t.append('<tr><td>%s</td><td>%s (%.1f h)</td><td>%s</td></tr>' % (e(filtre), s(sec), sec / 3600,
                                                                         ('%.1f / %d' % x) if x else ''))
    t.append('</table><h4>%s</h4>' % e('Infrarouge WFC3/IR' if fr else 'WFC3/IR infrared'))
    t.append('<table border="1" cellspacing="0" cellpadding="3"><tr><th>%s</th><th>11563 (s)</th><th>12498 (s)</th>'
             '<th>%s</th></tr>' % (e('Filtre' if fr else 'Filter'), e('XDF : médiane (ks) / poses' if fr else
                                                                       'XDF: median (ks) / exposures')))
    for filtre in ('F105W', 'F125W', 'F140W', 'F160W'):
        a = C.HUDF_POSES['WFC3/IR 11563'].get(filtre)
        b = C.HUDF_POSES['WFC3/IR 12498'].get(filtre)
        x = C.XDF.get(filtre)
        t.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (e(filtre), s(a) if a else '—',
                                                                         s(b) if b else '—', ('%.1f / %d' % x) if x else ''))
    t.append('</table><h4>%s</h4><p>%s</p>' % (e('Préréglage' if fr else 'Preset'), e(
        "« Couleur en trois filtres » : XDF F435W (bleu), F775W (rouge-proche infrarouge) et F160W (infrarouge), "
        "60 mas par pixel, 3 × 110 Mo.  Les trois images sont sur la même grille : elles s'empilent en couleur "
        "sans alignement (onglet Aligner ou PixInsight)." if fr else
        '"Three-filter colour": XDF F435W (blue), F775W (red–near infrared) and F160W (infrared), 60 mas per pixel, '
        '3 × 110 MB.  The three images share the same grid: they combine into colour without alignment (Align tab '
        'or PixInsight).')))
    t.append('<p><small>%s</small></p>' % e(
        "Sources : MAST, vue dbo.obspointing (somme des temps de pose par programme et filtre, 12 octobre 2026) ; "
        "readme HUDF12 (A. Koekemoer, STScI, 2012) ; https://archive.stsci.edu/prepds/xdf/ ; "
        "https://archive.stsci.edu/hlsps/xdf/ (tailles des fichiers)." if fr else
        'Sources: MAST, dbo.obspointing view (sum of exposure times per programme and filter, 12 October 2026); '
        'HUDF12 readme (A. Koekemoer, STScI, 2012); https://archive.stsci.edu/prepds/xdf/; '
        'https://archive.stsci.edu/hlsps/xdf/ (file sizes).'))
    return ''.join(t)
