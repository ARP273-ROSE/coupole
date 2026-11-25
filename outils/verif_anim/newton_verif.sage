# Vérification SageMath des anneaux de Newton de l'animation « Interférences et interférométrie » (code propre à
# Coupole).  Recalcule ici, sans le code de Coupole : (1) les rayons des anneaux sombres en géométrie exacte (flèche
# d'une sphère e = R − √(R² − r²), racine de 2ne = kλ en réflexion, 2ne = (k − ½)λ en transmission), comparés à la formule
# √(kλR/n) de l'animation (lame mince, e ≈ r²/2R) ; (2) l'éclairement réfléchi de deux ondes d'amplitudes de Fresnel
# (verre d'indice 1,5 : coefficients ±(n₁ − n₂)/(n₁ + n₂), transmissions 1 − r²) normalisé entre son minimum et son
# maximum, comparé à (1 − cos(4πne/λ))/2 ; (3) l'éclairement du modèle à des rayons donnés (e exact contre r²/2R).
# Usage : sage outils/verif_anim/newton_verif.sage   (écrit tests/newton_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'newton_sage.json'))
def f15(x):
    return float('%.15g' % float(x))
out = {'sage': VERSION_SAGE, 'rayons': [], 'fresnel': [], 'eclairement': []}
CAS = [(1.0, 589.0, 1.0), (1.0, 450.0, 1.0), (5.0, 650.0, 1.33), (0.1, 2200.0, 1.0), (20.0, 350.0, 1.7)]
for R, lam, n in CAS:
    R, lam, n = RR(R), RR(lam), RR(n)
    for cote in ('reflexion', 'transmission'):
        for k in (1, 2, 3, 10, 12):
            kk = k if cote == 'reflexion' else k - 1/2
            e = kk*lam*1e-9/(2*n)                                   # épaisseur voulue (m)
            r_exact = sqrt(R^2 - (R - e)^2)*1e3                     # mm, sphère exacte
            r_mince = sqrt(kk*lam*1e-9*R/n)*1e3
            out['rayons'].append([float(R), float(lam), float(n), cote, k, f15(r_mince), f15(r_exact)])
# deux ondes de Fresnel (incidence normale) : dessous de la lentille (verre → lame, pas de déphasage si n_lame < n_verre)
# et dessus de la lame de verre (lame → verre, déphasage de π) ; phase 4πne/λ
nv = 1.5
for n in (1.0, 1.33):
    r1 = (nv - n)/(nv + n); r2 = (n - nv)/(n + nv); t = 1 - r1^2
    phi = var('phi')
    I = (r1 + t*r2*cos(phi))^2 + (t*r2*sin(phi))^2
    Imin, Imax = I.subs(phi=0), I.subs(phi=pi)
    for ph in (0.3, 1.0, 2.0, 3.0, 4.5):
        norm = (I.subs(phi=ph) - Imin)/(Imax - Imin)
        out['fresnel'].append([float(n), ph, f15(norm), f15((1 - cos(ph))/2), f15(Imin/Imax)])
for R, lam, n in CAS:
    for r_mm in (0.0, 0.2, 0.77, 1.5, 3.0):
        e_exact = (RR(R) - sqrt(RR(R)^2 - (RR(r_mm)*1e-3)^2))*1e9
        I = (1 - cos(4*pi*RR(n)*e_exact/RR(lam)))/2
        out['eclairement'].append([R, lam, n, r_mm, f15(I)])
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, default=float)
print(len(out['rayons']), 'rayons ;', out['fresnel'][:2])
