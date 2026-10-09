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
  travail). Deuxième CI : 5 verts, Windows 3.10 rouge sur `test_pause_suspend_puis_reprend` (délai fixe de 1,5 s
  avant de chercher l'événement « pause » : trop court pour le démarrage du pilote sur ce serveur) → attente scrutée
  de l'événement (≤ 20 s) puis contrôle qu'en pause rien n'avance. Troisième CI : 6 jobs verts.

## 2026-10-09 — version 0.1.1 : paquet .deb, Release unique, retours de Kevin sur la 0.1.0
- **Release v0.1.0** publiée par la CI (6 actifs : Setup Windows, 2 dmg, 2 tar.gz, zip applicatif).
- **Paquet Debian/Ubuntu** : `build_deb.py` (Python + `dpkg-deb --root-owner-group`, sans root) à partir de
  `dist/Coupole/` : `/opt/coupole/{python,app}` + `.pyc` précompilés (`unchecked-hash`, /opt n'étant pas inscriptible),
  `/usr/bin/coupole`, `.desktop` (Name[fr], Keywords, StartupWMClass), icônes hicolor 16→512 + SVG, `copyright` DEP-5
  GPL-3+, `changelog.gz`, page de manuel, postinst/postrm (update-desktop-database, gtk-update-icon-cache, sans échec),
  marqueur `app/installation_systeme.json` lu par `core/maj.py`. Dépendances établies par `ldd` sur les .so de Qt 6.11
  et de CPython (ICU embarqué, OpenSSL statique) avec alternatives `t64` (Ubuntu 24.04 / Debian 13).
- **Mise à jour** : `maj.type_installation()` → `deb` / `systeme` (dossier non inscriptible) / `paquet` / `pip` ;
  `verifier()` retient le `.deb` de l'architecture (nom stable d'abord) ; `consigne_systeme()` donne URL + commande
  apt ; `appliquer()` refuse hors paquet autonome ; GUI : bouton « Télécharger le paquet ». Tests (4).
- **Paquets allégés** : `install_only_stripped` de python-build-standalone (libpython 219 Mo + binaire 102 Mo de
  symboles !), Tcl/Tk, include, share, pip, scripts de bin/, données de test, FFmpeg, eglfs, greffons Qt orphelins
  (Qt3D, Qml, WebView…) retirés : tar.gz 229 → 137 Mo ; `.deb` 106 Mo (xz), 4 089 fichiers, 2 501 .pyc.
- **Essais réels du .deb** (`/mnt/apps_pool/_transfert/coupole_deb_test/`) : ubuntu:22.04 et ubuntu:24.04 nus, `apt-get
  install ./coupole-linux-amd64.deb` (71 paquets tirés), `ldd` sur tous les .so (ne manquent que libgtk-3 / libcups des
  greffons facultatifs, en Recommends), `coupole --version`, `--help` FR et EN, `ohp inventaire` et `catalogue` **hors
  ligne** (`--network none`), GUI offscreen capturée, `coupole maj` (version simulée 0.0.9), `apt-get remove` : aucun
  reste hors `~/.config`. lintian (debian:bookworm) : seule erreur `dir-or-file-in-opt` (voulu), avertissements résiduels
  sur des fichiers de la bibliothèque standard (shebang sans bit x) et `hardening-no-pie` de l’interpréteur amont.
- **Thème sombre par défaut** + menu Affichage > Apparence (Ctrl+Maj+D) ; `conftest` applique le défaut ; captures
  régénérées en sombre (`outils/captures.py` suit `config.DEFAUTS`).
- **Banque OHP — possession** : `modules/ohp/possession.py` (lecture seule de `etat.sqlite`, URI `mode=ro`, jamais
  d'exception), `gui/pastilles.py` (icônes dessinées, couleurs `statut_*` du thème, contraste ≥ 4,5 testé),
  `gui/modele.py` : styles par ligne (couleur, icônes, bulles), `Progression` + `DelegueProgression` (mini-barre) ;
  filtre « À télécharger seulement », estimation des manquantes, légende, colonne « complet » des lots (clé objet /
  télescope / filtre / nuit si mobile, champs d'un objet fixe comptés ensemble) ; CLI `ohp inventaire --manquantes
  [--json]`, colonnes `possedee`/`statut_local`/`fichier_local` dans `ohp images --csv`. Tests (5 + GUI dans les 2 thèmes).
- **Cosmologie** : curseur log (0,001 → 1100, 1000 pas/décade, CURSEUR_MAX = 6041), repères dessinés sous le curseur
  (`ReperesCurseur`, géométrie du style), `calcul.courbes()` rend toutes les GRANDEURS, `calcul.interpoler()` (log-log),
  tableau mis à jour pendant le glissement, calcul exact au relâchement, synchro champ ↔ curseur, flèches = 10 pas.
  **Cause du non-redimensionnement** : sous 1500 px, le tableau réclamait toutes ses lignes (min 460 px) → panneau plus
  haut que la zone défilante → le splitter restait à sa hauteur de consigne et les courbes à leur minimum (220 px).
  Correction : `_disposer()` lit la hauteur du viewport de la QScrollArea, donne 55 % de la place visible aux courbes
  et le reste au tableau (qui défile). Tests : curseur (interpolation ≈ exact à 2e-3, exact à 1e-6 au relâchement),
  1024 → 1800 px (largeur + paint), 600 → 1000 px (hauteur).
- **Carte OSM nette** : `CarteMonde._zoom_tuiles()` → à DPR ≥ 1,5, tuiles z+1 dessinées à demi-taille (4 par tuile
  logique), `SmoothPixmapTransform`. Test : DPR simulé → clés z+1 demandées au cache, 4× plus de tuiles. Captures
  réelles 1× / 2× (`QT_SCALE_FACTOR=2`) : `/mnt/apps_pool/_transfert/coupole_carte_dpr/carte_{1x,2x}.png`.
- **Qualité des images** — profil sur 50 XISF T120 réels (`/mnt/zpool2/Astronomie/OHP_DU_ECU`, lecture seule) :
  **1,21 s/image** (lecture 0,06 s, analyse 1,15 s dont 80 % dans `_moffat`, 134 étoiles ajustées/image) ; bug trouvé :
  `OverflowError` dans `math.exp` sur une étoile réelle (pas LM aberrant) → bornes sur ln α et ln β + `try/except`
  par étoile. Optimisations : modèle vectorisé sur les 9 sous-points (`_moffat9`) → 0,44 s ; jacobien analytique
  (`_moffat9_jacobien`, vérifié contre les différences finies à 1e-5) → **0,33 s/image** ; 120 étoiles par image.
  Aucun O(n²) ni relecture du dossier par image (un seul `os.walk`). Nouveau `modules/qualite/moteur.py` :
  `ProcessPoolExecutor` spawn dimensionné par `parallele.planifier` (≤ 3 lecteurs si partage : `est_reseau` via
  /proc/mounts, `mount`, `GetDriveTypeW`), fenêtre 2×n (lecture recouverte), annulation par terminaison des processus,
  progression ≤ 10 Hz avec ETA et débit, CSV atomique après chaque image, cache `qualite.sqlite` (chemin, taille,
  mtime), `echantillon()` (première, dernière, milieu…), `planifier()` + `estimer_duree()` (3 images), GUI avec
  dialogue « gros dossier », CLI `--echantillon/--tout/--processus`. Tests sur 300 XISF synthétiques (6 lots) :
  complet, cache (0 refait), annulation < 30 s + reprise, échantillon, ETA décroissant, image illisible, CLI.
- **Ma machine** : ligne GPU reformulée (rien à installer), CuPy seulement en info-bulle + CONTRIBUTING.
- **Release unique** : job `nettoyer` de `release.yml` (vérifie les 10 actifs attendus, puis `gh release delete
  --cleanup-tag` des précédentes et suppression des artefacts) ; permissions `actions: write`. Après la 0.1.1 :
  suppression manuelle de v0.1.0 et de ses artefacts.
- Manuels FR/EN recompilés (34 p. chacun), CHANGELOG FR/EN 0.1.1, README, CONTRIBUTING.
- **v0.1.1 publiée** (run 37865797635, 8 jobs verts dont `nettoyer`) : 10 actifs, v0.1.0 et son tag supprimés par
  le job, 0 artefact restant. Essai de `coupole maj` (version simulée 0.0.9) dans ubuntu:24.04 nu : « aucune version »
  alors que la Release existe → **HTTPS impossible sans `ca-certificates`** (OpenSSL statique de CPython, autorités lues
  dans /etc/ssl/certs). → **0.1.2** : `ca-certificates` dans Depends, contrôle TLS dans l'essai du paquet de
  `release.yml`.
- **0.1.2 → 0.1.3** : le run de release v0.1.2 a échoué sur une apostrophe dans un commentaire de la chaîne bash de
  l'essai du `.deb` (`release.yml`) ; tag v0.1.2 retiré (aucune Release n'existait), correction, **v0.1.3** posé.
- 🔴 **BLOQUÉ PAR GITHUB (facturation)** : le run de release v0.1.3 (37868026954) et sa relance n'ont pas démarré :
  « The job was not started because recent account payments have failed or your spending limit needs to be
  increased » — minutes Actions du dépôt **privé** épuisées (macOS ×10, Windows ×2 ; 6 runs de tests + 3 de release
  dans la journée). **À faire par Kevin** : Settings > Billing & plans (relever la limite de dépense ou corriger le
  paiement), **ou rendre le dépôt public** (Actions gratuites, et de toute façon indispensable à la mise à jour
  automatique : l'API `releases/latest` répond 404 tant que le dépôt est privé — vérifié depuis l'interpréteur
  embarqué). Puis : `gh run rerun 37868026954` (ou `git push --delete origin v0.1.3 ; git push origin v0.1.3`).
  En attendant, **la Release v0.1.1 reste en ligne et complète** (10 actifs dont les deux `.deb`) ; son `.deb` ne
  déclare pas `ca-certificates` (installer `sudo apt install ca-certificates` à part sur un système minimal).
- Essais locaux du `.deb` 0.1.2 (avec `ca-certificates`) dans ubuntu:24.04 nu : installation, `coupole --version`,
  HTTPS OK (SIMBAD 200), désinstallation propre. Captures et profils : `/mnt/apps_pool/_transfert/coupole_deb_test/`
  (`gui_ubuntu_22_04.png`, `gui_ubuntu_24_04.png`) et `/mnt/apps_pool/_transfert/coupole_carte_dpr/`.

## 2026-10-09 — version 0.1.4 : second audit, usage réel à pleine échelle (rapport : `docs/AUDIT2_2026-10.md`)
Demande de Kevin : le premier audit avait raté le module Qualité (image par image sur la banque entière) ; trouver
**tous** les défauts de ce genre. Méthode : chaque fonction qui peut durer chronométrée sur la banque réelle
(`/mnt/zpool2/Astronomie/OHP_DU_ECU`, 7 625 XISF, lecture seule ; `_traitement` et index copiés dans
`/mnt/apps_pool/_transfert/coupole_audit2/`), sur un **partage réseau simulé** (FUSE, 2 ms par opération,
`outils/audit2/partage_simule.py`, conteneur avec `/dev/fuse`), et pour l'interface à **10 × la banque** (79 890
lignes) ; avant/après avec le code de 0.1.3 (`git archive 794092c`) dans le même conteneur.
- **33 constats, tous corrigés** (13 🔴, 13 🟠, 7 🟡). Les 5 plus coûteux :
  1. rangement final (à chaque session, même pour une image) sur partage : **60,7 s → 1,5 s** (un `stat` par
     fichier, parcours complet, 682 LOT.txt réécrits ; désormais seulement ce qui a changé) ;
  2. Qualité, relancer sur la banque déjà mesurée par un partage : **72 s → 2 s** (2–3 parcours, un `stat` + une
     requête par image et par passe ; QUALITE.csv réécrit après chaque image = O(n²)) ;
  3. tri / re-remplissage des tables : `lessThan` Python n·log n — 80 000 images **4,2 s → 0,16 s**, re-remplir trié
     **6,9 s → 0,3 s** ; table des images paresseuse ; en-tête Qt qui parcourait toutes les lignes à chaque dessin
     après « tout sélectionner » (0,77 s → 0,02 s, trouvé avec gdb, rendu identique au pixel) ;
  4. Réorganiser : O(n²) (61 M comparaisons) + séquentiel, sans progression ni arrêt : **243 s → 57 s** (borné par les
     disques), progression et Arrêter ajoutés ;
  5. base d'état : 3 validations SQLite par image (77 ms chacune sur partage) → groupées (1 s) ; chaîne de 48 images
     vers le partage **20,3 → 4,9 s** ; doublons de début de session 12,5 → 0,06 s.
- Autres : thème (1 s → 0,02 s ; 7,4 s à ×10), lots / estimation / possession / ciel en fond, carte du ciel (survol
  14 → 0,1 ms), tuiles (budget 30 ms, LRU), tracé (survol 30 → 1 ms), médoïdes et groupement des champs en numpy
  (résultats identiques), nouveautés en lecture seule, **bug** de tri textuel de la table Qualité.
- Tests : `tests/test_echelle.py` (21 tests : budgets tolérants à 80 000 lignes, compteurs exacts d'écritures, de
  validations, de lectures) ; tests d'interface adaptés (anti-rebond, calculs en fond). Validation locale (copie du
  dépôt sans `build/` ni `dist/`, `pip install ".[test]"`, offscreen) : **python:3.12-slim 278 réussis, 11 sautés,
  code 0 ; python:3.10-slim 278 réussis, 11 sautés, code 0** ; `test_adaptatif` + `test_gui_robustesse` +
  `test_echelle` à `QT_SCALE_FACTOR=1.5` et `2` : 36 réussis, code 0 (sous 3.12 et 3.10). CI GitHub non utilisée
  pour cette version (minutes du dépôt privé épuisées) ; *correction 0.1.7 : depuis le passage du dépôt en
  public, la CI `tests.yml` (Linux, Windows, macOS × 3.10, 3.12) tourne à chaque poussée sur `main` (6/6 depuis le
  commit `94b34be`).*
- Manuels FR/EN : traitement sur partage, réorganiser (progression, Arrêter), Qualité (cache, CSV toutes les 5 s),
  tableau des mesures du second audit ; recompilés. Aide : info-bulles Arrêter / Réorganiser.
- Reste proposé (§ 5 du rapport) : gel de 0,8 s au chargement à ×10 (0,17 s à l'échelle réelle), tri sur colonnes
  sans clé rapide à ×10, Windows non vérifiable ici (§ 6).
- **Aucun tag posé** (CI de publication bloquée par la facturation GitHub du dépôt privé : à décider par Kevin).

## 2026-10-09 — version 0.1.5 : les deux lenteurs restantes du second audit (rapport : `docs/AUDIT2_2026-10.md` § 8)
Mesures à 10 × la banque (79 890 lignes) et sur la banque réelle, destination copiée de la banque (possession,
lots, anomalies réels), avant (0.1.4) / après dans le même conteneur `python:3.12-slim` ; copies et scripts de travail
dans `/mnt/apps_pool/_transfert/coupole_audit3/`.
- **Gel au chargement** : le gel de 0,55–0,8 s n'était dans aucun créneau Python (tous < 40 ms) mais dans la
  concurrence pour le GIL : anomalies, possession et carte du ciel calculées par trois fils pendant le premier dessin
  des tables (chaque rappel Qt → Python attend le GIL), puis le fil de chargement pendant la mise en place de la
  fenêtre. Corrigé : tout est calculé en série par le fil de chargement avant la remise de l'inventaire
  (`precharger`), affiché par étapes d'un tour de boucle, et le chargement part 200 ms après le premier dessin.
  Plus long gel ×10 **549–572 → 54–66 ms** ; n réel 155 → 40–52 ms ; catalogue complet ~0,2–0,3 s plus tard.
- **Tri heure du site / drapeaux** : clés entières précalculées en fond, `numpy.argsort` stable ; toutes les colonnes
  ont une clé rapide (rangs) ; le double tri de `sortByColumn` n'est plus refait. ×10 : **757–775 → 52–53 ms**
  (heure du site), ~0,6 s → 49–56 ms (drapeaux), autres colonnes 35–65 ms.
- **Rien d'affiché ne change** : 41 empreintes par échelle (cellules, objets, anomalies, ciel, lots, ordre après 36
  tris) identiques 0.1.4 / 0.1.5 sur la banque réelle et à ×10 (`outils/audit2/mesure_ordre_tri.py`).
- Tests : `test_echelle.py` 21 → 25 (chargement sans silence > 0,3 s, tris < 0,45 s, clés = ordre des cellules,
  `permutation_triee` = `sorted`) ; échouent sur le code 0.1.4 (0,64 s ; 0,81 s) sauf l'équivalence des clés.
  Validation locale (copie sans `build/` ni `dist/`, `pip install ".[test]"`, offscreen) : **python:3.12-slim 282
  réussis, 11 sautés, code 0 ; python:3.10-slim 282 réussis, 11 sautés, code 0** ; `test_adaptatif` + `test_echelle`
  à `QT_SCALE_FACTOR=1.5` et `2` : 33 réussis, code 0 (3.12 et 3.10).
- **Aucun tag posé.**

## 2026-10-09 — version 0.1.6 : réglages conservés d'une fermeture à l'autre
Demande de Kevin : tous les réglages de personnalisation et tous les chemins saisis retrouvés au lancement suivant.
- Mécanisme unique : `coupole/core/etat_interface.py` (fichier `interface.json` versionné, lecture tolérante, écriture
  atomique seulement si quelque chose a changé, existence des chemins vérifiée dans un fil démon) et
  `coupole/gui/memoire.py` (éléments « suivis » : valeur rétablie à la construction, LUE au moment d'écrire ;
  minuteur unique : au plus une écriture toutes les 2 s, plus une à la fermeture ; `Reglages.differer` pour les
  réglages de `reglages.json` tapés au clavier). Les choix de traitement restent dans `reglages.json` (nouvelles clés
  `ohp_garder_doublons`, `ohp_garder_fits`, `ohp_mode_astap`, `ohp_verifier_qualite`), la disposition dans
  `interface.json`.
- Conservé : fenêtre (taille, position, écran, maximisée ; garde-fous écran disparu / hors écran → recentrée, trop
  grande → ramenée sur l'écran), taille des dialogues (+ onglet des Préférences), module, onglet OHP, séparateurs
  (catalogue, Qualité, Sites, Spectres), colonnes de tous les tableaux triables (largeur une fois choisie à la souris,
  ordre, tri), filtres et recherche du catalogue, nuit/filtre/objets choisis (appliqués quand les listes se
  remplissent), filtres anomalies et ciel, onglet Traitement (dossier dès la frappe, format, langue des noms, doublons,
  FITS, mode ASTAP, qualité), Qualité (dossier, échantillon, N), Spectres (dossier d'ouverture, 10 récents, axe),
  Cosmologie (modèle, H0/Ωm perso gardés même en repassant par Planck, Ωk, z, SH0ES, nouvelle échelle log/lin des
  courbes), Sites (site, zoom/centre de la carte, carte en ligne), dossiers de tous les dialogues de fichiers.
- Non conservé volontairement : traitement en cours (jamais relancé seul), sélection d'images à traiter, tableau de
  la Cosmologie (disposition automatique), séparateur de la Cosmologie (orientation automatique selon la largeur).
- Réinitialisation : Préférences > « Réinitialiser la disposition » (reconstruit l'interface tout de suite ; si un
  traitement tourne : effacé, plus rien d'écrit, origine au prochain lancement) ; `coupole --reinitialiser-interface`.
- Tests : `tests/test_reglages_conserves.py` (11) ; `conftest.py` efface la disposition avant chaque test.
  Validation (copie sans `build/` ni `dist/`, `pip install ".[test]"`, offscreen) : **python:3.12-slim 294 réussis,
  11 sautés, code 0 ; python:3.10-slim 294 réussis, 11 sautés, code 0** ; `test_adaptatif` + `test_reglages_conserves`
  + `test_gui_robustesse` + `test_echelle` à `QT_SCALE_FACTOR=1.5` et `2` : 51 réussis, code 0 (3.12 et 3.10).
  Un plantage natif isolé (1 suite complète sur ~10, sous 3.12, non reproduit ensuite) : à surveiller. *→ Cause
  trouvée et corrigée en 0.1.7 (ramasse-miettes cyclique dans un fil de calcul, voir plus bas).*
- Manuels FR/EN : section « Réglages conservés » (3.2), option `--reinitialiser-interface` dans les tableaux générés,
  captures Préférences / Spectres / Cosmologie refaites ; recompilés. CHANGELOG FR puis EN.
- **Aucun tag posé** (publication par Kevin).

## 2026-10-09 — version 0.1.7 : cause du plantage natif intermittent trouvée et corrigée
Le plantage « isolé » de la 0.1.6 n'était pas isolé : **reproduit 8 fois**, toujours à la même place.
- Reproduction : image `python:3.12-slim` + `gdb` (`/mnt/apps_pool/claude-code/coupole-crash/`, `boucle.sh`), copie
  sans `build/`/`dist/`, `pip install`, offscreen, `PYTHONFAULTHANDLER=1`, chaque suite sous
  `gdb -batch -ex run -ex 'thread apply all bt'`, 6 à 9 suites en parallèle (charge 8–10 sur 12 fils). Avant
  correction : suite complète **1 plantage sur 49** ; série `test_reglages_conserves` + `test_gui_robustesse` +
  `test_interface` **7 plantages sur 36 (≈ 20 %)**. Les 8 plantages tombent au même endroit ; les 7 relevés
  avec `-s` (sans quoi pytest avale la trace Python) ont la même signature : SIGABRT par `qFatal` de PyQt6 (`pyqt6_err_print` dans `PyQtSlotProxy::unislot`, slot d'un
  `QTimer`) après `RuntimeError: wrapped C/C++ object of type QLineEdit has been deleted` dans
  `Panneau._etape_suivante → _charger_possession → _possession_prete → _filtrer_objets` (`self.recherche.text()`),
  pendant `_ouvrir()` de `test_aucune_ecriture_disque_pendant_la_frappe`.
- **Cause** : le panneau en cause est celui de la fenêtre du test PRÉCÉDENT. Fermée (`close()`, pas détruite), elle
  reste retenue par des fermetures (`memoire.suivre(..., lambda: …self…)`) ; la fixture `propre` remet la mémoire à
  zéro → la fenêtre n'est plus qu'un **cycle de références**, que seul le ramasse-miettes cyclique libère. Celui-ci
  se déclenche dans le fil qui alloue quand le seuil est franchi : ici le fil `Tache` qui charge l'inventaire de la
  NOUVELLE fenêtre (piles natives : fils « Dummy »/`Tache` en plein `gc`). Le destructeur C++ de l'ancienne fenêtre
  (fenêtre sans parent : possédée par Python) tourne alors **dans ce fil de calcul**, widget après widget, pendant
  que le fil graphique sert encore le minuteur d'étapes (enfant du panneau, pas encore détruit) → champ déjà
  détruit → exception dans un slot → qFatal. Démontré à part (`exp2.py`) : `gc.collect()` dans un fil ordinaire
  détruit la fenêtre fermée. Dans l'application, même risque pour tout dialogue ou panneau devenu cycle (langue
  changée, Préférences fermées) ; l'application, elle, pose un `sys.excepthook` (exception journalisée), mais une
  destruction concurrente peut aussi écrire en mémoire libérée (SIGSEGV).
- Exclu : signaux de `Tache` vers des widgets détruits (protégés depuis l'audit), pools de processus, `QThread`
  détruit en marche (Qt 6 attend `isInFinish`), concurrence `json.dumps` / réglages (clés existantes seulement).
- **Correction (application)** : `coupole/gui/fil_graphique.py` — `installer_ramasse_miettes()` coupe le
  ramassage automatique et le refait toutes les 100 ms par un `QTimer` du fil graphique (`app.py` ; procédé de
  pyqtgraph) : un objet Qt meurt toujours dans le fil graphique. Ramassage complet borné (≥ 10 s d'écart, ≤ 2 % du
  temps) pour ne pas geler à 80 000 lignes. En plus : `Panneau.arreter()` (OHP) vide les étapes en attente et arrête
  ses minuteries ; `Memoire` écrit par un slot protégé (`_ecrire_protege`).
- **Garde permanente en mode test** (`installer_garde()`, posée par `conftest.py`, ou `COUPOLE_GARDE_FIL=1`) :
  méthodes d'affichage non virtuelles courantes (`setText`, `update`, `showMessage`, `setValue`…) → `RuntimeError`
  hors du fil graphique ; avertissements Qt « another thread / different thread / Destroyed while thread is still
  running » relevés ; ramassage cyclique hors du fil graphique relevé (`gc.callbacks`) ; fixture autouse qui fait
  échouer le test et ramasse les fenêtres laissées, dans le fil graphique, avant le suivant.
- Tests `tests/test_fil_graphique.py` (+6) : widget en cycle + fil qui alloue → détruit dans `MainThread` ; **ordre
  exact du plantage** (vraie fenêtre fermée avec une étape en attente, mémoire remise à zéro, fil de calcul qui
  alloue pendant que le fil graphique tourne) ; cycles toujours libérés ; les trois volets de la garde. Sur le code
  0.1.6 (ramassage automatique), 3 échouent (fenêtre détruite dans `fil-de-calcul` / `Dummy-1`).
- `test_chargement_a_dix_fois_la_banque_sans_gel` : budget 1,2 s sur la CI (variable `CI` ; ×3 la mesure CI la plus
  lente, 0,39 s sur macOS 3.10, comme le test du filtre), 0,3 s en local (garde la détection de la régression 0.1.4).
- Ordre aléatoire (`pytest-randomly`, graine notée) : aucun plantage, mais deux dépendances d'ordre des TESTS
  corrigées — un test de la CLI (`--lang en`) laissait l'anglais au suivant (`conftest.py` remet le français avant
  chaque test) ; `test_fenetre_fermee_…` attend que plus aucune `Tache` ne tourne (des tests remplacent
  `Tache.start` : leurs tâches jamais lancées restent dans `_actives`).
- Validation après correction (code final, mêmes conteneurs sous `gdb`, 8 à 10 suites en parallèle, charge ≈ 14) :
  **python:3.12-slim 42 suites complètes consécutives sans plantage (301 réussis, 11 sautés chacune)** ;
  **python:3.10-slim 10/10** ; ordre aléatoire 3.12 : 6/6 (graines notées dans `out_v1`/`out`), plus 12 passages
  aléatoires sans plantage avant les deux corrections de tests ; série la plus exposée (celle à 20 % de plantages)
  **45/45** ; `test_adaptatif` + `test_reglages_conserves` + `test_gui_robustesse` + `test_echelle` +
  `test_fil_graphique` à `QT_SCALE_FACTOR=1.5` et `2` : 57 réussis, code 0 (3.12 et 3.10).
- **Aucun tag posé** (publication v0.1.6 en cours, non touchée).
