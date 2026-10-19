"""Client WebDAV d'un partage public Nextcloud (lien « /s/<jeton> »), réduit à ce dont Coupole a besoin.

Un lien de partage public Nextcloud donne accès à un dossier par WebDAV : adresse ``<serveur>/public.php/webdav/``,
identifiant = jeton du lien, mot de passe = celui du partage (vide s'il n'y en a pas).  Les droits du partage sont
annoncés par la propriété ``oc:permissions`` de la racine (lettres : G lire, C déposer, K créer des dossiers,
N renommer, V déplacer, D supprimer, W écrire, R repartager).

**Méthodes employées, et seulement celles-là** : PROPFIND (lister), GET (lire, avec reprise), PUT (déposer, toujours
conditionnel) et MKCOL (créer un dossier).  Ce client n'a AUCUNE méthode de suppression, de renommage, de
déplacement ni de copie, même si le partage les permet : Coupole ne touche jamais aux fichiers des autres.  Un dépôt
se fait toujours avec une condition : ``If-None-Match: *`` (le fichier ne doit pas exister) ou ``If-Match: <etag>``
(le fichier n'a pas changé depuis la lecture) ; le serveur refuse (412) sinon, rien n'est écrasé.

Le jeton est un secret partagé : jamais écrit dans un journal ni dans un rapport (``Partage.masque()``).
"""
from __future__ import annotations

import base64
import email.utils
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from ...core import reseau

NS = {'d': 'DAV:', 'oc': 'http://owncloud.org/ns', 'nc': 'http://nextcloud.org/ns',
      'ocs': 'http://open-collaboration-services.org/ns'}
CORPS_PROPFIND = (b'<?xml version="1.0" encoding="UTF-8"?>'
                  b'<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">'
                  b'<d:prop><d:getlastmodified/><d:getcontentlength/><d:resourcetype/><d:getetag/>'
                  b'<d:getcontenttype/><oc:permissions/><oc:size/><d:quota-available-bytes/></d:prop></d:propfind>')
TAILLE_MAX_LISTE = 32_000_000          # octets d'une réponse PROPFIND (≈ 60 000 fichiers) : au-delà, refus
#: lettres de oc:permissions -> droit (clé de texte « pt_droit_<droit> »)
LETTRES = {'G': 'lire', 'C': 'deposer', 'W': 'ecrire', 'K': 'dossiers', 'N': 'renommer', 'V': 'deplacer',
           'D': 'supprimer', 'R': 'repartager'}
ORDRE_DROITS = ('lire', 'deposer', 'ecrire', 'dossiers', 'renommer', 'deplacer', 'supprimer', 'repartager')


class ErreurPartage(IOError):
    """Erreur lisible : `cle` est une clé de texte (pt_err_*), `code` le statut HTTP (0 : réseau)."""

    def __init__(self, cle: str, code: int = 0, detail: str = ''):
        super().__init__('%s (%s) %s' % (cle, code, detail))
        self.cle, self.code, self.detail = cle, code, detail


class Conflit(ErreurPartage):
    """412 : la condition d'un dépôt n'est plus vraie (fichier apparu ou modifié entre-temps).  Rien n'est écrit."""


class LienInvalide(ValueError):
    def __init__(self, cle: str):
        super().__init__(cle)
        self.cle = cle


# ============================================================================================== lien
@dataclass
class Partage:
    """Un partage : adresse du serveur, jeton, mot de passe éventuel."""
    serveur: str                    # https://hote[:port][/sous-chemin]  (sans barre finale)
    jeton: str
    mot_de_passe: str = ''

    @property
    def racine(self) -> str:
        return self.serveur + '/public.php/webdav/'

    def url(self, chemin: str = '') -> str:
        chemin = chemin.strip('/')
        return self.racine + '/'.join(urllib.parse.quote(p) for p in chemin.split('/') if p) if chemin else self.racine

    def lien(self) -> str:
        """Le lien de partage tel qu'on le colle dans un navigateur."""
        return '%s/s/%s' % (self.serveur, self.jeton)

    def masque(self) -> str:
        """Le lien sans le jeton (journaux, rapports, messages)."""
        return '%s/s/%s…' % (self.serveur, self.jeton[:2])

    def en_tetes(self) -> dict:
        jeton = base64.b64encode(('%s:%s' % (self.jeton, self.mot_de_passe)).encode('utf-8')).decode('ascii')
        return {'Authorization': 'Basic ' + jeton, 'X-Requested-With': 'XMLHttpRequest'}


RE_JETON = re.compile(r'^[A-Za-z0-9]{5,64}$')
_LOCAUX = ('127.0.0.1', 'localhost', '::1')


def analyser_lien(texte: str, jeton: str = '', mot_de_passe: str = '') -> Partage:
    """Accepte un lien de partage (« https://serveur/s/<jeton> », avec ou sans « index.php », « /download »,
    « ?path=… »), une adresse WebDAV publique (« https://serveur/public.php/dav/files/<jeton>/ »,
    « https://<jeton>@serveur/public.php/webdav/ ») ou « https://serveur/public.php/webdav/ » avec le jeton à part.
    Lève LienInvalide(cle).  HTTPS obligatoire (le jeton voyagerait en clair), sauf serveur local (essais)."""
    t = (texte or '').strip().strip('<>"\'')
    if not t:
        raise LienInvalide('pt_lien_vide')
    if '://' not in t:
        t = 'https://' + t
    t = re.sub(r'^(web)?davs://', 'https://', t)
    t = re.sub(r'^(web)?dav://', 'http://', t)
    try:
        u = urllib.parse.urlsplit(t)
    except ValueError:
        raise LienInvalide('pt_lien_illisible') from None
    hote = (u.hostname or '').lower()
    if not hote:
        raise LienInvalide('pt_lien_illisible')
    if u.scheme == 'http' and hote not in _LOCAUX:
        raise LienInvalide('pt_lien_https')
    if u.scheme not in ('http', 'https'):
        raise LienInvalide('pt_lien_illisible')
    serveur_base = '%s://%s' % (u.scheme, hote if ':' not in hote else '[%s]' % hote)
    if u.port:
        serveur_base += ':%d' % u.port
    chemin = urllib.parse.unquote(u.path or '')
    jeton_trouve = urllib.parse.unquote(u.username or '')
    mdp = mot_de_passe or urllib.parse.unquote(u.password or '')
    prefixe = ''
    m = re.search(r'^(.*?)/(?:index\.php/)?s/([A-Za-z0-9]+)(?:/.*)?$', chemin)
    if m:
        prefixe, jeton_trouve = m.group(1), m.group(2)
    else:
        m = re.search(r'^(.*?)/public\.php/dav/files/([A-Za-z0-9]+)(?:/.*)?$', chemin)
        if m:
            prefixe, jeton_trouve = m.group(1), m.group(2)
        else:
            m = re.search(r'^(.*?)/public\.php/webdav(?:/.*)?$', chemin)
            if not m:
                raise LienInvalide('pt_lien_pas_partage')
            prefixe = m.group(1)
            jeton_trouve = jeton_trouve or (jeton or '').strip()
            if not jeton_trouve:
                raise LienInvalide('pt_lien_jeton_manquant')
    if not RE_JETON.match(jeton_trouve or ''):
        raise LienInvalide('pt_lien_jeton_invalide')
    return Partage(serveur_base + prefixe.rstrip('/'), jeton_trouve, mdp)


# ============================================================================================== entrées
@dataclass
class Entree:
    chemin: str                     # relatif à la racine du partage, sans barre initiale ni finale ('' = racine)
    dossier: bool
    taille: int = 0
    modifie: float = 0.0            # secondes depuis 1970 (UTC)
    etag: str = ''
    mime: str = ''
    permissions: str = ''

    @property
    def nom(self) -> str:
        return self.chemin.rsplit('/', 1)[-1]

    @property
    def parent(self) -> str:
        return self.chemin.rsplit('/', 1)[0] if '/' in self.chemin else ''

    def vers_dict(self) -> dict:
        return {'chemin': self.chemin, 'dossier': self.dossier, 'taille': self.taille, 'modifie': self.modifie,
                'etag': self.etag, 'mime': self.mime}

    @classmethod
    def de_dict(cls, d: dict) -> 'Entree':
        return cls(d['chemin'], bool(d['dossier']), int(d.get('taille') or 0), float(d.get('modifie') or 0),
                   d.get('etag', ''), d.get('mime', ''))


def droits_de(permissions: str) -> list[str]:
    """Liste ordonnée des droits annoncés par oc:permissions (« RGDNVCK » → lire, déposer, dossiers…)."""
    vus = {LETTRES[c] for c in (permissions or '') if c in LETTRES}
    return [d for d in ORDRE_DROITS if d in vus]


def _date_http(texte: str) -> float:
    try:
        return email.utils.parsedate_to_datetime(texte).timestamp()
    except (TypeError, ValueError, IndexError):
        return 0.0


def analyser_multistatus(octets: bytes, prefixe_racine: str) -> list[Entree]:
    """Réponse 207 d'un PROPFIND -> entrées (chemins relatifs à la racine du partage)."""
    try:
        racine = ET.fromstring(octets)
    except ET.ParseError as e:
        raise ErreurPartage('pt_err_reponse', 207, str(e)) from None
    out = []
    pref = urllib.parse.unquote(prefixe_racine).rstrip('/') + '/'
    for rep in racine.findall('d:response', NS):
        href = urllib.parse.unquote((rep.findtext('d:href', '', NS) or '').strip())
        if '://' in href:
            href = urllib.parse.urlsplit(href).path
        if href.startswith(pref):
            rel = href[len(pref):]
        elif href.rstrip('/') + '/' == pref:
            rel = ''
        else:
            k = href.find('/public.php/webdav')
            rel = href[k + len('/public.php/webdav'):] if k >= 0 else href
        rel = rel.strip('/')
        if '..' in rel.split('/'):                 # jamais de chemin qui remonte
            continue
        props = {}
        for ps in rep.findall('d:propstat', NS):
            if '200' not in (ps.findtext('d:status', '', NS) or ''):
                continue
            p = ps.find('d:prop', NS)
            if p is not None:
                for enfant in p:
                    props[enfant.tag] = enfant
        rt = props.get('{DAV:}resourcetype')
        dossier = rt is not None and rt.find('d:collection', NS) is not None

        def texte(tag):
            e = props.get(tag)
            return (e.text or '').strip() if e is not None and e.text else ''
        taille = texte('{DAV:}getcontentlength') or texte('{http://owncloud.org/ns}size') or '0'
        out.append(Entree(rel, dossier, int(taille) if taille.isdigit() else 0,
                          _date_http(texte('{DAV:}getlastmodified')), texte('{DAV:}getetag').strip('"'),
                          texte('{DAV:}getcontenttype'), texte('{http://owncloud.org/ns}permissions')))
    return out


# ============================================================================================== client
class _Lecteur:
    """Fichier lu par blocs pour un PUT, avec progression."""

    def __init__(self, f, progression=None):
        self.f, self.progression = f, progression

    def read(self, n=-1):
        b = self.f.read(65536 if n is None or n < 0 else min(n, 65536))
        if b and self.progression is not None:
            self.progression(len(b))
        return b

    def __iter__(self):
        while True:
            b = self.read()
            if not b:
                return
            yield b


@dataclass
class InfoPartage:
    droits: list = field(default_factory=list)
    permissions: str = ''
    entrees: list = field(default_factory=list)      # contenu de la racine
    libre: int = -1                                   # octets disponibles annoncés (-1 : inconnu)
    etag: str = ''


class Client:
    METHODES = ('PROPFIND', 'GET', 'PUT', 'MKCOL')    # les seules ; voir l'en-tête du module

    def __init__(self, partage: Partage, delai: float = 30.0):
        self.partage = partage
        self.delai = delai
        self._verrou = threading.Lock()
        self.requetes = 0

    # ------------------------------------------------------------------ bas niveau
    def _requete(self, methode: str, chemin: str = '', corps: bytes | None = None, en_tetes: dict | None = None,
                 max_octets: int = TAILLE_MAX_LISTE, url: str | None = None):
        if methode not in self.METHODES:            # garde-fou : rien d'autre ne part jamais
            raise ValueError('method not allowed: %s' % methode)
        h = {'User-Agent': reseau.user_agent()}
        h.update(self.partage.en_tetes())
        h.update(en_tetes or {})
        req = urllib.request.Request(url or self.partage.url(chemin), data=corps, headers=h, method=methode)
        with self._verrou:
            self.requetes += 1
        try:
            with urllib.request.urlopen(req, timeout=self.delai) as r:
                return r.status, dict(r.headers), r.read(max_octets + 1)
        except urllib.error.HTTPError as e:
            code = e.code
            if code == 412:
                raise Conflit('pt_err_412', 412) from None
            cle = {401: 'pt_err_401', 403: 'pt_err_403', 404: 'pt_err_404', 405: 'pt_err_405', 409: 'pt_err_409',
                   423: 'pt_err_423', 507: 'pt_err_507'}.get(code, 'pt_err_http')
            raise ErreurPartage(cle, code) from None
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise ErreurPartage('pt_err_reseau', 0, '%s: %s' % (type(e).__name__, e)) from None

    # ------------------------------------------------------------------ lecture
    def propfind(self, chemin: str = '', profondeur: int = 1) -> list[Entree]:
        statut, _, corps = self._requete('PROPFIND', chemin, CORPS_PROPFIND,
                                         {'Depth': str(int(profondeur)), 'Content-Type': 'application/xml'})
        if len(corps) > TAILLE_MAX_LISTE:
            raise ErreurPartage('pt_err_trop_grand', statut)
        if statut != 207:
            raise ErreurPartage('pt_err_reponse', statut)
        return analyser_multistatus(corps, urllib.parse.urlsplit(self.partage.racine).path)

    def verifier(self) -> InfoPartage:
        """Vérifie le lien : droits et contenu de la racine (une seule requête)."""
        entrees = self.propfind('', 1)
        racine = next((e for e in entrees if e.chemin == ''), None)
        if racine is None:
            raise ErreurPartage('pt_err_reponse', 207)
        return InfoPartage(droits_de(racine.permissions), racine.permissions,
                           [e for e in entrees if e.chemin], -1, racine.etag)

    def etat(self, chemin: str) -> Entree | None:
        """Entrée d'un fichier ou dossier (PROPFIND profondeur 0) ; None s'il n'existe pas."""
        try:
            e = self.propfind(chemin, 0)
        except ErreurPartage as ex:
            if ex.code == 404:
                return None
            raise
        return e[0] if e else None

    def lister_tout(self, arret: threading.Event | None = None, progression=None, max_dossiers: int = 5000,
                    paralleles: int = 3) -> list[Entree]:
        """Toute l'arborescence, dossier par dossier (profondeur 1 : « infinity » est souvent refusé)."""
        import concurrent.futures as F
        vus: dict[str, Entree] = {}
        a_lire = ['']
        n = 0
        with F.ThreadPoolExecutor(max_workers=max(1, paralleles)) as ex:
            while a_lire:
                if arret is not None and arret.is_set():
                    raise reseau.Annule()
                lot, a_lire = a_lire[:paralleles * 4], a_lire[paralleles * 4:]
                for chemin, entrees in zip(lot, ex.map(lambda c: self.propfind(c, 1), lot)):
                    n += 1
                    for e in entrees:
                        if e.chemin == chemin:
                            if chemin == '' or chemin not in vus:
                                vus[chemin] = e
                            continue
                        if e.chemin in vus:
                            continue
                        vus[e.chemin] = e
                        if e.dossier:
                            if n + len(a_lire) >= max_dossiers:
                                raise ErreurPartage('pt_err_trop_grand', 207)
                            a_lire.append(e.chemin)
                    if progression is not None:
                        progression(n, len(vus))
        return [vus[k] for k in sorted(vus) if k]

    def lire(self, chemin: str, debut: int | None = None, fin: int | None = None, max_octets: int = 64_000_000) -> bytes:
        """Contenu d'un fichier, ou d'une plage d'octets [debut, fin] (« Range »)."""
        h = {}
        if debut is not None:
            h['Range'] = 'bytes=%d-%s' % (debut, '' if fin is None else int(fin))
        _, _, corps = self._requete('GET', chemin, None, h, max_octets)
        if len(corps) > max_octets:
            raise ErreurPartage('pt_err_trop_grand', 200)
        return corps

    def lire_avec_etag(self, chemin: str, max_octets: int = 64_000_000) -> tuple[bytes, str]:
        _, en_tetes, corps = self._requete('GET', chemin, None, None, max_octets)
        if len(corps) > max_octets:
            raise ErreurPartage('pt_err_trop_grand', 200)
        etag = ''
        for k, v in en_tetes.items():
            if k.lower() == 'etag':
                etag = v.strip().strip('"')
        return corps, etag

    def telecharger(self, chemin: str, destination: str, taille: int | None = None, limiteur=None, arret=None,
                    progression=None) -> tuple[str, int]:
        """Même moteur que la Banque OHP (reprise .part + Range, débit partagé, annulation)."""
        return reseau.telecharger(self.partage.url(chemin), destination, taille_attendue=taille, tolerance=0,
                                  limiteur=limiteur, arret=arret, progression=progression,
                                  en_tetes=self.partage.en_tetes())

    # ------------------------------------------------------------------ dépôt (toujours conditionnel)
    def deposer(self, chemin: str, donnees: bytes, si_etag: str | None = None, type_mime: str = '') -> str:
        """PUT conditionnel.  Sans `si_etag` : le fichier NE DOIT PAS exister (If-None-Match: *) ; avec : il doit
        avoir encore cet ETag (If-Match).  Lève Conflit si la condition ne tient plus.  Rend le nouvel ETag (ou '')."""
        h = {'Content-Type': type_mime or 'application/octet-stream'}
        if si_etag:
            h['If-Match'] = '"%s"' % si_etag.strip('"')
        else:
            h['If-None-Match'] = '*'
        _, en_tetes, _ = self._requete('PUT', chemin, bytes(donnees), h, 1_000_000)
        for k, v in en_tetes.items():
            if k.lower() in ('etag', 'oc-etag'):
                return v.strip().strip('"')
        return ''

    def deposer_fichier(self, chemin: str, local: str, si_etag: str | None = None, progression=None,
                        type_mime: str = '') -> str:
        """Comme `deposer`, en lisant le fichier local par blocs (grandes vidéos) ; `progression(n)` par bloc."""
        import os as _os
        taille = _os.path.getsize(local)
        h = {'Content-Type': type_mime or 'application/octet-stream', 'Content-Length': str(taille)}
        if si_etag:
            h['If-Match'] = '"%s"' % si_etag.strip('"')
        else:
            h['If-None-Match'] = '*'
        with open(local, 'rb') as f:
            corps = _Lecteur(f, progression)
            _, en_tetes, _ = self._requete('PUT', chemin, corps, h, 1_000_000)
        for k, v in en_tetes.items():
            if k.lower() in ('etag', 'oc-etag'):
                return v.strip().strip('"')
        return ''

    def creer_dossier(self, chemin: str) -> bool:
        """MKCOL ; False si le dossier existe déjà (405)."""
        try:
            self._requete('MKCOL', chemin.rstrip('/') + '/')
        except ErreurPartage as e:
            if e.code == 405:
                return False
            raise
        return True
