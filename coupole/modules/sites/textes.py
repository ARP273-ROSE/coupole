"""Textes du module « Sites et heures » (FR/EN)."""

TEXTES = {
    'sit_table_aide': {'fr': 'Sites connus (livrés, ou ajoutés par vous). Clic : centre la carte.', 'en': 'Known sites (shipped, or added by you). Click: centre the map.'},
    'sit_carte_aide': {'fr': 'Carte OpenStreetMap : molette pour zoomer, glisser pour déplacer, survol d\'un site : coordonnées.',
                       'en': 'OpenStreetMap map: wheel to zoom, drag to move, hover a site: coordinates.'},
    'sit_col_id': {'fr': 'identifiant', 'en': 'id'},
    'sit_col_nom': {'fr': 'nom', 'en': 'name'},
    'sit_col_lat': {'fr': 'latitude (°)', 'en': 'latitude (°)'},
    'sit_col_lon': {'fr': 'longitude E (°)', 'en': 'longitude E (°)'},
    'sit_col_alt': {'fr': 'altitude (m)', 'en': 'altitude (m)'},
    'sit_col_mpc': {'fr': 'code MPC', 'en': 'MPC code'},
    'sit_col_fuseau': {'fr': 'fuseau', 'en': 'time zone'},
    'sit_col_heure': {'fr': 'heure locale', 'en': 'local time'},
    'sit_col_origine': {'fr': 'origine', 'en': 'origin'},
    'sit_origine_livre': {'fr': 'livré', 'en': 'shipped'},
    'sit_origine_utilisateur': {'fr': 'ajouté', 'en': 'added'},
    'sit_ajouter': {'fr': 'Ajouter un site…', 'en': 'Add a site…'},
    'sit_ajouter_aide': {'fr': 'Coordonnées géodésiques (WGS 84), altitude, fuseau IANA, code MPC s\'il existe.',
                         'en': 'Geodetic coordinates (WGS 84), altitude, IANA time zone, MPC code if any.'},
    'sit_supprimer': {'fr': 'Supprimer', 'en': 'Delete'},
    'sit_supprimer_aide': {'fr': 'Supprime un site que vous avez ajouté (les sites livrés restent).', 'en': 'Delete a site you added (shipped sites remain).'},
    'sit_en_ligne': {'fr': 'Carte en ligne', 'en': 'Online map'},
    'sit_en_ligne_aide': {'fr': 'Décoché : aucune tuile n\'est téléchargée (fond simple).', 'en': 'Unchecked: no tile is downloaded (plain background).'},
    'sit_info': {'fr': '{nom} — {lat}°, {lon}° E, {alt} m — {fuseau} — {heure}', 'en': '{nom} — {lat}°, {lon}° E, {alt} m — {fuseau} — {heure}'},
    'sit_images': {'fr': 'Images de ce site dans la banque OHP : {n}', 'en': 'Images from this site in the OHP bank: {n}'},
    'sit_voir_images': {'fr': 'Voir ces images', 'en': 'Show these images'},
    'sit_voir_images_aide': {'fr': 'Ouvre la Banque OHP.', 'en': 'Open the OHP bank.'},
    'sit_dlg_titre': {'fr': 'Site d\'observation', 'en': 'Observing site'},
    'sit_champ_id_aide': {'fr': 'Identifiant court, sans espace.', 'en': 'Short identifier, no space.'},
    'sit_champ_nom_aide': {'fr': 'Nom complet.', 'en': 'Full name.'},
    'sit_champ_lat_aide': {'fr': 'Latitude géodésique, degrés décimaux, positive au nord.', 'en': 'Geodetic latitude, decimal degrees, positive north.'},
    'sit_champ_lon_aide': {'fr': 'Longitude, degrés décimaux, positive à l\'est.', 'en': 'Longitude, decimal degrees, positive east.'},
    'sit_champ_alt_aide': {'fr': 'Altitude en mètres.', 'en': 'Altitude in metres.'},
    'sit_champ_fuseau_aide': {'fr': 'Fuseau IANA (Europe/Paris, Indian/Antananarivo, Australia/Perth, Asia/Shanghai...).',
                              'en': 'IANA time zone (Europe/Paris, Indian/Antananarivo, Australia/Perth, Asia/Shanghai...).'},
    'sit_champ_mpc_aide': {'fr': 'Code d\'observatoire du Minor Planet Center (facultatif).', 'en': 'Minor Planet Center observatory code (optional).'},
    'sit_fuseau_invalide': {'fr': 'Fuseau inconnu : {fuseau}', 'en': 'Unknown time zone: {fuseau}'},
    'sit_aide_html': {'fr': "<h3>Sites et heures</h3><p>Coupole travaille toujours en UTC et affiche aussi l'heure locale du site "
                            "(et la vôtre si elle diffère). La « date du soir » d'une nuit est la date locale du site à midi "
                            "précédent. Le plein jour se calcule par la hauteur du Soleil au site (jamais signalé pour une "
                            "observation solaire ou radio).</p><p>Sites livrés : OHP (MPC 511), Meudon (005), Paris (007), "
                            "coordonnées tirées des constantes de parallaxe du Minor Planet Center. Les sites partenaires "
                            "s'ajoutent ici quand leurs coordonnées sont connues de source sûre.</p><p>Carte : © OpenStreetMap "
                            "contributors ; tuiles mises en cache, deux téléchargements au plus.</p>",
                      'en': "<h3>Sites and times</h3><p>Coupole always works in UTC and also shows the site's local time (and "
                            "yours when different). The « evening date » of a night is the site's local date at the previous "
                            "noon. Daytime is computed from the Sun's altitude at the site (never flagged for a solar or radio "
                            "observation).</p><p>Shipped sites: OHP (MPC 511), Meudon (005), Paris (007), coordinates from "
                            "the Minor Planet Center parallax constants. Partner sites are added here once their coordinates "
                            "are known from a reliable source.</p><p>Map: © OpenStreetMap contributors; tiles cached, at most "
                            "two downloads at a time.</p>"},
    'sit_cli': {'fr': 'liste les sites, ajoute ou supprime un site, convertit une date', 'en': 'list sites, add or delete a site, convert a date'},
    'sit_aide_ajouter': {'fr': 'ajoute un site : ID NOM LAT LON ALT FUSEAU [MPC]', 'en': 'add a site: ID NAME LAT LON ALT TIMEZONE [MPC]'},
    'sit_aide_supprimer': {'fr': 'supprime un site ajouté', 'en': 'delete an added site'},
    'sit_aide_heure': {'fr': 'affiche une date UTC (ISO) en heure du site et date du soir', 'en': 'show a UTC date (ISO) in site time and evening date'},
    'sit_aide_site': {'fr': 'identifiant du site (défaut : ohp)', 'en': 'site identifier (default: ohp)'},
    'sit_date_du_soir': {'fr': 'date du soir au site : {d}', 'en': 'evening date at the site: {d}'},
    'sit_soleil': {'fr': 'hauteur du Soleil : {h}°', 'en': 'Sun altitude: {h}°'},
}
