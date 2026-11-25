# Vérification SageMath de l'animation « La précession des équinoxes » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole, par des matrices de rotation en précision 120 bits : passage équateur →
# écliptique J2000 (rotation d'angle ε autour de l'axe des équinoxes), pôle céleste de l'année tourné autour du pôle
# de l'écliptique de −p (t − 2000), distances au pôle de Polaris, Véga, Thuban et Kochab à plusieurs dates, années
# du plus proche passage (minimisation), période 360°/p, année où le point vernal quitte les Poissons pour le Verseau.
# Usage : sage outils/verif_anim/precession_verif.sage   (écrit tests/precession_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'precession_sage.json'))
R = RealField(120)
def f10(x):
    return float('%.10g' % float(x))
p = R('5028.796195')/3600/100                     # ° par an
eps = R('84381.406')/3600
d2r = R(pi)/180
def Rx(a):
    return matrix(R, [[1, 0, 0], [0, cos(a), sin(a)], [0, -sin(a), cos(a)]])
def Rz(a):
    return matrix(R, [[cos(a), sin(a), 0], [-sin(a), cos(a), 0], [0, 0, 1]])
def v_eq(ra, dec):
    a, d = R(ra)*d2r, R(dec)*d2r
    return vector(R, [cos(d)*cos(a), cos(d)*sin(a), sin(d)])
M = Rx(eps*d2r)                                   # équatorial J2000 → écliptique J2000
pole2000 = M*vector(R, [0, 0, 1])
def pole(t):
    return Rz(p*(R(t) - 2000)*d2r)*pole2000         # rotation rétrograde autour de l'axe de l'écliptique
def dist(v, w):
    return arctan2((v.cross_product(w)).norm(), v*w)/d2r
ET = {'α UMi': (37.98, 89.26), 'α Lyr': (279.24, 38.79), 'α Dra': (211.10, 64.38), 'β UMi': (222.68, 74.16)}
out = {'sage': VERSION_SAGE, 'periode': f10(360/p), 'eps': f10(eps), 'distances': {}, 'minimum': {}}
for n, (ra, de) in ET.items():
    v = M*v_eq(ra, de)
    out['distances'][n] = {str(t): f10(dist(v, pole(t))) for t in (-12000, -2800, 0, 1500, 2026, 2100, 8000, 13800)}
    f = lambda t: float(dist(v, pole(t)))
    debut = {'α UMi': 2100, 'α Lyr': 13800, 'α Dra': -2800, 'β UMi': -1100}[n]
    tm = find_local_minimum(f, debut - 1500, debut + 1500, tol=1e-12)
    out['minimum'][n] = [f10(tm[1]), f10(tm[0])]
    print(n, out['minimum'][n])
# point vernal : longitude J2000 −p (t − 2000) ; limite Poissons/Verseau = 352,013° de la date 2026
lim = (R('352.013') - p*26) - 360
out['verseau'] = f10(2000 - lim/p)
out['taureau_belier'] = f10(2000 - (R('53.779') - p*26)/p)
print('Verseau', out['verseau'], 'Taureau → Bélier', out['taureau_belier'])
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False)
