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

## 2026-10-08 — état à la fin de la session
- Paquet Linux final reconstruit (avec SEP) : `Coupole-0.1.0-linux.tar.gz` (202 Mo) et `coupole-app-0.1.0.zip`
  (4,4 Mo, manuels compris) à la racine du dépôt (ignorés par git). **Mise à jour automatique essayée en vrai** sur
  une copie du paquet annoncée en 0.0.9 : archive appliquée, l'application repart en 0.1.0.
- Suite de tests : 129 réussis, 1 sauté (essai réseau, activé par `COUPOLE_TEST_RESEAU=1`) ; sous Python 3.10 aussi.
- `collecte.php` : **non modifié** — il accepte déjà toute application dont l'en-tête X-App suit
  `nom/version` (« coupole/0.1.0 ») et range ses rapports dans `rapports/coupole/` ; les genres envoyés par Coupole
  (installation, demarrage, plantage, crash_natif, gel, manuel) sont ceux qu'il connaît.

### Reste à faire pour publier
1. Créer le dépôt **public** `ARP273-ROSE/coupole` (nom en place dans `kit.json`, `coupole/donnees/sources.json`,
   `pyproject.toml`) et pousser ; la mise à jour automatique et le fichier de sources distant en dépendent.
2. Poser le tag `v0.1.0` : le workflow `release.yml` construit Windows (Python embarqué + Inno Setup), macOS (arm64,
   x86_64) et Linux (x86_64, arm64) et publie la Release.
3. Essayer réellement sous Windows (installeur, `install.bat`/`install.ps1`, raccourcis) et sous macOS (bundle, dmg) :
   non testés ici. Carte graphique NVIDIA/CuPy : non testée (pas de carte NVIDIA sur le NAS).
4. Sites partenaires (Madagascar, Australie côte ouest « ZATCO » d'après la transcription, Yunnan) : à ajouter quand
   leurs coordonnées seront connues de source sûre.
5. Formats réels des radio-antennes de Meudon et de Pologne : ajouter un lecteur quand un fichier exemple sera
   disponible (architecture et documentation en place).

## 2026-10-08 — fiche en ligne (SIMBAD, JPL) et module Cosmologie
### Vérification du calculateur « cosmologie-redshift » (avant intégration, dépôt non modifié)
- Code relu : `cosmo_core.py` (make_cosmology, grandeurs, incertitudes avec terme croisé, SH0ES, courbes), parties
  calculatoires de la GUI et de la console.
- Comparé sur 30 valeurs de z (0, 10⁻⁸ … 1100) × Ωk ∈ {−0,05, −0,01, 0, 0,01, 0,05} à (i) astropy construit
  indépendamment et (ii) une intégration SageMath 10.10 (mpmath 18 chiffres, Fermi-Dirac exacte des neutrinos,
  constantes CODATA, sans astropy) : `outils/verif_cosmo/`.
- Résultat : **aucun écart > 1e-4, aucun bug**. Distances ≤ 2,8e-6, âges et E(z) ≤ 1,8e-5 (ajustement de Komatsu
  des neutrinos dans astropy : contre une référence Sage qui l'emploie aussi, ≤ 1e-9). Constantes en dur (t₀,
  D_H, horizons des particules et des événements, z et valeur du maximum de D_A) ≤ 4,3e-6.
- Remarques (pas des bugs) : ρ(H₀, Ωm) = −0,9763 vient de σ(ω_c) et σ(ω_b) ajoutées en quadrature ; avec la valeur
  publiée σ(Ωm h²) = 0,00087, Sage donne ρ = −0,9863 (σ(D_C) à z = 1 : 0,311 % → 0,304 %). Ωk ≠ 0 bâtit Ωm = 0,31110
  exactement alors que Planck18 a 0,3110997 : saut de ~1e-6 entre Ωk = 0 et Ωk ≠ 0, négligeable.
- Trouvé en passant : `astropy.cosmology.comoving_volume` perd tous ses chiffres à z ≲ 1e-6 en univers courbe
  (volume ×50 à ×250, voire négatif) ; le calculateur ne calcule pas de volume, Coupole emploie un développement.

### Fait
- Cœur : `core/simbad.py` (client repris du calculateur + fiche détaillée en un appel sim-script), `core/enligne.py`
  (SIMBAD, Sesame, JPL SBDB ; cache daté 30 j, politesse 1 req/s/service, repli hors ligne, réglage
  `services_en_ligne`), `reseau.lire_texte`, adresses dans `sources.json` (version 2 ; domaine caltech.edu ajouté
  pour NED), `gui/fiche.py` (widget réutilisable), `FenetrePrincipale.ouvrir_module()`.
- Banque OHP : onglet et bouton « Fiche en ligne » (requête seulement onglet affiché, 0,6 s d'attente).
- Module `cosmo` : calcul (noyau du calculateur + volume, μ, kpc/″, jeux Planck 2015/WMAP 9/manuel/perso), GUI
  (tableau, courbes `gui/trace.TraceCourbes`, exemples, SIMBAD, export CSV), CLI `coupole cosmo`, aide F1.
- Dépendance ajoutée : scipy (astropy.cosmology en a besoin pour intégrer).
- Tests : `test_cosmo.py` (valeurs Sage figées dans `tests/cosmo_reference_sage.json`, 11 jeux), `test_enligne.py`
  (réponses simulées ; essai réel M27, NGC 6888, (3) Juno, Pluton avec `COUPOLE_TEST_RESEAU=1` : réussi),
  tests d'interface (module Cosmologie, fiche → Cosmologie).
- Captures FR/EN (`fiche_*.png`, `module_cosmo_*.png`, autres régénérées), manuels FR/EN complétés et recompilés.

## 2026-10-08 — audit complet et nouvelles fonctions (rapport : `docs/AUDIT_2026-10.md`)
Huit axes audités, constats avec fichier:ligne, gravité, correction et test ; puis chaîne complète mesurée et quatre
fonctions ajoutées (tout télécharger, rangement/réorganisation, journal, nouveautés).
- **Performance** : fenêtre affichée **1,51 → 0,42 s** (astropy/scipy/sep plus jamais chargés avant l'affichage :
  Cosmologie calculait dans le fil graphique à la construction, Qualité importait sep, la carte du ciel calculait
  l'écliptique au premier paint) ; mémoire de pointe IRIS 4096² **573 → 365 Mo** (vues sur la référence float64 qui
  empêchaient sa libération, hachage sans copie, memmap, XISF sans copies intermédiaires) ; une requête HTTP par
  image au lieu de deux ; progression agrégée à 10 Hz (3 073 → 251 événements).
- **Chaîne complète** (`outils/pipeline.py`, serveur local) : 24 images de 8 Mo à 8 Mo/s en **24,5 s = durée du
  téléchargement seul** (recouvrement complet) ; sans plafond 86 Mo/s de FITS convertis sur 5 processus
  (0,13 s/image) → le débit est borné par le réseau, pas par le CPU ni une sérialisation.
- **Parallélisme** : bridage manuel borné par la mémoire ; annulation qui termine les processus et ASTAP (Popen
  scruté) ; `BrokenProcessPool` : KeyError corrigé (le pilote plantait après un plantage de processus) ; pause ;
  fermeture : `arreter_tout()` lève et attend tous les fils, pools, QThread.
- **Robustesse** : `lire_json_protege` (réglages corrompus mis de côté), `ecrire_atomique` partout, bornes FITS/XISF,
  `Tache(parent=…).quand_fini()` (rien vers un widget détruit, exception de slot jamais fatale), vigie de gel et
  faulthandler **testés** (gel simulé détecté, SIGSEGV relevé).
- 🔴 **Bug trouvé** : logique des doublons de pixels inversée (`pilote._enregistrer`).
- **Sécurité** : HTTPS obligatoire (sources distant, collecte), `verifier_archive` (zip slip robuste, symlinks,
  bombe), rapports ≤ 64 ko + nom de machine masqué, noms réservés Windows, aucun écrasement au rangement,
  `release.yml` corrigé (importait `reporting`/`updater`), pip-audit propre.
- **Multiplateforme** : console cp1252 (`reconfigure(errors='replace')`), locales Windows, rôles de menu macOS,
  chemins > 250 car. ; tests à 150 % et 200 % ; Python 3.10 et 3.12.
- **Bilinguisme** : test de fuite de langue (aucune fuite réelle) ; 165 clés ajoutées.
- **Cosmologie** : combos dimensionnés au contenu (`ajuster_combo`), courbes sous le tableau sous 1500 px.
- **Nouvelles fonctions** : `ohp tout` (estimation volume/temps/place avant confirmation, dossier proposé par OS,
  reprise, pause, rapport), `JOURNAL.txt` bilingue horodaté, `ohp reorganiser` (déplacement sans écrasement),
  `ohp nouveautes` + bandeau au démarrage (fréquence réglable, jamais de téléchargement sans accord).
- Tests : **185 → 232** (3.12, exit 0), 226 sous 3.10 ; manuels FR/EN recompilés, captures régénérées.


## 2026-10-08 — suite de l'audit : § 10 « Proposé, non appliqué » tranché
Consigne : « fais au mieux » → appliquer ce qui apporte un gain réel sans risque, laisser le reste en l'expliquant.
- **Appliqué — proposition 2** (cache de la hauteur du Soleil) : `core/temps.py::hauteurs_soleil_cachees` — cache par
  (site arrondi, minute UTC), dict ordonné borné à 4 096 entrées + verrou (un cache par processus de conversion suffit,
  le `spawn` les isole) ; les deux hauteurs du contrôle « heure locale écrite par erreur » (heure lue, heure corrigée)
  partent en **un seul** appel astropy (le coût est par appel, pas par instant). Mesure dans `python:3.12-slim`
  (`mesure_soleil.py`, 60 poses de 20 s = 3 par minute) : **13,2 → 2,5 ms de CPU par pose** (−81 %) ; image isolée
  (profil `outils/pipeline.py`, conversion seule) : `soupcon_heure_locale` **33 → 13 ms**. Chaîne complète 24 images
  sans plafond : 2,28 → 2,31 s (inchangée, bornée par le réseau/les processus, comme annoncé). Deux instants d'une même
  minute reçoivent la valeur du premier calculé (≤ 0,25° d'écart) : sans effet sur des seuils à 0° et −12°.
  Tests : `test_cache_hauteur_du_soleil_par_minute` (même minute → un seul calcul, identique au calcul direct à 1e-9 ;
  minute suivante et autre site → nouveaux calculs), `test_cache_hauteur_du_soleil_entre_fils` (8 fils simultanés).
- **Appliqué — proposition 5** (ASTAP orphelin sous Windows) : `core/processus.py::confiner_descendance()` — chaque
  processus de conversion se place lui-même (initializer du pool) dans un job object `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`
  dont il détient le seul descripteur (`ctypes`, kernel32 : `CreateJobObjectW`, `SetInformationJobObject`,
  `AssignProcessToJobObject(GetCurrentProcess())`). Ses enfants (ASTAP) héritent du job ; quand le pilote le termine
  (`TerminateProcess`), ou s'il plante, le système ferme le descripteur → le job se ferme → ASTAP est tué à l'instant.
  Aucun PID à suivre côté pilote. Linux/macOS : inchangés (SIGTERM → `astap.tuer_en_cours`). Échec de l'API : journal
  technique, comportement d'avant. Tests Windows seulement (`tests/test_processus.py`, `skipif`) : parent confiné tué →
  l'enfant `ping -n 60` meurt ; **témoin** sans confinement → l'enfant survit (le test mesure bien le défaut corrigé).
- **Appliqué — proposition 4** (place juste) : `selection.fenetre_adaptee(est, conv, dl, libre)` — fenêtre nominale
  2 × conversions + téléchargements, réduite à `(libre − sortie) // (2 × plus gros)` quand la place manque, jamais sous
  conversions + 1 ; `place_necessaire(…, libre)` suit la fenêtre réduite, donc CLI (`ohp estimer`, `ohp telecharger`,
  `ohp tout`) et GUI acceptent ce qu'ils refusaient quand seule la réserve de fenêtre manquait. Le pilote recalcule la
  fenêtre au lancement sur la place réelle (`Traitement._fenetre`), signale la réduction (événement `fenetre` → journal
  de l'interface, ligne `jrn_fenetre_reduite` dans JOURNAL.txt, message `ohp_fenetre_reduite` en CLI). Tests :
  `test_fenetre_reduite_a_la_place_libre` (bornes), `test_pilote_reduit_la_fenetre_quand_la_place_est_juste` (place
  simulée : fenêtre 3 au lieu de 6, six images traitées, journal bilingue), témoin place large.
- **Non appliqué — proposition 1** (connexions HTTP persistantes) : gain < 1 % au plafond de 8 Mo/s (une image de 8 Mo
  dure 1 s, l'établissement TCP quelques ms) contre une gestion des connexions mortes à écrire ; à revoir seulement si
  le plafond est relevé bien au-delà.
- **Non appliqué — proposition 3** (`MEMOIRE_PAR_CONVERSION_MO` 500 → 400) : 365 Mo mesurés, mais ASTAP ajoute son
  propre processus à côté de chaque conversion ; une conversion de plus sur une machine à 4 Go ne vaut pas un risque
  d'échange ou d'OOM. Gardé à 500.
- Manuels FR/EN : phrase du pipeline (fenêtre réduite si la place est juste ; arrêt d'ASTAP par signal / job object)
  et recompilés ; CHANGELOG FR/EN ; `docs/AUDIT_2026-10.md` § 10 annoté.
- Tests dans `python:3.12-slim` (copie du dépôt sans `build/`, `pip install ".[test]"`, `QT_QPA_PLATFORM=offscreen`) :
  **232 réussis, 10 sautés, code de sortie 0** (les 2 tests du job object ne tournent que sous Windows : CI).
- Première CI (6 jobs) : Windows 3.10 vert (job object validé en vrai : enfant tué avec le parent confiné, témoin qui
  survit sans confinement) ; **deux défauts attrapés** — (i) le cache calculait hors du verrou : deux fils qui ratent
  le cache en même temps calculaient chacun à son propre instant et obtenaient des valeurs différentes pour la même
  minute → calcul **sous le verrou** (un seul calcul, même valeur pour tous) ; (ii) `test_interface_reactive` : hoquet
  de 0,69 s du serveur Windows partagé contre un seuil de 0,5 s → seuil porté à 1 s (un vrai gel durerait les 1,5 s du
  travail). Deuxième CI : voir le dépôt (6 jobs attendus verts).
