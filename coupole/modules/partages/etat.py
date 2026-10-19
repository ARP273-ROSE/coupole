"""Partages mémorisés (nom libre, lien) et état de chaque partage (dernière liste vue : nouveautés), en local.

Le lien d'un partage public donne accès à son contenu : il est gardé dans le dossier de réglages de l'utilisateur
(``partages.json``, droits 600 sous Linux et macOS), jamais ailleurs, jamais envoyé dans un rapport d'incident.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ...core import config
from .webdav import Entree, Partage, analyser_lien

_verrou = threading.Lock()


@dataclass
class PartageMemorise:
    nom: str
    lien: str                         # lien complet tel que collé (jeton compris)
    mot_de_passe: str = ''
    ajoute: float = 0.0
    derniere_visite: float = 0.0
    droits: list = field(default_factory=list)
    outil: str = ''                   # outil d'analyse choisi (« parallaxe »…) ; '' = détecté

    @property
    def ident(self) -> str:
        p = self.partage()
        return hashlib.sha1(('%s|%s' % (p.serveur, p.jeton)).encode()).hexdigest()[:12]

    def partage(self) -> Partage:
        return analyser_lien(self.lien, mot_de_passe=self.mot_de_passe)


def _chemin() -> Path:
    return config.dossier_config() / 'partages.json'


def dossier_partage(ident: str) -> Path:
    p = config.dossier_cache() / 'partages' / ident
    p.mkdir(parents=True, exist_ok=True)
    return p


def lister() -> list[PartageMemorise]:
    with _verrou:
        d = config.lire_json_protege(_chemin(), {'partages': []})
    out = []
    for x in d.get('partages', []):
        try:
            out.append(PartageMemorise(**{k: v for k, v in x.items() if k in PartageMemorise.__dataclass_fields__}))
        except TypeError:
            continue
    return out


def _ecrire(liste: list[PartageMemorise]):
    p = _chemin()
    with _verrou:
        config.ecrire_json_atomique(p, {'format': 1, 'partages': [asdict(x) for x in liste]})
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass


def ajouter(nom: str, lien: str, mot_de_passe: str = '', droits=None) -> PartageMemorise:
    """Ajoute (ou met à jour : même serveur et même jeton) un partage ; le nom est rendu unique."""
    partage = analyser_lien(lien, mot_de_passe=mot_de_passe)
    liste = lister()
    nouveau = PartageMemorise(nom.strip() or partage.serveur.split('//')[-1], partage.lien(), mot_de_passe,
                              time.time(), 0.0, list(droits or []))
    for k, x in enumerate(liste):
        if x.ident == nouveau.ident:
            nouveau.ajoute, nouveau.derniere_visite, nouveau.outil = x.ajoute, x.derniere_visite, x.outil
            liste[k] = nouveau
            _ecrire(liste)
            return nouveau
    noms = {x.nom for x in liste}
    base, n = nouveau.nom, 2
    while nouveau.nom in noms:
        nouveau.nom = '%s (%d)' % (base, n)
        n += 1
    liste.append(nouveau)
    _ecrire(liste)
    return nouveau


def retirer(ident: str) -> bool:
    """Oublie un partage (dans Coupole seulement : rien n'est touché sur le serveur)."""
    liste = lister()
    reste = [x for x in liste if x.ident != ident]
    if len(reste) == len(liste):
        return False
    _ecrire(reste)
    return True


def renommer(ident: str, nom: str) -> None:
    liste = lister()
    for x in liste:
        if x.ident == ident and nom.strip():
            x.nom = nom.strip()
    _ecrire(liste)


def modifier(ident: str, **champs) -> None:
    liste = lister()
    for x in liste:
        if x.ident == ident:
            for k, v in champs.items():
                if k in PartageMemorise.__dataclass_fields__:
                    setattr(x, k, v)
    _ecrire(liste)


def trouver(nom_ou_ident: str) -> PartageMemorise | None:
    for x in lister():
        if nom_ou_ident in (x.nom, x.ident):
            return x
    return None


# ------------------------------------------------------------------ liste vue (nouveautés)
def liste_vue(ident: str) -> list[Entree] | None:
    p = dossier_partage(ident) / 'liste.json'
    d = config.lire_json_protege(p, None)
    if not d:
        return None
    return [Entree.de_dict(x) for x in d.get('entrees', [])]


def vus(ident: str) -> set | None:
    """Chemins vus à la dernière visite marquée « vue » (None : jamais visité)."""
    d = config.lire_json_protege(dossier_partage(ident) / 'vus.json', None)
    return set(d.get('chemins', [])) if d else None


def memoriser_liste(ident: str, entrees: list[Entree]) -> None:
    config.ecrire_json_atomique(dossier_partage(ident) / 'liste.json',
                                {'date': time.time(), 'entrees': [e.vers_dict() for e in entrees]}, indent=None)


def marquer_vus(ident: str, entrees: list[Entree]) -> None:
    config.ecrire_json_atomique(dossier_partage(ident) / 'vus.json',
                                {'date': time.time(), 'chemins': [e.chemin for e in entrees if not e.dossier]},
                                indent=None)
    modifier(ident, derniere_visite=time.time())


def lire_json(ident: str, nom: str, defaut=None):
    return config.lire_json_protege(dossier_partage(ident) / nom, defaut)


def ecrire_json(ident: str, nom: str, objet) -> None:
    config.ecrire_json_atomique(dossier_partage(ident) / nom, objet, indent=None)


def exporter_texte(x: PartageMemorise) -> str:
    return json.dumps({'nom': x.nom, 'serveur': x.partage().serveur}, ensure_ascii=False)
