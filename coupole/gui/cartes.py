"""Cartes légères dessinées en Qt (sans QtWebEngine).

* ``CarteCiel`` : projection d'Aitoff (ascension droite croissante vers la gauche, 12 h au centre, comme
  dans Inventaire.pdf), points, écliptique et plan galactique (calculés par astropy).
* ``CarteMonde`` : tuiles OpenStreetMap (projection de Mercator Web) mises en cache disque, téléchargées
  au plus à deux à la fois avec un User-Agent identifiant l'application (politique d'usage des tuiles OSM :
  https://operations.osmfoundation.org/policies/tiles/), attribution « © OpenStreetMap contributors »
  toujours affichée.  Hors ligne : fond uni et graticule, les points restent utilisables.
"""
from __future__ import annotations

import concurrent.futures as F
import math
import os
import threading
import time
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PyQt6 import sip
from PyQt6.QtWidgets import QApplication, QToolTip, QWidget

from ..core import config
from ..core.i18n import tr


# ======================================================================== ciel
def aitoff(ra_deg, dec_deg):
    """Coordonnées d'Aitoff normalisées (x ∈ [-2, 2], y ∈ [-1, 1]) ; RA croissante vers la gauche, 12 h au centre."""
    lam = np.radians(180.0 - np.asarray(ra_deg, dtype=float))       # 12 h au centre, croissante vers la gauche
    lam = (lam + np.pi) % (2 * np.pi) - np.pi
    phi = np.radians(np.asarray(dec_deg, dtype=float))
    alpha = np.arccos(np.cos(phi) * np.cos(lam / 2))
    sinc = np.where(alpha == 0, 1.0, np.sin(alpha) / np.where(alpha == 0, 1.0, alpha))
    x = 2 * np.cos(phi) * np.sin(lam / 2) / sinc
    y = np.sin(phi) / sinc
    return x / np.pi * 2, y / (np.pi / 2)


_lignes_ciel = None
_VIDE = ((np.array([]), np.array([])), (np.array([]), np.array([])))


def calculer_lignes_ciel():
    """(écliptique, plan galactique) en (ra, dec) degrés — astropy, ~1 s au premier appel : à faire hors du
    fil graphique (CarteCiel le lance par une Tache) ; le résultat est gardé."""
    global _lignes_ciel
    if _lignes_ciel is None:
        try:
            from astropy import units as u
            from astropy.coordinates import BarycentricMeanEcliptic, Galactic, SkyCoord
            t = np.linspace(0, 360, 361)
            ecl = SkyCoord(lon=t * u.deg, lat=0 * t * u.deg, frame=BarycentricMeanEcliptic()).icrs
            gal = SkyCoord(l=t * u.deg, b=0 * t * u.deg, frame=Galactic()).icrs
            _lignes_ciel = ((ecl.ra.deg, ecl.dec.deg), (gal.ra.deg, gal.dec.deg))
        except Exception:
            _lignes_ciel = _VIDE
    return _lignes_ciel


def lignes_ciel():
    """Valeur déjà calculée, ou lignes vides (jamais de calcul dans le fil graphique)."""
    return _lignes_ciel if _lignes_ciel is not None else _VIDE


class CarteCiel(QWidget):
    point_clique = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []          # (ra, dec, rayon_px, QColor, étiquette, donnée)
        self.setMouseTracking(True)
        self.setMinimumSize(400, 220)
        self._t = None
        self._proj = None         # (taille du widget, x px, y px, rayons) : projection calculée une fois
        self._survol = None

    def showEvent(self, ev):
        super().showEvent(ev)
        if _lignes_ciel is None and self._t is None:          # premier affichage : lignes calculées en fond
            from .outils import Tache
            self._t = Tache(calculer_lignes_ciel, parent=self)
            self._t.quand_fini(lambda _: self.update())
            self._t.start()

    def definir(self, points):
        self.points = points
        self._proj = None
        self.update()

    def _projection(self):
        """Positions à l'écran de TOUS les points, en une projection numpy par taille de fenêtre (et non une
        projection par point à chaque dessin et à chaque mouvement de souris : 8 000 points rendaient le survol
        saccadé)."""
        taille = (self.width(), self.height())
        if self._proj is None or self._proj[0] != taille:
            if self.points:
                ra = np.fromiter((p[0] for p in self.points), float, len(self.points))
                de = np.fromiter((p[1] for p in self.points), float, len(self.points))
                x, y = self._px(ra, de)
                r = np.fromiter((p[2] for p in self.points), float, len(self.points))
            else:
                x = y = r = np.zeros(0)
            self._proj = (taille, np.asarray(x, float), np.asarray(y, float), r)
        return self._proj[1:]

    def _geo(self):
        w, h = self.width() - 20, self.height() - 40
        larg = min(w, 2 * h)
        return QPointF(self.width() / 2, 10 + h / 2), larg / 4, larg / 4

    def _px(self, ra, dec):
        c, sx, sy = self._geo()
        x, y = aitoff(ra, dec)
        return c.x() + x * sx, c.y() - y * sy * 1.0

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), self.palette().base())
        c, sx, sy = self._geo()
        fond = QPainterPath()
        t = np.linspace(-90, 90, 181)
        xs, ys = self._px(np.full_like(t, 0.0001), t)
        xs2, ys2 = self._px(np.full_like(t, 359.9999), t[::-1])
        fond.moveTo(xs[0], ys[0])
        for a, b in list(zip(xs, ys)) + list(zip(xs2, ys2)):
            fond.lineTo(a, b)
        p.fillPath(fond, QColor('#0F1A33'))
        grille = QPen(QColor(255, 255, 255, 50), 1)
        p.setPen(grille)
        for ra in range(0, 360, 30):
            d = np.linspace(-90, 90, 91)
            self._ligne(p, np.full_like(d, ra if ra else 0.0001), d)
        for de in (-60, -30, 0, 30, 60):
            r = np.linspace(0.0001, 359.9999, 361)
            self._ligne(p, r, np.full_like(r, de))
        (er, ed), (gr, gd) = lignes_ciel()
        p.setPen(QPen(QColor('#F2C14E'), 1.4, Qt.PenStyle.DashLine))
        self._ligne(p, er, ed, coupe=True)
        p.setPen(QPen(QColor('#9FB6D9'), 1.4, Qt.PenStyle.DotLine))
        self._ligne(p, gr, gd, coupe=True)
        f = QFont(self.font())
        f.setPointSizeF(max(7.0, f.pointSizeF() * 0.85))
        p.setFont(f)
        p.setPen(self.palette().text().color())
        for h in range(2, 24, 4):
            x, y = self._px(h * 15, 0)
            p.drawText(QRectF(x - 20, c.y() + sy + 4, 40, 14), Qt.AlignmentFlag.AlignHCenter, '%d h' % h)
        xs, ys, _ = self._projection()
        p.setPen(Qt.PenStyle.NoPen)
        couleur = None
        for (_, _, rayon, coul, _, _), x, y in zip(self.points, xs.tolist(), ys.tolist()):
            if coul is not couleur:
                p.setBrush(QBrush(coul))
                couleur = coul
            p.drawEllipse(QPointF(x, y), rayon, rayon)
        p.setPen(self.palette().text().color())
        p.drawText(QRectF(8, self.height() - 18, self.width() - 16, 16), Qt.AlignmentFlag.AlignLeft,
                   tr('carte_legende_ciel'))
        p.end()

    def _ligne(self, p, ra, dec, coupe=False):
        x, y = self._px(np.asarray(ra), np.asarray(dec))
        chemin = QPainterPath()
        prec = None
        for a, b in zip(x, y):
            if prec is None or (coupe and abs(a - prec[0]) > self.width() / 4):
                chemin.moveTo(float(a), float(b))
            else:
                chemin.lineTo(float(a), float(b))
            prec = (a, b)
        p.drawPath(chemin)

    def _proche(self, pos):
        """Point le plus proche du curseur (dans son rayon + 2 px, ou à moins de 12 px) : distances numpy."""
        if not self.points:
            return None
        xs, ys, rs = self._projection()
        d = np.hypot(xs - pos.x(), ys - pos.y())
        portee = np.maximum(12.0, rs + 2)
        ok = d < portee
        if not ok.any():
            return None
        k = int(np.flatnonzero(ok)[np.argmin(d[ok])])
        return self.points[k]

    def mouseMoveEvent(self, ev):
        pt = self._proche(ev.position())
        if pt is not None:
            if pt is not self._survol:              # l'info-bulle ne change qu'en changeant de point
                QToolTip.showText(ev.globalPosition().toPoint(), pt[4], self)
            self._survol = pt
        else:
            if self._survol is not None:
                QToolTip.hideText()
            self._survol = None

    def mousePressEvent(self, ev):
        pt = self._proche(ev.position())
        if pt is not None:
            self.point_clique.emit(pt[5])


# ======================================================================== monde
TAILLE_TUILE = 256
ZOOM_MAX = 19                 # dernier niveau servi par les tuiles OSM standard
DPR_TUILES_FINES = 1.5        # à partir de ce facteur d'échelle d'écran, on dessine les tuiles du niveau z + 1


def lonlat_vers_monde(lon, lat, z):
    n = 2 ** z * TAILLE_TUILE
    x = (lon + 180.0) / 360.0 * n
    lat = max(-85.05112878, min(85.05112878, lat))
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def monde_vers_lonlat(x, y, z):
    n = 2 ** z * TAILLE_TUILE
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


class CacheTuiles:
    """Tuiles OSM en cache disque ; deux téléchargements au plus ; réessai différé après un échec."""
    AGE_MAX = 30 * 86400

    def __init__(self, rappel):
        self.dossier = config.dossier_cache() / 'tuiles'
        self.pool = F.ThreadPoolExecutor(2, thread_name_prefix='tuiles')
        self.pool_disque = F.ThreadPoolExecutor(2, thread_name_prefix='tuiles-disque')
        self.en_cours = set()
        self.en_lecture = set()
        self.echecs = {}
        import collections
        self.memoire = collections.OrderedDict()   # LRU : les plus anciennes sortent une à une (plus de vidage
        #                                            complet qui faisait relire et décoder tout l'écran d'un coup)
        self.rappel = rappel
        self.verrou = threading.Lock()
        self.hors_ligne = False
        self.ferme = False

    def fermer(self):
        """Arrête les téléchargements (fermeture de la carte ou de l'application) ; plus aucun rappel ensuite."""
        self.ferme = True
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.pool_disque.shutdown(wait=False, cancel_futures=True)

    def chemin(self, z, x, y) -> Path:
        return self.dossier / str(z) / str(x) / ('%d.png' % y)

    MEMOIRE_MAX = 600

    def _garder(self, cle, im):
        with self.verrou:
            self.memoire[cle] = im
            self.memoire.move_to_end(cle)
            while len(self.memoire) > self.MEMOIRE_MAX:
                self.memoire.popitem(last=False)

    def _lire_disque(self, cle):
        """Lecture et décodage PNG d'une tuile du cache disque ; None si absente ou illisible."""
        p = self.chemin(*cle)
        try:
            st = p.stat()
        except OSError:
            return None
        im = QImage(str(p))
        if im.isNull():
            return None
        self._garder(cle, im)
        if time.time() - st.st_mtime > self.AGE_MAX:
            self._demander(cle)
        return im

    def tuile(self, z, x, y, synchrone=True):
        """La tuile en mémoire ; sinon lue sur le disque — tout de suite si `synchrone` (le dessin a encore du
        temps), sinon par un fil (le dessin suivant l'aura) ; sinon téléchargée."""
        cle = (z, x, y)
        with self.verrou:
            im = self.memoire.get(cle)
            if im is not None:
                self.memoire.move_to_end(cle)
                return im
        if synchrone:
            im = self._lire_disque(cle)
            if im is not None:
                return im
            if not self.chemin(*cle).exists():
                self._demander(cle)
            return None
        with self.verrou:
            if self.ferme or cle in self.en_lecture:
                return None
            self.en_lecture.add(cle)
        self.pool_disque.submit(self._lire_puis_rappeler, cle)
        return None

    def _lire_puis_rappeler(self, cle):
        try:
            im = self._lire_disque(cle)
            if im is None and not self.chemin(*cle).exists():
                self._demander(cle)
        finally:
            with self.verrou:
                self.en_lecture.discard(cle)
            if not self.ferme:
                self.rappel()

    def _demander(self, cle):
        with self.verrou:
            if self.ferme or cle in self.en_cours or self.hors_ligne or time.time() - self.echecs.get(cle, 0) < 300:
                return
            self.en_cours.add(cle)
        self.pool.submit(self._telecharger, cle)

    def _telecharger(self, cle):
        from ..core import reseau, sources
        z, x, y = cle
        url = sources.valeur('cartes.tuiles').format(z=z, x=x, y=y)
        try:
            with reseau.requete(url, delai=15) as r:
                data = r.read(2_000_000)
            p = self.chemin(z, x, y)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix('.tmp')
            tmp.write_bytes(data)
            os.replace(tmp, p)
            with self.verrou:
                self.memoire.pop(cle, None)
        except Exception:
            self.echecs[cle] = time.time()
            if len(self.echecs) > 6 and not any(self.chemin(*k).exists() for k in list(self.echecs)[:6]):
                self.hors_ligne = True
        finally:
            with self.verrou:
                self.en_cours.discard(cle)
            if not self.ferme:
                self.rappel()


class CarteMonde(QWidget):
    site_clique = pyqtSignal(object)
    vue_changee = pyqtSignal()        # zoom ou centre changés (la vue est gardée d'une fermeture à l'autre)
    _rafraichir = pyqtSignal()
    BUDGET_TUILES_S = 0.03

    def __init__(self, parent=None, en_ligne=True):
        super().__init__(parent)
        self.z = 2
        self.centre = (10.0, 30.0)
        self.points = []           # (lon, lat, étiquette, donnée)
        self.en_ligne = en_ligne
        self.cache = CacheTuiles(self._tuile_arrivee)
        self._rafraichir.connect(self.update)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.cache.fermer)
        self.destroyed.connect(self.cache.fermer)
        self._glisse = None
        self.setMouseTracking(True)
        self.setMinimumSize(400, 260)

    def _tuile_arrivee(self):
        # Appelé depuis un fil de téléchargement : si le widget a déjà été détruit (fenêtre fermée pendant un
        # téléchargement), émettre son signal ferait planter Python ; on vérifie d'abord.
        if not self.cache.ferme and not sip.isdeleted(self):
            self._rafraichir.emit()

    def definir(self, points):
        self.points = points
        self.update()

    def centrer(self, lon, lat, z=None):
        self.centre = (lon, lat)
        if z is not None:
            self.z = max(1, min(17, z))
        self.update()
        self.vue_changee.emit()

    def vue(self) -> dict:
        return {'z': int(self.z), 'lon': round(float(self.centre[0]), 6), 'lat': round(float(self.centre[1]), 6)}

    def definir_vue(self, v) -> bool:
        """Rétablit une vue gardée ; rend False (et ne change rien) si elle n'est pas valable."""
        try:
            z, lon, lat = v['z'], float(v['lon']), float(v['lat'])
        except (KeyError, TypeError, ValueError):
            return False
        if not isinstance(z, int) or isinstance(z, bool) or not (math.isfinite(lon) and math.isfinite(lat)):
            return False
        self.centrer(((lon + 180.0) % 360.0) - 180.0, max(-85.0, min(85.0, lat)), z)
        return True

    def _origine(self):
        cx, cy = lonlat_vers_monde(self.centre[0], self.centre[1], self.z)
        return cx - self.width() / 2, cy - self.height() / 2

    def _zoom_tuiles(self) -> tuple[int, int]:
        """(niveau de zoom des tuiles dessinées, nombre de tuiles par côté d'une tuile logique).

        Sur un écran dense (facteur d'échelle ≥ 1,5 : Windows à 150 %, Mac Retina), une tuile de 256 px dessinée
        en 256 pixels logiques est agrandie par le système et devient floue.  On prend alors les tuiles du niveau
        z + 1 — quatre par tuile logique, chacune dessinée à demi-taille (l'équivalent « @2x ») : à 2× le rendu
        est exactement à un pixel physique par pixel de tuile.  Le cache ne change pas (ce sont des tuiles
        ordinaires d'un autre niveau)."""
        try:
            dpr = float(self.devicePixelRatioF())
        except Exception:
            dpr = 1.0
        if dpr >= DPR_TUILES_FINES and self.z + 1 <= ZOOM_MAX:
            return self.z + 1, 2
        return self.z, 1

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)   # tuiles redimensionnées sans crénelage
        p.fillRect(self.rect(), QColor('#DDE6EE'))
        ox, oy = self._origine()
        n = 2 ** self.z
        manque = 0
        if self.en_ligne:
            zt, k = self._zoom_tuiles()
            cote = TAILLE_TUILE / k                 # taille logique d'une tuile du niveau dessiné
            # décodage des tuiles du disque dans le dessin pendant BUDGET_TUILES_S au plus, le reste par un fil
            # (redessin à l'arrivée) : un changement de zoom à 2× (≈ 100 tuiles) ne fige plus l'interface
            fin_budget = time.perf_counter() + self.BUDGET_TUILES_S
            for tx in range(int(ox // TAILLE_TUILE), int((ox + self.width()) // TAILLE_TUILE) + 1):
                for ty in range(max(0, int(oy // TAILLE_TUILE)), min(n, int((oy + self.height()) // TAILLE_TUILE) + 1)):
                    for i in range(k):
                        for j in range(k):
                            im = self.cache.tuile(zt, (tx * k + i) % (n * k), ty * k + j,
                                                  synchrone=time.perf_counter() < fin_budget)
                            if im is not None:
                                p.drawImage(QRectF(tx * TAILLE_TUILE - ox + i * cote, ty * TAILLE_TUILE - oy + j * cote,
                                                   cote, cote), im)
                            else:
                                manque += 1
        if not self.en_ligne or manque:
            p.setPen(QPen(QColor(100, 120, 140, 90), 1))
            for lon in range(-180, 181, 30):
                x, _ = lonlat_vers_monde(lon, 0, self.z)
                p.drawLine(QPointF(x - ox, 0), QPointF(x - ox, self.height()))
            for lat in range(-60, 61, 30):
                _, y = lonlat_vers_monde(0, lat, self.z)
                p.drawLine(QPointF(0, y - oy), QPointF(self.width(), y - oy))
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = QFont(self.font())
        f.setPointSizeF(max(7.0, f.pointSizeF() * 0.85))
        p.setFont(f)
        if not self.en_ligne or manque:                 # graduations du fond simple
            p.setPen(QColor(90, 105, 125))
            for lon in range(-180, 181, 30):
                x, _ = lonlat_vers_monde(lon, 0, self.z)
                p.drawText(QPointF(x - ox + 3, 12), '%d°' % lon)
            for lat in range(-60, 61, 30):
                _, y = lonlat_vers_monde(0, lat, self.z)
                p.drawText(QPointF(3, y - oy - 3), '%d°' % lat)
        centres = []
        for lon, lat, etiquette, _ in self.points:
            x, y = lonlat_vers_monde(lon, lat, self.z)
            centres.append((x - ox, y - oy, etiquette.split('\n')[0]))
            p.setPen(QPen(QColor('white'), 2))
            p.setBrush(QColor('#B5382B'))
            p.drawEllipse(QPointF(x - ox, y - oy), 6, 6)
        # Étiquettes sur fond clair (lisibles sur les tuiles), placées à droite, à gauche, dessous ou dessus du
        # point selon la place ; une étiquette qui chevaucherait encore une autre n'est pas dessinée (le survol
        # du point la montre).
        fm = p.fontMetrics()
        poses = []
        for cx, cy, texte in centres:
            l, h = fm.horizontalAdvance(texte) + 8, fm.height() + 2
            for r in (QRectF(cx + 9, cy - h / 2, l, h), QRectF(cx - 9 - l, cy - h / 2, l, h),
                      QRectF(cx - l / 2, cy + 9, l, h), QRectF(cx - l / 2, cy - 9 - h, l, h)):
                if not any(r.intersects(q) for q in poses):
                    poses.append(r)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(255, 255, 255, 215))
                    p.drawRoundedRect(r, 3, 3)
                    p.setPen(QColor('#1F2430'))
                    p.drawText(r, Qt.AlignmentFlag.AlignCenter, texte)
                    break
        texte = tr('carte_attribution') if self.en_ligne else tr('carte_hors_ligne')
        if self.en_ligne and self.cache.hors_ligne:
            texte = tr('carte_hors_ligne')
        lw = p.fontMetrics().horizontalAdvance(texte) + 10
        r = QRectF(self.width() - lw - 4, self.height() - 18, lw, 16)
        p.fillRect(r, QColor(255, 255, 255, 210))
        p.setPen(QColor('#1F2430'))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, texte)
        p.end()

    def _proche(self, pos):
        ox, oy = self._origine()
        for pt in self.points:
            x, y = lonlat_vers_monde(pt[0], pt[1], self.z)
            if math.hypot(x - ox - pos.x(), y - oy - pos.y()) < 9:
                return pt
        return None

    def mousePressEvent(self, ev):
        pt = self._proche(ev.position())
        if pt is not None:
            self.site_clique.emit(pt[3])
            return
        self._glisse = (ev.position(), self.centre)

    def mouseMoveEvent(self, ev):
        if self._glisse is not None:
            d = ev.position() - self._glisse[0]
            cx, cy = lonlat_vers_monde(*self._glisse[1], self.z)
            self.centre = monde_vers_lonlat(cx - d.x(), cy - d.y(), self.z)
            self.update()
            return
        pt = self._proche(ev.position())
        if pt is not None:
            QToolTip.showText(ev.globalPosition().toPoint(), pt[2], self)
        else:
            QToolTip.hideText()

    def mouseReleaseEvent(self, ev):
        if self._glisse is not None:
            self.vue_changee.emit()
        self._glisse = None

    def wheelEvent(self, ev):
        self.z = max(1, min(17, self.z + (1 if ev.angleDelta().y() > 0 else -1)))
        self.update()
        self.vue_changee.emit()
