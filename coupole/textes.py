"""Textes du cœur de Coupole (FR/EN) : ligne de commande, fenêtre principale, aide, ASTAP, rapports."""

TEXTES = {
    # ------------------------------------------------------------ généraux
    'oui': {'fr': 'oui', 'en': 'yes'},
    'non': {'fr': 'non', 'en': 'no'},
    'taille_go': {'fr': '{v} Go', 'en': '{v} GB'},
    'taille_mo': {'fr': '{v} Mo', 'en': '{v} MB'},
    'ecrit': {'fr': 'Écrit : {chemin}', 'en': 'Written: {chemin}'},
    'erreur_ecriture': {'fr': "Impossible d'écrire {chemin} : {erreur}", 'en': 'Cannot write {chemin}: {erreur}'},
    'interrompu': {'fr': 'Interrompu.', 'en': 'Interrupted.'},
    'interrompu_reprise': {'fr': 'Interrompu. Relancer la même commande reprend là où le traitement s\'est arrêté.',
                           'en': 'Interrupted. Running the same command again resumes where processing stopped.'},
    'os_windows': {'fr': 'Windows', 'en': 'Windows'},
    'os_macos': {'fr': 'macOS', 'en': 'macOS'},
    'os_linux': {'fr': 'Linux', 'en': 'Linux'},

    # ------------------------------------------------------------ argparse
    'argparse_usage': {'fr': 'utilisation : ', 'en': 'usage: '},
    'argparse_options': {'fr': 'options', 'en': 'options'},
    'argparse_positionnels': {'fr': 'arguments', 'en': 'positional arguments'},
    'argparse_aide': {'fr': 'affiche cette aide et quitte', 'en': 'show this help message and exit'},
    'argparse_requis': {'fr': 'arguments obligatoires manquants : %s', 'en': 'the following arguments are required: %s'},
    'argparse_choix': {'fr': 'choix invalide : %(value)r (possibles : %(choices)s)',
                       'en': 'invalid choice: %(value)r (choose from %(choices)s)'},
    'argparse_inconnus': {'fr': 'arguments non reconnus : %s', 'en': 'unrecognized arguments: %s'},
    'argparse_erreur': {'fr': '%(prog)s : erreur : %(message)s\n', 'en': '%(prog)s: error: %(message)s\n'},

    # ------------------------------------------------------------ ligne de commande
    'cli_description': {
        'fr': "Coupole — boîte à outils libre du DU « Explorer et Comprendre l'Univers » (Observatoire de Paris).\n"
              "Sans commande : interface graphique.",
        'en': "Coupole — free toolbox for the « Explorer et Comprendre l'Univers » diploma (Observatoire de Paris).\n"
              "Without a command: graphical interface."},
    'cli_epilogue': {'fr': "Aide d'une commande : coupole <commande> --help. Manuel : coupole manuel.",
                     'en': 'Help on a command: coupole <command> --help. Manual: coupole manual.'},
    'cli_aide_version': {'fr': 'affiche la version et quitte', 'en': 'show the version and exit'},
    'cli_aide_reinit_interface': {'fr': "efface la disposition gardée (fenêtre, colonnes, filtres, dossiers des "
                                        "dialogues) puis quitte ; les réglages ne changent pas",
                                  'en': 'erase the saved layout (window, columns, filters, file-dialog folders) and exit; '
                                        'settings do not change'},
    'cli_reinit_interface_fait': {'fr': "Disposition effacée : l'interface reprendra son état d'origine ({chemin}).",
                                  'en': 'Layout erased: the interface will start in its original state ({chemin}).'},
    'cli_reinit_interface_rien': {'fr': "Aucune disposition enregistrée : l'interface est déjà dans son état d'origine.",
                                  'en': 'No saved layout: the interface is already in its original state.'},
    'cli_aide_langue': {'fr': 'langue des messages (auto : celle du système)', 'en': 'message language (auto: system language)'},
    'cli_aide_verbeux': {'fr': 'journal détaillé', 'en': 'detailed log'},
    'cli_aide_json': {'fr': 'sortie JSON (pour les scripts)', 'en': 'JSON output (for scripts)'},
    'cli_commande': {'fr': 'COMMANDE', 'en': 'COMMAND'},
    'cli_commandes': {'fr': 'commandes', 'en': 'commands'},
    'cli_meta_chemin': {'fr': 'CHEMIN', 'en': 'PATH'},
    'cli_meta_dossier': {'fr': 'DOSSIER', 'en': 'FOLDER'},
    'cli_meta_fichier': {'fr': 'FICHIER', 'en': 'FILE'},
    'cli_gui': {'fr': "lance l'interface graphique", 'en': 'start the graphical interface'},
    'cli_astap': {'fr': 'ASTAP (facultatif) : détection, guide d\'installation', 'en': 'ASTAP (optional): detection, installation guide'},
    'cli_astap_desc': {'fr': "Cherche ASTAP et son catalogue d'étoiles, indique quoi installer pour ce système, "
                             "ou enregistre leur emplacement. Coupole fonctionne sans ASTAP.",
                       'en': 'Look for ASTAP and its star catalogue, show what to install for this system, or record '
                             'their location. Coupole works without ASTAP.'},
    'cli_astap_guide': {'fr': "affiche le guide d'installation pour ce système", 'en': 'show the installation guide for this system'},
    'cli_astap_definir': {'fr': "chemin de l'exécutable ASTAP (ou de son dossier)", 'en': 'path of the ASTAP executable (or its folder)'},
    'cli_astap_catalogue': {'fr': "dossier du catalogue d'étoiles (D80, D50...)", 'en': 'star catalogue folder (D80, D50...)'},
    'cli_astap_oublier': {'fr': 'oublie les chemins enregistrés (retour à la détection)', 'en': 'forget recorded paths (back to detection)'},
    'cli_rapports': {'fr': "rapports d'incident : état, accord, refus", 'en': 'incident reports: status, consent, refusal'},
    'cli_rapports_desc': {'fr': "Rien n'est envoyé sans accord. Sans accord, les rapports restent dans un dossier local.",
                          'en': 'Nothing is sent without consent. Without consent, reports stay in a local folder.'},
    'cli_rapports_activer': {'fr': "autorise l'envoi des rapports (anonymes)", 'en': 'allow sending (anonymous) reports'},
    'cli_rapports_desactiver': {'fr': "interdit l'envoi des rapports", 'en': 'forbid sending reports'},
    'cli_maj': {'fr': 'recherche une mise à jour', 'en': 'check for an update'},
    'cli_maj_desc': {'fr': "Interroge les versions publiées sur GitHub. Le paquet autonome se met à jour lui-même ; "
                           "une installation par pip/pipx indique la commande à lancer.",
                     'en': 'Query the releases published on GitHub. The standalone package updates itself; a pip/pipx '
                           'installation shows the command to run.'},
    'cli_maj_appliquer': {'fr': 'télécharge et installe la mise à jour (paquet autonome)', 'en': 'download and install the update (standalone package)'},
    'cli_modules': {'fr': 'liste les modules installés', 'en': 'list installed modules'},
    'cli_manuel': {'fr': 'chemin du manuel PDF', 'en': 'path of the PDF manual'},
    'modules_erreur': {'fr': 'Module ignoré : {paquet} ({erreur})', 'en': 'Module ignored: {paquet} ({erreur})'},
    'manuel_absent': {'fr': 'Manuel introuvable dans cette installation.', 'en': 'Manual not found in this installation.'},
    'gui_indisponible': {'fr': "Interface graphique indisponible ({erreur}). Toutes les fonctions restent accessibles "
                               "en ligne de commande : coupole --help",
                         'en': 'Graphical interface unavailable ({erreur}). Every function is still available on the '
                               'command line: coupole --help'},

    # ------------------------------------------------------------ parallélisme
    'parallele_raison_econome': {'fr': 'mode économe (petite machine ou choix manuel)', 'en': 'economy mode (small computer or manual choice)'},
    'parallele_raison_memoire': {'fr': 'limité par la mémoire disponible', 'en': 'limited by available memory'},
    'parallele_raison_coeurs': {'fr': 'limité par les cœurs du processeur (un cœur laissé libre)', 'en': 'limited by processor cores (one core left free)'},
    'parallele_raison_manuel': {'fr': 'bridage manuel', 'en': 'manual limit'},

    # ------------------------------------------------------------ ASTAP
    'astap_titre': {'fr': 'ASTAP (solveur astrométrique, facultatif)', 'en': 'ASTAP (astrometric solver, optional)'},
    'astap_absent': {'fr': 'ASTAP non trouvé.', 'en': 'ASTAP not found.'},
    'astap_sans_catalogue': {'fr': "ASTAP trouvé, mais aucun catalogue d'étoiles (D80, D50...).",
                             'en': 'ASTAP found, but no star catalogue (D80, D50...).'},
    'astap_catalogue_incomplet': {'fr': "Catalogue d'étoiles incomplet (tuiles manquantes) : réinstaller le catalogue.",
                                  'en': 'Incomplete star catalogue (missing tiles): reinstall the catalogue.'},
    'astap_pret': {'fr': 'ASTAP prêt : chaque solution sera vérifiée indépendamment.',
                   'en': 'ASTAP ready: every solution will be checked independently.'},
    'astap_executable': {'fr': 'Exécutable', 'en': 'Executable'},
    'astap_version': {'fr': 'Version', 'en': 'Version'},
    'astap_catalogue': {'fr': 'Catalogue', 'en': 'Catalogue'},
    'astap_tuiles': {'fr': 'tuiles', 'en': 'tiles'},
    'astap_sans_effet': {
        'fr': "Sans ASTAP, Coupole fait tout le reste : contrôles de cohérence de la solution existante (échelle, "
              "angle, centre), en-têtes, tri en lots, conversion. Seule manque la vérification INDÉPENDANTE de chaque "
              "solution (et la réfection d'une solution fausse).",
        'en': 'Without ASTAP, Coupole does everything else: consistency checks of the existing solution (scale, angle, '
              'centre), headers, sorting into stacks, conversion. Only the INDEPENDENT check of each solution (and '
              'redoing a wrong one) is missing.'},
    'astap_guide_titre': {'fr': 'Installer ASTAP — {systeme} {arch}{famille}', 'en': 'Installing ASTAP — {systeme} {arch}{famille}'},
    'astap_guide_pourquoi': {
        'fr': "ASTAP est gratuit (licence MPL 2.0), écrit par Han Kleijn. Coupole ne l'embarque pas (licence et taille "
              "du catalogue). Il faut deux choses : le programme, et UN catalogue d'étoiles.",
        'en': 'ASTAP is free (MPL 2.0 licence), written by Han Kleijn. Coupole does not bundle it (licence and catalogue '
              'size). Two things are needed: the program, and ONE star catalogue.'},
    'astap_guide_catalogue': {
        'fr': "Catalogue conseillé : D80 (≈ 1,2 Go). Les images de la banque ont des champs de 10,7′ à 31′ (T120 : "
              "13,1′ ; IRIS : 23′ et 31′), sous le seuil de 0,6° au-delà duquel le site officiel déclare D05 à D80 "
              "équivalents ; il précise que les catalogues denses conviennent aux petits champs. D80 est celui du "
              "traitement de référence (6 888 solutions confirmées sur 7 625). D50 (≈ 0,9 Go) convient aussi pour IRIS.",
        'en': 'Recommended catalogue: D80 (≈ 1.2 GB). The bank images have fields of 10.7′ to 31′ (T120: 13.1′; IRIS: '
              '23′ and 31′), below the 0.6° threshold above which the official site lists D05 to D80 as equivalent; it '
              'states that dense catalogues suit small fields. D80 is the one used for the reference processing '
              '(6,888 solutions confirmed out of 7,625). D50 (≈ 0.9 GB) also suits IRIS.'},
    'astap_guide_programme': {'fr': 'Télécharger le programme :', 'en': 'Download the program:'},
    'astap_guide_cat': {'fr': "Télécharger le catalogue d'étoiles :", 'en': 'Download the star catalogue:'},
    'astap_guide_detection': {
        'fr': "Ensuite : relancer « coupole astap » (ou le bouton « Chercher » de l'assistant). Si ASTAP est ailleurs : "
              "coupole astap --definir <exécutable> --catalogue <dossier>, ou les variables COUPOLE_ASTAP et "
              "COUPOLE_ASTAP_CATALOGUE.",
        'en': 'Then: run « coupole astap » again (or the « Search » button of the assistant). If ASTAP is elsewhere: '
              'coupole astap --set <executable> --catalog <folder>, or the COUPOLE_ASTAP and COUPOLE_ASTAP_CATALOGUE '
              'variables.'},
    'astap_guide_page': {'fr': 'Page officielle : {page}', 'en': 'Official page: {page}'},
    'astap_lien_installeur': {'fr': 'Installeur Windows 64 bits (astap_setup.exe)', 'en': 'Windows 64-bit installer (astap_setup.exe)'},
    'astap_lien_cli_zip': {'fr': 'Version ligne de commande seule (astap_cli, archive zip)', 'en': 'Command-line only version (astap_cli, zip archive)'},
    'astap_lien_pkg_m': {'fr': 'Paquet macOS Apple Silicon (astap_M1.pkg)', 'en': 'macOS Apple Silicon package (astap_M1.pkg)'},
    'astap_lien_pkg_intel': {'fr': 'Paquet macOS Intel (astap.pkg)', 'en': 'macOS Intel package (astap.pkg)'},
    'astap_lien_deb': {'fr': 'Paquet Debian/Ubuntu (.deb)', 'en': 'Debian/Ubuntu package (.deb)'},
    'astap_lien_rpm': {'fr': 'Paquet Fedora/openSUSE (.rpm)', 'en': 'Fedora/openSUSE package (.rpm)'},
    'astap_lien_arch': {'fr': 'Paquet Arch/Manjaro (.pkg.tar.zst)', 'en': 'Arch/Manjaro package (.pkg.tar.zst)'},
    'astap_lien_targz': {'fr': 'Archive pour toute distribution (.tar.gz)', 'en': 'Archive for any distribution (.tar.gz)'},
    'astap_lien_d80_exe': {'fr': 'Catalogue D80, installeur Windows (conseillé)', 'en': 'D80 catalogue, Windows installer (recommended)'},
    'astap_lien_d50_exe': {'fr': 'Catalogue D50, installeur Windows (plus léger)', 'en': 'D50 catalogue, Windows installer (lighter)'},
    'astap_lien_d80_pkg': {'fr': 'Catalogue D80, paquet macOS (conseillé)', 'en': 'D80 catalogue, macOS package (recommended)'},
    'astap_lien_d50_pkg': {'fr': 'Catalogue D50, paquet macOS (plus léger)', 'en': 'D50 catalogue, macOS package (lighter)'},
    'astap_lien_d80_deb': {'fr': 'Catalogue D80, paquet .deb (conseillé)', 'en': 'D80 catalogue, .deb package (recommended)'},
    'astap_lien_d50_deb': {'fr': 'Catalogue D50, paquet .deb (plus léger)', 'en': 'D50 catalogue, .deb package (lighter)'},
    'astap_lien_d80_zip': {'fr': 'Catalogue D80, archive zip (conseillé)', 'en': 'D80 catalogue, zip archive (recommended)'},
    'astap_lien_d50_zip': {'fr': 'Catalogue D50, archive zip (plus léger)', 'en': 'D50 catalogue, zip archive (lighter)'},
    'astap_etape_win_1': {'fr': "Lancer astap_setup.exe. Windows peut afficher « Windows a protégé votre ordinateur » "
                                "(éditeur inconnu) : « Informations complémentaires », puis « Exécuter quand même ».",
                          'en': 'Run astap_setup.exe. Windows may show « Windows protected your PC » (unknown publisher): '
                                '« More info », then « Run anyway ».'},
    'astap_etape_win_2': {'fr': "Lancer l'installeur du catalogue : il s'installe dans le même dossier ({dossier}).",
                          'en': 'Run the catalogue installer: it installs into the same folder ({dossier}).'},
    'astap_etape_win_3': {'fr': "Facultatif : décompresser astap_cli.exe (version ligne de commande) dans {dossier} ; "
                                "Coupole l'utilise de préférence à astap.exe.",
                          'en': 'Optional: unzip astap_cli.exe (command-line version) into {dossier}; Coupole prefers '
                                'it to astap.exe.'},
    'astap_etape_win_4': {'fr': "Tous les fichiers (programme et catalogue) doivent être dans le même dossier.",
                          'en': 'All files (program and catalogue) must be in the same folder.'},
    'astap_etape_win_arm_1': {'fr': "Créer le dossier {dossier} et y décompresser astap_cli.exe.",
                              'en': 'Create the folder {dossier} and unzip astap_cli.exe into it.'},
    'astap_etape_win_arm_2': {'fr': "Décompresser le catalogue D80 dans ce même dossier.",
                              'en': 'Unzip the D80 catalogue into the same folder.'},
    'astap_etape_win_arm_3': {'fr': "Indiquer ce dossier à Coupole (bouton « Choisir » ou coupole astap --definir {dossier}).",
                              'en': 'Point Coupole to this folder (« Choose » button or coupole astap --set {dossier}).'},
    'astap_etape_mac_1': {'fr': "Clic droit sur le paquet du programme, « Ouvrir », puis suivre l'installation "
                                "(ASTAP.app arrive dans Applications).",
                          'en': 'Right-click the program package, « Open », then follow the installation (ASTAP.app goes '
                                'into Applications).'},
    'astap_etape_mac_2': {'fr': "Même chose pour le paquet du catalogue : il s'installe dans {dossier}.",
                          'en': 'Same for the catalogue package: it installs into {dossier}.'},
    'astap_etape_mac_m': {'fr': "Mac à puce Apple : signer une fois le programme dans le Terminal (consigne du site "
                                "officiel) : codesign --force -s - /Applications/ASTAP.app/Contents/MacOS/astap",
                          'en': 'Apple silicon Mac: sign the program once in the Terminal (instruction from the official '
                                'site): codesign --force -s - /Applications/ASTAP.app/Contents/MacOS/astap'},
    'astap_etape_mac_3': {'fr': "Facultatif : la version ligne de commande (astap_cli) peut être décompressée dans {dossier}.",
                          'en': 'Optional: the command-line version (astap_cli) can be unzipped into {dossier}.'},
    'astap_etape_linux_deb_1': {'fr': "Installer le programme : sudo apt install ./astap_*.deb (ou double-clic sur le fichier).",
                                'en': 'Install the program: sudo apt install ./astap_*.deb (or double-click the file).'},
    'astap_etape_linux_deb_2': {'fr': "Installer le catalogue : sudo apt install ./d80_star_database.deb (il va dans {dossier}).",
                                'en': 'Install the catalogue: sudo apt install ./d80_star_database.deb (it goes into {dossier}).'},
    'astap_etape_linux_autre_1': {'fr': "Installer le paquet de la distribution (rpm : sudo dnf install ./astap_amd64.rpm ; "
                                        "Arch : sudo pacman -U ./astap_*.pkg.tar.zst), ou décompresser l'archive / "
                                        "astap_cli dans {dossier}.",
                                  'en': 'Install the distribution package (rpm: sudo dnf install ./astap_amd64.rpm; Arch: '
                                        'sudo pacman -U ./astap_*.pkg.tar.zst), or unpack the archive / astap_cli into '
                                        '{dossier}.'},
    'astap_etape_linux_autre_2': {'fr': "Décompresser le catalogue dans {dossier} (sudo unzip d80_star_database.zip -d {dossier}).",
                                  'en': 'Unzip the catalogue into {dossier} (sudo unzip d80_star_database.zip -d {dossier}).'},
    'astap_etape_linux_3': {'fr': "Pas d'AppImage officielle d'ASTAP. ASTAP cherche son catalogue dans {dossier} puis "
                                  "/usr/share/astap/data ; Coupole aussi.",
                            'en': 'There is no official ASTAP AppImage. ASTAP looks for its catalogue in {dossier} then '
                                  '/usr/share/astap/data; so does Coupole.'},

    # ------------------------------------------------------------ rapports
    'rapports_etat_oui': {'fr': "Envoi des rapports d'incident : autorisé.", 'en': 'Sending incident reports: allowed.'},
    'rapports_etat_non': {'fr': "Envoi des rapports d'incident : refusé (rapports gardés en local).",
                          'en': 'Sending incident reports: refused (reports kept locally).'},
    'rapports_etat_inconnu': {'fr': "Envoi des rapports d'incident : question pas encore posée (rien n'est envoyé).",
                              'en': 'Sending incident reports: not asked yet (nothing is sent).'},
    'rapports_dossier': {'fr': 'Dossier local des rapports : {dossier}', 'en': 'Local report folder: {dossier}'},

    # ------------------------------------------------------------ mise à jour
    'maj_verification': {'fr': 'Recherche de mise à jour ({depot})...', 'en': 'Checking for updates ({depot})...'},
    'maj_aucune': {'fr': 'Aucune version plus récente que {version}.', 'en': 'No version newer than {version}.'},
    'maj_disponible': {'fr': 'Version {version} disponible.', 'en': 'Version {version} available.'},
    'maj_pip': {'fr': 'Installation par pip/pipx : mettre à jour avec\n  {commande}',
                'en': 'pip/pipx installation: update with\n  {commande}'},
    'maj_systeme': {'fr': 'Installation par le paquet système (.deb) : Coupole ne se met pas à jour seul.\n'
                          'Téléchargez le nouveau paquet :\n  {url}\npuis installez-le :\n  {commande}',
                    'en': 'Installed from the system package (.deb): Coupole does not update itself.\n'
                          'Download the new package:\n  {url}\nthen install it:\n  {commande}'},
    'maj_ouvrir_page': {'fr': 'Télécharger le paquet', 'en': 'Download the package'},
    'maj_ouvrir_page_aide': {'fr': 'Ouvre l\'adresse du paquet .deb dans le navigateur.', 'en': 'Opens the .deb package address in the browser.'},
    'maj_faite': {'fr': 'Mise à jour installée. Relancer Coupole.', 'en': 'Update installed. Restart Coupole.'},
    'maj_appliquer_cli': {'fr': 'Pour l\'installer : coupole maj --appliquer', 'en': 'To install it: coupole update --apply'},
# ------------------------------------------------------------ sources
    'gpu_aucune': {'fr': 'aucune détectée', 'en': 'none detected'},
    'cli_sources': {'fr': 'adresses des services (TAP, résolveurs, mise à jour...)', 'en': 'service addresses (TAP, resolvers, updates...)'},
    'cli_sources_desc': {'fr': "Sans option : liste les adresses et leur origine (défaut livré, fichier distant, valeur forcée).",
                         'en': 'Without option: list the addresses and their origin (shipped default, remote file, forced value).'},
    'cli_meta_cle': {'fr': 'CLÉ', 'en': 'KEY'},
    'cli_meta_valeur': {'fr': 'VALEUR', 'en': 'VALUE'},
    'cli_sources_forcer': {'fr': 'force une valeur (jamais écrasée par une mise à jour)', 'en': 'force a value (never overwritten by an update)'},
    'cli_sources_defaut': {'fr': 'revient à la valeur par défaut pour cette clé', 'en': 'go back to the default value for this key'},
    'cli_sources_reinit': {'fr': 'revient aux valeurs par défaut pour toutes les clés', 'en': 'go back to the default values for every key'},
    'cli_sources_tester': {'fr': 'teste la connexion à cette adresse', 'en': 'test the connection to this address'},
    'cli_sources_distant': {'fr': 'récupère maintenant le fichier de sources publié dans le dépôt', 'en': 'fetch the sources file published in the repository now'},
    'sources_distant_ok': {'fr': 'Fichier de sources distant récupéré et accepté.', 'en': 'Remote sources file fetched and accepted.'},
    'sources_distant_non': {'fr': "Fichier de sources distant non retenu (injoignable, mal formé ou pas plus récent) : valeurs locales gardées.",
                            'en': 'Remote sources file not used (unreachable, malformed or not newer): local values kept.'},
    'sources_test_ok': {'fr': '{cle} : connexion réussie ({detail}).', 'en': '{cle}: connection succeeded ({detail}).'},
    'sources_test_echec': {'fr': '{cle} : échec de la connexion ({detail}).', 'en': '{cle}: connection failed ({detail}).'},
    'sources_origine_defaut': {'fr': 'défaut', 'en': 'default'},
    'sources_origine_distant': {'fr': 'distant', 'en': 'remote'},
    'sources_origine_utilisateur': {'fr': 'forcée', 'en': 'forced'},
# ------------------------------------------------------------ fenêtre principale et menus
    'menu_fichier': {'fr': '&Fichier', 'en': '&File'},
    'menu_affichage': {'fr': 'A&ffichage', 'en': '&View'},
    'menu_langue': {'fr': '&Langue', 'en': '&Language'},
    'menu_outils': {'fr': '&Outils', 'en': '&Tools'},
    'menu_aide': {'fr': '&Aide', 'en': '&Help'},
    'act_reglages': {'fr': 'Préférences…', 'en': 'Preferences…'},
    'act_reglages_aide': {'fr': 'Langue, dossier de sortie, format, parallélisme, débit, sources, mises à jour.',
                          'en': 'Language, output folder, format, parallelism, rate, sources, updates.'},
    'act_quitter': {'fr': 'Quitter', 'en': 'Quit'},
    'act_quitter_aide': {'fr': 'Ferme Coupole (un traitement en cours peut être repris plus tard).',
                         'en': 'Close Coupole (a running processing can be resumed later).'},
    'act_module': {'fr': 'Module', 'en': 'Module'},
    'act_module_aide': {'fr': 'Affiche ce module.', 'en': 'Show this module.'},
    'menu_apparence': {'fr': 'Apparence', 'en': 'Appearance'},
    'menu_apparence_aide': {'fr': 'Thème de Coupole : sombre (défaut) ou clair.', 'en': "Coupole's theme: dark (default) or light."},
    'act_apparence_clair': {'fr': 'Clair', 'en': 'Light'},
    'act_apparence_sombre': {'fr': 'Sombre', 'en': 'Dark'},
    'act_apparence_aide': {'fr': "Applique ce thème tout de suite et l'enregistre. Il ne dépend pas du thème de l'ordinateur ; "
                                 'même réglage que Préférences > Apparence.',
                           'en': "Applies this theme at once and saves it. It does not depend on the computer's theme; "
                                 'same setting as Preferences > Appearance.'},
    'act_apparence_basculer': {'fr': 'Basculer clair / sombre', 'en': 'Toggle light / dark'},
    'act_apparence_basculer_aide': {'fr': "Passe de l'un à l'autre (Ctrl+Maj+D).", 'en': 'Switches between the two (Ctrl+Shift+D).'},
    'apparence_appliquee': {'fr': 'Thème {nom} appliqué.', 'en': '{nom} theme applied.'},
    'act_langue': {'fr': 'Langue', 'en': 'Language'},
    'act_langue_aide': {'fr': "Change la langue de l'interface (auto : celle du système).",
                        'en': 'Change the interface language (auto: system language).'},
    'act_astap': {'fr': 'Assistant ASTAP…', 'en': 'ASTAP assistant…'},
    'act_astap_aide': {'fr': "Détecte ASTAP et son catalogue, ou explique comment les installer sur cet ordinateur.",
                       'en': 'Detect ASTAP and its catalogue, or explain how to install them on this computer.'},
    'act_aide_ecran': {'fr': 'Aide de cet écran', 'en': 'Help on this screen'},
    'act_aide_ecran_aide': {'fr': "Explique l'écran affiché.", 'en': 'Explain the screen shown.'},
    'act_manuel': {'fr': 'Manuel (PDF)', 'en': 'Manual (PDF)'},
    'act_manuel_aide': {'fr': 'Ouvre le manuel de référence.', 'en': 'Open the reference manual.'},
    'act_raccourcis': {'fr': 'Raccourcis clavier', 'en': 'Keyboard shortcuts'},
    'act_raccourcis_aide': {'fr': 'Liste des raccourcis clavier.', 'en': 'List of keyboard shortcuts.'},
    'act_signaler': {'fr': 'Signaler un problème…', 'en': 'Report a problem…'},
    'act_signaler_aide': {'fr': "Décrire un problème ; envoi anonyme ou fichier à joindre vous-même.",
                          'en': 'Describe a problem; anonymous sending or a file to attach yourself.'},
    'act_rapports': {'fr': "Envoyer les rapports d'incident", 'en': 'Send incident reports'},
    'act_rapports_aide': {'fr': "Coché : les plantages sont signalés automatiquement (anonymes). Décoché : rien n'est envoyé.",
                          'en': 'Checked: crashes are reported automatically (anonymous). Unchecked: nothing is sent.'},
    'act_maj': {'fr': 'Rechercher une mise à jour', 'en': 'Check for updates'},
    'act_maj_aide': {'fr': 'Interroge les versions publiées sur GitHub.', 'en': 'Query the releases published on GitHub.'},
    'act_apropos': {'fr': 'À propos de Coupole', 'en': 'About Coupole'},
    'act_apropos_aide': {'fr': 'Version, licence, configuration détectée.', 'en': 'Version, licence, detected configuration.'},
    'fen_modules_aide': {'fr': 'Modules de Coupole (Ctrl+1, Ctrl+2…).', 'en': 'Coupole modules (Ctrl+1, Ctrl+2…).'},
    'fen_module_erreur': {'fr': 'Le module « {module} » n\'a pas pu s\'ouvrir : {erreur}', 'en': 'The « {module} » module could not open: {erreur}'},
    'fen_pret': {'fr': 'Prêt.', 'en': 'Ready.'},
    'fen_arret_en_cours': {'fr': 'Arrêt des travaux en cours…', 'en': 'Stopping running work…'},
    'fen_reglages_restaures': {'fr': "Le fichier des réglages était illisible : valeurs par défaut rétablies (l'ancien fichier est gardé à côté, suffixe « .corrompu-… »).",
                               'en': 'The settings file was unreadable: defaults restored (the old file is kept alongside, suffix « .corrompu-… »).'},
    'fen_langue_occupe': {'fr': 'Un traitement est en cours : changer de langue après la fin.', 'en': 'A processing is running: change the language when it ends.'},
    'fen_quitter_titre': {'fr': 'Quitter', 'en': 'Quit'},
    'fen_quitter_occupe': {'fr': "Un traitement est en cours. Quitter l'interrompt (il reprendra au prochain lancement). Quitter ?",
                           'en': 'A processing is running. Quitting interrupts it (it will resume next time). Quit?'},
    'aide_ecran_titre': {'fr': 'Aide — {ecran}', 'en': 'Help — {ecran}'},
    'aide_ecran_aide': {'fr': "Aide de l'écran affiché.", 'en': 'Help on the screen shown.'},
    'aide_generale': {'fr': '<p>Choisir un module dans la barre de gauche. F1 : aide de l\'écran ; Maj+F1 : manuel. '
                            'Affichage &gt; Apparence : thème sombre (défaut) ou clair, Ctrl+Maj+D pour basculer.</p>',
                      'en': '<p>Pick a module in the left bar. F1: help on the screen; Shift+F1: manual. '
                            'View &gt; Appearance: dark (default) or light theme, Ctrl+Shift+D to toggle.</p>'},
    'dlg_ok': {'fr': 'OK', 'en': 'OK'},
    'dlg_ok_aide': {'fr': 'Valide et ferme.', 'en': 'Confirm and close.'},
    'dlg_annuler': {'fr': 'Annuler', 'en': 'Cancel'},
    'dlg_annuler_aide': {'fr': 'Ferme sans rien changer.', 'en': 'Close without changing anything.'},
    'unite_mos': {'fr': 'Mo/s', 'en': 'MB/s'},
    'fmt_xisf': {'fr': 'XISF compressé (PixInsight)', 'en': 'Compressed XISF (PixInsight)'},
    'fmt_fz': {'fr': 'FITS compressé sans perte (.fits.fz : Siril, astropy, DS9)', 'en': 'Lossless compressed FITS (.fits.fz: Siril, astropy, DS9)'},
    'fmt_fits': {'fr': 'FITS float32 non compressé', 'en': 'Uncompressed float32 FITS'},

    # ------------------------------------------------------------ consentement
    'consent_titre': {'fr': "Rapports d'incident", 'en': 'Incident reports'},
    'consent_texte': {'fr': "<p>Coupole peut envoyer à son auteur un rapport <b>anonyme</b> quand elle plante ou se fige, "
                            "et une preuve de vie par jour. Le rapport contient : version, système, processeur, mémoire, "
                            "carte graphique, et la trace de l'erreur avec les chemins tronqués (votre dossier personnel "
                            "devient « ~ »). <b>Jamais</b> de nom de machine, de nom d'utilisateur, ni d'image.</p>"
                            "<p>Sans accord, rien n'est envoyé : les rapports restent dans un dossier local. "
                            "Ce choix se change à tout moment (menu Aide, ou « coupole rapports »).</p>",
                      'en': '<p>Coupole can send its author an <b>anonymous</b> report when it crashes or freezes, and one '
                            'sign of life per day. The report contains: version, system, processor, memory, graphics card, '
                            'and the error trace with shortened paths (your home folder becomes « ~ »). <b>Never</b> a '
                            'computer name, a user name, or an image.</p><p>Without consent nothing is sent: reports stay in '
                            'a local folder. This choice can be changed at any time (Help menu, or « coupole reports »).</p>'},
    'consent_oui': {'fr': "Autoriser l'envoi", 'en': 'Allow sending'},
    'consent_oui_aide': {'fr': 'Les rapports anonymes seront envoyés.', 'en': 'Anonymous reports will be sent.'},
    'consent_non': {'fr': 'Ne rien envoyer', 'en': 'Send nothing'},
    'consent_non_aide': {'fr': 'Les rapports restent sur cet ordinateur.', 'en': 'Reports stay on this computer.'},

    # ------------------------------------------------------------ préférences
    'reg_titre': {'fr': 'Préférences', 'en': 'Preferences'},
    'reg_apparence': {'fr': 'Apparence', 'en': 'Appearance'},
    'reg_apparence_aide': {'fr': "Thème de Coupole. Il ne dépend pas du thème de l'ordinateur, pour que tout reste lisible.",
                           'en': "Coupole's theme. It does not follow the computer's theme, so that everything stays readable."},
    'reg_apparence_clair': {'fr': 'Clair', 'en': 'Light'},
    'reg_apparence_sombre': {'fr': 'Sombre', 'en': 'Dark'},
    'reg_langue': {'fr': "Langue de l'interface", 'en': 'Interface language'},
    'reg_langue_aide': {'fr': 'auto : la langue du système (français ou anglais).', 'en': 'auto: the system language (French or English).'},
    'reg_langue_auto': {'fr': 'Automatique', 'en': 'Automatic'},
    'reg_noms': {'fr': 'Langue des noms et en-têtes', 'en': 'Language of names and headers'},
    'reg_noms_aide': {'fr': "Langue des dossiers (01_Asteroides / 01_Asteroids), des noms d'objets et des commentaires FITS. "
                            "Un dossier déjà traité garde sa langue.",
                      'en': 'Language of folders (01_Asteroides / 01_Asteroids), object names and FITS comments. A folder '
                            'already processed keeps its language.'},
    'reg_dest': {'fr': 'Dossier de sortie', 'en': 'Output folder'},
    'reg_dest_aide': {'fr': 'Où ranger les images converties et les lots.', 'en': 'Where to store converted images and stacks.'},
    'reg_parcourir': {'fr': 'Parcourir…', 'en': 'Browse…'},
    'reg_dialogues_fichiers': {'fr': 'Boîtes de dialogue de fichiers', 'en': 'File dialogs'},
    'reg_dialogues_fichiers_systeme': {'fr': 'Système (explorateur du bureau)', 'en': 'System (desktop file manager)'},
    'reg_dialogues_fichiers_qt': {'fr': 'Qt (dialogue intégré)', 'en': 'Qt (built-in dialog)'},
    'reg_dialogues_fichiers_aide': {
        'fr': "Système (conseillé) : l'explorateur de votre bureau, avec ses emplacements, favoris et partages réseau "
              "(Explorateur Windows, Finder, Dolphin ou Fichiers sous Linux, par le portail XDG). Qt : le dialogue "
              "intégré à Coupole, en français, avec dossiers personnels, disques et partages montés dans la barre "
              "latérale ; à choisir seulement si le dialogue du système ne s'ouvre pas ou fonctionne mal. Sous Linux, "
              "repasser à « Système » prend effet au prochain lancement.",
        'en': 'System (recommended): your desktop\'s file manager, with its places, bookmarks and network shares '
              '(Windows Explorer, Finder, Dolphin or Files on Linux, through the XDG portal). Qt: the dialog built '
              'into Coupole, with home folders, drives and mounted shares in the sidebar; pick it only if the system '
              'dialog does not open or misbehaves. On Linux, switching back to “System” takes effect at next start.'},
    'aide_dossier_reseau': {
        'fr': "<p><b>Dossier sur un NAS ou un partage réseau.</b> Le dialogue « Parcourir » est l'explorateur du "
              "système : choisir le partage dans ses emplacements réseau. <i>Linux</i> : ouvrir d'abord le partage "
              "dans Dolphin ou Fichiers (smb://serveur/partage) ; il apparaît sous <tt>/run/user/&lt;uid&gt;/gvfs/"
              "smb-share:server=…,share=…</tt> (GNOME, ou KDE avec kio-fuse), ou monter le partage en cifs/nfs "
              "(<tt>/mnt/nas</tt>). <i>macOS</i> : Finder &gt; Aller &gt; Se connecter au serveur (⌘K), "
              "<tt>smb://serveur/partage</tt>, puis le choisir sous <tt>/Volumes</tt>. <i>Windows</i> : lecteur réseau "
              "(Z:) ou chemin UNC <tt>\\\\serveur\\partage</tt>, saisissable aussi dans le champ du dossier.</p>",
        'en': '<p><b>Folder on a NAS or a network share.</b> The “Browse” dialog is the system file manager: pick the '
              'share among its network places. <i>Linux</i>: first open the share in Dolphin or Files '
              '(smb://server/share); it shows up under <tt>/run/user/&lt;uid&gt;/gvfs/smb-share:server=…,share=…</tt> '
              '(GNOME, or KDE with kio-fuse), or mount the share with cifs/nfs (<tt>/mnt/nas</tt>). <i>macOS</i>: '
              'Finder &gt; Go &gt; Connect to Server (⌘K), <tt>smb://server/share</tt>, then pick it under '
              '<tt>/Volumes</tt>. <i>Windows</i>: network drive (Z:) or UNC path <tt>\\\\server\\share</tt>, '
              'which can also be typed into the folder field.</p>'},
    'reg_parcourir_aide': {'fr': 'Choisir le dossier.', 'en': 'Choose the folder.'},
    'reg_format': {'fr': 'Format de sortie', 'en': 'Output format'},
    'reg_format_aide': {'fr': 'XISF pour PixInsight (défaut) ; .fits.fz pour Siril et astropy ; FITS float32 si un logiciel ne lit rien d\'autre.',
                        'en': 'XISF for PixInsight (default); .fits.fz for Siril and astropy; float32 FITS if a program reads nothing else.'},
    'reg_dl': {'fr': 'Téléchargements simultanés', 'en': 'Simultaneous downloads'},
    'reg_dl_aide': {'fr': 'Auto : 3 (2 en mode économe). 4 au plus : le serveur de l\'Observatoire est public.',
                    'en': "Auto: 3 (2 in economy mode). At most 4: the Observatory's server is public."},
    'reg_conv': {'fr': 'Conversions simultanées', 'en': 'Simultaneous conversions'},
    'reg_conv_aide': {'fr': 'Auto : cœurs physiques moins un, borné par la mémoire disponible.',
                      'en': 'Auto: physical cores minus one, bounded by available memory.'},
    'reg_auto': {'fr': 'auto', 'en': 'auto'},
    'reg_debit': {'fr': 'Débit maximal', 'en': 'Maximum rate'},
    'reg_debit_aide': {'fr': 'Plafond du débit total de téléchargement (politesse envers le serveur public).',
                       'en': 'Cap on the total download rate (courtesy to the public server).'},
    'reg_econome': {'fr': 'Mode économe (petite machine)', 'en': 'Economy mode (small computer)'},
    'reg_econome_aide': {'fr': 'Une conversion et deux téléchargements à la fois : peu de mémoire, machine réactive.',
                         'en': 'One conversion and two downloads at a time: little memory, responsive computer.'},
    'reg_maj': {'fr': 'Rechercher les mises à jour au démarrage', 'en': 'Check for updates at startup'},
    'reg_nouveautes': {'fr': 'Vérifier les nouveautés de la banque OHP au démarrage', 'en': 'Check the OHP bank for new images at startup'},
    'reg_nouveautes_aide': {'fr': "Si Internet est disponible et qu'une copie locale existe : compare l'inventaire à la copie et propose "
                                  "(sans jamais télécharger seul) les nouveautés.",
                            'en': 'When the Internet is available and a local copy exists: compare the inventory with the copy and offer '
                                  '(never downloading on its own) what is new.'},
    'reg_nouveautes_heures': {'fr': 'Au plus une vérification toutes les', 'en': 'At most one check every'},
    'reg_nouveautes_heures_aide': {'fr': 'Fréquence maximale de la vérification automatique (heures).', 'en': 'Maximum frequency of the automatic check (hours).'},
    'unite_heures': {'fr': 'h', 'en': 'h'},
    'reg_disposition': {'fr': 'Disposition', 'en': 'Layout'},
    'reg_disposition_reinit': {'fr': 'Réinitialiser la disposition', 'en': 'Reset the layout'},
    'reg_disposition_reinit_aide': {'fr': "Coupole retrouve à chaque lancement la fenêtre, les colonnes, les filtres, les "
                                          "onglets et les dossiers des dialogues tels que vous les avez laissés. Ce bouton "
                                          "remet la fenêtre, les colonnes, les séparateurs, les filtres, les onglets, les "
                                          "fichiers récents et les dossiers des dialogues dans leur état d'origine. Les "
                                          "réglages de cette fenêtre (langue, thème, dossier de sortie, format…) ne changent pas.",
                                    'en': 'Each time it starts, Coupole restores the window, columns, filters, tabs and '
                                          'file-dialog folders as you left them. This button puts the window, columns, '
                                          'splitters, filters, tabs, recent files and file-dialog folders back to their '
                                          'original state. The settings of this window (language, '
                                          'theme, output folder, format…) do not change.'},
    'reg_disposition_question': {'fr': "Revenir à la disposition d'origine (fenêtre, colonnes, filtres, onglets, fichiers "
                                       "récents, dossiers des dialogues) ?",
                                 'en': 'Go back to the original layout (window, columns, filters, tabs, recent files, '
                                       'file-dialog folders)?'},
    'fen_disposition_reinitialisee': {'fr': "Disposition d'origine rétablie.", 'en': 'Original layout restored.'},
    'fen_disposition_plus_tard': {'fr': "Un traitement est en cours : la disposition d'origine sera rétablie au prochain "
                                        "lancement (rien n'est plus enregistré d'ici là).",
                                  'en': 'A processing is running: the original layout will come back at the next start '
                                        '(nothing more is saved until then).'},
    'aide_reglages_conserves': {'fr': "<p><b>Réglages conservés.</b> Taille et position de la fenêtre, colonnes (largeur, "
                                      "ordre, tri), séparateurs, module et onglet affichés, filtres et recherche, chemins "
                                      "saisis et dossiers des dialogues sont retrouvés au prochain lancement. Préférences "
                                      "&gt; « Réinitialiser la disposition » revient à l'origine.</p>",
                                'en': '<p><b>Saved settings.</b> Window size and position, columns (width, order, sort), '
                                      'splitters, module and tab shown, filters and search, typed paths and file-dialog '
                                      'folders come back at the next start. Preferences &gt; “Reset the layout” goes back '
                                      'to the original.</p>'},
    'reg_maj_aide': {'fr': 'Une requête discrète à GitHub au démarrage ; rien ne s\'installe sans votre accord.',
                     'en': 'One discreet request to GitHub at startup; nothing installs without your consent.'},

    # ------------------------------------------------------------ assistant ASTAP
    'astapdlg_titre': {'fr': 'Assistant ASTAP', 'en': 'ASTAP assistant'},
    'astapdlg_recherche': {'fr': 'Recherche en cours…', 'en': 'Searching…'},
    'astapdlg_chercher': {'fr': 'Chercher', 'en': 'Search'},
    'astapdlg_chercher_aide': {'fr': "Cherche ASTAP et son catalogue aux emplacements habituels, dans le PATH et les variables d'environnement.",
                               'en': 'Look for ASTAP and its catalogue in the usual places, in the PATH and environment variables.'},
    'astapdlg_choisir_exe': {'fr': "Choisir l'exécutable…", 'en': 'Choose the executable…'},
    'astapdlg_choisir_exe_aide': {'fr': 'Indiquer astap_cli (ou astap) installé ailleurs.', 'en': 'Point to astap_cli (or astap) installed elsewhere.'},
    'astapdlg_choisir_cat': {'fr': 'Choisir le catalogue…', 'en': 'Choose the catalogue…'},
    'astapdlg_choisir_cat_aide': {'fr': 'Indiquer le dossier qui contient les fichiers d80_*.1476 (ou d50_...).',
                                  'en': 'Point to the folder holding the d80_*.1476 (or d50_...) files.'},
    'astapdlg_oublier': {'fr': 'Oublier les chemins', 'en': 'Forget the paths'},
    'astapdlg_oublier_aide': {'fr': 'Revenir à la détection automatique.', 'en': 'Go back to automatic detection.'},
    'astapdlg_guide_aide': {'fr': "Guide d'installation pour ce système ; les liens ouvrent la page officielle de téléchargement.",
                            'en': 'Installation guide for this system; links open the official download page.'},

    # ------------------------------------------------------------ à propos, signalement, raccourcis
    'apropos_titre': {'fr': 'À propos de Coupole', 'en': 'About Coupole'},
    'apropos_aide': {'fr': 'Version, licence et configuration détectée.', 'en': 'Version, licence and detected configuration.'},
    'apropos_texte': {'fr': "Boîte à outils libre pour les étudiants du DU « Explorer et Comprendre l'Univers » "
                            "(Observatoire de Paris). Auteur : ARP273-ROSE.",
                      'en': "Free toolbox for students of the « Explorer et Comprendre l'Univers » diploma (Observatoire de "
                            "Paris). Author: ARP273-ROSE."},
    'apropos_credits': {'fr': "Données : banque « OHP student observations », Observatoire de Paris / PADC (Paris Astronomical "
                              "Data Centre), service TAP public, licence Etalab 2.0. Méthode : guide officiel de la base "
                              "(PADC-BDD-DU-ECU). Format XISF : spécification de Pleiades Astrophoto. ASTAP : Han Kleijn "
                              "(www.hnsky.org), facultatif, non inclus. Fiche en ligne : SIMBAD et Sesame "
                              "(CDS, Strasbourg), Aladin Lite, NED (NASA/IPAC), JPL Small-Body Database. Cosmologie : "
                              "noyau repris du calculateur « cosmologie-redshift » du même auteur, astropy.cosmology.",
                        'en': "Data: « OHP student observations » bank, Observatoire de Paris / PADC (Paris Astronomical Data "
                              "Centre), public TAP service, Etalab 2.0 licence. Method: official guide of the database "
                              "(PADC-BDD-DU-ECU). XISF format: Pleiades Astrophoto specification. ASTAP: Han Kleijn "
                              "(www.hnsky.org), optional, not included. Online record: SIMBAD and Sesame (CDS, "
                              "Strasbourg), Aladin Lite, NED (NASA/IPAC), JPL Small-Body Database. Cosmology: core "
                              "taken from the same author's « cosmologie-redshift » calculator, astropy.cosmology."},
    'apropos_licence': {'fr': 'Licence : GNU GPL version 3 ou ultérieure. Logiciel fourni sans garantie.',
                        'en': 'Licence: GNU GPL version 3 or later. Software provided without warranty.'},
    'apropos_config': {'fr': 'Système : {os}\nProcesseur : {cpu} ({p} cœurs, {l} logiques)\nMémoire : {ram} Go\n'
                             'Carte graphique : {gpu}\nPython : {python}\nASTAP : {astap}',
                       'en': 'System: {os}\nProcessor: {cpu} ({p} cores, {l} logical)\nMemory: {ram} GB\n'
                             'Graphics card: {gpu}\nPython: {python}\nASTAP: {astap}'},
    'signaler_titre': {'fr': 'Signaler un problème', 'en': 'Report a problem'},
    'signaler_texte': {'fr': "Décrire ce qui s'est passé et ce qui était attendu. Aucune donnée personnelle n'est jointe.",
                       'en': 'Describe what happened and what was expected. No personal data is attached.'},
    'signaler_zone_aide': {'fr': 'Votre description (4 000 caractères au plus).', 'en': 'Your description (4,000 characters at most).'},
    'signaler_diag': {'fr': 'Joindre la configuration (système, processeur, mémoire, ASTAP)', 'en': 'Attach the configuration (system, processor, memory, ASTAP)'},
    'signaler_diag_aide': {'fr': 'Aide à reproduire le problème ; rien de personnel.', 'en': 'Helps reproduce the problem; nothing personal.'},
    'signaler_envoyer': {'fr': 'Envoyer', 'en': 'Send'},
    'signaler_envoyer_aide': {'fr': 'Envoi anonyme au point de collecte.', 'en': 'Anonymous sending to the collection point.'},
    'signaler_fichier': {'fr': 'Enregistrer dans un fichier…', 'en': 'Save to a file…'},
    'signaler_fichier_aide': {'fr': 'Pour joindre le rapport à un courriel ou un message vous-même.', 'en': 'To attach the report to an e-mail or message yourself.'},
    'signaler_consentement': {'fr': "L'envoi des rapports n'est pas autorisé. L'autoriser maintenant ?",
                              'en': 'Sending reports is not allowed. Allow it now?'},
    'signaler_envoye': {'fr': 'Rapport envoyé (ou mis en file s\'il n\'y a pas de réseau). Merci.', 'en': 'Report sent (or queued if there is no network). Thank you.'},
    'racc_titre': {'fr': 'Raccourcis clavier', 'en': 'Keyboard shortcuts'},
    'racc_aide': {'fr': 'Raccourcis disponibles.', 'en': 'Available shortcuts.'},
    'racc_f1': {'fr': "Aide de l'écran affiché", 'en': 'Help on the screen shown'},
    'racc_manuel': {'fr': 'Manuel PDF', 'en': 'PDF manual'},
    'racc_modules': {'fr': 'Aller au module 1 … 9', 'en': 'Go to module 1 … 9'},
    'racc_reglages': {'fr': 'Préférences', 'en': 'Preferences'},
    'racc_astap': {'fr': 'Assistant ASTAP', 'en': 'ASTAP assistant'},
    'racc_apparence': {'fr': 'Thème clair / sombre', 'en': 'Light / dark theme'},
    'racc_actualiser': {'fr': "Banque OHP : rafraîchir l'inventaire", 'en': 'OHP bank: refresh the inventory'},
    'racc_quitter': {'fr': 'Quitter', 'en': 'Quit'},
    'maj_titre': {'fr': 'Mise à jour', 'en': 'Update'},
    'maj_question': {'fr': 'La version {version} est disponible. L\'installer maintenant ?', 'en': 'Version {version} is available. Install it now?'},
    'maj_redemarrer': {'fr': 'Mise à jour installée : Coupole va redémarrer.', 'en': 'Update installed: Coupole will restart.'},
    'maj_echec': {'fr': 'Mise à jour impossible : {erreur}', 'en': 'Update failed: {erreur}'},
# ------------------------------------------------------------ cartes
    'carte_attribution': {'fr': '© OpenStreetMap contributors', 'en': '© OpenStreetMap contributors'},
    'carte_hors_ligne': {'fr': 'Hors ligne : fond simple (carte © OpenStreetMap contributors quand le réseau revient)',
                         'en': 'Offline: plain background (map © OpenStreetMap contributors when the network is back)'},
    'carte_legende_ciel': {'fr': 'Aitoff, AD croissante vers la gauche, 12 h au centre — tirets dorés : écliptique ; pointillés : plan galactique',
                           'en': 'Aitoff, RA increasing to the left, 12 h at centre — gold dashes: ecliptic; dots: galactic plane'},
'reg_onglets_aide': {'fr': 'Réglages généraux et adresses des services.', 'en': 'General settings and service addresses.'},
    'reg_onglet_general': {'fr': 'Général', 'en': 'General'},
    'reg_onglet_sources': {'fr': 'Sources', 'en': 'Sources'},
    'reg_sources_intro': {'fr': "Adresses des services. Une valeur modifiée ici est « forcée » : ni une mise à jour ni le fichier "
                                "distant ne la remplacent. « Défaut » revient à la valeur livrée (ou publiée dans le dépôt).",
                          'en': "Service addresses. A value changed here is « forced »: neither an update nor the remote file "
                                "replaces it. « Default » goes back to the shipped (or published) value."},
    'reg_source_aide': {'fr': 'Adresse du service (modifiable).', 'en': 'Service address (editable).'},
    'reg_source_defaut': {'fr': 'Défaut', 'en': 'Default'},
    'reg_source_defaut_aide': {'fr': 'Revient à la valeur par défaut pour cette adresse.', 'en': 'Go back to the default value for this address.'},
    'reg_source_tester': {'fr': 'Tester', 'en': 'Test'},
    'reg_source_tester_aide': {'fr': 'Teste la connexion (une requête minuscule).', 'en': 'Test the connection (one tiny request).'},
    'reg_sources_reinit': {'fr': 'Tout revenir aux valeurs par défaut', 'en': 'Reset everything to defaults'},
    'reg_sources_reinit_aide': {'fr': 'Annule toutes les valeurs forcées.', 'en': 'Cancel every forced value.'},
    'reg_sources_distant': {'fr': 'Récupérer le fichier publié', 'en': 'Fetch the published file'},
    'reg_sources_distant_aide': {'fr': 'Télécharge maintenant le fichier de sources publié dans le dépôt (contrôle de forme, domaines autorisés).',
                                 'en': 'Download now the sources file published in the repository (shape check, allowed domains).'},
'cli_meta_id': {'fr': 'ID', 'en': 'ID'},
    'cli_meta_iso': {'fr': 'DATE_ISO', 'en': 'ISO_DATE'},
}
