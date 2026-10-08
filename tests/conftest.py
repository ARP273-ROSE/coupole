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
    yield app
