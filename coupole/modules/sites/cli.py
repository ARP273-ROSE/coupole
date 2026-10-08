"""coupole sites [--ajouter ...] [--supprimer ID] [--heure ISO --site ID]"""
from __future__ import annotations

import datetime as D

from ...core import sites, temps
from ...core.i18n import tr


def enregistrer(p):
    p.add_argument('--ajouter', '--add', nargs='+', metavar='X', help=tr('sit_aide_ajouter'))
    p.add_argument('--supprimer', '--delete', metavar=tr('cli_meta_id'), help=tr('sit_aide_supprimer'))
    p.add_argument('--heure', '--time', metavar=tr('cli_meta_iso'), help=tr('sit_aide_heure'))
    p.add_argument('--site', default='ohp', metavar=tr('cli_meta_id'), help=tr('sit_aide_site'))
    p.set_defaults(fonction=cmd)


def verifier_fuseau(nom: str) -> bool:
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(nom)
        return True
    except Exception:
        return False


def cmd(a):
    if a.ajouter:
        v = a.ajouter
        if len(v) < 6:
            print(tr('sit_aide_ajouter'))
            return 2
        if not verifier_fuseau(v[5]):
            print(tr('sit_fuseau_invalide', fuseau=v[5]))
            return 2
        sites.enregistrer_site({'id': v[0], 'nom': v[1], 'lat': float(v[2]), 'lon': float(v[3]), 'alt': float(v[4]),
                                'fuseau': v[5], 'mpc': v[6] if len(v) > 6 else ''})
    if a.supprimer:
        sites.supprimer_site(a.supprimer)
    if a.heure:
        s = sites.site(a.site)
        u = temps.iso_vers_utc(a.heure)
        if s is None or u is None:
            return 2
        print(temps.formater(u, s))
        print(tr('sit_date_du_soir', d=temps.date_du_soir(u, s)))
        print(tr('sit_soleil', h='%.1f' % temps.hauteur_soleil(u, s)))
        return 0
    maintenant = D.datetime.now(D.timezone.utc)
    for s in sites.sites():
        print('%-8s %-40s %9.5f %10.5f %6.0f  %-4s %-20s %s  [%s]' % (
            s.id, s.nom[:40], s.lat, s.lon, s.alt, s.mpc, s.fuseau or '~', temps.heure_locale(maintenant, s)
            .strftime('%H:%M'), tr('sit_origine_' + s.origine)))
    return 0
