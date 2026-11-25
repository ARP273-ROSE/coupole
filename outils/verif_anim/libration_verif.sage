# Vérification SageMath de l'animation « Rotation synchrone et libration » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : anomalie vraie (équation de Kepler à 40 chiffres), libration en longitude
# l = ν − M et en latitude b = arcsin(sin I sin(ν + ϖ)), maximum de l (≈ 2e), libration diurne arcsin(R⊕/a), puis la
# part de la surface vue au moins une fois par une méthode indépendante : grille fine de la sphère (aires exactes
# des bandes), chaque point déclaré vu s'il est à moins de 90° + ρ d'une des directions de la Terre (720 instants).
# Usage : sage outils/verif_anim/libration_verif.sage   (écrit tests/libration_sage.json)
import json, os
import numpy as np
import mpmath
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'libration_sage.json'))
mpmath.mp.dps = 40
def f10(x):
    return float('%.10g' % float(x))
def nu_de(M, e):
    M, e = mpmath.mpf(str(M)), mpmath.mpf(str(e))
    E = mpmath.findroot(lambda E: E - e*mpmath.sin(E) - M, M)
    return 2*mpmath.atan2(mpmath.sqrt(1 + e)*mpmath.sin(E/2), mpmath.sqrt(1 - e)*mpmath.cos(E/2))
def lib(M, e, I, w, sync=True):
    nu = nu_de(M, e)
    l = nu - (mpmath.mpf(str(M)) if sync else 0)
    l = mpmath.atan2(mpmath.sin(l), mpmath.cos(l))
    b = mpmath.asin(mpmath.sin(mpmath.radians(mpmath.mpf(str(I))))*mpmath.sin(nu + mpmath.radians(mpmath.mpf(str(w)))))
    return mpmath.degrees(l), mpmath.degrees(b)
out = {'sage': VERSION_SAGE, 'libration': {}}
for M in ('0.3', '1.0', '2.0', '3.0', '4.5', '6.0'):
    for e, I, w in (('0.0549', '6.68', '90'), ('0.2', '10', '30'), ('0.0549', '6.68', '250')):
        l, b = lib(M, e, I, w)
        out['libration']['%s,%s,%s,%s' % (M, e, I, w)] = [f10(l), f10(b)]
# maximum de l pour la Lune : 2e + (5/4)e³… (développement) et valeur exacte
e = mpmath.mpf('0.0549')
Mmax = mpmath.findroot(lambda M: mpmath.diff(lambda x: lib(x, e, 0, 0)[0], M), 1.5)
out['l_max'] = f10(lib(Mmax, e, 0, 0)[0])
out['rho_diurne'] = f10(mpmath.degrees(mpmath.asin(mpmath.mpf('6378.137')/mpmath.mpf('384400'))))
print('l_max', out['l_max'], 'rho', out['rho_diurne'])
# part vue : grille de la sphère
def fraction(dirs, rho):
    s = np.sin(np.radians(rho))
    nlat, nlon = 720, 1440
    lat_b = np.linspace(-np.pi/2, np.pi/2, nlat + 1)
    aire = (np.sin(lat_b[1:]) - np.sin(lat_b[:-1]))/2.0/nlon         # aire (fraction de sphère) de chaque case
    lat = (lat_b[1:] + lat_b[:-1])/2; lon = (np.arange(nlon) + 0.5)*2*np.pi/nlon
    LA, LO = np.meshgrid(lat, lon, indexing='ij')
    P = np.stack([np.cos(LA)*np.cos(LO), np.cos(LA)*np.sin(LO), np.sin(LA)], axis=-1)
    vu = np.zeros(LA.shape, dtype=bool)
    for S in dirs:
        vu |= (P @ np.array(S)) > -s
    return float((vu*aire[:, None]).sum())
def dirs_cycle(e, I, w, sync=True, n=720):
    d = []
    for j in range(n):
        l, b = lib(2*mpmath.pi*j/n, e, I, w, sync)
        l, b = float(mpmath.radians(l)), float(mpmath.radians(b))
        d.append((np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)))
    return d
rho = float(out['rho_diurne'])
fr = {}
for e, I, w in (('0.0549', '6.68', '90'), ('0', '0', '0'), ('0.0549', '0', '0'), ('0.2', '10', '30')):
    d = dirs_cycle(e, I, w, n=240)
    fr['%s,%s,%s' % (e, I, w)] = [f10(fraction(d, 0.0)), f10(fraction(d, rho))]
dd = []
for k in range(12):
    dd += dirs_cycle('0.0549', '6.68', 30*k, n=120)
fr['annees'] = [f10(fraction(dd, 0.0)), f10(fraction(dd, rho))]
out['fractions'] = fr
print(json.dumps(fr))
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False)
