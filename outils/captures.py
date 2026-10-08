"""Captures d'écran de l'interface (pour le manuel et les tests visuels), sans écran :

    QT_QPA_PLATFORM=offscreen python outils/captures.py fr docs/manuel/img
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def attendre(app, condition, delai=30.0):
    t0 = time.time()
    while not condition() and time.time() - t0 < delai:
        app.processEvents()
        time.sleep(0.02)


def main():
    langue = sys.argv[1] if len(sys.argv) > 1 else 'fr'
    dossier = Path(sys.argv[2] if len(sys.argv) > 2 else 'captures')
    dossier.mkdir(parents=True, exist_ok=True)
    from PyQt6.QtWidgets import QApplication
    from coupole.cli import initialiser
    from coupole.core import config, rapports
    config.reglages()['rapports_autorises'] = False
    config.reglages()['maj_auto'] = False
    initialiser(langue)
    rapports.init()
    app = QApplication(sys.argv)
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.resize(1400, 860)
    f.show()
    ohp = f.panneaux[0]
    attendre(app, lambda: ohp.inv is not None)
    # sélection : NGC 6888 (exemple du manuel)
    for r, o in enumerate(ohp.m_obj.donnees):
        if o['objet'] == 'NGC 6888':
            idx = ohp.p_obj.mapFromSource(ohp.m_obj.index(r, 0))
            ohp.v_obj.selectRow(idx.row())
            ohp.v_obj.scrollTo(idx)
    attendre(app, lambda: False, 0.5)
    ohp.f_nuit.setCurrentIndex(max(0, ohp.f_nuit.findData('2025-07-16')))
    attendre(app, lambda: False, 0.5)

    def capture(nom):
        attendre(app, lambda: False, 0.4)
        f.grab().save(str(dossier / ('%s_%s.png' % (nom, langue))))

    capture('catalogue')
    ohp.vers_traitement()
    capture('traitement')
    ohp.onglets.setCurrentIndex(3)
    attendre(app, lambda: ohp.m_anom.rowCount() > 0, 20)
    capture('anomalies')
    ohp.onglets.setCurrentIndex(2)
    capture('lots')
    for i, p in enumerate(f.panneaux):
        mid = getattr(getattr(p, 'module', None), 'id', '')
        if mid and mid != 'ohp':
            f.barre.setCurrentRow(i)
            attendre(app, lambda: False, 1.5)
            capture('module_' + mid)
    from coupole.gui import dialogues
    for nom, classe in (('astap', dialogues.DialogueASTAP), ('apropos', dialogues.DialogueAPropos),
                        ('reglages', dialogues.DialogueReglages)):
        d = classe(f)
        d.show()
        attendre(app, lambda: False, 0.5)
        d.grab().save(str(dossier / ('%s_%s.png' % (nom, langue))))
        d.close()
    print('captures dans', dossier)


if __name__ == '__main__':
    main()
