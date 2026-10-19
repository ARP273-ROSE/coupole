"""Textes FR/EN de la rubrique « Calculateurs de TD »."""
from __future__ import annotations

TEXTES = {
    'td_rubrique_intro': {'fr': 'Des calculateurs qui suivent pas à pas la démarche des TD et TP du cours, avec vos '
                                'nombres, puis montrent le calcul exact.',
                          'en': 'Calculators that follow the course exercises and practicals step by step, with your '
                                'numbers, then show the exact calculation.'},
    'td_liste_aide': {'fr': 'Choisissez un calculateur.', 'en': 'Choose a calculator.'},
    'td_calc_parallaxe': {'fr': 'Parallaxe (TP du cours)', 'en': 'Parallax (course practical)'},
    'td_calc_parallaxe_aide': {'fr': 'Altitude de l’ISS ou distance de la Lune par deux élévations relevées au même '
                                     'instant, comme dans le sujet du TP ; puis le calcul exact.',
                               'en': 'ISS altitude or Moon distance from two elevations taken at the same instant, as '
                                     'in the practical; then the exact calculation.'},
    'td_p_intro': {'fr': 'Le sujet : relevez dans Stellarium les élévations h₁ et h₂ de l’objet vu des deux lieux au '
                         'même instant ; la parallaxe est 2α = h₁ − h₂ ; la distance R entre les deux lieux se mesure '
                         '« par exemple avec Google Earth » ou avec EarthLocation d’astropy ; enfin 2α = R / D (2α en '
                         'radians). Les positions s’écrivent comme on veut (48°47′6″N, 48,785, 2.45 E…).',
                   'en': 'The practical: read in Stellarium the elevations h₁ and h₂ of the object seen from both '
                         'places at the same instant; the parallax is 2α = h₁ − h₂; the distance R between the two '
                         'places is measured “for instance with Google Earth” or with astropy’s EarthLocation; '
                         'finally 2α = R / D (2α in radians). Positions can be written in any way (48°47′6″N, '
                         '48.785, 2.45 E…).'},
    'td_cible': {'fr': 'Cible', 'en': 'Target'},
    'td_cible_aide': {'fr': 'ISS (altitude) ou Lune (distance).', 'en': 'ISS (altitude) or Moon (distance).'},
    'td_cible_iss': {'fr': 'ISS', 'en': 'ISS'},
    'td_cible_lune': {'fr': 'Lune', 'en': 'Moon'},
    'td_conf': {'fr': 'Position de l’objet', 'en': 'Object position'},
    'td_conf_aide': {'fr': 'Sans azimut, l’objet est supposé dans le plan vertical qui contient les deux lieux : '
                           'entre eux (chacun le voit du côté de l’autre) ou du même côté (au-delà du lieu qui le voit '
                           'le plus haut). Avec les deux azimuts, c’est inutile.',
                     'en': 'Without azimuth, the object is assumed in the vertical plane containing both places: '
                           'between them (each sees it toward the other) or on the same side (beyond the place that '
                           'sees it highest). With both azimuths, this is not needed.'},
    'td_conf_auto': {'fr': 'du même côté (ou d’après les azimuts)', 'en': 'same side (or from the azimuths)'},
    'td_conf_entre': {'fr': 'entre les deux lieux', 'en': 'between the two places'},
    'td_conf_meme': {'fr': 'du même côté', 'en': 'on the same side'},
    'td_lieu': {'fr': 'Lieu {n}', 'en': 'Place {n}'},
    'td_p': {'fr': 'Position', 'en': 'Position'},
    'td_p_aide': {'fr': 'Latitude et longitude, dans n’importe quelle écriture : 48°47′6″N 2°27′E, 48.785, 2.45, '
                        '48 47 06 N 2 27 00 E, 48d47m6s… Sans lettre : latitude puis longitude.',
                  'en': 'Latitude and longitude, written in any way: 48°47′6″N 2°27′E, 48.785, 2.45, 48 47 06 N 2 27 '
                        '00 E, 48d47m6s… Without letters: latitude then longitude.'},
    'td_p_indice': {'fr': '48°47′6″ N 2°27′ E', 'en': '48°47′6″ N 2°27′ E'},
    'td_alt': {'fr': 'Altitude', 'en': 'Elevation'},
    'td_alt_aide': {'fr': 'Altitude du lieu (m, ou « 1,2 km »).', 'en': 'Elevation of the place (m, or “1.2 km”).'},
    'td_alt_indice': {'fr': '35 m', 'en': '35 m'},
    'td_h': {'fr': 'Élévation h', 'en': 'Elevation h'},
    'td_h_aide': {'fr': 'Élévation (hauteur sur l’horizon) relevée dans Stellarium ; pour la Lune, la distance '
                        'angulaire Lune–étoile φ du sujet convient aussi (même calcul).',
                  'en': 'Elevation (altitude above the horizon) read in Stellarium; for the Moon, the Moon–star '
                        'angular distance φ of the practical works too (same calculation).'},
    'td_h_indice': {'fr': '54°37′ ou 54,62', 'en': '54°37′ or 54.62'},
    'td_az': {'fr': 'Azimut (facultatif)', 'en': 'Azimuth (optional)'},
    'td_az_aide': {'fr': 'Azimut relevé dans Stellarium (nord 0°, est 90°). Avec les deux azimuts, le calcul exact '
                         'triangule les visées dans l’espace.',
                   'en': 'Azimuth read in Stellarium (north 0°, east 90°). With both azimuths, the exact calculation '
                         'triangulates the lines of sight in space.'},
    'td_az_indice': {'fr': '150°', 'en': '150°'},
    'td_instant': {'fr': 'Date et heure TU (facultatif)', 'en': 'Date and time UT (optional)'},
    'td_instant_aide': {'fr': 'Instant de la mesure, en temps universel : sert à comparer à l’éphéméride.',
                        'en': 'Instant of the measurement, in universal time: used to compare with the ephemeris.'},
    'td_instant_indice': {'fr': '2026-10-17 04:29:11', 'en': '2026-10-17 04:29:11'},
    'td_maintenant': {'fr': 'Maintenant', 'en': 'Now'},
    'td_maintenant_aide': {'fr': 'Date et heure TU de cet ordinateur.', 'en': 'Date and time UT of this computer.'},
    'td_sigma_h': {'fr': 'Incertitude sur h', 'en': 'Uncertainty on h'},
    'td_sigma_h_aide': {'fr': 'Incertitude d’une élévation relevée (degrés).',
                        'en': 'Uncertainty of a read elevation (degrees).'},
    'td_sigma_pos': {'fr': 'Incertitude sur les lieux', 'en': 'Uncertainty on the places'},
    'td_sigma_pos_aide': {'fr': 'Incertitude de chaque position (mètres).', 'en': 'Uncertainty of each position '
                                                                                  '(metres).'},
    'td_sigma_t': {'fr': 'Incertitude sur l’heure', 'en': 'Uncertainty on the time'},
    'td_sigma_t_aide': {'fr': 'Décalage possible entre les deux mesures (secondes) : multiplié par la vitesse de '
                              'l’objet en élévation (d’après l’éphéméride, si l’heure est donnée).',
                        'en': 'Possible offset between both measurements (seconds): multiplied by the object’s speed '
                              'in elevation (from the ephemeris, if the time is given).'},
    'td_unite_deg': {'fr': '°', 'en': '°'},
    'td_unite_m': {'fr': 'm', 'en': 'm'},
    'td_unite_s': {'fr': 's', 'en': 's'},
    'td_eph': {'fr': 'Éphémérides', 'en': 'Ephemerides'},
    'td_eph_etat_de440': {'fr': 'Lune : JPL DE440 (fichier en cache). ISS : TLE de CelesTrak.',
                          'en': 'Moon: JPL DE440 (cached file). ISS: CelesTrak TLE.'},
    'td_eph_etat_meeus': {'fr': 'Lune : approximation de Meeus (quelques km) ; DE440 (32 Mo, une fois) pour mieux. '
                                'ISS : TLE de CelesTrak.',
                          'en': 'Moon: Meeus approximation (a few km); DE440 (32 MB, once) for better. ISS: CelesTrak '
                                'TLE.'},
    'td_de440': {'fr': 'Télécharger DE440', 'en': 'Download DE440'},
    'td_de440_aide': {'fr': 'Éphéméride JPL DE440 réduite (de440s.bsp, 32 Mo, domaine public), téléchargée une fois '
                            'et gardée ; tout marche ensuite hors ligne.',
                      'en': 'Reduced JPL DE440 ephemeris (de440s.bsp, 32 MB, public domain), downloaded once and kept; '
                            'everything then works offline.'},
    'td_de440_en_cours': {'fr': 'Téléchargement de DE440…', 'en': 'Downloading DE440…'},
    'td_de440_ok': {'fr': 'DE440 prête.', 'en': 'DE440 ready.'},
    'td_de440_echec': {'fr': 'DE440 non téléchargée : {erreur}', 'en': 'DE440 not downloaded: {erreur}'},
    'td_tle_recuperer': {'fr': 'Récupérer le TLE', 'en': 'Get the TLE'},
    'td_tle_recuperer_aide': {'fr': 'TLE de l’ISS le plus proche de l’instant : cache, sinon CelesTrak (éléments du '
                                    'jour). L’historique des TLE n’est pas librement disponible sans compte '
                                    'Space-Track : pour un passage ancien, collez un TLE de l’époque.',
                              'en': 'ISS TLE closest to the instant: cache, otherwise CelesTrak (current elements). '
                                    'TLE history is not freely available without a Space-Track account: for an old '
                                    'pass, paste a TLE of that time.'},
    'td_tle_aide': {'fr': 'Deux lignes du TLE. Vide : le TLE le plus proche de l’instant est récupéré tout seul '
                          '(cache, sinon CelesTrak). Saisie possible hors ligne.',
                    'en': 'Two TLE lines. Empty: the TLE closest to the instant is fetched automatically (cache, '
                          'otherwise CelesTrak). Can be typed offline.'},
    'td_tle_indice': {'fr': '1 25544U … / 2 25544 …', 'en': '1 25544U … / 2 25544 …'},
    'td_tle_recu': {'fr': 'TLE du {date} TU ({source}), à {age} jours de l’instant.',
                    'en': 'TLE of {date} UT ({source}), {age} days from the instant.'},
    'td_tle_aucun': {'fr': 'Aucun TLE (hors ligne ?) : collez-en un. {erreur}', 'en': 'No TLE (offline?): paste one. '
                                                                                     '{erreur}'},
    'td_tle_source_cache': {'fr': 'cache', 'en': 'cache'},
    'td_tle_source_celestrak': {'fr': 'CelesTrak', 'en': 'CelesTrak'},
    'td_calculer': {'fr': 'Calculer', 'en': 'Calculate'},
    'td_calculer_aide': {'fr': 'Toutes les étapes du sujet avec vos nombres, puis le calcul exact.',
                         'en': 'All the steps of the practical with your numbers, then the exact calculation.'},
    'td_exemple': {'fr': 'Exemple', 'en': 'Example'},
    'td_exemple_aide': {'fr': 'Remplir avec des données FICTIVES cohérentes (deux grandes villes).',
                        'en': 'Fill in with consistent FICTITIOUS data (two large cities).'},
    'td_exemple_fictif': {'fr': 'Exemple : données fictives (villes publiques, élévations calculées).',
                          'en': 'Example: fictitious data (public cities, computed elevations).'},
    'td_exporter': {'fr': 'Exporter le détail', 'en': 'Export the details'},
    'td_exporter_aide': {'fr': 'Le détail des calculs (CSV) pour la feuille « Calculs » du partage.',
                         'en': 'The calculation details (CSV) for the “Calculs” sheet of the share.'},
    'td_exporte': {'fr': 'Détail écrit : {chemin}', 'en': 'Details written: {chemin}'},
    'td_zoom': {'fr': 'Zoom', 'en': 'Zoom'},
    'td_zoom_aide': {'fr': 'Resserrer le dessin autour des deux lieux (× 1 à × 60).',
                     'en': 'Close in the drawing around the two places (× 1 to × 60).'},
    'td_schema_aide': {'fr': 'Coupe de la Terre dans le plan des deux lieux : corde R, verticales (tirets), horizons '
                             '(verts), visées (rouges), angles ; loupe : la flèche entre la corde et la surface.',
                       'en': 'Cross-section of the Earth in the plane of both places: chord R, verticals (dashed), '
                             'horizons (green), lines of sight (red), angles; magnifier: the sagitta between the '
                             'chord and the surface.'},
    'td_schema_vide': {'fr': 'Saisissez les deux lieux et les deux élévations, puis « Calculer » (ou « Exemple »).',
                       'en': 'Enter both places and both elevations, then “Calculate” (or “Example”).'},
    'td_s_objet_loin': {'fr': 'objet à {d} km →', 'en': 'object at {d} km →'},
    'td_s_D': {'fr': 'D₁ = {d} km', 'en': 'D₁ = {d} km'},
    'td_s_R': {'fr': 'R = {r} km', 'en': 'R = {r} km'},
    'td_s_prof': {'fr': 'corde {p}° sous l’horizon', 'en': 'chord {p}° below the horizon'},
    'td_s_loupe': {'fr': 'Loupe (échelles différentes)', 'en': 'Magnifier (different scales)'},
    'td_s_fleche': {'fr': 'flèche {f} m', 'en': 'sagitta {f} m'},
    'td_detail_aide': {'fr': 'Les étapes du sujet, numérotées, avec vos nombres.',
                       'en': 'The steps of the practical, numbered, with your numbers.'},
    'td_calcul_en_cours': {'fr': 'Calcul…', 'en': 'Calculating…'},
    'td_calcul_fait': {'fr': 'Calcul fait.', 'en': 'Calculation done.'},
    # étapes
    'td_e1': {'fr': 'Relevés (Stellarium)', 'en': 'Readings (Stellarium)'},
    'td_e1_t': {'fr': 'h₁ = {h1}°, h₂ = {h2}° (azimuts : {az1}°, {az2}°).',
                'en': 'h₁ = {h1}°, h₂ = {h2}° (azimuths: {az1}°, {az2}°).'},
    'td_e2': {'fr': 'Parallaxe 2α', 'en': 'Parallax 2α'},
    'td_e2_t': {'fr': '2α = |h₁ − h₂| = {a}° = {r} rad (× π / 180).', 'en': '2α = |h₁ − h₂| = {a}° = {r} rad '
                                                                            '(× π / 180).'},
    'td_e2_entre': {'fr': 'L’objet est ENTRE les deux lieux : les visées se croisent au-dessus de la base, et la '
                          'formule du sujet (une différence) devient 2α = 180° − h₁ − h₂ = {a}° = {r} rad.',
                    'en': 'The object is BETWEEN the two places: the lines of sight cross above the baseline, and the '
                          'practical’s formula (a difference) becomes 2α = 180° − h₁ − h₂ = {a}° = {r} rad.'},
    'td_e3': {'fr': 'Distance R entre les lieux', 'en': 'Distance R between the places'},
    'td_e3_t': {'fr': 'À la surface (comme Google Earth) : {s} km. En ligne droite (corde, EarthLocation d’astropy, '
                      'WGS84) : {c} km, soit {e} m de moins. La corde passe sous le sol : flèche de {f} m au milieu '
                      '(≈ R²/(8 R⊕) = {fa} m) ; elle plonge de {p1}° et {p2}° sous l’horizon de chaque lieu.',
                'en': 'At the surface (like Google Earth): {s} km. In a straight line (chord, astropy EarthLocation, '
                      'WGS84): {c} km, {e} m shorter. The chord runs below the ground: sagitta of {f} m at the middle '
                      '(≈ R²/(8 R⊕) = {fa} m); it dips {p1}° and {p2}° below the horizon of each place.'},
    'td_e4': {'fr': 'Formule du sujet : D = R / 2α', 'en': 'Practical’s formula: D = R / 2α'},
    'td_e4_t': {'fr': 'D = {c} km / {a} rad = {dc} km (avec la corde) ; {ds} km avec la distance à la surface.',
                'en': 'D = {c} km / {a} rad = {dc} km (with the chord); {ds} km with the surface distance.'},
    'td_e5': {'fr': 'Calcul exact', 'en': 'Exact calculation'},
    'td_e5_t': {'fr': 'Les deux horizons ne sont pas parallèles : ils font {theta}° entre eux (angle au centre de la '
                      'Terre). Triangulation des visées ({mode}) : distances {d1} km et {d2} km, distance au centre '
                      'de la Terre {dg} km, altitude {alt} km ; angle entre les visées {p}°.',
                'en': 'The two horizons are not parallel: they make {theta}° between them (angle at the Earth’s '
                      'centre). Triangulation of the lines of sight ({mode}): distances {d1} km and {d2} km, distance '
                      'to the Earth’s centre {dg} km, altitude {alt} km; angle between the lines of sight {p}°.'},
    'td_mode_azimuts': {'fr': 'avec les azimuts', 'en': 'with the azimuths'},
    'td_mode_entre': {'fr': 'objet entre les lieux, dans leur plan vertical', 'en': 'object between the places, in '
                                                                                   'their vertical plane'},
    'td_mode_meme_cote': {'fr': 'objet du même côté, dans le plan vertical des lieux',
                          'en': 'object on the same side, in the places’ vertical plane'},
    'td_e6': {'fr': 'Éphéméride', 'en': 'Ephemeris'},
    'td_e6_lune': {'fr': 'Lune ({src}) : à {dg} km du centre de la Terre, à {d1} km et {d2} km des lieux ; élévations '
                         'prédites {h1}° et {h2}° sans réfraction ({hr1}° et {hr2}° avec).',
                   'en': 'Moon ({src}): {dg} km from the Earth’s centre, {d1} km and {d2} km from the places; '
                         'predicted elevations {h1}° and {h2}° without refraction ({hr1}° and {hr2}° with).'},
    'td_e6_iss': {'fr': 'ISS (TLE à {age} jours) : altitude {alt} km, à {d1} km et {d2} km des lieux ; élévations '
                        'prédites {h1}° et {h2}°.',
                  'en': 'ISS (TLE {age} days away): altitude {alt} km, {d1} km and {d2} km from the places; predicted '
                        'elevations {h1}° and {h2}°.'},
    'td_src_de440': {'fr': 'JPL DE440', 'en': 'JPL DE440'},
    'td_src_meeus': {'fr': 'Meeus', 'en': 'Meeus'},
    'td_e7': {'fr': 'Incertitudes', 'en': 'Uncertainties'},
    'td_e7_t': {'fr': 'Avec σ(h) = {sh}° (heure comprise) et l’incertitude des lieux : D (sujet) à ± {s} km, distance '
                      'exacte à ± {x} km.',
                'en': 'With σ(h) = {sh}° (time included) and the places’ uncertainty: D (practical) to ± {s} km, '
                      'exact distance to ± {x} km.'},
    # alertes et erreurs
    'td_a_inversion_certaine': {'fr': 'Lieu {n} : latitude et longitude échangées (latitude > 90°), corrigé.',
                                'en': 'Place {n}: latitude and longitude swapped (latitude > 90°), corrected.'},
    'td_a_inversion_probable': {'fr': 'Lieu {n} : latitude et longitude sans doute échangées (la base deviendrait '
                                      'raisonnable). Vérifiez.',
                                'en': 'Place {n}: latitude and longitude probably swapped (the baseline would become '
                                      'reasonable). Check.'},
    'td_a_inversion_un_des_deux': {'fr': 'Base énorme : latitude et longitude sans doute échangées pour l’un des deux '
                                         'lieux. Vérifiez.',
                                   'en': 'Huge baseline: latitude and longitude probably swapped for one of the two '
                                         'places. Check.'},
    'td_a_tle_ancien': {'fr': 'Le TLE est à {j} jours de l’instant : position de l’ISS approximative (plusieurs km, '
                              'davantage après une manœuvre). CelesTrak, source libre sans compte, ne publie que les '
                              'éléments du jour ; l’historique des TLE exige un compte Space-Track (gratuit, '
                              'personnel) : collez le TLE de la date pour une comparaison exacte.',
                        'en': 'The TLE is {j} days from the instant: approximate ISS position (several km, more after '
                              'a manoeuvre). CelesTrak, a free source with no account, only publishes current '
                              'elements; TLE history requires a Space-Track account (free, personal): paste the TLE '
                              'of that date for an exact comparison.'},
    'td_tle_auto': {'fr': 'TLE de l’ISS : récupéré tout seul pour l’instant donné (cache, sinon CelesTrak).',
                    'en': 'ISS TLE: fetched automatically for the given instant (cache, otherwise CelesTrak).'},
    'td_tle_recherche': {'fr': 'Récupération du TLE de l’ISS…', 'en': 'Fetching the ISS TLE…'},
    'td_a_sans_sgp4': {'fr': 'Prédiction de l’ISS indisponible (paquet sgp4 absent).',
                       'en': 'ISS prediction unavailable (sgp4 package missing).'},
    'td_a_lune_azimuts': {'fr': 'Lune sans azimuts : la Lune n’est en général pas dans le plan vertical des deux '
                                'lieux ; donnez les azimuts pour un calcul exact.',
                          'en': 'Moon without azimuths: the Moon is generally not in the vertical plane of both '
                                'places; give the azimuths for an exact calculation.'},
    'td_err_vide': {'fr': 'Champ vide.', 'en': 'Empty field.'},
    'td_err_illisible': {'fr': '« {texte} » : écriture non reconnue.', 'en': '“{texte}”: format not recognised.'},
    'td_err_minutes': {'fr': '« {texte} » : minutes ≥ 60.', 'en': '“{texte}”: minutes ≥ 60.'},
    'td_err_secondes': {'fr': '« {texte} » : secondes ≥ 60.', 'en': '“{texte}”: seconds ≥ 60.'},
    'td_err_signe': {'fr': '« {texte} » : signe et lettre contradictoires.', 'en': '“{texte}”: sign and letter '
                                                                                   'contradict each other.'},
    'td_err_deux_angles': {'fr': '« {texte} » : il faut deux angles, latitude et longitude.',
                           'en': '“{texte}”: two angles are needed, latitude and longitude.'},
    'td_err_deux_lat': {'fr': '« {texte} » : deux latitudes (N/S), pas de longitude.', 'en': '“{texte}”: two '
                                                                                            'latitudes (N/S), no '
                                                                                            'longitude.'},
    'td_err_deux_lon': {'fr': '« {texte} » : deux longitudes (E/O), pas de latitude.', 'en': '“{texte}”: two '
                                                                                            'longitudes (E/W), no '
                                                                                            'latitude.'},
    'td_err_latitude': {'fr': '« {texte} » : latitude impossible.', 'en': '“{texte}”: impossible latitude.'},
    'td_err_longitude': {'fr': '« {texte} » : longitude impossible.', 'en': '“{texte}”: impossible longitude.'},
    'td_err_altitude': {'fr': '« {texte} » : altitude illisible.', 'en': '“{texte}”: unreadable elevation.'},
    'td_err_instant': {'fr': '« {texte} » : date et heure illisibles (AAAA-MM-JJ HH:MM:SS).',
                       'en': '“{texte}”: unreadable date and time (YYYY-MM-DD HH:MM:SS).'},
    'td_err_h': {'fr': 'Lieu {n} : élévation manquante.', 'en': 'Place {n}: elevation missing.'},
    'td_err_hauteurs': {'fr': 'Les deux élévations sont nécessaires.', 'en': 'Both elevations are needed.'},
    'td_err_parallaxe_nulle': {'fr': 'Parallaxe nulle : les deux élévations sont égales.',
                               'en': 'Zero parallax: both elevations are equal.'},
    'td_err_meme_lieu': {'fr': 'Les deux lieux sont confondus.', 'en': 'The two places are the same.'},
    'td_err_derriere': {'fr': 'Les visées ne se croisent pas devant les observateurs (élévations, azimuts ou position '
                              'de l’objet à revoir).',
                        'en': 'The lines of sight do not cross in front of the observers (check the elevations, '
                              'azimuths or object position).'},
    'td_err_tle': {'fr': 'TLE illisible ou hors de sa période de validité.', 'en': 'TLE unreadable or outside its '
                                                                                  'validity.'},
    # export
    'td_x_grandeur': {'fr': 'Grandeur', 'en': 'Quantity'},
    'td_x_valeur': {'fr': 'Valeur', 'en': 'Value'},
    'td_x_unite': {'fr': 'Unité', 'en': 'Unit'},
    'td_x_lat1': {'fr': 'Latitude du lieu 1', 'en': 'Latitude of place 1'},
    'td_x_lon1': {'fr': 'Longitude du lieu 1', 'en': 'Longitude of place 1'},
    'td_x_h1': {'fr': 'Élévation h₁', 'en': 'Elevation h₁'},
    'td_x_lat2': {'fr': 'Latitude du lieu 2', 'en': 'Latitude of place 2'},
    'td_x_lon2': {'fr': 'Longitude du lieu 2', 'en': 'Longitude of place 2'},
    'td_x_h2': {'fr': 'Élévation h₂', 'en': 'Elevation h₂'},
    'td_x_2alpha': {'fr': 'Parallaxe 2α', 'en': 'Parallax 2α'},
    'td_x_2alpha_rad': {'fr': 'Parallaxe 2α (radians)', 'en': 'Parallax 2α (radians)'},
    'td_x_surface': {'fr': 'Distance à la surface', 'en': 'Surface distance'},
    'td_x_corde': {'fr': 'Corde R', 'en': 'Chord R'},
    'td_x_fleche': {'fr': 'Flèche (corde – surface)', 'en': 'Sagitta (chord – surface)'},
    'td_x_D_surface': {'fr': 'D = R/2α (surface)', 'en': 'D = R/2α (surface)'},
    'td_x_D_corde': {'fr': 'D = R/2α (corde)', 'en': 'D = R/2α (chord)'},
    'td_x_theta': {'fr': 'Angle entre les horizons', 'en': 'Angle between the horizons'},
    'td_x_d1': {'fr': 'Distance exacte au lieu 1', 'en': 'Exact distance to place 1'},
    'td_x_d2': {'fr': 'Distance exacte au lieu 2', 'en': 'Exact distance to place 2'},
    'td_x_dgeo': {'fr': 'Distance au centre de la Terre', 'en': 'Distance to the Earth’s centre'},
    'td_x_alt': {'fr': 'Altitude de l’objet', 'en': 'Altitude of the object'},
    # ligne de commande
    'td_cli_p': {'fr': 'position du lieu {n} (n’importe quelle écriture)', 'en': 'position of place {n} (any '
                                                                               'format)'},
    'td_cli_h': {'fr': 'élévation mesurée au lieu {n}', 'en': 'elevation measured at place {n}'},
    'td_cli_az': {'fr': 'azimut mesuré au lieu {n} (facultatif)', 'en': 'azimuth measured at place {n} (optional)'},
    'td_cli_alt': {'fr': 'altitude du lieu {n}', 'en': 'elevation of place {n}'},
    'td_cli_cible': {'fr': 'cible : iss ou lune', 'en': 'target: iss or moon'},
    'td_cli_instant': {'fr': 'date et heure TU (comparaison à l’éphéméride)', 'en': 'date and time UT (ephemeris '
                                                                                   'comparison)'},
    'td_cli_parallaxe': {'fr': 'calculateur « Parallaxe (TP du cours) »', 'en': '“Parallax (course practical)” '
                                                                                'calculator'},
    'td_meta_texte': {'fr': 'TEXTE', 'en': 'TEXT'},
    # aide
    'td_aide_html': {
        'fr': '<h3>Calculateurs de TD</h3><p>Chaque calculateur suit la démarche d’un TD ou d’un TP du cours, pas à '
              'pas, avec VOS nombres, puis montre le calcul exact et dit ce qui change.</p>'
              '<h4>Parallaxe (TP du cours)</h4><ol><li><b>Relevés</b> : élévations h₁ et h₂ de l’ISS (ou de la Lune) '
              'au même instant depuis deux lieux, lues dans Stellarium (et, si possible, les azimuts).</li>'
              '<li><b>Parallaxe</b> : 2α = h₁ − h₂ (objet vu du même côté) ; si l’objet est ENTRE les deux lieux, les '
              'visées se croisent et 2α = 180° − h₁ − h₂.</li><li><b>Distance R</b> entre les lieux : à la surface '
              '(Google Earth) ou en ligne droite (la corde, EarthLocation d’astropy). La corde passe sous le sol : '
              'sa flèche vaut ≈ R²/(8 R⊕), 3 km pour 400 km.</li><li><b>D = R / 2α</b>, 2α en radians.</li></ol>'
              '<p><b>Le calcul exact</b> tient compte de la courbure : les deux horizons font entre eux l’angle au '
              'centre θ (4,5° pour 500 km). Pour la Lune, la différence h₁ − h₂ est presque entièrement due à θ : la '
              'formule du sujet appliquée aux élévations donne des milliers de km au lieu de 380 000 ; c’est pourquoi '
              'le TP de la Lune mesure la distance Lune–étoile. Avec les azimuts, les visées sont triangulées dans '
              'l’espace ; sinon l’objet est supposé dans le plan vertical des deux lieux.</p><p>Avec l’heure : '
              'éphéméride (Lune : JPL DE440 téléchargée une fois, sinon Meeus ; ISS : TLE de CelesTrak, l’historique '
              'des TLE n’étant pas librement disponible) et élévations prédites à comparer. Incertitudes propagées '
              '(élévations, lieux, heure). La réfraction (≈ 34′ à l’horizon) et l’épaisseur d’air traversée sont '
              'expliquées par l’animation « L’atmosphère terrestre » (thème Télescopes). « Exemple » : données fictives. « Exporter le détail » : pour la feuille '
              '« Calculs » du partage.</p>',
        'en': '<h3>Course calculators</h3><p>Each calculator follows the approach of an exercise or practical of the '
              'course, step by step, with YOUR numbers, then shows the exact calculation and what changes.</p>'
              '<h4>Parallax (course practical)</h4><ol><li><b>Readings</b>: elevations h₁ and h₂ of the ISS (or of '
              'the Moon) at the same instant from two places, read in Stellarium (and, if possible, the azimuths).'
              '</li><li><b>Parallax</b>: 2α = h₁ − h₂ (object seen on the same side); if the object is BETWEEN the '
              'places, the lines of sight cross and 2α = 180° − h₁ − h₂.</li><li><b>Distance R</b> between the '
              'places: at the surface (Google Earth) or in a straight line (the chord, astropy EarthLocation). The '
              'chord runs below the ground: its sagitta is ≈ R²/(8 R⊕), 3 km for 400 km.</li><li><b>D = R / 2α</b>, '
              '2α in radians.</li></ol><p><b>The exact calculation</b> accounts for curvature: the two horizons make '
              'the angle θ at the Earth’s centre (4.5° for 500 km). For the Moon, the difference h₁ − h₂ is almost '
              'entirely due to θ: the practical’s formula applied to elevations gives thousands of km instead of '
              '380,000; that is why the Moon practical measures the Moon–star distance. With azimuths, the lines of '
              'sight are triangulated in space; otherwise the object is assumed in the vertical plane of both places.'
              '</p><p>With the time: ephemeris (Moon: JPL DE440 downloaded once, otherwise Meeus; ISS: CelesTrak TLE, '
              'TLE history not being freely available) and predicted elevations to compare. Propagated '
              'uncertainties (elevations, places, time). Refraction (≈ 34′ at the horizon) and the thickness of air crossed are '
              'explained by the “Earth’s atmosphere” animation (Telescopes theme). “Example”: fictitious data. “Export the details”: for the '
              '“Calculs” sheet of the share.</p>'},
}
