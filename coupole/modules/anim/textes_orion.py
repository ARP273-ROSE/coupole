"""Textes FR/EN de la version 0.5.0 : spectres sur bases physiques (Explorateur de spectres, Parallaxe
spectroscopique), « Orion en 3D », fiches au survol et couleur vraie des étoiles : (fr, en).  Fusionnés dans
``textes.TEXTES`` (et exportés tels quels vers Coupole Web)."""

ANIM_ORION = {
    # ------------------------------------------------------------ spectres physiques (remarques communes)
    'spectres_d_borne': ('étalonnage borné (hors du domaine publié)', 'calibration clamped (outside the published range)'),
    'spectres_d_interpole': ('classe interpolée entre ses voisines', 'class interpolated between its neighbours'),
    'spectres_d_bc_naines': ('magnitude absolue tirée du rayon et de la température effective avec la correction '
                             'bolométrique des naines',
                             'absolute magnitude derived from the radius and the effective temperature with the dwarfs’ '
                             'bolometric correction'),
    'spectres_d_logg': ('atmosphère extrapolée (log g hors de la grille ATLAS9)',
                        'atmosphere extrapolated (log g outside the ATLAS9 grid)'),
    'spectres_d_froide': ('atmosphère extrapolée (température effective < 3 500 K, hors de la grille ATLAS9)',
                          'atmosphere extrapolated (effective temperature < 3,500 K, outside the ATLAS9 grid)'),
    'anim_spectrum010_logg': ('Gravité de surface log g', 'Surface gravity log g'),
    'anim_spectrum010_principales': ('Raies les plus intenses', 'Strongest lines'),
    'anim_spectrum010_remarque': ('Remarque', 'Note'),
    'anim_spectrum010_echelle': ('Raies', 'Lines'),
    'anim_spectrum010_echelle_aide': ('Contraste pédagogique (par défaut) : raies élargies à 0,8 nm et approfondies '
                                      '(rapport au continu élevé au cube) pour qu’on les voie, comme sur un spectre de démonstration ; échelle '
                                      'réaliste : profondeurs et largeurs calculées, souvent à peine visibles (Soleil).',
                                      'Teaching contrast (default): lines widened to 0.8 nm and deepened (ratio to the continuum cubed) so '
                                      'that they can be seen, as on a demonstration spectrum; realistic scale: computed '
                                      'depths and widths, often barely visible (the Sun).'),
    'anim_spectrum010_e_pedago': ('contraste pédagogique', 'teaching contrast'),
    'anim_spectrum010_e_realiste': ('échelle réaliste', 'realistic scale'),
    'anim_spectrum010_echelle_v': ('Échelle des raies', 'Line scale'),
    'anim_spectrum010_e_pedago_v': ('contraste pédagogique : raies élargies (0,8 nm) et approfondies (rapport au continu au cube)',
                                    'teaching contrast: lines widened (0.8 nm) and deepened (ratio to the continuum cubed)'),
    'anim_spectrum010_e_realiste_v': ('réaliste (profondeurs et largeurs calculées)',
                                      'realistic (computed depths and widths)'),
    'anim_spectrum010_contraste_note': ('Contraste pédagogique : raies renforcées pour être visibles (réglage « Raies »).',
                                        'Teaching contrast: lines enhanced to be visible (“Lines” setting).'),
    'anim_spectroparallax_etalonnage': ('Étalonnage de la magnitude absolue', 'Absolute magnitude calibration'),
    'anim_spectroparallax_ancien': ('ancien étalonnage (aucune magnitude absolue publiée pour ce type et cette classe)',
                                    'former calibration (no published absolute magnitude for this type and class)'),
    'anim_spectroparallax_f_ch': ('bande G (CH)', 'G band (CH)'),

    # ------------------------------------------------------------ fiche au survol
    'anim_aide_fiche': ('Survoler ou toucher une étoile ou une nébuleuse : sa fiche (valeurs et sources) ; au clavier, '
                        'Tab passe d’un objet à l’autre (du plus brillant au plus faible), les flèches aussi quand une '
                        'fiche est ouverte, Échap la ferme.',
                        'Hover over or touch a star or a nebula: its data sheet (values and sources); with the keyboard, '
                        'Tab goes from one object to the next (brightest first), so do the arrows while a sheet is '
                        'open, Escape closes it.'),
    'anim_fiche_type': ('Type', 'Type'),
    'anim_fiche_mag_v': ('Magnitude V', 'V magnitude'),
    'anim_fiche_mag_abs': ('Magnitude absolue', 'Absolute magnitude'),
    'anim_fiche_distance': ('Distance', 'Distance'),
    'anim_fiche_al': ('al', 'ly'),
    'anim_fiche_incertaine': ('mesure incertaine', 'uncertain measurement'),
    'anim_fiche_distance_affichee': ('Distance affichée', 'Displayed distance'),
    'anim_fiche_autres_mesures': ('Autres mesures', 'Other measurements'),
    'anim_fiche_teff': ('Température', 'Temperature'),
    'anim_fiche_rayon': ('Rayon', 'Radius'),
    'anim_fiche_luminosite': ('Luminosité', 'Luminosity'),
    'anim_fiche_taille': ('Taille', 'Size'),
    'anim_fiche_longueur': ('Longueur', 'Length'),
    'anim_fiche_diametre': ('Diamètre', 'Diameter'),
    'anim_fiche_arc': ('Arc', 'Arc'),
    'anim_fiche_age': ('Âge', 'Age'),
    'anim_fiche_ma': ('Ma', 'Myr'),
    'anim_fiche_excitatrices': ('Étoiles excitatrices', 'Exciting stars'),

    # ------------------------------------------------------------ règle typographique (unités SI)
    'anim_retrograde_u_vitesse': ('°·j⁻¹', '°·d⁻¹'),
    'anim_wagonwheel_par_image': ('° par image', '° per frame'),

    # ------------------------------------------------------------ couleur vraie (diagramme HR)
    'anim_hrexplorer_couleur_t': ('Couleur = température', 'Colour = temperature'),
    'anim_hrexplorer_couleur_t_aide': ('Chaque étoile prend la couleur d’un corps noir à sa température (CIE 1931 → '
                                       'sRGB) ; le contour garde la couleur de son groupe. Décoché : couleur du '
                                       'groupe.',
                                       'Each star takes the colour of a black body at its temperature (CIE 1931 → '
                                       'sRGB); its outline keeps the colour of its group. Unticked: group colour.'),
    'anim_bigdipper_source': ('Distances', 'Distances'),
    'anim_bigdipper_source_v': ('parallaxes adoptées par SIMBAD (Hipparcos 2007, Gaia), consultées le 14/10/2026',
                                'parallaxes adopted by SIMBAD (Hipparcos 2007, Gaia), retrieved on 14/10/2026'),

    # ------------------------------------------------------------ Orion en 3D
    'anim_orion3d_b_face': ('De face (vue de la Terre)', 'Face-on (seen from the Earth)'),
    'anim_orion3d_b_face_aide': ('Regarde Orion depuis la Terre : les projections sur la sphère céleste dessinent la '
                                 'constellation.',
                                 'Looks at Orion from the Earth: the projections on the celestial sphere draw the '
                                 'constellation.'),
    'anim_orion3d_b_cote': ('De côté', 'From the side'),
    'anim_orion3d_b_cote_aide': ('La Terre en bas, Orion en haut : chaque étoile à sa distance.',
                                 'The Earth at the bottom, Orion at the top: each star at its distance.'),
    'anim_orion3d_unite': ('Distances en', 'Distances in'),
    'anim_orion3d_unite_aide': ('Unité des distances écrites à côté des étoiles : années-lumière ou parsecs (1 pc = '
                                '3,26 al).',
                                'Unit of the distances written next to the stars: light-years or parsecs (1 pc = '
                                '3.26 ly).'),
    'anim_orion3d_u_al': ('années-lumière', 'light-years'),
    'anim_orion3d_u_pc': ('parsecs', 'parsecs'),
    'anim_orion3d_lignes': ('Lignes de visée', 'Lines of sight'),
    'anim_orion3d_lignes_aide': ('De la Terre à chaque étoile : vue de la Terre, chaque étoile est quelque part sur sa '
                                 'ligne de visée.',
                                 'From the Earth to each star: seen from the Earth, each star lies somewhere along its '
                                 'line of sight.'),
    'anim_orion3d_noms': ('Noms et distances', 'Names and distances'),
    'anim_orion3d_noms_aide': ('Nom de chaque étoile, de M42 et de la Tête de Cheval, avec sa distance.',
                               'Name of each star, of M42 and of the Horsehead, with its distance.'),
    'anim_orion3d_sphere': ('Sphère céleste', 'Celestial sphere'),
    'anim_orion3d_sphere_aide': ('Projection de chaque étoile sur la sphère céleste, où se dessine la figure d’Orion '
                                 'telle qu’on la voit.',
                                 'Projection of each star on the celestial sphere, where the figure of Orion appears '
                                 'as we see it.'),
    'anim_orion3d_figure': ('Figure dans l’espace', 'Figure in space'),
    'anim_orion3d_figure_aide': ('Les traits de la figure (Stellarium, ciel « moderne ») entre les étoiles à leur '
                                 'distance : de côté, ils relient des étoiles que rien n’associe.',
                                 'The lines of the figure (Stellarium, “modern” sky) between the stars at their '
                                 'distance: from the side, they join stars that nothing links.'),
    'anim_orion3d_nebuleuses': ('M42 et IC 434 en volume', 'M42 and IC 434 in volume'),
    'anim_orion3d_nebuleuses_aide': ('La nébuleuse d’Orion (cloque creusée dans le nuage OMC-1, Trapèze, Voile) et IC 434 '
                                     '(front rouge éclairé par σ Ori, pilier de la Tête de Cheval, bord d’Orion B) à leur '
                                     'position exacte, taille agrandie pour être visibles.',
                                     'The Orion Nebula (blister hollowed into the OMC-1 cloud, Trapezium, Veil) and IC 434 '
                                     '(red front lit by σ Ori, Horsehead pillar, edge of Orion B) at their exact position, '
                                     'enlarged to be visible.'),
    'anim_orion3d_trapeze': ('Trapèze (θ¹ Ori C)', 'Trapezium (θ¹ Ori C)'),
    'anim_orion3d_n_ic434': ('IC 434 et la Tête de Cheval', 'IC 434 and the Horsehead'),
    'anim_orion3d_agrandi': ('M42 et IC 434 : taille agrandie ×{k}, position et distance exactes ; forme de M42 au-delà '
                             'de 0,5 pc et profondeur d’IC 434 schématiques',
                             'M42 and IC 434: size enlarged ×{k}, exact position and distance; shape of M42 beyond '
                             '0.5 pc and depth of IC 434 schematic'),
    'anim_orion3d_nuages': ('Nuages Orion A et B', 'Orion A and B clouds'),
    'anim_orion3d_nuages_aide': ('Squelettes publiés des nuages moléculaires géants Orion A et Orion B (Zucker et al. '
                                 '2021).',
                                 'Published skeletons of the giant molecular clouds Orion A and Orion B (Zucker et al. '
                                 '2021).'),
    'anim_orion3d_barres': ('Barres d’erreur', 'Error bars'),
    'anim_orion3d_barres_aide': ('Incertitude de chaque distance mesurée, le long de la ligne de visée (Alnilam, '
                                 'Mintaka, Meissa et Hatysa, placées à la distance de leur groupe, n’en ont pas : leur '
                                 'mesure propre est dans les valeurs).',
                                 'Uncertainty of each measured distance, along the line of sight (Alnilam, Mintaka, '
                                 'Meissa and Hatysa, placed at the distance of their group, have none: their own '
                                 'measurement is in the values).'),
    'anim_orion3d_accentuees': ('Couleurs accentuées', 'Enhanced colours'),
    'anim_orion3d_accentuees_aide': ('Renforce la saturation des couleurs vraies, pâles à l’œil (choix pédagogique, '
                                     'désactivé par défaut).',
                                     'Boosts the saturation of the true colours, pale to the eye (teaching choice, off '
                                     'by default).'),
    'anim_orion3d_brutes': ('Distances mesurées brutes', 'Raw measured distances'),
    'anim_orion3d_brutes_aide': ('Alnilam, Mintaka, Meissa et Hatysa à leur parallaxe propre (très incertaine) au lieu '
                                 'de la distance publiée de leur groupe d’étoiles.',
                                 'Alnilam, Mintaka, Meissa and Hatysa at their own (very uncertain) parallax instead of '
                                 'the published distance of their star group.'),
    'anim_orion3d_mesure': ('mesure :', 'measured:'),
    'anim_orion3d_v_distances': ('Distances', 'Distances'),
    'anim_orion3d_d_publiees': ('publiées (Alnilam, Mintaka, Meissa, Hatysa : distance de leur groupe)',
                                'published (Alnilam, Mintaka, Meissa, Hatysa: distance of their group)'),
    'anim_orion3d_d_brutes': ('mesures directes brutes', 'raw direct measurements'),
    'anim_orion3d_v_couleurs': ('Couleurs', 'Colours'),
    'anim_orion3d_couleurs_accentuees': ('accentuées (saturation × 2,5)', 'enhanced (saturation × 2.5)'),
    'anim_orion3d_legende': ('couleur = température', 'colour = temperature'),
    'anim_orion3d_n_m42': ('M42', 'M42'),
    'anim_orion3d_n_tete': ('Tête de Cheval', 'Horsehead'),
    'anim_orion3d_n_orion_a': ('Orion A', 'Orion A'),
    'anim_orion3d_n_orion_b': ('Orion B', 'Orion B'),
    'anim_orion3d_souris': ('Glisser : tourner la scène (de face : la figure du ciel ; de côté : les profondeurs) ; '
                            'double-clic : revenir ; molette ou pincer : zoomer.',
                            'Drag: turn the scene (face-on: the figure in the sky; from the side: the depths); '
                            'double-click: back; wheel or pinch: zoom.'),
    'anim_orion3d_adapte': ('Propre à Coupole (pas dans ClassAction) : SIMBAD, Gaia DR3, Hipparcos 2007 et articles '
                            'cités dans les fiches',
                            'Coupole’s own (not in ClassAction): SIMBAD, Gaia DR3, Hipparcos 2007 and papers cited '
                            'in the data sheets'),
    'anim_orion3d_lien': ('Sources et crédits : NOTICE de Coupole', 'Sources and credits: Coupole NOTICE'),
}
