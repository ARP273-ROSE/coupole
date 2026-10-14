"""Moteur d'exécution (Python pur, sans numpy) du modèle « spectres physiques ».

Lit donnees/modele_spectres.json (produit par scripts/construire.py) et fournit, pour un type spectral numérique
(O0 = 0 … M9 = 69, réel) et une classe de luminosité ('I' … 'V') :

    m = ModeleSpectres.depuis_fichier(chemin)
    m.etalonnage(t, classe)      → {'teff', 'logg', 'bv', 'mv', 'rayon', 'logl', 'source', 'drapeaux'}
    m.intensites(t, classe)      → {'he_ii', 'he_i', 'h', 'metaux_ionises', 'metaux', 'molecules', 'ch'} (0–100)
    m.raies(t, classe)           → [{'id','lambda','espece','famille','nom','profondeur','W','fwhm'}]
    m.bandes(t, classe)          → [{'id','molecule','systeme','lambda_tete','degrade','eta_tete','d0'}]
    m.residu(t, classe, lam, familles=None, resolution=0.0)   → I/I_continu (0–1) à lam (nm, air)
    m.spectre(t, classe, lams, familles=None, resolution=0.0) → [I/I_continu]
    m.continu_relatif(teff, lam) → B_λ(T) / max_{380–720 nm} B_λ(T)
    m.couleur_etoile(teff)       → (r, g, b) 0–255 (Planck × CIE 1931 → sRGB)
    m.couleur_lambda(lam)        → (r, g, b) 0–255 (lumière monochromatique, composantes négatives écrêtées)
    m.beta_prime(teff, lam)      → β' de Milne–Eddington (profondeur maximale β'/(1+β'))

L'interface est la même, nom pour nom, dans spectres_physiques.ts.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

# constantes CODATA 2022 (exactes dans le SI) : h, c, k → c₂ = hc/k
H_SI = 6.62607015e-34
C_SI = 299792458.0
K_SI = 1.380649e-23
C2_NM_K = H_SI * C_SI / K_SI * 1e9        # 1,438 776 877… × 10⁷ nm K
FAM_BANDES = 'molecules'
AIRE_GAUSS = 0.5 * math.sqrt(math.pi / math.log(2))   # ∫ exp(−4 ln2 x²/f²) dx / f = 1,0645
AIRE_LORENTZ = math.pi / 2                            # ∫ 1/(1+(2x/f)²) dx / f


def _planck_rel(lam_nm: float, teff: float) -> float:
    """B_λ(T) à un facteur près : λ⁻⁵ / (exp(c₂/λT) − 1)."""
    return lam_nm ** -5 / math.expm1(C2_NM_K / (lam_nm * teff))


def _wien_x() -> float:
    """Racine de x = 5 (1 − e^{−x}) (maximum de B_λ), par Newton."""
    x = 5.0
    for _ in range(50):
        f = x - 5 * (1 - math.exp(-x))
        x -= f / (1 - 5 * math.exp(-x))
    return x


WIEN_X = _wien_x()


def pchip(ys, x: float):
    """Interpolation cubique monotone et lisse (PCHIP de Fritsch–Carlson) d'une suite régulière ys (pas 1) en x : passe
    par les nœuds, sans dépassement ni cassure.  Nœud absent (None) : repli comme l'interpolation linéaire."""
    n = len(ys)
    xx = min(max(float(x), 0.0), n - 1.0)
    k = min(int(math.floor(xx)), n - 2)
    s = xx - k
    y0, y1 = ys[k], ys[k + 1]
    if y0 is None or y1 is None:
        return y0 if s == 0 else (y1 if s == 1 else None)
    d = y1 - y0

    def pente(dp, dn):
        return dn if dp is None else (0.0 if dp * dn <= 0 else 2 * dp * dn / (dp + dn))

    ym = ys[k - 1] if k > 0 else None
    yp = ys[k + 2] if k + 2 < n else None
    m0 = pente(None if ym is None else y0 - ym, d)
    m1 = pente(None if yp is None else yp - y1, d)
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1
    h10 = s ** 3 - 2 * s ** 2 + s
    h01 = -2 * s ** 3 + 3 * s ** 2
    h11 = s ** 3 - s ** 2
    return h00 * y0 + h10 * m0 + h01 * y1 + h11 * m1


class ModeleSpectres:
    def __init__(self, donnees: dict, fines: dict | None = None):
        self.d = donnees
        # intensités des familles calculées tous les 1/pas de type (outils/verif_anim/intensites_fines.py)
        self.fines = fines
        self.classes = donnees['classes']
        self.types = donnees['types']
        self._raies = {r['id']: r for r in donnees['raies']}
        self._bandes = {b['id']: b for b in donnees['bandes']}

    @classmethod
    def depuis_fichier(cls, chemin: str | Path) -> 'ModeleSpectres':
        return cls(json.loads(Path(chemin).read_text(encoding='utf-8')))

    # ------------------------------------------------------------ interpolation en type
    def _encadre(self, t: float) -> tuple[int, int, float]:
        t = min(max(float(t), self.types[0]), self.types[-1])
        i = int(math.floor(t))
        j = min(i + 1, self.types[-1])
        return i, j, t - i

    def etalonnage(self, t: float, classe: str) -> dict:
        """Étalonnage au type t : interpolation monotone lisse (PCHIP) entre les types tabulés, T_eff en logarithme."""
        i, j, w = self._encadre(t)
        tab = self.d['etalonnage'][classe]
        a, b = tab[i], tab[j]
        tt = min(max(float(t), self.types[0]), self.types[-1])
        out = {}
        colonnes = self.__dict__.setdefault('_colonnes', {})       # colonnes tabulées, extraites une fois
        for k in ('teff', 'logg', 'bv', 'mv', 'rayon', 'logl'):
            ys = colonnes.get((classe, k))
            if ys is None:
                ys = colonnes[(classe, k)] = [None if e.get(k) is None else (math.log10(e[k]) if k == 'teff' else e[k])
                                              for e in tab]
            v = pchip(ys, tt)
            out[k] = None if v is None else (10 ** v if k == 'teff' else v)
        out['source'] = a['source'] if w < 0.5 else b['source']
        out['drapeaux'] = sorted(set(a['drapeaux']) | set(b['drapeaux'])) if 0 < w < 1 else list(
            (a if w == 0 else b)['drapeaux'])
        return out

    def intensites(self, t: float, classe: str) -> dict:
        """Intensités des familles (0–100) : grille fine (1/8 de type) interpolée par PCHIP ; sinon table par type."""
        if self.fines:
            tab = self.fines['intensites'][classe]
            x = min(max(float(t), self.types[0]), self.types[-1]) * self.fines['pas_par_type']
            return {f: max(0.0, pchip(v, x)) for f, v in tab.items()}
        i, j, w = self._encadre(t)
        tab = self.d['intensites_familles'][classe]
        return {f: (1 - w) * v[i] + w * v[j] for f, v in tab.items()}

    def raies(self, t: float, classe: str) -> list[dict]:
        i, j, w = self._encadre(t)
        fi = {x[0]: x[1:] for x in self.d['forces'][classe][i]}
        fj = {x[0]: x[1:] for x in self.d['forces'][classe][j]}
        out = []
        for rid in sorted(set(fi) | set(fj)):
            a = fi.get(rid, (0.0, 0.0, None))
            b = fj.get(rid, (0.0, 0.0, None))
            fw = a[2] if b[2] is None else (b[2] if a[2] is None else (1 - w) * a[2] + w * b[2])
            d0 = (1 - w) * a[0] + w * b[0]
            W = (1 - w) * a[1] + w * b[1]
            if W <= 0:
                continue
            r = self._raies[rid]
            out.append({'id': rid, 'lambda': r['lambda_air_nm'], 'espece': r['espece'], 'famille': r['famille'],
                        'nom': r['nom'], 'profondeur': d0, 'W': W, 'fwhm': fw})
        return out

    def bandes(self, t: float, classe: str) -> list[dict]:
        i, j, w = self._encadre(t)
        fi = {x[0]: x[1:] for x in self.d['forces_bandes'][classe][i]}
        fj = {x[0]: x[1:] for x in self.d['forces_bandes'][classe][j]}
        out = []
        for bid in sorted(set(fi) | set(fj)):
            a, b = fi.get(bid), fj.get(bid)
            eta = (1 - w) * (a[0] if a else 0.0) + w * (b[0] if b else 0.0)
            d0 = (a or b)[1] if (a is None or b is None) else (1 - w) * a[1] + w * b[1]
            if eta <= 0:
                continue
            bd = self._bandes[bid]
            out.append({'id': bid, 'molecule': bd['molecule'], 'systeme': bd['systeme'],
                        'lambda_tete': bd['lambda_tete_air_nm'], 'degrade': bd['degrade'], 'eta_tete': eta, 'd0': d0})
        return out

    # ------------------------------------------------------------ transfert : Milne–Eddington gris
    @staticmethod
    def beta_prime(teff: float, lam: float) -> float:
        """β' = (2/3) [B(T(τ=1)) − B(T(0))] / B(T(0)), T⁴(τ) = ¾ Teff⁴ (τ + ⅔)."""
        t0 = teff * (0.75 * (2 / 3)) ** 0.25
        t1 = teff * (0.75 * (1 + 2 / 3)) ** 0.25
        b0, b1 = _planck_rel(lam, t0), _planck_rel(lam, t1)
        return (2 / 3) * (b1 - b0) / b0

    @staticmethod
    def _profil(dl: float, d0: float, W: float, fwhm: float, resolution: float) -> float:
        """Pseudo-Voigt de même profondeur, FWHM et surface (W) que la raie calculée ; convolution approchée par
        une gaussienne instrumentale de FWHM « resolution » (W conservée)."""
        if fwhm is None or fwhm <= 0 or d0 <= 0:
            return 0.0
        m = (W / (d0 * fwhm) - AIRE_GAUSS) / (AIRE_LORENTZ - AIRE_GAUSS)
        m = min(1.0, max(0.0, m))
        f = math.sqrt(fwhm * fwhm + resolution * resolution) if resolution > 0 else fwhm
        d = W / (f * ((1 - m) * AIRE_GAUSS + m * AIRE_LORENTZ)) if resolution > 0 else d0
        x = 2 * dl / f
        return d * ((1 - m) * math.exp(-math.log(2) * x * x) + m / (1 + x * x))

    def residu(self, t: float, classe: str, lam: float, familles=None, resolution: float = 0.0) -> float:
        return self.spectre(t, classe, [lam], familles, resolution)[0]

    def spectre(self, t: float, classe: str, lams, familles=None, resolution: float = 0.0) -> list[float]:
        teff = self.etalonnage(t, classe)['teff']
        raies = [r for r in self.raies(t, classe) if familles is None or r['famille'] in familles]
        bandes = self.bandes(t, classe) if familles is None or FAM_BANDES in familles else []
        out = []
        for lam in lams:
            eta = 0.0
            for b in bandes:
                dl = lam - b['lambda_tete'] if b['degrade'] == 'rouge' else b['lambda_tete'] - lam
                if dl >= 0:
                    eta += b['eta_tete'] * math.exp(-dl / b['d0'])
            bp = self.beta_prime(teff, lam)
            res = 1 - bp * eta / ((1 + bp) * (1 + eta))
            for r in raies:
                dl = lam - r['lambda']
                if abs(dl) < 60 * max(r['fwhm'] or 0, resolution, 0.01):
                    res *= 1 - self._profil(dl, r['profondeur'], r['W'], r['fwhm'], resolution)
            out.append(res)
        return out

    # ------------------------------------------------------------ continu et couleurs
    @staticmethod
    def continu_relatif(teff: float, lam: float) -> float:
        lam_max = C2_NM_K / (WIEN_X * teff)
        ref = min(max(lam_max, 380.0), 720.0)      # maximum de B_λ sur [380, 720] nm
        return _planck_rel(lam, teff) / _planck_rel(ref, teff)

    def _xyz_vers_srgb(self, X: float, Y: float, Z: float) -> tuple[float, float, float]:
        M = self.d['srgb']['XYZ_vers_sRGB_lineaire']
        return tuple(M[k][0] * X + M[k][1] * Y + M[k][2] * Z for k in range(3))

    @staticmethod
    def _gamma(v: float) -> float:
        return 1.055 * v ** (1 / 2.4) - 0.055 if v > 0.0031308 else 12.92 * v

    def couleur_etoile(self, teff: float) -> tuple[int, int, int]:
        c = self.d['cie1931_5nm']
        X = Y = Z = 0.0
        for k, (xb, yb, zb) in enumerate(zip(c['xbar'], c['ybar'], c['zbar'])):
            b = _planck_rel(c['lambda0'] + k * c['pas'], teff)
            X, Y, Z = X + b * xb, Y + b * yb, Z + b * zb
        rgb = [max(0.0, v) for v in self._xyz_vers_srgb(X, Y, Z)]
        mx = max(rgb)
        return tuple(int(math.floor(255 * self._gamma(v / mx) + 0.5)) for v in rgb)

    def couleur_lambda(self, lam: float) -> tuple[int, int, int]:
        c = self.d['cie1931_5nm']
        x = (lam - c['lambda0']) / c['pas']
        i = int(min(max(math.floor(x), 0), len(c['xbar']) - 2))
        w = min(max(x - i, 0.0), 1.0)
        X, Y, Z = ((1 - w) * c[k][i] + w * c[k][i + 1] for k in ('xbar', 'ybar', 'zbar'))
        rgb = [max(0.0, v) for v in self._xyz_vers_srgb(X, Y, Z)]   # hors gamut : composantes négatives écrêtées
        mx = max(rgb)
        if mx <= 0:
            return (0, 0, 0)
        return tuple(int(math.floor(255 * self._gamma(v / mx) + 0.5)) for v in rgb)
