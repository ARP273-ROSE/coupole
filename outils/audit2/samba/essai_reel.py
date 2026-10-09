"""Essai réel : 3 images de (914) Palisana depuis le serveur de l'Observatoire vers /mnt/partage/OHP_DU_ECU_essai (Samba de
test, voir essai.sh) ; affiche les événements, la base finale du partage (statuts, meta, intégrité) et JOURNAL.txt."""
import os, sqlite3, sys, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
os.environ['XDG_CACHE_HOME'] = '/tmp/reel-cache'; os.environ['XDG_CONFIG_HOME'] = '/tmp/reel-conf'
from coupole.cli import initialiser
initialiser('fr')
from coupole.core.parallele import Plan
from coupole.modules.ohp.inventaire import Inventaire
from coupole.modules.ohp.pilote import Traitement
def principal():
    inv = Inventaire.charger()
    sel = [x for x in inv.images if 'Palisana' in x['objet'] and not x['doublon']][2:5]
    print(len(sel), [x['access_url'].rsplit('/', 1)[1] for x in sel], sum(x['access_estsize'] for x in sel) / 1024, 'Mo')
    dest = '/mnt/partage/OHP_DU_ECU_essai'
    def rapporter(ev):
        if ev['type'] in ('octets',):
            return
        print(time.strftime('%H:%M:%S'), ev if ev['type'] != 'fin' else {k: ev['bilan'][k] for k in ('compte', 'duree', 'lots')}, flush=True)
    t = Traitement(dest, inv, Plan(2, 2, False, 'essai'), {'format': 'xisf', 'langue': 'fr', 'mode_astap': 'jamais'}, rapporter=rapporter)
    try:
        t.lancer(sel)
    finally:
        t.fermer()
    p = dest + '/_traitement/etat.sqlite'
    db = sqlite3.connect('file:%s?mode=ro' % p, uri=True)
    print('base du partage :', db.execute('select statut, count(*) from images group by statut').fetchall(),
          db.execute('select * from meta').fetchall(), db.execute('PRAGMA integrity_check').fetchone())
    print(sorted(os.listdir(dest + '/_traitement')))
    print(open(dest + '/_traitement/JOURNAL.txt', encoding='utf-8').read()[-1500:])


if __name__ == '__main__':
    principal()
