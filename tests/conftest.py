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

# Traitement de référence (dépôt de l'auteur) : utilisé quand il est présent, sinon les tests concernés sont sautés.
REFERENCE = Path(os.environ.get('COUPOLE_REFERENCE',
                                '/workspace/GitHub/_docs/Observatoire-Paris/Banque-Images-OHP'))


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
    from coupole.gui import theme
    theme.appliquer(app)                        # le thème par défaut de Coupole (sombre), comme chez l'utilisateur
    yield app


@pytest.fixture(autouse=True)
def interface_vierge():
    """Chaque test part d'une disposition d'origine (interface.json effacé) : la fenêtre d'un test ne reprend pas
    la taille, les filtres ou les colonnes laissés par le précédent."""
    from coupole.core import etat_interface
    etat_interface.effacer_fichier()
    etat_interface.reinitialiser_pour_tests()
    yield
