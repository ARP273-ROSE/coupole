# Vérification SageMath de l'animation « Occultation d'une étoile par un astéroïde » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : vitesse de l'ombre à l'opposition √(GM☉/1 ua)(1 − 1/√r), échelle de
# Fresnel √(λΔ/2), diamètre de l'étoile projeté θΔ, cordes d'ellipses tournées (racines exactes de l'équation de la
# conique le long d'une droite), extrémités bruitées par le générateur de Park et Miller (entiers exacts), et
# ellipse ajustée par moindres carrés sur ces extrémités (équations normales résolues en rationnels, puis centre,
# demi-axes et orientation par les valeurs propres).
# Usage : sage outils/verif_anim/occultation_verif.sage   (écrit tests/occultation_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
R = RealField(120)
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'occultation_sage.json'))
GM = R('1.32712440018e20'); UA = R('149597870.700')
VT = sqrt(GM / (UA * 1000)) / 1000
out = {'sage': VERSION_SAGE, 'v_terre': float(VT), 'vitesse': {}, 'fresnel': {}, 'etoile': {}, 'cordes': [],
       'ajustements': []}
for r in ('1.5', '2.5', '5.2', '30', '96'):
    out['vitesse'][r] = float(VT * (1 - 1 / sqrt(R(r))))
for lam, d in (('550', '1.5'), ('550', '95'), ('700', '4.2')):
    out['fresnel'][lam + '_' + d] = float(sqrt(R(lam) * R('1e-12') * R(d) * UA / 2))
for th, d in (('0.1', '1.5'), ('45', '1.5'), ('2', '95')):
    out['etoile'][th + '_' + d] = float(R(th) * R(d) * UA / (R(648000000) / R(pi)))

def ellipse(a, b, psi, x0, y0):
    c, s = cos(R(psi) * R(pi) / 180), sin(R(psi) * R(pi) / 180)
    M = matrix(R, [[c, -s], [s, c]]) * diagonal_matrix(R, [1 / R(a) ** 2, 1 / R(b) ** 2]) * matrix(R, [[c, s], [-s, c]])
    return M, R(x0), R(y0)

def corde(el, y):
    M, x0, y0 = el
    x = polygen(R, 'x')
    dy = R(y) - y0
    P = M[0, 0] * x ** 2 + 2 * M[0, 1] * x * dy + M[1, 1] * dy ** 2 - 1
    rac = sorted(rr for rr, _ in P.roots(ring=R))
    return None if len(rac) < 2 else (x0 + rac[0], x0 + rac[1])

CAS = [((50, 40, 30, 0, 5), [-45, -30, -15, 0, 15, 30, 45], 1.1),
       ((1163, 1163, 0, 0, 116.3), [-900, -300, 0, 300, 900, 1300], 20),
       ((10.5, 7.875, 60, 0, -2.1), [-10.5, -7, -3.5, 0, 3.5, 7, 10.5], 0.5),
       ((50, 40, -75, 0, 0), [-20, 0, 20], 0)]
for (a, b, psi, x0, y0), ys, sig in CAS:
    el = ellipse(a, b, psi, x0, y0)
    cs = [corde(el, y) for y in ys]
    out['cordes'].append({'el': [float(a), float(b), float(psi), float(x0), float(y0)], 'ys': [float(y) for y in ys],
                          'cordes': [None if c is None else [float(c[0]), float(c[1])] for c in cs]})
    # bruit de Park et Miller, uniforme d'écart type sig
    m, xg = 2147483647, 2024
    pts = []
    br = []
    for y, c in zip(ys, cs):
        if c is None:
            br.append(None)
            continue
        e = []
        for _ in range(2):
            xg = (16807 * xg) % m
            e.append((2 * R(xg) / m - 1) * sqrt(R(3)) * R(sig))
        br.append([float(c[0] + e[0]), float(c[1] + e[1])])
        pts += [(c[0] + e[0], R(y)), (c[1] + e[1], R(y))]
    if len(pts) >= 5:
        A_ = matrix(R, [[x * x, x * y, y * y, x, y] for x, y in pts])
        sol = (A_.transpose() * A_).solve_right(A_.transpose() * vector(R, [1] * len(pts)))
        A, B, C, D, E = sol
        det = 4 * A * C - B * B
        xc = (B * E - 2 * C * D) / det; yc = (B * D - 2 * A * E) / det
        k = 1 - (D * xc + E * yc) / 2
        Q = matrix(R, [[A, B / 2], [B / 2, C]])
        l1, l2 = sorted(Q.eigenvalues())
        # vecteur propre de la plus petite valeur propre l1 (le grand axe), écrit à la main : (Q − l1 I) v = 0
        va, vb = vector(R, [B / 2, l1 - A]), vector(R, [l1 - C, B / 2])
        v1 = va if va.norm() >= vb.norm() else vb
        psi_f = R(atan2(v1[1], v1[0]) * 180 / pi)
        psi_f = psi_f - 180 * floor((psi_f + 90) / 180)          # ramené dans [−90°, 90°[
        out['ajustements'].append({'bruitees': br, 'x0': float(xc), 'y0': float(yc), 'a': float(sqrt(k / l1)),
                                   'b': float(sqrt(k / l2)), 'psi': float(psi_f)})
    else:
        out['ajustements'].append({'bruitees': br, 'aucun': True})
with open(SORTIE, 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False)[:1500])
