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
    'anim_orion3d_depliement': ('Dépliement (ciel → 3D)', 'Unfolding (sky → 3D)'),
    'anim_orion3d_depliement_aide': ('0 % : la constellation telle qu’on la voit, toutes les étoiles sur la sphère '
                                     'céleste ; 100 % : chaque étoile et chaque nuage à sa distance mesurée, vus de '
                                     'côté.',
                                     '0 %: the constellation as we see it, every star on the celestial sphere; '
                                     '100 %: every star and cloud at its measured distance, seen from the side.'),
    'anim_orion3d_b_ciel': ('Vue du ciel', 'Sky view'),
    'anim_orion3d_b_ciel_aide': ('Replie la scène : la figure d’Orion vue de la Terre.',
                                 'Folds the scene back: Orion as seen from the Earth.'),
    'anim_orion3d_b_3d': ('Vue 3D', '3D view'),
    'anim_orion3d_b_3d_aide': ('Déplie la scène : les étoiles partent à leur distance et la vue tourne de côté.',
                               'Unfolds the scene: the stars move to their distances and the view turns sideways.'),
    'anim_orion3d_cible': ('Regarder', 'Look at'),
    'anim_orion3d_cible_aide': ('Toute la constellation, ou plongée vers la nébuleuse d’Orion (M42) ou la Tête de '
                                'Cheval.',
                                'The whole constellation, or a dive towards the Orion Nebula (M42) or the Horsehead.'),
    'anim_orion3d_c_orion': ('Orion entier', 'All of Orion'),
    'anim_orion3d_c_m42': ('la nébuleuse d’Orion (M42)', 'the Orion Nebula (M42)'),
    'anim_orion3d_c_tete': ('la Tête de Cheval', 'the Horsehead'),
    'anim_orion3d_image': ('Image :', 'Image:'),
    'anim_orion3d_image_aide': ('Photographie posée sur le ciel dans les plongées : télescopes au sol de l’ESO (VST, '
                                'VLT) ou télescope spatial Hubble (infrarouge pour la Tête de Cheval).',
                                'Photograph laid on the sky in the dives: ESO ground-based telescopes (VST, VLT) or '
                                'the Hubble Space Telescope (infrared for the Horsehead).'),
    'anim_orion3d_i_sol': ('ESO (VST, VLT)', 'ESO (VST, VLT)'),
    'anim_orion3d_i_hubble': ('Hubble', 'Hubble'),
    'anim_orion3d_figure': ('Figure de la constellation', 'Constellation figure'),
    'anim_orion3d_figure_aide': ('Lignes de la figure (Stellarium, ciel « moderne ») : en 3D, elles relient des étoiles '
                                 'que rien n’associe.',
                                 'Lines of the figure (Stellarium, “modern” sky): in 3D they join stars that nothing '
                                 'links.'),
    'anim_orion3d_noms': ('Noms', 'Names'),
    'anim_orion3d_noms_aide': ('Noms des étoiles principales et des nébuleuses (et distance en 3D).',
                               'Names of the main stars and nebulae (and distance in 3D).'),
    'anim_orion3d_nebuleuses': ('Nuages et nébuleuses', 'Clouds and nebulae'),
    'anim_orion3d_nebuleuses_aide': ('Nuages moléculaires Orion A et B, anneau de λ Orionis, boucle de Barnard, M42 et '
                                     'la Tête de Cheval, à leurs distances publiées.',
                                     'Orion A and B molecular clouds, λ Orionis ring, Barnard’s Loop, M42 and the '
                                     'Horsehead, at their published distances.'),
    'anim_orion3d_images': ('Images', 'Images'),
    'anim_orion3d_images_aide': ('Photographies de l’ESO et de l’ESA/Hubble (CC BY 4.0) posées sur le ciel à leur '
                                 'place exacte (chargées à la demande).',
                                 'ESO and ESA/Hubble photographs (CC BY 4.0) laid on the sky at their exact place '
                                 '(loaded on demand).'),
    'anim_orion3d_barres': ('Barres d’erreur', 'Error bars'),
    'anim_orion3d_barres_aide': ('Incertitude de chaque distance le long de la ligne de visée ; en tirets, la mesure '
                                 'directe d’une étoile affichée à sa distance publiée.',
                                 'Uncertainty of each distance along the line of sight; dashed, the direct '
                                 'measurement of a star shown at its published distance.'),
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
    'anim_orion3d_v_vue': ('Vue', 'View'),
    'anim_orion3d_vue_ciel': ('le ciel vu de la Terre', 'the sky seen from the Earth'),
    'anim_orion3d_vue_3d': ('en 3D', 'in 3D'),
    'anim_orion3d_vue_entre': ('dépliement {p} %', 'unfolding {p} %'),
    'anim_orion3d_v_cible': ('On regarde', 'Looking at'),
    'anim_orion3d_v_proche': ('Étoile de la figure la plus proche', 'Closest star of the figure'),
    'anim_orion3d_v_loin': ('Étoile de la figure la plus lointaine', 'Farthest star of the figure'),
    'anim_orion3d_v_ceinture': ('Ceinture', 'Belt'),
    'anim_orion3d_v_distances': ('Distances', 'Distances'),
    'anim_orion3d_d_publiees': ('publiées (Alnilam, Mintaka, Meissa, Hatysa : distance de leur groupe)',
                                'published (Alnilam, Mintaka, Meissa, Hatysa: distance of their group)'),
    'anim_orion3d_d_brutes': ('mesures directes brutes', 'raw direct measurements'),
    'anim_orion3d_v_echelle': ('Échelle', 'Scale'),
    'anim_orion3d_echelle': ('tout est à l’échelle, sauf la taille des étoiles (selon leur magnitude)',
                             'everything is to scale except the size of the stars (by magnitude)'),
    'anim_orion3d_v_couleurs': ('Couleurs', 'Colours'),
    'anim_orion3d_couleurs_accentuees': ('accentuées (saturation × 2,5)', 'enhanced (saturation × 2.5)'),
    'anim_orion3d_legende': ('couleur = température', 'colour = temperature'),
    'anim_orion3d_barre': ('{l} pc', '{l} pc'),
    'anim_orion3d_n_m42': ('M42', 'M42'),
    'anim_orion3d_n_tete': ('Tête de Cheval', 'Horsehead'),
    'anim_orion3d_n_orion_a': ('Orion A', 'Orion A'),
    'anim_orion3d_n_orion_b': ('Orion B', 'Orion B'),
    'anim_orion3d_n_lambda': ('anneau de λ Ori', 'λ Ori ring'),
    'anim_orion3d_n_barnard': ('boucle de Barnard', 'Barnard’s Loop'),
    'anim_orion3d_souris': ('Glisser : tourner la scène autour d’Orion (double-clic : revenir) ; molette ou pincer : '
                            'zoomer.',
                            'Drag: turn the scene around Orion (double-click: back); wheel or pinch: zoom.'),
    'anim_orion3d_adapte': ('Propre à Coupole (pas dans ClassAction) : SIMBAD, Gaia DR3, Hipparcos 2007 et articles '
                            'cités dans les fiches',
                            'Coupole’s own (not in ClassAction): SIMBAD, Gaia DR3, Hipparcos 2007 and papers cited '
                            'in the data sheets'),
    'anim_orion3d_lien': ('Sources et crédits : NOTICE de Coupole', 'Sources and credits: Coupole NOTICE'),
}
