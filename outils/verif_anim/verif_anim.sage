# Vérification indépendante des calculs du module « Animations » (SageMath, 100 bits, sans le code de Coupole).
#
#   sage outils/verif_anim/verif_anim.sage tests/anim_reference_sage.json
#
# Chaque grandeur est recalculée ici à partir de sa définition (rotations, racines numériques, triangles
# semblables…) plutôt qu'en recopiant les formules fermées de coupole/modules/anim/astro.py ; le fichier JSON produit
# est relu par tests/test_anim_calculs.py, qui compare le code de Coupole à ces valeurs.
import json
import sys

R = RealField(100)
PI = R(pi)
D = PI / 180
SORTIE = sys.argv[1] if len(sys.argv) > 1 else 'anim_reference_sage.json'
from sage.version import version as VERSION_SAGE
ref = {'outil': 'SageMath %s' % VERSION_SAGE, 'precision_bits': 100}


def md(x, m):
    """Reste positif de x modulo m, en réels (le % de Sage refuse les expressions symboliques)."""
    x = R(x)
    return x - m * floor(x / m)


# ------------------------------------------------------------------ jour julien (définition : jours depuis -4712)
def jj(a, m, j, h=0):
    # comptage direct des jours du calendrier grégorien depuis 2000-01-01 12 h TU (JJ 2451545,0)
    from datetime import date
    n = (date(a, m, int(j)) - date(2000, 1, 1)).days
    return R(2451545) + n - R(1) / 2 + (R(j) - int(j)) + R(h) / 24


ref['jour_julien'] = [[a, m, j, h, float(jj(a, m, j, h))] for a, m, j, h in
                      [(2000, 1, 1, 12), (1987, 4, 10, 0), (1992, 10, 13, 0), (2026, 1, 1, 0), (2026, 3, 20, 14.75),
                       (1957, 10, 4.81, 0), (2100, 2, 28, 18)]]


# ------------------------------------------------------------------ temps sidéral moyen de Greenwich (IAU 1982)
# GMST(0 h TU) = 24110,54841 s + 8640184,812866 T + 0,093104 T² − 6,2e−6 T³ (secondes), + 1,00273790935 × TU
def gmst_secondes(jd):
    jd0 = (jd - R(1) / 2).floor() + R(1) / 2
    tu = (jd - jd0) * 86400
    t = (jd0 - 2451545) / 36525
    s = R('24110.54841') + R('8640184.812866') * t + R('0.093104') * t ** 2 - R('6.2e-6') * t ** 3
    tp = (jd - 2451545) / 36525
    r = R('1.002737909350795') + R('5.9006e-11') * tp - R('5.9e-15') * tp ** 2
    return md(s + r * tu, 86400)


ref['tsmg'] = []
for a, m, j, h in [(1987, 4, 10, 0), (1987, 4, 10, 19 + R(21) / 60), (2000, 1, 1, 12), (2026, 6, 21, 22.5),
                   (2026, 12, 31, 3.25), (2012, 2, 29, 0)]:
    jd = jj(a, m, j, h)
    ref['tsmg'].append([float(jd), float(gmst_secondes(jd) / 240)])           # degrés
# exemples 12.a et 12.b de Meeus : 13 h 10 min 46,3668 s et 8 h 34 min 57,0896 s
ref['tsmg_meeus'] = [[float(jj(1987, 4, 10, 0)), (13 * 3600 + 10 * 60 + 46.3668) / 240],
                     [float(jj(1987, 4, 10, 19 + R(21) / 60)), (8 * 3600 + 34 * 60 + 57.0896) / 240]]


# ------------------------------------------------------------------ obliquité moyenne (P03 / IAU 2006)
def obliquite(jd):
    t = (jd - 2451545) / 36525
    s = R('84381.406') - R('46.836769') * t - R('0.0001831') * t ** 2 + R('0.00200340') * t ** 3 \
        - R('5.76e-7') * t ** 4 - R('4.34e-8') * t ** 5
    return s / 3600


ref['obliquite'] = [[float(jd), float(obliquite(jd))] for jd in
                    [jj(2000, 1, 1, 12), jj(2026, 1, 1), jj(1900, 1, 1), jj(2100, 1, 1), jj(1000, 1, 1)]]


# ------------------------------------------------------------------ Soleil (algorithme de Meeus, chap. 25, en 100 bits)
def soleil(jd):
    t = (jd - 2451545) / 36525
    l0 = md(R('280.46646') + R('36000.76983') * t + R('0.0003032') * t ** 2, 360)
    m = md(R('357.52911') + R('35999.05029') * t - R('0.0001537') * t ** 2, 360)
    c = (R('1.914602') - R('0.004817') * t - R('0.000014') * t ** 2) * sin(m * D) + \
        (R('0.019993') - R('0.000101') * t) * sin(2 * m * D) + R('0.000289') * sin(3 * m * D)
    om = R('125.04') - R('1934.136') * t
    lam = l0 + c - R('0.00569') - R('0.00478') * sin(om * D)
    eps = obliquite(jd) + R('0.00256') * cos(om * D)
    # (α, δ) par rotation d'axe x d'angle ε du vecteur écliptique (cos λ, sin λ, 0)
    v = matrix(R, 3, 1, [cos(lam * D), sin(lam * D), 0])
    rx = matrix(R, [[1, 0, 0], [0, cos(eps * D), -sin(eps * D)], [0, sin(eps * D), cos(eps * D)]])
    w = rx * v
    alpha = md(R(atan2(w[1, 0], w[0, 0])) / D, 360)
    delta = asin(w[2, 0]) / D
    e = l0 - R('0.0057183') - alpha + (-R('0.00478') * sin(om * D)) * cos(eps * D)
    e = md(e + 180, 360) - 180
    return float(md(lam, 360)), float(alpha), float(delta), float(4 * e)


ref['soleil'] = []
for a, m, j, h in [(1992, 10, 13, 0), (2026, 3, 20, 12), (2026, 6, 21, 0), (2026, 9, 23, 6), (2026, 12, 21, 18),
                   (2026, 2, 11, 0), (2026, 11, 3, 0), (2010, 7, 26, 0)]:
    ref['soleil'].append([float(jj(a, m, j, h))] + list(soleil(jj(a, m, j, h))))
# exemple 25.a de Meeus (1992-10-13 0 h TD) : λ = 199,90895°, α = 198,38083°, δ = −7,78507° ; éq. du temps 13 min 42,6 s
ref['soleil_meeus'] = {'jj': float(jj(1992, 10, 13)), 'lambda': 199.90895, 'alpha': 198.38083, 'delta': -7.78507,
                       'eqt_min': 13 + 42.6 / 60}


# ------------------------------------------------------------------ repère équatorial → horizontal (par rotations)
def horizon(h, dec, lat):
    # vecteur (H, δ) dans le repère (méridien, est… ) : x vers H = 0, y vers H = −90° (est), z pôle
    v = matrix(R, 3, 1, [cos(dec * D) * cos(h * D), -cos(dec * D) * sin(h * D), sin(dec * D)])
    # rotation autour de l'axe est d'angle (90° − φ) : le pôle passe au zénith incliné
    c = 90 - R(lat)
    ry = matrix(R, [[cos(c * D), 0, -sin(c * D)], [0, 1, 0], [sin(c * D), 0, cos(c * D)]])
    w = ry * v                                      # x vers le sud-haut… ; on lit (sud, est, zénith)
    sud, est, zen = w[0, 0], w[1, 0], w[2, 0]
    az = md(R(atan2(est, -sud)) / D, 360)               # depuis le nord vers l'est
    return float(az), float(asin(zen) / D)


ref['horizon'] = []
for h, dec, lat in [(0, 0, 45), (-90, 0, 45), (90, 0, 45), (30, 20, 48.85), (-75, -10, 48.85), (150, 70, 60),
                    (10, -50, -33.9), (-120, 23.44, 66.56), (45, 89, 10), (200, -5, 0)]:
    ref['horizon'].append([h, dec, lat] + list(horizon(R(h), R(dec), R(lat))))


# ------------------------------------------------------------------ lever et coucher : racine de la hauteur
def h0_racine(dec, lat, h0):
    f = lambda H: sin(R(lat) * D) * sin(R(dec) * D) + cos(R(lat) * D) * cos(R(dec) * D) * cos(H * D) - sin(R(h0) * D)
    if f(R(180)) > 0:
        return 180.0
    if f(R(0)) < 0:
        return 0.0
    return float(find_root(f, 0, 180))


ref['lever'] = [[d, l, h0, h0_racine(d, l, h0)] for d, l, h0 in
                [(0, 45, 0), (23.44, 48.85, 0), (-23.44, 48.85, -0.833), (23.44, 48.85, -0.833), (10, 70, 0),
                 (-30, 70, 0), (5, 0, 0), (-12, -45, -0.833)]]


# ------------------------------------------------------------------ équation de Kepler, vis-viva, 3e loi
GM = R('1.32712440018e20')
UA = R('149597870700')
ref['kepler'] = []
for m_deg, e in [(5, 0.1), (60, 0.0167), (180, 0.5), (300, 0.7), (10, 0.9), (123.4, 0.249)]:
    ee = find_root(lambda x: x - e * sin(x) - R(m_deg) * D, 0, 2 * PI)
    ref['kepler'].append([m_deg, e, float(ee)])
ref['vis_viva'] = []
for a, e, f in [(1, 0.0167, 0), (1, 0.0167, 0.5), (1.524, 0.093, 0.25), (39.44, 0.249, 0.1), (5.203, 0.048, 0.7)]:
    m = 2 * PI * R(f)
    ee = find_root(lambda x: x - e * sin(x) - m, -1, 2 * PI + 1)
    r = R(a) * (1 - e * cos(ee))
    v = sqrt(GM * (2 / (r * UA) - 1 / (R(a) * UA))) / 1000
    ref['vis_viva'].append([a, e, f, float(r), float(v)])
ref['periode'] = [[a, float(R(a) ** R(1.5))] for a in (0.387, 1, 1.524, 5.203, 30.06, 39.44)]
# période sidérale de la Terre par la constante de gravitation : 2π √(a³/GM) en jours (contrôle de cohérence)
ref['annee_kepler_j'] = float(2 * PI * sqrt(UA ** 3 / GM) / 86400)


# ------------------------------------------------------------------ parsec, année-lumière, module de distance
pc = UA * 648000 / PI
al = R(299792458) * R('31557600')
ref['pc_en_al'] = float(pc / al)
ref['module'] = [[d, float(5 * log(R(d), 10) - 5)] for d in (1, 10, 100, 1000, 1.3012, 8.61)]


# ------------------------------------------------------------------ ombre de la Terre (triangles semblables)
rs, rt, rl, dl, ds = R(695700), R('6378.137'), R('1737.4'), R(384400), UA / 1000
lunaison = R('29.530588861')
L = ds * rt / (rs - rt)                     # sommet du cône : rt / L = rs / (L + ds)
ru = rt * (L - dl) / L
lp = ds * rt / (rs + rt)                     # cône de pénombre : sommet entre la Terre et le Soleil
rp = rt * (lp + dl) / lp
v = 2 * PI * dl / (lunaison * 24)
ref['eclipse_lune'] = {'longueur_ombre_km': float(L), 'rayon_ombre_km': float(ru), 'rayon_penombre_km': float(rp),
                       'ombre_en_diametres_lunaires': float(ru / rl), 'totalite_h': float(2 * (ru - rl) / v),
                       'ombre_totale_h': float(2 * (ru + rl) / v), 'penombre_h': float(2 * (rp + rl) / v)}


# ------------------------------------------------------------------ rétrogradation (orbites circulaires coplanaires)
def lam_geo(a, t):
    p = R(a) ** R(1.5)
    xp, yp = R(a) * cos(2 * PI * t / p), R(a) * sin(2 * PI * t / p)
    xt, yt = cos(2 * PI * t), sin(2 * PI * t)
    return atan2(yp - yt, xp - xt)


ref['retrogradation'] = []
for a in (1.524, 5.203, 9.54):
    tt = var('tt')
    dl_ = diff(lam_geo(a, tt), tt)
    ts = find_root(lambda x: dl_.subs(tt=x), R(1e-6), R(0.5) / (1 - 1 / R(a) ** R(1.5)) * R(0.999))
    amp = 2 * abs(lam_geo(a, R(ts)) - lam_geo(a, 0)) / D
    ref['retrogradation'].append([a, float(2 * ts * R('365.25')), float(amp)])


# ------------------------------------------------------------------ modèle de Ptolémée : propriétés de l'équant
ref['ptolemee'] = []
for t in (0, 0.3, 1.0, 1.881 / 2, 2.5):
    k = (R('3.53') - R('106.67')) * D + 2 * PI * R(t) / R('1.881')
    # le centre de l'épicycle est sur le déférent (centre (6, 0), rayon 60) dans la direction κ vue de l'équant (12, 0)
    s = var('s')
    m = find_root((12 + s * cos(k) - 6) ** 2 + (s * sin(k)) ** 2 - 3600, 0, 200)
    ref['ptolemee'].append([t, float(12 + m * cos(k)), float(m * sin(k))])

# ------------------------------------------------------------------ jour sidéral
ref['jour_sideral'] = [[y, float(86400 * R(y) / (R(y) + 1))] for y in (365, 365.25, 365.24219)]

# ================================================================== lot 2 (0.3.1) : Lune, Renaissance, antique
GSI = R('6.67430e-11')
GMT = R('3.986004418e14')
MT = GMT / GSI
ML = MT / R('81.300568')
MS = GM / GSI


# ------------------------------------------------------------------ périodes synodiques : retour de l'alignement
def synodique_par_racine(p1, p2):
    # premier instant > 0 où l'écart angulaire 2π t (1/p1 − 1/p2) atteint un tour
    f = lambda t: 2 * PI * t * (1 / R(p1) - 1 / R(p2)) - 2 * PI * sign(1 / R(p1) - 1 / R(p2))
    return abs(find_root(f, R('1e-6'), R(1e6)))


ref['synodique'] = [[p1, p2, float(synodique_par_racine(p1, p2))] for p1, p2 in
                    [(1, 1.8808), (1, 0.6152), (1, 11.862), (1, 0.2408), (1, 29.457), (27.321661, 365.256363)]]
ref['kepler3_inverse'] = [[pp, m, float(find_root(lambda a: a ** 3 - m * R(pp) ** 2, R('1e-6'), R(1e6)))]
                          for pp, m in [(1, 1), (11.862, 1), (0.2408, 1), (100, 2.5), (0.01, 0.3)]]

# ------------------------------------------------------------------ gravitation et satellites de la Terre
ref['gravitation'] = [[m1, m2, r, float(GSI * R(m1) * R(m2) / R(r) ** 2)] for m1, m2, r in
                      [(0.102, float(MT), 6.371e6), (72, 72, 2), (9.1093837e-31, 1.6726219e-27, 1e-10),
                       (float(MS), float(MT), 149597870700)]]
ref['orbite_terre'] = []
for r in (6378137, 6798000, 26560000, 384400000):
    pp = 2 * PI * sqrt(R(r) ** 3 / GMT)
    ref['orbite_terre'].append([r, float(pp), float(sqrt(GMT / R(r)))])
jsid = 86400 * R('365.256363004') / (R('365.256363004') + 1)     # rotation par rapport aux étoiles (année sidérale)
ref['geostationnaire'] = {'jour_sideral_s': float(jsid),
                          'rayon_m': float(find_root(lambda r: 2 * PI * sqrt(r ** 3 / GMT) - jsid, R(1e7), R(1e8)))}
ref['lune_periode_deux_corps_j'] = float(2 * PI * sqrt(R(384400000) ** 3 / (GMT * (1 + 1 / R('81.300568')))) / 86400)

# ------------------------------------------------------------------ petits angles
ref['petits_angles'] = [[d, dd, float(2 * asin(R(d) / (2 * R(dd))) * 648000 / PI), float(R(d) / R(dd) * 648000 / PI)]
                        for d, dd in [(2, 50), (1, 20), (3, 2), (12742, 384400), (3474.8, 384400)]]

# ------------------------------------------------------------------ marées d'équilibre
RT = R('6378137')
k_l = ML / MT * (RT / R(384400000)) ** 3 * RT
k_s = MS / MT * (RT / (UA)) ** 3 * RT
ref['marees'] = {'amplitude_lune_m': float(k_l), 'rapport_soleil_lune': float(k_s / k_l),
                 'marnage_lune_m': float(k_l * R(3) / 2)}

# ------------------------------------------------------------------ Vénus : élongation et phase par la loi des cosinus
ref['venus'] = []
for av, at in [(28.6479, 0), (10, 0), (180, 0), (90, 0), (300, 45), (46.3, 0)]:
    gamma = (R(at) - R(av)) * D                    # angle au Soleil entre la Terre et Vénus
    a = R('0.723332')
    d = sqrt(1 + a * a - 2 * a * cos(gamma))
    elong = acos((1 + d * d - a * a) / (2 * d)) / D              # angle à la Terre
    i = acos((a * a + d * d - 1) / (2 * a * d)) / D             # angle de phase, à Vénus
    ref['venus'].append([av, at, float(d), float(elong), float(i)])
# plus grande élongation : maximum de l'élongation, par la dérivée
a = R('0.723332')
el = lambda g: acos((1 + (1 + a * a - 2 * a * cos(g)) - a * a) / (2 * sqrt(1 + a * a - 2 * a * cos(g))))
gg = var('gg')
gmax = find_root(diff(el(gg), gg), R(0.1), R(1.5))
ref['venus_elongation_max'] = float(el(R(gmax)) / D)

# ------------------------------------------------------------------ configurations : instants des quadratures et élongations
ref['configurations'] = []
for a_obs, a_c in [(1, 2.4), (1, 1.523679), (1, 0.723332), (1.523679, 1), (1, 5.2026)]:
    p1, p2 = R(a_obs) ** R(1.5), R(a_c) ** R(1.5)
    s = 1 / abs(1 / p1 - 1 / p2)
    def angle_terre(t):
        th1, th2 = 2 * PI * t / p1, 2 * PI * t / p2
        x1, y1, x2, y2 = R(a_obs) * cos(th1), R(a_obs) * sin(th1), R(a_c) * cos(th2), R(a_c) * sin(th2)
        u = vector([x2 - x1, y2 - y1]); v = vector([-x1, -y1])
        return acos(u.dot_product(v) / (u.norm() * v.norm()))
    if a_c > a_obs:      # quadrature : angle de 90° à l'observateur
        t1 = find_root(lambda t: angle_terre(t) - PI / 2, R('1e-9'), s / 2 - R('1e-9'))
    else:                # plus grande élongation : maximum de l'angle à l'observateur
        tt = var('tt')
        t1 = find_root(lambda t: (angle_terre(t + R('1e-7')) - angle_terre(t - R('1e-7'))), R('1e-6'), s / 2 - R('1e-6'))
    ref['configurations'].append([a_obs, a_c, float(s), float(t1)])

# ------------------------------------------------------------------ Lune : phases moyennes, F, Soleil aux nœuds
def phase_moyenne(k):
    k = R(k); tt = k / R('1236.85')
    return R('2451550.09766') + R('29.530588861') * k + R('0.00015437') * tt ** 2 - R('0.000000150') * tt ** 3 \
        + R('0.00000000073') * tt ** 4


def arg_lat(k):
    k = R(k); tt = k / R('1236.85')
    return md(R('160.7108') + R('390.67050284') * k - R('0.0016118') * tt ** 2 - R('0.00000227') * tt ** 3
              + R('0.000000011') * tt ** 4, 360)


ref['phases_moyennes'] = [[k, float(phase_moyenne(k)), float(arg_lat(k))] for k in (0, 0.5, 326, 329, 329.5, 500.5, -10)]


def noeud(jd):
    t = (jd - 2451545) / 36525
    return md(R('125.0445479') - R('1934.1362891') * t + R('0.0020754') * t ** 2 + t ** 3 / 467441 - t ** 4 / 60616000,
              360)


ref['soleil_noeuds_2026'] = []
for cible, j0 in ((0, jj(2026, 2, 20)), (180, jj(2026, 8, 18))):
    f = lambda x: (md(R(soleil(R(x))[0]) - noeud(R(x)) - cible + 180, 360) - 180)
    ref['soleil_noeuds_2026'].append([cible, float(find_root(f, j0 - 15, j0 + 15))])

# ------------------------------------------------------------------ précession (IAU 1976) par matrices de rotation
def precession_sage(ra, dec, jd):
    t = (R(jd) - 2451545) / 36525
    zeta = (R('2306.2181') * t + R('0.30188') * t ** 2 + R('0.017998') * t ** 3) / 3600 * D
    z = (R('2306.2181') * t + R('1.09468') * t ** 2 + R('0.018203') * t ** 3) / 3600 * D
    th = (R('2004.3109') * t - R('0.42665') * t ** 2 - R('0.041833') * t ** 3) / 3600 * D
    rz = lambda a: matrix(R, [[cos(a), -sin(a), 0], [sin(a), cos(a), 0], [0, 0, 1]])
    ry = lambda a: matrix(R, [[cos(a), 0, -sin(a)], [0, 1, 0], [sin(a), 0, cos(a)]])
    m = rz(z) * ry(th) * rz(zeta)
    v = m * matrix(R, 3, 1, [cos(R(dec) * D) * cos(R(ra) * D), cos(R(dec) * D) * sin(R(ra) * D), sin(R(dec) * D)])
    return float(md(R(atan2(v[1, 0], v[0, 0])) / D, 360)), float(asin(v[2, 0]) / D)


ref['precession'] = [[ra, dec, float(jd), *precession_sage(ra, dec, jd)] for ra, dec, jd in
                     [(101.287155, -16.716116, jj(2026, 1, 1)), (279.234735, 38.783689, jj(2026, 7, 1)),
                      (37.954561, 89.264109, jj(2026, 1, 1)), (10, 20, jj(2100, 1, 1)), (300, -60, jj(1950, 1, 1))]]


# ------------------------------------------------------------------ lever héliaque (modèle de l'original : horizon, Soleil à −7°)
def hauteur_aube(ra, dec, lat, jour, dep=7):
    jd = jj(2026, 1, 1) + jour + R(1) / 2
    lam, alpha, delta, eqt = soleil(jd)
    p_, d_ = R(lat) * D, R(delta) * D
    c = (sin(-R(dep) * D) - sin(p_) * sin(d_)) / (cos(p_) * cos(d_))
    if abs(c) >= 1:
        return None
    hh = acos(c) / D
    tsl = R(alpha) - hh
    ra2, de2 = precession_sage(ra, dec, jd)
    hs = (tsl - R(ra2)) * D
    return float(asin(sin(p_) * sin(R(de2) * D) + cos(p_) * cos(R(de2) * D) * cos(hs)) / D)


ref['heliaque'] = []
for nom, ra, dec in (('sirius', 101.287155, -16.716116), ('vega', 279.234735, 38.783689),
                     ('aldebaran', 68.980163, 16.509302)):
    h = [hauteur_aube(ra, dec, 40.8, j) for j in range(365)]
    vis = [x is not None and x > 0 for x in h]
    jours = [j for j in range(365) if vis[j] and not vis[j - 1]]
    ref['heliaque'].append([nom, ra, dec, 40.8, jours, [[j, h[j]] for j in (0, 100, 200, 300)]])

# ------------------------------------------------------------------ pleine lune : déclinaison d'un point de latitude écliptique β
def dec_ecl(lam, beta, eps):
    v = matrix(R, 3, 1, [cos(R(beta) * D) * cos(R(lam) * D), cos(R(beta) * D) * sin(R(lam) * D), sin(R(beta) * D)])
    rx = matrix(R, [[1, 0, 0], [0, cos(R(eps) * D), -sin(R(eps) * D)], [0, sin(R(eps) * D), cos(R(eps) * D)]])
    return float(asin((rx * v)[2, 0]) / D)


ref['dec_ecliptique'] = [[lam, beta, eps, dec_ecl(lam, beta, eps)] for lam, beta, eps in
                         [(90, 5.145, 23.436), (270, -5.145, 23.436), (0, 5.145, 23.436), (135, 0, 23.44)]]


# ------------------------------------------------------------------ propriétés stellaires (lot 2 bis)
SIG = R('5.670374419e-8')
RSOL, LSOL = R('6.957e8'), R('3.828e26')
TSOL = find_root(lambda tt: 4 * PI * RSOL ** 2 * SIG * tt ** 4 - LSOL, R(5000), R(6500))
ref['stellaire'] = {'t_soleil': float(TSOL),
                    'ua_par_an_km_s': float(UA / 1000 / (R('365.25') * 86400)),
                    'luminosites': [[r, tt, float((R(r) * RSOL) ** 2 * 4 * PI * SIG * R(tt) ** 4 / LSOL)]
                                    for r, tt in [(1, 5830), (0.01, 9480), (100, 3800), (10, 38000)]],
                    'flux': [[w, d, float(R(w) / (4 * PI * R(d) ** 2))] for w, d in [(25, 1), (100, 2.5), (500, 5)]],
                    'doppler': [[lam, float(R('299792.458') * (R(lam) - R('656.28')) / R('656.28')),
                                 float(R('299792.458') * ((R(lam) / R('656.28')) ** 2 - 1) / ((R(lam) / R('656.28')) ** 2 + 1))]
                                for lam in (655, 656.28, 656.5, 657)],
                    'distances': [[m, mm, float(10 ** ((R(m) - R(mm) + 5) / 5))] for m, mm in
                                  [(1, 4.84), (-1.46, 1.42), (11.13, 15.53), (0, 0)]]}


def natif(x):
    """Nombres de Sage (Integer, RealNumber) → int / float de Python, pour le JSON."""
    if isinstance(x, dict):
        return {k: natif(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [natif(v) for v in x]
    if isinstance(x, str):
        return x
    if x in ZZ:
        return int(x)
    return float(x)


json.dump(natif(ref), open(SORTIE, 'w'), indent=1)
print('écrit', SORTIE)
