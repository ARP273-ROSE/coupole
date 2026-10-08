"""Textes (FR/EN) de la fiche d'informations en ligne (SIMBAD, Sesame, JPL SBDB), partagée par les modules."""

TEXTES = {
    'fiche_titre': {'fr': 'Fiche en ligne', 'en': 'Online record'},
    'fiche_vue_aide': {'fr': "Informations publiques sur l'objet choisi (SIMBAD, Sesame ou JPL SBDB). Les liens "
                             "s'ouvrent dans votre navigateur.",
                       'en': 'Public information on the selected object (SIMBAD, Sesame or JPL SBDB). Links open in '
                             'your browser.'},
    'fiche_activer': {'fr': 'Interroger les services en ligne', 'en': 'Query online services'},
    'fiche_activer_aide': {'fr': "Décoché : aucune requête n'est envoyée ; seules les fiches déjà en cache "
                                 "s'affichent. Une seule requête par objet choisi, gardée 30 jours en cache.",
                           'en': 'Unchecked: no request is sent; only records already cached are shown. One request '
                                 'per selected object, cached for 30 days.'},
    'fiche_actualiser': {'fr': 'Actualiser', 'en': 'Refresh'},
    'fiche_actualiser_aide': {'fr': 'Interroge de nouveau le service, sans tenir compte du cache.',
                              'en': 'Query the service again, ignoring the cache.'},
    'fiche_vers_cosmo': {'fr': 'Envoyer ce redshift au module Cosmologie',
                         'en': 'Send this redshift to the Cosmology module'},
    'fiche_vers_cosmo_aide': {'fr': 'Ouvre le module Cosmologie avec le redshift de cette fiche : distances, âges, '
                                    'échelle. Possible seulement pour z > 0.',
                              'en': "Opens the Cosmology module with this record's redshift: distances, ages, scale. "
                                    'Only for z > 0.'},
    'fiche_pas_de_z': {'fr': "Pas de redshift positif dans cette fiche (objet de notre Galaxie, ou qui s'approche) : "
                             'rien à convertir en distance cosmologique.',
                       'en': 'No positive redshift in this record (object in our Galaxy, or approaching): nothing to '
                             'convert into a cosmological distance.'},
    'fiche_choisir': {'fr': 'Choisissez un objet (un seul) dans le catalogue.',
                      'en': 'Select one object in the catalogue.'},
    'fiche_attente': {'fr': 'Interrogation de {service} pour « {nom} »…', 'en': 'Querying {service} for « {nom} »…'},
    'fiche_desactive': {'fr': 'Services en ligne désactivés : aucune fiche en cache pour « {nom} ».',
                        'en': 'Online services disabled: no cached record for « {nom} ».'},
    'fiche_hors_ligne': {'fr': 'Hors ligne ou service injoignable ({erreur}). La fiche apparaîtra quand la '
                               'connexion reviendra (bouton Actualiser). Le reste de Coupole fonctionne sans.',
                         'en': 'Offline or service unreachable ({erreur}). The record will appear when the connection '
                               'is back (Refresh button). The rest of Coupole works without it.'},
    'fiche_introuvable': {'fr': '« {nom} » est inconnu de {service}.', 'en': '« {nom} » is unknown to {service}.'},
    'fiche_planete': {'fr': "Planète : SIMBAD ne couvre pas le Système solaire et la base des petits corps du JPL "
                            "n'inclut pas les planètes. Pas de fiche en ligne.",
                      'en': "Planet: SIMBAD does not cover the Solar System and JPL's small-body database does not "
                            'include planets. No online record.'},
    'fiche_neocp': {'fr': "Désignation provisoire de la page NEOCP du Minor Planet Center, sans identification "
                          "connue : pas de fiche en ligne.",
                    'en': "Provisional designation from the Minor Planet Center's NEOCP page, with no known "
                          'identification: no online record.'},
    'fiche_vide': {'fr': 'Aucun objet.', 'en': 'No object.'},
    'fiche_date': {'fr': 'Source : {service}, consulté le {date} UTC{cache}.',
                   'en': 'Source: {service}, retrieved on {date} UTC{cache}.'},
    'fiche_depuis_cache': {'fr': ' (cache)', 'en': ' (cache)'},
    'fiche_perime': {'fr': ' — fiche en cache, service injoignable aujourd\'hui', 'en': ' — cached record, service '
                                                                                        'unreachable today'},
    'fiche_retenu': {'fr': 'Identifiant retenu par {service}', 'en': 'Identifier chosen by {service}'},
    'fiche_retenu_note': {'fr': "Le nom demandé était « {demande} » : vérifiez qu'il s'agit bien du même objet "
                                '(SIMBAD peut rattacher une nébuleuse à son étoile centrale).',
                          'en': 'The requested name was « {demande} »: check that this is the same object (SIMBAD may '
                                'attach a nebula to its central star).'},
    'fiche_type': {'fr': 'Type', 'en': 'Type'},
    'fiche_coord': {'fr': 'Coordonnées (ICRS, J2000)', 'en': 'Coordinates (ICRS, J2000)'},
    'fiche_mags': {'fr': 'Magnitudes', 'en': 'Magnitudes'},
    'fiche_plx': {'fr': 'Parallaxe', 'en': 'Parallax'},
    'fiche_plx_distance': {'fr': '{plx} ± {err} mas → distance ≈ {pc} pc ({al} al)',
                           'en': '{plx} ± {err} mas → distance ≈ {pc} pc ({al} ly)'},
    'fiche_plx_imprecise': {'fr': '{plx} ± {err} mas (trop imprécise pour en tirer une distance)',
                            'en': '{plx} ± {err} mas (too uncertain to give a distance)'},
    'fiche_distance': {'fr': 'Distance mesurée', 'en': 'Measured distance'},
    'fiche_methode': {'fr': 'méthode :', 'en': 'method:'},
    'fiche_vitesse': {'fr': 'Vitesse radiale / redshift', 'en': 'Radial velocity / redshift'},
    'fiche_vitesse_val': {'fr': 'v = {v} km/s, z = {z}', 'en': 'v = {v} km/s, z = {z}'},
    'fiche_qualite': {'fr': 'qualité', 'en': 'quality'},
    'fiche_taille': {'fr': 'Taille angulaire', 'en': 'Angular size'},
    'fiche_taille_val': {'fr': "{x}′ × {y}′ (angle de position {a}°)", 'en': "{x}′ × {y}′ (position angle {a}°)"},
    'fiche_sp': {'fr': 'Type spectral', 'en': 'Spectral type'},
    'fiche_morpho': {'fr': 'Type morphologique', 'en': 'Morphological type'},
    'fiche_ids': {'fr': 'Autres noms', 'en': 'Other names'},
    'fiche_ids_plus': {'fr': '… et {n} autres', 'en': '… and {n} more'},
    'fiche_liens': {'fr': 'Liens', 'en': 'Links'},
    'fiche_lien_simbad': {'fr': 'page SIMBAD', 'en': 'SIMBAD page'},
    'fiche_lien_aladin': {'fr': 'Aladin Lite (image du ciel)', 'en': 'Aladin Lite (sky image)'},
    'fiche_lien_ned': {'fr': 'NED (base extragalactique)', 'en': 'NED (extragalactic database)'},
    'fiche_lien_sbdb': {'fr': 'JPL Small-Body Database', 'en': 'JPL Small-Body Database'},
    'fiche_classe': {'fr': 'Classe orbitale', 'en': 'Orbit class'},
    'fiche_neo': {'fr': 'géocroiseur (NEO)', 'en': 'near-Earth object (NEO)'},
    'fiche_pha': {'fr': 'potentiellement dangereux (PHA)', 'en': 'potentially hazardous (PHA)'},
    'fiche_elements': {'fr': 'Éléments orbitaux (époque JD {jd})', 'en': 'Orbital elements (epoch JD {jd})'},
    'fiche_el_a': {'fr': 'demi-grand axe a', 'en': 'semi-major axis a'},
    'fiche_el_e': {'fr': 'excentricité e', 'en': 'eccentricity e'},
    'fiche_el_i': {'fr': 'inclinaison i', 'en': 'inclination i'},
    'fiche_el_q': {'fr': 'périhélie q', 'en': 'perihelion q'},
    'fiche_el_ad': {'fr': 'aphélie Q', 'en': 'aphelion Q'},
    'fiche_el_om': {'fr': 'longitude du nœud ascendant Ω', 'en': 'longitude of ascending node Ω'},
    'fiche_el_w': {'fr': 'argument du périhélie ω', 'en': 'argument of perihelion ω'},
    'fiche_el_per': {'fr': 'période orbitale', 'en': 'orbital period'},
    'fiche_annees': {'fr': '{v} ans', 'en': '{v} years'},
    'fiche_physique': {'fr': 'Caractéristiques physiques', 'en': 'Physical characteristics'},
    'fiche_ph_diameter': {'fr': 'diamètre', 'en': 'diameter'},
    'fiche_ph_albedo': {'fr': 'albédo géométrique', 'en': 'geometric albedo'},
    'fiche_ph_rot_per': {'fr': 'période de rotation', 'en': 'rotation period'},
    'fiche_ph_H': {'fr': 'magnitude absolue H', 'en': 'absolute magnitude H'},
    'fiche_ph_inconnu': {'fr': 'non mesuré (absent de la base)', 'en': 'not measured (absent from the database)'},
    'fiche_ambigu': {'fr': 'Plusieurs petits corps répondent à « {nom} » : {liste}.',
                     'en': 'Several small bodies match « {nom} »: {liste}.'},
}
