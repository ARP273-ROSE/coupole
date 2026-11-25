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
}
