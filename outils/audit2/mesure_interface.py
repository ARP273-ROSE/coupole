"""Mesures GUI (fil graphique) à l'échelle réelle puis ×10."""
import os, sys, time, copy
os.environ.setdefault('COUPOLE_HOME', '/travail/home')
os.environ['COUPOLE_SANS_RESEAU'] = '1'
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from coupole.cli import initialiser
initialiser('fr')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint, QPointF, QEvent
from PyQt6.QtGui import QMouseEvent
app = QApplication([])
from coupole.gui import theme
theme.appliquer(app)
from coupole.core import config
config.reglages()['dossier_sortie'] = '/travail/copie'
config.reglages()['ohp_verifier_nouveautes'] = False
FACTEUR = int(sys.argv[1]) if len(sys.argv) > 1 else 1
R = []
def calme():
    from coupole.gui import outils as _o
    fin = time.time() + 60
    while any(t.isRunning() for t in list(_o._actives)) and time.time() < fin:
        app.processEvents(); time.sleep(0.01)
    app.processEvents()
def chrono(nom, f, *a, **k):
    calme()
    t = time.perf_counter(); r = f(*a, **k); app.processEvents(); d = time.perf_counter() - t
    R.append((nom, d)); print('%-55s %8.1f ms' % (nom, d * 1000), flush=True); return r
def attendre(pred, t=60):
    fin = time.time() + t
    while not pred() and time.time() < fin:
        app.processEvents(); time.sleep(0.01)
from coupole.modules.ohp.inventaire import Inventaire
inv = Inventaire.charger()
if FACTEUR > 1:
    base = inv.images
    imgs = []
    for k in range(FACTEUR):
        for x in base:
            y = dict(x)
            if k:
                y['access_url'] = x['access_url'] + '?k=%d' % k
                y['objet'] = x['objet'] + ' %d' % k if k % 2 else x['objet']
                y['t_min'] = x['t_min'] + k * 1e-4
            imgs.append(y)
    inv.images = imgs
print('images', len(inv.images), 'objets', len(inv.objets()))
from coupole.modules.ohp.gui import Panneau
t = time.perf_counter()
p = Panneau()
p.resize(1400, 900); p.show()
print('construction Panneau %.0f ms' % ((time.perf_counter() - t) * 1000))
attendre(lambda: p.inv is not None)
p._t_inv.wait() if hasattr(p, '_t_inv') else None
app.processEvents()
chrono('_inventaire_pret (remplissage complet)', p._inventaire_pret, inv)
attendre(lambda: p.possession.existe, 30)
chrono('_possession_prete (re-run)', p._possession_prete, (p.possession, p._infos_ok))
chrono('_filtrer_objets (texte "m")', lambda: p.recherche.setText('m'))
chrono('_filtrer_objets (texte "")', lambda: p.recherche.setText(''))
chrono('case manquantes', lambda: p.f_manquantes.setChecked(True))
chrono('case manquantes off', lambda: p.f_manquantes.setChecked(False))
def _sync():
    t = getattr(p, '_minuteur_choix', None)
    if t is not None and t.isActive():
        t.stop(); p._objets_choisis()
chrono('selection 1 objet', lambda: (p.v_obj.selectRow(0), _sync()))
chrono('selection de tout (objets)', lambda: (p.v_obj.selectAll(), _sync()))
print('lignes images', p.m_img.rowCount())
chrono('tri images col date', lambda: p.v_img.sortByColumn(1, Qt.SortOrder.DescendingOrder))
chrono('tri images col possede', lambda: p.v_img.sortByColumn(0, Qt.SortOrder.AscendingOrder))
chrono('tri objets col images', lambda: p.v_obj.sortByColumn(3, Qt.SortOrder.DescendingOrder))
chrono('tri objets col possede', lambda: p.v_obj.sortByColumn(4, Qt.SortOrder.DescendingOrder))
chrono('filtre nuit (combo idx 1)', lambda: p.f_nuit.setCurrentIndex(1))
chrono('filtre nuit (tous)', lambda: p.f_nuit.setCurrentIndex(0))
chrono('select all images', p.v_img.selectAll)
chrono('_remplir_lots', p._remplir_lots)
chrono('reglages_changes (theme)', p.reglages_changes)
p.onglets.setCurrentIndex(4); app.processEvents()
chrono('_remplir_ciel', p._remplir_ciel)
print('points ciel', len(p.ciel.points))
attendre(lambda: __import__('coupole.gui.cartes', fromlist=['x'])._lignes_ciel is not None)
chrono('ciel repaint', p.ciel.repaint)
def survol():
    for k in range(10):
        ev = QMouseEvent(QEvent.Type.MouseMove, QPointF(100 + 30 * k, 150), QPointF(100 + 30 * k, 150), Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        p.ciel.mouseMoveEvent(ev)
chrono('ciel 10 survols', survol)
p.onglets.setCurrentIndex(3); app.processEvents()
attendre(lambda: len(p._anoms) > 0, 60)
chrono('_filtrer_anomalies', p._filtrer_anomalies)
print('anomalies', len(p._anoms))
p.onglets.setCurrentIndex(0); app.processEvents()
chrono('repaint table objets', p.v_obj.viewport().repaint)
chrono('repaint table images', p.v_img.viewport().repaint)
print('MAX', max(R, key=lambda r: r[1]))
