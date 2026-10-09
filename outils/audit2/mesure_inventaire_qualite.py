"""Chronomètre la phase « Inventaire du dossier… » du module Qualité, comme l'interface l'enchaîne, sur un vrai
partage SMB (montage cifs du noyau, latence ajoutée par `tc netem`) ou tout autre dossier.

    python mesure_inventaire_qualite.py DOSSIER [--repetitions N] [--sans-base] [--sans-index] [--cache-plein] [--jusqu-au-bout]

--sans-base : 0.1.9, ignore la sortie Coupole (parcours du dossier) ; --sans-index : ignore INDEX_LOTS.csv
(base d'état seule) ; --cache-plein : 0.1.9, cache rempli avant
la mesure (relance) ; --jusqu-au-bout : attend la fin (toutes les images) au lieu de l'inventaire.

Le code mesuré est celui trouvé par PYTHONPATH : 0.1.8 (planifier → estimer_duree → Mesureur, arrêt au
« début ») ou 0.1.9 (Mesureur en flux : inventaire et mesure en même temps, arrêt quand l'inventaire est fini).
Rend une ligne JSON par répétition : durées des étapes, premier résultat affiché, inventaire complet."""
import json, sys, threading, time

def principal():
    global etapes
    racine = sys.argv[1]
    rep = int(sys.argv[sys.argv.index('--repetitions') + 1]) if '--repetitions' in sys.argv else 1
    from coupole.core.parallele import Plan
    from coupole.modules.qualite import moteur

    etapes = {}
    def chrono(objet, nom, cle=None):
        f = getattr(objet, nom)
        def g(*a, **k):
            t = time.perf_counter()
            try:
                return f(*a, **k)
            finally:
                etapes[cle or nom] = round(etapes.get(cle or nom, 0.0) + time.perf_counter() - t, 3)
        setattr(objet, nom, g)

    chrono(moteur.CacheMesures, '__init__', 'CacheMesures()')
    for n in ('planifier', 'estimer_duree', 'empreintes', 'est_reseau'):
        if hasattr(moteur, n):
            chrono(moteur, n)
    ancien = hasattr(moteur, 'planifier')
    plan = Plan(1, 2, False, 'x')
    bout = '--jusqu-au-bout' in sys.argv
    if '--sans-base' in sys.argv:
        moteur.sortie_coupole = lambda r, *a: None
    if '--sans-index' in sys.argv:
        moteur.lots_index = lambda *a: None
    if '--cache-plein' in sys.argv and not ancien:
        import os
        t = time.perf_counter()
        c = moteur.CacheMesures(racine)
        from coupole.core import parcours
        for d, fs, dates in parcours.parcourir(racine, (".xisf",), a_dater=lambda f: f):
            for f, e in dates.items():
                c.ecrire(f, e[0], e[1], {'fichier': os.path.basename(f), 'fwhm_px': 3.0})
        c.fermer()
        print(json.dumps({'cache_rempli_s': round(time.perf_counter() - t, 3)}))

    for r in range(rep):
        etapes.clear()
        ev_t = {}
        arret = threading.Event()
        t0 = time.perf_counter()

        def rapporter(ev):
            t = round(time.perf_counter() - t0, 3)
            typ = ev['type']
            if typ == 'image':
                ev_t.setdefault('premiere_image', t)
            elif typ == 'inventaire':
                ev_t.setdefault('premier_comptage', t)
                if ev.get('fini'):
                    ev_t['inventaire_fini'] = t
                    ev_t['trouves'] = ev.get('trouves')
                    ev_t['source'] = ev.get('source')
                    if not bout:
                        arret.set()
            elif typ == 'debut':
                ev_t['debut'] = t
                if ancien:
                    arret.set()
        if ancien:                                   # le chemin de l'interface 0.1.8 : plan, estimation, moteur
            p = moteur.planifier(racine, None)
            ev_t['plan'] = round(time.perf_counter() - t0, 3)
            if p['total_dossier'] > moteur.SEUIL_GROS_DOSSIER and p['a_mesurer'] > 3:
                p['chemin'] = racine
                moteur.estimer_duree(p, 2)
                ev_t['estimation'] = round(time.perf_counter() - t0, 3)
            moteur.Mesureur(racine, plan, None, rapporter=rapporter, arret=arret, ecrire_rapports=False,
                            plan_dossier=p).lancer()
        else:
            b = moteur.Mesureur(racine, plan, None, rapporter=rapporter, arret=arret, ecrire_rapports=False,
                                demander=True, n_echantillon=10 ** 6 if bout else 5).lancer()
            ev_t.update(n=b['n'], deja=b['deja'], absentes=b['absentes'])
        print(json.dumps({'repetition': r, 'total_s': round(time.perf_counter() - t0, 3), 'etapes_s': etapes,
                          'evenements_s': ev_t}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    principal()
