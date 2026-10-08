"""Fiche en ligne (SIMBAD, Sesame, JPL SBDB) : réponses simulées, cache daté, repli hors ligne, politesse ;
puis un essai réel limité à quatre objets (COUPOLE_TEST_RESEAU=1)."""
import datetime as D
import json
import os
import time

import pytest

from coupole.core import config, enligne, reseau, simbad

SIMBAD_M27 = """::script::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

format object f1 "..."
query id M27

::console:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

C.D.S.  -  SIMBAD4 rel 1.8
simbatch done

::data::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

M  27\tPlanetaryNeb\tPlanetary Nebula\t299.9015132708700\t+22.7211977943200\t19 59 36.3631850088\t+22 43 16.312059552\t2.57 \t0.0373\tv\t-42.0\t-0.000140\t5\tE\tB=13.749,V=14.089,R=14.247,G=14.037333,\t 6.7 \t 6.7 \t  90\tDAO.6\t~\tM  27,BD+22  3878,NAME Dumbbell Nebula,NGC  6853,\t    0.242   kpc |  -0.048      +0.048   |        |2010ApJ...714.1096S
"""

SIMBAD_NGC6888 = SIMBAD_M27.split('::data:')[0] + """::data::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

HD 192163\tWolfRayet*\tWolf-Rayet\t303.0272578656099\t+38.3549400502800\t20 12 06.54\t+38 21 17.78\t0.5772 \t0.016\tv\t-100.00\t-0.000334\t~\tD\tV=7.50,\t    ~\t    ~\t   ~\tWN6(h)-s\t~\tNAME Crescent Nebula,HD 192163,NGC  6888,WR 136,\t 1732.5   pc  | -48.025     +48.025   |paral   |2020yCat.1350....0G
"""

SIMBAD_RIEN = """::script::::::

format object f1 "%IDLIST(1)"
query id zzzz

::error:::::::::::::::

[4] 'zzzz': No known catalog could be found
"""

SBDB_JUNO = json.dumps({
    'object': {'fullname': '3 Juno (A804 RA)', 'des': '3', 'spkid': '20000003', 'kind': 'an', 'neo': False,
               'pha': False, 'orbit_class': {'code': 'MBA', 'name': 'Main-belt Asteroid'}},
    'orbit': {'epoch': '2461200.5', 'elements': [
        {'name': 'e', 'value': '0.2557', 'units': None}, {'name': 'a', 'value': '2.671', 'units': 'au'},
        {'name': 'i', 'value': '12.99', 'units': 'deg'}, {'name': 'per', 'value': '1594.4', 'units': 'd'}]},
    'phys_par': [{'name': 'diameter', 'value': '246.596', 'units': 'km'}, {'name': 'albedo', 'value': '0.214'},
                 {'name': 'rot_per', 'value': '7.21', 'units': 'h'}, {'name': 'H', 'value': '5.19'}]})

SBDB_LISTE = json.dumps({'code': '300', 'list': [{'pdes': '1', 'name': 'Ceres'}, {'pdes': '2', 'name': 'Pallas'}]})


@pytest.fixture
def reseau_simule(monkeypatch):
    """Remplace le réseau : `reponses` associe un fragment d'URL à un texte (ou à une exception)."""
    appels = []
    reponses = {}

    def lire(url, delai=8, max_octets=2_000_000, accepter=()):
        appels.append(url)
        for frag, rep in reponses.items():
            if frag in url:
                if isinstance(rep, Exception):
                    raise rep
                return rep
        raise reseau.ServiceInjoignable('pas de réponse simulée pour ' + url)
    monkeypatch.setattr(reseau, 'lire_texte', lire)
    monkeypatch.setattr(enligne, 'INTERVALLE_MIN', 0.0)
    enligne.vider_cache()
    config.reglages()['services_en_ligne'] = True
    yield reponses, appels
    enligne.vider_cache()


def test_fiche_simbad_et_cache(reseau_simule):
    reponses, appels = reseau_simule
    reponses['sim-script'] = SIMBAD_M27
    r = enligne.fiche_objet('M27', 'pn')
    f = r['fiche']
    assert r['etat'] == 'ok' and not r['cache'] and f['nom'] == 'M 27' and f['otype'] == 'PlanetaryNeb'
    assert f['plx'] == 2.57 and f['flux']['V'] == 14.089 and f['dim_x'] == 6.7 and f['z'] == -0.00014
    assert f['distance']['valeur'] == 0.242 and f['distance']['unite'] == 'kpc'
    assert 'NAME Dumbbell Nebula' in f['ids'] and f['liens']['simbad'].endswith('Ident=M%2027')
    assert 'aladin' in f['liens'] and 'ned' not in f['liens']           # nébuleuse : pas de lien NED
    assert len(appels) == 1                                            # une seule requête
    D.datetime.fromisoformat(r['date'])
    r2 = enligne.fiche_objet('M27', 'pn')
    assert r2['cache'] and len(appels) == 1                           # depuis le cache disque daté
    assert json.loads(enligne.chemin_cache().read_text(encoding='utf-8'))


def test_identifiant_retenu_different(reseau_simule):
    reponses, _ = reseau_simule
    reponses['sim-script'] = SIMBAD_NGC6888
    r = enligne.fiche_objet('NGC 6888', 'neb')
    assert r['fiche']['nom'] == 'HD 192163' and r['fiche']['distance']['methode'] == 'paral'


def test_sbdb_petit_corps(reseau_simule):
    reponses, appels = reseau_simule
    reponses['sbdb.api'] = SBDB_JUNO
    r = enligne.fiche_objet('(3) Juno', 'ast')
    f = r['fiche']
    assert r['etat'] == 'ok' and f['service'] == 'sbdb' and f['classe_code'] == 'MBA'
    assert f['elements']['a'] == (2.671, 'au') and f['phys']['diameter'][0] == 246.596
    assert 'sstr=3&' in appels[0] and 'sim-script' not in ''.join(appels)
    assert f['liens']['sbdb'].endswith('sstr=20000003')


def test_sbdb_ambigu(reseau_simule):
    reponses, _ = reseau_simule
    reponses['sbdb.api'] = SBDB_LISTE
    r = enligne.fiche_objet('C', 'ast')
    assert r['fiche']['ambigu'] and len(r['fiche']['candidats']) == 2


def test_introuvable_puis_sesame(reseau_simule):
    reponses, appels = reseau_simule
    reponses['sim-script'] = SIMBAD_RIEN
    reponses['sesame'] = ('<?xml version="1.0"?><Sesame><Target><Resolver name="N=NED"><oname>FOO 1</oname>'
                          '<otype>G</otype><jpos>12 00 00.0 +10 00 00</jpos><jradeg>180.0</jradeg><jdedeg>10.0</jdedeg>'
                          '<z><v>0.0123</v></z></Resolver></Target></Sesame>')
    r = enligne.fiche_objet('Foo 1', 'gal')
    assert r['etat'] == 'ok' and r['fiche']['service'] == 'sesame' and r['fiche']['z'] == 0.0123
    assert 'ned' in r['fiche']['liens']
    reponses['sesame'] = '<?xml version="1.0"?><Sesame><Target></Target></Sesame>'
    r = enligne.fiche_objet('Bar 2', 'gal')
    assert r['etat'] == 'introuvable'


def test_hors_ligne_repli_propre(reseau_simule):
    reponses, _ = reseau_simule
    reponses['sim-script'] = reseau.ServiceInjoignable('URLError: [Errno -3] Temporary failure in name resolution')
    r = enligne.fiche_objet('M57', 'pn')
    assert r['etat'] == 'hors_ligne' and 'name resolution' in r['erreur'] and r['fiche'] is None
    # une fiche ancienne en cache : affichée, marquée « périmée », avec sa date
    reponses['sim-script'] = SIMBAD_M27
    enligne.fiche_objet('M27', 'pn')
    c = json.loads(enligne.chemin_cache().read_text(encoding='utf-8'))
    for e in c.values():
        e['date'] = '2020-01-01T00:00:00+00:00'
        e['resultat']['date'] = e['date']
    enligne.chemin_cache().write_text(json.dumps(c), encoding='utf-8')
    enligne._cache = None
    reponses['sim-script'] = reseau.ServiceInjoignable('timed out')
    r = enligne.fiche_objet('M27', 'pn')
    assert r['etat'] == 'ok' and r['cache'] and r['perime'] and r['date'].startswith('2020')


def test_services_desactives(reseau_simule):
    _, appels = reseau_simule
    config.reglages()['services_en_ligne'] = False
    try:
        assert enligne.fiche_objet('M31', 'gal')['etat'] == 'desactive'
        assert enligne.redshift('M31')['etat'] == 'desactive'
        assert appels == []
    finally:
        config.reglages()['services_en_ligne'] = True


def test_planetes_et_neocp_sans_requete(reseau_simule):
    _, appels = reseau_simule
    assert enligne.fiche_objet('Saturne', 'pla')['raison'] == 'fiche_planete'
    assert enligne.fiche_objet('A117QUQ', 'neocp')['raison'] == 'fiche_neocp'
    assert appels == []


def test_politesse_intervalle(reseau_simule, monkeypatch):
    reponses, _ = reseau_simule
    reponses['sbdb.api'] = SBDB_JUNO
    monkeypatch.setattr(enligne, 'INTERVALLE_MIN', 0.3)
    t0 = time.monotonic()
    enligne.fiche_objet('(3) Juno', 'ast')
    enligne.fiche_objet('(4) Vesta', 'ast')
    assert time.monotonic() - t0 >= 0.29


def test_redshift_par_nom(reseau_simule):
    reponses, _ = reseau_simule
    reponses['sim-script'] = ('::data::::::::\n\n3C 273\tBL Lac\t0.15756751\t187.27791535\t+02.05238857\t'
                              '3C 273,QSO B1226+023,\n')
    r = enligne.redshift('3c273')
    assert r['etat'] == 'ok' and r['nom'] == '3C 273' and abs(r['z'] - 0.1575675) < 1e-6


def test_designations_petits_corps():
    assert enligne.designation_sbdb('(3) Juno') == '3'
    assert enligne.designation_sbdb('(134340) Pluton') == '134340'
    assert enligne.designation_sbdb('29P/Schwassmann-Wachmann') == '29P'
    assert enligne.designation_sbdb('2013 DD1') == '2013 DD1'


def test_adresses_dans_les_sources():
    from coupole.core import sources
    for cle in ('simbad.base', 'simbad.page', 'aladin.page', 'ned.page', 'sbdb.page', 'resolution.sbdb',
                'resolution.sesame'):
        v = sources.valeur(cle)
        assert v and sources._domaine_ok(v), cle
    assert sources.valider(json.loads(sources.FICHIER_DEFAUT.read_text(encoding='utf-8'))) == []


def test_html_fiche_bilingue(reseau_simule, langue):
    pytest.importorskip('PyQt6')
    from coupole.gui.fiche import html_fiche
    reponses, _ = reseau_simule
    reponses['sim-script'] = SIMBAD_NGC6888
    r = enligne.fiche_objet('NGC 6888', 'neb')
    langue('fr')
    fr = html_fiche(r)
    langue('en')
    en = html_fiche(r)
    assert 'Parallaxe' in fr and 'Parallax' in en and fr != en
    assert 'HD 192163' in fr and 'NGC 6888' in fr          # le nom demandé et l'identifiant retenu
    assert '1732' in fr.replace(' ', '')


@pytest.mark.skipif(not os.environ.get('COUPOLE_TEST_RESEAU'), reason='essai réseau : COUPOLE_TEST_RESEAU=1')
def test_essai_reel_quatre_objets():
    """Vrais services, quatre objets seulement (politesse) : M27, NGC 6888, (3) Juno, Pluton."""
    enligne.vider_cache()
    config.reglages()['services_en_ligne'] = True
    m27 = enligne.fiche_objet('M27', 'pn')
    assert m27['etat'] == 'ok' and m27['fiche']['nom'] == 'M 27' and m27['fiche']['dim_x'] > 5
    n6888 = enligne.fiche_objet('NGC 6888', 'neb')
    assert n6888['etat'] == 'ok' and ('NGC 6888' in n6888['fiche']['ids'] or n6888['fiche']['nom'] == 'NGC 6888')
    juno = enligne.fiche_objet('(3) Juno', 'ast')
    assert juno['etat'] == 'ok' and juno['fiche']['classe_code'] == 'MBA'
    assert 2.6 < juno['fiche']['elements']['a'][0] < 2.7 and 200 < juno['fiche']['phys']['diameter'][0] < 300
    pluton = enligne.fiche_objet('(134340) Pluton', 'tno', '134340')
    assert pluton['etat'] == 'ok' and pluton['fiche']['classe_code'] == 'TNO'
    assert 39 < pluton['fiche']['elements']['a'][0] < 40
