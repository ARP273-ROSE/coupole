"""Textes d'interface du module « Banque OHP » (ligne de commande et fenêtre), FR/EN."""

TEXTES = {
    # ------------------------------------------------------------ catégories
    'ohp_cat_ast': {'fr': 'Astéroïdes', 'en': 'Asteroids'},
    'ohp_cat_neocp': {'fr': 'Désignations temporaires (NEOCP)', 'en': 'Temporary designations (NEOCP)'},
    'ohp_cat_com': {'fr': 'Comètes', 'en': 'Comets'},
    'ohp_cat_pla': {'fr': 'Planètes', 'en': 'Planets'},
    'ohp_cat_tno': {'fr': 'Transneptuniens et planètes naines', 'en': 'Trans-Neptunian objects and dwarf planets'},
    'ohp_cat_pn': {'fr': 'Nébuleuses planétaires', 'en': 'Planetary nebulae'},
    'ohp_cat_neb': {'fr': 'Nébuleuses et rémanents', 'en': 'Nebulae and remnants'},
    'ohp_cat_amas': {'fr': "Amas d'étoiles", 'en': 'Star clusters'},
    'ohp_cat_gal': {'fr': 'Galaxies', 'en': 'Galaxies'},
    'ohp_cat_eto': {'fr': 'Étoiles variables', 'en': 'Variable stars'},
    'ohp_cat_autre': {'fr': 'Non classés', 'en': 'Unclassified'},

    # ------------------------------------------------------------ ligne de commande : aides
    'ohp_meta_objet': {'fr': 'OBJET', 'en': 'OBJECT'},
    'ohp_meta_date': {'fr': 'AAAA-MM-JJ', 'en': 'YYYY-MM-DD'},
    'ohp_meta_texte': {'fr': 'TEXTE', 'en': 'TEXT'},
    'ohp_meta_mos': {'fr': 'Mo/s', 'en': 'MB/s'},
    'ohp_aide_objet': {'fr': 'objet(s) : « NGC 6888 », « Pluton », « 1998 AG6 », ou un nom de la base',
                       'en': 'object(s): « NGC 6888 », « Pluto », « 1998 AG6 », or a database name'},
    'ohp_aide_type': {'fr': 'catégorie : ast, neocp, com, pla, tno, pn, neb, amas, gal, eto (répétable)',
                      'en': 'category: ast, neocp, com, pla, tno, pn, neb, amas, gal, eto (repeatable)'},
    'ohp_aide_telescope': {'fr': 'télescope (répétable)', 'en': 'telescope (repeatable)'},
    'ohp_aide_filtre': {'fr': 'filtre : B, V, R (Johnson et Cousins), Bc, Vc, Rc, Ha, OIII, g, r, i, z, ou le nom exact '
                              '(« Johnson R ») ; répétable ou séparé par des virgules',
                        'en': 'filter: B, V, R (Johnson and Cousins), Bc, Vc, Rc, Ha, OIII, g, r, i, z, or the exact '
                              'name (« Johnson R »); repeatable or comma-separated'},
    'ohp_aide_nuit': {'fr': 'nuit (date du soir) ; répétable', 'en': 'night (evening date); repeatable'},
    'ohp_aide_dates': {'fr': 'écarte les poses à DATE-OBS partagée ou datées en plein jour',
                       'en': 'leave out exposures with a shared DATE-OBS or dated in daytime'},
    'ohp_aide_tout': {'fr': 'toute la banque (≈ 78 Go)', 'en': 'the whole bank (≈ 78 GB)'},
    'ohp_aide_rafraichir': {'fr': 'réinterroge le service TAP de l\'Observatoire (une requête)',
                            'en': "query the Observatory's TAP service again (one request)"},
    'ohp_aide_chercher': {'fr': 'filtre les objets dont le nom contient ce texte', 'en': 'keep objects whose name contains this text'},
    'ohp_aide_csv': {'fr': 'écrit aussi la liste dans ce fichier CSV', 'en': 'also write the list to this CSV file'},
    'ohp_cli_metadonnees': {'fr': "complète focale, pixel et binning des fichiers déjà convertis (pour PixInsight, N.I.N.A.)",
                            'en': 'completes focal length, pixel and binning of already converted files (for PixInsight, N.I.N.A.)'},
    'ohp_cli_metadonnees_desc': {'fr': "Pour chaque XISF/FITS du dossier : FOCALLEN accordé à l'échelle mesurée (ancienne valeur en "
                                       "HISTORY) et propriétés XISF Instrument:Sensor:XPixelSize, Instrument:Camera:XBinning, "
                                       "Instrument:Telescope:FocalLength… Les pixels ne sont pas touchés (relus et comparés), "
                                       "écriture atomique, journal dans _traitement/metadonnees.csv. Sans --reecrire : simulation.",
                                 'en': 'For each XISF/FITS of the folder: FOCALLEN matched to the measured scale (old value in '
                                       'HISTORY) and the XISF properties Instrument:Sensor:XPixelSize, Instrument:Camera:XBinning, '
                                       'Instrument:Telescope:FocalLength… Pixels are not touched (read back and compared), atomic '
                                       'writing, log in _traitement/metadonnees.csv. Without --rewrite: dry run.'},
    'ohp_aide_metadonnees_dossier': {'fr': 'dossier de sortie (ou un lot)', 'en': 'output folder (or one stack)'},
    'ohp_aide_metadonnees_reecrire': {'fr': "écrit vraiment (sinon : dit seulement ce qui changerait) ; note aussi "
                                            "dans la base d'état l'emplacement de chaque fichier, relatif au dossier "
                                            "de sortie (copie d'un ancien traitement, autre machine)",
                                      'en': 'really write (otherwise: only say what would change); also records each '
                                            "file's location, relative to the output folder, in the state database "
                                            '(copy from an older processing run, another computer)'},
    'ohp_metadonnees_absent': {'fr': 'Dossier introuvable : {dossier}', 'en': 'Folder not found: {dossier}'},
    'ohp_metadonnees_bilan': {'fr': '{fichiers} fichier(s) : {modifies} complété(s), {inchanges} déjà à jour, {erreurs} erreur(s) '
                                    '(journal : _traitement/metadonnees.csv) ; {base} image(s) notée(s) dans la base d\'état : '
                                    '« coupole ohp ranger » récrit alors les LOT.txt avec focale et pixel ; emplacements notés : {chemins}.',
                              'en': '{fichiers} file(s): {modifies} completed, {inchanges} already up to date, {erreurs} error(s) '
                                    '(log: _traitement/metadonnees.csv); {base} image(s) noted in the state database: '
                                    '« coupole ohp sort » then rewrites the LOT.txt files with focal length and pixel; locations recorded: {chemins}.'},
    'ohp_metadonnees_simulation': {'fr': 'Simulation : {fichiers} fichier(s), {modifies} à compléter, {inchanges} déjà à jour, '
                                         '{erreurs} erreur(s){base}. Ajouter --reecrire pour écrire.',
                                   'en': 'Dry run: {fichiers} file(s), {modifies} to complete, {inchanges} already up to date, '
                                         '{erreurs} error(s){base}. Add --rewrite to write.'},
    'ohp_aide_format': {'fr': 'format de sortie : xisf (PixInsight, défaut), xisf16 (XISF compatible N.I.N.A. et Siril : '
                              'entiers 16 bits, zlib), fz (FITS compressé sans perte), fits (float32)',
                        'en': 'output format: xisf (PixInsight, default), xisf16 (XISF compatible with N.I.N.A. and Siril: '
                              '16-bit integers, zlib), fz (lossless compressed FITS), fits (float32)'},
    'ohp_aide_dest': {'fr': 'dossier de destination (défaut : ~/Coupole/OHP_DU_ECU ou celui des réglages)',
                      'en': 'destination folder (default: ~/Coupole/OHP_DU_ECU or the one in the settings)'},
    'ohp_aide_noms': {'fr': 'langue des noms de dossiers, d\'objets et des en-têtes (défaut : langue de l\'interface)',
                      'en': 'language of folder names, object names and headers (default: interface language)'},
    'ohp_aide_astap': {'fr': 'vérification ASTAP : auto/tous (chaque image si ASTAP est là), suspectes, jamais',
                       'en': 'ASTAP check: auto/all (every image when ASTAP is present), suspicious, never'},
    'ohp_aide_dl': {'fr': 'téléchargements simultanés (défaut automatique ; 4 au plus)',
                    'en': 'simultaneous downloads (automatic by default; at most 4)'},
    'ohp_aide_conv': {'fr': 'conversions simultanées (défaut : selon cœurs et mémoire)',
                      'en': 'simultaneous conversions (default: from cores and memory)'},
    'ohp_aide_econome': {'fr': 'mode économe : 1 conversion, 2 téléchargements', 'en': 'economy mode: 1 conversion, 2 downloads'},
    'ohp_aide_debit': {'fr': 'plafond de débit vers le serveur en Mo/s (défaut : réglage ; aucun plafond, 0 = illimité)', 'en': 'download rate cap in MB/s (default: setting; no cap, 0 = unlimited)'},
    'ohp_aide_garder': {'fr': 'garde aussi les FITS d\'origine (dans _traitement/fits_origine)',
                        'en': 'also keep the original FITS (in _traitement/fits_origine)'},
    'ohp_aide_oui': {'fr': 'accepte une sélection de plus de 5 Go sans confirmation', 'en': 'accept a selection over 5 GB without confirmation'},
    'ohp_cli_inventaire': {'fr': "état de l'inventaire ; --rafraichir l'actualise", 'en': 'inventory status; --refresh updates it'},
    'ohp_cli_inventaire_desc': {'fr': "Inventaire de la banque par le service TAP public (http://tap-ufe.obspm.fr/tap, "
                                      "table ivoa.obscore), gardé en cache local.",
                                'en': 'Bank inventory from the public TAP service (http://tap-ufe.obspm.fr/tap, table '
                                      'ivoa.obscore), kept in a local cache.'},
    'ohp_cli_catalogue': {'fr': 'catalogue des objets', 'en': 'object catalogue'},
    'ohp_cli_catalogue_desc': {'fr': 'Les 194 noms de la base regroupés en objets, classés par type.',
                               'en': 'The 194 database names grouped into objects, sorted by type.'},
    'ohp_cli_images': {'fr': "liste les images d'une sélection", 'en': 'list the images of a selection'},
    'ohp_cli_images_desc': {'fr': 'Une ligne par image : date, télescope, filtre, pose, drapeaux (doublon, date partagée, plein jour).',
                            'en': 'One line per image: date, telescope, filter, exposure, flags (duplicate, shared date, daytime).'},
    'ohp_cli_estimer': {'fr': 'volume à télécharger et place nécessaire', 'en': 'volume to download and space needed'},
    'ohp_cli_estimer_desc': {'fr': 'Estimation avant téléchargement, avec la place libre à destination.',
                             'en': 'Estimate before downloading, with the free space at the destination.'},
    'ohp_cli_traiter': {'fr': 'télécharge, vérifie, corrige, convertit et range en lots', 'en': 'download, check, fix, convert and sort into stacks'},
    'ohp_cli_traiter_desc': {'fr': "Traitement complet d'une sélection, reprenable : relancer la même commande reprend "
                                   "là où elle s'est arrêtée.",
                             'en': 'Full processing of a selection, resumable: running the same command again resumes '
                                   'where it stopped.'},
    'ohp_cli_telecharger': {'fr': 'télécharge les FITS d\'origine, sans conversion', 'en': 'download the original FITS, without conversion'},
    'ohp_cli_telecharger_desc': {'fr': 'Rangement : <dossier>/<objet>/<nuit>_<télescope>/<fichier d\'origine>.',
                                 'en': 'Layout: <folder>/<object>/<night>_<telescope>/<original file>.'},
    'ohp_cli_ranger': {'fr': 'recalcule les lots et range ce qui est converti', 'en': 'recompute the stacks and sort what is converted'},
    'ohp_cli_ranger_desc': {'fr': 'Utile après une interruption, ou pour regrouper plusieurs traitements dans un même dossier.',
                            'en': 'Useful after an interruption, or to merge several runs in the same folder.'},
    'ohp_cli_bilan': {'fr': "état d'avancement d'un dossier de traitement", 'en': 'progress of a processing folder'},

    # ------------------------------------------------------------ ligne de commande : messages
    'ohp_interrogation_tap': {'fr': 'Interrogation du service TAP de l\'Observatoire de Paris...',
                              'en': 'Querying the Observatoire de Paris TAP service...'},
    'ohp_inventaire_resume': {'fr': '{n} images ({doublons} doublons), {objets} objets, {nuits} nuits, {taille}.\n'
                                    'Inventaire du {date} — source : {source}',
                              'en': '{n} images ({doublons} duplicates), {objets} objects, {nuits} nights, {taille}.\n'
                                    'Inventory of {date} — source: {source}'},
    'ohp_col_type': {'fr': 'type', 'en': 'type'},
    'ohp_col_objet': {'fr': 'objet', 'en': 'object'},
    'ohp_col_images': {'fr': 'images', 'en': 'images'},
    'ohp_col_volume': {'fr': 'volume', 'en': 'volume'},
    'ohp_col_nuits': {'fr': 'nuits', 'en': 'nights'},
    'ohp_col_telescopes': {'fr': 'télescopes', 'en': 'telescopes'},
    'ohp_col_date': {'fr': 'date UTC', 'en': 'UTC date'},
    'ohp_col_tel': {'fr': 'tél.', 'en': 'tel.'},
    'ohp_col_filtre': {'fr': 'filtre', 'en': 'filter'},
    'ohp_col_pose': {'fr': 'pose (s)', 'en': 'exp. (s)'},
    'ohp_col_drapeaux': {'fr': 'remarques', 'en': 'flags'},
    'ohp_col_remarque': {'fr': 'remarque', 'en': 'note'},
    'ohp_col_filtres': {'fr': 'filtres', 'en': 'filters'},
    'ohp_col_noms': {'fr': 'noms dans la base', 'en': 'names in the database'},
    'ohp_catalogue_total': {'fr': '{n} objet(s).', 'en': '{n} object(s).'},
    'ohp_objet_inconnu': {'fr': 'Aucun objet ne correspond à « {q} ». Voir : coupole ohp catalogue',
                          'en': 'No object matches « {q} ». See: coupole ohp catalog'},
    'ohp_objet_ambigu': {'fr': '« {q} » correspond à plusieurs objets : {liste}. Préciser.',
                         'en': '« {q} » matches several objects: {liste}. Be more specific.'},
    'ohp_selection_vide': {'fr': 'Sélection vide : indiquer un objet, un filtre de sélection, ou --tout.',
                           'en': 'Empty selection: give an object, a selection filter, or --all.'},
    'ohp_drapeau_doublon': {'fr': 'doublon', 'en': 'duplicate'},
    'ohp_drapeau_date': {'fr': 'date partagée', 'en': 'shared date'},
    'ohp_drapeau_diurne': {'fr': 'plein jour', 'en': 'daytime'},
    'ohp_estimation': {'fr': '{images} image(s) de {objets} objet(s) sur {nuits} nuit(s) ({doublons} doublon(s) écarté(s)) : '
                             '{fits} à télécharger → environ {sortie} en {format}.',
                       'en': '{images} image(s) of {objets} object(s) over {nuits} night(s) ({doublons} duplicate(s) left '
                             'out): {fits} to download → about {sortie} as {format}.'},
    'ohp_estimation_fits': {'fr': '{images} image(s) ({doublons} doublon(s) écarté(s)) : {fits} à télécharger.',
                            'en': '{images} image(s) ({doublons} duplicate(s) left out): {fits} to download.'},
    'ohp_place': {'fr': 'Place à prévoir : {besoin} ; libre : {libre} ({dest}).', 'en': 'Space needed: {besoin}; free: {libre} ({dest}).'},
    'ohp_place_insuffisante': {'fr': 'Place insuffisante à destination.', 'en': 'Not enough space at the destination.'},
    'ohp_fenetre_reduite': {'fr': 'Place juste à destination ({libre} libres) : au plus {fenetre} FITS en attente au lieu de {nominale} ; '
                                  'le traitement continue, un peu moins recouvert.',
                            'en': 'Tight space at the destination ({libre} free): at most {fenetre} FITS waiting instead of {nominale}; '
                                  'processing goes on, with a little less overlap.'},
    'ohp_confirmer_gros': {'fr': 'Sélection de {taille} : ajouter --oui pour confirmer.', 'en': 'Selection of {taille}: add --yes to confirm.'},
    'ohp_rien': {'fr': 'Rien à télécharger.', 'en': 'Nothing to download.'},
    'ohp_machine': {'fr': 'Machine : {cpu} cœurs ({log} logiques), {ram} Go libres → {dl} téléchargement(s), {conv} conversion(s) ({raison}).',
                    'en': 'Computer: {cpu} cores ({log} logical), {ram} GB free → {dl} download(s), {conv} conversion(s) ({raison}).'},
    'ohp_sans_astap': {'fr': "ASTAP absent : contrôles de cohérence seulement (voir « coupole astap » pour l'installer).",
                       'en': 'ASTAP missing: consistency checks only (see « coupole astap » to install it).'},
    'ohp_astap_desactive': {'fr': 'ASTAP désactivé : contrôles de cohérence seulement.', 'en': 'ASTAP disabled: consistency checks only.'},
    'ohp_avec_astap': {'fr': 'ASTAP : {exe} (catalogue {cat}).', 'en': 'ASTAP: {exe} (catalogue {cat}).'},
    'ohp_debut': {'fr': '{total} image(s) à télécharger ({deja} déjà faite(s)).', 'en': '{total} image(s) to download ({deja} already done).'},
    'ohp_ligne_image': {'fr': '[{n}/{total}] {statut:9} {wcs:11} {debit} Mo/s  {source}',
                        'en': '[{n}/{total}] {statut:9} {wcs:11} {debit} MB/s  {source}'},
    'ohp_ligne_echec': {'fr': 'ÉCHEC {source} : {erreur}', 'en': 'FAILED {source}: {erreur}'},
    'ohp_statut_ok': {'fr': 'converti', 'en': 'converted'},
    'ohp_statut_doublon': {'fr': 'doublon', 'en': 'duplicate'},
    'ohp_statut_echec': {'fr': 'échec', 'en': 'failed'},
    'ohp_wcs_confirmee': {'fr': 'confirmée', 'en': 'confirmed'},
    'ohp_wcs_validee': {'fr': 'validée', 'en': 'validated'},
    'ohp_wcs_refaite': {'fr': 'refaite', 'en': 'redone'},
    'ohp_wcs_echec': {'fr': 'sans solution', 'en': 'no solution'},
    'ohp_wcs_douteuse': {'fr': 'douteuse', 'en': 'doubtful'},
    'ohp_wcs_aucune': {'fr': '—', 'en': '—'},
    'ohp_bilan': {'fr': '{ok} converties, {doublons} doublons, {echecs} échecs ; {fits} de FITS → {sortie} ({ratio} %) ; '
                        '{lots} lots dans {dest}',
                  'en': '{ok} converted, {doublons} duplicates, {echecs} failures; {fits} of FITS → {sortie} ({ratio} %); '
                        '{lots} stacks in {dest}'},
    'ohp_bilan_wcs': {'fr': 'Solutions astrométriques : {v}', 'en': 'Astrometric solutions: {v}'},
    'ohp_relancer': {'fr': 'Des échecs : relancer la même commande (reprise automatique, 5 essais par image).',
                     'en': 'Some failures: run the same command again (automatic resume, 5 attempts per image).'},
    'ohp_ranges': {'fr': '{n} lot(s) rangé(s).', 'en': '{n} stack(s) sorted.'},
    'ohp_pas_de_traitement': {'fr': 'Aucun traitement dans {dest}.', 'en': 'No processing in {dest}.'},
    'ohp_dl_ok': {'fr': 'téléchargé', 'en': 'downloaded'},
    'ohp_dl_deja': {'fr': 'déjà là  ', 'en': 'present   '},
    'ohp_dl_echec': {'fr': 'ÉCHEC    ', 'en': 'FAILED    '},
    'ohp_dl_fin': {'fr': '{n} fichier(s) dans {dest}, {echecs} échec(s).', 'en': '{n} file(s) in {dest}, {echecs} failure(s).'},
    'ohp_avis_langue_impose': {'fr': 'Ce dossier a déjà été rempli avec les noms en « {valeur} » : cette langue est gardée.',
                               'en': 'This folder was already filled with names in « {valeur} »: that language is kept.'},
    'ohp_avis_format_impose': {'fr': 'Ce dossier a déjà été rempli au format « {valeur} » : ce format est gardé.',
                               'en': 'This folder was already filled in « {valeur} » format: that format is kept.'},
# ------------------------------------------------------------ doublons, anomalies, classement
    'ohp_aide_garder_doublons': {'fr': "traite aussi les doublons (inventaire et pixels identiques) au lieu de les écarter",
                                 'en': 'also process duplicates (inventory and identical pixels) instead of leaving them out'},
    'ohp_url_injoignable': {'fr': "si l'adresse de téléchargement ne répond plus, voir Préférences > Sources (ou « coupole sources »)",
                            'en': 'if the download address no longer answers, see Preferences > Sources (or « coupole sources »)'},
    'ohp_cli_anomalies': {'fr': "rapport d'anomalies : ce qui est écarté ou signalé, et pourquoi", 'en': 'anomaly report: what is left out or flagged, and why'},
    'ohp_cli_anomalies_desc': {'fr': "Doublons (même fichier, copie diurne, pixels identiques), dates partagées ou diurnes, champ incohérent, "
                                     "classement à vérifier, instrument inconnu. Rien n'est supprimé.",
                               'en': 'Duplicates (same file, daytime copy, identical pixels), shared or daytime dates, inconsistent field, '
                                     'classification to check, unknown instrument. Nothing is deleted.'},
    'ohp_aide_dest_anomalies': {'fr': 'ajoute les doublons de pixels trouvés dans ce dossier de traitement',
                                'en': 'add the pixel duplicates found in this processing folder'},
    'ohp_aide_nouveaux': {'fr': 'seulement les images nouvelles depuis le dernier rafraîchissement', 'en': 'only images new since the last refresh'},
    'ohp_cli_classer': {'fr': 'classement des noms de cibles : vérifier, corriger, fusionner', 'en': 'target name classification: check, correct, merge'},
    'ohp_cli_classer_desc': {'fr': "Sans argument : liste les noms à vérifier. Avec un nom de la base et --objet : mémorise la correction "
                                   "(fusion avec un objet existant si --type est omis). --en-ligne : interroge JPL SBDB et CDS Sesame.",
                             'en': 'Without argument: list the names to check. With a database name and --object: record the correction '
                                   '(merge into an existing object if --type is omitted). --online: query JPL SBDB and CDS Sesame.'},
    'ohp_meta_nom_base': {'fr': 'NOM_BASE', 'en': 'DB_NAME'},
    'ohp_aide_nom_base': {'fr': 'nom de cible tel qu\'il figure dans la base', 'en': 'target name as it appears in the database'},
    'ohp_aide_classer_objet': {'fr': 'objet canonique à associer (existant : fusion)', 'en': 'canonical object to associate (existing one: merge)'},
    'ohp_aide_classer_oublier': {'fr': 'oublie la correction de ce nom', 'en': 'forget the correction of this name'},
    'ohp_aide_en_ligne': {'fr': 'résout en ligne les noms inconnus (JPL SBDB, CDS Sesame), avec cache', 'en': 'resolve unknown names online (JPL SBDB, CDS Sesame), with cache'},
    'ohp_nouveautes': {'fr': '{images} image(s) et {noms} nom(s) de cible nouveaux depuis le {depuis} :',
                       'en': '{images} new image(s) and {noms} new target name(s) since {depuis}:'},
    'ohp_classement_utilisateur': {'fr': '(corrigé par vous)', 'en': '(corrected by you)'},
    'ohp_classement_distant': {'fr': '(table publiée)', 'en': '(published table)'},
    'ohp_classement_table': {'fr': '(table vérifiée)', 'en': '(checked table)'},
    'ohp_classement_regle': {'fr': '(règle sur le nom)', 'en': '(name rule)'},
    'ohp_classement_sbdb': {'fr': '(JPL SBDB, à vérifier)', 'en': '(JPL SBDB, to check)'},
    'ohp_classement_sesame': {'fr': '(CDS Sesame, à vérifier)', 'en': '(CDS Sesame, to check)'},
    'ohp_classement_en_ligne': {'fr': '(en ligne, à vérifier)', 'en': '(online, to check)'},
    'ohp_classement_position': {'fr': '(même champ qu\'un objet connu, à vérifier)', 'en': '(same field as a known object, to check)'},
    'ohp_classement_inconnu': {'fr': '(non classé, à vérifier)', 'en': '(unclassified, to check)'},
    'ohp_anomalies_total': {'fr': '{n} anomalie(s). Rien n\'a été supprimé ; « Garder les doublons » télécharge aussi ce qui est écarté.',
                            'en': '{n} anomaly(ies). Nothing was deleted; « Keep duplicates » also downloads what is left out.'},
    'ohp_resolution': {'fr': 'Résolution en ligne de {n} nom(s) inconnu(s)...', 'en': 'Resolving {n} unknown name(s) online...'},
    'ohp_a_verifier': {'fr': '{n} nom(s) à vérifier.', 'en': '{n} name(s) to check.'},
    'ohp_correction_oubliee': {'fr': 'Correction de « {nom} » oubliée.', 'en': 'Correction of « {nom} » forgotten.'},
    'ohp_nom_absent': {'fr': '« {nom} » ne figure pas dans la base.', 'en': '« {nom} » is not in the database.'},
    'ohp_correction_faite': {'fr': '« {nom} » → {objet} [{cat}] : correction mémorisée.', 'en': '« {nom} » → {objet} [{cat}]: correction recorded.'},
    'anom_action_ecartee': {'fr': 'écartée', 'en': 'left out'},
    'anom_action_signalee': {'fr': 'signalée', 'en': 'flagged'},
    'anom_meme_fichier': {'fr': 'même pose sous un autre chemin ou une autre orthographe', 'en': 'same exposure under another path or spelling'},
    'anom_copie_diurne': {'fr': "copie datée en plein jour d'une image bien datée", 'en': 'daytime-dated copy of a correctly dated image'},
    'anom_memes_meta': {'fr': 'mêmes date, filtre, pose et taille qu\'une autre image (nom différent)', 'en': 'same date, filter, exposure and size as another image (different name)'},
    'anom_date_partagee': {'fr': 'DATE-OBS identique à celle d\'une autre pose (une des deux est fausse)', 'en': 'DATE-OBS identical to another exposure (one of them is wrong)'},
    'anom_date_diurne': {'fr': 'pose datée entre 5 h et 17 h UTC', 'en': 'exposure dated between 5 and 17 h UTC'},
    'anom_champ_incoherent': {'fr': 'centre du champ loin des autres poses de l\'objet', 'en': 'field centre far from the other exposures of the object'},
    'anom_classement': {'fr': 'nom classé automatiquement ou non classé : à vérifier', 'en': 'name classified automatically or not at all: to check'},
    'anom_instrument': {'fr': 'instrument inconnu de la table (rangé à part)', 'en': 'instrument unknown to the table (kept separate)'},
    'anom_pixels_identiques': {'fr': 'pixels identiques à une autre image (empreinte SHA-1)', 'en': 'pixels identical to another image (SHA-1 fingerprint)'},
    'anom_col_genre': {'fr': 'anomalie', 'en': 'anomaly'},
    'anom_col_action': {'fr': 'action', 'en': 'action'},
    'anom_col_objet': {'fr': 'objet', 'en': 'object'},
    'anom_col_nuit': {'fr': 'nuit', 'en': 'night'},
    'anom_col_fichier': {'fr': 'fichier', 'en': 'file'},
    'anom_col_detail': {'fr': 'détail', 'en': 'detail'},
    'anom_col_explication': {'fr': 'explication', 'en': 'explanation'},
    'anom_col_url': {'fr': 'adresse', 'en': 'address'},
# ------------------------------------------------------------ interface graphique
    'ohp_onglets_aide': {'fr': 'Catalogue (choisir) → Téléchargement (options, progression) → Lots (empiler) ; Anomalies : ce qui est mis de côté et pourquoi.',
                         'en': 'Catalogue (choose) → Download (options, progress) → Stacks (stack); Anomalies: what is set aside and why.'},
    'ohp_onglet_catalogue': {'fr': 'Catalogue', 'en': 'Catalogue'},
    'ohp_onglet_catalogue_aide': {'fr': 'Cibles et images de la banque : choisir une cible, puis « Télécharger ».',
                                  'en': 'Targets and images of the bank: pick a target, then « Download ».'},
    'ohp_onglet_traitement_aide': {'fr': 'Télécharger la sélection, suivre la progression et le journal ; Options : dossier, format (XISF ou FITS), doublons, vérification astrométrique, parallélisme.',
                                   'en': 'Download the selection, follow progress and the log; Options: folder, format (XISF or FITS), duplicates, astrometric check, parallelism.'},
    'ohp_onglet_lots_aide': {'fr': 'Un lot = des images à empiler ensemble (même cible, même télescope, même filtre ; même nuit pour un objet mobile), rangées dans votre dossier.',
                             'en': 'A stack = images to stack together (same target, telescope and filter; same night for a moving object), sorted in your folder.'},
    'ohp_onglet_anomalies_aide': {'fr': 'Une anomalie = une image mise de côté ou à surveiller (doublon, date douteuse, champ incohérent) ; rien n\'est supprimé.',
                                  'en': 'An anomaly = an image set aside or to watch (duplicate, doubtful date, inconsistent field); nothing is deleted.'},
    'ohp_onglet_ciel_aide': {'fr': 'Les objets de la banque sur la carte du ciel.', 'en': 'The bank\'s objects on the sky map.'},
    'ohp_onglet_fiche_aide': {'fr': 'Fiche de l\'objet choisi (SIMBAD, JPL), en ligne.',
                              'en': 'Record of the selected object (SIMBAD, JPL), online.'},
    'ohp_onglet_traitement': {'fr': 'Téléchargement', 'en': 'Download'},
    'ohp_onglet_lots': {'fr': 'Lots', 'en': 'Stacks'},
    'ohp_onglet_anomalies': {'fr': 'Anomalies', 'en': 'Anomalies'},
    'ohp_recherche_aide': {'fr': "Filtre les objets par nom (objet canonique ou nom de la base).", 'en': 'Filter objects by name (canonical object or database name).'},
    'ohp_recherche_indice': {'fr': 'Chercher un objet (NGC 6888, Pluton, 1998 AG6…)', 'en': 'Search an object (NGC 6888, Pluto, 1998 AG6…)'},
    'ohp_f_cat_aide': {'fr': "Type d'objet.", 'en': 'Object type.'},
    'ohp_f_tel_aide': {'fr': 'Télescope : T120 (1,20 m) ou IRIS (50 cm).', 'en': 'Telescope: T120 (1.20 m) or IRIS (50 cm).'},
    'ohp_tous_types': {'fr': 'Tous les types', 'en': 'All types'},
    'ohp_tous_tel': {'fr': 'Tous les télescopes', 'en': 'All telescopes'},
    'ohp_toutes_nuits': {'fr': 'Toutes les nuits', 'en': 'All nights'},
    'ohp_tous_filtres': {'fr': 'Tous les filtres', 'en': 'All filters'},
    'ohp_tous_genres': {'fr': 'Toutes les anomalies', 'en': 'All anomalies'},
    'ohp_f_nouveaux': {'fr': 'Nouveaux seulement', 'en': 'New only'},
    'ohp_f_nouveaux_aide': {'fr': "Seulement ce qui est apparu depuis le rafraîchissement précédent de l'inventaire.",
                            'en': 'Only what appeared since the previous inventory refresh.'},
    'ohp_f_verifier': {'fr': 'À vérifier', 'en': 'To check'},
    'ohp_f_verifier_aide': {'fr': 'Seulement les objets classés automatiquement ou non classés.', 'en': 'Only objects classified automatically or not at all.'},
    'ohp_f_nuit_aide': {'fr': 'Nuit (date du soir, heure UTC moins 12 h).', 'en': 'Night (evening date, UTC minus 12 h).'},
    'ohp_f_filtre_aide': {'fr': 'Filtre tel que nommé dans la base.', 'en': 'Filter as named in the database.'},
    'ohp_f_dates': {'fr': 'Sans dates douteuses', 'en': 'Without doubtful dates'},
    'ohp_f_dates_aide': {'fr': 'Écarte les poses à DATE-OBS partagée ou datées en plein jour (utile pour CometAlignment et la photométrie datée).',
                         'en': 'Leave out exposures with a shared DATE-OBS or dated in daytime (useful for CometAlignment and timed photometry).'},
    'ohp_f_genre_aide': {'fr': "Genre d'anomalie.", 'en': 'Kind of anomaly.'},
    'ohp_rafraichir': {'fr': "Rafraîchir l'inventaire", 'en': 'Refresh the inventory'},
    'ohp_rafraichir_aide': {'fr': "Réinterroge le service TAP de l'Observatoire (une requête, quelques secondes) et montre ce qui est nouveau (Ctrl+R).",
                            'en': "Query the Observatory's TAP service again (one request, a few seconds) and show what is new (Ctrl+R)."},
    'ohp_chargement': {'fr': "Chargement de l'inventaire…", 'en': 'Loading the inventory…'},
    'ohp_inventaire_erreur': {'fr': "Inventaire indisponible : {erreur}. L'inventaire en cache (ou livré) reste utilisable ; voir Préférences > Sources.",
                              'en': 'Inventory unavailable: {erreur}. The cached (or shipped) inventory is still usable; see Preferences > Sources.'},
    'ohp_table_objets_aide': {'fr': 'Cibles de la banque : cliquez sur une cible pour voir ses images à droite (Ctrl+clic ou Maj+clic pour plusieurs). Clic droit : télécharger toutes ses images, ouvrir son dossier, voir ses lots.',
                              'en': 'Targets of the bank: click a target to see its images on the right (Ctrl+click or Shift+click for several). Right-click: download all its images, open its folder, show its stacks.'},
    'ohp_table_images_aide': {'fr': "Images des cibles choisies : c'est ce que « Télécharger » récupère. Double-clic : ouvrir l'image (ou la télécharger) ; clic droit : télécharger, ouvrir, ouvrir avec, ouvrir l'emplacement.",
                              'en': 'Images of the selected targets: this is what « Download » fetches. Double-click: open the image (or download it); right-click: download, open, open with, open location.'},
    'ohp_col_focale': {'fr': 'focale (mm)', 'en': 'focal length (mm)'},
    'ohp_col_pixel': {'fr': 'pixel (µm)', 'en': 'pixel (µm)'},
    'ohp_col_echelle': {'fr': 'échelle (″ px⁻¹)', 'en': 'scale (″ px⁻¹)'},
    'ohp_astro_titre': {'fr': 'Pour PixInsight / N.I.N.A.', 'en': 'For PixInsight / N.I.N.A.'},
    'ohp_astro_aide': {'fr': "Valeurs du lot choisi, lues dans l'en-tête de ses images : à saisir dans PixInsight (ImageSolver, "
                             "panneau « Astrometric solution » de WBPP) ou N.I.N.A. La focale est celle qui donne l'échelle "
                             "mesurée ; le pixel est le pixel effectif, binning compris.",
                       'en': 'Values of the selected stack, read from its images\' header: to enter in PixInsight (ImageSolver, '
                             'WBPP « Astrometric solution » panel) or N.I.N.A. The focal length is the one giving the measured '
                             'scale; the pixel is the effective pixel, binning included.'},
    'ohp_astro_instrument': {'fr': 'Instrument', 'en': 'Instrument'},
    'ohp_astro_focale': {'fr': 'Focale', 'en': 'Focal length'},
    'ohp_astro_pixel': {'fr': 'Pixel effectif', 'en': 'Effective pixel'},
    'ohp_astro_binning': {'fr': 'Binning', 'en': 'Binning'},
    'ohp_astro_avert_binning': {'fr': "Si le logiciel affiche {e2} ″ px⁻¹ (le double), il a appliqué le binning deux fois : saisir le "
                                "pixel non binné ({pnb} µm) avec le binning {b}, ou le pixel effectif avec le binning 1.",
                          'en': 'If the program shows {e2} ″ px⁻¹ (twice as much), it applied the binning twice: enter the '
                                'unbinned pixel ({pnb} µm) with binning {b}, or the effective pixel with binning 1.'},
    'ohp_astro_echelle': {'fr': 'Échelle', 'en': 'Scale'},
    'ohp_astro_champ': {'fr': 'Champ', 'en': 'Field'},
    'ohp_astro_centre': {'fr': 'Centre', 'en': 'Centre'},
    'ohp_astro_copier': {'fr': 'Copier', 'en': 'Copy'},
    'ohp_astro_copier_aide': {'fr': 'Copie cette valeur dans le presse-papiers.', 'en': 'Copies this value to the clipboard.'},
    'ohp_astro_tout': {'fr': 'Tout copier', 'en': 'Copy all'},
    'ohp_astro_tout_aide': {'fr': 'Copie toutes les valeurs du lot, au format texte.', 'en': 'Copies all the stack values, as text.'},
    'ohp_astro_copie': {'fr': 'Copié dans le presse-papiers.', 'en': 'Copied to the clipboard.'},
    'ohp_astro_copier_lot': {'fr': "Copier les paramètres d'astrométrie", 'en': 'Copy the astrometry parameters'},
    'ohp_astro_note': {'fr': "WBPP résout le master avec ses métadonnées si elles survivent à l'intégration, sinon avec les valeurs "
                             "de son panneau « Astrometric solution », qui restent celles du dernier instrument utilisé : y saisir "
                             "focale et pixel ci-dessus (un fichier de réglages WBPP par instrument évite de les ressaisir). "
                             "Vérifier : ouvrir le master, FITSHeader ou Image > Properties, chercher XPIXSZ, FOCALLEN et "
                             "Instrument:*.",
                       'en': 'WBPP solves the master with its metadata if they survive integration, otherwise with the values of '
                             'its « Astrometric solution » panel, which stay those of the last instrument used: enter the focal '
                             'length and pixel above there (one WBPP settings file per instrument avoids typing them again). '
                             'To check: open the master, FITSHeader or Image > Properties, look for XPIXSZ, FOCALLEN and '
                             'Instrument:*.'},
    'ohp_col_lots': {'fr': 'lots', 'en': 'stacks'},
    'ohp_repartition_lots': {'fr': "{n} images rangées en {lots} lots : {detail} — on empile lot par lot (même champ, même "
                                   "instrument, même filtre) : posséder toutes les images d'un objet ne veut pas dire qu'elles "
                                   "s'empilent ensemble.",
                             'en': '{n} images sorted into {lots} stacks: {detail} — stack each stack separately (same field, '
                                   'same instrument, same filter): owning all the images of an object does not mean they '
                                   'stack together.'},
    'ohp_objet_dossier': {'fr': 'Ouvrir le dossier de la cible', 'en': 'Open the target folder'},
    'ohp_objet_dossier_aide': {'fr': 'Ouvre le dossier de cet objet dans le dossier de sortie (gestionnaire de fichiers).',
                               'en': 'Opens this object\'s folder in the output folder (file manager).'},
    'ohp_objet_rien': {'fr': "Rien n'est encore téléchargé pour cet objet.", 'en': 'Nothing downloaded yet for this object.'},
    'ohp_objet_lots': {'fr': 'Voir les lots de cet objet', 'en': 'Show this object\'s stacks'},
    'ohp_objet_lots_aide': {'fr': "Onglet Lots, limité à cet objet : chaque lot s'empile à part.",
                            'en': 'Stacks tab, limited to this object: each stack is stacked separately.'},
    'ohp_lots_tous': {'fr': 'Tous les lots', 'en': 'All stacks'},
    'ohp_lots_tous_aide': {'fr': 'Retire le filtre sur un objet.', 'en': 'Removes the filter on an object.'},
    'ohp_lots_filtre': {'fr': 'Lots de {objet} : {n}', 'en': 'Stacks of {objet}: {n}'},
    'ohp_lot_ouvrir_dossier': {'fr': 'Ouvrir le dossier du lot', 'en': 'Open the stack folder'},
    'ohp_objet_pas_de_lot': {'fr': "Aucun lot pour cet objet dans INDEX_LOTS.csv du dossier de sortie.",
                             'en': 'No stack for this object in the output folder\'s INDEX_LOTS.csv.'},
    'ohp_motif_pas_de_lot': {'fr': 'aucun lot', 'en': 'no stack'},
    'ohp_lot_absent': {'fr': "Ce dossier de lot n'existe pas (ou plus) dans le dossier de sortie.",
                       'en': 'This stack folder does not exist (any more) in the output folder.'},
    'ohp_motif_dossier_absent': {'fr': 'dossier absent', 'en': 'folder missing'},
    'ohp_chemins_migres': {'fr': "Emplacements de {n} images retrouvés dans _traitement/journal.csv (copie d'un "
                                 "ancien traitement) et notés dans la base d'état.",
                           'en': 'Locations of {n} images found in _traitement/journal.csv (copy from an older '
                                 'processing run) and recorded in the state database.'},
    'ohp_col_etat': {'fr': 'état', 'en': 'status'},
    # ------------------------------------------------------------ ce qu'on possède déjà
    'ohp_col_possede': {'fr': 'possédé', 'en': 'owned'},
    'ohp_col_complet': {'fr': 'complet', 'en': 'complete'},
    'ohp_f_manquantes': {'fr': 'À télécharger seulement', 'en': 'To download only'},
    'ohp_f_manquantes_aide': {'fr': "Cache les objets entièrement possédés et, dans la liste des images, celles déjà converties ou "
                                    "écartées comme doublons de pixels ; la sélection et l'estimation ne portent plus que sur ce qui manque.",
                              'en': 'Hides fully owned objects and, in the image list, those already converted or left out as pixel '
                                    'duplicates; selection and estimate then cover only what is missing.'},
    'ohp_statut_possession_ok': {'fr': 'possédée', 'en': 'owned'},
    'ohp_statut_possession_doublon': {'fr': 'doublon écarté', 'en': 'duplicate left out'},
    'ohp_statut_possession_echec': {'fr': 'échec', 'en': 'failed'},
    'ohp_statut_possession_absente': {'fr': 'à télécharger', 'en': 'to download'},
    'ohp_bulle_possession': {'fr': '{statut}\nDate : {date}\nFichier : {chemin}', 'en': '{statut}\nDate: {date}\nFile: {chemin}'},
    'ohp_bulle_possession_objet': {'fr': 'Possédées : {possedees} / {total} — doublons de pixels écartés : {doublons} — échecs : {echecs} — à télécharger : {absentes}',
                                   'en': 'Owned: {possedees} / {total} — pixel duplicates left out: {doublons} — failed: {echecs} — to download: {absentes}'},
    'ohp_legende_aide': {'fr': "État d'après le dossier de sortie (_traitement/etat.sqlite), dans les deux listes. Images : coche verte = "
                               "convertie et rangée ; rond gris = mêmes pixels qu'une image déjà convertie, écartée ; triangle orange = "
                               "échec, à retenter ; flèche = pas encore téléchargée. Objets (pastille en tête de ligne, nom de "
                               "la même couleur) : coche = tout possédé (doublons écartés compris) ; demi-disque = en partie ; "
                               "triangle = au moins un échec ; flèche = rien de téléchargé. Trier par la colonne « possédé » range "
                               "les objets par état.",
                         'en': 'State according to the output folder (_traitement/etat.sqlite), in both lists. Images: green check = '
                               'converted and sorted; grey dot = same pixels as an image already converted, left out; orange '
                               'triangle = failed, to retry; arrow = never processed, to download. Objects (badge at the start of '
                               'the row, name in the same colour): check = everything owned (left-out duplicates included); half '
                               'disc = partly; triangle = at least one failure; arrow = nothing downloaded. Sorting by the “owned” '
                               'column orders objects by state.'},
    'ohp_statut_possession_partiel': {'fr': 'en partie', 'en': 'partly'},
    'ohp_bulle_etat_objet': {'fr': '{possedees} possédées / {total} · {absentes} à télécharger · {echecs} échec(s) · '
                                   '{doublons} doublon(s) écarté(s)',
                             'en': '{possedees} owned / {total} · {absentes} to download · {echecs} failed · '
                                   '{doublons} duplicate(s) left out'},
    'ohp_resume_possession': {'fr': 'possédées : {possedees} (+ {doublons} doublons écartés), échecs : {echecs}, '
                                    'à télécharger : {a_telecharger}',
                              'en': 'owned: {possedees} (+ {doublons} duplicates left out), failed: {echecs}, '
                                    'to download: {a_telecharger}'},
    'ohp_vide_choisir': {'fr': 'Aucune cible choisie : cliquez sur une cible dans la liste de gauche (Ctrl+clic pour en choisir plusieurs).',
                         'en': 'No target selected: click a target in the list on the left (Ctrl+click to pick several).'},
    'ohp_vide_filtres': {'fr': 'Aucune image de ces cibles ne correspond aux choix au-dessus de la liste (nuit, filtre, dates douteuses, « À télécharger seulement ») : élargissez-les.',
                         'en': 'No image of these targets matches the choices above the list (night, filter, doubtful dates, « To download only »): widen them.'},
    'ohp_vide_aucun_objet': {'fr': 'Aucun objet ne correspond à la recherche et aux filtres.',
                             'en': 'No object matches the search and the filters.'},
    'ohp_vide_tout_possede': {'fr': 'Tout est déjà téléchargé dans {dest}',
                              'en': 'Everything is already downloaded in {dest}'},
    'ohp_possession_recalculee': {'fr': 'Possession recalculée : {n} images trouvées dans {dest}',
                                  'en': 'Ownership recomputed: {n} images found in {dest}'},
    'ohp_estimation_manquantes': {'fr': '{manquantes} image(s) manquante(s) sur {total} ({possedees} déjà possédée(s)) : {fits} à télécharger → environ {sortie} en {format}.',
                                  'en': '{manquantes} missing image(s) out of {total} ({possedees} already owned): {fits} to download → about {sortie} as {format}.'},
    'ohp_lot_complet': {'fr': 'complet ({converties} / {base})', 'en': 'complete ({converties} / {base})'},
    'ohp_lot_incomplet': {'fr': 'incomplet ({converties} / {base})', 'en': 'incomplete ({converties} / {base})'},
    'ohp_lot_complet_aide': {'fr': 'Poses converties pour cet objet, cet instrument et ce filtre (et cette nuit pour un objet mobile), '
                                   'contre les poses que la banque possède ; un objet fixe découpé en plusieurs champs compte ses lots ensemble.',
                             'en': 'Exposures converted for this object, instrument and filter (and this night for a moving object), '
                                   'against the exposures the bank holds; a fixed object split into several fields counts its stacks together.'},
    'ohp_aide_manquantes': {'fr': "liste ce qui reste à télécharger par rapport au dossier de sortie (--dest)",
                            'en': 'list what remains to download compared with the output folder (--dest)'},
    'ohp_manquantes_entete': {'fr': 'Dossier : {dest}', 'en': 'Folder: {dest}'},
    'ohp_manquantes_ligne': {'fr': '{objet:<40} {manquantes:>5} / {total:<5} {taille}', 'en': '{objet:<40} {manquantes:>5} / {total:<5} {taille}'},
    'ohp_manquantes_total': {'fr': 'À télécharger : {manquantes} image(s) sur {total} ({objets} objet(s)), {taille} ; possédées : {possedees}, doublons écartés : {doublons}, échecs : {echecs}.',
                             'en': 'To download: {manquantes} image(s) out of {total} ({objets} object(s)), {taille}; owned: {possedees}, duplicates left out: {doublons}, failed: {echecs}.'},
    'ohp_manquantes_rien': {'fr': 'Aucune copie locale dans ce dossier : tout est à télécharger ({total} images, {taille}).',
                            'en': 'No local copy in this folder: everything is to download ({total} images, {taille}).'},
    'ohp_col_nuit': {'fr': 'nuit', 'en': 'night'},
    'ohp_etat_nouveau': {'fr': 'nouveau ({date})', 'en': 'new ({date})'},
    'ohp_etat_verifier': {'fr': 'à vérifier', 'en': 'to check'},
    'ohp_bulle_objet': {'fr': 'Noms dans la base : {noms} — doublons écartés : {doublons}', 'en': 'Names in the database: {noms} — duplicates left out: {doublons}'},
    'ohp_aucune_selection': {'fr': 'Aucune image choisie : cliquez sur une cible dans la liste de gauche du catalogue.', 'en': 'No image selected: click a target in the catalogue\'s left-hand list.'},
    'ohp_libre': {'fr': 'Libre à destination : {libre}.', 'en': 'Free at destination: {libre}.'},
    'ohp_corriger': {'fr': 'Corriger le classement…', 'en': 'Correct the classification…'},
    'ohp_corriger_aide': {'fr': "Renommer l'objet, changer son type, ou le fusionner avec un autre (correction mémorisée).",
                          'en': 'Rename the object, change its type, or merge it into another (correction recorded).'},
    'ohp_voir_fiche': {'fr': 'Fiche en ligne', 'en': 'Online record'},
    'ohp_voir_fiche_aide': {'fr': "Ouvre l'onglet « Fiche en ligne » pour l'objet choisi : SIMBAD (ciel profond) ou JPL "
                                  '(petits corps), si Internet est disponible.',
                            'en': 'Opens the « Online record » tab for the selected object: SIMBAD (deep sky) or JPL '
                                  '(small bodies), when the Internet is available.'},
    'ohp_corriger_un': {'fr': 'Sélectionner un seul objet.', 'en': 'Select a single object.'},
    'ohp_corriger_texte': {'fr': 'Objet : {objet}\nNoms dans la base : {noms}', 'en': 'Object: {objet}\nNames in the database: {noms}'},
    'ohp_corr_nom': {'fr': 'Nom canonique', 'en': 'Canonical name'},
    'ohp_corr_nom_aide': {'fr': 'Nom utilisé pour les dossiers, OBJECT et les lots.', 'en': 'Name used for folders, OBJECT and stacks.'},
    'ohp_corr_cat': {'fr': 'Type', 'en': 'Type'},
    'ohp_corr_cat_aide': {'fr': 'Détermine le tri : par champ (objets fixes) ou par nuit (objets mobiles).', 'en': 'Decides the sorting: by field (fixed objects) or by night (moving objects).'},
    'ohp_corr_fusion': {'fr': 'Fusionner avec', 'en': 'Merge into'},
    'ohp_corr_fusion_aide': {'fr': "Ces noms sont un alias d'un objet existant.", 'en': 'These names are an alias of an existing object.'},
    'ohp_corr_pas_fusion': {'fr': '(pas de fusion)', 'en': '(no merge)'},
    'ohp_corr_oublier': {'fr': 'Oublier ma correction', 'en': 'Forget my correction'},
    'ohp_corr_oublier_aide': {'fr': 'Revenir au classement automatique.', 'en': 'Go back to automatic classification.'},
    'ohp_corr_enregistrer': {'fr': 'Enregistrer', 'en': 'Save'},
    'ohp_corr_enregistrer_aide': {'fr': 'Mémorise la correction (fichier ohp_corrections.json des réglages).', 'en': 'Record the correction (ohp_corrections.json in the settings).'},
    'ohp_vers_traitement': {'fr': 'Options du téléchargement →', 'en': 'Download options →'},
    'ohp_vers_traitement_aide': {'fr': "Onglet Téléchargement : dossier, format (XISF ou FITS), doublons, FITS d'origine, vérification astrométrique, parallélisme ; progression et journal.", 'en': 'Download tab: folder, format (XISF or FITS), duplicates, original FITS, astrometric check, parallelism; progress and log.'},
    # ------------------------------------------------------------ télécharger sans manuel (0.7.2)
    'ohp_groupe_options': {'fr': 'Options', 'en': 'Options'},
    'ohp_guide_titre': {'fr': 'Pour télécharger des images :', 'en': 'To download images:'},
    'ohp_guide_etape1': {'fr': 'Choisissez une cible à gauche', 'en': 'Pick a target on the left'},
    'ohp_guide_etape2': {'fr': 'Ses images s\'affichent à droite', 'en': 'Its images appear on the right'},
    'ohp_guide_etape3': {'fr': 'Cliquez sur « Télécharger » sous les images', 'en': 'Click « Download » under the images'},
    'ohp_guide_suite': {'fr': "Coupole télécharge chaque image, la vérifie, la convertit (XISF pour PixInsight, ou FITS) et la range "
                              "dans votre dossier, demandé la première fois. Ensuite : double-clic sur une image pour l'ouvrir, "
                              "clic droit pour « Ouvrir avec ». Dossier, format et autres réglages : « Options du téléchargement ».",
                        'en': 'Coupole downloads each image, checks it, converts it (XISF for PixInsight, or FITS) and sorts it '
                              'into your folder, asked the first time. Then: double-click an image to open it, right-click for '
                              '« Open with ». Folder, format and other settings: « Download options ».'},
    'ohp_guide_aide': {'fr': 'Les trois gestes pour télécharger ; chaque étape faite est cochée.',
                       'en': 'The three steps to download; each step done is ticked.'},
    'ohp_guide_fermer': {'fr': 'Compris, masquer', 'en': 'Got it, hide'},
    'ohp_guide_fermer_aide': {'fr': 'Masque ce guide ; Aide > Guide de démarrage (Banque OHP) le réaffiche.',
                              'en': 'Hides this guide; Help > Getting started (OHP bank) shows it again.'},
    'ohp_guide_masque': {'fr': 'Guide masqué : Aide > Guide de démarrage (Banque OHP) le réaffiche.',
                         'en': 'Guide hidden: Help > Getting started (OHP bank) shows it again.'},
    'ohp_telecharger': {'fr': 'Télécharger', 'en': 'Download'},
    'ohp_telecharger_aide': {'fr': "Télécharge les images listées au-dessus, les vérifie, les convertit (format choisi dans les options) "
                                   "et les range dans votre dossier. Ce qui est déjà là n'est pas refait ; « Arrêter » puis "
                                   "« Télécharger » reprend là où c'était.",
                             'en': 'Downloads the images listed above, checks them, converts them (format chosen in the options) '
                                   'and sorts them into your folder. What is already there is not redone; « Stop » then '
                                   '« Download » resumes where it was.'},
    'ohp_telecharger_1': {'fr': 'Télécharger (1 image · {fits} → ≈ {sortie} en {format})',
                          'en': 'Download (1 image · {fits} → ≈ {sortie} as {format})'},
    'ohp_telecharger_n': {'fr': 'Télécharger ({n} images · {fits} → ≈ {sortie} en {format})',
                          'en': 'Download ({n} images · {fits} → ≈ {sortie} as {format})'},
    'ohp_telecharger_rien_choisi': {'fr': "Choisissez d'abord une cible dans la liste de gauche du catalogue.",
                                    'en': "First pick a target in the catalogue's left-hand list."},
    'ohp_telecharger_vide': {'fr': 'Aucune image ne correspond aux choix au-dessus de la liste (nuit, filtre…) : élargissez-les.',
                             'en': 'No image matches the choices above the list (night, filter…): widen them.'},
    'ohp_deja_telecharge': {'fr': 'Déjà téléchargé ✓', 'en': 'Already downloaded ✓'},
    'ohp_deja_telecharge_aide': {'fr': "Ces images sont déjà dans votre dossier : double-clic sur une image pour l'ouvrir.",
                                 'en': 'These images are already in your folder: double-click an image to open it.'},
    'ohp_telechargement_en_cours': {'fr': 'Téléchargement en cours…', 'en': 'Downloading…'},
    'ohp_telechargement_en_cours_aide': {'fr': "Progression à côté ; détail et journal dans l'onglet Téléchargement. « Arrêter » "
                                               "l'interrompt, « Télécharger » reprend ensuite là où c'était.",
                                         'en': 'Progress alongside; details and log in the Download tab. « Stop » interrupts it, '
                                               '« Download » then resumes where it was.'},
    'ohp_telechargement_lance': {'fr': "Téléchargement de {n} image(s) vers {dest} : progression sous la liste des images, détail "
                                       "dans l'onglet Téléchargement.",
                                 'en': 'Downloading {n} image(s) to {dest}: progress under the image list, details in the '
                                       'Download tab.'},
    'ohp_telechargement_fini': {'fr': "Téléchargement terminé : {ok} image(s) prête(s), {echecs} échec(s), dans {dest}. "
                                      "Double-clic sur une image pour l'ouvrir.",
                                'en': 'Download finished: {ok} image(s) ready, {echecs} failure(s), in {dest}. Double-click an '
                                      'image to open it.'},
    'ohp_attendre_fin': {'fr': 'Un téléchargement est en cours : attendez qu\'il se termine, ou arrêtez-le.',
                         'en': 'A download is in progress: wait for it to finish, or stop it.'},
    'ohp_motif_en_cours': {'fr': 'téléchargement en cours', 'en': 'download in progress'},
    'ohp_motif_deja': {'fr': 'déjà téléchargé', 'en': 'already downloaded'},
    'ohp_motif_pas_telechargee': {'fr': 'pas encore téléchargée', 'en': 'not downloaded yet'},
    'ohp_pas_telechargee': {'fr': "Cette image n'est pas encore téléchargée : « Télécharger cette image » (en haut de ce menu), "
                                  "double-clic sur la ligne, ou le bouton « Télécharger ».",
                            'en': 'This image is not downloaded yet: « Download this image » (top of this menu), double-click '
                                  'the row, or the « Download » button.'},
    'ohp_menu_telecharger_image': {'fr': 'Télécharger cette image', 'en': 'Download this image'},
    'ohp_menu_telecharger_images': {'fr': 'Télécharger ces {n} images', 'en': 'Download these {n} images'},
    'ohp_menu_telecharger_objet': {'fr': 'Télécharger toutes les images de {nom}', 'en': 'Download all the images of {nom}'},
    'ohp_menu_telecharger_objets': {'fr': 'Télécharger toutes les images de ces {n} cibles',
                                    'en': 'Download all the images of these {n} targets'},
    'ohp_proposer_image': {'fr': "Cette image n'est pas encore téléchargée ({fits}).\n\nLa télécharger maintenant ? Elle sera "
                                 "convertie et rangée dans votre dossier ; un double-clic l'ouvrira ensuite.",
                           'en': 'This image is not downloaded yet ({fits}).\n\nDownload it now? It will be converted and sorted '
                                 'into your folder; a double-click will then open it.'},
    'ohp_proposer_images': {'fr': "{n} images ne sont pas encore téléchargées ({fits}).\n\nLes télécharger maintenant ?",
                            'en': '{n} images are not downloaded yet ({fits}).\n\nDownload them now?'},
    'ohp_proposer_objet': {'fr': "{n} image(s) de {nom} ne sont pas encore téléchargées ({fits}).\n\nLes télécharger maintenant ?",
                           'en': '{n} image(s) of {nom} are not downloaded yet ({fits}).\n\nDownload them now?'},
    'ohp_estimation_aide': {'fr': 'Volume à télécharger, place prise une fois converti, et place libre dans votre dossier.',
                            'en': 'Volume to download, space taken once converted, and free space in your folder.'},
    'ohp_lots_intro': {'fr': "Un lot = des images d'une même cible, prises avec le même télescope et le même filtre (et la même nuit "
                             "pour un objet mobile) : elles s'empilent ensemble. Clic sur un lot : focale, pixel et échelle pour "
                             "PixInsight ou N.I.N.A.",
                       'en': 'A stack = images of one target, taken with the same telescope and filter (and the same night for a '
                             'moving object): they are stacked together. Click a stack: focal length, pixel and scale for '
                             'PixInsight or N.I.N.A.'},
    # info-bulles des colonnes (en-têtes)
    'ohp_col_type_aide': {'fr': "Type d'objet : galaxie, nébuleuse, amas, astéroïde, comète…", 'en': 'Object type: galaxy, nebula, cluster, asteroid, comet…'},
    'ohp_col_objet_aide': {'fr': 'Nom de la cible (plusieurs noms de la base peuvent la désigner : info-bulle de la ligne).',
                           'en': "Target name (several database names may refer to it: the row's tooltip)."},
    'ohp_col_remarque_aide': {'fr': 'Nom courant ou précision (« Croissant », « galaxie du Triangle »…).',
                              'en': 'Common name or detail (« Crescent », « Triangulum galaxy »…).'},
    'ohp_col_images_aide': {'fr': 'Nombre d\'images de la cible dans la banque.', 'en': 'Number of images of the target in the bank.'},
    'ohp_col_possede_aide': {'fr': "Images déjà dans votre dossier / images de la banque. Pastille : coche = tout, demi-disque = en "
                                   "partie, flèche = rien, triangle = un échec. Trier par cette colonne range les cibles par état.",
                             'en': 'Images already in your folder / images in the bank. Badge: check = all, half disc = partly, '
                                   'arrow = none, triangle = a failure. Sorting by this column orders targets by state.'},
    'ohp_col_volume_aide': {'fr': 'Taille à télécharger (FITS d\'origine).', 'en': 'Size to download (original FITS).'},
    'ohp_col_nuits_aide': {'fr': "Nombre de nuits d'observation.", 'en': 'Number of observing nights.'},
    'ohp_col_telescopes_aide': {'fr': 'T120 (télescope de 1,20 m) ou IRIS (télescope robotique de 50 cm).',
                                'en': 'T120 (1.20 m telescope) or IRIS (50 cm robotic telescope).'},
    'ohp_col_filtres_aide': {'fr': 'Filtres utilisés (B, V, R, Hα, OIII, g, r, i, z…).', 'en': 'Filters used (B, V, R, Hα, OIII, g, r, i, z…).'},
    'ohp_col_etat_aide': {'fr': '« nouveau » : apparu depuis le dernier rafraîchissement ; « à vérifier » : classé automatiquement.',
                          'en': '« new »: appeared since the last refresh; « to check »: classified automatically.'},
    'ohp_col_lots_aide': {'fr': 'Lots rangés dans votre dossier : un lot = des images à empiler ensemble.',
                          'en': 'Stacks sorted in your folder: a stack = images to stack together.'},
    'ohp_col_possede_img_aide': {'fr': "État de l'image dans votre dossier : possédée (coche verte), à télécharger (flèche), doublon "
                                       "écarté (rond gris), échec à retenter (triangle orange).",
                                 'en': 'State of the image in your folder: owned (green check), to download (arrow), duplicate left '
                                       'out (grey dot), failed, to retry (orange triangle).'},
    'ohp_col_date_aide': {'fr': 'Date et heure de la pose, en temps universel (UTC).', 'en': 'Date and time of the exposure, in Universal Time (UTC).'},
    'ohp_col_heure_site_aide': {'fr': "Heure locale du site d'observation (survol de la ligne : votre heure aussi).",
                                'en': 'Local time at the observing site (hover the row: your time too).'},
    'ohp_col_nuit_aide': {'fr': "Nuit d'observation, désignée par la date du soir.", 'en': 'Observing night, named by the evening date.'},
    'ohp_col_tel_aide': {'fr': 'Télescope : T120 (1,20 m) ou IRIS (50 cm).', 'en': 'Telescope: T120 (1.20 m) or IRIS (50 cm).'},
    'ohp_col_filtre_aide': {'fr': 'Filtre de la pose.', 'en': 'Filter of the exposure.'},
    'ohp_col_pose_aide': {'fr': 'Temps de pose, en secondes.', 'en': 'Exposure time, in seconds.'},
    'ohp_col_drapeaux_aide': {'fr': 'Remarques : doublon, date partagée avec une autre pose, pose datée en plein jour, nouveauté.',
                              'en': 'Flags: duplicate, date shared with another exposure, exposure dated in daytime, new.'},
    'ohp_col_noms_aide': {'fr': "Nom de la cible tel qu'il est écrit dans la base de l'Observatoire.",
                          'en': "Target name as written in the Observatory's database."},
    'ohp_selection_courante': {'fr': 'Sélection : {n} image(s) — {objets}', 'en': 'Selection: {n} image(s) — {objets}'},
    'ohp_groupe_sortie': {'fr': 'Dossier et format', 'en': 'Folder and format'},
    'ohp_groupe_astrometrie': {'fr': 'Solution astrométrique', 'en': 'Astrometric solution'},
    'ohp_groupe_machine': {'fr': 'Ordinateur et réseau', 'en': 'Computer and network'},
    'ohp_dest_aide': {'fr': 'Dossier de destination ; un dossier déjà rempli est complété et repris, jamais écrasé.',
                      'en': 'Destination folder; a folder already filled is completed and resumed, never overwritten.'},
    'ohp_garder_doublons': {'fr': 'Garder les doublons', 'en': 'Keep duplicates'},
    'ohp_garder_doublons_aide': {'fr': "Télécharge et convertit aussi les doublons de l'inventaire et les pixels identiques (signalés dans le journal).",
                                 'en': 'Also download and convert inventory duplicates and identical pixels (flagged in the log).'},
    'ohp_garder_fits': {'fr': "Garder les FITS d'origine", 'en': 'Keep the original FITS'},
    'ohp_garder_fits_aide': {'fr': "Conserve aussi les fichiers téléchargés (dans _traitement/fits_origine) : place doublée.",
                             'en': 'Also keep the downloaded files (in _traitement/fits_origine): double the space.'},
    'ohp_mode_astap_aide': {'fr': "Quand vérifier avec ASTAP : chaque image, seulement les solutions douteuses, ou jamais.",
                            'en': 'When to check with ASTAP: every image, only doubtful solutions, or never.'},
    'ohp_astap_tous': {'fr': 'Vérifier chaque image', 'en': 'Check every image'},
    'ohp_astap_suspectes': {'fr': 'Seulement les douteuses', 'en': 'Doubtful ones only'},
    'ohp_astap_jamais': {'fr': 'Jamais', 'en': 'Never'},
    'ohp_assistant_astap': {'fr': 'Assistant ASTAP…', 'en': 'ASTAP assistant…'},
    'ohp_assistant_astap_aide': {'fr': 'Détecter ou installer ASTAP (facultatif).', 'en': 'Detect or install ASTAP (optional).'},
    'ohp_lancer': {'fr': 'Lancer', 'en': 'Start'},
    'ohp_lancer_aide': {'fr': "Télécharge, vérifie, corrige, convertit et range la sélection. Reprenable à tout moment.",
                        'en': 'Download, check, fix, convert and sort the selection. Resumable at any time.'},
    'ohp_arreter': {'fr': 'Arrêter', 'en': 'Stop'},
    'ohp_arreter_aide': {'fr': "Arrête proprement : les images en cours se terminent, la reprise repart de là. "
                                 "Pendant une réorganisation : arrête la lecture des en-têtes (ce qui est reconnu est rangé).",
                         'en': 'Stop cleanly: images in progress finish, resuming starts from there. During a '
                               'reorganisation: stops reading headers (whatever is recognised is sorted).'},
    'ohp_barre_aide': {'fr': 'Images téléchargées et converties sur le total.', 'en': 'Images downloaded and converted out of the total.'},
    'ohp_journal_aide': {'fr': 'Journal du téléchargement (le détail complet est dans _traitement/journal.csv).',
                         'en': 'Download log (full details in _traitement/journal.csv).'},
    'ohp_journal_debut': {'fr': '{n} image(s) → {dest} ({format}).', 'en': '{n} image(s) → {dest} ({format}).'},
    'ohp_arret_demande': {'fr': 'Arrêt demandé : fin des images en cours…', 'en': 'Stop requested: finishing images in progress…'},
    'ohp_stats': {'fr': 'Débit : {debit} Mo/s — reste environ {reste} min', 'en': 'Rate: {debit} MB/s — about {reste} min left'},
    'ohp_erreur_traitement': {'fr': 'Erreur : {erreur} (rapportée ; relancer reprend le téléchargement).', 'en': 'Error: {erreur} (reported; starting again resumes the download).'},
    'ohp_confirmer_gros_gui': {'fr': 'La sélection fait {taille}. Continuer ?', 'en': 'The selection is {taille}. Continue?'},
    'ohp_lots_actualiser': {'fr': 'Actualiser', 'en': 'Refresh'},
    'ohp_lots_actualiser_aide': {'fr': 'Relit INDEX_LOTS.csv du dossier de sortie.', 'en': 'Read INDEX_LOTS.csv of the output folder again.'},
    'ohp_lots_ouvrir': {'fr': 'Ouvrir la fiche du lot', 'en': 'Open the stack sheet'},
    'ohp_lots_ouvrir_aide': {'fr': 'Ouvre LOT.txt (objet, poses, nuits, conseil d\'empilement). Double-clic : idem.',
                             'en': 'Open LOT.txt (object, exposures, nights, stacking advice). Double-click: same.'},
    'ohp_lots_dossier': {'fr': 'Ouvrir le dossier', 'en': 'Open the folder'},
    'ohp_lots_dossier_aide': {'fr': 'Ouvre le dossier de sortie dans le gestionnaire de fichiers.', 'en': 'Open the output folder in the file manager.'},
    'ohp_table_lots_aide': {'fr': 'Un lot = ce qu\'on empile ensemble (même objet, instrument, filtre, et même champ ou même nuit).',
                            'en': 'A stack = what is stacked together (same object, instrument, filter, and same field or same night).'},
    'ohp_lots_resume': {'fr': '{n} lot(s) dans {dest}', 'en': '{n} stack(s) in {dest}'},
    'ohp_lots_aucun': {'fr': 'Aucun lot dans {dest} pour le moment.', 'en': 'No stack in {dest} yet.'},
    'ohp_anomalies_intro': {'fr': "Une anomalie = une image mise de côté ou signalée (doublon, date douteuse, champ incohérent), avec la raison. Rien n'est supprimé ; « Garder les doublons » (options du téléchargement) télécharge aussi ce qui est écarté.",
                            'en': "An anomaly = an image set aside or flagged (duplicate, doubtful date, inconsistent field), with the reason. Nothing is deleted; « Keep duplicates » (download options) also downloads what is left out."},
    'ohp_table_anom_aide': {'fr': "Une ligne par image et par anomalie ; survol : adresse de l'image.", 'en': 'One line per image and anomaly; hover: image address.'},
    'ohp_anom_csv': {'fr': 'Exporter en CSV…', 'en': 'Export as CSV…'},
    'ohp_anom_csv_aide': {'fr': "Enregistre le rapport d'anomalies (colonnes bilingues).", 'en': 'Save the anomaly report (bilingual columns).'},
    'ohp_aide_html': {
        'fr': "<h3>Banque OHP</h3><p>Images des stages du DU à l'Observatoire de Haute-Provence (T120 depuis 2015, IRIS depuis "
              "2021), déjà calibrées (dark, flat) et résolues astrométriquement par la base.</p>"
              "<h4>Télécharger en trois gestes</h4><ol><li>Dans l'onglet <b>Catalogue</b>, <b>cliquez sur une cible</b> "
              "dans la liste de gauche (Ctrl+clic ou Maj+clic pour plusieurs ; la recherche et les types aident à la "
              "trouver).</li><li>Ses images s'affichent <b>à droite</b> ; filtrez par nuit ou par filtre si besoin.</li>"
              "<li>Cliquez sur le bouton bleu <b>Télécharger (N images · X Go → ≈ Y Go en XISF)</b> sous la liste. La "
              "première fois, Coupole demande le dossier où ranger les images (il y crée OHP_DU_ECU). La progression "
              "s'affiche sous le bouton ; à la fin, la pastille de chaque image devient une coche verte.</li></ol>"
              "<p>Ensuite : <b>double-clic</b> sur une image pour l'ouvrir, <b>clic droit</b> pour « Ouvrir avec » ou "
              "« Ouvrir l'emplacement du fichier ». Le clic droit propose aussi, en premier, « Télécharger cette image » "
              "(ou « ces N images ») ; sur une cible, « Télécharger toutes les images de … ». Un double-clic sur une "
              "image ou une cible pas encore téléchargée propose de la télécharger. Le bandeau de guidage se ferme par "
              "« Compris, masquer » et se rouvre par <b>Aide &gt; Guide de démarrage (Banque OHP)</b>. "
              "<b>Ne pas recalibrer</b> ces images.</p>"
              "<h4>Catalogue</h4><p>Les noms de la base sont regroupés en objets (cibles). La liste de droite est ce que "
              "« Télécharger » récupère ; au-dessus du bouton : volume à télécharger, place prise une fois converti, "
              "place libre. Chaque en-tête de colonne explique sa colonne au survol.</p>"
              "<h4>Téléchargement (onglet et options)</h4><p>L'onglet <b>Téléchargement</b> montre la progression et le "
              "journal, et réunit sous <b>Options</b> : dossier, format (XISF compressé, XISF compatible N.I.N.A./Siril, "
              "FITS compressé, FITS), langue des noms, garder les doublons, garder les FITS d'origine, vérifier la "
              "qualité, vérification astrométrique (ASTAP), téléchargements et conversions simultanés, débit. Le bouton "
              "« Options du téléchargement → » du catalogue y mène. Pour chaque image : téléchargement (reprise, contrôle de taille et d'en-tête), "
              "contrôle de la solution astrométrique (cohérence ; ASTAP s'il est installé), en-tête corrigé (objet, filtre, "
              "site MPC 511, centre réel, échelle, angle ; anciennes valeurs en HISTORY), conversion vérifiée pixel à pixel, "
              "rangement en lots. Arrêter puis relancer reprend là où c'était.</p><h4>Lots</h4><p>Objets fixes : un lot par "
              "champ (toutes nuits) et par filtre → StarAlignment. Objets mobiles : un lot par nuit → CometAlignment. "
              "LOT.txt donne le conseil d'empilement. <b>Possédé ≠ empilable ensemble</b> : « 840 / 840 » dit que toutes "
              "les images d'un objet sont là, pas qu'elles forment un seul empilement ; la colonne « lots » et l'info-bulle "
              "donnent la répartition (champ, instrument, filtre), et le clic droit « Voir les lots de cet objet ».</p>"
              "<h4>Ouvrir une image</h4><p>Double-clic sur une image possédée (images, Qualité) : l'application du système "
              "(pas encore téléchargée : Coupole propose de la télécharger) ; clic droit : « Télécharger cette image » "
              "d'abord, puis « Ouvrir », « Ouvrir avec » (seuls les logiciels qui lisent vraiment ce format : table vérifiée du manuel) et "
              "« Ouvrir l'emplacement du fichier ». Sur un objet : dossier de la cible, lots de l'objet.</p><h4>Anomalies</h4><p>Une anomalie = une image mise de côté ou à surveiller. Doublons, dates partagées ou diurnes, champs "
              "incohérents, noms à vérifier : tout est expliqué, rien n'est supprimé.</p>"
              "<h4>Fiche en ligne</h4><p>Facultative, si Internet est disponible : pour l'objet choisi, SIMBAD (type, "
              "coordonnées, magnitudes, parallaxe, distance mesurée, vitesse radiale et redshift, taille, identifiants, "
              "liens SIMBAD, Aladin Lite et NED pour les galaxies) ou la base des petits corps du JPL (classe orbitale, "
              "éléments, diamètre, albédo, rotation). Une requête par objet, gardée 30 jours en cache ; hors ligne, la "
              "dernière fiche connue s'affiche avec sa date. Un redshift positif s'envoie au module Cosmologie.</p>"
              "<h4>Tout télécharger, pause, journal</h4><p><b>Tout télécharger…</b> prend toute la banque (≈ 8 000 images, 78 Go → ≈ 30 Go en XISF) : le dossier est demandé au premier usage, puis volume, durée estimée (au plafond de débit s'il est posé, sinon au débit mesuré lors des téléchargements précédents) et place libre sont affichés <b>avant</b> confirmation. Le téléchargement reprend après une coupure ou une fermeture (rien n'est refait), <b>Pause</b> le suspend, <b>Arrêter</b> l'interrompt sans attendre ; un rapport de fin résume images, durée, échecs et lots. <b>Ouvrir le journal</b> montre _traitement/JOURNAL.txt (horodaté UTC, bilingue : sessions, chaque image, écarts, erreurs). <b>Réorganiser des fichiers…</b> range dans les lots des images déjà converties par Coupole qui se trouvent ailleurs (déplacement, jamais de copie ni d'écrasement).</p><h4>Dossier sur un partage réseau (NAS)</h4><p>La base d'état n'est jamais écrite directement sur un partage (sous Linux, SQLite n'y écrit pas : « database is locked »). Coupole travaille sur une <b>base de travail locale</b> (dossier de cache), copiée depuis le partage au début et <b>recopiée sur le partage toutes les 30 s</b>, à la fin et à l'arrêt (copie vérifiée, remplacée d'un coup : jamais de verrou ni de base à moitié écrite). Au lancement suivant, une base du partage plus récente est reprise, et des écritures non recopiées après un plantage sont recopiées. Si deux ordinateurs (ou le NAS) ont écrit chacun de leur côté, rien n'est écrasé : Coupole propose de <b>fusionner</b> (le statut le plus avancé gagne : convertie > doublon > échec), en gardant les deux bases d'origine (<code>coupole ohp fusionner --dest …</code>).</p><h4>Nouveautés</h4><p>Au démarrage (au plus une fois par jour, réglable dans les Préférences), si une copie locale existe, Coupole compare l'inventaire frais à votre copie et propose les nouveautés dans un bandeau : <b>Télécharger maintenant</b>, <b>Plus tard</b> ou <b>Voir</b>. Rien n'est jamais téléchargé sans votre accord. <b>Vérifier les nouveautés</b> lance la comparaison à la demande.</p><h4>Ce qu'on possède déjà</h4><p>D'après le dossier de sortie (_traitement/etat.sqlite, relu en fond à l'ouverture et après chaque téléchargement) : dans la liste des images, une pastille et une couleur douce distinguent <b>possédée</b> (coche verte), <b>doublon écarté</b> (rond gris), <b>échec</b> (triangle orange) et <b>à télécharger</b> (flèche) ; l'info-bulle donne la date et le fichier local. Dans la liste des objets, chaque ligne commence par une pastille aux mêmes couleurs (coche verte : tout possédé, doublons écartés compris ; demi-disque : en partie ; triangle orange : au moins un échec ; flèche : rien de téléchargé), le nom prend la même couleur, et la colonne <b>possédé</b>, juste après le nom (« 120 / 300 », mini-barre), trie les objets par état. La légende, sous les deux listes, vaut pour les deux. La ligne de résumé donne le total possédé et ce qui reste à télécharger ; la case <b>À télécharger seulement</b> cache ce qu'on a déjà (une liste vide dit alors « Tout est déjà téléchargé dans … »), et l'estimation ne compte que ce qui manque. Changer de dossier de sortie relit aussitôt sa possession (message dans la barre d'état). Au premier lancement, aucune cible n'est choisie : le bandeau de guidage et la liste des images disent quoi faire. Onglet Lots : colonne <b>complet / incomplet</b> (poses converties contre poses de la banque). Ligne de commande : <code>coupole ohp inventaire --manquantes</code>.</p><h4>Dossier de suivi, base illisible, fichiers sans base</h4><p>La ligne de résumé dit quel dossier est réellement lu et ce qu'on y a trouvé : « Dossier de suivi : … — N images possédées lues ». Si la base de suivi existe mais ne peut pas être lue, un <b>bandeau d'erreur</b> le dit avec la cause (et <code>coupole.log</code> la note) : ne relancez pas un téléchargement complet, les fichiers sont peut-être bien là. Si <code>_traitement/</code> manque alors que des images converties sont rangées, <b>Reconnaître les fichiers existants</b> lit l'en-tête de chaque fichier (adresse d'origine) et reconstruit la base, en fond, sans rien télécharger ni déplacer (<code>coupole ohp reconnaitre --dest …</code>). Sous Windows, un dossier sur un lecteur réseau (O:\\…) ou un chemin UNC (\\\\serveur\\partage\\…) est lu par une copie locale de la base. <b>Rafraîchir l'inventaire</b> relit aussi la possession.</p>",
        'en': "<h3>OHP image bank</h3><p>Images from the diploma's training nights at the Observatoire de Haute-Provence "
              "(T120 since 2015, IRIS since 2021), already calibrated (dark, flat) and astrometrically solved by the database.</p>"
              "<h4>Download in three steps</h4><ol><li>In the <b>Catalogue</b> tab, <b>click a target</b> in the "
              "left-hand list (Ctrl+click or Shift+click for several; the search box and the types help find it).</li>"
              "<li>Its images appear <b>on the right</b>; filter by night or filter if needed.</li><li>Click the blue "
              "<b>Download (N images · X GB → ≈ Y GB as XISF)</b> button under the list. The first time, Coupole asks "
              "for the folder to put the images in (it creates OHP_DU_ECU there). Progress shows under the button; at "
              "the end, each image's badge turns into a green check.</li></ol><p>Then: <b>double-click</b> an image "
              "to open it, <b>right-click</b> for « Open with » or « Open file location ». Right-click also offers, "
              "first, « Download this image » (or « these N images »); on a target, « Download all the images of … ». "
              "Double-clicking an image or a target not downloaded yet offers to download it. The guide banner closes "
              "with « Got it, hide » and comes back with <b>Help &gt; Getting started (OHP bank)</b>. "
              "<b>Do not recalibrate</b> these images.</p>"
              "<h4>Catalogue</h4><p>Database names are grouped into objects (targets). The right-hand list is what "
              "« Download » fetches; above the button: volume to download, space once converted, free space. Each "
              "column header explains its column on hover.</p>"
              "<h4>Download (tab and options)</h4><p>The <b>Download</b> tab shows progress and the log, and gathers "
              "under <b>Options</b>: folder, format (compressed XISF, N.I.N.A./Siril-compatible XISF, compressed FITS, "
              "FITS), language of names, keep duplicates, keep the original FITS, check quality, astrometric check "
              "(ASTAP), simultaneous downloads and conversions, rate. The catalogue's « Download options → » button "
              "leads there. For each image: download (resume, size and header checks), astrometric "
              "solution check (consistency; ASTAP if installed), fixed header (object, filter, MPC 511 site, true centre, "
              "scale, angle; old values in HISTORY), conversion checked pixel by pixel, sorting into stacks. Stopping then "
              "starting again resumes where it was.</p><h4>Stacks</h4><p>Fixed objects: one stack per field (all nights) and "
              "filter → StarAlignment. Moving objects: one stack per night → CometAlignment. LOT.txt gives stacking advice. <b>Owned ≠ stackable together</b>: « 840 / 840 » "
              "says all the images of an object are there, not that they form one stack; the « stacks » column and the "
              "tooltip give the breakdown (field, instrument, filter), and right-click « Show this object's stacks ».</p>"
              "<h4>Opening an image</h4><p>Double-click an owned image (images, Quality): the system application (not "
              "downloaded yet: Coupole offers to download it); right-click: « Download this image » first, then "
              "« Open », « Open with » (only programs that really read this format: checked table in the manual) and "
              "« Open file location ». On an object: target folder, the object's stacks.</p>"
              "<h4>Anomalies</h4><p>An anomaly = an image set aside or to watch. Duplicates, shared or daytime dates, inconsistent fields, names to check: everything is "
              "explained, nothing is deleted.</p>"
              "<h4>Online record</h4><p>Optional, when the Internet is available: for the selected object, SIMBAD (type, "
              "coordinates, magnitudes, parallax, measured distance, radial velocity and redshift, size, identifiers, "
              "SIMBAD, Aladin Lite and, for galaxies, NED links) or JPL's small-body database (orbit class, elements, "
              "diameter, albedo, rotation). One request per object, cached for 30 days; offline, the last known record is "
              "shown with its date. A positive redshift can be sent to the Cosmology module.</p>"
              "<h4>Download everything, pause, log</h4><p><b>Download everything…</b> takes the whole bank (≈ 8,000 images, 78 GB → ≈ 30 GB as XISF): the folder is asked on first use, then volume, estimated duration (at the rate cap if one is set, otherwise at the rate measured during previous downloads) and free space are shown <b>before</b> confirmation. The download resumes after a cut or a close (nothing is redone), <b>Pause</b> suspends it, <b>Stop</b> interrupts it without waiting; an end report sums up images, duration, failures and stacks. <b>Open the log</b> shows _traitement/JOURNAL.txt (UTC timestamps, bilingual: sessions, each image, discards, errors). <b>Reorganise files…</b> sorts into the stacks images already converted by Coupole that live elsewhere (moved, never copied nor overwritten).</p><h4>Folder on a network share (NAS)</h4><p>The state database is never written directly on a share (on Linux, SQLite cannot write there: « database is locked »). Coupole works on a <b>local working database</b> (cache folder), copied from the share at the start and <b>copied back to the share every 30 s</b>, at the end and on stop (verified copy, replaced in one go: never a lock nor a half-written database). At the next start, a newer database on the share is taken over, and writes not copied back after a crash are copied. If two computers (or the NAS) each wrote on their own, nothing is overwritten: Coupole offers to <b>merge</b> (most advanced status wins: converted > duplicate > failed), keeping both original databases (<code>coupole ohp merge --dest …</code>).</p><h4>New images</h4><p>At startup (at most once a day, adjustable in Preferences), when a local copy exists, Coupole compares a fresh inventory with your copy and offers what is new in a banner: <b>Download now</b>, <b>Later</b> or <b>Show</b>. Nothing is ever downloaded without your consent. <b>Check for new images</b> runs the comparison on demand.</p><h4>What you already own</h4><p>According to the output folder (_traitement/etat.sqlite, read again in the background when opening and after each download): in the image list, a marker and a soft colour tell apart <b>owned</b> (green check), <b>duplicate left out</b> (grey dot), <b>failed</b> (orange triangle) and <b>to download</b> (arrow); the tooltip gives the date and the local file. In the object list, each row starts with a badge in the same colours (green check: everything owned, left-out duplicates included; half disc: partly; orange triangle: at least one failure; arrow: nothing downloaded), the name takes the same colour, and the <b>owned</b> column, right after the name (« 120 / 300 », mini bar), sorts objects by state. The legend, below both lists, applies to both. The summary line gives the total owned and what is left to download; the <b>To download only</b> box hides what you already have (an empty list then says “Everything is already downloaded in …”), and the estimate counts only what is missing. Changing the output folder re-reads its ownership at once (message in the status bar). At first start, no target is selected: the guide banner and the image list say what to do. Stacks tab: <b>complete / incomplete</b> column (converted exposures against the bank's). Command line: <code>coupole ohp inventory --missing</code>.</p><h4>Tracking folder, unreadable database, files without a database</h4><p>The summary line says which folder is really read and what was found there: “Tracking folder: … — N owned images read”. If the tracking database exists but cannot be read, an <b>error banner</b> says so with the cause (and <code>coupole.log</code> records it): do not start a full download again, the files may well be there. If <code>_traitement/</code> is missing while converted images are sorted, <b>Recognise existing files</b> reads the header of each file (original address) and rebuilds the database, in the background, without downloading or moving anything (<code>coupole ohp recognise --dest …</code>). On Windows, a folder on a network drive (O:\\…) or a UNC path (\\\\server\\share\\…) is read through a local copy of the database. <b>Refresh the inventory</b> also re-reads ownership.</p>"},
'ohp_onglet_ciel': {'fr': 'Carte du ciel', 'en': 'Sky map'},
    'ohp_ciel_intro': {'fr': 'Un point par objet fixe (taille : nombre d\'images), un point par nuit pour les objets mobiles. Clic : sélectionne l\'objet.',
                       'en': 'One point per fixed object (size: number of images), one point per night for moving objects. Click: select the object.'},
    'ohp_ciel_aide': {'fr': 'Survol : nom et nombre d\'images ; clic : ouvre l\'objet dans le catalogue.', 'en': 'Hover: name and number of images; click: open the object in the catalogue.'},
    'ohp_ciel_bulle': {'fr': '{nom}\n{cat} — {n} image(s)', 'en': '{nom}\n{cat} — {n} image(s)'},
    'ohp_col_heure_site': {'fr': 'heure du site', 'en': 'site time'},
'ohp_meta_cat': {'fr': 'TYPE', 'en': 'TYPE'},
'ohp_qualite': {'fr': 'Vérifier la qualité des images', 'en': 'Check image quality'},
    'ohp_qualite_aide': {'fr': 'Facultatif : après le téléchargement, mesure chaque lot (QUALITE.csv, QUALITE.txt). Demande SEP.',
                         'en': 'Optional: after the download, measure each stack (QUALITE.csv, QUALITE.txt). Needs SEP.'},

    # ------------------------------------------------------------ tout télécharger, pause, nouveautés, journal (v0.1.0, audit)
    'ohp_cli_tout': {'fr': 'télécharge et convertit toute la banque (reprenable)', 'en': 'download and convert the whole bank (resumable)'},
    'ohp_cli_tout_desc': {'fr': "Toute la banque (≈ 8 000 images, ≈ 78 Go de FITS → ≈ 30 Go en XISF), avec estimation du volume et du "
                                "temps avant confirmation ; relancer la même commande reprend là où elle s'était arrêtée.",
                          'en': 'The whole bank (≈ 8,000 images, ≈ 78 GB of FITS → ≈ 30 GB as XISF), with a volume and time estimate '
                                'before confirmation; running the same command again resumes where it stopped.'},
    'ohp_cli_nouveautes': {'fr': 'images apparues dans la banque et absentes de la copie locale', 'en': 'images that appeared in the bank and are missing locally'},
    'ohp_cli_nouveautes_desc': {'fr': "Réinterroge le service TAP, compare à la copie locale (dossier de sortie) et liste les nouveautés ; "
                                      "--telecharger les traite dans la même arborescence (jamais sans cette option).",
                                'en': 'Query the TAP service again, compare with the local copy (output folder) and list what is new; '
                                      '--download processes them into the same tree (never without this option).'},
    'ohp_aide_telecharger_nouveautes': {'fr': 'télécharge et convertit les nouveautés listées', 'en': 'download and convert the listed new images'},
    'ohp_cli_reorganiser': {'fr': 'range dans les lots des fichiers convertis ailleurs (déplacement, jamais de copie)',
                            'en': 'sort files converted elsewhere into the stacks (move, never copy)'},
    'ohp_cli_reorganiser_desc': {'fr': "Parcourt un dossier, reconnaît les fichiers produits par Coupole (en-tête) et les déplace dans "
                                       "l'arborescence des lots de --dest ; conflit de nom → suffixe et ligne de journal ; rien n'est écrasé.",
                                 'en': 'Walk a folder, recognise files produced by Coupole (header) and move them into the stack tree of '
                                       '--dest; name conflict → suffix and a log line; nothing is overwritten.'},
    'ohp_aide_source_reorg': {'fr': 'dossier où se trouvent les fichiers à ranger', 'en': 'folder holding the files to sort'},
    'ohp_estimation_tout': {'fr': 'Toute la banque : {images} image(s) de {objets} objet(s), {fits} à télécharger → environ {sortie} en '
                                  '{format} ; {duree}.',
                            'en': 'The whole bank: {images} image(s) of {objets} object(s), {fits} to download → about {sortie} as '
                                  '{format}; {duree}.'},
    'ohp_duree_au_plafond': {'fr': 'au débit plafond de {debit} Mo/s : environ {temps}',
                             'en': 'at the {debit} MB/s cap: about {temps}'},
    'ohp_duree_au_mesure': {'fr': 'au débit mesuré lors des derniers téléchargements ({debit} Mo/s) : environ {temps}',
                            'en': 'at the rate measured during the last downloads ({debit} MB/s): about {temps}'},
    'ohp_duree_inconnue': {'fr': "durée selon la connexion (pas de plafond de débit ; elle s'affiche pendant le "
                                 "téléchargement, d'après le débit mesuré)",
                           'en': 'duration depends on the connection (no rate cap; it is shown during the download, '
                                 'from the measured rate)'},
    'ohp_duree_h': {'fr': '{h} h {m:02d} min', 'en': '{h} h {m:02d} min'},
    'ohp_duree_min': {'fr': '{m} min', 'en': '{m} min'},
    'ohp_duree_j': {'fr': '{j} j {h} h', 'en': '{j} d {h} h'},
    'ohp_confirmer_tout': {'fr': 'Toute la banque va être téléchargée et convertie ; ajouter --oui pour confirmer.',
                           'en': 'The whole bank is about to be downloaded and converted; add --yes to confirm.'},
    'ohp_tout': {'fr': 'Tout télécharger…', 'en': 'Download everything…'},
    'ohp_tout_aide': {'fr': "Toute la banque (≈ 8 000 images, ≈ 78 Go → ≈ 30 Go en XISF) : estimation du volume et du temps, confirmation, "
                            "puis téléchargement et conversion reprenables (ce qui est déjà fait n'est pas refait).",
                      'en': 'The whole bank (≈ 8,000 images, ≈ 78 GB → ≈ 30 GB as XISF): volume and time estimate, confirmation, '
                            'then a resumable download and conversion (what is already done is not redone).'},
    'ohp_tout_titre': {'fr': 'Tout télécharger', 'en': 'Download everything'},
    'ohp_tout_question': {'fr': '{estimation}\n\nDossier : {dest}\n{place}\n\nLe téléchargement peut être arrêté et repris à tout moment ; '
                                "ce qui est fait n'est jamais refait. Lancer ?",
                          'en': '{estimation}\n\nFolder: {dest}\n{place}\n\nThe download can be stopped and resumed at any time; '
                                'what is done is never redone. Start?'},
    'ohp_place_manque': {'fr': 'Place insuffisante : {besoin} nécessaires, {libre} libres dans {dest}. Choisir un autre dossier ou libérer de la place.',
                         'en': 'Not enough space: {besoin} needed, {libre} free in {dest}. Choose another folder or free some space.'},
    'ohp_choisir_dest_titre': {'fr': 'Où ranger les images téléchargées ? (un dossier OHP_DU_ECU y sera créé)', 'en': 'Where to put the downloaded images? (an OHP_DU_ECU folder will be created in it)'},
    'ohp_choisir_dest_texte': {'fr': 'Choisissez le dossier qui recevra les images (proposé : {dest}). Il sera organisé en lots : '
                                     'type / objet / champ ou nuit / filtre.',
                               'en': 'Choose the folder that will receive the images (proposed: {dest}). It will be organised in stacks: '
                                     'type / object / field or night / filter.'},
    'ohp_dest_non_inscriptible': {'fr': 'Dossier de sortie non inscriptible : {dest}', 'en': 'Output folder is not writable: {dest}'},
    'ohp_pause': {'fr': 'Pause', 'en': 'Pause'},
    'ohp_pause_aide': {'fr': "Suspend le téléchargement (les images en cours se terminent) ; cliquer de nouveau pour reprendre.",
                       'en': 'Suspend the download (images in progress finish); click again to resume.'},
    'ohp_reprendre': {'fr': 'Reprendre', 'en': 'Resume'},
    'ohp_pause_journal': {'fr': 'Pause.', 'en': 'Paused.'},
    'ohp_reprise_journal': {'fr': 'Reprise.', 'en': 'Resumed.'},
    'ohp_ouvrir_journal': {'fr': 'Ouvrir le journal', 'en': 'Open the log'},
    'ohp_ouvrir_journal_aide': {'fr': 'Ouvre _traitement/JOURNAL.txt du dossier de sortie : sessions, chaque image, écarts et erreurs, horodatés (UTC), FR / EN.',
                                'en': 'Open _traitement/JOURNAL.txt of the output folder: sessions, each image, discards and errors, timestamped (UTC), FR / EN.'},
    'ohp_journal_absent': {'fr': 'Aucun journal dans {dest} pour le moment.', 'en': 'No log in {dest} yet.'},
    'ohp_reorganiser': {'fr': 'Réorganiser des fichiers…', 'en': 'Reorganise files…'},
    'ohp_reorganiser_aide': {'fr': "Range dans l'arborescence des lots des images déjà converties par Coupole qui se trouvent ailleurs ou "
                                   "selon un ancien rangement : déplacement (jamais de copie), jamais d'écrasement, journal ; "
                                   "en-têtes lus en parallèle, progression affichée, « Arrêter » l'interrompt.",
                             'en': 'Sort images already converted by Coupole that live elsewhere or in an older layout into the stack '
                                   'tree: move (never copy), never overwrite, logged; headers read in parallel, progress shown, '
                                   '“Stop” interrupts it.'},
    'ohp_reorganise_progression': {'fr': 'Réorganisation : {fait} / {total} en-têtes lus…',
                                   'en': 'Reorganising: {fait} / {total} headers read…'},
    'ohp_reorganiser_titre': {'fr': 'Dossier contenant les fichiers à ranger', 'en': 'Folder holding the files to sort'},
    'ohp_reorganise_fait': {'fr': '{n} fichier(s) rangé(s) dans {lots} lot(s), {ignores} ignoré(s) (détail dans JOURNAL.txt).',
                            'en': '{n} file(s) sorted into {lots} stack(s), {ignores} ignored (details in JOURNAL.txt).'},
    'ohp_rapport_fin': {'fr': 'Rapport : {images} image(s) passée(s) en {duree} — {ok} converties, {doublons} doublons, {echecs} échec(s) ; '
                              '{sortie} écrits dans {lots} lot(s). Journal : {journal}',
                        'en': 'Report: {images} image(s) handled in {duree} — {ok} converted, {doublons} duplicates, {echecs} failure(s); '
                              '{sortie} written into {lots} stack(s). Log: {journal}'},
    'ohp_rapport_echecs': {'fr': 'Échecs : {liste}', 'en': 'Failures: {liste}'},
    'ohp_bandeau_nouveautes': {'fr': '{n} nouvelle(s) image(s) ({objets} objet(s), {taille}) depuis le {depuis} — télécharger maintenant ?',
                               'en': '{n} new image(s) ({objets} object(s), {taille}) since {depuis} — download now?'},
    'ohp_bandeau_aide': {'fr': "Nouveautés de la banque absentes de votre copie locale ; rien n'est téléchargé sans votre accord.",
                         'en': 'New images in the bank missing from your local copy; nothing is downloaded without your consent.'},
    'ohp_nouv_telecharger': {'fr': 'Télécharger maintenant', 'en': 'Download now'},
    'ohp_nouv_telecharger_aide': {'fr': 'Télécharge les seules nouveautés, dans le même dossier.', 'en': 'Download only the new images, into the same folder.'},
    'ohp_nouv_plus_tard': {'fr': 'Plus tard', 'en': 'Later'},
    'ohp_nouv_plus_tard_aide': {'fr': 'Cache ce message ; il reviendra à la prochaine vérification.', 'en': 'Hide this message; it will come back at the next check.'},
    'ohp_nouv_voir': {'fr': 'Voir', 'en': 'Show'},
    'ohp_nouv_voir_aide': {'fr': 'Filtre le catalogue sur les nouveautés.', 'en': 'Filter the catalogue on what is new.'},
    'ohp_nouv_verifier': {'fr': 'Vérifier les nouveautés', 'en': 'Check for new images'},
    'ohp_nouv_verifier_aide': {'fr': "Réinterroge le service TAP et compare à la copie locale (dossier de sortie).",
                               'en': 'Query the TAP service again and compare with the local copy (output folder).'},
    'ohp_nouv_aucune': {'fr': 'Aucune nouveauté depuis le {depuis} (copie locale à jour).', 'en': 'Nothing new since {depuis} (local copy up to date).'},
    'ohp_nouv_sans_copie': {'fr': 'Aucune copie locale dans {dest} : lancer d\'abord « Tout télécharger » ou télécharger une sélection.',
                            'en': 'No local copy in {dest}: run « Download everything » or download a selection first.'},
    'ohp_nouv_liste': {'fr': '{n} nouvelle(s) image(s), {objets} objet(s), {taille}, depuis le {depuis} :',
                       'en': '{n} new image(s), {objets} object(s), {taille}, since {depuis}:'},
    'ohp_nouv_statut': {'fr': 'Nouveautés : {n} image(s), {taille}', 'en': 'New images: {n}, {taille}'},
    'ohp_nouv_verification': {'fr': 'Vérification des nouveautés de la banque…', 'en': 'Checking the bank for new images…'},
    'ohp_nouv_hors_ligne': {'fr': 'Vérification des nouveautés impossible (hors ligne ou service indisponible).',
                            'en': 'Could not check for new images (offline or service unavailable).'},
    # ------------------------------------------------------------ JOURNAL.txt (lignes bilingues, horodatées)
    'jrn_session_debut': {'fr': 'DÉBUT de session Coupole {version} : {n} image(s) à télécharger, {deja} déjà faite(s) ; {dest} ({format}) ; '
                                '{dl} téléchargement(s), {conv} conversion(s)',
                          'en': 'Session START Coupole {version}: {n} image(s) to download, {deja} already done; {dest} ({format}); '
                                '{dl} download(s), {conv} conversion(s)'},
    'jrn_session_fin': {'fr': 'FIN de session ({etat}) : {ok} converties, {doublons} doublons, {echecs} échec(s), {duree} s, {sortie} Go, {lots} lot(s)',
                        'en': 'Session END ({etat}): {ok} converted, {doublons} duplicates, {echecs} failure(s), {duree} s, {sortie} GB, {lots} stack(s)'},
    'jrn_reprise': {'fr': 'reprise : {deja} image(s) déjà faite(s) ne seront pas refaites, {fits} téléchargement(s) retrouvé(s)',
                    'en': 'resume: {deja} image(s) already done will not be redone, {fits} download(s) found again'},
    'jrn_pause': {'fr': 'pause demandée', 'en': 'pause requested'},
    'jrn_fenetre_reduite': {'fr': 'place juste ({libre} Go libres) : fenêtre de FITS en attente réduite à {fenetre} (nominale {nominale})',
                            'en': 'tight space ({libre} GB free): window of waiting FITS reduced to {fenetre} (nominal {nominale})'},
    'jrn_reprise_pause': {'fr': 'reprise après pause', 'en': 'resumed after pause'},
    'jrn_telechargee': {'fr': 'téléchargée {source} ({octets} octets, {duree} s)', 'en': 'downloaded {source} ({octets} bytes, {duree} s)'},
    'jrn_convertie': {'fr': 'convertie {source} : solution {wcs}, taille {ratio} % du FITS, {duree} s',
                      'en': 'converted {source}: solution {wcs}, size {ratio} % of the FITS, {duree} s'},
    'jrn_doublon_inventaire': {'fr': 'écartée {source} : doublon d\'inventaire ({raison})', 'en': 'left out {source}: inventory duplicate ({raison})'},
    'jrn_pixels_identiques': {'fr': 'écartée {source} : pixels identiques à {autre}', 'en': 'left out {source}: pixels identical to {autre}'},
    'jrn_pixels_identiques_gardee': {'fr': 'gardée {source} malgré des pixels identiques à {autre} (option « garder les doublons »)',
                                     'en': 'kept {source} despite pixels identical to {autre} (« keep duplicates » option)'},
    'jrn_echec': {'fr': 'ÉCHEC {source} : {erreur}', 'en': 'FAILED {source}: {erreur}'},
    'jrn_processus_perdu': {'fr': 'processus de conversion perdu pendant {source} ; bassin reconstruit',
                            'en': 'conversion process lost while handling {source}; pool rebuilt'},
    'jrn_conflit_nom': {'fr': 'conflit de nom : {voulu} existait déjà → {retenu}', 'en': 'name conflict: {voulu} already existed → {retenu}'},
    'jrn_reorg_fichier': {'fr': 'réorganisation : {fichier} rattaché à {objet}', 'en': 'reorganisation: {fichier} attached to {objet}'},
    'jrn_reorg_ignore': {'fr': 'réorganisation : {fichier} ignoré ({raison})', 'en': 'reorganisation: {fichier} ignored ({raison})'},
    'reorg_deja_rangee': {'fr': 'déjà rangée ailleurs', 'en': 'already sorted elsewhere'},
    'reorg_format': {'fr': 'format inconnu', 'en': 'unknown format'},
    'reorg_illisible': {'fr': 'en-tête illisible', 'en': 'unreadable header'},
    'reorg_pas_coupole': {'fr': 'pas un fichier produit par Coupole', 'en': 'not a file produced by Coupole'},
    'reorg_inconnu_inventaire': {'fr': 'fichier d\'origine absent de l\'inventaire', 'en': 'source file missing from the inventory'},
    # base de travail locale (dossier de sortie sur un partage réseau, 0.1.10)
    'base_locale_avis': {'fr': 'Dossier sur un partage réseau : base de travail locale, recopiée sur le partage toutes les {secondes} s ({dest})',
                         'en': 'Folder on a network share: local working database, copied back to the share every {secondes} s ({dest})'},
    'base_locale_copiee': {'fr': 'Base d\'état du partage recopiée dans la base de travail locale.',
                           'en': 'State database copied from the share into the local working database.'},
    'base_locale_reprise': {'fr': 'Écritures de la session précédente pas encore recopiées (arrêt brutal) : recopiées sur le partage maintenant.',
                            'en': 'Writes of the previous session not yet copied back (abrupt stop): copied to the share now.'},
    'base_locale_rafraichie': {'fr': 'Base d\'état du partage plus récente (autre ordinateur ou NAS) : recopiée dans la base de travail locale.',
                               'en': 'State database on the share is newer (another computer or the NAS): copied into the local working database.'},
    'base_locale_divergence_en_cours': {'fr': 'La base d\'état du partage ({partage}) a été modifiée par un autre programme pendant ce téléchargement : elle n\'est plus remplacée, vos résultats restent dans la base de travail locale ; une fusion sera proposée.',
                                        'en': 'The state database on the share ({partage}) was changed by another program during this download: it is no longer replaced, your results stay in the local working database; a merge will be offered.'},
    'base_locale_partage_occupe': {'fr': 'Base d\'état du partage en cours d\'écriture par un autre programme (fichier -journal présent) : recopie remise au prochain passage.',
                                   'en': 'State database on the share is being written by another program (-journal file present): copy postponed to the next pass.'},
    'base_locale_envoi_echec': {'fr': 'Recopie de la base d\'état sur le partage impossible ({erreur}) : nouvel essai au prochain passage ; rien n\'est perdu (base de travail locale).',
                                'en': 'Could not copy the state database to the share ({erreur}): retried on the next pass; nothing is lost (local working database).'},
    'ohp_divergence_titre': {'fr': 'Deux versions de la base d\'état', 'en': 'Two versions of the state database'},
    'ohp_divergence_question': {'fr': 'La base d\'état du partage ({partage}) et votre base de travail locale ont été modifiées chacune de leur côté (deux ordinateurs, ou le NAS, ont rempli ce dossier). Rien n\'a été écrasé.\n\nFusionner les deux ? Pour chaque image, le statut le plus avancé est gardé (convertie > doublon écarté > échec) ; les deux bases d\'origine sont conservées dans {dossier}.',
                                    'en': 'The state database on the share ({partage}) and your local working database were each changed on their own (two computers, or the NAS, filled this folder). Nothing was overwritten.\n\nMerge them? For each image the most advanced status is kept (converted > duplicate left out > failed); both original databases are kept in {dossier}.'},
    'ohp_divergence_cli': {'fr': 'Deux versions de la base d\'état : celle du partage ({partage}) et la base de travail locale ont été modifiées chacune de leur côté. Rien n\'a été écrasé. Pour les fusionner (le statut le plus avancé gagne, les deux bases d\'origine sont gardées) : coupole ohp fusionner --dest "{dest}"',
                           'en': 'Two versions of the state database: the one on the share ({partage}) and the local working database were each changed on their own. Nothing was overwritten. To merge them (most advanced status wins, both originals are kept): coupole ohp merge --dest "{dest}"'},
    'ohp_fusion_faite': {'fr': 'Bases d\'état fusionnées : {total} images ({locale} venues de la base locale, {conflits} différences tranchées) ; partage mis à jour : {envoyee}. Bases d\'origine gardées : {dossier}',
                         'en': 'State databases merged: {total} images ({locale} from the local database, {conflits} differences settled); share updated: {envoyee}. Original databases kept: {dossier}'},
    'ohp_fusion_rien': {'fr': 'Pas de divergence pour {dest} : rien à fusionner.', 'en': 'No divergence for {dest}: nothing to merge.'},
    'ohp_fusion_echec': {'fr': 'Fusion impossible : {erreur}', 'en': 'Merge failed: {erreur}'},
    'ohp_fusion_relancer': {'fr': 'Relancez le téléchargement : il reprendra là où il en était.', 'en': 'Start the download again: it resumes where it stopped.'},
    'ohp_cli_fusionner': {'fr': 'fusionner la base d\'état du partage et la base de travail locale (après une divergence)',
                          'en': 'merge the state database on the share with the local working database (after a divergence)'},
    # ------------------------------------------------------------ 0.2.1 : base de suivi illisible ou absente
    'ohp_base_illisible': {'fr': "La base de suivi de ce dossier n'a pas pu être lue : {erreur}.  Rien n'est affiché comme "
                                 "possédé tant qu'elle reste illisible — ne relancez pas un téléchargement complet : "
                                 "les fichiers sont peut-être bien là.  Base : {chemin}",
                           'en': 'The tracking database of this folder could not be read: {erreur}.  Nothing is shown as '
                                 'owned while it stays unreadable — do not start a full download again: the files may '
                                 'well be there.  Database: {chemin}'},
    'ohp_base_absente_fichiers': {'fr': "Ce dossier contient des images converties mais pas de base de suivi "
                                        "(_traitement/etat.sqlite) : rien n'y paraît possédé.  « Reconnaître les fichiers "
                                        "existants » lit l'en-tête de chaque fichier (adresse d'origine) et reconstruit la "
                                        "base, sans rien télécharger ni déplacer.",
                                  'en': 'This folder holds converted images but no tracking database '
                                        '(_traitement/etat.sqlite): nothing in it looks owned.  “Recognise existing files” '
                                        'reads the header of each file (original address) and rebuilds the database, '
                                        'without downloading or moving anything.'},
    'ohp_bandeau_base_aide': {'fr': "État de la base de suivi du dossier de sortie (ce qui est déjà possédé).",
                              'en': 'State of the tracking database of the output folder (what is already owned).'},
    'ohp_reconnaitre': {'fr': 'Reconnaître les fichiers existants', 'en': 'Recognise existing files'},
    'ohp_reconnaitre_aide': {'fr': "Lit l'en-tête de chaque image convertie du dossier de sortie (OHP:Source:URL ou "
                                   "HISTORY) et l'inscrit comme possédée dans la base de suivi.  Ne télécharge rien, ne "
                                   "déplace rien, ne réécrit aucun fichier.",
                             'en': 'Reads the header of each converted image of the output folder (OHP:Source:URL or '
                                   'HISTORY) and records it as owned in the tracking database.  Downloads nothing, moves '
                                   'nothing, rewrites no file.'},
    'ohp_reconnaitre_progression': {'fr': 'Reconnaissance : {fait} / {total} en-têtes lus…',
                                    'en': 'Recognising: {fait} / {total} headers read…'},
    'ohp_reconnaitre_fait': {'fr': 'Fichiers reconnus : {n} inscrits comme possédés, {deja} déjà connus, {ignores} ignorés.',
                             'en': 'Files recognised: {n} recorded as owned, {deja} already known, {ignores} skipped.'},
    'ohp_cli_reconnaitre': {'fr': "reconstruire la base de suivi d'un dossier de sortie à partir des fichiers déjà rangés "
                                  "(sans rien télécharger)",
                            'en': 'rebuild the tracking database of an output folder from the files already sorted '
                                  '(downloads nothing)'},
    'ohp_suivi_dossier': {'fr': 'Dossier de suivi : {dest} — {n} images possédées lues',
                          'en': 'Tracking folder: {dest} — {n} owned images read'},
    'ohp_suivi_sans_base': {'fr': 'Dossier de suivi : {dest} — pas de base de suivi',
                            'en': 'Tracking folder: {dest} — no tracking database'},
    'ohp_suivi_illisible': {'fr': 'Dossier de suivi : {dest} — base illisible',
                            'en': 'Tracking folder: {dest} — unreadable database'},
}
