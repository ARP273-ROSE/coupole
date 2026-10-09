# PROGRESSION — Coupole

État d'avancement, tenu à jour pendant le développement (reprise possible).

## 2026-10-08 — démarrage
- [x] Lecture complète de dossier du traitement de référence (scripts d'origine) (README, Inventaire.pdf, scripts, TEST.md, index).
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

## 2026-10-08 — performance mesurée (`outils/mesures.py`, processeur à 6 cœurs, NVMe)
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
- Manuels LaTeX au format maison (préambule dérivé de préambule LaTeX maison) :
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

## 2026-10-09 — version 0.1.1 : paquet .deb, Release unique, retours d'utilisateur sur la 0.1.0
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
- **Essais réels du .deb** (`<dossier de travail>/coupole_deb_test/`) : ubuntu:22.04 et ubuntu:24.04 nus, `apt-get
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
  réelles 1× / 2× (`QT_SCALE_FACTOR=2`) : `<dossier de travail>/coupole_carte_dpr/carte_{1x,2x}.png`.
- **Qualité des images** — profil sur 50 XISF T120 réels (`/srv/banque/OHP_DU_ECU`, lecture seule) :
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
  dans la journée). **À faire par le mainteneur** : Settings > Billing & plans (relever la limite de dépense ou corriger le
  paiement), **ou rendre le dépôt public** (Actions gratuites, et de toute façon indispensable à la mise à jour
  automatique : l'API `releases/latest` répond 404 tant que le dépôt est privé — vérifié depuis l'interpréteur
  embarqué). Puis : `gh run rerun 37868026954` (ou `git push --delete origin v0.1.3 ; git push origin v0.1.3`).
  En attendant, **la Release v0.1.1 reste en ligne et complète** (10 actifs dont les deux `.deb`) ; son `.deb` ne
  déclare pas `ca-certificates` (installer `sudo apt install ca-certificates` à part sur un système minimal).
- Essais locaux du `.deb` 0.1.2 (avec `ca-certificates`) dans ubuntu:24.04 nu : installation, `coupole --version`,
  HTTPS OK (SIMBAD 200), désinstallation propre. Captures et profils : `<dossier de travail>/coupole_deb_test/`
  (`gui_ubuntu_22_04.png`, `gui_ubuntu_24_04.png`) et `<dossier de travail>/coupole_carte_dpr/`.

## 2026-10-09 — version 0.1.4 : second audit, usage réel à pleine échelle (rapport : `docs/AUDIT2_2026-10.md`)
Demande d'un utilisateur : le premier audit avait raté le module Qualité (image par image sur la banque entière) ; trouver
**tous** les défauts de ce genre. Méthode : chaque fonction qui peut durer chronométrée sur la banque réelle
(`/srv/banque/OHP_DU_ECU`, 7 625 XISF, lecture seule ; `_traitement` et index copiés dans
`<dossier de travail>/coupole_audit2/`), sur un **partage réseau simulé** (FUSE, 2 ms par opération,
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
- **Aucun tag posé** (CI de publication bloquée par la facturation GitHub du dépôt privé : à décider par le mainteneur).

## 2026-10-09 — version 0.1.5 : les deux lenteurs restantes du second audit (rapport : `docs/AUDIT2_2026-10.md` § 8)
Mesures à 10 × la banque (79 890 lignes) et sur la banque réelle, destination copiée de la banque (possession,
lots, anomalies réels), avant (0.1.4) / après dans le même conteneur `python:3.12-slim` ; copies et scripts de travail
dans `<dossier de travail>/coupole_audit3/`.
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
- CI `tests.yml` du commit `c193ab5` : **6/6** (Linux, Windows, macOS × 3.10, 3.12), étape « Liens du guide ASTAP » comprise. Premiers passages rouges : tests sous Windows (police large : colonnes au contenu plus larges que la vue → défilement admis ; hauteur du tableau empilé qui oubliait l’ascenseur horizontal : corrigé dans le code) et SourceForge en 403 pour les machines de CI (repli sur le flux RSS du dossier).
- **Aucun tag posé.**

## 2026-10-09 — version 0.1.6 : réglages conservés d'une fermeture à l'autre
Demande d'un utilisateur : tous les réglages de personnalisation et tous les chemins saisis retrouvés au lancement suivant.
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
- CI `tests.yml` du commit `f2cf35c` : **6/6** (Linux, Windows, macOS × 3.10, 3.12) ; sous Windows, le test UNC réel (`\\localhost\C$\…`) passe. Premier passage rouge sous Windows : tests seulement (possession simulée avec un dossier non absolu, ignorée comme périmée ; « : » interdit dans un nom de dossier).
- **Aucun tag posé** (publication par le mainteneur).

## 2026-10-09 — version 0.1.7 : cause du plantage natif intermittent trouvée et corrigée
Le plantage « isolé » de la 0.1.6 n'était pas isolé : **reproduit 8 fois**, toujours à la même place.
- Reproduction : image `python:3.12-slim` + `gdb` (`<dossier de travail>/coupole-crash/`, `boucle.sh`), copie
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
  `test_fil_graphique` à `QT_SCALE_FACTOR=1.5` et `2` : 57 réussis, code 0 (3.12 et 3.10). CI `tests.yml` du
  commit `95145bd` : **6/6** (Linux, Windows, macOS × 3.10, 3.12).
- **Aucun tag posé** (publication v0.1.6 en cours, non touchée).

## 2026-10-09 — 0.1.8 : explorateur du système, possession visible, lanceur par lien
Retours d'usage d'un utilisateur (Manjaro, KDE Plasma, paquet autonome 0.1.7, dossier de sortie `/mnt/partage/OHP_DU_ECU`).
- **Dialogue de fichiers générique, en anglais, sans le NAS** : cause = le Qt du paquet ne peut pas charger le greffon
  `kde` de plasma-integration (compilé pour le Qt du système) ; Qt prend alors son thème KDE intégré, sans dialogue
  natif ; le portail n'est choisi d'office que dans Flatpak/Snap. `gui/plateforme.py` : avant `QApplication`, si
  `QT_QPA_PLATFORMTHEME` n'est pas posé, sonde sans Qt (fichier de service D-Bus ou unité systemd du portail, fichiers
  `*.portal` avec `FileChooser`, sinon `NameHasOwner` par `dbus-send`/`gdbus` borné à 1 s) → `xdgdesktopportal` ;
  sinon bureau GTK + `libqgtk3` + GTK 3 → `gtk3` ; sinon dialogue Qt traduit, barre latérale complétée
  (`core/chemins.emplacements_systeme` : gvfs et ses partages, cifs/nfs/sshfs de `/proc/mounts`, `/run/media/$USER`,
  `/media`, `/mnt`). Tous les choix de fichiers par `gui/fichiers.py` (parent transmis, `DontUseNativeDialog`
  seulement si Préférences > « Boîtes de dialogue de fichiers » = Qt). Windows/macOS : rien à choisir, natifs.
- **Essai réel** (conteneur ubuntu:24.04, Xvfb, `dbus-run-session`, `xdg-desktop-portal` 1.18) : décision
  `portail` ; `dbus-monitor` voit `org.freedesktop.portal.FileChooser.OpenFile` avec la fenêtre parente
  `x11:…`, le titre, l'option `directory` et des filtres en français ; `xwininfo` montre « Dossier de sortie — Portal »
  dans **xdg-desktop-portal-kde** (XDG_CURRENT_DESKTOP=KDE) et « Dossier de sortie » dans xdg-desktop-portal-gtk
  (GNOME) ; `QT_QPA_PLATFORMTHEME=gtk3` : dialogue GTK dans le processus ; préférence Qt : dialogue Qt.
- **Traductions de Qt** : `qtbase_fr.qm` par `QTranslator` (dossier `QLibraryInfo.TranslationsPath`), rechargé au
  changement de langue. Constat dans le dialogue de repli : Qt 6 ne traduit pas « &Look in: » ni « Files of &type: »
  (absents du catalogue) → `QTranslator` complémentaire (retour `None` = chaîne nulle ; une chaîne vide masquait
  TOUTES les autres traductions). Paquets : `controler_qt` dans `build_unix.py` (greffons portail/GTK, `qtbase_fr`,
  `qt_fr`) et `build_package.py` (`qwindows.dll`, traductions) — la construction échoue s'il en manque ; `.deb`
  vérifié dans le conteneur nu de `release.yml` ; le paquet Windows charge les traductions à l'essai.
- **Chemins réseau** : URI SQLite d'un UNC (`file://serveur/…` refusée par SQLite → `file:////serveur/…`),
  `chemin_os` UNC long (`\\?\UNC\…`, l'ancien préfixe donnait `\\?\\\serveur…`), gvfs/kio-fuse reconnus comme
  partages. Test UNC réel sous Windows (`\\localhost\C$\…`, sauté si inaccessible).
- **Possession visible** (Banque OHP) : pastille d'état agrégé (`Possession.etat_agrege` : echec > complet > partiel >
  absente) sur la première colonne affichée, nom coloré (`statut_partiel` ajouté : contraste ≥ 4,5 vérifié avec
  `texte_doux`), info-bulle ; colonne « possédé » déplacée après « objet » (ordre logique inchangé →
  largeurs/tri gardés ; `memoire.entete(version=2)` migre l'ordre d'origine non modifié), largeurs auto de type/nom
  bornées pour qu'elle reste visible, tri par état (`ProgressionEtat`) ; légende sous les deux listes avec « en
  partie » ; résumé de possession ; messages centrés dans les tables vides (`VueTableau.message_vide`, dessiné
  dans la zone) ; premier objet choisi au premier lancement ; changement de dossier → relecture, résultat périmé
  ignoré, message dans la barre d'état.
- **Lanceur** : `Coupole.sh` suit les liens (boucle `readlink`, sans `-f`) ; `installer.sh` généré par
  `build_unix.py` (plus dans `release.yml`), pose `~/.local/bin/coupole`, signale le PATH ; `maj.reparer_lanceur()`
  réécrit au démarrage le lanceur d'un paquet ≤ 0.1.7 (la mise à jour ne touche que `app/`). `install.sh` posait déjà
  ses liens (venv) : inchangé. `release.yml` : essai par lien et lien de lien (Linux, .app macOS), installeur dans un
  HOME vide.
- Tests : `test_dialogues_systeme.py` (27, certains propres à Linux/Unix ou à Windows), `test_catalogue_possession.py` (16) ; tests existants
  adaptés (pastille en tête de ligne, `fichiers.choisir_*` simulés au lieu de `QFileDialog.get*`).
- Validation locale : **python:3.12-slim 345 réussis, 12 sautés, code 0 ; python:3.10-slim 345 / 12, code 0**.
  Manuels FR/EN (38 p.) recompilés (section « Choisir un fichier ou un dossier, dossier sur un NAS », possession,
  dépannage, installeur), captures Catalogue et Préférences refaites.
- CI `tests.yml` du commit `f2cf35c` : **6/6** (Linux, Windows, macOS × 3.10, 3.12) ; sous Windows, le test UNC réel (`\\localhost\C$\…`) passe. Premier passage rouge sous Windows : tests seulement (possession simulée avec un dossier non absolu, ignorée comme périmée ; « : » interdit dans un nom de dossier).
- **Aucun tag posé** (publication par le mainteneur).

## 2026-10-09 — version 0.1.9 : Qualité sur un vrai partage SMB, compatibilité vérifiée, métadonnées PixInsight
Retours d'utilisateur (Manjaro, 0.1.8, `/mnt/partage/OHP_DU_ECU/09_Galaxies` sur un partage SMB). Détail et
mesures : `docs/AUDIT2_2026-10.md` § 9.
- **Inventaire Qualité** : vrai Samba en conteneur, client cifs du noyau, `tc netem` ; arborescence réelle de la
  banque en fichiers vides. Cause : SQLite n'écrit pas à travers les verrous SMB (« database is locked », fichier de
  0 octet — le même que sur le NAS, créé par l'utilisateur à 13 h 33) ; trois ouvertures du cache × 30 s = **90,4 s** avant
  la première mesure (92,7 s à 10 ms). Cache local pour un partage, repli en 3 s ; inventaire producteur/consommateur
  (`moteur.inventorier`, `parcours.parcourir`) ; dossiers des lots d'après INDEX_LOTS.csv / la base d'état ; dates
  tirées de `scandir` ; 32 fils sur un partage ; échantillon mesuré d'abord, question non modale. **Après : inventaire
  0,13–0,22 s (0 ms), 0,24–0,56 s (10 ms), 0,57–1,05 s (20 ms) ; premier résultat 0,2–0,6 s.** `strace` : 0 ouverture,
  ≈ 1 `stat` par image (déjà en 0.1.8). Outil : `outils/audit2/mesure_inventaire_qualite.py`.
- **Non corrigé, à décider** : la base d'état du pilote (`etat.sqlite`) sur un partage cifs par défaut a le même
  défaut (« database is locked ») ; `vfs=unix-dotfile` fonctionne (essai) mais un verrou orphelin bloquerait.
- **En-têtes de tableaux** : `EnTete` garde chaque section au moins à la largeur de son titre, info-bulle du titre ;
  `equiper_entete` pour les QTableWidget ; info-bulles des QTabWidget sur la barre d'onglets. Tests génériques
  (tous les tableaux visibles, 1 366 / 2 000 px, échelles 1,5 et 2 ; aucun conteneur avec info-bulle propre).
- **Cosmologie** : colonnes au contenu, disposition auto (hystérésis 1 550 / 1 450) / côte à côte / empilée (menu
  Affichage + liste), séparateur gardé par disposition ; unités km s⁻¹ Mpc⁻¹ (CSV et cp1252 en ASCII ; test anti
  « x/y/z »). Captures des deux dispositions.
- **ASTAP** : D80 en zip inexistant (404) ; extraction du .deb vérifiée sur le vrai paquet (md5 1d0683cb…, 1 476
  tuiles) ; paquets Arch examinés (GTK2 non résolu, gtk3 dans extra, astap_cli statique) ; astap_cli préféré partout ;
  test des 30 liens en CI (`COUPOLE_TEST_LIENS=1`, étape dédiée de `tests.yml`).
- **Compatibilité** (`core/logiciels.py`, sources citées) : Siril AppImage 1.2.0/1.2.6 sans XISF, 1.4.0/1.4.4 bit à
  bit mais flottants hors [0, 1] ; paquets Debian 13 / Ubuntu 24.04 sans XISF ; N.I.N.A. 3.2 (code) sans zstd,
  flottants supposés [0, 1] ; ASTAP XISF non compressé seulement ; PCL inchangé ; spécification XISF 1.0 rév. 1
  (sept. 2026), XSD identique. Écart noté : `Observation:Center` = centre de la solution (rév. 1 : pointage).
- **XISF compatible** (`xisf16`) : UInt16 + piédestal 1 000 ADU, zlib+sh ; perte mesurée sur 66 poses de la banque
  (`outils/audit2/mesure_perte_uint16.py`). Sans piédestal : 99,75 % de pixels perdus sur une pose de 10 s.
- **Ouvrir** : double-clic / menu contextuel (Banque OHP images, objets, lots ; Qualité) ; « Ouvrir avec » selon la
  table ; emplacement par D-Bus/Finder/Explorateur. Colonne « lots » et répartition (possédé ≠ empilable).
- **PixInsight / N.I.N.A.** : FOCALLEN accordé à l'échelle, propriétés Instrument:* (spéc. rév. 1) ; encadré de
  l'onglet Lots, colonnes, LOT.txt ; `coupole ohp metadonnees --reecrire` (bloc recopié, relu ; base d'état mise à
  jour). Fichiers d'essai `tests/donnees/`.
- Validation locale (copie sans build/dist, `pip install ".[test]"`, offscreen) : **python:3.12-slim 371 réussis,
  13 sautés, code 0 ; python:3.10-slim 371 / 13, code 0** ; `test_adaptatif`, `test_echelle`, `test_gui_robustesse`
  à `QT_SCALE_FACTOR` 1,5 et 2 : 47 réussis, code 0 (les deux versions). Tests de référence (`COUPOLE_REFERENCE`)
  passés à part. Manuels FR/EN (41 p.) recompilés, temporaires supprimés ; captures refaites (Lots avec l'encadré,
  Cosmologie côte à côte et empilée, Traitement avec « qui lit quoi »).
- CI `tests.yml` du commit `c193ab5` : **6/6** (Linux, Windows, macOS × 3.10, 3.12), étape « Liens du guide ASTAP » comprise. Premiers passages rouges : tests sous Windows (police large : colonnes au contenu plus larges que la vue → défilement admis ; hauteur du tableau empilé qui oubliait l’ascenseur horizontal : corrigé dans le code) et SourceForge en 403 pour les machines de CI (repli sur le flux RSS du dossier).
- **Aucun tag posé.**

## 2026-10-09 — version 0.1.10 : base d'état sur un partage réseau (le « à décider » de la 0.1.9)
Le dossier de sortie d'un utilisateur est sur le partage (`/mnt/partage/OHP_DU_ECU`, base `_traitement/etat.sqlite`
partagée avec le NAS) : sous Linux, télécharger, *Tout télécharger* ou réorganiser vers lui échouait. Détail :
`docs/AUDIT2_2026-10.md` § 10.
- **Reproduit** (vrai Samba, cifs par défaut, banc `outils/audit2/samba/`) : `Etat()` → « database is locked » en
  60,1 s, `etat.sqlite` de 0 octet ; lecture seule (possession, nouveautés, anomalies) : fonctionne.
- **Décision** : pas de VFS `unix-dotfile` (verrou orphelin) ; **base de travail locale** (`core/base_partagee.py`) :
  `<cache>/bases/<clé du chemin>/etat.sqlite` + `.sync.json` ; partage détecté (`est_reseau`, déplacée dans
  `core/chemins.py`) ou essai d'écriture en échec (3 s, fichier de 0 octet retiré) ; recopie atomique (instantané
  par l'API de sauvegarde, `integrity_check`, temporaire sur le partage relu et comparé SHA-256, `os.replace`) toutes
  les 30 s (fil), en fin de session, à l'arrêt/annulation ; compteur `meta.version_partage`.
- **Démarrage** : partage plus récent → repris (réuni si une recopie a été remplacée par un autre écrivain) ;
  écritures non recopiées (plantage) → recopiées ; les deux → `Divergence`, rien d'écrasé, **fusion** (ok > doublon
  > echec > en_cours, puis le plus récent ; essais max ; empreintes réunies ; deux bases d'origine gardées) :
  question dans l'interface, `coupole ohp fusionner` en ligne de commande (code 5 sinon). Divergence pendant la
  session : plus de recopie, message, fusion au lancement suivant. `-journal` présent sur le partage : recopie
  remise.
- Lecteurs (possession, nouveautés, anomalies, inventaire Qualité) : base de travail si à jour. `metadonnees.maj_etat`
  passe par la même base. Qualité (`qualite.sqlite`) : cache local depuis 0.1.9, sans recopie ; JOURNAL.txt, CSV,
  LOT.txt écrits directement. Messages journal + barre d'état (« Dossier sur un partage réseau : base de travail
  locale, recopiée sur le partage toutes les 30 s »).
- **macOS/Windows** (raisonné, § 10.4) : smbfs et UNC/lecteur réseau passent par la même base de travail ; Windows
  vérifié par la CI (`\\localhost\C$`).
- Mesuré (vrai Samba) : ouverture 0,02 s (contre 60,1 s puis erreur), recopie 0,02–0,04 s (base de 1,3 Mo).
  **Essai réel** : 3 images de (914) Palisana depuis `tap-ufe.obspm.fr` vers `/mnt/partage/OHP_DU_ECU_essai` (Samba de
  test) : 3 converties, base du partage 3 `ok`, `integrity_check` ok, aucun temporaire ; relance : rien à refaire.
  Rien écrit dans `/srv/banque`.
- Tests : `tests/test_base_partagee.py` (20 + vrai cifs si `COUPOLE_TEST_SMB` + UNC Windows). Manuels FR/EN :
  section « Dossier de sortie sur un partage réseau », dépannage (3 lignes), `nobrl` plus nécessaire ; aide de la
  Banque OHP ; CHANGELOG FR/EN ; `\texttt` cassé (tabulation) corrigé dans le manuel FR.
- Validation locale (copie sans build/dist, `pip install ".[test]"`, offscreen) : **python:3.12-slim 389 réussis,
  15 sautés, code 0 ; python:3.10-slim 389 / 15, code 0**. Banc Samba (`outils/audit2/samba/essai.sh`, conteneurs
  retirés ensuite) : tests avec `COUPOLE_TEST_SMB` réussis, essai réel refait (3 converties, base du partage intègre).
- CI `tests.yml` du commit `09f8ae8` : **6/6** (Linux, Windows, macOS × 3.10, 3.12) ; sous Windows, `test_chemin_unc_reel` de la base de travail (`\\localhost\C$`) passe.
- **Aucun tag posé.**

## 2026-10-09 — version 0.1.11 : copie d'un ancien traitement, menus, dialogues, Qualité sur les poses d'un utilisateur
Retours d'utilisateur (Linux/KDE, 0.1.10, `/mnt/partage/OHP_DU_ECU` = copie produite par `ohp_xisf.py` avant Coupole).
- **Rien à ouvrir sur des objets possédés** : la base de cette copie note `final` = « /srv/ancien/OHP_DU_ECU/… »
  (conteneur d'alors) ; `possession` le rendait tel quel (chemin absolu étranger) → `chemin_image` inexistant,
  `dossier_objet` vide. Nouveau `modules/ohp/emplacements.py` : `info.chemin` relatif → `final` dans la sortie →
  `journal.csv` (url, puis fichier_source non ambigu ; cache par mtime/taille) → ancienne racine (`staging` avant
  `_traitement`) ou dossier de type → nom attendu dans le dossier du lot (numérotation « _2 » du rangement, à la
  demande). `Possession.lire_avec_infos` résout en fond (infos : `final` local en mémoire pour la complétude des lots),
  `a_migrer` → `emplacements.migrer` en fond (BasePartagee, PRAGMA journal_mode=DELETE, jamais pendant un traitement).
  `dossier_objet` : repli `dossier_attendu(<sortie>/<type>/<objet>)`. `metadonnees --reecrire` note les chemins
  (fichiers trouvés, puis journal). Pilote : `final` étranger rapporté avant le rangement (sinon `os.replace` d'un
  staging absent et `journal.csv` réécrit avec « ../.. ») ; `lots.ranger` note `chemin`, saute un staging absent ;
  `ecrire_journal` : `chemin`, sinon `final` dans la sortie, sinon la ligne précédente.
- **Vraie copie (lecture seule, base et journal copiés dans un dossier de travail ; rien écrit dans /srv/banque)** :
  7 625 images résolues par le journal en 0,34 s ; 300 tirées au sort présentes sur le disque ; ancienne racine =
  journal 7 625/7 625 ; nom attendu = journal 100/100 (0,2 s) ; migration d'une copie de la base sur « partage »
  simulé : 7 625 en 0,78 s, relue ensuite sans journal (origine « base »).
- **Défauts trouvés en passant** : la base d'`ohp_xisf.py` est en WAL → écritures dans le `-wal`, base principale
  inchangée, la recopie vers le partage ne voyait « rien de neuf » (aussi `metadonnees.maj_etat` en 0.1.10) → DELETE
  avant d'écrire ; `_copier_base` reprend un `-wal` ; recopie refusée si `-wal` non vide, `-wal` vide et `-shm`
  périmés retirés après remplacement.
- **Menus** : sur la capture d'un utilisateur, l'info-bulle « Rien n'est encore téléchargé… » d'une entrée GRISÉE couvrait le
  menu (cause principale : entrées désactivées, faute de chemin). `QMenu.setToolTipsVisible` retiré partout
  (`gui/ouvrir.action` : motif court dans le libellé, motif complet en `statusTip`), `ouvrir.montrer_menu` = `popup` +
  WA_DeleteOnClose (plus d'`exec` imbriqué) pour tous les menus contextuels (images, objets, lots, colonnes, Qualité).
- **Spectres et séries, « Ouvrir un fichier » sans effet** : filtre « (*.fits …) » sans nom → xdg-desktop-portal
  « invalid filter: name is empty ». **Reproduit en vrai** (ubuntu:24.04, Xvfb, dbus-run-session, xdg-desktop-portal
  1.18 + xdg-desktop-portal-kde, XDG_CURRENT_DESKTOP=KDE, `dbus-monitor`) : ancien filtre → `InvalidArgument`, aucune
  fenêtre ; nouveau → fenêtre « Ouvrir un fichier (nouveau filtre) — Portal » de xdg-desktop-portal-kde.
  `gui/fichiers` : `normaliser_filtre` (nom, motifs dédoublonnés, « Tous les fichiers (*) » à l'ouverture),
  `_parent_visible`, `_depart_existant`, journal de chaque ouverture/résultat/exception. Bouton « Ouvrir » sans le
  booléen `checked`. `tests/test_dialogues_fichiers.py` : les 13 appels de dialogue (garde-fou de comptage).
- **Qualité, 70 poses N.I.N.A. « mesurées » sans valeur** : `xisf.lire` strict (« incomplete FITSKeyword », N.I.N.A.
  écrit `CD1_1` sans commentaire). `xisf.lire(strict=False)` par défaut (tolérant), `strict=True`/`xisf.verifier`
  pour nos fichiers (formats.py, tests XSD). Vrais fichiers (copies dans `<dossier de travail>/qtest/`) : pose N.I.N.A.
  9576×6388 (strict : refus ; tolérant : lu), flat ASIAIR sans Metadata (copié de
  `…/Nuit_4/Flat/`, lecture seule), masterLight WBPP PixInsight 1.8.8 (strict ok). Mesure de la
  pose N.I.N.A. : 4,2 s, pic RSS 1 170 Mo (float32, fond soustrait en place), 14 455 sources, 400 étoiles, FWHM
  2,08 px = 3,53″ à 1,695″/px (matrice CD), RSN 108. Estimation mémoire 18 o/px + 150 Mo → processus limités
  (`limiter_par_memoire`). Erreurs : colonne `etat`, `rapport.motif_erreur`, `bilan_texte`, pile dans coupole.log,
  code 1 en CLI si rien n'est mesuré. Reorganisation/Ouvrir avec/metadonnees vérifiés sur ces formats.
- **Qualité, poses de ciel seulement** : `modules/qualite/calibration.py` (dossiers, noms — famille de
  `_DEFAULT_EXCLUDE_RE` d'astrosolver —, en-tête à la mesure) ; case, `--avec-calibration`, liste *Fichiers exclus…*.
  Le flat ASIAIR réel est exclu par son en-tête (`entete:flat`), le masterLight par le sien (`entete:master light`).
- Tests : `test_copie_ancienne.py` (20 lignes réelles de base + journal + INDEX_LOTS, XISF factices ; toutes les
  actions de l'interface sur la copie, local et partage simulé, popup + déclenchement des slots), 
  `test_dialogues_fichiers.py`, `test_qualite_calibration.py` (XISF « à la N.I.N.A. » et « à l'ASIAIR » construits
  octet par octet, arborescence N.I.N.A. + WBPP + ASIAIR). Manuels FR/EN (42 p.) complétés et recompilés.
- Validation locale (copie sans build/dist, `pip install ".[test]"`, offscreen) : **python:3.12-slim 480 réussis,
  15 sautés, code 0 ; python:3.10-slim 480 / 15, code 0**.
- CI `tests.yml` : commit `0f261ca` 4/6 (Windows : test du dossier de départ qui supposait « / » comme racine) ;
  commit `b459b98` **6/6** (Linux, Windows, macOS × 3.10, 3.12).
- **Aucun tag posé.**

## 2026-10-09 — version 0.1.12 : lancements journalisés, PixInsight, dépôt sans données personnelles
Retour d'utilisateur (Manjaro/KDE, 0.1.11) : « Ouvrir avec → PixInsight » ne faisait rien de visible et `coupole.log`
n'en gardait aucune trace. Diagnostic sur le poste : `PixInsight.sh` (eval, guillemets seulement autour des arguments
à espace), `.desktop` utilisateur sans `%F` ni MimeType, type MIME `application/x-kdeuser1`, instance ouverte qui
« cède la main » (code 0) sans rien ouvrir ; `PixInsight.sh -n fichier` ouvre l'image.
- **`core/lancement.py`** (nouveau) : `demarrer()` — liste d'arguments, détaché, stdout+stderr dans un fichier anonyme
  (pas de tube : le programme survit à Coupole), journal (programme, arguments, pid ; code et sortie si arrêt dans les
  3 s, `os.pread` pour ne pas déplacer la position partagée) ; `Lancement.verifier()` non bloquant, `attendre()`,
  `message()` → clé de texte FR/EN ; `ouvrir_systeme()` (startfile / open / xdg-open) ; `application_par_defaut()`
  (`xdg-mime query filetype|default`, .desktop dans XDG_DATA_HOME/DIRS, codes `%f %F %u %U`) ;
  `environnement_enfant()` retire le `QT_QPA_PLATFORMTHEME` posé par Coupole (`COUPOLE_QPA_THEME_POSE`).
- **`core/logiciels.py`** : `preparer_commande()` par logiciel et par système, sources citées en tête du module
  (forum PixInsight, fils 15197 / 14614 / 15888 ; `open(1)` ; manifeste Flathub de Siril ; `CommandLineOptions.cs`
  de N.I.N.A.). PixInsight Linux : script préféré au binaire, `/bin/sh` si le script n'est pas exécutable, lien
  symbolique temporaire (`lien_temporaire`, dossier privé 0700, liens de plus de 2 jours retirés, jamais leurs cibles)
  si `chemin_sur_pour_eval` refuse le chemin. `pixinsight_ouvert()` : `/proc/*/comm` (le cœur s'appelle
  « PixInsight », le script « PixInsight.sh »), `pgrep -x`, `tasklist` — pas `-e`, qui lancerait le cœur à chaque
  menu. Réglage `pixinsight_instance` (défaut `nouvelle`). Siril flatpak : `--file-forwarding @@ … @@`,
  `flatpak_voit()` lit `flatpak info --show-permissions` (host sans /tmp, /run sauf /run/media…, home, chemins,
  `!…`). N.I.N.A. : `SANS_FICHIER` (grisé avec la raison). `ouvrir_defaut()` : .desktop sans code de fichier →
  logiciel reconnu lancé directement, sinon message. `montrer_dans_dossier()` journalisé (explorer.exe : code ignoré).
- **Interface** : `gui/ouvrir.suivre()` (message immédiat puis état final par un QTimer de 250 ms),
  `statut()`, `montrer_emplacement()` ; `dialogues.ouvrir_fichier` passe par le même chemin ; menu « PixInsight
  (nouvelle fenêtre) » / « PixInsight (fenêtre ouverte, essai) » quand une instance tourne, celle du réglage d'abord ;
  Préférences > « PixInsight déjà ouvert » ; aide F1 `aide_ouvrir_avec` (correction du .desktop).
- **Tests** `tests/test_lancement.py` (26 cas) : faux PixInsight.sh qui reproduit l'`eval` + faux binaire qui note ses
  arguments ; **témoin** (le script appelé directement abîme un chemin à `$`) ; 14 noms difficiles (espace, `$`,
  `'`, `(`, accents, `` ` ``, `"`, `\`, `*`) dans un dossier lui-même difficile et dans un dossier sûr, `-n` ou non ;
  instance ouverte simulée (« Yielded execution ») ; Siril/ASTAP/Aladin directs ; programme direct sous tous les
  systèmes (CI Windows comprise) ; flatpak et permissions ; N.I.N.A. ; introuvable, code de retour + stderr ;
  .desktop sans `%F` (PixInsight lancé, application inconnue refusée), avec `%F` (xdg-open) ; menu selon instance
  et réglage ; barre d'état ; aucun `shell=True` ni `os.system` dans le code (analyse de l'AST).
- **Dépôt public, aucune donnée personnelle** (demande du mainteneur) : prénoms, chemins d'infrastructure, noms de
  machines, matériel personnel retirés des manuels (.tex et PDF), CHANGELOG (entrées passées comprises), PROGRESSION,
  audits, code, commentaires, tests, données de test (`/srv/ancien/OHP_DU_ECU` dans la copie d'exemple), outils
  (banc Samba : utilisateur `astro`) ; captures : `outils/captures.py` impose un dossier personnel neutre
  (`/tmp/utilisateur`) et une machine générique (`machine_neutre()`), captures refaites : Préférences, À propos,
  Ma machine, Spectres, Traitement (FR/EN) ; les autres vérifiées par OCR. `tests/test_confidentialite.py` : tous les
  fichiers suivis par git (texte, `pdftotext` + `pdfinfo`, PNG tEXt/zTXt/iTXt, .gz décompressés, chaînes des
  binaires), motifs et liste blanche explicites ; `poppler-utils` ajouté à la CI Linux. Historique git non réécrit
  (décision du mainteneur). `COUPOLE_REFERENCE` sans valeur par défaut.
- README : badges shields.io (Python 3.10+, GPL-3.0, Windows | Linux | macOS, dernière Release, statut de
  `tests.yml`, FR | EN).
- Manuels FR/EN : § « Ouvrir une image » (lancement de chaque logiciel, PixInsight déjà ouvert, double-clic et
  .desktop sans `%F`), Préférences ; recompilés (42 p.), temporaires supprimés.
- Validation locale (copie sans build/dist, `pip install ".[test]"`, offscreen) : **python:3.12-slim 509 réussis,
  15 sautés, code 0 ; python:3.10-slim 509 / 15, code 0**.
- CI `tests.yml` : commit `ce9bed1` 4/6 (macOS : test flatpak, `/tmp` résolu en `/private/tmp` — flatpak n'existe
  que sous Linux, test limité à Linux) ; commit `307efe4` **6/6** (Linux, Windows, macOS × 3.10, 3.12), garde-fou de
  confidentialité compris (PDF lus par pdftotext sous Linux).
- **Aucun tag posé.**
- Non vérifiable ici : PixInsight réel (logiciel commercial, absent du serveur de développement) — le comportement
  du script et de `-n` vient de l'essai sur le poste de l'utilisateur ; macOS et Windows : commandes d'après les
  sources citées, non essayées avec PixInsight.

## 2026-10-09 — version 0.2.0 : module « Archives des observatoires »
Demande : lister, rechercher, télécharger et préparer les images publiques des grands observatoires, actuelles et
passées, comme la Banque OHP ; méthode tirée des pratiques publiées (fils et tutoriels JWST/Hubble), sources citées.
- **Méthode et sources** : `docs/archives_methode.md`. Le fil Cloudy Nights « Working with JWST data from STScI /
  MAST » n'a pas pu être lu (403 aux lectures automatiques, aucun instantané sur web.archive.org) ; synthèse faite
  à partir de Galactic Hunter, Astronomy, Sky at Night Magazine, d'un tutoriel JWST, de l'aide du Hubble Legacy
  Archive et du HST Data Handbook, des documentations de Siril et de reproject, de Rector et al. 2007.
- **Services vérifiés sur place** (9 octobre 2026) : MAST TAP `ivoa.obscore` sans filtre ni date de publication →
  vue `dbo.obspointing` ; `CONTAINS(POINT, CIRCLE)` → 504 après 60 s, boîte `s_ra`/`s_dec` + `ORDER BY` distance
  → 1–2 s ; API Mashup `Mast.Caom.Cone` 74 s sur M 42 (écartée). ESO `tap_obs` : Phase 3 seulement,
  `INTERSECTS` 0,4–5 s, `access_estsize` en ko, fichier sans requêtes partielles (416). IRSA : TAP → DataLink (une
  requête par image) ; SIA 2 donne l'adresse et la taille → retenu. NOIRLab `adv_search` ; KOA TAP (poses brutes
  seulement) ; SkyServer DR18 ; **Gemini : « Login Required » (compte exigé)** ; **SMOKA : formulaire web** ; OPUS
  (`data.json`, `files/<id>.json`) ; PDS Imaging Atlas (Solr) pour JunoCam.
- **Module** `coupole/modules/archives/` : `services/` (base : requête, observation, VOTable/CSV, géométrie,
  politesse ; mast, eso, irsa, sol (noirlab, koa, sdss, gemini, smoka), planetes (opus, pds)), `recherche.py`
  (résolution du nom, archives en parallèle, filtres communs, tri, réponse tronquée signalée), `telechargement.py`
  (estimation, seuil, pilote, état `Archives/_etat/etat.sqlite` avec `BasePartagee`, journal bilingue,
  possession), `extraction.py` (SCI, détecteurs multiples, WCS, BUNIT, NaN + masque, crédit, XISF/FITS),
  `pds.py` (PDS3, VICAR, PDS4 maison), `alignement.py` (reproject facultatif ou scipy, unités par pixel, plus
  grand rectangle commun, ordre chromatique, PNG, PixelMath), `gui.py`, `cli.py`, `textes.py`.
- **Cœur** : `reseau.telecharger` recommence sans en-tête Range quand le serveur répond 416 dès l'octet 0 (ESO) ;
  `sources.json` version 3 (26 adresses d'archives, domaines ajoutés à la liste blanche) ; réglages
  `archives_dossier`, `archives_seuil_go`, `archives_debit_mo_s`, `archives_format`.
- **Défauts trouvés et corrigés pendant les essais réels** : label PDS3 des `CALIB` de Cassini qui place l'image
  une ligne trop tôt (valeurs de 1e38 : données lues d'après l'en-tête VICAR) ; poses brutes Keck avec BZERO
  (projection mémoire refusée → relecture sans) ; recadrage commun réduit à une bande par les colonnes mortes des
  mosaïques MIRI (rectangle calculé sur des blocs couverts à 90 %) ; identifiants PixelMath invalides (« - ») ;
  limite de lignes de MAST appliquée avant le tri (tri par distance côté serveur) ; mots-clés XISF relus avec un
  « / » final (lecture des valeurs réécrite) ; `reproject_exact` imprécis sous 0,05″ (méthode adaptative à la
  place).
- **Essais réels** (dossier temporaire du conteneur, effacé) : JWST MIRI `i2d` F770W + F1130W des Piliers (2 × 153
  Mo), WFC3/IR `drz` F160W + F110W (36,7 et 12,6 Mo) → 355,8 Mo en 12 s ; ESO APEX/LABOCA (14 Mo) et HAWK-I J (69 Mo,
  4 détecteurs) ; Spitzer MIPS 24 µm, AllWISE W1–W4 (274 Mo, IRSA à ~1 Mo/s), 2MASS J ; NOIRLab (0,3 Mo) ; SDSS g r i
  de M 51 (composition couleur réussie) ; Keck NIRC2 (4,2 Mo) ; Voyager 1 Io `GEOMED` (2 Mo), Cassini Encelade
  `CALIB` (4,2 Mo), JunoCam RDR (16,9 Mo). Alignements : MIRI seul (grille optimale, 2 346 × 2 548, 33 s en
  « exacte »), MIRI + WFC3/IR (grille de F160W), SDSS gri (2 044 × 1 476). Contrôle d'alignement sur les étoiles
  détectées (sommaire) : écart médian ≈ 1 px WFC3/IR entre F110W et F160W, ≈ 2,6 px (0,34″) avec MIRI : documenté
  (précision = celle des astrométries des archives).
- **Tests** : `tests/test_archives.py` (36), `tests/test_archives_reseau.py` (2, `COUPOLE_TEST_RESEAU=1` : réussi),
  `test_dialogues_fichiers.py` (dialogues du module). Budgets : 50 000 observations filtrées et triées < 2 s,
  possession de 50 000 lignes < 2 s, tableau de l'interface rempli et trié sur chaque colonne < 2 s.
  Mise à l'échelle 1,5 et 2 (`QT_SCALE_FACTOR`) : test_adaptatif, test_interface, test_archives,
  test_gui_robustesse, test_echelle verts fichier par fichier. Constat ancien (présent avant 0.2.0, vérifié sur
  `HEAD`) : `test_interface.py::test_fiche_en_ligne_vers_cosmologie` échoue si `test_adaptatif.py` tourne juste
  avant dans le même processus (ordre de la suite complète : vert).
- Manuels FR/EN : nouveau chapitre « Archives des observatoires » (tableau des archives, chercher, télécharger et
  préparer, formats planétaires, aligner et colorer, ligne de commande, crédits), tableaux des commandes
  régénérés, captures refaites (FR/EN), 50 et 49 pages. README (module, exemples, crédits), CHANGELOG FR puis EN,
  CONTRIBUTING (ajouter une archive), `pyproject` (extra `alignement` = reproject, ajouté à `test`).
- Validation locale (copie sans build/dist, `pip install ".[test]"`, offscreen) : **python:3.12-slim 548 réussis,
  17 sautés, code 0 (reproject 0.21.0) ; python:3.10-slim 548 / 17, code 0 (reproject 0.14.1)**.
- CI `tests.yml` : commit `9d21622` **6/6** du premier coup (Linux, Windows, macOS × 3.10, 3.12), garde-fou de
  confidentialité compris.
- **Aucun tag posé.**

## 2026-10-09 — version 0.2.1 : possession sous Windows (lecteur réseau), bibliothèques embarquées
- **Retour d'utilisateur** : copie complète de la banque sur un partage SMB, vue sous Windows par une lettre de
  lecteur réseau (dossier pré-rempli par le réglage `dossier_sortie`, le bon dossier, `_traitement/` dedans), base
  d'état en journal DELETE depuis l'après-midi : « tout à télécharger » sous Windows, tout possédé sous Linux.
- **Cause trouvée** : `chemins.uri_sqlite_lecture_seule` faisait `Path(chemin).resolve().as_uri()`. Sous Windows,
  `resolve()` (realpath → `GetFinalPathNameByHandle`) rend le chemin UNC d'un fichier sur une lettre de lecteur
  réseau ; `as_uri()` en fait `file://serveur/partage/…`, que SQLite refuse (« invalid uri authority », vérifié) ;
  l'exception était avalée par `Possession.lire_avec_infos` → statuts vides → « tout à télécharger ». Le chemin
  UNC tapé directement passait (branche `est_unc`). Pistes vérifiées et écartées pour ce cas : base WAL (DELETE au
  moment de l'essai ; gérée quand même), identifiant d'image (SHA-1 de l'URL, indépendant du système), lecture de
  `journal.csv` (BOM, « ; » : n'intervient pas dans les statuts), séparateurs d'`emplacements` (idem), dossier
  pré-rempli (le champ affiché est celui qui est lu ; `_dest_courante` = `abspath` du champ), clé de la base de
  travail (lettre et UNC = deux clés, deux bases de travail qui suivent chacune le partage : sans perte, divergence
  signalée au pire), sens de synchronisation (une base de travail n'est lue que si l'état du partage noté à la
  dernière synchronisation est identique ; sinon c'est la base du partage qui est lue), « Rafraîchir l'inventaire »
  (relit bien la possession : test ajouté). Base réelle relue en lecture seule (copie temporaire, 18 Mo, DELETE,
  7 625 ok + 364 doublons) : lisible, aucune anomalie.
- **Corrections** : URI construite sans résolution (`file:///O:/…`, `file:////serveur/…`, échappements) ;
  `base_partagee.lire_base` (base de travail à jour, sinon copie locale si partage ou WAL, sinon lecture directe ;
  chaque échec mène à l'autre voie ; `BaseIllisible` sinon) utilisée par la possession et les anomalies ;
  `Possession.erreur`, `base_absente`, `fichiers_sans_base` ; bandeau d'erreur et « Reconnaître les fichiers
  existants » (module `ohp/reconnaissance.py`, CLI `coupole ohp reconnaitre`) ; ligne « Dossier de suivi : … — N
  images possédées lues » (résumé + barre d'état) ; journal `coupole.log` : chaque lecture (provenance, nombre) et
  chaque synchronisation (sens). La réorganisation préfère l'adresse complète de l'en-tête (`OHP:Source:URL`).
- **Bibliothèques embarquées** : `requirements.txt` des paquets + `reproject` (et ses dépendances) + `psutil`
  (`sep`, `lxml` y étaient déjà) ; `kit.json` : `verification_import` étendu et `essai_embarquees`
  (`coupole.core.bibliotheques.essai_embarquees` : petit `reproject_interp` + extraction SEP), exécuté par
  `build_unix.py` après l'élagage, par `release.yml` (Windows, étape dédiée Linux/macOS, conteneur Debian) : sans
  elles, échec de la publication. « Ma machine » et « À propos » listent les bibliothèques facultatives.
  Roues vérifiées pour cp312 win_amd64, macOS arm64 et x86_64, manylinux x86_64 et aarch64 (aucune compilation).
- **Tailles mesurées** (paquet Linux x86_64 construit ici, `build_unix.py`, avant = 0.2.0 / après) : élagué
  525 → 562 Mo dépliés ; archive tar.gz 101 → 121 Mo ; .deb 109,3 → 120,9 Mo. Windows (estimation par les roues
  cp312 win_amd64 ajoutées, non construit ici) : + 13 Mo compressés, + 36 Mo dépliés avant élagage.
- **Tests** : `tests/test_partage_windows.py` (URI lettre/UNC/caractères spéciaux, la cause reproduite, lecture
  WAL/DELETE × local/partage, copie refaite seulement si la base change, secours si lecture directe refusée, base
  abîmée dite et journalisée, reconnaissance avec URL ou HISTORY, bandeau et reconnaissance dans l'interface,
  « Rafraîchir » relit la possession ; Windows : partage `C$` sous le nom de la machine (pas « localhost », que SQLite accepte comme autorité) en UNC et lettre posée par `net use` dans
  `tests.yml`, WAL et DELETE, premier lancement, base de travail ancienne d'un essai antérieur, `resolve()` → UNC
  et ancienne URI refusée sur le vrai lecteur) ; `test_machine_parallele.py` (bibliothèques).
- Manuels FR/EN (Installation : bibliothèques embarquées ; partage réseau : Windows, dossier de suivi,
  reconnaissance ; Dépannage), tableaux des commandes régénérés, aide F1, README, CHANGELOG FR puis EN.
- Validation locale (copie sans build/dist, `pip install ".[test]"`, offscreen) : **python:3.12-slim 573 réussis,
  21 sautés, code 0 (reproject 0.21.0) ; python:3.10-slim 573 / 21, code 0 (reproject 0.14.1)**.
- CI `tests.yml` : commit `b7e04db` **6/6**. Sous Windows (3.10 et 3.12), `net use X:` sur le partage `C$` de la
  machine : `GetDriveTypeW(X:) = 4` (lecteur distant) ; les 4 tests Windows de `test_partage_windows.py` ont tourné
  (aucun sauté) et passent — dont **la cause reproduite sur le vrai lecteur mappé** (`Path.resolve()` rend le chemin
  UNC, l'URI de la 0.2.0 est refusée par SQLite) et la possession complète (WAL et DELETE, UNC et lettre, premier
  lancement, base de travail ancienne).
- **Aucun tag posé** (publication et vérification du paquet par le mainteneur).
