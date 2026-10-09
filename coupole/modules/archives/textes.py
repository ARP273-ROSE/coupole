"""Textes du module « Archives des observatoires » (FR/EN)."""

_NOMS = {'mast': 'MAST (Hubble, JWST, GALEX)', 'eso': 'ESO', 'irsa': 'IRSA (Spitzer, WISE, 2MASS)',
         'noirlab': 'NOIRLab', 'koa': 'Keck (KOA)', 'sdss': 'SDSS', 'goa': 'Gemini', 'smoka': 'SMOKA (Subaru)',
         'opus': 'Voyager, Cassini (OPUS)', 'pds': 'Juno (PDS)'}

TEXTES = {
    **{'arc_nom_' + k: {'fr': v, 'en': v} for k, v in _NOMS.items()},
    'arc_info_mast': {'fr': "MAST (STScI) : produits finaux de Hubble (images « drizzlées » _drz, _drc), de JWST "
                            "(_i2d) et de GALEX.  Service TAP officiel de MAST.",
                      'en': 'MAST (STScI): final products of Hubble (drizzled _drz, _drc images), JWST (_i2d) and GALEX. '
                            'Official MAST TAP service.'},
    'arc_info_eso': {'fr': "Archive scientifique de l'ESO : produits réduits « Phase 3 » (VISTA, VST, HAWK-I, FORS, "
                           "MUSE…), service TAP ObsCore.",
                     'en': 'ESO Science Archive: reduced « Phase 3 » products (VISTA, VST, HAWK-I, FORS, MUSE…), '
                           'TAP ObsCore service.'},
    'arc_info_irsa': {'fr': 'IRSA (NASA/IPAC) : mosaïques Spitzer (SEIP), images Atlas de WISE (AllWISE) et de 2MASS, '
                            'service SIA 2.',
                      'en': 'IRSA (NASA/IPAC): Spitzer mosaics (SEIP), WISE (AllWISE) and 2MASS Atlas images, SIA 2 '
                            'service.'},
    'arc_info_noirlab': {'fr': 'NOIRLab Astro Data Archive (Kitt Peak, Cerro Tololo : DECam, Mosaic…) : piles et '
                               'images rééchantillonnées du pipeline.  Étape 2.',
                         'en': 'NOIRLab Astro Data Archive (Kitt Peak, Cerro Tololo: DECam, Mosaic…): pipeline stacks '
                               'and resampled images.  Stage 2.'},
    'arc_info_koa': {'fr': "Keck Observatory Archive : poses brutes de NIRC2, OSIRIS, MOSFIRE (aucun produit final "
                           "d'imagerie : décocher « Produits finaux seulement »).  Étape 2.",
                     'en': 'Keck Observatory Archive: raw NIRC2, OSIRIS, MOSFIRE frames (no final imaging product: '
                           'untick « Final products only »).  Stage 2.'},
    'arc_info_sdss': {'fr': 'SDSS : images calibrées u, g, r, i, z (champs de 13,5′ × 9,8′).  Étape 2.',
                      'en': 'SDSS: calibrated u, g, r, i, z images (13.5′ × 9.8′ fields).  Stage 2.'},
    'arc_info_goa': {'fr': "Gemini Observatory Archive : un compte gratuit (ORCID) est exigé, même pour les données "
                           "publiques ; l'accès anonyme est refusé.  Étape 2.",
                     'en': 'Gemini Observatory Archive: a free account (ORCID) is required, even for public data; '
                           'anonymous access is refused.  Stage 2.'},
    'arc_info_smoka': {'fr': "SMOKA (Subaru, Kiso, Okayama) : formulaire web seulement, aucune interface de "
                             "programmation publique ; non pris en charge.  Étape 2.",
                       'en': 'SMOKA (Subaru, Kiso, Okayama): web form only, no public programming interface; not '
                             'supported.  Stage 2.'},
    'arc_info_opus': {'fr': "OPUS (PDS, nœud Anneaux et Lunes) : images calibrées de Voyager (corrigées de la "
                            "distorsion) et de Cassini.  Recherche par corps (Jupiter, Saturne, Io…).  Étape 3.",
                      'en': 'OPUS (PDS Ring-Moon Systems Node): calibrated Voyager (distortion-corrected) and Cassini '
                            'images.  Search by body (Jupiter, Saturn, Io…).  Stage 3.'},
    'arc_info_pds': {'fr': "Atlas du PDS Imaging Node : images JunoCam (bandes de framelets, sans reconstruction).  "
                           "Recherche par corps.  Étape 3.",
                     'en': 'PDS Imaging Node Atlas: JunoCam images (framelet strips, not reconstructed).  Search by '
                           'body.  Stage 3.'},
    # ---------------------------------------------------------------- conditions d'usage et crédits
    'arc_cond_mast': {'fr': "Données publiques de MAST : libres de réutilisation.  Mentionner l'origine (« NASA/ESA, "
                            "STScI » pour Hubble, « NASA/ESA/CSA, STScI » pour JWST) et citer le programme.",
                      'en': 'Public MAST data: free to reuse.  Acknowledge the origin (« NASA/ESA, STScI » for Hubble, '
                            '« NASA/ESA/CSA, STScI » for JWST) and cite the programme.'},
    'arc_cond_eso': {'fr': "Données de l'ESO publiques après la période réservée.  Mention demandée : données obtenues "
                           "auprès de l'archive scientifique de l'ESO, avec l'identifiant du programme ; crédit « ESO ».",
                     'en': 'ESO data are public once the proprietary period is over.  Required acknowledgement: data '
                           'obtained through the ESO Science Archive Facility, with the programme ID; credit « ESO ».'},
    'arc_cond_irsa': {'fr': "Données d'IRSA publiques.  Mentionner IRSA (NASA/IPAC) et la mission : NASA/JPL-Caltech "
                            "(Spitzer), NASA/JPL-Caltech/UCLA (WISE), 2MASS/UMass/IPAC-Caltech/NASA/NSF.",
                      'en': 'IRSA data are public.  Acknowledge IRSA (NASA/IPAC) and the mission: NASA/JPL-Caltech '
                            '(Spitzer), NASA/JPL-Caltech/UCLA (WISE), 2MASS/UMass/IPAC-Caltech/NASA/NSF.'},
    'arc_cond_noirlab': {'fr': "Données publiques après la période réservée.  Mentionner l'Astro Data Archive de "
                               "NOIRLab (NSF NOIRLab/AURA) et le programme.",
                         'en': 'Public once the proprietary period is over.  Acknowledge the NOIRLab Astro Data Archive '
                               '(NSF NOIRLab/AURA) and the programme.'},
    'arc_cond_koa': {'fr': "Données publiques après la période réservée.  Mentionner le Keck Observatory Archive "
                           "(KOA), géré par NExScI pour la NASA, et le programme.",
                     'en': 'Public once the proprietary period is over.  Acknowledge the Keck Observatory Archive (KOA), '
                           'operated by NExScI for NASA, and the programme.'},
    'arc_cond_sdss': {'fr': 'Données publiques.  Mentionner le Sloan Digital Sky Survey (SDSS) et la version (DR17).',
                      'en': 'Public data.  Acknowledge the Sloan Digital Sky Survey (SDSS) and the release (DR17).'},
    'arc_cond_goa': {'fr': "Compte gratuit exigé.  Mentionner l'International Gemini Observatory (NOIRLab/NSF/AURA) "
                           "et le programme.",
                     'en': 'Free account required.  Acknowledge the International Gemini Observatory (NOIRLab/NSF/AURA) '
                           'and the programme.'},
    'arc_cond_smoka': {'fr': 'Non pris en charge par Coupole.', 'en': 'Not supported by Coupole.'},
    'arc_cond_pds': {'fr': "Données publiques du Planetary Data System (NASA).  Crédit : NASA/JPL-Caltech ; Cassini : "
                           "NASA/JPL-Caltech/Space Science Institute ; Juno : NASA/JPL-Caltech/SwRI/MSSS.",
                     'en': 'Public Planetary Data System (NASA) data.  Credit: NASA/JPL-Caltech; Cassini: '
                           'NASA/JPL-Caltech/Space Science Institute; Juno: NASA/JPL-Caltech/SwRI/MSSS.'},
    # ---------------------------------------------------------------- interface : recherche
    'arc_onglet_recherche_aide': {'fr': 'Chercher dans les archives, voir la fiche, estimer, télécharger et préparer.',
                                  'en': 'Search the archives, see the record, estimate, download and prepare.'},
    'arc_onglet_alignement_aide': {'fr': 'Aligner les images préparées sur une grille commune et proposer les couleurs.',
                                   'en': 'Align the prepared images onto a common grid and suggest the colours.'},
    'arc_onglet_recherche': {'fr': 'Recherche', 'en': 'Search'},
    'arc_onglet_alignement': {'fr': 'Alignement et couleur', 'en': 'Alignment and colour'},
    'arc_pret': {'fr': "Donnez un objet (M 42, NGC 3324…), des coordonnées (83.82 -5.39) ou, pour les sondes, un "
                       "corps (Jupiter, Saturne).",
                 'en': 'Give an object (M 42, NGC 3324…), coordinates (83.82 -5.39) or, for space probes, a body '
                       '(Jupiter, Saturn).'},
    'arc_nom': {'fr': 'Objet', 'en': 'Object'},
    'arc_nom_aide': {'fr': "Nom (résolu par SIMBAD, puis Sesame), coordonnées en degrés (83.82 -5.39) ou "
                           "sexagésimales (05:35:17 -05:23:28) ; pour Voyager, Cassini, Juno : le corps visé.",
                     'en': 'Name (resolved by SIMBAD, then Sesame), coordinates in degrees (83.82 -5.39) or '
                           'sexagesimal (05:35:17 -05:23:28); for Voyager, Cassini, Juno: the target body.'},
    'arc_nom_indice': {'fr': 'M 42, NGC 3324, 83.82 -5.39, Jupiter…', 'en': 'M 42, NGC 3324, 83.82 -5.39, Jupiter…'},
    'arc_rayon': {'fr': 'Rayon', 'en': 'Radius'},
    'arc_rayon_aide': {'fr': "Rayon de recherche autour de la position.  Une image est gardée si son centre est dans "
                             "ce cercle ou si son empreinte contient la position.",
                       'en': 'Search radius around the position.  An image is kept if its centre lies in this circle '
                             'or if its footprint contains the position.'},
    'arc_arcmin': {'fr': 'arcmin', 'en': 'arcmin'},
    'arc_chercher': {'fr': 'Chercher', 'en': 'Search'},
    'arc_chercher_aide': {'fr': 'Interroge les archives cochées (en parallèle, une requête par archive).',
                          'en': 'Query the ticked archives (in parallel, one request per archive).'},
    'arc_arreter_recherche': {'fr': 'Arrêter', 'en': 'Stop'},
    'arc_arreter_recherche_aide': {'fr': "N'attend plus les archives qui n'ont pas encore répondu.",
                                   'en': 'Stop waiting for archives that have not answered yet.'},
    'arc_case_archive': {'fr': 'Archive', 'en': 'Archive'},
    'arc_case_archive_aide': {'fr': 'Archive à interroger.', 'en': 'Archive to query.'},
    'arc_instrument': {'fr': 'Instrument', 'en': 'Instrument'},
    'arc_instrument_aide': {'fr': "Garder seulement ces instruments (morceau du nom, séparés par des virgules) : "
                                  "NIRCAM, ACS, WFC3, MIRI, HAWKI…",
                            'en': 'Keep only these instruments (part of the name, comma-separated): NIRCAM, ACS, WFC3, '
                                  'MIRI, HAWKI…'},
    'arc_instrument_indice': {'fr': 'NIRCAM, ACS…', 'en': 'NIRCAM, ACS…'},
    'arc_filtre': {'fr': 'Filtre', 'en': 'Filter'},
    'arc_filtre_aide': {'fr': 'Garder seulement ces filtres (nom exact, séparés par des virgules) : F444W, F656N, H, W1…',
                        'en': 'Keep only these filters (exact name, comma-separated): F444W, F656N, H, W1…'},
    'arc_filtre_indice': {'fr': 'F444W, F656N…', 'en': 'F444W, F656N…'},
    'arc_debut': {'fr': 'Du', 'en': 'From'},
    'arc_debut_aide': {'fr': "Observations commencées à partir de cette date (AAAA-MM-JJ, UTC).",
                       'en': 'Observations started on or after this date (YYYY-MM-DD, UTC).'},
    'arc_fin': {'fr': 'au', 'en': 'to'},
    'arc_fin_aide': {'fr': "Observations commencées jusqu'à cette date incluse (AAAA-MM-JJ, UTC).",
                     'en': 'Observations started up to this date included (YYYY-MM-DD, UTC).'},
    'arc_date_indice': {'fr': 'AAAA-MM-JJ', 'en': 'YYYY-MM-DD'},
    'arc_finaux': {'fr': 'Produits finaux seulement', 'en': 'Final products only'},
    'arc_finaux_aide': {'fr': "Seulement les images finales des pipelines (niveau 3) : JWST _i2d, Hubble _drz/_drc, "
                              "produits réduits de l'ESO, mosaïques Spitzer, Atlas WISE et 2MASS.  Décoché : aussi "
                              "les poses calibrées une à une, voire brutes.",
                        'en': 'Only the final images of the pipelines (level 3): JWST _i2d, Hubble _drz/_drc, ESO '
                              'reduced products, Spitzer mosaics, WISE and 2MASS Atlas.  Unticked: also the calibrated '
                              'single frames, or even raw ones.'},
    'arc_publics': {'fr': 'Données publiques seulement', 'en': 'Public data only'},
    'arc_publics_aide': {'fr': "Seulement les données dont la période réservée à l'équipe est terminée (date de mise "
                               "à disposition passée).  Les autres ne sont de toute façon pas téléchargeables.",
                         'en': 'Only data whose proprietary period is over (release date in the past).  The others '
                               'cannot be downloaded anyway.'},
    'arc_table_aide': {'fr': "Observations trouvées.  Pastille : verte = déjà téléchargée et préparée, orange = "
                             "échec, flèche = à télécharger.  Grisé : pas encore publique.  Double-clic : ouvrir "
                             "l'image préparée ; clic droit : ouvrir avec, page de l'archive.",
                       'en': 'Observations found.  Badge: green = already downloaded and prepared, orange = failure, '
                             'arrow = to download.  Greyed: not yet public.  Double-click: open the prepared image; '
                             'right-click: open with, archive page.'},
    'arc_table_vide': {'fr': 'Aucune observation : lancez une recherche.', 'en': 'No observation: run a search.'},
    'arc_col_etat': {'fr': 'état', 'en': 'status'},
    'arc_col_mission': {'fr': 'mission', 'en': 'mission'},
    'arc_col_instrument': {'fr': 'instrument', 'en': 'instrument'},
    'arc_col_filtre': {'fr': 'filtre', 'en': 'filter'},
    'arc_col_lambda': {'fr': 'λ (nm)', 'en': 'λ (nm)'},
    'arc_col_date': {'fr': 'date', 'en': 'date'},
    'arc_col_cible': {'fr': 'cible', 'en': 'target'},
    'arc_col_distance': {'fr': "distance (′)", 'en': "distance (′)"},
    'arc_col_taille': {'fr': 'taille', 'en': 'size'},
    'arc_col_archive': {'fr': 'archive', 'en': 'archive'},
    'arc_statut_ok': {'fr': 'possédée', 'en': 'owned'},
    'arc_statut_echec': {'fr': 'échec', 'en': 'failed'},
    'arc_statut_absente': {'fr': 'à télécharger', 'en': 'to download'},
    'arc_bulle': {'fr': '{id}\nCrédit : {credit}', 'en': '{id}\nCredit: {credit}'},
    'arc_vignette_aide': {'fr': "Vignette fournie par l'archive (quand elle existe), gardée en cache.",
                          'en': 'Thumbnail provided by the archive (when there is one), cached.'},
    'arc_pas_de_vignette': {'fr': "Pas de vignette pour cette observation.", 'en': 'No thumbnail for this observation.'},
    'arc_fiche_aide': {'fr': "Fiche de l'observation : programme, investigateur, dates, filtre, crédit et conditions "
                             "d'usage, lien vers la page de l'archive.",
                       'en': 'Observation record: programme, investigator, dates, filter, credit and usage terms, link '
                             'to the archive page.'},
    'arc_f_archive': {'fr': 'Archive', 'en': 'Archive'},
    'arc_f_mission': {'fr': 'Mission', 'en': 'Mission'},
    'arc_f_instrument': {'fr': 'Instrument', 'en': 'Instrument'},
    'arc_f_filtre': {'fr': 'Filtre', 'en': 'Filter'},
    'arc_f_lambda': {'fr': "Longueur d'onde", 'en': 'Wavelength'},
    'arc_f_debut': {'fr': 'Début (UTC)', 'en': 'Start (UTC)'},
    'arc_f_publique': {'fr': 'Publique depuis', 'en': 'Public since'},
    'arc_f_cible': {'fr': 'Cible', 'en': 'Target'},
    'arc_f_coord': {'fr': 'Centre', 'en': 'Centre'},
    'arc_f_programme': {'fr': 'Programme', 'en': 'Programme'},
    'arc_f_pi': {'fr': 'Investigateur principal', 'en': 'Principal investigator'},
    'arc_f_titre': {'fr': 'Titre', 'en': 'Title'},
    'arc_f_calib': {'fr': 'Niveau de calibration', 'en': 'Calibration level'},
    'arc_f_fichier': {'fr': 'Fichier', 'en': 'File'},
    'arc_f_taille': {'fr': 'Taille', 'en': 'Size'},
    'arc_f_credit': {'fr': 'Crédit :', 'en': 'Credit:'},
    'arc_f_page': {'fr': "Page de l'archive", 'en': 'Archive page'},
    'arc_f_reservee': {'fr': "Pas encore publique (période réservée à l'équipe).", 'en': 'Not yet public (proprietary period).'},
    'arc_f_possede': {'fr': 'Déjà téléchargée et préparée : {chemin}', 'en': 'Already downloaded and prepared: {chemin}'},
    'arc_selection': {'fr': '{n} observations choisies, {taille} annoncés.', 'en': '{n} observations selected, {taille} announced.'},
    # ---------------------------------------------------------------- interface : téléchargement
    'arc_dossier': {'fr': 'Dossier', 'en': 'Folder'},
    'arc_dossier_aide': {'fr': "Dossier de sortie ; les fichiers vont dans <dossier>/Archives/<mission>/<cible>/"
                               "<instrument>/<filtre>/ et l'état dans Archives/_etat (partage réseau accepté).",
                         'en': 'Output folder; files go to <folder>/Archives/<mission>/<target>/<instrument>/<filter>/ '
                               'and the state to Archives/_etat (network share accepted).'},
    'arc_choisir_dossier': {'fr': 'Choisir…', 'en': 'Choose…'},
    'arc_choisir_dossier_aide': {'fr': 'Choisit le dossier de sortie des archives.', 'en': 'Choose the output folder of the archives.'},
    'arc_format_aide': {'fr': "Format de l'image préparée : XISF Float32 (PixInsight, Siril ≥ 1.4) ou FITS Float32 "
                              "(tous les logiciels).",
                        'en': 'Format of the prepared image: XISF Float32 (PixInsight, Siril ≥ 1.4) or FITS Float32 '
                              '(every software).'},
    'arc_format_xisf': {'fr': 'XISF (Float32)', 'en': 'XISF (Float32)'},
    'arc_format_fits': {'fr': 'FITS (Float32)', 'en': 'FITS (Float32)'},
    'arc_garder': {'fr': "Garder le fichier d'origine", 'en': 'Keep the original file'},
    'arc_garder_aide': {'fr': "Décoché : le fichier téléchargé (toutes ses extensions) est effacé une fois l'image "
                              "scientifique préparée — place gagnée, mais il faudra le retélécharger pour ses "
                              "autres extensions (poids, erreurs).",
                        'en': 'Unticked: the downloaded file (all its extensions) is deleted once the science image is '
                              'prepared — space saved, but it must be downloaded again for its other extensions '
                              '(weights, errors).'},
    'arc_estimer': {'fr': 'Estimer le volume', 'en': 'Estimate the volume'},
    'arc_estimer_aide': {'fr': "Additionne les tailles annoncées par les archives et mesure les autres (une requête "
                               "d'un octet par fichier, un échantillon au-delà de 60 fichiers).  Rien n'est téléchargé.",
                         'en': 'Add up the sizes announced by the archives and measure the others (a one-byte request '
                               'per file, a sample beyond 60 files).  Nothing is downloaded.'},
    'arc_telecharger': {'fr': 'Télécharger la sélection', 'en': 'Download the selection'},
    'arc_telecharger_aide': {'fr': "Estime le volume, demande confirmation au-delà du seuil (2 Go par défaut), puis "
                                   "télécharge (débit plafonné, reprise), extrait l'image scientifique et la range.",
                             'en': 'Estimate the volume, ask for confirmation beyond the threshold (2 GB by default), then '
                                   'download (capped rate, resume), extract the science image and file it.'},
    'arc_pause': {'fr': 'Pause', 'en': 'Pause'},
    'arc_pause_aide': {'fr': 'Suspend les téléchargements (ceux en cours finissent leur fichier).',
                       'en': 'Suspend the downloads (the current ones finish their file).'},
    'arc_reprendre': {'fr': 'Reprendre', 'en': 'Resume'},
    'arc_annuler': {'fr': 'Annuler', 'en': 'Cancel'},
    'arc_annuler_aide': {'fr': "Arrête tout ; un fichier interrompu reprendra là où il s'était arrêté la prochaine fois.",
                         'en': 'Stop everything; an interrupted file will resume where it stopped next time.'},
    'arc_ouvrir_dossier': {'fr': 'Ouvrir le dossier', 'en': 'Open the folder'},
    'arc_ouvrir_dossier_aide': {'fr': 'Ouvre le dossier Archives dans le gestionnaire de fichiers.',
                                'en': 'Open the Archives folder in the file manager.'},
    'arc_barre_aide': {'fr': 'Fichiers traités sur fichiers demandés.', 'en': 'Files processed out of files requested.'},
    # ---------------------------------------------------------------- messages
    'arc_nom_requis': {'fr': 'Donnez un objet, des coordonnées ou un corps.', 'en': 'Give an object, coordinates or a body.'},
    'arc_aucune_archive': {'fr': 'Cochez au moins une archive.', 'en': 'Tick at least one archive.'},
    'arc_recherche_en_cours': {'fr': 'Recherche en cours…', 'en': 'Searching…'},
    'arc_interroge': {'fr': 'Interrogation de {archive}…', 'en': 'Querying {archive}…'},
    'arc_position': {'fr': 'Position : {ra}° {dec}°, rayon {r}′', 'en': 'Position: {ra}° {dec}°, radius {r}′'},
    'arc_introuvable': {'fr': 'Objet introuvable : {nom}', 'en': 'Object not found: {nom}'},
    'arc_resolution_impossible': {'fr': 'Résolution du nom impossible ({erreur}).', 'en': 'Name resolution failed ({erreur}).'},
    'arc_resultat_archive': {'fr': '{archive} : {n} en {s} s', 'en': '{archive}: {n} in {s} s'},
    'arc_tronque': {'fr': '(tronqué : affinez la recherche)', 'en': '(truncated: refine the search)'},
    'arc_compte_requis': {'fr': '{archive} : un compte est exigé (même pour les données publiques)',
                          'en': '{archive}: an account is required (even for public data)'},
    'arc_non_pris': {'fr': '{archive} : non pris en charge (formulaire web : {lien})',
                     'en': '{archive}: not supported (web form: {lien})'},
    'arc_erreur_archive': {'fr': '{archive} : erreur ({erreur})', 'en': '{archive}: error ({erreur})'},
    'arc_total': {'fr': '{n} observations', 'en': '{n} observations'},
    'arc_rien_selectionne': {'fr': "Choisissez des lignes dans le tableau.", 'en': 'Select rows in the table.'},
    'arc_rien_a_telecharger': {'fr': 'Rien à télécharger : tout est déjà là, ou rien de choisi.',
                               'en': 'Nothing to download: everything is already here, or nothing is selected.'},
    'arc_rien': {'fr': 'Rien à télécharger.', 'en': 'Nothing to download.'},
    'arc_estimation_en_cours': {'fr': 'Estimation du volume de {n} fichiers…', 'en': 'Estimating the volume of {n} files…'},
    'arc_estimation': {'fr': '{n} fichiers, {taille} ({connus} tailles annoncées, {mesures} mesurées, {estimes} '
                             'estimées, {inconnus} inconnues)',
                       'en': '{n} files, {taille} ({connus} sizes announced, {mesures} measured, {estimes} estimated, '
                             '{inconnus} unknown)'},
    'arc_au_dela_seuil': {'fr': 'Au-delà du seuil de confirmation ({seuil}).', 'en': 'Beyond the confirmation threshold ({seuil}).'},
    'arc_confirmer_titre': {'fr': 'Téléchargement volumineux', 'en': 'Large download'},
    'arc_confirmer': {'fr': '{n} fichiers, {taille} environ (seuil : {seuil}).  Télécharger ?',
                      'en': '{n} files, about {taille} (threshold: {seuil}).  Download?'},
    'arc_confirmer_cli': {'fr': 'Au-delà de {seuil} : relancez avec --oui pour confirmer.',
                          'en': 'Beyond {seuil}: run again with --yes to confirm.'},
    'arc_telechargement_en_cours': {'fr': 'Téléchargement de {n} fichiers…', 'en': 'Downloading {n} files…'},
    'arc_progression': {'fr': '{fait} / {n} fichiers, {taille} reçus', 'en': '{fait} / {n} files, {taille} received'},
    'arc_fini': {'fr': 'préparé : {chemin}', 'en': 'prepared: {chemin}'},
    'arc_deja': {'fr': 'déjà là : {id}', 'en': 'already here: {id}'},
    'arc_echec': {'fr': 'échec ({id}) : {erreur}', 'en': 'failure ({id}): {erreur}'},
    'arc_bilan_session': {'fr': '{ok} préparées, {deja} déjà là, {echec} échecs ; {taille} reçus en {s} s',
                          'en': '{ok} prepared, {deja} already here, {echec} failures; {taille} received in {s} s'},
    'arc_bilan': {'fr': '{ok} images préparées, {echec} échecs, {absente} déplacées ou effacées',
                  'en': '{ok} prepared images, {echec} failures, {absente} moved or deleted'},
    'arc_prepare': {'fr': '{chemin} : {forme} px, {nan} pixels sans donnée, unité {bunit}, WCS {wcs}',
                    'en': '{chemin}: {forme} px, {nan} pixels without data, unit {bunit}, WCS {wcs}'},
    'arc_archive_inconnue': {'fr': 'Archive inconnue : {a} (connues : {connues})', 'en': 'Unknown archive: {a} (known: {connues})'},
    'arc_etape_n': {'fr': 'étape {n}', 'en': 'stage {n}'},
    'arc_etat_ok': {'fr': 'utilisable', 'en': 'usable'},
    'arc_etat_compte': {'fr': 'compte exigé', 'en': 'account required'},
    'arc_etat_non_pris': {'fr': 'non pris en charge', 'en': 'not supported'},
    'arc_liste_defaut': {'fr': '* interrogée par défaut', 'en': '* queried by default'},
    # ---------------------------------------------------------------- journal (bilingue sur une ligne)
    'arc_j_session': {'fr': 'session : {n} fichiers vers {dest}', 'en': 'session: {n} files to {dest}'},
    'arc_j_ok': {'fr': '{id} préparé : {chemin}', 'en': '{id} prepared: {chemin}'},
    'arc_j_echec': {'fr': '{id} échec : {raison}', 'en': '{id} failure: {raison}'},
    'arc_j_inexploitable': {'fr': '{id} sans image exploitable : {raison}', 'en': '{id} has no usable image: {raison}'},
    'arc_j_fin': {'fr': 'fin : {ok} préparés, {deja} déjà là, {echec} échecs, {annule} annulés ({s} s)',
                  'en': 'end: {ok} prepared, {deja} already here, {echec} failures, {annule} cancelled ({s} s)'},
    # ---------------------------------------------------------------- alignement
    'arc_al_intro': {'fr': "Cochez les images préparées à aligner (même champ, filtres différents).  Elles sont "
                           "rééchantillonnées d'après leur astrométrie (WCS) sur une grille commune ; le résultat "
                           "(un fichier par filtre, masque commun, aperçu couleur, expression PixelMath) va dans "
                           "Archives/_alignes.",
                     'en': 'Tick the prepared images to align (same field, different filters).  They are resampled '
                           'by their astrometry (WCS) onto a common grid; the result (one file per filter, common mask, '
                           'colour preview, PixelMath expression) goes to Archives/_alignes.'},
    'arc_al_rafraichir': {'fr': 'Actualiser', 'en': 'Refresh'},
    'arc_al_rafraichir_aide': {'fr': 'Relit la liste des images préparées.', 'en': 'Reload the list of prepared images.'},
    'arc_al_ajouter': {'fr': 'Ajouter un fichier…', 'en': 'Add a file…'},
    'arc_al_ajouter_aide': {'fr': 'Ajoute une image FITS ou XISF qui a une astrométrie (WCS céleste).',
                            'en': 'Add a FITS or XISF image that has an astrometric solution (celestial WCS).'},
    'arc_al_filtre_fichiers': {'fr': 'Images (*.fits *.fit *.fts *.xisf)', 'en': 'Images (*.fits *.fit *.fts *.xisf)'},
    'arc_al_retirer': {'fr': 'Retirer', 'en': 'Remove'},
    'arc_al_retirer_aide': {'fr': 'Retire de la liste les lignes choisies (rien n\'est effacé).',
                            'en': 'Remove the selected lines from the list (nothing is deleted).'},
    'arc_al_liste_aide': {'fr': 'Images préparées qui ont une WCS céleste ; cochez celles à aligner.',
                          'en': 'Prepared images that have a celestial WCS; tick the ones to align.'},
    'arc_al_apercu_aide': {'fr': 'Aperçu couleur (étirement asinh, ordre chromatique des filtres).',
                           'en': 'Colour preview (asinh stretch, chromatic ordering of the filters).'},
    'arc_al_pas_apercu': {'fr': "L'aperçu couleur apparaîtra ici.", 'en': 'The colour preview will appear here.'},
    'arc_al_reference': {'fr': 'Grille', 'en': 'Grid'},
    'arc_al_reference_aide': {'fr': "Grille de sortie : celle d'une des images (souvent le filtre le plus fin), ou une "
                                    "grille optimale qui les couvre toutes.",
                              'en': 'Output grid: the one of an image (often the sharpest filter), or an optimal grid '
                                    'covering them all.'},
    'arc_al_optimale': {'fr': 'Grille optimale', 'en': 'Optimal grid'},
    'arc_al_methode': {'fr': 'Méthode', 'en': 'Method'},
    'arc_al_methode_aide': {'fr': "Bilinéaire : rapide, bon compromis ; adaptative : anti-crénelage, meilleure quand "
                                  "les pas de pixel diffèrent beaucoup ; exacte : recouvrement exact des pixels, lente "
                                  "(sous 0,05″ par pixel, l'adaptative la remplace) ; plus proche voisin : pixels copiés "
                                  "tels quels.  Adaptative et exacte demandent la bibliothèque reproject.",
                            'en': 'Bilinear: fast, good compromise; adaptive: anti-aliased, better when the pixel scales '
                                  'differ a lot; exact: exact pixel overlap, slow (below 0.05″ per pixel, adaptive '
                                  'replaces it); nearest neighbour: pixels copied as they are.  Adaptive and exact need '
                                  'the reproject library.'},
    'arc_al_adaptative': {'fr': 'Adaptative (reproject)', 'en': 'Adaptive (reproject)'},
    'arc_al_bilineaire': {'fr': 'Bilinéaire', 'en': 'Bilinear'},
    'arc_al_exacte': {'fr': 'Exacte (reproject)', 'en': 'Exact (reproject)'},
    'arc_al_proche': {'fr': 'Plus proche voisin', 'en': 'Nearest neighbour'},
    'arc_al_echelle': {'fr': 'Pixels ×', 'en': 'Pixels ×'},
    'arc_al_echelle_aide': {'fr': "Agrandit les pixels de sortie (2 = deux fois moins de pixels par côté) : pour les "
                                  "très grandes mosaïques JWST.",
                            'en': 'Enlarge the output pixels (2 = half as many pixels per side): for very large JWST '
                                  'mosaics.'},
    'arc_al_recadrer': {'fr': 'Recadrer sur la zone commune', 'en': 'Crop to the common area'},
    'arc_al_recadrer_aide': {'fr': 'Garde seulement le rectangle couvert par toutes les images.',
                             'en': 'Keep only the rectangle covered by every image.'},
    'arc_al_aligner': {'fr': 'Aligner', 'en': 'Align'},
    'arc_al_aligner_aide': {'fr': 'Rééchantillonne les images cochées sur la grille choisie et propose les couleurs.',
                            'en': 'Resample the ticked images onto the chosen grid and suggest colours.'},
    'arc_al_compo_aide': {'fr': 'Couleurs proposées : filtres rangés par longueur d\'onde, du bleu au rouge.',
                          'en': 'Suggested colours: filters sorted by wavelength, blue to red.'},
    'arc_al_col_image': {'fr': 'image', 'en': 'image'},
    'arc_al_col_couleur': {'fr': 'couleur', 'en': 'colour'},
    'arc_al_deux': {'fr': 'Cochez au moins deux images.', 'en': 'Tick at least two images.'},
    'arc_al_en_cours': {'fr': 'Alignement de {n} images…', 'en': 'Aligning {n} images…'},
    'arc_al_erreur': {'fr': 'Alignement impossible : {erreur}', 'en': 'Alignment failed: {erreur}'},
    'arc_al_fichiers': {'fr': 'Fichiers alignés, masque commun, composition.txt (PixelMath) : {dest}',
                        'en': 'Aligned files, common mask, composition.txt (PixelMath): {dest}'},
    'arc_aligne': {'fr': '{n} images alignées ({forme} px) : {dest}', 'en': '{n} images aligned ({forme} px): {dest}'},
    'arc_alignement_image': {'fr': 'image {k}/{n} : {nom}', 'en': 'image {k}/{n}: {nom}'},
    'arc_sans_reproject': {'fr': "Bibliothèque « reproject » absente : rééchantillonnage bilinéaire de scipy "
                                 "(pip install reproject pour la méthode exacte).",
                           'en': '« reproject » library missing: bilinear resampling by scipy (pip install reproject '
                                 'for the exact method).'},
    # ---------------------------------------------------------------- ligne de commande
    'arc_meta_nom': {'fr': 'OBJET', 'en': 'OBJECT'},
    'arc_meta_arcmin': {'fr': 'ARCMIN', 'en': 'ARCMIN'},
    'arc_meta_corps': {'fr': 'CORPS', 'en': 'BODY'},
    'arc_meta_date': {'fr': 'AAAA-MM-JJ', 'en': 'YYYY-MM-DD'},
    'arc_meta_mos': {'fr': 'MO/S', 'en': 'MB/S'},
    'arc_cli_liste': {'fr': 'liste les archives connues (étape, missions, état)', 'en': 'list the known archives (stage, missions, status)'},
    'arc_cli_chercher': {'fr': 'cherche des observations autour d\'un objet ou de coordonnées',
                         'en': 'search observations around an object or coordinates'},
    'arc_cli_chercher_desc': {'fr': "Cherche dans MAST, l'ESO et IRSA (par défaut) les produits finaux publics autour "
                                    "d'un objet ; --archive opus ou pds avec --corps pour les sondes planétaires.",
                              'en': 'Search MAST, ESO and IRSA (by default) for public final products around an object; '
                                    '--archive opus or pds with --body for planetary probes.'},
    'arc_cli_estimer': {'fr': 'estime le volume à télécharger', 'en': 'estimate the volume to download'},
    'arc_cli_estimer_desc': {'fr': "Comme « chercher », puis additionne les tailles (annoncées ou mesurées) sans rien "
                                   "télécharger.",
                             'en': 'Like « search », then add up the sizes (announced or measured) without downloading '
                                   'anything.'},
    'arc_cli_telecharger': {'fr': 'télécharge, prépare et range', 'en': 'download, prepare and file'},
    'arc_cli_telecharger_desc': {'fr': "Comme « chercher », puis télécharge (confirmation au-delà du seuil : --oui), "
                                       "extrait l'image scientifique et la range dans <dest>/Archives.",
                                 'en': 'Like « search », then download (confirmation beyond the threshold: --yes), extract '
                                       'the science image and file it in <dest>/Archives.'},
    'arc_cli_preparer': {'fr': 'prépare un fichier déjà téléchargé (FITS, PDS3, VICAR, PDS4)',
                         'en': 'prepare an already downloaded file (FITS, PDS3, VICAR, PDS4)'},
    'arc_cli_preparer_desc': {'fr': "Extrait l'image scientifique d'un FITS à extensions, ou convertit un produit "
                                    "planétaire, en XISF ou FITS Float32 à côté du fichier.",
                              'en': 'Extract the science image of a multi-extension FITS, or convert a planetary product, '
                                    'to XISF or FITS Float32 next to the file.'},
    'arc_cli_aligner': {'fr': 'aligne des images préparées sur une grille commune', 'en': 'align prepared images onto a common grid'},
    'arc_cli_aligner_desc': {'fr': "Rééchantillonne les images (WCS) sur la grille de l'une d'elles ou une grille "
                                   "optimale ; écrit les fichiers alignés, le masque commun, l'aperçu couleur et "
                                   "composition.txt.",
                             'en': 'Resample the images (WCS) onto the grid of one of them or an optimal grid; write the '
                                   'aligned files, the common mask, the colour preview and composition.txt.'},
    'arc_cli_bilan': {'fr': 'ce qui est déjà téléchargé et préparé', 'en': 'what is already downloaded and prepared'},
    'arc_aide_nom': {'fr': 'objet (nom ou coordonnées)', 'en': 'object (name or coordinates)'},
    'arc_aide_rayon': {'fr': 'rayon de recherche en minutes d\'arc (défaut : 3)', 'en': 'search radius in arcminutes (default: 3)'},
    'arc_aide_archive': {'fr': 'archive à interroger (répétable) : mast, eso, irsa, noirlab, koa, sdss, goa, smoka, '
                               'opus, pds',
                         'en': 'archive to query (repeatable): mast, eso, irsa, noirlab, koa, sdss, goa, smoka, opus, pds'},
    'arc_aide_mission': {'fr': 'mission (répétable) : JWST, HST, GALEX, ESO, Spitzer, WISE, 2MASS, NOIRLab, Keck, '
                               'SDSS, Voyager, Cassini, Juno',
                         'en': 'mission (repeatable): JWST, HST, GALEX, ESO, Spitzer, WISE, 2MASS, NOIRLab, Keck, SDSS, '
                               'Voyager, Cassini, Juno'},
    'arc_aide_instrument': {'fr': 'instrument (morceau du nom, répétable)', 'en': 'instrument (part of the name, repeatable)'},
    'arc_aide_filtre': {'fr': 'filtre (nom exact, répétable)', 'en': 'filter (exact name, repeatable)'},
    'arc_aide_debut': {'fr': 'observations à partir de cette date', 'en': 'observations on or after this date'},
    'arc_aide_fin': {'fr': "observations jusqu'à cette date", 'en': 'observations up to this date'},
    'arc_aide_tous_niveaux': {'fr': 'aussi les poses calibrées une à une et les données brutes',
                              'en': 'also the calibrated single frames and the raw data'},
    'arc_aide_non_publiques': {'fr': 'aussi les données encore réservées (pour information : non téléchargeables)',
                               'en': 'also the still proprietary data (for information: not downloadable)'},
    'arc_aide_corps': {'fr': 'corps du Système solaire (Voyager, Cassini, Juno)', 'en': 'Solar System body (Voyager, Cassini, Juno)'},
    'arc_aide_limite': {'fr': 'nombre maximal de lignes par archive (défaut : 2000)', 'en': 'maximum number of rows per archive (default: 2000)'},
    'arc_aide_id': {'fr': 'garder seulement cet identifiant (répétable)', 'en': 'keep only this identifier (repeatable)'},
    'arc_aide_csv': {'fr': 'écrit aussi les résultats dans ce fichier CSV', 'en': 'also write the results to this CSV file'},
    'arc_aide_dest': {'fr': 'dossier de sortie (défaut : celui des Préférences)', 'en': 'output folder (default: the one of the Preferences)'},
    'arc_aide_format': {'fr': 'format des images préparées (défaut : xisf)', 'en': 'format of the prepared images (default: xisf)'},
    'arc_aide_sans_original': {'fr': "efface le fichier d'origine une fois l'image préparée", 'en': 'delete the original file once the image is prepared'},
    'arc_aide_debit': {'fr': 'plafond de débit en Mo/s (défaut : réglage, 8)', 'en': 'rate cap in MB/s (default: setting, 8)'},
    'arc_aide_paralleles': {'fr': 'téléchargements simultanés (défaut : 2, au plus 6)', 'en': 'simultaneous downloads (default: 2, at most 6)'},
    'arc_aide_max': {'fr': 'au plus N fichiers (les plus proches)', 'en': 'at most N files (the closest)'},
    'arc_aide_oui': {'fr': 'confirme un téléchargement au-delà du seuil', 'en': 'confirm a download beyond the threshold'},
    'arc_aide_fichiers': {'fr': 'fichiers à préparer', 'en': 'files to prepare'},
    'arc_aide_etiquette': {'fr': 'label PDS3 détaché (.LBL) ou PDS4 (.xml)', 'en': 'detached PDS3 (.LBL) or PDS4 (.xml) label'},
    'arc_aide_fichiers_aligner': {'fr': 'images préparées (FITS ou XISF avec WCS)', 'en': 'prepared images (FITS or XISF with WCS)'},
    'arc_aide_dest_aligner': {'fr': 'dossier des fichiers alignés', 'en': 'folder of the aligned files'},
    'arc_aide_reference': {'fr': "indice de l'image de référence (défaut : 0, la première)", 'en': 'index of the reference image (default: 0, the first)'},
    'arc_aide_optimale': {'fr': 'grille optimale couvrant toutes les images', 'en': 'optimal grid covering every image'},
    'arc_aide_methode': {'fr': 'rééchantillonnage : bilineaire, adaptative, exacte (reproject), proche',
                         'en': 'resampling: bilineaire (bilinear), adaptative (adaptive), exacte (exact, reproject), '
                               'proche (nearest)'},
    'arc_aide_echelle': {'fr': 'facteur de taille des pixels de sortie (défaut : 1)', 'en': 'output pixel size factor (default: 1)'},
    'arc_aide_sans_recadrage': {'fr': 'ne recadre pas sur la zone commune', 'en': 'do not crop to the common area'},
    # ---------------------------------------------------------------- aide F1
    'arc_aide_html': {
        'fr': "<h3>Archives des observatoires</h3>"
              "<p>Les grands observatoires publient leurs images une fois la période réservée à l'équipe écoulée. "
              "Ce module les cherche, les télécharge poliment, en extrait l'image scientifique et vous aide à les "
              "aligner et à les colorer.</p>"
              "<h4>Chercher</h4><p>Un nom (résolu par SIMBAD puis Sesame) ou des coordonnées, un rayon, les archives à "
              "interroger.  Par défaut : seulement les <b>produits finaux</b> (JWST <code>_i2d</code>, Hubble "
              "<code>_drz</code>/<code>_drc</code>, produits réduits de l'ESO, mosaïques Spitzer, Atlas WISE et 2MASS) "
              "et seulement les <b>données publiques</b>.  Pour Voyager, Cassini et Juno, donnez un corps (Jupiter, "
              "Saturne, Io…) et cochez leurs archives.</p>"
              "<h4>Télécharger</h4><p>Choisissez des lignes, puis « Estimer le volume » : les tailles annoncées sont "
              "additionnées, les autres mesurées (une requête d'un octet).  Au-delà du seuil (2 Go par défaut), "
              "Coupole demande confirmation.  Débit plafonné, deux fichiers à la fois, reprise d'un fichier interrompu. "
              "Rangement : <code>Archives/&lt;mission&gt;/&lt;cible&gt;/&lt;instrument&gt;/&lt;filtre&gt;/</code>.  "
              "L'image préparée (<code>_sci</code>) garde la WCS, l'unité (<code>BUNIT</code>) et les constantes "
              "photométriques ; les pixels sans donnée (NaN) valent 0 et un masque les garde.  Le crédit de l'archive "
              "est écrit dans l'en-tête (<code>CREDIT</code>) : reprenez-le sous toute image publiée.</p>"
              "<h4>Aligner et colorer</h4><p>Cochez les images préparées d'un même champ : elles sont rééchantillonnées "
              "d'après leur WCS (pas de recherche d'étoiles) sur la grille d'une d'elles ou une grille optimale, "
              "recadrées sur la zone commune.  Les filtres sont rangés par longueur d'onde : la plus courte en bleu, "
              "la plus longue en rouge (ordre chromatique des images de Hubble et de JWST).  composition.txt donne "
              "l'expression PixelMath ; les fichiers alignés s'ouvrent dans PixInsight ou Siril, prêts à étirer.</p>"
              "<p>Méthode et sources : docs/archives_methode.md.  Archives sans accès anonyme (Gemini) ou sans "
              "interface (SMOKA) : signalées, non téléchargées.</p>",
        'en': "<h3>Observatory archives</h3>"
              "<p>Major observatories publish their images once the proprietary period is over.  This module searches "
              "them, downloads them politely, extracts the science image and helps you align and colour them.</p>"
              "<h4>Search</h4><p>A name (resolved by SIMBAD then Sesame) or coordinates, a radius, the archives to "
              "query.  By default: <b>final products</b> only (JWST <code>_i2d</code>, Hubble <code>_drz</code>/"
              "<code>_drc</code>, ESO reduced products, Spitzer mosaics, WISE and 2MASS Atlas) and <b>public data</b> "
              "only.  For Voyager, Cassini and Juno, give a body (Jupiter, Saturn, Io…) and tick their archives.</p>"
              "<h4>Download</h4><p>Select rows, then « Estimate the volume »: announced sizes are added up, the others "
              "measured (a one-byte request).  Beyond the threshold (2 GB by default), Coupole asks for confirmation.  "
              "Capped rate, two files at a time, an interrupted file resumes.  Filing: "
              "<code>Archives/&lt;mission&gt;/&lt;target&gt;/&lt;instrument&gt;/&lt;filter&gt;/</code>.  The prepared "
              "image (<code>_sci</code>) keeps the WCS, the unit (<code>BUNIT</code>) and the photometric constants; "
              "pixels without data (NaN) are set to 0 and a mask keeps them.  The archive credit is written in the "
              "header (<code>CREDIT</code>): repeat it under any published image.</p>"
              "<h4>Align and colour</h4><p>Tick the prepared images of one field: they are resampled by their WCS (no "
              "star matching) onto the grid of one of them or an optimal grid, cropped to the common area.  Filters "
              "are sorted by wavelength: the shortest in blue, the longest in red (chromatic ordering of the Hubble "
              "and JWST images).  composition.txt gives the PixelMath expression; the aligned files open in "
              "PixInsight or Siril, ready to stretch.</p>"
              "<p>Method and sources: docs/archives_methode.md.  Archives without anonymous access (Gemini) or without "
              "an interface (SMOKA): reported, not downloaded.</p>"},
}
