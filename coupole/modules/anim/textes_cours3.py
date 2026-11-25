"""Textes FR/EN des animations de cours ajoutées en dernier dans la 0.12.0 (précession séculaire d'une orbite,
phénomènes mutuels des satellites galiléens, traînées de météoroïdes).  Fusionnés dans ``textes.TEXTES`` (et exportés
tels quels vers Coupole Web)."""

ANIM_COURS_3 = {
    # ================================================================ Précession séculaire d'une orbite
    'anim_secularprecession_objet': ('Astéroïde', 'Asteroid'),
    'anim_secularprecession_objet_aide': ('Un géocroiseur réel (éléments de la base SBDB du JPL, époque 2026, '
                                          'arrondis) ; chaque élément peut ensuite être changé.',
                                          'A real near-Earth asteroid (elements from JPL’s SBDB, epoch 2026, rounded); '
                                          'each element can then be changed.'),
    'anim_secularprecession_o_apollo': ('(1862) Apollo', '(1862) Apollo'),
    'anim_secularprecession_o_icare': ('(1566) Icare', '(1566) Icarus'),
    'anim_secularprecession_o_phaethon': ('(3200) Phaéton (Géminides)', '(3200) Phaethon (Geminids)'),
    'anim_secularprecession_o_adonis': ('(2101) Adonis', '(2101) Adonis'),
    'anim_secularprecession_o_toutatis': ('(4179) Toutatis', '(4179) Toutatis'),
    'anim_secularprecession_a': ('Demi-grand axe a', 'Semi-major axis a'),
    'anim_secularprecession_a_aide': ('Il ne change pas en moyenne (théorie séculaire) ; il fixe la vitesse de la '
                                      'précession : plus l’astéroïde est près de Jupiter, plus elle est rapide.',
                                      'It does not change on average (secular theory); it sets the precession rate: '
                                      'the closer the asteroid to Jupiter, the faster it is.'),
    'anim_secularprecession_e': ('Excentricité e', 'Eccentricity e'),
    'anim_secularprecession_e_aide': ('Constante dans ce modèle ; l’orbite coupe celle de la Terre si son périhélie '
                                      'q = a(1 − e) est sous 1 ua et son aphélie Q = a(1 + e) au-dessus.',
                                      'Constant in this model; the orbit can cross the Earth’s if its perihelion '
                                      'q = a(1 − e) is below 1 au and its aphelion Q = a(1 + e) above.'),
    'anim_secularprecession_i': ('Inclinaison i', 'Inclination i'),
    'anim_secularprecession_i_aide': ('Angle entre le plan de l’orbite et l’écliptique (constant dans ce modèle) : '
                                      'l’orbite ne perce l’écliptique qu’aux deux nœuds.',
                                      'Angle between the orbital plane and the ecliptic (constant in this model): '
                                      'the orbit pierces the ecliptic only at the two nodes.'),
    'anim_secularprecession_o0': ('Longitude du nœud Ω en 2026', 'Longitude of the node Ω in 2026'),
    'anim_secularprecession_o0_aide': ('Direction du nœud ascendant aujourd’hui ; elle recule ensuite de A par an.',
                                       'Direction of the ascending node today; it then moves back by A per year.'),
    'anim_secularprecession_w0': ('Argument du périhélie ω en 2026', 'Argument of perihelion ω in 2026'),
    'anim_secularprecession_w0_aide': ('Angle du nœud ascendant au périhélie aujourd’hui ; il tourne ensuite de 2A '
                                       'par an et décide où sont les nœuds.',
                                       'Angle from the ascending node to the perihelion today; it then turns by 2A '
                                       'per year and decides where the nodes lie.'),
    'anim_secularprecession_aujourdhui': ('Aujourd’hui', 'Today'),
    'anim_secularprecession_aujourdhui_aide': ('Revient en 2026.', 'Goes back to 2026.'),
    'anim_secularprecession_suivant': ('Croisement suivant', 'Next crossing'),
    'anim_secularprecession_suivant_aide': ('Avance jusqu’à la prochaine époque où un nœud est sur l’orbite de la '
                                            'Terre.', 'Moves on to the next epoch when a node lies on the Earth’s '
                                            'orbit.'),
    'anim_secularprecession_t_vue': ('L’orbite vue du pôle de l’écliptique', 'The orbit seen from the ecliptic pole'),
    'anim_secularprecession_t_noeuds': ('Distance des nœuds au Soleil', 'Distance of the nodes from the Sun'),
    'anim_secularprecession_t_moid': ('Distance minimale entre les orbites', 'Minimum distance between the orbits'),
    'anim_secularprecession_legende_vue': ('trait plein : au-dessus de l’écliptique ; bleu : Terre ; flèche : '
                                           'périhélie', 'solid: above the ecliptic; blue: Earth; arrow: perihelion'),
    'anim_secularprecession_axe_t': ('milliers d’années après 2026', 'thousand years after 2026'),
    'anim_secularprecession_axe_r': ('r (ua)', 'r (au)'),
    'anim_secularprecession_axe_moid': ('MOID (ua)', 'MOID (au)'),
    'anim_secularprecession_terre': ('Terre', 'Earth'),
    'anim_secularprecession_pha': ('0,05 ua', '0.05 au'),
    'anim_secularprecession_deux': ('{a} ; {b}', '{a}; {b}'),
    'anim_secularprecession_ua': ('{x} ua', '{x} au'),
    'anim_secularprecession_an': ('an {an}', 'year {an}'),
    'anim_secularprecession_ans': ('{n} ans', '{n} years'),
    'anim_secularprecession_sec_an': ('{x}″ par an', '{x}″ per year'),
    'anim_secularprecession_n_asc': ('nœud ascendant', 'ascending node'),
    'anim_secularprecession_n_desc': ('nœud descendant', 'descending node'),
    'anim_secularprecession_prochain': ('an {an} ({noeud})', 'year {an} ({noeud})'),
    'anim_secularprecession_jamais': ('jamais : q > 1 ua ou Q < 1 ua', 'never: q > 1 au or Q < 1 au'),
    'anim_secularprecession_v_date': ('Date', 'Date'),
    'anim_secularprecession_v_vitesse': ('Précession A = (n/4) Σ (m/M☉) α² b(α)', 'Precession A = (n/4) Σ (m/M☉) α² '
                                         'b(α)'),
    'anim_secularprecession_v_tour': ('Tour de ϖ (et de Ω, à l’envers) 2π/A', 'Turn of ϖ (and of Ω, backwards) 2π/A'),
    'anim_secularprecession_v_tour_w': ('Tour de ω = ϖ − Ω : π/A', 'Turn of ω = ϖ − Ω: π/A'),
    'anim_secularprecession_v_angles': ('ω ; Ω', 'ω; Ω'),
    'anim_secularprecession_v_noeuds': ('Nœuds r☊ ; r☋ = a(1 − e²)/(1 ± e cos ω)', 'Nodes r☊; r☋ = a(1 − e²)/(1 ± '
                                        'e cos ω)'),
    'anim_secularprecession_v_moid': ('Distance minimale à l’orbite terrestre (MOID)', 'Minimum distance to the '
                                      'Earth’s orbit (MOID)'),
    'anim_secularprecession_v_prochain': ('Prochain croisement', 'Next crossing'),
    # ================================================================ Phénomènes mutuels des satellites galiléens
    'anim_mutualevents_actif': ('Satellite actif', 'Active satellite'),
    'anim_mutualevents_actif_aide': ('Celui qui passe devant (occultation) ou qui fait de l’ombre (éclipse) : le plus '
                                     'proche de la Terre ou du Soleil au moment de la rencontre.',
                                     'The one passing in front (occultation) or casting the shadow (eclipse): the '
                                     'closer to the Earth or the Sun at the time of the encounter.'),
    'anim_mutualevents_passif': ('Satellite passif', 'Passive satellite'),
    'anim_mutualevents_passif_aide': ('Celui qui est caché ou éclipsé (s’il est le même que l’actif, on prend le '
                                      'suivant).', 'The one hidden or eclipsed (if it is the same as the active one, '
                                      'the next one is taken).'),
    'anim_mutualevents_s_io': ('Io', 'Io'),
    'anim_mutualevents_s_europe': ('Europe', 'Europa'),
    'anim_mutualevents_s_ganymede': ('Ganymède', 'Ganymede'),
    'anim_mutualevents_s_callisto': ('Callisto', 'Callisto'),
    'anim_mutualevents_genre': ('Phénomène', 'Event'),
    'anim_mutualevents_genre_aide': ('Occultation : vu de la Terre, l’actif passe devant le passif. Éclipse : vu du '
                                     'Soleil, il passe devant, et le passif entre dans son ombre (puis sa pénombre).',
                                     'Occultation: seen from the Earth, the active one passes in front of the passive '
                                     'one. Eclipse: seen from the Sun, it passes in front, and the passive one enters '
                                     'its shadow (and penumbra).'),
    'anim_mutualevents_g_occultation': ('occultation (O)', 'occultation (O)'),
    'anim_mutualevents_g_eclipse': ('éclipse (E)', 'eclipse (E)'),
    'anim_mutualevents_B': ('Latitude de la Terre et du Soleil B', 'Latitude of the Earth and the Sun B'),
    'anim_mutualevents_B_aide': ('Hauteur de la Terre (et du Soleil) au-dessus du plan des orbites, vue de Jupiter : '
                                 'elle varie de ± 3° en 12 ans et passe par 0 tous les six ans ; les phénomènes '
                                 'mutuels n’ont lieu que lorsqu’elle est petite.',
                                 'Height of the Earth (and the Sun) above the orbital plane, seen from Jupiter: it '
                                 'varies by ± 3° in 12 years and goes through 0 every six years; mutual events '
                                 'only happen when it is small.'),
    'anim_mutualevents_phase': ('Angle de phase φ', 'Phase angle φ'),
    'anim_mutualevents_phase_aide': ('Angle Soleil-Jupiter-Terre (11° au plus) : pour une éclipse, la Terre voit '
                                     'l’ombre de côté, les deux satellites séparés.',
                                     'Sun-Jupiter-Earth angle (11° at most): for an eclipse, the Earth sees the '
                                     'shadow from the side, the two satellites apart.'),
    'anim_mutualevents_fx': ('Lieu de la rencontre x₀', 'Place of the encounter x₀'),
    'anim_mutualevents_fx_aide': ('Position de la rencontre à l’est ou à l’ouest de Jupiter, en fraction du rayon de '
                                  'l’orbite intérieure : loin de Jupiter les deux vont presque dans le même sens, la '
                                  'rencontre est lente.', 'Position of the encounter east or west of Jupiter, as a '
                                  'fraction of the inner orbit’s radius: far from Jupiter both move almost the same '
                                  'way, the encounter is slow.'),
    'anim_mutualevents_t_ciel': ('Vu de la Terre (gros plan)', 'Seen from the Earth (close-up)'),
    'anim_mutualevents_t_systeme': ('Le système vu du nord', 'The system seen from the north'),
    'anim_mutualevents_t_courbe': ('Courbe de lumière de la paire', 'Light curve of the pair'),
    'anim_mutualevents_legende_ciel': ('éclipse : ombre (noire) et pénombre (grise)', 'eclipse: umbra (black) and '
                                       'penumbra (grey)'),
    'anim_mutualevents_terre': ('Terre', 'Earth'),
    'anim_mutualevents_soleil': ('Soleil', 'Sun'),
    'anim_mutualevents_axe_t': ('t (min)', 't (min)'),
    'anim_mutualevents_axe_f': ('éclat', 'brightness'),
    'anim_mutualevents_phrase_occultation': ('{a} occulte {p}', '{a} occults {p}'),
    'anim_mutualevents_phrase_eclipse': ('{a} éclipse {p}', '{a} eclipses {p}'),
    'anim_mutualevents_notation': ('{n} : {p}', '{n}: {p}'),
    'anim_mutualevents_pc': ('{x} %', '{x}%'),
    'anim_mutualevents_min': ('{n} min', '{n} min'),
    'anim_mutualevents_km': ('{n} km', '{n} km'),
    'anim_mutualevents_kms': ('{n} km·s⁻¹', '{n} km·s⁻¹'),
    'anim_mutualevents_baisse': ('{pc} % (Δm = {dm})', '{pc}% (Δm = {dm})'),
    'anim_mutualevents_rien': ('aucune : les disques ne se touchent pas', 'none: the discs do not touch'),
    'anim_mutualevents_v_phenomene': ('Phénomène', 'Event'),
    'anim_mutualevents_v_instant': ('Instant (0 : rencontre)', 'Time (0: encounter)'),
    'anim_mutualevents_v_eclat': ('Éclat de la paire', 'Brightness of the pair'),
    'anim_mutualevents_v_impact': ('Écart des centres à la rencontre (Y₁ − Y₂) sin B', 'Distance between centres at '
                                   'the encounter (Y₁ − Y₂) sin B'),
    'anim_mutualevents_v_vitesse': ('Vitesse relative sur le ciel', 'Relative speed on the sky'),
    'anim_mutualevents_v_duree': ('Durée', 'Duration'),
    'anim_mutualevents_v_baisse': ('Baisse d’éclat maximale', 'Largest drop in brightness'),
    'anim_mutualevents_v_blim': ('Phénomène possible si B est sous', 'Event possible if B is below'),
    # ================================================================ Traînées de météoroïdes
    'anim_meteoroidtrails_comete': ('Comète', 'Comet'),
    'anim_meteoroidtrails_comete_aide': ('Comète mère d’un essaim (éléments de la base SBDB du JPL, arrondis, gardés '
                                         'fixes) ; la comète fictive a l’orbite de 55P tournée pour que son nœud soit '
                                         'exactement sur l’orbite de la Terre.',
                                         'Parent comet of a shower (elements from JPL’s SBDB, rounded, kept fixed); the '
                                         'fictitious comet has 55P’s orbit, turned so that its node lies exactly on '
                                         'the Earth’s orbit.'),
    'anim_meteoroidtrails_c_tempel_tuttle': ('55P/Tempel-Tuttle (Léonides)', '55P/Tempel-Tuttle (Leonids)'),
    'anim_meteoroidtrails_c_swift_tuttle': ('109P/Swift-Tuttle (Perséides)', '109P/Swift-Tuttle (Perseids)'),
    'anim_meteoroidtrails_c_fictive': ('comète fictive (nœud sur l’orbite terrestre)', 'fictitious comet (node on '
                                       'the Earth’s orbit)'),
    'anim_meteoroidtrails_dv': ('Vitesse d’éjection Δv', 'Ejection speed Δv'),
    'anim_meteoroidtrails_dv_aide': ('Vitesse maximale des grains par rapport au noyau (tirées au hasard dans une '
                                     'boule) : quelques mètres par seconde pour des grains millimétriques.',
                                     'Largest speed of the grains relative to the nucleus (drawn at random in a ball): '
                                     'a few metres per second for millimetre grains.'),
    'anim_meteoroidtrails_taille': ('Taille des grains', 'Grain size'),
    'anim_meteoroidtrails_taille_aide': ('Plus un grain est petit, plus la lumière du Soleil le pousse '
                                         '(β = 5,7 × 10⁻⁵/(ρ s), ρ = 1 g·cm⁻³) : il suit une orbite plus grande, de '
                                         'plus longue période, et s’éloigne plus vite de la comète.',
                                         'The smaller a grain, the harder sunlight pushes it (β = 5.7 × 10⁻⁵/(ρ s), '
                                         'ρ = 1 g·cm⁻³): it follows a larger orbit, with a longer period, and drifts '
                                         'away from the comet faster.'),
    'anim_meteoroidtrails_t_cm': ('1 cm (β = 5,7 × 10⁻⁵)', '1 cm (β = 5.7 × 10⁻⁵)'),
    'anim_meteoroidtrails_t_mm': ('1 mm (β = 5,7 × 10⁻⁴)', '1 mm (β = 5.7 × 10⁻⁴)'),
    'anim_meteoroidtrails_t_dixieme': ('0,1 mm (β = 5,7 × 10⁻³)', '0.1 mm (β = 5.7 × 10⁻³)'),
    'anim_meteoroidtrails_cadrage': ('Vue', 'View'),
    'anim_meteoroidtrails_cadrage_aide': ('Près du Soleil (2 ua autour, là où la Terre croise l’essaim) ou toute '
                                          'l’orbite de la comète.', 'Near the Sun (2 au around, where the Earth '
                                          'crosses the stream) or the comet’s whole orbit.'),
    'anim_meteoroidtrails_v_interieur': ('près du Soleil', 'near the Sun'),
    'anim_meteoroidtrails_v_orbite': ('toute l’orbite', 'whole orbit'),
    'anim_meteoroidtrails_relancer': ('Relancer', 'Restart'),
    'anim_meteoroidtrails_relancer_aide': ('Revient à la première année suivie.', 'Goes back to the first year '
                                           'followed.'),
    'anim_meteoroidtrails_t_vue': ('Les traînées vues de dessus', 'The trails seen from above'),
    'anim_meteoroidtrails_t_diagramme': ('Au nœud cette année : écarts à la Terre', 'At the node this year: offsets '
                                         'from the Earth'),
    'anim_meteoroidtrails_t_activite': ('Grains rencontrés, année par année', 'Grains met, year by year'),
    'anim_meteoroidtrails_legende_vue': ('une couleur par passage ; blanc : la comète ; bleu : la Terre',
                                         'one colour per passage; white: the comet; blue: the Earth'),
    'anim_meteoroidtrails_axe_dt': ('Δt (jours)', 'Δt (days)'),
    'anim_meteoroidtrails_axe_dr': ('Δr (ua)', 'Δr (au)'),
    'anim_meteoroidtrails_axe_an': ('année', 'year'),
    'anim_meteoroidtrails_axe_n': ('grains', 'grains'),
    'anim_meteoroidtrails_e_leonides': ('Léonides (55P/Tempel-Tuttle)', 'Leonids (55P/Tempel-Tuttle)'),
    'anim_meteoroidtrails_e_perseides': ('Perséides (109P/Swift-Tuttle)', 'Perseids (109P/Swift-Tuttle)'),
    'anim_meteoroidtrails_e_fictif': ('essaim fictif', 'fictitious shower'),
    'anim_meteoroidtrails_ans': ('{n} ans', '{n} years'),
    'anim_meteoroidtrails_beta': ('{x} × 10⁻⁴', '{x} × 10⁻⁴'),
    'anim_meteoroidtrails_noeud': ('{r} ua (Δr = {d} ua)', '{r} au (Δr = {d} au)'),
    'anim_meteoroidtrails_max': ('{an} ({n} grains)', '{an} ({n} grains)'),
    'anim_meteoroidtrails_v_essaim': ('Essaim', 'Shower'),
    'anim_meteoroidtrails_v_date': ('Année', 'Year'),
    'anim_meteoroidtrails_v_periode': ('Période de la comète', 'Period of the comet'),
    'anim_meteoroidtrails_v_beta': ('Pression de radiation / gravité β', 'Radiation pressure / gravity β'),
    'anim_meteoroidtrails_v_lachees': ('Traînées lâchées', 'Trails released'),
    'anim_meteoroidtrails_v_noeud': ('Nœud de la comète, écart à l’orbite terrestre', 'Node of the comet, offset from '
                                     'the Earth’s orbit'),
    'anim_meteoroidtrails_v_terre': ('La Terre au nœud', 'The Earth at the node'),
    'anim_meteoroidtrails_v_filet': ('Grains rencontrés cette année (|Δr| < 0,01 ua, |Δt| < 10 j)', 'Grains met this '
                                     'year (|Δr| < 0.01 au, |Δt| < 10 d)'),
    'anim_meteoroidtrails_v_max': ('Année la plus riche', 'Richest year'),
}
