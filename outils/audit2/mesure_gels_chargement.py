"""Chargement réel (fil de fond) à 10 × la banque : plus long gel du fil graphique (battement de 10 ms)."""
import os, sys, time
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mesure_interface.py')).read().split("print('images'")[0])
from coupole.modules.ohp import inventaire as INV
INV.Inventaire.charger = classmethod(lambda cls, r=False: inv)
from coupole.modules.ohp.gui import Panneau
from PyQt6.QtCore import QTimer
ecarts = []; dernier = [time.perf_counter()]
def bat():
    t = time.perf_counter(); ecarts.append((t - dernier[0], t)); dernier[0] = t
tm = QTimer(); tm.timeout.connect(bat); tm.start(10)
t0 = time.perf_counter()
p = Panneau(); p.resize(1400, 900); p.show()
attendre(lambda: p.inv is not None and p.possession.existe and len(p._anoms) > 0 and len(p.ciel.points) > 0, 120)
calme()
print('pret en %.0f ms ; plus long gel %.0f ms' % ((time.perf_counter() - t0) * 1000, max(e for e, _ in ecarts) * 1000))
ecarts.clear(); dernier[0] = time.perf_counter()
p.v_obj.selectAll()
attendre(lambda: p.m_img.rowCount() == len(inv.images), 30); calme(); time.sleep(0.3); app.processEvents(); calme()
print('tout selectionner (+ estimation en fond) : plus long gel %.0f ms' % (max(e for e, _ in ecarts) * 1000))
for col in (0, 1, 5, 0):
    ecarts.clear(); dernier[0] = time.perf_counter()
    p.v_img.sortByColumn(col, Qt.SortOrder.AscendingOrder); app.processEvents(); calme()
    time.sleep(0.05); app.processEvents()
    print('tri colonne %d : plus long gel %.0f ms' % (col, max(e for e, _ in ecarts) * 1000))
