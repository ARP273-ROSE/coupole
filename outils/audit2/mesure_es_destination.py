"""Fonctions d'E/S : destination locale vs partage simulé (FUSE, 2 ms par opération)."""
import os, sys, time, json
os.environ.setdefault('COUPOLE_HOME', '/travail/home_reseau')
os.environ['COUPOLE_SANS_RESEAU'] = '1'
from coupole.cli import initialiser
initialiser('fr')
from coupole.modules.ohp.inventaire import Inventaire
from coupole.modules.ohp import possession, lots, anomalies
from coupole.modules.ohp.pilote import Etat, Traitement
from coupole.core.parallele import Plan
dest = sys.argv[1]
quoi = sys.argv[2:] or ['lire', 'ranger', 'etat', 'doublons']
def chrono(nom, f, *a, **k):
    t = time.perf_counter(); r = f(*a, **k); d = time.perf_counter() - t
    print('%-50s %9.3f s' % (nom, d), flush=True); return r
inv = Inventaire.charger()
if 'lire' in quoi:
    chrono('Possession.lire', possession.Possession.lire, dest)
    chrono('lire_infos_ok', possession.lire_infos_ok, dest)
    chrono('depuis_traitement', anomalies.depuis_traitement, dest + '/_traitement/etat.sqlite')
    def lire_index():
        import csv
        with open(os.path.join(dest, 'INDEX_LOTS.csv'), encoding='utf-8-sig') as f:
            return list(csv.reader(f, delimiter=';'))
    chrono('lecture INDEX_LOTS.csv', lire_index)
if 'ranger' in quoi:
    t = Traitement(dest, inv, Plan(1, 1, True, ''), {'format': 'xisf', 'langue': 'fr'})
    idx = chrono('Traitement.ranger (rien à déplacer)', t.ranger)
    print('  lots', len(idx))
    t.fermer()
if 'etat' in quoi:
    e = Etat(os.path.join(dest, '_traitement', 'essai_etat.sqlite'))
    def ecritures(n=100):
        for k in range(n):
            e.ecrire('id%d' % k, 'u', 'ok', {'a': k})
    chrono('Etat.ecrire x100 (commit chacun)', ecritures)
    e.fermer()
    e = Etat(os.path.join(dest, '_traitement', 'essai_etat.sqlite'), 1.0)
    chrono('Etat.ecrire x100 (validation groupee 1 s)', ecritures)
    chrono('  fermer (validation finale)', e.fermer)
    os.remove(os.path.join(dest, '_traitement', 'essai_etat.sqlite'))
if 'doublons' in quoi:
    import shutil
    d2 = os.path.join(dest, '_essai_doublons')
    shutil.rmtree(d2, ignore_errors=True)
    t = Traitement(d2, inv, Plan(1, 1, True, ''), {'format': 'xisf', 'langue': 'fr'})
    dbl = [x for x in inv.images if x['doublon']]
    def debut():
        for x in dbl:
            from coupole.modules.ohp.conversion import ident, info_de_base
            i = ident(x)
            if t.etat.lire(i)[0] is None:
                t.etat.ecrire(i, x['access_url'], 'doublon', dict(info_de_base(x), doublon_de='inventaire'), 0)
                t.journal.ecrire('jrn_doublon_inventaire', source=x['access_url'].rsplit('/', 1)[1], raison='x')
    chrono('lancer(): %d doublons notés un par un' % len(dbl), debut)
    chrono('a_faire(toute la banque)', t.a_faire, inv.images)
    t.fermer()
    shutil.rmtree(d2, ignore_errors=True)
