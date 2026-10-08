"""Compare un dossier traité par Coupole au traitement de référence (ohp_xisf.py, 7-8 octobre 2026).

    python outils/comparer_reference.py DOSSIER_COUPOLE DOSSIER_TRAITEMENT_REFERENCE [COPIE_XISF_REFERENCE]

DOSSIER_TRAITEMENT_REFERENCE contient journal.csv et INDEX_LOTS.csv (Banque-Images-OHP/traitement) ;
COPIE_XISF_REFERENCE (facultatif) est la racine de la copie complète, pour comparer pixels et en-têtes.
Différences attendues et ignorées : la ligne HISTORY qui nomme le programme, le commentaire de XISFCONV,
la ligne HISTORY de l'écart (« XISF » → « sortie »), la date de création et l'application créatrice.
"""
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def lire_csv(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.reader(f, delimiter=';'))


def normaliser_mots(mots):
    out = []
    saute = False
    for n, v, c in mots:
        if n == 'HISTORY' and saute and ':' not in c and ' = ' not in c:
            saute = False                    # fin de la ligne « converti de » coupée à 70 caractères
            continue
        saute = False
        if n == 'HISTORY' and (' : converti de ' in c or 'converted from' in c or c.startswith('ohp_xisf.py')
                               or c.startswith('Coupole ')):
            saute = True
            continue
        if n == 'HISTORY' and ('ecart max' in c or '|FITS -' in c):
            continue
        if n == 'XISFCONV':
            c = ''
        out.append((n, v, c))
    return out


def comparer(dossier, ref_trait, ref_copie=None):
    from coupole.core import xisf
    nous = {r[-1]: r for r in lire_csv(os.path.join(dossier, '_traitement', 'journal.csv'))[1:]}
    ref = {}
    for r in lire_csv(os.path.join(ref_trait, 'journal.csv'))[1:]:
        if r[-1] in nous and (r[-1] not in ref or r[6] == 'ok'):
            ref[r[-1]] = r
    ecarts = []
    cols = lire_csv(os.path.join(dossier, '_traitement', 'journal.csv'))[0]
    ix = {c: i for i, c in enumerate(cols)}
    for url, r in nous.items():
        a = ref.get(url)
        if a is None:
            ecarts.append(('absente_reference', url))
            continue
        for c in ('statut', 'wcs', 'destination', 'mots_cles_modifies', 'date', 'pose'):
            if r[ix[c]] != a[ix[c]]:
                ecarts.append((c, url, a[ix[c]], r[ix[c]]))
        if r[ix['statut']] == 'ok' and a[ix['ratio']] and abs(float(r[ix['ratio']]) - float(a[ix['ratio']])) > 0.002:
            ecarts.append(('ratio', url, a[ix['ratio']], r[ix['ratio']]))
    # lots
    idx_n = {r[0]: r for r in lire_csv(os.path.join(dossier, 'INDEX_LOTS.csv'))[1:]}
    idx_r = {r[0]: r for r in lire_csv(os.path.join(ref_trait, 'INDEX_LOTS.csv'))[1:]}
    for lot, r in idx_n.items():
        a = idx_r.get(lot)
        if a is None:
            ecarts.append(('lot_absent_reference', lot))
            continue
        partiel = int(r[5]) < int(a[5])          # sélection partielle : seule la cohérence est comparable
        for i, nom in ((5, 'poses'), (6, 'pose_totale'), (7, 'nuits'), (11, 'alignement')):
            if r[i] != a[i] and not (partiel and nom in ('poses', 'pose_totale', 'nuits')):
                ecarts.append(('lot_' + nom, lot, a[i], r[i]))
        for i, nom, tol in ((8, 'ra', 2e-4), (9, 'dec', 2e-4), (10, 'angle', 0.05)):
            if r[i] and a[i] and abs(float(r[i]) - float(a[i])) > tol and int(r[5]) == int(a[5]):
                ecarts.append(('lot_' + nom, lot, a[i], r[i]))
    n_pix = 0
    if ref_copie:
        for url, r in nous.items():
            if r[ix['statut']] != 'ok':
                continue
            p_n = os.path.join(dossier, r[ix['destination']])
            p_r = os.path.join(ref_copie, ref[url][ix['destination']])
            if not os.path.exists(p_r):
                ecarts.append(('fichier_reference_absent', p_r))
                continue
            dn, inf_n = xisf.lire(p_n)
            dr, inf_r = xisf.lire(p_r)
            if dn.dtype != dr.dtype or dn.shape != dr.shape or not (dn == dr).all():
                ecarts.append(('pixels', url))
            else:
                n_pix += 1
            mn, mr = normaliser_mots(inf_n['mots_cles']), normaliser_mots(inf_r['mots_cles'])
            if mn != mr:
                diff = [(a, b) for a, b in zip(mr, mn) if a != b][:4] + ([('longueur', len(mr), len(mn))]
                                                                        if len(mn) != len(mr) else [])
                ecarts.append(('mots_cles', url, diff))
            pn = {k: v for k, v in inf_n['proprietes'].items() if not k.startswith('XISF:')}
            pr = {k: v for k, v in inf_r['proprietes'].items() if not k.startswith('XISF:')}
            if pn != pr:
                ecarts.append(('proprietes', url, {k: (pr.get(k), pn.get(k)) for k in set(pn) | set(pr)
                                                   if pn.get(k) != pr.get(k)}))
    return ecarts, len(nous), len(idx_n), n_pix


def main():
    ecarts, n, nl, npix = comparer(*sys.argv[1:4])
    print('%d images, %d lots, %d fichiers aux pixels identiques' % (n, nl, npix))
    for e in ecarts:
        print('ÉCART', e)
    print('aucun écart' if not ecarts else '%d écart(s)' % len(ecarts))


if __name__ == '__main__':
    main()
