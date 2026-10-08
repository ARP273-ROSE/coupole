"""Distances cosmologiques : du redshift aux distances, âges, volume, module de distance, échelle.

Noyau repris du calculateur « cosmologie-redshift » du même auteur (``programme/cosmo_core.py`` :
``make_cosmology``, grandeurs brutes, propagation des incertitudes avec le terme croisé, comparaison
SH0ES), adapté à Coupole (sans interface, unités en Mpc, textes traduits ailleurs).  Les formules ont été
vérifiées indépendamment le 8 octobre 2026 contre une intégration SageMath (mpmath, Fermi-Dirac exacte
pour les neutrinos) de z = 10⁻⁸ à 1100, univers plat et courbes (Ωk = ±0,01, ±0,05) : écart relatif
≤ 3·10⁻⁶ sur les distances et ≤ 2·10⁻⁵ sur les âges (ajustement de Komatsu des neutrinos dans astropy) —
voir ``outils/verif_cosmo/``.  Ajouts propres à Coupole : jeux de paramètres usuels (Planck 2015, WMAP 9,
ΛCDM « de manuel »), volume comobile (forme fermée de Hogg 1999, développement limité près de Ωk·x² = 0
où la forme fermée perd tous ses chiffres), module de distance, échelle en kpc par seconde d'arc.

Backend : ``astropy.cosmology``.

CE QUE Planck18 CONTIENT (cf. le cours du calculateur) :
    E(z)² = Ωr(z)(1+z)⁴ + Ωm0 (1+z)³ + Ωk (1+z)² + ΩΛ
    Ωm0 = 0,30966 (baryons + matière noire), Ων0 = 0,0014397 (neutrinos massifs, 0,06 eV) :
    Ωm0 + Ων0 = 0,3111, le « Ωm » du papier Planck 2018 ; Ωγ0 = 5,402·10⁻⁵ (T₀ = 2,7255 K).
"""
from __future__ import annotations

import math

import numpy as np

H0_PLANCK = 67.66                # km/s/Mpc  (Planck 2018, TT,TE,EE+lowE+lensing+BAO)
OM_PLANCK = 0.31110              # Ωm TOTAL (matière + neutrinos)
H0_SHOES = 73.04                 # km/s/Mpc  (SH0ES, Riess et al. 2022)
SIGMA_H0 = 0.42
SIGMA_OM = 0.0056
RHO_H0_OM = -0.9763              # corrélation H0–Ωm, déduite de ω_m = Ωm h² (voir le calculateur)

Z_MAX = 1500.0                   # au-delà : univers opaque, rien à observer
Z_CMB = 1089.8
Z_PROCHE = 0.03                  # en deçà, la vitesse propre de l'objet domine le redshift

# bornes des réglages (affichées à côté des champs : jamais de correction muette)
BORNES = {'H0': (40.0, 100.0), 'Om': (0.1, 1.0), 'Ok_planck18': (-0.05, 0.05), 'Ok_perso': (-0.3, 0.3)}

MODELES = ('planck18', 'planck15', 'wmap9', 'simple', 'perso')
AVEC_COURBURE = {'planck18', 'perso'}

# Grandeurs, dans l'ordre d'affichage : clé → unité (clé de traduction de l'unité)
GRANDEURS = [
    ('a', ''), ('E', ''), ('H_z', 'kms_mpc'),
    ('comoving', 'mpc'), ('transverse', 'mpc'), ('luminosity', 'mpc'), ('angular_diameter', 'mpc'),
    ('lookback', 'mpc'), ('lookback_gyr', 'gyr'), ('age_at_z', 'gyr'), ('t0_model', 'gyr'),
    ('distmod', 'mag'), ('kpc_arcsec', 'kpc_arcsec'), ('vol_gpc3', 'gpc3'),
    ('v_cz', 'kms'), ('v_sr', 'kms'), ('v_flrw', 'kms'),
]
DISTANCES = ('comoving', 'transverse', 'luminosity', 'angular_diameter', 'lookback')
AVEC_SIGMA = ('comoving', 'transverse', 'luminosity', 'angular_diameter', 'lookback', 'lookback_gyr', 'age_at_z',
              't0_model', 'distmod', 'kpc_arcsec', 'vol_gpc3', 'H_z', 'v_flrw')
COURBES = ('comoving', 'luminosity', 'angular_diameter', 'lookback')


class ErreurCosmo(ValueError):
    """Saisie hors du domaine utile ; `cle` est la clé de traduction de l'explication."""

    def __init__(self, cle: str, **valeurs):
        super().__init__(cle)
        self.cle, self.valeurs = cle, valeurs


def _astropy():
    from astropy import constants as const, units as u
    from astropy.cosmology import FlatLambdaCDM, LambdaCDM, Planck15, Planck18, WMAP9
    return const, u, FlatLambdaCDM, LambdaCDM, Planck15, Planck18, WMAP9


def c_kms() -> float:
    const, u = _astropy()[:2]
    return const.c.to_value(u.km / u.s)


def al_par_mpc() -> float:
    u = _astropy()[1]
    return (1 * u.Mpc).to_value(u.lyr)


# ============================================================================ modèles
_cache: dict = {}


def make_cosmology(H0: float = H0_PLANCK, Om: float = OM_PLANCK, Ok: float = 0.0):
    """Cosmologie ΛCDM avec le contenu radiatif de Planck 2018 (repris tel quel du calculateur).

    `Om` est la densité de matière TOTALE au sens du papier Planck (matière noire + baryons + neutrinos).
    astropy sépare les neutrinos, d'où `Om0 = Om - Onu0` ; Onu0 dépend de H0 (densité critique), on itère.
    Aux paramètres exacts de Planck 2018 sans courbure, on rend la réalisation `Planck18` elle-même.
    """
    const, u, FlatLambdaCDM, LambdaCDM, Planck15, Planck18, WMAP9 = _astropy()
    key = (round(H0, 6), round(Om, 8), round(Ok, 8))
    if key in _cache:
        return _cache[key]
    if key == (H0_PLANCK, round(OM_PLANCK, 8), 0.0):
        _cache[key] = Planck18
        return Planck18
    p = Planck18
    kw = dict(Tcmb0=p.Tcmb0, Neff=p.Neff, m_nu=p.m_nu, Ob0=p.Ob0)
    onu = p.Onu0
    c = None
    for _ in range(2):
        om0 = Om - onu
        c = LambdaCDM(H0=H0, Om0=om0, Ode0=1.0, **kw)
        onu = c.Onu0
    om0 = Om - onu
    ode0 = 1.0 - om0 - c.Ogamma0 - onu - Ok
    out = LambdaCDM(H0=H0, Om0=om0, Ode0=ode0, **kw)
    _cache[key] = out
    return out


def construire(modele: str = 'planck18', H0: float | None = None, Om: float | None = None, Ok: float = 0.0):
    """Modèle astropy pour un jeu de paramètres ; lève ErreurCosmo si les réglages sont hors bornes."""
    const, u, FlatLambdaCDM, LambdaCDM, Planck15, Planck18, WMAP9 = _astropy()
    if modele not in MODELES:
        raise ErreurCosmo('cosmo_err_modele', modele=modele)
    Ok = float(Ok or 0.0)
    if modele in AVEC_COURBURE:
        lo, hi = BORNES['Ok_' + modele]
        if not lo <= Ok <= hi:
            raise ErreurCosmo('cosmo_err_ok', mini=lo, maxi=hi)
    if modele == 'planck18':
        return make_cosmology(H0_PLANCK, OM_PLANCK, Ok)
    if modele == 'planck15':
        return Planck15
    if modele == 'wmap9':
        return WMAP9
    if modele == 'simple':
        key = ('simple',)
        if key not in _cache:
            _cache[key] = FlatLambdaCDM(H0=70.0, Om0=0.3, Tcmb0=0.0, name='LCDM 70/0.3/0.7')
        return _cache[key]
    H0 = float(H0 if H0 is not None else H0_PLANCK)
    Om = float(Om if Om is not None else OM_PLANCK)
    for nom, v in (('H0', H0), ('Om', Om)):
        lo, hi = BORNES[nom]
        if not lo <= v <= hi:
            raise ErreurCosmo('cosmo_err_' + nom.lower(), mini=lo, maxi=hi)
    try:
        m = make_cosmology(H0, Om, Ok)
    except ValueError as e:                        # refus d'astropy (densités incohérentes)
        raise ErreurCosmo('cosmo_err_parametres', erreur=str(e))
    zz = np.concatenate([[0.0], np.logspace(-3, math.log10(Z_MAX), 200)])
    with np.errstate(invalid='ignore'):
        e = m.efunc(zz)
    if not np.all(np.isfinite(e)) or np.any(e <= 0):
        raise ErreurCosmo('cosmo_err_rebond')
    return m


def parametres(model) -> dict:
    """Paramètres affichables d'un modèle astropy."""
    nu = float(np.sum(model.m_nu.value)) if model.has_massive_nu else 0.0
    return {'H0': model.H0.value, 'Om': model.Om0 + model.Onu0, 'Om0': model.Om0, 'Onu0': model.Onu0,
            'Ode0': model.Ode0, 'Ok0': model.Ok0, 'Ogamma0': model.Ogamma0, 'Tcmb0': model.Tcmb0.value,
            'Neff': model.Neff, 'mnu': nu}


# ============================================================================ grandeurs
def volume_comobile_gpc3(model, dm_mpc: float) -> float:
    """Volume comobile jusqu'à la distance transverse D_M (Hogg 1999, éq. 29), en Gpc³.

    La forme fermée (sinh/sin) soustrait deux nombres presque égaux quand Ωk·(D_M/D_H)² est petit :
    astropy y perd tous ses chiffres (volume faux, voire négatif, à z ≲ 10⁻⁴ en univers courbe).
    On emploie alors le développement V = (4π/3) D_M³ [1 − (3/10) u + (9/56) u²], u = Ωk (D_M/D_H)².
    """
    ok = float(model.Ok0)
    dh = c_kms() / model.H0.value                     # Mpc
    x = dm_mpc / dh
    uu = ok * x * x
    if abs(uu) < 1e-3:
        v = 4 * math.pi / 3 * dm_mpc ** 3 * (1 - 0.3 * uu + 9 / 56 * uu * uu)
    else:
        r = math.sqrt(abs(ok))
        inv = math.asinh(r * x) if ok > 0 else math.asin(min(1.0, r * x))
        v = 4 * math.pi * dh ** 3 / (2 * ok) * (x * math.sqrt(1 + uu) - inv / r)
    return v / 1e9


def _brut(model, z: float) -> dict:
    """Grandeurs brutes pour une cosmologie (distances en Mpc, temps en Gyr, vitesses en km/s)."""
    u = _astropy()[1]
    z = float(z)
    dc = model.comoving_distance(z).to_value(u.Mpc)
    dm = model.comoving_transverse_distance(z).to_value(u.Mpc)
    tl = model.lookback_time(z).to_value(u.Gyr)
    dl = (1 + z) * dm
    da = dm / (1 + z)
    ck = c_kms()
    # c × t_L : Gyr → Mpc (une année-lumière par année)
    lookback_mpc = tl * 1e9 / al_par_mpc()
    zp1sq = (1 + z) ** 2
    return {
        'a': 1 / (1 + z), 'E': float(model.efunc(z)), 'H_z': float(model.H(z).value),
        'comoving': dc, 'transverse': dm, 'luminosity': dl, 'angular_diameter': da, 'lookback': lookback_mpc,
        'lookback_gyr': tl, 'age_at_z': float(model.age(z).to_value(u.Gyr)),
        't0_model': float(model.age(0).to_value(u.Gyr)),
        'distmod': 5 * math.log10(dl * 1e5) if dl > 0 else float('nan'),           # D_L / 10 pc
        'kpc_arcsec': da * 1e3 * math.pi / 648000,
        'vol_gpc3': volume_comobile_gpc3(model, dm),
        'v_cz': ck * z, 'v_sr': ck * (zp1sq - 1) / (zp1sq + 1), 'v_flrw': model.H0.value * dc,
    }


_PAS_H0 = 0.10
_PAS_OM = 0.0015


def _sigmas(z: float, Ok: float) -> tuple[dict, dict]:
    """Incertitude 1σ (Planck 2018) propagée depuis (H0, Ωm) corrélés — dérivées centrées, terme croisé
    2ρAB σ_H0 σ_Ωm indispensable (H0 et Ωm sont fortement anticorrélés)."""
    hp = _brut(make_cosmology(H0_PLANCK + _PAS_H0, OM_PLANCK, Ok), z)
    hm = _brut(make_cosmology(H0_PLANCK - _PAS_H0, OM_PLANCK, Ok), z)
    op = _brut(make_cosmology(H0_PLANCK, OM_PLANCK + _PAS_OM, Ok), z)
    om = _brut(make_cosmology(H0_PLANCK, OM_PLANCK - _PAS_OM, Ok), z)
    out, indep = {}, {}
    for k in AVEC_SIGMA:
        A = (hp[k] - hm[k]) / (2 * _PAS_H0)
        B = (op[k] - om[k]) / (2 * _PAS_OM)
        v_indep = (A * SIGMA_H0) ** 2 + (B * SIGMA_OM) ** 2
        var = v_indep + 2 * RHO_H0_OM * A * B * SIGMA_H0 * SIGMA_OM
        out[k] = float(math.sqrt(max(var, 0.0)))
        indep[k] = float(math.sqrt(max(v_indep, 0.0)))
    return out, indep


def verifier_z(z) -> float:
    try:
        z = float(str(z).replace(',', '.').replace(' ', '').replace(' ', ''))
    except (TypeError, ValueError):
        raise ErreurCosmo('cosmo_err_z_illisible', z=z)
    if not math.isfinite(z):
        raise ErreurCosmo('cosmo_err_z_illisible', z=z)
    if z <= 0:
        raise ErreurCosmo('cosmo_err_z_negatif', z=z)
    if z > Z_MAX:
        raise ErreurCosmo('cosmo_err_z_grand', z=z, maxi=Z_MAX)
    return z


def avertissements(z: float) -> list[str]:
    out = []
    if z < Z_PROCHE:
        out.append('cosmo_av_proche')
    if z > Z_CMB:
        out.append('cosmo_av_opaque')
    return out


def calculer(z, modele: str = 'planck18', H0=None, Om=None, Ok: float = 0.0, incertitudes: bool = True,
             shoes: bool = False) -> dict:
    """Toutes les grandeurs pour un redshift z.

    Rend un dict : grandeurs (voir GRANDEURS), ``z``, ``modele``, ``parametres``, ``avertissements`` (clés),
    et pour Planck 2018 : ``sigma`` / ``sigma_indep`` (si `incertitudes`), ``shoes`` (si `shoes`).
    """
    z = verifier_z(z)
    m = construire(modele, H0, Om, Ok)
    d = _brut(m, z)
    d.update(z=z, modele=modele, parametres=parametres(m), avertissements=avertissements(z),
             Ok=float(m.Ok0))
    if modele == 'planck18':
        if incertitudes:
            d['sigma'], d['sigma_indep'] = _sigmas(z, float(Ok or 0.0))
        if shoes:
            sh = _brut(make_cosmology(H0_SHOES, OM_PLANCK, float(Ok or 0.0)), z)
            sh['ecart_pct'] = {k: (100.0 * (sh[k] / d[k] - 1.0) if d[k] else 0.0) for k in AVEC_SIGMA}
            d['shoes'] = sh
    return d


def grille_z(zmin: float = 1e-3, zmax: float = Z_MAX, n: int = 300) -> np.ndarray:
    return np.logspace(math.log10(zmin), math.log10(zmax), int(n))


def courbes(z_grille, modele: str = 'planck18', H0=None, Om=None, Ok: float = 0.0) -> dict:
    """Distances (Mpc) et temps (Gyr) sur une grille de z (calcul vectoriel astropy)."""
    u = _astropy()[1]
    m = construire(modele, H0, Om, Ok)
    z = np.asarray(z_grille, dtype=float)
    dm = m.comoving_transverse_distance(z).to_value(u.Mpc)
    tl = m.lookback_time(z).to_value(u.Gyr)
    return {
        'z': z,
        'comoving': m.comoving_distance(z).to_value(u.Mpc),
        'transverse': dm,
        'luminosity': (1 + z) * dm,
        'angular_diameter': dm / (1 + z),
        'lookback': tl * 1e9 / al_par_mpc(),
        'lookback_gyr': tl,
        'age_at_z': m.age(z).to_value(u.Gyr),
    }
