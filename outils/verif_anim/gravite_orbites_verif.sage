# Vérification SageMath de l'animation « Gravité et orbites » (d'après la simulation PhET Gravity and Orbits,
# University of Colorado Boulder ; code propre à Coupole) : constantes, conditions initiales des scénarios, périodes
# de Kepler et intégration indépendante (DOP853 de SciPy, tolérance 1e-13, en ua et jours) des scénarios, avec la
# même mesure des périodes (passages successifs par la direction de départ, vue du corps central).
# Constantes (sources) :
#   G = 6,67430e-11 m³ kg⁻¹ s⁻²                          CODATA 2018 (inchangée en 2022)
#   GM☉ = 1,3271244e20 m³ s⁻², GM⊕ = 3,986004e14 m³ s⁻²   UAI 2015, résolution B3 (valeurs nominales)
#   R☉ = 6,957e8 m, R⊕ = 6,3781e6 m                       UAI 2015, résolution B3 (valeurs nominales)
#   GM☾ = 4,902800118e12 m³ s⁻²                           éphémérides JPL DE440 (Park et al. 2021)
#   R☾ = 1,7374e6 m, demi-grand axe 3,844e8 m             NASA, Moon Fact Sheet
#   1 ua = 149 597 870 700 m                              UAI 2012, résolution B2
#   ISS : 419 725 kg, altitude 415 km                     NASA, International Space Station Facts and Figures
#   année sidérale 365,256363 j, mois sidéral 27,321661 j NASA Earth / Moon Fact Sheets ; 1 j = 86 400 s
# Usage : sage outils/verif_anim/gravite_orbites_verif.sage   (écrit tests/gravite_orbites_sage.json)
import json, os
import numpy as np
from scipy.integrate import solve_ivp

R = RealField(120)
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'gravite_orbites_sage.json'))

G = R('6.67430e-11')
GM = {'soleil': R('1.3271244e20'), 'terre': R('3.986004e14'), 'lune': R('4.902800118e12')}
M = {k: v / G for k, v in GM.items()}
M['iss'] = R(419725)
M['comete'] = R('1e14')
UA = R(149597870700)
JOUR = R(86400)
A_LUNE = R('3.844e8')
R_TERRE = R('6.3781e6')
ALT_ISS = R(415000)
VRAIES = {'terre': R('365.256363'), 'lune': R('27.321661')}

def kepler(gm, a):
    return 2 * R(pi) * sqrt(a ** 3 / gm)

res = {'constantes': {'G': float(G), 'masses': {k: float(v) for k, v in M.items()}, 'ua': float(UA)}}
res['kepler_j'] = {
    'terre_soleil': float(kepler(GM['soleil'] + GM['terre'], UA) / JOUR),
    'terre_soleil_lune': float(kepler(GM['soleil'] + GM['terre'] + GM['lune'], UA) / JOUR),
    'lune_terre': float(kepler(GM['terre'] + GM['lune'], A_LUNE) / JOUR),
    'iss_min': float(kepler(GM['terre'] + G * M['iss'], R_TERRE + ALT_ISS) / 60),
}
res['vraies_j'] = {k: float(v) for k, v in VRAIES.items()}

# ------------------------------------------------------------------ conditions initiales (recette de l'animation)
# Chaque couple (corps, primaire) part sur une orbite circulaire : corps à +r sur l'axe x de son primaire, vitesse
# relative sqrt(G (m + m_primaire) / r) selon +y (sens direct) ; Soleil, Terre et Lune ensemble partent de leur état
# réel du 1er janvier 2026 (ETAT_2026) ; la comète part
# de son périhélie (0,6 ua) à −x, vers −y, pour une aphélie de 2,4 ua.  Puis quantité de mouvement totale nulle et
# barycentre à l'origine.
def deux(m1, m2, r, gm_tot=None):
    """positions et vitesses de deux corps en orbite circulaire, barycentre au repos à l'origine"""
    v = sqrt(G * (m1 + m2) / r) if gm_tot is None else sqrt(gm_tot / r)
    x1 = -r * m2 / (m1 + m2); x2 = r * m1 / (m1 + m2)
    v1 = -v * m2 / (m1 + m2); v2 = v * m1 / (m1 + m2)
    return [(x1, R(0), R(0), v1), (x2, R(0), R(0), v2)]

def recentrer(corps):
    mt = sum(M[n] for n, _ in corps)
    cx = sum(M[n] * s[0] for n, s in corps) / mt; cy = sum(M[n] * s[1] for n, s in corps) / mt
    px = sum(M[n] * s[2] for n, s in corps) / mt; py = sum(M[n] * s[3] for n, s in corps) / mt
    return [(n, (s[0] - cx, s[1] - cy, s[2] - px, s[3] - py)) for n, s in corps]

# État réel du 1er janvier 2026 à 0 h TDB (DE440, orbites ramenées dans l'écliptique autour de leur ligne des nœuds),
# par outils/verif_anim/etat_initial_gravite.py (python-lab, skyfield) : [x, y, vx, vy] en m et m/s.
ETAT_2026 = {'soleil': [R('-447268.19852799166'), R('7.429785804638976'), R('7.282139173820521e-05'), R('-0.09207872686803291')], 'terre': [R('147103130738.3562'), R('7.429789767206905'), R('-31.149223260146357'), R('30273.645476968926')], 'lune': [R('147402951395.03217'), R('-201115268.94787067'), R('561.2687042467766'), R('31187.344882943245')]}

def scenario(nom):
    if nom == 'soleil_terre':
        a, b = deux(M['soleil'], M['terre'], UA)
        return recentrer([('soleil', a), ('terre', b)])
    if nom == 'terre_lune':
        a, b = deux(M['terre'], M['lune'], A_LUNE)
        return recentrer([('terre', a), ('lune', b)])
    if nom == 'terre_iss':
        a, b = deux(M['terre'], M['iss'], R_TERRE + ALT_ISS)
        return recentrer([('terre', a), ('iss', b)])
    if nom in ('soleil_terre_lune', 'libre'):
        corps = [(n, tuple(ETAT_2026[n])) for n in ('soleil', 'terre', 'lune')]
        if nom == 'libre':
            q, Q = R('0.6') * UA, R('2.4') * UA
            v = sqrt(G * (M['soleil'] + M['comete']) * (2 / q - 2 / (q + Q)))
            corps.append(('comete', (-q, R(0), R(0), -v)))
        return recentrer(corps)
    raise ValueError(nom)

PRIMAIRE = {'soleil_terre': {'terre': 'soleil'}, 'soleil_terre_lune': {'terre': 'soleil', 'lune': 'terre'},
            'terre_lune': {'lune': 'terre'}, 'terre_iss': {'iss': 'terre'},
            'libre': {'terre': 'soleil', 'lune': 'terre', 'comete': 'soleil'}}
DUREE_J = {'soleil_terre': 800.0, 'soleil_terre_lune': 800.0, 'terre_lune': 120.0, 'terre_iss': 0.5, 'libre': 1500.0}

def integrer(nom):
    corps = scenario(nom)
    noms = [n for n, _ in corps]
    m = np.array([float(G * M[n]) for n in noms]) * float(JOUR) ** 2 / float(UA) ** 3   # G m en ua³ j⁻²
    y0 = []
    for _, s in corps:
        y0 += [float(s[0] / UA), float(s[1] / UA), float(s[2] * JOUR / UA), float(s[3] * JOUR / UA)]
    n = len(noms)
    def f(t, y):
        d = np.zeros_like(y)
        for i in range(n):
            d[4 * i] = y[4 * i + 2]; d[4 * i + 1] = y[4 * i + 3]
            for j in range(n):
                if i != j:
                    dx = y[4 * j] - y[4 * i]; dy = y[4 * j + 1] - y[4 * i + 1]
                    r3 = (dx * dx + dy * dy) ** 1.5
                    d[4 * i + 2] += m[j] * dx / r3; d[4 * i + 3] += m[j] * dy / r3
        return d
    sol = solve_ivp(f, (0, DUREE_J[nom]), np.array(y0), method='DOP853', rtol=1e-13, atol=1e-16, dense_output=True,
                    max_step=0.02 if nom != 'terre_iss' else 0.0002)
    periodes = {}
    for c, p in PRIMAIRE[nom].items():
        i, k = noms.index(c), noms.index(p)
        rel = lambda t: (sol.sol(t)[4 * i] - sol.sol(t)[4 * k], sol.sol(t)[4 * i + 1] - sol.sol(t)[4 * k + 1])
        u0 = rel(0.0)
        # passages : produit vectoriel u0 × r qui passe de < 0 à ≥ 0 avec u0 · r > 0
        ts = sol.t
        passages = []
        for a, b in zip(ts[:-1], ts[1:]):
            ra, rb = rel(a), rel(b)
            ca = u0[0] * ra[1] - u0[1] * ra[0]; cb = u0[0] * rb[1] - u0[1] * rb[0]
            if ca < 0 <= cb and (u0[0] * rb[0] + u0[1] * rb[1]) > 0:
                lo, hi = a, b
                for _ in range(80):
                    mi = (lo + hi) / 2
                    rm = rel(mi)
                    if u0[0] * rm[1] - u0[1] * rm[0] < 0: lo = mi
                    else: hi = mi
                passages.append((lo + hi) / 2)
        if passages:
            periodes[c] = float(passages[-1] / len(passages))
    # énergie et moment cinétique (contrôle de l'intégration de référence)
    def energie(y):
        e = 0.0
        for a in range(n):
            e += 0.5 * m[a] * (y[4 * a + 2] ** 2 + y[4 * a + 3] ** 2)
            for b in range(a + 1, n):
                e -= m[a] * m[b] / np.hypot(y[4 * a] - y[4 * b], y[4 * a + 1] - y[4 * b + 1])
        return e
    e0, e1 = energie(sol.y[:, 0]), energie(sol.y[:, -1])
    etat = []
    for (c, s) in corps:
        etat.append([c, float(s[0]), float(s[1]), float(s[2]), float(s[3])])
    return {'etat_initial_si': etat, 'periodes_j': periodes, 'duree_j': float(DUREE_J[nom]),
            'derive_energie_reference': float(abs((e1 - e0) / e0)),
            'etat_final_ua_j': [float(x) for x in sol.y[:, -1]]}

res['scenarios'] = {}
for nom in ('soleil_terre', 'soleil_terre_lune', 'terre_lune', 'terre_iss', 'libre'):
    res['scenarios'][nom] = integrer(nom)
    print(nom, res['scenarios'][nom]['periodes_j'], res['scenarios'][nom]['derive_energie_reference'])

# rapport des accélérations de la Lune (Soleil / Terre) : > 1 ⇒ trajectoire toujours concave vers le Soleil
acc_soleil = GM['soleil'] / UA ** 2
acc_terre = GM['terre'] / A_LUNE ** 2
res['lune_concave'] = {'acc_soleil': float(acc_soleil), 'acc_terre': float(acc_terre), 'rapport': float(acc_soleil / acc_terre)}
print('kepler', res['kepler_j'])
print('rapport acc', res['lune_concave'])
with open(SORTIE, 'w') as fh:
    json.dump(res, fh, indent=1, sort_keys=True)
print('écrit', SORTIE)
