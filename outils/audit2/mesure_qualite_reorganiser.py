"""Réorganiser (inventorier les en-têtes) et Qualité (planifier, relance tout en cache) sur la banque réelle."""
import os, sys, time, json
os.environ.setdefault('COUPOLE_HOME', '/travail/home_m6')
os.environ['COUPOLE_SANS_RESEAU'] = '1'
from coupole.cli import initialiser
initialiser('fr')
from coupole.modules.ohp.inventaire import Inventaire
from coupole.modules.ohp import reorganisation
racine = sys.argv[1]
quoi = sys.argv[2]
def chrono(nom, f, *a, **k):
    t = time.perf_counter(); r = f(*a, **k); d = time.perf_counter() - t
    print('%-55s %9.3f s' % (nom, d), flush=True); return r
inv = Inventaire.charger()
if quoi == 'reorg':
    sous = sys.argv[3] if len(sys.argv) > 3 else ''
    tr_, ig = chrono('inventorier(%s)' % (sous or 'tout'), reorganisation.inventorier, os.path.join(racine, sous), inv, '/nulle/part')
    print(len(tr_), 'trouvés', len(ig), 'ignorés')
if quoi == 'qualite' and __name__ == '__main__':
    from coupole.modules.qualite import moteur, rapport
    chrono('rapport.fichiers (walk)', rapport.fichiers, racine)
    p = chrono('planifier(tout, cache vide)', moteur.planifier, racine, None)
    print(p['retenus'], 'retenus', p['deja'], 'deja', 'reseau', p['reseau'])
    # cache rempli artificiellement : relance « tout est déjà mesuré »
    c = moteur.CacheMesures(racine)
    t0 = time.perf_counter()
    for d, imgs in p['lots'].items():
        for f in imgs:
            st = os.stat(f)
            c.db.execute('INSERT OR REPLACE INTO mesures VALUES (?,?,?,?,?)', (f, st.st_size, st.st_mtime, json.dumps({'fichier': os.path.basename(f), 'fwhm_px': 3.0, 'ellipticite': 0.1, 'fond_adu': 100, 'bruit_adu': 5}), 'x'))
    c.db.commit(); c.fermer()
    print('cache rempli en %.1f s' % (time.perf_counter() - t0))
    p = chrono('planifier(tout, cache plein)', moteur.planifier, racine, None)
    evs = []
    m = moteur.Mesureur(racine, None, None, rapporter=evs.append, ecrire_rapports=False)
    chrono('Mesureur.lancer (tout en cache)', m.lancer)
    if hasattr(moteur, 'replanifier'):
        evs.clear()
        p = chrono('planifier (dialogue) + lancer avec ce plan : planifier', moteur.planifier, racine, None)
        m = moteur.Mesureur(racine, None, None, rapporter=evs.append, ecrire_rapports=False, plan_dossier=p)
        chrono('   puis Mesureur.lancer(plan_dossier)', m.lancer)
    print(len(evs), 'événements')
