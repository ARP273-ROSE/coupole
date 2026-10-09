"""Reconnaître les fichiers existants : reconstruire la base de suivi d'un dossier de sortie à partir des fichiers
convertis qui y sont déjà rangés (0.2.1).

Cas visé : un dossier de sortie complet (copie d'une autre machine, sauvegarde restaurée) dont le dossier
``_traitement/`` manque — sans base de suivi, rien ne paraît possédé et la Banque OHP proposerait de tout
retélécharger.  Chaque fichier converti porte son origine dans son en-tête (propriété XISF ``OHP:Source:URL`` ou
carte ``HISTORY « converti de <fichier> »``, voir ``reorganisation.analyser``) : on retrouve sa ligne d'inventaire,
donc son identifiant, et on l'inscrit « possédé » (statut ``ok``) avec son chemin relatif au dossier de sortie.

Rien n'est téléchargé, rien n'est déplacé ni réécrit : seule la base de suivi est créée ou complétée (par la base
de travail locale si le dossier est sur un partage, comme pour un traitement).  Une image déjà connue de la base
n'est pas touchée.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger('coupole.reconnaissance')


def reconnaitre(dest, inventaire, progression=None, arret=None, rapporter=None, processus=None) -> dict:
    """Inscrit dans ``<dest>/_traitement/etat.sqlite`` les fichiers convertis trouvés sous `dest`.

    `progression(fait, total)` : au plus 10 fois par seconde ; `arret` (threading.Event) : ce qui est déjà reconnu
    est gardé.  Lève base_partagee.Divergence (rien n'est écrit) si la base du partage et la base de travail locale
    ont changé chacune de leur côté.  Rend {'reconnus', 'deja', 'ignores': [(chemin, raison)], 'fichiers'}."""
    from . import emplacements, reorganisation
    from .conversion import ident
    from .pilote import Etat
    dest = os.path.abspath(str(dest))
    trouves, ignores = reorganisation.inventorier(dest, inventaire, dest, progression=progression, arret=arret,
                                                  processus=processus)
    chemin = os.path.join(dest, '_traitement', 'etat.sqlite')
    etat = Etat(chemin, delai=2.0, rapporter=rapporter)
    n = deja = 0
    try:
        statuts = etat.statuts()
        vus = set()
        for fichier, x, info in trouves:
            i = ident(x)
            if statuts.get(i) in ('ok', 'doublon') or i in vus:
                deja += 1
                continue
            vus.add(i)
            rel = emplacements.dans_sortie(fichier, dest)
            info.pop('reorganise', None)
            info.update(chemin=rel, final=fichier, staging='', reconnu=True,
                        extension='.fits.fz' if fichier.lower().endswith('.fits.fz') else os.path.splitext(fichier)[1])
            etat.ecrire(i, x['access_url'], 'ok', info, 0)
            n += 1
        etat.valider()
    finally:
        etat.fermer()
    log.info('reconnaissance de %s : %d fichier(s) inscrit(s), %d déjà connu(s), %d ignoré(s)', dest, n, deja,
             len(ignores))
    return {'reconnus': n, 'deja': deja, 'ignores': ignores, 'fichiers': len(trouves) + len(ignores)}
