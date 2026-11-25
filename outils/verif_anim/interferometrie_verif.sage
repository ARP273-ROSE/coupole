# Vérification SageMath de l'animation « Interférences et interférométrie » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : interfrange λ / B et résolution 1,22 λ / d des instruments proposés,
# visibilité d'un disque uniforme |2 J₁(x)/x| (x = π θ B / λ) et sa base de premier zéro (Bételgeuse à 575 nm :
# ≈ 3,07 m, la base où Michelson et Pease ont vu disparaître les franges), visibilité complexe d'un couple
# (1 + r e^(−2iπ B ρ/λ)) / (1 + r), son minimum (1 − r)/(1 + r) à B = λ/(2ρ), et l'intensité des franges
# I(α) = ½ A(α) (1 + |V| cos(2π B α/λ − arg V)) en quelques points, A = (2 J₁(u)/u)², u = π d α / λ.
# Usage : sage outils/verif_anim/interferometrie_verif.sage   (écrit tests/interferometrie_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
R = RealField(120)
PI = R(pi)
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'interferometrie_sage.json'))
MAS = R(648000000) / PI                           # mas par radian
NM = R(10) ** -9

def J1(x):
    return R(bessel_J(1, R(x)))

def vis_disque(theta_mas, b, lam_nm):
    x = PI * R(theta_mas) / MAS * R(b) / (R(lam_nm) * NM)
    return 2 * J1(x) / x

def vis_couple(rho_mas, b, lam_nm, r):
    u = R(b) / (R(lam_nm) * NM)
    t = R(rho_mas) / MAS
    CC = ComplexField(120)
    return (1 + R(r) * exp(CC(0, -2) * PI * u * t)) / (1 + R(r))

def airy(u):
    u = R(u)
    return R(1) if u == 0 else (2 * J1(u) / u) ** 2

def intensite(alpha_mas, b, d, lam_nm, v):
    lam = R(lam_nm) * NM
    a = R(alpha_mas) / MAS
    CC = ComplexField(120)
    v = CC(v)
    return R(1) / 2 * airy(PI * R(d) * a / lam) * (1 + abs(v) * cos(2 * PI * R(b) * a / lam - arg(v)))

v1 = R(find_root(lambda x: J1(x), 3, 4.5))
out = {'sage': VERSION_SAGE, 'v1': float(v1), 'instruments': {}, 'disque': [], 'couple': [], 'intensite': []}
for k, b, d in (('young', '0.0005', '0.0001'), ('michelson', '6.1', '0.15'), ('vlti_ut', '130', '8.2'),
                ('vlti_at', '200', '1.8'), ('chara', '331', '1')):
    out['instruments'][k] = {lam: {'frange': float(R(lam) * NM / R(b) * MAS),
                                   'seul': float(v1 / PI * R(lam) * NM / R(d) * MAS)} for lam in ('550', '2200')}
for th, b, lam in (('47', '2.5', '575'), ('47', '3', '575'), ('47', '6.1', '575'), ('5', '130', '2200'),
                   ('6', '200', '2200'), ('3.3', '331', '1650'), ('1', '10', '550'), ('0.5', '331', '550')):
    out['disque'].append({'theta': float(th), 'b': float(b), 'lam': float(lam), 'v': float(vis_disque(th, b, lam))})
out['zero_betelgeuse_575'] = float(v1 / PI * R(575) * NM / (R(47) / MAS))
out['zero_sirius_2200'] = float(v1 / PI * R(2200) * NM / (R(6) / MAS))
for rho, b, lam, dm in (('56', '1', '550', '0.1'), ('56', '3', '2200', '0'), ('20', '130', '2200', '1.5'),
                        ('20', '4.0', '550', '0')):
    r = R(10) ** (-R('0.4') * R(dm))
    v = vis_couple(rho, b, lam, r)
    out['couple'].append({'rho': float(rho), 'b': float(b), 'lam': float(lam), 'dm': float(dm),
                          're': float(real(v)), 'im': float(imag(v)), 'mod': float(abs(v)),
                          'b_min': float(R(lam) * NM / (2 * R(rho) / MAS)), 'v_min': float((1 - r) / (1 + r))})
for alpha, b, d, lam, genre, taille in (('0', '130', '8.2', '2200', 'disque', '5'),
                                         ('1.2', '130', '8.2', '2200', 'disque', '5'),
                                         ('20', '130', '8.2', '2200', 'disque', '5'),
                                         ('10', '6.1', '0.15', '575', 'disque', '47'),
                                         ('3', '200', '1.8', '2200', 'couple', '20'),
                                         ('0.7', '331', '1', '550', 'point', '0')):
    if genre == 'disque':
        v = vis_disque(taille, b, lam)
    elif genre == 'couple':
        v = vis_couple(taille, b, lam, 1)
    else:
        v = R(1)
    out['intensite'].append({'alpha': float(alpha), 'b': float(b), 'd': float(d), 'lam': float(lam),
                             'genre': genre, 'taille': float(taille),
                             'i': float(intensite(alpha, b, d, lam, v))})
with open(SORTIE, 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
