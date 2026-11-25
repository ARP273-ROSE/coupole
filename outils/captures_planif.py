"""Captures d'écran du « Planificateur de parallaxe » pour les manuels (exemple Paris–Lyon, TLE figé du 25/11/2026,
aucune requête vers l'extérieur).

    QT_QPA_PLATFORM=offscreen python outils/captures_planif.py fr docs/manuel/img
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['COUPOLE_HOME'] = tempfile.mkdtemp(prefix='coupole-captures-')
os.environ['COUPOLE_SANS_RESEAU'] = '1'
os.environ['COUPOLE_SANS_DIALOGUE'] = '1'

TLE = ('1 25544U 98067A   26329.13827943  .00005490  00000-0  10559-3 0  9990',
       '2 25544  51.6318 223.5847 0007441  62.8824 297.2922 15.49581740596707')


def attendre(app, cond, delai=120):
    fin = time.time() + delai
    while not cond() and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)


def main(langue: str, dossier: str):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(['coupole'])
    from coupole.cli import initialiser
    initialiser(langue)
    from coupole.gui import theme
    theme.appliquer(app)
    from coupole.modules.td import tle
    tle.garder(TLE)
    sortie = Path(dossier)
    sortie.mkdir(parents=True, exist_ok=True)
    from coupole.modules.td.gui import Panneau
    t = Panneau()
    t.resize(1500, 900)
    t.show()
    t.liste.setCurrentRow(1)
    p = t.planif
    p.exemple()
    p.e_debut.setText('2026-11-25')
    for cible, jours in (('iss', 7.0), ('lune', 45.0)):
        p.res = None
        p.c_cible.setCurrentIndex(p.c_cible.findData(cible))
        p.s_jours.setValue(jours)
        p.chercher()
        attendre(app, lambda: p.res is not None and p.b_chercher.isEnabled())
        attendre(app, lambda: False, 0.5)
        t.grab().save(str(sortie / ('td_planif_%s_%s.png' % (cible, langue))))
    t.close()
    print('captures dans', sortie)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
