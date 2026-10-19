"""Astrométrie EN LIGNE par le service libre nova.astrometry.net (API officielle), en dernier recours.

Ordre suivi par Coupole (``coupole/core/astrometrie.py``) : solution déjà dans l'en-tête → ASTAP installé →
astrometry.net installé (``solve-field``) → nova.astrometry.net, seulement si l'utilisateur a saisi SA clé d'API
(gratuite, compte nova) dans les Préférences ET accepté l'envoi de ses images (accord demandé avant chaque lot :
c'est un envoi vers un service tiers).

Ce que fait ce client, d'après la documentation de l'API (https://astrometry.net/doc/net/api.html) :

* connexion ``/api/login`` avec la clé (champ ``request-json``), clé de session réutilisée ;
* envoi ``/api/upload`` (multipart/form-data) d'une image ALLÉGÉE : FITS 16 bits en niveaux de gris, réduite par
  regroupement de pixels au-delà de ~4 millions de pixels (la solution est ensuite ramenée à l'image d'origine :
  CRPIX, matrice CD et coefficients SIP) ;
* indices pour aider (et ménager) le service : échelle en ″/px avec bornes basse et haute, position approchée (α, δ,
  rayon) si connue, ``downsample_factor`` pour les images bruitées, ``publicly_visible`` « n » par défaut
  (réglable), aucune licence commerciale ni modification accordée ;
* UNE soumission à la fois (verrou global), sondage espacé (5 s puis de plus en plus espacé jusqu'à 30 s), délai
  maximal, abandon propre (``arret``) ;
* reprise : l'identifiant de soumission est gardé en cache AVANT d'attendre ; une session interrompue reprend le
  sondage au lieu de renvoyer l'image ; erreurs réseau : trois essais espacés ;
* cache par empreinte (SHA-256 de l'image envoyée et des indices) : une image déjà résolue — ou déjà refusée par le
  service — n'est JAMAIS renvoyée ; on peut forcer un nouvel essai.

La clé d'API est un secret : gardée dans ``nova.json`` (dossier de réglages, droits 600), jamais écrite dans un
journal, un rapport d'incident ou le dépôt.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field

from . import config

URL_DEFAUT = 'https://nova.astrometry.net'
PIXELS_MAX = 4_000_000            # au-delà : regroupement de pixels avant l'envoi
SONDAGE_INITIAL = 5.0
SONDAGE_MAX = 30.0
DELAI_MAX = 900.0                 # secondes d'attente au plus pour une soumission
_verrou_soumission = threading.Lock()


class ErreurNova(IOError):
    """`cle` : clé de texte (nova_err_*) ; `detail` : texte technique (anglais), sans la clé d'API."""

    def __init__(self, cle: str, detail: str = ''):
        super().__init__('%s %s' % (cle, detail))
        self.cle, self.detail = cle, detail


class Abandon(Exception):
    pass


# ============================================================================================== réglages (secret)
def _chemin_reglages():
    return config.dossier_config() / 'nova.json'


def reglages() -> dict:
    d = config.lire_json_protege(_chemin_reglages(), {}) or {}
    return {'cle': str(d.get('cle', '') or ''), 'public': bool(d.get('public', False))}


def enregistrer(cle: str | None = None, public: bool | None = None) -> None:
    d = reglages()
    if cle is not None:
        d['cle'] = cle.strip()
    if public is not None:
        d['public'] = bool(public)
    config.ecrire_json_atomique(_chemin_reglages(), d)
    try:
        os.chmod(_chemin_reglages(), 0o600)
    except OSError:
        pass


def configure() -> bool:
    return bool(reglages()['cle'])


def url_service() -> str:
    try:
        from . import sources
        return (sources.valeur('astrometrie.nova') or URL_DEFAUT).rstrip('/')
    except Exception:
        return URL_DEFAUT


# ============================================================================================== indices
@dataclass
class Indices:
    """Ce que l'on sait de l'image (tout est facultatif)."""
    echelle_arcsec: float | None = None      # ″/px estimée (en-tête : XPIXSZ/FOCALLEN, ou WCS approchée)
    marge: float = 0.2                       # bornes : échelle × (1 ± marge)
    ra: float | None = None                  # centre approché (degrés)
    dec: float | None = None
    rayon_deg: float | None = None
    downsample: int | None = None            # facteur de réduction côté serveur (2 ou 4 : images bruitées)
    extra: dict = field(default_factory=dict)

    def parametres(self, facteur: int = 1) -> dict:
        p = {}
        if self.echelle_arcsec:
            e = self.echelle_arcsec * facteur
            p.update(scale_units='arcsecperpix', scale_type='ul', scale_lower=round(e * (1 - self.marge), 4),
                     scale_upper=round(e * (1 + self.marge), 4))
        if self.ra is not None and self.dec is not None:
            p.update(center_ra=round(float(self.ra) % 360.0, 5), center_dec=round(float(self.dec), 5),
                     radius=round(float(self.rayon_deg or 10.0), 3))
        if self.downsample:
            p['downsample_factor'] = int(self.downsample)
        p.update(self.extra)
        return p


def echelle_de_l_entete(h) -> float | None:
    """″/px d'après la taille des pixels et la focale (XPIXSZ µm, FOCALLEN mm), ou la WCS de l'en-tête."""
    try:
        px, f = float(h.get('XPIXSZ') or 0), float(h.get('FOCALLEN') or h.get('FOCAL') or 0)
        if px > 0 and f > 0:
            return 206.265 * px / f * float(h.get('XBINNING') or 1)
    except (TypeError, ValueError):
        pass
    for a, b in (('CD1_1', 'CD2_1'), ('CDELT1', None)):
        try:
            if a in h:
                v = math.hypot(float(h[a]), float(h[b]) if b and b in h else 0.0) * 3600.0
                if v > 0:
                    return v
        except (TypeError, ValueError):
            continue
    return None


# ============================================================================================== image allégée
def preparer_image(donnees, pixels_max: int = PIXELS_MAX) -> tuple[bytes, int]:
    """Image 2-D (ou cube couleur) → (FITS 16 bits gris, facteur de regroupement).  Les étoiles gardent leur place
    relative ; seule la taille diminue (≈ 8 Mo au plus)."""
    import numpy as np
    from astropy.io import fits
    a = np.asarray(donnees, dtype=np.float32)
    if a.ndim == 3:
        a = a.mean(axis=0) if a.shape[0] <= 4 else a.mean(axis=2)
    a = np.nan_to_num(a)
    f = 1
    while (a.shape[0] // f) * (a.shape[1] // f) > pixels_max:
        f += 1
    if f > 1:
        h, w = (a.shape[0] // f) * f, (a.shape[1] // f) * f
        a = a[:h, :w].reshape(h // f, f, w // f, f).mean(axis=(1, 3))
    bas, haut = np.percentile(a, 0.5), np.percentile(a, 99.995)
    a = np.clip((a - bas) / max(haut - bas, 1e-9), 0, 1) * 65535.0
    s = io.BytesIO()
    hdu = fits.PrimaryHDU((a - 32768).astype(np.int16))
    hdu.header['BZERO'] = 32768
    hdu.writeto(s)
    return s.getvalue(), f


def ramener_wcs(entete, facteur: int):
    """Solution d'une image réduite d'un facteur f → solution de l'image d'origine (convention FITS, pixels à
    partir de 1) : CRPIX' = (CRPIX − 0,5) f + 0,5 ; CD' = CD / f ; SIP : A'_pq = A_pq f^(1−p−q), AP'/BP' de même."""
    import re
    if facteur == 1:
        return entete
    h = entete.copy()
    for k in ('CRPIX1', 'CRPIX2'):
        if k in h:
            h[k] = (float(h[k]) - 0.5) * facteur + 0.5
    for k in ('CD1_1', 'CD1_2', 'CD2_1', 'CD2_2', 'CDELT1', 'CDELT2'):
        if k in h:
            h[k] = float(h[k]) / facteur
    for k in list(h.keys()):
        m = re.match(r'^(A|B|AP|BP)_(\d+)_(\d+)$', k)
        if m:
            p, q = int(m.group(2)), int(m.group(3))
            h[k] = float(h[k]) * facteur ** (1 - p - q)
    for k in ('IMAGEW', 'IMAGEH'):
        if k in h:
            h[k] = int(h[k]) * facteur
    return h


# ============================================================================================== cache
def dossier_cache():
    p = config.dossier_cache() / 'nova'
    p.mkdir(parents=True, exist_ok=True)
    return p


def empreinte(octets: bytes, parametres: dict) -> str:
    h = hashlib.sha256(octets)
    h.update(json.dumps(parametres, sort_keys=True).encode())
    return h.hexdigest()


def _etat_cache(cle: str) -> dict:
    return config.lire_json_protege(dossier_cache() / (cle + '.json'), {}) or {}


def _ecrire_cache(cle: str, **champs):
    d = _etat_cache(cle)
    d.update(champs)
    config.ecrire_json_atomique(dossier_cache() / (cle + '.json'), d)


# ============================================================================================== client
class Client:
    def __init__(self, cle_api: str, url: str | None = None, delai_requete: float = 60.0, publique: bool = False,
                 sondage_initial: float = SONDAGE_INITIAL, sondage_max: float = SONDAGE_MAX,
                 delai_max: float = DELAI_MAX):
        if not cle_api:
            raise ErreurNova('nova_err_cle')
        self.cle_api = cle_api
        self.url = (url or url_service()).rstrip('/')
        self.delai = delai_requete
        self.publique = publique
        self.sondage_initial, self.sondage_max, self.delai_max = sondage_initial, sondage_max, delai_max
        self.session = ''
        self.requetes: list[str] = []          # chemins appelés (essais), jamais la clé

    # ------------------------------------------------------------------ bas niveau
    def _ouvrir(self, chemin: str, data: bytes | None = None, en_tetes: dict | None = None, max_octets=20_000_000):
        from .reseau import user_agent
        h = {'User-Agent': user_agent()}
        h.update(en_tetes or {})
        dernier = None
        for essai in range(3):
            self.requetes.append(chemin)
            try:
                req = urllib.request.Request(self.url + chemin, data=data, headers=h)
                with urllib.request.urlopen(req, timeout=self.delai) as r:
                    return r.read(max_octets)
            except urllib.error.HTTPError as e:
                if e.code in (400, 401, 403, 404):
                    raise ErreurNova('nova_err_http', 'HTTP %d %s' % (e.code, chemin)) from None
                dernier = 'HTTP %d' % e.code
            except (urllib.error.URLError, OSError, ValueError) as e:
                dernier = '%s: %s' % (type(e).__name__, e)
            time.sleep(min(10.0, 1.0 * 3 ** essai) if self.sondage_initial >= 1 else 0.01)
        raise ErreurNova('nova_err_reseau', dernier or '')

    def _json(self, chemin: str, requete: dict | None = None) -> dict:
        data = None
        if requete is not None:
            data = urllib.parse.urlencode({'request-json': json.dumps(requete)}).encode()
        try:
            r = json.loads(self._ouvrir(chemin, data).decode('utf-8', 'replace'))
        except ValueError:
            raise ErreurNova('nova_err_reponse', chemin) from None
        if isinstance(r, dict) and r.get('status') == 'error':
            raise ErreurNova('nova_err_service', str(r.get('errormessage', ''))[:200])
        return r

    # ------------------------------------------------------------------ API
    def connecter(self) -> str:
        r = self._json('/api/login', {'apikey': self.cle_api})
        self.session = str(r.get('session') or '')
        if not self.session:
            raise ErreurNova('nova_err_cle')
        return self.session

    def envoyer(self, octets: bytes, nom: str, parametres: dict) -> int:
        if not self.session:
            self.connecter()
        req = {'session': self.session, 'publicly_visible': 'y' if self.publique else 'n',
               'allow_commercial_use': 'n', 'allow_modifications': 'n', 'crpix_center': True}
        req.update(parametres)
        borne = '===============%s==' % uuid.uuid4().hex
        corps = io.BytesIO()
        corps.write(('--%s\r\nContent-Type: text/plain\r\nMIME-Version: 1.0\r\nContent-disposition: form-data; '
                     'name="request-json"\r\n\r\n%s\r\n' % (borne, json.dumps(req))).encode())
        corps.write(('--%s\r\nContent-Type: application/octet-stream\r\nMIME-Version: 1.0\r\nContent-disposition: '
                     'form-data; name="file"; filename="%s"\r\n\r\n' % (borne, nom)).encode())
        corps.write(octets)
        corps.write(('\r\n--%s--\r\n' % borne).encode())
        r = json.loads(self._ouvrir('/api/upload', corps.getvalue(),
                                    {'Content-Type': 'multipart/form-data; boundary="%s"' % borne}).decode())
        if r.get('status') != 'success' or 'subid' not in r:
            raise ErreurNova('nova_err_service', str(r.get('errormessage', ''))[:200])
        return int(r['subid'])

    def attendre(self, subid: int, arret: threading.Event | None = None, progression=None) -> tuple[str, int | None]:
        """Sonde la soumission puis le travail : ('success', job) | ('failure', job) ; Abandon si `arret`."""
        t0 = time.monotonic()
        pause = self.sondage_initial
        job = None
        while True:
            if arret is not None and arret.is_set():
                raise Abandon()
            if time.monotonic() - t0 > self.delai_max:
                raise ErreurNova('nova_err_delai', 'sub %d' % subid)
            if job is None:
                s = self._json('/api/submissions/%d' % subid)
                jobs = [j for j in (s.get('jobs') or []) if j]
                if jobs:
                    job = int(jobs[-1])
            if job is not None:
                st = self._json('/api/jobs/%d' % job).get('status', '')
                if st in ('success', 'failure'):
                    return st, job
            if progression is not None:
                progression({'etape': 'attente', 'subid': subid, 'job': job, 'secondes': time.monotonic() - t0})
            fin = time.monotonic() + pause
            while time.monotonic() < fin:
                if arret is not None and arret.is_set():
                    raise Abandon()
                time.sleep(min(0.2, pause))
            pause = min(self.sondage_max, pause * 1.5)

    def wcs(self, job: int) -> bytes:
        return self._ouvrir('/wcs_file/%d' % job, max_octets=2_000_000)


# ============================================================================================== résolution
def resoudre(donnees, indices: Indices | None = None, nom: str = 'image.fits', arret=None, progression=None,
             forcer: bool = False, client: Client | None = None) -> dict:
    """Résout une image par nova.astrometry.net.  Rend {'entete': astropy Header (WCS de l'image d'ORIGINE) ou
    None, 'statut': 'resolu'|'echec', 'cache': bool, 'job', 'facteur'}.  Une seule soumission à la fois."""
    from astropy.io import fits
    indices = indices or Indices()
    octets, f = preparer_image(donnees)
    params = indices.parametres(f)
    cle = empreinte(octets, params)
    deja = _etat_cache(cle)
    if not forcer and deja.get('statut') in ('resolu', 'echec'):
        h = fits.Header.fromstring(deja['wcs'], sep='\n') if deja.get('wcs') else None
        return {'entete': ramener_wcs(h, f) if h is not None else None, 'statut': deja['statut'], 'cache': True,
                'job': deja.get('job'), 'facteur': f}
    if client is None:
        r = reglages()
        client = Client(r['cle'], publique=r['public'])
    with _verrou_soumission:
        subid = deja.get('subid') if not forcer else None
        if not subid:
            if progression is not None:
                progression({'etape': 'envoi', 'octets': len(octets)})
            subid = client.envoyer(octets, os.path.splitext(os.path.basename(nom))[0] + '.fits', params)
            _ecrire_cache(cle, subid=subid, statut='en_cours', date=time.time())
        elif not client.session:
            client.connecter()
        statut, job = client.attendre(int(subid), arret, progression)
        if statut != 'success':
            _ecrire_cache(cle, statut='echec', job=job)
            return {'entete': None, 'statut': 'echec', 'cache': False, 'job': job, 'facteur': f}
        brut = client.wcs(job)
    h = fits.Header.fromstring(brut.decode('ascii', 'replace'))
    _ecrire_cache(cle, statut='resolu', job=job, wcs=h.tostring(sep='\n'))
    return {'entete': ramener_wcs(h, f), 'statut': 'resolu', 'cache': False, 'job': job, 'facteur': f}
