"""Stockage de la sauvegarde commune (format de Coupole Web, `sauvegarde.py`) : fichier JSON dans le dossier de
configuration de l'utilisateur (`sauvegarde.json`), écriture atomique (fichier temporaire + os.replace) avec copie de
la version précédente (`sauvegarde.json.prec`), différée de 400 ms puis immédiate à la fermeture.  Lecture tolérante :
un fichier illisible est mis de côté ; une sauvegarde d'une version plus récente n'est jamais écrasée (l'application
travaille alors sur un document vide en mémoire et le signale).

Première ouverture en 0.6.0 : les réglages des animations gardés jusque-là dans interface.json (« modules.anim.<id> »)
sont repris (migration de la version 0)."""
from __future__ import annotations

import logging
from pathlib import Path

from ....core import config
from . import sauvegarde as S

log = logging.getLogger(__name__)
NOM = 'sauvegarde.json'


def application() -> str:
    try:
        from .... import __version__ as v
    except Exception:
        v = '0'
    return 'coupole/' + str(v)


class Stockage:
    def __init__(self, chemin: Path | None = None):
        self.chemin = Path(chemin) if chemin else config.dossier_config() / NOM
        self.lecture_seule = False
        self.abonnes = []
        self._minuteur = None
        self.doc = self._charger()

    # ------------------------------------------------------------ lecture
    def _charger(self) -> dict:
        brut = config.lire_json_protege(self.chemin, None, dict)
        if brut is None:
            brut = self._ancien_format()
        s = S.migrer(brut, application()) if brut is not None else S.vide(application())
        if s is None:                                  # version future : on ne l'écrase pas
            self.lecture_seule = True
            log.warning('%s written by a newer version: kept untouched', self.chemin.name)
            return S.vide(application())
        return s

    @staticmethod
    def _ancien_format():
        """Réglages des animations de l'interface (version 0) regroupés pour `migrer`."""
        try:
            from ....core.etat_interface import etat
            anim = etat().lire('modules.anim', None)
        except Exception:
            return None
        if not isinstance(anim, dict):
            return None
        reglages = {k: v for k, v in anim.items() if isinstance(v, dict)}
        return {'version': 0, 'reglages': reglages} if reglages else None

    # ------------------------------------------------------------ écriture
    def modifie(self):
        self.doc['modifie'] = S.maintenant()
        self.doc['application'] = application()
        self._programmer()
        for f in list(self.abonnes):
            try:
                f()
            except Exception:                          # un abonné défaillant n'empêche rien
                log.exception('abonné de la sauvegarde')

    def _programmer(self):
        try:
            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QApplication
        except ImportError:
            return self.ecrire()
        if QApplication.instance() is None:
            return self.ecrire()
        if self._minuteur is None:
            self._minuteur = QTimer()
            self._minuteur.setSingleShot(True)
            self._minuteur.setInterval(400)
            self._minuteur.timeout.connect(self.ecrire)
            QApplication.instance().aboutToQuit.connect(self.ecrire)
        if not self._minuteur.isActive():              # pas relancé à chaque changement
            self._minuteur.start()

    def ecrire(self) -> bool:
        if self._minuteur is not None:
            self._minuteur.stop()
        if self.lecture_seule:
            return False
        try:
            if self.chemin.exists():
                prec = self.chemin.with_name(NOM + '.prec')
                try:
                    prec.write_bytes(self.chemin.read_bytes())   # copie de la version précédente
                except OSError:
                    pass
            config.ecrire_atomique(self.chemin, S.exporter(self.doc))
            return True
        except OSError as e:
            log.warning('%s not written: %s', self.chemin.name, e)
            return False

    def remplacer(self, s: dict):
        self.doc = s
        self.modifie()

    def abonner(self, f):
        self.abonnes.append(f)
        return lambda: self.abonnes.remove(f) if f in self.abonnes else None

    # ------------------------------------------------------------ raccourcis
    def reglages_animation(self, ident: str) -> dict:
        return dict((self.doc['animations'].get(ident) or {}).get('reglages') or {})

    def memoriser_reglages(self, ident: str, reglages: dict):
        v = S.reglages_valides(reglages)
        ancien = (self.doc['animations'].get(ident) or {}).get('reglages')
        if v == (ancien or {}):
            return
        if v:
            self.doc['animations'][ident] = {'reglages': v, 'modifie': S.maintenant()}
        else:
            self.doc['animations'].pop(ident, None)
        self.modifie()

    def exporter_vers(self, chemin) -> None:
        config.ecrire_atomique(chemin, S.exporter(self.doc))

    @staticmethod
    def nom_export(suffixe: str = '') -> str:
        import time
        return time.strftime('coupole-sauvegarde-%Y-%m-%d-%H%M') + suffixe + '.json'


_UNIQUE: Stockage | None = None


def stockage() -> Stockage:
    global _UNIQUE
    if _UNIQUE is None:
        _UNIQUE = Stockage()
    return _UNIQUE


def reinitialiser_pour_tests(chemin=None):
    global _UNIQUE
    _UNIQUE = Stockage(chemin) if chemin else None
