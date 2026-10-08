"""Mesures de performance (chiffres reportés dans PROGRESSION.md) :

  1. démarrage : ligne de commande, fenêtre affichée, inventaire chargé ;
  2. mémoire de pointe d'une conversion (T120 1024² float64, IRIS 4096² float32), processus isolé ;
  3. réactivité de l'interface pendant un téléchargement (serveur local, aucune requête à l'Observatoire).

    QT_QPA_PLATFORM=offscreen python outils/mesures.py
"""
import http.server
import json
import os
import resource
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
PY = sys.executable


def demarrage_cli():
    t0 = time.perf_counter()
    subprocess.run([PY, '-m', 'coupole', '--version'], check=True, capture_output=True, cwd=RACINE)
    return time.perf_counter() - t0


def demarrage_gui():
    code = r'''
import time, sys
t0 = time.perf_counter()
from PyQt6.QtWidgets import QApplication
from coupole.cli import initialiser
from coupole.core import config
config.reglages()["rapports_autorises"] = False
config.reglages()["maj_auto"] = False
initialiser("fr")
app = QApplication(sys.argv)
from coupole.gui.fenetre import FenetrePrincipale
f = FenetrePrincipale(); f.show(); app.processEvents()
t1 = time.perf_counter()
while f.panneaux[0].inv is None:
    app.processEvents(); time.sleep(0.005)
t2 = time.perf_counter()
print("%.3f %.3f" % (t1 - t0, t2 - t0))
from coupole.gui.outils import attendre_taches
attendre_taches()
'''
    r = subprocess.run([PY, '-c', code], capture_output=True, text=True, cwd=RACINE,
                       env=dict(os.environ, QT_QPA_PLATFORM='offscreen'))
    a, b = r.stdout.split()[-2:]
    return float(a), float(b)


def memoire_conversion(nx, dtype):
    """Pic RSS d'un processus qui ne fait QUE la conversion (l'image d'essai est fabriquée par un autre processus :
    ru_maxrss est un maximum historique, la fabrication ne doit pas le gonfler)."""
    fabriquer = r'''
import sys, numpy as np
from astropy.io import fits
nx, dt, d = int(sys.argv[1]), sys.argv[2], sys.argv[3]
h = fits.Header(); h["CTYPE1"] = "RA---TAN"; h["CTYPE2"] = "DEC--TAN"; h["CRVAL1"] = 303.0; h["CRVAL2"] = 38.3
h["CRPIX1"] = nx / 2; h["CRPIX2"] = nx / 2; h["CD1_1"] = -0.46 / 3600; h["CD2_2"] = 0.46 / 3600
h["CD1_2"] = 0.0; h["CD2_1"] = 0.0; h["DATE-OBS"] = "2025-07-16T22:00:00"
a = np.random.default_rng(0).normal(1000, 30, (nx, nx)).astype(dt)
fits.PrimaryHDU(a, header=h).writeto(d + "/m.fits", overwrite=True)
'''
    code = r'''
import resource, sys, json
from coupole.cli import initialiser
initialiser("fr")
from coupole.modules.ohp import conversion
nx, d = int(sys.argv[1]), sys.argv[3]
base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
x = {"access_url": "http://x/m.fits", "objet": "NGC 6888", "cat": "neb", "tel": "IRIS", "nuit": "2025-07-16",
     "filter_name": "Ha", "t_exptime": 60.0, "t_min": 60872.9, "date_partagee": False, "target_name": "NGC 6888",
     "s_ra": 303.0, "s_dec": 38.3, "s_xel1": nx, "s_pixel_scale": 0.46, "site": "ohp", "diurne": False}
conversion.convertir(x, d + "/m.fits", d + "/m.xisf", {}, {}, {"format": "xisf"})
pic = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({"base_mo": round(base / 1024), "pic_mo": round(pic / 1024)}))
'''
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([PY, '-c', fabriquer, str(nx), dtype, d], check=True, cwd=RACINE)
        r = subprocess.run([PY, '-c', code, str(nx), dtype, d], capture_output=True, text=True, cwd=RACINE)
        return json.loads(r.stdout.strip().splitlines()[-1])


class Lent(http.server.BaseHTTPRequestHandler):
    taille = 8 * 2880 * 1000

    def log_message(self, *a):
        pass

    def do_GET(self):
        rg = self.headers.get('Range')
        debut, fin = 0, self.taille - 1
        if rg:
            a, b = rg.split('=')[1].split('-')
            debut, fin = int(a), (int(b) if b else fin)
        self.send_response(206 if rg else 200)
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (debut, fin, self.taille))
        self.send_header('Content-Length', str(fin - debut + 1))
        self.end_headers()
        bloc = b'SIMPLE  =                    T'.ljust(2880) if debut == 0 else b'\0' * 2880
        reste = fin - debut + 1
        while reste > 0:
            n = min(reste, 65536)
            self.wfile.write((bloc + b'\0' * 65536)[:n])
            bloc = b''
            reste -= n


def reactivite_pendant_telechargement():
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication
    from coupole.core import reseau
    app = QApplication.instance() or QApplication([])
    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Lent)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    url = 'http://127.0.0.1:%d/a.fits' % s.server_address[1]
    lim = reseau.LimiteurDebit(20e6)
    fin = threading.Event()

    def travail():
        with tempfile.TemporaryDirectory() as d:
            ths = [threading.Thread(target=reseau.telecharger, args=(url, os.path.join(d, '%d.fits' % i)),
                                    kwargs={'limiteur': lim}) for i in range(3)]
            for t in ths:
                t.start()
            for t in ths:
                t.join()
        fin.set()
    battements = []
    minuteur = QTimer()
    minuteur.timeout.connect(lambda: battements.append(time.monotonic()))
    minuteur.start(20)
    t0 = time.monotonic()
    threading.Thread(target=travail, daemon=True).start()
    while not fin.is_set():
        app.processEvents()
        time.sleep(0.002)
    duree = time.monotonic() - t0
    minuteur.stop()
    s.shutdown()
    ecarts = [b - a for a, b in zip(battements, battements[1:])]
    return {'duree_s': duree, 'debit_mo_s': 3 * Lent.taille / duree / 1e6, 'battements': len(battements),
            'ecart_max_ms': 1000 * max(ecarts), 'ecart_moyen_ms': 1000 * sum(ecarts) / len(ecarts)}


def main():
    os.environ.setdefault('COUPOLE_HOME', tempfile.mkdtemp(prefix='coupole-mesures-'))
    r = {'cli_version_s': demarrage_cli()}
    r['gui_fenetre_s'], r['gui_inventaire_s'] = demarrage_gui()
    r['conversion_T120_1024_float64'] = memoire_conversion(1024, '>f8')
    r['conversion_IRIS_4096_float32'] = memoire_conversion(4096, '>f4')
    r['gui_pendant_telechargement'] = reactivite_pendant_telechargement()
    print(json.dumps(r, indent=1))


if __name__ == '__main__':
    main()
