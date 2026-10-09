"""Démarrage de l'interface graphique."""
from __future__ import annotations

import logging
import os
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
    try:
        import logging.handlers
        h = logging.handlers.RotatingFileHandler(str(journal), maxBytes=2_000_000, backupCount=2, encoding='utf-8')
        h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
        logging.getLogger().addHandler(h)
        logging.getLogger().setLevel(logging.INFO)
    except OSError:                              # dossier en lecture seule : l'application démarre quand même
        logging.basicConfig(level=logging.WARNING)
    rapports.init()
    rapports.installer_crochets(config.dossier_config() / '_crash_natif.log')
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QGuiApplication
    if QApplication.instance() is None:     # mise à l'échelle fractionnaire exacte (125 %, 150 %…) sans arrondi
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('Coupole')
    app.setOrganizationName('Coupole')
    if sys.platform.startswith('linux'):        # relie la fenêtre à coupole.desktop (icône, regroupement du dock)
        app.setDesktopFileName('coupole')
    if sys.platform == 'win32':                 # verrou interrogé par l'installeur (AppMutex)
        try:
            import ctypes
            app._mutex_installeur = ctypes.windll.kernel32.CreateMutexW(None, False, 'CoupoleEnCours')
        except Exception:
            pass
    from . import fil_graphique, theme
    # objets Qt détruits dans le fil graphique seulement (ramasse-miettes cyclique de Python, 0.1.7)
    fil_graphique.installer_ramasse_miettes(app)
    if os.environ.get('COUPOLE_GARDE_FIL'):
        fil_graphique.installer_garde()
    theme.appliquer(app)
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
        from .outils import lancer_fil
        # sondes matérielles (PowerShell sous Windows : plusieurs secondes) et rapport de démarrage : hors du
        # fil graphique, jamais au prix d'un gel au lancement
        lancer_fil(lambda: (machine.detecter(), rapports.signaler_demarrage()))
        rapports.reprendre_file_en_fond()
        from ..core import sources
        sources.rafraichir_en_fond()            # fichier de sources publié : repli silencieux
        if config.reglages()['maj_auto']:
            verifier_maj(f, silencieux=True)
    from ..core import machine
    QTimer.singleShot(300, apres_affichage)
    from .outils import arreter_tout
    app.aboutToQuit.connect(lambda: (vigie.arreter(), arreter_tout()))
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
