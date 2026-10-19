"""Solution astrométrique d'une image, par ordre de préférence, sans jamais rien payer :

1. la solution déjà présente dans l'en-tête (gardée telle quelle) ;
2. ASTAP installé (libre, local) ;
3. astrometry.net installé (``solve-field`` dans le PATH, libre, local) ;
4. nova.astrometry.net, le service en ligne libre d'astrometry.net — seulement avec la clé d'API de l'utilisateur
   (Préférences) ET son accord pour cet envoi (`en_ligne=True`, demandé par l'interface avant chaque lot).

Indices tirés de l'en-tête quand il y en a (échelle d'après XPIXSZ/FOCALLEN ou une WCS approchée, centre approché) :
ils accélèrent la résolution et ménagent le service en ligne.  Utilisé par les modules Partages du DU (préparation
des FITS téléchargés), Banque OHP (images douteuses quand ASTAP manque) et Archives (si l'astrométrie y est
demandée).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time

CLES_WCS = ('CTYPE1', 'CTYPE2', 'CUNIT1', 'CUNIT2', 'CRPIX1', 'CRPIX2', 'CRVAL1', 'CRVAL2', 'CD1_1', 'CD1_2',
            'CD2_1', 'CD2_2', 'PC1_1', 'PC1_2', 'PC2_1', 'PC2_2', 'CDELT1', 'CDELT2', 'CROTA2', 'LONPOLE', 'LATPOLE',
            'RADESYS', 'EQUINOX', 'A_ORDER', 'B_ORDER', 'AP_ORDER', 'BP_ORDER')
MODES = ('wcs', 'auto', 'astap', 'astrometry.net', 'nova')


def cle_wcs(k: str) -> bool:
    return k in CLES_WCS or bool(re.match(r'^(A|B|AP|BP)_\d+_\d+$', k))


def a_une_wcs(h) -> bool:
    return 'CTYPE1' in h and 'CRVAL1' in h and str(h.get('CTYPE1', '')).startswith('RA')


def indices_de(h, largeur_px: int | None = None):
    """Indices (échelle, centre) tirés d'un en-tête FITS, même approximatif."""
    from .nova import Indices, echelle_de_l_entete
    ind = Indices(echelle_arcsec=echelle_de_l_entete(h))
    for cra, cdec in (('CRVAL1', 'CRVAL2'), ('RA', 'DEC'), ('OBJCTRA', 'OBJCTDEC')):
        try:
            if cra in h and cdec in h:
                ra, dec = h[cra], h[cdec]
                if isinstance(ra, str):
                    from astropy.coordinates import Angle
                    ra, dec = Angle(ra, unit='hourangle').degree, Angle(dec, unit='deg').degree
                ind.ra, ind.dec = float(ra), float(dec)
                break
        except Exception:
            continue
    if ind.ra is not None:
        champ = (ind.echelle_arcsec or 0) * (largeur_px or 0) / 3600.0
        ind.rayon_deg = max(2.0, 1.5 * champ) if champ else 10.0
    return ind


# ============================================================================================== moteurs locaux
def solveur_local() -> str:
    """astrometry.net installé (« solve-field » dans le PATH) ; '' sinon."""
    return shutil.which('solve-field') or ''


def par_astrometry_net(fits_chemin: str, indices=None, delai: float = 300, arret: threading.Event | None = None):
    """astrometry.net local → en-tête astropy de la solution (ou None)."""
    exe = solveur_local()
    if not exe:
        return None
    base = os.path.splitext(fits_chemin)[0]
    cmd = [exe, '--overwrite', '--no-plots', '--no-verify', '--new-fits', 'none', '--corr', 'none', '--match',
           'none', '--rdls', 'none', '--index-xyls', 'none', '--solved', 'none', '--crpix-center', '--tweak-order',
           '3', '--cpulimit', str(int(delai))]
    if indices is not None:
        p = indices.parametres()
        if 'scale_lower' in p:
            cmd += ['--scale-units', 'arcsecperpix', '--scale-low', str(p['scale_lower']), '--scale-high',
                    str(p['scale_upper'])]
        if 'center_ra' in p:
            cmd += ['--ra', str(p['center_ra']), '--dec', str(p['center_dec']), '--radius', str(p['radius'])]
        if 'downsample_factor' in p:
            cmd += ['--downsample', str(p['downsample_factor'])]
    cmd.append(fits_chemin)
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        t0 = time.monotonic()
        while proc.poll() is None:
            if (arret is not None and arret.is_set()) or time.monotonic() - t0 > delai + 30:
                proc.kill()
                return None
            time.sleep(0.2)
    except OSError:
        return None
    if not os.path.exists(base + '.wcs'):
        return None
    from astropy.io import fits
    try:
        return fits.getheader(base + '.wcs')
    finally:
        for ext in ('.wcs', '.axy'):
            try:
                os.remove(base + ext)
            except OSError:
                pass


def par_astap(fits_chemin: str, indices=None, arret=None):
    from . import astap, config
    e = astap.detecter(config.reglages().get('astap_executable', ''), config.reglages().get('astap_catalogue', ''))
    if not e.utilisable:
        return None
    ra = dec = None
    fov = 0.0
    rayon = 180.0
    if indices is not None and indices.ra is not None:
        ra, dec, rayon = indices.ra, indices.dec, indices.rayon_deg or 10.0
    sol, _ = astap.resoudre(e, fits_chemin, ra, dec, fov, rayon, arret=arret)
    if sol is None:
        return None
    return sol.header_astropy()


# ============================================================================================== chaîne
def resoudre(donnees, entete, mode: str = 'auto', en_ligne: bool = False, dossier_tmp: str = '', nom: str = 'image',
             arret=None, progression=None) -> tuple[object, str]:
    """(en-tête astropy de la solution ou None, source : 'entete'|'astap'|'astrometry.net'|'nova'|'').

    `mode` : 'wcs' (garder seulement), 'auto' (ASTAP, puis astrometry.net local, puis nova si `en_ligne`),
    'astap', 'astrometry.net', 'nova'."""
    import tempfile

    import numpy as np
    from astropy.io import fits
    if a_une_wcs(entete):
        return entete, 'entete'
    if mode == 'wcs':
        return None, ''
    a = np.asarray(donnees, np.float32)
    if a.ndim == 3:
        a = a.mean(axis=0) if a.shape[0] <= 4 else a.mean(axis=2)
    indices = indices_de(entete, a.shape[1])
    locaux = {'auto': ('astap', 'astrometry.net'), 'astap': ('astap',), 'astrometry.net': ('astrometry.net',),
              'nova': ()}.get(mode, ())
    if locaux:
        d = dossier_tmp or tempfile.mkdtemp(prefix='coupole-astrometrie-')
        tmp = os.path.join(d, re.sub(r'[^A-Za-z0-9_.-]+', '_', nom)[:60] + '_resolution.fits')
        fits.PrimaryHDU(a).writeto(tmp, overwrite=True)
        try:
            for moteur in locaux:
                if arret is not None and arret.is_set():
                    return None, ''
                if progression is not None:
                    progression({'etape': moteur})
                h = par_astap(tmp, indices, arret) if moteur == 'astap' else par_astrometry_net(tmp, indices,
                                                                                               arret=arret)
                if h is not None and a_une_wcs(h):
                    return h, moteur
        finally:
            for x in (tmp, os.path.splitext(tmp)[0] + '.wcs', os.path.splitext(tmp)[0] + '.axy',
                      os.path.splitext(tmp)[0] + '.ini', os.path.splitext(tmp)[0] + '.log'):
                try:
                    os.remove(x)
                except OSError:
                    pass
            if not dossier_tmp:
                shutil.rmtree(d, ignore_errors=True)
    if mode in ('auto', 'nova') and en_ligne:
        from . import nova
        if not nova.configure():
            return None, ''
        r = nova.resoudre(a, indices, nom + '.fits', arret, progression)
        if r['entete'] is not None and a_une_wcs(r['entete']):
            return r['entete'], 'nova'
    return None, ''


def copier_wcs(source, destination) -> None:
    """Recopie les mots-clés de solution (WCS + SIP) de `source` dans l'en-tête `destination`."""
    for k in source.keys():
        if cle_wcs(k):
            destination[k] = source[k]
    if 'A_ORDER' in destination and not str(destination.get('CTYPE1', '')).endswith('-SIP'):
        destination['CTYPE1'], destination['CTYPE2'] = 'RA---TAN-SIP', 'DEC--TAN-SIP'
