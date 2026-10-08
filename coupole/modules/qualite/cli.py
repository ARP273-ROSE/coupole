"""coupole qualite DOSSIER [--ecrire]"""
from __future__ import annotations

import os
import sys

from ...core.i18n import langue, tr
from . import mesures, rapport


def enregistrer(p):
    p.add_argument('dossier', metavar=tr('cli_meta_dossier'), help=tr('qual_aide_dossier'))
    p.add_argument('--ecrire', '--write', action='store_true', help=tr('qual_aide_ecrire'))
    p.set_defaults(fonction=cmd)


def cmd(a):
    if not mesures.disponible():
        print(tr('qual_absent'), file=sys.stderr)
        return 3
    lots = rapport.fichiers(a.dossier)
    n = 0
    for d, imgs in lots.items():
        print(tr('qual_lot', lot=os.path.relpath(d, a.dossier) if os.path.isdir(a.dossier) else d, n=len(imgs)))
        lignes = rapport.analyser_lot(imgs)
        n += len(lignes)
        for l in rapport.resume(lignes, langue()):
            print('  ' + l)
        if a.ecrire:
            rapport.ecrire(d, lignes)
    print(tr('qual_fini', n=n, lots=len(lots)))
    return 0
