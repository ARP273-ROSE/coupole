"""Textes FR/EN des animations du lot 3 (lumière et spectres, exoplanètes, étoiles doubles et variables, Système
solaire, Soleil, Voie lactée, cosmologie, télescopes) : (fr, en).  Fusionnés dans ``textes.TEXTES``."""

ANIM_LOT3 = {
    # ------------------------------------------------------------ communs
    'anim_c_pic_wien': ('Maximum (loi de Wien)', 'Peak (Wien’s law)'),
    'anim_c_exitance': ('Puissance par m² (σT⁴)', 'Power per m² (σT⁴)'),
    'anim_c_lambda_nm': ('longueur d’onde (nm)', 'wavelength (nm)'),
    'anim_c_luminance_unite': ('luminance (TW m⁻² sr⁻¹ m⁻¹)', 'radiance (TW m⁻² sr⁻¹ m⁻¹)'),
    'anim_c_intensite': ('intensité', 'intensity'),
    'anim_c_phase': ('Phase', 'Phase'),
    'anim_c_periode': ('Période', 'Period'),
    'anim_c_temps': ('Temps', 'Time'),
    'anim_c_ans': ('ans', 'years'),
    'anim_c_jours': ('jours', 'days'),
    'anim_c_heures': ('heures', 'hours'),
    'anim_c_flux_relatif': ('flux relatif', 'relative flux'),
    'anim_c_vitesse_radiale': ('vitesse radiale (m/s)', 'radial velocity (m/s)'),
    'anim_c_observateur': ('observateur', 'observer'),
    'anim_c_vers_observateur': ('vers l’observateur', 'to the observer'),
    'anim_c_etoile': ('étoile', 'star'),
    'anim_c_planete': ('planète', 'planet'),
    'anim_c_barycentre': ('centre de masse', 'center of mass'),
    'anim_c_libre': ('réglages libres', 'free settings'),
    'anim_c_aucun': ('aucun', 'none'),
    'anim_c_ua': ('ua', 'au'),

    # ------------------------------------------------------------ meltednail
    'anim_meltednail_temperature': ('Température', 'Temperature'),
    'anim_meltednail_temperature_aide': ('Température du clou (300 à 2 000 K). La lecture fait chauffer le clou jusqu’à '
                                         'la fusion du fer (1 811 K), puis le laisse refroidir.',
                                         'Temperature of the nail (300 to 2,000 K). Playing heats the nail up to the '
                                         'melting point of iron (1,811 K), then lets it cool down.'),
    'anim_meltednail_echelle_fixe': ('Échelle fixe', 'Fixed scale'),
    'anim_meltednail_echelle_fixe_aide': ('Garder l’échelle verticale de la courbe à 1 811 K (on voit la courbe grandir '
                                          'avec la température) ; sinon, l’échelle suit la courbe.',
                                          'Keep the vertical scale of the 1,811 K curve (the curve is seen to grow '
                                          'with temperature); otherwise the scale follows the curve.'),
    'anim_meltednail_temperature_v': ('Température', 'Temperature'),
    'anim_meltednail_visible': ('Part rayonnée dans le visible', 'Share radiated in the visible'),
    'anim_meltednail_titre_clou': ('Le clou', 'The nail'),
    'anim_meltednail_titre_courbe': ('Courbe du corps noir (loi de Planck)', 'Blackbody curve (Planck’s law)'),
    'anim_meltednail_invisible': ('presque tout le rayonnement est infrarouge : invisible',
                                  'nearly all the radiation is infrared: invisible'),
    'anim_meltednail_fusion': ('le fer fond (1 811 K)', 'iron melts (1,811 K)'),
}

ANIM_LOT3.update({
    # ------------------------------------------------------------ bbexplorer
    'anim_bbexplorer_courbe': ('Courbe', 'Curve'),
    'anim_bbexplorer_courbe_aide': ('Courbe à régler (jusqu’à cinq courbes de corps noir).',
                                    'Curve to adjust (up to five blackbody curves).'),
    'anim_bbexplorer_temperature': ('Température', 'Temperature'),
    'anim_bbexplorer_temperature_aide': ('Température de la courbe choisie (3 000 à 25 000 K, échelle logarithmique).',
                                         'Temperature of the selected curve (3,000 to 25,000 K, logarithmic scale).'),
    'anim_bbexplorer_ajouter': ('Ajouter une courbe', 'Add a curve'),
    'anim_bbexplorer_ajouter_aide': ('Ajouter une courbe à la température actuelle (cinq au plus).',
                                     'Add a curve at the current temperature (five at most).'),
    'anim_bbexplorer_retirer': ('Retirer la courbe', 'Remove the curve'),
    'anim_bbexplorer_retirer_aide': ('Retirer la courbe choisie (il en reste toujours une).',
                                     'Remove the selected curve (one always remains).'),
    'anim_bbexplorer_lambda_max': ('Axe jusqu’à', 'Axis up to'),
    'anim_bbexplorer_lambda_max_aide': ('Longueur d’onde au bord droit du graphe (1 000 à 5 000 nm).',
                                        'Wavelength at the right edge of the plot (1,000 to 5,000 nm).'),
    'anim_bbexplorer_echelle': ('Échelle verticale', 'Vertical scale'),
    'anim_bbexplorer_echelle_aide': ('Ajuster l’échelle à toutes les courbes, à la courbe choisie, ou la figer.',
                                     'Fit the scale to all curves, to the selected curve, or lock it.'),
    'anim_bbexplorer_e_toutes': ('toutes les courbes', 'all curves'),
    'anim_bbexplorer_e_choisie': ('courbe choisie', 'selected curve'),
    'anim_bbexplorer_e_fixe': ('figée', 'locked'),
    'anim_bbexplorer_aire': ('Aire sous la courbe', 'Area under the curve'),
    'anim_bbexplorer_aire_aide': ('Colorier l’aire sous la courbe choisie : elle vaut σT⁴/π, la puissance rayonnée '
                                  'croît comme la puissance quatrième de la température.',
                                  'Shade the area under the selected curve: it equals σT⁴/π, the radiated power grows '
                                  'as the fourth power of temperature.'),
    'anim_bbexplorer_pic': ('Maximum', 'Peak'),
    'anim_bbexplorer_pic_aide': ('Marquer la longueur d’onde du maximum (loi de Wien).',
                                 'Mark the peak wavelength (Wien’s law).'),
    'anim_bbexplorer_filtres': ('Filtres U, B, V, R', 'U, B, V, R filters'),
    'anim_bbexplorer_filtres_aide': ('Montrer la part de la courbe choisie que laisse passer chaque filtre, les '
                                     'magnitudes et les indices de couleur.',
                                     'Show the part of the selected curve passed by each filter, the magnitudes and '
                                     'the color indices.'),
    'anim_bbexplorer_titre': ('Courbes du corps noir', 'Blackbody curves'),
    'anim_bbexplorer_titre_filtres': ('Filtres', 'Filters'),
    'anim_bbexplorer_magnitudes': ('magnitudes', 'magnitudes'),
    'anim_bbexplorer_pic_a': ('maximum à {l} nm', 'peak at {l} nm'),
    'anim_bbexplorer_temperature_v': ('Température (courbe choisie)', 'Temperature (selected curve)'),
    'anim_bbexplorer_rapport_soleil': ('Puissance par m², rapportée au Soleil', 'Power per m², relative to the Sun'),
})
for _k in range(1, 6):
    ANIM_LOT3['anim_bbexplorer_courbe_%d' % _k] = ('courbe %d' % _k, 'curve %d' % _k)

ANIM_LOT3.update({
    # ------------------------------------------------------------ spectrum010
    'anim_spectrum010_mode': ('Spectre', 'Spectrum'),
    'anim_spectrum010_mode_aide': ('Spectre continu (corps chaud et dense), d’émission (gaz chaud et peu dense : raies '
                                   'brillantes) ou d’absorption (lumière d’une étoile traversant son atmosphère plus '
                                   'froide : raies sombres).',
                                   'Continuous spectrum (hot dense body), emission (hot thin gas: bright lines) or '
                                   'absorption (starlight crossing its cooler atmosphere: dark lines).'),
    'anim_spectrum010_continu': ('continu', 'continuous'),
    'anim_spectrum010_emission': ('d’émission', 'emission'),
    'anim_spectrum010_absorption': ('d’absorption', 'absorption'),
    'anim_spectrum010_type': ('Type spectral', 'Spectral type'),
    'anim_spectrum010_type_aide': ('Type spectral de l’étoile, de O0 (les plus chaudes) à M9 (les plus froides) : '
                                   'l’intensité des raies de chaque famille en dépend.',
                                   'Spectral type of the star, from O0 (hottest) to M9 (coolest): the strength of each '
                                   'family of lines depends on it.'),
    'anim_spectrum010_classe': ('Classe de luminosité', 'Luminosity class'),
    'anim_spectrum010_classe_aide': ('Supergéante (I), géante (III) ou naine de la séquence principale (V) : les raies '
                                     'des supergéantes, à l’atmosphère peu dense, sont plus fines.',
                                     'Supergiant (I), giant (III) or main-sequence dwarf (V): the lines of supergiants, '
                                     'whose atmospheres are thin, are narrower.'),
    'anim_spectrum010_mode_v': ('Spectre', 'Spectrum'),
    'anim_spectrum010_type_v': ('Type', 'Type'),
    'anim_spectrum010_fortes': ('Raies fortes', 'Strong lines'),
    'anim_spectrum010_titre_continu': ('Spectre continu', 'Continuous spectrum'),
    'anim_spectrum010_titre_emission': ('Spectre d’émission', 'Emission spectrum'),
    'anim_spectrum010_titre_absorption': ('Spectre d’absorption', 'Absorption spectrum'),
    'anim_spectrum010_titre_intensites': ('Intensité des raies selon le type spectral',
                                          'Line strengths versus spectral type'),
})
for _f, _fr, _en in (('he_ii', 'Hélium ionisé', 'Ionized helium'), ('he_i', 'Hélium neutre', 'Neutral helium'),
                     ('h', 'Hydrogène', 'Hydrogen'), ('metaux_ionises', 'Métaux ionisés', 'Ionized metals'),
                     ('metaux', 'Métaux neutres', 'Neutral metals'), ('molecules', 'Molécules', 'Molecules')):
    ANIM_LOT3['anim_spectrum010_f_' + _f] = (_fr, _en)
    ANIM_LOT3['anim_spectrum010_f_' + _f + '_aide'] = ('Montrer les raies : %s.' % _fr.lower(),
                                                       'Show the lines: %s.' % _en.lower())

ANIM_LOT3.update({
    # ------------------------------------------------------------ emspectrum
    'anim_emspectrum_log_lambda': ('log₁₀ λ (λ en m)', 'log₁₀ λ (λ in m)'),
    'anim_emspectrum_log_lambda_aide': ('Logarithme décimal de la longueur d’onde en mètres : −16 (rayons gamma de très '
                                        'haute énergie) à 4 (ondes radio de 10 km). On peut aussi cliquer ou glisser '
                                        'sur la bande du spectre.',
                                        'Decimal logarithm of the wavelength in metres: −16 (very high energy gamma '
                                        'rays) to 4 (10 km radio waves). One can also click or drag on the spectrum '
                                        'band.'),
    'anim_emspectrum_domaine': ('Domaine', 'Band'),
    'anim_emspectrum_lambda_v': ('Longueur d’onde', 'Wavelength'),
    'anim_emspectrum_frequence': ('Fréquence (c / λ)', 'Frequency (c / λ)'),
    'anim_emspectrum_energie': ('Énergie d’un photon (h ν)', 'Photon energy (h ν)'),
    'anim_emspectrum_temperature': ('Corps noir dont c’est le maximum', 'Blackbody peaking there'),
    'anim_emspectrum_objet': ('Taille comparable', 'Comparable size'),
    'anim_emspectrum_titre_onde': ('L’onde, à côté d’un objet de même taille', 'The wave, next to an object of the same size'),
})
for _k, _fr, _en, _cfr, _cen in (('gamma', 'rayons gamma', 'gamma rays', 'γ', 'γ'), ('x', 'rayons X', 'X-rays', 'X', 'X'),
                                 ('uv', 'ultraviolet', 'ultraviolet', 'UV', 'UV'), ('visible', 'visible', 'visible', 'vis.', 'vis.'),
                                 ('ir_proche', 'proche infrarouge', 'near infrared', 'PIR', 'NIR'),
                                 ('ir', 'infrarouge', 'infrared', 'IR', 'IR'),
                                 ('micro_ondes', 'micro-ondes', 'microwaves', 'micro-ondes', 'microwaves'),
                                 ('radio', 'ondes radio', 'radio waves', 'radio', 'radio')):
    ANIM_LOT3['anim_emspectrum_d_' + _k] = (_fr, _en)
    ANIM_LOT3['anim_emspectrum_c_' + _k] = (_cfr, _cen)
for _k, _fr, _en in (('noyau', 'noyau d’atome', 'atomic nucleus'), ('atome', 'atome', 'atom'),
                     ('molecule', 'petite molécule', 'small molecule'), ('virus', 'virus', 'virus'),
                     ('bacterie', 'bactérie', 'bacterium'), ('cellule', 'cellule', 'cell'),
                     ('cheveu', 'épaisseur d’un cheveu', 'width of a hair'), ('tete_epingle', 'tête d’épingle', 'pinhead'),
                     ('fourmi', 'fourmi', 'ant'), ('balle', 'balle de tennis', 'tennis ball'), ('humain', 'humain', 'human'),
                     ('immeuble', 'immeuble', 'building'), ('montagne', 'montagne', 'mountain')):
    ANIM_LOT3['anim_emspectrum_o_' + _k] = (_fr, _en)

ANIM_LOT3.update({
    # ------------------------------------------------------------ dopplershift
    'anim_dopplershift_vitesse': ('Vitesse de la source', 'Source speed'),
    'anim_dopplershift_vitesse_aide': ('Vitesse de la source en fraction de la vitesse c de l’onde (0 à 0,9). La source '
                                       'fait des allers et retours.',
                                       'Speed of the source as a fraction of the wave speed c (0 to 0.9). The source '
                                       'moves back and forth.'),
    'anim_dopplershift_direction': ('Direction', 'Direction'),
    'anim_dopplershift_direction_aide': ('Direction du mouvement de la source (0° : horizontale, 90° : verticale).',
                                         'Direction of the source motion (0°: horizontal, 90°: vertical).'),
    'anim_dopplershift_emission': ('Émission', 'Emission'),
    'anim_dopplershift_emission_aide': ('La source émet des ondes (décocher : elle se tait, les crêtes déjà émises '
                                        'continuent leur chemin).',
                                        'The source emits waves (untick: it falls silent, the crests already emitted '
                                        'keep travelling).'),
    'anim_dopplershift_trajectoire': ('Trajectoire', 'Path'),
    'anim_dopplershift_trajectoire_aide': ('Montrer le segment parcouru par la source.', 'Show the segment travelled by '
                                           'the source.'),
    'anim_dopplershift_f0': ('Fréquence émise f₀', 'Emitted frequency f₀'),
    'anim_dopplershift_vr': ('Vitesse de la source vers l’observateur', 'Source speed toward the observer'),
    'anim_dopplershift_f_recue': ('Fréquence reçue (mesurée)', 'Received frequency (measured)'),
    'anim_dopplershift_f_formule': ('f₀ / (1 − v_r / c)', 'f₀ / (1 − v_r / c)'),
    'anim_dopplershift_titre_emis': ('Signal émis par la source', 'Signal emitted by the source'),
    'anim_dopplershift_titre_recu': ('Signal reçu par l’observateur (on peut le faire glisser)',
                                     'Signal received by the observer (who can be dragged)'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ filters
    'anim_filters_source': ('Source', 'Source'),
    'anim_filters_source_aide': ('Spectre de la lumière émise : corps noir (loi de Planck), gaussienne, ou Soleil vu '
                                 'hors de l’atmosphère.',
                                 'Spectrum of the emitted light: blackbody (Planck’s law), Gaussian, or the Sun seen '
                                 'from above the atmosphere.'),
    'anim_filters_s_corps_noir': ('corps noir', 'blackbody'),
    'anim_filters_s_gauss': ('gaussienne', 'Gaussian'),
    'anim_filters_s_soleil': ('Soleil', 'Sun'),
    'anim_filters_temperature': ('Température', 'Temperature'),
    'anim_filters_temperature_aide': ('Température du corps noir (2 000 à 30 000 K).',
                                      'Temperature of the blackbody (2,000 to 30,000 K).'),
    'anim_filters_pic': ('Centre', 'Center'),
    'anim_filters_pic_aide': ('Longueur d’onde du maximum de la source gaussienne.',
                              'Wavelength of the peak of the Gaussian source.'),
    'anim_filters_largeur': ('Largeur', 'Width'),
    'anim_filters_largeur_aide': ('Largeur à mi-hauteur de la source gaussienne.',
                                  'Full width at half maximum of the Gaussian source.'),
    'anim_filters_filtre_centre': ('Centre du filtre', 'Filter center'),
    'anim_filters_filtre_centre_aide': ('Longueur d’onde où le filtre gaussien laisse tout passer.',
                                        'Wavelength at which the Gaussian filter passes everything.'),
    'anim_filters_filtre_largeur': ('Largeur du filtre', 'Filter width'),
    'anim_filters_filtre_largeur_aide': ('Largeur à mi-hauteur du filtre gaussien.',
                                         'Full width at half maximum of the Gaussian filter.'),
    'anim_filters_transmis': ('Lumière visible transmise', 'Visible light transmitted'),
    'anim_filters_transmis_tout': ('Lumière transmise (200 à 1 100 nm)', 'Light transmitted (200 to 1,100 nm)'),
    'anim_filters_titre_source': ('Source', 'Source'),
    'anim_filters_titre_filtres': ('Filtres (transmission combinée)', 'Filters (combined transmission)'),
    'anim_filters_titre_detecteur': ('Ce qui atteint le détecteur', 'What reaches the detector'),
    'anim_filters_couleur': ('couleur perçue', 'perceived color'),
})
for _f, _fr, _en in (('U', 'U (ultraviolet)', 'U (ultraviolet)'), ('B', 'B (bleu)', 'B (blue)'),
                     ('V', 'V (visuel)', 'V (visual)'), ('R', 'R (rouge)', 'R (red)'),
                     ('atmosphere', 'Atmosphère', 'Atmosphere'), ('gauss', 'Filtre gaussien', 'Gaussian filter')):
    ANIM_LOT3['anim_filters_f_' + _f] = (_fr, _en)
    ANIM_LOT3['anim_filters_f_' + _f + '_aide'] = ('Placer ce filtre devant le détecteur (les filtres choisis se '
                                                   'multiplient).',
                                                   'Put this filter in front of the detector (the chosen filters '
                                                   'multiply).')

ANIM_LOT3.update({
    # ------------------------------------------------------------ hydrogenatom
    'anim_hydrogenatom_energie': ('Énergie du photon', 'Photon energy'),
    'anim_hydrogenatom_energie_aide': ('Énergie du prochain photon tiré (0,5 à 14 eV). Il n’est absorbé que s’il '
                                       'correspond à un écart entre deux niveaux (à 0,01 eV près ici), ou s’il suffit '
                                       'à ioniser l’atome.',
                                       'Energy of the next photon fired (0.5 to 14 eV). It is absorbed only if it '
                                       'matches a gap between two levels (within 0.01 eV here), or if it is enough to '
                                       'ionize the atom.'),
    'anim_hydrogenatom_transition': ('Transition', 'Transition'),
    'anim_hydrogenatom_transition_aide': ('Transition dont on veut tirer le photon (séries de Lyman, Balmer, Paschen).',
                                          'Transition whose photon is to be fired (Lyman, Balmer, Paschen series).'),
    'anim_hydrogenatom_tirer': ('Tirer le photon', 'Fire the photon'),
    'anim_hydrogenatom_tirer_aide': ('Envoyer sur l’atome un photon de l’énergie choisie.',
                                     'Send a photon of the chosen energy at the atom.'),
    'anim_hydrogenatom_tirer_transition': ('Tirer le photon de la transition', 'Fire the transition photon'),
    'anim_hydrogenatom_tirer_transition_aide': ('Régler l’énergie sur la transition choisie et tirer le photon.',
                                                'Set the energy to the chosen transition and fire the photon.'),
    'anim_hydrogenatom_niveau': ('Niveau de l’électron', 'Electron level'),
    'anim_hydrogenatom_ionise': ('ionisé (électron libre)', 'ionized (free electron)'),
    'anim_hydrogenatom_photon': ('Photon', 'Photon'),
    'anim_hydrogenatom_e_niveau': ('Énergie du niveau', 'Level energy'),
    'anim_hydrogenatom_dernier': ('Dernier événement', 'Last event'),
    'anim_hydrogenatom_titre_atome': ('L’atome (rayons des orbites ∝ n²)', 'The atom (orbit radii ∝ n²)'),
    'anim_hydrogenatom_titre_niveaux': ('Niveaux d’énergie', 'Energy levels'),
    'anim_hydrogenatom_ionisation': ('ionisation (0 eV)', 'ionization (0 eV)'),
    'anim_hydrogenatom_j_tir': ('photon de {e} eV tiré', '{e} eV photon fired'),
    'anim_hydrogenatom_j_absorbe': ('absorbé : niveau {a} → {b}', 'absorbed: level {a} → {b}'),
    'anim_hydrogenatom_j_ionise': ('ionisation depuis le niveau {a} (électron libre, {k} eV)',
                                   'ionization from level {a} (free electron, {k} eV)'),
    'anim_hydrogenatom_j_passe': ('pas absorbé : le photon traverse', 'not absorbed: the photon passes through'),
    'anim_hydrogenatom_j_emet': ('émission : niveau {a} → {b} ({l} nm)', 'emission: level {a} → {b} ({l} nm)'),
    'anim_hydrogenatom_j_recombine': ('recombinaison sur le niveau {b}', 'recombination onto level {b}'),
})
for _a, _b in [(a, b) for a in (1, 2, 3) for b in range(a + 1, 7)]:
    _s = {1: ('Lyman', 'Lyman'), 2: ('Balmer', 'Balmer'), 3: ('Paschen', 'Paschen')}[_a]
    ANIM_LOT3['anim_hydrogenatom_t_%d_%d' % (_a, _b)] = ('%d → %d (%s)' % (_a, _b, _s[0]), '%d → %d (%s)' % (_a, _b, _s[1]))

ANIM_LOT3.update({
    # ------------------------------------------------------------ threeviewsspectra
    'anim_threeviewsspectra_position': ('Position du télescope', 'Telescope position'),
    'anim_threeviewsspectra_position_aide': ('Angle du télescope sur son cercle autour du nuage (on peut aussi le faire '
                                             'glisser).',
                                             'Angle of the telescope on its circle around the cloud (it can also be '
                                             'dragged).'),
    'anim_threeviewsspectra_cible': ('Viser', 'Aim at'),
    'anim_threeviewsspectra_cible_aide': ('Ce que vise le télescope : le nuage de gaz ou l’ampoule.',
                                          'What the telescope aims at: the gas cloud or the light bulb.'),
    'anim_threeviewsspectra_v_nuage': ('le nuage', 'the cloud'),
    'anim_threeviewsspectra_v_ampoule': ('l’ampoule', 'the bulb'),
    'anim_threeviewsspectra_gaz': ('Gaz du nuage', 'Gas of the cloud'),
    'anim_threeviewsspectra_gaz_aide': ('Élément du nuage : ses raies d’émission et d’absorption sont aux mêmes '
                                        'longueurs d’onde.',
                                        'Element of the cloud: its emission and absorption lines are at the same '
                                        'wavelengths.'),
    'anim_threeviewsspectra_g_hydrogene': ('hydrogène', 'hydrogen'),
    'anim_threeviewsspectra_g_helium': ('hélium', 'helium'),
    'anim_threeviewsspectra_g_sodium': ('sodium', 'sodium'),
    'anim_threeviewsspectra_g_mercure': ('mercure', 'mercury'),
    'anim_threeviewsspectra_spectre': ('Spectre observé', 'Observed spectrum'),
    'anim_threeviewsspectra_loi': ('Loi de Kirchhoff', 'Kirchhoff’s law'),
    'anim_threeviewsspectra_s_continu': ('continu', 'continuous'),
    'anim_threeviewsspectra_s_emission': ('raies d’émission', 'emission lines'),
    'anim_threeviewsspectra_s_absorption': ('raies d’absorption', 'absorption lines'),
    'anim_threeviewsspectra_s_rien': ('rien (ciel noir)', 'nothing (dark sky)'),
    'anim_threeviewsspectra_l_continu': ('un corps chaud et dense émet un spectre continu',
                                         'a hot dense body emits a continuous spectrum'),
    'anim_threeviewsspectra_l_emission': ('un gaz chaud et peu dense émet des raies brillantes',
                                          'a hot thin gas emits bright lines'),
    'anim_threeviewsspectra_l_absorption': ('un gaz plus froid devant une source continue absorbe les mêmes raies',
                                            'a cooler gas in front of a continuous source absorbs the same lines'),
    'anim_threeviewsspectra_l_rien': ('le télescope ne vise aucune source', 'the telescope points at no source'),
    'anim_threeviewsspectra_ampoule': ('ampoule', 'bulb'),
    'anim_threeviewsspectra_nuage': ('nuage de gaz', 'gas cloud'),
    'anim_threeviewsspectra_telescope': ('télescope', 'telescope'),
    'anim_threeviewsspectra_titre_scene': ('La scène (glisser le télescope)', 'The scene (drag the telescope)'),
    'anim_threeviewsspectra_titre_spectre': ('Spectre vu par le télescope', 'Spectrum seen by the telescope'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ hammerthrower
    'anim_hammerthrower_lanceur': ('Masse du lanceur', 'Thrower mass'),
    'anim_hammerthrower_lanceur_aide': ('Masse de l’athlète (40 à 150 kg).', 'Mass of the athlete (40 to 150 kg).'),
    'anim_hammerthrower_marteau': ('Masse du marteau', 'Hammer mass'),
    'anim_hammerthrower_marteau_aide': ('Masse de la boule (1 à 20 kg ; marteau masculin réglementaire : 7,26 kg).',
                                        'Mass of the ball (1 to 20 kg; regulation men’s hammer: 7.26 kg).'),
    'anim_hammerthrower_rapport': ('Masse étoile / planète', 'Star / planet mass'),
    'anim_hammerthrower_rapport_aide': ('Rapport des masses de l’étoile et de la planète (1 à 20 ; l’original prenait '
                                        '6,2 / 1,2). Le vrai rapport Soleil / Jupiter est d’environ 1 048.',
                                        'Mass ratio of the star and the planet (1 to 20; the original used 6.2 / 1.2). '
                                        'The real Sun / Jupiter ratio is about 1,048.'),
    'anim_hammerthrower_trajets': ('Trajectoires', 'Paths'),
    'anim_hammerthrower_trajets_aide': ('Tracer les cercles décrits autour du centre de masse.',
                                        'Draw the circles traced around the center of mass.'),
    'anim_hammerthrower_r_lanceur': ('Cercle du lanceur (rayon)', 'Thrower’s circle (radius)'),
    'anim_hammerthrower_r_boule': ('Cercle de la boule (rayon)', 'Ball’s circle (radius)'),
    'anim_hammerthrower_rapport_v': ('Rapport des rayons = rapport inverse des masses',
                                     'Ratio of radii = inverse mass ratio'),
    'anim_hammerthrower_r_etoile': ('Cercle de l’étoile, en part de la distance', 'Star’s circle, as a share of the distance'),
    'anim_hammerthrower_titre_lanceur': ('Le lanceur de marteau (vu de dessus, distance ≈ 2 m)',
                                         'The hammer thrower (seen from above, distance ≈ 2 m)'),
    'anim_hammerthrower_titre_etoile': ('Une étoile et sa planète', 'A star and its planet'),
    'anim_hammerthrower_lanceur_n': ('lanceur', 'thrower'),
    'anim_hammerthrower_boule': ('boule', 'ball'),
    # ------------------------------------------------------------ ca_extrasolarplanets_graph
    'anim_ca_extrasolarplanets_graph_systeme': ('Système', 'System'),
    'anim_ca_extrasolarplanets_graph_systeme_aide': ('Le Soleil et Jupiter, le Soleil et la Terre (avec la Lune), ou '
                                                     '51 Pegasi et sa planète, la première découverte autour d’une '
                                                     'étoile comme le Soleil (1995).',
                                                     'The Sun and Jupiter, the Sun and the Earth (with the Moon), or '
                                                     '51 Pegasi and its planet, the first found around a Sun-like star '
                                                     '(1995).'),
    'anim_ca_extrasolarplanets_graph_s_soleil_jupiter': ('Soleil et Jupiter', 'Sun and Jupiter'),
    'anim_ca_extrasolarplanets_graph_s_soleil_terre': ('Soleil et Terre', 'Sun and Earth'),
    'anim_ca_extrasolarplanets_graph_s_51peg': ('51 Pegasi b', '51 Pegasi b'),
    'anim_ca_extrasolarplanets_graph_k': ('Amplitude K (calculée)', 'Amplitude K (computed)'),
    'anim_ca_extrasolarplanets_graph_k_mesuree': ('Amplitude mesurée', 'Measured amplitude'),
    'anim_ca_extrasolarplanets_graph_v': ('Vitesse radiale de l’étoile', 'Radial velocity of the star'),
    'anim_ca_extrasolarplanets_graph_titre_orbite': ('Orbites vues de dessus', 'Orbits seen from above'),
    'anim_ca_extrasolarplanets_graph_titre_courbe': ('Vitesse radiale de l’étoile (deux orbites)',
                                                     'Radial velocity of the star (two orbits)'),
    'anim_ca_extrasolarplanets_graph_agrandie': ('orbite de l’étoile très agrandie', 'star’s orbit greatly enlarged'),
    'anim_ca_extrasolarplanets_graph_axe_t': ('temps (en périodes)', 'time (in periods)'),
    'anim_ca_extrasolarplanets_graph_eloigne': ('s’éloigne : décalage vers le rouge', 'receding: redshift'),
    'anim_ca_extrasolarplanets_graph_approche': ('s’approche : décalage vers le bleu', 'approaching: blueshift'),
    # ------------------------------------------------------------ radialvelocitydemo
    'anim_radialvelocitydemo_etoile': ('Masse de l’étoile', 'Star mass'),
    'anim_radialvelocitydemo_etoile_aide': ('Masse de l’étoile en masses solaires.', 'Star mass in solar masses.'),
    'anim_radialvelocitydemo_planete': ('Masse de la planète', 'Planet mass'),
    'anim_radialvelocitydemo_planete_aide': ('Masse de la planète en masses de Jupiter (0,01 à 20).',
                                             'Planet mass in Jupiter masses (0.01 to 20).'),
    'anim_radialvelocitydemo_a': ('Distance', 'Distance'),
    'anim_radialvelocitydemo_a_aide': ('Rayon de l’orbite (ua).', 'Orbit radius (au).'),
    'anim_radialvelocitydemo_amplification': ('Amplification du décalage', 'Shift magnification'),
    'anim_radialvelocitydemo_amplification_aide': ('Les vrais décalages sont minuscules (une fraction de picomètre) : '
                                                   'on les amplifie pour les voir.',
                                                   'The real shifts are tiny (a fraction of a picometre): they are '
                                                   'magnified to be seen.'),
    'anim_radialvelocitydemo_dl': ('Décalage réel de Hα', 'Real shift of Hα'),
    'anim_radialvelocitydemo_titre_systeme': ('L’étoile et sa planète vues de dessus', 'The star and its planet seen from above'),
    'anim_radialvelocitydemo_titre_spectre': ('Spectre de l’étoile (décalage amplifié)', 'Star spectrum (shift magnified)'),
    'anim_radialvelocitydemo_reference': ('raies au repos (référence)', 'lines at rest (reference)'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ ca_extrasolarplanets_starwobble
    'anim_ca_extrasolarplanets_starwobble_annee': ('Année', 'Year'),
    'anim_ca_extrasolarplanets_starwobble_annee_aide': ('Date (1800 à 2050, domaine de validité des éléments '
                                                        'orbitaux utilisés).',
                                                        'Date (1800 to 2050, range of validity of the orbital elements '
                                                        'used).'),
    'anim_ca_extrasolarplanets_starwobble_ans_par_s': ('Vitesse', 'Speed'),
    'anim_ca_extrasolarplanets_starwobble_ans_par_s_aide': ('Années écoulées par seconde pendant la lecture.',
                                                            'Years elapsed per second while playing.'),
    'anim_ca_extrasolarplanets_starwobble_date': ('Date', 'Date'),
    'anim_ca_extrasolarplanets_starwobble_distance': ('Centre du Soleil – centre de masse',
                                                      'Sun’s center – center of mass'),
    'anim_ca_extrasolarplanets_starwobble_dehors': ('Centre de masse hors du Soleil', 'Center of mass outside the Sun'),
    'anim_ca_extrasolarplanets_starwobble_titre': ('Le Soleil autour du centre de masse (vu du pôle de l’écliptique)',
                                                   'The Sun around the center of mass (seen from the ecliptic pole)'),
    'anim_ca_extrasolarplanets_starwobble_trainee': ('trajet du centre du Soleil pendant les 40 dernières années',
                                                     'path of the Sun’s center over the last 40 years'),
})
for _n, _fr, _en in (('mercure', 'Mercure', 'Mercury'), ('venus', 'Vénus', 'Venus'), ('terre', 'Terre', 'Earth'),
                     ('mars', 'Mars', 'Mars'), ('jupiter', 'Jupiter', 'Jupiter'), ('saturne', 'Saturne', 'Saturn'),
                     ('uranus', 'Uranus', 'Uranus'), ('neptune', 'Neptune', 'Neptune')):
    ANIM_LOT3['anim_ca_extrasolarplanets_starwobble_p_' + _n] = (_fr, _en)
    ANIM_LOT3['anim_ca_extrasolarplanets_starwobble_p_' + _n + '_aide'] = (
        'Compter l’attraction de %s.' % _fr, 'Include the pull of %s.' % _en)

ANIM_LOT3.update({
    # ------------------------------------------------------------ pulsarPeriodSim
    'anim_pulsarperiodsim_mouvement': ('Pulsar', 'Pulsar'),
    'anim_pulsarperiodsim_mouvement_aide': ('Pulsar immobile, ou en orbite (autour d’un compagnon invisible).',
                                            'Pulsar at rest, or in orbit (around an unseen companion).'),
    'anim_pulsarperiodsim_immobile': ('immobile', 'at rest'),
    'anim_pulsarperiodsim_orbite': ('en orbite', 'in orbit'),
    'anim_pulsarperiodsim_periode': ('Période du pulsar', 'Pulsar period'),
    'anim_pulsarperiodsim_periode_aide': ('Intervalle entre deux impulsions émises (unités réduites, la lumière va à '
                                          'la vitesse 1).',
                                          'Interval between two emitted pulses (reduced units, light travels at '
                                          'speed 1).'),
    'anim_pulsarperiodsim_periode_orbite': ('Période de l’orbite', 'Orbital period'),
    'anim_pulsarperiodsim_periode_orbite_aide': ('Durée d’un tour du pulsar sur son orbite : plus elle est courte, plus '
                                                 'il va vite et plus les intervalles varient.',
                                                 'Duration of one turn of the pulsar on its orbit: the shorter, the '
                                                 'faster it moves and the more the intervals vary.'),
    'anim_pulsarperiodsim_couleurs': ('Couleurs', 'Colors'),
    'anim_pulsarperiodsim_couleurs_aide': ('Colorer chaque impulsion selon que le pulsar s’approchait (bleu) ou '
                                           's’éloignait (rouge) de la Terre en l’émettant.',
                                           'Color each pulse according to whether the pulsar was approaching (blue) '
                                           'or receding (red) from the Earth when it emitted it.'),
    'anim_pulsarperiodsim_p_vraie': ('Période vraie', 'True period'),
    'anim_pulsarperiodsim_v_c': ('Vitesse orbitale / c', 'Orbital speed / c'),
    'anim_pulsarperiodsim_prevu': ('Intervalles prévus P (1 ± v/c)', 'Predicted intervals P (1 ± v/c)'),
    'anim_pulsarperiodsim_mesure': ('Intervalles mesurés', 'Measured intervals'),
    'anim_pulsarperiodsim_pulsar': ('pulsar', 'pulsar'),
    'anim_pulsarperiodsim_titre_scene': ('Les impulsions en route vers la Terre', 'The pulses on their way to the Earth'),
    'anim_pulsarperiodsim_titre_graphe': ('Intervalle entre deux arrivées', 'Interval between two arrivals'),
    'anim_pulsarperiodsim_axe_t': ('temps d’arrivée', 'arrival time'),
    'anim_pulsarperiodsim_axe_i': ('intervalle', 'interval'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ transitsimulator
    'anim_transitsimulator_systeme': ('Système', 'System'),
    'anim_transitsimulator_systeme_aide': ('Exemples de l’original, ou planètes réelles (NASA Exoplanet Archive, 2026) : '
                                           'choisir un système règle tous les curseurs.',
                                           'Examples of the original, or real planets (NASA Exoplanet Archive, 2026): '
                                           'choosing a system sets all the sliders.'),
    'anim_transitsimulator_s_a': ('exemple A : un Jupiter à 1 ua', 'example A: a Jupiter at 1 au'),
    'anim_transitsimulator_s_b': ('exemple B : une Terre à 1 ua', 'example B: an Earth at 1 au'),
    'anim_transitsimulator_masse_planete': ('Masse de la planète', 'Planet mass'),
    'anim_transitsimulator_masse_planete_aide': ('Masse de la planète en masses de Jupiter (elle ne change que la '
                                                 'période, très peu).',
                                                 'Planet mass in Jupiter masses (it only changes the period, very '
                                                 'slightly).'),
    'anim_transitsimulator_rayon_planete': ('Rayon de la planète', 'Planet radius'),
    'anim_transitsimulator_rayon_planete_aide': ('Rayon de la planète en rayons de Jupiter : la profondeur du transit '
                                                 'vaut (R_p / R_*)².',
                                                 'Planet radius in Jupiter radii: the transit depth is (R_p / R_*)².'),
    'anim_transitsimulator_masse_etoile': ('Masse de l’étoile', 'Star mass'),
    'anim_transitsimulator_masse_etoile_aide': ('Masse de l’étoile en masses solaires.', 'Star mass in solar masses.'),
    'anim_transitsimulator_rayon_etoile': ('Rayon de l’étoile', 'Star radius'),
    'anim_transitsimulator_rayon_etoile_aide': ('Rayon de l’étoile en rayons solaires.', 'Star radius in solar radii.'),
    'anim_transitsimulator_a': ('Demi-grand axe', 'Semi-major axis'),
    'anim_transitsimulator_a_aide': ('Taille de l’orbite (ua).', 'Size of the orbit (au).'),
    'anim_transitsimulator_e': ('Excentricité', 'Eccentricity'),
    'anim_transitsimulator_e_aide': ('Excentricité de l’orbite (0 : cercle).', 'Eccentricity of the orbit (0: circle).'),
    'anim_transitsimulator_i': ('Inclinaison', 'Inclination'),
    'anim_transitsimulator_i_aide': ('Inclinaison de l’orbite sur le plan du ciel : 90° = vue par la tranche ; en '
                                     'dessous d’un certain angle, la planète passe à côté de l’étoile.',
                                     'Inclination of the orbit to the plane of the sky: 90° = seen edge-on; below some '
                                     'angle, the planet misses the star.'),
    'anim_transitsimulator_omega': ('Argument du périastre', 'Argument of periastron'),
    'anim_transitsimulator_omega_aide': ('Orientation de l’orbite elliptique (sans effet si e = 0).',
                                         'Orientation of the elliptical orbit (no effect if e = 0).'),
    'anim_transitsimulator_bruit': ('Bruit des mesures', 'Measurement noise'),
    'anim_transitsimulator_bruit_aide': ('Écart type du bruit des mesures simulées, en flux relatif.',
                                         'Standard deviation of the simulated measurement noise, in relative flux.'),
    'anim_transitsimulator_mesures': ('Nombre de mesures', 'Number of measurements'),
    'anim_transitsimulator_mesures_aide': ('Mesures simulées réparties au hasard autour du transit (0 : aucune).',
                                           'Simulated measurements spread at random around the transit (0: none).'),
    'anim_transitsimulator_courbe': ('Courbe théorique', 'Theoretical curve'),
    'anim_transitsimulator_courbe_aide': ('Tracer la courbe de lumière calculée.', 'Draw the computed light curve.'),
    'anim_transitsimulator_profondeur': ('Profondeur du transit', 'Transit depth'),
    'anim_transitsimulator_rapport': ('Rapport des surfaces', 'Ratio of areas'),
    'anim_transitsimulator_duree': ('Durée du transit', 'Transit duration'),
    'anim_transitsimulator_pas_de_transit': ('pas de transit', 'no transit'),
    'anim_transitsimulator_b': ('Paramètre d’impact b', 'Impact parameter b'),
    'anim_transitsimulator_p_publiee': ('Période publiée', 'Published period'),
    'anim_transitsimulator_titre_vue': ('L’étoile vue de la Terre (planète à l’échelle)',
                                        'The star seen from the Earth (planet to scale)'),
    'anim_transitsimulator_titre_courbe': ('Courbe de lumière autour du transit', 'Light curve around the transit'),
    'anim_transitsimulator_axe_phase': ('phase (0 : milieu du transit)', 'phase (0: mid-transit)'),
    'anim_transitsimulator_echelle': ('le trait pointillé montre le trajet de la planète',
                                      'the dashed line shows the planet’s path'),
})
for _t in ('OGLE-TR-113 b', 'TrES-1 b', 'XO-1 b', 'HD 209458 b', 'OGLE-TR-111 b', 'OGLE-TR-10 b', 'HD 189733 b',
           'HD 149026 b', 'OGLE-TR-132 b'):
    ANIM_LOT3['anim_transitsimulator_s_' + _t.lower().replace(' ', '_').replace('-', '_')] = (_t, _t)

ANIM_LOT3.update({
    # ------------------------------------------------------------ radialvelocitysimulator
    'anim_radialvelocitysimulator_systeme': ('Système', 'System'),
    'anim_radialvelocitysimulator_systeme_aide': ('Exemples de l’original ou planètes réelles (NASA Exoplanet Archive, '
                                                  '2026) : choisir un système règle les curseurs.',
                                                  'Examples of the original or real planets (NASA Exoplanet Archive, '
                                                  '2026): choosing a system sets the sliders.'),
    'anim_radialvelocitysimulator_s_a': ('exemple A : un Jupiter à 1 ua', 'example A: a Jupiter at 1 au'),
    'anim_radialvelocitysimulator_s_b': ('exemple B : orbite excentrique (e = 0,4)', 'example B: eccentric orbit (e = 0.4)'),
    'anim_radialvelocitysimulator_s_c': ('exemple C : 0,05 M♃', 'example C: 0.05 M♃'),
    'anim_radialvelocitysimulator_s_d': ('exemple D : une Terre à 1 ua', 'example D: an Earth at 1 au'),
    'anim_radialvelocitysimulator_s_hd_68988_b': ('HD 68988 b', 'HD 68988 b'),
    'anim_radialvelocitysimulator_s_hd_33564_b': ('HD 33564 b', 'HD 33564 b'),
    'anim_radialvelocitysimulator_s_hd_39091_b': ('HD 39091 b (π Mensae b)', 'HD 39091 b (π Mensae b)'),
    'anim_radialvelocitysimulator_s_51_peg_b': ('51 Pegasi b', '51 Pegasi b'),
    'anim_radialvelocitysimulator_masse_etoile': ('Masse de l’étoile', 'Star mass'),
    'anim_radialvelocitysimulator_masse_etoile_aide': ('Masse de l’étoile en masses solaires.', 'Star mass in solar masses.'),
    'anim_radialvelocitysimulator_masse_planete': ('Masse de la planète', 'Planet mass'),
    'anim_radialvelocitysimulator_masse_planete_aide': ('Masse de la planète en masses de Jupiter.',
                                                        'Planet mass in Jupiter masses.'),
    'anim_radialvelocitysimulator_a': ('Demi-grand axe', 'Semi-major axis'),
    'anim_radialvelocitysimulator_a_aide': ('Taille de l’orbite (ua).', 'Size of the orbit (au).'),
    'anim_radialvelocitysimulator_e': ('Excentricité', 'Eccentricity'),
    'anim_radialvelocitysimulator_e_aide': ('Excentricité : la courbe cesse d’être une sinusoïde.',
                                            'Eccentricity: the curve is no longer a sine wave.'),
    'anim_radialvelocitysimulator_i': ('Inclinaison', 'Inclination'),
    'anim_radialvelocitysimulator_i_aide': ('Inclinaison de l’orbite (90° : vue par la tranche, 0° : vue de face, '
                                            'aucune vitesse radiale). On ne mesure que M_p sin i.',
                                            'Inclination of the orbit (90°: edge-on, 0°: face-on, no radial '
                                            'velocity). Only M_p sin i is measured.'),
    'anim_radialvelocitysimulator_omega': ('Argument du périastre', 'Argument of periastron'),
    'anim_radialvelocitysimulator_omega_aide': ('Orientation de l’ellipse par rapport à la ligne de visée.',
                                                'Orientation of the ellipse relative to the line of sight.'),
    'anim_radialvelocitysimulator_bruit': ('Bruit des mesures', 'Measurement noise'),
    'anim_radialvelocitysimulator_bruit_aide': ('Écart type du bruit des mesures simulées (m/s).',
                                                'Standard deviation of the simulated measurement noise (m/s).'),
    'anim_radialvelocitysimulator_mesures': ('Nombre de mesures', 'Number of measurements'),
    'anim_radialvelocitysimulator_mesures_aide': ('Mesures simulées à des phases tirées au hasard (0 : aucune).',
                                                  'Simulated measurements at random phases (0: none).'),
    'anim_radialvelocitysimulator_msini': ('M_p sin i (ce que mesure la méthode)', 'M_p sin i (what the method measures)'),
    'anim_radialvelocitysimulator_titre_orbite': ('Orbite vue de dessus', 'Orbit seen from above'),
    'anim_radialvelocitysimulator_titre_courbe': ('Vitesse radiale de l’étoile', 'Radial velocity of the star'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ eclipsingbinarysim
    'anim_eclipsingbinarysim_systeme': ('Système', 'System'),
    'anim_eclipsingbinarysim_systeme_aide': ('Huit exemples de l’original, puis 46 binaires réelles avec leur courbe de '
                                             'lumière observée (points gris). Les systèmes « à compléter » ont un '
                                             'paramètre volontairement faux : à retrouver pour que la courbe passe par '
                                             'les points.',
                                             'Eight examples of the original, then 46 real binaries with their observed '
                                             'light curve (grey dots). The « to complete » systems have one parameter '
                                             'deliberately wrong: find it so that the curve goes through the dots.'),
    'anim_eclipsingbinarysim_m1': ('Masse 1', 'Mass 1'),
    'anim_eclipsingbinarysim_m1_aide': ('Masse de l’étoile 1 (masses solaires).', 'Mass of star 1 (solar masses).'),
    'anim_eclipsingbinarysim_m2': ('Masse 2', 'Mass 2'),
    'anim_eclipsingbinarysim_m2_aide': ('Masse de l’étoile 2 (masses solaires).', 'Mass of star 2 (solar masses).'),
    'anim_eclipsingbinarysim_r1': ('Rayon 1', 'Radius 1'),
    'anim_eclipsingbinarysim_r1_aide': ('Rayon de l’étoile 1 (rayons solaires).', 'Radius of star 1 (solar radii).'),
    'anim_eclipsingbinarysim_r2': ('Rayon 2', 'Radius 2'),
    'anim_eclipsingbinarysim_r2_aide': ('Rayon de l’étoile 2 (rayons solaires).', 'Radius of star 2 (solar radii).'),
    'anim_eclipsingbinarysim_t1': ('Température 1', 'Temperature 1'),
    'anim_eclipsingbinarysim_t1_aide': ('Température de surface de l’étoile 1.', 'Surface temperature of star 1.'),
    'anim_eclipsingbinarysim_t2': ('Température 2', 'Temperature 2'),
    'anim_eclipsingbinarysim_t2_aide': ('Température de surface de l’étoile 2.', 'Surface temperature of star 2.'),
    'anim_eclipsingbinarysim_a': ('Demi-grand axe', 'Semi-major axis'),
    'anim_eclipsingbinarysim_a_aide': ('Distance moyenne entre les deux étoiles (rayons solaires).',
                                       'Mean distance between the two stars (solar radii).'),
    'anim_eclipsingbinarysim_e': ('Excentricité', 'Eccentricity'),
    'anim_eclipsingbinarysim_e_aide': ('Excentricité de l’orbite : l’éclipse secondaire n’est plus à mi-période.',
                                       'Eccentricity of the orbit: the secondary eclipse is no longer at half-period.'),
    'anim_eclipsingbinarysim_i': ('Inclinaison', 'Inclination'),
    'anim_eclipsingbinarysim_i_aide': ('Inclinaison (90° : vue par la tranche). Trop faible : plus d’éclipse.',
                                       'Inclination (90°: edge-on). Too low: no more eclipses.'),
    'anim_eclipsingbinarysim_omega': ('Argument du périastre', 'Argument of periastron'),
    'anim_eclipsingbinarysim_omega_aide': ('Orientation de l’orbite elliptique.', 'Orientation of the elliptical orbit.'),
    'anim_eclipsingbinarysim_decalage': ('Décalage de phase', 'Phase shift'),
    'anim_eclipsingbinarysim_decalage_aide': ('Faire glisser la courbe calculée le long des phases pour la caler sur '
                                              'les mesures.',
                                              'Slide the computed curve along the phases to line it up with the '
                                              'measurements.'),
    'anim_eclipsingbinarysim_unite': ('Axe vertical', 'Vertical axis'),
    'anim_eclipsingbinarysim_unite_aide': ('Flux relatif, ou magnitude (plus grande = plus faible).',
                                           'Relative flux, or magnitude (larger = fainter).'),
    'anim_eclipsingbinarysim_u_flux': ('flux', 'flux'),
    'anim_eclipsingbinarysim_u_mag': ('magnitude', 'magnitude'),
    'anim_eclipsingbinarysim_donnees': ('Mesures', 'Measurements'),
    'anim_eclipsingbinarysim_donnees_aide': ('Montrer la courbe de lumière observée du système réel choisi.',
                                             'Show the observed light curve of the chosen real system.'),
    'anim_eclipsingbinarysim_profondeur': ('Éclipse la plus profonde', 'Deepest eclipse'),
    'anim_eclipsingbinarysim_ecart': ('Écart modèle – mesures', 'Model – data deviation'),
    'anim_eclipsingbinarysim_a_completer': ('Système à compléter', 'System to complete'),
    'anim_eclipsingbinarysim_types': ('Types spectraux', 'Spectral types'),
    'anim_eclipsingbinarysim_titre_vue': ('Les deux étoiles vues de la Terre', 'The two stars seen from the Earth'),
    'anim_eclipsingbinarysim_titre_courbe': ('Courbe de lumière (filtre V)', 'Light curve (V filter)'),
    'anim_eclipsingbinarysim_axe_mag': ('magnitude relative', 'relative magnitude'),
})
for _k in range(1, 9):
    ANIM_LOT3['anim_eclipsingbinarysim_exemple_%d' % _k] = ('exemple %d' % _k, 'example %d' % _k)
from .donnees_lot3 import BINAIRES as _B, BINAIRES_A_COMPLETER as _AC  # noqa: E402
for _b in _B:
    _n = _b[0]
    ANIM_LOT3['anim_eclipsingbinarysim_s_' + _n.lower().replace(' ', '_')] = (
        _n + (' (à compléter)' if _n in _AC else ''), _n + (' (to complete)' if _n in _AC else ''))

ANIM_LOT3.update({
    # ------------------------------------------------------------ lightcurve
    'anim_lightcurve_auto': ('Mesures automatiques', 'Automatic measurements'),
    'anim_lightcurve_auto_aide': ('Prendre une mesure à intervalles réguliers pendant la lecture.',
                                  'Take a measurement at regular intervals while playing.'),
    'anim_lightcurve_intervalle': ('Intervalle des mesures', 'Measurement interval'),
    'anim_lightcurve_intervalle_aide': ('Temps entre deux mesures automatiques (jours). Un intervalle proche d’un '
                                        'multiple de la période remplit mal la courbe.',
                                        'Time between two automatic measurements (days). An interval close to a '
                                        'multiple of the period fills the curve poorly.'),
    'anim_lightcurve_bruit': ('Bruit', 'Noise'),
    'anim_lightcurve_bruit_aide': ('Écart type du bruit des mesures (flux relatif).',
                                   'Standard deviation of the measurement noise (relative flux).'),
    'anim_lightcurve_mesurer': ('Mesurer', 'Measure'),
    'anim_lightcurve_mesurer_aide': ('Mesurer l’éclat maintenant et le reporter à la phase actuelle.',
                                     'Measure the brightness now and plot it at the current phase.'),
    'anim_lightcurve_effacer': ('Effacer les mesures', 'Clear the measurements'),
    'anim_lightcurve_effacer_aide': ('Effacer les points de la courbe.', 'Clear the points of the curve.'),
    'anim_lightcurve_ecoule': ('Temps écoulé', 'Elapsed time'),
    'anim_lightcurve_cycles': ('Périodes complètes', 'Complete periods'),
    'anim_lightcurve_mesures': ('Mesures', 'Measurements'),
    'anim_lightcurve_titre_couple': ('Le couple vu de la Terre (période 3,65 jours)',
                                     'The pair seen from the Earth (period 3.65 days)'),
    'anim_lightcurve_titre_courbe': ('Mesures reportées selon la phase', 'Measurements plotted against phase'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ centerofmass
    'anim_centerofmass_m1': ('Masse 1', 'Mass 1'),
    'anim_centerofmass_m1_aide': ('Masse du corps 1 (1 à 10).', 'Mass of body 1 (1 to 10).'),
    'anim_centerofmass_m2': ('Masse 2', 'Mass 2'),
    'anim_centerofmass_m2_aide': ('Masse du corps 2 (1 à 10).', 'Mass of body 2 (1 to 10).'),
    'anim_centerofmass_separation': ('Séparation', 'Separation'),
    'anim_centerofmass_separation_aide': ('Distance entre les deux corps (1 à 20 ; une case du quadrillage = 1).',
                                          'Distance between the two bodies (1 to 20; one grid square = 1).'),
    'anim_centerofmass_fixe': ('Centre de masse fixe', 'Fixed center of mass'),
    'anim_centerofmass_fixe_aide': ('Garder le centre de masse au milieu ; sinon le corps 1 reste en place et le centre '
                                    'de masse se déplace.',
                                    'Keep the center of mass in the middle; otherwise body 1 stays put and the center '
                                    'of mass moves.'),
    'anim_centerofmass_r1': ('Distance r₁ (corps 1 – centre de masse)', 'Distance r₁ (body 1 – center of mass)'),
    'anim_centerofmass_r2': ('Distance r₂ (corps 2 – centre de masse)', 'Distance r₂ (body 2 – center of mass)'),
    'anim_centerofmass_produits': ('Équilibre', 'Balance'),
    'anim_centerofmass_titre': ('Deux corps et leur centre de masse', 'Two bodies and their center of mass'),
    # ------------------------------------------------------------ wagonwheel
    'anim_wagonwheel_periode': ('Période de rotation', 'Rotation period'),
    'anim_wagonwheel_periode_aide': ('Durée d’un tour de la roue (1 à 10 s).', 'Time for one turn of the wheel (1 to 10 s).'),
    'anim_wagonwheel_cadence': ('Images par seconde', 'Frames per second'),
    'anim_wagonwheel_cadence_aide': ('Nombre d’images (ou de mesures) par seconde : 0,1 à 10.',
                                     'Number of frames (or measurements) per second: 0.1 to 10.'),
    'anim_wagonwheel_rayons': ('Rayons', 'Spokes'),
    'anim_wagonwheel_rayons_aide': ('Nombre de rayons identiques : avec n rayons, la roue paraît la même tous les '
                                    '360°/n.',
                                    'Number of identical spokes: with n spokes, the wheel looks the same every '
                                    '360°/n.'),
    'anim_wagonwheel_vrai': ('Rotation vraie', 'True rotation'),
    'anim_wagonwheel_apparent': ('Rotation apparente', 'Apparent rotation'),
    'anim_wagonwheel_image': ('image', 'frame'),
    'anim_wagonwheel_p_apparente': ('Période apparente', 'Apparent period'),
    'anim_wagonwheel_sens': ('La roue semble', 'The wheel seems to'),
    'anim_wagonwheel_avant': ('tourner dans le bon sens', 'turn the right way'),
    'anim_wagonwheel_arriere': ('tourner à l’envers', 'turn backwards'),
    'anim_wagonwheel_immobile': ('immobile', 'stand still'),
    'anim_wagonwheel_titre_vraie': ('La roue en continu', 'The wheel, continuously'),
    'anim_wagonwheel_titre_vue': ('La roue vue image par image', 'The wheel seen frame by frame'),
})
for _n in (1, 2, 4, 8):
    ANIM_LOT3['anim_wagonwheel_r_%d' % _n] = (str(_n), str(_n))

ANIM_LOT3.update({
    # ------------------------------------------------------------ solarsystemproperties
    'anim_solarsystemproperties_propriete': ('Propriété', 'Property'),
    'anim_solarsystemproperties_propriete_aide': ('Grandeur montrée par l’histogramme (rapportée à la Terre quand '
                                                  'c’est utile).',
                                                  'Quantity shown by the histogram (relative to the Earth where '
                                                  'useful).'),
    'anim_solarsystemproperties_g_tellurique': ('Planètes telluriques', 'Terrestrial planets'),
    'anim_solarsystemproperties_g_tellurique_aide': ('Montrer Mercure, Vénus, la Terre et Mars.',
                                                     'Show Mercury, Venus, the Earth and Mars.'),
    'anim_solarsystemproperties_g_geante': ('Planètes géantes', 'Giant planets'),
    'anim_solarsystemproperties_g_geante_aide': ('Montrer Jupiter, Saturne, Uranus et Neptune.',
                                                 'Show Jupiter, Saturn, Uranus and Neptune.'),
    'anim_solarsystemproperties_g_naine': ('Pluton (planète naine)', 'Pluto (dwarf planet)'),
    'anim_solarsystemproperties_g_naine_aide': ('Montrer Pluton, planète naine depuis 2006.',
                                                'Show Pluto, a dwarf planet since 2006.'),
    'anim_solarsystemproperties_log': ('Échelle logarithmique', 'Logarithmic scale'),
    'anim_solarsystemproperties_log_aide': ('Échelle verticale logarithmique, pour comparer des grandeurs très '
                                            'différentes (sans effet sur la rotation, qui peut être négative).',
                                            'Logarithmic vertical scale, to compare very different quantities (no '
                                            'effect on rotation, which can be negative).'),
    'anim_solarsystemproperties_p_distance': ('Distance moyenne au Soleil', 'Mean distance from the Sun'),
    'anim_solarsystemproperties_p_periode': ('Période orbitale', 'Orbital period'),
    'anim_solarsystemproperties_p_masse': ('Masse', 'Mass'),
    'anim_solarsystemproperties_p_rayon': ('Rayon', 'Radius'),
    'anim_solarsystemproperties_p_satellites': ('Satellites connus', 'Known moons'),
    'anim_solarsystemproperties_p_rotation': ('Période de rotation', 'Rotation period'),
    'anim_solarsystemproperties_p_densite': ('Densité', 'Density'),
    'anim_solarsystemproperties_u_distance': ('ua', 'au'),
    'anim_solarsystemproperties_u_periode': ('années', 'years'),
    'anim_solarsystemproperties_u_masse': ('masses terrestres', 'Earth masses'),
    'anim_solarsystemproperties_u_rayon': ('rayons terrestres', 'Earth radii'),
    'anim_solarsystemproperties_u_satellites': ('NASA, 2026', 'NASA, 2026'),
    'anim_solarsystemproperties_u_rotation': ('jours ; négatif : rétrograde', 'days; negative: retrograde'),
    'anim_solarsystemproperties_u_densite': ('g/cm³', 'g/cm³'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ formationtemps
    'anim_formationtemps_temperature': ('Température', 'Temperature'),
    'anim_formationtemps_temperature_aide': ('Température de la nébuleuse (20 à 2 000 K) : on lit la distance au Soleil '
                                             'où elle régnait et l’état de chaque substance.',
                                             'Temperature of the nebula (20 to 2,000 K): read the distance from the '
                                             'Sun where it prevailed and the state of each substance.'),
    'anim_formationtemps_distance': ('Distance au Soleil', 'Distance from the Sun'),
    'anim_formationtemps_solides': ('Substances solides', 'Solid substances'),
    'anim_formationtemps_titre': ('Température de la nébuleuse selon la distance', 'Nebula temperature versus distance'),
    'anim_formationtemps_titre_etats': ('État à cette température', 'State at this temperature'),
    'anim_formationtemps_axe_d': ('distance au Soleil (ua)', 'distance from the Sun (au)'),
    'anim_formationtemps_axe_t': ('température (K)', 'temperature (K)'),
    'anim_formationtemps_solide': ('solide', 'solid'),
    'anim_formationtemps_gaz': ('gaz', 'gas'),
})
for _k, _fr, _en in (('oxydes', 'Oxydes métalliques', 'Metal oxides'), ('fer_nickel', 'Fer et nickel métalliques',
                     'Metallic iron and nickel'), ('silicates', 'Silicates', 'Silicates'),
                     ('feldspaths', 'Feldspaths', 'Feldspars'), ('troilite', 'Troïlite (FeS)', 'Troilite (FeS)'),
                     ('eau', 'Glace d’eau', 'Water ice'), ('ammoniac', 'Ammoniac', 'Ammonia'),
                     ('methane', 'Méthane', 'Methane'), ('argon_neon', 'Argon, néon', 'Argon, neon')):
    ANIM_LOT3['anim_formationtemps_s_' + _k] = (_fr, _en)

ANIM_LOT3.update({
    # ------------------------------------------------------------ drivingthroughsnow
    'anim_drivingthroughsnow_voiture': ('Vitesse de la voiture', 'Car speed'),
    'anim_drivingthroughsnow_voiture_aide': ('Vitesse de la voiture (unités arbitraires).',
                                             'Speed of the car (arbitrary units).'),
    'anim_drivingthroughsnow_neige': ('Vitesse de chute de la neige', 'Snow falling speed'),
    'anim_drivingthroughsnow_neige_aide': ('Vitesse de chute des flocons, dans les mêmes unités.',
                                           'Falling speed of the flakes, in the same units.'),
    'anim_drivingthroughsnow_champ': ('Champ de vision', 'Field of view'),
    'anim_drivingthroughsnow_champ_aide': ('Angle de vue horizontal du conducteur.', 'Horizontal viewing angle of the driver.'),
    'anim_drivingthroughsnow_visibilite': ('Visibilité', 'Visibility'),
    'anim_drivingthroughsnow_visibilite_aide': ('Distance au-delà de laquelle on ne voit plus les flocons.',
                                                'Distance beyond which the flakes are no longer seen.'),
    'anim_drivingthroughsnow_radiant': ('radiant', 'radiant'),
    'anim_drivingthroughsnow_radiant_aide': ('Marquer le point d’où semblent venir les flocons.',
                                             'Mark the point the flakes seem to come from.'),
    'anim_drivingthroughsnow_radiant_v': ('Hauteur du radiant', 'Height of the radiant'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ fusion01, fusion02 (textes communs)
    'anim_fusion_suivante': ('Étape suivante', 'Next step'),
    'anim_fusion_suivante_aide': ('Passer à la réaction suivante.', 'Go to the next reaction.'),
    'anim_fusion_etape': ('Étape', 'Step'),
    'anim_fusion_q': ('Énergie libérée par cette étape', 'Energy released by this step'),
    'anim_fusion_total': ('Énergie totale (4 ¹H → ⁴He)', 'Total energy (4 ¹H → ⁴He)'),
    'anim_fusion_neutrinos': ('Emportée par les neutrinos', 'Carried away by neutrinos'),
    'anim_fusion_titre_scene': ('La réaction', 'The reaction'),
    'anim_fusion_titre_etapes': ('Les étapes', 'The steps'),
    'anim_fusion_bilan': ('Bilan : 4 ¹H → ⁴He + {e} MeV', 'Net: 4 ¹H → ⁴He + {e} MeV'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ milkywayrotationalvelocity
    'anim_milkywayrotationalvelocity_rayon': ('Distance au centre', 'Distance from the center'),
    'anim_milkywayrotationalvelocity_rayon_aide': ('Rayon du cercle considéré (0,5 à 25 kpc) ; on peut aussi cliquer '
                                                   'ou glisser sur la courbe.',
                                                   'Radius of the circle considered (0.5 to 25 kpc); one can also '
                                                   'click or drag on the curve.'),
    'anim_milkywayrotationalvelocity_kepler': ('Courbe képlérienne', 'Keplerian curve'),
    'anim_milkywayrotationalvelocity_kepler_aide': ('Tracer la vitesse qu’on aurait au-delà si toute la masse était '
                                                    'contenue dans le cercle choisi (v ∝ 1/√R).',
                                                    'Draw the speed one would get beyond if all the mass were inside '
                                                    'the chosen circle (v ∝ 1/√R).'),
    'anim_milkywayrotationalvelocity_r': ('Rayon', 'Radius'),
    'anim_milkywayrotationalvelocity_v': ('Vitesse de rotation', 'Rotation speed'),
    'anim_milkywayrotationalvelocity_m': ('Masse contenue (v² R / G)', 'Mass inside (v² R / G)'),
    'anim_milkywayrotationalvelocity_tour': ('Durée d’un tour', 'Time for one turn'),
    'anim_milkywayrotationalvelocity_ma': ('millions d’années', 'million years'),
    'anim_milkywayrotationalvelocity_k': ('si toute la masse était dedans', 'if all the mass were inside'),
    'anim_milkywayrotationalvelocity_soleil': ('Soleil', 'Sun'),
    'anim_milkywayrotationalvelocity_titre_courbe': ('Courbe de rotation de la Voie lactée',
                                                     'Rotation curve of the Milky Way'),
    'anim_milkywayrotationalvelocity_titre_galaxie': ('La Galaxie vue de face (schéma)', 'The Galaxy seen face-on (sketch)'),
    'anim_milkywayrotationalvelocity_axe_r': ('distance au centre (kpc)', 'distance from the center (kpc)'),
    'anim_milkywayrotationalvelocity_axe_v': ('vitesse (km/s)', 'speed (km/s)'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ trafficdensity
    'anim_trafficdensity_vitesse': ('Vitesse des voitures', 'Car speed'),
    'anim_trafficdensity_vitesse_aide': ('Vitesse des voitures sur route libre.', 'Speed of the cars on the open road.'),
    'anim_trafficdensity_lente': ('Vitesse en dépassant', 'Speed while passing'),
    'anim_trafficdensity_lente_aide': ('Vitesse des voitures dans la zone où elles attendent de dépasser le tracteur.',
                                       'Speed of the cars in the stretch where they wait to pass the tractor.'),
    'anim_trafficdensity_tracteur': ('tracteur', 'tractor'),
    'anim_trafficdensity_v_tracteur': ('Vitesse du tracteur', 'Tractor speed'),
    'anim_trafficdensity_v_tracteur_aide': ('Vitesse du tracteur (toujours plus lente que les voitures qui le '
                                          'dépassent).',
                                          'Speed of the tractor (always slower than the cars passing it).'),
    'anim_trafficdensity_zone': ('on dépasse', 'passing'),
    'anim_trafficdensity_prevu': ('Densité du bouchon (prévue)', 'Jam density (predicted)'),
    'anim_trafficdensity_mesure': ('Densité du bouchon (comptée)', 'Jam density (counted)'),
    'anim_trafficdensity_dans_zone': ('Voitures dans le bouchon', 'Cars in the jam'),
    'anim_trafficdensity_titre': ('La route vue en suivant le tracteur (le marquage au sol défile)',
                                  'The road seen while following the tractor (the road markings scroll)'),
    'anim_trafficdensity_densite': ('nombre de voitures le long de la route', 'number of cars along the road'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ balloon
    'anim_balloon_rayon': ('Rayon du ballon', 'Balloon radius'),
    'anim_balloon_rayon_aide': ('Facteur d’échelle a : 1 au départ, 3 gonflé. La lecture gonfle le ballon.',
                                'Scale factor a: 1 at the start, 3 inflated. Playing inflates the balloon.'),
    'anim_balloon_taux': ('Vitesse de gonflage', 'Inflation rate'),
    'anim_balloon_taux_aide': ('da/dt : croissance du rayon par seconde.', 'da/dt: growth of the radius per second.'),
    'anim_balloon_distances': ('Distances', 'Distances'),
    'anim_balloon_distances_aide': ('Tracer, le long de la surface, les distances aux cinq galaxies les plus proches de '
                                    'la nôtre.',
                                    'Draw, along the surface, the distances to the five galaxies nearest ours.'),
    'anim_balloon_rayon_v': ('Facteur d’échelle a', 'Scale factor a'),
    'anim_balloon_h': ('H = (da/dt) / a', 'H = (da/dt) / a'),
    'anim_balloon_age': ('1 / H', '1 / H'),
    'anim_balloon_plus_proche': ('Distance à la plus proche voisine', 'Distance to the nearest neighbour'),
    'anim_balloon_nous': ('nous', 'us'),
    'anim_balloon_titre_ballon': ('Le ballon (le tourner à la souris)', 'The balloon (turn it with the mouse)'),
    'anim_balloon_titre_hubble': ('Vitesse d’éloignement selon la distance', 'Recession speed versus distance'),
    'anim_balloon_axe_d': ('distance le long de la surface', 'distance along the surface'),
    'anim_balloon_axe_v': ('vitesse d’éloignement', 'recession speed'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ galacticredshift
    'anim_galacticredshift_z': ('Décalage z', 'Redshift z'),
    'anim_galacticredshift_z_aide': ('Décalage vers le rouge : chaque longueur d’onde est multipliée par 1 + z '
                                     '(0 à 1).',
                                     'Redshift: each wavelength is multiplied by 1 + z (0 to 1).'),
    'anim_galacticredshift_filtres': ('Filtres U, B, V, R', 'U, B, V, R filters'),
    'anim_galacticredshift_filtres_aide': ('Montrer les filtres et la lumière qu’ils reçoivent (barres : rapportées '
                                           'à la galaxie au repos ; Δm : variation de magnitude depuis z = 0).',
                                           'Show the filters and the light they receive (bars: relative to the galaxy '
                                           'at rest; Δm: change in magnitude since z = 0).'),
    'anim_galacticredshift_raies': ('Raies', 'Lines'),
    'anim_galacticredshift_raies_aide': ('Marquer quelques raies : calcium (H et K), bande G, magnésium, sodium, '
                                         'hydrogène.',
                                         'Mark a few lines: calcium (H and K), G band, magnesium, sodium, hydrogen.'),
    'anim_galacticredshift_v': ('Vitesse (Doppler relativiste)', 'Speed (relativistic Doppler)'),
    'anim_galacticredshift_halpha': ('Raie Hα observée à', 'Hα line observed at'),
    'anim_galacticredshift_titre': ('Spectre de la galaxie M32, décalé', 'Spectrum of the galaxy M32, shifted'),
    'anim_galacticredshift_titre_f': ('Lumière reçue dans chaque filtre', 'Light received in each filter'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ telescope10
    'anim_telescope10_objet': ('Objet', 'Object'),
    'anim_telescope10_objet_aide': ('Ce que vise la lunette : la Lune, Saturne ou un amas globulaire.',
                                    'What the telescope points at: the Moon, Saturn or a globular cluster.'),
    'anim_telescope10_o_lune': ('la Lune', 'the Moon'),
    'anim_telescope10_o_saturne': ('Saturne', 'Saturn'),
    'anim_telescope10_o_amas': ('un amas globulaire', 'a globular cluster'),
    'anim_telescope10_objectif': ('Objectif', 'Objective'),
    'anim_telescope10_objectif_aide': ('Diamètre de l’objectif (et sa focale) : plus il est grand, plus il recueille '
                                       'de lumière et plus il sépare les détails fins.',
                                       'Diameter of the objective (and its focal length): the larger, the more light '
                                       'it gathers and the finer the details it resolves.'),
    'anim_telescope10_d_8': ('8 pouces (203 mm, F = 1 400 mm)', '8 inches (203 mm, F = 1,400 mm)'),
    'anim_telescope10_d_6': ('6 pouces (152 mm, F = 1 220 mm)', '6 inches (152 mm, F = 1,220 mm)'),
    'anim_telescope10_d_4': ('4 pouces (102 mm, F = 1 020 mm)', '4 inches (102 mm, F = 1,020 mm)'),
    'anim_telescope10_oculaire': ('Oculaire', 'Eyepiece'),
    'anim_telescope10_oculaire_aide': ('Focale de l’oculaire : plus elle est courte, plus le grossissement F / f est '
                                       'fort et le champ étroit.',
                                       'Focal length of the eyepiece: the shorter, the higher the magnification F / f '
                                       'and the narrower the field.'),
    'anim_telescope10_e_40': ('40 mm', '40 mm'),
    'anim_telescope10_e_20': ('20 mm', '20 mm'),
    'anim_telescope10_e_10': ('10 mm', '10 mm'),
    'anim_telescope10_mise_au_point': ('Mise au point', 'Focus'),
    'anim_telescope10_mise_au_point_aide': ('Décalage de l’oculaire par rapport à la position nette (0 : image nette).',
                                            'Offset of the eyepiece from the sharp position (0: sharp image).'),
    'anim_telescope10_g': ('Grossissement F / f', 'Magnification F / f'),
    'anim_telescope10_champ': ('Champ réel', 'True field'),
    'anim_telescope10_resolution': ('Pouvoir séparateur (Rayleigh, 550 nm)', 'Resolving power (Rayleigh, 550 nm)'),
    'anim_telescope10_collecteur': ('Lumière recueillie / œil', 'Light gathered / eye'),
    'anim_telescope10_net': ('Image nette', 'Sharp image'),
    'anim_telescope10_titre_lunette': ('La lunette', 'The telescope'),
    'anim_telescope10_titre_vue': ('Dans l’oculaire', 'In the eyepiece'),
    'anim_telescope10_champ_v': ('champ réel : {c}′', 'true field: {c}′'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ buckets
    'anim_buckets_pose': ('Temps de pose', 'Exposure time'),
    'anim_buckets_pose_aide': ('Durée de la pose (1 à 60 s ; elle défile deux fois plus vite que le temps réel).',
                               'Exposure duration (1 to 60 s; it runs twice as fast as real time).'),
    'anim_buckets_etoile': ('Flux de l’étoile', 'Star flux'),
    'anim_buckets_etoile_aide': ('Photons de l’étoile reçus par seconde (répartis sur quelques pixels).',
                                 'Photons from the star received per second (spread over a few pixels).'),
    'anim_buckets_ciel': ('Fond du ciel', 'Sky background'),
    'anim_buckets_ciel_aide': ('Photons du ciel reçus par seconde et par pixel.',
                               'Sky photons received per second and per pixel.'),
    'anim_buckets_poser': ('Poser', 'Expose'),
    'anim_buckets_poser_aide': ('Vider le capteur et commencer une pose.', 'Empty the sensor and start an exposure.'),
    'anim_buckets_lire': ('Lire', 'Read out'),
    'anim_buckets_lire_aide': ('Arrêter la pose et lire le capteur, case par case.',
                               'Stop the exposure and read out the sensor, pixel by pixel.'),
    'anim_buckets_etat': ('État', 'State'),
    'anim_buckets_m_repos': ('au repos', 'idle'),
    'anim_buckets_m_pose': ('pose en cours', 'exposing'),
    'anim_buckets_m_lecture': ('lecture en cours', 'reading out'),
    'anim_buckets_m_fini': ('image lue', 'image read'),
    'anim_buckets_t_pose': ('Temps posé', 'Time exposed'),
    'anim_buckets_attendu': ('Électrons attendus (± √N)', 'Electrons expected (± √N)'),
    'anim_buckets_lus': ('Pixels lus', 'Pixels read'),
    'anim_buckets_registre': ('registre de lecture', 'readout register'),
    'anim_buckets_ampli': ('amplificateur', 'amplifier'),
    'anim_buckets_titre_ccd': ('Le capteur (pixels = seaux)', 'The sensor (pixels = buckets)'),
    'anim_buckets_titre_image': ('Image reconstruite (électrons)', 'Reconstructed image (electrons)'),
})

ANIM_LOT3.update({
    # ------------------------------------------------------------ snellslaw
    'anim_snellslaw_milieu1': ('Milieu du haut', 'Upper medium'),
    'anim_snellslaw_milieu1_aide': ('Milieu d’où vient le rayon (règle n₁).', 'Medium the ray comes from (sets n₁).'),
    'anim_snellslaw_milieu2': ('Milieu du bas', 'Lower medium'),
    'anim_snellslaw_milieu2_aide': ('Milieu où passe le rayon (règle n₂).', 'Medium the ray enters (sets n₂).'),
    'anim_snellslaw_n1': ('Indice n₁', 'Index n₁'),
    'anim_snellslaw_n1_aide': ('Indice de réfraction du milieu du haut.', 'Refractive index of the upper medium.'),
    'anim_snellslaw_n2': ('Indice n₂', 'Index n₂'),
    'anim_snellslaw_n2_aide': ('Indice de réfraction du milieu du bas.', 'Refractive index of the lower medium.'),
    'anim_snellslaw_angle': ('Angle d’incidence θ₁', 'Angle of incidence θ₁'),
    'anim_snellslaw_angle_aide': ('Angle entre le rayon et la normale (on peut aussi faire glisser le laser dans la '
                                  'moitié haute).',
                                  'Angle between the ray and the normal (the laser can also be dragged in the upper '
                                  'half).'),
    'anim_snellslaw_t2': ('Angle de réfraction θ₂', 'Angle of refraction θ₂'),
    'anim_snellslaw_totale': ('réflexion totale', 'total internal reflection'),
    'anim_snellslaw_limite': ('Angle limite', 'Critical angle'),
    'anim_snellslaw_pas_de_limite': ('aucun (n₁ ≤ n₂)', 'none (n₁ ≤ n₂)'),
    'anim_snellslaw_reflechie': ('Part réfléchie (Fresnel)', 'Share reflected (Fresnel)'),
    'anim_snellslaw_brewster': ('Angle de Brewster', 'Brewster angle'),
    'anim_snellslaw_haut': ('haut', 'top'),
    'anim_snellslaw_bas': ('bas', 'bottom'),
})
for _k, _fr, _en in (('air', 'air (1,00)', 'air (1.00)'), ('eau', 'eau (1,33)', 'water (1.33)'),
                     ('huile', 'huile (1,50)', 'oil (1.50)'), ('flint', 'verre flint (1,66)', 'flint glass (1.66)'),
                     ('zircon', 'zircon (1,92)', 'zircon (1.92)'), ('diamant', 'diamant (2,42)', 'diamond (2.42)')):
    ANIM_LOT3['anim_snellslaw_m_' + _k] = (_fr, _en)

ANIM_LOT3.update({
    # ------------------------------------------------------------ lookbacktimesim
    'anim_lookbacktimesim_exemple': ('Exemple', 'Example'),
    'anim_lookbacktimesim_exemple_aide': ('Réglages libres, ou une supernova historique : vue en 1054 (nébuleuse du '
                                          'Crabe) ou en 1006.',
                                          'Free settings, or a historical supernova: seen in 1054 (Crab Nebula) or in '
                                          '1006.'),
    'anim_lookbacktimesim_libre': ('réglages libres', 'free settings'),
    'anim_lookbacktimesim_crabe': ('supernova de 1054 (Crabe)', 'supernova of 1054 (Crab)'),
    'anim_lookbacktimesim_sn1006': ('supernova de 1006', 'supernova of 1006'),
    'anim_lookbacktimesim_distance': ('Distance de l’étoile', 'Distance of the star'),
    'anim_lookbacktimesim_distance_aide': ('Distance entre l’étoile et l’observateur, en années-lumière.',
                                           'Distance between the star and the observer, in light-years.'),
    'anim_lookbacktimesim_explosion': ('Année de l’explosion', 'Year of the explosion'),
    'anim_lookbacktimesim_explosion_aide': ('Année (astronomique : 0 = 1 av. J.-C., −1 = 2 av. J.-C.) où l’étoile '
                                            'explose.',
                                            'Year (astronomical: 0 = 1 BC, −1 = 2 BC) when the star explodes.'),
    'anim_lookbacktimesim_vitesse_ans': ('Vitesse', 'Speed'),
    'anim_lookbacktimesim_vitesse_ans_aide': ('Années écoulées par seconde pendant la lecture.',
                                              'Years elapsed per second while playing.'),
    'anim_lookbacktimesim_ap': ('{a} apr. J.-C.', 'AD {a}'),
    'anim_lookbacktimesim_av': ('{a} av. J.-C.', '{a} BC'),
    'anim_lookbacktimesim_maintenant': ('Année affichée', 'Year shown'),
    'anim_lookbacktimesim_explose': ('L’étoile explose en', 'The star explodes in'),
    'anim_lookbacktimesim_vue': ('L’explosion est vue en', 'The explosion is seen in'),
    'anim_lookbacktimesim_ce_qu_il_voit': ('L’observateur voit', 'The observer sees'),
    'anim_lookbacktimesim_voit_sn': ('la supernova', 'the supernova'),
    'anim_lookbacktimesim_voit_etoile': ('l’étoile, encore intacte', 'the star, still intact'),
    'anim_lookbacktimesim_titre_scene': ('La lumière de l’explosion en route vers l’observateur',
                                         'The light of the explosion on its way to the observer'),
    'anim_lookbacktimesim_titre_frise': ('Frise chronologique', 'Timeline'),
    'anim_lookbacktimesim_m_explosion': ('explosion', 'explosion'),
    'anim_lookbacktimesim_m_vue': ('vue', 'seen'),
})
