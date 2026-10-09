"""Métadonnées d'instrument que PixInsight (ImageSolver, WBPP) et N.I.N.A. lisent : focale, pixel, binning.

Vérifié dans le code de PixInsight (PJSR, gitlab.com/pixinsight/PJSR) :
  * include/pjsr/astrometry/AstrometricMetadata.js (l. 103-106, 352-355) : ImageSolver lit les propriétés XISF
    ``Instrument:Telescope:FocalLength`` (mètres) et ``Instrument:Sensor:XPixelSize`` (µm), sinon les mots-clés
    FOCALLEN (mm) et XPIXSZ (µm) ; AUCUNE multiplication par XBINNING : XPIXSZ est le pixel EFFECTIF, binning
    compris (T120 en binning 2 : 27 µm) — c'est aussi la définition de la spécification XISF (révision 1,
    « Instrument:Sensor:XPixelSize … must account for pixel binning »).
  * src/scripts/BatchPreprocessing/BPP-Solver.js (l. 100-145) : WBPP résout le MASTER intégré, en partant des
    valeurs de son panneau « Astrometric solution » (gardées d'une session à l'autre : celles du dernier
    instrument), remplacées par les métadonnées trouvées dans le master s'il en a.

Écrit ici (nouveaux fichiers, et `coupole ohp metadonnees --reecrire` pour les fichiers existants, pixels
intacts) : FOCALLEN cohérent avec l'échelle MESURÉE (f = 206 264,806 × XPIXSZ / PIXSCALE, ancienne valeur en
HISTORY), et les propriétés XISF Instrument:Telescope:FocalLength, Instrument:Sensor:XPixelSize/YPixelSize,
Instrument:Camera:XBinning/YBinning, Instrument:Camera:Name, Instrument:Telescope:Aperture (T120 : 1,20 m, le
diamètre qui lui donne son nom ; autres télescopes : seulement si l'en-tête le donne, APTDIA en mm).
"""
from __future__ import annotations

import csv
import io
import os

ARCSEC_PAR_RAD_MM = 206.264806          # ″ par radian / 1000 : f (mm) = 206,264806 × pixel (µm) / échelle (″ px⁻¹)
ECART_FOCALE_MM = 0.5                   # en deçà, FOCALLEN est gardé tel quel


def _val(mots, nom):
    for n, v, _c in mots:
        if n == nom:
            v = (v or '').strip().strip("'").strip()
            try:
                return float(v)
            except ValueError:
                return v or None
    return None


def _num(x):
    return x if isinstance(x, float) else None


def instrument(mots, props: dict | None = None) -> dict:
    """Ce qu'il faut saisir dans PixInsight ou N.I.N.A., lu dans l'en-tête : {'instrument', 'focale_mm',
    'focale_entete_mm', 'pixel_um', 'pixel_y_um', 'binning', 'echelle', 'champ_arcmin', 'ra', 'dec'} (None si
    inconnu).  La focale donnée est celle qui correspond à l'échelle mesurée."""
    props = props or {}
    xpix = _num(_val(mots, 'XPIXSZ'))
    ypix = _num(_val(mots, 'YPIXSZ')) or xpix
    xbin = _num(_val(mots, 'XBINNING'))
    ybin = _num(_val(mots, 'YBINNING')) or xbin
    ech = _num(_val(mots, 'PIXSCALE'))
    foc = _num(_val(mots, 'FOCALLEN'))
    f_mes = ARCSEC_PAR_RAD_MM * xpix / ech if xpix and ech else None
    nx, ny = _num(_val(mots, 'NAXIS1')), _num(_val(mots, 'NAXIS2'))
    tel = _val(mots, 'TELESCOP') or props.get('Instrument:Telescope:Name') or ''
    cam = _val(mots, 'INSTRUME') or ''
    return {'instrument': ' — '.join(x for x in (str(tel).strip(), str(cam).strip()) if x) or None,
            'telescope': str(tel).strip() or None, 'camera': str(cam).strip() or None,
            'focale_mm': f_mes or foc, 'focale_entete_mm': foc, 'pixel_um': xpix, 'pixel_y_um': ypix,
            'binning': (int(xbin), int(ybin or xbin)) if xbin else None, 'echelle': ech,
            'champ_arcmin': (nx * ech / 60, ny * ech / 60) if nx and ny and ech else None,
            'ra': _num(_val(mots, 'RA')), 'dec': _num(_val(mots, 'DEC'))}


def completer(mots, proprietes, histoire, apertures=None):
    """Complète en place : FOCALLEN cohérent avec l'échelle mesurée (ancienne valeur en HISTORY via `histoire`,
    une fonction (nom, ancienne valeur) → texte), et les propriétés Instrument:* (liste [(id, type, valeur)]).
    Rend la liste des changements (noms)."""
    changes = []
    inf = instrument(mots)
    xpix, ech, foc = inf['pixel_um'], inf['echelle'], inf['focale_entete_mm']
    f_mes = ARCSEC_PAR_RAD_MM * xpix / ech if xpix and ech else None
    if f_mes and (foc is None or abs(f_mes - foc) > ECART_FOCALE_MM):
        valeur = '%.1f' % f_mes
        for i, (n, v, c) in enumerate(mots):
            if n == 'FOCALLEN':
                mots[i] = ('FOCALLEN', valeur, c)
                mots.append(('HISTORY', '', histoire('FOCALLEN', v)))
                break
        else:
            mots.append(('FOCALLEN', valeur, '[mm] focal length matching the measured scale'))
        changes.append('FOCALLEN')
    focale = f_mes or foc
    voulues = []
    if focale:
        voulues.append(('Instrument:Telescope:FocalLength', 'Float32', round(focale / 1000.0, 6)))
    if xpix:
        voulues += [('Instrument:Sensor:XPixelSize', 'Float32', xpix),
                    ('Instrument:Sensor:YPixelSize', 'Float32', inf['pixel_y_um'] or xpix)]
    if inf['binning']:
        voulues += [('Instrument:Camera:XBinning', 'Int32', inf['binning'][0]),
                    ('Instrument:Camera:YBinning', 'Int32', inf['binning'][1])]
    if inf['camera']:
        voulues.append(('Instrument:Camera:Name', 'String', inf['camera']))
    apt = _num(_val(mots, 'APTDIA'))
    nom_tel = ' '.join(str(v) for i_, t_, v in proprietes if i_ == 'Instrument:Telescope:Name') + ' ' + \
        str(inf['telescope'] or '')
    if apt:
        voulues.append(('Instrument:Telescope:Aperture', 'Float32', apt / 1000.0))
    elif 'T120' in nom_tel:
        voulues.append(('Instrument:Telescope:Aperture', 'Float32', 1.2))
    index = {pid: k for k, (pid, _t, _v) in enumerate(proprietes)}
    for pid, typ, val in voulues:
        if pid in index:
            ancien = proprietes[index[pid]]
            try:
                egal = abs(float(ancien[2]) - float(val)) < 1e-6 if typ != 'String' else str(ancien[2]) == str(val)
            except (TypeError, ValueError):
                egal = False
            if not egal:
                proprietes[index[pid]] = (pid, typ, val)
                changes.append(pid)
        else:
            proprietes.append((pid, typ, val))
            changes.append(pid)
    return changes


# ------------------------------------------------------------------ fichiers existants
def reecrire(chemin, langue='fr', simuler=False) -> list:
    """Complète les métadonnées d'un fichier converti (XISF, FITS, .fits.fz) SANS toucher aux pixels ; relit et
    vérifie (pixels identiques, en-tête attendu).  Rend la liste des changements ([] : rien à faire)."""
    from ...core.i18n import tr
    import numpy as np

    def histoire(nom, ancien):
        return tr('hdr_origine', langue, nom=nom, valeur=ancien, raison=' (%s)' % tr('hdr_raison_focale_mesuree', langue))
    bas = str(chemin).lower()
    if bas.endswith('.xisf'):
        from ...core import xisf
        e = xisf.lire_entete(chemin)
        mots = list(e['mots_cles'])
        props = [(pid, e['types'].get(pid) or 'String', v) for pid, v in e['proprietes'].items()]
        changes = completer(mots, props, histoire)
        if not changes or simuler:
            return changes
        avant, _ = xisf.lire(chemin)
        xisf.reecrire_entete(chemin, mots, props)
        apres, inf = xisf.lire(chemin)
        if avant.dtype != apres.dtype or not np.array_equal(avant, apres, equal_nan=avant.dtype.kind == 'f'):
            raise ValueError('pixels changed while rewriting the header')
        if [tuple(m) for m in inf['mots_cles']] != [(xisf.xml_texte(a), xisf.xml_texte(b), xisf.xml_texte(c))
                                                    for a, b, c in mots]:
            raise ValueError('keywords read back differ')
        return changes
    if bas.endswith(('.fits', '.fit', '.fts', '.fits.fz')):
        from astropy.io import fits
        ext = 1 if bas.endswith('.fz') else 0
        with fits.open(chemin, memmap=False) as hd:
            h = hd[ext].header
            mots = [(k, repr(h[k]) if isinstance(h[k], str) else str(h[k]), h.comments[k]) for k in h
                    if k not in ('HISTORY', 'COMMENT', '')]
            avant = np.array(hd[ext].data)
        props = []
        changes = [c for c in completer(mots, props, histoire) if c == 'FOCALLEN']
        if not changes or simuler:
            return changes
        nouveau = next(v for n, v, _c in mots if n == 'FOCALLEN')
        with fits.open(chemin, mode='update', memmap=False) as hd:
            h = hd[ext].header
            ancien = h.get('FOCALLEN')
            h['FOCALLEN'] = (float(nouveau), h.comments['FOCALLEN'] if 'FOCALLEN' in h else '[mm] focal length')
            if ancien is not None:
                h.add_history(histoire('FOCALLEN', ancien))
        with fits.open(chemin, memmap=False) as hd:
            apres = np.array(hd[ext].data)
        if avant.dtype != apres.dtype or not np.array_equal(avant, apres, equal_nan=avant.dtype.kind == 'f'):
            raise ValueError('pixels changed while rewriting the header')
        return changes
    return []


def instrument_fichier(chemin) -> dict | None:
    """`instrument()` d'un fichier converti, d'après son en-tête seul (XISF : premiers Ko ; FITS : en-tête)."""
    try:
        bas = str(chemin).lower()
        if bas.endswith('.xisf'):
            from ...core import xisf
            e = xisf.lire_entete(chemin)
            return instrument(e['mots_cles'], e['proprietes'])
        from astropy.io import fits
        h = fits.getheader(chemin, 1 if bas.endswith('.fz') else 0)
        return instrument([(k, repr(h[k]) if isinstance(h[k], str) else str(h[k]), '') for k in h
                           if k not in ('HISTORY', 'COMMENT', '')])
    except Exception:
        return None


def _base_etat(dossier):
    p = os.path.abspath(str(dossier))
    for _ in range(8):
        if os.path.isfile(os.path.join(p, '_traitement', 'etat.sqlite')):
            return os.path.join(p, '_traitement', 'etat.sqlite')
        parent = os.path.dirname(p)
        if parent == p:
            return None
        p = parent
    return None


def maj_etat(dossier, valeurs: dict) -> int:
    """Note focale, pixel et binning dans la base d'état de la sortie (par nom de fichier) : le prochain rangement
    (`coupole ohp ranger`) les écrit dans LOT.txt.  Rend le nombre d'images mises à jour (0 sans base)."""
    import json
    import sqlite3
    chemin = _base_etat(dossier)
    if not chemin or not valeurs:
        return 0
    n = 0
    from ...core import base_partagee
    base = base_partagee.BasePartagee(chemin)          # partage réseau : base de travail locale, recopiée
    try:
        db = sqlite3.connect(base.ouvrir(), timeout=5)
        try:
            maj = []
            for i, info in db.execute("SELECT id, info FROM images WHERE statut='ok'"):
                try:
                    d = json.loads(info or '{}')
                except ValueError:
                    continue
                v = valeurs.get(os.path.basename((d.get('final') or '').replace('\\', '/')))
                if not v:
                    continue
                nouveau = {'focale_mm': round(v['focale_mm'], 1) if v.get('focale_mm') else None,
                           'pixel_um': v.get('pixel_um'), 'binning': list(v['binning']) if v.get('binning') else None}
                if any(d.get(k) != val for k, val in nouveau.items()):
                    d.update(nouveau)
                    maj.append((json.dumps(d, ensure_ascii=False), i))
            if maj:
                db.executemany('UPDATE images SET info=? WHERE id=?', maj)
                db.commit()
            n = len(maj)
            base.fermer(db)
        finally:
            db.close()
    except (sqlite3.Error, OSError, base_partagee.Divergence):
        return 0
    return n


def reecrire_dossier(dossier, langue='fr', simuler=False, rapporter=None, arret=None) -> dict:
    """Tous les fichiers convertis d'un dossier (sous-dossiers compris) ; journal dans
    ``<dossier>/_traitement/metadonnees.csv`` (fichier ; changements ; erreur).  Rend les comptes."""
    from ...core import parcours
    from ...core.config import ecrire_atomique
    lots = parcours.lister(dossier, ('.xisf', '.fits', '.fit', '.fts', '.fits.fz'))
    fichiers = [f for v in lots.values() for f in v]
    out = {'fichiers': len(fichiers), 'modifies': 0, 'inchanges': 0, 'erreurs': 0, 'base': 0}
    valeurs = {}
    journal = io.StringIO()
    w = csv.writer(journal, delimiter=';')
    w.writerow(['fichier', 'changements', 'erreur'])
    for k, f in enumerate(fichiers):
        if arret is not None and arret.is_set():
            break
        try:
            ch = reecrire(f, langue, simuler)
            out['modifies' if ch else 'inchanges'] += 1
            if not simuler:
                v = instrument_fichier(f)
                if v and v.get('pixel_um'):
                    valeurs[os.path.basename(f)] = v
            w.writerow([os.path.relpath(f, dossier), ' '.join(ch), ''])
        except Exception as e:                       # un fichier abîmé n'arrête pas les autres
            out['erreurs'] += 1
            w.writerow([os.path.relpath(f, dossier), '', '%s: %s' % (type(e).__name__, e)])
        if rapporter:
            rapporter(k + 1, len(fichiers))
    if not simuler:
        out['base'] = maj_etat(dossier, valeurs)
        try:
            os.makedirs(os.path.join(dossier, '_traitement'), exist_ok=True)
            ecrire_atomique(os.path.join(dossier, '_traitement', 'metadonnees.csv'), journal.getvalue(), 'utf-8-sig')
        except OSError:
            pass
    return out
