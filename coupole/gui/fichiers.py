"""Dialogues de fichiers : l'explorateur du système (Windows, macOS, Dolphin/Nautilus par le portail XDG sous
Linux), ou, en repli, le dialogue de Qt traduit et complété des emplacements du système (montages, partages).

Tous les choix de fichier ou de dossier de Coupole passent par ici. Préférences > « Boîtes de dialogue de
fichiers » : « système » (défaut) ou « Qt » (si le dialogue du système fonctionne mal chez quelqu'un).
"""
from __future__ import annotations

import logging
import os
import re

from PyQt6.QtCore import QStandardPaths, QUrl
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog

from ..core import config
from ..core.chemins import emplacements_systeme
from ..core.i18n import tr
from . import plateforme

log = logging.getLogger(__name__)

# Qt (QPlatformFileDialogHelper::filterRegExp) découpe un filtre « Nom (*.a *.b) » ainsi pour le portail XDG ;
# le portail refuse (InvalidArgument) un nom vide, une liste de motifs vide ou un motif vide : le dialogue ne
# s'ouvre alors PAS DU TOUT (0.1.10, Spectres et séries : « (*.fits *.fit …) » sans nom).
FILTRE_QT = re.compile(r'^(.*)\(([a-zA-Z0-9_.,*? +;#\-\[\]@\{\}/!<>\$%&=^~:\|]*)\)$')


def force_qt() -> bool:
    return config.reglages()['dialogues_fichiers'] == 'qt'


def emplacements() -> list[str]:
    """Barre latérale du dialogue de Qt : dossier personnel, Bureau, Documents, Images, Téléchargements, racine,
    puis les emplacements du système (partages gvfs, montages cifs/nfs, /run/media/…, /media, /mnt, /Volumes)."""
    sortie: list[str] = []
    L = QStandardPaths.StandardLocation
    for lieu in (L.HomeLocation, L.DesktopLocation, L.DocumentsLocation, L.PicturesLocation, L.DownloadLocation):
        p = QStandardPaths.writableLocation(lieu)
        if p and os.path.isdir(p) and p not in sortie:
            sortie.append(p)
    if os.name != 'nt':
        sortie.append('/')
    for p in emplacements_systeme():
        if p not in sortie:
            sortie.append(p)
    return sortie


def _preparer(d: QFileDialog):
    if force_qt():
        d.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    if force_qt() or not plateforme.dialogue_natif_attendu():
        urls = [QUrl.fromLocalFile(p) for p in emplacements()]
        if os.name == 'nt':
            urls.append(QUrl('file:'))             # « Ce PC » : lecteurs et lecteurs réseau
        d.setSidebarUrls(urls)


def filtres_portail(filtre: str) -> list[tuple[str, list[str]]]:
    """Ce que Qt enverra au portail XDG pour `filtre` (« Nom (*.a *.b);;Autre (*) ») : [(nom, [motifs])]."""
    out = []
    for f in (filtre or '').split(';;'):
        m = FILTRE_QT.match(f.strip())
        if m:
            out.append((m.group(1).strip(), [x for x in m.group(2).split(' ') if x]))
        elif f.strip():
            out.append((f.strip(), [x for x in f.split(' ') if x]))      # Qt : motifs sans nom
    return out


def normaliser_filtre(filtre: str, tous: bool = False) -> str:
    """Filtre acceptable par tous les dialogues (portail XDG compris) : chaque filtre a un nom (« Fichiers pris en
    charge » s'il manquait) et au moins un motif, sans motif répété ni filtre en double ; `tous` : « Tous les
    fichiers (*) » à la fin (ouverture)."""
    vus, sortie = set(), []
    for nom, motifs in filtres_portail(filtre):
        propres = []
        for x in motifs:
            if x and x not in propres:
                propres.append(x)
        if not propres:
            continue
        nom = nom or tr('fichiers_pris_en_charge')
        cle = (nom, tuple(propres))
        if cle in vus:
            continue
        vus.add(cle)
        sortie.append('%s (%s)' % (nom, ' '.join(propres)))
    if tous and sortie and not any(p == ['*'] for _, p in filtres_portail(';;'.join(sortie))):
        sortie.append('%s (*)' % tr('fichiers_tous'))
    return ';;'.join(sortie)


def _parent_visible(parent):
    """La fenêtre (visible) à laquelle rattacher le dialogue : le portail XDG et macOS l'exigent ; un widget caché
    ou détruit ne donne pas d'identifiant de fenêtre."""
    w = None
    try:
        w = parent.window() if parent is not None else None
        if w is not None and w.isVisible():
            return w
    except RuntimeError:                             # objet Qt détruit
        w = None
    return QApplication.activeWindow() or next((x for x in QApplication.topLevelWidgets()
                                                if x.isVisible() and x.isWindow()), None) or w


def _depart_existant(depart: str) -> str:
    """Dossier de départ qui existe (le plus proche parent existant ; sinon le dossier personnel) : un dossier
    disparu ou un partage démonté est refusé par certains dialogues."""
    if not depart:
        return ''
    p = os.path.abspath(os.path.expanduser(depart))
    nom = ''
    while p and not os.path.isdir(p):
        parent = os.path.dirname(p)
        if parent == p:
            return os.path.expanduser('~')
        nom = nom or os.path.basename(p)
        p = parent
    if nom and not os.path.isdir(os.path.join(p, nom)) and os.path.splitext(nom)[1] and \
            os.path.dirname(os.path.abspath(os.path.expanduser(depart))) == p:
        return os.path.join(p, nom)                    # nom de fichier proposé (enregistrement) gardé
    return p


def _executer(parent, titre: str, depart: str, filtre: str, mode: str) -> tuple[str, str]:
    # parent indispensable : le portail XDG et macOS rattachent leur fenêtre à celle de l'application
    fen = _parent_visible(parent)
    filtre = normaliser_filtre(filtre, tous=mode == 'ouvrir')
    depart_reel = _depart_existant(depart)
    log.info('file dialog open: mode=%s title=%r start=%r (asked %r) filters=%r parent=%s visible=%s theme=%s',
             mode, titre, depart_reel, depart, filtre, type(parent).__name__ if parent is not None else None,
             bool(fen), plateforme.decision.get('theme'))
    d = None
    try:
        d = QFileDialog(fen, titre, depart_reel or '', filtre or '')
        if mode == 'dossier':
            d.setFileMode(QFileDialog.FileMode.Directory)
            d.setOption(QFileDialog.Option.ShowDirsOnly, True)
        elif mode == 'ouvrir':
            d.setFileMode(QFileDialog.FileMode.ExistingFile)
        else:
            d.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            d.setFileMode(QFileDialog.FileMode.AnyFile)
        _preparer(d)
        if d.exec() != QDialog.DialogCode.Accepted:
            log.info('file dialog closed: cancelled (%s)', titre)
            return '', ''
        choisis = d.selectedFiles()
        if not choisis:
            log.info('file dialog closed: nothing selected (%s)', titre)
            return '', ''
        log.info('file dialog closed: %r (filter %r)', choisis[0], d.selectedNameFilter())
        return choisis[0], d.selectedNameFilter()
    except Exception:                                  # jamais un bouton muet : la pile est dans coupole.log
        log.exception('file dialog failed (%s)', titre)
        return '', ''
    finally:
        if d is not None:
            d.deleteLater()


def choisir_dossier(parent, titre: str, depart: str = '') -> str:
    """Comme ``QFileDialog.getExistingDirectory`` (chaîne vide si annulé)."""
    return _executer(parent, titre, depart, '', 'dossier')[0]


def choisir_fichier(parent, titre: str, depart: str = '', filtre: str = '') -> tuple[str, str]:
    """Comme ``QFileDialog.getOpenFileName`` : (chemin, filtre choisi)."""
    return _executer(parent, titre, depart, filtre, 'ouvrir')


def choisir_enregistrement(parent, titre: str, depart: str = '', filtre: str = '') -> tuple[str, str]:
    """Comme ``QFileDialog.getSaveFileName`` : (chemin, filtre choisi)."""
    return _executer(parent, titre, depart, filtre, 'enregistrer')
