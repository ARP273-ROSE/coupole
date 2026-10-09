"""Rapport de qualité par lot : QUALITE.csv (une ligne par image) et QUALITE.txt (résumé FR puis EN)."""
from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np

from ...core.i18n import tr
from . import mesures

EXTENSIONS = ('.xisf', '.fits', '.fit', '.fts', '.fits.fz')
COLONNES = ['fichier', 'etoiles', 'fwhm_px', 'fwhm_arcsec', 'ellipticite', 'fond_adu', 'fond_adu_s', 'bruit_adu',
            'rsn', 'gradient_pct', 'residu_pct', 'satures', 'trainees', 'echantillonnage']


def fichiers(racine) -> dict:
    """{dossier de lot: [fichiers image]} ; un dossier = un lot (fichiers d'image au même niveau).

    Parcours parallèle (`core.parcours`) : sur un partage réseau, la lecture de chaque dossier est un aller-retour."""
    from ...core import parcours
    p = Path(racine)
    if p.is_file():
        return {str(p.parent): [str(p)]}
    if '_traitement' in p.parts:
        return {}
    return parcours.lister(p, EXTENSIONS)


def analyser_lot(images, progression=None, arret=None):
    lignes = []
    for k, f in enumerate(images):
        if arret is not None and arret.is_set():
            break
        try:
            a, ent = mesures.lire_image(f)
            r = mesures.analyser(a, ent)
            r['fichier'] = os.path.basename(f)
            del a
        except Exception as e:  # une image illisible n'arrête pas le lot
            r = {'fichier': os.path.basename(f), 'erreur': str(e)[:200]}
        lignes.append(r)
        if progression:
            progression(k + 1, len(images), r)
    return lignes


def _fmt(v, f='%.3g'):
    return '' if v is None else (f % v if isinstance(v, float) else str(v))


def resume(lignes, L) -> list[str]:
    ok = [l for l in lignes if l.get('fwhm_px')]
    t = lambda k, **kw: tr('qual_' + k, L, **kw)  # noqa: E731
    out = [t('resume_titre', n=len(lignes), mesurees=len(ok))]
    if not ok:
        return out + [t('resume_aucune')]
    fw = np.array([l['fwhm_px'] for l in ok])
    out.append(t('resume_fwhm', med='%.2f' % np.median(fw), mini='%.2f' % fw.min(), maxi='%.2f' % fw.max(),
                 arc=_fmt(np.median([l['fwhm_arcsec'] for l in ok if l.get('fwhm_arcsec')]) if any(
                     l.get('fwhm_arcsec') for l in ok) else None, '%.2f')))
    out.append(t('resume_ellipticite', med='%.3f' % np.median([l['ellipticite'] for l in ok])))
    out.append(t('resume_fond', fond='%.0f' % np.median([l['fond_adu'] for l in ok]),
                 bruit='%.1f' % np.median([l['bruit_adu'] for l in ok])))
    pires = sorted(ok, key=lambda l: -l['fwhm_px'])[:3]
    out.append(t('resume_pires', liste=', '.join('%s (%.2f px)' % (l['fichier'], l['fwhm_px']) for l in pires)))
    sat = sum(l.get('satures', 0) for l in ok)
    tr_ = [l['fichier'] for l in ok if l.get('trainees')]
    out.append(t('resume_satures', n=sat))
    if tr_:
        out.append(t('resume_trainees', liste=', '.join(tr_[:10])))
    ech = {l['echantillonnage'] for l in ok if l.get('echantillonnage')}
    out.append(t('resume_echantillonnage', v=', '.join(t('ech_' + e) for e in sorted(ech))))
    carte = [l['carte_fwhm'] for l in ok if l.get('carte_fwhm')]
    if carte:
        m = np.full((3, 3), np.nan)
        for j in range(3):
            for k in range(3):
                vals = [c[j][k] for c in carte if c[j][k] is not None]
                if vals:
                    m[j, k] = np.median(vals)
        out.append(t('resume_carte'))
        for j in range(3):
            out.append('    ' + '  '.join('%5.2f' % v if np.isfinite(v) else '   — ' for v in m[j]))
        out.append(t('resume_carte_limite'))
    out.append(t('resume_prudence'))
    return out


def ecrire(dossier, lignes, txt: bool = True):
    """QUALITE.csv (écriture atomique : jamais de fichier à moitié écrit, même appelé après chaque image) et,
    si `txt`, QUALITE.txt (résumé FR puis EN, écrit quand le lot est complet)."""
    import io
    from ...core.config import ecrire_atomique
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow(['%s (%s)' % (tr('qual_col_' + c, 'fr'), tr('qual_col_' + c, 'en')) for c in COLONNES])
    for l in lignes:
        w.writerow([_fmt(l.get(c), '%.4g') for c in COLONNES])
    ecrire_atomique(os.path.join(dossier, 'QUALITE.csv'), buf.getvalue(), 'utf-8-sig')
    if txt:
        ecrire_atomique(os.path.join(dossier, 'QUALITE.txt'),
                        '\n'.join(['=== Français ==='] + resume(lignes, 'fr') + ['', '=== English ==='] +
                                  resume(lignes, 'en')) + '\n')
