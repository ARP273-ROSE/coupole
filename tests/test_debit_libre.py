"""0.2.3 : plus de plafond de débit par défaut.

Aucun plafond par défaut (0 = illimité partout) ; le plafond reste réglable ; une installation qui avait gardé
l'ancien défaut (8 Mo/s) passe à illimité, une valeur choisie est conservée ; sans plafond, la durée est estimée
d'après le débit mesuré lors des téléchargements précédents.
"""
import json
import threading
import time

import pytest


def test_defauts_sans_plafond():
    from coupole.core import config
    assert config.DEFAUTS['debit_max_mo_s'] == 0
    assert config.DEFAUTS['archives_debit_mo_s'] == 0


@pytest.mark.parametrize('valeur', [0, 0.0, None, -3])
def test_limiteur_zero_ou_none_ne_bride_pas(valeur):
    from coupole.core.reseau import LimiteurDebit
    lim = LimiteurDebit(valeur)
    assert not lim.plafonne
    t0 = time.monotonic()
    for _ in range(200):
        lim.prendre(1 << 20)                 # 200 Mo « reçus » : instantané sans plafond
    assert time.monotonic() - t0 < 0.5
    assert lim.octets_total == 200 << 20


def test_limiteur_mesure_le_debit_obtenu():
    from coupole.core import reseau
    lim = reseau.LimiteurDebit(0)
    assert lim.mesure() == 0                 # rien reçu
    lim.prendre(1_000_000)
    lim._t_premier -= 4.0                    # 5 Mo sur 4 s
    lim.prendre(4_000_000)
    assert abs(lim.mesure() - 1.25e6) < 0.05e6
    petit = reseau.LimiteurDebit(0)
    petit.prendre(10_000)
    assert petit.mesure() == 0               # trop peu de données : pas de mesure


def test_limiteur_plafond_leve_en_cours():
    from coupole.core.reseau import LimiteurDebit
    lim = LimiteurDebit(100_000)
    lim.prendre(100_000)
    fini = threading.Event()

    def prendre():
        lim.prendre(400_000)                 # ≈ 4 s au plafond
        fini.set()

    threading.Thread(target=prendre, daemon=True).start()
    time.sleep(0.2)
    lim.regler(0)
    assert fini.wait(1.5)


def _reglages_ecrits(tmp_path, contenu):
    from coupole.core import config
    p = tmp_path / 'reglages.json'
    p.write_text(json.dumps(contenu), encoding='utf-8')
    return config.Reglages(p), p


def test_migration_ancien_defaut_vers_illimite(tmp_path):
    r, p = _reglages_ecrits(tmp_path, {'id_installation': 'abc', 'debit_max_mo_s': 8.0, 'archives_debit_mo_s': 8})
    assert r['debit_max_mo_s'] == 0 and r['archives_debit_mo_s'] == 0
    disque = json.loads(p.read_text(encoding='utf-8'))
    assert disque['debit_max_mo_s'] == 0 and disque['debit_sans_plafond_023'] is True


def test_migration_conserve_un_choix_de_l_utilisateur(tmp_path):
    r, _ = _reglages_ecrits(tmp_path, {'id_installation': 'abc', 'debit_max_mo_s': 5.5, 'archives_debit_mo_s': 12.0})
    assert r['debit_max_mo_s'] == 5.5 and r['archives_debit_mo_s'] == 12.0


def test_migration_une_seule_fois(tmp_path):
    """Un plafond de 8 Mo/s choisi APRÈS la migration reste en place."""
    r, p = _reglages_ecrits(tmp_path, {'id_installation': 'abc', 'debit_max_mo_s': 8.0,
                                       'debit_sans_plafond_023': True})
    assert r['debit_max_mo_s'] == 8.0
    from coupole.core import config
    assert config.Reglages(p)['debit_max_mo_s'] == 8.0


def test_estimation_plafond_mesure_inconnu():
    from coupole.core import config, reseau
    r = config.reglages()
    ancien = r.get('debit_mesure_mo_s')
    try:
        r['debit_mesure_mo_s'] = 0.0
        assert reseau.debit_estime(0) == (0.0, 'inconnu')
        assert reseau.debit_estime(8e6) == (8e6, 'plafond')
        r['debit_mesure_mo_s'] = 30.0
        assert reseau.debit_estime(0) == (30e6, 'mesure')
        assert reseau.debit_estime(8e6) == (8e6, 'plafond')        # plafond plus bas que le réseau
        r['debit_mesure_mo_s'] = 3.0
        assert reseau.debit_estime(8e6) == (3e6, 'mesure')         # réseau plus lent que le plafond
    finally:
        r['debit_mesure_mo_s'] = ancien or 0.0


def test_memoriser_seulement_un_debit_qui_dit_quelque_chose_du_reseau():
    from coupole.core import config, reseau
    r = config.reglages()
    ancien = r.get('debit_mesure_mo_s')
    try:
        r['debit_mesure_mo_s'] = 0.0
        lim = reseau.LimiteurDebit(10e6)
        lim.prendre(1_000_000)
        lim._t_premier -= 4.0
        lim.octets_total = 40_000_000        # 10 Mo/s au plafond de 10 : on ne mesure que le plafond
        assert reseau.memoriser_debit(lim) == 0 and r['debit_mesure_mo_s'] == 0
        libre = reseau.LimiteurDebit(0)
        libre.prendre(1_000_000)
        libre._t_premier -= 2.0
        libre.octets_total = 50_000_000      # 25 Mo/s sans plafond
        assert reseau.memoriser_debit(libre) > 0 and abs(r['debit_mesure_mo_s'] - 25.0) < 0.1
    finally:
        r['debit_mesure_mo_s'] = ancien or 0.0


def test_phrase_de_duree_ohp():
    from coupole.core import config
    from coupole.modules.ohp.gui_sans_qt import duree_lisible
    from coupole.modules.ohp.pilote import phrase_duree
    r = config.reglages()
    ancien = r.get('debit_mesure_mo_s')
    try:
        r['debit_mesure_mo_s'] = 0.0
        from coupole.core.i18n import decimal                 # « 8,0 » en français, « 8.0 » en anglais (0.7.0)
        assert decimal(8.0) in phrase_duree(78e9, 8e6, duree_lisible)
        sans = phrase_duree(78e9, 0, duree_lisible)
        assert '{' not in sans and sans
        r['debit_mesure_mo_s'] = 50.0
        assert decimal(50.0) in phrase_duree(78e9, 0, duree_lisible)
    finally:
        r['debit_mesure_mo_s'] = ancien or 0.0


def test_plafond_des_archives():
    from coupole.core import config
    from coupole.modules.archives.telechargement import plafond_octets_s
    r = config.reglages()
    avant = (r['debit_max_mo_s'], r['archives_debit_mo_s'])
    try:
        r['debit_max_mo_s'], r['archives_debit_mo_s'] = 0.0, 0.0
        assert plafond_octets_s() == 0
        r['debit_max_mo_s'] = 6.0                    # plafond général des Préférences : vaut aussi pour les archives
        assert plafond_octets_s() == 6e6
        r['archives_debit_mo_s'] = 2.0               # réglage propre aux archives : prioritaire
        assert plafond_octets_s() == 2e6
        assert plafond_octets_s(0) == 0 and plafond_octets_s(3) == 3e6     # option --debit
    finally:
        r['debit_max_mo_s'], r['archives_debit_mo_s'] = avant


def test_champ_debit_case_et_valeur(app_qt):
    from coupole.gui.outils import DEBIT_MAXI, ChampDebit
    c = ChampDebit(0)
    assert not c.case.isChecked() and c.value() == 0 and not c.valeur.isEnabled()
    assert c.case.toolTip() and c.valeur.toolTip()
    vus = []
    c.valueChanged.connect(vus.append)
    c.case.setChecked(True)
    assert c.value() > 0 and c.valeur.isEnabled() and vus[-1] == c.value()
    c.valeur.setValue(250.0)
    assert c.value() == 250.0 and DEBIT_MAXI >= 1000
    c.setValue(0)
    assert c.value() == 0
    assert ChampDebit(5.5).value() == 5.5
