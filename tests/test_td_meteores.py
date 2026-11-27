"""Module « Pluies de météores » (td/meteores.py) : données IMO, calendrier, profils, réduction, nuit, campagne ;
valeurs de référence calculées par SageMath (outils/verif_meteores/meteores_verif_sage.py → meteores_sage.json)."""
import datetime as D
import json
import math
from pathlib import Path

import pytest

from coupole.modules.td import meteores as M
from coupole.modules.td import planif as P

REF = json.loads((Path(__file__).with_name('meteores_sage.json')).read_text(encoding='utf-8'))
PARIS = P.Site(48.8366, 2.336, 67.0, 'Paris')
UTC = D.timezone.utc


def _t(s):
    return D.datetime.fromisoformat(s.replace('Z', '+00:00'))


def test_donnees_imo():
    ps = M.pluies()
    assert len(ps) == 39 and len({p.code for p in ps}) == 39
    per = M.pluie('PER')
    assert (per.lambda_max, per.alpha, per.delta, per.v, per.r, per.zhr) == (140.0, 48, 58, 59, 2.2, 110)
    gem = M.pluie('GEM')
    assert (gem.lambda_max, gem.zhr, gem.r) == (262.2, 150, 2.6)
    assert {p.code for p in ps if p.variable} == {'PPU', 'JBO', 'AMO', 'PHO'}
    assert 'Rendtel' in M.sources()['imo'] and 'Jenniskens' in M.sources()['pentes']


def test_calendrier_2027_comme_le_tableau_5():
    """Début, fin et date du maximum de l'année du tableau (2027) : ceux du tableau 5 de l'IMO (la source antihélion,
    active toute l'année, à un jour près)."""
    cal = {e['code']: e for e in M.calendrier(2027)}
    for p in M.pluies():
        e = cal[p.code]
        for cle, val in (('debut', p.debut), ('fin', p.fin)):
            m, j = (int(x) for x in val.split('-'))
            ecart = abs((e[cle].date() - D.date(e[cle].year, m, j)).days)
            assert ecart <= (1 if p.code == 'ANT' else 0), (p.code, cle, e[cle], val)
        if p.max and p.code != 'PUP':
            m, j = (int(x) for x in p.max.split('-'))
            assert (e['max'].month, e['max'].day) == (m, j), (p.code, e['max'])


@pytest.mark.parametrize('x', REF['longitude_solaire'])
def test_longitude_solaire_instants_imo(x):
    lam = M.longitude_solaire(M.jj_de(_t(x['date'])))
    assert abs(lam - x['meeus']) < 1e-6                     # même formule que Sage
    assert abs(lam - x['imo']) < 0.02                       # instants publiés par l'IMO (arrondis à l'heure)


def test_maxima_2027_heures_imo():
    """Heures des maxima 2027 publiées dans le texte du calendrier (à 30 min près, l'IMO arrondit)."""
    cal = {e['code']: e['max'] for e in M.calendrier(2027)}
    for code, s in (('QUA', '2027-01-04T03:25'), ('AUR', '2027-09-01T15:30'), ('SPE', '2027-09-10T00:00'),
                    ('OCT', '2027-10-06T11:00'), ('DRA', '2027-10-09T07:00'), ('URS', '2027-12-23T04:00')):
        assert abs((cal[code] - _t(s + 'Z')).total_seconds()) < 1800, code
    # η-Aquarides : l'IMO 2027 écrit « May 6, 09h UT », l'heure de 2026 ; λ = 45,5° tombe vers 15 h en 2027
    assert abs((cal['ETA'] - _t('2027-05-06T15:12Z')).total_seconds()) < 600
    assert abs((M.calendrier(2026)[[e['code'] for e in M.calendrier(2026)].index('ETA')]['max']
                - _t('2026-05-06T09:05Z')).total_seconds()) < 600


def test_taux_exemple_du_cours_et_fiche_imo():
    assert M.taux_attendu(100, 50, 4.0, 1.0, 2.2) == pytest.approx(REF['cours']['lm4'], rel=1e-12)
    assert M.taux_attendu(100, 50, 5.0, 1.0, 2.2) == pytest.approx(REF['cours']['lm5'], rel=1e-12)
    assert round(REF['cours']['lm4']) == 11 and round(REF['cours']['lm5']) == 23     # « N = 10 … 23 » du cours
    publie = {90: 100, 70: 94, 50: 77, 40: 64, 30: 50, 20: 34, 10: 17}                 # tableau 1 de la fiche
    for h, v in publie.items():
        n = M.taux_attendu(100, h, 6.5)
        assert n == pytest.approx(REF['imo_tableau1'][str(h)], rel=1e-12) and round(n) == v
    assert M.taux_attendu(100, -5) == 0.0


@pytest.mark.parametrize('c', REF['reduction'])
def test_reduction(c):
    r = M.reduction(c['n'], c['t'], c['lm'], c['f'], c['r'], c['h'])
    assert r['zhr'] == pytest.approx(c['zhr'], rel=1e-12) and r['err'] == pytest.approx(c['err'], rel=1e-12)


def test_reduction_alertes():
    assert M.reduction(5, 1, 6, 1, 2.5, 15)['alertes'] == ['mt_alerte_h']
    assert M.reduction(5, 1, 6, 0.6, 2.5, 45)['alertes'] == ['mt_alerte_f']
    assert M.reduction(5, 1, 6, 1, 2.5, -3)['zhr'] is None
    with pytest.raises(ValueError):
        M.reduction(5, 0, 6, 1, 2.5, 40)


def test_profils_jenniskens():
    for code, zm in (('PER', 110), ('GEM', 150)):
        lm = M.pluie(code).lambda_max
        for dl, v in REF['profils'][code].items():
            assert M.zhr(code, (lm + float(dl)) % 360) == pytest.approx(v, rel=1e-9), (code, dl)
    assert M.zhr('PER', 100.0) == 0.0                          # hors de la période d'activité
    assert M.zhr('ANT', M.longitude_solaire(M.jj_de(_t('2027-03-01T00:00Z')))) == 4.0
    # profil indicatif (sans pente publiée) : 1 % du maximum aux limites d'activité
    g = M._geometrie('LYR')
    assert M.zhr('LYR', g['l0'] + 1e-9) == pytest.approx(0.18, rel=1e-6)
    assert M.zhr('LYR', M.pluie('LYR').lambda_max) == pytest.approx(18.0)
    assert not M.pente_publiee('LYR') and M.pente_publiee('GEM')


def test_radiant_derive():
    lm = M.pluie('PER').lambda_max
    a, d = M.radiant('PER', lm)
    assert abs(a - 48) < 1.5 and abs(d - 58) < 0.5           # tableau 6 au maximum ≈ tableau 5
    a, d = M.radiant('PER', M.longitude_solaire(M.jj_de(_t('2027-07-25T00:00Z'))))
    assert (round(a), round(d)) == (22, 53)
    a, d = M.radiant('QUA', M.longitude_solaire(M.jj_de(_t('2027-01-05T00:00Z'))))
    assert (round(a), round(d)) == (231, 49)
    assert M.radiant('AND', 250.0) == (25.0, 51.0)            # absente du tableau 6


@pytest.mark.parametrize('x', REF['hauteur'])
def test_hauteur_comme_sage(x):
    h, az = M.hauteur_az(P.Site(x['lat'], x['lon'], 0.0), x['alpha'], x['delta'], _t(x['date']))
    assert abs(h - x['h']) < 0.02 and abs((az - x['az'] + 180) % 360 - 180) < 0.05


@pytest.mark.parametrize('x', REF['champ'])
def test_champ(x):
    az, h = M._champ(x['az_r'], x['h_r'], None)
    assert h == 60.0
    assert abs((az - x['az_r'] - x['daz'] + 180) % 360 - 180) < 1e-9
    assert M._champ(0.0, 10.0, None) is None


def test_champ_du_cote_oppose_a_la_lune():
    az, _ = M._champ(90.0, 45.0, 90.0 + 44.0)
    assert (az - 90.0 + 180) % 360 - 180 < 0


def test_indice_population():
    c = REF['indice']
    r = M.indice_population({int(k): v for k, v in c['comptes'].items()}, c['lm'])
    assert [m for m, _ in r['rapports']] == [m for m, _ in c['rapports']]
    assert r['r'] == pytest.approx(c['r'], rel=1e-12)
    assert M.indice_population({}, 6)['r'] is None


def test_nuit_geminides_2026():
    N = M.nuit(PARIS, D.date(2026, 12, 13), lm=6.0)
    assert N.pluies[0]['code'] == 'GEM'
    g = N.pluies[0]
    i = g['meilleur']
    t = N.instant(i)
    assert D.datetime(2026, 12, 13, 23, tzinfo=UTC) < t < D.datetime(2026, 12, 14, 5, tzinfo=UTC)
    assert g['h'][i] > 60 and N.soleil[i] < -12
    assert 300 < g['attendu'] < 600 and 9 < g['heures'] < 12
    assert g['taux'][i] == pytest.approx(M.taux_attendu(g['zhr'][i], g['h'][i], 6.0, 1.0, 2.6), rel=1e-9)
    assert not (g['utile'] & (N.soleil >= -12)).any() and not (g['utile'] & (g['h'] < 20)).any()
    # la nuit prend le radiant du milieu de la nuit (dérive ≈ 1°/jour : quelques centièmes de degré d'écart)
    assert abs(M.hauteur_radiant(PARIS, 'GEM', t) - g['h'][i]) < 0.2


def test_nuit_lune_genante():
    """Perséides 2027 : Lune gibbeuse le soir, couchée avant l'aube → temps utile en fin de nuit seulement."""
    N = M.nuit(PARIS, D.date(2027, 8, 12), codes=['PER'])
    e = N.pluies[0]
    assert N.lune_frac > 0.6
    assert not (e['utile'] & (N.lune > 0)).any() and e['utile'].any()


def test_campagne_et_ics():
    C = M.campagne(PARIS, D.date(2026, 12, 10), D.date(2026, 12, 16))
    assert C and all(x['code'] in ('GEM', 'ANT', 'HYD', 'MON', 'PUP', 'COM') for x in C)
    best = max(C, key=lambda x: x['note'])
    assert best['code'] == 'GEM' and best['note'] == 100 and best['nuit'] in (D.date(2026, 12, 13), D.date(2026, 12, 14))
    txt = M.ics(C[:2], 'Paris')
    assert txt.startswith('BEGIN:VCALENDAR') and txt.count('BEGIN:VEVENT') == 2 and '\r\n' in txt


@pytest.fixture
def qapp_met(monkeypatch):
    import os
    monkeypatch.setenv('QT_QPA_PLATFORM', os.environ.get('QT_QPA_PLATFORM', 'offscreen'))
    monkeypatch.setenv('COUPOLE_SANS_RESEAU', '1')
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication(['coupole'])


def test_panneau(qapp_met):
    """Les quatre onglets avec les vrais widgets : calendrier → nuit du maximum, campagne (fil de fond), réduction."""
    import time
    from coupole.modules.td.gui import CALCULATEURS, Panneau
    assert CALCULATEURS[-1] == ('meteores', 'td_calc_meteores')
    t = Panneau()
    t.liste.setCurrentRow(2)
    p = t.meteores
    assert t.pile.currentWidget() is p and t.aide_html() == p.aide_html()
    p.e['p'].setText('')
    p.calculer_nuit()
    assert p.l_etat.text()                                            # lieu manquant : message, pas d'exception
    p.exemple()
    p.c_locale.setChecked(False)
    p.s_annee.setValue(2026)
    assert p.t_cal.rowCount() == 39 and p.t_cal.item(0, 7).text() != '—'
    i = [e['code'] for e in p.cal].index('GEM')
    p.t_cal.selectRow(i)
    p.voir_nuit_du_max()
    assert p.onglets.currentIndex() == 1 and p.N.pluies[0]['code'] == 'GEM'
    assert 'Géminides' in p.d_nuit.toPlainText() or 'Geminids' in p.d_nuit.toPlainText()
    p.graphe.grab()                                                    # dessin sans erreur
    p.e_du.setText('2026-12-12')
    p.e_au.setText('2026-12-15')
    p.chercher()
    fin = time.time() + 60
    while not p.b_camp.isEnabled() and time.time() < fin:
        qapp_met.processEvents()
        time.sleep(0.01)
    assert p.t_camp.rowCount() == len(p.camp) > 0 and p.b_ics.isEnabled()
    p._voir_nuit_campagne(0)
    assert p.onglets.currentIndex() == 1
    p.c_rpluie.setCurrentIndex(p.c_rpluie.findData('GEM'))
    assert p.s_r.value() == 2.6
    p.e_rdeb.setText('2026-12-14 01:00')
    p.e_rfin.setText('2026-12-14 02:00')
    p.s_n.setValue(48)
    p.reduire()
    assert 'ZHR' in p.l_zhr.text()
    p.e_mags.setText('-1:2 0:4 1:9 2:21 3:38 4:55 5:30')
    p.estimer_r()
    assert p.s_r.value() == pytest.approx(REF['indice']['r'], abs=0.005)
    p.e_rfin.setText('pas une date')
    p.reduire()
    assert p.l_etat.text()
    t.close()
