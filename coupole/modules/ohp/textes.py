"""Textes du module « Banque OHP » (FR/EN).

Les clés hdr_* vont dans les en-têtes FITS : ASCII seulement, sans apostrophe
dans les commentaires (le traitement de référence écrit « l image »).  Leur
version française est identique à celle d'ohp_xisf.py.
"""
TEXTES = {
    # ------------------------------------------------------------ en-têtes FITS (ASCII)
    'hdr_raison_focale_mesuree': {'fr': 'focale accordee a l echelle mesuree : 206.265 x XPIXSZ / PIXSCALE',
                                  'en': 'focal length matching the measured scale: 206.265 x XPIXSZ / PIXSCALE'},
    'hdr_origine': {'fr': "valeur d'origine : {nom} = {valeur}{raison}", 'en': 'original value: {nom} = {valeur}{raison}'},
    'hdr_converti': {'fr': '{version} : converti de {source}', 'en': '{version}: converted from {source}'},
    'hdr_tan_sans_sip': {'fr': 'TAN projection (pas de coefficients SIP)', 'en': 'TAN projection (no SIP coefficients)'},
    'hdr_tan': {'fr': 'TAN projection', 'en': 'TAN projection'},
    'hdr_raison_sip': {'fr': 'SIP annonce sans A_/B_', 'en': 'SIP announced without A_/B_'},
    'hdr_solution_remplacee': {'fr': 'solution remplacee par ASTAP', 'en': 'solution replaced by ASTAP'},
    'hdr_refaite': {'fr': 'solution astrometrique refaite par ASTAP (catalogue {catalogue}) : {raisons}',
                    'en': 'astrometric solution redone by ASTAP (catalogue {catalogue}): {raisons}'},
    'hdr_confirmee': {'fr': 'solution astrometrique d origine confirmee par ASTAP (ecart {ecart} arcsec)',
                      'en': 'original astrometric solution confirmed by ASTAP (offset {ecart} arcsec)'},
    'hdr_ra': {'fr': '[deg] centre de l image (solution astrometrique)', 'en': '[deg] image centre (astrometric solution)'},
    'hdr_raison_centre': {'fr': 'remplace par le centre reel', 'en': 'replaced by the actual centre'},
    'hdr_objctra': {'fr': 'centre de l image [h m s] (solution astrometrique)',
                    'en': 'image centre [h m s] (astrometric solution)'},
    'hdr_objctdec': {'fr': 'centre de l image [d m s] (solution astrometrique)',
                     'en': 'image centre [d m s] (astrometric solution)'},
    'hdr_pixscale': {'fr': '[arcsec/px] echelle mesuree (solution)', 'en': '[arcsec/px] measured scale (solution)'},
    'hdr_orientat': {'fr': '[deg] angle de position de l axe Y, E depuis N', 'en': '[deg] position angle of Y axis, E of N'},
    'hdr_focale_effective': {'fr': '[mm] focale effective deduite de l echelle mesuree',
                             'en': '[mm] effective focal length from measured scale'},
    'hdr_raison_focale': {'fr': 'incoherente avec l echelle', 'en': 'inconsistent with the scale'},
    'hdr_pixsz_deduit': {'fr': '[um] deduit : echelle mesuree x FOCALLEN', 'en': '[um] derived: measured scale x FOCALLEN'},
    'hdr_focale_deduite': {'fr': '[mm] deduite : XPIXSZ / echelle mesuree', 'en': '[mm] derived: XPIXSZ / measured scale'},
    'hdr_object': {'fr': 'nom normalise (alias de la base fusionnes)', 'en': 'normalised name (database aliases merged)'},
    'hdr_raison_object': {'fr': 'alias normalise', 'en': 'normalised alias'},
    'hdr_filter': {'fr': 'filtre normalise', 'en': 'normalised filter'},
    'hdr_filtsys': {'fr': 'systeme photometrique du filtre', 'en': 'photometric system of the filter'},
    'hdr_filtorig': {'fr': 'valeur d origine de FILTER', 'en': 'original value of FILTER'},
    'hdr_raison_site': {'fr': 'latitude et longitude inversees dans la base',
                        'en': 'latitude and longitude swapped in the database'},
    'hdr_sitelat': {'fr': '[d m s] latitude OHP, MPC 511, WGS 84', 'en': '[d m s] OHP latitude, MPC 511, WGS 84'},
    'hdr_sitelong': {'fr': '[d m s] longitude Est OHP, MPC 511', 'en': '[d m s] OHP east longitude, MPC 511'},
    'hdr_siteelev': {'fr': '[m] hauteur ellipsoidale OHP, MPC 511', 'en': '[m] OHP ellipsoidal height, MPC 511'},
    'hdr_dateobs': {'fr': 'debut de pose UTC (base : t_min + pose/2)', 'en': 'exposure start UTC (database: t_min + exp/2)'},
    'hdr_datedout': {'fr': 'DATE-OBS partagee avec une autre pose de la base',
                     'en': 'DATE-OBS shared with another exposure of the database'},
    'hdr_exptime': {'fr': '[s] duree de pose', 'en': '[s] exposure time'},
    'hdr_xisfconv': {'fr': 'conversion par Coupole', 'en': 'conversion by Coupole'},
    'hdr_u16': {'fr': 'XISF UInt16 + {ped} ADU : {neg} px < -{ped} mis a 0, {haut} px ecretes en haut, fond {fond} ADU',
                'en': 'XISF UInt16 + {ped} ADU: {neg} px < -{ped} set to 0, {haut} px clipped high, background {fond} ADU'},
    'hdr_pedestal': {'fr': '[ADU] piedestal ajoute a chaque pixel (a retirer)', 'en': '[ADU] pedestal added to every pixel (to subtract)'},
    'hdr_ecart': {'fr': '{conv} ; ecart max |FITS - sortie| = {ecart} ADU',
                  'en': '{conv}; max |FITS - output| difference = {ecart} ADU'},

    # ------------------------------------------------------------ LOT.txt
    'lot_lot': {'fr': 'Lot : {v}', 'en': 'Stack: {v}'},
    'lot_objet': {'fr': 'Objet : {objet}   (type : {type})', 'en': 'Object: {objet}   (type: {type})'},
    'lot_noms': {'fr': 'Noms dans la base : {v}', 'en': 'Names in the database: {v}'},
    'lot_instrument': {'fr': 'Instrument : {v}', 'en': 'Instrument: {v}'},
    'lot_filtre': {'fr': 'Filtre : {f} (systeme : {s})', 'en': 'Filter: {f} (system: {s})'},
    'lot_poses': {'fr': 'Poses : {n}   pose totale : {tot} s ({hms})', 'en': 'Exposures: {n}   total exposure: {tot} s ({hms})'},
    'lot_durees': {'fr': 'Durees : {v}', 'en': 'Durations: {v}'},
    'lot_nuits': {'fr': 'Nuits (date du soir) : {v}', 'en': 'Nights (evening date): {v}'},
    'lot_centre': {'fr': 'Centre moyen : RA {ra}  Dec {de}  ({rad}, {ded} deg) ; ecart max au centre : {dmax} arcmin',
                   'en': 'Mean centre: RA {ra}  Dec {de}  ({rad}, {ded} deg); max offset from centre: {dmax} arcmin'},
    'lot_astrometrie': {'fr': 'Pour PixInsight (ImageSolver, WBPP) et N.I.N.A. : focale {f} mm ; pixel effectif {p} um '
                              '(binning {b} compris) ; echelle mesuree {e} arcsec/px',
                        'en': 'For PixInsight (ImageSolver, WBPP) and N.I.N.A.: focal length {f} mm; effective pixel {p} um '
                              '(binning {b} included); measured scale {e} arcsec/px'},
    'lot_astrometrie_binning': {'fr': "Si le logiciel affiche {e2} arcsec/px (le double), il a applique le binning deux fois : "
                                      "saisir le pixel non binne {pnb} um avec le binning {b}, ou le pixel effectif avec le "
                                      "binning 1.",
                                'en': 'If the program shows {e2} arcsec/px (twice as much), it applied the binning twice: enter '
                                      'the unbinned pixel {pnb} um with binning {b}, or the effective pixel with binning 1.'},
    'lot_astrometrie_wbpp': {'fr': "WBPP resout le master avec les metadonnees de l'image si elles survivent a l'integration, "
                                   "sinon avec les valeurs de son panneau Astrometric solution, qui restent celles du dernier "
                                   "instrument : y saisir la focale et le pixel ci-dessus (un fichier de reglages WBPP par "
                                   "instrument evite de les ressaisir).",
                             'en': 'WBPP solves the master with the image metadata if they survive integration, otherwise with '
                                   'the values of its Astrometric solution panel, which stay those of the last instrument: '
                                   'enter the focal length and pixel above there (one WBPP settings file per instrument avoids '
                                   'typing them again).'},
    'lot_angle': {'fr': 'Angle de position moyen (axe Y, E depuis N) : {a} deg ; echelle : {e} arcsec/px',
                  'en': 'Mean position angle (Y axis, E of N): {a} deg; scale: {e} arcsec/px'},
    'lot_solutions': {'fr': 'Solutions astrometriques : {v}', 'en': 'Astrometric solutions: {v}'},
    'lot_dates': {'fr': 'Attention : {n} pose(s) a DATE-OBS partagee avec une autre pose (mot-cle DATEDOUT = T)',
                  'en': 'Warning: {n} exposure(s) with a DATE-OBS shared with another exposure (keyword DATEDOUT = T)'},
    'lot_conseil_sans': {'fr': 'Conseil : pas de solution astrometrique fiable. A resoudre (ImageSolver) avant tout empilement.',
                         'en': 'Advice: no reliable astrometric solution. Solve it (ImageSolver) before any stacking.'},
    'lot_conseil_mobile': {
        'fr': "Conseil : objet mobile. CometAlignment sur le noyau/l'objet (premiere et derniere pose pointees, "
              "interpolation lineaire en temps), puis ImageIntegration ; a part, StarAlignment + ImageIntegration "
              "des memes poses pour le fond d'etoiles. Pas de calibration (deja faite).",
        'en': 'Advice: moving object. CometAlignment on the nucleus/object (first and last exposures marked, '
              'linear interpolation in time), then ImageIntegration; separately, StarAlignment + ImageIntegration '
              'of the same exposures for the star field. No calibration (already done).'},
    'lot_conseil_fixe_8': {'fr': 'Conseil : StarAlignment sur la meilleure pose, puis ImageIntegration (rejet : Winsorized ou ESD). Pas de calibration (deja faite).',
                           'en': 'Advice: StarAlignment on the best exposure, then ImageIntegration (rejection: Winsorized or ESD). No calibration (already done).'},
    'lot_conseil_fixe_3': {'fr': 'Conseil : StarAlignment sur la meilleure pose, puis ImageIntegration (peu de poses : rejet Percentile ou aucun). Pas de calibration (deja faite).',
                           'en': 'Advice: StarAlignment on the best exposure, then ImageIntegration (few exposures: Percentile rejection or none). No calibration (already done).'},
    'lot_conseil_fixe_peu': {'fr': 'Conseil : StarAlignment sur la meilleure pose, puis ImageIntegration — moins de 3 poses : empilement limite. Pas de calibration (deja faite).',
                             'en': 'Advice: StarAlignment on the best exposure, then ImageIntegration — fewer than 3 exposures: limited stacking. No calibration (already done).'},
    'lot_fichiers_xisf': {'fr': "Fichiers : XISF Float32 en ADU (bounds -1000:65535 : PixInsight lit (ADU+1000)/66535, meme echelle pour tous) ou UInt16 (IRIS entiers, 0-65535) ; compression zstd+sh. Rien a regler a l'ouverture.",
                          'en': 'Files: XISF Float32 in ADU (bounds -1000:65535: PixInsight reads (ADU+1000)/66535, same scale for all) or UInt16 (integer IRIS frames, 0-65535); zstd+sh compression. Nothing to set when opening.'},
    'lot_fichiers_fz': {'fr': 'Fichiers : FITS compresses par tuiles (.fits.fz), Float32 en ADU (GZIP_2, sans perte) ou UInt16 (RICE_1, sans perte). Lus par Siril, astropy, DS9.',
                        'en': 'Files: tile-compressed FITS (.fits.fz), Float32 in ADU (GZIP_2, lossless) or UInt16 (RICE_1, lossless). Read by Siril, astropy, DS9.'},
    'lot_fichiers_fits': {'fr': 'Fichiers : FITS Float32 en ADU (ou UInt16), non compresses. Dans PixInsight, regler la plage de lecture FITS sur 0-65535 (Truncate).',
                          'en': 'Files: uncompressed FITS, Float32 in ADU (or UInt16). In PixInsight, set the FITS input range to 0-65535 (Truncate).'},
    'lot_col_fichier': {'fr': 'fichier', 'en': 'file'},
    'lot_col_pose': {'fr': 'pose_s', 'en': 'exp_s'},
    'lot_col_wcs': {'fr': 'wcs', 'en': 'wcs'},
    'lot_col_date': {'fr': 'date_doute', 'en': 'date_doubt'},
    'lot_oui': {'fr': 'oui', 'en': 'yes'},
    'lot_align_aucun': {'fr': 'aucun (a resoudre)', 'en': 'none (solve first)'},

    # ------------------------------------------------------------ colonnes de INDEX_LOTS.csv
    'csv_dossier': {'fr': 'dossier', 'en': 'folder'},
    'csv_type': {'fr': 'type', 'en': 'type'},
    'csv_objet': {'fr': 'objet', 'en': 'object'},
    'csv_lot': {'fr': 'lot', 'en': 'stack'},
    'csv_filtre': {'fr': 'filtre', 'en': 'filter'},
    'csv_poses': {'fr': 'poses', 'en': 'exposures'},
    'csv_pose_totale_s': {'fr': 'pose_totale_s', 'en': 'total_exposure_s'},
    'csv_nuits': {'fr': 'nuits', 'en': 'nights'},
    'csv_centre_ra': {'fr': 'centre_ra', 'en': 'centre_ra'},
    'csv_centre_dec': {'fr': 'centre_dec', 'en': 'centre_dec'},
    'csv_angle_deg': {'fr': 'angle_deg', 'en': 'angle_deg'},
    'csv_alignement': {'fr': 'alignement', 'en': 'alignment'},
}
