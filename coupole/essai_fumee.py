"""Essai « fumée » d'un paquet construit (installeur Windows, .app macOS, tar.gz/.deb Linux), sans écran :

    QT_QPA_PLATFORM=offscreen python -m coupole.essai_fumee

Ouvre la fenêtre principale et chaque module, les 94 animations, une page de chaque sorte (accueil des modules,
module, question notée, recherche, Mes modules, progression), une fiche, une table et une image, vérifie que toutes
les données livrées se lisent (JSON compressés, images WebP, police mathématique), change de thème et de langue.
Code de sortie 0 si tout va bien ; sinon 1 et la liste des défauts.  Rien n'est écrit hors d'un dossier temporaire."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import traceback


def main() -> int:
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from .cli import console_tolerante
    console_tolerante()                            # console Windows (cp1252) : jamais d'erreur d'encodage
    os.environ['COUPOLE_HOME'] = tempfile.mkdtemp(prefix='coupole-fumee-')
    os.environ['COUPOLE_SANS_RESEAU'] = '1'
    defauts: list[str] = []
    sys.excepthook = lambda t, v, tb: defauts.append(''.join(traceback.format_exception(t, v, tb))[-800:])
    t0 = time.perf_counter()
    from PyQt6.QtGui import QImage
    from PyQt6.QtWidgets import QApplication
    from .cli import initialiser
    from .core import config
    initialiser('fr')
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    app = QApplication.instance() or QApplication(sys.argv)
    from .gui import theme
    theme.appliquer(app)

    def tourner(s=0.05):
        fin = time.time() + s
        while time.time() < fin:
            app.processEvents()

    def verifier(cond, texte):
        if not cond:
            defauts.append(texte)

    # données livrées
    from .modules.anim import catalogue, formule
    from .modules.anim.classe import contenu
    verifier(len(contenu.toutes_les_questions()) >= 517, 'questions manquantes')
    verifier(len(contenu.modules()) >= 24, 'modules manquants')
    photos = [i for i in list(contenu._images().values()) + list(contenu.images_questions().values())
              if i.get('nature') == 'photo']
    verifier(len(photos) >= 16, 'photographies manquantes')
    for i in photos:
        ch = contenu.chemin_image(i.get('fichier') or i['id'])
        verifier(ch.exists() and not QImage(str(ch)).isNull(), 'image illisible (WebP) : %s' % ch.name)
    verifier('STIX' in formule.famille(), 'police mathématique non chargée : %r' % formule.famille())
    verifier(len(catalogue.ENTREES) >= 94, 'animations manquantes')
    # kit commun : mise à jour et rapports importables, paquet reconnu, style figé, logo, manuels FR et EN
    from .core import maj, rapports
    u = maj.kit('updater')
    maj.kit('reporting')
    maj.kit('interface_kit')
    verifier(bool(maj.depot()), 'dépôt de distribution inconnu')
    if maj.est_paquet():
        verifier(u.is_packaged() and bool(u.REPO), 'paquet non reconnu par la mise à jour (kit.json ?)')
    rapports.init()
    verifier(str(app.property('coupole_style')).lower() == 'fusion', 'style Qt non figé : %r' % app.property('coupole_style'))
    from PyQt6.QtSvg import QSvgRenderer
    from .gui.ressources import DOSSIER as RESSOURCES
    verifier(QSvgRenderer(str(RESSOURCES / 'coupole.svg')).isValid(), 'logo SVG illisible')
    from .cli import chemin_manuel
    from .core import i18n
    for lg in ('fr', 'en'):
        i18n.choisir_langue(lg)
        ch = chemin_manuel()
        verifier(bool(ch) and os.path.getsize(ch) > 100_000 and ch.endswith('_%s.pdf' % lg), 'manuel %s absent' % lg)
    i18n.choisir_langue('fr')
    # fenêtre principale, modules, animations
    from .gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.resize(1280, 800)
    f.show()
    tourner(0.3)
    for p in f.panneaux:
        ident = getattr(getattr(p, 'module', None), 'id', None)
        verifier(ident is not None, 'module défectueux : %s' % type(p).__name__)
        if ident:
            f.ouvrir_module(ident)
            tourner(0.05)
    p = f.ouvrir_module('anim')
    for e in catalogue.ENTREES:
        a = p.ouvrir(e.id)
        verifier(a is not None, 'animation %s' % e.id)
        if a is not None:
            a.toile.repaint()
    v = p.classe
    p.montrer('modules')
    v.aller_module('light', False)
    v.aller_question('intro', 'ca_intro_scale', False)
    q = v.pile.currentWidget()
    q.choisir(q.inst['bonnes'][0])
    q.valider()
    verifier(contenu.question('ca_intro_scale') is not None and q.valide, 'question non notée')
    v.aller_recherche('soleil')
    p.montrer('mes')
    p.montrer('progression')
    from .modules.anim.classe.ressources_qt import fermer_toutes, ouvrir_ressource
    for g, i in (('fiche', 'intro_density'), ('table', 'densities'), ('image', 'startrails')):
        w = ouvrir_ressource(g, i)
        w.repaint()
    tourner(0.2)
    fermer_toutes()
    for nom in ('clair', 'sombre'):
        f.changer_apparence(nom)
        tourner(0.05)
    from .gui import dialogues
    d = dialogues.DialogueAPropos(f)
    d.show()
    tourner(0.2)
    d.close()
    f.changer_langue('en')
    tourner(0.2)
    f.changer_langue('fr')
    tourner(0.1)
    f.close()
    tourner(0.2)
    print('essai fumée : %d animations, %d questions, %.1f s, %s' % (
        len(catalogue.ENTREES), len(contenu.toutes_les_questions()), time.perf_counter() - t0,
        'OK' if not defauts else '%d défaut(s)' % len(defauts)))
    for d in defauts:
        print('DÉFAUT :', d)
    return 1 if defauts else 0


if __name__ == '__main__':
    sys.exit(main())
