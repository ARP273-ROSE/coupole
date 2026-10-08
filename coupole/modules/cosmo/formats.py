"""Mise en forme des grandeurs cosmologiques (langue courante) et export CSV."""
from __future__ import annotations

import csv
import math

from ...core.i18n import langue, tr
from . import calcul

ESPACE = ' '                # espace fine insécable : séparateur des milliers


def nombre(x: float, dec: int = 3) -> str:
    if x is None or not math.isfinite(x):
        return '—'
    s = '{:,.{d}f}'.format(x, d=dec).replace(',', ESPACE)
    return s.replace('.', ',') if langue() == 'fr' else s


def chiffres(x: float, n: int = 4) -> str:
    """n chiffres significatifs, sans notation scientifique pour les valeurs usuelles."""
    if x is None or not math.isfinite(x):
        return '—'
    if x == 0:
        return '0'
    e = math.floor(math.log10(abs(x)))
    if -4 <= e < 9:
        return nombre(x, max(0, n - 1 - e))
    s = '%.*e' % (n - 1, x)
    return s.replace('.', ',') if langue() == 'fr' else s


def court(x: float) -> str:
    """Redshift ou paramètre sans zéros inutiles (« 0,158 », « 1089,8 »)."""
    if x is None or not math.isfinite(x):
        return '—'
    s = '%.6g' % x
    return s.replace('.', ',') if langue() == 'fr' else s


def annees_lumiere(mpc: float) -> str:
    al = mpc * calcul.al_par_mpc()
    for lim, cle in ((1e9, 'cosmo_u_gal'), (1e6, 'cosmo_u_mal'), (0.0, 'cosmo_u_kal')):
        if al >= lim:
            return '%s %s' % (chiffres(al / (lim or 1e3), 4), tr(cle))
    return '%s %s' % (chiffres(al / 1e3, 4), tr('cosmo_u_kal'))


def duree(gyr: float) -> str:
    if gyr >= 1:
        return '%s %s' % (chiffres(gyr, 5), tr('cosmo_u_gyr'))
    if gyr >= 1e-3:
        return '%s %s' % (chiffres(gyr * 1e3, 4), tr('cosmo_u_myr'))
    return '%s %s' % (chiffres(gyr * 1e6, 4), tr('cosmo_u_kyr'))


def valeur(cle: str, v: float) -> str:
    """Valeur affichée dans le tableau, avec son unité."""
    if v is None or not math.isfinite(v):
        return '—'
    if cle in calcul.DISTANCES:
        return '%s %s  ·  %s' % (chiffres(v, 5), tr('cosmo_u_mpc'), annees_lumiere(v))
    if cle in ('lookback_gyr', 'age_at_z', 't0_model'):
        return duree(v)
    if cle in ('a', 'E'):
        return chiffres(v, 6)
    if cle == 'H_z':
        return '%s %s' % (chiffres(v, 5), tr('cosmo_u_kms_mpc'))
    if cle == 'distmod':
        return '%s %s' % (nombre(v, 3), tr('cosmo_u_mag'))
    if cle == 'kpc_arcsec':
        if v < 1:
            return '%s %s' % (chiffres(v * 1e3, 4), tr('cosmo_u_pc_arcsec'))
        return '%s %s' % (chiffres(v, 4), tr('cosmo_u_kpc_arcsec'))
    if cle == 'vol_gpc3':
        return '%s %s' % (chiffres(v, 4), tr('cosmo_u_gpc3'))
    if cle.startswith('v_'):
        return '%s %s  (%s %s)' % (nombre(v, 0), tr('cosmo_u_kms'), nombre(v / calcul.c_kms(), 3), tr('cosmo_u_c'))
    return chiffres(v, 5)


def incertitude(cle: str, v: float, s: float) -> str:
    """« ± σ (pourcentage) » dans l'unité principale de la grandeur."""
    if s is None or v is None or not v:
        return ''
    pct = 100 * s / abs(v)
    if cle in calcul.DISTANCES:
        txt = '± %s %s' % (chiffres(s, 2), tr('cosmo_u_mpc'))
    elif cle in ('lookback_gyr', 'age_at_z', 't0_model'):
        txt = '± ' + duree(s)
    elif cle == 'distmod':
        return '± %s %s' % (nombre(s, 3), tr('cosmo_u_mag'))
    else:
        txt = '± ' + chiffres(s, 2)
    return '%s  (%s %%)' % (txt, nombre(pct, 2))


def unite_csv(unite: str) -> str:
    return {'': '', 'mpc': 'Mpc', 'gyr': 'Gyr', 'kms': 'km/s', 'kms_mpc': 'km/s/Mpc', 'mag': 'mag',
            'kpc_arcsec': 'kpc/arcsec', 'gpc3': 'Gpc3'}.get(unite, unite)


def ecrire_csv_resultats(chemin, resultats: list[dict]):
    """Une ligne par (z, grandeur) : valeurs brutes, unité SI-astro, incertitude, SH0ES, années-lumière."""
    al = calcul.al_par_mpc()
    with open(chemin, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['z', tr('cosmo_csv_cle'), tr('cosmo_col_grandeur'), tr('cosmo_col_valeur'), tr('cosmo_csv_unite'),
                    tr('cosmo_col_sigma'), tr('cosmo_col_shoes'), tr('cosmo_csv_al'), tr('cosmo_csv_parametres')])
        for d in resultats:
            p = d['parametres']
            params = '%s H0=%.4f Om=%.5f Ode=%.5f Ok=%.5f' % (d['modele'], p['H0'], p['Om'], p['Ode0'], p['Ok0'])
            for cle, unite in calcul.GRANDEURS:
                s = (d.get('sigma') or {}).get(cle)
                sh = (d.get('shoes') or {}).get(cle)
                w.writerow(['%.10g' % d['z'], cle, tr('cosmo_g_' + cle), '%.10g' % d[cle], unite_csv(unite),
                            '' if s is None else '%.6g' % s, '' if sh is None else '%.10g' % sh,
                            '%.10g' % (d[cle] * al) if cle in calcul.DISTANCES else '', params])


def ecrire_csv_courbes(chemin, c: dict):
    cols = [('z', 'z'), ('comoving', 'D_C_Mpc'), ('transverse', 'D_M_Mpc'), ('luminosity', 'D_L_Mpc'),
            ('angular_diameter', 'D_A_Mpc'), ('lookback', 'c_tL_Mpc'), ('lookback_gyr', 't_L_Gyr'),
            ('age_at_z', 'age_Gyr')]
    with open(chemin, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow([n for _, n in cols])
        for i in range(len(c['z'])):
            w.writerow(['%.8g' % c[k][i] for k, _ in cols])
