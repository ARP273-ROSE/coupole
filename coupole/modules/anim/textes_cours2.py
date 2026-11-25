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
    'anim_impactcrater_i_glace': ('glace (comète), 1 000 kg·m⁻³', 'ice (comet), 1,000 kg·m⁻³'),
    'anim_impactcrater_i_poreux': ('roche poreuse, 1 500 kg·m⁻³', 'porous rock, 1,500 kg·m⁻³'),
    'anim_impactcrater_i_rocheux': ('roche dense, 3 000 kg·m⁻³', 'dense rock, 3,000 kg·m⁻³'),
    'anim_impactcrater_i_fer': ('fer, 8 000 kg·m⁻³', 'iron, 8,000 kg·m⁻³'),
    'anim_impactcrater_cible': ('Sol', 'Ground'),
    'anim_impactcrater_cible_aide': ('Roche de la cible (densité).', 'Target rock (density).'),
    'anim_impactcrater_c_sedimentaire': ('roches sédimentaires, 2 500 kg·m⁻³', 'sedimentary rock, 2,500 kg·m⁻³'),
    'anim_impactcrater_c_cristalline': ('roches cristallines, 2 750 kg·m⁻³', 'crystalline rock, 2,750 kg·m⁻³'),
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
}
