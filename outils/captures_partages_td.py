"""Captures d'écran des manuels pour la 0.8.0 : « Partages du DU » (partage FICTIF servi en local par le serveur WebDAV
des essais) et « Calculateurs de TD » (exemples fictifs).  Aucune donnée réelle, aucune requête vers l'extérieur.

    QT_QPA_PLATFORM=offscreen python outils/captures_partages_td.py fr docs/manuel/img
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


def attendre(app, cond, delai=60):
    fin = time.time() + delai
    while not cond() and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)


def main(langue: str, dossier: str):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(['coupole'])
    from coupole.cli import initialiser
    initialiser(langue)
    from coupole.gui import memoire, theme
    theme.appliquer(app)
    from tests import partages_exemple as X
    from tests.serveur_webdav import ServeurWebdav
    sortie = Path(dossier)
    sortie.mkdir(parents=True, exist_ok=True)
    fa, _ = X.fits_lune(X.PARIS, X.T_LUNE, 'Observateur A')
    fb, _ = X.fits_lune(X.MARSEILLE, X.T_LUNE, 'Observateur B')
    s = ServeurWebdav({'2025/2025-11-03-18-38-26-A.fits': fa, '2025/2025-11-03-18-38-26-B.fits': fb,
                       '2025/localisations.xlsx': X.classeur(X.lignes_mesures()),
                       '17 Octobre 2026/ISS-26-10-17-04-29-11.204-ABC.png': b'\x89PNG\r\n\x1a\n',
                       'Lisez-moi.txt': b'Deposez vos images ici.'})
    memoire.retenir('modules.partages.sortie', tempfile.mkdtemp(prefix='coupole-sortie-'))
    from coupole.modules.partages.gui import Panneau
    p = Panneau()
    p.resize(1360, 820)
    p.show()
    p.ajouter_partage_direct('Défi parallaxe (exemple)' if langue == 'fr' else 'Parallax challenge (example)', s.lien)
    attendre(app, lambda: p.session is not None and p.session.structure is not None and p.arbre.topLevelItemCount())
    p._choisir_noeud(('dossier', '2025'))
    p.vue.selectRow(0)
    attendre(app, lambda: False, 1.5)
    p.grab().save(str(sortie / ('partages_contenu_%s.png' % langue)))
    p.ouvrir_tableau('2025/localisations.xlsx')
    attendre(app, lambda: p.modele_m.rowCount() == 5)
    p.grab().save(str(sortie / ('partages_mesures_%s.png' % langue)))
    fits_ = [f for f in p.session.structure.fichiers if f.genre == 'fits']
    p.telecharger(fits_)
    attendre(app, lambda: not p.occupe() and len(p.possedes) == 2)
    o = p.outil_panneau
    o.chercher_paires()
    o.c_cible.setCurrentIndex(o.c_cible.findData('lune'))
    o.mesurer(o.a, [fits_[0]])
    o.mesurer(o.b, [fits_[1]])
    attendre(app, lambda: o.a.t_points.rowCount() == 1 and o.b.t_points.rowCount() == 1)
    o.calculer()
    attendre(app, lambda: o.resultat is not None)
    p.onglets.setCurrentIndex(2)
    from PyQt6.QtWidgets import QScrollArea
    attendre(app, lambda: False, 0.3)
    for sa in o.findChildren(QScrollArea):                 # les résultats, sous les visées
        sa.verticalScrollBar().setValue(sa.verticalScrollBar().maximum())
    attendre(app, lambda: False, 0.5)
    p.grab().save(str(sortie / ('partages_analyse_%s.png' % langue)))
    p.onglets.setCurrentIndex(3)
    attendre(app, lambda: False, 0.3)
    p.grab().save(str(sortie / ('partages_depot_%s.png' % langue)))
    p.arreter()
    p.close()
    s.fermer()
    from coupole.modules.td.gui import Panneau as PTD
    t = PTD()
    t.resize(1360, 820)
    t.show()
    for cible in ('iss', 'lune'):
        tp = t.parallaxe
        tp.res = None
        tp.c_cible.setCurrentIndex(tp.c_cible.findData(cible))
        tp.exemple()
        attendre(app, lambda: tp.res is not None)
        attendre(app, lambda: False, 0.5)
        t.grab().save(str(sortie / ('td_parallaxe_%s_%s.png' % (cible, langue))))
    t.close()
    from coupole.gui.dialogues import DialogueReglages
    d = DialogueReglages()
    d.onglets.setCurrentIndex(d.onglets.count() - 1)
    d.resize(820, 520)
    d.show()
    attendre(app, lambda: False, 0.3)
    d.grab().save(str(sortie / ('reglages_astrometrie_%s.png' % langue)))
    d.close()
    print('captures dans', sortie)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
