"""coupole qualite DOSSIER [--ecrire] [--echantillon N | --tout] [--processus N]"""
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
    p.set_defaults(fonction=cmd)


def cmd(a):
    if not mesures.disponible():
        print(tr('qual_absent'), file=sys.stderr)
        return 3
    from .gui_sans_qt import duree_lisible
    ech = a.echantillon
    plan_dossier = moteur.planifier(a.dossier, ech)        # un seul parcours du dossier, repris par le moteur
    if ech is None and not a.tout:
        total = plan_dossier['total_dossier']
        if total > moteur.SEUIL_GROS_DOSSIER:
            ech = moteur.ECHANTILLON_DEFAUT
            print(tr('qual_cli_echantillon_auto', total=total, n=ech))
    racine = a.dossier
    etat = {'dernier': 0.0}

    def rapporter(ev):
        t = ev['type']
        if t == 'debut':
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
            if ev['annule']:
                print(tr('interrompu_reprise'))
    arret = threading.Event()
    m = moteur.Mesureur(racine, None, ech, rapporter=rapporter, arret=arret, ecrire_rapports=a.ecrire,
                        processus_max=a.processus, langue=langue(), plan_dossier=plan_dossier)
    try:
        b = m.lancer()
    except KeyboardInterrupt:
        arret.set()
        return 130
    return 1 if b['annule'] else 0
