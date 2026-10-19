"""Tableau des mesures d'un partage (« localisations ») : lecture tolérante, normalisation, contrôles ligne par ligne.

Les tableaux remplis à la main par les étudiants mélangent les formats (« 2,45° », 2.45, « 48°47′05″ N »,
« 03/11/2025 18:38:26 TU », « 10/25/2025 20:45:52 TU » à l'américaine, nombres de jours d'Excel), oublient des
champs, inversent latitude et longitude, notent l'heure locale au lieu du temps universel.  Ce module :

* repère la ligne d'en-tête et le rôle de chaque colonne par des mots-clés FR/EN (cible, fichier, auteur, date et
  heure, longitude, latitude, altitude, azimut, hauteur, ascension droite, déclinaison) ;
* normalise chaque valeur (angles, dates, altitudes) et dit ce qu'il a normalisé ;
* contrôle chaque ligne et signale les anomalies, avec la preuve quand il en a une :
  - latitude hors de [−90°, 90°] : inversion certaine ;
  - inversion probable confirmée par l'en-tête du fichier (SITELAT/SITELONG d'un FITS, GPS d'une photo) ou par la
    position de la Lune : la hauteur et l'azimut notés ne collent qu'avec les coordonnées échangées ;
  - heure locale probable : l'heure d'en-tête du fichier ou la position de la Lune s'accordent avec l'heure notée
    moins 1 h ou 2 h ;
  - date ambiguë (jour et mois ≤ 12) ou au format américain (mois/jour/année) ;
  - champs manquants, valeurs impossibles, fichier introuvable dans le partage, écart entre l'heure du tableau et
    celle de l'en-tête ;
* **ne modifie jamais l'original** : les corrections proposées sont des propositions, appliquées (ou non) aux
  calculs seulement, et toujours signalées dans les rapports.
"""
from __future__ import annotations

import datetime as D
import math
import re
import unicodedata
from dataclasses import dataclass, field

from .tableur import Cellule, Feuille, date_excel

UTC = D.timezone.utc

#: rôle -> mots-clés (minuscules, sans accents) ; le mot-clé le plus long qui convient l'emporte
MOTS_CLES = {
    'numero': ('n°', 'no', 'num', 'numero', 'number', '#', 'id', 'ou'),
    'cible': ('cible', 'target', 'objet', 'object'),
    'fichier': ('nom du fichier', 'fichier', 'file', 'filename', 'image', 'photo'),
    'auteur': ('auteur', 'author', 'observateur', 'observer', 'nom de l\'auteur', 'name', 'prenom'),
    'date': ('date', 'heure', 'time', 'utc', 'date + heure', 'instant', 'datetime'),
    'longitude': ('longitude', 'long', 'lon', 'lng'),
    'latitude': ('latitude', 'lat'),
    'altitude': ('altitude', 'alt', 'elevation (m)', 'altitude (m)'),
    'azimut': ('azimut', 'azimuth', 'az'),
    'hauteur': ('hauteur', 'elevation', 'height', 'hauteur sur l\'horizon', 'el'),
    'ra': ('ra', 'alpha', 'ascension', 'ascension droite', 'right ascension', 'ad'),
    'dec': ('dec', 'delta', 'declinaison', 'declination', 'de'),
}
ROLES = tuple(MOTS_CLES)


def normaliser(t: str) -> str:
    t = unicodedata.normalize('NFKD', str(t or ''))
    return ''.join(c for c in t if not unicodedata.combining(c)).lower().strip()


def role_et_score(entete: str) -> tuple[str, int]:
    """(rôle, force) d'une colonne d'après son titre ; ('', 0) si inconnu.  Un mot-clé court (≤ 4 lettres) doit être
    un mot entier du titre ; un mot-clé long peut en être une partie.  Le mot-clé le plus long l'emporte."""
    n = normaliser(entete)
    if not n:
        return '', 0
    mots = set(re.findall(r"[a-z]+", n))
    meilleur, score = '', 0
    for role, cles in MOTS_CLES.items():
        for c in cles:
            if re.fullmatch(r'[a-z]{1,4}', c):
                ok = c in mots
            else:
                ok = c in n
            if ok and len(c) > score:
                meilleur, score = role, len(c)
    # « altitude de la Lune (km) », « altitude de l'ISS » : un résultat, pas l'altitude du lieu
    if meilleur == 'altitude' and re.search(r'lune|moon|iss|km\)', n):
        return '', 0
    if meilleur == 'hauteur' and 'lune' in n:
        return '', 0
    return meilleur, score


def role_de(entete: str) -> str:
    return role_et_score(entete)[0]


# ============================================================================================== valeurs
@dataclass
class Valeur:
    valeur: object = None
    notes: list = field(default_factory=list)      # clés de texte « pt_n_* » : ce qui a été normalisé


RE_DMS = re.compile(r'^\s*([+-]?)\s*(\d+(?:[.,]\d+)?)\s*(?:°|d|:|\s)\s*(?:(\d+(?:[.,]\d+)?)\s*(?:[\'′m:]|\s)\s*'
                    r'(?:(\d+(?:[.,]\d+)?)\s*(?:["″s]|\'\')?)?)?\s*$')
RE_HMS = re.compile(r'^\s*(\d{1,2})\s*[h:\s]\s*(\d{1,2})\s*[m:\'′\s]\s*(\d{1,2}(?:[.,]\d+)?)\s*[s"″]?\s*$')


def angle(v, heures: bool = False, cellule: Cellule | None = None) -> Valeur:
    """« 2,45° », « 02,5658° », 2.45, « 48°47′05″ N », « 2°27′ E », « O 1,6 », « +44:13:51 » → degrés.
    `heures` : ascension droite (« 0h41m50s » ou nombre < 24 lu en heures si le titre le dit)."""
    out = Valeur()
    if v is None or v == '':
        return out
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if heures and cellule is not None and cellule.date and 0 <= float(v) < 1:
            out.valeur = float(v) * 24.0 * 15.0              # heure d'Excel (fraction de jour) : « 7:40:49 »
            out.notes.append('pt_n_hms')
            return out
        out.valeur = float(v) * (15.0 if heures else 1.0)
        return out
    t = str(v).strip()
    t = re.sub(r'(\d)\s*s$', '\\1″', t)          # « 50s » : des secondes (un « S » majuscule reste le sud)
    signe = 1.0
    m = re.search(r'\b([NSEOW])\b|([NSEOW])$|^([NSEOW])', t.upper().replace('°', ' '))
    if m:
        lettre = next(g for g in m.groups() if g)
        if lettre in 'SOW':
            signe = -1.0
        t = re.sub(r'(?i)\b[nseow]\b|[nseow]$|^[nseow]', '', t).strip()
        out.notes.append('pt_n_lettre')
    if ',' in t and '.' not in t:
        out.notes.append('pt_n_virgule')
    if '°' in t:
        out.notes.append('pt_n_degre')
    if heures or re.search(r'\d\s*h', t):
        mh = RE_HMS.match(t)
        if mh:
            h, mi, s = (float(x.replace(',', '.')) for x in mh.groups())
            out.valeur = signe * (h + mi / 60 + s / 3600) * 15.0
            out.notes.append('pt_n_hms')
            return out
    t2 = t.replace(',', '.').replace('°', ' ').replace('º', ' ').strip()
    try:
        out.valeur = signe * float(t2) * (15.0 if heures else 1.0)
        return out
    except ValueError:
        pass
    m4 = re.match(r'^\s*([+-]?)(\d{1,3}):(\d{1,2}):(\d{1,2}):(\d{1,2})\s*$', t)
    if m4:                                       # « +44:13:51:00 » : degrés, minutes, secondes, centièmes
        s0, d, mi, se, cs = m4.groups()
        val = int(d) + int(mi) / 60 + (int(se) + int(cs) / 100) / 3600
        out.valeur = (-1.0 if s0 == '-' else 1.0) * signe * val * (15.0 if heures else 1.0)
        out.notes.append('pt_n_dms')
        return out
    md = RE_DMS.match(t.replace('º', '°'))
    if md:
        s0, d, mi, se = md.groups()
        val = float(d.replace(',', '.')) + float((mi or '0').replace(',', '.')) / 60 + \
            float((se or '0').replace(',', '.')) / 3600
        out.valeur = (-1.0 if s0 == '-' else 1.0) * signe * val * (15.0 if heures else 1.0)
        out.notes.append('pt_n_dms')
        return out
    out.notes.append('pt_n_illisible')
    return out


def nombre(v) -> Valeur:
    out = Valeur()
    if v is None or v == '':
        return out
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        out.valeur = float(v)
        return out
    t = str(v).strip().lower()
    km = 'km' in t
    t = re.sub(r'[a-z\s]', '', t).replace(',', '.')
    try:
        out.valeur = float(t) * (1000.0 if km else 1.0)
        if km:
            out.notes.append('pt_n_km')
        if ',' in str(v):
            out.notes.append('pt_n_virgule')
    except ValueError:
        out.notes.append('pt_n_illisible')
    return out


RE_DATE = re.compile(r'(\d{1,4})[/.\-](\d{1,2})[/.\-](\d{1,4})[ T,]+(\d{1,2})[:h](\d{2})(?:[:m](\d{2}(?:[.,]\d+)?))?')
RE_FUSEAU = re.compile(r'\b(tu|ut|utc|gmt|z)\b|z$', re.I)
RE_LOCAL = re.compile(r'\b(locale?|local time|cet|cest|hec|heure d.?ete|heure d.?hiver)\b', re.I)
RE_DECALAGE = re.compile(r'(?:utc|gmt|tu)?\s*([+-])(\d{1,2})(?::?(\d{2}))?\s*$', re.I)


def instant(v, cellule: Cellule | None = None) -> Valeur:
    """Date et heure → datetime UTC (supposé UTC si le fuseau n'est pas dit : noté).  Nombres de jours d'Excel,
    « JJ/MM/AAAA HH:MM:SS », « AAAA-MM-JJ HH:MM:SS », « MM/JJ/AAAA » (américain, reconnu quand le jour > 12)."""
    out = Valeur()
    if v is None or v == '':
        return out
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if (cellule is not None and cellule.date) or 20000 < float(v) < 80000:
            d = date_excel(float(v))
            if d is not None:
                out.valeur = d.replace(tzinfo=UTC)
                out.notes.append('pt_n_excel')
                out.notes.append('pt_n_fuseau_non_dit')
        return out
    t = str(v).strip()
    m = RE_DATE.search(t)
    if not m:
        out.notes.append('pt_n_illisible')
        return out
    a, b, c, h, mi, s = m.groups()
    s = float((s or '0').replace(',', '.'))
    if len(a) == 4:
        annee, mois, jour = int(a), int(b), int(c)
    else:
        annee = int(c) + (2000 if len(c) == 2 else 0)
        x, y = int(a), int(b)
        if x > 12 and y <= 12:
            jour, mois = x, y
        elif y > 12 and x <= 12:
            mois, jour = x, y
            out.notes.append('pt_n_date_us')
        else:
            jour, mois = x, y
            if x != y and x <= 12 and y <= 12:
                out.notes.append('pt_n_date_ambigue')
    try:
        d = D.datetime(annee, mois, jour, int(h), int(mi), int(s), int(round((s % 1) * 1e6)) % 1000000, tzinfo=UTC)
    except ValueError:
        out.notes.append('pt_n_illisible')
        return out
    reste = t[m.end():]
    if RE_LOCAL.search(t):
        out.notes.append('pt_n_heure_locale_dite')
    elif RE_FUSEAU.search(reste) or RE_FUSEAU.search(t[:m.start()]):
        out.notes.append('pt_n_tu')
    else:
        md = RE_DECALAGE.search(reste)
        if md and reste.strip():
            dh = int(md.group(2)) + int(md.group(3) or 0) / 60
            d -= D.timedelta(hours=dh if md.group(1) == '+' else -dh)
            out.notes.append('pt_n_decalage')
        else:
            out.notes.append('pt_n_fuseau_non_dit')
    out.valeur = d
    return out


def cible_normalisee(t: str) -> str:
    from .structure import cible_de
    return cible_de(str(t or '')) or normaliser(t)


# ============================================================================================== lignes et anomalies
@dataclass
class Anomalie:
    ligne: int
    champ: str
    niveau: str                  # 'erreur' | 'attention' | 'info'
    cle: str                     # clé de texte pt_a_*
    valeurs: dict = field(default_factory=dict)


@dataclass
class Mesure:
    ligne: int                               # numéro de ligne du tableau (1 = première ligne)
    numero: str = ''
    cible: str = ''
    cible_brute: str = ''
    fichier: str = ''
    auteur: str = ''
    instant: D.datetime | None = None
    lat: float | None = None
    lon: float | None = None
    alt_m: float | None = None
    az: float | None = None
    h: float | None = None
    ra: float | None = None
    dec: float | None = None
    brut: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)        # champ -> [clés pt_n_*]
    corrections: dict = field(default_factory=dict)  # champ -> valeur proposée (jamais écrite dans l'original)
    anomalies: list = field(default_factory=list)

    def retenu(self, champ: str, appliquer: bool = True):
        """Valeur retenue pour les calculs : la correction proposée si `appliquer`, sinon la valeur lue."""
        if appliquer and champ in self.corrections:
            return self.corrections[champ]
        return getattr(self, champ)

    @property
    def niveau(self) -> str:
        n = {a.niveau for a in self.anomalies}
        return 'erreur' if 'erreur' in n else 'attention' if 'attention' in n else 'info' if n else 'ok'


@dataclass
class Tableau:
    feuille: str
    ligne_entete: int
    colonnes: dict                 # rôle -> numéro de colonne (1-based)
    titres: dict                   # numéro de colonne -> titre
    mesures: list
    anomalies: list

    def resume(self) -> dict:
        n = {'erreur': 0, 'attention': 0, 'info': 0}
        for a in self.anomalies:
            n[a.niveau] = n.get(a.niveau, 0) + 1
        return {'lignes': len(self.mesures), **n}


def trouver_entete(fe: Feuille, max_lignes: int = 40) -> tuple[int, dict, dict]:
    """(ligne d'en-tête, rôle -> colonne, colonne -> titre) : la première ligne qui nomme au moins trois rôles."""
    for l in range(1, min(fe.nb_lignes, max_lignes) + 1):
        roles, titres, forces = {}, {}, {}
        for c, cel in enumerate(fe.ligne(l), 1):
            if cel is None or not isinstance(cel.valeur, str):
                continue
            r, f = role_et_score(cel.valeur)
            titres[c] = cel.valeur
            if r and f > forces.get(r, 0):
                roles[r], forces[r] = c, f
        if len([r for r in roles if r != 'numero']) >= 3:
            return l, roles, titres
    return 0, {}, {}


def est_tableau_de_mesures(fe: Feuille) -> bool:
    l, roles, _ = trouver_entete(fe)
    return bool(l) and ({'latitude', 'longitude'} <= set(roles) or {'date', 'cible'} <= set(roles))


def lire_tableau(fe: Feuille) -> Tableau:
    l0, roles, titres = trouver_entete(fe)
    mesures = []
    if not l0:
        return Tableau(fe.nom, 0, {}, {}, [], [])
    heures_ra = 'ra' in roles and re.search(r'\bh\b|heure|hour', normaliser(titres.get(roles['ra'], '')))
    for l in range(l0 + 1, fe.nb_lignes + 1):
        cel = {r: fe.cellules.get((l, c)) for r, c in roles.items()}
        utiles = [r for r, x in cel.items() if x is not None and x.valeur not in (None, '') and r != 'numero']
        if not utiles:
            continue
        m = Mesure(l)
        m.brut = {r: (x.texte() if x is not None else '') for r, x in cel.items()}

        def val(r):
            x = cel.get(r)
            return x.valeur if x is not None else None
        m.numero = m.brut.get('numero', '')
        m.cible_brute = str(val('cible') or '').strip()
        m.cible = cible_normalisee(m.cible_brute) if m.cible_brute else ''
        m.fichier = str(val('fichier') or '').strip()
        m.auteur = str(val('auteur') or '').strip()
        for champ, fonc in (('lat', lambda v: angle(v)), ('lon', lambda v: angle(v)),
                            ('az', lambda v: angle(v)), ('h', lambda v: angle(v)),
                            ('ra', lambda v: angle(v, heures=bool(heures_ra), cellule=cel.get('ra'))),
                            ('dec', lambda v: angle(v)),
                            ('alt_m', nombre)):
            role = {'lat': 'latitude', 'lon': 'longitude', 'az': 'azimut', 'h': 'hauteur', 'alt_m': 'altitude'}.get(
                champ, champ)
            r = fonc(val(role))
            setattr(m, champ, r.valeur)
            if r.notes:
                m.notes[champ] = r.notes
        r = instant(val('date'), cel.get('date'))
        m.instant = r.valeur
        if r.notes:
            m.notes['instant'] = r.notes
        mesures.append(m)
    return Tableau(fe.nom, l0, roles, titres, mesures, [])


# ------------------------------------------------------------------------------------------------ contrôles
def _a(m: Mesure, champ, niveau, cle, **v):
    a = Anomalie(m.ligne, champ, niveau, cle, v)
    m.anomalies.append(a)
    return a


def controler(t: Tableau, fichiers_partage: dict | None = None, entetes: dict | None = None,
              verifier_lune: bool = True) -> Tableau:
    """Contrôles ligne par ligne.  `fichiers_partage` : {nom de fichier normalisé: chemin} du partage ;
    `entetes` : {nom de fichier: {'lat', 'lon', 'instant', 'alt_m'}} lus dans les en-têtes (FITS, EXIF)."""
    entetes = {normaliser(k): v for k, v in (entetes or {}).items()}
    t.anomalies = []
    vus: dict[str, int] = {}
    for m in t.mesures:
        m.anomalies = []
        m.corrections = {}
        for champ, cle in (('cible', 'cible'), ('fichier', 'fichier'), ('auteur', 'auteur'), ('instant', 'date'),
                           ('lat', 'latitude'), ('lon', 'longitude')):
            if cle in t.colonnes and getattr(m, champ) in (None, ''):
                illisible = 'pt_n_illisible' in m.notes.get(champ, [])
                _a(m, champ, 'erreur' if champ in ('instant', 'lat', 'lon') else 'attention',
                   'pt_a_illisible' if illisible else 'pt_a_manquant', valeur=m.brut.get(cle, ''))
        for champ, notes in m.notes.items():
            if 'pt_n_virgule' in notes or 'pt_n_degre' in notes or 'pt_n_dms' in notes or 'pt_n_lettre' in notes:
                _a(m, champ, 'info', 'pt_a_normalise', valeur=m.brut.get(_role(champ), ''),
                   lu=_format(getattr(m, champ)))
        n_inst = m.notes.get('instant', [])
        if 'pt_n_date_us' in n_inst:
            _a(m, 'instant', 'attention', 'pt_a_date_us', valeur=m.brut.get('date', ''), lu=_format(m.instant))
        if 'pt_n_date_ambigue' in n_inst:
            _date_ambigue(m)
        if 'pt_n_heure_locale_dite' in n_inst:
            _a(m, 'instant', 'attention', 'pt_a_heure_locale_dite', valeur=m.brut.get('date', ''))
        if 'pt_n_fuseau_non_dit' in n_inst and 'pt_n_excel' not in n_inst:
            _a(m, 'instant', 'info', 'pt_a_fuseau_non_dit', valeur=m.brut.get('date', ''))
        _controle_valeurs(m)
        _controle_inversion(m, entetes, verifier_lune)
        _controle_heure(m, entetes, verifier_lune)
        if fichiers_partage is not None and m.fichier:
            nf = normaliser(m.fichier)
            if nf not in fichiers_partage and not any(k.startswith(nf + '.') or k.rsplit('.', 1)[0] == nf
                                                       for k in fichiers_partage):
                proche = _plus_proche(nf, list(fichiers_partage))
                _a(m, 'fichier', 'attention', 'pt_a_fichier_absent', valeur=m.fichier, proche=proche)
        if m.fichier:
            cle = normaliser(m.fichier)
            if cle in vus:
                _a(m, 'fichier', 'info', 'pt_a_doublon', autre=vus[cle])
            vus.setdefault(cle, m.ligne)
    _controle_groupe(t, entetes)
    for m in t.mesures:
        _controle_lune(m, verifier_lune)
        t.anomalies.extend(m.anomalies)
    return t


def _date_ambigue(m: Mesure):
    """Jour et mois ≤ 12 : le nom du fichier (« 2025-11-03-… ») tranche s'il porte une date ; sinon, signalé."""
    from .structure import instants_du_nom
    lu = m.instant.date()
    noms = {d.date() for d in instants_du_nom(m.fichier)} if m.fichier else set()
    if lu in noms:
        return                                          # confirmée par le nom du fichier
    try:
        echange = m.instant.replace(month=lu.day, day=lu.month)
    except ValueError:
        echange = None
    if echange is not None and echange.date() in noms:
        m.corrections['instant'] = echange
        _a(m, 'instant', 'attention', 'pt_a_date_inversee_nom', valeur=m.brut.get('date', ''),
           nom=echange.date().isoformat(), lu=_format(echange))
        return
    _a(m, 'instant', 'attention', 'pt_a_date_ambigue', valeur=m.brut.get('date', ''), lu=_format(m.instant))


def _ecart_deg(a, b) -> float:
    """Écart approximatif (degrés de grand cercle) entre deux points (lat, lon)."""
    la1, lo1, la2, lo2 = (math.radians(x) for x in (a[0], a[1], b[0], b[1]))
    c = math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2) * math.cos(lo2 - lo1)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def _controle_groupe(t: Tableau, entetes: dict):
    """Inversion probable par comparaison : les coordonnées échangées tombent près (< 10°) d'un lieu SÛR (ligne
    confirmée, en-tête d'un fichier) alors que les coordonnées telles quelles sont loin (> 30°) de tous les lieux
    sûrs.  Sans lieu sûr, rien n'est signalé (un site lointain, par exemple dans l'hémisphère sud, est légitime)."""
    surs = [(e['lat'], e['lon']) for e in entetes.values() if e.get('lat') is not None and e.get('lon') is not None]
    for m in t.mesures:
        if 'lat' in m.corrections and m.corrections.get('lon') is not None:
            surs.append((m.corrections['lat'], m.corrections['lon']))
        elif m.lat is not None and m.lon is not None and not any(a.champ == 'lat' for a in m.anomalies) and \
                normaliser(m.fichier) in entetes:
            surs.append((m.lat, m.lon))
    if not surs:
        return
    for m in t.mesures:
        if m.lat is None or m.lon is None or 'lat' in m.corrections or abs(m.lat) > 90 or abs(m.lon) > 90:
            continue
        direct = min(_ecart_deg((m.lat, m.lon), s) for s in surs)
        echange = min(_ecart_deg((m.lon, m.lat), s) for s in surs)
        if echange < 10 and direct > 30:
            m.corrections['lat'], m.corrections['lon'] = m.lon, m.lat
            _a(m, 'lat', 'attention', 'pt_a_inversion_probable', lat=_format(m.lat), lon=_format(m.lon),
               ecart='%.0f' % (echange * 111))


def _controle_lune(m: Mesure, verifier_lune: bool):
    """Hauteur et azimut notés comparés à la position de la Lune (lieu et heure retenus) : écart > 2° signalé."""
    if not (verifier_lune and m.cible == 'lune' and m.h is not None and m.az is not None):
        return
    lat, lon, inst = m.retenu('lat'), m.retenu('lon'), m.retenu('instant')
    if lat is None or lon is None or inst is None:
        return
    e = _ecart_altaz(lat, lon, m.alt_m, inst, m.h, m.az)
    if e is not None and e > 2:
        from . import astro
        hl, azl, _, _ = astro.altaz_lune(lat, lon, m.alt_m or 0.0, astro.Instant(inst))
        _a(m, 'h', 'attention' if e < 20 else 'erreur', 'pt_a_altaz_lune', ecart='%.1f' % e, h='%.1f' % hl,
           az='%.1f' % azl)


def _role(champ):
    return {'lat': 'latitude', 'lon': 'longitude', 'az': 'azimut', 'h': 'hauteur', 'alt_m': 'altitude',
            'instant': 'date'}.get(champ, champ)


def _format(v) -> str:
    if isinstance(v, float):
        return ('%.6f' % v).rstrip('0').rstrip('.')
    if isinstance(v, D.datetime):
        return v.strftime('%Y-%m-%d %H:%M:%S') + (' UTC' if v.tzinfo else '')
    return '' if v is None else str(v)


def _controle_valeurs(m: Mesure):
    if m.alt_m is not None and not -500 <= m.alt_m <= 6000:
        _a(m, 'alt_m', 'attention', 'pt_a_altitude', valeur=_format(m.alt_m))
    if m.az is not None and not 0 <= m.az <= 360:
        _a(m, 'az', 'erreur', 'pt_a_azimut', valeur=_format(m.az))
    if m.h is not None and not -5 <= m.h <= 90:
        _a(m, 'h', 'erreur', 'pt_a_hauteur', valeur=_format(m.h))
    if m.lon is not None and not -180 <= m.lon <= 360:
        _a(m, 'lon', 'erreur', 'pt_a_longitude', valeur=_format(m.lon))


def _ecart_altaz(lat, lon, alt_m, inst, h, az) -> float | None:
    """Écart angulaire (°) entre la position notée (h, az) et celle de la Lune vue du lieu à l'instant."""
    from . import astro
    try:
        hl, azl, _, _ = astro.altaz_lune(lat, lon, alt_m or 0.0, astro.Instant(inst))
    except Exception:
        return None
    u = astro.vecteur_altaz(0.0, 0.0, h, az)
    v = astro.vecteur_altaz(0.0, 0.0, hl, azl)
    return astro.separation_deg(u, v)


def _controle_inversion(m: Mesure, entetes: dict, verifier_lune: bool):
    if m.lat is None or m.lon is None:
        return
    if abs(m.lat) > 90 and abs(m.lon) <= 90:
        m.corrections['lat'], m.corrections['lon'] = m.lon, m.lat
        _a(m, 'lat', 'erreur', 'pt_a_inversion_certaine', lat=_format(m.lat), lon=_format(m.lon))
        return
    if abs(m.lat) > 90:
        _a(m, 'lat', 'erreur', 'pt_a_latitude', valeur=_format(m.lat))
        return
    ref = entetes.get(normaliser(m.fichier)) or entetes.get(normaliser(m.fichier).rsplit('.', 1)[0])
    if ref and ref.get('lat') is not None and ref.get('lon') is not None:
        direct = abs(ref['lat'] - m.lat) + abs(ref['lon'] - m.lon)
        echange = abs(ref['lat'] - m.lon) + abs(ref['lon'] - m.lat)
        if echange < 0.1 and direct > 0.5:
            m.corrections['lat'], m.corrections['lon'] = m.lon, m.lat
            _a(m, 'lat', 'erreur', 'pt_a_inversion_entete', lat=_format(ref['lat']), lon=_format(ref['lon']))
            return
        if direct > 0.1:
            _a(m, 'lat', 'attention', 'pt_a_ecart_entete', lat=_format(ref['lat']), lon=_format(ref['lon']),
               ecart_km='%.0f' % (direct * 111))
        return
    if verifier_lune and m.cible == 'lune' and m.retenu('instant') is not None and m.h is not None and m.az is not None:
        e_direct = _ecart_altaz(m.lat, m.lon, m.alt_m, m.retenu('instant'), m.h, m.az)
        e_echange = _ecart_altaz(m.lon, m.lat, m.alt_m, m.retenu('instant'), m.h, m.az)
        if e_direct is not None and e_echange is not None and e_echange < 5 and e_direct > 3 * max(e_echange, 2):
            m.corrections['lat'], m.corrections['lon'] = m.lon, m.lat
            _a(m, 'lat', 'erreur', 'pt_a_inversion_lune', direct='%.1f' % e_direct, echange='%.1f' % e_echange)
            return


def _controle_heure(m: Mesure, entetes: dict, verifier_lune: bool):
    if m.instant is None:
        return
    inst = m.retenu('instant')
    ref = entetes.get(normaliser(m.fichier)) or entetes.get(normaliser(m.fichier).rsplit('.', 1)[0])
    if ref and isinstance(ref.get('instant'), D.datetime):
        dt = (inst - ref['instant']).total_seconds()
        for heures in (1, 2, -1, -2):
            if abs(dt - heures * 3600) < 120:
                m.corrections['instant'] = inst - D.timedelta(hours=heures)
                _a(m, 'instant', 'erreur', 'pt_a_heure_locale_entete', heures='%+d' % heures,
                   entete=_format(ref['instant']))
                return
        if abs(dt) > 0.5:
            _a(m, 'instant', 'attention' if abs(dt) > 2 else 'info', 'pt_a_ecart_horloge', ecart='%+.1f' % dt,
               entete=_format(ref['instant']))
        return
    if verifier_lune and m.cible == 'lune' and m.h is not None and m.az is not None:
        lat, lon = m.retenu('lat'), m.retenu('lon')
        if lat is None or lon is None:
            return
        e0 = _ecart_altaz(lat, lon, m.alt_m, inst, m.h, m.az)
        if e0 is None or e0 < 3:
            return
        meilleurs = []
        for heures in (1, 2, -1, -2):
            e = _ecart_altaz(lat, lon, m.alt_m, inst - D.timedelta(hours=heures), m.h, m.az)
            if e is not None:
                meilleurs.append((e, heures))
        if meilleurs:
            e, heures = min(meilleurs)
            if e < 3 and e0 > 3 * max(e, 1):
                m.corrections['instant'] = inst - D.timedelta(hours=heures)
                _a(m, 'instant', 'attention', 'pt_a_heure_locale_lune', heures='%+d' % heures, e0='%.1f' % e0,
                   e='%.1f' % e)


def _plus_proche(n: str, noms: list) -> str:
    import difflib
    r = difflib.get_close_matches(n, noms, 1, 0.6)
    return r[0] if r else ''
