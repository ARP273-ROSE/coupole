# Historique

Version anglaise : [CHANGELOG.en.md](CHANGELOG.en.md).

## 0.1.0 — 8 octobre 2026

Première version.

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
