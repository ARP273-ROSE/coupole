# Vérification SageMath de l'animation « Diffraction et pouvoir de résolution » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : premier zéro de J₁ (→ 1,22 λ/D), largeur à mi-hauteur de la tache d'Airy,
# premier zéro de l'amplitude d'une pupille à obstruction centrale (ε = 0,14 ; 0,33 ; 0,34), intensité au milieu de
# deux étoiles égales à l'écart de Rayleigh (73,5 %), éclat du premier anneau, valeurs de J₁ et de I₀ e^(−x) en
# quelques points (contrôle des approximations rationnelles recopiées dans Coupole), pouvoir de résolution des
# instruments proposés, diamètre où la tache d'Airy égale le seeing, et profil d'une pose longue (tache d'Airy
# convoluée par une gaussienne, intégrale numérique mpmath) en trois points.
# Usage : sage outils/verif_anim/resolution_verif.sage   (écrit tests/resolution_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
import mpmath
mpmath.mp.dps = 30
R = RealField(120)
PI = R(pi)
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'resolution_sage.json'))
SEC = R(648000) / PI

def J1(x):
    return R(bessel_J(1, R(x)))

def amp(v, eps):
    v = R(v); eps = R(eps)
    a = 2 * J1(v) / v
    if eps > 0:
        a -= eps ** 2 * 2 * J1(eps * v) / (eps * v)
    return a / (1 - eps ** 2)

def zero(eps):
    return R(find_root(lambda v: amp(v, eps), 2.5, 4.2))

v1 = R(find_root(lambda x: J1(x), 3, 4.5))
fw = 2 * R(find_root(lambda v: amp(v, 0) ** 2 - R(1) / 2, 1, 2)) / PI         # FWHM en λ/D
creux = 2 * amp(v1 / 2, 0) ** 2 / (1 + amp(v1, 0) ** 2)                       # milieu / sommet à l'écart de Rayleigh
# éclat du premier anneau : maximum de I entre le premier et le deuxième zéro
v2 = R(find_root(lambda x: J1(x), 6.5, 7.5))
vm = R(find_root(lambda v: R(bessel_J(2, R(v))), v1 + R(0.5), v2 - R(0.3)))   # I′ ∝ J₁ J₂ : sommet de l’anneau au zéro de J₂
anneau = amp(vm, 0) ** 2

out = {'sage': VERSION_SAGE,
       'v1': float(v1), 'rayleigh': float(v1 / PI), 'fwhm_airy': float(fw), 'creux_rayleigh': float(creux),
       'anneau1': float(anneau),
       'zeros': {str(e): float(zero(e)) for e in ('0.14', '0.33', '0.34')},
       'j1': {str(x): float(J1(x)) for x in ('0.5', '1', '3', '3.8317', '7', '8', '12.5', '30')},
       'i0e': {str(x): float(R(bessel_I(0, R(x))) * exp(-R(x))) for x in ('0.2', '1', '3.7', '3.8', '10', '80')},
       'instruments': {}, 'turbulence': {}}
for k, d in (('oeil', '0.007'), ('lunette80', '0.08'), ('sc200', '0.2032'), ('m1', '1'), ('hubble', '2.4'),
             ('vlt', '8.2'), ('elt', '39.3')):
    out['instruments'][k] = float(v1 / PI * R('550e-9') / R(d) * SEC)
for s, lam in (('1', '550'), ('0.5', '2200'), ('2', '550')):
    out['turbulence'][s + '_' + lam] = float(v1 / PI * R(lam) * R('1e-9') / (R(s) / SEC))

# Pose longue : D = 0,2 m, λ = 550 nm, seeing 0,3″ (convolution) : I(r)/I(0) en r = 0,2″, 0,5″, 1″
tv = R('550e-9') / (PI * R('0.2')) * SEC
sig = R('0.3') / (2 * sqrt(2 * log(R(2))))
def P(x):
    return amp(x / tv, 0) ** 2 if x > 0 else R(1)
def conv(r):
    f = lambda x: mpmath.mpf(P(R(x))) * mpmath.exp(-(r - x) ** 2 / (2 * sig ** 2)) * mpmath.besseli(0, r * x / sig ** 2) * mpmath.exp(-r * x / sig ** 2) * x
    return mpmath.quad(f, [0, tv * 3.83, tv * 7.02, tv * 10.17, tv * 13.32, r + 8 * sig + tv * 20]) / sig ** 2
I0 = conv(mpmath.mpf(0))
out['pose_longue'] = {str(r): float(conv(mpmath.mpf(r)) / I0) for r in ('0.2', '0.5', '1.0')}
with open(SORTIE, 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
