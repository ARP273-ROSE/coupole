"""Télécharger une sélection d'un partage : même moteur que la Banque OHP (reprise, débit partagé, annulation,
pause), préparation au choix (XISF ou FITS), astrométrie, rangement par date et par cible.

Rangement : ``<dossier choisi>/<nom du partage>/<AAAA-MM-JJ>/<cible>/<observateur>/<fichier>`` (« divers » quand la
cible n'est pas reconnue, la date du dossier quand le nom ne la donne pas).  Les fichiers d'origine (FITS, JPEG,
vidéos, tableaux) sont gardés tels quels dans ``_originaux/`` à côté, sauf si l'utilisateur ne veut que la version
préparée.  Astrométrie (``core/astrometrie``) : la solution déjà présente dans l'en-tête est gardée ; sinon, sur
demande, ASTAP ou astrometry.net installés, puis, en dernier recours et seulement avec l'accord de l'utilisateur et
sa clé d'API, le service libre nova.astrometry.net.
"""
from __future__ import annotations

import collections
import concurrent.futures as F
import datetime as D
import os
import re
import threading
import time

from ...core import config, reseau
from ...core.i18n import tr
from . import structure as S

ETAT = '_etat_partage.json'
ORIGINAUX = '_originaux'


def sortie_par_defaut() -> str:
    return str(config.dossier_sortie_defaut() / 'Partages')


def jeton(t: str, defaut: str = 'divers') -> str:
    t = S.normaliser(t)
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return t[:60] or defaut


def dossier_de(racine: str, nom_partage: str, f: S.Fichier, date_dossier: D.date | None = None,
               cible: str = '', observateur: str = '') -> str:
    quand = f.instant.date() if f.instant is not None and not f.doute else date_dossier
    jour = quand.isoformat() if quand else 'sans-date'
    return os.path.join(racine, jeton(nom_partage, 'partage'), jour, jeton(f.cible or cible, 'divers'),
                        jeton(f.observateur or observateur, 'inconnu'))


def cible_et_observateur(session, f: S.Fichier) -> tuple[str, str]:
    """Cible et observateur d'un fichier quand son nom ne les dit pas : en-tête FITS déjà lu (OBJECT, OBSERVER),
    puis tableau de mesures (ligne qui cite ce fichier)."""
    cible, obs = '', ''
    e = (getattr(session, 'entetes', None) or {}).get(f.chemin) or {}
    cible = S.cible_de(str(e.get('objet') or ''))
    obs = str(e.get('observateur') or '')
    if not cible or not obs:
        nom = S.normaliser(f.nom)
        for t in (session.tableaux_de_mesures() if hasattr(session, 'tableaux_de_mesures') else []):
            for m in t.mesures:
                if m.fichier and S.normaliser(m.fichier) in (nom, nom.rsplit('.', 1)[0]):
                    cible = cible or m.cible
                    obs = obs or m.auteur
    return cible, obs


def preparer_fits(source: str, dest_sans_ext: str, fmt: str, astrometrie: str = 'wcs', arret=None,
                  en_ligne: bool = False) -> dict:
    """FITS (2-D ou cube couleur) → XISF ou FITS, en-tête nettoyé, WCS gardée ou calculée (chaîne commune
    ``core/astrometrie`` : en-tête → ASTAP → astrometry.net local → nova.astrometry.net si `en_ligne`).  Rend
    {'chemin', 'wcs': 'entete'|'astap'|'astrometry.net'|'nova'|'', 'octets'}."""
    import warnings

    import numpy as np
    from astropy.io import fits

    from ...core import astrometrie as A
    from ..archives.extraction import ecrire_image
    from .analyses.parallaxe.image import entete_propre
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with fits.open(source, memmap=False) as hdul:
            hdu = next(h for h in hdul if getattr(h, 'data', None) is not None and h.data.ndim >= 2)
            donnees = np.asarray(hdu.data, dtype=np.float32)
            entete = entete_propre(hdu.header)
    if donnees.ndim == 3:
        donnees = donnees.mean(axis=0) if donnees.shape[0] <= 4 else donnees[0]
        for k in ('NAXIS3',):
            entete.remove(k, ignore_missing=True)
    entete['NAXIS'] = 2
    sol, wcs = A.resoudre(donnees, entete, astrometrie, en_ligne, os.path.dirname(dest_sans_ext),
                          os.path.basename(dest_sans_ext), arret)
    if sol is not None and wcs != 'entete':
        A.copier_wcs(sol, entete)
    for k in ('BZERO', 'BSCALE', 'BLANK'):
        entete.remove(k, ignore_missing=True)
    entete['BITPIX'] = -32
    chemin = dest_sans_ext + ('.xisf' if fmt == 'xisf' else '.fits')
    octets = ecrire_image(chemin, donnees, entete, fmt)
    return {'chemin': chemin, 'wcs': wcs, 'octets': octets}


class Telechargement:
    """Télécharge et range une sélection.  Événements (`rapporter(dict)`) : {'genre': 'debut'|'octets'|'fini'|
    'deja'|'erreur'|'fin', …}.  `arret` annule ; `pause` suspend."""

    def __init__(self, session, fichiers: list, sortie: str, fmt: str = 'xisf', garder_originaux: bool = True,
                 astrometrie: str = 'wcs', debit_octets_s: float = 0.0, paralleles: int = 2, rapporter=None,
                 arret: threading.Event | None = None, pause: threading.Event | None = None, en_ligne: bool = False):
        self.session = session
        self.fichiers = list(fichiers)
        self.sortie = os.path.abspath(os.path.expanduser(sortie))
        self.fmt = fmt if fmt in ('xisf', 'fits') else 'xisf'
        self.garder = bool(garder_originaux)
        self.astrometrie = astrometrie
        self.en_ligne = bool(en_ligne)          # nova.astrometry.net : seulement avec l'accord de l'utilisateur
        self.paralleles = max(1, min(6, int(paralleles or 2)))
        self.rapporter = rapporter or (lambda ev: None)
        self.arret = arret or threading.Event()
        self.pause = pause or threading.Event()
        self.limiteur = reseau.LimiteurDebit(debit_octets_s)
        self._verrou = threading.Lock()
        self._octets = 0
        self._dernier = 0.0
        self.bilan = collections.Counter()
        self.etat_chemin = os.path.join(self.sortie, ETAT)
        self.etat = config.lire_json_protege(self.etat_chemin, {}) or {}

    def _evt(self, **ev):
        try:
            self.rapporter(ev)
        except Exception:
            pass

    def _progres(self, n):
        with self._verrou:
            self._octets += n
            t = time.monotonic()
            if t - self._dernier < 0.1:
                return
            self._dernier = t
            total = self._octets
        self._evt(genre='octets', octets=total)

    def _date_dossier(self, f: S.Fichier):
        st = self.session.structure
        d = st.dossiers.get(f.dossier) if st else None
        return d.date if d is not None and not d.annee_seule else None

    def traiter(self, f: S.Fichier) -> str:
        cle = '%s|%s' % (self.session.ident, f.chemin)
        deja = self.etat.get(cle)
        if deja and deja.get('etag') == f.etag and deja.get('taille') == f.taille and \
                os.path.exists(os.path.join(self.sortie, deja.get('chemin', ''))):
            self._evt(genre='deja', chemin=f.chemin)
            return 'deja'
        while self.pause.is_set() and not self.arret.is_set():
            time.sleep(0.2)
        if self.arret.is_set():
            raise reseau.Annule()
        dossier = dossier_de(self.sortie, self.session.memorise.nom, f, self._date_dossier(f),
                             *cible_et_observateur(self.session, f))
        orig = os.path.join(dossier, ORIGINAUX) if f.genre == 'fits' else dossier
        os.makedirs(orig, exist_ok=True)
        local = os.path.join(orig, f.nom)
        self._evt(genre='debut', chemin=f.chemin, taille=f.taille)
        self.session.client.telecharger(f.chemin, local, f.taille, self.limiteur, self.arret, self._progres)
        final, wcs = local, ''
        if f.genre == 'fits':
            base = os.path.join(dossier, os.path.splitext(f.nom)[0])
            try:
                r = preparer_fits(local, base, self.fmt, self.astrometrie, self.arret, self.en_ligne)
                final, wcs = r['chemin'], r['wcs']
                if not self.garder:
                    os.remove(local)
                    try:
                        os.rmdir(orig)
                    except OSError:
                        pass
            except Exception as e:                    # FITS illisible : l'original reste, l'erreur est dite
                self._evt(genre='erreur', chemin=f.chemin, erreur='%s: %s' % (type(e).__name__, e))
        rel = os.path.relpath(final, self.sortie)
        with self._verrou:
            self.etat[cle] = {'chemin': rel, 'etag': f.etag, 'taille': f.taille, 'wcs': wcs,
                              'date': D.datetime.now(D.timezone.utc).isoformat()}
        self._evt(genre='fini', chemin=f.chemin, local=final, wcs=wcs)
        return 'ok'

    def executer(self) -> dict:
        os.makedirs(self.sortie, exist_ok=True)
        t0 = time.monotonic()

        def un(f):
            if self.arret.is_set():
                return 'annule'
            try:
                return self.traiter(f)
            except reseau.Annule:
                return 'annule'
            except Exception as e:
                self._evt(genre='erreur', chemin=f.chemin, erreur='%s: %s' % (type(e).__name__, e))
                return 'echec'
        try:
            with F.ThreadPoolExecutor(max_workers=self.paralleles) as ex:
                for st in ex.map(un, self.fichiers):
                    self.bilan[st] += 1
        finally:
            config.ecrire_json_atomique(self.etat_chemin, self.etat)
        res = dict(self.bilan)
        res['octets'] = self._octets
        res['dossier'] = self.sortie
        res['secondes'] = time.monotonic() - t0
        reseau.memoriser_debit(self.limiteur)
        self._evt(genre='fin', bilan=res)
        return res


def possedes(sortie: str, ident: str) -> dict:
    """{chemin du partage: chemin local} des fichiers déjà téléchargés dans `sortie`."""
    d = config.lire_json_protege(os.path.join(sortie, ETAT), {}) or {}
    out = {}
    for cle, v in d.items():
        i, _, chemin = cle.partition('|')
        if i == ident and os.path.exists(os.path.join(sortie, v.get('chemin', ''))):
            out[chemin] = os.path.join(sortie, v['chemin'])
    return out


def estimation(fichiers: list) -> str:
    n = sum(f.taille for f in fichiers)
    return tr('taille_go', v=('%.2f' % (n / 1e9))) if n >= 1e9 else tr('taille_mo', v=('%.1f' % (n / 1e6)))
