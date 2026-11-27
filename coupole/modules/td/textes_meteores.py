"""Textes FR/EN du calculateur « Pluies de météores » (rubrique Calculateurs de TD)."""
from __future__ import annotations

TEXTES_METEORES = {
    'td_calc_meteores': {'fr': 'Pluies de météores', 'en': 'Meteor showers'},
    'td_calc_meteores_aide': {
        'fr': 'Calendrier des pluies (IMO), nuit d’observation à votre lieu (radiant, Lune, taux attendu, champ à '
              'viser), meilleures nuits d’une campagne et calcul du ZHR de vos comptages : le TP « Observation des '
              'météores ».',
        'en': 'Shower calendar (IMO), observing night at your place (radiant, Moon, expected rate, field to aim at), '
              'best nights of a campaign and ZHR of your counts: the “Meteor observation” practical.'},
    'mt_intro': {
        'fr': 'Pour le TP « Observation des météores » : choisissez votre lieu, puis le calendrier des pluies, une '
              'nuit (hauteur du radiant heure par heure, Lune, nombre de météores attendus, où regarder), une '
              'campagne (les meilleures nuits jusqu’à la date du rapport) ou la réduction de vos comptages '
              '(ZHR et indice de population r, comme dans le cours).',
        'en': 'For the “Meteor observation” practical: choose your place, then the shower calendar, a night (radiant '
              'altitude hour by hour, Moon, expected number of meteors, where to look), a campaign (the best nights '
              'until the report deadline) or the reduction of your counts (ZHR and population index r, as in the '
              'course).'},
    'mt_lieu': {'fr': 'Lieu d’observation', 'en': 'Observing place'},
    'mt_lm': {'fr': 'Magnitude limite', 'en': 'Limiting magnitude'},
    'mt_lm_aide': {'fr': 'Magnitude des étoiles les plus faibles visibles à l’œil nu sur votre site (6,5 : ciel '
                         'parfait ; 5 à 6 : campagne ; 4 : banlieue). Le nombre de météores vus en dépend beaucoup.',
                   'en': 'Magnitude of the faintest stars visible to the naked eye at your site (6.5: perfect sky; '
                         '5 to 6: countryside; 4: suburbs). The number of meteors seen depends strongly on it.'},
    'mt_f': {'fr': 'Ciel dégagé (F)', 'en': 'Clear sky (F)'},
    'mt_f_aide': {'fr': 'Fraction du champ de vue non masquée (arbres, nuages) : 1 = rien ne gêne.',
                  'en': 'Fraction of the field of view not obstructed (trees, clouds): 1 = nothing in the way.'},
    'mt_locale': {'fr': 'Heures locales', 'en': 'Local times'},
    'mt_locale_aide': {'fr': 'Heures dans le fuseau de cet ordinateur ; sinon en UTC (temps universel), comme dans '
                             'le calendrier de l’IMO et les rapports.',
                       'en': 'Times in this computer’s time zone; otherwise UTC, as in the IMO calendar and '
                             'reports.'},
    'mt_onglet_calendrier': {'fr': 'Calendrier', 'en': 'Calendar'},
    'mt_onglet_nuit': {'fr': 'Une nuit', 'en': 'One night'},
    'mt_onglet_campagne': {'fr': 'Campagne', 'en': 'Campaign'},
    'mt_onglet_reduction': {'fr': 'Réduction (ZHR)', 'en': 'Reduction (ZHR)'},
    'mt_onglet_calendrier_aide': {'fr': 'Les pluies de l’année : activité, maximum, ZHR, radiant.',
                                  'en': 'The showers of the year: activity, maximum, ZHR, radiant.'},
    'mt_onglet_nuit_aide': {'fr': 'Une nuit à votre lieu : radiant, Lune, météores attendus, où regarder.',
                            'en': 'One night at your place: radiant, Moon, expected meteors, where to look.'},
    'mt_onglet_campagne_aide': {'fr': 'Les meilleures nuits d’une période, avec agenda .ics.',
                                'en': 'The best nights of a period, with an .ics calendar.'},
    'mt_onglet_reduction_aide': {'fr': 'Le ZHR de vos comptages et l’indice de population r.',
                                 'en': 'The ZHR of your counts and the population index r.'},
    # calendrier
    'mt_annee': {'fr': 'Année', 'en': 'Year'},
    'mt_annee_aide': {'fr': 'Les dates sont recalculées pour l’année choisie à partir des longitudes solaires de '
                            'l’IMO.', 'en': 'Dates are recomputed for the chosen year from the IMO solar longitudes.'},
    'mt_col_pluie': {'fr': 'Pluie', 'en': 'Shower'},
    'mt_col_activite': {'fr': 'Activité', 'en': 'Activity'},
    'mt_col_max': {'fr': 'Maximum', 'en': 'Maximum'},
    'mt_col_zhr': {'fr': 'ZHR', 'en': 'ZHR'},
    'mt_col_r': {'fr': 'r', 'en': 'r'},
    'mt_col_v': {'fr': 'V∞ (km/s)', 'en': 'V∞ (km/s)'},
    'mt_col_radiant': {'fr': 'Radiant α, δ', 'en': 'Radiant α, δ'},
    'mt_col_culm': {'fr': 'Culmination', 'en': 'Culmination'},
    'mt_col_lune': {'fr': 'Lune', 'en': 'Moon'},
    'mt_calendrier_aide': {'fr': 'Liste de travail des pluies visuelles de l’IMO. Culmination : hauteur maximale du '
                                 'radiant à votre lieu. Lune : fraction éclairée au maximum. Double-clic : la nuit du '
                                 'maximum.',
                           'en': 'IMO working list of visual meteor showers. Culmination: highest altitude of the '
                                 'radiant at your place. Moon: illuminated fraction at the maximum. Double-click: '
                                 'the night of the maximum.'},
    'mt_voir_nuit': {'fr': 'Nuit du maximum', 'en': 'Night of the maximum'},
    'mt_zhr_var': {'fr': 'variable', 'en': 'variable'},
    'mt_zhr_plus': {'fr': '{z} ou plus', 'en': '{z} or more'},
    'mt_jamais': {'fr': 'jamais levé', 'en': 'never rises'},
    'mt_diurne': {'fr': ' (radiant proche du Soleil : surtout radio)', 'en': ' (radiant near the Sun: mostly radio)'},
    # une nuit
    'mt_nuit_date': {'fr': 'Nuit du', 'en': 'Night of'},
    'mt_nuit_date_aide': {'fr': 'Date du soir (AAAA-MM-JJ) : la nuit va de ce soir au lendemain matin.',
                          'en': 'Date of the evening (YYYY-MM-DD): the night runs from that evening to the next '
                                'morning.'},
    'mt_nuit_indice': {'fr': 'ex. 2026-12-13', 'en': 'e.g. 2026-12-13'},
    'mt_calculer': {'fr': 'Calculer', 'en': 'Compute'},
    'mt_graphe_aide': {'fr': 'Hauteur du radiant des pluies actives (traits pleins), de la Lune (tirets) et nombre '
                             'de météores attendus par heure pour la première pluie (aire). Gris : Soleil à moins '
                             'de 12° sous l’horizon.',
                       'en': 'Altitude of the radiants of the active showers (solid lines), of the Moon (dashes) '
                             'and expected meteors per hour for the first shower (area). Grey: Sun less than 12° '
                             'below the horizon.'},
    'mt_axe_h': {'fr': 'hauteur (°)', 'en': 'altitude (°)'},
    'mt_axe_taux': {'fr': 'météores / h', 'en': 'meteors / h'},
    'mt_leg_lune': {'fr': 'Lune', 'en': 'Moon'},
    'mt_n_titre': {'fr': 'Nuit du {date}', 'en': 'Night of {date}'},
    'mt_n_noire': {'fr': 'Nuit noire (Soleil à plus de 12° sous l’horizon) de {debut} à {fin}.',
                   'en': 'Dark night (Sun more than 12° below the horizon) from {debut} to {fin}.'},
    'mt_n_pas_nuit': {'fr': 'Le Soleil ne descend pas à 12° sous l’horizon : pas de nuit noire.',
                      'en': 'The Sun does not go 12° below the horizon: no dark night.'},
    'mt_n_lune': {'fr': 'Lune éclairée à {p} %.', 'en': 'Moon {p} % illuminated.'},
    'mt_n_lune_ok': {'fr': ' Elle gêne peu (moins de 5 jours de la nouvelle lune).',
                     'en': ' It hardly matters (within 5 days of New Moon).'},
    'mt_n_lune_ko': {'fr': ' Elle gêne : seules les heures où elle est couchée comptent.',
                     'en': ' It interferes: only the hours when it is set count.'},
    'mt_n_pluie': {'fr': '<b>{nom}</b> : {n} météores attendus en {heures} h utiles ; au mieux {taux} par heure '
                         'vers {heure} (radiant à {h}°, ZHR {z}).',
                   'en': '<b>{nom}</b>: {n} meteors expected in {heures} useful hours; at best {taux} per hour '
                         'around {heure} (radiant at {h}°, ZHR {z}).'},
    'mt_n_pluie_rien': {'fr': '<b>{nom}</b> : aucun temps utile (radiant trop bas, jour ou Lune).',
                        'en': '<b>{nom}</b>: no useful time (radiant too low, daylight or Moon).'},
    'mt_n_var': {'fr': ' ZHR variable : donnez une valeur supposée.', 'en': ' Variable ZHR: give an assumed value.'},
    'mt_n_champ': {'fr': 'Regardez vers l’azimut {az}° à {h}° de hauteur (à 20-40° du radiant, pas sur lui).',
                   'en': 'Look towards azimuth {az}° at {h}° altitude (20-40° from the radiant, not at it).'},
    'mt_n_aucune': {'fr': 'Aucune pluie active cette nuit (hors sporadiques).',
                    'en': 'No active shower tonight (apart from sporadics).'},
    'mt_n_conseil': {'fr': 'Rappels de la fiche IMO : 20 min d’adaptation à l’obscurité, lampe rouge, heure exacte, '
                           'noter la magnitude limite et le centre du champ ; observer seul, sans combiner ses '
                           'comptages avec ceux des voisins.',
                     'en': 'Reminders from the IMO sheet: 20 min of dark adaptation, red light, exact time, note the '
                           'limiting magnitude and the centre of the field; observe alone, without combining your '
                           'counts with your neighbours’.'},
    'mt_pluie_toutes': {'fr': 'Toutes les pluies actives', 'en': 'All active showers'},
    'mt_zhr_force': {'fr': 'ZHR supposée', 'en': 'Assumed ZHR'},
    'mt_zhr_force_aide': {'fr': 'Pour une pluie à ZHR « variable » (ou pour tester une prévision d’activité) ; 0 : '
                                'celle de l’IMO.',
                          'en': 'For a shower with a “variable” ZHR (or to test an activity prediction); 0: the '
                                'IMO value.'},
    'mt_nuit_pluie': {'fr': 'Pluie', 'en': 'Shower'},
    # campagne
    'mt_du': {'fr': 'Du', 'en': 'From'},
    'mt_au': {'fr': 'Au', 'en': 'To'},
    'mt_du_aide': {'fr': 'Début de la période (AAAA-MM-JJ) ; vide : aujourd’hui.',
                   'en': 'Start of the period (YYYY-MM-DD); empty: today.'},
    'mt_au_aide': {'fr': 'Fin de la période (AAAA-MM-JJ) ; vide : le 31 août suivant (date limite du rapport).',
                   'en': 'End of the period (YYYY-MM-DD); empty: the following 31 August (report deadline).'},
    'mt_min': {'fr': 'Au moins', 'en': 'At least'},
    'mt_min_aide': {'fr': 'Nombre minimal de météores attendus dans la nuit pour garder une pluie. La fiche IMO '
                          'conseille de débuter avec plus de 15-20 météores par heure.',
                    'en': 'Minimum number of meteors expected in the night to keep a shower. The IMO sheet '
                          'advises beginners to start with more than 15-20 meteors per hour.'},
    'mt_unite_met': {'fr': 'météores', 'en': 'meteors'},
    'mt_chercher': {'fr': 'Chercher les nuits', 'en': 'Find nights'},
    'mt_col_nuit': {'fr': 'Nuit du', 'en': 'Night of'},
    'mt_col_attendus': {'fr': 'Attendus', 'en': 'Expected'},
    'mt_col_heures': {'fr': 'Heures utiles', 'en': 'Useful hours'},
    'mt_col_meilleur': {'fr': 'Au mieux vers', 'en': 'Best around'},
    'mt_col_taux': {'fr': 'Taux max (/h)', 'en': 'Peak rate (/h)'},
    'mt_col_hr': {'fr': 'Radiant', 'en': 'Radiant'},
    'mt_col_note': {'fr': 'Note', 'en': 'Score'},
    'mt_campagne_aide': {'fr': 'Une ligne par nuit et par pluie. Note : 100 pour la meilleure nuit de la période. '
                               'Double-clic : le détail de la nuit.',
                         'en': 'One row per night and shower. Score: 100 for the best night of the period. '
                               'Double-click: details of the night.'},
    'mt_ics': {'fr': 'Agenda .ics', 'en': '.ics calendar'},
    'mt_csv': {'fr': 'Tableau CSV', 'en': 'CSV table'},
    'mt_c_fini': {'fr': '{n} nuits retenues du {debut} au {fin}.', 'en': '{n} nights kept from {debut} to {fin}.'},
    'mt_c_aucun': {'fr': 'Aucune nuit ne donne assez de météores : baissez le minimum ou allongez la période.',
                   'en': 'No night gives enough meteors: lower the minimum or lengthen the period.'},
    'mt_en_cours': {'fr': 'Calcul en cours…', 'en': 'Computing…'},
    'mt_exporte': {'fr': 'Enregistré : {chemin}', 'en': 'Saved: {chemin}'},
    # réduction
    'mt_r_intro': {'fr': 'ZHR = N · r^(6,5 − LM) / (F · t_eff · sin h) : le nombre de météores qu’on aurait vu en '
                         'une heure, sous un ciel parfait (LM 6,5), radiant au zénith.',
                   'en': 'ZHR = N · r^(6.5 − LM) / (F · t_eff · sin h): the number of meteors one would have seen '
                         'in one hour under a perfect sky (LM 6.5) with the radiant at the zenith.'},
    'mt_r_pluie': {'fr': 'Pluie', 'en': 'Shower'},
    'mt_r_debut': {'fr': 'Début', 'en': 'Start'},
    'mt_r_fin': {'fr': 'Fin', 'en': 'End'},
    'mt_r_heure_aide': {'fr': 'AAAA-MM-JJ HH:MM (UTC, ou heure locale si la case est cochée) ; sert au temps '
                              'effectif et à la hauteur du radiant au milieu de l’intervalle.',
                        'en': 'YYYY-MM-DD HH:MM (UTC, or local time if the box is ticked); used for the effective '
                              'time and the radiant altitude at mid-interval.'},
    'mt_r_pause': {'fr': 'Pauses', 'en': 'Breaks'},
    'mt_r_pause_aide': {'fr': 'Minutes passées à noter, à se réchauffer… à retirer du temps d’observation.',
                        'en': 'Minutes spent writing, warming up… to subtract from the observing time.'},
    'mt_unite_min': {'fr': 'min', 'en': 'min'},
    'mt_r_n': {'fr': 'Météores comptés (N)', 'en': 'Meteors counted (N)'},
    'mt_r_n_aide': {'fr': 'Météores de cette pluie seulement (pas les sporadiques).',
                    'en': 'Meteors of this shower only (not sporadics).'},
    'mt_r_r': {'fr': 'Indice de population r', 'en': 'Population index r'},
    'mt_r_r_aide': {'fr': 'Celui de l’IMO pour la pluie, ou le vôtre (calcul ci-dessous).',
                    'en': 'The IMO value for the shower, or yours (computed below).'},
    'mt_r_resultat': {'fr': '<b>ZHR = {z} ± {e}</b> (t_eff = {t} h, radiant à {h}° au milieu de l’intervalle).',
                      'en': '<b>ZHR = {z} ± {e}</b> (t_eff = {t} h, radiant at {h}° at mid-interval).'},
    'mt_r_facteurs': {'fr': 'Corrections : durée × {t}, champ × {f}, magnitude limite × {lm}, hauteur × {h}. '
                            'Incertitude : ZHR/√N (statistique de comptage).',
                      'en': 'Corrections: duration × {t}, field × {f}, limiting magnitude × {lm}, altitude × {h}. '
                            'Uncertainty: ZHR/√N (counting statistics).'},
    'mt_r_couche': {'fr': 'Le radiant est sous l’horizon au milieu de l’intervalle : pas de ZHR.',
                    'en': 'The radiant is below the horizon at mid-interval: no ZHR.'},
    'mt_alerte_h': {'fr': 'Radiant à moins de 20° : correction très forte, la fiche IMO déconseille ces mesures.',
                    'en': 'Radiant below 20°: very large correction, the IMO sheet advises against such data.'},
    'mt_alerte_f': {'fr': 'Champ très masqué : correction forte (le cours conseille d’écarter ces mesures).',
                    'en': 'Field heavily obstructed: large correction (the course advises discarding such data).'},
    'mt_err_entrees': {'fr': 'Durée et F doivent être positifs.', 'en': 'Duration and F must be positive.'},
    'mt_err_lieu': {'fr': 'Donnez d’abord le lieu d’observation.', 'en': 'Give the observing place first.'},
    'mt_err_date': {'fr': 'Date illisible : « {texte} » (AAAA-MM-JJ, ou AAAA-MM-JJ HH:MM).',
                    'en': 'Unreadable date: “{texte}” (YYYY-MM-DD, or YYYY-MM-DD HH:MM).'},
    'mt_r_mags': {'fr': 'Magnitudes notées', 'en': 'Recorded magnitudes'},
    'mt_r_mags_aide': {'fr': 'Nombre de météores par magnitude, ex. « -1:2 0:4 1:9 2:21 3:38 4:55 ».',
                       'en': 'Number of meteors per magnitude, e.g. “-1:2 0:4 1:9 2:21 3:38 4:55”.'},
    'mt_r_mags_indice': {'fr': 'ex. -1:2 0:4 1:9 2:21 3:38', 'en': 'e.g. -1:2 0:4 1:9 2:21 3:38'},
    'mt_r_indice': {'fr': 'r ≈ {r} (moyenne des rapports {liste}) : reporté plus haut.',
                    'en': 'r ≈ {r} (mean of the ratios {liste}): copied above.'},
    'mt_r_indice_aucun': {'fr': 'Pas assez de météores pour estimer r (il faut au moins 3 météores cumulés par '
                                'classe, jusqu’à LM − 1).',
                          'en': 'Not enough meteors to estimate r (at least 3 cumulated meteors per class are '
                                'needed, up to LM − 1).'},
    'mt_r_calculer': {'fr': 'Calculer le ZHR', 'en': 'Compute the ZHR'},
    'mt_r_r_calc': {'fr': 'Estimer r', 'en': 'Estimate r'},
    'mt_sources': {'fr': 'Données : calendrier 2027 de l’IMO (J. Rendtel éd.) ; pentes d’activité : Jenniskens '
                         '(1994). Profil indicatif quand la pente n’est pas publiée.',
                   'en': 'Data: IMO 2027 calendar (J. Rendtel ed.); activity slopes: Jenniskens (1994). '
                         'Indicative profile when no slope is published.'},
    'mt_aide_html': {
        'fr': '<h3>Pluies de météores</h3><p>Calculateur du TP « Observation des météores » (cours 3.2 '
              'd’astrodynamique). <b>Calendrier</b> : la liste de travail des pluies visuelles de l’IMO (calendrier '
              '2027, tableau 5), dates recalculées pour l’année choisie à partir de la longitude solaire du '
              'maximum ; la position du radiant suit la dérive du tableau 6.</p><p><b>Une nuit</b> : de midi à midi, '
              'pas de 5 min : hauteur du Soleil, de la Lune, de chaque radiant ; taux attendu n = ZHR · F · sin h / '
              'r^(6,5 − LM), ZHR suivant le profil d’activité de Jenniskens (1994) : ZHR_max · 10^(−B|λ − λ_max|), '
              'deux composantes pour les Quadrantides, Perséides, Géminides et Ursides. Sans pente publiée, '
              'B est pris pour que la ZHR tombe à 1 % du maximum aux limites d’activité : profil indicatif. Temps '
              'utile : Soleil à plus de 12° sous l’horizon, radiant à 20° au moins, Lune couchée ou à moins de '
              '5 jours de la nouvelle lune (fraction éclairée ≤ 25 %), règles de la fiche IMO. Champ conseillé : '
              '60° de hauteur, à 30° du radiant, du côté opposé à la Lune.</p><p><b>Campagne</b> : chaque nuit de '
              'la période, les pluies qui donnent assez de météores ; agenda .ics. Le TP demande plusieurs '
              'séances : commencez par une grande pluie.</p><p><b>Réduction</b> : ZHR = N · r^(6,5 − LM) / (F · '
              't_eff · sin h), hauteur du radiant calculée au milieu de l’intervalle, incertitude ZHR/√N ; r '
              'estimé par les rapports des nombres cumulés Φ(m+1)/Φ(m) jusqu’à LM − 1. Envoyez vos comptages à '
              'l’IMO (imo.net) : c’est leur réduction qui fait foi.</p><p>Astronomie : Soleil et Lune par ERFA '
              '(ou JPL DE440), longitude solaire J2000 de Meeus ; vérifié avec SageMath et sur les instants de '
              'maximum publiés par l’IMO (à quelques minutes près). Précision : celle d’un planning.</p>',
        'en': '<h3>Meteor showers</h3><p>Calculator for the “Meteor observation” practical (course 3.2 of '
              'astrodynamics). <b>Calendar</b>: the IMO working list of visual meteor showers (2027 calendar, '
              'table 5), dates recomputed for the chosen year from the solar longitude of the maximum; the radiant '
              'follows the drift of table 6.</p><p><b>One night</b>: noon to noon, 5 min steps: altitude of the Sun, '
              'the Moon and each radiant; expected rate n = ZHR · F · sin h / r^(6.5 − LM), the ZHR following '
              'the activity profile of Jenniskens (1994): ZHR_max · 10^(−B|λ − λ_max|), two components for the '
              'Quadrantids, Perseids, Geminids and Ursids. Without a published slope, B is chosen so that the ZHR '
              'falls to 1 % of the maximum at the activity limits: indicative profile. Useful time: Sun more than '
              '12° below the horizon, radiant at least 20° high, Moon set or within 5 days of New Moon '
              '(illuminated fraction ≤ 25 %), rules of the IMO sheet. Suggested field: 60° altitude, 30° from the '
              'radiant, on the side away from the Moon.</p><p><b>Campaign</b>: each night of the period, the '
              'showers giving enough meteors; .ics calendar. The practical asks for several sessions: start with a '
              'major shower.</p><p><b>Reduction</b>: ZHR = N · r^(6.5 − LM) / (F · t_eff · sin h), radiant altitude '
              'computed at mid-interval, uncertainty ZHR/√N; r estimated from the ratios of cumulated counts '
              'Φ(m+1)/Φ(m) up to LM − 1. Send your counts to the IMO (imo.net): their reduction is the reference.'
              '</p><p>Astronomy: Sun and Moon from ERFA (or JPL DE440), J2000 solar longitude from Meeus; checked '
              'with SageMath and against the times of maximum published by the IMO (within a few minutes). '
              'Accuracy: that of a plan.</p>'},
    # info-bulles des boutons
    'mt_voir_nuit_aide': {'fr': 'Ouvre la nuit du maximum de la pluie choisie dans le tableau.',
                          'en': 'Opens the night of the maximum of the shower chosen in the table.'},
    'mt_calculer_aide': {'fr': 'Calcule la nuit au lieu choisi.', 'en': 'Computes the night at the chosen place.'},
    'mt_chercher_aide': {'fr': 'Calcule chaque nuit de la période (quelques secondes).',
                         'en': 'Computes every night of the period (a few seconds).'},
    'mt_ics_aide': {'fr': 'Enregistre les nuits retenues dans un agenda .ics (une heure avant et après le meilleur '
                          'moment).', 'en': 'Saves the nights kept in an .ics calendar (one hour before and after '
                                            'the best time).'},
    'mt_csv_aide': {'fr': 'Enregistre le tableau des nuits (CSV, séparateur « ; »).',
                    'en': 'Saves the table of nights (CSV, “;” separator).'},
    'mt_r_calculer_aide': {'fr': 'Calcule le ZHR de l’intervalle avec la hauteur du radiant à votre lieu.',
                           'en': 'Computes the ZHR of the interval with the radiant altitude at your place.'},
    'mt_r_r_calc_aide': {'fr': 'Estime r à partir des magnitudes notées et le reporte dans le champ r.',
                         'en': 'Estimates r from the recorded magnitudes and copies it into the r field.'},
    'mt_detail_aide': {'fr': 'Détail de la nuit : nuit noire, Lune, météores attendus par pluie, champ à viser.',
                       'en': 'Details of the night: dark night, Moon, expected meteors per shower, field to aim at.'},
}
