"""coupole qualite DOSSIER [--ecrire] [--echantillon N | --tout] [--processus N] [--avec-calibration]"""
from __future__ import annotations

import os
import sys
import threading

from ...core.i18n import langue, tr
from . import mesures, moteur, rapport


def enregistrer(p):
    p.add_argument('dossier', metavar=tr('cli_meta_dossier'), help=tr('qual_aide_dossier'))
    p.add_argument('--ecrire', '--write', action='store_true', help=tr('qual_aide_ecrire'))
    p.add_argument('--echantillon', '--sample', type=int, default=None, metavar='N', help=tr('qual_aide_echantillon'))
    p.add_argument('--tout', '--all', action='store_true', help=tr('qual_aide_tout'))
    p.add_argument('--processus', '--processes', type=int, default=None, metavar='N', help=tr('qual_aide_processus'))
    p.add_argument('--avec-calibration', '--with-calibration', action='store_true', help=tr('qual_aide_avec_calibration'))
    p.set_defaults(fonction=cmd)


def cmd(a):
    if not mesures.disponible():
        print(tr('qual_absent'), file=sys.stderr)
        return 3
    from .gui_sans_qt import duree_lisible
    ech = a.echantillon
    # inventaire et mesure en flux ; au-delà de 200 images (sans --tout), échantillon choisi d'office
    auto = ech is None and not a.tout
    racine = a.dossier
    etat = {'dernier': 0.0}

    def rapporter(ev):
        t = ev['type']
        if t == 'decision':
            print(tr('qual_cli_echantillon_auto', total=ev['total_dossier'], n=ev['n']))
        elif t == 'debut':
            texte = tr('qual_debut', total=ev['total'], lots=ev['lots'], deja=ev['deja'], processus=ev['processus'])
            if ev['echantillon']:
                texte += ' ' + tr('qual_debut_echantillon', n=ev['echantillon'], dossier=ev['total_dossier'])
            if ev['reseau']:
                texte += ' ' + tr('qual_reseau')
            print(texte)
        elif t == 'progression':
            import time
            if time.monotonic() - etat['dernier'] >= 5 and ev['eta_s'] is not None:    # une ligne toutes les 5 s
                etat['dernier'] = time.monotonic()
                print(tr('qual_cli_progression', fait=ev['fait'], total=ev['total'], eta=duree_lisible(ev['eta_s'])))
        elif t == 'lot':
            d = ev['lot']
            print(tr('qual_lot', lot=os.path.relpath(d, racine) if os.path.isdir(racine) else d, n=len(ev['lignes'])))
            for l in rapport.resume(ev['lignes'], langue()):
                print('  ' + l)
        elif t == 'fin':
            print(tr('qual_fini', n=ev['n'], lots=ev['lots'], deja=ev['deja'], duree=duree_lisible(ev['duree'])))
            print(rapport.bilan_texte(ev))
            from .calibration import texte_motif
            for f, motif in sorted(ev.get('liste_exclus') or [])[:50]:
                print('  - %s — %s' % (os.path.relpath(f, racine) if os.path.isdir(racine) else f, texte_motif(motif)))
            if len(ev.get('liste_exclus') or []) > 50:
                print('  …')
            if ev['annule']:
                print(tr('interrompu_reprise'))
    arret = threading.Event()
    m = moteur.Mesureur(racine, None, ech, rapporter=rapporter, arret=arret, ecrire_rapports=a.ecrire,
                        processus_max=a.processus, langue=langue(), auto=auto,
                        avec_calibration=getattr(a, 'avec_calibration', False))
    try:
        b = m.lancer()
    except KeyboardInterrupt:
        arret.set()
        return 130
    return 1 if b['annule'] or (b['echecs'] and not b['mesurees_ok']) else 0     # tout en erreur : jamais « 0 »
