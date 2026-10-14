"""Captures du module « Animations » pour le manuel, sans écran :

    QT_QPA_PLATFORM=offscreen python outils/captures_anim.py fr docs/manuel/img

Produit module_anim_<langue>.png (fenêtre principale, catalogue et une animation) et anim_<id>_<langue>.png (rendu
de quelques animations).  Dossier personnel neutre, comme outils/captures.py."""
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
DOSSIER_NEUTRE = os.path.join(tempfile.gettempdir(), 'utilisateur')
os.makedirs(DOSSIER_NEUTRE, exist_ok=True)
os.environ['HOME'] = DOSSIER_NEUTRE
os.environ['COUPOLE_HOME'] = tempfile.mkdtemp(prefix='coupole-captures-')

RENDUS = ('eclipticsimulator', 'lunar_applet', 'shadowsim', 'celhorcomp', 'kepler', 'marsorbit', 'longlat',
          'eclipsetable', 'mooninc', 'tidesim', 'venusphases', 'configurationssimulator', 'heliacalrisingsim',
          'transitmovie', 'hrexplorer')


def attendre(app, s):
    t0 = time.time()
    while time.time() - t0 < s:
        app.processEvents()
        time.sleep(0.02)


def main():
    langue = sys.argv[1] if len(sys.argv) > 1 else 'fr'
    dossier = Path(sys.argv[2] if len(sys.argv) > 2 else 'captures')
    dossier.mkdir(parents=True, exist_ok=True)
    from PyQt6.QtWidgets import QApplication
    from coupole.cli import initialiser
    from coupole.core import config
    config.reglages()['rapports_autorises'] = False
    config.reglages()['maj_auto'] = False
    initialiser(langue)
    app = QApplication(sys.argv)
    from coupole.gui import theme
    theme.appliquer(app)
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.resize(1400, 900)
    f.show()
    p = f.ouvrir_module('anim')
    w = p.ouvrir('sunmotions')
    w.c_analemme.setChecked(True)
    w.heure.setValue(15.0)
    attendre(app, 1.0)
    f.grab().save(str(dossier / ('module_anim_%s.png' % langue)))
    from coupole.modules.anim import catalogue
    for ident in RENDUS:
        a = catalogue.PAR_ID[ident].charger()()
        if ident == 'hrexplorer':                       # montrer les étoiles proches et brillantes
            a.groupe.setCurrentIndex(a.groupe.findData('les_deux'))
        a.resize(1100, 760)
        a.show()
        for _ in range(12):
            a.pas(0.1)
        attendre(app, 0.2)
        a.grab().save(str(dossier / ('anim_%s_%s.png' % (ident.lower(), langue))))
        a.close()
    f.close()


if __name__ == '__main__':
    main()
