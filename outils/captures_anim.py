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
          'transitmovie', 'hrexplorer',
          # lot 3 (0.4.0)
          'bbexplorer', 'hydrogenatom', 'threeviewsspectra', 'transitsimulator', 'ca_extrasolarplanets_starwobble',
          'eclipsingbinarysim', 'galacticredshift', 'milkywayrotationalvelocity', 'telescope10', 'fusion02',
          # 0.4.1 : formules, étiquettes, sphères
          'gravcalc', 'hammerthrower', 'bigdipper')
# 0.4.1 : variantes (nom du fichier, identifiant, réglages)
VARIANTES = (('daylightsimulator_nord', 'daylightsimulator', {'projection': 'nord', 'crepuscule': True}),
             ('daylightsimulator_globe', 'daylightsimulator', {'projection': 'globe', 'crepuscule': True}),
             ('shadowsim_rejeu', 'shadowsim', {'rejouer': 'S20', 'instant': 0.15}),
             # 0.4.2 : la machine d'Anticythère (fermée, face avant et arrière ; ouverte et éclatée)
             ('antikythera_avant', 'antikythera', {}),
             ('antikythera_arriere', 'antikythera', {'face': 'arriere'}),
             ('antikythera_ouverte', 'antikythera', {'enveloppe': False, 'face': 'trois_quarts', 'eclatement': 60}))


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
        elif ident == 'bbexplorer':                     # trois courbes et les filtres
            for t in (4000.0, 9000.0):
                a._ajouter()
                a.t.setValue(t)
            a.c_filtres.setChecked(True)
        elif ident == 'eclipsingbinarysim':             # un système réel et sa courbe observée
            a.prereglage.setCurrentIndex(a.prereglage.findData('EK Cep'))
            a._appliquer()
        elif ident == 'hydrogenatom':                   # un photon de Lyman β vient d'être absorbé
            a.transition.setCurrentIndex(a.transition.findData('1-3'))
            a.tirer_transition()
            for _ in range(13):
                a.pas(0.1)
        elif ident == 'galacticredshift':
            a.z.setValue(0.3)
        elif ident == 'transitsimulator':
            a.prereglage.setCurrentIndex(a.prereglage.findData('HD 209458 b'))
            a._appliquer()
        a.resize(1100, 760)
        a.show()
        if ident != 'hydrogenatom':
            for _ in range(12):
                a.pas(0.1)
        attendre(app, 0.2)
        a.grab().save(str(dossier / ('anim_%s_%s.png' % (ident.lower(), langue))))
        a.close()
    for nom, ident, reglages in VARIANTES:
        a = catalogue.PAR_ID[ident].charger()()
        for cle, v in reglages.items():
            w = a._defauts[cle][0]
            if hasattr(w, 'findData'):
                w.setCurrentIndex(w.findData(v))
            elif hasattr(w, 'setChecked'):
                w.setChecked(v)
            else:
                w.setValue(v)
        if ident == 'daylightsimulator':
            a.jour.setValue(172.0)
            a.heure.setValue(15.5)
            if reglages.get('projection') == 'globe':
                a.recentrer()
                a.tourner_globe(-140, 110, 250)
        a.resize(1100, 760)
        a.show()
        attendre(app, 0.2)
        a.grab().save(str(dossier / ('anim_%s_%s.png' % (nom, langue))))
        a.close()
    f.close()


if __name__ == '__main__':
    main()
