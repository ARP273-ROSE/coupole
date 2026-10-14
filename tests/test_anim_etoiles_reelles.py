"""0.5.0 : spectres sur bases physiques, « Orion en 3D », fiches au survol, couleur vraie des étoiles et règle
typographique — mêmes cas que Coupole Web (références communes : tests/spectres_physiques_reference.json.gz,
orion3d_reference.json, couleurs_reference.json, typographie_cas.json, typographie_reference.json)."""
from __future__ import annotations

import gzip
import json
import math
import random
import time
from pathlib import Path

import pytest

ICI = Path(__file__).parent
ORION = json.loads((ICI / 'orion3d_reference.json').read_text(encoding='utf-8'))


def _proche(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(b))


# ------------------------------------------------------------------ moteur des spectres physiques
def _compare(a, b, chemin, err):
    if isinstance(b, dict):
        for k in b:
            _compare(a.get(k) if isinstance(a, dict) else None, b[k], '%s.%s' % (chemin, k), err)
    elif isinstance(b, list):
        if not isinstance(a, (list, tuple)) or len(a) != len(b):
            err.append('%s : longueur' % chemin)
        else:
            for k, (x, y) in enumerate(zip(a, b)):
                _compare(x, y, '%s[%d]' % (chemin, k), err)
    elif isinstance(b, (int, float)) and not isinstance(b, bool) and isinstance(a, (int, float)):
        if abs(a - b) > max(1e-12, 1e-9 * abs(b)):
            err.append('%s : %r ≠ %r' % (chemin, a, b))
    elif a != b:
        err.append('%s : %r ≠ %r' % (chemin, a, b))


def test_moteur_spectres_reproduit_les_100_cas():
    from coupole.modules.anim.spectre_physique import modele
    from coupole.modules.anim.spectres_physiques import ModeleSpectres
    m = modele()
    with gzip.open(ICI / 'spectres_physiques_reference.json.gz', 'rt', encoding='utf-8') as f:
        ref = json.load(f)
    err = []
    for c in ref['cas']:
        t, cl = c['type'], c['classe']
        e = m.etalonnage(t, cl)
        r = m.raies(t, cl)
        b = m.bandes(t, cl)
        got = {'etalonnage': e, 'intensites': m.intensites(t, cl), 'n_raies': len(r),
               'raies_fortes': sorted(r, key=lambda x: -x['W'])[:6], 'n_bandes': len(b), 'bandes_premieres': b[:3],
               'spectre': m.spectre(t, cl, ref['lambdas']), 'spectre_r0p3': m.spectre(t, cl, ref['lambdas'], None, 0.3),
               'spectre_h_seul': m.spectre(t, cl, ref['lambdas'], ['h']),
               'spectre_sans_molecules': m.spectre(t, cl, ref['lambdas'], ['he_ii', 'he_i', 'h', 'metaux_ionises', 'metaux']),
               'couleur_etoile': list(m.couleur_etoile(e['teff'])),
               'continu': [ModeleSpectres.continu_relatif(e['teff'], l) for l in (400, 500, 600, 700)],
               'beta_prime_500': ModeleSpectres.beta_prime(e['teff'], 500)}
        attendu = {k: v for k, v in c.items() if k not in ('type', 'classe')}
        _compare(got, attendu, '%s%s' % (cl, t), err)
    for l, rgb in ref['couleur_lambda'].items():
        _compare(list(m.couleur_lambda(float(l))), rgb, 'couleur_lambda[%s]' % l, err)
    assert err[:20] == [] and len(ref['cas']) == 100


def test_spectres_types_entiers_comme_le_modele():
    """Aux types entiers, l'étalonnage PCHIP est exactement celui du modèle et la grille fine des intensités retrouve
    sa table (calculée par la même physique : écart ≤ 0,02 sur 100) ; entre deux types, plus de cassure."""
    from coupole.modules.anim.spectre_physique import modele
    m = modele()
    with gzip.open(ICI / 'spectres_physiques_reference.json.gz', 'rt', encoding='utf-8') as f:
        ref = json.load(f)
    for c in ref['modele']:
        if c['type'] != int(c['type']):
            continue
        e = m.etalonnage(c['type'], c['classe'])
        assert abs(e['teff'] - c['etalonnage']['teff']) < 1e-6 * c['etalonnage']['teff']
        for f, v in c['intensites'].items():
            assert abs(m.intensites(c['type'], c['classe'])[f] - v) <= 0.02, (c['type'], c['classe'], f)
    # He II de B0 à B1 (classe V) : décroissance monotone, sans palier ni cassure (pente continue)
    xs = [10 + k / 32 for k in range(33)]
    ys = [m.intensites(x, 'V')['he_ii'] for x in xs]
    assert all(b <= a + 1e-9 for a, b in zip(ys, ys[1:]))
    d = [b - a for a, b in zip(ys, ys[1:])]
    assert max(abs(b - a) for a, b in zip(d, d[1:])) < 0.6


def test_spectres_controles_physiques():
    from coupole.modules.anim.spectre_physique import modele, remarques
    m = modele()
    assert m.etalonnage(42, 'V')['teff'] == pytest.approx(5770)

    def pic(f):
        return max(range(70), key=lambda t: m.intensites(t, 'V')[f])
    assert pic('he_ii') < pic('he_i') < pic('h') < pic('molecules')
    for cl in ('I', 'III', 'V'):
        for f in ('he_ii', 'he_i', 'h', 'metaux_ionises', 'metaux', 'molecules', 'ch'):
            avant = None
            for k in range(277):
                v = m.intensites(k / 4, cl)[f]
                assert math.isfinite(v)
                if avant is not None:
                    assert abs(v - avant) < 30, (cl, f, k)
                avant = v
    # cas signalés : supergéante B (log g hors grille), naine M froide (T_eff < 3 500 K), classe III interpolée
    assert any('ATLAS9' in r for r in remarques(12, 'I'))
    assert any('3' in r and 'ATLAS9' in r for r in remarques(66, 'V'))
    assert remarques(42, 'V') == []


def test_parallaxe_ancien_etalonnage_signale():
    from coupole.modules.anim.animations.parallaxe_spectro import magnitude_absolue
    assert not magnitude_absolue(42, 5)['ancien'] and magnitude_absolue(42, 5)['M'] == pytest.approx(4.80)
    assert magnitude_absolue(30, 1)['ancien'] and magnitude_absolue(30, 2)['ancien']    # F0 I, F0 II
    assert not magnitude_absolue(5, 1)['ancien']                                         # O5 I : Martins 2005


# ------------------------------------------------------------------ couleur vraie
def test_couleurs_cie_reference_et_accent():
    from coupole.modules.anim.couleur_etoile import accentuer, couleur_etoile, rayon_disque
    ref = json.loads((ICI / 'couleurs_reference.json').read_text(encoding='utf-8'))
    for e in ref['etoiles']:
        c = couleur_etoile(e['teff_K'])
        assert max(abs(a - b) for a, b in zip(c, e['rgb'])) <= 1, e['nom']
    r1, g1, b1 = couleur_etoile(3600)
    assert r1 > g1 > b1
    r2, _, b2 = couleur_etoile(12000)
    assert b2 > r2
    a = accentuer(couleur_etoile(3600))
    assert a[0] - a[2] > r1 - b1
    for t in (float('nan'), -5, 0, 1e9):
        assert all(math.isfinite(v) for v in couleur_etoile(t))
    assert rayon_disque(float('nan')) == 1.2


# ------------------------------------------------------------------ Orion en 3D : géométrie commune
def test_geometrie_orion_identique_au_web():
    from coupole.modules.anim import orion3d_geo as O
    for c in ORION['cameras']:
        cam = O.camera(*c['args'])
        for k in ('F', 'cx', 'cy', 'D'):
            assert _proche(cam[k], c['camera'][k]), (k, c['args'])
        for k in ('oeil', 'droite', 'haut', 'avant'):
            assert all(_proche(a, b) for a, b in zip(cam[k], c['camera'][k]))
        pts = [O.projeter(cam, O.deplier(e['xyz'], c['args'][3])) for e in O.DONNEES['etoiles'][::7]]
        for q, r in zip(pts, c['projections']):
            assert (q is None) == (r is None)
            if q:
                assert all(_proche(a, b, 1e-8) for a, b in zip(q, r))
    for (ra, dec), r in zip(((80, -4), (88, 0), (85, -10), (78, 5)), ORION['coquille']):
        q = O.point_coquille(O.direction(ra, dec), O.DONNEES['icrs_vers_gal'])
        assert all(_proche(a, b) for a, b in zip(q, r))


def test_donnees_orion_coherentes():
    from coupole.modules.anim import orion3d_geo as O
    for e in O.DONNEES['etoiles']:
        assert abs(O.norme(e['xyz']) - e['d']) < 0.02, e['id']
        u, d = O.unitaire(e['xyz']), O.direction(e['ra'], e['dec'])
        assert math.acos(min(1.0, O.dot(u, d))) < 1e-3, e['id']
    M = O.DONNEES['icrs_vers_gal']
    for i in range(3):
        for j in range(3):
            assert abs(O.dot(M[i], M[j]) - (1 if i == j else 0)) < 1e-9
    d = {e['id']: e['d'] for e in O.DONNEES['etoiles']}
    assert d['bet_ori'] == pytest.approx(264.55, abs=0.01) and d['tet01_ori_c'] == 388
    assert d['alf_ori'] == pytest.approx(168.1) and d['gam_ori'] == pytest.approx(77.4) and d['pi_03_ori'] == pytest.approx(8.07)
    # vue du ciel : œil au Soleil, gnomonique (nord en haut, est à gauche)
    cam = O.camera('orion', 'orion', 1, 0, 0, 0, 800, 600)
    assert O.norme(cam['oeil']) < 1e-9
    P = O.direction(83, 0)
    a = O.projeter(cam, O.comb(P, 100, (0, 0, 0), 0))
    b = O.projeter(cam, O.comb(P, 700, (0, 0, 0), 0))
    assert math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-9
    assert O.projeter(cam, O.comb(O.direction(83, 5), 400, (0, 0, 0), 0))[1] < a[1]
    assert O.projeter(cam, O.comb(O.direction(88, 0), 400, (0, 0, 0), 0))[0] < a[0]


# ------------------------------------------------------------------ fiches
def test_fiches_completes_et_identiques_au_web(langue):
    from coupole.modules.anim.fiche_texte import contenu_fiche
    from coupole.modules.anim.fiches import toutes_les_fiches
    F = toutes_les_fiches()
    assert len(F) > 300
    for lg in ('fr', 'en'):
        langue(lg)
        for i, f in F.items():
            assert f['id'] == i and f['categorie'] in ('etoile', 'nebuleuse') and f['noms']['fr'] and f['noms']['en']
            c = contenu_fiche(f, lg)
            tout = json.dumps([c['titre'], c['sous_titre'], c['lignes'], c['resume']], ensure_ascii=False)
            assert 'NaN' not in tout and 'None' not in tout and c['lignes'], i
        for i, att in ORION['fiches'][lg].items():
            c = contenu_fiche(F[i], lg)
            assert c['titre'] == att['titre'] and c['sous_titre'] == att['sous_titre'] and c['resume'] == att['resume']
            assert [(l['libelle'], l['valeur'], l['source']) for l in c['lignes']] == \
                [(l['libelle'], l['valeur'], l['source']) for l in att['lignes']], i


def test_placement_de_la_fiche():
    from coupole.modules.anim.fiche_flottante import placer_fiche
    for c in ORION['placements']:
        x, y, r, w, h, W, H = c['entree']
        bx, by = placer_fiche(x, y, r, w, h, W, H)
        assert _proche(bx, c['sortie'][0]) and _proche(by, c['sortie'][1])
        d = r + 10
        place = x + d + w <= W - 4 or x - d - w >= 4 or y + d + h <= H - 4 or y - d - h >= 4
        if place and w <= W - 8 and h <= H - 8:
            cx, cy = max(bx, min(bx + w, x)), max(by, min(by + h, y))
            assert math.hypot(cx - x, cy - y) >= r + 2 - 1e-9


# ------------------------------------------------------------------ animations à fiches (rendu hors écran)
def _anim(ident):
    from coupole.modules.anim import catalogue
    return catalogue.PAR_ID[ident].charger()()


@pytest.mark.parametrize('ident,mini', [('orion3d', 18), ('bigdipper', 7), ('dipperclock', 1), ('celhorcomp', 3),
                                         ('hrexplorer', 1), ('heliacalrisingsim', 1)])
def test_objets_a_fiche(app_qt, ident, mini):
    from coupole.modules.anim.fiches import toutes_les_fiches
    a = _anim(ident)
    assert type(a).FICHES
    if ident == 'hrexplorer':
        a.groupe.setCurrentIndex(3)
    if ident == 'dipperclock':
        a.heure.setValue(23)
    a.image(900, 640)
    assert len(a.survolables) >= mini
    F = toutes_les_fiches()
    for o in a.survolables:
        assert o['fiche'] in F and all(math.isfinite(o[k]) for k in ('x', 'y', 'r'))
    ordre = a.objets_ordonnes()
    assert all(ordre[i]['ordre'] >= ordre[i - 1]['ordre'] for i in range(1, len(ordre)))
    a.close()


def test_survol_toucher_clavier(app_qt):
    """La fiche suit la souris, le toucher et le clavier (Tab, flèches, Échap) ; jamais par-dessus l'objet."""
    from PyQt6.QtCore import QPoint, QPointF, Qt
    from PyQt6.QtTest import QTest
    a = _anim('orion3d')
    a.resize(1000, 760)
    a.show()
    app_qt.processEvents()
    t = a.toile
    t.repaint()
    app_qt.processEvents()
    assert a.survolables
    o = min(a.survolables, key=lambda u: u['ordre'])
    QTest.mouseMove(t, QPoint(int(round(o['x'])), int(round(o['y']))))
    app_qt.processEvents()
    f = t._fiche
    assert f is not None and f.isVisible() and f.affichee == o['fiche']
    g = f.geometry()
    cx, cy = max(g.left(), min(g.right(), o['x'])), max(g.top(), min(g.bottom(), o['y']))
    assert math.hypot(cx - o['x'], cy - o['y']) >= o['r']
    assert t.accessibleDescription()
    # Échap ferme ; Tab parcourt du plus brillant au plus faible ; flèches ensuite
    QTest.keyClick(t, Qt.Key.Key_Escape)
    assert not f.isVisible()
    t.setFocus()
    assert t.focusNextPrevChild(True) and t._designe[1] == 'clavier'
    premier = t._designe[0]
    QTest.keyClick(t, Qt.Key.Key_Right)
    assert t._designe[0] != premier
    QTest.keyClick(t, Qt.Key.Key_Escape)
    assert t._designe is None
    # toucher sans glisser : la fiche s'ouvre ; à côté : elle se ferme
    QTest.mouseClick(t, Qt.MouseButton.LeftButton, pos=QPoint(int(round(o['x'])), int(round(o['y']))))
    app_qt.processEvents()
    assert f.isVisible()
    a.close()


def test_orion_rendu_glissers_aberrants(app_qt):
    """1 000 glissers (dont aberrants), tous les réglages : jamais d'angle ni de valeur non finis ; scène fixe."""
    from PyQt6.QtCore import QPointF
    a = _anim('orion3d')
    assert not type(a).ANIMEE and not a.en_lecture
    g = random.Random(7)
    aberrants = (float('nan'), float('inf'), -float('inf'), 1e12, -1e12, 0.0)
    for i in range(1000):
        if i % 40 == 0:
            img = a.image(820, 560)
            assert not img.isNull()
            for _, (w, _d) in list(a._defauts.items()):
                if hasattr(w, 'setChecked'):
                    w.setChecked(g.random() < 0.5)
                elif hasattr(w, 'count'):
                    w.setCurrentIndex(int(g.random() * w.count()))
        a.presser(QPointF(g.random() * 820, g.random() * 560), None)
        dx = aberrants[i % 6] if i % 9 == 0 else (g.random() - 0.5) * 300
        dy = aberrants[(i + 3) % 6] if i % 11 == 0 else (g.random() - 0.5) * 300
        a.glisser(QPointF(g.random() * 820, g.random() * 560), dx, dy)
        a.relacher(QPointF(0, 0))
        assert math.isfinite(a.vue3d.az) and math.isfinite(a.vue3d.alt)
    for _, v in a.valeurs():
        assert 'nan' not in v.lower() and 'inf' not in v.lower()
    a.close()


def test_orion_vues_et_scene_fixe(app_qt):
    """Boutons « de face » et « de côté » : vue instantanée, aucune lecture ; rien ne redessine la scène au repos."""
    from coupole.modules.anim.animations.orion3d import VUE_COTE, VUE_FACE
    a = _anim('orion3d')
    assert (a.vue3d.az, a.vue3d.alt) == VUE_COTE
    a._regarder(VUE_FACE)
    assert abs(a.vue3d.alt - VUE_FACE[1]) < 1e-9
    assert not a.en_lecture and not a.minuteur.isActive()
    a._regarder(VUE_COTE)
    assert not a.en_lecture and not a.minuteur.isActive()
    a.close()


def test_orion_nebuleuses_identiques_au_web_et_publiees():
    """Volumes de M42 et d'IC 434 : mêmes particules que le web (référence commune), à la bonne place."""
    from coupole.modules.anim import nebuleuses_orion as N
    from coupole.modules.anim import orion3d_geo as O
    ref = json.loads((Path(__file__).parent / 'nebuleuses_orion_reference.json').read_text('utf-8'))
    assert ref['agrandi'] == N.AGRANDI
    for n, r in zip(N.nebuleuses(), ref['nebuleuses']):
        assert n['id'] == r['id'] and len(n['particules']) == len(r['particules'])
        for q, x in zip(n['particules'], r['particules']):
            assert max(abs(q['p'][i] - x[i]) for i in range(3)) < 1e-3 and q['genre'] == x[-1]
    m42, ic = N.nebuleuses()
    # centre de M42 = θ¹ Ori C (388 pc) ; front 0,2 pc derrière lui, agrandi ×AGRANDI
    assert abs(O.norme(m42['centre']) - 388.0) < 0.5
    rep = m42['reperes'][0]['p']
    assert abs(O.norme([rep[i] - m42['centre'][i] for i in range(3)]) - 0.2 * N.AGRANDI) < 0.01
    # σ Ori : 3,9 pc projetés de la Tête de Cheval (Gerin et al. 2009 : 3,5 pc à leur distance), agrandis
    s = ic['etoiles'][0]['p']
    assert 3.6 * N.AGRANDI < O.norme([s[i] - ic['centre'][i] for i in range(3)]) < 4.2 * N.AGRANDI
    assert 300 < sum(len(n['particules']) for n in N.nebuleuses()) < 1200


def test_rendu_rapide(app_qt):
    """Coût d'une image (hors écran, minimum de 8) : Orion dans ses vues, spectres ; NAS chargé : borne large."""
    mesures = {}
    for ident, reglages in (('orion3d', {}), ('orion3d', {'nuages': True}), ('orion3d', {'face': True}),
                            ('spectrum010', {}), ('spectroparallax', {})):
        a = _anim(ident)
        for k, v in reglages.items():
            if k == 'face':
                from coupole.modules.anim.animations.orion3d import VUE_FACE
                a._regarder(VUE_FACE)
            else:
                a._defauts[k][0].setChecked(v)
        a.image(720, 470)
        ts = []
        for _ in range(8):
            t0 = time.perf_counter()
            a.image(720, 470)
            ts.append(time.perf_counter() - t0)
        mesures['%s %s' % (ident, reglages)] = min(ts) * 1000
        a.close()
    print(mesures)
    assert max(mesures.values()) < 40


# ------------------------------------------------------------------ règle typographique
def test_formateur_commun_et_regle():
    from coupole.modules.anim import typographie as T
    from coupole.modules.anim.typo import interdit, typo
    cas = json.loads((ICI / 'typographie_cas.json').read_text(encoding='utf-8'))
    for a, b in cas['unite']:
        assert T.unite(a) == b
    for (x, lg, d), b in cas['nombre']:
        assert T.nombre(x, lg, d) == b
    for (x, lg, c), b in cas['sci']:
        assert T.sci(x, lg, c) == b
    for (t, lg), n in cas['controle']:
        assert (len(T.controle(t, lg)) > 0) == (n > 0), t
    ref = json.loads((ICI / 'typographie_reference.json').read_text(encoding='utf-8'))
    for a, b in ref['typo']:
        assert typo(a) == b, a
    for a, b in ref['interdits']:
        assert interdit(a) == b, a


def _fautes(s, lg):
    from coupole.modules.anim import formule, typographie as T
    from coupole.modules.anim.typo import interdit
    s = s.replace('CC BY 4.0', '').replace('License 2.0', '')
    texte = ' '.join(m for g, m in formule.morceaux(s) if g == 'texte')
    return T.controle(texte, lg) + (['règle des animations'] if interdit(texte) else [])


def test_textes_selon_la_regle():
    from coupole.modules.anim.textes import TEXTES
    fautes = []
    for k, v in TEXTES.items():
        if k.endswith('_html'):
            continue
        for lg in ('fr', 'en'):
            if isinstance(v.get(lg), str) and _fautes(v[lg], lg):
                fautes.append('%s (%s) : %s' % (k, lg, _fautes(v[lg], lg)))
    assert fautes == []


def test_valeurs_et_toile_selon_la_regle(app_qt, langue, monkeypatch):
    """Les 94 animations : valeurs affichées et textes dessinés sur la toile, réglages par défaut puis changés."""
    from coupole.modules.anim import catalogue, dessin
    from coupole.modules.anim.typo import interdit
    ecrits = []
    avant = dessin._ecrire

    def espion(p, x, y, s):
        ecrits.append(s)
        return avant(p, x, y, s)
    monkeypatch.setattr(dessin, '_ecrire', espion)
    fautes = set()
    for lg in ('fr', 'en'):
        langue(lg)
        for e in catalogue.ENTREES:
            a = e.charger()()
            a.image(900, 620)
            for k, (cle, (w, _d)) in enumerate(a._defauts.items(), start=1):
                if hasattr(w, 'mini'):
                    w.setValue(w.mini + ((k * 0.37) % 1) * (w.maxi - w.mini))
                elif hasattr(w, 'setChecked'):
                    w.setChecked(not w.isChecked())
                elif hasattr(w, 'count') and w.count() > 1:
                    w.setCurrentIndex(k % w.count())
            a.pas(0.4)
            a.image(900, 620)
            for x, y in a.valeurs():
                for s in (x, y):
                    if _fautes(s, lg):
                        fautes.add('%s : %s %s' % (e.id, s, _fautes(s, lg)))
            a.close()
    for s in ecrits:
        if interdit(s):
            fautes.add('toile : %s' % s)
    assert sorted(fautes) == []


def test_formules_delimiteurs_extensibles():
    from coupole.modules.anim import formule

    def ecrire(n):
        k = n[0]
        if k == 'rangee':
            return ' '.join(ecrire(x) for x in n[1])
        if k in ('id', 'nb', 'op'):
            return n[1]
        if k == 'frac':
            return '(%s)/(%s)' % (ecrire(n[1]), ecrire(n[2]))
        if k == 'sup':
            return '%s^%s' % (ecrire(n[1]), ecrire(n[2]))
        if k == 'sub':
            return '%s_%s' % (ecrire(n[1]), ecrire(n[2]))
        if k == 'subsup':
            return '%s_%s^%s' % (ecrire(n[1]), ecrire(n[2]), ecrire(n[3]))
        if k == 'racine':
            return '√[%s]' % ecrire(n[1])
        if k == 'paren':
            return '%s%s%s' % (n[2], ecrire(n[1]), n[3])
        return '?'
    for s, att in (('d = 10^((m − M + 5)/5)', 'd = 10^(m − M + 5)/(5)'),
                   ('t ≈ 10¹⁰ × (M/M☉)^(−2,5)', 't ≈ 10^10 × ((M)/(M_☉))^− 2,5'),
                   ('√((1+β)/(1−β))', '√[(1 + β)/(1 − β)]'),
                   ('λ_max = b / T', 'λ_max = (b)/(T)'), ('sin E = a_int / a_ext', 'sin E = (a_int)/(a_ext)')):
        assert ecrire(formule.analyser(s)) == att, s
    # le glyphe des parenthèses est agrandi (ky > 1,2) autour d'une fraction ; la racine couvre son contenu
    for s in ('t ≈ 10¹⁰ × (M/M☉)^(−2,5)', 'L / L☉ = (R / R☉)² (T / T☉)⁴', 'E = 13,598 eV (1/n² − 1/m²)'):
        prims = formule.mise_en_page(s, 16.0)[3]
        assert max([q[7] for q in prims if q[0] == 't' and len(q) > 7] or [0]) > 1.2, s
    simple, grande = formule.mise_en_page('√x', 16.0), formule.mise_en_page('√((1+β)/(1−β))', 16.0)
    assert grande[1] + grande[2] > 1.5 * (simple[1] + simple[2])
    assert formule.analyser('λ_max')[2] == ('id', 'max')


def test_valeurs_verifiees_par_sagemath():
    """outils/verif_anim/etoiles_reelles_verif.sage (conteneur sagemath, 120 bits) : parsec → année-lumière, distances
    et barres des 300 fiches, parallaxe du Trapèze, matrice ICRS → galactique contre sa définition."""
    s = json.loads((ICI / 'etoiles_reelles_sage.json').read_text(encoding='utf-8'))
    assert s['pc_en_al'] == pytest.approx(3.2615637772, abs=1e-10)        # constante des valeurs d'Orion en 3D
    assert s['distances_verifiees'] > 290 and s['ecart_relatif_max_al'] < 1e-3 and s['ecart_relatif_max_barres'] < 0.06
    assert round(s['trapeze_pc']) == 402 and round(s['trapeze_moins_pc']) == 4 and round(s['trapeze_plus_pc']) == 4
    assert s['matrice_galactique_ecart_max'] < 1e-6 and s['matrice_galactique_orthonormee'] < 1e-9
    assert s['norme_xyz_moins_d_max'] < 0.02 and s['tabit_al'] == pytest.approx(26.32, abs=0.01)
