# Historique

Version anglaise : [CHANGELOG.en.md](CHANGELOG.en.md).

## 0.1.3 — 9 octobre 2026

- Construction : le run de release v0.1.2 a échoué sur une apostrophe glissée dans un commentaire de l'essai du `.deb`
  (`release.yml`) ; aucun changement de l'application. Les actifs de la 0.1.3 sont ceux attendus pour la 0.1.2.

## 0.1.2 — 9 octobre 2026

- **Paquet `.deb` : dépendance `ca-certificates` ajoutée.** L'interpréteur embarqué (OpenSSL statique) lit les autorités de
  certification dans `/etc/ssl/certs` : sur un système minimal sans ce paquet, toute connexion HTTPS échouait en silence
  (recherche de mise à jour, SIMBAD, JPL) — trouvé en essayant `coupole maj` dans un conteneur Ubuntu nu. L'essai du
  paquet dans `release.yml` vérifie désormais une connexion HTTPS depuis l'interpréteur embarqué.

## 0.1.1 — 9 octobre 2026

- **Paquet Debian/Ubuntu** (`coupole_0.1.1_amd64.deb`, `_arm64.deb`, et noms stables `coupole-linux-amd64.deb` /
  `-arm64.deb`) construit par `build_deb.py` à partir du paquet Linux autonome : fichiers sous `/opt/coupole`,
  commande `/usr/bin/coupole` (interface sans argument, ligne de commande avec), entrée de menu, icônes, page de
  manuel, `copyright` GPL-3, dépendances système de Qt résolues par apt (vérifiées par `ldd` et par installation dans
  des conteneurs Ubuntu 22.04 et 24.04 nus). Une installation `.deb` ne se met pas à jour par archive : Coupole
  signale la nouvelle version et pointe vers le `.deb` de la Release (bouton *Télécharger le paquet*,
  `coupole maj`). `release.yml` construit le `.deb`, l'essaie dans un conteneur nu, le joint à la Release, puis **ne
  garde qu'une Release en ligne** (les précédentes et leurs tags sont supprimés une fois la nouvelle complète, ainsi
  que les artefacts de construction) ; la mise à jour automatique s'appuie sur `releases/latest` et des noms stables.
- **Paquets Linux/macOS allégés** : interpréteur python-build-standalone « stripped » (−320 Mo dépliés : libpython
  219 Mo et binaire 102 Mo de symboles de débogage), Tcl/Tk, en-têtes et greffons Qt orphelins retirés ;
  `Coupole-0.1.1-linux.tar.gz` : 229 → 137 Mo ; `.deb` : 106 Mo.
- **Thème sombre par défaut** ; menu *Affichage > Apparence* (entrées cochables *Clair* / *Sombre*, Ctrl+Maj+D
  bascule) appliqué immédiatement et enregistré, synchronisé avec les Préférences ; un utilisateur qui avait choisi
  le thème clair le garde. Captures des manuels régénérées en sombre.
- **Banque OHP — ce qu'on possède déjà** : d'après `_traitement/etat.sqlite` (relu en fond à l'ouverture, après chaque
  traitement et à chaque changement de dossier), pastille et couleur douce par image (possédée, doublon écarté,
  échec, à télécharger ; contraste ≥ 4,5 dans les deux thèmes ; info-bulle avec statut, date et fichier local),
  colonne *possédé* « 120 / 300 » avec mini-barre et pastille (complet / partiel / rien) par objet, triable ; case
  *À télécharger seulement* ; estimation qui ne compte que les manquantes ; légende ; onglet Lots : colonne
  *complet / incomplet* ; `coupole ohp inventaire --manquantes [--json]` et colonnes `possedee`, `statut_local`,
  `fichier_local` dans le CSV de `ohp images`.
- **Cosmologie** : curseur de redshift sous le champ z (échelle logarithmique de 0,001 à 1100, repères par décade)
  qui déplace le marqueur des courbes et met à jour le tableau en direct par interpolation sur la grille des
  courbes (toutes les grandeurs y sont désormais calculées), calcul exact au relâchement, champ et curseur
  synchronisés, flèches = pas fin. **Correctif** : les courbes ne suivaient pas le redimensionnement de la fenêtre
  quand elles passent sous le tableau (le panneau, plus haut que la zone défilante, gardait sa hauteur de consigne) :
  la moitié de la hauteur visible leur revient désormais.
- **Carte OpenStreetMap nette sur les écrans denses** (Windows à 125–150 %, Mac Retina) : tuiles du niveau de zoom
  supérieur dessinées à demi-taille (équivalent « @2x »), lissage activé ; la carte était auparavant agrandie par
  le système et apparaissait pixelisée.
- **Qualité des images — vitesse et reprise** : mesure 3,7 × plus rapide (1,21 → 0,33 s par image T120 : modèle de
  Moffat vectorisé, dérivées analytiques, 120 étoiles par image) ; mesures en processus parallèles (plan machine,
  mode économe, bridage ; au plus 3 sur un dossier réseau, détecté et signalé), interface libre, arrêt immédiat ;
  chaque image écrite aussitôt dans `QUALITE.csv` (atomique) ; cache `_traitement/qualite.sqlite` par (chemin,
  taille, date) : relancer ne refait rien, fermer puis rouvrir reprend ; au-delà de 200 images, échantillon de 5 par
  lot proposé (ou tout, avec la durée estimée sur 3 images) ; progression avec temps restant et débit ;
  `coupole qualite --echantillon N | --tout | --processus N`. **Correctif** : sur certaines étoiles réelles,
  l'ajustement débordait (`OverflowError`) et arrêtait la mesure de l'image.
- **Ma machine** : la ligne « Calcul sur carte graphique » n'évoque plus CuPy (rien à installer : aucune fonction
  n'utilise la carte pour l'instant) ; le détail pour les développeurs est dans l'info-bulle et CONTRIBUTING.
- Tests : +37 (possession, moteur Qualité sur 300 XISF simulés, curseur, redimensionnement, tuiles denses, menu
  Apparence, cas `.deb` de la mise à jour).

## 0.1.0 — 8 octobre 2026

Première version.

- **Suite de l'audit** (§ 10 du rapport, propositions appliquées) : hauteur du Soleil du contrôle « heure locale écrite
  par erreur » calculée en un seul appel astropy et mise en cache par (site, minute UTC) dans chaque processus de
  conversion (13,2 → 2,5 ms de CPU par pose sur une série de poses de 20 s, 33 → 13 ms sur une image isolée ; débit
  global inchangé, borné par le réseau) ; sous Windows, chaque processus de conversion se place dans un *job object*
  « kill on close » : à l'annulation, l'ASTAP qu'il a lancé meurt immédiatement avec lui au lieu de finir seul (jusqu'à
  4 min) — repli silencieux si l'API refuse, Linux et macOS inchangés (signal) ; quand la place libre à destination est
  juste, la file des FITS en attente (2 × conversions + téléchargements) est **réduite automatiquement** (jamais sous
  conversions + 1), avec un message et une ligne de journal, au lieu de refuser le traitement. Non appliqué, à dessein :
  connexions HTTP persistantes (gain < 1 %) et budget mémoire 500 → 400 Mo par conversion (prudence : ASTAP ajoute son
  propre processus).
- **Audit complet** (`docs/AUDIT_2026-10.md`) : performance (fenêtre affichée en 0,42 s au lieu de 1,51 s : astropy,
  scipy et SEP ne se chargent plus avant l'affichage ; mémoire de pointe d'une conversion IRIS 4096² ramenée de
  573 à 365 Mo ; une requête HTTP par image au lieu de deux ; progression agrégée à 10 Hz), parallélisme (bridage
  manuel borné par la mémoire ; annulation qui termine les processus de conversion et ASTAP ; plantage d'un
  processus survécu ; fermeture qui arrête et attend tous les fils), robustesse (réglages corrompus mis de côté ;
  écritures atomiques partout ; disque plein, dossier non inscriptible, FITS et XISF abîmés, fuseau inconnu, réseau
  coupé testés ; signaux Qt protégés contre les widgets détruits ; vigie de gel et crash natif testés), sécurité
  (HTTPS obligatoire pour le fichier de sources et le point de collecte ; archive de mise à jour contrôlée : zip
  slip, liens symboliques, bombe ; rapports bornés à 64 ko, nom de machine masqué ; noms de dossiers sûrs ; aucun
  écrasement de fichier au rangement ; pip-audit sans alerte), multiplateforme (console Windows cp1252 ; locales
  Windows ; rôles de menu macOS ; chemins longs), bilinguisme (test de fuite de langue). **Correctif** : avec
  « Garder les doublons », une image aux pixels identiques était supprimée au lieu d'être gardée (et inversement).
- **Banque OHP — Tout télécharger** : toute la banque (≈ 8 000 images, 78 Go → ≈ 30 Go en XISF) avec volume, durée
  estimée au débit plafond et place libre affichés avant confirmation ; dossier demandé au premier usage
  (`Documents/Coupole/OHP_DU_ECU` proposé) ; reprise après coupure ou fermeture ; **pause / reprise** ; rapport de
  fin ; `coupole ohp tout`.
- **Journal lisible** `_traitement/JOURNAL.txt` (horodaté UTC, bilingue, rotation), bouton « Ouvrir le journal ».
- **Réorganiser** : range des fichiers déjà convertis par Coupole (ailleurs, ancien rangement) dans l'arborescence des
  lots — déplacement, jamais de copie ni d'écrasement, journal ; `coupole ohp reorganiser`.
- **Nouveautés de la banque** : vérification au démarrage (au plus une fois par jour, réglable, désactivable) de
  l'inventaire TAP contre la copie locale ; bandeau « N nouvelles images (M objets, X Go) depuis le … — Télécharger
  maintenant ? / Plus tard / Voir » ; jamais de téléchargement sans accord ; `coupole ohp nouveautes [--telecharger]`.
- **Cosmologie** : liste des modèles jamais coupée ; courbes sous le tableau quand la place manque (colonne SH0ES
  toujours visible sans défilement).
- **Cosmologie** (nouveau module) : du redshift aux distances comobile radiale et transverse, de luminosité,
  angulaire et de trajet de la lumière, temps de regard en arrière, âge à z et âge actuel, E(z) et H(z), module de
  distance, échelle en kpc par seconde d'arc, volume comobile, trois vitesses de récession ; Planck 2018 par défaut
  (incertitude 1σ avec la corrélation H₀–Ωm, comparaison SH0ES), Planck 2015, WMAP 9, ΛCDM « de manuel », jeu
  personnalisé (H₀, Ωm, Ωk) ; valeurs hors plage refusées avec une explication ; redshift d'un objet demandé à
  SIMBAD ; courbes des distances ; export CSV ; ligne de commande `coupole cosmo`. Noyau de calcul repris du
  calculateur « cosmologie-redshift » du même auteur, **vérifié avant intégration** contre astropy et une
  intégration indépendante sous SageMath (z de 10⁻⁸ à 1100, univers plats et courbes) : aucun bug, écart ≤ 3·10⁻⁶
  sur les distances, ≤ 2·10⁻⁵ sur les âges. Volume comobile : développement limité aux très petits z en univers
  courbe, où la formule d'astropy perd tous ses chiffres (volume faux, voire négatif).
- **Fiche en ligne** (Banque OHP, réutilisable par les autres modules) : SIMBAD (type, coordonnées, magnitudes,
  parallaxe, distance mesurée, vitesse radiale et redshift, taille angulaire, types spectral et morphologique,
  identifiants, liens SIMBAD, Aladin Lite et NED), repli Sesame, JPL Small-Body Database pour les petits corps
  (classe orbitale, éléments, diamètre, albédo, rotation) ; facultative et jamais bloquante (fil de fond, délai de
  8 s, une requête par objet, cache daté de 30 jours, repli hors ligne avec la dernière fiche connue) ; identifiant
  retenu toujours affiché ; « envoyer ce redshift au module Cosmologie ». Adresses dans `sources.json`.
- **Tous les écrans** : interface adaptée de 1024×600 (ou 1366×768 à 150 %) à la 4K, sans troncature ni
  débordement : tailles plafonnées à l'écran, contenus défilants, textes qui passent à la ligne, filtres et réglages
  en rangées souples, barre des modules réduite aux icônes sous 1 100 px, mise à l'échelle fractionnaire exacte ;
  vérifié par des tests à 6 tailles d'écran et à 150/200 %.
- **Correctif** : fermer la carte du monde pendant le téléchargement d'une tuile pouvait faire planter Python.
- **Apparence** : style, couleurs et police propres à Coupole, indépendants des réglages de l'ordinateur (mode sombre
  du système, thèmes GTK/KDE, taille de police) ; thème clair ou sombre au choix dans les Préférences ; couleurs
  douces (blanc cassé, anthracite, bleu ardoise) et coins arrondis ; contraste texte/fond WCAG ≥ 4,5 vérifié par test.

- **Cœur** : interface PyQt6 et ligne de commande complète, français et anglais partout (détection de la langue du
  système, choix forcé), info-bulles sur tous les widgets ; modules découverts automatiquement (livrés, installés,
  ou déposés dans le dossier des réglages) ; détection du matériel (système, processeur, cœurs, mémoire, disque,
  carte graphique) et parallélisme adapté ; adresses des services configurables (fichier de sources, valeurs forcées,
  fichier publié dans le dépôt avec contrôle de forme et liste blanche de domaines) ; rapports d'incident anonymes
  avec consentement ; mise à jour automatique des paquets depuis les Releases GitHub ; manuel PDF et aide par écran.
- **Banque OHP** : inventaire par TAP (cache, instantané livré, nouveautés signalées) ; catalogue des 166 objets
  (table de classement en JSON, règles, résolution en ligne facultative, regroupement par position, corrections
  mémorisées) ; téléchargement poli et reprenable ; doublons par empreinte des pixels ; contrôle de la solution
  astrométrique (cohérence, ASTAP facultatif) ; en-têtes corrigés avec HISTORY, correction de position conditionnelle
  et idempotente ; sorties XISF, FITS compressé sans perte, FITS float32 ; lots empilables, `LOT.txt` bilingue,
  `INDEX_LOTS.csv`, `journal.csv` ; rapport d'anomalies ; carte du ciel. Conforme au traitement de référence du
  7-8 octobre 2026 (pixels et en-têtes identiques sur l'essai réel).
- **Qualité des images** (facultatif, SEP) : FWHM et ellipticité (ajustement de Moffat, carte 3 × 3), fond, bruit,
  gradient, résidu, saturation, traînées, échantillonnage ; validé sur images synthétiques.
- **Spectres et séries** : lecture FITS (axe WCS, cubes radio, tables) et CSV, vitesse radio.
- **Sites et heures** : OHP, Meudon, Paris (constantes MPC), sites ajoutés, carte OpenStreetMap, UTC et heure locale.
- **Ma machine** : diagnostic (exemple de module).
- **Distribution** : paquets Windows (Python embarqué + Inno Setup), macOS (.app, .dmg) et Linux (archive + installeur),
  scripts `install.sh` / `install.ps1` / `install.bat`, `pipx`/`pip`.
