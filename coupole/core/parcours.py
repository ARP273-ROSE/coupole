"""Parcours d'arborescence parallèle (partages réseau).

Sur un partage SMB/NFS, lire un dossier coûte un aller-retour réseau : `os.walk` les enchaîne un par un (1 233
dossiers dans la banque OHP rangée : 5,7 s à 2 ms par opération).  Ici chaque dossier lu fait aussitôt partir la
lecture de ses sous-dossiers, par plusieurs fils (le GIL est rendu pendant l'appel système) : 0,4 s.  Le type de
chaque entrée vient de la liste du dossier (`scandir`), sans `stat` supplémentaire ; la taille et la date ne sont
lues (`DirEntry.stat`, gratuit sous Windows, servi par le cache d'attributs du client SMB juste après la liste
sous Linux) que pour les fichiers demandés, dans le même fil, juste après la liste.

`parcourir` rend les dossiers au fur et à mesure (pour commencer à travailler avant la fin du parcours) ;
`lister` rend tout, trié.
"""
from __future__ import annotations

import concurrent.futures as F
import os

FILS = 16


def _lister_dossier(d, extensions, exclus, a_dater=None):
    """(dossier, [fichiers triés], [sous-dossiers triés], {fichier: (taille, mtime) ou None}).

    `a_dater(fichiers triés)` → les fichiers dont on veut taille et date (None : aucun)."""
    fichiers, sous, entrees = [], [], {}
    try:
        with os.scandir(d) as it:
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False):
                        if e.name not in exclus:
                            sous.append(e.path)
                    elif extensions is None or e.name.lower().endswith(extensions):
                        fichiers.append(e.path)
                        entrees[e.path] = e
                except OSError:
                    continue
    except OSError:
        pass
    fichiers.sort()
    dates = {}
    if a_dater is not None and fichiers:
        for f in a_dater(fichiers):
            try:
                st = entrees[f].stat()
                dates[f] = (int(st.st_size), float(st.st_mtime))
            except (OSError, KeyError):
                dates[f] = None
    return d, fichiers, sorted(sous), dates


def parcourir(racine, extensions: tuple | None = None, exclus=('_traitement',), fils: int = FILS, arret=None,
              a_dater=None):
    """Génère (dossier, [fichiers triés], {fichier: (taille, mtime) ou None}) pour chaque dossier qui contient des
    fichiers retenus, **dès qu'il est lu** (ordre d'arrivée, pas d'ordre alphabétique) ; `arret` (Event) interrompt.

    `extensions` en minuscules (None = tous) ; sous-dossiers `exclus` ignorés ; `a_dater` : voir `_lister_dossier`."""
    racine = str(racine)
    if not os.path.isdir(racine):
        return
    exclus = set(exclus or ())
    with F.ThreadPoolExecutor(max(1, fils), thread_name_prefix='parcours') as pool:
        en_cours = {pool.submit(_lister_dossier, racine, extensions, exclus, a_dater)}
        try:
            while en_cours:
                if arret is not None and arret.is_set():
                    return
                finis, en_cours = F.wait(en_cours, timeout=0.2, return_when=F.FIRST_COMPLETED)
                for fut in finis:
                    d, fs, sous, dates = fut.result()
                    for s in sous:
                        en_cours.add(pool.submit(_lister_dossier, s, extensions, exclus, a_dater))
                    if fs:
                        yield d, fs, dates
        finally:
            for fut in en_cours:
                fut.cancel()


def lister(racine, extensions: tuple | None = None, exclus=('_traitement',), fils: int = FILS) -> dict:
    """{dossier: [fichiers (chemins complets, triés)]} pour chaque dossier qui contient des fichiers retenus
    (`extensions` en minuscules, None = tous), sous-dossiers `exclus` ignorés ; dossiers triés."""
    return dict(sorted((d, fs) for d, fs, _ in parcourir(racine, extensions, exclus, fils)))
