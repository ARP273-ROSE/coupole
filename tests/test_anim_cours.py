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


# ---------------------------------------------------------------- diagramme a–e (0.12.0)
def test_diagramme_ae_contre_sage():
    from coupole.modules.anim import diagramme_ae as ae
    s = sage('survols_impacts')
    for k, ref in s['ae'].items():
        a, e, i = {'sedna': (544.0, 0.86, 11.9)}.get(k) or [o[1:] for o in ae.OBJETS if o[0] == k][0]
        assert ae.perihelie(a, e) == pytest.approx(ref['q'], rel=1e-9), k
        assert ae.aphelie(a, e) == pytest.approx(ref['Q'], rel=1e-9), k
        assert ae.periode(a) == pytest.approx(ref['P'], rel=1e-9), k
        assert ae.tisserand(a, e, i) == pytest.approx(ref['T'], rel=1e-8, abs=1e-9), k
        assert ae.famille(a, e) == ref['famille'], k
    for pq, ref in s['resonances'].items():
        p, q = map(int, pq.split(':'))
        assert ae.resonance(p, q) == pytest.approx(ref, rel=1e-9)
    for cle, ref in s['kepler'].items():
        a, e, m = map(float, cle.split(','))
        x, y = ae.position(a, e, m)
        assert x == pytest.approx(ref[0], abs=1e-9) and y == pytest.approx(ref[1], abs=1e-9), cle


def test_diagramme_ae_familles_et_croisements():
    from coupole.modules.anim import diagramme_ae as ae
    assert ae.famille(0.741, 0.322) == 'atira' and ae.famille(0.922, 0.191) == 'aten'
    assert ae.famille(1.13, 0.204) == 'apollo' and ae.famille(1.46, 0.223) == 'amor'
    assert ae.famille(5.28, 0.0243) == 'troyen' and ae.famille(39.6, 0.252) == 'transneptunien'
    assert ae.croisees(1.13, 0.204) == ['terre'] and ae.croisees(17.9, 0.968)[-1] == 'neptune'
    assert ae.genre_tisserand(ae.tisserand(3.46, 0.641, 7.04)) == 'comete_jupiter'
    assert ae.genre_tisserand(ae.tisserand(17.9, 0.968, 162.0)) == 'comete_halley'


def test_diagramme_ae_interface(app_qt):
    from PyQt6.QtCore import QPointF
    from coupole.modules.anim.animations.diagramme_ae import DiagrammeAE
    a = DiagrammeAE()
    a.resize(1000, 700)
    a.objet.setCurrentIndex(a.objet.findData('apophis'))
    assert a.a.value() == pytest.approx(0.922) and a.e.value() == pytest.approx(0.191)
    v = dict(a.valeurs())
    assert v['Classe de l’orbite'].startswith('géocroiseur Aten') and v['Croise l’orbite de'] == 'Terre'
    assert not a.image(900, 560).isNull()
    ax = a._graphe
    assert a.presser(QPointF(ax.px(1.5), ax.py(0.5)), None)
    assert a.objet.currentData() == 'libre' and a.a.value() == pytest.approx(1.5, rel=0.02)
    assert dict(a.valeurs())['Classe de l’orbite'].startswith('géocroiseur Apollo')


# ---------------------------------------------------------------- assistance gravitationnelle (0.12.0)
def test_assistance_contre_integration_sage():
    from coupole.modules.anim import assistance as ga
    s = sage('survols_impacts')
    for cle, ref in s['survols'].items():
        pl, vinf, rp, ang, cote = cle.split(',')
        r = ga.survol(pl, float(vinf), float(rp), float(ang), cote == 'derriere')
        assert r['V'] == pytest.approx(ref['V'], rel=1e-9), cle
        assert r['delta'] == pytest.approx(ref['delta'], rel=1e-9), cle
        assert r['delta'] == pytest.approx(ref['delta_integre'], abs=1e-8), cle       # survol intégré par Sage
        assert r['u_out'][0] == pytest.approx(ref['u_out'][0], abs=1e-8), cle
        assert r['u_out'][1] == pytest.approx(ref['u_out'][1], abs=1e-8), cle
        assert r['gain'] == pytest.approx(ref['gain'], abs=1e-7), cle
        assert r['dv'] == pytest.approx(ref['dv'], rel=1e-9) and r['v_peri'] == pytest.approx(ref['v_peri'], rel=1e-9)
        for nom in ('orb_in', 'orb_out'):
            for k in ('a', 'e', 'q', 'Q'):
                if ref[nom][k] is None:
                    assert math.isinf(r[nom][k]), (cle, nom, k)
                else:
                    assert r[nom][k] == pytest.approx(ref[nom][k], rel=1e-8), (cle, nom, k)


def test_assistance_hyperbole():
    from coupole.modules.anim import assistance as ga
    gm, _, _ = ga.planete('jupiter')
    s = ga.survol('jupiter', 10.0, 5.0, 150.0, True)
    x, y = ga.hyperbole(s, gm, 0.0)
    assert math.hypot(x, y) == pytest.approx(s['r_p'], rel=1e-12)
    # loin du périastre, la direction du mouvement tend vers u_in (avant) et u_out (après)
    for f, u in ((-12.0, s['u_in']), (12.0, s['u_out'])):
        p0, p1 = ga.hyperbole(s, gm, f), ga.hyperbole(s, gm, f + 1e-3)
        d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        assert ((p1[0] - p0[0]) / d, (p1[1] - p0[1]) / d) == pytest.approx(u, abs=1e-6)
    t = 3.0e4
    f = ga.anomalie(s, gm, t)
    a = s['r_p'] / (s['e'] - 1.0)
    assert s['e'] * math.sinh(f) - f == pytest.approx(math.sqrt(gm / a ** 3) * t, rel=1e-12)


def test_assistance_interface(app_qt):
    from coupole.modules.anim.animations.assistance import Assistance
    a = Assistance()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Gain'].startswith('+10,27') and v['Orbite après le survol'] == 'de 5,01 à 77,06 ua du Soleil'
    a.angle.setValue(90.0)                           # v∞ perpendiculaire : derrière accélère, devant freine
    assert dict(a.valeurs())['Gain'].startswith('+')
    a.cote.setCurrentIndex(a.cote.findData('devant'))
    assert dict(a.valeurs())['Gain'].startswith('−')
    a.planete.setCurrentIndex(a.planete.findData('venus'))
    for _ in range(30):
        a.pas(0.2)
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- cratère d'impact (0.12.0)
def test_cratere_contre_sage():
    from coupole.modules.anim import cratere as cr
    s = sage('survols_impacts')
    for cle, ref in s['crateres'].items():
        L, v, th, ri, rt = map(float, cle.split(','))
        c = cr.cratere(L, v, th, ri, rt)
        for k in ('transitoire', 'prof_transitoire', 'final', 'profondeur', 'rempart', 'breche'):
            assert c[k] == pytest.approx(ref[k], rel=1e-8, abs=1e-6), (cle, k)
        assert c['genre'] == ref['genre']
        e = cr.energie(L, ri, v)
        assert e == pytest.approx(ref['E'], rel=1e-8)
        assert cr.recurrence_ans(e / cr.MT_J) == pytest.approx(ref['recurrence'], rel=1e-8)


def test_cratere_cas_du_cours(app_qt):
    from coupole.modules.anim.animations.cratere import Cratere
    a = Cratere()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Diamètre du cratère final'] == '22,4 km'                 # « un cratère de 23 km » au cours
    assert v['Forme'].startswith('cratère complexe')
    a.exemple.setCurrentIndex(a.exemple.findData('meteor_crater'))
    v = dict(a.valeurs())
    assert v['Forme'].startswith('cratère simple') and 'Attention' in v
    for _ in range(25):
        a.pas(0.25)
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- rotation synchrone et libration (0.12.0)
def test_libration_contre_sage():
    from coupole.modules.anim import libration as lb
    s = sage('libration')
    for cle, (l_ref, b_ref) in s['libration'].items():
        M, e, I, w = map(float, cle.split(','))
        l, b = lb.libration(M, e, I, w)
        assert l == pytest.approx(l_ref, abs=1e-8) and b == pytest.approx(b_ref, abs=1e-8), cle
    lmax = max(lb.libration(k / 1000.0, lb.E_LUNE, 0.0, 0.0)[0] for k in range(3142))
    assert lmax == pytest.approx(s['l_max'], abs=1e-5)
    assert lb.rho_diurne(lb.E_LUNE) == pytest.approx(s['rho_diurne'], abs=1e-9)
    rho = lb.rho_diurne(lb.E_LUNE)
    # part vue : méthode des azimuts (Coupole) contre une grille fine de la sphère (Sage), à 10⁻³ près
    for cle, (f0, f1) in s['fractions'].items():
        if cle == 'annees':
            assert lb.fraction_annees(lb.E_LUNE, lb.I_LUNE) == pytest.approx(f0, abs=1e-3)
            assert lb.fraction_annees(lb.E_LUNE, lb.I_LUNE, rho_deg=rho) == pytest.approx(f1, abs=1e-3)
            continue
        e, I, w = map(float, cle.split(','))
        assert lb.fraction_mois(e, I, w) == pytest.approx(f0, abs=1e-3), cle
        assert lb.fraction_mois(e, I, w, rho_deg=rho) == pytest.approx(f1, abs=1e-3), cle


def test_libration_projection_et_rotation():
    from coupole.modules.anim import libration as lb
    assert lb.projection(0.0, 0.0, 0.0, 0.0) == pytest.approx((0.0, 0.0, 1.0))
    x, _, z = lb.projection(17.0, 59.1, 6.0, 0.0)              # l > 0 : la mer des Crises se rapproche du centre
    assert x < lb.projection(17.0, 59.1, 0.0, 0.0)[0] and z > 0.0
    assert lb.fraction_mois(0.0549, 6.68, 0.0, synchrone=False) == pytest.approx(1.0)
    assert lb.fraction_mois(0.0, 0.0, 0.0) == pytest.approx(0.5)


def test_libration_interface(app_qt):
    from coupole.modules.anim.animations.libration import Libration
    a = Libration()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['… au fil des années (ϖ tourne)'] == '58,0 %' and v['Libration diurne arcsin(R⊕/d)'] == '0,95°'
    for _ in range(12):
        a.pas(0.3)
    assert '(2e sin M' in dict(a.valeurs())['Libration en longitude l = ν − M']
    a.rotation.setCurrentIndex(a.rotation.findData('aucune'))
    assert dict(a.valeurs())['Surface vue au moins une fois en un mois'] == '100,0 %'
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- précession des équinoxes (0.12.0)
def test_precession_contre_sage():
    from coupole.modules.anim import precession as pr
    s = sage('precession')
    assert pr.PERIODE_ANS == pytest.approx(s['periode'], rel=1e-9) and pr.EPS == pytest.approx(s['eps'], rel=1e-9)
    for n, d in s['distances'].items():
        for t, ref in d.items():
            assert pr.distance_au_pole(n, float(t)) == pytest.approx(ref, abs=1e-8), (n, t)
    for n, (t, d) in s['minimum'].items():
        ts = [t + k for k in range(-30, 31)]
        t_min = min(ts, key=lambda x: pr.distance_au_pole(n, x))
        assert abs(t_min - t) <= 1.0 and pr.distance_au_pole(n, t_min) == pytest.approx(d, abs=1e-5), n
    assert pr.annee_entree('aqr', 2026.0) == pytest.approx(s['verseau'], abs=1e-6)
    assert pr.annee_entree('ari', -5000.0) == pytest.approx(s['taureau_belier'], abs=1e-6)


def test_precession_etoiles_polaires_et_zodiaque():
    from coupole.modules.anim import precession as pr
    assert pr.plus_proche(2100.0)[0] == 'α UMi' and pr.plus_proche(-2800.0)[0] == 'α Dra'
    assert pr.plus_proche(13800.0)[0] == 'α Lyr'
    assert pr.constellation(pr.point_vernal(2026.0)) == 'psc' and pr.constellation(pr.point_vernal(3000.0)) == 'aqr'
    assert pr.constellation(pr.point_vernal(-2800.0)) == 'tau'
    assert pr.distance_au_pole('α UMi', 2000.0 + pr.PERIODE_ANS) == pytest.approx(pr.distance_au_pole('α UMi', 2000.0))


def test_precession_interface(app_qt):
    from coupole.modules.anim.animations.precession import Precession
    a = Precession()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Étoile brillante la plus proche du pôle'] == 'Polaris (α UMi), à 0,63°'
    assert v['Constellation suivante'] == 'Verseau, à partir de 2598'
    a.annee.setValue(-2800.0)
    assert dict(a.valeurs())['Année'] == '−2800 (2801 av. J.-C.)'
    a.annee.setValue(14900.0)
    a.pas(0.5)
    assert a.annee.value() < 0.0                           # le temps reboucle après 15 000
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- résonances et chaos (0.12.0)
def test_resonances_contre_sage():
    from coupole.modules.anim import resonances as rs
    s = sage('resonances')
    for pq, a in s['resonances'].items():
        p, q = map(int, pq.split(':'))
        assert rs.A_JUPITER_UA * (q / p) ** (2.0 / 3.0) == pytest.approx(a, rel=1e-9)
    cas = {'hilda': (3.97, 0.15, 0.0), 'kirkwood': (2.5, 0.1, 0.0), 'comete': (3.6, 0.55, 150.0)}
    for k, (a, e, phi) in cas.items():
        ref = s['cas'][k]
        s1 = rs.etat_initial(a, e, phi, rs.MU_JUPITER)
        assert s1 == pytest.approx(ref['initial'], abs=1e-9), k
        assert rs.elements(s1, rs.MU_JUPITER) == pytest.approx((ref['a0'], ref['e0']), abs=1e-9), k
        s2, t = rs.jumeau(s1), 0.0
        for T in ('6', '30'):
            if k == 'comete' and T == '30':
                continue                                   # chaotique : les deux intégrateurs divergent ensuite
            s1, s2, _ = rs.avancer(rs.MU_JUPITER, s1, s2, float(T) - t)
            t = float(T)
            assert s1 == pytest.approx(ref[T]['etat'], abs=5e-9), (k, T)
            assert rs.elements(s1, rs.MU_JUPITER) == pytest.approx((ref[T]['a'], ref[T]['e']), abs=1e-8), (k, T)
            assert rs.ecart(s1, s2) == pytest.approx(ref[T]['ecart'], rel=1e-5), (k, T)


def test_resonances_regulier_contre_chaotique():
    from coupole.modules.anim import resonances as rs
    mu = rs.MU_JUPITER
    ecarts = {}
    for k, a, e, phi in rs.CAS:
        if k not in ('hilda', 'comete'):
            continue
        s1 = rs.etat_initial(a, e, phi, mu)
        s2 = rs.jumeau(s1)
        s1, s2, _ = rs.avancer(mu, s1, s2, 2.0 * math.pi * 40)
        ecarts[k] = rs.ecart(s1, s2)
    assert ecarts['hilda'] < 1e-3 < ecarts['comete']
    assert rs.resonance_proche(3.97)[0] == (3, 2) and rs.rapport_periodes(2.5011) == pytest.approx(3.0, rel=1e-3)


def test_resonances_interface(app_qt):
    from coupole.modules.anim.animations.resonances import Resonances
    a = Resonances()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Résonance la plus proche'].startswith('3:2 à 3,97 ua')
    for _ in range(10):
        a.pas(0.2)
    assert a.t == pytest.approx(2.0 * 2.0 * math.pi, rel=1e-9)
    a.repere.setCurrentIndex(a.repere.findData('fixe'))
    assert not a.image(900, 560).isNull()
    a.cas.setCurrentIndex(a.cas.findData('troyen'))
    assert a.a.value() == pytest.approx(5.2026) and a.t == 0.0
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- limite de Roche (0.12.0)
def test_roche_contre_sage():
    from coupole.modules.anim import roche as ro
    s = sage('roche')
    assert ro.K_RIGIDE == pytest.approx(s['K_rigide'], rel=1e-9)
    for k, rm, rs_, _, d0 in ro.SYSTEMES:
        ref = s['systemes'][k]
        assert ro.limite(rm / rs_, 'fluide') == pytest.approx(ref['fluide'], rel=1e-9), k
        assert ro.limite(rm / rs_, 'rigide') == pytest.approx(ref['rigide'], rel=1e-9), k
        assert ro.etirement(rm / rs_, d0) == pytest.approx(ref['etirement'], rel=1e-9), k
        assert ro.allongement(rm / rs_, d0) == pytest.approx(ref['allongement'], rel=1e-9), k
    for g in s['grains']:
        d, th, gx, gy = g['depart']
        x, y = d * math.cos(th) + gx * math.cos(th) - gy * math.sin(th), d * math.sin(th) + gx * math.sin(th) + gy * math.cos(th)
        om = d ** -1.5
        el = ro.elements(x, y, -om * y, om * x)
        for T, ref in g['positions'].items():
            assert ro.position_kepler(el, float(T)) == pytest.approx(ref, abs=1e-8), (g['depart'], T)


def test_roche_dislocation(app_qt):
    from coupole.modules.anim.animations.roche import Roche
    a = Roche()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Limite de Roche, satellite fluide 2,44 R ∛(ρₚ/ρₛ)'].startswith('2,21 R')    # anneaux à 2,27 R
    assert v['État'] == 'entier'
    for _ in range(20):
        a.pas(0.25)
    assert a.debris is not None and a.d < a.limite() + 0.1
    assert dict(a.valeurs())['État'].startswith('disloqué')
    a.systeme.setCurrentIndex(a.systeme.findData('mars_phobos'))
    a.modele.setCurrentIndex(a.modele.findData('rigide'))
    a.c_descente.setChecked(False)
    for _ in range(5):
        a.pas(0.25)
    assert a.debris is None                             # Phobos, rigide, tient à 2,76 R
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- précession séculaire d'une orbite (0.12.0)
def test_seculaire_contre_sage():
    from coupole.modules.anim import seculaire as sc
    s = sage('seculaire')
    for al, b1, b2 in s['laplace']:
        assert sc.laplace_b(1.5, 1, al) == pytest.approx(b1, rel=1e-9)
        assert sc.laplace_b(1.5, 2, al) == pytest.approx(b2, rel=1e-9)
    for k, a, e, i, o, w in sc.OBJETS:
        ref = s['objets'][k]
        A = sc.frequence(a)
        assert A == pytest.approx(ref['A'], rel=1e-9), k
        assert A * sc.SEC_PAR_RAD == pytest.approx(ref['A_arcsec_an'], rel=1e-9)
        assert sc.frequence_quadrupole(a) == pytest.approx(ref['quadrupole'], rel=1e-9)
        assert sc.noeuds(a, e, w) == pytest.approx((ref['r_asc'], ref['r_desc']), rel=1e-9)
        c = sc.croisements(a, e, w, A, 0.0, 2.0 * math.pi / A)
        assert [g for _, g in c] == [g for _, g in ref['croisements']], k
        assert [t for t, _ in c] == pytest.approx([t for t, _ in ref['croisements']], abs=1e-3)
        assert sc.moid(a, e, i, w) == pytest.approx(ref['moid'], abs=1e-7), k
        for ww, m in ref['moid_w']:
            assert sc.moid(a, e, i, ww) == pytest.approx(m, abs=1e-7), (k, ww)
    # théorie contre intégration directe (Soleil + Jupiter circulaire, 3 000 ans) : à 0,2 % près
    it = s['integration']
    A_j = sc.moyen_mouvement(it['a']) / 4.0 * sc.terme(it['a'], 5.2029, 1047.348_644)
    assert A_j == pytest.approx(it['A_jupiter'], rel=1e-9)
    assert it['pente_varpi'] == pytest.approx(A_j, rel=2e-3)
    assert -it['pente_omega'] == pytest.approx(A_j, rel=2e-3)


def test_seculaire_interface(app_qt):
    from coupole.modules.anim.animations.seculaire import Seculaire
    a = Seculaire()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Date'] == 'an 2026'
    assert v['Précession A = (n/4) Σ (m/M☉) α² b(α)'] == '14,34″ par an'
    assert v['Prochain croisement'] == 'an 22494 (nœud ascendant)'
    a.suivant()
    assert a.t == pytest.approx(20467.80114, abs=1e-3)
    assert float(dict(a.valeurs())['Distance minimale à l’orbite terrestre (MOID)'].split()[0].replace(',', '.')) < 1e-3
    a.objet.setCurrentIndex(a.objet.findData('phaethon'))
    assert a.a.value() == pytest.approx(1.27) and a.t == 0.0
    assert dict(a.valeurs())['Prochain croisement'] == 'an 2641 (nœud descendant)'
    a.e.setValue(0.1)
    assert dict(a.valeurs())['Prochain croisement'].startswith('jamais')
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- phénomènes mutuels des satellites galiléens (0.12.0)
def test_mutuels_contre_sage():
    from coupole.modules.anim import mutuels as mu
    s = sage('mutuels')
    for d, r1, r2, aire in s['lentilles']:
        assert mu.aire_commune(d, r1, r2) == pytest.approx(aire, rel=1e-9)
    for r in s['rencontres']:
        R = mu.Rencontre(*r['cas'])
        tol = 1e-9 if r['cas'][2] == 'occultation' else 1e-6
        for t, f in r['flux']:
            assert R.flux(t) == pytest.approx(f, abs=tol), (r['cas'], t)
        # durée tracée (flux < 1) contre premier et dernier contacts autour de 0 (pas de la courbe : 2T/240)
        ct = [x for x in r['contacts'] if abs(x) < R.demi_fenetre()]
        fmin, _, duree = mu.resume(R.courbe())
        if len(ct) == 2:
            assert duree == pytest.approx(ct[1] - ct[0], abs=4.0 * R.demi_fenetre() / 240.0), r["cas"]   # un pas à chaque bout


def test_mutuels_cas_limites():
    from coupole.modules.anim import mutuels as mu
    assert mu.aire_commune(0.0, 2.0, 1.0) == pytest.approx(math.pi)
    assert mu.aire_commune(3.0, 2.0, 1.0) == 0.0
    # occultation totale d'Europe par Io (Io plus grand) : il ne reste que l'éclat d'Io
    R = mu.Rencontre('io', 'europe', 'occultation', 0.0, 0.0, 0.5)
    fio, feu = mu.flux_propre('io'), mu.flux_propre('europe')
    assert mu.resume(R.courbe())[0] == pytest.approx(fio / (fio + feu), rel=1e-12)
    # B trop grand : rien
    R = mu.Rencontre('europe', 'io', 'occultation', 1.0, 0.0, 0.5)
    assert R.b_limite() < 1.0 and mu.resume(R.courbe())[2] == 0.0


def test_mutuels_interface(app_qt):
    from coupole.modules.anim.animations.mutuels import Mutuels
    a = Mutuels()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Phénomène'] == '2\u202fO\u202f1 : Europe occulte Io'
    assert v['Baisse d’éclat maximale'] == '38,7 % (Δm = 0,53)'
    a.genre.setCurrentIndex(a.genre.findData('eclipse'))
    assert dict(a.valeurs())['Phénomène'] == '2\u202fE\u202f1 : Europe éclipse Io'
    a.passif.setCurrentIndex(a.passif.findData('europe'))           # même satellite : on prend le suivant
    assert a.paire() == ('europe', 'ganymede')
    for _ in range(5):
        a.pas(0.5)
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- traînées de météoroïdes (0.12.0)
def test_trainees_contre_sage():
    from coupole.modules.anim import trainees as tn
    s = sage('trainees')
    for k, r in tn.TAILLES:
        assert tn.beta(r) == pytest.approx(s['beta'][k], rel=1e-9)
    for lam, an, t in s['terre']:
        assert tn.date_terre(lam, an) == pytest.approx(t, abs=1e-8)
    for cas in s['grains']:
        orb = tn.orbite_comete(cas['comete'])
        P = orb.periode()
        tk = orb.t0 + round((cas['tk'] - orb.t0) / P) * P
        assert tk == pytest.approx(cas['tk'], abs=1e-7)
        grains = tn.ejecter(orb, tk, cas['dv'], cas['beta'], n=3, graine=cas['graine'])
        genre = tn.noeud_terrestre(orb)
        for o, ref in zip(grains, cas['grains']):
            r, lam, mn = tn.noeud(o, genre)
            tau0 = tk + ((mn - o.m0) % (2.0 * math.pi)) / o.n
            for j, (t_ref, r_ref) in enumerate(ref['noeuds']):
                assert tau0 + j * o.periode() == pytest.approx(t_ref, abs=2e-7), (cas['comete'], j)
                assert r == pytest.approx(r_ref, abs=1e-8)
            for t, x, y, z in ref['positions']:
                assert o.position(t) == pytest.approx((x, y, z), abs=2e-7)


def test_trainees_essaim():
    from coupole.modules.anim import trainees as tn
    # comète fictive : son nœud descendant est exactement sur l'orbite terrestre
    orb = tn.orbite_comete('fictive')
    r, lam, _ = tn.noeud(orb, 'desc')
    assert r == pytest.approx(tn.r_terre(lam), abs=1e-12)
    # les Léonides : nœud descendant, 17 novembre, la comète passe 0,0082 ua à l'intérieur
    orb = tn.orbite_comete('tempel_tuttle')
    assert tn.noeud_terrestre(orb) == 'desc'
    r, lam, _ = tn.noeud(orb, 'desc')
    assert r - tn.r_terre(lam) == pytest.approx(-0.00819, abs=1e-5)
    assert tn.date_terre(lam, 1999) == pytest.approx(1999.8784, abs=1e-4)
    a0, a1 = tn.fenetre('fictive')
    E = tn.Essaim('fictive', 10.0, 'mm', a0, a1)
    assert len(E.ejections) == 10 and all(len(g) == tn.N_GRAINS for _, g, _ in E.traines)
    act = E.activite(a0, a1)
    meilleures = sorted(act, key=lambda y: -act[y])[:6]
    # l'activité se concentre dans les années qui suivent un retour de la comète
    assert all(min(abs(y - tk) for tk in E.ejections) < 6.0 for y in meilleures)
    assert sum(act.values()) > 100


def test_trainees_interface(app_qt):
    from coupole.modules.anim.animations.trainees import Trainees
    a = Trainees()
    a.resize(1000, 700)
    v = dict(a.valeurs())
    assert v['Essaim'] == 'Léonides (55P/Tempel-Tuttle)'
    assert v['Nœud de la comète, écart à l’orbite terrestre'] == '0,9804 ua (Δr = −0,0082 ua)'
    assert v['La Terre au nœud'] in ('16 novembre', '17 novembre')
    assert v['Année la plus riche'] == '1865 (26 grains)'
    a.t = 1999.5
    v = dict(a.valeurs())
    assert v['Traînées lâchées'] == '8' and int(v['Grains rencontrés cette année (|Δr| < 0,01 ua, |Δt| < 10 j)']) > 10
    a.comete.setCurrentIndex(a.comete.findData('swift_tuttle'))
    assert dict(a.valeurs())['La Terre au nœud'] in ('11 août', '12 août')
    a.cadrage.setCurrentIndex(a.cadrage.findData('orbite'))
    for _ in range(5):
        a.pas(0.5)
    assert not a.image(900, 560).isNull()


# ---------------------------------------------------------------- orbites de halo (points de Lagrange, 0.12.0)
def test_halo_richardson_contre_sage():
    from coupole.modules.anim import lagrange as lg
    s = sage('halo')
    mus = {k: m for k, m, _ in lg.SYSTEMES}
    for c in s['cas']:
        mu = mus[c['systeme']]
        h = lg.halo(mu, c['point'], c['delta'])
        assert h.gamma == pytest.approx(c['gamma'], rel=1e-10)
        assert (h.Ax, h.Az) == pytest.approx((c['Ax'], c['Az']), rel=1e-9)
        assert h.periode() == pytest.approx(c['periode'], rel=1e-10)
        e = h.etat(0.0)
        assert e == pytest.approx(c['richardson'], abs=1e-12)
        # vraie orbite périodique (correction différentielle sous SageMath) : Richardson en est proche
        g, amp = c['gamma'], max(c['Ax'], c['Az']) * c['gamma']
        assert abs(c['corrige'][0] - e[0]) < 0.07 * amp, c
        assert c['corrige'][4] == pytest.approx(e[4], rel=0.05)
        assert c['demi_periode_corrigee'] == pytest.approx(h.periode() / 2.0, rel=3e-3)
        assert lg.depart(mu, 'halo_' + c['point'].lower(), c['delta']) == pytest.approx(e, abs=1e-15)


def test_halo_interface(app_qt):
    from coupole.modules.anim.animations.lagrange import Lagrange
    a = Lagrange()
    a.resize(1000, 700)
    a.systeme.setCurrentIndex(a.systeme.findData('soleil_terre'))
    a.cas.setCurrentIndex(a.cas.findData('halo_l1'))
    assert a.delta.value() == pytest.approx(0.01) and len(a.s) == 6
    v = dict(a.valeurs())
    assert v['Orbite de halo : amplitudes Ax, Ay, Az ; période'].endswith('176,8 jours')
    assert v['Écart du corps à l’orbite de Richardson'] == '0 km'
    a.pas(0.05)
    assert float(dict(a.valeurs())['Écart du corps à l’orbite de Richardson'].split()[0].replace(' ', '')
                 .replace(' ', '')) < 1000.0
    assert not a.image(900, 560).isNull()
    a.cas.setCurrentIndex(a.cas.findData('tetard'))
    assert len(a.s) == 4 and 'Orbite de halo : amplitudes Ax, Ay, Az ; période' not in dict(a.valeurs())


# ---------------------------------------------------------------- anneaux de Newton (interférométrie, 0.12.0)
def test_newton_contre_sage():
    from coupole.modules.anim import interferometrie as itf
    s = sage('newton')
    for R, lam, n, cote, k, r_mince, r_exact in s['rayons']:
        r = itf.rayon_sombre(k, R, lam, n, cote)
        assert r == pytest.approx(r_mince, rel=1e-12)
        assert r == pytest.approx(r_exact, rel=2e-4)                   # lame mince : e ≈ r²/2R
        assert itf.newton(r, R, lam, n, cote) == pytest.approx(0.0, abs=1e-12)
    for n, ph, fresnel, modele, contraste in s['fresnel']:
        assert fresnel == pytest.approx(modele, abs=1e-12) and contraste < 1e-3
        e = ph * 589.0 / (4.0 * math.pi * n)
        assert itf.newton_e(e, 589.0, n, 'reflexion') == pytest.approx(modele, abs=1e-12)
    for R, lam, n, r_mm, I in s['eclairement']:
        assert itf.newton(r_mm, R, lam, n) == pytest.approx(I, abs=0.04)    # e exact contre r²/2R


def test_newton_interface(app_qt):
    from coupole.modules.anim.animations.interferometrie import Interferometrie
    a = Interferometrie()
    a.resize(1000, 700)
    assert not a.rayon.isVisible() or a.rayon.isHidden()
    a.montage.setCurrentIndex(a.montage.findData('anneaux'))
    a.lam.setValue(589.0)
    v = dict(a.valeurs())
    assert v['Anneaux sombres r₁, r₂, r₃ = √(kλR/n)'] == '0,767 ; 1,085 ; 1,329 mm'
    assert v['Épaisseur de la lame au 1ᵉʳ anneau'] == '294 nm'
    a.indice.setValue(1.33)
    assert dict(a.valeurs())['Anneaux sombres r₁, r₂, r₃ = √(kλR/n)'].startswith('0,665')
    a.c_blanche.setChecked(True)
    a.cote.setCurrentIndex(a.cote.findData('transmission'))
    assert dict(a.valeurs())['Centre (lentille au contact)'] == 'clair'
    assert not a.image(900, 560).isNull()
    a.montage.setCurrentIndex(a.montage.findData('interferometre'))
    assert 'Interfrange λ / B' in ' '.join(k for k, _ in a.valeurs()) or len(a.valeurs()) > 4
