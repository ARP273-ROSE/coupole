"""Conversion d'UNE image : pixels, solution astrométrique, en-tête corrigé, écriture vérifiée.

Repris pas à pas de ``ohp_xisf.py:traiter()`` (traitement de référence du
7-8 octobre 2026).  Cette fonction est exécutée dans un processus séparé
(multiprocessing) : elle ne touche ni à la base d'état, ni au réseau, ni à
l'interface ; elle reçoit tout ce qu'il lui faut et renvoie un dictionnaire.

Mémoire : une seule image à la fois par processus ; le pic mesuré est de
l'ordre de 10 fois la taille de l'image en float32 (voir PROGRESSION.md).
"""
from __future__ import annotations

import datetime as D
import hashlib
import math
import os
import re
import time
import warnings

import numpy as np

from ...core import astap as astap_mod
from ...core import sites as sites_mod
from ...core import temps as temps_mod
from ...core.astro import ecart_angle, parse_sexa, sep_deg, sexa, utc
from ...core.fitsentete import Entete, fnum, fstr, lire_cartes
from ...core.i18n import tr
from . import formats
from .astrometrie import ACCORD_ASTAP, DESACCORD_ASTAP, cle_classe, cle_groupe, controles, wcs_de
from .cibles import FIXES, MOBILES, nom_affiche

# filtre de la base → (FILTER normalisé, système, nom de dossier sûr sous Windows : R ≠ r_SDSS)
FILTRES = {'Johnson B': ('B', 'Johnson', 'B'), 'Johnson V': ('V', 'Johnson', 'V'), 'Johnson R': ('R', 'Johnson', 'R'),
           'Bcousins': ('B', 'Cousins', 'B'), 'Vcousins': ('V', 'Cousins', 'V'), 'Rcousins': ('R', 'Cousins', 'R'),
           'Ha': ('Ha', 'Narrowband', 'Ha'), 'OIII': ('OIII', 'Narrowband', 'OIII'),
           'SDSS g': ('g', 'SDSS', 'g_SDSS'), 'SDSS r': ('r', 'SDSS', 'r_SDSS'), 'SDSS i': ('i', 'SDSS', 'i_SDSS'),
           'SDSS z': ('z', 'SDSS', 'z_SDSS'), 'iGunn': ('i', 'Gunn', 'i_Gunn')}
RE_WCS_NEUTRALISE = re.compile(r'^(A|B|AP|BP)_(ORDER|\d+_\d+)$|^(CD|PC)\d_\d$|^CDELT\d$|^CROTA\d$|^PV\d_\d+$|'
                               r'^CRVAL\d$|^CRPIX\d$|^CTYPE\d$|^CUNIT\d$|^LONPOLE$|^LATPOLE$|^IMAGEW$|^IMAGEH$')


def sur(s: str) -> str:
    """Nom de fichier/dossier sûr sous Windows : ASCII, ni / \\ : * ? \" < > | ni espace."""
    from ...core.fitsentete import ascii_
    s = ascii_(s).replace('/', '_').replace('(', '').replace(')', '')
    s = re.sub(r'^([CPDXI])_(\d{4})', r'\1\2', s)
    s = re.sub(r'[^A-Za-z0-9.\-]+', '_', s).strip('._')
    return s or 'objet'


def ident(x) -> str:
    return hashlib.sha1(x['access_url'].encode()).hexdigest()[:16]


def info_de_base(x) -> dict:
    return {'source': x['access_url'].rsplit('/', 1)[1], 'url': x['access_url'], 'objet': x['objet'],
            'cat': x['cat'], 'tel': x['tel'], 'nuit': str(x['nuit']), 'filtre_base': x['filter_name'],
            'pose': x['t_exptime'], 'mjd': x['t_min'], 'date_partagee': x['date_partagee'],
            'nom_base': x['target_name']}


def pixels(fic):
    """(données de sortie, référence float64, bitpix, entier16) ; aucune perte au-delà du demi-ULP float32."""
    from astropy.io import fits
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with fits.open(fic, memmap=False, do_not_scale_image_data=True) as hd:
            brut = hd[0].data
            bitpix = hd[0].header['BITPIX']
            bzero = hd[0].header.get('BZERO', 0)
            bscale = hd[0].header.get('BSCALE', 1)
    if brut is None or brut.ndim != 2:
        raise ValueError('not a 2-D image')
    if bitpix == 16 and bzero == 32768 and bscale == 1:
        phys = (brut.astype(np.int32) + 32768).astype('<u2')
        return phys, phys.astype(np.float64), bitpix, True
    if bitpix in (-64, -32):
        phys = brut.astype(np.float64) * bscale + bzero if (bscale != 1 or bzero != 0) else brut
        return phys.astype('<f4'), phys.astype(np.float64), bitpix, False
    phys = brut.astype(np.float64) * bscale + bzero
    return phys.astype('<f4'), phys, bitpix, False


def empreinte(ref) -> str:
    return hashlib.sha1(np.ascontiguousarray(ref).tobytes()).hexdigest()


def corriger_site(ent, site_, info, H):
    """LATITUDE/LONGITUD corrigées seulement si l'inversion est démontrée ; SITELAT/SITELONG/SITEELEV ajoutés
    seulement s'ils manquent (cohérents : gardés ; incohérents : signalés, pas touchés).  Idempotent."""
    la, lo = ent.gets('LATITUDE'), ent.gets('LONGITUD')
    diag = sites_mod.diagnostic_position(la, lo, site_, ent.getf('LAT-OBS'), ent.getf('LONG-OBS'))
    info['position'] = diag
    if diag == 'inversee' and site_ is not None:
        ent.poser('LATITUDE', fstr(sexa(site_.lat, signe=False, dec=0)), 'Latitude of observation site (N)',
                  H('raison_site'))
        ent.poser('LONGITUD', fstr(sexa(site_.lon, signe=False, dec=0)), 'Longitude of observation site (E)',
                  H('raison_site'))
    if site_ is None:
        info['site_mots_cles'] = 'site_inconnu'
        return
    etat = []
    for cle, val, com, ref in (('SITELAT', fstr(sexa(site_.lat, dec=1)), H('sitelat'), site_.lat),
                               ('SITELONG', fstr(sexa(site_.lon, dec=1)), H('sitelong'), site_.lon)):
        v = ent.gets(cle)
        if v is None:
            ent.poser(cle, val, com)
        elif parse_sexa(v) is None or abs(parse_sexa(v) - ref) > sites_mod.TOLERANCE_DEG:
            etat.append(cle + '_incoherent')
    if ent.get('SITEELEV') is None:
        ent.poser('SITEELEV', fnum(site_.alt, '%.0f'), H('siteelev'))
    info['site_mots_cles'] = ' '.join(etat) or 'ok'


def convertir(x: dict, fic: str, sortie: str, med: dict, medo: dict, options: dict) -> dict:
    """Convertit `fic` (FITS téléchargé) vers `sortie`.  Renvoie le dictionnaire d'information.

    options : format ('xisf'|'fz'|'fits'), langue ('fr'|'en' : en-têtes et noms), astap (dict
    EtatASTAP ou None), mode_astap ('tous'|'suspectes'|'jamais'), createur (texte).
    Lève une exception en cas d'échec (le pilote la journalise).
    """
    L = options.get('langue', 'fr')
    fmt = options.get('format', 'xisf')

    def H(cle, **kw):
        return tr('hdr_' + cle, L, **kw)

    t0 = time.time()
    info = info_de_base(x)
    info['octets_fits'] = os.path.getsize(fic)
    cartes = lire_cartes(fic)
    sortie_px, ref, bitpix, entier16 = pixels(fic)
    ny, nx = sortie_px.shape
    info.update(bitpix=bitpix, nx=nx, ny=ny)
    info['sha_pixels'] = empreinte(ref)
    fini = np.isfinite(ref)
    info['non_finis'] = int((~fini).sum())
    info['min'] = float(np.nanmin(ref)) if fini.any() else None
    info['max'] = float(np.nanmax(ref)) if fini.any() else None
    info['negatifs'] = int((ref < 0).sum())
    info['hors_bornes'] = int(((ref < formats.BORNES[0]) | (ref > formats.BORNES[1])).sum())
    conv = formats.description_conversion(fmt, bitpix, entier16)

    # ------------------------------------------------------------ en-tête et solution
    ent = Entete(cartes, H('origine'))
    ent.histoire.append(H('converti', version=options.get('createur', 'Coupole'), source=info['source'][:60]))
    ct1 = ent.gets('CTYPE1') or ''
    if ct1.endswith('-SIP') and ent.get('A_ORDER') is None:
        ent.poser('CTYPE1', fstr(ct1[:-4]), H('tan_sans_sip'), H('raison_sip'))
        ent.poser('CTYPE2', fstr((ent.gets('CTYPE2') or 'DEC--TAN-SIP')[:-4]), H('tan'), H('raison_sip'))
    xpix, foc = ent.getf('XPIXSZ'), ent.getf('FOCALLEN')
    ech_nom = 206.264806 * xpix / foc if xpix and foc else None
    sol = wcs_de(ent, nx, ny)
    pb = ['pas de solution WCS'] if sol is None else controles(x, sol, nx, ech_nom, med, medo)
    if sol is not None:
        info['ecart_base_arcsec'] = round(sep_deg(sol['ra'], sol['dec'], x['s_ra'], x['s_dec']) * 3600, 1)
    info['doutes'] = pb
    etat = options.get('astap')
    etat = astap_mod.EtatASTAP(**etat) if isinstance(etat, dict) else etat
    mode = options.get('mode_astap', 'tous')
    faire_astap = bool(etat and etat.utilisable) and (mode == 'tous' or (mode == 'suspectes' and pb))
    info['astap_disponible'] = bool(etat and etat.utilisable)
    resolu, msg_astap, pb_a = None, '', []
    if faire_astap:
        kk = cle_groupe(x)
        if sol is not None:
            ra0, de0, ech0 = sol['ra'], sol['dec'], sol['echelle']
        else:
            ra0, de0 = medo.get(kk, (x['s_ra'], x['s_dec']))[:2]
            ech0 = (med.get(cle_classe(x), {}).get('echelle') or ech_nom or 0.77)
        if pb and sol is not None:
            if kk in medo:
                ra0, de0 = medo[kk][:2]
            if ech_nom:
                ech0 = ech_nom
        fov = ny * ech0 / 3600
        rayon = 3.0 if not pb else 10.0
        resolu, msg_astap = astap_mod.resoudre(etat, fic, ra0, de0, fov, rayon)
        if resolu is None:                       # champ dense : 50 étoiles les plus brillantes
            resolu, m2 = astap_mod.resoudre(etat, fic, ra0, de0, fov, rayon, ('-s', '50'))
            msg_astap += ' ; -s 50 : ' + m2
        if resolu is None:                       # -fov = hauteur ; à défaut la diagonale
            resolu, m2 = astap_mod.resoudre(etat, fic, ra0, de0, fov * math.sqrt(2), rayon)
            msg_astap += ' ; diagonale : ' + m2
        if resolu is None and pb:                # aveugle, en dernier recours
            resolu, m2 = astap_mod.resoudre(etat, fic, None, None, 0, 180)
            msg_astap += ' ; aveugle : ' + m2
    sol_a = wcs_de(resolu, nx, ny) if resolu is not None else None
    info['astap'] = msg_astap
    if sol_a is not None:
        info['astap_echelle'] = round(sol_a['echelle'], 4)
        pb_a = controles(x, sol_a, nx, ech_nom, med, medo)
        if x['cat'] in MOBILES:                  # un objet mobile peut s'écarter : ASTAP fait foi
            pb_a = [p for p in pb_a if not p.startswith('centre')]
    if sol is not None and sol_a is not None:
        ecart = sep_deg(sol['ra'], sol['dec'], sol_a['ra'], sol_a['dec']) * 3600
        info['ecart_astap_arcsec'] = round(ecart, 2)
        info['ecart_astap_echelle'] = round(sol_a['echelle'] / sol['echelle'] - 1, 5)
        info['ecart_astap_angle'] = round(ecart_angle(sol_a['angle'], sol['angle']), 3)
        if ecart <= ACCORD_ASTAP and abs(sol_a['echelle'] / sol['echelle'] - 1) < 0.01:
            wstat = 'confirmee'
        elif ecart > DESACCORD_ASTAP and pb and not pb_a:
            wstat = 'refaite'
        elif not pb:
            wstat = 'validee'
            info['remarque_astap'] = 'ASTAP en desaccord (%.0f"), solution existante gardee (coherente)' % ecart
        elif not pb_a:
            wstat = 'refaite'
        else:
            wstat = 'echec'
    elif sol is not None:
        wstat = 'validee' if not pb else ('echec' if faire_astap else 'douteuse')
    elif sol_a is not None and not pb_a:
        wstat = 'refaite'
    else:
        wstat = 'echec'
    info['wcs'] = wstat
    if wstat == 'refaite':
        ent.neutraliser(lambda n: RE_WCS_NEUTRALISE.match(n) is not None, H('solution_remplacee'))
        for nom, val, com in resolu.k:
            if re.match(r'^(CTYPE|CUNIT|CRVAL|CRPIX|CD\d_|A_|B_|AP_|BP_)', nom) or nom in ('EQUINOX', 'RADESYS'):
                if nom in ('EQUINOX', 'RADESYS') and ent.get(nom) is not None:
                    continue
                ent.k.append([nom, val, com])
        ent.histoire.append(H('refaite', catalogue=(etat.catalogue or '').upper(), raisons='; '.join(pb)[:200]))
        sol_final = sol_a
    elif wstat in ('confirmee', 'validee'):
        sol_final = sol
    else:
        sol_final = None
    if wstat == 'confirmee':
        ent.histoire.append(H('confirmee', ecart='%.1f' % info['ecart_astap_arcsec']))
    if sol_final:
        info.update(ra=sol_final['ra'], dec=sol_final['dec'], echelle=sol_final['echelle'],
                    angle=sol_final['angle'], parite=sol_final['parite'])
        if sol is not None and wstat == 'refaite':
            info['deplacement_centre_arcsec'] = round(sep_deg(sol['ra'], sol['dec'], sol_final['ra'],
                                                              sol_final['dec']) * 3600, 1)
        ent.poser('RA', fnum(sol_final['ra'], '%.6f'), H('ra'), H('raison_centre'))
        ent.poser('DEC', fnum(sol_final['dec'], '%+.6f'), H('ra'), H('raison_centre'))
        ent.poser('OBJCTRA', fstr(sexa(sol_final['ra'], heures=True, signe=False, dec=2)), H('objctra'),
                  H('raison_centre'))
        ent.poser('OBJCTDEC', fstr(sexa(sol_final['dec'], dec=1)), H('objctdec'), H('raison_centre'))
        ent.poser('PIXSCALE', fnum(sol_final['echelle'], '%.5f'), H('pixscale'))
        ent.poser('ORIENTAT', fnum(sol_final['angle'], '%.3f'), H('orientat'))
        if xpix and foc:
            if abs(ech_nom / sol_final['echelle'] - 1) > 0.02:
                ent.poser('FOCALLEN', fnum(206.264806 * xpix / sol_final['echelle'], '%.1f'), H('focale_effective'),
                          H('raison_focale'))
        elif foc and not xpix:
            v = sol_final['echelle'] * foc / 206.264806
            ent.poser('XPIXSZ', fnum(v, '%.3f'), H('pixsz_deduit'))
            ent.poser('YPIXSZ', fnum(v, '%.3f'), H('pixsz_deduit'))
        elif xpix and not foc:
            ent.poser('FOCALLEN', fnum(206.264806 * xpix / sol_final['echelle'], '%.1f'), H('focale_deduite'))
    info['echelle_nominale'] = ech_nom

    # ------------------------------------------------------------ objet, filtre, site, date, pose
    objet_h = nom_affiche(x['objet'], L)
    info['objet_affiche'] = objet_h
    ent.poser('OBJECT', fstr(objet_h), H('object'), H('raison_object'))
    f_norm, f_sys, f_dos = FILTRES.get(x['filter_name'], (x['filter_name'], '', sur(x['filter_name'])))
    f_orig = ent.gets('FILTER')
    ent.poser('FILTER', fstr(f_norm), H('filter'), H('filter'))
    ent.poser('FILTSYS', fstr(f_sys), H('filtsys'))
    if f_orig is not None and f_orig != f_norm:
        ent.poser('FILTORIG', fstr(f_orig), H('filtorig'))
    info['filtre'], info['filtre_dossier'], info['filtre_sys'] = f_norm, f_dos, f_sys
    # ------------------------------------------------------------ site : correction conditionnelle et idempotente
    site_ = sites_mod.site(x.get('site') or '') if x.get('site') else None
    corriger_site(ent, site_, info, H)
    # t_min de la base = DATE-OBS - pose/2 : DATE-OBS (début de pose) fait foi
    d_inv = utc(x['t_min']) + D.timedelta(seconds=x['t_exptime'] / 2)
    d_hdr = ent.gets('DATE-OBS')
    d_deb = d_inv
    if d_hdr is None:
        ent.poser('DATE-OBS', fstr(d_inv.isoformat(timespec='milliseconds')), H('dateobs'))
        info['date'] = 'ajoutee'
    else:
        try:
            d_deb = D.datetime.fromisoformat(d_hdr[:23])
            dt = abs((d_deb - d_inv).total_seconds())
            info['date'] = 'ok' if dt < 1.5 else 'ecart %.0f s avec la base' % dt
        except ValueError:
            info['date'] = 'illisible'
            d_deb = d_inv
    info['debut'] = d_deb.isoformat(timespec='milliseconds')
    if site_ is not None:
        try:
            r_t = temps_mod.lire_temps({k[0]: ent.gets(k[0]) for k in ent.k if k[0] in
                                        ('DATE-OBS', 'MJD-OBS', 'JD', 'TIMESYS', 'TIME-OBS', 'UT')})
            soup = None if x.get('diurne') else temps_mod.soupcon_heure_locale(r_t, site_)
            if soup:
                info['heure_locale_soupconnee'] = soup
        except Exception as e:  # le contrôle du temps ne fait jamais échouer une conversion
            info['temps_erreur'] = str(e)[:100]
    if x['date_partagee']:
        ent.poser('DATEDOUT', 'T', H('datedout'))
    e_hdr = ent.getf('EXPTIME')
    if e_hdr is None:
        e2 = ent.getf('EXPOSURE')
        ent.poser('EXPTIME', fnum(e2 if e2 is not None else x['t_exptime'], '%.3f'), H('exptime'))
        info['pose_ctrl'] = 'ajoutee'
    else:
        info['pose_ctrl'] = 'ok' if abs(e_hdr - x['t_exptime']) < 0.01 else 'ecart base %.3f' % x['t_exptime']

    # ------------------------------------------------------------ précision float32
    ecart = 0.0
    if sortie_px.dtype.kind == 'f':
        # contrôle pixel à pixel par blocs de lignes : la mémoire de pointe ne dépend pas de la taille de l'image
        pas = max(1, (1 << 20) // max(1, nx))
        hors = 0
        for i in range(0, ny, pas):
            r_ = ref[i:i + pas]
            s_ = sortie_px[i:i + pas]
            s64 = s_.astype(np.float64)
            f_ = np.isfinite(r_)
            diff = np.abs(r_[f_] - s64[f_])
            if diff.size:
                ecart = max(ecart, float(diff.max()))
                hors += int((diff > np.spacing(np.abs(s_[f_])).astype(np.float64) / 2 * (1 + 1e-9)).sum())
            if not np.array_equal(np.isnan(r_), np.isnan(s64)):
                raise ValueError('NaN moved')
        if hors:
            raise ValueError('difference > half float32 ULP on %d pixels' % hors)
    info['ecart_max'] = ecart
    ent.poser('XISFCONV', fstr(conv[:68]), H('xisfconv'))
    ent.histoire.append(H('ecart', conv=conv, ecart='%.3g' % ecart))
    info['modifs'] = sorted(set(ent.modifs))
    mots = ent.finaliser()
    debut_txt = d_deb.strftime('%Y-%m-%dT%H:%M:%S.') + '%03dZ' % (d_deb.microsecond // 1000)
    props = [('Observation:Object:Name', 'String', objet_h),
             ('Observation:Title', 'String', 'OHP %s DU ECU %s %s %gs' % (x['tel'], objet_h, f_norm, x['t_exptime'])),
             ('Observation:Time:Start', 'TimePoint', debut_txt),

             ('Instrument:Telescope:Name', 'String', 'OHP T120' if x['tel'] == 'T120' else 'OHP IRIS'),
             ('Instrument:ExposureTime', 'Float32', x['t_exptime']),
             ('Instrument:Filter:Name', 'String', f_norm),
             ('Organization:Name', 'String', 'Observatoire de Paris - DU ECU (OHP student observations)'),
             ('OHP:Source:URL', 'String', x['access_url']),
             ('OHP:Conversion:Description', 'String', conv),
             ('OHP:Conversion:MaxAbsDifference', 'Float64', ecart),
             ('OHP:Astrometry:Status', 'String', wstat)]
    if site_ is not None:
        props[3:3] = [('Observation:Location:Name', 'String',
                       site_.nom + (' (MPC %s)' % site_.mpc if site_.mpc else '')),
                      ('Observation:Location:Latitude', 'Float64', site_.lat),
                      ('Observation:Location:Longitude', 'Float64', site_.lon),
                      ('Observation:Location:Elevation', 'Float64', round(site_.alt, 1))]
    if sol_final:
        props += [('Observation:Center:RA', 'Float64', sol_final['ra']),
                  ('Observation:Center:Dec', 'Float64', sol_final['dec'])]
    if foc:
        props.append(('Instrument:Telescope:FocalLength', 'Float32', (ent.getf('FOCALLEN') or foc) / 1000))
    del ref
    info['octets_sortie'] = formats.ecrire(fmt, sortie, sortie_px, mots, props,
                                           options.get('createur', 'Coupole'))
    info['octets_xisf'] = info['octets_sortie']        # nom de colonne du journal d'origine
    info['ratio'] = round(info['octets_sortie'] / info['octets_fits'], 4)
    info['format'] = fmt
    info['staging'] = sortie
    info['t_conversion'] = round(time.time() - t0, 2)
    return info
