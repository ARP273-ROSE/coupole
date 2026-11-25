# Vérification SageMath de l'animation « Étoiles filantes et radiant » (code propre à Coupole).
# Recalcule ici, sans le code de Coupole : jour julien (Meeus, chap. 7), temps sidéral moyen de Greenwich
# (IAU 1982, Meeus éq. 12.4), angle horaire, hauteur et azimut du radiant (trigonométrie sphérique), taux horaire
# HR = ZHR × sin h ÷ r^(6,5 − m_lim) (International Meteor Organization), heure de culmination (temps sidéral égal
# à l'ascension droite, la nuit du maximum) et hauteur de culmination 90° − |φ − δ|.
# Données des essaims : calendrier de l'IMO (radiant au maximum, ZHR, indice de population r).
# Usage : sage outils/verif_anim/radiant_verif.sage   (écrit tests/radiant_sage.json)
import json, os
from sage.version import version as VERSION_SAGE
R = RealField(120)
PI = R(pi)
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'radiant_sage.json'))
D = PI / 180
ES = {'quadrantides': (1, 4, 230, 49, 80, '2.1'), 'perseides': (8, 12, 48, 58, 100, '2.2'),
      'geminides': (12, 14, 112, 33, 150, '2.6'), 'eta_aquarides': (5, 6, 338, -1, 50, '2.4')}
def jj(an, mo, jo, h):
    if mo <= 2:
        an -= 1; mo += 12
    a = floor(an / 100); b = 2 - a + floor(a / 4)
    return floor(R(365.25) * (an + 4716)) + floor(R(30.6001) * (mo + 1)) + jo + R(h) / 24 + b - R(1524.5)
def tsmg(j):
    t = (j - R(2451545)) / 36525
    x = R('280.46061837') + R('360.98564736629') * (j - 2451545) + R('0.000387933') * t ** 2 - t ** 3 / 38710000
    return x - 360 * floor(x / 360)
out = {'sage': VERSION_SAGE, 'cas': []}
for k, (mo, jo, al, de, zhr, r) in ES.items():
    for lat in (45, -30, 60):
        for h in ('20', '23.5', '27', '29.75'):
            j = jj(2026, mo, jo, h)
            H = (tsmg(j) - al) * D
            phi, d = R(lat) * D, R(de) * D
            sh = sin(phi) * sin(d) + cos(phi) * cos(d) * cos(H)
            alt = arcsin(sh) / D
            az = atan2(-cos(d) * sin(H), sin(d) * cos(phi) - cos(d) * cos(H) * sin(phi)) / D
            az = az - 360 * floor(az / 360)
            for m in ('6.5', '5'):
                hr = R(zhr) * sin(alt * D) / R(r) ** (R('6.5') - R(m)) if alt > 0 else R(0)
                out['cas'].append({'essaim': k, 'lat': int(lat), 'heure': float(R(h)), 'mlim': float(R(m)),
                                   'az': float(az), 'h': float(alt), 'hr': float(hr)})
    th0 = tsmg(jj(2026, mo, jo, 18))
    dh = ((R(al) - th0) - 360 * floor((R(al) - th0) / 360)) / R('360.98564736629') * 24
    out.setdefault('culmination', {})[k] = float((18 + dh) - 24 * floor((18 + dh) / 24))
with open(SORTIE, 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(len(out['cas']), out['culmination'])
