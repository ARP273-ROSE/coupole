# Vérification SageMath de l'animation « La limite de Roche » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : la limite d'une sphère rigide en rotation synchrone (résolution symbolique
# de 3GM r/d³ = Gm/r² avec M = 4/3 π ρ_M R³, m = 4/3 π ρ_m r³), les limites fluide (2,44) et rigide des quatre
# systèmes, l'étirement 3 (ρ_M/ρ_m)(R/d)³ et l'allongement 15/4 (ρ_M/ρ_m)(R/d)³, puis des orbites de grains lâchés par
# un amas en rotation d'ensemble, intégrées numériquement (scipy DOP853, deux corps, GM = 1) et comparées à la
# propagation képlérienne.
# Usage : sage outils/verif_anim/roche_verif.sage   (écrit tests/roche_sage.json)
import json, os
from scipy.integrate import solve_ivp
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'roche_sage.json'))
def f10(x):
    return float('%.10g' % float(x))
G, rM, rm, R, r, d = var('G rho_M rho_m R r d', domain='positive')
M = 4/3*pi*rM*R^3; m = 4/3*pi*rm*r^3
sol = solve(3*G*M*r/d^3 == G*m/r^2, d)
Ks = [(s.rhs()/(R*(rM/rm)^(1/3))).simplify_full() for s in sol]
K_rigide = [K for K in Ks if abs(CC(K).imag()) < 1e-30][0]          # la seule racine réelle
print('limite rigide : d =', K_rigide, '× R ∛(ρ_M/ρ_m)')
out = {'sage': VERSION_SAGE, 'K_rigide': f10(K_rigide), 'systemes': {}}
SYS = {'terre_lune': (5514, 3344, 10), 'mars_phobos': (3933, 1876, 2.76), 'saturne_glace': (687, 920, 3.08),
       'jupiter_comete': (1326, 500, 4.0)}
for k, (a, b, dd) in SYS.items():
    q = QQ(a)/QQ(b)
    out['systemes'][k] = {'fluide': f10(2.44*q^(1/3)), 'rigide': f10(K_rigide*q^(1/3)),
                          'etirement': f10(3*q/RR(dd)^3), 'allongement': f10(15/4*q/RR(dd)^3)}
    print(k, out['systemes'][k])
def f2(t, s):
    x, y, vx, vy = s
    r3 = (x*x + y*y)**1.5
    return [vx, vy, -x/r3, -y/r3]
grains = []
for (dd, th, gx, gy) in ((2.2, 0.3, 0.16, 0.0), (2.2, 0.3, -0.16, 0.05), (3.0, 1.0, 0.1, -0.1), (2.0, 4.0, 0.0, 0.16)):
    om = dd**-1.5
    c, s = cos(th), sin(th)
    x, y = float(dd*c + gx*c - gy*s), float(dd*s + gx*s + gy*c)
    s0 = [x, y, float(-om*y), float(om*x)]
    pos = {}
    for T in (5.0, 40.0):
        so = solve_ivp(f2, (0, T), s0, method='DOP853', rtol=1e-13, atol=1e-14)
        pos[str(T)] = [f10(so.y[0, -1]), f10(so.y[1, -1])]
    grains.append({'depart': [float(dd), float(th), float(gx), float(gy)], 'positions': pos})
out['grains'] = grains
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False)
