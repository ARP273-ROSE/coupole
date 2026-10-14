"""Socle commun des animations : toile dessinée (QPainter), lecture / pause / vitesse / réinitialisation,
réglages (curseur + champ numérique synchronisés, cases, listes) gardés d'une session à l'autre, valeurs affichées.

Une animation hérite de `Animation`, déclare `ID` (identifiant du catalogue ClassAction) et redéfinit :
``construire()`` (réglages), ``avancer(dt)`` (dt en secondes réelles × vitesse), ``dessiner(p, rect)``,
``valeurs()`` (liste de (libellé, valeur) affichée sous la toile) et, si besoin, ``presser`` / ``glisser`` /
``relacher`` (souris).  Rien de lourd n'est calculé : une image coûte quelques millisecondes (anti-gel)."""
from __future__ import annotations

import math
import time

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPalette
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                             QSlider, QVBoxLayout, QWidget)

from ...core.i18n import langue, tr
from ...gui import memoire
from ...gui.adaptatif import Flux
from ...gui.outils import aide
from . import dessin, formule

PERIODE_MS = 33                 # ≈ 30 images par seconde
VITESSE_MIN, VITESSE_MAX = 0.1, 10.0


def nombre(x: float, dec: int = 1) -> str:
    """Nombre dans la langue courante (virgule décimale en français, espace fine pour les milliers)."""
    if x is None or not math.isfinite(x):
        return '—'
    s = '{:,.{d}f}'.format(x, d=dec).replace(',', ' ')
    if s.startswith('-') and float(s.replace(' ', '').replace(',', '.') or 0) == 0:
        s = s[1:]
    return s.replace('.', ',') if langue() == 'fr' else s


def angle(x: float, dec: int = 1) -> str:
    return nombre(x, dec) + '°'


def heures_minutes(h: float, secondes: bool = False) -> str:
    """Heures décimales → « 13 h 05 » (fr) / « 13:05 » (en), modulo 24."""
    h = h % 24.0
    tot = int(round(h * (3600 if secondes else 60)))
    if secondes:
        hh, reste = divmod(tot, 3600)
        mm, ss = divmod(reste, 60)
        hh %= 24
        return ('%d h %02d min %02d s' if langue() == 'fr' else '%d:%02d:%02d') % (hh, mm, ss)
    hh, mm = divmod(tot, 60)
    hh %= 24
    return ('%d h %02d' if langue() == 'fr' else '%d:%02d') % (hh, mm)


def duree_hm(h: float) -> str:
    """Durée en heures → « 15 h 57 min » / « 15 h 57 min »."""
    tot = int(round(h * 60))
    hh, mm = divmod(tot, 60)
    return tr('anim_duree_hm', h=hh, m='%02d' % mm)


MOIS_JOURS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def date_du_jour(jour: float) -> str:
    """Jour de l'année (0 = 1er janvier, année de 365 jours) → « 21 mars » / « March 21 »."""
    j = int(math.floor(jour % 365.0))
    m = 0
    while j >= MOIS_JOURS[m]:
        j -= MOIS_JOURS[m]
        m += 1
    nom = tr('anim_mois_%d' % (m + 1))
    return ('%d %s' % (j + 1, nom)) if langue() == 'fr' else ('%s %d' % (nom, j + 1))


def jour_de_date(mois: int, jour: int) -> int:
    return sum(MOIS_JOURS[:mois - 1]) + jour - 1


class Reglage(QWidget):
    """Libellé + curseur + champ numérique synchronisés (échelle linéaire ou logarithmique).

    La valeur exacte est gardée à part : le champ n'en montre qu'un arrondi, et une animation peut avancer par
    petits pas sans que l'arrondi du champ ne les perde."""

    valueChanged = pyqtSignal(float)
    PAS = 1000

    def __init__(self, texte: str, mini: float, maxi: float, valeur: float, dec: int = 1, unite: str = '',
                 log: bool = False, cle_aide: str = '', parent=None):
        super().__init__(parent)
        self.mini, self.maxi, self.log = mini, maxi, log
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 8, 0)
        self.libelle = QLabel(texte)
        if any(g == 'formule' for g, _ in formule.morceaux(texte)):
            px, col, _ = formule.contexte_widget(self.libelle)
            self.libelle.setTextFormat(Qt.TextFormat.RichText)
            self.libelle.setText(formule.enrichir(texte, px, col))
        h.addWidget(self.libelle)
        self.curseur = QSlider(Qt.Orientation.Horizontal)
        self.curseur.setRange(0, self.PAS)
        self.curseur.setMinimumWidth(110)
        self.curseur.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        h.addWidget(self.curseur, 1)
        self.champ = QDoubleSpinBox()
        self.champ.setDecimals(dec)
        self.champ.setRange(mini, maxi)
        self.champ.setSingleStep(10 ** (-dec) if dec > 0 else 1)
        self.champ.setKeyboardTracking(False)
        if unite:
            self.champ.setSuffix(' ' + unite)
        h.addWidget(self.champ)
        if cle_aide:
            for w in (self.libelle, self.curseur, self.champ):
                aide(w, cle_aide)
        self._v = float(valeur)
        self._sync = True
        self.champ.setValue(valeur)
        self.curseur.setValue(self._pos(valeur))
        self._sync = False
        self.curseur.valueChanged.connect(self._curseur_bouge)
        self.champ.valueChanged.connect(self._champ_change)

    def sizeHint(self):
        s = super().sizeHint()
        return QSize(max(s.width(), 300), s.height())

    def _pos(self, v: float) -> int:
        if self.log:
            v = max(v, self.mini)
            t = (math.log10(v) - math.log10(self.mini)) / (math.log10(self.maxi) - math.log10(self.mini))
        else:
            t = (v - self.mini) / (self.maxi - self.mini) if self.maxi > self.mini else 0
        return int(round(max(0.0, min(1.0, t)) * self.PAS))

    def _val(self, pos: int) -> float:
        t = pos / self.PAS
        if self.log:
            return 10 ** (math.log10(self.mini) + t * (math.log10(self.maxi) - math.log10(self.mini)))
        return self.mini + t * (self.maxi - self.mini)

    def _vers_curseur(self, v):
        self._sync = True
        self.curseur.setValue(self._pos(v))
        self._sync = False

    def _curseur_bouge(self, pos):
        if self._sync:
            return
        self._appliquer(self._val(pos), curseur=False)

    def _champ_change(self, v):
        if self._sync:
            return
        self._appliquer(v, champ=False)

    def _appliquer(self, v: float, champ: bool = True, curseur: bool = True):
        v = max(self.mini, min(self.maxi, float(v)))
        change = v != self._v
        self._v = v
        self._sync = True
        if champ:
            self.champ.setValue(v)
        if curseur:
            self.curseur.setValue(self._pos(v))
        self._sync = False
        if change:
            self.valueChanged.emit(v)

    def value(self) -> float:
        return self._v

    def setValue(self, v: float):
        self._appliquer(v)

    def relire_champ(self):
        """Après le rétablissement du champ par la mémoire de l'interface : la valeur exacte suit le champ."""
        self._v = float(self.champ.value())
        self._vers_curseur(self._v)

    def borner(self, mini: float, maxi: float):
        """Change les bornes (le simulateur du module de distance les fait suivre le verrou choisi)."""
        self.mini, self.maxi = mini, maxi
        self._sync = True
        self.champ.setRange(mini, maxi)
        self._sync = False
        self._appliquer(self._v)
        self._vers_curseur(self._v)


class Toile(QWidget):
    """Surface de dessin d'une animation ; la souris est transmise à l'animation."""

    def __init__(self, anim):
        super().__init__(anim)
        self.anim = anim
        self.setMinimumSize(300, 250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(False)
        self._dernier = None
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    def sizeHint(self):
        return QSize(720, 470)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        r = QRectF(self.rect())
        p.fillRect(r, dessin.c('fond'))
        self.anim._vues = []
        dessin.debut_image(p, r)
        try:
            self.anim.dessiner(p, r)
        finally:
            p.end()

    def mousePressEvent(self, ev):
        pos = ev.position()
        self._dernier = pos
        self.anim.presser(pos, ev.button())

    def mouseMoveEvent(self, ev):
        if self._dernier is None:
            return
        pos = ev.position()
        dx, dy = pos.x() - self._dernier.x(), pos.y() - self._dernier.y()
        self._dernier = pos
        self.anim.glisser(pos, dx, dy)

    def mouseReleaseEvent(self, ev):
        self._dernier = None
        self.anim.relacher(ev.position())

    def wheelEvent(self, ev):
        if self.anim.molette(ev.position(), ev.angleDelta().y()):
            ev.accept()
        else:
            super().wheelEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        if not self.anim.double_clic(ev.position()):
            super().mouseDoubleClickEvent(ev)


class Animation(QWidget):
    ID = ''
    ANIMEE = True               # boutons lecture / pause / vitesse
    LECTURE_AU_DEPART = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self._defauts = {}                       # cle → (widget, valeur par défaut)
        self._vues = []                          # (rect, Vue3D) des sphères qu'on fait tourner à la souris
        self._glisse = None                      # vue en cours de rotation, ou rappel de déplacement d'objet
        self.en_lecture = False
        self._t_dernier = None
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        self.nb_vues = 0                         # sphères qu'on fait tourner au glisser (pour l'aide)
        self.toile = Toile(self)
        v.addWidget(self.toile, 1)
        # aide propre à l'animation, discrète, sous la scène (jamais d'info-bulle par-dessus le dessin)
        self.l_aide = QLabel('')
        self.l_aide.setWordWrap(True)
        self.l_aide.setObjectName('anim_aide_scene')
        f = self.l_aide.font()
        f.setPointSizeF(f.pointSizeF() * 0.9)
        self.l_aide.setFont(f)
        self.l_aide.setForegroundRole(QPalette.ColorRole.PlaceholderText)
        v.addWidget(self.l_aide)
        self.barre = Flux()
        v.addLayout(self.barre)
        self.flux = Flux()
        v.addLayout(self.flux)
        self.l_valeurs = QLabel('')
        self.l_valeurs.setWordWrap(True)
        self.l_valeurs.setTextFormat(Qt.TextFormat.RichText)
        self.l_valeurs.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(self.l_valeurs)
        self.minuteur = QTimer(self)
        self.minuteur.setInterval(PERIODE_MS)
        self.minuteur.timeout.connect(self._battement)
        if self.ANIMEE:
            self.b_lecture = QPushButton(tr('anim_lecture'))
            aide(self.b_lecture, 'anim_lecture_aide')
            self.b_lecture.clicked.connect(self.basculer_lecture)
            self.barre.addWidget(self.b_lecture)
            self.vitesse = self.curseur('vitesse', VITESSE_MIN, VITESSE_MAX, 1.0, dec=2, log=True,
                                        cle_texte='anim_vitesse', cle_aide='anim_vitesse_aide', unite='×',
                                        flux=self.barre, rafraichir=False)
        b = QPushButton(tr('anim_reinitialiser'))
        aide(b, 'anim_reinitialiser_aide')
        b.clicked.connect(self.reinitialiser)
        self.barre.addWidget(b)
        self.construire()
        self.l_aide.setText(self.aide_interaction())
        self.rafraichir()
        if self.ANIMEE and self.LECTURE_AU_DEPART:
            self.basculer_lecture()

    # ------------------------------------------------------------ à redéfinir
    def construire(self):
        pass

    def avancer(self, dt: float):
        pass

    def dessiner(self, p, rect: QRectF):
        pass

    def valeurs(self) -> list:
        return []

    def presser(self, pos: QPointF, bouton) -> bool:
        for r, vue in self._vues:
            if r.contains(pos):
                self._glisse = vue
                return True
        return False

    def glisser(self, pos: QPointF, dx: float, dy: float):
        if callable(self._glisse):
            self._glisse(pos)
            self.rafraichir()
        elif self._glisse is not None:
            self._glisse.tourner(dx, dy)
            self.toile.update()

    def relacher(self, pos: QPointF):
        self._glisse = None

    def molette(self, pos: QPointF, delta: float) -> bool:
        """Molette sur la toile (delta en huitièmes de degré) ; rend True si l'animation s'en sert."""
        return False

    def double_clic(self, pos: QPointF) -> bool:
        return False

    # ------------------------------------------------------------ réglages
    def _cle(self, cle: str) -> str:
        return 'modules.anim.%s.%s' % (self.ID, cle)

    def _texte(self, cle: str, cle_texte: str | None) -> str:
        return cle_texte or 'anim_%s_%s' % (self.ID.lower(), cle)

    def curseur(self, cle: str, mini: float, maxi: float, defaut: float, dec: int = 1, unite: str = '',
                log: bool = False, cle_texte: str | None = None, cle_aide: str | None = None, flux=None,
                rafraichir: bool = True) -> Reglage:
        ct = self._texte(cle, cle_texte)
        r = Reglage(tr(ct), mini, maxi, defaut, dec, unite, log, cle_aide or ct + '_aide')
        memoire.nombre(r.champ, self._cle(cle))
        r.relire_champ()
        self._defauts[cle] = (r, defaut)
        if rafraichir:
            r.valueChanged.connect(lambda *_: self.reglage_change())
        (flux or self.flux).addWidget(r)
        return r

    def coche(self, cle: str, defaut: bool = False, cle_texte: str | None = None, flux=None) -> QCheckBox:
        ct = self._texte(cle, cle_texte)
        w = QCheckBox(tr(ct))
        w.setChecked(defaut)
        aide(w, ct + '_aide')
        memoire.case(w, self._cle(cle))
        self._defauts[cle] = (w, defaut)
        w.toggled.connect(lambda *_: self.reglage_change())
        (flux or self.flux).addWidget(w)
        return w

    def choix(self, cle: str, options: list, defaut, cle_texte: str | None = None, flux=None) -> QComboBox:
        """options : [(clé du texte, donnée)]."""
        ct = self._texte(cle, cle_texte)
        w = QComboBox()
        for cle_opt, donnee in options:
            w.addItem(tr(cle_opt), donnee)
        w.setCurrentIndex(max(0, w.findData(defaut)))
        aide(w, ct + '_aide')
        memoire.liste(w, self._cle(cle))
        self._defauts[cle] = (w, defaut)
        w.currentIndexChanged.connect(lambda *_: self.reglage_change())
        boite = QWidget()
        h = QHBoxLayout(boite)
        h.setContentsMargins(0, 0, 8, 0)
        lab = QLabel(tr(ct))
        aide(lab, ct + '_aide')
        h.addWidget(lab)
        h.addWidget(w)
        (flux or self.flux).addWidget(boite)
        w._boite = boite                         # pour masquer la liste avec son libellé
        return w

    def bouton(self, cle_texte: str, rappel, flux=None) -> QPushButton:
        b = QPushButton(tr(cle_texte))
        aide(b, cle_texte + '_aide')
        b.clicked.connect(rappel)
        (flux or self.flux).addWidget(b)
        return b

    def vue(self, az: float, alt: float, alt_min: float = -89.0, alt_max: float = 89.0) -> dessin.Vue3D:
        self.nb_vues += 1
        return dessin.Vue3D(az, alt, alt_min, alt_max)

    def aide_interaction(self) -> str:
        """Ce que fait la souris dans cette animation précise (texte « souris » propre à l'animation s'il existe,
        sinon selon qu'elle a une sphère à tourner et/ou des objets à déplacer)."""
        from ...core import i18n
        cles = i18n.toutes_les_cles()
        ident = self.ID.lower()
        propre = next((k for k in ('anim_%s_souris' % ident, 'anim_%s_aide_souris' % ident) if k in cles), None)
        deplace = type(self).presser is not Animation.presser
        if propre:
            return tr(propre)
        if self.nb_vues:
            return tr('anim_aide_tourner_deplacer' if deplace else 'anim_aide_tourner')
        if deplace:
            return tr('anim_aide_deplacer')
        return ''

    def zone_rotative(self, rect: QRectF, vue: dessin.Vue3D):
        """À appeler dans dessiner() : la souris fait tourner `vue` dans `rect`."""
        self._vues.append((QRectF(rect), vue))

    def etat_reglages(self, modifies: bool = True) -> dict:
        """Réglages courants (clé → valeur), seulement ceux qui diffèrent du défaut si `modifies`."""
        out = {}
        for cle, (w, defaut) in self._defauts.items():
            if isinstance(w, Reglage):
                v = round(w.champ.value(), w.champ.decimals())
                d = round(float(defaut), w.champ.decimals())
            elif isinstance(w, QCheckBox):
                v, d = w.isChecked(), defaut
            elif isinstance(w, QComboBox):
                v, d = w.currentData(), defaut
            else:
                continue
            if not modifies or v != d:
                out[cle] = v
        return out

    def adresse_web(self) -> str:
        """Fragment de l'adresse partageable de Coupole Web pour cette animation (« #/a/<id>?clé=valeur&… »)."""
        from urllib.parse import quote, urlencode
        parametres = []
        for cle, v in self.etat_reglages().items():
            if isinstance(v, bool):
                s = 'true' if v else 'false'
            elif isinstance(v, float):
                s = repr(int(v)) if v == int(v) else repr(v)
            else:
                s = str(v)
            if len(s) <= 80:
                parametres.append((cle, s))
        q = urlencode(parametres)
        return '#/a/%s%s' % (quote(self.ID, safe=''), '?' + q if q else '')

    def reglage_change(self):
        self.rafraichir()

    def reinitialiser(self):
        for cle, (w, defaut) in self._defauts.items():
            if isinstance(w, Reglage):
                w.setValue(defaut)
            elif isinstance(w, QCheckBox):
                w.setChecked(defaut)
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(max(0, w.findData(defaut)))
        for v in self.__dict__.values():
            if isinstance(v, dessin.Vue3D):
                v.reinitialiser()
        self.etat_initial()
        if self.en_lecture:
            self.basculer_lecture()
        self.rafraichir()

    def etat_initial(self):
        """Remet l'état interne (temps, positions) à son origine ; appelé par Réinitialiser."""

    # ------------------------------------------------------------ lecture
    def basculer_lecture(self):
        self.en_lecture = not self.en_lecture
        if self.ANIMEE:
            self.b_lecture.setText(tr('anim_pause' if self.en_lecture else 'anim_lecture'))
        self._t_dernier = time.monotonic()
        if self.en_lecture and self.isVisible():
            self.minuteur.start()
        else:
            self.minuteur.stop()

    def arreter(self):
        if self.en_lecture:
            self.basculer_lecture()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.rafraichir()

    def showEvent(self, ev):
        super().showEvent(ev)
        if self.en_lecture:
            self._t_dernier = time.monotonic()
            self.minuteur.start()

    def hideEvent(self, ev):
        super().hideEvent(ev)
        self.minuteur.stop()

    def _battement(self):
        t = time.monotonic()
        dt = min(0.2, t - (self._t_dernier or t))
        self._t_dernier = t
        v = self.vitesse.value() if self.ANIMEE else 1.0
        self.avancer(dt * v)
        self.rafraichir()

    def pas(self, dt: float = 0.1):
        """Fait avancer d'un pas (tests, boutons pas à pas)."""
        self.avancer(dt)
        self.rafraichir()

    # ------------------------------------------------------------ affichage
    def rafraichir(self):
        self.toile.update()
        lignes = self.valeurs()
        texte = ''
        if lignes:
            par_ligne = 2 if len(lignes) > 4 and self.width() >= 700 else 1
            px, col, _ = formule.contexte_widget(self.l_valeurs)
            rangs = []
            for i in range(0, len(lignes), par_ligne):
                rangs.append(''.join('<td style="padding-right:8px">%s</td><td style="padding-right:24px"><b>%s</b></td>'
                                     % (formule.enrichir(a, px, col), formule.enrichir(b, px, col, valeur=True))
                                     for a, b in lignes[i:i + par_ligne]))
            texte = '<table>%s</table>' % ''.join('<tr>%s</tr>' % r for r in rangs)
        if texte != self.l_valeurs.text():
            self.l_valeurs.setText(texte)

    def image(self, largeur: int = 720, hauteur: int = 470):
        """Rendu hors écran (tests, captures du manuel)."""
        from PyQt6.QtGui import QImage
        img = QImage(largeur, hauteur, QImage.Format.Format_ARGB32_Premultiplied)  # comme l’écran
        img.fill(dessin.c('fond'))
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._vues = []
        r = QRectF(0, 0, largeur, hauteur)
        dessin.debut_image(p, r)
        try:
            self.dessiner(p, r)
        finally:
            p.end()
        return img
