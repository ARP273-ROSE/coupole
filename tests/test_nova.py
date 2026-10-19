"""Astrométrie en ligne (0.8.0) : client nova.astrometry.net contre un FAUX serveur qui imite l'API officielle
(aucun appel réel), chaîne commune en-tête → ASTAP → astrometry.net local → nova, et retour de la WCS d'une image
réduite à l'image d'origine."""
import http.server
import json
import threading
import time
import urllib.parse

import numpy as np
import pytest

from coupole.core import astrometrie as A
from coupole.core import nova as N


class FauxNova:
    """/api/login, /api/upload (multipart), /api/submissions/<id>, /api/jobs/<id>, /wcs_file/<id>."""

    def __init__(self, cle='cle-de-test', resoudre=True, jobs_apres=2, echecs_reseau=0):
        self.cle, self.resoudre, self.jobs_apres = cle, resoudre, jobs_apres
        self.echecs_reseau = echecs_reseau
        self.envois: list = []
        self.requetes: list = []
        self.sondages = 0
        self.verrou = threading.Lock()
        self.en_cours = 0
        self.max_simultanes = 0
        faux = self

        class G(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _rep(self, code, corps, ctype='application/json'):
                b = corps if isinstance(corps, bytes) else json.dumps(corps).encode()
                self.send_response(code)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_POST(self):
                n = int(self.headers.get('Content-Length') or 0)
                corps = self.rfile.read(n)
                with faux.verrou:
                    faux.requetes.append(self.path)
                    if faux.echecs_reseau > 0:
                        faux.echecs_reseau -= 1
                        self._rep(503, {'status': 'error'})
                        return
                if self.path == '/api/login':
                    req = json.loads(urllib.parse.parse_qs(corps.decode())['request-json'][0])
                    if req.get('apikey') != faux.cle:
                        self._rep(200, {'status': 'error', 'errormessage': 'bad apikey'})
                        return
                    self._rep(200, {'status': 'success', 'session': 'sess42'})
                elif self.path == '/api/upload':
                    ct = self.headers.get('Content-Type', '')
                    assert ct.startswith('multipart/form-data')
                    debut = corps.index(b'\r\n\r\n') + 4
                    fin = corps.index(b'\r\n--', debut)
                    req = json.loads(corps[debut:fin])
                    with faux.verrou:
                        faux.en_cours += 1
                        faux.max_simultanes = max(faux.max_simultanes, faux.en_cours)
                        faux.envois.append({'req': req, 'octets': len(corps)})
                        sub = len(faux.envois)
                    self._rep(200, {'status': 'success', 'subid': sub, 'hash': 'x'})
                else:
                    self._rep(404, {})

            def do_GET(self):
                with faux.verrou:
                    faux.requetes.append(self.path)
                p = self.path.strip('/').split('/')
                if p[:2] == ['api', 'submissions']:
                    with faux.verrou:
                        faux.sondages += 1
                        pret = faux.sondages >= faux.jobs_apres
                    self._rep(200, {'jobs': [int(p[2]) + 1000] if pret else [], 'job_calibrations': []})
                elif p[:2] == ['api', 'jobs']:
                    with faux.verrou:
                        faux.en_cours = max(0, faux.en_cours - 1)
                    self._rep(200, {'status': 'success' if faux.resoudre else 'failure'})
                elif p[0] == 'wcs_file':
                    from astropy.io import fits
                    h = fits.Header()
                    h['CTYPE1'], h['CTYPE2'] = 'RA---TAN-SIP', 'DEC--TAN-SIP'
                    h['CRVAL1'], h['CRVAL2'], h['CRPIX1'], h['CRPIX2'] = 10.5, 20.25, 50.5, 40.5
                    h['CD1_1'], h['CD1_2'], h['CD2_1'], h['CD2_2'] = -2e-3, 0.0, 0.0, 2e-3
                    h['A_ORDER'], h['A_2_0'], h['B_ORDER'], h['B_0_2'] = 2, 1e-5, 2, -2e-5
                    self._rep(200, fits.PrimaryHDU(header=h).header.tostring().encode(), 'application/fits')
                else:
                    self._rep(404, {})

        self.http = http.server.ThreadingHTTPServer(('127.0.0.1', 0), G)
        self.http.daemon_threads = True
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = 'http://127.0.0.1:%d' % self.http.server_address[1]

    def client(self, **k):
        return N.Client(k.pop('cle', self.cle), self.url, sondage_initial=0.01, sondage_max=0.02, **k)

    def fermer(self):
        self.http.shutdown()
        self.http.server_close()


@pytest.fixture
def faux():
    f = FauxNova()
    yield f
    f.fermer()


def _image(h=300, w=400, graine=0):
    rng = np.random.default_rng(graine)
    a = rng.normal(100, 5, (h, w)).astype(np.float32)
    for _ in range(40):
        x, y = rng.uniform(5, w - 5), rng.uniform(5, h - 5)
        yy, xx = np.mgrid[0:h, 0:w]
        a += 800 * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / 3.0)
    return a


def test_parcours_complet_et_cache(faux):
    img = _image()
    ind = N.Indices(echelle_arcsec=7.2, ra=10.4, dec=20.3, rayon_deg=2.0)
    r = N.resoudre(img, ind, 'lune.fits', client=faux.client())
    assert r['statut'] == 'resolu' and not r['cache'] and r['facteur'] == 1
    assert r['entete']['CRVAL1'] == 10.5 and A.a_une_wcs(r['entete'])
    req = faux.envois[0]['req']
    assert req['session'] == 'sess42' and req['publicly_visible'] == 'n' and req['allow_commercial_use'] == 'n'
    assert req['scale_units'] == 'arcsecperpix' and req['scale_lower'] == pytest.approx(5.76) and \
        req['scale_upper'] == pytest.approx(8.64)
    assert (req['center_ra'], req['center_dec'], req['radius']) == (10.4, 20.3, 2.0)
    assert faux.sondages >= 2                                          # attendu que le travail existe
    # même image, mêmes indices : jamais renvoyée
    n = len(faux.requetes)
    r2 = N.resoudre(img, ind, 'lune.fits', client=faux.client())
    assert r2['cache'] and r2['statut'] == 'resolu' and len(faux.requetes) == n and len(faux.envois) == 1
    assert faux.cle not in json.dumps(N._etat_cache(N.empreinte(N.preparer_image(img)[0], ind.parametres())))


def test_echec_garde_et_force(faux):
    faux.resoudre = False
    img = _image(graine=1)
    assert N.resoudre(img, None, client=faux.client())['statut'] == 'echec'
    assert N.resoudre(img, None, client=faux.client())['cache']                     # un refus n'est pas renvoyé
    assert len(faux.envois) == 1
    faux.resoudre = True
    assert N.resoudre(img, None, client=faux.client(), forcer=True)['statut'] == 'resolu'
    assert len(faux.envois) == 2


def test_reprise_apres_abandon(faux):
    faux.jobs_apres = 10 ** 9                                   # le travail n'apparaît jamais : on abandonne
    arret = threading.Event()
    threading.Timer(0.3, arret.set).start()
    img = _image(graine=2)
    with pytest.raises(N.Abandon):
        N.resoudre(img, None, arret=arret, client=faux.client())
    assert len(faux.envois) == 1
    faux.jobs_apres = 0                                          # relancé plus tard : on reprend le sondage
    r = N.resoudre(img, None, client=faux.client())
    assert r['statut'] == 'resolu' and len(faux.envois) == 1    # pas de second envoi


def test_une_soumission_a_la_fois_et_erreurs(faux):
    faux.jobs_apres = 3
    res = []
    fils = [threading.Thread(target=lambda g=g: res.append(N.resoudre(_image(graine=10 + g), None,
                                                                      client=faux.client()))) for g in range(3)]
    for f in fils:
        f.start()
    for f in fils:
        f.join(30)
    assert len(res) == 3 and faux.max_simultanes == 1
    with pytest.raises(N.ErreurNova) as e:
        faux.client(cle='mauvaise').connecter()
    assert e.value.cle == 'nova_err_service'
    with pytest.raises(N.ErreurNova):
        N.Client('')
    faux.echecs_reseau = 2                                      # deux 503 : réessayé, puis réussi
    assert faux.client().connecter() == 'sess42'
    c = faux.client(delai_max=0.2)
    faux.jobs_apres = 10 ** 9
    c.connecter()
    with pytest.raises(N.ErreurNova) as e:
        c.attendre(1)
    assert e.value.cle == 'nova_err_delai'


def test_image_allegee_et_wcs_ramenee():
    from astropy.io import fits
    from astropy.wcs import WCS
    grande = np.zeros((3000, 4000), np.float32)
    octets, f = N.preparer_image(grande, pixels_max=1_000_000)
    assert f == 4 and fits.getdata(__import__('io').BytesIO(octets)).shape == (750, 1000)
    h = fits.Header()
    h['NAXIS'], h['NAXIS1'], h['NAXIS2'] = 2, 1000, 750
    h['CTYPE1'], h['CTYPE2'] = 'RA---TAN-SIP', 'DEC--TAN-SIP'
    h['CRVAL1'], h['CRVAL2'], h['CRPIX1'], h['CRPIX2'] = 150.0, 2.0, 500.5, 375.5
    h['CD1_1'], h['CD1_2'], h['CD2_1'], h['CD2_2'] = -8e-4, 1e-5, 1e-5, 8e-4
    h['A_ORDER'], h['B_ORDER'] = 2, 2
    h['A_2_0'], h['A_1_1'], h['B_0_2'] = 3e-6, -1e-6, 2e-6
    g = N.ramener_wcs(h, f)
    g['NAXIS1'], g['NAXIS2'] = 4000, 3000
    petit, grand = WCS(h), WCS(g)
    for x, y in ((10.0, 20.0), (900.0, 700.0), (500.0, 100.0)):
        # le pixel (x, y) de l'image réduite couvre les pixels f x … f x + f − 1 de l'originale : centre f x + 1,5
        a = petit.all_pix2world([[x, y]], 0)[0]
        b = grand.all_pix2world([[f * x + (f - 1) / 2, f * y + (f - 1) / 2]], 0)[0]
        assert np.allclose(a, b, atol=1e-9)


def test_indices_et_chaine(monkeypatch, faux):
    from astropy.io import fits
    h = fits.Header()
    h['XPIXSZ'], h['FOCALLEN'], h['RA'], h['DEC'] = 3.76, 530.0, 83.8, -5.4
    ind = A.indices_de(h, 6000)
    assert ind.echelle_arcsec == pytest.approx(206.265 * 3.76 / 530) and (ind.ra, ind.dec) == (83.8, -5.4)
    assert ind.rayon_deg == pytest.approx(1.5 * ind.echelle_arcsec * 6000 / 3600)
    img = _image(graine=5)
    # en-tête déjà résolu : rien d'autre n'est tenté
    w = fits.Header()
    w['CTYPE1'], w['CRVAL1'] = 'RA---TAN', 1.0
    assert A.resoudre(img, w, 'auto', True)[1] == 'entete'
    # aucun moteur local, pas d'accord : rien
    monkeypatch.setattr(A, 'par_astap', lambda *a, **k: None)
    monkeypatch.setattr(A, 'par_astrometry_net', lambda *a, **k: None)
    assert A.resoudre(img, h, 'auto', False) == (None, '')
    # accord + clé : nova (faux serveur)
    monkeypatch.setattr(N, 'reglages', lambda: {'cle': faux.cle, 'public': False})
    monkeypatch.setattr(N, 'url_service', lambda: faux.url)
    monkeypatch.setattr(N, 'SONDAGE_INITIAL', 0.01)
    orig = N.Client.__init__

    def rapide(self, *a, **k):
        k.update(sondage_initial=0.01, sondage_max=0.02)
        orig(self, *a, **k)
    monkeypatch.setattr(N.Client, '__init__', rapide)
    sol, source = A.resoudre(img, h, 'auto', True)
    assert source == 'nova' and sol['CRVAL1'] == 10.5
    # mode « astrometry.net » seul : jamais en ligne même avec l'accord
    assert A.resoudre(_image(graine=6), h, 'astrometry.net', True) == (None, '')


def test_cle_gardee_a_part(tmp_path):
    import os
    import sys
    N.enregistrer('ma-cle', False)
    assert N.reglages() == {'cle': 'ma-cle', 'public': False} and N.configure()
    if sys.platform != 'win32':
        assert oct(os.stat(N._chemin_reglages()).st_mode & 0o777) == '0o600'
    from coupole.core import config
    assert 'ma-cle' not in json.dumps(dict(config.reglages().valeurs))
    N.enregistrer('', None)
    assert not N.configure()
    time.sleep(0)
