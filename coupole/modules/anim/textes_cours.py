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
    # ================================================================ Étoiles filantes et radiant
    'anim_meteorradiant_essaim': ('Pluie d’étoiles filantes', 'Meteor shower'),
    'anim_meteorradiant_essaim_aide': ('Essaim observé, la nuit de son maximum (radiant, vitesse et ZHR du '
                                       'calendrier de l’International Meteor Organization).',
                                       'Shower observed on the night of its maximum (radiant, speed and ZHR from '
                                       'the International Meteor Organization calendar).'),
    'anim_meteorradiant_e_quadrantides': ('Quadrantides (3–4 janvier)', 'Quadrantids (3–4 January)'),
    'anim_meteorradiant_e_lyrides': ('Lyrides (22 avril)', 'Lyrids (22 April)'),
    'anim_meteorradiant_e_eta_aquarides': ('Êta Aquarides (6 mai)', 'Eta Aquariids (6 May)'),
    'anim_meteorradiant_e_perseides': ('Perséides (12 août)', 'Perseids (12 August)'),
    'anim_meteorradiant_e_orionides': ('Orionides (21 octobre)', 'Orionids (21 October)'),
    'anim_meteorradiant_e_leonides': ('Léonides (17 novembre)', 'Leonids (17 November)'),
    'anim_meteorradiant_e_geminides': ('Géminides (14 décembre)', 'Geminids (14 December)'),
    'anim_meteorradiant_heure': ('Heure locale', 'Local time'),
    'anim_meteorradiant_heure_aide': ('Heure solaire moyenne, de 18 h à 6 h du matin (30 h).',
                                      'Mean solar time, from 6 pm to 6 am (30 h).'),
    'anim_meteorradiant_mlim': ('Magnitude limite du ciel', 'Sky limiting magnitude'),
    'anim_meteorradiant_mlim_aide': ('Étoiles les plus faibles visibles à l’œil nu : 6,5 sous un ciel pur de '
                                     'campagne, 4 en banlieue, 3 en ville. Chaque magnitude perdue divise le taux '
                                     'par r (indice de population de l’essaim, 2 à 2,6).',
                                     'Faintest stars visible to the naked eye: 6.5 under a pure country sky, 4 in '
                                     'the suburbs, 3 in town. Each magnitude lost divides the rate by r (the '
                                     'shower’s population index, 2 to 2.6).'),
    'anim_meteorradiant_prolonger': ('Prolonger les traînées', 'Extend the trails'),
    'anim_meteorradiant_prolonger_aide': ('Prolonge chaque traînée vers l’arrière (pointillés) : toutes se croisent '
                                          'au radiant.',
                                          'Extends each trail backwards (dotted): they all cross at the radiant.'),
    'anim_meteorradiant_etoiles': ('Étoiles', 'Stars'),
    'anim_meteorradiant_etoiles_aide': ('Étoiles de fond (tirées au hasard, pas un vrai catalogue) : elles tournent '
                                        'avec le radiant.',
                                        'Background stars (random, not a real catalogue): they turn with the '
                                        'radiant.'),
    'anim_meteorradiant_t_ciel': ('Le ciel vu de dessous (zénith au centre, est à gauche)',
                                  'The sky seen from below (zenith at the centre, east on the left)'),
    'anim_meteorradiant_t_nuit': ('Au fil de la nuit', 'Through the night'),
    'anim_meteorradiant_radiant': ('radiant', 'radiant'),
    'anim_meteorradiant_n': ('N', 'N'),
    'anim_meteorradiant_e': ('E', 'E'),
    'anim_meteorradiant_s': ('S', 'S'),
    'anim_meteorradiant_o': ('O', 'W'),
    'anim_meteorradiant_axe_heure': ('heure locale', 'local time'),
    'anim_meteorradiant_axe_hauteur': ('hauteur (°)', 'altitude (°)'),
    'anim_meteorradiant_leg_hauteur': ('trait plein : hauteur du radiant', 'solid: radiant altitude'),
    'anim_meteorradiant_leg_taux': ('pointillés : taux attendu (90° ↔ ZHR = {zhr} par heure)',
                                    'dotted: expected rate (90° ↔ ZHR = {zhr} per hour)'),
    'anim_meteorradiant_leg_grise': ('grisé : crépuscule et jour', 'shaded: twilight and day'),
    'anim_meteorradiant_ad': ('{h} h {m} min', '{h}h {m}m'),
    'anim_meteorradiant_date': ('vers le {j} {m}', 'around {m} {j}'),
    'anim_meteorradiant_c_bouvier': ('Bouvier', 'Boötes'),
    'anim_meteorradiant_c_lyre': ('Lyre', 'Lyra'),
    'anim_meteorradiant_c_verseau': ('Verseau', 'Aquarius'),
    'anim_meteorradiant_c_persee': ('Persée', 'Perseus'),
    'anim_meteorradiant_c_orion': ('Orion', 'Orion'),
    'anim_meteorradiant_c_lion': ('Lion', 'Leo'),
    'anim_meteorradiant_c_gemeaux': ('Gémeaux', 'Gemini'),
    'anim_meteorradiant_v_maximum': ('Maximum', 'Peak'),
    'anim_meteorradiant_v_radiant': ('Radiant', 'Radiant'),
    'anim_meteorradiant_v_vitesse': ('Vitesse d’entrée dans l’atmosphère', 'Atmospheric entry speed'),
    'anim_meteorradiant_v_zhr': ('ZHR (taux horaire zénithal)', 'ZHR (zenithal hourly rate)'),
    'anim_meteorradiant_v_heure': ('Heure', 'Time'),
    'anim_meteorradiant_v_hauteur': ('Hauteur du radiant', 'Radiant altitude'),
    'anim_meteorradiant_sous_horizon': ('sous l’horizon ({h})', 'below the horizon ({h})'),
    'anim_meteorradiant_v_taux': ('Taux attendu (ZHR × sin h, magnitude limite)', 'Expected rate (ZHR × sin h, limiting magnitude)'),
    'anim_meteorradiant_par_heure': ('≈ {n} par heure', '≈ {n} per hour'),
    'anim_meteorradiant_v_culmination': ('Le radiant culmine', 'The radiant culminates'),
    'anim_meteorradiant_v_soleil': ('Hauteur du Soleil', 'Sun altitude'),
    'anim_meteorradiant_ciel_nuit': ('nuit noire', 'full darkness'),
    'anim_meteorradiant_ciel_crepuscule': ('crépuscule', 'twilight'),
    'anim_meteorradiant_ciel_jour': ('jour', 'daylight'),
    # ================================================================ Interférences et interférométrie
    'anim_interferometry_instrument': ('Instrument', 'Instrument'),
    'anim_interferometry_montage': ('Montage', 'Set-up'),
    'anim_interferometry_montage_aide': ('Deux télescopes recombinés (interférométrie stellaire), ou les anneaux de '
                                         'Newton : une lentille posée sur une lame de verre.',
                                         'Two recombined telescopes (stellar interferometry), or Newton’s rings: a lens '
                                         'resting on a glass plate.'),
    'anim_interferometry_m_interferometre': ('interféromètre (deux télescopes)', 'interferometer (two telescopes)'),
    'anim_interferometry_m_anneaux': ('anneaux de Newton', 'Newton’s rings'),
    'anim_interferometry_rayon': ('Rayon de courbure de la lentille R', 'Radius of curvature of the lens R'),
    'anim_interferometry_rayon_aide': ('Plus la lentille est plate (R grand), plus la lame d’air s’épaissit lentement '
                                       'et plus les anneaux sont larges : r ∝ √R.',
                                       'The flatter the lens (large R), the more slowly the air film thickens and the '
                                       'wider the rings: r ∝ √R.'),
    'anim_interferometry_indice': ('Indice de la lame n', 'Index of the film n'),
    'anim_interferometry_indice_aide': ('1 pour de l’air, 1,33 pour de l’eau glissée entre la lentille et la lame : '
                                        'la longueur d’onde y est n fois plus courte, les anneaux se resserrent.',
                                        '1 for air, 1.33 for water slipped between lens and plate: the wavelength is '
                                        'n times shorter there, the rings tighten.'),
    'anim_interferometry_cote': ('Vu', 'Seen'),
    'anim_interferometry_cote_aide': ('En réflexion (lumière renvoyée vers le haut : centre noir) ou en transmission '
                                      '(lumière qui traverse : figure complémentaire, centre clair).',
                                      'In reflection (light sent back up: dark centre) or in transmission (light going '
                                      'through: complementary pattern, bright centre).'),
    'anim_interferometry_c_reflexion': ('en réflexion', 'in reflection'),
    'anim_interferometry_c_transmission': ('en transmission', 'in transmission'),
    'anim_interferometry_blanche': ('Lumière blanche', 'White light'),
    'anim_interferometry_blanche_aide': ('Chaque longueur d’onde donne ses anneaux : ils se mélangent en teintes de '
                                         'Newton, puis en blanc loin du centre.',
                                         'Each wavelength makes its own rings: they blend into Newton’s colours, then '
                                         'into white far from the centre.'),
    'anim_interferometry_t_anneaux': ('Les anneaux de Newton', 'Newton’s rings'),
    'anim_interferometry_t_lame': ('Coupe : la lame d’air (courbure exagérée)', 'Cross-section: the air film (curvature '
                                   'exaggerated)'),
    'anim_interferometry_t_profil': ('Éclairement selon la distance au centre', 'Brightness versus distance from the '
                                     'centre'),
    'anim_interferometry_verre': ('lame de verre', 'glass plate'),
    'anim_interferometry_legende_lame': ('e(r) = r²/2R ; retard 2ne + λ/2', 'e(r) = r²/2R; delay 2ne + λ/2'),
    'anim_interferometry_axe_r': ('r (mm)', 'r (mm)'),
    'anim_interferometry_mm': ('{x} mm', '{x} mm'),
    'anim_interferometry_nm': ('{x} nm', '{x} nm'),
    'anim_interferometry_trois': ('{a} ; {b} ; {c} mm', '{a}; {b}; {c} mm'),
    'anim_interferometry_v_anneaux': ('Anneaux sombres r₁, r₂, r₃ = √(kλR/n)', 'Dark rings r₁, r₂, r₃ = √(kλR/n)'),
    'anim_interferometry_v_ecart10': ('Écart du 9ᵉ au 10ᵉ anneau (ils se resserrent)', 'Gap from the 9th to the 10th '
                                      'ring (they tighten)'),
    'anim_interferometry_v_centre': ('Centre (lentille au contact)', 'Centre (lens in contact)'),
    'anim_interferometry_centre_reflexion': ('noir : déphasage de π à la réflexion sur le verre', 'dark: phase shift '
                                             'of π on reflection off the glass'),
    'anim_interferometry_centre_transmission': ('clair', 'bright'),
    'anim_interferometry_v_lame': ('Épaisseur de la lame au 1ᵉʳ anneau', 'Film thickness at the 1st ring'),
    'anim_interferometry_v_blanche': ('En lumière blanche', 'In white light'),
    'anim_interferometry_teintes': ('teintes de Newton près du centre, blanc au-delà', 'Newton’s colours near the '
                                    'centre, white further out'),
    'anim_interferometry_instrument_aide': ('Choisir un instrument règle sa base et le diamètre de ses ouvertures ; '
                                            'on peut ensuite les changer à la main.',
                                            'Choosing an instrument sets its baseline and the diameter of its '
                                            'apertures; you can then change them by hand.'),
    'anim_interferometry_i_libre': ('(réglage libre)', '(free setting)'),
    'anim_interferometry_i_young': ('Fentes d’Young (écart 0,5 mm)', 'Young’s slits (0.5 mm apart)'),
    'anim_interferometry_i_michelson': ('Michelson et Pease, 1920 (base de 6,1 m)',
                                        'Michelson and Pease, 1920 (6.1 m baseline)'),
    'anim_interferometry_i_vlti_ut': ('VLTI, deux télescopes de 8,2 m (130 m)', 'VLTI, two 8.2 m telescopes (130 m)'),
    'anim_interferometry_i_vlti_at': ('VLTI, télescopes auxiliaires de 1,8 m (200 m)',
                                      'VLTI, 1.8 m auxiliary telescopes (200 m)'),
    'anim_interferometry_i_chara': ('CHARA, télescopes de 1 m (331 m)', 'CHARA, 1 m telescopes (331 m)'),
    'anim_interferometry_base': ('Base B', 'Baseline B'),
    'anim_interferometry_base_aide': ('Distance entre les deux télescopes (ou les deux fentes), échelle '
                                      'logarithmique. L’interfrange sur le ciel vaut λ / B.',
                                      'Distance between the two telescopes (or the two slits), logarithmic scale. '
                                      'The fringe spacing on the sky is λ / B.'),
    'anim_interferometry_diametre': ('Diamètre d d’un télescope', 'Diameter d of one telescope'),
    'anim_interferometry_diametre_aide': ('Diamètre de chaque ouverture. Seule, elle ne résout que 1,22 λ / d : les '
                                          'franges sont prises dans sa tache d’Airy.',
                                          'Diameter of each aperture. On its own it only resolves 1.22 λ / d: the '
                                          'fringes sit inside its Airy spot.'),
    'anim_interferometry_lambda': ('Longueur d’onde λ', 'Wavelength λ'),
    'anim_interferometry_lambda_aide': ('Longueur d’onde observée : 550 nm au milieu du visible, 2 200 nm dans '
                                        'l’infrarouge (bande K, celle du VLTI et de CHARA).',
                                        'Observed wavelength: 550 nm in the middle of the visible range, 2,200 nm '
                                        'in the infrared (K band, used by the VLTI and CHARA).'),
    'anim_interferometry_objet': ('Source', 'Source'),
    'anim_interferometry_objet_aide': ('Ce que regarde l’interféromètre : une étoile non résolue, le disque d’une '
                                       'étoile ou un couple serré. Les étoiles réelles règlent la taille.',
                                       'What the interferometer looks at: an unresolved star, the disc of a star or '
                                       'a close pair. The real stars set the size.'),
    'anim_interferometry_o_point': ('Étoile non résolue (un point)', 'Unresolved star (a point)'),
    'anim_interferometry_o_disque': ('Disque d’une étoile', 'Disc of a star'),
    'anim_interferometry_o_couple': ('Couple de deux étoiles', 'Pair of two stars'),
    'anim_interferometry_o_betelgeuse': ('Bételgeuse (disque de 47 mas)', 'Betelgeuse (47 mas disc)'),
    'anim_interferometry_o_sirius': ('Sirius A (disque de 6 mas)', 'Sirius A (6 mas disc)'),
    'anim_interferometry_o_capella': ('Capella (couple à 56 mas)', 'Capella (pair 56 mas apart)'),
    'anim_interferometry_taille': ('Taille angulaire θ ou ρ', 'Angular size θ or ρ'),
    'anim_interferometry_taille_aide': ('Diamètre θ du disque, ou séparation ρ du couple (mesurée le long de la '
                                        'base), en millisecondes d’arc (mas), échelle logarithmique.',
                                        'Diameter θ of the disc, or separation ρ of the pair (measured along the '
                                        'baseline), in milliarcseconds (mas), logarithmic scale.'),
    'anim_interferometry_dmag': ('Écart d’éclat Δm du couple', 'Brightness difference Δm of the pair'),
    'anim_interferometry_dmag_aide': ('La seconde étoile du couple est plus faible de Δm magnitudes : la '
                                      'visibilité ne descend plus jusqu’à zéro.',
                                      'The second star of the pair is Δm magnitudes fainter: the visibility no '
                                      'longer drops to zero.'),
    'anim_interferometry_balayer': ('Allonger la base en lecture', 'Lengthen the baseline while playing'),
    'anim_interferometry_balayer_aide': ('Pendant la lecture, la base grandit (échelle logarithmique) et repart du '
                                         'début de l’axe : on voit les franges s’effacer puis revenir.',
                                         'While playing, the baseline grows (logarithmic scale) and starts again '
                                         'from the beginning of the axis: the fringes fade, then come back.'),
    'anim_interferometry_enveloppe': ('Enveloppes', 'Envelopes'),
    'anim_interferometry_enveloppe_aide': ('Pointillés : la tache d’Airy d’un télescope seul (gris) et les bornes '
                                           '(1 ± V) / 2 entre lesquelles oscillent les franges (rouge).',
                                           'Dotted: the Airy spot of a single telescope (grey) and the bounds '
                                           '(1 ± V) / 2 between which the fringes oscillate (red).'),
    'anim_interferometry_t_schema': ('Deux télescopes, une étoile (schéma, angles exagérés)',
                                     'Two telescopes, one star (diagram, angles exaggerated)'),
    'anim_interferometry_t_franges': ('Franges d’interférence', 'Interference fringes'),
    'anim_interferometry_t_visibilite': ('Visibilité des franges selon la base', 'Fringe visibility versus baseline'),
    'anim_interferometry_recombinaison': ('recombinaison', 'beam combiner'),
    'anim_interferometry_vers_etoile': ('lumière de l’étoile ↓', 'starlight ↓'),
    'anim_interferometry_axe_mas': ('angle sur le ciel (mas)', 'angle on the sky (mas)'),
    'anim_interferometry_axe_sec': ('angle sur le ciel (″)', 'angle on the sky (″)'),
    'anim_interferometry_axe_i': ('intensité', 'intensity'),
    'anim_interferometry_axe_b': ('base B (m)', 'baseline B (m)'),
    'anim_interferometry_axe_v': ('visibilité V', 'visibility V'),
    'anim_interferometry_v_frange': ('Interfrange λ / B', 'Fringe spacing λ / B'),
    'anim_interferometry_v_un_telescope': ('Un télescope seul : 1,22 λ / d', 'One telescope alone: 1.22 λ / d'),
    'anim_interferometry_v_gain': ('Gain en finesse B / d', 'Gain in sharpness B / d'),
    'anim_interferometry_v_visibilite': ('Visibilité V', 'Visibility V'),
    'anim_interferometry_v_phase': ('Franges', 'Fringes'),
    'anim_interferometry_centrees': ('centrées (phase 0)', 'centred (phase 0)'),
    'anim_interferometry_retournees': ('retournées : décalées d’une demi-frange (phase 180°)',
                                       'reversed: shifted by half a fringe (phase 180°)'),
    'anim_interferometry_decalees': ('décalées de {x}°', 'shifted by {x}°'),
    'anim_interferometry_v_zero': ('Base du premier zéro 1,22 λ / θ', 'Baseline of the first zero 1.22 λ / θ'),
    'anim_interferometry_v_minimum': ('Base du premier minimum λ / 2ρ', 'Baseline of the first minimum λ / 2ρ'),
    'anim_interferometry_v_verdict': ('La source', 'The source'),
    'anim_interferometry_v_ponctuelle': ('un point : V = 1 quelle que soit la base',
                                         'a point: V = 1 whatever the baseline'),
    'anim_interferometry_v_seul': ('résolue déjà par un télescope seul', 'already resolved by one telescope alone'),
    'anim_interferometry_v_interferometre': ('résolue par l’interféromètre seulement (V < 0,9)',
                                             'resolved by the interferometer only (V < 0.9)'),
    'anim_interferometry_v_non_resolue': ('non résolue : base trop courte (V ≥ 0,9)',
                                          'unresolved: baseline too short (V ≥ 0.9)'),
    'anim_interferometry_v_ecran': ('Interfrange sur un écran à 1 m', 'Fringe spacing on a screen 1 m away'),
    # ================================================================ Occultation d'une étoile par un astéroïde
    'anim_occultation_objet': ('Astéroïde', 'Asteroid'),
    'anim_occultation_objet_aide': ('Un exemple règle la taille, la forme et la distance ; on peut ensuite tout '
                                    'changer à la main.',
                                    'An example sets the size, shape and distance; you can then change everything '
                                    'by hand.'),
    'anim_occultation_o_ceinture': ('Astéroïde de la ceinture principale (100 km)', 'Main-belt asteroid (100 km)'),
    'anim_occultation_o_troyen': ('Petit troyen de Jupiter (21 km, comme Polymele)',
                                  'Small Jupiter Trojan (21 km, like Polymele)'),
    'anim_occultation_o_eris': ('Éris, planète naine (2 326 km)', 'Eris, dwarf planet (2,326 km)'),
    'anim_occultation_o_libre': ('(réglage libre)', '(free setting)'),
    'anim_occultation_diametre': ('Diamètre (grand axe)', 'Diameter (major axis)'),
    'anim_occultation_diametre_aide': ('Plus grande dimension de l’astéroïde, donc de son ombre (échelle '
                                       'logarithmique).',
                                       'Largest dimension of the asteroid, hence of its shadow (logarithmic scale).'),
    'anim_occultation_forme': ('Aplatissement b / a', 'Elongation b / a'),
    'anim_occultation_forme_aide': ('Petit axe rapporté au grand axe : 1 pour un disque, moins pour un astéroïde '
                                    'allongé.',
                                    'Minor axis divided by the major axis: 1 for a disc, less for an elongated '
                                    'asteroid.'),
    'anim_occultation_orientation': ('Orientation ψ', 'Orientation ψ'),
    'anim_occultation_orientation_aide': ('Angle du grand axe avec la direction du mouvement de l’ombre.',
                                          'Angle of the major axis with the direction of motion of the shadow.'),
    'anim_occultation_distance': ('Distance au Soleil r', 'Distance from the Sun r'),
    'anim_occultation_distance_aide': ('À l’opposition, l’ombre court à √(GM☉/1 ua) (1 − 1/√r) : la Terre va plus '
                                       'vite que l’astéroïde. Un objet lointain donne une ombre rapide.',
                                       'At opposition the shadow moves at √(GM☉/1 au) (1 − 1/√r): the Earth is '
                                       'faster than the asteroid. A distant object casts a fast shadow.'),
    'anim_occultation_stations': ('Nombre d’observateurs', 'Number of observers'),
    'anim_occultation_stations_aide': ('Observateurs alignés en travers de la trajectoire prévue, à intervalles '
                                       'réguliers.',
                                       'Observers lined up across the predicted path, at regular intervals.'),
    'anim_occultation_espacement': ('Espacement des observateurs', 'Spacing of the observers'),
    'anim_occultation_espacement_aide': ('Distance entre deux observateurs voisins, perpendiculairement à la '
                                         'trajectoire (échelle logarithmique).',
                                         'Distance between two neighbouring observers, across the path '
                                         '(logarithmic scale).'),
    'anim_occultation_decalage': ('Erreur de prévision', 'Prediction error'),
    'anim_occultation_decalage_aide': ('Écart entre la trajectoire réelle de l’ombre et la trajectoire prévue, en '
                                       'diamètres : les observateurs des bords voient alors un « négatif ».',
                                       'Offset between the actual path of the shadow and the predicted one, in '
                                       'diameters: observers at the edges then record a “negative”.'),
    'anim_occultation_etoile': ('Diamètre apparent de l’étoile', 'Apparent diameter of the star'),
    'anim_occultation_etoile_aide': ('En millisecondes d’arc : 0,1 mas pour une étoile ordinaire, une quarantaine '
                                     'pour une supergéante comme Bételgeuse, que l’astéroïde ne cache alors qu’en '
                                     'partie.',
                                     'In milliarcseconds: 0.1 mas for an ordinary star, about forty for a '
                                     'supergiant such as Betelgeuse, which the asteroid then only partly hides.'),
    'anim_occultation_sigma': ('Erreur de chronométrage σ', 'Timing error σ'),
    'anim_occultation_sigma_aide': ('Écart type de l’erreur sur chaque instant de disparition et de réapparition '
                                    '(réaction d’un observateur à l’œil, horloge mal réglée).',
                                    'Standard deviation of the error on each disappearance and reappearance time '
                                    '(reaction of a visual observer, badly set clock).'),
    'anim_occultation_vraie': ('Vraie forme', 'True shape'),
    'anim_occultation_vraie_aide': ('Contour réel de l’astéroïde, en pointillés, pour juger la reconstitution.',
                                    'Actual outline of the asteroid, dotted, to judge the reconstruction.'),
    'anim_occultation_ajuster': ('Ellipse ajustée', 'Fitted ellipse'),
    'anim_occultation_ajuster_aide': ('Ellipse ajustée par moindres carrés sur les extrémités des cordes (il faut '
                                      'au moins trois cordes).',
                                      'Ellipse fitted by least squares to the ends of the chords (at least three '
                                      'chords are needed).'),
    'anim_occultation_t_plan': ('L’ombre balaie les observateurs', 'The shadow sweeps over the observers'),
    'anim_occultation_t_courbes': ('Éclat de l’étoile vu par chaque observateur', 'Star brightness seen by each observer'),
    'anim_occultation_t_forme': ('Les cordes mesurées et la forme reconstituée',
                                 'The measured chords and the reconstructed shape'),
    'anim_occultation_observateurs': ('points : les observateurs (gris : étoile cachée)',
                                      'dots: the observers (grey: star hidden)'),
    'anim_occultation_axe_t': ('temps (s)', 'time (s)'),
    'anim_occultation_axe_flux': ('éclat', 'brightness'),
    'anim_occultation_legende_forme': ('jaune : cordes ; rouge : ± σ ; bleu : ellipse ajustée',
                                       'yellow: chords; red: ± σ; blue: fitted ellipse'),
    'anim_occultation_v_vitesse': ('Vitesse de l’ombre (à l’opposition)', 'Shadow speed (at opposition)'),
    'anim_occultation_v_distance': ('Distance de la Terre Δ', 'Distance from the Earth Δ'),
    'anim_occultation_v_cordes': ('Observateurs qui voient l’étoile disparaître',
                                  'Observers who see the star disappear'),
    'anim_occultation_sur': ('{n} sur {N}', '{n} of {N}'),
    'anim_occultation_v_plus_longue': ('Plus longue disparition', 'Longest disappearance'),
    'anim_occultation_duree_corde': ('{d} s (corde de {c})', '{d} s (chord of {c})'),
    'anim_occultation_v_ajustee': ('Ellipse ajustée 2a × 2b', 'Fitted ellipse 2a × 2b'),
    'anim_occultation_pas_assez': ('il faut au moins trois cordes', 'at least three chords are needed'),
    'anim_occultation_v_equivalent': ('Diamètre équivalent √(2a · 2b)', 'Equivalent diameter √(2a · 2b)'),
    'anim_occultation_vrai_ajuste': ('vrai {v}, ajusté {a}', 'true {v}, fitted {a}'),
    'anim_occultation_v_erreur': ('Erreur de position σ v', 'Position error σ v'),
    'anim_occultation_v_fresnel': ('Échelle de Fresnel √(λ Δ / 2)', 'Fresnel scale √(λ Δ / 2)'),
    'anim_occultation_v_etoile': ('Étoile projetée à la distance de l’astéroïde', 'Star projected at the asteroid’s distance'),
    'anim_occultation_franche': ('disparition franche', 'sharp disappearance'),
    'anim_occultation_progressive': ('disparition progressive, voire partielle', 'gradual, even partial, disappearance'),
    # ================================================================ Le mécanisme de Kozai-Lidov
    'anim_kozai_systeme': ('Système', 'System'),
    'anim_kozai_systeme_aide': ('Le système fixe le temps caractéristique tₖ = (M/M′)(a′/a)³ P/2π ; '
                                'l’évolution, comptée en tₖ, est la même pour tous.',
                                'The system sets the characteristic time tₖ = (M/M′)(a′/a)³ P/2π; the '
                                'evolution, counted in tₖ, is the same for all.'),
    'anim_kozai_s_asteroide': ('Astéroïde à 2,7 ua, perturbé par Jupiter', 'Asteroid at 2.7 au, perturbed by Jupiter'),
    'anim_kozai_s_satellite': ('Satellite sur orbite de 12 h, perturbé par la Lune',
                               'Satellite on a 12 h orbit, perturbed by the Moon'),
    'anim_kozai_s_exoplanete': ('Planète à 5 ua, étoile compagne à 500 ua', 'Planet at 5 au, companion star at 500 au'),
    'anim_kozai_i0': ('Inclinaison de départ i₀', 'Initial inclination i₀'),
    'anim_kozai_i0_aide': ('Inclinaison de l’orbite sur le plan du perturbateur au départ. Sous 39,2°, presque '
                           'rien ne se passe ; au-dessus, l’excentricité grimpe.',
                           'Inclination of the orbit on the perturber’s plane at the start. Below 39.2° almost '
                           'nothing happens; above it, the eccentricity climbs.'),
    'anim_kozai_e0': ('Excentricité de départ e₀', 'Initial eccentricity e₀'),
    'anim_kozai_e0_aide': ('Excentricité au départ (échelle logarithmique) : une orbite presque circulaire met plus '
                           'longtemps à démarrer.',
                           'Eccentricity at the start (logarithmic scale): a nearly circular orbit takes longer '
                           'to get going.'),
    'anim_kozai_w0': ('Argument du périastre de départ ω₀', 'Initial argument of periapsis ω₀'),
    'anim_kozai_w0_aide': ('Angle entre la ligne des nœuds et le périastre au départ : il décide si ω tourne '
                           '(circulation) ou oscille autour de 90° ou 270° (libration).',
                           'Angle between the line of nodes and the periapsis at the start: it decides whether ω '
                           'goes round (circulation) or swings around 90° or 270° (libration).'),
    'anim_kozai_trace': ('Trajectoire dans le portrait de phase', 'Path in the phase portrait'),
    'anim_kozai_trace_aide': ('Laisse la trace des états (ω, e) parcourus.', 'Leaves a trail of the (ω, e) states '
                              'visited.'),
    'anim_kozai_recommencer': ('Recommencer', 'Restart'),
    'anim_kozai_recommencer_aide': ('Repart des valeurs de départ.', 'Starts again from the initial values.'),
    'anim_kozai_t_orbite': ('L’orbite et le plan du perturbateur (à faire tourner)',
                            'The orbit and the perturber’s plane (drag to rotate)'),
    'anim_kozai_t_temps': ('L’excentricité et l’inclinaison s’échangent', 'Eccentricity and inclination trade off'),
    'anim_kozai_t_phase': ('Portrait de phase (ω, e)', 'Phase portrait (ω, e)'),
    'anim_kozai_perturbateur': ('perturbateur (loin)', 'perturber (far away)'),
    'anim_kozai_periastre': ('périastre', 'periapsis'),
    'anim_kozai_normale': ('normale', 'normal'),
    'anim_kozai_axe_t': ('temps (tₖ)', 'time (tₖ)'),
    'anim_kozai_axe_ei': ('e et i / 90°', 'e and i / 90°'),
    'anim_kozai_legende_temps': ('jaune : e ; bleu : i / 90° ; tirets : eₘₐₓ prévue, i critique',
                                 'yellow: e; blue: i / 90°; dashes: predicted eₘₐₓ, critical i'),
    'anim_kozai_axe_w': ('argument du périastre ω (°)', 'argument of periapsis ω (°)'),
    'anim_kozai_axe_e': ('excentricité e', 'eccentricity e'),
    'anim_kozai_limite': ('e ≤ √(1 − C²) : i ne peut pas passer sous 0', 'e ≤ √(1 − C²): i cannot go below 0'),
    'anim_kozai_v_c': ('C = √(1 − e²) cos i (conservée)', 'C = √(1 − e²) cos i (conserved)'),
    'anim_kozai_c_conservee': ('{c} (au départ {c0})', '{c} (at the start {c0})'),
    'anim_kozai_v_e': ('Excentricité e', 'Eccentricity e'),
    'anim_kozai_v_i': ('Inclinaison i', 'Inclination i'),
    'anim_kozai_v_w': ('Argument du périastre ω', 'Argument of periapsis ω'),
    'anim_kozai_v_critique': ('Inclinaison critique arccos √(3/5)', 'Critical inclination arccos √(3/5)'),
    'anim_kozai_v_emax_prevue': ('eₘₐₓ = √(1 − 5/3 cos² i₀) (départ circulaire)',
                                 'eₘₐₓ = √(1 − 5/3 cos² i₀) (circular start)'),
    'anim_kozai_sous_critique': ('0 : sous l’inclinaison critique', '0: below the critical inclination'),
    'anim_kozai_v_emax': ('e maximale atteinte', 'Largest e reached'),
    'anim_kozai_emax_i': ('{e}, avec i = {i}', '{e}, with i = {i}'),
    'anim_kozai_v_tk': ('Temps caractéristique tₖ', 'Characteristic time tₖ'),
    'anim_kozai_v_periode': ('Période des oscillations', 'Period of the oscillations'),
    'anim_kozai_periode': ('{p} tₖ = {a}', '{p} tₖ = {a}'),
    'anim_kozai_en_mesure': ('en mesure (deux maxima de e)', 'being measured (two maxima of e)'),
    'anim_kozai_v_temps': ('Temps écoulé', 'Elapsed time'),
    'anim_kozai_temps': ('{t} tₖ = {a}', '{t} tₖ = {a}'),
    'anim_kozai_ans': ('{x} ans', '{x} years'),
    'anim_kozai_millions_ans': ('{x} millions d’années', '{x} million years'),
    # ================================================================ Les points de Lagrange
    'anim_lagrange_systeme': ('Système', 'System'),
    'anim_lagrange_systeme_aide': ('Les deux astres qui tournent l’un autour de l’autre ; μ est la part de masse du '
                                   'plus petit.',
                                   'The two bodies orbiting each other; μ is the mass fraction of the smaller one.'),
    'anim_lagrange_s_soleil_terre': ('Soleil et Terre (avec la Lune)', 'Sun and Earth (with the Moon)'),
    'anim_lagrange_s_terre_lune': ('Terre et Lune', 'Earth and Moon'),
    'anim_lagrange_s_soleil_jupiter': ('Soleil et Jupiter', 'Sun and Jupiter'),
    'anim_lagrange_s_pluton_charon': ('Pluton et Charon (μ > 0,0385)', 'Pluto and Charon (μ > 0.0385)'),
    'anim_lagrange_cas': ('Petit corps lâché', 'Small body released'),
    'anim_lagrange_cas_aide': ('Où l’on lâche le petit corps, au repos (ou sur un cercle) dans le repère tournant ; '
                               'ou sur une orbite de halo autour de L1 ou L2, en trois dimensions.',
                               'Where the small body is released, at rest (or on a circle) in the rotating frame; or on '
                               'a halo orbit around L1 or L2, in three dimensions.'),
    'anim_lagrange_c_halo_l1': ('Orbite de halo autour de L1', 'Halo orbit around L1'),
    'anim_lagrange_c_halo_l2': ('Orbite de halo autour de L2', 'Halo orbit around L2'),
    'anim_lagrange_t_halo': ('L’orbite de halo vue du grand astre', 'The halo orbit seen from the large body'),
    'anim_lagrange_legende_halo': ('pointillés : Richardson (3ᵉ ordre) ; jaune : trajectoire intégrée',
                                   'dotted: Richardson (3rd order); yellow: integrated path'),
    'anim_lagrange_v_halo': ('Orbite de halo : amplitudes Ax, Ay, Az ; période', 'Halo orbit: amplitudes Ax, Ay, Az; '
                             'period'),
    'anim_lagrange_halo': ('{ax} km, {ay} km, {az} km ; {j} jours', '{ax} km, {ay} km, {az} km; {j} days'),
    'anim_lagrange_v_ecart': ('Écart du corps à l’orbite de Richardson', 'Distance of the body from Richardson’s orbit'),
    'anim_lagrange_c_tetard': ('Près de L4 : un « têtard »', 'Near L4: a “tadpole”'),
    'anim_lagrange_c_fer_a_cheval': ('En face du petit astre : un « fer à cheval »',
                                     'Opposite the small body: a “horseshoe”'),
    'anim_lagrange_c_l1': ('Juste à côté de L1', 'Right next to L1'),
    'anim_lagrange_c_l2': ('Juste à côté de L2', 'Right next to L2'),
    'anim_lagrange_c_l3': ('Juste à côté de L3', 'Right next to L3'),
    'anim_lagrange_delta': ('Écart au départ δ', 'Initial offset δ'),
    'anim_lagrange_delta_aide': ('Écart au point de départ, en unités de la distance a des deux astres (L1, L2, '
                                 'L3 : δ/100). Plus il est grand, plus la boucle est large. Orbite de halo : δ est '
                                 'l’amplitude hors du plan Az (en a, bornée à 0,4 fois la distance du point au petit '
                                 'astre ; son signe choisit la famille nord ou sud).',
                                 'Offset from the starting point, in units of the distance a between the two bodies '
                                 '(L1, L2, L3: δ/100). The larger it is, the wider the loop. Halo orbit: δ is the '
                                 'out-of-plane amplitude Az (in a, capped at 0.4 times the distance from the point to '
                                 'the small body; its sign picks the northern or southern family).'),
    'anim_lagrange_interdit': ('Zones interdites', 'Forbidden regions'),
    'anim_lagrange_interdit_aide': ('En gris, là où 2Ω < C : le petit corps n’a pas l’énergie d’y aller '
                                    '(courbes de vitesse nulle).',
                                    'In grey, where 2Ω < C: the small body lacks the energy to go there '
                                    '(zero-velocity curves).'),
    'anim_lagrange_hill': ('Sphère de Hill', 'Hill sphere'),
    'anim_lagrange_hill_aide': ('Cercle de rayon a ∛(μ/3) autour du petit astre : là, c’est lui qui retient '
                                'ses satellites.',
                                'Circle of radius a ∛(μ/3) around the small body: within it, the small body '
                                'holds its satellites.'),
    'anim_lagrange_relancer': ('Relâcher', 'Release again'),
    'anim_lagrange_relancer_aide': ('Repart du point de départ.', 'Starts again from the starting point.'),
    'anim_lagrange_t_carte': ('Le repère qui tourne avec les deux astres', 'The frame rotating with the two bodies'),
    'anim_lagrange_t_zoom': ('Autour du petit astre : L1, L2 et la sphère de Hill',
                             'Around the small body: L1, L2 and the Hill sphere'),
    'anim_lagrange_t_potentiel': ('Potentiel effectif le long de l’axe', 'Effective potential along the axis'),
    'anim_lagrange_axe_x': ('x (a)', 'x (a)'),
    'anim_lagrange_axe_phi': ('−Ω', '−Ω'),
    'anim_lagrange_legende_pot': ('rouge : −C/2 ; le corps ne va que là où la courbe passe sous ce trait',
                                  'red: −C/2; the body only goes where the curve lies below this line'),
    'anim_lagrange_millions_km': ('millions de km', 'million km'),
    'anim_lagrange_v_mu': ('Rapport de masse μ', 'Mass ratio μ'),
    'anim_lagrange_v_l1': ('L1 : distance au petit astre', 'L1: distance from the small body'),
    'anim_lagrange_v_l2': ('L2 : distance au petit astre', 'L2: distance from the small body'),
    'anim_lagrange_v_hill': ('Rayon de Hill a ∛(μ/3)', 'Hill radius a ∛(μ/3)'),
    'anim_lagrange_v_l4': ('L4 et L5', 'L4 and L5'),
    'anim_lagrange_stables': ('stables (μ < 0,0385)', 'stable (μ < 0.0385)'),
    'anim_lagrange_instables': ('instables (μ > 0,0385)', 'unstable (μ > 0.0385)'),
    'anim_lagrange_v_c': ('Constante de Jacobi C du petit corps', 'Jacobi constant C of the small body'),
    'anim_lagrange_v_cl': ('C aux points de Lagrange', 'C at the Lagrange points'),
    'anim_lagrange_v_regions': ('Son énergie lui permet d’aller', 'Its energy lets it go'),
    'anim_lagrange_r_ferme': ('près d’un seul astre : L1 lui est fermé', 'near one body only: L1 is closed to it'),
    'anim_lagrange_r_l1': ('d’un astre à l’autre par L1, sans s’échapper', 'from one body to the other through L1, '
                           'without escaping'),
    'anim_lagrange_r_l2': ('aussi au-delà de L2 ; la zone interdite fait un fer à cheval par L4, L3 et L5',
                           'also beyond L2; the forbidden region forms a horseshoe through L4, L3 and L5'),
    'anim_lagrange_r_l3': ('aussi par L3 ; restent deux îlots interdits, autour de L4 et de L5 (têtards)',
                           'also through L3; two forbidden islands remain, around L4 and L5 (tadpoles)'),
    'anim_lagrange_r_partout': ('partout (C sous celle de L4)', 'anywhere (C below that of L4)'),
    'anim_lagrange_v_temps': ('Temps écoulé', 'Elapsed time'),
    'anim_lagrange_orbites': ('{n} tours des deux astres', '{n} revolutions of the two bodies'),
    'anim_lagrange_v_etat': ('État', 'State'),
    'anim_lagrange_contact': ('collision avec un des astres', 'collision with one of the bodies'),
}
