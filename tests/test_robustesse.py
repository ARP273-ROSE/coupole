"""Anti-plantage et sécurité du cœur : réglages corrompus, écritures atomiques, archive de mise à jour piégée, HTTPS
obligatoire, XISF et FITS bornés, budget mémoire, réseau en panne, rapports bornés et anonymes, vigie de gel,
plantage natif (faulthandler), noms de dossiers sûrs, console cp1252, fuseau inconnu, langue Windows."""
import json
import os
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path

import numpy as np
import pytest

from coupole.core import config, i18n, maj, parallele, rapports, reseau, sources, xisf
from coupole.core.fitsentete import lire_cartes
from coupole.core.machine import Machine

from .serveur_local import ServeurLocal


# ---------------------------------------------------------------- réglages
def test_reglages_corrompus_mis_de_cote(tmp_path):
    p = tmp_path / 'reglages.json'
    p.write_text('{"langue": "fr", ...pas du json', encoding='utf-8')
    r = config.Reglages(p)
    assert r['langue'] == 'auto' and r.restaure
    copies = list(tmp_path.glob('reglages.json.corrompu-*'))
    assert len(copies) == 1 and 'pas du json' in copies[0].read_text(encoding='utf-8')
    assert json.loads(p.read_text(encoding='utf-8'))['id_installation']          # réécrit, valide
    p.write_text('[1, 2, 3]', encoding='utf-8')                                 # valide mais pas un objet
    r2 = config.Reglages(p)
    assert r2['langue'] == 'auto' and len(list(tmp_path.glob('reglages.json.corrompu-*'))) == 2


def test_ecriture_atomique_sans_fichier_partiel(tmp_path, monkeypatch):
    p = tmp_path / 'x.json'
    config.ecrire_json_atomique(p, {'a': 1})
    assert json.loads(p.read_text(encoding='utf-8')) == {'a': 1}
    import os as _os
    vrai = _os.fdopen

    class Plein:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def write(self, s):
            raise OSError(28, 'No space left on device')
    monkeypatch.setattr(_os, 'fdopen', lambda fd, *a, **k: (_os.close(fd), Plein())[1])
    with pytest.raises(OSError):
        config.ecrire_json_atomique(p, {'a': 2})
    monkeypatch.setattr(_os, 'fdopen', vrai)
    assert json.loads(p.read_text(encoding='utf-8')) == {'a': 1}               # l'ancien contenu est intact
    assert [f.name for f in tmp_path.iterdir()] == ['x.json']                  # aucun .tmp orphelin


# ---------------------------------------------------------------- mise à jour : archive
def _zip(tmp_path, membres):
    z = tmp_path / 'm.zip'
    with zipfile.ZipFile(z, 'w') as f:
        for nom, contenu in membres:
            f.writestr(nom, contenu)
    return z


@pytest.mark.parametrize('membre', ['../evil.py', '/etc/passwd', 'C:\\Windows\\x.py', 'a/../../b.py'])
def test_archive_zip_slip_refusee(tmp_path, membre):
    z = _zip(tmp_path, [(membre, 'x'), ('lancer.py', 'x')])
    with zipfile.ZipFile(z) as f, pytest.raises(RuntimeError):
        maj.verifier_archive(f, tmp_path / 'ext')


def test_archive_lien_symbolique_et_bombe_refuses(tmp_path):
    z = tmp_path / 'l.zip'
    with zipfile.ZipFile(z, 'w') as f:
        info = zipfile.ZipInfo('lien')
        info.external_attr = (0o120777 << 16)
        f.writestr(info, '/etc/passwd')
    with zipfile.ZipFile(z) as f, pytest.raises(RuntimeError, match='symbolic'):
        maj.verifier_archive(f, tmp_path / 'ext')
    z2 = tmp_path / 'b.zip'
    with zipfile.ZipFile(z2, 'w', zipfile.ZIP_DEFLATED) as f:
        f.writestr('gros.bin', b'\0' * (maj.CONTENU_MAX + 1))
    with zipfile.ZipFile(z2) as f, pytest.raises(RuntimeError, match='unpacked'):
        maj.verifier_archive(f, tmp_path / 'ext')
    z3 = _zip(tmp_path, [('coupole/__init__.py', ''), ('lancer.py', 'x'), ('sous/dossier/f.py', 'y')])
    with zipfile.ZipFile(z3) as f:
        maj.verifier_archive(f, tmp_path / 'ext')                             # archive honnête : acceptée


# ---------------------------------------------------------------- sources : HTTPS, taille
def test_sources_distant_https_obligatoire_et_taille(monkeypatch):
    d = json.loads(json.dumps(sources.defauts()))
    d['version'] = 99
    d['valeurs']['sources.distant'] = 'http://raw.githubusercontent.com/x/y/sources.json'
    assert any('https' in p for p in sources.valider(d))
    d['valeurs']['sources.distant'] = 'https://raw.githubusercontent.com/x/y/sources.json'
    assert sources.valider(d) == []
    import urllib.request

    class Rep:
        def __init__(self, n):
            self.n = n

        def read(self, k=-1):
            return b'{' + b' ' * (self.n - 2) + b'}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr(urllib.request, 'urlopen', lambda req, timeout=0: Rep(sources.TAILLE_MAX_DISTANT + 10))
    assert sources.rafraichir_distant() is False                               # trop gros : refusé sans planter


# ---------------------------------------------------------------- XISF et FITS bornés
def test_xisf_tronque_et_geometrie_demesuree(tmp_path):
    p = tmp_path / 'a.xisf'
    xisf.ecrire(p, np.arange(64, dtype='<u2').reshape(8, 8), [])
    tronque = tmp_path / 't.xisf'
    tronque.write_bytes(p.read_bytes()[:-20])                                  # fichier partiel (coupure)
    with pytest.raises(xisf.ErreurXISF):
        xisf.lire(tronque)
    brut = p.read_bytes()
    abime = brut.replace(b'geometry="8:8:1"', b'geometry="99999:99999:1"')    # XML plus long que l'en-tête annoncé
    (tmp_path / 'e.xisf').write_bytes(abime)
    with pytest.raises(xisf.ErreurXISF, match='XML'):
        xisf.lire(tmp_path / 'e.xisf')
    lg = int.from_bytes(brut[8:12], 'little')
    xml = brut[16:16 + lg].replace(b'geometry="8:8:1"', b'geometry="99999999:99999999:1"')
    enorme = b'XISF0100' + len(xml).to_bytes(4, 'little') + bytes(4) + xml + brut[16 + lg:]
    (tmp_path / 'g.xisf').write_bytes(enorme)
    with pytest.raises(xisf.ErreurXISF, match='too large'):
        xisf.lire(tmp_path / 'g.xisf')
    faux = tmp_path / 'f.xisf'
    faux.write_bytes(b'XISF0100' + (xisf.ENTETE_MAX + 1).to_bytes(4, 'little') + bytes(4) + b'x' * 100)
    with pytest.raises(xisf.ErreurXISF, match='header too large'):
        xisf.lire(faux)


def test_fits_qui_nen_est_pas_un(tmp_path):
    p = tmp_path / 'x.fits'
    p.write_bytes(b'\0' * 2880 * 10)
    with pytest.raises(IOError, match='SIMPLE'):
        lire_cartes(p)
    q = tmp_path / 'sans_end.fits'
    q.write_bytes(b'SIMPLE  =                    T'.ljust(80) * 36 * 3000)   # 3 000 blocs sans END
    t0 = time.monotonic()
    with pytest.raises(IOError, match='END'):
        lire_cartes(q)
    assert time.monotonic() - t0 < 5


def test_xisf_tmp_nettoye_si_disque_plein(tmp_path, monkeypatch):
    import builtins
    vrai = builtins.open

    def ouvrir(chemin, mode='r', *a, **k):
        f = vrai(chemin, mode, *a, **k)
        if 'wb' in mode and str(chemin).endswith('.tmp'):
            class Plein:
                def write(self, b):
                    raise OSError(28, 'No space left on device')

                def flush(self):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    f.close()
                    return False
            return Plein()
        return f
    monkeypatch.setattr(builtins, 'open', ouvrir)
    with pytest.raises(OSError):
        xisf.ecrire(tmp_path / 'p.xisf', np.zeros((4, 4), '<u2'), [])
    monkeypatch.setattr(builtins, 'open', vrai)
    assert list(tmp_path.iterdir()) == []                                      # ni .xisf ni .tmp


# ---------------------------------------------------------------- parallélisme : petite et grosse machine, budget
def _m(coeurs, logiques, tot, dispo):
    return Machine('Linux', '6', 'x86_64', 'cpu', coeurs, logiques, tot, dispo, '3.12', [])


def test_plans_petite_et_grosse_machine():
    petite = parallele.planifier(_m(2, 4, 2048, 1200))
    assert (petite.telechargements, petite.conversions, petite.econome) == (2, 1, True)
    grosse = parallele.planifier(_m(32, 64, 65536, 60000))
    assert (grosse.telechargements, grosse.conversions, grosse.econome) == (3, 16, False)
    assert parallele.budget_memoire_mo(grosse) == 16 * parallele.MEMOIRE_PAR_CONVERSION_MO <= 60000 * parallele.PART_MEMOIRE
    moyenne = parallele.planifier(_m(6, 12, 32768, 20000))
    assert moyenne.conversions == 5 and moyenne.raison == 'parallele_raison_coeurs'


def test_bridage_manuel_borne_par_la_memoire():
    p = parallele.planifier(_m(32, 64, 4096, 2000), conversions=16)
    assert p.conversions == max(1, int(2000 * parallele.PART_MEMOIRE // parallele.MEMOIRE_PAR_CONVERSION_MO)) == 2
    assert p.raison == 'parallele_raison_memoire'
    assert parallele.planifier(_m(32, 64, 65536, 60000), conversions=6).conversions == 6


# ---------------------------------------------------------------- réseau : panne totale, requête unique
def test_reseau_panne_totale_puis_une_seule_requete(tmp_path, monkeypatch):
    monkeypatch.setattr('time.sleep', lambda *_: None)
    s = ServeurLocal({'/a.fits': b'SIMPLE  =                    T' + bytes(2880 * 2 - 30)})
    try:
        s.pannes['/a.fits'] = 'refus'
        with pytest.raises(IOError):
            reseau.telecharger(s.url('/a.fits'), str(tmp_path / 'a.fits'), essais=3)
        assert s.compter('/a.fits') == 3 and not (tmp_path / 'a.fits').exists()
        s.pannes.clear()
        s.requetes.clear()
        assert reseau.telecharger(s.url('/a.fits'), str(tmp_path / 'a.fits'), taille_attendue=2880 * 2)[0] == 'ok'
        assert s.compter('/a.fits') == 1                                       # un seul GET, pas de sondage
        assert reseau.telecharger(s.url('/a.fits'), str(tmp_path / 'a.fits'), taille_attendue=2880 * 2)[0] == 'deja'
        assert s.compter('/a.fits') == 1                                       # déjà complet : aucune requête
    finally:
        s.fermer()


# ---------------------------------------------------------------- rapports : bornes, anonymat
def test_rapport_borne_et_anonyme(monkeypatch, tmp_path):
    import platform
    rapports.init(tmp_path)
    rapports.definir_consentement(False)
    hote = platform.node()
    gros = 'x' * 200_000 + ' ' + str(Path.home()) + '/Documents/a/b/c/d.txt ' + (hote if len(hote) > 2 else 'zz')
    r = rapports.envoyer('manuel', description=gros, detail={'chemin': str(Path.home()) + '/a/b/c/d', 'n': 3},
                         liste=[str(Path.home()) + '/x/y/z/w'])
    charge = json.dumps(r, ensure_ascii=False).encode('utf-8')
    assert len(charge) <= rapports.RAPPORT_MAX
    assert str(Path.home()) not in charge.decode('utf-8')
    if len(hote) > 2:
        assert hote not in r['description']
    assert r['detail']['chemin'].startswith('~') and r['detail']['n'] == 3
    assert r['liste'][0].startswith('~')
    assert 'poste' in r and not any(k in r for k in ('node', 'hostname', 'user'))
    f = sorted((tmp_path / '_rapports').glob('*.json'))
    assert f and json.loads(f[-1].read_text(encoding='utf-8'))['genre'] == 'manuel'
    rapports.definir_consentement(False)


def test_vigie_detecte_un_gel(monkeypatch):
    envoyes = []
    monkeypatch.setattr(rapports, 'envoyer', lambda genre, **c: envoyes.append((genre, c)) or {})
    v = rapports.Vigie(seuil=0.4, periode=0.1)
    v.battre()
    v.demarrer()
    try:
        time.sleep(1.0)                                   # le « fil graphique » ne bat plus : gel simulé
        assert [g for g, _ in envoyes] == ['gel'] and envoyes[0][1]['phase'] == 'debut'
        assert 'GUI' in envoyes[0][1]['piles']            # la pile du fil surveillé est jointe
        v.battre()
        assert [g for g, _ in envoyes] == ['gel', 'gel'] and envoyes[1][1]['phase'] == 'fin'
    finally:
        v.arreter()


def test_crash_natif_releve_par_faulthandler(tmp_path, monkeypatch):
    journal = tmp_path / '_crash_natif.log'
    code = ('import faulthandler, ctypes, sys\n'
            'f = open(sys.argv[1], "w"); faulthandler.enable(f)\n'
            'ctypes.string_at(0)\n')                      # lecture de l adresse 0 : SIGSEGV
    r = subprocess.run([sys.executable, '-c', code, str(journal)], capture_output=True)
    assert r.returncode != 0 and journal.stat().st_size > 0
    envoyes = []
    monkeypatch.setattr(rapports, 'envoyer', lambda genre, **c: envoyes.append((genre, c)) or {})
    assert rapports.relever_crash_natif(journal) is True
    assert envoyes[0][0] == 'crash_natif' and 'Fatal Python error' in envoyes[0][1]['trace']
    assert not journal.exists() and rapports.relever_crash_natif(journal) is False


# ---------------------------------------------------------------- noms sûrs, console, fuseau, langue
def test_noms_de_dossiers_surs_partout():
    from coupole.modules.ohp.conversion import LONGUEUR_NOM_MAX, sur
    assert sur('CON') == 'CON_' and sur('com1') == 'com1_' and sur('nul.fits') == 'nul.fits_'
    assert sur('..') == 'objet' and sur('../../etc') == 'etc' and '/' not in sur('a/b\\c:d*e?f"g<h>i|j')
    assert len(sur('x' * 300)) <= LONGUEUR_NOM_MAX
    assert sur('(136199) Éris') == '136199_Eris'


def test_console_cp1252_ne_plante_pas():
    """Console Windows (cp1252) : « ≤ », « → », « σ » n'y existent pas ; la CLI remplace au lieu de planter."""
    racine = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONIOENCODING='cp1252', PYTHONUTF8='0', COUPOLE_HOME=os.environ['COUPOLE_HOME'])
    for args in (['--lang', 'fr', 'cosmo', '1'], ['--lang', 'fr', 'ohp', 'estimer', 'Palisana'], ['--lang', 'fr', '--help']):
        r = subprocess.run([sys.executable, '-m', 'coupole'] + args, capture_output=True, cwd=racine, env=env)
        assert r.returncode == 0, (args, r.stderr[-800:])
        assert b'UnicodeEncodeError' not in r.stderr


def test_fuseau_inconnu_repli_nautique():
    from coupole.core.sites import Site
    import datetime as D
    s = Site('mars', 'Olympus', 18.65, -133.8, 21000, 'Mars/Olympus_Mons')
    assert s.fuseau_approche
    z = s.zone()
    assert z.utcoffset(D.datetime(2026, 1, 1)) == D.timedelta(hours=-9)       # -133,8° / 15 = -8,9 → -9 h


@pytest.mark.parametrize('code,attendu', [('French_France.1252', 'fr'), ('English_United States.1252', 'en'),
                                          ('fr_BE@euro', 'fr'), ('C.UTF-8', 'en'), ('en_CA:fr_CA', 'en')])
def test_detection_langue_windows_et_variantes(code, attendu, monkeypatch):
    for v in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv('LANG', code)
    monkeypatch.setattr('locale.setlocale', lambda *a: 'C')
    assert i18n.detecter_langue() == attendu
