"""Les archives connues de Coupole, dans l'ordre d'affichage.  Ajouter une archive : une classe `Archive`
(``base.py``) et une ligne ici ; ses adresses dans ``coupole/donnees/sources.json``."""
from __future__ import annotations

from .base import Archive, CompteRequis, NonPrisEnCharge, Requete, Resultat  # noqa: F401
from .eso import Eso
from .irsa import Irsa
from .mast import Mast
from .planetes import Opus, PdsAtlas
from .sol import Gemini, Koa, Noirlab, Sdss, Smoka

ARCHIVES: dict[str, Archive] = {a.id: a for a in (Mast(), Eso(), Irsa(), Noirlab(), Koa(), Sdss(), Gemini(), Smoka(),
                                                  Opus(), PdsAtlas())}
PAR_DEFAUT = ('mast', 'eso', 'irsa')          # étape 1 : interrogées sans rien choisir


def archive(ident: str) -> Archive:
    return ARCHIVES[ident]


def missions() -> list[tuple[str, str]]:
    """[(mission, archive)] de toutes les archives."""
    return [(m, a.id) for a in ARCHIVES.values() for m in a.missions]


def archive_de_mission(mission: str) -> str | None:
    for m, a in missions():
        if m.lower() == (mission or '').lower():
            return a
    return None
