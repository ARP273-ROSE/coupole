"""Ouvrir une image depuis un tableau : double-clic (application associée du système), menu contextuel « Ouvrir »,
« Ouvrir avec » (seulement les logiciels qui lisent vraiment ce fichier, les autres grisés avec la raison) et
« Ouvrir l'emplacement du fichier » (fichier sélectionné dans le gestionnaire de fichiers).

Depuis 0.1.12, chaque lancement passe par `core/lancement.py` (liste d'arguments, coupole.log) et son résultat
s'affiche dans la barre d'état (`suivre`) : jamais de silence."""
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


# ------------------------------------------------------------------ suivi des lancements (0.1.12)
_suivis = []          # lancements dont on attend l'état final (référence tenue)


def statut(texte: str, ms: int = 10000):
    """Message dans la barre d'état de la fenêtre principale (la fenêtre active d'abord)."""
    from PyQt6.QtWidgets import QApplication, QMainWindow
    fenetres = []
    w = QApplication.activeWindow()
    if w is not None:
        fenetres.append(w.window())
    fenetres += [x for x in QApplication.topLevelWidgets() if x not in fenetres]
    for f in fenetres:
        if isinstance(f, QMainWindow) and f.isVisible():
            f.statusBar().showMessage(texte, ms)
            return True
    return False


def texte_lancement(l) -> str:
    m = l.message() if l is not None else None
    if m is None:
        return ''
    cle, params = m
    return tr(cle, **params)


def suivre(l, nom: str = ''):
    """Affiche tout de suite « Ouverture… » ou l'erreur, puis l'état final des premières secondes (erreur, code de
    retour, PixInsight qui cède la main…) ; rien n'est silencieux."""
    from PyQt6.QtCore import QTimer
    if l is None or l is True or l is False:          # anciens appels / remplacés dans les tests
        return l
    nom = nom or l.nom
    if not l.ok:
        statut(texte_lancement(l), 15000)
        return l
    statut(tr('lg_lancement_en_cours', logiciel=nom), 5000)
    _suivis.append(l)
    minuteur = QTimer()
    minuteur.setInterval(250)

    def tic():
        if not l.verifier():
            return
        minuteur.stop()
        try:
            _suivis.remove(l)
            _suivis.remove(minuteur)
        except ValueError:
            pass
        t = texte_lancement(l)
        if t:
            statut(t, 20000)
    minuteur.timeout.connect(tic)
    _suivis.append(minuteur)
    minuteur.start()
    return l


def ouvrir_defaut(chemin):
    """Double-clic / « Ouvrir » : application associée, journalisée ; lancement direct si le .desktop de
    l'application par défaut ne reçoit pas de fichier (Linux)."""
    p = os.path.abspath(str(chemin))
    l = logiciels.ouvrir_defaut(p, installes())
    if l is None:                                     # ni xdg-open, ni open, ni startfile : Qt
        import logging
        ok = QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        logging.getLogger('coupole.lancement').info('launch [QDesktopServices] %s -> %s', p, ok)
        if not ok:
            statut(tr('lg_err_aucun_moyen', detail=p), 15000)
        return ok
    return suivre(l)


def lancer_logiciel(lg: str, chemin, nouvelle=None):
    return suivre(logiciels.lancer_logiciel(lg, chemin, installes(), nouvelle=nouvelle))


def montrer_emplacement(chemin):
    """« Ouvrir l'emplacement », « dossier de la cible », « dossier du lot » : journalisé, erreur en barre d'état."""
    l = logiciels.montrer_dans_dossier(chemin)
    if l is None:
        statut(tr('lg_err_aucun_moyen', detail=str(chemin)), 15000)
        return None
    return suivre(l)


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
        nom = logiciels.NOMS[lg]
        if lg == 'pixinsight' and ok and logiciels.pixinsight_ouvert():
            # une instance tourne : les deux façons, celle des Préférences d'abord
            nouvelle_dabord = logiciels._instance_voulue(None)
            for nouvelle in ((True, False) if nouvelle_dabord else (False, True)):
                b = action(sm, tr('lg_pixinsight_nouvelle' if nouvelle else 'lg_pixinsight_envoyer'), True,
                           tr('lg_pixinsight_nouvelle_aide' if nouvelle else 'lg_pixinsight_envoyer_aide'))
                b.triggered.connect(lambda _=False, n=nouvelle: lancer_logiciel('pixinsight', chemin, n))
            continue
        motif_court = tr('lg_motif_argument') if raison == logiciels.SANS_FICHIER.get(lg) else tr('lg_motif_illisible')
        b = action(sm, nom, ok, tr('lg_ouvrir_avec_aide', logiciel=nom), tr(raison) if raison else '', motif_court)
        b.triggered.connect(lambda _=False, x=lg: lancer_logiciel(x, chemin))
    sm.setEnabled(existe)
    c = action(menu, tr('lg_emplacement'), existe, tr('lg_emplacement_aide'), tr(raison_absent), court)
    c.triggered.connect(lambda: montrer_emplacement(chemin))
    return menu
