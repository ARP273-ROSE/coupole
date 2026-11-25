# Vérification SageMath de l'animation « Traînées de météoroïdes » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : l'état de la comète au périhélie, les vitesses d'éjection (générateur de
# Park et Miller, entiers exacts), puis la trajectoire de quelques grains intégrée numériquement (scipy DOP853, Soleil
# seul, GM(1 − β)) sur plusieurs révolutions : positions à des dates données, et instants et distances des passages
# au nœud (traversée de l'écliptique, find_root) ; la date où la Terre (orbite képlérienne, éléments de Standish) est
# à une longitude donnée, contrôlée en résolvant l'équation de Kepler de la Terre à cette date.
# Usage : sage outils/verif_anim/trainees_verif.sage   (écrit tests/trainees_sage.json)
import json, os
import numpy as np
from scipy.integrate import solve_ivp
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'trainees_sage.json'))
def f10(x):
    return float('%.15g' % float(x))       # dates en années : 15 chiffres
K = RR('0.01720209895')
GM = (K*365.25)^2
MS = 365.25*86400/(149597870.7*1000)
def rot(a, e, i, o, w):
    i, o, w = [RR(x)*pi.n()/180 for x in (i, o, w)]
    Rz = lambda t: matrix(RR, [[cos(t), -sin(t), 0], [sin(t), cos(t), 0], [0, 0, 1]])
    Rx = lambda t: matrix(RR, [[1, 0, 0], [0, cos(t), -sin(t)], [0, sin(t), cos(t)]])
    return Rz(o)*Rx(i)*Rz(w)
def etat_perihelie(a, e, i, o, w, mu=GM):
    q = a*(1 - e); vq = sqrt(mu*(1 + e)/q)
    M = rot(a, e, i, o, w)
    return M*vector(RR, [q, 0, 0]), M*vector(RR, [0, vq, 0])
class PM:
    def __init__(s, g): s.x = Integer(g) % 2147483647 or 1
    def __call__(s):
        s.x = (16807*s.x) % 2147483647
        return RR(s.x)/2147483647
COM = {'tempel_tuttle': (10.3383, 0.905553, 162.487, 235.271, 172.500, 1998.1591),
       'swift_tuttle': (26.0921, 0.963226, 113.454, 139.381, 152.982, 1992.9459)}
out = {'sage': VERSION_SAGE, 'beta': {k: f10(5.7e-5/r) for k, r in (('cm', 1.0), ('mm', 0.1), ('dixieme', 0.01))},
       'grains': [], 'terre': []}
def f(t, y, mu):
    r = np.linalg.norm(y[:3])
    return np.concatenate([y[3:], -mu*y[:3]/r**3])
for cle, tk, dv, beta, graine, n_rev in (('tempel_tuttle', 1898.4, 10.0, 5.7e-4, 1004, 3),
                                         ('tempel_tuttle', 1965.0, 30.0, 5.7e-3, 1006, 2),
                                         ('swift_tuttle', 1859.7, 10.0, 5.7e-5, 1002, 1)):
    a, e, i, o, w, tp = COM[cle]
    P = a^(3/2)*2*pi.n()/sqrt(GM)
    tk = tp + round((tk - tp)/P)*P                  # le passage au périhélie le plus proche
    r0, v0 = etat_perihelie(a, e, i, o, w)
    g = PM(graine)
    mu = float(GM*(1 - beta))
    res = []
    for j in range(3):                               # les trois premiers grains de cette éjection
        cz = 2*g() - 1; ph = 2*pi.n()*g(); s = dv*MS*g()^(1/3)
        sz = sqrt(max(0, 1 - cz^2))
        dvv = vector(RR, [s*sz*cos(ph), s*sz*sin(ph), s*cz])
        y0 = np.array([float(x) for x in list(r0) + list(v0 + dvv)])
        # passages au nœud : z = 0 à moins de 1,2 ua du Soleil (près du périhélie)
        def ecl(t, y, mu): return y[2]
        ecl.direction = 0
        T = float(n_rev*P*1.1)
        so = solve_ivp(f, (0, T), y0, args=(mu,), method='DOP853', rtol=1e-12, atol=1e-14, events=ecl, dense_output=True)
        noeuds = []
        for te, ye in zip(so.t_events[0], so.y_events[0]):
            if te > 1e-6 and np.linalg.norm(ye[:3]) < 1.2:
                noeuds.append([f10(tk + te), f10(np.linalg.norm(ye[:3]))])
        dates = [5.0, float(P), float(n_rev*P)]
        pos = [[f10(tk + d)] + [f10(x) for x in so.sol(d)[:3]] for d in dates]
        res.append({'noeuds': noeuds, 'positions': pos})
    out['grains'].append({'comete': cle, 'tk': f10(tk), 'dv': dv, 'beta': beta, 'graine': graine, 'grains': res})
    print(cle, tk, [r['noeuds'][:2] for r in res])
# la Terre : longitude vraie à une date (Kepler résolu ici), pour vérifier date_terre
aE, eE, varpi, L0, nE = 1.00000261, 0.01671123, 102.93768193, 100.46457166, 35999.37244981/100
for lam, an in ((55.271, 1999), (319.381, 2026), (10.0, 1850), (200.0, 2100)):
    # date où la longitude vraie vaut λ : M = E − e sin E, ν(E) = λ − ϖ ; on part de la date approchée et on résout
    def lon(t):
        M = (L0 + nE*(t - 2000) - varpi)*pi.n()/180
        E = find_root(lambda x: x - eE*sin(x) - M, M - 1, M + 1)
        nu = 2*atan2(sqrt(1 + eE)*sin(E/2), sqrt(1 - eE)*cos(E/2))
        x = nu*180/pi.n() + varpi
        return x - 360*floor(x/360)
    def ecart(t):
        x = lon(t) - lam + 180
        return x - 360*floor(x/360) - 180
    ts = [an + k/400 for k in range(401)]
    t_ = [find_root(ecart, ts[k], ts[k + 1]) for k in range(400) if ecart(ts[k])*ecart(ts[k + 1]) < 0 and abs(ecart(ts[k])) < 10][0]
    out['terre'].append([lam, an, f10(t_)])
    print('Terre', lam, an, t_)
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False, default=float)
