import os, time, sys
os.environ['COUPOLE_HOME'] = '/travail/home_carte'
os.environ['COUPOLE_SANS_RESEAU'] = '1'
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from coupole.cli import initialiser
initialiser('fr')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QColor, QPainter
app = QApplication([])
from coupole.gui.cartes import CarteMonde, TAILLE_TUILE
from coupole.core import config
import random
c = CarteMonde(en_ligne=True)
c.resize(1400, 900); c.show(); app.processEvents()
# tuiles PNG réalistes (bruit) dans le cache disque pour les niveaux 5 à 7
def tuile(p):
    im = QImage(256, 256, QImage.Format.Format_RGB32)
    for y in range(0, 256, 4):
        for x in range(0, 256, 4):
            im.setPixelColor(x, y, QColor(random.randrange(256), random.randrange(256), random.randrange(256)))
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(str(p))
base = tuile
for z in (5, 6):
    n = 2 ** z
    for x in range(n):
        for y in range(n):
            p = c.cache.chemin(z, x, y)
            if not p.exists():
                tuile(p)
c.cache.hors_ligne = True       # pas de téléchargement
def mesure(nom, f):
    t = time.perf_counter(); f(); app.processEvents(); print('%-40s %7.1f ms' % (nom, (time.perf_counter() - t) * 1000), flush=True)
c.centrer(2.7, 48.8, 5)
c.cache.memoire.clear()
mesure('premier dessin z5 (tuiles lues sur disque)', c.repaint)
mesure('dessin suivant z5 (memoire)', c.repaint)
for k in range(6):
    c.centrer(2.7 + 25 * k, 48.8, 5)
    mesure('glisser %d' % k, c.repaint)
c.centrer(2.7, 48.8, 6)
mesure('zoom z6 (tuiles neuves)', c.repaint)
import time as T
T.sleep(0.3); app.processEvents()
mesure('z6 apres arrivee des tuiles', c.repaint)
c.cache.memoire.clear()
from PyQt6.QtCore import Qt

