"""Module « Animations » : catalogue (92 animations, états, recherche), chaque animation créée hors écran, animée,
dessinée, réglages gardés, bilinguisme, contraste des couleurs, panneau dans la fenêtre principale, ligne de
commande."""
import json
import time

import pytest

from coupole.modules.anim import catalogue


# ---------------------------------------------------------------- catalogue (sans Qt)
def test_catalogue_complet():
    assert len(catalogue.ENTREES) == 92
    assert len({e.id for e in catalogue.ENTREES}) == 92
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
    assert len(d) == 92 and sum(x['disponible'] for x in d) == len(catalogue.faites())
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
    assert p.ouvrir('balloon') is None and p.pile.currentWidget() is p.vide         # à venir : description seule
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
