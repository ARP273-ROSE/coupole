"""Vérification SageMath du module « Pluies de météores » (td/meteores.py, jumeau web td_meteores.ts).

Calcule en précision étendue (RealField(80)) les valeurs de référence des tests :
  1. l'exemple du cours de J. Vaubaillon (ZHR = 100, LM = 4,0 ou 5,0, h = 50°, r = 2,2 → N ≈ 10 et 23) ;
  2. le tableau 1 de la fiche IMO (n pour ZHR = 100 selon la hauteur du radiant, LM = 6,5) ;
  3. la réduction ZHR = N r^(6,5−LM) / (F t sin h) et ZHR/√N ;
  4. le profil de Jenniskens des Perséides et des Géminides (deux composantes) ;
  5. la longitude solaire J2000 de Meeus (chap. 25) moins la précession, comparée aux instants publiés par l'IMO
     (calendrier 2027) — référence indépendante du code ;
  6. la hauteur du radiant des Perséides (précession IAU 1976, temps sidéral 1982, trigonométrie sphérique), pour
     comparer à ERFA (IAU 2006) utilisé par Coupole ;
  7. le centre du champ conseillé (hauteur 60°, à 30° du radiant) ;
  8. l'indice de population sur un échantillon.

Usage : docker exec -i sagemath sage -python - < outils/verif_meteores/meteores_verif_sage.py > tests/meteores_sage.json
"""
import json

from sage.all import RealField, pi, sin, cos, asin, acos, atan2, sqrt, floor

R = RealField(80)
D = R(pi) / 180
mod360 = lambda x: x - 360 * floor(x / 360)
out = {}

# 1. exemple du cours
n = lambda zhr, h, lm, r, f=1: R(zhr) * f * sin(R(h) * D) / R(r) ** (R(6.5) - R(lm))
out['cours'] = {'lm4': float(n(100, 50, 4.0, 2.2)), 'lm5': float(n(100, 50, 5.0, 2.2))}
# 2. tableau 1 de la fiche IMO
out['imo_tableau1'] = {str(h): float(n(100, h, 6.5, 2.5)) for h in (90, 70, 50, 40, 30, 20, 10)}
# 3. réduction
def zhr(N, t, lm, f, r, h):
    z = R(N) * R(r) ** (R(6.5) - R(lm)) / (R(f) * R(t) * sin(R(h) * D))
    return z, z / sqrt(R(N))
cas = [(10, 1.0, 4.0, 1.0, 2.2, 50.0), (37, 0.75, 5.8, 0.9, 2.6, 35.0), (120, 2.0, 6.2, 1.0, 2.2, 62.0)]
out['reduction'] = [{'n': c[0], 't': c[1], 'lm': c[2], 'f': c[3], 'r': c[4], 'h': c[5],
                     'zhr': float(zhr(*c)[0]), 'err': float(zhr(*c)[1])} for c in cas]
# 4. profils (Δλ en degrés, ZHR_max de l'IMO)
def profil(zm, comp, dl):
    tot = sum(R(c[0]) for c in comp)
    return R(zm) * sum(R(c[0]) * R(10) ** (-R(c[1] if dl < 0 else c[2]) * abs(R(dl))) for c in comp) / tot
PER = [[70, 0.35, 0.35], [23, 0.050, 0.092]]
GEM = [[74, 0.59, 0.81], [18, 0.09, 0.31]]
out['profils'] = {'PER': {str(dl): float(profil(110, PER, dl)) for dl in (-5, -1, 0, 0.5, 3)},
                  'GEM': {str(dl): float(profil(150, GEM, dl)) for dl in (-2, -0.5, 0, 0.5, 2)}}

# 5. longitude solaire
def jj(an, mo, j, h=0, mi=0):
    if mo <= 2:
        an, mo = an - 1, mo + 12
    a = floor(R(an) / 100)
    b = 2 - a + floor(a / 4)
    return floor(R(365.25) * (an + 4716)) + floor(R(30.6001) * (mo + 1)) + R(j) + b - R(1524.5) + (R(h) + R(mi) / 60) / 24


def lam2000(jj_utc):
    jt = jj_utc + R(69.184) / 86400
    t = (jt - R(2451545)) / 36525
    l0 = R(280.46646) + R(36000.76983) * t + R(0.0003032) * t ** 2
    m = R(357.52911) + R(35999.05029) * t - R(0.0001537) * t ** 2
    c = ((R(1.914602) - R(0.004817) * t - R(0.000014) * t ** 2) * sin(m * D)
         + (R(0.019993) - R(0.000101) * t) * sin(2 * m * D) + R(0.000289) * sin(3 * m * D))
    om = R(125.04) - R(1934.136) * t
    lam = l0 + c - R(0.00569) - R(0.00478) * sin(om * D)
    return mod360(lam - R(1.39697137) * t)


imo = [((2027, 1, 4, 3, 25), 283.15), ((2027, 6, 11, 21, 55), 80.378), ((2027, 9, 1, 15, 30), 158.6),
       ((2027, 9, 10, 0, 0), 166.7), ((2027, 10, 6, 11, 0), 192.58), ((2027, 10, 9, 7, 0), 195.4),
       ((2027, 12, 23, 4, 0), 270.7), ((2016, 7, 28, 0, 7), 125.132)]
out['longitude_solaire'] = [{'date': '%04d-%02d-%02dT%02d:%02d:00Z' % d, 'imo': l, 'meeus': float(lam2000(jj(*d)))}
                            for d, l in imo]

# 6. hauteur du radiant des Perséides (α 48°, δ +58°, J2000) vue de l'Observatoire de Paris
def precession(a, d, jj_utc):
    T = (jj_utc + R(69.184) / 86400 - R(2451545)) / 36525
    z0 = (R(2306.2181) + (R(0.30188) + R(0.017998) * T) * T) * T / 3600 * D
    z = (R(2306.2181) + (R(1.09468) + R(0.018203) * T) * T) * T / 3600 * D
    th = (R(2004.3109) - (R(0.42665) + R(0.041833) * T) * T) * T / 3600 * D
    a, d = R(a) * D, R(d) * D
    A = cos(d) * sin(a + z0)
    B = cos(th) * cos(d) * cos(a + z0) - sin(th) * sin(d)
    C = sin(th) * cos(d) * cos(a + z0) + cos(th) * sin(d)
    return (atan2(A, B) + z), asin(C)


def hauteur(a, d, lat, lon, jj_utc):
    ad, dd = precession(a, d, jj_utc)
    Tu = (jj_utc - R(2451545)) / 36525
    gmst = R(280.46061837) + R(360.98564736629) * (jj_utc - R(2451545)) + R(0.000387933) * Tu ** 2 - Tu ** 3 / 38710000
    H = (gmst + R(lon)) * D - ad
    p = R(lat) * D
    sh = sin(p) * sin(dd) + cos(p) * cos(dd) * cos(H)
    az = atan2(-cos(dd) * sin(H), sin(dd) * cos(p) - cos(dd) * cos(H) * sin(p))
    return asin(sh) / D, mod360(az / D)


out['hauteur'] = []
for d in ((2027, 8, 13, 2, 0), (2027, 8, 12, 21, 30), (2026, 12, 14, 1, 0)):
    a, de = (48.0, 58.0) if d[1] == 8 else (113.0, 33.0)
    h, az = hauteur(a, de, 48.8366, 2.336, jj(*d))
    out['hauteur'].append({'date': '%04d-%02d-%02dT%02d:%02d:00Z' % d, 'alpha': a, 'delta': de,
                           'lat': 48.8366, 'lon': 2.336, 'h': float(h), 'az': float(az)})

# 7. centre du champ : hauteur 60°, séparation 30° avec le radiant (az_r, h_r)
champs = []
for azr, hr in ((40.0, 45.0), (300.0, 70.0), (180.0, 25.0)):
    c = (cos(30 * D) - sin(R(hr) * D) * sin(60 * D)) / (cos(R(hr) * D) * cos(60 * D))
    daz = acos(max(R(-1), min(R(1), c))) / D
    az = mod360(R(azr) + daz)
    sep = acos(sin(R(hr) * D) * sin(60 * D) + cos(R(hr) * D) * cos(60 * D) * cos((az - R(azr)) * D)) / D
    champs.append({'az_r': azr, 'h_r': hr, 'daz': float(daz), 'sep': float(sep)})
out['champ'] = champs

# 8. indice de population : Φ(m+1)/Φ(m) cumulés jusqu'à m+1 ≤ LM − 1
comptes = {-1: 2, 0: 4, 1: 9, 2: 21, 3: 38, 4: 55, 5: 30}
lm = R(6.0)
cum, s = {}, 0
for m in range(-1, 7):
    s += comptes.get(m, 0)
    cum[m] = s
rap = [(m, R(cum[m + 1]) / cum[m]) for m in sorted(cum) if m + 1 in cum and m + 1 <= lm - 1 and cum[m] >= 3]
out['indice'] = {'comptes': {str(k): v for k, v in comptes.items()}, 'lm': 6.0,
                 'rapports': [[m, float(x)] for m, x in rap], 'r': float(sum(x for _, x in rap) / len(rap))}
print(json.dumps(out, indent=1, ensure_ascii=False))
