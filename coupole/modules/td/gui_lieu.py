"""« Choisir un lieu » : une carte OpenStreetMap où l'on clique, ou une adresse cherchée (Nominatim, OpenStreetMap),
puis l'altitude du terrain (Open-Meteo, modèle numérique Copernicus à 90 m).  Sert aux calculateurs de TD
(Parallaxe, Planificateur) : rend latitude, longitude, altitude et un nom court.

Réseau : rien n'est envoyé tant qu'on ne clique pas sur « Chercher » (adresse → Nominatim, une requête par clic,
comme le demande sa politique d'usage) ou sur la carte (point → Open-Meteo pour l'altitude) ; les tuiles de la carte
suivent la politique de la carte du module Sites (cache disque, deux téléchargements au plus).
"""
from __future__ import annotations

import json
import math
import urllib.parse

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout)

from ...core.i18n import langue, tr
from ...gui import memoire
from ...gui.cartes import CarteMonde
from ...gui.outils import Tache, aide, bouton, bouton_principal, champ


def geocoder(texte: str, lg: str = 'fr') -> list[dict]:
    """Adresse ou nom de lieu → [{nom, court, lat, lon}] (Nominatim, OpenStreetMap ; 8 au plus)."""
    from ...core import reseau, sources
    url = sources.valeur('lieux.geocodage').format(q=urllib.parse.quote(texte.strip()), langue=lg)
    out = []
    for r in json.loads(reseau.lire_texte(url, delai=15)):
        try:
            lat, lon = float(r['lat']), float(r['lon'])
        except (KeyError, TypeError, ValueError):
            continue
        nom = str(r.get('display_name', ''))
        a = r.get('address') or {}
        court = str(r.get('name') or next((a[k] for k in ('village', 'town', 'city', 'hamlet', 'municipality') if a.get(k)),
                                          nom.split(',')[0])).strip()
        out.append({'nom': nom, 'court': court, 'lat': lat, 'lon': lon})
    return out


def altitude(lat: float, lon: float) -> float | None:
    """Altitude du terrain (m) au point donné (Open-Meteo, Copernicus DEM GLO-90), None si indisponible."""
    from ...core import reseau, sources
    url = sources.valeur('lieux.altitude').format(lat='%.5f' % lat, lon='%.5f' % lon)
    try:
        v = json.loads(reseau.lire_texte(url, delai=10)).get('elevation')
        return float(v[0]) if v else None
    except Exception:                                   # hors ligne, service indisponible : l'altitude reste à saisir
        return None


class DialogueLieu(QDialog):
    """Rend, si accepté, `self.choix` = {'lat', 'lon', 'alt' (m ou None), 'nom'}."""

    def __init__(self, parent=None, lat: float | None = None, lon: float | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr('lieu_titre'))
        self.choix = None
        self._taches = []
        v = QVBoxLayout(self)
        intro = QLabel(tr('lieu_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        h = QHBoxLayout()
        self.e_adresse = champ('lieu_adresse_aide', '', 'lieu_adresse_indice')
        self.e_adresse.returnPressed.connect(self.chercher)
        h.addWidget(self.e_adresse, 1)
        self.b_chercher = bouton('lieu_chercher', self.chercher)
        h.addWidget(self.b_chercher)
        v.addLayout(h)
        self.resultats = aide(QListWidget(), 'lieu_resultats_aide')
        self.resultats.setMaximumHeight(110)
        self.resultats.hide()
        self.resultats.currentItemChanged.connect(self._resultat_choisi)
        v.addWidget(self.resultats)
        self.carte = CarteMonde(self)
        aide(self.carte, 'lieu_carte_aide')
        self.carte.lieu_clique.connect(self._clic)
        if lat is not None and lon is not None:
            self.carte.centrer(lon, lat, 11)
            self._poser(lat, lon, None, '', chercher_alt=False)
        else:
            self.carte.centrer(2.5, 46.5, 5)
        v.addWidget(self.carte, 1)
        self.l_choix = QLabel(tr('lieu_aucun'))
        self.l_choix.setWordWrap(True)
        self.l_choix.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(self.l_choix)
        att = QLabel(tr('lieu_attribution'))
        att.setWordWrap(True)
        att.setOpenExternalLinks(True)
        v.addWidget(att)
        h = QHBoxLayout()
        h.addStretch(1)
        h.addWidget(bouton('dlg_annuler', self.reject))
        self.b_ok = bouton_principal('lieu_utiliser', self.accept)
        self.b_ok.setEnabled(self.choix is not None)
        h.addWidget(self.b_ok)
        v.addLayout(h)
        self.resize(900, 680)
        memoire.dialogue(self, 'td_lieu')

    # ------------------------------------------------------------------ adresse
    def chercher(self):
        t = self.e_adresse.text().strip()
        if not t:
            return
        self.b_chercher.setEnabled(False)
        self.l_choix.setText(tr('lieu_recherche'))
        tache = Tache(geocoder, t, langue(), parent=self)
        tache.quand_fini(self._trouves)
        tache.quand_erreur(lambda e: (self.b_chercher.setEnabled(True), self.l_choix.setText(tr('lieu_erreur', erreur=e[:150]))))
        self._taches.append(tache)
        tache.start()

    def _trouves(self, liste):
        self.b_chercher.setEnabled(True)
        self.resultats.clear()
        if not liste:
            self.resultats.hide()
            self.l_choix.setText(tr('lieu_rien'))
            return
        for r in liste:
            it = QListWidgetItem(r['nom'])
            it.setData(Qt.ItemDataRole.UserRole, r)
            self.resultats.addItem(it)
        self.resultats.show()
        self.resultats.setCurrentRow(0)

    def _resultat_choisi(self, it, _=None):
        if it is None:
            return
        r = it.data(Qt.ItemDataRole.UserRole)
        self.carte.centrer(r['lon'], r['lat'], 14)
        self._poser(r['lat'], r['lon'], None, r['court'])

    # ------------------------------------------------------------------ carte
    def _clic(self, lon, lat):
        # un clic près du lieu trouvé l'affine : il garde son nom (à moins de 20 km)
        c = self.choix
        proche = c is not None and math.hypot((lat - c['lat']) * 111, (lon - c['lon']) * 111 * math.cos(math.radians(lat))) < 20
        self._poser(lat, lon, None, c['nom'] if proche else '')

    def _poser(self, lat, lon, alt, nom, chercher_alt=True):
        self.choix = {'lat': lat, 'lon': lon, 'alt': alt, 'nom': nom}
        self.carte.definir([(lon, lat, nom or tr('lieu_point'), None)])
        self._afficher()
        if hasattr(self, 'b_ok'):
            self.b_ok.setEnabled(True)
        if chercher_alt:
            t = Tache(altitude, lat, lon, parent=self)
            t.quand_fini(lambda a, c=dict(self.choix): self._altitude(c, a))
            self._taches.append(t)
            t.start()

    def _altitude(self, c, a):
        if self.choix and (self.choix['lat'], self.choix['lon']) == (c['lat'], c['lon']):
            self.choix['alt'] = a
            self._afficher()

    def _afficher(self):
        if not hasattr(self, 'l_choix') or not self.choix:
            return
        c = self.choix
        alt = tr('lieu_alt_inconnue') if c['alt'] is None else '%d m' % round(c['alt'])
        self.l_choix.setText(tr('lieu_choisi', pos=texte_position(c['lat'], c['lon']), alt=alt,
                                nom=c['nom'] or '—'))

    def accept(self):
        if self.choix is None:
            return
        super().accept()


def texte_position(lat: float, lon: float) -> str:
    """« 48.83660 N, 2.33600 E » : ce que relit le lecteur de coordonnées des calculateurs."""
    return '%.5f %s, %.5f %s' % (abs(lat), 'N' if lat >= 0 else 'S', abs(lon), 'E' if lon >= 0 else 'W')


def choisir(parent, champ_position, champ_altitude=None, champ_nom=None) -> bool:
    """Ouvre la fenêtre, pré-centrée sur la position déjà saisie ; remplit les champs si l'on valide."""
    from . import coordonnees as K
    lat = lon = None
    try:
        p = K.lire_position(champ_position.text())
        lat, lon = p.lat, p.lon
    except K.CoordonneeIllisible:
        pass
    d = DialogueLieu(parent, lat, lon)
    if d.exec() != QDialog.DialogCode.Accepted or not d.choix:
        return False
    c = d.choix
    champ_position.setText(texte_position(c['lat'], c['lon']))
    if champ_altitude is not None and c['alt'] is not None:
        champ_altitude.setText('%d' % round(c['alt']))
    if champ_nom is not None and c['nom'] and not champ_nom.text().strip():
        champ_nom.setText(c['nom'][:40])
    return True
