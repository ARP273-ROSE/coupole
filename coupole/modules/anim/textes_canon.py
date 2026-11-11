"""Textes FR/EN de l'animation « Le canon de Newton » (idée des Principia de Newton, 1687 ; textes propres à
Coupole).  Fusionnés dans ``textes.TEXTES`` (et exportés tels quels vers Coupole Web)."""

ANIM_CANON = {
    # ------------------------------------------------------------ réglages
    'anim_newtoncannon_astre': ('Astre', 'Body'),
    'anim_newtoncannon_astre_aide': ('Astre sur lequel se dresse la montagne (sphérique, immobile, sans rotation).',
                                     'Body on which the mountain stands (spherical, motionless, not rotating).'),
    'anim_newtoncannon_a_terre': ('Terre', 'Earth'),
    'anim_newtoncannon_a_lune': ('Lune', 'Moon'),
    'anim_newtoncannon_a_mars': ('Mars', 'Mars'),
    'anim_newtoncannon_a_ceres': ('Cérès (planète naine)', 'Ceres (dwarf planet)'),
    'anim_newtoncannon_a_dimorphos': ('Dimorphos (astéroïde de 151 m)', 'Dimorphos (151 m asteroid)'),
    'anim_newtoncannon_altitude': ('Altitude du canon', 'Cannon altitude'),
    'anim_newtoncannon_altitude_aide': ('Hauteur de la montagne au-dessus du sol (échelle logarithmique). Plus le canon '
                                        'est haut, plus les vitesses de satellisation et de libération sont faibles.',
                                        'Height of the mountain above the ground (logarithmic scale). The higher the '
                                        'cannon, the lower the orbital and escape speeds.'),
    'anim_newtoncannon_vitesse': ('Vitesse de tir', 'Muzzle speed'),
    'anim_newtoncannon_vitesse_aide': ('Vitesse du boulet à la sortie du canon. Repères sous le curseur : v₁, vitesse '
                                       'de satellisation (orbite circulaire) ; v₂, vitesse de libération. On peut aussi '
                                       'tirer le bout de la flèche verte.',
                                       'Speed of the ball leaving the cannon. Marks under the slider: v₁, circular '
                                       'orbital speed; v₂, escape speed. You can also drag the tip of the green '
                                       'arrow.'),
    'anim_newtoncannon_angle': ('Angle de tir', 'Firing angle'),
    'anim_newtoncannon_angle_aide': ('Angle au-dessus de l’horizontale (0° : tir horizontal, comme chez Newton).',
                                     'Angle above the horizontal (0°: horizontal shot, as in Newton).'),
    'anim_newtoncannon_air': ('Atmosphère', 'Atmosphere'),
    'anim_newtoncannon_air_aide': ('L’air freine le boulet (traînée ½ ρ v² × aire × coefficient de traînée). Densité réelle : Terre de 0 à '
                                   '1 000 km par tranches exponentielles (CIRA-72), Mars exponentielle (H = 11,1 km).',
                                   'Air slows the ball down (drag ½ ρ v² × area × drag coefficient). Real density: Earth from 0 to '
                                   '1,000 km in exponential layers (CIRA-72), Mars exponential (H = 11.1 km).'),
    'anim_newtoncannon_projectile': ('Projectile', 'Projectile'),
    'anim_newtoncannon_projectile_aide': ('Coefficient balistique B = masse / (coefficient de traînée × aire) : plus il est petit, plus l’air '
                                          'freine.',
                                          'Ballistic coefficient B = mass / (drag coefficient × area): the smaller it is, the more the air '
                                          'slows the object down.'),
    'anim_newtoncannon_p_boulet': ('Boulet de fonte (B ≈ 1 300 kg·m⁻²)', 'Cast-iron ball (B ≈ 1,300 kg·m⁻²)'),
    'anim_newtoncannon_p_capsule': ('Capsule (B ≈ 350 kg·m⁻²)', 'Capsule (B ≈ 350 kg·m⁻²)'),
    'anim_newtoncannon_p_satellite': ('Satellite (B ≈ 50 kg·m⁻²)', 'Satellite (B ≈ 50 kg·m⁻²)'),
    'anim_newtoncannon_temps': ('Temps', 'Time'),
    'anim_newtoncannon_temps_aide': ('Accélération du temps : ×100, une seconde à l’écran vaut 100 s.',
                                     'Time acceleration: at ×100, one second on screen is 100 s.'),
    'anim_newtoncannon_t_1': ('×1 (temps réel)', '×1 (real time)'),
    'anim_newtoncannon_t_10': ('×10', '×10'),
    'anim_newtoncannon_t_100': ('×100', '×100'),
    'anim_newtoncannon_t_1000': ('×1 000', '×1,000'),
    'anim_newtoncannon_apercu': ('Trajectoire prévue', 'Predicted path'),
    'anim_newtoncannon_apercu_aide': ('Pointillés : la trajectoire qu’aurait le boulet sans air (conique de Kepler), '
                                      'mise à jour pendant qu’on règle le tir.',
                                      'Dotted line: the path the ball would follow without air (Kepler conic), updated '
                                      'while you set up the shot.'),
    'anim_newtoncannon_defi': ('Défi', 'Challenge'),
    'anim_newtoncannon_defi_aide': ('Un objectif ; chaque tir est vérifié automatiquement.',
                                    'A goal; each shot is checked automatically.'),
    'anim_newtoncannon_d_aucun': ('Aucun', 'None'),
    'anim_newtoncannon_d_cercle': ('Orbite circulaire', 'Circular orbit'),
    'anim_newtoncannon_d_liberation': ('Libération au plus juste', 'Just enough to escape'),
    'anim_newtoncannon_d_au_dessus': ('Orbite au-dessus de l’air', 'Orbit above the air'),
    'anim_newtoncannon_d_antipodes': ('Viser les antipodes', 'Hit the antipodes'),
    'anim_newtoncannon_d_dimorphos': ('Satellite de Dimorphos', 'Satellite of Dimorphos'),
    # ------------------------------------------------------------ boutons
    'anim_newtoncannon_feu': ('Feu !', 'Fire!'),
    'anim_newtoncannon_feu_aide': ('Tirer avec les réglages actuels (touche Espace quand la scène a le focus).',
                                   'Fire with the current settings (Space key when the scene has the focus).'),
    'anim_newtoncannon_recommencer': ('Recommencer', 'Restart'),
    'anim_newtoncannon_recommencer_aide': ('Refaire le dernier tir depuis le canon.', 'Redo the last shot from the cannon.'),
    'anim_newtoncannon_effacer': ('Effacer les tirs', 'Clear shots'),
    'anim_newtoncannon_effacer_aide': ('Effacer toutes les trajectoires.', 'Clear all paths.'),
    'anim_newtoncannon_recadrer': ('Recadrer', 'Reframe'),
    'anim_newtoncannon_recadrer_aide': ('Revenir au cadrage automatique, qui suit la trajectoire (double-clic aussi).',
                                        'Back to automatic framing, which follows the path (double-click too).'),
    'anim_newtoncannon_pr_pied': ('Tombe au pied', 'Falls nearby'),
    'anim_newtoncannon_pr_pied_aide': ('Tir lent (0,3 v₁) : le boulet retombe près de la montagne.',
                                       'Slow shot (0.3 v₁): the ball falls back near the mountain.'),
    'anim_newtoncannon_pr_ras_sol': ('Tour au ras du sol', 'Round trip at ground level'),
    'anim_newtoncannon_pr_ras_sol_aide': ('Depuis une montagne basse, à v₁ : le boulet fait le tour de l’astre et '
                                          'revient dans le dos du canon.',
                                          'From a low mountain, at v₁: the ball goes round the body and comes back '
                                          'behind the cannon.'),
    'anim_newtoncannon_pr_iss': ('Orbite de l’ISS', 'ISS orbit'),
    'anim_newtoncannon_pr_iss_aide': ('Terre, 415 km, à v₁ ≈ 7,66 km·s⁻¹ : un tour en 92,9 min.',
                                      'Earth, 415 km, at v₁ ≈ 7.66 km·s⁻¹: one orbit in 92.9 min.'),
    'anim_newtoncannon_pr_ellipse': ('Ellipse', 'Ellipse'),
    'anim_newtoncannon_pr_ellipse_aide': ('Plus vite que v₁ (√1,5 v₁) : ellipse d’excentricité 0,5, le canon au '
                                          'périapside.',
                                          'Faster than v₁ (√1.5 v₁): ellipse of eccentricity 0.5, the cannon at '
                                          'periapsis.'),
    'anim_newtoncannon_pr_liberation': ('Juste libéré', 'Just escaping'),
    'anim_newtoncannon_pr_liberation_aide': ('Exactement v₂ = √2 v₁ : parabole, le boulet ne revient jamais.',
                                             'Exactly v₂ = √2 v₁: parabola, the ball never comes back.'),
    'anim_newtoncannon_pr_hyperbole': ('Hyperbole', 'Hyperbola'),
    'anim_newtoncannon_pr_hyperbole_aide': ('Au-delà de v₂ (√3 v₁) : hyperbole d’excentricité 2.',
                                            'Beyond v₂ (√3 v₁): hyperbola of eccentricity 2.'),
    'anim_newtoncannon_pr_rentree': ('Rentrée atmosphérique', 'Atmospheric re-entry'),
    'anim_newtoncannon_pr_rentree_aide': ('Terre avec l’air : une capsule à 200 km, un peu sous v₁ (périgée prévu à '
                                          '60 km) ; l’air la freine et elle se pose avant le périgée.',
                                          'Earth with air: a capsule at 200 km, slightly below v₁ (perigee planned at '
                                          '60 km); the air slows it down and it lands before perigee.'),
    # ------------------------------------------------------------ dessin
    'anim_newtoncannon_titre': ('Le canon de Newton : {a}', 'Newton’s cannon: {a}'),
    'anim_newtoncannon_v1': ('v₁ satellisation', 'v₁ orbit'),
    'anim_newtoncannon_v2': ('v₂ libération', 'v₂ escape'),
    'anim_newtoncannon_legende': ('Tir {n} · {v} · {a}', 'Shot {n} · {v} · {a}'),
    'anim_newtoncannon_echelle': ('{d}', '{d}'),
    'anim_newtoncannon_temps_ecoule': ('t = {t} ({k})', 't = {t} ({k})'),
    'anim_newtoncannon_atm_echelle': ('air à l’échelle', 'air to scale'),
    'anim_newtoncannon_reussi': ('Défi réussi !', 'Challenge met!'),
    'anim_newtoncannon_rate': ('Raté, on recommence ?', 'Missed, try again?'),
    # ------------------------------------------------------------ valeurs
    'anim_newtoncannon_v_reperes': ('À l’altitude du canon', 'At the cannon’s altitude'),
    'anim_newtoncannon_v_reperes_val': ('v₁ = {v1} (satellisation) · v₂ = {v2} (libération)',
                                        'v₁ = {v1} (circular orbit) · v₂ = {v2} (escape)'),
    'anim_newtoncannon_v_tir': ('Tir réglé', 'Shot set'),
    'anim_newtoncannon_v_tir_val': ('{v} = {k1} v₁ = {k2} v₂ · angle {a}', '{v} = {k1} v₁ = {k2} v₂ · angle {a}'),
    'anim_newtoncannon_v_trajectoire': ('Trajectoire prévue (sans air)', 'Predicted path (no air)'),
    'anim_newtoncannon_ty_retombe': ('retombe sur le sol (morceau d’ellipse)', 'falls back to the ground (piece of an ellipse)'),
    'anim_newtoncannon_ty_cercle': ('orbite circulaire', 'circular orbit'),
    'anim_newtoncannon_ty_ellipse': ('orbite elliptique', 'elliptical orbit'),
    'anim_newtoncannon_ty_parabole': ('parabole : libéré tout juste', 'parabola: just escaping'),
    'anim_newtoncannon_ty_hyperbole': ('hyperbole : libéré', 'hyperbola: escaping'),
    'anim_newtoncannon_v_type_val': ('{t} · e = {e}', '{t} · e = {e}'),
    'anim_newtoncannon_v_apsides': ('Périapside · apoapside (altitudes)', 'Periapsis · apoapsis (altitudes)'),
    'anim_newtoncannon_sous_sol': ('{h} (sous la surface)', '{h} (below the surface)'),
    'anim_newtoncannon_infini': ('à l’infini', 'at infinity'),
    'anim_newtoncannon_v_periode': ('Période (3ᵉ loi de Kepler)', 'Period (Kepler’s 3rd law)'),
    'anim_newtoncannon_v_energie': ('Énergie mécanique par kilogramme', 'Mechanical energy per kilogram'),
    'anim_newtoncannon_lie': ('{e} (< 0 : lié à l’astre)', '{e} (< 0: bound to the body)'),
    'anim_newtoncannon_libre': ('{e} (≥ 0 : libre)', '{e} (≥ 0: free)'),
    'anim_newtoncannon_v_tir_n': ('Tir {n}', 'Shot {n}'),
    'anim_newtoncannon_en_vol': ('en vol : t = {t}, altitude {h}, {v}', 'in flight: t = {t}, altitude {h}, {v}'),
    'anim_newtoncannon_en_orbite': ('en orbite : {n} tour(s), période mesurée {T} (Kepler : {Tk}), altitude {h}',
                                    'in orbit: {n} orbit(s), measured period {T} (Kepler: {Tk}), altitude {h}'),
    'anim_newtoncannon_impact': ('impact après {t}, à {d} du pied de la montagne ({a})',
                                 'impact after {t}, {d} from the foot of the mountain ({a})'),
    'anim_newtoncannon_libere': ('libéré : à {d} du centre après {t}, il ne reviendra jamais',
                                 'escaped: {d} from the centre after {t}, it will never come back'),
    'anim_newtoncannon_v_freinage': ('Freinage de l’air', 'Air drag'),
    'anim_newtoncannon_freinage_val': ('{a} ({g} g), densité {r}', '{a} ({g} g), density {r}'),
    'anim_newtoncannon_v_defi': ('Défi', 'Challenge'),
    'anim_newtoncannon_j': ('j', 'd'),
    # énoncés des défis
    'anim_newtoncannon_de_cercle': ('Mettre le boulet sur une orbite circulaire (e ≤ 0,02).',
                                    'Put the ball on a circular orbit (e ≤ 0.02).'),
    'anim_newtoncannon_de_liberation': ('Depuis la Lune, se libérer avec le moins de vitesse possible (moins de 2 % '
                                        'au-dessus de v₂).',
                                        'From the Moon, escape with as little speed as possible (less than 2% above '
                                        'v₂).'),
    'anim_newtoncannon_de_au_dessus': ('Sur Terre, avec l’air : une orbite qui ne touche jamais l’atmosphère '
                                       '(périgée au-dessus de 100 km). Le canon est à 60 km…',
                                       'On Earth, with air: an orbit that never touches the atmosphere (perigee '
                                       'above 100 km). The cannon is at 60 km…'),
    'anim_newtoncannon_de_antipodes': ('Faire tomber le boulet aux antipodes du canon (180° ± 3° plus loin). Indice : levez un peu le canon.',
                                       'Make the ball land at the antipodes of the cannon (180° ± 3° away). Hint: raise the barrel a little.'),
    'anim_newtoncannon_de_dimorphos': ('Mettre un boulet en orbite autour de l’astéroïde Dimorphos.',
                                       'Put a ball in orbit around the asteroid Dimorphos.'),
    # verdicts
    'anim_newtoncannon_ve_a_tirer': ('réglez puis tirez (Feu ou Espace)', 'set up then fire (Fire or Space)'),
    'anim_newtoncannon_ve_reussi': ('Réussi ! {d}', 'Success! {d}'),
    'anim_newtoncannon_ve_cercle': ('e = {e}', 'e = {e}'),
    'anim_newtoncannon_ve_liberation': ('{p} % au-dessus de v₂', '{p}% above v₂'),
    'anim_newtoncannon_ve_au_dessus': ('périgée à {h}', 'perigee at {h}'),
    'anim_newtoncannon_ve_antipodes': ('impact à {d}', 'impact at {d}'),
    'anim_newtoncannon_ve_dimorphos': ('un tour complet, à quelques centimètres par seconde',
                                       'one full orbit, at a few centimetres per second'),
    'anim_newtoncannon_ve_sol': ('Raté : le boulet touche le sol.', 'Missed: the ball hits the ground.'),
    'anim_newtoncannon_ve_sol_indice': ('Raté : le boulet retombe. Indice : une orbite repasse toujours par son point '
                                        'de départ, et le canon est dans l’air…',
                                        'Missed: the ball falls back. Hint: an orbit always comes back through its '
                                        'starting point, and the cannon is in the air…'),
    'anim_newtoncannon_ve_e': ('Raté : e = {e}, orbite trop allongée.', 'Missed: e = {e}, orbit too elongated.'),
    'anim_newtoncannon_ve_lent': ('Raté : il manque {p} % pour atteindre v₂ ; il reviendra.',
                                  'Missed: {p}% short of v₂; it will come back.'),
    'anim_newtoncannon_ve_rapide': ('Libéré, mais {p} % au-dessus de v₂ : visez moins de 2 %.',
                                    'Escaped, but {p}% above v₂: aim for less than 2%.'),
    'anim_newtoncannon_ve_ouverte': ('Raté : le boulet s’échappe.', 'Missed: the ball escapes.'),
    'anim_newtoncannon_ve_perigee': ('Raté : périgée à {h}, dans l’air. Indice : une orbite repasse toujours par son '
                                     'point de départ.',
                                     'Missed: perigee at {h}, in the air. Hint: an orbit always comes back through '
                                     'its starting point.'),
    'anim_newtoncannon_ve_astre_terre': ('Ce défi se joue sur Terre.', 'This challenge is played on Earth.'),
    'anim_newtoncannon_ve_astre_dimorphos': ('Ce défi se joue sur Dimorphos.', 'This challenge is played on Dimorphos.'),
    'anim_newtoncannon_ve_impact': ('Raté : impact à {d} (visez 180°).', 'Missed: impact at {d} (aim for 180°).'),
    'anim_newtoncannon_ve_pas_de_chute': ('Raté : le boulet ne retombe pas.', 'Missed: the ball does not come down.'),
    'anim_newtoncannon_ve_tour': ('attendez un tour complet…', 'wait for one full orbit…'),
    'anim_newtoncannon_ve_loin': ('il s’éloigne…', 'it is moving away…'),
    'anim_newtoncannon_ve_chute': ('il tombe…', 'it is falling…'),
    'anim_newtoncannon_adapte': ('Propre à Coupole (pas dans ClassAction), d’après l’expérience de pensée de Newton '
                                 '(Traité du système du monde, 1728) : UAI 2015, DE440, Dawn (Cérès), DART (Dimorphos), '
                                 'atmosphère CIRA-72 ; idée reprise du simulateur de Science Étonnante (explorables.scienceetonnante.com), '
                                 'refait sans rien en copier',
                                 'Coupole’s own (not in ClassAction), after Newton’s thought experiment (Treatise of '
                                 'the System of the World, 1728): IAU 2015, DE440, Dawn (Ceres), DART (Dimorphos), '
                                 'CIRA-72 atmosphere; idea taken from the Science Étonnante simulator (explorables.scienceetonnante.com), '
                                 'remade without copying anything'),
    'anim_newtoncannon_lien': ('Sources : fichier NOTICE de Coupole', 'Sources: Coupole NOTICE file'),
    # aide
    'anim_newtoncannon_souris': ('Tirer le bout de la flèche verte règle l’angle et la vitesse (cercles v₁ : '
                                 'satellisation, v₂ : libération) ; Feu ou Espace pour tirer ; ↑ ↓ vitesse, ← → angle ; '
                                 'molette ou deux doigts pour zoomer, double-clic pour recadrer.',
                                 'Drag the tip of the green arrow to set the angle and speed (circles v₁: orbit, '
                                 'v₂: escape); Fire or Space to shoot; ↑ ↓ speed, ← → angle; wheel or two fingers to '
                                 'zoom, double-click to reframe.'),
}
