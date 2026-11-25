# Vérification SageMath de l'animation « Les éléments d'une orbite » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : périodes des orbites types (T = 2π √(a³/μ)), demi-grands axes des orbites
# géostationnaire et Molniya tirés du jour sidéral, vitesses au périgée et à l'apogée (vis-viva), et, pour un jeu
# d'éléments, l'anomalie excentrique (équation de Kepler, racine numérique), l'anomalie vraie, la distance, la
# position et la vitesse dans le repère équatorial (matrices de rotation exactes Rz(Ω) Rx(i) Rz(ω)), et le point
# sous le satellite.
# Constantes : μ = GM⊕ = 398 600,4418 km³ s⁻² (IERS 2010 / WGS 84) ; R⊕ = 6 378,137 km ; jour sidéral 86 164,0905 s.
# Usage : sage outils/verif_anim/elements_orbite_verif.sage   (écrit tests/elements_orbite_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
R = RealField(120)
PI = R(pi)
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'elements_orbite_sage.json'))
MU = R('398600.4418'); RT = R('6378.137'); JS = R('86164.0905')
def T(a): return 2 * PI * sqrt(R(a) ** 3 / MU)
def vv(r, a): return sqrt(MU * (2 / R(r) - 1 / R(a)))
D = lambda x: R(x) * PI / 180
def mod360(x):
    x = R(x)
    return x - 360 * floor(x / 360)      # (le % de Sage garde le signe du dividende)
def Rz(t): return matrix(R, [[cos(t), -sin(t), 0], [sin(t), cos(t), 0], [0, 0, 1]])
def Rx(t): return matrix(R, [[1, 0, 0], [0, cos(t), -sin(t)], [0, sin(t), cos(t)]])
out = {'sage': VERSION_SAGE, 'periodes': {}, 'vitesses': {}}
ORB = {'iss': ('6795', '0.0005'), 'polaire': ('7178', '0.001'), 'gps': ('26560', '0.01'), 'molniya': ('26562', '0.74'),
       'geo': ('42164', '0')}
for k, (a, e) in ORB.items():
    out['periodes'][k] = float(T(a))
    a, e = R(a), R(e)
    out['vitesses'][k] = [float(vv(a * (1 - e), a)), float(vv(a * (1 + e), a))]
out['a_geo'] = float((MU * (JS / (2 * PI)) ** 2) ** (R(1) / 3))
out['a_molniya'] = float((MU * (JS / 2 / (2 * PI)) ** 2) ** (R(1) / 3))
cas = []
for (a, e, i, Om, w, M, t) in (('18000', '0.3', '40', '45', '60', '100', '5000'), ('26562', '0.74', '63.4', '45', '270', '200', '30000'),
                               ('7178', '0.001', '98.6', '45', '90', '359', '100'), ('9000', '0.5', '150', '300', '10', '30', '0')):
    a, e = R(a), R(e)
    m = D(M)
    E = R(find_root(lambda x: x - e * sin(x) - m, 0, 2 * PI))
    nu = 2 * atan2(sqrt(1 + e) * sin(E / 2), sqrt(1 - e) * cos(E / 2))
    r = a * (1 - e * cos(E))
    p = a * (1 - e ** 2); h = sqrt(MU * p)
    rot = Rz(D(Om)) * Rx(D(i)) * Rz(D(w))
    pos = rot * vector(R, [r * cos(nu), r * sin(nu), 0])
    vit = rot * vector(R, [-MU / h * sin(nu), MU / h * (e + cos(nu)), 0])
    t = R(t)
    lat = atan2(pos[2], sqrt(pos[0] ** 2 + pos[1] ** 2)) * 180 / PI
    lon = (atan2(pos[1], pos[0]) - 2 * PI / JS * t) * 180 / PI
    lon = mod360(lon + 180) - 180
    cas.append({'el': [float(a), float(e), float(R(i)), float(R(Om)), float(R(w)), float(R(M))], 't': float(t),
                'E': float(mod360(E * 180 / PI)), 'nu': float(mod360(nu * 180 / PI)), 'r': float(r), 'v': float(vv(r, a)),
                'pos': [float(x) for x in pos], 'vit': [float(x) for x in vit], 'lat': float(lat), 'lon': float(lon),
                'norme_vit': float(vit.norm())})
out['cas'] = cas
with open(SORTIE, 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False)[:2500])
