"""Intensités des familles de raies sur une grille fine en type spectral (pas de 1/8), calculées par la physique du
modèle « spectres physiques » (scripts de construction : atmosphères ATLAS9, Saha–Boltzmann, largeurs équivalentes)
avec un étalonnage interpolé de façon monotone et lisse (PCHIP de Fritsch–Carlson sur log T_eff et log g, entre les
70 types tabulés de chaque classe).  Les courbes de l'Explorateur de spectres n'ont plus de cassures : entre deux types
entiers, l'intensité est calculée et non plus interpolée en ligne droite.

Vérification « avec le moteur de référence » : aux types entiers, la grille fine retrouve la table du modèle
(intensites_familles, même normalisation : W / W_max de chaque raie représentative, maximum de la famille ramené à 100).

    python3 outils/verif_anim/intensites_fines.py DOSSIER_SPECTRES_PHYSIQUES
    → coupole/modules/anim/donnees/intensites_fines.json.gz (+ rapport de vérification sur la sortie standard)

Durée : quelques minutes (2 765 états d'atmosphère).
"""
from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parents[2]
PAS = 8                                         # points par type spectral
CLASSES = ['I', 'II', 'III', 'IV', 'V']
FAMILLES = ['he_ii', 'he_i', 'h', 'metaux_ionises', 'metaux', 'molecules', 'ch']


def pchip(x: np.ndarray, y: np.ndarray, xs: np.ndarray) -> np.ndarray:
    """Interpolation cubique monotone (Fritsch–Carlson, même formule que pchip() des moteurs TS et Python)."""
    h = np.diff(x)
    d = np.diff(y) / h
    n = len(x)
    m = np.zeros(n)
    for k in range(1, n - 1):
        if d[k - 1] * d[k] <= 0:
            m[k] = 0.0
        else:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])
    m[0], m[-1] = d[0], d[-1]
    out = np.empty_like(xs)
    for j, t in enumerate(xs):
        k = min(max(int(np.searchsorted(x, t) - 1), 0), n - 2)
        s = (t - x[k]) / h[k]
        h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
        out[j] = h00 * y[k] + h10 * h[k] * m[k] + h01 * y[k + 1] + h11 * h[k] * m[k + 1]
    return out


def main(dossier: Path) -> int:
    sys.path.insert(0, str(dossier / 'scripts'))
    import construire as K  # noqa: E402
    import molecules as MOL  # noqa: E402
    import raies as R  # noqa: E402

    modele = json.load(gzip.open(ICI / 'coupole' / 'modules' / 'anim' / 'donnees' / 'modele_spectres.json.gz', 'rt'))
    types = np.array(modele['types'], dtype=float)
    cand = R.candidats()
    bandes = MOL.bandes_tio() + MOL.bandes_ch()
    tio = [k for k, b in enumerate(bandes) if b['molecule'] == 'TiO']
    chb = [k for k, b in enumerate(bandes) if b['molecule'] == 'CH']
    obl = {}
    for esp, lam in K.OBLIGATOIRES:
        i = min((i for i, r in enumerate(cand) if r['espece'] == esp), key=lambda i: abs(cand[i]['lambda'] - lam))
        obl.setdefault(cand[i]['famille'], []).append(i)
    lam_obl = {i: cand[i]['lambda'] for f in obl for i in obl[f]}

    xs = np.arange(0, 69 * PAS + 1) / PAS
    brut = {}
    W = {}
    for c in CLASSES:
        et = modele['etalonnage'][c]
        lt = pchip(types, np.log10([e['teff'] for e in et]), xs)
        lg = pchip(types, np.array([e['logg'] for e in et]), xs)
        for j, S in enumerate(xs):
            at = R.etat_atmosphere(float(10 ** lt[j]), float(lg[j]))
            B = [R.force_bande(b, at) for b in bandes]
            idx = list(lam_obl)
            fond = R.eta_bandes(np.array([lam_obl[i] for i in idx]), bandes, B)
            W[(c, j)] = {i: R.force_raie(cand[i], at, float(fd))['W'] for i, fd in zip(idx, fond)}
            brut[(c, j)] = {
                'molecules': K.largeur_bandes_combinees([bandes[k] for k in tio], [B[k] for k in tio], 10 ** lt[j]),
                'ch': K.largeur_bandes_combinees([bandes[k] for k in chb], [B[k] for k in chb], 10 ** lt[j]),
            }
        print(c, 'fait', file=sys.stderr)
    # normalisation : celle de la table (W_max de chaque raie et maximum de chaque famille sur les types ENTIERS)
    entiers = [j for j in range(len(xs)) if j % PAS == 0]
    wmax = {i: max(W[(c, j)][i] for c in CLASSES for j in entiers) for i in lam_obl}
    for key in brut:
        for f, ids in obl.items():
            brut[key][f] = sum(W[key][i] / wmax[i] for i in ids) / len(ids)
    norme = {f: max(brut[(c, j)][f] for c in CLASSES for j in entiers) for f in FAMILLES}
    fines = {c: {f: [round(100 * brut[(c, j)][f] / norme[f], 2) for j in range(len(xs))] for f in FAMILLES}
             for c in CLASSES}
    # vérification : aux types entiers, la table du modèle
    ecart = 0.0
    for c in CLASSES:
        for f in FAMILLES:
            for t in range(70):
                ecart = max(ecart, abs(fines[c][f][t * PAS] - modele['intensites_familles'][c][f][t]))
    print(f'écart maximal aux types entiers avec la table du modèle : {ecart:.3f} (sur 100)')
    sortie = {'version': 1, 'pas_par_type': PAS, 'source': 'outils/verif_anim/intensites_fines.py (modèle spectres '
              'physiques 1.0.0, étalonnage PCHIP)', 'ecart_types_entiers': round(ecart, 3), 'intensites': fines}
    with gzip.open(ICI / 'coupole' / 'modules' / 'anim' / 'donnees' / 'intensites_fines.json.gz', 'wt',
                   encoding='utf-8') as fh:
        json.dump(sortie, fh, separators=(',', ':'))
    return 0


if __name__ == '__main__':
    sys.exit(main(Path(sys.argv[1]).resolve()))
