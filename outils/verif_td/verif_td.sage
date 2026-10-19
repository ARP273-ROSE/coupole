# Calculateur « Parallaxe (TP du cours) » : vérification INDÉPENDANTE (SageMath, RealField(200)) de la géométrie.
#   sage outils/verif_td/verif_td.sage outils/verif_td/cas_td.json > tests/td_parallaxe_sage.json
# Rien n'est importé de Coupole : WGS84 (a = 6 378 137 m, 1/f = 298,257 223 563), corde, distance à la surface
# (Vincenty, itéré à 200 bits), flèche (profondeur du milieu de la corde sous l'ellipsoïde, par itération de la
# latitude géodésique), profondeur de la corde sous chaque horizon, angle au centre, azimut d'un lieu vers l'autre,
# formule du sujet 2α = |h₁ − h₂| (ou 180° − h₁ − h₂ si l'objet est entre les lieux) et D = R / 2α, triangulation
# exacte (point le plus proche des deux visées) et altitude de l'objet.
import json, sys
R = RealField(200)
A = R(6378137) / 1000
F = 1 / R('298.257223563')
B = A * (1 - F)
E2 = F * (2 - F)
DEG = R(pi) / 180


def mod360(x):
    return x - 360 * floor(x / 360)


def V(*c):
    return vector(R, c)


def ecef(lat, lon, h_m):
    la, lo = R(lat) * DEG, R(lon) * DEG
    N = A / sqrt(1 - E2 * sin(la) ** 2)
    h = R(h_m) / 1000
    return V((N + h) * cos(la) * cos(lo), (N + h) * cos(la) * sin(lo), (N * (1 - E2) + h) * sin(la))


def geodetique(P):
    x, y, z = P
    p = sqrt(x * x + y * y)
    lo = atan2(y, x)
    la = atan2(z, p * (1 - E2))
    for _ in range(80):
        N = A / sqrt(1 - E2 * sin(la) ** 2)
        h = p / cos(la) - N
        la = atan2(z, p * (1 - E2 * N / (N + h)))
    N = A / sqrt(1 - E2 * sin(la) ** 2)
    return la / DEG, lo / DEG, p / cos(la) - N


def enu(lat, lon):
    la, lo = R(lat) * DEG, R(lon) * DEG
    return (V(-sin(lo), cos(lo), 0), V(-sin(la) * cos(lo), -sin(la) * sin(lo), cos(la)),
            V(cos(la) * cos(lo), cos(la) * sin(lo), sin(la)))


def vincenty(lat1, lon1, lat2, lon2):
    L = (R(lon2) - R(lon1)) * DEG
    U1, U2 = atan((1 - F) * tan(R(lat1) * DEG)), atan((1 - F) * tan(R(lat2) * DEG))
    lam = L
    for _ in range(500):
        sl, cl = sin(lam), cos(lam)
        ss = sqrt((cos(U2) * sl) ** 2 + (cos(U1) * sin(U2) - sin(U1) * cos(U2) * cl) ** 2)
        cs = sin(U1) * sin(U2) + cos(U1) * cos(U2) * cl
        sig = atan2(ss, cs)
        sa = cos(U1) * cos(U2) * sl / ss
        c2a = 1 - sa ** 2
        c2sm = cs - 2 * sin(U1) * sin(U2) / c2a
        C = F / 16 * c2a * (4 + F * (4 - 3 * c2a))
        nl = L + (1 - C) * F * sa * (sig + C * ss * (c2sm + C * cs * (-1 + 2 * c2sm ** 2)))
        if abs(nl - lam) < R(10) ** -45:
            lam = nl
            break
        lam = nl
    u2 = c2a * (A ** 2 - B ** 2) / B ** 2
    AA = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    BB = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    ds = BB * ss * (c2sm + BB / 4 * (cs * (-1 + 2 * c2sm ** 2) - BB / 6 * c2sm * (-3 + 4 * ss ** 2)
                                     * (-3 + 4 * c2sm ** 2)))
    return B * AA * (sig - ds)


def az_vers(o, P):
    E, N, Z = enu(o[0], o[1])
    v = P - ecef(*o[:3])
    a = atan2(v * E, v * N) / DEG
    return a + 360 if a < 0 else a


def direction(lat, lon, h, az):
    E, N, Z = enu(lat, lon)
    h, a = R(h) * DEG, R(az) * DEG
    return cos(h) * sin(a) * E + cos(h) * cos(a) * N + sin(h) * Z


cas = json.load(open(sys.argv[1]))['cas']
out = {'outil': 'SageMath, RealField(200)', 'cas': []}
for c in cas:
    o1, o2 = c['o1'], c['o2']
    r1, r2 = ecef(*o1[:3]), ecef(*o2[:3])
    Rc = (r2 - r1).norm()
    s = vincenty(o1[0], o1[1], o2[0], o2[1])
    s1, s2 = ecef(o1[0], o1[1], 0), ecef(o2[0], o2[1], 0)
    fleche = -geodetique((s1 + s2) / 2)[2]
    prof = []
    for o, w in ((o1, r2 - r1), (o2, r1 - r2)):
        prof.append(asin((w * enu(o[0], o[1])[2]) / Rc) / DEG)
    Z1, Z2 = enu(o1[0], o1[1])[2], enu(o2[0], o2[1])[2]
    theta = acos(Z1 * Z2) / DEG
    a12, a21 = az_vers(o1, r2), az_vers(o2, r1)
    entre = c['config'] == 'entre'
    if o1[4] is not None and o2[4] is not None:
        az1, az2 = R(o1[4]), R(o2[4])
        d = mod360(az1 - az2 + 180) - 180
        entre = abs(d) > 90
    elif entre:
        az1, az2 = a12, a21
    elif o1[3] >= o2[3]:
        az1, az2 = mod360(a12 + 180), a21
    else:
        az1, az2 = a12, mod360(a21 + 180)
    deux_alpha = (180 - R(o1[3]) - R(o2[3])) if entre else abs(R(o1[3]) - R(o2[3]))
    u1, u2 = direction(o1[0], o1[1], o1[3], az1), direction(o2[0], o2[1], o2[3], az2)
    w, cc = r2 - r1, u1 * u2
    d1, d2 = matrix(R, [[1, -cc], [cc, -1]]).solve_right(V(w * u1, w * u2))
    M = (r1 + d1 * u1 + r2 + d2 * u2) / 2
    la, lo, H = geodetique(M)
    out['cas'].append({'id': c['id'], 'corde_km': float(Rc), 'surface_km': float(s), 'fleche_km': float(fleche),
                       'fleche_approchee_km': float((s2 - s1).norm() ** 2 / (8 * R('6371.0088'))),
                       'profondeur_deg': [float(x) for x in prof], 'angle_centre_deg': float(theta),
                       'az_1_vers_2': float(a12), 'az_2_vers_1': float(a21), 'entre': bool(entre),
                       'deux_alpha_deg': float(deux_alpha), 'D_corde_km': float(Rc / (deux_alpha * DEG)),
                       'D_surface_km': float(s / (deux_alpha * DEG)), 'distances_km': [float(d1), float(d2)],
                       'distance_geo_km': float(M.norm()), 'altitude_km': float(H), 'sous_point': [float(la),
                                                                                                   float(lo)],
                       'ecart_droites_km': float((r1 + d1 * u1 - r2 - d2 * u2).norm())})
print(json.dumps(out, indent=1))
