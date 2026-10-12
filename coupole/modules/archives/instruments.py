"""Instruments et filtres des archives, comparés à ceux d'un astrophotographe amateur.

Valeurs relevées dans les documentations officielles (consultées le 12 octobre 2026) :

* WFC3 : Instrument Handbook, tableaux 6.2 (UVIS) et 7.2 (IR), longueur d'onde pivot et largeur —
  https://hst-docs.stsci.edu/wfc3ihb ;
* ACS : Instrument Handbook, tableau 5.1, longueur d'onde centrale et largeur — https://hst-docs.stsci.edu/acsihb ;
* WFPC2 : Instrument Handbook (valeurs arrondies, marquées ≈) — https://www.stsci.edu/hst/instrumentation/legacy/wfpc2 ;
* JWST : JDox, « NIRCam Filters » (pivot, largeur), « MIRI Filters and Dispersers », « NIRISS Imaging »,
  « NIRCam Field of View » — https://jwst-docs.stsci.edu ;
* ESO : pages des instruments FORS2 (filtres), HAWK-I (échelle 0,1064″/px, champ 7,5′), MUSE (465–930 nm,
  1′ × 1′, 0,2″), VIRCAM (Z Y J H Ks, 0,34″/px), OmegaCAM (0,21″/px) — https://www.eso.org/sci/facilities/paranal/instruments/ ;
* Spitzer : IRAC et MIPS Instrument Handbooks (IRSA) ; WISE et 2MASS : Explanatory Supplements (IRSA) ;
  SDSS : https://www.sdss.org/instruments/camera/ ;
* Voyager et Cassini ISS : PDS Ring-Moon Systems Node (documentation des instruments) ; JunoCam : Hansen et al.
  2017, Space Science Reviews 213, 475 (valeurs approchées, marquées ≈) ;
* Keck NIRC2 : https://www2.keck.hawaii.edu/inst/nirc2/ .

Longueurs d'onde en nm.  « Équivalent amateur » : le filtre d'un astrophotographe qui laisse passer la même
lumière (L, R, V, B, Hα, OIII, SII) ou, à défaut, pourquoi il n'y en a pas.
"""
from __future__ import annotations

import re

# instrument : (mission, champ, échelle, domaine, source)
INSTRUMENTS = {
    'ACS/WFC': ('HST', '202″ × 202″', '0,05″/px', '350–1100 nm', 'https://hst-docs.stsci.edu/acsihb'),
    'WFC3/UVIS': ('HST', '162″ × 162″', '0,04″/px', '200–1000 nm', 'https://hst-docs.stsci.edu/wfc3ihb'),
    'WFC3/IR': ('HST', '136″ × 123″', '0,13″/px', '800–1700 nm', 'https://hst-docs.stsci.edu/wfc3ihb'),
    'WFPC2': ('HST', '≈ 150″ × 150″ (en L)', '0,1″/px (WF), 0,046″/px (PC)', '120–1100 nm',
              'https://www.stsci.edu/hst/instrumentation/legacy/wfpc2'),
    'NIRCAM': ('JWST', "2 modules de 2,2′ × 2,2′ (9,7 arcmin²)", '0,031″/px (0,6–2,3 µm), 0,063″/px (2,4–5 µm)',
               '0,6–5 µm', 'https://jwst-docs.stsci.edu/jwst-near-infrared-camera'),
    'MIRI': ('JWST', '74″ × 113″', '0,11″/px', '5–28 µm', 'https://jwst-docs.stsci.edu/jwst-mid-infrared-instrument'),
    'NIRISS': ('JWST', '2,2′ × 2,2′', '0,066″/px', '0,8–5 µm',
               'https://jwst-docs.stsci.edu/jwst-near-infrared-imager-and-slitless-spectrograph'),
    'HAWKI': ('ESO VLT', '7,5′ × 7,5′', '0,1064″/px', '0,85–2,5 µm',
              'https://www.eso.org/sci/facilities/paranal/instruments/hawki.html'),
    'FORS2': ('ESO VLT', '6,8′ × 6,8′', '0,25″/px', '330–1100 nm',
              'https://www.eso.org/sci/facilities/paranal/instruments/fors.html'),
    'MUSE': ('ESO VLT', '1′ × 1′ (cube : une image par longueur d’onde)', '0,2″/px', '465–930 nm',
             'https://www.eso.org/sci/facilities/paranal/instruments/muse.html'),
    'VIRCAM': ('ESO VISTA', '≈ 1,6° (16 détecteurs, 6 « pawprints » par tuile)', '0,34″/px', '0,85–2,4 µm',
               'https://www.eso.org/sci/facilities/paranal/instruments/vircam.html'),
    'OMEGACAM': ('ESO VST', '1° × 1° (32 CCD)', '0,21″/px', '320–1000 nm',
                 'https://www.eso.org/sci/facilities/paranal/instruments/omegacam.html'),
    'IRAC': ('Spitzer', '5,2′ × 5,2′', '1,2″/px (mosaïques SEIP : 0,6″/px)', '3,6–8 µm',
             'https://irsa.ipac.caltech.edu/data/SPITZER/docs/irac/'),
    'MIPS': ('Spitzer', '5,4′ × 5,4′ (24 µm)', '2,5″/px (24 µm)', '24–160 µm',
             'https://irsa.ipac.caltech.edu/data/SPITZER/docs/mips/'),
    'WISE': ('WISE', '47′ × 47′', '2,75″/px (images Atlas : 1,375″/px)', '3,4–22 µm',
             'https://wise2.ipac.caltech.edu/docs/release/allwise/expsup/'),
    '2MASS': ('2MASS', 'images Atlas 8,5′ × 17′', '1″/px (Atlas)', '1,2–2,2 µm',
              'https://irsa.ipac.caltech.edu/data/2MASS/docs/releases/allsky/doc/explsup.html'),
    'SDSS': ('SDSS', '13,5′ × 9,8′ par champ', '0,396″/px', '300–1100 nm', 'https://www.sdss.org/instruments/camera/'),
    'NIRC2': ('Keck', '10″ (étroit) ou 40″ (large)', '0,01″ ou 0,04″/px', '1–5 µm',
              'https://www2.keck.hawaii.edu/inst/nirc2/'),
    'VOYAGER ISS': ('Voyager', '0,42° (NAC), 3,2° (WAC)', '800 × 800 px (vidicon)', '280–640 nm',
                    'https://pds-rings.seti.org/voyager/iss/'),
    'CASSINI ISS': ('Cassini', '0,35° (NAC), 3,5° (WAC)', '1024 × 1024 px, 6 µrad/px (NAC)', '200–1100 nm',
                    'https://pds-rings.seti.org/cassini/iss/'),
    'JUNOCAM': ('Juno', '58° (balayage par rotation)', 'bandes de 1648 × 128 px', '≈ 400–900 nm',
                'https://doi.org/10.1007/s11214-014-0079-x'),
}

# filtre : (instrument, λ (nm), largeur (nm), usage, équivalent amateur imposé ou '', approché)
_F = [
    # WFC3/UVIS (pivot, largeur ; tableau 6.2)
    ('F225W', 'WFC3/UVIS', 237.2, 46.7, 'ultraviolet large', '', False),
    ('F275W', 'WFC3/UVIS', 271.0, 40.5, 'ultraviolet large', '', False),
    ('F336W', 'WFC3/UVIS', 335.5, 51.2, 'U, Strömgren u', '', False),
    ('F343N', 'WFC3/UVIS', 343.5, 24.9, '[Ne V] 3426', '', False),
    ('F390W', 'WFC3/UVIS', 392.4, 89.4, 'Washington C (violet)', '', False),
    ('F395N', 'WFC3/UVIS', 395.5, 8.5, 'Ca II 3933/3968', '', False),
    ('F438W', 'WFC3/UVIS', 432.6, 61.5, 'B (WFPC2)', '', False),
    ('F475W', 'WFC3/UVIS', 477.3, 134.4, "SDSS g'", '', False),
    ('F475X', 'WFC3/UVIS', 494.1, 205.7, 'bleu très large', '', False),
    ('F502N', 'WFC3/UVIS', 501.0, 6.5, '[O III] 5007', 'OIII', False),
    ('F555W', 'WFC3/UVIS', 530.8, 156.5, 'V (WFPC2)', '', False),
    ('F606W', 'WFC3/UVIS', 588.9, 218.9, 'V large', '', False),
    ('F625W', 'WFC3/UVIS', 624.3, 146.5, "SDSS r'", '', False),
    ('F631N', 'WFC3/UVIS', 630.4, 5.8, '[O I] 6300', '', False),
    ('F656N', 'WFC3/UVIS', 656.1, 1.8, 'Hα 6562', 'Hα', False),
    ('F657N', 'WFC3/UVIS', 656.7, 12.1, 'Hα + [N II] large', 'Hα', False),
    ('F658N', 'WFC3/UVIS', 658.4, 2.8, '[N II] 6583', '', False),
    ('F673N', 'WFC3/UVIS', 676.6, 11.8, '[S II] 6717/6731', 'SII', False),
    ('F600LP', 'WFC3/UVIS', 746.8, 234.0, 'passe-haut (> 600 nm)', '', False),
    ('FQ727N', 'WFC3/UVIS', 727.5, 6.4, 'méthane 727 nm (planètes)', '', False),
    ('F814W', 'WFC3/UVIS', 803.9, 156.5, 'I large (WFPC2)', '', False),
    ('FQ889N', 'WFC3/UVIS', 889.2, 9.9, 'méthane 889 nm (planètes)', '', False),
    ('F850LP', 'WFC3/UVIS', 917.6, 119.3, "SDSS z'", '', False),
    # WFC3/IR (pivot, largeur ; tableau 7.2)
    ('F098M', 'WFC3/IR', 986.4, 157.0, 'référence du grisme bleu', '', False),
    ('F105W', 'WFC3/IR', 1055.2, 265.0, 'Y large', '', False),
    ('F110W', 'WFC3/IR', 1153.4, 443.0, 'YJ large', '', False),
    ('F125W', 'WFC3/IR', 1248.6, 284.5, 'J large', '', False),
    ('F126N', 'WFC3/IR', 1258.5, 15.2, '[Fe II]', '', False),
    ('F128N', 'WFC3/IR', 1283.2, 15.9, 'Paschen β', '', False),
    ('F140W', 'WFC3/IR', 1392.3, 384.0, 'JH large', '', False),
    ('F160W', 'WFC3/IR', 1536.9, 268.3, 'H', '', False),
    ('F164N', 'WFC3/IR', 1640.4, 20.9, '[Fe II]', '', False),
    # ACS/WFC (centrale, largeur ; tableau 5.1)
    ('F435W', 'ACS/WFC', 429.7, 103.8, 'B de Johnson', '', False),
    ('F475W', 'ACS/WFC', 476.0, 145.8, "SDSS g", '', False),
    ('F502N', 'ACS/WFC', 502.2, 5.7, '[O III] (1 %)', 'OIII', False),
    ('F550M', 'ACS/WFC', 558.0, 54.7, 'V étroit', '', False),
    ('F555W', 'ACS/WFC', 534.6, 119.3, 'V de Johnson', '', False),
    ('F606W', 'ACS/WFC', 590.7, 234.2, 'V large', '', False),
    ('F625W', 'ACS/WFC', 631.8, 144.2, 'SDSS r', '', False),
    ('F658N', 'ACS/WFC', 658.4, 7.8, 'Hα (1 %), avec [N II]', 'Hα', False),
    ('F660N', 'ACS/WFC', 660.2, 4.0, '[N II] (1 %)', '', False),
    ('F775W', 'ACS/WFC', 776.4, 152.8, 'SDSS i', '', False),
    ('F814W', 'ACS/WFC', 833.3, 251.1, 'I large', '', False),
    ('F850LP', 'ACS/WFC', 944.5, 122.9, 'SDSS z', '', False),
    # WFPC2 (≈)
    ('F439W', 'WFPC2', 431.0, 47.0, 'B', '', True),
    ('F502N', 'WFPC2', 501.0, 3.0, '[O III] 5007', 'OIII', True),
    ('F555W', 'WFPC2', 544.0, 123.0, 'V', '', True),
    ('F606W', 'WFPC2', 600.0, 150.0, 'V large', '', True),
    ('F656N', 'WFPC2', 656.4, 2.2, 'Hα', 'Hα', True),
    ('F673N', 'WFPC2', 673.2, 4.7, '[S II]', 'SII', True),
    ('F814W', 'WFPC2', 800.0, 129.0, 'I', '', True),
    # JWST NIRCam (pivot, largeur ; JDox)
    ('F070W', 'NIRCAM', 705, 128, 'usage général', '', False),
    ('F090W', 'NIRCAM', 902, 194, 'usage général', '', False),
    ('F115W', 'NIRCAM', 1154, 225, 'usage général', '', False),
    ('F150W', 'NIRCAM', 1501, 318, 'usage général', '', False),
    ('F187N', 'NIRCAM', 1874, 24, 'Paschen α', '', False),
    ('F200W', 'NIRCAM', 1988, 461, 'usage général', '', False),
    ('F212N', 'NIRCAM', 2121, 27, 'H₂', '', False),
    ('F277W', 'NIRCAM', 2776, 672, 'usage général', '', False),
    ('F335M', 'NIRCAM', 3362, 348, 'PAH, CH₄', '', False),
    ('F356W', 'NIRCAM', 3565, 786, 'usage général', '', False),
    ('F405N', 'NIRCAM', 4053, 46, 'Brackett α', '', False),
    ('F410M', 'NIRCAM', 4083, 436, 'naines brunes, H₂O, CH₄', '', False),
    ('F444W', 'NIRCAM', 4402, 1024, 'usage général', '', False),
    ('F470N', 'NIRCAM', 4708, 51, 'H₂', '', False),
    # JWST MIRI (pivot, largeur ; JDox)
    ('F560W', 'MIRI', 5635, 1000, 'large bande', '', False),
    ('F770W', 'MIRI', 7639, 1950, 'PAH, large bande', '', False),
    ('F1000W', 'MIRI', 9953, 1800, 'silicates', '', False),
    ('F1130W', 'MIRI', 11309, 730, 'PAH', '', False),
    ('F1280W', 'MIRI', 12810, 2470, 'large bande', '', False),
    ('F1500W', 'MIRI', 15064, 2920, 'large bande', '', False),
    ('F1800W', 'MIRI', 17984, 2950, 'silicates', '', False),
    ('F2100W', 'MIRI', 20795, 4580, 'large bande', '', False),
    ('F2550W', 'MIRI', 25365, 3670, 'large bande', '', False),
    # ESO FORS2 (centrale, largeur à mi-hauteur ; page des filtres FORS)
    ('B_HIGH', 'FORS2', 440, 103.5, 'B', '', False),
    ('G_HIGH', 'FORS2', 470, 160.5, 'g', '', False),
    ('V_HIGH', 'FORS2', 557, 123.5, 'V', '', False),
    ('R_SPECIAL', 'FORS2', 655, 165.0, 'R', '', False),
    ('I_BESS', 'FORS2', 768, 138.0, 'I de Bessel', '', False),
    ('Z_GUNN', 'FORS2', 910, 130.5, 'z de Gunn', '', False),
    ('H_ALPHA', 'FORS2', 656.3, 6.1, 'Hα', 'Hα', False),
    ('OIII', 'FORS2', 500.1, 5.7, '[O III]', 'OIII', False),
    ('SII', 'FORS2', 672.8, 6.6, '[S II]', 'SII', False),
    # ESO VIRCAM (et HAWK-I : mêmes bandes J H Ks) (centrale, largeur ; page VIRCAM)
    ('Z', 'VIRCAM', 880, 120, 'Z', '', False),
    ('Y', 'VIRCAM', 1020, 100, 'Y', '', False),
    ('J', 'VIRCAM', 1250, 180, 'J', '', False),
    ('H', 'VIRCAM', 1650, 300, 'H', '', False),
    ('KS', 'VIRCAM', 2150, 300, 'Ks', '', False),
    # Spitzer, WISE, 2MASS, SDSS
    ('IRAC1', 'IRAC', 3600, 750, '3,6 µm (étoiles, vieilles populations)', '', True),
    ('IRAC2', 'IRAC', 4500, 1015, '4,5 µm', '', True),
    ('IRAC3', 'IRAC', 5800, 1425, '5,8 µm (PAH)', '', True),
    ('IRAC4', 'IRAC', 8000, 2905, '8 µm (PAH, poussière tiède)', '', True),
    ('MIPS24', 'MIPS', 24000, 5300, '24 µm (poussière chaude)', '', True),
    ('W1', 'WISE', 3400, 640, '3,4 µm', '', True),
    ('W2', 'WISE', 4600, 1100, '4,6 µm', '', True),
    ('W3', 'WISE', 12000, 6300, '12 µm', '', True),
    ('W4', 'WISE', 22000, 4700, '22 µm', '', True),
    ('J', '2MASS', 1235, 162, 'J', '', False),
    ('H', '2MASS', 1662, 251, 'H', '', False),
    ('KS', '2MASS', 2159, 262, 'Ks', '', False),
    ('U', 'SDSS', 355.1, 56, 'u', '', False),
    ('G', 'SDSS', 468.6, 138, 'g', '', False),
    ('R', 'SDSS', 616.6, 138, 'r', '', False),
    ('I', 'SDSS', 748.0, 152, 'i', '', False),
    ('Z', 'SDSS', 893.2, 95, 'z', '', False),
    # Voyager ISS, Cassini ISS (≈, PDS Ring-Moon Systems Node), JunoCam (≈)
    ('VIOLET', 'VOYAGER ISS', 416, 60, 'violet', '', True),
    ('BLUE', 'VOYAGER ISS', 479, 60, 'bleu', 'B', True),
    ('GREEN', 'VOYAGER ISS', 566, 50, 'vert', 'V', True),
    ('ORANGE', 'VOYAGER ISS', 591, 50, 'orange', 'R', True),
    ('CLEAR', 'VOYAGER ISS', 497, 300, 'sans filtre', 'L', True),
    ('BL1', 'CASSINI ISS', 451, 100, 'bleu', 'B', True),
    ('GRN', 'CASSINI ISS', 568, 110, 'vert', 'V', True),
    ('RED', 'CASSINI ISS', 650, 150, 'rouge', 'R', True),
    ('HAL', 'CASSINI ISS', 656, 10, 'Hα', 'Hα', True),
    ('MT2', 'CASSINI ISS', 727, 4, 'méthane 727 nm', '', True),
    ('MT3', 'CASSINI ISS', 889, 10, 'méthane 889 nm', '', True),
    ('CL1', 'CASSINI ISS', 611, 440, 'sans filtre', 'L', True),
    ('BLUE', 'JUNOCAM', 480, 100, 'bleu', 'B', True),
    ('GREEN', 'JUNOCAM', 550, 100, 'vert', 'V', True),
    ('RED', 'JUNOCAM', 680, 150, 'rouge', 'R', True),
    ('METHANE', 'JUNOCAM', 889, 20, 'méthane 889 nm', '', True),
]
FILTRES: dict[tuple[str, str], dict] = {}
for _n, _i, _l, _w, _u, _e, _a in _F:
    FILTRES[(_i, _n)] = {'filtre': _n, 'instrument': _i, 'lambda': float(_l), 'largeur': float(_w), 'usage': _u,
                         'equivalent': _e, 'approche': _a}

USAGES_EN = {'ultraviolet large': 'wide ultraviolet', 'bleu très large': 'very wide blue', 'V large': 'wide V',
             'passe-haut (> 600 nm)': 'long pass (> 600 nm)', 'méthane 727 nm (planètes)': 'methane 727 nm (planets)',
             'méthane 889 nm (planètes)': 'methane 889 nm (planets)', 'I large (WFPC2)': 'wide I (WFPC2)',
             'référence du grisme bleu': 'blue grism reference', 'Y large': 'wide Y', 'YJ large': 'wide YJ',
             'J large': 'wide J', 'JH large': 'wide JH', 'B de Johnson': 'Johnson B', 'V étroit': 'narrow V',
             'V de Johnson': 'Johnson V', 'Hα (1 %), avec [N II]': 'Hα (1 %), with [N II]', 'I large': 'wide I',
             'usage général': 'general purpose', 'naines brunes, H₂O, CH₄': 'brown dwarfs, H₂O, CH₄',
             'large bande': 'broad band', 'silicates': 'silicates', 'I de Bessel': 'Bessel I', 'z de Gunn': 'Gunn z',
             '3,6 µm (étoiles, vieilles populations)': '3.6 µm (stars, old populations)', '5,8 µm (PAH)': '5.8 µm (PAH)',
             '8 µm (PAH, poussière tiède)': '8 µm (PAH, warm dust)', '24 µm (poussière chaude)': '24 µm (hot dust)',
             'violet': 'violet', 'bleu': 'blue', 'vert': 'green', 'orange': 'orange', 'rouge': 'red',
             'sans filtre': 'no filter', 'méthane 727 nm': 'methane 727 nm', 'méthane 889 nm': 'methane 889 nm',
             'Washington C (violet)': 'Washington C (violet)', 'Hα + [N II] large': 'wide Hα + [N II]',
             'Ca II 3933/3968': 'Ca II 3933/3968', 'B (WFPC2)': 'B (WFPC2)', 'V (WFPC2)': 'V (WFPC2)'}


def normaliser_instrument(instrument: str) -> str:
    i = (instrument or '').upper().replace('-', '').replace('_', '')
    for cle in ('WFC3/UVIS', 'WFC3/IR', 'ACS/WFC', 'WFPC2', 'NIRCAM', 'MIRI', 'NIRISS', 'HAWKI', 'FORS2', 'MUSE',
                'VIRCAM', 'OMEGACAM', 'IRAC', 'MIPS', 'NIRC2', 'JUNOCAM'):
        if cle.replace('-', '') in i.replace(' ', ''):
            return cle
    if 'VOYAGER' in i or i.startswith('VG'):
        return 'VOYAGER ISS'
    if 'CASSINI' in i or i.startswith('CO'):
        return 'CASSINI ISS'
    if 'WISE' in i:
        return 'WISE'
    if '2MASS' in i:
        return '2MASS'
    if 'SDSS' in i:
        return 'SDSS'
    return i


def info_filtre(filtre: str, instrument: str = '') -> dict | None:
    """Fiche d'un filtre ({'filtre', 'instrument', 'lambda', 'largeur', 'usage', 'equivalent', 'approche'}) ;
    « CLEAR;F444W », « F775W;CLEAR2L » → le filtre utile.  None si inconnu."""
    ins = normaliser_instrument(instrument)
    noms = [n.strip().upper() for n in re.split(r'[;,+ ]', filtre or '') if n.strip()]
    noms = [n for n in noms if not n.startswith('CLEAR') and n not in ('OPAQUE',)] or noms
    for n in noms:
        n2 = n.replace('_HIGH+113', '_HIGH').split('+')[0]
        if (ins, n2) in FILTRES:
            return FILTRES[(ins, n2)]
        if n2.startswith('H_ALPHA') and (ins, 'H_ALPHA') in FILTRES:
            return FILTRES[(ins, 'H_ALPHA')]
    for n in noms:                                # même nom chez un autre instrument de la même mission
        for (i, f), v in FILTRES.items():
            if f == n and (not ins or i.split('/')[0] == ins.split('/')[0]):
                return v
    return None


def equivalent_amateur(lam: float | None, largeur: float | None = None, impose: str = '') -> str:
    """Clé courte de l'équivalent amateur : 'L', 'B', 'V', 'R', 'Hα', 'OIII', 'SII', 'NII', 'UV', 'IR proche',
    'IR' (aucun : invisible pour un capteur amateur)."""
    if impose:
        return impose
    if lam is None:
        return ''
    if largeur and largeur < 15:
        for centre, nom in ((656.3, 'Hα'), (500.7, 'OIII'), (672.4, 'SII'), (658.4, 'NII'), (486.1, 'Hβ')):
            if abs(lam - centre) <= max(largeur, 3):
                return nom
    if lam < 380:
        return 'UV'
    if largeur and largeur > 200 and 450 < lam < 650:
        return 'L'
    if lam < 500:
        return 'B'
    if lam < 590:
        return 'V'
    if lam < 700:
        return 'R'
    if lam < 1050:
        return 'IR proche'
    return 'IR'


EXPLICATIONS = {
    'L': ('Luminance (L) : large bande visible, comme un filtre L.', 'Luminance (L): wide visible band, like an L filter.'),
    'B': ('Bleu (B).', 'Blue (B).'), 'V': ('Vert / visuel (V, G).', 'Green / visual (V, G).'), 'R': ('Rouge (R).', 'Red (R).'),
    'Hα': ('Hα (filtre à bande étroite de 3 à 7 nm).', 'Hα (3–7 nm narrowband filter).'),
    'OIII': ('OIII (bande étroite).', 'OIII (narrowband).'), 'SII': ('SII (bande étroite).', 'SII (narrowband).'),
    'NII': ('[N II] : tout près de Hα, souvent inclus dans un filtre Hα amateur de 7 nm.',
            '[N II]: right next to Hα, often inside a 7 nm amateur Hα filter.'),
    'Hβ': ('Hβ (bande étroite).', 'Hβ (narrowband).'),
    'UV': ("Ultraviolet : arrêté en grande partie par l'atmosphère, aucun équivalent amateur courant.",
           'Ultraviolet: largely blocked by the atmosphere, no common amateur equivalent.'),
    'IR proche': ("Proche infrarouge : comme un filtre « IR-pass » (685 à 850 nm) sur une caméra monochrome ; au-delà "
                  "de 1 µm, un capteur CMOS ne voit plus rien.",
                  'Near infrared: like an IR-pass filter (685–850 nm) on a mono camera; beyond 1 µm a CMOS sensor sees '
                  'nothing.'),
    'IR': ("Infrarouge au-delà de 1 µm : invisible pour une caméra amateur (silicium) ; à colorer en « fausses "
           "couleurs ».", 'Infrared beyond 1 µm: invisible to an amateur (silicon) camera; to be shown in false colour.'),
}


def bulle_filtre(filtre: str, instrument: str = '', langue: str = 'fr') -> str:
    """Info-bulle d'un nom de filtre : longueur d'onde, largeur, usage, équivalent amateur."""
    f = info_filtre(filtre, instrument)
    if f is None:
        return ''
    eq = equivalent_amateur(f['lambda'], f['largeur'], f['equivalent'])
    approx = '≈ ' if f['approche'] else ''
    usage = f['usage'] if langue == 'fr' else USAGES_EN.get(f['usage'], f['usage'])
    lam = f['lambda']
    lam_txt = ('%s%.0f nm' % (approx, lam)) if lam < 2000 else ('%s%.2f µm' % (approx, lam / 1000)).replace('.', ',' if langue == 'fr' else '.')
    if langue == 'fr':
        return '%s (%s) : %s, largeur %s%.0f nm — %s.\nÉquivalent amateur : %s' % (
            f['filtre'], f['instrument'], lam_txt, approx, f['largeur'], usage, EXPLICATIONS.get(eq, ('—',))[0])
    return '%s (%s): %s, width %s%.0f nm — %s.\nAmateur equivalent: %s' % (
        f['filtre'], f['instrument'], lam_txt, approx, f['largeur'], usage, EXPLICATIONS.get(eq, ('', '—'))[1])


def html_topo(langue: str = 'fr') -> str:
    """Onglet « Instruments et filtres » : tableau des instruments puis des filtres, sources citées."""
    import html as H
    e = H.escape
    fr = langue == 'fr'
    t = ['<h3>%s</h3>' % e('Instruments et filtres des archives' if fr else 'Archive instruments and filters'),
         '<p>%s</p>' % e(
             "Un télescope amateur de 200 mm échantillonne typiquement 1 à 2″ par pixel sur un champ d'un degré ; "
             "Hubble voit 0,04 à 0,13″ par pixel sur 2 à 3′ ; JWST de 0,03 à 0,11″.  Les filtres des observatoires "
             "portent un nom codé : F = filtre, nombre = longueur d'onde (nm pour Hubble, centièmes de µm pour "
             "JWST), lettre = largeur (W large, M moyen, N étroit, LP passe-haut, X très large)." if fr else
             'A 200 mm amateur telescope typically samples 1–2″ per pixel over a one-degree field; Hubble sees '
             '0.04–0.13″ per pixel over 2–3′; JWST 0.03–0.11″.  Observatory filter names are coded: F = filter, '
             'number = wavelength (nm for Hubble, hundredths of a µm for JWST), letter = width (W wide, M medium, '
             'N narrow, LP long pass, X extra wide).'),
         '<table border="1" cellspacing="0" cellpadding="3"><tr><th>%s</th></tr>' % '</th><th>'.join(
             e(x) for x in (('Instrument', 'Mission', 'Champ', 'Échelle', 'Domaine', 'Source') if fr else
                            ('Instrument', 'Mission', 'Field', 'Scale', 'Range', 'Source')))]
    for nom, (mission, champ, echelle, domaine, src) in INSTRUMENTS.items():
        t.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><a href="%s">%s</a></td></tr>' % (
            e(nom), e(mission), e(champ if fr else champ.replace(',', '.')), e(echelle if fr else echelle.replace(',', '.')),
            e(domaine if fr else domaine.replace(',', '.')), e(src), e(src.split('/')[2])))
    t.append('</table><h4>%s</h4>' % e('Filtres principaux' if fr else 'Main filters'))
    t.append('<table border="1" cellspacing="0" cellpadding="3"><tr><th>%s</th></tr>' % '</th><th>'.join(
        e(x) for x in (('Filtre', 'Instrument', 'λ (nm)', 'Largeur (nm)', 'Usage', 'Équivalent amateur') if fr else
                       ('Filter', 'Instrument', 'λ (nm)', 'Width (nm)', 'Use', 'Amateur equivalent'))))
    for f in FILTRES.values():
        eq = equivalent_amateur(f['lambda'], f['largeur'], f['equivalent'])
        a = '≈ ' if f['approche'] else ''
        t.append('<tr><td>%s</td><td>%s</td><td>%s%.0f</td><td>%s%.0f</td><td>%s</td><td>%s</td></tr>' % (
            e(f['filtre']), e(f['instrument']), a, f['lambda'], a, f['largeur'],
            e(f['usage'] if fr else USAGES_EN.get(f['usage'], f['usage'])),
            e(eq if fr else {'IR proche': 'near IR'}.get(eq, eq))))
    t.append('</table><p><small>%s</small></p>' % e(
        "Sources : manuels des instruments WFC3 (tableaux 6.2, 7.2 ; longueur d'onde pivot) et ACS (tableau 5.1 ; "
        "longueur d'onde centrale), JDox (NIRCam, MIRI, NIRISS), pages des instruments de l'ESO, manuels Spitzer, "
        "suppléments explicatifs WISE et 2MASS, SDSS, PDS Ring-Moon Systems Node, Hansen et al. 2017 (JunoCam).  "
        "≈ : valeur arrondie ou approchée." if fr else
        'Sources: WFC3 (tables 6.2, 7.2; pivot wavelength) and ACS (table 5.1; central wavelength) instrument '
        'handbooks, JDox (NIRCam, MIRI, NIRISS), ESO instrument pages, Spitzer handbooks, WISE and 2MASS explanatory '
        'supplements, SDSS, PDS Ring-Moon Systems Node, Hansen et al. 2017 (JunoCam).  ≈: rounded or approximate.'))
    return ''.join(t)
