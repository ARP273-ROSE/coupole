"""Accès réseau poli : User-Agent identifiant, débit plafonné, reprise, annulation.

Le serveur de l'Observatoire de Paris est public et partagé : Coupole ne le
martèle pas.  Toutes les requêtes portent un User-Agent qui nomme
l'application et sa version ; le débit total est plafonné (seau à jetons
partagé par tous les fils) ; le nombre de téléchargements simultanés est
borné (core.parallele).
"""
from __future__ import annotations

import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from .. import __version__



def user_agent() -> str:
    from . import sources
    return 'Coupole/%s (+https://github.com/%s; DU ECU Observatoire de Paris)' % (__version__,
                                                                                 sources.valeur('maj.depot'))


class Annule(Exception):
    """L'utilisateur a demandé l'arrêt."""


class LimiteurDebit:
    """Seau à jetons partagé : au plus `octets_s` octets par seconde, tous fils confondus."""

    def __init__(self, octets_s: float):
        self.debit = max(0.0, float(octets_s))
        self.jetons = self.debit
        self.t = time.monotonic()
        self.verrou = threading.Lock()

    def regler(self, octets_s: float):
        with self.verrou:
            self.debit = max(0.0, float(octets_s))

    def prendre(self, n: int, arret: threading.Event | None = None):
        if self.debit <= 0:
            return
        while True:
            with self.verrou:
                maintenant = time.monotonic()
                self.jetons = min(self.debit, self.jetons + (maintenant - self.t) * self.debit)
                self.t = maintenant
                if self.jetons >= n or self.jetons >= self.debit:
                    self.jetons -= n
                    return
                attente = (n - self.jetons) / self.debit
            if arret is not None and arret.wait(min(attente, 0.5)):
                raise Annule()
            elif arret is None:
                time.sleep(min(attente, 0.5))


def requete(url, data=None, en_tetes=None, delai=60):
    h = {'User-Agent': user_agent()}
    h.update(en_tetes or {})
    req = urllib.request.Request(url, data=data, headers=h)
    return urllib.request.urlopen(req, timeout=delai)


class ServiceInjoignable(IOError):
    """Service en ligne injoignable, trop lent ou en erreur (hors ligne, DNS, délai dépassé, HTTP 5xx...)."""


def lire_texte(url: str, delai: float = 8, max_octets: int = 2_000_000, accepter=()) -> str:
    """Petite requête GET (services en ligne) : texte de la réponse, ou ServiceInjoignable.

    `accepter` : codes HTTP « d'erreur » dont le corps est quand même utile (ex. 300 de JPL SBDB).
    """
    try:
        with requete(url, delai=delai) as r:
            return r.read(max_octets).decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        if e.code in accepter:
            return e.read(max_octets).decode('utf-8', 'replace')
        raise ServiceInjoignable('HTTP %d' % e.code) from e
    except Exception as e:                      # réseau absent, DNS, délai dépassé, TLS...
        raise ServiceInjoignable('%s: %s' % (type(e).__name__, e)) from e


def tap_sync(url_service: str, adql: str, delai=300) -> bytes:
    """Requête TAP synchrone (ADQL), résultat CSV."""
    corps = urllib.parse.urlencode({'REQUEST': 'doQuery', 'LANG': 'ADQL', 'FORMAT': 'csv',
                                    'QUERY': adql}).encode()
    with requete(url_service.rstrip('/') + '/sync', data=corps, delai=delai) as r:
        return r.read()


def taille_distante(url: str, delai=60) -> int:
    """Taille exacte annoncée par le serveur (requête Range sur 1 octet)."""
    with requete(url, en_tetes={'Range': 'bytes=0-0'}, delai=delai) as r:
        cr = r.headers.get('Content-Range', '')
        return int(cr.rsplit('/', 1)[1]) if '/' in cr else int(r.headers.get('Content-Length', 0))


def telecharger(url: str, chemin: str, taille_attendue: int | None = None, tolerance=2048,
                limiteur: LimiteurDebit | None = None, arret: threading.Event | None = None,
                progression=None, essais=4, verifier=None):
    """Télécharge avec reprise (.part + HTTP Range) et contrôles.

    Renvoie ('ok'|'deja', octets reçus).  Lève IOError après `essais` échecs, Annule si arrêt.
    `verifier(chemin_part)` : contrôle supplémentaire (ex. en-tête FITS), lève IOError si mauvais.
    """
    part = chemin + '.part'
    dernier = ''
    for essai in range(1, essais + 1):
        if arret is not None and arret.is_set():
            raise Annule()
        try:
            total = taille_distante(url)
            if taille_attendue is not None and abs(total - taille_attendue) > tolerance:
                raise IOError('server size %d != inventory %d' % (total, taille_attendue))
            if os.path.exists(chemin) and os.path.getsize(chemin) == total:
                return 'deja', 0
            debut = os.path.getsize(part) if os.path.exists(part) else 0
            if debut > total:
                os.remove(part)
                debut = 0
            recu = 0
            if debut < total:
                with requete(url, en_tetes={'Range': 'bytes=%d-' % debut}, delai=120) as r, \
                        open(part, 'ab' if debut else 'wb') as f:
                    if debut and r.status != 206:          # Range ignoré : on repart de zéro
                        f.seek(0)
                        f.truncate()
                        debut = 0
                    while True:
                        if arret is not None and arret.is_set():
                            raise Annule()
                        b = r.read(1 << 16)
                        if not b:
                            break
                        if limiteur is not None:
                            limiteur.prendre(len(b), arret)
                        f.write(b)
                        recu += len(b)
                        if progression is not None:
                            progression(len(b))
            t = os.path.getsize(part)
            if t != total:
                raise IOError('received %d of %d bytes' % (t, total))
            if verifier is not None:
                verifier(part)
            os.replace(part, chemin)
            return 'ok', recu
        except Annule:
            raise
        except (urllib.error.URLError, OSError, ValueError) as e:
            dernier = str(e)
            if arret is not None:
                if arret.wait(2 * essai):
                    raise Annule()
            else:
                time.sleep(2 * essai)
    raise IOError(dernier or 'download failed')
