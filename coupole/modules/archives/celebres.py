"""Cibles et programmes célèbres, noms usuels (FR/EN) et guide du Hubble Ultra Deep Field.

Chiffres vérifiés le 12 octobre 2026 :

* programmes, investigateurs, titres et temps de pose : vue ``dbo.obspointing`` du service TAP de MAST
  (``SUM(t_exptime)`` des produits du pipeline standard, groupés par programme, instrument et filtre) ;
* HUDF12 : fichier ``hlsp_hudf12_hst_readme.txt`` (A. Koekemoer, STScI, 15 novembre 2012) ;
* XDF : page https://archive.stsci.edu/prepds/xdf/ (Illingworth et al. 2013, ApJS 209, 6) ;
* tailles des fichiers HLSP : en-tête ``Content-Length`` du serveur https://archive.stsci.edu/hlsps/ .
"""
from __future__ import annotations

from .corps import normaliser

# Noms usuels → identifiant que SIMBAD comprend (ou coordonnées « ra dec » en degrés quand SIMBAD n'a pas d'objet)
ALIAS = {
    'Piliers de la Création': 'M 16', 'Pillars of Creation': 'M 16', "Nébuleuse de l'Aigle": 'M 16',
    'Eagle Nebula': 'M 16', "Nébuleuse d'Orion": 'M 42', 'Orion Nebula': 'M 42', "Grande nébuleuse d'Orion": 'M 42',
    'Nébuleuse de la Carène': 'NGC 3372', 'Carène': 'NGC 3372', 'Carina Nebula': 'NGC 3372', 'Carina': 'NGC 3372',
    'Falaises cosmiques': 'NGC 3324', 'Cosmic Cliffs': 'NGC 3324',
    "Galaxie d'Andromède": 'M 31', 'Andromède': 'M 31', 'Andromeda': 'M 31', 'Andromeda Galaxy': 'M 31',
    'Galaxie du Tourbillon': 'M 51', 'Whirlpool Galaxy': 'M 51', 'Galaxie du Sombrero': 'M 104',
    'Sombrero Galaxy': 'M 104', 'Nébuleuse du Crabe': 'M 1', 'Crab Nebula': 'M 1', 'Nébuleuse de la Lyre': 'M 57',
    'Ring Nebula': 'M 57', 'Nébuleuse annulaire': 'M 57', "Nébuleuse de l'Anneau austral": 'NGC 3132',
    'Southern Ring Nebula': 'NGC 3132', 'Quintette de Stephan': 'HCG 92', "Stephan's Quintet": 'HCG 92',
    'Stephans Quintet': 'HCG 92', 'Nébuleuse de la Tête de Cheval': 'Barnard 33', 'Horsehead Nebula': 'Barnard 33',
    'Tête de Cheval': 'Barnard 33', 'Nébuleuse de la Tarentule': 'NGC 2070', 'Tarantula Nebula': 'NGC 2070',
    'Œil de Chat': 'NGC 6543', "Cat's Eye Nebula": 'NGC 6543', 'Cats Eye Nebula': 'NGC 6543',
    'Hubble Ultra Deep Field': '53.1625 -27.7914', 'Champ ultra-profond de Hubble': '53.1625 -27.7914',
    'HUDF': '53.1625 -27.7914', 'UDF': '53.1625 -27.7914', 'XDF': '53.1625 -27.7914',
    'Hubble Deep Field': '189.2042 62.2294', 'Champ profond de Hubble': '189.2042 62.2294', 'HDF': '189.2042 62.2294',
    'HDF Nord': '189.2042 62.2294', 'HDF North': '189.2042 62.2294',
    'La Rose': 'Arp 273', 'Arp273': 'Arp 273', 'Rose galactique': 'Arp 273',
}
_ALIAS = {normaliser(k): v for k, v in ALIAS.items()}

# Programmes célèbres (vérifiés dans dbo.obspointing) : (clé, nom FR, nom EN, mission, programme(s), recherche, rayon ′)
PROGRAMMES = (
    ('hudf', "Hubble Ultra Deep Field (2003-2004)", 'Hubble Ultra Deep Field (2003-2004)', 'HST', '9978, 10086',
     '53.1625 -27.7914', 2.0),
    ('hudf09', 'HUDF09 : infrarouge WFC3 (2009-2011)', 'HUDF09: WFC3 infrared (2009-2011)', 'HST', '11563',
     '53.1625 -27.7914', 2.0),
    ('hudf12', 'HUDF12 : infrarouge profond (2012)', 'HUDF12: deep infrared (2012)', 'HST', '12498',
     '53.1625 -27.7914', 2.0),
    ('hdf', 'Hubble Deep Field (1995)', 'Hubble Deep Field (1995)', 'HST', '6337', '189.2042 62.2294', 2.0),
    ('piliers95', 'Piliers de la Création (1995, WFPC2)', 'Pillars of Creation (1995, WFPC2)', 'HST', '5773',
     'M 16', 2.0),
    ('piliers14', 'Piliers de la Création (2014, WFC3)', 'Pillars of Creation (2014, WFC3)', 'HST', '13926',
     '274.712 -13.838', 3.0),
    ('piliers22', 'Piliers de la Création (2022, JWST)', 'Pillars of Creation (2022, JWST)', 'JWST', '2739',
     '274.712 -13.838', 3.0),
    ('carene_hst', 'Nébuleuse de la Carène : relevé Hα (2005-2006)', 'Carina Nebula: Hα survey (2005-2006)', 'HST',
     '10475', 'NGC 3372', 20.0),
    ('carene_jwst', 'Falaises cosmiques de la Carène (2022, JWST)', 'Cosmic Cliffs in Carina (2022, JWST)', 'JWST',
     '2731', 'NGC 3324', 4.0),
    ('quintette', 'Quintette de Stephan (2022, JWST)', "Stephan's Quintet (2022, JWST)", 'JWST', '2732', 'HCG 92', 4.0),
    ('anneau_austral', "Nébuleuse de l'Anneau austral (2022, JWST)", 'Southern Ring Nebula (2022, JWST)', 'JWST',
     '2733', 'NGC 3132', 3.0),
    ('arp273', 'Arp 273, « la Rose » (2010, WFC3)', 'Arp 273, "the Rose" (2010, WFC3)', 'HST', '12326', 'Arp 273', 3.0),
)


def alias(nom: str) -> str | None:
    """Identifiant ou coordonnées d'un nom usuel (« Piliers de la Création » → « M 16 »), sinon None."""
    return _ALIAS.get(normaliser(nom))


def noms_usuels() -> list[str]:
    """Noms proposés pendant la frappe (noms usuels français et anglais)."""
    return [k for k in ALIAS if len(k) > 4 and not k.isupper()]


# ================================================================================================ guide HUDF
# Temps de pose (secondes) par filtre, SUM(t_exptime) des produits du pipeline standard dans dbo.obspointing.
HUDF_POSES = {
    # programme 9978 + 10086 (S. Beckwith, « The Ultra Deep Field with ACS »), ACS/WFC, 2003-09 → 2004-01
    'ACS/WFC': {'F435W': 125560 + 9320, 'F606W': 130420 + 4900, 'F775W': 333140 + 13970, 'F850LP': 328280 + 18340},
    # programme 11563 (G. Illingworth), WFC3/IR, 2009-2011
    'WFC3/IR 11563': {'F105W': 119858, 'F125W': 183796, 'F160W': 235410},
    # programme 12498 (R. Ellis, HUDF12), WFC3/IR, 2012 (readme HUDF12 : 198 423 / 82 676 / 71 652 s)
    'WFC3/IR 12498': {'F105W': 198423, 'F140W': 82676, 'F160W': 71652},
}
# XDF (Illingworth et al. 2013) : temps médian dans la zone la plus profonde (ks) et nombre de poses
XDF = {'F435W': (152.4, 164), 'F606W': (174.4, 286), 'F775W': (377.8, 460), 'F814W': (50.8, 362),
       'F850LP': (421.6, 700), 'F105W': (266.7, 248), 'F125W': (112.5, 289), 'F140W': (86.7, 122),
       'F160W': (236.1, 366)}

# Produits de haut niveau (HLSP) déjà empilés, téléchargeables directement (taille mesurée le 12 octobre 2026)
HLSP_HUDF = (
    # (projet, chemin sous /hlsps/, instrument, filtre, taille en octets, nature)
    ('xdf', 'xdf/hlsp_xdf_hst_wfc3ir-60mas_hudf_f160w_v1_sci.fits', 'WFC3/IR', 'F160W', 110255040, 'xdf60'),
    ('xdf', 'xdf/hlsp_xdf_hst_wfc3ir-60mas_hudf_f125w_v1_sci.fits', 'WFC3/IR', 'F125W', 110255040, 'xdf60'),
    ('xdf', 'xdf/hlsp_xdf_hst_wfc3ir-60mas_hudf_f105w_v1_sci.fits', 'WFC3/IR', 'F105W', 110255040, 'xdf60'),
    ('xdf', 'xdf/hlsp_xdf_hst_acswfc-60mas_hudf_f850lp_v1_sci.fits', 'ACS/WFC', 'F850LP', 110255040, 'xdf60'),
    ('xdf', 'xdf/hlsp_xdf_hst_acswfc-60mas_hudf_f775w_v1_sci.fits', 'ACS/WFC', 'F775W', 110255040, 'xdf60'),
    ('xdf', 'xdf/hlsp_xdf_hst_acswfc-60mas_hudf_f606w_v1_sci.fits', 'ACS/WFC', 'F606W', 110255040, 'xdf60'),
    ('xdf', 'xdf/hlsp_xdf_hst_acswfc-60mas_hudf_f435w_v1_sci.fits', 'ACS/WFC', 'F435W', 110255040, 'xdf60'),
    ('hudf09', 'hudf09/hlsp_hudf09_hst_wfc3ir_hudf09-1_f160w_v1_sci.fits', 'WFC3/IR', 'F160W', 40207680, 'hudf09'),
    ('hudf12', 'hudf12/hlsp_hudf12_hst_wfc3ir_udfmain_f160w_v1.0_drz.fits', 'WFC3/IR', 'F160W', 51868800, 'hudf12'),
)
# Préréglage « couleur du HUDF en trois filtres » : le plus léger qui donne une image couleur (3 × 110 Mo)
PRESET_HUDF = ('F435W', 'F775W', 'F160W')
def _lambda(filtre, instrument):
    from .instruments import info_filtre
    f = info_filtre(filtre, instrument)
    return f['lambda'] if f else None


def observations_hlsp(filtres=None) -> list[dict]:
    """Observations « Coupole » des HLSP du HUDF (même pilote de téléchargement que les recherches)."""
    from .services.base import lien, observation
    out = []
    for projet, chemin, instr, filtre, taille, nature in HLSP_HUDF:
        if filtres and filtre not in filtres:
            continue
        if projet != 'xdf' and filtres:
            continue
        expo = XDF.get(filtre, (None, None))
        out.append(observation(
            id='hlsp:' + chemin.rsplit('/', 1)[-1].rsplit('.', 1)[0], archive='mast', mission='HST',
            instrument=instr, filtre=filtre, lambda_nm=_lambda(filtre, instr), debut='', publique='', public=True,
            calib=4, final=True, cible='HUDF', ra=53.1625, dec=-27.7914, url=lien('archives.hlsp', chemin=chemin),
            fichier=chemin.rsplit('/', 1)[-1], taille=taille, page=lien('archives.hlsp.page', projet=projet),
            programme=projet.upper(), titre='Hubble Ultra Deep Field — HLSP %s' % projet.upper(),
            credit='NASA/ESA, STScI; %s team' % projet.upper(), conditions='arc_cond_mast', obs_id=projet,
            exposition=(expo[0] * 1000) if (projet == 'xdf' and expo[0]) else None,
            poses=expo[1] if projet == 'xdf' else None, produit='hlsp', nature='mosaique'))
    return out
