"""Ce que l'on possède déjà : l'état du dossier de sortie rapporté à l'inventaire de la banque.

La source de vérité est ``<destination>/_traitement/etat.sqlite`` (statut ``ok`` / ``doublon`` / ``echec`` par
identifiant d'image, tenu par le pilote).  Ce module la lit en entier (quelques milliers de lignes, quelques
millisecondes), sans Qt, et répond : cette image est-elle possédée ?  combien d'images de cet objet a-t-on ?
que reste-t-il à télécharger ?  Il ne lève jamais : sans dossier, sans base ou base illisible → rien n'est possédé.

Statuts rendus (``STATUTS``) :
  * ``ok`` — convertie et rangée (possédée) ;
  * ``doublon`` — mêmes pixels qu'une image déjà convertie : écartée par le traitement (pas à retélécharger) ;
  * ``echec`` — le traitement a échoué (à retenter) ;
  * ``absente`` — jamais traitée (à télécharger).
"""
from __future__ import annotations

import collections as C
import json
import os

from .conversion import ident

STATUTS = ('ok', 'doublon', 'echec', 'absente')
POSSEDES = ('ok', 'doublon')                 # ce qui n'est plus à télécharger


def _uri_lecture_seule(chemin: str) -> str:
    """URI SQLite en lecture seule (chemins avec espaces, accents ou « ? », Windows compris)."""
    from pathlib import Path
    return Path(chemin).resolve().as_uri() + '?mode=ro'


class Possession:
    """Lecture seule de l'état d'une destination ; `vide()` quand il n'y a rien."""

    def __init__(self, dest: str = '', statuts: dict | None = None, details: dict | None = None):
        self.dest = dest or ''
        self.statuts: dict[str, str] = statuts or {}        # id → 'ok' | 'doublon' | 'echec'
        self.details: dict[str, dict] = details or {}       # id → {'date': …, 'chemin': …}
        self.existe = bool(self.statuts)

    @classmethod
    def vide(cls) -> 'Possession':
        return cls()

    @classmethod
    def lire(cls, dest) -> 'Possession':
        """Lit `<dest>/_traitement/etat.sqlite` ; jamais d'exception (base absente, verrouillée, abîmée → vide)."""
        dest = str(dest or '')
        chemin = os.path.join(dest, '_traitement', 'etat.sqlite') if dest else ''
        if not chemin or not os.path.exists(chemin):
            return cls(dest)
        import sqlite3
        statuts, details = {}, {}
        try:
            # URI en lecture seule : on ne crée rien, on ne modifie rien, on ne gêne pas un pilote qui écrit.
            db = sqlite3.connect(_uri_lecture_seule(chemin), uri=True, timeout=5)
            try:
                for i, statut, maj, info in db.execute('SELECT id, statut, maj, info FROM images'):
                    if statut not in ('ok', 'doublon', 'echec'):
                        continue
                    statuts[i] = statut
                    chemin_local = ''
                    if info:
                        try:
                            d = json.loads(info)
                            chemin_local = d.get('final') or ''
                        except ValueError:
                            pass
                    details[i] = {'date': (maj or '')[:19].replace('T', ' '), 'chemin': chemin_local}
            finally:
                db.close()
        except Exception:                        # sqlite3.Error, OSError : rien de possédé plutôt qu'un plantage
            return cls(dest)
        return cls(dest, statuts, details)

    # ---------------------------------------------------------------- par image
    def statut(self, x: dict) -> str:
        return self.statuts.get(ident(x), 'absente')

    def detail(self, x: dict) -> dict:
        """{'statut', 'date', 'chemin'} ; le chemin local est relatif à la destination quand il est dedans."""
        i = ident(x)
        d = self.details.get(i, {})
        chemin = d.get('chemin') or ''
        if chemin and self.dest:
            try:
                rel = os.path.relpath(chemin, self.dest)
                if not rel.startswith('..'):
                    chemin = rel
            except ValueError:                   # lecteurs différents sous Windows
                pass
        return {'statut': self.statuts.get(i, 'absente'), 'date': d.get('date', ''), 'chemin': chemin}

    def possedee(self, x: dict) -> bool:
        """Plus rien à télécharger pour cette image (convertie, ou écartée comme doublon de pixels)."""
        return self.statuts.get(ident(x)) in POSSEDES

    # ---------------------------------------------------------------- par objet, par sélection
    def manquantes(self, images) -> list[dict]:
        """Les images encore à télécharger : ni doublon de la base, ni possédées (un échec est à retenter)."""
        return [x for x in images if not x['doublon'] and not self.possedee(x)]

    def compte(self, images) -> dict:
        """{'possedees', 'doublons', 'echecs', 'absentes', 'total'} sur les images utiles (hors doublons de la base)."""
        c = C.Counter(self.statut(x) for x in images if not x['doublon'])
        return {'possedees': c['ok'], 'doublons': c['doublon'], 'echecs': c['echec'], 'absentes': c['absente'],
                'total': sum(c.values())}

    def compte_objets(self, images) -> dict[str, dict]:
        """Par objet canonique : le même compte que `compte`, en une passe sur l'inventaire."""
        par = {}
        for x in images:
            if x['doublon']:
                continue
            c = par.setdefault(x['objet'], {'possedees': 0, 'doublons': 0, 'echecs': 0, 'absentes': 0, 'total': 0})
            s = self.statut(x)
            c['possedees' if s == 'ok' else 'doublons' if s == 'doublon' else 'echecs' if s == 'echec' else 'absentes'] += 1
            c['total'] += 1
        return par

    @staticmethod
    def etat_objet(c: dict) -> str:
        """« complet » (tout possédé), « partiel », ou « aucun »."""
        if not c or c['total'] == 0:
            return 'aucun'
        traitees = c['possedees'] + c['doublons']
        if traitees >= c['total']:
            return 'complet'
        return 'partiel' if traitees > 0 else 'aucun'

    # ---------------------------------------------------------------- par lot
    def lots(self, images, infos_ok) -> dict[str, dict]:
        """Complétude des lots : pour chaque dossier de lot, poses converties et poses de la base pour la même clé
        (objet, télescope, filtre, et nuit pour un objet mobile) ; un objet fixe découpé en plusieurs champs compte
        ses lots ensemble (la base ne connaît pas les champs).

        infos_ok : [(id, info)] des images converties (`Etat.ok()` ou lecture directe).  Rend
        {dossier_absolu_normalisé: {'converties': n, 'base': m, 'complet': bool}}.
        """
        from .cibles import MOBILES

        def cle(objet, cat, tel, filtre, nuit):
            return (objet, tel, filtre, str(nuit) if cat in MOBILES else '')
        base = C.Counter(cle(x['objet'], x['cat'], x['tel'], x['filter_name'], x['nuit'])
                         for x in images if not x['doublon'])
        par_cle = C.Counter()
        par_lot = C.defaultdict(set)
        for _, info in infos_ok:
            final = info.get('final') or ''
            if not final:
                continue
            k = cle(info.get('objet'), info.get('cat'), info.get('tel'), info.get('filtre_base'), info.get('nuit'))
            par_cle[k] += 1
            par_lot[os.path.normcase(os.path.abspath(os.path.dirname(final)))].add(k)
        out = {}
        for dossier, cles in par_lot.items():
            conv = sum(par_cle[k] for k in cles)
            tot = sum(base.get(k, 0) for k in cles)
            out[dossier] = {'converties': conv, 'base': tot, 'complet': tot > 0 and conv >= tot}
        return out


def lire_infos_ok(dest) -> list:
    """[(id, info)] des images converties, en lecture seule ; [] si rien (sans exception)."""
    chemin = os.path.join(str(dest or ''), '_traitement', 'etat.sqlite') if dest else ''
    if not chemin or not os.path.exists(chemin):
        return []
    import sqlite3
    try:
        db = sqlite3.connect(_uri_lecture_seule(chemin), uri=True, timeout=5)
        try:
            return [(i, json.loads(s)) for i, s in db.execute("SELECT id, info FROM images WHERE statut='ok'") if s]
        finally:
            db.close()
    except Exception:
        return []
