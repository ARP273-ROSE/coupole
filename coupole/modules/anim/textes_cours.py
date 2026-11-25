"""Textes FR/EN des animations propres à Coupole tirées des cours d'astronomie générale (diffraction et pouvoir de
résolution, éléments d'une orbite, transfert de Hohmann, radiant des étoiles filantes).  Fusionnés dans
``textes.TEXTES`` (et exportés tels quels vers Coupole Web)."""

ANIM_COURS = {
    # ================================================================ Diffraction et pouvoir de résolution
    'anim_resolution_instrument': ('Instrument', 'Instrument'),
    'anim_resolution_instrument_aide': ('Choisir un instrument règle son diamètre et son obstruction centrale ; on '
                                        'peut ensuite les changer à la main.',
                                        'Choosing an instrument sets its diameter and central obstruction; you can '
                                        'then change them by hand.'),
    'anim_resolution_i_libre': ('(réglage libre)', '(free setting)'),
    'anim_resolution_i_oeil': ('Œil (pupille de 7 mm)', 'Eye (7 mm pupil)'),
    'anim_resolution_i_lunette80': ('Lunette de 80 mm', '80 mm refractor'),
    'anim_resolution_i_sc200': ('Schmidt-Cassegrain de 203 mm (ε = 0,34)', '203 mm Schmidt-Cassegrain (ε = 0.34)'),
    'anim_resolution_i_m1': ('Télescope de 1 m', '1 m telescope'),
    'anim_resolution_i_hubble': ('Hubble, 2,4 m (ε = 0,33)', 'Hubble, 2.4 m (ε = 0.33)'),
    'anim_resolution_i_vlt': ('Un télescope du VLT, 8,2 m (ε = 0,14)', 'One VLT telescope, 8.2 m (ε = 0.14)'),
    'anim_resolution_i_elt': ('ELT, 39,3 m (obstruction non modélisée)', 'ELT, 39.3 m (obstruction not modelled)'),
    'anim_resolution_diametre': ('Diamètre D', 'Diameter D'),
    'anim_resolution_diametre_aide': ('Diamètre de l’objectif ou du miroir principal (échelle logarithmique).',
                                      'Diameter of the objective lens or primary mirror (logarithmic scale).'),
    'anim_resolution_obstruction': ('Obstruction centrale ε', 'Central obstruction ε'),
    'anim_resolution_obstruction_aide': ('Diamètre du miroir secondaire rapporté à D (0 : lunette). L’obstruction '
                                         'resserre un peu la tache centrale mais envoie plus de lumière dans les '
                                         'anneaux.',
                                         'Secondary mirror diameter divided by D (0: refractor). The obstruction '
                                         'slightly narrows the central spot but sends more light into the rings.'),
    'anim_resolution_lambda': ('Longueur d’onde λ', 'Wavelength λ'),
    'anim_resolution_lambda_aide': ('Longueur d’onde observée : 550 nm au milieu du visible, 2 200 nm dans '
                                    'l’infrarouge (bande K). La tache grandit avec λ.',
                                    'Observed wavelength: 550 nm in the middle of the visible range, 2,200 nm in '
                                    'the infrared (K band). The spot grows with λ.'),
    'anim_resolution_separation': ('Séparation des deux étoiles', 'Separation of the two stars'),
    'anim_resolution_separation_aide': ('Écart angulaire entre les deux étoiles, en secondes d’arc (échelle '
                                        'logarithmique).',
                                        'Angular distance between the two stars, in arcseconds (logarithmic '
                                        'scale).'),
    'anim_resolution_dmag': ('Écart d’éclat Δm', 'Brightness difference Δm'),
    'anim_resolution_dmag_aide': ('La seconde étoile est plus faible de Δm magnitudes (flux divisé par 2,512 '
                                  'à chaque magnitude) : un compagnon faible se perd dans les anneaux de '
                                  'l’étoile brillante.',
                                  'The second star is Δm magnitudes fainter (flux divided by 2.512 for each '
                                  'magnitude): a faint companion gets lost in the rings of the bright star.'),
    'anim_resolution_seeing': ('Turbulence (seeing)', 'Turbulence (seeing)'),
    'anim_resolution_seeing_aide': ('Largeur à mi-hauteur de l’image d’une étoile en pose longue à travers '
                                    'l’atmosphère. 0 : au-dessus de l’atmosphère (télescope spatial, ou optique '
                                    'adaptative parfaite).',
                                    'Full width at half maximum of a star image in a long exposure through the '
                                    'atmosphere. 0: above the atmosphere (space telescope, or perfect adaptive '
                                    'optics).'),
    'anim_resolution_etirer': ('Étirer l’image (voir les anneaux)', 'Stretch the image (see the rings)'),
    'anim_resolution_etirer_aide': ('Échelle logarithmique de l’intensité (trois décades) : le premier anneau ne '
                                    'porte que 1,7 % de l’éclat du centre, invisible sans étirement.',
                                    'Logarithmic intensity scale (three decades): the first ring is only 1.7% as '
                                    'bright as the centre, invisible without a stretch.'),
    'anim_resolution_anneau': ('Premier anneau noir', 'First dark ring'),
    'anim_resolution_anneau_aide': ('Cercle pointillé au rayon du premier anneau noir de chaque étoile.',
                                    'Dotted circle at the radius of the first dark ring of each star.'),
    'anim_resolution_t_image': ('Image des deux étoiles', 'Image of the two stars'),
    'anim_resolution_t_coupe': ('Intensité le long de la droite qui joint les étoiles',
                                'Intensity along the line joining the stars'),
    'anim_resolution_axe_x': ('position (″)', 'position (″)'),
    'anim_resolution_axe_y': ('intensité', 'intensity'),
    'anim_resolution_rayleigh_ecart': ('traits : écart de Rayleigh 1,22 λ / D',
                                       'lines: Rayleigh separation 1.22 λ / D'),
    'anim_resolution_v_rayleigh': ('1,22 λ / D', '1.22 λ / D'),
    'anim_resolution_v_anneau': ('Premier anneau noir', 'First dark ring'),
    'anim_resolution_v_fwhm': ('Largeur à mi-hauteur d’une étoile', 'Full width at half maximum of a star'),
    'anim_resolution_v_rapport': ('Séparation / (1,22 λ / D)', 'Separation / (1.22 λ / D)'),
    'anim_resolution_v_creux': ('Intensité au creux entre les sommets', 'Intensity in the dip between the peaks'),
    'anim_resolution_du_sommet': ('du plus faible sommet', 'of the fainter peak'),
    'anim_resolution_aucun_creux': ('aucun : un seul sommet', 'none: a single peak'),
    'anim_resolution_v_verdict': ('Les deux étoiles', 'The two stars'),
    'anim_resolution_separees': ('séparées', 'resolved'),
    'anim_resolution_limite': ('à la limite de la séparation', 'at the resolution limit'),
    'anim_resolution_confondues': ('confondues', 'unresolved'),
    'anim_resolution_v_dturb': ('Diamètre où la tache d’Airy égale le seeing',
                                'Diameter at which the Airy spot equals the seeing'),
}
