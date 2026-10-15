"""Ressources des modules au bureau : fiches (widgets Qt + moteur de formules), tables (QTableWidget), images (crédit et
licence affichés), fenêtres de ressources (une par ressource, plusieurs à la fois, redimensionnables), aperçu au survol.
Même contenu et même ordre que Coupole Web (src/app/contenu.ts)."""
from __future__ import annotations

import html as _html
import re

from PyQt6 import sip
from PyQt6.QtCore import QPoint, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QHBoxLayout, QHeaderView, QLabel, QScrollArea, QSizePolicy,
                             QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)

from ....core.i18n import langue, tr
from .. import dessin, formule
from . import contenu
from .schema_qt import SchemaWidget

bi = contenu.bi


def theme_courant() -> str:
    app = QApplication.instance()
    if app is not None:
        return 'clair' if app.palette().window().color().lightness() > 128 else 'sombre'
    return 'clair' if dessin.theme() == 'clair' else 'sombre'


def texte_html(s: str, w: QWidget | None = None, valeur_couleur: str | None = None) -> str:
    """HTML d'un texte des contenus : `$formule$` (moteur de formules), `**valeur**`, retours à la ligne."""
    if w is not None:
        px, col, dpr = formule.contexte_widget(w)
    else:
        app = QApplication.instance()
        col = app.palette().windowText().color().name() if app is not None else '#D9DDE2'
        px = app.font().pointSizeF() * 96 / 72 if app is not None else 14.0
        dpr = 2.0
    out = []
    for i, ligne in enumerate((s or '').split('\n')):
        if i:
            out.append('<br>')
        for m in re.split(r'(\*\*.+?\*\*)', ligne):
            if not m:
                continue
            gras = m.startswith('**') and m.endswith('**') and len(m) > 4
            m2 = m[2:-2] if gras else m
            parts = []
            for j, x in enumerate(re.split(r'\$([^$]+)\$', m2)):
                if x:
                    parts.append(formule.html(x, px * 1.05, valeur_couleur or col, dpr) if j % 2 else formule.enrichir(x, px, col))
            t = ''.join(parts)
            out.append('<b style="color:%s">%s</b>' % (valeur_couleur or '#5be35b', t) if gras else t)
    return ''.join(out)


def etiquette(texte_riche: str, parent=None, classe: str = '') -> QLabel:
    lab = QLabel(parent)
    lab.setWordWrap(True)
    lab.setTextFormat(Qt.TextFormat.RichText)
    lab.setOpenExternalLinks(True)
    lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    lab.setText(texte_riche)
    if classe:
        lab.setObjectName(classe)
    return lab


def _formule_bloc(src: str, legende: str | None, parent) -> QWidget:
    w = QFrame(parent)
    w.setObjectName('formuleBloc')
    w.setFrameShape(QFrame.Shape.StyledPanel)
    v = QVBoxLayout(w)
    lab = QLabel(w)
    px, col, dpr = formule.contexte_widget(lab)
    lab.setTextFormat(Qt.TextFormat.RichText)
    lab.setText(formule.html(src, px * 1.35, col, dpr))
    lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lab.setAccessibleName(src)
    v.addWidget(lab)
    if legende:
        v.addWidget(etiquette(texte_html(legende, lab), w))
    return w


class ImageWidget(QWidget):
    """Photo mise à l'échelle (proportions gardées)."""

    def __init__(self, chemin, alt: str = '', parent=None):
        super().__init__(parent)
        self.pix = QPixmap(str(chemin))
        self.setAccessibleName(alt)
        pol = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        pol.setHeightForWidth(True)
        self.setSizePolicy(pol)
        self.setMinimumSize(120, 80)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return int(w * self.pix.height() / max(1, self.pix.width())) if not self.pix.isNull() else 80

    def sizeHint(self):
        return QSize(520, self.heightForWidth(520))

    def paintEvent(self, _):
        if self.pix.isNull():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        r = QRectF(self.rect())
        s = min(r.width() / self.pix.width(), r.height() / self.pix.height())
        w, h = self.pix.width() * s, self.pix.height() * s
        p.drawPixmap(QRectF(r.center().x() - w / 2, r.center().y() - h / 2, w, h), self.pix, QRectF(self.pix.rect()))
        p.end()


def credit_html(i: dict) -> str:
    lic = ('<a href="%s">%s</a>' % (_html.escape(i['licence_url']), _html.escape(str(i.get('licence', ''))))
           if i.get('licence_url') else _html.escape(str(i.get('licence', ''))))
    src = ' · <a href="%s">%s</a>' % (_html.escape(i['source_url']), _html.escape(tr('classe_source'))) if i.get('source_url') else ''
    return '<small>%s %s — %s%s</small>' % (_html.escape(tr('classe_credit')), _html.escape(bi(i.get('credit'))), lic, src)


def bloc_image(i: dict, parent=None, compacte=False) -> QWidget:
    w = QWidget(parent)
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 4, 0, 4)
    if i['nature'] == 'schema':
        for s in i.get('schemas', []):
            sch = contenu.schema(s)
            if sch:
                v.addWidget(SchemaWidget(sch, theme_courant(), w))
        if not compacte and i.get('legende'):
            v.addWidget(etiquette(texte_html(bi(i['legende'])), w))
    elif i['nature'] == 'table':
        t = contenu.table(i['table'])
        if t:
            v.addWidget(bloc_table(t, w))
    else:
        v.addWidget(ImageWidget(contenu.chemin_image(i['id']), bi(i.get('titre')), w))
        if not compacte and i.get('legende'):
            v.addWidget(etiquette(texte_html(bi(i['legende'])), w))
        v.addWidget(etiquette(credit_html(i), w))
    return w


def bloc_table(t: dict, parent=None, lignes_max=None) -> QWidget:
    w = QWidget(parent)
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    cols = t['colonnes']
    lignes = t['lignes'][:lignes_max] if lignes_max else t['lignes']
    tab = QTableWidget(len(lignes), len(cols), w)
    tab.setAccessibleName(bi(t['titre']))
    tab.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tab.setHorizontalHeaderLabels([re.sub(r'\$([^$]+)\$', r'\1', bi(c['titre'])) for c in cols])
    tab.verticalHeader().setVisible(False)
    for i, l in enumerate(lignes):
        info = ' — '.join(x for x in (bi(l.get('note')) if l.get('note') else '',
                                      tr('classe_sources') + ' : ' + ', '.join(l['source']) if l.get('source') else '') if x)
        for j, c in enumerate(cols):
            v_ = l['cellules'].get(c['cle'])
            it = QTableWidgetItem('—' if v_ is None else re.sub(r'\$([^$]+)\$', r'\1', bi(v_)))
            if c.get('align') == 'd':
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if info:
                it.setToolTip(info)
            tab.setItem(i, j, it)
    tab.resizeColumnsToContents()
    tab.setAlternatingRowColors(True)
    tab.setShowGrid(False)
    hh = tab.horizontalHeader()
    hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    hh.setStretchLastSection(False)
    if len(cols) > 1:
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)   # la place libre va aux noms, pas à la dernière colonne
    else:
        hh.setStretchLastSection(True)
    h = tab.horizontalHeader().height() + sum(tab.rowHeight(i) for i in range(len(lignes))) + 6
    tab.setMinimumHeight(min(h, 420))
    tab.setMaximumHeight(max(h, 120) if len(lignes) <= 30 else 16777215)   # pas de grand vide sous une courte table
    v.addWidget(tab)
    if lignes_max is None:
        for f in t.get('formules', []):
            v.addWidget(_formule_bloc(bi(f['source']), bi(f.get('legende')) if f.get('legende') else None, w))
        for n in t.get('notes', []):
            v.addWidget(etiquette(texte_html(bi(n)), w))
        if (t.get('origine') or {}).get('correction'):
            v.addWidget(Repliable(tr('classe_ce_qui_a_change'), texte_html(bi(t['origine']['correction'])), w))
    return w


class Repliable(QWidget):
    """Volet repliable (« Ce qui a changé », « Sources ») : bouton accessible au clavier."""

    def __init__(self, titre: str, texte: str, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 2, 0, 2)
        self.b = QToolButton(self)
        self.b.setText(titre)
        self.b.setCheckable(True)
        self.b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.b.setArrowType(Qt.ArrowType.RightArrow)
        self.lab = etiquette(texte, self)
        self.lab.setVisible(False)
        self.b.toggled.connect(self._basculer)
        v.addWidget(self.b)
        v.addWidget(self.lab)

    def _basculer(self, ouvert):
        self.b.setArrowType(Qt.ArrowType.DownArrow if ouvert else Qt.ArrowType.RightArrow)
        self.lab.setVisible(ouvert)


def bloc_fiche(f: dict, parent=None) -> QWidget:
    w = QWidget(parent)
    v = QVBoxLayout(w)
    res = etiquette('<i>%s</i>' % texte_html(bi(f['resume'])), w)
    v.addWidget(res)
    for b in f['blocs']:
        t = b['type']
        if t == 'definition':
            v.addWidget(etiquette(texte_html(bi(b['texte'])), w))
        elif t in ('formule', 'reaction'):
            v.addWidget(_formule_bloc(bi(b['source']), bi(b.get('legende')) if b.get('legende') else None, w))
        elif t == 'schema':
            s = contenu.schema(b['ref'])
            if s:
                v.addWidget(SchemaWidget(s, theme_courant(), w))
                cap = QLabel('<small>%s</small>' % _html.escape(bi(s['titre'])), w)
                cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
                v.addWidget(cap)
        elif t == 'image':
            i = contenu.image(b['ref'])
            if i:
                v.addWidget(bloc_image(i, w))
        elif t == 'ordres_de_grandeur':
            v.addWidget(etiquette('<b>%s</b><ul>%s</ul>' % (_html.escape(tr('classe_ordres_grandeur')), ''.join(
                '<li>%s</li>' % texte_html(bi(x['texte'])) for x in b['items'])), w))
        elif t in ('piege', 'plus'):
            cadre = QFrame(w)
            cadre.setObjectName('piege' if t == 'piege' else 'plus')
            cadre.setFrameShape(QFrame.Shape.StyledPanel)
            h = QVBoxLayout(cadre)
            h.addWidget(etiquette('<b>%s</b> %s' % (_html.escape(tr('classe_piege' if t == 'piege' else 'classe_plus_loin')),
                                                   texte_html(bi(b['texte']))), cadre))
            v.addWidget(cadre)
    if (f.get('origine') or {}).get('correction'):
        v.addWidget(Repliable(tr('classe_ce_qui_a_change'), texte_html(bi(f['origine']['correction'])), w))
    if f.get('sources'):
        src = contenu.sources()
        items = []
        for k in f['sources']:
            s = src.get(k)
            if not s:
                items.append('<li>%s</li>' % _html.escape(k))
                continue
            lien = ' — <a href="%s">%s</a>' % (_html.escape(s['url']), _html.escape(re.sub(r'^https?://([^/]+).*', r'\1', s['url']))) if s.get('url') else ''
            items.append('<li>%s<i>%s</i>%s%s</li>' % (_html.escape(s['auteurs'] + ', ') if s.get('auteurs') else '',
                                                        _html.escape(s.get('titre', k)), _html.escape(', ' + s['ref']) if s.get('ref') else '', lien))
        v.addWidget(Repliable(tr('classe_sources'), '<ul>%s</ul>' % ''.join(items), w))
    v.addStretch(1)
    return w


def contenu_ressource(genre: str, i: str, parent=None) -> tuple[str, QWidget]:
    if genre == 'image':
        im = contenu.image(i)
        return bi(im['titre']), bloc_image(im, parent)
    o = contenu.fiche(i) if genre == 'fiche' else contenu.table(i)
    return bi(o['titre']), (bloc_fiche(o, parent) if genre == 'fiche' else bloc_table(o, parent))


# ------------------------------------------------------------------ fenêtres de ressources
class FenetreRessource(QWidget):
    def __init__(self, genre: str, i: str):
        super().__init__(None, Qt.WindowType.Window)
        self.cle = genre + ':' + i
        titre, w = contenu_ressource(genre, i)
        self.setWindowTitle('%s — %s' % (titre, tr('classe_genre_' + genre)))
        self.setAccessibleName(titre)
        zone = QScrollArea(self)
        zone.setWidgetResizable(True)
        zone.setFrameShape(QFrame.Shape.NoFrame)
        zone.setWidget(w)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 10, 14, 10)
        v.setSpacing(6)
        # en-tête : genre (discret) puis titre (0.7.0 : la fenêtre commençait directement par le texte)
        g = QLabel(tr('classe_genre_' + genre).upper())
        g.setStyleSheet('color: palette(placeholder-text); font-size: 8pt; letter-spacing: 1px;')
        v.addWidget(g)
        t = QLabel(titre)
        t.setWordWrap(True)
        f = t.font()
        f.setPointSizeF(f.pointSizeF() * 1.3)
        f.setBold(True)
        t.setFont(f)
        t.setAccessibleName(titre)
        ligne = QHBoxLayout()
        ligne.addWidget(t, 1)
        from .favoris_qt import BoutonFavori
        self.b_favori = BoutonFavori(genre, i, titre, self)
        ligne.addWidget(self.b_favori, 0, Qt.AlignmentFlag.AlignTop)
        v.addLayout(ligne)
        v.addWidget(zone, 1)
        # taille au contenu (bornée) : une petite table n'ouvre plus une grande fenêtre vide
        hc = w.sizeHint().height() + t.sizeHint().height() + g.sizeHint().height() + 50
        self.resize(620, int(max(260, min(680, hc))))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(ev)


_FENETRES: dict = {}


def ouvrir_ressource(genre: str, i: str) -> QWidget:
    """Ouvre (ou ramène au premier plan) la fenêtre de la ressource ; plusieurs fenêtres à la fois."""
    cle = genre + ':' + i
    f = _FENETRES.get(cle)
    if f is not None and sip.isdeleted(f):
        f = _FENETRES.pop(cle, None) and None
    try:
        if f is not None and f.isVisible():
            f.raise_()
            f.activateWindow()
            return f
    except RuntimeError:                        # fenêtre détruite
        pass
    f = FenetreRessource(genre, i)
    _FENETRES[cle] = f
    # seulement si c'est encore elle : fermée puis rouverte aussitôt, l'ancienne fenêtre est détruite après
    # l'ouverture de la nouvelle et retirait la nouvelle du registre (0.7.0)
    f.destroyed.connect(lambda *_, f=f: _FENETRES.pop(cle, None) if _FENETRES.get(cle) is f else None)
    n = len(_FENETRES)
    ecran = QApplication.primaryScreen()
    if ecran is not None:
        g = ecran.availableGeometry()
        f.move(g.right() - f.width() - 40 - (n % 6) * 28, g.top() + 60 + (n % 6) * 28)
    f.show()
    return f


def fenetres_ouvertes() -> list:
    return [f for f in _FENETRES.values() if not sip.isdeleted(f) and f.isVisible()]


def fermer_toutes():
    for f in list(_FENETRES.values()):
        try:
            f.close()
        except RuntimeError:
            pass


# ------------------------------------------------------------------ aperçu au survol
class Apercu(QFrame):
    """Bulle d'aperçu (≤ 196 × 156 px) : fiche (résumé et premier schéma), table (4 lignes), image réduite."""

    def __init__(self):
        super().__init__(None, Qt.WindowType.ToolTip)
        self.setObjectName('apercu')
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(6, 6, 6, 6)
        self.setFixedWidth(196)
        self.setMaximumHeight(156)
        self.minuteur = QTimer(self)
        self.minuteur.setSingleShot(True)
        self.minuteur.setInterval(400)
        self.minuteur.timeout.connect(self._montrer)
        self._cible = None

    def programmer(self, genre, i, pos: QPoint):
        if genre not in ('fiche', 'table', 'image'):
            return self.cacher()
        self._cible = (genre, i, pos)
        self.minuteur.start()

    def cacher(self):
        self.minuteur.stop()
        self._cible = None
        self.hide()

    def _montrer(self):
        if not self._cible:
            return
        genre, i, pos = self._cible
        while self.v.count():
            it = self.v.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        if genre == 'fiche':
            f = contenu.fiche(i)
            b = next((x for x in f['blocs'] if x['type'] == 'schema'), None)
            if b and contenu.schema(b['ref']):
                s = SchemaWidget(contenu.schema(b['ref']), theme_courant(), self)
                s.setFixedHeight(84)
                self.v.addWidget(s)
            lab = QLabel(bi(f['resume']), self)
            lab.setWordWrap(True)
            fo = lab.font()
            fo.setPointSizeF(fo.pointSizeF() * 0.8)
            lab.setFont(fo)
            self.v.addWidget(lab)
        elif genre == 'table':
            self.v.addWidget(bloc_table(contenu.table(i), self, lignes_max=4))
        else:
            im = contenu.image(i)
            if im['nature'] == 'photo':
                self.v.addWidget(ImageWidget(contenu.chemin_image(i), '', self))
            elif im['nature'] == 'schema' and im.get('schemas') and contenu.schema(im['schemas'][0]):
                self.v.addWidget(SchemaWidget(contenu.schema(im['schemas'][0]), theme_courant(), self))
        self.adjustSize()
        self.move(pos + QPoint(12, 16))
        self.show()


_APERCU: Apercu | None = None


def apercu() -> Apercu:
    """La bulle d'aperçu, unique ; recréée si l'objet Qt a été détruit (fermeture de toutes les fenêtres, tests)."""
    global _APERCU
    if _APERCU is None or sip.isdeleted(_APERCU):
        _APERCU = Apercu()
    return _APERCU
