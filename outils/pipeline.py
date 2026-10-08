"""Mesure de la chaîne complète sur un serveur LOCAL (aucune requête publique) : débit de chaque étape et étape
limitante.  Chiffres reportés dans docs/AUDIT_2026-10.md.

    QT_QPA_PLATFORM=offscreen python outils/pipeline.py [N_IMAGES] [COTE] [DEBIT_MO_S]

Étapes mesurées, séparément puis enchaînées :
  1. inventaire : enrichissement de l'instantané livré (7 989 lignes) ;
  2. téléchargement seul (fils, débit plafonné ou non) ;
  3. conversion seule (un processus, cProfile : lecture FITS, contrôles, empreinte, écriture XISF + relecture) ;
  4. chaîne complète (pilote : téléchargements + conversions en pipeline) ;
  5. rangement (lots, LOT.txt, INDEX_LOTS.csv, journaux).
"""
import cProfile
import io
import json
import os
import pstats
import sys
import tempfile
import threading
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / 'tests'))


def fits_bytes(ra, dec, seed, cote, dtype='>f8'):
    import numpy as np
    from astropy.io import fits
    h = fits.Header()
    h['CTYPE1'], h['CTYPE2'] = 'RA---TAN', 'DEC--TAN'
    h['CRVAL1'], h['CRVAL2'] = ra, dec
    h['CRPIX1'], h['CRPIX2'] = cote / 2, cote / 2
    h['CD1_1'], h['CD2_2'], h['CD1_2'], h['CD2_1'] = -0.77 / 3600, 0.77 / 3600, 0.0, 0.0
    h['DATE-OBS'] = '2023-08-15T22:08:42.000'
    h['EXPTIME'] = 20.0
    h['LATITUDE'], h['LONGITUD'] = '05 42 44', '43 55 54'
    h['XPIXSZ'], h['FOCALLEN'] = 13.5, 3600.0
    a = np.random.default_rng(seed).normal(1000, 30, (cote, cote)).astype(dtype)
    buf = io.BytesIO()
    fits.PrimaryHDU(a, header=h).writeto(buf)
    return buf.getvalue()


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    cote = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    debit = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0            # 0 : sans plafond
    os.environ.setdefault('COUPOLE_HOME', tempfile.mkdtemp(prefix='coupole-pipeline-'))
    from coupole.cli import initialiser
    initialiser('fr')
    from coupole.core import machine, parallele, reseau
    from coupole.modules.ohp import inventaire as INV
    from coupole.modules.ohp.conversion import convertir
    from coupole.modules.ohp.pilote import Traitement
    from serveur_local import ServeurLocal
    r = {'n': n, 'cote': cote, 'debit_plafond_mo_s': debit}

    # 1. inventaire
    t0 = time.perf_counter()
    brut, meta = INV.lire(INV.INSTANTANE)
    t1 = time.perf_counter()
    inv0 = INV.Inventaire(brut, meta)
    t2 = time.perf_counter()
    r['inventaire'] = {'lecture_s': round(t1 - t0, 3), 'enrichissement_s': round(t2 - t1, 3), 'lignes': len(inv0.images)}

    # banque locale : n images d'un même objet mobile (une nuit)
    rangs = [x for x in brut if 'palisana' in x['access_url'].lower()][:1] * n
    s = ServeurLocal()
    lignes = []
    for k, x in enumerate(rangs):
        contenu = fits_bytes(x['s_ra'] + k * 0.001, x['s_dec'], k, cote)
        s.fichiers['/i%d.fits' % k] = contenu
        lignes.append(dict(x, access_url=s.url('/i%d.fits' % k), access_estsize=len(contenu) / 1024))
    inv = INV.Inventaire(lignes, meta)
    octets = sum(len(v) for v in s.fichiers.values())
    r['octets_total_mo'] = round(octets / 1e6, 1)
    m = machine.detecter()
    plan = parallele.planifier(m)
    r['plan'] = {'telechargements': plan.telechargements, 'conversions': plan.conversions, 'coeurs': m.coeurs_physiques}

    # 2. téléchargement seul
    with tempfile.TemporaryDirectory() as d:
        lim = reseau.LimiteurDebit(debit * 1e6) if debit else None
        import concurrent.futures as F
        t0 = time.perf_counter()
        with F.ThreadPoolExecutor(plan.telechargements) as ex:
            list(ex.map(lambda x: reseau.telecharger(x['access_url'], os.path.join(d, os.path.basename(x['access_url'])),
                                                     int(x['access_estsize'] * 1024), limiteur=lim), inv.images))
        dt = time.perf_counter() - t0
        r['telechargement_seul'] = {'s': round(dt, 2), 'mo_s': round(octets / dt / 1e6, 1), 'images_s': round(n / dt, 2),
                                    'requetes': len(s.requetes)}
        # 3. conversion seule (un processus, dans ce processus pour le profil)
        fic = os.path.join(d, 'i0.fits')
        x = dict(inv.images[0], nuit=str(inv.images[0]['nuit']))
        from coupole.modules.ohp.astrometrie import attentes, attentes_pour
        med, medo = attentes(inv.images)
        m1, m2 = attentes_pour(x, med, medo)
        pr = cProfile.Profile()
        t0 = time.perf_counter()
        pr.enable()
        info = convertir(x, fic, os.path.join(d, 'i0.xisf'), m1, m2, {'format': 'xisf', 'langue': 'fr'})
        pr.disable()
        dt = time.perf_counter() - t0
        st = io.StringIO()
        pstats.Stats(pr, stream=st).sort_stats('cumulative').print_stats(18)
        r['conversion_seule'] = {'s': round(dt, 3), 'mo_fits_s': round(len(s.fichiers['/i0.fits']) / dt / 1e6, 1),
                                 'ratio': info['ratio'], 'profil': [l.strip() for l in st.getvalue().splitlines()
                                                                    if 'coupole' in l or 'zstandard' in l or 'astropy' in l][:14]}

    # 4. chaîne complète
    s.requetes.clear()
    with tempfile.TemporaryDirectory() as d:
        evts = []
        t = Traitement(d, inv, plan, {'format': 'xisf', 'langue': 'fr', 'debit_octets_s': debit * 1e6 if debit else 1e12},
                       rapporter=evts.append, arret=threading.Event())
        t0 = time.perf_counter()
        b = t.lancer(inv.images)
        dt = time.perf_counter() - t0
        t.fermer()
        premiers = [e for e in evts if e['type'] == 'image']
        r['chaine_complete'] = {'s': round(dt, 2), 'images_s': round(n / dt, 2), 'mo_fits_s': round(octets / dt / 1e6, 1),
                                'ok': b['compte']['ok'], 'evenements_octets': sum(1 for e in evts if e['type'] == 'octets'),
                                'evenements_total': len(evts), 'requetes_http': len(s.requetes),
                                'duree_pilote_s': b['duree']}
        # 5. rangement seul (déjà inclus ; on le remesure)
        t0 = time.perf_counter()
        t = Traitement(d, inv, plan, {'format': 'xisf', 'langue': 'fr'})
        t.ranger()
        t.fermer()
        r['rangement_s'] = round(time.perf_counter() - t0, 3)
    s.fermer()
    # étape limitante
    conv_par_s = plan.conversions / r['conversion_seule']['s']
    dl_par_s = r['telechargement_seul']['images_s']
    r['limite'] = {'conversions_images_s_theorique': round(conv_par_s, 2), 'telechargement_images_s': round(dl_par_s, 2),
                   'etape_limitante': 'reseau' if dl_par_s < conv_par_s else 'conversion'}
    print(json.dumps(r, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
