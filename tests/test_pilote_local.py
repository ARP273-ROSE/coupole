"""Chaîne complète sur un serveur LOCAL (aucune requête publique) : pipeline, doublons de pixels, échec et plantage
d'un processus de conversion, annulation, pause, reprise, réseau coupé, FITS corrompu, journal lisible, nouveautés
entre deux lancements, réorganisation de fichiers déjà convertis, dossier non inscriptible."""
import json
import os
import shutil
import threading
import time

import numpy as np
import pytest

from coupole.core import config
from coupole.core.parallele import Plan
from coupole.modules.ohp import inventaire as INV
from coupole.modules.ohp.conversion import ident
from coupole.modules.ohp.pilote import Etat, Traitement, estimation_temps

from .serveur_local import ServeurLocal

N = 128                                  # côté des images synthétiques (rapide) ; la banque réelle : 1024 et 4096


def fits_synthetique(ra, dec, seed=0, taille=N, dtype='>f4'):
    from astropy.io import fits
    h = fits.Header()
    h['CTYPE1'], h['CTYPE2'] = 'RA---TAN', 'DEC--TAN'
    h['CRVAL1'], h['CRVAL2'] = ra, dec
    h['CRPIX1'], h['CRPIX2'] = taille / 2, taille / 2
    h['CD1_1'], h['CD2_2'], h['CD1_2'], h['CD2_1'] = -0.77 / 3600, 0.77 / 3600, 0.0, 0.0
    h['DATE-OBS'] = '2023-08-15T22:08:42.000'
    h['EXPTIME'] = 20.0
    h['LATITUDE'], h['LONGITUD'] = '05 42 44', '43 55 54'
    a = np.random.default_rng(seed).normal(1000, 30, (taille, taille)).astype(dtype)
    import io
    buf = io.BytesIO()
    fits.PrimaryHDU(a, header=h).writeto(buf)
    return buf.getvalue()


@pytest.fixture(scope='module')
def banque(tmp_path_factory):
    """Six images de (914) Palisana servies localement ; les deux dernières ont des pixels identiques (doublon)."""
    brut, meta = INV.lire(INV.INSTANTANE)
    rangs = [x for x in brut if 'palisana' in x['access_url'].lower()][:6]
    assert len(rangs) == 6
    s = ServeurLocal()
    lignes = []
    for k, x in enumerate(rangs):
        contenu = fits_synthetique(x['s_ra'], x['s_dec'], seed=(k if k < 5 else 4))
        chemin = '/img%d.fits' % k
        s.fichiers[chemin] = contenu
        y = dict(x, access_url=s.url(chemin), access_estsize=len(contenu) / 1024)
        lignes.append(y)
    inv = INV.Inventaire(lignes, dict(meta, source='local'))
    yield s, inv
    s.fermer()


def plan():
    return Plan(telechargements=2, conversions=2, econome=False, raison='x')


def lancer(dest, inv, sel, options=None, evts=None, arret=None, pause=None):
    t = Traitement(str(dest), inv, plan(), dict({'format': 'xisf', 'langue': 'fr', 'debit_octets_s': 50e6},
                                                  **(options or {})),
                   rapporter=(evts.append if evts is not None else None), arret=arret, pause=pause)
    try:
        return t.lancer(sel)
    finally:
        t.fermer()


# ---------------------------------------------------------------- pipeline complet
def test_pipeline_complet_et_journal(tmp_path, banque):
    s, inv = banque
    dest = tmp_path / 'sortie'
    evts = []
    s.requetes.clear()
    b = lancer(dest, inv, inv.images, evts=evts)
    assert b['compte'] == {'ok': 5, 'doublon': 1, 'echec': 0}, b
    assert b['lots'] >= 1 and (dest / 'INDEX_LOTS.csv').exists()
    # une seule requête HTTP par image (plus aucun sondage préalable de la taille)
    for k in range(6):
        assert s.compter('/img%d.fits' % k) == 1, s.requetes
    # progression agrégée : bien moins d'événements « octets » que de blocs de 64 Kio
    assert sum(1 for e in evts if e['type'] == 'octets') <= 6 * 3
    assert any(e['type'] == 'fin' for e in evts)
    # journal lisible, bilingue, horodaté
    j = (dest / '_traitement' / 'JOURNAL.txt').read_text(encoding='utf-8')
    assert 'DÉBUT de session' in j and 'Session START' in j and 'FIN de session' in j
    assert j.count('convertie') >= 5 and 'pixels identiques' in j and 'UTC |' in j
    # rapport de fin
    assert b['images'] == 6 and b['duree'] > 0 and b['echecs'] == []
    # la reprise ne refait rien
    evts2 = []
    b2 = lancer(dest, inv, inv.images, evts=evts2)
    assert b2['compte'] == {'ok': 0, 'doublon': 0, 'echec': 0}
    assert next(e for e in evts2 if e['type'] == 'debut')['deja'] == 6
    # fichiers rangés, jamais de .tmp ni de .part qui traîne
    restes = [p for p in dest.rglob('*') if p.suffix in ('.tmp', '.part')]
    assert not restes
    assert len(list(dest.rglob('*.xisf'))) == 5


def test_doublon_de_pixels_garde_a_la_demande(tmp_path, banque):
    s, inv = banque
    b = lancer(tmp_path / 'g', inv, inv.images, {'garder_doublons': True})
    assert b['compte'] == {'ok': 6, 'doublon': 0, 'echec': 0}
    e = Etat(str(tmp_path / 'g' / '_traitement' / 'etat.sqlite'))
    infos = dict(e.ok())
    e.fermer()
    assert sum(1 for i in infos.values() if i.get('doublon_de')) == 1       # signalé, pas écarté


# ---------------------------------------------------------------- pannes d'un processus de conversion
def test_exception_dans_un_processus(tmp_path, banque):
    s, inv = banque
    evts = []
    b = lancer(tmp_path / 'e', inv, inv.images[:3], {'_simuler': 'exception'}, evts=evts)
    assert b['compte']['echec'] == 3 and b['compte']['ok'] == 0
    assert all('simulated' in e['erreur'] for e in evts if e['type'] == 'echec')
    assert len(b['echecs']) == 3


def test_plantage_dun_processus_ne_tue_pas_le_pilote(tmp_path, banque):
    """Un processus de conversion qui meurt (os._exit) : image en échec, bassin reconstruit, le pilote survit."""
    s, inv = banque
    b = lancer(tmp_path / 'p', inv, inv.images[:2], {'_simuler': 'plantage'})
    assert b['compte']['echec'] >= 1 and b['compte']['ok'] == 0
    j = (tmp_path / 'p' / '_traitement' / 'JOURNAL.txt').read_text(encoding='utf-8')
    assert 'processus de conversion perdu' in j or 'ÉCHEC' in j


# ---------------------------------------------------------------- annulation, pause, reprise
def test_annulation_rapide_puis_reprise(tmp_path, banque):
    s, inv = banque
    s.lenteur = 0.05                                 # 65 Kio toutes les 50 ms : ~0,1 s par image de 64 Kio
    arret = threading.Event()
    evts = []

    def rapporter(ev):
        evts.append(ev)
        if ev['type'] == 'telecharge' and not arret.is_set():
            arret.set()                              # dès la première image téléchargée : on annule
    t0 = time.monotonic()
    t = Traitement(str(tmp_path / 'a'), inv, plan(), {'format': 'xisf', 'langue': 'fr'}, rapporter=rapporter, arret=arret)
    try:
        b = t.lancer(inv.images)
    finally:
        t.fermer()
        s.lenteur = 0.0
    assert b['annule'] and time.monotonic() - t0 < 20
    assert b['compte']['ok'] + b['compte']['doublon'] < 6
    j = (tmp_path / 'a' / '_traitement' / 'JOURNAL.txt').read_text(encoding='utf-8')
    assert 'interrompu' in j
    # reprise : tout se termine, rien n'est refait
    b2 = lancer(tmp_path / 'a', inv, inv.images)
    e = Etat(str(tmp_path / 'a' / '_traitement' / 'etat.sqlite'))
    st = e.statuts()
    e.fermer()
    assert sorted(st.values()).count('ok') == 5 and not b2['annule']
    j = (tmp_path / 'a' / '_traitement' / 'JOURNAL.txt').read_text(encoding='utf-8')
    assert 'reprise' in j


def test_pause_suspend_puis_reprend(tmp_path, banque):
    s, inv = banque
    pause = threading.Event()
    pause.set()
    evts = []
    arret = threading.Event()
    res = {}

    def corps():
        res['b'] = lancer(tmp_path / 'pz', inv, inv.images[:3], evts=evts, arret=arret, pause=pause)
    fil = threading.Thread(target=corps, daemon=True)
    fil.start()
    # le pilote signale la pause dès son premier tour de boucle ; sur un serveur de CI lent, son démarrage (base
    # d'état, journal) peut dépasser la seconde : on attend l'événement au lieu d'un délai fixe
    t0 = time.monotonic()
    while not any(e['type'] == 'pause' and e['actif'] for e in evts) and time.monotonic() - t0 < 20:
        time.sleep(0.05)
    assert any(e['type'] == 'pause' and e['actif'] for e in evts)
    time.sleep(1.0)
    assert not any(e['type'] in ('image', 'telecharge') for e in evts)        # en pause : rien n'avance
    pause.clear()
    fil.join(60)
    assert not fil.is_alive() and res['b']['compte']['ok'] == 3


# ---------------------------------------------------------------- réseau et fichiers abîmés
def test_reseau_coupe_puis_refus(tmp_path, banque, monkeypatch):
    s, inv = banque
    monkeypatch.setattr('time.sleep', lambda *_: None)
    s.pannes['/img1.fits'] = 'coupure_une_fois'                 # coupure au milieu : reprise par Range
    s.pannes['/img2.fits'] = 'refus'                            # serveur en erreur : échec propre après essais
    try:
        from coupole.core import reseau
        orig = reseau.telecharger

        def rapide(*a, **k):
            k['essais'] = 2
            return orig(*a, **k)
        monkeypatch.setattr(reseau, 'telecharger', rapide)
        b = lancer(tmp_path / 'r', inv, inv.images[:3])
    finally:
        s.pannes.clear()
    assert b['compte']['ok'] == 2 and b['compte']['echec'] == 1
    assert any('503' in e['erreur'] or 'download' in e['erreur'] for e in b['echecs'])
    # la reprise par Range a bien eu lieu : deux requêtes pour img1, la seconde avec un Range non nul
    rg = [r for p, r in s.requetes if p == '/img1.fits']
    assert len(rg) >= 2 and any(r and not r.endswith('=0-') for r in rg)


def test_fits_corrompu(tmp_path, banque):
    s, inv = banque
    bon = s.fichiers['/img0.fits']
    s.fichiers['/corrompu.fits'] = b'SIMPLE  =                    T' + bytes(len(bon) - 30)   # en-tête sans END
    x = dict(inv.images[0], access_url=s.url('/corrompu.fits'))
    try:
        b = lancer(tmp_path / 'c', inv, [x])
    finally:
        del s.fichiers['/corrompu.fits']
    assert b['compte']['echec'] == 1 and b['compte']['ok'] == 0
    assert not list((tmp_path / 'c').rglob('*.xisf'))


def test_dossier_de_sortie_non_inscriptible(tmp_path, banque):
    s, inv = banque
    fichier = tmp_path / 'pas_un_dossier'
    fichier.write_text('x')
    with pytest.raises(OSError):
        Traitement(str(fichier), inv, plan(), {'format': 'xisf'})


# ---------------------------------------------------------------- nouveautés entre deux lancements
def test_nouveautes_entre_deux_lancements(tmp_path, banque, monkeypatch):
    s, inv = banque
    monkeypatch.setattr(INV, 'chemin_historique', lambda: tmp_path / 'h.json')
    brut = [dict(x) for x in inv.images]
    anciennes, nouvelles = brut[:4], brut[4:]
    INV.noter_vus(anciennes, '2026-10-01')                         # premier inventaire connu
    inv1 = INV.Inventaire(anciennes, inv.meta)
    dest = tmp_path / 'n'
    lancer(dest, inv1, inv1.images)                                # copie locale des 4 premières
    n0 = INV.nouveautes_locales(inv1, dest)
    assert n0['copie'] and n0['images'] == []
    INV.noter_vus(brut, '2026-10-20')                              # la base a grandi de 2 images
    inv2 = INV.Inventaire(brut, inv.meta)
    n = INV.nouveautes_locales(inv2, dest)
    assert len(n['images']) == 2 and n['depuis'] == '2026-10-01' and n['octets'] > 0
    assert n['objets'] == ['(914) Palisana']
    assert not INV.nouveautes_locales(inv2, tmp_path / 'inexistant')['copie']
    lancer(dest, inv2, n['images'])                                # « télécharger maintenant »
    INV.marquer_reference('2026-10-20')
    inv3 = INV.Inventaire(brut, inv.meta)
    assert INV.nouveautes_locales(inv3, dest)['images'] == []


def test_verification_automatique_respecte_la_frequence(tmp_path, banque, monkeypatch):
    s, inv = banque
    r = config.reglages()
    appels = []
    monkeypatch.setattr(INV.Inventaire, 'charger', classmethod(lambda cls, raf=False: appels.append(raf) or inv))
    r['ohp_verifier_nouveautes'] = False
    assert INV.verifier_nouveautes(str(tmp_path)) is None and appels == []
    r['ohp_verifier_nouveautes'] = True
    r['ohp_derniere_verification'] = ''
    assert INV.verifier_nouveautes(str(tmp_path)) is not None and appels == [True]
    assert INV.verifier_nouveautes(str(tmp_path)) is None and len(appels) == 1          # trop tôt : pas de requête
    assert INV.verifier_nouveautes(str(tmp_path), forcer=True) is not None and len(appels) == 2


# ---------------------------------------------------------------- réorganiser
def test_reorganiser_des_fichiers_deplaces(tmp_path, banque):
    s, inv = banque
    dest = tmp_path / 'ro'
    lancer(dest, inv, inv.images[:3])
    fichiers = sorted(dest.rglob('*.xisf'))
    assert len(fichiers) == 3
    ailleurs = tmp_path / 'vrac'
    ailleurs.mkdir()
    for k, f in enumerate(fichiers):
        shutil.move(str(f), str(ailleurs / ('ancien_%d.xisf' % k)))
    (ailleurs / 'etranger.xisf').write_bytes(b'XISF0100' + bytes(8))          # pas un fichier de Coupole
    (ailleurs / 'note.txt').write_text('x')
    # un fichier étranger occupe déjà le nom voulu d'une image : il ne doit jamais être écrasé
    occupe = fichiers[0]
    occupe.parent.mkdir(parents=True, exist_ok=True)
    occupe.write_bytes(b'pas a moi')
    t = Traitement(str(dest), inv, plan(), {'format': 'xisf', 'langue': 'fr'})
    try:
        r = t.reorganiser(str(ailleurs))
    finally:
        t.fermer()
    assert r['ranges'] == 3 and r['lots'] >= 1
    assert {raison for _, raison in r['ignores']} <= {'illisible', 'pas_coupole'}
    assert occupe.read_bytes() == b'pas a moi'                                 # rien d'écrasé
    assert len(list(dest.rglob('*.xisf'))) == 4 and not list(ailleurs.rglob('ancien_*.xisf'))
    assert (ailleurs / 'etranger.xisf').exists()                               # l'étranger reste où il est
    j = (dest / '_traitement' / 'JOURNAL.txt').read_text(encoding='utf-8')
    assert 'réorganisation' in j and 'conflit de nom' in j and 'name conflict' in j


# ---------------------------------------------------------------- place juste : fenêtre réduite, pas de refus
def test_fenetre_reduite_a_la_place_libre():
    from coupole.modules.ohp.selection import fenetre_adaptee, fenetre_nominale, place_necessaire
    est = {'plus_gros': 10e6, 'octets_sortie': 30e6}
    assert fenetre_nominale(2, 2) == 6
    assert fenetre_adaptee(est, 2, 2, None) == 6                      # place inconnue : nominale
    assert fenetre_adaptee(est, 2, 2, 1e12) == 6                      # large : nominale
    assert fenetre_adaptee(est, 2, 2, 30e6 + 6 * 20e6) == 6           # exactement la réserve nominale
    assert fenetre_adaptee(est, 2, 2, 30e6 + 4 * 20e6) == 4           # juste : réduite à ce qui tient
    assert fenetre_adaptee(est, 2, 2, 30e6 + 1 * 20e6) == 3           # jamais sous conversions + 1
    assert fenetre_adaptee(est, 2, 2, 0.0) == 3
    assert fenetre_adaptee({'plus_gros': 0, 'octets_sortie': 0}, 2, 2, 0.0) == 6   # rien à télécharger : nominale
    # la place « nécessaire » suit la fenêtre réduite : ce qui était refusé (12 FITS de réserve) passe avec 4
    assert place_necessaire(est, 2, 2) == 30e6 + 6 * 20e6
    libre = 30e6 + 4 * 20e6 + 1
    assert place_necessaire(est, 2, 2, libre) == 30e6 + 4 * 20e6 and libre >= place_necessaire(est, 2, 2, libre)


def test_pilote_reduit_la_fenetre_quand_la_place_est_juste(tmp_path, banque, monkeypatch):
    """Place libre simulée juste au-dessus de la sortie : fenêtre 3 au lieu de 6, événement + ligne de journal,
    et les six images sont quand même toutes traitées."""
    s, inv = banque
    from coupole.core import machine
    from coupole.modules.ohp.selection import estimer
    est = estimer(inv.images, 'xisf')
    libre_simulee = est['octets_sortie'] + 2 * est['plus_gros'] * 1.5          # de quoi tenir 1 FITS, pas plus
    monkeypatch.setattr(machine, 'disque_libre_go', lambda chemin: libre_simulee / 1e9)
    evts = []
    dest = tmp_path / 'juste'
    bilan = lancer(dest, inv, inv.images, evts=evts)
    fen = [e for e in evts if e['type'] == 'fenetre']
    assert len(fen) == 1 and fen[0]['fenetre'] == 3 and fen[0]['nominale'] == 6
    assert bilan['compte']['ok'] + bilan['compte']['doublon'] == 6 and bilan['compte']['echec'] == 0
    journal = (dest / '_traitement' / 'JOURNAL.txt').read_text(encoding='utf-8')
    assert 'réduite à 3' in journal and 'reduced to 3' in journal


def test_pilote_garde_la_fenetre_nominale_quand_la_place_est_large(tmp_path, banque):
    s, inv = banque
    evts = []
    lancer(tmp_path / 'large', inv, inv.images, evts=evts)
    assert not [e for e in evts if e['type'] == 'fenetre']


# ---------------------------------------------------------------- estimation « tout »
def test_estimation_du_temps(banque):
    s, inv = banque
    from coupole.modules.ohp.selection import estimer
    est = estimer(inv.images, 'xisf')
    assert est['images'] == 6
    # 78 Go à 8 Mo/s : 9 750 s = 2 h 42 min 30 s (SageMath : 78e9/8e6 = 9750)
    assert abs(estimation_temps(78e9, 8e6) - 9750.0) < 1e-6


def test_cli_tout_et_nouveautes_sans_reseau(capsys, monkeypatch, tmp_path, banque):
    s, inv = banque
    from coupole import cli
    from coupole.modules.ohp import cli as ohp_cli
    monkeypatch.setattr(ohp_cli, '_inventaire', lambda rafraichir=False: inv)
    code = cli.main(['--lang', 'fr', 'ohp', 'tout', '--dest', str(tmp_path / 't')])
    out = capsys.readouterr()
    assert code == 4 and 'Toute la banque' in out.out and '--oui' in out.err
    code = cli.main(['--lang', 'en', 'ohp', 'nouveautes', '--dest', str(tmp_path / 'vide')])
    out = capsys.readouterr()
    assert code == 1 and 'No local copy' in out.out
