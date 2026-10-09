"""Chaîne complète (serveur HTTP local) vers une destination donnée (locale ou partage simulé)."""
import os, sys, time, threading, tempfile, shutil
sys.path.insert(0, '/src/outils'); sys.path.insert(0, '/src/tests')
def main():
    dest = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    os.environ.setdefault('COUPOLE_HOME', tempfile.mkdtemp(prefix='m15-'))
    from coupole.cli import initialiser
    initialiser('fr')
    from coupole.core import machine, parallele
    from coupole.modules.ohp import inventaire as INV
    from coupole.modules.ohp.pilote import Traitement
    from serveur_local import ServeurLocal
    from pipeline import fits_bytes
    brut, meta = INV.lire(INV.INSTANTANE)
    rangs = [x for x in brut if 'palisana' in x['access_url'].lower()][:1] * n
    s = ServeurLocal(); lignes = []
    for k, x in enumerate(rangs):
        c = fits_bytes(x['s_ra'] + k * 0.001, x['s_dec'], k, 512)
        s.fichiers['/i%d.fits' % k] = c
        lignes.append(dict(x, access_url=s.url('/i%d.fits' % k), access_estsize=len(c) / 1024))
    inv = INV.Inventaire(lignes, meta)
    plan = parallele.planifier(machine.detecter())
    shutil.rmtree(dest, ignore_errors=True); os.makedirs(dest)
    t = Traitement(dest, inv, plan, {'format': 'xisf', 'langue': 'fr', 'debit_octets_s': 1e12}, arret=threading.Event())
    t0 = time.perf_counter(); b = t.lancer(inv.images); dt = time.perf_counter() - t0; t.fermer()
    print('%s : %d images en %.1f s (%.2f s/image), ok=%d, plan %d dl / %d conv' % (dest, n, dt, dt / n, b['compte']['ok'], plan.telechargements, plan.conversions))
    t = Traitement(dest, inv, plan, {'format': 'xisf', 'langue': 'fr'})
    t0 = time.perf_counter(); t.lancer(inv.images); print('  relance (tout fait) %.1f s' % (time.perf_counter() - t0)); t.fermer()
    s.fermer()
if __name__ == '__main__':
    main()
