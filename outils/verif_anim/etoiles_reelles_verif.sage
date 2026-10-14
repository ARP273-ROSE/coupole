# Vérification SageMath (précision 120 bits, indépendante du code Python et TypeScript) des valeurs calculées pour la
# 0.5.0 : conversion parsec → année-lumière (définitions UAI 2012 et 2015), distances et barres des étoiles des
# animations (al ↔ pc), parallaxe moyenne du Trapèze (Gaia DR3, 4 étoiles) et matrice ICRS → galactique (définition
# du repère galactique de Hipparcos : pôle nord galactique et longitude du pôle céleste).
# Usage : sage outils/verif_anim/etoiles_reelles_verif.sage   (écrit tests/etoiles_reelles_sage.json)
import gzip, json, os
R = RealField(120)
ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.abspath(os.path.join(ICI, '..', '..'))
D = os.path.join(DEPOT, 'coupole', 'modules', 'anim', 'donnees')

# [1] 1 pc = 648000/π ua ; 1 ua = 149 597 870 700 m (UAI 2012 B2) ; 1 al = c × 365,25 j (UAI)
pc_m = R(648000) / R(pi) * R(149597870700)
al_m = R(299792458) * R(36525) / R(100) * R(86400)
K = pc_m / al_m
res = {'pc_en_al': float(K)}

# [2] distances des étoiles des animations : al = pc × K (arrondis du jeu de données), barres comprises
F = json.load(gzip.open(os.path.join(D, 'fiches.json.gz'), 'rt'))['fiches']
ecart = R(0); ecart_barres = R(0); n = 0
for f in F.values():
    d = f.get('distance') or {}
    if 'pc' in d and 'al' in d:
        pc = R(d['pc']); al = R(d['al'])
        # le jeu de données arrondit al à 0,01 (≥ 10 al) ou 0,001 ; on compare en relatif
        ecart = max(ecart, abs(pc * K - al) / al)
        for a, b in (('pc_moins', 'al_moins'), ('pc_plus', 'al_plus')):
            if d.get(a) is not None and d.get(b) is not None and R(d[b]) > 1:
                ecart_barres = max(ecart_barres, abs(R(d[a]) * K - R(d[b])) / R(d[b]))
        n += 1
res['distances_verifiees'] = int(n)
res['ecart_relatif_max_al'] = float(ecart)
res['ecart_relatif_max_barres'] = float(ecart_barres)

# [3] Trapèze : ϖ = 2,4877 ± 0,0247 mas (moyenne pondérée Gaia DR3 de θ¹ Ori A–D, point zéro soustrait)
w, s = R('2.4877'), R('0.0247')
res['trapeze_pc'] = float(1000 / w)
res['trapeze_moins_pc'] = float(1000 / w - 1000 / (w + s))
res['trapeze_plus_pc'] = float(1000 / (w - s) - 1000 / w)

# [4] matrice ICRS → galactique depuis la définition (pôle nord galactique α = 192,85948°, δ = 27,12825° ;
#     longitude galactique du pôle nord céleste l = 122,93192°), comparée à celle d'astropy embarquée
a, d, l = [R(x) * R(pi) / 180 for x in ('192.85948', '27.12825', '122.93192')]
def rz(t):
    return matrix(R, [[cos(t), sin(t), 0], [-sin(t), cos(t), 0], [0, 0, 1]])
def ry(t):
    return matrix(R, [[cos(t), 0, -sin(t)], [0, 1, 0], [sin(t), 0, cos(t)]])
M = rz(R(pi) - l) * ry(R(pi) / 2 - d) * rz(a)
S = json.load(gzip.open(os.path.join(D, 'orion3d.json.gz'), 'rt'))
A = matrix(R, S['icrs_vers_gal'])
res['matrice_galactique_ecart_max'] = float(max(abs(x) for x in (M - A).list()))
res['matrice_galactique_orthonormee'] = float(max(abs(x) for x in (A * A.transpose() - identity_matrix(R, 3)).list()))

# [5] distance de quelques étoiles d'Orion à leur position (|xyz| = d) et séparation Tête de Cheval – σ Ori
E = {e['id']: e for e in S['etoiles']}
res['norme_xyz_moins_d_max'] = float(max(abs(sqrt(sum(R(v) ** 2 for v in e['xyz'])) - R(e['d'])) for e in S['etoiles']))
res['tabit_al'] = float(R(E['pi_03_ori']['d']) * K)
json.dump(res, open(os.path.join(DEPOT, 'tests', 'etoiles_reelles_sage.json'), 'w'), indent=int(1), ensure_ascii=False)
print(json.dumps(res, indent=int(1), ensure_ascii=False))
