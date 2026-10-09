import os, time
os.environ['COUPOLE_HOME'] = '/travail/home'
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from coupole.cli import initialiser
initialiser('fr')
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF, QEvent, Qt
from PyQt6.QtGui import QMouseEvent
app = QApplication([])
from coupole.gui.trace import Trace
for n in (4000, 1_000_000):
    t = Trace(); t.resize(1400, 700); t.show(); app.processEvents()
    x = np.linspace(1400, 1430, n); y = np.random.randn(n).cumsum()
    t0 = time.perf_counter(); t.definir(x, y, 'x', 'y'); t.repaint(); d = time.perf_counter() - t0
    t0 = time.perf_counter()
    for k in range(10):
        ev = QMouseEvent(QEvent.Type.MouseMove, QPointF(100 + 50 * k, 200), QPointF(100 + 50 * k, 200), Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        t.mouseMoveEvent(ev); t.repaint()
    print(n, 'points : definir+dessin %.0f ms ; survol (dessin) %.1f ms' % (d * 1000, (time.perf_counter() - t0) * 100))
