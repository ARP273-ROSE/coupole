"""coupole donnees lire|exporter FICHIER"""
from __future__ import annotations

import csv
import json

import numpy as np

from ...core import donnees
from ...core.i18n import tr


def enregistrer(p):
    sous = p.add_subparsers(dest='don_commande', metavar=tr('cli_commande'), title=tr('cli_commandes'))
    s = sous.add_parser('lire', aliases=['read'], help=tr('don_cli_lire'), description=tr('don_cli_lire'),
                        formatter_class=p.formatter_class)
    s.add_argument('fichier', metavar=tr('cli_meta_fichier'), help=tr('don_aide_fichier'))
    s.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    s.set_defaults(fonction=cmd_lire)
    s = sous.add_parser('exporter', aliases=['export'], help=tr('don_cli_exporter'), description=tr('don_cli_exporter'),
                        formatter_class=p.formatter_class)
    s.add_argument('fichier', metavar=tr('cli_meta_fichier'), help=tr('don_aide_fichier'))
    s.add_argument('--csv', required=True, metavar=tr('cli_meta_fichier'), help=tr('don_cli_exporter'))
    s.add_argument('--hdu', type=int, default=None, help=tr('don_aide_hdu'))
    s.add_argument('--vitesse', '--velocity', action='store_true', help=tr('don_aide_vitesse'))
    s.add_argument('--f0', type=float, default=None, metavar='MHz', help=tr('don_aide_f0'))
    s.set_defaults(fonction=cmd_exporter)
    p.set_defaults(fonction=lambda a: (print(tr('don_formats', liste=', '.join('%s (%s)' % f for f in donnees.formats()))),
                                       p.print_help(), 0)[2])


def cmd_lire(a):
    ds = donnees.lire(a.fichier)
    if a.json:
        print(json.dumps([d.resume() for d in ds], ensure_ascii=False, indent=1, default=str))
        return 0
    for i, d in enumerate(ds):
        r = d.resume()
        print('[%d] %s %s %s' % (i, tr('don_genre_' + d.genre), d.titre,
                                 ('n=%d %s [%s] %.6g → %.6g' % (r['n'], d.nom_x, d.unite_x, r['x'][0], r['x'][1]))
                                 if 'n' in r else r.get('forme', r.get('colonnes', ''))))
    return 0


def colonnes(d, vitesse=False, f0_mhz=None):
    """(en-têtes, colonnes) à exporter ou afficher."""
    x, y = d.x, d.y
    tete = ['%s [%s]' % (d.nom_x, d.unite_x) if d.unite_x else d.nom_x, '%s [%s]' % (d.nom_y, d.unite_y)
            if d.unite_y else d.nom_y]
    cols = [x, y]
    if vitesse and d.meta.get('axe') == 'freq':
        f0 = f0_mhz * 1e6 if f0_mhz else (d.meta.get('restfreq_hz') or donnees.HI_HZ)
        cols.append(donnees.vitesse_radio(donnees.en_hz(x, d.unite_x or 'Hz'), f0))
        tete.append('v_radio [km s^-1] (f0=%.9g MHz)' % (f0 / 1e6))
    return tete, cols


def cmd_exporter(a):
    ds = [d for d in donnees.lire(a.fichier) if d.x is not None]
    d = ds[a.hdu] if a.hdu is not None else ds[0]
    tete, cols = colonnes(d, a.vitesse, a.f0)
    with open(a.csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(tete)
        for ligne in zip(*cols):
            w.writerow(['%.10g' % v for v in ligne])
    print(tr('ecrit', chemin=a.csv))
    return 0
