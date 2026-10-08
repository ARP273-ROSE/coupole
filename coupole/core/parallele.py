"""Choix du parallélisme selon la machine.

Deux ressources différentes, deux réglages :

* le **réseau** (téléchargements) : des fils d'exécution, peu nombreux, parce
  que le serveur de l'Observatoire est public et partagé.  Le plafond ne dépend
  pas de la machine : 3 par défaut, 4 au plus, 2 en mode économe ;
* le **calcul** (conversions) : des processus (multiprocessing), bornés à la
  fois par les cœurs physiques (moins un, laissé à l'interface et au système)
  et par la mémoire disponible, à raison de ``MEMOIRE_PAR_CONVERSION_MO`` par
  conversion en cours (pic mesuré sur une image IRIS de 4096 x 4096 pixels,
  voir PROGRESSION.md).

Mode économe (automatique sous 4 Go de mémoire ou 2 cœurs, ou forcé) : une
seule conversion et deux téléchargements.
"""
from __future__ import annotations

from dataclasses import dataclass

from .machine import Machine

TELECHARGEMENTS_DEFAUT = 3
TELECHARGEMENTS_MAX = 4           # politesse envers un serveur public
CONVERSIONS_MAX = 16
MEMOIRE_PAR_CONVERSION_MO = 500   # pic mesuré : IRIS 4096² float32 ≈ 440 Mo par processus ; cf. PROGRESSION.md
PART_MEMOIRE = 0.5                # on ne prévoit d'utiliser que la moitié de la mémoire libre


@dataclass
class Plan:
    telechargements: int
    conversions: int
    econome: bool
    raison: str                    # clé de traduction expliquant la limite retenue


def planifier(m: Machine, telechargements: int = 0, conversions: int = 0,
              econome: bool | None = None) -> Plan:
    """Calcule le plan ; `telechargements`/`conversions` > 0 imposent une valeur (bridage manuel)."""
    auto_econome = (0 < m.memoire_totale_mo < 4096) or m.coeurs_physiques <= 2
    eco = auto_econome if econome is None else bool(econome)
    if eco:
        t, c, raison = 2, 1, 'parallele_raison_econome'
    else:
        par_coeurs = max(1, m.coeurs_physiques - 1)
        dispo = m.memoire_disponible_mo or m.memoire_totale_mo // 2
        par_memoire = max(1, int(dispo * PART_MEMOIRE // MEMOIRE_PAR_CONVERSION_MO)) if dispo else 1
        c = max(1, min(par_coeurs, par_memoire, CONVERSIONS_MAX))
        raison = 'parallele_raison_memoire' if par_memoire < par_coeurs else 'parallele_raison_coeurs'
        t = TELECHARGEMENTS_DEFAUT
    if telechargements > 0:
        t = min(telechargements, TELECHARGEMENTS_MAX)
        raison = 'parallele_raison_manuel'
    if conversions > 0:
        c = min(conversions, CONVERSIONS_MAX)
        raison = 'parallele_raison_manuel'
        # Même imposé à la main, le nombre de processus reste dans le budget mémoire : sinon le système
        # échange ou tue un processus (OOM), ce que l'utilisateur n'a certainement pas voulu.
        dispo = m.memoire_disponible_mo or m.memoire_totale_mo // 2
        if dispo:
            plafond = max(1, int(dispo * PART_MEMOIRE // MEMOIRE_PAR_CONVERSION_MO))
            if c > plafond:
                c, raison = plafond, 'parallele_raison_memoire'
    return Plan(telechargements=t, conversions=c, econome=eco, raison=raison)


def budget_memoire_mo(plan: Plan) -> int:
    """Mémoire que le plan peut engager au pire (processus de conversion x pic mesuré)."""
    return plan.conversions * MEMOIRE_PAR_CONVERSION_MO
