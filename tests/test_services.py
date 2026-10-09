"""Sources configurables, rapports d'incident, mise à jour, réseau (serveur local), modules, données 1D."""
import http.server
import io
import json
import os
import threading
import zipfile
from pathlib import Path

import numpy as np
import pytest

from coupole.core import config, donnees, maj, modules, rapports, reseau, sources


# ---------------------------------------------------------------- sources
def doc(**valeurs):
    d = json.loads(json.dumps(sources.defauts()))
    d['version'] = 99
    d['valeurs'].update(valeurs)
    return d


def test_sources_controle_de_forme():
    assert sources.valider(doc()) == []
    assert sources.valider(doc(**{'ohp.tap': 'https://pirate.example.com/tap'}))       # domaine refusé
    assert sources.valider(dict(doc(), valeurs={'cle.inconnue': 'x'}))
    assert sources.valider('pas un objet')
    assert sources.valider(dict(doc(), format=2))


def test_sources_priorite(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, 'chemin_cache_distant', lambda: tmp_path / 'distant.json')
    (tmp_path / 'distant.json').write_text(json.dumps(doc(**{'ohp.tap': 'https://nouveau.obspm.fr/tap'})))
    assert sources.valeur('ohp.tap') == 'https://nouveau.obspm.fr/tap'
    assert sources.toutes()['ohp.tap'][1] == 'distant'
    sources.forcer('ohp.tap', 'http://mon-miroir.local/tap')             # valeur forcée : jamais écrasée
    try:
        assert sources.valeur('ohp.tap') == 'http://mon-miroir.local/tap'
    finally:
        sources.forcer('ohp.tap', None)
    assert sources.valeur('ohp.tap') == 'https://nouveau.obspm.fr/tap'
    (tmp_path / 'distant.json').write_text('{"format": 1, "version": 99, "valeurs": {"ohp.tap": 5}}')
    assert sources.valeur('ohp.tap') == sources.defauts()['valeurs']['ohp.tap']   # mal formé : repli silencieux


def test_reecriture_url():
    sources.forcer('ohp.telechargement.de', 'http://tap-ufe.obspm.fr/getproduct/')
    sources.forcer('ohp.telechargement.vers', 'https://miroir.obspm.fr/produits/')
    try:
        assert sources.reecrire_url('http://tap-ufe.obspm.fr/getproduct/ufe/a.fits') == \
            'https://miroir.obspm.fr/produits/ufe/a.fits'
    finally:
        sources.tout_reinitialiser()
    assert sources.reecrire_url('http://tap-ufe.obspm.fr/getproduct/x') == 'http://tap-ufe.obspm.fr/getproduct/x'


# ---------------------------------------------------------------- rapports
def test_anonymisation(monkeypatch):
    monkeypatch.setenv('USER', 'jdupont')
    t = rapports.anonymiser('%s/Documents/a/b/c/x.py jdupont' % Path.home())
    assert str(Path.home()) not in t and 'jdupont' not in t
    m = rapports.machine()
    assert 'poste' in m and m['poste'].startswith('install-') and 'node' not in m


def test_rien_ne_part_sans_accord(monkeypatch, tmp_path):
    envoyes = []
    monkeypatch.setattr(rapports, '_poster', lambda charge: envoyes.append(charge) or True)
    rapports.init(tmp_path)
    rapports.definir_consentement(False)
    rapports.envoyer('plantage', traceback='x')
    assert not envoyes and list((tmp_path / '_rapports').glob('*.json'))
    rapports.definir_consentement(True)
    assert rapports.vider_file() == 1 and len(envoyes) == 1
    rapports.definir_consentement(False)


# ---------------------------------------------------------------- mise à jour
def test_versions_et_notes():
    assert maj.plus_recente('v1.10.0', '1.9.3') and not maj.plus_recente('1.0.0', '1.0.0')
    corps = '## English\nHello\n## Français\nBonjour'
    assert maj.notes_dans_la_langue(corps, 'fr') == 'Bonjour'
    assert maj.notes_dans_la_langue(corps, 'en') == 'Hello'


def test_archive_piegee_refusee(tmp_path, monkeypatch):
    z = tmp_path / 'm.zip'
    with zipfile.ZipFile(z, 'w') as f:
        f.writestr('../../evil.py', 'x')
    monkeypatch.setattr(maj, 'est_paquet', lambda: True)
    class Rep(io.BytesIO):
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr(maj, '_ouvrir', lambda url: Rep(z.read_bytes()))
    monkeypatch.setattr(maj, 'dossier_app', lambda: tmp_path / 'app')
    (tmp_path / 'app').mkdir()
    with pytest.raises(RuntimeError):
        maj.appliquer({'url': 'https://github.com/x.zip', 'version': '9'})


def test_hotes_de_confiance():
    assert maj._de_confiance('https://objects.githubusercontent.com/a')
    assert not maj._de_confiance('http://github.com/a') and not maj._de_confiance('https://evil.com/a')


def _faux_paquet(tmp_path, monkeypatch, marqueur=None):
    """Un paquet autonome factice : python/bin/python3 et app/ ; `marqueur` = fiche d'installation système."""
    (tmp_path / 'python' / 'bin').mkdir(parents=True)
    (tmp_path / 'python' / 'bin' / 'python3').write_text('')
    (tmp_path / 'app').mkdir()
    if marqueur is not None:
        (tmp_path / 'app' / maj.MARQUEUR_SYSTEME).write_text(json.dumps(marqueur), encoding='utf-8')
    monkeypatch.setattr(maj, 'dossier_app', lambda: tmp_path / 'app')
    monkeypatch.setattr(maj, '_architecture_deb', lambda: 'amd64')


def test_installation_deb_signalee_jamais_appliquee(tmp_path, monkeypatch, capsys):
    """Paquet .deb : les fichiers sont à dpkg sous /opt ; Coupole signale la version, montre le .deb et la commande
    apt, et refuse d'appliquer l'archive."""
    _faux_paquet(tmp_path, monkeypatch, {'type': 'deb', 'architecture': 'amd64', 'actif': 'coupole-linux-amd64.deb',
                                         'commande': 'sudo apt install ./coupole-linux-amd64.deb'})
    assert maj.est_paquet() and maj.type_installation() == 'deb' and not maj.peut_appliquer()
    with pytest.raises(RuntimeError, match='system package'):
        maj.appliquer({'url': 'https://github.com/x.zip', 'version': '9'})
    # sans Release lue : adresse stable « latest/download »
    c = maj.consigne_systeme(None)
    assert c['url'].endswith('/releases/latest/download/coupole-linux-amd64.deb')
    assert c['commande'] == 'sudo apt install ./coupole-linux-amd64.deb'
    # avec la Release : l'actif .deb qu'elle contient
    c = maj.consigne_systeme({'deb': 'https://github.com/d/coupole_0.9.0_amd64.deb', 'deb_nom': 'coupole_0.9.0_amd64.deb',
                              'page': 'https://github.com/d'})
    assert c['url'].endswith('coupole_0.9.0_amd64.deb') and c['commande'] == 'sudo apt install ./coupole_0.9.0_amd64.deb'
    # la ligne de commande, dans les deux langues
    from coupole import cli
    monkeypatch.setattr(maj, 'verifier', lambda v: {'version': '9.9.9', 'url': 'https://github.com/x.zip', 'taille': 1,
                                                    'notes': '## Français\nN\n## English\nN', 'page': 'https://github.com/p',
                                                    'deb': 'https://github.com/p/coupole-linux-amd64.deb',
                                                    'deb_nom': 'coupole-linux-amd64.deb'})
    assert cli.main(['--lang', 'fr', 'maj', '--appliquer']) == 0
    fr = capsys.readouterr().out
    assert 'paquet système' in fr and 'sudo apt install ./coupole-linux-amd64.deb' in fr and 'coupole-linux-amd64.deb' in fr
    assert cli.main(['--lang', 'en', 'update', '--apply']) == 0
    en = capsys.readouterr().out
    assert 'system package' in en and 'sudo apt install' in en and 'Mise à jour' not in en
    assert not list((tmp_path / 'app').glob('*.py'))        # rien n'a été écrit dans app/


def test_paquet_autonome_inscriptible_reste_un_paquet(tmp_path, monkeypatch):
    _faux_paquet(tmp_path, monkeypatch)
    assert maj.type_installation() == 'paquet' and maj.peut_appliquer()
    monkeypatch.setattr(maj, 'est_paquet', lambda: False)
    assert maj.type_installation() == 'pip'


@pytest.mark.skipif(os.name == 'nt' or (hasattr(os, 'geteuid') and os.geteuid() == 0),
                    reason='root écrit partout ; droits POSIX requis')
def test_paquet_non_inscriptible_signale_sans_appliquer(tmp_path, monkeypatch):
    _faux_paquet(tmp_path, monkeypatch)
    (tmp_path / 'app').chmod(0o555)
    try:
        assert maj.type_installation() == 'systeme' and not maj.peut_appliquer()
        with pytest.raises(RuntimeError, match='system package'):
            maj.appliquer({'url': 'https://github.com/x.zip', 'version': '9'})
    finally:
        (tmp_path / 'app').chmod(0o755)


def test_verifier_retient_le_deb_de_l_architecture(monkeypatch):
    release = {'tag_name': 'v9.0.0', 'html_url': 'https://github.com/r', 'body': '## English\nx',
               'assets': [{'name': 'coupole-app-9.0.0.zip', 'browser_download_url': 'https://github.com/a/app.zip', 'size': 5},
                          {'name': 'coupole_9.0.0_arm64.deb', 'browser_download_url': 'https://github.com/a/arm.deb'},
                          {'name': 'coupole_9.0.0_amd64.deb', 'browser_download_url': 'https://github.com/a/v.deb'},
                          {'name': 'coupole-linux-amd64.deb', 'browser_download_url': 'https://github.com/a/s.deb'}]}

    class Rep(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr(maj, '_ouvrir', lambda url: Rep(json.dumps(release).encode()))
    monkeypatch.setattr(maj, 'depot', lambda: 'x/y')
    monkeypatch.setattr(maj, '_architecture_deb', lambda: 'amd64')
    m = maj.verifier('0.1.0')
    assert m['version'] == '9.0.0' and m['url'].endswith('app.zip')
    assert m['deb'] == 'https://github.com/a/s.deb' and m['deb_nom'] == 'coupole-linux-amd64.deb'   # nom stable d'abord
    release['assets'].pop()
    assert maj.verifier('0.1.0')['deb'] == 'https://github.com/a/v.deb'
    monkeypatch.setattr(maj, '_architecture_deb', lambda: 'arm64')
    assert maj.verifier('0.1.0')['deb'] == 'https://github.com/a/arm.deb'


# ---------------------------------------------------------------- réseau : reprise sur un serveur local avec Range
class Gestionnaire(http.server.BaseHTTPRequestHandler):
    contenu = b'SIMPLE  =                    T' + bytes(2880 * 3 - 30)
    coupe = [True]

    def log_message(self, *a):
        pass

    def do_GET(self):
        debut, fin = 0, len(self.contenu) - 1
        rg = self.headers.get('Range')
        if rg:
            a, b = rg.split('=')[1].split('-')
            debut = int(a)
            fin = int(b) if b else fin
        corps = self.contenu[debut:fin + 1]
        self.send_response(206 if rg else 200)
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (debut, fin, len(self.contenu)))
        self.send_header('Content-Length', str(len(corps)))
        self.end_headers()
        assert self.headers['User-Agent'].startswith('Coupole/')
        if self.coupe[0] and len(corps) > 1:          # première fois : coupure au milieu
            self.coupe[0] = False
            self.wfile.write(corps[:4000])
            return
        self.wfile.write(corps)


@pytest.fixture
def serveur():
    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Gestionnaire)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield 'http://127.0.0.1:%d/f.fits' % s.server_address[1]
    s.shutdown()


def test_telechargement_avec_reprise(tmp_path, serveur, monkeypatch):
    monkeypatch.setattr('time.sleep', lambda s: None)
    p = str(tmp_path / 'f.fits')
    etat, recu = reseau.telecharger(serveur, p, taille_attendue=2880 * 3, limiteur=reseau.LimiteurDebit(10e6))
    assert etat == 'ok' and open(p, 'rb').read() == Gestionnaire.contenu
    assert reseau.telecharger(serveur, p)[0] == 'deja'


def test_annulation(tmp_path, serveur):
    arret = threading.Event()
    arret.set()
    with pytest.raises(reseau.Annule):
        reseau.telecharger(serveur, str(tmp_path / 'g.fits'), arret=arret)


# ---------------------------------------------------------------- modules
def test_decouverte_des_modules():
    ids = [m.id for m in modules.decouvrir(recharger=True)]
    assert ids[0] == 'ohp' and {'machine', 'donnees', 'sites'} <= set(ids)


def test_module_defectueux_ignore(tmp_path):
    d = config.dossier_config() / 'modules' / 'casse'
    d.mkdir(parents=True, exist_ok=True)
    (d / '__init__.py').write_text('')
    (d / 'manifest.json').write_text('{"id": "casse", "version": "1"}')       # nom manquant
    try:
        mods = modules.decouvrir(recharger=True)
        assert 'casse' not in [m.id for m in mods]
        assert any('casse' in p for p, _ in modules.erreurs)
    finally:
        import shutil
        shutil.rmtree(d)
        modules.decouvrir(recharger=True)


def test_module_utilisateur_ajoute(tmp_path):
    d = config.dossier_config() / 'modules' / 'monmodule'
    d.mkdir(parents=True, exist_ok=True)
    (d / '__init__.py').write_text('')
    (d / 'textes.py').write_text("TEXTES = {'mm_bonjour': {'fr': 'Bonjour', 'en': 'Hello'}}")
    (d / 'manifest.json').write_text(json.dumps({'id': 'monmodule', 'version': '0.1', 'nom': {'fr': 'Mon module',
                                                 'en': 'My module'}, 'textes': 'textes:TEXTES'}))
    try:
        mods = modules.decouvrir(recharger=True)
        assert 'monmodule' in [m.id for m in mods]
        from coupole.core.i18n import tr
        assert tr('mm_bonjour', 'en') == 'Hello'
    finally:
        import shutil
        shutil.rmtree(d)
        modules.decouvrir(recharger=True)


# ---------------------------------------------------------------- données 1D
def test_spectre_hi_fits(tmp_path):
    from astropy.io import fits
    n, f0 = 600, donnees.HI_HZ
    df = 2.0e6 / n
    f = f0 - 1.0e6 + np.arange(n) * df
    v_in = 31.0
    y = 2 + 4 * np.exp(-0.5 * ((f - donnees.frequence_depuis_vitesse(v_in, f0)) / 15e3) ** 2)
    h = fits.Header()
    h.update(CTYPE1='FREQ', CUNIT1='Hz', CRVAL1=f[0], CDELT1=df, CRPIX1=1.0, RESTFRQ=f0, SPECSYS='LSRK')
    p = tmp_path / 's.fits'
    fits.PrimaryHDU(y.reshape(1, 1, n), header=h).writeto(p)          # cube radio 1 x 1 x N
    d = donnees.lire(p)[0]
    assert d.genre == 'spectre' and d.meta['specsys'] == 'LSRK' and len(d.x) == n
    v = donnees.vitesse_radio(d.x, d.meta['restfreq_hz'])
    centre = float(np.sum(v * (d.y - 2)) / np.sum(d.y - 2))           # barycentre de la raie
    assert abs(centre - v_in) < 0.05
    dv_canal = abs(v[1] - v[0])
    assert abs(dv_canal - donnees.C_KM_S * df / f0) < 1e-9


def test_csv_et_serie_temporelle(tmp_path):
    p = tmp_path / 'courbe.csv'
    p.write_text('# courbe de lumière\nMJD;mag\n60000.1;14.2\n60000.2;14.3\n60000.3;14.1\n')
    d = donnees.lire(p)[0]
    assert d.genre == 'serie' and d.nom_x == 'MJD' and list(d.y) == [14.2, 14.3, 14.1]
    q = tmp_path / 'spectre.txt'
    q.write_text('freq (MHz)  Ta (K)\n1420.0 1.0\n1420.4 3.0\n1420.8 1.0\n')
    s = donnees.lire(q)[0]
    assert s.genre == 'spectre' and s.unite_x == 'MHz'
    assert abs(donnees.vitesse_radio(donnees.en_hz(s.x, s.unite_x))[1] - 1.213974) < 1e-5     # SageMath


def test_table_fits(tmp_path):
    from astropy.io import fits
    t = fits.BinTableHDU.from_columns([fits.Column('TIME', 'D', array=np.arange(5.0)),
                                       fits.Column('FLUX', 'E', array=np.ones(5))])
    fits.HDUList([fits.PrimaryHDU(), t]).writeto(tmp_path / 't.fits')
    d = [x for x in donnees.lire(tmp_path / 't.fits') if x.genre != 'image'][0]
    assert d.genre == 'serie' and d.nom_y == 'FLUX'


def test_format_inconnu():
    with pytest.raises(ValueError):
        donnees.lire('fichier.inconnu')
