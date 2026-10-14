# Machine d'Anticythère : vérification indépendante (SageMath, arithmétique rationnelle exacte) des rapports
# d'engrenages repris d'Anticythere3D (du même auteur) dans Coupole et Coupole Web.
#   docker exec sagemath sage /chemin/anticythere_verif.sage > anticythere_reference_sage.json
# Les nombres de dents sont ressaisis ici (Freeth et al., Nature 444, 2006 ; Nature 454, 2008) : rien n'est importé
# du code vérifié.  Sortie : JSON (fractions en « n/d », réels à 15 chiffres).
import json

Z = {'a1': 48, 'b1': 223, 'b2': 64, 'b3': 32, 'c1': 38, 'c2': 48, 'd1': 24, 'd2': 127,
     'e1': 32, 'e2': 32, 'e3': 223, 'e4': 188, 'e5': 50, 'e6': 50, 'f1': 53, 'f2': 30, 'g1': 54, 'g2': 20,
     'h1': 60, 'h2': 15, 'i1': 60, 'k1': 50, 'k2': 50, 'l1': 38, 'l2': 53, 'm1': 96, 'm2': 15, 'm3': 27,
     'n1': 53, 'n2': 15, 'o1': 60, 'p1': 60, 'p2': 12}
assert len(Z) == 33                                         # 33 roues (palier 2 : 30 attestées + entrée + phase)

def r(*paires):
    return prod(QQ(Z[a]) / Z[b] for a, b in paires)

lune = r(('b2', 'c1'), ('c2', 'd1'), ('d2', 'e2'))         # Lune sidérale, tours par an
meton = r(('b2', 'l1'), ('l2', 'm1'), ('m2', 'n1'))
callippe = meton * r(('n2', 'p1'), ('p2', 'o1'))
porte = r(('b2', 'l1'), ('l2', 'm1'), ('m3', 'e3'))
saros = porte * r(('e4', 'f1'), ('f2', 'g1'))
exel = saros * r(('g2', 'h1'), ('h2', 'i1'))

lunaisons_par_an = lune - 1                                 # Lune sidérale moins le tour du Soleil
assert lunaisons_par_an == QQ(235) / 19                     # cycle métonique : 235 lunaisons en 19 ans
assert meton == QQ(5) / 19                                  # 5 spires en 19 ans
assert callippe == QQ(1) / 76                               # 1 tour en 4 × 19 ans
assert saros == QQ(4) / 223 * lunaisons_par_an              # 4 spires pour 223 lunaisons
assert saros == QQ(940) / 4237
assert exel / saros == QQ(1) / 12 and exel == QQ(235) / 12711   # 1/3 de tour par Saros
assert lune == QQ(254) / 19 and porte == QQ(477) / 4237

AN = QQ(36524219) / 100000                                  # année tropique 365,24219 j (convention de la machine)
mois_anom = AN / (lune - porte)
mois_sid = AN / lune
mois_syn = AN / lunaisons_par_an
saros_j = 223 * mois_syn

# fraction continue : 235/19 est une réduite de 365,24219 / 29,530588853
reduites = continued_fraction(QQ(36524219) / 100000 / (QQ(29530588853) / 10**9)).convergents()[:8]

# relations de période des planètes (Freeth et al. 2021) : (cycles synodiques, années)
PL = {'mercury': (1513, 480, True), 'venus': (289, 462, True), 'mars': (133, 284, False),
      'jupiter': (315, 344, False), 'saturn': (427, 442, False)}
plan = {}
for k, (p, q, inf) in PL.items():
    sid = QQ(q + p) / q if inf else QQ(q - p) / q
    plan[k] = {'sidereal_ratio': str(sid), 'periode_ans': float(RealField(80)(1 / sid))}

# entraxes des 17 prises : m (N1 + N2) / 2, module 1 mm
prises = [('a1', 'b1'), ('b2', 'c1'), ('c2', 'd1'), ('d2', 'e2'), ('e5', 'k1'), ('k2', 'e6'), ('e1', 'b3'),
          ('b2', 'l1'), ('l2', 'm1'), ('m2', 'n1'), ('n2', 'p1'), ('p2', 'o1'), ('m3', 'e3'), ('e4', 'f1'),
          ('f2', 'g1'), ('g2', 'h1'), ('h2', 'i1')]

# tenon et fente : amplitude arcsin(ε / r), ε = 1,1 mm, r = 9,6 mm
R = RealField(100)
amplitude = R(arcsin(R(11) / 96) * 180 / pi)

# ère de Nabonassar : 1er Thoth de l'an 1 = 26 février −746 (calendrier julien) ; jour julien à midi
def jd_julien(a, m, j):
    if m <= 2:
        a, m = a - 1, m + 12
    return floor(R(365.25) * (a + 4716)) + floor(R(30.6001) * (m + 1)) + j - 1524   # midi
nabonassar = jd_julien(-746, 2, 26)

R15 = lambda x: float(RealField(80)(x))
print(json.dumps({
    'rapports': {'moon_sid': str(lune), 'metonic': str(meton), 'callippic': str(callippe), 'carrier_e3': str(porte),
                 'saros': str(saros), 'exeligmos': str(exel)},
    'lunaisons_par_an': str(lunaisons_par_an),
    'reduites_annee_sur_lunaison': [str(c) for c in reduites],
    'mois_anomalistique_j': R15(mois_anom), 'mois_sideral_j': R15(mois_sid), 'mois_synodique_j': R15(mois_syn),
    'saros_j': R15(saros_j), 'exeligmos_ans': R15(1 / exel), 'porte_satellite_ans': R15(1 / porte),
    'manivelle_jours_par_tour': R15(AN * 48 / 223),
    'planetes': plan,
    'entraxes_mm': {'%s-%s' % (a, b): R15(QQ(Z[a] + Z[b]) / 2) for a, b in prises},
    'tenon_fente_amplitude_deg': float(amplitude),
    'nabonassar_jd': int(nabonassar),
    'dents_total': int(sum(Z.values())),
}, indent=1, ensure_ascii=False))
