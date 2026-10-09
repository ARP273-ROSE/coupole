"""Chargement réel (fil de fond) à 10 × la banque : plus long gel du fil graphique (battement de 10 ms).

0.1.5 : la construction du panneau (synchrone, indépendante de la taille de la banque) est mesurée à part ; les
attentes se font en traitant les événements (l'ancien `time.sleep(0.3)` du fil graphique comptait lui-même pour un
« gel » de 300 ms après « tout sélectionner ») ; les tris couvrent les neuf colonnes de la table des images.
"""
import os, sys, time
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mesure_interface.py')).read().split("print('images'")[0])
from coupole.modules.ohp import inventaire as INV
INV.Inventaire.charger = classmethod(lambda cls, r=False: inv)
from coupole.modules.ohp.gui import Panneau
from PyQt6.QtCore import QTimer
ecarts = []; dernier = [time.perf_counter()]
def bat():
    t = time.perf_counter(); ecarts.append((t - dernier[0], t)); dernier[0] = t
def remise():
    ecarts.clear(); dernier[0] = time.perf_counter()
def patienter(s):
    fin = time.perf_counter() + s
    while time.perf_counter() < fin:
        app.processEvents(); time.sleep(0.005)
def pire():
    return max(e for e, _ in ecarts) * 1000 if ecarts else 0.0
tm = QTimer(); tm.timeout.connect(bat); tm.start(10)
t0 = time.perf_counter()
p = Panneau(); p.resize(1400, 900); p.show()
print('construction du panneau %.0f ms' % ((time.perf_counter() - t0) * 1000))
remise()
attendre(lambda: p.inv is not None and p.possession.existe and len(p._anoms) > 0 and len(p.ciel.points) > 0, 120)
calme(); patienter(0.3); calme()
print('pret en %.0f ms ; plus long gel %.0f ms' % ((time.perf_counter() - t0) * 1000, pire()))
remise()
p.v_obj.selectAll()
attendre(lambda: p.m_img.rowCount() == len(inv.images), 30); calme(); patienter(0.3); calme()
print('tout selectionner (+ estimation en fond) : plus long gel %.0f ms' % pire())
for col in (2, 7, 0, 1, 5, 2):
    remise()
    t = time.perf_counter()
    p.v_img.sortByColumn(col, Qt.SortOrder.AscendingOrder)
    d = time.perf_counter() - t
    calme(); patienter(0.05)
    print('tri colonne %d : %.0f ms ; plus long gel %.0f ms' % (col, d * 1000, pire()))
