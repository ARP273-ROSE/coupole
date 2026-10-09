"""0.1.11 — chaque bouton qui ouvre un dialogue de fichier ou de dossier l'ouvre vraiment.

Retour d'utilisateur (KDE, portail XDG depuis 0.1.8) : dans « Spectres et séries », « Ouvrir un fichier » ne faisait
rien.  Cause : le filtre « (*.fits *.fit …) » n'avait pas de nom ; Qt l'envoie au portail avec un nom vide, que
xdg-desktop-portal refuse (« invalid filter: name is empty », src/file-chooser.c) — le dialogue ne s'ouvre pas.

Ici : QFileDialog remplacé par un double qui note parent, titre, dossier et filtres ; chaque bouton de
l'application est déclenché ; filtres vérifiés comme le portail les vérifie, parent = fenêtre visible ; chaque
ouverture et son résultat (ou son exception) sont dans le journal.
"""
import logging
import os
import re
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QDialog, QFileDialog, QPushButton

from coupole.core.i18n import tr
from coupole.gui import fichiers

RACINE = Path(__file__).resolve().parents[1] / 'coupole'


class FauxDialogue:
    """Double de QFileDialog : rien ne s'affiche, tout est noté ; `exec` rend « annulé » (ou lève)."""
    FileMode, Option, AcceptMode = QFileDialog.FileMode, QFileDialog.Option, QFileDialog.AcceptMode
    ouverts: list = []
    lever = None

    def __init__(self, parent, titre, dossier, filtre):
        self.parent, self.titre, self.dossier, self.filtre = parent, titre, dossier, filtre
        FauxDialogue.ouverts.append(self)

    def setFileMode(self, *_):
        pass

    def setOption(self, *_):
        pass

    def setAcceptMode(self, *_):
        pass

    def setSidebarUrls(self, *_):
        pass

    def exec(self):
        if FauxDialogue.lever:
            raise FauxDialogue.lever
        return QDialog.DialogCode.Rejected

    def selectedFiles(self):
        return []

    def selectedNameFilter(self):
        return ''

    def deleteLater(self):
        pass


@pytest.fixture
def faux(monkeypatch):
    FauxDialogue.ouverts = []
    FauxDialogue.lever = None
    monkeypatch.setattr(fichiers, 'QFileDialog', FauxDialogue)
    return FauxDialogue


def verifier_filtres_portail(filtre):
    """Les règles de xdg-desktop-portal (check_filter) sur ce que Qt lui enverra."""
    vus = set()
    for nom, motifs in fichiers.filtres_portail(filtre):
        assert nom, 'filtre sans nom : %r' % filtre
        assert motifs and all(motifs), 'filtre sans motif : %r' % filtre
        assert len(set(motifs)) == len(motifs), 'motif répété : %r' % filtre
        assert (nom, tuple(motifs)) not in vus, 'filtre en double : %r' % filtre
        vus.add((nom, tuple(motifs)))


def verifier_ouverture(faux, n=1):
    assert len(faux.ouverts) == n, 'le bouton n\'a pas ouvert de dialogue'
    d = faux.ouverts[-1]
    assert d.parent is not None and d.parent.isVisible() and d.parent.isWindow()
    assert d.titre
    verifier_filtres_portail(d.filtre)
    return d


def test_filtre_sans_nom_reçoit_un_nom():
    assert fichiers.filtres_portail('(*.fits *.fit)') == [('', ['*.fits', '*.fit'])]       # ce que Qt envoyait
    f = fichiers.normaliser_filtre('(*.fits *.fit *.fits)', tous=True)
    assert f == 'Fichiers pris en charge (*.fits *.fit);;Tous les fichiers (*)'
    verifier_filtres_portail(f)
    assert fichiers.normaliser_filtre('CSV (*.csv);;CSV (*.csv);;Vide ()') == 'CSV (*.csv)'
    assert fichiers.normaliser_filtre('') == ''


def test_depart_inexistant():
    assert fichiers._depart_existant('') == ''
    racine = os.path.abspath(os.sep)                                     # « / » ou « D:\\ » (Windows)
    assert fichiers._depart_existant(os.path.join(racine, 'inexistant', 'a', 'b')) == racine
    d = os.path.expanduser('~')
    assert fichiers._depart_existant(os.path.join(d, 'pas_la', 'x')) == d
    assert fichiers._depart_existant(os.path.join(d, 'rapport.json')) == os.path.join(d, 'rapport.json')


def test_toutes_les_ouvertures_sont_couvertes():
    """Garde-fou : un nouvel appel à `fichiers.choisir_*` doit être ajouté au test des boutons ci-dessous."""
    n = 0
    for f in RACINE.rglob('*.py'):
        if f.name == 'fichiers.py':
            continue
        n += len(re.findall(r'fichiers\.choisir_(?:dossier|fichier|enregistrement)\(', f.read_text(encoding='utf-8')))
    assert n == 15


def _montrer(w, app):
    w.resize(1100, 700)
    w.show()
    app.processEvents()
    return w


def _bouton(w, cle):
    return next(b for b in w.findChildren(QPushButton) if b.text() == tr(cle))


def test_spectres_et_series(app_qt, faux):
    from coupole.modules.donnees.gui import Panneau
    p = _montrer(Panneau(), app_qt)
    try:
        _bouton(p, 'don_ouvrir').click()                       # le vrai bouton, comme l'utilisateur
        d = verifier_ouverture(faux)
        noms = [n for n, _ in fichiers.filtres_portail(d.filtre)]
        assert noms[0] == 'Spectres et séries' and 'Tous les fichiers' in noms
        assert '*.fits' in fichiers.filtres_portail(d.filtre)[0][1]

        class D:
            x = [1.0]
        p._courant = lambda: D()
        p.exporter()
        verifier_ouverture(faux, 2)
    finally:
        p.close()


def test_cosmologie(app_qt, faux):
    from coupole.modules.cosmo.gui import Panneau
    p = _montrer(Panneau(), app_qt)
    try:
        p.resultat = {'z': 1.0}
        p.exporter_tableau()
        verifier_ouverture(faux, 1)
        p.courbes = {'z': [0, 1]}
        p.exporter_courbes()
        verifier_ouverture(faux, 2)
    finally:
        p.close()


def test_qualite(app_qt, faux):
    from coupole.modules.qualite.gui import Panneau
    p = _montrer(Panneau(), app_qt)
    try:
        p.choisir()
        verifier_ouverture(faux)
    finally:
        p.close()


def test_archives(app_qt, faux):
    from coupole.modules.archives.gui import Panneau
    p = _montrer(Panneau(), app_qt)
    try:
        p.choisir_dossier()
        verifier_ouverture(faux, 1)
        p.ajouter_fichiers()
        d = verifier_ouverture(faux, 2)
        assert '*.xisf' in fichiers.filtres_portail(d.filtre)[0][1]
    finally:
        p.arreter()
        p.close()


def test_banque_ohp(app_qt, faux, monkeypatch, tmp_path):
    import time
    from coupole.core import config
    from coupole.modules.ohp import gui as G
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    monkeypatch.setattr(G.QMessageBox, 'information', lambda *a, **k: None)
    p = _montrer(G.Panneau(), app_qt)
    try:
        fin = time.time() + 30
        while p.inv is None and time.time() < fin:
            app_qt.processEvents()
            time.sleep(0.01)
        p._parcourir()
        verifier_ouverture(faux, 1)
        monkeypatch.setitem(config.reglages().valeurs, 'dossier_sortie', '')
        assert p._choisir_dest_si_besoin() is None
        verifier_ouverture(faux, 2)
        p.reorganiser()
        verifier_ouverture(faux, 3)
        p._exporter_anomalies()
        verifier_ouverture(faux, 4)
    finally:
        p.arreter()
        p.close()


def test_dialogues_de_l_application(app_qt, faux):
    from coupole.gui import dialogues as D
    r = _montrer(D.DialogueReglages(), app_qt)
    a = _montrer(D.DialogueASTAP(), app_qt)
    s = _montrer(D.DialogueSignaler(), app_qt)
    try:
        r._parcourir()
        verifier_ouverture(faux, 1)
        a.choisir_exe()
        verifier_ouverture(faux, 2)
        a.choisir_cat()
        verifier_ouverture(faux, 3)
        s.fichier()
        d = verifier_ouverture(faux, 4)
        assert d.dossier.endswith('coupole-rapport.json')
    finally:
        for w in (r, a, s):
            w.close()


def test_journal_de_chaque_ouverture(app_qt, faux, caplog):
    from PyQt6.QtWidgets import QWidget
    w = _montrer(QWidget(), app_qt)
    caplog.set_level(logging.INFO, logger='coupole.gui.fichiers')
    assert fichiers.choisir_fichier(w, 'Essai', '/inexistant', '(*.fits)') == ('', '')
    texte = caplog.text
    assert 'file dialog open: mode=ouvrir' in texte and "filters='Fichiers pris en charge (*.fits)" in texte
    assert 'file dialog closed: cancelled' in texte
    faux.lever = RuntimeError('portail injoignable')
    assert fichiers.choisir_dossier(w, 'Essai', '') == ''                 # jamais d'exception jusqu'au bouton
    assert 'file dialog failed' in caplog.text and 'portail injoignable' in caplog.text
    w.close()


def test_parent_cache_remplace_par_une_fenetre_visible(app_qt, faux):
    from PyQt6.QtWidgets import QWidget
    visible = _montrer(QWidget(), app_qt)
    cache = QWidget()
    fichiers.choisir_dossier(cache, 'Essai', '')
    assert faux.ouverts[-1].parent is not cache and faux.ouverts[-1].parent.isVisible()
    visible.close()
