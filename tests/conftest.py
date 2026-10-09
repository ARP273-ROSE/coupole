"""Configuration commune des tests : dossier de réglages jetable, Qt sans écran, chemins de référence."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['COUPOLE_HOME'] = tempfile.mkdtemp(prefix='coupole-tests-')
os.environ['COUPOLE_SANS_RESEAU'] = '1'      # jamais de requête publique depuis les tests (serveur local seulement)

# Traitement de référence (scripts d'origine) : dossier donné par COUPOLE_REFERENCE ; sinon les tests concernés sont
# sautés.
REFERENCE = Path(os.environ.get('COUPOLE_REFERENCE') or os.devnull)


@pytest.fixture(scope='session', autouse=True)
def textes():
    from coupole.cli import initialiser
    initialiser('fr')
    yield


@pytest.fixture
def langue():
    from coupole.core import i18n

    def choisir(l):
        i18n.choisir_langue(l)
    yield choisir
    i18n.choisir_langue('fr')


@pytest.fixture(scope='session')
def reference():
    if not (REFERENCE / 'traitement' / 'journal.csv').exists():
        pytest.skip('traitement de référence absent (COUPOLE_REFERENCE)')
    return REFERENCE


@pytest.fixture(scope='session')
def inventaire():
    from coupole.modules.ohp.inventaire import Inventaire
    return Inventaire.charger()


@pytest.fixture(scope='session')
def app_qt():
    pytest.importorskip('PyQt6')
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from coupole.gui import fil_graphique, theme
    fil_graphique.installer_ramasse_miettes(app)   # comme l'application : objets Qt détruits dans le fil graphique
    fil_graphique.installer_garde()             # appel d'affichage hors du fil graphique → échec du test
    theme.appliquer(app)                        # le thème par défaut de Coupole (sombre), comme chez l'utilisateur
    yield app


@pytest.fixture(autouse=True)
def garde_fil_graphique(request):
    """Garde permanente (0.1.7) : un test échoue si, pendant qu'il tournait, une méthode d'affichage a été appelée
    hors du fil graphique, si Qt a signalé un objet manipulé depuis un autre fil, ou si le ramasse-miettes cyclique
    a tourné hors du fil graphique (il y détruirait des widgets : cause du plantage natif de la 0.1.6).
    Les fenêtres laissées par le test sont ramassées ici, dans le fil graphique, avant le test suivant."""
    from coupole.gui import fil_graphique
    fil_graphique.vider_violations()
    yield
    if 'PyQt6.QtWidgets' in sys.modules:
        from PyQt6.QtWidgets import QApplication
        if QApplication.instance() is not None:
            import gc
            gc.collect()
    v = fil_graphique.vider_violations()
    assert not v, 'Qt/GUI thread violations:\n' + '\n'.join(v[:20])


@pytest.fixture(autouse=True)
def interface_vierge():
    """Chaque test part d'une disposition d'origine (interface.json effacé) : la fenêtre d'un test ne reprend pas
    la taille, les filtres ou les colonnes laissés par le précédent."""
    from coupole.core import etat_interface, i18n
    etat_interface.effacer_fichier()
    etat_interface.reinitialiser_pour_tests()
    i18n.choisir_langue('fr')        # en ordre aléatoire, un test de la CLI (`--lang en`) laissait l'anglais au suivant
    yield
