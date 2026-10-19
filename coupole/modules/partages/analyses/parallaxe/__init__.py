"""Outil « Parallaxe (Lune, ISS) » : paires simultanées, distance de la Lune, altitude de l'ISS, rapport."""
from __future__ import annotations

from .. import Outil
from ...structure import normaliser


class OutilParallaxe(Outil):
    def __init__(self):
        super().__init__('parallaxe', 'pc_outil_nom', 'pc_outil_description')

    def raisons(self, structure, tableaux: list) -> list[str]:
        out = []
        if structure is None:
            return out
        textes = ' '.join(normaliser(f.chemin) for f in structure.fichiers[:5000])
        if 'parallax' in textes:
            out.append('pc_raison_nom')
        if 'lune' in structure.cibles or 'iss' in structure.cibles:
            out.append('pc_raison_cibles')
        if any({'latitude', 'longitude'} <= set(t.colonnes) for t in tableaux):
            out.append('pc_raison_tableau')
        if len(structure.observateurs) >= 2:
            out.append('pc_raison_observateurs')
        return out

    def pertinence(self, structure, tableaux: list) -> float:
        poids = {'pc_raison_nom': 0.4, 'pc_raison_cibles': 0.3, 'pc_raison_tableau': 0.2,
                 'pc_raison_observateurs': 0.1}
        return min(1.0, sum(poids[r] for r in self.raisons(structure, tableaux)))

    def panneau(self, parent, contexte):
        from .gui import PanneauParallaxe
        return PanneauParallaxe(contexte, parent)
