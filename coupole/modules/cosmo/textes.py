"""Textes du module « Cosmologie » (FR/EN).  Explications reprises du calculateur cosmologie-redshift."""

TEXTES = {
    # ------------------------------------------------------------ modèles et réglages
    'cosmo_modele': {'fr': 'Paramètres cosmologiques', 'en': 'Cosmological parameters'},
    'cosmo_modele_aide': {'fr': "Jeu de paramètres du modèle ΛCDM. Planck 2018 est la référence actuelle ; les autres "
                                "servent à comparer (articles anciens, exercices de manuel).",
                          'en': 'Parameter set of the ΛCDM model. Planck 2018 is the current reference; the others are '
                                'for comparison (older papers, textbook exercises).'},
    'cosmo_mod_planck18': {'fr': 'Planck 2018 (référence)', 'en': 'Planck 2018 (reference)'},
    'cosmo_mod_planck15': {'fr': 'Planck 2015', 'en': 'Planck 2015'},
    'cosmo_mod_wmap9': {'fr': 'WMAP 9 ans', 'en': 'WMAP 9-year'},
    'cosmo_mod_simple': {'fr': 'ΛCDM de manuel (H₀ = 70, Ωm = 0,3, sans rayonnement)',
                         'en': 'Textbook ΛCDM (H₀ = 70, Ωm = 0.3, no radiation)'},
    'cosmo_mod_perso': {'fr': 'Personnalisé (rayonnement de Planck 2018)', 'en': 'Custom (Planck 2018 radiation)'},
    'cosmo_h0': {'fr': 'H₀ (km/s/Mpc)', 'en': 'H₀ (km/s/Mpc)'},
    'cosmo_h0_aide': {'fr': 'Constante de Hubble actuelle. Planck 2018 : 67,66 ; SH0ES (céphéides et supernovæ) : '
                            '73,04. Modèle « Personnalisé » seulement.',
                      'en': 'Present-day Hubble constant. Planck 2018: 67.66; SH0ES (Cepheids and supernovae): 73.04. '
                            '« Custom » model only.'},
    'cosmo_om': {'fr': 'Ωm (matière totale)', 'en': 'Ωm (total matter)'},
    'cosmo_om_aide': {'fr': 'Part de la matière (noire + baryons + neutrinos) dans la densité critique aujourd\'hui. '
                            'Planck 2018 : 0,3111. Modèle « Personnalisé » seulement.',
                      'en': 'Share of matter (dark + baryons + neutrinos) in today\'s critical density. Planck 2018: '
                            '0.3111. « Custom » model only.'},
    'cosmo_ok': {'fr': 'Ωk (courbure)', 'en': 'Ωk (curvature)'},
    'cosmo_ok_aide': {'fr': "Part de la courbure dans le contenu de l'univers (pas une longueur) : toutes les parts "
                            "réunies font 1, et ΩΛ s'ajuste. Ωk > 0 : univers ouvert ; Ωk < 0 : fermé. Planck 2018 : "
                            "0,0007 ± 0,0019.",
                      'en': "Share of curvature in the content of the universe (not a length): all the shares add up to "
                            "1, and ΩΛ adjusts. Ωk > 0: open universe; Ωk < 0: closed. Planck 2018: 0.0007 ± 0.0019."},
    'cosmo_bornes': {'fr': 'Plages acceptées : H₀ de {h0a} à {h0b} ; Ωm de {oma} à {omb} ; Ωk de {oka} à {okb} '
                           '(Planck 2018 : de {okpa} à {okpb}, déjà 25 fois son incertitude). Une valeur hors plage '
                           'est refusée avec une explication, jamais corrigée en silence.',
                     'en': 'Accepted ranges: H₀ from {h0a} to {h0b}; Ωm from {oma} to {omb}; Ωk from {oka} to {okb} '
                           '(Planck 2018: from {okpa} to {okpb}, already 25 times its uncertainty). An out-of-range '
                           'value is refused with an explanation, never silently corrected.'},
    'cosmo_params': {'fr': 'H₀ = {h0} km/s/Mpc · Ωm = {om} (dont Ων = {onu}) · ΩΛ = {ode} · Ωk = {ok} · Ωγ = {og} · '
                           'T₀ = {t} K · Neff = {neff} · Σmν = {mnu} eV',
                     'en': 'H₀ = {h0} km/s/Mpc · Ωm = {om} (incl. Ων = {onu}) · ΩΛ = {ode} · Ωk = {ok} · Ωγ = {og} · '
                           'T₀ = {t} K · Neff = {neff} · Σmν = {mnu} eV'},
    'cosmo_shoes': {'fr': 'Comparer avec SH0ES (H₀ = 73,04)', 'en': 'Compare with SH0ES (H₀ = 73.04)'},
    'cosmo_shoes_aide': {'fr': 'Ajoute une colonne : mêmes grandeurs avec la mesure locale de SH0ES (Riess et al. '
                               '2022), en désaccord à ~5σ avec Planck (tension de Hubble). Planck 2018 seulement.',
                         'en': 'Adds a column: same quantities with the local SH0ES measurement (Riess et al. 2022), '
                               'in ~5σ disagreement with Planck (Hubble tension). Planck 2018 only.'},
    # ------------------------------------------------------------ saisie
    'cosmo_z': {'fr': 'Redshift z', 'en': 'Redshift z'},
    'cosmo_z_aide': {'fr': 'Décalage vers le rouge, de 0 (exclu) à 1500. Virgule ou point acceptés. Entrée : '
                           'calculer.',
                     'en': 'Redshift, from 0 (excluded) to 1500. Comma or point accepted. Enter: compute.'},
    'cosmo_z_indice': {'fr': 'ex. 0,158', 'en': 'e.g. 0.158'},
    'cosmo_calculer': {'fr': 'Calculer', 'en': 'Compute'},
    'cosmo_calculer_aide': {'fr': 'Calcule toutes les grandeurs pour ce redshift et ces paramètres.',
                            'en': 'Compute every quantity for this redshift and these parameters.'},
    'cosmo_objet': {'fr': 'Objet', 'en': 'Object'},
    'cosmo_objet_aide': {'fr': 'Nom d\'un objet extragalactique (M 87, 3C 273, NGC 4993, GN-z11…) : son redshift est '
                               'demandé à SIMBAD si Internet est disponible.',
                         'en': 'Name of an extragalactic object (M 87, 3C 273, NGC 4993, GN-z11…): its redshift is '
                               'requested from SIMBAD when the Internet is available.'},
    'cosmo_objet_indice': {'fr': 'ex. 3C 273', 'en': 'e.g. 3C 273'},
    'cosmo_chercher': {'fr': 'Chercher le redshift (SIMBAD)', 'en': 'Look up redshift (SIMBAD)'},
    'cosmo_chercher_aide': {'fr': 'Une requête à SIMBAD (nom tolérant : « m87 », « ngc4486 »…), réponse gardée en '
                                  'cache. Hors ligne : saisissez z vous-même.',
                            'en': 'One request to SIMBAD (tolerant naming: « m87 », « ngc4486 »…), answer cached. '
                                  'Offline: type z yourself.'},
    'cosmo_candidats_aide': {'fr': 'Plusieurs objets répondent à ce nom : choisissez le bon (identifiant SIMBAD, type, '
                                   'redshift).',
                             'en': 'Several objects match this name: pick the right one (SIMBAD identifier, type, '
                                   'redshift).'},
    'cosmo_candidats_choix': {'fr': '— choisir —', 'en': '— choose —'},
    'cosmo_recherche': {'fr': 'Recherche de « {nom} » dans SIMBAD…', 'en': 'Looking up « {nom} » in SIMBAD…'},
    'cosmo_trouve': {'fr': '{nom} ({type}) : z = {z} (SIMBAD{cache}).', 'en': '{nom} ({type}): z = {z} (SIMBAD{cache}).'},
    'cosmo_trouve_sans_z': {'fr': '{nom} ({type}) : SIMBAD ne donne pas de redshift positif ({z}) — objet de notre '
                                  'Galaxie ou qui s\'approche.',
                            'en': '{nom} ({type}): SIMBAD gives no positive redshift ({z}) — object in our Galaxy or '
                                  'approaching.'},
    'cosmo_ambigu': {'fr': '{n} objets répondent à « {nom} » : choisissez dans la liste.',
                     'en': '{n} objects match « {nom} »: choose from the list.'},
    'cosmo_introuvable': {'fr': '« {nom} » est inconnu de SIMBAD.', 'en': '« {nom} » is unknown to SIMBAD.'},
    'cosmo_hors_ligne': {'fr': 'SIMBAD injoignable ({erreur}) : saisissez z vous-même.',
                         'en': 'SIMBAD unreachable ({erreur}): type z yourself.'},
    'cosmo_desactive': {'fr': 'Services en ligne désactivés (onglet Fiche en ligne de la Banque OHP) : saisissez z.',
                        'en': 'Online services disabled (Online record tab of the OHP bank): type z.'},
    'cosmo_recu': {'fr': 'Redshift reçu de la fiche en ligne : {nom}.', 'en': 'Redshift received from the online '
                                                                               'record: {nom}.'},
    # ------------------------------------------------------------ exemples
    'cosmo_ex_m87': {'fr': 'M 87', 'en': 'M 87'},
    'cosmo_ex_m87_aide': {'fr': "Galaxie elliptique géante de l'amas de la Vierge, trou noir imagé par l'Event Horizon "
                                "Telescope (2019). z donne D_C ≈ 62 M al, les mesures directes ~55 M al : l'écart est dû "
                                "à la vitesse propre de M 87 dans l'amas.",
                          'en': 'Giant elliptical galaxy in the Virgo cluster, black hole imaged by the Event Horizon '
                                'Telescope (2019). z gives D_C ≈ 62 Mly, direct measurements ~55 Mly: the difference is '
                                "M 87's peculiar velocity within the cluster."},
    'cosmo_ex_3c273': {'fr': '3C 273', 'en': '3C 273'},
    'cosmo_ex_3c273_aide': {'fr': 'Premier quasar identifié comme tel (Maarten Schmidt, 1963), le plus brillant vu de '
                                  'la Terre (mv ≈ 12,9). D_C = 2,20 G al mais D_L = 2,54 G al : l\'écart devient visible.',
                            'en': 'The first object identified as a quasar (Maarten Schmidt, 1963), the brightest seen '
                                  'from Earth (mv ≈ 12.9). D_C = 2.20 Gly but D_L = 2.54 Gly: the difference shows.'},
    'cosmo_ex_z1': {'fr': 'z = 1', 'en': 'z = 1'},
    'cosmo_ex_z1_aide': {'fr': "Repère pédagogique : l'univers avait 5,85 milliards d'années et était deux fois plus "
                               "petit qu'aujourd'hui (a = 0,5).",
                         'en': 'A teaching landmark: the universe was 5.85 billion years old and half its present size '
                               '(a = 0.5).'},
    'cosmo_ex_z234': {'fr': 'z = 2,34', 'en': 'z = 2.34'},
    'cosmo_ex_z234_aide': {'fr': '« Cosmic noon » : pic d\'activité des quasars et de formation d\'étoiles ; tranche-clé '
                                 'des relevés BAO (BOSS, eBOSS, forêt Lyman-α).',
                           'en': '« Cosmic noon »: peak of quasar activity and star formation; a key slice of the BAO '
                                 'surveys (BOSS, eBOSS, Lyman-α forest).'},
    'cosmo_ex_ulas': {'fr': 'ULAS J1120', 'en': 'ULAS J1120'},
    'cosmo_ex_ulas_aide': {'fr': 'Quasar découvert en 2011 (Mortlock et al.), trou noir de 2×10⁹ M☉. Univers âgé de '
                                 '749 millions d\'années en Planck 2018 (l\'article annonçait 770, en cosmologie WMAP7).',
                           'en': 'Quasar discovered in 2011 (Mortlock et al.), 2×10⁹ M☉ black hole. The universe was '
                                 '749 million years old in Planck 2018 (the paper quoted 770, in WMAP7 cosmology).'},
    'cosmo_ex_gnz11': {'fr': 'GN-z11', 'en': 'GN-z11'},
    'cosmo_ex_gnz11_aide': {'fr': "L'une des galaxies les plus lointaines confirmées (JWST 2022-2023) : l'univers avait "
                                  "435 millions d'années.",
                            'en': 'One of the most distant confirmed galaxies (JWST 2022-2023): the universe was 435 '
                                  'million years old.'},
    'cosmo_ex_reion': {'fr': 'Réionisation', 'en': 'Reionisation'},
    'cosmo_ex_reion_aide': {'fr': "Pas un objet mais une époque (ici z = 20) : les premières étoiles réionisent "
                                  "l'hydrogène intergalactique. Plage typique 6 < z < 30.",
                            'en': 'Not an object but an epoch (here z = 20): the first stars reionise intergalactic '
                                  'hydrogen. Typical range 6 < z < 30.'},
    'cosmo_ex_cmb': {'fr': 'Fond diffus', 'en': 'CMB'},
    'cosmo_ex_cmb_aide': {'fr': 'Surface de dernière diffusion (z = 1089,8) : la lumière la plus ancienne, émise quand '
                                "l'univers avait 372 000 ans et devint transparent.",
                          'en': 'Last-scattering surface (z = 1089.8): the oldest light, emitted when the universe was '
                                '372,000 years old and became transparent.'},
    # ------------------------------------------------------------ résultats
    'cosmo_table_aide': {'fr': 'Résultats pour le redshift et les paramètres choisis. Survol d\'une ligne : définition '
                               'et formule. Incertitude 1σ propagée depuis H₀ et Ωm de Planck 2018 (avec leur '
                               'corrélation).',
                         'en': 'Results for the chosen redshift and parameters. Hover a row: definition and formula. '
                               '1σ uncertainty propagated from Planck 2018 H₀ and Ωm (with their correlation).'},
    'cosmo_col_grandeur': {'fr': 'grandeur', 'en': 'quantity'},
    'cosmo_col_valeur': {'fr': 'valeur', 'en': 'value'},
    'cosmo_col_sigma': {'fr': '± 1σ (Planck 2018)', 'en': '± 1σ (Planck 2018)'},
    'cosmo_col_shoes': {'fr': 'avec SH0ES', 'en': 'with SH0ES'},
    'cosmo_g_a': {'fr': "Facteur d'échelle a = 1/(1+z)", 'en': 'Scale factor a = 1/(1+z)'},
    'cosmo_g_a_aide': {'fr': "Facteur d'échelle à l'émission (a = 1 aujourd'hui) : l'univers était (1+z) fois plus "
                             "petit dans chaque direction.",
                       'en': 'Scale factor at emission (a = 1 today): the universe was (1+z) times smaller in every '
                             'direction.'},
    'cosmo_g_E': {'fr': 'E(z) = H(z)/H₀', 'en': 'E(z) = H(z)/H₀'},
    'cosmo_g_E_aide': {'fr': "Taux d'expansion à l'émission, relatif à aujourd'hui : E(z)² = Ωr(z)(1+z)⁴ + Ωm(1+z)³ + "
                             "Ωk(1+z)² + ΩΛ, rayonnement (photons, neutrinos) compris.",
                       'en': 'Expansion rate at emission, relative to today: E(z)² = Ωr(z)(1+z)⁴ + Ωm(1+z)³ + Ωk(1+z)² '
                             '+ ΩΛ, radiation (photons, neutrinos) included.'},
    'cosmo_g_H_z': {'fr': 'Paramètre de Hubble H(z)', 'en': 'Hubble parameter H(z)'},
    'cosmo_g_H_z_aide': {'fr': "H(z) = H₀·E(z) : vitesse d'expansion à l'époque de l'émission.",
                         'en': 'H(z) = H₀·E(z): expansion rate when the light was emitted.'},
    'cosmo_g_comoving': {'fr': 'Distance comobile radiale D_C', 'en': 'Line-of-sight comoving distance D_C'},
    'cosmo_g_comoving_aide': {'fr': "Distance « immobile » dans le repère qui s'étend avec l'univers : la distance "
                                    "actuelle (t = t₀) de l'objet. D_C = D_H ∫₀^z dz'/E(z'). Sature à ~46 G al "
                                    "(horizon des particules).",
                              'en': "Distance fixed in the frame expanding with the universe: the object's present-day "
                                    "distance (t = t₀). D_C = D_H ∫₀^z dz'/E(z'). Saturates at ~46 Gly (particle "
                                    'horizon).'},
    'cosmo_g_transverse': {'fr': 'Distance comobile transverse D_M', 'en': 'Transverse comoving distance D_M'},
    'cosmo_g_transverse_aide': {'fr': 'Égale à D_C en univers plat ; sinon D_M = (D_H/√|Ωk|)·sinh ou sin(√|Ωk|·D_C/D_H). '
                                      "C'est elle qui entre dans D_L et D_A.",
                                'en': 'Equal to D_C in a flat universe; otherwise D_M = (D_H/√|Ωk|)·sinh or '
                                      'sin(√|Ωk|·D_C/D_H). It is the one entering D_L and D_A.'},
    'cosmo_g_luminosity': {'fr': 'Distance de luminosité D_L', 'en': 'Luminosity distance D_L'},
    'cosmo_g_luminosity_aide': {'fr': 'Distance pour la photométrie : F = L/(4π D_L²), D_L = (1+z)·D_M. C\'est elle qui '
                                      'relie magnitudes apparente et absolue.',
                                'en': 'Distance for photometry: F = L/(4π D_L²), D_L = (1+z)·D_M. It links apparent and '
                                      'absolute magnitudes.'},
    'cosmo_g_angular_diameter': {'fr': 'Distance angulaire D_A', 'en': 'Angular diameter distance D_A'},
    'cosmo_g_angular_diameter_aide': {'fr': 'Distance pour les tailles : θ = taille/D_A, D_A = D_M/(1+z). Passe par un '
                                            'maximum (~5,85 G al vers z ≈ 1,6) : au-delà, un objet plus lointain paraît '
                                            'plus grand.',
                                      'en': 'Distance for sizes: θ = size/D_A, D_A = D_M/(1+z). Peaks (~5.85 Gly near '
                                            'z ≈ 1.6): beyond, a more distant object looks larger.'},
    'cosmo_g_lookback': {'fr': 'Distance de trajet de la lumière c·t_L', 'en': 'Light-travel distance c·t_L'},
    'cosmo_g_lookback_aide': {'fr': 'Temps de trajet de la lumière × c : la valeur « intuitive », bornée par c·t₀, '
                                    'mais physiquement la moins propre à grand z.',
                              'en': 'Light travel time × c: the « intuitive » value, bounded by c·t₀, but physically '
                                    'the least meaningful at high z.'},
    'cosmo_g_lookback_gyr': {'fr': 'Temps de regard en arrière t_L', 'en': 'Lookback time t_L'},
    'cosmo_g_lookback_gyr_aide': {'fr': "Durée écoulée depuis l'émission de la lumière reçue aujourd'hui : "
                                        "t_L = ∫₀^z dz'/[(1+z')H(z')].",
                                  'en': "Time elapsed since the light received today was emitted: "
                                        "t_L = ∫₀^z dz'/[(1+z')H(z')]."},
    'cosmo_g_age_at_z': {'fr': "Âge de l'univers à z", 'en': 'Age of the universe at z'},
    'cosmo_g_age_at_z_aide': {'fr': "Âge de l'univers à l'émission : t(z) = ∫_z^∞ dz'/[(1+z')H(z')]. Contrôle : "
                                    "t_L + âge = t₀.",
                              'en': "Age of the universe at emission: t(z) = ∫_z^∞ dz'/[(1+z')H(z')]. Check: t_L + age "
                                    '= t₀.'},
    'cosmo_g_t0_model': {'fr': "Âge actuel de l'univers t₀", 'en': 'Present age of the universe t₀'},
    'cosmo_g_t0_model_aide': {'fr': 'Âge aujourd\'hui dans le modèle choisi (13,79 milliards d\'années en Planck 2018 ; '
                                    'il change avec H₀, Ωm et Ωk).',
                              'en': 'Age today in the chosen model (13.79 billion years in Planck 2018; it changes with '
                                    'H₀, Ωm and Ωk).'},
    'cosmo_g_distmod': {'fr': 'Module de distance μ', 'en': 'Distance modulus μ'},
    'cosmo_g_distmod_aide': {'fr': 'μ = m − M = 5 log₁₀(D_L / 10 pc), sans extinction ni correction K.',
                             'en': 'μ = m − M = 5 log₁₀(D_L / 10 pc), without extinction or K-correction.'},
    'cosmo_g_kpc_arcsec': {'fr': 'Échelle (propre)', 'en': 'Scale (proper)'},
    'cosmo_g_kpc_arcsec_aide': {'fr': "Taille réelle couverte par une seconde d'arc à ce redshift : D_A × 1″. Utile pour "
                                      "convertir une taille mesurée sur une image.",
                                'en': 'Physical size spanned by one arcsecond at this redshift: D_A × 1″. Useful to '
                                      'convert a size measured on an image.'},
    'cosmo_g_vol_gpc3': {'fr': 'Volume comobile jusqu\'à z', 'en': 'Comoving volume out to z'},
    'cosmo_g_vol_gpc3_aide': {'fr': "Volume comobile de la sphère de rayon D_C (tout le ciel), en Gpc³ : sert aux "
                                    "densités d'objets (comptages). Formule de Hogg (1999), exacte aussi en univers courbe.",
                              'en': 'Comoving volume of the sphere of radius D_C (whole sky), in Gpc³: used for object '
                                    'densities (counts). Hogg (1999) formula, exact in curved universes too.'},
    'cosmo_g_v_cz': {'fr': 'Vitesse « cz » (Doppler naïf)', 'en': 'Velocity « cz » (naive Doppler)'},
    'cosmo_g_v_cz_aide': {'fr': 'v = cz : valable seulement pour z ≪ 1 ; dépasse c dès z > 1, ce qui n\'a pas de sens.',
                          'en': 'v = cz: valid only for z ≪ 1; exceeds c as soon as z > 1, which is meaningless.'},
    'cosmo_g_v_sr': {'fr': 'Vitesse (Doppler relativiste)', 'en': 'Velocity (relativistic Doppler)'},
    'cosmo_g_v_sr_aide': {'fr': 'v/c = ((1+z)²−1)/((1+z)²+1) : bornée par c mais inadaptée (elle suppose un '
                                'espace-temps statique).',
                          'en': 'v/c = ((1+z)²−1)/((1+z)²+1): bounded by c but inappropriate (it assumes a static '
                                'spacetime).'},
    'cosmo_g_v_flrw': {'fr': 'Vitesse de récession actuelle H₀·D_C', 'en': 'Present recession velocity H₀·D_C'},
    'cosmo_g_v_flrw_aide': {'fr': "La définition correcte en cosmologie : v = H·D_propre. Non bornée par c — c'est "
                                  "l'espace qui s'étire, rien ne s'y propage plus vite que la lumière.",
                            'en': 'The correct definition in cosmology: v = H·D_proper. Not bounded by c — space '
                                  'stretches, nothing travels faster than light through it.'},
    # unités
    'cosmo_u_mpc': {'fr': 'Mpc', 'en': 'Mpc'},
    'cosmo_u_gyr': {'fr': "milliards d'années", 'en': 'billion years'},
    'cosmo_u_myr': {'fr': "millions d'années", 'en': 'million years'},
    'cosmo_u_kyr': {'fr': 'mille ans', 'en': 'thousand years'},
    'cosmo_u_kms': {'fr': 'km/s', 'en': 'km/s'},
    'cosmo_u_kms_mpc': {'fr': 'km/s/Mpc', 'en': 'km/s/Mpc'},
    'cosmo_u_mag': {'fr': 'mag', 'en': 'mag'},
    'cosmo_u_kpc_arcsec': {'fr': 'kpc par seconde d\'arc', 'en': 'kpc per arcsecond'},
    'cosmo_u_pc_arcsec': {'fr': 'pc par seconde d\'arc', 'en': 'pc per arcsecond'},
    'cosmo_u_gpc3': {'fr': 'Gpc³', 'en': 'Gpc³'},
    'cosmo_u_gal': {'fr': 'G al', 'en': 'Gly'},
    'cosmo_u_mal': {'fr': 'M al', 'en': 'Mly'},
    'cosmo_u_kal': {'fr': 'k al', 'en': 'kly'},
    'cosmo_u_c': {'fr': 'c', 'en': 'c'},
    # avertissements et erreurs
    'cosmo_av_proche': {'fr': "z < 0,03 : à cette distance, la vitesse propre de l'objet (quelques centaines de km/s "
                              "dans son groupe ou son amas) pèse autant que l'expansion : la distance tirée de z est "
                              "indicative ; préférez une mesure directe (céphéides, TRGB…).",
                        'en': "z < 0.03: at this distance the object's peculiar velocity (a few hundred km/s within "
                              'its group or cluster) weighs as much as the expansion: the distance from z is only '
                              'indicative; prefer a direct measurement (Cepheids, TRGB…).'},
    'cosmo_av_opaque': {'fr': "z > 1089,8 : avant la recombinaison, l'univers est opaque ; aucun objet n'est "
                              "observable à ce redshift (les grandeurs restent calculables).",
                        'en': 'z > 1089.8: before recombination the universe is opaque; no object is observable at '
                              'this redshift (the quantities remain computable).'},
    'cosmo_err_z_illisible': {'fr': '« {z} » n\'est pas un nombre.', 'en': '« {z} » is not a number.'},
    'cosmo_err_z_negatif': {'fr': "z = {z} : un redshift nul ou négatif (objet qui s'approche, comme M 31) ne donne "
                                  "pas de distance cosmologique.",
                            'en': 'z = {z}: a zero or negative redshift (approaching object, like M 31) gives no '
                                  'cosmological distance.'},
    'cosmo_err_z_grand': {'fr': "z = {z} dépasse {maxi:g} : au-delà de z ≈ 1090 l'univers est opaque, il n'y a rien à "
                                "observer plus loin.",
                          'en': 'z = {z} exceeds {maxi:g}: beyond z ≈ 1090 the universe is opaque, there is nothing to '
                                'observe further out.'},
    'cosmo_err_modele': {'fr': 'Modèle inconnu : {modele}.', 'en': 'Unknown model: {modele}.'},
    'cosmo_err_ok': {'fr': 'Ωk doit rester entre {mini} et {maxi} pour ce modèle.',
                     'en': 'Ωk must stay between {mini} and {maxi} for this model.'},
    'cosmo_err_h0': {'fr': 'H₀ doit rester entre {mini} et {maxi} km/s/Mpc.',
                     'en': 'H₀ must stay between {mini} and {maxi} km/s/Mpc.'},
    'cosmo_err_om': {'fr': 'Ωm doit rester entre {mini} et {maxi}.', 'en': 'Ωm must stay between {mini} and {maxi}.'},
    'cosmo_err_parametres': {'fr': 'Paramètres refusés par astropy : {erreur}', 'en': 'Parameters refused by astropy: '
                                                                                     '{erreur}'},
    'cosmo_err_rebond': {'fr': "Ces paramètres décrivent un univers sans Big Bang (E(z)² devient négatif : « rebond ») "
                               "ou qui s'effondre : les distances n'y sont pas définies. Diminuez ΩΛ (Ωm ou Ωk plus "
                               "grands).",
                         'en': 'These parameters describe a universe without a Big Bang (E(z)² becomes negative: '
                               '« bounce ») or one that recollapses: distances are not defined. Lower ΩΛ (larger Ωm or '
                               'Ωk).'},
    # courbes et export
    'cosmo_courbes_aide': {'fr': 'Distances en fonction de z (échelles logarithmiques), pour les paramètres choisis. '
                                 'Trait pointillé : le z courant. Survol : valeurs lues sur les courbes.',
                           'en': 'Distances versus z (logarithmic scales), for the chosen parameters. Dashed line: the '
                                 'current z. Hover: values read on the curves.'},
    'cosmo_courbe_dc': {'fr': 'D_C (comobile)', 'en': 'D_C (comoving)'},
    'cosmo_courbe_dl': {'fr': 'D_L (luminosité)', 'en': 'D_L (luminosity)'},
    'cosmo_courbe_da': {'fr': 'D_A (angulaire)', 'en': 'D_A (angular)'},
    'cosmo_courbe_dlt': {'fr': 'c·t_L (trajet lumière)', 'en': 'c·t_L (light travel)'},
    'cosmo_axe_z': {'fr': 'redshift z', 'en': 'redshift z'},
    'cosmo_axe_d': {'fr': 'distance (G al)', 'en': 'distance (Gly)'},
    'cosmo_calcul_courbes': {'fr': 'Calcul des courbes…', 'en': 'Computing curves…'},
    'cosmo_csv_table': {'fr': 'Exporter le tableau (CSV)…', 'en': 'Export the table (CSV)…'},
    'cosmo_csv_table_aide': {'fr': 'Écrit les grandeurs du tableau (valeurs brutes, unités, incertitudes) dans un '
                                   'fichier CSV (séparateur « ; », UTF-8), lisible par un tableur.',
                             'en': 'Write the table quantities (raw values, units, uncertainties) to a CSV file '
                                   '(« ; » separator, UTF-8), readable by a spreadsheet.'},
    'cosmo_csv_courbes': {'fr': 'Exporter les courbes (CSV)…', 'en': 'Export the curves (CSV)…'},
    'cosmo_csv_courbes_aide': {'fr': 'Écrit les distances et les temps sur une grille de z (300 points de 0,001 à '
                                     '1500) dans un fichier CSV.',
                               'en': 'Write distances and times on a z grid (300 points from 0.001 to 1500) to a CSV '
                                     'file.'},
    'cosmo_rien_a_exporter': {'fr': 'Rien à exporter : calculez d\'abord.', 'en': 'Nothing to export: compute first.'},
    'cosmo_ecrit': {'fr': 'Écrit : {chemin}', 'en': 'Written: {chemin}'},
    'cosmo_csv_cle': {'fr': 'cle', 'en': 'key'},
    'cosmo_csv_unite': {'fr': 'unite', 'en': 'unit'},
    'cosmo_csv_al': {'fr': 'valeur_annees_lumiere', 'en': 'value_light_years'},
    'cosmo_csv_parametres': {'fr': 'parametres', 'en': 'parameters'},
    'cosmo_credits': {'fr': 'Noyau de calcul repris du calculateur « cosmologie-redshift » du même auteur, vérifié '
                            'indépendamment (SageMath, de z = 10⁻⁸ à 1100) ; backend astropy.cosmology.',
                      'en': 'Computation core taken from the same author\'s « cosmologie-redshift » calculator, '
                            'independently checked (SageMath, from z = 10⁻⁸ to 1100); astropy.cosmology backend.'},
    # aide écran
    'cosmo_aide_html': {
        'fr': "<h3>Cosmologie</h3><p>Le redshift z d'une galaxie lointaine ne donne pas « une » distance mais plusieurs, "
              "toutes justes, qui répondent à des questions différentes. Ce module les calcule dans le modèle ΛCDM.</p>"
              "<h4>Saisir</h4><p>Tapez z (virgule ou point) et Entrée, ou cliquez un exemple, ou donnez le nom d'un "
              "objet : son redshift est demandé à SIMBAD si Internet est disponible (une requête, gardée en cache). "
              "Depuis la Banque OHP, l'onglet <i>Fiche en ligne</i> envoie directement le redshift d'un objet ici.</p>"
              "<h4>Quelle distance pour quoi ?</h4><ul><li><b>D_C</b>, comobile : où est l'objet aujourd'hui ;</li>"
              "<li><b>D_L</b>, luminosité : photométrie, F = L/(4πD_L²), module de distance ;</li><li><b>D_A</b>, "
              "angulaire : tailles sur le ciel, échelle en kpc par seconde d'arc ; elle passe par un maximum ;</li>"
              "<li><b>c·t_L</b> : chemin parcouru par la lumière, la plus intuitive et la moins physique.</li></ul>"
              "<h4>Paramètres</h4><p>Planck 2018 (H₀ = 67,66, Ωm = 0,3111, rayonnement et neutrinos compris) par défaut, "
              "avec l'incertitude 1σ propagée depuis H₀ et Ωm corrélés et, au choix, la comparaison SH0ES (tension de "
              "Hubble). Planck 2015, WMAP 9, un ΛCDM « de manuel » et un jeu personnalisé (H₀, Ωm, Ωk) servent à "
              "comparer. Une valeur hors plage est refusée avec une explication.</p>"
              "<h4>Limites</h4><p>z ≤ 0 (objet qui s'approche) ne donne pas de distance ; sous z = 0,03 la vitesse propre "
              "de l'objet domine ; au-delà de z ≈ 1090 l'univers est opaque.</p>"
              "<h4>Exporter</h4><p>Le tableau et les courbes s'exportent en CSV (« ; », UTF-8). Ligne de commande : "
              "<code>coupole cosmo 0,158</code>, <code>coupole cosmo --objet \"3C 273\"</code>, "
              "<code>coupole cosmo 1 --modele wmap9 --csv resultats.csv</code>.</p>"
              "<h4>Origine et vérification</h4><p>Noyau repris du calculateur « cosmologie-redshift » du même auteur. "
              "Vérifié le 8 octobre 2026 contre astropy et contre une intégration indépendante sous SageMath "
              "(Fermi-Dirac exacte pour les neutrinos), de z = 10⁻⁸ à 1100, univers plats et courbes : écart ≤ 3·10⁻⁶ "
              "sur les distances, ≤ 2·10⁻⁵ sur les âges.</p>",
        'en': "<h3>Cosmology</h3><p>The redshift z of a distant galaxy does not give « one » distance but several, all "
              "correct, answering different questions. This module computes them in the ΛCDM model.</p>"
              "<h4>Input</h4><p>Type z (comma or point) and Enter, or click an example, or give an object's name: its "
              "redshift is requested from SIMBAD when the Internet is available (one request, cached). From the OHP "
              "bank, the <i>Online record</i> tab sends an object's redshift straight here.</p>"
              "<h4>Which distance for what?</h4><ul><li><b>D_C</b>, comoving: where the object is today;</li><li><b>D_L"
              "</b>, luminosity: photometry, F = L/(4πD_L²), distance modulus;</li><li><b>D_A</b>, angular: sizes on "
              "the sky, scale in kpc per arcsecond; it goes through a maximum;</li><li><b>c·t_L</b>: path travelled by "
              "the light, the most intuitive and the least physical.</li></ul>"
              "<h4>Parameters</h4><p>Planck 2018 (H₀ = 67.66, Ωm = 0.3111, radiation and neutrinos included) by "
              "default, with the 1σ uncertainty propagated from correlated H₀ and Ωm and, optionally, the SH0ES "
              "comparison (Hubble tension). Planck 2015, WMAP 9, a « textbook » ΛCDM and a custom set (H₀, Ωm, Ωk) are "
              "there for comparison. An out-of-range value is refused with an explanation.</p>"
              "<h4>Limits</h4><p>z ≤ 0 (approaching object) gives no distance; below z = 0.03 the object's peculiar "
              "velocity dominates; beyond z ≈ 1090 the universe is opaque.</p>"
              "<h4>Export</h4><p>The table and curves export to CSV (« ; », UTF-8). Command line: "
              "<code>coupole cosmo 0.158</code>, <code>coupole cosmo --object \"3C 273\"</code>, "
              "<code>coupole cosmo 1 --model wmap9 --csv results.csv</code>.</p>"
              "<h4>Origin and checks</h4><p>Core taken from the same author's « cosmologie-redshift » calculator. "
              "Checked on 8 October 2026 against astropy and against an independent SageMath integration (exact "
              "Fermi-Dirac for neutrinos), from z = 10⁻⁸ to 1100, flat and curved universes: deviation ≤ 3·10⁻⁶ on "
              "distances, ≤ 2·10⁻⁵ on ages.</p>"},
    # ligne de commande
    'cosmo_meta_nom': {'fr': 'NOM', 'en': 'NAME'},
    'cosmo_cli_z': {'fr': 'redshift(s) à calculer', 'en': 'redshift(s) to compute'},
    'cosmo_cli_objet': {'fr': 'nom d\'objet : redshift demandé à SIMBAD', 'en': 'object name: redshift requested from '
                                                                             'SIMBAD'},
    'cosmo_cli_modele': {'fr': 'jeu de paramètres (défaut : planck18)', 'en': 'parameter set (default: planck18)'},
    'cosmo_cli_h0': {'fr': 'H₀ en km/s/Mpc (modèle perso)', 'en': 'H₀ in km/s/Mpc (custom model)'},
    'cosmo_cli_om': {'fr': 'Ωm total (modèle perso)', 'en': 'total Ωm (custom model)'},
    'cosmo_cli_ok': {'fr': 'Ωk, courbure (planck18 ou perso)', 'en': 'Ωk, curvature (planck18 or perso)'},
    'cosmo_cli_shoes': {'fr': 'ajoute la comparaison SH0ES (planck18)', 'en': 'add the SH0ES comparison (planck18)'},
    'cosmo_cli_sans_sigma': {'fr': 'sans les incertitudes (plus rapide)', 'en': 'without uncertainties (faster)'},
    'cosmo_cli_csv': {'fr': 'écrit les résultats dans ce fichier CSV', 'en': 'write the results to this CSV file'},
    'cosmo_cli_courbes': {'fr': 'écrit les courbes (z de ZMIN à ZMAX, N points) dans le fichier CSV donné par --csv',
                          'en': 'write the curves (z from ZMIN to ZMAX, N points) to the CSV file given by --csv'},
    'cosmo_cli_json': {'fr': 'sortie JSON', 'en': 'JSON output'},
    'cosmo_cli_aucun_z': {'fr': 'Donnez au moins un redshift, ou --objet NOM.', 'en': 'Give at least one redshift, or '
                                                                                     '--object NAME.'},
    'cosmo_cli_titre': {'fr': 'z = {z} — {modele}', 'en': 'z = {z} — {modele}'},
}
