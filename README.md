<p align="center"><img src="logo/coupole_256.png" width="128" alt="Coupole"></p>

# Coupole

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/ARP273-ROSE/coupole/releases/latest)
[![Version](https://img.shields.io/github/v/release/ARP273-ROSE/coupole?label=version)](https://github.com/ARP273-ROSE/coupole/releases/latest)
[![Tests](https://github.com/ARP273-ROSE/coupole/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/ARP273-ROSE/coupole/actions/workflows/tests.yml)
[![Langue / Language](https://img.shields.io/badge/langue-FR%20%7C%20EN-informational.svg)](#english)

**Français** · [English](#english)

Boîte à outils **libre** (GPL-3.0) pour les étudiants du DU « Explorer et Comprendre l'Univers » (DU ECU) de
l'Observatoire de Paris. Python 3.10+, interface graphique PyQt6 **et** ligne de commande complète, en français et en
anglais, sur Windows, macOS et Linux. Architecture **modulaire** : d'autres modules viendront au fil de l'année
(simulateurs, exercices, radioastronomie...).

| Module | Ce qu'il fait |
|---|---|
| **Banque OHP** | Récupère la banque d'images « OHP student observations » (T120 et IRIS, 7 989 images, 78 Go) par le service TAP public de l'Observatoire ; catalogue des 166 objets ; téléchargement avec reprise ; doublons écartés (et expliqués) ; solution astrométrique contrôlée (ASTAP facultatif) ; en-têtes corrigés avec traçabilité ; conversion **XISF** (PixInsight), **FITS compressé sans perte** (`.fits.fz` : Siril, astropy) ou FITS float32 ; tri en **lots empilables** avec fiche `LOT.txt` ; carte du ciel ; rapport d'anomalies ; **fiche en ligne** facultative (SIMBAD, JPL, liens Aladin et NED). |
| **Archives des observatoires** (0.2.0) | Images publiques des grands observatoires et des sondes, actuelles et passées : **Hubble, JWST, GALEX** (MAST), **ESO** (produits Phase 3), **Spitzer, WISE, 2MASS** (IRSA), **NOIRLab** (DECam…), **Keck** (KOA, poses brutes), **SDSS**, **Voyager et Cassini** (OPUS, PDS), **Juno** (JunoCam, PDS). Recherche par nom ou coordonnées (ou par corps pour les sondes), produits finaux et données publiques par défaut, **volume estimé avant téléchargement** et confirmation au-delà d'un seuil, débit plafonné et reprise ; extraction de l'image scientifique (WCS, unités, NaN masqués, crédit dans l'en-tête), XISF ou FITS ; conversion PDS3/VICAR/PDS4 ; **alignement** par l'astrométrie sur une grille commune et **composition couleur** dans l'ordre des longueurs d'onde (aperçu, PixelMath). Gemini (compte exigé) et SMOKA (formulaire web) signalés. Méthode et sources : [docs/archives_methode.md](docs/archives_methode.md). |
| **Qualité des images** | Facultatif : FWHM, ellipticité (carte 3 × 3), fond, bruit, gradient, saturation, traînées, échantillonnage — mesures validées sur images synthétiques. |
| **Spectres et séries** | Lecture et tracé de données 1D (spectres H I à 21 cm avec axe fréquence ↔ vitesse radio, courbes de lumière, tables FITS ou CSV). |
| **Cosmologie** | Du redshift aux distances (comobile, luminosité, angulaire, trajet de la lumière), âges, volume comobile, module de distance, échelle en kpc/″ ; Planck 2018 avec incertitudes, SH0ES, Planck 2015, WMAP 9, jeu personnalisé ; redshift d'un objet demandé à SIMBAD ; courbes, export CSV. Noyau repris du calculateur [cosmologie-redshift](https://github.com/ARP273-ROSE/cosmologie-redshift), vérifié sous SageMath. |
| **Sites et heures** | Sites d'observation (MPC), carte OpenStreetMap, heure UTC et heure locale du site. |
| **Ma machine** | Diagnostic matériel et parallélisme retenu (exemple minimal de module). |

<p align="center"><img src="docs/manuel/img/catalogue_fr.png" width="820" alt="Catalogue de la banque OHP"></p>
<p align="center"><img src="docs/manuel/img/module_archives_fr.png" width="820" alt="Archives des observatoires"></p>

### Installer

**Paquets tout compris** (rien d'autre à installer, mise à jour automatique) — page *Releases* du dépôt :

| Système | Fichier | Installation |
|---|---|---|
| Windows 10/11 64 bits | `Coupole-Setup-x.y.z.exe` | double-clic ; « Informations complémentaires » puis « Exécuter quand même » au premier lancement (installeur non signé) ; aucun mot de passe administrateur |
| macOS Apple Silicon / Intel | `Coupole-x.y.z-macos-arm64.dmg` / `-x86_64.dmg` | glisser dans Applications ; premier lancement : clic droit, « Ouvrir » |
| **Ubuntu / Debian** x86_64 / ARM64 | `coupole_x.y.z_amd64.deb` / `_arm64.deb` | `sudo apt install ./coupole_x.y.z_amd64.deb` (apt installe les bibliothèques Qt nécessaires) ; commande `coupole`, entrée de menu ; désinstaller : `sudo apt remove coupole`. Ubuntu 22.04 ou plus récent, Debian 12 ou plus récent |
| Autre Linux x86_64 / ARM64 | `Coupole-x.y.z-linux-x86_64.tar.gz` | décompresser, lancer `installer.sh` (dans `~/.local/share`, entrée de menu) |

**Avec le Python de l'ordinateur** (≥ 3.10) — depuis le dossier des sources :

```bash
sh install.sh          # Linux, macOS : environnement virtuel, dépendances, lanceurs ; Entrée pour confirmer
install.bat            # Windows (double-clic) : idem, raccourcis Bureau et menu Démarrer
```

**Pour les habitués de Python** :

```bash
pipx install git+https://github.com/ARP273-ROSE/coupole        # ou : pip install .
pip install ".[qualite]"                                        # + module Qualité (SEP)
pip install ".[alignement]"                                     # + reproject (alignement adaptatif et exact)
python -m coupole            # interface ;   coupole --help : ligne de commande
```

Les paquets autonomes (installeur Windows, .dmg, .deb, tar.gz) embarquent déjà SEP, reproject, psutil et lxml
(0.2.1) ; « Ma machine » et « À propos » listent les bibliothèques facultatives présentes.

### En deux minutes

```bash
coupole ohp catalogue --type neb                       # les nébuleuses de la banque
coupole ohp estimer "NGC 6888" --nuit 2025-07-16      # 800 images, 6,72 Go → 2,44 Go en XISF
coupole ohp traiter "(914) Palisana" --dest ~/OHP      # télécharge, vérifie, corrige, convertit, range
coupole ohp tout --dest ~/OHP --oui                    # toute la banque (≈ 78 Go → ≈ 30 Go), reprenable
coupole ohp nouveautes --dest ~/OHP                    # ce qui est apparu dans la banque depuis votre copie
coupole ohp reorganiser ~/Vrac --dest ~/OHP            # range des fichiers déjà convertis (déplacement, jamais d'écrasement)
coupole ohp anomalies --csv anomalies.csv              # ce qui est écarté, et pourquoi
coupole qualite ~/OHP --ecrire                         # QUALITE.csv et QUALITE.txt par lot
coupole archives chercher "M 16" --mission JWST        # produits finaux publics de JWST autour des Piliers
coupole archives telecharger "M 16" --mission JWST --instrument MIRI --dest ~/Ciel   # estimation, confirmation
coupole archives aligner ~/Ciel/Archives/JWST/M_16/MIRI_IMAGE/*/*_sci.xisf --dest ~/Ciel/Piliers --optimale
coupole archives chercher --archive opus --corps Io --debut 1979-03-01 --fin 1979-03-10   # Voyager 1
coupole --lang en ohp catalog                           # tout existe aussi en anglais
```

Tout ce que fait l'interface se fait en ligne de commande (`--json` pour les scripts). Le traitement est
**reprenable** : relancer la même commande reprend là où il s'était arrêté ; il peut être mis en **pause** ; un
**journal lisible et bilingue** (`_traitement/JOURNAL.txt`) garde la trace de chaque session et de chaque image.
« Tout télécharger » affiche volume, durée estimée et place libre **avant** de demander confirmation ; au démarrage,
Coupole peut signaler (sans jamais télécharger seul) les **nouveautés** de la banque absentes de votre copie.

### Pourquoi XISF par défaut (et quand préférer autre chose)

| Format | Pour | Détail |
|---|---|---|
| **XISF** (défaut) | PixInsight | Float32 en ADU avec `bounds="-1000:65535"` (rien à régler à l'ouverture, même échelle pour toutes les poses), UInt16 pour les FITS IRIS entiers ; compression zstd+sh niveau 9 : 36 % du FITS d'origine pour le T120. |
| **XISF compatible** (0.1.9) | N.I.N.A., Siril ≥ 1.4, PixInsight | Entiers 16 bits + piédestal de 1 000 ADU (`PEDESTAL`), zlib+sh comme N.I.N.A. : N.I.N.A. ramène tout flottant à [0, 1] (image blanche) et la 3.2 ne lit pas zstd ; Siril garde les flottants XISF hors de sa plage (vérifié sur le code et par essai réel : tableau « qui lit quoi » du manuel). |
| **FITS compressé `.fits.fz`** | Siril, astropy, DS9 | Compression par tuiles du standard FITS, **sans perte** : GZIP_2 sans quantification pour les flottants (RICE_1 et HCOMPRESS quantifient : vérifié, écart d'un ADU), RICE_1 pour les entiers. |
| **FITS float32** | tout logiciel | Non compressé ; dans PixInsight, régler la plage FITS sur 0–65535 (Truncate). |

Chaque fichier écrit est relu et comparé pixel à pixel ; l'écart au FITS d'origine (float64 du T120) reste sous le
demi-ULP du float32 (≤ 0,016 ADU).

### ASTAP (facultatif)

Sans ASTAP, Coupole fait **tout** : contrôles de cohérence de la solution astrométrique existante (échelle, angle,
centre), en-têtes, lots, conversion. ASTAP ajoute la **vérification indépendante** de chaque solution (et la
réfection d'une solution fausse). L'assistant (menu *Outils*, ou `coupole astap --guide`) indique le bon paquet pour
le système et l'architecture détectés (Windows x64/ARM64, macOS Intel/Apple Silicon, Linux deb/rpm/Arch/archive,
x86_64/arm64), le catalogue conseillé — **D80** (≈ 1,2 Go) : les champs de la banque (10,7′ à 31′) sont sous le seuil
de 0,6° du site officiel, qui indique que les catalogues denses conviennent aux petits champs ; D50 convient aussi pour
IRIS — avec les liens officiels (www.hnsky.org/astap.htm), puis détecte ASTAP et son catalogue (emplacements par
défaut, PATH, variables `COUPOLE_ASTAP` et `COUPOLE_ASTAP_CATALOGUE`, choix manuel) et vérifie version et complétude
(1 476 tuiles).

### La carte graphique

Elle est détectée et affichée (NVIDIA, AMD, Intel, Apple), mais **le module Banque OHP ne l'utilise pas** : son
travail est limité par le réseau, le disque et la compression Zstandard (processeur). L'API `coupole.core.calcul`
permet aux modules futurs d'utiliser CuPy (facultatif) quand c'est utile. Le parallélisme, lui, s'adapte à la
machine : téléchargements 3 (4 au plus, serveur public, débit plafonné à 8 Mo/s), conversions = cœurs physiques − 1
bornées par la mémoire disponible (≈ 500 Mo par conversion d'image IRIS 4096²), mode économe automatique sous 4 Go
ou 2 cœurs, bridage manuel possible.

### Rapports d'incident et mises à jour

Au premier lancement, Coupole demande s'il peut envoyer des rapports **anonymes** en cas de plantage (version,
système, processeur, mémoire, trace d'erreur aux chemins tronqués, 64 ko au plus ; jamais de nom de machine,
d'utilisateur ni d'image). Sans accord, rien ne part. Audit complet (performance, parallélisme, robustesse,
sécurité, multiplateforme, bilinguisme) : [docs/AUDIT_2026-10.md](docs/AUDIT_2026-10.md). Les paquets se mettent à jour d'eux-mêmes depuis les Releases GitHub (archive
du code seulement, aucun exécutable téléchargé) ; une installation par pip/pipx indique la commande à lancer ; une
installation par le paquet `.deb` (fichiers sous `/opt/coupole`, gérés par dpkg) signale la nouvelle version et
pointe vers le `.deb` à installer.

### Évolutif

Adresses des services dans `coupole/donnees/sources.json` (modifiables dans les Préférences ou `coupole sources`,
mises à jour par le fichier publié dans le dépôt, contrôle de forme et liste blanche de domaines) ; table de
classement des cibles en JSON, corrections mémorisées, nouveaux noms classés par règles, résolution en ligne
facultative (JPL SBDB, CDS Sesame) et regroupement par position ; nouveautés de la base signalées à chaque
rafraîchissement ; colonnes ObsCore, instruments et filtres nouveaux tolérés.

### Documentation

- Manuel de référence : `coupole/docs/manuel_fr.pdf` (menu *Aide* > *Manuel*, ou `coupole manuel`).
- Écrire un module, ajouter un format : [CONTRIBUTING.md](CONTRIBUTING.md). Historique : [CHANGELOG.md](CHANGELOG.md).

### Sources et crédits

Données : banque « OHP student observations », Observatoire de Paris / PADC (Paris Astronomical Data Centre),
service TAP public, licence Etalab 2.0. Méthode de traitement : guide officiel de la base (PADC-BDD-DU-ECU) et
inventaire de la banque de l'auteur. Format XISF : spécification de Pleiades Astrophoto. ASTAP : Han Kleijn
(www.hnsky.org), non inclus. SEP : Source Extractor en Python (LGPL). Cartes : © OpenStreetMap contributors.
Fiche en ligne : SIMBAD et Sesame (CDS, Strasbourg), Aladin Lite (CDS), NED (NASA/IPAC), JPL Small-Body Database.
Archives : MAST (STScI ; NASA/ESA, NASA/ESA/CSA), ESO Science Archive Facility, IRSA (NASA/IPAC), Astro Data Archive
de NOIRLab, Keck Observatory Archive (NExScI), SDSS, Planetary Data System (nœud Anneaux et Lunes : OPUS ; Imaging
Node) ; chaque image téléchargée porte le crédit de son archive (`CREDIT`), à reprendre sous toute image publiée ;
reproject (Astropy, BSD, facultatif).
Cosmologie : noyau de calcul repris du calculateur « cosmologie-redshift » du même auteur (publié sans licence
formelle, intégré ici par son auteur sous GPL-3), astropy.cosmology, paramètres Planck 2018 / 2015, WMAP 9, SH0ES.
Auteur : ARP273-ROSE. Licence : GNU GPL version 3 ou ultérieure.

---

<a id="english"></a>
## English

**Free** (GPL-3.0) toolbox for students of the « Explorer et Comprendre l'Univers » university diploma (DU ECU) of
the Observatoire de Paris. Python 3.10+, PyQt6 graphical interface **and** a complete command line, in French and
English, on Windows, macOS and Linux. **Modular** architecture: more modules will come during the year.

| Module | What it does |
|---|---|
| **OHP image bank** | Fetches the « OHP student observations » bank (T120 and IRIS, 7,989 images, 78 GB) through the Observatory's public TAP service; catalogue of 166 objects; resumable downloads; duplicates left out (and explained); astrometric solution checked (ASTAP optional); headers fixed with traceability; **XISF** (PixInsight), **lossless compressed FITS** (`.fits.fz`: Siril, astropy) or float32 FITS output; sorting into **stackable sets** with a `LOT.txt` sheet; sky map; anomaly report; optional **online record** (SIMBAD, JPL, Aladin and NED links). |
| **Observatory archives** (0.2.0) | Public images from major observatories and space probes, current and past: **Hubble, JWST, GALEX** (MAST), **ESO** (Phase 3 products), **Spitzer, WISE, 2MASS** (IRSA), **NOIRLab** (DECam…), **Keck** (KOA, raw frames), **SDSS**, **Voyager and Cassini** (OPUS, PDS), **Juno** (JunoCam, PDS). Search by name or coordinates (or by body for probes), final products and public data by default, **volume estimated before downloading** and confirmation beyond a threshold, capped rate and resume; science image extraction (WCS, units, masked NaN, credit in the header), XISF or FITS; PDS3/VICAR/PDS4 conversion; **alignment** by astrometry onto a common grid and **colour composition** in wavelength order (preview, PixelMath). Gemini (account required) and SMOKA (web form) reported. Method and sources: [docs/archives_methode.md](docs/archives_methode.md) (French, English summary). |
| **Image quality** | Optional: FWHM, ellipticity (3 × 3 map), background, noise, gradient, saturation, trails, sampling — measurements validated on synthetic images. |
| **Spectra and series** | Reading and plotting 1D data (21 cm H I spectra with frequency ↔ radio velocity axis, light curves, FITS or CSV tables). |
| **Cosmology** | From redshift to distances (comoving, luminosity, angular, light travel), ages, comoving volume, distance modulus, scale in kpc/″; Planck 2018 with uncertainties, SH0ES, Planck 2015, WMAP 9, custom set; an object's redshift requested from SIMBAD; curves, CSV export. Core taken from the [cosmologie-redshift](https://github.com/ARP273-ROSE/cosmologie-redshift) calculator, checked with SageMath. |
| **Sites and times** | Observing sites (MPC), OpenStreetMap map, UTC and site local time. |
| **My computer** | Hardware diagnosis and chosen parallelism (minimal example module). |

### Installing

**All-inclusive packages** (nothing else to install, automatic updates) — repository *Releases* page:
`Coupole-Setup-x.y.z.exe` (Windows 10/11 64-bit; « More info » then « Run anyway » on first launch; no
administrator password), `Coupole-x.y.z-macos-arm64.dmg` / `-x86_64.dmg` (first launch: right click, « Open »),
`coupole_x.y.z_amd64.deb` / `_arm64.deb` (Ubuntu 22.04+, Debian 12+: `sudo apt install ./coupole_x.y.z_amd64.deb`,
which pulls the Qt system libraries; `coupole` command and menu entry; `sudo apt remove coupole` to uninstall),
`Coupole-x.y.z-linux-x86_64.tar.gz` / `-arm64` for other Linux systems (unpack, run `installer.sh`).

**With the computer's Python** (≥ 3.10), from the source folder: `sh install.sh` (Linux, macOS) or `install.bat`
(Windows) — virtual environment, dependencies, launchers; press Enter to confirm.

**For Python users**: `pipx install git+https://github.com/ARP273-ROSE/coupole` (or `pip install .`);
`pip install ".[qualite]"` adds the Quality module, `pip install ".[alignement]"` adds reproject (adaptive and
exact alignment); `python -m coupole` starts the interface, `coupole --help`
the command line. The standalone packages (Windows installer, .dmg, .deb, tar.gz) already bundle SEP, reproject,
psutil and lxml (0.2.1); « My computer » and « About » list the optional libraries present.

### In two minutes

```bash
coupole --lang en ohp catalog --type neb
coupole --lang en ohp estimate "NGC 6888" --night 2025-07-16
coupole --lang en ohp process "(914) Palisana" --dest ~/OHP
coupole --lang en ohp anomalies --csv anomalies.csv
coupole --lang en qualite ~/OHP --write
coupole --lang en archives search "M 16" --mission JWST
coupole --lang en archives download "M 16" --mission JWST --instrument MIRI --dest ~/Sky
coupole --lang en archives align ~/Sky/Archives/JWST/M_16/MIRI_IMAGE/*/*_sci.xisf --dest ~/Sky/Pillars --optimal
```

Everything the interface does is available on the command line (`--json` for scripts); processing is
**resumable**.

### Output formats

**XISF** (default, PixInsight): Float32 in ADU with `bounds="-1000:65535"` (nothing to set when opening, same scale
for every exposure), UInt16 for integer IRIS FITS; zstd+sh level 9 compression (36 % of the original T120 FITS).
**Compatible XISF** (0.1.9; N.I.N.A., Siril ≥ 1.4, PixInsight): 16-bit integers + 1,000 ADU pedestal (`PEDESTAL`),
zlib+sh like N.I.N.A. — N.I.N.A. maps any float to [0, 1] (white image) and 3.2 cannot read zstd; Siril keeps XISF
floats outside its range (checked in the code and by real tests: « who reads what » table in the manual).
**`.fits.fz`** (Siril, astropy, DS9): FITS tile compression, **lossless** — GZIP_2 without quantization for floats
(RICE_1 and HCOMPRESS quantize: checked, one-ADU error), RICE_1 for integers. **float32 FITS**: universal,
uncompressed. Every file written is read back and compared pixel by pixel.

### ASTAP (optional)

Without ASTAP, Coupole does **everything**: consistency checks of the existing astrometric solution, headers, stacks,
conversion. ASTAP adds an **independent check** of each solution. The assistant (*Tools* menu, or
`coupole astap --guide`) gives the right package for the detected system and architecture, the recommended catalogue
(**D80**, ≈ 1.2 GB; D50 also suits IRIS) with the official links (www.hnsky.org/astap.htm), then detects ASTAP and its
catalogue (default locations, PATH, `COUPOLE_ASTAP` / `COUPOLE_ASTAP_CATALOGUE`, manual choice) and checks version and
completeness.

### Graphics card

Detected and shown, but **not used by the OHP bank module** (its work is bound by network, disk and Zstandard
compression on the processor). The `coupole.core.calcul` API lets future modules use CuPy (optional). Parallelism
adapts to the computer (downloads: 3, at most 4, rate capped at 8 MB/s; conversions: physical cores − 1, bounded by
available memory; automatic economy mode below 4 GB or 2 cores; manual limits).

### Incident reports and updates

At first launch Coupole asks whether it may send **anonymous** crash reports (64 kB at most, never a computer or user
name); without consent nothing is sent. Full audit (performance, parallelism, robustness, security, cross-platform,
bilingualism): [docs/AUDIT_2026-10.md](docs/AUDIT_2026-10.md) (French).
Packages update themselves from GitHub Releases (code archive only, no executable downloaded); a pip/pipx installation
shows the command to run; a `.deb` installation (files under `/opt/coupole`, managed by dpkg) announces the new
version and points to the `.deb` to install.

### Documentation, sources, credits

Reference manual: `coupole/docs/manuel_en.pdf` (*Help* > *Manual*, or `coupole manual`). Writing a module, adding a
format: [CONTRIBUTING.md](CONTRIBUTING.md). History: [CHANGELOG.en.md](CHANGELOG.en.md).
Data: « OHP student observations », Observatoire de Paris / PADC, public TAP service, Etalab 2.0 licence. XISF:
Pleiades Astrophoto specification. ASTAP: Han Kleijn (www.hnsky.org), not included. SEP (LGPL). Maps: ©
OpenStreetMap contributors. Online record: SIMBAD and Sesame (CDS, Strasbourg), Aladin Lite (CDS), NED (NASA/IPAC),
JPL Small-Body Database. Archives: MAST (STScI; NASA/ESA, NASA/ESA/CSA), ESO Science Archive Facility, IRSA
(NASA/IPAC), NOIRLab Astro Data Archive, Keck Observatory Archive (NExScI), SDSS, Planetary Data System (Ring-Moon
Systems Node: OPUS; Imaging Node); every downloaded image carries its archive's credit (`CREDIT`), to repeat under any
published image; reproject (Astropy, BSD, optional). Cosmology: computation core taken from the same author's « cosmologie-redshift » calculator
(published without a formal licence, included here by its author under GPL-3), astropy.cosmology, Planck 2018 / 2015,
WMAP 9, SH0ES parameters. Author: ARP273-ROSE. Licence: GNU GPL version 3 or later.
