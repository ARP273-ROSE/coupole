"""Temps (UTC partout, heure locale du site, date du soir) et sites (correction de position idempotente)."""
import datetime as D

import pytest

from coupole.core import sites, temps
from coupole.core.fitsentete import Entete
from coupole.core.sites import Site

UTC = D.timezone.utc
OHP = sites.site('ohp')
PERTH = Site('perth', 'test austral', -31.95, 115.86, 20, 'Australia/Perth')          # hémisphère sud, UTC+8
KIRITIMATI = Site('kiri', 'test UTC+14', 1.87, -157.4, 5, 'Pacific/Kiritimati')       # à l'est de la ligne de changement de date


def test_lecture_iso_et_decalages():
    assert temps.iso_vers_utc('2025-07-16T22:20:23.5') == D.datetime(2025, 7, 16, 22, 20, 23, 500000, UTC)
    assert temps.iso_vers_utc('2025-07-17T00:20:23+02:00') == D.datetime(2025, 7, 16, 22, 20, 23, tzinfo=UTC)
    assert temps.iso_vers_utc('2025-07-16T22:20:23Z').tzinfo is UTC
    assert temps.iso_vers_utc('pas une date') is None
    with pytest.raises(ValueError):
        temps.utc_vers_mjd(D.datetime(2025, 1, 1))           # jamais de date sans fuseau


def test_mjd_aller_retour():
    u = D.datetime(2023, 8, 15, 22, 8, 42, tzinfo=UTC)
    assert abs((temps.mjd_vers_utc(temps.utc_vers_mjd(u)) - u).total_seconds()) < 1e-3


def test_date_du_soir_selon_le_site():
    u = D.datetime(2025, 7, 16, 23, 30, tzinfo=UTC)           # 01:30 à l'OHP le 17
    assert temps.date_du_soir(u, OHP) == D.date(2025, 7, 16)
    u2 = D.datetime(2025, 7, 16, 14, 0, tzinfo=UTC)           # 22:00 à Perth le 16 : nuit du 16
    assert temps.date_du_soir(u2, PERTH) == D.date(2025, 7, 16)
    u3 = D.datetime(2025, 7, 16, 18, 0, tzinfo=UTC)           # 02:00 à Perth le 17 : encore la nuit du 16
    assert temps.date_du_soir(u3, PERTH) == D.date(2025, 7, 16)
    # Kiritimati (UTC+14) : 2025-07-16 08:00 UTC = 22:00 le 16 → nuit du 16, alors qu'en UTC-12 ce serait le 15
    u4 = D.datetime(2025, 7, 16, 8, 0, tzinfo=UTC)
    assert temps.heure_locale(u4, KIRITIMATI).hour == 22
    assert temps.date_du_soir(u4, KIRITIMATI) == D.date(2025, 7, 16)


def test_passage_de_minuit():
    avant = D.datetime(2025, 1, 15, 22, 59, tzinfo=UTC)       # 23:59 à l'OHP (hiver, UTC+1)
    apres = D.datetime(2025, 1, 15, 23, 1, tzinfo=UTC)        # 00:01 le 16
    assert temps.heure_locale(avant, OHP).day == 15 and temps.heure_locale(apres, OHP).day == 16
    assert temps.date_du_soir(avant, OHP) == temps.date_du_soir(apres, OHP) == D.date(2025, 1, 15)


def test_hauteur_du_soleil():
    midi = D.datetime(2025, 6, 21, 11, 40, tzinfo=UTC)
    minuit = D.datetime(2025, 6, 21, 23, 40, tzinfo=UTC)
    assert temps.hauteur_soleil(midi, OHP) > 60                 # 90 − 43,9 + 23,4 ≈ 69,5°
    assert temps.hauteur_soleil(minuit, OHP) < -15
    hiver_perth = D.datetime(2025, 6, 21, 4, 0, tzinfo=UTC)    # midi à Perth en hiver austral
    assert 25 < temps.hauteur_soleil(hiver_perth, PERTH) < 40   # 90 − 32 − 23,4 ≈ 34,6°


def test_heure_locale_ecrite_par_erreur():
    # DATE-OBS écrite en heure locale de l'OHP (UTC+2), MJD-OBS juste : écart de 2 h exactement
    vrai = D.datetime(2025, 7, 16, 22, 20, 23, tzinfo=UTC)
    r = temps.lire_temps({'DATE-OBS': '2025-07-17T00:20:23', 'MJD-OBS': temps.utc_vers_mjd(vrai)})
    assert temps.soupcon_heure_locale(r, OHP).startswith('ecart_fuseau')
    r2 = temps.lire_temps({'DATE-OBS': '2025-07-16T22:20:23', 'MJD-OBS': temps.utc_vers_mjd(vrai)})
    assert r2['alertes'] == [] and temps.soupcon_heure_locale(r2, OHP) is None
    # sans MJD : une pose « nocturne » datée 14:00 UTC à Perth tomberait de jour ; −8 h, de nuit
    r3 = temps.lire_temps({'DATE-OBS': '2025-06-21T14:00:00'})
    assert temps.soupcon_heure_locale(r3, PERTH) is None        # 22:00 locale : nuit, rien à dire
    r4 = temps.lire_temps({'DATE-OBS': '2025-06-21T23:00:00'})  # 07:00 locale… mais en hiver, Soleil à peine levé
    assert temps.soupcon_heure_locale(r4, PERTH) in (None,) or temps.soupcon_heure_locale(r4, PERTH).startswith('soleil')


def test_cache_hauteur_du_soleil_par_minute():
    """Deux poses de la même minute : un seul calcul astropy ; résultat identique au calcul direct."""
    temps.vider_cache_soleil()
    t1 = D.datetime(2023, 8, 15, 22, 8, 42, tzinfo=UTC)
    t2 = t1 + D.timedelta(seconds=15)                      # même minute UTC
    t3 = t1 + D.timedelta(seconds=30)                      # minute suivante
    direct = temps.hauteur_soleil(t1, OHP)
    assert abs(temps.hauteurs_soleil_cachees([t1], OHP)[0] - direct) < 1e-9
    s = temps.statistiques_cache_soleil()
    assert s['calculs'] == 1 and s['reutilisations'] == 0 and s['entrees'] == 1
    assert temps.hauteurs_soleil_cachees([t2], OHP)[0] == temps.hauteurs_soleil_cachees([t1], OHP)[0]
    s = temps.statistiques_cache_soleil()
    assert s['calculs'] == 1 and s['reutilisations'] == 2          # aucun nouveau calcul
    assert abs(temps.hauteurs_soleil_cachees([t2], OHP)[0] - temps.hauteur_soleil(t2, OHP)) < 0.3   # ≤ 0,25°/min
    # minute suivante et autre site : nouveaux calculs ; deux instants manquants → UN appel astropy
    h3, h4 = temps.hauteurs_soleil_cachees([t3, t3 + D.timedelta(minutes=1)], OHP)
    assert temps.statistiques_cache_soleil()['calculs'] == 2
    assert abs(h3 - temps.hauteur_soleil(t3, OHP)) < 1e-9
    temps.hauteurs_soleil_cachees([t1], PERTH)
    assert temps.statistiques_cache_soleil()['calculs'] == 3 and temps.statistiques_cache_soleil()['entrees'] == 4
    # soupcon_heure_locale passe par le cache : la 2e pose de la même minute ne calcule rien
    temps.vider_cache_soleil()
    r1 = temps.lire_temps({'DATE-OBS': '2025-06-21T23:00:00'})
    r2 = temps.lire_temps({'DATE-OBS': '2025-06-21T23:00:20'})
    a, b = temps.soupcon_heure_locale(r1, PERTH), temps.soupcon_heure_locale(r2, PERTH)
    assert a == b and temps.statistiques_cache_soleil()['calculs'] == 1


def test_cache_hauteur_du_soleil_entre_fils():
    """Appels simultanés depuis plusieurs fils : mêmes valeurs, aucune exception, cache cohérent."""
    import threading
    temps.vider_cache_soleil()
    t = D.datetime(2024, 3, 1, 18, 30, 5, tzinfo=UTC)
    instants = [t + D.timedelta(seconds=k) for k in range(8)]
    resultats, erreurs = {}, []

    def corps(k):
        try:
            resultats[k] = temps.hauteurs_soleil_cachees([instants[k], instants[k] - D.timedelta(hours=1)], OHP)
        except Exception as e:                                    # pragma: no cover
            erreurs.append(e)
    fils = [threading.Thread(target=corps, args=(k,)) for k in range(8)]
    [f.start() for f in fils]
    [f.join(30) for f in fils]
    assert not erreurs and len(resultats) == 8
    assert len({tuple(v) for v in resultats.values()}) == 1          # tous la même paire (même minute)
    assert temps.statistiques_cache_soleil()['entrees'] == 2 and temps.statistiques_cache_soleil()['calculs'] == 1


def test_affichage_utc_et_local():
    u = D.datetime(2025, 7, 16, 22, 20, 23, tzinfo=UTC)
    t = temps.formater(u, OHP, local_utilisateur=False)
    assert t.startswith('2025-07-16 22:20:23 UTC') and '2025-07-17 00:20:23 (UTC+2)' in t


# ---------------------------------------------------------------- position : trois cas, idempotence
@pytest.mark.parametrize('lat,lon,attendu', [
    ('43 55 54', '05 42 44', 'juste'),             # base corrigée un jour : on ne touche à rien
    ('05 42 44', '43 55 54', 'inversee'),          # inversion démontrée (cas actuel de la banque)
    ('05 42 44', '05 42 55', 'ambigue'),           # une seule valeur fausse : signalé, pas corrigé
    ('12 00 00', '40 00 00', 'ambigue'),           # autre site
])
def test_diagnostic_position(lat, lon, attendu):
    assert sites.diagnostic_position(lat, lon, OHP) == attendu


def _entete(lat, lon, extra=()):
    cartes = ["%-8s= '%s'" % ('LATITUDE', lat), "%-8s= '%s'" % ('LONGITUD', lon)] + list(extra)
    return Entete([c.ljust(80) for c in cartes])


def test_correction_idempotente():
    from coupole.core.i18n import tr
    from coupole.modules.ohp.conversion import corriger_site

    def H(c, **k):
        return tr('hdr_' + c, 'fr', **k)
    e = _entete('05 42 44', '43 55 54')
    info = {}
    corriger_site(e, OHP, info, H)
    assert info['position'] == 'inversee' and e.gets('LATITUDE') == '43 55 55' and e.gets('SITELAT')
    premieres = list(e.modifs)
    # deuxième passage sur l'en-tête corrigé : rien ne bouge
    e2 = Entete([("%-8s= %s / %s" % (n, v, c))[:80].ljust(80) for n, v, c in e.k])
    info2 = {}
    corriger_site(e2, OHP, info2, H)
    assert info2['position'] == 'juste' and e2.modifs == [] and info2['site_mots_cles'] == 'ok'
    assert 'LATITUDE' in premieres


def test_ambigu_rien_n_est_touche():
    from coupole.core.i18n import tr
    from coupole.modules.ohp.conversion import corriger_site
    e = _entete('05 42 44', '05 42 55', ["SITELAT = '+10 00 00'"])
    info = {}
    corriger_site(e, OHP, info, lambda c, **k: tr('hdr_' + c, 'fr', **k))
    assert info['position'] == 'ambigue'
    assert e.gets('LATITUDE') == '05 42 44' and e.gets('SITELAT') == '+10 00 00'
    assert 'SITELAT_incoherent' in info['site_mots_cles']
