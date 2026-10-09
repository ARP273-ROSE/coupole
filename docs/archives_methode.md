# Archives des observatoires : où chercher, quoi télécharger, comment aligner

Synthèse des pratiques publiées par les amateurs qui retraitent les données publiques de Hubble et de JWST, des
documentations des archives et de celles des outils d'alignement, et de ce qu'en applique le module **Archives**
de Coupole (0.2.0).  Les mesures citées ont été faites sur les services réels le 9 octobre 2026.

## 1. Sources consultées

| Source | Ce qu'on en retient |
|---|---|
| Cloudy Nights, « Working with JWST data from STScI / MAST » (forum Experienced Deep Sky Imaging, novembre 2022), https://www.cloudynights.com/forums/topic/848552-working-with-jwst-data-from-stsci-mast/ | Fil fondateur (traitement des Piliers de la Création à partir des fichiers de MAST dans PixInsight).  **Contenu non lisible ici** : le forum répond 403 aux lectures automatiques et aucune copie n'existe dans les archives du web (web.archive.org : aucun instantané).  Seuls son titre, sa date et son sujet ont pu être vérifiés ; rien de ce document n'en est tiré au-delà. |
| Galactic Hunter, « How to Download Raw Data from the James Webb Space Telescope », https://www.galactic-hunter.com/post/jwst-data | Recherche avancée de MAST (mission JWST, nom de la cible, instrument NIRCam seul) ; dans le dossier de niveau 3, garder les `*_i2d.fits`, ignorer les `*_segm.fits` ; un jeu complet pèse « des centaines de gigaoctets » ; couleur attribuée selon la longueur d'onde du filtre ; PixelMath pour composer. |
| Astronomy, « How to process JWST images like a pro », https://www.astronomy.com/observing/process-jwst-images-like-a-pro/ | Seules les extensions `i2d` « SCI » sont utiles ; filtres rangés par longueur d'onde (F187N → bleu, F356W → vert, F470N → rouge) ; alignement (StarAlignment) sur le filtre du milieu ; étirement à partir de l'auto-étirement, points noirs réglés par canal. |
| Sky at Night Magazine, « How to produce your own space images using James Webb Space Telescope data », https://www.skyatnightmagazine.com/astrophotography/astrophoto-tips/produce-images-using-james-webb-space-telescope-data | Portail de MAST, recherche avancée, colonne « date de publication » pour ne voir que les données déjà publiques. |
| Tutoriel JWST (S. Rugheimer), https://sarahrugheimer.com/JWST_Tutorial.html | Les `i2d` font 1 à 5 Go ; dans une même observation NIRCam, les images de la voie courte sont déjà alignées entre elles, de même pour la voie longue : seul l'alignement entre voies est nécessaire ; Siril (alignement global par les étoiles) ou PixInsight ; couleur par longueur d'onde. |
| Hubble Legacy Archive, aide, https://hla.stsci.edu/hla_help.html ; HST Data Handbook (ACS), « Types of ACS files », https://hst-docs.stsci.edu/acsdhb/chapter-2-acs-data-structure/2-1-types-of-acs-files | Produits « drizzlés » : `*_drz.fits` (combinés, corrigés de la distorsion) et `*_drc.fits` (de plus corrigés de l'efficacité de transfert de charge, ACS/WFC et WFC3/UVIS) : préférer `drc`, sinon `drz`.  Extensions SCI, WHT, CTX. |
| Documentation de Siril, « Registration », https://siril.readthedocs.io/en/stable/preprocessing/registration.html | Depuis la 1.3, l'alignement **astrométrique** (d'après la WCS de chaque image, distorsions SIP comprises en 1.4) est le mode conseillé pour des images d'instruments ou de champs différents. |
| Documentation de reproject, « Celestial images », https://reproject.readthedocs.io/en/stable/celestial.html | `reproject_interp` : le plus rapide, pas de conservation du flux, moins bon si les pas diffèrent beaucoup ; `reproject_adaptive` : anti-crénelage, plus exact quand les pas diffèrent ; `reproject_exact` : « drizzle » exact, lent, **perte de précision sous 0,05″ par pixel** ; le rééchantillonnage suppose une **brillance de surface** : une image en flux par pixel doit être convertie. |
| Rector et al. 2007, AJ 133, 598, « Image-processing techniques for the creation of presentation-quality astronomical images » | Ordre chromatique : la longueur d'onde la plus courte en bleu, la plus longue en rouge, les autres réparties entre les deux. |
| Services : MAST TAP (https://mast.stsci.edu/vo-tap/api/v0.1/caom), ESO TAP ObsCore (https://archive.eso.org/tap_obs), IRSA SIA 2 (https://irsa.ipac.caltech.edu/SIA), NOIRLab (https://astroarchive.noirlab.edu/api), KOA TAP, SkyServer (SDSS), OPUS (https://opus.pds-rings.seti.org/api), PDS Imaging Atlas | Schémas lus (`TAP_SCHEMA`), réponses examinées, temps de réponse mesurés (voir § 3). |

## 2. Bonnes pratiques retenues, et ce que Coupole en fait

1. **Télécharger les produits finaux, pas les poses.**  JWST `*_i2d.fits` (niveau 3), Hubble `*_drc.fits` ou
   `*_drz.fits`, produits « Phase 3 » de l'ESO, mosaïques Spitzer SEIP, images Atlas de WISE et 2MASS.
   → Case « Produits finaux seulement », cochée par défaut ; « tous les niveaux » pour les poses calibrées.
2. **Seulement ce qui est public.**  Les données sont réservées à l'équipe pendant une période (souvent 12 mois) ;
   leur date de mise à disposition est publiée.  → Case « Données publiques seulement » (date de publication
   passée et, pour MAST, `datarights = PUBLIC`).
3. **Le volume avant tout.**  Une `i2d` NIRCam des Piliers fait 5,4 Go ; le jeu complet de la même observation
   (6 filtres NIRCam + 3 MIRI) 19,6 Go ; une `i2d` MIRI 153 Mo ; une `drz` WFC3/IR 37 à 87 Mo ; une `drz`
   ACS/WFC classique plus de 200 Mo.  → « Estimer le volume » : tailles annoncées (ESO, IRSA, NOIRLab, PDS) ou
   mesurées par une requête d'un octet (MAST, OPUS), échantillon par instrument au-delà de 60 fichiers ;
   confirmation au-delà de 2 Go (réglage `archives_seuil_go`).
4. **Courtoisie envers les serveurs.**  → User-Agent qui nomme Coupole, débit plafonné (8 Mo/s par défaut),
   deux téléchargements à la fois, une recherche par seconde au plus par service, reprise d'un fichier interrompu
   (requête partielle) plutôt que de tout recommencer, aucune requête au démarrage.
5. **N'ouvrir que l'image scientifique.**  Les FITS des pipelines ont une extension principale vide et des
   extensions SCI, ERR, WHT… → extraction de l'extension SCI (ou, pour une pose à plusieurs détecteurs de l'ESO,
   un fichier par détecteur), avec sa WCS (distorsions SIP comprises), son unité (`BUNIT`), les constantes
   photométriques (`PHOTMJSR`, `PHOTFLAM`, `PIXAR_SR`…), les dates, le programme, l'investigateur.
6. **Les NaN.**  Les bords des mosaïques JWST et HST et les pixels rejetés valent NaN ; PixInsight les traite
   mal.  → NaN remplacés par 0, masque `_masque.fits` (1 = donnée) gardé à côté et relu par l'alignement.
7. **Aligner par l'astrométrie, pas par les étoiles.**  Les archives fournissent une WCS exacte ; entre deux
   instruments (NIRCam et MIRI, Hubble et JWST) les étoiles changent d'aspect et de nombre (diffraction,
   saturation, poussière opaque en visible et transparente en infrarouge), ce qui met en défaut l'alignement par
   étoiles.  → Rééchantillonnage sur une grille commune (celle d'une image, ou grille optimale) avec reproject,
   ou scipy si reproject manque ; recadrage sur le plus grand rectangle couvert par toutes les images.
8. **Unités.**  Une brillance de surface (MJy/sr de JWST) ne change pas avec le pas du pixel ; une quantité par
   pixel (électrons/s de Hubble, nanomaggies de SDSS) doit être multipliée par le rapport des surfaces de pixel.
   → Fait automatiquement d'après `BUNIT`.
9. **Couleurs dans l'ordre des longueurs d'onde.**  → Composition proposée : 3 filtres = bleu, vert, rouge ;
   davantage = teintes réparties du bleu au rouge ; aperçu PNG (étirement asinh) et expression PixelMath
   (identifiants d'image tels que PixInsight les donne) dans `composition.txt`.
10. **Créditer.**  « NASA/ESA/CSA, STScI » (JWST), « NASA/ESA, STScI » (Hubble), « ESO » et le programme,
    « NASA/JPL-Caltech » (Spitzer), etc.  → Crédit dans la fiche et dans l'en-tête de chaque fichier produit
    (`CREDIT`, `COMMENT`), conditions d'usage de chaque archive dans la fiche.

## 3. Choix techniques par archive (mesurés le 9 octobre 2026)

* **MAST** : la table `ivoa.obscore` du TAP n'a ni filtre, ni date de publication, ni investigateur, ni adresse du
  produit ; la vue `dbo.obspointing` les a (`filters`, `t_obs_release`, `datarights`, `proposal_pi`, `dataurl`,
  `jpegurl`).  `CONTAINS(POINT, CIRCLE)` dépasse le délai de la passerelle (504 après 60 s) ; une boîte sur
  `s_ra`/`s_dec`, triée par distance (`ORDER BY`), répond en 1 à 2 s.  L'API « Mashup » (`Mast.Caom.Cone`) répond
  en 74 s sur M 42 : écartée.  Téléchargement : `Download/file?uri=mast:…` (requêtes partielles acceptées).
  TESS (cubes de pleine image), Kepler (pas d'image de champ) et Pan-STARRS (service de découpes séparé) ne sont
  pas proposés.
* **ESO** : `ivoa.ObsCore` ne contient que des produits Phase 3 ; `INTERSECTS(s_region, CIRCLE)` en 0,4 à 5 s ;
  `access_estsize` en ko ; fichier `dataPortal/file/<dp_id>` anonyme, **sans requêtes partielles** (416 dès
  l'octet 0 : Coupole recommence alors sans en-tête Range).  Les « pawprints » (HAWK-I 4 détecteurs, VISTA 16,
  OmegaCAM 32) donnent un fichier par détecteur.
* **IRSA** : le TAP ne donne qu'une adresse DataLink (une requête de plus par image) ; le service **SIA 2** rend
  les mêmes colonnes avec l'adresse directe, la taille et le rôle (`science`, `weight`, `noise`) : interrogé par
  collection (`spitzer_seip`, `wise_allwise`, `twomass_allsky`).
* **NOIRLab** : recherche avancée JSON, produits `stacked`/`resampled`, `release_date`, `.fits.fz`.
* **KOA** : TAP par instrument ; seulement des poses brutes d'imagerie (aucune avec « produits finaux ») ;
  téléchargement anonyme, sans requêtes partielles.
* **SDSS** : table `Field` (SkyServer DR18), fichiers `frame-*.fits.bz2` de DR17 (calibrés, WCS).
* **Gemini** : « Login Required » pour l'accès anonyme (protection contre les robots) : **compte gratuit exigé**
  même pour les données publiques ; signalé, rien n'est téléchargé.
* **SMOKA** : formulaire web seulement, données surtout brutes : signalé, **non pris en charge**.
* **OPUS** (Voyager, Cassini) : recherche par corps, dates, filtre ; produit Voyager `_GEOMED` (calibré, distorsion
  du vidicon corrigée, 1000 × 1000), Cassini `_CALIB` (CISSCAL).  Les fichiers sont au format VICAR avec un label
  PDS3 détaché ; pour Cassini, le label place l'image à l'enregistrement 2 alors qu'une ligne binaire la précède
  (taille du fichier : 2 × 4096 + 1024 × 4096 octets) : Coupole lit les données d'après l'en-tête VICAR.
* **PDS Imaging Atlas** (JunoCam) : Solr ; produits RDR (calibrés) ; une image est un empilement de *framelets*
  (bandes de 128 lignes, 4 filtres) : converti tel quel.

## 4. Ce qui n'est pas géré

* Reconstruction des images JunoCam (projection des framelets d'après la géométrie SPICE) : non faite.
* Fichiers PDS compressés (codage de Huffman des EDR de Voyager), réels VAX, entrelacement BIL/BIP à plusieurs
  bandes, tableaux PDS4 à plus de trois axes : refusés avec un message.
* Cubes (spectroscopie intégrale de champ, MUSE, NIRSpec IFU), spectres : hors du périmètre (images seulement).
* Compte Gemini : non géré.  SMOKA : non géré.
* La WCS complète des `i2d` JWST (modèle GWCS de l'extension ASDF) n'est pas lue : on emploie la WCS FITS que le
  pipeline écrit dans l'en-tête de l'extension SCI (sur une `i2d`, image déjà rééchantillonnée sur un plan
  tangent, elle décrit la grille de sortie).
* La précision de l'alignement est celle des astrométries fournies par les archives : entre deux missions (ou
  deux programmes anciens de Hubble), un écart résiduel de l'ordre du pixel peut subsister.  Le contrôle
  automatique sur l'essai réel (étoiles détectées sur F160W de WFC3/IR, F110W de WFC3/IR et F770W de MIRI après
  rééchantillonnage sur la grille de F160W) donne un écart médian d'environ 1 pixel WFC3/IR (0,13″) entre les deux
  filtres de Hubble et d'environ 2,6 pixels (0,34″) avec MIRI, sur peu d'étoiles et avec une détection sommaire
  (nébulosité) : à prendre comme un ordre de grandeur.  Pour une superposition parfaite, affiner ensuite par les
  étoiles (StarAlignment de PixInsight, alignement global de Siril) sur les fichiers déjà rééchantillonnés : il ne
  reste alors qu'une petite translation à corriger.

## English summary

The **Archives** module follows the practices published by amateurs who reprocess Hubble and JWST public data
(Galactic Hunter, Astronomy, Sky at Night Magazine, a JWST tutorial; the founding Cloudy Nights thread could not be
read: the forum refuses automated reads and no web-archive copy exists) and the documentation of the archives,
Siril and reproject: download final products only (`i2d`, `drc`/`drz`, ESO Phase 3, SEIP, Atlas), public data only,
estimate the volume first and confirm beyond a threshold, be polite to servers, extract the SCI extension with its
WCS, units and photometric keywords, handle NaN with a mask, align by astrometry (reprojection onto a common grid)
rather than by stars, correct per-pixel units for the pixel-area ratio, colour the filters in chromatic order, and
always credit the archive.  Gemini (account required) and SMOKA (web form only) are reported, not downloaded.
