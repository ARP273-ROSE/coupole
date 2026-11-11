"""« Le canon de Newton » (0.9.0) : constantes et valeurs de référence recalculées par SageMath
(tests/canon_newton_sage.json : vitesses de satellisation et de libération, éléments des préréglages, impacts par
l'équation de Kepler, antipodes, tirs avec air intégrés par DOP853), cas communs avec Coupole Web
(tests/canon_cas.json), puis l'animation hors écran : préréglages, défis réussis et ratés, flèche à tirer, clavier,
zoom et recadrage, valeurs, durée d'une image, aucune image qui gèle."""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import pytest

from coupole.modules.anim import canon_meca as C

ICI = Path(__file__).resolve().parent
SAGE = json.loads((ICI / 'canon_newton_sage.json').read_text('utf-8'))
#: le fichier des cas communs est produit sous Linux : comparaison au bit près sur la même libm seulement
LIBM_REFERENCE = sys.platform.startswith('linux')
CAS = json.loads((ICI / 'canon_cas.json').read_text('utf-8'))


def _proche(a, b, rel):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-300)


def _jusqu_au_bout(t, dt=60.0, n=100000):
    for _ in range(n):
        if t.etat != 'vol':
            break
        t.avancer(dt, 10 ** 7)
    return t


# ------------------------------------------------------------------ constantes et formules
def test_constantes_des_astres_comme_sagemath():
    for nom, A in C.ASTRES.items():
        s = SAGE['astres'][nom]
        assert _proche(A['gm'], s['gm'], 1e-12), nom
        # Cérès : rayon de la sphère de même volume, arrondi à 10 m
        assert _proche(A['r'], s['r'], 2e-7 if nom == 'ceres' else 1e-15), nom


@pytest.mark.parametrize('astre', C.NOMS_ASTRES)
def test_vitesses_et_elements_comme_sagemath(astre):
    A = C.ASTRES[astre]
    s = SAGE['vitesses'][astre]
    assert _proche(C.v_satellisation(A['gm'], A['r']), s['surface']['v1'], 1e-6 if astre == 'ceres' else 1e-13)
    assert _proche(C.v_liberation(A['gm'], A['r']), s['surface']['v2'], 1e-6 if astre == 'ceres' else 1e-13)
    R = C.REGLAGES[astre]
    d = s['defaut']
    x, y, vx, vy = C.etat_tir(A['r'], R['a0'] * R['ua'], R['v0'] * R['uv'], 0.0)
    el = C.elements(A['gm'], A['r'], x, y, vx, vy)
    tol = 1e-6 if astre == 'ceres' else 1e-11
    for k in ('eps', 'e', 'rp', 'ra', 'T'):
        assert _proche(el[k], d[k], tol), (astre, k)


@pytest.mark.parametrize('nom', sorted(SAGE['prereglages']))
def test_prereglages_comme_sagemath(nom):
    s = SAGE['prereglages'][nom]
    pre, _, astre = nom.rpartition('_')
    if nom in ('iss', 'rentree'):
        pre, astre = nom, 'terre'
    elif nom.startswith('ras_sol'):
        pre, astre = 'ras_sol', nom[len('ras_sol_'):]
    p = C.prereglage(pre, astre)
    assert p['astre'] == s['astre'] and p['altitude'] == s['altitude']
    tol = 1e-6 if astre == 'ceres' else 1e-12
    assert _proche(p['v'], s['v'], tol)
    A = C.ASTRES[p['astre']]
    x, y, vx, vy = C.etat_tir(A['r'], p['altitude'], p['v'], p['angle'])
    el = C.elements(A['gm'], A['r'], x, y, vx, vy)
    assert abs(el['e'] - s['e']) < 1e-9
    assert _proche(el['rp'], s['rp'], tol) or s['e'] < 1e-9
    if 'T' in s and s['e'] < 0.99:            # (parabole : énergie nulle à l'arrondi près, période sans objet)
        assert _proche(el['T'], s['T'], tol)
    attendu = {'pied': 'retombe', 'ras_sol': 'cercle', 'iss': 'cercle', 'ellipse': 'ellipse', 'liberation': 'parabole',
               'hyperbole': 'hyperbole', 'rentree': 'ellipse'}[pre]
    assert el['type'] == attendu
    if 'impact_deg' in s:
        # le tir intégré retombe là où Kepler le dit
        t = _jusqu_au_bout(C.Tir(1, p['astre'], p['altitude'], p['v'], p['angle']), 10.0)
        assert t.etat == 'impact'
        assert abs(t.angle_balaye_deg() - s['impact_deg']) < 2e-4 * max(1.0, s['impact_deg'])
        assert _proche(t.t, s['impact_s'], 2e-5)


@pytest.mark.parametrize('nom', ['terre_5kms_45deg', 'lune_1kms_30deg'])
def test_tirs_inclines_retombent_comme_kepler(nom):
    s = SAGE['tirs'][nom]
    astre, alt, v, ang = {'terre_5kms_45deg': ('terre', 100e3, 5000.0, 45.0),
                          'lune_1kms_30deg': ('lune', 10e3, 1000.0, 30.0)}[nom]
    t = _jusqu_au_bout(C.Tir(1, astre, alt, v, ang), 5.0)
    assert t.etat == 'impact'
    assert abs(t.angle_balaye_deg() - s['impact_deg']) < 1e-4 * s['impact_deg']
    assert _proche(t.t, s['impact_s'], 1e-5)


def test_antipodes():
    s = SAGE['antipodes']
    A = C.ASTRES['terre']
    # tir horizontal qui touche le sol au périgée : la vitesse « juste aux antipodes »
    r0 = A['r'] + 100e3
    assert _proche(math.sqrt(2 * A['gm'] * A['r'] / (r0 * (r0 + A['r']))), s['v'], 1e-13)
    t = _jusqu_au_bout(C.Tir(1, 'terre', 100e3, s['v_179'], 0.0), 30.0)
    assert t.etat == 'impact' and abs(t.angle_balaye_deg() - 179) < 0.05
    # incliné de 10° : une plage de 36 m·s⁻¹ (jouable au curseur, pas de 10 m·s⁻¹) mène à 180° ± 3°
    lo, hi = s['plage_10deg']
    assert 30 < hi - lo < 40
    for v, d in ((s['v_180_10deg'], 180.0), (lo, 177.0), (hi, 183.0)):
        t = _jusqu_au_bout(C.Tir(1, 'terre', 100e3, v, 10.0), 30.0)
        assert abs(t.angle_balaye_deg() - d) < 0.01
    assert C.juger('antipodes', _jusqu_au_bout(C.Tir(1, 'terre', 100e3, 7930.0, 10.0)))[0] == 'reussi'
    assert C.juger('antipodes', _jusqu_au_bout(C.Tir(1, 'terre', 100e3, 7900.0, 10.0)))[0] == 'echec'


@pytest.mark.parametrize('nom,astre,alt,ang,proj', [
    ('rentree_capsule', 'terre', 200e3, 0, 'capsule'), ('boulet_100km_5kms', 'terre', 100e3, 0, 'boulet'),
    ('satellite_180km', 'terre', 180e3, 0, 'satellite'), ('mars_boulet_50km_2500', 'mars', 50e3, 0, 'boulet')])
def test_air_comme_dop853(nom, astre, alt, ang, proj):
    """Avec l'air (frottement en schéma d'ordre 1, pas borné par le temps de freinage et la hauteur d'échelle) :
    même impact que l'intégration DOP853 de SageMath à 0,4 % près."""
    s = SAGE['air'][nom]
    v = s.get('v', {'boulet_100km_5kms': 5000.0, 'mars_boulet_50km_2500': 2500.0}.get(nom))
    t = _jusqu_au_bout(C.Tir(1, astre, alt, v, ang, True, proj), 120.0)
    assert t.etat == 'impact' and s['touche']
    assert _proche(t.t, s['impact_s'], 4e-3)
    assert abs(t.angle_balaye_deg() - s['impact_deg']) < 4e-3 * s['impact_deg']


def test_densite_de_l_air():
    # continuité du modèle par tranches (CIRA-72) : chaque tranche prolongée donne presque la suivante
    for (h0, r0, H), (h1, r1, _) in zip(C.ATM_TERRE, C.ATM_TERRE[1:]):
        assert _proche(r0 * math.exp(-(h1 - h0) / H), r1, 0.12)
    assert C.densite('terre', 0) == 1.225 and C.densite('terre', 3e6) == 0
    assert _proche(C.densite('terre', 400e3), 3.725e-12, 1e-12)
    assert C.densite('mars', 0) == 0.020 and C.densite('lune', 0) == 0


def test_periode_mesuree_comme_kepler():
    p = C.prereglage('iss', 'terre')
    t = C.Tir(1, 'terre', p['altitude'], p['v'], 0.0)
    for _ in range(40):
        t.avancer(300.0)
    assert t.tours() >= 2 and _proche(t.periode(), SAGE['prereglages']['iss']['T'], 1e-7)
    assert abs(t.periode() / 60 - 92.867) < 0.001


def test_liberation_et_hyperbole():
    for nom in ('liberation', 'hyperbole'):
        p = C.prereglage(nom, 'terre')
        t = _jusqu_au_bout(C.Tir(1, 'terre', p['altitude'], p['v'], 0.0), 600.0)
        assert t.etat == 'libere' and t.rayon() > C.LOIN * (C.ASTRES['terre']['r'] + p['altitude'])


def test_pas_borne_par_appel():
    """Jamais de gel : un appel fait au plus MAX_PAS_IMAGE pas, même dans l'air dense à 8 km·s⁻¹."""
    t = C.Tir(1, 'terre', 1000.0, 8000.0, 0.0, True, 'boulet')
    k = t.avancer(1e6)
    assert k <= C.MAX_PAS_IMAGE


# ------------------------------------------------------------------ cas communs avec Coupole Web
def test_cas_communs_reproduits():
    """Le fichier partagé avec le web (outils/cas_canon.py) est bien ce que calcule canon_meca aujourd'hui."""
    for cas in CAS['tirs']:
        t = C.Tir(1, cas['astre'], cas['alt'], cas['v'], cas['angle'], cas['air'], cas['projectile'])
        for e in cas['etapes']:
            k = t.avancer(cas['dt'])
            b = t.boulet
            assert k == e['pas'] and t.etat == e['etat'] and t.tours() == e['tours'] and len(t.x) == e['n_trace']
            for a, x in ((t.t, e['t']), (b.x, e['x']), (b.y, e['y']), (b.vx, e['vx']), (b.vy, e['vy']),
                         (t.phi, e['phi'])):
                # au bit près sous Linux (où le fichier est produit) ; ailleurs, la bibliothèque mathématique
                # (sqrt, exp, atan2) peut différer du dernier bit (Windows, macOS : CI du 11/11/2026)
                assert a == x if LIBM_REFERENCE else math.isclose(a, x, rel_tol=1e-9, abs_tol=1e-9)
    for p, v in CAS['prereglages'].items():
        astre, _, nom = p.partition('_')
        assert C.prereglage(nom, astre) == v


# ------------------------------------------------------------------ animation (hors écran)
def _anim():
    from coupole.modules.anim.animations.canon_newton import CanonNewton
    a = CanonNewton()
    a.resize(1100, 800)
    a.image(900, 640)
    return a


def test_feu_lecture_et_valeurs(app_qt, langue):
    for lg in ('fr', 'en'):
        langue(lg)
        a = _anim()
        assert not a.tirs and not a.en_lecture
        v = dict(a.valeurs())
        assert len(v) >= 5
        a.feu()
        assert a.en_lecture and len(a.tirs) == 1
        for _ in range(40):
            a.pas(0.2)
        assert a.courant().etat == 'impact'
        texte = ' '.join(b for _, b in a.valeurs())
        assert ('impact' in texte)
        a.close()


def test_prereglages_un_clic(app_qt):
    a = _anim()
    for nom in C.PREREGLAGES:
        a.prereglage(nom)
        assert a.tirs[-1].el0['type'] == {'pied': 'retombe', 'ras_sol': 'cercle', 'iss': 'cercle',
                                          'ellipse': 'ellipse', 'liberation': 'parabole', 'hyperbole': 'hyperbole',
                                          'rentree': 'ellipse'}[nom]
        assert a.en_lecture
        for _ in range(5):
            a.pas(0.2)
    assert a.astre() == 'terre' and a.c_air.isChecked()        # la rentrée se passe sur Terre, avec l'air
    a.recommencer()
    assert len(a.tirs) == C.PREREGLAGES.__len__() and a.tirs[-1].t == 0
    a.effacer()
    assert not a.tirs
    a.close()


def test_tirs_gardes_et_couleurs(app_qt):
    from coupole.modules.anim.animations.canon_newton import MAX_TIRS
    a = _anim()
    for _ in range(MAX_TIRS + 3):
        a.feu()
    assert len(a.tirs) == MAX_TIRS and a.tirs[-1].n == MAX_TIRS + 3
    assert len({t.couleur for t in a.tirs}) == MAX_TIRS
    a.close()


def _jouer(a, n=400, dt=0.5):
    for _ in range(n):
        a.pas(dt)
        if a.verdict()[0] in ('reussi', 'echec'):
            break
    return a.verdict()


def test_defis(app_qt):
    a = _anim()
    d = a.c_defi
    # orbite circulaire : contexte Terre 300 km ; à v₁, réussi après un tour
    d.setCurrentIndex(d.findData('cercle'))
    assert a.astre() == 'terre' and a.altitude_m() == 300e3
    A = C.ASTRES['terre']
    a.r_vit['terre'].setValue(C.v_satellisation(A['gm'], A['r'] + 300e3) / 1000)
    a.feu()
    assert _jouer(a)[0] == 'reussi'
    a.r_vit['terre'].setValue(9.0)
    a.feu()
    assert _jouer(a)[0] == 'echec'
    # libération au plus juste depuis la Lune
    d.setCurrentIndex(d.findData('liberation'))
    assert a.astre() == 'lune'
    L = C.ASTRES['lune']
    v2 = C.v_liberation(L['gm'], L['r'] + 10e3) / 1000
    a.r_vit['lune'].setValue(v2 * 1.01)
    a.feu()
    assert _jouer(a, 2000, 1.0)[0] == 'reussi'
    a.r_vit['lune'].setValue(v2 * 1.05)
    a.feu()
    assert _jouer(a)[0] == 'echec'
    # au-dessus de l'air : depuis 60 km, impossible ; en montant le canon à 150 km, réussi
    d.setCurrentIndex(d.findData('au_dessus'))
    assert a.c_air.isChecked() and a.altitude_m() == 60e3
    a.r_vit['terre'].setValue(C.v_satellisation(A['gm'], A['r'] + 60e3) / 1000)
    a.feu()
    etat, txt = _jouer(a)
    assert etat == 'echec' and ('100' in txt or 'point de départ' in txt)
    a.r_alt['terre'].setValue(150)
    a.r_vit['terre'].setValue(C.v_satellisation(A['gm'], A['r'] + 150e3) / 1000)
    a.feu()
    assert _jouer(a)[0] == 'reussi'
    # antipodes : 10° et 7,93 km·s⁻¹
    d.setCurrentIndex(d.findData('antipodes'))
    a.r_angle.setValue(10.0)
    a.r_vit['terre'].setValue(7.93)
    a.feu()
    assert _jouer(a)[0] == 'reussi'
    # Dimorphos : un tour au ras du sol
    d.setCurrentIndex(d.findData('dimorphos'))
    assert a.astre() == 'dimorphos' and a.c_temps.currentData() == 1000
    a.prereglage('ras_sol')
    assert _jouer(a)[0] == 'reussi'
    a.c_temps.setCurrentIndex(a.c_temps.findData(1000))
    a.close()


def test_fleche_clavier_zoom(app_qt):
    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QKeyEvent
    a = _anim()
    tx, ty = a._bout()
    X, Y = a._bouche()
    assert a.presser(QPointF(tx, ty), Qt.MouseButton.LeftButton)
    a.glisser(QPointF(X + 100, Y - 100), 0, 0)
    a.relacher(QPointF(X + 100, Y - 100))
    assert a.r_angle.value() == pytest.approx(45.0, abs=0.06)
    v = a.r_vit['terre'].value()
    assert v == pytest.approx(math.hypot(100, 100) / a._k_fleche() / 1000, rel=1e-2)
    # presque horizontal : aimanté à 0°
    tx, ty = a._bout()
    assert a.presser(QPointF(tx, ty), Qt.MouseButton.LeftButton)
    a.glisser(QPointF(X + 120, Y - 2), 0, 0)
    a.relacher(QPointF(X + 120, Y - 2))
    assert a.r_angle.value() == 0.0
    # clavier : Espace tire, flèches règlent
    def touche(k):
        return a.touche(QKeyEvent(QEvent.Type.KeyPress, k, Qt.KeyboardModifier.NoModifier))
    assert touche(Qt.Key.Key_Space) and len(a.tirs) == 1
    v0 = a.r_vit['terre'].value()
    assert touche(Qt.Key.Key_Up) and a.r_vit['terre'].value() > v0
    assert touche(Qt.Key.Key_Left) and a.r_angle.value() == 1.0
    assert not touche(Qt.Key.Key_A)
    # molette : zoom manuel ; on peut alors déplacer la vue ; double-clic : retour au cadrage automatique
    s0 = a._cam['s']
    assert a.molette(QPointF(450, 320), 240)
    a.image(900, 640)
    assert a.manuel is not None and a._cam['s'] == pytest.approx(s0 * 1.44, rel=1e-6)
    assert a.presser(QPointF(30, 600), Qt.MouseButton.LeftButton)
    a.glisser(QPointF(80, 600), 50, 0)
    a.relacher(QPointF(80, 600))
    assert a.double_clic(QPointF(10, 10)) and a.manuel is None
    a.close()


def test_cadrage_suit_le_boulet(app_qt):
    """Cadrage automatique : la planète, la trajectoire prévue et le boulet tiennent dans le panneau."""
    a = _anim()
    a.prereglage('hyperbole')
    for _ in range(80):
        a.pas(1.0)
        a.image(900, 640)
        b = a.courant().boulet
        X, Y = a._vers_ecran(b.x, b.y)
        r = a._panneau
        assert r.left() - 1 <= X <= r.right() + 1 and r.top() - 1 <= Y <= r.bottom() + 1
    a.close()


def test_changer_d_astre(app_qt):
    a = _anim()
    a.feu()
    a.c_astre.setCurrentIndex(a.c_astre.findData('ceres'))
    assert not a.tirs and a.c_temps.currentData() == 1000
    assert a.r_vit['ceres'].isVisibleTo(a) and not a.r_vit['terre'].isVisibleTo(a)
    assert not a.c_air.isVisibleTo(a)
    reps = a.r_vit['ceres']._regle.reperes
    assert [t for _, t, _ in reps] == ['v₁', 'v₂'] and reps[1][0] == pytest.approx(reps[0][0] * math.sqrt(2))
    a.close()


def test_rendu_rapide(app_qt):
    """Une image en moins de 30 ms (thèmes, tirs dans l'air et hors de l'air, 8 traces)."""
    import os
    a = _anim()
    for nom in ('pied', 'ras_sol', 'ellipse', 'liberation', 'hyperbole', 'rentree', 'iss', 'ras_sol'):
        a.prereglage(nom)
        for _ in range(30):
            a.pas(0.3)
    meilleur = math.inf
    for _ in range(6):
        t0 = time.perf_counter()
        for _ in range(5):
            a.image(900, 640)
        meilleur = min(meilleur, (time.perf_counter() - t0) / 5)
    assert meilleur < (0.06 if os.environ.get('CI') else 0.03)
    a.close()


def test_aimant_v1_v2(app_qt):
    """Posé « sur » v₁ ou v₂ (glissière ou flèche), le curseur donne la valeur exacte : un peu moins, le boulet
    s'écrasait au ras du sol ou revenait au lieu de s'échapper.  Un pas du clavier sort du repère."""
    a = _anim()
    a.prereglage('ras_sol')
    r = a.r_vit[a.astre()]
    A = C.ASTRES[a.astre()]
    r0 = A['r'] + a.altitude_m()
    v1 = C.v_satellisation(A['gm'], r0) / C.REGLAGES[a.astre()]['uv']
    v2 = C.v_liberation(A['gm'], r0) / C.REGLAGES[a.astre()]['uv']
    r.setValue(5.0)
    r.curseur.setValue(r._pos(v1) - 2)
    assert r.value() == v1
    r.setValue(5.0)
    r.curseur.setValue(r._pos(v2) + 3)
    assert r.value() == v2
    r.curseur.setValue(r.curseur.value() + 1)
    assert r.value() != v2
    assert r.aimanter(9.5) == 9.5
