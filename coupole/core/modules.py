"""Découverte des modules.

Un module est un paquet Python qui contient un ``manifest.json`` :

    {
      "id": "ohp",                         identifiant court (sous-commande CLI)
      "version": "1.0.0",
      "nom": {"fr": "...", "en": "..."},
      "description": {"fr": "...", "en": "..."},
      "icone": "icone.svg",                fichier dans le paquet du module
      "ordre": 10,                         position dans la barre latérale
      "textes": "textes:TEXTES",           traductions du module
      "gui": "gui:Panneau",                classe QWidget (facultatif)
      "cli": "cli:enregistrer",            fonction(sous_parseur) (facultatif)
      "coupole_min": "0.1.0"               version minimale de Coupole
    }

Trois sources, dans cet ordre :
  1. les modules livrés, sous ``coupole/modules/`` ;
  2. les paquets installés qui déclarent le point d'entrée ``coupole.modules``
     (``pip install coupole-mon-module``) ;
  3. le dossier ``modules/`` des réglages de l'utilisateur (copier un dossier
     suffit, sans rien installer).
Un module défectueux est écarté avec un message ; il n'empêche jamais
l'application de démarrer.
"""
from __future__ import annotations

import importlib
import json
import logging
import pkgutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import i18n
from .config import dossier_config

log = logging.getLogger(__name__)


@dataclass
class Module:
    id: str
    version: str
    nom: dict
    description: dict
    paquet: str
    dossier: Path
    icone: str = ''
    ordre: int = 100
    gui: str = ''
    cli: str = ''
    origine: str = 'livre'
    textes: str = ''
    extra: dict = field(default_factory=dict)

    def nom_local(self) -> str:
        return self.nom.get(i18n.langue()) or self.nom.get('en') or self.id

    def description_locale(self) -> str:
        return self.description.get(i18n.langue()) or self.description.get('en') or ''

    def chemin_icone(self) -> Path | None:
        return (self.dossier / self.icone) if self.icone else None

    def _charger(self, ref: str):
        mod, _, attr = ref.partition(':')
        m = importlib.import_module('%s.%s' % (self.paquet, mod))
        return getattr(m, attr)

    def classe_gui(self):
        return self._charger(self.gui) if self.gui else None

    def fonction_cli(self):
        return self._charger(self.cli) if self.cli else None


def _version_tuple(v: str):
    return tuple(int(x) if x.isdigit() else 0 for x in (v or '0').split('.'))


def lire_manifeste(paquet: str, origine: str) -> Module:
    m = importlib.import_module(paquet)
    dossier = Path(m.__file__).resolve().parent
    data = json.loads((dossier / 'manifest.json').read_text(encoding='utf-8'))
    for cle in ('id', 'version', 'nom'):
        if cle not in data:
            raise ValueError('manifest.json: missing "%s"' % cle)
    for lg in i18n.LANGUES:
        if not data['nom'].get(lg):
            raise ValueError('manifest.json: name missing for language "%s"' % lg)
    mod = Module(id=data['id'], version=data['version'], nom=data['nom'],
                 description=data.get('description', {}), paquet=paquet, dossier=dossier,
                 icone=data.get('icone', ''), ordre=int(data.get('ordre', 100)), gui=data.get('gui', ''),
                 cli=data.get('cli', ''), origine=origine, textes=data.get('textes', ''), extra=data)
    from .. import __version__
    if _version_tuple(__version__) < _version_tuple(data.get('coupole_min', '0')):
        raise ValueError('needs Coupole >= %s' % data['coupole_min'])
    if mod.textes:
        i18n.enregistrer(mod._charger(mod.textes))
    return mod


_modules: list[Module] | None = None
erreurs: list[tuple[str, str]] = []


def decouvrir(recharger: bool = False) -> list[Module]:
    global _modules
    if _modules is not None and not recharger:
        return _modules
    erreurs.clear()
    trouves: dict[str, Module] = {}
    candidats: list[tuple[str, str]] = []
    from .. import modules as _livres
    for info in pkgutil.iter_modules(_livres.__path__):
        if info.ispkg:
            candidats.append(('coupole.modules.' + info.name, 'livre'))
    try:
        from importlib.metadata import entry_points
        for ep in entry_points(group='coupole.modules'):
            candidats.append((ep.value.split(':')[0], 'installe'))
    except Exception as e:  # pragma: no cover
        log.warning('entry points: %s', e)
    perso = dossier_config() / 'modules'
    if perso.is_dir():
        if str(perso) not in sys.path:
            sys.path.insert(0, str(perso))
        for d in sorted(perso.iterdir()):
            if (d / 'manifest.json').exists() and (d / '__init__.py').exists():
                candidats.append((d.name, 'utilisateur'))
    for paquet, origine in candidats:
        try:
            mod = lire_manifeste(paquet, origine)
            if mod.id in trouves:
                raise ValueError('duplicate module id "%s"' % mod.id)
            trouves[mod.id] = mod
        except Exception as e:
            erreurs.append((paquet, '%s: %s' % (type(e).__name__, e)))
            log.warning('module %s ignored: %s', paquet, e)
    _modules = sorted(trouves.values(), key=lambda m: (m.ordre, m.id))
    return _modules
