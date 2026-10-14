"""La machine d'Anticythère, sans Qt : nombres de dents, trains, rapports EXACTS (fractions), tenon et fente, sorties
des cadrans, implantation des arbres, inscriptions des cadrans, astronomie de calage.  Adapté d'Anticythere3D, du même
auteur (anticythere/kinematics.py, layout.py, dialface.py, astro.py) : mêmes nombres, mêmes formules, mêmes tests ;
identique à src/calc/anticythere.ts de Coupole Web.

Sources des données : Freeth et al., Nature 444 (2006) 587–591 et notes supplémentaires (nombres de dents) ; Freeth,
Jones, Steele, Bitsakis, Nature 454 (2008) 614–617 (calendriers, Jeux, éclipses) ; Freeth et al., Scientific Reports
11:5821 (2021) (le Cosmos : relations de période des planètes) ; Meeus, Astronomical Algorithms, 2e éd., ch. 7, 25,
47, 54.

Convention : ``turns`` = tours de la grande roue b1 depuis l'époque de calage (J2000) ; 1 tour de b1 = 1 année
tropique.  Angles en TOURS, convertis en degrés à l'affichage."""
from __future__ import annotations

import math
from fractions import Fraction as F

TROPICAL_YEAR = 365.24219
SYNODIC_MONTH = 29.530588853

# ==================================================================== dents et trains
#: nombres de dents relevés par tomographie (Freeth et al. 2006, 2008)
TEETH = {
    'a1': 48, 'b1': 223, 'b2': 64, 'b3': 32, 'c1': 38, 'c2': 48, 'd1': 24, 'd2': 127,
    'e1': 32, 'e2': 32, 'e3': 223, 'e4': 188, 'e5': 50, 'e6': 50, 'f1': 53, 'f2': 30, 'g1': 54, 'g2': 20,
    'h1': 60, 'h2': 15, 'i1': 60, 'k1': 50, 'k2': 50, 'l1': 38, 'l2': 53, 'm1': 96, 'm2': 15, 'm3': 27,
    'n1': 53, 'n2': 15, 'o1': 60, 'p1': 60, 'p2': 12,
}

#: chaînes (roue menante, roue menée) ; deux roues de même lettre sont solidaires du même arbre
TRAINS = {
    'metonic': [('b2', 'l1'), ('l2', 'm1'), ('m2', 'n1')],
    'callippic': [('b2', 'l1'), ('l2', 'm1'), ('m2', 'n1'), ('n2', 'p1'), ('p2', 'o1')],
    'saros': [('b2', 'l1'), ('l2', 'm1'), ('m3', 'e3'), ('e4', 'f1'), ('f2', 'g1')],
    'exeligmos': [('b2', 'l1'), ('l2', 'm1'), ('m3', 'e3'), ('e4', 'f1'), ('f2', 'g1'), ('g2', 'h1'), ('h2', 'i1')],
    'moon_sid': [('b2', 'c1'), ('c2', 'd1'), ('d2', 'e2')],
    'carrier_e3': [('b2', 'l1'), ('l2', 'm1'), ('m3', 'e3')],
}


def train_ratio(pairs) -> F:
    """Produit exact des rapports (menante / menée) le long d'un train."""
    r = F(1)
    for a, b in pairs:
        r *= F(TEETH[a], TEETH[b])
    return r


#: rapports exacts, en tours de sortie par tour de b1 (donc par année)
RATIOS = {k: train_ratio(v) for k, v in TRAINS.items()}
RATIOS['mean_sun'] = F(1)
#: ligne des nœuds : rétrograde ; Freeth et al. 2021 proposent un train épicycloïdal réalisant −5/93
RATIOS['nodes'] = F(-5, 93)

#: valeurs attendues (non-régression), calculées indépendamment sous SageMath
EXPECTED = {'metonic': F(5, 19), 'callippic': F(1, 76), 'saros': F(940, 4237), 'exeligmos': F(235, 12711),
            'moon_sid': F(254, 19), 'carrier_e3': F(477, 4237)}


def self_check() -> list:
    errs = ['%s: attendu %s, obtenu %s' % (k, v, RATIOS[k]) for k, v in EXPECTED.items() if RATIOS[k] != v]
    if RATIOS['saros'] != F(4, 223) * F(235, 19):
        errs.append('saros != (4/223)x(235/19)')
    if RATIOS['exeligmos'] / RATIOS['saros'] != F(1, 12):
        errs.append('exeligmos/saros != 1/12')
    return errs


# ==================================================================== planètes (Freeth et al. 2021)
def _pl(syn, years, inferior, a):
    return {'syn': syn, 'years': years, 'inferior': inferior, 'a': a,
            'sidereal_ratio': F(years + syn, years) if inferior else F(years - syn, years)}


#: relations de période (cycles synodiques, années) ; ``a`` : demi-grand axe (ua), rapport épicycle / déférent
PLANETS = {'mercury': _pl(1513, 480, True, 0.387098), 'venus': _pl(289, 462, True, 0.723332),
           'mars': _pl(133, 284, False, 1.523679), 'jupiter': _pl(315, 344, False, 5.2026),
           'saturn': _pl(427, 442, False, 9.5549)}
NOMS_PLANETES = ('mercury', 'venus', 'mars', 'jupiter', 'saturn')


# ==================================================================== tenon et fente
class PinAndSlot:
    """Tenon et fente des roues k1/k2 : ε = 1,1 mm entre les axes, r = 9,6 mm (tomographie)."""

    def __init__(self, eps: float = 1.1, r: float = 9.6):
        self.eps, self.r = eps, r

    @property
    def amplitude_deg(self) -> float:
        return math.degrees(math.asin(self.eps / self.r))

    def delta_turns(self, rel_turns: float) -> float:
        th = 2.0 * math.pi * rel_turns
        return math.atan2(self.eps * math.sin(th), self.r + self.eps * math.cos(th)) / (2.0 * math.pi)

    def speed_ratio(self, rel_turns: float) -> float:
        th = 2.0 * math.pi * rel_turns
        return (self.r * (self.r + self.eps * math.cos(th))
                / (self.r ** 2 + self.eps ** 2 + 2.0 * self.r * self.eps * math.cos(th)))


# ==================================================================== machine
GAMES = ('isthmia', 'olympia', 'nemea', 'pythia')


def _mod(x: float, m: float) -> float:
    return x % m


class Mechanism:
    """La machine complète, purement numérique."""

    def __init__(self, pin=None, offsets=None):
        self.pin = pin or PinAndSlot()
        self.offsets = dict(mean_sun=0.0, moon=0.0, nodes=0.0, anomaly=0.0, metonic=0.0, saros=0.0, planets={})
        if offsets:
            self.offsets.update(offsets)
        self._turns = 0.0

    @property
    def turns(self) -> float:
        return self._turns

    @turns.setter
    def turns(self, v: float) -> None:
        if math.isfinite(v):
            self._turns = float(v)

    @property
    def days(self) -> float:
        return self._turns * TROPICAL_YEAR

    @days.setter
    def days(self, v: float) -> None:
        if math.isfinite(v):
            self._turns = float(v) / TROPICAL_YEAR

    def advance_days(self, n: float) -> None:
        self.days = self.days + n

    def raw(self, name: str) -> float:
        return float(RATIOS[name]) * self._turns

    def anomaly_phase(self) -> float:
        return self.raw('moon_sid') - self.raw('carrier_e3') + self.offsets['anomaly']

    def moon_true_turns(self):
        mean = self.raw('moon_sid') + self.offsets['moon']
        d = self.pin.delta_turns(self.anomaly_phase())
        return mean + d, d * 360.0

    def outputs(self) -> dict:
        t = self._turns
        mean_sun = t + self.offsets['mean_sun']
        moon_true, anom = self.moon_true_turns()
        phase = moon_true - mean_sun
        met = self.raw('metonic') + self.offsets['metonic']
        cal = self.raw('callippic')
        sar = self.raw('saros') + self.offsets['saros']
        exe = self.raw('exeligmos')
        # 1e-9 : après exactement 1 Saros, (1/3 % 1)*3 = 0,999… en flottant (frontière trouvée par SageMath)
        exe_sector = int(_mod(exe, 1.0) * 3.0 + 1e-9) + 1
        games_year = int(_mod(t, 4.0)) + 1
        return {
            'turns': t, 'days': self.days, 'mean_sun': mean_sun,
            'moon_mean': self.raw('moon_sid') + self.offsets['moon'], 'moon_true': moon_true,
            'moon_anomaly_deg': anom, 'carrier_e3': self.raw('carrier_e3'),
            'nodes': self.raw('nodes') + self.offsets['nodes'], 'phase_turns': phase,
            'phase_illum': (1.0 - math.cos(2.0 * math.pi * phase)) / 2.0,
            'metonic': met, 'metonic_cell': int(_mod(met, 5.0) / 5.0 * 235.0) + 1,
            'metonic_year': int(_mod(met / 5.0, 1.0) * 19.0) + 1,
            'callippic': cal, 'callippic_quarter': int(_mod(cal, 1.0) * 4.0) + 1,
            'saros': sar, 'saros_cell': int(_mod(sar, 4.0) / 4.0 * 223.0) + 1,
            'exeligmos': exe, 'exeligmos_sector': exe_sector, 'exeligmos_hours': ((exe_sector - 1) % 3) * 8,
            'games_year': games_year, 'games_name': GAMES[(games_year - 1) % 4],
            'planets': {k: float(d['sidereal_ratio']) * t + self.offsets['planets'].get(k, 0.0)
                        for k, d in PLANETS.items()},
        }

    def gear_angles(self) -> dict:
        """Angle (tours) de CHAQUE roue (mêmes chaînes que gear_angles d'Anticythere3D)."""
        t, T = self._turns, TEETH
        a = {}
        a['b1'] = a['b2'] = t
        a['a1'] = -t * T['b1'] / T['a1']
        r = t * (T['b2'] / T['c1'])
        a['c1'] = a['c2'] = -r
        r2 = -r * (T['c2'] / T['d1'])
        a['d1'] = a['d2'] = r2
        r3 = r2 * (T['d2'] / T['e2'])
        a['e2'] = a['e5'] = -r3
        carrier = self.raw('carrier_e3')
        a['e3'] = a['e4'] = carrier
        a['k1'] = a['e5']
        a['k2'] = a['k1'] + self.pin.delta_turns(self.anomaly_phase())
        a['e6'] = a['e1'] = -a['k2']
        a['b3'] = -a['e1']
        m = t * (T['b2'] / T['l1'])
        a['l1'] = a['l2'] = -m
        m2 = -m * (T['l2'] / T['m1'])
        a['m1'] = a['m2'] = a['m3'] = m2
        m3 = m2 * (T['m2'] / T['n1'])
        a['n1'] = a['n2'] = -m3
        m4 = -m3 * (T['n2'] / T['p1'])
        a['p1'] = a['p2'] = m4
        a['o1'] = -m4 * (T['p2'] / T['o1'])
        s2 = carrier * (T['e4'] / T['f1'])
        a['f1'] = a['f2'] = -s2
        s3 = -s2 * (T['f2'] / T['g1'])
        a['g1'] = a['g2'] = s3
        s4 = s3 * (T['g2'] / T['h1'])
        a['h1'] = a['h2'] = -s4
        a['i1'] = -s4 * (T['h2'] / T['i1'])
        return a


def _vitesses() -> dict:
    """Vitesse moyenne exacte de chaque roue (tours par an), signée comme gear_angles()."""
    T = TEETH
    r = {}
    r['b1'] = r['b2'] = F(1)
    r['a1'] = F(-T['b1'], T['a1'])
    c = -F(T['b2'], T['c1'])
    r['c1'] = r['c2'] = c
    d = c * F(T['c2'], T['d1'])
    r['d1'] = r['d2'] = d
    e = -(d * F(T['d2'], T['e2']))
    r['e2'] = r['e5'] = r['k1'] = r['k2'] = e
    r['e6'] = r['e1'] = -e
    r['b3'] = e
    car = RATIOS['carrier_e3']
    r['e3'] = r['e4'] = car
    lv = -F(T['b2'], T['l1'])
    r['l1'] = r['l2'] = lv
    m = lv * F(T['l2'], T['m1'])
    r['m1'] = r['m2'] = r['m3'] = m
    n = -(m * F(T['m2'], T['n1']))
    r['n1'] = r['n2'] = n
    p = n * F(T['n2'], T['p1'])
    r['p1'] = r['p2'] = p
    r['o1'] = -p * F(T['p2'], T['o1'])
    f = -(car * F(T['e4'], T['f1']))
    r['f1'] = r['f2'] = f
    g = f * F(T['f2'], T['g1'])
    r['g1'] = r['g2'] = g
    h = -(g * F(T['g2'], T['h1']))
    r['h1'] = r['h2'] = h
    r['i1'] = h * F(T['h2'], T['i1'])
    return r


#: vitesse moyenne exacte de chaque roue (la modulation du tenon-fente, de moyenne nulle, est omise)
GEAR_RATES = _vitesses()

# ==================================================================== implantation (layout.py)
MODULE = 1.0
GEAR_THICKNESS = 2.6
LEVEL_PITCH = 3.4
ARBOR_RADIUS = 2.0
EXPLODE_GAP = 12.0
N_LEVELS = 16

#: position (x, y) de chaque arbre, mm : optimisation sous contraintes (SageMath + scipy) d'Anticythere3D 1.3.1
ARBORS = {
    'K': (8.795, -30.198), 'a': (135.5, 0.0), 'b': (0.0, 0.0), 'c': (33.423, -38.521), 'd': (12.022, -67.469),
    'e': (-31.976, -1.254), 'f': (88.145, -10.797), 'g': (80.0, -52.0), 'h': (46.569, -30.036),
    'i': (15.326, -9.297), 'k': (10.007, -28.41), 'l': (21.528, 46.234), 'm': (91.22, 19.905), 'n': (80.0, 52.0),
    'o': (13.6707, 41.0575), 'p': (48.444, 31.74),
}
LEVELS = {
    'a1': 1, 'b1': 1, 'b2': 2, 'c1': 2, 'l1': 2, 'c2': 3, 'd1': 3, 'd2': 4, 'e2': 4, 'b3': 5, 'e1': 5, 'l2': 6,
    'm1': 6, 'm2': 7, 'n1': 7, 'e6': 8, 'k2': 8, 'e5': 9, 'k1': 9, 'e3': 10, 'm3': 10, 'e4': 11, 'f1': 11,
    'n2': 12, 'p1': 12, 'o1': 13, 'p2': 13, 'f2': 14, 'g1': 14, 'g2': 15, 'h1': 15, 'h2': 16, 'i1': 16,
}
SPOKED = {'b1': 4, 'e3': 4, 'e4': 4}
CARRIED_BY = {'k': 'e3', 'K': 'e3'}
MOUNTED_ON = {'k': 'e3'}
ARBOR_OF = {
    'a1': 'a', 'b1': 'b', 'b2': 'b', 'b3': 'b', 'c1': 'c', 'c2': 'c', 'd1': 'd', 'd2': 'd', 'e1': 'e', 'e2': 'e',
    'e3': 'e', 'e4': 'e', 'e5': 'e', 'e6': 'e', 'f1': 'f', 'f2': 'f', 'g1': 'g', 'g2': 'g', 'h1': 'h', 'h2': 'h',
    'i1': 'i', 'k1': 'k', 'k2': 'K', 'l1': 'l', 'l2': 'l', 'm1': 'm', 'm2': 'm', 'm3': 'm', 'n1': 'n', 'n2': 'n',
    'o1': 'o', 'p1': 'p', 'p2': 'p',
}
SUBSYSTEMS = {
    'input': ('b1', 'b2', 'a1'), 'moon': ('c1', 'c2', 'd1', 'd2', 'e2', 'e5', 'e6', 'e1', 'b3'),
    'anomaly': ('k1', 'k2', 'e3', 'e4'), 'metonic': ('l1', 'l2', 'm1', 'm2', 'n1'),
    'callippic': ('n2', 'p1', 'p2', 'o1'), 'saros': ('m3', 'f1', 'f2', 'g1'), 'exeligmos': ('g2', 'h1', 'h2', 'i1'),
}
SUBSYSTEM_KEYS = ('input', 'moon', 'anomaly', 'metonic', 'callippic', 'saros', 'exeligmos')
SUBSYSTEM_OF = {g: s for s, gs in SUBSYSTEMS.items() for g in gs}
#: palette des sous-ensembles (Anticythere3D : CIEDE2000 ≥ 20, daltonismes simulés), RVB 0–255
COLORS = {'input': (0xde, 0x69, 0x10), 'moon': (0x0d, 0x59, 0xc1), 'anomaly': (0x8e, 0x17, 0x00),
          'metonic': (0x1d, 0x95, 0x94), 'callippic': (0x78, 0x6f, 0x4c), 'saros': (0x84, 0x19, 0x59),
          'exeligmos': (0xb6, 0x6c, 0xcd)}
#: les 17 prises : entraxe m (N₁ + N₂) / 2
MESHES = (('a1', 'b1'), ('b2', 'c1'), ('c2', 'd1'), ('d2', 'e2'), ('e5', 'k1'), ('k2', 'e6'), ('e1', 'b3'),
          ('b2', 'l1'), ('l2', 'm1'), ('m2', 'n1'), ('n2', 'p1'), ('p2', 'o1'), ('m3', 'e3'), ('e4', 'f1'),
          ('f2', 'g1'), ('g2', 'h1'), ('h2', 'i1'))


def level_pitch(explode: float = 0.0) -> float:
    return LEVEL_PITCH + max(0.0, min(1.0, explode)) * EXPLODE_GAP


def level_z(level: int, explode: float = 0.0) -> float:
    return (N_LEVELS - level) * level_pitch(explode)


def front_shift(explode: float = 0.0) -> float:
    return level_z(1, explode) - level_z(1, 0.0)


def orbit(x: float, y: float, carrier_turns: float):
    ex, ey = ARBORS['e']
    a = 2.0 * math.pi * carrier_turns
    dx, dy = x - ex, y - ey
    c, s = math.cos(a), math.sin(a)
    return ex + c * dx - s * dy, ey + s * dx + c * dy


def gear_placement(name: str, explode: float = 0.0, carrier_turns: float = 0.0):
    x, y = ARBORS[ARBOR_OF[name]]
    z = level_z(LEVELS[name], explode)
    if ARBOR_OF[name] in ('k', 'K'):
        x, y = orbit(x, y, carrier_turns)
    return x, y, z


def arbor_position(arbor: str, carrier_turns: float = 0.0):
    x, y = ARBORS[arbor]
    return orbit(x, y, carrier_turns) if arbor in CARRIED_BY else (x, y)


def arbor_stub(explode: float = 0.0) -> float:
    return 0.6 + 0.4 * max(0.0, min(1.0, explode)) * EXPLODE_GAP


def arbor_extent(arbor: str, explode: float = 0.0):
    zs = [level_z(LEVELS[g], explode) for g, a in ARBOR_OF.items() if a == arbor]
    stub = arbor_stub(explode)
    return min(zs) - stub, max(zs) + GEAR_THICKNESS + stub


BACK_DIAL_ARBORS = ('n', 'g', 'o', 'i')
FRONT_DIAL_ARBORS = ('b',)


def arbor_span(arbor: str, explode: float = 0.0):
    z0, z1 = arbor_extent(arbor, explode)
    if arbor in MOUNTED_ON:
        zc = level_z(LEVELS[MOUNTED_ON[arbor]], explode)
        z0, z1 = min(z0, zc), max(z1, zc + GEAR_THICKNESS)
    if arbor in BACK_DIAL_ARBORS:
        z0 = level_z(N_LEVELS) - 8.0 - 12.0
    if arbor in FRONT_DIAL_ARBORS:
        z1 = level_z(1, explode) + 8.0 + 9.0
    return z0, z1


METONIC_RADIUS = 50.0
SAROS_RADIUS = 46.25


def mechanism_extent(margin: float = 14.0):
    xs, ys = [], []
    for g in LEVELS:
        x, y = ARBORS[ARBOR_OF[g]]
        r = MODULE * (TEETH[g] / 2.0 + 1.0)
        xs += [x - r, x + r]
        ys += [y - r, y + r]
    ax, ay = ARBORS['a']
    xs += [ax + 30.0]
    ys += [ay - 20.0, ay + 20.0]
    for arbor, rad in (('n', METONIC_RADIUS), ('g', SAROS_RADIUS)):
        x, y = ARBORS[arbor]
        xs += [x - rad, x + rad]
        ys += [y - rad, y + rad]
    return min(xs) - margin, max(xs) + margin, min(ys) - margin, max(ys) + margin


_X0, _X1, _Y0, _Y1 = mechanism_extent()
CASE_WIDTH = _X1 - _X0
CASE_HEIGHT = _Y1 - _Y0
CASE_CX = (_X0 + _X1) / 2.0
CASE_CY = (_Y0 + _Y1) / 2.0

CRANK_SHAFT = 34.0
CRANK_ARM = 26.0
CRANK_HANDLE = 20.0
CRANK_RADIUS = CRANK_ARM - 4.0
#: tours de manivelle (roue a1) par tour de b1 = 223/48, de sens contraire
CRANK_PER_TURN = -223.0 / 48.0

FRONT_DIAL_SPAN = 244.0
SUN_HAND = FRONT_DIAL_SPAN / 2.0 * 0.825 - 3.0
MOON_HAND = FRONT_DIAL_SPAN / 2.0 * (0.63 + 0.825) / 2.0
BACK_DIAL_SPAN = max(CASE_WIDTH, CASE_HEIGHT) + 12.0
CALLIPPIC_RADIUS = 9.9
EXELIGMOS_RADIUS = 9.2
GAMES_RADIUS = 13.0
GAMES_CENTER = (-70.0, 0.0)
COSMOS_RINGS = (('moon', 26.0, (191, 199, 214)), ('mercury', 34.0, (140, 122, 107)), ('venus', 42.0, (230, 212, 158)),
                ('sun', 50.0, (255, 204, 64)), ('mars', 58.0, (199, 82, 51)), ('jupiter', 65.0, (217, 194, 158)),
                ('saturn', 72.0, (184, 158, 97)))
METONIC_CENTER = ARBORS['n']
SAROS_CENTER = ARBORS['g']
Z_FRONT = level_z(1) + 16.0
Z_BACK = level_z(N_LEVELS) - 18.0

# ==================================================================== inscriptions (dialface.py)
ZODIAC_GREEK = (('ΚΡΙΟΣ', 'Bélier', 'Aries'), ('ΤΑΥΡΟΣ', 'Taureau', 'Taurus'), ('ΔΙΔΥΜΟΙ', 'Gémeaux', 'Gemini'),
                ('ΚΑΡΚΙΝΟΣ', 'Cancer', 'Cancer'), ('ΛΕΩΝ', 'Lion', 'Leo'), ('ΠΑΡΘΕΝΟΣ', 'Vierge', 'Virgo'),
                ('ΧΗΛΑΙ', 'Balance', 'Libra'), ('ΣΚΟΡΠΙΟΣ', 'Scorpion', 'Scorpio'),
                ('ΤΟΞΟΤΗΣ', 'Sagittaire', 'Sagittarius'), ('ΑΙΓΟΚΕΡΩΣ', 'Capricorne', 'Capricorn'),
                ('ΥΔΡΟΧΟΟΣ', 'Verseau', 'Aquarius'), ('ΙΧΘΥΕΣ', 'Poissons', 'Pisces'))
EGYPTIAN_GREEK = ('ΘΩΘ', 'ΦΑΩΦΙ', 'ΑΘΥΡ', 'ΧΟΙΑΚ', 'ΤΥΒΙ', 'ΜΕΧΕΙΡ', 'ΦΑΜΕΝΩΘ', 'ΦΑΡΜΟΥΘΙ', 'ΠΑΧΩΝ', 'ΠΑΥΝΙ', 'ΕΠΙΦΙ',
                  'ΜΕΣΟΡΗ')
EGYPTIAN_MONTHS = ('Thoth', 'Phaophi', 'Athyr', 'Choiak', 'Tybi', 'Mechir', 'Phamenoth', 'Pharmouthi', 'Pachon',
                   'Payni', 'Epiphi', 'Mesore')
PARAPEGMA_LETTERS = 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'
GAMES_GREEK = ('ΙΣΘΜΙΑ', 'ΟΛΥΜΠΙΑ', 'ΝΕΜΕΑ', 'ΠΥΘΙΑ')
CORINTHIAN_MONTHS = (('ΦΟΙΝΙΚΑΙΟΣ', 'ΦΟΙΝ'), ('ΚΡΑΝΕΙΟΣ', 'ΚΡΑΝ'), ('ΛΑΝΟΤΡΟΠΙΟΣ', 'ΛΑΝΟ'), ('ΜΑΧΑΝΕΥΣ', 'ΜΑΧΑ'),
                     ('ΔΩΔΕΚΑΤΕΥΣ', 'ΔΩΔΕ'), ('ΕΥΚΛΕΙΟΣ', 'ΕΥΚΛ'), ('ΑΡΤΕΜΙΣΙΟΣ', 'ΑΡΤΕ'), ('ΨΥΔΡΕΥΣ', 'ΨΥΔΡ'),
                     ('ΓΑΜΕΙΛΙΟΣ', 'ΓΑΜΕ'), ('ΑΓΡΙΑΝΙΟΣ', 'ΑΓΡΙ'), ('ΠΑΝΑΜΟΣ', 'ΠΑΝΑ'), ('ΑΠΕΛΛΑΙΟΣ', 'ΑΠΕΛ'))
GREEK_NUMERALS = ('Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ϛ', 'Ζ', 'Η', 'Θ', 'Ι', 'ΙΑ', 'ΙΒ', 'ΙΓ', 'ΙΔ', 'ΙΕ', 'ΙϚ', 'ΙΖ', 'ΙΗ', 'ΙΘ')
#: années de 13 mois du cycle métonique : (12k) mod 19 < 7 ; 235 = 19 × 12 + 7
EMBOLISMIC_YEARS = {2, 5, 8, 10, 13, 16, 19}
#: cases du Saros portant un glyphe : calculées (syzygie proche d'un nœud) sur 223 mois depuis janvier 2000
SAROS_SOLAR = {0, 1, 6, 7, 12, 18, 24, 30, 36, 42, 47, 48, 53, 54, 59, 65, 71, 77, 83, 88, 89, 95, 100, 106, 107, 112,
               118, 124, 129, 130, 136, 141, 147, 148, 153, 159, 165, 171, 177, 182, 183, 188, 189, 194, 200, 206,
               212, 218}
SAROS_LUNAR = {0, 6, 12, 18, 30, 35, 41, 47, 53, 59, 71, 76, 82, 88, 94, 100, 106, 112, 123, 129, 135, 141, 147, 153,
               159, 164, 176, 182, 188, 194, 200, 217}
EXELIGMOS_LABELS = ('0', 'Η', 'ΙϚ')


def metonic_year_starts() -> list:
    out, mois = [], 0
    for k in range(1, 20):
        out.append(mois)
        mois += 13 if k in EMBOLISMIC_YEARS else 12
    assert mois == 235, mois
    return out


def saros_glyph(k: int) -> str:
    s, lu = k in SAROS_SOLAR, k in SAROS_LUNAR
    return 'ΗΣ' if s and lu else 'Η' if s else 'Σ' if lu else ''


# ==================================================================== astronomie de référence (astro.py)
J2000 = 2451545.0
_DEG = math.pi / 180.0


def julian_day(year: int, month: int, day: float, hour: float = 0.0) -> float:
    """Jour julien ; calendrier grégorien à partir du 15 octobre 1582, julien avant ; années astronomiques."""
    y, m = year, month
    d = day + hour / 24.0
    if m <= 2:
        y -= 1
        m += 12
    b = 0
    if (year, month, day) >= (1582, 10, 15):
        a = math.floor(y / 100)
        b = 2 - a + math.floor(a / 4)
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def from_julian_day(jd: float):
    """(année, mois, jour, heure décimale)."""
    z = math.floor(jd + 0.5)
    f = jd + 0.5 - z
    a = z
    if z >= 2299161:
        alpha = math.floor((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - math.floor(alpha / 4)
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)
    day = b - d - math.floor(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    di = math.floor(day)
    return int(year), int(month), int(di), (day - di) * 24.0


def centuries(jd: float) -> float:
    return (jd - J2000) / 36525.0


def sun_mean_longitude(jd: float) -> float:
    t = centuries(jd)
    return (280.46646 + 36000.76983 * t + 0.0003032 * t * t) % 360.0


def sun_mean_anomaly(jd: float) -> float:
    t = centuries(jd)
    return (357.52911 + 35999.05029 * t - 0.0001537 * t * t) % 360.0


def sun_longitude(jd: float) -> float:
    t = centuries(jd)
    m = sun_mean_anomaly(jd) * _DEG
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m) + (0.019993 - 0.000101 * t) * math.sin(2 * m)
         + 0.000289 * math.sin(3 * m))
    return (sun_mean_longitude(jd) + c) % 360.0


def moon_arguments(jd: float) -> dict:
    t = centuries(jd)
    return dict(Lp=(218.3164477 + 481267.88123421 * t - 0.0015786 * t * t) % 360.0,
                D=(297.8501921 + 445267.1114034 * t - 0.0018819 * t * t) % 360.0,
                M=(357.5291092 + 35999.0502909 * t - 0.0001536 * t * t) % 360.0,
                Mp=(134.9633964 + 477198.8675055 * t + 0.0087414 * t * t) % 360.0,
                F=(93.272095 + 483202.0175233 * t - 0.0036539 * t * t) % 360.0,
                Omega=(125.0445479 - 1934.1362891 * t + 0.0020754 * t * t) % 360.0)


_MOON_TERMS = ((6.288774, 0, 0, 1, 0), (1.274027, 2, 0, -1, 0), (0.658314, 2, 0, 0, 0), (0.213618, 0, 0, 2, 0),
               (-0.185116, 0, 1, 0, 0), (-0.114332, 0, 0, 0, 2), (0.058793, 2, 0, -2, 0), (0.057066, 2, -1, -1, 0),
               (0.053322, 2, 0, 1, 0), (0.045758, 2, -1, 0, 0), (-0.040923, 0, 1, -1, 0), (-0.03472, 1, 0, 0, 0),
               (-0.030383, 0, 1, 1, 0), (0.015327, 2, 0, 0, -2), (-0.012528, 0, 0, 1, 2), (0.01098, 0, 0, 1, -2))


def moon_longitude(jd: float) -> float:
    a = moon_arguments(jd)
    total = 0.0
    for coef, cd, cm, cmp_, cf in _MOON_TERMS:
        total += coef * math.sin((cd * a['D'] + cm * a['M'] + cmp_ * a['Mp'] + cf * a['F']) * _DEG)
    return (a['Lp'] + total) % 360.0


def elongation(jd: float) -> float:
    return (moon_longitude(jd) - sun_longitude(jd)) % 360.0


SOLAR_LIMIT, SOLAR_CENTRAL, LUNAR_LIMIT, LUNAR_CENTRAL = 18.5, 15.4, 12.2, 9.5


def eclipse_possible(jd: float) -> dict:
    """Critère que la machine mécanise : syzygie proche d'un nœud (Meeus ch. 54)."""
    e = elongation(jd)
    f = moon_arguments(jd)['F'] % 180.0
    dist = min(f, 180.0 - f)
    if min(e, 360.0 - e) < 12.0 and dist < SOLAR_LIMIT:
        return dict(type='solar', certain=dist < SOLAR_CENTRAL, arg=dist)
    if abs(e - 180.0) < 12.0 and dist < LUNAR_LIMIT:
        return dict(type='lunar', certain=dist < LUNAR_CENTRAL, arg=dist)
    return dict(type=None, certain=False, arg=dist)


def calibrate_planets(jd: float) -> dict:
    t = centuries(jd)
    mean = {'mercury': 252.250906 + 149472.6746358 * t, 'venus': 181.979801 + 58517.815676 * t,
            'mars': 355.433 + 19141.6964471 * t, 'jupiter': 34.351519 + 3036.3027748 * t,
            'saturn': 50.077444 + 1223.5110686 * t}
    return {k: (v % 360.0) / 360.0 for k, v in mean.items()}


def calibration_offsets(jd: float) -> dict:
    """Décalages qui calent la machine sur le ciel à la date jd (Soleil MOYEN, Lune MOYENNE, anomalie, nœud)."""
    a = moon_arguments(jd)
    return dict(mean_sun=sun_mean_longitude(jd) / 360.0, moon=a['Lp'] / 360.0, anomaly=a['Mp'] / 360.0,
                nodes=a['Omega'] / 360.0, metonic=0.0, saros=0.0, planets=calibrate_planets(jd))


def geocentric_longitude(name: str, helio_turns: float, mean_sun_turns: float) -> float:
    """Longitude géocentrique (degrés) d'après le modèle à épicycle du Cosmos (Freeth et al. 2021) : planète sur
    son cercle (période tirée de la relation de période), Terre sur le sien (Soleil moyen + 180°)."""
    a = PLANETS[name]['a']
    lp, le = 2 * math.pi * helio_turns, 2 * math.pi * (mean_sun_turns + 0.5)
    return math.degrees(math.atan2(a * math.sin(lp) - math.sin(le), a * math.cos(lp) - math.cos(le))) % 360.0


#: ère de Nabonassar : 1er Thoth de l'an 1 = 26 février −746 (julien), JD 1448638 ; année vague de 365 jours
NABONASSAR_JD = 1448638


def egyptian_day(jd: float) -> int:
    return int(math.floor(jd + 0.5 - NABONASSAR_JD) % 365)


def egyptian_date(jd: float):
    """(mois 0–11, ou 12 pour les jours épagomènes ; jour 1–30)."""
    n = egyptian_day(jd)
    return (n // 30, n % 30 + 1) if n < 360 else (12, n - 360 + 1)


def machine_calee() -> Mechanism:
    """Machine calée sur le ciel à J2000, comme Anticythere3D."""
    return Mechanism(offsets=calibration_offsets(J2000))


def zodiac_sign(longitude_deg: float):
    lon = longitude_deg % 360.0
    i = int(lon // 30.0)
    return i, lon - 30.0 * i


def phase_index(elongation_turns: float) -> int:
    return int((elongation_turns % 1.0) * 8.0 + 0.5) % 8
