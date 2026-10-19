"""Textes FR/EN de l'animation « L'atmosphère terrestre » (0.8.0, propre à Coupole).  Fusionnés dans
``textes.TEXTES`` (et exportés tels quels vers Coupole Web)."""

ANIM_ATMOSPHERE = {
    'anim_earthatmosphere_vue': ('Vue', 'View'),
    'anim_earthatmosphere_vue_aide': ('Épaisseur traversée, extinction et rougissement, fenêtres atmosphériques, '
                                      'réfraction.',
                                      'Thickness crossed, extinction and reddening, atmospheric windows, refraction.'),
    'anim_earthatmosphere_v_epaisseur': ('Épaisseur traversée', 'Thickness crossed'),
    'anim_earthatmosphere_v_extinction': ('Extinction et rougissement', 'Extinction and reddening'),
    'anim_earthatmosphere_v_fenetres': ('Fenêtres atmosphériques', 'Atmospheric windows'),
    'anim_earthatmosphere_v_refraction': ('Réfraction', 'Refraction'),
    'anim_earthatmosphere_hauteur': ('Hauteur', 'Altitude'),
    'anim_earthatmosphere_hauteur_aide': ('Hauteur vraie de l’astre au-dessus de l’horizon.',
                                          'True altitude of the object above the horizon.'),
    'anim_earthatmosphere_pression': ('Pression', 'Pressure'),
    'anim_earthatmosphere_pression_aide': ('Pression au sol : 1013 hPa au niveau de la mer, ≈ 740 hPa à 2 600 m '
                                           '(Paranal), ≈ 615 hPa à 4 200 m (plus hauts observatoires).',
                                           'Ground pressure: 1013 hPa at sea level, ≈ 740 hPa at 2,600 m (Paranal), '
                                           '≈ 615 hPa at 4,200 m (highest observatories).'),
    'anim_earthatmosphere_temperature': ('Température', 'Temperature'),
    'anim_earthatmosphere_temperature_aide': ('Température de l’air au sol (la réfraction diminue quand il fait '
                                              'chaud).',
                                              'Air temperature at the ground (refraction decreases when it is warm).'),
    'anim_earthatmosphere_aerosols': ('Aérosols', 'Aerosols'),
    'anim_earthatmosphere_aerosols_aide': ('Trouble d’Ångström β (épaisseur optique des aérosols à 1 µm) : 0,02 site '
                                           'très pur, 0,05 bon site, 0,2 air chargé de poussières ou de pollution.',
                                           'Ångström turbidity β (aerosol optical depth at 1 µm): 0.02 very clean '
                                           'site, 0.05 good site, 0.2 dusty or polluted air.'),
    'anim_earthatmosphere_latitude': ('Latitude', 'Latitude'),
    'anim_earthatmosphere_latitude_aide': ('Latitude du lieu (pour l’avance du lever et le retard du coucher).',
                                           'Latitude of the place (for the earlier rising and later setting).'),
    'anim_earthatmosphere_exagerer': ('Réfraction exagérée', 'Exaggerated refraction'),
    'anim_earthatmosphere_exagerer_aide': ('Multiplie la réfraction par 40 sur le dessin du rayon pour voir sa '
                                           'courbure (les valeurs restent vraies).',
                                           'Multiplies refraction by 40 in the drawing of the ray to see its '
                                           'curvature (values stay true).'),
    'anim_earthatmosphere_val_x_secz': ('Masse d’air sec z', 'Airmass sec z'),
    'anim_earthatmosphere_val_x_ky': ('Masse d’air (Kasten & Young)', 'Airmass (Kasten & Young)'),
    'anim_earthatmosphere_val_x_pickering': ('Masse d’air (Pickering)', 'Airmass (Pickering)'),
    'anim_earthatmosphere_val_chemin': ('Trajet dans 8 km d’atmosphère', 'Path through 8 km of atmosphere'),
    'anim_earthatmosphere_val_dm': ('Extinction en {b}', 'Extinction in {b}'),
    'anim_earthatmosphere_val_refraction': ('Réfraction', 'Refraction'),
    'anim_earthatmosphere_val_apparente': ('Hauteur apparente', 'Apparent altitude'),
    'anim_earthatmosphere_val_aplatissement': ('Aplatissement du Soleil à l’horizon', 'Flattening of the Sun at the '
                                                                                     'horizon'),
    'anim_earthatmosphere_val_avance': ('Lever avancé, coucher retardé', 'Earlier rising, later setting'),
    'anim_earthatmosphere_val_dispersion': ('Dispersion 0,45 – 0,65 µm', 'Dispersion 0.45 – 0.65 µm'),
    'anim_earthatmosphere_t_coupe': ('Coupe de la Terre et de l’atmosphère', 'Cross-section of the Earth and the '
                                                                            'atmosphere'),
    'anim_earthatmosphere_t_masse': ('Masse d’air selon la hauteur', 'Airmass versus altitude'),
    'anim_earthatmosphere_c_tropo': ('troposphère (0–12 km)', 'troposphere (0–12 km)'),
    'anim_earthatmosphere_c_strato': ('stratosphère (12–50 km)', 'stratosphere (12–50 km)'),
    'anim_earthatmosphere_c_meso': ('mésosphère (50–85 km)', 'mesosphere (50–85 km)'),
    'anim_earthatmosphere_e_couche': ('couche homogène de 8 km (échelle de hauteur)', 'homogeneous 8 km layer (scale '
                                                                                     'height)'),
    'anim_earthatmosphere_e_trajet': ('trajet {l} km, X = {x}', 'path {l} km, X = {x}'),
    'anim_earthatmosphere_e_agrandie': ('épaisseurs agrandies × {k}', 'thicknesses enlarged × {k}'),
    'anim_earthatmosphere_sphere': ('coquille de 8 km', '8 km shell'),
    'anim_earthatmosphere_t_tau': ('Épaisseur optique au zénith', 'Optical depth at the zenith'),
    'anim_earthatmosphere_total': ('total', 'total'),
    'anim_earthatmosphere_ozone': ('ozone (Chappuis)', 'ozone (Chappuis)'),
    'anim_earthatmosphere_t_soleil': ('Le Soleil transmis', 'The transmitted Sun'),
    'anim_earthatmosphere_e_transmis': ('{t} % de la lumière visible (X = {x})', '{t} % of the visible light '
                                                                                 '(X = {x})'),
    'anim_earthatmosphere_e_rougit': ('le bleu est diffusé : le Soleil rougit', 'blue is scattered: the Sun reddens'),
    'anim_earthatmosphere_t_fenetres': ('Transmission de l’atmosphère au zénith, des rayons γ à la radio',
                                        'Atmospheric transmission at the zenith, from γ rays to radio'),
    'anim_earthatmosphere_t_fenetres_zoom': ('Du proche UV à l’infrarouge moyen : bandes photométriques et absorptions',
                                             'From near UV to mid-infrared: photometric bands and absorptions'),
    'anim_earthatmosphere_e_x': ('à la hauteur choisie (X = {x})', 'at the chosen altitude (X = {x})'),
    'anim_earthatmosphere_transmission': ('Transmission', 'Transmission'),
    'anim_earthatmosphere_d_gamma_x': ('γ, X', 'γ, X'),
    'anim_earthatmosphere_d_uv_lointain': ('UV lointain', 'far UV'),
    'anim_earthatmosphere_d_uv_ozone': ('UV (ozone)', 'UV (ozone)'),
    'anim_earthatmosphere_d_ir_lointain': ('IR lointain', 'far IR'),
    'anim_earthatmosphere_d_submm': ('submm', 'submm'),
    'anim_earthatmosphere_d_mm': ('mm', 'mm'),
    'anim_earthatmosphere_d_radio': ('radio', 'radio'),
    'anim_earthatmosphere_d_ionosphere': ('ionosphère', 'ionosphere'),
    'anim_earthatmosphere_e_radio': ('fenêtre radio : radiotélescopes au sol', 'radio window: ground radio '
                                                                              'telescopes'),
    'anim_earthatmosphere_e_espace': ('γ, X, UV, IR lointain : satellites', 'γ, X, UV, far IR: satellites'),
    'anim_earthatmosphere_source_eso': ('0,3–30 µm : modèle de ciel de l’ESO (SkyCalc, Paranal, 2,5 mm d’eau '
                                        'précipitable) ; ailleurs : schéma',
                                        '0.3–30 µm: ESO sky model (SkyCalc, Paranal, 2.5 mm of precipitable water); '
                                        'elsewhere: sketch'),
    'anim_earthatmosphere_t_rayon': ('Un rayon dans des couches d’indice décroissant', 'A ray through layers of '
                                                                                       'decreasing index'),
    'anim_earthatmosphere_e_apparente': ('direction apparente', 'apparent direction'),
    'anim_earthatmosphere_e_comprime': ('distances horizontales comprimées × {k}', 'horizontal distances compressed '
                                                                                   '× {k}'),
    'anim_earthatmosphere_e_exagere': ('réfraction × 40', 'refraction × 40'),
    'anim_earthatmosphere_t_refraction': ('Réfraction selon la hauteur', 'Refraction versus altitude'),
    'anim_earthatmosphere_t_soleil_couchant': ('Le Soleil à l’horizon, à l’échelle', 'The Sun at the horizon, to '
                                                                                    'scale'),
    'anim_earthatmosphere_e_aplati': ('aplati : {r} × son diamètre', 'flattened: {r} × its diameter'),
    'anim_earthatmosphere_e_vrai': ('pointillés : position vraie, sous l’horizon', 'dotted: true position, below '
                                                                                  'the horizon'),
    'anim_earthatmosphere_e_avance': ('lever avancé et coucher retardé de {t} min (latitude {lat}°)',
                                      'rising earlier and setting later by {t} min (latitude {lat}°)'),
    'anim_earthatmosphere_e_dispersion': ('bleu, vert, rouge : {d}″ d’écart', 'blue, green, red: {d}″ apart'),
    'anim_earthatmosphere_adapte': ('Propre à Coupole (pas dans ClassAction) : modèle de ciel de l’ESO, Kasten & '
                                    'Young (1989), Pickering (2002), Hansen & Travis (1974), Ångström (1929), Bennett '
                                    '(1982), Sæmundsson (1986), Ciddor (1996)',
                                    'Coupole’s own (not in ClassAction): ESO sky model, Kasten & Young (1989), '
                                    'Pickering (2002), Hansen & Travis (1974), Ångström (1929), Bennett (1982), '
                                    'Sæmundsson (1986), Ciddor (1996)'),
    'anim_earthatmosphere_lien': ('Sources : fichier NOTICE de Coupole', 'Sources: Coupole NOTICE file'),
    'anim_earthatmosphere_a_voir': (
        'Près de l’horizon, la lumière traverse jusqu’à 38 fois plus d’air qu’au zénith : les étoiles y pâlissent '
        '(Δm = k X) et rougissent, car l’air diffuse le bleu bien plus que le rouge (Rayleigh, ∝ λ⁻⁴). L’atmosphère '
        'ne laisse passer que le visible, quelques fenêtres infrarouges et la radio : d’où les télescopes en altitude '
        'et dans l’espace. Elle courbe aussi les rayons : un astre paraît plus haut qu’il n’est (34′ à l’horizon, '
        'plus que le diamètre du Soleil), le Soleil couchant s’aplatit et se lève 2 à 3 min plus tôt. Dans le défi '
        'parallaxe, la réfraction se retire avant le calcul.',
        'Near the horizon, light crosses up to 38 times more air than at the zenith: stars fade there (Δm = k X) and '
        'redden, because air scatters blue much more than red (Rayleigh, ∝ λ⁻⁴). The atmosphere only lets through '
        'the visible, a few infrared windows and radio: hence telescopes at altitude and in space. It also bends '
        'rays: an object looks higher than it is (34′ at the horizon, more than the Sun’s diameter), the setting Sun '
        'flattens and rises 2 to 3 min earlier. In the parallax challenge, refraction is removed before computing.'),
}
