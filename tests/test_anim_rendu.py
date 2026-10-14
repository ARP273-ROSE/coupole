"""Module « Animations » (0.4.1) : rendu des astres, étiquettes sans chevauchement, formules mises en forme, sens du
glisser, côtes Natural Earth, éclipses rejouées, aide propre à chaque animation, ordre des thèmes, lien vers la
version web.  Mêmes règles et mêmes cas que Coupole Web (tests/unit/*.test.ts)."""
import gzip
import json
import math
import time
from pathlib import Path

import pytest

from coupole.modules.anim import catalogue

TAILLES = ((420, 560), (720, 470), (1280, 800), (2560, 1440))


@pytest.fixture(scope='module')
def appli():
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _recouvrement(a, b) -> float:
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


@pytest.mark.parametrize('ident', [e.id for e in catalogue.ENTREES])
def test_etiquettes_sans_chevauchement(appli, ident):
    """Pour chaque animation, quatre formats et trois instants : aucune étiquette à cartouche n'en recouvre une autre
    (plus de 15 % de la plus petite) ni ne sort de la toile."""
    from coupole.modules.anim import dessin
    a = catalogue.PAR_ID[ident].charger()()
    a.resize(1000, 700)
    for k in range(3):
        if k:
            a.pas(0.73)
        for w, h in TAILLES:
            a.image(w, h)
            b = dessin.etiquettes_posees()
            for i in range(len(b)):
                assert b[i][0] >= -1 and b[i][1] >= -1 and b[i][0] + b[i][2] <= w + 1 and b[i][1] + b[i][3] <= h + 1, \
                    (ident, w, h, 'hors de la toile', b[i])
                for j in range(i):
                    lim = 0.15 * min(b[i][2] * b[i][3], b[j][2] * b[j][3])
                    assert _recouvrement(b[i], b[j]) <= lim, (ident, w, h, b[i], b[j])
    a.close()


def test_placeur_ecarte_et_relie(appli):
    """Deux étiquettes voulues au même endroit : la seconde est déplacée autour du point d'accroche."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QImage, QPainter
    from coupole.modules.anim import dessin
    img = QImage(400, 300, QImage.Format.Format_ARGB32)
    p = QPainter(img)
    dessin.debut_image(p, QRectF(0, 0, 400, 300))
    dessin.disque(p, 200, 150, 10, 'terre')
    for s in ('lanceur', 'centre de masse', 'étoile'):
        dessin.texte(p, 200, 150, s, fond=True)
    p.end()
    b = dessin.etiquettes_posees()
    assert len(b) == 3
    for i in range(3):
        for j in range(i):
            assert _recouvrement(b[i], b[j]) == 0


@pytest.mark.parametrize('az,alt', [(0, 0), (215, 30), (100, -40)])
def test_glisser_suit_la_souris(az, alt):
    """Glisser vers la droite fait partir la face visible vers la droite, vers le bas la fait descendre, à la vitesse
    de la souris (un radian par rayon de sphère) : le globe ne tourne plus à l'envers."""
    from coupole.modules.anim.dessin import Vue3D
    import numpy as np
    v = Vue3D(az, alt)
    v.rayon_px = 150
    d = v.d.copy()
    x0, y0, _ = v.projeter(d)
    v.tourner(10, 0)
    x1, _, _ = v.projeter(d)
    assert 9 < (x1[0] - x0[0]) * 150 < 11
    v2 = Vue3D(az, alt)
    v2.rayon_px = 150
    e = v2.d.copy()
    v2.tourner(0, 10)
    _, y2, _ = v2.projeter(e)
    assert (y2[0] - y0[0]) * 150 < -9                  # y écran vers le haut dans la projection : le point descend
    assert np.isfinite(v2.az)


def test_longitude_latitude_le_globe_suit_la_souris(appli):
    """Le démonstrateur longitude/latitude : un glisser vers la droite amène vers l'avant les longitudes de l'ouest."""
    from PyQt6.QtCore import QPointF, Qt
    from coupole.modules.anim.animations.longitude_latitude import globe_xyz
    a = catalogue.PAR_ID['longlat'].charger()()
    a.image(800, 600)
    vue = a.globe
    centre_avant = vue.d.copy()
    a.presser(QPointF(400, 470), Qt.MouseButton.LeftButton)
    a.glisser(QPointF(440, 470), 40, 0)
    a.relacher(QPointF(440, 470))
    # le point de la surface qui était au centre est passé à droite
    x, _, z = vue.projeter(centre_avant)
    assert x[0] > 0.1 and z[0] > 0
    assert globe_xyz(0, 0).shape == (3,)
    a.close()


# ------------------------------------------------------------------ formules
def _ecrire(n) -> str:
    k = n[0]
    if k == 'rangee':
        return ' '.join(_ecrire(x) for x in n[1])
    if k in ('id', 'nb', 'op'):
        return n[1]
    if k == 'frac':
        return '(%s)/(%s)' % (_ecrire(n[1]), _ecrire(n[2]))
    if k == 'sup':
        return '%s^%s' % (_ecrire(n[1]), _ecrire(n[2]))
    if k == 'sub':
        return '%s_%s' % (_ecrire(n[1]), _ecrire(n[2]))
    if k == 'subsup':
        return '%s_%s^%s' % (_ecrire(n[1]), _ecrire(n[2]), _ecrire(n[3]))
    if k == 'racine':
        return '√[%s]' % _ecrire(n[1])
    return '%s%s%s' % (n[2], _ecrire(n[1]), n[3])


@pytest.mark.parametrize('s,attendu', [
    ('F = G M₁ M₂ / R²', 'F = (G M_1 M_2)/(R^2)'),
    ('b = √(a² − c²)', 'b = √[a^2 − c^2]'),
    ('f₀ / (1 − v_r / c)', '(f_0)/(1 − (v_r)/(c))'),
    ('H = (da/dt) / a', 'H = ((d a)/(d t))/(a)'),
    ('(R_p / R_*)²', '((R_p)/(R_∗))^2'),
    ('m − M = 5 log₁₀ d − 5', 'm − M = 5 log_10 d − 5'),
    ('P² = a³ / M', 'P^2 = (a^3)/(M)'),
    ('206 265″ × d / D', '(206 265″ × d)/(D)'),
    ('R / R☉ = √(L / L☉) / (T / T☉)²', '(R)/(R_☉) = (√[(L)/(L_☉)])/(((T)/(T_☉))^2)'),
    ('1/S = 1/E − 1/P', '(1)/(S) = (1)/(E) − (1)/(P)'),
    ('∝ 1 / sin h', '∝ (1)/(sin h)'),
    ('F × (1/3 × 1/2) / (3)² = F × 1/18', '(F × ((1)/(3) × (1)/(2)))/((3)^2) = F × (1)/(18)'),
    ('σT⁴/π', '(σ T^4)/(π)'),
    ('v ∝ 1/√R', 'v ∝ (1)/(√[R])'),
    ('= (6,67 × 10⁻¹¹) (5,97 × 10²⁴) / (6,37 × 10⁶)²',
     '= ((6,67 × 10^−11) (5,97 × 10^24))/((6,37 × 10^6)^2)'),
])
def test_analyse_des_formules(s, attendu):
    """Mêmes arbres que Coupole Web (tests/unit/formule.test.ts)."""
    from coupole.modules.anim import formule
    assert _ecrire(formule.analyser(s)) == attendu


def test_police_mathematique_embarquee(appli):
    """STIX Two Math (sous-ensemble OTF, licence OFL livrée) : chargée, avec les vraies lettres italiques."""
    from PyQt6.QtGui import QFontMetricsF
    from coupole.modules.anim import formule
    assert formule.POLICE_FICHIER.exists() and formule.POLICE_FICHIER.stat().st_size < 200_000
    assert formule.famille() == 'STIX Two Math'
    fm = QFontMetricsF(formule._police(20))
    for c in 'FGMRhαδφλσ':
        assert fm.inFontUcs4(ord(formule.italique(c))), c
    assert (Path(__file__).resolve().parents[1] / 'LICENCES' / 'OFL-STIX-Two.txt').exists()


def test_mise_en_page_fraction_et_puissance(appli):
    """Une fraction est empilée (plus haute qu'une ligne), un exposant est surélevé, le cache sert."""
    from coupole.modules.anim import formule
    w1, a1, d1, _ = formule.mise_en_page('F = G M₁ M₂', 16.0)
    w2, a2, d2, prims = formule.mise_en_page('F = G M₁ M₂ / R²', 16.0)
    assert a2 + d2 > 1.8 * (a1 + d1)
    assert any(q[0] == 'l' for q in prims)                     # trait de fraction
    assert formule.mise_en_page('F = G M₁ M₂ / R²', 16.0) is formule.mise_en_page('F = G M₁ M₂ / R²', 16.0)
    t0 = time.perf_counter()
    for _ in range(200):
        formule.mise_en_page('F = G M₁ M₂ / R²', 16.0)
    assert time.perf_counter() - t0 < 0.05


def test_formules_des_textes(appli):
    """Les formules des descriptions sont reconnues et mises en forme ; un résultat avec unité ne l'est pas ;
    × 10ⁿ devient un vrai exposant."""
    from coupole.modules.anim import formule
    h = formule.enrichir('La loi F = G M₁ M₂ / R² relie…')
    assert 'data:image/png;base64' in h and 'relie' in h
    assert formule.est_formule('1/S = 1/E − 1/P')
    assert not formule.est_formule('33 al')
    assert not formule.est_formule('10,0 pc')
    assert '10<sup>−11</sup>' in formule.enrichir('6,67 × 10⁻¹¹ m³/kg/s²')


def test_formules_dessinees_sur_la_toile(appli):
    """Le calculateur de Newton dessine sa formule mise en forme (fraction), plus haute qu'une ligne de texte."""
    a = catalogue.PAR_ID['gravcalc'].charger()()
    img = a.image(900, 600)
    assert not img.isNull()
    a.close()


# ------------------------------------------------------------------ astres
def test_astres_en_spheres(appli):
    """Le Soleil a un halo (des pixels clairs au-delà de son rayon) ; une Terre éclairée par un Soleil à gauche a
    son côté jour (gauche) plus clair que son côté nuit (droite)."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QColor, QImage, QPainter
    from coupole.modules.anim import dessin
    img = QImage(400, 200, QImage.Format.Format_ARGB32)
    img.fill(dessin.c('fond'))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    dessin.debut_image(p, QRectF(0, 0, 400, 200))
    dessin.disque(p, 60, 100, 30, 'soleil')
    dessin.disque(p, 300, 100, 40, 'terre')
    p.end()
    fond = QColor(dessin.c('fond')).lightness()
    assert QColor(img.pixel(60 + 36, 100)).lightness() > fond + 3          # halo
    jour = QColor(img.pixel(300 - 25, 100)).lightness()
    nuit = QColor(img.pixel(300 + 25, 100)).lightness()
    assert jour > nuit + 25


# ------------------------------------------------------------------ cartes
def test_cotes_natural_earth():
    """Côtes Natural Earth 1:50m simplifiées (domaine public) : assez de points pour un trait fin, mais léger."""
    f = Path(catalogue.__file__).resolve().parent / 'donnees' / 'cotes.json.gz'
    assert f.stat().st_size < 100_000
    doc = json.loads(gzip.decompress(f.read_bytes()))
    assert 'Natural Earth' in doc['source']
    n = sum(len(q) for q in doc['polygones'])
    assert 10_000 < n < 20_000 and len(doc['polygones']) > 200
    for q in doc['polygones']:
        for lon, lat in q:
            assert -180 <= lon <= 180 and -90 <= lat <= 90


def test_terminateur_exact_du_simulateur_jour_nuit():
    """Le Soleil est à 0° de hauteur le long du terminateur tracé (géométrie exacte, toutes saisons)."""
    from coupole.modules.anim.animations import jour_nuit
    import numpy as np
    for jour in (0, 79, 172, 266, 355):
        dec, lon_ss = jour_nuit.subsolaire(jour + 0.5)
        if abs(dec) < 0.05:
            continue
        lons = np.linspace(-180, 180, 73)
        lats = jour_nuit.latitude_terminateur(lons, dec, lon_ss)
        for lo, la in zip(lons, lats):
            h = math.degrees(math.asin(math.sin(math.radians(la)) * math.sin(math.radians(dec)) +
                                       math.cos(math.radians(la)) * math.cos(math.radians(dec)) *
                                       math.cos(math.radians(lo - lon_ss))))
            assert abs(h) < 1e-6


# ------------------------------------------------------------------ éclipses
def test_soleil_entier_dans_le_simulateur_d_ombres(appli):
    from coupole.modules.anim.animations import ombres
    assert ombres.MARGE_SOLEIL > 0
    a = catalogue.PAR_ID['shadowsim'].charger()()
    img = a.image(600, 420)
    from PyQt6.QtGui import QColor
    from coupole.modules.anim import dessin
    # le disque du Soleil (pas seulement son halo) tient entier dans la toile : au bord, on n'a que le halo pâle
    cy = int(round(img.height() * 0.72 / 2))
    centre = QColor(img.pixel(int(ombres.R_SOLEIL + ombres.MARGE_SOLEIL), cy)).lightness()
    bord = QColor(img.pixel(1, cy)).lightness()
    fond = QColor(dessin.c('fond')).lightness()
    assert centre > bord + 60 and bord < fond + 40
    a.close()


def test_eclipses_rejouees_compatibles_avec_la_table():
    """Chaque éclipse de la table 2015–2044 a une trajectoire compatible avec son type (mêmes bornes que le web)."""
    from coupole.modules.anim import astro
    from coupole.modules.anim.animations import ombres
    from coupole.modules.anim.donnees_eclipses import LUNE, SOLEIL
    RL, RT = astro.R_LUNE_KM, astro.R_TERRE_KM
    assert len(SOLEIL) + len(LUNE) == 133
    for i, e in enumerate(LUNE):
        r = ombres.rejeu('L%d' % i)
        y = abs(r['y_km'])
        if e[3] == 'total':
            assert y < r['ru_km'] - RL
        elif e[3] == 'partial':
            assert r['ru_km'] - RL < y < r['ru_km'] + RL
        else:
            assert r['ru_km'] + RL < y < r['rp_km'] + RL
    for i, e in enumerate(SOLEIL):
        r = ombres.rejeu('S%d' % i)
        y = abs(r['y_km'])
        if e[3] == 'partial':
            assert RT < y < RT + r['rp_km']
        else:
            assert y < RT


def test_mode_rejouer_dans_l_interface(appli):
    a = catalogue.PAR_ID['shadowsim'].charger()()
    assert a.rejouer.count() == 134
    assert not a.instant.isVisibleTo(a)
    a.rejouer.setCurrentIndex(a.rejouer.findData('S20'))              # 8 avril 2024, totale
    assert a.instant.isVisibleTo(a)
    a.instant.setValue(0.4)
    assert any('2024' in v for _, v in a.valeurs())
    assert not a.image(800, 600).isNull()
    a.close()


# ------------------------------------------------------------------ aide, thèmes, version web
def test_aide_propre_a_chaque_animation(appli):
    """Plus d'info-bulle générique sur la toile : une aide discrète sous la scène, propre à l'animation."""
    from coupole.modules.anim.base import Animation
    for e in catalogue.ENTREES:
        a = e.charger()()
        assert not a.toile.toolTip(), e.id
        assert not a.aide_interaction().startswith('anim_'), e.id
        if a.nb_vues or type(a).presser is not Animation.presser:
            assert a.aide_interaction(), e.id
        a.close()
    a = catalogue.PAR_ID['longlat'].charger()()
    assert 'point' in a.l_aide.text()
    a.close()


def test_ordre_pedagogique_des_themes():
    assert catalogue.THEMES == ('intro', 'coordsmotion', 'lunarcycles', 'ancientastro', 'renaissance', 'solar',
                                'solarsystemdebris', 'sunsolarenergy', 'light', 'telescopes', 'stellarprops',
                                'binaryvariablestars', 'extrasolarplanets', 'ismstarformation', 'milkyway', 'cosmology')
    assert {e.theme for e in catalogue.ENTREES} <= set(catalogue.THEMES)


def test_lien_version_web(appli):
    from coupole.modules.anim import gui
    p = gui.Panneau()
    assert p.adresse_web() == gui.ADRESSE_WEB or p.adresse_web().startswith(gui.ADRESSE_WEB + '#/a/')
    w = p.ouvrir('longlat')
    w.lat.setValue(12.5)
    u = p.adresse_web()
    assert u.startswith('https://arp273-rose.github.io/coupole-web/#/a/longlat?') and 'latitude=12.5' in u
    w.reinitialiser()
    assert p.adresse_web() == gui.ADRESSE_WEB + '#/a/longlat'
    p.arreter()


# ------------------------------------------------------------------ performances
def test_rendu_rapide(appli):
    """Rendu médian de toutes les animations à 720 × 470 : quelques millisecondes (large marge pour la CI)."""
    import statistics
    temps = []
    for e in catalogue.ENTREES:
        a = e.charger()()
        a.image(720, 470)
        t0 = time.perf_counter()
        for _ in range(3):
            a.image(720, 470)
        temps.append((time.perf_counter() - t0) / 3)
        a.close()
    assert statistics.median(temps) < 0.025


# ------------------------------------------------------------------ simulateur jour-nuit : projections polaires
@pytest.mark.parametrize('nord', [True, False])
def test_projection_polaire_directe_et_inverse(nord):
    """Azimutale équidistante polaire : le pôle au centre, l'équateur au bord (rayon 1), aller-retour exact."""
    from coupole.modules.anim.animations import jour_nuit as jn
    u, v = jn.projeter_polaire(90.0 if nord else -90.0, 37.0, nord)
    assert abs(u) < 1e-12 and abs(v) < 1e-12
    for lat in (0.0, 12.5, 45.0, 66.56, 89.0):
        la = lat if nord else -lat
        for lon in (-179.0, -90.0, -12.3, 0.0, 45.0, 135.0):
            u, v = jn.projeter_polaire(la, lon, nord)
            assert abs(math.hypot(u, v) - (90.0 - lat) / 90.0) < 1e-12           # distances au pôle vraies
            la2, lo2 = jn.inverse_polaire(float(u), float(v), nord)
            assert abs(la2 - la) < 1e-9 and abs(((lo2 - lon + 180) % 360) - 180) < 1e-9
    # vu du pôle Nord, l'est est dans le sens inverse des aiguilles d'une montre (méridien 0 en bas, 90° E à droite)
    u, v = jn.projeter_polaire(0.0, 90.0, True)
    assert u > 0.99 and abs(v) < 1e-9


def test_terminateur_polaire_tangent_au_cercle_polaire(appli):
    """Au solstice de juin, la nuit touche le cercle arctique (méridien opposé au Soleil) et le cercle antarctique
    (méridien du Soleil) ; le pôle est toujours bien classé (jour ou nuit polaire), sans artefact."""
    from PyQt6.QtCore import QPointF
    from coupole.modules.anim.animations import jour_nuit as jn
    dec, lon_ss = jn.subsolaire(jn.astro.jour_julien(2026, 6, 21) - jn.astro.jour_julien(2026, 1, 1) + 0.35)
    assert dec > 23.43
    eps = 90.0 - dec

    def nuit(lat, lon, nord, decalage=0.0):
        u, v = jn.projeter_polaire(lat, lon, nord)
        return jn.chemin_nuit_polaire(dec, lon_ss, decalage, nord).contains(QPointF(float(u), float(v)))

    anti = lon_ss + 180.0
    assert nuit(eps - 0.2, anti, True) and not nuit(eps + 0.2, anti, True)
    assert not nuit(-eps + 0.2, lon_ss, False) and nuit(-eps - 0.2, lon_ss, False)
    for jour in range(0, 365, 7):
        d, lo = jn.subsolaire(jour + 0.5)
        for nord in (True, False):
            u, v = jn.projeter_polaire(90.0 if nord else -90.0, 0.0, nord)
            h_pole = d if nord else -d
            if abs(h_pole) > 0.05:
                assert jn.chemin_nuit_polaire(d, lo, 0.0, nord).contains(QPointF(float(u), float(v))) == (h_pole < 0)


def test_simulateur_jour_nuit_en_projection_polaire(appli):
    from PyQt6.QtCore import QPointF, Qt
    from coupole.modules.anim.animations import jour_nuit as jn
    a = catalogue.PAR_ID['daylightsimulator'].charger()()
    for proj in ('nord', 'sud'):
        a.projection.setCurrentIndex(a.projection.findData(proj))
        a.c_crepuscule.setChecked(True)
        for bord in (0, 30):
            a.bord.setCurrentIndex(a.bord.findData(bord))
            for tournant in (True, False):
                a.c_tournant.setChecked(tournant)
                assert not a.image(800, 600).isNull()
                # glisser sur la carte : le point suit la souris (inverse de la projection)
                cx, cy, rr = a._disque
                q = QPointF(cx + rr / 2, cy)
                a.presser(q, Qt.MouseButton.LeftButton)
                a.relacher(q)
                _, lon_ss = jn.subsolaire(a._jour())
                lo_attendu = 90.0 + (0.0 if tournant else lon_ss)
                lat_attendue = (90.0 - 0.5 * (90.0 + bord)) * (1 if proj == 'nord' else -1)
                assert abs(a.lat.value() - lat_attendue) < 0.2
                assert abs(((a.lon.value() - lo_attendu + 180) % 360) - 180) < 0.2
    a.close()


def test_globe_nuit_exacte(appli):
    """Globe 3D : la région de nuit dessinée (orthographique, bornée par le limbe) contient exactement les points
    visibles où le Soleil est sous l'horizon (ou sous −6°, −12°, −18°)."""
    import numpy as np
    from PyQt6.QtCore import QPointF
    from coupole.modules.anim.animations import jour_nuit as jn
    rng = np.random.default_rng(1)
    for _ in range(12):
        s = rng.normal(size=3)
        s /= np.linalg.norm(s)
        for decalage in (0.0, 6.0, 18.0):
            polys = jn.nuit_orthographique(s, decalage)
            ch = jn._chemin_ecran(polys, 0.0, 0.0, 1.0) if polys else None
            c = -math.sin(math.radians(decalage))
            for _ in range(200):
                x, y = rng.uniform(-1, 1, 2)
                if x * x + y * y > 0.97:
                    continue
                q = np.array([x, y, math.sqrt(1 - x * x - y * y)])
                marge = abs(q @ s - c)
                if marge < 0.02:
                    continue
                dedans = bool(ch is not None and ch.contains(QPointF(x, -y)))
                assert dedans == (q @ s < c), (s, decalage, x, y)


def test_globe_souris(appli):
    """Globe 3D : glisser vers la droite amène vers la droite le point saisi ; double-clic : face au point
    subsolaire ; clic droit : l'observateur ; molette : zoom borné."""
    import numpy as np
    from PyQt6.QtCore import QPointF, Qt
    from coupole.modules.anim.animations import jour_nuit as jn
    a = catalogue.PAR_ID['daylightsimulator'].charger()()
    a.projection.setCurrentIndex(a.projection.findData('globe'))
    a.c_tournant.setChecked(True)
    a.image(800, 600)
    cx, cy, rr = a._disque
    centre = a.globe[2].copy()                         # point de la Terre au centre de l'image
    a.presser(QPointF(cx, cy), Qt.MouseButton.LeftButton)
    a.glisser(QPointF(cx + 30, cy), 30, 0)
    a._t_glisse = 0.0                                   # pas d'inertie pour la mesure
    a.relacher(QPointF(cx + 30, cy))
    v = a.globe @ centre
    assert abs(v[0] * rr - 30) < 1.5 and abs(v[1]) < 1e-6
    a.tourner_globe(0, 25, rr)
    assert (a.globe @ centre)[1] * rr < -20             # vers le bas
    assert np.allclose(a.globe @ a.globe.T, np.eye(3), atol=1e-9)
    a.double_clic(QPointF(cx, cy))
    dec, lon = jn.subsolaire(a._jour())
    assert np.allclose(a.vue_globe(lon) @ jn.globe_xyz(dec, lon), [0, 0, 1], atol=1e-9)
    assert a.globe[1][2] > 0                            # le nord en haut
    a.presser(QPointF(cx, cy), Qt.MouseButton.RightButton)
    assert abs(a.lat.value() - dec) < 0.1 and abs(((a.lon.value() - lon + 180) % 360) - 180) < 0.1
    a.c_tournant.setChecked(False)                      # Soleil fixe dans la vue : la Terre tourne dessous
    a.recentrer()
    a.heure.setValue((a.heure.value() + 3) % 24)
    dec2, lon2 = jn.subsolaire(a._jour())
    assert abs(lon2 - lon) > 40                         # trois heures plus tard…
    assert np.allclose(a.vue_globe(lon2) @ jn.globe_xyz(dec2, lon2), a.vue_globe(lon) @ jn.globe_xyz(dec, lon),
                       atol=0.01)                       # … le point subsolaire est toujours au même endroit de la vue
    for _ in range(50):
        a.molette(QPointF(cx, cy), 120)
    assert a._zoom == 4.0
    assert not a.image(800, 600).isNull()
    a.close()


def test_globe_troncons_coupes_au_limbe():
    """Une ligne qui passe derrière le globe est coupée exactement sur le limbe."""
    import numpy as np
    from coupole.modules.anim.animations import jour_nuit as jn
    t = np.linspace(0, 2 * math.pi, 37)
    v = np.stack([np.cos(t), np.zeros_like(t), np.sin(t)], axis=1)        # grand cercle, moitié derrière
    tr_ = jn.troncons(v)
    assert len(tr_) == 1
    for bout in (tr_[0][0], tr_[0][-1]):
        assert abs(math.hypot(*bout) - 1) < 1e-9 and abs(bout[1]) < 1e-9
    assert all(np.hypot(q[0], q[1]) <= 1 + 1e-9 for q in tr_[0])


@pytest.mark.parametrize('proj', ['nord', 'sud', 'globe'])
def test_jour_nuit_etiquettes_toutes_projections(appli, proj):
    from coupole.modules.anim import dessin
    a = catalogue.PAR_ID['daylightsimulator'].charger()()
    a.projection.setCurrentIndex(a.projection.findData(proj))
    a.c_crepuscule.setChecked(True)
    for w, h in TAILLES:
        a.image(w, h)
        b = dessin.etiquettes_posees()
        for i in range(len(b)):
            assert b[i][0] >= -1 and b[i][1] >= -1 and b[i][0] + b[i][2] <= w + 1 and b[i][1] + b[i][3] <= h + 1
            for j in range(i):
                assert _recouvrement(b[i], b[j]) <= 0.15 * min(b[i][2] * b[i][3], b[j][2] * b[j][3])
    a.close()


@pytest.mark.parametrize('ident,proj', [('daylightsimulator', 'globe'), ('longlat', None), ('celhorcomp', None),
                                        ('sunmotions', None), ('balloon', None)])
def test_fuzz_glisser_pendant_la_lecture(appli, ident, proj):
    """1 000 glissers aléatoires (petits, énormes, nuls, et quelques valeurs non finies) pendant que l'animation
    avance : l'orientation reste finie et orthonormée, le rendu n'est jamais vide."""
    import numpy as np
    from PyQt6.QtCore import QPointF, Qt
    from PyQt6.QtGui import QColor
    from coupole.modules.anim import dessin
    from coupole.modules.anim.animations import jour_nuit as jn
    rng = np.random.default_rng(7)
    a = catalogue.PAR_ID[ident].charger()()
    a.resize(900, 650)
    if proj:
        a.projection.setCurrentIndex(a.projection.findData(proj))
    if a.ANIMEE and not a.en_lecture:
        a.basculer_lecture()
    a.image(800, 600)
    avant = [np.array(v.d) for v in a.__dict__.values() if isinstance(v, dessin.Vue3D)]
    globe_avant = np.array(a.globe) if proj == 'globe' else None
    for k in range(1000):
        if k % 10 == 0:
            a.pas(0.05)                                 # l'animation avance entre les glissers
            a.image(800, 600)
        g = getattr(a, '_disque', None) or (400, 300, 200)
        x0, y0 = g[0] + rng.uniform(-50, 50), g[1] + rng.uniform(-50, 50)
        a.presser(QPointF(x0, y0), Qt.MouseButton.LeftButton)
        dx, dy = rng.choice([rng.normal(0, 3), rng.normal(0, 400), 0.0]), rng.normal(0, 30)
        if k % 97 == 0:
            dx = float('nan') if k % 2 else float('inf')
        a.glisser(QPointF(x0 + (dx if math.isfinite(dx) else 0), y0 + dy), dx, dy)
        a.relacher(QPointF(x0, y0))
        if hasattr(a, '_inertie_pas'):
            a._inertie_pas()
    if proj == 'globe':
        assert jn.valide(a.globe) and not np.allclose(a.globe, globe_avant)
    else:
        apres = [np.array(v.d) for v in a.__dict__.values() if isinstance(v, dessin.Vue3D)]
        assert any(not np.allclose(x, y) for x, y in zip(avant, apres))      # les glissers ont bien tourné la vue
    for v in a.__dict__.values():
        if isinstance(v, dessin.Vue3D):
            assert math.isfinite(v.az) and math.isfinite(v.alt)
            assert np.all(np.isfinite(v.d)) and abs(np.linalg.norm(v.d) - 1) < 1e-9
    img = a.image(800, 600)
    couleurs = {img.pixel(x, y) for x in range(0, 800, 8) for y in range(0, 600, 8)}
    assert len(couleurs) > 8
    fond = QColor(dessin.c('fond')).rgb()
    assert sum(1 for c in couleurs if c != fond) > 4
    if a.ANIMEE and a.en_lecture:
        a.basculer_lecture()
    a.close()


# ------------------------------------------------------------------ titres des panneaux (0.4.2)
def test_mise_en_page_des_titres():
    from coupole.modules.anim import dessin

    def mesure(s):
        return len(s) * 7

    assert dessin.titre_court('Système de Copernic (vu du nord)') == 'Système de Copernic'
    assert dessin.titre_court('Système de Ptolémée : épicycle sur le déférent') == 'Système de Ptolémée'
    t = 'Vénus au télescope (taille apparente à l’échelle)'
    assert dessin.mettre_en_page_titre(t, 1000, False, mesure) == ([t], False)
    lignes, abrege = dessin.mettre_en_page_titre(t, 200, True, mesure)
    assert len(lignes) == 2 and not abrege and ' '.join(lignes) == t
    assert dessin.mettre_en_page_titre(t, 140, False, mesure) == (['Vénus au télescope'], True)
    lignes, abrege = dessin.mettre_en_page_titre(t, 70, False, mesure)
    assert abrege and lignes[0].endswith('…')
    for larg in (0, 7, 30, 60, 100, 150, 220, 400):
        for deux in (True, False):
            assert all(mesure(x) <= max(larg, 7) for x in dessin.mettre_en_page_titre(t, larg, deux, mesure)[0])


@pytest.mark.parametrize('ident', [e.id for e in catalogue.ENTREES])
def test_titres_dans_leur_panneau(appli, ident):
    """Pour chaque animation, en français et en anglais, à 420 px de large (et dans les autres formats) : chaque titre
    de panneau reste dans son panneau, aucun ne recouvre un autre (bogue des « Phases de Vénus » sur fenêtre étroite)."""
    from coupole.core import i18n
    from coupole.modules.anim import dessin
    fautes = []
    langue = i18n.langue()
    try:
        for lg in ('fr', 'en'):
            i18n.choisir_langue(lg)
            a = catalogue.PAR_ID[ident].charger()()
            for w, h in ((420, 560), (300, 640)) + TAILLES[1:]:
                a.image(w, h)
                t = dessin.titres_poses()
                for j, u in enumerate(t):
                    x, y, bw, bh = u['boite']
                    px, py, pw, ph = u['panneau']
                    if x < px + 4 or x + bw > px + pw - 4 or y < py or y + bh > py + ph:
                        fautes.append('%s %dx%d : titre « %s » hors de son panneau' % (lg, w, h, u['complet']))
                    for v in t[j + 1:]:
                        if _recouvrement(u['boite'], v['boite']) > 0.25:
                            fautes.append('%s %dx%d : « %s » et « %s »' % (lg, w, h, u['complet'], v['complet']))
            a.close()
    finally:
        i18n.choisir_langue(langue)
    assert not fautes, fautes[:6]


def test_titre_abrege_infobulle_et_nom_accessible(appli):
    """Un titre abrégé garde son texte complet : info-bulle au survol du titre, et nom accessible de la toile."""
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest
    from coupole.modules.anim import dessin
    a = catalogue.PAR_ID['venusphases'].charger()()
    a.resize(420, 330)
    a.show()
    appli.processEvents()
    a.toile.repaint()
    appli.processEvents()
    t = a.toile._titres
    assert t and all(u['complet'] in a.toile.accessibleName() for u in t)
    # info-bulle : seulement au-dessus d'un titre abrégé (titre factice posé sur la toile déjà dessinée)
    a.toile._titres = [{'boite': (20.0, 10.0, 120.0, 16.0), 'abrege': True, 'complet': 'Titre complet (long)'}]
    # le curseur peut déjà être à cet endroit (test précédent, fenêtre de même géométrie) : sans déplacement réel, Qt
    # n'envoie aucun événement → on passe d'abord ailleurs (fragilité d'ordre, 0.7.0)
    QTest.mouseMove(a.toile, QPoint(5, a.toile.height() - 5))
    appli.processEvents()
    QTest.mouseMove(a.toile, QPoint(60, 18))
    appli.processEvents()
    assert a.toile.toolTip() == 'Titre complet (long)'
    QTest.mouseMove(a.toile, QPoint(a.toile.width() // 2, a.toile.height() - 5))
    appli.processEvents()
    assert a.toile.toolTip() == ''
    a.close()
    assert dessin.titre_court('A (b)') == 'A'
