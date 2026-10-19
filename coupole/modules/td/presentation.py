"""Pas-à-pas, détail HTML et export CSV du calculateur « Parallaxe (TP du cours) » (sans Qt : interface et ligne
de commande)."""
from __future__ import annotations

import html
import math

from ...core.i18n import decimal as _dec
from ...core.i18n import tr
from . import parallaxe_tp as T


def _n(x, c=1) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return '—'
    return _dec(float(x), c)


# ============================================================================================== pas-à-pas
def etapes(e: T.Entrees, r: dict) -> list[tuple[str, str]]:
    """(titre, texte) des étapes du sujet, avec les nombres de l'utilisateur, puis le calcul exact."""
    g, sc, ss = r['geometrie'], r['sujet_corde'], r['sujet_surface']
    o1, o2 = e.o1, e.o2
    out = [(tr('td_e1'), tr('td_e1_t', h1=_n(o1.h, 3), h2=_n(o2.h, 3), az1=_n(o1.az, 2) if o1.az is not None else '—',
                            az2=_n(o2.az, 2) if o2.az is not None else '—'))]
    out.append((tr('td_e2'), tr('td_e2_entre' if sc['entre'] else 'td_e2_t', a=_n(sc['deux_alpha_deg'], 4),
                                r=_n(sc['deux_alpha_rad'], 6))))
    out.append((tr('td_e3'), tr('td_e3_t', s=_n(g['surface_km'], 3), c=_n(g['corde_km'], 3),
                                e=_n(g['ecart_corde_surface_km'] * 1000, 0), f=_n(g['fleche_km'] * 1000, 0),
                                fa=_n(g['fleche_approchee_km'] * 1000, 0), p1=_n(g['profondeur_deg'][0], 3),
                                p2=_n(g['profondeur_deg'][1], 3))))
    out.append((tr('td_e4'), tr('td_e4_t', ds=_n(ss['D_km'], 1), dc=_n(sc['D_km'], 1), a=_n(sc['deux_alpha_rad'], 6),
                                c=_n(g['corde_km'], 3))))
    x = r.get('exact')
    if x:
        out.append((tr('td_e5'), tr('td_e5_t', theta=_n(g['angle_centre_deg'], 4), d1=_n(x['distances_km'][0], 1),
                                    d2=_n(x['distances_km'][1], 1), dg=_n(x['distance_geo_km'], 1),
                                    alt=_n(x['altitude_km'], 2), p=_n(x['parallaxe_vraie_deg'], 4),
                                    mode=tr('td_mode_' + x['configuration']))))
    eph = r.get('ephemeride')
    if eph:
        if r['cible'] == 'lune':
            out.append((tr('td_e6'), tr('td_e6_lune', src=tr('td_src_' + eph['source']),
                                        dg=_n(eph['distance_geo_km'], 1), d1=_n(eph['lieux'][0]['distance_km'], 1),
                                        d2=_n(eph['lieux'][1]['distance_km'], 1), h1=_n(eph['lieux'][0]['h_deg'], 3),
                                        h2=_n(eph['lieux'][1]['h_deg'], 3),
                                        hr1=_n(eph['lieux'][0]['h_refraction_deg'], 3),
                                        hr2=_n(eph['lieux'][1]['h_refraction_deg'], 3))))
        else:
            out.append((tr('td_e6'), tr('td_e6_iss', alt=_n(eph['altitude_km'], 1), age=_n(eph['age_jours'], 1),
                                        d1=_n(eph['lieux'][0]['distance_km'], 1),
                                        d2=_n(eph['lieux'][1]['distance_km'], 1), h1=_n(eph['lieux'][0]['h_deg'], 3),
                                        h2=_n(eph['lieux'][1]['h_deg'], 3))))
    inc = r['incertitudes']
    out.append((tr('td_e7'), tr('td_e7_t', sh=_n(inc['sigma_h_effectif_deg'], 3), s=_n(inc['sujet_total_km'], 1),
                                x=_n(inc['exact_total_km'], 1) if inc['exact_total_km'] is not None else '—')))
    return out


def html_detail(e: T.Entrees, r: dict) -> str:
    h = []
    for a, v in r['alertes']:
        h.append('<p><b>⚠ %s</b></p>' % html.escape(tr(a, **v)))
    h.append('<ol>')
    for titre, texte in etapes(e, r):
        h.append('<li><b>%s</b><br>%s</li>' % (html.escape(titre), html.escape(texte).replace('\n', '<br>')))
    h.append('</ol>')
    return ''.join(h)


def texte_export(r: dict) -> str:
    """Détail des calculs pour la feuille « Calculs » du partage : CSV « grandeur ; valeur ; unité »."""
    import csv
    import io
    from ...core.i18n import decimal as dec
    s = io.StringIO()
    w = csv.writer(s, delimiter=';')
    w.writerow([tr('td_x_grandeur'), tr('td_x_valeur'), tr('td_x_unite')])
    o1, o2 = r['lieux']
    g, sc, ss = r['geometrie'], r['sujet_corde'], r['sujet_surface']
    lignes = [('td_x_lat1', o1.lat, '°', 6), ('td_x_lon1', o1.lon, '°', 6), ('td_x_h1', o1.h, '°', 4),
              ('td_x_lat2', o2.lat, '°', 6), ('td_x_lon2', o2.lon, '°', 6), ('td_x_h2', o2.h, '°', 4),
              ('td_x_2alpha', sc['deux_alpha_deg'], '°', 4), ('td_x_2alpha_rad', sc['deux_alpha_rad'], 'rad', 6),
              ('td_x_surface', g['surface_km'], 'km', 3), ('td_x_corde', g['corde_km'], 'km', 3),
              ('td_x_fleche', g['fleche_km'] * 1000, 'm', 0), ('td_x_D_surface', ss['D_km'], 'km', 1),
              ('td_x_D_corde', sc['D_km'], 'km', 1), ('td_x_theta', g['angle_centre_deg'], '°', 4)]
    x = r.get('exact')
    if x:
        lignes += [('td_x_d1', x['distances_km'][0], 'km', 1), ('td_x_d2', x['distances_km'][1], 'km', 1),
                   ('td_x_dgeo', x['distance_geo_km'], 'km', 1), ('td_x_alt', x['altitude_km'], 'km', 2)]
    for cle, v, u, c in lignes:
        w.writerow([tr(cle), dec(float(v), c) if v is not None else '', u])
    return s.getvalue()
