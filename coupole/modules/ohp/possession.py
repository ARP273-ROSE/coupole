"""Ce que l'on possède déjà : l'état du dossier de sortie rapporté à l'inventaire de la banque.

La source de vérité est ``<destination>/_traitement/etat.sqlite`` (statut ``ok`` / ``doublon`` / ``echec`` par
identifiant d'image, tenu par le pilote).  Ce module la lit en entier (quelques milliers de lignes, quelques
millisecondes), sans Qt, et répond : cette image est-elle possédée ?  combien d'images de cet objet a-t-on ?
que reste-t-il à télécharger ?  Il ne lève jamais.  Sans dossier ou sans base : rien n'est possédé.  Base présente
mais illisible (0.2.1) : rien n'est possédé ET `erreur` le dit (l'interface affiche un bandeau, le journal note la
cause) — jamais plus un « tout à télécharger » silencieux.

Statuts rendus (``STATUTS``) :
  * ``ok`` — convertie et rangée (possédée) ;
  * ``doublon`` — mêmes pixels qu'une image déjà convertie : écartée par le traitement (pas à retélécharger) ;
  * ``echec`` — le traitement a échoué (à retenter) ;
  * ``absente`` — jamais traitée (à télécharger).
"""
from __future__ import annotations

import collections as C
import json
import logging
import os

from .conversion import ident

STATUTS = ('ok', 'doublon', 'echec', 'absente')
POSSEDES = ('ok', 'doublon')                 # ce qui n'est plus à télécharger
log = logging.getLogger('coupole.possession')


def _lire(chemin: str, requete: str) -> list:
    """Lignes de la base d'état `chemin` : base de travail locale à jour, copie locale (partage réseau, base WAL)
    ou la base elle-même en lecture seule (core/base_partagee.lire_base).  Lève BaseIllisible."""
    from ...core.base_partagee import lire_base
    return lire_base(chemin, requete)[0]


def fichiers_ranges_presents(dest) -> bool:
    """Des fichiers convertis sont-ils rangés dans `dest` (dossiers de type « 07_Nebuleuses »…) ?  Rapide : on
    s'arrête au premier fichier trouvé.  Sert à proposer « Reconnaître les fichiers existants » quand
    `_traitement/` manque."""
    from .emplacements import _dossiers_type
    from .reorganisation import EXTENSIONS
    try:
        noms = set(os.listdir(str(dest)))
    except OSError:
        return False
    for d in sorted(noms & _dossiers_type()):
        for _racine, _dossiers, fichiers in os.walk(os.path.join(str(dest), d)):
            if any(f.lower().endswith(EXTENSIONS) for f in fichiers):
                return True
    return False


def _relatif(chemin: str, dest: str) -> str:
    """Chemin local relatif à la destination quand il est dedans (sinon tel quel)."""
    if chemin and dest:
        try:
            rel = os.path.relpath(chemin, dest)
            if not rel.startswith('..'):
                return rel
        except ValueError:                       # lecteurs différents sous Windows
            pass
    return chemin


class Possession:
    """Lecture seule de l'état d'une destination ; `vide()` quand il n'y a rien."""

    def __init__(self, dest: str = '', statuts: dict | None = None, details: dict | None = None):
        self.dest = dest or ''
        self.statuts: dict[str, str] = statuts or {}        # id → 'ok' | 'doublon' | 'echec'
        self.details: dict[str, dict] = details or {}       # id → {'date': …, 'chemin': …}
        self.existe = bool(self.statuts)
        self.a_migrer: list = []                            # [(id, chemin relatif)] trouvés par journal.csv
        self.erreur = ''                                    # base présente mais illisible : la cause
        self.base_absente = False                           # pas de _traitement/etat.sqlite dans `dest`
        self.fichiers_sans_base = False                     # … mais des fichiers convertis y sont rangés

    @classmethod
    def vide(cls) -> 'Possession':
        return cls()

    @classmethod
    def lire(cls, dest) -> 'Possession':
        """Lit `<dest>/_traitement/etat.sqlite` ; jamais d'exception (base absente, verrouillée, abîmée → vide)."""
        return cls.lire_avec_infos(dest)[0]

    @classmethod
    def lire_avec_infos(cls, dest) -> tuple['Possession', list]:
        """(Possession, [(id, info)] des converties) en UNE lecture de la base : l'interface demandait les deux
        et décodait deux fois les 7 625 JSON (et, sur un partage, ouvrait deux fois la base).

        Le chemin de chaque image convertie est rapporté au dossier de sortie courant (`emplacements.resoudre` :
        `info['chemin']`, `final` s'il est dedans, `journal.csv`, dossier de type) ; dans les infos rendues,
        `final` est remplacé (en mémoire seulement) par ce chemin local, pour la complétude des lots.
        `a_migrer` : [(id, chemin relatif)] trouvés par le journal, à noter dans la base (`emplacements.migrer`)."""
        from . import emplacements
        dest = str(dest or '')
        chemin = os.path.join(dest, '_traitement', 'etat.sqlite') if dest else ''
        if not chemin or not os.path.exists(chemin):
            p = cls(dest)
            if dest:
                p.base_absente = True
                p.fichiers_sans_base = os.path.isdir(dest) and fichiers_ranges_presents(dest)
                log.info('possession de %s : pas de base de suivi (_traitement/etat.sqlite)%s', dest,
                         ', fichiers convertis présents' if p.fichiers_sans_base else '')
            return p, []
        statuts, details, infos_ok = {}, {}, []
        try:
            # lecture seule : on ne crée rien, on ne modifie rien, on ne gêne pas un pilote qui écrit
            lignes = _lire(chemin, 'SELECT id, statut, maj, info FROM images')
        except Exception as e:                   # BaseIllisible, sqlite3.Error, OSError : DIT, jamais muet
            p = cls(dest)
            p.erreur = str(e) or type(e).__name__
            log.warning('possession de %s : base de suivi illisible : %s', dest, p.erreur)
            return p, []
        journal = None
        a_migrer = []
        for i, statut, maj, info in lignes:
            if statut not in ('ok', 'doublon', 'echec'):
                continue
            statuts[i] = statut
            rel, origine = '', ''
            if info and statut == 'ok':
                try:
                    d = json.loads(info)
                except ValueError:
                    d = None
                if isinstance(d, dict):
                    rel, origine = emplacements.resoudre(dest, d, journal={'url': {}, 'source': {}})
                    if origine not in ('base',):             # journal lu une seule fois, et seulement s'il sert
                        if journal is None:
                            journal = emplacements.lire_journal(dest)
                        rel, origine = emplacements.resoudre(dest, d, journal)
                    if origine == 'journal':
                        a_migrer.append((i, rel))
                    d = dict(d, _id=i)
                    if rel:
                        d['final'] = emplacements.absolu(dest, rel)
                    infos_ok.append((i, d))
            details[i] = {'date': (maj or '')[:19].replace('T', ' '), 'chemin': rel.replace('/', os.sep),
                          'origine': origine}
        poss = cls(dest, statuts, details)
        poss.a_migrer = a_migrer
        log.info('possession de %s : %d image(s) possédée(s) lue(s) (%d ligne(s) dans la base)', dest,
                 sum(1 for v in statuts.values() if v in POSSEDES), len(lignes))
        return poss, infos_ok

    # ---------------------------------------------------------------- par image
    def statut(self, x: dict) -> str:
        return self.statuts.get(ident(x), 'absente')

    def detail(self, x: dict) -> dict:
        """{'statut', 'date', 'chemin', 'origine'} ; le chemin est relatif au dossier de sortie courant ('' si
        introuvable) ; origine : 'base', 'journal' (journal.csv), 'rebase' (dossier de type) ou ''."""
        i = ident(x)
        d = self.details.get(i, {})
        # chemin déjà rendu relatif à la lecture (fil de fond) : rien à recalculer à chaque affichage
        return {'statut': self.statuts.get(i, 'absente'), 'date': d.get('date', ''), 'chemin': d.get('chemin') or '',
                'origine': d.get('origine', '')}

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

    @staticmethod
    def etat_agrege(c: dict) -> str:
        """État d'un objet pour sa pastille dans la liste des objets, aux couleurs de la légende des images :
        « echec » (au moins une image en échec, à retenter), « complet » (tout possédé, doublons écartés compris),
        « partiel » (une partie manque), « absente » (rien de téléchargé)."""
        if not c or c.get('total', 0) <= 0:
            return 'absente'
        if c.get('echecs', 0) > 0:
            return 'echec'
        traitees = c.get('possedees', 0) + c.get('doublons', 0)
        if traitees >= c['total']:
            return 'complet'
        return 'partiel' if traitees > 0 else 'absente'

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


def lire_statuts(dest) -> dict:
    """{id: statut} en lecture seule, sans décoder les infos ; {} si rien (sans exception, sans rien créer)."""
    chemin = os.path.join(str(dest or ''), '_traitement', 'etat.sqlite') if dest else ''
    if not chemin or not os.path.exists(chemin):
        return {}
    try:
        return dict(_lire(chemin, 'SELECT id, statut FROM images'))
    except Exception as e:
        log.warning('statuts de %s illisibles : %s', dest, e)
        return {}


def lire_infos_ok(dest) -> list:
    """[(id, info)] des images converties, en lecture seule ; [] si rien (sans exception)."""
    chemin = os.path.join(str(dest or ''), '_traitement', 'etat.sqlite') if dest else ''
    if not chemin or not os.path.exists(chemin):
        return []
    try:
        return [(i, json.loads(s)) for i, s in _lire(chemin, "SELECT id, info FROM images WHERE statut='ok'") if s]
    except Exception as e:
        log.warning('infos de %s illisibles : %s', dest, e)
        return []
