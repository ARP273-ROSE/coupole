# Vérification SageMath de l'animation « Phénomènes mutuels des satellites galiléens » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : l'aire commune de deux disques (formule fermée contrôlée par une intégration
# numérique), puis, pour quelques rencontres (orbites circulaires coplanaires, Terre et Soleil à la latitude B, Soleil à
# l'angle de phase φ), l'éclat de la paire à des instants donnés : occultation = aire commune exacte ; éclipse =
# intégrale double (scipy dblquad, en coordonnées polaires sur le disque éclipsé) de la part du disque solaire cachée
# par le satellite actif ; instants des premier et dernier contacts (find_root) et durée.
# Usage : sage outils/verif_anim/mutuels_verif.sage   (écrit tests/mutuels_sage.json)
import json, os
from scipy.integrate import dblquad
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'mutuels_sage.json'))
def f10(x):
    return float('%.10g' % float(x))
SAT = {'io': (1, 421800.0, 1821.6, 1.769138, 0.63), 'europe': (2, 671100.0, 1560.8, 3.551181, 0.67),
       'ganymede': (3, 1070400.0, 2631.2, 7.154553, 0.43), 'callisto': (4, 1882700.0, 2410.3, 16.689017, 0.17)}
RS = 695700.0
D = 5.2029*149597870.7
RHO = RS/D
def lentille(d, r1, r2):
    d, r1, r2 = RR(d), RR(r1), RR(r2)
    if d >= r1 + r2: return RR(0)
    if d <= abs(r1 - r2): return pi.n()*min(r1, r2)^2
    a1 = acos((d^2 + r1^2 - r2^2)/(2*d*r1)); a2 = acos((d^2 + r2^2 - r1^2)/(2*d*r2))
    return r1^2*a1 + r2^2*a2 - (r1^2*sin(2*a1) + r2^2*sin(2*a2))/2   # deux segments circulaires
def lentille_num(d, r1, r2):
    # aire de {x² + y² ≤ r1², (x − d)² + y² ≤ r2²} : intégrale en x de la hauteur commune
    def h(x):
        y1 = sqrt(max(0, r1^2 - x^2)); y2 = sqrt(max(0, r2^2 - (x - d)^2))
        return 2*min(y1, y2)
    x0, x1 = max(-r1, d - r2), min(r1, d + r2)
    xk = (d^2 + r1^2 - r2^2)/(2*d)                 # abscisse où les deux cercles se coupent (point anguleux)
    if x0 < xk < x1:
        return numerical_integral(h, x0, xk, eps_rel=1e-13)[0] + numerical_integral(h, xk, x1, eps_rel=1e-13)[0]
    return numerical_integral(h, x0, x1, eps_rel=1e-13)[0]
out = {'sage': VERSION_SAGE, 'lentilles': [], 'rencontres': []}
for d, r1, r2 in ((1.0, 1.0, 1.0), (0.5, 1.0, 0.6), (2.0, 1.8216, 1.5608), (3000.0, 1821.6, 1560.8), (0.3, 1.0, 0.2)):
    a, b = lentille(d, r1, r2), lentille_num(d, r1, r2)
    assert abs(a - b) < 1e-7*max(1, a), (d, r1, r2, a, b)   # racines aux bornes : quadrature à 1e-8 près
    out['lentilles'].append([d, r1, r2, f10(a)])
class R:
    def __init__(s, act, pas, genre, B, phi, fx):
        s.A, s.P = SAT[act], SAT[pas]; s.genre = genre
        s.b = RR(B)*pi.n()/180; s.psi = RR(phi)*pi.n()/180 if genre == 'eclipse' else RR(0)
        aa, ap = s.A[1], s.P[1]
        x0 = RR(fx)*min(aa, ap); cote = 1 if aa < ap else -1
        s.la0 = atan2(cote*sqrt(aa^2 - x0^2), x0) + s.psi
        s.lp0 = atan2(cote*sqrt(ap^2 - x0^2), x0) + s.psi
        s.na = 2*pi.n()/(s.A[3]*1440); s.np = 2*pi.n()/(s.P[3]*1440)
    def pos(s, t):
        la, lp = s.la0 + s.na*t, s.lp0 + s.np*t
        return vector([s.A[1]*cos(la), s.A[1]*sin(la), 0]), vector([s.P[1]*cos(lp), s.P[1]*sin(lp), 0])
    def base(s, psi):
        # direction du viseur : azimut ψ, latitude B ; Y du repère du viseur s'éloigne de lui
        d = vector([sin(psi)*cos(s.b), -cos(psi)*cos(s.b), sin(s.b)])
        ex = vector([cos(psi), sin(psi), 0])
        ey = d.cross_product(ex)
        return d, ex, ey
    def ciel(s, P, psi):
        d, ex, ey = s.base(psi)
        return P.dot_product(ex), P.dot_product(ey), P.dot_product(d)
    def flux(s, t):
        fa = s.A[4]*s.A[2]^2; fp = s.P[4]*s.P[2]^2
        Pa, Pp = s.pos(t)
        if s.genre == 'occultation':
            xa, ya, _ = s.ciel(Pa, 0); xp, yp, _ = s.ciel(Pp, 0)
            cache = lentille(sqrt((xa - xp)^2 + (ya - yp)^2), s.A[2], s.P[2])/(pi.n()*s.P[2]^2)
            return (fa + fp*(1 - cache))/(fa + fp)
        xa, ya, za = s.ciel(Pa, s.psi); xp, yp, zp = s.ciel(Pp, s.psi)
        ell = za - zp
        if ell <= 0: return RR(1)
        ox, oy = float(xa - xp), float(ya - yp)
        ra, rp, ell = float(s.A[2]), float(s.P[2]), float(ell)
        def cache(th, r):
            u, v = r*cos(th), r*sin(th)
            dl = sqrt((ox - u)^2 + (oy - v)^2)/ell
            return float(lentille(dl, ra/ell, RHO)/(pi.n()*RHO^2))*r
        val = dblquad(cache, 0, rp, 0, 2*pi.n(), epsabs=1e-3, epsrel=1e-9)[0]
        return (fa + fp*(1 - val/(pi.n()*rp^2)))/(fa + fp)
    def contacts(s):
        # premiers et derniers contacts : distance des centres (ou à l'axe de l'ombre) = somme des rayons (+ pénombre)
        def g(t):
            Pa, Pp = s.pos(t)
            xa, ya, za = s.ciel(Pa, s.psi); xp, yp, zp = s.ciel(Pp, s.psi)
            taille = s.A[2] + s.P[2] + ((za - zp)*RHO if s.genre == 'eclipse' else 0)
            return sqrt((xa - xp)^2 + (ya - yp)^2) - taille
        ts = [RR(k) for k in range(-200, 201)]
        rac = [find_root(g, ts[k], ts[k + 1]) for k in range(len(ts) - 1) if g(ts[k])*g(ts[k + 1]) < 0]
        return rac
CAS = [('europe', 'io', 'occultation', 0.1, 8.0, 0.5), ('io', 'europe', 'occultation', 0.0, 8.0, 0.5),
       ('io', 'callisto', 'occultation', 0.02, 8.0, -0.3), ('europe', 'io', 'eclipse', 0.1, 8.0, 0.5),
       ('ganymede', 'io', 'eclipse', 0.05, 6.0, 0.5), ('io', 'ganymede', 'eclipse', 0.0, 10.0, -0.8)]
for c in CAS:
    r = R(*c)
    instants = [-20.0, -5.0, 0.0, 3.7, 12.5]
    fl = [[t, f10(r.flux(t))] for t in instants]
    ct = r.contacts()
    out['rencontres'].append({'cas': list(c), 'flux': fl, 'contacts': [f10(x) for x in ct]})
    print(c, fl, 'contacts', ct)
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False, default=float)
