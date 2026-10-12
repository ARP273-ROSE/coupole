"""Téléchargement poli, préparation et rangement des fichiers d'archive ; état, journal, possession.

* Rangement par champ (0.2.2, ``rangement.py``) : ``<sortie>/Archives/<champ>/<cible>_<instrument>_<filtre>_<date>_
  <type>_<n>x<pose>s.xisf`` (image préparée, recadrée sur sa zone utile) ; le fichier d'origine seulement sur option
  (``<champ>/_originaux/``), le masque des pixels sans donnée seulement sur option (compressé).
* État : ``<sortie>/Archives/_etat/etat.sqlite`` — même schéma et même logique de partage réseau que la Banque OHP
  (``core/base_partagee.py`` : sur un partage, base de travail locale recopiée atomiquement) ; un téléchargement
  interrompu reprend (fichier ``.part`` et requête partielle quand le serveur l'accepte) ; un fichier déjà préparé
  n'est jamais refait.  Journal lisible et bilingue ``_etat/JOURNAL.txt``.
* Courtoisie : User-Agent qui nomme Coupole, débit total plafonné (seau à jetons partagé), deux téléchargements
  simultanés par défaut, une seule mesure de taille à la fois par archive, jamais de nouvel essai immédiat en
  boucle (attente croissante).
* Volume : `estimer()` additionne les tailles annoncées et mesure les autres (requête partielle d'un octet,
  échantillon par instrument au-delà de 60 fichiers) avant tout téléchargement ; au-delà du seuil (réglage
  ``archives_seuil_go``, 2 Go par défaut), l'interface et la ligne de commande demandent confirmation.
"""
from __future__ import annotations

import collections
import concurrent.futures as F
import datetime as D
import json
import os
import threading
import time

from ...core import config, reseau
from ..ohp.conversion import sur
from ..ohp.pilote import Etat, Journal
from .extraction import Inexploitable, preparer
from .services import ARCHIVES

SEUIL_GO_DEFAUT = 2.0
ECHANTILLON = 60                 # au-delà, tailles inconnues estimées par un échantillon par (archive, instrument)
PAR_GROUPE = 4


def dossier_archives(sortie) -> str:
    return os.path.join(os.path.abspath(os.path.expanduser(str(sortie))), 'Archives')


def sortie_par_defaut() -> str:
    r = config.reglages()
    return r.get('archives_dossier') or r.get('dossier_sortie') or str(config.dossier_sortie_defaut())


def chemin_etat(sortie) -> str:
    return os.path.join(dossier_archives(sortie), '_etat', 'etat.sqlite')


def nom_cible(o: dict, cible: str = '') -> str:
    """Dossier de la cible : le nom cherché, sinon la cible de l'archive, sinon les coordonnées."""
    if cible:
        return sur(cible)
    if o.get('cible'):
        return sur(o['cible'])
    if o.get('ra') is not None:
        return 'RA%07.3f_DEC%+07.3f' % (o['ra'], o['dec'])
    return 'divers'


def dossier_de(sortie, o: dict, cible: str = '') -> str:
    """Dossier du champ (classement par champ, comme la Banque OHP)."""
    from .rangement import nom_champ
    return os.path.join(dossier_archives(sortie), nom_champ(o, cible))


def base_preparee(fichier: str) -> str:
    n = fichier
    for ext in ('.fits.gz', '.fits.fz', '.fits.bz2', '.fit.gz', '.fits', '.fit', '.fts', '.img', '.IMG', '.xml', '.fz', '.gz'):
        if n.lower().endswith(ext.lower()):
            n = n[:-len(ext)]
            break
    return sur(n) + '_sci'


# ================================================================================================ estimation
def taille_mesuree(url: str, delai: float = 30) -> int | None:
    try:
        t = reseau.taille_distante(url, delai=delai)
        return t or None
    except Exception:
        return None


def estimer(observations: list[dict], mesurer: bool = True, arret: threading.Event | None = None,
            progression=None) -> dict:
    """{'octets', 'connus', 'mesures', 'estimes', 'inconnus', 'n'} ; complète `taille` des observations mesurées
    (et marque `taille_estimee` celles extrapolées).  Une mesure à la fois par archive (courtoisie)."""
    connus = [o for o in observations if o.get('taille')]
    reste = [o for o in observations if not o.get('taille')]
    mesures = estimes = 0
    if mesurer and reste:
        groupes = collections.defaultdict(list)
        for o in reste:
            groupes[(o['archive'], o['instrument'], o['filtre'] if o['archive'] == 'sdss' else '')].append(o)
        a_mesurer = []
        for g in groupes.values():
            a_mesurer += g if len(reste) <= ECHANTILLON else g[:PAR_GROUPE]
        par_archive = collections.defaultdict(list)
        for o in a_mesurer:
            par_archive[o['archive']].append(o)

        def mesurer_archive(liste):
            n = 0
            for o in liste:
                if arret is not None and arret.is_set():
                    break
                try:
                    url = ARCHIVES[o['archive']].adresse_fichier(o) if o['archive'] == 'opus' else o['url']
                except Exception:
                    url = o['url']
                t = taille_mesuree(url)
                if t:
                    o['taille'] = t
                    n += 1
                if progression:
                    progression(1)
            return n
        with F.ThreadPoolExecutor(max_workers=max(1, min(4, len(par_archive)))) as ex:
            mesures = sum(ex.map(mesurer_archive, par_archive.values()))
        for g in groupes.values():
            vus = [o['taille'] for o in g if o.get('taille')]
            if vus:
                moyenne = sum(vus) / len(vus)
                for o in g:
                    if not o.get('taille'):
                        o['taille'], o['taille_estimee'] = int(moyenne), True
                        estimes += 1
    inconnus = sum(1 for o in observations if not o.get('taille'))
    return {'octets': sum(o.get('taille') or 0 for o in observations), 'connus': len(connus), 'mesures': mesures,
            'estimes': estimes, 'inconnus': inconnus, 'n': len(observations)}


def seuil_octets() -> float:
    try:
        return float(config.reglages().get('archives_seuil_go', SEUIL_GO_DEFAUT)) * 1e9
    except (TypeError, ValueError):
        return SEUIL_GO_DEFAUT * 1e9


# ================================================================================================ pilote
class Telechargement:
    """Télécharge, prépare et range une liste d'observations.  Événements (`rapporter(dict)`) :
    {'genre': 'debut'|'octets'|'fini'|'erreur'|'deja'|'fin', …}.  `arret` annule ; `pause` suspend."""

    def __init__(self, sortie, observations: list[dict], cible: str = '', fmt: str = 'xisf',
                 garder_original: bool = False, debit_octets_s: float = 8e6, paralleles: int = 2,
                 rapporter=None, arret: threading.Event | None = None, pause: threading.Event | None = None,
                 masque: bool = False, recadrer: bool = True):
        self.sortie = os.path.abspath(os.path.expanduser(str(sortie)))
        self.racine = dossier_archives(self.sortie)
        self.trav = os.path.join(self.racine, '_etat')
        os.makedirs(self.trav, exist_ok=True)
        self.observations = list(observations)
        self.cible = cible
        self.fmt = fmt if fmt in ('xisf', 'fits') else 'xisf'
        self.garder = bool(garder_original)
        self.masque = bool(masque)
        self.recadrer = bool(recadrer)
        self._recus: dict[str, int] = {}
        self._gardes = 0
        self.paralleles = max(1, min(6, int(paralleles or 2)))
        self.rapporter = rapporter or (lambda ev: None)
        self.arret = arret or threading.Event()
        self.pause = pause or threading.Event()
        self.limiteur = reseau.LimiteurDebit(debit_octets_s)
        self.journal = Journal(self.trav, 1.0)
        self.etat = Etat(os.path.join(self.trav, 'etat.sqlite'), 1.0)
        self._verrou = threading.Lock()
        self._octets = 0
        self._dernier_evt = 0.0
        self.bilan = collections.Counter()

    # ------------------------------------------------------------------ événements
    def _evt(self, **ev):
        try:
            self.rapporter(ev)
        except Exception:
            pass

    def _progres(self, n, ident=''):
        with self._verrou:
            self._octets += n
            if ident:
                self._recus[ident] = self._recus.get(ident, 0) + n
            t = time.monotonic()
            if t - self._dernier_evt < 0.1:
                return
            self._dernier_evt = t
            total = self._octets
            recus = dict(self._recus)
        self._evt(genre='octets', octets=total, recus=recus)

    # ------------------------------------------------------------------ une observation
    def traiter(self, o: dict) -> str:
        from .extraction import Inexploitable as _Inex
        from .produits import classer
        from .rangement import ORIGINAUX, libre, nom_lisible
        classer(o)
        statut, _, info = self.etat.lire(o['id'])
        dossier = dossier_de(self.sortie, o, self.cible)
        if statut == 'ok' and info.get('prepare') and os.path.exists(os.path.join(self.racine, info['prepare'])):
            self._evt(genre='deja', id=o['id'])
            return 'deja'
        while self.pause.is_set() and not self.arret.is_set():
            time.sleep(0.2)
        if self.arret.is_set():
            raise reseau.Annule()
        originaux = os.path.join(dossier, ORIGINAUX)
        os.makedirs(originaux, exist_ok=True)
        self._evt(genre='debut', id=o['id'], fichier=o['fichier'], taille=o.get('taille'))
        a = ARCHIVES[o['archive']]
        url = a.adresse_fichier(o)
        fichier = os.path.join(originaux, sur_fichier(o['fichier']))
        exact = o.get('taille') if (o.get('taille') and not o.get('taille_estimee') and o['archive'] in ('mast',)) else None
        reseau.telecharger(url, fichier, taille_attendue=exact, limiteur=self.limiteur, arret=self.arret,
                           progression=lambda n, i=o['id']: self._progres(n, i))
        etiquette = ''
        if o.get('etiquette'):
            etiquette = os.path.join(originaux, sur_fichier(o['etiquette'].rsplit('/', 1)[-1]))
            reseau.telecharger(o['etiquette'], etiquette, limiteur=self.limiteur, arret=self.arret)
        octets_origine = os.path.getsize(fichier)
        self._evt(genre='telecharge', id=o['id'], octets=octets_origine)

        def nommer(entete):
            return libre(os.path.join(dossier, nom_lisible(o, self.cible, entete)), '.' + self.fmt,
                         appartient=lambda c: False)
        try:
            r = preparer(fichier, os.path.join(dossier, base_preparee(o['fichier'])), o, self.fmt,
                         etiquette or None, masque=self.masque, recadrer=self.recadrer, nommer=nommer)
        except _Inex as e:
            if not self.garder:
                self._effacer_originaux(fichier, etiquette, originaux)
            info = {'fichier': os.path.relpath(fichier, self.racine) if self.garder else '', 'raison': str(e)}
            self.etat.ecrire(o['id'], url, 'echec', info)
            self.journal.ecrire('arc_j_inexploitable', id=o['id'], raison=str(e))
            self._evt(genre='erreur', id=o['id'], erreur=str(e))
            return 'echec'
        except Exception:
            if not self.garder:                  # fichier illisible : rien ne reste derrière (il sera retéléchargé)
                self._effacer_originaux(fichier, etiquette, originaux)
            raise
        if not self.garder:
            self._effacer_originaux(fichier, etiquette, originaux)
        gardes = r['octets'] + sum(os.path.getsize(m) for m in r.get('masques', []) if os.path.exists(m))
        if self.garder:
            gardes += octets_origine
        with self._verrou:
            self._gardes += gardes
        info = {'fichier': os.path.relpath(fichier, self.racine) if self.garder else '',
                'prepare': os.path.relpath(r['chemin'], self.racine),
                'masque': os.path.relpath(r['masque'], self.racine) if r['masque'] else '',
                'autres': [os.path.relpath(c, self.racine) for c in r.get('chemins', [])[1:]],
                'octets': octets_origine, 'octets_prepare': r['octets'], 'forme': list(r['forme']),
                'forme_origine': list(r.get('forme_origine') or r['forme']), 'recadrage': r.get('recadrage'),
                'nan': r['nan'], 'wcs': r['wcs'], 'bunit': r['bunit'], 'extension': r['extension'],
                'archive': o['archive'], 'mission': o['mission'], 'instrument': o['instrument'], 'filtre': o['filtre'],
                'lambda_nm': o['lambda_nm'], 'cible': self.cible or o['cible'], 'debut': o['debut'],
                'credit': o['credit'], 'page': o['page'], 'poses': r.get('poses'), 'exposition': r.get('exposition'),
                'produit': o.get('produit', ''), 'nature': o.get('nature', ''), 'variante': bool(o.get('variante')),
                'obs_id': o.get('obs_id', ''), 'date': D.datetime.now(D.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
        self.etat.ecrire(o['id'], url, 'ok', info)
        self.journal.ecrire('arc_j_ok', id=o['id'], chemin=info['prepare'])
        if r.get('recadrage'):
            self.journal.ecrire('arc_j_recadre', chemin=info['prepare'],
                                avant='%d×%d' % (info['forme_origine'][1], info['forme_origine'][0]),
                                apres='%d×%d' % (r['forme'][1], r['forme'][0]))
        self._evt(genre='fini', id=o['id'], chemin=r['chemin'], octets_origine=octets_origine, octets_garde=gardes,
                  forme=list(r['forme']), forme_origine=info['forme_origine'])
        return 'ok'

    @staticmethod
    def _effacer_originaux(fichier, etiquette, originaux):
        for f in (fichier, etiquette):
            try:
                if f:
                    os.remove(f)
            except OSError:
                pass
        try:
            os.rmdir(originaux)
        except OSError:
            pass

    # ------------------------------------------------------------------ boucle
    def executer(self) -> dict:
        self.journal.ecrire('arc_j_session', n=len(self.observations), dest=self.racine)
        t0 = time.monotonic()

        def un(o):
            if self.arret.is_set():
                return 'annule'
            try:
                return self.traiter(o)
            except reseau.Annule:
                return 'annule'
            except Exception as e:
                try:
                    self.etat.ecrire(o['id'], o['url'], 'echec', {'raison': '%s: %s' % (type(e).__name__, e)})
                except Exception:
                    pass
                self.journal.ecrire('arc_j_echec', id=o['id'], raison='%s: %s' % (type(e).__name__, e))
                self._evt(genre='erreur', id=o['id'], erreur='%s: %s' % (type(e).__name__, e))
                return 'echec'
        try:
            with F.ThreadPoolExecutor(max_workers=self.paralleles) as ex:
                for st in ex.map(un, self.observations):
                    self.bilan[st] += 1
                    self.etat.valider_si_du()
                    self.journal.vider_si_du()
        finally:
            self.etat.fermer()
            self.journal.ecrire('arc_j_fin', ok=self.bilan['ok'], deja=self.bilan['deja'], echec=self.bilan['echec'],
                                annule=self.bilan['annule'], s='%.0f' % (time.monotonic() - t0))
            self.journal.vider()
        res = dict(self.bilan)
        res['octets'] = self._octets
        res['octets_gardes'] = self._gardes
        res['dossier'] = self.racine
        res['secondes'] = time.monotonic() - t0
        self._evt(genre='fin', bilan=res)
        return res


def sur_fichier(nom: str) -> str:
    """Nom de fichier sûr qui garde ses extensions (.fits.gz, _i2d.fits, .IMG)."""
    nom = nom.rsplit('/', 1)[-1]
    for ext in ('.fits.gz', '.fits.fz', '.fits.bz2', '.fits', '.fit', '.IMG', '.img', '.LBL', '.lbl', '.xml', '.fz', '.gz'):
        if nom.endswith(ext):
            return sur(nom[:-len(ext)]) + ext
    return sur(nom)


# ================================================================================================ possession
STATUTS = ('ok', 'echec', 'absente')


def chemin_relatif(p: str) -> str:
    """Chemin relatif noté dans la base d'état, avec le séparateur du système (« HST\\M16\\x » ↔ « HST/M16/x »)."""
    return p.replace('\\', '/').replace('/', os.sep) if p else p


def possession(sortie) -> dict[str, dict]:
    """{id: {'statut', **info}} d'après la base d'état ; jamais d'exception (rien → {})."""
    chemin = chemin_etat(sortie)
    if not os.path.exists(chemin):
        return {}
    import sqlite3
    from ...core.base_partagee import chemin_lecture
    from ...core.chemins import uri_sqlite_lecture_seule
    try:
        db = sqlite3.connect(uri_sqlite_lecture_seule(chemin_lecture(chemin)), uri=True, timeout=5)
        try:
            lignes = db.execute('SELECT id, statut, info FROM images').fetchall()
        finally:
            db.close()
    except sqlite3.Error:
        return {}
    out = {}
    racine = dossier_archives(sortie)
    for i, st, info in lignes:
        try:
            d = json.loads(info) if info else {}
        except ValueError:
            d = {}
        for k in ('prepare', 'fichier', 'masque'):          # base écrite sous Windows, relue ailleurs (et l'inverse)
            if isinstance(d.get(k), str):
                d[k] = chemin_relatif(d[k])
        if isinstance(d.get('autres'), list):
            d['autres'] = [chemin_relatif(x) for x in d['autres'] if isinstance(x, str)]
        if st == 'ok' and d.get('prepare') and not os.path.exists(os.path.join(racine, d['prepare'])):
            st = 'absente'                                     # fichier déplacé ou effacé à la main
        d['statut'] = st
        out[i] = d
    return out
