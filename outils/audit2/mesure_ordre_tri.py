"""Empreintes de ce que montre le catalogue (0.1.5) : cellules des images, objets, anomalies, carte du ciel, lots, et
ordre de la table des images après chacun de 36 tris (9 colonnes × croissant/décroissant × 2 passes, chaque tri
partant du précédent), avec leur durée.  À lancer sur l'ancien code (PYTHONPATH=/travail/avant) et sur le nouveau,
puis comparer les deux JSON.  Usage : mesure_ordre_tri.py FACTEUR SORTIE.json"""
import os, sys, time, hashlib, json
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mesure_interface.py')).read().split("print('images'")[0])
from coupole.modules.ohp import inventaire as INV
INV.Inventaire.charger = classmethod(lambda cls, r=False: inv)
from coupole.modules.ohp.gui import Panneau


def empreinte(objet):
    return hashlib.sha1(repr(objet).encode()).hexdigest()[:16]


p = Panneau(); p.resize(1400, 900); p.show()
attendre(lambda: p.inv is not None and p.possession.existe and len(p._anoms) > 0 and len(p.ciel.points) > 0, 120)
attendre(lambda: p.m_lots.rowCount() > 0, 20)
calme()
res = {'cellules': empreinte([p._ligne_image(x) for x in inv.images]),
       'objets': empreinte([tuple(map(str, l)) for l in p.m_obj.lignes]),
       'anomalies': empreinte([tuple(map(str, l)) for l in p.m_anom.lignes]),
       'ciel': empreinte(sorted(str((q[0], q[1], q[2], q[3].name(), q[4], q[5])) for q in p.ciel.points)),
       'lots': empreinte([tuple(map(str, l)) for l in p.m_lots.lignes])}
print(res)
p.v_obj.selectAll(); p._minuteur_choix.stop(); p._objets_choisis(); app.processEvents()
assert p.m_img.rowCount() == len(inv.images), p.m_img.rowCount()
for passe in (1, 2):
    for col in range(9):
        for ordre in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
            t = time.perf_counter()
            p.v_img.sortByColumn(col, ordre)
            d = time.perf_counter() - t
            h = empreinte([x['access_url'] for x in p.m_img.donnees])
            res['%d/%d/%s' % (passe, col, ordre.name)] = h
            print('passe %d col %d %-16s %6.0f ms  %s' % (passe, col, ordre.name, d * 1000, h), flush=True)
json.dump(res, open(sys.argv[2], 'w'), indent=1)
