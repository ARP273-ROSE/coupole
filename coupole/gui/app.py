"""Démarrage de l'interface graphique."""
from __future__ import annotations

import logging
import sys
import time

T0 = time.perf_counter()


def main() -> int:
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication

    from ..cli import initialiser
    from ..core import config, rapports
    initialiser()
    journal = config.dossier_config() / 'coupole.log'
    logging.basicConfig(filename=str(journal), level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    rapports.init()
    rapports.installer_crochets(config.dossier_config() / '_crash_natif.log')
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('Coupole')
    app.setOrganizationName('Coupole')
    if sys.platform == 'win32':                 # verrou interrogé par l'installeur (AppMutex)
        try:
            import ctypes
            app._mutex_installeur = ctypes.windll.kernel32.CreateMutexW(None, False, 'CoupoleEnCours')
        except Exception:
            pass
    from .dialogues import demander_consentement_si_besoin, verifier_maj
    from .fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.show()
    logging.getLogger(__name__).info('window shown after %.2f s', time.perf_counter() - T0)
    vigie = rapports.Vigie()
    battement = QTimer(f)
    battement.timeout.connect(vigie.battre)
    battement.start(1000)
    vigie.demarrer()

    def apres_affichage():
        demander_consentement_si_besoin(f)
        rapports.signaler_demarrage()
        rapports.reprendre_file_en_fond()
        if config.reglages()['maj_auto']:
            verifier_maj(f, silencieux=True)
    QTimer.singleShot(300, apres_affichage)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
