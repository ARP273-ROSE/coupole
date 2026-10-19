"""Une session de travail sur un partage : liste, structure, tableaux de mesures, en-têtes, fichiers en cache.

Tout ce qui touche le réseau est ici, sans Qt : l'interface l'appelle depuis des fils de fond, la ligne de commande
directement.  Lecture seule : aucune méthode de cette classe n'écrit sur le partage (le dépôt est dans ``depot.py``).
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

from . import etat, structure as S, tableur
from .mesures import controler, est_tableau_de_mesures, lire_tableau
from .webdav import Client, InfoPartage

#: octets lus au début d'un FITS pour son en-tête (un en-tête dépasse rarement 10 blocs de 2 880 octets)
OCTETS_ENTETE = 2880 * 12
TAILLE_MAX_TABLEAU = 20_000_000


class Session:
    def __init__(self, memorise: etat.PartageMemorise, delai: float = 30.0):
        self.memorise = memorise
        self.partage = memorise.partage()
        self.client = Client(self.partage, delai)
        self.ident = memorise.ident
        self.dossier = etat.dossier_partage(self.ident)
        self.info: InfoPartage | None = None
        self.entrees: list = []
        self.structure: S.Structure | None = None
        self.tableaux: dict = {}            # chemin -> (Classeur, [Tableau de mesures])
        self.entetes: dict = etat.lire_json(self.ident, 'entetes.json', {}) or {}
        self._verrou = threading.Lock()

    # ------------------------------------------------------------------ liste
    def verifier(self) -> InfoPartage:
        self.info = self.client.verifier()
        etat.modifier(self.ident, droits=self.info.droits)
        return self.info

    def rafraichir(self, arret=None, progression=None) -> S.Structure:
        """Relit toute l'arborescence ; les fichiers absents de la visite précédente sont « nouveaux »."""
        self.entrees = self.client.lister_tout(arret, progression)
        etat.memoriser_liste(self.ident, self.entrees)
        self.structure = S.decouvrir(self.entrees, etat.vus(self.ident))
        self._appliquer_entetes()
        return self.structure

    def depuis_cache(self) -> S.Structure | None:
        """Structure de la dernière liste lue (hors ligne, ou en attendant le réseau)."""
        e = etat.liste_vue(self.ident)
        if e is None:
            return None
        self.entrees = e
        self.structure = S.decouvrir(e, etat.vus(self.ident))
        self._appliquer_entetes()
        return self.structure

    def marquer_vus(self):
        etat.marquer_vus(self.ident, self.entrees)
        if self.structure is not None:
            for f in self.structure.fichiers:
                f.nouveau = False

    # ------------------------------------------------------------------ fichiers
    def chemin_cache(self, chemin: str) -> Path:
        p = self.dossier / 'fichiers' / Path(*[x for x in chemin.split('/') if x not in ('', '.', '..')])
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def fichier_local(self, chemin: str, taille: int | None = None, limiteur=None, arret=None,
                      progression=None) -> str:
        """Copie locale (cache) d'un fichier du partage ; téléchargée si absente ou incomplète."""
        p = str(self.chemin_cache(chemin))
        if taille is not None and os.path.exists(p) and os.path.getsize(p) == taille:
            return p
        self.client.telecharger(chemin, p, taille, limiteur, arret, progression)
        return p

    def debut_fichier(self, chemin: str, octets: int) -> bytes:
        return self.client.lire(chemin, 0, octets - 1, max_octets=octets + 1024)

    # ------------------------------------------------------------------ en-têtes FITS (sans tout télécharger)
    def lire_entete_fits(self, chemin: str) -> dict:
        """Lieu et heure d'un FITS d'après son en-tête, lu par une requête partielle (premiers 34 ko)."""
        from .analyses.parallaxe.image import lieu_et_heure
        cartes = analyser_cartes(self.debut_fichier(chemin, OCTETS_ENTETE))
        lh = lieu_et_heure(cartes)
        r = {'lat': lh['lat'], 'lon': lh['lon'], 'alt_m': lh['alt_m'], 'pose_s': lh['pose_s'],
             'instant': lh['instant'].isoformat() if lh['instant'] else None,
             'milieu': lh['milieu'].isoformat() if lh['milieu'] else None,
             'objet': str(cartes.get('OBJECT', '') or '').strip(), 'wcs': 'CTYPE1' in cartes and 'CRVAL1' in cartes,
             'instrument': str(cartes.get('INSTRUME', '') or '').strip(),
             'focale': cartes.get('FOCALLEN') or cartes.get('FOCAL'), 'observateur': str(cartes.get('OBSERVER', '')
                                                                                          or '').strip()}
        with self._verrou:
            self.entetes[chemin] = r
            etat.ecrire_json(self.ident, 'entetes.json', self.entetes)
        self._appliquer_entetes()
        return r

    def entetes_lieux(self) -> dict:
        """{chemin: {'lat', 'lon', 'alt_m', 'instant', 'milieu'}} avec des datetime (pour paires et contrôles)."""
        import datetime as D
        out = {}
        for c, e in self.entetes.items():
            d = dict(e)
            for k in ('instant', 'milieu'):
                if d.get(k):
                    try:
                        d[k] = D.datetime.fromisoformat(d[k])
                    except ValueError:
                        d[k] = None
            out[c] = d
        return out

    def _appliquer_entetes(self):
        if self.structure is None:
            return
        import datetime as D
        for f in self.structure.fichiers:
            e = self.entetes.get(f.chemin)
            if e and e.get('milieu'):
                try:
                    f.instant = D.datetime.fromisoformat(e['milieu'])
                    f.instant_source = 'entete'
                    f.doute = False
                except ValueError:
                    pass

    # ------------------------------------------------------------------ tableaux
    def lire_tableau(self, chemin: str) -> tuple:
        """(Classeur, [Tableau de mesures contrôlés]) d'un .xlsx/.csv du partage."""
        donnees = self.client.lire(chemin, max_octets=TAILLE_MAX_TABLEAU)
        (self.dossier / 'tableaux').mkdir(exist_ok=True)
        classeur = tableur.lire(donnees, chemin)
        mesures = []
        noms = {S.normaliser(f.nom): f.chemin for f in (self.structure.fichiers if self.structure else [])}
        ent = {os.path.basename(c): v for c, v in self.entetes_lieux().items()}
        for fe in classeur.feuilles:
            if est_tableau_de_mesures(fe):
                t = lire_tableau(fe)
                controler(t, noms if noms else None, ent)
                mesures.append(t)
        self.tableaux[chemin] = (classeur, mesures)
        return classeur, mesures

    def tableaux_de_mesures(self) -> list:
        return [t for _, ts in self.tableaux.values() for t in ts]


def analyser_cartes(octets: bytes) -> dict:
    """Cartes d'un en-tête FITS brut → {mot-clé: valeur} (texte, nombre, booléen) ; tolère les cartes non standard."""
    out = {}
    for i in range(0, len(octets) - 79, 80):
        c = octets[i:i + 80].decode('ascii', 'replace')
        cle = c[:8].strip()
        if cle == 'END':
            break
        if c[8:10] != '= ' or not cle:
            continue
        v = c[10:]
        v = v.strip()
        if v.startswith("'"):
            fin = v.find("'", 1)
            while fin != -1 and v[fin + 1:fin + 2] == "'":
                fin = v.find("'", fin + 2)
            out[cle] = v[1:fin if fin != -1 else None].replace("''", "'").rstrip()
            continue
        v = v.split('/')[0].strip()
        if v in ('T', 'F'):
            out[cle] = v == 'T'
            continue
        try:
            out[cle] = int(v)
        except ValueError:
            try:
                out[cle] = float(v.replace('D', 'E'))
            except ValueError:
                out[cle] = v
    return out
