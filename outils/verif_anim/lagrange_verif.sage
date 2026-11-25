# Vérification SageMath de l'animation « Les points de Lagrange » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : μ des quatre systèmes, abscisses de L1, L2, L3 (racines du gradient
# de Ω sur l'axe, à 40 chiffres), L4 et L5, constantes de Jacobi aux cinq points, rayon de Hill, μ de Routh
# (1 − √(23/27))/2 et instabilité de L4 au-delà (valeurs propres du système linéarisé), puis une intégration
# indépendante (mpmath.odefun) d'un têtard et d'un fer à cheval autour de Soleil-Jupiter jusqu'à t = 6.
# Usage : sage outils/verif_anim/lagrange_verif.sage   (écrit tests/lagrange_sage.json)
import json, os
import mpmath
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'lagrange_sage.json'))
R = RealField(140)
SYS = {'soleil_terre': 1/(1 + R('328900.56')), 'terre_lune': 1/(1 + R('81.300568')),
       'soleil_jupiter': 1/(1 + R('1047.348644')), 'pluton_charon': R('0.1218')/R('1.1218')}
def Om(mu, x, y):
    return (x^2 + y^2)/2 + (1 - mu)/sqrt((x + mu)^2 + y^2) + mu/sqrt((x - 1 + mu)^2 + y^2)
def gx(mu, x):
    return x - (1 - mu)*(x + mu)/abs(x + mu)^3 - mu*(x - 1 + mu)/abs(x - 1 + mu)^3
out = {'sage': VERSION_SAGE, 'mu_routh': float((1 - sqrt(R(23)/27))/2), 'systemes': {}}
for k, mu in SYS.items():
    mpmath.mp.dps = 45
    m_ = mpmath.mpf(str(mu))
    rh = (m_/3)**(mpmath.mpf(1)/3)
    g = lambda x: x - (1 - m_)*(x + m_)/abs(x + m_)**3 - m_*(x - 1 + m_)/abs(x - 1 + m_)**3
    x1 = R(str(mpmath.findroot(g, (1 - m_ - 3*rh, 1 - m_ - rh/10), solver='anderson')))
    x2 = R(str(mpmath.findroot(g, (1 - m_ + rh/10, 1 - m_ + 3*rh), solver='anderson')))
    x3 = R(str(mpmath.findroot(g, (mpmath.mpf('-1.5'), -m_ - mpmath.mpf('0.1')), solver='anderson')))
    pts = {'L1': (R(x1), R(0)), 'L2': (R(x2), R(0)), 'L3': (R(x3), R(0)), 'L4': (1/R(2) - mu, sqrt(R(3))/2),
           'L5': (1/R(2) - mu, -sqrt(R(3))/2)}
    # stabilité de L4 : matrice du système linéarisé (x, y, vx, vy)
    x, y = var('x y')
    O = (x^2 + y^2)/2 + (1 - mu)/sqrt((x + mu)^2 + y^2) + mu/sqrt((x - 1 + mu)^2 + y^2)
    Hs = [[diff(O, a, b).subs(x=pts['L4'][0], y=pts['L4'][1]) for b in (x, y)] for a in (x, y)]
    M = matrix(RDF, [[0, 0, 1, 0], [0, 0, 0, 1], [Hs[0][0], Hs[0][1], 0, 2], [Hs[1][0], Hs[1][1], -2, 0]])
    stable = max(abs(real(v)) for v in M.eigenvalues()) < 1e-9
    out['systemes'][k] = {'mu': float(mu), 'L': {n: [float(p[0]), float(p[1])] for n, p in pts.items()},
                          'C': {n: float(2*Om(mu, p[0], p[1])) for n, p in pts.items()},
                          'hill': float((mu/3)^(R(1)/3)), 'L4_stable': bool(stable)}
    print(k, float(mu), [float(pts[n][0]) for n in ('L1', 'L2', 'L3')], 'L4 stable :', stable)
# intégrations indépendantes (Soleil-Jupiter)
mpmath.mp.dps = 25
mu = mpmath.mpf(1)/(1 + mpmath.mpf('1047.348644'))
def f(t, s):
    x, y, vx, vy = s
    dx1, dx2 = x + mu, x - 1 + mu
    r1 = mpmath.sqrt(dx1**2 + y**2); r2 = mpmath.sqrt(dx2**2 + y**2)
    k1, k2 = (1 - mu)/r1**3, mu/r2**3
    return [vx, vy, x - k1*dx1 - k2*dx2 + 2*vy, y - k1*y - k2*y - 2*vx]
L4 = (mpmath.mpf(1)/2 - mu, mpmath.sqrt(3)/2)
d = mpmath.mpf('0.005')
departs = {'tetard': [L4[0] + d/2, L4[1] + d*mpmath.sqrt(3)/2, 0, 0]}
r = 1 + mpmath.mpf('0.01')
departs['fer_a_cheval'] = [-r, 0, 0, -(r**mpmath.mpf(-0.5) - r)]
out['trajectoires'] = {}
for k, s0 in departs.items():
    sol = mpmath.odefun(f, 0, s0)
    out['trajectoires'][k] = {t: [float(v) for v in sol(mpmath.mpf(t))] for t in ('2', '6')}
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False)
print(json.dumps(out['trajectoires'], indent=1))
