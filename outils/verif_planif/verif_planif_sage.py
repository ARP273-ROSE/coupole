"""Vérification SageMath des formules du planificateur (planif.py) : erreur de la formule du sujet, magnitude de
l'ISS, Δφ idéal de la Lune, angle au plan commun.  Données : sortie de references_skyfield.py, recopiées ici
(le conteneur sagemath ne voit pas le dépôt).

Usage : docker exec -i sagemath sage -python - < outils/verif_planif/verif_planif_sage.py
"""
from sage.all import RealField, pi, sin, cos, log, asin, sqrt, vector, arccos

R = RealField(80)
# géodésiques WGS84 → ECEF
a = R(6378.137); f = 1 / R(298.257223563); e2 = f * (2 - f)


def ecef(lat, lon, h_m):
    la, lo = R(lat) * pi / 180, R(lon) * pi / 180
    N = a / sqrt(1 - e2 * sin(la) ** 2)
    h = R(h_m) / 1000
    return vector(R, [(N + h) * cos(la) * cos(lo), (N + h) * cos(la) * sin(lo), (N * (1 - e2) + h) * sin(la)])


r1, r2 = ecef(48.8366, 2.3360, 67), ecef(45.76, 4.84, 170)
corde = (r2 - r1).norm()
print('corde Paris (Observatoire)–Lyon : %.6f km' % corde)

# 1. formule du sujet, cas « entre » : 2α = 180 − h1 − h2, D = R / 2α ; vraie distance au milieu donnée
h1, h2, Dvrai = R(66.0), R(56.9), None
deux_alpha = (180 - h1 - h2) * pi / 180
print('ISS entre, h = 66,0 / 56,9 : D_sujet = %.3f km' % (corde / deux_alpha))

# 2. magnitude ISS : m = −1,8 + 5 log10(d/1000) − 2,5 log10 F(β), F = (sin β + (π − β) cos β) / π
for d, beta in ((450, 30), (1200, 90), (800, 120)):
    b = R(beta) * pi / 180
    F = (sin(b) + (pi - b) * cos(b)) / pi
    print('magnitude d=%d km β=%d° : %.4f' % (d, beta, -1.8 + 5 * log(R(d) / 1000, 10) - R(2.5) * log(F, 10)))

# 3. Δφ idéal Lune (arcmin) pour la base et D = 384 400 km ; erreur relative si Δφ mesuré = 3,82′
ideal = corde / 384400 * 180 / pi * 60
print('Δφ idéal (D = 384 400 km) : %.5f′ ; Δφ = 3,82′ → D surestimée de %.2f %%' % (ideal, 100 * (ideal / R(3.82) - 1)))

# 4. fraction éclairée : k = (1 − cos E) / 2 (angle de phase ≈ 180° − élongation E)
for E in (0, 90, 180):
    print('élongation %3d° → k = %.4f' % (E, (1 - cos(R(E) * pi / 180)) / 2))
