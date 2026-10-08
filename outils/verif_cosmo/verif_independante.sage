# Vérification indépendante des distances cosmologiques (SageMath + mpmath, sans astropy).
# Lit un JSON {Z, liste:[{nom, params, candidats:{source: [lignes par z]}}], constantes, ...}
# et rapporte, pour chaque source, les écarts relatifs à l'intégration de référence.
import json
import sys
from mpmath import mp, mpf, sqrt as msqrt, exp as mexp, log as mlog, quad, pi as mpi, findroot, asinh as masinh, \
    asin as masin, sinh as msinh, sin as msin, zeta as mzeta, log10 as mlog10

mp.dps = 18
ENTREE, SORTIE = sys.argv[1], sys.argv[2]
doc = json.load(open(ENTREE))

# ---------------------------------------------------------------- constantes (SI, CODATA 2018 = 2022 pour G, hbar)
c = mpf(299792458)
G = mpf('6.67430e-11')
kB = mpf('1.380649e-23')
hbar = mpf('1.054571817e-34')
eV = mpf('1.602176634e-19')
Mpc = mpf('3.0856775814913673e22')
an = mpf(31557600)                    # année julienne (s)
al = c * an                           # année-lumière (m)
Gyr = an * 10**9
Gpc = Mpc * 1000
kpc = Mpc / 1000
pc = Mpc / 10**6
seconde_arc = mpi / (180 * 3600)

# ---------------------------------------------------------------- neutrinos : Fermi-Dirac exacte, tabulée
PREF = mpf(120) / (7 * mpi**4)


def f_brute(y):
    y = mpf(y)
    return PREF * quad(lambda x: x**2 * msqrt(x**2 + y**2) / (mexp(x) + 1), [0, 2, 8, 20, 60])


LMIN, LMAX, PAS = mpf(-9), mpf(14), mpf('0.05')
NT = int((LMAX - LMIN) / PAS) + 1
LT = [LMIN + PAS * i for i in range(NT)]
FT = [f_brute(mexp(l)) for l in LT]
ASYMP = PREF * mpf(3) / 2 * mzeta(3)


def f_exacte(y):
    if y <= 0:
        return mpf(1)
    l = mlog(y)
    if l <= LMIN:
        return mpf(1)
    if l >= LMAX:
        return ASYMP * y               # régime non relativiste : f ≈ (120/7π⁴)·(3/2)ζ(3)·y
    i = int((l - LMIN) / PAS)
    i = max(0, min(NT - 9, i - 4))
    s = mpf(0)
    for j in range(9):
        t = FT[i + j]
        for k in range(9):
            if k != j:
                t *= (l - LT[i + k]) / (LT[i + j] - LT[i + k])
        s += t
    return s


def f_komatsu(y):                      # ajustement de Komatsu et al. (2011), celui d'astropy
    return (1 + (mpf('0.3173') * y)**mpf('1.83'))**(1 / mpf('1.83'))


class Modele:
    def __init__(self, p, exacte=True):
        self.H0 = mpf(p['H0']) * 1000 / Mpc              # s⁻¹
        self.H0_kms = mpf(p['H0'])
        self.Om0, self.Ok0 = mpf(p['Om0']), mpf(p['Ok0'])
        T = mpf(p['Tcmb0'])
        rho_c = 3 * self.H0**2 / (8 * mpi * G)
        # densité d'énergie des photons : (π²/15) (kT)⁴ / (ħc)³
        self.Og0 = (mpi**2 / 15) * (kB * T)**4 / (hbar * c)**3 / (rho_c * c**2)
        Tnu = (mpf(4) / 11)**(mpf(1) / 3) * T
        m = [mpf(x) for x in p['m_nu']]
        self.ff = f_exacte if exacte else f_komatsu
        self.y = [x * eV / (kB * Tnu) for x in m if x > 0] if T > 0 else []
        self.nml = len([x for x in m if x <= 0])
        self.npn = mpf(p['Neff']) / len(m) if m else mpf(0)
        self.Onu0 = self.Og0 * self.nurel(0) if T > 0 else mpf(0)
        self.Ode0 = 1 - self.Om0 - self.Og0 - self.Onu0 - self.Ok0
        self.DH = c / self.H0
        self.tH = 1 / self.H0

    def nurel(self, z):
        zp1 = 1 + mpf(z)
        return mpf(7) / 8 * (mpf(4) / 11)**(mpf(4) / 3) * self.npn * (sum(self.ff(y / zp1) for y in self.y)
                                                                         + self.nml)

    def E(self, z):
        zp1 = 1 + mpf(z)
        Or = self.Og0 * (1 + self.nurel(z)) if self.Og0 > 0 else 0
        return msqrt(Or * zp1**4 + self.Om0 * zp1**3 + self.Ok0 * zp1**2 + self.Ode0)

    def Ea(self, a):
        return self.E(1 / mpf(a) - 1)

    def DM(self, dc):
        ok = self.Ok0
        if ok == 0:
            return dc
        r = msqrt(abs(ok))
        return self.DH / r * (msinh(r * dc / self.DH) if ok > 0 else msin(r * dc / self.DH))

    def volume(self, dm):
        ok, DH = self.Ok0, self.DH
        if ok == 0:
            return 4 * mpi / 3 * dm**3
        # forme fermée de Hogg (1999) ; la soustraction perd ~2·log10(1/(Ωk x²)) chiffres à petit z :
        # on l'évalue avec 100 chiffres (l'entrée D_M, elle, n'est pas amplifiée : f'(x) ≈ 2u).
        with mp.workdps(100):
            x = mpf(dm) / DH
            r = msqrt(abs(ok))
            inv = masinh(r * x) if ok > 0 else masin(r * x)
            v = 4 * mpi * DH**3 / (2 * ok) * (x * msqrt(1 + ok * x**2) - inv / r)
        return +v

    def age_a(self, a):
        a = mpf(a)
        pts = [mpf(0)] + [mpf(q) for q in ('1e-7', '1e-6', '1e-5', '1e-4', '1e-3', '1e-2', '0.1', '0.5') if mpf(q) < a] + [a]
        return self.tH * quad(lambda x: 1 / (x * self.Ea(x)) if x > 0 else 0, pts)


def grille(mod, Z):
    """Grandeurs sur la grille Z (croissante), intégrales cumulées intervalle par intervalle."""
    out = []
    dc_cum, tl_cum, zp = mpf(0), mpf(0), mpf(0)
    for z in Z:
        z = mpf(z)
        if z > zp:
            dc_cum += quad(lambda x: 1 / mod.E(x), [zp, z])
            tl_cum += quad(lambda x: 1 / ((1 + x) * mod.E(x)), [zp, z])
            zp = z
        dc = mod.DH * dc_cum
        tl = mod.tH * tl_cum
        dm = mod.DM(dc)
        dl, da = dm * (1 + z), dm / (1 + z)
        r = {'comoving': dc / al, 'transverse': dm / al, 'luminosity': dl / al, 'angular_diameter': da / al,
             'lookback': c * tl / al, 'lookback_gyr': tl / Gyr, 'age_at_z': mod.age_a(1 / (1 + z)) / Gyr,
             'E': mod.E(z), 'v_flrw': mod.H0_kms * dc / Mpc, 'vol_gpc3': mod.volume(dm) / Gpc**3}
        if z > 0:
            r['distmod'] = 5 * mlog10(dl / (10 * pc))
            r['kpc_arcsec'] = da * seconde_arc / kpc
        out.append(r)
    return out


def ecart(v, ref):
    if v is None or ref is None:
        return None
    v, ref = mpf(v), mpf(ref)
    if ref == 0:
        return abs(v)
    return abs(v / ref - 1)


SEUIL = mpf('1e-4')
Z = doc['Z']
rapport = {'modeles': []}
for m in doc['liste']:
    print('===', m['nom'], flush=True)
    refs = {}
    for variante, exacte in (('exacte', True), ('komatsu', False)):
        mod = Modele(m['params'], exacte)
        refs[variante] = grille(mod, Z)
        if variante == 'exacte':
            print('  Ω_γ = %s  Ω_ν = %s  Ω_Λ = %s  t0 = %s Gyr' % (mod.Og0, mod.Onu0, mod.Ode0,
                                                                    mod.age_a(1) / Gyr), flush=True)
    bilan = {}
    for src, lignes in m['candidats'].items():
        for variante in ('exacte', 'komatsu'):
            pire, hors = {}, []
            for z, l, rf in zip(Z, lignes, refs[variante]):
                for q, v in l.items():
                    if q not in rf:
                        continue
                    e = ecart(v, rf[q])
                    if e is None:
                        continue
                    if e > pire.get(q, (mpf(-1), 0))[0]:
                        pire[q] = (e, z)
                    if e > SEUIL:
                        hors.append((q, z, float(e), float(v), float(rf[q])))
            bilan['%s/%s' % (src, variante)] = {'pire': {q: (float(e), z) for q, (e, z) in pire.items()},
                                                'hors_seuil': hors}
            print('  %-22s vs %-8s : pire écart %s' % (src, variante, ', '.join(
                '%s %.1e (z=%g)' % (q, e, z) for q, (e, z) in sorted(pire.items()))), flush=True)
            for h in hors:
                print('      > 1e-4 : %s z=%g  écart %.3e  (%r vs %r)' % h, flush=True)
    rapport['modeles'].append({'nom': m['nom'], 'bilan': bilan,
                               'ref_exacte': [{k: float(v) for k, v in r.items()} for r in refs['exacte']]})

# ---------------------------------------------------------------- constantes écrites en dur (Planck 2018 plat)
if 'constantes' in doc:
    K = doc['constantes']
    p = {'H0': 67.66, 'Om0': 0.30966, 'Ok0': 0, 'Tcmb0': 2.7255, 'Neff': 3.046, 'm_nu': [0, 0, 0.06]}
    mod = Modele(p, True)
    t0 = mod.age_a(1) / Gyr
    DH = mod.DH / al / 10**9
    hp = mod.DH * quad(lambda a: 1 / (a**2 * mod.Ea(a)) if a > 0 else 1 / msqrt(mod.Og0 * (1 + mod.nurel(10**12))),
                       [0, mpf('1e-6'), mpf('1e-4'), mpf('1e-2'), 1]) / al / 10**9
    he = mod.DH * quad(lambda s: 1 / mod.Ea(1 / s) if s > 0 else 1 / msqrt(mod.Ode0), [0, mpf('0.5'), 1]) / al / 10**9

    def dc(z):
        return mod.DH * quad(lambda x: 1 / mod.E(x), [0, z])
    zmax = findroot(lambda z: (1 + z) * mod.DH / mod.E(z) - dc(z), mpf('1.6'))
    damax = dc(zmax) / (1 + zmax) / al / 10**9
    print('=== constantes du calculateur')
    for nom, v_prog, v_ref in (('T0_GYR', K['T0_GYR'], t0), ('D_H_GLYR', K['D_H_GLYR'], DH),
                               ('PARTICLE_HORIZON_GLYR', K['PARTICLE_HORIZON_GLYR'], hp),
                               ('EVENT_HORIZON_GLYR', K['EVENT_HORIZON_GLYR'], he),
                               ('Z_DA_MAX', K['Z_DA_MAX'], zmax), ('DA_MAX_GLYR', K['DA_MAX_GLYR'], damax)):
        print('  %-22s programme %-14r  Sage %-22s  écart relatif %.2e' % (nom, v_prog, mp.nstr(v_ref, 12),
                                                                         float(ecart(v_prog, v_ref))))
        rapport.setdefault('constantes', {})[nom] = (v_prog, float(v_ref), float(ecart(v_prog, v_ref)))
    # corrélation ρ(H0, Ωm) déduite de ω_m = Ωm h² : relation (s_w/w)² = (s_O/O)² + 4(s_h/h)² + 4ρ(s_O/O)(s_h/h)
    def rho(w, sw):
        O, sO, h, sh = mpf('0.3111'), mpf('0.0056'), mpf('0.6766'), mpf('0.0042')
        return ((sw / w)**2 - (sO / O)**2 - 4 * (sh / h)**2) / (4 * (sO / O) * (sh / h))
    r1 = rho(mpf('0.11933') + mpf('0.02242') + mpf('0.06') / mpf('93.14'), msqrt(mpf('0.00091')**2 + mpf('0.00014')**2))
    r2 = rho(mpf('0.14240'), mpf('0.00087'))
    print('  rho : %s (σ(ω_c), σ(ω_b) ajoutées en quadrature, comme le programme)  ;  %s (σ(Ω_m h²) = 0,00087 publiée)'
          % (mp.nstr(r1, 6), mp.nstr(r2, 6)))
    rapport['rho'] = (float(r1), float(r2))

json.dump(rapport, open(SORTIE, 'w'), indent=1, default=float)
print('fini')
