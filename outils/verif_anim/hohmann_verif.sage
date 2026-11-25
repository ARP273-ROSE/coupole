# Vérification SageMath de l'animation « Le transfert de Hohmann » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : vitesses circulaires et sur l'ellipse de transfert (vis-viva), poussées,
# Δv total, durée (demi-période de l'ellipse), angle de phase au départ, période synodique des fenêtres de tir, et la
# position sur l'ellipse au quart et à la moitié du trajet (équation de Kepler, racine numérique).
# Constantes : GM⊕ = 398 600,4418 km³ s⁻² ; GM☉ = 1,327 124 400 18 × 10¹¹ km³ s⁻² (UAI) ; R⊕ = 6 378,137 km ;
# ua = 149 597 870,700 km ; Lune 384 400 km ; demi-grands axes de Mars 1,523 679, Vénus 0,723 332, Jupiter 5,202 6 ua.
# Usage : sage outils/verif_anim/hohmann_verif.sage   (écrit tests/hohmann_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
R = RealField(120)
PI = R(pi)
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'hohmann_sage.json'))
MT = R('398600.4418'); MS = R('1.32712440018e11'); RT = R('6378.137'); UA = R('149597870.700')
SC = {'leo_geo': (MT, RT + 200, R(42164)), 'leo_iss': (MT, RT + 200, RT + 417), 'terre_lune': (MT, RT + 200, R(384400)),
      'terre_mars': (MS, UA, R('1.523679') * UA), 'terre_venus': (MS, UA, R('0.723332') * UA),
      'terre_jupiter': (MS, UA, R('5.2026') * UA)}
out = {'sage': VERSION_SAGE}
for k, (mu, r1, r2) in SC.items():
    a = (r1 + r2) / 2; e = abs(r2 - r1) / (r2 + r1)
    v1, v2 = sqrt(mu / r1), sqrt(mu / r2)
    vd, va = sqrt(mu * (2 / r1 - 1 / a)), sqrt(mu * (2 / r2 - 1 / a))
    t = PI * sqrt(a ** 3 / mu)
    n1, n2 = sqrt(mu / r1 ** 3), sqrt(mu / r2 ** 3)
    ph = (PI - n2 * t) * 180 / PI
    ph = ph - 360 * floor((ph + 180) / 360)
    pos = {}
    for f in ('0.25', '0.5'):
        n = sqrt(mu / a ** 3)
        M = n * t * R(f) + (0 if r2 >= r1 else PI)
        E = R(find_root(lambda x: x - e * sin(x) - M, 0, 2 * PI))
        nu = 2 * atan2(sqrt(1 + e) * sin(E / 2), sqrt(1 - e) * cos(E / 2))
        r = a * (1 - e * cos(E))
        ang = nu if r2 >= r1 else PI + nu
        pos[f] = [float(r), float(ang)]
    out[k] = {'v1': float(v1), 'v2': float(v2), 'vd': float(vd), 'va': float(va), 'dv1': float(vd - v1),
              'dv2': float(v2 - va), 'dv': float(abs(vd - v1) + abs(v2 - va)), 't': float(t), 'phase': float(ph),
              'synodique': float(2 * PI / abs(n1 - n2)), 'position': pos}
with open(SORTIE, 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps({k: (v if k == 'sage' else {x: v[x] for x in ('dv1', 'dv2', 't', 'phase', 'synodique')}) for k, v in out.items()}, indent=1))
