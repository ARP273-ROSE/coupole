"""« Maintenant » (0.7.1) : instant de l'appareil sans erreur de fuseau ni d'heure d'été, mêmes résultats que Coupole
Web (tests/maintenant_cas.json : 15 instants × 11 fuseaux, passages à l'heure d'été et d'hiver, décalages exotiques,
jour de l'an, 29 février) ; boutons des animations datées ; « En direct » s'arrête quand on touche la date."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from coupole.modules.anim import maintenant as M

CAS = json.loads((Path(__file__).with_name('maintenant_cas.json')).read_text('utf-8'))


def _proche(a, b, eps=1e-9):
    return abs(a - b) <= eps * max(1.0, abs(b))


def test_identique_au_web():
    for c in CAS['cas']:
        i = M.instant(c['ms'], c['tz'])
        ctx = (c['iso'], c['tz'])
        assert i.tz == c['tz_retenu'], ctx
        assert (i.decalage, i.decalage_standard) == (c['decalage'], c['decalage_standard']), ctx
        assert list(i.local) == c['local'] and list(i.tu) == c['tu'], ctx
        assert M.jour_index(i.local[1], i.local[2]) == c['jour_local'], ctx
        assert _proche(M.jour_tu(i), c['jour_tu']), ctx
        j, h = M.heure_solaire(i, M.meridien_du_fuseau(i))
        assert j == c['solaire_meridien'][0] and _proche(h, c['solaire_meridien'][1]), ctx
        assert _proche(M.tsl_heures(i.jj, 2.35), c['tsl_paris']), ctx
        assert _proche(M.elongation_lune(i.jj), c['elongation_lune']), ctx
        assert M.texte_heure(i, 'fr') == c['texte_fr'] and M.texte_heure(i, 'en') == c['texte_en'], ctx
        assert M.texte_date(i, 'fr') == c['date_fr'] and M.texte_date(i, 'en') == c['date_en'], ctx
    for m, t in CAS['libelles']:
        assert M.libelle_decalage(m) == t
    for mo, j, k in CAS['jours']:
        assert M.jour_index(mo, j) == k


def test_changement_d_heure_paris():
    from datetime import datetime, timezone
    a = M.instant(int(datetime(2026, 10, 25, 0, 59, 59, tzinfo=timezone.utc).timestamp() * 1000), 'Europe/Paris')
    b = M.instant(int(datetime(2026, 10, 25, 1, 0, 0, tzinfo=timezone.utc).timestamp() * 1000), 'Europe/Paris')
    assert M.texte_heure(a, 'fr') == '02:59 heure de Paris (UTC+2) · 00:59 TU'
    assert M.texte_heure(b, 'fr') == '02:00 heure de Paris (UTC+1) · 01:00 TU'
    # l'heure solaire au méridien du fuseau ne saute pas
    assert math.isclose(M.heure_solaire(b, 15.0)[1] - M.heure_solaire(a, 15.0)[1], 1 / 3600, abs_tol=1e-9)


def test_fuseau_local_valide():
    assert M.fuseau_local()                              # IANA, « UTC » ou fuseau du système
    i = M.maintenant()
    assert i.tz and math.isfinite(i.jj)


ANIMS = ['daylightsimulator', 'sunmotions', 'sunpaths', 'sunmotionsoverview', 'dipperclock', 'heliacalrisingsim', 'transitmovie',
         'daylighthoursexplorer', 'seasonsim', 'horizon', 'fullmoondec', 'sunsrays', 'eclipticsimulator', 'zodiac',
         'siderealTimeAndHourAngleDemo', 'celhorcomp', 'lunar_applet', 'ca_extrasolarplanets_starwobble', 'antikythera']


@pytest.mark.parametrize('ident', ANIMS)
def test_boutons_et_direct(app_qt, ident, monkeypatch):
    from coupole.modules.anim import catalogue
    e = catalogue.PAR_ID[ident]
    a = e.charger()()
    a.resize(900, 640)
    assert a.b_maintenant is not None
    from datetime import datetime, timezone
    t = int(datetime(2026, 10, 25, 0, 59, 30, tzinfo=timezone.utc).timestamp() * 1000)
    monkeypatch.setattr(M, 'maintenant', lambda: M.instant(t, 'Europe/Paris'))
    a.b_maintenant.click()
    assert 'UTC+2' in a.l_maintenant.text() and '00:59' in a.l_maintenant.text()
    a.b_direct.setChecked(True)
    assert a._minuteur_direct.isActive()
    # toucher un réglage de date arrête « En direct »
    for cle in a.TEMPS:
        w = a._defauts[cle][0]
        if hasattr(w, 'setValue'):
            w.setValue(w.value() * 0.5 + 1)
            break
    else:
        a._arreter_direct()
    assert not a.b_direct.isChecked() and not a._minuteur_direct.isActive()
    a.deleteLater()
