"""Serveur HTTP local pour les tests : sert des fichiers en mémoire avec HTTP Range, compte les requêtes,
et sait simuler des pannes (coupure au milieu, refus, lenteur).  Aucune requête ne sort de la machine."""
from __future__ import annotations

import http.server
import threading
import time


class _Gestionnaire(http.server.BaseHTTPRequestHandler):
    serveur_test = None            # instance de ServeurLocal (posée à la création)

    def log_message(self, *a):
        pass

    def do_GET(self):
        s = self.serveur_test
        with s.verrou:
            s.requetes.append((self.path, self.headers.get('Range', '')))
            panne = s.pannes.get(self.path)
        contenu = s.fichiers.get(self.path)
        if contenu is None:
            self.send_error(404)
            return
        if panne == 'refus' or (panne == 'refus_apres_premiere' and s.compter(self.path) > 1):
            self.send_error(503)
            return
        debut, fin = 0, len(contenu) - 1
        rg = self.headers.get('Range')
        if rg:
            a, b = rg.split('=')[1].split('-')
            debut = int(a)
            fin = int(b) if b else fin
            if debut >= len(contenu):
                self.send_error(416)
                return
        corps = contenu[debut:fin + 1]
        self.send_response(206 if rg else 200)
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (debut, fin, len(contenu)))
        self.send_header('Content-Length', str(len(corps)))
        self.end_headers()
        if panne == 'coupure_une_fois' and len(corps) > 4000:
            with s.verrou:
                s.pannes.pop(self.path, None)
            self.wfile.write(corps[:4000])
            return
        if s.lenteur:
            for i in range(0, len(corps), 65536):
                self.wfile.write(corps[i:i + 65536])
                time.sleep(s.lenteur)
            return
        self.wfile.write(corps)


class ServeurLocal:
    """`fichiers` : {chemin ('/a.fits'): bytes}.  `pannes` : {chemin: 'refus' | 'refus_apres_premiere' | 'coupure_une_fois'}."""

    def __init__(self, fichiers: dict | None = None, lenteur: float = 0.0):
        self.fichiers = dict(fichiers or {})
        self.pannes: dict = {}
        self.requetes: list = []
        self.lenteur = lenteur
        self.verrou = threading.Lock()
        gest = type('Gest', (_Gestionnaire,), {'serveur_test': self})
        self.http = http.server.ThreadingHTTPServer(('127.0.0.1', 0), gest)
        self.http.daemon_threads = True
        self.fil = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.fil.start()

    @property
    def base(self) -> str:
        return 'http://127.0.0.1:%d' % self.http.server_address[1]

    def url(self, chemin: str) -> str:
        return self.base + chemin

    def compter(self, chemin: str) -> int:
        with self.verrou:
            return sum(1 for p, _ in self.requetes if p == chemin)

    def fermer(self):
        self.http.shutdown()
        self.http.server_close()
