# « Démonstrateur du temps sidéral et de l'angle horaire », encadré « Dans l'hémisphère Sud » (0.8.0) :
# vérification SageMath (RealField(120), indépendante du code) des affirmations de l'encadré.
#   sage outils/verif_anim/temps_sideral_sud_verif.sage > tests/temps_sideral_sud_sage.json
# * hauteur : sin h = sin φ sin δ + cos φ cos δ cos H ; H = TSL − α compté vers l'ouest ; avant la culmination
#   (H < 0) la hauteur croît, après (H > 0) elle décroît, dans les deux hémisphères ;
# * culmination supérieure à h = 90° − |φ − δ|, côté NORD si δ > φ (cas de la plupart des astres vus du Sud) ;
# * circumpolaire (jamais couchée) si la hauteur minimale (H = 12 h) est positive : δ < −(90° − |φ|) pour φ < 0 ;
# * face au nord, l'est est à DROITE et l'ouest à GAUCHE : un astre qui culmine au nord se lève à droite (azimut
#   entre 0° et 180°, H < 0) et se couche à gauche (azimut entre 180° et 360°, H > 0) : il défile de droite à gauche.
# * σ Octantis : distance au pôle Sud céleste (J2000, SIMBAD : δ = −88,956 499 5°), magnitude V 5,42.
import json
R = RealField(120)
D = R(pi) / 180


def hauteur(phi, dec, H_heures):
    phi, dec, H = R(phi) * D, R(dec) * D, R(H_heures) * 15 * D
    return asin(sin(phi) * sin(dec) + cos(phi) * cos(dec) * cos(H)) / D


def azimut(phi, dec, H_heures):
    """Azimut compté du nord vers l'est."""
    phi, dec, H = R(phi) * D, R(dec) * D, R(H_heures) * 15 * D
    x = -cos(dec) * sin(H)                                   # composante est
    y = cos(phi) * sin(dec) - sin(phi) * cos(dec) * cos(H)  # composante nord
    a = R(atan2(R(x), R(y))) / D
    return a + 360 if a < 0 else a


out = {'outil': 'SageMath, RealField(120)', 'cas': []}
for phi in (-12.5, -23.44, -33.87, -45.0, -70.0):
    for dec in (-80.0, -60.0, -50.0, -30.0, -10.0, 0.0, 20.0, 45.0):
        hmin = min(hauteur(phi, dec, R(h) / 10) for h in range(-120, 121))
        hmax = max(hauteur(phi, dec, R(h) / 10) for h in range(-120, 121))
        montee = hauteur(phi, dec, R('-1.0')) > hauteur(phi, dec, R('-1.1'))      # avant la culmination : monte
        descente = hauteur(phi, dec, R('1.1')) < hauteur(phi, dec, R('1.0'))
        az_culm = azimut(phi, dec, R(0))
        out['cas'].append({'lat': phi, 'dec': dec, 'h_min': float(hmin), 'h_max': float(hmax),
                           'h_culmination': float(90 - abs(R(phi) - R(dec))),
                           'circumpolaire': bool(hmin > 0), 'formule_circumpolaire': bool(R(dec) < -(90 - abs(R(phi)))),
                           'culmine_au_nord': bool(abs(az_culm) < 1e-9 or abs(az_culm - 360) < 1e-9),
                           'formule_nord': bool(R(dec) > R(phi)), 'monte_avant': bool(montee),
                           'descend_apres': bool(descente),
                           'az_lever_puis_coucher': [float(azimut(phi, dec, R(-5))), float(azimut(phi, dec, R(5)))]})
        c = out['cas'][-1]
        assert c['circumpolaire'] == c['formule_circumpolaire'] and c['monte_avant'] and c['descend_apres']
        if abs(R(dec) - R(phi)) > 1e-9:
            assert c['culmine_au_nord'] == c['formule_nord']
        assert abs(R(c['h_max']) - R(c['h_culmination'])) < 1e-6
        if c['formule_nord'] and abs(R(dec) - R(phi)) > 1e-9:
            e, o = c['az_lever_puis_coucher']
            assert 0 < e < 180 and 180 < o < 360           # à droite (est) avant, à gauche (ouest) après
sigma_oct = R('-88.95649953627')
out['sigma_oct'] = {'dec': float(sigma_oct), 'distance_pole_deg': float(90 + sigma_oct), 'V': 5.42}
print(json.dumps(out, indent=1, default=float))
