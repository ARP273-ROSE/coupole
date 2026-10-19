"""Rapport d'une mesure de parallaxe : HTML autonome (schéma intégré) et PDF (Qt), dans la langue de l'interface.

Le schéma (QPainter sur une QImage, donc sans écran) montre la Terre, les deux observateurs, la base, les deux
visées et l'objet, avec la parallaxe ; il n'est pas à l'échelle (la Lune serait à 60 rayons terrestres), ce qu'il dit.
"""
from __future__ import annotations

import base64
import datetime as D
import html
import math

from .....core.i18n import decimal, tr

e = html.escape


def _n(x, c=1) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return '—'
    return decimal(float(x), c)


_APP = []


def _application_qt():
    """QPainter et les polices exigent une QGuiApplication : la ligne de commande n'en a pas, on en crée une
    (hors écran si aucun affichage n'est disponible)."""
    import os
    import sys
    from PyQt6.QtGui import QGuiApplication
    if QGuiApplication.instance() is None:
        if sys.platform.startswith('linux') and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        _APP.append(QGuiApplication(['coupole']))


def schema_png(res: dict, largeur: int = 900, hauteur: int = 520) -> bytes:
    _application_qt()
    from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
    from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen
    img = QImage(largeur, hauteur, QImage.Format.Format_ARGB32)
    img.fill(QColor('#ffffff'))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    f = QFont()
    f.setPointSizeF(11)
    p.setFont(f)
    cx, cy, R = largeur / 2, hauteur + 1.9 * hauteur, 2.25 * hauteur
    p.setPen(QPen(QColor('#3d6fb4'), 2))
    p.setBrush(QColor('#dbe8f7'))
    p.drawEllipse(QPointF(cx, cy), R, R)
    ang = math.radians(9)
    O1 = QPointF(cx - R * math.sin(ang), cy - R * math.cos(ang))
    O2 = QPointF(cx + R * math.sin(ang), cy - R * math.cos(ang))
    M = QPointF(cx + 30, 70)
    p.setPen(QPen(QColor('#c0392b'), 2))
    p.drawLine(O1, M)
    p.drawLine(O2, M)
    p.setPen(QPen(QColor('#2c3e50'), 2, Qt.PenStyle.DashLine))
    p.drawLine(O1, O2)
    p.setBrush(QColor('#555555') if res.get('genre') == 'lune' else QColor('#f1c40f'))
    p.setPen(QPen(QColor('#222222'), 1))
    p.drawEllipse(M, 14, 14)
    for q in (O1, O2):
        p.setBrush(QColor('#c0392b'))
        p.drawEllipse(q, 6, 6)
    p.setPen(QColor('#111111'))
    obs = res.get('observateurs', [{}, {}])
    p.drawText(QRectF(O1.x() - 190, O1.y() + 8, 200, 40), int(Qt.AlignmentFlag.AlignRight),
               'A : ' + (obs[0].get('nom') or 'A'))
    p.drawText(QRectF(O2.x() - 10, O2.y() + 8, 220, 40), int(Qt.AlignmentFlag.AlignLeft),
               'B : ' + (obs[1].get('nom') or 'B'))
    milieu = QPointF((O1.x() + O2.x()) / 2, (O1.y() + O2.y()) / 2)
    p.drawText(QRectF(milieu.x() - 200, milieu.y() + 10, 400, 24), int(Qt.AlignmentFlag.AlignCenter),
               tr('pc_r_schema_base', b=_n(res.get('base_km'), 1)))
    if res.get('genre') == 'lune':
        txt = tr('pc_r_schema_lune', d=_n(res.get('distance_geo_km'), 0), p=_n(res.get('parallaxe_arcsec'), 1))
    else:
        txt = tr('pc_r_schema_iss', h=_n(res.get('altitude_km'), 1), p=_n(res.get('parallaxe_deg'), 2))
    p.drawText(QRectF(M.x() + 24, M.y() - 14, largeur - M.x() - 30, 60), int(Qt.AlignmentFlag.AlignLeft), txt)
    f.setPointSizeF(9)
    p.setFont(f)
    p.setPen(QColor('#666666'))
    p.drawText(QRectF(10, hauteur - 24, largeur - 20, 20), int(Qt.AlignmentFlag.AlignLeft), tr('pc_r_schema_echelle'))
    p.end()
    tampon = QByteArray()
    b = QBuffer(tampon)
    b.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(b, 'PNG')
    return bytes(tampon)


def lignes_resultats(res: dict) -> list[tuple[str, str]]:
    out = []
    if res.get('genre') == 'lune':
        out += [(tr('pc_r_instant'), res['instant'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-4] + ' UTC'),
                (tr('pc_r_dt'), _n(res['dt_s'], 2) + ' s'),
                (tr('pc_r_base'), _n(res['base_km'], 1) + ' km'),
                (tr('pc_r_base_perp'), _n(res['base_perp_km'], 1) + ' km'),
                (tr('pc_r_parallaxe'), _n(res['parallaxe_arcsec'], 1) + '″'),
                (tr('pc_r_distance_geo'), _n(res['distance_geo_km'], 0) + ' km ± ' + _n(res['sigma_km'], 0) + ' km'),
                (tr('pc_r_distance_topo'), ' ; '.join(_n(x, 0) + ' km' for x in res['distance_topo_km'])),
                (tr('pc_r_distance_simple'), _n(res['distance_simple_km'], 0) + ' km'),
                (tr('pc_r_ecart_droites'), _n(res['ecart_droites_km'], 1) + ' km'),
                (tr('pc_r_eph', src=tr('pc_eph_' + res['ephemeride'])), _n(res['distance_geo_eph_km'], 0) + ' km'),
                (tr('pc_r_ecart'), _n(res['ecart_km'], 0) + ' km (' + _n(100 * res['ecart_rel'], 2) + ' %)'),
                (tr('pc_r_parallaxe_eph'), _n(res['parallaxe_eph_arcsec'], 1) + '″'),
                (tr('pc_r_ecart_dir'), ' ; '.join(_n(x, 1) + '″' for x in res['ecart_direction_eph_arcsec'])),
                (tr('pc_r_hauteurs'), ' ; '.join('%s° / %s°' % (_n(h, 1), _n(a, 1)) for h, a in res['hauteurs'])),
                (tr('pc_r_refraction'), ' ; '.join(_n(x, 0) + '″' for x in res['refraction_arcsec'])),
                (tr('pc_r_decalage_temps'), ' ; '.join(_n(x, 1) + '″' for x in res['decalage_temps_arcsec']))]
        if res.get('methode_sujet'):
            m = res['methode_sujet']
            out.append((tr('pc_r_sujet'), _n(m['distance_km'], 0) + ' km (Δφ = ' + _n(m['dphi_arcsec'], 1) + '″)'))
    else:
        out += [(tr('pc_r_instant'), res['instant'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-4] + ' UTC'),
                (tr('pc_r_base'), _n(res['base_km'], 1) + ' km'),
                (tr('pc_r_parallaxe'), _n(res['parallaxe_deg'], 2) + '°'),
                (tr('pc_r_angles'), ' ; '.join(_n(x, 2) + '°' for x in res['angles_deg'])),
                (tr('pc_r_distances'), ' ; '.join(_n(x, 1) + ' km' for x in res['distances_km'])),
                (tr('pc_r_ecart_droites'), _n(1000 * res['ecart_droites_km'], 0) + ' m'),
                (tr('pc_r_altitude'), _n(res['altitude_km'], 1) + ' km ± ' + _n(res['sigma_km'], 1) + ' km'),
                (tr('pc_r_sous_point'), '%s° N ; %s° E' % (_n(res['sous_point'][0], 2), _n(res['sous_point'][1], 2))),
                (tr('pc_r_formules'), tr('pc_r_formules_v', s=_n(res['distance_sym_km'], 1),
                                         p=_n(res['distance_petits_angles_km'], 1)))]
        if res.get('plans'):
            out.append((tr('pc_r_plans'), _n(res['plans']['altitude_km'], 1) + ' km (' +
                        _n(res['plans']['angle_plans_deg'], 1) + '°)'))
        h = res.get('horloge') or {}
        if h.get('decalage_s') is not None:
            out.append((tr('pc_r_horloge'), tr('pc_r_horloge_v', dt=_n(h['decalage_s'], 2),
                                               h=_n(h['altitude_km'], 1), e=_n(1000 * h['ecart_km'], 0))))
        t = res.get('tle') or {}
        if t.get('altitude_km') is not None:
            out.append((tr('pc_r_tle'), _n(t['altitude_km'], 1) + ' km ; ' +
                        tr('pc_r_tle_ecart', e=_n(t.get('ecart_km'), 1), a=_n(t.get('age_j'), 1))))
        elif t.get('erreur'):
            out.append((tr('pc_r_tle'), tr(t['erreur'])))
    return out


def html_rapport(res: dict, titre: str = '', notes: list | None = None, png: bytes | None = None,
                 integrer_image: bool = True) -> str:
    """Rapport HTML autonome.  `notes` : textes déjà traduits (corrections appliquées, anomalies)."""
    png = png if png is not None else schema_png(res)
    src = 'data:image/png;base64,' + base64.b64encode(png).decode('ascii') if integrer_image else 'schema.png'
    h = ['<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8"><title>%s</title>' % (
        tr('pc_r_langue'), e(titre or tr('pc_r_titre_' + res.get('genre', 'lune')))),
        '<style>body{font-family:sans-serif;max-width:60em;margin:2em auto;padding:0 1em;color:#222;background:#fff}'
        'table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:.3em .5em;text-align:left;'
        'vertical-align:top}th{background:#eef3fa}h1{font-size:1.5em}img{max-width:100%}.note{color:#555}</style>'
        '</head><body>',
        '<h1>%s</h1>' % e(titre or tr('pc_r_titre_' + res.get('genre', 'lune'))),
        '<p class="note">%s</p>' % e(tr('pc_r_genere', date=D.datetime.now(D.timezone.utc).strftime(
            '%Y-%m-%d %H:%M UTC'))),
        '<p><img src="%s" alt="%s"></p>' % (src, e(tr('pc_r_schema'))),
        '<h2>%s</h2><table>' % e(tr('pc_r_observateurs'))]
    h.append('<tr><th></th><th>%s</th><th>%s</th><th>%s</th></tr>' % (e(tr('pc_r_lat')), e(tr('pc_r_lon')),
                                                                       e(tr('pc_r_alt'))))
    for k, o in enumerate(res.get('observateurs', [])):
        h.append('<tr><td>%s : %s</td><td>%s°</td><td>%s°</td><td>%s m</td></tr>' % (
            'AB'[k], e(o.get('nom') or ''), _n(o['lat'], 5), _n(o['lon'], 5), _n(o.get('alt_m'), 0)))
    h.append('</table><h2>%s</h2><table>' % e(tr('pc_r_resultats')))
    for a, b in lignes_resultats(res):
        h.append('<tr><th>%s</th><td>%s</td></tr>' % (e(a), e(b)))
    h.append('</table>')
    if res.get('budget'):
        h.append('<h2>%s</h2><table><tr><th>%s</th><th>%s</th><th>%s</th></tr>' % (
            e(tr('pc_r_budget')), e(tr('pc_r_source')), e(tr('pc_r_observateur')), e(tr('pc_r_contribution'))))
        unite = 'km'
        for cle, v, qui in res['budget']:
            h.append('<tr><td>%s</td><td>%s</td><td>%s %s</td></tr>' % (e(tr(cle)), e(qui), _n(v, 2), unite))
        h.append('<tr><th colspan="2">%s</th><th>%s km</th></tr></table>' % (e(tr('pc_r_total')),
                                                                          _n(res.get('sigma_km'), 2)))
    h.append('<h2>%s</h2><p>%s</p>' % (e(tr('pc_r_methode')), e(tr('pc_r_methode_' + res.get('genre', 'lune')))))
    if notes:
        h.append('<h2>%s</h2><ul>%s</ul>' % (e(tr('pc_r_notes')), ''.join('<li>%s</li>' % e(n) for n in notes)))
    h.append('<p class="note">%s</p></body></html>' % e(tr('pc_r_pied')))
    return '\n'.join(h)


def ecrire_html(chemin: str, res: dict, titre: str = '', notes=None) -> str:
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write(html_rapport(res, titre, notes))
    return chemin


def ecrire_pdf(chemin: str, res: dict, titre: str = '', notes=None) -> str:
    """PDF par Qt (QTextDocument → QPdfWriter) ; à appeler dans le fil graphique (ou sans interface : une
    QGuiApplication hors écran est créée au besoin)."""
    from PyQt6.QtCore import QMarginsF, QUrl
    from PyQt6.QtGui import QGuiApplication, QImage, QPageLayout, QPageSize, QPdfWriter, QTextDocument
    if QGuiApplication.instance() is None:
        import os
        import sys
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        ecrire_pdf._app = QGuiApplication(sys.argv[:1])       # garde l'application en vie
    png = schema_png(res)
    doc = QTextDocument()
    img = QImage()
    img.loadFromData(png)
    doc.addResource(QTextDocument.ResourceType.ImageResource.value, QUrl('schema.png'), img)
    doc.setHtml(html_rapport(res, titre, notes, png, integrer_image=False).replace(
        '<img src="schema.png"', '<img width="620" src="schema.png"'))
    w = QPdfWriter(chemin)
    w.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    w.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Unit.Millimeter)
    w.setResolution(150)
    doc.setPageSize(w.pageLayout().paintRectPixels(w.resolution()).size().toSizeF())
    doc.print(w)
    return chemin
