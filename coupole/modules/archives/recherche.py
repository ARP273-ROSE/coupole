"""Recherche dans plusieurs archives à la fois : résolution du nom, une tâche par archive, filtres communs, tri.

Jamais dans le fil graphique (l'interface passe par une `Tache`).  Une archive injoignable, qui exige un compte ou
qui n'a pas d'interface n'empêche pas les autres de répondre : son `Resultat` porte l'erreur.
"""
from __future__ import annotations

import concurrent.futures as F
import math
import re
import threading
import time

from ...core import enligne, reseau
from .services import ARCHIVES, PAR_DEFAUT, CompteRequis, NonPrisEnCharge, Requete, Resultat
from .services.base import filtrer, lignes_recues, remettre_compte

RE_SEXA = re.compile(r'^\s*(\d{1,2})[:h ]\s*(\d{1,2})[:m ]\s*(\d{1,2}(?:\.\d*)?)s?\s*,?\s*([+-−]?)\s*(\d{1,2})[:d° ]\s*'
                     r'(\d{1,2})[:\'′m ]\s*(\d{1,2}(?:\.\d*)?)["″s]?\s*$')
RE_DEG = re.compile(r'^\s*(\d{1,3}(?:\.\d*)?)\s*[, ]\s*([+-−]?\d{1,2}(?:\.\d*)?)\s*$')


def lire_coordonnees(texte: str) -> tuple[float, float] | None:
    """« 83.822 -5.391 », « 83.822, -5.391 » (degrés) ou « 05:35:17.3 -05:23:28 » / « 5h35m17s -5d23m28s »."""
    t = (texte or '').strip()
    m = RE_DEG.match(t)
    if m:
        ra, dec = float(m.group(1)), float(m.group(2).replace('−', '-'))
        if 0 <= ra < 360 and -90 <= dec <= 90:
            return ra, dec
        return None
    m = RE_SEXA.match(t)
    if m:
        h, mi, s, signe, d, dm, ds = m.groups()
        ra = 15 * (int(h) + int(mi) / 60 + float(s) / 3600)
        dec = int(d) + int(dm) / 60 + float(ds) / 3600
        if signe in ('-', '−'):
            dec = -dec
        if 0 <= ra < 360 and -90 <= dec <= 90:
            return ra, dec
    return None


def resoudre(nom: str, delai: float = 10.0) -> dict:
    """{'ra', 'dec', 'nom', 'service'} ; lève LookupError (introuvable) ou reseau.ServiceInjoignable."""
    c = lire_coordonnees(nom)
    if c:
        return {'ra': c[0], 'dec': c[1], 'nom': '', 'service': 'coordonnees'}
    r = enligne.fiche_objet(nom, cat='ciel', delai=delai, en_ligne=True)
    f = r.get('fiche') or {}
    if r.get('etat') == 'hors_ligne':
        raise reseau.ServiceInjoignable(r.get('erreur') or 'offline')
    if f.get('ra') is None or f.get('dec') is None:
        raise LookupError(nom)
    return {'ra': float(f['ra']), 'dec': float(f['dec']), 'nom': f.get('nom') or nom, 'service': f.get('service', '')}


def chercher(q: Requete, archives: tuple | None = None, arret: threading.Event | None = None,
             rapporter=None, paralleles: int = 4) -> list[Resultat]:
    """Interroge les archives (par défaut celles de l'étape 1) ; rend un `Resultat` par archive, observations
    filtrées par `filtrer` et triées par distance puis date."""
    if not (archives or q.archives) and q.missions:      # missions choisies : les archives qui les servent
        from .services import archive_de_mission
        archives = tuple(dict.fromkeys(a for a in (archive_de_mission(m) for m in q.missions) if a))
    ids = [a for a in (archives or q.archives or PAR_DEFAUT) if a in ARCHIVES]
    rapporter = rapporter or (lambda **k: None)

    def une(ident):
        a = ARCHIVES[ident]
        t0 = time.monotonic()
        res = Resultat(archive=ident, observations=[])
        if arret is not None and arret.is_set():
            return res
        if a.celeste and q.ra is None:
            return res
        if not a.celeste and not q.cible:
            return res
        rapporter(genre='archive_debut', archive=ident)
        try:
            remettre_compte()
            obs = a.chercher(q)
            res.tronque = lignes_recues() > q.limite or len(obs) > q.limite
            obs = filtrer(obs[:q.limite] if len(obs) > q.limite else obs, q)
            res.observations = obs
        except CompteRequis as e:
            res.compte_requis, res.erreur = True, str(e)
        except NonPrisEnCharge as e:
            res.non_pris_en_charge, res.erreur = True, str(e)
        except Exception as e:                    # réseau, réponse illisible, erreur ADQL : l'archive suivante
            res.erreur = '%s: %s' % (type(e).__name__, e)
        res.secondes = time.monotonic() - t0
        rapporter(genre='archive_fin', archive=ident, n=len(res.observations), erreur=res.erreur)
        return res

    with F.ThreadPoolExecutor(max_workers=max(1, min(paralleles, len(ids) or 1))) as ex:
        resultats = list(ex.map(une, ids))
    return resultats


def toutes(resultats: list[Resultat]) -> list[dict]:
    """Observations de tous les résultats, triées (distance au centre, puis mission, filtre, date) et sans doublon
    d'identifiant."""
    vus, out = set(), []
    for r in resultats:
        for o in r.observations:
            if o['id'] not in vus:
                vus.add(o['id'])
                out.append(o)
    out.sort(key=lambda o: (o['distance'] if o['distance'] is not None else math.inf, o['mission'],
                            o['lambda_nm'] if o['lambda_nm'] is not None else math.inf, o['debut']))
    return out


def requete(nom: str = '', rayon_arcmin: float = 3.0, **kw) -> Requete:
    """Requête depuis un nom ou des coordonnées (résolus ici, en ligne : à appeler hors du fil graphique)."""
    q = Requete(nom=nom, rayon=rayon_arcmin / 60.0, **kw)
    if nom and not q.cible:
        r = resoudre(nom)
        q.ra, q.dec = r['ra'], r['dec']
    return q
