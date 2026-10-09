"""Dialogues de fichiers : l'explorateur du système (Windows, macOS, Dolphin/Nautilus par le portail XDG sous
Linux), ou, en repli, le dialogue de Qt traduit et complété des emplacements du système (montages, partages).

Tous les choix de fichier ou de dossier de Coupole passent par ici. Préférences > « Boîtes de dialogue de
fichiers » : « système » (défaut) ou « Qt » (si le dialogue du système fonctionne mal chez quelqu'un).
"""
from __future__ import annotations

import os

from PyQt6.QtCore import QStandardPaths, QUrl
from PyQt6.QtWidgets import QDialog, QFileDialog

from ..core import config
from ..core.chemins import emplacements_systeme
from . import plateforme


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


def _executer(parent, titre: str, depart: str, filtre: str, mode: str) -> tuple[str, str]:
    # parent indispensable : le portail XDG et macOS rattachent leur fenêtre à celle de l'application
    d = QFileDialog(parent, titre, depart or '', filtre or '')
    if mode == 'dossier':
        d.setFileMode(QFileDialog.FileMode.Directory)
        d.setOption(QFileDialog.Option.ShowDirsOnly, True)
    elif mode == 'ouvrir':
        d.setFileMode(QFileDialog.FileMode.ExistingFile)
    else:
        d.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        d.setFileMode(QFileDialog.FileMode.AnyFile)
    _preparer(d)
    try:
        if d.exec() != QDialog.DialogCode.Accepted:
            return '', ''
        choisis = d.selectedFiles()
        if not choisis:
            return '', ''
        return choisis[0], d.selectedNameFilter()
    finally:
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
