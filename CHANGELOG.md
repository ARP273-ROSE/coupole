# Historique

Version anglaise : [CHANGELOG.en.md](CHANGELOG.en.md).

## 0.1.0 — 8 octobre 2026

Première version.

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
