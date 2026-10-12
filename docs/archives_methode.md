# Archives des observatoires : où chercher, quoi télécharger, comment aligner

Synthèse des pratiques publiées par les amateurs qui retraitent les données publiques de Hubble et de JWST, des
documentations des archives et de celles des outils d'alignement, et de ce qu'en applique le module **Archives**
de Coupole (0.2.0 à 0.2.2).  Les mesures citées ont été faites sur les services réels le 9 octobre 2026.

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
4. **Courtoisie envers les serveurs.**  → User-Agent qui nomme Coupole, débit libre par défaut depuis 0.2.3 (plafond réglable ; 8 Mo/s jusqu'en 0.2.2),
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

## 5. Version 0.2.2 : rendre les produits compréhensibles

Retour d'utilisateur sur la 0.2.1 : « je ne comprends pas ce que j'obtiens ».  Diagnostic sur de vrais
téléchargements (copie en lecture seule) et vérifications sur les services, le 12 octobre 2026.

| Source | Ce qu'on en retient |
|---|---|
| MAST, « HAP Single Visit Mosaics Now Available » (décembre 2020), https://archive.stsci.edu/contents/newsletters/december-2020/hap-single-visit-mosaics-now-available | Mosaïques d'une visite : toutes les poses d'une visite, filtres alignés entre eux et sur Gaia (`WCSNAME` contient `FIT_SVM_GAIA`), même grille orientée nord en haut ; trois niveaux : pose, filtre, « total » (image de **détection** pour les catalogues). |
| MAST, « Multi-Visit Mosaics from Hubble Now Available » (mai 2022), https://archive.stsci.edu/contents/newsletters/may-2022/multi-visit-mosaics-from-hubble-now-available | Mosaïques multi-visites : toutes les observations publiques ACS et WFC3 d'un champ, sur une grille prédéfinie ; cellules de 0,2° (21 × 21 par cellule de projection de 4,2°), 0,04″/px (WFC3/IR aussi 0,12″/px, « coarse ») ; alignées sur Gaia ; les produits d'une même « couche » (cellule, détecteur) partagent la grille et s'empilent directement. |
| DrizzlePac, « Multi-visit Mosaic Processing » et « Multi-visit Mosaic Products », https://drizzlepac.readthedocs.io/en/latest/mast_data_products/mvm_processing.html | Nom `hst_skycell-pPPPPxXXyYY_<inst>_<det>_<filtre>_all_drc` ; l'emprise d'une cellule est le plus petit rectangle qui contient **toutes les poses de la cellule** (tous filtres confondus) : un filtre peut n'en occuper qu'un coin (cas réel de M 16). Limites : décalage de quelques pixels possible entre visites, objets mobiles dédoublés. |
| HST Data Handbook (ACS), « Types of ACS files » | `drz` : poses combinées et corrigées de la distorsion ; `drc` : idem à partir de poses corrigées de la CTE (ACS/WFC, WFC3/UVIS). |
| En-têtes réels (lecture des 600 premiers ko par requête partielle) | `drz` du pipeline et `drc` SVM d'une même visite : mêmes 4 poses (`NCOMBINE = 4`, `NDRIZIM = 8` = 4 poses × 2 détecteurs), 2 600 s ; MVM : 8 poses (`NUMEXP = 8`), 5 200 s. |
| MAST TAP `dbo.obspointing` | `provenance_name` (CALWF3, CALACS, HAP-SVM, HAP-MVM), `t_exptime` (temps total), `target_classification`, `mtflag` (cible mobile), `intenttype`. |
| HUDF : MAST (programmes 9978, 10086, 11563, 12498), readme HUDF12, https://archive.stsci.edu/prepds/xdf/ | Temps de pose par filtre (somme des produits du pipeline par programme), XDF ≈ 1,8 million de secondes, 30 et 60 mas ; fichiers de 110 Mo (60 mas) et 441 Mo (30 mas). |
| Documentations des instruments (WFC3, ACS, JDox, ESO, IRSA, SDSS, PDS) | Topo des instruments et des filtres (`coupole/modules/archives/instruments.py`, sources dans l'en-tête du fichier). |

Ce que Coupole en fait :

1. **Recadrage sur la zone utile** : plus petit rectangle des pixels valides (finis et non nuls), lu par blocs de
   lignes ; `CRPIX1/CRPIX2` décalés (WCS exacte, SIP comprise) ; `CROPX0`, `CROPY0`, `ORIGNAX1`, `ORIGNAX2`.
   Cellule de M 16 : 19 806 × 15 741 → 762 × 5 217 px.
2. **Pas de masque par défaut** (le masque pleine taille non compressé de la 0.2.1 pesait 312 Mo) ; sur option,
   entiers 8 bits compressés après recadrage.  Sans masque, l'alignement tient les 0 exacts pour « sans donnée »
   (`NANCOUNT` > 0 et `NANFILL` = 0).  Original non gardé par défaut.
3. **Un produit logique par filtre** : MVM si elle existe (toutes les poses, CTE corrigée, grille commune), sinon par
   visite la SVM, sinon le pipeline standard ; JWST : mosaïque `c…` sinon l'observation au plus long temps de
   pose.  Les autres deviennent des variantes (cachées), les images de détection sont écartées.  Arp 273 : 17
   produits → 3.
4. **Noms lisibles et rangement par champ**, réorganisation des téléchargements existants (déplacements, jamais
   d'écrasement, journal).
5. **Recherche tolérante** : la 0.2.1 résolvait « jupiter » par SIMBAD dès qu'une archive céleste était cochée
   (`LookupError`, recherche abandonnée) ; un corps du Système solaire est désormais cherché par nom de cible
   (MAST `target_name LIKE 'JUPITER%' AND mtflag = 1`, OPUS, PDS).  Second défaut trouvé : OPUS rend Voyager puis
   Cassini, et la limite de lignes coupait la fin de la liste (aucune image de Cassini pour « saturne ») : limite
   désormais répartie entre missions.
6. **Catalogue sans critère** (`GROUP BY target_name`) : HST limité aux MVM (la table entière dépasse 60 s : 504),
   JWST `i2d` (34 s), ESO (1,7 s), OPUS `meta/mults`, facettes Solr du PDS ; cache de 30 jours.
7. **Aperçus** : `jpegurl` de MAST est un JPEG pleine résolution (jusqu'à 19 806 × 15 741 px, 3,7 à 4,2 Mo) ; la 0.2.1
   le tronquait à 3 Mo.  Lu en entier, décodé réduit (`QImageReader.setScaledSize`), recadré sur la zone qui diffère
   du fond (blanc chez MAST), PNG de 400 px ; ESO : `previews/v1/files/<id>/thumbnail` (le lien « preview » de
   DataLink est un PDF) ; sinon vignette générée après téléchargement, sinon la raison.

## English summary

The **Archives** module follows the practices published by amateurs who reprocess Hubble and JWST public data
(Galactic Hunter, Astronomy, Sky at Night Magazine, a JWST tutorial; the founding Cloudy Nights thread could not be
read: the forum refuses automated reads and no web-archive copy exists) and the documentation of the archives,
Siril and reproject: download final products only (`i2d`, `drc`/`drz`, ESO Phase 3, SEIP, Atlas), public data only,
estimate the volume first and confirm beyond a threshold, be polite to servers, extract the SCI extension with its
WCS, units and photometric keywords, handle NaN with a mask, align by astrometry (reprojection onto a common grid)
rather than by stars, correct per-pixel units for the pixel-area ratio, colour the filters in chromatic order, and
always credit the archive.  Since 0.2.2 (section 5): prepared images are cropped to their useful area (a Hubble
multi-visit "sky cell" can be 19,806 × 15,741 px for a corner of data), no mask by default, one logical product per
filter (MVM, else SVM, else standard pipeline; variants hidden, detection images left out, choice from the MAST and
DrizzlePac documentation), readable names filed by field, Solar System bodies searched by target name, a
criteria-free target catalogue, reduced official previews and a filter guide with amateur equivalents.  Gemini (account required) and SMOKA (web form only) are reported, not downloaded.
