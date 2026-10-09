"""État de l'interface conservé d'une fermeture à l'autre : ``interface.json`` (dossier des réglages).

Ce fichier garde la DISPOSITION et ce que l'on regardait — fenêtre (taille, position, écran, maximisée), taille
des dialogues, séparateurs, colonnes (largeur, ordre, tri), module et onglet actifs, filtres et recherche,
dossiers où s'ouvre chaque dialogue de fichiers, fichiers récents, paramètres des calculs.  Les choix de
traitement (dossier de sortie, format, options du traitement, ASTAP…) restent dans ``reglages.json``.

Règles :
* lecture tolérante : clé absente, type faux, valeur hors bornes → la valeur par défaut, jamais d'exception ; un
  fichier illisible est mis de côté (``interface.json.corrompu-<date>``) et l'interface repart de zéro ;
* écriture atomique (fichier temporaire + remplacement), et seulement si quelque chose a changé ; c'est
  l'interface (``gui/memoire.py``) qui la déclenche, au plus une fois toutes les 2 s et à la fermeture ;
* rien de ce qui serait dangereux à rejouer n'est gardé (un traitement en cours n'est jamais relancé seul) ;
* versionné (``version``) : un fichier d'une version plus récente de Coupole est ignoré, pas mal interprété ;
* l'existence des chemins gardés est vérifiée dans un fil de fond (un partage réseau absent ne bloque jamais
  le démarrage) : tant qu'elle n'est pas connue, un dialogue s'ouvre au dossier par défaut.

« Réinitialiser la disposition » (Préférences) et ``coupole --reinitialiser-interface`` effacent ce fichier.
"""
from __future__ import annotations

import copy
import logging
import math
import os
import threading
from pathlib import Path

from .config import dossier_config, ecrire_json_atomique, lire_json_protege

log = logging.getLogger(__name__)

VERSION = 1
NOM_FICHIER = 'interface.json'
MAX_RECENTS = 10
LONGUEUR_MAX_TEXTE = 4096          # un champ ne garde jamais plus (fichier collé par erreur, etc.)

_verrou = threading.Lock()


def _normaliser(valeur):
    """Copie « JSON » de la valeur (tuples → listes ; flottants non finis refusés) ; ValueError sinon."""
    def propre(v):
        if isinstance(v, float) and not math.isfinite(v):
            raise ValueError('non-finite float')
        if isinstance(v, (list, tuple)):
            return [propre(x) for x in v]
        if isinstance(v, dict):
            return {str(k): propre(x) for k, x in v.items()}
        if v is None or isinstance(v, (bool, int, float, str)):
            return v
        raise ValueError('not JSON: %s' % type(v).__name__)
    return propre(valeur)


def type_correct(valeur, types) -> bool:
    """isinstance, sauf qu'un booléen n'est pas un nombre (True n'est pas une largeur de colonne)."""
    if types is None:
        return True
    if not isinstance(types, tuple):
        types = (types,)
    if isinstance(valeur, bool) and bool not in types:
        return False
    if isinstance(valeur, int) and not isinstance(valeur, bool) and float in types and int not in types:
        return True                    # 3 vaut 3.0
    return isinstance(valeur, types)


class EtatInterface:
    def __init__(self, chemin: Path | None = None):
        self.chemin = Path(chemin) if chemin else dossier_config() / NOM_FICHIER
        self.ecritures = 0             # écritures sur disque (tests du budget : aucune pendant la frappe)
        self.quand_modifie = None      # rappel () : l'interface programme une écriture différée
        self.existence: dict[str, bool] = {}     # chemin → existe (rempli par le fil de vérification)
        self._sale = False
        existait = self.chemin.exists()
        lu = lire_json_protege(self.chemin, None)
        self.restaure = existait and lu is None    # fichier présent mais illisible : mis de côté
        self.donnees = self._valider(lu)

    @staticmethod
    def _valider(lu):
        if not isinstance(lu, dict):
            return {'version': VERSION}
        v = lu.get('version')
        if not type_correct(v, int) or v < 1 or v > VERSION:
            # version inconnue (fichier d'une version plus récente de Coupole) : on repart de zéro sans deviner
            log.warning('interface.json version %r ignored', v)
            return {'version': VERSION}
        lu['version'] = VERSION
        return lu

    # ---------------------------------------------------------------- lecture tolérante
    def _noeud(self, cle: str, creer=False):
        parties = cle.split('.')
        d = self.donnees
        for p in parties[:-1]:
            suivant = d.get(p)
            if not isinstance(suivant, dict):
                if not creer:
                    return None, parties[-1]
                suivant = d[p] = {}
            d = suivant
        return d, parties[-1]

    def lire(self, cle: str, defaut=None, types=None, valider=None):
        """Valeur de `cle` (« a.b.c ») ; `defaut` si absente, d'un autre type que `types`, ou refusée par
        `valider(v)` (qui peut aussi lever : c'est un refus)."""
        d, nom = self._noeud(cle)
        if d is None or nom not in d:
            return defaut
        v = d[nom]
        if not type_correct(v, types):
            return defaut
        if valider is not None:
            try:
                if not valider(v):
                    return defaut
            except Exception:
                return defaut
        return copy.deepcopy(v)

    def lire_entier(self, cle, defaut, mini=None, maxi=None):
        v = self.lire(cle, None, int)
        if v is None:
            return defaut
        if mini is not None and v < mini or maxi is not None and v > maxi:
            return defaut
        return v

    def lire_texte(self, cle, defaut=''):
        v = self.lire(cle, None, str)
        return defaut if v is None else v[:LONGUEUR_MAX_TEXTE]

    # ---------------------------------------------------------------- écriture (en mémoire)
    def ecrire(self, cle: str, valeur) -> bool:
        """Change une valeur EN MÉMOIRE ; rend True si elle a changé (l'écriture disque suivra, différée)."""
        try:
            valeur = _normaliser(valeur)
        except ValueError as e:
            log.debug('interface %s not kept: %s', cle, e)
            return False
        if isinstance(valeur, str) and len(valeur) > LONGUEUR_MAX_TEXTE:
            valeur = valeur[:LONGUEUR_MAX_TEXTE]
        d, nom = self._noeud(cle, creer=True)
        if nom in d and d[nom] == valeur and type(d[nom]) is type(valeur):
            return False
        d[nom] = valeur
        self._marquer()
        return True

    def effacer(self, cle: str) -> bool:
        d, nom = self._noeud(cle)
        if d is None or nom not in d:
            return False
        del d[nom]
        self._marquer()
        return True

    def _marquer(self):
        self._sale = True
        if self.quand_modifie is not None:
            try:
                self.quand_modifie()
            except Exception:                      # l'interface a disparu : l'écriture se fera à la fermeture
                pass

    @property
    def modifie(self) -> bool:
        return self._sale

    def enregistrer(self) -> bool:
        """Écrit le fichier (atomique) s'il y a du nouveau ; rend True si une écriture a eu lieu."""
        with _verrou:
            if not self._sale:
                return False
            try:
                ecrire_json_atomique(self.chemin, self.donnees, indent=1)
            except OSError as e:                   # disque plein, dossier en lecture seule : on continue
                log.warning('interface state not saved: %s', e)
                return False
            self._sale = False
            self.ecritures += 1
            return True

    def reinitialiser(self) -> bool:
        """Oublie toute la disposition (fichier effacé) ; rend True si un fichier existait."""
        with _verrou:
            self.donnees = {'version': VERSION}
            self._sale = False
            try:
                self.chemin.unlink()
                return True
            except FileNotFoundError:
                return False
            except OSError as e:
                log.warning('interface state not removed: %s', e)
                return False

    # ---------------------------------------------------------------- dossiers des dialogues, fichiers récents
    def dossier(self, cle: str, defaut: str = '') -> str:
        """Dossier où rouvrir le dialogue `cle` : le dernier utilisé s'il existe (vérifié en fond), sinon `defaut`.
        Tant que la vérification n'a pas répondu (partage réseau lent), `defaut` : jamais d'attente."""
        v = self.lire_texte('dossiers.' + cle, '')
        if v and self.existence.get(v) is True:
            return v
        return defaut

    def retenir_dossier(self, cle: str, chemin: str, est_fichier: bool = False):
        """Retient le dossier d'un chemin choisi dans un dialogue (le dossier parent pour un fichier)."""
        if not chemin:
            return
        d = os.path.dirname(chemin) if est_fichier else chemin
        d = os.path.abspath(os.path.expanduser(d))
        self.existence[d] = True                   # on vient de le choisir : il existe
        self.ecrire('dossiers.' + cle, d)

    def recents(self, cle: str) -> list[str]:
        v = self.lire('recents.' + cle, [], list)
        return [x[:LONGUEUR_MAX_TEXTE] for x in v if isinstance(x, str) and x][:MAX_RECENTS]

    def ajouter_recent(self, cle: str, chemin: str):
        chemin = os.path.abspath(os.path.expanduser(chemin))
        cle_norm = os.path.normcase(chemin)
        liste = [chemin] + [x for x in self.recents(cle) if os.path.normcase(x) != cle_norm]
        self.existence[chemin] = True
        self.ecrire('recents.' + cle, liste[:MAX_RECENTS])

    def chemins_connus(self) -> list[str]:
        """Tous les chemins gardés (dossiers des dialogues, fichiers récents, dossiers analysés)."""
        out = []
        dossiers = self.lire('dossiers', {}, dict)
        out += [v for v in dossiers.values() if isinstance(v, str) and v]
        for liste in self.lire('recents', {}, dict).values():
            if isinstance(liste, list):
                out += [x for x in liste if isinstance(x, str) and x]
        q = self.lire_texte('modules.qualite.dossier', '')
        if q:
            out.append(q)
        return list(dict.fromkeys(out))

    def verifier_existence_en_fond(self, rappel=None) -> threading.Thread:
        """Vérifie dans un fil de fond (démon : il ne retient jamais la fermeture) que les chemins gardés existent.
        Un partage réseau injoignable peut y bloquer des dizaines de secondes : l'interface n'attend pas."""
        chemins = self.chemins_connus()

        def verifier():
            for c in chemins:
                try:
                    self.existence[c] = os.path.exists(c)
                except (OSError, ValueError):
                    self.existence[c] = False
            if rappel is not None:
                try:
                    rappel()
                except Exception:
                    pass
        t = threading.Thread(target=verifier, name='coupole-chemins', daemon=True)
        t.start()
        return t


_etat: EtatInterface | None = None


def etat() -> EtatInterface:
    global _etat
    if _etat is None:
        _etat = EtatInterface()
    return _etat


def reinitialiser_pour_tests():
    global _etat
    _etat = None


def effacer_fichier() -> bool:
    """`coupole --reinitialiser-interface` : efface interface.json (la disposition d'origine reviendra)."""
    if _etat is not None:
        return _etat.reinitialiser()
    chemin = dossier_config() / NOM_FICHIER
    try:
        chemin.unlink()
        return True
    except FileNotFoundError:
        return False

