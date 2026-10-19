"""Textes du module « Partages du DU » et de son outil « Parallaxe » (FR/EN)."""

DROITS = {
    'lire': ('lecture', 'read'), 'deposer': ('dépôt', 'upload'), 'ecrire': ('modification', 'write'),
    'dossiers': ('création de dossiers', 'folder creation'), 'renommer': ('renommage', 'rename'),
    'deplacer': ('déplacement', 'move'), 'supprimer': ('SUPPRESSION', 'DELETION'),
    'repartager': ('repartage', 'reshare'),
}
GENRES = {
    'fits': ('FITS', 'FITS'), 'jpeg': ('JPEG', 'JPEG'), 'png': ('PNG', 'PNG'), 'tiff': ('TIFF', 'TIFF'),
    'raw': ('photo brute', 'raw photo'), 'xisf': ('XISF', 'XISF'), 'ser': ('vidéo SER', 'SER video'),
    'avi': ('vidéo AVI', 'AVI video'), 'video': ('vidéo', 'video'), 'tableau': ('tableau', 'spreadsheet'),
    'astrometrie': ('solution astrométrique', 'astrometric solution'), 'document': ('document', 'document'),
    'autre': ('autre', 'other'),
}
CIBLES = {
    'iss': ('ISS', 'ISS'), 'tiangong': ('Tiangong', 'Tiangong'), 'lune': ('Lune', 'Moon'), 'soleil': ('Soleil', 'Sun'),
    'jupiter': ('Jupiter', 'Jupiter'), 'saturne': ('Saturne', 'Saturn'), 'mars': ('Mars', 'Mars'),
    'venus': ('Vénus', 'Venus'), 'mercure': ('Mercure', 'Mercury'), 'uranus': ('Uranus', 'Uranus'),
    'neptune': ('Neptune', 'Neptune'), 'eclipse': ('éclipse', 'eclipse'), 'occultation': ('occultation', 'occultation'),
    'comete': ('comète', 'comet'), 'asteroide': ('astéroïde', 'asteroid'), 'spectre': ('spectre', 'spectrum'),
}
COLONNES = {
    'etat': ('État', 'Status', "Nouveau depuis votre dernière visite, ou déjà téléchargé.",
             'New since your last visit, or downloaded.'),
    'nom': ('Fichier', 'File', 'Nom du fichier dans le partage.', 'File name in the share.'),
    'genre': ('Type', 'Type', 'Type reconnu d’après l’extension (FITS, JPEG, vidéo SER…).',
              'Type recognised from the extension (FITS, JPEG, SER video…).'),
    'taille': ('Taille', 'Size', 'Taille du fichier sur le serveur.', 'File size on the server.'),
    'instant': ('Instant (UTC)', 'Time (UTC)',
                "Instant de la prise : en-tête FITS si on l'a lu, sinon le nom du fichier (« d'après le nom » : "
                "souvent l'heure LOCALE de l'appareil, à vérifier) ; « ? » : contredit la date du dossier.",
                'Time of the shot: FITS header once read, otherwise the file name (“from the name”: often the '
                'LOCAL time of the device, to be checked); “?”: contradicts the folder date.'),
    'observateur': ('Observateur', 'Observer', "Deviné d'après le nom du fichier ou du dossier.",
                    'Guessed from the file or folder name.'),
    'cible': ('Cible', 'Target', "Reconnue d'après les noms (ISS, Lune…).", 'Recognised from the names (ISS, Moon…).'),
    'dossier': ('Dossier', 'Folder', 'Dossier dans le partage.', 'Folder in the share.'),
}
COL_MESURES = {
    'ligne': ('Ligne', 'Row'), 'niveau': ('Bilan', 'Check'), 'cible': ('Cible', 'Target'), 'auteur': ('Auteur', 'Author'),
    'instant': ('Instant (UTC)', 'Time (UTC)'), 'lat': ('Latitude', 'Latitude'), 'lon': ('Longitude', 'Longitude'),
    'alt': ('Altitude (m)', 'Elevation (m)'), 'az': ('Azimut', 'Azimuth'), 'h': ('Hauteur', 'Altitude'),
    'fichier': ('Fichier', 'File'), 'remarques': ('Remarques', 'Remarks'),
}
DEPOT = {
    'auteur': ('Auteur', 'Author', 'Votre nom, tel que vous voulez le voir dans le tableau.',
               'Your name, as you want it in the table.', 'Prénom Nom', 'First Last'),
    'cible': ('Cible', 'Target', 'Ce que vous avez photographié (Lune, ISS…).', 'What you photographed (Moon, ISS…).',
              'Lune', 'Moon'),
    'date': ('Date et heure (UTC)', 'Date and time (UTC)',
             'Milieu de la pose, en temps universel (pas l’heure locale) : AAAA-MM-JJ HH:MM:SS.',
             'Middle of the exposure, in universal time (not local time): YYYY-MM-DD HH:MM:SS.',
             '2026-10-17 04:30:03', '2026-10-17 04:30:03'),
    'latitude': ('Latitude (°)', 'Latitude (°)', 'Latitude du lieu, nord positif, en degrés décimaux.',
                 'Latitude of the site, north positive, in decimal degrees.', '45.1234', '45.1234'),
    'longitude': ('Longitude (°)', 'Longitude (°)', 'Longitude du lieu, est positif, en degrés décimaux.',
                  'Longitude of the site, east positive, in decimal degrees.', '4.5678', '4.5678'),
    'altitude': ('Altitude (m)', 'Elevation (m)', 'Altitude du lieu au-dessus du niveau de la mer, en mètres.',
                 'Elevation of the site above sea level, in metres.', '120', '120'),
    'azimut': ('Azimut (°)', 'Azimuth (°)', 'Facultatif : azimut de la cible (nord 0°, est 90°).',
               'Optional: azimuth of the target (north 0°, east 90°).', '135.2', '135.2'),
    'hauteur': ('Hauteur (°)', 'Altitude (°)', 'Facultatif : hauteur de la cible sur l’horizon.',
                'Optional: altitude of the target above the horizon.', '32.5', '32.5'),
}

TEXTES = {
    # ------------------------------------------------------------ général
    'pt_pret': {'fr': 'Prêt.', 'en': 'Ready.'},
    'pt_partage': {'fr': 'Partage', 'en': 'Share'},
    'pt_partage_aide': {'fr': 'Les partages que vous avez ajoutés (un nom libre par lien). Le contenu du partage choisi '
                              's’affiche dessous et à droite.',
                        'en': 'The shares you added (a free name per link). The content of the chosen share is shown '
                              'below and on the right.'},
    'pt_aucun_partage': {'fr': 'Aucun partage : cliquez « Ajouter un partage… » et collez le lien donné par '
                               'l’enseignant ou par un autre étudiant.',
                         'en': 'No share yet: click “Add a share…” and paste the link given by the teacher or by '
                               'another student.'},
    'pt_ajouter': {'fr': 'Ajouter un partage…', 'en': 'Add a share…'},
    'pt_ajouter_aide': {'fr': 'Coller un lien de partage Nextcloud (https://…/s/…) ; Coupole vérifie le lien et '
                              'affiche vos droits avant de le mémoriser.',
                        'en': 'Paste a Nextcloud share link (https://…/s/…); Coupole checks the link and shows your '
                              'rights before remembering it.'},
    'pt_rafraichir': {'fr': 'Rafraîchir', 'en': 'Refresh'},
    'pt_rafraichir_aide': {'fr': 'Relire tout le contenu du partage (en arrière-plan) ; ce qui est apparu depuis votre '
                                 'dernière visite est marqué « nouveau ».',
                           'en': 'Read the whole share again (in the background); what appeared since your last visit '
                                 'is marked “new”.'},
    'pt_gerer': {'fr': 'Gérer ▾', 'en': 'Manage ▾'},
    'pt_gerer_aide': {'fr': 'Renommer, vérifier, copier le lien ou oublier ce partage (dans Coupole seulement : rien '
                            'n’est jamais modifié sur le serveur).',
                      'en': 'Rename, check, copy the link or forget this share (in Coupole only: nothing is ever '
                            'changed on the server).'},
    'pt_renommer': {'fr': 'Renommer…', 'en': 'Rename…'},
    'pt_renommer_aide': {'fr': 'Changer le nom que vous donnez à ce partage.', 'en': 'Change the name you give to this '
                                                                                     'share.'},
    'pt_renommer_question': {'fr': 'Nouveau nom :', 'en': 'New name:'},
    'pt_verifier': {'fr': 'Vérifier le lien et les droits', 'en': 'Check the link and the rights'},
    'pt_verifier_aide': {'fr': 'Relire les droits annoncés par le serveur.', 'en': 'Read the rights announced by the '
                                                                                   'server again.'},
    'pt_copier_lien': {'fr': 'Copier le lien', 'en': 'Copy the link'},
    'pt_copier_lien_aide': {'fr': 'Copier le lien de partage dans le presse-papiers (à transmettre seulement aux '
                                  'personnes concernées).',
                            'en': 'Copy the share link to the clipboard (to be passed only to the people concerned).'},
    'pt_lien_copie': {'fr': 'Lien copié.', 'en': 'Link copied.'},
    'pt_oublier': {'fr': 'Oublier ce partage', 'en': 'Forget this share'},
    'pt_oublier_aide': {'fr': 'Retirer ce partage de la liste de Coupole. Rien n’est touché sur le serveur.',
                        'en': 'Remove this share from the Coupole list. Nothing is touched on the server.'},
    'pt_oublier_question': {'fr': 'Oublier le partage « {nom} » ? Son contenu sur le serveur reste intact ; vos '
                                  'fichiers téléchargés restent sur votre disque.',
                            'en': 'Forget the share “{nom}”? Its content on the server stays intact; your downloaded '
                                  'files stay on your disk.'},
    'pt_oublie': {'fr': 'Partage « {nom} » oublié.', 'en': 'Share “{nom}” forgotten.'},
    'pt_ajoute': {'fr': 'Partage « {nom} » ajouté.', 'en': 'Share “{nom}” added.'},
    'pt_nom_defaut': {'fr': 'Partage du DU', 'en': 'DU share'},
    'pt_droits': {'fr': 'Droits du lien :', 'en': 'Link rights:'},
    'pt_droits_aide': {'fr': 'Ce que le lien permet, d’après le serveur. Coupole n’utilise que la lecture et le dépôt '
                             'de NOUVEAUX fichiers (et l’ajout d’une ligne dans un tableau, sans rien écraser) ; il '
                             'n’a aucune commande de suppression, de renommage ni de déplacement.',
                       'en': 'What the link allows, according to the server. Coupole only uses reading and uploading '
                             'NEW files (and adding a row to a table, without overwriting anything); it has no delete, '
                             'rename or move command.'},
    'pt_droit_aucun': {'fr': 'aucun', 'en': 'none'},
    'pt_attention': {'fr': 'Attention :', 'en': 'Warning:'},
    'pt_droit_suppression': {'fr': 'ce lien permet à TOUTE personne qui le possède de supprimer, renommer ou déplacer '
                                   'les fichiers des autres. Coupole ne le fait jamais ; manipulez le partage avec '
                                   'soin dans votre navigateur et ne diffusez pas le lien.',
                             'en': 'this link lets ANYONE who has it delete, rename or move the files of others. '
                                   'Coupole never does so; handle the share with care in your browser and do not '
                                   'spread the link.'},
    'pt_lecture': {'fr': 'Lecture du partage…', 'en': 'Reading the share…'},
    'pt_lecture_n': {'fr': 'Lecture du partage : {d} dossier(s), {f} élément(s)…', 'en': 'Reading the share: {d} '
                                                                                         'folder(s), {f} item(s)…'},
    'pt_lu': {'fr': 'Partage « {nom} » lu.', 'en': 'Share “{nom}” read.'},
    'pt_lu_cache': {'fr': 'Partage « {nom} » : dernière liste connue affichée, lecture en cours…',
                    'en': 'Share “{nom}”: last known list shown, reading…'},
    'pt_erreur': {'fr': 'Erreur : {erreur}', 'en': 'Error: {erreur}'},
    'pt_resume': {'fr': '{n} fichier(s) dans {d} dossier(s), {o} ; {s} série(s), {obs} observateur(s), {t} tableau(x).',
                  'en': '{n} file(s) in {d} folder(s), {o}; {s} series, {obs} observer(s), {t} table(s).'},
    'pt_resume_aide': {'fr': 'Ce que Coupole a reconnu dans le partage (d’après les seuls noms et tailles).',
                       'en': 'What Coupole recognised in the share (from names and sizes only).'},
    'pt_nouveautes': {'fr': '{n} fichier(s) nouveau(x) depuis votre dernière visite.',
                      'en': '{n} new file(s) since your last visit.'},
    'pt_nouveautes_voir': {'fr': 'Voir les nouveautés', 'en': 'Show what is new'},
    'pt_nouveautes_voir_aide': {'fr': 'Afficher seulement les fichiers apparus depuis votre dernière visite.',
                                'en': 'Show only the files that appeared since your last visit.'},
    'pt_nouveautes_vus': {'fr': 'Marquer comme vus', 'en': 'Mark as seen'},
    'pt_nouveautes_vus_aide': {'fr': 'Les fichiers actuels ne seront plus « nouveaux » à la prochaine visite.',
                               'en': 'The current files will no longer be “new” at the next visit.'},
    'pt_inconnu': {'fr': 'inconnu', 'en': 'unknown'},
    'pt_inconnue': {'fr': 'inconnue', 'en': 'unknown'},
    'pt_oui': {'fr': 'oui', 'en': 'yes'},
    'pt_non': {'fr': 'non', 'en': 'no'},
    'pt_taille_ko': {'fr': '{v} ko', 'en': '{v} kB'},
    # ------------------------------------------------------------ guide
    'pt_guide_titre': {'fr': 'Pour commencer :', 'en': 'Getting started:'},
    'pt_guide_etape1': {'fr': 'ajoutez un partage (collez son lien)', 'en': 'add a share (paste its link)'},
    'pt_guide_etape2': {'fr': 'choisissez un dossier, une série ou un tableau à gauche',
                        'en': 'choose a folder, a series or a table on the left'},
    'pt_guide_etape3': {'fr': '« Télécharger », ou l’onglet « Analyse »', 'en': '“Download”, or the “Analysis” tab'},
    'pt_guide_suite': {'fr': 'Un partage est un dossier collaboratif : chacun y dépose ses images à sa façon. Coupole '
                             'en devine la structure (dates, observateurs, séries, tableaux) et contrôle les tableaux '
                             'de mesures, sans jamais rien y modifier.',
                       'en': 'A share is a collaborative folder: everyone uploads images in their own way. Coupole '
                             'guesses its structure (dates, observers, series, tables) and checks the measurement '
                             'tables, without ever changing anything in it.'},
    'pt_guide_fermer': {'fr': 'Compris', 'en': 'Got it'},
    'pt_guide_fermer_aide': {'fr': 'Masquer ce guide (Aide > Guide des partages le réaffiche).',
                             'en': 'Hide this guide (Help > Shares guide shows it again).'},
    'pt_guide_aide': {'fr': 'Les trois gestes du module ; chaque étape faite est cochée.',
                      'en': 'The three steps of the module; each done step is ticked.'},
    'act_guide_partages': {'fr': 'Guide des partages', 'en': 'Shares guide'},
    'act_guide_partages_aide': {'fr': 'Réafficher le guide en trois étapes du module « Partages du DU ».',
                                'en': 'Show the three-step guide of the “DU shared folders” module again.'},
    # ------------------------------------------------------------ dialogue d'ajout
    'pt_ajout_titre': {'fr': 'Ajouter un partage', 'en': 'Add a share'},
    'pt_ajout_intro': {'fr': 'Collez le lien de partage (« https://…/s/… », tel qu’il s’ouvre dans un navigateur) ou '
                             'l’adresse WebDAV du partage. Donnez-lui un nom libre (« Images-parallaxe »…). Le lien est '
                             'gardé seulement sur cet ordinateur.',
                       'en': 'Paste the share link (“https://…/s/…”, as it opens in a browser) or the WebDAV address '
                             'of the share. Give it a free name (“Parallax images”…). The link is kept on this computer '
                             'only.'},
    'pt_ajout_nom': {'fr': 'Nom', 'en': 'Name'},
    'pt_ajout_nom_aide': {'fr': 'Un nom à vous, pour reconnaître ce partage dans la liste.',
                          'en': 'A name of your own, to recognise this share in the list.'},
    'pt_ajout_nom_indice': {'fr': 'Images-parallaxe', 'en': 'Parallax images'},
    'pt_ajout_lien': {'fr': 'Lien', 'en': 'Link'},
    'pt_ajout_lien_aide': {'fr': 'Lien de partage Nextcloud (https://serveur/s/jeton) ou adresse WebDAV publique '
                                 '(https://serveur/public.php/dav/files/jeton/).',
                           'en': 'Nextcloud share link (https://server/s/token) or public WebDAV address '
                                 '(https://server/public.php/dav/files/token/).'},
    'pt_ajout_lien_indice': {'fr': 'https://…/s/…', 'en': 'https://…/s/…'},
    'pt_ajout_mdp': {'fr': 'Mot de passe (si demandé)', 'en': 'Password (if required)'},
    'pt_ajout_mdp_aide': {'fr': 'Seulement si le partage est protégé par un mot de passe.',
                          'en': 'Only if the share is protected by a password.'},
    'pt_ajout_verifier': {'fr': 'Vérifier', 'en': 'Check'},
    'pt_ajout_verifier_aide': {'fr': 'Interroger le serveur : le lien est-il valable, que permet-il ?',
                               'en': 'Ask the server: is the link valid, what does it allow?'},
    'pt_ajout_en_cours': {'fr': 'Vérification…', 'en': 'Checking…'},
    'pt_ajout_ok': {'fr': 'Lien valable : {n} élément(s) à la racine.', 'en': 'Valid link: {n} item(s) at the root.'},
    'pt_ajout_resultat_aide': {'fr': 'Résultat de la vérification du lien.', 'en': 'Result of the link check.'},
    # ------------------------------------------------------------ liens et erreurs
    'pt_lien_vide': {'fr': 'Collez d’abord un lien.', 'en': 'Paste a link first.'},
    'pt_lien_illisible': {'fr': 'Ce texte n’est pas une adresse web.', 'en': 'This text is not a web address.'},
    'pt_lien_https': {'fr': 'Le lien doit commencer par https:// (le jeton voyagerait en clair sinon).',
                      'en': 'The link must start with https:// (the token would travel in clear text otherwise).'},
    'pt_lien_pas_partage': {'fr': 'Ce n’est pas un lien de partage Nextcloud (« /s/… » ou « /public.php/… »).',
                            'en': 'This is not a Nextcloud share link (“/s/…” or “/public.php/…”).'},
    'pt_lien_jeton_manquant': {'fr': 'Cette adresse WebDAV ne contient pas le jeton : collez plutôt le lien « /s/… ».',
                               'en': 'This WebDAV address does not contain the token: paste the “/s/…” link instead.'},
    'pt_lien_jeton_invalide': {'fr': 'Le jeton du lien est invalide.', 'en': 'The link token is invalid.'},
    'pt_err_401': {'fr': 'Accès refusé : lien périmé, ou mot de passe manquant ou faux.',
                   'en': 'Access denied: expired link, or missing or wrong password.'},
    'pt_err_403': {'fr': 'Action refusée par le serveur (droits du lien insuffisants).',
                   'en': 'Action refused by the server (insufficient link rights).'},
    'pt_err_404': {'fr': 'Introuvable : le partage ou le fichier n’existe plus.',
                   'en': 'Not found: the share or the file no longer exists.'},
    'pt_err_405': {'fr': 'Le serveur refuse cette opération.', 'en': 'The server refuses this operation.'},
    'pt_err_409': {'fr': 'Le dossier de destination n’existe pas.', 'en': 'The destination folder does not exist.'},
    'pt_err_412': {'fr': 'Conflit : le fichier a changé ou est apparu entre-temps ; rien n’a été écrasé.',
                   'en': 'Conflict: the file changed or appeared meanwhile; nothing was overwritten.'},
    'pt_err_423': {'fr': 'Fichier verrouillé (ouvert par quelqu’un d’autre) ; réessayez plus tard.',
                   'en': 'File locked (open by someone else); try again later.'},
    'pt_err_507': {'fr': 'Espace de stockage du partage plein.', 'en': 'Share storage is full.'},
    'pt_err_http': {'fr': 'Erreur du serveur.', 'en': 'Server error.'},
    'pt_err_reponse': {'fr': 'Réponse du serveur illisible.', 'en': 'Unreadable server response.'},
    'pt_err_reseau': {'fr': 'Serveur injoignable (réseau absent ou trop lent).',
                      'en': 'Server unreachable (no network or too slow).'},
    'pt_err_trop_grand': {'fr': 'Réponse trop volumineuse.', 'en': 'Response too large.'},
    # ------------------------------------------------------------ arbre et table
    'pt_arbre_aide': {'fr': 'Structure reconnue : dossiers (avec leur date), séries de poses de chaque observateur, '
                            'tableaux de mesures, nouveautés. Clic droit : télécharger tout le nœud, lire les en-têtes.',
                      'en': 'Recognised structure: folders (with their date), each observer’s series of exposures, '
                            'measurement tables, what is new. Right click: download the whole node, read the headers.'},
    'pt_n_nouveaux': {'fr': 'Nouveautés ({n})', 'en': 'New ({n})'},
    'pt_n_nouveaux_aide': {'fr': 'Fichiers apparus depuis votre dernière visite.',
                           'en': 'Files that appeared since your last visit.'},
    'pt_n_tableaux': {'fr': 'Tableaux de mesures ({n})', 'en': 'Measurement tables ({n})'},
    'pt_n_tableaux_aide': {'fr': 'Classeurs et fichiers CSV du partage (localisations, calculs…).',
                           'en': 'Spreadsheets and CSV files of the share (locations, calculations…).'},
    'pt_n_tout': {'fr': 'Tout le partage ({n} · {o})', 'en': 'Whole share ({n} · {o})'},
    'pt_n_tout_aide': {'fr': 'Tous les fichiers du partage.', 'en': 'All the files of the share.'},
    'pt_n_dossier': {'fr': '{nom} ({n} · {o})', 'en': '{nom} ({n} · {o})'},
    'pt_n_dossier_aide': {'fr': 'Dossier : {chemin}', 'en': 'Folder: {chemin}'},
    'pt_n_date': {'fr': 'Date reconnue : {date}', 'en': 'Recognised date: {date}'},
    'pt_n_lieu': {'fr': 'Lieu : {lieu}', 'en': 'Place: {lieu}'},
    'pt_n_observateur': {'fr': 'Observateur : {nom}', 'en': 'Observer: {nom}'},
    'pt_n_serie': {'fr': 'Série de {obs}, {debut} → {fin} ({n} : {genres})',
                   'en': 'Series by {obs}, {debut} → {fin} ({n}: {genres})'},
    'pt_n_serie_aide': {'fr': 'Prises successives d’un même observateur ({date}, cible : {cible}). Heures d’après les '
                              'noms tant que les en-têtes ne sont pas lus.',
                        'en': 'Successive shots of the same observer ({date}, target: {cible}). Times from the names '
                              'until the headers are read.'},
    'pt_table_aide': {'fr': 'Fichiers du nœud choisi. Clic droit : télécharger, aperçu, en-tête, analyse ; '
                            'double-clic : ouvrir ou proposer de télécharger.',
                      'en': 'Files of the chosen node. Right click: download, preview, header, analysis; double click: '
                            'open or offer to download.'},
    'pt_table_vide': {'fr': 'Rien ici : choisissez un dossier ou une série à gauche.',
                      'en': 'Nothing here: choose a folder or a series on the left.'},
    'pt_table_sans_partage': {'fr': 'Ajoutez d’abord un partage (bouton « Ajouter un partage… »).',
                              'en': 'Add a share first (“Add a share…” button).'},
    'pt_etat_nouveau': {'fr': 'nouveau', 'en': 'new'},
    'pt_etat_possede': {'fr': 'téléchargé', 'en': 'downloaded'},
    'pt_heure_nom_court': {'fr': '(nom)', 'en': '(name)'},
    'pt_heure_nom': {'fr': 'Heure lue dans le nom du fichier : souvent l’heure LOCALE de l’appareil. L’en-tête (clic '
                           'droit > Lire les en-têtes) donne l’heure TU de la pose.',
                     'en': 'Time read from the file name: often the LOCAL time of the device. The header (right click > '
                           'Read the headers) gives the UT time of the exposure.'},
    'pt_heure_douteuse': {'fr': 'Instant douteux : il contredit la date du dossier ou du dépôt.',
                          'en': 'Doubtful time: it contradicts the folder or upload date.'},
    'pt_annote': {'fr': '(annotée)', 'en': '(annotated)'},
    'pt_annotation_aide': {'fr': 'Image annotée par astrometry.net : une illustration, pas une mesure.',
                           'en': 'Image annotated by astrometry.net: an illustration, not a measurement.'},
    'pt_selection': {'fr': '{n} fichier(s) · {o}', 'en': '{n} file(s) · {o}'},
    'pt_selection_aide': {'fr': 'Sélection courante (ou tout le nœud si rien n’est sélectionné).',
                          'en': 'Current selection (or the whole node when nothing is selected).'},
    'pt_fiche_aide': {'fr': 'Ce qu’on sait du fichier choisi.', 'en': 'What is known about the chosen file.'},
    'pt_fiche_entete': {'fr': 'En-tête : latitude {lat}°, longitude {lon}°, milieu de pose {t} UTC, objet « {objet} », '
                              'solution astrométrique : {wcs}.',
                        'en': 'Header: latitude {lat}°, longitude {lon}°, mid-exposure {t} UTC, object “{objet}”, '
                              'astrometric solution: {wcs}.'},
    'pt_fiche_local': {'fr': 'Téléchargé : {chemin}', 'en': 'Downloaded: {chemin}'},
    'pt_apercu_aide': {'fr': 'Aperçu : JPEG, PNG, TIFF, FITS (étiré), première image d’une vidéo SER ou AVI (lue seule, '
                             'sans télécharger la vidéo).',
                       'en': 'Preview: JPEG, PNG, TIFF, FITS (stretched), first frame of a SER or AVI video (read '
                             'alone, without downloading the video).'},
    'pt_apercu_rien': {'fr': 'Choisissez un fichier pour son aperçu.', 'en': 'Choose a file for its preview.'},
    'pt_apercu_calcul': {'fr': 'Aperçu en cours…', 'en': 'Preview in progress…'},
    'pt_apercu_forcer': {'fr': 'Aperçu quand même', 'en': 'Preview anyway'},
    'pt_apercu_forcer_aide': {'fr': 'Télécharger le fichier entier (dans le cache) pour en faire l’aperçu.',
                              'en': 'Download the whole file (to the cache) to make its preview.'},
    'pt_ap_genre': {'fr': 'Pas d’aperçu pour ce type de fichier.', 'en': 'No preview for this file type.'},
    'pt_ap_trop_grand': {'fr': 'Fichier volumineux : aperçu sur demande.', 'en': 'Large file: preview on request.'},
    'pt_ap_illisible': {'fr': 'Image illisible.', 'en': 'Unreadable image.'},
    'pt_ap_ser_illisible': {'fr': 'En-tête SER illisible.', 'en': 'Unreadable SER header.'},
    'pt_ap_avi_illisible': {'fr': 'Fichier AVI illisible.', 'en': 'Unreadable AVI file.'},
    'pt_ap_avi_codec': {'fr': 'Vidéo AVI compressée (codec non lu) : pas d’aperçu.',
                        'en': 'Compressed AVI video (codec not read): no preview.'},
    'pt_proposer': {'fr': 'Télécharger « {nom} » ({o}) ?', 'en': 'Download “{nom}” ({o})?'},
    'pt_menu_telecharger': {'fr': 'Télécharger ({n} · {o})', 'en': 'Download ({n} · {o})'},
    'pt_menu_telecharger_tout': {'fr': 'Télécharger tout ce nœud ({n} · {o})', 'en': 'Download this whole node ({n} · '
                                                                                   '{o})'},
    'pt_menu_apercu': {'fr': 'Aperçu', 'en': 'Preview'},
    'pt_menu_entetes': {'fr': 'Lire les en-têtes FITS (lieu, heure)', 'en': 'Read the FITS headers (place, time)'},
    'pt_menu_entetes_aide': {'fr': 'Lit seulement le début de chaque FITS (34 ko) : lieu, heure TU, objet, '
                                   'solution astrométrique.',
                             'en': 'Reads only the beginning of each FITS (34 kB): place, UT time, object, astrometric '
                                   'solution.'},
    'pt_menu_tableau': {'fr': 'Lire ce tableau (onglet Mesures)', 'en': 'Read this table (Measurements tab)'},
    'pt_menu_tableau_aide': {'fr': 'Lire, normaliser et contrôler ce tableau, ligne par ligne.',
                             'en': 'Read, normalise and check this table, row by row.'},
    'pt_menu_copier': {'fr': 'Copier le chemin', 'en': 'Copy the path'},
    'pt_menu_copier_aide': {'fr': 'Copier le chemin dans le partage.', 'en': 'Copy the path in the share.'},
    'pt_motif_deja': {'fr': 'déjà téléchargé', 'en': 'already downloaded'},
    'pt_deja_aide': {'fr': 'Tout est déjà dans votre dossier.', 'en': 'Everything is in your folder already.'},
    'pt_entetes_lecture': {'fr': 'Lecture de {n} en-tête(s)…', 'en': 'Reading {n} header(s)…'},
    'pt_entetes_progres': {'fr': 'En-têtes : {n} / {t}', 'en': 'Headers: {n} / {t}'},
    'pt_entetes_lues': {'fr': '{n} en-tête(s) lu(s) : lieux et heures TU connus.',
                        'en': '{n} header(s) read: places and UT times known.'},
    # ------------------------------------------------------------ télécharger
    'pt_telecharger': {'fr': 'Télécharger', 'en': 'Download'},
    'pt_telecharger_n': {'fr': 'Télécharger ({n} · {o})', 'en': 'Download ({n} · {o})'},
    'pt_telecharger_aide': {'fr': 'Télécharger la sélection (ou tout le nœud) : reprise, débit partagé ; FITS préparés '
                                  'en XISF ou FITS avec leur solution astrométrique ; rangement par date, cible et '
                                  'observateur.',
                            'en': 'Download the selection (or the whole node): resume, shared bandwidth; FITS prepared '
                                  'as XISF or FITS with their astrometric solution; sorted by date, target and '
                                  'observer.'},
    'pt_telechargement_en_cours': {'fr': 'Téléchargement en cours…', 'en': 'Download in progress…'},
    'pt_deja': {'fr': 'Déjà téléchargé', 'en': 'Already downloaded'},
    'pt_pause': {'fr': 'Pause', 'en': 'Pause'},
    'pt_pause_aide': {'fr': 'Suspendre ou reprendre les téléchargements.', 'en': 'Suspend or resume the downloads.'},
    'pt_reprendre': {'fr': 'Reprendre', 'en': 'Resume'},
    'pt_annuler': {'fr': 'Arrêter', 'en': 'Stop'},
    'pt_annuler_aide': {'fr': 'Arrêter les téléchargements (les fichiers commencés reprendront plus tard).',
                        'en': 'Stop the downloads (started files will resume later).'},
    'pt_ouvrir_dossier': {'fr': 'Ouvrir le dossier', 'en': 'Open the folder'},
    'pt_ouvrir_dossier_aide': {'fr': 'Ouvrir le dossier de téléchargement.', 'en': 'Open the download folder.'},
    'pt_dossier': {'fr': 'Dossier :', 'en': 'Folder:'},
    'pt_dossier_aide': {'fr': 'Où ranger les fichiers : <dossier>/<partage>/<date>/<cible>/<observateur>/.',
                        'en': 'Where to store the files: <folder>/<share>/<date>/<target>/<observer>/.'},
    'pt_choisir_dossier': {'fr': 'Choisir…', 'en': 'Choose…'},
    'pt_choisir_dossier_aide': {'fr': 'Choisir le dossier de téléchargement.', 'en': 'Choose the download folder.'},
    'pt_format_aide': {'fr': 'Format des FITS préparés (les photos et vidéos restent dans leur format).',
                       'en': 'Format of the prepared FITS (photos and videos keep their format).'},
    'pt_format_xisf': {'fr': 'XISF (PixInsight)', 'en': 'XISF (PixInsight)'},
    'pt_format_fits': {'fr': 'FITS', 'en': 'FITS'},
    'pt_astrometrie_aide': {'fr': 'Solution astrométrique : celle de l’en-tête (si présente) ; « locale » : ASTAP ou '
                                  'astrometry.net installés sur cet ordinateur ; « puis nova » : en dernier recours, '
                                  'et seulement avec votre clé d’API (Préférences) et votre accord avant l’envoi, le '
                                  'service libre nova.astrometry.net.',
                            'en': 'Astrometric solution: the one in the header (if any); “local”: ASTAP or '
                                  'astrometry.net installed on this computer; “then nova”: as a last resort, and only '
                                  'with your API key (Preferences) and your consent before sending, the free '
                                  'nova.astrometry.net service.'},
    'pt_astro_wcs': {'fr': 'Astrométrie : en-tête', 'en': 'Astrometry: header'},
    'pt_astro_auto': {'fr': 'Astrométrie : locale', 'en': 'Astrometry: local'},
    'pt_astro_astap': {'fr': 'Astrométrie : ASTAP', 'en': 'Astrometry: ASTAP'},
    'pt_astro_anet': {'fr': 'Astrométrie : astrometry.net', 'en': 'Astrometry: astrometry.net'},
    'pt_astro_en_ligne': {'fr': 'Astrométrie : locale, puis nova', 'en': 'Astrometry: local, then nova'},
    'pt_nova_sans_cle': {'fr': 'Pour l’astrométrie en ligne, saisissez d’abord votre clé d’API nova.astrometry.net '
                               '(gratuite) dans Préférences > Astrométrie.',
                         'en': 'For online astrometry, first enter your nova.astrometry.net API key (free) in '
                               'Preferences > Astrometry.'},
    'pt_nova_accord_titre': {'fr': 'Envoyer à nova.astrometry.net ?', 'en': 'Send to nova.astrometry.net?'},
    'pt_nova_accord': {'fr': 'Les images de cette sélection qui n’ont pas de solution astrométrique, et que ni ASTAP ni '
                             'astrometry.net installés n’ont résolues, seront ENVOYÉES au service libre '
                             'nova.astrometry.net (version allégée : niveaux de gris, réduite), une à la fois, avec '
                             'votre clé d’API. Images {visibilite} sur le site de nova. Une image déjà envoyée ne '
                             'l’est jamais deux fois. Continuer ?',
                       'en': 'The images of this selection that have no astrometric solution, and that neither the '
                             'installed ASTAP nor astrometry.net could solve, will be SENT to the free '
                             'nova.astrometry.net service (lightened version: greyscale, reduced), one at a time, '
                             'with your API key. Images {visibilite} on the nova website. An image already sent is '
                             'never sent twice. Continue?'},
    'pt_nova_privees': {'fr': 'non publiques', 'en': 'not public'},
    'pt_nova_publiques': {'fr': 'publiques', 'en': 'public'},
    'pt_garder': {'fr': 'Garder les originaux', 'en': 'Keep the originals'},
    'pt_garder_aide': {'fr': 'Garder aussi les FITS d’origine (sous-dossier _originaux).',
                       'en': 'Also keep the original FITS (_originaux subfolder).'},
    'pt_barre_aide': {'fr': 'Progression du téléchargement.', 'en': 'Download progress.'},
    'pt_progres_aide': {'fr': 'Volume reçu et débit.', 'en': 'Received volume and rate.'},
    'pt_rien_a_telecharger': {'fr': 'Rien à télécharger.', 'en': 'Nothing to download.'},
    'pt_dl_debut': {'fr': 'Téléchargement de {n} fichier(s), {o}…', 'en': 'Downloading {n} file(s), {o}…'},
    'pt_dl_progres': {'fr': '{o} sur {t} ({d} Mo/s)', 'en': '{o} of {t} ({d} MB/s)'},
    'pt_dl_erreur': {'fr': 'Échec pour {chemin} : {erreur}', 'en': 'Failed for {chemin}: {erreur}'},
    'pt_dl_fin': {'fr': 'Terminé : {ok} téléchargé(s), {deja} déjà là, {echec} échec(s), {annule} annulé(s) — {dossier}',
                  'en': 'Done: {ok} downloaded, {deja} already there, {echec} failure(s), {annule} cancelled — '
                        '{dossier}'},
    # ------------------------------------------------------------ mesures
    'pt_onglet_contenu': {'fr': 'Contenu', 'en': 'Content'},
    'pt_onglet_contenu_aide': {'fr': 'Fichiers du partage, aperçus, téléchargement.', 'en': 'Share files, previews, '
                                                                                            'download.'},
    'pt_onglet_mesures': {'fr': 'Mesures', 'en': 'Measurements'},
    'pt_onglet_mesures_aide': {'fr': 'Tableaux de mesures lus, normalisés et contrôlés ligne par ligne.',
                               'en': 'Measurement tables read, normalised and checked row by row.'},
    'pt_onglet_analyse': {'fr': 'Analyse', 'en': 'Analysis'},
    'pt_onglet_analyse_aide': {'fr': 'L’outil adapté au défi (Parallaxe…), détecté d’après le contenu ou choisi.',
                               'en': 'The tool suited to the challenge (Parallax…), detected from the content or '
                                     'chosen.'},
    'pt_onglet_depot': {'fr': 'Déposer ma mesure', 'en': 'Upload my measurement'},
    'pt_onglet_depot_aide': {'fr': 'Déposer vos images et votre ligne de mesure, sans rien écraser.',
                             'en': 'Upload your images and your measurement row, without overwriting anything.'},
    'pt_mesures_intro': {'fr': 'Les tableaux remplis à la main mélangent les formats. Coupole les lit sans les '
                               'modifier, normalise les valeurs et signale chaque doute, preuve à l’appui (en-tête du '
                               'fichier, position de la Lune). « * » : valeur corrigée pour les calculs.',
                         'en': 'Hand-filled tables mix formats. Coupole reads them without changing them, normalises the '
                               'values and reports each doubt, with evidence (file header, position of the Moon). '
                               '“*”: value corrected for the calculations.'},
    'pt_tableau': {'fr': 'Tableau', 'en': 'Table'},
    'pt_tableau_aide': {'fr': 'Les tableaux (xlsx, csv) trouvés dans le partage.', 'en': 'The tables (xlsx, csv) found '
                                                                                         'in the share.'},
    'pt_lire_tableau': {'fr': 'Lire et contrôler', 'en': 'Read and check'},
    'pt_lire_tableau_aide': {'fr': 'Télécharger le tableau (en mémoire), le normaliser et le contrôler.',
                             'en': 'Download the table (in memory), normalise it and check it.'},
    'pt_a_verifier': {'fr': 'Lignes à vérifier seulement', 'en': 'Rows to check only'},
    'pt_a_verifier_aide': {'fr': 'Masquer les lignes sans erreur ni avertissement.', 'en': 'Hide the rows without error '
                                                                                           'or warning.'},
    'pt_corrections': {'fr': 'Corrections proposées', 'en': 'Proposed corrections'},
    'pt_corrections_aide': {'fr': 'Appliquer aux calculs les corrections proposées (latitude et longitude échangées, '
                                  'heure locale ramenée en TU…). Le tableau d’origine '
                                  'n’est jamais modifié ; les rapports disent les corrections appliquées.',
                            'en': 'Apply the proposed corrections to the calculations (swapped latitude and '
                                  'longitude, local time converted to UT…). The original table is '
                                  'never changed; the reports state the corrections applied.'},
    'pt_exporter_csv': {'fr': 'Exporter (CSV)…', 'en': 'Export (CSV)…'},
    'pt_exporter_csv_aide': {'fr': 'Enregistrer le tableau normalisé, avec les remarques, en CSV.',
                             'en': 'Save the normalised table, with the remarks, as CSV.'},
    'pt_exporte': {'fr': 'Exporté : {chemin}', 'en': 'Exported: {chemin}'},
    'pt_mesures_aide': {'fr': 'Une ligne par mesure ; info-bulle de « Remarques » : le détail de chaque contrôle.',
                        'en': 'One row per measurement; “Remarks” tooltip: details of each check.'},
    'pt_mesures_vide': {'fr': 'Choisissez un tableau puis « Lire et contrôler ».', 'en': 'Choose a table then “Read '
                                                                                         'and check”.'},
    'pt_mesures_pas_lu': {'fr': 'Tableau pas encore lu.', 'en': 'Table not read yet.'},
    'pt_mesures_pas_tableau': {'fr': 'Aucune feuille de ce classeur n’a la forme d’un tableau de mesures (lieu, date, '
                                     'cible).',
                               'en': 'No sheet of this workbook looks like a measurement table (place, date, target).'},
    'pt_mesures_resume': {'fr': '{n} ligne(s) : {e} erreur(s), {a} avertissement(s), {i} remarque(s).',
                          'en': '{n} row(s): {e} error(s), {a} warning(s), {i} note(s).'},
    'pt_mesures_resume_aide': {'fr': 'Bilan des contrôles.', 'en': 'Summary of the checks.'},
    'pt_tableau_lecture': {'fr': 'Lecture de {chemin}…', 'en': 'Reading {chemin}…'},
    'pt_tableau_lu': {'fr': '{chemin} lu et contrôlé.', 'en': '{chemin} read and checked.'},
    'pt_niveau_erreur': {'fr': 'erreur', 'en': 'error'},
    'pt_niveau_attention': {'fr': 'à vérifier', 'en': 'to check'},
    'pt_niveau_info': {'fr': 'normalisée', 'en': 'normalised'},
    'pt_niveau_ok': {'fr': 'correcte', 'en': 'correct'},
    'pt_a_manquant': {'fr': 'champ vide', 'en': 'empty field'},
    'pt_a_illisible': {'fr': 'valeur illisible : « {valeur} »', 'en': 'unreadable value: “{valeur}”'},
    'pt_a_normalise': {'fr': '« {valeur} » lu {lu}', 'en': '“{valeur}” read as {lu}'},
    'pt_a_date_us': {'fr': 'date au format américain (mois/jour) : « {valeur} » lue {lu}',
                     'en': 'US date format (month/day): “{valeur}” read as {lu}'},
    'pt_a_date_ambigue': {'fr': 'date ambiguë « {valeur} » (jour/mois ou mois/jour ?) : lue {lu}',
                          'en': 'ambiguous date “{valeur}” (day/month or month/day?): read as {lu}'},
    'pt_a_date_inversee_nom': {'fr': 'date « {valeur} » lue mois/jour : le nom du fichier donne le {nom} ; '
                                     'corrigée en {lu}',
                               'en': 'date “{valeur}” read month/day: the file name gives {nom}; corrected to {lu}'},
    'pt_a_heure_locale_dite': {'fr': 'heure locale indiquée « {valeur} » : à convertir en TU',
                               'en': 'local time stated “{valeur}”: convert to UT'},
    'pt_a_fuseau_non_dit': {'fr': 'fuseau non précisé « {valeur} » : supposé TU', 'en': 'time zone not stated '
                                                                                       '“{valeur}”: assumed UT'},
    'pt_a_altitude': {'fr': 'altitude improbable ({valeur} m)', 'en': 'unlikely elevation ({valeur} m)'},
    'pt_a_azimut': {'fr': 'azimut impossible ({valeur}°)', 'en': 'impossible azimuth ({valeur}°)'},
    'pt_a_hauteur': {'fr': 'hauteur impossible ({valeur}°)', 'en': 'impossible altitude ({valeur}°)'},
    'pt_a_longitude': {'fr': 'longitude impossible ({valeur}°)', 'en': 'impossible longitude ({valeur}°)'},
    'pt_a_latitude': {'fr': 'latitude impossible ({valeur}°)', 'en': 'impossible latitude ({valeur}°)'},
    'pt_a_inversion_certaine': {'fr': 'latitude et longitude inversées (latitude {lat}° impossible) : échangées',
                                'en': 'latitude and longitude swapped (latitude {lat}° impossible): exchanged'},
    'pt_a_inversion_entete': {'fr': 'latitude et longitude inversées : l’en-tête du fichier donne {lat}° N, {lon}° E',
                              'en': 'latitude and longitude swapped: the file header gives {lat}° N, {lon}° E'},
    'pt_a_inversion_lune': {'fr': 'latitude et longitude inversées : la hauteur et l’azimut notés ne correspondent à la '
                                  'Lune qu’avec les coordonnées échangées (écart {echange}° au lieu de {direct}°)',
                            'en': 'latitude and longitude swapped: the noted altitude and azimuth match the Moon only '
                                  'with exchanged coordinates (offset {echange}° instead of {direct}°)'},
    'pt_a_inversion_probable': {'fr': 'latitude et longitude probablement inversées : échangées, elles tombent à {ecart} '
                                      'km d’un lieu sûr du même partage ({lat}, {lon} tels quels)',
                                'en': 'latitude and longitude probably swapped: exchanged, they fall {ecart} km from a '
                                      'reliable site of the same share ({lat}, {lon} as written)'},
    'pt_a_ecart_entete': {'fr': 'lieu différent de l’en-tête du fichier ({lat}°, {lon}° ; ≈ {ecart_km} km)',
                          'en': 'place differs from the file header ({lat}°, {lon}°; ≈ {ecart_km} km)'},
    'pt_a_heure_locale_entete': {'fr': 'heure locale probable : l’en-tête du fichier donne {entete} UTC, soit TU '
                                       '{heures} h',
                                 'en': 'probable local time: the file header gives {entete} UTC, i.e. UT {heures} h'},
    'pt_a_heure_locale_lune': {'fr': 'heure locale probable : la Lune colle à {e}° près avec l’heure notée {heures} h '
                                     '(écart {e0}° sinon)',
                               'en': 'probable local time: the Moon matches within {e}° with the noted time {heures} h '
                                     '(offset {e0}° otherwise)'},
    'pt_a_ecart_horloge': {'fr': 'écart de {ecart} s avec l’heure de l’en-tête ({entete} UTC)',
                           'en': '{ecart} s difference with the header time ({entete} UTC)'},
    'pt_a_altaz_lune': {'fr': 'hauteur et azimut notés à {ecart}° de la Lune (attendu : hauteur {h}°, azimut {az}°)',
                        'en': 'noted altitude and azimuth {ecart}° away from the Moon (expected: altitude {h}°, '
                              'azimuth {az}°)'},
    'pt_a_fichier_absent': {'fr': 'fichier « {valeur} » absent du partage (proche : « {proche} »)',
                            'en': 'file “{valeur}” not in the share (close: “{proche}”)'},
    'pt_a_doublon': {'fr': 'même fichier que la ligne {autre}', 'en': 'same file as row {autre}'},
    # ------------------------------------------------------------ analyse
    'pt_outil': {'fr': 'Outil :', 'en': 'Tool:'},
    'pt_outil_aide': {'fr': 'L’outil d’analyse employé pour ce partage (gardé pour la prochaine fois).',
                      'en': 'The analysis tool used for this share (kept for next time).'},
    'pt_outil_detecte': {'fr': 'choisi d’après le contenu : {raisons}.', 'en': 'chosen from the content: {raisons}.'},
    'pt_outil_choisi': {'fr': 'choisi à la main.', 'en': 'chosen by hand.'},
    # ------------------------------------------------------------ dépôt
    'pt_depot_intro': {'fr': 'Déposez vos images (sous un nom libre : jamais d’écrasement) et ajoutez VOTRE ligne au '
                             'tableau des mesures. Rien ne part sans votre confirmation, qui liste exactement ce qui sera '
                             'envoyé. Coupole ne supprime, ne renomme et ne déplace jamais rien.',
                       'en': 'Upload your images (under a free name: never overwritten) and add YOUR row to the '
                             'measurement table. Nothing leaves without your confirmation, which lists exactly what will '
                             'be sent. Coupole never deletes, renames or moves anything.'},
    'pt_depot_permis': {'fr': 'Ce partage accepte les dépôts.', 'en': 'This share accepts uploads.'},
    'pt_depot_interdit': {'fr': 'Ce lien ne permet pas de déposer (lecture seule).', 'en': 'This link does not allow '
                                                                                         'uploads (read only).'},
    'pt_depot_ajouter': {'fr': 'Ajouter des fichiers…', 'en': 'Add files…'},
    'pt_depot_ajouter_aide': {'fr': 'Choisir vos images ou vidéos à déposer.', 'en': 'Choose your images or videos to '
                                                                                     'upload.'},
    'pt_depot_retirer': {'fr': 'Retirer', 'en': 'Remove'},
    'pt_depot_retirer_aide': {'fr': 'Retirer le fichier choisi de la liste (rien n’est touché sur le disque).',
                              'en': 'Remove the chosen file from the list (nothing is touched on disk).'},
    'pt_depot_fichiers_aide': {'fr': 'Fichiers qui seront déposés.', 'en': 'Files that will be uploaded.'},
    'pt_depot_dossier': {'fr': 'Dossier du partage', 'en': 'Share folder'},
    'pt_depot_dossier_aide': {'fr': 'Où déposer : un dossier existant, ou un nouveau nom (il sera créé).',
                              'en': 'Where to upload: an existing folder, or a new name (it will be created).'},
    'pt_depot_tableau': {'fr': 'Tableau', 'en': 'Table'},
    'pt_depot_tableau_aide': {'fr': 'Tableau où ajouter votre ligne (lisez-le d’abord dans l’onglet Mesures).',
                              'en': 'Table where your row is added (read it first in the Measurements tab).'},
    'pt_depot_sans_tableau': {'fr': '(pas de ligne de tableau)', 'en': '(no table row)'},
    'pt_depot_preparer': {'fr': 'Préparer le dépôt…', 'en': 'Prepare the upload…'},
    'pt_depot_preparer_aide': {'fr': 'Calculer les noms libres et la ligne, puis montrer exactement ce qui sera envoyé '
                                     'avant tout envoi.',
                               'en': 'Work out the free names and the row, then show exactly what will be sent before '
                                     'anything is sent.'},
    'pt_depot_lire_entete': {'fr': 'Remplir d’après l’en-tête FITS', 'en': 'Fill from the FITS header'},
    'pt_depot_lire_entete_aide': {'fr': 'Lieu et heure (milieu de pose, TU) lus dans l’en-tête de votre premier FITS.',
                                  'en': 'Place and time (mid-exposure, UT) read from the header of your first FITS.'},
    'pt_depot_entete_lu': {'fr': 'Champs remplis d’après l’en-tête : vérifiez-les.', 'en': 'Fields filled from the '
                                                                                         'header: check them.'},
    'pt_depot_pas_fits': {'fr': 'Aucun FITS dans la liste.', 'en': 'No FITS in the list.'},
    'pt_depot_rien': {'fr': 'Rien à déposer : ajoutez des fichiers ou choisissez un tableau.',
                      'en': 'Nothing to upload: add files or choose a table.'},
    'pt_depot_incomplet': {'fr': 'Pour une ligne de tableau : date et heure (UTC), latitude et longitude au moins.',
                           'en': 'For a table row: date and time (UTC), latitude and longitude at least.'},
    'pt_depot_preparation': {'fr': 'Préparation du dépôt…', 'en': 'Preparing the upload…'},
    'pt_depot_confirmer_intro': {'fr': 'Voici EXACTEMENT ce qui sera envoyé au partage « {partage} » :',
                                 'en': 'Here is EXACTLY what will be sent to the share “{partage}”:'},
    'pt_depot_confirmer_fichiers': {'fr': '{n} fichier(s), {o} :', 'en': '{n} file(s), {o}:'},
    'pt_depot_confirmer_ligne': {'fr': 'Une ligne ajoutée au tableau {tableau} (feuille « {feuille} ») :',
                                 'en': 'One row added to the table {tableau} (sheet “{feuille}”):'},
    'pt_depot_confirmer_secours': {'fr': 'Si le tableau change entre-temps (trois essais), la ligne sera déposée à côté, '
                                         'dans {csv}.',
                                   'en': 'If the table changes meanwhile (three attempts), the row will be uploaded '
                                         'beside it, in {csv}.'},
    'pt_depot_confirmer_regles': {'fr': 'Aucun fichier existant n’est remplacé, renommé ni supprimé ; une copie du '
                                        'tableau tel qu’il était est gardée sur votre ordinateur.',
                                  'en': 'No existing file is replaced, renamed or deleted; a copy of the table as it '
                                        'was is kept on your computer.'},
    'pt_depot_confirmer_aide': {'fr': 'Relisez : seul ce qui est listé partira.', 'en': 'Read it again: only what is '
                                                                                      'listed will leave.'},
    'pt_depot_envoyer': {'fr': 'Envoyer', 'en': 'Send'},
    'pt_depot_annule': {'fr': 'Dépôt annulé : rien n’a été envoyé.', 'en': 'Upload cancelled: nothing was sent.'},
    'pt_depot_envoi': {'fr': 'Envoi en cours…', 'en': 'Sending…'},
    'pt_depot_echec': {'fr': 'Échec du dépôt : {erreur}', 'en': 'Upload failed: {erreur}'},
    'pt_depot_ok_fichiers': {'fr': '{n} fichier(s) déposé(s).', 'en': '{n} file(s) uploaded.'},
    'pt_depot_ok_ligne': {'fr': 'Ligne {ligne} ajoutée au tableau (copie de l’ancienne version : {sauvegarde}).',
                          'en': 'Row {ligne} added to the table (copy of the previous version: {sauvegarde}).'},
    'pt_depot_ok_csv': {'fr': 'Le tableau changeait sans cesse : ligne déposée à côté, dans {csv} (copie du tableau : '
                              '{sauvegarde}).',
                        'en': 'The table kept changing: row uploaded beside it, in {csv} (copy of the table: '
                              '{sauvegarde}).'},
    'pt_depot_etat_aide': {'fr': 'Où en est le dépôt.', 'en': 'Upload status.'},
    'pt_j_fichier': {'fr': 'Déposé : {chemin}', 'en': 'Uploaded: {chemin}'},
    'pt_j_ligne': {'fr': 'Ligne {ligne} ajoutée à {chemin}', 'en': 'Row {ligne} added to {chemin}'},
    'pt_j_conflit': {'fr': 'Conflit sur {chemin} (essai {essai}) : relecture', 'en': 'Conflict on {chemin} (attempt '
                                                                                     '{essai}): reading again'},
    'pt_j_csv': {'fr': 'Ligne déposée dans {chemin}', 'en': 'Row uploaded to {chemin}'},
    # ------------------------------------------------------------ ligne de commande
    'pt_meta_nom': {'fr': 'NOM', 'en': 'NAME'},
    'pt_meta_lien': {'fr': 'LIEN', 'en': 'LINK'},
    'pt_meta_chemin': {'fr': 'CHEMIN', 'en': 'PATH'},
    'pt_meta_mdp': {'fr': 'MOT_DE_PASSE', 'en': 'PASSWORD'},
    'pt_meta_valeur': {'fr': 'RÔLE=VALEUR', 'en': 'ROLE=VALUE'},
    'pt_cli_ajouter': {'fr': 'ajouter un partage (lien vérifié, droits affichés)', 'en': 'add a share (link checked, '
                                                                                         'rights shown)'},
    'pt_cli_ajouter_desc': {'fr': 'Vérifie le lien de partage, affiche les droits (avertit si la suppression est '
                                  'permise) et le mémorise sous un nom libre.',
                            'en': 'Checks the share link, shows the rights (warns if deletion is allowed) and remembers '
                                  'it under a free name.'},
    'pt_cli_nom': {'fr': 'nom donné au partage', 'en': 'name given to the share'},
    'pt_cli_lien': {'fr': 'lien de partage (https://…/s/…) ou adresse WebDAV', 'en': 'share link (https://…/s/…) or '
                                                                                   'WebDAV address'},
    'pt_cli_mdp': {'fr': 'mot de passe du partage, s’il en a un', 'en': 'share password, if any'},
    'pt_cli_liste': {'fr': 'partages mémorisés', 'en': 'remembered shares'},
    'pt_cli_oublier': {'fr': 'oublier un partage (rien n’est touché sur le serveur)', 'en': 'forget a share (nothing '
                                                                                          'is touched on the server)'},
    'pt_cli_explorer': {'fr': 'structure du partage (dossiers, séries, tableaux, nouveautés)',
                        'en': 'share structure (folders, series, tables, what is new)'},
    'pt_cli_explorer_desc': {'fr': 'Lit toute l’arborescence et dit ce qui a été reconnu.', 'en': 'Reads the whole tree '
                                                                                              'and states what was '
                                                                                              'recognised.'},
    'pt_cli_fichiers': {'fr': 'lister aussi chaque fichier', 'en': 'list each file as well'},
    'pt_cli_vus': {'fr': 'marquer le contenu actuel comme vu', 'en': 'mark the current content as seen'},
    'pt_cli_tableau': {'fr': 'lire et contrôler les tableaux de mesures', 'en': 'read and check the measurement tables'},
    'pt_cli_tableau_desc': {'fr': 'Normalise chaque ligne et signale les anomalies (jamais de modification).',
                            'en': 'Normalises each row and reports anomalies (never changes anything).'},
    'pt_cli_chemin_tableau': {'fr': 'tableau à lire (tous par défaut)', 'en': 'table to read (all by default)'},
    'pt_cli_avec_entetes': {'fr': 'lire d’abord les en-têtes FITS (lieux et heures, contrôles plus sûrs)',
                            'en': 'read the FITS headers first (places and times, safer checks)'},
    'pt_cli_entetes': {'fr': 'lire les en-têtes des FITS (lieu, heure TU, objet)', 'en': 'read the FITS headers (place, '
                                                                                       'UT time, object)'},
    'pt_cli_dossier': {'fr': 'dossier du partage (tout par défaut)', 'en': 'share folder (everything by default)'},
    'pt_cli_paires': {'fr': 'paires simultanées (même cible, deux observateurs)', 'en': 'simultaneous pairs (same '
                                                                                      'target, two observers)'},
    'pt_cli_paires_desc': {'fr': 'Cherche les prises d’une même cible par deux observateurs éloignés, presque au même '
                                 'instant.',
                           'en': 'Looks for shots of the same target by two distant observers, at almost the same '
                                 'time.'},
    'pt_cli_seuil_iss': {'fr': 'écart maximal pour l’ISS (s)', 'en': 'maximum difference for the ISS (s)'},
    'pt_cli_seuil_lune': {'fr': 'écart maximal pour la Lune (s)', 'en': 'maximum difference for the Moon (s)'},
    'pt_cli_base': {'fr': 'base minimale (km)', 'en': 'minimum baseline (km)'},
    'pt_cli_sans_corrections': {'fr': 'ne pas appliquer les corrections proposées', 'en': 'do not apply the proposed '
                                                                                         'corrections'},
    'pt_cli_telecharger': {'fr': 'télécharger des fichiers ou dossiers du partage', 'en': 'download files or folders '
                                                                                        'of the share'},
    'pt_cli_telecharger_desc': {'fr': 'Même moteur que la Banque OHP ; FITS préparés en XISF ou FITS ; rangement par '
                                      'date, cible et observateur.',
                                'en': 'Same engine as the OHP image bank; FITS prepared as XISF or FITS; sorted by date, '
                                      'target and observer.'},
    'pt_cli_chemins': {'fr': 'chemins dans le partage (fichiers ou dossiers)', 'en': 'paths in the share (files or '
                                                                                   'folders)'},
    'pt_cli_sortie': {'fr': 'dossier de téléchargement', 'en': 'download folder'},
    'pt_cli_format': {'fr': 'format des FITS préparés', 'en': 'format of the prepared FITS'},
    'pt_cli_astrometrie': {'fr': 'solution astrométrique si l’en-tête n’en a pas', 'en': 'astrometric solution when '
                                                                                         'the header has none'},
    'pt_cli_en_ligne': {'fr': 'accepter l’envoi des images sans solution à nova.astrometry.net (clé d’API des '
                              'Préférences)',
                        'en': 'agree to send the images without a solution to nova.astrometry.net (API key from the '
                              'Preferences)'},
    'pt_cli_sans_originaux': {'fr': 'ne pas garder les FITS d’origine', 'en': 'do not keep the original FITS'},
    'pt_cli_fini': {'fr': 'reçu : {chemin}', 'en': 'received: {chemin}'},
    'pt_cli_mesurer': {'fr': 'mesurer la Lune ou l’ISS sur des images', 'en': 'measure the Moon or the ISS on images'},
    'pt_cli_mesurer_desc': {'fr': 'Centre du disque lunaire (ou trait de l’ISS) et sa position (α, δ) d’après la '
                                  'solution astrométrique de l’image.',
                            'en': 'Centre of the lunar disc (or ISS trail) and its position (α, δ) from the astrometric '
                                  'solution of the image.'},
    'pt_cli_images': {'fr': 'images (FITS avec solution astrométrique)', 'en': 'images (FITS with an astrometric '
                                                                               'solution)'},
    'pt_cli_cible': {'fr': 'cible mesurée', 'en': 'measured target'},
    'pt_cli_mesure': {'fr': '{fichier} : centre ({x}, {y}) px → α = {ra}°, δ = {dec}° ; milieu de pose {t}',
                      'en': '{fichier}: centre ({x}, {y}) px → α = {ra}°, δ = {dec}°; mid-exposure {t}'},
    'pt_cli_calculer': {'fr': 'calcul de parallaxe d’après un fichier de visées (JSON)', 'en': 'parallax calculation '
                                                                                             'from a sightings file '
                                                                                             '(JSON)'},
    'pt_cli_calculer_desc': {'fr': 'Fichier JSON : {"cible": "lune"|"iss", "methode": "deux"|"diurne"|"vitesse"|'
                                   '"orbite", "visees": [{"nom", "lat", "lon", "alt_m", "points": [{"instant": '
                                   '"2026-10-21T04:33:44Z", "ra": 96.2, "dec": 23.7}]}], "tle": [ligne 1, ligne 2]}.',
                             'en': 'JSON file: {"cible": "lune"|"iss", "methode": "deux"|"diurne"|"vitesse"|"orbite", '
                                   '"visees": [{"nom", "lat", "lon", "alt_m", "points": [{"instant": '
                                   '"2026-10-21T04:33:44Z", "ra": 96.2, "dec": 23.7}]}], "tle": [line 1, line 2]}.'},
    'pt_cli_fichier_visees': {'fr': 'fichier JSON des visées', 'en': 'JSON sightings file'},
    'pt_cli_html': {'fr': 'écrire aussi le rapport HTML', 'en': 'also write the HTML report'},
    'pt_cli_pdf': {'fr': 'écrire aussi le rapport PDF', 'en': 'also write the PDF report'},
    'pt_cli_deposer': {'fr': 'déposer sa mesure (fichiers et ligne du tableau)', 'en': 'upload one’s measurement (files '
                                                                                     'and table row)'},
    'pt_cli_deposer_desc': {'fr': 'Sans --oui, montre seulement ce qui serait envoyé. Jamais d’écrasement : noms libres, '
                                  'dépôts conditionnels, copie locale du tableau.',
                            'en': 'Without --yes, only shows what would be sent. Never overwrites: free names, '
                                  'conditional uploads, local copy of the table.'},
    'pt_cli_fichiers_depot': {'fr': 'fichiers à déposer', 'en': 'files to upload'},
    'pt_cli_dossier_depot': {'fr': 'dossier du partage où déposer', 'en': 'share folder to upload to'},
    'pt_cli_tableau_depot': {'fr': 'tableau où ajouter la ligne', 'en': 'table to add the row to'},
    'pt_cli_valeur': {'fr': 'valeur de la ligne : auteur=…, cible=…, date=…, latitude=…, longitude=…, altitude=…',
                      'en': 'row value: auteur=…, cible=…, date=…, latitude=…, longitude=…, altitude=…'},
    'pt_cli_oui': {'fr': 'envoyer vraiment', 'en': 'really send'},
    'pt_cli_plan': {'fr': 'Dépôt prévu dans « {partage} » :', 'en': 'Planned upload to “{partage}”:'},
    'pt_cli_sans_oui': {'fr': 'Rien n’a été envoyé : ajoutez --oui pour envoyer.', 'en': 'Nothing was sent: add --yes '
                                                                                         'to send.'},
    'pt_cli_inconnu': {'fr': 'Partage inconnu : {nom} (voir « coupole partages liste »).',
                       'en': 'Unknown share: {nom} (see “coupole partages list”).'},
    'pt_cli_un_tableau': {'fr': 'tableau : {chemin}', 'en': 'table: {chemin}'},
    'pt_cli_de440': {'fr': 'télécharger l’éphéméride JPL DE440 (de440s.bsp, 32 Mo)', 'en': 'download the JPL DE440 '
                                                                                        'ephemeris (de440s.bsp, 32 MB)'},
    # ------------------------------------------------------------ aide
    'pt_aide_html': {
        'fr': "<h3>Partages du DU</h3>"
              "<p>Les défis et TP du DU se font souvent dans un <b>dossier partagé</b> (Nextcloud de l'Observatoire) : "
              "l'enseignant, ou un étudiant, crée un lien ; chacun y dépose ses images, ses vidéos et parfois une ligne "
              "dans un tableau. Ce module rassemble tout au même endroit : plusieurs partages mémorisés, leur "
              "structure, les aperçus, les nouveautés, le téléchargement, le contrôle des tableaux, l'analyse et le "
              "dépôt de votre propre mesure.</p>"
              "<h4>Banque OHP ou partage ?</h4><p>La <b>Banque OHP</b> est une archive professionnelle : le service "
              "TAP de l'Observatoire, des métadonnées normalisées, des FITS des télescopes T120 et IRIS. Un "
              "<b>partage</b> est un dossier collaboratif d'étudiants : formats et métadonnées hétérogènes, saisis à la "
              "main — à valider. Coupole devine la structure (dossiers datés, observateurs, séries, tableaux), dit "
              "d'où vient chaque information (en-tête, tableau, nom de fichier) et signale les doutes.</p>"
              "<h4>Les gestes</h4><ol><li><b>Ajouter un partage</b> : collez le lien (« https://…/s/… »), donnez un "
              "nom. Les droits du lien sont affichés ; si le lien permet de supprimer, Coupole vous prévient (il ne "
              "le fait jamais).</li><li><b>Choisir</b> à gauche un dossier, une série ou les nouveautés ; aperçu à "
              "droite (FITS, JPEG, PNG, TIFF, première image d'une vidéo SER ou AVI).</li><li><b>Télécharger</b> "
              "(bouton bleu, clic droit, double-clic) ou passer à l'onglet <b>Analyse</b>.</li></ol>"
              "<h4>Mesures</h4><p>Les tableaux (xlsx, csv) sont lus sans être modifiés : formats normalisés "
              "(« 2,45° », « 48°47′05″ », dates d'Excel ou américaines), contrôles ligne par ligne (latitude et "
              "longitude inversées, heure locale au lieu du TU, champs manquants), avec la preuve quand il y en a une "
              "(en-tête du fichier, position de la Lune). Les corrections proposées servent aux calculs si vous le "
              "voulez, jamais au tableau d'origine.</p>"
              "<h4>Déposer</h4><p>Uniquement sur votre action, après une confirmation qui liste exactement ce qui "
              "part. Noms libres (« _2 »), dépôts conditionnels (le serveur refuse s'il y a eu un changement), copie "
              "locale du tableau avant l'ajout de votre ligne, et, en cas de conflit répété, un petit fichier "
              "« ligne_….csv » à côté. Jamais de suppression, de renommage ni de déplacement.</p>"
              "<p>Le lien d'un partage est un secret partagé : il n'est gardé que sur votre ordinateur et n'apparaît "
              "dans aucun rapport.</p>",
        'en': "<h3>DU shared folders</h3>"
              "<p>DU challenges and practicals often happen in a <b>shared folder</b> (the Observatory's Nextcloud): "
              "the teacher, or a student, creates a link; everyone uploads images, videos and sometimes a row to a "
              "table. This module gathers everything in one place: several remembered shares, their structure, "
              "previews, what is new, download, table checks, analysis and upload of your own measurement.</p>"
              "<h4>OHP image bank or share?</h4><p>The <b>OHP image bank</b> is a professional archive: the "
              "Observatory's TAP service, standardised metadata, FITS from the T120 and IRIS telescopes. A "
              "<b>share</b> is a collaborative folder of students: heterogeneous formats and metadata typed by hand — "
              "to be validated. Coupole guesses the structure (dated folders, observers, series, tables), states where "
              "each piece of information comes from (header, table, file name) and reports doubts.</p>"
              "<h4>Steps</h4><ol><li><b>Add a share</b>: paste the link (“https://…/s/…”), give a name. The link "
              "rights are shown; if the link allows deletion, Coupole warns you (it never deletes).</li><li><b>Choose"
              "</b> a folder, a series or what is new on the left; preview on the right (FITS, JPEG, PNG, TIFF, first "
              "frame of a SER or AVI video).</li><li><b>Download</b> (blue button, right click, double click) or go "
              "to the <b>Analysis</b> tab.</li></ol>"
              "<h4>Measurements</h4><p>Tables (xlsx, csv) are read without being changed: formats normalised "
              "(“2,45°”, “48°47′05″”, Excel or US dates), row-by-row checks (swapped latitude and longitude, local "
              "time instead of UT, missing fields), with evidence when there is some (file header, position of the "
              "Moon). The proposed corrections are used for calculations if you wish, never written to the original "
              "table.</p>"
              "<h4>Upload</h4><p>Only on your action, after a confirmation listing exactly what leaves. Free names "
              "(“_2”), conditional uploads (the server refuses if something changed), local copy of the table before "
              "adding your row, and, after repeated conflicts, a small “ligne_….csv” file beside it. Never any "
              "deletion, renaming or moving.</p>"
              "<p>A share link is a shared secret: it is kept on your computer only and appears in no report.</p>"},
    # ============================================================ outil Parallaxe
    'pc_outil_nom': {'fr': 'Parallaxe (Lune, ISS)', 'en': 'Parallax (Moon, ISS)'},
    'pc_outil_description': {'fr': 'Paires simultanées, distance de la Lune, altitude de l’ISS, rapport.',
                             'en': 'Simultaneous pairs, distance of the Moon, altitude of the ISS, report.'},
    'pc_raison_nom': {'fr': '« parallaxe » dans les noms', 'en': '“parallax” in the names'},
    'pc_raison_cibles': {'fr': 'images de la Lune ou de l’ISS', 'en': 'images of the Moon or the ISS'},
    'pc_raison_tableau': {'fr': 'tableau de localisations', 'en': 'table of locations'},
    'pc_raison_observateurs': {'fr': 'plusieurs observateurs', 'en': 'several observers'},
    'pc_intro': {'fr': 'Deux observateurs éloignés photographient la même cible au même instant : la cible ne se '
                       'projette pas au même endroit parmi les étoiles. Cet écart (la parallaxe) et la distance entre '
                       'les deux lieux (la base) donnent la distance de la Lune ou l’altitude de l’ISS.',
                 'en': 'Two distant observers photograph the same target at the same time: the target does not project '
                       'onto the same place among the stars. This offset (the parallax) and the distance between the two '
                       'sites (the baseline) give the distance of the Moon or the altitude of the ISS.'},
    'pc_seuil_iss': {'fr': 'ISS ≤', 'en': 'ISS ≤'},
    'pc_seuil_iss_aide': {'fr': 'Écart d’heure maximal entre deux prises de l’ISS (elle parcourt 7,7 km/s ; le décalage '
                                'se corrige le long du trait).',
                          'en': 'Maximum time difference between two ISS shots (it moves 7.7 km/s; the offset is '
                                'corrected along the trail).'},
    'pc_seuil_lune': {'fr': 'Lune ≤', 'en': 'Moon ≤'},
    'pc_seuil_lune_aide': {'fr': 'Écart d’heure maximal entre deux prises de la Lune (≈ 33″ de mouvement par minute, '
                                 'corrigé par l’éphéméride).',
                           'en': 'Maximum time difference between two Moon shots (≈ 33″ of motion per minute, corrected '
                                 'by the ephemeris).'},
    'pc_base_min': {'fr': 'base ≥', 'en': 'baseline ≥'},
    'pc_base_min_aide': {'fr': 'Distance minimale entre les deux lieux : la parallaxe de la Lune ne vaut qu’≈ 1′ par '
                               '100 km.',
                         'en': 'Minimum distance between the two sites: the Moon parallax is only ≈ 1′ per 100 km.'},
    'pc_unite_s': {'fr': 's', 'en': 's'},
    'pc_unite_km': {'fr': 'km', 'en': 'km'},
    'pc_unite_m': {'fr': 'm', 'en': 'm'},
    'pc_unite_arcsec': {'fr': '″', 'en': '″'},
    'pc_chercher': {'fr': 'Chercher les paires', 'en': 'Find pairs'},
    'pc_chercher_aide': {'fr': 'Paires d’après les tableaux de mesures (corrections comprises si cochées) et les séries '
                               'de fichiers (heures des en-têtes lus, sinon des noms).',
                         'en': 'Pairs from the measurement tables (corrections included if ticked) and the file series '
                               '(times from the headers read, otherwise from the names).'},
    'pc_lire_entetes': {'fr': 'Lire les en-têtes FITS', 'en': 'Read the FITS headers'},
    'pc_lire_entetes_aide': {'fr': 'Lieux et heures TU exacts de tous les FITS (début des fichiers seulement).',
                             'en': 'Exact places and UT times of all FITS (beginning of the files only).'},
    'pc_paires_aide': {'fr': 'Paires trouvées, de la plus simultanée à la moins simultanée. Choisir une paire remplit '
                             'les visées A et B.',
                       'en': 'Pairs found, from the most to the least simultaneous. Choosing a pair fills sightings A '
                             'and B.'},
    'pc_paires_vide': {'fr': 'Aucune paire : il faut deux observateurs éloignés, la même cible, presque au même '
                             'instant (lisez le tableau des mesures et les en-têtes).',
                       'en': 'No pair: two distant observers, the same target, at almost the same time are needed (read '
                             'the measurement table and the headers).'},
    'pc_paires_trouvees': {'fr': '{n} paire(s) simultanée(s), dont {s} à la seconde près.',
                           'en': '{n} simultaneous pair(s), {s} of them within one second.'},
    'pc_p_cible': {'fr': 'Cible', 'en': 'Target'},
    'pc_p_a': {'fr': 'Observateur A', 'en': 'Observer A'},
    'pc_p_b': {'fr': 'Observateur B', 'en': 'Observer B'},
    'pc_p_ecart': {'fr': 'Écart (s)', 'en': 'Difference (s)'},
    'pc_p_base': {'fr': 'Base (km)', 'en': 'Baseline (km)'},
    'pc_p_source': {'fr': 'Source', 'en': 'Source'},
    'pc_p_remarques': {'fr': 'Remarques', 'en': 'Remarks'},
    'pc_p_sans_lieu': {'fr': 'lieu inconnu', 'en': 'unknown place'},
    'pc_p_heure_nom': {'fr': 'heure tirée d’un nom de fichier (à confirmer)', 'en': 'time taken from a file name (to '
                                                                                  'be confirmed)'},
    'pc_source_tableau': {'fr': 'tableau', 'en': 'table'},
    'pc_source_entete': {'fr': 'en-tête', 'en': 'header'},
    'pc_source_nom': {'fr': 'nom', 'en': 'name'},
    'pc_source_fichiers': {'fr': 'Fichiers : {f}', 'en': 'Files: {f}'},
    'pc_paire_prise': {'fr': 'Paire reprise dans les visées A et B : mesurez maintenant la cible sur les images (clic '
                             'droit sur un fichier > Mesurer pour A / B) ou saisissez α et δ.',
                       'en': 'Pair copied into sightings A and B: now measure the target on the images (right click on '
                             'a file > Measure for A / B) or type α and δ.'},
    'pc_cible': {'fr': 'Cible', 'en': 'Target'},
    'pc_cible_aide': {'fr': 'Lune : distance ; ISS : altitude.', 'en': 'Moon: distance; ISS: altitude.'},
    'pc_methode': {'fr': 'Méthode', 'en': 'Method'},
    'pc_methode_aide': {'fr': 'Deux observateurs (la méthode du défi) ; ou un seul : parallaxe diurne de la Lune '
                              '(plusieurs heures de mesures), vitesse angulaire ou orbite circulaire de l’ISS.',
                        'en': 'Two observers (the challenge method); or one: diurnal parallax of the Moon (several hours '
                              'of measurements), angular speed or circular orbit of the ISS.'},
    'pc_m_deux': {'fr': 'Deux observateurs', 'en': 'Two observers'},
    'pc_m_diurne': {'fr': 'Un observateur : parallaxe diurne (Lune)', 'en': 'One observer: diurnal parallax (Moon)'},
    'pc_m_vitesse': {'fr': 'Un observateur : vitesse angulaire (ISS)', 'en': 'One observer: angular speed (ISS)'},
    'pc_m_orbite': {'fr': 'Un observateur : orbite circulaire (ISS)', 'en': 'One observer: circular orbit (ISS)'},
    'pc_eph_aide': {'fr': 'Éphéméride de comparaison : JPL DE440 (si le fichier de440s.bsp est présent), sinon '
                          'l’approximation de Meeus (≈ 6 km d’écart quadratique moyen).',
                    'en': 'Comparison ephemeris: JPL DE440 (if the de440s.bsp file is present), otherwise the Meeus '
                          'approximation (≈ 6 km RMS).'},
    'pc_eph_etat_de440': {'fr': 'Éphéméride : DE440', 'en': 'Ephemeris: DE440'},
    'pc_eph_etat_meeus': {'fr': 'Éphéméride : Meeus (≈ 6 km)', 'en': 'Ephemeris: Meeus (≈ 6 km)'},
    'pc_eph_de440': {'fr': 'JPL DE440', 'en': 'JPL DE440'},
    'pc_eph_meeus': {'fr': 'Meeus (ERFA moon98)', 'en': 'Meeus (ERFA moon98)'},
    'pc_de440': {'fr': 'Télécharger DE440 (32 Mo)', 'en': 'Download DE440 (32 MB)'},
    'pc_de440_aide': {'fr': 'Éphéméride JPL DE440 (de440s.bsp, 1849–2150), téléchargée une fois dans le cache.',
                      'en': 'JPL DE440 ephemeris (de440s.bsp, 1849–2150), downloaded once to the cache.'},
    'pc_de440_sans_jplephem': {'fr': 'Le paquet Python « jplephem » est nécessaire pour lire DE440 (pip install '
                                     'jplephem).',
                               'en': 'The “jplephem” Python package is needed to read DE440 (pip install jplephem).'},
    'pc_de440_en_cours': {'fr': 'Téléchargement de DE440…', 'en': 'Downloading DE440…'},
    'pc_de440_ok': {'fr': 'Éphéméride DE440 prête.', 'en': 'DE440 ephemeris ready.'},
    'pc_de440_echec': {'fr': 'DE440 non téléchargée : {erreur}', 'en': 'DE440 not downloaded: {erreur}'},
    'pc_visee': {'fr': 'Visée {l}', 'en': 'Sighting {l}'},
    'pc_nom': {'fr': 'Observateur', 'en': 'Observer'},
    'pc_nom_aide': {'fr': 'Nom de l’observateur (pour le rapport).', 'en': 'Observer name (for the report).'},
    'pc_lat': {'fr': 'Latitude (°)', 'en': 'Latitude (°)'},
    'pc_lat_aide': {'fr': 'Nord positif ; « 48,785 », « 48°47′05″ N » acceptés.', 'en': 'North positive; “48.785”, '
                                                                                      '“48°47′05″ N” accepted.'},
    'pc_lat_indice': {'fr': '48,785', 'en': '48.785'},
    'pc_lon': {'fr': 'Longitude (°)', 'en': 'Longitude (°)'},
    'pc_lon_aide': {'fr': 'Est positif ; « 2,45 », « 2°27′ E » acceptés.', 'en': 'East positive; “2.45”, “2°27′ E” '
                                                                                 'accepted.'},
    'pc_lon_indice': {'fr': '2,45', 'en': '2.45'},
    'pc_alt': {'fr': 'Altitude (m)', 'en': 'Elevation (m)'},
    'pc_alt_aide': {'fr': 'Altitude du lieu (m) ; 100 m d’erreur ne change presque rien.', 'en': 'Site elevation (m); '
                                                                                               'a 100 m error changes '
                                                                                               'almost nothing.'},
    'pc_mode': {'fr': 'Mesure', 'en': 'Measurement'},
    'pc_mode_aide': {'fr': 'α, δ lus sur la solution astrométrique (le mieux : la réfraction est la même pour les '
                           'étoiles) ; ou hauteur et azimut, mesurés sur le ciel (réfraction retirée) ou lus dans '
                           'Stellarium sans atmosphère.',
                     'en': 'α, δ read from the astrometric solution (best: refraction is the same for the stars); or '
                           'altitude and azimuth, measured on the sky (refraction removed) or read in Stellarium '
                           'without atmosphere.'},
    'pc_mode_radec': {'fr': 'α, δ (astrométrie)', 'en': 'α, δ (astrometry)'},
    'pc_mode_altaz_mesuree': {'fr': 'hauteur, azimut mesurés', 'en': 'measured altitude, azimuth'},
    'pc_mode_altaz_vraie': {'fr': 'hauteur, azimut sans atmosphère', 'en': 'altitude, azimuth without atmosphere'},
    'pc_points_aide': {'fr': 'Un point (Lune, ou ISS au même instant), deux points (extrémités d’un trait : début et fin '
                             'de pose) ou une série de points datés. Instants en UTC ; α en degrés ou « 0h41m50s ».',
                       'en': 'One point (Moon, or ISS at the same time), two points (trail ends: start and end of the '
                             'exposure) or a series of dated points. Times in UTC; α in degrees or “0h41m50s”.'},
    'pc_col_instant': {'fr': 'Instant (UTC)', 'en': 'Time (UTC)'},
    'pc_col_ra': {'fr': 'α (°)', 'en': 'α (°)'},
    'pc_col_dec': {'fr': 'δ (°)', 'en': 'δ (°)'},
    'pc_col_h': {'fr': 'Hauteur (°)', 'en': 'Altitude (°)'},
    'pc_col_az': {'fr': 'Azimut (°)', 'en': 'Azimuth (°)'},
    'pc_point_ajouter': {'fr': 'Ajouter un point', 'en': 'Add a point'},
    'pc_point_ajouter_aide': {'fr': 'Nouvelle ligne à remplir.', 'en': 'New row to fill.'},
    'pc_point_retirer': {'fr': 'Retirer', 'en': 'Remove'},
    'pc_point_retirer_aide': {'fr': 'Retirer le point choisi.', 'en': 'Remove the chosen point.'},
    'pc_point_inverser': {'fr': 'Inverser le sens', 'en': 'Reverse the direction'},
    'pc_point_inverser_aide': {'fr': 'Le début et la fin d’un trait se ressemblent : si le sens supposé est faux, '
                                     'inversez les instants.',
                               'en': 'The start and end of a trail look alike: if the assumed direction is wrong, '
                                     'reverse the times.'},
    'pc_sigma': {'fr': 'Incertitude de direction', 'en': 'Direction uncertainty'},
    'pc_sigma_aide': {'fr': 'Centrage et astrométrie (secondes d’arc) ; remplie d’après la mesure sur l’image.',
                      'en': 'Centring and astrometry (arcseconds); filled from the measurement on the image.'},
    'pc_sigma_t': {'fr': 'Incertitude de l’heure', 'en': 'Time uncertainty'},
    'pc_sigma_t_aide': {'fr': 'Horloge de l’appareil (s) : 0,5 s pour une heure réglée par GPS ou Internet.',
                        'en': 'Device clock (s): 0.5 s for a time set by GPS or the Internet.'},
    'pc_sigma_pos': {'fr': 'Incertitude du lieu', 'en': 'Site uncertainty'},
    'pc_sigma_pos_aide': {'fr': 'Position du lieu (m).', 'en': 'Site position (m).'},
    'pc_horloge': {'fr': 'Décalage d’horloge connu', 'en': 'Known clock offset'},
    'pc_horloge_aide': {'fr': 'Secondes à ajouter aux heures de cet observateur (horloge en retard : positif).',
                        'en': 'Seconds added to this observer’s times (clock running late: positive).'},
    'pc_etoile': {'fr': 'Étoile de référence (α δ, facultatif)', 'en': 'Reference star (α δ, optional)'},
    'pc_etoile_aide': {'fr': 'Pour comparer à la méthode du sujet (écart des séparations Lune–étoile).',
                       'en': 'To compare with the method of the assignment (difference of Moon–star separations).'},
    'pc_etoile_indice': {'fr': '56.871 24.105', 'en': '56.871 24.105'},
    'pc_tle': {'fr': 'TLE (ISS, facultatif)', 'en': 'TLE (ISS, optional)'},
    'pc_tle_aide': {'fr': 'Deux lignes d’éléments orbitaux (CelesTrak) proches de la date : altitude prédite pour '
                          'comparaison (paquet sgp4 nécessaire).',
                    'en': 'Two lines of orbital elements (CelesTrak) close to the date: predicted altitude for '
                          'comparison (sgp4 package needed).'},
    'pc_tle_charger': {'fr': 'Charger…', 'en': 'Load…'},
    'pc_tle_charger_aide': {'fr': 'Lire un fichier TLE (texte de CelesTrak).', 'en': 'Read a TLE file (CelesTrak '
                                                                                     'text).'},
    'pc_tle_sans_sgp4': {'fr': 'comparaison impossible : paquet sgp4 absent', 'en': 'comparison impossible: sgp4 '
                                                                                   'package missing'},
    'pc_tle_erreur': {'fr': 'TLE inutilisable à cette date', 'en': 'TLE unusable at this date'},
    'pc_calculer': {'fr': 'Calculer', 'en': 'Compute'},
    'pc_calculer_aide': {'fr': 'Triangulation, comparaison à l’éphéméride (ou au TLE), budget d’erreur.',
                         'en': 'Triangulation, comparison with the ephemeris (or the TLE), error budget.'},
    'pc_resultats_aide': {'fr': 'Résultats du calcul.', 'en': 'Calculation results.'},
    'pc_rapport_html': {'fr': 'Rapport HTML…', 'en': 'HTML report…'},
    'pc_rapport_html_aide': {'fr': 'Rapport autonome (schéma, valeurs, incertitudes) à ouvrir dans un navigateur.',
                             'en': 'Self-contained report (diagram, values, uncertainties) to open in a browser.'},
    'pc_rapport_pdf': {'fr': 'Rapport PDF…', 'en': 'PDF report…'},
    'pc_rapport_pdf_aide': {'fr': 'Même rapport, en PDF A4.', 'en': 'Same report, as A4 PDF.'},
    'pc_rapport_ecrit': {'fr': 'Rapport écrit : {chemin}', 'en': 'Report written: {chemin}'},
    'pc_menu_mesurer': {'fr': 'Mesurer pour la visée {l} ({n} image(s))', 'en': 'Measure for sighting {l} ({n} '
                                                                               'image(s))'},
    'pc_menu_mesurer_aide': {'fr': 'Lune : centre du disque ; ISS : objet mobile d’une série, ou trait d’une pose. '
                                   'Position (α, δ) d’après la solution astrométrique ; lieu et heure d’après '
                                   'l’en-tête.',
                             'en': 'Moon: centre of the disc; ISS: moving object of a series, or trail of an exposure. '
                                   'Position (α, δ) from the astrometric solution; place and time from the header.'},
    'pc_mesure_en_cours': {'fr': 'Mesure de {n} image(s)…', 'en': 'Measuring {n} image(s)…'},
    'pc_mesure_ok': {'fr': '{n} point(s) mesuré(s).', 'en': '{n} point(s) measured.'},
    'pc_mesure_echec': {'fr': 'Mesure impossible : {erreur}', 'en': 'Measurement impossible: {erreur}'},
    'pc_note_lune': {'fr': '{nom} : centre ({x} ; {y}) px, rayon {r} px, incertitude ≈ {s}″',
                     'en': '{nom}: centre ({x}; {y}) px, radius {r} px, uncertainty ≈ {s}″'},
    'pc_note_sature': {'fr': '{nom} : ATTENTION, Lune saturée ({s} % du disque au maximum) ou disque de taille anormale '
                             '(rapport au rayon attendu {r}) : le centre mesuré est douteux, l\'incertitude a été '
                             'élargie. Préférez une pose plus courte.',
                       'en': '{nom}: WARNING, saturated Moon ({s} % of the disc at maximum) or disc of abnormal size '
                             '(ratio to the expected radius {r}): the measured centre is doubtful, the uncertainty '
                             'has been widened. Prefer a shorter exposure.'},
    'pc_note_trait': {'fr': 'Trait : sens supposé (début = première extrémité) ; « Inverser le sens » si besoin.',
                      'en': 'Trail: assumed direction (start = first end); “Reverse the direction” if needed.'},
    'pc_note_correction': {'fr': 'Ligne {ligne} du tableau : correction appliquée ({champs}).',
                           'en': 'Table row {ligne}: correction applied ({champs}).'},
    'pc_err_lieu': {'fr': 'Visée {nom} : latitude et longitude nécessaires.', 'en': 'Sighting {nom}: latitude and '
                                                                                 'longitude needed.'},
    'pc_err_point_vide': {'fr': 'Visée {nom} : aucun point complet (instant, deux angles).',
                          'en': 'Sighting {nom}: no complete point (time, two angles).'},
    'pc_err_derriere': {'fr': 'Les deux visées ne se croisent pas devant les observateurs : vérifiez les directions '
                              '(α, δ), les lieux et les heures.',
                        'en': 'The two sightings do not cross in front of the observers: check the directions (α, δ), '
                              'the sites and the times.'},
    'pc_err_deux_points': {'fr': 'Visée {nom} : deux points (début et fin de pose) nécessaires.',
                           'en': 'Sighting {nom}: two points (start and end of exposure) needed.'},
    'pc_err_quatre_points': {'fr': 'Visée {nom} : quatre points datés au moins.', 'en': 'Sighting {nom}: at least four '
                                                                                       'dated points.'},
    'pc_err_six_points': {'fr': 'Visée {nom} : six points au moins, répartis sur plusieurs heures.',
                          'en': 'Sighting {nom}: at least six points, spread over several hours.'},
    'pc_err_deux_visees': {'fr': 'Deux visées nécessaires.', 'en': 'Two sightings needed.'},
    'pc_b_direction': {'fr': 'direction mesurée', 'en': 'measured direction'},
    'pc_b_position': {'fr': 'position du lieu', 'en': 'site position'},
    'pc_b_heure': {'fr': 'heure', 'en': 'time'},
    'pc_b_ephemeride': {'fr': 'éphéméride de Meeus (comparaison seulement, ≈ 6 km)', 'en': 'Meeus ephemeris '
                                                                                         '(comparison only, ≈ 6 km)'},
    'pc_res_diurne': {'fr': 'Distance géocentrique : {distance_geo_km} km ± {sigma_km} km ({points} points sur '
                            '{duree_h} h ; résidus {rms_arcsec}″).',
                      'en': 'Geocentric distance: {distance_geo_km} km ± {sigma_km} km ({points} points over {duree_h} '
                            'h; residuals {rms_arcsec}″).'},
    'pc_res_vitesse': {'fr': 'Altitude : {altitude_km} km (vitesse angulaire {omega_deg_s}°/s à {hauteur_deg}° de '
                             'hauteur).',
                       'en': 'Altitude: {altitude_km} km (angular speed {omega_deg_s}°/s at {hauteur_deg}° altitude).'},
    'pc_res_orbite': {'fr': 'Altitude : {altitude_km} km (rayon {rayon_km} km ; {points} visées ; résidus '
                            '{rms_arcsec}″ ; G·M déduit {gm} km³/s²).',
                      'en': 'Altitude: {altitude_km} km (radius {rayon_km} km; {points} sightings; residuals '
                            '{rms_arcsec}″; derived G·M {gm} km³/s²).'},
    'pc_cli_base': {'fr': 'base {b} km', 'en': 'baseline {b} km'},
    # ------------------------------------------------------------ rapport
    'pc_r_langue': {'fr': 'fr', 'en': 'en'},
    'pc_r_titre_lune': {'fr': 'Distance de la Lune par la parallaxe', 'en': 'Distance of the Moon by parallax'},
    'pc_r_titre_iss': {'fr': 'Altitude de l’ISS par la parallaxe', 'en': 'Altitude of the ISS by parallax'},
    'pc_r_genere': {'fr': 'Rapport établi par Coupole le {date}.', 'en': 'Report made by Coupole on {date}.'},
    'pc_r_schema': {'fr': 'Schéma de la mesure', 'en': 'Diagram of the measurement'},
    'pc_r_schema_base': {'fr': 'base {b} km', 'en': 'baseline {b} km'},
    'pc_r_schema_lune': {'fr': 'Lune : {d} km\nparallaxe {p}″', 'en': 'Moon: {d} km\nparallax {p}″'},
    'pc_r_schema_iss': {'fr': 'ISS : {h} km d’altitude\nparallaxe {p}°', 'en': 'ISS: {h} km altitude\nparallax {p}°'},
    'pc_r_schema_echelle': {'fr': 'Schéma qui n’est pas à l’échelle (la Lune est à environ 60 rayons terrestres).',
                            'en': 'Diagram not to scale (the Moon is about 60 Earth radii away).'},
    'pc_r_observateurs': {'fr': 'Observateurs', 'en': 'Observers'},
    'pc_r_lat': {'fr': 'Latitude', 'en': 'Latitude'},
    'pc_r_lon': {'fr': 'Longitude', 'en': 'Longitude'},
    'pc_r_alt': {'fr': 'Altitude', 'en': 'Elevation'},
    'pc_r_resultats': {'fr': 'Résultats', 'en': 'Results'},
    'pc_r_instant': {'fr': 'Instant commun', 'en': 'Common time'},
    'pc_r_dt': {'fr': 'Écart entre les deux prises', 'en': 'Difference between the two shots'},
    'pc_r_base': {'fr': 'Base (corde)', 'en': 'Baseline (chord)'},
    'pc_r_base_perp': {'fr': 'Base vue de la Lune (projetée)', 'en': 'Baseline seen from the Moon (projected)'},
    'pc_r_parallaxe': {'fr': 'Parallaxe mesurée', 'en': 'Measured parallax'},
    'pc_r_distance_geo': {'fr': 'Distance géocentrique de la Lune', 'en': 'Geocentric distance of the Moon'},
    'pc_r_distance_topo': {'fr': 'Distances depuis A et B', 'en': 'Distances from A and B'},
    'pc_r_distance_simple': {'fr': 'Formule simple base projetée / parallaxe', 'en': 'Simple formula projected '
                                                                                    'baseline / parallax'},
    'pc_r_ecart_droites': {'fr': 'Écart entre les deux droites de visée', 'en': 'Gap between the two lines of sight'},
    'pc_r_eph': {'fr': 'Éphéméride ({src})', 'en': 'Ephemeris ({src})'},
    'pc_r_ecart': {'fr': 'Écart mesure − éphéméride', 'en': 'Measurement − ephemeris'},
    'pc_r_parallaxe_eph': {'fr': 'Parallaxe attendue', 'en': 'Expected parallax'},
    'pc_r_ecart_dir': {'fr': 'Écart des directions à l’éphéméride (A ; B)', 'en': 'Direction offsets from the ephemeris '
                                                                                  '(A; B)'},
    'pc_r_hauteurs': {'fr': 'Hauteur / azimut de la cible (A ; B)', 'en': 'Altitude / azimuth of the target (A; B)'},
    'pc_r_refraction': {'fr': 'Réfraction à ces hauteurs (A ; B)', 'en': 'Refraction at these altitudes (A; B)'},
    'pc_r_decalage_temps': {'fr': 'Correction pour l’instant commun (A ; B)', 'en': 'Correction to the common time (A; '
                                                                                    'B)'},
    'pc_r_sujet': {'fr': 'Méthode du sujet (séparations à l’étoile)', 'en': 'Assignment method (separations from the '
                                                                            'star)'},
    'pc_r_angles': {'fr': 'Angles en A et en B', 'en': 'Angles at A and B'},
    'pc_r_distances': {'fr': 'Distances depuis A et B', 'en': 'Distances from A and B'},
    'pc_r_altitude': {'fr': 'Altitude de l’ISS', 'en': 'Altitude of the ISS'},
    'pc_r_sous_point': {'fr': 'Point sous l’ISS', 'en': 'Point below the ISS'},
    'pc_r_formules': {'fr': 'Formules approchées', 'en': 'Approximate formulas'},
    'pc_r_formules_v': {'fr': 'symétrique {s} km au-dessus de la corde ; petits angles {p} km',
                        'en': 'symmetric {s} km above the chord; small angles {p} km'},
    'pc_r_plans': {'fr': 'Méthode des plans (sans horloge commune)', 'en': 'Plane method (no common clock)'},
    'pc_r_horloge': {'fr': 'Décalage d’horloge estimé', 'en': 'Estimated clock offset'},
    'pc_r_horloge_v': {'fr': '{dt} s (B) : altitude {h} km, droites à {e} m', 'en': '{dt} s (B): altitude {h} km, lines '
                                                                                   '{e} m apart'},
    'pc_r_tle': {'fr': 'Prédiction du TLE', 'en': 'TLE prediction'},
    'pc_r_tle_ecart': {'fr': 'écart de position {e} km ; TLE de {a} j', 'en': 'position offset {e} km; TLE {a} d old'},
    'pc_r_budget': {'fr': 'Budget d’erreur', 'en': 'Error budget'},
    'pc_r_source': {'fr': 'Source', 'en': 'Source'},
    'pc_r_observateur': {'fr': 'Observateur', 'en': 'Observer'},
    'pc_r_contribution': {'fr': 'Contribution', 'en': 'Contribution'},
    'pc_r_total': {'fr': 'Total (somme quadratique)', 'en': 'Total (quadratic sum)'},
    'pc_r_methode': {'fr': 'Méthode', 'en': 'Method'},
    'pc_r_methode_lune': {'fr': 'Méthode vectorielle topocentrique : directions (α, δ) du centre de la Lune lues sur la '
                                'solution astrométrique de chaque photo, lieux WGS84 ramenés dans le repère des étoiles '
                                '(rotation de la Terre IAU 2006/2000A), point le plus proche des deux droites. Les '
                                'deux directions sont ramenées à l’instant commun par le mouvement apparent de la Lune. '
                                'La réfraction touche autant la Lune que les étoiles voisines : seule la réfraction '
                                'différentielle reste. L’éphéméride est calculée comme la mesure (temps de lumière '
                                'compris).',
                          'en': 'Topocentric vector method: directions (α, δ) of the Moon centre read from the '
                                'astrometric solution of each photo, WGS84 sites brought into the star frame (Earth '
                                'rotation IAU 2006/2000A), closest point of the two lines. Both directions are brought '
                                'to the common time by the apparent motion of the Moon. Refraction affects the Moon as '
                                'much as the nearby stars: only differential refraction remains. The ephemeris is '
                                'computed like the measurement (light time included).'},
    'pc_r_methode_iss': {'fr': 'Triangulation des deux visées : directions passées dans le repère terrestre à leur '
                               'instant, interpolées le long de chaque trait à l’instant commun (milieu du recouvrement '
                               'des poses), point le plus proche des deux droites, altitude au-dessus de l’ellipsoïde '
                               'WGS84. Contrôles : méthode des plans (sans horloge commune), décalage d’horloge qui '
                               'rend les droites concourantes, prédiction d’un TLE.',
                         'en': 'Triangulation of the two sightings: directions brought into the Earth frame at their '
                               'own time, interpolated along each trail to the common time (middle of the exposure '
                               'overlap), closest point of the two lines, altitude above the WGS84 ellipsoid. Checks: '
                               'plane method (no common clock), clock offset that makes the lines meet, TLE '
                               'prediction.'},
    'pc_r_notes': {'fr': 'Remarques', 'en': 'Remarks'},
    'pc_r_pied': {'fr': 'Coupole — physique d’après le guide « Parallaxe » du DU ; éphéméride et repères : ERFA (IAU), '
                        'JPL DE440 si présente.',
                  'en': 'Coupole — physics after the DU “Parallax” guide; ephemeris and frames: ERFA (IAU), JPL DE440 '
                        'if present.'},
    'pc_aide_html': {
        'fr': "<h3>Outil « Parallaxe (Lune, ISS) »</h3>"
              "<ol><li><b>Chercher les paires</b> : même cible, deux observateurs éloignés (base ≥ 100 km), presque au "
              "même instant (ISS ≤ 5 s, Lune ≤ 60 s). Lisez d'abord le tableau des mesures et les en-têtes FITS "
              "(heures TU exactes).</li>"
              "<li><b>Mesurer</b> : clic droit sur une image > Mesurer pour A ou B. Lune : centre du disque ajusté sur "
              "le limbe (le terminateur est écarté) ; ISS : objet mobile d'une série de poses courtes, ou trait d'une "
              "pose longue. La position (α, δ) vient de la solution astrométrique de l'image (en-tête, ou ASTAP / "
              "astrometry.net installés).</li>"
              "<li><b>Calculer</b>, puis le rapport HTML ou PDF.</li></ol>"
              "<p><b>Lune</b> : méthode vectorielle topocentrique, comparaison à DE440 (ou à Meeus), budget d'erreur "
              "(direction, lieu, heure). <b>ISS</b> : triangulation, correction du décalage d'horloge le long du trait, "
              "méthode des plans, comparaison au TLE. Méthodes à un seul observateur : parallaxe diurne de la Lune "
              "(plusieurs heures), vitesse angulaire ou orbite circulaire de l'ISS.</p>"
              "<p>Ordres de grandeur : la parallaxe de la Lune vaut ≈ 1′ par 100 km de base ; il faut donc mesurer le "
              "centre de la Lune à quelques secondes d'arc près, et les deux heures à quelques secondes près.</p>",
        'en': "<h3>“Parallax (Moon, ISS)” tool</h3>"
              "<ol><li><b>Find pairs</b>: same target, two distant observers (baseline ≥ 100 km), at almost the same "
              "time (ISS ≤ 5 s, Moon ≤ 60 s). Read the measurement table and the FITS headers first (exact UT "
              "times).</li>"
              "<li><b>Measure</b>: right click on an image > Measure for A or B. Moon: centre of the disc fitted on the "
              "limb (the terminator is left out); ISS: moving object of a series of short exposures, or trail of a "
              "long exposure. The position (α, δ) comes from the astrometric solution of the image (header, or "
              "installed ASTAP / astrometry.net).</li>"
              "<li><b>Compute</b>, then the HTML or PDF report.</li></ol>"
              "<p><b>Moon</b>: topocentric vector method, comparison with DE440 (or Meeus), error budget (direction, "
              "site, time). <b>ISS</b>: triangulation, clock offset correction along the trail, plane method, "
              "comparison with the TLE. One-observer methods: diurnal parallax of the Moon (several hours), angular "
              "speed or circular orbit of the ISS.</p>"
              "<p>Orders of magnitude: the Moon parallax is ≈ 1′ per 100 km of baseline; the Moon centre must "
              "therefore be measured to a few arcseconds, and both times to a few seconds.</p>"},
}

for _d, (_fr, _en) in DROITS.items():
    TEXTES['pt_droit_' + _d] = {'fr': _fr, 'en': _en}
for _g, (_fr, _en) in GENRES.items():
    TEXTES['pt_genre_' + _g] = {'fr': _fr, 'en': _en}
for _c, (_fr, _en) in CIBLES.items():
    TEXTES['pt_cible_' + _c] = {'fr': _fr, 'en': _en}
for _c, (_fr, _en, _afr, _aen) in COLONNES.items():
    TEXTES['pt_col_' + _c] = {'fr': _fr, 'en': _en}
    TEXTES['pt_col_%s_aide' % _c] = {'fr': _afr, 'en': _aen}
for _c, (_fr, _en) in COL_MESURES.items():
    TEXTES['pt_m_' + _c] = {'fr': _fr, 'en': _en}
for _r, (_fr, _en, _afr, _aen, _ifr, _ien) in DEPOT.items():
    TEXTES['pt_depot_' + _r] = {'fr': _fr, 'en': _en}
    TEXTES['pt_depot_%s_aide' % _r] = {'fr': _afr, 'en': _aen}
    TEXTES['pt_depot_%s_indice' % _r] = {'fr': _ifr, 'en': _ien}
