# Historique

Version anglaise : [CHANGELOG.en.md](CHANGELOG.en.md).

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
