"""Modèle de données générique : images, spectres 1D, séries temporelles, tables.

Rien n'y suppose une image 2D.  Un fichier donne une liste de ``Donnee`` (une
par extension FITS utile, ou une pour un CSV).  Les lecteurs sont enregistrés
par extension de fichier ; un module peut en ajouter (voir CONTRIBUTING.md,
« Ajouter un format ») :

    from coupole.core import donnees
    donnees.enregistrer_lecteur(('.rad',), lire_rad, 'SRT .rad')

Conversions spectrales (exactes, sans hypothèse cachée) :
  vitesse radio  v = c (1 − f / f0)   (convention « radio » de la FITS WCS, Greisen et al. 2006)
  f0 lue dans RESTFRQ / RESTFREQ, sinon fournie par l'utilisateur (défaut proposé : raie H I,
  1 420,405 751 768 MHz).  Le référentiel de la vitesse est celui de l'axe des fréquences
  (SPECSYS : TOPOCENT, LSRK...) ; Coupole ne fait aucune correction de référentiel implicite.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

C_KM_S = 299792.458
HI_HZ = 1420405751.768            # raie 21 cm de l'hydrogène neutre (Hz)

GENRES = ('image', 'spectre', 'serie', 'table')


@dataclass
class Donnee:
    genre: str
    titre: str
    source: str = ''
    x: np.ndarray | None = None
    y: np.ndarray | None = None
    nom_x: str = ''
    unite_x: str = ''
    nom_y: str = ''
    unite_y: str = ''
    image: np.ndarray | None = None
    table: dict = field(default_factory=dict)
    entete: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    def resume(self) -> dict:
        d = {'genre': self.genre, 'titre': self.titre, 'source': self.source, 'meta': self.meta}
        if self.x is not None:
            d.update(n=int(len(self.x)), x=[float(np.nanmin(self.x)), float(np.nanmax(self.x))],
                     nom_x=self.nom_x, unite_x=self.unite_x, nom_y=self.nom_y, unite_y=self.unite_y)
        if self.image is not None:
            d['forme'] = list(self.image.shape)
        if self.table:
            d['colonnes'] = list(self.table)
        return d


_lecteurs: list[tuple[tuple, object, str]] = []


def enregistrer_lecteur(extensions, fonction, nom: str):
    _lecteurs.append((tuple(e.lower() for e in extensions), fonction, nom))


def formats() -> list[tuple[str, str]]:
    return [(nom, ' '.join(ext)) for ext, _, nom in _lecteurs]


def lire(chemin) -> list[Donnee]:
    p = str(chemin)
    bas = p.lower()
    for ext, f, _ in sorted(_lecteurs, key=lambda t: -max(len(e) for e in t[0])):
        if any(bas.endswith(e) for e in ext):
            return f(p)
    raise ValueError('unknown format: %s' % Path(p).suffix)


# ======================================================================== unités et axes spectraux
_FACTEURS_HZ = {'hz': 1.0, 'khz': 1e3, 'mhz': 1e6, 'ghz': 1e9}
_FACTEURS_KMS = {'m/s': 1e-3, 'km/s': 1.0, 'kms-1': 1.0, 'km s-1': 1.0, 'ms-1': 1e-3, 'm s-1': 1e-3}


def en_hz(valeurs, unite: str):
    f = _FACTEURS_HZ.get((unite or 'hz').strip().lower())
    if f is None:
        raise ValueError('not a frequency unit: %r' % unite)
    return np.asarray(valeurs, dtype=float) * f


def vitesse_radio(freq_hz, f0_hz=HI_HZ):
    """km/s, convention radio : v = c (1 − f/f0)."""
    return C_KM_S * (1.0 - np.asarray(freq_hz, dtype=float) / float(f0_hz))


def frequence_depuis_vitesse(v_kms, f0_hz=HI_HZ):
    return float(f0_hz) * (1.0 - np.asarray(v_kms, dtype=float) / C_KM_S)


def axe_wcs_1d(h, n, axe=1):
    """Valeurs de l'axe `axe` (1-based) d'après CRVAL/CDELT (ou CDi_i)/CRPIX, linéaire."""
    crval = float(h.get('CRVAL%d' % axe, 0.0))
    cdelt = h.get('CDELT%d' % axe, h.get('CD%d_%d' % (axe, axe), 1.0))
    crpix = float(h.get('CRPIX%d' % axe, 1.0))
    i = np.arange(1, n + 1, dtype=float)
    return crval + (i - crpix) * float(cdelt)


def _genre_axe(ctype: str, unite: str) -> str:
    c = (ctype or '').upper()
    u = (unite or '').lower()
    if c.startswith('FREQ') or u in _FACTEURS_HZ:
        return 'freq'
    if c.startswith(('VRAD', 'VELO', 'VOPT', 'VELO-LSR', 'VLSR')) or u in _FACTEURS_KMS:
        return 'vitesse'
    if c.startswith(('WAVE', 'AWAV')) or u in ('angstrom', 'nm', 'um', 'm'):
        return 'longueur_onde'
    return ''


# ======================================================================== FITS
def lire_fits(chemin) -> list[Donnee]:
    import warnings
    from astropy.io import fits
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with fits.open(chemin, memmap=True) as hd:
            for k, h in enumerate(hd):
                hdr = h.header
                ent = {c: hdr[c] for c in hdr if c not in ('COMMENT', 'HISTORY', '')}
                nom = (hdr.get('EXTNAME') or ('HDU %d' % k)).strip()
                if isinstance(h, (fits.BinTableHDU, fits.TableHDU)):
                    out.append(_depuis_table({c: np.asarray(h.data[c]) for c in h.columns.names
                                              if np.asarray(h.data[c]).ndim == 1},
                                             {c.name: (c.unit or '') for c in h.columns}, nom, chemin, ent))
                    continue
                data = getattr(h, 'data', None)
                if data is None:
                    continue
                a = np.asarray(data)
                axes_utiles = [i for i, n in enumerate(a.shape) if n > 1]
                if len(axes_utiles) == 1:
                    # spectre 1D (éventuellement dans un cube radio 1 x 1 x N) : axe FITS = ndim - indice numpy
                    i_np = axes_utiles[0]
                    axe = a.ndim - i_np
                    y = a.reshape(-1).astype(float)
                    x = axe_wcs_1d(hdr, len(y), axe)
                    ctype, unite = str(hdr.get('CTYPE%d' % axe, '')), str(hdr.get('CUNIT%d' % axe, ''))
                    g = _genre_axe(ctype, unite)
                    meta = {'axe': g, 'ctype': ctype, 'specsys': str(hdr.get('SPECSYS', '')),
                            'restfreq_hz': float(hdr.get('RESTFRQ', hdr.get('RESTFREQ', 0)) or 0) or None}
                    if g == 'freq' and not unite:
                        unite = 'Hz'
                    out.append(Donnee('spectre' if g else 'serie', nom, str(chemin), x=x, y=y, nom_x=ctype or 'x',
                                      unite_x=unite, nom_y=str(hdr.get('BTYPE', 'intensity')),
                                      unite_y=str(hdr.get('BUNIT', '')), entete=ent, meta=meta))
                elif len(axes_utiles) >= 2:
                    out.append(Donnee('image', nom, str(chemin), image=a, entete=ent,
                                      meta={'forme': list(a.shape)}))
    return out


# ======================================================================== tables (FITS ou CSV)
_TEMPS = re.compile(r'^(time|temps|mjd|jd|bjd|hjd|date|t|utc)\b', re.I)
_FREQ = re.compile(r'^(freq|frequency|fr[ée]quence|nu)\b', re.I)
_VIT = re.compile(r'^(v|vel|velo|velocity|vitesse|vlsr|vrad)\b', re.I)
_INT = re.compile(r'^(flux|intensity|intensit[ée]|power|puissance|ta|tb|temp|antenna|amplitude|mag|signal|counts)', re.I)


def _depuis_table(cols: dict, unites: dict, nom, chemin, ent) -> Donnee:
    num = {k: np.asarray(v, dtype=float) for k, v in cols.items() if _numerique(v)}
    x = y = None
    genre = 'table'
    meta = {}
    noms = list(num)
    cx = next((k for k in noms if _FREQ.match(k)), None)
    if cx:
        genre, meta['axe'] = 'spectre', 'freq'
    else:
        cx = next((k for k in noms if _VIT.match(k)), None)
        if cx:
            genre, meta['axe'] = 'spectre', 'vitesse'
        else:
            cx = next((k for k in noms if _TEMPS.match(k)), None)
            if cx:
                genre = 'serie'
    if cx:
        cy = next((k for k in noms if k != cx and _INT.match(k)), None) or next((k for k in noms if k != cx), None)
        if cy:
            x, y = num[cx], num[cy]
    d = Donnee(genre, nom, str(chemin), x=x, y=y, nom_x=cx or '', unite_x=unites.get(cx, '') if cx else '',
               nom_y=cy if x is not None else '', unite_y=unites.get(cy, '') if x is not None else '',
               table=num, entete=ent, meta=meta)
    if genre == 'spectre' and meta['axe'] == 'freq' and not d.unite_x:
        d.unite_x = _unite_dans_nom(cx) or ''
    if genre == 'spectre' and meta['axe'] == 'vitesse' and not d.unite_x:
        d.unite_x = _unite_dans_nom(cx) or ''
    return d


def _unite_dans_nom(nom: str) -> str:
    m = re.search(r'[\[(]\s*([A-Za-z/ \-0-9]+?)\s*[\])]', nom or '')
    return m.group(1) if m else ''


def _numerique(v) -> bool:
    try:
        a = np.asarray(v, dtype=float)
        return a.ndim == 1 and np.isfinite(a).any()
    except (TypeError, ValueError):
        return False


def lire_csv(chemin) -> list[Donnee]:
    txt = Path(chemin).read_text(encoding='utf-8-sig', errors='replace')
    lignes = [l for l in txt.splitlines() if l.strip() and not l.lstrip().startswith(('#', '%', '!'))]
    if not lignes:
        raise ValueError('empty file')
    try:
        dialecte = csv.Sniffer().sniff('\n'.join(lignes[:20]), delimiters=',;\t ')
        delim = dialecte.delimiter
    except csv.Error:
        delim = None
    lecteur = (csv.reader(io.StringIO('\n'.join(lignes)), delimiter=delim) if delim and delim != ' '
               else ([c for c in l.split()] for l in lignes))
    rangs = [[c.strip() for c in r if c.strip() != ''] for r in lecteur]
    rangs = [r for r in rangs if r]
    entete = None
    try:
        [float(c) for c in rangs[0]]
    except ValueError:
        entete = rangs[0]
        rangs = rangs[1:]
    n = max(len(r) for r in rangs)
    if entete and len(entete) != n and (not delim or delim == ' '):
        # en-tête séparé par des espaces mais noms avec espaces : « freq (MHz)  Ta (K) »
        brut = next(l for l in lignes if l.strip())
        entete = [c.strip() for c in re.split(r'\s{2,}|\t', brut.strip()) if c.strip()]
    noms = entete if entete and len(entete) == n else ['col%d' % (i + 1) for i in range(n)]
    cols = {}
    for i, nom in enumerate(noms):
        vals = []
        for r in rangs:
            try:
                vals.append(float(r[i].replace(',', '.') if delim != ',' else r[i]))
            except (ValueError, IndexError):
                vals.append(np.nan)
        cols[nom] = np.asarray(vals)
    d = _depuis_table(cols, {k: _unite_dans_nom(k) for k in cols}, Path(chemin).name, chemin, {})
    if d.x is None and len(cols) >= 2:                     # deux colonnes sans nom : x, y
        ks = list(cols)
        d.x, d.y, d.nom_x, d.nom_y, d.genre = cols[ks[0]], cols[ks[1]], ks[0], ks[1], 'serie'
    return [d]


enregistrer_lecteur(('.fits', '.fit', '.fts', '.fits.gz', '.fits.fz', '.fz'), lire_fits, 'FITS')
enregistrer_lecteur(('.csv', '.txt', '.dat', '.tsv'), lire_csv, 'CSV / texte')
