"""Textes FR/EN du « Planificateur de parallaxe » (rubrique Calculateurs de TD)."""
from __future__ import annotations

TEXTES_PLANIF = {
    'td_calc_planif': {'fr': 'Planificateur de parallaxe', 'en': 'Parallax planner'},
    'td_calc_planif_aide': {'fr': 'Trouve les dates et heures où deux observateurs peuvent mesurer ensemble la '
                                  'parallaxe de l’ISS ou de la Lune, et les classe du plus facile au plus difficile.',
                            'en': 'Finds the dates and times when two observers can measure the parallax of the ISS '
                                  'or the Moon together, ranked from easiest to hardest.'},
    'pl_intro': {'fr': 'Donnez les deux lieux : le planificateur cherche les passages de l’ISS (ou les soirées de Lune) '
                       'visibles des DEUX lieux, haut et dans un ciel noir, et les classe. Il privilégie les cas où '
                       'l’objet passe dans le plan vertical commun des deux lieux, là où la formule simple du sujet '
                       'marche ; pour chaque créneau, il dit l’erreur que ferait cette formule et la précision '
                       'd’horloge nécessaire. Dépouillez ensuite la mesure avec « Parallaxe (TP du cours) ».',
                 'en': 'Give the two places: the planner looks for ISS passes (or Moon evenings) visible from BOTH '
                       'places, high and in a dark sky, and ranks them. It favours cases where the object crosses the '
                       'common vertical plane of the two places, where the simple formula of the practical works; for '
                       'each slot it gives the error that formula would make and the clock accuracy needed. Then '
                       'reduce the measurement with “Parallax (course practical)”.'},
    'pl_cible': {'fr': 'Objet', 'en': 'Object'},
    'pl_cible_aide': {'fr': 'ISS : passages des prochains jours (le TLE ne vaut que quelques jours). Lune : soirées '
                            'des prochains mois avec une étoile de repère près de la Lune.',
                      'en': 'ISS: passes over the next days (a TLE is only good for a few days). Moon: evenings over '
                            'the next months with a reference star near the Moon.'},
    'pl_lieu': {'fr': 'Lieu {n}', 'en': 'Place {n}'},
    'pl_nom': {'fr': 'Nom', 'en': 'Name'},
    'pl_nom_aide': {'fr': 'Un nom court pour vous y retrouver (facultatif).', 'en': 'A short name (optional).'},
    'pl_nom_indice': {'fr': 'ex. Lyon', 'en': 'e.g. Lyon'},
    'pl_debut': {'fr': 'À partir du', 'en': 'From'},
    'pl_debut_aide': {'fr': 'Début de la recherche (UTC), « AAAA-MM-JJ » ou « AAAA-MM-JJ HH:MM » ; vide : maintenant.',
                      'en': 'Start of the search (UTC), “YYYY-MM-DD” or “YYYY-MM-DD HH:MM”; empty: now.'},
    'pl_debut_indice': {'fr': 'vide = maintenant', 'en': 'empty = now'},
    'pl_jours': {'fr': 'Durée', 'en': 'Span'},
    'pl_jours_aide': {'fr': 'Nombre de jours explorés (ISS : 14 au plus, le TLE vieillit ; Lune : 400 au plus).',
                      'en': 'Number of days searched (ISS: at most 14, the TLE ages; Moon: at most 400).'},
    'pl_unite_j': {'fr': 'j', 'en': 'd'},
    'pl_hmin': {'fr': 'Hauteur minimale', 'en': 'Minimum elevation'},
    'pl_hmin_aide': {'fr': 'Hauteur minimale de l’objet, vue des DEUX lieux.',
                     'en': 'Minimum elevation of the object, seen from BOTH places.'},
    'pl_soleil': {'fr': 'Soleil au plus à', 'en': 'Sun at most at'},
    'pl_soleil_aide': {'fr': 'Hauteur maximale du Soleil aux deux lieux : −6° fin du crépuscule civil, −12° nautique, '
                             '−18° nuit noire. L’ISS se voit surtout en début et fin de nuit.',
                       'en': 'Maximum Sun elevation at both places: −6° end of civil twilight, −12° nautical, −18° '
                             'full night. The ISS is mostly seen early and late in the night.'},
    'pl_mag': {'fr': 'Étoile au plus de magnitude', 'en': 'Star at most of magnitude'},
    'pl_mag_aide': {'fr': 'Étoile de repère (Lune) : magnitude maximale.', 'en': 'Reference star (Moon): faintest magnitude.'},
    'pl_sep': {'fr': 'Étoile à moins de', 'en': 'Star within'},
    'pl_sep_aide': {'fr': 'Distance maximale entre le centre de la Lune et l’étoile de repère (selon le champ de votre '
                          'instrument).',
                    'en': 'Maximum distance between the Moon’s centre and the reference star (depends on your field '
                          'of view).'},
    'pl_phase': {'fr': 'Lune éclairée au plus à', 'en': 'Moon lit at most'},
    'pl_phase_aide': {'fr': 'Fraction éclairée maximale : une Lune pleine éblouit et noie les étoiles voisines.',
                      'en': 'Maximum illuminated fraction: a full Moon dazzles and drowns nearby stars.'},
    'pl_unite_pct': {'fr': '%', 'en': '%'},
    'pl_locale': {'fr': 'Heures de cet ordinateur', 'en': 'This computer’s time zone'},
    'pl_locale_aide': {'fr': 'Afficher les heures dans le fuseau de cet ordinateur au lieu de l’UTC.',
                       'en': 'Show times in this computer’s time zone instead of UTC.'},
    'pl_chercher': {'fr': 'Chercher', 'en': 'Search'},
    'pl_chercher_aide': {'fr': 'Lancer la recherche des créneaux.', 'en': 'Search for slots.'},
    'pl_exemple': {'fr': 'Exemple', 'en': 'Example'},
    'pl_exemple_aide': {'fr': 'Deux lieux d’exemple (Paris et Lyon).', 'en': 'Two example places (Paris and Lyon).'},
    'pl_csv': {'fr': 'Exporter (CSV)', 'en': 'Export (CSV)'},
    'pl_csv_aide': {'fr': 'Enregistrer la liste des créneaux en tableau CSV.', 'en': 'Save the slots as a CSV table.'},
    'pl_ics': {'fr': 'Agenda (.ics)', 'en': 'Calendar (.ics)'},
    'pl_ics_aide': {'fr': 'Enregistrer les créneaux dans un fichier d’agenda à importer et à envoyer à votre binôme.',
                    'en': 'Save the slots as a calendar file to import and send to your partner.'},
    'pl_tableau_aide': {'fr': 'Créneaux du plus facile au plus difficile. Cliquez sur une ligne pour le détail.',
                        'en': 'Slots from easiest to hardest. Click a row for details.'},
    'pl_col_date': {'fr': 'Date', 'en': 'Date'},
    'pl_col_heure': {'fr': 'Meilleur instant', 'en': 'Best time'},
    'pl_col_note': {'fr': 'Note', 'en': 'Score'},
    'pl_col_h': {'fr': 'Hauteurs', 'en': 'Elevations'},
    'pl_col_mesure': {'fr': 'Parallaxe', 'en': 'Parallax'},
    'pl_col_sujet': {'fr': 'Erreur formule', 'en': 'Formula error'},
    'pl_col_infos': {'fr': 'Remarques', 'en': 'Notes'},
    'pl_ciel_aide': {'fr': 'Le ciel de chaque lieu (centre : zénith, bord : horizon) : trajectoire de l’objet pendant le '
                           'créneau, point au meilleur instant.',
                     'en': 'Each place’s sky (centre: zenith, edge: horizon): the object’s track during the slot, dot at '
                           'the best time.'},
    'pl_detail_aide': {'fr': 'Détail du créneau choisi.', 'en': 'Details of the chosen slot.'},
    'pl_N': {'fr': 'N', 'en': 'N'}, 'pl_E': {'fr': 'E', 'en': 'E'}, 'pl_S': {'fr': 'S', 'en': 'S'},
    'pl_O': {'fr': 'O', 'en': 'W'},
    'pl_en_cours': {'fr': 'Recherche en cours…', 'en': 'Searching…'},
    'pl_fini': {'fr': '{n} créneau(x) trouvé(s) du {debut} au {fin} (base {base} km ; éphéméride : {source}).',
                'en': '{n} slot(s) found from {debut} to {fin} (baseline {base} km; ephemeris: {source}).'},
    'pl_aucun': {'fr': 'Aucun créneau : élargissez la durée, baissez la hauteur minimale ou acceptez un ciel moins noir.',
                 'en': 'No slot: widen the span, lower the minimum elevation or accept a lighter sky.'},
    'pl_exporte': {'fr': 'Enregistré : {chemin}', 'en': 'Saved: {chemin}'},
    'pl_tle_info': {'fr': 'TLE de l’ISS : époque {date} ({source}).', 'en': 'ISS TLE: epoch {date} ({source}).'},
    'pl_err_tle': {'fr': 'Pas de TLE de l’ISS (hors ligne ?) : récupérez-en un dans « Parallaxe (TP du cours) » ou '
                         'collez-le. {erreur}',
                   'en': 'No ISS TLE (offline?): fetch one in “Parallax (course practical)” or paste it. {erreur}'},
    'pl_err_cible': {'fr': 'Objet inconnu.', 'en': 'Unknown object.'},
    'pl_err_lieu': {'fr': 'Latitude hors de −90° à +90°.', 'en': 'Latitude outside −90° to +90°.'},
    'pl_err_lieux': {'fr': 'Donnez les deux lieux.', 'en': 'Give both places.'},
    'pl_err_debut': {'fr': 'Date de début illisible : « {texte} ».', 'en': 'Unreadable start date: “{texte}”.'},
    'pl_a_tle_vieux': {'fr': 'Le TLE aura plus de 5 jours à la fin de la période : les heures des derniers jours peuvent '
                             'glisser de plusieurs secondes ; relancez la recherche la veille.',
                       'en': 'The TLE will be over 5 days old by the end of the span: times on the last days may drift '
                             'by several seconds; search again the day before.'},
    'pl_r_meme_cote': {'fr': 'même côté', 'en': 'same side'},
    'pl_r_hors_plan': {'fr': 'hors du plan commun', 'en': 'off the common plane'},
    'pl_r_faible': {'fr': 'ISS peu brillante', 'en': 'faint ISS'},
    'pl_r_lune_faible': {'fr': 'parallaxe faible vers l’étoile', 'en': 'small parallax towards the star'},
    'pl_r_lune_pleine': {'fr': 'Lune très éclairée', 'en': 'bright Moon'},
    'pl_tendance': {'fr': 'Tendance sur 90 jours (heures indicatives)', 'en': '90-day outlook (approximate times)'},
    'pl_tendance_aide': {'fr': 'ISS : chercher jusqu’à 90 jours avec le TLE du jour. Les soirs de passage restent justes '
                               'des semaines ; l’heure dérive d’environ 4 s par jour d’âge du TLE (marge affichée). '
                               'Classement par date. Relancer la recherche précise 2 ou 3 jours avant.',
                         'en': 'ISS: search up to 90 days with today’s TLE. The evenings with passes stay right for weeks; '
                               'the time drifts by about 4 s per day of TLE age (margin shown). Sorted by date. Run the '
                               'precise search again 2 or 3 days before.'},
    'pl_a_tendance': {'fr': 'Tendance : les dates et les soirs sont fiables, les heures sont à ± la marge indiquée ; '
                            'relancez la recherche précise 2 ou 3 jours avant.',
                      'en': 'Outlook: dates and evenings are reliable, times are within ± the margin shown; run the '
                            'precise search again 2 or 3 days before.'},
    'pl_r_indicatif': {'fr': 'heure indicative', 'en': 'approximate time'},
    'pl_d_marge': {'fr': 'Heure indicative à ± {m} min (âge du TLE à cette date : {a} jours) : relancez la recherche '
                         'précise 2 ou 3 jours avant.',
                   'en': 'Approximate time, ± {m} min (TLE age at that date: {a} days): run the precise search again '
                         '2 or 3 days before.'},
    'pl_cli_tendance': {'fr': 'ISS : tendance jusqu’à 90 jours (heures indicatives)', 'en': 'ISS: outlook up to 90 days (approximate times)'},
    # choix d'un lieu (carte, adresse)
    'lieu_bouton': {'fr': 'Carte / adresse…', 'en': 'Map / address…'},
    'lieu_bouton_aide': {'fr': 'Choisir le lieu sur une carte ou par son adresse ; remplit la position et l’altitude.',
                         'en': 'Pick the place on a map or by its address; fills in the position and the elevation.'},
    'lieu_titre': {'fr': 'Choisir un lieu', 'en': 'Choose a place'},
    'lieu_intro': {'fr': 'Cliquez sur la carte (glisser pour la déplacer, molette pour zoomer), ou tapez une adresse, '
                         'une ville, un lieu-dit puis « Chercher ». L’altitude du terrain est ajoutée toute seule.',
                   'en': 'Click on the map (drag to move it, wheel to zoom), or type an address, a town or a place '
                         'name then “Search”. The ground elevation is added automatically.'},
    'lieu_adresse': {'fr': 'Adresse ou lieu', 'en': 'Address or place'},
    'lieu_adresse_aide': {'fr': 'Adresse, ville, observatoire… Elle est envoyée au service Nominatim '
                                '(OpenStreetMap) quand vous cliquez sur « Chercher », et seulement alors.',
                          'en': 'Address, town, observatory… It is sent to the Nominatim service (OpenStreetMap) '
                                'when you click “Search”, and only then.'},
    'lieu_adresse_indice': {'fr': 'ex. 61 avenue de l’Observatoire, Paris', 'en': 'e.g. Royal Observatory, Greenwich'},
    'lieu_chercher': {'fr': 'Chercher', 'en': 'Search'},
    'lieu_chercher_aide': {'fr': 'Chercher cette adresse (OpenStreetMap).', 'en': 'Look up this address (OpenStreetMap).'},
    'lieu_resultats_aide': {'fr': 'Lieux trouvés : choisissez le bon, puis affinez d’un clic sur la carte si besoin.',
                            'en': 'Places found: pick the right one, then refine with a click on the map if needed.'},
    'lieu_carte_aide': {'fr': 'Cliquez pour poser le lieu ; glissez pour déplacer la carte ; molette : zoom.',
                        'en': 'Click to set the place; drag to move the map; wheel: zoom.'},
    'lieu_aucun': {'fr': 'Aucun lieu choisi.', 'en': 'No place chosen.'},
    'lieu_point': {'fr': 'Lieu choisi', 'en': 'Chosen place'},
    'lieu_recherche': {'fr': 'Recherche…', 'en': 'Searching…'},
    'lieu_rien': {'fr': 'Rien trouvé : essayez une autre écriture, ou cliquez sur la carte.',
                  'en': 'Nothing found: try another spelling, or click on the map.'},
    'lieu_erreur': {'fr': 'Recherche impossible (hors ligne ?) : {erreur}', 'en': 'Search failed (offline?): {erreur}'},
    'lieu_alt_inconnue': {'fr': 'altitude inconnue (à saisir)', 'en': 'elevation unknown (type it in)'},
    'lieu_choisi': {'fr': 'Lieu : <b>{pos}</b> — altitude {alt} — {nom}', 'en': 'Place: <b>{pos}</b> — elevation {alt} — {nom}'},
    'lieu_utiliser': {'fr': 'Utiliser ce lieu', 'en': 'Use this place'},
    'lieu_utiliser_aide': {'fr': 'Remplir la position et l’altitude avec ce lieu.', 'en': 'Fill in the position and elevation with this place.'},
    'lieu_attribution': {'fr': 'Carte et adresses © contributeurs d’<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> ; '
                               'altitude : <a href="https://open-meteo.com/">Open-Meteo</a> (Copernicus DEM GLO-90).',
                         'en': 'Map and addresses © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors; '
                               'elevation: <a href="https://open-meteo.com/">Open-Meteo</a> (Copernicus DEM GLO-90).'},
    # détail
    'pl_d_titre_iss': {'fr': 'Passage de l’ISS du {date}', 'en': 'ISS pass on {date}'},
    'pl_d_titre_lune': {'fr': 'La Lune le {date}', 'en': 'The Moon on {date}'},
    'pl_d_creneau': {'fr': 'Visible des deux lieux de {debut} à {fin} ; meilleur instant <b>{meilleur}</b> (note '
                           '{note}/100).',
                     'en': 'Visible from both places from {debut} to {fin}; best time <b>{meilleur}</b> (score '
                           '{note}/100).'},
    'pl_d_lieu': {'fr': '{nom} : hauteur {h}°, azimut {az}°, distance {d} km, Soleil à {s}°',
                  'en': '{nom}: elevation {h}°, azimuth {az}°, distance {d} km, Sun at {s}°'},
    'pl_d_mag': {'fr': ', magnitude {m}', 'en': ', magnitude {m}'},
    'pl_d_parallaxe': {'fr': 'Parallaxe vraie (angle entre les deux visées) : <b>{p}°</b>. Altitude de l’ISS : {alt} km.',
                       'en': 'True parallax (angle between the two lines of sight): <b>{p}°</b>. ISS altitude: {alt} km.'},
    'pl_d_plan': {'fr': 'Écart au plan vertical commun des deux lieux : {e}° ; l’ISS est {ou}.',
                  'en': 'Offset from the common vertical plane of the two places: {e}°; the ISS is {ou}.'},
    'pl_d_entre': {'fr': 'ENTRE les deux lieux (chacun la voit du côté de l’autre)',
                   'en': 'BETWEEN the two places (each sees it on the other’s side)'},
    'pl_d_cote': {'fr': 'du MÊME CÔTÉ pour les deux lieux', 'en': 'on the SAME SIDE for both places'},
    'pl_d_sujet': {'fr': 'Formule du sujet (D = R / 2α) : erreur de <b>{e} %</b> sur la distance à cet instant.',
                   'en': 'Formula of the practical (D = R / 2α): <b>{e} %</b> error on the distance at this time.'},
    'pl_d_sujet_na': {'fr': 'Formule du sujet : inapplicable (2α nul).', 'en': 'Formula of the practical: not applicable (2α is zero).'},
    'pl_d_synchro_iss': {'fr': 'L’ISS se déplace de {v}°/s : un décalage d’horloge de <b>{s} s</b> entre les deux '
                               'observateurs fausse déjà la parallaxe de 1 %. Synchronisez les montres (GPS, horloge '
                               'radio) et notez l’heure de chaque pose.',
                         'en': 'The ISS moves {v}°/s: a clock offset of <b>{s} s</b> between the two observers '
                               'already spoils the parallax by 1 %. Synchronise the clocks (GPS, radio clock) and note '
                               'the time of each exposure.'},
    'pl_d_etoiles': {'fr': 'Étoiles brillantes près de l’ISS (lieu 1) : {liste}.', 'en': 'Bright stars near the ISS (place 1): {liste}.'},
    'pl_d_phase': {'fr': 'Lune éclairée à {p} %.', 'en': 'Moon {p} % lit.'},
    'pl_d_etoile': {'fr': 'Étoile de repère : <b>{nom}</b> (magnitude {V}) ; distance Lune–étoile φ₁ = {p1}° au lieu 1, '
                          'φ₂ = {p2}° au lieu 2 ; <b>Δφ = {d}′</b> (au mieux {i}′ pour cette base).',
                    'en': 'Reference star: <b>{nom}</b> (magnitude {V}); Moon–star distance φ₁ = {p1}° at place 1, '
                          'φ₂ = {p2}° at place 2; <b>Δφ = {d}′</b> (at best {i}′ for this baseline).'},
    'pl_d_sujet_lune': {'fr': 'Formule du sujet (D = R / Δφ) : la distance sortirait surestimée de <b>{e} %</b> '
                              '(Δφ n’atteint l’idéal que si la base est alignée avec la direction Lune–étoile).',
                        'en': 'Formula of the practical (D = R / Δφ): the distance would come out <b>{e} %</b> too large '
                              '(Δφ only reaches the ideal when the baseline lines up with the Moon–star direction).'},
    'pl_d_synchro_lune': {'fr': 'La Lune ne glisse devant les étoiles que d’environ 0,5″/s : un décalage de {s} s entre '
                                'les deux photos fausse Δφ de 1 %. Il faut surtout mesurer φ à quelques secondes '
                                'd’arc près (focale, astrométrie).',
                          'en': 'The Moon only slides in front of the stars by about 0.5″/s: an offset of {s} s between '
                                'the two photos spoils Δφ by 1 %. Above all, φ must be measured to a few arcseconds '
                                '(focal length, astrometry).'},
    'pl_d_remarques': {'fr': 'Remarques : {liste}.', 'en': 'Notes: {liste}.'},
    'pl_d_conseil': {'fr': 'Ensuite : notez h₁, h₂ (et les azimuts) au même instant, puis dépouillez dans « Parallaxe '
                           '(TP du cours) », qui fait aussi le calcul exact.',
                     'en': 'Then: note h₁, h₂ (and the azimuths) at the same time, then reduce in “Parallax (course '
                           'practical)”, which also does the exact calculation.'},
    'pl_aide_html': {'fr': '<h3>Planificateur de parallaxe</h3><p>Il cherche, pour deux lieux, les créneaux où l’objet '
                           'est visible des deux à la fois : hauteur minimale atteinte aux deux lieux, Soleil assez bas '
                           'aux deux lieux, ISS éclairée par le Soleil (ombre de la Terre), Lune pas trop éclairée et '
                           'étoile de repère assez proche et brillante.</p><p><b>La note</b> (sur 100) monte quand les '
                           'deux voient l’objet haut, quand l’objet passe près du plan vertical commun des deux lieux '
                           '(c’est là que la formule simple du sujet marche) et quand la parallaxe est grande. Pour la '
                           'Lune, elle mesure Δφ = φ₁ − φ₂ (la différence de distance Lune–étoile entre les deux lieux) '
                           'rapporté au meilleur Δφ possible, R / D.</p><p><b>Erreur de la formule</b> : l’écart entre '
                           'la distance que donnerait la formule du sujet et la vraie distance. Quand l’ISS ne passe pas '
                           'entre les deux observateurs ou s’écarte du plan commun, cette erreur grandit : choisissez '
                           'les créneaux où elle est faible, ou dépouillez avec le calcul exact (azimuts notés).</p>'
                           '<p><b>Calculs</b> : ISS par TLE (CelesTrak, ou ARISS si CelesTrak ne répond pas) et SGP4 ; '
                           'Lune par JPL DE440 si le fichier est là, sinon ERFA ; Soleil par ERFA ; étoiles du Yale '
                           'Bright Star Catalogue (V ≤ 5,5). Contrôlés par skyfield (écart ≤ 0,1° pour l’ISS, 0,01° '
                           'pour la Lune) : c’est la précision d’un planning.</p><p><b>Agenda</b> : un fichier .ics à '
                           'importer et à envoyer à votre binôme.</p>',
                     'en': '<h3>Parallax planner</h3><p>For two places, it looks for slots when the object is visible '
                           'from both at once: minimum elevation reached at both places, Sun low enough at both places, '
                           'ISS lit by the Sun (Earth’s shadow), Moon not too bright and a reference star close and '
                           'bright enough.</p><p><b>The score</b> (out of 100) rises when both see the object high, '
                           'when the object crosses near the common vertical plane of the two places (where the simple '
                           'formula of the practical works) and when the parallax is large. For the Moon it measures '
                           'Δφ = φ₁ − φ₂ (the difference in Moon–star distance between the two places) against the best '
                           'possible Δφ, R / D.</p><p><b>Formula error</b>: the gap between the distance the '
                           'practical’s formula would give and the true distance. When the ISS does not pass between '
                           'the two observers or leaves the common plane, this error grows: pick slots where it is '
                           'small, or reduce with the exact calculation (azimuths noted).</p><p><b>Computation</b>: ISS '
                           'from a TLE (CelesTrak, or ARISS when CelesTrak does not answer) and SGP4; Moon from JPL '
                           'DE440 when the file is present, otherwise ERFA; Sun from ERFA; stars from the Yale Bright '
                           'Star Catalogue (V ≤ 5.5). Checked against skyfield (within 0.1° for the ISS, 0.01° for the '
                           'Moon): planning accuracy.</p><p><b>Calendar</b>: an .ics file to import and send to your '
                           'partner.</p>'},
    # ligne de commande
    'pl_cli': {'fr': 'Planificateur de parallaxe : créneaux où deux lieux voient ensemble l’ISS ou la Lune.',
               'en': 'Parallax planner: slots when two places see the ISS or the Moon together.'},
    'pl_cli_p': {'fr': 'Position du lieu {n} (latitude, longitude)', 'en': 'Position of place {n} (latitude, longitude)'},
    'pl_cli_jours': {'fr': 'Nombre de jours', 'en': 'Number of days'},
    'pl_cli_debut': {'fr': 'Début (UTC), AAAA-MM-JJ[ HH:MM]', 'en': 'Start (UTC), YYYY-MM-DD[ HH:MM]'},
    'pl_cli_ics': {'fr': 'Écrire aussi un agenda .ics à ce chemin', 'en': 'Also write an .ics calendar to this path'},
    'pl_cli_ligne': {'fr': '{date}  note {note:>3}  h {h1}°/{h2}°  {mesure}  erreur formule {err}  {infos}',
                     'en': '{date}  score {note:>3}  h {h1}°/{h2}°  {mesure}  formula error {err}  {infos}'},
}
