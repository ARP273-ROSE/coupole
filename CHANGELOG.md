# Historique

Version anglaise : [CHANGELOG.en.md](CHANGELOG.en.md).

## 0.8.2 — 20 octobre 2026

- **Navigation des animations dans un ordre logique** : Modules, Animations, Bibliothèque, Favoris, Progression. La
  Bibliothèque perd son onglet « Animations », qui répétait la page Animations (rangée par thème, avec la recherche) ;
  les animations d'un module restent dans la page du module.
- **L'atmosphère terrestre, vue Réfraction** : le Soleil à l'échelle suit le curseur de hauteur (il était figé sur
  l'horizon) ; la vue le suit et indique l'horizon quand il sort du cadre.

## 0.8.1 — 19 octobre 2026

- **Calculateur de TD « Parallaxe »** : le TLE de l'ISS est récupéré tout seul au moment du calcul (CelesTrak), sans clic ; il est gardé pour le hors-ligne. Pour une date ancienne, Coupole prend le plus proche et le signale (l'historique complet demande un compte Space-Track, gratuit).

## 0.8.0 — 19 octobre 2026

**Partages du DU.** Nouveau module pour les dossiers collaboratifs des défis et TP (partages Nextcloud de
l'Observatoire). Aucun lien n'est livré : vous collez celui que l'équipe vous a donné, il reste sur votre ordinateur
(`partages.json`, lisible par vous seul) et n'apparaît dans aucun rapport.

- **Plusieurs partages mémorisés** (nom libre, renommer, oublier, copier le lien), droits du lien affichés (Coupole
  prévient si le lien permet de supprimer : il ne le fait jamais).
- **Structure devinée** sans rien télécharger : genres de fichiers, instant d'après le nom (ambiguïté
  JJ-MM-AA / AA-MM-JJ tranchée par la date de dépôt, heure « d'après le nom » signalée), observateurs, cibles,
  prises, séries ; en-têtes FITS lus par requête partielle (34 premiers ko). Présentation comme la Banque OHP : liste à
  gauche, contenu à droite, bouton bleu « Télécharger (N · taille) », clic droit, guide en trois étapes (*Aide > Guide
  des partages*), aperçus (FITS, JPEG, PNG, TIFF, SER, AVI), bandeau des nouveautés.
- **Tableaux de mesures contrôlés** (xlsx, csv, jamais modifiés) : formats normalisés, inversions latitude/longitude
  (certaines, prouvées par l'en-tête, par la Lune ou par comparaison aux lieux sûrs), heure locale, dates
  américaines, date ambiguë tranchée par le nom du fichier, fichiers absents ; corrections proposées pour les calculs
  seulement ; export CSV normalisé.
- **Outil « Parallaxe (Lune, ISS) »** (architecture d'outils extensible) : paires simultanées, centre de la Lune
  ajusté sur le limbe (Lune saturée signalée), objet mobile ou trait de l'ISS, distance de la Lune par la méthode
  vectorielle topocentrique — **directions astrométriques ramenées aux directions géométriques** (le temps de lumière
  diffère entre les observateurs : ≈ 20 km d'erreur sinon) —, altitude de l'ISS par triangulation avec décalage
  d'horloge estimé et méthode des plans, comparaison à JPL DE440 (fichier téléchargé une fois) ou à Meeus et au TLE,
  budget d'erreur, rapports HTML et PDF (aussi depuis la ligne de commande, sans écran).
- **Dépôt de sa mesure sans rien écraser** : confirmation qui liste tout, noms libres, dépôts conditionnels
  (If-None-Match / If-Match), première ligne libre du tableau (rien d'autre ne change, octet pour octet), copie
  locale avant l'ajout, petit CSV à côté après trois conflits ; le client WebDAV n'a aucune méthode de suppression,
  de renommage ni de déplacement.
- Ligne de commande `coupole partages` (ajouter, liste, explorer, tableau, entêtes, paires, télécharger, mesurer,
  calculer, déposer, de440).

**Astrométrie en ligne en dernier recours (nova.astrometry.net).** Chaîne commune : solution de l'en-tête, ASTAP,
astrometry.net installé, puis le service libre nova.astrometry.net avec **votre** clé d'API (*Préférences >
Astrométrie*, gardée à part) et **votre accord avant chaque envoi**. Image allégée (16 bits, réduite ; solution
ramenée à l'image d'origine, SIP compris), indices d'échelle et de position, images non publiques par défaut, une
soumission à la fois, sondage espacé, abandon propre, reprise ; une image déjà envoyée ne l'est jamais deux fois
(cache). Sert aux Partages du DU et à la Banque OHP (images sans solution quand ASTAP manque).

**Calculateurs de TD.** Nouvelle rubrique : des calculateurs qui suivent pas à pas la démarche des TD et TP du cours.
Premier : **Parallaxe (TP du cours)**, d'après le sujet officiel (ISS, Lune) : élévations h₁ et h₂, 2α = h₁ − h₂ (ou
180° − h₁ − h₂ si l'objet est entre les lieux), R à la surface (comme Google Earth) et en corde (EarthLocation
d'astropy), D = R/2α ; puis le calcul exact (les horizons font l'angle θ ; triangulation avec ou sans azimuts), la
**flèche** de la corde et sa profondeur sous chaque horizon, l'éphéméride si l'heure est donnée (Lune : DE440 ou
Meeus ; ISS : TLE le plus proche de l’instant récupéré tout seul au calcul, gardé en cache, âge affiché ; pour un passage ancien, l’avertissement dit que l’historique exige un compte Space-Track), les incertitudes (élévations, lieux, heure). Positions
écrites de **n'importe quelle façon** (décimal, virgule, N/S/E/O/W, degrés-minutes-secondes, ordre libre si les
lettres le disent), inversion signalée. Dessin de tout l'exercice (coupe de la Terre, corde, verticales, horizons,
visées, angles, loupe sur la flèche), pas-à-pas numéroté, exemple fictif, export CSV pour la feuille « Calculs ».
Ligne de commande `coupole td parallaxe`. Vérifié contre SageMath (corde à 1 mm).

**Nouvelle animation « L'atmosphère terrestre : absorption, épaisseur traversée, réfraction »** (96ᵉ, propre à
Coupole, thème *Télescopes* : l'atmosphère est le premier instrument que traverse la lumière, elle décide où et comment
on observe). Quatre vues : **épaisseur traversée** (coupe de la Terre et de l'atmosphère, couches, échelle de hauteur
8 km, trajet qui s'allonge vers l'horizon ; masse d'air par sec z, Kasten & Young 1989, Pickering 2002 et coquille
sphérique : ≈ 38 à l'horizon) ; **extinction et rougissement** (Rayleigh ∝ λ⁻⁴, aérosols d'Ångström, ozone ;
Δm = k X en U B V R I ; couleur du Soleil transmis selon sa hauteur) ; **fenêtres atmosphériques** (transmission de
0,3 à 30 µm d'après le modèle de ciel de l'ESO — SkyCalc, Paranal —, bandes J H K L M N Q et absorptions H₂O, CO₂,
O₃ ; schéma des domaines γ, X, UV, infrarouge lointain, submillimétrique, radio, ionosphère ; pourquoi des télescopes
en altitude et dans l'espace) ; **réfraction** (rayon dans des couches d'indice décroissant, exagération possible,
hauteur apparente et vraie — Bennett, Sæmundsson, ≈ 34′ à l'horizon —, Soleil aplati à l'échelle, lever avancé et
coucher retardé selon la latitude, dispersion par l'indice de Ciddor, pression et température). Formules vérifiées
par SageMath, sources dans NOTICE ; lien avec le défi parallaxe et le calculateur de TD.

**Temps sidéral et angle horaire.** L'arc de l'angle horaire est affiché par défaut (un choix mémorisé est gardé) ;
encadré « Dans l'hémisphère Sud » (culmination vers le nord, défilement de droite à gauche face au nord, σ Octantis,
étoiles circumpolaires si δ < −(90° − |φ|)), vérifié par SageMath.

**Dépendances** (licences MIT) : `jplephem` (DE440) et `sgp4` (TLE), embarquées dans les paquets autonomes.

**Essais** : serveur WebDAV factice (PROPFIND, GET partiel, PUT conditionnel, 412, méthodes destructrices refusées et
comptées), classeur synthétique (styles, formule, deuxième feuille, lignes pré-numérotées), contrôles, paires,
calculs contre skyfield + DE440 et SageMath (scripts `outils/verif_parallaxe/`, `outils/verif_td/`), faux serveur
nova, interface sans écran et parcours d’un débutant de bout en bout ; 1 623 essais réussis.

## 0.7.2 — 15 octobre 2026

**Banque OHP : télécharger sans manuel.** Retour d'un étudiant (0.4.1, Windows) : il voyait le catalogue, faisait un
clic droit sur une image et ne trouvait que « Ouvrir (rien de téléchargé) » ; le vrai chemin (« Traiter cette
sélection → », onglet Traitement, Lancer) était introuvable — et, en 1366 × 768, ce bouton était sous le bord de la
fenêtre.

- **Un bouton « Télécharger » visible, en couleur d'accent**, sous la liste des images : « Télécharger (840 images ·
  7,15 Go → ≈ 2,64 Go en XISF) ». Il télécharge, vérifie, convertit et range tout de suite, avec le dossier et le
  format mémorisés ; le dossier est demandé la première fois (dialogue de fichiers complet du système). Progression
  et « Arrêter » sous le bouton ; à la fin, la barre d'état dit où sont les images et comment les ouvrir. Grisé
  avec la raison au survol (« Choisissez d'abord une cible… »), « Déjà téléchargé ✓ » quand tout est là.
- **« Traiter » devient « Télécharger » partout** : onglet *Traitement* → *Téléchargement*, qui garde la progression,
  le journal et réunit tous les réglages sous *Options* (dossier, format XISF ou FITS, langue des noms, doublons,
  FITS d'origine, qualité, astrométrie, parallélisme) ; « Traiter cette sélection → » → « Options du téléchargement
  → » ; messages, barre d'état, journal, aide F1 et manuels suivent. Inchangés pour rester compatibles : les noms
  internes (`_traitement/etat.sqlite`…) et la ligne de commande (`coupole ohp traiter`).
- **Menus contextuels** : le menu d'une image commence par « Télécharger cette image » (ou « ces N images »), puis
  Ouvrir / Ouvrir avec / Ouvrir l'emplacement, grisés avec leur raison (« pas encore téléchargée ») ; celui d'une
  cible par « Télécharger toutes les images de NGC 6888 ». **Double-clic** sur une image ou une cible pas encore
  téléchargée : Coupole propose de la télécharger.
- **Premier lancement** : bandeau de guidage en trois étapes (① choisir une cible à gauche, ② ses images à droite,
  ③ Télécharger), chaque étape faite cochée, fermable (« Compris, masquer »), réaffichable par *Aide > Guide de
  démarrage (Banque OHP)* ; plus aucune cible choisie d'office ; listes vides explicites (« Aucune cible choisie :
  cliquez sur une cible dans la liste de gauche »).
- **Lisibilité** : info-bulle d'une ligne sur chaque en-tête de colonne ; colonnes clés d'abord (images : état, date,
  télescope, filtre, pose ; cibles : objet, possédé, volume) ; « Lots » et « Anomalies » expliqués en une ligne ;
  onglets dans l'ordre de l'usage (Catalogue, Téléchargement, Lots, Carte du ciel, Fiche en ligne, Anomalies) ; date
  et adresse du service d'inventaire passées en info-bulle. **En 1366 × 768, à 100 % comme à 125 %, le bouton
  Télécharger est à l'écran sans défiler** : les onglets Téléchargement et Lots défilent seuls et n'imposent plus
  leur hauteur au catalogue.
- **Archives des observatoires**, même logique : « Télécharger la sélection (N · taille) » en couleur d'accent juste
  sous le tableau, grisé avec la raison ; clic droit qui commence par « Télécharger cette observation / ces N
  observations » (sélection multiple) ; double-clic sur une ligne absente qui propose de la télécharger.
- Tests : `tests/test_parcours_debutant.py` (premier lancement, choisir une cible, Télécharger sur un serveur local,
  fichier présent, Ouvrir disponible, menus, double-clic, 1366 × 768 et 125 %, Archives).

**Nouvelle animation « Gravité et orbites » (95ᵉ)**, d'après la simulation PhET « Gravity and Orbits » du projet PhET
Interactive Simulations de l'University of Colorado Boulder : idée et fonctions reprises, code, dessins et textes
propres à Coupole (rien de PhET n'est copié ; licences vérifiées et citées dans `NOTICE`). Faite dans Coupole Web
0.6.1 d'abord, avec la même mécanique (nombres identiques au bit près, cas communs `tests/gravite_cas.json`) et le
même rendu.

- **Scénarios** : Soleil et Terre ; Soleil, Terre et Lune ; Terre et Lune ; Terre et station spatiale (ISS) ; libre
  (Soleil, Terre, Lune et une comète d'aphélie 2,4 ua). Le Soleil, la Terre et la Lune ensemble partent de leur état
  **réel du 1ᵉʳ janvier 2026** (DE440, orbites ramenées dans l'écliptique autour de leur ligne des nœuds,
  `outils/verif_anim/etat_initial_gravite.py`) : une Lune lancée sur un cercle de Kepler prendrait, dans le champ de
  marée du Soleil, une période de 27,05 à 27,81 j selon la phase de départ.
- **Vues « Modèle »** (astres agrandis, distance Terre–Lune ×78) **et « À l'échelle »** (la Terre et la Lune vues du
  Soleil : un seul point), passage en douceur (QTimer arrêté à l'arrivée).
- **Mécanique** `gravite_meca.py` : Yoshida d'ordre 4, pas adaptatif, constantes CODATA 2018, UAI 2015 et 2012, DE440,
  NASA ; collisions ; périodes mesurées (Terre 365,26 j, Lune 27,34 j, ISS 92,87 min, comète 671,0 j), énergie et
  moment cinétique conservés à 10⁻¹⁴ près ; intégration indépendante sous SageMath
  (`outils/verif_anim/gravite_orbites_verif.sage` → `tests/gravite_orbites_sage.json`) : mêmes périodes à 2 × 10⁻⁶.
- **Réglages** : force de gravité (bleu), vecteur vitesse (vert), trajectoires, grille, ruban de mesure, gravité,
  Lune vue du Soleil, masses du Soleil, de la Terre et de la Lune ; Pas, Retour, Effacer les trajectoires ; glisser
  un astre (satellites compris), tirer une flèche de vitesse, glisser le ruban.
- **Lune vue du Soleil** : vraie trajectoire (jamais de boucle) et rapport des courbures Lune / Terre, toujours
  positif, dans un panneau à côté de la scène (fenêtre large) ou dessous (fenêtre haute), jamais par-dessus le
  mouvement ; astres de 5 px au moins en vue « Modèle ».
- Thème « Renaissance », module « L'astronomie de la Renaissance » (`ANIMATIONS_AJOUTEES` de
  `outils/importer_contenu.py`) ; recherche « gravity and orbits » / « gravité et orbites » en premier (cas
  régénérés) ; aide F1 ; manuels FR et EN (section « Gravité et orbites (0.7.2) », captures nouvelles) ; NOTICE.
- Traces dessinées en traits de 1 px (600 points au plus) : la voie rapide de QPainter (un trait plus épais faisait
  remplir le contour de la trace qui se recoupe, 20 fois plus lent).
- Tests : `tests/test_anim_gravite.py` (cas communs au bit, physique, SageMath, glisser, flèche, ruban, vues et
  passage, valeurs, durée d'une image).

## 0.7.1 — 15 octobre 2026

**Recherche bilingue, favoris, bibliothèque ; « Maintenant » et « En direct » ; ombres d'éclipse en vraie géométrie ;
fusion lisible.** Fait dans Coupole Web 0.6.0, avec le même moteur de recherche, la même sauvegarde et les mêmes
calculs (cas de référence communs).

- **Recherche bilingue** : en français ou en anglais, quelle que soit la langue de l'interface, la recherche trouve
  le même contenu (modules, animations, questions, fiches, tables, images), affiché dans la langue de l'interface
  (« seasons » → « Simulateur des saisons (NAAP) ») ; accents, casse, pluriels simples et petites fautes tolérés ;
  classement titre > mots-clés > texte ; mots trouvés en gras ; titre de l'autre langue quand c'est lui qui
  correspond ; résultats groupés par type ; « favoris seulement ». Moteur `classe/recherche.py`, identique ligne pour
  ligne à celui du web (`tests/recherche_cas.json`, dont 97 recherches sur les vrais contenus). Le catalogue des
  animations s'en sert aussi.
- **Favoris** : bouton étoile dans les pages (module, question, fiche, table, image, animation), clic droit ou Ctrl+D
  dans les listes, étoile dorée devant les favoris ; section « Mes favoris » de l'accueil ; page « Mes favoris »
  (groupés par type, filtre, tri, Suppr pour retirer). Sauvegarde commune **version 2** (une version 1 se lit telle
  quelle ; export / import avec Coupole Web ; réinitialisation partielle « tous les favoris »).
- **« Mes modules » devient « Collections »**, au second plan (« Mes favoris → Organiser en collections… ») ; la barre
  propose *Modules*, *Bibliothèque*, *Animations*, *Mes favoris*, *Ma progression*.
- **Bibliothèque** : la présentation d'origine de ClassAction, un onglet par type montrant tout le contenu, rangé par
  module dans l'ordre d'origine ; vignettes des images et des animations ; filtres module et favoris.
- **« Maintenant », « En direct », « Ma position »** dans les 19 animations datées : instant de l'ordinateur
  (`datetime.now(timezone.utc)`), affiché dans le fuseau du système (zoneinfo ; « 09:20 heure de Paris (UTC+2) ·
  07:20 TU ») ; heure solaire au méridien du fuseau hors heure d'été, ou à la longitude d'un site choisi ; « En direct »
  s'arrête dès qu'on touche la date ou qu'on relance la lecture. Les anciens boutons « Maintenant » de l'horloge de
  la Grande Ourse (qui prenait l'heure d'été pour l'heure solaire) et « Aujourd'hui » d'Anticythère sont remplacés.
- **Simulateur des ombres d'éclipse** refait : type d'éclipse en vraie géométrie (distance de la Lune telle que placée :
  aucune, partielle, annulaire, hybride, totale ; largeur de la bande ; Lune : règle de Danjon), cônes de la Terre et
  de la Lune, vue 3D de l'orbite inclinée et de la ligne des nœuds, curseurs position et angle aux nœuds, éclipses
  rejouées avec leur géométrie JPL DE440 (`outils/verif_anim/geometrie_eclipses.py`) ; les 133 éclipses de la table
  retrouvent leur type ; distances extrêmes de la Lune 1900–2100 : 356 375 km et 406 712 km.
- **Chaîne proton-proton, cycle CNO** : neutrino νₑ, particules légères reconnaissables et agrandies, étiquettes
  placées sans chevauchement, légende.
- **Glisser** : si rien n'est saisi à l'appui, la saisie est retentée au mouvement ; la toile prend le focus à l'appui.

## 0.7.0 — 14 octobre 2026

**Passe finale avant publication : présentation plus moderne et plus légère, de 1024 × 600 à la 4K, tout essayé
automatiquement, plusieurs plantages et gels corrigés, paquets vérifiés en vrai.**

- **Accueil des modules** : cartes de même largeur en grille (numéro, titre, contenu sans les zéros et au singulier
  pour 1, barre de progression fine), dessinées d'un seul tenant (un widget par carte au lieu de cinq).
- **Navigation** : la vue courante (*Modules*, *Animations*, *Mes modules*, *Ma progression*) est mise en évidence ;
  page de module plus compacte (titre d'origine, progression et actions sur une rangée) ; onglets vides grisés.
- **Questions** : ressources liées à droite en fenêtre large, dans un menu « ★ n » en fenêtre étroite, plus rien
  quand il n'y en a pas ; figure bornée à 45 % de la hauteur (les choix restent visibles en 1024 × 600) ; choix
  sélectionné encadré ; verdict aux couleurs du thème ; icône plein écran lisible dans les deux thèmes.
- **Figures des questions lisibles dans les deux thèmes** : un texte posé sur un fond dessiné (ciel nocturne, ovale
  bleu nuit…) prend une couleur contrastée ; 100 questions étaient touchées dans le thème clair.
- **Schémas** : un texte plus large dans la police du système que prévu est resserré au dessin ; plus aucun
  recouvrement, quelle que soit la police (Windows, macOS, Linux).
- **Fenêtres de fiches, tables et images** : en-tête (genre, titre), taille ajustée au contenu ; tables à lignes
  alternées, la colonne des noms prend la place libre. *Ma progression* : une seule table (plus de double ascenseur).
- **Animations en petite fenêtre** : la scène ne passe plus sous les réglages (la page défile) ; barres de défilement
  fines, survol des listes, aide F1 qui commence par les modules.
- **Nombres** : virgule décimale dans tous les champs en français (débit, rayon de recherche…), dans les tailles et
  les débits (« 78,03 Go », « 66,6 Mo ») de la banque OHP et des archives, dans *Ma machine* et *À propos* ; signe moins
  typographique en *Cosmologie*.
- **Plantages et gels corrigés** : simulateur des configurations planétaires avec deux orbites égales (division par
  zéro) ; molette très rapide sur le globe du jour-nuit ; fenêtre de ressource fermée puis rouverte aussitôt (perdue
  du registre) ; un module dont la construction échoue n'arrête plus l'application ; sélection de la banque OHP
  gardée quand la liste se reconstruit ; style de l'interface posé une seule fois (changement de thème plus court et
  sans repolissage inutile).
- **Performances** : bande de spectre de l'Explorateur de spectres et de la Parallaxe spectroscopique 4 fois plus
  rapide (identique au bit près), axe des températures calculé une fois ; mises en page des rangées de réglages et des
  cartes mémorisées : changement de thème ramené à 0,2–0,3 s, navigation entre pages sous 60 ms.
- **Fiabilité** : l'annonce « Effacé — Annuler » et le clignotement de la réponse utilisent des minuteries rattachées à
  leur page (une minuterie survivait à un changement de langue et visait une étiquette détruite).
- **Tests** : audit automatisé de bout en bout (`tests/test_passe_finale.py`) : les 517 questions notées, textes des
  figures lisibles, les 94 animations (chaque réglage, chaque bouton : aucune exception, budget de temps dans le fil
  graphique), glissers aléatoires sur chaque animation, export → effacement → import identique, import d'un export de
  Coupole Web, langue et thème à chaud, fenêtres rouvertes, effacement puis changement de thème, fermeture et
  réouverture ; suite stable en ordre aléatoire ; essai « fumée » de l'application construite (`python -m
  coupole.essai_fumee`) dans chaque paquet (Windows, macOS, Linux) ; construction d'essai sans publication.
- **Kit commun des applications de bureau** (standard de l'auteur) : mise à jour et rapports d'incident par les
  modules communs `updater.py` et `reporting.py`, identiques au gabarit et réglés par `kit.json` (Coupole n'en garde
  que l'adaptation : paquet `.deb`, pip, lanceur) ; accord des rapports et identifiant d'installation repris sans
  perte ; aucun nom de machine envoyé ; faulthandler armé avant de relever la trace du plantage précédent ;
  `coupole --check` (essai complet sans écran) lancé sur chaque paquet ; installeur Windows bilingue et lien
  permanent `Coupole-Setup.exe` ; paquets Linux `Coupole-X-linux-x86_64.tar.gz` / `-arm64` (installation dans le
  profil, commande `coupole`) ; boîte de fichiers complète de Qt par défaut sous Linux ; logo dans « À propos »
  (une seule source SVG). Mise à jour réelle essayée sous Linux : paquet 0.4.1 publié → 0.7.0 par son ancien module,
  puis 0.7.0 → 0.7.1 par le nouveau, données intactes ; paquet `.deb` installé, vérifié et retiré dans un Ubuntu nu.
- Banque de questions : corrections de la contre-expertise recopiées.

## 0.6.0 — 14 octobre 2026

**Module « Animations » : navigation par les 22 modules de ClassAction, 517 questions, fiches, tables et images,
« Mes modules », sauvegarde de tout ; Orion en 3D refaite ; spectres lissés.**

- **Navigation par modules** : le module s'ouvre sur l'accueil des 22 modules (et deux bonus), avec *Modules*,
  *Animations*, *Mes modules*, *Ma progression*, une recherche FR/EN (questions, animations, fiches, tables, images) et
  un fil d'Ariane. Page de module à onglets *Questions* (W/G/C/D numérotées, état ○ ◐ ✓ ✗), *Animations*, *Fiches*,
  *Tables*, *Images* ; ressources dans des fenêtres séparées (plusieurs à la fois) ; aperçu au survol ; clic droit
  « Ajouter à… ».
- **517 questions** d'après ClassAction (Apache 2.0), mêmes données et même moteur que Coupole Web (empreintes de 8 000
  instances identiques) : menus *Adapter la question*, nouveau tirage, figures vectorielles (QPainter), *Valider*,
  *Montrer la réponse* (clignote en orange), indice, explication, éléments de réponse, « Ce qui a changé », ressources
  liées ★, précédente / suivante, plein écran ; clavier A–H, Entrée, R, I, N, F, ← →.
- **110 fiches, 14 tables, 109 schémas** écrits pour Coupole (widgets Qt, moteur de formules, schémas dessinés par un
  moteur QPainter qui lit leur description avec la largeur réelle des textes, contrôle de non-chevauchement), photos
  libres avec crédit et licence.
- **Mes modules** (créer, copier, renommer, supprimer avec annulation, ajouter, retirer, réordonner) et **sauvegarde
  de tout** dans `sauvegarde.json` (dossier de configuration, écriture atomique, copie précédente) : réglages de chaque
  animation, réponses, scores, tentatives, progression, Mes modules, préférences, au format de Coupole Web (34 cas de
  parité) ; export / import JSON croisé avec le web ; réinitialisation tout ou partie avec confirmation, copie gardée
  et annulation ; page *Ma progression*.
- **Orion en 3D refaite sur le modèle de la Grande Ourse 3D** (étoiles principales à leur distance, Terre, lignes de
  visée, figure sur la sphère céleste, vues *De face* et *De côté*), **M42 et IC 434 / Tête de Cheval en volume**
  d'après leur géométrie publiée, taille agrandie ×12 et signalée ; plus de dépliement ni de photographies ; étiquettes
  plus lisibles ; scène fixe (aucun rendu au repos) ; notes des fiches traduites en anglais.
- **Explorateur de spectres** : intensités calculées tous les 1/8 de type (étalonnage PCHIP, vérifié contre la table
  du modèle : 0,01 sur 100), courbes sans paliers ni cassures ; *contraste pédagogique* des raies (par défaut, dit à
  l'écran) ou *échelle réaliste* ; aussi dans la Parallaxe spectroscopique.
- Manuels FR et EN : section « Modules, questions et ressources (0.6.0) », captures nouvelles ; aide F1 complétée.

## 0.5.0 — 14 octobre 2026

**Module « Animations » : spectres sur bases physiques, « Orion en 3D » (94ᵉ animation), fiches au survol, couleur
vraie des étoiles, règle typographique partout.**

- **Orion en 3D** (nouveau thème « Milieu interstellaire et formation des étoiles », entre Exoplanètes et Voie
  lactée), propre à Coupole : la constellation telle qu'on la voit, puis dépliée progressivement en trois dimensions,
  chaque étoile à sa distance mesurée (SIMBAD, Gaia DR3, Hipparcos 2007, mesures dédiées) avec sa barre d'erreur ;
  nuages moléculaires Orion A et B (Zucker et al. 2021, Großschedl et al. 2018), anneau de λ Orionis, boucle de
  Barnard (Foley et al. 2023), nébuleuse d'Orion en « blister » (Wen & O'Dell 1995, O'Dell et al. 2009), Tête de
  Cheval ; plongée vers M42 et la Tête de Cheval avec les images de l'ESO et de l'ESA/Hubble posées sur le ciel
  (CC BY 4.0, crédit mot pour mot sur la scène et en lien sous la scène). Distances publiées par défaut pour
  Alnilam, Mintaka, Meissa et Hatysa, option « distances mesurées brutes » ; Trapèze à 388 ± 5 pc (VLBA), Gaia DR3
  (402 pc) et Menten et al. 2007 (414 pc) dans la fiche ; option « couleurs accentuées », désactivée par défaut.
- **Fiche au survol, générique** : survol, toucher ou clavier (Tab, flèches, Échap) ouvrent une fiche posée à côté de
  l'objet, jamais dessus, lue par les lecteurs d'écran : noms, type, magnitudes, distance et incertitude, température,
  rayon, luminosité, et la source de chaque valeur. Branchée sur Orion en 3D, la Grande Ourse 3D, l'horloge de la
  Grande Ourse, le lever héliaque, la comparaison des repères et le diagramme HR (321 fiches).
- **Couleur vraie des étoiles** (corps noir → CIE 1931 → sRGB, vérifiée par SageMath) dans ces animations ; diagramme
  HR : case « Couleur = température » ; Grande Ourse 3D : distances mises à jour (parallaxes adoptées par SIMBAD).
- **Spectres sur bases physiques** (Explorateur de spectres, Parallaxe spectroscopique) : Saha–Boltzmann sur des
  atmosphères ATLAS9, courbes lisses par classe, axe en type spectral et en température, 133 raies NIST, bandes TiO et
  CH, continu de Planck coloré ; G2 V = 5 770 K ; cas extrapolés et ancien étalonnage des magnitudes absolues
  signalés à l'écran. Moteur et données copiés tels quels, avec leurs 100 cas de référence.
- **Règle typographique** dans les 94 animations : unités SI (km·s⁻¹, m·s⁻², W·m⁻²…), signe moins « − », espaces
  fines, virgule décimale (aussi dans les champs numériques), puissances de dix en exposant, formules aux
  délimiteurs et radicaux extensibles, indices de mots en romain ; formateur commun au bureau, au web et aux
  ressources ; test sur tous les textes affichés.
- **Mesures** (QPainter hors écran, 720 × 470, NAS chargé) : Orion en 3D 5,5 ms (ciel) à 7,4 ms (3D), 1,7 ms en
  plongée ; Explorateur de spectres 3,3 ms ; Parallaxe spectroscopique 3,4 ms.
- **Vérifié** : SageMath (parsec → année-lumière, distances et barres des fiches, parallaxe du Trapèze, matrice
  ICRS → galactique) ; mêmes nombres et mêmes fiches que Coupole Web (références communes) ; manuels FR (88 p.) et
  EN (86 p.) ; aide F1.

## 0.4.2 — 14 octobre 2026

**Module « Animations » : la machine d'Anticythère en 3D (93ᵉ animation), titres de panneaux qui ne débordent plus,
trois vues d'un spectre corrigé, globe 3D par défaut dans le simulateur jour-nuit.**

- **Machine d'Anticythère** (thème « Astronomie antique », s'ajoute aux 92 animations d'après ClassAction), adaptée
  d'[Anticythere3D](https://github.com/ARP273-ROSE/Anticythere3D), du même auteur : les 33 roues, leurs nombres de
  dents (Freeth et al. 2006, 2008), les rapports exacts, l'implantation des arbres, le tenon et la fente, les cadrans
  et leurs inscriptions grecques, repris à l'identique avec leurs tests. Manivelle saisie à la souris et lecture
  animée ; date, calendrier égyptien (anneau tourné vers l'aiguille du Soleil), zodiaque, phase avec la sphère
  demi-argentée, planètes du Cosmos (relations de période de Freeth et al. 2021, longitude géocentrique par
  l'épicycle), spirales métonique et du Saros avec leur aiguille et les glyphes d'éclipses, cadrans callippique,
  exeligmos et Jeux ; machine fermée ou ouverte (case « Enveloppe »), étages éclatés, face avant, face arrière ou
  trois-quarts ; survol d'une roue : nom, dents, rapport exact, fonction ; lien vers l'application complète.
- **Rendu sans OpenGL** : projection orthographique, caméra par quaternion (jamais d'orientation invalide), algorithme
  du peintre, cadrans gravés mis en cache selon le zoom, dentures simplifiées quand elles deviennent trop petites :
  1 à 4 ms par image fermée, 5 à 9 ms ouverte.
- **Vérifié** : rapports recalculés sous SageMath (métonique 235/19, Saros 223 lunaisons, callippique 1/76,
  exeligmos 235/12711, Lune sidérale 254/19, porte-satellite 477/4237, mois anomalistique, 17 entraxes, ère de
  Nabonassar) ; tests du mécanisme d'Anticythere3D repris ; valeurs identiques à Coupole Web au caractère près.
- **Titres de panneaux** : dans une fenêtre étroite, le titre d'un panneau débordait sur le panneau voisin (Phases de
  Vénus chez Copernic et chez Ptolémée, et 20 autres animations). Il est désormais coupé sur deux lignes, raccourci
  ou terminé par « … », jamais plus large que son panneau ; le titre complet reste en info-bulle et dans le nom
  accessible de la scène ; test des 92 animations à 420 px.
- **Trois vues d'un spectre** : le télescope à 0°, visant le nuage avec l'ampoule devant, annonçait des raies
  d'absorption ; l'ampoule, opaque, cache le nuage : spectre continu. L'ordre le long de la visée est pris en compte
  (absorption seulement si le gaz est entre le télescope et l'ampoule) ; le télescope et son étiquette restent hors
  du halo de l'ampoule.
- **Simulateur jour-nuit** : s'ouvre sur le globe 3D (un choix déjà mémorisé est gardé).
- Manuels FR et EN : section « La machine d'Anticythère », captures nouvelles et régénérées.

## 0.4.1 — 14 octobre 2026

**Module « Animations » : graphismes modernisés, formules mises en forme, étiquettes sans chevauchement, cartes
précises, et les corrections demandées.**

- **Astres en sphères** : Soleil, Lune, Terre et Mars ont du volume (dégradé radial au foyer tourné vers la lumière,
  limbe assombri), un côté nuit au-delà du terminateur quand un Soleil est dans le panneau, et le Soleil un halo
  discret ; phases de la Lune avec le même volume. Vectoriel, lissé, brosses en cache : le rendu reste à environ
  1,5 ms par image (médiane des 92 animations à 720 × 470, comme avant).
- **Formules** : moteur de mise en page maison en QPainter (fractions empilées, exposants, indices, radicaux,
  parenthèses extensibles, × 10ⁿ en vrai exposant, italique mathématique), police STIX Two Math embarquée
  (OFL, sous-ensemble de 139 ko), cache ; sur la toile (calculateur de Newton, algèbre de la gravitation, module de
  distance, petits angles, luminosité, flux, excentricité, hauteur méridienne, vitesse d'une étoile) et dans les
  descriptions, libellés et valeurs.
- **Étiquettes** : placeur commun anti-chevauchement (24 positions autour de l'objet, évitement des objets et des
  textes, trait de rappel, fond semi-transparent) ; un test vérifie les 92 animations à quatre tailles et trois
  instants.
- **Cartes** : côtes Natural Earth 1:50m (domaine public, 65 ko, chargées à la demande) au lieu du tracé grossier de
  l'original ; le simulateur jour-nuit propose quatre projections (équirectangulaire ; polaire Nord ou Sud, jusqu'à
  l'équateur ou aux tropiques, Terre ou terminateur tournant ; globe 3D vu de l'espace à tourner librement, avec
  inertie, molette pour zoomer, double-clic pour revenir au point subsolaire, clic droit pour l'observateur) avec un
  terminateur exact, les crépuscules, le jour et la nuit polaires.
- **Courbe de rotation de la Voie lactée** : plus de cassure au raccord de 5 kpc ; courbe lisse d'un modèle de masse
  publié (McMillan 2017, calculé avec galpy : bulbe, disques, gaz, halo de matière noire, composantes affichables),
  mesures réelles avec barres d'erreur (Eilers et al. 2019, compilation galkin), courbe képlérienne tirée de la
  masse du modèle dans la sphère, Galaxie vue du pôle Nord galactique à l'échelle (barre de Wegg et al. 2015, bras de
  Reid et al. 2019, Soleil à 8,21 kpc, sens de rotation, cercle du rayon choisi).
- **Éclipses** : le Soleil du simulateur des ombres n'est plus tronqué ; « Rejouer une éclipse » montre chacune des
  133 éclipses de la table 2015–2044 en proportions réelles, avec un curseur d'instant.
- **Corrections** : le globe tournait à l'envers du glisser (longitude/latitude et toutes les sphères) ; rayons du
  Soleil qui débordaient du panneau « Vue de la Terre » des saisons ; étiquettes empilées de la Grande Ourse 3D et du
  lanceur de marteau (et la Terre qui sortait de l'image sur un écran très large) ; textes coupés ou superposés en
  petite fenêtre (légendes, horloges, niveaux de l'hydrogène, rayons du Soleil, spectre électromagnétique, ombre du
  bâtiment, phase de la Lune…), trouvés par un audit visuel des 92 animations à 420, 1280 et 2560 pixels de large.
- **Aide** : plus d'info-bulle générique géante sur la scène ; une aide discrète, propre à chaque animation, sous la
  scène. Thèmes dans un ordre pédagogique (Introduction d'abord, Cosmologie à la fin).
- **Version web** : un bouton ouvre l'animation, avec ses réglages, dans Coupole Web
  (arp273-rose.github.io/coupole-web).

## 0.4.0 — 14 octobre 2026

**Module « Animations », lot 3 : les 32 dernières animations ; le catalogue ClassAction est complet (92 sur 92).**

- **Lumière et spectres (8)** : clou chauffé jusqu'à la fusion (couleur et éclat calculés par la loi de Planck et la
  vision humaine, au lieu du film de l'original), courbes du corps noir (cinq courbes, loi de Wien, aire σT⁴/π,
  magnitudes et indices de couleur U, B, V, R), explorateur de spectres (continu, émission, absorption, six familles de
  raies selon le type spectral), spectre électromagnétique (fréquence, énergie du photon, objets de même taille),
  effet Doppler (crêtes émises par une source mobile, signal reçu calculé par le temps retardé, observateur à faire
  glisser), filtres (corps noir, gaussienne ou Soleil ; filtres U, B, V, R, atmosphère, filtre gaussien ; couleur
  perçue), atome d'hydrogène (photons absorbés, ionisation, réémission, niveaux d'énergie, journal), les trois lois
  de Kirchhoff (télescope à faire glisser autour d'un nuage de gaz et d'une ampoule).
- **Exoplanètes (7)** : lanceur de marteau et étoile à planète autour de leur centre de masse, courbe de vitesse radiale
  (Soleil et Jupiter, Soleil et Terre, 51 Pegasi b), le Soleil autour du barycentre du Système solaire (positions
  vraies des planètes de 1800 à 2050), période d'un pulsar en orbite, décalage des raies du spectre, simulateur de
  transits (NAAP, 9 planètes réelles, mesures bruitées), simulateur de vitesses radiales (NAAP, orbites excentriques
  et inclinées, planètes réelles).
- **Étoiles doubles et variables (4)** : binaires à éclipses (NAAP) avec 46 systèmes réels et leurs courbes de lumière
  observées, dont sept « à compléter » ; construction d'une courbe de lumière mesure après mesure ; centre de masse ;
  repliement (roue de charrette vue image par image).
- **Divers (13)** : propriétés des planètes (histogrammes), températures de formation et condensation, la neige vue
  d'une voiture (radiant des étoiles filantes), chaîne proton-proton et cycle CNO (énergie de chaque étape), courbe de
  rotation de la Voie lactée et masse contenue, ondes de densité (tracteur et voitures), univers-ballon et loi de
  Hubble-Lemaître, décalage vers le rouge du spectre de M32, télescope (grossissement, champ, pouvoir séparateur, mise
  au point), capteur CCD (pose et lecture case par case), loi de Snell-Descartes (réflexion totale, Fresnel, Brewster),
  regard vers le passé (supernovæ de 1054 et de 1006).
- **Les films de l'original** (clou, lanceur de marteau, ballon, réactions de fusion, spectre électromagnétique,
  embouteillage…) sont devenus des simulations interactives.
- **Données réelles, sources citées (NOTICE)** : filtres U, B, V, R de Landolt (1992) ; fonctions colorimétriques CIE
  1931 corrigées par Judd et Vos ; spectre de M32 (Santos et al. 2002) ; courbes de lumière du Catalog and Atlas of
  Eclipsing Binaries (numérisées depuis l'original) ; exoplanètes de la NASA Exoplanet Archive (2026) au lieu des
  valeurs de 2007 (ex. HD 209458 b : 1,39 R♃, orbite circulaire) ; planètes de la NASA Planetary Fact Sheet (2026 :
  95 satellites pour Jupiter, 274 pour Saturne) ; masses DE440 et éléments de Standish (JPL) ; excès de masse AME 2020 ;
  courbe de rotation de Gaia (Eilers et al. 2019) au-delà de 5 kpc.
- **Corrections de l'original** : constantes exactes du SI (σ, constante de Wien tirée de x = 5 (1 − e⁻ˣ), h, c),
  hydrogène à 13,598 eV (masse réduite) et hc = 1 239,84 eV nm (l'original : 13,6 et 1 240), transformation sRGB de la
  norme IEC 61966-2-1, période 0,1158 j pour a = 1 R☉ (l'original : 0,1155), brillance des binaires dans le filtre V
  par la loi de Planck, Rayleigh et Dawes en millimètres, éclipses par l'aire exacte de recouvrement des disques.
- **Vérification** : `outils/verif_anim/verif_anim.sage` recalcule les nouvelles grandeurs par d'autres voies (racine
  de Wien, intégration numérique de Planck, lois de Fresnel en sinus et tangentes, temps retardé et vitesses radiales
  par racines et dérivées, aire de recouvrement par intégration, durée de transit de Seager et Mallén-Ornelas,
  barycentre par matrices de rotation) ; tests contre ERFA (barycentre à mieux que 5 × 10⁻⁵ ua), contre les courbes
  observées des binaires, régime établi des ondes de densité ; tests d'interface (souris, atome qui absorbe puis
  réémet, lecture complète du CCD, préréglages).  Rendu ≤ 5 ms par image.
- Aide (F1), manuels FR/EN (tableaux des 92 animations, calculs et résultats du lot 3, captures), README, NOTICE.

## 0.3.1 — 14 octobre 2026

**Module « Animations », lot 2 : la Lune, la Renaissance, l'astronomie antique et les propriétés stellaires ; 60
animations disponibles.**

- **La Lune (12)** : vocabulaire des phases, phases avec un ballon de basket, trois points de vue (Terre, Soleil, œil
  libre), positions et phases de deux corps (l'un peut devenir la lune de l'autre), phases et diagramme d'horizon,
  questionnaire des phases (phase, Lune ou Soleil cachés, avec verdict), plans bissecteurs en 3D, déclinaison de la
  pleine lune, retard synodique (jour sidéral et jour solaire), marées (marée d'équilibre de la Lune et du Soleil,
  force de marée, vives et mortes eaux, niveau chez un observateur), inclinaison de l'orbite lunaire (saisons
  d'éclipses, vue du Soleil à l'échelle), table des 133 éclipses de 2015 à 2044 (zones de visibilité traduites).
- **Renaissance et orbites (9)** : phases de Vénus selon Copernic et selon Ptolémée, simulateur des configurations
  planétaires (arrêt ou pause à chaque configuration), calculateur de période synodique, 3e loi de Kepler, excentricité
  d'une ellipse, algèbre de la gravitation (fraction exacte), loi de la gravitation de l'électron à la Voie lactée
  (mémoire des résultats), orbites autour de la Terre.
- **Astronomie antique (3)** : approximation des petits angles, horloge de la Grande Ourse (ciel du nord en projection
  stéréographique, étoiles de SIMBAD précessées à la date), lever héliaque (année entière, Sirius, Véga…).
- **L'ombre d'un bâtiment** remplace le film de l'original (« Union Seasons Demonstrator ») : simulation de l'ombre
  portée jour après jour, à heure fixe ou au midi vrai ; tout le thème « coordonnées et mouvements » est disponible.
- **Propriétés stellaires (5)** : luminosité d'une étoile (Stefan-Boltzmann), flux (inverse du carré), vitesse d'une
  étoile (Doppler et mouvement propre), parallaxe spectroscopique (spectre, classes de luminosité), diagramme HR (NAAP)
  avec les étoiles les plus proches et les plus brillantes, droites d'égal rayon et comparaison au Soleil.
- **Calculs exacts** : phases moyennes de la Lune et argument de latitude (Meeus 49 et 54), nœud de l'orbite lunaire,
  précession IAU 1976, marée d'équilibre, périodes synodiques, G (CODATA 2018), GM de la Terre, constantes solaires
  nominales de l'UAI (T☉ = 5 772 K), magnitude bolométrique du Soleil 4,74 et facteur 2,5 de Pogson (l'original
  écrivait 2,51189), Hα à 656,28 nm, 1 ua/an = 4,740 47 km/s, jour sidéral par rapport aux étoiles.  Les étalonnages
  empiriques de l'original (type spectral, corrections bolométriques, séquences HR) sont repris tels quels.
- **Vérification** : `outils/verif_anim/verif_anim.sage` recalcule les nouvelles grandeurs sous SageMath (racines
  numériques, matrices de précession, loi des cosinus…) ; tests : chaque éclipse de la table à moins de 1,01 jour d'une
  phase moyenne avec |sin F| < 0,36 et dans une saison d'éclipses, précession contre astropy (10⁻⁴ °), lever héliaque
  de Sirius à 40,8° N le 11 août, orbite géostationnaire de 42 164 km ; tests d'interface (souris, arrêt aux
  configurations, un jour solaire exact) et des clés de texte FR/EN.
- Aide (F1), manuels FR/EN (tableau des 60 animations, huit captures nouvelles, calculs), README.

## 0.3.0 — 14 octobre 2026

**Nouveau module « Animations » (lot 1) : les animations pédagogiques ClassAction refaites en Python.**

- **Module Animations** : les animations ClassAction de l'université du Nebraska-Lincoln (Flash/ActionScript, licence
  Apache 2.0), devenues illisibles avec la fin de Flash, refaites en Python pour Windows, macOS et Linux, dessinées
  en QPainter (3D par projection calculée, sans OpenGL ni dépendance nouvelle), dans le thème sombre par défaut, en
  français et en anglais.  Lecture / pause, vitesse (0,1 à 10 ×), réinitialisation, curseurs et champs numériques,
  valeurs calculées affichées, sphères à faire tourner et objets à déplacer à la souris ; réglages gardés d'une session
  à l'autre ; une seule animation tourne à la fois, et seulement quand elle est affichée.
- **Catalogue** des 92 animations d'origine par thème, avec recherche (FR/EN, sans accents), filtres par thème et par
  état, nom et description dans les deux langues, titre d'origine ; « à venir » pour celles des lots suivants.
- **Lot 1 — 21 animations** : démonstrateur longitude/latitude (globe, côtes, villes, ligne de changement de date),
  mouvements du Soleil (analemme, ombre, lever et coucher), simulateur des saisons (NAAP), phases de la Lune (NAAP),
  rayons du Soleil, azimut/hauteur, coordonnées équatoriales, comparaison des systèmes de coordonnées, temps sidéral et
  angle horaire, simulateur de l'écliptique, obliquité, écliptique (zodiaque, 13 constellations officielles), temps
  sidéral et solaire, plages de déclinaison, ombres d'éclipse (avec la méthode d'Aristarque en proportions réelles),
  orbite de Mars selon Ptolémée, épicycles, mouvement rétrograde, orbite planétaire (NAAP, lois de Kepler), calculateur
  de parallaxe, module de distance.  Comportements et réglages repris du code ActionScript d'origine (décompilé quand
  la source manquait).
- **Et 9 autres animations « coordonnées et mouvements »** (toutes, sauf le film de l'ombre d'un bâtiment) : durée du
  jour, hauteur méridienne, trajectoires du Soleil, vue d'ensemble des mouvements du Soleil, position du Soleil sur
  l'horizon, jour et nuit sur une carte (terminateur, crépuscules), antipodes, Grande Ourse en 3D, repères céleste et
  horizontal.  30 animations disponibles en tout.
- **Calculs exacts** au lieu des approximations d'origine : temps sidéral IAU 1982, obliquité IAU 2006, Soleil et
  équation du temps de Meeus (0,01°), équation de Kepler et vis-viva, parsec et année-lumière de l'UAI, limites des
  constellations de l'UAI.  Vérifiés par `outils/verif_anim/verif_anim.sage` (SageMath, 100 bits, par d'autres voies
  que le code), par les exemples publiés de Meeus et par astropy.
- **Ligne de commande** : `coupole anim liste [--faites] [--json]`, `coupole anim info ID`.
- **Licence** : fichier `NOTICE` (« d'après ClassAction, University of Nebraska-Lincoln Astronomy Education, Apache
  License 2.0 ») et texte de la licence Apache dans `LICENCES/Apache-2.0.txt`, livrés dans les paquets ; paragraphe
  dédié dans le `copyright` du paquet Debian.
- Aide F1, info-bulles, manuels FR/EN (chapitre « Animations », captures), README.  Tests : `tests/test_anim_calculs.py`
  (calculs contre SageMath, Meeus et astropy) et `tests/test_anim_gui.py` (catalogue, chaque animation créée hors
  écran, animée et dessinée, réglages gardés, souris, panneau, ligne de commande).

## 0.2.3 — 12 octobre 2026

**Plus de limite de débit par défaut.**

- **Demande d'utilisateur : « enlever la limite de vitesse de téléchargement ».**  Jusqu'en 0.2.2, tout
  téléchargement (Banque OHP, Archives, ligne de commande) était plafonné à 8 Mo/s par défaut.  Désormais **aucun
  plafond par défaut** : les téléchargements vont à la vitesse de la connexion.  Valeur 0 ou vide = illimité,
  partout (`debit_max_mo_s`, `archives_debit_mo_s`, `--debit 0`).
- **Le plafond reste disponible** pour qui veut brider sa connexion : Préférences et onglet Traitement, case
  **« Limiter le débit »** puis la valeur, plage étendue de **0,1 à 1 000 Mo/s** (au lieu de 0,5 à 20).  Le plafond des
  Préférences vaut aussi pour les Archives (sauf réglage propre `archives_debit_mo_s`).
- **Migration** : une installation qui avait gardé l'ancien défaut (8 Mo/s enregistré) passe à illimité au premier
  lancement de la 0.2.3 ; une autre valeur, choisie par l'utilisateur, est conservée.  Migration faite une seule
  fois : un plafond de 8 Mo/s choisi ensuite reste en place.
- **Estimation des durées sans plafond** : « Tout télécharger » (interface et `coupole ohp tout`) estime la durée
  d'après le **débit mesuré** lors des téléchargements précédents (mémorisé à la fin de chaque traitement, seulement
  s'il dit quelque chose du réseau et pas du plafond) ; au plafond s'il est posé et plus lent ; sinon « selon la
  connexion ».  Pendant un téléchargement, le temps restant suit toujours le débit réellement mesuré.
- **La courtoisie envers les serveurs publics demeure** : User-Agent qui nomme Coupole, nombre de téléchargements
  simultanés borné (3 par défaut, 4 au plus pour la Banque OHP ; 2 pour les Archives), une recherche par seconde au
  plus par service, reprise d'un fichier interrompu.  Seul le plafond de débit disparaît.
- Textes FR/EN, info-bulles, aide F1, aide des commandes, manuels FR/EN (Préférences, téléchargement, « Tout
  télécharger », Archives) et captures mis à jour ; tests `tests/test_debit_libre.py`.

## 0.2.2 — 12 octobre 2026

**Archives des observatoires : comprendre ce qu'on télécharge par rapport à ce qu'on prend avec son télescope.**

- **Retour d'utilisateur (Windows, 0.2.1) : « je ne comprends pas ce que j'obtiens ».** Diagnostic sur ses vrais
  téléchargements : M 16 donnait une image « noire sauf un bout à droite » — produit Hubble « skycell » (mosaïque
  multi-visites) de 19 806 × 15 741 pixels (2,49 Go chez MAST) dont le filtre F775W n'occupe qu'un coin — et un
  masque pleine taille de 312 Mo ; Arp 273 donnait 17 fichiers pour 3 filtres (pour chaque filtre : `drz` du
  pipeline par visite, mosaïque d'une visite, mosaïque multi-visites, plus deux images de détection « total »).
- **Recadrage automatique sur la zone utile** : la WCS suit (CRPIX décalés ; `CROPX0`, `CROPY0`, `ORIGNAX1`,
  `ORIGNAX2`), tailles avant et après dans la barre d'état, la fiche et le journal. M 16 : 762 × 5 217 pixels.
- **Rien d'autre que le produit préparé par défaut** : ni fichier d'origine, ni masque. Le masque devient une
  option (entiers 8 bits compressés, après recadrage) ; sans lui, l'alignement tient les 0 exacts pour « sans
  donnée ».
- **Un produit logique par filtre**, choisi d'après la documentation de MAST et de DrizzlePac : la mosaïque
  multi-visites (toutes les poses, corrigées de la CTE, grille commune à tous les filtres), sinon par visite la
  mosaïque d'une visite (SVM, alignée sur Gaia), sinon le pipeline standard ; JWST : la mosaïque `c…`, sinon
  l'observation la plus longue. Les autres produits des mêmes poses deviennent des **variantes** (case « Montrer
  les variantes »), les images de détection sont écartées ; la fiche dit pourquoi. Arp 273 : 3 produits au lieu de 17.
- **Nature des données en clair** : colonnes « nature » (pose unitaire, produit combiné, mosaïque, image de
  détection) et « pose totale » (« 8 × 650 s = 5 200 s (1 h 27 min) ») ; badges « Produit final » et « Pose
  calibrée » ; niveau de calibration expliqué ; aide sur les unités (électrons/s, MJy/sr : pas des ADU, d'où
  l'image noire sans étirement) ; explication de drz/drc (CTE), SVM/MVM et « skycell ».
- **Noms lisibles et rangement par champ** (comme la Banque OHP) :
  `Archives/<champ>/<cible>_<instrument>_<filtre>_<date>_<type>_<n>x<pose>s.xisf` ; identifiant de l'archive dans
  l'en-tête et la fiche. **Réorganiser les téléchargements** (bouton et `coupole archives reorganiser`) : renomme,
  range, recadre, supprime les masques pleine taille et met les variantes à part, sans jamais écraser, journalisé.
  Essai sur une copie des vrais téléchargements : 18 fichiers rangés, 11 recadrés, 16 masques supprimés,
  1 641 → 910 Mo.
- **Recherche tolérante.** « jupiter », « saturne » ne donnaient rien : le nom était envoyé à SIMBAD (qui ne connaît
  pas les planètes) et l'échec arrêtait toute la recherche ; de plus OPUS rend Voyager puis Cassini et la limite de
  lignes coupait Cassini. Désormais : table FR/EN des corps du Système solaire (Jupiter, Saturne, Io, Titan,
  Encelade, Japet, Phœbé…), cherchés **par nom de cible** dans MAST (cible mobile), Voyager/Cassini et Juno ; limite
  partagée entre missions ; noms usuels (« Piliers de la Création », « Carène », « HUDF ») et numéros de catalogue
  réécrits (« m16 », « ngc6611 », « arp273 ») ; suggestions pendant la frappe ; propositions si introuvable.
- **Catalogue des cibles sans critère** (nouvel onglet, `coupole archives catalogue`) : Hubble (mosaïques
  multi-visites), JWST, ESO, Voyager, Cassini, Juno ; les plus observées d'abord, par type d'objet, pages de 100,
  cache de 30 jours, requêtes agrégées (`GROUP BY target_name`) ; programmes célèbres vérifiés (HDF, HUDF, HUDF09,
  HUDF12, Piliers 1995/2014/2022, Carène, Quintette de Stephan, Anneau austral, Arp 273).
- **Taille affichée d'emblée** (annoncée, ou mesurée en fond, plus de bouton « Estimer ») et total de la sélection.
- **Aperçus.** MAST fournit des JPEG pleine résolution (jusqu'à 19 806 × 15 741 px) que la 0.2.1 tronquait à 3 Mo :
  lus en entier, décodés réduits, recadrés sur la zone utile ; vignettes de l'ESO ; sinon vignette générée après
  téléchargement ; sinon la raison.
- **Progression** : débit, temps restant (fichier et total), barre en deux phases (téléchargement puis
  préparation), état final « Terminé : N fichiers, X téléchargés, Y gardés, Z erreurs — Ouvrir le dossier ».
- **Guide Hubble Ultra Deep Field** (onglet, `coupole archives hudf`) : programmes, poses `flt`/`flc` contre
  produits HLSP déjà empilés (XDF, HUDF09, HUDF12), temps de pose par filtre vérifiés sur MAST, préréglage
  « couleur en 3 filtres » (XDF F435W, F775W, F160W, 3 × 110 Mo).
- **Topo instruments et filtres** (onglet, info-bulles des noms de filtres, `coupole archives instruments`, chapitre
  du manuel) : Hubble, JWST, ESO, Spitzer, WISE, 2MASS, SDSS, Keck, Voyager, Cassini, JunoCam ; champ, échelle,
  longueurs d'onde ; équivalent amateur (L, R, V, B, Hα, OIII, SII) ; sources officielles citées.
- Essais réels : Jupiter (Hubble), Saturne (Cassini), Arp 273 (produit le plus léger, 218 Mo), HUDF09 F160W ;
  cellule de M 16 recadrée depuis une copie des fichiers existants. Manuels FR/EN, aide F1, méthode
  (`docs/archives_methode.md`, section 5) mis à jour.

## 0.2.1 — 9 octobre 2026

**Possession reconnue sous Windows sur un lecteur réseau ; bibliothèques facultatives embarquées dans tous les
paquets.**

- **Possession non reconnue sous Windows (retour d'utilisateur).** Une copie complète de la banque sur un partage
  SMB, vue par une lettre de lecteur réseau (`O:\OHP_DU_ECU`), apparaissait entièrement possédée sous Linux et
  « tout à télécharger » sous Windows, base d'état en journal DELETE. **Cause** : l'URI SQLite de lecture était
  construite par `Path.resolve().as_uri()` ; sous Windows, `resolve()` remplace la lettre d'un lecteur réseau par
  le chemin UNC du partage, et `as_uri()` en fait `file://serveur/partage/…`, que SQLite refuse (« invalid uri
  authority »). L'erreur était avalée : base illisible → rien de possédé, sans un mot. Les chemins UNC tapés
  directement (`\\serveur\partage\…`) n'étaient pas touchés. Mêmes conséquences pour les anomalies du traitement
  et la base du module Archives sur un lecteur réseau.
- **Corrections.** URI construite sans résolution (`file:///O:/…`, `file:////serveur/partage/…`, caractères
  spéciaux échappés). Lecture de la base d'état par **copie locale** (cache de l'utilisateur, refaite seulement si
  la base change) quand le dossier est sur un partage ou que la base est en WAL (`-wal` recopié et reporté) ;
  lecture directe en secours, et inversement. Une base WAL sur un partage n'est donc plus jamais illisible depuis
  Windows.
- **Ne plus jamais échouer en silence.** Base de suivi présente mais illisible : **bandeau d'erreur** dans la Banque
  OHP (« La base de suivi de ce dossier n'a pas pu être lue : … ») avec la cause, message sur la sortie d'erreur en
  ligne de commande, et ligne dans `coupole.log`. Chaque lecture y est notée (dossier, base de travail, copie ou
  lecture directe, nombre d'images possédées lues), de même que chaque synchronisation avec un partage (sens,
  base de travail utilisée).
- **« Dossier de suivi : <chemin> — N images possédées lues »** dans la ligne de résumé de la Banque OHP et dans la
  barre d'état : le dossier réellement lu, et ce qu'on y a trouvé.
- **Reconnaître les fichiers existants.** Si `_traitement/` manque alors que des images converties sont rangées,
  le bandeau le propose : l'en-tête de chaque fichier (`OHP:Source:URL`, sinon `HISTORY « converti de … »`) donne
  l'image d'origine, inscrite comme possédée avec son chemin relatif ; en fond, avec progression ; rien n'est
  téléchargé, déplacé ni réécrit. Ligne de commande : `coupole ohp reconnaitre --dest DOSSIER`. La réorganisation
  préfère désormais l'adresse complète de l'en-tête au seul nom de fichier.
- **Rafraîchir l'inventaire** relit aussi la possession (vérifié par un test).
- **Bibliothèques facultatives embarquées.** Les paquets autonomes (installeur Windows, .dmg, tar.gz, .deb)
  n'embarquaient pas `reproject` : le module Archives retombait sur un rééchantillonnage bilinéaire de scipy. Ils
  embarquent désormais `reproject` (avec `astropy-healpix`, `dask`, `zarr`), `sep`, `psutil` et `lxml` ; seul CuPy
  (carte NVIDIA, inutilisé) reste à part. Chaque paquet construit les importe et les fait tourner (petit
  rééchantillonnage, extraction SEP) à son essai en CI, sinon la publication échoue. « Ma machine » et « À propos »
  affichent les bibliothèques facultatives présentes et absentes, avec leur version.
- Intégration continue Windows : le vrai partage administratif `C$` de la machine (nom de la machine, pas « localhost » que SQLite tolère) en UNC **et** par une lettre de lecteur réseau
  posée par `net use` (DRIVE_REMOTE), base en WAL puis en DELETE, premier lancement sans base de travail et base de
  travail ancienne d'un essai antérieur.

## 0.2.0 — 9 octobre 2026

**Nouveau module « Archives des observatoires » : les images publiques des grands observatoires et des sondes,
actuelles et passées, comme la Banque OHP.**

- **Archives couvertes.** Étape 1 : **MAST** (Hubble, JWST, GALEX) par le service TAP officiel (vue
  `dbo.obspointing` : filtres, date de publication, investigateur, adresse du produit et de la vignette), **ESO**
  (TAP ObsCore, produits réduits « Phase 3 »), **IRSA** (Spitzer SEIP, AllWISE, 2MASS, par SIA 2 qui donne
  l'adresse directe et la taille). Étape 2 : **NOIRLab** (piles et images rééchantillonnées), **Keck/KOA**
  (poses brutes de NIRC2, OSIRIS, MOSFIRE), **SDSS** (images calibrées u g r i z) ; **Gemini** signalé (compte
  exigé même pour les données publiques), **SMOKA** signalé (formulaire web seulement). Étape 3 : **Voyager ISS** et
  **Cassini ISS** par OPUS (nœud Anneaux et Lunes du PDS), **JunoCam** par l'Atlas du PDS Imaging Node. Adresses
  dans `sources.json` (version 3), modifiables.
- **Recherche** par nom (SIMBAD puis Sesame) ou coordonnées (degrés ou sexagésimales) et rayon, ou par corps du
  Système solaire (noms français acceptés : Saturne, Encelade…) ; filtres mission, instrument, filtre, dates ; par
  défaut **produits finaux seulement** (JWST `_i2d`, Hubble `_drz`/`_drc`, Phase 3, SEIP, Atlas) et **données
  publiques seulement** ; une observation est gardée si son centre est dans le cercle ou si son empreinte contient
  la cible ; les plus proches d'abord ; réponse tronquée signalée ; archives interrogées en parallèle, une panne
  n'arrête pas les autres.
- **Volume avant téléchargement** : tailles annoncées ou mesurées (requête d'un octet, échantillon par instrument
  au-delà de 60 fichiers), confirmation au-delà de 2 Go (réglage `archives_seuil_go`) ; débit plafonné (8 Mo/s),
  deux fichiers à la fois, reprise d'un fichier interrompu ; un serveur qui refuse les requêtes partielles (ESO)
  est repris depuis le début (`core/reseau.telecharger`).
- **Préparation** : extension scientifique (SCI) des FITS à extensions, un fichier par détecteur pour les poses à
  plusieurs détecteurs de l'ESO, WCS (SIP comprise), unité `BUNIT` et constantes photométriques, dates, programme,
  investigateur ; NaN remplacés par 0 avec un **masque** ; **crédit** de l'archive dans l'en-tête (`CREDIT`) et
  conditions d'usage dans la fiche ; XISF Float32 (bornes = minimum et maximum des données) ou FITS Float32 ;
  entiers avec BZERO lus sans projection mémoire.
- **Formats planétaires** (lecteur maison, sans dépendance) : PDS3 (label attaché ou détaché, pointeurs en
  enregistrements ou en octets, préfixes de ligne, mise à l'échelle), VICAR, PDS4 ; lignes retournées pour que
  l'image s'affiche comme dans l'archive. Label PDS3 de Cassini qui place l'image une ligne trop tôt : données lues
  d'après l'en-tête VICAR.
- **Rangement** `<sortie>/Archives/<mission>/<cible>/<instrument>/<filtre>/`, base d'état et journal bilingue dans
  `Archives/_etat` (même logique de partage réseau que la Banque OHP), **possession** (pastilles), `coupole
  archives bilan`.
- **Alignement** par l'astrométrie : grille d'une image ou grille optimale, rééchantillonnage bilinéaire,
  adaptatif ou exact (bibliothèque **reproject**, facultative : `pip install ".[alignement]"`) ou bilinéaire par
  scipy sans elle ; unités par pixel corrigées du rapport des surfaces de pixel ; recadrage sur le plus grand
  rectangle commun ; **composition couleur** dans l'ordre des longueurs d'onde (3 filtres : bleu, vert, rouge ;
  davantage : palette chromatique), aperçu PNG, `composition.txt` avec l'expression PixelMath.
- **Interface** : nouveau module dans la barre latérale (onglets Recherche et Alignement, vignette et fiche de
  l'observation, lien vers la page de l'archive, menu « Ouvrir avec »), info-bulles, aide F1, français et anglais ;
  **ligne de commande** `coupole archives liste | chercher | estimer | telecharger | preparer | aligner | bilan`.
- **Méthode et sources** : `docs/archives_methode.md` (pratiques publiées pour retraiter les données de JWST et
  Hubble, documentations des archives, de Siril et de reproject, mesures sur les services réels).
- **Essais réels** (fichiers effacés ensuite) : JWST MIRI `i2d` F770W et F1130W des Piliers de la Création (153 Mo
  chacun), Hubble WFC3/IR `drz` F110W et F160W, ESO APEX/LABOCA et HAWK-I (4 détecteurs), Spitzer MIPS, AllWISE
  W1–W4, 2MASS J, NOIRLab, SDSS g r i de M 51 (composition couleur), Keck NIRC2, Voyager 1 (Io, `GEOMED`), Cassini
  (Encelade, `CALIB`), JunoCam (RDR) ; alignements MIRI seul, MIRI + WFC3/IR, SDSS gri.
- **Tests** : `tests/test_archives.py` (réponses simulées de chaque archive, géométrie, coordonnées, extraction,
  PDS3/VICAR/PDS4, alignement d'étoiles synthétiques avec et sans reproject, conservation du flux, téléchargement
  sur serveur local avec coupure, reprise et serveur sans requêtes partielles, 50 000 observations : filtres, tri,
  possession, tableau de l'interface) ; essai réseau `tests/test_archives_reseau.py` (`COUPOLE_TEST_RESEAU=1`).

## 0.1.12 — 9 octobre 2026

**« Ouvrir avec → PixInsight » ouvre vraiment l'image, et plus aucun lancement n'est silencieux.** Retour
d'utilisateur (Manjaro/KDE, 0.1.11) : rien ne se passait, et `coupole.log` ne disait rien.

- **Journal de chaque lancement** : *Ouvrir*, *Ouvrir avec*, *Ouvrir l'emplacement*, dossier de la cible ou du lot,
  manuel, `JOURNAL.txt`, `LOT.txt` — méthode, programme, arguments, numéro de processus dans `coupole.log` ; si le
  programme s'arrête dans les 3 premières secondes, son code de retour et le début de ce qu'il a écrit (sortie et
  erreurs capturées). Le résultat s'affiche dans la barre d'état (« Ouverture dans Siril… », programme introuvable,
  arrêt immédiat avec son message). Toujours une liste d'arguments, jamais d'interpréteur de commandes (garde-fou :
  test qui refuse tout `shell=True`).
- **PixInsight (Linux)** : lancé par son script `PixInsight.sh` (le binaire seul ne démarre pas, d'après l'éditeur).
  Ce script reconstruit ses arguments par un `eval` et n'entoure de guillemets que ceux qui contiennent une espace :
  un chemin avec `$`, `` ` ``, `'`, `(`, `*`… serait interprété → il reçoit alors un lien symbolique temporaire au
  nom sans caractère spécial. Windows : `PixInsight.exe` ; macOS : `open -a` (nouvelle instance : `open -n -a …
  --args -n`).
- **PixInsight déjà ouvert** : sans option, il confie l'image à l'instance ouverte et sort (« Yielded execution to
  running application instance #1 ») ; occupée par un script, elle n'ouvre rien. Nouveau réglage *Préférences >
  PixInsight déjà ouvert* : nouvelle fenêtre (`-n`, **par défaut**) ou envoyer à la fenêtre ouverte (essai). Quand
  une instance tourne, le menu propose les deux ; si PixInsight cède la main, la barre d'état le dit.
- **Double-clic** : si l'application associée a un `.desktop` sans `%F` (cas d'un `pixinsight.desktop` écrit à la
  main : `xdg-open` lançait PixInsight sans l'image), Coupole le détecte (`xdg-mime`) et lance le logiciel
  directement ; l'aide (F1) et le manuel expliquent comment corriger ce `.desktop` (Coupole n'y touche pas).
- **Siril en flatpak** : `flatpak run --file-forwarding … @@ fichier @@` ; si le bac à sable ne voit pas le dossier
  (réglage `flatpak override`), message avec la commande à taper. **N.I.N.A.** grisé dans *Ouvrir avec* : il
  n'ouvre pas une image passée en argument (ses options, vérifiées dans son code : profil, séquence, débogage).
  ASTAP et Aladin : programme direct, chemin tel quel.
- Les programmes lancés n'héritent plus du thème Qt choisi par Coupole pour ses propres dialogues.
- **Dépôt public : aucune donnée personnelle.** Manuels, historique, audits, code, tests et outils relus : noms,
  chemins d'une infrastructure personnelle, machines et matériel remplacés par des formulations neutres (« retour
  d'utilisateur », `/mnt/partage/OHP_DU_ECU`…) ; captures refaites avec un dossier personnel et une machine
  génériques ; `tests/test_confidentialite.py` parcourt tous les fichiers du dépôt (texte, texte des PDF, PNG, .gz,
  chaînes des binaires) et échoue sur ces motifs. Le dossier du traitement de référence des tests se donne par
  `COUPOLE_REFERENCE`.
- README : badges (Python, licence, systèmes, version, tests, langues).

## 0.1.11 — 9 octobre 2026

**Une copie faite avant Coupole s'ouvre enfin, les menus se cliquent, « Ouvrir un fichier » de Spectres et séries
s'ouvre sous KDE, et le module Qualité mesure vraiment les poses de N.I.N.A. et de l'ASIAIR — seulement les poses de
ciel.** Retours d'utilisateur (Linux/KDE, 0.1.10, dossier de sortie `/mnt/partage/OHP_DU_ECU`).

- **Objets possédés (4/4, pastille verte) mais rien à ouvrir.** La copie d'un utilisateur a été produite par l'ancien script
  `ohp_xisf.py`, dans un conteneur : sa base d'état ne note que le chemin absolu d'alors
  (« /srv/ancien/OHP_DU_ECU/… »), introuvable sur le poste. Coupole retrouve maintenant chaque fichier dans
  le dossier de sortie courant, dans cet ordre : chemin relatif noté dans la base (`info.chemin`, nouveau), `final`
  s'il est dans le dossier, `_traitement/journal.csv` (adresse puis fichier d'origine ; lu une fois, en cache, relu
  s'il change), ancienne racine ou dossier de type, puis nom attendu dans le dossier du lot (calcul du rangement,
  « _2 » compris). Jamais le chemin absolu d'une autre machine. Vérifié sur la vraie copie (lecture seule) :
  **7 625 images retrouvées en 0,34 s**, 300 tirées au sort toutes présentes ; ancienne racine et nom attendu donnent
  les mêmes chemins que le journal (7 625/7 625, 100/100).
- **Migration** : les chemins trouvés par le journal sont notés dans la base d'état, en fond, une fois, groupés
  (0,8 s pour 7 625 images), par la base de travail locale recopiée si le dossier est sur un partage ; jamais pendant
  un traitement ; un échec ne change rien (le journal continue de servir). `coupole ohp metadonnees --reecrire` note
  aussi les emplacements (d'après les fichiers trouvés, puis le journal).
- **Dossier de la cible** : à défaut de chemin, le dossier attendu `<sortie>/<type>/<objet>` s'il existe. Double-clic,
  *Ouvrir*, *Ouvrir avec*, *Ouvrir l'emplacement*, *Ouvrir le dossier de la cible*, *Voir les lots*, encadré et
  complétude des lots vérifiés sur une reproduction réduite de la vraie copie (20 lignes réelles de la base et du
  journal), aussi sous un partage simulé.
- **Relancer un traitement vers une telle copie** ne casse plus rien : le rangement rapporte `final` au dossier courant
  (il aurait cherché à déplacer des fichiers « absents » et réécrit `journal.csv` avec des « ../.. ») ; une base
  d'`ohp_xisf.py` en mode WAL est passée en journal DELETE avant d'être écrite (sinon la recopie vers le partage ne
  voyait rien de neuf), un `-wal` non vide sur le partage bloque la recopie comme un `-journal`.
- **Menus contextuels cliquables sous KDE** : plus d'info-bulle dans les menus (celle d'une entrée grisée s'ouvrait
  par-dessus le menu et en captait la souris) ; le motif est dans le libellé (« Ouvrir avec (rien de téléchargé) »)
  et en barre d'état au survol ; menus ouverts par `popup` (plus de boucle imbriquée), détruits à la fermeture.
- **Spectres et séries, « Ouvrir un fichier » ne faisait rien sous KDE** : le filtre « (*.fits *.fit …) » n'avait pas
  de nom ; le portail XDG le refuse (« invalid filter: name is empty », reproduit avec xdg-desktop-portal-kde réel :
  aucune fenêtre ; corrigé : fenêtre « Ouvrir un fichier — Portal »). Tous les dialogues passent par un filtre
  normalisé (nom, motifs sans doublon), une fenêtre parente visible, un dossier de départ qui existe ; chaque
  ouverture, son résultat ou son exception sont notés dans `coupole.log`. Test de chacun des 13 boutons de dialogue.
- **Qualité : lecteur XISF tolérant.** Les 70 poses N.I.N.A. d'un utilisateur (caméra de 61 Mpx, zlib+sh) étaient
  refusées (« incomplete FITSKeyword » : N.I.N.A. écrit `CD1_1` sans commentaire) et le résultat restait vide sans
  rien dire. La lecture des fichiers des autres logiciels accepte mots-clés sans commentaire ni valeur, `Metadata`
  absente (ASIAIR), propriétés inconnues, éléments en plus, images couleur ; seul ce qui empêche de lire les pixels
  est refusé. Nos fichiers restent contrôlés strictement (`xisf.verifier`). Pose réelle : 4,2 s, 1 170 Mo de pointe
  (calcul en float32), FWHM 2,08 px = 3,5″ à 1,695″/px, 400 étoiles ; processus limités d'après la taille des images.
- **Jamais d'échec silencieux** : colonne *état* (mesurée, erreur avec motif lisible, exclu), résumé « N image(s)
  trouvée(s), M pose(s) de ciel mesurée(s), K en erreur (format XISF non lu : …), X fichier(s) de calibration
  exclu(s) », pile dans `coupole.log`, code de sortie 1 en ligne de commande si rien n'a pu être mesuré.
- **Qualité : poses de ciel seulement.** Exclusion à l'inventaire, sans ouvrir les fichiers, par le dossier (Flat(s),
  Dark(s), Bias, Offset(s), Calibration, Master(s), cosmetized, registered, Plats, Noirs…) et le nom (`FLAT_`, `DARK_`,
  `BIAS_`, masters, sorties WBPP `_c`, `_cc`, `_r`…, même famille que l'expression d'astrosolver), puis à la mesure
  par l'en-tête (`IMAGETYP`, `FRAME`, `Observation:Image:Type`). Case *Inclure aussi les poses de calibration*,
  option `--avec-calibration`, liste *Fichiers exclus…*.

## 0.1.10 — 9 octobre 2026

**Le traitement fonctionne vers un dossier sur un partage réseau.** Le dossier de sortie d'un utilisateur est sur le NAS
(partage SMB monté par cifs sous Manjaro) : télécharger les nouveautés, *Tout télécharger* ou réorganiser vers ce
dossier échouait.

- **Cause (reproduite sur un vrai serveur Samba, montage cifs par défaut)** : SQLite ne peut pas écrire à travers les
  verrous de plage SMB — « database is locked » au bout de 60 s, base d'état de 0 octet. La lecture seule
  (possession, nouveautés, anomalies) et la copie de fichiers fonctionnaient.
- **Base de travail locale** : sur un partage (cifs, nfs, sshfs, gvfs, kio-fuse ; smbfs sous macOS ; UNC ou lecteur
  réseau sous Windows), ou si SQLite n'arrive pas à écrire en 3 s, la base d'état est tenue dans le dossier de cache
  de l'utilisateur (une par dossier de sortie) et **recopiée sur le partage toutes les 30 s**, en fin de session, à
  l'arrêt et à l'annulation : instantané cohérent, `PRAGMA integrity_check`, copie dans un fichier temporaire du
  partage relue et comparée (SHA-256), puis remplacement d'un coup. Aucun verrou n'est posé sur le partage : pas de
  verrou orphelin possible, et le NAS ou un autre ordinateur voient toujours une base complète. Journal et barre
  d'état : « Dossier sur un partage réseau : base de travail locale, recopiée sur le partage toutes les 30 s ».
- **Au démarrage** : base du partage plus récente (traitée ailleurs) → reprise ; écritures non recopiées après un
  plantage → recopiées. **Deux écrivains** (deux ordinateurs, ou le NAS) : rien n'est écrasé, Coupole prévient et
  propose une **fusion** (le statut le plus avancé gagne : convertie > doublon > échec), les deux bases d'origine
  sont gardées ; ligne de commande `coupole ohp fusionner --dest DOSSIER`.
- Possession, nouveautés et anomalies lisent la base de travail quand elle est à jour (pas de lecture page par page
  sur le réseau). `coupole ohp metadonnees --reecrire` met aussi à jour la base d'état sur un partage.
- Manuels : section « Dossier de sortie sur un partage réseau » (Linux, macOS, Windows), dépannage ; aide de la
  Banque OHP. Audit : `docs/AUDIT2_2026-10.md` § 10 ; banc Samba reproductible `outils/audit2/samba/`.

## 0.1.9 — 9 octobre 2026

**Le module Qualité démarre tout de suite sur un partage réseau, les logiciels d'astronomie ouvrent vraiment nos
fichiers, et PixInsight trouve focale et pixel.** Retours d'utilisateur (Manjaro, 0.1.8, dossier sur un partage SMB).

- **« Inventaire du dossier… » interminable sur un partage SMB : cause trouvée et mesurée.** Sur un vrai partage
  Samba monté par le client cifs du noyau, SQLite ne peut pas écrire à travers les verrous de plage SMB (« database
  is locked ») : le cache des mesures était ouvert trois fois sur le partage avant la première mesure, 30 s
  d'attente chacune — 90,4 s d'inventaire pour 831 XISF, et aucun cache au bout (fichier de 0 octet, retrouvé sur le
  NAS). Le cache ne s'écrit plus jamais sur un partage (dossier de cache de l'utilisateur ; un ancien cache du
  partage est relu ; repli local en 3 s si une base locale est verrouillée).
- **Inventaire en flux** : la mesure commence au premier lot trouvé, pendant que l'inventaire continue (« 1 234
  fichiers trouvés dans 56 lots… », *Arrêter* immédiat). Aucun fichier ouvert pendant l'inventaire, taille et date
  tirées de la liste du dossier (un `stat` au plus par image) ; dans une sortie Coupole, seuls les dossiers des lots
  sont lus (`INDEX_LOTS.csv`, sinon la base d'état copiée d'un bloc) ; 32 fils de lecture sur un partage. Gros
  dossier : l'échantillon est mesuré d'abord et la question (échantillon ou tout) est posée sans arrêter la mesure,
  avec une durée tirée des images déjà mesurées. Mesuré sur le vrai partage : 92,7 s avant la première mesure
  (latence 10 ms) → inventaire complet en 0,24–0,57 s, premier résultat en 0,2–0,6 s ; à 20 ms : 0,57–1,05 s.
- **Titres de colonnes jamais tronqués** (« étoiles mesurées » apparaissait « toiles mesurée ») : chaque section
  garde au moins la largeur de son titre, titre entier en info-bulle, dans tous les tableaux (test à 100, 150 et
  200 %). Info-bulles des onglets de la Banque OHP sur chaque onglet (elle restait affichée par-dessus le groupe
  « Solution astrométrique »).
- **Cosmologie** : côte à côte, le tableau prend la largeur de ses colonnes (la colonne « valeur » n'est plus coupée)
  et les courbes le reste ; empilés, toutes les lignes si la place le permet, courbes d'au moins 300 px.
  *Affichage > Disposition de la Cosmologie* : automatique (hystérésis 1 550 / 1 450 px), côte à côte ou empilée,
  gardée avec la position du séparateur de chaque disposition. **Unités** non ambiguës : km s⁻¹ Mpc⁻¹, km s⁻¹,
  mag arcsec⁻² (CSV et console cp1252 : `km s^-1 Mpc^-1`).
- **Compatibilité vérifiée, pas supposée** : Siril 1.2.x ne lit pas le XISF ; 1.4.0 et 1.4.4 (AppImage officielles,
  essai réel) lisent tous nos codecs bit à bit mais gardent les flottants en ADU hors de leur plage [0, 1] ;
  N.I.N.A. 3.2 ne décompresse pas zstd et ramène tout flottant à [0, 1] sans lire `bounds` (image blanche) ; ASTAP
  ne lit que le XISF non compressé ; PixInsight (code PCL) inchangé. Tableau « qui lit quoi » dans les manuels et
  sous la liste des formats.
- **Nouveau format « XISF compatible N.I.N.A. et Siril »** (`--format xisf16`) : UInt16 avec un piédestal de 1 000 ADU
  (`PEDESTAL`), compression zlib+sh comme N.I.N.A. Perte mesurée sur 66 poses de la banque : arrondi ≤ 0,5 ADU,
  fond moyen changé de 0,014 ADU au plus, 0,012 % de pixels écrêtés en haut ; sans le piédestal, une pose de 10 s
  au fond sur-soustrait perdait 99,75 % de ses pixels. Le défaut PixInsight ne change pas.
- **Ouvrir une image** : double-clic sur une image possédée (Banque OHP, Qualité) → application du système ; clic
  droit → *Ouvrir avec* (seulement les logiciels installés qui lisent vraiment ce fichier, les autres grisés avec la
  raison) et *Ouvrir l'emplacement du fichier* (fichier sélectionné : Explorateur, Finder, Dolphin/Nautilus par
  D-Bus). Objets : *Ouvrir le dossier de la cible*, *Voir les lots de cet objet*.
- **Possédé ≠ empilable ensemble** : colonne « lots » et répartition par champ, instrument et filtre dans
  l'info-bulle (« 840 images rangées en 9 lots : champ 1 T120 : B 200 · V 300 · R 300 ; … »).
- **Focale et pixel pour PixInsight et N.I.N.A.** : `FOCALLEN` accordé à l'échelle mesurée (7 234,1 mm au lieu de
  7 200 pour le T120, ancienne valeur en HISTORY) et propriétés `Instrument:Sensor:XPixelSize`,
  `Instrument:Camera:XBinning`… (ce que lit ImageSolver, vérifié dans le code de PixInsight) ; onglet Lots : encadré
  « Pour PixInsight / N.I.N.A. » (focale, pixel effectif, binning, échelle, champ, centre, boutons Copier),
  colonnes focale/pixel/échelle masquables, mêmes valeurs dans `LOT.txt` ; `coupole ohp metadonnees DOSSIER
  --reecrire` complète les fichiers déjà convertis sans toucher aux pixels.
- **Guide ASTAP** : le lien « D80 en zip » de la page officielle est mort (le D80 n'existe qu'en .exe, .pkg et .deb) ;
  hors Debian, extraction sûre du `.deb` (vérifiée sur le vrai paquet) ; Arch/Manjaro : rien dans le PATH, `astap`
  graphique GTK2 introuvable dans les dépôts officiels, `astap_cli` suffit (et Coupole le préfère désormais partout) ;
  un test de l'intégration continue vérifie chaque lien pour chaque système.
- Trois petits fichiers d'essai pour les testeurs dans `tests/donnees/` (XISF par défaut, XISF compatible, FITS).

## 0.1.8 — 9 octobre 2026

**Le vrai explorateur de fichiers du système, et voir d'un coup d'œil ce qu'on possède déjà.** Retours d'usage sous
Manjaro (KDE Plasma, paquet autonome 0.1.7, dossier de sortie sur un NAS).

- **Dialogues de fichiers natifs sous Linux** : le paquet autonome embarque son propre Qt, qui ne peut pas charger le
  greffon du bureau installé sur le système ; le dialogue « Dossier de sortie » retombait sur celui de Qt, en anglais
  et sans les emplacements du système (le NAS monté dans Dolphin était inatteignable). Au démarrage, avant la
  création de l'application et si l'utilisateur n'a rien imposé (`QT_QPA_PLATFORMTHEME`), Coupole regarde en moins
  d'une seconde si le **portail XDG** est disponible avec un moteur qui sait choisir des fichiers, et le prend :
  Dolphin sous KDE, Fichiers sous GNOME. Sinon, sous un bureau GTK, le dialogue GTK ; sinon le dialogue de Qt,
  traduit, avec dans sa barre latérale les dossiers personnels, `/media`, `/mnt`, `/run/media/$USER`, les partages
  ouverts dans le gestionnaire de fichiers (gvfs) et les montages cifs, nfs, sshfs. Essai réel dans un conteneur
  (Xvfb, bus de session, `xdg-desktop-portal`) : le dialogue s'ouvre dans `xdg-desktop-portal-kde` sous KDE et
  `xdg-desktop-portal-gtk` sous GNOME, rattaché à la fenêtre de Coupole. Windows et macOS gardent leur dialogue
  natif (Explorateur, Finder) : aucun réglage ne le désactive. Tous les choix de fichiers passent par un seul
  module (`gui/fichiers.py`), avec la fenêtre parente.
- **Préférences > Boîtes de dialogue de fichiers** : *Système* (défaut) ou *Qt*, au cas où le portail serait cassé
  chez quelqu'un ; bilingue, avec info-bulle.
- **Textes fournis par Qt en français** (boutons standard, menus contextuels des champs, dialogue de repli) :
  catalogue `qtbase_fr` chargé, rechargé à chaque changement de langue ; les deux libellés que Qt 6 ne traduit pas
  encore (« Voir dans », « Fichiers de type ») sont complétés par l'application. Les paquets gardent les greffons
  `libqxdgdesktopportal`, `libqgtk3` et les traductions : la construction échoue s'ils manquent (Linux, macOS,
  Windows), et le `.deb` est vérifié dans un conteneur nu.
- **Dossier sur un NAS** : manuels et aide de l'écran expliquent comment choisir un partage (Linux : gvfs, kio-fuse,
  cifs/nfs ; macOS : Se connecter au serveur ; Windows : lecteur réseau ou chemin UNC). Chemins UNC corrigés : la
  base d'état était ouverte par une URI SQLite `file://serveur/…` que SQLite refuse (autorité non vide) ; chemins
  longs `\\?\UNC\…` ; montages gvfs et kio-fuse reconnus comme partages réseau.
- **Ce qu'on possède, visible dans la liste des objets** : pastille en tête de ligne aux couleurs de la légende
  (coche verte : tout possédé, doublons écartés compris ; demi-disque : en partie ; triangle orange : au moins un
  échec ; flèche : rien), nom de l'objet de la même couleur (contraste ≥ 4,5 dans les deux thèmes), info-bulle
  « 12 possédées / 12 · 0 à télécharger · 0 échec(s) · 3 doublon(s) écarté(s) ». La colonne « possédé » suit le nom
  (au lieu d'être hors de vue à droite ; un ordre choisi à la main est gardé, l'ordre d'origine d'avant la 0.1.8 est
  migré) et trie par état. La légende, avec l'état « en partie », est placée sous les deux listes.
- **Résumé de la possession** dans la ligne de l'inventaire (par exemple « possédées : 7 625 (+ 220 doublons écartés), échecs :
  0, à télécharger : 0 ») ; **listes vides qui s'expliquent** en leur centre : « Choisissez un ou plusieurs objets… »,
  « Tout est déjà téléchargé dans … » ; au premier lancement, le premier objet est choisi.
- **Changer de dossier de sortie** relit sa possession en fond (un résultat périmé est ignoré) et la barre d'état
  l'annonce (« Possession recalculée : N images trouvées dans … »).
- **Lanceur du paquet Linux** : `Coupole.sh` suit les liens symboliques (lien de lien compris, sans `readlink -f`,
  absent de macOS avant 12.3) ; un lien `~/.local/bin/coupole` échouait (« …/.local/bin/python/bin/python3 : aucun
  fichier »). `installer.sh` crée lui-même ce lien et signale un `~/.local/bin` absent du `PATH` ; le lanceur d'un
  paquet déjà installé est réparé par l'application au démarrage (la mise à jour ne remplace que `app/`).
- Tests : `test_dialogues_systeme.py` (+27, certains propres à Linux ou à Windows : décision du thème selon le bureau, sonde du portail, préférence,
  dialogue parenté et natif ou Qt, traductions de Qt, élagage des paquets, URI UNC, chemin gvfs, UNC réel sous
  Windows, lanceur par lien et lien de lien, réparation du lanceur, installeur), `test_catalogue_possession.py`
  (+16 : états agrégés, tri par état, pastilles et couleurs, colonnes, listes vides, résumé, changement de dossier).

## 0.1.7 — 9 octobre 2026

**Correction d'un plantage intermittent** (fermeture brutale de l'application, environ une fois sur cinq dans la
série de tests la plus exposée, jamais au même endroit en apparence).

- **Cause** : le ramasse-miettes de Python, qui libère les objets liés entre eux par des références circulaires, se
  déclenchait dans le fil qui allouait de la mémoire à ce moment-là — souvent un fil de calcul (chargement de
  l'inventaire, sondes, tuiles de carte). Une fenêtre fermée qui n'était plus retenue que par ces références
  circulaires était alors détruite **par ce fil de calcul**, pendant que le fil de l'interface servait encore les
  minuteurs de ses widgets : un minuteur du panneau Banque OHP lisait un champ déjà détruit (« wrapped C/C++ object
  of type QLineEdit has been deleted »), et PyQt6 arrête alors le processus.
- **Correction** : le ramassage automatique est remplacé par un ramassage à cadence fixe (toutes les 100 ms) dans le
  fil de l'interface (`coupole/gui/fil_graphique.py`) ; tout objet Qt est désormais détruit dans ce fil. Les
  ramassages complets sont bornés (au plus un toutes les 10 s et 2 % du temps) pour ne jamais geler l'interface.
- Panneau Banque OHP fermé : ses étapes d'affichage en attente et ses minuteries sont arrêtées. Écriture différée
  des réglages : une erreur imprévue est journalisée, jamais fatale.
- **Garde permanente dans les tests** : un test échoue si une méthode d'affichage est appelée hors du fil de
  l'interface, si Qt signale un objet manipulé depuis un autre fil, ou si le ramasse-miettes tourne hors du fil de
  l'interface (`COUPOLE_GARDE_FIL=1` l'active aussi dans l'application).
- Tests : `test_fil_graphique.py` (+6), qui reproduisent l'ordre exact du plantage (fenêtre fermée, puis fil de
  calcul qui alloue) et échouent sur la 0.1.6. Budget du test de chargement à dix fois la banque porté à 1,2 s sur
  l'intégration continue (×3 la mesure la plus lente observée : 0,39 s sur macOS) ; 0,3 s en local.

## 0.1.6 — 9 octobre 2026

**Réglages conservés d'une fermeture à l'autre** : tout ce qui se règle à l'écran et tous les chemins saisis sont
retrouvés au lancement suivant (manuel, section « Réglages conservés »).

- **Fenêtre** : taille, position, écran, état maximisé ; garde-fous : écran débranché ou position hors des écrans →
  fenêtre recentrée, taille plus grande que l'écran → ramenée sur l'écran (compatible avec l'interface adaptative, à
  100, 150 et 200 %). Taille de chaque dialogue (et onglet des Préférences).
- **Disposition** : module affiché, onglet de la Banque OHP, séparateurs, largeur et ordre des colonnes, colonne et
  sens du tri de chaque tableau (les colonnes continuent de s'ajuster au contenu tant qu'on n'a pas choisi leurs
  largeurs).
- **Banque OHP** : recherche, type, télescope, cases « nouveaux », « à vérifier », « à télécharger », « sans dates
  douteuses », nuit, filtre, objets choisis (rétablis dès l'inventaire chargé), filtres des anomalies et de la carte
  du ciel. Onglet Traitement : dossier de sortie gardé **dès qu'il est modifié** (et non plus seulement au lancement
  d'un traitement), format, langue des noms, « garder les doublons », « garder les FITS », mode ASTAP, « vérifier la
  qualité » ; un changement du dossier dans les Préférences est repris par l'onglet.
- **Qualité des images** : dossier analysé, mode échantillon et N. **Spectres et séries** : dossier du dialogue
  d'ouverture, menu **Récents** (10 fichiers, un fichier disparu est grisé), axe. **Cosmologie** : jeu de paramètres,
  paramètres personnalisés (gardés même en repassant par Planck), Ωk, z, option SH0ES, et nouvelle **échelle des
  courbes** (distances en logarithmique ou en linéaire). **Sites et heures** : site choisi, zoom et centre de la
  carte, « carte en ligne ».
- **Dialogues de fichiers** : chacun rouvre dans le dernier dossier utilisé (exports CSV, réorganisation, ASTAP,
  signalement…).
- Mécanisme unique (`core/etat_interface.py`, `gui/memoire.py`) : `interface.json` versionné à côté de
  `reglages.json` ; écriture **différée et groupée** (au plus une toutes les 2 s, plus une à la fermeture), atomique,
  seulement si quelque chose a changé — jamais une écriture par frappe ; lecture tolérante (clé absente, type faux,
  valeur hors bornes → défaut ; fichier illisible mis de côté) ; existence des chemins vérifiée en fond (un partage
  réseau absent ne bloque pas le démarrage). Rien de dangereux à rejouer n'est gardé : un traitement n'est jamais
  relancé seul.
- **Réinitialiser** : Préférences > « Réinitialiser la disposition » (immédiat, réglages intacts) et
  `coupole --reinitialiser-interface` (`--reset-interface`).
- Tests : `test_reglages_conserves.py` (+11) — deux fenêtres successives retrouvent chaque élément ; réglages
  corrompus ou de mauvais types → défauts ; position hors écran, écran disparu, fenêtre maximisée ; aucune écriture
  disque pendant la frappe (puis une seule, groupée) ; réinitialisation. Chaque test part d'une disposition vierge.

## 0.1.5 — 9 octobre 2026

Les deux lenteurs laissées par le second audit (`docs/AUDIT2_2026-10.md`, § 8), mesurées à dix fois la banque
(80 000 lignes) ; aucun résultat affiché ne change (ordres de tri identiques à la 0.1.4 sur la banque réelle et à
×10, cellules, anomalies, carte du ciel, lots identiques).

- **Chargement sans gel** : plus long silence du fil graphique pendant le chargement **0,55–0,8 s → 55–66 ms** à
  80 000 lignes (0,16 s → 40 ms sur la banque). Ce n'était plus un calcul du fil graphique mais la concurrence
  pour le GIL : carte du ciel, anomalies et possession tournaient dans trois fils en même temps que le premier dessin
  des tables, et chaque rappel de Qt vers Python attendait le GIL. Ils sont désormais calculés en série par le fil
  de chargement, avant la remise de l'inventaire ; l'affichage se fait ensuite par étapes courtes ; le chargement
  part 0,2 s après le premier dessin de la fenêtre (catalogue prêt ~0,2 s plus tard qu'avant).
- **Tri par l'heure du site et par les drapeaux** : clés entières calculées une fois au chargement (en fond), tri
  numpy : **0,66–0,78 s → 50–60 ms** à 80 000 lignes ; toutes les colonnes de la table des images ont maintenant une
  clé rapide (40–80 ms à 80 000 lignes) et le double tri demandé par `QTableView.sortByColumn` n'est plus refait.
- « Tout sélectionner » sans filtre ne parcourt plus l'inventaire (liste déjà triée reprise telle quelle).
- Tests : `test_echelle.py` (+4) — chargement réel à 80 000 lignes sans silence > 100 ms (budget ×3), tri des
  colonnes heure du site / drapeaux < 150 ms (×3), chaque clé rapide égale à l'ordre des cellules sur la banque
  réelle, tri numpy identique à `sorted`.

## 0.1.4 — 9 octobre 2026

Second audit de performance, en usage réel et à pleine échelle (`docs/AUDIT2_2026-10.md`) : chaque fonction qui peut
durer chronométrée sur la banque entière (7 625 XISF), sur un partage réseau simulé (2 ms par accès) et, pour
l'interface, à dix fois la banque (80 000 lignes). 33 constats, tous corrigés ; aucun résultat de calcul changé.

- **Grandes listes fluides** : tri par une clé par ligne dans le modèle (et non par comparaisons Python deux à deux :
  4 s → 0,1–0,2 s pour 80 000 images, 0,3–0,5 s → 0,05 s sur la banque) ; table des images **paresseuse** (cellules
  calculées pour les lignes affichées seulement) : « tout sélectionner » 2,5 s → 0,06–0,37 s à 80 000 images, 0,48 →
  0,04 s sur la banque ; l'en-tête des tableaux ne parcourt plus toutes les lignes à chaque dessin après « tout
  sélectionner » (0,77 s → 0,02 s, rendu identique) ; changer de thème ne recalcule que les couleurs (1 s → 0,02 s ;
  7,4 s à 80 000 lignes) ; filtre du catalogue en une passe ; anti-rebond de la sélection.
- **Rien de lent dans le fil graphique** : index des lots, estimation (place libre comprise), possession et comptes par
  objet, points de la carte du ciel calculés en fond ; carte du ciel : survol 14 ms → 0,1 ms ; carte du monde :
  décodage des tuiles borné à 30 ms par dessin, cache LRU ; tracé des spectres : survol 30 ms → 1 ms ; export CSV en
  fond ; médoïdes et groupement des champs en numpy (0,63 et 0,67 s → 0,07 et 0,09 s, résultats identiques).
- **Partage réseau (NAS)** : base d'état validée au plus une fois par seconde (au lieu de 3 fois par image : 7,7 s →
  0,07 s pour 100 écritures), JOURNAL.txt écrit par paquets, doublons notés en une passe (12,5 s → 0,06 s) ; rangement
  final sans rien à déplacer **60,7 s → 1,5 s** (LOT.txt et INDEX_LOTS.csv réécrits seulement s'ils ont changé, plus
  de `stat` par fichier ni de parcours complet) ; 48 images vers une destination sur le partage : 20,3 → 4,9 s.
- **Réorganiser** : plus de parcours de l'inventaire pour chaque fichier (61 millions de comparaisons), en-têtes lus
  par plusieurs processus, **progression affichée et Arrêter** (interface et ligne de commande) ; banque entière :
  243 → 57 s (borné par la lecture des disques).
- **Qualité** : un seul parcours du dossier (en parallèle), tailles et dates lues en parallèle, cache lu en une
  requête, plan du dialogue repris par le moteur : relancer sur la banque déjà mesurée par un partage **72 s → 2 s** ;
  QUALITE.csv réécrit au plus toutes les 5 s et en fin de lot (et non après chaque image : O(n²) octets par lot) ; cache
  validé par paquets. **Correctif** : la table triait FWHM, fond, RSN… comme du texte.
- **Correctifs** : la vérification des nouveautés ouvrait la base de la destination en écriture ; la lecture des
  doublons de pixels pour le rapport d'anomalies pouvait lever une exception.
- Tests : +21 (`tests/test_echelle.py`, budgets de temps tolérants et compteurs exacts : écritures, validations,
  lectures par image) ; outils de mesure dans `outils/audit2/`.

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
