"""Lire un classeur .xlsx (ou un .csv) sans dépendance lourde, et y AJOUTER une ligne sans rien toucher d'autre.

Un .xlsx est une archive zip de fichiers XML (Office Open XML, ECMA-376) : ``xl/workbook.xml`` (feuilles),
``xl/sharedStrings.xml`` (textes partagés), ``xl/styles.xml`` (formats : une cellule de date est un NOMBRE de jours
depuis le 30/12/1899 avec un format de date), ``xl/worksheets/sheetN.xml`` (cellules).  zipfile + ElementTree
suffisent ; openpyxl n'est pas nécessaire.

Ajout d'une ligne (dépôt de sa mesure) : seule la feuille visée est réécrite, et seulement par insertion d'un
élément ``<row>`` à la fin de ``<sheetData>`` (cellules en texte « inlineStr » ou en nombre) et mise à jour de la
plage ``<dimension>`` ; tous les autres fichiers de l'archive sont recopiés OCTET POUR OCTET (styles, formules,
macros, autres feuilles).  Le classeur d'origine n'est jamais modifié en place : on fabrique un nouveau contenu,
déposé ensuite sous condition d'ETag (voir ``depot.py``).
"""
from __future__ import annotations

import csv
import datetime as D
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

NS_MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NS_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
N = {'m': NS_MAIN, 'r': NS_REL}
TAILLE_MAX_ENTREE = 64_000_000          # octets décompressés par fichier interne (bombe de décompression)
FORMATS_DATE = set(range(14, 23)) | {45, 46, 47}
EPOQUE = D.datetime(1899, 12, 30)


class ClasseurIllisible(ValueError):
    pass


@dataclass
class Cellule:
    ref: str
    valeur: object                 # str, float, bool, ou None
    formule: str = ''
    date: bool = False             # nombre affiché comme une date (format de cellule)

    def texte(self) -> str:
        if self.valeur is None:
            return ''
        if isinstance(self.valeur, float):
            return ('%.15g' % self.valeur)
        return str(self.valeur)

    def comme_date(self) -> D.datetime | None:
        if self.date and isinstance(self.valeur, float):
            return date_excel(self.valeur)
        return None


@dataclass
class Feuille:
    nom: str
    chemin: str                    # chemin interne (xl/worksheets/sheet1.xml) ; '' pour un CSV
    cellules: dict = field(default_factory=dict)       # (ligne, colonne) 1-based -> Cellule

    @property
    def nb_lignes(self) -> int:
        return max((l for l, _ in self.cellules), default=0)

    @property
    def nb_colonnes(self) -> int:
        return max((c for _, c in self.cellules), default=0)

    def ligne(self, l: int) -> list:
        return [self.cellules.get((l, c)) for c in range(1, self.nb_colonnes + 1)]

    def lignes(self):
        for l in range(1, self.nb_lignes + 1):
            yield l, self.ligne(l)


@dataclass
class Classeur:
    feuilles: list
    format: str = 'xlsx'

    def feuille(self, nom_ou_index=0) -> Feuille:
        if isinstance(nom_ou_index, int):
            return self.feuilles[nom_ou_index]
        return next(f for f in self.feuilles if f.nom == nom_ou_index)


def date_excel(n: float) -> D.datetime | None:
    try:
        return EPOQUE + D.timedelta(days=float(n))
    except (OverflowError, ValueError):
        return None


def vers_excel(dt: D.datetime) -> float:
    if dt.tzinfo is not None:
        dt = dt.astimezone(D.timezone.utc).replace(tzinfo=None)
    return (dt - EPOQUE).total_seconds() / 86400.0


RE_REF = re.compile(r'^([A-Z]+)(\d+)$')


def colonne_num(lettres: str) -> int:
    n = 0
    for c in lettres:
        n = n * 26 + (ord(c) - 64)
    return n


def colonne_lettres(n: int) -> str:
    s = ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _lire_zip(z: zipfile.ZipFile, nom: str) -> bytes:
    info = z.getinfo(nom)
    if info.file_size > TAILLE_MAX_ENTREE:
        raise ClasseurIllisible('entry too large: %s' % nom)
    return z.read(nom)


def _texte_si(si) -> str:
    """Texte d'un <si> ou <is> : texte simple, ou « rich text » (suite de <r><t>) ; indications phonétiques ignorées."""
    t = si.find('m:t', N)
    if t is not None:
        return t.text or ''
    return ''.join(r.findtext('m:t', '', N) or '' for r in si.findall('m:r', N))


def _formats_dates(z: zipfile.ZipFile) -> list[bool]:
    """Pour chaque style de cellule (index de cellXfs) : affiche-t-il une date ?"""
    try:
        racine = ET.fromstring(_lire_zip(z, 'xl/styles.xml'))
    except KeyError:
        return []
    perso = {}
    for nf in racine.findall('m:numFmts/m:numFmt', N):
        code = re.sub(r'"[^"]*"|\[[^\]]*\]|\\.', '', nf.get('formatCode', '')).lower()
        perso[int(nf.get('numFmtId', '0'))] = bool(re.search(r'[dmyhs]', code)) and 'general' not in code
    out = []
    for xf in racine.findall('m:cellXfs/m:xf', N):
        i = int(xf.get('numFmtId', '0'))
        out.append(i in FORMATS_DATE or perso.get(i, False))
    return out


def lire_xlsx(octets: bytes) -> Classeur:
    try:
        z = zipfile.ZipFile(io.BytesIO(octets))
    except zipfile.BadZipFile as e:
        raise ClasseurIllisible(str(e)) from None
    with z:
        try:
            wb = ET.fromstring(_lire_zip(z, 'xl/workbook.xml'))
            rels = ET.fromstring(_lire_zip(z, 'xl/_rels/workbook.xml.rels'))
        except (KeyError, ET.ParseError) as e:
            raise ClasseurIllisible(str(e)) from None
        cibles = {r.get('Id'): r.get('Target') for r in rels}
        partages = []
        if 'xl/sharedStrings.xml' in z.namelist():
            sst = ET.fromstring(_lire_zip(z, 'xl/sharedStrings.xml'))
            partages = [_texte_si(si) for si in sst.findall('m:si', N)]
        dates = _formats_dates(z)
        feuilles = []
        for s in wb.findall('m:sheets/m:sheet', N):
            cible = cibles.get(s.get('{%s}id' % NS_REL), '')
            chemin = cible.lstrip('/') if cible.startswith('/') else 'xl/' + cible
            chemin = re.sub(r'[^/]+/\.\./', '', chemin)
            if chemin not in z.namelist():
                continue
            feuilles.append(_lire_feuille(s.get('name', ''), chemin, _lire_zip(z, chemin), partages, dates))
    return Classeur(feuilles)


def _lire_feuille(nom, chemin, octets, partages, dates) -> Feuille:
    f = Feuille(nom, chemin)
    racine = ET.fromstring(octets)
    for row in racine.iterfind('m:sheetData/m:row', N):
        ligne_r = int(row.get('r', '0') or 0)
        col_suiv = 1
        for c in row.findall('m:c', N):
            ref = c.get('r') or '%s%d' % (colonne_lettres(col_suiv), ligne_r)
            m = RE_REF.match(ref)
            if not m:
                continue
            col, lig = colonne_num(m.group(1)), int(m.group(2))
            col_suiv = col + 1
            t = c.get('t', 'n')
            v = c.findtext('m:v', None, N)
            formule = c.findtext('m:f', '', N) or ''
            style = int(c.get('s', '0') or 0)
            valeur: object = None
            est_date = False
            if t == 's' and v is not None:
                try:
                    valeur = partages[int(v)]
                except (ValueError, IndexError):
                    valeur = ''
            elif t == 'inlineStr':
                is_ = c.find('m:is', N)
                valeur = _texte_si(is_) if is_ is not None else ''
            elif t in ('str', 'e'):
                valeur = v or ''
            elif t == 'b':
                valeur = v == '1'
            elif v is not None and v != '':
                try:
                    valeur = float(v)
                    est_date = style < len(dates) and dates[style]
                except ValueError:
                    valeur = v
            if valeur is None and not formule:
                continue
            f.cellules[(lig, col)] = Cellule(ref, valeur, formule, est_date)
    return f


def lire_csv(octets: bytes) -> Classeur:
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            texte = octets.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialecte = csv.Sniffer().sniff(texte[:4096], delimiters=';,\t')
    except csv.Error:
        dialecte = csv.excel
    f = Feuille('csv', '')
    for l, ligne in enumerate(csv.reader(io.StringIO(texte), dialecte), 1):
        for c, v in enumerate(ligne, 1):
            if v != '':
                f.cellules[(l, c)] = Cellule('%s%d' % (colonne_lettres(c), l), v)
    return Classeur([f], 'csv')


def lire(octets: bytes, nom: str = '') -> Classeur:
    if nom.lower().endswith(('.csv', '.tsv')) or not octets[:2] == b'PK':
        return lire_csv(octets)
    return lire_xlsx(octets)


# ============================================================================================== ajout d'une ligne
def _cellule_xml(ref: str, v) -> str:
    if v is None or v == '':
        return ''
    if isinstance(v, bool):
        return '<c r="%s" t="b"><v>%d</v></c>' % (ref, int(v))
    if isinstance(v, (int, float)):
        return '<c r="%s"><v>%s</v></c>' % (ref, repr(float(v)) if isinstance(v, float) else str(v))
    t = escape(str(v))
    return '<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, t)


def ligne_libre(fe: Feuille, colonne_numero: int | None = 1) -> int:
    """Première ligne libre : celle qui suit la dernière ligne où une colonne AUTRE que la numérotation porte une
    valeur (un tableau peut être pré-numéroté sur des centaines de lignes vides)."""
    derniere = 0
    for (l, c), cel in fe.cellules.items():
        if c != colonne_numero and cel.valeur not in (None, ''):
            derniere = max(derniere, l)
    return derniere + 1


def _attribut(balise: str, nom: str) -> str:
    m = re.search(r'\b%s="([^"]*)"' % nom, balise)
    return m.group(1) if m else ''


def ajouter_ligne(octets: bytes, valeurs: list, feuille=0, colonne_numero: int | None = 1) -> tuple[bytes, int]:
    """Nouveau contenu du classeur avec `valeurs` dans la première ligne libre de la feuille ; rend (octets, ligne).

    `valeurs[k]` va dans la colonne k+1 ; None laisse la cellule telle qu'elle est (ex. un numéro déjà inscrit).
    Rien d'autre ne change : les autres entrées de l'archive sont recopiées telles quelles, la ligne visée garde son
    style (attribut « s » de chaque cellule) ; seules ses cellules vides reçoivent une valeur.  Une cellule déjà
    remplie n'est JAMAIS remplacée : si la ligne visée n'est plus libre, ClasseurIllisible."""
    classeur = lire_xlsx(octets)
    fe = classeur.feuille(feuille)
    src = zipfile.ZipFile(io.BytesIO(octets))
    texte = _lire_zip(src, fe.chemin).decode('utf-8')
    n = ligne_libre(fe, colonne_numero)
    pref = re.search(r'<(\w+:)?sheetData\b', texte)
    p = (pref.group(1) or '') if pref else ''
    ep = re.escape(p)
    motif_ligne = re.compile(r'<%srow\b[^>]*?\br="(\d+)"[^>]*?(?:/>|>.*?</%srow>)' % (ep, ep), re.S)
    motif_cel = re.compile(r'<%sc\b[^>]*?(?:/>|>.*?</%sc>)' % (ep, ep), re.S)

    def cel(ref, v, style):
        x = _cellule_xml(ref, v)
        if style:
            x = x.replace('<c r="%s"' % ref, '<c r="%s" s="%s"' % (ref, style), 1)
        if p:
            for t in ('c', 'v', 'is', 't'):
                x = x.replace('<%s ' % t, '<%s%s ' % (p, t)).replace('<%s>' % t, '<%s%s>' % (p, t)).replace(
                    '</%s>' % t, '</%s%s>' % (p, t))
        return x
    lignes = list(motif_ligne.finditer(texte))
    existante = next((m for m in lignes if int(m.group(1)) == n), None)
    cellules: dict[int, str] = {}
    ouverture = '<%srow r="%d"' % (p, n)
    if existante is not None:
        elt = existante.group(0)
        tete = re.match(r'<%srow\b[^>]*?(?=/?>)' % ep, elt).group(0)
        ouverture = re.sub(r'\sspans="[^"]*"', '', tete)
        for mc in motif_cel.finditer(elt):
            ref = _attribut(mc.group(0), 'r')
            mr = RE_REF.match(ref)
            if mr:
                cellules[colonne_num(mr.group(1))] = mc.group(0)
    for k, v in enumerate(valeurs, 1):
        if v is None or v == '':
            continue
        ancienne = cellules.get(k, '')
        if ancienne and re.search(r'<%s(?:v|is)\b' % ep, ancienne):
            raise ClasseurIllisible('row %d column %d is not empty' % (n, k))
        style = _attribut(ancienne.split('>', 1)[0], 's') if ancienne else ''
        cellules[k] = cel('%s%d' % (colonne_lettres(k), n), v, style)
    ligne = '%s>%s</%srow>' % (ouverture, ''.join(cellules[k] for k in sorted(cellules)), p)
    if existante is not None:
        texte = texte[:existante.start()] + ligne + texte[existante.end():]
    else:
        suivante = next((m for m in lignes if int(m.group(1)) > n), None)
        if suivante is not None:
            texte = texte[:suivante.start()] + ligne + texte[suivante.start():]
        elif re.search(r'<%ssheetData\s*/>' % ep, texte):
            texte = re.sub(r'<%ssheetData\s*/>' % ep, '<%ssheetData>%s</%ssheetData>' % (p, ligne, p), texte, 1)
        elif '</%ssheetData>' % p in texte:
            k = texte.rindex('</%ssheetData>' % p)
            texte = texte[:k] + ligne + texte[k:]
        else:
            raise ClasseurIllisible('sheetData not found')
    derniere_col = max(len(valeurs), fe.nb_colonnes, 1)

    def dim(m):
        debut, _, fin = m.group(2).partition(':')
        mf = RE_REF.match(fin or debut)
        col = max(colonne_num(mf.group(1)) if mf else 1, derniere_col)
        lig = max(int(mf.group(2)) if mf else 1, n)
        return '%s%s:%s%d"' % (m.group(1), debut if fin else 'A1', colonne_lettres(col), lig)
    texte = re.sub(r'(<%sdimension\s+ref=")([A-Z0-9:]+)"' % ep, dim, texte, 1)
    sortie = io.BytesIO()
    with zipfile.ZipFile(sortie, 'w') as dst:
        for info in src.infolist():
            if info.filename == fe.chemin:
                ni = zipfile.ZipInfo(info.filename, info.date_time)
                ni.compress_type = zipfile.ZIP_DEFLATED
                ni.external_attr = info.external_attr
                dst.writestr(ni, texte.encode('utf-8'))
            else:
                dst.writestr(info, _lire_zip(src, info.filename))
    src.close()
    return sortie.getvalue(), n


def ecrire_xlsx_simple(lignes: list[list], nom_feuille: str = 'Feuille1') -> bytes:
    """Petit classeur neuf (une feuille, textes en ligne) : sert aux essais et aux exemples de format."""
    def ligne_xml(r, vals):
        return '<row r="%d">%s</row>' % (r, ''.join(_cellule_xml('%s%d' % (colonne_lettres(k), r), v)
                                                     for k, v in enumerate(vals, 1)))
    nl = max(len(lignes), 1)
    nc = max((len(x) for x in lignes), default=1)
    feuille = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<worksheet xmlns="%s" xmlns:r="%s"><dimension ref="A1:%s%d"/><sheetData>%s</sheetData></worksheet>'
               % (NS_MAIN, NS_REL, colonne_lettres(nc), nl, ''.join(ligne_xml(r, v) for r, v in enumerate(lignes, 1))))
    fichiers = {
        '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.'
        'openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.'
        'openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.'
        'openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        '_rels/.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.'
        'openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
        'org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        'xl/workbook.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="%s" xmlns:r="%s">'
        '<sheets><sheet name="%s" sheetId="1" r:id="rId1"/></sheets></workbook>' % (NS_MAIN, NS_REL,
                                                                                     escape(nom_feuille)),
        'xl/_rels/workbook.xml.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="'
        'http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.'
        'openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>',
        'xl/worksheets/sheet1.xml': feuille,
    }
    sortie = io.BytesIO()
    with zipfile.ZipFile(sortie, 'w', zipfile.ZIP_DEFLATED) as z:
        for nom, contenu in fichiers.items():
            z.writestr(nom, contenu)
    return sortie.getvalue()
