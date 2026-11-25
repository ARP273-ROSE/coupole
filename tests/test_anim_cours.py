"""Animations tirées des cours (propres à Coupole) : calculs comparés aux valeurs recalculées par SageMath
(outils/verif_anim/*_verif.sage → tests/*_sage.json), comportements de l'interface."""
import json
import math
from pathlib import Path

import pytest

from coupole.modules.anim import diffraction as dif

ICI = Path(__file__).resolve().parent


def sage(nom):
    return json.loads((ICI / ('%s_sage.json' % nom)).read_text(encoding='utf-8'))


# ---------------------------------------------------------------- diffraction et pouvoir de résolution
def test_diffraction_constantes():
    s = sage('resolution')
    assert dif.V1 == pytest.approx(s['v1'], abs=1e-12)
    assert dif.RAYLEIGH == pytest.approx(s['rayleigh'], abs=1e-12)
    assert dif.FWHM_AIRY == pytest.approx(s['fwhm_airy'], abs=1e-12)


def test_diffraction_bessel():
    s = sage('resolution')
    for x, v in s['j1'].items():
        assert dif.j1(float(x)) == pytest.approx(v, abs=2e-8), x
        assert dif.j1(-float(x)) == pytest.approx(-v, abs=2e-8), x
    for x, v in s['i0e'].items():
        assert dif.i0e(float(x)) == pytest.approx(v, rel=2e-6), x


def test_diffraction_zeros_et_anneau():
    s = sage('resolution')
    assert dif.premier_zero(0.0) == pytest.approx(s['v1'], abs=1e-6)
    for e, v in s['zeros'].items():
        assert dif.premier_zero(float(e)) == pytest.approx(v, abs=1e-6), e
    # éclat du premier anneau : 1,75 % du centre
    vm = max(dif.airy(dif.V1 + k * 0.001) for k in range(3200))
    assert vm == pytest.approx(s['anneau1'], rel=1e-4)


def test_diffraction_rayleigh_et_instruments():
    s = sage('resolution')
    for k, d, _ in dif.INSTRUMENTS:
        assert dif.rayleigh_arcsec(d, 550.0) == pytest.approx(s['instruments'][k], rel=1e-9), k
    for cle, v in s['turbulence'].items():
        seeing, lam = cle.split('_')
        assert dif.diametre_turbulence(float(seeing), float(lam)) == pytest.approx(v, rel=1e-9)
    pr = dif.Profil(0.2, 550.0)
    theta = dif.rayleigh_arcsec(0.2, 550.0)
    assert pr.t1 == pytest.approx(theta, rel=1e-6)
    assert dif.creux_milieu(pr, theta) / 100.0 == pytest.approx(s['creux_rayleigh'], abs=2e-3)
    fw = dif.largeur_mi_hauteur(pr) / (550e-9 / 0.2 * dif.SEC_PAR_RAD)
    assert fw == pytest.approx(s['fwhm_airy'], abs=2e-3)


def test_diffraction_pose_longue():
    s = sage('resolution')
    pr = dif.Profil(0.2, 550.0, 0.0, 0.3)
    assert pr.mode == 'convolution'
    for r, v in s['pose_longue'].items():
        assert pr.valeur(float(r)) == pytest.approx(v, abs=3e-3), r
    # turbulence forte : gaussienne de largeur quadratique
    g = dif.Profil(8.2, 550.0, 0.14, 0.8)
    assert g.mode == 'gauss'
    attendu = math.hypot(0.8, dif.FWHM_AIRY * 550e-9 / 8.2 * dif.SEC_PAR_RAD)
    assert dif.largeur_mi_hauteur(g) == pytest.approx(attendu, rel=5e-3)


def test_diffraction_coupe_et_verdict():
    pr = dif.Profil(0.2, 550.0)
    th = dif.rayleigh_arcsec(0.2, 550.0)
    assert dif.coupe(pr, 0.5 * th)['creux'] is None                  # un seul sommet
    assert dif.coupe(pr, 3 * th)['creux'] < 1.0                       # bien séparées : creux noir
    assert dif.verdict(2 * th, 0.2, 550.0, 0.0) == 'separees'
    assert dif.verdict(th, 0.2, 550.0, 0.0) == 'limite'
    assert dif.verdict(0.5 * th, 0.2, 550.0, 0.0) == 'confondues'
    assert dif.verdict(2 * th, 0.2, 550.0, 3.0) == 'confondues'      # la turbulence décide


def test_resolution_interface(app_qt):
    from coupole.modules.anim.animations.resolution import Resolution
    a = Resolution()
    a.resize(900, 640)
    a.instrument.setCurrentIndex(a.instrument.findData('hubble'))
    assert a.diametre.value() == pytest.approx(240.0) and a.obstruction.value() == pytest.approx(0.33)
    a.diametre.setValue(30.0)                                           # réglage libre ensuite
    assert a.instrument.currentData() == 'hubble' and a.diametre.value() == pytest.approx(30.0)
    v = dict(a.valeurs())
    assert 'Premier anneau noir' in v and '1,22 λ / D' in v
    for s in (0.0, 0.5, 3.0):
        a.seeing.setValue(s)
        assert not a.image(640, 420).isNull()


# ---------------------------------------------------------------- les éléments d'une orbite
def test_orbite_periodes_et_vitesses():
    from coupole.modules.anim import elements_orbitaux as eo
    s = sage('elements_orbite')
    for k, (a, e, i, om, w) in eo.ORBITES.items():
        assert eo.periode_s(a) == pytest.approx(s['periodes'][k], rel=1e-12), k
        vp, va = s['vitesses'][k]
        assert eo.vitesse(a * (1 - e), a) == pytest.approx(vp, rel=1e-12)
        assert eo.vitesse(a * (1 + e), a) == pytest.approx(va, rel=1e-12)
    assert eo.demi_grand_axe_de_periode(eo.JOUR_SIDERAL_S) == pytest.approx(s['a_geo'], rel=1e-12)
    assert eo.demi_grand_axe_de_periode(eo.JOUR_SIDERAL_S / 2) == pytest.approx(s['a_molniya'], rel=1e-12)
    # les orbites types sont bien ce qu'elles disent
    assert eo.genre_orbite(*eo.ORBITES['geo'][:3]) == 'geostationnaire'
    assert abs(eo.ORBITES['geo'][0] - s['a_geo']) < 1.0 and abs(eo.ORBITES['molniya'][0] - s['a_molniya']) < 1.0
    assert eo.genre_orbite(*eo.ORBITES['polaire'][:3]) == 'polaire'
    assert eo.genre_orbite(6000.0, 0.0, 10.0) == 'heurte'


def test_orbite_position_vitesse_trace():
    from coupole.modules.anim import elements_orbitaux as eo
    for c in sage('elements_orbite')['cas']:
        a, e, i, om, w, m = c['el']
        st = eo.etat(a, e, i, om, w, m)
        assert st['E'] == pytest.approx(c['E'], abs=1e-9)
        assert st['nu'] == pytest.approx(c['nu'], abs=1e-9)
        assert st['r'] == pytest.approx(c['r'], rel=1e-12)
        assert st['v'] == pytest.approx(c['v'], rel=1e-12)
        assert st['pos'] == pytest.approx(c['pos'], abs=1e-7)
        assert st['vit'] == pytest.approx(c['vit'], abs=1e-10)
        assert math.sqrt(sum(x * x for x in st['vit'])) == pytest.approx(c['norme_vit'], rel=1e-12)
        lat, lon = eo.sous_satellite(st['pos'], c['t'])
        assert lat == pytest.approx(c['lat'], abs=1e-9) and lon == pytest.approx(c['lon'], abs=1e-9)


def test_orbite_interface(app_qt):
    from coupole.modules.anim.animations.elements_orbite import ElementsOrbite
    a = ElementsOrbite()
    a.resize(900, 640)
    a.orbite.setCurrentIndex(a.orbite.findData('molniya'))
    assert a.e.value() == pytest.approx(0.74) and a.i.value() == pytest.approx(63.4) and a.w.value() == pytest.approx(270.0)
    v = dict(a.valeurs())
    assert v['Période T'] == '11 h 58 min'
    a.orbite.setCurrentIndex(a.orbite.findData('geo'))
    assert 'géostationnaire' in dict(a.valeurs())['Orbite']
    for _ in range(30):
        a.pas(0.2)
    for trace in (True, False):
        a.c_trace.setChecked(trace)
        assert not a.image(640, 420).isNull()


# ---------------------------------------------------------------- le transfert de Hohmann
def test_hohmann_bilans():
    from coupole.modules.anim import hohmann_meca as hm
    s = sage('hohmann')
    for k, (mu, r1, r2, *_r) in hm.SCENARIOS.items():
        b = hm.bilan(mu, r1, r2)
        for x in ('v1', 'v2', 'vd', 'va', 'dv1', 'dv2', 'dv', 't', 'phase', 'synodique'):
            assert b[x] == pytest.approx(s[k][x], rel=1e-11, abs=1e-12), (k, x)
        for f, (r, ang) in s[k]['position'].items():
            rr, aa = hm.position_transfert(b, r1, r2, 0.0, b['t'] * float(f))
            assert rr == pytest.approx(r, rel=1e-11), (k, f)
            assert math.remainder(aa - ang, 2 * math.pi) == pytest.approx(0.0, abs=1e-9), (k, f)
        # au bout de la demi-ellipse : r₂, à l'opposé du départ ; partir à l'angle de phase = rendez-vous
        rr, aa = hm.position_transfert(b, r1, r2, 0.3, b['t'])
        assert rr == pytest.approx(r2, rel=1e-9) and math.remainder(aa - 0.3 - math.pi, 2 * math.pi) == pytest.approx(0, abs=1e-7)
        assert hm.ecart_rendez_vous(b, b['phase']) == pytest.approx(0.0, abs=1e-9)
        assert hm.attente_fenetre(b, b['phase']) == pytest.approx(0.0, abs=1e-6 * b['synodique']) or \
            hm.attente_fenetre(b, b['phase']) == pytest.approx(b['synodique'], rel=1e-6)


def test_hohmann_interface(app_qt):
    from coupole.modules.anim.animations.hohmann import Hohmann
    a = Hohmann()
    a.resize(900, 640)
    a.scenario.setCurrentIndex(a.scenario.findData('terre_mars'))
    a.c_auto.setChecked(True)
    for _ in range(120):                              # attente, départ à la fenêtre, transfert, arrivée
        a.pas(0.1)
    assert a.etape() == 'arrive' and abs(a.ecart()) < 0.5
    assert 'rendez-vous réussi' in dict(a.valeurs())['Vaisseau']
    a.recommencer()
    a.c_auto.setChecked(False)
    a.lancer()                                        # départ immédiat : la cible n'y est pas
    for _ in range(70):
        a.pas(0.1)
    assert a.etape() == 'arrive' and abs(a.ecart()) > 2
    for k in ('leo_geo', 'terre_venus', 'terre_lune'):
        a.scenario.setCurrentIndex(a.scenario.findData(k))
        assert a.etape() == 'attente' and not a.image(640, 420).isNull()


# ---------------------------------------------------------------- étoiles filantes et radiant
def test_radiant_hauteur_et_taux():
    from coupole.modules.anim import meteores as me
    s = sage('radiant')
    for c in s['cas']:
        az, h = me.hauteur_radiant(c['essaim'], c['heure'], c['lat'])
        # (temps sidéral en double précision : jour julien ≈ 2,46 × 10⁶, d'où quelques 10⁻⁸ degré)
        assert h == pytest.approx(c['h'], abs=1e-6), c
        assert math.remainder(az - c['az'], 360.0) == pytest.approx(0.0, abs=1e-6), c
        assert me.taux_horaire(c['essaim'], h, c['mlim']) == pytest.approx(c['hr'], rel=1e-7, abs=1e-9), c
    for k, hc in s['culmination'].items():
        assert me.culmination(k, 45.0)[0] == pytest.approx(hc, abs=1e-8)
        # à l'heure de culmination, le radiant est au méridien, à 90° − |φ − δ|
        az, h = me.hauteur_radiant(k, hc if hc >= 12 else hc + 24, 45.0)
        assert h == pytest.approx(90.0 - abs(45.0 - me.ESSAIMS[k][3]), abs=1e-6)


def test_radiant_traînees_vers_le_radiant():
    """Toute traînée est sur un grand cercle qui passe par le radiant et s'en éloigne ; plus courte près de lui."""
    from coupole.modules.anim import meteores as me
    g = me.Aleatoire(7)
    az_r, h_r = 40.0, 55.0
    rad = me.vers_horizon(az_r, h_r)
    n = 0
    for _ in range(400):
        t = me.trainee(g, az_r, h_r)
        if t is None or t[4] < 1.5:
            continue
        n += 1
        p, q = me.vers_horizon(t[0], t[1]), me.vers_horizon(t[2], t[3])
        nrm = (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])
        assert abs(sum(a * b for a, b in zip(nrm, rad))) < 1e-9          # radiant dans le plan du grand cercle
        dist = lambda v: math.degrees(math.acos(max(-1, min(1, sum(a * b for a, b in zip(v, rad))))))
        assert dist(q) > dist(p)                                          # s'éloigne du radiant
        lg = math.degrees(math.acos(max(-1, min(1, sum(a * b for a, b in zip(p, q))))))
        assert lg <= 25.0 * 1.2 * math.sin(math.radians(t[4])) + 1e-9
    assert n > 150
    # générateur identique au web (Park et Miller) : premiers tirages connus
    g = me.Aleatoire(1)
    assert [round(g() * 2147483647) for _ in range(3)] == [16807, 282475249, 1622650073]


def test_radiant_interface(app_qt):
    from coupole.modules.anim.animations.radiant import Radiant
    a = Radiant()
    a.resize(900, 640)
    a.essaim.setCurrentIndex(a.essaim.findData('perseides'))
    a.lat.setValue(45.0)
    a.heure.setValue(23.0)
    v = dict(a.valeurs())
    assert v['Le radiant culmine'].startswith('5 h 4')
    for _ in range(200):
        a.pas(0.1)
    assert 18.0 <= a.heure.value() <= 30.0 and a.filantes
    a.lat.setValue(-55.0)                              # Perséides invisibles de l'hémisphère sud profond
    assert dict(a.valeurs())['Hauteur du radiant'].startswith('sous')
    assert not a.image(640, 420).isNull()


# ---------------------------------------------------------------- interférences et interférométrie
def test_interferometrie_instruments():
    from coupole.modules.anim import interferometrie as itf
    s = sage('interferometrie')
    for k, b, d in itf.INSTRUMENTS:
        for lam, v in s['instruments'][k].items():
            assert itf.interfrange_mas(b, float(lam)) == pytest.approx(v['frange'], rel=1e-12), k
            assert itf.resolution_mas(d, float(lam)) == pytest.approx(v['seul'], rel=1e-12), k


def test_interferometrie_visibilites():
    from coupole.modules.anim import interferometrie as itf
    s = sage('interferometrie')
    for c in s['disque']:
        v = itf.visibilite_complexe('disque', c['theta'], c['b'], c['lam'])
        assert v.real == pytest.approx(c['v'], abs=2e-8), c
        assert v.imag == 0.0
    assert itf.base_premier_zero('disque', 47.0, 575.0) == pytest.approx(s['zero_betelgeuse_575'], rel=1e-12)
    assert itf.base_premier_zero('disque', 6.0, 2200.0) == pytest.approx(s['zero_sirius_2200'], rel=1e-12)
    assert abs(itf.visibilite_complexe('disque', 47.0, s['zero_betelgeuse_575'], 575.0)) < 1e-7
    for c in s['couple']:
        r = 10 ** (-0.4 * c['dm'])
        v = itf.visibilite_complexe('couple', c['rho'], c['b'], c['lam'], r)
        assert v.real == pytest.approx(c['re'], abs=1e-12) and v.imag == pytest.approx(c['im'], abs=1e-12), c
        assert itf.base_premier_zero('couple', c['rho'], c['lam'], r) == pytest.approx(c['b_min'], rel=1e-12)
        assert itf.visibilite('couple', c['rho'], c['b_min'], c['lam'], r) == pytest.approx(c['v_min'], abs=1e-12)
    assert itf.visibilite('point', 0.0, 300.0, 550.0) == 1.0
    assert itf.base_premier_zero('point', 0.0, 550.0) is None


def test_interferometrie_intensite():
    from coupole.modules.anim import interferometrie as itf
    s = sage('interferometrie')
    for c in s['intensite']:
        v = itf.visibilite_complexe(c['genre'], c['taille'], c['b'], c['lam'])
        assert itf.intensite(c['alpha'], c['b'], c['d'], c['lam'], v) == pytest.approx(c['i'], abs=3e-8), c
    # franges d'un point : au centre 1, au premier minimum (α = λ / 2B) presque 0
    b, lam = 130.0, 2200.0
    assert itf.intensite(0.0, b, 8.2, lam, 1 + 0j) == pytest.approx(1.0)
    assert itf.intensite(itf.interfrange_mas(b, lam) / 2, b, 8.2, lam, 1 + 0j) < 1e-2
    # au-delà du premier zéro, les franges d'un disque sont retournées : minimum au centre
    v = itf.visibilite_complexe('disque', 5.0, 150.0, 2200.0)
    assert v.real < 0
    assert itf.intensite(0.0, 150.0, 8.2, 2200.0, v) < itf.intensite(itf.interfrange_mas(150.0, 2200.0) / 2, 150.0,
                                                                     8.2, 2200.0, v)
    xs, ys, demi = itf.coupe(130.0, 8.2, 2200.0, 1 + 0j)
    assert demi == pytest.approx(6 * itf.interfrange_mas(130.0, 2200.0)) and len(xs) == len(ys) == 401


def test_interferometrie_verdict():
    from coupole.modules.anim import interferometrie as itf
    assert itf.verdict('point', 0.0, 8.2, 2200.0, 1.0) == 'v_ponctuelle'
    assert itf.verdict('disque', 100.0, 8.2, 2200.0, 0.0) == 'v_seul'           # 100 mas > 67 mas
    assert itf.verdict('disque', 5.0, 8.2, 2200.0, 0.1) == 'v_interferometre'
    assert itf.verdict('disque', 0.2, 8.2, 2200.0, 0.99) == 'v_non_resolue'


def test_interferometrie_interface(app_qt):
    from coupole.modules.anim.animations.interferometrie import Interferometrie
    a = Interferometrie()
    a.resize(1000, 700)
    a.instrument.setCurrentIndex(a.instrument.findData('michelson'))
    assert a.base.value() == pytest.approx(6.1) and a.diametre.value() == pytest.approx(0.15)
    a.objet.setCurrentIndex(a.objet.findData('betelgeuse'))
    a.lam.setValue(575.0)
    v = dict(a.valeurs())
    assert v['Base du premier zéro 1,22 λ / θ'] == '3,08 m'
    assert v['Interfrange λ / B'] == '19 mas'
    a.base.setValue(3.08)
    assert dict(a.valeurs())['Visibilité V'].startswith('0,00')
    a.c_balayer.setChecked(True)
    b0, b1 = a.axe_bases()
    for _ in range(300):
        a.pas(0.1)
        assert b0 * 0.999 <= a.base.value() <= b1 * 1.2
    a.instrument.setCurrentIndex(a.instrument.findData('young'))
    assert 'Interfrange sur un écran à 1 m' in dict(a.valeurs())
    for o in ('point', 'couple', 'capella', 'sirius'):
        a.objet.setCurrentIndex(a.objet.findData(o))
        assert not a.image(640, 420).isNull()


# ---------------------------------------------------------------- occultation d'une étoile par un astéroïde
def test_occultation_vitesses_echelles():
    from coupole.modules.anim import occultation as oc
    s = sage('occultation')
    assert oc.V_TERRE == pytest.approx(s['v_terre'], rel=1e-14)
    for r, v in s['vitesse'].items():
        assert oc.vitesse_ombre(float(r)) == pytest.approx(v, rel=1e-13), r
    for k, v in s['fresnel'].items():
        lam, d = k.split('_')
        assert oc.fresnel_km(float(lam), float(d)) == pytest.approx(v, rel=1e-13), k
    for k, v in s['etoile'].items():
        th, d = k.split('_')
        assert oc.etoile_km(float(th), float(d)) == pytest.approx(v, rel=1e-13), k


def test_occultation_cordes_et_ajustement():
    from coupole.modules.anim import occultation as oc
    s = sage('occultation')
    for c, aj in zip(s['cordes'], s['ajustements']):
        el = oc.Ellipse(*c['el'])
        cs = oc.cordes(el, c['ys'])
        for (y, x1, x2), attendu in zip(cs, c['cordes']):
            if attendu is None:
                assert x1 is None, y
            else:
                assert (x1, x2) == pytest.approx(tuple(attendu), abs=1e-9), y
        sig = {0: 1.1, 1: 20.0, 2: 0.5, 3: 0.0}[s['cordes'].index(c)]
        br = oc.bruiter(cs, sig)
        for (y, x1, x2), attendu in zip(br, aj['bruitees']):
            if attendu is not None:
                assert (x1, x2) == pytest.approx(tuple(attendu), abs=1e-9), y
        f = oc.ajuster_ellipse([(x, y) for y, x1, x2 in br if x1 is not None for x in (x1, x2)])
        if aj.get('aucun'):
            assert f is None
            continue
        assert f[:4] == pytest.approx((aj['x0'], aj['y0'], aj['a'], aj['b']), rel=1e-7, abs=1e-7)
        assert math.remainder(f[4] - aj['psi'], 180.0) == pytest.approx(0.0, abs=1e-5)


def test_occultation_corde_duree_et_fraction():
    from coupole.modules.anim import occultation as oc
    el = oc.Ellipse(50.0, 50.0, 0.0)
    x1, x2 = el.corde(0.0)
    assert (x1, x2) == pytest.approx((-50.0, 50.0))
    assert el.corde(50.0001) is None
    # étoile ponctuelle : tout ou rien ; étoile projetée plus grande que l'astéroïde : jamais entièrement cachée
    assert oc.fraction_cachee(el, 0.0, 0.0, 0.0) == 1.0 and oc.fraction_cachee(el, 60.0, 0.0, 0.0) == 0.0
    f = oc.fraction_cachee(el, 0.0, 0.0, 100.0)
    assert 0.2 < f < 0.3                                            # (50/100)² = 25 % du disque
    assert len(oc.GRILLE) > 150
    assert oc.stations(3, 10.0) == [-10.0, 0.0, 10.0]
    # trop peu de cordes : pas d'ellipse
    assert oc.ajuster_ellipse([(1.0, 0.0), (-1.0, 0.0), (0.5, 1.0), (-0.5, 1.0)]) is None


def test_occultation_interface(app_qt):
    from coupole.modules.anim.animations.occultation import Occultation
    a = Occultation()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Vitesse de l’ombre (à l’opposition)'] == '10,95 km·s⁻¹'
    assert v['Observateurs qui voient l’étoile disparaître'] == '6 sur 7'
    a.objet.setCurrentIndex(a.objet.findData('eris'))
    assert a.diametre.value() == pytest.approx(2326.0)
    assert dict(a.valeurs())['Vitesse de l’ombre (à l’opposition)'] == '26,74 km·s⁻¹'
    a.n_stations.setValue(2)
    assert dict(a.valeurs())['Ellipse ajustée 2a × 2b'] == 'il faut au moins trois cordes'
    a.etoile.setValue(50.0)
    a.objet.setCurrentIndex(a.objet.findData('troyen'))
    assert 'progressive' in dict(a.valeurs())['Étoile projetée à la distance de l’astéroïde']
    tm = a.t_max()
    for _ in range(120):
        a.pas(0.1)
        assert -tm - 1e-9 <= a.instant() <= tm + 1e-9
    assert not a.image(640, 420).isNull()


# ---------------------------------------------------------------- le mécanisme de Kozai-Lidov
def test_kozai_constantes_et_tk():
    from coupole.modules.anim import kozai as kz
    s = sage('kozai')
    assert s['hamiltonien'] and s['vectoriel']
    assert kz.I_CRITIQUE == pytest.approx(s['i_critique'], abs=1e-12)
    for i0, em in s['e_max'].items():
        assert kz.e_max_circulaire(float(i0)) == pytest.approx(em, abs=1e-12)
        assert kz.i_a_e(kz.constante_c(0.0, float(i0)), em) == pytest.approx(s['i_au_max'][i0], abs=1e-8)
    assert kz.e_max_circulaire(30.0) == 0.0
    for k, m, ap, per in kz.SYSTEMES:
        assert kz.t_kozai_ans(m, ap, per) == pytest.approx(s['t_k'][k], rel=1e-12), k


def test_kozai_integration_contre_sage():
    from coupole.modules.anim import kozai as kz
    s = sage('kozai')
    for c in s['etats']:
        ev, jv = kz.vecteurs(c['e0'], c['i0'], c['w0'])
        tau = 0.0
        for tt in ('3', '7.5'):
            ev, jv = kz.integrer(ev, jv, float(tt) - tau)
            tau = float(tt)
            assert ev + jv == pytest.approx(c['etats'][tt], abs=2e-9), (c, tt)
        # C et l'énergie conservés
        e, i, w, _ = kz.elements(ev, jv)
        assert kz.constante_c(e, i) == pytest.approx(kz.constante_c(c['e0'], c['i0']), abs=1e-10)
        assert kz.energie(e, i, w) == pytest.approx(kz.energie(c['e0'], c['i0'], c['w0']), abs=1e-9)


def test_kozai_elements_aller_retour():
    from coupole.modules.anim import kozai as kz
    for e, i, w, o in ((0.3, 63.0, 40.0, 10.0), (0.6, 52.0, 230.0, -120.0), (0.01, 85.0, 359.0, 0.0)):
        e2, i2, w2, o2 = kz.elements(*kz.vecteurs(e, i, w, o))
        assert (e2, i2) == pytest.approx((e, i), abs=1e-12)
        assert math.remainder(w2 - w, 360.0) == pytest.approx(0.0, abs=1e-9)
        assert math.remainder(o2 - o, 360.0) == pytest.approx(0.0, abs=1e-9)


def test_kozai_interface_periode(app_qt):
    from coupole.modules.anim.animations.kozai import Kozai
    s = sage('kozai')
    a = Kozai()
    a.resize(1000, 700)
    a.i0.setValue(65.0)
    a.e0.setValue(0.05)
    a.w0.setValue(0.0)
    a.recommencer()
    for _ in range(140):                                  # 0,1 s × 2 t_K/s : 28 t_K
        a.pas(0.1)
    m = s['maxima']['0.05_65_0']
    # instant du maximum interpolé linéairement entre deux images (pas de 0,2 t_K ici) : à 3 × 10⁻³ près
    assert a.maxima[0] == pytest.approx(m[0], abs=3e-3) and a.maxima[1] == pytest.approx(m[1], abs=3e-3)
    v = dict(a.valeurs())
    assert v['Période des oscillations'].startswith('5,03 tₖ')
    assert v['e maximale atteinte'].startswith('0,83')
    assert v['Inclinaison critique arccos √(3/5)'] == '39,23°'
    a.i0.setValue(30.0)                                   # sous l'inclinaison critique : e reste petite
    assert a.tau == 0.0
    for _ in range(50):
        a.pas(0.1)
    assert a.e_max < 0.1
    assert not a.image(640, 420).isNull()


# ---------------------------------------------------------------- les points de Lagrange
def test_lagrange_points_et_constantes():
    from coupole.modules.anim import lagrange as lg
    s = sage('lagrange')
    assert lg.MU_ROUTH == pytest.approx(s['mu_routh'], abs=1e-15)
    for k, mu, _ in lg.SYSTEMES:
        c = s['systemes'][k]
        assert mu == pytest.approx(c['mu'], rel=1e-14), k
        L = lg.points_lagrange(mu)
        for n, (x, y) in L.items():
            assert (x, y) == pytest.approx(tuple(c['L'][n]), abs=1e-12), (k, n)
            assert lg.jacobi(mu, x, y, 0.0, 0.0) == pytest.approx(c['C'][n], abs=1e-11), (k, n)
            gx, gy = lg.gradient(mu, x, y)
            assert abs(gx) < 1e-9 and abs(gy) < 1e-9, (k, n)          # vrais équilibres
        assert lg.rayon_hill(mu) == pytest.approx(c['hill'], rel=1e-13)
        assert (mu < lg.MU_ROUTH) == c['L4_stable'], k


def test_lagrange_trajectoires_contre_sage():
    from coupole.modules.anim import lagrange as lg
    s = sage('lagrange')
    mu = lg.SYSTEMES[2][1]
    for cas, delta in (('tetard', 0.005), ('fer_a_cheval', 0.01)):
        st = lg.depart(mu, cas, delta)
        c0 = lg.jacobi(mu, *st)
        t = 0.0
        for tt in ('2', '6'):
            st, touche = lg.integrer(mu, st, float(tt) - t)
            t = float(tt)
            assert not touche
            assert st == pytest.approx(tuple(s['trajectoires'][cas][tt]), abs=1e-10), (cas, tt)
        assert lg.jacobi(mu, *st) == pytest.approx(c0, abs=1e-11)
    # régions selon C
    L = lg.points_lagrange(mu)
    cl = {k: lg.jacobi(mu, x, y, 0.0, 0.0) for k, (x, y) in L.items()}
    assert lg.regions(mu, cl['L1'] + 1e-6) == 'r_ferme'
    assert lg.regions(mu, (cl['L1'] + cl['L2']) / 2) == 'r_l1'
    assert lg.regions(mu, (cl['L2'] + cl['L3']) / 2) == 'r_l2'
    assert lg.regions(mu, (cl['L3'] + cl['L4']) / 2) == 'r_l3'
    assert lg.regions(mu, cl['L4'] - 1e-6) == 'r_partout'


def test_lagrange_interface(app_qt):
    from coupole.modules.anim.animations.lagrange import Lagrange
    a = Lagrange()
    a.resize(1000, 700)
    a.systeme.setCurrentIndex(a.systeme.findData('soleil_terre'))
    v = dict(a.valeurs())
    assert v['L2 : distance au petit astre'].endswith('1,51 millions de km')     # le JWST
    assert v['Rapport de masse μ'] == '3,040 × 10⁻⁶'
    a.systeme.setCurrentIndex(a.systeme.findData('soleil_jupiter'))
    a.cas.setCurrentIndex(a.cas.findData('fer_a_cheval'))
    assert a.delta.value() == pytest.approx(0.01)
    c0 = lg_c(a)
    for _ in range(40):
        a.pas(0.1)
    assert lg_c(a) == pytest.approx(c0, abs=1e-9) and len(a.trace) > 100
    assert dict(a.valeurs())['Son énergie lui permet d’aller'].startswith('aussi au-delà de L2')
    a.systeme.setCurrentIndex(a.systeme.findData('pluton_charon'))
    assert dict(a.valeurs())['L4 et L5'] == 'instables (μ > 0,0385)'
    a.cas.setCurrentIndex(a.cas.findData('l1'))
    for _ in range(80):
        a.pas(0.1)
    assert not a.image(640, 420).isNull()


def lg_c(a):
    from coupole.modules.anim import lagrange as lg
    return lg.jacobi(a.mu_a()[0], *a.s)
