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


RE_CATALOGUE = re.compile(r'^\s*(m|ngc|ic|arp|ugc|pgc|sh\s*2-?|abell|hcg|caldwell|c|barnard|b|lbn|ldn|vdb|mrk|'
                          r'markarian|messier)\s*-?\s*(\d+[a-z]?)\s*$', re.I)
CATALOGUES = {'m': 'M', 'messier': 'M', 'ngc': 'NGC', 'ic': 'IC', 'arp': 'Arp', 'ugc': 'UGC', 'pgc': 'PGC',
              'abell': 'Abell', 'hcg': 'HCG', 'caldwell': 'Caldwell', 'c': 'Caldwell', 'barnard': 'Barnard',
              'b': 'Barnard', 'lbn': 'LBN', 'ldn': 'LDN', 'vdb': 'VdB', 'mrk': 'Mrk', 'markarian': 'Mrk'}


def variantes_nom(nom: str) -> list[str]:
    """Écritures à essayer auprès de SIMBAD/Sesame : nom usuel (« Piliers de la Création » → « M 16 »), numéro
    de catalogue détaché et dans la casse attendue (« m16 », « ngc6611 », « sh2-155 », « arp273 »)."""
    from .celebres import alias
    out = []
    a = alias(nom)
    if a:
        out.append(a)
    m = RE_CATALOGUE.match(nom or '')
    if m:
        cat = re.sub(r'\s+', '', m.group(1).lower())
        if cat.startswith('sh2'):
            out.append('Sh 2-%s' % m.group(2))
        else:
            out.append('%s %s' % (CATALOGUES.get(cat, m.group(1)), m.group(2).upper()))
    propre = ' '.join((nom or '').split())
    if propre:
        out.append(propre)
    return list(dict.fromkeys(out))


def interpreter(texte: str) -> dict:
    """Ce que l'on a tapé : {'genre': 'vide'|'coordonnees'|'corps'|'nom', 'ra', 'dec', 'corps', 'noms'}.
    Un corps du Système solaire (« jupiter », « Saturne », « Encelade ») se cherche par nom de cible."""
    from .corps import reconnaitre
    t = (texte or '').strip()
    if not t:
        return {'genre': 'vide'}
    c = lire_coordonnees(t)
    if c:
        return {'genre': 'coordonnees', 'ra': c[0], 'dec': c[1]}
    corps = reconnaitre(t)
    if corps is not None:
        return {'genre': 'corps', 'corps': corps}
    noms = variantes_nom(t)
    c = lire_coordonnees(noms[0]) if noms else None
    if c:
        return {'genre': 'coordonnees', 'ra': c[0], 'dec': c[1], 'alias': noms[0]}
    return {'genre': 'nom', 'noms': noms}


def resoudre(nom: str, delai: float = 10.0) -> dict:
    """{'ra', 'dec', 'nom', 'service'} ; lève LookupError (introuvable) ou reseau.ServiceInjoignable.  Essaie le nom
    usuel, le numéro de catalogue réécrit, puis le nom tel quel (SIMBAD, puis Sesame qui interroge aussi NED et
    VizieR)."""
    i = interpreter(nom)
    if i['genre'] == 'coordonnees':
        return {'ra': i['ra'], 'dec': i['dec'], 'nom': '', 'service': 'coordonnees'}
    if i['genre'] == 'corps':
        raise LookupError(nom)
    noms = i.get('noms') or [nom]
    derniere = None
    for n in noms:
        r = enligne.fiche_objet(n, cat='ciel', delai=delai, en_ligne=True)
        f = r.get('fiche') or {}
        if r.get('etat') == 'hors_ligne':
            derniere = reseau.ServiceInjoignable(r.get('erreur') or 'offline')
            continue
        if f.get('ra') is not None and f.get('dec') is not None:
            return {'ra': float(f['ra']), 'dec': float(f['dec']), 'nom': f.get('nom') or n,
                    'service': f.get('service', '')}
    if derniere is not None:
        raise derniere
    raise LookupError(nom)


def suggestions(debut: str, langue: str = 'fr', n: int = 10) -> list[str]:
    """Propositions pendant la frappe : corps du Système solaire, noms usuels et programmes célèbres."""
    from .celebres import noms_usuels
    from .corps import normaliser, suggestions as s_corps
    d = normaliser(debut)
    if len(d) < 2:
        return []
    out = s_corps(debut, langue, n)
    for nom in noms_usuels():
        if normaliser(nom).startswith(d) and nom not in out:
            out.append(nom)
    return out[:n]


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
        if a.celeste and q.ra is None and not (a.par_corps and q.cible):
            return res
        if not a.celeste and not q.cible:
            return res
        rapporter(genre='archive_debut', archive=ident)
        try:
            remettre_compte()
            obs = a.chercher(q)
            res.tronque = lignes_recues() > q.limite or len(obs) > q.limite
            obs = filtrer(tronquer_equitable(obs, q.limite), q)
            progs = {str(p).strip() for p in (q.extra.get('programmes') or ()) if str(p).strip()}
            if progs:                                       # programme célèbre choisi dans le catalogue
                obs = [o for o in obs if str(o.get('programme') or '').strip() in progs]
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


def tronquer_equitable(obs: list[dict], n: int) -> list[dict]:
    """Au plus `n` observations, réparties entre les missions d'une même archive (OPUS rend Voyager puis Cassini :
    couper la liste à `n` supprimait toutes les images de Cassini — « saturne » ne trouvait rien pour Cassini)."""
    if len(obs) <= n:
        return obs
    par_mission: dict[str, list] = {}
    for o in obs:
        par_mission.setdefault(o.get('mission', ''), []).append(o)
    if len(par_mission) == 1:
        return obs[:n]
    out, listes, k = [], list(par_mission.values()), 0
    while len(out) < n:
        ajoute = False
        for l in listes:
            if k < len(l) and len(out) < n:
                out.append(l[k])
                ajoute = True
        if not ajoute:
            break
        k += 1
    garde = {id(o) for o in out}
    return [o for o in obs if id(o) in garde]


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
    from .produits import regrouper
    return regrouper(out)


def requete(nom: str = '', rayon_arcmin: float = 3.0, **kw) -> Requete:
    """Requête depuis un nom, un corps du Système solaire ou des coordonnées (résolus ici, en ligne : à appeler
    hors du fil graphique).  Un corps donne `cible` (recherche par nom de cible), le reste des coordonnées."""
    q = Requete(nom=nom, rayon=rayon_arcmin / 60.0, **kw)
    if nom and not q.cible:
        i = interpreter(nom)
        if i['genre'] == 'corps':
            q.cible = i['corps']['en']
            return q
        r = resoudre(nom)
        q.ra, q.dec = r['ra'], r['dec']
    return q


def archives_pour(q: Requete, cochees: tuple) -> tuple:
    """Archives à interroger : pour un corps du Système solaire, celles qui cherchent par nom de cible (MAST,
    Voyager/Cassini, Juno), même non cochées ; sinon les archives célestes cochées."""
    from .services import ARCHIVES
    if q.ra is None and q.cible:
        return tuple(a for a in ARCHIVES if not ARCHIVES[a].celeste or ARCHIVES[a].par_corps)
    return tuple(a for a in cochees if ARCHIVES[a].celeste)
