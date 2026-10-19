"""Serveur WebDAV factice d'un partage public Nextcloud, pour les essais (aucune requête ne sort de la machine).

Il répond à ``/public.php/webdav/<chemin>`` comme Nextcloud : authentification « Basic » (identifiant = jeton du
partage, mot de passe éventuel), PROPFIND (profondeur 0 ou 1, réponse 207 avec ``oc:permissions``), GET (avec
« Range » et ETag), PUT conditionnel (``If-None-Match: *`` / ``If-Match`` → 412 si la condition ne tient plus) et
MKCOL (405 si le dossier existe).  Les méthodes DELETE, MOVE, COPY et PROPPATCH sont NOTÉES puis refusées (405) : les
essais vérifient qu'aucune n'est jamais envoyée.
"""
from __future__ import annotations

import base64
import email.utils
import hashlib
import http.server
import threading
import time
import urllib.parse
from xml.sax.saxutils import escape

RACINE = '/public.php/webdav'


class _Gestionnaire(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    serveur_test = None

    def log_message(self, *a):
        pass

    # ------------------------------------------------------------------ outils
    def _chemin(self) -> str | None:
        p = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        if not (p == RACINE or p.startswith(RACINE + '/')):
            return None
        return p[len(RACINE):].strip('/')

    def _auth(self) -> bool:
        s = self.serveur_test
        h = self.headers.get('Authorization', '')
        if not h.startswith('Basic '):
            return False
        try:
            jeton, _, mdp = base64.b64decode(h[6:]).decode('utf-8').partition(':')
        except ValueError:
            return False
        return jeton == s.jeton and mdp == s.mot_de_passe

    def _repondre(self, code: int, corps: bytes = b'', en_tetes: dict | None = None):
        self.send_response(code)
        for k, v in (en_tetes or {}).items():
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(corps)))
        self.end_headers()
        if corps and self.command != 'HEAD':
            self.wfile.write(corps)

    def _corps(self) -> bytes:
        n = int(self.headers.get('Content-Length') or 0)
        return self.rfile.read(n) if n else b''

    def _entree(self):
        s = self.serveur_test
        with s.verrou:
            s.requetes.append((self.command, self.path, dict(self.headers)))
        if not self._auth():
            self._corps()
            self._repondre(401, b'', {'WWW-Authenticate': 'Basic realm="Nextcloud"'})
            return None
        c = self._chemin()
        if c is None:
            self._corps()
            self._repondre(404)
            return None
        return c

    # ------------------------------------------------------------------ méthodes
    def do_PROPFIND(self):
        c = self._entree()
        if c is None:
            return
        self._corps()
        s = self.serveur_test
        profondeur = self.headers.get('Depth', '1')
        with s.verrou:
            if c and c not in s.fichiers and c not in s.dossiers:
                self._repondre(404)
                return
            reponses = [s.xml_entree(c)]
            if c in s.dossiers and profondeur != '0':
                pref = c + '/' if c else ''
                for x in sorted(set(s.fichiers) | s.dossiers):
                    if x and x.startswith(pref) and '/' not in x[len(pref):]:
                        reponses.append(s.xml_entree(x))
        corps = ('<?xml version="1.0"?><d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" '
                 'xmlns:nc="http://nextcloud.org/ns">%s</d:multistatus>' % ''.join(reponses)).encode('utf-8')
        self._repondre(207, corps, {'Content-Type': 'application/xml; charset=utf-8'})

    def do_GET(self):
        c = self._entree()
        if c is None:
            return
        s = self.serveur_test
        with s.verrou:
            contenu = s.fichiers.get(c)
            etag = s.etags.get(c, '')
        if contenu is None:
            self._repondre(404)
            return
        rg = self.headers.get('Range')
        if rg:
            a, b = rg.split('=')[1].split('-')
            debut = int(a)
            fin = min(int(b), len(contenu) - 1) if b else len(contenu) - 1
            if debut >= len(contenu):
                self._repondre(416)
                return
            self._repondre(206, contenu[debut:fin + 1], {'ETag': '"%s"' % etag,
                                                         'Content-Range': 'bytes %d-%d/%d' % (debut, fin, len(contenu))})
            return
        self._repondre(200, contenu, {'ETag': '"%s"' % etag, 'Accept-Ranges': 'bytes'})

    def do_PUT(self):
        c = self._entree()
        if c is None:
            return
        corps = self._corps()
        s = self.serveur_test
        with s.verrou:
            if s.avant_put is not None:                  # simuler un autre étudiant qui écrit au même moment
                f, s.avant_put = s.avant_put, None
                f(s, c)
            if 'C' not in s.permissions and 'W' not in s.permissions:
                self._repondre(403)
                return
            parent = c.rsplit('/', 1)[0] if '/' in c else ''
            if parent not in s.dossiers:
                self._repondre(409)
                return
            existe = c in s.fichiers
            inm, im = self.headers.get('If-None-Match'), self.headers.get('If-Match')
            if inm == '*' and existe:
                self._repondre(412)
                return
            if im is not None and (not existe or im.strip('"') != s.etags.get(c)):
                self._repondre(412)
                return
            if existe and inm is None and im is None and not s.ecrasement_permis:
                s.ecrasements.append(c)
            s.poser(c, corps)
            etag = s.etags[c]
        self._repondre(204 if existe else 201, b'', {'ETag': '"%s"' % etag, 'OC-ETag': '"%s"' % etag})

    def do_MKCOL(self):
        c = self._entree()
        if c is None:
            return
        self._corps()
        s = self.serveur_test
        with s.verrou:
            if c in s.dossiers or c in s.fichiers:
                self._repondre(405)
                return
            s.dossiers.add(c)
        self._repondre(201)

    def _interdit(self):
        s = self.serveur_test
        with s.verrou:
            s.interdites.append((self.command, self.path))
        self._entree()
        self._corps()
        self._repondre(405)

    do_DELETE = do_MOVE = do_COPY = do_PROPPATCH = do_LOCK = _interdit


class ServeurWebdav:
    """`fichiers` : {chemin relatif: bytes} ; les dossiers parents sont créés.  `permissions` : lettres oc:permissions
    de la racine (« GCK » : lire, déposer, créer des dossiers)."""

    def __init__(self, fichiers: dict | None = None, jeton: str = 'AbCdEf123456', mot_de_passe: str = '',
                 permissions: str = 'GCK', dates: dict | None = None):
        self.jeton, self.mot_de_passe, self.permissions = jeton, mot_de_passe, permissions
        self.fichiers: dict[str, bytes] = {}
        self.etags: dict[str, str] = {}
        self.dates: dict[str, float] = {}
        self.dossiers: set[str] = {''}
        self.requetes: list = []
        self.interdites: list = []
        self.ecrasements: list = []
        self.ecrasement_permis = False
        self.avant_put = None
        self.verrou = threading.RLock()
        for c, v in (fichiers or {}).items():
            self.poser(c, v, (dates or {}).get(c))
        gest = type('Gest', (_Gestionnaire,), {'serveur_test': self})
        self.http = http.server.ThreadingHTTPServer(('127.0.0.1', 0), gest)
        self.http.daemon_threads = True
        self.fil = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.fil.start()

    def poser(self, chemin: str, contenu: bytes, date: float | None = None):
        chemin = chemin.strip('/')
        parties = chemin.split('/')
        for k in range(1, len(parties)):
            self.dossiers.add('/'.join(parties[:k]))
        self.fichiers[chemin] = bytes(contenu)
        self.etags[chemin] = hashlib.md5(bytes(contenu) + str(time.monotonic_ns()).encode()).hexdigest()
        self.dates[chemin] = date if date is not None else time.time()

    def xml_entree(self, c: str) -> str:
        href = RACINE + '/' + '/'.join(urllib.parse.quote(p) for p in c.split('/') if p)
        if c in self.dossiers:
            href = href.rstrip('/') + '/'
            props = '<d:resourcetype><d:collection/></d:resourcetype><oc:permissions>%s</oc:permissions>' % (
                escape(self.permissions) if c == '' else 'GCK')
            props += '<d:getetag>"dir%s"</d:getetag>' % hashlib.md5(c.encode()).hexdigest()[:8]
        else:
            props = ('<d:resourcetype/><d:getcontentlength>%d</d:getcontentlength><d:getetag>"%s"</d:getetag>'
                     '<d:getlastmodified>%s</d:getlastmodified><d:getcontenttype>application/octet-stream'
                     '</d:getcontenttype><oc:permissions>G</oc:permissions>'
                     % (len(self.fichiers[c]), self.etags[c], email.utils.formatdate(self.dates[c], usegmt=True)))
        return ('<d:response><d:href>%s</d:href><d:propstat><d:prop>%s</d:prop><d:status>HTTP/1.1 200 OK</d:status>'
                '</d:propstat></d:response>' % (escape(href), props))

    @property
    def base(self) -> str:
        return 'http://127.0.0.1:%d' % self.http.server_address[1]

    @property
    def lien(self) -> str:
        """Lien de partage tel qu'un étudiant le colle (« …/s/<jeton> »)."""
        return '%s/s/%s' % (self.base, self.jeton)

    def methodes(self) -> set:
        with self.verrou:
            return {m for m, _, _ in self.requetes}

    def fermer(self):
        self.http.shutdown()
        self.http.server_close()
