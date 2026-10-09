"""Rendu net aux écrans denses (carte OSM : tuiles du niveau z + 1 à partir de 1,5×), curseur de redshift du module
Cosmologie (synchronisation champ ↔ curseur, interpolation pendant le glissement, calcul exact au relâchement),
courbes qui suivent le redimensionnement de la fenêtre."""
import time

import numpy as np
import pytest

pytest.importorskip('PyQt6')
from PyQt6.QtCore import QEvent, QObject, Qt  # noqa: E402
from PyQt6.QtGui import QImage  # noqa: E402


def attendre(app, condition, delai=30):
    t0 = time.time()
    while not condition() and time.time() - t0 < delai:
        app.processEvents()
        time.sleep(0.02)
    return condition()


# ---------------------------------------------------------------- carte du monde : tuiles fines
def _carte_avec_cache_simule(dpr):
    from coupole.gui.cartes import CarteMonde
    carte = CarteMonde(en_ligne=True)
    carte.resize(600, 400)
    cles = []
    im = QImage(256, 256, QImage.Format.Format_RGB32)
    im.fill(Qt.GlobalColor.gray)

    def tuile(z, x, y):
        cles.append((z, x, y))
        return im
    carte.cache.tuile = tuile
    carte.devicePixelRatioF = lambda: dpr
    carte.centrer(2.76, 49.31, 5)
    return carte, cles


@pytest.mark.parametrize('dpr, zoom_attendu, par_tuile', [(1.0, 5, 1), (1.5, 6, 4), (2.0, 6, 4)])
def test_tuiles_du_niveau_superieur_sur_ecran_dense(app_qt, dpr, zoom_attendu, par_tuile):
    """À 1× : tuiles du niveau z. À ≥ 1,5× : tuiles du niveau z + 1, quatre par tuile logique (rendu « @2x »)."""
    carte, cles = _carte_avec_cache_simule(dpr)
    assert carte._zoom_tuiles() == (zoom_attendu, 2 if par_tuile == 4 else 1)
    carte.grab()
    assert cles and all(c[0] == zoom_attendu for c in cles)
    carte1, cles1 = _carte_avec_cache_simule(1.0)
    carte1.grab()
    assert len(cles) == par_tuile * len(cles1)              # même emprise, quatre fois plus de tuiles à 2×
    carte.cache.fermer()
    carte1.cache.fermer()


def test_zoom_maximal_reste_servi(app_qt):
    from coupole.gui import cartes
    carte, cles = _carte_avec_cache_simule(2.0)
    carte.z = cartes.ZOOM_MAX
    assert carte._zoom_tuiles() == (cartes.ZOOM_MAX, 1)     # pas de niveau z + 1 : tuiles ordinaires
    carte.cache.fermer()


# ---------------------------------------------------------------- cosmologie : curseur et redimensionnement
@pytest.fixture(scope='module')
def fenetre(app_qt):
    from coupole.core import config
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.resize(1024, 700)
    f.show()
    yield f
    f.close()
    from coupole.gui.outils import attendre_taches
    attendre_taches()


def test_curseur_de_redshift(app_qt, fenetre):
    from coupole.modules.cosmo import calcul, formats
    from coupole.modules.cosmo.gui import CURSEUR_MAX, curseur_du_z, z_du_curseur
    p = fenetre.ouvrir_module('cosmo')
    assert attendre(app_qt, lambda: p.resultat is not None and p.courbes is not None, 60)
    # correspondance curseur ↔ z : repères aux décades, bornes
    assert z_du_curseur(0) == pytest.approx(0.001) and z_du_curseur(CURSEUR_MAX) == pytest.approx(1100, rel=1e-3)
    assert curseur_du_z(1.0) == 3000 and curseur_du_z(10.0) == 4000 and z_du_curseur(3000) == pytest.approx(1.0)
    # le champ z place le curseur
    p.definir_z(2.34)
    assert attendre(app_qt, lambda: p.resultat is not None and abs(p.resultat['z'] - 2.34) < 1e-9, 60)
    assert p.curseur.value() == curseur_du_z(2.34)
    # glissement : champ, marqueur et tableau suivent par interpolation, sans calcul
    tache_avant = p._tache
    p.curseur.setSliderDown(True)
    p.curseur.setValue(curseur_du_z(0.5))
    app_qt.processEvents()
    assert p.z.text() == formats.court(z_du_curseur(curseur_du_z(0.5)))
    assert p.trace.marqueur == pytest.approx(z_du_curseur(curseur_du_z(0.5)))
    assert p._tache is tache_avant                           # aucun recalcul pendant le glissement
    assert 'interpol' in p.l_etat.text()
    ligne_dc = next(l for l, k in zip(p.m_res.lignes, p.m_res.donnees) if k == 'comoving')
    exact = calcul.calculer(z_du_curseur(curseur_du_z(0.5)), incertitudes=False)
    interp = calcul.interpoler(p.courbes, z_du_curseur(curseur_du_z(0.5)))
    assert ligne_dc[1] == formats.valeur('comoving', interp['comoving'])
    assert abs(interp['comoving'] / exact['comoving'] - 1) < 2e-3   # la grille de 300 points est fine
    # relâchement : calcul exact (au z affiché dans le champ, 6 chiffres), cohérent à 1e-6
    z_champ = calcul.verifier_z(p.z.text())
    exact = calcul.calculer(z_champ, incertitudes=False)
    p.curseur.setSliderDown(False)
    p.curseur.sliderReleased.emit()
    assert attendre(app_qt, lambda: p.resultat is not None and 'interpol' not in p.l_etat.text()
                    and abs(p.resultat['z'] - z_champ) < 1e-12, 60)
    for k, _ in calcul.GRANDEURS:
        assert abs(p.resultat[k] - exact[k]) <= 1e-6 * max(1.0, abs(exact[k])), k
    ligne_dc = next(l for l, k in zip(p.m_res.lignes, p.m_res.donnees) if k == 'comoving')
    assert ligne_dc[1] == formats.valeur('comoving', exact['comoving'])
    # flèche du clavier (pas fin, curseur non enfoncé) : calcul exact direct
    v0 = p.curseur.value()
    p.curseur.triggerAction(p.curseur.SliderAction.SliderSingleStepAdd)
    assert p.curseur.value() == v0 + 10
    assert p.z.text() == formats.court(z_du_curseur(v0 + 10))
    z_champ = calcul.verifier_z(p.z.text())
    assert attendre(app_qt, lambda: p.resultat is not None and abs(p.resultat['z'] - z_champ) < 1e-12, 60)


def test_interpolation_sur_la_grille(inventaire=None):
    """`interpoler` retrouve les valeurs de la grille elle-même et reste proche du calcul exact entre deux points."""
    from coupole.modules.cosmo import calcul
    c = calcul.courbes(calcul.grille_z())
    for k, _ in calcul.GRANDEURS:
        assert k in c and len(c[k]) == len(c['z'])
    i = 120
    d = calcul.interpoler(c, float(c['z'][i]))
    for k, _ in calcul.GRANDEURS:
        if np.isfinite(c[k][i]):
            assert abs(d[k] - c[k][i]) <= 1e-9 * max(1.0, abs(c[k][i])), k
    z = float(np.sqrt(c['z'][i] * c['z'][i + 1]))           # entre deux points
    d, e = calcul.interpoler(c, z), calcul.calculer(z, incertitudes=False)
    for k in ('comoving', 'luminosity', 'angular_diameter', 'lookback_gyr', 'age_at_z', 'distmod', 'vol_gpc3', 'H_z'):
        assert abs(d[k] / e[k] - 1) < 5e-3, k


class _CompteurPaint(QObject):
    def __init__(self):
        super().__init__()
        self.n = 0

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Type.Paint:
            self.n += 1
        return False


def test_les_courbes_suivent_la_fenetre(app_qt, fenetre):
    """1024 → 1800 px : la largeur du widget de courbes change et il est redessiné, dans les deux dispositions
    (courbes sous le tableau sous 1500 px, à côté au-dessus)."""
    p = fenetre.ouvrir_module('cosmo')
    assert attendre(app_qt, lambda: p.resultat is not None and p.courbes is not None, 60)
    compteur = _CompteurPaint()
    p.trace.installEventFilter(compteur)
    fenetre.resize(1024, 700)
    app_qt.processEvents()
    attendre(app_qt, lambda: False, 0.3)
    l1, h1 = p.trace.width(), p.trace.height()
    assert p.splitter.orientation() == Qt.Orientation.Vertical
    n1 = compteur.n
    fenetre.resize(1800, 1000)
    app_qt.processEvents()
    attendre(app_qt, lambda: p.trace.width() > l1 + 200, 5)
    assert p.trace.width() > l1 + 200
    from coupole.modules.cosmo.gui import LARGEUR_COTE_A_COTE
    if p.width() >= LARGEUR_COTE_A_COTE:                      # l'écran virtuel de certains serveurs de CI est plus étroit
        assert p.splitter.orientation() == Qt.Orientation.Horizontal
    assert compteur.n > n1                                    # un nouveau paint a eu lieu
    # sous 1500 px, les courbes grandissent avec la hauteur de la fenêtre au lieu de rester figées à leur minimum
    fenetre.resize(1200, 600)
    app_qt.processEvents()
    attendre(app_qt, lambda: p.splitter.orientation() == Qt.Orientation.Vertical, 5)
    h_bas = p.trace.height()
    fenetre.resize(1200, 1000)
    app_qt.processEvents()
    attendre(app_qt, lambda: p.trace.height() > h_bas + 30, 5)
    assert p.trace.height() > h_bas + 30
    p.trace.removeEventFilter(compteur)
