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


def action(menu: QMenu, texte: str, actif: bool, aide: str = '', motif: str = '', motif_court: str = ''):
    """Action de menu.  Désactivée : le motif court est dans le libellé (« Ouvrir avec (rien de téléchargé) ») et
    le motif complet dans la barre d'état au survol (`statusTip`).

    Pas d'info-bulle dans les menus (0.1.11) : sous Linux/KDE (Wayland surtout), l'info-bulle d'une entrée
    s'ouvre par-dessus le menu et en capte la souris — « ça s'affiche mais impossible de cliquer »."""
    a = menu.addAction(texte if actif or not motif_court else '%s  (%s)' % (texte, motif_court))
    a.setEnabled(bool(actif))
    a.setStatusTip(aide if actif else (motif or aide))
    return a


def montrer_menu(menu: QMenu, pos_global) -> QMenu:
    """Affiche un menu contextuel sans boucle d'événements imbriquée (`popup`, pas `exec` : le menu ne retient
    pas le signal qui l'a ouvert), détruit à la fermeture ; rend le menu (tests)."""
    from PyQt6.QtCore import Qt
    menu.setToolTipsVisible(False)
    for sm in menu.findChildren(QMenu):
        sm.setToolTipsVisible(False)
    menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
    parent = menu.parentWidget()
    if parent is not None:
        parent._menu_contextuel = menu             # référence tenue jusqu'au prochain menu
    menu.popup(pos_global)
    return menu


def remplir_menu(menu: QMenu, chemin, existe: bool | None = None, raison_absent: str = 'lg_pas_telechargee'):
    """Ajoute à `menu` les actions d'ouverture du fichier `chemin` (désactivées, motif dans le libellé, s'il
    n'existe pas)."""
    existe = bool(chemin) and os.path.exists(chemin) if existe is None else existe
    court = tr('lg_motif_rien')
    a = action(menu, tr('lg_ouvrir'), existe, tr('lg_ouvrir_aide'), tr(raison_absent), court)
    a.triggered.connect(lambda: ouvrir_defaut(chemin))
    sm = menu.addMenu(tr('lg_ouvrir_avec') if existe else '%s  (%s)' % (tr('lg_ouvrir_avec'), court))
    sm.menuAction().setStatusTip(tr('lg_ouvrir_avec_aide_menu') if existe else tr(raison_absent))
    props = logiciels.propositions(chemin, installes()) if existe else []
    if not props:
        action(sm, tr('lg_aucun_logiciel'), False)
    for lg, ok, raison in props:
        b = action(sm, logiciels.NOMS[lg], ok, tr('lg_ouvrir_avec_aide', logiciel=logiciels.NOMS[lg]),
                   tr(raison) if raison else '', tr('lg_motif_illisible'))
        cmd = installes()[lg]
        b.triggered.connect(lambda _=False, c=cmd: logiciels.lancer(c, chemin))
    sm.setEnabled(existe)
    c = action(menu, tr('lg_emplacement'), existe, tr('lg_emplacement_aide'), tr(raison_absent), court)
    c.triggered.connect(lambda: logiciels.montrer_dans_dossier(chemin))
    return menu
