# Vérification SageMath de l'animation « Précession séculaire d'une orbite » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : les coefficients de Laplace b^(1)_{3/2}(α) par intégration numérique
# (numerical_integral) et par leur série hypergéométrique, la fréquence séculaire A de Laplace-Lagrange pour une
# particule test (Murray et Dermott 1999, chap. 7) due aux quatre planètes géantes, les distances des nœuds et les
# instants où un nœud passe à 1 ua (find_root) ; puis un contrôle indépendant de la théorie : un astéroïde peu
# excentrique et peu incliné à 1,47 ua, intégré directement (scipy DOP853) avec le Soleil et Jupiter sur des orbites
# circulaires : pente de ϖ(t) et de Ω(t) sur 3 000 ans comparée à +A et −A (Jupiter seul).
# Usage : sage outils/verif_anim/seculaire_verif.sage   (écrit tests/seculaire_sage.json)
import json, os
import numpy as np
from scipy.integrate import solve_ivp
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'seculaire_sage.json'))
def f10(x):
    return float('%.10g' % float(x))
GEANTES = [(5.2029, 1047.348644), (9.5367, 3497.9018), (19.1892, 22902.98), (30.0699, 19412.26)]
def b_int(s, j, al):
    v = numerical_integral(lambda p: cos(j*p)/(1 - 2*al*cos(p) + al^2)^s, 0, 2*pi, eps_rel=1e-14)[0]
    return v/pi
def b_serie(al):
    # b^(1)_{3/2}(α) = 3α ₂F₁(3/2, 5/2; 2; α²)   (développement de Laplace)
    return 3*al*hypergeometric([3/2, 5/2], [2], al^2).n(80)
out = {'sage': VERSION_SAGE, 'laplace': [], 'objets': {}}
for al in (0.05, 0.2, 0.2826, 0.5, 0.6):
    bi, bs = b_int(1.5, 1, al), b_serie(al)
    assert abs(bi - bs) < 1e-12*abs(bs), (al, bi, bs)
    out['laplace'].append([float(al), f10(bs), f10(b_int(1.5, 2, al))])
def A_LL(a, planetes=GEANTES):
    n = 2*pi/a^(3/2)
    return n/4*sum((RR(a)/aj)^2*b_serie(RR(a)/aj)/m for aj, m in planetes)
OBJ = {'apollo': (1.47, 0.56, 286.0, 6.35), 'icare': (1.08, 0.827, 31.4, 22.8), 'phaethon': (1.27, 0.89, 322.0, 22.3),
       'adonis': (1.87, 0.764, 43.7, 1.32), 'toutatis': (2.54, 0.625, 278.0, 0.448)}
def moid_sage(a, e, i, w):
    # distance minimale entre l'ellipse (anomalie vraie ν) et le cercle terrestre (longitude λ) : minimisation
    # à deux variables depuis une grille de départs, sans passer par la forme « ρ − 1 » du code de Coupole
    i, w = RR(i)*pi.n()/180, RR(w)*pi.n()/180
    p = a*(1 - e^2)
    def pos(nu):
        r = p/(1 + e*cos(nu)); u = w + nu
        return vector(RDF, [r*cos(u), r*sin(u)*cos(i), r*sin(u)*sin(i)])
    def d2(v):
        P = pos(v[0]); T = vector(RDF, [cos(v[1]), sin(v[1]), 0])
        return (P - T).dot_product(P - T)
    best = None
    for k in range(24):
        nu0 = 2*pi.n()*k/24
        P = pos(nu0)
        s = minimize(d2, [nu0, float(atan2(P[1], P[0]))], algorithm='simplex')
        v = sqrt(d2(s))
        best = v if best is None or v < best else best
    return best
for k, (a, e, w0, inc) in OBJ.items():
    A = RR(A_LL(a))
    p = a*(1 - e^2)
    rasc = p/(1 + e*cos(w0*pi/180)); rdesc = p/(1 - e*cos(w0*pi/180))
    # instants des croisements dans [0, 2π/A] : ω(t) = ω0 + 2At, r(ω) = 1
    T = 2*pi/A
    ts = []
    for genre, sg in (('asc', 1), ('desc', -1)):
        f = lambda t: p/(1 + sg*e*cos(w0*pi/180 + 2*A*t)) - 1
        N = 4000
        for j in range(N):
            t0, t1 = T*j/N, T*(j + 1)/N
            if f(t0)*f(t1) < 0:
                ts.append([f10(find_root(f, t0, t1, xtol=1e-12)), genre])
    ts.sort()
    out['objets'][k] = {'A': f10(A), 'A_arcsec_an': f10(A*180/pi*3600), 'periode_varpi': f10(2*pi/A),
                        'r_asc': f10(rasc), 'r_desc': f10(rdesc), 'croisements': ts,
                        'moid': f10(moid_sage(a, e, inc, w0)), 'moid_w': [[ww, f10(moid_sage(a, e, inc, ww))] for ww in (0, 45, 90, 200)],
                        'quadrupole': f10(3/4*2*pi/a^(3/2)*sum((a/aj)^3/m for aj, m in GEANTES))}
    print(k, out['objets'][k]['A_arcsec_an'], '″/an, ϖ en', round(2*pi/A), 'ans,', len(ts), 'croisements')
# --- contrôle indépendant : intégration directe Soleil + Jupiter circulaire (unités ua, an, GM☉ = 4π²)
mu = 1/1047.348644
GM = 4*pi.n()^2
aJ = 5.2029
nJ = float(sqrt(GM*(1 + mu)/aJ^3))
def jup(t):
    c, s = np.cos(nJ*t), np.sin(nJ*t)
    return np.array([aJ*c, aJ*s, 0.0])
def f3(t, y):
    # repère héliocentrique : Soleil fixe à l'origine, Jupiter sur son cercle, terme indirect
    r = y[:3]; rj = jup(t)
    d = rj - r
    acc = -GM*r/np.linalg.norm(r)**3 + GM*mu*(d/np.linalg.norm(d)**3 - rj/np.linalg.norm(rj)**3)
    return np.concatenate([y[3:], acc])
def elements(y):
    r, v = y[:3], y[3:]
    h = np.cross(r, v)
    ev = np.cross(v, h)/GM - r/np.linalg.norm(r)
    nod = np.array([-h[1], h[0], 0.0])
    return float(np.arctan2(ev[1], ev[0])), float(np.arctan2(nod[1], nod[0]))
a0, e0, i0 = 1.47, 0.05, 2.0*pi.n()/180
rp = a0*(1 - e0); vp = float(sqrt(GM*(1 + e0)/rp))
y0 = np.array([rp, 0.0, 0.0, 0.0, vp*float(cos(i0)), vp*float(sin(i0))])
ts_ = np.linspace(0, 3000, 601)
so = solve_ivp(f3, (0, 3000), y0, method='DOP853', rtol=1e-10, atol=1e-12, t_eval=ts_)
vp_ = np.unwrap([elements(so.y[:, j])[0] for j in range(len(ts_))])
om_ = np.unwrap([elements(so.y[:, j])[1] for j in range(len(ts_))])
pente_varpi = float(np.polyfit(ts_, vp_, 1)[0]); pente_om = float(np.polyfit(ts_, om_, 1)[0])
A_jup = float(A_LL(a0, [(aJ, 1047.348644)]))
print('intégration : dϖ/dt =', pente_varpi, ' dΩ/dt =', pente_om, ' A (Jupiter seul) =', A_jup)
out['integration'] = {'a': float(a0), 'e': float(e0), 'i_deg': 2.0, 'duree_ans': 3000, 'pente_varpi': f10(pente_varpi),
                      'pente_omega': f10(pente_om), 'A_jupiter': f10(A_jup)}
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False, default=float)
