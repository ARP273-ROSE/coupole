# « L'atmosphère terrestre » (0.8.0) : vérification SageMath (RealField(120)) des formules de l'animation, réécrites
# ici d'après leurs publications.  sage outils/verif_atmosphere/atmosphere_verif.sage > tests/atmosphere_sage.json
#  masse d'air : sec z ; Kasten & Young (1989) ; Pickering (2002) ; coquille sphérique homogène (H = 8 km, R = 6371 km)
#  épaisseur optique : Rayleigh (Hansen & Travis 1974), Ångström (1929), ozone (gaussienne de Chappuis, modèle simplifié)
#  réfraction : Bennett (1982), Sæmundsson (1986), facteur P/1010 × 283/(273 + T) ; indice de Ciddor (1996)
#  aplatissement d'un disque de rayon 0,2666° centré sur l'horizon vrai ; avance du lever (h0 = −0,5667°)
import json
R = RealField(120)
D = R(pi) / 180

def secz(h): return 1 / sin(R(h) * D)
def ky(h): h = R(h); return 1 / (sin(h * D) + R('0.50572') * (h + R('6.07995')) ** R('-1.6364'))
def pick(h): h = R(h); return 1 / sin((h + 244 / (165 + 47 * h ** R('1.1'))) * D)
def chemin(h, H=R(8), Rt=R(6371)): h = R(h); return sqrt((Rt + H) ** 2 - (Rt * cos(h * D)) ** 2) - Rt * sin(h * D)
def tau_r(l, P=R('1013.25')): l = R(l); return R('0.008569') / l ** 4 * (1 + R('0.0113') / l ** 2 + R('0.00013') / l ** 4) * R(P) / R('1013.25')
def tau_a(l, b=R('0.05'), a=R('1.3')): return R(b) * R(l) ** (-R(a))
def tau_o(l, du=300): return R('0.042') * R(du) / 300 * exp(-R('0.5') * ((R(l) - R('0.60')) / R('0.09')) ** 2)
def k(l, P=R('1013.25'), b=R('0.05')): return 5 / (2 * log(R(10))) * (tau_r(l, P) + tau_a(l, b) + tau_o(l))
def fpt(P, T): return (R(P) / 1010) * (R(283) / (273 + R(T)))
def bennett(h, P=1010, T=10): h = max(R(-1), R(h)); return max(R(0), 1 / tan((h + R('7.31') / (h + R('4.4'))) * D)) / 60 * fpt(P, T)
def saem(h, P=1010, T=10): h = max(R(-1), R(h)); return max(R(0), R('1.02') / tan((h + R('10.3') / (h + R('5.11'))) * D)) / 60 * fpt(P, T)
def ciddor(l): s2 = 1 / R(l) ** 2; return (5792105 / (R('238.0185') - s2) + 167917 / (R('57.362') - s2)) * R(10) ** -8
def avance(lat, dec=0, h0=R('-0.5667')):
    p, d = R(lat) * D, R(dec) * D
    def H(h): return acos((sin(R(h) * D) - sin(p) * sin(d)) / (cos(p) * cos(d))) / D
    return (H(h0) - H(0)) / 15 * 60 * R('0.99726957')

out = {'outil': 'SageMath, RealField(120)', 'masse_air': [], 'bandes': [], 'refraction': [], 'ciddor': [],
       'aplatissement': [], 'avance': []}
for h in (0, 0.5, 1, 2, 5, 10, 20, 30, 45, 60, 90):
    out['masse_air'].append({'h': h, 'secz': float(secz(h)) if h > 0 else None, 'kasten_young': float(ky(h)),
                             'pickering': float(pick(h)), 'chemin_km': float(chemin(h)), 'sphere': float(chemin(h) / 8)})
for b, l in (('U', 0.365), ('B', 0.445), ('V', 0.551), ('R', 0.658), ('I', 0.806)):
    for P in (1013.25, 740):
        out['bandes'].append({'bande': b, 'lambda': l, 'P': P, 'tau_r': float(tau_r(R(l), R(P))), 'tau_a': float(tau_a(R(l))),
                              'tau_o': float(tau_o(R(l))), 'k': float(k(R(l), R(P)))})
for h in (-1, 0, 0.5, 2, 5, 10, 20, 45, 89):
    for P, T in ((1010, 10), (740, -5), (1030, 30)):
        out['refraction'].append({'h': h, 'P': P, 'T': T, 'bennett': float(bennett(h, P, T)), 'saemundsson': float(saem(h, P, T))})
for l in (0.4, 0.45, 0.55, 0.65, 0.8):
    out['ciddor'].append({'lambda': l, 'n_moins_1': float(ciddor(R(l)))})
for P, T in ((1010, 10), (740, -5)):
    r = R('0.2666')
    bas, haut = -r, r
    hb, hh = bas + saem(bas, P, T), haut + saem(haut, P, T)
    out['aplatissement'].append({'P': P, 'T': T, 'rapport': float((hh - hb) / (2 * r))})
for lat in (0, 30, 48.8, 60):
    out['avance'].append({'lat': lat, 'minutes': float(avance(lat))})
print(json.dumps(out, indent=1, default=float))
