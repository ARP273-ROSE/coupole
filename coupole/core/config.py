"""Dossiers de l'application et réglages persistants (JSON).

Les données de l'utilisateur ne vivent jamais dans le dossier d'installation :
elles survivent ainsi aux mises à jour et aux réinstallations.

  Windows : %LOCALAPPDATA%\\Coupole            (réglages, cache, journaux)
  macOS   : ~/Library/Application Support/Coupole
  Linux   : $XDG_CONFIG_HOME/coupole (réglages) ; $XDG_CACHE_HOME/coupole (cache)

La variable d'environnement COUPOLE_HOME remplace tout (tests, installations
portables).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

log = logging.getLogger(__name__)

NOM = 'Coupole'
NOM_TECHNIQUE = 'coupole'


def _base() -> tuple[Path, Path]:
    force = os.environ.get('COUPOLE_HOME')
    if force:
        p = Path(force)
        return p, p / 'cache'
    if sys.platform == 'win32':
        b = Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local') / NOM
        return b, b / 'cache'
    if sys.platform == 'darwin':
        b = Path.home() / 'Library' / 'Application Support' / NOM
        return b, Path.home() / 'Library' / 'Caches' / NOM
    conf = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / NOM_TECHNIQUE
    cache = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / NOM_TECHNIQUE
    return conf, cache


def dossier_config() -> Path:
    p = _base()[0]
    p.mkdir(parents=True, exist_ok=True)
    return p


def dossier_cache() -> Path:
    p = _base()[1]
    p.mkdir(parents=True, exist_ok=True)
    return p


def dossier_sortie_defaut() -> Path:
    """Dossier proposé pour les images : ~/Coupole (visible, facile à retrouver)."""
    return Path.home() / NOM


DEFAUTS = {
    'langue': 'auto',
    'rapports_autorises': None,        # None : question pas encore posée
    'id_installation': None,           # identifiant aléatoire, sans lien avec la personne
    'astap_executable': '',
    'astap_catalogue': '',
    'telechargements_max': 0,          # 0 : automatique
    'conversions_max': 0,              # 0 : automatique
    'debit_max_mo_s': 8.0,             # plafond de débit vers le serveur public
    'mode_econome': False,
    'dossier_sortie': '',
    'format_sortie': 'xisf',
    'langue_noms': 'auto',             # langue des noms de dossiers et d'objets
    'maj_auto': True,
    'apparence': 'sombre',             # thème de Coupole (sombre par défaut, ou clair), indépendant de celui du système
    'dialogues_fichiers': 'systeme',   # systeme : explorateur du système (portail XDG sous Linux) ; qt : dialogue de Qt
    'pixinsight_instance': 'nouvelle', # PixInsight déjà ouvert : nouvelle (-n, sûr) | envoyer (céder à l'instance)
    'services_en_ligne': True,         # fiches SIMBAD / JPL et redshift par nom (une requête par objet, cache)
    'ohp_verifier_nouveautes': True,   # Banque OHP : comparer l'inventaire TAP à la copie locale au démarrage
    'ohp_nouveautes_heures': 24,       # au plus une vérification par ce nombre d'heures
    'ohp_derniere_verification': '',   # ISO UTC de la dernière vérification des nouveautés
    # options de l'onglet Traitement (Banque OHP), gardées dès qu'elles changent (0.1.6)
    'ohp_garder_doublons': False,
    'ohp_garder_fits': False,
    'ohp_mode_astap': 'tous',          # tous | suspectes | jamais
    'ohp_verifier_qualite': False,
}

_verrou = threading.Lock()


def ecrire_atomique(chemin, texte: str, encodage: str = 'utf-8') -> None:
    """Écrit `texte` dans un fichier temporaire du même dossier puis le substitue d'un coup (os.replace) :
    une coupure de courant, un disque plein ou un plantage ne laissent jamais de fichier à moitié écrit."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(chemin.parent), prefix='.' + chemin.name + '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding=encodage, newline='') as f:
            f.write(texte)
        os.replace(tmp, chemin)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def ecrire_json_atomique(chemin, objet, indent: int | None = 1) -> None:
    ecrire_atomique(chemin, json.dumps(objet, ensure_ascii=False, indent=indent))


def lire_json_protege(chemin, defaut=None, attendu=dict):
    """Lit un JSON ; s'il est illisible ou n'a pas le type attendu, le met de côté (`.corrompu-<date>`) et
    rend `defaut`.  Un fichier absent rend `defaut` sans rien faire."""
    chemin = Path(chemin)
    try:
        texte = chemin.read_text(encoding='utf-8')
    except FileNotFoundError:
        return defaut
    except OSError as e:
        log.warning('%s unreadable: %s', chemin.name, e)
        return defaut
    try:
        doc = json.loads(texte)
        if attendu is not None and not isinstance(doc, attendu):
            raise ValueError('not a %s' % attendu.__name__)
        return doc
    except ValueError as e:
        copie = chemin.with_name('%s.corrompu-%s' % (chemin.name, time.strftime('%Y%m%d-%H%M%S')))
        k = 1
        while copie.exists():                                   # deux fichiers abîmés dans la même seconde
            k += 1
            copie = chemin.with_name('%s.corrompu-%s-%d' % (chemin.name, time.strftime('%Y%m%d-%H%M%S'), k))
        try:
            os.replace(chemin, copie)
            log.warning('%s corrupt (%s): kept as %s, defaults restored', chemin.name, e, copie.name)
        except OSError:
            pass
        return defaut


class Reglages:
    """Réglages lus et écrits de façon atomique (fichier temporaire + remplacement).

    Un fichier corrompu (JSON invalide, ou qui n'est pas un objet) est mis de côté sous
    ``reglages.json.corrompu-<date>`` et les valeurs par défaut reprennent : l'application démarre toujours.
    """

    def __init__(self, chemin: Path | None = None):
        self.chemin = chemin or dossier_config() / 'reglages.json'
        self.valeurs = dict(DEFAUTS)
        self.ecritures = 0                 # écritures sur disque (tests du budget d'écriture)
        self.quand_modifie = None          # rappel () d'une valeur différée : l'interface programme l'écriture
        self._sale = False
        existait = self.chemin.exists()
        lu = lire_json_protege(self.chemin, None)
        self.valeurs.update(lu or {})
        self.restaure = existait and lu is None            # fichier présent mais illisible : mis de côté
        if not self.valeurs.get('id_installation'):
            self.valeurs['id_installation'] = uuid.uuid4().hex[:12]
            self.enregistrer()

    def __getitem__(self, cle):
        return self.valeurs.get(cle, DEFAUTS.get(cle))

    def __setitem__(self, cle, valeur):
        self.valeurs[cle] = valeur
        self.enregistrer()

    def get(self, cle, defaut=None):
        return self.valeurs.get(cle, defaut)

    def lire(self, cle, types):
        """Valeur de `cle` si elle a le type attendu, sinon la valeur par défaut (fichier modifié à la main,
        ancienne version) : jamais d'exception."""
        v = self.valeurs.get(cle, DEFAUTS.get(cle))
        if not isinstance(types, tuple):
            types = (types,)
        if isinstance(v, bool) and bool not in types or not isinstance(v, types):
            return DEFAUTS.get(cle)
        return v

    def differer(self, cle, valeur):
        """Change une valeur EN MÉMOIRE ; l'écriture sur disque est groupée et différée (au plus toutes les 2 s,
        et à la fermeture) par l'interface : une frappe dans un champ n'écrit jamais le fichier."""
        if cle in self.valeurs and self.valeurs[cle] == valeur and type(self.valeurs[cle]) is type(valeur):
            return
        self.valeurs[cle] = valeur
        self._sale = True
        if self.quand_modifie is not None:
            try:
                self.quand_modifie()
            except Exception:
                pass

    def enregistrer_si_modifie(self) -> bool:
        if not self._sale:
            return False
        self.enregistrer()
        return True

    def enregistrer(self):
        with _verrou:
            try:
                ecrire_json_atomique(self.chemin, self.valeurs, indent=2)
                self._sale = False
                self.ecritures += 1
            except OSError as e:                       # disque plein, dossier en lecture seule : on continue
                log.warning('settings not saved: %s', e)


_reglages: Reglages | None = None


def reglages() -> Reglages:
    global _reglages
    if _reglages is None:
        _reglages = Reglages()
    return _reglages


def reinitialiser_pour_tests():
    global _reglages
    _reglages = None
