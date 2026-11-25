"""Textes FR/EN des animations de cours de la 0.12.0 (diagramme a–e, assistance gravitationnelle, cratère d'impact,
libration, précession des équinoxes, résonances et chaos, limite de Roche).  Fusionnés dans ``textes.TEXTES`` (et
exportés tels quels vers Coupole Web)."""

ANIM_COURS_2 = {
    # ================================================================ Le diagramme a–e
    'anim_aediagram_objet': ('Petit corps', 'Small body'),
    'anim_aediagram_objet_aide': ('Un astéroïde ou une comète réels (éléments de la base SBDB du JPL, arrondis) : '
                                  'son point se place sur le diagramme.',
                                  'A real asteroid or comet (elements from JPL’s SBDB, rounded): its point is placed '
                                  'on the diagram.'),
    'anim_aediagram_o_libre': ('(point choisi à la souris)', '(point chosen with the mouse)'),
    'anim_aediagram_o_atira': ('(163693) Atira', '(163693) Atira'),
    'anim_aediagram_o_apophis': ('(99942) Apophis', '(99942) Apophis'),
    'anim_aediagram_o_tk7': ('2010 TK7 (troyen de la Terre)', '2010 TK7 (Earth Trojan)'),
    'anim_aediagram_o_cruithne': ('(3753) Cruithne', '(3753) Cruithne'),
    'anim_aediagram_o_bennu': ('(101955) Bennu', '(101955) Bennu'),
    'anim_aediagram_o_ryugu': ('(162173) Ryugu', '(162173) Ryugu'),
    'anim_aediagram_o_itokawa': ('(25143) Itokawa', '(25143) Itokawa'),
    'anim_aediagram_o_icare': ('(1566) Icare', '(1566) Icarus'),
    'anim_aediagram_o_phaethon': ('(3200) Phaéton (Géminides)', '(3200) Phaethon (Geminids)'),
    'anim_aediagram_o_didymos': ('(65803) Didymos (DART)', '(65803) Didymos (DART)'),
    'anim_aediagram_o_toutatis': ('(4179) Toutatis', '(4179) Toutatis'),
    'anim_aediagram_o_eros': ('(433) Éros', '(433) Eros'),
    'anim_aediagram_o_encke': ('2P/Encke', '2P/Encke'),
    'anim_aediagram_o_vesta': ('(4) Vesta', '(4) Vesta'),
    'anim_aediagram_o_ceres': ('(1) Cérès', '(1) Ceres'),
    'anim_aediagram_o_pallas': ('(2) Pallas', '(2) Pallas'),
    'anim_aediagram_o_hygie': ('(10) Hygie', '(10) Hygiea'),
    'anim_aediagram_o_tchouri': ('67P/Tchourioumov-Guérassimenko', '67P/Churyumov-Gerasimenko'),
    'anim_aediagram_o_hilda': ('(153) Hilda', '(153) Hilda'),
    'anim_aediagram_o_hektor': ('(624) Hektor (troyen de Jupiter)', '(624) Hektor (Jupiter Trojan)'),
    'anim_aediagram_o_hidalgo': ('(944) Hidalgo', '(944) Hidalgo'),
    'anim_aediagram_o_chiron': ('(2060) Chiron', '(2060) Chiron'),
    'anim_aediagram_o_halley': ('1P/Halley', '1P/Halley'),
    'anim_aediagram_o_swift_tuttle': ('109P/Swift-Tuttle (Perséides)', '109P/Swift-Tuttle (Perseids)'),
    'anim_aediagram_o_pluton': ('(134340) Pluton', '(134340) Pluto'),
    'anim_aediagram_o_arrokoth': ('(486958) Arrokoth', '(486958) Arrokoth'),
    'anim_aediagram_o_eris': ('(136199) Éris', '(136199) Eris'),
    'anim_aediagram_a': ('Demi-grand axe a', 'Semi-major axis a'),
    'anim_aediagram_a_aide': ('Taille de l’orbite, en unités astronomiques (échelle logarithmique) ; la période en '
                              'découle : P = a √a ans.',
                              'Size of the orbit, in astronomical units (logarithmic scale); the period follows: '
                              'P = a √a years.'),
    'anim_aediagram_e': ('Excentricité e', 'Eccentricity e'),
    'anim_aediagram_e_aide': ('Allongement de l’orbite : 0 pour un cercle, près de 1 pour une ellipse très '
                              'allongée (comète).',
                              'Elongation of the orbit: 0 for a circle, close to 1 for a very elongated ellipse '
                              '(comet).'),
    'anim_aediagram_i': ('Inclinaison i', 'Inclination i'),
    'anim_aediagram_i_aide': ('Inclinaison de l’orbite sur l’écliptique ; elle ne change pas le diagramme, seulement '
                              'le paramètre de Tisserand (au-delà de 90°, l’orbite est rétrograde, comme celle de '
                              'Halley).',
                              'Inclination of the orbit to the ecliptic; it does not change the diagram, only the '
                              'Tisserand parameter (beyond 90°, the orbit is retrograde, like Halley’s).'),
    'anim_aediagram_familles': ('Familles de géocroiseurs', 'Near-Earth object groups'),
    'anim_aediagram_familles_aide': ('Courbes q = 1,017 ua (aphélie de la Terre), q = 1,3 ua (limite des géocroiseurs), '
                                     'q = 1,666 ua (aphélie de Mars), Q = 0,983 ua (périhélie de la Terre, pointillé) '
                                     'et a = 1 ua.',
                                     'Curves q = 1.017 au (Earth’s aphelion), q = 1.3 au (near-Earth limit), '
                                     'q = 1.666 au (Mars’s aphelion), Q = 0.983 au (Earth’s perihelion, dotted) and '
                                     'a = 1 au.'),
    'anim_aediagram_kirkwood': ('Résonances avec Jupiter', 'Resonances with Jupiter'),
    'anim_aediagram_kirkwood_aide': ('Demi-grands axes où le corps fait p tours pendant que Jupiter en fait q : en rouge '
                                     'les lacunes de Kirkwood (3:1, 5:2, 7:3, 2:1), vidées par Jupiter ; en bleu les '
                                     'résonances qui retiennent au contraire des astéroïdes (Hilda 3:2, troyens 1:1).',
                                     'Semi-major axes where the body makes p revolutions while Jupiter makes q: in red '
                                     'the Kirkwood gaps (3:1, 5:2, 7:3, 2:1), emptied by Jupiter; in blue the '
                                     'resonances that on the contrary hold asteroids (Hildas 3:2, Trojans 1:1).'),
    'anim_aediagram_objets': ('Petits corps réels', 'Real small bodies'),
    'anim_aediagram_objets_aide': ('Les 27 astéroïdes et comètes de la liste, en points bleus.',
                                   'The 27 asteroids and comets of the list, as blue dots.'),
    'anim_aediagram_souris': ('Cliquer ou glisser dans le diagramme : choisir a et e.',
                              'Click or drag in the diagram: choose a and e.'),
    'anim_aediagram_t_diagramme': ('Diagramme demi-grand axe – excentricité', 'Semi-major axis – eccentricity diagram'),
    'anim_aediagram_t_orbite': ('L’orbite vue de dessus, parmi celles des planètes', 'The orbit seen from above, among '
                                'those of the planets'),
    'anim_aediagram_axe_a': ('a (ua)', 'a (au)'),
    'anim_aediagram_axe_e': ('e', 'e'),
    'anim_aediagram_l_atira': ('Atira', 'Atira'),
    'anim_aediagram_l_aten': ('Aten', 'Aten'),
    'anim_aediagram_l_apollo': ('Apollo', 'Apollo'),
    'anim_aediagram_l_amor': ('Amor', 'Amor'),
    'anim_aediagram_l_ceinture': ('ceinture principale', 'main belt'),
    'anim_aediagram_l_troyen': ('troyens', 'Trojans'),
    'anim_aediagram_l_centaure': ('centaures', 'Centaurs'),
    'anim_aediagram_l_transneptunien': ('transneptuniens', 'trans-Neptunian'),
    'anim_aediagram_echelle': ('cadre : ± {d}', 'frame: ± {d}'),
    'anim_aediagram_v_q': ('Périhélie q = a(1 − e)', 'Perihelion q = a(1 − e)'),
    'anim_aediagram_v_Q': ('Aphélie Q = a(1 + e)', 'Aphelion Q = a(1 + e)'),
    'anim_aediagram_v_p': ('Période P = a √a', 'Period P = a √a'),
    'anim_aediagram_ans': ('{n} ans', '{n} years'),
    'anim_aediagram_v_famille': ('Classe de l’orbite', 'Orbit class'),
    'anim_aediagram_f_atira': ('géocroiseur Atira (orbite entièrement intérieure à celle de la Terre)',
                               'Atira near-Earth object (orbit entirely inside Earth’s)'),
    'anim_aediagram_f_aten': ('géocroiseur Aten (a < 1 ua, croise l’orbite de la Terre)',
                              'Aten near-Earth object (a < 1 au, crosses Earth’s orbit)'),
    'anim_aediagram_f_apollo': ('géocroiseur Apollo (a > 1 ua, croise l’orbite de la Terre)',
                                'Apollo near-Earth object (a > 1 au, crosses Earth’s orbit)'),
    'anim_aediagram_f_amor': ('géocroiseur Amor (frôle l’orbite de la Terre par l’extérieur)',
                              'Amor near-Earth object (grazes Earth’s orbit from outside)'),
    'anim_aediagram_f_croiseur_mars': ('croiseur de Mars', 'Mars-crosser'),
    'anim_aediagram_f_ceinture_int': ('bord intérieur de la ceinture (a < 2 ua)', 'inner edge of the belt (a < 2 au)'),
    'anim_aediagram_f_ceinture': ('ceinture principale', 'main belt'),
    'anim_aediagram_f_ceinture_ext': ('ceinture extérieure (dont les Hilda)', 'outer belt (including the Hildas)'),
    'anim_aediagram_f_troyen': ('troyen de Jupiter (si l’objet est près de L4 ou L5)',
                                'Jupiter Trojan (if the object is near L4 or L5)'),
    'anim_aediagram_f_autre': ('autre (orbite allongée près de Jupiter)', 'other (elongated orbit near Jupiter)'),
    'anim_aediagram_f_centaure': ('centaure (entre Jupiter et Neptune)', 'Centaur (between Jupiter and Neptune)'),
    'anim_aediagram_f_transneptunien': ('transneptunien', 'trans-Neptunian object'),
    'anim_aediagram_v_croise': ('Croise l’orbite de', 'Crosses the orbit of'),
    'anim_aediagram_aucune': ('aucune planète', 'no planet'),
    'anim_aediagram_p_mercure': ('Mercure', 'Mercury'),
    'anim_aediagram_p_venus': ('Vénus', 'Venus'),
    'anim_aediagram_p_terre': ('Terre', 'Earth'),
    'anim_aediagram_p_mars': ('Mars', 'Mars'),
    'anim_aediagram_p_jupiter': ('Jupiter', 'Jupiter'),
    'anim_aediagram_p_saturne': ('Saturne', 'Saturn'),
    'anim_aediagram_p_uranus': ('Uranus', 'Uranus'),
    'anim_aediagram_p_neptune': ('Neptune', 'Neptune'),
    'anim_aediagram_v_tisserand': ('Paramètre de Tisserand T (vis-à-vis de Jupiter)', 'Tisserand parameter T (with respect to Jupiter)'),
    'anim_aediagram_t_asteroide': ('orbite d’astéroïde (T > 3)', 'asteroid orbit (T > 3)'),
    'anim_aediagram_t_comete_jupiter': ('orbite de comète de la famille de Jupiter (2 < T < 3)',
                                        'Jupiter-family comet orbit (2 < T < 3)'),
    'anim_aediagram_t_comete_halley': ('orbite de comète de type Halley ou à longue période (T < 2)',
                                       'Halley-type or long-period comet orbit (T < 2)'),
    'anim_aediagram_v_distance': ('Distance au Soleil en ce moment', 'Distance from the Sun right now'),

    # ================================================================ L'assistance gravitationnelle
    'anim_gravityassist_planete': ('Planète survolée', 'Planet flown by'),
    'anim_gravityassist_planete_aide': ('Plus la planète est massive, plus elle tourne la trajectoire ; plus elle va '
                                        'vite sur son orbite, plus le gain possible est grand.',
                                        'The more massive the planet, the more it bends the trajectory; the faster it '
                                        'moves on its orbit, the larger the possible gain.'),
    'anim_gravityassist_p_venus': ('Vénus', 'Venus'),
    'anim_gravityassist_p_terre': ('Terre', 'Earth'),
    'anim_gravityassist_p_mars': ('Mars', 'Mars'),
    'anim_gravityassist_p_jupiter': ('Jupiter', 'Jupiter'),
    'anim_gravityassist_p_saturne': ('Saturne', 'Saturn'),
    'anim_gravityassist_vinf': ('Vitesse d’arrivée v∞', 'Arrival speed v∞'),
    'anim_gravityassist_vinf_aide': ('Vitesse de la sonde par rapport à la planète, loin d’elle (vitesse « à l’infini »). '
                                     'Elle est la même au départ : vue de la planète, la sonde ne gagne rien.',
                                     'Speed of the probe relative to the planet, far from it (speed “at infinity”). '
                                     'It is the same on departure: seen from the planet, the probe gains nothing.'),
    'anim_gravityassist_rp': ('Distance au plus près rₚ (en rayons)', 'Closest distance rₚ (in radii)'),
    'anim_gravityassist_rp_aide': ('Distance du centre de la planète au point le plus proche, en rayons de la planète '
                                   '(échelle logarithmique) : plus on passe près, plus la trajectoire tourne.',
                                   'Distance from the planet’s centre to the closest point, in planet radii '
                                   '(logarithmic scale): the closer the pass, the more the trajectory turns.'),
    'anim_gravityassist_angle': ('Direction d’arrivée', 'Arrival direction'),
    'anim_gravityassist_angle_aide': ('Direction de v∞ à l’arrivée, comptée depuis le sens du mouvement de la planète '
                                      '(0° : la sonde la rattrape par l’arrière… dans le même sens ; 180° : elle vient '
                                      'à sa rencontre).',
                                      'Direction of v∞ on arrival, measured from the direction of the planet’s motion '
                                      '(0°: moving the same way as the planet; 180°: coming head-on).'),
    'anim_gravityassist_cote': ('Passage', 'Pass'),
    'anim_gravityassist_cote_aide': ('Côté de la planète où passe la sonde : derrière elle (par rapport à son '
                                     'mouvement), la vitesse relative est tournée vers l’avant ; devant elle, vers '
                                     'l’arrière.',
                                     'Side of the planet the probe passes: behind it (relative to its motion), the '
                                     'relative velocity is turned forwards; in front of it, backwards.'),
    'anim_gravityassist_derriere': ('derrière la planète', 'behind the planet'),
    'anim_gravityassist_devant': ('devant la planète', 'in front of the planet'),
    'anim_gravityassist_soleil': ('Orbites autour du Soleil', 'Orbits around the Sun'),
    'anim_gravityassist_soleil_aide': ('Orbite de la sonde autour du Soleil avant le survol (pointillé bleu) et après '
                                       '(trait rouge).',
                                       'Orbit of the probe around the Sun before the flyby (dotted blue) and after '
                                       '(solid red).'),
    'anim_gravityassist_t_planete': ('Vu de la planète : une hyperbole', 'Seen from the planet: a hyperbola'),
    'anim_gravityassist_t_vitesses': ('Vu du Soleil : v = V + v∞', 'Seen from the Sun: v = V + v∞'),
    'anim_gravityassist_t_soleil': ('Orbites autour du Soleil, avant et après', 'Orbits around the Sun, before and '
                                    'after'),
    'anim_gravityassist_mouvement': ('mouvement de la planète', 'motion of the planet'),
    'anim_gravityassist_vers_soleil': ('vers le Soleil', 'towards the Sun'),
    'anim_gravityassist_e_in': ('avant', 'before'),
    'anim_gravityassist_e_out': ('après', 'after'),
    'anim_gravityassist_cache': ('(orbites masquées)', '(orbits hidden)'),
    'anim_gravityassist_legende_soleil': ('bleu : avant ; rouge : après', 'blue: before; red: after'),
    'anim_gravityassist_v_V': ('Vitesse V de la planète', 'Planet speed V'),
    'anim_gravityassist_v_rp': ('Altitude au plus près', 'Closest altitude'),
    'anim_gravityassist_v_delta': ('Déviation δ = 2 arcsin(1/(1 + rₚv∞²/GM))', 'Deflection δ = 2 arcsin(1/(1 + '
                                   'rₚv∞²/GM))'),
    'anim_gravityassist_v_peri': ('Vitesse au plus près', 'Speed at closest approach'),
    'anim_gravityassist_v_dv': ('Variation de la vitesse 2 v∞ sin(δ/2)', 'Change of velocity 2 v∞ sin(δ/2)'),
    'anim_gravityassist_v_avant_apres': ('Vitesse autour du Soleil, avant → après', 'Speed around the Sun, before → '
                                         'after'),
    'anim_gravityassist_v_gain': ('Gain', 'Gain'),
    'anim_gravityassist_v_avant': ('Orbite avant le survol', 'Orbit before the flyby'),
    'anim_gravityassist_v_apres': ('Orbite après le survol', 'Orbit after the flyby'),
    'anim_gravityassist_orbite': ('de {q} à {Q} ua du Soleil', 'from {q} to {Q} au from the Sun'),
    'anim_gravityassist_liberee': ('libérée : quitte le Système solaire', 'escaping: leaves the Solar System'),

    # ================================================================ Le cratère d'impact
    'anim_impactcrater_exemple': ('Exemple', 'Example'),
    'anim_impactcrater_exemple_aide': ('Un cas tout prêt ; on peut ensuite changer chaque réglage.',
                                       'A ready-made case; you can then change each setting.'),
    'anim_impactcrater_x_libre': ('(réglage libre)', '(free setting)'),
    'anim_impactcrater_x_cours': ('Le cas du cours : 1,5 km à 20 km·s⁻¹', 'The course example: 1.5 km at 20 km·s⁻¹'),
    'anim_impactcrater_x_meteor_crater': ('Météorite de fer de 50 m (Meteor Crater, Arizona)',
                                          '50 m iron meteorite (Meteor Crater, Arizona)'),
    'anim_impactcrater_x_chicxulub': ('Astéroïde de 10 km (Chicxulub, fin des dinosaures)',
                                      '10 km asteroid (Chicxulub, end of the dinosaurs)'),
    'anim_impactcrater_L': ('Diamètre de l’impacteur L', 'Impactor diameter L'),
    'anim_impactcrater_L_aide': ('Diamètre de l’astéroïde ou de la comète (échelle logarithmique).',
                                 'Diameter of the asteroid or comet (logarithmic scale).'),
    'anim_impactcrater_v': ('Vitesse d’impact v', 'Impact speed v'),
    'anim_impactcrater_v_aide': ('Au moins 11,2 km·s⁻¹ (vitesse de libération de la Terre), au plus 72 km·s⁻¹ (comète '
                                 'rétrograde de face) ; une vingtaine de km·s⁻¹ en moyenne pour un astéroïde.',
                                 'At least 11.2 km·s⁻¹ (Earth’s escape speed), at most 72 km·s⁻¹ (head-on retrograde '
                                 'comet); about twenty km·s⁻¹ on average for an asteroid.'),
    'anim_impactcrater_theta': ('Angle avec le sol θ', 'Angle to the ground θ'),
    'anim_impactcrater_theta_aide': ('90° : chute verticale ; l’angle le plus probable est 45°. Le cratère varie '
                                     'comme ∛(sin θ).',
                                     '90°: vertical fall; the most likely angle is 45°. The crater scales as ∛(sin θ).'),
    'anim_impactcrater_impacteur': ('Impacteur', 'Impactor'),
    'anim_impactcrater_impacteur_aide': ('Nature, donc densité, de l’impacteur.', 'Nature, hence density, of the '
                                         'impactor.'),
    'anim_impactcrater_i_glace': ('glace (comète), 1 000 kg·m⁻³', 'ice (comet), 1,000 kg·m⁻³'),
    'anim_impactcrater_i_poreux': ('roche poreuse, 1 500 kg·m⁻³', 'porous rock, 1,500 kg·m⁻³'),
    'anim_impactcrater_i_rocheux': ('roche dense, 3 000 kg·m⁻³', 'dense rock, 3,000 kg·m⁻³'),
    'anim_impactcrater_i_fer': ('fer, 8 000 kg·m⁻³', 'iron, 8,000 kg·m⁻³'),
    'anim_impactcrater_cible': ('Sol', 'Ground'),
    'anim_impactcrater_cible_aide': ('Roche de la cible (densité).', 'Target rock (density).'),
    'anim_impactcrater_c_sedimentaire': ('roches sédimentaires, 2 500 kg·m⁻³', 'sedimentary rock, 2,500 kg·m⁻³'),
    'anim_impactcrater_c_cristalline': ('roches cristallines, 2 750 kg·m⁻³', 'crystalline rock, 2,750 kg·m⁻³'),
    'anim_impactcrater_t_coupe': ('Coupe du cratère (à l’échelle)', 'Cross-section of the crater (to scale)'),
    'anim_impactcrater_t_graphe': ('Diamètre final selon la taille de l’impacteur', 'Final diameter versus impactor '
                                   'size'),
    'anim_impactcrater_axe_L': ('L (m)', 'L (m)'),
    'anim_impactcrater_axe_D': ('D (km)', 'D (km)'),
    'anim_impactcrater_transition': ('simple ↓ complexe ↑', 'simple ↓ complex ↑'),
    'anim_impactcrater_cote': ('D = {d}', 'D = {d}'),
    'anim_impactcrater_echelle': ('pointillé : cavité transitoire', 'dotted: transient cavity'),
    'anim_impactcrater_v_masse': ('Masse de l’impacteur', 'Impactor mass'),
    'anim_impactcrater_v_energie': ('Énergie ½ m v²', 'Energy ½ m v²'),
    'anim_impactcrater_energie': ('{j} J = {mt} Mt de TNT', '{j} J = {mt} Mt of TNT'),
    'anim_impactcrater_v_transitoire': ('Cavité transitoire (diamètre × profondeur)', 'Transient cavity (diameter × '
                                        'depth)'),
    'anim_impactcrater_v_final': ('Diamètre du cratère final', 'Final crater diameter'),
    'anim_impactcrater_v_profondeur': ('Profondeur du cratère final', 'Final crater depth'),
    'anim_impactcrater_v_genre': ('Forme', 'Shape'),
    'anim_impactcrater_g_simple': ('cratère simple (cuvette, au fond une lentille de brèche)',
                                   'simple crater (bowl, with a breccia lens at the bottom)'),
    'anim_impactcrater_g_complexe': ('cratère complexe (fond plat, piton central, bords effondrés en terrasses)',
                                     'complex crater (flat floor, central peak, rim collapsed into terraces)'),
    'anim_impactcrater_v_rapport': ('Diamètre du cratère / diamètre de l’impacteur', 'Crater diameter / impactor '
                                    'diameter'),
    'anim_impactcrater_v_frequence': ('Un impact aussi énergique sur la Terre', 'An impact this energetic on Earth'),
    'anim_impactcrater_tous': ('tous les {n} ans en moyenne', 'every {n} years on average'),
    'anim_impactcrater_v_attention': ('Attention', 'Caution'),
    'anim_impactcrater_atmosphere': ('sous 200 m, l’atmosphère freine et fragmente l’impacteur (non modélisé ici)',
                                     'below 200 m, the atmosphere slows down and breaks up the impactor (not '
                                     'modelled here)'),
    # ================================================================ Rotation synchrone et libration
    'anim_libration_e': ('Excentricité de l’orbite e', 'Orbital eccentricity e'),
    'anim_libration_e_aide': ('0,0549 pour la Lune ; on peut l’exagérer pour mieux voir l’effet : la Lune va plus vite '
                              'près de la Terre, alors que sa rotation reste uniforme.',
                              '0.0549 for the Moon; it can be exaggerated to see the effect better: the Moon moves '
                              'faster near the Earth, while its rotation stays uniform.'),
    'anim_libration_i': ('Inclinaison de l’équateur lunaire I', 'Tilt of the lunar equator I'),
    'anim_libration_i_aide': ('Angle entre l’équateur de la Lune et le plan de son orbite (6,68°) : on voit tour à tour '
                              'un peu au-delà du pôle nord et du pôle sud.',
                              'Angle between the Moon’s equator and its orbital plane (6.68°): we see in turn a little '
                              'beyond the north pole and the south pole.'),
    'anim_libration_varpi': ('Angle nœud – périgée ϖ', 'Node – perigee angle ϖ'),
    'anim_libration_varpi_aide': ('Angle entre la ligne des nœuds de l’équateur lunaire et le périgée ; il fait le tour '
                                  'en quelques années, ce qui change la forme de la courbe de libration.',
                                  'Angle between the line of nodes of the lunar equator and the perigee; it goes '
                                  'round in a few years, which changes the shape of the libration curve.'),
    'anim_libration_rotation': ('Rotation de la Lune', 'Rotation of the Moon'),
    'anim_libration_rotation_aide': ('Synchrone (un tour en un mois sidéral, comme la vraie Lune, freinée par les marées) '
                                     'ou aucune, pour comparer : on verrait alors toute la Lune en un mois.',
                                     'Synchronous (one turn per sidereal month, like the real Moon, braked by the tides) '
                                     'or none, to compare: we would then see the whole Moon within a month.'),
    'anim_libration_r_synchrone': ('synchrone', 'synchronous'),
    'anim_libration_r_aucune': ('aucune (pour comparer)', 'none (to compare)'),
    'anim_libration_diurne': ('Libration diurne', 'Diurnal libration'),
    'anim_libration_diurne_aide': ('Un observateur à la surface de la Terre voit la Lune d’un point déplacé de jusqu’à un '
                                   'rayon terrestre : environ 0,95° de plus sur les bords (au lever et au coucher).',
                                   'An observer on the Earth’s surface sees the Moon from a point shifted by up to one '
                                   'Earth radius: about 0.95° more at the edges (at moonrise and moonset).'),
    'anim_libration_grille': ('Méridiens et parallèles', 'Meridians and parallels'),
    'anim_libration_grille_aide': ('Grille tous les 30° ; en jaune le méridien origine, en bleu les méridiens ±90° (le '
                                   'bord de la Lune sans libration).',
                                   'Grid every 30°; in yellow the prime meridian, in blue the ±90° meridians (the edge '
                                   'of the Moon without libration).'),
    'anim_libration_t_lune': ('La Lune vue de la Terre', 'The Moon seen from the Earth'),
    'anim_libration_t_orbite': ('L’orbite vue de dessus', 'The orbit seen from above'),
    'anim_libration_t_courbe': ('Libration au fil du mois', 'Libration over the month'),
    'anim_libration_legende_lune': ('nord en haut, est lunaire à droite', 'north up, lunar east to the right'),
    'anim_libration_legende_orbite': ('jaune : méridien origine (Lune agrandie)', 'yellow: prime meridian (Moon '
                                      'enlarged)'),
    'anim_libration_axe_l': ('l (°)', 'l (°)'),
    'anim_libration_axe_b': ('b (°)', 'b (°)'),
    'anim_libration_f_crisium': ('mer des Crises', 'Mare Crisium'),
    'anim_libration_f_tycho': ('Tycho', 'Tycho'),
    'anim_libration_f_copernic': ('Copernic', 'Copernicus'),
    'anim_libration_f_grimaldi': ('Grimaldi', 'Grimaldi'),
    'anim_libration_f_orientale': ('mer Orientale', 'Mare Orientale'),
    'anim_libration_v_jour': ('Depuis le périgée', 'Since perigee'),
    'anim_libration_jours': ('{n} jours', '{n} days'),
    'anim_libration_v_l': ('Libration en longitude l = ν − M', 'Libration in longitude l = ν − M'),
    'anim_libration_v_b': ('Libration en latitude b', 'Libration in latitude b'),
    'anim_libration_v_distance': ('Distance Terre-Lune', 'Earth-Moon distance'),
    'anim_libration_v_mois': ('Surface vue au moins une fois en un mois', 'Surface seen at least once in a month'),
    'anim_libration_v_annees': ('… au fil des années (ϖ tourne)', '… over the years (ϖ turns)'),
    'anim_libration_v_diurne': ('Libration diurne arcsin(R⊕/d)', 'Diurnal libration arcsin(R⊕/d)'),
    # ================================================================ La précession des équinoxes
    'anim_precession_annee': ('Année', 'Year'),
    'anim_precession_annee_aide': ('Année (numérotation astronomique : l’an 0 est l’an 1 av. J.-C.). En lecture, le '
                                   'temps défile de mille ans par seconde.',
                                   'Year (astronomical numbering: year 0 is 1 BC). When playing, time runs at a '
                                   'thousand years per second.'),
    'anim_precession_noms': ('Noms des étoiles', 'Star names'),
    'anim_precession_noms_aide': ('Polaris, Kochab, Thuban, Véga, Deneb, Alderamin, Errai… : les « étoiles polaires » '
                                  'successives.',
                                  'Polaris, Kochab, Thuban, Vega, Deneb, Alderamin, Errai…: the successive “pole '
                                  'stars”.'),
    'anim_precession_dates': ('Dates sur le cercle du pôle', 'Dates on the pole circle'),
    'anim_precession_dates_aide': ('Position du pôle céleste tous les 2 000 ans.',
                                   'Position of the celestial pole every 2,000 years.'),
    'anim_precession_t_carte': ('Le ciel autour du pôle de l’écliptique', 'The sky around the ecliptic pole'),
    'anim_precession_t_zodiaque': ('Le point vernal recule le long du zodiaque', 'The vernal point moves back along '
                                   'the zodiac'),
    'anim_precession_t_terre': ('L’axe de la Terre décrit un cône', 'The Earth’s axis sweeps a cone'),
    'anim_precession_pole_ecl': ('pôle de l’écliptique', 'ecliptic pole'),
    'anim_precession_pole': ('pôle céleste', 'celestial pole'),
    'anim_precession_legende_carte': ('pointillé : cercle de 23,44° que parcourt le pôle ; rouge : 10° autour du pôle',
                                      'dotted: 23.44° circle the pole travels; red: 10° around the pole'),
    'anim_precession_gamma': ('équinoxe de mars', 'March equinox'),
    'anim_precession_legende_zodiaque': ('limites des constellations de l’UAI le long de l’écliptique',
                                         'IAU constellation boundaries along the ecliptic'),
    'anim_precession_normale': ('perpendiculaire à l’écliptique', 'perpendicular to the ecliptic'),
    'anim_precession_axe': ('axe de rotation', 'rotation axis'),
    'anim_precession_av_jc': ('{a} ({b} av. J.-C.)', '{a} ({b} BC)'),
    'anim_precession_v_annee': ('Année', 'Year'),
    'anim_precession_v_periode': ('Précession', 'Precession'),
    'anim_precession_periode': ('un tour en {p} ans ({v}″ par an)', 'one turn in {p} years ({v}″ per year)'),
    'anim_precession_v_decalage': ('Recul du point vernal depuis l’an 2000', 'Shift of the vernal point since 2000'),
    'anim_precession_v_polaire': ('Étoile brillante la plus proche du pôle', 'Bright star closest to the pole'),
    'anim_precession_a': ('{e}, à {d}', '{e}, {d} away'),
    'anim_precession_v_polaris': ('Distance de Polaris au pôle', 'Distance of Polaris from the pole'),
    'anim_precession_v_vega': ('Déclinaison de Véga', 'Declination of Vega'),
    'anim_precession_v_equinoxe': ('À l’équinoxe de mars, le Soleil est devant', 'At the March equinox, the Sun is in '
                                   'front of'),
    'anim_precession_v_suivante': ('Constellation suivante', 'Next constellation'),
    'anim_precession_vers': ('{c}, à partir de {a}', '{c}, from {a}'),
    'anim_precession_e_polaris': ('Polaris', 'Polaris'),
    'anim_precession_e_vega': ('Véga', 'Vega'),
    'anim_precession_e_thuban': ('Thuban', 'Thuban'),
    'anim_precession_e_deneb': ('Deneb', 'Deneb'),
    'anim_precession_e_kochab': ('Kochab', 'Kochab'),
    'anim_precession_e_alderamin': ('Alderamin', 'Alderamin'),
    'anim_precession_e_errai': ('Errai', 'Errai'),
    'anim_precession_e_iota_her': ('ι Herculis', 'ι Herculis'),
    'anim_precession_e_delta_cyg': ('δ Cygni', 'δ Cygni'),
    'anim_precession_e_capella': ('Capella', 'Capella'),
    # ================================================================ Résonances et chaos
    'anim_resonances_cas': ('Astéroïde', 'Asteroid'),
    'anim_resonances_cas_aide': ('Un cas tout prêt (demi-grand axe, excentricité, position par rapport à Jupiter au '
                                 'départ) ; chaque réglage peut ensuite être changé.',
                                 'A ready-made case (semi-major axis, eccentricity, position relative to Jupiter at '
                                 'the start); each setting can then be changed.'),
    'anim_resonances_c_kirkwood': ('Dans la lacune de Kirkwood 3:1 (2,50 ua)', 'In the 3:1 Kirkwood gap (2.50 au)'),
    'anim_resonances_c_ceinture': ('Ceinture principale, hors résonance (2,30 ua)', 'Main belt, off resonance (2.30 '
                                   'au)'),
    'anim_resonances_c_hilda': ('Hilda, résonance 3:2 (3,97 ua)', 'Hilda, 3:2 resonance (3.97 au)'),
    'anim_resonances_c_troyen': ('Troyen, résonance 1:1 (devant Jupiter, en L4)', 'Trojan, 1:1 resonance (ahead of '
                                 'Jupiter, at L4)'),
    'anim_resonances_c_deux_un': ('Lacune 2:1 (3,28 ua)', '2:1 gap (3.28 au)'),
    'anim_resonances_c_comete': ('Comète qui croise l’orbite de Jupiter', 'Comet crossing Jupiter’s orbit'),
    'anim_resonances_a': ('Demi-grand axe a', 'Semi-major axis a'),
    'anim_resonances_a_aide': ('Demi-grand axe de départ, autour du Soleil.', 'Starting semi-major axis, around the '
                               'Sun.'),
    'anim_resonances_e': ('Excentricité e', 'Eccentricity e'),
    'anim_resonances_e_aide': ('Excentricité de départ ; l’astéroïde part de son périhélie.',
                               'Starting eccentricity; the asteroid starts from its perihelion.'),
    'anim_resonances_phi': ('Angle avec Jupiter φ₀', 'Angle from Jupiter φ₀'),
    'anim_resonances_phi_aide': ('Angle, vu du Soleil, entre Jupiter et l’astéroïde au départ.',
                                 'Angle, seen from the Sun, between Jupiter and the asteroid at the start.'),
    'anim_resonances_masse': ('Masse de Jupiter', 'Mass of Jupiter'),
    'anim_resonances_masse_aide': ('Réelle, ou dix fois plus grande pour voir plus vite les effets de Jupiter.',
                                   'Real, or ten times larger to see Jupiter’s effects sooner.'),
    'anim_resonances_m_reelle': ('réelle', 'real'),
    'anim_resonances_m_x10': ('× 10', '× 10'),
    'anim_resonances_repere': ('Repère', 'Frame'),
    'anim_resonances_repere_aide': ('Tournant avec Jupiter (une orbite en résonance y dessine une figure fermée) ou fixe.',
                                    'Rotating with Jupiter (a resonant orbit draws a closed figure in it) or fixed.'),
    'anim_resonances_r_tournant': ('tournant avec Jupiter', 'rotating with Jupiter'),
    'anim_resonances_r_fixe': ('fixe', 'fixed'),
    'anim_resonances_jumeau': ('Jumeau', 'Twin'),
    'anim_resonances_jumeau_aide': ('Un second astéroïde lâché 78 km plus loin (10⁻⁷ fois la distance de Jupiter), en '
                                    'bleu.',
                                    'A second asteroid released 78 km away (10⁻⁷ times Jupiter’s distance), in blue.'),
    'anim_resonances_relancer': ('Relancer', 'Restart'),
    'anim_resonances_relancer_aide': ('Repart des conditions initiales.', 'Starts again from the initial conditions.'),
    'anim_resonances_t_tournant': ('Dans le repère qui tourne avec Jupiter', 'In the frame rotating with Jupiter'),
    'anim_resonances_t_fixe': ('Dans un repère fixe', 'In a fixed frame'),
    'anim_resonances_t_a': ('Demi-grand axe au fil du temps', 'Semi-major axis over time'),
    'anim_resonances_t_ecart': ('Écart entre les deux jumeaux (échelle logarithmique)', 'Distance between the two '
                                'twins (logarithmic scale)'),
    'anim_resonances_axe_t': ('orbites de Jupiter', 'Jupiter orbits'),
    'anim_resonances_axe_a': ('a (ua)', 'a (au)'),
    'anim_resonances_axe_ecart': ('écart (ua)', 'distance (au)'),
    'anim_resonances_jupiter': ('Jupiter', 'Jupiter'),
    'anim_resonances_v_temps': ('Temps écoulé', 'Elapsed time'),
    'anim_resonances_temps': ('{n} orbites de Jupiter ({ans} ans)', '{n} Jupiter orbits ({ans} years)'),
    'anim_resonances_v_a': ('Demi-grand axe a', 'Semi-major axis a'),
    'anim_resonances_v_e': ('Excentricité e', 'Eccentricity e'),
    'anim_resonances_v_rapport': ('Période de Jupiter / période de l’astéroïde', 'Jupiter’s period / the asteroid’s '
                                  'period'),
    'anim_resonances_v_proche': ('Résonance la plus proche', 'Nearest resonance'),
    'anim_resonances_proche': ('{p}:{q} à {a} ua (écart {d} %)', '{p}:{q} at {a} au ({d}% away)'),
    'anim_resonances_ejecte': ('orbite ouverte : éjecté par Jupiter', 'open orbit: ejected by Jupiter'),
    'anim_resonances_v_ecart': ('Écart entre les jumeaux', 'Distance between the twins'),
    'anim_resonances_ecart': ('{km} km (× {f} depuis le départ)', '{km} km (× {f} since the start)'),
    'anim_resonances_v_etat': ('État', 'State'),
    'anim_resonances_collision': ('collision avec Jupiter ou le Soleil', 'collision with Jupiter or the Sun'),
    # ================================================================ La limite de Roche
    'anim_roche_systeme': ('Système', 'System'),
    'anim_roche_systeme_aide': ('Planète et satellite : règle le rapport des densités et la distance de départ.',
                                'Planet and satellite: sets the density ratio and the starting distance.'),
    'anim_roche_s_terre_lune': ('Terre et Lune (rapprochée : elle est à 60 R)', 'Earth and Moon (brought closer: it is '
                                'at 60 R)'),
    'anim_roche_s_mars_phobos': ('Mars et Phobos (à 2,76 R, il descend)', 'Mars and Phobos (at 2.76 R, it is '
                                 'spiralling in)'),
    'anim_roche_s_saturne_glace': ('Saturne et un bloc de glace (à la distance de Mimas)', 'Saturn and a block of ice '
                                   '(at Mimas’s distance)'),
    'anim_roche_s_jupiter_comete': ('Jupiter et une comète (ρ ≈ 500 kg·m⁻³)', 'Jupiter and a comet (ρ ≈ 500 kg·m⁻³)'),
    'anim_roche_rapport': ('Rapport des densités ρₚ/ρₛ', 'Density ratio ρₚ/ρₛ'),
    'anim_roche_rapport_aide': ('Densité de la planète divisée par celle du satellite (échelle logarithmique) : un '
                                'satellite peu dense se disloque plus loin.',
                                'Density of the planet divided by that of the satellite (logarithmic scale): a '
                                'low-density satellite breaks up further out.'),
    'anim_roche_d0': ('Distance de départ', 'Starting distance'),
    'anim_roche_d0_aide': ('Distance du satellite au centre de la planète, en rayons de la planète.',
                           'Distance of the satellite from the planet’s centre, in planet radii.'),
    'anim_roche_modele': ('Satellite', 'Satellite'),
    'anim_roche_modele_aide': ('Fluide (il s’allonge sous la marée : limite 2,44 R ∛(ρₚ/ρₛ)) ou rigide, sans cohésion '
                               '(sphère en rotation synchrone : 1,44 R ∛(ρₚ/ρₛ)).',
                               'Fluid (the tide elongates it: limit 2.44 R ∛(ρₚ/ρₛ)) or rigid, without cohesion '
                               '(sphere in synchronous rotation: 1.44 R ∛(ρₚ/ρₛ)).'),
    'anim_roche_m_fluide': ('fluide', 'fluid'),
    'anim_roche_m_rigide': ('rigide', 'rigid'),
    'anim_roche_descente': ('Le satellite descend', 'The satellite spirals in'),
    'anim_roche_descente_aide': ('Son orbite rétrécit peu à peu, comme celle de Phobos freinée par les marées (bien plus '
                                 'vite ici : en réalité, des dizaines de millions d’années).',
                                 'Its orbit slowly shrinks, like Phobos’s, braked by the tides (much faster here: in '
                                 'reality, tens of millions of years).'),
    'anim_roche_relancer': ('Relancer', 'Restart'),
    'anim_roche_relancer_aide': ('Repart de la distance de départ, satellite entier.', 'Starts again from the starting '
                                 'distance, with a whole satellite.'),
    'anim_roche_t_vue': ('Le satellite et sa planète', 'The satellite and its planet'),
    'anim_roche_t_gros_plan': ('Gros plan : la marée étire le satellite', 'Close-up: the tide stretches the satellite'),
    'anim_roche_t_graphe': ('Étirement de marée / gravité propre', 'Tidal stretching / self-gravity'),
    'anim_roche_legende_vue': ('pointillés : limites fluide (rouge) et rigide (bleu)', 'dotted: fluid (red) and rigid '
                               '(blue) limits'),
    'anim_roche_legende_gros_plan': ('la planète est à gauche ; flèches : marée', 'the planet is to the left; arrows: '
                                     'tide'),
    'anim_roche_plus_de_satellite': ('satellite disloqué', 'satellite broken up'),
    'anim_roche_axe_d': ('d (R)', 'd (R)'),
    'anim_roche_axe_rapport': ('marée / gravité', 'tide / gravity'),
    'anim_roche_rigide_court': ('rigide', 'rigid'),
    'anim_roche_fluide_court': ('fluide', 'fluid'),
    'anim_roche_r_km': ('{r} R ({km} km)', '{r} R ({km} km)'),
    'anim_roche_v_fluide': ('Limite de Roche, satellite fluide 2,44 R ∛(ρₚ/ρₛ)', 'Roche limit, fluid satellite '
                            '2.44 R ∛(ρₚ/ρₛ)'),
    'anim_roche_v_rigide': ('Limite, satellite rigide ∛3 R ∛(ρₚ/ρₛ)', 'Limit, rigid satellite ∛3 R ∛(ρₚ/ρₛ)'),
    'anim_roche_v_d': ('Distance du satellite', 'Distance of the satellite'),
    'anim_roche_v_etirement': ('Étirement de marée / gravité propre 3 (ρₚ/ρₛ)(R/d)³', 'Tidal stretching / '
                               'self-gravity 3 (ρₚ/ρₛ)(R/d)³'),
    'anim_roche_v_allongement': ('Allongement d’un satellite fluide 15/4 (ρₚ/ρₛ)(R/d)³', 'Elongation of a fluid '
                                 'satellite 15/4 (ρₚ/ρₛ)(R/d)³'),
    'anim_roche_v_etat': ('État', 'State'),
    'anim_roche_intact': ('entier', 'whole'),
    'anim_roche_disloque': ('disloqué : {n} grains sur {m} en anneau', 'broken up: {n} grains out of {m} in a ring'),
}
