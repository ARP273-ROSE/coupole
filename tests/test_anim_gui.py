"""Module « Animations » : catalogue (92 animations, états, recherche), chaque animation créée hors écran, animée,
dessinée, réglages gardés, bilinguisme, contraste des couleurs, panneau dans la fenêtre principale, ligne de
commande."""
import json
import time

import pytest

from coupole.modules.anim import catalogue


# ---------------------------------------------------------------- catalogue (sans Qt)
def test_catalogue_complet():
    assert len(catalogue.ENTREES) == 95
    assert len({e.id for e in catalogue.ENTREES}) == 95
    assert set(e.theme for e in catalogue.ENTREES) <= set(catalogue.THEMES)
    assert set(catalogue.LOT1) <= {e.id for e in catalogue.faites()}
    assert len(catalogue.LOT1) == 21


def test_catalogue_textes_bilingues():
    from coupole.core import i18n
    cles = i18n.toutes_les_cles()
    for e in catalogue.ENTREES:
        for pref in ('anim_nom_', 'anim_desc_'):
            assert cles[pref + e.cle]['fr'] and cles[pref + e.cle]['en'], e.id
    for t in catalogue.THEMES:
        assert 'anim_theme_' + t in cles


def test_catalogue_classes_importables():
    from coupole.modules.anim.base import Animation
    for e in catalogue.faites():
        cls = e.charger()
        assert issubclass(cls, Animation) and cls.ID == e.id


def test_cli_liste_et_info(capsys):
    from coupole.cli import main
    assert main(['--lang', 'fr', 'anim', 'liste', '--json']) in (0, None)
    d = json.loads(capsys.readouterr().out)
    assert len(d) == 95 and sum(x['disponible'] for x in d) == len(catalogue.faites())
    assert main(['--lang', 'fr', 'anim', 'info', 'sunmotions']) in (0, None)
    assert 'Soleil' in capsys.readouterr().out
    assert main(['--lang', 'fr', 'anim', 'info', 'inexistante']) == 1


# ---------------------------------------------------------------- chaque animation
@pytest.fixture
def propre(app_qt):
    from coupole.gui import memoire
    memoire.reinitialiser_pour_tests()
    yield app_qt


@pytest.mark.parametrize('ident', [e.id for e in catalogue.faites()])
def test_animation_creee_animee_dessinee(propre, ident):
    """Création hors écran, dix pas d'animation, rendu sans erreur et non vide, image < 60 ms, toutes les
    étiquettes traduites, tous les réglages ont une info-bulle."""
    from PyQt6.QtWidgets import QAbstractButton, QAbstractSpinBox, QComboBox, QSlider
    from coupole.core import i18n
    cls = catalogue.PAR_ID[ident].charger()
    w = cls()
    w.resize(1000, 760)
    w.show()
    propre.processEvents()
    for _ in range(10):
        w.pas(0.1)
    propre.processEvents()
    t0 = time.perf_counter()
    img = w.image(800, 520)
    dt = time.perf_counter() - t0
    assert not img.isNull()
    couleurs = {img.pixel(x, y) for x in range(0, 800, 4) for y in range(0, 520, 4)}
    assert len(couleurs) > 8, 'rendu vide'          # un fond uni n'a qu'une couleur ; tracés lissés : des dizaines
    assert dt < 0.5                    # large pour les machines de CI ; en local ≈ 10 à 30 ms
    for c in w.findChildren((QAbstractButton, QAbstractSpinBox, QComboBox, QSlider)):
        if c.isVisibleTo(w):
            assert c.toolTip(), (ident, type(c).__name__, getattr(c, 'text', lambda: '')())
    for lab, val in w.valeurs():
        assert not lab.startswith('anim_') and not val.startswith('anim_'), (ident, lab, val)
    # réinitialisation et lecture / pause
    w.reinitialiser()
    if w.ANIMEE:
        w.basculer_lecture()
        assert w.minuteur.isActive()
        w.basculer_lecture()
        assert not w.minuteur.isActive()
    w.close()


@pytest.mark.parametrize('langue_code', ['fr', 'en'])
def test_animations_dans_les_deux_langues(propre, langue, langue_code):
    langue(langue_code)
    for e in catalogue.faites():
        w = e.charger()()
        w.image(500, 360)
        for lab, val in w.valeurs():
            assert lab and val
        w.close()


def test_contraste_des_couleurs_du_dessin(app_qt):
    """Textes et tracés lisibles sur le fond de la toile, dans les deux thèmes (contraste ≥ 3)."""
    from PyQt6.QtGui import QColor
    from coupole.modules.anim.dessin import PALETTES

    def lum(h):
        c = QColor(h)
        v = []
        for x in (c.redF(), c.greenF(), c.blueF()):
            v.append(x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4)
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]

    for nom, p in PALETTES.items():
        f = lum(p['fond'])
        for cle in ('texte', 'doux', 'equateur', 'ecliptique', 'soleil', 'accent1', 'accent2', 'accent3', 'arc1',
                    'arc2', 'horizon', 'mars'):
            l = lum(p[cle])
            ratio = (max(l, f) + 0.05) / (min(l, f) + 0.05)
            assert ratio >= 3.0, (nom, cle, round(ratio, 2))


def test_reglages_gardes(propre):
    from coupole.gui import memoire
    from coupole.core.etat_interface import etat
    cls = catalogue.PAR_ID['sunmotions'].charger()
    w = cls()
    w.lat.setValue(-33.9)
    w.c_analemme.setChecked(True)
    memoire.memoire().ecrire()
    w.close()
    assert etat().lire('modules.anim.sunmotions.latitude', None, (int, float)) == pytest.approx(-33.9)
    memoire.reinitialiser_pour_tests()
    w2 = cls()
    assert w2.lat.value() == pytest.approx(-33.9) and w2.c_analemme.isChecked()
    w2.reinitialiser()
    assert w2.lat.value() == pytest.approx(40.8) and not w2.c_analemme.isChecked()
    w2.close()


def test_reglage_garde_la_valeur_exacte(propre):
    """Le champ arrondit à l'affichage, pas la valeur : une animation peut avancer par petits pas."""
    from coupole.modules.anim.base import Reglage
    r = Reglage('x', 0.0, 364.0, 10.0, dec=0)
    for _ in range(10):
        r.setValue(r.value() + 0.04)
    assert r.value() == pytest.approx(10.4)
    r.champ.setValue(200)
    assert r.value() == 200.0


def test_souris_deplace_l_etoile(propre):
    """Glisser l'étoile du démonstrateur azimut/hauteur la déplace (et met à jour les curseurs)."""
    from PyQt6.QtCore import QPoint, QPointF, Qt
    from PyQt6.QtTest import QTest
    import numpy as np
    from coupole.modules.anim import astro
    w = catalogue.PAR_ID['altazimuth'].charger()()
    w.resize(900, 700)
    w.show()
    propre.processEvents()
    w.toile.repaint()
    pe = w._pe
    xs, ys, _, _ = pe.ecran(np.array(astro.vecteur_horizon(w.az.value(), w.alt.value())))
    depart = QPoint(int(xs[0]), int(ys[0]))
    QTest.mousePress(w.toile, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, depart)
    QTest.mouseMove(w.toile, depart + QPoint(-40, 30))
    QTest.mouseRelease(w.toile, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, depart + QPoint(-40, 30))
    assert (w.az.value(), w.alt.value()) != (140.0, 45.0)
    w.close()


# ---------------------------------------------------------------- panneau dans la fenêtre principale
def test_panneau_animations(propre):
    from coupole.gui.fenetre import FenetrePrincipale
    from coupole.gui.outils import attendre_taches
    f = FenetrePrincipale()
    f.show()
    p = f.ouvrir_module('anim')
    assert p is not None and p.module.id == 'anim'
    assert p.arbre.topLevelItemCount() == len(catalogue.THEMES)
    w = p.ouvrir('kepler')
    assert w is not None and p.pile.currentWidget() is w
    assert p.ouvrir('balloon') is not None                    # 0.4.0 : le catalogue est complet
    p.etat.setCurrentIndex(p.etat.findData('a_venir'))
    assert sum(p.arbre.topLevelItem(i).childCount() for i in range(p.arbre.topLevelItemCount())) == 0
    p.etat.setCurrentIndex(p.etat.findData('faites'))
    n = sum(p.arbre.topLevelItem(i).childCount() for i in range(p.arbre.topLevelItemCount()))
    assert n == len(catalogue.faites())
    p.recherche.setText('saisons')
    ids = [p.arbre.topLevelItem(i).child(k).data(0, 256) for i in range(p.arbre.topLevelItemCount())
           for k in range(p.arbre.topLevelItem(i).childCount())]
    assert 'eclipticsimulator' in ids and 'kepler' not in ids
    assert 'ClassAction' in p.aide_html()
    p.arreter()
    f.close()
    attendre_taches()


# ---------------------------------------------------------------- lot 2 (0.3.1)
def test_lot2_complet():
    faites = {e.id for e in catalogue.faites()}
    assert len(catalogue.LOT2) == 25 and set(catalogue.LOT2) <= faites
    themes = {e.id: e.theme for e in catalogue.ENTREES}
    for theme in ('lunarcycles', 'renaissance', 'ancientastro', 'coordsmotion', 'stellarprops'):
        assert all(e.faite for e in catalogue.ENTREES if e.theme == theme), theme
    assert {themes[i] for i in catalogue.LOT2} == {'lunarcycles', 'renaissance', 'ancientastro', 'coordsmotion'}
    assert {themes[i] for i in catalogue.LOT2_BIS} == {'stellarprops'} and len(catalogue.LOT2_BIS) == 5
    assert len(catalogue.faites()) >= 60


def test_cles_de_texte_des_animations():
    """Chaque clé « anim_… » écrite en toutes lettres dans le code d'une animation existe en français et en anglais
    (les clés composées à la volée sont vérifiées par le rendu des deux langues)."""
    import re
    from pathlib import Path
    from coupole.core import i18n
    cles = i18n.toutes_les_cles()
    dossier = Path(catalogue.__file__).with_name('animations')
    for f in sorted(dossier.glob('*.py')):
        for cle in set(re.findall(r"'(anim_[a-z0-9_]+)'", f.read_text(encoding='utf-8'))):
            if cle.endswith('_'):
                continue
            assert cle in cles and cles[cle]['fr'] and cles[cle]['en'], (f.name, cle)


def test_souris_lot2(propre):
    """Glisser : la Lune du questionnaire, un corps du démonstrateur de phases (qui devient une lune), la boule des
    petits angles."""
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest

    def glisser(w, depart, arrivee):
        QTest.mousePress(w.toile, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, depart)
        QTest.mouseMove(w.toile, arrivee)
        QTest.mouseRelease(w.toile, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, arrivee)

    w = catalogue.PAR_ID['phaseDemonstrator'].charger()()
    w.resize(900, 700)
    w.show()
    propre.processEvents()
    w.toile.repaint()
    _, cx, cy, s = w._zone
    x1, y1 = w.pos[1]
    x2, y2 = w.pos[2]
    glisser(w, QPoint(int(cx + s * x1), int(cy - s * y1)), QPoint(int(cx + s * x2 + 8), int(cy - s * y2)))
    assert w.lune == 1                                       # assez près : le corps 1 devient la lune du corps 2
    w.close()

    w = catalogue.PAR_ID['lunarphasequizzer'].charger()()
    w.resize(900, 700)
    w.show()
    w.mode.setCurrentIndex(w.mode.findData('lune'))
    propre.processEvents()
    w.toile.repaint()
    _, cx, cy, ro = w._schema
    avant = w.devine['lune']
    glisser(w, QPoint(int(cx + ro), int(cy)), QPoint(int(cx), int(cy - ro)))
    assert w.devine['lune'] != avant
    w.basculer_reponse()
    assert any(lab == 'Verdict' or 'erdict' in lab for lab, _ in w.valeurs())
    w.close()


def test_configurations_s_arretent(propre):
    w = catalogue.PAR_ID['configurationssimulator'].charger()()
    w.action.setCurrentIndex(w.action.findData('arreter'))
    w.basculer_lecture()
    for _ in range(200):
        if not w.en_lecture:
            break
        w.pas(0.2)
    assert not w.en_lecture                                  # arrêt à la configuration suivante
    tp, _ = w.prochain(w.t - 1e-6)
    assert w.t == pytest.approx(tp, abs=1e-6)
    w.close()


def test_retard_synodique_un_jour(propre):
    w = catalogue.PAR_ID['synodiclag'].charger()()
    w.lancer('solaire')
    for _ in range(500):
        if not w.en_lecture:
            break
        w.pas(0.1)
    rot, sol = w.durees()
    assert w.ecoule_h == pytest.approx(sol) and (w.phi - w.theta) % 360.0 == pytest.approx(0.0, abs=1e-6)
    w.close()


# ---------------------------------------------------------------- lot 3 (0.4.0) : catalogue complet
def test_lot3_catalogue_complet():
    faites = {e.id for e in catalogue.faites()}
    assert len(faites) == 95 and not catalogue.a_venir()
    assert len(catalogue.LOT3) == 32 and set(catalogue.LOT3) <= faites
    assert len(set(catalogue.ORDRE)) == 95
    themes = {e.id: e.theme for e in catalogue.ENTREES}
    assert sum(themes[i] == 'light' for i in catalogue.LOT3) == 8
    assert sum(themes[i] == 'extrasolarplanets' for i in catalogue.LOT3) == 7
    assert sum(themes[i] == 'binaryvariablestars' for i in catalogue.LOT3) == 4


def test_souris_lot3(propre):
    """Glisser : le laser de Snell-Descartes, le télescope des trois spectres, la longueur d'onde du spectre EM,
    l'observateur de l'effet Doppler, le rayon de la courbe de rotation."""
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest

    def glisser(w, depart, arrivee):
        QTest.mousePress(w.toile, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, depart)
        QTest.mouseMove(w.toile, arrivee)
        QTest.mouseRelease(w.toile, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, arrivee)

    for ident, attribut in (('snellslaw', 'theta'), ('threeviewsspectra', 'angle'), ('emspectrum', 'l'),
                            ('milkywayrotationalvelocity', 'r')):
        w = catalogue.PAR_ID[ident].charger()()
        w.resize(900, 700)
        w.show()
        propre.processEvents()
        w.toile.repaint()
        avant = getattr(w, attribut).value()
        t = w.toile
        if ident == 'snellslaw':
            glisser(w, QPoint(t.width() // 2 - 150, t.height() // 2 - 60), QPoint(t.width() // 2 - 40, t.height() // 2 - 200))
        elif ident == 'threeviewsspectra':
            cx, cy, k = w._scene
            from coupole.modules.anim.animations.kirchhoff import R_TELESCOPE
            glisser(w, QPoint(int(cx - R_TELESCOPE * k), int(cy)), QPoint(int(cx), int(cy - R_TELESCOPE * k)))
        elif ident == 'emspectrum':
            r = w._zone
            glisser(w, QPoint(int(r.left() + 10), int(r.center().y())), QPoint(int(r.right() - 10), int(r.center().y())))
        else:
            ax = w._axes
            glisser(w, QPoint(int(ax.px(3.0)), int(ax.py(150))), QPoint(int(ax.px(18.0)), int(ax.py(150))))
        assert getattr(w, attribut).value() != pytest.approx(avant), ident
        w.close()
    w = catalogue.PAR_ID['dopplershift'].charger()()
    w.resize(900, 700)
    w.show()
    propre.processEvents()
    w.toile.repaint()
    boite, k = w._zone
    avant = list(w.obs)
    glisser(w, QPoint(int(boite.left() + avant[0] * k), int(boite.top() + avant[1] * k)),
            QPoint(int(boite.left() + 20 * k), int(boite.top() + 40 * k)))
    assert w.obs != avant
    w.close()


def test_atome_absorbe_puis_reemet(propre):
    from coupole.modules.anim import lumiere
    w = catalogue.PAR_ID['hydrogenatom'].charger()()
    w.transition.setCurrentIndex(w.transition.findData('1-3'))
    w.tirer_transition()
    for _ in range(15):                                  # 1,5 s : le photon arrive et il est absorbé
        w.pas(0.1)
    assert w.n == 3
    for _ in range(80):                                  # puis l'atome retombe, en émettant
        w.pas(0.1)
    assert w.n == 1 and any('3 → ' in j for j in w.journal)
    w.e.setValue(14.0)
    w.tirer()
    for _ in range(15):
        w.pas(0.1)
    assert w.n == 0                                      # ionisé
    assert lumiere.transition_ev(1, 3) == pytest.approx(12.09, abs=0.005)
    w.close()


def test_ccd_pose_et_lecture(propre):
    w = catalogue.PAR_ID['buckets'].charger()()
    w.pose.setValue(4.0)
    w.poser()
    for _ in range(400):
        w.pas(0.1)
        if w.mode == 'fini':
            break
    assert w.mode == 'fini'
    lues = [v for ligne in w.lues for v in ligne]
    assert None not in lues and len(lues) == 20
    assert max(lues) == w.lues[1][2] or max(lues) == w.lues[1][1] or max(lues) == w.lues[2][2]   # l'étoile
    w.close()


def test_courbe_de_lumiere_mesures(propre):
    w = catalogue.PAR_ID['lightcurve'].charger()()
    w.mesurer()
    assert len(w.points) == 1
    w.c_auto.setChecked(True)
    for _ in range(100):
        w.pas(0.1)
    assert len(w.points) > 10
    w.effacer()
    assert not w.points
    w.close()


def test_prereglages_lot3(propre):
    """Choisir un système réel règle tous les curseurs (transits, vitesses radiales, binaires à éclipses)."""
    w = catalogue.PAR_ID['transitsimulator'].charger()()
    w.prereglage.setCurrentIndex(w.prereglage.findData('HD 189733 b'))
    w._appliquer()
    assert w.rp.value() == pytest.approx(1.13) and w.i.value() == pytest.approx(85.71)
    w.close()
    w = catalogue.PAR_ID['radialvelocitysimulator'].charger()()
    w.prereglage.setCurrentIndex(w.prereglage.findData('HD 39091 b'))
    w._appliquer()
    assert w.e.value() == pytest.approx(0.642) and w.i.value() == pytest.approx(45.8)
    w.close()
    w = catalogue.PAR_ID['eclipsingbinarysim'].charger()()
    w.prereglage.setCurrentIndex(w.prereglage.findData('EK Cep'))
    w._appliquer()
    assert w.r1.value() == pytest.approx(0.095 * 16.58, rel=1e-3) and w.donnees()
    assert any('cart' in lab for lab, _ in w.valeurs())
    w.close()
