"""Contenu d'une fiche au survol, sans affichage : titre, désignations, lignes (libellé, valeur, source) et résumé lu
par les lecteurs d'écran.  Même fonction, ligne pour ligne, que src/anim/fiche_texte.ts de Coupole Web (tests croisés
sur les mêmes fiches) ; le widget de la toile n'en fait que la mise en page."""
from __future__ import annotations

import math
import re

from ...core.i18n import langue, tr
from .base import nombre

METHODES_EN = {
    'parallaxe adoptée par SIMBAD': 'SIMBAD adopted parallax',
    'mesure dédiée': 'dedicated measurement',
    'amas (VLBA)': 'cluster (VLBA)',
    'publiée': 'published',
    'SIMBAD (peu fiable)': 'SIMBAD (unreliable)',
    'Gaia DR3 (peu fiable)': 'Gaia DR3 (unreliable)',
}

EXPRESSIONS_EN = (
    (r'médiane de (\d+) mesures SIMBAD mesFe_h', r'median of \1 SIMBAD mesFe_h measurements'),
    (r'médiane des mesures SIMBAD mesFe_h', 'median of the SIMBAD mesFe_h measurements'),
    (r'calculée : ', 'computed: '),
    (r', sans extinction', ', no extinction'),
    (r'estimée de B−V \(séquence des naines de ', 'estimated from B−V (dwarf sequence of '),
    (r' pour d = ', ' for d = '),
    (r' adoptée par les auteurs', ' adopted by the authors'),
    (r' du compagnon ', ' of the companion '),
    (r'estimée du type spectral', 'estimated from the spectral type'),
    (r'naine de même sous-type', 'dwarf of the same subtype'),
    (r'table révisée', 'revised table'),
    (r'point zéro', 'zero point'),
)


def source_courte(s, lg: str | None = None) -> str:
    """Source courte et dans la langue : en anglais, le commentaire en français qui suit la référence est retiré."""
    if not s:
        return ''
    lg = lg or langue()
    t = s.strip()
    if lg == 'en':
        for motif, v in EXPRESSIONS_EN:
            t = re.sub(motif, v, t)
        for sep in (' — ', ' ; ', ' (VizieR', ', voir', ' : «', ', résumé'):
            i = t.find(sep)
            if i > 0:
                t = t[:i]
    return t[:149].rstrip() + '…' if len(t) > 150 else t


def _ecart(moins, plus, dec: int) -> str:
    if moins is None and plus is None:
        return ''
    if moins is not None and plus is not None and abs(moins - plus) < 10 ** -dec / 2:
        return ' ± %s' % nombre(moins, dec)
    return ' (−%s/+%s)' % (nombre(moins or 0, dec), nombre(plus or 0, dec))


def _dec_dist(d: float) -> int:
    return 2 if d < 10 else 1 if d < 100 else 0


def _num(v):
    x = (v or {}).get('valeur') if isinstance(v, dict) else None
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else None


def contenu_fiche(f: dict, lg: str | None = None) -> dict:
    """{'titre', 'sous_titre', 'couleur', 'lignes': [{'libelle', 'valeur', 'source', 'alerte'}], 'resume'}."""
    lg = lg or langue()
    L = []
    noms = f.get('noms') or {}
    titre = noms.get(lg) or noms.get('fr', '')
    des = [d for d in (f.get('designations') or []) if d != titre][:4]
    sous_titre = ' · '.join(des)
    ty = f.get('type') or {}
    typ = (ty.get(lg) or ty.get('fr') or '') if ty else ''
    tsp = f.get('type_spectral') or {}
    sp = tsp.get('valeur') if isinstance(tsp.get('valeur'), str) else ''
    if typ or sp:
        L.append({'libelle': tr('anim_fiche_type'), 'valeur': ' · '.join(x for x in (typ, sp) if x),
                  'source': source_courte(tsp.get('source') if tsp.get('source') is not None else ty.get('source'), lg)})
    v, mv = _num(f.get('V')), _num(f.get('M_V'))
    if v is not None:
        L.append({'libelle': tr('anim_fiche_mag_v'), 'valeur': nombre(v, 2), 'source': source_courte(f['V'].get('source'), lg)})
    if mv is not None:
        L.append({'libelle': tr('anim_fiche_mag_abs'), 'valeur': nombre(mv, 2),
                  'source': source_courte(f['M_V'].get('source'), lg)})
    d = f.get('distance')
    if d and isinstance(d.get('pc'), (int, float)):
        dp = _dec_dist(d['pc'])
        val = '%s%s pc' % (nombre(d['pc'], dp), _ecart(d.get('pc_moins'), d.get('pc_plus'), dp))
        if isinstance(d.get('al'), (int, float)):
            da = _dec_dist(d['al'])
            val += ' · %s%s %s' % (nombre(d['al'], da), _ecart(d.get('al_moins'), d.get('al_plus'), da), tr('anim_fiche_al'))
        meth = d.get('methode') or ''
        if meth and lg == 'en':
            meth = METHODES_EN.get(meth, meth)
        L.append({'libelle': tr('anim_fiche_distance'),
                  'valeur': val + (' — %s' % tr('anim_fiche_incertaine') if d.get('peu_fiable') else ''),
                  'source': ' · '.join(x for x in (meth, source_courte(d.get('source'), lg)) if x),
                  'alerte': bool(d.get('peu_fiable'))})
        s = d.get('affichage_suggere')
        if s and isinstance(s.get('pc'), (int, float)):
            L.append({'libelle': tr('anim_fiche_distance_affichee'), 'valeur': '%s pc' % nombre(s['pc'], _dec_dist(s['pc'])),
                      'source': source_courte(s.get('pourquoi'), lg)})
        alt = [a for a in (d.get('alternatives') or []) if isinstance(a.get('d'), (int, float))][:4]
        if alt:
            L.append({'libelle': tr('anim_fiche_autres_mesures'), 'valeur': ' ; '.join(
                '%s%s pc (%s)' % (nombre(a['d'], _dec_dist(a['d'])), _ecart(a.get('moins'), a.get('plus'), _dec_dist(a['d'])),
                                  re.split(r'[,:(]', source_courte(a.get('ref'), lg))[0].strip()) for a in alt),
                'source': ''})
    t = _num(f.get('teff'))
    if t is not None:
        inc = f['teff'].get('incertitude')
        L.append({'libelle': tr('anim_fiche_teff'),
                  'valeur': '%s%s K' % (nombre(t, 0), ' ± %s' % nombre(inc, 0) if isinstance(inc, (int, float)) else ''),
                  'source': source_courte(f['teff'].get('source'), lg)})
    r = _num(f.get('rayon_Rsun'))
    if r is not None:
        rr = f['rayon_Rsun']
        dr = 2 if r < 10 else 0
        moins = rr.get('moins') if rr.get('moins') is not None else rr.get('incertitude')
        plus = rr.get('plus') if rr.get('plus') is not None else rr.get('incertitude')
        L.append({'libelle': tr('anim_fiche_rayon'), 'valeur': '%s%s R☉' % (nombre(r, dr), _ecart(moins, plus, dr)),
                  'source': source_courte(rr.get('source'), lg)})
    ll = _num(f.get('luminosite_log_Lsun'))
    if ll is not None:
        lum = 10 ** ll
        L.append({'libelle': tr('anim_fiche_luminosite'), 'valeur': '%s L☉' % nombre(lum, 2 if lum < 10 else 0),
                  'source': source_courte(f['luminosite_log_Lsun'].get('source'), lg)})
    ta = (f.get('taille_arcmin') or {}).get('valeur')
    if isinstance(ta, list) and ta:
        tp = _num(f.get('taille_pc'))
        L.append({'libelle': tr('anim_fiche_taille'),
                  'valeur': ' × '.join('%s′' % nombre(float(x), 0) for x in ta) + (' (%s pc)' % nombre(tp, 2) if tp is not None else ''),
                  'source': source_courte(f['taille_arcmin'].get('source'), lg)})
    for cle, unite, libelle in (('longueur_pc', ' pc', 'anim_fiche_longueur'), ('diametre_deg', '°', 'anim_fiche_diametre'),
                                ('arc_deg', '°', 'anim_fiche_arc')):
        o = f.get(cle)
        if o and isinstance(o.get('valeur'), (int, float)):
            L.append({'libelle': tr(libelle), 'valeur': '%s%s' % (nombre(o['valeur'], 0), unite),
                      'source': source_courte(o.get('ref'), lg)})
    age = f.get('age')
    if age:
        if isinstance(age.get('valeur_Myr'), (int, float)):
            err = age.get('err_Myr')
            L.append({'libelle': tr('anim_fiche_age'), 'valeur': '%s%s %s' % (
                nombre(age['valeur_Myr'], 1), ' ± %s' % nombre(err, 1) if isinstance(err, (int, float)) else '',
                tr('anim_fiche_ma')), 'source': source_courte(age.get('ref'), lg)})
        elif age.get('note'):
            L.append({'libelle': tr('anim_fiche_age'), 'valeur': source_courte(age['note'], 'fr'), 'source': ''})
    if f.get('etoiles_excitatrices'):
        L.append({'libelle': tr('anim_fiche_excitatrices'), 'valeur': ', '.join(
            re.sub(r'^\* ', '', s).split(' (')[0].split(' — ')[0].strip() for s in f['etoiles_excitatrices']), 'source': ''})
    for ligne in L:
        ligne.setdefault('alerte', False)
    morceaux = [titre]
    if typ:
        morceaux.append(typ)
    if d and isinstance(d.get('pc'), (int, float)):
        morceaux.append('%s pc' % nombre(d['pc'], _dec_dist(d['pc'])))
    if t is not None:
        morceaux.append('%s K' % nombre(t, 0))
    return {'titre': titre, 'sous_titre': sous_titre, 'couleur': f.get('couleur'), 'lignes': L,
            'resume': ', '.join(morceaux)}
