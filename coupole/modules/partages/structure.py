"""Découverte de la STRUCTURE d'un partage d'étudiants : rien n'y est normalisé, tout est deviné et dit comme tel.

À partir de la seule liste des fichiers (chemin, taille, date de dépôt), sans rien télécharger :

* **genre** de chaque fichier : image FITS, JPEG, PNG, TIFF, vidéo SER/AVI/MP4, tableau (xlsx, ods, csv),
  solution astrométrique (.wcs, .new, .axy, .corr), image annotée par astrometry.net (« astrometry » dans le nom),
  document ;
* **instant** de la prise d'après le nom (« AAAA-MM-JJ-HH-MM-SS », « AA-MM-JJ-HH-MM-SS.sss » ou « JJ-MM-AA-… »,
  « IMG20260618223000 », « ISS_20251018_050430 ») : un nom qui se lit de deux façons (17-10-26 = 17 octobre 2026 ou
  26 octobre 2017) est tranché par la date de dépôt du fichier (la prise est antérieure au dépôt, et proche) ;
  l'heure d'un nom est souvent l'heure LOCALE de l'appareil : elle est marquée « d'après le nom » et ne remplace
  jamais l'heure TU d'un en-tête FITS ou d'un tableau ;
* **date du dossier** (« 17 Octobre 2026 », « 2025 », « 2026-10-17 », « 17-10-2026 - Lieu - Nom ») ;
* **observateur** : dernière partie d'un dossier « date - lieu - nom », ou initiales/nom qui suivent l'heure dans le
  nom du fichier (« …-38-26-ABC.fits » → « ABC ») ;
* **cible** : mots du nom ou du dossier (ISS, Lune/Moon, Soleil, planètes…) ;
* **prises** : fichiers du même instant et du même observateur (FITS + PNG + TIFF d'une même photo) ;
* **séries** : prises successives d'un observateur dans un dossier, espacées de moins de 2 minutes ;
* **tableaux de métadonnées** : xlsx/ods/csv (ex. tableau des localisations, feuille de calculs).
"""
from __future__ import annotations

import datetime as D
import os
import re
import unicodedata
from dataclasses import dataclass, field

UTC = D.timezone.utc

GENRES = {
    'fits': ('.fits', '.fit', '.fts', '.fits.fz', '.fit.fz', '.fz'),
    'jpeg': ('.jpg', '.jpeg', '.jpe'),
    'png': ('.png',),
    'tiff': ('.tif', '.tiff'),
    'raw': ('.cr2', '.cr3', '.nef', '.arw', '.dng', '.orf', '.raf', '.rw2'),
    'xisf': ('.xisf',),
    'ser': ('.ser',),
    'avi': ('.avi',),
    'video': ('.mp4', '.mov', '.mkv', '.m4v', '.webm'),
    'tableau': ('.xlsx', '.xlsm', '.ods', '.csv', '.tsv'),
    'astrometrie': ('.wcs', '.new', '.axy', '.corr', '.rdls', '.match', '.solved'),
    'document': ('.pdf', '.txt', '.md', '.doc', '.docx', '.odt', '.tex', '.html'),
}
IMAGES = ('fits', 'jpeg', 'png', 'tiff', 'raw', 'xisf')
VIDEOS = ('ser', 'avi', 'video')
APERCU_POSSIBLE = ('fits', 'jpeg', 'png', 'tiff', 'ser', 'avi')

MOIS = {'janvier': 1, 'janv': 1, 'jan': 1, 'january': 1, 'fevrier': 2, 'fevr': 2, 'fev': 2, 'feb': 2, 'february': 2,
        'mars': 3, 'mar': 3, 'march': 3, 'avril': 4, 'avr': 4, 'apr': 4, 'april': 4, 'mai': 5, 'may': 5, 'juin': 6,
        'jun': 6, 'june': 6, 'juillet': 7, 'juil': 7, 'jul': 7, 'july': 7, 'aout': 8, 'aug': 8, 'august': 8,
        'septembre': 9, 'sept': 9, 'sep': 9, 'september': 9, 'octobre': 10, 'oct': 10, 'october': 10,
        'novembre': 11, 'nov': 11, 'november': 11, 'decembre': 12, 'dec': 12, 'december': 12}
#: mots -> cible normalisée (clé de texte « pt_cible_<cible> »)
CIBLES = {'iss': 'iss', 'tiangong': 'tiangong', 'css': 'tiangong', 'lune': 'lune', 'moon': 'lune', 'lunaire': 'lune',
          'soleil': 'soleil', 'sun': 'soleil', 'jupiter': 'jupiter', 'saturne': 'saturne', 'saturn': 'saturne',
          'mars': 'mars', 'venus': 'venus', 'mercure': 'mercure', 'mercury': 'mercure', 'uranus': 'uranus',
          'neptune': 'neptune', 'eclipse': 'eclipse', 'occultation': 'occultation', 'comete': 'comete',
          'comet': 'comete', 'asteroide': 'asteroide', 'asteroid': 'asteroide', 'spectre': 'spectre',
          'spectrum': 'spectre'}
#: mots qui ne sont ni un observateur ni une cible (appareils, logiciels, procédés)
MOTS_TECHNIQUES = {'img', 'dsc', 'dscn', 'pxl', 'mvimg', 'vid', 'image', 'photo', 'astrometry', 'astrometrie', 'net',
                   'wcs', 'solved', 'new', 'final', 'stack', 'stacked', 'light', 'raw', 'crop', 'copie', 'copy',
                   'test', 'essai', 'parallaxe', 'parallax', 'smartphone', 'tp', 'defi', 'mesure', 'mesures',
                   'calculs', 'calcul', 'resultats', 'localisations', 'localisation', 'pose', 'serie', 'tu', 'ut',
                   'utc', 'gmt', 'cest', 'cet', 'h', 'min', 's', 'et', 'de', 'du', 'la', 'le', 'les', 'des', 'and',
                   'the', 'of', 'jpg', 'png', 'fits', 'fit', 'tif', 'tiff'}


def normaliser(t: str) -> str:
    t = unicodedata.normalize('NFKD', t or '')
    return ''.join(c for c in t if not unicodedata.combining(c)).lower()


def genre_de(nom: str) -> str:
    n = nom.lower()
    for g, exts in GENRES.items():
        if n.endswith(exts):
            return g
    return 'autre'


def est_annotation(nom: str) -> bool:
    """Image annotée renvoyée par astrometry.net (pas une mesure : une illustration)."""
    n = normaliser(nom)
    return 'astrometry' in n or 'annot' in n


# ============================================================================================== dates et heures
RE_HEURE_SEP = re.compile(r'(?<!\d)(\d{2}|\d{4})[-_.](\d{2})[-_.](\d{2})[-_ T.](\d{2})[-_.:h](\d{2})[-_.:m](\d{2})'
                          r'(?:[.,](\d{1,6}))?(?!\d)')
RE_HEURE_COLLEE = re.compile(r'(?<!\d)(\d{4})(\d{2})(\d{2})[_\-T]?(\d{2})(\d{2})(\d{2})(?:[.,_]?(\d{3}))?(?!\d)')
RE_DATE_SEULE = re.compile(r'(?<!\d)(\d{4})[-_.](\d{2})[-_.](\d{2})(?!\d)|(?<!\d)(\d{2})[-_./](\d{2})[-_./](\d{4})(?!\d)')
RE_DATE_MOIS = re.compile(r'(?<!\d)(\d{1,2})(?:er)?\s+([a-zA-Zéèûôà]+)\.?\s+(\d{4})(?!\d)')
RE_ANNEE = re.compile(r'^(19|20)\d{2}$')


def _dt(a, mo, j, h=0, mi=0, s=0, frac='') -> D.datetime | None:
    try:
        us = int((frac or '0').ljust(6, '0')[:6])
        return D.datetime(int(a), int(mo), int(j), int(h), int(mi), int(s), us, tzinfo=UTC)
    except ValueError:
        return None


def instants_du_nom(nom: str) -> list[D.datetime]:
    """Tous les instants qu'un nom de fichier peut signifier (souvent un seul ; deux si l'ordre est ambigu)."""
    base = os.path.splitext(nom)[0]
    out = []
    m = RE_HEURE_SEP.search(base)
    if m:
        x, y, z, h, mi, s, fr = m.groups()
        if len(x) == 4:
            out.append(_dt(x, y, z, h, mi, s, fr))
        else:
            out.append(_dt(2000 + int(x), y, z, h, mi, s, fr))      # AA-MM-JJ
            out.append(_dt(2000 + int(z), y, x, h, mi, s, fr))      # JJ-MM-AA
    else:
        m = RE_HEURE_COLLEE.search(base)
        if m:
            a, mo, j, h, mi, s, fr = m.groups()
            out.append(_dt(a, mo, j, h, mi, s, fr))
    vus, res = set(), []
    for d in out:
        if d is not None and 1990 <= d.year <= 2100 and d not in vus:
            vus.add(d)
            res.append(d)
    return res


def instant_du_nom(nom: str, depot: float = 0.0) -> D.datetime | None:
    """L'instant du nom ; s'il est ambigu, celui qui précède le dépôt du fichier et en est le plus proche."""
    c = instants_du_nom(nom)
    if not c:
        return None
    if len(c) == 1 or not depot:
        return c[0]
    t = D.datetime.fromtimestamp(depot, UTC)
    avant = [d for d in c if d <= t + D.timedelta(days=1)]
    return min(avant or c, key=lambda d: abs((t - d).total_seconds()))


def date_du_dossier(nom: str) -> D.date | None:
    """« 17 Octobre 2026 », « 2026-10-17 », « 17-10-2026 - Lieu - Nom » → date ; « 2025 » → 1er janvier (année seule)."""
    n = normaliser(nom)
    m = RE_DATE_MOIS.search(n)
    if m and m.group(2).rstrip('.') in MOIS:
        try:
            return D.date(int(m.group(3)), MOIS[m.group(2).rstrip('.')], int(m.group(1)))
        except ValueError:
            pass
    m = RE_DATE_SEULE.search(n)
    if m:
        try:
            if m.group(1):
                return D.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return D.date(int(m.group(6)), int(m.group(5)), int(m.group(4)))
        except ValueError:
            pass
    if RE_ANNEE.match(n.strip()):
        return D.date(int(n.strip()), 1, 1)
    return None


def annee_seule(nom: str) -> bool:
    return bool(RE_ANNEE.match(normaliser(nom).strip()))


# ============================================================================================== observateur, cible
def _mots(texte: str) -> list[str]:
    return [m for m in re.split(r'[^0-9A-Za-zÀ-ÿ]+', texte) if m]


def cible_de(*textes: str) -> str:
    for t in textes:
        for m in _mots(normaliser(t)):
            if m in CIBLES:
                return CIBLES[m]
    return ''


def observateur_du_nom(nom: str) -> str:
    """Ce qui suit l'heure dans le nom (« …-18-38-26-ABC.fits » → « ABC », « …-04-29-11.204-Prénom Nom.fit » →
    « Prénom Nom »), sans les mots techniques ni les cibles ; '' sinon."""
    base = os.path.splitext(os.path.splitext(nom)[0])[0] if nom.lower().endswith('.fz') else os.path.splitext(nom)[0]
    m = RE_HEURE_SEP.search(base) or RE_HEURE_COLLEE.search(base)
    reste = base[m.end():] if m else ''
    avant = base[:m.start()] if m else base
    mots = [w for w in _mots(reste) if normaliser(w) not in MOTS_TECHNIQUES and normaliser(w) not in CIBLES
            and not w.isdigit()]
    if not mots and m:
        mots = [w for w in _mots(avant) if normaliser(w) not in MOTS_TECHNIQUES and normaliser(w) not in CIBLES
                and not w.isdigit()]
        if len(mots) > 2:
            return ''
    return ' '.join(mots)[:60]


def decouper_dossier(nom: str) -> dict:
    """« 17-10-2026 - Lieu - Prénom Nom » → {'date', 'lieu', 'observateur'} (parties reconnues seulement)."""
    parties = [p.strip() for p in re.split(r'\s+[-–—]\s+|\s*_\s*-\s*', nom) if p.strip()]
    out = {'date': date_du_dossier(nom), 'lieu': '', 'observateur': ''}
    if len(parties) >= 2 and date_du_dossier(parties[0]):
        reste = parties[1:]
        if len(reste) >= 2:
            out['lieu'], out['observateur'] = reste[0], ' - '.join(reste[1:])
        else:
            out['observateur'] = reste[0]
    return out


# ============================================================================================== modèle
@dataclass
class Fichier:
    chemin: str
    taille: int
    depot: float                      # date de dépôt sur le serveur (epoch UTC)
    etag: str = ''
    genre: str = 'autre'
    instant: D.datetime | None = None  # d'après le nom (à confirmer par l'en-tête)
    instant_source: str = ''          # 'nom' | 'entete' | 'tableau'
    observateur: str = ''
    cible: str = ''
    annotation: bool = False
    prise: str = ''                   # identifiant de la prise (variantes d'une même photo)
    serie: str = ''
    nouveau: bool = False
    doute: bool = False               # instant du nom incohérent avec la date du dossier ou du dépôt

    @property
    def nom(self) -> str:
        return self.chemin.rsplit('/', 1)[-1]

    @property
    def dossier(self) -> str:
        return self.chemin.rsplit('/', 1)[0] if '/' in self.chemin else ''


@dataclass
class Serie:
    ident: str
    dossier: str
    observateur: str
    cible: str
    debut: D.datetime
    fin: D.datetime
    fichiers: list = field(default_factory=list)

    @property
    def duree(self) -> float:
        return (self.fin - self.debut).total_seconds()

    def genres(self) -> dict:
        out: dict[str, int] = {}
        for f in self.fichiers:
            out[f.genre] = out.get(f.genre, 0) + 1
        return out


@dataclass
class Dossier:
    chemin: str
    date: D.date | None = None
    annee_seule: bool = False
    lieu: str = ''
    observateur: str = ''
    sous_dossiers: list = field(default_factory=list)
    fichiers: list = field(default_factory=list)

    @property
    def nom(self) -> str:
        return self.chemin.rsplit('/', 1)[-1] if self.chemin else ''

    def tous_les_fichiers(self) -> list:
        out = list(self.fichiers)
        for d in self.sous_dossiers:
            out.extend(d.tous_les_fichiers())
        return out

    def taille(self) -> int:
        return sum(f.taille for f in self.tous_les_fichiers())


@dataclass
class Structure:
    racine: Dossier
    fichiers: list
    dossiers: dict
    series: list
    tableaux: list
    observateurs: list
    cibles: list

    def fichier(self, chemin: str) -> Fichier | None:
        return next((f for f in self.fichiers if f.chemin == chemin), None)

    def resume(self) -> dict:
        n: dict[str, int] = {}
        for f in self.fichiers:
            n[f.genre] = n.get(f.genre, 0) + 1
        return {'fichiers': len(self.fichiers), 'dossiers': len(self.dossiers) - 1, 'octets': self.racine.taille(),
                'genres': n, 'series': len(self.series), 'observateurs': len(self.observateurs),
                'tableaux': len(self.tableaux), 'nouveaux': sum(1 for f in self.fichiers if f.nouveau)}


ECART_SERIE_S = 120.0


def decouvrir(entrees, deja_vus: set | None = None) -> Structure:
    """`entrees` : objets ou dicts avec chemin, dossier, taille, modifie, etag (webdav.Entree).
    `deja_vus` : chemins vus à la visite précédente (None : première visite, rien n'est « nouveau »)."""
    dossiers: dict[str, Dossier] = {'': Dossier('')}
    fichiers: list[Fichier] = []

    def dossier(chemin: str) -> Dossier:
        if chemin in dossiers:
            return dossiers[chemin]
        parent = dossier(chemin.rsplit('/', 1)[0] if '/' in chemin else '')
        nom = chemin.rsplit('/', 1)[-1]
        dec = decouper_dossier(nom)
        d = Dossier(chemin, dec['date'] or parent.date, annee_seule(nom) or (dec['date'] is None and parent.annee_seule),
                    dec['lieu'] or parent.lieu, dec['observateur'] or parent.observateur)
        dossiers[chemin] = d
        parent.sous_dossiers.append(d)
        return d
    for e in entrees:
        get = (lambda k, d=None, e=e: e.get(k, d)) if isinstance(e, dict) else (lambda k, d=None, e=e: getattr(e, k, d))
        chemin = (get('chemin') or '').strip('/')
        if not chemin:
            continue
        if get('dossier'):
            dossier(chemin)
            continue
        d = dossier(chemin.rsplit('/', 1)[0] if '/' in chemin else '')
        nom = chemin.rsplit('/', 1)[-1]
        f = Fichier(chemin, int(get('taille') or 0), float(get('modifie') or 0), get('etag') or '', genre_de(nom))
        f.annotation = est_annotation(nom) and f.genre in IMAGES
        f.instant = instant_du_nom(nom, f.depot)
        if f.instant is not None:
            f.instant_source = 'nom'
        if f.instant is not None:
            f.doute = _douteux(f.instant, d, f.depot)
        f.observateur = observateur_du_nom(nom) or d.observateur
        f.cible = cible_de(nom, d.nom, d.chemin)
        f.nouveau = deja_vus is not None and chemin not in deja_vus
        d.fichiers.append(f)
        fichiers.append(f)
    for d in dossiers.values():
        d.sous_dossiers.sort(key=lambda x: (x.date or D.date.max, normaliser(x.nom)))
        d.fichiers.sort(key=lambda f: (f.instant or D.datetime.max.replace(tzinfo=UTC), normaliser(f.nom)))
    # prises : même dossier, même observateur, même instant (variantes FITS/PNG/TIFF d'une photo)
    for f in fichiers:
        if f.instant is not None and f.genre in IMAGES + VIDEOS:
            f.prise = '%s|%s|%s' % (f.dossier, normaliser(f.observateur), f.instant.isoformat())
    # séries : prises successives d'un observateur dans un dossier (écart < 2 min)
    series: list[Serie] = []
    groupes: dict[tuple, list[Fichier]] = {}
    for f in fichiers:
        if f.instant is not None and f.genre in IMAGES + VIDEOS and not f.annotation:
            groupes.setdefault((f.dossier, normaliser(f.observateur)), []).append(f)
    for (dos, _obs), liste in sorted(groupes.items()):
        liste.sort(key=lambda f: f.instant)
        courant: list[Fichier] = []
        for f in liste:
            if courant and (f.instant - courant[-1].instant).total_seconds() > ECART_SERIE_S:
                series.append(_serie(courant, len(series)))
                courant = []
            courant.append(f)
        if courant:
            series.append(_serie(courant, len(series)))
    for s in series:
        for f in s.fichiers:
            f.serie = s.ident
    tableaux = [f for f in fichiers if f.genre == 'tableau']
    obs = sorted({f.observateur for f in fichiers if f.observateur}, key=normaliser)
    cibles = sorted({f.cible for f in fichiers if f.cible})
    return Structure(dossiers[''], fichiers, dossiers, series, tableaux, obs, cibles)


def _douteux(instant: D.datetime, d: Dossier, depot: float) -> bool:
    """Un instant tiré du nom qui contredit la date du dossier (autre année, ou autre jour à plus de 2 jours près)
    ou qui suit le dépôt, ou le précède de plus d'un an."""
    if d.date is not None:
        if d.annee_seule:
            if instant.year != d.date.year:
                return True
        elif abs((instant.date() - d.date).days) > 2:
            return True
    if depot:
        t = D.datetime.fromtimestamp(depot, UTC)
        if instant > t + D.timedelta(days=1) or (t - instant).days > 366:
            return True
    return False


def _serie(fichiers: list, k: int) -> Serie:
    f0 = fichiers[0]
    cibles = [f.cible for f in fichiers if f.cible]
    return Serie('s%d' % (k + 1), f0.dossier, f0.observateur, max(set(cibles), key=cibles.count) if cibles else '',
                 fichiers[0].instant, fichiers[-1].instant, list(fichiers))
