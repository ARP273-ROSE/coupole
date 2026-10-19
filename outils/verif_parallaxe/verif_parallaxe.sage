# Partages du DU, outil Parallaxe : vérification INDÉPENDANTE (SageMath, 200 bits) des briques géométriques.
#   docker exec sagemath sage /chemin/outils/verif_parallaxe/verif_parallaxe.sage > tests/parallaxe_reference_sage.json
# Rien n'est importé de Coupole : formules réécrites ici d'après leurs définitions.
#  * ellipsoïde WGS84 (a = 6 378 137 m, 1/f = 298,257 223 563) : géodésique → cartésien, et l'inverse par itération
#    à 200 bits jusqu'à stabilité ;
#  * point le plus proche de deux droites (équations normales 2 × 2 résolues exactement) ;
#  * réfraction : Bennett (1982) pour une hauteur apparente, Saemundsson (1986) pour une hauteur vraie ;
#  * cercle de Kåsa : moindres carrés algébriques x² + y² = A x + B y + C, résolus exactement sur QQ ;
#  * orbite circulaire : vitesse angulaire apparente d'un satellite au zénith d'un lieu, et sa racine (altitude).
import json

R = RealField(200)
A_WGS = R(6378137)
F_WGS = 1 / R('298.257223563')
E2 = F_WGS * (2 - F_WGS)
DEG = R(pi) / 180


def ecef(lat, lon, h):
    la, lo = R(lat) * DEG, R(lon) * DEG
    N = A_WGS / sqrt(1 - E2 * sin(la) ** 2)
    return [(N + h) * cos(la) * cos(lo) / 1000, (N + h) * cos(la) * sin(lo) / 1000, (N * (1 - E2) + h) * sin(la) / 1000]


def geodesique(x, y, z):
    x, y, z = R(x) * 1000, R(y) * 1000, R(z) * 1000
    p = sqrt(x * x + y * y)
    lo = atan2(y, x)
    la = atan2(z, p * (1 - E2))
    for _ in range(60):
        N = A_WGS / sqrt(1 - E2 * sin(la) ** 2)
        h = p / cos(la) - N
        la = atan2(z, p * (1 - E2 * N / (N + h)))
    N = A_WGS / sqrt(1 - E2 * sin(la) ** 2)
    h = p / cos(la) - N
    return [la / DEG, lo / DEG, h / 1000]


def unit(v):
    n = sqrt(sum(c * c for c in v))
    return [c / n for c in v]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def trianguler(O1, u1, O2, u2):
    u1, u2 = unit([R(c) for c in u1]), unit([R(c) for c in u2])
    O1, O2 = [R(c) for c in O1], [R(c) for c in O2]
    w = [b - a for a, b in zip(O1, O2)]
    c = dot(u1, u2)
    M = matrix(R, [[1, -c], [c, -1]])
    d1, d2 = M.solve_right(vector(R, [dot(w, u1), dot(w, u2)]))
    P1 = [o + d1 * u for o, u in zip(O1, u1)]
    P2 = [o + d2 * u for o, u in zip(O2, u2)]
    milieu = [(a + b) / 2 for a, b in zip(P1, P2)]
    return milieu, d1, d2, sqrt(sum((a - b) ** 2 for a, b in zip(P1, P2)))


def bennett(h):
    h = R(h)
    return (1 / tan((h + R('7.31') / (h + R('4.4'))) * DEG)) / 60


def saemundsson(h):
    h = R(h)
    return (R('1.02') / tan((h + R('10.3') / (h + R('5.11'))) * DEG)) / 60


out = {'outil': 'SageMath, RealField(200)', 'ecef': [], 'geodesique': [], 'trianguler': [],
       'refraction': [], 'kasa': {}, 'orbite': []}

for lat, lon, h in ((48.8566, 2.3522, 35.0), (43.2965, 5.3698, 12.0), (-31.9523, 115.8613, 20.0),
                    (89.9, -45.0, 3000.0), (0.0, 180.0, 0.0), (-45.5, -70.25, 2400.0)):
    out['ecef'].append({'lat': lat, 'lon': lon, 'h_m': h, 'xyz_km': [float(c) for c in ecef(R(lat), R(lon), R(h))]})

for xyz in ((4019.25, 1225.5, 5268.75), (-2210.0, 4600.125, -4400.5), (6778.0, 0.0, 10.0), (1000.0, 2000.0, 6500.0)):
    out['geodesique'].append({'xyz_km': list(xyz), 'lat_lon_h': [float(c) for c in geodesique(*xyz)]})

paris, lyon = ecef(R('48.8566'), R('2.3522'), R(35)), ecef(R('45.764'), R('4.8357'), R(170))
for O1, u1, O2, u2 in (([float(c) for c in paris], (0.1, 0.2, 0.97), [float(c) for c in lyon], (0.15, 0.25, 0.96)),
                       ([0.0, 0.0, 0.0], (1.0, 0.0, 0.0), [0.0, 100.0, 0.0], (380000.0, -100.0, 0.5)),
                       ([6378.0, 0.0, 0.0], (0.6, 0.8, 0.0), [6000.0, 2000.0, 1000.0], (0.9, 0.3, 0.2))):
    M, d1, d2, e = trianguler(O1, u1, O2, u2)
    out['trianguler'].append({'O1': O1, 'u1': list(u1), 'O2': O2, 'u2': list(u2), 'milieu': [float(c) for c in M],
                              'd1': float(d1), 'd2': float(d2), 'ecart': float(e)})

for h in (0, 2, 5, 10, 20, 30, 45, 60, 80, 89):
    out['refraction'].append({'h_deg': h, 'bennett_deg': float(bennett(h)), 'saemundsson_deg': float(saemundsson(h))})

# cercle de Kåsa sur des points EXACTS (rationnels) d'un cercle perturbé de façon déterministe
pts = []
for k in range(40):
    t = 2 * pi * k / 40 + QQ(1) / 7
    r = QQ(150) + QQ((k * 37) % 11 - 5) / 10
    pts.append((QQ(round(RR(300.25 + r * cos(t)) * 1000)) / 1000, QQ(round(RR(250.5 + r * sin(t)) * 1000)) / 1000))
Aq = matrix(QQ, [[x, y, 1] for x, y in pts])
bq = vector(QQ, [x * x + y * y for x, y in pts])
c = (Aq.transpose() * Aq).solve_right(Aq.transpose() * bq)
xc, yc = c[0] / 2, c[1] / 2
out['kasa'] = {'points': [[float(x), float(y)] for x, y in pts], 'xc': float(xc), 'yc': float(yc),
               'r': float(sqrt(R(c[2] + xc ** 2 + yc ** 2)))}

# satellite au zénith d'un lieu de l'équateur (R = a) : ω = v / (r − R), v = √(GM/r) ; racine en r pour une vitesse angulaire donnée
GM = R('398600.4418')
Rt = A_WGS / 1000                      # lieu sur l'équateur, au niveau de l'ellipsoïde
for alt in (300, 420, 550, 800):
    r = Rt + alt
    w = sqrt(GM / r) / (r - Rt)
    f = lambda x: sqrt(GM / x) / (x - Rt) - w
    racine = find_root(f, Rt + 100, Rt + 3000, xtol=1e-14)
    out['orbite'].append({'R_km': float(Rt), 'altitude_km': alt, 'omega_rad_s': float(w),
                          'racine_altitude_km': float(R(racine) - Rt)})

print(json.dumps(out, indent=1, default=float))
