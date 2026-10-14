# Vérification (SageMath) de quelques valeurs du modèle de masse de la Voie lactée (McMillan 2017, paramètres
# repris de galpy, potential/McMillan17.py) utilisées par « Courbe de rotation de la Voie lactée ».
# Usage : sage outils/verif_anim/voie_lactee_verif.sage
R = RealField(80)
UA_KM = R(149597870.7)
PC_M = UA_KM * 1000 * 648000 / R(pi)
KPC_M = PC_M * 1000
GM_SOLEIL = R(1.32712440018e20)                 # m^3 s^-2
G = GM_SOLEIL / (KPC_M * 10^6)                   # kpc (km/s)^2 / M_sol
print("G =", G, "kpc (km/s)^2 / Msol")

# halo NFW : rho0 = 0,00854 Msol/pc^3, rh = 19,6 kpc ; v^2 = G M(<r) / r, M(<r) = 4 pi rho0 rh^3 [ln(1+x) - x/(1+x)]
rho0 = R(0.00854) * 10^9                          # Msol / kpc^3
rh = R(19.6)
def v_halo(r):
    x = r / rh
    return sqrt(G * 4 * R(pi) * rho0 * rh^3 * (log(1 + x) - x / (1 + x)) / r)
for r, galpy in [(8.2, 152.059), (15, 176.746), (25, 190.747)]:
    v = v_halo(R(r))
    print("halo v(%s kpc) = %.3f km/s ; galpy %.3f ; écart relatif %.2e" % (r, v, galpy, abs(v - galpy) / galpy))

# bulbe : rho = rho0b / (1 + m/r0)^1.8 * exp(-(m/rcut)^2), m = sqrt(R^2 + (z/q)^2), q = 0,5
rho0b = R(98.4) * 10^9
r0 = R(0.075); rcut = R(2.1); q = R(0.5)
def masse_bulbe(rmax):
    # coordonnées sphériques (r, mu = cos theta) ; symétrie : facteur 2 * 2 pi
    f = lambda r, mu: r^2 * rho0b / (1 + sqrt(r^2 * (1 - mu^2) + (r * mu / q)^2) / r0)^R(1.8) * exp(-(r^2 * (1 - mu^2) + (r * mu / q)^2) / rcut^2)
    from scipy.integrate import dblquad
    v, e = dblquad(lambda mu, r: float(f(r, mu)), 0, float(rmax), 0, 1, epsabs=1e2, epsrel=1e-9)
    return 4 * R(pi) * v
for rmax, galpy in [(2, 7.36185e9), (25, 8.87709e9)]:
    m = masse_bulbe(rmax)
    print("bulbe M(<%s kpc) = %.5e Msol ; galpy %.5e ; écart relatif %.2e" % (rmax, m, galpy, abs(m - galpy) / galpy))
