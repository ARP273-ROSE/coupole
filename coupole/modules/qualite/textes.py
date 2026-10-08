"""Textes du module « Qualité des images » (FR/EN)."""

TEXTES = {
    'qual_absent': {'fr': "Le contrôle de qualité demande la bibliothèque SEP (Source Extractor en Python, LGPL, ≈ 1 Mo) : "
                          "pip install sep. Le reste de Coupole fonctionne sans elle.",
                    'en': 'The quality check needs the SEP library (Source Extractor in Python, LGPL, ≈ 1 MB): '
                          'pip install sep. The rest of Coupole works without it.'},
    'qual_cli': {'fr': 'mesure la qualité des images d\'un dossier (lots) ; jamais lancé automatiquement',
                 'en': 'measure the quality of the images of a folder (stacks); never run automatically'},
    'qual_aide_dossier': {'fr': 'dossier de lots (ou un fichier image)', 'en': 'folder of stacks (or one image file)'},
    'qual_aide_ecrire': {'fr': 'écrit QUALITE.csv et QUALITE.txt dans chaque lot', 'en': 'write QUALITE.csv and QUALITE.txt in each stack'},
    'qual_lot': {'fr': 'Lot {lot} : {n} image(s)', 'en': 'Stack {lot}: {n} image(s)'},
    'qual_choisir': {'fr': 'Choisir un dossier…', 'en': 'Choose a folder…'},
    'qual_choisir_aide': {'fr': 'Dossier de lots produit par la Banque OHP (ou tout dossier d\'images XISF/FITS).',
                          'en': 'Folder of stacks produced by the OHP bank (or any folder of XISF/FITS images).'},
    'qual_lancer': {'fr': 'Mesurer', 'en': 'Measure'},
    'qual_lancer_aide': {'fr': 'Mesure chaque image (hors du fil graphique) et écrit le rapport de chaque lot.',
                         'en': 'Measure each image (off the GUI thread) and write the report of each stack.'},
    'qual_arreter': {'fr': 'Arrêter', 'en': 'Stop'},
    'qual_arreter_aide': {'fr': 'Arrête après l\'image en cours.', 'en': 'Stop after the current image.'},
    'qual_table_aide': {'fr': 'Une ligne par image mesurée ; le résumé de chaque lot est dans QUALITE.txt.',
                        'en': 'One line per measured image; each stack summary is in QUALITE.txt.'},
    'qual_resume_aide': {'fr': 'Résumé du dernier lot mesuré.', 'en': 'Summary of the last stack measured.'},
    'qual_barre_aide': {'fr': 'Images mesurées.', 'en': 'Images measured.'},
    'qual_fini': {'fr': 'Terminé : {n} image(s) dans {lots} lot(s).', 'en': 'Done: {n} image(s) in {lots} stack(s).'},
    'qual_col_fichier': {'fr': 'fichier', 'en': 'file'},
    'qual_col_etoiles': {'fr': 'étoiles mesurées', 'en': 'stars measured'},
    'qual_col_fwhm_px': {'fr': 'FWHM (px)', 'en': 'FWHM (px)'},
    'qual_col_fwhm_arcsec': {'fr': 'FWHM (″)', 'en': 'FWHM (″)'},
    'qual_col_ellipticite': {'fr': 'ellipticité', 'en': 'ellipticity'},
    'qual_col_fond_adu': {'fr': 'fond (ADU)', 'en': 'background (ADU)'},
    'qual_col_fond_adu_s': {'fr': 'fond (ADU/s)', 'en': 'background (ADU/s)'},
    'qual_col_bruit_adu': {'fr': 'bruit du fond (ADU)', 'en': 'background noise (ADU)'},
    'qual_col_rsn': {'fr': 'RSN médian', 'en': 'median SNR'},
    'qual_col_gradient_pct': {'fr': 'gradient (%)', 'en': 'gradient (%)'},
    'qual_col_residu_pct': {'fr': 'résidu du fond (%)', 'en': 'background residual (%)'},
    'qual_col_satures': {'fr': 'étoiles saturées', 'en': 'saturated stars'},
    'qual_col_trainees': {'fr': 'traînées', 'en': 'trails'},
    'qual_col_echantillonnage': {'fr': 'échantillonnage', 'en': 'sampling'},
    'qual_ech_sous': {'fr': 'sous-échantillonné (FWHM < 2 px)', 'en': 'undersampled (FWHM < 2 px)'},
    'qual_ech_correct': {'fr': 'correct (FWHM de 2 à 5 px)', 'en': 'adequate (FWHM 2 to 5 px)'},
    'qual_ech_sur': {'fr': 'sur-échantillonné (FWHM > 5 px)', 'en': 'oversampled (FWHM > 5 px)'},
    'qual_resume_titre': {'fr': 'Qualité : {n} image(s), {mesurees} mesurée(s).', 'en': 'Quality: {n} image(s), {mesurees} measured.'},
    'qual_resume_aucune': {'fr': 'Aucune étoile mesurable (champ pauvre, pose trop courte ou image sans étoile ponctuelle).',
                           'en': 'No measurable star (poor field, exposure too short or no point-like star).'},
    'qual_resume_fwhm': {'fr': 'FWHM médiane : {med} px ({arc}″) ; de {mini} à {maxi} px selon les poses.',
                         'en': 'Median FWHM: {med} px ({arc}″); from {mini} to {maxi} px across exposures.'},
    'qual_resume_ellipticite': {'fr': 'Ellipticité médiane : {med}.', 'en': 'Median ellipticity: {med}.'},
    'qual_resume_fond': {'fr': 'Fond médian : {fond} ADU ; bruit du fond : {bruit} ADU.', 'en': 'Median background: {fond} ADU; background noise: {bruit} ADU.'},
    'qual_resume_pires': {'fr': 'Poses les plus floues : {liste}.', 'en': 'Blurriest exposures: {liste}.'},
    'qual_resume_satures': {'fr': 'Étoiles saturées (toutes poses) : {n}.', 'en': 'Saturated stars (all exposures): {n}.'},
    'qual_resume_trainees': {'fr': 'Traînées probables (satellites, avions) dans : {liste}.', 'en': 'Probable trails (satellites, aircraft) in: {liste}.'},
    'qual_resume_echantillonnage': {'fr': 'Échantillonnage : {v}.', 'en': 'Sampling: {v}.'},
    'qual_resume_carte': {'fr': 'FWHM médiane par neuvième de champ (px ; en haut de la carte = première ligne du fichier) :',
                          'en': 'Median FWHM per ninth of the field (px; top of the map = first row of the file):'},
    'qual_resume_carte_limite': {'fr': "Une FWHM qui croît vers un bord ou un coin peut venir d'un basculement du capteur, d'une "
                                       "courbure de champ ou de la collimation ; elle peut aussi venir de la turbulence, du suivi "
                                       "ou de la mise au point. Cette carte ne suffit pas à trancher.",
                                 'en': 'A FWHM growing towards an edge or corner may come from sensor tilt, field curvature or '
                                       'collimation; it may also come from seeing, tracking or focus. This map alone cannot tell.'},
    'qual_resume_prudence': {'fr': "Mesures indicatives : fond en ADU (pas de point zéro photométrique, donc pas de mag/arcsec²) ; "
                                   "RSN donné seulement quand le gain est dans l'en-tête.",
                             'en': 'Indicative measurements: background in ADU (no photometric zero point, hence no mag/arcsec²); '
                                   'SNR given only when the gain is in the header.'},
    'qual_aide_html': {'fr': "<h3>Qualité des images (facultatif)</h3><p>Mesures faites avec SEP (Source Extractor en Python) et "
                             "numpy, validées sur images synthétiques à paramètres connus (FWHM à mieux que 2 % pour des profils "
                             "gaussiens et de Moffat de 2,5 à 7 px, ellipticité à ± 0,02, fond à 0,5 %, bruit à 5 %).</p>"
                             "<p>Fond, bruit, FWHM et ellipticité (médianes et carte 3 × 3), gradient du fond et résidu "
                             "(vignetage, flat), étoiles saturées, traînées, échantillonnage. Pas de mag/arcsec² (pas de point "
                             "zéro), pas de RSN sans gain, pas de détection de « donuts » (méthode non validée).</p>"
                             "<p>Rapport par lot : QUALITE.csv et QUALITE.txt. Jamais lancé automatiquement.</p>",
                       'en': "<h3>Image quality (optional)</h3><p>Measurements made with SEP (Source Extractor in Python) and "
                             "numpy, validated on synthetic images with known parameters (FWHM better than 2 % for Gaussian and "
                             "Moffat profiles from 2.5 to 7 px, ellipticity ± 0.02, background 0.5 %, noise 5 %).</p>"
                             "<p>Background, noise, FWHM and ellipticity (medians and 3 × 3 map), background gradient and "
                             "residual (vignetting, flat), saturated stars, trails, sampling. No mag/arcsec² (no zero point), no "
                             "SNR without gain, no dust-donut detection (method not validated).</p><p>Report per stack: "
                             "QUALITE.csv and QUALITE.txt. Never run automatically.</p>"},
}
