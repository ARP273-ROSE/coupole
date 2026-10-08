"""Recherche d'un objet dans SIMBAD (CDS, Strasbourg) à partir de son nom, et fiche détaillée.

Repris du calculateur « cosmologie-redshift » du même auteur (``programme/simbad.py``, déjà testé sur la
vraie API), adapté à Coupole : adresse du service lue dans les sources (``simbad.base``), User-Agent de
l'application, délais courts, erreurs réseau traduites en ``SimbadError`` (une ``ServiceInjoignable``).

Le but est qu'un nom tapé de mémoire suffise : « m31 », « M 31 », « ngc224 », « Andromeda », « 3c273 »
désignent tous quelque chose de précis pour SIMBAD, mais pas sous la même forme.  Trois niveaux sont
enchaînés, du moins coûteux au plus large :

  1. la saisie est envoyée telle quelle au résolveur de noms (``sim-script``), qui absorbe déjà
     l'essentiel (casse, espaces, « messier » pour « M ») ;
  2. si cela ne donne rien, des variantes locales sont essayées, toutes en un seul appel ;
  3. en dernier ressort, joker insensible à la casse (``sim-id``), puis fouille des identifiants par
     sous-chaîne (TAP/ADQL, lente : ~5 s).

Pièges mesurés de l'API (à relire avant d'y toucher) :
  * quand rien n'est trouvé, la réponse de ``sim-script`` **réémet le script** : on ne lit que la section
    qui suit ``::data:`` ;
  * le joker ne marche qu'en encadrement ``*…*`` ;
  * ADQL n'a ni ILIKE, ni LOWER() : LIKE distingue la casse, d'où trois variantes de casse ;
  * homonymes : « GN-z11 » (z = 10,6) ≠ « GNz11 » (catalogue GNZ, z = 0,053) ; « NGC 6888 » est résolu en
    l'étoile Wolf-Rayet HD 192163 : l'identifiant retenu est donc **toujours** affiché.
"""
from __future__ import annotations

import re
import unicodedata
import urllib.parse
from dataclasses import dataclass, field

from . import reseau, sources

TIMEOUT = 8.0
TIMEOUT_TAP = 15.0
MAX_CANDIDATES = 15
MIN_SUBSTRING_LEN = 5


class SimbadError(reseau.ServiceInjoignable):
    """SIMBAD est injoignable ou répond de travers."""


def hote() -> str:
    return (sources.valeur('simbad.base') or 'https://simbad.u-strasbg.fr/simbad').rstrip('/')


@dataclass
class SimbadObject:
    """Un objet renvoyé par SIMBAD."""

    name: str
    otype: str = ""
    redshift: float | None = None
    ra: float | None = None
    dec: float | None = None
    matched: str = ""          # identifiant qui a effectivement répondu
    aliases: list[str] = field(default_factory=list)

    def label(self) -> str:
        bits = [self.name]
        if self.otype:
            bits.append(f"({self.otype})")
        if self.redshift is not None:
            bits.append(f"z = {self.redshift:g}")
        return "  ".join(bits)


# --------------------------------------------------------------------------
# Normalisation et variantes de noms
# --------------------------------------------------------------------------

_CATALOGUES = {
    "messier": "M", "m": "M",
    "ngc": "NGC", "ic": "IC", "ugc": "UGC", "ugca": "UGCA",
    "pgc": "PGC", "leda": "LEDA", "eso": "ESO", "arp": "Arp",
    "abell": "ACO", "aco": "ACO", "sh2": "SH2", "sh": "SH2",
    "ldn": "LDN", "lbn": "LBN", "barnard": "Barnard", "b": "Barnard",
    "caldwell": "C", "collinder": "Cr", "melotte": "Mel",
    "hd": "HD", "hip": "HIP", "hr": "HR", "gj": "GJ", "sao": "SAO",
    "3c": "3C", "4c": "4C", "pks": "PKS", "qso": "QSO",
    "sdss": "SDSS", "2mass": "2MASS", "wise": "WISE", "iras": "IRAS",
    "mrk": "Mrk", "markarian": "Mrk", "vv": "VV", "hcg": "HCG",
}

_ACCENTS = str.maketrans("", "", "̧̀́̂̃̈̊")


def _strip_accents(text: str) -> str:
    return unicodedata.normalize("NFD", text).translate(_ACCENTS)


def flatten(text: str) -> str:
    """Réduit un nom à ses lettres et chiffres, en minuscules (« M 31 », « m31 », « M-31 » → « m31 »)."""
    return re.sub(r"[^a-z0-9]", "", _strip_accents(text).lower())


def name_variants(raw: str) -> list[str]:
    """Formes successives à essayer, de la plus fidèle à la plus retravaillée."""
    cleaned = _strip_accents(raw).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return []

    out: list[str] = [cleaned]

    def add(candidate: str) -> None:
        candidate = candidate.strip()
        if candidate and candidate not in out:
            out.append(candidate)

    add(cleaned.replace("-", " ").replace("_", " "))
    add(re.sub(r"[\s_]+", "", cleaned))
    add(re.sub(r"([A-Za-z])(\d)", r"\1 \2", cleaned))        # ngc224 -> ngc 224
    add(re.sub(r"([A-Za-z])[\s_-]+(\d)", r"\1\2", cleaned))   # ngc 224 -> ngc224

    match = (re.match(r"^([A-Za-z][A-Za-z0-9]*)[\s_-]*(.*)$", cleaned)
             or re.match(r"^(\d+[A-Za-z]+)[\s_-]*(.*)$", cleaned))
    if match:
        head, tail = match.group(1).lower(), match.group(2).strip()
        expanded = _CATALOGUES.get(head)
        if expanded and tail:
            add(f"{expanded} {tail}")
            add(f"{expanded}{tail}")
    match = re.match(r"^([A-Za-z]+)(\d.*)$", re.sub(r"[\s_-]+", "", cleaned))
    if match:
        expanded = _CATALOGUES.get(match.group(1).lower())
        if expanded:
            add(f"{expanded} {match.group(2)}")

    add(cleaned.upper())
    return out[:10]


# --------------------------------------------------------------------------
# Accès réseau
# --------------------------------------------------------------------------

def _fetch(url: str, timeout: float) -> str:
    try:
        return reseau.lire_texte(url, delai=timeout)
    except reseau.ServiceInjoignable as exc:
        raise SimbadError(str(exc)) from exc


def _as_float(text: str) -> float | None:
    text = (text or "").strip()
    if not text or text in {"~", "--"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


_COLUMNS = "%IDLIST(1)\t%OTYPE(V)\t%RV(Z)\t%COO(d;A)\t%COO(d;D)"
_SCRIPT_FORMAT = 'format object f1 "%s"\n' % _COLUMNS
_SCRIPT_FORMAT_FULL = 'format object f1 "%s\t%%IDLIST[%%*,]"\n' % _COLUMNS


def _data_lines(payload: str) -> list[str]:
    """Lignes de la section de données d'une réponse sim-script (le script réémis est ignoré)."""
    marker = payload.find("::data:")
    if marker < 0:
        return []
    body = payload[marker:].split("\n", 1)[-1]
    out = []
    for line in body.splitlines():
        line = line.rstrip()
        if not line.strip() or line.startswith(":") or "\t" not in line:
            continue
        if line.lstrip().startswith(("format ", "query ", "!!", "error")):
            continue
        out.append(line)
    return out


def _parse_script(payload: str) -> list[SimbadObject]:
    found: list[SimbadObject] = []
    for line in _data_lines(payload):
        cells = (line.split("\t") + [""] * 6)[:6]
        name = cells[0].strip()
        if not name:
            continue
        found.append(SimbadObject(
            name=name, otype=cells[1].strip(), redshift=_as_float(cells[2]),
            ra=_as_float(cells[3]), dec=_as_float(cells[4]), matched=name,
            aliases=[a.strip() for a in cells[5].split(",") if a.strip()],
        ))
    return found


def _script_url(script: str) -> str:
    return f"{hote()}/sim-script?" + urllib.parse.urlencode({"script": script})


def _query_ids(identifiers: list[str], timeout: float) -> list[SimbadObject]:
    identifiers = [i for i in identifiers if i.strip()]
    if not identifiers:
        return []
    header = _SCRIPT_FORMAT_FULL if len(identifiers) == 1 else _SCRIPT_FORMAT
    script = header + "".join(f"query id {i}\n" for i in identifiers)
    return _parse_script(_fetch(_script_url(script), timeout))


_OBJECT_LINE = re.compile(r"^Object\s+(.+?)\s+---", re.M)
_TABLE_LINE = re.compile(r"^\s*\d+\s*\|\s*(\S[^|]*?)\s*\|", re.M)


def _wildcard_ids(name: str, timeout: float) -> list[str]:
    """Identifiants contenant le nom demandé, casse indifférente (joker ``*…*``)."""
    if len(flatten(name)) < MIN_SUBSTRING_LEN:
        return []
    url = f"{hote()}/sim-id?" + urllib.parse.urlencode({
        "Ident": f"*{name}*", "NbIdent": "wild", "output.format": "ASCII", "output.max": str(MAX_CANDIDATES)})
    payload = _fetch(url, timeout)
    ids = _OBJECT_LINE.findall(payload) or _TABLE_LINE.findall(payload)
    return [i.strip() for i in ids[:MAX_CANDIDATES] if i.strip()]


_TAP_QUERY = (
    "SELECT TOP {n} b.main_id, o.otype_longname, b.rvz_redshift, b.ra, b.dec, i.id "
    "FROM ident AS i JOIN basic AS b ON i.oidref = b.oid "
    "LEFT JOIN otypedef AS o ON b.otype = o.otype "
    "WHERE {where}"
)


def _like_patterns(name: str) -> list[str]:
    """Motifs LIKE couvrant la casse (ADQL n'offre ni ILIKE ni LOWER) ; séparateurs → « % »."""
    core = re.sub(r"[\s_-]+", "%", name.strip())
    core = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])|(?<=[a-z])(?=[A-Z])", "%", core).replace("%%", "%")
    forms: list[str] = []
    for form in (core, core.upper(), core.title()):
        if form and form not in forms:
            forms.append(form)
    return ["%" + f + "%" for f in forms[:3]]


def _tap_search(name: str, timeout: float) -> list[SimbadObject]:
    if len(flatten(name)) < MIN_SUBSTRING_LEN:
        return []
    patterns = _like_patterns(name)
    where = " OR ".join("i.id LIKE '%s'" % p.replace("'", "''") for p in patterns)
    query = _TAP_QUERY.format(n=MAX_CANDIDATES * 2, where="(%s)" % where)
    url = f"{hote()}/sim-tap/sync?" + urllib.parse.urlencode({
        "request": "doQuery", "lang": "adql", "format": "text",
        "maxrec": str(MAX_CANDIDATES * 2), "query": query})
    payload = _fetch(url, timeout)
    target = flatten(name)
    found: list[SimbadObject] = []
    for line in payload.splitlines()[2:]:
        cells = [c.strip().strip('"') for c in line.split("|")]
        if len(cells) < 6 or not cells[0]:
            continue
        if target not in flatten(cells[5]):
            continue
        found.append(SimbadObject(name=cells[0], otype=cells[1], redshift=_as_float(cells[2]),
                                  ra=_as_float(cells[3]), dec=_as_float(cells[4]), matched=cells[5]))
    return found


def _merge(*groups: list[SimbadObject]) -> list[SimbadObject]:
    out: dict[str, SimbadObject] = {}
    for group in groups:
        for obj in group:
            existing = out.get(obj.name)
            if existing is None:
                out[obj.name] = obj
            elif obj.matched and obj.matched not in existing.aliases:
                existing.aliases.append(obj.matched)
    return list(out.values())[:MAX_CANDIDATES]


def _match_rank(query: str, obj: SimbadObject) -> int:
    asked = flatten(query)
    if not asked:
        return 3
    best = 3
    for known in (obj.name, obj.matched, *obj.aliases):
        flat = flatten(known)
        if not flat:
            continue
        if flat == asked:
            return 0
        if flat.startswith(asked):
            best = min(best, 1)
        elif asked in flat or flat in asked:
            best = min(best, 2)
    return best


def resolve(query: str, timeout: float = TIMEOUT, approfondir: bool = True) -> tuple[list[SimbadObject], str]:
    """Cherche un objet à partir d'un nom saisi librement : (candidats, forme retenue).

    Aucune entrée : introuvable ; une seule : réponse certaine (le résolveur a reconnu le nom) ; plusieurs :
    à l'utilisateur de choisir.  Lève SimbadError si SIMBAD est injoignable.  `approfondir=False` s'arrête
    après les deux premiers niveaux (un ou deux appels rapides).
    """
    variants = name_variants(query)
    if not variants:
        return [], ""
    exact = variants[0]
    direct = _merge(_query_ids([exact], timeout))
    if direct:
        return direct, exact
    found = _merge(_query_ids(variants[1:], timeout))
    if found or not approfondir:
        return found, exact
    try:
        ids = _wildcard_ids(exact, timeout)
        found = _merge(_query_ids(ids, timeout) if ids else [])
    except SimbadError:
        found = []
    if not found:
        found = _merge(_tap_search(exact, max(timeout, TIMEOUT_TAP)))
    found.sort(key=lambda o: _match_rank(exact, o))
    return found, exact


# --------------------------------------------------------------------------
# Fiche détaillée (une seule requête sim-script)
# --------------------------------------------------------------------------

# Champs de la fiche, séparés par des tabulations.  La mesure de distance préférée (%MEASLIST(distance;|F))
# contient elle-même des « | » : elle est placée en dernier.
_FICHE = ("%IDLIST(1)\t%OTYPE(S)\t%OTYPE(V)\t%COO(d;A)\t%COO(d;D)\t%COO(s;A)\t%COO(s;D)\t%PLX(V)\t%PLX(E)\t"
          "%RV(T)\t%RV(V)\t%RV(Z)\t%RV(E)\t%RV(Q)\t%FLUXLIST(U,B,V,R,I,G,J,H,K;N=F,)\t%DIM(X)\t%DIM(Y)\t%DIM(A)\t"
          "%SP(S)\t%MT(M)\t%IDLIST[%*,]\t%MEASLIST(distance;|F)")
_FICHE_CHAMPS = ('nom', 'otype', 'type', 'ra', 'dec', 'ra_s', 'dec_s', 'plx', 'plx_err', 'rv_type', 'vr', 'z',
                 'rv_err', 'rv_qualite', 'flux', 'dim_x', 'dim_y', 'dim_angle', 'sp', 'morpho', 'ids', 'distance')
_NOMBRES = {'ra', 'dec', 'plx', 'plx_err', 'vr', 'z', 'rv_err', 'dim_x', 'dim_y', 'dim_angle'}


def _lire_distance(texte: str) -> dict | None:
    """« 0.242   kpc |  -0.048      +0.048   |  method |2010ApJ...714.1096S » → dict."""
    morceaux = [m.strip() for m in texte.split('|')]
    if not morceaux or not morceaux[0]:
        return None
    m = re.match(r'^([-+0-9.eE]+)\s*([A-Za-z]*)', morceaux[0])
    if not m:
        return None
    d = {'valeur': float(m.group(1)), 'unite': m.group(2) or 'pc', 'moins': None, 'plus': None,
         'methode': '', 'reference': ''}
    if len(morceaux) > 1:
        err = re.findall(r'[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?', morceaux[1])
        if len(err) >= 2:
            d['moins'], d['plus'] = abs(float(err[0])), abs(float(err[1]))
    if len(morceaux) > 2:
        d['methode'] = morceaux[2]
    if len(morceaux) > 3:
        d['reference'] = morceaux[3]
    return d


def lire_fiche(payload: str) -> dict | None:
    """Analyse la réponse de ``fiche()`` (premier objet trouvé)."""
    for line in _data_lines(payload):
        cells = line.split("\t")
        if len(cells) < len(_FICHE_CHAMPS) - 1 or not cells[0].strip():
            continue
        cells = (cells + [''] * len(_FICHE_CHAMPS))[:len(_FICHE_CHAMPS)]
        f = {}
        for k, v in zip(_FICHE_CHAMPS, cells):
            f[k] = _as_float(v) if k in _NOMBRES else v.strip()
        f['nom'] = re.sub(r'\s+', ' ', f['nom'])
        flux = {}
        for paire in f['flux'].split(','):
            if '=' in paire:
                bande, val = paire.split('=', 1)
                v = _as_float(val)
                if v is not None:
                    flux[bande.strip()] = v
        f['flux'] = flux
        f['ids'] = [re.sub(r'\s+', ' ', i.strip()) for i in f['ids'].split(',') if i.strip()]
        f['distance'] = _lire_distance(f['distance'])
        for k in ('sp', 'morpho', 'rv_type', 'rv_qualite', 'otype', 'type'):
            if f[k] == '~':
                f[k] = ''
        return f
    return None


def fiche(identifiants: list[str], timeout: float = TIMEOUT) -> dict | None:
    """Fiche du premier identifiant reconnu parmi `identifiants` (essayés dans l'ordre, un seul appel)."""
    ids = []
    for i in identifiants:
        i = re.sub(r'\s+', ' ', (i or '').strip())
        if i and i not in ids:
            ids.append(i)
    if not ids:
        return None
    script = 'format object f1 "%s"\n' % _FICHE + ''.join('query id %s\n' % i for i in ids[:12])
    f = lire_fiche(_fetch(_script_url(script), timeout))
    return f
