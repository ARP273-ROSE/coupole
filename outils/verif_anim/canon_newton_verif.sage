# Vérification SageMath de l'animation « Le canon de Newton » (idée des Principia, 1687 ; code propre à Coupole).
# Tout est recalculé ici depuis les définitions, sans le code de Coupole : constantes des astres, vitesses de
# satellisation √(GM/r) et de libération √(2GM/r), éléments des orbites des préréglages (énergie, moment cinétique,
# vecteur excentricité), période de Kepler, point et instant d'impact des tirs qui retombent (équation de Kepler,
# racine numérique), vitesse qui mène aux antipodes, et intégrations indépendantes (DOP853 de SciPy, tolérance
# 1e-12) des tirs avec air (rentrée d'une capsule, orbite basse d'un satellite qui se dégrade, boulet freiné).
# Constantes (sources) :
#   G = 6,67430e-11 m³ kg⁻¹ s⁻²                               CODATA 2018 (inchangée en 2022)
#   Terre : GM = 3,986004e14 m³ s⁻², R = 6 378,1 km             UAI 2015, résolution B3 (valeurs nominales)
#   Lune : GM = 4,902800118e12 m³ s⁻² (DE440), R = 1 737,4 km   Park et al. 2021 ; NASA Moon Fact Sheet
#   Mars : GM = 42 828,375816 km³ s⁻² (DE440), R = 3 389,5 km   Park et al. 2021 ; Archinal et al. 2018 (rayon moyen)
#   Cérès : GM = 62,62905 km³ s⁻², V = 434,13e6 km³             Park et al. 2019 (Dawn) ; R de la sphère de même volume
#   Dimorphos : M = 4,3e9 kg, diamètre équivalent 151 m         Daly et al. 2023 (DART)
#   Atmosphère terrestre : modèle exponentiel par tranches 0–1 000 km (CIRA-72 ; Vallado 2013, tableau 8-4)
#   Atmosphère martienne : ρ₀ = 0,020 kg m⁻³, H = 11,1 km       NASA, Mars Fact Sheet
# Usage : sage outils/verif_anim/canon_newton_verif.sage   (écrit tests/canon_newton_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
import numpy as np
from scipy.integrate import solve_ivp

R = RealField(120)
PI = R(pi)
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'canon_newton_sage.json'))

G = R('6.67430e-11')
R_CERES = (3 * R('434.13e6') * R(10) ** 9 / (4 * PI)) ** (R(1) / 3)
ASTRES = {
    'terre': (R('3.986004e14'), R('6.3781e6')),
    'lune': (R('4.902800118e12'), R('1.7374e6')),
    'mars': (R('4.2828375816e13'), R('3.3895e6')),
    'ceres': (R('6.262905e10'), R_CERES),
    'dimorphos': (G * R('4.3e9'), R('151') / 2),
}
# altitudes des réglages (m) : défaut et « au ras du sol »
A0 = {'terre': 100000, 'lune': 10000, 'mars': 50000, 'ceres': 10000, 'dimorphos': 10}
RAS = {'terre': 10000, 'lune': 2000, 'mars': 10000, 'ceres': 2000, 'dimorphos': 2}
V0 = {'terre': 5000, 'lune': 1000, 'mars': 2500, 'ceres': 200, 'dimorphos': R('0.04')}
ALT_ISS = R(415000)

TERRE = [(0, '1.225', '7.249'), (25, '3.899e-2', '6.349'), (30, '1.774e-2', '6.682'), (40, '3.972e-3', '7.554'),
         (50, '1.057e-3', '8.382'), (60, '3.206e-4', '7.714'), (70, '8.770e-5', '6.549'), (80, '1.905e-5', '5.799'),
         (90, '3.396e-6', '5.382'), (100, '5.297e-7', '5.877'), (110, '9.661e-8', '7.263'), (120, '2.438e-8', '9.473'),
         (130, '8.484e-9', '12.636'), (140, '3.845e-9', '16.149'), (150, '2.070e-9', '22.523'),
         (180, '5.464e-10', '29.740'), (200, '2.789e-10', '37.105'), (250, '7.248e-11', '45.546'),
         (300, '2.418e-11', '53.628'), (350, '9.518e-12', '53.298'), (400, '3.725e-12', '58.515'),
         (450, '1.585e-12', '60.828'), (500, '6.967e-13', '63.822'), (600, '1.454e-13', '71.835'),
         (700, '3.614e-14', '88.667'), (800, '1.170e-14', '124.64'), (900, '5.245e-15', '181.05'),
         (1000, '3.019e-15', '268.00')]
TERRE = [(float(h) * 1000, float(r), float(H) * 1000) for h, r, H in TERRE]
B = {'boulet': 1300.0, 'capsule': 350.0, 'satellite': 50.0}


def rho(astre, h):
    if astre == 'terre':
        if h > 2.5e6:
            return 0.0
        h0, r0, H = TERRE[0]
        for t in TERRE:
            if t[0] <= h:
                h0, r0, H = t
        return r0 * np.exp(-(h - h0) / H)
    if astre == 'mars':
        return 0.0 if h > 40 * 11100.0 else 0.020 * np.exp(-h / 11100.0)
    return 0.0


def orbite(mu, Rp, alt, v, ang_deg=0):
    """Éléments de l'orbite d'un tir depuis (0, R + alt) à v, ang au-dessus de l'horizontale (vers +x)."""
    a_ = R(ang_deg) * PI / 180
    r = vector(R, [0, Rp + alt])
    w = vector(R, [v * cos(a_), v * sin(a_)])
    rn = r.norm()
    eps = w.dot_product(w) / 2 - mu / rn
    h = r[0] * w[1] - r[1] * w[0]
    ev = ((w.dot_product(w) - mu / rn) * r - r.dot_product(w) * w) / mu
    e = ev.norm()
    p = h ** 2 / mu
    rp = p / (1 + e)
    out = {'v1': float(sqrt(mu / rn)), 'v2': float(sqrt(2 * mu / rn)), 'eps': float(eps), 'e': float(e),
           'rp': float(rp), 'v': float(v)}
    if eps < 0:
        a = -mu / (2 * eps)
        out['ra'] = float(a * (1 + e))
        out['T'] = float(2 * PI * sqrt(a ** 3 / mu))
    # impact : r(ν) = R sur le chemin, en partant de ν0, dans le sens du mouvement (h < 0 : sens horaire)
    if rp < Rp and eps < 0:
        sens = -1 if h < 0 else 1
        ux, uy = ev[0] / e, ev[1] / e
        nu0 = atan2(sens * (ux * r[1] - uy * r[0]), ux * r[0] + uy * r[1])
        nui = arccos((p / Rp - 1) / e)        # dans ]0, π[ : branche qui revient vers le périgée, ν = 2π − nui
        nu_i = 2 * PI - nui
        while nu_i < nu0:
            nu_i += 2 * PI
        a = -mu / (2 * eps)
        n = sqrt(mu / a ** 3)

        def M(nu):
            E = 2 * atan(sqrt((1 - e) / (1 + e)) * tan(nu / 2))
            return E - e * sin(E)
        # temps entre ν0 et ν_i (tours entiers du demi-angle gérés par la boucle de 2π)
        def t_de(nu):
            k = floor((nu + PI) / (2 * PI))
            return (M(nu - 2 * PI * k) + 2 * PI * k) / n
        out['impact_deg'] = float((nu_i - nu0) * 180 / PI)
        out['impact_s'] = float(t_de(nu_i) - t_de(nu0))
    return out


res = {'outil': 'SageMath %s' % VERSION_SAGE, 'constantes': {'G': float(G)},
       'astres': {k: {'gm': float(m), 'r': float(r)} for k, (m, r) in ASTRES.items()}}

# vitesses à la surface et aux altitudes des réglages
res['vitesses'] = {}
for k, (mu, Rp) in ASTRES.items():
    res['vitesses'][k] = {
        'surface': {'v1': float(sqrt(mu / Rp)), 'v2': float(sqrt(2 * mu / Rp))},
        'defaut': orbite(mu, Rp, R(A0[k]), R(V0[k])),
    }

# préréglages (même définition que l'animation : e = v²/v₁² − 1 au-delà de v₁ pour un tir horizontal)
pre = {}
for k, (mu, Rp) in ASTRES.items():
    for nom, alt, f in (('pied', A0[k], R('0.3')), ('ras_sol', RAS[k], R(1)), ('ellipse', A0[k], sqrt(R('1.5'))),
                        ('liberation', A0[k], sqrt(R(2))), ('hyperbole', A0[k], sqrt(R(3)))):
        v1 = sqrt(mu / (Rp + alt))
        pre['%s_%s' % (nom, k)] = dict(orbite(mu, Rp, R(alt), f * v1), astre=k, altitude=float(alt))
mu, Rp = ASTRES['terre']
pre['iss'] = dict(orbite(mu, Rp, ALT_ISS, sqrt(mu / (Rp + ALT_ISS))), astre='terre', altitude=float(ALT_ISS))
r0, rp = Rp + 200000, Rp + 60000
pre['rentree'] = dict(orbite(mu, Rp, R(200000), sqrt(mu / r0) * sqrt(2 * rp / (r0 + rp))), astre='terre',
                      altitude=200000.0)
res['prereglages'] = pre

# tirs du défaut et tir incliné (sans air)
res['tirs'] = {
    'terre_5kms_45deg': orbite(mu, Rp, R(100000), R(5000), 45),
    'lune_1kms_30deg': orbite(*ASTRES['lune'], R(10000), R(1000), 30),
}
# antipodes : depuis 100 km, tir horizontal qui touche le sol au périgée (r_p = R) : v = √(2 μ R / (r0 (r0 + R)))
r0 = Rp + 100000
v_anti = sqrt(2 * mu * Rp / (r0 * (r0 + Rp)))
res['antipodes'] = {'v': float(v_anti), 'v_moins_1pc': orbite(mu, Rp, R(100000), v_anti * R('0.99'))}
# vitesse (tir horizontal depuis 100 km) qui fait tomber le boulet à 179° du canon (racine numérique)
v179 = find_root(lambda v: orbite(mu, Rp, R(100000), R(v))['impact_deg'] - 179, float(v_anti) * 0.99,
                 float(v_anti) * (1 - 1e-12))
res['antipodes']['v_179'] = float(v179)
res['antipodes']['tir_179'] = orbite(mu, Rp, R(100000), R(v179))
# tir incliné de 10° : une large plage de vitesses mène aux antipodes (défi jouable au curseur)
v180 = find_root(lambda v: orbite(mu, Rp, R(100000), R(v), 10)['impact_deg'] - 180, 7700, 8100)
res['antipodes']['v_180_10deg'] = float(v180)
res['antipodes']['plage_10deg'] = [float(find_root(lambda v: orbite(mu, Rp, R(100000), R(v), 10)['impact_deg'] - c,
                                                   7700, 8100)) for c in (177, 183)]
# au-dessus de l'air : une orbite repasse par son point de départ, donc périgée ≤ altitude du canon ; depuis 60 km
# aucun tir n'a son périgée au-dessus de 100 km ; depuis 150 km, tir horizontal à v₁ : cercle à 150 km
res['au_dessus'] = orbite(mu, Rp, R(150000), sqrt(mu / (Rp + 150000)))


# intégrations indépendantes avec l'air (DOP853, 1e-12)
def integrer(astre, alt, v, ang, proj, t_max):
    mu, Rp = [float(x) for x in ASTRES[astre]]
    k = 0.5 / B[proj]
    a_ = float(ang) * np.pi / 180

    def f(t, s):
        x, y, vx, vy = s
        r = np.hypot(x, y)
        g = -mu / r ** 3
        vv = np.hypot(vx, vy)
        d = k * rho(astre, r - Rp) * vv
        return [vx, vy, g * x - d * vx, g * y - d * vy]

    def sol(t, s):
        return np.hypot(s[0], s[1]) - Rp
    sol.terminal = True
    sol.direction = -1
    s0 = [0.0, Rp + float(alt), float(v) * np.cos(a_), float(v) * np.sin(a_)]
    r = solve_ivp(f, (0, t_max), s0, method='DOP853', rtol=1e-12, atol=1e-6, events=sol, max_step=50.0)
    x, y = r.y[0][-1], r.y[1][-1]
    th0 = np.pi / 2
    # angle balayé (sens horaire) : déroulé sur toute la trajectoire
    th = np.unwrap(np.arctan2(r.y[1], r.y[0]))
    return {'impact_s': float(r.t[-1]), 'impact_deg': float(-(th[-1] - th[0]) * 180 / np.pi),
            'touche': bool(len(r.t_events[0]) > 0)}


pr = pre['rentree']
res['air'] = {
    'rentree_capsule': dict(integrer('terre', 200000, pr['v'], 0, 'capsule', 20000), v=pr['v']),
    'boulet_100km_5kms': integrer('terre', 100000, 5000, 0, 'boulet', 5000),
    'satellite_180km': dict(integrer('terre', 180000, float(sqrt(mu / (Rp + 180000))), 0, 'satellite', 2e5),
                            v=float(sqrt(mu / (Rp + 180000)))),
    'mars_boulet_50km_2500': integrer('mars', 50000, 2500, 0, 'boulet', 5000),
}

with open(SORTIE, 'w') as f:
    json.dump(res, f, indent=1, sort_keys=True, default=float)
print(json.dumps(res['air'], indent=1, default=float))
