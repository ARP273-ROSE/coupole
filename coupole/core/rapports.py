"""Rapports d'incident : le module commun du kit (`reporting.py`, identique au gabarit), branché sur Coupole.

Le kit fait le travail (installation, preuve de vie, plantage, crash natif, gel, signalement écrit ; accord demandé
au premier lancement ; file d'attente locale ; anonymisation : ni nom de machine, ni nom d'utilisateur, ni chemin
complet ; identifiant aléatoire de l'installation).  Ce module ajoute ce qui est propre à Coupole :

- le dossier de données de Coupole (hors du dossier d'installation) et l'en-tête « coupole/x.y.z » ;
- la reprise sans perte de l'accord donné aux versions ≤ 0.6 (réglage « rapports_autorises ») ;
- un rapport jamais plus gros que RAPPORT_MAX ;
- les crochets d'exceptions (fil principal et fils secondaires) et faulthandler, armé AVANT de relever la trace du
  crash précédent (mise de côté sous un autre nom) : un plantage pendant le relevé lui-même laisse aussi sa trace ;
- aucun envoi vers le vrai point de collecte pendant les essais (COUPOLE_SANS_RESEAU, COUPOLE_RAPPORTS_URL).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
import traceback
from pathlib import Path

from .. import __version__
from . import config
from .maj import kit

log = logging.getLogger(__name__)

APPLICATION = 'coupole'
RAPPORT_MAX = 64_000       # octets : un rapport ne dépasse jamais cette taille (charge réseau, vie privée)
GENRES = ('installation', 'demarrage', 'plantage', 'crash_natif', 'gel', 'manuel')
#: point de collecte factice des essais : rien ne part vers le vrai serveur
COLLECTE_DESACTIVEE = 'https://127.0.0.1:9/rapports-desactives'


def _r():
    return kit('reporting')


def init(dossier: Path | None = None) -> None:
    """Prépare le module commun : dossier de données de Coupole, nom et version, accord repris des anciennes
    versions, point de collecte des essais."""
    r = _r()
    base = Path(dossier or config.dossier_config())
    r.init(base, application=APPLICATION, version=__version__)
    url = os.environ.get('COUPOLE_RAPPORTS_URL')
    if url:
        r.ENDPOINT = url
    elif os.environ.get('COUPOLE_SANS_RESEAU'):
        r.ENDPOINT = COLLECTE_DESACTIVEE
    # Accord donné à Coupole ≤ 0.6 (config, « rapports_autorises ») : repris tel quel, une seule fois.
    reglages = config.reglages()
    if r.consentement() is None:
        ancien = reglages['rapports_autorises']
        if ancien is not None:
            r.definir_consentement(bool(ancien))
            log.info('report consent carried over from settings: %s', bool(ancien))
    # même identifiant aléatoire d'installation qu'avant (continuité des rapports d'un même poste)
    if not r._reglages.get('id_installation') and reglages['id_installation']:
        r._reglages['id_installation'] = 'install-' + str(reglages['id_installation'])
        for cle in ('installee_le', 'dernier_demarrage'):
            if reglages.get(cle) and not r._reglages.get(cle):
                r._reglages[cle] = reglages.get(cle)
        r._ecrire_reglages()


def dossier_rapports() -> Path | None:
    return getattr(_r(), '_dossier', None)


def consentement():
    """True, False, ou None tant que la question n'a pas été posée."""
    return _r().consentement()


def definir_consentement(accepte: bool) -> None:
    _r().definir_consentement(bool(accepte))
    try:                                            # le réglage visible dans les Préférences suit
        config.reglages()['rapports_autorises'] = bool(accepte)
    except Exception:
        pass


def anonymiser(texte) -> str:
    return _r().anonymiser(texte if isinstance(texte, str) or texte is None else str(texte))


def machine() -> dict:
    """Ce que le module commun joint à chaque rapport (identifiant aléatoire, jamais le nom de la machine)."""
    return _r()._machine()


def _type_installation() -> str:
    from . import maj
    try:
        return maj.type_installation()
    except Exception:
        return '?'


def envoyer(genre: str, **champs) -> dict:
    """Constitue un rapport et le transmet en fond si l'utilisateur l'a accepté (sinon il reste en file locale)."""
    genre = genre if genre in GENRES else 'autre'
    champs.setdefault('paquet', _type_installation())
    # borne de taille : les plus longs textes sont raccourcis (par le début : le bas d'une trace compte) jusqu'à tenir
    for _ in range(12):
        if len(json.dumps(champs, ensure_ascii=False, default=str).encode('utf-8')) <= RAPPORT_MAX - 4000:
            break
        cle = max((k for k, v in champs.items() if isinstance(v, str)), key=lambda k: len(champs[k]), default=None)
        if cle is None:
            break
        champs[cle] = '[…] ' + champs[cle][-(len(champs[cle]) // 2):]
    return _r().envoyer(genre, **champs)


def vider_file() -> int:
    return _r().vider_file()


def reprendre_file_en_fond() -> None:
    _r().reprendre_file_en_fond()


def signaler_demarrage() -> None:
    """Preuve de vie, au plus une fois par jour (installation la première fois)."""
    r = _r()
    r.signaler_demarrage(premier=not r._reglages.get('installee_le'), paquet=_type_installation())


def signaler_plantage(tb_texte: str, **champs) -> dict:
    return _r().signaler_plantage(tb_texte[-8000:], **champs)


def relever_crash_natif(chemin) -> bool:
    return _r().relever_crash_natif(chemin)


def Vigie(seuil=10.0, periode=2.0):
    """Vigie du module commun : le fil graphique appelle battre() régulièrement."""
    return _r().Vigie(seuil=seuil, periode=periode)


_fichier_faulthandler = None


def armer_faulthandler(chemin: Path) -> None:
    """faulthandler armé AVANT de relever la trace du crash précédent : celle-ci est d'abord mise de côté sous un
    autre nom (l'ouverture du fichier en écriture la viderait), puis relevée ; un plantage pendant le relevé (ou
    n'importe quand ensuite) écrit sa trace dans le fichier armé."""
    global _fichier_faulthandler
    chemin = Path(chemin)
    precedent = chemin.with_name(chemin.stem + '.precedent' + chemin.suffix)
    try:
        if chemin.exists() and chemin.stat().st_size > 0:
            os.replace(chemin, precedent)
    except OSError:
        pass
    try:
        import faulthandler
        _fichier_faulthandler = open(chemin, 'w', encoding='utf-8')
        faulthandler.enable(file=_fichier_faulthandler, all_threads=True)
    except Exception:
        pass
    try:
        relever_crash_natif(precedent)
    except Exception:
        pass


def installer_crochets(chemin_faulthandler: Path | None = None) -> None:
    """Exceptions non rattrapées (fil principal et fils secondaires) + crash natif (faulthandler)."""
    ancien = sys.excepthook

    def crochet(t, v, tb):
        texte = ''.join(traceback.format_exception(t, v, tb))
        log.error('uncaught exception:\n%s', texte)
        try:
            signaler_plantage(texte)
        except Exception:
            pass
        ancien(t, v, tb)
    sys.excepthook = crochet

    def crochet_fil(args):
        crochet(args.exc_type, args.exc_value, args.exc_traceback)
    threading.excepthook = crochet_fil
    if chemin_faulthandler is not None:
        armer_faulthandler(chemin_faulthandler)
