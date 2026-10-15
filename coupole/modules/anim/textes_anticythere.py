"""Textes FR/EN de la machine d'Anticythère (adaptée d'Anticythere3D, du même auteur) : (fr, en).  Fusionnés dans
``textes.TEXTES``.  Les explications des sous-ensembles reprennent celles d'Anticythere3D."""

ANIM_ANTICYTHERE = {
    # ------------------------------------------------------------ réglages
    'anim_antikythera_enveloppe': ('Enveloppe', 'Case'),
    'anim_antikythera_enveloppe_aide': ('Machine fermée : coffret de bois et plaques de bronze gravées en grec. '
                                        'Décocher pour voir le train d’engrenages.',
                                        'Closed machine: wooden case and bronze plates engraved in Greek. Untick to '
                                        'see the gear train.'),
    'anim_antikythera_eclatement': ('Éclatement des étages', 'Exploded levels'),
    'anim_antikythera_eclatement_aide': ('Écarte les 16 plans d’engrènement le long des arbres : aucune roue ne bouge '
                                         'dans son plan, celles qui s’engrènent restent face à face.',
                                         'Spreads the 16 meshing planes along the arbors: no gear moves within its '
                                         'plane, meshing gears stay face to face.'),
    'anim_antikythera_face': ('Vue', 'View'),
    'anim_antikythera_face_aide': ('Face avant (calendrier, zodiaque, Lune, Cosmos), face arrière (spirales métonique '
                                   'et du Saros) ou trois-quarts ; glisser fait ensuite tourner la machine.',
                                   'Front face (calendar, zodiac, Moon, Cosmos), back face (Metonic and Saros '
                                   'spirals) or three-quarter view; dragging then turns the machine.'),
    'anim_antikythera_f_avant': ('face avant', 'front face'),
    'anim_antikythera_f_arriere': ('face arrière', 'back face'),
    'anim_antikythera_f_trois_quarts': ('trois-quarts', 'three-quarter'),
    'anim_antikythera_lunaison': ('+1 lunaison', '+1 lunation'),
    'anim_antikythera_lunaison_aide': ('Avance d’un mois synodique (29,53 jours).',
                                       'Advances by one synodic month (29.53 days).'),
    'anim_antikythera_annee': ('+1 an', '+1 year'),
    'anim_antikythera_annee_aide': ('Avance d’une année tropique : un tour de la grande roue b1.',
                                    'Advances by one tropical year: one turn of the great wheel b1.'),
    'anim_antikythera_souris': ('Glisser la poignée de la manivelle (sur le flanc droit de la face avant) fait avancer '
                                'la machine ; glisser ailleurs la fait tourner dans tous les sens. Survoler une roue '
                                '(ou la toucher) donne son nom, ses dents et son rapport. Double-clic : revenir à la '
                                'vue choisie.',
                                'Drag the crank handle (on the right side of the front face) to drive the machine; '
                                'drag anywhere else to turn it in any direction. Hover over a gear (or tap it) for its '
                                'name, teeth and ratio. Double-click: back to the chosen view.'),
    # ------------------------------------------------------------ titres des panneaux
    'anim_antikythera_titre_avant': ('Face avant : calendrier égyptien, zodiaque, Lune et Cosmos',
                                     'Front face: Egyptian calendar, zodiac, Moon and Cosmos'),
    'anim_antikythera_titre_arriere': ('Face arrière : spirales métonique et du Saros',
                                       'Back face: Metonic and Saros spirals'),
    'anim_antikythera_titre_ouverte': ('Le mécanisme : 33 roues colorées par fonction',
                                       'The mechanism: 33 gears coloured by function'),
    'anim_antikythera_legende': ('Sous-ensembles', 'Subsystems'),
    # ------------------------------------------------------------ valeurs
    'anim_antikythera_v_date': ('Date', 'Date'),
    'anim_antikythera_v_egypte': ('Calendrier égyptien', 'Egyptian calendar'),
    'anim_antikythera_v_soleil': ('Soleil (zodiaque)', 'Sun (zodiac)'),
    'anim_antikythera_v_lune': ('Lune (zodiaque)', 'Moon (zodiac)'),
    'anim_antikythera_v_phase': ('Phase de la Lune', 'Moon phase'),
    'anim_antikythera_v_anomalie': ('Correction d’anomalie (tenon-fente)', 'Anomaly correction (pin and slot)'),
    'anim_antikythera_v_noeud': ('Nœud ascendant', 'Ascending node'),
    'anim_antikythera_v_meton': ('Spirale métonique', 'Metonic spiral'),
    'anim_antikythera_v_callippe': ('Cadran callippique', 'Callippic dial'),
    'anim_antikythera_v_jeux': ('Cadran des Jeux', 'Games dial'),
    'anim_antikythera_v_saros': ('Spirale du Saros', 'Saros spiral'),
    'anim_antikythera_v_exeligmos': ('Exeligmos', 'Exeligmos'),
    'anim_antikythera_v_eclipse': ('Éclipse', 'Eclipse'),
    'anim_antikythera_v_planete': ('{nom} (Cosmos)', '{nom} (Cosmos)'),
    'anim_antikythera_v_ecart': ('Écart au ciel réel', 'Error against the real sky'),
    'anim_antikythera_v_manivelle': ('Manivelle', 'Crank'),
    'anim_antikythera_v_roue': ('Roue', 'Gear'),
    'anim_antikythera_greg': ('{d} (grégorien)', '{d} (Gregorian)'),
    'anim_antikythera_jul': ('{d} (julien)', '{d} (Julian)'),
    'anim_antikythera_av_jc': ('{a} av. J.-C.', '{a} BC'),
    'anim_antikythera_epagomene': ('jour épagomène {j}', 'epagomenal day {j}'),
    'anim_antikythera_meton_val': ('case {case} — année {an}', 'cell {case} — year {an}'),
    'anim_antikythera_callippe_val': ('cycle {q} sur 4', 'cycle {q} of 4'),
    'anim_antikythera_saros_val': ('case {case}', 'cell {case}'),
    'anim_antikythera_glyphe': ('{v} — glyphe {g}', '{v} — glyph {g}'),
    'anim_antikythera_exel_val': ('ajouter {h} h', 'add {h} h'),
    'anim_antikythera_eclipse_sol': ('éclipse de Soleil possible', 'solar eclipse possible'),
    'anim_antikythera_eclipse_lune': ('éclipse de Lune possible', 'lunar eclipse possible'),
    'anim_antikythera_eclipse_aucune': ('aucune à cette lunaison', 'none this lunation'),
    'anim_antikythera_eclipse_certaine': ('{t} (certaine)', '{t} (certain)'),
    'anim_antikythera_phase_val': ('{nom} — {pc} % éclairée', '{nom} — {pc} % lit'),
    'anim_antikythera_ecart_val': ('Soleil {s}, Lune {l}', 'Sun {s}, Moon {l}'),
    'anim_antikythera_manivelle_val': ('{t} tours depuis J2000 ({j} jours)', '{t} turns since J2000 ({j} days)'),
    'anim_antikythera_roue_val': ('{nom} : {dents} dents, {rapport} tour par an{sens} — {fonction}',
                                  '{nom}: {dents} teeth, {rapport} turn per year{sens} — {fonction}'),
    'anim_antikythera_sens_inverse': (' (sens inverse)', ' (reversed)'),
    'anim_antikythera_roue_aucune': ('survoler une roue (ou la toucher)', 'hover over a gear (or tap it)'),
    'anim_antikythera_dents': ('{n} dents', '{n} teeth'),
    # ------------------------------------------------------------ noms
    'anim_antikythera_sub_input': ('Entrée et roue motrice', 'Input and main wheel'),
    'anim_antikythera_sub_moon': ('Train de la Lune', 'Moon train'),
    'anim_antikythera_sub_anomaly': ('Anomalie lunaire (tenon et fente)', 'Lunar anomaly (pin and slot)'),
    'anim_antikythera_sub_metonic': ('Cycle métonique', 'Metonic cycle'),
    'anim_antikythera_sub_callippic': ('Cycle callippique', 'Callippic cycle'),
    'anim_antikythera_sub_saros': ('Saros (éclipses)', 'Saros (eclipses)'),
    'anim_antikythera_sub_exeligmos': ('Exeligmos', 'Exeligmos'),
    'anim_antikythera_phase_0': ('Nouvelle Lune', 'New Moon'),
    'anim_antikythera_phase_1': ('Premier croissant', 'Waxing crescent'),
    'anim_antikythera_phase_2': ('Premier quartier', 'First quarter'),
    'anim_antikythera_phase_3': ('Gibbeuse croissante', 'Waxing gibbous'),
    'anim_antikythera_phase_4': ('Pleine Lune', 'Full Moon'),
    'anim_antikythera_phase_5': ('Gibbeuse décroissante', 'Waning gibbous'),
    'anim_antikythera_phase_6': ('Dernier quartier', 'Last quarter'),
    'anim_antikythera_phase_7': ('Dernier croissant', 'Waning crescent'),
    'anim_antikythera_pl_mercury': ('Mercure', 'Mercury'),
    'anim_antikythera_pl_venus': ('Vénus', 'Venus'),
    'anim_antikythera_pl_mars': ('Mars', 'Mars'),
    'anim_antikythera_pl_jupiter': ('Jupiter', 'Jupiter'),
    'anim_antikythera_pl_saturn': ('Saturne', 'Saturn'),
    'anim_antikythera_jeux_isthmia': ('Isthmia', 'Isthmia'),
    'anim_antikythera_jeux_olympia': ('Olympia', 'Olympia'),
    'anim_antikythera_jeux_nemea': ('Nemea', 'Nemea'),
    'anim_antikythera_jeux_pythia': ('Pythia', 'Pythia'),
    'anim_antikythera_epagomenes': ('épagomènes', 'epagomenal'),
    # ------------------------------------------------------------ provenance et lien croisé
    'anim_antikythera_adapte': ('Adaptée d’Anticythere3D, du même auteur', 'Adapted from Anticythere3D, by the same '
                                                                            'author'),
    'anim_antikythera_lien': ('Application complète : Anticythere3D', 'Full application: Anticythere3D'),
}

#: dépôt public de l'application complète (lien croisé de la fiche)
URL_ANTICYTHERE3D = 'https://github.com/ARP273-ROSE/Anticythere3D'
