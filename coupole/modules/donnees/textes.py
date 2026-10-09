"""Textes du module « Spectres et séries » (FR/EN)."""

TEXTES = {
    'don_ouvrir': {'fr': 'Ouvrir un fichier…', 'en': 'Open a file…'},
    'don_ouvrir_aide': {'fr': 'FITS (image 1D avec axe WCS, cube radio 1×1×N, table binaire) ou CSV/texte en colonnes.',
                        'en': 'FITS (1D image with WCS axis, 1×1×N radio cube, binary table) or CSV/text in columns.'},
    'don_liste_aide': {'fr': 'Contenu du fichier : une ligne par extension utile.', 'en': 'File contents: one line per useful extension.'},
    'don_axe': {'fr': 'Axe horizontal', 'en': 'Horizontal axis'},
    'don_axe_aide': {'fr': "Pour un spectre en fréquence : fréquence, ou vitesse radio v = c (1 − f/f0).",
                     'en': 'For a frequency spectrum: frequency, or radio velocity v = c (1 − f/f0).'},
    'don_axe_brut': {'fr': 'Axe du fichier', 'en': 'File axis'},
    'don_axe_mhz': {'fr': 'Fréquence (MHz)', 'en': 'Frequency (MHz)'},
    'don_axe_vitesse': {'fr': 'Vitesse radio (km/s)', 'en': 'Radio velocity (km/s)'},
    'don_f0': {'fr': 'Fréquence de repos f0 (MHz)', 'en': 'Rest frequency f0 (MHz)'},
    'don_f0_aide': {'fr': "Lue dans RESTFRQ si présente ; sinon raie H I à 1 420,405 751 768 MHz.",
                    'en': 'Read from RESTFRQ when present; otherwise the H I line at 1,420.405751768 MHz.'},
    'don_colx': {'fr': 'Colonne x', 'en': 'x column'},
    'don_colx_aide': {'fr': 'Colonne de la table pour l\'axe horizontal.', 'en': 'Table column for the horizontal axis.'},
    'don_coly': {'fr': 'Colonne y', 'en': 'y column'},
    'don_coly_aide': {'fr': 'Colonne de la table pour l\'axe vertical.', 'en': 'Table column for the vertical axis.'},
    'don_trace_aide': {'fr': 'Survol : valeur au curseur.', 'en': 'Hover: value under the cursor.'},
    'don_exporter': {'fr': 'Exporter en CSV…', 'en': 'Export as CSV…'},
    'don_recents': {'fr': 'Récents', 'en': 'Recent'},
    'don_recents_aide': {'fr': 'Les 10 derniers fichiers ouverts (gardés d\'une fermeture à l\'autre).',
                         'en': 'The last 10 files opened (kept from one session to the next).'},
    'don_recent_absent': {'fr': '(introuvable)', 'en': '(not found)'},
    'don_recents_vider': {'fr': 'Vider la liste', 'en': 'Clear the list'},
    'don_recents_vider_aide': {'fr': 'Oublie les fichiers récents (les fichiers eux-mêmes ne sont pas touchés).',
                               'en': 'Forget the recent files (the files themselves are not touched).'},
    'don_exporter_aide': {'fr': 'Enregistre les deux colonnes affichées (avec la vitesse si elle est affichée).',
                          'en': 'Save the two displayed columns (with the velocity when it is displayed).'},
    'don_aucun': {'fr': 'Aucun fichier ouvert.', 'en': 'No file open.'},
    'don_lecture': {'fr': 'Lecture de {fichier}…', 'en': 'Reading {fichier}…'},
    'don_info': {'fr': '{genre} — {n} points — {x}', 'en': '{genre} — {n} points — {x}'},
    'don_genre_image': {'fr': 'image', 'en': 'image'},
    'don_genre_spectre': {'fr': 'spectre', 'en': 'spectrum'},
    'don_genre_serie': {'fr': 'série', 'en': 'series'},
    'don_genre_table': {'fr': 'table', 'en': 'table'},
    'don_referentiel': {'fr': 'Référentiel des vitesses : celui de l\'axe des fréquences ({specsys}) ; aucune correction implicite (LSR, barycentre).',
                        'en': 'Velocity frame: that of the frequency axis ({specsys}); no implicit correction (LSR, barycentre).'},
    'don_inconnu': {'fr': 'non précisé', 'en': 'not stated'},
    'don_erreur': {'fr': 'Lecture impossible : {erreur}', 'en': 'Cannot read: {erreur}'},
    'don_image_ici': {'fr': 'Image {forme} : à ouvrir dans un logiciel d\'images (ce module trace les données 1D).',
                      'en': 'Image {forme}: open it in an image program (this module plots 1D data).'},
    'don_aide_html': {'fr': "<h3>Spectres et séries</h3><p>Lecture de données 1D : spectres (radioastronomie H I à 21 cm par "
                            "exemple), courbes de lumière, tables. Formats : FITS (axe WCS linéaire CRVAL/CDELT/CRPIX, "
                            "cubes 1×1×N, tables binaires), CSV ou texte en colonnes (en-tête facultatif).</p>"
                            "<p>Vitesse radio : v = c (1 − f/f0), convention radio de la norme FITS. Le référentiel est celui "
                            "de l'axe des fréquences (mot-clé SPECSYS) : Coupole ne corrige ni du LSR ni du barycentre.</p>"
                            "<p>Ajouter un format : voir CONTRIBUTING.md (« Ajouter un format »).</p>",
                      'en': "<h3>Spectra and series</h3><p>Reading 1D data: spectra (21 cm H I radio astronomy for instance), "
                            "light curves, tables. Formats: FITS (linear WCS axis CRVAL/CDELT/CRPIX, 1×1×N cubes, binary "
                            "tables), CSV or text in columns (header optional).</p><p>Radio velocity: v = c (1 − f/f0), FITS "
                            "radio convention. The frame is that of the frequency axis (SPECSYS keyword): Coupole corrects "
                            "for neither LSR nor barycentre.</p><p>Adding a format: see CONTRIBUTING.md (« Adding a format »).</p>"},
    'don_cli_lire': {'fr': 'décrit le contenu d\'un fichier (FITS, CSV)', 'en': 'describe the contents of a file (FITS, CSV)'},
    'don_cli_exporter': {'fr': 'exporte un spectre ou une série en CSV', 'en': 'export a spectrum or a series as CSV'},
    'don_aide_fichier': {'fr': 'fichier à lire', 'en': 'file to read'},
    'don_aide_vitesse': {'fr': 'ajoute la vitesse radio (spectre en fréquence)', 'en': 'add the radio velocity (frequency spectrum)'},
    'don_aide_f0': {'fr': 'fréquence de repos en MHz (défaut : RESTFRQ, sinon H I)', 'en': 'rest frequency in MHz (default: RESTFRQ, else H I)'},
    'don_aide_hdu': {'fr': 'numéro de la donnée dans le fichier (défaut : la première 1D)', 'en': 'index of the dataset in the file (default: the first 1D one)'},
    'don_formats': {'fr': 'Formats reconnus : {liste}', 'en': 'Recognised formats: {liste}'},
}
