"""Partage d'exemple pour les essais du module « Partages du DU » : tout est FICTIF et fabriqué ici.

Lieux : centres de grandes villes (coordonnées publiques arrondies), observateurs « Observateur A/B/C ».  Le classeur
reproduit les défauts typiques d'un tableau rempli à la main (virgules décimales, degrés, date à l'américaine, nombre
de jours d'Excel, latitude et longitude échangées, heure locale, fichier introuvable), avec un style de date, des
textes partagés, une formule, une deuxième feuille et des lignes pré-numérotées : de quoi vérifier que l'ajout d'une
ligne ne touche à rien d'autre.  Les images FITS portent une solution astrométrique TAN exacte, construite à partir
de la position de la Lune (ou d'un point de trajectoire) calculée par Coupole.
"""
from __future__ import annotations

import datetime as D
import io
import math
import zipfile
from xml.sax.saxutils import escape

import numpy as np

UTC = D.timezone.utc
PARIS = (48.8566, 2.3522, 35.0)
MARSEILLE = (43.2965, 5.3698, 12.0)
STRASBOURG = (48.5734, 7.7521, 140.0)
LYON = (45.7640, 4.8357, 170.0)
PERTH = (-31.9523, 115.8613, 20.0)
T_LUNE = D.datetime(2025, 11, 3, 18, 38, 26, tzinfo=UTC)
T_ISS = D.datetime(2026, 10, 17, 4, 29, 11, 204000, tzinfo=UTC)

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NSR = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def _c(ref, v, style=None, partage=None, formule=None):
    s = ' s="%d"' % style if style is not None else ''
    if formule is not None:
        return '<c r="%s"%s><f>%s</f><v>%s</v></c>' % (ref, s, escape(formule), v)
    if partage is not None:
        return '<c r="%s"%s t="s"><v>%d</v></c>' % (ref, s, partage)
    if v is None:
        return '<c r="%s"%s/>' % (ref, s)
    return '<c r="%s"%s><v>%r</v></c>' % (ref, s, float(v))


def classeur(lignes: list, pre_numerotees: int = 30) -> bytes:
    """Classeur « localisations » : `lignes` = listes de valeurs (str, float, ou ('date', jours d'Excel)).

    Colonnes : N° | Cible | Nom du fichier | Auteur | Date + heure (TU) | Longitude | Latitude | Altitude (m) |
    Azimut | Hauteur.  Ligne 1 : titre ; ligne 2 : en-têtes ; lignes suivantes : mesures, puis lignes numérotées
    vides jusqu'à `pre_numerotees`.  Deuxième feuille « Calculs » avec une formule."""
    textes: list[str] = []

    def sst(t):
        if t not in textes:
            textes.append(t)
        return textes.index(t)
    entetes = ['N°', 'Cible', 'Nom du fichier', 'Auteur', 'Date + heure (TU)', 'Longitude', 'Latitude',
               'Altitude (m)', 'Azimut', 'Hauteur']
    rows = ['<row r="1"><c r="A1" t="s" s="2"><v>%d</v></c></row>' % sst('Défi parallaxe — localisations')]
    rows.append('<row r="2" spans="1:10">%s</row>' % ''.join(
        _c('%s2' % chr(65 + k), None, 2, sst(t)) for k, t in enumerate(entetes)))
    r = 3
    for vals in lignes:
        cel = [_c('A%d' % r, r - 2)]
        for k, v in enumerate(vals, 1):
            ref = '%s%d' % (chr(65 + k), r)
            if isinstance(v, tuple) and v[0] == 'date':
                cel.append(_c(ref, v[1], 1))
            elif isinstance(v, str):
                cel.append(_c(ref, None, None, sst(v)))
            elif v is not None:
                cel.append(_c(ref, v))
        rows.append('<row r="%d">%s</row>' % (r, ''.join(cel)))
        r += 1
    while r <= pre_numerotees:                               # lignes numérotées d'avance, vides, avec un style
        rows.append('<row r="%d">%s%s</row>' % (r, _c('A%d' % r, r - 2), ''.join(
            _c('%s%d' % (chr(65 + k), r), None, 3) for k in range(1, 10))))
        r += 1
    feuille1 = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="%s" xmlns:r="%s">'
                '<dimension ref="A1:J%d"/><sheetData>%s</sheetData><mergeCells count="1"><mergeCell ref="A1:J1"/>'
                '</mergeCells></worksheet>' % (NS, NSR, r - 1, ''.join(rows)))
    feuille2 = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="%s"><sheetData>'
                '<row r="1"><c r="A1" t="s"><v>%d</v></c><c r="B1"><f>2*PI()*6371</f><v>40030.17</v></c></row>'
                '</sheetData></worksheet>' % (NS, sst('Circonférence (km)')))
    sst_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><sst xmlns="%s" count="%d" uniqueCount="%d">%s'
               '</sst>' % (NS, len(textes), len(textes), ''.join('<si><t>%s</t></si>' % escape(t) for t in textes)))
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="%s"><numFmts count="1">'
              '<numFmt numFmtId="164" formatCode="dd/mm/yyyy\\ hh:mm:ss"/></numFmts><fonts count="2"><font/>'
              '<font><b/></font></fonts><fills count="1"><fill/></fills><borders count="1"><border/></borders>'
              '<cellXfs count="4"><xf numFmtId="0"/><xf numFmtId="164" applyNumberFormat="1"/><xf numFmtId="0" '
              'fontId="1"/><xf numFmtId="2"/></cellXfs></styleSheet>' % NS)
    fichiers = {
        '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/'
        'package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
        'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/></Types>',
        '_rels/.rels': '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/'
        'package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/'
        '2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        'xl/workbook.xml': '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="%s" xmlns:r="%s"><sheets>'
        '<sheet name="Localisations" sheetId="1" r:id="rId1"/><sheet name="Calculs" sheetId="2" r:id="rId2"/>'
        '</sheets></workbook>' % (NS, NSR),
        'xl/_rels/workbook.xml.rels': '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
        'openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
        'org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="/xl/worksheets/'
        'sheet2.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>',
        'xl/worksheets/sheet1.xml': feuille1, 'xl/worksheets/sheet2.xml': feuille2,
        'xl/sharedStrings.xml': sst_xml, 'xl/styles.xml': styles,
        'xl/vbaProject.bin': bytes(range(256)),            # contenu opaque : doit être recopié à l'octet près
    }
    sortie = io.BytesIO()
    with zipfile.ZipFile(sortie, 'w', zipfile.ZIP_DEFLATED) as z:
        for nom, contenu in fichiers.items():
            z.writestr(nom, contenu)
    return sortie.getvalue()


def jours_excel(dt: D.datetime) -> float:
    return (dt.astimezone(UTC).replace(tzinfo=None) - D.datetime(1899, 12, 30)).total_seconds() / 86400.0


def altaz_lune(lieu, t):
    from coupole.modules.partages import astro
    h, az, _, _ = astro.altaz_lune(lieu[0], lieu[1], lieu[2], astro.Instant(t))
    return h, az


def lignes_mesures() -> list:
    """Lignes du tableau d'exemple (sans la colonne N°) et ce que chacune doit déclencher."""
    hA, azA = altaz_lune(PARIS, T_LUNE)
    hB, azB = altaz_lune(MARSEILLE, T_LUNE)
    hC, azC = altaz_lune(STRASBOURG, T_LUNE - D.timedelta(hours=1))
    return [
        # Lune, A : propre, mais virgules et degrés (normalisés), heure notée en TU
        ['Lune', '2025-11-03-18-38-26-A.fits', 'Observateur A', '03/11/2025 18:38:26 TU', '2,3522°', '48,8566°',
         35, round(azA, 2), round(hA, 2)],
        # Lune, B : date en nombre de jours d'Excel ; latitude et longitude échangées (la Lune le prouve)
        ['Lune', '2025-11-03-18-38-26-B.fits', 'Observateur B', ('date', jours_excel(T_LUNE)), MARSEILLE[0],
         MARSEILLE[1], 12, round(azB, 2), round(hB, 2)],
        # Lune, C : heure LOCALE notée (TU + 1 h) : la Lune notée colle avec l'heure moins 1 h
        ['Lune', '2025-11-03-18-38-26-C.jpg', 'Observateur C', '03/11/2025 18:38:26', STRASBOURG[1],
         STRASBOURG[0], 140, round(azC, 2), round(hC, 2)],
        # ISS, date à l'américaine (mois/jour), fichier absent du partage
        ['ISS', 'ISS_inexistant.fits', 'Observateur D', '10/25/2025 20:45:52 TU', '4°50′09″ E', '45°45′50″ N',
         '170', None, None],
        # site austral, latitude et longitude échangées de façon certaine (|latitude| > 90°)
        ['Lune', '', 'Observateur E', '2025-11-03 18:38:26 UTC', PERTH[0], PERTH[1], 20, None, None],
    ]


# ------------------------------------------------------------------ images FITS avec WCS exacte
def fits_tan(direction_radec, lieu, t_debut, pose_s, image, echelle_arcsec=2.0, objet='Moon', observateur='',
             rotation_deg=0.0, centre_px=None) -> bytes:
    """FITS 2-D dont la WCS TAN place `direction_radec` au pixel `centre_px` (défaut : centre de l'image)."""
    from astropy.io import fits
    h, w = image.shape
    cx, cy = centre_px if centre_px is not None else ((w - 1) / 2, (h - 1) / 2)
    e = echelle_arcsec / 3600.0
    r = math.radians(rotation_deg)
    hdr = fits.Header()
    hdr['CTYPE1'], hdr['CTYPE2'] = 'RA---TAN', 'DEC--TAN'
    hdr['CRVAL1'], hdr['CRVAL2'] = float(direction_radec[0]), float(direction_radec[1])
    hdr['CRPIX1'], hdr['CRPIX2'] = cx + 1.0, cy + 1.0
    hdr['CD1_1'], hdr['CD1_2'] = -e * math.cos(r), e * math.sin(r)
    hdr['CD2_1'], hdr['CD2_2'] = e * math.sin(r), e * math.cos(r)
    hdr['RADESYS'] = 'ICRS'
    hdr['DATE-OBS'] = t_debut.astimezone(UTC).replace(tzinfo=None).isoformat(timespec='milliseconds')
    hdr['EXPTIME'] = float(pose_s)
    hdr['SITELAT'], hdr['SITELONG'], hdr['SITEELEV'] = lieu[0], lieu[1], lieu[2]
    hdr['OBJECT'] = objet
    if observateur:
        hdr['OBSERVER'] = observateur
    s = io.BytesIO()
    fits.PrimaryHDU(np.asarray(image, np.float32), hdr).writeto(s)
    return s.getvalue()


def disque(h, w, cx, cy, r, terminateur=True) -> np.ndarray:
    """Lune gibbeuse : disque de rayon r centré en (cx, cy), éclairé à ~75 % (terminateur elliptique), bruit faible."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dans = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    if terminateur:
        b = 0.5 * r
        ombre = ((xx - cx) / b) ** 2 + ((yy - cy) / r) ** 2 <= 1.0
        dans &= ~(ombre & (xx < cx)) & ~(xx < cx - b)
    rng = np.random.default_rng(3)
    return (100 + 2000 * dans + rng.normal(0, 5, (h, w))).astype(np.float32)


def fits_lune(lieu, t, nom_obs, decalage_px=(0.0, 0.0)) -> tuple[bytes, tuple]:
    """FITS d'une Lune dont le centre (au pixel connu) est la direction astrométrique prédite pour ce lieu."""
    from coupole.modules.partages import astro
    ti = astro.Instant(t + D.timedelta(seconds=0.5))
    O = astro.observateur_gcrs(lieu[0], lieu[1], lieu[2], ti)
    v, _ = astro.lune_astrometrique(ti, O)
    ra, dec = astro.radec(v)
    h, w = 480, 640
    r_px = math.degrees(math.asin(astro.R_LUNE_KM / np.linalg.norm(v))) * 3600 / 8.0
    cx, cy = 300.0 + decalage_px[0], 250.0 + decalage_px[1]
    img = disque(h, w, cx, cy, r_px)
    return fits_tan((ra, dec), lieu, t, 1.0, img, 8.0, 'Moon', nom_obs, 12.0, (cx, cy)), (ra, dec)
