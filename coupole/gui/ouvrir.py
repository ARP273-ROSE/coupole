"""Ouvrir une image depuis un tableau : double-clic (application associée du système), menu contextuel « Ouvrir »,
« Ouvrir avec » (seulement les logiciels qui lisent vraiment ce fichier, les autres grisés avec la raison) et
« Ouvrir l'emplacement du fichier » (fichier sélectionné dans le gestionnaire de fichiers)."""
from __future__ import annotations

import os

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMenu

from ..core import logiciels
from ..core.i18n import tr

_installes = None


def installes(rafraichir: bool = False) -> dict:
    """Logiciels d'astronomie trouvés (cherchés une fois par session : quelques tests d'existence)."""
    global _installes
    if _installes is None or rafraichir:
        _installes = logiciels.detecter()
    return _installes


def ouvrir_defaut(chemin) -> bool:
    return QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(str(chemin))))


def remplir_menu(menu: QMenu, chemin, existe: bool | None = None, raison_absent: str = 'lg_pas_telechargee'):
    """Ajoute à `menu` les actions d'ouverture du fichier `chemin` (désactivées s'il n'existe pas)."""
    existe = bool(chemin) and os.path.exists(chemin) if existe is None else existe
    menu.setToolTipsVisible(True)
    a = menu.addAction(tr('lg_ouvrir'))
    a.setToolTip(tr('lg_ouvrir_aide') if existe else tr(raison_absent))
    a.setEnabled(existe)
    a.triggered.connect(lambda: ouvrir_defaut(chemin))
    sm = menu.addMenu(tr('lg_ouvrir_avec'))
    sm.setToolTipsVisible(True)
    props = logiciels.propositions(chemin, installes()) if existe else []
    if not props:
        b = sm.addAction(tr('lg_aucun_logiciel'))
        b.setEnabled(False)
    for lg, ok, raison in props:
        b = sm.addAction(logiciels.NOMS[lg])
        b.setEnabled(ok)
        b.setToolTip(tr('lg_ouvrir_avec_aide', logiciel=logiciels.NOMS[lg]) if ok else tr(raison))
        cmd = installes()[lg]
        b.triggered.connect(lambda _=False, c=cmd: logiciels.lancer(c, chemin))
    sm.setEnabled(existe)
    c = menu.addAction(tr('lg_emplacement'))
    c.setToolTip(tr('lg_emplacement_aide'))
    c.setEnabled(existe)
    c.triggered.connect(lambda: logiciels.montrer_dans_dossier(chemin))
    return menu
