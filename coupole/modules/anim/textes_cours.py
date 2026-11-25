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
    'anim_resolution_lambda_aide': ('Longueur d’onde observée : 550 nm au milieu du visible, 2 200 nm dans '
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
    # ================================================================ Les éléments d'une orbite
    'anim_orbitalelements_orbite': ('Orbite type', 'Typical orbit'),
    'anim_orbitalelements_orbite_aide': ('Choisir une orbite type règle les cinq éléments ; on peut ensuite les '
                                         'changer à la main.',
                                         'Choosing a typical orbit sets the five elements; you can then change them '
                                         'by hand.'),
    'anim_orbitalelements_o_libre': ('(réglage libre)', '(free setting)'),
    'anim_orbitalelements_o_iss': ('Station spatiale (≈ 420 km, i = 51,6°)', 'Space station (≈ 420 km, i = 51.6°)'),
    'anim_orbitalelements_o_polaire': ('Héliosynchrone (≈ 800 km, i = 98,6°)', 'Sun-synchronous (≈ 800 km, i = 98.6°)'),
    'anim_orbitalelements_o_gps': ('GPS (demi-jour sidéral, i = 55°)', 'GPS (half a sidereal day, i = 55°)'),
    'anim_orbitalelements_o_molniya': ('Molniya (e = 0,74, i = 63,4°)', 'Molniya (e = 0.74, i = 63.4°)'),
    'anim_orbitalelements_o_geo': ('Géostationnaire (42 164 km)', 'Geostationary (42,164 km)'),
    'anim_orbitalelements_a': ('Demi-grand axe a', 'Semi-major axis a'),
    'anim_orbitalelements_a_aide': ('Taille de l’orbite, depuis le centre de la Terre (rayon : 6 378 km) ; elle '
                                    'fixe la période : T = 2π √(a³ / GM).',
                                    'Size of the orbit, from the centre of the Earth (radius: 6,378 km); it sets '
                                    'the period: T = 2π √(a³ / GM).'),
    'anim_orbitalelements_e': ('Excentricité e', 'Eccentricity e'),
    'anim_orbitalelements_e_aide': ('Forme de l’orbite : 0 pour un cercle, proche de 1 pour une ellipse très '
                                    'allongée. Périgée a (1 − e), apogée a (1 + e).',
                                    'Shape of the orbit: 0 for a circle, close to 1 for a very elongated ellipse. '
                                    'Perigee a (1 − e), apogee a (1 + e).'),
    'anim_orbitalelements_i': ('Inclinaison i', 'Inclination i'),
    'anim_orbitalelements_i_aide': ('Angle entre le plan de l’orbite et celui de l’équateur : 0° équatoriale, 90° '
                                    'polaire, au-delà de 90° rétrograde (le satellite tourne en sens inverse de la '
                                    'Terre).',
                                    'Angle between the orbital plane and the equatorial plane: 0° equatorial, 90° '
                                    'polar, beyond 90° retrograde (the satellite goes round against the Earth’s '
                                    'rotation).'),
    'anim_orbitalelements_noeud': ('Longitude du nœud ascendant Ω', 'Longitude of the ascending node Ω'),
    'anim_orbitalelements_noeud_aide': ('Angle, dans le plan de l’équateur, du point vernal γ au nœud ascendant '
                                        '(là où le satellite traverse l’équateur vers le nord). Il oriente le plan '
                                        'de l’orbite.',
                                        'Angle, in the equatorial plane, from the vernal point γ to the ascending '
                                        'node (where the satellite crosses the equator heading north). It orients '
                                        'the orbital plane.'),
    'anim_orbitalelements_perigee': ('Argument du périgée ω', 'Argument of perigee ω'),
    'anim_orbitalelements_perigee_aide': ('Angle, dans le plan de l’orbite, du nœud ascendant au périgée. Il oriente '
                                          'l’ellipse dans son plan (sans effet sur un cercle).',
                                          'Angle, in the orbital plane, from the ascending node to the perigee. It '
                                          'orients the ellipse within its plane (no effect on a circle).'),
    'anim_orbitalelements_angles': ('Angles Ω, ω, i', 'Angles Ω, ω, i'),
    'anim_orbitalelements_angles_aide': ('Dessine les trois angles qui orientent l’orbite.',
                                         'Draws the three angles that orient the orbit.'),
    'anim_orbitalelements_plan': ('Plan de l’équateur', 'Equatorial plane'),
    'anim_orbitalelements_plan_aide': ('Plan de référence ; la partie de l’orbite au sud de l’équateur est en '
                                       'pointillé.',
                                       'Reference plane; the part of the orbit south of the equator is dotted.'),
    'anim_orbitalelements_trace': ('Trace au sol', 'Ground track'),
    'anim_orbitalelements_trace_aide': ('Points de la Terre survolés : la Terre tourne sous l’orbite (un tour en '
                                        '23 h 56 min), d’où le décalage d’une révolution à l’autre.',
                                        'Points on the Earth flown over: the Earth turns under the orbit (one turn in '
                                        '23 h 56 min), hence the shift from one revolution to the next.'),
    'anim_orbitalelements_t_espace': ('L’orbite dans l’espace (repère équatorial)', 'The orbit in space (equatorial frame)'),
    'anim_orbitalelements_t_trace': ('Trace au sol (trois dernières révolutions)', 'Ground track (last three revolutions)'),
    'anim_orbitalelements_vernal': ('γ point vernal', 'γ vernal point'),
    'anim_orbitalelements_t_plan': ('L’orbite dans son plan (ν : anomalie vraie)', 'The orbit in its own plane (ν: true anomaly)'),
    'anim_orbitalelements_noeud_asc': ('nœud ascendant', 'ascending node'),
    'anim_orbitalelements_perigee_m': ('périgée', 'perigee'),
    'anim_orbitalelements_apogee_m': ('apogée', 'apogee'),
    'anim_orbitalelements_satellite': ('satellite', 'satellite'),
    'anim_orbitalelements_km': ('km', 'km'),
    'anim_orbitalelements_altitude': ('altitude', 'altitude'),
    'anim_orbitalelements_d_ms': ('{m} min {s} s', '{m} min {s} s'),
    'anim_orbitalelements_d_hm': ('{h} h {m} min', '{h} h {m} min'),
    'anim_orbitalelements_d_j': ('{j} jours', '{j} days'),
    'anim_orbitalelements_v_periode': ('Période T', 'Period T'),
    'anim_orbitalelements_v_perigee': ('Périgée a (1 − e)', 'Perigee a (1 − e)'),
    'anim_orbitalelements_v_apogee': ('Apogée a (1 + e)', 'Apogee a (1 + e)'),
    'anim_orbitalelements_v_vitesses': ('Vitesse au périgée / à l’apogée', 'Speed at perigee / at apogee'),
    'anim_orbitalelements_v_position': ('Position', 'Position'),
    'anim_orbitalelements_v_temps': ('Temps depuis le passage au périgée', 'Time since perigee passage'),
    'anim_orbitalelements_v_genre': ('Orbite', 'Orbit'),
    'anim_orbitalelements_g_heurte': ('le périgée est sous la surface : le satellite s’écrase',
                                      'the perigee is below the surface: the satellite crashes'),
    'anim_orbitalelements_g_geostationnaire': ('géostationnaire : le satellite reste au-dessus du même point',
                                               'geostationary: the satellite stays above the same point'),
    'anim_orbitalelements_g_geosynchrone': ('géosynchrone : la trace au sol se referme chaque jour',
                                            'geosynchronous: the ground track closes every day'),
    'anim_orbitalelements_g_polaire': ('quasi polaire : elle survole presque toute la Terre',
                                       'near-polar: it flies over almost the whole Earth'),
    'anim_orbitalelements_g_retrograde': ('rétrograde (i > 90°)', 'retrograde (i > 90°)'),
    'anim_orbitalelements_g_prograde': ('directe (i < 90°)', 'prograde (i < 90°)'),
    'anim_orbitalelements_souris': ('Glisser dans la vue 3D : la faire tourner.', 'Drag in the 3D view: rotate it.'),
    # ================================================================ Le transfert de Hohmann
    'anim_hohmann_scenario': ('Transfert', 'Transfer'),
    'anim_hohmann_scenario_aide': ('Orbite de départ et d’arrivée, circulaires et dans le même plan.',
                                   'Departure and arrival orbits, circular and in the same plane.'),
    'anim_hohmann_s_leo_geo': ('Orbite basse (200 km) → géostationnaire', 'Low orbit (200 km) → geostationary'),
    'anim_hohmann_s_leo_iss': ('Orbite basse (200 km) → station spatiale (417 km)',
                               'Low orbit (200 km) → space station (417 km)'),
    'anim_hohmann_s_terre_lune': ('Orbite basse → orbite de la Lune', 'Low orbit → the Moon’s orbit'),
    'anim_hohmann_s_terre_mars': ('Terre → Mars (autour du Soleil)', 'Earth → Mars (around the Sun)'),
    'anim_hohmann_s_terre_venus': ('Terre → Vénus (autour du Soleil)', 'Earth → Venus (around the Sun)'),
    'anim_hohmann_s_terre_jupiter': ('Terre → Jupiter (autour du Soleil)', 'Earth → Jupiter (around the Sun)'),
    'anim_hohmann_auto': ('Partir à la fenêtre de tir', 'Leave at the launch window'),
    'anim_hohmann_auto_aide': ('Le vaisseau part tout seul quand la cible a la bonne avance (angle de phase) ; '
                               'décocher pour partir avec « Partir maintenant ».',
                               'The spacecraft leaves by itself when the target has the right lead (phase '
                               'angle); untick to leave with “Leave now”.'),
    'anim_hohmann_fantome': ('Cible à l’arrivée', 'Target at arrival'),
    'anim_hohmann_fantome_aide': ('Cercle pointillé : où sera la cible à l’arrivée si l’on part maintenant. La '
                                  'fenêtre de tir s’ouvre quand il tombe au bout de la demi-ellipse.',
                                  'Dotted circle: where the target will be at arrival if we leave now. The launch '
                                  'window opens when it falls at the end of the half-ellipse.'),
    'anim_hohmann_lancer': ('Partir maintenant', 'Leave now'),
    'anim_hohmann_lancer_aide': ('Première poussée tout de suite, quelle que soit la position de la cible.',
                                 'First burn right now, wherever the target is.'),
    'anim_hohmann_recommencer': ('Recommencer', 'Start again'),
    'anim_hohmann_recommencer_aide': ('Revenir avant le départ.', 'Go back to before the departure.'),
    'anim_hohmann_t_orbites': ('Les deux orbites et la demi-ellipse de transfert',
                               'The two orbits and the transfer half-ellipse'),
    'anim_hohmann_t_vitesses': ('Vitesses (vis-viva)', 'Speeds (vis-viva)'),
    'anim_hohmann_b_v1': ('orbite de départ', 'departure orbit'),
    'anim_hohmann_b_vd': ('ellipse, au départ', 'ellipse, at departure'),
    'anim_hohmann_b_va': ('ellipse, à l’arrivée', 'ellipse, at arrival'),
    'anim_hohmann_b_v2': ('orbite d’arrivée', 'arrival orbit'),
    'anim_hohmann_total': ('Δv total : {dv} km·s⁻¹', 'Total Δv: {dv} km·s⁻¹'),
    'anim_hohmann_fantome_m': ('cible à l’arrivée', 'target at arrival'),
    'anim_hohmann_n_terre': ('Terre', 'Earth'),
    'anim_hohmann_n_mars': ('Mars', 'Mars'),
    'anim_hohmann_n_venus': ('Vénus', 'Venus'),
    'anim_hohmann_n_jupiter': ('Jupiter', 'Jupiter'),
    'anim_hohmann_n_lune': ('Lune', 'Moon'),
    'anim_hohmann_n_geo_sat': ('satellite géostationnaire', 'geostationary satellite'),
    'anim_hohmann_n_iss': ('station', 'station'),
    'anim_hohmann_v_dv1': ('Première poussée Δv₁', 'First burn Δv₁'),
    'anim_hohmann_v_dv2': ('Seconde poussée Δv₂', 'Second burn Δv₂'),
    'anim_hohmann_v_dv': ('Δv total', 'Total Δv'),
    'anim_hohmann_v_duree': ('Durée du transfert (demi-ellipse)', 'Transfer time (half-ellipse)'),
    'anim_hohmann_v_phase': ('Avance de la cible au départ (angle de phase)', 'Target lead at departure (phase angle)'),
    'anim_hohmann_v_synodique': ('Une fenêtre de tir tous les', 'One launch window every'),
    'anim_hohmann_v_avance': ('Avance actuelle de la cible', 'Current target lead'),
    'anim_hohmann_v_etat': ('Vaisseau', 'Spacecraft'),
    'anim_hohmann_e_attente': ('en attente — fenêtre de tir dans {d}', 'waiting — launch window in {d}'),
    'anim_hohmann_e_transfert': ('en route — {d} depuis le départ', 'en route — {d} since departure'),
    'anim_hohmann_e_reussi': ('arrivé — rendez-vous réussi', 'arrived — rendezvous achieved'),
    'anim_hohmann_e_rate_avance': ('arrivé — la cible est passée {x} plus loin', 'arrived — the target is {x} ahead'),
    'anim_hohmann_e_rate_retard': ('arrivé — la cible a {x} de retard', 'arrived — the target is {x} behind'),
}
