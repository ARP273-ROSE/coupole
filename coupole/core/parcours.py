"""Parcours d'arborescence parallèle (partages réseau).

Sur un partage SMB/NFS, lire un dossier coûte un aller-retour réseau : `os.walk` les enchaîne un par un (1 233
dossiers dans la banque OHP rangée : 5,7 s à 2 ms par opération).  Ici l'arborescence est lue niveau par niveau,
chaque niveau par plusieurs fils (le GIL est rendu pendant l'appel système) : 0,4 s.  Le type de chaque entrée
vient de la liste du dossier (`scandir`), sans `stat` supplémentaire.
"""
from __future__ import annotations

import concurrent.futures as F
import os

FILS = 16


def _lister_dossier(d, extensions, exclus):
    fichiers, sous = [], []
    try:
        with os.scandir(d) as it:
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False):
                        if e.name not in exclus:
                            sous.append(e.path)
                    elif extensions is None or e.name.lower().endswith(extensions):
                        fichiers.append(e.path)
                except OSError:
                    continue
    except OSError:
        pass
    return d, sorted(fichiers), sorted(sous)


def lister(racine, extensions: tuple | None = None, exclus=('_traitement',), fils: int = FILS) -> dict:
    """{dossier: [fichiers (chemins complets, triés)]} pour chaque dossier qui contient des fichiers retenus
    (`extensions` en minuscules, None = tous), sous-dossiers `exclus` ignorés ; dossiers triés."""
    out = {}
    racine = str(racine)
    if not os.path.isdir(racine):
        return out
    exclus = set(exclus or ())
    niveau = [racine]
    with F.ThreadPoolExecutor(max(1, fils), thread_name_prefix='parcours') as pool:
        while niveau:
            suivant = []
            res = pool.map(lambda d: _lister_dossier(d, extensions, exclus), niveau) if len(niveau) > 1 else \
                [_lister_dossier(niveau[0], extensions, exclus)]
            for d, fs, sous in res:
                if fs:
                    out[d] = fs
                suivant += sous
            niveau = suivant
    return dict(sorted(out.items()))
