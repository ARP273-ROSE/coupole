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
import os
import sys
import tempfile
import threading
import uuid
from pathlib import Path

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
}

_verrou = threading.Lock()


class Reglages:
    """Réglages lus et écrits de façon atomique (fichier temporaire + remplacement)."""

    def __init__(self, chemin: Path | None = None):
        self.chemin = chemin or dossier_config() / 'reglages.json'
        self.valeurs = dict(DEFAUTS)
        try:
            self.valeurs.update(json.loads(self.chemin.read_text(encoding='utf-8')))
        except Exception:
            pass
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

    def enregistrer(self):
        with _verrou:
            try:
                self.chemin.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp = tempfile.mkstemp(dir=str(self.chemin.parent), suffix='.tmp')
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self.valeurs, f, indent=2, ensure_ascii=False)
                os.replace(tmp, self.chemin)
            except OSError:
                pass


_reglages: Reglages | None = None


def reglages() -> Reglages:
    global _reglages
    if _reglages is None:
        _reglages = Reglages()
    return _reglages


def reinitialiser_pour_tests():
    global _reglages
    _reglages = None
