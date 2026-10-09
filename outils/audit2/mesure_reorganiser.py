import os, sys, time
os.environ.setdefault('COUPOLE_HOME', '/travail/home_m6')
os.environ['COUPOLE_SANS_RESEAU'] = '1'
from coupole.cli import initialiser
initialiser('fr')
from coupole.modules.ohp.inventaire import Inventaire
from coupole.modules.ohp import reorganisation
if __name__ == '__main__':
  inv = Inventaire.charger()
  racine = sys.argv[1]; sous = sys.argv[2] if len(sys.argv) > 2 else ''
  t = time.perf_counter()
  tr_, ig = reorganisation.inventorier(os.path.join(racine, sous), inv, '/nulle/part', progression=lambda f, n: None)
  print('inventorier(%s) %.1f s' % (sous or 'tout', time.perf_counter() - t), len(tr_), 'trouvés', len(ig), 'ignorés')
