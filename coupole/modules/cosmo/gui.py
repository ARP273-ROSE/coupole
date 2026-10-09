"""Panneau « Cosmologie » : redshift → distances, âges, volume, module de distance, échelle ; courbes ; export CSV."""
from __future__ import annotations

import math
import os

from PyQt6.QtCore import QEvent, QLocale, Qt, pyqtSignal
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import (QDoubleSpinBox, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QScrollArea,
                             QSlider, QSplitter, QStyle, QStyleOptionSlider, QVBoxLayout, QWidget)

from ...core.i18n import langue, tr
from ...gui import fichiers, memoire
from ...gui.adaptatif import Flux
from ...gui.modele import ModeleTableau, vue_tableau
from ...gui.outils import Tache, aide, bouton, case, champ, liste
from ...gui.trace import TraceCourbes
from . import calcul, formats

EXEMPLES = [('cosmo_ex_m87', 0.00428), ('cosmo_ex_3c273', 0.158), ('cosmo_ex_z1', 1.0), ('cosmo_ex_z234', 2.34),
            ('cosmo_ex_ulas', 7.085), ('cosmo_ex_gnz11', 10.6), ('cosmo_ex_reion', 20.0), ('cosmo_ex_cmb', 1089.8)]


def _calcul_complet(z, modele, H0, Om, Ok, shoes, avec_courbes):
    """Hors du fil graphique : contrôle des paramètres (astropy, importé ici et pas avant), grandeurs,
    et courbes si les paramètres ont changé.  Une saisie hors bornes lève ErreurCosmo, rendue à l'interface."""
    try:
        calcul.construire(modele, H0, Om, Ok)
        d = calcul.calculer(z, modele, H0, Om, Ok, incertitudes=(modele == 'planck18'), shoes=shoes)
        c = calcul.courbes(calcul.grille_z(), modele, H0, Om, Ok) if avec_courbes else None
    except calcul.ErreurCosmo as e:
        return 'erreur', e
    return d, c


# Disposition automatique, avec hystérésis (pas de bascule incessante pendant qu'on redimensionne) : côte à côte à
# partir de 1550 px de large, retour à l'empilement sous 1450 px ; au premier affichage, seuil de 1500 px.
LARGEUR_COTE_A_COTE = 1500
LARGEUR_VERS_COTE = 1550
LARGEUR_VERS_EMPILE = 1450
DISPOSITIONS = ('auto', 'cote', 'empile')
COURBES_MIN = 300               # hauteur lisible des courbes sous le tableau (pixels logiques)

# Curseur de redshift : échelle logarithmique de 0,001 à 1100, 1000 pas par décade (flèches : 10 pas, soit 2,3 % en z).
CURSEUR_LOG_MIN = -3.0
CURSEUR_Z_MAX = 1100.0
CURSEUR_PAS_DECADE = 1000
CURSEUR_MAX = int(round((math.log10(CURSEUR_Z_MAX) - CURSEUR_LOG_MIN) * CURSEUR_PAS_DECADE))      # 6041
CURSEUR_REPERES = (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)


def z_du_curseur(v: int) -> float:
    return 10 ** (CURSEUR_LOG_MIN + v / CURSEUR_PAS_DECADE)


def curseur_du_z(z: float) -> int:
    if not z or z <= 0:
        return 0
    return int(round((math.log10(z) - CURSEUR_LOG_MIN) * CURSEUR_PAS_DECADE))


class ReperesCurseur(QWidget):
    """Les repères 0,001 … 1000 sous le curseur, alignés sur ses graduations (géométrie demandée au style)."""

    def __init__(self, curseur: QSlider, parent=None):
        super().__init__(parent)
        self.curseur = curseur
        self.setFixedHeight(self.fontMetrics().height() + 2)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setPen(self.palette().placeholderText().color())
        f = p.font()
        f.setPointSizeF(max(7.0, f.pointSizeF() * 0.85))
        p.setFont(f)
        fm = p.fontMetrics()
        opt = QStyleOptionSlider()
        self.curseur.initStyleOption(opt)
        st = self.curseur.style()
        rainure = st.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self.curseur)
        poignee = st.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self.curseur)
        gauche = rainure.x() + poignee.width() // 2
        largeur = max(1, rainure.width() - poignee.width())
        for z in CURSEUR_REPERES:
            x = gauche + QStyle.sliderPositionFromValue(0, CURSEUR_MAX, curseur_du_z(z), largeur)
            texte = formats.court(z)
            w = fm.horizontalAdvance(texte)
            x = min(max(x - w / 2, 0), self.width() - w)
            p.drawText(int(x), fm.ascent() + 1, texte)
        p.end()


def _paire(cle_libelle, widget):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 10, 0)
    h.addWidget(QLabel(tr(cle_libelle)))
    h.addWidget(widget)
    return w


class Panneau(QWidget):
    disposition_changee = pyqtSignal(str)            # 'auto' | 'cote' | 'empile' (menu Affichage synchronisé)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.disposition_choisie = 'auto'
        self._tailles = {}                           # orientation → tailles du séparateur choisies à la main
        self._orientation_auto = None
        self.resultat = None
        self.courbes = None
        self._cle_courbes = None
        self._tache = None
        self._en_attente = False
        self._premier_affichage = True
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
        self.echelle = liste('cosmo_echelle_aide', [(tr('cosmo_echelle_log'), 'log'), (tr('cosmo_echelle_lin'), 'lin')])
        f.addWidget(_paire('cosmo_echelle', self.echelle))
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
        # curseur de redshift (échelle log) : glisser lit les valeurs sur la grille déjà calculée, relâcher calcule
        self.curseur = aide(QSlider(Qt.Orientation.Horizontal), 'cosmo_curseur_aide')
        self.curseur.setRange(0, CURSEUR_MAX)
        self.curseur.setSingleStep(10)
        self.curseur.setPageStep(CURSEUR_PAS_DECADE)
        self.curseur.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.curseur.setTickInterval(CURSEUR_PAS_DECADE)
        self.curseur.setTracking(True)
        self._curseur_sync = False
        self.curseur.valueChanged.connect(self._curseur_bouge)
        self.curseur.sliderReleased.connect(self._curseur_relache)
        v.addWidget(self.curseur)
        self.reperes = ReperesCurseur(self.curseur)
        v.addWidget(self.reperes)
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
        self.v_res.setWordWrap(False)
        sp.addWidget(self.v_res)
        self.trace = aide(TraceCourbes(), 'cosmo_courbes_aide')
        sp.addWidget(self.trace)
        sp.setSizes([760, 400])
        sp.setStretchFactor(0, 3)
        sp.setStretchFactor(1, 2)
        self.splitter = sp
        sp.splitterMoved.connect(self._separateur_deplace)
        v.addWidget(sp, 1)
        f = Flux()
        self.l_disposition = liste('cosmo_disposition_aide', [(tr('cosmo_disposition_' + d), d) for d in DISPOSITIONS])
        self.l_disposition.currentIndexChanged.connect(
            lambda _i: self.definir_disposition(self.l_disposition.currentData()))
        f.addWidget(_paire('cosmo_disposition', self.l_disposition))
        f.addWidget(bouton('cosmo_csv_table', self.exporter_tableau))
        f.addWidget(bouton('cosmo_csv_courbes', self.exporter_courbes))
        self.l_credits = QLabel(tr('cosmo_credits'))
        self.l_credits.setWordWrap(True)
        v.addLayout(f)
        v.addWidget(self.l_credits)

        self._memoriser()                            # avant les branchements : rien n'est calculé deux fois
        self.modele.currentIndexChanged.connect(self._modele_change)
        for w in (self.h0, self.om, self.ok):
            w.valueChanged.connect(self.calculer)
        for w in (self.h0, self.om):
            w.valueChanged.connect(self._retenir_perso)
        self.shoes.toggled.connect(self.calculer)
        self.echelle.currentIndexChanged.connect(self._tracer_courbes)
        self._modele_change(calculer=False)          # premier calcul au premier affichage (showEvent)

    # ------------------------------------------------------------ réglages gardés d'une fermeture à l'autre
    def _memoriser(self):
        """Jeu de paramètres, paramètres personnalisés (H0, Ωm gardés même quand on repasse à Planck), Ωk, z
        courant, option SH0ES, échelle des courbes."""
        from ...core.etat_interface import etat
        e, m, k = etat(), memoire.memoire(), 'modules.cosmo.'
        perso = e.lire(k + 'perso', None, list)
        self._perso = (calcul.H0_PLANCK, calcul.OM_PLANCK)
        if perso and len(perso) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                             for x in perso):
            h0, om = float(perso[0]), float(perso[1])
            if self.h0.minimum() <= h0 <= self.h0.maximum() and self.om.minimum() <= om <= self.om.maximum():
                self._perso = (h0, om)
        memoire.liste(self.modele, k + 'modele')
        if self.modele.currentData() == 'perso':
            self.h0.setValue(self._perso[0])
            self.om.setValue(self._perso[1])
        memoire.nombre(self.ok, k + 'ok')
        memoire.case(self.shoes, k + 'shoes')
        memoire.liste(self.echelle, k + 'echelle')
        z = e.lire_texte(k + 'z', '')
        if z.strip():
            try:
                calcul.verifier_z(z)                 # une valeur illisible garde le défaut (z = 1)
                self.z.setText(z.strip()[:40])
            except calcul.ErreurCosmo:
                pass
        m.suivre(k + 'perso', lambda: list(self._perso), self.h0)
        m.suivre(k + 'z', self.z.text, self.z, self.z.editingFinished)
        d = e.lire_texte(k + 'disposition', 'auto')
        self.disposition_choisie = d if d in DISPOSITIONS else 'auto'
        self.l_disposition.blockSignals(True)
        self.l_disposition.setCurrentIndex(max(0, self.l_disposition.findData(self.disposition_choisie)))
        self.l_disposition.blockSignals(False)
        tailles = e.lire(k + 'separateurs', None, dict) or {}
        for o in ('cote', 'empile'):
            t = tailles.get(o)
            if isinstance(t, list) and len(t) == 2 and all(isinstance(x, int) and not isinstance(x, bool)
                                                           and 0 < x < 100000 for x in t):
                self._tailles[o] = t
        m.suivre(k + 'disposition', lambda: self.disposition_choisie, self.l_disposition,
                 self.l_disposition.currentIndexChanged)
        m.suivre(k + 'separateurs', lambda: dict(self._tailles) or None, self.splitter, self.splitter.splitterMoved)

    def _retenir_perso(self, *_):
        if self.modele.currentData() == 'perso':
            self._perso = (self.h0.value(), self.om.value())
            memoire.memoire().signaler()

    # ------------------------------------------------------------ disposition
    def showEvent(self, ev):
        super().showEvent(ev)
        if self._premier_affichage:
            self._premier_affichage = False
            self.calculer()
        # Quand le panneau est plus haut que la zone défilante, agrandir la fenêtre ne le redimensionne pas (il
        # garde sa hauteur de consigne) : on écoute donc la zone visible elle-même, pour que les courbes suivent.
        zone = self._zone_defilante()
        if zone is not None and getattr(self, '_viewport_surveille', None) is not zone.viewport():
            self._viewport_surveille = zone.viewport()
            zone.viewport().installEventFilter(self)
        self._disposer()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._disposer()

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Type.Resize and obj is getattr(self, '_viewport_surveille', None):
            self._disposer()
        return super().eventFilter(obj, ev)

    def _zone_defilante(self):
        w = self.parentWidget()
        while w is not None and not isinstance(w, QScrollArea):
            w = w.parentWidget()
        return w

    def _hauteur_visible(self) -> int:
        """Hauteur de la zone défilante qui contient le panneau (ou du panneau lui-même)."""
        zone = self._zone_defilante()
        return zone.viewport().height() if zone is not None else self.height()

    def definir_disposition(self, mode: str):
        """Menu Affichage ou liste du module : automatique, côte à côte, empilée (gardée d'une fois à l'autre)."""
        if mode not in DISPOSITIONS:
            return
        changee = mode != self.disposition_choisie
        self.disposition_choisie = mode
        if self.l_disposition.currentData() != mode:
            self.l_disposition.blockSignals(True)
            self.l_disposition.setCurrentIndex(self.l_disposition.findData(mode))
            self.l_disposition.blockSignals(False)
        self._orientation_auto = None
        self._disposer()
        if changee:
            memoire.memoire().signaler()
            self.disposition_changee.emit(mode)

    def orientation_voulue(self):
        """Orientation du séparateur selon le choix ; en automatique, seuils avec hystérésis."""
        H, V = Qt.Orientation.Horizontal, Qt.Orientation.Vertical
        if self.disposition_choisie == 'cote':
            return H
        if self.disposition_choisie == 'empile':
            return V
        l = self.width()
        actuelle = self._orientation_auto
        if actuelle is None:
            actuelle = H if l >= LARGEUR_COTE_A_COTE else V
        elif actuelle == H and l < LARGEUR_VERS_EMPILE:
            actuelle = V
        elif actuelle == V and l >= LARGEUR_VERS_COTE:
            actuelle = H
        self._orientation_auto = actuelle
        return actuelle

    @staticmethod
    def _nom(orientation) -> str:
        return 'cote' if orientation == Qt.Orientation.Horizontal else 'empile'

    def _separateur_deplace(self, *_):
        """Position choisie à la main, gardée pour CETTE disposition (côte à côte et empilée ont chacune la leur)."""
        if self.splitter.sizes() and all(x > 0 for x in self.splitter.sizes()):
            self._tailles[self._nom(self.splitter.orientation())] = list(self.splitter.sizes())

    def largeur_tableau(self) -> int:
        """Largeur qu'il faut au tableau pour montrer toutes ses colonnes (au contenu) sans ascenseur horizontal."""
        v = self.v_res
        cols = sum(v.columnWidth(c) for c in range(self.m_res.columnCount()) if not v.isColumnHidden(c))
        return cols + 2 * v.frameWidth() + (v.verticalScrollBar().sizeHint().width()
                                             if v.verticalScrollBar().isVisible() else 0) + 4

    def hauteur_tableau(self) -> int:
        """Hauteur qu'il faut au tableau pour montrer toutes ses lignes."""
        v = self.v_res
        n = self.m_res.rowCount()
        return v.horizontalHeader().height() + sum(v.rowHeight(r) for r in range(n)) + 2 * v.frameWidth() + 4

    def _disposer(self):
        """Tableau et courbes côte à côte sur un grand écran, l'un sous l'autre sinon (ou selon le choix du menu
        Affichage / de la liste « Disposition »).

        Côte à côte : le tableau prend la largeur de ses colonnes (au contenu, jamais tronquées), les courbes tout
        le reste.  Empilé : le tableau montre toutes ses lignes si la place le permet, sinon la place est partagée
        en gardant au moins COURBES_MIN pixels aux courbes ; ses colonnes s'élargissent en proportion pour remplir
        la largeur.  Une position du séparateur choisie à la main est gardée pour chaque disposition."""
        voulu = self.orientation_voulue()
        nom = self._nom(voulu)
        nouvelle = self.splitter.orientation() != voulu
        if nouvelle:
            self.splitter.setOrientation(voulu)
        self._ajuster_colonnes(voulu)
        visible = self._hauteur_visible()
        reste = max(0, self.height() - self.splitter.height())      # tout ce qui n'est pas le tableau et les courbes
        disponible = max(200, visible - reste - 8)
        if voulu == Qt.Orientation.Vertical:
            h = self.hauteur_tableau() if self.m_res.rowCount() else 160
            if h + COURBES_MIN <= disponible:
                table = h                                           # toutes les lignes, le reste aux courbes
            else:                                                   # partage équilibré, courbes lisibles
                table = max(140, disponible - max(COURBES_MIN, disponible // 2))
            courbes_min = max(COURBES_MIN, disponible - table)
            self.v_res.setMinimumHeight(table)
            self.v_res.setMinimumWidth(0)
            self.trace.setMinimumHeight(courbes_min)
            if nouvelle or self._tailles.get(nom) is None:
                self.splitter.setSizes(self._tailles.get(nom) or [table, max(courbes_min, disponible - table)])
        else:
            courbes_min = max(200, min(disponible, 320))
            self.v_res.setMinimumHeight(0)
            self.trace.setMinimumHeight(courbes_min)
            if self.m_res.rowCount():
                largeur = self.largeur_tableau()
                if nouvelle or self._tailles.get(nom) is None:
                    total = self.splitter.width() - self.splitter.handleWidth()
                    defaut = [largeur, total - largeur] if total >= largeur + 300 else [max(200, total - 300), 300]
                    self.splitter.setSizes(self._tailles.get(nom) or defaut)
        # pour les tests et le diagnostic : ce que la disposition a vu et décidé
        self.disposition = {'visible': visible, 'reste': reste, 'disponible': disponible, 'courbes_min': courbes_min,
                            'orientation': voulu, 'choix': self.disposition_choisie}

    def _ajuster_colonnes(self, orientation=None):
        """Colonnes au contenu, jamais tronquées, aucune n'est étirée artificiellement ; empilé (le tableau a toute
        la largeur), l'espace en trop est réparti en proportion de chaque colonne."""
        v = self.v_res
        if self.m_res.rowCount() == 0:
            return
        en_tete = v.horizontalHeader()
        en_tete.setStretchLastSection(False)
        v.resizeColumnsToContents()
        if orientation == Qt.Orientation.Vertical:
            visibles = [c for c in range(self.m_res.columnCount()) if not v.isColumnHidden(c)]
            dispo = v.viewport().width() - 2
            total = sum(v.columnWidth(c) for c in visibles)
            if visibles and total < dispo:
                k = dispo / total
                for c in visibles[:-1]:
                    v.setColumnWidth(c, int(v.columnWidth(c) * k))
                v.setColumnWidth(visibles[-1], max(v.columnWidth(visibles[-1]),
                                                   dispo - sum(v.columnWidth(c) for c in visibles[:-1])))

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

    def _modele_change(self, *_, calculer=True):
        m = self.modele.currentData()
        perso = m == 'perso'
        for w in (self.h0, self.om):
            w.setEnabled(perso)
        self.ok.setEnabled(m in calcul.AVEC_COURBURE)
        self.shoes.setEnabled(m == 'planck18')
        for w in (self.h0, self.om):
            w.blockSignals(True)
        if not perso:
            self.h0.setValue(calcul.H0_PLANCK)
            self.om.setValue(calcul.OM_PLANCK)
        else:                                        # on retrouve ses propres paramètres
            self.h0.setValue(self._perso[0])
            self.om.setValue(self._perso[1])
        for w in (self.h0, self.om):
            w.blockSignals(False)
        if calculer:
            self.calculer()

    # ------------------------------------------------------------ calcul
    def definir_z(self, z):
        self.z.setText(formats.court(z))
        self.calculer()

    # ------------------------------------------------------------ curseur
    def _placer_curseur(self, z: float):
        """Met le curseur sur z sans déclencher de calcul (champ et curseur restent d'accord)."""
        self._curseur_sync = True
        try:
            self.curseur.setValue(max(0, min(CURSEUR_MAX, curseur_du_z(z))))
        finally:
            self._curseur_sync = False

    def _curseur_bouge(self, v: int):
        if self._curseur_sync:
            return
        z = z_du_curseur(v)
        self.z.setText(formats.court(z))
        self.trace.placer_marqueur(z)
        if self.curseur.isSliderDown():
            self._afficher_interpole(z)             # fluide : lecture sur la grille, pas de recalcul
        else:
            self.calculer()                         # flèches du clavier, clic sur la rainure : calcul exact

    def _curseur_relache(self):
        self.calculer()

    def _afficher_interpole(self, z: float):
        """Pendant le glissement : valeurs interpolées sur la grille des courbes (sigma et SH0ES laissés en « … »)."""
        if not self.courbes or not self.m_res.lignes:
            return
        d = calcul.interpoler(self.courbes, z)
        lignes = []
        for ligne, k in zip(self.m_res.lignes, self.m_res.donnees):
            v = d.get(k)
            lignes.append((ligne[0], formats.valeur(k, v) if v is not None else ligne[1],
                           '…' if ligne[2] else '', '…' if ligne[3] else ''))
        self.m_res.lignes = lignes
        self.m_res.dataChanged.emit(self.m_res.index(0, 0), self.m_res.index(len(lignes) - 1, 3))
        self.l_etat.setText(tr('cosmo_curseur_approx', z=formats.court(z)))

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
            z = calcul.verifier_z(self.z.text())             # sans astropy : contrôle immédiat de la saisie
        except calcul.ErreurCosmo as e:
            self._erreur_cosmo(e)
            return
        cle = (modele, round(H0, 4), round(Om, 5), round(Ok, 5))
        avec = cle != self._cle_courbes
        if avec:
            self.l_etat.setText(tr('cosmo_calcul_courbes'))
        self._tache = Tache(_calcul_complet, z, modele, H0, Om, Ok, self.shoes.isChecked(), avec, parent=self)
        self._tache.quand_fini(lambda r, k=cle: self._afficher(r, k))
        self._tache.quand_erreur(self._erreur)
        self._tache.start()

    def _erreur_cosmo(self, e):
        self.l_etat.setText(tr(e.cle, **{k: self._n(v) if isinstance(v, float) else v
                                         for k, v in e.valeurs.items()}))

    def _erreur(self, e):
        self.l_etat.setText(e)
        self._suite()

    def _suite(self):
        if self._en_attente:
            self._en_attente = False
            self.calculer()

    def _afficher(self, r, cle):
        d, c = r
        if d == 'erreur':
            self._erreur_cosmo(c)
            self._suite()
            return
        if c is not None:
            self.courbes, self._cle_courbes = c, cle
            self._tracer_courbes()
        self.trace.placer_marqueur(d['z'])
        self._placer_curseur(d['z'])
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
        self._disposer()
        self.l_etat.setText(' '.join(tr(a) for a in d['avertissements']))
        self._suite()

    def _tracer_courbes(self, *_):
        """Courbes des distances en fonction de z ; distances en échelle logarithmique (défaut) ou linéaire."""
        c = self.courbes
        if not c:
            return
        k = 1e-3 * calcul.al_par_mpc() / 1e6       # Mpc → G al
        self.trace.definir([(tr('cosmo_courbe_dc'), c['z'], c['comoving'] * k),
                            (tr('cosmo_courbe_dl'), c['z'], c['luminosity'] * k),
                            (tr('cosmo_courbe_da'), c['z'], c['angular_diameter'] * k),
                            (tr('cosmo_courbe_dlt'), c['z'], c['lookback'] * k)],
                           tr('cosmo_axe_z'), tr('cosmo_axe_d'), log_y=self.echelle.currentData() != 'lin')
        self.trace.format_x = 'z = {:.4g}'
        self.trace.format_y = '{:.4g}'

    # ------------------------------------------------------------ SIMBAD
    def chercher(self):
        nom = self.objet.text().strip()
        if not nom:
            return
        from ...core import enligne
        self.b_chercher.setEnabled(False)
        self.candidats.setVisible(False)
        self.l_etat.setText(tr('cosmo_recherche', nom=nom))
        self._t_nom = Tache(enligne.redshift, nom, parent=self)
        self._t_nom.quand_fini(self._nom_trouve)
        self._t_nom.quand_erreur(lambda e: self._nom_trouve({'etat': 'hors_ligne', 'erreur': e, 'demande': nom}))
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
        f, _ = fichiers.choisir_enregistrement(self, tr('cosmo_csv_table'),
                                               os.path.join(memoire.dossier('cosmo_exporter'),
                                                            'cosmologie_z%g.csv' % self.resultat['z']), 'CSV (*.csv)')
        if f:
            memoire.retenir('cosmo_exporter', f, est_fichier=True)
            formats.ecrire_csv_resultats(f, [self.resultat])
            self.l_etat.setText(tr('cosmo_ecrit', chemin=f))

    def exporter_courbes(self):
        if not self.courbes:
            QMessageBox.information(self, tr('cosmo_csv_courbes'), tr('cosmo_rien_a_exporter'))
            return
        f, _ = fichiers.choisir_enregistrement(self, tr('cosmo_csv_courbes'),
                                               os.path.join(memoire.dossier('cosmo_exporter'),
                                                            'cosmologie_courbes.csv'), 'CSV (*.csv)')
        if f:
            memoire.retenir('cosmo_exporter', f, est_fichier=True)
            formats.ecrire_csv_courbes(f, self.courbes)
            self.l_etat.setText(tr('cosmo_ecrit', chemin=f))

    def aide_html(self):
        return tr('cosmo_aide_html')
