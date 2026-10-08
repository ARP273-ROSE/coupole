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
