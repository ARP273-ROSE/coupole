"""Outils d'analyse branchés sur un partage, par type de défi ou de TP.

Un outil est une classe qui dérive de ``Outil`` et s'inscrit dans ``OUTILS`` ; il dit à quel point il convient au
contenu d'un partage (``pertinence``), fournit son panneau d'interface (``panneau``) et, s'il le veut, ses commandes
(``cli``).  Le premier outil est « Parallaxe (Lune, ISS) » ; d'autres (photométrie, astrométrie d'astéroïde,
spectroscopie…) s'ajoutent sans toucher au reste : un sous-paquet de plus, une ligne dans ``_charger``.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Outil:
    id: str = ''
    cle_nom: str = ''              # clé de texte du nom
    cle_description: str = ''      # clé de texte de la description

    def pertinence(self, structure, tableaux: list) -> float:
        """0 (sans rapport) à 1 (fait pour ce partage), d'après les noms, les cibles, les tableaux."""
        return 0.0

    def panneau(self, parent, contexte):
        """QWidget de l'outil ; `contexte` : le panneau du module (session, structure, téléchargements)."""
        raise NotImplementedError

    def raisons(self, structure, tableaux: list) -> list[str]:
        """Clés de texte qui expliquent la pertinence (montrées à l'utilisateur)."""
        return []


OUTILS: list[Outil] = []


def _charger():
    if OUTILS:
        return
    from .parallaxe import OutilParallaxe
    OUTILS.append(OutilParallaxe())


def outils() -> list[Outil]:
    _charger()
    return list(OUTILS)


def outil(ident: str) -> Outil | None:
    return next((o for o in outils() if o.id == ident), None)


def detecter(structure, tableaux: list) -> list[tuple[Outil, float]]:
    """Outils triés du plus au moins pertinent pour ce partage."""
    r = [(o, o.pertinence(structure, tableaux)) for o in outils()]
    return sorted(r, key=lambda x: -x[1])
