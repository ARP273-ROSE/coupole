# Vérification SageMath de l'animation « Résonances et chaos » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : demi-grands axes des résonances p:q avec Jupiter, état initial dans le repère
# tournant d'un astéroïde lâché à son périhélie (passage héliocentrique → barycentrique → tournant, refait par matrices),
# éléments osculateurs de cet état (doivent redonner a et e), puis intégration indépendante du problème restreint
# (scipy DOP853, tolérance 10⁻¹³) des deux jumeaux pour trois cas, jusqu'à t = 6 et t = 30.
# Usage : sage outils/verif_anim/resonances_verif.sage   (écrit tests/resonances_sage.json)
import json, os
from scipy.integrate import solve_ivp
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'resonances_sage.json'))
R = RealField(120)
def f10(x):
    return float('%.10g' % float(x))
AJ = R('5.2026')
MU = 1/(1 + R('1047.348644'))
out = {'sage': VERSION_SAGE, 'resonances': {}}
for p, q in ((1, 1), (3, 2), (2, 1), (7, 3), (5, 2), (3, 1), (4, 1)):
    out['resonances']['%d:%d' % (p, q)] = f10(AJ*(R(q)/p)^(2/3))
def initial(a_ua, e, phi, mu):
    a, e, ph = R(a_ua)/AJ, R(e), R(phi)*R(pi)/180
    r = a*(1 - e); v = sqrt((1 - mu)*(1 + e)/r)
    Rot = matrix(R, [[cos(ph), -sin(ph)], [sin(ph), cos(ph)]])
    pos = vector(R, [-mu, 0]) + Rot*vector(R, [r, 0])
    vin = vector(R, [0, -mu]) + Rot*vector(R, [0, v])                 # Soleil + vitesse képlérienne au périhélie
    omega_r = vector(R, [-pos[1], pos[0]])
    vr = vin - omega_r
    return [pos[0], pos[1], vr[0], vr[1]]
def elements(s, mu):
    x, y, vx, vy = s
    d = vector(R, [x + mu, y]); u = vector(R, [vx - y, vy + x + mu])
    gm = 1 - mu; r = d.norm(); v2 = u*u
    ev = ((v2 - gm/r)*d - (d*u)*u)/gm
    return -gm/(2*(v2/2 - gm/r))*AJ, ev.norm()
def f(t, s, mu):
    x, y, vx, vy = s
    r1 = ((x + mu)**2 + y**2)**1.5; r2 = ((x - 1 + mu)**2 + y**2)**1.5
    ax = x - (1 - mu)*(x + mu)/r1 - mu*(x - 1 + mu)/r2 + 2*vy
    ay = y - (1 - mu)*y/r1 - mu*y/r2 - 2*vx
    return [vx, vy, ax, ay]
cas = {'hilda': ('3.97', '0.15', '0'), 'kirkwood': ('2.50', '0.10', '0'), 'comete': ('3.6', '0.55', '150')}
out['cas'] = {}
for k, (a, e, phi) in cas.items():
    s0 = initial(a, e, phi, MU)
    a_, e_ = elements(s0, MU)
    s0f = [float(c) for c in s0]
    s1f = [s0f[0] + 1e-7] + s0f[1:]
    res = {'initial': [f10(c) for c in s0], 'a0': f10(a_), 'e0': f10(e_)}
    for T in (6, 30):
        sol = solve_ivp(f, (0, T), s0f, args=(float(MU),), method='DOP853', rtol=1e-13, atol=1e-14)
        sol2 = solve_ivp(f, (0, T), s1f, args=(float(MU),), method='DOP853', rtol=1e-13, atol=1e-14)
        y1 = sol.y[:, -1]; y2 = sol2.y[:, -1]
        ae = elements([R(c) for c in y1], MU)
        res[str(T)] = {'etat': [f10(c) for c in y1], 'a': f10(ae[0]), 'e': f10(ae[1]),
                       'ecart': f10(sqrt((y1[0] - y2[0])**2 + (y1[1] - y2[1])**2))}
    out['cas'][k] = res
    print(k, res['a0'], res['e0'], res['30'])
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False)
