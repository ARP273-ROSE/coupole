"""Détection de la machine et parallélisme adaptatif."""
import time

from coupole.core import calcul, machine, parallele
from coupole.core.machine import Machine


def m(coeurs=8, ram_tot=16384, ram_dispo=12000):
    return Machine('Linux', '6', 'x86_64', 'cpu', coeurs, coeurs * 2, ram_tot, ram_dispo, '3.12', [])


def test_detection_rend_des_valeurs_plausibles():
    d = machine.detecter(rafraichir=True)
    assert d.coeurs_physiques >= 1 and d.coeurs_logiques >= d.coeurs_physiques
    assert d.memoire_totale_mo > 100 and 0 < d.memoire_disponible_mo <= d.memoire_totale_mo
    assert d.architecture and d.systeme
    assert isinstance(d.cartes, list)
    assert machine.disque_libre_go('/chemin/qui/n/existe/pas/encore') > 0


def test_gros_ordinateur_limite_par_les_coeurs():
    p = parallele.planifier(m(coeurs=8, ram_dispo=64000))
    assert p.conversions == 7 and p.telechargements == 3 and not p.econome
    assert p.raison == 'parallele_raison_coeurs'


def test_memoire_bornee():
    p = parallele.planifier(m(coeurs=16, ram_dispo=3000))
    assert p.conversions == max(1, int(3000 * parallele.PART_MEMOIRE // parallele.MEMOIRE_PAR_CONVERSION_MO))
    assert p.raison == 'parallele_raison_memoire'


def test_petite_machine_mode_econome():
    for mm in (m(coeurs=2), m(ram_tot=3000, ram_dispo=1500)):
        p = parallele.planifier(mm)
        assert p.econome and p.conversions == 1 and p.telechargements == 2


def test_bridage_manuel_et_politesse_reseau():
    p = parallele.planifier(m(coeurs=32), telechargements=10, conversions=2)
    assert p.telechargements == parallele.TELECHARGEMENTS_MAX == 4 and p.conversions == 2
    assert parallele.planifier(m(coeurs=32), econome=True).econome
    assert not parallele.planifier(m(coeurs=2), econome=False).econome


def test_api_gpu_repli_numpy():
    import numpy as np
    assert calcul.tableaux(preferer_gpu=False) is np
    r = calcul.resume_gpu()
    assert set(r) == {'cartes', 'nvidia', 'cupy'}
    assert calcul.tableaux(preferer_gpu=True) is np or r['cupy']
    assert (calcul.vers_numpy(np.arange(3)) == np.arange(3)).all()


def test_limiteur_de_debit():
    from coupole.core.reseau import LimiteurDebit
    lim = LimiteurDebit(200_000)
    t0 = time.monotonic()
    for _ in range(10):
        lim.prendre(50_000)                 # 500 ko à 200 ko/s : ≈ 1,5 s après le premier seau
    dt = time.monotonic() - t0
    assert 1.2 < dt < 3.0


# ---------------------------------------------------------------- 0.2.1 : bibliothèques facultatives
def test_bibliotheques_facultatives_listees():
    from coupole.core import bibliotheques
    from coupole.modules.machine import cli
    liste = bibliotheques.facultatives()
    noms = [b['module'] for b in liste]
    assert noms[:2] == ['sep', 'reproject'] and 'cupy' in noms
    presentes, absentes = bibliotheques.resume(liste)
    # installées par l'extra « test » : présentes, avec leur version
    assert 'sep ' in presentes and 'reproject ' in presentes
    d = cli.rapport()
    lignes = dict(cli.lignes(d))
    assert 'reproject' in lignes['Bibliothèques facultatives']
    assert 'Bibliothèques facultatives' in cli.infobulles()


def test_essai_des_bibliotheques_embarquees():
    from coupole.core import bibliotheques
    v = bibliotheques.essai_embarquees()
    assert set(v) == set(bibliotheques.EMBARQUEES) and all(v.values())


def test_a_propos_donne_les_bibliotheques():
    from coupole.gui.dialogues import texte_configuration
    assert 'Bibliothèques facultatives : sep ' in texte_configuration()


def test_paquets_embarquent_reproject_et_sep():
    """requirements.txt (paquets autonomes) et contrôle des paquets en CI (kit.json)."""
    import json
    from pathlib import Path
    racine = Path(__file__).resolve().parents[1]
    req = (racine / 'requirements.txt').read_text(encoding='utf-8')
    for nom in ('sep', 'reproject', 'psutil', 'lxml'):
        assert any(l.startswith(nom) for l in req.splitlines()), nom
    kit = json.loads((racine / 'kit.json').read_text(encoding='utf-8'))
    assert {'sep', 'reproject', 'astropy_healpix', 'psutil'} <= set(kit['verification_import'])
    assert kit['essai_embarquees'] == 'coupole.core.bibliotheques:essai_embarquees'
    wf = (racine / '.github' / 'workflows' / 'release.yml').read_text(encoding='utf-8')
    assert wf.count('essai_embarquees') >= 3
