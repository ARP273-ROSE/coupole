"""Textes du module « Animations » (FR/EN) : interface, réglages et valeurs de chaque animation, catalogue."""
from .catalogue import THEMES
from .textes_catalogue import NOMS_DESCRIPTIONS


def _t(fr, en):
    return {'fr': fr, 'en': en}


TEXTES = {
    # ------------------------------------------------------------ module, catalogue
    'anim_titre': _t('Animations', 'Animations'),
    'anim_recherche_aide': _t("Chercher une animation par son nom (français ou anglais) ou un mot de sa description.",
                              'Search an animation by its name (French or English) or a word of its description.'),
    'anim_recherche_indice': _t('Chercher (saisons, Lune, Kepler…)', 'Search (seasons, Moon, Kepler…)'),
    'anim_theme': _t('Thème', 'Topic'),
    'anim_theme_aide': _t('Ne montrer que les animations d’un thème.', 'Show only the animations of one topic.'),
    'anim_theme_tous': _t('Tous les thèmes', 'All topics'),
    'anim_etat': _t('État', 'Status'),
    'anim_etat_aide': _t('Toutes les animations du catalogue, celles déjà refaites dans Coupole, ou celles à venir.',
                         'Every animation of the catalogue, those already remade in Coupole, or those to come.'),
    'anim_etat_toutes': _t('Toutes', 'All'),
    'anim_etat_faites': _t('Disponibles', 'Available'),
    'anim_etat_a_venir': _t('À venir', 'Coming'),
    'anim_liste_aide': _t('Catalogue par thème. Double-clic ou Entrée : ouvrir l’animation (les animations « à venir » '
                          'sont décrites mais pas encore refaites).',
                          'Catalogue by topic. Double-click or Enter: open the animation (« coming » animations are '
                          'described but not yet remade).'),
    'anim_compte': _t('{faites} animations disponibles sur {total} du catalogue d’origine.',
                      '{faites} animations available out of {total} in the original catalogue.'),
    'anim_disponible': _t('disponible', 'available'),
    'anim_a_venir': _t('à venir', 'coming'),
    'anim_titre_origine': _t('Titre d’origine : {titre}', 'Original title: {titre}'),
    'anim_theme_de': _t('Thème : {theme}', 'Topic: {theme}'),
    'anim_choisir': _t('Choisissez une animation dans le catalogue, à gauche.',
                       'Choose an animation in the catalogue, on the left.'),
    'anim_pas_encore': _t('Cette animation n’est pas encore refaite dans Coupole ; elle le sera dans un prochain lot.',
                          'This animation is not remade in Coupole yet; it will come in a later batch.'),
    'anim_credits': _t('D’après ClassAction, University of Nebraska-Lincoln Astronomy Education (Apache License 2.0). '
                       'Refait en Python : calculs vérifiés, interface bilingue.',
                       'After ClassAction, University of Nebraska-Lincoln Astronomy Education (Apache License 2.0). '
                       'Remade in Python: checked computations, bilingual interface.'),
    'anim_erreur': _t('Impossible d’ouvrir cette animation : {erreur}', 'Unable to open this animation: {erreur}'),
    'anim_version_web': _t('Version web ↗', 'Web version ↗'),
    'anim_version_web_aide': _t('Ouvrir cette animation, avec ses réglages, dans Coupole Web '
                                '(arp273-rose.github.io/coupole-web) : les mêmes animations dans un navigateur, sur '
                                'ordinateur, tablette ou téléphone, sans installation.',
                                'Open this animation, with its settings, in Coupole Web '
                                '(arp273-rose.github.io/coupole-web): the same animations in a browser, on a computer, '
                                'tablet or phone, with nothing to install.'),
    'anim_aide_tourner': _t('Glisser avec la souris : faire tourner la vue.', 'Drag with the mouse: rotate the view.'),
    'anim_aide_tourner_deplacer': _t('Glisser avec la souris : faire tourner la sphère, ou déplacer un objet en le '
                                     'saisissant.', 'Drag with the mouse: rotate the sphere, or move an object by '
                                     'grabbing it.'),
    'anim_aide_deplacer': _t('Glisser avec la souris : déplacer les objets de la scène.',
                             'Drag with the mouse: move the objects in the scene.'),
    'anim_lecture': _t('▶ Lecture', '▶ Play'),
    'anim_lecture_aide': _t('Lancer ou mettre en pause l’animation.', 'Start or pause the animation.'),
    'anim_pause': _t('⏸ Pause', '⏸ Pause'),
    'anim_vitesse': _t('Vitesse', 'Speed'),
    'anim_vitesse_aide': _t('Vitesse de l’animation, de 0,1 à 10 fois la vitesse normale (échelle logarithmique).',
                            'Animation speed, from 0.1 to 10 times the normal speed (logarithmic scale).'),
    'anim_reinitialiser': _t('Réinitialiser', 'Reset'),
    'anim_reinitialiser_aide': _t('Remettre les réglages, la vue et le temps de cette animation à leur état de départ.',
                                  'Put back the settings, view and time of this animation to their initial state.'),
    'anim_aide_html': _t(
        "<h3>Animations</h3><p>Les animations pédagogiques ClassAction de l’université du Nebraska-Lincoln, écrites à "
        "l’origine en Flash, refaites en Python pour Windows, macOS et Linux. Les 92 animations du catalogue sont "
        "toutes disponibles, classées par thème ; celles qui n’étaient que des films sont devenues des simulations. "
        "S’y ajoutent, dans « Astronomie antique », la machine d’Anticythère en 3D, adaptée d’Anticythere3D, du même "
        "auteur (manivelle à la souris, cadrans gravés en grec, machine ouverte ou éclatée, rapports exacts des "
        "engrenages ; application complète : github.com/ARP273-ROSE/Anticythere3D), et, dans « Milieu interstellaire "
        "et formation des étoiles », Orion en 3D : la constellation dépliée à ses vraies distances, avec ses nuages, la "
        "nébuleuse d’Orion et la Tête de Cheval, et une plongée avec les images de l’ESO et de Hubble.</p>"
        "<h4>Fiches au survol</h4><p>Dans Orion en 3D, la Grande Ourse 3D, l’horloge de la Grande Ourse, le lever "
        "héliaque, la comparaison des repères et le diagramme HR, survoler (ou toucher) une étoile ou une nébuleuse "
        "ouvre sa fiche, posée à côté d’elle : nom, type, magnitudes, distance et son incertitude, température, rayon, "
        "luminosité, et la source de chaque valeur (SIMBAD, Gaia DR3, Hipparcos, articles). Au clavier : Tab passe "
        "d’un objet à l’autre, du plus brillant au plus faible, les flèches aussi quand une fiche est ouverte, Échap "
        "la ferme ; le résumé est lu par les lecteurs d’écran. Les étoiles réelles ont leur couleur vraie (corps noir "
        "à leur température, CIE 1931).</p>"
        "<h4>Spectres</h4><p>L’Explorateur de spectres et la Parallaxe spectroscopique calculent les raies "
        "(Saha–Boltzmann sur des atmosphères modèles, 133 raies du NIST, bandes moléculaires de TiO et de CH, continu "
        "de Planck) ; les cas extrapolés et l’ancien étalonnage des magnitudes absolues sont signalés.</p>"
        "<h4>Manipuler</h4><ul><li><b>Glisser</b> sur une sphère la fait tourner (le point saisi suit la souris) ; sur "
        "une étoile, la Lune, la Terre ou un observateur, les déplace. Ce que fait la souris dans chaque animation est "
        "rappelé en petit sous la scène.</li><li><b>Lecture / Pause</b> et <b>Vitesse</b> (0,1 à 10 ×) animent le temps ; "
        "<b>Réinitialiser</b> revient à l’état de départ.</li><li>Chaque réglage a un curseur et un champ numérique ; "
        "les valeurs calculées s’affichent sous les réglages.</li><li>Les réglages sont gardés d’une session à "
        "l’autre.</li><li><b>Version web ↗</b> ouvre l’animation, avec ses réglages, dans Coupole Web "
        "(arp273-rose.github.io/coupole-web), dans un navigateur, sur ordinateur, tablette ou téléphone.</li></ul>"
        "<h4>Rendu</h4><p>Soleil, Lune, Terre et planètes en sphères ombrées (côté nuit tourné à l’opposé du Soleil), "
        "formules mises en forme (fractions, exposants, indices, radicaux ; police STIX Two Math), étiquettes placées "
        "sans se chevaucher. Simulateur jour-nuit : côtes Natural Earth, projection équirectangulaire, polaire (pôle "
        "Nord ou Sud) ou globe 3D à tourner à la souris (molette : zoom ; double-clic : face au point subsolaire). "
        "Simulateur des ombres d’éclipse : « Rejouer une éclipse » montre chacune des 133 éclipses de la table "
        "2015–2044 en proportions réelles.</p><h4>Calculs</h4><p>Temps sidéral (IAU 1982), obliquité (IAU 2006), position du Soleil et "
        "équation du temps (Meeus, précision 0,01°), changements de repère, équation de Kepler, module de distance, "
        "cônes d’ombre, phases moyennes de la Lune et nœuds de son orbite (saisons d’éclipses), précession, marées "
        "d’équilibre, périodes synodiques, gravitation de Newton, loi de Stefan-Boltzmann et constantes solaires de "
        "l’UAI, lois de Planck et de Wien, niveaux de l’hydrogène, réfraction et formules de Fresnel, effet Doppler "
        "par le temps retardé, vitesses radiales, transits et éclipses (aire exacte de recouvrement des disques), "
        "barycentre du Système solaire, bilans des réactions de fusion : vérifiés avec SageMath, astropy et ERFA "
        "(voir le manuel, chapitre Animations). Les étalonnages empiriques de l’original (type spectral, corrections "
        "bolométriques, séquences du diagramme HR) sont repris tels quels ; les données réelles (exoplanètes, "
        "planètes, binaires à éclipses, spectres) citent leur source dans le fichier NOTICE.</p>"
        "<p>D’après ClassAction, University of Nebraska-Lincoln Astronomy Education, Apache License 2.0 (fichier "
        "NOTICE).</p>",
        "<h3>Animations</h3><p>The ClassAction teaching animations of the University of Nebraska-Lincoln, originally "
        "written in Flash, remade in Python for Windows, macOS and Linux. All 92 animations of the catalogue are "
        "available, sorted by topic; those that were only movies have become simulations. Added to them are, in "
        "“Ancient astronomy”, the Antikythera Mechanism in 3D, adapted from Anticythere3D, by the same author (crank "
        "turned with the mouse, dials engraved in Greek, open or exploded machine, exact gear ratios; full "
        "application: github.com/ARP273-ROSE/Anticythere3D), and, in “Interstellar Medium and Star Formation”, Orion "
        "in 3D: the constellation unfolded to its true distances, with its clouds, the Orion Nebula and the Horsehead, "
        "and a dive with ESO and Hubble images.</p>"
        "<h4>Hover data sheets</h4><p>In Orion in 3D, Big Dipper 3D, the Big Dipper clock, heliacal rising, the "
        "coordinate systems comparison and the HR diagram, hovering over (or touching) a star or a nebula opens its "
        "data sheet, laid next to it: name, type, magnitudes, distance and its uncertainty, temperature, radius, "
        "luminosity, and the source of each value (SIMBAD, Gaia DR3, Hipparcos, papers). With the keyboard: Tab goes "
        "from one object to the next, brightest first, so do the arrows while a sheet is open, Escape closes it; the "
        "summary is read by screen readers. Real stars have their true colour (black body at their temperature, CIE "
        "1931).</p>"
        "<h4>Spectra</h4><p>The Spectrum Explorer and the Spectroscopic Parallax compute the lines (Saha–Boltzmann on "
        "model atmospheres, 133 NIST lines, TiO and CH molecular bands, Planck continuum); extrapolated cases and the "
        "former absolute-magnitude calibration are flagged.</p>"
        "<h4>Handling</h4><ul><li><b>Dragging</b> a sphere rotates it (the grabbed point follows the mouse); dragging "
        "a star, the Moon, the Earth or an observer moves it. What the mouse does in each animation is recalled in "
        "small print below the scene.</li><li><b>Play / Pause</b> and <b>Speed</b> (0.1 to 10 ×) run the time; <b>Reset</b> "
        "goes back to the initial state.</li><li>Each setting has a slider and a numeric field; computed values are "
        "shown below the settings.</li><li>Settings are kept from one session to the next.</li><li><b>Web version ↗</b> "
        "opens the animation, with its settings, in Coupole Web (arp273-rose.github.io/coupole-web), in a browser, on "
        "a computer, tablet or phone.</li></ul><h4>Rendering</h4><p>Sun, Moon, Earth and planets as shaded spheres "
        "(night side turned away from the Sun), typeset formulas (fractions, superscripts, subscripts, radicals; STIX "
        "Two Math font), labels placed without overlapping. Daylight simulator: Natural Earth coastlines, "
        "equirectangular or polar (North or South Pole) projection, or a 3D globe rotated with the mouse (wheel: zoom; "
        "double-click: face the subsolar point). Eclipse shadow simulator: “Replay an eclipse” shows each of the 133 "
        "eclipses of the 2015–2044 table to true scale.</p>"
        "<h4>Computations</h4><p>Sidereal time (IAU 1982), obliquity (IAU 2006), position of the Sun and equation of "
        "time (Meeus, 0.01° accuracy), coordinate changes, Kepler’s equation, distance modulus, shadow cones, mean "
        "lunar phases and nodes of the lunar orbit (eclipse seasons), precession, equilibrium tides, synodic periods, "
        "Newton’s gravitation, Stefan-Boltzmann law and IAU solar constants, Planck’s and Wien’s laws, hydrogen levels, "
        "refraction and Fresnel formulas, Doppler effect through the retarded time, radial velocities, transits and "
        "eclipses (exact overlap area of the discs), barycenter of the Solar System, energy budgets of the fusion "
        "reactions: checked with SageMath, astropy and ERFA (see the manual, Animations chapter). The empirical "
        "calibrations of the original (spectral type, bolometric corrections, HR diagram sequences) are kept as they "
        "are; the real data (exoplanets, planets, eclipsing binaries, spectra) cite their source in the NOTICE "
        "file.</p>"
        "<p>After ClassAction, University of Nebraska-Lincoln Astronomy Education, Apache License 2.0 (NOTICE "
        "file).</p>"),
    'anim_cli_aide': _t('Catalogue des animations (liste, description)', 'Animation catalogue (list, description)'),
    'anim_cli_liste': _t('Liste les animations du catalogue (état, thème, nom).',
                         'List the animations of the catalogue (status, topic, name).'),
    'anim_cli_info': _t('Décrit une animation (identifiant ClassAction).', 'Describe an animation (ClassAction id).'),
    'anim_cli_id': _t('identifiant ClassAction (ex. sunmotions)', 'ClassAction id (e.g. sunmotions)'),
    'anim_cli_meta_id': _t('ID', 'ID'),
    'anim_cli_inconnue': _t('Animation inconnue : {id}', 'Unknown animation: {id}'),
    'anim_cli_faites': _t('seulement les animations disponibles', 'only the available animations'),
    # ------------------------------------------------------------ unités, mois, points cardinaux
    'anim_duree_hm': _t('{h} h {m} min', '{h} h {m} min'),
    'anim_u_annees': _t('ans', 'years'),
    'anim_u_jour': _t('jour', 'day'),
    'anim_pc_n': _t('N', 'N'), 'anim_pc_s': _t('S', 'S'), 'anim_pc_e': _t('E', 'E'), 'anim_pc_o': _t('O', 'W'),
    # ------------------------------------------------------------ réglages communs
    'anim_c_latitude': _t('Latitude', 'Latitude'),
    'anim_c_latitude_aide': _t('Latitude de l’observateur, de −90° (pôle Sud) à +90° (pôle Nord).',
                               'Latitude of the observer, from −90° (South Pole) to +90° (North Pole).'),
    'anim_c_longitude': _t('Longitude', 'Longitude'),
    'anim_c_longitude_aide': _t('Longitude, de −180° (ouest) à +180° (est) du méridien de Greenwich.',
                                'Longitude, from −180° (west) to +180° (east) of the Greenwich meridian.'),
    'anim_c_azimut': _t('Azimut', 'Azimuth'),
    'anim_c_azimut_aide': _t('Azimut, compté depuis le nord vers l’est (nord 0°, est 90°, sud 180°, ouest 270°).',
                             'Azimuth, measured from north toward east (north 0°, east 90°, south 180°, west 270°).'),
    'anim_c_hauteur': _t('Hauteur', 'Altitude'),
    'anim_c_hauteur_aide': _t('Hauteur au-dessus de l’horizon (négative dessous), de −90° (nadir) à +90° (zénith).',
                              'Altitude above the horizon (negative below), from −90° (nadir) to +90° (zenith).'),
    'anim_c_ra': _t('Ascension droite', 'Right ascension'),
    'anim_c_ra_aide': _t('Ascension droite α, en heures (1 h = 15°), comptée vers l’est depuis le point vernal.',
                         'Right ascension α, in hours (1 h = 15°), measured eastward from the vernal point.'),
    'anim_c_dec': _t('Déclinaison', 'Declination'),
    'anim_c_dec_aide': _t('Déclinaison δ, angle au nord (+) ou au sud (−) de l’équateur céleste.',
                          'Declination δ, angle north (+) or south (−) of the celestial equator.'),
    'anim_c_tsl': _t('Temps sidéral local', 'Local sidereal time'),
    'anim_c_tsl_aide': _t('Temps sidéral local : ascension droite des étoiles qui passent au méridien.',
                          'Local sidereal time: right ascension of the stars crossing the meridian.'),
    'anim_c_jour': _t('Jour de l’année', 'Day of the year'),
    'anim_c_jour_aide': _t('Jour de l’année (0 = 1er janvier, 79 ≈ équinoxe de mars, 172 ≈ solstice de juin), année '
                           '2026.',
                           'Day of the year (0 = January 1, 79 ≈ March equinox, 172 ≈ June solstice), year 2026.'),
    'anim_c_heure': _t('Heure', 'Time'),
    'anim_c_heure_aide': _t('Heure solaire moyenne locale (heure civile sans fuseau horaire ni heure d’été).',
                            'Local mean solar time (civil time without time zone or daylight saving time).'),
    'anim_c_date': _t('Date', 'Date'),
}

for _i in range(1, 13):
    TEXTES['anim_mois_%d' % _i] = _t(('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
                                      'septembre', 'octobre', 'novembre', 'décembre')[_i - 1],
                                     ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                                      'September', 'October', 'November', 'December')[_i - 1])
    TEXTES['anim_mois_court_%d' % _i] = _t(('janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août',
                                            'sept.', 'oct.', 'nov.', 'déc.')[_i - 1],
                                           ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
                                            'Nov', 'Dec')[_i - 1])

THEMES_TEXTES = {
    'coordsmotion': ('Coordonnées et mouvements', 'Coordinates and Motions'),
    'lunarcycles': ('La Lune : phases et éclipses', 'Lunar Cycles'),
    'renaissance': ('Astronomie de la Renaissance : orbites', 'Renaissance Astronomy'),
    'stellarprops': ('Propriétés stellaires', 'Stellar Properties'),
    'light': ('Lumière et spectres', 'Light and Spectra'),
    'extrasolarplanets': ('Exoplanètes', 'Extrasolar Planets'),
    'binaryvariablestars': ('Étoiles doubles et variables', 'Binary and Variable Stars'),
    'ancientastro': ('Astronomie antique', 'Ancient Astronomy'),
    'solar': ('Système solaire', 'Solar System'),
    'solarsystemdebris': ('Petits corps du Système solaire', 'Solar System Debris'),
    'sunsolarenergy': ('Le Soleil et son énergie', 'Sun and Solar Energy'),
    'ismstarformation': ('Milieu interstellaire et formation des étoiles', 'Interstellar Medium and Star Formation'),
    'milkyway': ('La Voie lactée', 'Milky Way'),
    'cosmology': ('Cosmologie', 'Cosmology'),
    'telescopes': ('Télescopes', 'Telescopes'),
    'intro': ('Introduction', 'Introduction'),
}
assert set(THEMES_TEXTES) == set(THEMES)
for _k, (_fr, _en) in THEMES_TEXTES.items():
    TEXTES['anim_theme_' + _k] = _t(_fr, _en)
for _id, (_nfr, _nen, _dfr, _den) in NOMS_DESCRIPTIONS.items():
    TEXTES['anim_nom_' + _id.lower()] = _t(_nfr, _nen)
    TEXTES['anim_desc_' + _id.lower()] = _t(_dfr, _den)

# ==================================================================== textes des animations
_ANIM = {
    # ------------------------------------------------------------ longlat
    'anim_longlat_format': ('Affichage', 'Display'),
    'anim_longlat_format_aide': ('Latitude et longitude en degrés décimaux (48,86°) ou sexagésimaux (48° 51′ 24″).',
                                 'Latitude and longitude in decimal degrees (48.86°) or sexagesimal (48° 51′ 24″).'),
    'anim_longlat_decimal': ('décimal', 'decimal'),
    'anim_longlat_sexagesimal': ('sexagésimal', 'sexagesimal'),
    'anim_longlat_reperes': ('Repères', 'Features'),
    'anim_longlat_reperes_aide': ('Équateur, méridien de Greenwich et ligne de changement de date.',
                                  'Equator, Greenwich meridian and International Date Line.'),
    'anim_longlat_villes': ('Villes', 'Cities'),
    'anim_longlat_villes_aide': ('Afficher une vingtaine de villes du monde (celles du simulateur d’origine).',
                                 'Show about twenty cities of the world (those of the original simulator).'),
    'anim_longlat_equateur': ('Équateur', 'Equator'),
    'anim_longlat_greenwich': ('Méridien de Greenwich', 'Prime Meridian'),
    'anim_longlat_ligne_date': ('Ligne de changement de date', 'International Date Line'),
    'anim_longlat_souris': ('Glisser le point jaune pour le déplacer, le reste du globe pour le tourner ; clic droit : '
                            'placer le point.',
                            'Drag the yellow point to move it, the rest of the globe to rotate it; right click: place '
                            'the point.'),
    # ------------------------------------------------------------ altazimuth
    'anim_altazimuth_zenith': ('Zénith', 'Zenith'),
    'anim_altazimuth_zenith_aide': ('Nommer le zénith, point du ciel à la verticale de l’observateur.',
                                    'Label the zenith, the point of the sky straight above the observer.'),
    'anim_altazimuth_nadir': ('Nadir', 'Nadir'),
    'anim_altazimuth_nadir_aide': ('Nommer le nadir, à l’opposé du zénith.', 'Label the nadir, opposite the zenith.'),
    'anim_altazimuth_horizon': ('Plan de l’horizon', 'Horizon plane'),
    'anim_altazimuth_horizon_aide': ('Nommer le plan de l’horizon.', 'Label the horizon plane.'),
    'anim_altazimuth_plan_horizon': ('Plan de l’horizon', 'Horizon plane'),
    'anim_altazimuth_meridien': ('Méridien', 'Meridian'),
    'anim_altazimuth_meridien_aide': ('Montrer le méridien : du nord au sud en passant par le zénith.',
                                      'Show the meridian: from north to south through the zenith.'),
    'anim_altazimuth_distance_zenithale': ('Distance zénithale', 'Zenith distance'),
    # ------------------------------------------------------------ radecdemo
    'anim_radecdemo_est': ('Direction de l’est', 'East direction'),
    'anim_radecdemo_est_aide': ('Flèche vers l’est : sens de l’ascension droite croissante.',
                                'Arrow toward east: direction of increasing right ascension.'),
    'anim_radecdemo_ecliptique': ('Écliptique', 'Ecliptic'),
    'anim_radecdemo_ecliptique_aide': ('Tracer l’écliptique, inclinée de 23,44° sur l’équateur céleste.',
                                       'Draw the ecliptic, inclined by 23.44° to the celestial equator.'),
    'anim_radecdemo_poles_terre': ('Pôles terrestres', 'Earth’s poles'),
    'anim_radecdemo_poles_terre_aide': ('Nommer les pôles de la Terre.', 'Label the Earth’s poles.'),
    'anim_radecdemo_equateur': ('Équateur terrestre', 'Earth’s equator'),
    'anim_radecdemo_equateur_aide': ('Nommer l’équateur de la Terre.', 'Label the Earth’s equator.'),
    'anim_radecdemo_poles_ciel': ('Pôles célestes', 'Celestial poles'),
    'anim_radecdemo_poles_ciel_aide': ('Nommer les pôles nord et sud célestes, prolongements de l’axe de la Terre.',
                                       'Label the north and south celestial poles, extensions of the Earth’s axis.'),
    'anim_radecdemo_equateur_celeste': ('Équateur céleste', 'Celestial equator'),
    'anim_radecdemo_equateur_celeste_aide': ('Nommer l’équateur céleste, projection de l’équateur terrestre.',
                                             'Label the celestial equator, projection of the Earth’s equator.'),
    'anim_radecdemo_zero': ('Cercle horaire 0 h', '0h hour circle'),
    'anim_radecdemo_zero_aide': ('Nommer le cercle horaire 0 h, origine des ascensions droites (point vernal).',
                                 'Label the 0h hour circle, origin of right ascensions (vernal point).'),
    'anim_radecdemo_l_ecliptique': ('écliptique', 'ecliptic'),
    'anim_radecdemo_l_pole_nord': ('pôle Nord', 'North Pole'),
    'anim_radecdemo_l_pole_sud': ('pôle Sud', 'South Pole'),
    'anim_radecdemo_l_equateur': ('équateur', 'equator'),
    'anim_radecdemo_l_pnc': ('pôle nord céleste', 'north celestial pole'),
    'anim_radecdemo_l_psc': ('pôle sud céleste', 'south celestial pole'),
    'anim_radecdemo_l_equateur_celeste': ('équateur céleste', 'celestial equator'),
    'anim_radecdemo_l_zero': ('0 h', '0h'),
    # ------------------------------------------------------------ angle horaire
    'anim_siderealtimeandhourangledemo_arc': ('Arc de l’angle horaire', 'Hour angle arc'),
    'anim_siderealtimeandhourangledemo_arc_aide': ('Tracer l’angle horaire le long du parallèle de l’étoile, depuis '
                                                   'le méridien (positif vers l’ouest).',
                                                   'Draw the hour angle along the star’s parallel, from the meridian '
                                                   '(positive toward west).'),
    'anim_siderealtimeandhourangledemo_h': ('Angle horaire H = TSL − α', 'Hour angle H = LST − α'),
    # ------------------------------------------------------------ mouvements du Soleil
    'anim_sunmotions_mode': ('Animation', 'Animation'),
    'anim_sunmotions_mode_aide': ('En continu (le temps s’écoule), en boucle sur une journée, ou jour par jour à la '
                                  'même heure (analemme).',
                                  'Continuous (time flows), looping over one day, or day by day at the same time '
                                  '(analemma).'),
    'anim_sunmotions_continu': ('en continu', 'continuous'),
    'anim_sunmotions_boucle': ('boucle sur la journée', 'loop over the day'),
    'anim_sunmotions_pas': ('jour par jour', 'day by day'),
    'anim_sunmotions_parallele': ('Trajet du jour', 'Daily path'),
    'anim_sunmotions_parallele_aide': ('Parallèle de déclinaison du Soleil : sa course diurne.',
                                       'Declination circle of the Sun: its daily path.'),
    'anim_sunmotions_ecliptique': ('Écliptique', 'Ecliptic'),
    'anim_sunmotions_ecliptique_aide': ('Écliptique : trajet annuel du Soleil parmi les étoiles.',
                                        'Ecliptic: annual path of the Sun among the stars.'),
    'anim_sunmotions_mois': ('Mois', 'Months'),
    'anim_sunmotions_mois_aide': ('Position du Soleil sur l’écliptique au milieu de chaque mois.',
                                  'Position of the Sun on the ecliptic in the middle of each month.'),
    'anim_sunmotions_dessous': ('Sous l’horizon', 'Below horizon'),
    'anim_sunmotions_dessous_aide': ('Dessiner aussi la partie de la sphère située sous l’horizon.',
                                     'Also draw the part of the sphere below the horizon.'),
    'anim_sunmotions_ombre': ('Ombre', 'Shadow'),
    'anim_sunmotions_ombre_aide': ('Ombre de l’observateur, à l’opposé du Soleil, longue quand il est bas.',
                                   'Shadow of the observer, opposite the Sun, long when it is low.'),
    'anim_sunmotions_analemme': ('Analemme', 'Analemma'),
    'anim_sunmotions_analemme_aide': ('Positions du Soleil à la même heure tout au long de l’année : un « 8 » dû à '
                                      'l’obliquité et à l’excentricité de l’orbite.',
                                      'Positions of the Sun at the same time all year long: an « 8 » due to the '
                                      'obliquity and the eccentricity of the orbit.'),
    'anim_sunmotions_heure_vraie': ('Heure solaire vraie', 'Apparent solar time'),
    'anim_sunmotions_eqt': ('Équation du temps', 'Equation of time'),
    'anim_sunmotions_culmination': ('Hauteur à midi vrai', 'Altitude at apparent noon'),
    'anim_sunmotions_lever_coucher': ('Lever / coucher', 'Sunrise / sunset'),
    'anim_sunmotions_az_lever': ('Azimut lever / coucher', 'Sunrise / sunset azimuth'),
    'anim_sunmotions_duree': ('Durée du jour', 'Day length'),
    'anim_sunmotions_jour_polaire': ('jour polaire (le Soleil ne se couche pas)', 'polar day (the Sun does not set)'),
    'anim_sunmotions_nuit_polaire': ('nuit polaire (le Soleil ne se lève pas)', 'polar night (the Sun does not rise)'),
    # ------------------------------------------------------------ saisons (NAAP)
    'anim_eclipticsimulator_vue_terre': ('Vue de la Terre', 'Earth view'),
    'anim_eclipticsimulator_vue_terre_aide': ('La Terre vue de côté (le Soleil à gauche) ou depuis le Soleil.',
                                              'The Earth seen from the side (Sun on the left) or from the Sun.'),
    'anim_eclipticsimulator_cote': ('de côté', 'from the side'),
    'anim_eclipticsimulator_soleil': ('depuis le Soleil', 'from the Sun'),
    'anim_eclipticsimulator_observateur': ('Pour l’observateur', 'For the observer'),
    'anim_eclipticsimulator_observateur_aide': ('Angle des rayons du Soleil à midi, ou étalement d’un faisceau de '
                                                'lumière sur le sol (∝ 1 / sin h).',
                                                'Angle of the Sun’s rays at noon, or spread of a light beam on the '
                                                'ground (∝ 1 / sin h).'),
    'anim_eclipticsimulator_angle': ('angle des rayons', 'sunlight angle'),
    'anim_eclipticsimulator_faisceau': ('étalement du faisceau', 'sunbeam spread'),
    'anim_eclipticsimulator_subsolaire': ('Point subsolaire', 'Subsolar point'),
    'anim_eclipticsimulator_subsolaire_aide': ('Point de la Terre où le Soleil est au zénith (à la latitude δ☉).',
                                               'Point of the Earth where the Sun is at the zenith (at latitude δ☉).'),
    'anim_eclipticsimulator_etiquettes': ('Étiquettes', 'Labels'),
    'anim_eclipticsimulator_etiquettes_aide': ('Mois des équinoxes et solstices sur l’orbite.',
                                               'Months of the equinoxes and solstices on the orbit.'),
    'anim_eclipticsimulator_vue_orbite': ('Orbite (glisser pour tourner)', 'Orbit (drag to rotate)'),
    'anim_eclipticsimulator_vue_angle': ('Rayons du Soleil à midi', 'Sun’s rays at noon'),
    'anim_eclipticsimulator_vue_faisceau': ('Faisceau sur le sol', 'Beam on the ground'),
    'anim_eclipticsimulator_mars': ('mars', 'March'), 'anim_eclipticsimulator_juin': ('juin', 'June'),
    'anim_eclipticsimulator_sept': ('septembre', 'September'), 'anim_eclipticsimulator_dec': ('décembre', 'December'),
    'anim_eclipticsimulator_h_midi': ('Hauteur du Soleil à midi', 'Sun’s altitude at noon'),
    'anim_eclipticsimulator_etalement': ('Étalement du faisceau', 'Beam spread'),
    'anim_eclipticsimulator_surface': ('surface éclairée × {x}', 'lit area × {x}'),
    # ------------------------------------------------------------ phases de la Lune (NAAP)
    'anim_lunar_applet_phase': ('Angle de phase', 'Phase angle'),
    'anim_lunar_applet_phase_aide': ('Angle Soleil-Terre-Lune compté depuis la nouvelle lune (0°), vers l’est : '
                                     'premier quartier 90°, pleine lune 180°, dernier quartier 270°.',
                                     'Sun-Earth-Moon angle counted from new moon (0°), eastward: first quarter 90°, '
                                     'full moon 180°, third quarter 270°.'),
    'anim_lunar_applet_nom_phase': ('Phase', 'Phase'),
    'anim_lunar_applet_nom_phase_aide': ('Aller directement à une phase nommée.', 'Go straight to a named phase.'),
    'anim_lunar_applet_j_moins': ('−1 j', '−1 d'), 'anim_lunar_applet_j_plus': ('+1 j', '+1 d'),
    'anim_lunar_applet_h_moins': ('−1 h', '−1 h'), 'anim_lunar_applet_h_plus': ('+1 h', '+1 h'),
    'anim_lunar_applet_min_moins': ('−1 min', '−1 min'), 'anim_lunar_applet_min_plus': ('+1 min', '+1 min'),
    'anim_lunar_applet_j_moins_aide': ('Reculer d’un jour (la phase recule de 12,2°).',
                                       'Go back one day (the phase goes back by 12.2°).'),
    'anim_lunar_applet_j_plus_aide': ('Avancer d’un jour (la phase avance de 12,2°).',
                                      'Go forward one day (the phase moves on by 12.2°).'),
    'anim_lunar_applet_h_moins_aide': ('Reculer d’une heure.', 'Go back one hour.'),
    'anim_lunar_applet_h_plus_aide': ('Avancer d’une heure.', 'Go forward one hour.'),
    'anim_lunar_applet_min_moins_aide': ('Reculer d’une minute.', 'Go back one minute.'),
    'anim_lunar_applet_min_plus_aide': ('Avancer d’une minute.', 'Go forward one minute.'),
    'anim_lunar_applet_angle': ('Angle', 'Angle'),
    'anim_lunar_applet_angle_aide': ('Montrer l’angle de phase sur la vue de l’orbite.',
                                     'Show the phase angle on the orbit view.'),
    'anim_lunar_applet_reperes': ('Heures', 'Time ticks'),
    'anim_lunar_applet_reperes_aide': ('Heures locales autour de la Terre : midi face au Soleil, minuit à l’opposé.',
                                       'Local times around the Earth: noon facing the Sun, midnight opposite.'),
    'anim_lunar_applet_repere': ('Repère lunaire', 'Lunar landmark'),
    'anim_lunar_applet_repere_aide': ('Un cratère fixe sur la Lune : la Lune tourne toujours la même face vers la '
                                      'Terre.',
                                      'A fixed crater on the Moon: the Moon always shows the same face to the Earth.'),
    'anim_lunar_applet_vue_orbite': ('Orbite (Soleil à droite)', 'Orbit (Sun on the right)'),
    'anim_lunar_applet_vue_phase': ('Phase vue de la Terre', 'Phase seen from the Earth'),
    'anim_lunar_applet_vue_ciel': ('Ciel de l’observateur', 'Observer’s sky'),
    'anim_lunar_applet_eclairee': ('Fraction éclairée', 'Illuminated fraction'),
    'anim_lunar_applet_depuis_nouvelle': ('Depuis la nouvelle lune', 'Since new moon'),
    'anim_lunar_applet_jh': ('{j} j {h} h', '{j} d {h} h'),
    'anim_lunar_applet_elongation': ('Élongation', 'Elongation'),
    'anim_lunar_applet_h_soleil': ('Hauteur du Soleil', 'Sun’s altitude'),
    'anim_lunar_applet_h_lune': ('Hauteur de la Lune', 'Moon’s altitude'),
    'anim_phase_nl': ('nouvelle lune', 'new moon'), 'anim_phase_pc': ('premier croissant', 'waxing crescent'),
    'anim_phase_pq': ('premier quartier', 'first quarter'), 'anim_phase_gc': ('gibbeuse croissante', 'waxing gibbous'),
    'anim_phase_pl': ('pleine lune', 'full moon'), 'anim_phase_gd': ('gibbeuse décroissante', 'waning gibbous'),
    'anim_phase_dq': ('dernier quartier', 'third quarter'), 'anim_phase_dc': ('dernier croissant', 'waning crescent'),
    # ------------------------------------------------------------ rayons du Soleil
    'anim_sunsrays_cercles': ('Cercles polaires', 'Polar circles'),
    'anim_sunsrays_cercles_aide': ('Tracer les cercles polaires (±66,56°) en plus de l’équateur et des tropiques.',
                                   'Draw the polar circles (±66.56°) besides the equator and the tropics.'),
    'anim_sunsrays_latitude': ('Rayons les plus directs à la latitude', 'Most direct rays at latitude'),
    'anim_sunsrays_jour_polaire': ('Jour polaire au-delà de', 'Polar day beyond'),
    'anim_sunsrays_moment': ('Moment de l’année', 'Time of year'),
    'anim_sunsrays_equinoxe_mars': ('Équinoxe de mars', 'March equinox'),
    'anim_sunsrays_solstice_juin': ('Solstice de juin', 'June solstice'),
    'anim_sunsrays_equinoxe_sept': ('Équinoxe de septembre', 'September equinox'),
    'anim_sunsrays_solstice_dec': ('Solstice de décembre', 'December solstice'),
    'anim_sunsrays_equinoxe_mars_aide': ('Aller à l’équinoxe de mars.', 'Go to the March equinox.'),
    'anim_sunsrays_solstice_juin_aide': ('Aller au solstice de juin.', 'Go to the June solstice.'),
    'anim_sunsrays_equinoxe_sept_aide': ('Aller à l’équinoxe de septembre.', 'Go to the September equinox.'),
    'anim_sunsrays_solstice_dec_aide': ('Aller au solstice de décembre.', 'Go to the December solstice.'),
    'anim_sunsrays_equateur': ('équateur', 'equator'),
    'anim_sunsrays_tropique_cancer': ('tropique du Cancer', 'Tropic of Cancer'),
    'anim_sunsrays_tropique_capricorne': ('tropique du Capricorne', 'Tropic of Capricorn'),
    'anim_sunsrays_cercle_arctique': ('cercle arctique', 'Arctic Circle'),
    'anim_sunsrays_cercle_antarctique': ('cercle antarctique', 'Antarctic Circle'),
    # ------------------------------------------------------------ comparaison des repères
    'anim_celhorcomp_duree': ('Durée', 'Duration'),
    'anim_celhorcomp_duree_aide': ('Animer en continu, ou pendant 1, 3, 6 ou 12 heures sidérales puis s’arrêter.',
                                   'Run continuously, or during 1, 3, 6 or 12 sidereal hours, then stop.'),
    'anim_celhorcomp_continu': ('en continu', 'continuously'),
    'anim_celhorcomp_1h': ('1 heure', '1 hour'), 'anim_celhorcomp_3h': ('3 heures', '3 hours'),
    'anim_celhorcomp_6h': ('6 heures', '6 hours'), 'anim_celhorcomp_12h': ('12 heures', '12 hours'),
    'anim_celhorcomp_trainees': ('Traînées', 'Star trails'),
    'anim_celhorcomp_trainees_aide': ('Traînées des étoiles dans le ciel de l’observateur (2 h ou 6 h de rotation).',
                                      'Star trails in the observer’s sky (2 h or 6 h of rotation).'),
    'anim_celhorcomp_aucune': ('aucune', 'none'), 'anim_celhorcomp_courtes': ('courtes', 'short'),
    'anim_celhorcomp_longues': ('longues', 'long'),
    'anim_celhorcomp_grande_ourse': ('Grande Ourse', 'Big Dipper'),
    'anim_celhorcomp_grande_ourse_aide': ('Les sept étoiles de la Grande Ourse (circumpolaire en France).',
                                          'The seven stars of the Big Dipper.'),
    'anim_celhorcomp_orion': ('Orion', 'Orion'),
    'anim_celhorcomp_orion_aide': ('La constellation d’Orion, sur l’équateur céleste : visible des deux hémisphères.',
                                   'The constellation Orion, on the celestial equator: seen from both hemispheres.'),
    'anim_celhorcomp_croix_du_sud': ('Croix du Sud', 'Southern Cross'),
    'anim_celhorcomp_croix_du_sud_aide': ('La Croix du Sud (δ ≈ −60°) : invisible depuis l’Europe.',
                                          'The Southern Cross (δ ≈ −60°): never seen from Europe.'),
    'anim_celhorcomp_circumpolaire': ('Région circumpolaire', 'Circumpolar region'),
    'anim_celhorcomp_circumpolaire_aide': ('Étoiles qui ne se couchent jamais à cette latitude.',
                                           'Stars that never set at this latitude.'),
    'anim_celhorcomp_lever': ('Région de lever et coucher', 'Rise and set region'),
    'anim_celhorcomp_lever_aide': ('Étoiles qui se lèvent et se couchent.', 'Stars that rise and set.'),
    'anim_celhorcomp_jamais': ('Région jamais levée', 'Never rise region'),
    'anim_celhorcomp_jamais_aide': ('Étoiles qui ne se lèvent jamais à cette latitude.',
                                    'Stars that never rise at this latitude.'),
    'anim_celhorcomp_equateur': ('Équateur céleste', 'Celestial equator'),
    'anim_celhorcomp_equateur_aide': ('Tracer l’équateur céleste.', 'Draw the celestial equator.'),
    'anim_celhorcomp_zero': ('Cercle 0 h', '0h circle'),
    'anim_celhorcomp_zero_aide': ('Tracer le cercle horaire 0 h.', 'Draw the 0h hour circle.'),
    'anim_celhorcomp_ajouter': ('Ajouter une étoile', 'Add a star'),
    'anim_celhorcomp_ajouter_aide': ('Ajouter une étoile au hasard sur la sphère céleste.',
                                     'Add a star at random on the celestial sphere.'),
    'anim_celhorcomp_retirer': ('Retirer les étoiles', 'Remove the stars'),
    'anim_celhorcomp_retirer_aide': ('Retirer les étoiles ajoutées au hasard.', 'Remove the stars added at random.'),
    'anim_celhorcomp_celeste': ('Sphère céleste', 'Celestial sphere'),
    'anim_celhorcomp_locale': ('Ciel de l’observateur', 'Observer’s sky'),
    # ------------------------------------------------------------ plages de déclinaison
    'anim_latsim_agrandir': ('Agrandir la Terre', 'Enlarge the Earth'),
    'anim_latsim_agrandir_aide': ('Dessiner la Terre en grand (elle est en réalité minuscule devant la sphère '
                                  'céleste).',
                                  'Draw the Earth large (it is in fact tiny compared with the celestial sphere).'),
    'anim_latsim_circumpolaire': ('Circumpolaires', 'Circumpolar'),
    'anim_latsim_lever': ('Se lèvent et se couchent', 'Rise and set'),
    'anim_latsim_jamais': ('Jamais levées', 'Never rise'),
    'anim_latsim_aucune': ('aucune', 'none'),
    'anim_latsim_hauteur_pole': ('Hauteur du pôle céleste', 'Altitude of the celestial pole'),
    # ------------------------------------------------------------ écliptique
    'anim_seasonsim_mois_debut': ('Début : mois', 'Start: month'),
    'anim_seasonsim_mois_debut_aide': ('Mois de la date de départ du Soleil.', 'Month of the Sun’s starting date.'),
    'anim_seasonsim_jour_debut': ('jour', 'day'),
    'anim_seasonsim_jour_debut_aide': ('Jour de la date de départ.', 'Day of the starting date.'),
    'anim_seasonsim_mois_fin': ('Fin : mois', 'End: month'),
    'anim_seasonsim_mois_fin_aide': ('Mois de la date d’arrivée.', 'Month of the ending date.'),
    'anim_seasonsim_jour_fin': ('jour', 'day'),
    'anim_seasonsim_jour_fin_aide': ('Jour de la date d’arrivée.', 'Day of the ending date.'),
    'anim_seasonsim_cote': ('Vue', 'View'),
    'anim_seasonsim_cote_aide': ('Depuis l’intérieur de la sphère (le ciel comme on le voit, l’est à gauche) ou depuis '
                                 'l’extérieur.',
                                 'From inside the sphere (the sky as we see it, east on the left) or from outside.'),
    'anim_seasonsim_dedans': ('de l’intérieur', 'from inside'), 'anim_seasonsim_dehors': ('de l’extérieur', 'from outside'),
    'anim_seasonsim_aller_debut': ('Aller au début', 'Go to start'),
    'anim_seasonsim_aller_debut_aide': ('Placer le Soleil à la date de départ.', 'Put the Sun at the starting date.'),
    'anim_seasonsim_lambda': ('Longitude écliptique du Soleil', 'Sun’s ecliptic longitude'),
    'anim_seasonsim_titre_dedans': ('Carte du ciel vue de l’intérieur de la sphère céleste (α croît vers l’est, à '
                                    'gauche)',
                                    'Sky map seen from inside the celestial sphere (α increases eastward, to the left)'),
    'anim_seasonsim_titre_dehors': ('Carte vue de l’extérieur de la sphère céleste', 'Map seen from outside the celestial '
                                                                                      'sphere'),
    'anim_seasonsim_pv': ('équinoxe de mars', 'March equinox'), 'anim_seasonsim_se': ('solstice de juin', 'June solstice'),
    'anim_seasonsim_pa': ('équinoxe de septembre', 'September equinox'),
    'anim_seasonsim_sh': ('solstice de décembre', 'December solstice'),
    # ------------------------------------------------------------ obliquité
    'anim_obliquity_obliquite': ('Obliquité', 'Obliquity'),
    'anim_obliquity_obliquite_aide': ('Angle entre l’axe de rotation et la perpendiculaire au plan de l’orbite.',
                                      'Angle between the rotation axis and the perpendicular to the orbital plane.'),
    'anim_obliquity_terre': ('Terre', 'Earth'), 'anim_obliquity_mars': ('Mars', 'Mars'),
    'anim_obliquity_uranus': ('Uranus', 'Uranus'),
    'anim_obliquity_terre_aide': ('Obliquité de la Terre en 2026 (IAU 2006).', 'Earth’s obliquity in 2026 (IAU 2006).'),
    'anim_obliquity_mars_aide': ('Obliquité de Mars : 25,19°.', 'Obliquity of Mars: 25.19°.'),
    'anim_obliquity_uranus_aide': ('Obliquité d’Uranus : 97,77° (elle roule sur son orbite).',
                                   'Obliquity of Uranus: 97.77° (it rolls along its orbit).'),
    'anim_obliquity_terre_j2000': ('Terre, J2000', 'Earth, J2000'),
    'anim_obliquity_terre_2026': ('Terre, 2026', 'Earth, 2026'),
    'anim_obliquity_plan': ('plan de l’orbite', 'orbital plane'),
    # ------------------------------------------------------------ zodiaque
    'anim_zodiac_signes': ('Signes', 'Signs'),
    'anim_zodiac_signes_aide': ('Secteurs de 30° comptés depuis l’équinoxe de mars (signes astrologiques), décalés des '
                                'constellations par la précession.',
                                'Sectors of 30° counted from the March equinox (astrological signs), shifted from the '
                                'constellations by precession.'),
    'anim_zodiac_derriere': ('Le Soleil est devant', 'The Sun is in front of'),
    'anim_zodiac_minuit': ('Au méridien à minuit', 'On the meridian at midnight'),
    'anim_zodiac_signe': ('Signe (secteur de 30°)', 'Sign (30° sector)'),
    'anim_cst_psc': ('Poissons', 'Pisces'), 'anim_cst_ari': ('Bélier', 'Aries'), 'anim_cst_tau': ('Taureau', 'Taurus'),
    'anim_cst_gem': ('Gémeaux', 'Gemini'), 'anim_cst_cnc': ('Cancer', 'Cancer'), 'anim_cst_leo': ('Lion', 'Leo'),
    'anim_cst_vir': ('Vierge', 'Virgo'), 'anim_cst_lib': ('Balance', 'Libra'), 'anim_cst_sco': ('Scorpion', 'Scorpius'),
    'anim_cst_oph': ('Ophiuchus', 'Ophiuchus'), 'anim_cst_sgr': ('Sagittaire', 'Sagittarius'),
    'anim_cst_cap': ('Capricorne', 'Capricornus'), 'anim_cst_aqr': ('Verseau', 'Aquarius'),
    # ------------------------------------------------------------ temps sidéral et solaire
    'anim_siderealsolartime_annee': ('Année', 'Year'),
    'anim_siderealsolartime_annee_aide': ('Nombre de jours solaires dans l’année : 365 (simple, comme l’original), '
                                          '365,25 (julienne) ou 365,2422 (tropique).',
                                          'Number of solar days in the year: 365 (simple, as in the original), 365.25 '
                                          '(Julian) or 365.2422 (tropical).'),
    'anim_siderealsolartime_simple': ('365 jours', '365 days'),
    'anim_siderealsolartime_julienne': ('365,25 jours', '365.25 days'),
    'anim_siderealsolartime_tropique': ('365,2422 jours', '365.2422 days'),
    'anim_siderealsolartime_minuit': ('Minuit', 'Midnight'), 'anim_siderealsolartime_lever': ('6 h', '6 am'),
    'anim_siderealsolartime_midi': ('Midi', 'Noon'), 'anim_siderealsolartime_coucher': ('18 h', '6 pm'),
    'anim_siderealsolartime_minuit_aide': ('Aller au prochain minuit solaire.', 'Go to the next solar midnight.'),
    'anim_siderealsolartime_lever_aide': ('Aller à la prochaine 6 h solaire (lever à l’équinoxe).',
                                          'Go to the next solar 6 am (sunrise at the equinox).'),
    'anim_siderealsolartime_midi_aide': ('Aller au prochain midi solaire.', 'Go to the next solar noon.'),
    'anim_siderealsolartime_coucher_aide': ('Aller à la prochaine 18 h solaire.', 'Go to the next solar 6 pm.'),
    'anim_siderealsolartime_plus1_sol': ('+1 jour solaire', '+1 solar day'),
    'anim_siderealsolartime_plus1_sol_aide': ('Avancer de 24 h solaires : même position du Soleil.',
                                              'Move on by 24 solar hours: same position of the Sun.'),
    'anim_siderealsolartime_plus10_sol': ('+10 jours solaires', '+10 solar days'),
    'anim_siderealsolartime_plus10_sol_aide': ('Avancer de 10 jours solaires.', 'Move on by 10 solar days.'),
    'anim_siderealsolartime_plus1_sid': ('+1 jour sidéral', '+1 sidereal day'),
    'anim_siderealsolartime_plus1_sid_aide': ('Avancer d’un jour sidéral : mêmes étoiles au méridien, 3 min 56 s plus '
                                              'tôt en temps solaire.',
                                              'Move on by one sidereal day: same stars on the meridian, 3 min 56 s '
                                              'earlier in solar time.'),
    'anim_siderealsolartime_plus10_sid': ('+10 jours sidéraux', '+10 sidereal days'),
    'anim_siderealsolartime_plus10_sid_aide': ('Avancer de 10 jours sidéraux.', 'Move on by 10 sidereal days.'),
    'anim_siderealsolartime_solaire': ('Temps solaire', 'Solar time'),
    'anim_siderealsolartime_sideral': ('Temps sidéral', 'Sidereal time'),
    'anim_siderealsolartime_jours': ('Jours depuis l’équinoxe de mars', 'Days since the March equinox'),
    'anim_siderealsolartime_duree_sid': ('Durée du jour sidéral', 'Length of the sidereal day'),
    'anim_siderealsolartime_ecart': ('Écart avec le jour solaire', 'Difference with the solar day'),
    'anim_siderealsolartime_vue_orbite': ('Orbite vue du nord', 'Orbit seen from the north'),
    'anim_siderealsolartime_horloges': ('Horloges de 24 h', '24-hour clocks'),
    'anim_siderealsolartime_etoile': ('vers une étoile lointaine', 'toward a distant star'),
    # ------------------------------------------------------------ ombres
    'anim_shadowsim_reel': ('Proportions réelles', 'Real proportions'),
    'anim_shadowsim_reel_aide': ('Encart : traversée de l’ombre de la Terre par la Lune avec les vraies dimensions '
                                 '(méthode d’Aristarque).',
                                 'Inset: the Moon crossing the Earth’s shadow with true dimensions (Aristarchus’ '
                                 'method).'),
    'anim_shadowsim_terre': ('Terre', 'Earth'), 'anim_shadowsim_lune': ('Lune', 'Moon'),
    'anim_shadowsim_aide_souris': ('Glisser la Terre ou la Lune pour les déplacer.', 'Drag the Earth or the Moon to move '
                                                                                     'them.'),
    'anim_shadowsim_lunaire': ('Éclipse de Lune', 'Lunar eclipse'),
    'anim_shadowsim_solaire': ('Éclipse de Soleil', 'Solar eclipse'),
    'anim_shadowsim_aucune': ('aucune', 'none'), 'anim_shadowsim_totale': ('totale', 'total'),
    'anim_shadowsim_annulaire': ('annulaire', 'annular'), 'anim_shadowsim_partielle': ('partielle', 'partial'),
    'anim_shadowsim_penombre': ('par la pénombre', 'penumbral'),
    'anim_shadowsim_rayon_ombre': ('Ombre de la Terre à la distance de la Lune (rayon)',
                                   'Earth’s shadow at the Moon’s distance (radius)'),
    'anim_shadowsim_diam_lune': ('le rayon lunaire', 'the lunar radius'),
    'anim_shadowsim_longueur_ombre': ('Longueur du cône d’ombre de la Terre', 'Length of the Earth’s shadow cone'),
    'anim_shadowsim_totalite': ('Totalité (éclipse centrale)', 'Totality (central eclipse)'),
    'anim_shadowsim_phase_ombre': ('Passage dans l’ombre (contacts 1 à 4)', 'Umbral passage (contacts 1 to 4)'),
    'anim_shadowsim_titre_reel': ('Éclipse centrale de Lune, proportions réelles', 'Central lunar eclipse, real '
                                                                                   'proportions'),
    'anim_shadowsim_rapport': ('Ombre ≈ {x} diamètres lunaires', 'Shadow ≈ {x} lunar diameters'),
    'anim_shadowsim_rejouer': ('Rejouer une éclipse', 'Replay an eclipse'),
    'anim_shadowsim_rejouer_aide': ('Rejouer une éclipse de la table 2015–2044 : passage de la Lune dans l’ombre de la '
                                    'Terre, ou de l’ombre de la Lune sur la Terre, en proportions réelles.',
                                    'Replay an eclipse from the 2015–2044 table: the Moon crossing the Earth’s shadow, '
                                    'or the Moon’s shadow crossing the Earth, to true scale.'),
    'anim_shadowsim_libre': ('— aucune (placement libre) —', '— none (free placement) —'),
    'anim_shadowsim_soleil': ('Soleil', 'Sun'), 'anim_shadowsim_lune_t': ('Lune', 'Moon'),
    'anim_shadowsim_instant': ('Instant de l’éclipse', 'Moment of the eclipse'),
    'anim_shadowsim_instant_aide': ('Faire avancer la Lune (ou son ombre) le long de sa trajectoire, du début à la fin '
                                    'de l’éclipse.', 'Move the Moon (or its shadow) along its path, from the start to '
                                    'the end of the eclipse.'),
    'anim_shadowsim_rejouee': ('Éclipse rejouée', 'Replayed eclipse'),
    'anim_shadowsim_ecart': ('Écart à l’axe de l’ombre', 'Distance from the shadow axis'),
    'anim_shadowsim_titre_lune': ('Éclipse de Lune du {date} : la Lune traverse l’ombre de la Terre (proportions '
                                  'réelles, nord en haut)', 'Lunar eclipse of {date}: the Moon crosses the Earth’s '
                                  'shadow (true scale, north up)'),
    'anim_shadowsim_titre_soleil': ('Éclipse de Soleil du {date} : l’ombre de la Lune balaie la Terre (proportions '
                                    'réelles, nord en haut)', 'Solar eclipse of {date}: the Moon’s shadow sweeps the '
                                    'Earth (true scale, north up)'),
    'anim_shadowsim_note': ('Trajectoire approchée (éléments moyens, Meeus).', 'Approximate path (mean elements, '
                            'Meeus).'),
    'anim_shadowsim_duree_tot': ('Totalité : {d}', 'Totality: {d}'),
    # ------------------------------------------------------------ Mars de Ptolémée
    'anim_marsorbit_soleil': ('Soleil', 'Sun'),
    'anim_marsorbit_soleil_aide': ('Montrer le Soleil sur son cercle excentrique.',
                                   'Show the Sun on its eccentric circle.'),
    'anim_marsorbit_cercles': ('Déférent et épicycle', 'Deferent and epicycle'),
    'anim_marsorbit_cercles_aide': ('Montrer le déférent, l’épicycle et le point équant.',
                                    'Show the deferent, the epicycle and the equant point.'),
    'anim_marsorbit_temps': ('Temps', 'Time'),
    'anim_marsorbit_long_mars': ('Longitude de Mars (vue de la Terre)', 'Longitude of Mars (seen from the Earth)'),
    'anim_marsorbit_long_soleil': ('Longitude du Soleil', 'Longitude of the Sun'),
    'anim_marsorbit_elongation': ('Élongation de Mars', 'Elongation of Mars'),
    'anim_marsorbit_sens': ('Mouvement apparent', 'Apparent motion'),
    'anim_marsorbit_direct': ('direct (vers l’est)', 'prograde (eastward)'),
    'anim_marsorbit_retro': ('rétrograde (vers l’ouest)', 'retrograde (westward)'),
    'anim_marsorbit_equant': ('équant', 'equant'), 'anim_marsorbit_mars': ('Mars', 'Mars'),
    # ------------------------------------------------------------ épicycles
    'anim_pathtracer_centre': ('Corps fixe', 'Fixed body'),
    'anim_pathtracer_centre_aide': ('Corps gardé immobile au centre de l’écran : le jaune (héliocentrique), le bleu '
                                    '(géocentrique) ou le rouge.',
                                    'Body kept still at the center of the screen: the yellow one (heliocentric), the '
                                    'blue one (geocentric) or the red one.'),
    'anim_pathtracer_jaune': ('jaune (le « Soleil »)', 'yellow (the « Sun »)'),
    'anim_pathtracer_bleu': ('bleu (la « Terre »)', 'blue (the « Earth »)'),
    'anim_pathtracer_rouge': ('rouge (la « planète »)', 'red (the « planet »)'),
    'anim_pathtracer_temps': ('Temps (périodes du corps bleu)', 'Time (periods of the blue body)'),
    'anim_pathtracer_periode_rouge': ('Période du corps rouge', 'Period of the red body'),
    'anim_pathtracer_vu_depuis': ('Corps immobile : {corps}', 'Body held still: {corps}'),
    # ------------------------------------------------------------ rétrogradation
    'anim_retrograde_inclinaison': ('Inclinaison réelle', 'True inclination'),
    'anim_retrograde_inclinaison_aide': ('Orbite de Mars inclinée de 1,85° sur l’écliptique : la trajectoire apparente '
                                         'forme une boucle (latitude exagérée sur la bande des étoiles).',
                                         'Orbit of Mars inclined by 1.85° to the ecliptic: the apparent path forms a '
                                         'loop (latitude exaggerated on the star strip).'),
    'anim_retrograde_lignes': ('Lignes de visée', 'Lines of sight'),
    'anim_retrograde_lignes_aide': ('Garder les dernières lignes de visée Terre → Mars.',
                                    'Keep the latest Earth → Mars lines of sight.'),
    'anim_retrograde_ciel': ('Mars devant les étoiles lointaines (l’est à gauche)',
                             'Mars against the distant stars (east on the left)'),
    'anim_retrograde_jours': ('Jours depuis l’opposition', 'Days since opposition'),
    'anim_retrograde_lambda': ('Longitude géocentrique de Mars', 'Geocentric longitude of Mars'),
    'anim_retrograde_beta': ('Latitude géocentrique de Mars', 'Geocentric latitude of Mars'),
    'anim_retrograde_vitesse': ('Vitesse apparente', 'Apparent speed'),
    'anim_retrograde_sens': ('Mouvement', 'Motion'),
    'anim_retrograde_theorie': ('Rétrogradation (orbites circulaires)', 'Retrograde loop (circular orbits)'),
    'anim_retrograde_theorie_val': ('{j} jours, {a}', '{j} days, {a}'),
    'anim_retrograde_msg_est': ('La planète avance vers l’est par rapport aux étoiles.',
                                'The planet moves eastward relative to the background stars.'),
    'anim_retrograde_msg_ouest': ('La planète ralentit, s’arrête et repart vers l’ouest : mouvement rétrograde.',
                                  'The planet slows, stops and begins moving westward: retrograde motion.'),
    'anim_retrograde_msg_reprend': ('La planète ralentit, s’arrête et repart vers l’est.',
                                    'The planet now slows, stops and begins moving eastward again.'),
    # ------------------------------------------------------------ Kepler (NAAP)
    'anim_kepler_a': ('Demi-grand axe a', 'Semimajor axis a'),
    'anim_kepler_a_aide': ('Demi-grand axe de l’orbite, de 0,1 à 50 ua (échelle logarithmique).',
                           'Semimajor axis of the orbit, from 0.1 to 50 AU (logarithmic scale).'),
    'anim_kepler_e': ('Excentricité e', 'Eccentricity e'),
    'anim_kepler_e_aide': ('Excentricité de l’ellipse, de 0 (cercle) à 0,7.', 'Eccentricity of the ellipse, from 0 '
                                                                               '(circle) to 0.7.'),
    'anim_kepler_planete': ('Orbite de', 'Orbit of'),
    'anim_kepler_planete_aide': ('Reprendre l’orbite d’une planète du Système solaire.',
                                 'Use the orbit of a planet of the Solar System.'),
    'anim_kepler_aucune': ('(au choix)', '(free)'),
    'anim_kepler_centre': ('Centre', 'Center'), 'anim_kepler_centre_aide': ('Montrer le centre de l’ellipse.',
                                                                           'Show the center of the ellipse.'),
    'anim_kepler_foyer_vide': ('Foyer vide', 'Empty focus'),
    'anim_kepler_foyer_vide_aide': ('Montrer le second foyer, vide (le Soleil occupe l’autre).',
                                    'Show the second, empty focus (the Sun is at the other one).'),
    'anim_kepler_axes': ('Demi-axes', 'Semi-axes'),
    'anim_kepler_axes_aide': ('Montrer le grand axe et le petit axe (a et b).', 'Show the major and minor axes (a and b).'),
    'anim_kepler_rayon': ('Rayon vecteur', 'Radius vector'),
    'anim_kepler_rayon_aide': ('Segment du Soleil à la planète.', 'Segment from the Sun to the planet.'),
    'anim_kepler_vitesse': ('Vitesse', 'Velocity'),
    'anim_kepler_vitesse_aide': ('Vecteur vitesse (longueur proportionnelle à la vitesse, relative au périhélie).',
                                 'Velocity vector (length proportional to the speed, relative to perihelion).'),
    'anim_kepler_systeme': ('Orbites du Système solaire', 'Solar System orbits'),
    'anim_kepler_systeme_aide': ('Tracer les orbites des planètes pour comparer.', 'Draw the planets’ orbits for '
                                                                                   'comparison.'),
    'anim_kepler_balayage': ('Aire balayée', 'Sweep size'),
    'anim_kepler_balayage_aide': ('Durée de chaque balayage, en fraction de la période (2e loi : aires égales en temps '
                                  'égaux).',
                                  'Duration of each sweep, as a fraction of the period (2nd law: equal areas in equal '
                                  'times).'),
    'anim_kepler_balayer': ('Balayer', 'Sweep'),
    'anim_kepler_balayer_aide': ('Colorier les aires balayées pendant l’animation, une sur deux.',
                                 'Color the swept areas while animating, one out of two.'),
    'anim_kepler_effacer': ('Effacer les aires', 'Erase sweeps'),
    'anim_kepler_effacer_aide': ('Effacer les aires coloriées.', 'Erase the colored areas.'),
    'anim_kepler_periode': ('Période (P² = a³)', 'Period (P² = a³)'),
    'anim_kepler_b': ('Demi-petit axe b', 'Semiminor axis b'),
    'anim_kepler_peri_aphe': ('Périhélie / aphélie', 'Perihelion / aphelion'),
    'anim_kepler_r': ('Distance au Soleil', 'Distance to the Sun'),
    'anim_kepler_v': ('Vitesse (vis-viva)', 'Speed (vis-viva)'),
    'anim_kepler_temps': ('Temps depuis le périhélie', 'Time since perihelion'),
    'anim_kepler_aire': ('Dernière aire balayée', 'Last swept area'),
    'anim_planete_mercure': ('Mercure', 'Mercury'), 'anim_planete_venus': ('Vénus', 'Venus'),
    'anim_planete_terre': ('Terre', 'Earth'), 'anim_planete_mars': ('Mars', 'Mars'),
    'anim_planete_jupiter': ('Jupiter', 'Jupiter'), 'anim_planete_saturne': ('Saturne', 'Saturn'),
    'anim_planete_uranus': ('Uranus', 'Uranus'), 'anim_planete_neptune': ('Neptune', 'Neptune'),
    'anim_planete_pluton': ('Pluton', 'Pluto'),
    # ------------------------------------------------------------ parallaxe
    'anim_parallaxdiag_arcsec': ('Parallaxe (″)', 'Parallax (″)'),
    'anim_parallaxdiag_arcsec_aide': ('Parallaxe annuelle en secondes d’arc.', 'Annual parallax in arcseconds.'),
    'anim_parallaxdiag_pc': ('Distance (pc)', 'Distance (pc)'),
    'anim_parallaxdiag_pc_aide': ('Distance en parsecs : d = 1 / p.', 'Distance in parsecs: d = 1 / p.'),
    'anim_parallaxdiag_al': ('Distance (al)', 'Distance (ly)'),
    'anim_parallaxdiag_al_aide': ('Distance en années-lumière (1 pc = 3,2616 al).',
                                  'Distance in light-years (1 pc = 3.2616 ly).'),
    'anim_parallaxdiag_ua': ('Distance (ua)', 'Distance (AU)'),
    'anim_parallaxdiag_formule': ('Relation', 'Relation'),
    'anim_parallaxdiag_proxima': ('Proxima du Centaure', 'Proxima Centauri'),
    'anim_parallaxdiag_proxima_aide': ('Parallaxe de Proxima du Centaure : 768,07 mas (Gaia DR3).',
                                       'Parallax of Proxima Centauri: 768.07 mas (Gaia DR3).'),
    'anim_parallaxdiag_sirius': ('Sirius', 'Sirius'),
    'anim_parallaxdiag_sirius_aide': ('Parallaxe de Sirius : 379,21 mas (nouvelle réduction d’Hipparcos).',
                                      'Parallax of Sirius: 379.21 mas (new Hipparcos reduction).'),
    'anim_parallaxdiag_vega': ('Véga', 'Vega'),
    'anim_parallaxdiag_vega_aide': ('Parallaxe de Véga : 130,23 mas (nouvelle réduction d’Hipparcos).',
                                    'Parallax of Vega: 130.23 mas (new Hipparcos reduction).'),
    'anim_parallaxdiag_une_ua': ('1 ua', '1 AU'),
    'anim_parallaxdiag_schema': ('Schéma (angle très exagéré)', 'Diagram (angle greatly exaggerated)'),
    # ------------------------------------------------------------ module de distance
    'anim_stellarmag_verrou': ('Verrouiller', 'Lock'),
    'anim_stellarmag_verrou_aide': ('Grandeur gardée fixe : les deux autres varient ensemble.',
                                    'Quantity kept fixed: the two others vary together.'),
    'anim_stellarmag_verrou_M': ('M (magnitude absolue)', 'M (absolute magnitude)'),
    'anim_stellarmag_verrou_m': ('m (magnitude apparente)', 'm (apparent magnitude)'),
    'anim_stellarmag_verrou_d': ('d (distance)', 'd (distance)'),
    'anim_stellarmag_m': ('m', 'm'),
    'anim_stellarmag_m_aide': ('Magnitude apparente : éclat vu de la Terre.', 'Apparent magnitude: brightness seen from '
                                                                              'the Earth.'),
    'anim_stellarmag_M': ('M', 'M'),
    'anim_stellarmag_M_aide': ('Magnitude absolue : éclat qu’aurait l’étoile à 10 pc.',
                               'Absolute magnitude: brightness the star would have at 10 pc.'),
    'anim_stellarmag_d': ('d', 'd'),
    'anim_stellarmag_d_aide': ('Distance, de 1 à 1 000 parsecs (échelle logarithmique). On peut aussi glisser '
                               'l’étoile.',
                               'Distance, from 1 to 1,000 parsecs (logarithmic scale). The star can also be dragged.'),
    'anim_stellarmag_equation': ('m − M', 'm − M'),
    'anim_stellarmag_module': ('Module de distance', 'Distance modulus'),
}
TEXTES.update({k: _t(*v) for k, v in _ANIM.items()})

# ==================================================================== lot 1 bis (coordonnées et mouvements)
_ANIM_BIS = {
    # durée du jour
    'anim_daylighthoursexplorer_moyenne': ('Afficher la moyenne annuelle', 'Show the yearly average'),
    'anim_daylighthoursexplorer_moyenne_aide': ('Ligne de la durée moyenne du jour sur l’année.',
                                                'Line of the average day length over the year.'),
    'anim_daylighthoursexplorer_point': ('Point sur la courbe', 'Point on the curve'),
    'anim_daylighthoursexplorer_point_aide': ('Point à faire glisser sur la courbe pour choisir le jour.',
                                              'Point to drag along the curve to choose the day.'),
    'anim_daylighthoursexplorer_refraction': ('Réfraction', 'Refraction'),
    'anim_daylighthoursexplorer_refraction_aide': ('Lever et coucher du bord supérieur du Soleil, réfraction comprise '
                                                   '(h₀ = −0,833°) au lieu de l’horizon géométrique (comme l’original).',
                                                   'Rising and setting of the Sun’s upper limb, refraction included '
                                                   '(h₀ = −0.833°) instead of the geometric horizon (as in the '
                                                   'original).'),
    'anim_daylighthoursexplorer_vue_globe': ('Parallèle de l’observateur', 'Observer’s parallel'),
    'anim_daylighthoursexplorer_vue_courbe': ('Durée du jour au fil de l’année', 'Day length over the year'),
    'anim_daylighthoursexplorer_extremes': ('Plus court / plus long', 'Shortest / longest'),
    # hauteur méridienne
    'anim_meridaltdiagram_objet': ('Astre', 'Object'),
    'anim_meridaltdiagram_objet_aide': ('Astre dessiné à sa hauteur de passage au méridien.',
                                        'Object drawn at its meridian altitude.'),
    'anim_meridaltdiagram_etoile': ('étoile', 'star'), 'anim_meridaltdiagram_soleil': ('Soleil', 'Sun'),
    'anim_meridaltdiagram_lune': ('Lune', 'Moon'), 'anim_meridaltdiagram_planete': ('planète', 'planet'),
    'anim_meridaltdiagram_aucun': ('aucun', 'none'),
    'anim_meridaltdiagram_plage_soleil': ('Plage du Soleil et des planètes', 'Sun and planets range'),
    'anim_meridaltdiagram_plage_soleil_aide': ('Hauteurs possibles du Soleil et des planètes au méridien '
                                               '(δ de −23,44° à +23,44°).',
                                               'Possible meridian altitudes of the Sun and planets (δ from −23.44° '
                                               'to +23.44°).'),
    'anim_meridaltdiagram_plage_lune': ('Plage de la Lune', 'Moon range'),
    'anim_meridaltdiagram_plage_lune_aide': ('Hauteurs possibles de la Lune au méridien (δ jusqu’à ±28,6°).',
                                             'Possible meridian altitudes of the Moon (δ up to ±28.6°).'),
    'anim_meridaltdiagram_hauteur': ('Hauteur au méridien', 'Meridian altitude'),
    'anim_meridaltdiagram_formule': ('Calcul', 'Computation'),
    'anim_meridaltdiagram_eq': ('Hauteur de l’équateur céleste', 'Altitude of the celestial equator'),
    'anim_meridaltdiagram_remarque': ('Remarque', 'Note'),
    'anim_meridaltdiagram_jamais': ('l’astre ne se lève pas à cette latitude', 'the object never rises at this '
                                                                               'latitude'),
    # trajectoires du Soleil, vue d'ensemble
    'anim_sunpaths_reference': ('Solstices et équinoxes', 'Solstices and equinoxes'),
    'anim_sunpaths_reference_aide': ('Trajectoires du Soleil aux solstices (δ = ±23,44°) et aux équinoxes (δ = 0).',
                                     'Paths of the Sun at the solstices (δ = ±23.44°) and equinoxes (δ = 0).'),
    'anim_sunpaths_du_jour': ('Trajectoire du jour', 'Path of the day'),
    'anim_sunpaths_du_jour_aide': ('Trajectoire du Soleil le jour choisi.', 'Path of the Sun on the chosen day.'),
    'anim_sunpaths_solstice_juin': ('solstice de juin', 'June solstice'),
    'anim_sunpaths_equinoxes': ('équinoxes', 'equinoxes'),
    'anim_sunpaths_solstice_dec': ('solstice de décembre', 'December solstice'),
    'anim_sunpaths_duree_solstice_juin': ('Jour au solstice de juin', 'Day at the June solstice'),
    'anim_sunpaths_duree_equinoxes': ('Jour aux équinoxes', 'Day at the equinoxes'),
    'anim_sunpaths_duree_solstice_dec': ('Jour au solstice de décembre', 'Day at the December solstice'),
    'anim_sunmotionsoverview_etape1': ('1. Pôles', '1. Poles'),
    'anim_sunmotionsoverview_etape1_aide': ('Étape 1 : l’axe du monde et les pôles célestes.',
                                            'Step 1: the celestial axis and poles.'),
    'anim_sunmotionsoverview_etape2': ('2. Équateur céleste', '2. Celestial equator'),
    'anim_sunmotionsoverview_etape2_aide': ('Étape 2 : l’équateur céleste, perpendiculaire à l’axe.',
                                            'Step 2: the celestial equator, perpendicular to the axis.'),
    'anim_sunmotionsoverview_etape3': ('3. Trajet des équinoxes', '3. Equinox path'),
    'anim_sunmotionsoverview_etape3_aide': ('Étape 3 : aux équinoxes, le Soleil suit l’équateur céleste.',
                                            'Step 3: at the equinoxes, the Sun follows the celestial equator.'),
    'anim_sunmotionsoverview_etape4': ('4. Trajets des solstices', '4. Solstice paths'),
    'anim_sunmotionsoverview_etape4_aide': ('Étape 4 : aux solstices, parallèles à ±23,44° de l’équateur.',
                                            'Step 4: at the solstices, parallels at ±23.44° from the equator.'),
    # lever sur l'horizon
    'anim_horizon_cote': ('Horizon', 'Horizon'),
    'anim_horizon_cote_aide': ('Regarder vers l’est (lever) ou vers l’ouest (coucher).',
                               'Look toward east (sunrise) or west (sunset).'),
    'anim_horizon_est': ('est (lever)', 'east (sunrise)'), 'anim_horizon_ouest': ('ouest (coucher)', 'west (sunset)'),
    'anim_horizon_trace': ('Repères', 'Marks'),
    'anim_horizon_trace_aide': ('Directions du lever aux solstices et aux équinoxes.',
                                'Sunrise directions at the solstices and equinoxes.'),
    'anim_horizon_azimut': ('Azimut', 'Azimuth'),
    'anim_horizon_amplitude': ('Écart entre les solstices', 'Spread between the solstices'),
    'anim_horizon_ne': ('NE', 'NE'), 'anim_horizon_se': ('SE', 'SE'), 'anim_horizon_sw': ('SO', 'SW'),
    'anim_horizon_nw': ('NO', 'NW'),
    # jour et nuit
    'anim_daylightsimulator_mode': ('Animation', 'Animation'),
    'anim_daylightsimulator_mode_aide': ('Faire avancer l’heure (mouvement quotidien) ou la date à heure fixe '
                                         '(mouvement annuel).',
                                         'Run the time (daily motion) or the date at a fixed time (yearly motion).'),
    'anim_daylightsimulator_jour': ('jour', 'day'), 'anim_daylightsimulator_annee': ('année', 'year'),
    'anim_daylightsimulator_tu': ('Temps universel', 'Universal time'),
    'anim_daylightsimulator_tu_aide': ('Heure à Greenwich (TU).', 'Time at Greenwich (UT).'),
    'anim_daylightsimulator_crepuscule': ('Crépuscules', 'Twilights'),
    'anim_daylightsimulator_crepuscule_aide': ('Bandes des crépuscules civil, nautique et astronomique (Soleil à 6°, '
                                               '12° et 18° sous l’horizon).',
                                               'Bands of civil, nautical and astronomical twilight (Sun 6°, 12° and '
                                               '18° below the horizon).'),
    'anim_daylightsimulator_projection': ('Projection', 'Projection'),
    'anim_daylightsimulator_projection_aide': ('Carte équirectangulaire (latitude et longitude proportionnelles), ou '
                                               'azimutale équidistante centrée sur le pôle Nord ou le pôle Sud, jusqu’à '
                                               'l’équateur (régions polaires, nuit et jour polaires sans déformation), '
                                               'ou globe 3D vu de l’espace, à tourner à la souris.',
                                               'Equirectangular map (latitude and longitude proportional), '
                                               'azimuthal equidistant centred on the North or South Pole, down to the '
                                               'equator (polar regions, polar night and day without distortion), or a '
                                               '3D globe seen from space, rotated with the mouse.'),
    'anim_daylightsimulator_proj_equi': ('équirectangulaire', 'equirectangular'),
    'anim_daylightsimulator_proj_nord': ('pôle Nord', 'North Pole'),
    'anim_daylightsimulator_proj_sud': ('pôle Sud', 'South Pole'),
    'anim_daylightsimulator_proj_globe': ('globe 3D (vue de l’espace)', '3D globe (view from space)'),
    'anim_daylightsimulator_souris': ('Carte : glisser pour placer l’observateur. Globe 3D : glisser pour le faire '
                                      'tourner dans tous les sens (le point saisi suit la souris), molette pour '
                                      'zoomer, double-clic pour revenir au point subsolaire, clic droit pour placer '
                                      'l’observateur.',
                                      'Map: drag to place the observer. 3D globe: drag to rotate it in any direction '
                                      '(the grabbed point follows the mouse), wheel to zoom, double-click to go back to '
                                      'the subsolar point, right click to place the observer.'),
    'anim_daylightsimulator_jour_polaire': ('jour polaire (Soleil à {h} de hauteur)', 'polar day (Sun {h} high)'),
    'anim_daylightsimulator_nuit_polaire': ('nuit polaire (Soleil à {h})', 'polar night (Sun at {h})'),
    'anim_daylightsimulator_pole_horizon': ('le Soleil fait le tour de l’horizon (équinoxe)',
                                            'the Sun runs along the horizon (equinox)'),
    'anim_daylightsimulator_pole_n': ('Au pôle Nord', 'At the North Pole'),
    'anim_daylightsimulator_pole_s': ('Au pôle Sud', 'At the South Pole'),
    'anim_daylightsimulator_bord': ('Vue polaire jusqu’à', 'Polar view down to'),
    'anim_daylightsimulator_bord_aide': ('Bord de la vue polaire : l’équateur, ou 30° au-delà pour voir les deux '
                                         'tropiques.', 'Edge of the polar view: the equator, or 30° beyond to see both '
                                         'tropics.'),
    'anim_daylightsimulator_bord_0': ('l’équateur', 'the equator'),
    'anim_daylightsimulator_bord_30': ('30° au-delà (tropiques)', '30° beyond (tropics)'),
    'anim_daylightsimulator_tournant': ('Terminateur tournant', 'Rotating terminator'),
    'anim_daylightsimulator_tournant_aide': ('Vue polaire et globe : la carte reste fixe (méridien de Greenwich en bas, '
                                             'ou en haut au pôle Sud) et le terminateur tourne ; sinon la Terre tourne '
                                             'sous un terminateur fixe (midi en bas).',
                                             'Polar view and globe: the map stays fixed (Greenwich meridian at the '
                                             'bottom, or at the top for the South Pole) and the terminator turns; '
                                             'otherwise the Earth turns under a fixed terminator (noon at the bottom).'),
    'anim_daylightsimulator_axe': ('Axe des pôles', 'Polar axis'),
    'anim_daylightsimulator_axe_aide': ('Montrer l’axe de rotation de la Terre (partie cachée en pointillé).',
                                        'Show the Earth’s rotation axis (hidden part dotted).'),
    'anim_daylightsimulator_vers_soleil': ('vers le Soleil', 'to the Sun'),
    'anim_daylightsimulator_subsolaire': ('Point subsolaire', 'Subsolar point'),
    'anim_daylightsimulator_h_soleil': ('Hauteur du Soleil pour l’observateur', 'Sun’s altitude for the observer'),
    # antipodes
    'anim_antipodesexplorer_contrainte': ('Déplacement', 'Dragging'),
    'anim_antipodesexplorer_contrainte_aide': ('Déplacer librement, ou seulement le long d’un parallèle ou d’un '
                                               'méridien.',
                                               'Drag freely, or only along a parallel or a meridian.'),
    'anim_antipodesexplorer_libre': ('libre', 'free'), 'anim_antipodesexplorer_parallele': ('le long du parallèle',
                                                                                           'along the parallel'),
    'anim_antipodesexplorer_meridien': ('le long du méridien', 'along the meridian'),
    'anim_antipodesexplorer_aimant': ('Multiples de 5°', 'Snap to 5°'),
    'anim_antipodesexplorer_aimant_aide': ('Arrondir la position aux multiples de 5°.',
                                           'Round the position to multiples of 5°.'),
    'anim_antipodesexplorer_point': ('Point', 'Point'), 'anim_antipodesexplorer_antipode': ('Antipode', 'Antipode'),
    'anim_antipodesexplorer_globe': ('Globe', 'Globe'),
    'anim_antipodesexplorer_carte': ('Carte (glisser le point)', 'Map (drag the point)'),
    # Grande Ourse
    'anim_bigdipper_lignes': ('Lignes de visée', 'Lines of sight'),
    'anim_bigdipper_lignes_aide': ('Lignes de la Terre à chaque étoile, jusqu’à la sphère céleste.',
                                   'Lines from the Earth to each star, up to the celestial sphere.'),
    'anim_bigdipper_noms': ('Noms et distances', 'Names and distances'),
    'anim_bigdipper_noms_aide': ('Nom de chaque étoile et sa distance en années-lumière.',
                                 'Name of each star and its distance in light-years.'),
    'anim_bigdipper_sphere': ('Projection sur le ciel', 'Projection on the sky'),
    'anim_bigdipper_sphere_aide': ('L’astérisme tel qu’on le voit, projeté sur la sphère céleste, avec sa grille '
                                   '(α, δ).',
                                   'The asterism as seen, projected on the celestial sphere, with its (α, δ) grid.'),
    # repères céleste et horizontal
    'anim_celestialhorizon_bascule': ('Repère', 'Frame'),
    'anim_celestialhorizon_bascule_aide': ('0 : repère local (zénith en haut) ; 1 : repère céleste (pôle en haut).',
                                           '0: local frame (zenith up); 1: celestial frame (pole up).'),
    'anim_celestialhorizon_basculer': ('Basculer', 'Switch'),
    'anim_celestialhorizon_basculer_aide': ('Passer d’un repère à l’autre (rotation de 90° − φ autour de l’axe '
                                            'est-ouest).',
                                            'Go from one frame to the other (rotation of 90° − φ about the east-west '
                                            'axis).'),
    'anim_celestialhorizon_rotation': ('Angle de rotation (90° − φ)', 'Rotation angle (90° − φ)'),
    'anim_celestialhorizon_titre_local': ('Repère local : zénith en haut, horizon horizontal',
                                          'Local frame: zenith up, horizon level'),
    'anim_celestialhorizon_titre_celeste': ('Repère céleste : pôle en haut, équateur céleste horizontal',
                                            'Celestial frame: pole up, celestial equator level'),
}
TEXTES.update({k: _t(*v) for k, v in _ANIM_BIS.items()})

from .textes_lot2 import ANIM_LOT2  # noqa: E402  (lot 2 : Lune, Renaissance, astronomie antique…)

TEXTES.update({k: _t(*v) for k, v in ANIM_LOT2.items()})

from .textes_lot3 import ANIM_LOT3  # noqa: E402  (lot 3 : lumière, exoplanètes, étoiles doubles, divers)

TEXTES.update({k: _t(*v) for k, v in ANIM_LOT3.items()})

from .textes_anticythere import ANIM_ANTICYTHERE  # noqa: E402  (la machine d'Anticythère, d'après Anticythere3D)

TEXTES.update({k: _t(*v) for k, v in ANIM_ANTICYTHERE.items()})

from .textes_orion import ANIM_ORION  # noqa: E402  (0.5.0 : spectres physiques, Orion en 3D, fiches au survol)

TEXTES.update({k: _t(*v) for k, v in ANIM_ORION.items()})

for _cle, _fr, _en in (('buenos_aires', 'Buenos Aires', 'Buenos Aires'), ('lima', 'Lima', 'Lima'),
                       ('casablanca', 'Casablanca', 'Casablanca'), ('monrovia', 'Monrovia', 'Monrovia'),
                       ('sao_paulo', 'São Paulo', 'São Paulo'), ('lincoln', 'Lincoln', 'Lincoln'),
                       ('bagdad', 'Bagdad', 'Baghdad'), ('greenwich', 'Greenwich', 'Greenwich'),
                       ('singapour', 'Singapour', 'Singapore'), ('la_havane', 'La Havane', 'Havana'),
                       ('canberra', 'Canberra', 'Canberra'), ('calcutta', 'Calcutta', 'Kolkata'),
                       ('pekin', 'Pékin', 'Beijing'), ('reykjavik', 'Reykjavik', 'Reykjavik'),
                       ('mourmansk', 'Mourmansk', 'Murmansk'), ('washington', 'Washington', 'Washington'),
                       ('barrow', 'Utqiaġvik (Barrow)', 'Utqiaġvik (Barrow)'), ('moscou', 'Moscou', 'Moscow'),
                       ('le_cap', 'Le Cap', 'Cape Town'), ('mcmurdo', 'Base McMurdo', 'McMurdo Station')):
    TEXTES['anim_ville_' + _cle] = _t(_fr, _en)
for _h in (0, 6, 12, 18):
    TEXTES['anim_siderealsolartime_ts%d' % _h] = _t('TS %d h' % _h, 'ST %dh' % _h)
    TEXTES['anim_siderealsolartime_ts%d_aide' % _h] = _t('Aller au prochain instant où le temps sidéral vaut %d h.' % _h,
                                                         'Go to the next time the sidereal time is %dh.' % _h)


# règle typographique : milliers séparés par une espace fine insécable (formateur commun, typographie.normaliser)
from .typographie import normaliser as _normaliser  # noqa: E402

for _v in TEXTES.values():
    for _lg in ('fr', 'en'):
        if isinstance(_v.get(_lg), str):
            _v[_lg] = _normaliser(_v[_lg])

from .textes_classe import TEXTES_CLASSE  # noqa: E402

TEXTES.update({k: _t(*v) for k, v in TEXTES_CLASSE.items()})
