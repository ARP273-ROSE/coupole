# Contribuer à Coupole · Contributing to Coupole

**Français** · [English](#english)

## Écrire un module

Un module est un paquet Python qui contient un `manifest.json`. Il est découvert automatiquement, de trois façons :

1. livré avec Coupole : un dossier dans `coupole/modules/` ;
2. installé à part : un paquet qui déclare le point d'entrée `coupole.modules` dans son `pyproject.toml`
   (`[project.entry-points."coupole.modules"]` puis `mon_module = "mon_paquet"`) ;
3. déposé à la main : un dossier dans le sous-dossier `modules/` des réglages (`~/.config/coupole/modules/` sous
   Linux, `~/Library/Application Support/Coupole/modules/` sous macOS, `%LOCALAPPDATA%\Coupole\modules\` sous Windows).

Un module défectueux est écarté avec un message (`coupole modules`) ; il n'empêche jamais l'application de démarrer.

### Le manifeste

```json
{
  "id": "parallaxe",
  "version": "0.1.0",
  "nom": {"fr": "Parallaxe Terre-Lune", "en": "Earth-Moon parallax"},
  "description": {"fr": "…", "en": "…"},
  "icone": "icone.svg",
  "ordre": 50,
  "textes": "textes:TEXTES",
  "gui": "gui:Panneau",
  "cli": "cli:enregistrer",
  "coupole_min": "0.1.0"
}
```

`nom` doit exister en français **et** en anglais. `gui` et `cli` sont facultatifs (un module peut n'avoir qu'une
ligne de commande).

### Les textes : tout passe par `tr()`

```python
# textes.py
TEXTES = {
    'par_titre': {'fr': 'Parallaxe', 'en': 'Parallax'},
    'par_calculer': {'fr': 'Calculer', 'en': 'Compute'},
    'par_calculer_aide': {'fr': 'Calcule la distance…', 'en': 'Computes the distance…'},
}
```

Préfixer les clés par l'identifiant du module. Aucune chaîne visible en dur : le test
`tests/test_traductions.py` échoue sinon. Chaque widget interactif a une info-bulle (clé `<clé>_aide`) : les
fabriques `bouton()`, `case()`, `liste()`, `champ()` de `coupole.gui.outils` l'imposent, et
`tests/test_interface.py` le vérifie dans les deux langues.

### L'interface

```python
# gui.py
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from ...core.i18n import tr          # module livré ; module externe : from coupole.core.i18n import tr
from ...gui.outils import Tache, bouton

class Panneau(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.addWidget(bouton('par_calculer', self.calculer))

    def calculer(self):
        t = Tache(fonction_longue, 42)        # jamais de travail long dans le fil graphique
        t.fini.connect(self.afficher)
        t.start()

    def aide_html(self):                      # F1 : aide de l'écran
        return tr('par_aide_html')

    def occupe(self):                         # facultatif : empêche de quitter en plein travail
        return False
```

Un panneau peut en ouvrir un autre : `self.window().ouvrir_module('cosmo')` rend le panneau du module (ou `None`),
par exemple pour lui passer une valeur (`recevoir_redshift(z, nom)` du module Cosmologie).

### La ligne de commande

```python
# cli.py
from ...core.i18n import tr

def enregistrer(p):                          # p : sous-parseur argparse « coupole <id> »
    p.add_argument('--distance', type=float, help=tr('par_aide_distance'))
    p.set_defaults(fonction=lambda a: print(a.distance) or 0)
```

### Ce que le cœur fournit

| Module | Pour |
|---|---|
| `coupole.core.i18n` | `tr()`, langue courante |
| `coupole.core.config` | dossiers (réglages, cache), réglages persistants |
| `coupole.core.machine`, `parallele` | matériel détecté, nombre de processus et de téléchargements |
| `coupole.core.calcul` | `tableaux(preferer_gpu=True)` : CuPy si possible, sinon numpy |
| `coupole.core.reseau` | téléchargement poli (User-Agent, débit plafonné, reprise, annulation), requête TAP |
| `coupole.core.sources` | adresses des services (jamais en dur) |
| `coupole.core.enligne`, `simbad` | fiche d'un objet (SIMBAD, Sesame, JPL SBDB) avec cache daté et repli hors ligne ; redshift par nom |
| `coupole.gui.fiche` | widget « Fiche en ligne » prêt à l'emploi (`FicheEnLigne.demander(nom, cat)`) |
| `coupole.core.temps`, `sites` | temps en UTC, heure locale du site, date du soir, hauteur du Soleil, base des sites |
| `coupole.core.xisf` | écrire et relire un XISF |
| `coupole.core.donnees` | lecture générique (images, spectres, séries, tables) |
| `coupole.core.astap` | détection et lancement d'ASTAP |
| `coupole.core.rapports` | rapports d'incident (avec consentement) |

## Ajouter un format de données

```python
from coupole.core import donnees

def lire_rad(chemin):
    """Exemple : fichier texte à deux colonnes fréquence (MHz) / intensité."""
    import numpy as np
    f, y = np.loadtxt(chemin, unpack=True)
    return [donnees.Donnee('spectre', 'rad', str(chemin), x=f, y=y, nom_x='freq', unite_x='MHz',
                           nom_y='Ta', unite_y='K', meta={'axe': 'freq', 'specsys': '', 'restfreq_hz': None})]

donnees.enregistrer_lecteur(('.rad',), lire_rad, 'Mon format')
```

Appeler `enregistrer_lecteur` à l'import du module (par exemple dans `textes.py` ou `__init__.py`). Ne rien
supposer qui ne soit écrit dans le fichier : un axe sans unité reste sans unité, une vitesse se calcule seulement
avec une fréquence de repos connue.

## Règles du dépôt

- Python 3.10+, dépendances légères ; tout ce qui est facultatif (ASTAP, SEP, CuPy) doit pouvoir manquer.
- `pytest` doit passer (`pip install ".[test]"` puis `python -m pytest`).
- Version : uniquement dans `VERSION`. Historique : `CHANGELOG.md` (français) et `CHANGELOG.en.md`.

---

<a id="english"></a>
## English

### Writing a module

A module is a Python package containing a `manifest.json`, discovered automatically: shipped in
`coupole/modules/`, installed separately with a `coupole.modules` entry point, or dropped into the `modules/` folder
of the settings directory. A broken module is skipped with a message and never prevents startup.

The manifest gives `id`, `version`, `nom` (French **and** English names), `description`, `icone`, `ordre`, and
optional `textes`, `gui` (a `QWidget` class), `cli` (a function receiving the argparse sub-parser) and `coupole_min`
(see the example above).

Every visible string goes through `tr()` with keys declared in the module's `TEXTES` dictionary (French and English);
every interactive widget has a tooltip (`<key>_aide`). `tests/test_traductions.py` and `tests/test_interface.py`
enforce both. Long work never runs on the GUI thread (`coupole.gui.outils.Tache`). A panel may provide
`aide_html()` (F1 help) and `occupe()`.

The core provides i18n, settings and folders, hardware detection and parallelism planning, an optional GPU array API
(CuPy or numpy), polite networking (User-Agent, rate cap, resume, cancellation, TAP), configurable service addresses,
online object records (SIMBAD, Sesame, JPL SBDB: `coupole.core.enligne`, widget `coupole.gui.fiche`, dated
cache, offline fallback), UTC/local time and sites, XISF reading/writing, generic data reading, ASTAP detection and consented incident reports.

### Adding a data format

Write a reader returning a list of `coupole.core.donnees.Donnee` and register it with
`donnees.enregistrer_lecteur(extensions, function, name)` (see the example above). Assume nothing that the file does
not state.

### Repository rules

Python 3.10+, light dependencies, optional components may be missing; `pytest` must pass; the version lives only in
`VERSION`; history in `CHANGELOG.md` (French) and `CHANGELOG.en.md`.
