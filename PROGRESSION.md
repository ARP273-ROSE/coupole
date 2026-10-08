# PROGRESSION — Coupole

État d'avancement, tenu à jour pendant le développement (reprise possible).

## 2026-10-08 — démarrage
- [x] Lecture complète de `_docs/Observatoire-Paris/Banque-Images-OHP/` (README, Inventaire.pdf, scripts, TEST.md, index).
- [x] Lecture du kit (`_kit_windows`), de MountMonitor (multiplateforme, i18n), de `collecte.php`.
- [x] Nom choisi : **Coupole** (PyPI : libre ; GitHub : seulement des dépôts personnels sans étoile, aucun logiciel d'astronomie connu).
- [x] Service TAP direct vérifié : `http://tap-ufe.obspm.fr/tap/sync`, `SELECT COUNT(*) FROM ivoa.obscore` = 7 989.
- [ ] Cœur, modules, GUI, CLI, tests, paquets, manuels.

## 2026-10-08 — cœur et module Banque OHP opérationnels
- Inventaire par TAP direct (une requête ADQL, 1,6 s) ; instantané livré `coupole/modules/ohp/data/inventaire.json.gz`
  (7 989 lignes). Enrichissement **identique** à `cibles.charger()` sur les 7 989 images (nuit, objet, catégorie,
  doublons, dates partagées, plein jour) — y compris avec la nuit et le plein jour recalculés d'après le site
  (midi local, hauteur du Soleil à l'OHP).
- **Essai réel** (serveur de l'Observatoire, 109 Mo) : (914) Palisana (16 lignes dont 6 doublons) + IRIS M16 OIII
  (UInt16) + IRIS NGC 5866 z (Float32, CTYPE -SIP sans coefficients), ASTAP CLI 2026.09.01 + D80 :
  12 converties, 6 doublons, 10 confirmées + 2 validées, 3 lots, 14 s.
  Comparaison au traitement de référence (`outils/comparer_reference.py`, 12 XISF relus sur la copie du NAS) :
  **pixels identiques bit à bit (12/12), mêmes en-têtes** (hors nom du programme), mêmes statuts, mêmes
  destinations, mêmes lots → « aucun écart ».

## 2026-10-08 — distribution
- `install.sh` testé dans `python:3.12-slim` (installation complète, lanceurs, entrée de menu, `coupole ohp inventaire`)
  et dans `debian:bookworm-slim` sans Python (message FR et EN, code 1) et avec Python sans `venv` (message, code 1).
- `install.ps1` : syntaxe validée par PowerShell 7 (conteneur `mcr.microsoft.com/powershell`) ; enregistré en UTF-8
  avec BOM (PowerShell 5.1) ; **non exécuté sous Windows** (raccourcis par WScript.Shell).
- Suite de tests sous Python 3.10 (`python:3.10-slim`) : 105 réussis, 7 sautés (traitement de référence absent).
- Paquet Linux autonome construit localement (`build_unix.py`, CPython 3.12.14 python-build-standalone) :
  327 Mo dépliés, archive 197 Mo, archive applicative 1,1 Mo ; `Coupole.sh --version`, catalogue, et traitement réel
  de (914) Palisana sans ASTAP (10 converties, 10 validées) depuis le paquet.
  Défaut trouvé et corrigé : le paquet s'annonçait en 0.0.0 (VERSION ignoré faute de kit.json) → détection par
  `lancer.py`/`pyproject.toml`, et test `test_version_unique`.

## 2026-10-08 — performance mesurée (`outils/mesures.py`, Ryzen 5 8500G, 6 cœurs, NVMe)
| Mesure | Résultat |
|---|---|
| `coupole --version` (ligne de commande) | 0,10 à 0,20 s |
| Fenêtre affichée | 0,36 à 0,49 s |
| Inventaire chargé (fil de fond, fenêtre déjà utilisable) | 3,1 s au tout premier lancement (hauteur du Soleil de 7 989 poses par astropy), puis 0,64 à 0,69 s (cache) |
| Mémoire de pointe d'une conversion T120 1024² float64 | 144 Mo (processus), +80 Mo par rapport aux imports |
| Mémoire de pointe d'une conversion IRIS 4096² float32 | 600 Mo avant optimisation du contrôle de précision : 855 Mo ; contrôle pixel à pixel désormais par blocs de lignes → réserve de 500 Mo par conversion dans le plan de parallélisme |
| Interface pendant 3 téléchargements simultanés (serveur local, 28 Mo/s) | minuteur de 20 ms : 123 battements, écart maximal 20,8 ms, moyen 20,0 ms → aucune saccade |
| Essai réel 18 poses (Palisana + 2 IRIS), 3 téléchargements, 5 conversions, ASTAP | 14 s de bout en bout ; débit plafonné à 8 Mo/s par défaut |

## 2026-10-08 — module « Qualité des images » (facultatif, SEP + numpy)
Validation sur images synthétiques (`tests/synthetique.py`, étoiles intégrées sur le pixel) — 14 tests :
- FWHM : ajustement d'un Moffat elliptique à β libre (Levenberg-Marquardt en numpy, départ par moments adaptatifs).
  Écart à la valeur injectée ≤ 0,4 % pour des profils gaussiens et Moffat β = 3 de 2,5 à 8 px (tolérance des tests : 2 %).
  Des moments gaussiens seuls surestimaient de 13 à 17 % la FWHM d'un Moffat β = 3 → méthode remplacée.
  Premier essai d'ajustement : ellipticité fausse (θ sans gradient au départ circulaire) → départ par les moments.
- Ellipticité injectée 0,10 / 0,25 → ± 0,02 ; fond à 0,5 % ; bruit à 5 % ; gradient linéaire et vignetage radial
  retrouvés ; carte 3 × 3 ordonnée pour une FWHM qui varie de 3 à 6 px sur le champ ; 5 étoiles saturées → 5 ;
  traînée de 300 px → 1, aucune sur une image sans traînée ; RSN absent sans gain, présent avec EGAIN.
- Retiré (non validable ici) : mag/arcsec² (pas de point zéro), « donuts » de poussière.
Images réelles : 14 images IRIS (12 nuits de 2021 à 2026 + 2 de l'essai, FWHM de 2,4 à 11,3 px, bonnes et mauvaises
nuits) comparées à la FWHM écrite par PinPoint dans l'en-tête : corrélation r = 0,974 (SageMath), rapport médian 1,046
(0,85 à 1,16) — accord d'ordre et de rang, écart attribuable à des estimateurs différents (méthode de PinPoint non
décrite dans les en-têtes). T120 (914) Palisana : FWHM 2,0 à 2,6″, cohérente avec le seeing du site.

## 2026-10-08 — documentation
- Manuels LaTeX au format maison (préambule dérivé de `Ressources-Pedagogiques/latex/preambule.tex`) :
  `docs/manuel/manuel_fr.pdf` (27 p.) et `manuel_en.pdf` (25 p.), captures FR et EN, tableaux des commandes
  générés depuis les vrais analyseurs (`outils/tables_cli.py`), compilés par `docs/manuel/compiler.sh` (deux passes,
  temporaires supprimés), copiés dans `coupole/docs/` (menu Aide > Manuel, `coupole manuel`).
- README bilingue, CONTRIBUTING (écrire un module, ajouter un format), CHANGELOG.md (FR) et CHANGELOG.en.md.
