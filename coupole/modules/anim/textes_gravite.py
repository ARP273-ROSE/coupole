"""Textes FR/EN de l'animation « Gravité et orbites » (0.7.2), d'après la simulation PhET Gravity and Orbits du
projet PhET Interactive Simulations de l'University of Colorado Boulder : idée et fonctions reprises, code, dessins
et textes propres à Coupole (aucune partie de PhET).  Fusionnés dans ``textes.TEXTES`` (et exportés tels quels vers
Coupole Web)."""

ANIM_GRAVITE = {
    # ------------------------------------------------------------ réglages
    'anim_gravityorbits_scenario': ('Scénario', 'Scenario'),
    'anim_gravityorbits_scenario_aide': ('Corps en présence ; chacun part de son orbite (Soleil, Terre et Lune ensemble : '
                                         'positions et vitesses réelles du 1ᵉʳ janvier 2026).',
                                         'Bodies present; each starts on its orbit (Sun, Earth and Moon together: real '
                                         'positions and velocities on 1 January 2026).'),
    'anim_gravityorbits_sc_soleil_terre': ('Soleil et Terre', 'Sun and Earth'),
    'anim_gravityorbits_sc_soleil_terre_lune': ('Soleil, Terre et Lune', 'Sun, Earth and Moon'),
    'anim_gravityorbits_sc_terre_lune': ('Terre et Lune', 'Earth and Moon'),
    'anim_gravityorbits_sc_terre_iss': ('Terre et station spatiale (ISS)', 'Earth and space station (ISS)'),
    'anim_gravityorbits_sc_libre': ('Libre : Soleil, Terre, Lune et comète', 'Free: Sun, Earth, Moon and comet'),
    'anim_gravityorbits_mode': ('Vue', 'View'),
    'anim_gravityorbits_mode_aide': ('Modèle : astres agrandis (et distance Terre–Lune agrandie) pour être lisibles ; '
                                     'à l’échelle : tailles et distances réelles. On passe de l’une à l’autre en '
                                     'douceur.',
                                     'Model: bodies enlarged (and the Earth–Moon distance enlarged) to be readable; to '
                                     'scale: real sizes and distances. The view moves smoothly from one to the other.'),
    'anim_gravityorbits_mode_modele': ('Modèle', 'Model'),
    'anim_gravityorbits_mode_echelle': ('À l’échelle', 'To scale'),
    'anim_gravityorbits_masse_soleil': ('Masse du Soleil', 'Mass of the Sun'),
    'anim_gravityorbits_masse_soleil_aide': ('En masses solaires (1 M☉ = 1,988 × 10³⁰ kg).',
                                             'In solar masses (1 M☉ = 1.988 × 10³⁰ kg).'),
    'anim_gravityorbits_masse_terre': ('Masse de la Terre', 'Mass of the Earth'),
    'anim_gravityorbits_masse_terre_aide': ('En masses terrestres (1 M⊕ = 5,972 × 10²⁴ kg).',
                                            'In Earth masses (1 M⊕ = 5.972 × 10²⁴ kg).'),
    'anim_gravityorbits_masse_lune': ('Masse de la Lune', 'Mass of the Moon'),
    'anim_gravityorbits_masse_lune_aide': ('En masses lunaires (1 M☾ = 7,346 × 10²² kg).',
                                           'In lunar masses (1 M☾ = 7.346 × 10²² kg).'),
    'anim_gravityorbits_force': ('Force de gravité', 'Gravity force'),
    'anim_gravityorbits_force_aide': ('Flèches bleues : force de gravité totale sur chaque corps (longueur relative à '
                                      'celle du départ, propre à chaque corps).',
                                      'Blue arrows: total gravity force on each body (length relative to the start, '
                                      'for each body).'),
    'anim_gravityorbits_vecteurs_vitesse': ('Vecteur vitesse', 'Velocity vector'),
    'anim_gravityorbits_vecteurs_vitesse_aide': ('Flèches vertes : vitesse de chaque corps (même échelle pour tous) ; '
                                                 'tirer le bout d’une flèche change la vitesse.',
                                                 'Green arrows: velocity of each body (same scale for all); drag the '
                                                 'tip of an arrow to change the velocity.'),
    'anim_gravityorbits_traces': ('Trajectoires', 'Paths'),
    'anim_gravityorbits_traces_aide': ('Chemin parcouru par chaque corps.', 'Path followed by each body.'),
    'anim_gravityorbits_grille': ('Grille', 'Grid'),
    'anim_gravityorbits_grille_aide': ('Quadrillage ; la taille d’un carreau est écrite en bas à gauche.',
                                       'Grid; the size of a square is written at the bottom left.'),
    'anim_gravityorbits_ruban': ('Ruban de mesure', 'Measuring tape'),
    'anim_gravityorbits_ruban_aide': ('Glisser ses deux bouts : il mesure la vraie distance dans l’espace.',
                                      'Drag its two ends: it measures the real distance in space.'),
    'anim_gravityorbits_gravite': ('Gravité', 'Gravity'),
    'anim_gravityorbits_gravite_aide': ('Sans gravité, chaque corps file en ligne droite à vitesse constante (première '
                                        'loi de Newton).',
                                        'Without gravity, each body moves off in a straight line at constant speed '
                                        '(Newton’s first law).'),
    'anim_gravityorbits_lune_soleil': ('Lune vue du Soleil', 'Moon seen from the Sun'),
    'anim_gravityorbits_lune_soleil_aide': ('Encart : vraie trajectoire de la Lune autour du Soleil et sa courbure, '
                                            'toujours tournée vers le Soleil.',
                                            'Inset: the Moon’s real path around the Sun and its curvature, always '
                                            'turned towards the Sun.'),
    'anim_gravityorbits_pas': ('Pas', 'Step'),
    'anim_gravityorbits_pas_aide': ('Avancer d’un petit pas de temps.', 'Move forward by a small time step.'),
    'anim_gravityorbits_retour': ('Retour', 'Rewind'),
    'anim_gravityorbits_retour_aide': ('Revenir aux positions et vitesses du dernier départ.',
                                       'Go back to the positions and velocities of the last start.'),
    'anim_gravityorbits_effacer': ('Effacer les trajectoires', 'Clear paths'),
    'anim_gravityorbits_effacer_aide': ('Efface les chemins déjà tracés.', 'Clears the paths already drawn.'),
    # ------------------------------------------------------------ noms
    'anim_gravityorbits_n_soleil': ('Soleil', 'Sun'),
    'anim_gravityorbits_n_terre': ('Terre', 'Earth'),
    'anim_gravityorbits_n_lune': ('Lune', 'Moon'),
    'anim_gravityorbits_n_iss': ('ISS', 'ISS'),
    'anim_gravityorbits_n_comete': ('Comète', 'Comet'),
    'anim_gravityorbits_n_terre_lune': ('Terre et Lune (un seul point)', 'Earth and Moon (a single dot)'),
    # ------------------------------------------------------------ toile
    'anim_gravityorbits_titre_modele': ('Modèle (astres agrandis)', 'Model (bodies enlarged)'),
    'anim_gravityorbits_titre_echelle': ('À l’échelle (tailles et distances réelles)', 'To scale (real sizes and distances)'),
    'anim_gravityorbits_titre_lune_soleil': ('Lune vue du Soleil (vraie géométrie)', 'Moon seen from the Sun (true geometry)'),
    'anim_gravityorbits_vers_soleil': ('vers le Soleil', 'towards the Sun'),
    'anim_gravityorbits_courbure_graphe': ('courbure Lune / Terre', 'Moon / Earth curvature'),
    'anim_gravityorbits_jours': ('{n} jours terrestres', '{n} Earth days'),
    'anim_gravityorbits_minutes': ('{n} min', '{n} min'),
    'anim_gravityorbits_j': ('j', 'd'),
    'anim_gravityorbits_carreau': ('carreau : {d}', 'square: {d}'),
    'anim_gravityorbits_agrandi': ('astres ×{k} ; distance Terre–Lune ×{l}', 'bodies ×{k}; Earth–Moon distance ×{l}'),
    'anim_gravityorbits_agrandi_astres': ('astres ×{k}', 'bodies ×{k}'),
    'anim_gravityorbits_agrandi_iss': ('station ×{k}', 'station ×{k}'),
    'anim_gravityorbits_sans_gravite': ('gravité coupée', 'gravity off'),
    'anim_gravityorbits_ua': ('ua', 'au'),
    'anim_gravityorbits_millions_km': ('{n} millions de km', '{n} million km'),
    # ------------------------------------------------------------ valeurs
    'anim_gravityorbits_v_temps': ('Temps écoulé', 'Elapsed time'),
    'anim_gravityorbits_v_distance': ('Distance {a}–{b}', '{a}–{b} distance'),
    'anim_gravityorbits_v_vitesse': ('Vitesse relative {a} / {b}', '{a} / {b} relative speed'),
    'anim_gravityorbits_v_periode': ('Période mesurée ({a})', 'Measured period ({a})'),
    'anim_gravityorbits_v_attente': ('après un premier tour', 'after a first revolution'),
    'anim_gravityorbits_v_vraie': ('vraie : {t}', 'true: {t}'),
    'anim_gravityorbits_v_kepler': ('Kepler : {t}', 'Kepler: {t}'),
    'anim_gravityorbits_v_ecart': ('écart {e}\u202f%', '{e}% off'),
    'anim_gravityorbits_v_energie': ('Énergie totale', 'Total energy'),
    'anim_gravityorbits_v_derive': ('variation relative {d}', 'relative change {d}'),
    'anim_gravityorbits_v_moment': ('Moment cinétique (variation relative)', 'Angular momentum (relative change)'),
    'anim_gravityorbits_v_ruban': ('Ruban de mesure', 'Measuring tape'),
    'anim_gravityorbits_v_courbure': ('Courbure de la Lune vue du Soleil', 'Curvature of the Moon seen from the Sun'),
    'anim_gravityorbits_v_courbure_val': ('toujours vers le Soleil : de {a} à {b} fois celle de la Terre',
                                          'always towards the Sun: {a} to {b} times the Earth’s'),
    'anim_gravityorbits_v_courbure_neg': ('change de signe (de {a} à {b} fois celle de la Terre)',
                                          'changes sign ({a} to {b} times the Earth’s)'),
    'anim_gravityorbits_v_gravite': ('Gravité', 'Gravity'),
    'anim_gravityorbits_v_gravite_coupee': ('coupée : chaque corps va tout droit à vitesse constante',
                                            'off: each body goes straight on at constant speed'),
    'anim_gravityorbits_v_collision': ('Collision', 'Collision'),
    'anim_gravityorbits_v_collision_val': ('écrasement : {a} sur {b}', 'crash: {a} into {b}'),
    'anim_gravityorbits_v_dessin': ('Dessin', 'Drawing'),
    # ------------------------------------------------------------ aide, provenance
    'anim_gravityorbits_souris': ('Glisser un astre pour le déplacer (ses satellites le suivent) ; glisser le bout d’une '
                                  'flèche verte pour changer sa vitesse ; glisser les bouts du ruban pour mesurer.',
                                  'Drag a body to move it (its satellites follow); drag the tip of a green arrow to '
                                  'change its velocity; drag the ends of the tape to measure.'),
    'anim_gravityorbits_adapte': ('D’après la simulation PhET « Gravity and Orbits » (University of Colorado Boulder) ; '
                                  'code, dessins et textes propres à Coupole',
                                  'After the PhET simulation “Gravity and Orbits” (University of Colorado Boulder); '
                                  'code, drawings and texts are Coupole’s own'),
    'anim_gravityorbits_lien': ('La simulation d’origine : PhET Interactive Simulations',
                                'The original simulation: PhET Interactive Simulations'),
    'anim_gravityorbits_a_voir': (
        'La Terre tourne autour du Soleil en 365,26 jours, la Lune autour de la Terre en 27,3 jours : les périodes '
        'mesurées le confirment à mieux que 0,2 %. Coupez la gravité : chaque corps file tout droit, c’est la gravité'
        ' qui courbe les trajectoires. Passez « à l’échelle » : vus du Soleil, la Terre et la Lune ne font qu’un seul'
        ' point, et le Soleil n’est qu’un tout petit disque. En vue « Modèle », la distance Terre–Lune est agrandie '
        '78 fois : la trace de la Lune y fait des boucles qui n’existent pas. La vraie trajectoire de la Lune autour '
        'du Soleil ne fait jamais de boucle : elle est toujours tournée vers le Soleil, qui la tire deux fois plus '
        'fort que la Terre. L’énergie totale et le moment cinétique restent constants.',
        'The Earth goes round the Sun in 365.26 days, the Moon round the Earth in 27.3 days: the measured periods '
        'confirm it to better than 0.2%. Turn gravity off: each body moves off in a straight line; gravity is what '
        'bends the paths. Switch to “to scale”: seen from the Sun, the Earth and the Moon are a single dot, and the '
        'Sun is only a tiny disc. In the “Model” view the Earth–Moon distance is enlarged 78 times: the Moon’s trace '
        'makes loops there that do not exist. The Moon’s real path around the Sun never loops: it always curves '
        'towards the Sun, which pulls it twice as hard as the Earth does. Total energy and angular momentum stay '
        'constant.'),
}

#: la simulation d'origine (lien croisé de la fiche)
URL_PHET = 'https://phet.colorado.edu/sims/html/gravity-and-orbits/latest/gravity-and-orbits_fr.html'
