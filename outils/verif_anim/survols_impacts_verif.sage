# Vérification SageMath des trois animations « P6 » (code propre à Coupole) : le diagramme a–e, l'assistance
# gravitationnelle et le cratère d'impact.  Recalcule ici, sans le code de Coupole :
#  - diagramme a–e : q, Q, P = a^(3/2), paramètre de Tisserand, famille (définitions CNEOS et SBDB réécrites),
#    résonances a_J (q/p)^(2/3), positions képlériennes (équation de Kepler résolue à 50 chiffres) ;
#  - assistance : déviation δ, puis le survol INTÉGRÉ numériquement (scipy DOP853, deux corps, départ à 10⁶ rₚ) depuis l'asymptote
#    d'entrée au paramètre d'impact b, du bon côté : direction de sortie, vitesse au périastre, gain héliocentrique,
#    orbites autour du Soleil avant et après (vis-viva) ;
#  - cratère : équations 21 à 28 et 48 de Collins, Melosh et Marcus (2005) en précision arbitraire.
# Usage : sage outils/verif_anim/survols_impacts_verif.sage   (écrit tests/survols_impacts_sage.json)
import json, os
import mpmath
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'survols_impacts_sage.json'))
R = RealField(160)
def f10(x):
    return float('%.10g' % float(x))
out = {'sage': VERSION_SAGE}

# ------------------------------------------------------------------ diagramme a–e
AJ = R('5.2026')
OBJ = {'ceres': ('2.77', '0.0797', '10.6'), 'apophis': ('0.922', '0.191', '3.34'), 'atira': ('0.741', '0.322', '25.6'),
       'eros': ('1.46', '0.223', '10.8'), 'bennu': ('1.13', '0.204', '6.03'), 'tchouri': ('3.46', '0.641', '7.04'),
       'halley': ('17.9', '0.968', '162'), 'hektor': ('5.28', '0.0243', '18.1'), 'chiron': ('13.7', '0.38', '6.93'),
       'sedna': ('544', '0.86', '11.9'), 'pallas': ('2.77', '0.231', '34.9'), 'hidalgo': ('5.73', '0.662', '42.5')}
def famille(a, e):
    q, Q = a*(1 - e), a*(1 + e)
    if q < R('1.3'):
        if a < 1:
            return 'atira' if Q < R('0.983') else 'aten'
        return 'apollo' if q < R('1.017') else 'amor'
    if a < R('3.2'):
        return 'croiseur_mars' if q < R('1.666') else ('ceinture_int' if a < 2 else 'ceinture')
    if a < R('4.6'):
        return 'ceinture_ext'
    if a < R('5.5'):
        return 'troyen' if e < R('0.3') else 'autre'
    return 'centaure' if a < R('30.1') else 'transneptunien'
ae = {}
for k, (a, e, i) in OBJ.items():
    a, e, i = R(a), R(e), R(i)
    T = AJ/a + 2*cos(i*pi/180)*sqrt(a/AJ*(1 - e^2))
    ae[k] = {'q': f10(a*(1 - e)), 'Q': f10(a*(1 + e)), 'P': f10(a^(3/2)), 'T': f10(T), 'famille': famille(a, e)}
out['ae'] = ae
out['resonances'] = {'%d:%d' % (p, q): f10(AJ*(R(q)/p)^(2/3)) for p, q in ((3, 1), (5, 2), (7, 3), (2, 1), (3, 2), (1, 1))}
mpmath.mp.dps = 50
pos = {}
for a, e, M in (('1.0', '0.5', '1.0'), ('2.77', '0.0797', '4.0'), ('17.9', '0.968', '0.05'), ('3.46', '0.641', '5.9')):
    am, em, Mm = mpmath.mpf(a), mpmath.mpf(e), mpmath.mpf(M)
    E = mpmath.findroot(lambda E: E - em*mpmath.sin(E) - Mm, mpmath.pi)
    pos['%s,%s,%s' % (a, e, M)] = [f10(am*(mpmath.cos(E) - em)), f10(am*mpmath.sqrt(1 - em**2)*mpmath.sin(E))]
out['kepler'] = pos

# ------------------------------------------------------------------ assistance gravitationnelle
GMS = R('1.32712440018e11'); UA = R('149597870.7')
PL = {'venus': ('324858.59', '6051.8', '0.723'), 'terre': ('398600.44', '6378.1', '1.0'),
      'jupiter': ('126686534', '71492', '5.203'), 'saturne': ('37931187', '60268', '9.537')}
def orbite(a_ua, vt, vr):
    r = a_ua*UA; v2 = vt^2 + vr^2; en = v2/2 - GMS/r; h = r*vt
    e = sqrt(max(R(0), 1 + 2*en*h^2/GMS^2))
    if en >= 0:
        return {'a': None, 'e': f10(e), 'q': f10(h^2/GMS/(1 + e)/UA), 'Q': None}
    a = -GMS/(2*en)
    return {'a': f10(a/UA), 'e': f10(e), 'q': f10(a*(1 - e)/UA), 'Q': f10(a*(1 + e)/UA)}
mpmath.mp.dps = 30
surv = {}
for cle, vinf, rp_r, ang, derr in (('jupiter', '10', '5', '150', True), ('jupiter', '10', '5', '150', False),
                                   ('venus', '6', '1.1', '200', True), ('terre', '4', '1.2', '120', True),
                                   ('saturne', '8', '3', '30', False), ('terre', '9', '1.05', '270', False)):
    gm, rayon, a = map(R, PL[cle])
    vinf, rp = R(vinf), R(rp_r)*rayon
    th = R(ang)*pi/180
    u = vector(R, [cos(th), sin(th)])
    n = vector(R, [-u[1], u[0]])
    if n[0] != 0 and (n[0] < 0) != derr:
        n = -n
    delta = 2*arcsin(1/(1 + rp*vinf^2/gm))
    b = rp*sqrt(1 + 2*gm/(rp*vinf^2))
    # intégration indépendante, unités : longueur r_p, vitesse v∞ (μ' = gm/(r_p v∞²))
    mu1 = mpmath.mpf(str(gm/(rp*vinf^2)))
    bb = mpmath.mpf(str(b/rp)); D = mpmath.mpf(10)**6
    ux, uy = mpmath.mpf(str(u[0])), mpmath.mpf(str(u[1])); nx, ny = mpmath.mpf(str(n[0])), mpmath.mpf(str(n[1]))
    # départ loin en amont sur l'asymptote d'entrée, vitesse ajustée par l'énergie : v² = 1 + 2μ'/r
    x0, y0 = -D*ux + bb*nx, -D*uy + bb*ny
    r0 = mpmath.sqrt(x0**2 + y0**2); v0 = mpmath.sqrt(1 + 2*mu1/r0)
    # moment cinétique exact : h = b · 1 ; la vitesse de départ garde h et l'énergie
    vr_ = -mpmath.sqrt(v0**2 - (bb/r0)**2)                  # radiale (vers la planète)
    er = (x0/r0, y0/r0); sgn = 1 if (x0*uy - y0*ux) > 0 else -1
    et = (-er[1]*sgn, er[0]*sgn)
    vt_ = bb/r0
    vx0, vy0 = vr_*er[0] + vt_*et[0], vr_*er[1] + vt_*et[1]
    from scipy.integrate import solve_ivp
    m1f = float(mu1)
    def f(t, s):
        x, y, vx, vy = s
        r3 = (x*x + y*y)**1.5
        return [vx, vy, -m1f*x/r3, -m1f*y/r3]
    ivp = solve_ivp(f, (0.0, float(2*D)), [float(x0), float(y0), float(vx0), float(vy0)], method='DOP853',
                    rtol=1e-13, atol=1e-12)
    sT = ivp.y[:, -1]
    # asymptote de sortie tirée de l'état final (vecteur excentricité et moment cinétique de la trajectoire intégrée)
    X = vector(R, [R(str(sT[0])), R(str(sT[1]))]); Vv = vector(R, [R(str(sT[2])), R(str(sT[3]))])
    m1 = R(str(mu1)); rT = X.norm(); hz = X[0]*Vv[1] - X[1]*Vv[0]
    ev = ((Vv*Vv - m1/rT)*X - (X*Vv)*Vv)/m1
    ee = ev.norm(); eh = ev/ee
    perp = vector(R, [-eh[1], eh[0]]) if hz > 0 else vector(R, [eh[1], -eh[0]])
    uo = (-eh + sqrt(ee^2 - 1)*perp)/ee
    rmin = hz^2/m1/(1 + ee)
    V = sqrt(GMS/(a*UA))
    vin = vector(R, [V + vinf*u[0], vinf*u[1]]); vo = vector(R, [V + vinf*uo[0], vinf*uo[1]])
    surv['%s,%s,%s,%s,%s' % (cle, vinf, rp_r, ang, 'derriere' if derr else 'devant')] = {
        'V': f10(V), 'delta': f10(delta), 'delta_integre': f10(arccos(u*uo)), 'u_out': [f10(uo[0]), f10(uo[1])],
        'rmin_rp': f10(rmin), 'gain': f10(vo.norm() - vin.norm()), 'dv': f10(2*vinf*sin(delta/2)),
        'v_peri': f10(sqrt(vinf^2 + 2*gm/rp)), 'orb_in': orbite(a, vin[0], vin[1]), 'orb_out': orbite(a, vo[0], vo[1])}
    print(cle, float(delta), float(arccos(u*uo)), float(rmin), float(vo.norm() - vin.norm()))
out['survols'] = surv

# ------------------------------------------------------------------ cratère (Collins et al. 2005)
def cratere(L, v, th, ri, rt, k=R('1.161')):
    L, v, th, ri, rt = R(L), R(v), R(th), R(ri), R(rt)
    Dtc = k*(ri/rt)^(1/3)*L^R('0.78')*v^R('0.44')*R('9.81')^R('-0.22')*sin(th*pi/180)^(1/3)
    dtc = Dtc/(2*sqrt(R(2)))
    if Dtc <= 2560:
        Dfr = R('1.25')*Dtc; h = R('0.07')*Dtc^4/Dfr^3; Vbr = R('0.032')*Dfr^3
        t = R('2.8')*Vbr*(dtc + h)/(dtc*Dfr^2); d = dtc + h - t; g = 'simple'
    else:
        Dfr = R('1.17')*(Dtc/1000)^R('1.13')/R('3.2')^R('0.13')*1000; h = R('0.07')*Dtc^4/Dfr^3
        t = R(0); d = R('0.4')*(Dfr/1000)^R('0.3')*1000; g = 'complexe'
    E = pi/6*ri*L^3*v^2/2
    Emt = E/R('4.18e15')
    return {'transitoire': f10(Dtc), 'prof_transitoire': f10(dtc), 'final': f10(Dfr), 'profondeur': f10(d),
            'rempart': f10(h), 'breche': f10(t), 'genre': g, 'E': f10(E), 'E_Mt': f10(Emt),
            'recurrence': f10(109*Emt^R('0.78'))}
cr = {}
for L, v, th, ri, rt in (('1500', '20000', '45', '3000', '2500'), ('50', '12000', '45', '8000', '2500'),
                         ('10000', '20000', '45', '3000', '2500'), ('100', '17000', '90', '1000', '2750'),
                         ('300', '25000', '30', '1500', '2750'), ('2000', '11000', '60', '8000', '2500'),
                         ('1900', '17000', '45', '3000', '2500')):
    cr['%s,%s,%s,%s,%s' % (L, v, th, ri, rt)] = cratere(L, v, th, ri, rt)
out['crateres'] = cr
print(json.dumps(cr['1500,20000,45,3000,2500']))
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False)
