"""Rubrique « Calculateurs de TD » : la liste des calculateurs à gauche, le calculateur choisi à droite.

Premier calculateur : « Parallaxe (TP du cours) » — saisie tolérante, pas-à-pas numéroté avec les nombres de
l'utilisateur, dessin de tout l'exercice (coupe de la Terre, corde, verticales, horizons, visées, angles, flèche à
la loupe), calcul exact, éphémérides, incertitudes, export du détail.
"""
from __future__ import annotations

import datetime as D
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QPlainTextEdit, QSlider, QSplitter, QStackedWidget, QTextBrowser, QVBoxLayout, QWidget)

from ...core.i18n import tr
from ...gui import fichiers, memoire
from ...gui.adaptatif import Flux, defilable
from ...gui.outils import Tache, aide, bouton, bouton_principal, champ, decimal, liste
from . import coordonnees as K
from . import parallaxe_tp as T
from .presentation import _n, html_detail, texte_export

UTC = D.timezone.utc
CALCULATEURS = (('parallaxe_tp', 'td_calc_parallaxe'),)


# ============================================================================================== dessin
class Schema(QWidget):
    """Coupe de la Terre dans le plan des deux lieux et du centre : corde R, verticales, horizons, visées h₁ et h₂,
    angle au centre θ, parallaxe 2α, distance D, flèche agrandie à la loupe.  `zoom` : 1 (tout l'exercice) à 60."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.res = None
        self.zoom = 1.0
        self.setMinimumSize(360, 300)
        aide(self, 'td_schema_aide')

    def montrer(self, res):
        self.res = res
        self.update()

    def _couleurs(self):
        from ...gui import theme
        fond = theme.couleur('base')
        sombre = fond.lightness() < 128
        return {'fond': fond, 'texte': theme.couleur('texte'), 'doux': theme.couleur('texte_doux'),
                'terre': QColor('#2c4f7c' if sombre else '#cfe0f3'), 'bord': QColor('#6fa8dc' if sombre else '#3d6fb4'),
                'corde': QColor('#f2c14e' if sombre else '#b7791f'), 'visee': QColor('#ef8a80' if sombre else '#c0392b'),
                'horizon': QColor('#8fd19e' if sombre else '#2e7d32'), 'objet': QColor('#ffffff' if sombre else '#222')}

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self._couleurs()
        p.fillRect(self.rect(), c['fond'])
        if not self.res or not self.res.get('exact'):
            p.setPen(c['doux'])
            p.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap),
                       tr('td_schema_vide'))
            return
        self._dessiner(p, c)

    def _plan(self):
        """Coordonnées 2-D (km) dans le plan (centre de la Terre, lieu 1, lieu 2) : x le long de la corde, y vers
        le haut au milieu."""
        import numpy as np
        g = self.res['geometrie']
        r1, r2 = np.array(g['r1']), np.array(g['r2'])
        M = np.array(self.res['exact']['M'])
        ex = (r2 - r1) / np.linalg.norm(r2 - r1)
        m = (r1 + r2) / 2
        ey = m - (m @ ex) * ex
        ey /= np.linalg.norm(ey)

        def q(v):
            return float(v @ ex), float(v @ ey)
        return q(r1), q(r2), q(M), float(np.linalg.norm(m - (m @ ex) * ex)) + g['fleche_km']

    def _dessiner(self, p, c):
        (x1, y1), (x2, y2), (xm, ym), rt = self._plan()
        w, h = self.width(), self.height()
        loin = math.hypot(xm, ym) > 3 * rt
        # cadre : la base et l'objet (s'il n'est pas trop loin), resserré par le zoom
        xs, ys = [x1, x2], [y1, y2]
        if not loin:
            xs.append(xm)
            ys.append(ym)
        else:
            ys.append(y1 + 0.35 * abs(x2 - x1) + 50)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        # zoom : de tout l'exercice (×1) jusqu'à la base seule (×60), en progression géométrique ; le centre glisse
        # vers le milieu de la base, les deux lieux restent toujours dans le cadre
        tout = max(max(xs) - min(xs), max(ys) - min(ys), 50.0) * 1.35
        base = max(abs(x2 - x1), 1.0) * 1.3
        u = min(1.0, max(0.0, (self.zoom - 1.0) / 59.0))
        etendue = tout * (min(base, tout) / tout) ** u
        cx, cy = cx + u * ((x1 + x2) / 2 - cx), cy + u * ((y1 + y2) / 2 - cy)
        k = min(w, h) / etendue

        def P(x, y):
            return QPointF(w / 2 + (x - cx) * k, h / 2 - (y - cy) * k)
        places: list[QRectF] = []
        # la loupe dans le coin le plus libre (loin des lieux et de l'objet) ; les étiquettes l'évitent
        lw, lh = 190, 110
        pts = [P(x1, y1), P(x2, y2)] + ([P(xm, ym)] if not loin else [])
        coins = [QRectF(w - lw - 8, 8, lw, lh), QRectF(8, 8, lw, lh), QRectF(w - lw - 8, h - lh - 8, lw, lh),
                 QRectF(8, h - lh - 8, lw, lh)]
        self._r_loupe = max(coins, key=lambda r: min(math.hypot(r.center().x() - q.x(), r.center().y() - q.y())
                                                     for q in pts))
        places.append(self._r_loupe.adjusted(-4, -4, 4, 4))
        f = QFont(self.font())
        f.setPointSizeF(max(8.0, f.pointSizeF() * 0.95))
        p.setFont(f)
        fm = p.fontMetrics()

        def etiquette(pt: QPointF, texte: str, couleur):
            br = QRectF(fm.boundingRect(texte)).adjusted(-3, -2, 3, 2)
            for dx, dy in ((8, -8), (8, 14), (-br.width() - 8, -8), (-br.width() - 8, 14), (-br.width() / 2, -18),
                           (-br.width() / 2, 24), (14, 2), (-br.width() - 14, 2), (8, -26), (8, 32)):
                r = QRectF(pt.x() + dx, pt.y() + dy - br.height() + 4, br.width(), br.height())
                if not any(r.intersects(q) for q in places) and self.rect().contains(r.toRect()):
                    break
            r.moveLeft(min(max(r.left(), 2.0), w - r.width() - 2))       # jamais coupée par le bord
            r.moveTop(min(max(r.top(), 2.0), h - r.height() - 2))
            places.append(r)
            p.fillRect(r, QColor(c['fond'].red(), c['fond'].green(), c['fond'].blue(), 200))
            p.setPen(couleur)
            p.drawText(r, int(Qt.AlignmentFlag.AlignCenter), texte)
        # Terre (cercle du rayon local au milieu de la corde)
        p.setPen(QPen(c['bord'], 1.5))
        p.setBrush(c['terre'])
        centre = P(0.0, 0.0)
        p.drawEllipse(centre, rt * k, rt * k)
        g = self.res['geometrie']
        x = self.res['exact']
        A, B, M = P(x1, y1), P(x2, y2), P(xm, ym)
        # verticales et horizons
        for (xa, ya), pt in (((x1, y1), A), ((x2, y2), B)):
            n = math.hypot(xa, ya)
            ux, uy = xa / n, ya / n
            L = etendue * 0.18
            p.setPen(QPen(c['doux'], 1, Qt.PenStyle.DashLine))
            p.drawLine(pt, P(xa + ux * L, ya + uy * L))
            p.setPen(QPen(c['horizon'], 1.4))
            p.drawLine(P(xa - uy * L, ya + ux * L), P(xa + uy * L, ya - ux * L))
        # corde R
        p.setPen(QPen(c['corde'], 2.2))
        p.drawLine(A, B)
        # visées et objet
        p.setPen(QPen(c['visee'], 1.8))
        if loin:
            for (xa, ya), pt in (((x1, y1), A), ((x2, y2), B)):
                dx, dy = xm - xa, ym - ya
                n = math.hypot(dx, dy)
                fin = P(xa + dx / n * etendue, ya + dy / n * etendue)
                p.drawLine(pt, fin)
            etiquette(QPointF(w / 2 - fm.horizontalAdvance(tr('td_s_objet_loin', d=_n(x['distances_km'][0], 0))) / 2,
                              26), tr('td_s_objet_loin', d=_n(x['distances_km'][0], 0)), c['visee'])
        else:
            p.drawLine(A, M)
            p.drawLine(B, M)
            p.setBrush(c['objet'])
            p.drawEllipse(M, 4, 4)
            etiquette(M, tr('td_s_D', d=_n(x['distances_km'][0], 0)), c['visee'])
            etiquette(QPointF((M.x() + A.x()) / 2, (M.y() + A.y()) / 2), '2α = %s°' % _n(
                x['parallaxe_vraie_deg'], 2), c['visee'])
        p.setBrush(Qt.BrushStyle.NoBrush)
        for pt, n, o in ((A, 1, self.res['lieux'][0]), (B, 2, self.res['lieux'][1])):
            p.setPen(QPen(c['texte'], 1))
            p.setBrush(c['visee'])
            p.drawEllipse(pt, 3.5, 3.5)
            etiquette(pt, 'h%s = %s°' % ('₁' if n == 1 else '₂', _n(o.h, 3)), c['texte'])
        etiquette(QPointF((A.x() + B.x()) / 2, (A.y() + B.y()) / 2), tr('td_s_R', r=_n(g['corde_km'], 1)),
                  c['corde'])
        for pt, prof in ((A, g['profondeur_deg'][0]), (B, g['profondeur_deg'][1])):
            etiquette(QPointF(pt.x(), pt.y() + 16), tr('td_s_prof', p=_n(abs(prof), 2)), c['horizon'])
        etiquette(centre if self.rect().contains(centre.toPoint()) else QPointF(w / 2, h - 30),
                  'θ = %s°' % _n(g['angle_centre_deg'], 3), c['doux'])
        self._loupe(p, c, g, fm)

    def _loupe(self, p, c, g, fm):
        """Loupe : la flèche (écart corde–surface au milieu), agrandie pour être visible même pour 3 km."""
        r = self._r_loupe
        lw, lh = r.width(), r.height()
        p.setPen(QPen(c['doux'], 1))
        p.setBrush(c['fond'])
        p.drawRoundedRect(r, 6, 6)
        f = g['fleche_km']
        s = g['corde_sol_km']
        # demi-corde sur 80 % de la largeur ; la flèche sur 45 % de la hauteur (échelles différentes, dites)
        kx = 0.8 * lw / max(s, 1e-9)
        ky = 0.45 * lh / max(f, 1e-9)
        x0, y0 = r.center().x(), r.top() + 26
        path = QPainterPath()
        for i in range(41):
            u = -s / 2 + s * i / 40
            yv = f * (1 - (2 * u / s) ** 2)            # arc ≈ parabole à cette échelle
            pt = QPointF(x0 + u * kx, y0 + (f - yv) * ky)
            path.moveTo(pt) if i == 0 else path.lineTo(pt)
        p.setPen(QPen(c['bord'], 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        yc = y0 + f * ky
        p.setPen(QPen(c['corde'], 1.8))
        p.drawLine(QPointF(x0 - s / 2 * kx, yc), QPointF(x0 + s / 2 * kx, yc))
        p.setPen(QPen(c['visee'], 1.2, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(x0, y0), QPointF(x0, yc))
        p.setPen(c['texte'])
        p.drawText(QRectF(r.left() + 6, r.top() + 4, lw - 12, 18), int(Qt.AlignmentFlag.AlignLeft),
                   tr('td_s_loupe'))
        p.drawText(QRectF(r.left() + 6, yc + 4, lw - 12, 34), int(Qt.AlignmentFlag.AlignCenter) |
                   int(Qt.TextFlag.TextWordWrap), tr('td_s_fleche', f=_n(f * 1000, 0)))


# ============================================================================================== panneau Parallaxe
class PanneauParallaxeTP(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.res = None
        self.tle = None
        self._taches = []
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        intro = QLabel(tr('td_p_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        sp = QSplitter(Qt.Orientation.Horizontal)
        gauche = QWidget()
        vg = QVBoxLayout(gauche)
        vg.setContentsMargins(0, 0, 0, 0)
        f = QFormLayout()
        self.c_cible = liste('td_cible_aide', [(tr('td_cible_iss'), 'iss'), (tr('td_cible_lune'), 'lune')])
        f.addRow(tr('td_cible'), self.c_cible)
        self.c_conf = liste('td_conf_aide', [(tr('td_conf_auto'), ''), (tr('td_conf_entre'), 'entre'),
                                             (tr('td_conf_meme'), 'meme_cote')])
        f.addRow(tr('td_conf'), self.c_conf)
        vg.addLayout(f)
        self.e = {}
        for n in (1, 2):
            g = QGroupBox(tr('td_lieu', n=n))
            fl = QFormLayout(g)
            for cle in ('p', 'alt', 'h', 'az'):
                w = champ('td_%s_aide' % cle, '', 'td_%s_indice' % cle)
                self.e[cle + str(n)] = w
                fl.addRow(tr('td_' + cle), w)
                memoire.champ(w, 'modules.td.parallaxe.%s%d' % (cle, n))
            vg.addWidget(g)
        f = QFormLayout()
        h = QHBoxLayout()
        self.e_instant = champ('td_instant_aide', '', 'td_instant_indice')
        memoire.champ(self.e_instant, 'modules.td.parallaxe.instant')
        h.addWidget(self.e_instant, 1)
        h.addWidget(bouton('td_maintenant', self.maintenant))
        f.addRow(tr('td_instant'), h)
        self.s_h = decimal('td_sigma_h_aide', 0.0, 10.0, 0.1, 'td_unite_deg')
        self.s_h.setDecimals(3)
        self.s_pos = decimal('td_sigma_pos_aide', 0.0, 100000.0, 20.0, 'td_unite_m')
        self.s_t = decimal('td_sigma_t_aide', 0.0, 600.0, 1.0, 'td_unite_s')
        f.addRow(tr('td_sigma_h'), self.s_h)
        f.addRow(tr('td_sigma_pos'), self.s_pos)
        f.addRow(tr('td_sigma_t'), self.s_t)
        vg.addLayout(f)
        g = QGroupBox(tr('td_eph'))
        vgg = QVBoxLayout(g)
        self.l_eph = QLabel('')
        self.l_eph.setWordWrap(True)
        vgg.addWidget(self.l_eph)
        fl = Flux()
        self.b_de440 = bouton('td_de440', self.telecharger_de440)
        self.b_tle = bouton('td_tle_recuperer', self.recuperer_tle)
        fl.addWidget(self.b_de440)
        fl.addWidget(self.b_tle)
        vgg.addLayout(fl)
        self.e_tle = aide(QPlainTextEdit(), 'td_tle_aide')
        self.e_tle.setMaximumHeight(56)
        self.e_tle.setPlaceholderText(tr('td_tle_indice'))
        vgg.addWidget(self.e_tle)
        vg.addWidget(g)
        fl = Flux()
        self.b_calculer = bouton_principal('td_calculer', self.calculer)
        fl.addWidget(self.b_calculer)
        fl.addWidget(bouton('td_exemple', self.exemple))
        self.b_exporter = bouton('td_exporter', self.exporter)
        self.b_exporter.setEnabled(False)
        fl.addWidget(self.b_exporter)
        vg.addLayout(fl)
        vg.addStretch(1)
        sp.addWidget(defilable(gauche))
        droite = QSplitter(Qt.Orientation.Vertical)
        haut = QWidget()
        vh = QVBoxLayout(haut)
        vh.setContentsMargins(0, 0, 0, 0)
        self.schema = Schema()
        vh.addWidget(self.schema, 1)
        hz = QHBoxLayout()
        hz.addWidget(QLabel(tr('td_zoom')))
        self.zoom = aide(QSlider(Qt.Orientation.Horizontal), 'td_zoom_aide')
        self.zoom.setRange(10, 600)
        self.zoom.setValue(10)
        self.zoom.valueChanged.connect(self._zoom)
        hz.addWidget(self.zoom, 1)
        vh.addLayout(hz)
        droite.addWidget(haut)
        self.detail = aide(QTextBrowser(), 'td_detail_aide')
        droite.addWidget(self.detail)
        droite.setSizes([420, 420])
        sp.addWidget(droite)
        sp.setStretchFactor(0, 2)
        sp.setStretchFactor(1, 3)
        v.addWidget(sp, 1)
        self.l_etat = QLabel('')
        self.l_etat.setWordWrap(True)
        v.addWidget(self.l_etat)
        memoire.liste(self.c_cible, 'modules.td.parallaxe.cible')
        memoire.separateur(sp, 'modules.td.parallaxe.separateur')
        self._maj_eph()

    # ------------------------------------------------------------------ outils
    def _zoom(self, v):
        self.schema.zoom = v / 10.0
        self.schema.update()

    def _maj_eph(self):
        from ..partages import astro
        src = astro.source_ephemeride()
        self.l_eph.setText(tr('td_eph_etat_' + src))
        self.b_de440.setVisible(src != 'de440')
        self.b_de440.setEnabled(astro.jplephem_present())

    def maintenant(self):
        self.e_instant.setText(D.datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S'))

    def exemple(self):
        ex = T.exemple(self.c_cible.currentData())
        self.c_cible.setCurrentIndex(self.c_cible.findData(ex['cible']))
        for n in (1, 2):
            self.e['p%d' % n].setText(ex['p%d' % n])
            self.e['alt%d' % n].setText(ex['alt%d' % n])
            self.e['h%d' % n].setText(ex['h%d' % n])
            self.e['az%d' % n].setText(ex['az%d' % n])
        self.e_instant.setText(ex['instant'])
        self.l_etat.setText(tr('td_exemple_fictif'))
        self.calculer()

    def telecharger_de440(self):
        from ...core import reseau, sources
        from ..partages import astro
        self.b_de440.setEnabled(False)
        self.l_etat.setText(tr('td_de440_en_cours'))
        t = Tache(reseau.telecharger, sources.valeur('ephemerides.de440s'),
                  str(astro.dossier_ephemerides() / astro.NOM_DE440), parent=self)
        t.quand_fini(lambda r: (self._maj_eph(), self.l_etat.setText(tr('td_de440_ok'))))
        t.quand_erreur(lambda e: (self.b_de440.setEnabled(True), self.l_etat.setText(tr('td_de440_echec',
                                                                                          erreur=e[:200]))))
        self._taches.append(t)
        t.start()

    def recuperer_tle(self):
        from . import tle
        inst = self._instant() or D.datetime.now(UTC)
        self.b_tle.setEnabled(False)
        t = Tache(tle.pour, inst, parent=self)
        t.quand_fini(self._tle_recu)
        t.quand_erreur(lambda e: (self.b_tle.setEnabled(True), self.l_etat.setText(e[:200])))
        self._taches.append(t)
        t.start()

    def _tle_recu(self, r):
        self.b_tle.setEnabled(True)
        if not r['tle']:
            self.l_etat.setText(tr('td_tle_aucun', erreur=r['erreur'][:200]))
            return
        self.e_tle.setPlainText('\n'.join(r['tle']))
        self.l_etat.setText(tr('td_tle_recu', date=r['epoque'].strftime('%Y-%m-%d %H:%M'),
                               age=_n(r['age_jours'], 1), source=tr('td_tle_source_' + r['source'])))

    def _instant(self):
        t = self.e_instant.text().strip()
        if not t:
            return None
        from ..partages.mesures import instant
        v = instant(t if any(x in t.upper() for x in ('UTC', ' TU', 'Z')) else t + ' UTC').valeur
        if v is None:
            raise K.CoordonneeIllisible('td_err_instant', texte=t)
        return v

    def entrees(self) -> T.Entrees:
        lieux, notes = [], []
        for n in (1, 2):
            pos = K.lire_position(self.e['p%d' % n].text())
            for x in pos.notes:
                if x.startswith('td_a_'):
                    notes.append((x, {'n': n}))
            h = self.e['h%d' % n].text().strip()
            az = self.e['az%d' % n].text().strip()
            if not h:
                raise K.CoordonneeIllisible('td_err_h', n=n)
            lieux.append(T.Lieu(pos.lat, pos.lon, K.lire_altitude(self.e['alt%d' % n].text()), K.lire_angle(h).valeur,
                                K.lire_angle(az).valeur % 360.0 if az else None))
        tle = None
        lignes = [x for x in self.e_tle.toPlainText().splitlines() if x.strip()]
        if len(lignes) >= 2:
            tle = tuple(lignes)
        return T.Entrees(lieux[0], lieux[1], self.c_cible.currentData(), self._instant(), tle,
                         self.c_conf.currentData(), self.s_h.value(), self.s_pos.value(), self.s_t.value(), notes)

    def calculer(self):
        try:
            e = self.entrees()
        except K.CoordonneeIllisible as ex:
            self.l_etat.setText(tr(ex.cle, **ex.valeurs))
            return
        self.b_calculer.setEnabled(False)
        self.l_etat.setText(tr('td_calcul_en_cours'))
        t = Tache(T.calculer, e, parent=self)
        t.quand_fini(lambda r, e=e: self._resultat(e, r))
        t.quand_erreur(self._erreur)
        self._taches.append(t)
        t.start()

    def _erreur(self, texte):
        self.b_calculer.setEnabled(True)
        cle = next((m for m in texte.replace(':', ' ').split() if m.startswith('td_err_')), '')
        self.l_etat.setText(tr(cle) if cle else texte[:300])

    def _resultat(self, e, r):
        self.b_calculer.setEnabled(True)
        r['lieux'] = [e.o1, e.o2]
        self.res = r
        self.schema.montrer(r)
        self.detail.setHtml(html_detail(e, r))
        self.b_exporter.setEnabled(True)
        self.l_etat.setText(tr('td_calcul_fait'))

    def exporter(self):
        if not self.res:
            return
        chemin, _ = fichiers.choisir_enregistrement(self, tr('td_exporter'), 'parallaxe_tp.csv', 'CSV (*.csv)')
        if not chemin:
            return
        with open(chemin, 'w', encoding='utf-8-sig', newline='') as fh:
            fh.write(texte_export(self.res))
        self.l_etat.setText(tr('td_exporte', chemin=chemin))

    def aide_html(self) -> str:
        return tr('td_aide_html')


# ============================================================================================== rubrique
class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self)
        sp = QSplitter(Qt.Orientation.Horizontal)
        g = QWidget()
        vg = QVBoxLayout(g)
        vg.setContentsMargins(0, 0, 0, 0)
        lab = QLabel(tr('td_rubrique_intro'))
        lab.setWordWrap(True)
        vg.addWidget(lab)
        self.liste = aide(QListWidget(), 'td_liste_aide')
        for ident, cle in CALCULATEURS:
            it = QListWidgetItem(tr(cle))
            it.setData(Qt.ItemDataRole.UserRole, ident)
            it.setToolTip(tr(cle + '_aide'))
            self.liste.addItem(it)
        vg.addWidget(self.liste, 1)
        sp.addWidget(g)
        self.pile = QStackedWidget()
        self.parallaxe = PanneauParallaxeTP()
        self.pile.addWidget(self.parallaxe)
        sp.addWidget(self.pile)
        sp.setStretchFactor(0, 1)
        sp.setStretchFactor(1, 5)
        sp.setSizes([220, 1100])
        h.addWidget(sp)
        self.liste.setCurrentRow(0)
        self.liste.currentRowChanged.connect(self.pile.setCurrentIndex)

    def aide_html(self) -> str:
        return tr('td_aide_html')


_ = (QComboBox,)
