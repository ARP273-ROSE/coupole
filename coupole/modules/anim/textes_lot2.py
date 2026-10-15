"""Textes FR/EN des animations du lot 2 (Lune, Renaissance, astronomie antique, propriétés stellaires) : (fr, en).
Fusionnés dans ``textes.TEXTES``."""

ANIM_LOT2 = {
    # ------------------------------------------------------------ communs
    'anim_u_jours': ('jours', 'days'),
    'anim_u_heures': ('h', 'h'),
    'anim_oui': ('oui', 'yes'),
    'anim_non': ('non', 'no'),
    'anim_est': ('E', 'E'),
    'anim_ouest': ('O', 'W'),
    'anim_c_elongation': ('Élongation', 'Elongation'),
    'anim_c_angle_phase': ('Angle de phase', 'Phase angle'),
    'anim_c_eclairee': ('Fraction éclairée', 'Illuminated fraction'),
    'anim_c_distance': ('Distance', 'Distance'),
    # ------------------------------------------------------------ lunar_phaser
    'anim_lunar_phaser_periode': ('Lunaison à l’écran', 'Lunation on screen'),
    'anim_lunar_phaser_periode_aide': ('Durée, en secondes, d’une lunaison complète pendant l’animation (29,53 s : une '
                                       'seconde pour un jour, comme l’original).',
                                       'Duration, in seconds, of a whole lunation during the animation (29.53 s: one '
                                       'second per day, as in the original).'),
    'anim_lunar_phaser_bande': ('Les huit phases', 'The eight phases'),
    'anim_lunar_phaser_bande_aide': ('Montrer les huit phases nommées sous la Lune, la phase courante entourée.',
                                     'Show the eight named phases below the Moon, the current one circled.'),
    'anim_lunar_phaser_age': ('Âge de la Lune', 'Age of the Moon'),
    'anim_lunar_phaser_ecoules': ('Jours écoulés', 'Days elapsed'),
}
for _cle, _fr, _en in (('nl', 'Nouvelle lune', 'New moon'), ('pc', 'Premier croissant', 'Waxing crescent'),
                       ('pq', 'Premier quartier', 'First quarter'), ('gc', 'Gibbeuse croissante', 'Waxing gibbous'),
                       ('pl', 'Pleine lune', 'Full moon'), ('gd', 'Gibbeuse décroissante', 'Waning gibbous'),
                       ('dq', 'Dernier quartier', 'Third quarter'), ('dc', 'Dernier croissant', 'Waning crescent')):
    ANIM_LOT2['anim_lunar_phaser_b_' + _cle] = (_fr, _en)
    ANIM_LOT2['anim_lunar_phaser_b_' + _cle + '_aide'] = ('Montrer la Lune à la phase « %s » et remettre le compteur '
                                                          'à zéro.' % _fr.lower(),
                                                          'Show the Moon at the « %s » phase and reset the counter.'
                                                          % _en.lower())

ANIM_LOT2.update({
    # ------------------------------------------------------------ basketball
    'anim_basketball_angle': ('Position de l’œil', 'Eye position'),
    'anim_basketball_angle_aide': ('Angle de l’œil autour du ballon, vu de dessus : 0° entre la lampe et le ballon '
                                   '(ballon vu « plein »), 180° de l’autre côté (vu « nouveau »). On peut aussi faire '
                                   'glisser l’œil.',
                                   'Angle of the eye around the ball, seen from above: 0° between the lamp and the ball '
                                   '(ball seen « full »), 180° on the other side (seen « new »). The eye can also be '
                                   'dragged.'),
    'anim_basketball_position': ('Phase équivalente', 'Equivalent phase'),
    'anim_basketball_position_aide': ('Placer l’œil là où la Lune montrerait cette phase.',
                                      'Put the eye where the Moon would show this phase.'),
    'anim_basketball_lune': ('Comparer à la Lune', 'Compare with the Moon'),
    'anim_basketball_lune_aide': ('Montrer la phase de la Lune qui correspond à ce que voit l’œil.',
                                  'Show the phase of the Moon that matches what the eye sees.'),
    'anim_basketball_vue_dessus': ('La pièce vue de dessus', 'The room seen from above'),
    'anim_basketball_vue_oeil': ('Ce que voit l’œil', 'What the eye sees'),
    'anim_basketball_vue_lune': ('La Lune à la même phase', 'The Moon at the same phase'),
    'anim_basketball_oeil': ('œil', 'eye'),
    'anim_basketball_cote': ('Côté éclairé vu par l’œil', 'Lit side seen by the eye'),
    'anim_basketball_droite': ('à droite', 'on the right'),
    'anim_basketball_gauche': ('à gauche', 'on the left'),
    'anim_basketball_phase_lune': ('Phase lunaire équivalente', 'Equivalent lunar phase'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ moonphases
    'anim_moonphases_psi': ('Direction de l’œil', 'Direction of the eye'),
    'anim_moonphases_psi_aide': ('Direction, vue de la Lune, de l’observateur libre (0° : du côté du Soleil, 180° : à '
                                 'l’opposé). On peut aussi faire glisser l’œil ou la Lune.',
                                 'Direction, seen from the Moon, of the free observer (0°: on the side of the Sun, '
                                 '180°: opposite). The eye or the Moon can also be dragged.'),
    'anim_moonphases_vue_dessus': ('L’orbite de la Lune vue de dessus', 'The orbit of the Moon seen from above'),
    'anim_moonphases_vu_terre': ('Vue de la Terre', 'Seen from the Earth'),
    'anim_moonphases_vu_soleil': ('Vue du Soleil', 'Seen from the Sun'),
    'anim_moonphases_vu_libre': ('Vue de l’œil', 'Seen from the eye'),
    'anim_moonphases_vers_soleil': ('vers le Soleil', 'to the Sun'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ phaseDemonstrator
    'anim_phasedemonstrator_orbites': ('Orbites', 'Orbits'),
    'anim_phasedemonstrator_orbites_aide': ('Tracer l’orbite circulaire de chaque corps (autour du Soleil, ou autour de '
                                            'l’autre corps pour une lune).',
                                            'Draw the circular orbit of each body (around the Sun, or around the other '
                                            'body for a moon).'),
    'anim_phasedemonstrator_phase1': ('Phase du corps 1', 'Phase of body 1'),
    'anim_phasedemonstrator_phase1_aide': ('Montrer ou cacher la phase du corps 1 (pour la deviner d’abord).',
                                           'Show or hide the phase of body 1 (to guess it first).'),
    'anim_phasedemonstrator_phase2': ('Phase du corps 2', 'Phase of body 2'),
    'anim_phasedemonstrator_phase2_aide': ('Montrer ou cacher la phase du corps 2 (pour la deviner d’abord).',
                                           'Show or hide the phase of body 2 (to guess it first).'),
    'anim_phasedemonstrator_planete': ('planète {n}', 'planet {n}'),
    'anim_phasedemonstrator_lune': ('lune {n}', 'moon {n}'),
    'anim_phasedemonstrator_vu': ('{a} vue de {b}', '{a} seen from {b}'),
    'anim_phasedemonstrator_plan': ('Le plan des orbites, vu de dessus', 'The plane of the orbits, seen from above'),
    'anim_phasedemonstrator_souris': ('Faire glisser les corps ; tout près de l’autre, un corps devient sa lune.',
                                       'Drag the bodies; very close to the other one, a body becomes its moon.'),
    'anim_phasedemonstrator_dist_soleil': ('Distances au Soleil (1 / 2)', 'Distances to the Sun (1 / 2)'),
    'anim_phasedemonstrator_dist_mutuelle': ('Distance entre les deux corps', 'Distance between the two bodies'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ positionsdemonstrator
    'anim_positionsdemonstrator_soleil': ('Position du Soleil', 'Sun position'),
    'anim_positionsdemonstrator_soleil_aide': ('Position du Soleil sur l’équateur céleste, de 1 à 8 (de 3 h en 3 h) : '
                                               'elle fixe l’heure (position 1 : 6 h, lever ; 3 : midi ; 5 : 18 h, '
                                               'coucher ; 7 : minuit).',
                                               'Position of the Sun on the celestial equator, from 1 to 8 (every 3 h): '
                                               'it sets the time (position 1: 6 a.m., sunrise; 3: noon; 5: 6 p.m., '
                                               'sunset; 7: midnight).'),
    'anim_positionsdemonstrator_lune': ('Position de la Lune', 'Moon position'),
    'anim_positionsdemonstrator_lune_aide': ('Position de la Lune sur l’équateur céleste, de 1 à 8 ; l’écart avec le '
                                             'Soleil donne la phase (deux positions vers l’est : premier quartier).',
                                             'Position of the Moon on the celestial equator, from 1 to 8; the gap with '
                                             'the Sun gives the phase (two positions eastward: first quarter).'),
    'anim_positionsdemonstrator_reperes': ('Repères 1 à 8', 'Marks 1 to 8'),
    'anim_positionsdemonstrator_reperes_aide': ('Numéroter les huit positions sur l’équateur céleste.',
                                                'Number the eight positions on the celestial equator.'),
    'anim_positionsdemonstrator_bande': ('Bande de ±30°', '±30° band'),
    'anim_positionsdemonstrator_bande_aide': ('Bande de ±30° autour de l’équateur céleste, où se trouvent toujours le '
                                              'Soleil (±23,4°) et la Lune (±28,6°).',
                                              'Band of ±30° around the celestial equator, where the Sun (±23.4°) and '
                                              'the Moon (±28.6°) always are.'),
    'anim_positionsdemonstrator_heure': ('Montrer l’heure', 'Show the time'),
    'anim_positionsdemonstrator_heure_aide': ('Afficher l’heure (la cacher pour la deviner d’après le ciel).',
                                              'Show the time (hide it to guess it from the sky).'),
    'anim_positionsdemonstrator_phase': ('Phase de la Lune', 'Phase of the Moon'),
    'anim_positionsdemonstrator_phase_aide': ('Afficher la phase (la cacher pour la deviner d’après les positions).',
                                              'Show the phase (hide it to guess it from the positions).'),
    'anim_positionsdemonstrator_ciel': ('Le ciel de l’observateur', 'The sky of the observer'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ lunarphasequizzer
    'anim_lunarphasequizzer_mode': ('Question', 'Question'),
    'anim_lunarphasequizzer_mode_aide': ('Ce qui est caché : l’aspect de la Lune, sa position sur l’orbite ou la '
                                         'direction du Soleil.',
                                         'What is hidden: the appearance of the Moon, its position on the orbit or the '
                                         'direction of the Sun.'),
    'anim_lunarphasequizzer_m_apparence': ('Quelle est la phase de la Lune ?', 'What is the moon’s phase?'),
    'anim_lunarphasequizzer_m_lune': ('Où est la Lune ?', 'Where is the moon?'),
    'anim_lunarphasequizzer_m_soleil': ('Où est le Soleil ?', 'Where is the sun?'),
    'anim_lunarphasequizzer_reponse': ('Votre phase', 'Your phase'),
    'anim_lunarphasequizzer_reponse_aide': ('Réponse à « Quelle est la phase ? » : angle de phase (0° nouvelle lune, '
                                            '90° premier quartier, 180° pleine lune, 270° dernier quartier).',
                                            'Answer to « What is the phase? »: phase angle (0° new moon, 90° first '
                                            'quarter, 180° full moon, 270° third quarter).'),
    'anim_lunarphasequizzer_nouvelle': ('Nouvelle question', 'New question'),
    'anim_lunarphasequizzer_nouvelle_aide': ('Tirer au hasard une nouvelle position de la Lune et une nouvelle direction '
                                             'du Soleil.',
                                             'Draw at random a new position of the Moon and a new direction of the Sun.'),
    'anim_lunarphasequizzer_montrer': ('Montrer la réponse', 'Show answer'),
    'anim_lunarphasequizzer_montrer_aide': ('Montrer ou cacher la réponse (tout est alors affiché).',
                                            'Show or hide the answer (everything is then displayed).'),
    'anim_lunarphasequizzer_cacher': ('Cacher la réponse', 'Hide answer'),
    'anim_lunarphasequizzer_schema': ('L’orbite de la Lune vue du nord', 'The orbit of the Moon seen from the north'),
    'anim_lunarphasequizzer_aspect': ('La Lune vue de la Terre', 'The Moon seen from the Earth'),
    'anim_lunarphasequizzer_votre_reponse': ('votre réponse', 'your answer'),
    'anim_lunarphasequizzer_question': ('Question', 'Question'),
    'anim_lunarphasequizzer_votre': ('Votre réponse', 'Your answer'),
    'anim_lunarphasequizzer_vraie': ('Bonne réponse', 'Right answer'),
    'anim_lunarphasequizzer_verdict': ('Verdict', 'Verdict'),
    'anim_lunarphasequizzer_juste': ('Juste : même phase', 'Right: same phase'),
    'anim_lunarphasequizzer_faux': ('Pas tout à fait : autre phase', 'Not quite: another phase'),
    'anim_lunarphasequizzer_glisser_lune': ('Faire glisser la Lune (en bleu) à sa place.',
                                            'Drag the Moon (in blue) to its place.'),
    'anim_lunarphasequizzer_glisser_soleil': ('Faire glisser la lumière (en bleu) pour orienter le Soleil.',
                                              'Drag the light (in blue) to orient the Sun.'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ synodiclag
    'anim_synodiclag_rotation': ('Rotation de la Terre', 'Rotation of the Earth'),
    'anim_synodiclag_rotation_aide': ('Durée d’un tour de la Terre par rapport aux étoiles (jour sidéral) : la vraie '
                                      '(23 h 56 min 4 s), ou ralentie (240 h, 1 200 h) comme dans l’original pour '
                                      'rendre le retard visible.',
                                      'Duration of one turn of the Earth with respect to the stars (sidereal day): the '
                                      'real one (23 h 56 min 4 s), or slowed down (240 h, 1,200 h) as in the original '
                                      'to make the lag visible.'),
    'anim_synodiclag_r_reel': ('réelle : 23 h 56 min 4 s', 'real: 23 h 56 min 4 s'),
    'anim_synodiclag_r_h240': ('240 h', '240 h'),
    'anim_synodiclag_r_h1200': ('1 200 h', '1,200 h'),
    'anim_synodiclag_sideral': ('Un jour sidéral', 'One sidereal day'),
    'anim_synodiclag_sideral_aide': ('Faire tourner la Terre d’un tour exactement par rapport aux étoiles, puis '
                                     's’arrêter.',
                                     'Turn the Earth exactly once with respect to the stars, then stop.'),
    'anim_synodiclag_solaire': ('Un jour solaire', 'One solar day'),
    'anim_synodiclag_solaire_aide': ('Faire tourner la Terre jusqu’à ce que le Soleil revienne au méridien, puis '
                                     's’arrêter.',
                                     'Turn the Earth until the Sun comes back to the meridian, then stop.'),
    'anim_synodiclag_midi': ('Réaligner sur midi', 'Realign to noon'),
    'anim_synodiclag_midi_aide': ('Tourner la flèche de l’observateur vers le Soleil (midi) sans changer la date.',
                                  'Turn the observer’s arrow toward the Sun (noon) without changing the date.'),
    'anim_synodiclag_ombre': ('Position de départ', 'Starting position'),
    'anim_synodiclag_ombre_aide': ('Laisser une Terre pâle à la position du début du jour.',
                                   'Leave a pale Earth at the position of the start of the day.'),
    'anim_synodiclag_jour_sideral': ('Jour sidéral (rotation)', 'Sidereal day (rotation)'),
    'anim_synodiclag_jour_solaire': ('Jour solaire', 'Solar day'),
    'anim_synodiclag_retard': ('Retard du jour solaire', 'Lag of the solar day'),
    'anim_synodiclag_angle_soleil': ('Angle du méridien au Soleil', 'Angle from the meridian to the Sun'),
    'anim_synodiclag_tour_etoiles': ('Rotation depuis le départ', 'Rotation since the start'),
    'anim_synodiclag_ecoule': ('Temps écoulé', 'Elapsed time'),
    'anim_synodiclag_vers_etoiles': ('vers une étoile', 'to a star'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ tidesim
    'anim_tidesim_soleil': ('Avec le Soleil', 'With the Sun'),
    'anim_tidesim_soleil_aide': ('Ajouter la marée due au Soleil (0,46 fois celle de la Lune) : vives eaux à la '
                                 'nouvelle et à la pleine lune, mortes eaux aux quartiers.',
                                 'Add the tide due to the Sun (0.46 times that of the Moon): spring tides at new and '
                                 'full moon, neap tides at the quarters.'),
    'anim_tidesim_fleches': ('Force de marée', 'Tidal force'),
    'anim_tidesim_fleches_aide': ('Flèches de la force de marée : différence entre l’attraction subie en un point et '
                                  'celle subie au centre de la Terre ; elle étire la Terre vers l’astre et à l’opposé.',
                                  'Arrows of the tidal force: difference between the pull felt at a point and at the '
                                  'centre of the Earth; it stretches the Earth toward the body and away from it.'),
    'anim_tidesim_decalage': ('Décalage des bourrelets', 'Bulge offset'),
    'anim_tidesim_decalage_aide': ('Avance des bourrelets dans le sens de la rotation de la Terre, qui les entraîne '
                                   '(0° : marée d’équilibre ; les valeurs fortes sont exagérées pour être visibles).',
                                   'Lead of the bulges in the direction of the Earth’s rotation, which drags them '
                                   '(0°: equilibrium tide; large values are exaggerated to be visible).'),
    'anim_tidesim_exageration': ('Exagération', 'Exaggeration'),
    'anim_tidesim_exageration_aide': ('Agrandissement du dessin des bourrelets (la marée d’équilibre ne fait que '
                                      'quelques dizaines de centimètres).',
                                      'Enlargement of the drawn bulges (the equilibrium tide is only a few tens of '
                                      'centimetres).'),
    'anim_tidesim_niveau': ('Niveau chez l’observateur', 'Level at the observer'),
    'anim_tidesim_marnage_lune': ('Marnage dû à la Lune seule', 'Tidal range from the Moon alone'),
    'anim_tidesim_rapport': ('Rapport Soleil / Lune', 'Sun / Moon ratio'),
    'anim_tidesim_type': ('Marée', 'Tide'),
    'anim_tidesim_t_vives': ('de vives eaux', 'spring tide'),
    'anim_tidesim_t_mortes': ('de mortes eaux', 'neap tide'),
    'anim_tidesim_t_moyennes': ('moyenne', 'intermediate'),
    'anim_tidesim_courbe': ('Niveau de la mer chez l’observateur (point rouge), ±1,5 jour',
                            'Sea level at the observer (red dot), ±1.5 day'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ mooninc
    'anim_mooninc_plan': ('Plan de l’écliptique', 'Ecliptic plane'),
    'anim_mooninc_plan_aide': ('Montrer le plan de l’orbite de la Terre (écliptique), où se trouvent le Soleil et '
                               'l’ombre de la Terre.',
                               'Show the plane of the Earth’s orbit (ecliptic), where the Sun and the Earth’s shadow '
                               'lie.'),
    'anim_mooninc_orbite': ('Orbite de la Lune', 'Orbit of the Moon'),
    'anim_mooninc_orbite_aide': ('Tracer l’orbite de la Lune, inclinée de 5,1° sur l’écliptique.',
                                 'Draw the orbit of the Moon, tilted by 5.1° to the ecliptic.'),
    'anim_mooninc_tailles': ('Grossir la Terre et la Lune', 'Enlarge the Earth and the Moon'),
    'anim_mooninc_tailles_aide': ('Dessiner la Terre et la Lune trois fois plus grosses (la vue de gauche n’est pas à '
                                  'l’échelle ; celle de droite l’est).',
                                  'Draw the Earth and the Moon three times bigger (the left view is not to scale; '
                                  'the right one is).'),
    'anim_mooninc_vue': ('La Terre, l’orbite de la Lune et la lumière du Soleil',
                         'The Earth, the orbit of the Moon and the sunlight'),
    'anim_mooninc_depuis_soleil': ('Vu du Soleil (à l’échelle)', 'Seen from the Sun (to scale)'),
    'anim_mooninc_noeud_asc': ('nœud ascendant', 'ascending node'),
    'anim_mooninc_noeud_desc': ('nœud descendant', 'descending node'),
    'anim_mooninc_jours': ('Jours écoulés', 'Days elapsed'),
    'anim_mooninc_latitude': ('Latitude écliptique de la Lune', 'Ecliptic latitude of the Moon'),
    'anim_mooninc_soleil_noeud': ('Écart du Soleil à la ligne des nœuds', 'Distance of the Sun from the line of nodes'),
    'anim_mooninc_eclipse': ('Éclipse', 'Eclipse'),
    'anim_mooninc_e_aucune': ('aucune', 'none'),
    'anim_mooninc_e_soleil': ('éclipse de Soleil', 'solar eclipse'),
    'anim_mooninc_e_lune_ombre': ('éclipse de Lune (ombre)', 'lunar eclipse (umbral)'),
    'anim_mooninc_e_lune_penombre': ('éclipse de Lune (pénombre)', 'lunar eclipse (penumbral)'),
    'anim_mooninc_frise': ('±60 jours : saisons d’éclipses (bandes), nouvelles et pleines lunes, aujourd’hui (trait '
                           'rouge)',
                           '±60 days: eclipse seasons (bands), new and full moons, today (red line)'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ fullmoondec
    'anim_fullmoondec_ciel': ('Le ciel à minuit, pleine lune au méridien', 'The sky at midnight, full moon on the meridian'),
    'anim_fullmoondec_graphe': ('Déclinaison de la pleine lune (bande ±5,1° ; pointillé : Soleil)',
                                'Declination of the full moon (band ±5.1°; dotted: Sun)'),
    'anim_fullmoondec_dec_soleil': ('Déclinaison du Soleil', 'Declination of the Sun'),
    'anim_fullmoondec_dec_lune': ('Déclinaison possible de la pleine lune', 'Possible declination of the full moon'),
    'anim_fullmoondec_hauteur': ('Hauteur à minuit (méridien)', 'Altitude at midnight (meridian)'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ moonbisector
    'anim_moonbisector_soleil': ('Direction du Soleil', 'Direction of the Sun'),
    'anim_moonbisector_soleil_aide': ('Direction du Soleil dans le plan de l’orbite (degrés).',
                                      'Direction of the Sun in the plane of the orbit (degrees).'),
    'anim_moonbisector_lune': ('Position de la Lune', 'Position of the Moon'),
    'anim_moonbisector_lune_aide': ('Position de la Lune sur son orbite (degrés, même origine que le Soleil) ; la '
                                    'différence des deux est l’angle de phase.',
                                    'Position of the Moon on its orbit (degrees, same origin as the Sun); the '
                                    'difference of the two is the phase angle.'),
    'anim_moonbisector_etape1': ('1. Direction du Soleil', '1. Sun direction'),
    'anim_moonbisector_etape1_aide': ('Étape 1 : la lumière du Soleil arrive en rayons parallèles sur la Terre et la '
                                      'Lune.',
                                      'Step 1: sunlight reaches the Earth and the Moon as parallel rays.'),
    'anim_moonbisector_etape2': ('2. Plans « Soleil »', '2. « Sun » planes'),
    'anim_moonbisector_etape2_aide': ('Étape 2 : plans perpendiculaires à la direction du Soleil, qui séparent la moitié '
                                      'éclairée de la moitié dans la nuit.',
                                      'Step 2: planes perpendicular to the direction of the Sun, which separate the lit '
                                      'half from the night half.'),
    'anim_moonbisector_etape3': ('3. Ombres', '3. Shadows'),
    'anim_moonbisector_etape3_aide': ('Étape 3 : assombrir la moitié de la Terre et de la Lune qui est dans la nuit.',
                                      'Step 3: darken the half of the Earth and of the Moon that is in the night.'),
    'anim_moonbisector_etape4': ('4. Ligne Terre–Lune', '4. Earth–Moon line'),
    'anim_moonbisector_etape4_aide': ('Étape 4 : la ligne qui joint la Terre et la Lune.',
                                      'Step 4: the line joining the Earth and the Moon.'),
    'anim_moonbisector_etape5': ('5. Plans « Terre–Lune »', '5. « Earth–Moon » planes'),
    'anim_moonbisector_etape5_aide': ('Étape 5 : plans perpendiculaires à la ligne Terre–Lune : la moitié de la Lune '
                                      'tournée vers la Terre est la seule qu’on puisse voir.',
                                      'Step 5: planes perpendicular to the Earth–Moon line: the half of the Moon facing '
                                      'the Earth is the only one that can be seen.'),
    'anim_moonbisector_etape6': ('6. Lune vue de la Terre', '6. Moon seen from Earth'),
    'anim_moonbisector_etape6_aide': ('Étape 6 : la phase, partie éclairée de la moitié tournée vers la Terre.',
                                      'Step 6: the phase, lit part of the half facing the Earth.'),
    'anim_moonbisector_dessus': ('Vue de dessus', 'Overhead view'),
    'anim_moonbisector_dessus_aide': ('Regarder le plan de l’orbite depuis le nord.',
                                      'Look at the plane of the orbit from the north.'),
    'anim_moonbisector_cote': ('Vue en perspective', 'Perspective view'),
    'anim_moonbisector_cote_aide': ('Revenir à la vue oblique de départ (on peut aussi faire tourner la vue à la '
                                    'souris).',
                                    'Go back to the initial oblique view (the view can also be rotated with the '
                                    'mouse).'),
    'anim_moonbisector_espace': ('La Terre et la Lune, et leurs plans bissecteurs', 'The Earth and the Moon, and their '
                                                                                    'bisecting planes'),
    'anim_moonbisector_disque': ('La Lune vue de la Terre', 'The Moon seen from the Earth'),
    'anim_moonbisector_angle_plans': ('Angle entre les deux plans de la Lune', 'Angle between the two planes of the Moon'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ eclipsetable
    'anim_eclipsetable_soleil': ('Éclipses de Soleil', 'Solar eclipses'),
    'anim_eclipsetable_soleil_aide': ('Montrer les éclipses de Soleil (disque jaune ; noir : totale, anneau : '
                                      'annulaire, encoche : partielle).',
                                      'Show the solar eclipses (yellow disc; black: total, ring: annular, notch: '
                                      'partial).'),
    'anim_eclipsetable_lune': ('Éclipses de Lune', 'Lunar eclipses'),
    'anim_eclipsetable_lune_aide': ('Montrer les éclipses de Lune (rouge : totale, rose : partielle, gris : par la '
                                    'pénombre).',
                                    'Show the lunar eclipses (red: total, pink: partial, grey: penumbral).'),
    'anim_eclipsetable_saisons': ('Saisons d’éclipses', 'Eclipse seasons'),
    'anim_eclipsetable_saisons_aide': ('Bandes de ±20 jours autour de chaque passage du Soleil à un nœud de l’orbite '
                                       'lunaire (jaune : nœud ascendant, bleu : descendant) ; toutes les éclipses y '
                                       'tombent.',
                                       'Bands of ±20 days around each passage of the Sun at a node of the lunar orbit '
                                       '(yellow: ascending node, blue: descending); every eclipse falls inside.'),
    'anim_eclipsetable_eclipse': ('Éclipse (cliquer sur une icône)', 'Eclipse (click an icon)'),
    'anim_eclipsetable_g_soleil': ('de Soleil du {date}', 'solar, {date}'),
    'anim_eclipsetable_g_lune': ('de Lune du {date}', 'lunar, {date}'),
    'anim_eclipsetable_type': ('Type', 'Type'),
    'anim_eclipsetable_t_total': ('totale', 'total'),
    'anim_eclipsetable_t_annular': ('annulaire', 'annular'),
    'anim_eclipsetable_t_hybrid': ('hybride', 'hybrid'),
    'anim_eclipsetable_t_partial': ('partielle', 'partial'),
    'anim_eclipsetable_t_penumbral': ('par la pénombre', 'penumbral'),
    'anim_eclipsetable_saros': ('Saros', 'Saros'),
    'anim_eclipsetable_grandeur': ('Grandeur', 'Magnitude'),
    'anim_eclipsetable_duree': ('Durée (centralité ; Lune : ombre, totalité)', 'Duration (central; Moon: umbra, '
                                                                                'totality)'),
    'anim_eclipsetable_zones': ('Visible depuis', 'Visible from'),
    'anim_eclipsetable_verif': ('Vérification (Meeus)', 'Check (Meeus)'),
    'anim_eclipsetable_verif_v': ('phase moyenne à {j} j, F = {f}°, |sin F| = {s} (< 0,36)',
                                  'mean phase at {j} d, F = {f}°, |sin F| = {s} (< 0.36)'),
})
ANIM_LOT2['anim_eclipsetable_totalite'] = ('totalité', 'totality')

ANIM_LOT2.update({
    # ------------------------------------------------------------ gravalgebra
    'anim_gravalgebra_m1': ('Masse M₁ multipliée par', 'Mass M₁ multiplied by'),
    'anim_gravalgebra_m1_aide': ('Facteur appliqué à la première masse.', 'Factor applied to the first mass.'),
    'anim_gravalgebra_m2': ('Masse M₂ multipliée par', 'Mass M₂ multiplied by'),
    'anim_gravalgebra_m2_aide': ('Facteur appliqué à la seconde masse.', 'Factor applied to the second mass.'),
    'anim_gravalgebra_d': ('Distance d multipliée par', 'Distance d multiplied by'),
    'anim_gravalgebra_d_aide': ('Facteur appliqué à la distance entre les centres (la force varie comme son carré '
                                'inverse).',
                                'Factor applied to the distance between the centres (the force varies as its inverse '
                                'square).'),
    'anim_gravalgebra_f_1_3': ('un tiers', 'one third'),
    'anim_gravalgebra_f_1_2': ('un demi', 'one half'),
    'anim_gravalgebra_f_1': ('un', 'one'),
    'anim_gravalgebra_f_2': ('deux', 'two'),
    'anim_gravalgebra_f_3': ('trois', 'three'),
    'anim_gravalgebra_calcul': ('Calcul', 'Computation'),
    'anim_gravalgebra_force': ('Nouvelle force', 'New force'),
    'anim_gravalgebra_fois': ('{f} fois la force de départ', '{f} times the initial force'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ venusphases, ptolemaic
    'anim_venusphases_venus': ('Position de Vénus', 'Position of Venus'),
    'anim_venusphases_venus_aide': ('Longitude héliocentrique de Vénus sur son orbite (0,723 ua) ; on peut aussi faire '
                                    'glisser Vénus.',
                                    'Heliocentric longitude of Venus on its orbit (0.723 AU); Venus can also be '
                                    'dragged.'),
    'anim_venusphases_terre': ('Position de la Terre', 'Position of the Earth'),
    'anim_venusphases_terre_aide': ('Longitude héliocentrique de la Terre ; on peut aussi faire glisser la Terre.',
                                    'Heliocentric longitude of the Earth; the Earth can also be dragged.'),
    'anim_venusphases_orbites': ('Système de Copernic (vu du nord)', 'Copernican system (seen from the north)'),
    'anim_venusphases_telescope': ('Vénus au télescope (taille apparente à l’échelle)',
                                   'Venus in the telescope (apparent size to scale)'),
    'anim_venusphases_diametre': ('Diamètre apparent', 'Apparent diameter'),
    'anim_ptolemaic_modele': ('Système de Ptolémée : épicycle sur la ligne Terre–Soleil',
                              'Ptolemaic system: epicycle on the Earth–Sun line'),
    'anim_ptolemaic_temps': ('Temps', 'Time'),
    'anim_ptolemaic_elong_max': ('Élongation maximale du modèle', 'Greatest elongation of the model'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ keplers_third
    'anim_keplers_third_a': ('Demi-grand axe a', 'Semimajor axis a'),
    'anim_keplers_third_a_aide': ('Demi-grand axe de l’orbite, en unités astronomiques (échelle logarithmique) ; la '
                                  'période suit.',
                                  'Semimajor axis of the orbit, in astronomical units (logarithmic scale); the period '
                                  'follows.'),
    'anim_keplers_third_p': ('Période P', 'Period P'),
    'anim_keplers_third_p_aide': ('Période de révolution, en années ; le demi-grand axe suit.',
                                  'Orbital period, in years; the semimajor axis follows.'),
    'anim_keplers_third_masse': ('Masse de l’étoile', 'Mass of the star'),
    'anim_keplers_third_masse_aide': ('Masse de l’étoile en masses solaires (1 pour le Soleil) : P² = a³ / M.',
                                      'Mass of the star in solar masses (1 for the Sun): P² = a³ / M.'),
    'anim_keplers_third_planete': ('Planète', 'Planet'),
    'anim_keplers_third_planete_aide': ('Prendre le demi-grand axe d’une planète du Système solaire.',
                                        'Take the semimajor axis of a planet of the Solar System.'),
    'anim_keplers_third_verif': ('Vérification', 'Check'),
    'anim_keplers_third_axe_a': ('demi-grand axe (ua)', 'semimajor axis (AU)'),
    'anim_keplers_third_axe_p': ('période (années)', 'period (years)'),
    # ------------------------------------------------------------ synodiccalculator
    'anim_synodiccalculator_genre': ('Planète', 'Planet'),
    'anim_synodiccalculator_genre_aide': ('Planète supérieure (plus loin du Soleil que la Terre) ou inférieure (plus '
                                          'près) : la formule change.',
                                          'Superior planet (farther from the Sun than the Earth) or inferior (closer): '
                                          'the formula changes.'),
    'anim_synodiccalculator_superieure': ('supérieure', 'superior'),
    'anim_synodiccalculator_inferieure': ('inférieure', 'inferior'),
    'anim_synodiccalculator_p': ('Période sidérale P', 'Sidereal period P'),
    'anim_synodiccalculator_p_aide': ('Période de révolution autour du Soleil par rapport aux étoiles (années '
                                      'sidérales) ; la période synodique suit.',
                                      'Period of revolution around the Sun with respect to the stars (sidereal years); '
                                      'the synodic period follows.'),
    'anim_synodiccalculator_s': ('Période synodique S', 'Synodic period S'),
    'anim_synodiccalculator_s_aide': ('Temps entre deux mêmes configurations vues de la Terre (deux oppositions, deux '
                                      'conjonctions inférieures…) ; la période sidérale suit.',
                                      'Time between two identical configurations seen from the Earth (two oppositions, '
                                      'two inferior conjunctions…); the sidereal period follows.'),
    'anim_synodiccalculator_planete': ('Préréglage', 'Preset'),
    'anim_synodiccalculator_planete_aide': ('Prendre la période sidérale d’une planète réelle.',
                                            'Take the sidereal period of a real planet.'),
    'anim_synodiccalculator_formule': ('Relation', 'Relation'),
    'anim_synodiccalculator_conjonctions': ('Périodes synodiques écoulées', 'Synodic periods elapsed'),
    'anim_synodiccalculator_planete_p': ('planète', 'planet'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ ellipsedemo
    'anim_ellipsedemo_a': ('Demi-grand axe a', 'Semimajor axis a'),
    'anim_ellipsedemo_a_aide': ('Demi-grand axe de l’ellipse (unités du dessin, de 40 à 100 comme l’original).',
                                'Semimajor axis of the ellipse (drawing units, from 40 to 100 as in the original).'),
    'anim_ellipsedemo_c': ('Distance centre–foyer c', 'Centre–focus distance c'),
    'anim_ellipsedemo_c_aide': ('Distance du centre à chacun des foyers (de 0, cercle, à a − 1).',
                                'Distance from the centre to each focus (from 0, a circle, to a − 1).'),
    'anim_ellipsedemo_jardinier': ('Somme des distances aux foyers', 'Sum of the distances to the foci'),
    'anim_ellipsedemo_jardinier_aide': ('Un point parcourt l’ellipse : la somme de ses distances aux deux foyers reste '
                                        'égale à 2a (le jardinier trace une ellipse avec une corde et deux piquets).',
                                        'A point runs along the ellipse: the sum of its distances to the two foci stays '
                                        'equal to 2a (the gardener draws an ellipse with a string and two stakes).'),
    'anim_ellipsedemo_b': ('Demi-petit axe b', 'Semiminor axis b'),
    'anim_ellipsedemo_b_aide': ('Montrer le demi-petit axe b = √(a² − c²).', 'Show the semiminor axis b = √(a² − c²).'),
    'anim_ellipsedemo_e': ('Excentricité e', 'Eccentricity e'),
    'anim_ellipsedemo_somme': ('Distances aux foyers', 'Distances to the foci'),
    # ------------------------------------------------------------ gravcalc
    'anim_gravcalc_m1': ('M₁ (puissance de 10)', 'M₁ (power of 10)'),
    'anim_gravcalc_m1_aide': ('Masse du premier corps : exposant de 10 en kilogrammes (−30 : électron ; 42 : Voie '
                              'lactée).',
                              'Mass of the first body: power of 10 in kilograms (−30: electron; 42: Milky Way).'),
    'anim_gravcalc_m2': ('M₂ (puissance de 10)', 'M₂ (power of 10)'),
    'anim_gravcalc_m2_aide': ('Masse du second corps : exposant de 10 en kilogrammes.',
                              'Mass of the second body: power of 10 in kilograms.'),
    'anim_gravcalc_r': ('R (puissance de 10)', 'R (power of 10)'),
    'anim_gravcalc_r_aide': ('Distance entre les centres : exposant de 10 en mètres (−15 : un proton ; 26 : rayon de '
                             'l’Univers observable).',
                             'Distance between the centres: power of 10 in metres (−15: a proton; 26: radius of the '
                             'observable Universe).'),
    'anim_gravcalc_pm1': ('Objet 1', 'Object 1'),
    'anim_gravcalc_pm1_aide': ('Prendre la masse d’un objet connu.', 'Take the mass of a known object.'),
    'anim_gravcalc_pm2': ('Objet 2', 'Object 2'),
    'anim_gravcalc_pm2_aide': ('Prendre la masse d’un objet connu.', 'Take the mass of a known object.'),
    'anim_gravcalc_pr': ('Distance', 'Distance'),
    'anim_gravcalc_pr_aide': ('Prendre une distance connue.', 'Take a known distance.'),
    'anim_gravcalc_libre': ('(valeur libre)', '(free value)'),
    'anim_gravcalc_memoriser': ('Mémoriser', 'Store'),
    'anim_gravcalc_memoriser_aide': ('Garder ces valeurs dans le tableau (six lignes au plus).',
                                     'Keep these values in the table (six rows at most).'),
    'anim_gravcalc_effacer': ('Effacer', 'Clear'),
    'anim_gravcalc_effacer_aide': ('Vider le tableau des valeurs mémorisées.', 'Empty the table of stored values.'),
    'anim_gravcalc_force': ('Force F', 'Force F'),
    'anim_gravcalc_a1': ('Accélération de M₁ (F / M₁)', 'Acceleration of M₁ (F / M₁)'),
    'anim_gravcalc_a2': ('Accélération de M₂ (F / M₂)', 'Acceleration of M₂ (F / M₂)'),
})
for _cle, _fr, _en in (('electron', 'électron', 'electron'), ('proton', 'proton', 'proton'),
                       ('pomme', 'petite pomme', 'small apple'), ('kilogramme', '1 kilogramme', '1 kilogram'),
                       ('personne', 'personne', 'person'), ('montagne', 'grande montagne', 'large mountain'),
                       ('asteroide', 'gros astéroïde', 'large asteroid'), ('lune', 'Lune', 'Moon'),
                       ('mars', 'Mars', 'Mars'), ('terre', 'Terre', 'Earth'), ('jupiter', 'Jupiter', 'Jupiter'),
                       ('soleil', 'Soleil', 'Sun'), ('voie_lactee', 'Voie lactée', 'Milky Way')):
    ANIM_LOT2['anim_gravcalc_m_' + _cle] = (_fr, _en)
for _cle, _fr, _en in (('proton', 'rayon d’un proton', 'proton radius'), ('atome', 'rayon d’un atome', 'atom radius'),
                       ('metre', '1 mètre', '1 metre'), ('deux_metres', 'distance sociale (2 m)', 'social spacing (2 m)'),
                       ('rayon_terre', 'rayon de la Terre', 'radius of the Earth'),
                       ('lune', 'distance de la Lune', 'distance to the Moon'),
                       ('mars', 'Mars au plus près', 'closest approach to Mars'),
                       ('soleil', 'distance du Soleil', 'distance to the Sun'),
                       ('jupiter', 'Jupiter au plus près', 'closest approach to Jupiter'),
                       ('etoile', 'étoile la plus proche', 'nearest star'),
                       ('voie_lactee', 'rayon de la Voie lactée', 'radius of the Milky Way'),
                       ('univers', 'rayon de l’Univers observable', 'radius of the observable Universe')):
    ANIM_LOT2['anim_gravcalc_d_' + _cle] = (_fr, _en)

ANIM_LOT2.update({
    # ------------------------------------------------------------ earthorbitplot
    'anim_earthorbitplot_r': ('Rayon de l’orbite', 'Orbital radius'),
    'anim_earthorbitplot_r_aide': ('Distance du satellite au centre de la Terre (échelle logarithmique, de la surface '
                                   'à 450 000 km) ; on peut aussi cliquer ou glisser sur la courbe.',
                                   'Distance of the satellite from the centre of the Earth (logarithmic scale, from the '
                                   'surface to 450,000 km); one can also click or drag on the curve.'),
    'anim_earthorbitplot_point': ('Orbite remarquable', 'Notable orbit'),
    'anim_earthorbitplot_point_aide': ('Aller à une orbite connue.', 'Go to a known orbit.'),
    'anim_earthorbitplot_p_newton': ('boulet de Newton (au ras du sol)', 'Newton’s cannonball (at ground level)'),
    'anim_earthorbitplot_p_iss': ('Station spatiale', 'Space Station'),
    'anim_earthorbitplot_p_gps': ('satellites GPS', 'GPS satellites'),
    'anim_earthorbitplot_p_geo': ('géostationnaire', 'geostationary'),
    'anim_earthorbitplot_p_lune': ('Lune', 'Moon'),
    'anim_earthorbitplot_log': ('Périodes en échelle logarithmique', 'Periods on a logarithmic scale'),
    'anim_earthorbitplot_log_aide': ('Axe des périodes logarithmique : la loi devient une droite de pente 3/2.',
                                     'Logarithmic period axis: the law becomes a straight line of slope 3/2.'),
    'anim_earthorbitplot_rayon': ('Rayon', 'Radius'),
    'anim_earthorbitplot_altitude': ('Altitude', 'Altitude'),
    'anim_earthorbitplot_periode': ('Période', 'Period'),
    'anim_earthorbitplot_vitesse': ('Vitesse', 'Speed'),
    'anim_earthorbitplot_lune_vraie': ('Avec la masse de la Lune', 'With the mass of the Moon'),
    'anim_earthorbitplot_axe_r': ('rayon de l’orbite (km)', 'orbital radius (km)'),
    'anim_earthorbitplot_axe_p': ('période (jours)', 'period (days)'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ configurationssimulator
    'anim_configurationssimulator_a_obs': ('Orbite de l’observateur', 'Observer’s orbit'),
    'anim_configurationssimulator_a_obs_aide': ('Demi-grand axe (ua) de la planète d’où l’on observe (1 : la Terre).',
                                                'Semimajor axis (AU) of the planet we observe from (1: the Earth).'),
    'anim_configurationssimulator_p_obs': ('Observateur', 'Observer'),
    'anim_configurationssimulator_p_obs_aide': ('Placer l’observateur sur une planète du Système solaire.',
                                                'Put the observer on a planet of the Solar System.'),
    'anim_configurationssimulator_a_cible': ('Orbite de la planète observée', 'Orbit of the observed planet'),
    'anim_configurationssimulator_a_cible_aide': ('Demi-grand axe (ua) de la planète observée (2,4 au départ, comme '
                                                  'l’original).',
                                                  'Semimajor axis (AU) of the observed planet (2.4 at start, as in the '
                                                  'original).'),
    'anim_configurationssimulator_p_cible': ('Planète observée', 'Observed planet'),
    'anim_configurationssimulator_p_cible_aide': ('Prendre une planète du Système solaire.',
                                                  'Take a planet of the Solar System.'),
    'anim_configurationssimulator_action': ('À chaque configuration', 'At each configuration'),
    'anim_configurationssimulator_action_aide': ('Continuer, s’arrêter, ou faire une pause (durée réglable) quand une '
                                                 'configuration est atteinte.',
                                                 'Keep going, stop, or pause (adjustable duration) when a configuration '
                                                 'is reached.'),
    'anim_configurationssimulator_continuer': ('continuer', 'keep going'),
    'anim_configurationssimulator_arreter': ('s’arrêter', 'stop'),
    'anim_configurationssimulator_pause': ('pause', 'pause'),
    'anim_configurationssimulator_duree_pause': ('Durée de la pause', 'Pause duration'),
    'anim_configurationssimulator_duree_pause_aide': ('Durée de la pause à chaque configuration (secondes).',
                                                      'Duration of the pause at each configuration (seconds).'),
    'anim_configurationssimulator_elongation': ('Angle d’élongation', 'Elongation angle'),
    'anim_configurationssimulator_elongation_aide': ('Tracer l’angle, vu de l’observateur, entre le Soleil et la '
                                                     'planète.',
                                                     'Draw the angle, seen from the observer, between the Sun and the '
                                                     'planet.'),
    'anim_configurationssimulator_s': ('Période synodique', 'Synodic period'),
    'anim_configurationssimulator_temps': ('Temps', 'Time'),
    'anim_configurationssimulator_prochain': ('Prochaine configuration', 'Next configuration'),
    'anim_configurationssimulator_dans': ('{nom} dans {j} jours', '{nom} in {j} days'),
    'anim_configurationssimulator_elong_max': ('Plus grande élongation', 'Greatest elongation'),
    'anim_configurationssimulator_observateur': ('observateur', 'observer'),
    'anim_configurationssimulator_cible': ('planète', 'planet'),
    'anim_configurationssimulator_e_opposition': ('opposition', 'opposition'),
    'anim_configurationssimulator_e_quadrature_est': ('quadrature orientale', 'eastern quadrature'),
    'anim_configurationssimulator_e_conjonction': ('conjonction', 'conjunction'),
    'anim_configurationssimulator_e_quadrature_ouest': ('quadrature occidentale', 'western quadrature'),
    'anim_configurationssimulator_e_conj_inf': ('conjonction inférieure', 'inferior conjunction'),
    'anim_configurationssimulator_e_elong_ouest': ('plus grande élongation ouest', 'greatest western elongation'),
    'anim_configurationssimulator_e_conj_sup': ('conjonction supérieure', 'superior conjunction'),
    'anim_configurationssimulator_e_elong_est': ('plus grande élongation est', 'greatest eastern elongation'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ smallangledemo
    'anim_smallangledemo_diametre': ('Diamètre d', 'Diameter d'),
    'anim_smallangledemo_diametre_aide': ('Diamètre de la boule (unités arbitraires, de 1 à 3 comme l’original).',
                                          'Diameter of the ball (arbitrary units, from 1 to 3 as in the original).'),
    'anim_smallangledemo_distance': ('Distance D', 'Distance D'),
    'anim_smallangledemo_distance_aide': ('Distance de l’œil au centre de la boule (mêmes unités) ; on peut aussi '
                                          'faire glisser la boule.',
                                          'Distance from the eye to the centre of the ball (same units); the ball can '
                                          'also be dragged.'),
    'anim_smallangledemo_approche': ('Petits angles : 206 265″ × d / D', 'Small angles: 206,265″ × d / D'),
    'anim_smallangledemo_exacte': ('Valeur exacte : 2 asin(d / 2D)', 'Exact value: 2 asin(d / 2D)'),
    'anim_smallangledemo_erreur': ('Écart relatif de l’approximation', 'Relative error of the approximation'),
    # ------------------------------------------------------------ dipperclock
    'anim_dipperclock_noms': ('Noms', 'Labels'),
    'anim_dipperclock_noms_aide': ('Nommer l’étoile Polaire, la Grande Ourse, la Petite Ourse et Cassiopée.',
                                   'Label the North Star, the Big Dipper, the Little Dipper and Cassiopeia.'),
    'anim_dipperclock_grande_ourse': ('Grande Ourse', 'Big Dipper'),
    'anim_dipperclock_petite_ourse': ('Petite Ourse', 'Little Dipper'),
    'anim_dipperclock_cassiopee': ('Cassiopée', 'Cassiopeia'),
    'anim_dipperclock_polaire': ('Polaire', 'North Star'),
    'anim_dipperclock_dubhe': ('Angle horaire de Dubhe', 'Hour angle of Dubhe'),
})
for _v in (20, 30, 40, 50, 60):
    ANIM_LOT2['anim_smallangledemo_b%d' % _v] = ('D = %d' % _v, 'D = %d' % _v)
    ANIM_LOT2['anim_smallangledemo_b%d_aide' % _v] = ('Placer la boule à la distance %d.' % _v,
                                                      'Put the ball at distance %d.' % _v)

ANIM_LOT2.update({
    # ------------------------------------------------------------ heliacalrisingsim
    'anim_heliacalrisingsim_etoile': ('Étoile', 'Star'),
    'anim_heliacalrisingsim_etoile_aide': ('Choisir une étoile brillante (l’original proposait Véga et Sirius), ou '
                                           'régler librement α et δ.',
                                           'Choose a bright star (the original offered Vega and Sirius), or set α and δ '
                                           'freely.'),
    'anim_heliacalrisingsim_depression': ('Abaissement du Soleil', 'Sun depression'),
    'anim_heliacalrisingsim_depression_aide': ('Profondeur du Soleil sous l’horizon à partir de laquelle l’étoile '
                                               'devient visible (7° comme l’original ; plus pour une étoile faible).',
                                               'Depth of the Sun below the horizon from which the star becomes visible '
                                               '(7° as in the original; more for a faint star).'),
    'anim_heliacalrisingsim_aube': ('Début de l’aube', 'Start of dawn'),
    'anim_heliacalrisingsim_aube_aide': ('Placer l’heure au début de l’aube (Soleil à l’abaissement choisi) au lieu de '
                                         'l’heure réglée.',
                                         'Set the time to the start of dawn (Sun at the chosen depression) instead of '
                                         'the set time.'),
    'anim_heliacalrisingsim_h_aube': ('Hauteur de l’étoile à l’aube', 'Altitude of the star at dawn'),
    'anim_heliacalrisingsim_lever': ('Lever héliaque', 'Heliacal rising'),
    'anim_heliacalrisingsim_jamais': ('aucun (étoile circumpolaire ou jamais levée)', 'none (circumpolar or never '
                                                                                       'rising star)'),
    'anim_heliacalrisingsim_graphe': ('L’année : nuit (sombre), étoile levée (bleu), lever héliaque (trait jaune)',
                                      'The year: night (dark), star up (blue), heliacal rising (yellow line)'),
    'anim_heliacalrisingsim_ciel': ('Le ciel à cet instant', 'The sky at that time'),
})
for _cle, _fr, _en in (('sirius', 'Sirius', 'Sirius'), ('vega', 'Véga', 'Vega'), ('aldebaran', 'Aldébaran', 'Aldebaran'),
                       ('spica', 'Spica', 'Spica'), ('antares', 'Antarès', 'Antares'),
                       ('fomalhaut', 'Fomalhaut', 'Fomalhaut'), ('arcturus', 'Arcturus', 'Arcturus')):
    ANIM_LOT2['anim_heliacalrisingsim_e_' + _cle] = (_fr, _en)

ANIM_LOT2.update({
    # ------------------------------------------------------------ transitmovie
    'anim_transitmovie_midi': ('Midi vrai', 'True noon'),
    'anim_transitmovie_midi_aide': ('Montrer le bâtiment chaque jour au midi vrai (Soleil au méridien) au lieu de '
                                    'l’heure réglée : l’ombre pointe alors toujours vers le nord.',
                                    'Show the building every day at true noon (Sun on the meridian) instead of the set '
                                    'time: the shadow then always points north.'),
    'anim_transitmovie_trace': ('Trajet de l’ombre dans la journée', 'Path of the shadow during the day'),
    'anim_transitmovie_trace_aide': ('Tracer le chemin, du lever au coucher, de l’ombre du coin nord-est du toit.',
                                     'Draw the path, from sunrise to sunset, of the shadow of the north-east corner of '
                                     'the roof.'),
    'anim_transitmovie_scene': ('Le bâtiment et son ombre (faire tourner la vue à la souris)',
                                'The building and its shadow (rotate the view with the mouse)'),
    'anim_transitmovie_graphe': ('Hauteur du Soleil à cette heure, au fil de l’année',
                                 'Altitude of the Sun at this time, over the year'),
    'anim_transitmovie_dec': ('Déclinaison du Soleil', 'Declination of the Sun'),
    'anim_transitmovie_longueur': ('Longueur de l’ombre (× hauteur)', 'Shadow length (× height)'),
})

ANIM_LOT2.update({
    # ------------------------------------------------------------ stellarlum
    'anim_stellarlum_rayon': ('Rayon', 'Radius'),
    'anim_stellarlum_rayon_aide': ('Rayon de l’étoile en rayons solaires (0,01 à 100, échelle logarithmique).',
                                   'Radius of the star in solar radii (0.01 to 100, logarithmic scale).'),
    'anim_stellarlum_type': ('Type spectral', 'Spectral type'),
    'anim_stellarlum_type_aide': ('Type spectral numérique (O7 = 7, B0 = 10, A0 = 20, F0 = 30, G0 = 40, K0 = 50, M0 = 60) '
                                  'de la séquence principale ; il fixe la température.',
                                  'Numerical spectral type (O7 = 7, B0 = 10, A0 = 20, F0 = 30, G0 = 40, K0 = 50, M0 = 60) '
                                  'on the main sequence; it sets the temperature.'),
    'anim_stellarlum_type_v': ('Type spectral', 'Spectral type'),
    'anim_stellarlum_temperature': ('Température', 'Temperature'),
    'anim_stellarlum_rayon_m': ('Rayon', 'Radius'),
    'anim_stellarlum_lum': ('Luminosité', 'Luminosity'),
    'anim_stellarlum_soleil': ('Soleil', 'Sun'),
    'anim_stellarlum_echelle': ('Tailles sur une échelle logarithmique (0,01 à 100 R☉)',
                                'Sizes on a logarithmic scale (0.01 to 100 R☉)'),
    # ------------------------------------------------------------ lightdetector
    'anim_lightdetector_puissance': ('Ampoule', 'Light bulb'),
    'anim_lightdetector_puissance_aide': ('Puissance rayonnée par l’ampoule (watts).',
                                          'Power radiated by the bulb (watts).'),
    'anim_lightdetector_distance': ('Distance du détecteur', 'Detector distance'),
    'anim_lightdetector_distance_aide': ('Distance entre l’ampoule et le détecteur (1 à 5 m) ; on peut aussi faire '
                                         'glisser le détecteur.',
                                         'Distance between the bulb and the detector (1 to 5 m); the detector can also '
                                         'be dragged.'),
    'anim_lightdetector_spheres': ('Sphères', 'Spheres'),
    'anim_lightdetector_spheres_aide': ('Tracer les sphères de 1 à 5 m sur lesquelles la lumière se répartit.',
                                        'Draw the spheres of 1 to 5 m over which the light spreads.'),
    'anim_lightdetector_flux': ('Flux reçu', 'Received flux'),
    'anim_lightdetector_rapport': ('Fraction du flux à 1 m', 'Fraction of the flux at 1 m'),
    'anim_lightdetector_aire': ('Aire de la sphère 4π d²', 'Area of the sphere 4π d²'),
    'anim_lightdetector_detecteur': ('détecteur', 'detector'),
    # ------------------------------------------------------------ stellarvel
    'anim_stellarvel_lambda': ('Longueur d’onde de Hα observée', 'Observed Hα wavelength'),
    'anim_stellarvel_lambda_aide': ('Longueur d’onde mesurée de la raie Hα (656,28 nm au repos) : plus grande, '
                                    'l’étoile s’éloigne (décalage vers le rouge).',
                                    'Measured wavelength of the Hα line (656.28 nm at rest): longer, the star recedes '
                                    '(redshift).'),
    'anim_stellarvel_mu': ('Mouvement propre', 'Proper motion'),
    'anim_stellarvel_mu_aide': ('Déplacement apparent de l’étoile sur le ciel, en secondes d’arc par an.',
                                'Apparent motion of the star on the sky, in arcseconds per year.'),
    'anim_stellarvel_distance': ('Distance', 'Distance'),
    'anim_stellarvel_distance_aide': ('Distance de l’étoile en parsecs (1 à 10) ; on peut aussi faire glisser l’étoile.',
                                      'Distance of the star in parsecs (1 to 10); the star can also be dragged.'),
    'anim_stellarvel_vr': ('Vitesse radiale c Δλ / λ₀', 'Radial velocity c Δλ / λ₀'),
    'anim_stellarvel_vt': ('Vitesse transverse 4,74 μ d', 'Transverse velocity 4.74 μ d'),
    'anim_stellarvel_v': ('Vitesse dans l’espace', 'Space velocity'),
    'anim_stellarvel_angle': ('Angle avec la ligne de visée', 'Angle with the line of sight'),
    'anim_stellarvel_relativiste': ('Vitesse radiale (formule relativiste)', 'Radial velocity (relativistic formula)'),
    'anim_stellarvel_eloigne': ('s’éloigne', 'receding'),
    'anim_stellarvel_approche': ('se rapproche', 'approaching'),
    # ------------------------------------------------------------ spectroparallax
    'anim_spectroparallax_type': ('Type spectral', 'Spectral type'),
    'anim_spectroparallax_type_aide': ('Type spectral numérique (O0 = 0 … M9 = 69), tel qu’on le lit dans le spectre ; '
                                       'on peut aussi cliquer dans le diagramme.',
                                       'Numerical spectral type (O0 = 0 … M9 = 69), as read from the spectrum; one can '
                                       'also click in the diagram.'),
    'anim_spectroparallax_classe': ('Classe de luminosité', 'Luminosity class'),
    'anim_spectroparallax_classe_aide': ('I supergéante, II géante lumineuse, III géante, IV sous-géante, V naine '
                                         '(séquence principale) : se lit à la finesse des raies.',
                                         'I supergiant, II bright giant, III giant, IV subgiant, V dwarf (main '
                                         'sequence): read from the width of the lines.'),
    'anim_spectroparallax_c_I': ('I (supergéante)', 'I (supergiant)'),
    'anim_spectroparallax_c_II': ('II (géante lumineuse)', 'II (bright giant)'),
    'anim_spectroparallax_c_III': ('III (géante)', 'III (giant)'),
    'anim_spectroparallax_c_IV': ('IV (sous-géante)', 'IV (subgiant)'),
    'anim_spectroparallax_c_V': ('V (séquence principale)', 'V (main sequence)'),
    'anim_spectroparallax_m': ('Magnitude apparente m', 'Apparent magnitude m'),
    'anim_spectroparallax_m_aide': ('Magnitude apparente mesurée de l’étoile (−5 à 15).',
                                    'Measured apparent magnitude of the star (−5 to 15).'),
    'anim_spectroparallax_emission': ('Raies en émission', 'Emission lines'),
    'anim_spectroparallax_emission_aide': ('Montrer les raies en couleur sur fond noir (émission) au lieu de raies '
                                           'sombres sur l’arc-en-ciel (absorption).',
                                           'Show the lines in colour on a black background (emission) instead of dark '
                                           'lines on the rainbow (absorption).'),
    'anim_spectroparallax_type_c': ('Type et classe', 'Type and class'),
    'anim_spectroparallax_lum': ('Luminosité (diagramme HR)', 'Luminosity (HR diagram)'),
    'anim_spectroparallax_M': ('Magnitude absolue M', 'Absolute magnitude M'),
    'anim_spectroparallax_module': ('Module de distance m − M', 'Distance modulus m − M'),
    'anim_spectroparallax_distance': ('Distance', 'Distance'),
    'anim_spectroparallax_al': ('al', 'ly'),
    'anim_spectroparallax_raies': ('Raies', 'Lines'),
    'anim_spectroparallax_diagramme': ('Diagramme HR et classes de luminosité', 'HR diagram and luminosity classes'),
    'anim_spectroparallax_spectre': ('Spectre', 'Spectrum'),
    'anim_spectroparallax_axe_x': ('type spectral (température décroissante)', 'spectral type (decreasing temperature)'),
    'anim_spectroparallax_f_he_ii': ('hélium ionisé', 'ionized helium'),
    'anim_spectroparallax_f_he_i': ('hélium', 'helium'),
    'anim_spectroparallax_f_h': ('hydrogène', 'hydrogen'),
    'anim_spectroparallax_f_metaux_ionises': ('métaux ionisés', 'ionized metals'),
    'anim_spectroparallax_f_metaux': ('métaux neutres', 'neutral metals'),
    'anim_spectroparallax_f_molecules': ('molécules', 'molecules'),
    'anim_spectroparallax_q_tf': ('{f} très faible', 'very weak {f}'),
    'anim_spectroparallax_q_f': ('{f} faible', 'weak {f}'),
    'anim_spectroparallax_q_m': ('{f} moyen', 'moderate {f}'),
    'anim_spectroparallax_q_F': ('{f} fort', 'strong {f}'),
    'anim_spectroparallax_q_tF': ('{f} très fort', 'very strong {f}'),
    # ------------------------------------------------------------ hrexplorer
    'anim_hrexplorer_temperature': ('Température', 'Temperature'),
    'anim_hrexplorer_temperature_aide': ('Température de surface de l’étoile (2 300 à 40 000 K) ; on peut aussi cliquer '
                                         'ou glisser dans le diagramme.',
                                         'Surface temperature of the star (2,300 to 40,000 K); one can also click or '
                                         'drag in the diagram.'),
    'anim_hrexplorer_luminosite': ('Luminosité', 'Luminosity'),
    'anim_hrexplorer_luminosite_aide': ('Luminosité en luminosités solaires (10⁻⁴ à 10⁶, échelle logarithmique).',
                                        'Luminosity in solar luminosities (10⁻⁴ to 10⁶, logarithmic scale).'),
    'anim_hrexplorer_groupe': ('Étoiles', 'Stars'),
    'anim_hrexplorer_groupe_aide': ('Placer dans le diagramme les étoiles les plus proches, les plus brillantes, les '
                                    'deux, ou seulement celles qui sont à la fois proches et brillantes.',
                                    'Plot the nearest stars, the brightest ones, both, or only those that are both near '
                                    'and bright.'),
    'anim_hrexplorer_g_aucune': ('aucune', 'none'),
    'anim_hrexplorer_g_proches': ('les plus proches', 'nearest'),
    'anim_hrexplorer_g_brillantes': ('les plus brillantes', 'brightest'),
    'anim_hrexplorer_g_les_deux': ('les deux', 'both'),
    'anim_hrexplorer_g_communes': ('proches et brillantes', 'near and bright'),
    'anim_hrexplorer_sequence': ('Séquence principale', 'Main sequence'),
    'anim_hrexplorer_sequence_aide': ('Tracer la séquence principale (classe V).', 'Draw the main sequence (class V).'),
    'anim_hrexplorer_classes': ('Autres classes', 'Other classes'),
    'anim_hrexplorer_classes_aide': ('Tracer les classes de luminosité I à IV (supergéantes à sous-géantes).',
                                     'Draw the luminosity classes I to IV (supergiants to subgiants).'),
    'anim_hrexplorer_rayons': ('Rayons égaux', 'Equal radii'),
    'anim_hrexplorer_rayons_aide': ('Tracer les droites d’égal rayon (de 0,0001 à 1 000 R☉).',
                                    'Draw the lines of equal radius (from 0.0001 to 1,000 R☉).'),
    'anim_hrexplorer_rayon': ('Rayon', 'Radius'),
    'anim_hrexplorer_formule': ('Relation', 'Relation'),
    'anim_hrexplorer_diagramme': ('Diagramme de Hertzsprung-Russell', 'Hertzsprung-Russell diagram'),
    'anim_hrexplorer_comparaison': ('Comparaison avec le Soleil', 'Comparison with the Sun'),
    'anim_hrexplorer_axe_t': ('température (K)', 'temperature (K)'),
    'anim_hrexplorer_hors_echelle': ('(au moins un disque est trop petit pour être à l’échelle)',
                                     '(at least one disc is too small to be to scale)'),
})
for _w in (20, 25, 50, 100, 400, 500):
    ANIM_LOT2['anim_lightdetector_w%d' % _w] = ('%d W' % _w, '%d W' % _w)
